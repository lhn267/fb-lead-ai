"""
fb_auto_scroller.py - Công Cụ Tự Động Cuộn & Cào Danh Sách Bạn Bè Facebook
Tự động cuộn trang bạn bè Facebook với cơ chế giả lập hành vi người thật,
trích xuất Họ tên, Link Profile, Thông tin công việc/học vấn và xuất file Excel/CSV.
"""

import os
import sys
import io
import re
import time
import random
import platform
import subprocess
import pandas as pd
from typing import List, Dict, Any, Optional

# Ensure UTF-8 output on Windows CMD
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright, Page, BrowserContext

CHROME_PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_chrome_session")

def get_chrome_executable() -> Optional[str]:
    """Tìm đường dẫn Google Chrome chính thức trên Windows."""
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def clean_profile_link(raw_link: str) -> str:
    """Chuẩn hóa đường dẫn Facebook cá nhân."""
    if not raw_link:
        return ""
    link = raw_link.strip().split("?")[0].rstrip("/")
    if "profile.php" in raw_link:
        m = re.search(r"id=(\d+)", raw_link)
        if m:
            return f"https://www.facebook.com/profile.php?id={m.group(1)}"
        return raw_link.split("&sk=")[0]
    for suffix in ["/friends_mutual", "/friends", "/about", "/about_work_and_education"]:
        if link.endswith(suffix):
            link = link[:-len(suffix)]
    return link.rstrip("/")

def extract_friends_from_page(page: Page) -> List[Dict[str, str]]:
    """
    Trích xuất toàn bộ bạn bè hiện có trong DOM Facebook.
    Tương thích với cả giao diện Facebook cá nhân mới lẫn Profile Pro.
    """
    js_code = """
    () => {
        const results = [];
        const seenUrls = new Set();
        
        // Tìm các container bạn bè phổ biến trên Facebook
        const links = document.querySelectorAll('a[href*="/"]');
        
        links.forEach(a => {
            const href = a.getAttribute('href') || '';
            
            // Lọc các link có khả năng là profile bạn bè
            const isProfile = (
                (href.includes('facebook.com/') || href.startsWith('/')) &&
                !href.includes('/groups/') &&
                !href.includes('/watch/') &&
                !href.includes('/marketplace/') &&
                !href.includes('/gaming/') &&
                !href.includes('/bookmarks/') &&
                !href.includes('/notifications') &&
                !href.includes('/messages/') &&
                !href.includes('/events/') &&
                !href.includes('/saved/') &&
                !href.includes('/pages/') &&
                !href.includes('/help/') &&
                !href.includes('login') &&
                !href.includes('#')
            );
            
            if (!isProfile) return;
            
            // Tìm tên hiển thị
            let name = a.innerText.trim();
            if (!name || name.length < 2 || name.includes('\\n')) {
                const span = a.querySelector('span[dir="auto"], span');
                if (span) name = span.innerText.trim();
            }
            
            // Bỏ qua các text nút chức năng
            const ignoreList = ['Thêm bạn bè', 'Nhắn tin', 'Bạn bè', 'Xóa', 'Chặn', 'Theo dõi', 'Hủy kết bạn', 'Đang theo dõi', 'Xem tất cả'];
            if (!name || ignoreList.some(ig => name.toLowerCase() === ig.toLowerCase()) || name.length > 50) return;
            
            // Tìm container chứa thông tin phụ (công việc, bạn chung)
            let card = a.closest('div[role="article"]') || a.closest('div[data-visualcompletion="ignore-dynamic-snippet"]') || a.parentElement?.parentElement?.parentElement;
            let infoText = '';
            if (card) {
                const cardText = card.innerText.trim();
                const lines = cardText.split('\\n').map(l => l.trim()).filter(l => l && l !== name && !ignoreList.includes(l));
                if (lines.length > 0) {
                    infoText = lines.join(' · ');
                }
            }
            
            // Chuẩn hóa link
            let fullUrl = href.startsWith('http') ? href : ('https://www.facebook.com' + href);
            fullUrl = fullUrl.split('?')[0];
            
            if (!seenUrls.has(fullUrl) && name) {
                seenUrls.add(fullUrl);
                results.push({
                    name: name,
                    link: fullUrl,
                    info: infoText
                });
            }
        });
        
        return results;
    }
    """
    try:
        raw_items = page.evaluate(js_code)
        cleaned = []
        seen = set()
        for it in raw_items:
            c_link = clean_profile_link(it.get("link", ""))
            c_name = it.get("name", "").strip()
            if c_link and c_name and c_link not in seen:
                seen.add(c_link)
                cleaned.append({
                    "Họ và tên": c_name,
                    "Link Facebook": c_link,
                    "Thông tin giới thiệu / Công việc": it.get("info", "")
                })
        return cleaned
    except Exception as e:
        print(f"[!] Lỗi trích xuất: {e}")
        return []

def run_auto_scroller(
    target_url: str = "https://www.facebook.com/me/friends",
    max_scrolls: int = 500,
    output_filename: str = "danh_sach_ban_be_tu_dong"
):
    print("=" * 70)
    print("   🚀 TOOL TỰ ĐỘNG CUỘN & CÀO BẠN BÈ FACEBOOK (AUTO-SCROLLER)")
    print("=" * 70)
    print(f"[*] Trang đích: {target_url}")
    print(f"[*] Phiên đăng nhập: {CHROME_PROFILE_DIR}")
    print("[*] Cơ chế cuộn: Giả lập cử chỉ người thật (Human-like jitter & delay)")
    print("[*] Mẹo: Bạn có thể bấm [Ctrl + C] bất kỳ lúc nào để DỪNG và LƯU dữ liệu ngay!\n")

    os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)
    chrome_exe = get_chrome_executable()

    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": CHROME_PROFILE_DIR,
            "headless": False,
            "viewport": {"width": 1280, "height": 850},
            "ignore_default_args": ["--enable-automation"]
        }
        if chrome_exe:
            launch_kwargs["channel"] = "chrome"

        try:
            context = p.chromium.launch_persistent_context(**launch_kwargs)
        except Exception as e:
            print(f"[!] Lỗi khởi động Chrome profile: {e}")
            print(">> Hãy đảm bảo bạn đã đóng mọi cửa sổ Chrome mở bằng session này trước khi chạy!")
            return

        page = context.pages[0] if context.pages else context.new_page()

        print(f">> Đang mở trình duyệt và truy cập: {target_url} ...")
        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        # Kiểm tra xem có đang ở trang login không
        if "login" in page.url.lower():
            print("\n[!] BẠN CHƯA ĐĂNG NHẬP FACEBOOK TRÊN PROFILE NÀY!")
            print(">> Hãy thao tác đăng nhập Facebook trên cửa sổ vừa hiện lên...")
            print(">> Tool sẽ tự động bắt đầu cuộn sau khi bạn đăng nhập thành công vào danh sách bạn bè.\n")
            # Chờ người dùng đăng nhập xong
            while "login" in page.url.lower():
                time.sleep(2)
            time.sleep(3)
            if not target_url in page.url:
                page.goto(target_url)
                time.sleep(3)

        print("\n" + "-" * 70)
        print("   ▶ BẮT ĐẦU TỰ ĐỘNG CUỘN (Tự động tải thêm bạn bè)...")
        print("   (Bấm Ctrl+C trên cửa sổ này bất cứ lúc nào để kết thúc & xuất file)")
        print("-" * 70 + "\n")

        scroll_count = 0
        no_growth_streak = 0
        last_friend_count = 0
        all_friends = []

        try:
            while scroll_count < max_scrolls:
                scroll_count += 1
                
                # 1. Cuộn chuột với khoảng cách ngẫu nhiên
                scroll_delta = random.randint(600, 1100)
                page.mouse.wheel(0, scroll_delta)
                
                # 2. Thi thoảng cuộn nhẹ ngược lên 100px (mô phỏng mắt người lướt)
                if scroll_count % 8 == 0:
                    time.sleep(0.5)
                    page.mouse.wheel(0, -random.randint(80, 150))
                    time.sleep(0.4)

                # 3. Delay ngẫu nhiên giữa các lần cuộn (2.0s - 3.8s) để an toàn tuyệt đối
                delay = random.uniform(2.0, 3.8)
                time.sleep(delay)

                # 4. Kiểm tra số lượng bạn bè hiện tại trong DOM mỗi 3 lần cuộn
                if scroll_count % 3 == 0 or scroll_count == 1:
                    all_friends = extract_friends_from_page(page)
                    curr_count = len(all_friends)
                    
                    print(f" [Cuộn #{scroll_count:03d}] Đã quét được: {curr_count} bạn bè | Delay: {delay:.1f}s")
                    
                    if curr_count > last_friend_count:
                        last_friend_count = curr_count
                        no_growth_streak = 0
                    else:
                        no_growth_streak += 1
                        
                    # Nếu 6 lần kiểm tra liên tiếp (~18 lần cuộn) không có bạn bè mới -> Đã chạm đáy trang
                    if no_growth_streak >= 6:
                        print("\n[✓] Đã cuộn hết toàn bộ danh sách bạn bè (Đã chạm đáy trang)!")
                        break

        except KeyboardInterrupt:
            print("\n\n[!] BẠN ĐÃ BẤM DỪNG (CTRL+C)!")
            print(">> Đang thu thập và xuất toàn bộ dữ liệu bạn bè đã cuộn được...")

        # Trích xuất lần cuối cùng
        print("\n>> Đang hoàn thiện trích xuất dữ liệu...")
        final_friends = extract_friends_from_page(page)
        if len(final_friends) > len(all_friends):
            all_friends = final_friends

        try:
            context.close()
        except Exception:
            pass

    # Xuất file kết quả
    if all_friends:
        df = pd.DataFrame(all_friends)
        
        # Thêm STT
        df.insert(0, "STT", range(1, len(df) + 1))
        
        csv_file = f"{output_filename}.csv"
        xlsx_file = f"{output_filename}.xlsx"
        
        # Lưu file CSV UTF-8-BOM để Excel mở không bị lỗi font tiếng Việt
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")
        
        # Lưu file Excel
        try:
            df.to_excel(xlsx_file, index=False)
            excel_saved = True
        except Exception:
            excel_saved = False
            
        print("\n" + "=" * 70)
        print(f"   🎉 THÀNH CÔNG! ĐÃ CÀO ĐƯỢC {len(df)} BẠN BÈ FACEBOOK")
        print("=" * 70)
        print(f" [1] File CSV:   {os.path.abspath(csv_file)}")
        if excel_saved:
            print(f" [2] File Excel: {os.path.abspath(xlsx_file)}")
        print("\n👉 BƯỚC TIẾP THEO:")
        print("   1. Mở ứng dụng web (Chay_He_Thong.bat).")
        print("   2. Vào 'Tab 1: Nạp File & Phân Tích' và kéo thả file vừa tạo vào.")
        print("   3. Bấm 'Bắt đầu xử lý' để AI tự bóc tách chức vụ, công ty, cấp bậc!")
        print("=" * 70 + "\n")
    else:
        print("\n[!] Không tìm thấy dữ liệu bạn bè nào. Vui lòng kiểm tra lại trang bạn bè hoặc đăng nhập.")

if __name__ == "__main__":
    # Cho phép người dùng nhập link tùy chọn nếu muốn
    print("Nhập URL trang bạn bè cần cuộn (Nhấn Enter để dùng mặc định: https://www.facebook.com/me/friends):")
    user_url = input("URL > ").strip()
    if not user_url:
        user_url = "https://www.facebook.com/me/friends"
        
    run_auto_scroller(target_url=user_url)
