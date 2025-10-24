import os
from PyQt5.QtWidgets import QMessageBox,QApplication 
from PyQt5.QtGui import QFont
import sys
def check_dependencies():
    """Kiểm tra các thư viện cần thiết"""
    required_packages = {
        'PyQt5': 'PyQt5',
        'socket': 'socket',
        'json': 'json',
        'threading': 'threading',
        'hashlib': 'hashlib',
        'base64': 'base64',
        'datetime': 'datetime'
    }
    missing_packages = []
    for package_name, import_name in required_packages.items():
        try:
            if import_name == 'PyQt5':
                from PyQt5.QtWidgets import QApplication
            elif import_name == 'socket':
                import socket
            elif import_name == 'json':
                import json
            elif import_name == 'threading':
                import threading
            elif import_name == 'hashlib':
                import hashlib
            elif import_name == 'base64':
                import base64
            elif import_name == 'datetime':
                import datetime
        except ImportError:
            missing_packages.append(package_name)
    if missing_packages:
        print("❌ Thiếu các thư viện sau:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Cài đặt bằng lệnh:")
        if 'PyQt5' in missing_packages:
            print("   pip install PyQt5")
        return False
    return True
def main():
    """Hàm main chính để khởi động ứng dụng (ĐÃ SỬA LỖI KHỞI TẠO TÀI NGUYÊN)"""
    print("💬 Khởi động Chat LAN Client v3.0...")
    print("=" * 60)
    
    if not check_dependencies():
        return 1
        
    try:
        # --- LOGIC SỬA LỖI NẰM Ở ĐÂY ---
        
        # 1. Tạo đối tượng QApplication TRƯỚC TIÊN
        app = QApplication(sys.argv)
        
        # 2. Import file tài nguyên đã được biên dịch
        from client import resources_rc
        
        # 3. Gọi hàm qInitResources() để đăng ký tài nguyên với ứng dụng
        #    Đây là bước quan trọng nhất để icon hoạt động sau khi đóng gói.
        resources_rc.qInitResources()
        
        # 4. Bây giờ mới import và chạy các thành phần còn lại của ứng dụng
        from client.simple_main import ApplicationController, load_and_apply_initial_theme

        print("📋 Thông tin Client...")
        print("=" * 60)

        # Thiết lập các thuộc tính cho app
        app.setApplicationName("Chat LAN Enterprise")
        app.setStyle('Fusion')
        font = QFont("Arial", 10)
        app.setFont(font)
        load_and_apply_initial_theme(app)
        app.setQuitOnLastWindowClosed(False) # Giữ nguyên hành vi của bạn
        
        # 5. Khởi tạo và chạy Controller
        controller = ApplicationController()
        controller.run()
        
        # 6. Bắt đầu vòng lặp sự kiện của ứng dụng
        return app.exec_()
        
        # ------------------------------------

    except ImportError as e:
        print(f"❌ Lỗi import: {e}")
        print("💡 Đảm bảo bạn đang chạy từ thư mục gốc của project")
        return 1
    except Exception as e:
        print(f"❌ Lỗi khởi động client: {e}")
        QMessageBox.critical(None, "Lỗi nghiêm trọng", f"Ứng dụng gặp lỗi: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())