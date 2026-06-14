"""
app.py — Flask server chính
Chạy web:     python app.py
Chạy desktop: python desktop.py
"""

import logging
from flask import Flask

from routes.tiktok import tiktok_bp
from routes.youtube import youtube_bp
from routes.direct import direct_bp
from routes.email import email_bp
from routes.common import common_bp

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB

# Tắt cảnh báo "development server" và các log mặc định của Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Register Blueprints
app.register_blueprint(tiktok_bp)
app.register_blueprint(youtube_bp)
app.register_blueprint(direct_bp)
app.register_blueprint(email_bp)
app.register_blueprint(common_bp)

if __name__ == "__main__":
    print("🌐  Web đang chạy tại: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
