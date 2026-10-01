import os
import sys
import time
from playwright.sync_api import sync_playwright

CHROME_PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_chrome_session")

def main():
    print("=" * 65)
    print("   🌐 TIỆN ÍCH ĐĂNG NHẬP FACEBOOK ĐỂ LƯU PHIÊN CÀO DỮ LIỆU")
    print("=" * 65)
    print("\n1. Trình duyệt sẽ mở ra trang Facebook ngay bây giờ.")
    print("2. Vui lòng đăng nhập tài khoản Facebook của bạn (tài khoản clone hoặc tài khoản chính).")
    print("3. Sau khi vào được bảng tin Facebook, bạn chỉ cần ĐÓNG CỬA SỔ TRÌNH DUYỆT.")
    print("4. Phiên đăng nhập sẽ được lưu vĩnh viễn trên máy tính của bạn.\n")
    print("=" * 65)
    
    os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.facebook.com/")
        
        print("\nTrình duyệt đã mở. Vui lòng thao tác trên trình duyệt...")
        
        # Keep waiting until the user closes the window or 5 minutes pass
        start_time = time.time()
        while time.time() - start_time < 300:
            time.sleep(1)
            if not context.pages:
                break
                
        context.close()
        
    print("\n✅ ĐÃ LƯU PHIÊN ĐĂNG NHẬP THÀNH CÔNG! Bạn có thể sử dụng tính năng cào sâu ngay bây giờ.")

if __name__ == "__main__":
    main()
