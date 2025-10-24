import json
import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Các import này vẫn cần thiết cho các lớp bên dưới
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from client.login_register_window import LoginRegisterWindow
from client.main_chat_window import MainChatWindow

def load_and_apply_initial_theme(app):
    """Tải và áp dụng theme ngay khi ứng dụng khởi động."""
    try:
        if os.path.exists("chat_settings.json"):
            with open("chat_settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            if settings.get('theme') == 'dark':
                script_dir = os.path.dirname(os.path.realpath(__file__))
                qss_path = os.path.join(script_dir, 'dark_theme.qss')
                with open(qss_path, "r") as f:
                    app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Không thể tải theme ban đầu: {e}")

class ApplicationController:
    """Lớp quản lý luồng hoạt động của ứng dụng."""
    def __init__(self):
        self.login_window = None
        self.main_chat_window = None

    def run(self):
        """Bắt đầu vòng lặp ứng dụng."""
        self.show_login()

    def show_login(self):
        """Hiển thị cửa sổ đăng nhập."""
        if not self.login_window:
            self.login_window = LoginRegisterWindow()
            self.login_window.login_successful.connect(self.on_login_success)
        self.login_window.center_on_screen()
        self.login_window.show()

    def on_login_success(self, user_data):
        """Xử lý khi đăng nhập thành công."""
        print("Đăng nhập thành công, chuyển sang cửa sổ chat chính.")
        client = self.login_window.client
        
        self.main_chat_window = MainChatWindow(client, user_data)
        self.main_chat_window.logged_out.connect(self.on_logout)
        
        self.login_window.hide()
        self.main_chat_window.show()
        
        print("Đang tải dữ liệu ban đầu...")
        all_users = user_data.get('all_users', [])
        conversations = user_data.get('conversations', [])
        
        self.main_chat_window.update_contacts([], all_users)
        self.main_chat_window.update_conversations(conversations)
        
        if conversations:
            print("Mở cuộc hội thoại đầu tiên làm mặc định...")
            first_conv = conversations[0]
            if first_conv.get('type') == 'private':
                self.main_chat_window.start_private_chat(first_conv['other_user'])
            elif first_conv.get('type') == 'group':
                self.main_chat_window.start_group_chat(first_conv['group_id'], first_conv['group_name'])
        else:
            print("Không có hội thoại nào, hiển thị màn hình chào mừng.")
            self.main_chat_window.show_welcome_screen()

    def on_logout(self):
        """Xử lý khi đăng xuất."""
        print("Đã đăng xuất, quay về màn hình đăng nhập.")
        if self.main_chat_window:
            self.main_chat_window.deleteLater()
            self.main_chat_window = None
        self.login_window.reset_login_form()
        self.show_login()