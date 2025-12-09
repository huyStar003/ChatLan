from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, LargeBinary, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref # Đảm bảo có backref
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib
Base = declarative_base()
group_members = Table('group_members', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)



class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(64), nullable=False)  # SHA-256 hash
    display_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    avatar = Column(LargeBinary, nullable=True)
    status = Column(String(20), default="offline")  # online, away, busy, offline
    status_message = Column(String(200), nullable=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    # Relationships
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    groups = relationship("Group", secondary=group_members, back_populates="members")
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    def verify_password(self, password):
        """
        Xác thực password với backward compatibility.
        - User mới: password plaintext được hash một lần ở server
        - User cũ (legacy): password đã được double-hash (client hash -> server hash lại)
        
        Logic: Hash password một lần và so sánh. Nếu không match và password là hash string
        (64 hex chars từ client cũ), thử hash lại một lần nữa để so sánh với DB double-hash.
        """
        # Hash password một lần (cho user mới hoặc plaintext từ client mới)
        single_hash = self.hash_password(password)
        if self.password_hash == single_hash:
            return True
        
        # Backward compatibility: Nếu password là hash string từ client cũ (64 hex chars),
        # hash lại một lần nữa để so sánh với DB (đã là double-hash)
        if len(password) == 64 and all(c in '0123456789abcdef' for c in password.lower()):
            double_hash = self.hash_password(password)
            if self.password_hash == double_hash:
                return True
        
        return False
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Mối quan hệ với người tạo
    creator = relationship("User")
    # Mối quan hệ với các thành viên
    members = relationship("User", secondary=group_members, back_populates="groups")
    # Mối quan hệ với tin nhắn của nhóm
    messages = relationship("Message", back_populates="group")
class Message(Base):
    __tablename__ = "messages"   
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_message_id = Column(String(100), nullable=True, index=True) # THÊM DÒNG NÀY
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # None for group messages
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, image, file, emoji
    file_name = Column(String(255), nullable=True)
    file_data = Column(LargeBinary, nullable=True)
    file_size = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    is_read = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)   
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    group = relationship("Group", back_populates="messages")
    reply_to = relationship("Message", remote_side=[id])
class Conversation(Base):
    __tablename__ = "conversations"   
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=func.now())   
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    last_message = relationship("Message", foreign_keys=[last_message_id])
class UserSession(Base):
    __tablename__ = "user_sessions"    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(64), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)   
    # Relationships
    user = relationship("User")
class TypingStatus(Base):
    __tablename__ = "typing_status"    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    is_typing = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.now())   
    # Relationships
    user = relationship("User")
    conversation = relationship("Conversation")
