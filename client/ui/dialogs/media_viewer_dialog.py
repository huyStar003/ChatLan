"""Dialog for viewing media, files, or links."""
import base64
from typing import List, Dict
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QScrollArea, 
                             QWidget, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap


class MediaViewerDialog(QDialog):
    """Dialog to view all media, files, or links."""
    
    def __init__(self, title: str, messages: List[Dict], media_type: str, parent=None):
        """
        Initialize media viewer dialog.
        
        Args:
            title: Dialog title
            messages: List of message dictionaries
            media_type: Type of media ('image', 'file', 'link')
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 700)
        
        layout = QVBoxLayout(self)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        content_layout = QGridLayout(content_widget) if media_type == 'image' else QVBoxLayout(content_widget)
        
        if not messages:
            content_layout.addWidget(QLabel("Không có mục nào."))
        else:
            if media_type == 'image':
                # Display images in grid
                num_columns = 4
                for i, msg in enumerate(messages):
                    row, col = divmod(i, num_columns)
                    try:
                        pixmap = QPixmap()
                        pixmap.loadFromData(base64.b64decode(msg['file_data']))
                        img_label = QLabel()
                        img_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        img_label.setFixedSize(120, 120)
                        img_label.setStyleSheet("border: 1px solid #ddd; border-radius: 8px;")
                        content_layout.addWidget(img_label, row, col)
                    except Exception as e:
                        print(f"Lỗi load ảnh: {e}")
            else:
                # Display files/links as list
                for msg in messages:
                    label = QLabel(msg.get('file_name') or msg.get('content'))
                    content_layout.addWidget(label)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

