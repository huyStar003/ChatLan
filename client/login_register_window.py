import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox, QFrame,
                            QTabWidget, QCheckBox, QGroupBox, QTextEdit,
                            QProgressBar, QComboBox, QSizePolicy, QSpacerItem, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QIcon
from .socket_client import SocketClient
import json
import hashlib

class LoginRegisterWindow(QWidget):
    login_successful = pyqtSignal(dict)  # user_data
    
    def __init__(self):
        super().__init__()
        self.client = SocketClient()
        self.setup_client_connections()
        self.init_ui()
        self.setup_chatlan_styles()
        self.load_saved_settings()
        self.center_on_screen()
        
        self.login_attempts = 0
        self.max_login_attempts = 5
        
    def setup_client_connections(self):
        self.client.connected.connect(self.on_connected)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.message_received.connect(self.on_message_received)
        self.client.error_occurred.connect(self.on_error_occurred)
        
    def reset_login_form(self):
        self.login_password.clear()
        self.hide_error_message()
        self.login_button.setEnabled(True)
        self.login_button.setText("Đăng nhập")
        
    def init_ui(self):
        self.setWindowTitle("ChatLAN - Đăng nhập")
        self.setFixedSize(1000,1000)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(30)
        left_layout.setContentsMargins(50, 80, 50, 80)
        
        logo_layout = QHBoxLayout()
        logo_icon = QLabel("💬")
        logo_icon.setFont(QFont("Arial", 32))
        logo_icon.setStyleSheet("color: #0068ff;")
        
        logo_text = QLabel("CHAT LAN")
        logo_text.setFont(QFont("Arial", 20, QFont.Bold))
        logo_text.setStyleSheet("color: #0068ff; margin-left: 5px;")
        
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        
        
        
        description = QLabel(
            "Nền tảng nhắn tin dành cho mạng nội bộ,\n"
            "kết nối mọi người trong tổ chức của bạn một cách\n"
            "nhanh chóng, an toàn và hiệu quả."
        )
        description.setFont(QFont("Arial", 14))
        description.setStyleSheet("color: #666; line-height: 1.5;")
        description.setWordWrap(True)
        
        left_layout.addLayout(logo_layout)
   
        left_layout.addWidget(description)
        left_layout.addStretch()
        
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20) # Giảm spacing
        right_layout.setContentsMargins(60, 40, 60, 40) # Điều chỉnh margin
        
        form_header = QLabel("Đăng nhập chatlan")
        form_header.setFont(QFont("Arial", 20, QFont.Bold))
        form_header.setStyleSheet("color: #333; margin-bottom: 10px;")
        form_header.setAlignment(Qt.AlignCenter)
        
        server_frame = QFrame()
        server_frame.setObjectName("serverFrame")
        server_layout = QVBoxLayout(server_frame)
        server_layout.setSpacing(10)
        server_layout.setContentsMargins(20, 15, 20, 15)
        
        server_title = QLabel("Kết nối Server")
        server_title.setFont(QFont("Arial", 12, QFont.Bold))
        server_title.setStyleSheet("color: #666;")
        
        server_input_layout = QHBoxLayout()
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost")
        self.host_input.setText("localhost")
        self.host_input.setFont(QFont("Arial", 11))
        self.host_input.setMinimumHeight(35)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("12345")
        self.port_input.setText("12345")
        self.port_input.setFont(QFont("Arial", 11))
        self.port_input.setMaximumWidth(80)
        self.port_input.setMinimumHeight(35)
        
        self.connect_button = QPushButton("Kết nối")
        self.connect_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.connect_button.setMinimumHeight(35)
        self.connect_button.setMaximumWidth(80)
        self.connect_button.clicked.connect(self.connect_to_server)
        self.connect_button.setObjectName("connectButton")
        
        server_input_layout.addWidget(self.host_input, 3)
        server_input_layout.addWidget(self.port_input, 1)
        server_input_layout.addWidget(self.connect_button, 1)
        
        self.connection_status = QLabel("Chưa kết nối")
        self.connection_status.setFont(QFont("Arial", 10))
        self.connection_status.setStyleSheet("color: #e74c3c; text-align: center;")
        self.connection_status.setAlignment(Qt.AlignCenter)
        
        server_layout.addWidget(server_title)
        server_layout.addLayout(server_input_layout)
        server_layout.addWidget(self.connection_status)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Arial", 12))
        self.tab_widget.setObjectName("chatlanTabWidget")
        
        # Login tab
        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)
        login_layout.setSpacing(15) # Giảm spacing
        login_layout.setContentsMargins(0, 15, 0, 15) # Điều chỉnh margin
        
        self.login_error_frame = QFrame()
        self.login_error_frame.setObjectName("errorFrame")
        self.login_error_frame.setVisible(False)
        error_layout = QVBoxLayout(self.login_error_frame)
        error_layout.setContentsMargins(15, 10, 15, 10)
        
        self.login_error_message = QLabel("")
        self.login_error_message.setFont(QFont("Arial", 10))
        self.login_error_message.setWordWrap(True)
        self.login_error_message.setAlignment(Qt.AlignCenter)
        self.login_error_message.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        error_layout.addWidget(self.login_error_message)
        
        # SỬ DỤNG QFormLayout cho form đăng nhập
        login_form_layout = QFormLayout()
        login_form_layout.setSpacing(10)
        login_form_layout.setLabelAlignment(Qt.AlignLeft)
        login_form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Nhập tên đăng nhập")
        self.login_username.setFont(QFont("Arial", 12))
        self.login_username.setMinimumHeight(40)
        self.login_username.returnPressed.connect(self.handle_login)
        self.login_username.setObjectName("chatlanInput")
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Nhập mật khẩu")
        self.login_password.setFont(QFont("Arial", 12))
        self.login_password.setMinimumHeight(40)
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.returnPressed.connect(self.handle_login)
        self.login_password.setObjectName("chatlanInput")
        
        login_form_layout.addRow("Tên đăng nhập", self.login_username)
        login_form_layout.addRow("Mật khẩu", self.login_password)

        self.remember_login = QCheckBox("Ghi nhớ đăng nhập")
        self.remember_login.setFont(QFont("Arial", 10))
        self.remember_login.setChecked(True)
        self.remember_login.setObjectName("chatlanCheckbox")
        
        self.login_button = QPushButton("Đăng nhập")
        self.login_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.login_button.setMinimumHeight(45)
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setEnabled(False)
        self.login_button.setObjectName("chatlanLoginButton")
        
        forgot_password = QLabel('<a href="#" style="color: #0068ff; text-decoration: none;">Quên mật khẩu?</a>')
        forgot_password.setFont(QFont("Arial", 10))
        forgot_password.setAlignment(Qt.AlignCenter)
        forgot_password.setOpenExternalLinks(False)
        
        self.login_attempts_label = QLabel("")
        self.login_attempts_label.setFont(QFont("Arial", 9))
        self.login_attempts_label.setAlignment(Qt.AlignCenter)
        self.login_attempts_label.setStyleSheet("color: #e67e22; margin-top: 5px;")
        self.login_attempts_label.setVisible(False)
        
        login_layout.addWidget(self.login_error_frame)
        login_layout.addLayout(login_form_layout)
        login_layout.addWidget(self.remember_login)
        login_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)) # Thêm khoảng trống
        login_layout.addWidget(self.login_button)
        login_layout.addWidget(forgot_password)
        login_layout.addWidget(self.login_attempts_label)
        login_layout.addStretch()
        
        # Register tab
        register_tab = QWidget()
        register_layout = QVBoxLayout(register_tab)
        register_layout.setSpacing(12)
        register_layout.setContentsMargins(0, 15, 0, 15)
        
        self.register_error_frame = QFrame()
        self.register_error_frame.setObjectName("errorFrame")
        self.register_error_frame.setVisible(False)
        register_error_layout = QVBoxLayout(self.register_error_frame)
        register_error_layout.setContentsMargins(15, 10, 15, 10)
        
        self.register_error_message = QLabel("")
        self.register_error_message.setFont(QFont("Arial", 10))
        self.register_error_message.setWordWrap(True)
        self.register_error_message.setAlignment(Qt.AlignCenter)
        self.register_error_message.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        register_error_layout.addWidget(self.register_error_message)
        
        # SỬ DỤNG QFormLayout cho form đăng ký
        register_form_layout = QFormLayout()
        register_form_layout.setSpacing(10)
        register_form_layout.setLabelAlignment(Qt.AlignLeft)
        register_form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)

        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Nhập tên đăng nhập (3-20 ký tự)")
        self.register_username.setFont(QFont("Arial", 12))
        self.register_username.setMinimumHeight(38)
        self.register_username.setObjectName("chatlanInput")
        
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Ít nhất 6 ký tự")
        self.register_password.setFont(QFont("Arial", 12))
        self.register_password.setMinimumHeight(38)
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setObjectName("chatlanInput")
        
        self.register_confirm_password = QLineEdit()
        self.register_confirm_password.setPlaceholderText("Nhập lại mật khẩu")
        self.register_confirm_password.setFont(QFont("Arial", 12))
        self.register_confirm_password.setMinimumHeight(38)
        self.register_confirm_password.setEchoMode(QLineEdit.Password)
        self.register_confirm_password.returnPressed.connect(self.handle_register)
        self.register_confirm_password.setObjectName("chatlanInput")
        
        self.register_display_name = QLineEdit()
        self.register_display_name.setPlaceholderText("Tên hiển thị (tùy chọn)")
        self.register_display_name.setFont(QFont("Arial", 12))
        self.register_display_name.setMinimumHeight(38)
        self.register_display_name.setObjectName("chatlanInput")
        
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Email (tùy chọn)")
        self.register_email.setFont(QFont("Arial", 12))
        self.register_email.setMinimumHeight(38)
        self.register_email.setObjectName("chatlanInput")

        register_form_layout.addRow("Tên đăng nhập", self.register_username)
        register_form_layout.addRow("Mật khẩu", self.register_password)
        register_form_layout.addRow("Xác nhận mật khẩu", self.register_confirm_password)
        register_form_layout.addRow("Tên hiển thị", self.register_display_name)
        register_form_layout.addRow("Email", self.register_email)

        self.show_password_register = QCheckBox("Hiển thị mật khẩu")
        self.show_password_register.setFont(QFont("Arial", 10))
        self.show_password_register.toggled.connect(self.toggle_register_password_visibility)
        self.show_password_register.setObjectName("chatlanCheckbox")
        
        self.register_button = QPushButton("Đăng ký")
        self.register_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.register_button.setMinimumHeight(45)
        self.register_button.clicked.connect(self.handle_register)
        self.register_button.setEnabled(False)
        self.register_button.setObjectName("chatlanRegisterButton")
        
        register_layout.addWidget(self.register_error_frame)
        register_layout.addLayout(register_form_layout)
        register_layout.addWidget(self.show_password_register)
        register_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)) # Thêm khoảng trống
        register_layout.addWidget(self.register_button)
        register_layout.addStretch()
        
        self.tab_widget.addTab(login_tab, "Đăng nhập") # Đổi tên tab cho phù hợp
        self.tab_widget.addTab(register_tab, "Đăng ký")
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(40)
        self.status_label.setVisible(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setMinimumHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setObjectName("chatlanProgressBar")
        
        right_layout.addWidget(form_header)
        right_layout.addWidget(server_frame)
        right_layout.addWidget(self.tab_widget)
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.status_label)
        right_layout.addStretch(1) # Thêm stretch để đẩy các widget lên
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        self.setLayout(main_layout)
        
        self.login_username.setFocus()
        
    def setup_chatlan_styles(self):
        """Thiết lập style theo phong cách chatlan"""
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFormLayout QLabel {
                font-size: 11px;
                color: #666;
                padding-bottom: 5px;
            }
            #leftPanel {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #e8f4fd, stop: 0.5 #f0f8ff, stop: 1 #e0efff);
                border: none;
            }
            #rightPanel {
                background-color: #ffffff;
                border-left: 1px solid #e1e8ed;
            }
            #serverFrame {
                background-color: #f8f9fa;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            #chatlanInput {
                padding: 10px 12px;
                border: 1px solid #d1d9e0;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 12px;
                color: #333;
            }
            #chatlanInput:focus {
                border-color: #0068ff;
                outline: none;
                background-color: #ffffff;
            }
            #chatlanInput:hover {
                border-color: #74b9ff;
            }
            #chatlanLoginButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #0068ff, stop: 1 #0052cc);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 12px;
            }
            #chatlanLoginButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #0052cc, stop: 1 #003d99);
            }
            #chatlanLoginButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #003d99, stop: 1 #002966);
            }
            #chatlanLoginButton:disabled {
                background-color: #b0b0b0;
                color: #ffffff;
            }
            #chatlanRegisterButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #28a745, stop: 1 #218838);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 12px;
            }
            #chatlanRegisterButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #218838, stop: 1 #1e7e34);
            }
            #chatlanRegisterButton:disabled {
                background-color: #b0b0b0;
                color: #ffffff;
            }
            #connectButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
                padding: 8px 12px;
            }
            #connectButton:hover {
                background-color: #138496;
            }
            #connectButton:disabled {
                background-color: #6c757d;
            }
            #chatlanCheckbox {
                color: #666;
                font-size: 10px;
                spacing: 8px;
                margin-top: 5px;
            }
            #chatlanCheckbox::indicator {
                width: 16px;
                height: 16px;
            }
            #chatlanCheckbox::indicator:unchecked {
                border: 1px solid #d1d9e0;
                border-radius: 3px;
                background-color: white;
            }
            #chatlanCheckbox::indicator:checked {
                border: 1px solid #0068ff;
                border-radius: 3px;
                background-color: #0068ff;
            }
            #chatlanTabWidget::pane {
                border: 1px solid #e1e8ed;
                border-top: none;
                border-radius: 0 0 6px 6px;
                background-color: white;
            }
            #chatlanTabWidget QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #e1e8ed;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 12px 20px;
                margin-right: 2px;
                font-weight: bold;
                font-size: 11px;
                color: #666;
                min-width: 100px;
            }
            #chatlanTabWidget QTabBar::tab:selected {
                background-color: white;
                border-color: #e1e8ed;
                border-bottom: 1px solid white;
                color: #0068ff;
            }
            #chatlanTabWidget QTabBar::tab:hover {
                background-color: #e3f2fd;
                color: #0068ff;
            }
            #chatlanProgressBar {
                border: none;
                border-radius: 2px;
                background-color: #e1e8ed;
            }
            #chatlanProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #0068ff, stop: 1 #74b9ff);
                border-radius: 2px;
            }
            #errorFrame {
                background-color: #fff5f5;
                border: 1px solid #fed7d7;
                border-radius: 6px;
                margin: 5px 0;
            }
        """)
        
    def show_error_message(self, message, tab="login"):
        """Hiển thị thông báo lỗi"""
        if tab == "login":
            self.login_error_message.setText(message)
            self.login_error_frame.setVisible(True)
        else:
            self.register_error_message.setText(message)
            self.register_error_frame.setVisible(True)
            
    def hide_error_message(self, tab="login"):
        """Ẩn thông báo lỗi"""
        if tab == "login":
            self.login_error_frame.setVisible(False)
        else:
            self.register_error_frame.setVisible(False)
            
    def update_login_attempts_display(self):
        """Cập nhật hiển thị số lần thử đăng nhập"""
        if self.login_attempts > 0:
            remaining = self.max_login_attempts - self.login_attempts
            if remaining > 0:
                self.login_attempts_label.setText(
                    f"Còn {remaining} lần thử. Tài khoản sẽ bị khóa tạm thời nếu nhập sai tiếp."
                )
                self.login_attempts_label.setStyleSheet("color: #e67e22; font-weight: bold;")
            else:
                self.login_attempts_label.setText(
                    "Tài khoản đã bị khóa tạm thời. Vui lòng thử lại sau 5 phút."
                )
                self.login_attempts_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.login_attempts_label.setVisible(True)
        else:
            self.login_attempts_label.setVisible(False)
            
    def toggle_register_password_visibility(self, checked):
        """Toggle hiển thị mật khẩu đăng ký"""
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.register_password.setEchoMode(mode)
        self.register_confirm_password.setEchoMode(mode)
        
    def connect_to_server(self):
        """Kết nối đến server"""
        host = self.host_input.text().strip() or "localhost"
        try:
            port = int(self.port_input.text().strip() or "12345")
        except ValueError:
            self.show_status("Port phải là một số nguyên hợp lệ!", "error")
            return
        
        self.connect_button.setEnabled(False)
        self.connect_button.setText("Đang kết nối...")
        self.show_status("Đang kết nối đến server...", "info")
        self.progress_bar.setVisible(True)
        
        if self.client.connect_to_server(host, port):
            pass
        else:
            self.connect_button.setEnabled(True)
            self.connect_button.setText("Kết nối")
            self.progress_bar.setVisible(False)
            
    @pyqtSlot()
    def on_connected(self):
        """Xử lý khi kết nối thành công"""
        self.connection_status.setText("Đã kết nối")
        self.connection_status.setStyleSheet("color: #28a745; font-weight: bold;")
        self.connect_button.setText("Đã kết nối")
        self.connect_button.setEnabled(False)
        self.login_button.setEnabled(True)
        self.register_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.show_status("Kết nối thành công! Bạn có thể đăng nhập hoặc đăng ký.", "success")
        
    @pyqtSlot()
    def on_disconnected(self):
        """Xử lý khi mất kết nối"""
        self.connection_status.setText("Mất kết nối")
        self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.connect_button.setText("Kết nối lại")
        self.connect_button.setEnabled(True)
        self.login_button.setEnabled(False)
        self.register_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.show_status("Mất kết nối đến server. Vui lòng kết nối lại.", "error")
        
    @pyqtSlot(dict)
    def on_message_received(self, message):
        """Xử lý tin nhắn từ server"""
        message_type = message.get('type')
        success = message.get('success', False)
        
        if success:
            if 'session_token' in message:
                self.show_status("Đăng nhập thành công! Đang chuyển hướng...", "success")
                self.progress_bar.setVisible(False)
                self.hide_error_message("login")
                self.login_attempts = 0
                self.update_login_attempts_display()
                
                if self.remember_login.isChecked():
                    self.save_settings()
                    
                QTimer.singleShot(1500, lambda: self.login_successful.emit(message))
                
            elif message_type == 'register' or 'Đăng ký thành công' in message.get('message', ''):
                self.show_status("Đăng ký thành công! Bạn có thể đăng nhập ngay.", "success")
                self.progress_bar.setVisible(False)
                self.hide_error_message("register")
                self.reset_register_form()
                
                self.tab_widget.setCurrentIndex(0)
                self.login_username.setText(self.register_username.text())
                self.login_username.setFocus()
        else:
            error_msg = message.get('error', 'Có lỗi xảy ra')
            
            if message_type == 'login' or 'đăng nhập' in error_msg.lower():
                self.login_attempts += 1
                self.update_login_attempts_display()
                
                if 'tài khoản không tồn tại' in error_msg.lower() or 'username' in error_msg.lower():
                    self.show_error_message(
                        "Tài khoản không tồn tại. Vui lòng kiểm tra lại tên đăng nhập hoặc đăng ký tài khoản mới.",
                        "login"
                    )
                    self.login_username.setFocus()
                    self.login_username.selectAll()
                    
                elif 'mật khẩu' in error_msg.lower() or 'password' in error_msg.lower():
                    self.show_error_message(
                        f"Mật khẩu không chính xác. Còn {self.max_login_attempts - self.login_attempts} lần thử.",
                        "login"
                    )
                    self.login_password.setFocus()
                    self.login_password.selectAll()
                    
                elif self.login_attempts >= self.max_login_attempts:
                    self.show_error_message(
                        "Tài khoản đã bị khóa tạm thời do nhập sai quá nhiều lần. Vui lòng thử lại sau 5 phút.",
                        "login"
                    )
                    self.login_button.setEnabled(False)
                    QTimer.singleShot(300000, self.reset_login_attempts)
                else:
                    self.show_error_message(f"Lỗi đăng nhập: {error_msg}", "login")
                    
            elif message_type == 'register' or 'đăng ký' in error_msg.lower():
                if 'tài khoản đã tồn tại' in error_msg.lower():
                    self.show_error_message(
                        "Tài khoản đã tồn tại. Vui lòng chọn tên đăng nhập khác hoặc đăng nhập nếu đây là tài khoản của bạn.",
                        "register"
                    )
                    self.register_username.setFocus()
                    self.register_username.selectAll()
                else:
                    self.show_error_message(f"Lỗi đăng ký: {error_msg}", "register")
            else:
                self.show_status(f"Lỗi: {error_msg}", "error")
                
            self.progress_bar.setVisible(False)
            
        if self.login_attempts < self.max_login_attempts:
            self.login_button.setEnabled(True)
            self.login_button.setText("Đăng nhập")
        self.register_button.setEnabled(True)
        self.register_button.setText("Đăng ký")
        
    def reset_login_attempts(self):
        """Reset số lần thử đăng nhập"""
        self.login_attempts = 0
        self.update_login_attempts_display()
        self.login_button.setEnabled(True)
        self.hide_error_message("login")
        self.show_status("Tài khoản đã được mở khóa. Bạn có thể thử đăng nhập lại.", "info")
        
    @pyqtSlot(str)
    def on_error_occurred(self, error_message):
        """Xử lý lỗi"""
        self.show_status(f"Lỗi kết nối: {error_message}", "error")
        self.progress_bar.setVisible(False)
        
        self.login_button.setEnabled(self.client.is_connected() and self.login_attempts < self.max_login_attempts)
        self.login_button.setText("Đăng nhập")
        self.register_button.setEnabled(self.client.is_connected())
        self.register_button.setText("Đăng ký")
        
    def handle_login(self):
        """Xử lý đăng nhập"""
        if not self.client.is_connected():
            self.show_error_message("Vui lòng kết nối đến server trước khi đăng nhập.", "login")
            return
            
        if self.login_attempts >= self.max_login_attempts:
            self.show_error_message("Tài khoản đã bị khóa tạm thời. Vui lòng thử lại sau 5 phút.", "login")
            return
            
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username:
            self.show_error_message("Vui lòng nhập tài khoản.", "login")
            self.login_username.setFocus()
            return
            
        if len(username) < 3:
            self.show_error_message("tên đăng nhập phải có ít nhất 3 ký tự.", "login")
            self.login_username.setFocus()
            return
            
        if not password:
            self.show_error_message("Vui lòng nhập mật khẩu.", "login")
            self.login_password.setFocus()
            return
            
        if len(password) < 6:
            self.show_error_message("Mật khẩu phải có ít nhất 6 ký tự.", "login")
            self.login_password.setFocus()
            return
            
        self.hide_error_message("login")
        
        # Gửi plaintext password, server sẽ hash một lần
        # (Đã sửa từ double-hash: client hash -> server hash lại)
        
        self.login_button.setEnabled(False)
        self.login_button.setText("Đang đăng nhập...")
        self.show_status("Đang xác thực thông tin đăng nhập...", "info")
        self.progress_bar.setVisible(True)
        
        self.client.login(username, password)
        
    def handle_register(self):
        """Xử lý đăng ký"""
        if not self.client.is_connected():
            self.show_error_message("Vui lòng kết nối đến server trước khi đăng ký.", "register")
            return
            
        username = self.register_username.text().strip()
        password = self.register_password.text()
        confirm_password = self.register_confirm_password.text()
        display_name = self.register_display_name.text().strip()
        email = self.register_email.text().strip()
        
        if not username:
            self.show_error_message("Vui lòng nhập tên đăng nhập.", "register")
            self.register_username.setFocus()
            return
            
        if len(username) < 3 or len(username) > 20:
            self.show_error_message("Tên đăng nhập phải có từ 3-20 ký tự.", "register")
            self.register_username.setFocus()
            return
            
        if not password:
            self.show_error_message("Vui lòng nhập mật khẩu.", "register")
            self.register_password.setFocus()
            return
            
        if len(password) < 6:
            self.show_error_message("Mật khẩu phải có ít nhất 6 ký tự.", "register")
            self.register_password.setFocus()
            return
            
        if password != confirm_password:
            self.show_error_message("Mật khẩu xác nhận không khớp.", "register")
            self.register_confirm_password.setFocus()
            return
            
        if email and ('@' not in email or '.' not in email):
            self.show_error_message("Email không hợp lệ.", "register")
            self.register_email.setFocus()
            return
            
        self.hide_error_message("register")
        
        # Gửi plaintext password, server sẽ hash một lần
        # (Đã sửa từ double-hash: client hash -> server hash lại)
        
        self.register_button.setEnabled(False)
        self.register_button.setText("Đang đăng ký...")
        self.show_status("Đang tạo tài khoản...", "info")
        self.progress_bar.setVisible(True)
        
        self.client.register(username, password, display_name, email)
        
    def show_status(self, message, status_type="info"):
        """Hiển thị thông báo trạng thái"""
        self.status_label.setText(message)
        self.status_label.setVisible(True)
        
        if status_type == "error":
            self.status_label.setStyleSheet("""
                color: #e74c3c; 
                font-weight: bold; 
                background-color: #fff5f5; 
                padding: 10px; 
                border-radius: 6px; 
                border: 1px solid #fed7d7;
            """)
        elif status_type == "success":
            self.status_label.setStyleSheet("""
                color: #27ae60; 
                font-weight: bold; 
                background-color: #f0fff4; 
                padding: 10px; 
                border-radius: 6px; 
                border: 1px solid #c3e6cb;
            """)
        elif status_type == "info":
            self.status_label.setStyleSheet("""
                color: #0068ff; 
                font-weight: bold; 
                background-color: #f0f8ff; 
                padding: 10px; 
                border-radius: 6px; 
                border: 1px solid #bee5eb;
            """)
        else:
            self.status_label.setStyleSheet("color: #333; padding: 10px;")
            
        if status_type in ["success", "info"]:
            QTimer.singleShot(8000, lambda: self.status_label.setVisible(False))
            
    def reset_register_form(self):
        """Reset form đăng ký"""
        self.register_username.clear()
        self.register_password.clear()
        self.register_confirm_password.clear()
        self.register_display_name.clear()
        self.register_email.clear()
        self.show_password_register.setChecked(False)
        self.hide_error_message("register")
        
    def save_settings(self):
        """Lưu cài đặt"""
        try:
            settings = {
                "host": self.host_input.text().strip(),
                "port": self.port_input.text().strip(),
                "username": self.login_username.text().strip(),
                "remember_login": self.remember_login.isChecked()
            }
            with open("chat_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def load_saved_settings(self):
        """Load cài đặt đã lưu"""
        try:
            with open("chat_settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            self.host_input.setText(settings.get("host", "localhost"))
            self.port_input.setText(settings.get("port", "12345"))
            self.login_username.setText(settings.get("username", ""))
            self.remember_login.setChecked(settings.get("remember_login", True))
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def center_on_screen(self):
        """Căn giữa cửa sổ trên màn hình"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def closeEvent(self, event):
        """Xử lý khi đóng cửa sổ"""
        if self.client.is_connected():
            self.client.disconnect()
        event.accept()

