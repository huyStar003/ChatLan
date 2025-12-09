"""Dialog for selecting emojis."""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QVBoxLayout, 
                             QLabel, QPushButton, QTabWidget, QWidget, QGridLayout, 
                             QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class EmojiPicker(QDialog):
    """Dialog for selecting emojis."""
    
    emoji_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Initialize emoji picker dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Chọn Emoji")
        self.setFixedSize(400, 400)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        categories = {
            "😀 Mặt cười": ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚"],
            "❤️ Trái tim": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝"],
            "👍 Cử chỉ": ["👍", "👎", "👌", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👋", "🤚", "🖐️", "✋"],
            "🎉 Hoạt động": ["🎉", "🎊", "🎈", "🎁", "🎀", "🎂", "🍰", "🧁", "🍭", "🍬", "🍫", "🍩", "🍪", "☕", "🍵", "🥤", "🍺", "🍻"]
        }
        
        tab_widget = QTabWidget()
        
        # Set font that supports emojis
        emoji_font = QFont("Segoe UI Emoji", 16)

        for category_name, emojis in categories.items():
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            
            emoji_grid_widget = QWidget()
            emoji_grid_layout = QGridLayout(emoji_grid_widget)
            emoji_grid_layout.setSpacing(5)

            num_columns = 10
            
            for i, emoji_char in enumerate(emojis):
                row = i // num_columns
                col = i % num_columns
                
                # Create button
                emoji_btn = QPushButton()
                emoji_btn.setFixedSize(40, 40)
                emoji_btn.clicked.connect(lambda checked, e=emoji_char: self.select_emoji(e))
                emoji_btn.setStyleSheet("""
                    QPushButton {
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        background-color: white;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                        border-color: #0084ff;
                    }
                """)

                # Create layout for button to contain QLabel
                button_layout = QVBoxLayout(emoji_btn)
                button_layout.setContentsMargins(0, 0, 0, 0)
                
                # Create QLabel to display emoji
                emoji_label = QLabel(emoji_char)
                emoji_label.setFont(emoji_font)
                emoji_label.setAlignment(Qt.AlignCenter)
                
                # Add QLabel to button layout
                button_layout.addWidget(emoji_label)
                
                # Add button to grid
                emoji_grid_layout.addWidget(emoji_btn, row, col)
            
            scroll_area = QScrollArea()
            scroll_area.setWidget(emoji_grid_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("border: none;")
            
            tab_layout.addWidget(scroll_area)
            tab_widget.addTab(tab, category_name)
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
    
    def select_emoji(self, emoji_char: str):
        """
        Handle emoji selection.
        
        Args:
            emoji_char: Selected emoji character
        """
        self.emoji_selected.emit(emoji_char)
        self.accept()

