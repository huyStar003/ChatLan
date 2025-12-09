"""Message manager for handling message operations."""
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from ..models.message import Message
from ..models.user import User


class MessageManager:
    """Manages message operations and caching."""
    
    def __init__(self, current_user_id: int):
        """
        Initialize message manager.
        
        Args:
            current_user_id: ID of the current user
        """
        self.current_user_id = current_user_id
        self.message_cache: Dict[str, List[Message]] = {}  # Key: conversation_key
    
    def _get_conversation_key(self, group_id: Optional[int] = None, 
                             other_user_id: Optional[int] = None) -> str:
        """
        Generate a unique key for a conversation.
        
        Args:
            group_id: Group ID for group conversations
            other_user_id: Other user ID for private conversations
            
        Returns:
            Unique conversation key
        """
        if group_id:
            return f"group_{group_id}"
        elif other_user_id:
            return f"private_{min(self.current_user_id, other_user_id)}_{max(self.current_user_id, other_user_id)}"
        return "unknown"
    
    def add_message(self, message_data: Dict, 
                   group_id: Optional[int] = None,
                   other_user_id: Optional[int] = None) -> Message:
        """
        Add a new message to cache.
        
        Args:
            message_data: Message data dictionary
            group_id: Group ID if group message
            other_user_id: Other user ID if private message
            
        Returns:
            Message instance
        """
        message = Message.from_dict(message_data)
        key = self._get_conversation_key(group_id, other_user_id)
        
        if key not in self.message_cache:
            self.message_cache[key] = []
        
        # Check if message already exists (avoid duplicates)
        if not any(m.id == message.id for m in self.message_cache[key]):
            self.message_cache[key].append(message)
            # Sort by timestamp
            self.message_cache[key].sort(key=lambda m: m.timestamp)
        
        return message
    
    def update_messages(self, messages_data: List[Dict],
                       group_id: Optional[int] = None,
                       other_user_id: Optional[int] = None) -> List[Message]:
        """
        Update messages for a conversation.
        
        Args:
            messages_data: List of message dictionaries
            group_id: Group ID if group conversation
            other_user_id: Other user ID if private conversation
            
        Returns:
            List of Message instances
        """
        key = self._get_conversation_key(group_id, other_user_id)
        messages = [Message.from_dict(msg) for msg in messages_data]
        
        # Remove duplicates and sort
        seen_ids = set()
        unique_messages = []
        for msg in messages:
            if msg.id not in seen_ids:
                seen_ids.add(msg.id)
                unique_messages.append(msg)
        
        unique_messages.sort(key=lambda m: m.timestamp)
        self.message_cache[key] = unique_messages
        
        return unique_messages
    
    def get_messages(self, group_id: Optional[int] = None,
                    other_user_id: Optional[int] = None) -> List[Message]:
        """
        Get messages for a conversation.
        
        Args:
            group_id: Group ID if group conversation
            other_user_id: Other user ID if private conversation
            
        Returns:
            List of Message instances
        """
        key = self._get_conversation_key(group_id, other_user_id)
        return self.message_cache.get(key, [])
    
    def remove_message(self, message_id: int,
                      group_id: Optional[int] = None,
                      other_user_id: Optional[int] = None) -> bool:
        """
        Remove a message from cache.
        
        Args:
            message_id: ID of message to remove
            group_id: Group ID if group conversation
            other_user_id: Other user ID if private conversation
            
        Returns:
            True if message was removed, False otherwise
        """
        key = self._get_conversation_key(group_id, other_user_id)
        if key in self.message_cache:
            original_len = len(self.message_cache[key])
            self.message_cache[key] = [
                m for m in self.message_cache[key] if m.id != message_id
            ]
            return len(self.message_cache[key]) < original_len
        return False
    
    def clear_conversation(self, group_id: Optional[int] = None,
                          other_user_id: Optional[int] = None):
        """
        Clear all messages for a conversation.
        
        Args:
            group_id: Group ID if group conversation
            other_user_id: Other user ID if private conversation
        """
        key = self._get_conversation_key(group_id, other_user_id)
        if key in self.message_cache:
            del self.message_cache[key]
    
    def generate_client_message_id(self) -> str:
        """
        Generate a unique client message ID.
        
        Returns:
            Unique message ID string
        """
        return str(uuid.uuid4())
    
    def mark_as_read(self, message_id: int,
                    group_id: Optional[int] = None,
                    other_user_id: Optional[int] = None) -> bool:
        """
        Mark a message as read.
        
        Args:
            message_id: ID of message to mark as read
            group_id: Group ID if group conversation
            other_user_id: Other user ID if private conversation
            
        Returns:
            True if message was found and marked, False otherwise
        """
        key = self._get_conversation_key(group_id, other_user_id)
        if key in self.message_cache:
            for message in self.message_cache[key]:
                if message.id == message_id:
                    message.is_read = True
                    return True
        return False

