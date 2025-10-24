import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon, QFont
from .login_register_window import LoginRegisterWindow
from .main_chat_window import MainChatWindow
from .socket_client import SocketClient

class ChatApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Chat LAN Enterprise")
        self.app.setApplicationVersion("3.0.0")
        self.app.setOrganizationName("Enterprise Solutions")
        
        # Set application style
        self.app.setStyle('Fusion')
        
        # Set default font
        font = QFont("Arial", 10)
        self.app.setFont(font)
        
        # Windows and clients
        self.login_window = None
        self.main_window = None
        self.client = None
        
        self.init_application()
    
    def init_application(self):
        """Khởi tạo ứng dụng"""
        # Show login window
        self.show_login_window()
    
    def show_login_window(self):
        """Hiển thị cửa sổ đăng nhập"""
        self.login_window = LoginRegisterWindow()
        self.login_window.login_successful.connect(self.on_login_successful)
        self.login_window.center_on_screen()
        self.login_window.show()
    
    @pyqtSlot(dict)
    def on_login_successful(self, user_data):
        """Xử lý khi đăng nhập thành công"""
        try:
            # Get client from login window
            self.client = self.login_window.client
            
            # Hide login window
            self.login_window.hide()
            
            # Show main chat window
            self.main_window = MainChatWindow(self.client, user_data)
            self.main_window.show()
            
            # Handle main window close
            self.main_window.destroyed.connect(self.on_main_window_closed)
            
        except Exception as e:
            QMessageBox.critical(
                None,
                "Lỗi",
                f"Không thể khởi động cửa sổ chat chính:\n{str(e)}"
            )
            self.app.quit()
    
    def on_main_window_closed(self):
        """Xử lý khi cửa sổ chính bị đóng"""
        # Show login window again or quit
        self.show_login_window()
    
    def run(self):
        """Chạy ứng dụng"""
        try:
            return self.app.exec_()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Lỗi nghiêm trọng",
                f"Ứng dụng gặp lỗi nghiêm trọng:\n{str(e)}"
            )
            return 1

def main():
    """Hàm main"""
    try:
        # Enable high DPI scaling
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create and run application
        chat_app = ChatApplication()
        return chat_app.run()
        
    except Exception as e:
        print(f"❌ Lỗi khởi động ứng dụng: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
