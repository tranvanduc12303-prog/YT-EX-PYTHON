"""
desktop.py — Đóng gói Flask thành Desktop App bằng pywebview
Chạy: python desktop.py
"""

import threading
import webview
from app import app   # import Flask app


def run_flask():
    """Chạy Flask trong thread riêng (không debug, không reloader)."""
    app.run(port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    # Khởi động Flask ở background thread
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # Mở cửa sổ desktop trỏ vào localhost
    webview.create_window(
        title="YouTube Excel Loader",
        url="http://127.0.0.1:5000",
        width=1100,
        height=750,
        min_size=(800, 600),
        background_color="#0d0d0d",
    )
    webview.start()
