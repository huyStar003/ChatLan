# 💬 Chat LAN Enterprise v3.0

Hệ thống chat nội bộ doanh nghiệp được xây dựng bằng Python, hỗ trợ chat nhóm và chat riêng tư với giao diện hiện đại, tương tự Zalo.

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu hình](#-cấu-hình)
- [Sử dụng](#-sử-dụng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Đóng gói ứng dụng](#-đóng-gói-ứng-dụng)
- [Xử lý sự cố](#-xử-lý-sự-cố)
- [Đóng góp](#-đóng-góp)
- [License](#-license)

## ✨ Tính năng

### 🔐 Xác thực và Bảo mật
- ✅ Đăng ký/Đăng nhập với mã hóa mật khẩu (SHA-256)
- ✅ Quản lý session token
- ✅ Xác thực người dùng an toàn

### 💬 Chat
- ✅ Chat nhóm (Group Chat) - Tạo và quản lý nhóm chat
- ✅ Chat riêng tư (Private Chat) - Trò chuyện 1-1
- ✅ Gửi tin nhắn văn bản
- ✅ Trạng thái "đang gõ" (Typing indicator)
- ✅ Tin nhắn real-time với Optimistic UI Update
- ✅ Hiển thị thời gian gửi tin nhắn

### 📎 Đa phương tiện
- ✅ Gửi file đính kèm (tối đa 10MB)
- ✅ Gửi hình ảnh
- ✅ Xem trước media trong ứng dụng

### 🎨 Giao diện
- ✅ Giao diện hiện đại, tương tự Zalo
- ✅ Dark theme và Light theme
- ✅ Emoji picker
- ✅ Chat bubbles với màu sắc phân biệt
- ✅ Responsive design

### 🔍 Tìm kiếm và Quản lý
- ✅ Tìm kiếm tin nhắn trong cuộc trò chuyện
- ✅ Export lịch sử chat ra file text
- ✅ Xóa lịch sử chat
- ✅ Quản lý danh sách liên hệ
- ✅ Quản lý danh sách hội thoại

### 👥 Quản lý Nhóm
- ✅ Tạo nhóm chat mới
- ✅ Thêm/Xóa thành viên khỏi nhóm
- ✅ Xem danh sách thành viên nhóm
- ✅ Quản lý quyền thành viên

### 🔄 Kết nối
- ✅ Auto-reconnect khi mất kết nối
- ✅ Hiển thị trạng thái online/offline
- ✅ Thông báo khi người dùng thay đổi trạng thái

## 💻 Yêu cầu hệ thống

### Server
- **Python**: 3.7 trở lên
- **PostgreSQL**: 12 trở lên
- **Hệ điều hành**: Windows, Linux, macOS

### Client
- **Python**: 3.7 trở lên
- **Hệ điều hành**: Windows, Linux, macOS
- **RAM**: Tối thiểu 512MB
- **Ổ cứng**: 100MB trống

## 📦 Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd ChatLAN
```

### 2. Cài đặt PostgreSQL

Tải và cài đặt PostgreSQL từ [postgresql.org](https://www.postgresql.org/download/)

Tạo database và user:

```sql
CREATE DATABASE chat_lan_db;
CREATE USER chat_user WITH PASSWORD 'chat_password';
GRANT ALL PRIVILEGES ON DATABASE chat_lan_db TO chat_user;
```

### 3. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

Hoặc cài đặt từng package:

```bash
pip install PyQt5>=5.15.0
pip install sqlalchemy>=1.4.0
pip install psycopg2-binary>=2.9.0
```

### 4. Cấu hình Database

Chỉnh sửa file `server_config.ini`:

```ini
[Server]
host = 192.168.1.10  # IP của server
port = 12345

[Database]
db_user = chat_user
db_password = chat_password
db_host = 192.168.1.10
db_port = 5432
db_name = chat_lan_db
```

## ⚙️ Cấu hình

### Server Configuration

File `server_config.ini` chứa các cấu hình:

- **host**: Địa chỉ IP mà server sẽ lắng nghe (0.0.0.0 để lắng nghe tất cả)
- **port**: Cổng mà server sử dụng (mặc định: 12345)
- **Database**: Thông tin kết nối PostgreSQL

### Client Configuration

Client tự động kết nối đến server khi khởi động. Đảm bảo:
- Server đang chạy
- IP và port trong `server_config.ini` đúng
- Firewall cho phép kết nối

## 🚀 Sử dụng

### Khởi động Server

**Cách 1: Sử dụng Python script**
```bash
python run_server.py
```

**Cách 2: Sử dụng file exe (Windows)**
```bash
cd dist
start_server.bat
```

**Cách 3: Chạy trực tiếp file exe**
```bash
cd dist
run_server.exe
```

### Khởi động Client

**Cách 1: Sử dụng Python script**
```bash
python run_client.py
```

**Cách 2: Sử dụng file exe (Windows)**
```bash
cd dist
ChatLAN.exe
```

### Đăng ký tài khoản

1. Mở ứng dụng client
2. Click "Đăng ký"
3. Điền thông tin:
   - Username (bắt buộc)
   - Password (bắt buộc)
   - Display Name (tùy chọn)
   - Email (tùy chọn)
4. Click "Đăng ký"

### Đăng nhập

1. Nhập Username và Password
2. Click "Đăng nhập"
3. Sau khi đăng nhập thành công, bạn sẽ thấy giao diện chat chính

### Gửi tin nhắn

1. Chọn một cuộc trò chuyện từ sidebar
2. Nhập tin nhắn vào ô nhập liệu
3. Nhấn Enter hoặc click nút "Gửi"
4. Sử dụng Shift+Enter để xuống dòng

### Tạo nhóm chat

1. Click nút "Tạo nhóm" (icon +) trên sidebar
2. Nhập tên nhóm
3. Chọn các thành viên từ danh sách
4. Click "Tạo nhóm"

### Gửi file

1. Chọn cuộc trò chuyện
2. Click icon đính kèm (📎)
3. Chọn file cần gửi (tối đa 10MB)
4. File sẽ được upload và hiển thị trong chat

### Tìm kiếm tin nhắn

1. Mở cuộc trò chuyện cần tìm
2. Click icon tìm kiếm (🔍) hoặc nhấn Ctrl+F
3. Nhập từ khóa
4. Xem kết quả trong dialog

### Export lịch sử chat

1. Mở cuộc trò chuyện cần export
2. Vào menu "File" > "Export lịch sử chat"
3. Chọn vị trí lưu file
4. File sẽ được lưu dưới dạng .txt

## 📁 Cấu trúc dự án

```
ChatLAN/
├── client/                 # Client application
│   ├── core/              # Core models và managers
│   │   ├── models/        # Data models (User, Message, Conversation)
│   │   └── managers/      # Business logic managers
│   ├── ui/                # UI components
│   │   ├── components/    # Main UI components (Sidebar, ChatArea, InfoSidebar)
│   │   ├── dialogs/       # Dialog windows
│   │   └── widgets/        # Custom widgets (ChatBubble, etc.)
│   ├── resources/         # Resources (icons, images)
│   ├── utils/             # Utility functions
│   ├── main_chat_window.py    # Main chat window
│   ├── login_register_window.py  # Login/Register window
│   ├── socket_client.py   # Socket client implementation
│   └── simple_main.py     # Application controller
│
├── server/                # Server application
│   ├── server.py         # Main server logic
│   ├── database.py       # Database operations
│   └── models.py         # Database models
│
├── dist/                  # Distribution files (exe, configs)
├── build/                 # Build artifacts
│
├── run_client.py         # Client entry point
├── run_server.py         # Server entry point
├── server_config.ini     # Server configuration
├── requirements.txt       # Python dependencies
├── ChatLAN.spec          # PyInstaller spec for client
├── run_server.spec       # PyInstaller spec for server
└── README.md             # This file
```

## 🛠️ Công nghệ sử dụng

### Frontend (Client)
- **PyQt5**: Framework GUI
- **Python Socket**: Kết nối TCP với server
- **JSON**: Serialization dữ liệu

### Backend (Server)
- **Python Socket**: TCP server
- **SQLAlchemy**: ORM cho database
- **PostgreSQL**: Database server
- **Threading**: Xử lý đa luồng

### Database Schema
- **Users**: Thông tin người dùng
- **Groups**: Thông tin nhóm chat
- **Messages**: Tin nhắn
- **GroupMembers**: Thành viên nhóm

## 📦 Đóng gói ứng dụng

### Sử dụng PyInstaller

**Đóng gói Client:**
```bash
pyinstaller ChatLAN.spec
```

**Đóng gói Server:**
```bash
pyinstaller run_server.spec
```

File exe sẽ được tạo trong thư mục `dist/`

### Tùy chỉnh spec file

Chỉnh sửa file `.spec` để:
- Thêm/bớt file và thư mục
- Thay đổi icon
- Cấu hình options

## 🔧 Xử lý sự cố

### Server không khởi động được

**Lỗi: "Address already in use"**
- Port đang được sử dụng bởi ứng dụng khác
- Giải pháp: Thay đổi port trong `server_config.ini`

**Lỗi: "Cannot connect to database"**
- Kiểm tra PostgreSQL đang chạy
- Kiểm tra thông tin trong `server_config.ini`
- Kiểm tra firewall

### Client không kết nối được server

**Lỗi: "Không có kết nối đến server"**
- Kiểm tra server đang chạy
- Kiểm tra IP và port trong `server_config.ini`
- Kiểm tra firewall cho phép kết nối
- Kiểm tra network connectivity

### Tin nhắn không hiển thị

- Kiểm tra console log để xem debug messages
- Đảm bảo đã chọn đúng cuộc trò chuyện
- Thử refresh bằng cách đóng và mở lại cuộc trò chuyện

### Lỗi import module

**Lỗi: "ModuleNotFoundError"**
- Cài đặt lại dependencies: `pip install -r requirements.txt`
- Đảm bảo đang chạy từ thư mục gốc của project

### Database errors

**Lỗi: "Table does not exist"**
- Database chưa được khởi tạo
- Chạy lại server để tự động tạo tables

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng:

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

### Coding Standards

- Sử dụng Python PEP 8 style guide
- Comment code bằng tiếng Việt
- Viết docstring cho các hàm quan trọng
- Test trước khi commit

## 📝 Changelog

### v3.0.0
- ✅ Giao diện mới hiện đại như Zalo
- ✅ Optimistic UI Update
- ✅ Cải thiện hiệu năng
- ✅ Auto-reconnect
- ✅ Export lịch sử chat
- ✅ Tìm kiếm tin nhắn
- ✅ Quản lý nhóm chat nâng cao

## 📄 License

Dự án này được phát hành dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## 👨‍💻 Tác giả

Chat LAN Enterprise Team

## 🙏 Lời cảm ơn

- PyQt5 community
- SQLAlchemy team
- PostgreSQL community
- Tất cả contributors

## 📞 Liên hệ

Nếu có câu hỏi hoặc gặp vấn đề, vui lòng:
- Mở issue trên GitHub
- Gửi email đến team

---

**Made with ❤️ by Chat LAN Enterprise Team**

