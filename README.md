# YouTube Excel Loader — Python 🐍

Đọc file Excel chứa link YouTube.  
- **Chế độ Web** → Flask server, mở trình duyệt  
- **Chế độ Desktop** → pywebview bọc Flask thành app cửa sổ native  

---

## 📁 Cấu trúc dự án

```
yt-excel-python/
├── app.py              ← Flask server + logic đọc Excel
├── desktop.py          ← Launcher cho Desktop App (pywebview)
├── requirements.txt    ← Danh sách thư viện Python
└── templates/
    └── index.html      ← Giao diện web
```

---

## ⚙️ Yêu cầu

- **Python ≥ 3.10** → https://python.org/downloads  
  *(Chọn "Add to PATH" khi cài)*
- **VS Code** + extension **Python** (của Microsoft)

---

## 🚀 Cài đặt & Chạy

### Bước 1 — Mở thư mục trong VS Code
```
File → Open Folder → chọn thư mục yt-excel-python
```

### Bước 2 — Mở Terminal
```
Terminal → New Terminal  (Ctrl + `)
```

### Bước 3 — Tạo môi trường ảo (khuyên dùng)
```bash
python -m venv venv

# Kích hoạt (Windows):
venv\Scripts\activate

# Kích hoạt (macOS/Linux):
source venv/bin/activate
```

### Bước 4 — Cài thư viện
```bash
pip install -r requirements.txt
```

---

## ▶️ Chạy ứng dụng

### 🌐 Chế độ Web
```bash
python app.py
```
→ Mở trình duyệt vào **http://127.0.0.1:5000**

### 🖥️ Chế độ Desktop App
```bash
python desktop.py
```
→ Mở cửa sổ app trực tiếp trên máy tính

---

## 📄 Format file Excel

App tự quét **toàn bộ ô trong tất cả sheet**, tìm ô nào chứa link YouTube.

| Tiêu đề | Link |
|---------|------|
| Học Python | https://youtube.com/watch?v=abc123 |
| React cơ bản | https://youtu.be/xyz456 |

> Link có thể nằm ở bất kỳ cột nào, không cần cấu trúc cố định.

---

## 🛠️ Thư viện sử dụng

| Thư viện | Mục đích |
|----------|----------|
| `flask` | Web server HTTP |
| `openpyxl` | Đọc file Excel (.xlsx) |
| `pywebview` | Bọc web thành Desktop App |

---

## ❓ Lỗi thường gặp

**`ModuleNotFoundError`**  
→ Chưa cài: `pip install -r requirements.txt`

**`venv\Scripts\activate` lỗi trên Windows PowerShell**  
→ Chạy: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**pywebview không mở cửa sổ (Linux)**  
→ Cài thêm: `pip install pywebview[gtk]`
