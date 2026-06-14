import io
import concurrent.futures
from flask import Blueprint, request, jsonify
import openpyxl
import yt_dlp

from state import ALLOWED_URLS
from utils import extract_tiktok_links_from_workbook

tiktok_bp = Blueprint('tiktok', __name__)

@tiktok_bp.route("/upload_tiktok", methods=["POST"])
def upload_tiktok():
    if "file" not in request.files:
        return jsonify({"error": "Không có file được gửi lên"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Tên file trống"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xlsm", "xltx", "xltm"):
        return jsonify({"error": f"Định dạng .{ext} không hỗ trợ. Dùng .xlsx"}), 400

    try:
        data = file.read()
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        links = extract_tiktok_links_from_workbook(wb)
        
        def get_meta(l):
            if not l["valid"]:
                return None
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(l["url"], download=False)
                    
                    channel_name = info.get('uploader') or info.get('title') or "Không xác định"
                    channel_url = info.get('uploader_url') or l["url"]
                    
                    if channel_url:
                        return {
                            "channel": channel_name,
                            "url": channel_url
                        }
                    return None
            except Exception as e:
                print(f"Error extracting TikTok {l['url']}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            meta_results = list(executor.map(get_meta, links))
            
        unique_channels = {}
        for m in meta_results:
            if m and m["url"]:
                unique_channels[m["url"]] = m["channel"]
                ALLOWED_URLS.add(m["url"]) # Allow downloading from this channel URL

        channels_list = [{"channel": v, "url": k} for k, v in unique_channels.items()]

        return jsonify({
            "filename": file.filename,
            "sheets": wb.sheetnames,
            "channels": channels_list,
            "total": len(links),
            "total_channels": len(channels_list)
        })
    except Exception as exc:
        return jsonify({"error": f"Lỗi xử lý file: {exc}"}), 500
