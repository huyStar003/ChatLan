import sys
import os
import subprocess
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QSplitter, QFrame, QLabel, QPushButton, QLineEdit,
                            QTextEdit, QListWidget, QListWidgetItem, QMenuBar,
                            QMenu, QAction, QStatusBar, QMessageBox, QFileDialog,
                            QProgressBar, QComboBox, QCheckBox, QTabWidget,
                            QScrollArea, QGroupBox, QDialog, QDialogButtonBox,
                            QTextBrowser, QApplication, QInputDialog,QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot, QThread, QSize
from PyQt5.QtGui import (QFont, QPixmap, QPainter, QColor, QBrush, QIcon, 
                        QTextCursor, QTextCharFormat, QKeySequence, QCursor,QFontMetrics)
from .socket_client import SocketClient
from datetime import datetime, timedelta  # Thêm timedelta import
import json
import base64
import mimetypes
import client.resources_rc 
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject 
from typing import List, Dict 

# Trong file: client/main_chat_window.py
# Thêm lớp này vào sau các dòng import
def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả dev và PyInstaller """
    try:
        # PyInstaller tạo một thư mục tạm thời và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Nếu không phải đang chạy từ file đã đóng gói, dùng đường dẫn bình thường
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources"))
    
    return os.path.join(base_path, relative_path)
class CreateGroupDialog(QDialog):
    """Dialog để tạo một nhóm chat mới."""
    def __init__(self, contacts, parent=None):
        super().__init__(parent)
        self.contacts = contacts
        self.setWindowTitle("Tạo nhóm chat mới")
        self.setMinimumSize(400, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        name_layout = QHBoxLayout()
        name_label = QLabel("Tên nhóm:")
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Nhập tên cho nhóm của bạn...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.group_name_input)
        layout.addLayout(name_layout)

        members_label = QLabel("Chọn thành viên:")
        layout.addWidget(members_label)

        self.members_list = QListWidget()
        self.members_list.setSelectionMode(QListWidget.MultiSelection)
        for contact in self.contacts:
            item = QListWidgetItem(f"{contact['display_name']} (@{contact['username']})")
            item.setData(Qt.UserRole, contact['id'])
            self.members_list.addItem(item)
        layout.addWidget(self.members_list)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_group_data(self):
        """Lấy thông tin nhóm và danh sách thành viên đã chọn."""
        group_name = self.group_name_input.text().strip()
        selected_items = self.members_list.selectedItems()
        member_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        return group_name, member_ids
class MediaViewerDialog(QDialog):
    """Cửa sổ để xem toàn bộ media, file hoặc link."""
    def __init__(self, title, messages, media_type, parent=None):
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
                # Hiển thị ảnh dưới dạng lưới
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
            else: # Hiển thị file/link dạng danh sách
                for msg in messages:
                    label = QLabel(msg.get('file_name') or msg.get('content'))
                    content_layout.addWidget(label)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)


# Trong file: client/main_chat_window.py
# Thêm lớp này vào sau các dòng import

class SearchResultDialog(QDialog):
    def __init__(self, query, results, parent=None):
        super().__init__(parent)
        self.query = query
        self.results = results
        self.setWindowTitle(f"Kết quả tìm kiếm cho: '{query}'")
        self.setMinimumSize(500, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tiêu đề
        title_label = QLabel(f"{len(self.results)} kết quả được tìm thấy")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # Danh sách kết quả
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
                results_list.setItemWidget(item_widget, item) # Sửa lỗi ở đây
        
        layout.addWidget(results_list)

        # Nút Đóng
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 0, Qt.AlignCenter)

    def create_result_widget(self, message):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)

        # Dòng 1: Người gửi và Thời gian
        header_layout = QHBoxLayout()
        sender_name = message['sender']['display_name']
        sender_label = QLabel(f"<strong>{sender_name}</strong>")
        
        timestamp = datetime.fromisoformat(message['timestamp']).strftime('%d/%m/%Y %H:%M')
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: #666;")

        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)

        # Dòng 2: Nội dung tin nhắn
        content_label = QLabel(message['content'])
        content_label.setWordWrap(True)

        layout.addLayout(header_layout)
        layout.addWidget(content_label)
        
        # Thêm đường kẻ phân cách
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        return widget


# Trong file: client/main_chat_window.py
# Thêm lớp này vào sau các dòng import

class UserProfileDialog(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Thông tin tài khoản")
        self.setFixedSize(350, 450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Phần Header với Avatar và Tên ---
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

        # --- Phần Body với thông tin chi tiết ---
        body_frame = QFrame()
        body_layout = QVBoxLayout(body_frame)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(15)

        # Username
        body_layout.addLayout(self.create_info_row(':/icons/at-sign.png', f"@{self.user_data.get('username', 'N/A')}"))
        # Email
        body_layout.addLayout(self.create_info_row(':/icons/email.png', self.user_data.get('email') or "Chưa cập nhật email"))
        # Trạng thái
        status_icon = ':/icons/status-online.png' if self.user_data.get('is_online') else ':/icons/status-offline.png'
        status_text = "Đang hoạt động" if self.user_data.get('is_online') else "Không hoạt động"
        body_layout.addLayout(self.create_info_row(status_icon, status_text))

        body_layout.addStretch()

        # --- Nút Đóng ---
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        
        layout.addWidget(header_frame, 1) # Chiếm 1 phần
        layout.addWidget(body_frame, 2)   # Chiếm 2 phần
        layout.addWidget(close_button, 0, Qt.AlignCenter)
        layout.setContentsMargins(10,10,10,10)


    def create_info_row(self, icon_path, text):
        row_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(icon_path).pixmap(QSize(20, 20)))
        text_label = QLabel(text)
        text_label.setFont(QFont("Arial", 10))
        row_layout.addWidget(icon_label)
        row_layout.addWidget(text_label)
        row_layout.addStretch()
        return row_layout

    def create_circular_avatar(self, avatar_data, size):
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

    def create_default_avatar_pixmap(self, size):
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



class EmojiPicker(QDialog):
    emoji_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chọn Emoji")
        self.setFixedSize(400, 400)
        self.init_ui()
    
    # >>> THAY THẾ HÀM init_ui NÀY <<<
    def init_ui(self):
        layout = QVBoxLayout()
        
        categories = {
            "😀 Mặt cười": ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚"],
            "❤️ Trái tim": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝"],
            "👍 Cử chỉ": ["👍", "👎", "👌", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👋", "🤚", "🖐️", "✋"],
            "🎉 Hoạt động": ["🎉", "🎊", "🎈", "🎁", "🎀", "🎂", "🍰", "🧁", "🍭", "🍬", "🍫", "🍩", "🍪", "☕", "🍵", "🥤", "🍺", "🍻"]
        }
        
        tab_widget = QTabWidget()
        
        # Chỉ định font chữ hỗ trợ emoji
        emoji_font = QFont("Segoe UI Emoji", 16) # Giảm kích thước font một chút cho vừa vặn

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
                
                # --- KỸ THUẬT MỚI: DÙNG QLABEL BÊN TRONG QPUSHBUTTON ---
                
                # 1. Tạo một nút bấm trống
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

                # 2. Tạo một layout cho nút bấm để chứa QLabel
                button_layout = QVBoxLayout(emoji_btn)
                button_layout.setContentsMargins(0, 0, 0, 0)
                
                # 3. Tạo QLabel để hiển thị emoji
                emoji_label = QLabel(emoji_char)
                emoji_label.setFont(emoji_font)
                emoji_label.setAlignment(Qt.AlignCenter) # Căn giữa emoji trong label
                
                # 4. Thêm QLabel vào layout của nút bấm
                button_layout.addWidget(emoji_label)
                
                # Thêm nút bấm (đã chứa label) vào lưới chính
                emoji_grid_layout.addWidget(emoji_btn, row, col)
            
            scroll_area = QScrollArea()
            scroll_area.setWidget(emoji_grid_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("border: none;")
            
            tab_layout.addWidget(scroll_area)
            tab_widget.addTab(tab, category_name)
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
    
    def select_emoji(self, emoji_char):
        self.emoji_selected.emit(emoji_char)
        self.accept()
# >>> THÊM LỚP MỚI NÀY VÀO <<<
class ClickableFrame(QFrame):
    """Một QFrame tùy chỉnh có thể bắt sự kiện click chuột."""
    clicked = pyqtSignal() # Tạo một tín hiệu tên là 'clicked'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        # Khi sự kiện click chuột xảy ra
        if event.button() == Qt.LeftButton:
            self.clicked.emit() # Phát tín hiệu 'clicked'
            event.accept() # << QUAN TRỌNG: Ngăn sự kiện lan truyền lên cha
        else:
            super().mousePressEvent(event) # Xử lý các nút chuột khác (nếu có)
class ChatBubble(QWidget):
    def __init__(self, message_data, is_own_message=False, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.is_own_message = is_own_message
        self.init_ui()
    
    # >>> THAY THẾ TOÀN BỘ HÀM init_ui NÀY <<<
    def init_ui(self):
        # Layout chính cho bubble
        layout = QVBoxLayout()
        alignment = Qt.AlignRight if self.is_own_message else Qt.AlignLeft
        layout.setAlignment(alignment)
        layout.setContentsMargins(10, 5, 10, 5)

        # Container chính cho nội dung tin nhắn
        message_container = QFrame()
        message_container.setMaximumWidth(450) 
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(12, 8, 12, 8)
        message_layout.setSpacing(4)

        
        # Điều kiện đúng: kiểm tra sự tồn tại của 'group_id'
        is_group_message = self.message_data.get('group_id') is not None
        
        # Chỉ hiển thị tên người gửi cho tin nhắn NHẬN ĐƯỢC trong chat NHÓM
        if not self.is_own_message and is_group_message:
            sender_label = QLabel(self.message_data['sender']['display_name'])
            sender_label.setFont(QFont("Arial", 9, QFont.Bold))
            sender_label.setStyleSheet("color: #005ae0; margin-bottom: 2px;")
            message_layout.addWidget(sender_label)

        # =================================================================
        # === KẾT THÚC SỬA LỖI ===
        # =================================================================

        # Nội dung tin nhắn (văn bản)
        content_text = self.message_data.get('content', '')
        content_label = QLabel(content_text)
        content_label.setFont(QFont("Arial", 11))
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if content_text and self.message_data.get('message_type') == 'text':
             message_layout.addWidget(content_label)

        # Nội dung file/ảnh (nếu có)
        message_type = self.message_data.get('message_type', 'text')
        if message_type == 'image' and self.message_data.get('file_data'):
            self.add_image_content(message_layout)
        elif message_type == 'file' and self.message_data.get('file_data'):
            self.add_file_content(message_layout)

        # Thời gian gửi (timestamp)
        timestamp_str = self.format_timestamp(self.message_data['timestamp'])
        timestamp_label = QLabel(timestamp_str)
        timestamp_label.setFont(QFont("Arial", 8))
        timestamp_label.setAlignment(Qt.AlignRight)
        message_layout.addWidget(timestamp_label)

        # Thiết lập màu sắc và style
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
    
    def add_image_content(self, layout):
        """Thêm nội dung hình ảnh"""
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
    
    def add_file_content(self, layout):
        """Thêm nội dung file với ClickableFrame để xử lý click chính xác."""
        
        # --- Container chính cho widget file, sử dụng lớp mới ---
        file_frame = ClickableFrame() # <<< THAY ĐỔI Ở ĐÂY
        file_frame.clicked.connect(self.open_file) # <<< KẾT NỐI TÍN HIỆU MỚI
        file_frame.setToolTip("Mở file bằng ứng dụng mặc định")

        file_layout = QHBoxLayout(file_frame)
        file_layout.setContentsMargins(10, 8, 10, 8)
        file_layout.setSpacing(10)
        
        # --- Icon file ---
        file_icon_label = QLabel()
        file_icon_label.setPixmap(QIcon(resource_path('icons/attachment.png')).pixmap(QSize(28, 28)))
        
        # --- Thông tin file (tên và kích thước) ---
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
        
        # --- Nút tải về ---
        download_btn = QPushButton()
        download_btn.setIcon(QIcon(resource_path('icons/download.png')))
        download_btn.setIconSize(QSize(20, 20))
        download_btn.setFixedSize(30, 30)
        download_btn.setCursor(Qt.PointingHandCursor)
        download_btn.setToolTip("Lưu file về máy")
        download_btn.clicked.connect(self.download_file)
        
        # --- Thêm các thành phần vào layout ---
        file_layout.addWidget(file_icon_label, alignment=Qt.AlignCenter)
        file_layout.addLayout(file_info_layout)
        file_layout.addStretch()
        file_layout.addWidget(download_btn, alignment=Qt.AlignCenter)
        
        # --- StyleSheet ---
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
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 15px;
            }}
            QPushButton:hover {{
background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
        layout.addWidget(file_frame)
        
    def open_file(self):
        """Mở file bằng ứng dụng mặc định."""
        try:
            file_data = base64.b64decode(self.message_data['file_data'])
            file_name = self.message_data.get('file_name', 'download')
            
            # Lưu file vào thư mục tạm thời
            temp_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ChatLAN_Temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, file_name)

            with open(temp_path, 'wb') as f:
                f.write(file_data)

            # Mở file bằng ứng dụng mặc định
            if sys.platform == "win32":
                os.startfile(temp_path)
            elif sys.platform == "darwin":
                subprocess.Popen(['open', temp_path])
            else:
                subprocess.Popen(['xdg-open', temp_path])

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở file: {str(e)}")

    def download_file(self):
        """Tải xuống file"""
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
    
    # <<<<<<<<<<<<<<<<<<< THAY THẾ HÀM NÀY >>>>>>>>>>>>>>>>>>>>
    def format_timestamp(self, timestamp_str):
        """Format timestamp một cách chính xác."""
        try:
            # Chuyển chuỗi ISO 8601 thành đối tượng datetime
            # Tách phần microsecond nếu có (ví dụ: .123456)
            if '.' in timestamp_str:
                timestamp_str = timestamp_str.split('.')[0]
            
            # Xử lý các định dạng phổ biến
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', ''))
            except ValueError:
                dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

            now = datetime.now()
            
            # So sánh ngày tháng
            if dt.date() == now.date():
                return dt.strftime("%H:%M") # Hôm nay: chỉ hiển thị giờ:phút
            elif dt.date() == (now.date() - timedelta(days=1)):
                return f"Hôm qua, {dt.strftime('%H:%M')}" # Hôm qua
            else:
                return dt.strftime("%d/%m/%Y %H:%M") # Ngày khác: hiển thị đầy đủ
        except Exception as e:
            print(f"Error formatting timestamp '{timestamp_str}': {e}")
            return timestamp_str # Trả về chuỗi gốc nếu có lỗi
    # <<<<<<<<<<<<<<<<<<<<<<<<<<< KẾT THÚC THAY THẾ >>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    def format_file_size(self, size_bytes):
        """Format file size"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

class MainChatWindow(QMainWindow):
    # >>> THÊM TÍN HIỆU NÀY VÀO ĐẦU LỚP <<<
    logged_out = pyqtSignal()
    def __init__(self, client: SocketClient, user_data: dict):
        super().__init__()
        
        self.client = client
        self.user_data = user_data
        self.current_chat_user = None
        self.current_chat_type = None   # "group" or "private"
        #self.messages = []
        self.message_cache = {} # THÊM DÒNG NÀY: Cache tin nhắn
        self.conversations = []
        self.contacts = []
        
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.stop_typing)
        self.typing_timer.setSingleShot(True)
        
        self.setup_client_connections()
        self.init_ui()
        self.setup_styles()
        #self.load_initial_data()
        
        # Auto refresh data every 30 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # 30 seconds
    

    # Thêm 2 hàm này vào trong lớp MainChatWindow

    def show_contact_context_menu(self, position):
        """Hiển thị menu chuột phải cho danh sách liên hệ."""
        item = self.contacts_list.itemAt(position)
        if not item:
            return
        
        widget = self.contacts_list.itemWidget(item)
        if not hasattr(widget, 'contact_data'):
            return
            
        user_data = widget.contact_data
        
        menu = QMenu()
        view_profile_action = QAction(QIcon(resource_path('icons/info.png')), "Xem thông tin", self)
        view_profile_action.triggered.connect(lambda: self.show_user_profile(user_data))
        menu.addAction(view_profile_action)
        
        menu.exec_(self.contacts_list.mapToGlobal(position))

    def show_conversation_context_menu(self, position):
        """Hiển thị menu chuột phải cho danh sách hội thoại."""
        item = self.conversations_list.itemAt(position)
        if not item:
            return
            
        widget = self.conversations_list.itemWidget(item)
        # Bỏ qua nếu là item chat nhóm
        if not hasattr(widget, 'conversation_data'):
            return
            
        user_data = widget.conversation_data['other_user']
        
        menu = QMenu()
        view_profile_action = QAction(QIcon(resource_path('icons/info.png')), "Xem thông tin", self)
        view_profile_action.triggered.connect(lambda: self.show_user_profile(user_data))
        menu.addAction(view_profile_action)
        
        menu.exec_(self.conversations_list.mapToGlobal(position))


    def show_user_profile(self, user_data):
        """Hiển thị dialog thông tin của một người dùng."""
        if not user_data:
            return
        dialog = UserProfileDialog(user_data, self)
        dialog.exec_()


    def get_current_chat_id(self):
        """Lấy ID định danh cho cuộc trò chuyện hiện tại."""
        if self.current_chat_type == "group":
            # Tạo ID duy nhất cho cache của nhóm
            return f"group_{self.current_group_id}"
        elif self.current_chat_user:
            return self.current_chat_user['username']
        return None
    

    # >>> THÊM HÀM MỚI NÀY VÀO CLASS MainChatWindow <<<
    def format_timestamp_for_list(self, timestamp_str):
        """Format timestamp cho danh sách hội thoại (gọn hơn)."""
        try:
            # Chuyển chuỗi ISO 8601 thành đối tượng datetime
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now()
            
            if dt.date() == now.date():
                return dt.strftime("%H:%M") # Hôm nay: chỉ hiển thị giờ:phút
            elif dt.date() == (now.date() - timedelta(days=1)):
                return "Hôm qua" # Hôm qua
            else:
                return dt.strftime("%d/%m") # Ngày khác: hiển thị ngày/tháng
        except Exception:
            return "" # Trả về chuỗi rỗng nếu có lỗi

    def clear_chat_display(self):
        """Xóa sạch tất cả các bubble tin nhắn trên màn hình."""
        # Vòng lặp phải duyệt ngược để tránh lỗi index khi xóa item
        for i in reversed(range(self.messages_layout.count())): 
            item = self.messages_layout.itemAt(i)
            # Chỉ xóa widget, không xóa spacer (cục đẩy)
            if item.widget():
                item.widget().setParent(None)


    # <<<<<<<<<<<<<<<<<<< THÊM HÀM MỚI NÀY >>>>>>>>>>>>>>>>>>>>
    def load_data_from_login(self, login_response_data):
        """Load dữ liệu ban đầu nhận được ngay sau khi đăng nhập."""
        print("Loading initial data from login response...")
        all_users = login_response_data.get('all_users', [])
        conversations = login_response_data.get('conversations', [])
        
        self.update_contacts([], all_users) # Cập nhật danh bạ
        self.update_conversations(conversations) # Cập nhật hội thoại
        
        self.start_group_chat() # Bắt đầu mặc định ở chat nhóm

    def load_initial_data(self):
        """Load dữ liệu ban đầu bằng cách gửi request đến server."""
        # Hàm này vẫn hữu ích cho việc làm mới thủ công
        print("Requesting initial data from server...")
        self.client.get_contacts()
        self.client.get_conversations()
        self.start_group_chat()  # Start with group chat
        # Kết thúc thêm hàm


    def setup_client_connections(self):
        """Kết nối signals từ socket client"""
        self.client.message_received.connect(self.on_message_received)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error_occurred.connect(self.on_error_occurred)
    
    def init_ui(self):
        print("Initializing UI")
        self.manual_close_confirmed = True  # Thêm dòng này
        self.setWindowTitle(f"Chat LAN - {self.user_data['user']['display_name']}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        


        
        # --- THAY ĐỔI CẤU TRÚC SPLITTER ---
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Phần 1: Sidebar trái (danh bạ, hội thoại)
        self.create_sidebar()
        self.main_splitter.addWidget(self.sidebar)
        
        # Phần 2: Khu vực chat chính
        self.create_chat_area()
        self.main_splitter.addWidget(self.chat_area)
        
        # Phần 3: Sidebar phải (thông tin hội thoại)
        self.create_info_sidebar()
        self.main_splitter.addWidget(self.info_sidebar)
        self.info_sidebar.setVisible(False) # Ẩn đi lúc đầu

        # Set splitter proportions
        self.main_splitter.setSizes([300, 600, 0]) # Ban đầu sidebar phải có size 0
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(1, False)
        
        main_layout.addWidget(self.main_splitter)
        # >>> ĐẢM BẢO 2 DÒNG NÀY TỒN TẠI <<<
        self.create_menu_bar()
        self.create_status_bar()


    # Trong file: client/main_chat_window.py
    # Thêm các hàm này vào lớp MainChatWindow

    def create_info_sidebar(self):
        """Tạo sidebar phải để hiển thị thông tin hội thoại."""
        self.info_sidebar = QFrame()
        self.info_sidebar.setFixedWidth(320)
        self.info_sidebar.setStyleSheet("background-color: #f0f2f5; border-left: 1px solid #e0e0e0;")
        
        # Layout chính cho sidebar, dùng QScrollArea để có thể cuộn
        main_layout = QVBoxLayout(self.info_sidebar)
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

    def toggle_info_sidebar(self, checked):
        """Ẩn/hiện sidebar thông tin."""
        self.info_sidebar.setVisible(checked)
        if checked:
            self.main_splitter.setSizes([300, 600, 320])
            self.update_info_sidebar() # Cập nhật nội dung khi mở
        else:
            self.main_splitter.setSizes([300, 920, 0])

    # >>> THAY THẾ HÀM update_info_sidebar <<<

    def update_info_sidebar(self):
        """Cập nhật sidebar thông tin. Yêu cầu dữ liệu từ server nếu cần."""
        # Xóa nội dung cũ
        layout = self.info_sidebar_layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Nếu là chat nhóm, gửi yêu cầu lấy danh sách thành viên.
        # Server sẽ trả về gói tin 'group_members_list', và on_message_received sẽ xử lý nó.
        if self.current_chat_type == "group" and self.current_group_id:
            self.info_sidebar_layout.addWidget(QLabel("Đang tải thông tin nhóm..."))
            self.client.get_group_members(self.current_group_id)
        
        # Nếu là chat riêng, hiển thị thông tin ngay lập tức
        elif self.current_chat_type == "private" and self.current_chat_user:
            self._build_sidebar_ui_from_data({}) # Xây dựng UI với dữ liệu rỗng trước
            
        layout.addStretch()
    def _build_sidebar_ui_from_data(self, data):
        """
        Xây dựng toàn bộ giao diện cho sidebar thông tin từ dữ liệu được cung cấp.
        """
        layout = self.info_sidebar_layout
        # Xóa nội dung cũ
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Lấy dữ liệu
        is_group = self.current_chat_type == "group"
        header_data = {'display_name': self.chat_title.text().replace("💬 ", "")} if is_group else self.current_chat_user
        
        creator_id = data.get('creator_id')
        members = data.get('members', [])
        current_user_id = self.user_data['user']['id']
        is_creator = (current_user_id == creator_id)

        # Header
        self._add_info_sidebar_header(header_data)

        # Widget cuộn
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        if is_group and is_creator and self.current_group_id != 1:
            add_member_btn = QPushButton(QIcon(resource_path('icons/user-plus.png')), " Thêm thành viên")
            add_member_btn.clicked.connect(self.show_add_member_dialog)
            add_member_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #e7f3ff; color: #005ae0; border: 1px solid #d1e7ff;
                    padding: 8px; border-radius: 6px; text-align: center; font-weight: bold;
                }
                QPushButton:hover { background-color: #d1e7ff; }
            """)
            scroll_layout.addWidget(add_member_btn)

        # 2. HỘP THÀNH VIÊN (QGroupBox)
        #    Được thêm vào scroll_layout, nằm ngay bên dưới nút "Thêm thành viên".
        if is_group:
            members_box = QGroupBox(f"Thành viên ({len(members)})")
            members_box.setFont(QFont("Arial", 11, QFont.Bold))
            members_box_layout = QVBoxLayout(members_box) # Layout BÊN TRONG groupbox

            # Danh sách thành viên được thêm vào layout của groupbox
            for member in members:
                member_widget = self.create_member_widget(member, creator_id, is_creator)
                members_box_layout.addWidget(member_widget)
            
            scroll_layout.addWidget(members_box) # Thêm groupbox vào layout chính

        # =================================================================
        # === KẾT THÚC SỬA LỖI ===
        # =================================================================

        # 3. KHU VỰC MEDIA
        chat_id = self.get_current_chat_id()
        messages = self.message_cache.get(chat_id, [])
        
        media_messages = [m for m in messages if m.get('message_type') == 'image']
        if media_messages:
            self._add_media_section("Ảnh/Video", media_messages, 'image', scroll_layout)

        file_messages = [m for m in messages if m.get('message_type') == 'file']
        if file_messages:
            self._add_media_section("File đã gửi", file_messages, 'file', scroll_layout)

        # Hoàn thiện layout
        scroll_layout.addStretch()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)
        scroll_area.setStyleSheet("border: none; background-color: transparent;")
        layout.addWidget(scroll_area)
    def create_member_widget(self, member_data, creator_id, is_current_user_creator):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Avatar (giữ nguyên)
        avatar_label = QLabel()
        avatar_label.setFixedSize(30, 30)
        avatar_label.setStyleSheet("background-color: #ccc; border-radius: 15px;")
        
        # Tên và vai trò (giữ nguyên)
        info_layout = QVBoxLayout()
        name_label = QLabel(member_data['display_name'])
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        info_layout.addWidget(name_label)

        if member_data['id'] == creator_id:
            role_label = QLabel("Nhóm trưởng")
            role_label.setFont(QFont("Arial", 8, QFont.StyleItalic))
            role_label.setStyleSheet("color: #e67e22;")
            info_layout.addWidget(role_label)

        layout.addWidget(avatar_label)
        layout.addLayout(info_layout)
        layout.addStretch()

        # Nút Xóa (chỉ nhóm trưởng thấy và không thể xóa chính mình)
        if is_current_user_creator and member_data['id'] != creator_id and self.current_group_id != 1:
            remove_btn = QPushButton(QIcon(resource_path('icons/user-minus.png')), "")
            remove_btn.setFixedSize(28, 28)
            remove_btn.setIconSize(QSize(16, 16)) # Chỉnh kích thước icon cho phù hợp
            remove_btn.setToolTip(f"Xóa {member_data['display_name']} khỏi nhóm")
            remove_btn.clicked.connect(lambda: self.remove_member(member_data['id']))
            
            # --- THÊM STYLESHEET CHO NÚT NÀY ---
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

    # Thêm các hàm xử lý sự kiện
    def show_add_member_dialog(self):
        """Hiển thị dialog để chọn người dùng thêm vào nhóm."""
        # Lấy danh sách thành viên hiện tại để loại trừ
        group_members_response = self.client.get_group_members(self.current_group_id)
        # Đây là một lời gọi bất đồng bộ, để đơn giản, ta sẽ lấy danh sách contact hiện có
        
        current_members_ids = []
        # (Logic lấy member ID từ sidebar sẽ phức tạp, ta sẽ lấy từ danh sách contact và lọc)
        
        # Lấy danh sách tất cả các contact
        all_contacts = self.contacts
        
        # Lọc ra những người chưa có trong nhóm
        # (Cần có danh sách thành viên hiện tại từ server để làm chính xác)
        # Giả sử ta có `self.current_group_members` được cập nhật từ `group_members_list`
        
        # Để đơn giản hóa, ta sẽ hiển thị tất cả contact và server sẽ kiểm tra
        items = [f"{c['display_name']} (@{c['username']})" for c in self.contacts]
        if not items:
            QMessageBox.information(self, "Thông báo", "Không có người dùng nào khác để thêm.")
            return

        item, ok = QInputDialog.getItem(self, "Thêm thành viên", "Chọn người dùng để thêm vào nhóm:", items, 0, False)
        
        if ok and item:
            # Tìm lại user_id từ item đã chọn
            selected_username = item.split('@')[1][:-1]
            selected_user = next((c for c in self.contacts if c['username'] == selected_username), None)
            if selected_user:
                self.client.add_group_member(self.current_group_id, selected_user['id'])

    def remove_member(self, member_id):
        """Gửi yêu cầu xóa thành viên."""
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xóa thành viên này khỏi nhóm?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.client.remove_group_member(self.current_group_id, member_id)

    def _add_info_sidebar_header(self, target_data):
        """Tạo phần header cho info sidebar."""
        header_widget = QWidget()
        layout = QVBoxLayout(header_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        avatar_label = QLabel()
        avatar_label.setFixedSize(80, 80)
        # (Cần hàm tạo avatar hình tròn)
        # avatar_pixmap = self.create_circular_avatar(...)
        # avatar_label.setPixmap(avatar_pixmap)
        avatar_label.setStyleSheet("background-color: #ccc; border-radius: 40px;") # Placeholder

        name_label = QLabel(target_data['display_name'])
        name_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        layout.addWidget(avatar_label)
        layout.addWidget(name_label)
        self.info_sidebar_layout.addWidget(header_widget)

    def _add_info_sidebar_actions(self, is_group):
        """Tạo các nút hành động nhanh."""
        actions_widget = QWidget()
        layout = QGridLayout(actions_widget)
        
        # Hàm trợ giúp
        def create_action_button(icon_path, text):
            widget = QWidget()
            v_layout = QVBoxLayout(widget)
            v_layout.setAlignment(Qt.AlignCenter)
            
            icon_btn = QPushButton(QIcon(icon_path), "")
            icon_btn.setIconSize(QSize(24, 24))
            icon_btn.setFixedSize(48, 48)
            icon_btn.setStyleSheet("background-color: #e4e6eb; border-radius: 24px;")
            
            text_label = QLabel(text)
            text_label.setFont(QFont("Arial", 9))
            
            v_layout.addWidget(icon_btn)
            v_layout.addWidget(text_label)
            return widget

            
        self.info_sidebar_layout.addWidget(actions_widget)


    def _add_media_section(self, title, messages, media_type, target_layout):
        """Tạo một khu vực hiển thị media và thêm vào layout được chỉ định."""
        # Tiêu đề khu vực
        header_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        
        see_all_btn = QPushButton("Xem tất cả")
        see_all_btn.setStyleSheet("border: none; color: #0084ff;")
        see_all_btn.clicked.connect(lambda: self.show_media_viewer(title, messages, media_type))
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(see_all_btn)
        target_layout.addLayout(header_layout) # Thêm vào layout đích

        # Nội dung (lưới ảnh hoặc danh sách file)
        content_widget = QWidget()
        if media_type == 'image':
            layout = QGridLayout(content_widget)
            layout.setSpacing(5)
            num_columns = 3
            for i, msg in enumerate(messages[:6]):
                row, col = divmod(i, num_columns)
                try:
                    pixmap = QPixmap()
                    pixmap.loadFromData(base64.b64decode(msg['file_data']))
                    img_label = QLabel()
                    img_label.setPixmap(pixmap.scaled(85, 85, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                    img_label.setFixedSize(85, 85)
                    img_label.setStyleSheet("border-radius: 8px;")
                    layout.addWidget(img_label, row, col)
                except Exception as e:
                    print(f"Lỗi load ảnh thumbnail: {e}")
        else: # file
            layout = QVBoxLayout(content_widget)
            layout.setSpacing(5)
            for msg in messages[:4]:
                label = QLabel(f"📄 {msg.get('file_name', 'N/A')}")
                layout.addWidget(label)
        
        target_layout.addWidget(content_widget) # Thêm vào layout đích
        
        # Thêm đường kẻ phân cách
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("border-color: #ddd;")
        target_layout.addWidget(line) # Thêm vào layout đích


    def show_media_viewer(self, title, messages, media_type):
        """Mở dialog để xem toàn bộ media/file."""
        dialog = MediaViewerDialog(title, messages, media_type, self)
        dialog.exec_()

    # >>> THAY THẾ HÀM create_media_box <<<
    def create_media_box(self, title, messages, media_type):
        """Tạo QGroupBox, hiển thị ảnh dạng lưới hoặc file dạng danh sách."""
        box = QGroupBox(title)
        box.setFont(QFont("Arial", 11, QFont.Bold))
        
        # Layout chính cho box
        box_layout = QVBoxLayout(box)

        if media_type == 'image':
            # Sử dụng QGridLayout cho ảnh
            content_layout = QGridLayout()
            num_columns = 3
            # Chỉ hiển thị tối đa 6 ảnh trong sidebar
            for i, msg in enumerate(messages[:6]):
                row, col = divmod(i, num_columns)
                try:
                    pixmap = QPixmap()
                    pixmap.loadFromData(base64.b64decode(msg['file_data']))
                    img_label = QLabel()
                    img_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    img_label.setFixedSize(80, 80)
                    img_label.setStyleSheet("border: 1px solid #ddd; border-radius: 8px;")
                    content_layout.addWidget(img_label, row, col)
                except Exception as e:
                    print(f"Lỗi load ảnh thumbnail: {e}")
            box_layout.addLayout(content_layout)
        else: # media_type == 'file'
            # Sử dụng QVBoxLayout cho file
            content_layout = QVBoxLayout()
            for msg in messages[:4]: # Hiển thị 4 file đầu tiên
                file_name = msg.get('file_name', 'Không có tên')
                label = QLabel(file_name)
                content_layout.addWidget(label)
            box_layout.addLayout(content_layout)

        # Nút "Xem tất cả"
        if len(messages) > (6 if media_type == 'image' else 4):
            see_all_btn = QPushButton("Xem tất cả")
            # Kết nối nút với hàm mở dialog
            see_all_btn.clicked.connect(lambda: self.show_media_viewer(title, messages, media_type))
            box_layout.addWidget(see_all_btn, 0, Qt.AlignCenter)

        return box





    def create_sidebar(self):
        """Tạo sidebar"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # User info header
        self.create_user_header(sidebar_layout)
        
        action_frame = QFrame()
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(10, 5, 10, 5)

        self.create_group_btn = QPushButton(QIcon(resource_path('icons/users.png')), " Tạo nhóm mới")
        self.create_group_btn.clicked.connect(self.show_create_group_dialog)
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
        sidebar_layout.addWidget(action_frame)



        # Tab widget for conversations and contacts
        self.sidebar_tabs = QTabWidget()
        self.sidebar_tabs.setFont(QFont("Arial", 10))
        
        # Conversations tab
        conversations_tab = QWidget()
        conversations_layout = QVBoxLayout(conversations_tab)
        conversations_layout.setContentsMargins(10, 10, 10, 10)
        conversations_layout.setSpacing(0) # Đặt spacing về 0
        
        # Group chat button
        #self.group_chat_btn = QPushButton("💬 Chat nhóm")
        #self.group_chat_btn.setFont(QFont("Arial", 10, QFont.Bold))
        #self.group_chat_btn.clicked.connect(self.start_group_chat)
        #conversations_layout.addWidget(self.group_chat_btn)
        
        # Conversations list
        self.conversations_list = QListWidget()
        self.conversations_list.itemClicked.connect(self.on_conversation_selected)
        # >>> THÊM 2 DÒNG NÀY <<<
        self.conversations_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.conversations_list.customContextMenuRequested.connect(self.show_conversation_context_menu)


        conversations_layout.addWidget(self.conversations_list)
        
    
        # Contacts tab
        contacts_tab = QWidget()
        contacts_layout = QVBoxLayout(contacts_tab)
        contacts_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search contacts
        self.contact_search = QLineEdit()
        self.contact_search.setPlaceholderText("🔍 Tìm kiếm liên hệ...")
        self.contact_search.textChanged.connect(self.filter_contacts)
        contacts_layout.addWidget(self.contact_search)
        
        # Contacts list
        self.contacts_list = QListWidget()
        self.contacts_list.itemClicked.connect(self.on_contact_selected)
        # >>> THÊM 2 DÒNG NÀY <<<
        self.contacts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contacts_list.customContextMenuRequested.connect(self.show_contact_context_menu)
        contacts_layout.addWidget(self.contacts_list)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Làm mới")
        self.refresh_btn.setFont(QFont("Arial", 9))
        self.refresh_btn.clicked.connect(self.refresh_data)
        contacts_layout.addWidget(self.refresh_btn)
        
        # Add tabs
        self.sidebar_tabs.addTab(conversations_tab, "💬 Hội thoại")
        self.sidebar_tabs.addTab(contacts_tab, "👥 Danh bạ")
        
        sidebar_layout.addWidget(self.sidebar_tabs)
    
    # Thêm hàm này vào trong lớp MainChatWindow

    def show_create_group_dialog(self):
        """Hiển thị dialog để tạo nhóm mới."""
        # Chỉ lấy các contact không phải là chính mình
        contacts_for_group = [c for c in self.contacts if c['id'] != self.user_data['user']['id']]
        if not contacts_for_group:
            QMessageBox.information(self, "Thông báo", "Bạn cần có ít nhất một liên hệ để tạo nhóm.")
            return

        dialog = CreateGroupDialog(contacts_for_group, self)
        if dialog.exec_() == QDialog.Accepted:
            group_name, member_ids = dialog.get_group_data()
            
            if not group_name:
                QMessageBox.warning(self, "Lỗi", "Tên nhóm không được để trống.")
                return
            # Một nhóm cần ít nhất 2 người (bạn và 1 người khác)
            if len(member_ids) < 1:
                QMessageBox.warning(self, "Lỗi", "Bạn phải chọn ít nhất một thành viên để tạo nhóm.")
                return
            
            # Gửi yêu cầu tạo nhóm lên server
            print(f"Đang gửi yêu cầu tạo nhóm '{group_name}' với thành viên: {member_ids}")
            self.client.create_group(group_name, member_ids)
    def create_group_chat_widget(self):
        """Tạo widget cho item 'Chat nhóm' theo phong cách Zalo."""
        widget = QWidget()
        # Layout chính cho toàn bộ item
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # --- 1. Avatar nhóm (hiện tại dùng icon mặc định) ---
        # Việc tạo avatar ghép đòi hỏi logic phức tạp, tạm thời dùng icon nhóm
        avatar_label = QLabel()
        group_icon = QIcon(resource_path('icons/users.png')) # Sử dụng icon mới
        avatar_label.setPixmap(group_icon.pixmap(QSize(50, 50)))
        avatar_label.setFixedSize(50, 50)

        # --- 2. Cột thông tin (Tên nhóm và số thành viên) ---
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Tên nhóm
        group_name_label = QLabel("Chat nhóm")
        group_name_label.setFont(QFont("Arial", 11, QFont.Bold))
        group_name_label.setStyleSheet("color: #333;")

        # Dòng thông tin số thành viên
        member_info_layout = QHBoxLayout()
        member_info_layout.setSpacing(5)
        
        member_icon = QLabel()
        member_icon.setPixmap(QIcon(resource_path('icons/users.png')).pixmap(QSize(14, 14)))
        
        # Lấy số lượng thành viên (tổng số contact + chính mình)
        member_count = len(self.contacts) + 1 
        member_count_label = QLabel(f"{member_count} thành viên")
        member_count_label.setFont(QFont("Arial", 9))
        member_count_label.setStyleSheet("color: #666;")

        member_info_layout.addWidget(member_icon)
        member_info_layout.addWidget(member_count_label)
        member_info_layout.addStretch()

        info_layout.addWidget(group_name_label)
        info_layout.addLayout(member_info_layout)

        # --- Thêm các thành phần vào layout chính ---
        main_layout.addWidget(avatar_label)
        main_layout.addLayout(info_layout)
        main_layout.addStretch()
        
        # Lưu một thuộc tính để nhận biết đây là item chat nhóm
        widget.is_group_chat_item = True
        
        return widget


    def create_user_header(self, layout):
        """Tạo header thông tin user với icon chuẩn."""
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
        self.set_user_avatar()
        
        # User info
        user_info_layout = QVBoxLayout()
        
        self.user_name_label = QLabel(self.user_data['user']['display_name'])
        self.user_name_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.user_name_label.setStyleSheet("color: #333;")
        
        # Status selector
        self.status_combo = QComboBox()
        self.status_combo.addItems(["🟢 Online", "🟡 Away", "🔴 Busy"])
        self.status_combo.setFont(QFont("Arial", 9))
        self.status_combo.currentTextChanged.connect(self.update_user_status)
        
        user_info_layout.addWidget(self.user_name_label)
        user_info_layout.addWidget(self.status_combo)
        


        # --- ĐÂY LÀ THAY ĐỔI CHÍNH ---
        # Nút Cài đặt / Thông tin cá nhân
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon(resource_path('icons/settings.png'))) # Sử dụng icon từ resource
        self.settings_btn.setIconSize(QSize(20, 20)) # Đặt kích thước icon
        self.settings_btn.setFixedSize(35, 35)
        self.settings_btn.setToolTip("Xem thông tin cá nhân")
        self.settings_btn.clicked.connect(lambda: self.show_user_profile(self.user_data['user']))
        
        # Áp dụng style cho nút
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
    
    def create_chat_area(self):
        """Tạo khu vực chat"""
        self.chat_area = QFrame()
        chat_layout = QVBoxLayout(self.chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat header
        self.create_chat_header(chat_layout)
        


        # <<<<<<<<<<<<<<<<<<< THAY ĐỔI LOGIC Ở ĐÂY >>>>>>>>>>>>>>>>>>>>
        # Messages area
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget chứa tất cả các bubble chat
        self.messages_container = QWidget()
        self.messages_scroll.setWidget(self.messages_container)

        # Layout chính cho các bubble chat, đặt bên trong container
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(5)
        
        # Thêm một "cục đẩy" (spacer) để các tin nhắn luôn bắt đầu từ trên xuống
        self.messages_layout.addStretch()
        
        chat_layout.addWidget(self.messages_scroll)
        # <<<<<<<<<<<<<<<<<<<<<<<<<<< KẾT THÚC >>>>>>>>>>>>>>>>>>>>>>>>>>>>
        


        # Typing indicator
        self.typing_indicator = QLabel("")
        font = QFont("Arial", 9)
        font.setStyle(QFont.StyleItalic)
        self.typing_indicator.setFont(font)
        self.typing_indicator.setStyleSheet("color: #666; padding: 5px 15px;")
        self.typing_indicator.setVisible(False)
        chat_layout.addWidget(self.typing_indicator)
        
        # Input area
        self.create_input_area(chat_layout)
    
    def create_chat_header(self, layout):
        """Tạo header chat"""
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
        



        # --- CÁC THAY ĐỔI CHÍNH NẰM Ở ĐÂY ---
        
        # Nút Tìm kiếm
        self.search_btn = QPushButton()
        self.search_btn.setIcon(QIcon(resource_path('icons/search.png'))) # Sử dụng icon
        self.search_btn.setIconSize(QSize(20, 20))
        self.search_btn.setFixedSize(35, 35)
        self.search_btn.setToolTip("Tìm kiếm tin nhắn (Ctrl+F)")
        self.search_btn.setShortcut("Ctrl+F")
        self.search_btn.clicked.connect(self.show_search_dialog)
        
        # Nút Xóa Chat
        self.clear_chat_btn = QPushButton()
        self.clear_chat_btn.setIcon(QIcon(resource_path('icons/delete.png'))) # Sử dụng icon
        self.clear_chat_btn.setIconSize(QSize(20, 20))
        self.clear_chat_btn.setFixedSize(35, 35)
        self.clear_chat_btn.setToolTip("Xóa lịch sử chat")
        self.clear_chat_btn.clicked.connect(self.clear_current_chat)




        # Thêm các widget vào layout
        header_layout.addWidget(self.chat_title)
        header_layout.addWidget(self.chat_status)
        header_layout.addStretch()
        header_layout.addWidget(self.search_btn)
        header_layout.addWidget(self.clear_chat_btn)
        
        # >>> THÊM NÚT MỚI VÀO ĐÂY <<<
        self.info_sidebar_btn = QPushButton()
        self.info_sidebar_btn.setIcon(QIcon(resource_path('icons/info-sidebar.png')))
        self.info_sidebar_btn.setIconSize(QSize(20, 20))
        self.info_sidebar_btn.setFixedSize(35, 35)
        self.info_sidebar_btn.setToolTip("Thông tin hội thoại")
        self.info_sidebar_btn.setCheckable(True) # Làm cho nút có trạng thái on/off
        self.info_sidebar_btn.toggled.connect(self.toggle_info_sidebar)
        header_layout.addWidget(self.info_sidebar_btn)


        layout.addWidget(self.chat_header)
    
        # Áp dụng style cho các nút icon (đã có trong hàm setup_styles)
        # Bạn có thể copy style này vào đây để chắc chắn
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

    # >>> THAY THẾ HÀM create_input_area <<<
    def create_input_area(self, layout):
        """Tạo khu vực nhập tin nhắn với kích thước icon và nút cân đối."""
        input_frame = QFrame()
        input_frame.setFixedHeight(70) # Giảm chiều cao tổng thể một chút
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 10, 15, 10)
        
        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(8) # Giảm khoảng cách giữa các nút

        # --- CẤU HÌNH KÍCH THƯỚC ---
        BUTTON_SIZE = 40  # Kích thước của nút (hình vuông 40x40 pixels)
        ICON_SIZE = 22    # Kích thước của icon bên trong (hình vuông 22x22 pixels)
        
        # --- Nút Đính kèm file ---
        self.file_btn = QPushButton()
        self.file_btn.setIcon(QIcon(resource_path('icons/attachment.png')))
        self.file_btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE) 
        self.file_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.file_btn.setToolTip("Đính kèm file (Ctrl+O)")
        self.file_btn.setShortcut("Ctrl+O") # Thêm phím tắt
        self.file_btn.clicked.connect(self.upload_file)
        
        # --- Nút Chọn Emoji ---
        self.emoji_btn = QPushButton()
        self.emoji_btn.setIcon(QIcon(resource_path('icons/emoji.png')))
        self.emoji_btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.emoji_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.emoji_btn.setToolTip("Chọn emoji (Ctrl+E)")
        self.emoji_btn.setShortcut("Ctrl+E") # Thêm phím tắt
        self.emoji_btn.clicked.connect(self.show_emoji_picker)
        
        # Ô nhập tin nhắn
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Nhập tin nhắn...")
        self.message_input.setFont(QFont("Arial", 11))
        self.message_input.textChanged.connect(self.on_message_input_changed)
        self.message_input.installEventFilter(self)
        
        # Nút Gửi
        self.send_btn = QPushButton("Gửi")
        self.send_btn.setFixedSize(60, 40)
        self.send_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setEnabled(False)
        
        # Thêm các widget vào layout
        input_row_layout.addWidget(self.file_btn)
        input_row_layout.addWidget(self.emoji_btn)
        input_row_layout.addWidget(self.message_input)
        input_row_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(input_row_layout)
        layout.addWidget(input_frame)

        # --- StyleSheet để hoàn thiện giao diện ---
        icon_button_style = """
            QPushButton {
                background-color: transparent; /* Nền trong suốt */
                border: none; /* Bỏ viền */
                border-radius: 20px; /* Bo tròn hoàn hảo */
            }
            QPushButton:hover {
                background-color: #e9ecef; /* Màu nền khi di chuột qua */
            }
            QPushButton:pressed {
                background-color: #dde0e3; /* Màu nền khi nhấn */
            }
        """
        self.file_btn.setStyleSheet(icon_button_style)
        self.emoji_btn.setStyleSheet(icon_button_style)
    
    def create_menu_bar(self):
        """Tạo menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        export_action = QAction('📤 Export Chat', self)
        export_action.triggered.connect(self.export_chat)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        logout_action = QAction('🚪 Đăng xuất', self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        exit_action = QAction('❌ Thoát', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        refresh_action = QAction('🔄 Làm mới', self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('ℹ️ Về chúng tôi', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """Tạo status bar"""
        self.status_bar = self.statusBar()
        
        # Connection status
        self.connection_label = QLabel("🟢 Đã kết nối")
        self.connection_label.setStyleSheet("color: #28a745; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # Message count
        # Đảm bảo rằng self.message_count_label được tạo ra ở đây
        self.message_count_label = QLabel("0 tin nhắn")
        self.message_count_label.setStyleSheet("margin-right: 10px;")
        self.status_bar.addPermanentWidget(self.message_count_label)
        
        # Show ready message
        self.status_bar.showMessage("Sẵn sàng", 3000)
    
    def setup_styles(self):
        """Thiết lập styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QFrame {
                background-color: #f8f9fa;
                border: none;
            }
            QSplitter::handle {
                background-color: #e1e5e9;
                width: 1px;
            }
            QTabWidget::pane {
                border: 1px solid #e1e5e9;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #e1e5e9;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-color: #0084ff;
                color: #0084ff;
            }
            QListWidget {
                background-color: white;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e1e5e9;
                border-radius: 20px;
                background-color: white;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #0084ff;
                outline: none;
            }
            QTextEdit {
                padding: 8px 12px;
                border: 2px solid #e1e5e9;
                border-radius: 12px;
                background-color: white;
                font-size: 11px;
            }
            QTextEdit:focus {
                border-color: #0084ff;
                outline: none;
            }
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
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
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #e1e5e9;
                border-radius: 6px;
                background-color: white;
                font-size: 9px;
            }
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #ccc;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #999;
            }
        """)
        
        # Special styles for specific buttons
#        self.group_chat_btn.setStyleSheet("""
#            QPushButton {
#                background-color: #28a745;
#                color: white;
#                border: none;
#                padding: 10px;
#                border-radius: 8px;
#                font-weight: bold;
#            }
#            QPushButton:hover {
#                background-color: #218838;
#            }""")
        
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        # Icon buttons
        icon_button_style = """
            QPushButton {
                background-color: #f8f9fa;
                color: #333;
                border: 1px solid #e1e5e9;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #0084ff;
            }
        """
        
        self.file_btn.setStyleSheet(icon_button_style)
        self.emoji_btn.setStyleSheet(icon_button_style)
        self.settings_btn.setStyleSheet(icon_button_style)
        self.search_btn.setStyleSheet(icon_button_style)
        self.clear_chat_btn.setStyleSheet(icon_button_style)
        
        # Chat header style
        self.chat_header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e1e5e9;
            }
        """)
    
    def set_user_avatar(self):
        """Đặt avatar user"""
        avatar_data = self.user_data['user'].get('avatar')
        if avatar_data:
            try:
                image_data = base64.b64decode(avatar_data)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                
                # Create circular avatar
                circular_pixmap = self.create_circular_avatar(pixmap, 50)
                self.user_avatar.setPixmap(circular_pixmap)
            except:
                self.set_default_avatar()
        else:
            self.set_default_avatar()
    
    def set_default_avatar(self):
        """Đặt avatar mặc định"""
        pixmap = QPixmap(50, 50)
        pixmap.fill(QColor("#0084ff"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        
        # Draw first letter of display name
        display_name = self.user_data['user']['display_name']
        if display_name:
            painter.drawText(pixmap.rect(), Qt.AlignCenter, display_name[0].upper())
        
        painter.end()
        
        # Make circular
        circular_pixmap = self.create_circular_avatar(pixmap, 50)
        self.user_avatar.setPixmap(circular_pixmap)
    
    def create_circular_avatar(self, pixmap, size):
        """Tạo avatar hình tròn"""
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
    
    def load_initial_data(self):
        """Load dữ liệu ban đầu"""
        self.client.get_contacts()
        self.client.get_conversations()
        self.start_group_chat()  # Start with group chat
    
    def refresh_data(self):
        """Làm mới dữ liệu"""
        self.client.get_contacts()
        self.client.get_conversations()
        self.status_bar.showMessage("Đã làm mới dữ liệu", 2000)
    
    @pyqtSlot(dict)
    def on_message_received(self, message: Dict):
        """Xử lý tin nhắn từ server."""
        print(f"DEBUG CLIENT PROCESS -> DICT: {message}")

        message_type = message.get('type')
        success = message.get('success', True)
        
        if success:
            if message_type == 'get_contacts':
                self.update_contacts(message.get('online_users', []), message.get('all_users', []))
            
            elif message_type == 'get_conversations':
                self.update_conversations(message.get('conversations', []))
            
            elif message_type == 'get_messages':
                self.update_messages(message.get('messages', []))
            
            elif message_type == 'new_message':
                self.add_new_message(message.get('message'))

            elif message_type == 'user_status':
                self.update_user_status_display(message.get('user'))
            
            elif message_type == 'typing_status':
                self.update_typing_status(message.get('user'), message.get('is_typing', False))
            
            elif message_type == 'message_deleted':
                self.remove_message(message.get('message_id'))

            elif message_type == 'search_results':
                query = message.get('query', '')
                results = message.get('messages', [])
                search_dialog = SearchResultDialog(query, results, self)
                search_dialog.exec_()
            elif message_type == 'group_members_list':
                # Cập nhật sidebar với danh sách thành viên mới
                if message.get('group_id') == self.current_group_id and self.info_sidebar.isVisible():
                    self._build_sidebar_ui_from_data(message)
            elif message_type == 'removed_from_group':
                # Xử lý khi bị xóa khỏi nhóm
                group_id = message.get('group_id')
                self.conversations = [c for c in self.conversations if not (c.get('type') == 'group' and c.get('group_id') == group_id)]
                self.refresh_conversations_list()
                if self.current_group_id == group_id:
                    self.show_welcome_screen()
                QMessageBox.information(self, "Thông báo", "Bạn đã bị xóa khỏi một nhóm.")
            elif message_type == 'add_member_response' or message_type == 'remove_member_response':
                self.status_bar.showMessage(message.get('message', 'Thao tác hoàn tất.'), 3000)
            # Xử lý khi có thông báo về nhóm mới
            elif message_type == 'new_group_notification':
                new_conversation = message.get('conversation')
                if new_conversation:
                    QMessageBox.information(self, "Thông báo", f"Bạn đã được thêm vào nhóm '{new_conversation['group_name']}'")
                    # Thêm hội thoại mới vào đầu danh sách và làm mới giao diện
                    self.conversations.insert(0, new_conversation)
                    self.refresh_conversations_list()

        else: # Xử lý lỗi
            error_msg = message.get('error', 'Unknown error')
            if message_type == 'create_group':
                 QMessageBox.critical(self, "Lỗi tạo nhóm", f"Không thể tạo nhóm:\n{error_msg}")
            else:
                self.status_bar.showMessage(f"Lỗi: {error_msg}", 5000)
    
    @pyqtSlot()
    def on_disconnected(self):
        """Xử lý khi mất kết nối"""
        self.connection_label.setText("🔴 Mất kết nối")
        self.connection_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.status_bar.showMessage("Mất kết nối đến server", 5000)
        
        # Disable input
        self.message_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.file_btn.setEnabled(False)
    
    @pyqtSlot(str)
    def on_error_occurred(self, error_message):
        """Xử lý lỗi"""
        self.status_bar.showMessage(f"Lỗi: {error_message}", 5000)
    
    def update_contacts(self, online_users, all_users):
        """Cập nhật danh sách liên hệ"""
        self.contacts = all_users
        self.refresh_contacts_list()
    
    def refresh_contacts_list(self):
        """Làm mới danh sách liên hệ"""
        self.contacts_list.clear()
        
        search_text = self.contact_search.text().lower()
        
        for contact in self.contacts:
            if contact['username'] == self.user_data['user']['username']:
                continue  # Skip self
            
            display_name = contact['display_name']
            username = contact['username']
            
            # Filter by search text
            if search_text and search_text not in display_name.lower() and search_text not in username.lower():
                continue
            
            item = QListWidgetItem()
            
            # Create contact widget
            contact_widget = self.create_contact_widget(contact)
            item.setSizeHint(contact_widget.sizeHint())
            
            self.contacts_list.addItem(item)
            self.contacts_list.setItemWidget(item, contact_widget)
    
    # >>> THAY THẾ HÀM create_contact_widget <<<
    def create_contact_widget(self, contact):
        """Tạo widget cho contact với avatar nhất quán."""
        # Widget chính
        widget = QWidget()
        widget.setMinimumHeight(60) # Đặt chiều cao tối thiểu cho cân đối

        # Layout chính của widget
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8) # Đặt margin giống bên hội thoại
        layout.setSpacing(10)

        # --- Phần Avatar ---
        avatar_label = QLabel()
        avatar_label.setFixedSize(40, 40) # Kích thước avatar 40x40

        # Lấy chữ cái đầu
        display_name = contact.get('display_name', '?')
        first_letter = display_name[0].upper() if display_name else '?'
        
        # Tạo pixmap tròn với màu nền dựa trên trạng thái online/offline
        pixmap = QPixmap(40, 40)
        color = QColor("#28a745") if contact.get('is_online') else QColor("#6c757d") # Xanh: online, Xám: offline
        pixmap.fill(color)
        
        # Vẽ chữ cái lên pixmap
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, first_letter)
        painter.end()
        
        # Bo tròn avatar và đặt nó cho label
        # Tái sử dụng hàm create_circular_avatar đã có
        avatar_label.setPixmap(self.create_circular_avatar(pixmap, 40))

        # --- Phần Thông tin ---
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(3)
        
        # Tên hiển thị
        name_label = QLabel(contact['display_name'])
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setStyleSheet("color: #333;")
        
        # Username
        username_label = QLabel(f"@{contact['username']}")
        username_label.setFont(QFont("Arial", 9))
        username_label.setStyleSheet("color: #666;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(username_label)

        # --- Phần Trạng thái (chữ) ---
        status_text_label = QLabel("Online" if contact.get('is_online') else "Offline")
        status_text_label.setFont(QFont("Arial", 9))
        status_text_label.setAlignment(Qt.AlignRight) # Căn phải
        status_text_label.setStyleSheet(f"color: {'#28a745' if contact.get('is_online') else '#6c757d'};")

        # Thêm các thành phần vào layout chính
        layout.addWidget(avatar_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(status_text_label)
        
        # Lưu dữ liệu contact vào widget
        widget.contact_data = contact
        
        return widget
    
    def update_conversations(self, conversations):
        """Cập nhật danh sách hội thoại và đảm bảo nhóm chung (ID=1) luôn ở đầu."""
        
        # --- LOGIC MỚI: SẮP XẾP LẠI DANH SÁCH ---
        company_group = None
        other_conversations = []

        for conv in conversations:
            # Tìm và tách nhóm chung ra
            if conv.get('type') == 'group' and conv.get('group_id') == 1:
                company_group = conv
            else:
                other_conversations.append(conv)
                
        # Sắp xếp các hội thoại còn lại như bình thường (theo thời gian cập nhật)
        # (Server đã sắp xếp sẵn, nhưng để chắc chắn, ta có thể sắp xếp lại)
        other_conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)

        # Tạo danh sách cuối cùng: nhóm chung (nếu có) + các hội thoại khác
        final_conversations = []
        if company_group:
            final_conversations.append(company_group)
        final_conversations.extend(other_conversations)
        # -----------------------------------------

        self.conversations = final_conversations # Lưu lại danh sách đã sắp xếp
        self.refresh_conversations_list()
    def refresh_conversations_list(self):
        """Làm mới danh sách hội thoại, xử lý cả chat riêng và chat nhóm."""
        self.conversations_list.clear()
        
        # Không cần thêm item chat nhóm mặc định nữa vì server đã trả về
        
        for conversation in self.conversations:
            item = QListWidgetItem()
            conv_widget = None

            # KIỂM TRA LOẠI HỘI THOẠI
            if conversation.get('type') == 'private':
                conv_widget = self.create_conversation_widget(conversation)
            elif conversation.get('type') == 'group':
                conv_widget = self.create_group_conversation_widget(conversation)

            if conv_widget:
                item.setSizeHint(conv_widget.sizeHint())
                self.conversations_list.addItem(item)
                self.conversations_list.setItemWidget(item, conv_widget)

    # >>> THÊM HÀM MỚI NÀY VÀO LỚP <<<
    def create_group_conversation_widget(self, conversation):
        """Tạo widget cho một hội thoại nhóm trong danh sách."""
        widget = QWidget()
        widget.setMinimumHeight(60)
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(10)

        # Avatar nhóm
        avatar_label = QLabel()
        avatar_label.setFixedSize(40, 40)
        # Tạo avatar chữ cái từ tên nhóm
        group_name = conversation.get('group_name', 'G')
        first_letter = group_name[0].upper() if group_name else 'G'
        pixmap = QPixmap(40, 40)
        pixmap.fill(QColor("#1e88e5")) # Màu xanh cho nhóm
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, first_letter)
        painter.end()
        avatar_label.setPixmap(self.create_circular_avatar(pixmap, 40))

        # Thông tin nhóm
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        
        name_label = QLabel(group_name)
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        
        last_message = conversation.get('last_message')
        if last_message and last_message.get('sender'):
            sender_name = last_message['sender']['display_name']
            content = last_message['content']
            if len(content) > 20:
                content = content[:20] + "..."
            last_msg_text = f"{sender_name}: {content}"
            last_msg_label = QLabel(last_msg_text)
            last_msg_label.setFont(QFont("Arial", 9))
            last_msg_label.setStyleSheet("color: #666;")
        else:
            last_msg_label = QLabel(f"{conversation.get('member_count', 0)} thành viên")
            last_msg_label.setFont(QFont("Arial", 9, QFont.StyleItalic))
            last_msg_label.setStyleSheet("color: #999;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(last_msg_label)

        # Thời gian
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
        if last_message:
            timestamp_label = QLabel(self.format_timestamp_for_list(last_message['timestamp']))
            timestamp_label.setFont(QFont("Arial", 8))
            timestamp_label.setStyleSheet("color: #888;")
            timestamp_label.setAlignment(Qt.AlignRight)
            right_layout.addWidget(timestamp_label)

        main_layout.addWidget(avatar_label)
        main_layout.addLayout(info_layout)
        main_layout.addStretch()
        main_layout.addLayout(right_layout)
        
        # Lưu dữ liệu vào widget để xử lý click
        widget.conversation_data = conversation
        
        return widget
    def create_conversation_widget(self, conversation):
        """Tạo widget cho conversation với layout đã sửa lỗi"""
        # Widget chính, đặt chiều cao tối thiểu và style
        widget = QWidget()
        widget.setMinimumHeight(60) # Đặt chiều cao tối thiểu để có không gian

        # Layout chính của widget
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8) # Tăng khoảng đệm
        layout.setSpacing(10) # Tăng khoảng cách giữa các phần tử

        # Lấy thông tin người dùng khác trong hội thoại
        other_user = conversation['other_user']
        
        # Avatar hoặc chấm trạng thái
        # Thay vì chỉ dùng chấm, chúng ta có thể tạo avatar chữ cái giống header
        avatar_label = QLabel()
        avatar_label.setFixedSize(40, 40) # Kích thước avatar
        # Tạo avatar chữ cái
        display_name = other_user.get('display_name', '?')
        first_letter = display_name[0].upper() if display_name else '?'
        # Tạo pixmap tròn
        pixmap = QPixmap(40, 40)
        # Dùng màu khác nhau dựa trên trạng thái online/offline
        color = QColor("#28a745") if other_user.get('is_online') else QColor("#6c757d")
        pixmap.fill(color)
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, first_letter)
        painter.end()
        # Bo tròn avatar
        avatar_label.setPixmap(self.create_circular_avatar(pixmap, 40))

        # Layout cho phần thông tin (tên và tin nhắn cuối)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(3)
        
        # Tên người dùng
        name_label = QLabel(other_user['display_name'])
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setStyleSheet("color: #333;")
        
        # Tin nhắn cuối cùng
        last_message = conversation.get('last_message')
        if last_message:
            # Rút gọn tin nhắn cuối nếu quá dài
            last_msg_text = last_message['content']
            if len(last_msg_text) > 25:
                last_msg_text = last_msg_text[:25] + "..."
            last_msg_label = QLabel(last_msg_text)
            last_msg_label.setFont(QFont("Arial", 9))
            last_msg_label.setStyleSheet("color: #666;")
        else:
            last_msg_label = QLabel("Chưa có tin nhắn")
            last_msg_label.setFont(QFont("Arial", 9, QFont.StyleItalic))
            last_msg_label.setStyleSheet("color: #999;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(last_msg_label)

        # Layout cho phần bên phải (thời gian và số tin chưa đọc)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        right_layout.setAlignment(Qt.AlignTop) # Căn lề trên

        # Thời gian cập nhật
        if last_message:
            # Format lại timestamp cho gọn gàng
            timestamp_label = QLabel(self.format_timestamp_for_list(last_message['timestamp']))
            timestamp_label.setFont(QFont("Arial", 8))
            timestamp_label.setStyleSheet("color: #888;")
            timestamp_label.setAlignment(Qt.AlignRight)
            right_layout.addWidget(timestamp_label)

        # Số tin nhắn chưa đọc
        unread_count = conversation.get('unread_count', 0)
        if unread_count > 0:
            unread_label = QLabel(str(unread_count))
            unread_label.setFixedSize(20, 20)
            unread_label.setAlignment(Qt.AlignCenter)
            unread_label.setStyleSheet("""
                QLabel {
                    background-color: #dc3545;
                    color: white;
                    border-radius: 10px;
                    font-size: 9px;
                    font-weight: bold;
                }
            """)
            right_layout.addWidget(unread_label, 0, Qt.AlignRight) # Căn phải
        
        # Thêm các thành phần vào layout chính
        layout.addWidget(avatar_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(right_layout)
        
        # Lưu dữ liệu hội thoại vào widget
        widget.conversation_data = conversation
        
        return widget
    
    def update_messages(self, messages: List[Dict]):
        """Cập nhật tin nhắn vào cache và hiển thị."""
        chat_id = self.get_current_chat_id()
        if not chat_id:
            return

        print(f"Updating messages for chat_id: {chat_id}. Received {len(messages)} messages.")
        
        # Lưu vào cache
        self.message_cache[chat_id] = messages
        
        # Cập nhật số lượng tin nhắn hiển thị
        self.message_count_label.setText(f"{len(messages)} tin nhắn")
        
        # Vẽ lại màn hình chat
        self.refresh_messages_display() 
    
    def refresh_messages_display(self):
        """Làm mới hiển thị tin nhắn từ cache."""
        self.clear_chat_display()
        
        chat_id = self.get_current_chat_id()
        messages_to_show = self.message_cache.get(chat_id, [])
        
        print(f"Refreshing display for chat_id: {chat_id}. Found {len(messages_to_show)} messages in cache.")
        
        # Thêm các bubble mới
        for message in messages_to_show:
            self.add_message_bubble(message)
        
        # Cuộn xuống dưới cùng sau khi thêm tin nhắn
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def add_message_bubble(self, message_data):
        """Thêm bubble tin nhắn vào layout."""
        if not message_data or not message_data.get('sender'):
            print("Warning: Invalid message_data passed to add_message_bubble")
            return

        current_user_id = self.user_data['user']['id']
        is_own_message = message_data['sender']['id'] == current_user_id
        
        bubble = ChatBubble(message_data, is_own_message)
        
        # Chèn bubble vào vị trí ngay trước "cục đẩy" (spacer)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
    # <<<<<<<<<<<<<<<<<<<<<<<<<<< KẾT THÚC THAY THẾ >>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    # <<<<<<<<<<<<<<<<<<< SỬA LẠI HÀM add_new_message >>>>>>>>>>>>>>>>>>>>
    def add_new_message(self, message_data):
        """Thêm tin nhắn mới, xử lý đúng cho cả chat riêng và chat nhóm."""
        if not message_data:
            return

        client_msg_id = message_data.get('client_message_id')
        current_user_id = self.user_data['user']['id']
        sender_id = message_data['sender']['id']

        # --- SỬA LỖI LOGIC Ở ĐÂY ---
        chat_id = None
        group_id = message_data.get('group_id')

        if group_id:
            # Đây là tin nhắn nhóm
            chat_id = f"group_{group_id}"
        elif message_data.get('receiver'):
            # Đây là tin nhắn riêng
            # Nếu mình là người gửi, chat_id là của người nhận
            # Nếu mình là người nhận, chat_id là của người gửi
            if sender_id == current_user_id:
                chat_id = message_data['receiver']['username']
            else:
                chat_id = message_data['sender']['username']
        
        if not chat_id:
            print(f"Cảnh báo: Không thể xác định chat_id cho tin nhắn: {message_data}")
            return

        # Logic chống trùng lặp và cập nhật cho tin nhắn mình gửi
        if client_msg_id and sender_id == current_user_id:
            if chat_id in self.message_cache:
                for i, msg in enumerate(self.message_cache[chat_id]):
                    if msg.get('client_message_id') == client_msg_id:
                        # Thay thế tin nhắn "nháp" bằng tin nhắn thật từ server
                        self.message_cache[chat_id][i] = message_data
                        # Vẽ lại toàn bộ cửa sổ chat để cập nhật ID và timestamp
                        self.refresh_messages_display()
                        return 
        
        # Thêm tin nhắn mới vào cache
        if chat_id not in self.message_cache:
            self.message_cache[chat_id] = []
        self.message_cache[chat_id].append(message_data)

        # Nếu đang xem đúng cuộc trò chuyện này thì mới vẽ ra màn hình
        if chat_id == self.get_current_chat_id():
            self.add_message_bubble(message_data)
            self.scroll_to_bottom()
            # Nếu là chat riêng, đánh dấu đã đọc
            if not group_id:
                self.client.mark_messages_read(message_data['sender']['username'])
        
        # Luôn làm mới danh sách hội thoại để cập nhật tin nhắn cuối và thứ tự
        self.client.get_conversations()

    
    
    def update_user_status_display(self, user_data):
        """Cập nhật hiển thị trạng thái user và làm mới danh bạ."""
        if not user_data:
            return

        print(f"Updating UI for user '{user_data['username']}' with status '{user_data['status']}'")
        
        # <<<<<<<<<<<<<<<<<<< THAY ĐỔI LOGIC Ở ĐÂY >>>>>>>>>>>>>>>>>>>>
        # Cách đơn giản và hiệu quả nhất: khi có bất kỳ thay đổi trạng thái nào,
        # hãy yêu cầu server cung cấp lại danh sách liên hệ mới nhất.
        # Điều này đảm bảo cả trạng thái (online/offline) và danh sách người dùng
        # (nếu có người mới đăng ký) đều được cập nhật.
        self.client.get_contacts()
        self.client.get_conversations() # Cũng nên cập nhật hội thoại

        # Cập nhật trạng thái của cuộc trò chuyện hiện tại nếu có
        if self.current_chat_type == "private" and self.current_chat_user and self.current_chat_user['id'] == user_data['id']:
            self.current_chat_user = user_data # Cập nhật dữ liệu mới nhất
            if user_data.get('is_online', False):
                self.chat_status.setText("🟢 Online")
                self.chat_status.setStyleSheet("color: #28a745;")
            else:
                self.chat_status.setText("🔴 Offline")
                self.chat_status.setStyleSheet("color: #dc3545;")
        
        self.status_bar.showMessage(f"Người dùng {user_data['display_name']} đã {user_data['status']}.", 3000)

    
    def update_typing_status(self, user_data, is_typing):
        """Cập nhật trạng thái đang gõ"""
        if not user_data:
            return
        
        # Check if typing status is for current chat
        should_show = False
        
        if self.current_chat_type == "group":
            should_show = True
        elif self.current_chat_type == "private" and self.current_chat_user:
            should_show = user_data['id'] == self.current_chat_user['id']
        
        if should_show:
            if is_typing:
                self.typing_indicator.setText(f"{user_data['display_name']} đang gõ...")
                self.typing_indicator.setVisible(True)
            else:
                self.typing_indicator.setVisible(False)
    
    def remove_message(self, message_id):
        """Xóa tin nhắn"""
        # Remove from messages list
        self.messages = [msg for msg in self.messages if msg['id'] != message_id]
        
        # Refresh display
        self.refresh_messages_display()
    
    def scroll_to_bottom(self):
        """Cuộn xuống cuối"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def start_private_chat(self, user_data):
        """Bắt đầu chat riêng và LUÔN LUÔN tải lịch sử chat."""
        print(f"Starting private chat with: {user_data['username']}")
        self.clear_chat_display()
        self.current_chat_type = "private"
        self.current_chat_user = user_data
        self.current_group_id = None # Reset group_id khi chat riêng
        self.info_sidebar_btn.setChecked(False)
        
        self.chat_title.setText(f"💬 {user_data['display_name']}")
        
        if user_data.get('is_online', False):
            self.chat_status.setText("🟢 Online")
            self.chat_status.setStyleSheet("color: #28a745;")
        else:
            self.chat_status.setText("🔴 Offline")
            self.chat_status.setStyleSheet("color: #dc3545;")
        
        # Kích hoạt các nút nhập liệu
        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(bool(self.message_input.toPlainText().strip()))
        self.file_btn.setEnabled(True)
        
        # --- LOGIC QUAN TRỌNG ---
        # Xóa cache cũ (nếu có) và luôn yêu cầu server cung cấp lịch sử mới nhất.
        # Điều này đảm bảo dữ liệu luôn được làm mới khi mở lại cuộc trò chuyện.
        chat_id = self.get_current_chat_id()
        if chat_id in self.message_cache:
            del self.message_cache[chat_id]
        
        print(f"Requesting message history for user: {user_data['username']}")
        self.client.get_messages(other_user=user_data['username'])

        # Đánh dấu các tin nhắn là đã đọc
        self.client.mark_messages_read(user_data['username'])

    # >>> THAY THẾ HÀM NÀY <<<
    def start_group_chat(self, group_id, group_name):
        """Bắt đầu chat nhóm và LUÔN LUÔN tải lịch sử chat."""
        print(f"Starting group chat for group: {group_name} (ID: {group_id})")
        self.clear_chat_display()
        self.current_chat_type = "group"
        self.current_chat_user = None
        self.current_group_id = group_id

        self.chat_title.setText(f"💬 {group_name}")
        self.chat_status.setText("Nhóm chat")
        self.chat_status.setStyleSheet("color: #666;")
        self.info_sidebar_btn.setChecked(False)

        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(bool(self.message_input.toPlainText().strip()))
        self.file_btn.setEnabled(True)

        # Xóa cache cũ và yêu cầu lịch sử mới từ server
        chat_id = self.get_current_chat_id()
        if chat_id in self.message_cache:
            del self.message_cache[chat_id]

        print(f"Requesting message history for group ID: {group_id}")
        self.client.get_messages(group_id=group_id)


    
    def start_private_chat(self, user_data):
        """Bắt đầu chat riêng"""
        self.clear_chat_display()
        self.current_chat_type = "private"
        self.current_chat_user = user_data
        self.current_group_id = None # Reset group_id khi chat riêng
        self.info_sidebar_btn.setChecked(False)
        
        self.chat_title.setText(f"💬 {user_data['display_name']}")
        
        if user_data.get('is_online', False):
            self.chat_status.setText("🟢 Online")
            self.chat_status.setStyleSheet("color: #28a745;")
        else:
            self.chat_status.setText("🔴 Offline")
            self.chat_status.setStyleSheet("color: #dc3545;")
        
        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(bool(self.message_input.toPlainText().strip()))
        self.file_btn.setEnabled(True)
        
        # Logic tải tin nhắn từ cache hoặc server
        chat_id = self.get_current_chat_id()
        if chat_id in self.message_cache:
            self.refresh_messages_display()
        else:
            # SỬA LỜI GỌI HÀM Ở ĐÂY
            self.client.get_messages(other_user=user_data['username'])

        self.client.mark_messages_read(user_data['username'])
    
    def on_conversation_selected(self, item):
        """Xử lý khi chọn một mục trong danh sách hội thoại."""
        widget = self.conversations_list.itemWidget(item)
        if not widget or not hasattr(widget, 'conversation_data'):
            return

        conversation = widget.conversation_data
        conv_type = conversation.get('type')

        if conv_type == 'private':
            other_user = conversation['other_user']
            self.start_private_chat(other_user)
        elif conv_type == 'group':
            group_id = conversation['group_id']
            group_name = conversation['group_name']
            self.start_group_chat(group_id, group_name)
    
    def on_contact_selected(self, item):
        """Xử lý khi chọn contact"""
        widget = self.contacts_list.itemWidget(item)
        if widget and hasattr(widget, 'contact_data'):
            contact = widget.contact_data
            self.start_private_chat(contact)
    
    def filter_contacts(self):
        """Lọc danh sách liên hệ"""
        self.refresh_contacts_list()
    
    def on_message_input_changed(self):
        """Xử lý khi nội dung input thay đổi"""
        has_text = bool(self.message_input.toPlainText().strip())
        self.send_btn.setEnabled(has_text)
        
        # Handle typing status
        if has_text:
            if self.current_chat_type == "group":
                self.client.start_typing(is_group=True)
            elif self.current_chat_user:
                self.client.start_typing(other_user=self.current_chat_user['username'], is_group=False)
            
            # Reset typing timer
            self.typing_timer.start(3000)  # Stop typing after 3 seconds of inactivity
        else:
            self.stop_typing()
    
    def stop_typing(self):
        """Dừng trạng thái đang gõ"""
        if self.current_chat_type == "group":
            self.client.stop_typing(is_group=True)
        elif self.current_chat_user:
            self.client.stop_typing(other_user=self.current_chat_user['username'], is_group=False)
    
    # <<<<<<<<<<<<<<<<<<< THAY THẾ TOÀN BỘ HÀM NÀY >>>>>>>>>>>>>>>>>>>>
    def send_message(self):
        """Gửi tin nhắn và thực hiện Optimistic UI Update."""
        message_text = self.message_input.toPlainText().strip()
        if not message_text:
            return
        
        self.stop_typing()

        import time
        import random
        client_msg_id = f"client_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        # Gửi tin nhắn đi qua socket
        if self.current_chat_type == "group":
            # Gửi kèm group_id
            self.client.send_group_message(self.current_group_id, message_text, client_message_id=client_msg_id)
        elif self.current_chat_user:
            self.client.send_private_message(self.current_chat_user['username'], message_text, client_message_id=client_msg_id)
        
        # Tạo "bản nháp" tin nhắn để hiển thị ngay
        temp_message_data = {
            "client_message_id": client_msg_id,
            "id": -1,
            "sender": self.user_data['user'],
            "receiver": self.current_chat_user if self.current_chat_type == 'private' else None,
            "group_id": self.current_group_id if self.current_chat_type == 'group' else None,
            "content": message_text,
            "message_type": "text",
            "timestamp": datetime.now().isoformat(),
        }
        
        chat_id = self.get_current_chat_id()
        if chat_id:
            if chat_id not in self.message_cache:
                self.message_cache[chat_id] = []
            self.message_cache[chat_id].append(temp_message_data)
            self.add_message_bubble(temp_message_data)
            self.scroll_to_bottom()

        self.message_input.clear()
        self.send_btn.setEnabled(False)
    def show_welcome_screen(self):
        """Hiển thị màn hình chào mừng khi không có hội thoại nào."""
        self.clear_chat_display()
        self.chat_title.setText(f"Chào mừng, {self.user_data['user']['display_name']}!")
        self.chat_status.setText("Hãy bắt đầu một cuộc trò chuyện.")
        self.message_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.file_btn.setEnabled(False) 
    def upload_file(self):
        """Upload file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file để gửi",
            "",
            "All Files (*)"
        )
        
        if file_path:
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:
                    QMessageBox.warning(self, "Cảnh báo", "File quá lớn! Kích thước tối đa là 10MB.")
                    return
                
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                file_name = os.path.basename(file_path)
                
                # SỬA LỜI GỌI HÀM Ở ĐÂY
                if self.current_chat_type == "group":
                    self.client.upload_file(file_data, file_name, group_id=self.current_group_id)
                elif self.current_chat_user:
                    self.client.upload_file(file_data, file_name, receiver=self.current_chat_user['username'])
                
                self.status_bar.showMessage(f"Đang gửi file: {file_name}", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể đọc file: {str(e)}")
    
    def show_emoji_picker(self):
        """Hiển thị emoji picker"""
        emoji_picker = EmojiPicker(self)
        emoji_picker.emoji_selected.connect(self.insert_emoji)
        emoji_picker.exec_()
    
    def insert_emoji(self, emoji_char):
        """Chèn emoji vào input"""
        cursor = self.message_input.textCursor()
        cursor.insertText(emoji_char)
        self.message_input.setFocus()
    
    def update_user_status(self, status_text):
        """Cập nhật trạng thái user"""
        status_map = {
            "🟢 Online": "online",
            "🟡 Away": "away",
            "🔴 Busy": "busy"
        }
        
        status = status_map.get(status_text, "online")
        self.client.update_status(status)
    
    # Sửa lại hàm show_search_dialog để chỉ gửi yêu cầu
    def show_search_dialog(self):
        """Hiển thị dialog tìm kiếm và gửi yêu cầu đến server."""
        # Chỉ cho phép tìm kiếm khi đang trong một cuộc trò chuyện
        if not self.current_chat_user and self.current_chat_type != "group":
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn một cuộc trò chuyện để tìm kiếm.")
            return

        search_text, ok = QInputDialog.getText(
            self, 
            "Tìm kiếm tin nhắn", 
            "Nhập từ khóa tìm kiếm:"
        )
        
        if ok and search_text.strip():
            # Gửi yêu cầu tìm kiếm đến server
            self.client.search_messages(search_text.strip())
            self.status_bar.showMessage(f"Đang tìm kiếm '{search_text.strip()}'...", 2000)
    
    def clear_current_chat(self):
        """Xóa lịch sử chat hiện tại"""
        if self.current_chat_type == "private" and self.current_chat_user:
            reply = QMessageBox.question(
                self,
                "Xác nhận",
                f"Bạn có chắc muốn xóa toàn bộ lịch sử chat với {self.current_chat_user['display_name']}?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.client.clear_chat(self.current_chat_user['username'])
                self.messages.clear()
                self.refresh_messages_display()
                self.status_bar.showMessage("Đã xóa lịch sử chat", 3000)
        else:
            QMessageBox.information(self, "Thông báo", "Không thể xóa lịch sử chat nhóm.")
    
    def show_settings(self):
        """Hiển thị cài đặt"""
        QMessageBox.information(self, "Cài đặt", "Tính năng cài đặt sẽ được phát triển trong phiên bản tiếp theo.")
    
    # >>> THAY THẾ HÀM export_chat <<<
    def export_chat(self):
        """Lấy tin nhắn từ cache và xuất ra file .txt."""
        chat_id = self.get_current_chat_id()
        
        if not chat_id or chat_id not in self.message_cache:
            QMessageBox.warning(self, "Không thể xuất", "Không có tin nhắn trong cuộc trò chuyện này để xuất.")
            return
            
        messages_to_export = self.message_cache[chat_id]
        
        if not messages_to_export:
            QMessageBox.warning(self, "Không thể xuất", "Cuộc trò chuyện này không có tin nhắn.")
            return

        # Lấy tên cuộc trò chuyện để đặt tên file
        chat_name = "group_chat"
        if self.current_chat_type == "private" and self.current_chat_user:
            chat_name = self.current_chat_user['username']
        
        default_filename = f"chat_history_{chat_name}_{datetime.now().strftime('%Y%m%d')}.txt"

        # Mở hộp thoại lưu file
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Lưu lịch sử chat", 
            default_filename,
            "Text Files (*.txt);;All Files (*)"
        )
        
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    # Ghi thông tin header
                    f.write(f"Lịch sử trò chuyện - {self.chat_title.text()}\n")
                    f.write(f"Ngày xuất: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*50 + "\n\n")
                    
                    # Ghi từng tin nhắn
                    for message in messages_to_export:
                        sender_name = message['sender']['display_name']
                        timestamp_str = self.format_timestamp(message['timestamp'])
                        content = message['content']
                        
                        f.write(f"[{timestamp_str}] {sender_name}:\n")
                        f.write(f"{content}\n\n")
                
                QMessageBox.information(self, "Thành công", f"Lịch sử chat đã được lưu tại:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {str(e)}")
    
    # >>> THAY THẾ HÀM logout <<<
    def logout(self):
        """Xử lý đăng xuất: phát tín hiệu để trình quản lý xử lý."""
        reply = QMessageBox.question(
            self,
            "Xác nhận đăng xuất",
            "Bạn có chắc muốn đăng xuất khỏi tài khoản này?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print("Người dùng xác nhận đăng xuất. Phát tín hiệu logged_out.")
            # Ngắt kết nối khỏi server
            if self.client.is_connected():
                self.client.disconnect()
            
            # Phát tín hiệu để simple_main.py xử lý việc chuyển cửa sổ
            self.logged_out.emit()
            
            # Đóng cửa sổ này lại
            self.close()
    
    def show_about(self):
        """Hiển thị thông tin về ứng dụng"""
        QMessageBox.about(
            self,
            "Về Chat LAN v3.0",
            """
            <h3>Chat LAN Enterprise v3.0</h3>
            <p><b>Hệ thống chat nội bộ doanh nghiệp</b></p>
            
            <p><b>Tính năng chính:</b></p>
            <ul>
            <li>✅ Đăng nhập/Đăng ký với mã hóa mật khẩu</li>
            <li>✅ Chat nhóm và chat riêng tư</li>
            <li>✅ Gửi file và hình ảnh</li>
            <li>✅ Emoji picker</li>
            <li>✅ Trạng thái đang gõ</li>
            <li>✅ Tìm kiếm tin nhắn</li>
            <li>✅ Export lịch sử chat</li>
            <li>✅ Auto-reconnect</li>
            <li>✅ Giao diện hiện đại như Zalo</li>
            </ul>
            
            <p><b>Công nghệ:</b> Python, PyQt5, Socket, SQLite</p>
            <p><b>Phiên bản:</b> 3.0.0</p>
            """
        )
    
    def eventFilter(self, obj, event):
        """Event filter cho message input"""
        if obj == self.message_input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                # Enter without Shift = send message
                self.send_message()
                return True
            elif event.key() == Qt.Key_Return and event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter = new line
                return False
        
        return super().eventFilter(obj, event)
    
    # >>> THAY THẾ HÀM closeEvent <<<
    def closeEvent(self, event):
        """Xử lý khi người dùng đóng cửa sổ bằng nút X."""
        # Khi đóng bằng nút X, coi như là thoát hoàn toàn ứng dụng
        reply = QMessageBox.question(
            self,
            "Xác nhận thoát",
            "Bạn có chắc muốn thoát ứng dụng?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            print("Người dùng xác nhận thoát ứng dụng.")
            if self.client.is_connected():
                self.client.disconnect()
            # Thoát hoàn toàn ứng dụng
            QApplication.instance().quit()
            event.accept()
        else:
            event.ignore()