import os
import threading
from flask import Blueprint, request, jsonify, send_file

from state import email_task_state, DOWNLOAD_DIR
from utils import process_email_thread_func

email_bp = Blueprint('email', __name__)

@email_bp.route("/upload_email_file", methods=["POST"])
def upload_email_file():
    if "file" not in request.files:
        return jsonify({"error": "Không có file được gửi lên"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Tên file trống"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xlsm"):
        return jsonify({"error": f"Định dạng .{ext} không hỗ trợ. Dùng .xlsx"}), 400
        
    source_col = int(request.form.get("source_col", 1))
    target_col = int(request.form.get("target_col", 2))

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    input_path = os.path.join(DOWNLOAD_DIR, "temp_email_input.xlsx")
    output_path = os.path.join(DOWNLOAD_DIR, f"{file.filename.rsplit('.', 1)[0]}_emails.xlsx")
    
    file.save(input_path)

    if email_task_state["status"] == "running":
        return jsonify({"error": "Một tiến trình khác đang chạy"}), 400

    # Khởi chạy thread
    thread = threading.Thread(target=process_email_thread_func, args=(input_path, output_path, source_col, target_col))
    thread.start()

    return jsonify({"message": "Đã bắt đầu xử lý email", "filename": file.filename})

@email_bp.route("/stop_email_process", methods=["POST"])
def stop_email_process():
    if email_task_state["status"] == "running":
        email_task_state["status"] = "stopped"
        return jsonify({"message": "Đang dừng quá trình xử lý..."})
    return jsonify({"message": "Không có tiến trình nào đang chạy."})

@email_bp.route("/email_progress", methods=["GET"])
def email_progress():
    return jsonify(email_task_state)
    
@email_bp.route("/download_email_result", methods=["GET"])
def download_email_result():
    file_path = email_task_state.get("output_file")
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File không tồn tại"}), 404
