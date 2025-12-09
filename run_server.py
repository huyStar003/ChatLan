import os
import sys
import signal
import threading
import time
import configparser
from typing import Dict, Any

def load_server_config(config_path: str = "server_config.ini") -> Dict[str, Any]:
    """
    Đọc cấu hình server từ file INI.
    Fallback về giá trị mặc định nếu file không tồn tại.
    """
    defaults = {
        "host": "0.0.0.0",
        "port": 12345
    }
    
    config = configparser.ConfigParser()
    if os.path.exists(config_path):
        try:
            config.read(config_path, encoding='utf-8')
            if 'Server' in config:
                server_config = config['Server']
                return {
                    "host": server_config.get('host', defaults['host']),
                    "port": int(server_config.get('port', defaults['port']))
                }
        except Exception as e:
            print(f"⚠️ Lỗi đọc config file {config_path}: {e}. Sử dụng giá trị mặc định.")
    
    return defaults

def check_dependencies():
    """Kiểm tra các thư viện cần thiết"""
    required_packages = [
        'sqlalchemy',
        'hashlib',
        'socket',
        'threading',
        'json',
        'base64',
        'datetime'
    ]    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'hashlib':
                import hashlib
            elif package == 'socket':
                import socket
            elif package == 'threading':
                import threading
            elif package == 'json':
                import json
            elif package == 'base64':
                import base64
            elif package == 'datetime':
                import datetime
            elif package == 'sqlalchemy':
                import sqlalchemy
        except ImportError:
            missing_packages.append(package)
    if missing_packages:
        print("❌ Thiếu các thư viện sau:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Cài đặt bằng lệnh:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False   
    return True

def main():
    """Main function"""
    print("🚀 Khởi động Chat LAN Server v3.0...")
    print("=" * 60)    
    # Check dependencies
    if not check_dependencies():
        input("\nNhấn Enter để thoát...")
        return 1    
    try:
        # Import server
        from server.server import ChatServer
        
        # Đọc cấu hình từ file
        server_config = load_server_config()
        SERVER_HOST = server_config["host"]
        SERVER_PORT = server_config["port"]
        
        print("📋 Thông tin Server:")
        print(f"   - Host: {SERVER_HOST}")
        print(f"   - Port: {SERVER_PORT}")
        print("   - Protocol: TCP Socket")
        print("   - Database: PostGreSQL")
        print("   - Features: Authentication, File Upload, Real-time Chat")
        print("=" * 60)        
        # Create server
        server = ChatServer(host=SERVER_HOST, port=SERVER_PORT)        
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n🛑 Nhận tín hiệu dừng server...")
            server.stop()
            sys.exit(0)        
        signal.signal(signal.SIGINT, signal_handler)       
        # Start server
        print("🌐 Server đang khởi động...")
        print("⏹️  Nhấn Ctrl+C để dừng server")
        print("=" * 60)       
        server.start()       
    except KeyboardInterrupt:
        print("\n👋 Server đã dừng!")
        return 0
    except ImportError as e:
        print(f"❌ Lỗi import: {e}")
        print("💡 Đảm bảo bạn đang chạy từ thư mục gốc của project")
        input("\nNhấn Enter để thoát...")
        return 1
    except Exception as e:
        print(f"❌ Lỗi khởi động server: {e}")
        input("\nNhấn Enter để thoát...")
        return 1

if __name__ == "__main__":
    sys.exit(main())