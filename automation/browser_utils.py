import random
import time
from playwright.sync_api import Page

def random_wait(min_sec: float = 1.5, max_sec: float = 4.0):
    """
    Random timeout: Custom wait function to randomize the timeout 
    using random.uniform() instead of a fixed time.sleep().
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def realistic_type(page: Page, selector: str, text: str, min_delay_ms: int = 80, max_delay_ms: int = 250):
    """
    Realistic typing: Types text character by character with a random delay per keystroke.
    Also occasionally pauses for a short time to mimic human thought/reading.
    """
    element = page.locator(selector)
    element.focus()
    
    for char in text:
        element.press_sequentially(char, delay=0)
        
        # 5% chance to "pause and think" for up to 1.5s
        if random.random() < 0.05:
            time.sleep(random.uniform(0.5, 1.5))
            
        delay_sec = random.uniform(min_delay_ms / 1000.0, max_delay_ms / 1000.0)
        time.sleep(delay_sec)

def human_scroll(page: Page, scrolls: int = 3, min_px: int = 300, max_px: int = 600):
    """
    Human-like scrolling: Scrolls down the page one step at a time with variable amounts, 
    including a 20% chance of scrolling up slightly to mimic human reading behavior.
    """
    for _ in range(scrolls):
        if random.random() < 0.20:
            scroll_up_amount = random.randint(100, 300)
            page.mouse.wheel(0, -scroll_up_amount)
            random_wait(0.5, 1.5)
        else:
            scroll_down_amount = random.randint(min_px, max_px)
            page.mouse.wheel(0, scroll_down_amount)
            random_wait(0.8, 2.5)

def safe_click(page: Page, selector: str):
    """
    Safe interaction: Moves the mouse to a randomized coordinate inside the element's bounding box 
    using multiple steps to simulate human mouse movement, then pauses, then clicks.
    """
    element = page.locator(selector).first
    element.wait_for(state="visible")
    
    box = element.bounding_box()
    if box and box["width"] > 10 and box["height"] > 10:
        # Move to a random coordinate inside the element
        target_x = box["x"] + random.uniform(5, box["width"] - 5)
        target_y = box["y"] + random.uniform(5, box["height"] - 5)
        
        # Simulate human mouse movement with steps
        page.mouse.move(target_x, target_y, steps=random.randint(5, 15))
    else:
        # Fallback if bounding box is not valid or element is too small
        element.hover()
    
    # Small pause to simulate human hesitation/reading before clicking
    random_wait(0.3, 1.2)
    
    element.click()
