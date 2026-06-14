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
    """
    element = page.locator(selector)
    element.focus()
    
    # We loop through manually to have strict control over randomizing each keystroke delay
    for char in text:
        # Type a single character instantly
        element.type(char, delay=0)
        
        # Apply the random delay between keystrokes
        delay_sec = random.uniform(min_delay_ms / 1000.0, max_delay_ms / 1000.0)
        time.sleep(delay_sec)

def human_scroll(page: Page, scrolls: int = 3, min_px: int = 300, max_px: int = 600):
    """
    Human-like scrolling: Scrolls down the page one step at a time with variable amounts, 
    including a 20% chance of scrolling up slightly to mimic human reading behavior.
    """
    for _ in range(scrolls):
        # 20% chance to scroll up instead of down
        if random.random() < 0.20:
            # Scroll up slightly (usually a smaller amount than a full down scroll)
            scroll_up_amount = random.randint(100, 300)
            page.mouse.wheel(0, -scroll_up_amount)
            random_wait(0.5, 1.5)
        else:
            # Normal scroll down
            scroll_down_amount = random.randint(min_px, max_px)
            page.mouse.wheel(0, scroll_down_amount)
            random_wait(0.8, 2.5)

def safe_click(page: Page, selector: str):
    """
    Safe interaction: Uses hover() to simulate cursor movement before clicking.
    """
    element = page.locator(selector)
    
    # Wait for the element to be in the DOM and visible
    element.wait_for(state="visible")
    
    # Hover over the element to trigger any CSS hover states or lazy-loaded listeners
    element.hover()
    
    # Small pause to simulate human hesitation/reading before clicking
    random_wait(0.3, 1.2)
    
    # Perform the actual click
    element.click()
