import requests
from playwright.sync_api import sync_playwright

class HidemiumManager:
    """
    Helper class to integrate with the Hidemium Local API and connect Playwright.
    """
    def __init__(self, api_url="http://127.0.0.1:8989"): # Replace port with Hidemium's default API port if different
        self.api_url = api_url

    def start_profile(self, profile_id: str):
        """
        Starts a Hidemium profile via its API and retrieves the debugger connection port.
        Note: Adjust the endpoint and response parsing based on Hidemium's actual API docs.
        """
        start_endpoint = f"{self.api_url}/api/v1/profile/start"
        params = {"profileId": profile_id}
        
        try:
            response = requests.get(start_endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Example: assuming Hidemium returns a 'port' or 'ws_url' to connect to
            port = data.get("port") 
            if port:
                return port
            else:
                raise ValueError(f"Could not find debug port in Hidemium response: {data}")
                
        except Exception as e:
            print(f"Error starting Hidemium profile: {e}")
            return None

    def connect_playwright(self, port: int):
        """
        Connects Playwright to the running Hidemium browser via CDP (Chrome DevTools Protocol).
        """
        pw = sync_playwright().start()
        
        # Connect over CDP using the port provided by Hidemium
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        
        # Attach to the existing context and page that Hidemium automatically opened
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()
        
        return pw, browser, context, page
