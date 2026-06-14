import os
from automation.browser_utils import random_wait, realistic_type, human_scroll, safe_click
from automation.hidemium_manager import HidemiumManager

def upload_video_workflow(profile_id: str, video_path: str, title: str, description: str):
    """
    Example workflow combining the Hidemium anti-detect browser and human-like utilities 
    to upload a video to TikTok (or similar platform).
    """
    hidemium = HidemiumManager()
    
    print(f"Starting Hidemium profile {profile_id}...")
    port = hidemium.start_profile(profile_id)
    if not port:
        print("Failed to start browser. Exiting.")
        return

    print("Connecting Playwright to the browser...")
    pw, browser, context, page = hidemium.connect_playwright(port)
    
    try:
        # 1. Navigate to the upload page
        page.goto("https://www.tiktok.com/upload", timeout=60000)
        random_wait(3.0, 5.0)
        
        # 2. Simulate human scrolling on the page before interacting
        print("Simulating human scroll...")
        human_scroll(page, scrolls=2)
        
        # 3. Handle File Upload (Note: This is a direct file chooser interaction, 
        # usually safer than trying to click the OS file dialog)
        print("Uploading file...")
        # TikTok's file input is typically hidden, so we listen for the filechooser event
        with page.expect_file_chooser() as fc_info:
            # We use safe_click to hover and click the upload button
            safe_click(page, "button:has-text('Select file')") # Adjust selector as needed
        
        file_chooser = fc_info.value
        file_chooser.set_files(os.path.abspath(video_path))
        
        random_wait(5.0, 8.0) # Wait for initial processing/uploading
        
        # 4. Realistic typing for the Caption/Title
        print("Typing description...")
        caption_selector = "div[contenteditable='true']" # Adjust selector as needed
        safe_click(page, caption_selector)
        
        # Clear existing text safely
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        random_wait(0.5, 1.0)
        
        realistic_type(page, caption_selector, f"{title} - {description}")
        
        # 5. Final scrolling and submission
        human_scroll(page, scrolls=1)
        random_wait(1.5, 3.0)
        
        print("Clicking Post...")
        safe_click(page, "button:has-text('Post')") # Adjust selector as needed
        
        # Wait for the success confirmation
        random_wait(8.0, 12.0)
        print("Upload workflow completed successfully.")
        
    except Exception as e:
        print(f"An error occurred during automation: {e}")
        
    finally:
        # Cleanup
        print("Closing Playwright connection...")
        browser.close()
        pw.stop()

if __name__ == "__main__":
    # Example usage:
    # upload_video_workflow("YOUR_HIDEMIUM_PROFILE_ID", "./downloads/video.mp4", "My Awesome Video", "#trending #viral")
    pass
