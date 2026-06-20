import csv
import concurrent.futures
import sys
import os
from playwright.sync_api import sync_playwright

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
CHANNELS = ['@tiktok', '@khaby.lame', '@mrbeast', '@bellapoarch']

# Configure the number of threads running simultaneously.
# Set max_workers to 3-5 to minimize the risk of being rate-limited 
# or temporarily blocked by TikTok's anti-bot protections.
MAX_WORKERS = 3

def scrape_channel(channel_name):
    """
    Scrape the 10 most recent videos from a TikTok channel.
    This function is run independently by each worker thread.
    """
    videos = []
    
    # 1. Initialize Playwright cleanly and independently within each thread.
    # Playwright's sync_playwright context manager is not thread-safe if shared,
    # so instantiating it inside the worker function ensures zero cross-thread pollution.
    try:
        with sync_playwright() as p:
            # Initialize browser. Setting headless=False often helps bypass basic bot detection
            browser = p.chromium.launch(headless=False)
            
            # Configure a user_agent to simulate a real browser request
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            
            # new_context creates a fresh incognito browser context
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            
            print(f"[{channel_name}] Navigating to profile...")
            url = f"https://www.tiktok.com/{channel_name}"
            
            try:
                # Go to the profile. 'domcontentloaded' is faster and less prone to timeout than 'networkidle'
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for TikTok's video feed items to appear on the DOM
                page.wait_for_selector('div[data-e2e="user-post-item"]', timeout=20000)
                page.wait_for_timeout(2000) # Buffer to let dynamic React/Vue elements settle
                
                # Grab all video elements on the loaded page
                video_elements = page.locator('div[data-e2e="user-post-item"]').all()
                print(f"[{channel_name}] Found {len(video_elements)} videos. Extracting top 10...")
                
                # 2. Extract Data (Limit to 10 most recent)
                for i, element in enumerate(video_elements[:10]):
                    try:
                        # Video Link
                        link_locator = element.locator('a').first
                        video_link = link_locator.get_attribute('href')
                        if video_link and not video_link.startswith('http'):
                            video_link = "https://www.tiktok.com" + video_link
                            
                        # Title (usually stashed in the a-tag's title attribute)
                        title = link_locator.get_attribute('title') or f"Video {i+1} (No Title)"
                            
                        # Views
                        views_locator = element.locator('strong[data-e2e="video-views"]')
                        views = views_locator.inner_text() if views_locator.count() > 0 else "N/A"
                        
                        videos.append({
                            "Channel": channel_name,
                            "Title": title,
                            "Video Link": video_link,
                            "Views": views
                        })
                    except Exception as e:
                        # If one video's HTML structure changes, catch it but continue to the next video
                        print(f"[{channel_name}] Warning: Failed to extract a video item: {e}")
            except Exception as e:
                # Take a screenshot if we fail to load the page properly (e.g. Captcha)
                os.makedirs("errors", exist_ok=True)
                error_img = f"errors/{channel_name.replace('@', '')}_error.png"
                page.screenshot(path=error_img)
                print(f"[{channel_name}] ❌ Error during page load/scraping (saved screenshot {error_img}): {e}")
                
            finally:
                browser.close()
            
    except Exception as e:
        # 3. Security/Error Handling: Catching channel/network failures
        # This ensures one blocked channel doesn't crash the main process or other threads.
        print(f"[{channel_name}] ❌ Error scraping channel: {e}")
        
    return videos

def main():
    print(f"Starting scraper with {MAX_WORKERS} concurrent threads...\n")
    all_data = []
    
    # 4. Multithreading Configuration
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Map the channels to the thread worker function
        future_to_channel = {executor.submit(scrape_channel, ch): ch for ch in CHANNELS}
        
        # Process results sequentially as soon as any thread completes
        for future in concurrent.futures.as_completed(future_to_channel):
            channel = future_to_channel[future]
            result = future.result()
            if result:
                all_data.extend(result)
                print(f"✅ [{channel}] Successfully extracted {len(result)} videos.")
                
    # 5. Output: Merge Data & Export
    if all_data:
        with open("tiktok_data.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["Channel", "Title", "Video Link", "Views"])
            writer.writeheader()
            writer.writerows(all_data)
        print("\n🎉 Scraping complete! Data has been successfully exported to 'tiktok_data.csv'.")
    else:
        print("\n⚠️ No data was extracted.")

if __name__ == "__main__":
    main()