import asyncio
import sys
import pandas as pd
from playwright.async_api import async_playwright, Playwright

# Fix lỗi in tiếng Việt trên console Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# ==============================================================
# CẤU HÌNH BIẾN (Dễ dàng thay đổi)
# ==============================================================
EXCEL_FILE = "data.xlsx"
LOGIN_URL = "https://example.com/login" # Thay bằng URL đăng nhập thực tế của bạn

# Thay bằng HTML/CSS selector tương ứng trên website
SELECTOR_EMAIL = "input[name='email']"         # Selector cho ô Email
SELECTOR_PASSWORD = "input[name='password']"   # Selector cho ô Password
SELECTOR_LOGIN_BTN = "button[type='submit']"   # Selector cho nút Đăng nhập

# Giới hạn số lượng trình duyệt mở cùng lúc
MAX_CONCURRENT_BROWSERS = 2

async def login_task(p: Playwright, email: str, password: str, sem: asyncio.Semaphore):
    """Hàm xử lý đăng nhập cho từng tài khoản"""
    # Semaphore đảm bảo chỉ có tối đa MAX_CONCURRENT_BROWSERS chạy qua block này cùng lúc
    async with sem:
        print(f"[{email}] Bắt đầu chạy...")
        
        # Khởi tạo trình duyệt Chrome bình thường (hiển thị UI)
        # channel="chrome" dùng Chrome có sẵn trên máy. Nếu máy chưa có, có thể xoá tham số này để dùng Chromium mặc định.
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"[{email}] Đang truy cập trang web...")
            await page.goto(LOGIN_URL)
            
            # Đợi trang tải xong ổn định
            await page.wait_for_load_state("networkidle")
            
            # Tìm và điền Email
            print(f"[{email}] Điền email...")
            await page.wait_for_selector(SELECTOR_EMAIL)
            await page.fill(SELECTOR_EMAIL, email)
            
            # Tìm và điền Password
            print(f"[{email}] Điền mật khẩu...")
            await page.wait_for_selector(SELECTOR_PASSWORD)
            await page.fill(SELECTOR_PASSWORD, password)
            
            # Click nút đăng nhập
            print(f"[{email}] Click đăng nhập...")
            await page.wait_for_selector(SELECTOR_LOGIN_BTN)
            await page.click(SELECTOR_LOGIN_BTN)
            
            # Đợi 5 giây sau khi click để kiểm tra kết quả
            print(f"[{email}] Đang chờ 5s để kiểm tra kết quả đăng nhập...")
            await asyncio.sleep(5)
            
            print(f"[{email}] Đã hoàn thành tác vụ!")
            
        except Exception as e:
            print(f"[{email}] Lỗi xảy ra: {str(e)}")
        finally:
            print(f"[{email}] Đóng trình duyệt.")
            await browser.close()

async def main():
    print(f"Đang đọc dữ liệu từ {EXCEL_FILE}...")
    try:
        # Đọc dữ liệu từ Excel bằng Pandas (yêu cầu cài đặt thư viện 'openpyxl')
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{EXCEL_FILE}'. Vui lòng tạo file này cùng thư mục với script.")
        return
    except Exception as e:
        print(f"Lỗi đọc Excel: {e}")
        return
        
    # Kiểm tra tính hợp lệ của file Excel
    if "Email" not in df.columns or "Password" not in df.columns:
        print("Lỗi: File Excel bắt buộc phải có 2 cột tên là 'Email' và 'Password'.")
        return

    # Lọc bỏ các dòng bị trống (NaN)
    df = df.dropna(subset=['Email', 'Password'])
    accounts = df.to_dict('records')
    
    total_acc = len(accounts)
    print(f"Tìm thấy {total_acc} tài khoản. Sẽ chạy tối đa {MAX_CONCURRENT_BROWSERS} trình duyệt cùng lúc.")
    
    if total_acc == 0:
        return

    # Sử dụng Semaphore để giới hạn luồng chạy song song
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSERS)
    
    # Khởi tạo Playwright
    async with async_playwright() as p:
        tasks = []
        for acc in accounts:
            email = str(acc['Email']).strip()
            password = str(acc['Password']).strip()
            
            # Bỏ qua nếu dữ liệu trống sau khi loại bỏ khoảng trắng
            if not email or not password:
                continue
                
            # Tạo task bất đồng bộ cho mỗi tài khoản
            task = asyncio.create_task(login_task(p, email, password, semaphore))
            tasks.append(task)
            
        # Chờ tất cả các task hoàn tất
        await asyncio.gather(*tasks)
        
    print("\nToàn bộ tiến trình đã hoàn thành!")

if __name__ == "__main__":
    asyncio.run(main())
