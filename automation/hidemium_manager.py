import requests
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:2222"

class HidemiumManager:
    """
    Helper class to integrate with the Hidemium API and connect Playwright.
    """
    def __init__(self, api_url=BASE_URL): 
        self.api_url = api_url

    def start_profile(self, profile_id: str):
        """
        Starts a Hidemium profile via its API and retrieves the CDP/WebSocket connection details.
        Endpoint: http://localhost:2222/openProfile?uuid={profile_id}
        """
        # API URL as requested by user (fixed to the correct one)
        start_endpoint = f"{self.api_url}/openProfile?uuid={profile_id}"
        
        try:
            print(f"[*] Đang gọi API Hidemium: {start_endpoint}")
            response = requests.get(start_endpoint)
            response.raise_for_status()
            data = response.json()
            
            # In ra toàn bộ response từ Hidemium để dễ debug lỗi "không kết nối được"
            print(f"[*] Response từ Hidemium API ({profile_id}): {data}")
            
            ws_endpoint = None
            
            # Parse response from Hidemium v4/v5 API
            if "data" in data and isinstance(data["data"], dict):
                ws_endpoint = data["data"].get("web_socket")
                port = data["data"].get("remote_port") or data["data"].get("port")
                
            # Fallback nếu api không trả về web_socket trực tiếp nhưng có port
            if not ws_endpoint and port:
                ws_endpoint = f"ws://127.0.0.1:{port}/devtools/browser"
                
            if not ws_endpoint:
                print(f"[-] Không tìm thấy thông tin cổng kết nối CDP hoặc WebSocket URL trong response: {data}")
                return None
                
            return {
                "ws_endpoint": ws_endpoint,
                "profile_id": profile_id
            }
            
        except requests.exceptions.ConnectionError:
            print(f"[-] Lỗi KẾT NỐI API: Không thể kết nối tới {self.api_url}. Hãy chắc chắn rằng app Hidemium đang mở và API được cấu hình chạy ở port 2222.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[-] Lỗi khi gọi API khởi động Hidemium profile: {e}")
            return None
        except Exception as e:
            print(f"[-] Lỗi khi xử lý phản hồi từ Hidemium: {e}")
            return None

    def stop_profile(self, profile_id: str):
        """
        Closes a running Hidemium profile via its API.
        Endpoint: http://localhost:2222/closeProfile?uuid={profile_id}
        """
        stop_endpoint = f"{self.api_url}/closeProfile?uuid={profile_id}"
        
        try:
            response = requests.get(stop_endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[-] Lỗi khi gọi API đóng Hidemium profile: {e}")
            return None

    def get_schedules(self):
        """
        Retrieves the list of automation schedules.
        Endpoint: GET http://localhost:2222/automation/schedule
        """
        endpoint = f"{self.api_url}/automation/schedule"
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[-] Lỗi khi gọi API lấy danh sách schedule: {e}")
            return None

    def create_schedule(self, payload: dict):
        """
        Creates a new automation schedule.
        Endpoint: POST http://localhost:2222/automation/schedule
        """
        endpoint = f"{self.api_url}/automation/schedule"
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[-] Lỗi khi gọi API tạo schedule: {e}")
            return None

    def connect_playwright(self, ws_endpoint: str):
        """
        Connects Playwright to the running Hidemium browser via CDP (Chrome DevTools Protocol).
        """
        pw = sync_playwright().start()
        
        # Connect over CDP using the endpoint provided by Hidemium
        browser = pw.chromium.connect_over_cdp(ws_endpoint)
        
        # Attach to the existing context and page that Hidemium automatically opened
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()
        
        return pw, browser, context, page
