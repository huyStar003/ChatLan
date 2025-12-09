"""Dialog for displaying search results."""
from typing import List, Dict
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QPushButton, QWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class SearchResultDialog(QDialog):
    """Dialog to display search results."""
    
    def __init__(self, query: str, results: List[Dict], parent=None):
        """
        Initialize search result dialog.
        
        Args:
            query: Search query string
            results: List of message dictionaries matching the query
            parent: Parent widget
        """
        super().__init__(parent)
        self.query = query
        self.results = results
        self.setWindowTitle(f"Kết quả tìm kiếm cho: '{query}'")
        self.setMinimumSize(500, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"{len(self.results)} kết quả được tìm thấy")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # Results list
        results_list = QListWidget()
        if not self.results:
            no_result_item = QListWidgetItem("Không tìm thấy tin nhắn nào phù hợp.")
            results_list.addItem(no_result_item)
        else:
            for message in self.results:
                item = QListWidgetItem()
                item_widget = self.create_result_widget(message)
                item.setSizeHint(item_widget.sizeHint())
                results_list.addItem(item)
                results_list.setItemWidget(item, item_widget)  # Fixed: correct order
        
        layout.addWidget(results_list)

        # Close button
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 0, Qt.AlignCenter)

    def create_result_widget(self, message: Dict) -> QWidget:
        """
        Create a widget for a single search result.
        
        Args:
            message: Message dictionary
            
        Returns:
            Widget displaying the message
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)

        # Row 1: Sender and Time
        header_layout = QHBoxLayout()
        sender_name = message['sender']['display_name']
        sender_label = QLabel(f"<strong>{sender_name}</strong>")
        
        timestamp = datetime.fromisoformat(message['timestamp']).strftime('%d/%m/%Y %H:%M')
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: #666;")

        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)

        # Row 2: Message content
        content_label = QLabel(message['content'])
        content_label.setWordWrap(True)

        layout.addLayout(header_layout)
        layout.addWidget(content_label)
        
        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        return widget

