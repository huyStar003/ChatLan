"""Chat area component for displaying messages and input."""
from typing import Optional
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QWidget, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont, QIcon

from ...utils import resource_path


class ChatArea(QFrame):
    """Chat area component for displaying messages and input."""
    
    # Signals
    message_sent = pyqtSignal(str)  # Emits message content
    file_upload_clicked = pyqtSignal()
    emoji_clicked = pyqtSignal()
    search_clicked = pyqtSignal()
    clear_chat_clicked = pyqtSignal()
    info_sidebar_toggled = pyqtSignal(bool)  # Emits toggle state
    
    def __init__(self, parent=None):
        """
        Initialize chat area component.
        
        Args:
            parent: Parent widget (MainChatWindow)
        """
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat header
        self.create_chat_header(layout)
        
        # Messages area
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget containing all chat bubbles
        self.messages_container = QWidget()
        self.messages_scroll.setWidget(self.messages_container)

        # Main layout for chat bubbles
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(5)
        
        # Add stretch to push messages to top
        self.messages_layout.addStretch()
        
        layout.addWidget(self.messages_scroll)
        
        # Typing indicator
        self.typing_indicator = QLabel("")
        font = QFont("Arial", 9)
        font.setStyle(QFont.StyleItalic)
        self.typing_indicator.setFont(font)
        self.typing_indicator.setStyleSheet("color: #666; padding: 5px 15px;")
        self.typing_indicator.setVisible(False)
        layout.addWidget(self.typing_indicator)
        
        # Input area
        self.create_input_area(layout)
    
    def create_chat_header(self, layout: QVBoxLayout):
        """
        Create chat header.
        
        Args:
            layout: Parent layout to add header to
        """
        self.chat_header = QFrame()
        self.chat_header.setFixedHeight(60)
        header_layout = QHBoxLayout(self.chat_header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Chat title
        self.chat_title = QLabel("Chọn cuộc trò chuyện để bắt đầu")
        self.chat_title.setFont(QFont("Arial", 14, QFont.Bold))
        self.chat_title.setStyleSheet("color: #333;")
        
        # Chat status
        self.chat_status = QLabel("")
        self.chat_status.setFont(QFont("Arial", 10))
        self.chat_status.setStyleSheet("color: #666;")
        
        # Search button
        self.search_btn = QPushButton()
        self.search_btn.setIcon(QIcon(resource_path('icons/search.png')))
        self.search_btn.setIconSize(QSize(20, 20))
        self.search_btn.setFixedSize(35, 35)
        self.search_btn.setToolTip("Tìm kiếm tin nhắn (Ctrl+F)")
        self.search_btn.setShortcut("Ctrl+F")
        self.search_btn.clicked.connect(self.search_clicked.emit)
        
        # Clear chat button
        self.clear_chat_btn = QPushButton()
        self.clear_chat_btn.setIcon(QIcon(resource_path('icons/delete.png')))
        self.clear_chat_btn.setIconSize(QSize(20, 20))
        self.clear_chat_btn.setFixedSize(35, 35)
        self.clear_chat_btn.setToolTip("Xóa lịch sử chat")
        self.clear_chat_btn.clicked.connect(self.clear_chat_clicked.emit)
        
        # Info sidebar toggle button
        self.info_sidebar_btn = QPushButton()
        self.info_sidebar_btn.setIcon(QIcon(resource_path('icons/info-sidebar.png')))
        self.info_sidebar_btn.setIconSize(QSize(20, 20))
        self.info_sidebar_btn.setFixedSize(35, 35)
        self.info_sidebar_btn.setToolTip("Thông tin hội thoại")
        self.info_sidebar_btn.setCheckable(True)
        self.info_sidebar_btn.toggled.connect(self.info_sidebar_toggled.emit)
        
        # Add widgets to layout
        header_layout.addWidget(self.chat_title)
        header_layout.addWidget(self.chat_status)
        header_layout.addStretch()
        header_layout.addWidget(self.search_btn)
        header_layout.addWidget(self.clear_chat_btn)
        header_layout.addWidget(self.info_sidebar_btn)
        
        layout.addWidget(self.chat_header)
        
        # Apply styles
        icon_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 17px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """
        self.search_btn.setStyleSheet(icon_button_style)
        self.clear_chat_btn.setStyleSheet(icon_button_style)
    
    def create_input_area(self, layout: QVBoxLayout):
        """
        Create input area for message input.
        
        Args:
            layout: Parent layout to add input area to
        """
        input_frame = QFrame()
        input_frame.setFixedHeight(70)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 10, 15, 10)
        
        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(8)

        # Button and icon sizes
        BUTTON_SIZE = 40
        ICON_SIZE = 22
        
        # File attachment button
        self.file_btn = QPushButton()
        self.file_btn.setIcon(QIcon(resource_path('icons/attachment.png')))
        self.file_btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.file_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.file_btn.setToolTip("Đính kèm file (Ctrl+O)")
        self.file_btn.setShortcut("Ctrl+O")
        self.file_btn.clicked.connect(self.file_upload_clicked.emit)
        
        # Emoji button
        self.emoji_btn = QPushButton()
        self.emoji_btn.setIcon(QIcon(resource_path('icons/emoji.png')))
        self.emoji_btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.emoji_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.emoji_btn.setToolTip("Chọn emoji (Ctrl+E)")
        self.emoji_btn.setShortcut("Ctrl+E")
        self.emoji_btn.clicked.connect(self.emoji_clicked.emit)
        
        # Message input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Nhập tin nhắn...")
        self.message_input.setFont(QFont("Arial", 11))
        
        # Send button
        self.send_btn = QPushButton("Gửi")
        self.send_btn.setFixedSize(60, 40)
        self.send_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.send_btn.setEnabled(False)
        
        # Add widgets to layout
        input_row_layout.addWidget(self.file_btn)
        input_row_layout.addWidget(self.emoji_btn)
        input_row_layout.addWidget(self.message_input)
        input_row_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(input_row_layout)
        layout.addWidget(input_frame)

        # Apply styles
        icon_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dde0e3;
            }
        """
        self.file_btn.setStyleSheet(icon_button_style)
        self.emoji_btn.setStyleSheet(icon_button_style)
    
    def set_chat_title(self, title: str):
        """
        Set chat title.
        
        Args:
            title: Chat title text
        """
        if self.chat_title:
            self.chat_title.setText(title)
    
    def set_chat_status(self, status: str):
        """
        Set chat status.
        
        Args:
            status: Status text
        """
        if self.chat_status:
            self.chat_status.setText(status)
    
    def clear_messages(self):
        """Clear all messages from the chat area."""
        while self.messages_layout.count():
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.messages_layout.addStretch()
    
    def add_message_widget(self, widget):
        """
        Add a message widget to the chat area.
        
        Args:
            widget: Message widget to add
        """
        # Remove stretch temporarily
        if self.messages_layout.count() > 0:
            item = self.messages_layout.itemAt(self.messages_layout.count() - 1)
            if item and item.spacerItem():
                self.messages_layout.removeItem(item)
        
        self.messages_layout.addWidget(widget)
        # Add stretch back
        self.messages_layout.addStretch()
        
        # Scroll to bottom
        self.messages_scroll.verticalScrollBar().setValue(
            self.messages_scroll.verticalScrollBar().maximum()
        )
    
    def set_typing_indicator(self, text: str, visible: bool = True):
        """
        Set typing indicator text and visibility.
        
        Args:
            text: Indicator text
            visible: Whether to show the indicator
        """
        if self.typing_indicator:
            self.typing_indicator.setText(text)
            self.typing_indicator.setVisible(visible)
    
    def set_message_input_handler(self, handler):
        """Set handler for message input text change."""
        self.message_input.textChanged.connect(handler)
    
    def set_message_input_event_filter(self, filter_obj):
        """Set event filter for message input."""
        self.message_input.installEventFilter(filter_obj)
    
    def get_message_text(self) -> str:
        """
        Get current message input text.
        
        Returns:
            Message text
        """
        return self.message_input.toPlainText().strip()
    
    def clear_message_input(self):
        """Clear message input."""
        self.message_input.clear()
    
    def set_send_button_enabled(self, enabled: bool):
        """
        Enable or disable send button.
        
        Args:
            enabled: Whether to enable the button
        """
        self.send_btn.setEnabled(enabled)
    
    def _on_send_clicked(self):
        """Handle send button click."""
        message = self.get_message_text()
        if message:
            self.message_sent.emit(message)
            self.clear_message_input()

