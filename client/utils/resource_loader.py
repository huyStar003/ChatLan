"""Resource path utilities for PyInstaller compatibility."""
import sys
import os


def resource_path(relative_path: str) -> str:
    """
    Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả dev và PyInstaller.
    
    Args:
        relative_path: Đường dẫn tương đối từ thư mục resources
        
    Returns:
        Đường dẫn tuyệt đối đến resource
    """
    try:
        # PyInstaller tạo một thư mục tạm thời và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Nếu không phải đang chạy từ file đã đóng gói, dùng đường dẫn bình thường
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))
    
    return os.path.join(base_path, relative_path)

