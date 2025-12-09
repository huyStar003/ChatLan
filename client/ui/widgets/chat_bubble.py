"""ChatBubble widget - displays a single chat message."""
import os
import sys
import subprocess
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QFontMetrics

from ...utils.resource_loader import resource_path
from .clickable_frame import ClickableFrame


class ChatBubble(QWidget):
    """Widget to display a single chat message bubble."""
    
    def __init__(self, message_data: Dict, is_own_message: bool = False, parent=None):
        """
        Initialize chat bubble.
        
        Args:
            message_data: Dictionary containing message data
            is_own_message: Whether this is the current user's message
            parent: Parent widget
        """
        super().__init__(parent)
        self.message_data = message_data
        self.is_own_message = is_own_message
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        # Main layout for bubble
        layout = QVBoxLayout()
        alignment = Qt.AlignRight if self.is_own_message else Qt.AlignLeft
        layout.setAlignment(alignment)
        layout.setContentsMargins(10, 5, 10, 5)

        # Main container for message content
        message_container = QFrame()
        message_container.setMaximumWidth(450)
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(12, 8, 12, 8)
        message_layout.setSpacing(4)

        # Check if this is a group message
        is_group_message = self.message_data.get('group_id') is not None
        
        # Show sender name for received messages in group chats
        if not self.is_own_message and is_group_message:
            sender_label = QLabel(self.message_data['sender']['display_name'])
            sender_label.setFont(QFont("Arial", 9, QFont.Bold))
            sender_label.setStyleSheet("color: #005ae0; margin-bottom: 2px;")
            message_layout.addWidget(sender_label)

        # Message content (text)
        content_text = self.message_data.get('content', '')
        content_label = QLabel(content_text)
        content_label.setFont(QFont("Arial", 11))
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if content_text and self.message_data.get('message_type') == 'text':
            message_layout.addWidget(content_label)

        # File/image content (if any)
        message_type = self.message_data.get('message_type', 'text')
        if message_type == 'image' and self.message_data.get('file_data'):
            self.add_image_content(message_layout)
        elif message_type == 'file' and self.message_data.get('file_data'):
            self.add_file_content(message_layout)

        # Timestamp
        timestamp_str = self.format_timestamp(self.message_data['timestamp'])
        timestamp_label = QLabel(timestamp_str)
        timestamp_label.setFont(QFont("Arial", 8))
        timestamp_label.setAlignment(Qt.AlignRight)
        message_layout.addWidget(timestamp_label)

        # Set colors and styles
        if self.is_own_message:
            message_container.setStyleSheet("""
                QFrame { background-color: #cce4ff; color: #050505; border-radius: 18px; }
                QLabel { color: #050505; }
            """)
        else:
            message_container.setStyleSheet("""
                QFrame { background-color: #e4e6eb; color: #050505; border-radius: 18px; }
                QLabel { color: #050505; background-color: transparent; }
            """)

        layout.addWidget(message_container)
        self.setLayout(layout)
    
    def add_image_content(self, layout: QVBoxLayout):
        """Add image content to the message."""
        try:
            image_data = base64.b64decode(self.message_data['file_data'])
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            # Scale image to fit
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                image_label = QLabel()
                image_label.setPixmap(scaled_pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                image_label.setStyleSheet("border: 1px solid #ddd; border-radius: 8px; margin: 5px;")
                
                layout.addWidget(image_label)
        except Exception as e:
            print(f"Error displaying image: {e}")
    
    def add_file_content(self, layout: QVBoxLayout):
        """Add file content with ClickableFrame for accurate click handling."""
        # Main container for file widget
        file_frame = ClickableFrame()
        file_frame.clicked.connect(self.open_file)
        file_frame.setToolTip("Mở file bằng ứng dụng mặc định")

        file_layout = QHBoxLayout(file_frame)
        file_layout.setContentsMargins(10, 8, 10, 8)
        file_layout.setSpacing(10)
        
        # File icon
        file_icon_label = QLabel()
        file_icon_label.setPixmap(QIcon(resource_path('icons/attachment.png')).pixmap(QSize(28, 28)))
        
        # File info (name and size)
        file_info_layout = QVBoxLayout()
        file_info_layout.setSpacing(2)
        
        original_file_name = self.message_data.get('file_name', 'Unknown file')
        file_name_font = QFont("Arial", 10, QFont.Bold)
        metrics = QFontMetrics(file_name_font)
        elided_file_name = metrics.elidedText(original_file_name, Qt.ElideRight, 200)
        
        file_name_label = QLabel(elided_file_name)
        file_name_label.setFont(file_name_font)
        file_name_label.setToolTip(original_file_name)

        file_size = self.message_data.get('file_size', 0)
        file_size_label = QLabel(self.format_file_size(file_size))
        file_size_label.setFont(QFont("Arial", 8))
        
        file_info_layout.addWidget(file_name_label)
        file_info_layout.addWidget(file_size_label)
        
        # Download button
        download_btn = QPushButton()
        download_btn.setIcon(QIcon(resource_path('icons/download.png')))
        download_btn.setIconSize(QSize(20, 20))
        download_btn.setFixedSize(30, 30)
        download_btn.setCursor(Qt.PointingHandCursor)
        download_btn.setToolTip("Lưu file về máy")
        download_btn.clicked.connect(self.download_file)
        
        # Add components to layout
        file_layout.addWidget(file_icon_label, alignment=Qt.AlignCenter)
        file_layout.addLayout(file_info_layout)
        file_layout.addStretch()
        file_layout.addWidget(download_btn, alignment=Qt.AlignCenter)
        
        # StyleSheet
        is_own = self.is_own_message
        text_color = 'white' if is_own else '#050505'
        
        file_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 12px;
            }}
            QLabel {{ color: {text_color}; background-color: transparent; }}
        """)
        
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout.addWidget(file_frame)
        
    def open_file(self):
        """Open file with default application."""
        try:
            file_data = base64.b64decode(self.message_data['file_data'])
            file_name = self.message_data.get('file_name', 'download')
            
            # Save file to temp directory
            temp_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ChatLAN_Temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, file_name)

            with open(temp_path, 'wb') as f:
                f.write(file_data)

            # Open file with default application
            if sys.platform == "win32":
                os.startfile(temp_path)
            elif sys.platform == "darwin":
                subprocess.Popen(['open', temp_path])
            else:
                subprocess.Popen(['xdg-open', temp_path])

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở file: {str(e)}")

    def download_file(self):
        """Download file."""
        try:
            file_data = base64.b64decode(self.message_data['file_data'])
            file_name = self.message_data.get('file_name', 'download')
            
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Lưu file", 
                file_name,
                "All Files (*)"
            )
            
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(file_data)
                
                QMessageBox.information(self, "Thành công", f"File đã được lưu tại:\n{save_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải file: {str(e)}")
    
    def format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp accurately."""
        try:
            # Convert ISO 8601 string to datetime object
            # Split microsecond part if present (e.g., .123456)
            if '.' in timestamp_str:
                timestamp_str = timestamp_str.split('.')[0]
            
            # Handle common formats
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', ''))
            except ValueError:
                dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

            now = datetime.now()
            
            # Compare dates
            if dt.date() == now.date():
                return dt.strftime("%H:%M")  # Today: show only hour:minute
            elif dt.date() == (now.date() - timedelta(days=1)):
                return f"Hôm qua, {dt.strftime('%H:%M')}"  # Yesterday
            else:
                return dt.strftime("%d/%m/%Y %H:%M")  # Other days: show full date
        except Exception as e:
            print(f"Error formatting timestamp '{timestamp_str}': {e}")
            return timestamp_str  # Return original string on error
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

