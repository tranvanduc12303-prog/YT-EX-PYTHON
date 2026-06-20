from flask import Blueprint, render_template, jsonify, request
from state import app_stats, email_task_state
import subprocess
import threading
import sys
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

common_bp = Blueprint('common', __name__)

@common_bp.route("/")
def index():
    return render_template("index.html")

@common_bp.route("/stats", methods=["GET"])
def get_stats():
    return jsonify({
        "app_stats": app_stats,
        "email_sheet_stats": email_task_state.get("sheet_stats", {})
    })

@common_bp.route("/run_gmail_creator", methods=["POST"])
def run_gmail_creator():
    def run_script():
        try:
            # Chạy file gmail_creator.py bằng Python trong môi trường ảo hiện tại
            # Dùng sys.executable để đảm bảo dùng đúng python (venv)
            subprocess.run([sys.executable, "gmail_creator.py"], check=True)
        except Exception as e:
            print(f"Lỗi khi chạy script tạo gmail: {e}")

    # Chạy script trong một luồng nền để không chặn phản hồi của web UI
    thread = threading.Thread(target=run_script, daemon=True)
    thread.start()
    
    return jsonify({"message": "Đã bắt đầu chạy kịch bản tạo Gmail."})

@common_bp.route("/launch_hidemium", methods=["POST"])
def launch_hidemium():
    data = request.json or {}
    profile_id = data.get("profile_id")
    url = data.get("url")

    if not profile_id or not url:
        return jsonify({"error": "Thiếu profile_id hoặc url"}), 400

    def open_browser():
        try:
            from automation.hidemium_manager import HidemiumManager
            manager = HidemiumManager()
            conn = manager.start_profile(profile_id)
            if conn and "ws_endpoint" in conn:
                pw, browser, context, page = manager.connect_playwright(conn["ws_endpoint"])
                print(f"[*] Navigating to {url} on Profile {profile_id}")
                page.goto(url)
                # We intentionally don't close the browser so the user can see it
            else:
                print("[-] Không thể khởi động profile Hidemium.")
        except Exception as e:
            print(f"[-] Lỗi khi mở browser: {e}")

    thread = threading.Thread(target=open_browser, daemon=True)
    thread.start()

    return jsonify({"message": "Đã gửi lệnh mở trình duyệt."})

def worker_launch(row_data):
    profile_id = row_data.get("profile_id")
    url = row_data.get("url")
    if not profile_id or str(profile_id).lower() == "nan":
        return
        
    try:
        from automation.hidemium_manager import HidemiumManager
        manager = HidemiumManager()
        conn = manager.start_profile(profile_id)
        if conn and "ws_endpoint" in conn:
            pw, browser, context, page = manager.connect_playwright(conn["ws_endpoint"])
            if url and str(url).lower() != "nan":
                print(f"[*] Batch Navigating to {url} on Profile {profile_id}")
                page.goto(url)
            else:
                print(f"[*] Successfully launched Profile {profile_id}")
            # We intentionally don't close the browser so the user can see it
        else:
            print(f"[-] Không thể khởi động profile Hidemium {profile_id}.")
    except Exception as e:
        print(f"[-] Lỗi khi mở browser batch ({profile_id}): {e}")

@common_bp.route("/launch_hidemium_batch", methods=["POST"])
def launch_hidemium_batch():
    if 'file' not in request.files:
        return jsonify({"error": "Không tìm thấy file tải lên"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Chưa chọn file"}), 400

    try:
        df = pd.read_excel(file)
        
        # Tìm cột Profile ID
        profile_col = None
        for c in df.columns:
            col_lower = str(c).lower()
            if "profile" in col_lower or "id" in col_lower or "uuid" in col_lower:
                profile_col = c
                break
        if not profile_col and len(df.columns) > 0:
            profile_col = df.columns[0]
            
        # Tìm cột URL (Tùy chọn)
        url_col = None
        for c in df.columns:
            if "url" in str(c).lower() or "link" in str(c).lower():
                url_col = c
                break
            
        if not profile_col:
            return jsonify({"error": "Không thể xác định cột Profile ID trong file Excel."}), 400

        tasks = []
        for index, row in df.iterrows():
            profile_id = str(row[profile_col]).strip()
            url = str(row[url_col]).strip() if url_col else None
            tasks.append({
                "profile_id": profile_id,
                "url": url
            })
            
        def run_batch():
            print(f"=== Bắt đầu chạy Batch Hidemium với {len(tasks)} luồng ===")
            with ThreadPoolExecutor(max_workers=5, thread_name_prefix="BatchWorker") as executor:
                executor.map(worker_launch, tasks)
            print("=== Hoàn thành chạy Batch Hidemium ===")
                
        threading.Thread(target=run_batch, daemon=True).start()
        
        return jsonify({"message": f"Đã bắt đầu chạy batch {len(tasks)} profiles."})
        
    except Exception as e:
        return jsonify({"error": f"Lỗi xử lý file Excel: {str(e)}"}), 500
