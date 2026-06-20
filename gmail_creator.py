import threading
import random
import string
import time
import os
from concurrent.futures import ThreadPoolExecutor
from faker import Faker
from automation.hidemium_manager import HidemiumManager
from automation.browser_utils import realistic_type, safe_click, random_wait

file_lock = threading.Lock()

def generate_random_profile():
    """
    Tạo thông tin cá nhân ngẫu nhiên: Họ, Tên, Ngày tháng năm sinh, Giới tính, Username, Password.
    Sử dụng Faker để tạo dữ liệu chuẩn quốc tế.
    """
    fake = Faker('en_US')
    first_name = fake.first_name()
    last_name = fake.last_name()
    
    # Random ngày tháng năm sinh (đảm bảo trên 18 tuổi)
    dob = fake.date_of_birth(minimum_age=18, maximum_age=65)
    day = str(dob.day)
    month = str(dob.month)
    year = str(dob.year)
    
    # 1: Nữ, 2: Nam
    gender_value = random.choice(["1", "2"]) 

    # Username: [Real Name] + [Last Name] + [Chuỗi ngẫu nhiên 4-7 ký tự]
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(4, 7)))
    username = f"{first_name.lower()}{last_name.lower()}{random_suffix}"

    # Password: 10-14 ký tự (chữ hoa, chữ thường, số, ký tự đặc biệt)
    length = random.randint(10, 14)
    password = fake.password(length=length, special_chars=True, digits=True, upper_case=True, lower_case=True)
    
    # Đảm bảo có đủ các loại ký tự trong password
    if not any(c.isupper() for c in password): password += random.choice(string.ascii_uppercase)
    if not any(c.islower() for c in password): password += random.choice(string.ascii_lowercase)
    if not any(c.isdigit() for c in password): password += random.choice(string.digits)
    if not any(c in string.punctuation for c in password): password += random.choice("!@#$%^&*")

    return {
        "first_name": first_name,
        "last_name": last_name,
        "day": day,
        "month": month,
        "year": year,
        "gender_value": gender_value,
        "username": username,
        "password": password
    }


def save_account_success(username, password):
    with file_lock:
        with open("success_accounts.txt", "a", encoding="utf-8") as file:
            file.write(f"{username}|{password}\n")
        print(f"[+] LUỒNG {threading.current_thread().name} - Đã lưu thành công: {username}")


def click_next_button(page):
    """Mô phỏng thời gian suy nghĩ từ 1.5s đến 3.0s trước khi click nút Next."""
    random_wait(1.5, 3.0)
    safe_click(page, 'button:has-text("Next"), button:has-text("Tiếp theo")')
    random_wait(2.5, 4.0)


def check_bot_error(page, profile_id):
    """Kiểm tra nếu trang hiển thị 'An error occurred' hoặc 'unknownerror'."""
    try:
        url = page.url.lower()
        content = page.content().lower()
        if "unknownerror" in url or "an error occurred" in content or "đã xảy ra lỗi" in content:
            os.makedirs("errors", exist_ok=True)
            screenshot_path = f"errors/error_{profile_id}_{int(time.time())}.png"
            page.screenshot(path=screenshot_path)
            raise Exception(f"Phát hiện lỗi Google (bot check). Đã lưu ảnh {screenshot_path}")
    except Exception as e:
        if "Phát hiện lỗi Google" in str(e):
            raise e


def create_gmail_profile(profile_id):
    """Kết nối Hidemium và thực hiện toàn bộ luồng đăng ký."""
    profile = generate_random_profile()
    thread_name = threading.current_thread().name
    print(f"[*] {thread_name} - Khởi động Hidemium profile {profile_id} để tạo {profile['username']}")

    manager = HidemiumManager()
    
    connection_info = manager.start_profile(profile_id)
    if not connection_info or "ws_endpoint" not in connection_info:
        print(f"[-] {thread_name} - Không thể mở profile Hidemium: {profile_id}")
        return

    ws_endpoint = connection_info["ws_endpoint"]
    
    pw = None
    browser = None
    try:
        pw, browser, context, page = manager.connect_playwright(ws_endpoint)

        page.goto("https://accounts.google.com/signup", timeout=60000)
        check_bot_error(page, profile_id)
        
        # BƯỚC 1: NHẬP HỌ TÊN
        realistic_type(page, 'input[name="firstName"]', profile['first_name'])
        realistic_type(page, 'input[name="lastName"]', profile['last_name'])
        click_next_button(page)
        check_bot_error(page, profile_id)
        
        if "phone" in page.url.lower() or page.locator('input[type="tel"]').count() > 0:
            raise Exception("Bị yêu cầu xác minh số điện thoại (OTP) ngay sau bước Tên.")

        # BƯỚC 2: NHẬP NGÀY SINH & GIỚI TÍNH
        page.wait_for_selector('select#month, select[aria-labelledby="month"]', timeout=10000)
        realistic_type(page, 'input[name="day"]', profile['day'])
        page.select_option('select#month, select[aria-labelledby="month"]', index=int(profile['month']))
        random_wait(0.5, 1.2)
        realistic_type(page, 'input[name="year"]', profile['year'])
        page.select_option('select#gender, select[aria-labelledby="gender"]', value=profile['gender_value'])
        click_next_button(page)
        check_bot_error(page, profile_id)

        if "phone" in page.url.lower() or page.locator('input[type="tel"]').count() > 0:
            raise Exception("Bị yêu cầu xác minh số điện thoại (OTP) sau bước Ngày sinh.")

        # BƯỚC 3: CHỌN USERNAME
        page.wait_for_selector('input[name="Username"]', timeout=10000)
        custom_email_radio = page.locator('div[role="radio"]:has-text("Create your own"), div[role="radio"]:has-text("Tạo địa chỉ Gmail")')
        if custom_email_radio.count() > 0:
            custom_email_radio.first.click()
            random_wait(1.0, 2.5)

        realistic_type(page, 'input[name="Username"]', profile['username'])
        click_next_button(page)
        check_bot_error(page, profile_id)
        
        # BƯỚC 4: NHẬP PASSWORD
        page.wait_for_selector('input[name="Passwd"]', timeout=10000)
        realistic_type(page, 'input[name="Passwd"]', profile['password'])
        random_wait(0.5, 1.0)
        realistic_type(page, 'input[name="PasswdAgain"]', profile['password'])
        click_next_button(page)
        check_bot_error(page, profile_id)

        # BƯỚC 5: KIỂM TRA OTP CUỐI CÙNG
        page.wait_for_timeout(3000)
        check_bot_error(page, profile_id)
        if "phone" in page.url.lower() or page.locator('input[type="tel"]').count() > 0:
            raise Exception("Google yêu cầu xác minh số điện thoại (OTP) trước khi hoàn tất.")

        save_account_success(profile['username'], profile['password'])
        print(f"[+] {thread_name} - Tạo tài khoản thành công mà không dính OTP!")

    except Exception as e:
        print(f"[-] {thread_name} - Lỗi/Bị chặn ở profile {profile_id} ({profile['username']}): {str(e)}")
    finally:
        # Giải phóng RAM và đóng profile
        if browser:
            try:
                browser.close()
            except:
                pass
        if pw:
            try:
                pw.stop()
            except:
                pass
        
        print(f"[*] {thread_name} - Đang tắt profile Hidemium {profile_id} và giải phóng bộ nhớ...")
        manager.stop_profile(profile_id)


def worker_task(profile_id):
    """Wrapper cho ThreadPoolExecutor"""
    if profile_id:
        create_gmail_profile(profile_id)


def main():
    max_workers = 5
    
    # Danh sách ID của các profile Hidemium đã được tạo sẵn
    hidemium_profile_ids = [
        "2818958c-7c34-4d28-9e2d-cfde97ac71b7",
        "28189490-1577-43e2-ba54-1db965857468",
        "28189430-7e21-4749-bc1a-159c03caa8d5",
        "281712c7-5214-498c-baf2-53ded1090679",
        "2816ae50-2cca-47a9-b54a-ab18d7c41283",
        "2816ad49-a483-4113-88bf-820743b63318"
    ]

    print(f"=== Bắt đầu chạy tự động hóa với {max_workers} luồng qua Hidemium ===")
    
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Worker") as executor:
        executor.map(worker_task, hidemium_profile_ids)
        
    print("=== Đã hoàn thành toàn bộ tác vụ! ===")

if __name__ == "__main__":
    main()
