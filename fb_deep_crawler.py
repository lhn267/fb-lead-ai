import os
import re
import time
import json
import platform
import subprocess
import pandas as pd
from typing import List, Dict, Any, Optional, Callable
from playwright.sync_api import sync_playwright, BrowserContext, Page

# Profile directory for persistent Facebook session
CHROME_PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_chrome_session")

def get_chrome_channel() -> Optional[str]:
    """
    Returns 'chrome' only if Google Chrome is verified to exist on the host system.
    Otherwise returns None (which tells Playwright to use its bundled Chromium).
    """
    sys_name = platform.system()
    if sys_name == "Windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        if any(os.path.exists(p) for p in chrome_paths):
            return "chrome"
    elif sys_name == "Linux":
        if os.path.exists("/opt/google/chrome/chrome") or os.path.exists("/usr/bin/google-chrome"):
            return "chrome"
    elif sys_name == "Darwin":
        if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
            return "chrome"
    return None

def ensure_playwright_installed():
    """Installs Playwright Chromium if it is not installed in the environment."""
    import sys
    try:
        cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
        subprocess.run(cmd, capture_output=True, timeout=180)
    except Exception:
        pass

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

def cleanup_chrome_lock():
    """
    Cleans up any lingering Chrome processes using CHROME_PROFILE_DIR and removes stale lock files.
    """
    try:
        ps_cmd = (
            "$procs = Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -like '*fb_chrome_session*' }; "
            "if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force } }"
        )
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], 
                       capture_output=True, timeout=5)
    except Exception:
        pass
        
    for fname in ["lockfile", "SingletonLock", "SingletonSocket", "SingletonCookie"]:
        fpath = os.path.join(CHROME_PROFILE_DIR, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass

def get_clean_profile_url(profile_url: str) -> str:
    """Converts mutual friends, subtabs, or query URLs into a clean base profile URL."""
    if not profile_url or not isinstance(profile_url, str):
        return ""
    clean = profile_url.strip()
    if "profile.php" in clean:
        m = re.search(r"id=(\d+)", clean)
        if m:
            return f"https://www.facebook.com/profile.php?id={m.group(1)}"
        return clean.split("&sk=")[0]
    else:
        clean = clean.split("?")[0].rstrip("/")
        for suffix in ["/friends_mutual", "/friends", "/about_work_and_education", "/about"]:
            if clean.endswith(suffix):
                clean = clean[:-len(suffix)]
        return clean.rstrip("/")

def extract_work_education_from_page(page: Page) -> Dict[str, Any]:
    """
    Extracts Work, School, Category, Bio, and Contact text from Facebook's page.
    Compatible with both modern Professional Mode profiles and classic personal profiles.
    """
    page_text = page.inner_text("body")
    lines = [line.strip() for line in page_text.split("\n") if line.strip()]
    
    IGNORE_TERMS = {
        "facebook", "tìm bạn bè", "nhắn tin", "thêm bạn bè", "bạn bè", "ảnh", "reels",
        "sự kiện", "xem thêm", "xem tất cả", "tất cả", "bài viết", "bộ lọc", "bài viết đã ghim",
        "giới thiệu", "thông tin cá nhân", "nữ", "nam", "độc thân", "thước phim",
        "hãy viết gì đó", "ảnh/video", "gắn thẻ người khác", "cảm xúc/hoạt động",
        "xem thêm công việc", "xem thêm học vấn", "đăng ký", "trả lời", "tác giả",
        "không có nơi làm việc để hiển thị", "không có trường học nào để hiển thị",
        "đăng nhập", "bạn quên tài khoản", "quyền riêng tư", "điều khoản", "quảng cáo"
    }
    
    work_items = []
    school_items = []
    bio_items = []
    contact_items = []
    category = ""
    current_sec = None
    
    for i, line in enumerate(lines):
        line_l = line.lower()
        
        # Follower counts or mutual friends
        if "người theo dõi" in line_l or re.match(r"^(\d+[\.,]?\d*[KkMm]?|\d+\s+bạn\s+chung)$", line):
            continue
            
        # Detect Category / Hạng mục
        if any(cat in line_l for cat in ["người sáng tạo nội dung", "blogger", "bất động sản", "doanh nhân", "nghệ sĩ", "chuyên viên", "nhà phát triển"]):
            category = line
            continue
            
        # Section headers
        if line_l in ["công việc", "work"]:
            current_sec = "work"
            continue
        elif line_l in ["giáo dục", "học vấn", "trình độ học vấn", "education", "đại học", "trường học"]:
            current_sec = "school"
            continue
        elif line_l in ["thông tin liên hệ", "liên kết", "liên hệ", "contact"]:
            current_sec = "contact"
            continue
        elif line_l in ["thông tin cá nhân", "bạn bè", "bài viết", "ảnh", "reels", "sự kiện", "xem thêm", "tổng quan"]:
            current_sec = None
            continue
            
        if line_l in IGNORE_TERMS or line.startswith("URL:") or (line.startswith("http") and "facebook.com" in line):
            if not (current_sec == "contact" and ("linkedin" in line_l or "zalo" in line_l or ".com" in line_l)):
                continue
                
        if len(line) < 2 or len(line) > 160:
            continue
            
        # Section items
        if current_sec == "work":
            if line not in work_items and not any(term in line_l for term in ["vào ngày", "tháng"]):
                if not line.startswith("·"):
                    work_items.append(line)
        elif current_sec == "school":
            if line not in school_items:
                school_items.append(line)
        elif current_sec == "contact":
            if any(kw in line_l for kw in ["linkedin", "zalo", "github", ".vn", ".com", ".asia"]) and not any(ig in line_l for ig in ["facebook", "fbcdn"]):
                if line not in contact_items:
                    contact_items.append(line)
                    
        # Explicit Vietnamese keywords anywhere in page
        if any(kw in line_l for kw in ["làm việc tại", "chức vụ", "giám đốc tại", "quản lý tại", "founder tại", "ceo tại", "chủ tịch tại", "từng làm việc tại", "chủ sáng lập tại"]):
            if line not in work_items:
                work_items.append(line)
        elif any(kw in line_l for kw in ["đã học tại", "từng học tại", "học tại", "sinh viên tại", "cựu sinh viên tại"]):
            if line not in school_items:
                school_items.append(line)
                
        # Bio / Subtitle detection
        if i < 22 and not current_sec:
            if any(kw in line_l for kw in ["hiring", "ceo", "founder", "lead", "manager", "director", "chuyên", "tư vấn", "zalo", "kinh doanh", "hr"]):
                if line not in bio_items and line != category:
                    bio_items.append(line)

    parts = []
    if category:
        parts.append(f"Hạng mục/Lĩnh vực: {category}")
    if work_items:
        parts.append(f"Công việc: {' · '.join(work_items[:4])}")
    if school_items:
        parts.append(f"Học vấn: {' · '.join(school_items[:2])}")
    if bio_items:
        parts.append(f"Tiểu sử/Mô tả: {' | '.join(bio_items[:2])}")
    if contact_items:
        parts.append(f"Liên hệ: {' · '.join(contact_items[:2])}")
        
    full_text = " | ".join(parts) if parts else "Không có thông tin việc làm công khai"
    return {
        "category": category,
        "work": " · ".join(work_items[:4]),
        "school": " · ".join(school_items[:2]),
        "bio": " | ".join(bio_items[:2]),
        "full_text": full_text
    }

def inject_cookie_string(context, cookie_str: str):
    """Parses standard cookie string and injects into Playwright browser context."""
    if not cookie_str or not isinstance(cookie_str, str):
        return
    cookies = []
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            name, val = item.split("=", 1)
            name = name.strip()
            val = val.strip()
            if name:
                cookies.append({
                    "name": name,
                    "value": val,
                    "domain": ".facebook.com",
                    "path": "/"
                })
    if cookies:
        context.add_cookies(cookies)

def run_deep_profile_crawl(
    df: pd.DataFrame,
    link_col: str,
    name_col: str,
    start_index: int = 1,
    max_count: int = 50,
    delay_seconds: float = 3.5,
    headless: bool = True,
    cookie_str: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> pd.DataFrame:
    """
    Crawls Facebook profiles deeply to extract Work & Education directly from their About page.
    Uses persistent Chrome session context so user only needs to log in once.
    """
    os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)
    
    enriched_df = df.copy()
    if "Thông tin cào sâu" not in enriched_df.columns:
        enriched_df["Thông tin cào sâu"] = ""
        
    start_pos = max(0, int(start_index) - 1)
    end_pos = min(len(enriched_df), start_pos + int(max_count))
    total_to_crawl = max(0, end_pos - start_pos)
    
    browser = None
    context = None
    channel_to_use = get_chrome_channel()
    
    launch_args = ["--disable-blink-features=AutomationControlled"]
    if platform.system() == "Linux":
        launch_args.extend(["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])

    with sync_playwright() as p:
        if cookie_str and cookie_str.strip():
            # If user provided raw cookie string, launch clean browser instance
            try:
                browser = p.chromium.launch(
                    channel=channel_to_use,
                    headless=headless,
                    args=launch_args,
                    ignore_default_args=["--enable-automation"]
                )
            except Exception:
                try:
                    browser = p.chromium.launch(
                        channel=None,
                        headless=headless,
                        args=launch_args,
                        ignore_default_args=["--enable-automation"]
                    )
                except Exception:
                    ensure_playwright_installed()
                    browser = p.chromium.launch(
                        channel=None,
                        headless=headless,
                        args=launch_args,
                        ignore_default_args=["--enable-automation"]
                    )
            context = browser.new_context(viewport={"width": 1280, "height": 800}, user_agent=DEFAULT_USER_AGENT)
            inject_cookie_string(context, cookie_str)
        else:
            # Persistent session mode
            cleanup_chrome_lock()
            time.sleep(0.5)

            def try_launch_persistent(ch):
                kwargs = {
                    "user_data_dir": CHROME_PROFILE_DIR,
                    "headless": headless,
                    "viewport": {"width": 1280, "height": 800},
                    "user_agent": DEFAULT_USER_AGENT,
                    "args": launch_args,
                    "ignore_default_args": ["--enable-automation"]
                }
                if ch:
                    kwargs["channel"] = ch
                return p.chromium.launch_persistent_context(**kwargs)

            try:
                context = try_launch_persistent(channel_to_use)
            except Exception as err:
                err_str = str(err)
                if ("chrome" in err_str.lower() and "not found" in err_str.lower()) or "executable doesn" in err_str.lower():
                    # Fallback to standard Chromium without channel="chrome"
                    try:
                        context = try_launch_persistent(None)
                    except Exception:
                        ensure_playwright_installed()
                        context = try_launch_persistent(None)
                elif "ProcessSingleton" in err_str or "Lock file" in err_str:
                    time.sleep(1.0)
                    cleanup_chrome_lock()
                    try:
                        context = try_launch_persistent(channel_to_use)
                    except Exception as final_err:
                        raise RuntimeError(
                            "Cửa sổ Google Chrome đăng nhập Facebook vẫn đang mở! "
                            "Vui lòng ĐÓNG cửa sổ Chrome vừa mở (hoặc tắt Dang_Nhap_Facebook.bat) "
                            "rồi bấm lại 'Bắt đầu cào sâu'. Hoặc bạn có thể dán Cookie Facebook ở ô bên dưới để cào ngay lập tức mà không cần mở trình duyệt."
                        ) from final_err
                else:
                    try:
                        ensure_playwright_installed()
                        context = try_launch_persistent(None)
                    except Exception:
                        raise err
            
        page = context.pages[0] if context.pages else context.new_page()
        
        # Check if logged in
        page.goto("https://www.facebook.com/", timeout=45000)
        time.sleep(2)
        
        is_logged_in = True
        if "login" in page.url.lower() or page.query_selector('input[name="email"]'):
            is_logged_in = False
            if progress_callback:
                progress_callback(0, total_to_crawl, "Lưu ý: Chưa đăng nhập Facebook trong phiên duyệt. Đang cào ở chế độ Công khai...")

        for curr_i, idx in enumerate(range(start_pos, end_pos)):
            row = enriched_df.iloc[idx]
            raw_url = str(row.get(link_col, "")).strip()
            name_val = str(row.get(name_col, f"Người {idx+1}")).strip()
            
            if not raw_url or not raw_url.startswith("http"):
                continue
                
            clean_url = get_clean_profile_url(raw_url)
            
            if progress_callback:
                progress_callback(curr_i + 1, total_to_crawl, f"Đang cào profile #{idx+1} ({curr_i+1}/{total_to_crawl}): {name_val}")
                
            try:
                # 1. First visit the clean base profile page (renders Bio, Category, Intro Card with Work/Education/Links)
                page.goto(clean_url, timeout=30000)
                page.wait_for_timeout(int(delay_seconds * 1000))
                
                info_res = extract_work_education_from_page(page)
                
                # 2. If no work/school/category found on main timeline, check /about page
                if info_res["full_text"] == "Không có thông tin việc làm công khai":
                    about_url = f"{clean_url}&sk=about" if "profile.php" in clean_url else f"{clean_url}/about"
                    try:
                        page.goto(about_url, timeout=20000)
                        page.wait_for_timeout(int(delay_seconds * 800))
                        info_about = extract_work_education_from_page(page)
                        if info_about["full_text"] != "Không có thông tin việc làm công khai":
                            info_res = info_about
                    except Exception:
                        pass
                        
                enriched_df.at[enriched_df.index[idx], "Thông tin cào sâu"] = info_res["full_text"]
            except Exception as e:
                enriched_df.at[enriched_df.index[idx], "Thông tin cào sâu"] = f"Lỗi truy cập profile: {str(e)[:50]}"
                
        if browser:
            browser.close()
        elif context:
            context.close()
            
    return enriched_df
