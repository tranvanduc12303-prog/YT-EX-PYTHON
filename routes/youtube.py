import io
import os
import sys
import subprocess
import concurrent.futures
from flask import Blueprint, request, jsonify
import openpyxl
import yt_dlp

from state import ALLOWED_URLS, app_stats, download_state, DownloadCancelled, DOWNLOAD_DIR
from utils import extract_links_from_workbook, yt_progress_hook
from automation.youtube_uploader import upload_video_to_youtube

youtube_bp = Blueprint('youtube', __name__)

@youtube_bp.route("/upload_video", methods=["POST"])
def api_upload_video():
    """
    Automates uploading a video to YouTube using Hidemium + Playwright.
    Expected JSON body:
    {
        "profile_id": "...",
        "video_path": "C:\\path\\to\\video.mp4",
        "title": "Video Title",
        "description": "Video Description"
    }
    """
    data = request.json or {}
    profile_id = data.get("profile_id")
    video_path = data.get("video_path")
    title = data.get("title", "No Title")
    description = data.get("description", "")
    
    if not all([profile_id, video_path]):
        return jsonify({"error": "Missing profile_id or video_path"}), 400
        
    try:
        # We can run this in a separate thread if we don't want to block the Flask route,
        # but for simplicity and returning the immediate result, we run it synchronously.
        result = upload_video_to_youtube(
            profile_id=profile_id, 
            video_path=video_path, 
            title=title, 
            description=description
        )
        if result.get("success"):
            return jsonify({"message": "Upload process completed successfully.", "details": result})
        else:
            return jsonify({"error": result.get("error", "Unknown error occurred.")}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to run upload script: {e}"}), 500

@youtube_bp.route("/upload", methods=["POST"])
def upload():
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
        links = extract_links_from_workbook(wb)
        
        def get_meta(l):
            if not l["valid"]:
                return None
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(l["url"], download=False)
                    
                    channel_name = info.get("uploader") or info.get("channel") or info.get("title") or "Không xác định"
                    channel_url = info.get("uploader_url") or info.get("channel_url")
                    
                    if not channel_url and 'entries' in info:
                        channel_url = l["url"]
                        
                    if channel_url:
                        if not channel_url.startswith("http"):
                            channel_url = f"https://www.youtube.com{channel_url}" if channel_url.startswith("/") else f"https://www.youtube.com/{channel_url}"
                        return {
                            "channel": channel_name,
                            "url": channel_url
                        }
                    return None
            except Exception as e:
                print(f"Error extracting {l['url']}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            meta_results = list(executor.map(get_meta, links))
            
        unique_channels = {}
        channel_counts = {}
        for m in meta_results:
            if m and m["url"]:
                unique_channels[m["url"]] = m["channel"]
                channel_counts[m["channel"]] = channel_counts.get(m["channel"], 0) + 1

        channels_list = [{"channel": v, "url": k} for k, v in unique_channels.items()]
        
        app_stats["yt_total_links"] += len(links)
        app_stats["yt_valid_links"] += len([l for l in links if l["valid"]])
        
        if "yt_channel_stats" not in app_stats:
            app_stats["yt_channel_stats"] = {}
        for ch, count in channel_counts.items():
            app_stats["yt_channel_stats"][ch] = app_stats["yt_channel_stats"].get(ch, 0) + count

        return jsonify({
            "filename": file.filename,
            "sheets": wb.sheetnames,
            "channels": channels_list,
            "total": len(links),
            "total_channels": len(channels_list)
        })
    except Exception as exc:
        return jsonify({"error": f"Lỗi đọc file: {exc}"}), 500


@youtube_bp.route("/download_all", methods=["POST"])
def download_all():
    data = request.json or {}
    urls = data.get("urls", [])
    if not urls:
        return jsonify({"error": "Không có URL nào để tải"}), 400
        
    valid_urls = [u for u in urls if u in ALLOWED_URLS]
    if not valid_urls:
        return jsonify({"error": "Tất cả link đều không hợp lệ hoặc không có trong file Excel!"}), 403

    download_state["stop_requested"] = False
    download_state["is_downloading"] = True

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': 'best',
        'quiet': False,
        'progress_hooks': [yt_progress_hook],
    }

    success_count = 0
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in valid_urls:
                if download_state["stop_requested"]:
                    break
                try:
                    ydl.download([url])
                    success_count += 1
                    app_stats["yt_downloaded"] += 1
                except DownloadCancelled:
                    break
                except Exception as e:
                    print(f"Lỗi tải {url}: {e}")
                    continue
        
        if download_state["stop_requested"]:
            return jsonify({"message": f"Đã dừng tải. Thành công {success_count}/{len(valid_urls)} video!", "folder": DOWNLOAD_DIR})
        return jsonify({"message": f"Tải thành công {success_count}/{len(valid_urls)} video!", "folder": DOWNLOAD_DIR})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        download_state["is_downloading"] = False
        download_state["stop_requested"] = False


@youtube_bp.route("/stop_download", methods=["POST"])
def stop_download():
    if download_state["is_downloading"]:
        download_state["stop_requested"] = True
        return jsonify({"message": "Đang dừng quá trình tải..."})
    return jsonify({"message": "Không có tiến trình tải nào đang chạy."})


@youtube_bp.route("/open_folder", methods=["POST"])
def open_folder():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(DOWNLOAD_DIR)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", DOWNLOAD_DIR])
        else:
            subprocess.Popen(["xdg-open", DOWNLOAD_DIR])
        return jsonify({"message": "Đã mở thư mục tải về"})
    except Exception as e:
        return jsonify({"error": f"Không thể mở thư mục: {e}"}), 500

@youtube_bp.route("/fetch_channel", methods=["POST"])
def fetch_channel():
    data = request.json or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "Vui lòng nhập link Channel hoặc Playlist"}), 400

    # extract_flat=True để lấy danh sách nhanh mà không tải chi tiết từng video
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            videos = []
            
            def extract_entries(entries_list):
                for entry in entries_list:
                    if not entry: continue
                    _type = entry.get('_type')
                    if _type == 'playlist' or 'entries' in entry:
                        tab_url = entry.get('url') or entry.get('webpage_url')
                        if tab_url:
                            try:
                                tab_info = ydl.extract_info(tab_url, download=False)
                                if 'entries' in tab_info:
                                    extract_entries(tab_info['entries'])
                            except:
                                pass
                        elif 'entries' in entry:
                            extract_entries(entry['entries'])
                    elif _type == 'url' or entry.get('url'):
                        v_url = entry.get('url') or entry.get('webpage_url')
                        if v_url:
                            if not v_url.startswith("http"):
                                v_url = f"https://www.youtube.com/watch?v={v_url}"
                            v_type = 'short' if '/shorts/' in v_url else 'video'
                            videos.append({
                                "title": entry.get('title', 'Không có tiêu đề'),
                                "url": v_url,
                                "type": v_type
                            })

            if 'entries' in info:
                extract_entries(info['entries'])
            else:
                v_url = info.get("url") or info.get("webpage_url")
                if v_url:
                    if not v_url.startswith("http"):
                        v_url = f"https://www.youtube.com/watch?v={v_url}"
                    v_type = 'short' if '/shorts/' in v_url else 'video'
                    videos.append({
                        "title": info.get("title", "Không có tiêu đề"),
                        "url": v_url,
                        "type": v_type
                    })
            
            # Thêm vào danh sách cho phép tải
            for v in videos:
                ALLOWED_URLS.add(v["url"])
                
            return jsonify({
                "channel_title": info.get("title", "Channel/Playlist"),
                "videos": videos,
                "total": len(videos)
            })
    except Exception as e:
        return jsonify({"error": f"Lỗi khi quét link: {str(e)}"}), 500
