import os
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from automation.hidemium_manager import HidemiumManager
from automation.browser_utils import realistic_type, safe_click, random_wait, human_scroll

def upload_video_to_youtube(profile_id: str, video_path: str, title: str, description: str) -> dict:
    if not os.path.exists(video_path):
        return {"success": False, "error": f"Video file not found at {video_path}"}
        
    manager = HidemiumManager()
    
    print(f"[*] Opening Hidemium profile: {profile_id}")
    connection_details = manager.start_profile(profile_id)
    
    if not connection_details or "ws_endpoint" not in connection_details:
        return {"success": False, "error": "Failed to get CDP connection endpoint from Hidemium API."}
        
    ws_endpoint = connection_details["ws_endpoint"]
    print(f"[*] Successfully started. Connecting on CDP endpoint: {ws_endpoint}")
    
    pw, browser, context, page = None, None, None, None
    try:
        pw, browser, context, page = manager.connect_playwright(ws_endpoint)
        
        # Navigate to YouTube Studio
        print("[*] Navigating to YouTube Studio...")
        page.goto("https://studio.youtube.com", timeout=60000)
        page.wait_for_load_state("networkidle")
        
        # Click the "Create" button
        print("[*] Clicking 'Create' and 'Upload video'...")
        page.wait_for_selector('#create-icon', timeout=15000)
        safe_click(page, '#create-icon')
        
        # Click "Upload videos"
        page.wait_for_selector('tp-yt-paper-item#text-item-0', timeout=10000)
        random_wait(0.5, 1.5)
        safe_click(page, 'tp-yt-paper-item#text-item-0')
        
        # Select video file
        print("[*] Waiting for file chooser...")
        page.wait_for_selector('input[type="file"]', timeout=10000)
        
        print(f"[*] Uploading file: {video_path}")
        page.set_input_files('input[type="file"]', video_path)
        
        # Wait for the upload form to appear
        print("[*] Waiting for upload form to load...")
        page.wait_for_selector('#title-textarea', timeout=30000)
        
        # Fill Title
        print("[*] Filling title...")
        page.wait_for_selector('#title-textarea #textbox', timeout=10000)
        page.fill('#title-textarea #textbox', '') # clear
        random_wait(0.5, 1.5)
        realistic_type(page, '#title-textarea #textbox', title)
        
        # Fill Description
        print("[*] Filling description...")
        page.wait_for_selector('#description-textarea #textbox', timeout=10000)
        page.fill('#description-textarea #textbox', '')
        random_wait(0.5, 1.5)
        realistic_type(page, '#description-textarea #textbox', description)
        
        # Select "No, it's not made for kids" (Mandatory)
        print("[*] Setting Audience: Not made for kids...")
        human_scroll(page, scrolls=2, min_px=150, max_px=300)
        page.wait_for_selector('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]', timeout=10000)
        safe_click(page, 'tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]')

        # Proceed through steps
        print("[*] Proceeding through steps...")
        # Step 1 -> Step 2 (Video elements)
        page.wait_for_selector('#next-button', timeout=10000)
        safe_click(page, '#next-button')
        random_wait(1.5, 3.0)
        
        # Step 2 -> Step 3 (Checks)
        page.wait_for_selector('#next-button', timeout=10000)
        safe_click(page, '#next-button')
        random_wait(1.5, 3.0)

        # Step 3 -> Step 4 (Visibility)
        page.wait_for_selector('#next-button', timeout=10000)
        safe_click(page, '#next-button')
        random_wait(1.5, 3.0)

        # In Visibility step (Display mode)
        print("[*] Setting visibility to Public...")
        page.wait_for_selector('tp-yt-paper-radio-button[name="PUBLIC"]', timeout=10000)
        safe_click(page, 'tp-yt-paper-radio-button[name="PUBLIC"]')
        random_wait(1.0, 2.0)
        
        # Publish button
        print("[*] Clicking Publish...")
        page.wait_for_selector('#done-button', timeout=10000)
        safe_click(page, '#done-button')
        
        # Wait for the "Video published" dialog to confirm
        print("[*] Waiting for publish confirmation...")
        try:
            # The dialog box for successful publish is ytcp-video-share-dialog or ytcp-uploads-dialog
            page.wait_for_selector('ytcp-video-share-dialog', timeout=60000)
            print("[*] Video published successfully!")
            video_published = True
        except PlaywrightTimeoutError:
            print("[!] Could not confirm publish dialog, it might still be uploading/processing.")
            # It's better to wait until upload is 100% or just return
            video_published = False
            
        return {"success": True, "published": video_published, "message": "Video uploaded successfully."}

    except Exception as e:
        print(f"[!] Error during YouTube upload: {e}")
        return {"success": False, "error": str(e)}
        
    finally:
        if browser:
            try:
                browser.disconnect()
            except Exception:
                pass
        if pw:
            try:
                pw.stop()
            except Exception:
                pass
                
        # Close Profile gracefully via API
        print(f"[*] Closing Hidemium profile: {profile_id}")
        manager.stop_profile(profile_id)
