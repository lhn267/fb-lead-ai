import os
import sys
import io
import time

# Ensure Windows CMD never crashes on UTF-8 text
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

CHROME_PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_chrome_session")

def main():
    print("=" * 65)
    print("   🌐 TIỆN ÍCH ĐĂNG NHẬP FACEBOOK ĐỂ LƯU PHIÊN CÀO DỮ LIỆU")
    print("=" * 65)
    print("\n1. Trình duyệt Chromium sẽ mở ra trang Facebook ngay bây giờ.")
    print("2. Vui lòng đăng nhập tài khoản Facebook của bạn.")
    print("3. Sau khi vào được bảng tin Facebook, bạn chỉ cần ĐÓNG CỬA SỔ TRÌNH DUYỆT ĐÓ LẠI.")
    print("4. Phiên đăng nhập sẽ được lưu an toàn trên máy tính của bạn.\n")
    print("=" * 65)
    
    os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE_DIR,
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 800},
            ignore_default_args=["--enable-automation"]
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.facebook.com/")
        
        print("\nTrình duyệt đã mở thành công!")
        print(">> Hãy thao tác đăng nhập Facebook trên cửa sổ trình duyệt vừa hiện lên...")
        print(">> Sau khi xong, hãy ĐÓNG cửa sổ trình duyệt để hoàn tất.")
        
        # Keep waiting until the user closes the window or 10 minutes pass
        start_time = time.time()
        while time.time() - start_time < 600:
            time.sleep(1)
            try:
                if not context.pages or page.is_closed():
                    break
            except Exception:
                break
                
        try:
            context.close()
        except Exception:
            pass
        
    print("\n[OK] ĐÃ LƯU PHIÊN ĐĂNG NHẬP THÀNH CÔNG! Bạn có thể bắt đầu cào sâu ngay bây giờ.")

if __name__ == "__main__":
    main()
