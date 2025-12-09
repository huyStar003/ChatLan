"""Dialog for displaying user profile information."""
import base64
from typing import Dict, Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QIcon


class UserProfileDialog(QDialog):
    """Dialog to display user profile information."""
    
    def __init__(self, user_data: Dict, parent=None):
        """
        Initialize user profile dialog.
        
        Args:
            user_data: Dictionary containing user data
            parent: Parent widget
        """
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Thông tin tài khoản")
        self.setFixedSize(350, 450)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header section with Avatar and Name
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #0084ff;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setAlignment(Qt.AlignCenter)

        avatar_label = QLabel()
        avatar_label.setFixedSize(100, 100)
        avatar_pixmap = self.create_circular_avatar(self.user_data.get('avatar'), 100)
        avatar_label.setPixmap(avatar_pixmap)
        
        display_name_label = QLabel(self.user_data.get('display_name', 'N/A'))
        display_name_label.setFont(QFont("Arial", 18, QFont.Bold))
        display_name_label.setStyleSheet("color: white;")
        display_name_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(avatar_label, alignment=Qt.AlignCenter)
        header_layout.addWidget(display_name_label)

        # Body section with detailed information
        body_frame = QFrame()
        body_layout = QVBoxLayout(body_frame)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(15)

        # Username
        body_layout.addLayout(self.create_info_row(':/icons/at-sign.png', f"@{self.user_data.get('username', 'N/A')}"))
        # Email
        body_layout.addLayout(self.create_info_row(':/icons/email.png', self.user_data.get('email') or "Chưa cập nhật email"))
        # Status
        status_icon = ':/icons/status-online.png' if self.user_data.get('is_online') else ':/icons/status-offline.png'
        status_text = "Đang hoạt động" if self.user_data.get('is_online') else "Không hoạt động"
        body_layout.addLayout(self.create_info_row(status_icon, status_text))

        body_layout.addStretch()

        # Close button
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        
        layout.addWidget(header_frame, 1)  # Takes 1 part
        layout.addWidget(body_frame, 2)    # Takes 2 parts
        layout.addWidget(close_button, 0, Qt.AlignCenter)
        layout.setContentsMargins(10, 10, 10, 10)

    def create_info_row(self, icon_path: str, text: str) -> QHBoxLayout:
        """
        Create a row with icon and text.
        
        Args:
            icon_path: Path to icon resource
            text: Text to display
            
        Returns:
            Layout containing icon and text
        """
        row_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(icon_path).pixmap(QSize(20, 20)))
        text_label = QLabel(text)
        text_label.setFont(QFont("Arial", 10))
        row_layout.addWidget(icon_label)
        row_layout.addWidget(text_label)
        row_layout.addStretch()
        return row_layout

    def create_circular_avatar(self, avatar_data: Optional[str], size: int) -> QPixmap:
        """
        Create a circular avatar pixmap.
        
        Args:
            avatar_data: Base64 encoded avatar data
            size: Size of the avatar
            
        Returns:
            Circular pixmap of the avatar
        """
        if avatar_data:
            try:
                image_data = base64.b64decode(avatar_data)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
            except:
                pixmap = self.create_default_avatar_pixmap(size)
        else:
            pixmap = self.create_default_avatar_pixmap(size)

        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(Qt.transparent)
        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(scaled_pixmap))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.end()
        return circular_pixmap

    def create_default_avatar_pixmap(self, size: int) -> QPixmap:
        """
        Create a default avatar with initial letter.
        
        Args:
            size: Size of the avatar
            
        Returns:
            Default avatar pixmap
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor("#e0e0e0"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("#333"))
        painter.setFont(QFont("Arial", size // 2, QFont.Bold))
        display_name = self.user_data.get('display_name', 'A')
        painter.drawText(pixmap.rect(), Qt.AlignCenter, display_name[0].upper())
        painter.end()
        return pixmap

