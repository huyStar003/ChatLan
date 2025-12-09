"""User data model."""
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime


@dataclass
class User:
    """Represents a user."""
    
    id: int
    username: str
    display_name: str
    email: Optional[str] = None
    avatar: Optional[bytes] = None
    status: str = "offline"
    status_message: Optional[str] = None
    is_online: bool = False
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """
        Create User instance from dictionary.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            User instance
        """
        # Parse timestamps
        last_seen = None
        if data.get('last_seen'):
            last_seen_str = data['last_seen']
            if isinstance(last_seen_str, str):
                try:
                    if '.' in last_seen_str:
                        last_seen_str = last_seen_str.split('.')[0]
                    last_seen = datetime.fromisoformat(last_seen_str.replace('Z', ''))
                except ValueError:
                    pass
        
        created_at = None
        if data.get('created_at'):
            created_at_str = data['created_at']
            if isinstance(created_at_str, str):
                try:
                    if '.' in created_at_str:
                        created_at_str = created_at_str.split('.')[0]
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', ''))
                except ValueError:
                    pass
        
        # Parse avatar if present
        avatar = None
        if data.get('avatar'):
            import base64
            try:
                avatar = base64.b64decode(data['avatar'])
            except:
                pass
        
        return cls(
            id=data.get('id'),
            username=data.get('username', ''),
            display_name=data.get('display_name', data.get('username', '')),
            email=data.get('email'),
            avatar=avatar,
            status=data.get('status', 'offline'),
            status_message=data.get('status_message'),
            is_online=data.get('is_online', False),
            last_seen=last_seen,
            created_at=created_at
        )
    
    def to_dict(self) -> Dict:
        """
        Convert User to dictionary.
        
        Returns:
            Dictionary representation of the user
        """
        result = {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'status': self.status,
            'is_online': self.is_online,
        }
        
        if self.email:
            result['email'] = self.email
        if self.avatar:
            import base64
            result['avatar'] = base64.b64encode(self.avatar).decode()
        if self.status_message:
            result['status_message'] = self.status_message
        if self.last_seen:
            result['last_seen'] = self.last_seen.isoformat()
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
            
        return result

