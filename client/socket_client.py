import socket
import json
import threading
import time
from typing import Optional, Callable, Dict, Any,List 
from PyQt5.QtCore import QObject, pyqtSignal
class SocketClient(QObject):
    # Signals
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    message_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.socket: Optional[socket.socket] = None
        self.host = 'localhost'  # Default to localhost for consistency with UI
        self.port = 12345
        self.session_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.connected_flag = False
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        self.reconnect_thread: Optional[threading.Thread] = None
        self.auto_reconnect = True
        self.reconnect_delay = 5  # seconds
    def connect_to_server(self, host: str, port: int) -> bool:
        """Kết nối đến server"""
        self.host = host
        self.port = port
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)  # 30 second timeout
            self.socket.connect((host, port))            
            self.connected_flag = True
            self.running = True            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()            
            self.connected.emit()
            return True            
        except Exception as e:
            self.error_occurred.emit(f"Không thể kết nối đến server: {str(e)}")
            return False   
    def disconnect(self):
        """Ngắt kết nối"""
        self.running = False
        self.connected_flag = False
        self.auto_reconnect = False       
        if self.socket:
            try:
                # Send logout if logged in
                if self.session_token:
                    self.send_message({
                        'type': 'logout',
                        'session_token': self.session_token
                    })             
                self.socket.close()
            except:
                pass    
            self.socket = None
        self.session_token = None
        self.user_id = None
        self.disconnected.emit()
    def send_message(self, message: dict) -> bool:
        """Gửi tin nhắn đến server"""
        if not self.connected_flag or not self.socket:
            print(f"DEBUG: Cannot send message - connected_flag={self.connected_flag}, socket={self.socket}")
            self.error_occurred.emit("Không có kết nối đến server")
            return False
        try:
            data = json.dumps(message, ensure_ascii=False).encode('utf-8')
            print(f"DEBUG CLIENT SEND -> RAW DATA: {data.decode('utf-8')}")
            # Use sendall to ensure all data is sent
            self.socket.sendall(data)
            print(f"DEBUG: Successfully sent {len(data)} bytes")
            return True
        except Exception as e:
            print(f"DEBUG: Error sending message: {e}")
            self.error_occurred.emit(f"Lỗi gửi tin nhắn: {str(e)}")
            self._handle_connection_lost()
            return False
    def register(self, username: str, password: str, display_name: str = "", email: str = "") -> bool:
        """Đăng ký tài khoản"""
        return self.send_message({
            'type': 'register',
            'username': username,
            'password': password,
            'display_name': display_name,
            'email': email
        })
    def login(self, username: str, password: str) -> bool:
        """Đăng nhập"""
        return self.send_message({
            'type': 'login',
            'username': username,
            'password': password
        })
    def send_group_message(self, group_id: int, content: str, message_type: str = 'text', client_message_id: str = None) -> bool:
        """Gửi tin nhắn đến một nhóm cụ thể."""
        if not self.session_token:
            return False
        message = {
            'type': 'send_message', # Vẫn là 'send_message' theo logic server
            'session_token': self.session_token,
            'group_id': group_id, # Thêm group_id
            'content': content,
            'message_type': message_type
        }
        if client_message_id:
            message['client_message_id'] = client_message_id
        return self.send_message(message)
    def send_private_message(self, receiver: str, content: str, message_type: str = 'text', reply_to_id: int = None, client_message_id: str = None) -> bool:
        if not self.session_token:
            return False
        message = {
            'type': 'send_private_message',
            'session_token': self.session_token,
            'receiver': receiver,
            'content': content,
            'message_type': message_type
        }
        if reply_to_id:
            message['reply_to_id'] = reply_to_id
        if client_message_id: # THÊM KHỐI IF NÀY
            message['client_message_id'] = client_message_id
        return self.send_message(message)
    def upload_file(self, file_data: bytes, file_name: str, receiver: str = None, group_id: int = None) -> bool:
        """Upload file đến chat riêng hoặc nhóm."""
        if not self.session_token:
            return False
        import base64
        message = {
            'type': 'upload_file',
            'session_token': self.session_token,
            'file_name': file_name,
            'file_data': base64.b64encode(file_data).decode('utf-8'),
        }
        if group_id:
            message['group_id'] = group_id
        elif receiver:
            message['receiver'] = receiver
        else:
            # Mặc định gửi vào nhóm chung nếu không có đích cụ thể
            # Hoặc bạn có thể trả về lỗi ở đây
            return False 
        
        return self.send_message(message)
    def get_contacts(self) -> bool:
        """Lấy danh sách liên hệ"""
        if not self.session_token:
            return False
        return self.send_message({
            'type': 'get_contacts',
            'session_token': self.session_token
        })
    def get_conversations(self) -> bool:
        """Lấy danh sách hội thoại"""
        if not self.session_token:
            return False
        return self.send_message({
            'type': 'get_conversations',
            'session_token': self.session_token
        })
    def get_messages(self, other_user: str = None, group_id: int = None, limit: int = 50, offset: int = 0) -> bool:
        """Lấy tin nhắn từ chat riêng hoặc chat nhóm."""
        if not self.session_token:
            return False
        
        message = {
            'type': 'get_messages',
            'session_token': self.session_token,
            'limit': limit,
            'offset': offset
        }
        # Thêm tham số phù hợp vào yêu cầu
        if group_id:
            message['group_id'] = group_id
        elif other_user:
            message['other_user'] = other_user
        
        return self.send_message(message)
    def mark_messages_read(self, sender: str) -> bool:
        """Đánh dấu tin nhắn đã đọc"""
        if not self.session_token:
            return False
        return self.send_message({
            'type': 'mark_read',
            'session_token': self.session_token,
            'sender': sender
        })
    def start_typing(self, other_user: str = None, is_group: bool = False) -> bool:
        """Bắt đầu gõ"""
        if not self.session_token:
            return False
        message = {
            'type': 'typing_start',
            'session_token': self.session_token,
            'is_group': is_group
        }
        if other_user:
            message['other_user'] = other_user
        return self.send_message(message)
    def stop_typing(self, other_user: str = None, is_group: bool = False) -> bool:
        """Dừng gõ"""
        if not self.session_token:
            return False
        message = {
            'type': 'typing_stop',
            'session_token': self.session_token,
            'is_group': is_group
        }
        if other_user:
            message['other_user'] = other_user
        return self.send_message(message)
    def update_status(self, status: str, status_message: str = None) -> bool:
        """Cập nhật trạng thái"""
        if not self.session_token:
            return False
        message = {
            'type': 'update_status',
            'session_token': self.session_token,
            'status': status
        }
        if status_message:
            message['status_message'] = status_message
        return self.send_message(message)
    def search_messages(self, query: str, limit: int = 20) -> bool:
        """Tìm kiếm tin nhắn"""
        if not self.session_token:
            return False
        
        return self.send_message({
            'type': 'search_messages',
            'session_token': self.session_token,
            'query': query,
            'limit': limit
        })
    def delete_message(self, message_id: int) -> bool:
        """Xóa tin nhắn"""
        if not self.session_token:
            return False
        return self.send_message({
            'type': 'delete_message',
            'session_token': self.session_token,
            'message_id': message_id
        })
    def clear_chat(self, other_user: str) -> bool:
        """Xóa toàn bộ chat"""
        if not self.session_token:
            return False
        
        return self.send_message({
            'type': 'clear_chat',
            'session_token': self.session_token,
            'other_user': other_user
        })
    def upload_avatar(self, avatar_data: bytes) -> bool:
        """Upload avatar"""
        if not self.session_token:
            return False
        import base64
        return self.send_message({
            'type': 'upload_avatar',
            'session_token': self.session_token,
            'avatar_data': base64.b64encode(avatar_data).decode('utf-8')
        })
    def _receive_messages(self):
        """Thread nhận tin nhắn từ server"""
        buffer = ""
        while self.running and self.connected_flag:
            try:
                if not self.socket:
                    break           
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                print(f"DEBUG CLIENT RECV <- RAW DATA: {data}")
                buffer += data          
                # Xử lý tất cả các gói JSON hoàn chỉnh có trong buffer
                while True:
                    try:
                        # Tìm vị trí kết thúc của một đối tượng JSON
                        # Giả định rằng mỗi gói JSON là một dictionary, bắt đầu bằng '{' và kết thúc bằng '}'
                        # Đây là một giả định đơn giản, có thể cần cải tiến nếu server gửi các loại JSON khác
                        start_index = buffer.find('{')
                        if start_index == -1:
                            # Không có JSON object nào trong buffer, xóa buffer và đợi dữ liệu mới
                            buffer = ""
                            break
                        # Tìm dấu ngoặc đóng tương ứng
                        brace_count = 0
                        end_index = -1
                        in_string = False
                        for i in range(start_index, len(buffer)):
                            char = buffer[i]
                            if char == '"':
                                # Bỏ qua các dấu ngoặc trong chuỗi
                                if i > 0 and buffer[i-1] != '\\':
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
                            
                            # Xử lý message
                            if message.get('type') == 'login' or (message.get('success') and 'session_token' in message):
                                self.session_token = message.get('session_token')
                                self.user_id = message.get('user_id')
                            self.message_received.emit(message)
                            
                            # Xóa gói JSON đã xử lý khỏi buffer
                            buffer = buffer[end_index + 1:]
                        else:
                            # Chưa có gói JSON hoàn chỉnh, đợi thêm dữ liệu
                            break          
                    except json.JSONDecodeError:
                        # Nếu có lỗi, có thể gói JSON chưa hoàn chỉnh hoặc bị lỗi
                        # Chúng ta sẽ đợi thêm dữ liệu
                        print(f"JSONDecodeError, buffer hiện tại: {buffer}")
                        break # Thoát vòng lặp while True và đợi recv() tiếp
                    except Exception as e:
                        print(f"Lỗi xử lý buffer: {e}")
                        buffer = "" # Xóa buffer để tránh lặp lỗi
                        break 
            except socket.timeout:
                continue
            except ConnectionResetError:
                break
            except Exception as e:
                if self.running:
                    self.error_occurred.emit(f"Lỗi nhận tin nhắn: {str(e)}")
                break
        # Connection lost
        if self.running:
            self._handle_connection_lost()
    def _handle_connection_lost(self):
        """Xử lý mất kết nối"""
        self.connected_flag = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None      
        self.disconnected.emit()        
        # Auto reconnect if enabled
        if self.auto_reconnect and self.running:
            self._start_reconnect()   
    def _start_reconnect(self):
        """Bắt đầu quá trình reconnect"""
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return        
        self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self.reconnect_thread.start()   
    def _reconnect_loop(self):
        """Loop reconnect"""
        while self.running and self.auto_reconnect and not self.connected_flag:
            try:
                time.sleep(self.reconnect_delay)                
                if not self.running:
                    break
                self.error_occurred.emit(f"Đang thử kết nối lại đến {self.host}:{self.port}...")
                
                if self.connect_to_server(self.host, self.port):
                    self.error_occurred.emit("Kết nối lại thành công!")
                    break
                else:
                    self.error_occurred.emit(f"Kết nối lại thất bại. Thử lại sau {self.reconnect_delay} giây...")
            except Exception as e:
                self.error_occurred.emit(f"Lỗi reconnect: {str(e)}")
    def is_connected(self) -> bool:
        """Kiểm tra trạng thái kết nối"""
        return self.connected_flag and self.socket is not None
    def is_logged_in(self) -> bool:
        """Kiểm tra đã đăng nhập chưa"""
        return self.session_token is not None
    def create_group(self, group_name: str, member_ids: List[int]) -> bool:
        """Gửi yêu cầu tạo nhóm chat mới."""
        if not self.session_token:
            return False
        
        return self.send_message({
            'type': 'create_group',
            'session_token': self.session_token,
            'group_name': group_name,
            'member_ids': member_ids
        })
    def get_group_members(self, group_id: int) -> bool:
        """Yêu cầu lấy danh sách thành viên của một nhóm."""
        if not self.session_token:
            return False
        return self.send_message({
            'type': 'get_group_members',
            'session_token': self.session_token,
            'group_id': group_id
        })

    def add_group_member(self, group_id: int, member_id: int) -> bool:
        """Yêu cầu thêm thành viên vào nhóm."""
        if not self.session_token:
            return False
        return self.send_message({
            'type': 'add_group_member',
            'session_token': self.session_token,
            'group_id': group_id,
            'member_id': member_id
        })

    def remove_group_member(self, group_id: int, member_id: int) -> bool:
        """Yêu cầu xóa thành viên khỏi nhóm."""
        if not self.session_token:
            return False
        return self.send_message({
            'type': 'remove_group_member',
            'session_token': self.session_token,
            'group_id': group_id,
            'member_id': member_id
        })