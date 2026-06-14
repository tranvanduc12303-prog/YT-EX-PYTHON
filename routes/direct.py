import os
from flask import Blueprint, request, jsonify
import yt_dlp

from state import download_state, app_stats, DownloadCancelled, DOWNLOAD_DIR
from utils import is_youtube, yt_progress_hook

direct_bp = Blueprint('direct', __name__)

@direct_bp.route("/api/direct_info", methods=["POST"])
def direct_info():
    data = request.json or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "Vui lòng nhập link!"}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get("title", "Không có tiêu đề")
            thumbnail = info.get("thumbnail", "")
            duration = info.get("duration", 0)
            
            formats_out = []
            
            # Phân loại và cung cấp các lựa chọn tải theo yêu cầu
            if is_youtube(url):
                formats_out = [
                    {"format_id": "bestvideo[height<=1080]+bestaudio/best[height<=1080]", "label": "Video 1080p", "type": "video"},
                    {"format_id": "bestvideo[height<=720]+bestaudio/best[height<=720]", "label": "Video 720p", "type": "video"},
                    {"format_id": "bestvideo[height<=480]+bestaudio/best[height<=480]", "label": "Video 480p", "type": "video"},
                    {"format_id": "bestaudio/best", "label": "Audio Only (MP3)", "type": "audio"}
                ]
            else:
                formats_out = [
                    {"format_id": "best", "label": "Tải Video (Chất lượng tốt nhất)", "type": "video"},
                    {"format_id": "bestaudio/best", "label": "Tải Audio Only", "type": "audio"}
                ]

            return jsonify({
                "title": title,
                "thumbnail": thumbnail,
                "duration": duration,
                "url": url,
                "formats": formats_out,
                "is_youtube": is_youtube(url)
            })
    except Exception as e:
        return jsonify({"error": f"Lỗi lấy thông tin: {str(e)}"}), 500


@direct_bp.route("/api/direct_download", methods=["POST"])
def direct_download():
    data = request.json or {}
    url = data.get("url")
    format_id = data.get("format_id")
    is_audio = data.get("type") == "audio"
    
    if not url or not format_id:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    download_state["stop_requested"] = False
    download_state["is_downloading"] = True

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': format_id,
        'quiet': False,
        'progress_hooks': [yt_progress_hook],
    }
    
    # Định dạng âm thanh thì cần FFmpeg
    if is_audio:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            app_stats["yt_downloaded"] += 1
            
        if download_state["stop_requested"]:
            return jsonify({"message": f"Đã dừng tải!", "folder": DOWNLOAD_DIR})
        return jsonify({"message": f"Tải thành công!", "folder": DOWNLOAD_DIR})
    except DownloadCancelled:
        return jsonify({"message": "Đã dừng tải", "folder": DOWNLOAD_DIR})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        download_state["is_downloading"] = False
        download_state["stop_requested"] = False
