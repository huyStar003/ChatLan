from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QListWidgetItem, QPushButton, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QBrush
class UserListWidget(QWidget):
    user_selected = pyqtSignal(str)  # Signal khi chọn user để chat
    group_chat_selected = pyqtSignal()  # Signal khi chọn chat nhóm
    def __init__(self):
        super().__init__()
        self.current_user = ""
        self.online_users = []
        self.init_ui()
        self.setup_styles()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Header
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel("Danh sách người dùng")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        
        self.online_count_label = QLabel("0 người online")
        self.online_count_label.setFont(QFont("Arial", 9))
        self.online_count_label.setStyleSheet("color: #666;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.online_count_label)
        # Chat nhóm button
        self.group_chat_button = QPushButton("💬 Chat nhóm")
        self.group_chat_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.group_chat_button.clicked.connect(self.group_chat_selected.emit)
        # User list
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.on_user_selected)
        # Thêm widgets
        layout.addWidget(header_frame)
        layout.addWidget(self.group_chat_button)
        layout.addWidget(self.user_list)
        
        self.setLayout(layout)
    def setup_styles(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e1e5e9;
            }
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px;
                margin: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QListWidget {
                background-color: white;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-bottom: 1px solid #f0f0f0;
                background-color: white;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
    def set_current_user(self, username):
        self.current_user = username
    def update_user_list(self, users):
        """Cập nhật danh sách user online"""
        self.online_users = users
        self.user_list.clear()
        online_count = 0
        for user in users:
            if user["username"] != self.current_user:  # Không hiển thị chính mình
                item = QListWidgetItem() 
                # Tạo widget cho user item
                user_widget = self.create_user_item(user["username"], True)
                item.setSizeHint(user_widget.sizeHint())
                
                self.user_list.addItem(item)
                self.user_list.setItemWidget(item, user_widget)
                online_count += 1
        # Cập nhật số lượng user online
        self.online_count_label.setText(f"{online_count} người online")
    def create_user_item(self, username, is_online=True):
        """Tạo widget cho một user item"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        # Status indicator (online/offline)
        status_label = QLabel("●")
        status_label.setFont(QFont("Arial", 12))
        if is_online:
            status_label.setStyleSheet("color: #28a745;")  # Green for online
        else:
            status_label.setStyleSheet("color: #dc3545;")  # Red for offline
        # Username
        username_label = QLabel(username)
        username_label.setFont(QFont("Arial", 11))
        username_label.setStyleSheet("color: #333;")
        # Status text
        status_text = QLabel("Đang hoạt động" if is_online else "Không hoạt động")
        status_text.setFont(QFont("Arial", 9))
        status_text.setStyleSheet("color: #666;")
        # Layout
        layout.addWidget(status_label)
        layout.addWidget(username_label)
        layout.addStretch()
        layout.addWidget(status_text)
        return widget
    def on_user_selected(self, item):
        """Xử lý khi chọn user để chat"""
        row = self.user_list.row(item)
        if row < len(self.online_users):
            selected_user = None
            current_row = 0
            for user in self.online_users:
                if user["username"] != self.current_user:
                    if current_row == row:
                        selected_user = user["username"]
                        break
                    current_row += 1
            if selected_user:
                self.user_selected.emit(selected_user)
    def get_online_user_count(self):
        """Lấy số lượng user online (không tính mình)"""
        return len([u for u in self.online_users if u["username"] != self.current_user])
    def is_user_online(self, username):
        """Kiểm tra user có online không"""
        return any(u["username"] == username for u in self.online_users)
