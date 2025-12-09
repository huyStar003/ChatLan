"""Sidebar component for conversations and contacts."""
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QListWidget, 
                             QLineEdit, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap

from ...utils import resource_path


class Sidebar(QFrame):
    """Sidebar component for displaying conversations and contacts."""
    
    # Signals
    conversation_selected = pyqtSignal(dict)  # Emits conversation data
    contact_selected = pyqtSignal(dict)  # Emits contact data
    create_group_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    status_changed = pyqtSignal(str)  # Emits new status
    
    def __init__(self, parent=None):
        """
        Initialize sidebar component.
        
        Args:
            parent: Parent widget (MainChatWindow)
        """
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedWidth(300)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # User info header
        self.create_user_header(layout)
        
        # Action frame (Create group button)
        action_frame = QFrame()
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(10, 5, 10, 5)

        self.create_group_btn = QPushButton(QIcon(resource_path('icons/users.png')), " Tạo nhóm mới")
        self.create_group_btn.clicked.connect(self.create_group_clicked.emit)
        self.create_group_btn.setStyleSheet("""
            QPushButton { 
                background-color: #e7f3ff; 
                color: #005ae0; 
                border: 1px solid #d1e7ff;
                padding: 8px; 
                border-radius: 6px;
                text-align: left;
            }
            QPushButton:hover { background-color: #d1e7ff; }
        """)
        action_layout.addWidget(self.create_group_btn)
        layout.addWidget(action_frame)

        # Tab widget for conversations and contacts
        self.sidebar_tabs = QTabWidget()
        self.sidebar_tabs.setFont(QFont("Arial", 10))
        
        # Conversations tab
        conversations_tab = QWidget()
        conversations_layout = QVBoxLayout(conversations_tab)
        conversations_layout.setContentsMargins(10, 10, 10, 10)
        conversations_layout.setSpacing(0)
        
        # Conversations list
        self.conversations_list = QListWidget()
        self.conversations_list.itemClicked.connect(self._on_conversation_clicked)
        self.conversations_list.setContextMenuPolicy(Qt.CustomContextMenu)
        conversations_layout.addWidget(self.conversations_list)
        
        # Contacts tab
        contacts_tab = QWidget()
        contacts_layout = QVBoxLayout(contacts_tab)
        contacts_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search contacts
        self.contact_search = QLineEdit()
        self.contact_search.setPlaceholderText("🔍 Tìm kiếm liên hệ...")
        contacts_layout.addWidget(self.contact_search)
        
        # Contacts list
        self.contacts_list = QListWidget()
        self.contacts_list.itemClicked.connect(self._on_contact_clicked)
        self.contacts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        contacts_layout.addWidget(self.contacts_list)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Làm mới")
        self.refresh_btn.setFont(QFont("Arial", 9))
        self.refresh_btn.clicked.connect(self.refresh_clicked.emit)
        contacts_layout.addWidget(self.refresh_btn)
        
        # Add tabs
        self.sidebar_tabs.addTab(conversations_tab, "💬 Hội thoại")
        self.sidebar_tabs.addTab(contacts_tab, "👥 Danh bạ")
        
        layout.addWidget(self.sidebar_tabs)
    
    def create_user_header(self, layout: QVBoxLayout):
        """
        Create user info header.
        
        Args:
            layout: Parent layout to add header to
        """
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Avatar
        self.user_avatar = QLabel()
        self.user_avatar.setFixedSize(50, 50)
        self.user_avatar.setStyleSheet("""
            QLabel {
                border: 2px solid #0084ff;
                border-radius: 25px;
                background-color: #e3f2fd;
            }
        """)
        
        # User info
        user_info_layout = QVBoxLayout()
        
        self.user_name_label = QLabel("User")
        self.user_name_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.user_name_label.setStyleSheet("color: #333;")
        
        # Status selector
        self.status_combo = QComboBox()
        self.status_combo.addItems(["🟢 Online", "🟡 Away", "🔴 Busy"])
        self.status_combo.setFont(QFont("Arial", 9))
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        
        user_info_layout.addWidget(self.user_name_label)
        user_info_layout.addWidget(self.status_combo)
        
        # Settings button
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon(resource_path('icons/settings.png')))
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setFixedSize(35, 35)
        self.settings_btn.setToolTip("Xem thông tin cá nhân")
        
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 17px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)

        header_layout.addWidget(self.user_avatar)
        header_layout.addLayout(user_info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.settings_btn)
        
        layout.addWidget(header_frame)
    
    def set_user_info(self, user_data: Dict):
        """
        Set user information in header.
        
        Args:
            user_data: User data dictionary
        """
        if self.user_name_label:
            self.user_name_label.setText(user_data.get('display_name', 'User'))
        # Avatar will be set by parent window
    
    def set_user_avatar(self, avatar_pixmap: QPixmap):
        """
        Set user avatar.
        
        Args:
            avatar_pixmap: Avatar pixmap
        """
        if self.user_avatar:
            self.user_avatar.setPixmap(avatar_pixmap)
    
    def update_conversations(self, conversations: List[Dict]):
        """
        Update conversations list.
        
        Args:
            conversations: List of conversation dictionaries
        """
        self.conversations_list.clear()
        # Parent window will handle adding items with custom widgets
    
    def update_contacts(self, contacts: List[Dict]):
        """
        Update contacts list.
        
        Args:
            contacts: List of contact dictionaries
        """
        self.contacts_list.clear()
        # Parent window will handle adding items with custom widgets
    
    def filter_contacts(self, text: str):
        """
        Filter contacts by search text.
        
        Args:
            text: Search text
        """
        # Parent window will handle filtering
        pass
    
    def _on_conversation_clicked(self, item):
        """Handle conversation item click."""
        # Get conversation data from item
        if hasattr(item, 'conversation_data'):
            self.conversation_selected.emit(item.conversation_data)
    
    def _on_contact_clicked(self, item):
        """Handle contact item click."""
        # Get contact data from item
        if hasattr(item, 'contact_data'):
            self.contact_selected.emit(item.contact_data)
    
    def _on_status_changed(self, status_text: str):
        """Handle status change."""
        # Extract status from text (e.g., "🟢 Online" -> "online")
        status_map = {
            "🟢 Online": "online",
            "🟡 Away": "away",
            "🔴 Busy": "busy"
        }
        status = status_map.get(status_text, "online")
        self.status_changed.emit(status)
    
    def set_conversation_context_menu_handler(self, handler):
        """Set handler for conversation context menu."""
        self.conversations_list.customContextMenuRequested.connect(handler)
    
    def set_contact_context_menu_handler(self, handler):
        """Set handler for contact context menu."""
        self.contacts_list.customContextMenuRequested.connect(handler)
    
    def set_settings_clicked_handler(self, handler):
        """Set handler for settings button click."""
        self.settings_btn.clicked.connect(handler)
    
    def set_contact_search_handler(self, handler):
        """Set handler for contact search text change."""
        self.contact_search.textChanged.connect(handler)

