import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

class DownloadCancelled(Exception):
    pass

download_state = {
    "stop_requested": False,
    "is_downloading": False
}
ALLOWED_URLS = set()

email_task_state = {
    "status": "idle", # idle, running, stopped, completed, error
    "progress": 0,
    "total_rows": 0,
    "processed_rows": 0,
    "emails_found": 0,
    "output_file": "",
    "error_msg": "",
    "sheet_stats": {} # Để vẽ chart: {"Sheet1": 10, "Sheet2": 5}
}

app_stats = {
    "yt_total_links": 0,
    "yt_valid_links": 0,
    "yt_downloaded": 0,
    "email_extracted_total": 0,
}
