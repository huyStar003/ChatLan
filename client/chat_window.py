from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QLineEdit, QPushButton, QFrame, 
                            QScrollArea, QSplitter, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor
from datetime import datetime
import json
class ChatWindow(QWidget):
    message_sent = pyqtSignal(str, str, str)  # type, receiver, message
    request_chat_history = pyqtSignal(str)  # other_user
    def __init__(self):
        super().__init__()
        self.current_user = ""
        self.current_chat_user = ""
        self.is_group_chat = False
        self.init_ui()
        self.setup_styles()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Chat header
        self.chat_header = QFrame()
        self.chat_header.setFixedHeight(60)
        header_layout = QHBoxLayout(self.chat_header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        self.chat_title = QLabel("Chọn người dùng để bắt đầu chat")
        self.chat_title.setFont(QFont("Arial", 14, QFont.Bold))
        self.chat_title.setStyleSheet("color: #333;")
        
        self.chat_status = QLabel("")
        self.chat_status.setFont(QFont("Arial", 9))
        self.chat_status.setStyleSheet("color: #666;")
        
        header_layout.addWidget(self.chat_title)
        header_layout.addStretch()
        header_layout.addWidget(self.chat_status)
        # Chat messages area
        self.messages_area = QTextEdit()
        self.messages_area.setReadOnly(True)
        self.messages_area.setFont(QFont("Arial", 10))
        # Message input area
        input_frame = QFrame()
        input_frame.setFixedHeight(80)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 10, 15, 10)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Nhập tin nhắn...")
        self.message_input.setFont(QFont("Arial", 11))
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("Gửi")
        self.send_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setEnabled(False)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        # Add to main layout
        layout.addWidget(self.chat_header)
        layout.addWidget(self.messages_area)
        layout.addWidget(input_frame)
        self.setLayout(layout)
        # Enable message input when there's text
        self.message_input.textChanged.connect(self.on_message_input_changed)
    def setup_styles(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e1e5e9;
            }
            QTextEdit {
                background-color: white;
                border: none;
                padding: 15px;
                font-size: 11px;
                line-height: 1.4;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #e1e5e9;
                border-radius: 20px;
                background-color: white;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #0084ff;
                outline: none;
            }
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 20px;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
            QPushButton:pressed {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
    def set_current_user(self, username):
        self.current_user = username
    def start_private_chat(self, username):
        """Bắt đầu chat riêng với user"""
        self.current_chat_user = username
        self.is_group_chat = False
        self.chat_title.setText(f"Chat với {username}")
        self.chat_status.setText("Đang hoạt động")
        self.messages_area.clear()
        self.message_input.setEnabled(True)
        self.message_input.setPlaceholderText(f"Nhắn tin cho {username}...")
        # Request chat history
        self.request_chat_history.emit(username)
    def start_group_chat(self):
        """Bắt đầu chat nhóm"""
        self.current_chat_user = ""
        self.is_group_chat = True
        self.chat_title.setText("Chat nhóm")
        self.chat_status.setText("Tất cả thành viên")
        self.messages_area.clear()
        self.message_input.setEnabled(True)
        self.message_input.setPlaceholderText("Nhắn tin cho tất cả...")
    def send_message(self):
        """Gửi tin nhắn"""
        message = self.message_input.text().strip()
        if not message:
            return
        if self.is_group_chat:
            self.message_sent.emit("group_message", "", message)
        else:
            if self.current_chat_user:
                self.message_sent.emit("private_message", self.current_chat_user, message)
        self.message_input.clear()
    def add_message(self, sender, message, timestamp, is_own_message=False):
        """Thêm tin nhắn vào chat"""
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M")
        except:
            time_str = datetime.now().strftime("%H:%M")
        # Create message HTML
        if is_own_message:
            message_html = f"""
            <div style="text-align: right; margin: 8px 0;">
                <div style="display: inline-block; background-color: #0084ff; color: white; 
                           padding: 8px 12px; border-radius: 18px; max-width: 70%; 
                           word-wrap: break-word;">
                    {self.escape_html(message)}
                </div>
                <div style="font-size: 9px; color: #666; margin-top: 2px;">
                    {time_str}
                </div>
            </div>
            """
        else:
            sender_name = sender if self.is_group_chat else ""
            message_html = f"""
            <div style="text-align: left; margin: 8px 0;">
                {f'<div style="font-size: 10px; color: #0084ff; font-weight: bold; margin-bottom: 2px;">{sender}</div>' if sender_name else ''}
                <div style="display: inline-block; background-color: #f1f3f4; color: #333; 
                           padding: 8px 12px; border-radius: 18px; max-width: 70%; 
                           word-wrap: break-word;">
                    {self.escape_html(message)}
                </div>
                <div style="font-size: 9px; color: #666; margin-top: 2px;">
                    {time_str}
                </div>
            </div>
            """
        # Add to messages area
        cursor = self.messages_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(message_html)
        # Scroll to bottom
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    def load_chat_history(self, messages):
        """Load lịch sử chat"""
        self.messages_area.clear()
        for msg in messages:
            is_own = msg["sender"] == self.current_user
            self.add_message(
                msg["sender"],
                msg["message"],
                msg["timestamp"],
                is_own
            )
    def load_group_history(self, messages):
        """Load lịch sử chat nhóm"""
        if self.is_group_chat:
            self.messages_area.clear()
            for msg in messages:
                is_own = msg["sender"] == self.current_user
                self.add_message(
                    msg["sender"],
                    msg["message"],
                    msg["timestamp"],
                    is_own
                )
    def on_message_input_changed(self):
        """Xử lý khi nội dung input thay đổi"""
        has_text = bool(self.message_input.text().strip())
        self.send_button.setEnabled(has_text and (self.current_chat_user or self.is_group_chat))
    def escape_html(self, text):
        """Escape HTML characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    def show_connection_status(self, connected):
        """Hiển thị trạng thái kết nối"""
        if connected:
            self.chat_status.setText("Đang hoạt động")
            self.chat_status.setStyleSheet("color: #28a745;")
        else:
            self.chat_status.setText("Mất kết nối")
            self.chat_status.setStyleSheet("color: #dc3545;")
