"""Message data model."""
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime


@dataclass
class Message:
    """Represents a chat message."""
    
    id: int
    sender_id: int
    content: str
    timestamp: datetime
    message_type: str = "text"
    receiver_id: Optional[int] = None
    group_id: Optional[int] = None
    file_name: Optional[str] = None
    file_data: Optional[bytes] = None
    file_size: Optional[int] = None
    is_read: bool = False
    is_edited: bool = False
    reply_to_id: Optional[int] = None
    client_message_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """
        Create Message instance from dictionary.
        
        Args:
            data: Dictionary containing message data
            
        Returns:
            Message instance
        """
        # Parse timestamp
        timestamp_str = data.get('timestamp', '')
        if isinstance(timestamp_str, str):
            try:
                if '.' in timestamp_str:
                    timestamp_str = timestamp_str.split('.')[0]
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', ''))
            except ValueError:
                timestamp = datetime.now()
        else:
            timestamp = timestamp_str
        
        # Parse file_data if present
        file_data = None
        if data.get('file_data'):
            import base64
            try:
                file_data = base64.b64decode(data['file_data'])
            except:
                pass
        
        sender = data.get('sender', {})
        receiver = data.get('receiver', {})
        
        return cls(
            id=data.get('id'),
            sender_id=sender.get('id') if sender else data.get('sender_id'),
            receiver_id=receiver.get('id') if receiver else data.get('receiver_id'),
            group_id=data.get('group_id'),
            content=data.get('content', ''),
            message_type=data.get('message_type', 'text'),
            timestamp=timestamp,
            file_name=data.get('file_name'),
            file_data=file_data,
            file_size=data.get('file_size'),
            is_read=data.get('is_read', False),
            is_edited=data.get('is_edited', False),
            reply_to_id=data.get('reply_to_id'),
            client_message_id=data.get('client_message_id')
        )
    
    def to_dict(self) -> Dict:
        """
        Convert Message to dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        result = {
            'id': self.id,
            'sender_id': self.sender_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'message_type': self.message_type,
            'is_read': self.is_read,
            'is_edited': self.is_edited,
        }
        
        if self.receiver_id:
            result['receiver_id'] = self.receiver_id
        if self.group_id:
            result['group_id'] = self.group_id
        if self.file_name:
            result['file_name'] = self.file_name
        if self.file_data:
            import base64
            result['file_data'] = base64.b64encode(self.file_data).decode()
        if self.file_size:
            result['file_size'] = self.file_size
        if self.reply_to_id:
            result['reply_to_id'] = self.reply_to_id
        if self.client_message_id:
            result['client_message_id'] = self.client_message_id
            
        return result
    
    @property
    def is_group_message(self) -> bool:
        """Check if this is a group message."""
        return self.group_id is not None
    
    @property
    def is_private_message(self) -> bool:
        """Check if this is a private message."""
        return self.receiver_id is not None and self.group_id is None

