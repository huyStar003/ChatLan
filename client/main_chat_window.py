import sys
import os
import subprocess
import time
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import base64
import mimetypes

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QSplitter, QFrame, QLabel, QPushButton, QLineEdit,
                            QTextEdit, QListWidget, QListWidgetItem, QMenuBar,
                            QMenu, QAction, QStatusBar, QMessageBox, QFileDialog,
                            QProgressBar, QComboBox, QCheckBox, QTabWidget,
                            QScrollArea, QGroupBox, QDialog, QDialogButtonBox,
                            QTextBrowser, QApplication, QInputDialog, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot, QThread, QSize
from PyQt5.QtGui import (QFont, QPixmap, QPainter, QColor, QBrush, QIcon, 
                        QTextCursor, QTextCharFormat, QKeySequence, QCursor, QFontMetrics)

from .socket_client import SocketClient
from .ui.widgets import ChatBubble
from .ui.dialogs import (
    CreateGroupDialog, MediaViewerDialog, SearchResultDialog,
    UserProfileDialog, EmojiPicker
)
from .ui.components import Sidebar, ChatArea, InfoSidebar
from .core.models import Message, User, Conversation
from .core.managers import MessageManager, ConversationManager
from .utils import resource_path
import client.resources_rc


class MainChatWindow(QMainWindow):
    # >>> THÊM TÍN HIỆU NÀY VÀO ĐẦU LỚP <<<
    logged_out = pyqtSignal()
    
    def __init__(self, client: SocketClient, user_data: dict):
        super().__init__()
        
        # Validate user_data
        if not user_data or 'user' not in user_data:
            raise ValueError("user_data phải chứa key 'user'")
        if 'id' not in user_data['user']:
            raise ValueError("user_data['user'] phải chứa key 'id'")
        
        self.client = client
        self.user_data = user_data
        self.current_chat_user = None
        self.current_chat_type = None   # "group" or "private"
        self.current_group_id = None     # Initialize group_id
        
        # Initialize managers
        try:
            self.message_manager = MessageManager(self.user_data['user']['id'])
            self.conversation_manager = ConversationManager(self.user_data['user']['id'])
        except Exception as e:
            raise ValueError(f"Không thể khởi tạo managers: {str(e)}")
        
        # Keep for backward compatibility during migration
        self.message_cache = {}  # Will be replaced by MessageManager
        self.conversations = []  # Will be replaced by ConversationManager
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
    
    def _safe_get_widget(self, component_name, widget_name, default=None):
        """
        Helper method để truy cập an toàn widget từ component.
        
        Args:
            component_name: Tên component ('sidebar', 'chat_area', 'info_sidebar')
            widget_name: Tên widget cần lấy
            default: Giá trị mặc định nếu không tìm thấy
            
        Returns:
            Widget hoặc default value
        """
        component = getattr(self, component_name, None)
        if component and hasattr(component, widget_name):
            return getattr(component, widget_name)
        return default
    

    # Thêm 2 hàm này vào trong lớp MainChatWindow

    def show_contact_context_menu(self, position):
        """Hiển thị menu chuột phải cho danh sách liên hệ."""
        item = self.sidebar.contacts_list.itemAt(position)
        if not item:
            return
        
        widget = self.sidebar.contacts_list.itemWidget(item)
        if not hasattr(widget, 'contact_data'):
            return
            
        user_data = widget.contact_data
        
        menu = QMenu()
        view_profile_action = QAction(QIcon(resource_path('icons/info.png')), "Xem thông tin", self)
        view_profile_action.triggered.connect(lambda: self.show_user_profile(user_data))
        menu.addAction(view_profile_action)
        
        menu.exec_(self.sidebar.contacts_list.mapToGlobal(position))

    def show_conversation_context_menu(self, position):
        """Hiển thị menu chuột phải cho danh sách hội thoại."""
        item = self.sidebar.conversations_list.itemAt(position)
        if not item:
            return
            
        widget = self.sidebar.conversations_list.itemWidget(item)
        # Bỏ qua nếu là item chat nhóm
        if not hasattr(widget, 'conversation_data'):
            return
            
        user_data = widget.conversation_data['other_user']
        
        menu = QMenu()
        view_profile_action = QAction(QIcon(resource_path('icons/info.png')), "Xem thông tin", self)
        view_profile_action.triggered.connect(lambda: self.show_user_profile(user_data))
        menu.addAction(view_profile_action)
        
        menu.exec_(self.sidebar.conversations_list.mapToGlobal(position))


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
        self.chat_area.clear_messages()


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
        display_name = self.user_data.get('user', {}).get('display_name', 'User')
        self.setWindowTitle(f"Chat LAN - {display_name}")
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
        
        # Phần 1: Sidebar trái (danh bạ, hội thoại) - Sử dụng Component mới
        self.sidebar = Sidebar(self)
        # Connect signals
        self.sidebar.conversation_selected.connect(self.on_conversation_selected)
        self.sidebar.contact_selected.connect(self.on_contact_selected)
        self.sidebar.create_group_clicked.connect(self.show_create_group_dialog)
        self.sidebar.refresh_clicked.connect(self.refresh_data)
        self.sidebar.status_changed.connect(self.update_user_status)
        self.sidebar.set_settings_clicked_handler(
            lambda: self.show_user_profile(self.user_data['user'])
        )
        self.sidebar.set_conversation_context_menu_handler(
            self.show_conversation_context_menu
        )
        self.sidebar.set_contact_context_menu_handler(
            self.show_contact_context_menu
        )
        self.sidebar.set_contact_search_handler(self.filter_contacts)
        # Set user info
        self.sidebar.set_user_info(self.user_data['user'])
        # Set avatar
        avatar_pixmap = self.create_user_avatar_pixmap(self.user_data['user'])
        if avatar_pixmap:
            self.sidebar.set_user_avatar(avatar_pixmap)
        self.main_splitter.addWidget(self.sidebar)
        
        # Phần 2: Khu vực chat chính - Sử dụng Component mới
        self.chat_area = ChatArea(self)
        # Connect signals
        self.chat_area.message_sent.connect(self.send_message)
        self.chat_area.file_upload_clicked.connect(self.upload_file)
        self.chat_area.emoji_clicked.connect(self.show_emoji_picker)
        self.chat_area.search_clicked.connect(self.show_search_dialog)
        self.chat_area.clear_chat_clicked.connect(self.clear_current_chat)
        self.chat_area.info_sidebar_toggled.connect(self.toggle_info_sidebar)
        # Set input handlers
        self.chat_area.set_message_input_handler(self.on_message_input_changed)
        self.chat_area.set_message_input_event_filter(self)
        self.main_splitter.addWidget(self.chat_area)
        
        # Phần 3: Sidebar phải (thông tin hội thoại) - Sử dụng Component mới
        self.info_sidebar = InfoSidebar(self)
        # Connect signals
        self.info_sidebar.add_member_clicked.connect(self.show_add_member_dialog)
        self.info_sidebar.remove_member_clicked.connect(self.remove_member)
        self.info_sidebar.media_viewer_requested.connect(self.show_media_viewer)
        self.info_sidebar.setVisible(False)  # Ẩn đi lúc đầu
        self.main_splitter.addWidget(self.info_sidebar)

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

    # create_info_sidebar() đã được thay thế bằng InfoSidebar component trong init_ui()

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
        self.info_sidebar.clear_content()

        # Nếu là chat nhóm, gửi yêu cầu lấy danh sách thành viên.
        # Server sẽ trả về gói tin 'group_members_list', và on_message_received sẽ xử lý nó.
        if self.current_chat_type == "group" and self.current_group_id:
            self.info_sidebar.add_loading_indicator("Đang tải thông tin nhóm...")
            self.client.get_group_members(self.current_group_id)
        
        # Nếu là chat riêng, hiển thị thông tin ngay lập tức
        elif self.current_chat_type == "private" and self.current_chat_user:
            self._build_sidebar_ui_from_data({}) # Xây dựng UI với dữ liệu rỗng trước
    
    def _build_sidebar_ui_from_data(self, data):
        """
        Xây dựng toàn bộ giao diện cho sidebar thông tin từ dữ liệu được cung cấp.
        """
        # Xóa nội dung cũ
        self.info_sidebar.clear_content()
        layout = self.info_sidebar.info_sidebar_layout

        # Lấy dữ liệu
        is_group = self.current_chat_type == "group"
        chat_title_text = self.chat_area.chat_title.text() if hasattr(self.chat_area, 'chat_title') else ""
        header_data = {'display_name': chat_title_text.replace("💬 ", "")} if is_group else self.current_chat_user
        
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

        # 3. KHU VỰC MEDIA - Sử dụng MessageManager
        group_id = self.current_group_id if self.current_chat_type == "group" else None
        other_user_id = self.current_chat_user['id'] if self.current_chat_type == "private" and self.current_chat_user else None
        messages = self.message_manager.get_messages(group_id=group_id, other_user_id=other_user_id)
        
        # Convert Message objects to dict for compatibility
        messages_dict = [m.to_dict() if hasattr(m, 'to_dict') else m.__dict__ for m in messages]
        
        media_messages = [m for m in messages_dict if m.get('message_type') == 'image']
        if media_messages:
            self._add_media_section("Ảnh/Video", media_messages, 'image', scroll_layout)

        file_messages = [m for m in messages_dict if m.get('message_type') == 'file']
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
        # Ensure member_data is a dict
        if not isinstance(member_data, dict):
            if hasattr(member_data, 'to_dict'):
                member_data = member_data.to_dict()
            elif hasattr(member_data, '__dict__'):
                member_data = member_data.__dict__
        
        name_label = QLabel(member_data.get('display_name', 'Unknown') if isinstance(member_data, dict) else 'Unknown')
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        info_layout.addWidget(name_label)

        member_id = member_data.get('id') if isinstance(member_data, dict) else getattr(member_data, 'id', None)
        if member_id == creator_id:
            role_label = QLabel("Nhóm trưởng")
            role_label.setFont(QFont("Arial", 8, QFont.StyleItalic))
            role_label.setStyleSheet("color: #e67e22;")
            info_layout.addWidget(role_label)

        layout.addWidget(avatar_label)
        layout.addLayout(info_layout)
        layout.addStretch()

        # Nút Xóa (chỉ nhóm trưởng thấy và không thể xóa chính mình)
        if is_current_user_creator and member_id != creator_id and self.current_group_id != 1:
            remove_btn = QPushButton(QIcon(resource_path('icons/user-minus.png')), "")
            remove_btn.setFixedSize(28, 28)
            remove_btn.setIconSize(QSize(16, 16)) # Chỉnh kích thước icon cho phù hợp
            display_name = member_data.get('display_name', 'Unknown') if isinstance(member_data, dict) else 'Unknown'
            remove_btn.setToolTip(f"Xóa {display_name} khỏi nhóm")
            remove_btn.clicked.connect(lambda: self.remove_member(member_id))
            
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
        # Convert contacts to dicts for easier access
        contacts_list = []
        for c in self.contacts:
            if isinstance(c, dict):
                contacts_list.append(c)
            elif hasattr(c, 'to_dict'):
                contacts_list.append(c.to_dict())
            elif hasattr(c, '__dict__'):
                contacts_list.append(c.__dict__)
        
        items = [f"{c.get('display_name', 'Unknown')} (@{c.get('username', 'unknown')})" for c in contacts_list]
        if not items:
            QMessageBox.information(self, "Thông báo", "Không có người dùng nào khác để thêm.")
            return

        item, ok = QInputDialog.getItem(self, "Thêm thành viên", "Chọn người dùng để thêm vào nhóm:", items, 0, False)
        
        if ok and item:
            # Tìm lại user_id từ item đã chọn
            try:
                selected_username = item.split('@')[1][:-1]
                selected_user = next((c for c in contacts_list if c.get('username') == selected_username), None)
                if selected_user:
                    user_id = selected_user.get('id')
                    if user_id:
                        self.client.add_group_member(self.current_group_id, user_id)
            except (IndexError, AttributeError) as e:
                print(f"Error parsing selected user: {e}")

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

        name_label = QLabel(target_data.get('display_name', 'Unknown') if isinstance(target_data, dict) else getattr(target_data, 'display_name', 'Unknown'))
        name_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        layout.addWidget(avatar_label)
        layout.addWidget(name_label)
        self.info_sidebar.info_sidebar_layout.addWidget(header_widget)

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

            
        self.info_sidebar.info_sidebar_layout.addWidget(actions_widget)


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
        
        # refresh_btn nằm trong sidebar
        if hasattr(self, 'sidebar') and self.sidebar and hasattr(self.sidebar, 'refresh_btn'):
            self.sidebar.refresh_btn.setStyleSheet("""
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
        
        if hasattr(self, 'chat_area') and self.chat_area:
            if hasattr(self.chat_area, 'file_btn'):
                self.chat_area.file_btn.setStyleSheet(icon_button_style)
            if hasattr(self.chat_area, 'emoji_btn'):
                self.chat_area.emoji_btn.setStyleSheet(icon_button_style)
        # search_btn và clear_chat_btn nằm trong chat_area
        if hasattr(self, 'chat_area') and self.chat_area:
            if hasattr(self.chat_area, 'search_btn'):
                self.chat_area.search_btn.setStyleSheet(icon_button_style)
            if hasattr(self.chat_area, 'clear_chat_btn'):
                self.chat_area.clear_chat_btn.setStyleSheet(icon_button_style)
        # settings_btn nằm trong sidebar
        if hasattr(self, 'sidebar') and self.sidebar and hasattr(self.sidebar, 'settings_btn'):
            self.sidebar.settings_btn.setStyleSheet(icon_button_style)
        
        # Chat header style - nằm trong chat_area
        if hasattr(self, 'chat_area') and self.chat_area and hasattr(self.chat_area, 'chat_header'):
            self.chat_area.chat_header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e1e5e9;
            }
        """)
    
    def create_user_avatar_pixmap(self, user_data, size=50):
        """Tạo avatar pixmap từ user_data"""
        avatar_data = user_data.get('avatar')
        if avatar_data:
            try:
                image_data = base64.b64decode(avatar_data)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                return self.create_circular_avatar(pixmap, size)
            except:
                return self.create_default_avatar_pixmap(user_data, size)
        else:
            return self.create_default_avatar_pixmap(user_data, size)
    
    def create_default_avatar_pixmap(self, user_data, size):
        """Tạo avatar mặc định"""
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor("#e0e0e0"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("#333"))
        painter.setFont(QFont("Arial", size // 2, QFont.Bold))
        display_name = user_data.get('display_name', 'A')
        painter.drawText(pixmap.rect(), Qt.AlignCenter, display_name[0].upper())
        painter.end()
        return self.create_circular_avatar(pixmap, size)
    
    def set_user_avatar(self):
        """Đặt avatar user"""
        avatar_pixmap = self.create_user_avatar_pixmap(self.user_data['user'])
        if avatar_pixmap and hasattr(self, 'user_avatar'):
            self.user_avatar.setPixmap(avatar_pixmap)
    
    def set_default_avatar(self):
        """Đặt avatar mặc định"""
        pixmap = QPixmap(50, 50)
        pixmap.fill(QColor("#0084ff"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        
        # Draw first letter of display name
        display_name = self.user_data.get('user', {}).get('display_name', 'User')
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
                print(f"DEBUG: Received new_message from server: {message.get('message')}")
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
                # Remove from ConversationManager
                conversations = self.conversation_manager.get_conversations()
                self.conversation_manager.conversations = [
                    c for c in conversations 
                    if not (c.is_group and c.group_id == group_id)
                ]
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
                    # Ensure it's a dict
                    if not isinstance(new_conversation, dict):
                        if hasattr(new_conversation, 'to_dict'):
                            new_conversation = new_conversation.to_dict()
                        elif hasattr(new_conversation, '__dict__'):
                            new_conversation = new_conversation.__dict__
                    
                    group_name = new_conversation.get('group_name', 'Nhóm mới') if isinstance(new_conversation, dict) else 'Nhóm mới'
                    QMessageBox.information(self, "Thông báo", f"Bạn đã được thêm vào nhóm '{group_name}'")
                    # Thêm hội thoại mới vào ConversationManager
                    if isinstance(new_conversation, dict):
                        self.conversation_manager.add_or_update_conversation(new_conversation)
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
        if hasattr(self, 'chat_area') and self.chat_area:
            if hasattr(self.chat_area, 'message_input'):
                self.chat_area.message_input.setEnabled(False)
            if hasattr(self.chat_area, 'send_btn'):
                self.chat_area.send_btn.setEnabled(False)
            if hasattr(self.chat_area, 'file_btn'):
                self.chat_area.file_btn.setEnabled(False)
    
    @pyqtSlot(str)
    def on_error_occurred(self, error_message):
        """Xử lý lỗi"""
        self.status_bar.showMessage(f"Lỗi: {error_message}", 5000)
    
    def update_contacts(self, online_users, all_users):
        """Cập nhật danh sách liên hệ"""
        # Update ConversationManager
        contacts = self.conversation_manager.update_contacts(online_users, all_users)
        # Update Sidebar component
        contacts_dict = [c.to_dict() if hasattr(c, 'to_dict') else c.__dict__ for c in contacts]
        self.sidebar.update_contacts(contacts_dict)
    
    def refresh_contacts_list(self):
        """Làm mới danh sách liên hệ"""
        # This is now handled by Sidebar component
        contacts = self.conversation_manager.get_contacts()
        contacts_dict = [c.to_dict() if hasattr(c, 'to_dict') else c.__dict__ for c in contacts]
        self.sidebar.update_contacts(contacts_dict)
    
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

        # Update ConversationManager
        self.conversation_manager.update_conversations(final_conversations)
        self.refresh_conversations_list()
    
    def refresh_conversations_list(self):
        """Làm mới danh sách hội thoại, xử lý cả chat riêng và chat nhóm."""
        self.sidebar.conversations_list.clear()
        
        # Không cần thêm item chat nhóm mặc định nữa vì server đã trả về
        conversations = self.conversation_manager.get_conversations()
        
        for conversation in conversations:
            # Convert Conversation object to dict for compatibility
            if hasattr(conversation, 'to_dict'):
                conv_dict = conversation.to_dict()
            elif isinstance(conversation, dict):
                conv_dict = conversation
            else:
                # Fallback: try to access attributes
                conv_dict = {
                    'type': getattr(conversation, 'type', 'group' if getattr(conversation, 'is_group', False) else 'private'),
                    'group_id': getattr(conversation, 'group_id', None),
                    'group_name': getattr(conversation, 'group_name', None),
                    'other_user': conversation.other_user.to_dict() if hasattr(conversation, 'other_user') and conversation.other_user and hasattr(conversation.other_user, 'to_dict') else (conversation.other_user.__dict__ if hasattr(conversation, 'other_user') and conversation.other_user else None),
                    'last_message': conversation.last_message.to_dict() if hasattr(conversation, 'last_message') and conversation.last_message and hasattr(conversation.last_message, 'to_dict') else (conversation.last_message.__dict__ if hasattr(conversation, 'last_message') and conversation.last_message else None),
                    'updated_at': conversation.updated_at.isoformat() if hasattr(conversation, 'updated_at') and conversation.updated_at else None,
                    'unread_count': getattr(conversation, 'unread_count', 0)
                }
            item = QListWidgetItem()
            conv_widget = None

            # KIỂM TRA LOẠI HỘI THOẠI
            if conv_dict.get('type') == 'private':
                conv_widget = self.create_conversation_widget(conv_dict)
            elif conv_dict.get('type') == 'group':
                conv_widget = self.create_group_conversation_widget(conv_dict)

            if conv_widget:
                item.setSizeHint(conv_widget.sizeHint())
                self.sidebar.conversations_list.addItem(item)
                self.sidebar.conversations_list.setItemWidget(item, conv_widget)

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
        # Ensure last_message is a dict if it exists
        if last_message and not isinstance(last_message, dict):
            if hasattr(last_message, 'to_dict'):
                last_message = last_message.to_dict()
            elif hasattr(last_message, '__dict__'):
                last_message = last_message.__dict__
        
        if last_message and isinstance(last_message, dict) and last_message.get('sender'):
            sender = last_message.get('sender')
            if isinstance(sender, dict):
                sender_name = sender.get('display_name', 'Unknown')
            else:
                sender_name = getattr(sender, 'display_name', 'Unknown')
            content = last_message.get('content', '')
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
        if last_message and isinstance(last_message, dict):
            timestamp = last_message.get('timestamp')
            if timestamp:
                timestamp_label = QLabel(self.format_timestamp_for_list(timestamp))
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
        other_user = conversation.get('other_user')
        if not other_user:
            return None
        
        # Ensure other_user is a dict
        if not isinstance(other_user, dict):
            if hasattr(other_user, 'to_dict'):
                other_user = other_user.to_dict()
            elif hasattr(other_user, '__dict__'):
                other_user = other_user.__dict__
            else:
                return None
        
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
        name_label = QLabel(other_user.get('display_name', 'Unknown'))
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setStyleSheet("color: #333;")
        
        # Tin nhắn cuối cùng
        last_message = conversation.get('last_message')
        # Ensure last_message is a dict if it exists
        if last_message and not isinstance(last_message, dict):
            if hasattr(last_message, 'to_dict'):
                last_message = last_message.to_dict()
            elif hasattr(last_message, '__dict__'):
                last_message = last_message.__dict__
        
        if last_message and isinstance(last_message, dict):
            # Rút gọn tin nhắn cuối nếu quá dài
            last_msg_text = last_message.get('content', '')
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
        if last_message and isinstance(last_message, dict):
            # Format lại timestamp cho gọn gàng
            timestamp = last_message.get('timestamp')
            if timestamp:
                timestamp_label = QLabel(self.format_timestamp_for_list(timestamp))
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
        group_id = self.current_group_id if self.current_chat_type == "group" else None
        other_user_id = self.current_chat_user['id'] if self.current_chat_type == "private" and self.current_chat_user else None
        
        if not group_id and not other_user_id:
            return

        print(f"Updating messages. Received {len(messages)} messages.")
        
        # Lưu vào MessageManager
        self.message_manager.update_messages(messages, group_id=group_id, other_user_id=other_user_id)
        
        # Cập nhật số lượng tin nhắn hiển thị
        self.message_count_label.setText(f"{len(messages)} tin nhắn")
        
        # Vẽ lại màn hình chat
        self.refresh_messages_display() 
    
    def refresh_messages_display(self):
        """Làm mới hiển thị tin nhắn từ cache."""
        self.chat_area.clear_messages()
        
        group_id = self.current_group_id if self.current_chat_type == "group" else None
        other_user_id = self.current_chat_user['id'] if self.current_chat_type == "private" and self.current_chat_user else None
        messages_to_show = self.message_manager.get_messages(group_id=group_id, other_user_id=other_user_id)
        
        print(f"Refreshing display. Found {len(messages_to_show)} messages.")
        
        # Convert Message objects to dict for compatibility
        for message in messages_to_show:
            message_dict = message.to_dict() if hasattr(message, 'to_dict') else message.__dict__
            self.add_message_bubble(message_dict)
        
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
        
        # Chèn bubble vào ChatArea component
        self.chat_area.add_message_widget(bubble)
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
        group_id_for_msg = message_data.get('group_id')
        
        # Xác định other_user_id cho tin nhắn riêng
        # Nếu mình là người gửi: other_user_id là receiver
        # Nếu mình là người nhận: other_user_id là sender
        if not group_id_for_msg:  # Tin nhắn riêng
            if sender_id == current_user_id:
                # Mình là người gửi, other_user_id là người nhận
                receiver_data = message_data.get('receiver')
                other_user_id_for_msg = receiver_data.get('id') if receiver_data else None
            else:
                # Mình là người nhận, other_user_id là người gửi
                other_user_id_for_msg = sender_id
        else:
            other_user_id_for_msg = None
        
        if client_msg_id and sender_id == current_user_id:
            messages = self.message_manager.get_messages(group_id=group_id_for_msg, other_user_id=other_user_id_for_msg)
            for i, msg in enumerate(messages):
                msg_dict = msg.to_dict() if hasattr(msg, 'to_dict') else msg.__dict__
                if msg_dict.get('client_message_id') == client_msg_id:
                    # Update message in manager
                    self.message_manager.update_messages([message_data], group_id=group_id_for_msg, other_user_id=other_user_id_for_msg)
                    # Vẽ lại toàn bộ cửa sổ chat để cập nhật ID và timestamp
                    self.refresh_messages_display()
                    return 
        
        # Thêm tin nhắn mới vào MessageManager
        self.message_manager.add_message(message_data, group_id=group_id_for_msg, other_user_id=other_user_id_for_msg)

        # Nếu đang xem đúng cuộc trò chuyện này thì mới vẽ ra màn hình
        current_group_id = self.current_group_id if self.current_chat_type == "group" else None
        current_other_user_id = None
        if self.current_chat_type == "private" and self.current_chat_user:
            current_other_user_id = self.current_chat_user.get('id')
        
        # Kiểm tra xem tin nhắn có thuộc cuộc trò chuyện hiện tại không
        should_display = False
        if group_id_for_msg:
            # Tin nhắn nhóm: so sánh group_id
            should_display = (group_id_for_msg == current_group_id)
        else:
            # Tin nhắn riêng: so sánh other_user_id
            should_display = (other_user_id_for_msg == current_other_user_id)
        
        if should_display:
            print(f"DEBUG: Displaying message - group_id={group_id_for_msg}, other_user_id={other_user_id_for_msg}, current_group={current_group_id}, current_user={current_other_user_id}")
            self.add_message_bubble(message_data)
            self.scroll_to_bottom()
            # Nếu là chat riêng, đánh dấu đã đọc
            if not group_id_for_msg:
                self.client.mark_messages_read(message_data['sender']['username'])
        else:
            print(f"DEBUG: Not displaying message - group_id={group_id_for_msg}, other_user_id={other_user_id_for_msg}, current_group={current_group_id}, current_user={current_other_user_id}")
        
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
        scrollbar = self.chat_area.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def start_private_chat(self, user_data):
        """Bắt đầu chat riêng và LUÔN LUÔN tải lịch sử chat."""
        # Ensure user_data is a dict
        if not isinstance(user_data, dict):
            if hasattr(user_data, 'to_dict'):
                user_data = user_data.to_dict()
            elif hasattr(user_data, '__dict__'):
                user_data = user_data.__dict__
            else:
                print(f"Error: Invalid user_data type: {type(user_data)}")
                return
        
        username = user_data.get('username', 'Unknown')
        display_name = user_data.get('display_name', 'Unknown')
        print(f"Starting private chat with: {username}")
        self.clear_chat_display()
        self.current_chat_type = "private"
        self.current_chat_user = user_data
        self.current_group_id = None # Reset group_id khi chat riêng
        
        self.chat_area.set_chat_title(f"💬 {display_name}")
        
        if user_data.get('is_online', False):
            self.chat_area.set_chat_status("🟢 Online")
        else:
            self.chat_area.set_chat_status("🔴 Offline")
        
        # Kích hoạt các nút nhập liệu
        self.chat_area.set_send_button_enabled(bool(self.chat_area.get_message_text().strip()))
        
        # --- LOGIC QUAN TRỌNG ---
        # Xóa cache cũ (nếu có) và luôn yêu cầu server cung cấp lịch sử mới nhất.
        # Điều này đảm bảo dữ liệu luôn được làm mới khi mở lại cuộc trò chuyện.
        other_user_id = user_data.get('id')
        if other_user_id:
            self.message_manager.clear_conversation(other_user_id=other_user_id)
        
        print(f"Requesting message history for user: {username}")
        self.client.get_messages(other_user=username)

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

        self.chat_area.set_chat_title(f"💬 {group_name}")
        self.chat_area.set_chat_status("Nhóm chat")
        # Note: info_sidebar_btn is now in ChatArea component, accessed via signal

        self.chat_area.set_send_button_enabled(bool(self.chat_area.get_message_text().strip()))

        # Xóa cache cũ và yêu cầu lịch sử mới từ server
        self.message_manager.clear_conversation(group_id=group_id)

        print(f"Requesting message history for group ID: {group_id}")
        self.client.get_messages(group_id=group_id)


    
    def on_conversation_selected(self, item):
        """Xử lý khi chọn một mục trong danh sách hội thoại."""
        widget = self.sidebar.conversations_list.itemWidget(item)
        if not widget or not hasattr(widget, 'conversation_data'):
            return

        conversation = widget.conversation_data
        
        # Ensure conversation is a dict
        if not isinstance(conversation, dict):
            if hasattr(conversation, 'to_dict'):
                conversation = conversation.to_dict()
            else:
                return
        
        conv_type = conversation.get('type')

        if conv_type == 'private':
            other_user = conversation.get('other_user')
            if other_user:
                # Ensure other_user is a dict
                if not isinstance(other_user, dict):
                    if hasattr(other_user, 'to_dict'):
                        other_user = other_user.to_dict()
                    elif hasattr(other_user, '__dict__'):
                        other_user = other_user.__dict__
                    else:
                        return
                self.start_private_chat(other_user)
        elif conv_type == 'group':
            group_id = conversation.get('group_id')
            group_name = conversation.get('group_name')
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
        has_text = bool(self.chat_area.get_message_text().strip())
        self.chat_area.set_send_button_enabled(has_text)
        
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
        message_text = self.chat_area.get_message_text().strip()
        if not message_text:
            return
        
        # Kiểm tra kết nối đến server
        if not self.client.is_connected():
            QMessageBox.warning(self, "Lỗi", "Không có kết nối đến server. Vui lòng kiểm tra lại kết nối.")
            return
        
        # Kiểm tra đã đăng nhập chưa
        if not self.client.is_logged_in():
            QMessageBox.warning(self, "Lỗi", "Bạn chưa đăng nhập. Vui lòng đăng nhập lại.")
            return
        
        # Kiểm tra có cuộc trò chuyện đang mở không
        if not self.current_chat_type:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một cuộc trò chuyện để gửi tin nhắn.")
            return
        
        self.stop_typing()

        import time
        import random
        client_msg_id = f"client_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        # Gửi tin nhắn đi qua socket
        success = False
        if self.current_chat_type == "group":
            # Kiểm tra group_id hợp lệ
            if self.current_group_id is None:
                QMessageBox.warning(self, "Lỗi", "Không thể xác định nhóm chat. Vui lòng chọn lại nhóm.")
                return
            # Gửi kèm group_id
            success = self.client.send_group_message(self.current_group_id, message_text, client_message_id=client_msg_id)
        elif self.current_chat_type == "private" and self.current_chat_user:
            # Kiểm tra username hợp lệ
            if not self.current_chat_user.get('username'):
                QMessageBox.warning(self, "Lỗi", "Không thể xác định người nhận. Vui lòng chọn lại cuộc trò chuyện.")
                return
            success = self.client.send_private_message(self.current_chat_user['username'], message_text, client_message_id=client_msg_id)
        else:
            QMessageBox.warning(self, "Lỗi", "Không thể xác định đích gửi tin nhắn. Vui lòng chọn lại cuộc trò chuyện.")
            return
        
        if not success:
            QMessageBox.warning(self, "Lỗi", "Không thể gửi tin nhắn. Vui lòng thử lại.")
            return
        
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
        
        # Add optimistic message to manager
        group_id = self.current_group_id if self.current_chat_type == "group" else None
        other_user_id = self.current_chat_user['id'] if self.current_chat_type == "private" and self.current_chat_user else None
        
        if group_id or other_user_id:
            print(f"DEBUG: Adding optimistic message - group_id={group_id}, other_user_id={other_user_id}, client_msg_id={client_msg_id}")
            self.message_manager.add_message(temp_message_data, group_id=group_id, other_user_id=other_user_id)
            self.add_message_bubble(temp_message_data)
            self.scroll_to_bottom()
        else:
            print(f"DEBUG: Cannot add optimistic message - group_id={group_id}, other_user_id={other_user_id}")

        self.chat_area.clear_message_input()
        self.chat_area.set_send_button_enabled(False)
    def show_welcome_screen(self):
        """Hiển thị màn hình chào mừng khi không có hội thoại nào."""
        self.clear_chat_display()
        display_name = self.user_data.get('user', {}).get('display_name', 'User')
        self.chat_area.set_chat_title(f"Chào mừng, {display_name}!")
        self.chat_area.set_chat_status("Hãy bắt đầu một cuộc trò chuyện.")
        self.chat_area.message_input.setEnabled(False)
        self.chat_area.set_send_button_enabled(False)
        self.chat_area.file_btn.setEnabled(False) 
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
        if hasattr(self, 'chat_area') and self.chat_area and hasattr(self.chat_area, 'message_input'):
            cursor = self.chat_area.message_input.textCursor()
            cursor.insertText(emoji_char)
            self.chat_area.message_input.setFocus()
    
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
                other_user_id = self.current_chat_user.get('id')
                if other_user_id:
                    self.message_manager.clear_conversation(other_user_id=other_user_id)
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
        group_id = self.current_group_id if self.current_chat_type == "group" else None
        other_user_id = self.current_chat_user['id'] if self.current_chat_type == "private" and self.current_chat_user else None
        
        if not group_id and not other_user_id:
            QMessageBox.warning(self, "Không thể xuất", "Không có tin nhắn trong cuộc trò chuyện này để xuất.")
            return
            
        messages = self.message_manager.get_messages(group_id=group_id, other_user_id=other_user_id)
        # Convert Message objects to dict
        messages_to_export = [m.to_dict() if hasattr(m, 'to_dict') else m.__dict__ for m in messages]
        
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
        # Kiểm tra xem chat_area đã được khởi tạo chưa
        if hasattr(self, 'chat_area') and self.chat_area and hasattr(self.chat_area, 'message_input'):
            if obj == self.chat_area.message_input and event.type() == event.KeyPress:
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