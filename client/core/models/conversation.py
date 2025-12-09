"""Conversation data model."""
from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime

from .message import Message
from .user import User


@dataclass
class Conversation:
    """Represents a conversation (private or group)."""
    
    conversation_id: Optional[int] = None
    type: str = "private"  # "private" or "group"
    other_user: Optional[User] = None  # For private conversations
    group_id: Optional[int] = None  # For group conversations
    group_name: Optional[str] = None  # For group conversations
    member_count: Optional[int] = None  # For group conversations
    last_message: Optional[Message] = None
    updated_at: Optional[datetime] = None
    unread_count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Conversation':
        """
        Create Conversation instance from dictionary.
        
        Args:
            data: Dictionary containing conversation data
            
        Returns:
            Conversation instance
        """
        # Parse updated_at
        updated_at = None
        if data.get('updated_at'):
            updated_at_str = data['updated_at']
            if isinstance(updated_at_str, str):
                try:
                    if '.' in updated_at_str:
                        updated_at_str = updated_at_str.split('.')[0]
                    updated_at = datetime.fromisoformat(updated_at_str.replace('Z', ''))
                except ValueError:
                    pass
        
        # Parse other_user
        other_user = None
        if data.get('other_user'):
            from .user import User
            other_user = User.from_dict(data['other_user'])
        
        # Parse last_message
        last_message = None
        if data.get('last_message'):
            from .message import Message
            last_message = Message.from_dict(data['last_message'])
        
        return cls(
            conversation_id=data.get('conversation_id'),
            type=data.get('type', 'private'),
            other_user=other_user,
            group_id=data.get('group_id'),
            group_name=data.get('group_name'),
            member_count=data.get('member_count'),
            last_message=last_message,
            updated_at=updated_at,
            unread_count=data.get('unread_count', 0)
        )
    
    def to_dict(self) -> Dict:
        """
        Convert Conversation to dictionary.
        
        Returns:
            Dictionary representation of the conversation
        """
        result = {
            'type': self.type,
            'unread_count': self.unread_count,
        }
        
        if self.conversation_id:
            result['conversation_id'] = self.conversation_id
        if self.other_user:
            result['other_user'] = self.other_user.to_dict()
        if self.group_id:
            result['group_id'] = self.group_id
        if self.group_name:
            result['group_name'] = self.group_name
        if self.member_count is not None:
            result['member_count'] = self.member_count
        if self.last_message:
            result['last_message'] = self.last_message.to_dict()
        if self.updated_at:
            result['updated_at'] = self.updated_at.isoformat()
            
        return result
    
    @property
    def display_name(self) -> str:
        """Get display name for the conversation."""
        if self.type == "group":
            return self.group_name or f"Group {self.group_id}"
        elif self.other_user:
            return self.other_user.display_name
        return "Unknown"
    
    @property
    def is_group(self) -> bool:
        """Check if this is a group conversation."""
        return self.type == "group"
    
    @property
    def is_private(self) -> bool:
        """Check if this is a private conversation."""
        return self.type == "private"

