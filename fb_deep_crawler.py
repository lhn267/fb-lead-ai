import os
import re
import time
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Callable
from playwright.sync_api import sync_playwright, BrowserContext, Page

# Profile directory for persistent Facebook session
CHROME_PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_chrome_session")

def get_about_url(profile_url: str) -> str:
    """Converts a standard Facebook profile URL into its About Work & Education URL."""
    if not profile_url or not isinstance(profile_url, str):
        return ""
    clean = profile_url.split("?")[0].rstrip("/")
    if "profile.php" in profile_url:
        # Match ID
        m = re.search(r"id=(\d+)", profile_url)
        if m:
            return f"https://www.facebook.com/profile.php?id={m.group(1)}&sk=about_work_and_education"
        return f"{profile_url}&sk=about_work_and_education"
    else:
        return f"{clean}/about_work_and_education"

def extract_work_education_from_page(page: Page) -> Dict[str, Any]:
    """
    Extracts Work, School, and Basic Info text from Facebook's about_work_and_education page.
    """
    page_text = page.inner_text("body")
    lines = [line.strip() for line in page_text.split("\n") if line.strip()]
    
    work_items = []
    school_items = []
    
    current_section = None
    
    IGNORE_PHRASES = [
        "không có nơi làm việc để hiển thị",
        "không có trường học nào để hiển thị",
        "đăng nhập", "bạn quên tài khoản", "xem thêm", "giới thiệu", "bài viết",
        "ảnh", "reels", "tổng quan", "nơi từng sống", "thông tin liên hệ",
        "tính minh bạch", "gia đình", "chi tiết về", "cột mốc", "xem tất cả",
        "email hoặc số điện thoại", "mật khẩu", "quên mật khẩu", "tạo tài khoản",
        "quyền riêng tư", "điều khoản", "quảng cáo", "lựa chọn quảng cáo", "cookie"
    ]
    
    for i, line in enumerate(lines):
        line_low = line.lower()
        
        # Section detection
        if line_low in ["công việc", "work"]:
            current_section = "work"
            continue
        elif line_low in ["đại học", "college", "học vấn", "education"]:
            current_section = "school"
            continue
        elif line_low in ["trường trung học", "high school", "trường học"]:
            current_section = "high_school"
            continue
        elif line_low in ["nơi từng sống", "places lived", "thông tin liên hệ", "tổng quan", "overview"]:
            current_section = "other"
            continue
            
        if any(ig in line_low for ig in IGNORE_PHRASES):
            continue
            
        if len(line) < 3 or len(line) > 150:
            continue
            
        # Collect items based on section
        if current_section == "work":
            # Collect meaningful job lines
            if not any(item in line for item in work_items):
                work_items.append(line)
        elif current_section in ["school", "high_school"]:
            if not any(item in line for item in school_items):
                school_items.append(line)
    # Broad scan for explicit Vietnamese job/school statements
    for line in lines:
        line_s = line.strip()
        line_low = line_s.lower()
        if any(ig in line_low for ig in IGNORE_PHRASES) or len(line_s) < 5 or len(line_s) > 120:
            continue
            
        if any(kw in line_low for kw in ["làm việc tại", "chức vụ", "giám đốc tại", "quản lý tại", "founder tại", "ceo tại", "chủ tịch tại", "từng làm việc tại", "chủ sáng lập tại"]):
            if line_s not in work_items:
                work_items.append(line_s)
        elif any(kw in line_low for kw in ["đã học tại", "từng học tại", "học tại", "sinh viên tại", "cựu sinh viên tại"]):
            if line_s not in school_items:
                school_items.append(line_s)

    # Build concise combined text
    combined_parts = []
    if work_items:
        combined_parts.append("Công việc: " + " · ".join(work_items[:3]))
    if school_items:
        combined_parts.append("Học vấn: " + " · ".join(school_items[:2]))
        
    full_text = " | ".join(combined_parts)
    
    return {
        "work": " · ".join(work_items[:3]) if work_items else "",
        "school": " · ".join(school_items[:2]) if school_items else "",
        "full_text": full_text if full_text else "Không có thông tin việc làm công khai"
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
        
    total_to_crawl = min(len(enriched_df), max_count)
    
    with sync_playwright() as p:
        # Launch persistent context to reuse cookies in clean stealth mode
        context = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE_DIR,
            channel="chrome",
            headless=headless,
            viewport={"width": 1280, "height": 800},
            ignore_default_args=["--enable-automation", "--no-sandbox"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        
        # Inject cookie string if provided
        if cookie_str:
            inject_cookie_string(context, cookie_str)
            
        page = context.pages[0] if context.pages else context.new_page()
        
        # Check if logged in
        page.goto("https://www.facebook.com/", timeout=45000)
        time.sleep(2)
        
        is_logged_in = True
        if "login" in page.url.lower() or page.query_selector('input[name="email"]'):
            is_logged_in = False
            if progress_callback:
                progress_callback(0, total_to_crawl, "Lưu ý: Chưa đăng nhập Facebook trong phiên duyệt. Đang cào ở chế độ Công khai...")

        for idx in range(total_to_crawl):
            row = enriched_df.iloc[idx]
            raw_url = str(row.get(link_col, "")).strip()
            name_val = str(row.get(name_col, f"Người {idx+1}")).strip()
            
            if not raw_url or not raw_url.startswith("http"):
                continue
                
            about_url = get_about_url(raw_url)
            
            if progress_callback:
                progress_callback(idx + 1, total_to_crawl, f"Đang cào profile ({idx+1}/{total_to_crawl}): {name_val}")
                
            try:
                page.goto(about_url, timeout=30000)
                # Wait for React DOM to render
                page.wait_for_timeout(int(delay_seconds * 1000))
                
                info_res = extract_work_education_from_page(page)
                enriched_df.at[idx, "Thông tin cào sâu"] = info_res["full_text"]
            except Exception as e:
                enriched_df.at[idx, "Thông tin cào sâu"] = f"Lỗi truy cập profile: {str(e)[:50]}"
                
        context.close()
        
    return enriched_df
