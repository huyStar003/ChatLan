"""Conversation manager for handling conversation operations."""
from typing import List, Dict, Optional
from datetime import datetime

from ..models.conversation import Conversation
from ..models.user import User
from ..models.message import Message


class ConversationManager:
    """Manages conversation operations."""
    
    def __init__(self, current_user_id: int):
        """
        Initialize conversation manager.
        
        Args:
            current_user_id: ID of the current user
        """
        self.current_user_id = current_user_id
        self.conversations: List[Conversation] = []
        self.contacts: List[User] = []
    
    def update_conversations(self, conversations_data: List[Dict]) -> List[Conversation]:
        """
        Update conversations list.
        
        Args:
            conversations_data: List of conversation dictionaries
            
        Returns:
            List of Conversation instances
        """
        self.conversations = [
            Conversation.from_dict(conv) for conv in conversations_data
        ]
        # Sort by updated_at (most recent first)
        self.conversations.sort(
            key=lambda c: c.updated_at or datetime.min,
            reverse=True
        )
        return self.conversations
    
    def get_conversations(self) -> List[Conversation]:
        """
        Get all conversations.
        
        Returns:
            List of Conversation instances
        """
        return self.conversations
    
    def get_conversation_by_group_id(self, group_id: int) -> Optional[Conversation]:
        """
        Get conversation by group ID.
        
        Args:
            group_id: Group ID
            
        Returns:
            Conversation instance or None
        """
        for conv in self.conversations:
            if conv.group_id == group_id:
                return conv
        return None
    
    def get_conversation_by_user_id(self, user_id: int) -> Optional[Conversation]:
        """
        Get conversation by other user ID.
        
        Args:
            user_id: Other user ID
            
        Returns:
            Conversation instance or None
        """
        for conv in self.conversations:
            if conv.is_private and conv.other_user and conv.other_user.id == user_id:
                return conv
        return None
    
    def add_or_update_conversation(self, conversation_data: Dict) -> Conversation:
        """
        Add or update a conversation.
        
        Args:
            conversation_data: Conversation data dictionary
            
        Returns:
            Conversation instance
        """
        conv = Conversation.from_dict(conversation_data)
        
        # Check if conversation already exists
        existing = None
        if conv.is_group and conv.group_id:
            existing = self.get_conversation_by_group_id(conv.group_id)
        elif conv.is_private and conv.other_user:
            existing = self.get_conversation_by_user_id(conv.other_user.id)
        
        if existing:
            # Update existing conversation
            existing.last_message = conv.last_message
            existing.updated_at = conv.updated_at
            existing.unread_count = conv.unread_count
            return existing
        else:
            # Add new conversation
            self.conversations.append(conv)
            # Re-sort
            self.conversations.sort(
                key=lambda c: c.updated_at or datetime.min,
                reverse=True
            )
            return conv
    
    def update_contacts(self, online_users_data: List[Dict], 
                       all_users_data: List[Dict]) -> List[User]:
        """
        Update contacts list.
        
        Args:
            online_users_data: List of online user dictionaries
            all_users_data: List of all user dictionaries
            
        Returns:
            List of User instances
        """
        # Combine and deduplicate
        all_users_dict = {}
        for user_data in all_users_data:
            user_id = user_data.get('id')
            if user_id:
                all_users_dict[user_id] = user_data
        
        # Mark online status
        online_ids = {u.get('id') for u in online_users_data}
        for user_id, user_data in all_users_dict.items():
            user_data['is_online'] = user_id in online_ids
        
        self.contacts = [User.from_dict(user_data) for user_data in all_users_dict.values()]
        return self.contacts
    
    def get_contacts(self) -> List[User]:
        """
        Get all contacts.
        
        Returns:
            List of User instances
        """
        return self.contacts
    
    def get_contact_by_id(self, user_id: int) -> Optional[User]:
        """
        Get contact by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance or None
        """
        for contact in self.contacts:
            if contact.id == user_id:
                return contact
        return None
    
    def get_contact_by_username(self, username: str) -> Optional[User]:
        """
        Get contact by username.
        
        Args:
            username: Username
            
        Returns:
            User instance or None
        """
        for contact in self.contacts:
            if contact.username == username:
                return contact
        return None
    
    def update_user_status(self, user_data: Dict) -> Optional[User]:
        """
        Update user status in contacts.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Updated User instance or None
        """
        user_id = user_data.get('id')
        if not user_id:
            return None
        
        contact = self.get_contact_by_id(user_id)
        if contact:
            # Update contact
            updated_user = User.from_dict(user_data)
            contact.status = updated_user.status
            contact.is_online = updated_user.is_online
            contact.status_message = updated_user.status_message
            contact.last_seen = updated_user.last_seen
            if updated_user.avatar:
                contact.avatar = updated_user.avatar
            return contact
        
        return None

