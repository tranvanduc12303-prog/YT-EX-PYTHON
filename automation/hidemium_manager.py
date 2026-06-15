import requests
from playwright.sync_api import sync_playwright

class HidemiumManager:
    """
    Helper class to integrate with the Hidemium V4 Local API and connect Playwright.
    """
    def __init__(self, api_url="http://127.0.0.1:2222"): 
        self.api_url = api_url

    def open_hidemium_profile(self, profile_id: str):
        """
        Starts a Hidemium profile via its V4 API and retrieves the CDP/WebSocket connection details.
        Usually passes the profile's `id` parameter.
        """
        start_endpoint = f"{self.api_url}/api/v4/profile/start"
        params = {"id": profile_id}
        
        try:
            response = requests.get(start_endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract WebSocket endpoint or debug port from Hidemium's JSON response
            # Note: The exact JSON structure depends on Hidemium's actual response. 
            # We attempt standard locations for antidetect browsers.
            ws_endpoint = None
            
            if "data" in data and isinstance(data["data"], dict):
                ws_data = data["data"].get("ws", {})
                if isinstance(ws_data, dict):
                    ws_endpoint = ws_data.get("playwright") or ws_data.get("puppeteer")
                else:
                    ws_endpoint = data["data"].get("ws_endpoint") or data["data"].get("wsEndpoint")
                    
            if not ws_endpoint:
                ws_endpoint = data.get("wsEndpoint") or data.get("ws_endpoint")
                
            port = data.get("port") or (data.get("data", {}).get("port"))

            if ws_endpoint:
                return {"ws_endpoint": ws_endpoint, "port": port}
            elif port:
                # If only port is provided, Playwright can connect to http://127.0.0.1:<port>
                return {"ws_endpoint": f"http://127.0.0.1:{port}", "port": port}
            else:
                # Fallback to returning the raw response data if we couldn't parse the exact keys
                return data
                
        except requests.exceptions.RequestException as e:
            print(f"Error starting Hidemium profile (API Call failed): {e}")
            return None
        except Exception as e:
            print(f"Error parsing Hidemium response: {e}")
            return None

    def close_hidemium_profile(self, profile_id: str):
        """
        Closes a running Hidemium profile via its V4 Local API.
        """
        stop_endpoint = f"{self.api_url}/api/v4/profile/stop"
        # Sometimes close endpoints use /api/v4/profile/close or /stop. 
        # Adapt if Hidemium's docs specify 'close' instead of 'stop'.
        params = {"id": profile_id}
        
        try:
            response = requests.get(stop_endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error closing Hidemium profile: {e}")
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
