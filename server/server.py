import socket
import threading
import json
import base64
import time 
from datetime import datetime
from typing import Dict, List, Optional
from .database import DatabaseManager, Group,User
from .database import Message
from sqlalchemy import desc
import os

class ChatServer:
    def __init__(self, host='192.168.1.10', port=12345):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)        
        # Database
        self.db = DatabaseManager()       
        # Client connections: {user_id: client_socket}
        self.clients: Dict[int, socket.socket] = {}      
        # User sessions: {session_token: user_id}
        self.sessions: Dict[str, int] = {}        
        # Typing status: {user_id: {conversation_id: timestamp}}
        self.typing_status: Dict[int, Dict[int, float]] = {}       
        self.running = False       
        print(f"🚀 Chat Server initializing on {host}:{port}")   
        self._initialize_company_group()
    def _initialize_company_group(self):
        """
        Kiểm tra và tự động tạo nhóm chung cho toàn công ty nếu chưa tồn tại.
        Hàm này sẽ tạo nhóm đầu tiên và quy ước nó là nhóm chung.
        """
        try:
            print("🏢 Checking for company-wide group...")
            # Sử dụng session của DB để truy vấn
            # Thay vì kiểm tra ID=1, chúng ta kiểm tra xem có bất kỳ nhóm nào chưa
            any_group_exists = self.db.db.query(Group).first()
            
            if not any_group_exists:
                print("⚠️ No groups found. Creating the first one as the company-wide group...")
                
                # Tìm một user bất kỳ để làm "creator"
                first_user = self.db.db.query(User).first()
                creator_id = first_user.id if first_user else None

                # Tạo nhóm mới một cách tự nhiên, không gán cứng ID
                # PostgreSQL sẽ tự động gán ID=1 cho bản ghi đầu tiên này.
                new_group = Group(
                    name="Thông báo chung", 
                    creator_id=creator_id
                )
                self.db.db.add(new_group)
                self.db.db.commit()
                print(f"✅ Successfully created company-wide group '{new_group.name}' with ID {new_group.id}.")
            else:
                print(f"👍 Company-wide group (ID: {any_group_exists.id}) already exists.")
        except Exception as e:
            print(f"❌ Error initializing company-wide group: {e}")
            self.db.db.rollback()
    def start(self):
        """Khởi động server"""
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
            self.running = True           
            print(f"✅ Server started successfully!")
            print(f"🌐 Listening on {self.host}:{self.port}")
            print(f"📊 Database ready")
            print("=" * 50)            
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=self._cleanup_thread, daemon=True)
            cleanup_thread.start()           
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    print(f"🔗 New connection from {address}")                   
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True)
                    client_thread.start()                   
                except Exception as e:
                    if self.running:
                        print(f"❌ Error accepting connection: {e}")                    
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
        finally:
            self.stop()   
    def stop(self):
        """Dừng server"""
        print("\n👋 Shutting down server...")
        self.running = False       
        # Close all client connections
        for user_id, client_socket in self.clients.copy().items():
            try:
                client_socket.close()
            except:
                pass        
        self.clients.clear()
        self.sessions.clear()       
        # Close server socket
        try:
            self.socket.close()
        except:
            pass       
        # Close database
        self.db.close()
        print("✅ Server stopped successfully")   
    def _handle_client(self, client_socket: socket.socket, address):
        """Xử lý client connection với bộ đệm JSON an toàn."""
        user_id = None
        buffer = "" # Bộ đệm cho mỗi client
        try:
            while self.running:
                try:
                    # Nhận dữ liệu và nối vào buffer
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        # Client đã ngắt kết nối
                        break
                    buffer += data
                    # Xử lý tất cả các gói JSON hoàn chỉnh có trong buffer
                    while True:
                        # Tìm vị trí bắt đầu và kết thúc của một đối tượng JSON
                        # Giả định mỗi gói tin là một dictionary, bắt đầu bằng '{' và kết thúc bằng '}'
                        try:
                            start_index = buffer.find('{')
                            if start_index == -1:
                                # Không có JSON object nào, có thể là dữ liệu rác
                                buffer = ""
                                break
                            # Tìm dấu ngoặc đóng tương ứng, xử lý trường hợp có dấu ngoặc trong chuỗi
                            brace_count = 0
                            end_index = -1
                            in_string = False
                            for i in range(start_index, len(buffer)):
                                char = buffer[i]
                                if char == '"' and (i == 0 or buffer[i-1] != '\\'):
                                    in_string = not in_string
                                elif not in_string:
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1                   
                                if brace_count == 0 and i >= start_index:
                                    end_index = i
                                    break                           
                            if end_index != -1:
                                # Đã tìm thấy một gói JSON hoàn chỉnh
                                json_str = buffer[start_index : end_index + 1]
                                message = json.loads(json_str)                              
                                # Xóa gói JSON đã xử lý khỏi buffer
                                buffer = buffer[end_index + 1:]                                
                                # Xử lý message
                                response = self._process_message(message, client_socket, address)                                
                                # Cập nhật user_id nếu đăng nhập thành công
                                if message.get('type') == 'login' and response.get('success'):
                                    user_id = response.get('user_id')
                                    self.clients[user_id] = client_socket                               
                                # Gửi phản hồi nếu có
                                if response:
                                    self._send_message(client_socket, response)
                            else:
                                # Chưa có gói JSON hoàn chỉnh, đợi thêm dữ liệu
                                break                               
                        except json.JSONDecodeError:
                            # Lỗi này có thể xảy ra nếu gói tin chưa đầy đủ, đợi thêm dữ liệu
                            print(f"JSONDecodeError - Buffer có thể chưa hoàn chỉnh. Buffer: {buffer}")
                            break # Thoát vòng lặp while True và đợi recv() tiếp
                        except Exception as e:
                            print(f"Lỗi xử lý buffer của client {address}: {e}")
                            buffer = "" # Xóa buffer để tránh lặp lỗi
                            break
                except ConnectionResetError:
                    break # Client ngắt kết nối đột ngột
                except Exception as e:
                    if self.running:
                        print(f"Lỗi xử lý client {address}: {e}")
                    break                   
        except Exception as e:
            print(f"Lỗi nghiêm trọng trong client handler {address}: {e}")
        finally:
            # Dọn dẹp khi client ngắt kết nối
            if user_id:
                self._handle_disconnect(user_id)            
            try:
                client_socket.close()
            except:
                pass           
            print(f"🔌 Client {address} đã ngắt kết nối")    
    def _process_message(self, message: dict, client_socket: socket.socket, address) -> dict:
        """Xử lý tin nhắn từ client"""
        message_type = message.get('type')        
        try:
            if message_type == 'register':
                return self._handle_register(message)            
            elif message_type == 'login':
                return self._handle_login(message, address)            
            elif message_type == 'logout':
                return self._handle_logout(message)            
            elif message_type == 'send_message':
                return self._handle_send_message(message)           
            elif message_type == 'send_private_message':
                return self._handle_send_private_message(message)         
            elif message_type == 'upload_file':
                return self._handle_upload_file(message)          
            elif message_type == 'get_contacts':
                return self._handle_get_contacts(message)        
            elif message_type == 'get_conversations':
                return self._handle_get_conversations(message)        
            elif message_type == 'get_messages':
                return self._handle_get_messages(message)       
            elif message_type == 'mark_read':
                return self._handle_mark_read(message)            
            elif message_type == 'typing_start':
                return self._handle_typing_start(message)            
            elif message_type == 'typing_stop':
                return self._handle_typing_stop(message)            
            elif message_type == 'update_status':
                return self._handle_update_status(message)            
            elif message_type == 'search_messages':
                return self._handle_search_messages(message)           
            elif message_type == 'delete_message':
                return self._handle_delete_message(message)    
            elif message_type == 'create_group':
                return self._handle_create_group(message)    
            elif message_type == 'get_group_members':
                return self._handle_get_group_members(message)
            elif message_type == 'add_group_member':
                return self._handle_add_group_member(message)
            elif message_type == 'remove_group_member':
                return self._handle_remove_group_member(message)       
            elif message_type == 'clear_chat':
                return self._handle_clear_chat(message)            
            elif message_type == 'upload_avatar':
                return self._handle_upload_avatar(message)
            else:
                return {"success": False, "error": "Unknown message type"}     
        except Exception as e:
            print(f"❌ Error processing message type {message_type}: {e}")
            return {"success": False, "error": str(e)}
    def _handle_create_group(self, message: dict) -> dict:
        """Xử lý yêu cầu tạo nhóm mới."""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}

        group_name = message.get('group_name')
        member_ids = message.get('member_ids', [])

        success, msg, group = self.db.create_chat_group(group_name, user_id, member_ids)

        if success:
            # Thông báo cho tất cả thành viên về nhóm mới
            self._broadcast_new_group(group)
            return {
                "type": "group_created",
                "success": True,
                "message": msg,
                "group_id": group.id,
                "group_name": group.name
            }
        else:
            return {"type": "create_group", "success": False, "error": msg}
    def _broadcast_new_group(self, group):
        """Thông báo cho các thành viên về một nhóm mới được tạo."""
        # Lấy tin nhắn cuối cùng (sẽ là None vì nhóm vừa được tạo)
        last_msg = self.db.db.query(Message).filter(Message.group_id == group.id).order_by(desc(Message.timestamp)).first()

        # Tạo một đối tượng hội thoại đầy đủ, giống hệt như khi get_conversations
        conversation_data = {
            "type": "group",
            "group_id": group.id,
            "group_name": group.name,
            "member_count": len(group.members),
            "last_message": self.db._message_to_dict(last_msg) if last_msg else None,
            "updated_at": last_msg.timestamp.isoformat() if last_msg else group.created_at.isoformat()
        }

        # Gói tin cuối cùng gửi đi
        notification = {
            "type": "new_group_notification",
            "conversation": conversation_data
        }

        for member in group.members:
            # Gửi thông báo đến tất cả thành viên (bao gồm cả người tạo)
            self._send_message_to_user(member.id, notification)
    def _handle_register(self, message: dict) -> dict:
        """Xử lý đăng ký"""
        username = message.get('username', '').strip()
        password = message.get('password', '')
        display_name = message.get('display_name', '').strip()
        email = message.get('email', '').strip()
        success, error_msg, user = self.db.register_user(
            username, password, display_name or None, email or None)
        if success:
            return {
                "type": "register", # THÊM DÒNG NÀY
                "success": True,
                "message": "Đăng ký thành công",
                "user": self.db._user_to_dict(user)}
        else:
            return {"success": False, "error": error_msg}
    def _handle_add_group_member(self, message: dict) -> dict:
        """Xử lý yêu cầu thêm thành viên."""
        session_token = message.get('session_token')
        actor_id = self.sessions.get(session_token)
        if not actor_id:
            return {"success": False, "error": "Invalid session"}

        group_id = message.get('group_id')
        member_id_to_add = message.get('member_id')
        
        success, msg = self.db.add_member_to_group(group_id, actor_id, member_id_to_add)
        
        if success:
            # Thông báo cho mọi người trong nhóm về sự thay đổi
            self._broadcast_group_update(group_id)
        
        return {"type": "add_member_response", "success": success, "message": msg}

    def _handle_remove_group_member(self, message: dict) -> dict:
        """Xử lý yêu cầu xóa thành viên."""
        session_token = message.get('session_token')
        actor_id = self.sessions.get(session_token)
        if not actor_id:
            return {"success": False, "error": "Invalid session"}

        group_id = message.get('group_id')
        member_id_to_remove = message.get('member_id')

        success, msg = self.db.remove_member_from_group(group_id, actor_id, member_id_to_remove)

        if success:
            # Thông báo cho người bị xóa (nếu họ online)
            self._send_message_to_user(member_id_to_remove, {
                "type": "removed_from_group",
                "group_id": group_id
            })
            # Thông báo cho các thành viên còn lại
            self._broadcast_group_update(group_id)

        return {"type": "remove_member_response", "success": success, "message": msg}
    def _handle_get_group_members(self, message: dict) -> dict:
        """Xử lý yêu cầu lấy danh sách thành viên nhóm."""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}

        group_id = message.get('group_id')
        group = self.db.db.query(Group).filter(Group.id == group_id).first()

        if group:
            members_data = [self.db._user_to_dict(member) for member in group.members]
            return {
                "type": "group_members_list",
                "success": True,
                "group_id": group_id,
                "creator_id": group.creator_id,
                "members": members_data
            }
        return {"success": False, "error": "Group not found"}
    def _broadcast_group_update(self, group_id: int):
        """Gửi thông báo cập nhật thông tin nhóm đến các thành viên."""
        group = self.db.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            return

        # Gửi lại danh sách thành viên mới nhất
        update_packet = {
            "type": "group_members_list",
            "success": True,
            "group_id": group_id,
            "creator_id": group.creator_id,
            "members": [self.db._user_to_dict(member) for member in group.members]
        }
        
        for member in group.members:
            self._send_message_to_user(member.id, update_packet)
    def _handle_login(self, message: dict, address) -> dict:
        """Xử lý đăng nhập (ĐÃ SỬA LỖI LOGIC TRẢ VỀ HỘI THOẠI)."""
        username = message.get('username', '').strip()
        password = message.get('password', '')        
        
        success, error_msg, user, session_token = self.db.login_user(
            username, password, address[0])       
        
        if success:
            self.sessions[session_token] = user.id          
            self._broadcast_user_status(user.id, "online")
            
            # --- LOGIC SỬA LỖI NẰM Ở ĐÂY ---
            # Lấy danh sách tất cả người dùng (trừ chính user này)
            all_users = self.db.get_all_users(exclude_user_id=user.id)
            
            # Lấy danh sách tất cả các hội thoại (cả nhóm và riêng tư) mà user tham gia
            # Hàm get_conversations đã được thiết kế để làm việc này
            conversations = self.db.get_conversations(user.id)
            
            print(f"DEBUG LOGIN: Found {len(conversations)} conversations for user {user.id}")
            # --------------------------------

            return {
                "type": "login",
                "success": True,
                "message": "Đăng nhập thành công",
                "user": self.db._user_to_dict(user),
                "session_token": session_token,
                "user_id": user.id,
                "all_users": all_users,
                "conversations": conversations # Trả về danh sách hội thoại đã lấy được
            }
        else:
            return {"success": False, "error": error_msg}
    def _handle_logout(self, message: dict) -> dict:
        """Xử lý đăng xuất"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if user_id:
            self.db.logout_user(user_id, session_token)
            # Remove from sessions and clients
            if session_token in self.sessions:
                del self.sessions[session_token]
            if user_id in self.clients:
                del self.clients[user_id]
            # Broadcast user offline status
            self._broadcast_user_status(user_id, "offline")
            return {"success": True, "message": "Đăng xuất thành công"}
        return {"success": False, "error": "Invalid session"}
    def _handle_send_message(self, message: dict) -> dict:
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        
        group_id = message.get('group_id')
        content = message.get('content', '')
        client_msg_id = message.get('client_message_id')

        if not group_id:
            return {"success": False, "error": "Group ID is required"}

        # Sửa lỗi logic: không truyền is_group_message nữa
        msg = self.db.save_message(
            sender_id=user_id,
            group_id=group_id,
            content=content,
            message_type='text',
            client_message_id=client_msg_id
        )
        
        if msg:
            self._broadcast_message_to_group(msg)
            return {"success": True, "message": "Message processed"}
        return {"success": False, "error": "Failed to send message"}
    def _broadcast_message_to_group(self, message: 'Message'):
        """Broadcast tin nhắn đến TẤT CẢ thành viên của một nhóm cụ thể."""
        if not message.group_id:
            return

        # Sử dụng session của DB để lấy thông tin group và members
        group = self.db.db.query(Group).filter(Group.id == message.group_id).first()
        if not group:
            print(f"Lỗi broadcast: Không tìm thấy nhóm với ID {message.group_id}")
            return

        message_data = {
            "type": "new_message",
            "message": self.db._message_to_dict(message)
        }
        
        print(f"Broadcasting message id {message.id} to group {group.id} ('{group.name}')")
        
        # Lấy danh sách ID thành viên từ đối tượng group
        member_ids = [member.id for member in group.members]
        print(f"Group members to notify: {member_ids}")
        
        for member_id in member_ids:
            # Gửi tin nhắn đến thành viên nếu họ đang online
            # self.clients là một dictionary {user_id: client_socket}
            if member_id in self.clients:
                print(f"  -> Sending to online user {member_id}")
                self._send_message_to_user(member_id, message_data)
            else:
                print(f"  -> User {member_id} is offline.")
    def _handle_send_private_message(self, message: dict) -> dict:
        """Xử lý gửi tin nhắn riêng"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)       
        if not user_id:
            return {"success": False, "error": "Invalid session"}   
        
        receiver_username = message.get('receiver')
        content = message.get('content', '')
        message_type = message.get('message_type', 'text')
        reply_to_id = message.get('reply_to_id')
        client_msg_id = message.get('client_message_id')
        
        receiver = self.db.get_user_by_username(receiver_username)
        if not receiver:
            return {"success": False, "error": "Receiver not found"}
            
        # SỬA LỜI GỌI HÀM Ở ĐÂY:
        # Loại bỏ is_group=False và đảm bảo không truyền group_id
        msg = self.db.save_message(
            sender_id=user_id,
            receiver_id=receiver.id,
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
            client_message_id=client_msg_id
        )
        
        if msg:
            new_message_packet = {
                "type": "new_message",
                "message": self.db._message_to_dict(msg)
            }
            
            # Gửi tin nhắn đến người nhận nếu họ đang online
            self._send_message_to_user(receiver.id, new_message_packet)
            
            # Gửi lại xác nhận cho chính người gửi
            # (Điều này quan trọng để client có thể cập nhật trạng thái tin nhắn)
            self._send_message_to_user(user_id, new_message_packet)

            # Trả về một phản hồi đơn giản, vì client đã nhận được tin nhắn đầy đủ ở trên
            return {
                "success": True,
                "message": "Message processed",
                "client_message_id": client_msg_id
            }
            
        return {"success": False, "error": "Failed to send message"}
    def _handle_upload_file(self, message: dict) -> dict:
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        
        file_name = message.get('file_name')
        file_data_b64 = message.get('file_data')
        receiver_username = message.get('receiver')
        group_id = message.get('group_id')

        try:
            file_data = base64.b64decode(file_data_b64)
            if len(file_data) > 10 * 1024 * 1024:
                return {"success": False, "error": "File quá lớn (tối đa 10MB)"}

            file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
            message_type = "image" if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp'] else "file"
            
            receiver_id = None
            if receiver_username:
                receiver = self.db.get_user_by_username(receiver_username)
                if receiver: receiver_id = receiver.id

            msg = self.db.save_message(
                sender_id=user_id,
                receiver_id=receiver_id,
                group_id=group_id,
                content=f"📎 {file_name}",
                message_type=message_type,
                file_name=file_name,
                file_data=file_data
            )

            if msg:
                if group_id:
                    self._broadcast_message_to_group(msg)
                elif receiver_id:
                    new_message_packet = {"type": "new_message", "message": self.db._message_to_dict(msg)}
                    self._send_message_to_user(receiver_id, new_message_packet)
                    self._send_message_to_user(user_id, new_message_packet)
                
                return {"success": True, "message": "File uploaded successfully", "message_id": msg.id}
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}
        
        return {"success": False, "error": "Failed to upload file"}
    def _send_message_to_user(self, user_id: int, message_data: dict):
        """Gửi một gói tin đến một user cụ thể nếu họ online."""
        if user_id in self.clients:
            try:
                self._send_message(self.clients[user_id], message_data)
            except Exception as e:
                print(f"Lỗi khi gửi tin đến user {user_id}: {e}")
                self._handle_disconnect(user_id)

    def _handle_get_contacts(self, message: dict) -> dict:
        """Lấy danh sách liên hệ"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        online_users = self.db.get_online_users()
        all_users = self.db.get_all_users(exclude_user_id=user_id)
        return {
            "type": "get_contacts", # THÊM DÒNG NÀY
            "success": True,
            "online_users": online_users,
            "all_users": all_users}
    def _handle_get_conversations(self, message: dict) -> dict:
        """Lấy danh sách hội thoại"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        conversations = self.db.get_conversations(user_id)
        return {
            "type": "get_conversations", # THÊM DÒNG NÀY
            "success": True,
            "conversations": conversations}
    def _handle_get_messages(self, message: dict) -> dict:
        """Lấy tin nhắn (ĐÃ SỬA LỖI LOGIC)."""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}

        # --- LOGIC SỬA LỖI NẰM Ở ĐÂY ---
        other_username = message.get('other_user')
        group_id = message.get('group_id') # Lấy group_id từ message của client
        limit = message.get('limit', 50)
        offset = message.get('offset', 0)

        messages = []
        
        if group_id:
            # Ưu tiên xử lý tin nhắn nhóm nếu có group_id
            print(f"Server handling get_messages for GROUP ID: {group_id}")
            messages = self.db.get_messages(user_id=user_id, group_id=group_id, limit=limit, offset=offset)
        elif other_username:
            # Xử lý tin nhắn riêng tư nếu không có group_id
            print(f"Server handling get_messages for PRIVATE chat with: {other_username}")
            other_user = self.db.get_user_by_username(other_username)
            if other_user:
                messages = self.db.get_messages(user_id=user_id, other_user_id=other_user.id, limit=limit, offset=offset)
        
        return {
            "type": "get_messages",
            "success": True,
            "messages": messages
        }
    def _handle_mark_read(self, message: dict) -> dict:
        """Đánh dấu tin nhắn đã đọc"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        sender_username = message.get('sender')
        sender = self.db.get_user_by_username(sender_username)
        if sender:
            self.db.mark_messages_as_read(user_id, sender.id)
            return {"success": True, "message": "Messages marked as read"}
        return {"success": False, "error": "Sender not found"}
    def _handle_typing_start(self, message: dict) -> dict:
        """Xử lý bắt đầu gõ"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        other_username = message.get('other_user')
        is_group = message.get('is_group', False)
        # Update typing status
        if user_id not in self.typing_status:
            self.typing_status[user_id] = {}
        conversation_key = 'group' if is_group else other_username
        self.typing_status[user_id][conversation_key] = time.time()
        # Notify other users
        if is_group:
            # Broadcast typing status to all online users
            for uid, client_socket in self.clients.items():
                if uid != user_id:
                    self._send_message(client_socket, {
                        "type": "typing_status",
                        "user": self.db._user_to_dict(self.db.get_user_by_id(user_id)),
                        "is_typing": True,
                        "is_group": True})
        else:
            # Send to specific user
            other_user = self.db.get_user_by_username(other_username)
            if other_user and other_user.id in self.clients:
                self._send_message(self.clients[other_user.id], {
                    "type": "typing_status",
                    "user": self.db._user_to_dict(self.db.get_user_by_id(user_id)),
                    "is_typing": True,
                    "is_group": False}) 
        return {"success": True}
    def _handle_typing_stop(self, message: dict) -> dict:
        """Xử lý dừng gõ"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)       
        if not user_id:
            return {"success": False, "error": "Invalid session"}       
        other_username = message.get('other_user')
        is_group = message.get('is_group', False)        
        # Remove typing status
        if user_id in self.typing_status:
            conversation_key = 'group' if is_group else other_username
            if conversation_key in self.typing_status[user_id]:
                del self.typing_status[user_id][conversation_key]
        # Notify other users
        if is_group:
            # Broadcast typing status to all online users
            for uid, client_socket in self.clients.items():
                if uid != user_id:
                    self._send_message(client_socket, {"type": "typing_status",
                        "user": self.db._user_to_dict(self.db.get_user_by_id(user_id)),
                        "is_typing": False,
                        "is_group": True})
        else:
            # Send to specific user
            other_user = self.db.get_user_by_username(other_username)
            if other_user and other_user.id in self.clients:
                self._send_message(self.clients[other_user.id], {
                    "type": "typing_status",
                    "user": self.db._user_to_dict(self.db.get_user_by_id(user_id)),
                    "is_typing": False,
                    "is_group": False})
        return {"success": True}
    def _handle_update_status(self, message: dict) -> dict:
        """Cập nhật trạng thái user"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        status = message.get('status', 'online')
        status_message = message.get('status_message')
        self.db.update_user_status(user_id, status, status_message)
        # Broadcast status change
        self._broadcast_user_status(user_id, status)
        return {"success": True, "message": "Status updated"}
    def _handle_search_messages(self, message: dict) -> dict:
        """Tìm kiếm tin nhắn và trả về với type 'search_results'."""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        query = message.get('query', '')
        limit = message.get('limit', 20)
        messages = self.db.search_messages(user_id, query, limit)
        return {
            "success": True,
            "messages": messages,
            "query": query # Trả lại cả query để hiển thị trên dialog
        }
    def _handle_delete_message(self, message: dict) -> dict:
        """Xóa tin nhắn"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        message_id = message.get('message_id')
        if self.db.delete_message(message_id, user_id):
            # Notify other users about message deletion
            self._broadcast_message_deleted(message_id, user_id)
            return {"success": True, "message": "Message deleted"}
        return {"success": False, "error": "Failed to delete message"}
    def _handle_clear_chat(self, message: dict) -> dict:
        """Xóa toàn bộ chat"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)
        if not user_id:
            return {"success": False, "error": "Invalid session"}
        other_username = message.get('other_user')
        other_user = self.db.get_user_by_username(other_username)
        if other_user:
            # Gọi hàm xóa trong DB và kiểm tra kết quả
            if self.db.clear_chat(user_id, other_user.id):
                # Trả về thông báo thành công để client có thể xử lý
                return {
                    "type": "chat_cleared", # Thêm type để client nhận biết
                    "success": True, 
                    "message": "Lịch sử chat đã được xóa vĩnh viễn",
                    "cleared_with_user": other_username # Gửi lại username để client biết đã xóa chat nào
                }
            else:
                return {"success": False, "error": "Lỗi khi xóa dữ liệu trên server"}
        return {"success": False, "error": "User not found"}
    def _handle_upload_avatar(self, message: dict) -> dict:
        """Upload avatar"""
        session_token = message.get('session_token')
        user_id = self.sessions.get(session_token)  
        if not user_id:
            return {"success": False, "error": "Invalid session"}    
        avatar_data_b64 = message.get('avatar_data')     
        try:
            avatar_data = base64.b64decode(avatar_data_b64)           
            # Check file size (max 1MB for avatar)
            if len(avatar_data) > 1024 * 1024:
                return {"success": False, "error": "Avatar too large (max 1MB)"}           
            self.db.update_user_avatar(user_id, avatar_data)            
            # Broadcast avatar update
            self._broadcast_user_status(user_id, None)  # Will include new avatar          
            return {"success": True, "message": "Avatar updated"}           
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}    
    def _handle_disconnect(self, user_id: int):
        """Xử lý khi user disconnect"""
        # Set user offline
        self.db.update_user_status(user_id, "offline")        
        # Remove from clients
        if user_id in self.clients:
            del self.clients[user_id]        
        # Remove from typing status
        if user_id in self.typing_status:
            del self.typing_status[user_id]        
        # Broadcast offline status
        self._broadcast_user_status(user_id, "offline")
    def _broadcast_message(self, message, exclude_user_id: int = None):
        """Broadcast tin nhắn đến các client phù hợp."""
        # Chỉ broadcast tin nhắn nhóm (group_id không NULL)
        if not message.group_id:
            return
        message_data = {
            "type": "new_message",
            "message": self.db._message_to_dict(message)
        }        
        print(f"Broadcasting group message id {message.id} from user {message.sender_id}")
        for user_id, client_socket in self.clients.copy().items():
            if user_id != exclude_user_id:
                try:
                    self._send_message(client_socket, message_data)
                except Exception as e:
                    print(f"Error broadcasting to user {user_id}, removing. Error: {e}")
                    self._handle_disconnect(user_id) # Xử lý disconnect nếu không gửi được    
    def _broadcast_user_status(self, user_id: int, status: str = None):
        """Broadcast trạng thái user"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return       
        status_data = {
            "type": "user_status",
            "user": self.db._user_to_dict(user)
        }       
        for uid, client_socket in self.clients.copy().items():
            if uid != user_id:
                try:
                    self._send_message(client_socket, status_data)
                except:
                    # Remove disconnected client
                    if uid in self.clients:
                        del self.clients[uid]    
    def _broadcast_message_deleted(self, message_id: int, user_id: int):
        """Broadcast tin nhắn bị xóa"""
        delete_data = {
            "type": "message_deleted",
            "message_id": message_id,
            "deleted_by": user_id
        }       
        for uid, client_socket in self.clients.copy().items():
            try:
                self._send_message(client_socket, delete_data)
            except:
                # Remove disconnected client
                if uid in self.clients:
                    del self.clients[uid]   
    def _send_message(self, client_socket: socket.socket, message: dict):
        """Gửi tin nhắn đến client và in ra để gỡ lỗi."""
        try:
            # In ra gói tin đầy đủ trước khi gửi
            print(f"DEBUG SERVER SEND -> TO {client_socket.getpeername()}: {json.dumps(message)}")
            
            data = json.dumps(message, ensure_ascii=False).encode('utf-8')
            client_socket.send(data)
        except Exception as e:
            print(f"❌ Lỗi khi gửi tin nhắn: {e}")
            raise
    def _send_error(self, client_socket: socket.socket, error_message: str):
        """Gửi thông báo lỗi đến client"""
        error_data = {"success": False, "error": error_message}
        self._send_message(client_socket, error_data)    
    def _cleanup_thread(self):
        """Thread cleanup định kỳ"""
        while self.running:
            try:
                # Cleanup expired sessions
                self.db.cleanup_expired_sessions()                
                # Cleanup old typing status
                current_time = time.time()
                for user_id in list(self.typing_status.keys()):
                    for conv_key in list(self.typing_status[user_id].keys()):
                        if current_time - self.typing_status[user_id][conv_key] > 10:
                            del self.typing_status[user_id][conv_key]                    
                    if not self.typing_status[user_id]:
                        del self.typing_status[user_id]                
                # Sleep for 5 minutes
                time.sleep(300)                
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
                time.sleep(60)
def main():
    """Main function để chạy server"""
    import signal
    import sys   
    # Tạo server instance
    server = ChatServer(host='0.0.0.0', port=12345)   
    # Handle Ctrl+C
    
    def signal_handler(sig, frame):
        print("\n🛑 Received interrupt signal")
        server.stop()
        sys.exit(0)   
    signal.signal(signal.SIGINT, signal_handler)    
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
    except Exception as e:
        print(f"❌ Server error: {e}")
        server.stop()
if __name__ == "__main__":
    main()
