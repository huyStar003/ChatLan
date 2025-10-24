from sqlalchemy import create_engine, desc, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from .models import Base, User, Message, Conversation, UserSession, TypingStatus, Group, group_members
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import secrets
import base64
import os
# Thông tin kết nối PostgreSQL
DB_USER = "chat_user"
DB_PASSWORD = "chat_password"
DB_HOST = "192.168.1.20"
DB_PORT = "5432"
DB_NAME = "chat_lan_db"
# Chuỗi kết nối (Connection String) cho PostgreSQL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
class DatabaseManager:
    def __init__(self, database_url: str = DATABASE_URL):
        # Thay đổi trong hàm create_engine
        self.engine = create_engine(
            database_url,
            # Không cần connect_args cho PostgreSQL
            echo=False # Đặt là True nếu muốn xem các câu lệnh SQL được thực thi
            )
        # Tạo tất cả các bảng nếu chúng chưa tồn tại
        Base.metadata.create_all(bind=self.engine)        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()   
    def register_user(self, username: str, password: str, display_name: str = None, email: str = None) -> Tuple[bool, str, Optional[User]]:
        """Đăng ký user mới và tự động thêm vào nhóm chung (ID=1)."""
        try:
            # Validate input
            if len(username) < 3:
                return False, "Tên đăng nhập phải có ít nhất 3 ký tự", None
            if len(password) < 6:
                return False, "Mật khẩu phải có ít nhất 6 ký tự", None
            
            # Check if user exists
            existing_user = self.db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "Tên đăng nhập đã tồn tại", None
                
            # Create new user
            user = User(
                username=username,
                password_hash=User.hash_password(password),
                display_name=display_name or username,
                email=email,
                status="offline")
            self.db.add(user)
            
            # --- LOGIC MỚI: TỰ ĐỘNG THÊM VÀO NHÓM CHUNG ---
            # Tìm nhóm chung (quy ước là nhóm có ID = 1)
            company_group = self.db.query(Group).filter(Group.id == 1).first()
            if company_group:
                print(f"Đang thêm người dùng '{username}' vào nhóm chung '{company_group.name}'...")
                user.groups.append(company_group)
            else:
                print("Cảnh báo: Không tìm thấy nhóm chung (ID=1) để thêm người dùng mới.")
            # ---------------------------------------------

            self.db.commit()
            self.db.refresh(user)
            
            return True, "Đăng ký thành công", user
        except Exception as e:
            self.db.rollback()
            return False, f"Lỗi đăng ký: {str(e)}", None
    def login_user(self, username: str, password: str, ip_address: str = None) -> Tuple[bool, str, Optional[User], Optional[str]]:
        """Đăng nhập user"""
        try:
            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                return False, "Tên đăng nhập không tồn tại", None, None
            if not user.verify_password(password):
                return False, "Mật khẩu không đúng", None, None
            # Update user status
            user.is_online = True
            user.status = "online"
            user.last_seen = datetime.now()
            # Create session token
            session_token = secrets.token_hex(32)
            session = UserSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=ip_address,
                expires_at=datetime.now() + timedelta(days=7))
            self.db.add(session)
            self.db.commit()
            return True, "Đăng nhập thành công", user, session_token
        except Exception as e:
            self.db.rollback()
            return False, f"Lỗi đăng nhập: {str(e)}", None, None
    def logout_user(self, user_id: int, session_token: str = None):
        """Đăng xuất user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_online = False
                user.status = "offline"
                user.last_seen = datetime.now()
            # Deactivate session
            if session_token:
                session = self.db.query(UserSession).filter(
                    UserSession.session_token == session_token
                ).first()
                if session:
                    session.is_active = False
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error logging out user: {e}")
    def verify_session(self, session_token: str) -> Optional[User]:
        """Xác thực session token"""
        try:
            session = self.db.query(UserSession).filter(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.now())
            ).first()
            if session:
                return session.user
            return None
        except Exception as e:
            print(f"Error verifying session: {e}")
            return None
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Lấy user theo username"""
        return self.db.query(User).filter(User.username == username).first()
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Lấy user theo ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    def update_user_status(self, user_id: int, status: str, status_message: str = None):
        """Cập nhật trạng thái user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.status = status
                user.is_online = status != "offline"
                if status_message is not None:
                    user.status_message = status_message
                user.last_seen = datetime.now()
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error updating user status: {e}")
    def get_online_users(self) -> List[Dict]:
        """Lấy danh sách user online"""
        try:
            users = self.db.query(User).filter(User.is_online == True).all()
            return [self._user_to_dict(user) for user in users]
        except Exception as e:
            print(f"Error getting online users: {e}")
            return []
    def get_all_users(self, exclude_user_id: int = None) -> List[Dict]:
        """Lấy tất cả users"""
        try:
            query = self.db.query(User)
            if exclude_user_id:
                query = query.filter(User.id != exclude_user_id)
            
            users = query.all()
            return [self._user_to_dict(user) for user in users]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    def save_message(self, sender_id: int, receiver_id: int = None, group_id: int = None, content: str = "", 
                 message_type: str = "text", file_name: str = None, 
                 file_data: bytes = None, reply_to_id: int = None, 
                 client_message_id: str = None) -> Optional[Message]:
        """Lưu tin nhắn (phiên bản sửa lỗi logic)."""
        try:
            if group_id:
                message = Message(
                    sender_id=sender_id,
                    group_id=group_id,
                    receiver_id=None, # Đảm bảo receiver_id là NULL
                    content=content,
                    message_type=message_type,
                    file_name=file_name,
                    file_data=file_data,
                    file_size=len(file_data) if file_data else None,
                    reply_to_id=reply_to_id,
                    client_message_id=client_message_id
                )
            elif receiver_id:
                message = Message(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    group_id=None, # Đảm bảo group_id là NULL
                    content=content,
                    message_type=message_type,
                    file_name=file_name,
                    file_data=file_data,
                    file_size=len(file_data) if file_data else None,
                    reply_to_id=reply_to_id,
                    client_message_id=client_message_id
                )
            else:
                return None

            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            if receiver_id:
                self._update_conversation(sender_id, receiver_id, message.id)
            
            return message
        except Exception as e:
            self.db.rollback()
            print(f"[DB-SAVE] Lỗi khi lưu tin nhắn: {e}")
            return None
    def get_messages(self, user_id: int, other_user_id: int = None, group_id: int = None,
                 limit: int = 50, offset: int = 0) -> List[Dict]:
        """Lấy tin nhắn (sửa lỗi logic truy vấn cho nhóm)."""
        try:
            # Buộc SQLAlchemy đọc lại dữ liệu từ DB, tránh lỗi cache session
            self.db.expire_all()

            messages = []
            if group_id:
                print(f"[DB-GET] Getting messages for GROUP ID: {group_id}")
                
                # Lấy đối tượng Group từ DB
                group = self.db.query(Group).filter(Group.id == group_id).first()
                if not group:
                    print(f"[DB-GET] Không tìm thấy nhóm {group_id}")
                    return []

                # Kiểm tra tư cách thành viên
                is_member = any(member.id == user_id for member in group.members)
                if not is_member:
                    print(f"[DB-GET] User {user_id} không phải thành viên nhóm {group_id}.")
                    return []

                # SỬA LỖI TRUY VẤN: Truy vấn thông qua Message.group_id
                messages = self.db.query(Message).filter(
                    Message.group_id == group_id
                ).order_by(Message.id.desc()).limit(limit).all()

            elif other_user_id:
                print(f"[DB-GET] Getting messages between USER ID: {user_id} and {other_user_id}")
                messages = self.db.query(Message).filter(
                    and_(
                        Message.group_id.is_(None),
                        or_(
                            and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                            and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
                        )
                    )
                ).order_by(Message.id.desc()).limit(limit).all()

            print(f"[DB-GET] Found {len(messages)} messages.")
            return [self._message_to_dict(msg) for msg in reversed(messages)]
        except Exception as e:
            print(f"[DB-GET] Lỗi khi lấy tin nhắn: {e}")
            import traceback
            traceback.print_exc() # In ra traceback đầy đủ để gỡ lỗi
            return []
    def get_conversations(self, user_id: int) -> List[Dict]:
        """Lấy danh sách hội thoại, bao gồm cả chat riêng và chat nhóm."""
        try:
            # Lấy các cuộc trò chuyện cá nhân
            private_convs = self.db.query(Conversation).filter(
                or_(Conversation.user1_id == user_id, Conversation.user2_id == user_id)
            ).order_by(desc(Conversation.updated_at)).all()
            
            result = []
            for conv in private_convs:
                other_user = conv.user2 if conv.user1_id == user_id else conv.user1
                unread_count = self.get_unread_count(user_id, other_user.id)
                
                result.append({
                    "type": "private", # Thêm loại hội thoại
                    "conversation_id": conv.id,
                    "other_user": self._user_to_dict(other_user),
                    "last_message": self._message_to_dict(conv.last_message) if conv.last_message else None,
                    "updated_at": conv.updated_at.isoformat(),
                    "unread_count": unread_count
                })

            # Lấy các nhóm mà người dùng là thành viên
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                for group in user.groups:
                    # Tìm tin nhắn cuối cùng của nhóm
                    last_msg = self.db.query(Message).filter(Message.group_id == group.id).order_by(desc(Message.timestamp)).first()
                    
                    result.append({
                        "type": "group", # Thêm loại hội thoại
                        "group_id": group.id,
                        "group_name": group.name,
                        "member_count": len(group.members),
                        "last_message": self._message_to_dict(last_msg) if last_msg else None,
                        "updated_at": last_msg.timestamp.isoformat() if last_msg else group.created_at.isoformat()
                    })
            
            # Sắp xếp lại toàn bộ danh sách dựa trên thời gian cập nhật mới nhất
            result.sort(key=lambda x: x['updated_at'], reverse=True)

            return result
        except Exception as e:
            print(f"Lỗi khi lấy danh sách hội thoại: {e}")
            return []
    def mark_messages_as_read(self, user_id: int, sender_id: int):
        """Đánh dấu tin nhắn đã đọc"""
        try:
            self.db.query(Message).filter(
                and_(
                    Message.sender_id == sender_id,
                    Message.receiver_id == user_id,
                    Message.is_read == False
                )
            ).update({"is_read": True})
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error marking messages as read: {e}")
    def get_unread_count(self, user_id: int, sender_id: int = None) -> int:
        """Lấy số tin nhắn chưa đọc"""
        try:
            query = self.db.query(Message).filter(
                and_(
                    Message.receiver_id == user_id,
                    Message.is_read == False
                )
            )
            if sender_id:
                query = query.filter(Message.sender_id == sender_id)
            return query.count()
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
    def search_messages(self, user_id: int, query: str, limit: int = 20) -> List[Dict]:
        """Tìm kiếm tin nhắn"""
        try:
            messages = self.db.query(Message).filter(
                and_(
                    or_(
                        Message.sender_id == user_id,
                        Message.receiver_id == user_id,
                        Message.is_group_message == True
                    ),
                    Message.content.contains(query)
                )
            ).order_by(desc(Message.timestamp)).limit(limit).all()
            return [self._message_to_dict(msg) for msg in messages]
        except Exception as e:
            print(f"Error searching messages: {e}")
            return []
    def update_typing_status(self, user_id: int, conversation_id: int = None, is_typing: bool = False):
        """Cập nhật trạng thái đang gõ"""
        try:
            typing_status = self.db.query(TypingStatus).filter(
                and_(
                    TypingStatus.user_id == user_id,
                    TypingStatus.conversation_id == conversation_id
                )
            ).first()
            if typing_status:
                typing_status.is_typing = is_typing
                typing_status.updated_at = datetime.now()
            else:
                typing_status = TypingStatus(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    is_typing=is_typing
                )
                self.db.add(typing_status)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error updating typing status: {e}")
    def get_typing_users(self, conversation_id: int = None, exclude_user_id: int = None) -> List[Dict]:
        """Lấy danh sách user đang gõ"""
        try:
            query = self.db.query(TypingStatus).filter(
                and_(
                    TypingStatus.is_typing == True,
                    TypingStatus.updated_at > datetime.now() - timedelta(seconds=10)
                )
            )
            if conversation_id:
                query = query.filter(TypingStatus.conversation_id == conversation_id)
            if exclude_user_id:
                query = query.filter(TypingStatus.user_id != exclude_user_id)
            typing_statuses = query.all()
            return [self._user_to_dict(ts.user) for ts in typing_statuses]
        except Exception as e:
            print(f"Error getting typing users: {e}")
            return []
    def update_user_avatar(self, user_id: int, avatar_data: bytes):
        """Cập nhật avatar user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.avatar = avatar_data
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error updating avatar: {e}")
    def delete_message(self, message_id: int, user_id: int) -> bool:
        """Xóa tin nhắn"""
        try:
            message = self.db.query(Message).filter(
                and_(
                    Message.id == message_id,
                    Message.sender_id == user_id
                )
            ).first()
            
            if message:
                self.db.delete(message)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting message: {e}")
            return False
    def clear_chat(self, user_id: int, other_user_id: int) -> bool:
        """Xóa toàn bộ chat giữa hai người dùng một cách an toàn."""
        try:
            # --- BƯỚC 1: Tìm và cập nhật hội thoại liên quan TRƯỚC ---
            conversation = self.db.query(Conversation).filter(
                or_(
                    and_(Conversation.user1_id == user_id, Conversation.user2_id == other_user_id),
                    and_(Conversation.user1_id == other_user_id, Conversation.user2_id == user_id)
                )
            ).first()
            # Nếu có hội thoại, cập nhật last_message_id thành None
            if conversation:
                print(f"Đang cập nhật hội thoại ID {conversation.id}, đặt last_message_id thành NULL.")
                conversation.last_message_id = None
                self.db.commit() # Commit thay đổi này trước
            # --- BƯỚC 2: Bây giờ mới tiến hành xóa tin nhắn ---
            messages_to_delete = self.db.query(Message).filter(
                and_(
                    Message.is_group_message == False,
                    or_(
                        and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                        and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
                    )
                )
            )
            deleted_count = messages_to_delete.delete(synchronize_session=False)
            self.db.commit()
            print(f"Đã xóa thành công {deleted_count} tin nhắn giữa user {user_id} và {other_user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Lỗi khi xóa cuộc trò chuyện: {e}")
            return False
    def _update_conversation(self, user1_id: int, user2_id: int, last_message_id: int):
        """Cập nhật hội thoại"""
        try:
            conversation = self.db.query(Conversation).filter(
                or_(
                    and_(Conversation.user1_id == user1_id, Conversation.user2_id == user2_id),
                    and_(Conversation.user1_id == user2_id, Conversation.user2_id == user1_id)
                )
            ).first()
            if conversation:
                conversation.last_message_id = last_message_id
                conversation.updated_at = datetime.now()
            else:
                conversation = Conversation(
                    user1_id=min(user1_id, user2_id),
                    user2_id=max(user1_id, user2_id),
                    last_message_id=last_message_id
                )
                self.db.add(conversation)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error updating conversation: {e}")
    def _user_to_dict(self, user: User) -> Dict:
        """Convert User object to dictionary"""
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "status": user.status,
            "status_message": user.status_message,
            "is_online": user.is_online,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
            "avatar": base64.b64encode(user.avatar).decode() if user.avatar else None,
            "created_at": user.created_at.isoformat()
        }
    def _message_to_dict(self, message: Message) -> Dict:
        """Convert Message object to dictionary (đã cập nhật để hỗ trợ group_id)."""
        if not message: return None
        return {
            "id": message.id,
            "client_message_id": message.client_message_id,
            "sender": self._user_to_dict(message.sender),
            "receiver": self._user_to_dict(message.receiver) if message.receiver else None,
            "group_id": message.group_id, # <<< THÊM DÒNG NÀY
            "content": message.content,
            "message_type": message.message_type,
            "file_name": message.file_name,
            "file_data": base64.b64encode(message.file_data).decode() if message.file_data else None,
            "file_size": message.file_size,
            "timestamp": message.timestamp.isoformat(),
            "is_read": message.is_read,
            "is_edited": message.is_edited,
            "reply_to_id": message.reply_to_id
        }
    def cleanup_expired_sessions(self):
        """Xóa session hết hạn"""
        try:
            self.db.query(UserSession).filter(
                UserSession.expires_at < datetime.now()
            ).delete()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error cleaning up sessions: {e}")
    def close(self):
        """Đóng kết nối database"""
        self.db.close()
    def create_chat_group(self, name: str, creator_id: int, member_ids: List[int]) -> Tuple[bool, str, Optional[Group]]:
        """Tạo một nhóm chat mới."""
        try:
            if not name:
                return False, "Tên nhóm không được để trống.", None
            
            # Lấy các đối tượng User từ DB
            creator = self.db.query(User).filter(User.id == creator_id).first()
            if not creator:
                return False, "Người tạo không tồn tại.", None

            # Đảm bảo người tạo cũng là thành viên
            all_member_ids = set(member_ids)
            all_member_ids.add(creator_id)

            members = self.db.query(User).filter(User.id.in_(all_member_ids)).all()
            if len(members) != len(all_member_ids):
                return False, "Một hoặc nhiều thành viên không tồn tại.", None

            # Tạo nhóm mới
            new_group = Group(name=name, creator_id=creator_id)
            new_group.members.extend(members)
            
            self.db.add(new_group)
            self.db.commit()
            self.db.refresh(new_group)
            
            return True, "Tạo nhóm thành công", new_group
        except Exception as e:
            self.db.rollback()
            print(f"Lỗi khi tạo nhóm: {e}")
            return False, f"Lỗi server: {e}", None
    def add_member_to_group(self, group_id: int, actor_id: int, member_id_to_add: int) -> Tuple[bool, str]:
        """Thêm một thành viên mới vào nhóm."""
        try:
            group = self.db.query(Group).filter(Group.id == group_id).first()
            if not group:
                return False, "Nhóm không tồn tại."
            
            # Chỉ người tạo nhóm mới có quyền thêm thành viên
            if group.creator_id != actor_id:
                return False, "Bạn không có quyền thêm thành viên vào nhóm này."

            member_to_add = self.db.query(User).filter(User.id == member_id_to_add).first()
            if not member_to_add:
                return False, "Người dùng này không tồn tại."

            # Kiểm tra xem người dùng đã ở trong nhóm chưa
            if member_to_add in group.members:
                return False, "Người dùng này đã là thành viên của nhóm."

            group.members.append(member_to_add)
            self.db.commit()
            print(f"User {member_id_to_add} đã được thêm vào nhóm {group_id} bởi {actor_id}.")
            return True, "Thêm thành viên thành công."
        except Exception as e:
            self.db.rollback()
            print(f"Lỗi khi thêm thành viên: {e}")
            return False, "Lỗi server khi thêm thành viên."

    def remove_member_from_group(self, group_id: int, actor_id: int, member_id_to_remove: int) -> Tuple[bool, str]:
        """Xóa một thành viên khỏi nhóm."""
        try:
            group = self.db.query(Group).filter(Group.id == group_id).first()
            if not group:
                return False, "Nhóm không tồn tại."

            # Chỉ người tạo nhóm mới có quyền xóa
            if group.creator_id != actor_id:
                return False, "Bạn không có quyền xóa thành viên khỏi nhóm này."
            
            # Không cho phép nhóm trưởng tự xóa mình
            if actor_id == member_id_to_remove:
                return False, "Nhóm trưởng không thể rời khỏi nhóm."

            member_to_remove = self.db.query(User).filter(User.id == member_id_to_remove).first()
            if not member_to_remove:
                return False, "Người dùng này không tồn tại."

            if member_to_remove not in group.members:
                return False, "Người dùng này không phải là thành viên của nhóm."

            group.members.remove(member_to_remove)
            self.db.commit()
            print(f"User {member_id_to_remove} đã bị xóa khỏi nhóm {group_id} bởi {actor_id}.")
            return True, "Xóa thành viên thành công."
        except Exception as e:
            self.db.rollback()
            print(f"Lỗi khi xóa thành viên: {e}")
            return False, "Lỗi server khi xóa thành viên."