import os
import json
import time
import pandas as pd
import streamlit as st
from fb_processor import (
    detect_columns,
    clean_file_data,
    process_friends_dataframe,
    export_styled_excel,
    merge_and_deduplicate_dfs
)
from fb_deep_crawler import run_deep_profile_crawl, CHROME_PROFILE_DIR

# Page configuration
st.set_page_config(
    page_title="AI FB Lead Extractor - Phân Loại Bạn Bè Facebook",
    page_icon="https://img.icons8.com/color/96/facebook-new.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- UNIFIED SVG ICON ENGINE -----------------
def get_svg_icon(name: str, size: int = 18, color: str = "currentColor", extra_style: str = "") -> str:
    """Returns a clean, unified Lucide/Feather vector SVG icon with consistent stroke and geometry."""
    style_attr = f'style="vertical-align: middle; display: inline-block; {extra_style}"'
    icons = {
        "facebook": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path></svg>',
        "settings": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>',
        "target": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>',
        "upload": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>',
        "table": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="12" y1="3" x2="12" y2="21"></line></svg>',
        "chart": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
        "book": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>',
        "users": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
        "star": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
        "briefcase": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
        "check": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        "trash": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>',
        "search": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
        "filter": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>',
        "download": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>',
        "play": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>',
        "bolt": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
        "save": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>',
        "eye": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>',
        "shield": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
        "school": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>',
        "building": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><path d="M9 22v-4h6v4"></path><path d="M8 6h.01"></path><path d="M16 6h.01"></path><path d="M8 10h.01"></path><path d="M16 10h.01"></path><path d="M8 14h.01"></path><path d="M16 14h.01"></path></svg>',
        "user": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
        "link": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>',
        "external": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>'
    }
    return icons.get(name, "")

# Custom Styling for modern corporate look
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 800;
        color: #1E3A8A;
        margin: 0;
        line-height: 1.2;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #4B5563;
        margin-top: 6px;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .metric-val {
        font-size: 1.9rem;
        font-weight: 800;
        margin-top: 6px;
    }
    .val-green { color: #059669; }
    .val-blue { color: #2563EB; }
    .val-amber { color: #D97706; }
    .val-red { color: #DC2626; }
    .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 1.15rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-top: 14px;
        margin-bottom: 10px;
    }
    .alert-success {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        border-radius: 10px;
        padding: 14px 18px;
        color: #065F46;
        margin-bottom: 16px;
    }
    .alert-info {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 12px 16px;
        color: #1E40AF;
        margin-bottom: 14px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

CONFIG_FILE = "config.json"

def load_saved_config():
    cfg = {}
    # 1. Cloud Secrets (Streamlit Cloud / Hugging Face Spaces)
    try:
        if hasattr(st, "secrets"):
            if "GEMINI_API_KEY" in st.secrets:
                cfg["gemini_key"] = st.secrets["GEMINI_API_KEY"]
            if "OPENAI_API_KEY" in st.secrets:
                cfg["openai_key"] = st.secrets["OPENAI_API_KEY"]
            if "TARGET_CRITERIA" in st.secrets:
                cfg["target_criteria"] = st.secrets["TARGET_CRITERIA"]
    except Exception:
        pass

    # 2. Environment Variables
    if os.getenv("GEMINI_API_KEY") and not cfg.get("gemini_key"):
        cfg["gemini_key"] = os.getenv("GEMINI_API_KEY")
    if os.getenv("OPENAI_API_KEY") and not cfg.get("openai_key"):
        cfg["openai_key"] = os.getenv("OPENAI_API_KEY")

    # 3. Local disk config.json (persists locally)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                disk_cfg = json.load(f)
                cfg.update({k: v for k, v in disk_cfg.items() if v})
        except Exception:
            pass
    return cfg

def save_user_config(config_dict):
    st.session_state["saved_config"] = config_dict
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
    except Exception:
        # In cloud environments with read-only filesystems, session_state safely keeps the config
        pass

saved_cfg = load_saved_config()

# ----------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom: 14px;">
        {get_svg_icon('settings', 24, '#1E3A8A')}
        <span style="font-size: 1.2rem; font-weight: 700; color: #1E3A8A;">Cấu Hình Hệ Thống</span>
    </div>
    """, unsafe_allow_html=True)

    api_provider = st.selectbox(
        "Nhà cung cấp AI",
        options=["Google Gemini (Khuyên dùng - Miễn phí)", "OpenAI (ChatGPT)", "Chế độ Offline (Bộ lọc quy tắc nội bộ)"],
        index=0 if saved_cfg.get("provider", "gemini") == "gemini" else (1 if saved_cfg.get("provider") == "openai" else 2)
    )

    api_key = ""
    model_name = "gemini-2.5-flash"

    if "Gemini" in api_provider:
        provider_code = "gemini"
        api_key = st.text_input(
            "Gemini API Key",
            value=saved_cfg.get("gemini_key", ""),
            type="password",
            help="Lấy API Key Google Gemini miễn phí tại Google AI Studio"
        )
        st.markdown(
            f"<a href='https://aistudio.google.com/app/apikey' target='_blank' style='text-decoration:none; color:#2563EB; font-weight:600; font-size:0.9rem;'>"
            f"{get_svg_icon('external', 14, '#2563EB')} Lấy Gemini API Key miễn phí (30 giây)</a>",
            unsafe_allow_html=True
        )
        model_name = st.selectbox(
            "Model Gemini",
            ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"],
            index=0
        )
    elif "OpenAI" in api_provider:
        provider_code = "openai"
        api_key = st.text_input(
            "OpenAI API Key",
            value=saved_cfg.get("openai_key", ""),
            type="password",
            help="Nhập API Key từ platform.openai.com"
        )
        model_name = st.selectbox("Model OpenAI", ["gpt-4o-mini", "gpt-4o"], index=0)
    else:
        provider_code = "offline"
        st.markdown(f"""
        <div class="alert-info" style="margin-top:10px;">
            {get_svg_icon('shield', 18, '#1E40AF')}
            <span style="font-size:0.88rem;">Chế độ Offline: Sử dụng bộ từ điển lọc rác và quy tắc bóc tách chức vụ nội bộ không cần API.</span>
        </div>
        """, unsafe_allow_html=True)

    target_criteria = st.text_area(
        "Tiêu chí Khách mục tiêu (ICP)",
        value=saved_cfg.get("target_criteria", "Ưu tiên tìm kiếm: Chủ doanh nghiệp, C-Level (CEO, Founder, Giám đốc), Trưởng phòng kinh doanh/Marketing. Loại bỏ các chức danh đùa cợt hoặc không có công việc rõ ràng."),
        help="Định hướng cho AI hiểu bạn đang nhắm tới tệp khách hàng nào để chấm điểm Lead Tier chính xác."
    )

    batch_size = st.slider("Kích thước gói xử lý (Batch Size)", min_value=10, max_value=50, value=saved_cfg.get("batch_size", 25), step=5)

    if st.button("Lưu Cấu Hình", use_container_width=True):
        cfg = {
            "provider": provider_code,
            "gemini_key": api_key if provider_code == "gemini" else saved_cfg.get("gemini_key", ""),
            "openai_key": api_key if provider_code == "openai" else saved_cfg.get("openai_key", ""),
            "target_criteria": target_criteria,
            "batch_size": batch_size
        }
        save_user_config(cfg)
        st.success("Đã lưu cấu hình thành công!")

    st.markdown("---")
    st.caption("Phiên bản: **1.2.0 Pro**\nTối ưu xử lý danh sách bạn bè 3.000 - 4.000 Friends.")


# ----------------- MAIN HEADER -----------------
st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; margin-bottom: 4px;">
    {get_svg_icon('facebook', 34, '#1877F2')}
    <div class="main-header">Hệ Thống Trích Xuất & Phân Loại Lead Facebook Tự Động</div>
</div>
<div class="sub-header">Tải file danh sách bạn bè cào từ Facebook (CSV / Excel) &rarr; Bấm nút &rarr; AI tự động bóc tách Họ tên, Chức vụ, Công ty, Trường học & Lọc sạch dữ liệu rác chuẩn CRM.</div>
""", unsafe_allow_html=True)

# Tabs
tab_upload, tab_deep_crawl, tab_results, tab_analytics, tab_guide = st.tabs([
    "1. Tải Lên & Xử Lý Nhanh",
    "2. 🔍 Cào Sâu Trang Cá Nhân",
    "3. Bảng Kết Quả & Xuất File",
    "4. Phân Tích Dữ Liệu",
    "5. Hướng Dẫn A-Z"
])

# Initialize session state
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "deep_enriched_df" not in st.session_state:
    st.session_state.deep_enriched_df = None
if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "selected_file_name" not in st.session_state:
    st.session_state.selected_file_name = ""
if "total_files_count" not in st.session_state:
    st.session_state.total_files_count = 0
if "total_before_dedup" not in st.session_state:
    st.session_state.total_before_dedup = 0
if "dupes_removed_count" not in st.session_state:
    st.session_state.dupes_removed_count = 0

# ----------------- TAB 1: UPLOAD & PROCESS -----------------
with tab_upload:
    st.markdown(f"""
    <div class="section-title">
        {get_svg_icon('upload', 20, '#1E3A8A')}
        <span>Tải Lên File Cào Danh Sách Bạn Bè Facebook</span>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Chọn 1 hoặc nhiều file xuất từ Instant Data Scraper (.csv, .xlsx, .xls)",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help="Kéo thả tất cả các file bạn vừa quét (ví dụ quét theo chữ A, B, C... hoặc từng đợt) vào đây. Hệ thống sẽ tự động gộp và loại bỏ trùng lặp 100%!"
    )

    if uploaded_files:
        try:
            dfs = [clean_file_data(f) for f in uploaded_files]
            deduped_df, total_before, dupes_removed = merge_and_deduplicate_dfs(dfs)
            st.session_state.raw_df = deduped_df
            st.session_state.total_files_count = len(uploaded_files)
            st.session_state.total_before_dedup = total_before
            st.session_state.dupes_removed_count = dupes_removed
            
            if len(uploaded_files) == 1:
                st.session_state.selected_file_name = uploaded_files[0].name
            else:
                st.session_state.selected_file_name = f"{len(uploaded_files)} files: " + ", ".join([f.name for f in uploaded_files[:2]]) + ("..." if len(uploaded_files) > 2 else "")
        except Exception as e:
            st.error(f"Lỗi khi đọc file: {e}")

    df_current = st.session_state.raw_df

    if df_current is not None:
        st.markdown("---")
        
        # Display Deduplication Status Banner
        if st.session_state.dupes_removed_count > 0 or st.session_state.total_files_count > 1:
            st.markdown(f"""
            <div class="alert-success">
                {get_svg_icon('check', 22, '#059669')}
                <div>
                    <strong style="font-size:0.98rem;">TỰ ĐỘNG GỘP VÀ KHỬ TRÙNG LẶP THÀNH CÔNG</strong><br>
                    <span>&bull; <b>Số file đã nạp:</b> {st.session_state.total_files_count} file</span><br>
                    <span>&bull; <b>Tổng số dòng gộp lại:</b> {st.session_state.total_before_dedup} dòng</span><br>
                    <span>&bull; <b>Số bạn bè bị quét trùng đã tự động loại bỏ:</b> {st.session_state.dupes_removed_count} dòng (chuẩn hóa theo Link Profile)</span><br>
                    <span>&bull; <b>Dữ liệu bạn bè duy nhất thực tế đưa vào AI:</b> <b>{len(df_current)} người</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; margin: 10px 0;">
                {get_svg_icon('users', 20, '#2563EB')}
                <span style="font-size: 1.1rem; font-weight: 600; color: #1E293B;">Dữ liệu đầu vào: {len(df_current)} người bạn (Nguồn: {st.session_state.selected_file_name})</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Auto-detect columns (Content-Aware, like ChatGPT)
        detected = detect_columns(df_current)
        all_cols = list(df_current.columns)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            name_idx = all_cols.index(detected["name_col"]) if detected.get("name_col") in all_cols else 0
            sel_name_col = st.selectbox("Cột Họ và tên", options=all_cols, index=name_idx, help="Hệ thống đã tự động lọc bỏ các cột ảnh avatar")

        with col_c2:
            link_idx = all_cols.index(detected["link_col"]) if detected.get("link_col") in all_cols else 0
            sel_link_col = st.selectbox("Cột Link Profile Facebook", options=all_cols, index=link_idx, help="Cột chứa đường dẫn facebook.com")

        # Smart multi-select for Info columns
        default_info = [c for c in detected.get("info_cols", []) if c in all_cols and c not in [sel_name_col, sel_link_col]]
        if not default_info and detected.get("info_col") in all_cols and detected.get("info_col") not in [sel_name_col, sel_link_col]:
            default_info = [detected.get("info_col")]

        sel_info_cols = st.multiselect(
            "Các cột chứa Thông tin Công việc / Học vấn / Bạn chung (Tự động gộp dữ liệu như ChatGPT):",
            options=[c for c in all_cols if c not in [sel_name_col, sel_link_col]],
            default=default_info,
            help="Hệ thống sẽ tự động gộp nội dung các cột này lại với nhau (giống như cách ChatGPT đọc toàn bộ dòng) để AI có đầy đủ thông tin nhất."
        )

        if not sel_info_cols:
            st.markdown(f"""
            <div style="background-color:#FEF2F2; border:1px solid #FECACA; border-radius:10px; padding:14px 18px; margin: 12px 0; color:#991B1B;">
                <div style="display:flex; align-items:center; gap:8px; font-weight:700; font-size:1rem; margin-bottom:6px;">
                    {get_svg_icon('shield', 20, '#DC2626')}
                    CẢNH BÁO: FILE NÀY KHÔNG CÓ CỘT THÔNG TIN CÔNG VIỆC / HỌC VẤN!
                </div>
                <div style="font-size:0.9rem; line-height:1.5;">
                    • <b>Hiện trạng file:</b> File bạn vừa nạp chỉ có cột Tên và Link, hoàn toàn không có cột chữ mô tả nào từ Facebook. Nếu bấm xử lý, AI sẽ không có dữ liệu để đọc.<br>
                    • <b>Nguyên nhân 1:</b> Khi quét bằng Instant Data Scraper, tool đã bắt nhầm khung bảng con. Hãy bấm nút <b>"Try another table"</b> trên tiện ích để chọn khung to bao quát cả dòng công việc.<br>
                    • <b>Nguyên nhân 2:</b> Trên màn hình Facebook bạn vừa quét, tài khoản đó chỉ hiện chữ "X bạn chung" chứ Facebook không hiển thị dòng học vấn/công việc ra ngoài danh sách bạn bè.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("Xem trước dữ liệu chuẩn bị gửi cho AI (5 người đầu tiên)"):
            preview_rows = []
            for idx, r in df_current.head(5).iterrows():
                nm = str(r.get(sel_name_col, "")).strip() if pd.notna(r.get(sel_name_col)) else ""
                lk = str(r.get(sel_link_col, "")).strip() if pd.notna(r.get(sel_link_col)) else ""
                inf_parts = []
                for c in sel_info_cols:
                    if c in df_current.columns and pd.notna(r.get(c)):
                        v = str(r.get(c, "")).strip()
                        if v and v.lower() != "nan" and not v.startswith("http"):
                            inf_parts.append(v)
                preview_rows.append({
                    "Họ và tên": nm,
                    "Link Facebook": lk,
                    "Thông tin gộp gửi cho AI": " · ".join(inf_parts) if inf_parts else "(Không có mô tả công việc)"
                })
            st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Process Trigger Button
        btn_col1, btn_col2 = st.columns([2, 3])
        with btn_col1:
            start_btn = st.button("BẮT ĐẦU XỬ LÝ & BÓC TÁCH DỮ LIỆU", type="primary", use_container_width=True)

        if start_btn:
            if provider_code != "offline" and not api_key:
                st.warning("Bạn chưa nhập API Key. Hệ thống sẽ tự động chuyển sang chế độ Offline (sử dụng bộ quy tắc nội bộ) để xử lý dữ liệu cho bạn.")
                eff_provider = "offline"
                eff_key = None
            else:
                eff_provider = provider_code
                eff_key = api_key

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(done, total):
                pct = int((done / total) * 100)
                progress_bar.progress(pct)
                status_text.text(f"Đang xử lý: {done}/{total} người bạn ({pct}%)...")

            try:
                start_time = time.time()
                status_text.text("Đang khởi động phân tích lô dữ liệu...")
                
                processed_results = process_friends_dataframe(
                    df=df_current,
                    name_col=sel_name_col,
                    link_col=sel_link_col,
                    info_cols=sel_info_cols,
                    api_key=eff_key,
                    api_provider=eff_provider,
                    model_name=model_name,
                    target_criteria=target_criteria,
                    batch_size=batch_size,
                    progress_callback=update_progress
                )
                
                elapsed = round(time.time() - start_time, 1)
                st.session_state.processed_df = processed_results
                progress_bar.progress(100)
                status_text.success(f"Hoàn tất xử lý {len(processed_results)} người bạn trong {elapsed} giây!")
                st.info("Hãy chuyển sang Tab 3 (Bảng Kết Quả & Xuất File) để lọc và tải file Excel về máy!")

            except Exception as e:
                st.error(f"Xảy ra lỗi trong quá trình xử lý: {str(e)}")

# ----------------- TAB 2: DEEP PROFILE CRAWLER -----------------
with tab_deep_crawl:
    st.markdown(f"""
    <div class="section-title">
        {get_svg_icon('search', 20, '#1E3A8A')}
        <span>Cào Sâu Thông Tin Công Việc & Học Vấn Từ Trang Cá Nhân</span>
    </div>
    <div style="font-size:0.95rem; color:#4B5563; margin-bottom:15px; line-height:1.5;">
        Dành cho các trường hợp danh sách bạn bè cào về <b>chỉ hiện chữ "X bạn chung"</b> mà không có cột thông tin công việc.<br>
        Tính năng này sẽ sử dụng trình duyệt để <b>tự động mở trực tiếp tab Giới thiệu</b> (Công việc & Học vấn) của từng người trên Facebook để lấy sạch thông tin họ cài đặt.
    </div>
    """, unsafe_allow_html=True)

    # Status of login
    session_exists = os.path.exists(CHROME_PROFILE_DIR) and len(os.listdir(CHROME_PROFILE_DIR)) > 0
    if not session_exists:
        st.markdown(f"""
        <div style="background-color:#FFFBEB; border:1px solid #FDE68A; border-radius:10px; padding:14px 18px; margin-bottom:15px; color:#92400E;">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">
                {get_svg_icon('shield', 18, '#D97706')} LƯU Ý QUAN TRỌNG: CẦN LƯU PHIÊN ĐĂNG NHẬP FACEBOOK TRƯỚC
            </div>
            <div style="font-size:0.9rem; line-height:1.5;">
                Để cào được đầy đủ thông tin của bạn bè, bạn cần đăng nhập Facebook 1 lần duy nhất trên máy tính:<br>
                1. Hãy nháy đúp chuột vào file: <b><code>Dang_Nhap_Facebook.bat</code></b> trong thư mục phần mềm.<br>
                2. Đăng nhập tài khoản Facebook của bạn (tài khoản clone hoặc nick chính).<br>
                3. Sau khi vào được bảng tin Facebook, đóng cửa sổ trình duyệt đó lại. Trình duyệt sẽ nhớ phiên đăng nhập vĩnh viễn!
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-success" style="margin-bottom:15px;">
            {get_svg_icon('check', 18, '#059669')}
            <span style="font-size:0.92rem;"><b>Đã sẵn sàng phiên trình duyệt:</b> Trình duyệt đã có dữ liệu đăng nhập, sẵn sàng cào sâu thông tin trang cá nhân của bạn bè.</span>
        </div>
        """, unsafe_allow_html=True)

    # Determine input dataframe for deep crawling
    df_for_deep = None
    if st.session_state.raw_df is not None:
        df_for_deep = st.session_state.raw_df
        st.info(f"Đang sử dụng dữ liệu từ file vừa nạp: **{len(df_for_deep)} người bạn** ({st.session_state.selected_file_name}).")
    else:
        deep_upload = st.file_uploader(
            "Hoặc nạp file CSV / Excel chứa danh sách Link Profile Facebook:",
            type=["csv", "xlsx", "xls"],
            key="deep_crawler_upload"
        )
        if deep_upload:
            df_for_deep = clean_file_data(deep_upload)

    if df_for_deep is not None:
        detected_deep = detect_columns(df_for_deep)
        all_cols_deep = list(df_for_deep.columns)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            name_idx_d = all_cols_deep.index(detected_deep["name_col"]) if detected_deep.get("name_col") in all_cols_deep else 0
            deep_name_col = st.selectbox("Cột Họ và tên", options=all_cols_deep, index=name_idx_d, key="deep_sel_name")
        with col_d2:
            link_idx_d = all_cols_deep.index(detected_deep["link_col"]) if detected_deep.get("link_col") in all_cols_deep else 0
            deep_link_col = st.selectbox("Cột Link Profile Facebook", options=all_cols_deep, index=link_idx_d, key="deep_sel_link")

        # Crawler Settings
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            crawl_limit = st.number_input(
                "Số lượng profile muốn cào sâu",
                min_value=1,
                max_value=len(df_for_deep),
                value=min(len(df_for_deep), 50),
                step=5,
                help="Nên cào mỗi đợt từ 20 đến 50 người để đảm bảo an toàn tuyệt đối cho tài khoản."
            )
        with col_s2:
            crawl_delay = st.slider(
                "Độ trễ an toàn giữa các profile (giây)",
                min_value=2.0,
                max_value=6.0,
                value=3.5,
                step=0.5,
                help="Mô phỏng hành vi người thật xem trang cá nhân (3.5s là mức chuẩn an toàn)."
            )
        with col_s3:
            crawl_headless = st.checkbox("Chạy ẩn (Headless)", value=True, help="Bỏ tích nếu bạn muốn nhìn thấy cửa sổ trình duyệt tự động mở và lướt qua từng trang cá nhân.")

        if st.button("🚀 BẮT ĐẦU CÀO SÂU CÔNG VIỆC & HỌC VẤN", type="primary", use_container_width=True):
            p_bar_deep = st.progress(0)
            status_deep = st.empty()

            def deep_cb(current, total, msg):
                pct = int((current / total) * 100) if total > 0 else 0
                p_bar_deep.progress(min(pct, 100))
                status_deep.text(msg)

            try:
                start_deep_t = time.time()
                status_deep.text("Đang khởi động trình duyệt tự động...")
                enriched_res = run_deep_profile_crawl(
                    df=df_for_deep,
                    link_col=deep_link_col,
                    name_col=deep_name_col,
                    max_count=int(crawl_limit),
                    delay_seconds=float(crawl_delay),
                    headless=crawl_headless,
                    progress_callback=deep_cb
                )
                st.session_state.deep_enriched_df = enriched_res
                p_bar_deep.progress(100)
                dur = round(time.time() - start_deep_t, 1)
                status_deep.success(f"Hoàn tất cào sâu thông tin cho {crawl_limit} profile trong {dur} giây!")
            except Exception as e:
                st.error(f"Lỗi khi cào sâu profile: {e}")

        # If we have deep enriched results
        if st.session_state.get("deep_enriched_df") is not None:
            res_deep_df = st.session_state.deep_enriched_df
            st.markdown("---")
            st.markdown("##### 📋 Kết quả cào sâu trực tiếp từ trang cá nhân:")
            st.dataframe(
                res_deep_df[[deep_name_col, deep_link_col, "Thông tin cào sâu"]].head(int(crawl_limit) if 'crawl_limit' in locals() else 50),
                use_container_width=True
            )

            # Button to send immediately to AI
            if st.button("🤖 CHUYỂN DỮ LIỆU NÀY CHO AI BÓC TÁCH & PHÂN LOẠI CRM NGAY", type="primary", use_container_width=True):
                # Run AI on this enriched dataframe
                ai_p_bar = st.progress(0)
                ai_status = st.empty()

                def update_deep_ai_p(done, total):
                    pct = int((done / total) * 100)
                    ai_p_bar.progress(pct)
                    ai_status.text(f"AI đang bóc tách: {done}/{total} người ({pct}%)...")

                eff_provider = provider_code if api_key else "offline"
                eff_key = api_key if api_key else None

                sub_df = res_deep_df.head(int(crawl_limit) if 'crawl_limit' in locals() else len(res_deep_df))
                ai_output = process_friends_dataframe(
                    df=sub_df,
                    name_col=deep_name_col,
                    link_col=deep_link_col,
                    info_cols=["Thông tin cào sâu"],
                    api_key=eff_key,
                    api_provider=eff_provider,
                    model_name=model_name,
                    target_criteria=target_criteria,
                    batch_size=batch_size,
                    progress_callback=update_deep_ai_p
                )
                st.session_state.processed_df = ai_output
                ai_p_bar.progress(100)
                ai_status.success("Đã hoàn tất phân loại CRM bằng AI! Hãy chuyển sang Tab 3 (Bảng Kết Quả & Xuất File) để xem và tải Excel!")

# ----------------- TAB 3: RESULTS & EXPORT -----------------
with tab_results:
    if st.session_state.processed_df is None:
        st.markdown(f"""
        <div class="alert-info">
            {get_svg_icon('table', 20, '#1E40AF')}
            <span>Chưa có dữ liệu xử lý. Vui lòng tải file và bấm nút 'Bắt đầu xử lý' ở Tab 1 trước.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        res_df = st.session_state.processed_df.copy()

        # Summary KPIs
        total_leads = len(res_df)
        high_potential = len(res_df[res_df["Phân loại Lead"] == "Tiềm năng cao"])
        mid_potential = len(res_df[res_df["Phân loại Lead"] == "Tiềm năng trung bình"])
        trash_count = len(res_df[res_df["Đánh giá"].str.contains("Rác", na=False)])
        valid_count = len(res_df[res_df["Đánh giá"] == "Hợp lệ"])

        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">{get_svg_icon("users", 18, "#2563EB")} <span>TỔNG QUÉT</span></div>
                <div class="metric-val">{total_leads}</div>
            </div>
            ''', unsafe_allow_html=True)
        with kpi2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">{get_svg_icon("star", 18, "#059669")} <span>TIỀM NĂNG CAO</span></div>
                <div class="metric-val val-green">{high_potential}</div>
            </div>
            ''', unsafe_allow_html=True)
        with kpi3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">{get_svg_icon("briefcase", 18, "#0284C7")} <span>TIỀM NĂNG TRUNG BÌNH</span></div>
                <div class="metric-val val-blue">{mid_potential}</div>
            </div>
            ''', unsafe_allow_html=True)
        with kpi4:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">{get_svg_icon("check", 18, "#D97706")} <span>HỢP LỆ</span></div>
                <div class="metric-val val-amber">{valid_count}</div>
            </div>
            ''', unsafe_allow_html=True)
        with kpi5:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">{get_svg_icon("trash", 18, "#DC2626")} <span>RÁC / ĐÙA CỢT</span></div>
                <div class="metric-val val-red">{trash_count}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("---")

        # Filters
        st.markdown(f'''
        <div class="section-title">
            {get_svg_icon("filter", 20, "#1E3A8A")}
            <span>Bộ Lọc Nhanh Dữ Liệu</span>
        </div>
        ''', unsafe_allow_html=True)
        
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        with f_col1:
            tier_options = ["Tất cả"] + list(res_df["Phân loại Lead"].unique())
            sel_tier = st.selectbox("Phân loại Lead", options=tier_options, index=0)

        with f_col2:
            status_options = ["Tất cả"] + list(res_df["Đánh giá"].unique())
            sel_status = st.selectbox("Đánh giá dữ liệu", options=status_options, index=0)

        with f_col3:
            level_options = ["Tất cả"] + list(res_df["Cấp bậc"].unique())
            sel_level = st.selectbox("Cấp bậc chức vụ", options=level_options, index=0)

        with f_col4:
            search_kw = st.text_input("Tìm kiếm (Tên, Công ty, Ngành, Trường)", value="", placeholder="Nhập từ khóa...")

        # Apply Filters
        filtered_df = res_df.copy()
        if sel_tier != "Tất cả":
            filtered_df = filtered_df[filtered_df["Phân loại Lead"] == sel_tier]
        if sel_status != "Tất cả":
            filtered_df = filtered_df[filtered_df["Đánh giá"] == sel_status]
        if sel_level != "Tất cả":
            filtered_df = filtered_df[filtered_df["Cấp bậc"] == sel_level]
        if search_kw.strip():
            kw = search_kw.strip().lower()
            filtered_df = filtered_df[
                filtered_df["Họ và tên"].str.lower().str.contains(kw, na=False) |
                filtered_df["Tên công ty / Đơn vị"].str.lower().str.contains(kw, na=False) |
                (filtered_df["Tên công ty chuẩn hóa"].str.lower().str.contains(kw, na=False) if "Tên công ty chuẩn hóa" in filtered_df.columns else False) |
                (filtered_df["Trường học / Học vấn"].str.lower().str.contains(kw, na=False) if "Trường học / Học vấn" in filtered_df.columns else False) |
                filtered_df["Chức vụ"].str.lower().str.contains(kw, na=False) |
                filtered_df["Lĩnh vực / Ngành nghề"].str.lower().str.contains(kw, na=False)
            ]

        st.write(f"Hiển thị **{len(filtered_df)}** / {len(res_df)} kết quả phù hợp:")

        # Interactive Data Table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "Link Facebook": st.column_config.LinkColumn("Link Facebook", display_text="Mở Profile FB")
            }
        )

        st.markdown("---")
        st.markdown(f'''
        <div class="section-title">
            {get_svg_icon("download", 20, "#1E3A8A")}
            <span>Xuất Dữ Liệu</span>
        </div>
        ''', unsafe_allow_html=True)

        # Export buttons
        exp_col1, exp_col2, _ = st.columns([2, 2, 4])
        
        # Generate styled Excel in memory (multi-user safe)
        excel_bytes = export_styled_excel(filtered_df)

        with exp_col1:
            st.download_button(
                label="Tải File Excel Chuẩn CRM (.xlsx)",
                data=excel_bytes,
                file_name="facebook_leads_crm.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )

        with exp_col2:
            csv_data = filtered_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="Tải File CSV (.csv)",
                data=csv_data,
                file_name="facebook_leads.csv",
                mime="text/csv",
                use_container_width=True
            )

# ----------------- TAB 4: ANALYTICS -----------------
with tab_analytics:
    if st.session_state.processed_df is None:
        st.markdown(f"""
        <div class="alert-info">
            {get_svg_icon('chart', 20, '#1E40AF')}
            <span>Vui lòng xử lý dữ liệu trước để xem biểu đồ phân tích.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        df_an = st.session_state.processed_df

        an_col1, an_col2 = st.columns(2)
        with an_col1:
            st.markdown(f'''
            <div class="section-title">
                {get_svg_icon("chart", 18, "#1E3A8A")}
                <span>Phân Bổ Cấp Bậc</span>
            </div>
            ''', unsafe_allow_html=True)
            level_counts = df_an["Cấp bậc"].value_counts().reset_index()
            level_counts.columns = ["Cấp bậc", "Số lượng"]
            st.bar_chart(data=level_counts, x="Cấp bậc", y="Số lượng")

        with an_col2:
            st.markdown(f'''
            <div class="section-title">
                {get_svg_icon("target", 18, "#1E3A8A")}
                <span>Phân Bổ Tầng Lead</span>
            </div>
            ''', unsafe_allow_html=True)
            tier_counts = df_an["Phân loại Lead"].value_counts().reset_index()
            tier_counts.columns = ["Phân loại Lead", "Số lượng"]
            st.bar_chart(data=tier_counts, x="Phân loại Lead", y="Số lượng")

        st.markdown(f'''
        <div class="section-title">
            {get_svg_icon("building", 18, "#1E3A8A")}
            <span>Phân Bổ Ngành Nghề / Lĩnh Vực</span>
        </div>
        ''', unsafe_allow_html=True)
        ind_counts = df_an[df_an["Lĩnh vực / Ngành nghề"] != "Không rõ"]["Lĩnh vực / Ngành nghề"].value_counts().reset_index()
        ind_counts.columns = ["Lĩnh vực", "Số lượng"]
        if not ind_counts.empty:
            st.bar_chart(data=ind_counts, x="Lĩnh vực", y="Số lượng")
        else:
            st.write("Chưa có đủ thông tin ngành nghề chi tiết.")

# ----------------- TAB 5: STEP-BY-STEP GUIDE & SAFE SCALING -----------------
with tab_guide:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
        {get_svg_icon('shield', 26, '#1E3A8A')}
        <h3 style="margin:0; font-size:1.35rem; font-weight:700; color:#1E3A8A;">Chiến Lược Triển Khai Thực Chiến (Từ Clone đến Nick Chính 3k - 4k Friends)</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
Hệ thống được thiết kế theo đúng mô hình 4 bước tối ưu của bạn:

---

#### Bước 1: Chuẩn bị tài khoản Clone thử nghiệm
1. **Kết bạn thử nghiệm:** Tài khoản clone chỉ cần có từ 50 - 100 bạn bè có cập nhật phần Giới thiệu / Công việc.
2. **Môi trường cách ly:** Đăng nhập nick clone trên một Profile Chrome riêng biệt (hoặc trình duyệt phụ) để tránh dính cookie hoặc liên đới IP tài khoản chính A và B.

---

#### Bước 2: Cào dữ liệu bằng Instant Data Scraper (Miễn phí 100%)
1. Cài đặt tiện ích **Instant Data Scraper** từ Chrome Web Store.
2. Truy cập: `https://www.facebook.com/me/friends` trên profile clone.
3. Bấm icon Instant Data Scraper trên thanh công cụ trình duyệt.
4. **Cài đặt tốc độ (Delay):**
   - **Min delay:** `2.5s`
   - **Max delay:** `4.0s`
   *(Mức delay này mô phỏng hành vi cuộn chuột tự nhiên của người thật, an toàn tuyệt đối).*
5. Bấm **Start Crawling** -> Sau khi cuộn xong, bấm nút **XLSX** hoặc **CSV** để tải file về máy.

---

#### Bước 3: Đưa file vào Hệ Thống AI tự động (Không cần copy paste thủ công)
- Mở hệ thống này (giao diện web).
- Kéo thả file vừa tải về vào **Tab 1: Tải Lên & Xử Lý**.
- Hệ thống sẽ tự động khớp cột Tên, Link Profile, Thông tin công việc & Trường học.
- Bấm nút: **BẮT ĐẦU XỬ LÝ & BÓC TÁCH DỮ LIỆU**.
- AI sẽ chia thành từng gói 25 người, bóc tách và phân loại thành:
  - **Họ và tên**
  - **Chức vụ (Job Title)**
  - **Tên công ty (Company)**
  - **Tên công ty chuẩn hóa**
  - **Trường học / Học vấn**
  - **Cấp bậc (C-Level / Quản lý / Chuyên viên / Sinh viên...)**
  - **Ngành nghề**
  - **Đánh giá Hợp lệ hay Rác**
  - **Điểm tiềm năng (Lead Tier)**

---

#### Bước 4: Mẹo Quét Chia Nhỏ (Theo Bảng Chữ Cái) & Khử Trùng Lặp Tự Động
Khi tài khoản có 3.000 – 4.000 bạn bè, trình duyệt chắc chắn sẽ bị đơ/lag nếu cuộn liên tục. Vì vậy:

1. **Cách chia nhỏ tối ưu nhất (Theo bảng chữ cái):**
   - Vào ô **Tìm kiếm bạn bè** trong danh sách bạn bè Facebook.
   - Gõ chữ **"A"** -> Facebook chỉ hiện bạn bè có chữ A -> Bật tool quét -> Tải về `A.xlsx`.
   - Gõ chữ **"B"** -> Bật tool quét -> Tải về `B.xlsx`.
   - Làm tương tự với các ký tự chính (*A, B, C, D, Đ, G, H, K, L, M, N, P, Q, S, T, V*).

2. **Khử trùng lặp tự động 100% (Không cần làm thủ công trong Excel):**
   - Chắc chắn giữa các file `A.xlsx`, `B.xlsx` sẽ có người bị trùng (ví dụ tên Nguyễn Văn A có cả chữ A và B).
   - Bạn **KHÔNG CẦN** mở Excel ra copy paste rồi bấm Remove Duplicates!
   - Chỉ cần **chọn tất cả các file đó kéo thả vào Tab 1 cùng một lúc**: Hệ thống sẽ tự động gộp tất cả các file, chuẩn hóa đường link profile Facebook và **xóa sạch 100% những người bị quét trùng lặp** trước khi đưa vào AI!
   - Giúp bạn tiết kiệm 100% token AI và tiết kiệm thời gian lọc thủ công.

---

#### Bước 5: Nguyên Tắc An Toàn Tài Khoản Chính A & B (Chống Checkpoint)
- **Cài đặt Delay an toàn:** Đặt **Min delay: 3.0s** và **Max delay: 5.0s**.
- **Không cào quá dồn dập:** Mỗi buổi cào 5-7 chữ cái (khoảng 800 - 1.000 người), chia làm 2-3 ngày là xong toàn bộ 4.000 bạn bè an toàn tuyệt đối.
- **Chi phí AI:** 3.000 bạn bè khi chia lô 25 người = ~120 requests. Với **Gemini Flash (Free tier của Google)**, bạn xử lý toàn bộ danh sách bạn bè với chi phí **0 ĐỒNG**!
""")
