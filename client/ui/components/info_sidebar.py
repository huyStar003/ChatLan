"""Info sidebar component for displaying conversation information."""
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QWidget, QGroupBox,
                             QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap

from ...utils import resource_path


class InfoSidebar(QFrame):
    """Info sidebar component for displaying conversation information."""
    
    # Signals
    add_member_clicked = pyqtSignal()
    remove_member_clicked = pyqtSignal(int)  # Emits member_id
    media_viewer_requested = pyqtSignal(str, list, str)  # title, messages, media_type
    
    def __init__(self, parent=None):
        """
        Initialize info sidebar component.
        
        Args:
            parent: Parent widget (MainChatWindow)
        """
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedWidth(320)
        self.setStyleSheet("background-color: #f0f2f5; border-left: 1px solid #e0e0e0;")
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        self.info_sidebar_layout = QVBoxLayout(content_widget)
        self.info_sidebar_layout.setAlignment(Qt.AlignTop)
        self.info_sidebar_layout.setSpacing(15)
        self.info_sidebar_layout.setContentsMargins(10, 15, 10, 15)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def clear_content(self):
        """Clear all content from the sidebar."""
        while self.info_sidebar_layout.count():
            child = self.info_sidebar_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def add_header(self, display_name: str, avatar_pixmap: Optional[QPixmap] = None):
        """
        Add header section with avatar and name.
        
        Args:
            display_name: Display name
            avatar_pixmap: Optional avatar pixmap
        """
        header_widget = QWidget()
        layout = QVBoxLayout(header_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        avatar_label = QLabel()
        avatar_label.setFixedSize(80, 80)
        if avatar_pixmap:
            avatar_label.setPixmap(avatar_pixmap)
        else:
            avatar_label.setStyleSheet("background-color: #ccc; border-radius: 40px;")

        name_label = QLabel(display_name)
        name_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        layout.addWidget(avatar_label)
        layout.addWidget(name_label)
        self.info_sidebar_layout.addWidget(header_widget)
    
    def add_add_member_button(self, visible: bool = True):
        """
        Add "Add Member" button for group chats.
        
        Args:
            visible: Whether to show the button
        """
        if not visible:
            return
            
        add_member_btn = QPushButton(QIcon(resource_path('icons/users.png')), " Thêm thành viên")
        add_member_btn.clicked.connect(self.add_member_clicked.emit)
        add_member_btn.setStyleSheet("""
            QPushButton { 
                background-color: #e7f3ff; color: #005ae0; border: 1px solid #d1e7ff;
                padding: 8px; border-radius: 6px; text-align: center; font-weight: bold;
            }
            QPushButton:hover { background-color: #d1e7ff; }
        """)
        self.info_sidebar_layout.addWidget(add_member_btn)
    
    def add_members_section(self, members: List[Dict], creator_id: Optional[int] = None, 
                           is_current_user_creator: bool = False):
        """
        Add members section for group chats.
        
        Args:
            members: List of member dictionaries
            creator_id: ID of group creator
            is_current_user_creator: Whether current user is creator
        """
        members_box = QGroupBox(f"Thành viên ({len(members)})")
        members_box.setFont(QFont("Arial", 11, QFont.Bold))
        members_box_layout = QVBoxLayout(members_box)

        for member in members:
            member_widget = self._create_member_widget(member, creator_id, is_current_user_creator)
            members_box_layout.addWidget(member_widget)
        
        self.info_sidebar_layout.addWidget(members_box)
    
    def add_media_section(self, title: str, messages: List[Dict], media_type: str, 
                         max_preview: int = 6):
        """
        Add media section (images or files).
        
        Args:
            title: Section title
            messages: List of message dictionaries
            media_type: Type of media ('image' or 'file')
            max_preview: Maximum number of items to preview
        """
        # Header with title and "See all" button
        header_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        
        see_all_btn = QPushButton("Xem tất cả")
        see_all_btn.setStyleSheet("border: none; color: #0084ff;")
        see_all_btn.clicked.connect(
            lambda: self.media_viewer_requested.emit(title, messages, media_type)
        )
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(see_all_btn)
        self.info_sidebar_layout.addLayout(header_layout)

        # Content widget
        content_widget = QWidget()
        if media_type == 'image':
            layout = QGridLayout(content_widget)
            layout.setSpacing(5)
            num_columns = 3
            import base64
            for i, msg in enumerate(messages[:max_preview]):
                row, col = divmod(i, num_columns)
                try:
                    pixmap = QPixmap()
                    pixmap.loadFromData(base64.b64decode(msg['file_data']))
                    img_label = QLabel()
                    img_label.setPixmap(
                        pixmap.scaled(85, 85, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    )
                    img_label.setFixedSize(85, 85)
                    img_label.setStyleSheet("border-radius: 8px;")
                    layout.addWidget(img_label, row, col)
                except Exception as e:
                    print(f"Lỗi load ảnh thumbnail: {e}")
        else:  # file
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(5)
            for msg in messages[:max_preview]:
                label = QLabel(f"📄 {msg.get('file_name', 'N/A')}")
                layout.addWidget(label)
        
        self.info_sidebar_layout.addWidget(content_widget)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("border-color: #ddd;")
        self.info_sidebar_layout.addWidget(line)
    
    def add_loading_indicator(self, text: str = "Đang tải thông tin..."):
        """
        Add loading indicator.
        
        Args:
            text: Loading text
        """
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        self.info_sidebar_layout.addWidget(label)
    
    def _create_member_widget(self, member_data: Dict, creator_id: Optional[int],
                             is_current_user_creator: bool) -> QWidget:
        """
        Create a widget for a single member.
        
        Args:
            member_data: Member data dictionary
            creator_id: ID of group creator
            is_current_user_creator: Whether current user is creator
            
        Returns:
            Member widget
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Avatar
        avatar_label = QLabel()
        avatar_label.setFixedSize(30, 30)
        avatar_label.setStyleSheet("background-color: #ccc; border-radius: 15px;")
        
        # Name and role
        info_layout = QVBoxLayout()
        name_label = QLabel(member_data.get('display_name', 'Unknown'))
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        info_layout.addWidget(name_label)

        if member_data.get('id') == creator_id:
            role_label = QLabel("Nhóm trưởng")
            role_label.setFont(QFont("Arial", 8, QFont.StyleItalic))
            role_label.setStyleSheet("color: #e67e22;")
            info_layout.addWidget(role_label)

        layout.addWidget(avatar_label)
        layout.addLayout(info_layout)
        layout.addStretch()

        # Remove button (only for creator, not for themselves, not for group ID 1)
        current_group_id = getattr(self.parent_window, 'current_group_id', None)
        if (is_current_user_creator and 
            member_data.get('id') != creator_id and 
            current_group_id != 1):
            remove_btn = QPushButton(QIcon(resource_path('icons/user-minus.png')), "")
            remove_btn.setFixedSize(28, 28)
            remove_btn.setIconSize(QSize(16, 16))
            remove_btn.setToolTip(f"Xóa {member_data.get('display_name')} khỏi nhóm")
            remove_btn.clicked.connect(
                lambda: self.remove_member_clicked.emit(member_data.get('id'))
            )
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #fbebeb;
                    border: 1px solid #f5c6cb;
                    border-radius: 14px;
                }
                QPushButton:hover {
                    background-color: #f8d7da;
                }
            """)
            layout.addWidget(remove_btn)
        
        return widget
    
    def add_stretch(self):
        """Add stretch to push content to top."""
        self.info_sidebar_layout.addStretch()

