import os
import json
import time
import pandas as pd
import streamlit as st
import importlib
import fb_processor
import fb_deep_crawler
import linkedin_matcher
importlib.reload(fb_processor)
importlib.reload(fb_deep_crawler)
importlib.reload(linkedin_matcher)
from fb_processor import (
    detect_columns,
    clean_file_data,
    process_friends_dataframe,
    export_styled_excel,
    merge_and_deduplicate_dfs,
    clean_and_reorder_crm_dataframe,
    map_to_info_completeness
)
from fb_deep_crawler import run_deep_profile_crawl, CHROME_PROFILE_DIR

@st.cache_resource
def ensure_cloud_playwright():
    import platform
    import sys
    import subprocess
    if platform.system() == "Linux":
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True, timeout=180)
        except Exception:
            pass
    return True

ensure_cloud_playwright()

# Page configuration
st.set_page_config(
    page_title="AI FB Lead Extractor - Phân Loại Bạn Bè Facebook",
    page_icon="https://img.icons8.com/color/96/facebook-new.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- UNIFIED SVG ICON ENGINE -----------------
def get_svg_icon(name: str, size: int = 18, color: str = "currentColor", extra_style: str = "") -> str:
    """Returns a clean, unified Lucide vector SVG icon with consistent stroke and geometry."""
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
        "check": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><polyline points="20 6 9 17 4 12"></polyline></svg>',
        "check_circle": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        "x_circle": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
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
        "external": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>',
        "key": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><circle cx="7.5" cy="15.5" r="5.5"></circle><path d="m21 2-9.6 9.6"></path><path d="m15.5 7.5 3 3L22 7l-3-3"></path></svg>',
        "bot": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><rect x="4" y="4" width="16" height="16" rx="2"></rect><rect x="9" y="9" width="6" height="6"></rect><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"></path></svg>',
        "rocket": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"></path><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"></path><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"></path><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"></path></svg>',
        "lightbulb": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"></path><path d="M9 18h6"></path><path d="M10 22h4"></path></svg>',
        "clipboard": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><rect width="14" height="18" x="5" y="4" rx="2"></rect><path d="M8 4V2a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><path d="M9 9h6M9 13h6M9 17h4"></path></svg>',
        "sparkles": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path></svg>',
        "info": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {style_attr}><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>',
        "linkedin": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{color}" {style_attr}><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>'
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
        gap: 8px;
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
        gap: 10px;
        font-size: 1.18rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-top: 14px;
        margin-bottom: 12px;
    }
    .icon-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 9px;
        flex-shrink: 0;
    }
    .icon-pill-sm {
        width: 24px;
        height: 24px;
        border-radius: 6px;
    }
    .icon-pill-lg {
        width: 40px;
        height: 40px;
        border-radius: 10px;
    }
    .icon-pill-blue { background: #EFF6FF; border: 1px solid #BFDBFE; color: #2563EB; }
    .icon-pill-emerald { background: #ECFDF5; border: 1px solid #A7F3D0; color: #059669; }
    .icon-pill-amber { background: #FFFBEB; border: 1px solid #FDE68A; color: #D97706; }
    .icon-pill-purple { background: #F5F3FF; border: 1px solid #DDD6FE; color: #7C3AED; }
    .icon-pill-rose { background: #FEF2F2; border: 1px solid #FECACA; color: #DC2626; }
    .icon-pill-slate { background: #F8FAFC; border: 1px solid #E2E8F0; color: #475569; }
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
        gap: 12px;
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
            if "FB_COOKIE" in st.secrets:
                cfg["fb_cookie"] = st.secrets["FB_COOKIE"]
    except Exception:
        pass

    # 2. Environment Variables
    if os.getenv("GEMINI_API_KEY") and not cfg.get("gemini_key"):
        cfg["gemini_key"] = os.getenv("GEMINI_API_KEY")
    if os.getenv("OPENAI_API_KEY") and not cfg.get("openai_key"):
        cfg["openai_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("FB_COOKIE") and not cfg.get("fb_cookie"):
        cfg["fb_cookie"] = os.getenv("FB_COOKIE")

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

AUTO_SAVE_CRM_FILE = "crm_leads_autosave.csv"
AUTO_SAVE_DEEP_FILE = "deep_crawl_autosave.csv"

def load_autosaved_data():
    crm_df = None
    deep_df = None
    if os.path.exists(AUTO_SAVE_CRM_FILE):
        try:
            crm_df = pd.read_csv(AUTO_SAVE_CRM_FILE, encoding="utf-8-sig")
            if not crm_df.empty:
                crm_df = clean_and_reorder_crm_dataframe(crm_df)
            else:
                crm_df = None
        except Exception:
            crm_df = None

    if os.path.exists(AUTO_SAVE_DEEP_FILE):
        try:
            deep_df = pd.read_csv(AUTO_SAVE_DEEP_FILE, encoding="utf-8-sig")
            if deep_df.empty:
                deep_df = None
        except Exception:
            deep_df = None

    return crm_df, deep_df

def save_crm_autosave(df: pd.DataFrame):
    if df is not None and not df.empty:
        try:
            cleaned = clean_and_reorder_crm_dataframe(df)
            cleaned.to_csv(AUTO_SAVE_CRM_FILE, index=False, encoding="utf-8-sig")
        except Exception:
            pass

def save_deep_autosave(df: pd.DataFrame):
    if df is not None and not df.empty:
        try:
            df.to_csv(AUTO_SAVE_DEEP_FILE, index=False, encoding="utf-8-sig")
        except Exception:
            pass

def clear_autosaved_data():
    for f in [AUTO_SAVE_CRM_FILE, AUTO_SAVE_DEEP_FILE]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

def style_dataframe_with_linkedin(df: pd.DataFrame):
    """
    Applies bold styling, dark green text and mint green background
    to all rows that have a valid LinkedIn profile URL.
    """
    if df is None or df.empty or "Link LinkedIn" not in df.columns:
        return df

    def _highlight_linkedin_row(row):
        has_li = "linkedin.com/in" in str(row.get("Link LinkedIn", ""))
        if has_li:
            return ["background-color: #DCFCE7; color: #14532D; font-weight: 700;"] * len(row)
        else:
            return ["background-color: #FFFFFF; color: #4B5563; font-weight: 400;"] * len(row)

    return df.style.apply(_highlight_linkedin_row, axis=1)

saved_cfg = load_saved_config()

# Initialize session state & restore autosaved progress
auto_crm, auto_deep = load_autosaved_data()

if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "deep_enriched_df" not in st.session_state:
    st.session_state.deep_enriched_df = auto_deep
if "processed_df" not in st.session_state:
    st.session_state.processed_df = auto_crm
if "selected_file_name" not in st.session_state:
    st.session_state.selected_file_name = ""
if "total_files_count" not in st.session_state:
    st.session_state.total_files_count = 0
if "total_before_dedup" not in st.session_state:
    st.session_state.total_before_dedup = 0
if "dupes_removed_count" not in st.session_state:
    st.session_state.dupes_removed_count = 0

# ----------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom: 14px;">
        <span class="icon-pill icon-pill-blue">{get_svg_icon('settings', 18, '#2563EB')}</span>
        <span style="font-size: 1.15rem; font-weight: 700; color: #1E3A8A;">Cấu Hình Hệ Thống</span>
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
            ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"],
            index=0,
            help="gemini-2.5-flash-lite là model thế hệ mới tốc độ cao, hạn mức quota lớn nhất, không bị nghẽn 429."
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
            <span class="icon-pill icon-pill-blue" style="width:26px; height:26px;">{get_svg_icon('shield', 14, '#1E40AF')}</span>
            <span style="font-size:0.88rem;">Chế độ Offline: Sử dụng bộ từ điển lọc rác và quy tắc bóc tách chức vụ nội bộ không cần API.</span>
        </div>
        """, unsafe_allow_html=True)

    target_criteria = st.text_area(
        "Tiêu chí Khách mục tiêu (ICP)",
        value=saved_cfg.get("target_criteria", "Ưu tiên tìm kiếm: Chủ doanh nghiệp, C-Level (CEO, Founder, Giám đốc), Trưởng phòng kinh doanh/Marketing. Loại bỏ các chức danh đùa cợt hoặc không có công việc rõ ràng."),
        help="Định hướng cho AI hiểu bạn đang nhắm tới tệp khách hàng nào để chấm điểm Lead Tier chính xác."
    )

    batch_size = st.slider("Kích thước gói xử lý (Batch Size)", min_value=10, max_value=50, value=saved_cfg.get("batch_size", 25), step=5)

    serper_api_key = st.text_input(
        "Serper API Key (Tìm Google / LinkedIn)",
        value=saved_cfg.get("serper_key", ""),
        type="password",
        help="Dùng để tự động tìm kiếm Profile LinkedIn trên Google. Đăng ký nhận 2.500 lượt tìm kiếm miễn phí tại serper.dev"
    )
    if serper_api_key and serper_api_key.strip() != saved_cfg.get("serper_key", ""):
        saved_cfg["serper_key"] = serper_api_key.strip()
        save_user_config(saved_cfg)
    st.markdown(
        f"<a href='https://serper.dev/signup' target='_blank' style='text-decoration:none; color:#2563EB; font-weight:600; font-size:0.85rem;'>"
        f"{get_svg_icon('external', 13, '#2563EB')} Lấy Serper API Key miễn phí (2.500 lượt)</a>",
        unsafe_allow_html=True
    )

    if st.button("Lưu Cấu Hình", use_container_width=True):
        cfg = {
            "provider": provider_code,
            "gemini_key": api_key if provider_code == "gemini" else saved_cfg.get("gemini_key", ""),
            "openai_key": api_key if provider_code == "openai" else saved_cfg.get("openai_key", ""),
            "serper_key": serper_api_key.strip() if serper_api_key else saved_cfg.get("serper_key", ""),
            "target_criteria": target_criteria,
            "batch_size": batch_size,
            "fb_cookie": saved_cfg.get("fb_cookie", "")
        }
        save_user_config(cfg)
        st.success("Đã lưu cấu hình thành công!")

    # Auto-save & Local Database manager
    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:0.92rem; font-weight:700; color:#1E3A8A; margin-bottom:8px; display:flex; align-items:center; gap:8px;">
        <span class="icon-pill icon-pill-emerald icon-pill-sm">{get_svg_icon('save', 14, '#059669')}</span>
        <span>Bộ Nhớ Tự Động Lưu</span>
    </div>
    """, unsafe_allow_html=True)
    
    current_leads_count = len(st.session_state.processed_df) if st.session_state.processed_df is not None else 0
    if current_leads_count > 0:
        st.markdown(f"""
        <div style="background-color:#F0FDF4; border:1px solid #BBF7D0; border-radius:6px; padding:6px 10px; font-size:0.83rem; color:#166534; margin-bottom:8px;">
            Đã lưu an toàn <b>{current_leads_count} khách hàng</b> trên ổ cứng (tắt máy mở lại vẫn còn nguyên).
        </div>
        """, unsafe_allow_html=True)
        if st.button("Xóa bộ nhớ để làm tệp mới", type="secondary", use_container_width=True):
            clear_autosaved_data()
            st.session_state.processed_df = None
            st.session_state.deep_enriched_df = None
            st.rerun()
    else:
        st.caption("Dữ liệu bóc tách được sẽ tự động lưu vĩnh viễn trên ổ cứng máy tính.")

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
tab_upload, tab_deep_crawl, tab_results, tab_linkedin, tab_analytics, tab_guide = st.tabs([
    "1. Nạp File & Phân Tích",
    "2. Cào Sâu Trang Cá Nhân",
    "3. Bảng Kết Quả CRM",
    "4. Ghép Nối LinkedIn",
    "5. Biểu Đồ Phân Tích",
    "6. Hướng Dẫn Sử Dụng"
])



# ----------------- TAB 1: UPLOAD & PROCESS -----------------
with tab_upload:
    st.markdown(f"""
    <div class="section-title">
        <span class="icon-pill icon-pill-blue">{get_svg_icon('upload', 18, '#2563EB')}</span>
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
                <span class="icon-pill icon-pill-emerald">{get_svg_icon('check_circle', 18, '#059669')}</span>
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
            <div style="display:flex; align-items:center; gap:10px; margin: 10px 0;">
                <span class="icon-pill icon-pill-blue">{get_svg_icon('users', 18, '#2563EB')}</span>
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
                <div style="display:flex; align-items:center; gap:10px; font-weight:700; font-size:1rem; margin-bottom:6px;">
                    <span class="icon-pill icon-pill-rose">{get_svg_icon('shield', 18, '#DC2626')}</span>
                    <span>CẢNH BÁO: FILE NÀY KHÔNG CÓ CỘT THÔNG TIN CÔNG VIỆC / HỌC VẤN!</span>
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
                save_crm_autosave(processed_results)
                progress_bar.progress(100)
                status_text.success(f"Hoàn tất xử lý {len(processed_results)} người bạn trong {elapsed} giây (Đã tự động lưu an toàn vào máy)!")
                st.info("Hãy chuyển sang Tab 3 (Bảng Kết Quả & Xuất File) để lọc và tải file Excel về máy!")

            except Exception as e:
                st.error(f"Xảy ra lỗi trong quá trình xử lý: {str(e)}")

# ----------------- TAB 2: DEEP PROFILE CRAWLER -----------------
with tab_deep_crawl:
    st.markdown(f"""
    <div class="section-title">
        <span class="icon-pill icon-pill-blue">{get_svg_icon('search', 20, '#2563EB')}</span>
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
            <div style="display:flex; align-items:center; gap:10px; font-weight:700; font-size:1rem; margin-bottom:6px;">
                <span class="icon-pill icon-pill-amber">{get_svg_icon('shield', 18, '#D97706')}</span>
                <span>LƯU Ý QUAN TRỌNG: CẦN LƯU PHIÊN ĐĂNG NHẬP FACEBOOK TRƯỚC</span>
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
        <div class="alert-success" style="margin-bottom:12px;">
            <span class="icon-pill icon-pill-emerald">{get_svg_icon('check_circle', 18, '#059669')}</span>
            <span style="font-size:0.92rem;"><b>Đã sẵn sàng phiên trình duyệt:</b> Trình duyệt đã có dữ liệu đăng nhập, sẵn sàng cào sâu thông tin trang cá nhân của bạn bè.</span>
        </div>
        <div style="background-color:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:10px 14px; margin-bottom:15px; font-size:0.88rem; color:#1E40AF; display:flex; align-items:center; gap:10px;">
            <span class="icon-pill icon-pill-blue" style="width:26px; height:26px;">{get_svg_icon('lightbulb', 16, '#2563EB')}</span>
            <span><b>Mẹo quan trọng:</b> Hãy đảm bảo bạn đã <b>TẮT cửa sổ Chrome đăng nhập</b> (nếu trước đó có mở bằng <code>Dang_Nhap_Facebook.bat</code>) trước khi bấm cào sâu, vì Chrome chỉ cho phép một ứng dụng mở phiên tại một thời điểm.</span>
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

        # Smart start index suggestion based on previously saved progress
        suggested_start = 1
        if st.session_state.get("processed_df") is not None and not st.session_state.processed_df.empty:
            suggested_start = min(len(df_for_deep), len(st.session_state.processed_df) + 1)
        elif st.session_state.get("deep_enriched_df") is not None:
            crawled_mask = st.session_state.deep_enriched_df["Thông tin cào sâu"].astype(str).str.strip().ne("") & ~st.session_state.deep_enriched_df["Thông tin cào sâu"].isna()
            if int(crawled_mask.sum()) > 0:
                suggested_start = min(len(df_for_deep), int(crawled_mask.sum()) + 1)

        # Crawler Settings
        col_s1, col_s2, col_s3, col_s4 = st.columns([1.5, 1.5, 2, 1.5])
        with col_s1:
            start_row = st.number_input(
                "Bắt đầu từ người số",
                min_value=1,
                max_value=len(df_for_deep),
                value=suggested_start,
                step=10,
                help=f"Vị trí bắt đầu cào trong file (Gợi ý tự động: người số {suggested_start} dựa trên tiến độ đã lưu)"
            )
        with col_s2:
            crawl_limit = st.number_input(
                "Số lượng cào đợt này",
                min_value=1,
                max_value=min(len(df_for_deep), 200),
                value=min(len(df_for_deep), 50),
                step=10,
                help="Nên cào mỗi đợt từ 20 đến 50 người để đảm bảo an toàn tuyệt đối cho tài khoản."
            )
        with col_s3:
            crawl_delay = st.slider(
                "Độ trễ an toàn giữa các profile (giây)",
                min_value=2.0,
                max_value=6.0,
                value=3.5,
                step=0.5,
                help="Mô phỏng hành vi người thật xem trang cá nhân (3.5s là mức chuẩn an toàn)."
            )
        with col_s4:
            crawl_headless = st.checkbox("Chạy ẩn (Headless)", value=True, help="Bỏ tích nếu bạn muốn nhìn thấy cửa sổ trình duyệt tự động mở và lướt qua từng trang cá nhân.")

        calc_end_row = min(len(df_for_deep), int(start_row) + int(crawl_limit) - 1)
        st.markdown(f"""
        <div style="background-color:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:9px 14px; margin-bottom:12px; font-size:0.88rem; color:#166534; display:flex; align-items:center; gap:8px;">
            <span class="icon-pill icon-pill-emerald icon-pill-sm">{get_svg_icon('check_circle', 14, '#059669')}</span>
            <span><b>Phạm vi cào đợt này:</b> Từ người số <b>{start_row}</b> đến <b>{calc_end_row}</b> (Tổng cộng <b>{calc_end_row - int(start_row) + 1} người</b> / {len(df_for_deep)} người trong file).</span>
        </div>
        """, unsafe_allow_html=True)

        saved_fb_cookie = saved_cfg.get("fb_cookie", "")
        with st.expander("Cấu hình Cookie Facebook (Tự động lưu vĩnh viễn, không cần nhập lại)", expanded=not bool(saved_fb_cookie)):
            deep_cookie = st.text_input(
                "Chuỗi Cookie Facebook (c_user=...; xs=...):",
                value=saved_fb_cookie,
                type="password",
                help="Chuỗi Cookie sẽ được tự động lưu vĩnh viễn trên máy tính. Bạn không cần phải dán lại ở các lần sử dụng tiếp theo!"
            )
            if deep_cookie and deep_cookie != saved_fb_cookie:
                saved_cfg["fb_cookie"] = deep_cookie
                save_user_config(saved_cfg)
                st.success("Đã tự động lưu Cookie mới vào hệ thống!")
            elif saved_fb_cookie:
                st.markdown(f'''
                <div style="display:flex; align-items:center; gap:8px; font-size:0.88rem; color:#059669; margin-top:6px;">
                    <span class="icon-pill icon-pill-emerald icon-pill-sm">{get_svg_icon('check_circle', 14, '#059669')}</span>
                    <span>Đã có Cookie lưu sẵn trong cấu hình. Bạn chỉ cần bấm nút Cào sâu bên dưới!</span>
                </div>
                ''', unsafe_allow_html=True)

        if st.button("BẮT ĐẦU CÀO SÂU CÔNG VIỆC & HỌC VẤN", type="primary", use_container_width=True):
            p_bar_deep = st.progress(0)
            status_deep = st.empty()

            def deep_cb(current, total, msg):
                pct = int((current / total) * 100) if total > 0 else 0
                p_bar_deep.progress(min(pct, 100))
                status_deep.text(msg)

            try:
                start_deep_t = time.time()
                status_deep.text("Đang khởi động trình duyệt tự động...")
                eff_cookie = deep_cookie.strip() if ('deep_cookie' in locals() and deep_cookie and deep_cookie.strip()) else saved_cfg.get("fb_cookie", "").strip()
                
                # Use existing accumulated df if valid
                base_df = df_for_deep.copy()
                if st.session_state.get("deep_enriched_df") is not None and len(st.session_state.deep_enriched_df) == len(df_for_deep):
                    base_df = st.session_state.deep_enriched_df

                enriched_res = run_deep_profile_crawl(
                    df=base_df,
                    link_col=deep_link_col,
                    name_col=deep_name_col,
                    start_index=int(start_row),
                    max_count=int(crawl_limit),
                    delay_seconds=float(crawl_delay),
                    headless=crawl_headless,
                    cookie_str=eff_cookie if eff_cookie else None,
                    progress_callback=deep_cb
                )
                st.session_state.deep_enriched_df = enriched_res
                save_deep_autosave(enriched_res)
                p_bar_deep.progress(100)
                dur = round(time.time() - start_deep_t, 1)
                status_deep.success(f"Hoàn tất cào sâu thông tin từ người #{start_row} đến #{calc_end_row} ({calc_end_row - int(start_row) + 1} profile) trong {dur} giây (Đã tự động lưu vào đệm máy tính)!")
            except Exception as e:
                st.error(f"Lỗi khi cào sâu profile: {e}")

        # If we have deep enriched results
        if st.session_state.get("deep_enriched_df") is not None:
            res_deep_df = st.session_state.deep_enriched_df
            has_info_mask = res_deep_df["Thông tin cào sâu"].astype(str).str.strip().ne("") & ~res_deep_df["Thông tin cào sâu"].isna()
            crawled_count = int(has_info_mask.sum())

            st.markdown("---")
            st.markdown(f'''
            <div class="section-title">
                <span class="icon-pill icon-pill-blue">{get_svg_icon('clipboard', 20, '#2563EB')}</span>
                <span>Kết quả cào sâu trực tiếp từ trang cá nhân ({crawled_count} / {len(res_deep_df)} người đã cào):</span>
            </div>
            ''', unsafe_allow_html=True)
            
            show_df = res_deep_df[has_info_mask] if crawled_count > 0 else res_deep_df.head(int(crawl_limit))
            st.dataframe(
                show_df[[deep_name_col, deep_link_col, "Thông tin cào sâu"]],
                use_container_width=True
            )

            # Action buttons for Tab 2
            act_col1, act_col2 = st.columns([3, 2])
            with act_col1:
                handoff_btn = st.button("CHUYỂN DỮ LIỆU CHO AI BÓC TÁCH & TỰ ĐỘNG GỘP VÀO CRM", type="primary", use_container_width=True)
            with act_col2:
                raw_crawled_bytes = export_styled_excel(show_df)
                st.download_button(
                    label="Tải File Thô Cào Sâu (.xlsx)",
                    data=raw_crawled_bytes,
                    file_name="facebook_crawled_raw.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            if handoff_btn:
                # Run AI on enriched dataframe
                ai_p_bar = st.progress(0)
                ai_status = st.empty()

                def update_deep_ai_p(done, total):
                    pct = int((done / total) * 100) if total > 0 else 0
                    ai_p_bar.progress(pct)
                    ai_status.text(f"AI đang bóc tách: {done}/{total} người ({pct}%)...")

                eff_provider = provider_code if api_key else "offline"
                eff_key = api_key if api_key else None

                # Target the current selected batch of profiles
                start_pos = max(0, int(start_row) - 1)
                end_pos = min(len(res_deep_df), start_pos + int(crawl_limit))
                current_batch_df = res_deep_df.iloc[start_pos:end_pos]
                
                # Check if current batch has crawled info; if not, fallback to all with info
                curr_has_info = current_batch_df["Thông tin cào sâu"].astype(str).str.strip().ne("") & ~current_batch_df["Thông tin cào sâu"].isna()
                if curr_has_info.sum() > 0:
                    sub_df = current_batch_df[curr_has_info]
                else:
                    sub_df = res_deep_df[has_info_mask] if crawled_count > 0 else current_batch_df

                if sub_df.empty:
                    ai_p_bar.progress(100)
                    ai_status.warning("Chưa có thông tin cào sâu nào trong đợt này. Vui lòng bấm nút 'Bắt đầu cào sâu' trước khi chuyển cho AI!")
                else:
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

                    # GOM thông minh: Cập nhật đè nếu cào lại, thêm mới nối tiếp nếu là người mới
                    existing_crm = st.session_state.get("processed_df")
                    if existing_crm is not None and not existing_crm.empty and "Link Facebook" in existing_crm.columns:
                        batch_links = set(ai_output["Link Facebook"].dropna().astype(str).str.strip())
                        existing_preserved = existing_crm[~existing_crm["Link Facebook"].astype(str).str.strip().isin(batch_links)]
                        combined_crm = pd.concat([existing_preserved, ai_output], ignore_index=True)
                        st.session_state.processed_df = combined_crm
                    else:
                        st.session_state.processed_df = ai_output

                    save_crm_autosave(st.session_state.processed_df)

                    ai_p_bar.progress(100)
                    total_accumulated = len(st.session_state.processed_df)
                    ai_status.success(f"Đã bóc tách và CẬP NHẬT thành công {len(ai_output)} người vào bảng CRM tổng (Hiện có {total_accumulated} người đã lưu an toàn trên ổ cứng)! Hãy chuyển sang Tab 3 để tải 1 FILE EXCEL DUY NHẤT!")

# ----------------- TAB 3: RESULTS & EXPORT -----------------
with tab_results:
    if st.session_state.processed_df is None:
        st.markdown(f"""
        <div class="alert-info">
            <span class="icon-pill icon-pill-blue">{get_svg_icon('table', 18, '#2563EB')}</span>
            <span>Chưa có dữ liệu xử lý. Vui lòng tải file và bấm nút 'Bắt đầu xử lý' ở Tab 1 trước.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        res_df = clean_and_reorder_crm_dataframe(st.session_state.processed_df)
        tier_col = "Độ đầy đủ thông tin" if "Độ đầy đủ thông tin" in res_df.columns else "Phân loại Lead"

        # Summary KPIs
        total_leads = len(res_df)
        high_potential = len(res_df[res_df[tier_col] == "Cao"])
        mid_potential = len(res_df[res_df[tier_col] == "Trung bình"])
        trash_count = len(res_df[res_df["Đánh giá"].str.contains("Rác", na=False)])
        valid_count = len(res_df[res_df["Đánh giá"] == "Hợp lệ"])

        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-blue icon-pill-sm">{get_svg_icon("users", 14, "#2563EB")}</span>
                    <span>TỔNG QUÉT</span>
                </div>
                <div class="metric-val">{total_leads}</div>
            </div>
            ''', unsafe_allow_html=True)
        with kpi2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-emerald icon-pill-sm">{get_svg_icon("star", 14, "#059669")}</span>
                    <span>ĐẦY ĐỦ (CAO)</span>
                </div>
                <div class="metric-val val-green">{high_potential}</div>
            </div>
            ''', unsafe_allow_html=True)
        with kpi3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-blue icon-pill-sm">{get_svg_icon("briefcase", 14, "#2563EB")}</span>
                    <span>TRUNG BÌNH</span>
                </div>
                <div class="metric-val val-blue">{mid_potential}</div>
            </div>
            ''', unsafe_allow_html=True)
        with kpi4:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-amber icon-pill-sm">{get_svg_icon("check_circle", 14, "#D97706")}</span>
                    <span>HỢP LỆ</span>
                </div>
                <div class="metric-val val-amber">{valid_count}</div>
            </div>
            ''', unsafe_allow_html=True)
        with kpi5:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-rose icon-pill-sm">{get_svg_icon("trash", 14, "#DC2626")}</span>
                    <span>RÁC / ĐÙA CỢT</span>
                </div>
                <div class="metric-val val-red">{trash_count}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("---")

        # Filters
        st.markdown(f'''
        <div class="section-title">
            <span class="icon-pill icon-pill-blue">{get_svg_icon("filter", 18, "#2563EB")}</span>
            <span>Bộ Lọc Nhanh Dữ Liệu</span>
        </div>
        ''', unsafe_allow_html=True)
        
        f_col0, f_col1, f_col2, f_col3, f_col4 = st.columns(5)

        with f_col0:
            raw_entity_vals = list(res_df["Loại hình đơn vị"].dropna().unique()) if "Loại hình đơn vị" in res_df.columns else []
            entity_order = ["Công ty", "Hộ kinh doanh", "Cá nhân", "Chưa xác định"]
            entity_options = ["Tất cả"] + [e for e in entity_order if e in raw_entity_vals] + [e for e in raw_entity_vals if e not in entity_order]
            sel_entity = st.selectbox("Loại hình đơn vị", options=entity_options, index=0)

        with f_col1:
            tier_options = ["Tất cả"] + list(res_df[tier_col].unique())
            sel_tier = st.selectbox("Độ đầy đủ thông tin", options=tier_options, index=0)

        with f_col2:
            status_options = ["Tất cả"] + list(res_df["Đánh giá"].unique())
            sel_status = st.selectbox("Đánh giá dữ liệu", options=status_options, index=0)

        with f_col3:
            level_options = ["Tất cả"] + list(res_df["Cấp bậc"].unique())
            sel_level = st.selectbox("Cấp bậc chức vụ", options=level_options, index=0)

        with f_col4:
            search_kw = st.text_input("Tìm kiếm (Tên, Công ty, Ngành...)", value="", placeholder="Nhập từ khóa...")

        # Apply Filters
        filtered_df = res_df.copy()
        if sel_entity != "Tất cả" and "Loại hình đơn vị" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Loại hình đơn vị"] == sel_entity]
        if sel_tier != "Tất cả":
            filtered_df = filtered_df[filtered_df[tier_col] == sel_tier]
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
                (filtered_df["Loại hình đơn vị"].str.lower().str.contains(kw, na=False) if "Loại hình đơn vị" in filtered_df.columns else False) |
                (filtered_df["Trường học / Học vấn"].str.lower().str.contains(kw, na=False) if "Trường học / Học vấn" in filtered_df.columns else False) |
                filtered_df["Chức vụ"].str.lower().str.contains(kw, na=False) |
                filtered_df["Lĩnh vực / Ngành nghề"].str.lower().str.contains(kw, na=False)
            ]

        st.write(f"Hiển thị **{len(filtered_df)}** / {len(res_df)} kết quả phù hợp:")

        # Interactive Data Table
        filtered_df = clean_and_reorder_crm_dataframe(filtered_df)
        tab3_col_config = {
            "STT": st.column_config.NumberColumn("STT", width="small"),
            "Họ và tên": st.column_config.TextColumn("Họ và tên", width="medium"),
            "Chức vụ": st.column_config.TextColumn("Chức vụ", width="small"),
            "Tên công ty / Đơn vị": st.column_config.TextColumn("Tên công ty / Đơn vị", width="medium"),
            "Tên công ty chuẩn hóa": st.column_config.TextColumn("Công ty chuẩn hóa", width="medium"),
            "Loại hình đơn vị": st.column_config.TextColumn("Loại hình đơn vị", width="small"),
            "Trường học / Học vấn": st.column_config.TextColumn("Học vấn / Trường", width="medium"),
            "Cấp bậc": st.column_config.TextColumn("Cấp bậc", width="small"),
            "Lĩnh vực / Ngành nghề": st.column_config.TextColumn("Lĩnh vực", width="small"),
            "Đánh giá": st.column_config.TextColumn("Đánh giá", width="small"),
            "Độ đầy đủ thông tin": st.column_config.TextColumn("Độ đầy đủ TT", width="small"),
            "Link Facebook": st.column_config.LinkColumn("Link Facebook", display_text="Mở FB", width="small")
        }
        if "Độ khớp LinkedIn" in filtered_df.columns:
            tab3_col_config["Độ khớp LinkedIn"] = st.column_config.TextColumn("Độ khớp", width="small")
        if "Link LinkedIn" in filtered_df.columns:
            tab3_col_config["Link LinkedIn"] = st.column_config.LinkColumn("Link LinkedIn", display_text="Xem Profile", width="small")
        if "Tìm trên Google" in filtered_df.columns:
            tab3_col_config["Tìm trên Google"] = st.column_config.LinkColumn("Tìm Google", display_text="Tìm kiếm", width="small")

        styled_tab3_table = style_dataframe_with_linkedin(filtered_df)
        st.dataframe(
            styled_tab3_table,
            use_container_width=True,
            column_config=tab3_col_config
        )

        st.markdown("---")
        st.markdown(f'''
        <div class="section-title">
            <span class="icon-pill icon-pill-emerald">{get_svg_icon("download", 18, "#059669")}</span>
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

# ----------------- TAB 4: LINKEDIN MATCHING -----------------
with tab_linkedin:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom: 8px;">
        <span class="icon-pill icon-pill-blue" style="width:40px; height:40px; background:#0A66C2;">{get_svg_icon('linkedin', 22, '#FFFFFF')}</span>
        <div>
            <div style="font-size:1.35rem; font-weight:800; color:#0A66C2;">Tìm Kiếm & Ghép Nối Profile LinkedIn Tự Động</div>
            <div style="font-size:0.9rem; color:#4B5563;">Định danh Profile LinkedIn qua Google Dorking: <code>site:linkedin.com/in "[Họ tên]" "[Tên công ty]"</code></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.processed_df is None:
        st.markdown(f"""
        <div class="alert-info">
            <span class="icon-pill icon-pill-blue">{get_svg_icon('info', 18, '#2563EB')}</span>
            <span>Chưa có dữ liệu CRM để ghép nối LinkedIn. Vui lòng tải file ở Tab 1 hoặc Cào sâu ở Tab 2 trước!</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        df_li = clean_and_reorder_crm_dataframe(st.session_state.processed_df)
        total_crm_leads = len(df_li)
        tier_col = "Độ đầy đủ thông tin" if "Độ đầy đủ thông tin" in df_li.columns else "Phân loại Lead"

        # Count stats
        has_li_count = df_li["Link LinkedIn"].astype(str).str.contains("linkedin.com/in", na=False).sum() if "Link LinkedIn" in df_li.columns else 0
        high_tier_count = len(df_li[df_li[tier_col] == "Cao"])
        mid_tier_count = len(df_li[df_li[tier_col] == "Trung bình"])
        has_company_count = len(df_li[df_li["Tên công ty / Đơn vị"].ne("Chưa cập nhật") & df_li["Tên công ty / Đơn vị"].ne("Ảo") & ~df_li["Tên công ty / Đơn vị"].isna()])

        # KPI Summary cards
        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
        with c_kpi1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-blue icon-pill-sm">{get_svg_icon("users", 14, "#2563EB")}</span>
                    <span>TỔNG LEAD CRM</span>
                </div>
                <div class="metric-val">{total_crm_leads}</div>
            </div>
            ''', unsafe_allow_html=True)
        with c_kpi2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-emerald icon-pill-sm">{get_svg_icon("star", 14, "#059669")}</span>
                    <span>THÔNG TIN ĐẦY ĐỦ (CAO)</span>
                </div>
                <div class="metric-val val-green">{high_tier_count}</div>
            </div>
            ''', unsafe_allow_html=True)
        with c_kpi3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-amber icon-pill-sm">{get_svg_icon("building", 14, "#D97706")}</span>
                    <span>CÓ CÔNG TY RÕ RÀNG</span>
                </div>
                <div class="metric-val val-amber">{has_company_count}</div>
            </div>
            ''', unsafe_allow_html=True)
        with c_kpi4:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-header">
                    <span class="icon-pill icon-pill-blue icon-pill-sm">{get_svg_icon("linkedin", 14, "#0A66C2")}</span>
                    <span>ĐÃ MATCH LINKEDIN</span>
                </div>
                <div class="metric-val val-blue">{has_li_count}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Configuration options
        st.markdown(f'''
        <div class="section-title">
            <span class="icon-pill icon-pill-blue">{get_svg_icon("filter", 18, "#2563EB")}</span>
            <span>Cấu Hình Tệp Matching & Phương Thức</span>
        </div>
        ''', unsafe_allow_html=True)

        opt_col1, opt_col2 = st.columns(2)
        with opt_col1:
            target_filter = st.selectbox(
                "Chọn tệp đối tượng cần tìm LinkedIn:",
                options=[
                    f"1. Nhóm thông tin Đầy đủ (Cao) ({high_tier_count} người) [Khuyên dùng để match]",
                    f"2. Cả nhóm Cao & Trung bình ({high_tier_count + mid_tier_count} người)",
                    f"3. Tất cả những người có tên công ty ({has_company_count} người)",
                    f"4. Toàn bộ danh bạ ({total_crm_leads} người)"
                ],
                index=0
            )

        with opt_col2:
            search_mode = st.radio(
                "Phương thức tìm kiếm LinkedIn:",
                options=[
                    "Google Serper API (Tự động 100%, siêu tốc ~20s)",
                    "Tạo link Google 1-Click (100% Miễn phí, không cần API Key)"
                ],
                index=0,
                horizontal=True
            )

        # Base target dataframe for the selected filter
        if "1. Nhóm thông tin Đầy đủ" in target_filter:
            base_target_df = df_li[df_li[tier_col] == "Cao"].copy()
        elif "2. Cả nhóm Cao" in target_filter:
            base_target_df = df_li[df_li[tier_col].isin(["Cao", "Trung bình"])].copy()
        elif "3. Tất cả những người có tên công ty" in target_filter:
            base_target_df = df_li[df_li["Tên công ty / Đơn vị"].ne("Chưa cập nhật") & df_li["Tên công ty / Đơn vị"].ne("Ảo") & ~df_li["Tên công ty / Đơn vị"].isna()].copy()
        else:
            base_target_df = df_li.copy()

        total_in_group = len(base_target_df)
        has_li_col = "Link LinkedIn" in base_target_df.columns
        already_has_li_mask = base_target_df["Link LinkedIn"].astype(str).str.contains("linkedin.com/in", na=False) if has_li_col else pd.Series(False, index=base_target_df.index)
        group_matched_count = int(already_has_li_mask.sum())
        group_unmatched_count = total_in_group - group_matched_count

        # Mode selector & Skip option
        col_m1, col_m2 = st.columns([3, 2])
        with col_m1:
            match_mode = st.radio(
                "Cách chọn danh sách quét:",
                options=[
                    "Quét theo số thứ tự (Ví dụ: Từ người 101 đến 476)",
                    "Tự động quét người chưa có Link (Khuyên dùng)"
                ],
                index=0,
                horizontal=True
            )
        with col_m2:
            skip_already_matched = st.checkbox(
                "Bỏ qua người đã có Link LinkedIn (Tránh tốn API)",
                value=True,
                help="Nếu tích chọn, hệ thống sẽ bỏ qua những ai đã có link LinkedIn trong máy để tiết kiệm lượt gọi API."
            )

        col_inputs, col_card = st.columns([1, 1])

        if "Quét theo số thứ tự" in match_mode:
            with col_inputs:
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    start_match_idx = st.number_input(
                        "Bắt đầu từ người số:",
                        min_value=1,
                        max_value=max(1, total_in_group),
                        value=1,
                        step=10,
                        help="Vị trí bắt đầu trong tệp đối tượng này (từ 1 đến tổng số người)."
                    )
                calc_start = max(0, int(start_match_idx) - 1)
                remaining_from_start = max(1, total_in_group - calc_start)

                with c_s2:
                    match_limit = st.number_input(
                        "Số lượng muốn quét đợt này:",
                        min_value=1,
                        max_value=max(1, total_in_group),
                        value=min(100, remaining_from_start) if remaining_from_start > 0 else 1,
                        step=10,
                        help="Số lượng người muốn tra cứu trong đợt này (Enter để cập nhật)."
                    )

            calc_end = min(total_in_group, calc_start + int(match_limit))
            calc_count = max(0, calc_end - calc_start)

            # Slicing from the stable base dataframe
            subset_selected = base_target_df.iloc[calc_start:calc_end].copy()

            if has_li_col:
                in_slice_has_link = subset_selected["Link LinkedIn"].astype(str).str.contains("linkedin.com/in", na=False)
                slice_already_count = int(in_slice_has_link.sum())
            else:
                in_slice_has_link = pd.Series(False, index=subset_selected.index)
                slice_already_count = 0

            if skip_already_matched:
                subset_to_match = subset_selected[~in_slice_has_link].copy()
            else:
                subset_to_match = subset_selected.copy()

            with col_card:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if skip_already_matched and slice_already_count > 0:
                    detail_note = f"<div style='color:#059669; font-size:0.82rem; margin-top:4px; display:flex; align-items:center; gap:6px;'>{get_svg_icon('check', 13, '#059669')} <span><b>{len(subset_to_match)} người</b> chưa có link sẽ được tra cứu ({slice_already_count} người đã có link sẽ tự động bỏ qua để tiết kiệm API)</span></div>"
                else:
                    detail_note = f"<div style='color:#059669; font-size:0.82rem; margin-top:4px; display:flex; align-items:center; gap:6px;'>{get_svg_icon('check', 13, '#059669')} <span><b>{len(subset_to_match)} người</b> sẽ được tra cứu trong đợt này</span></div>"

                st.markdown(f"""
                <div style="background:#F0FDF4; border:1px solid #BBF7D0; padding:12px 16px; border-radius:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="icon-pill icon-pill-emerald icon-pill-sm">{get_svg_icon('target', 14, '#059669')}</span>
                        <span style="font-weight:700; color:#166534; font-size:0.92rem;">Phạm vi quét: Từ người số {calc_start + 1} đến {calc_end}</span>
                    </div>
                    <div style="color:#15803D; font-size:0.84rem; margin-top:4px;">
                        Tổng chọn: <b>{calc_count} người</b> (trên tổng số {total_in_group} người trong nhóm)
                    </div>
                    {detail_note}
                </div>
                """, unsafe_allow_html=True)

        else:
            # Mode 2: Auto pick unmatched
            unmatched_df = base_target_df[~already_has_li_mask].copy()
            unmatched_total = len(unmatched_df)

            with col_inputs:
                auto_limit = st.number_input(
                    "Số lượng muốn quét đợt này:",
                    min_value=1,
                    max_value=max(1, unmatched_total) if unmatched_total > 0 else 1,
                    value=min(100, unmatched_total) if unmatched_total > 0 else 1,
                    step=10,
                    help="Số người chưa có link LinkedIn sẽ được lấy tự động từ trên xuống."
                )

            subset_to_match = unmatched_df.head(int(auto_limit)).copy()
            calc_count = len(subset_to_match)

            with col_card:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background:#EFF6FF; border:1px solid #BFDBFE; padding:12px 16px; border-radius:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="icon-pill icon-pill-blue icon-pill-sm">{get_svg_icon('bolt', 14, '#2563EB')}</span>
                        <span style="font-weight:700; color:#1D4ED8; font-size:0.92rem;">Tự động lấy: {calc_count} người tiếp theo chưa có link</span>
                    </div>
                    <div style="color:#2563EB; font-size:0.84rem; margin-top:4px;">
                        Hiện còn <b>{unmatched_total} / {total_in_group} người</b> chưa có LinkedIn trong nhóm này
                    </div>
                    <div style="color:#64748B; font-size:0.80rem; margin-top:4px; display:flex; align-items:center; gap:6px;">
                        {get_svg_icon('info', 13, '#64748B')} <span>Hệ thống tự bốc từ trên xuống, quét xong tự động trừ dần</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Trigger button
        btn_m1, _ = st.columns([2, 3])
        with btn_m1:
            run_match_btn = st.button("BẮT ĐẦU TÌM KIẾM & GHÉP NỐI LINKEDIN", type="primary", use_container_width=True)

        eff_serper = saved_cfg.get("serper_key", "").strip()

        if run_match_btn:
            if "Serper" in search_mode and not eff_serper:
                st.warning("Bạn chưa cấu hình Serper API Key ở thanh Cấu hình (Sidebar bên trái)! Vui lòng dán Key tại Sidebar để tiếp tục hoặc chọn phương thức 'Tạo link Google 1-Click' để chạy miễn phí.")
            elif len(subset_to_match) == 0:
                st.info("Tất cả những người trong phạm vi đã chọn đều đã có Link LinkedIn trước đó!")
            else:
                p_bar_li = st.progress(0)
                status_li = st.empty()

                def update_li_progress(done, total, msg):
                    pct = int((done / total) * 100) if total > 0 else 0
                    p_bar_li.progress(min(pct, 100))
                    status_li.text(msg)

                eff_serper = serper_key_input.strip() if "Serper" in search_mode else ""
                t_start = time.time()
                
                matched_subset = linkedin_matcher.match_leads_dataframe(
                    df=subset_to_match,
                    serper_key=eff_serper,
                    max_workers=5,
                    progress_callback=update_li_progress
                )

                # Merge matched columns back to main processed_df
                for col in ["Link LinkedIn", "Độ khớp LinkedIn", "Tìm trên Google"]:
                    if col not in df_li.columns:
                        df_li[col] = ""
                    df_li.loc[matched_subset.index, col] = matched_subset[col]

                df_li = clean_and_reorder_crm_dataframe(df_li)
                st.session_state.processed_df = df_li
                save_crm_autosave(df_li)
                p_bar_li.progress(100)
                t_dur = round(time.time() - t_start, 1)

                found_new = matched_subset["Link LinkedIn"].astype(str).str.contains("linkedin.com/in", na=False).sum()
                status_li.success(f"Hoàn tất ghép nối cho {len(matched_subset)} người trong {t_dur}s (Tìm thấy {found_new} Profile LinkedIn)! Dữ liệu đã được lưu an toàn vào máy.")

        # Show Table of matched leads
        if "Link LinkedIn" in df_li.columns or "Tìm trên Google" in df_li.columns:
            st.markdown("---")
            st.markdown(f'''
            <div class="section-title">
                <span class="icon-pill icon-pill-blue">{get_svg_icon("table", 18, "#2563EB")}</span>
                <span>Bảng Kết Quả Đã Ghép Nối LinkedIn</span>
            </div>
            ''', unsafe_allow_html=True)

            # Quality Audit & Cleaning Tool
            with st.expander("Kiểm định & Lọc sạch dữ liệu LinkedIn (Loại bỏ người nhận nhầm - Miễn phí 100%)", expanded=False):
                st.markdown(f"""
                <div style="font-size:0.86rem; color:#334155; line-height:1.6; margin-bottom:10px;">
                    <div>Hệ thống áp dụng <b>cơ chế kiểm duyệt 3 lớp nghiêm ngặt (Giải pháp 1 & 4)</b>:</div>
                    <ul style="margin:4px 0 8px 18px; padding:0; color:#475569;">
                        <li><b>Lớp 1 (Tên chính & Họ)</b>: Bắt buộc tên chính tiếng Việt (từ cuối cùng) phải khớp chuẩn trong tiêu đề hoặc URL profile LinkedIn. Tự động loại bỏ ngay những người khác họ tên.</li>
                        <li><b>Lớp 2 (Tín hiệu xác nhận đa điểm)</b>: Phải có ít nhất một xác nhận trùng khớp về <i>Công ty / Đơn vị</i>, <i>Trường học / Học vấn</i> hoặc <i>Chức danh chuyên môn</i>.</li>
                        <li><b>Lớp 3 (Tuyệt đối không Fallback)</b>: Không gán bừa kết quả tìm kiếm đầu tiên nếu chưa đạt ngưỡng tin cậy cao (dưới 50 điểm sẽ để trống link thay vì nhận nhầm).</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                c_clean_btn, c_clean_note = st.columns([2, 3])
                with c_clean_btn:
                    if st.button("LÀM SẠCH TOÀN BỘ LINK ĐÃ QUÉT TRƯỚC ĐÂY", type="secondary", use_container_width=True, help="Tự động kiểm định lại các profile đã lưu trong CRM bằng thuật toán mới, xóa bỏ các link sai lệch mà không tốn bất kỳ lượt Serper API nào."):
                        with st.spinner("Đang rà soát và đối chiếu lại dữ liệu theo chuẩn nghiêm ngặt..."):
                            cleaned_df, retained_cnt, cleaned_cnt = linkedin_matcher.recheck_and_clean_dataframe(df_li)
                            st.session_state.processed_df = cleaned_df
                            save_crm_autosave(cleaned_df)
                            st.success(f"Hoàn tất kiểm định: Giữ lại {retained_cnt} Profile chính xác 100% và dọn sạch {cleaned_cnt} Profile nhận nhầm!")
                            st.rerun()
                with c_clean_note:
                    st.caption("Dùng dữ liệu tiêu đề và tóm tắt đã lưu sẵn trên máy, không tốn thêm bất kỳ lượt tìm kiếm Serper API nào.")

            # Determine matched and search link masks
            has_li_mask = df_li["Link LinkedIn"].astype(str).str.contains("linkedin.com/in", na=False) if "Link LinkedIn" in df_li.columns else pd.Series(False, index=df_li.index)
            has_gg_mask = df_li["Tìm trên Google"].astype(str).str.contains("http", na=False) if "Tìm trên Google" in df_li.columns else pd.Series(False, index=df_li.index)
            processed_mask = has_li_mask | has_gg_mask

            total_proc_count = int(processed_mask.sum())
            matched_proc_count = int(has_li_mask.sum())
            unmatched_proc_count = total_proc_count - matched_proc_count

            tbl_col1, tbl_col2 = st.columns([3, 2])
            with tbl_col1:
                tbl_filter = st.radio(
                    "Lọc kết quả hiển thị:",
                    options=[
                        f"Tất cả đã tra cứu ({total_proc_count})",
                        f"Chỉ người tìm thấy Link LinkedIn ({matched_proc_count})",
                        f"Chỉ người chưa có Link Profile ({unmatched_proc_count})"
                    ],
                    index=0,
                    horizontal=True
                )
            with tbl_col2:
                sort_order = st.selectbox(
                    "Thứ tự hiển thị:",
                    options=[
                        "Thứ tự gốc theo danh bạ (1, 2, 3...)",
                        "Đưa người có LinkedIn lên đầu",
                        "Độ khớp cao xuống thấp"
                    ],
                    index=0
                )

            # Apply filter
            if "Chỉ người tìm thấy Link LinkedIn" in tbl_filter:
                li_view_df = df_li[has_li_mask].copy()
            elif "Chỉ người chưa có Link Profile" in tbl_filter:
                li_view_df = df_li[~has_li_mask & has_gg_mask].copy()
            else:
                li_view_df = df_li[processed_mask].copy()

            if li_view_df.empty:
                li_view_df = df_li.head(20).copy()

            # Apply sort order (Default: preserves natural CRM sequence!)
            if sort_order == "Đưa người có LinkedIn lên đầu" and "Link LinkedIn" in li_view_df.columns:
                li_view_df["_has_li"] = li_view_df["Link LinkedIn"].astype(str).str.contains("linkedin.com/in", na=False).astype(int)
                li_view_df = li_view_df.sort_values(by="_has_li", ascending=False).drop(columns=["_has_li"])
            elif sort_order == "Độ khớp cao xuống thấp" and "Độ khớp LinkedIn" in li_view_df.columns:
                score_map = {
                    "Khớp cao (90-100%)": 3,
                    "Khớp vừa (60-80%)": 2,
                    "Cần đối soát (<50%)": 1,
                    "Cần đối soát": 1,
                    "Chưa tìm thấy": 0
                }
                li_view_df["_score"] = li_view_df["Độ khớp LinkedIn"].map(lambda x: score_map.get(str(x), 0))
                li_view_df = li_view_df.sort_values(by="_score", ascending=False).drop(columns=["_score"])

            # Reset index and add clean STT column
            li_view_df = clean_and_reorder_crm_dataframe(li_view_df)
            li_view_df = li_view_df.reset_index(drop=True)
            li_view_df.insert(0, "STT", range(1, len(li_view_df) + 1))

            st.markdown("""
            <div style="display:flex; align-items:center; gap:20px; margin: 8px 0 12px 0; font-size:0.86rem; background:#F8FAFC; border:1px solid #E2E8F0; padding:8px 14px; border-radius:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="display:inline-block; width:14px; height:14px; background:#DCFCE7; border:2px solid #22C55E; border-radius:3px;"></span>
                    <span style="font-weight:700; color:#14532D;">Tô nền xanh & in đậm: Đã tìm thấy Profile LinkedIn</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="display:inline-block; width:14px; height:14px; background:#FFFFFF; border:1px solid #CBD5E1; border-radius:3px;"></span>
                    <span style="color:#64748B;">Chữ thường: Chưa tìm thấy Profile (kèm link tìm kiếm Google 1-Click)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Display table with proper column widths and hidden index
            # Exactly requested order: profile info -> Độ đầy đủ thông tin -> Độ khớp LinkedIn -> Link Facebook -> Link LinkedIn -> Tìm trên Google
            display_cols = [
                c for c in [
                    "STT",
                    "Họ và tên",
                    "Chức vụ",
                    "Tên công ty / Đơn vị",
                    "Tên công ty chuẩn hóa",
                    "Loại hình đơn vị",
                    "Trường học / Học vấn",
                    "Cấp bậc",
                    "Lĩnh vực / Ngành nghề",
                    "Độ đầy đủ thông tin",
                    "Độ khớp LinkedIn",
                    "Link Facebook",
                    "Link LinkedIn",
                    "Tìm trên Google"
                ] if c in li_view_df.columns
            ]
            styled_li_table = style_dataframe_with_linkedin(li_view_df[display_cols])
            st.dataframe(
                styled_li_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "STT": st.column_config.NumberColumn("STT", width="small"),
                    "Họ và tên": st.column_config.TextColumn("Họ và tên", width="medium"),
                    "Tên công ty / Đơn vị": st.column_config.TextColumn("Tên công ty / Đơn vị", width="medium"),
                    "Tên công ty chuẩn hóa": st.column_config.TextColumn("Công ty chuẩn hóa", width="medium"),
                    "Loại hình đơn vị": st.column_config.TextColumn("Loại hình đơn vị", width="small"),
                    "Chức vụ": st.column_config.TextColumn("Chức vụ", width="small"),
                    "Trường học / Học vấn": st.column_config.TextColumn("Học vấn / Trường", width="medium"),
                    "Cấp bậc": st.column_config.TextColumn("Cấp bậc", width="small"),
                    "Lĩnh vực / Ngành nghề": st.column_config.TextColumn("Lĩnh vực", width="small"),
                    "Độ đầy đủ thông tin": st.column_config.TextColumn("Độ đầy đủ TT", width="small"),
                    "Độ khớp LinkedIn": st.column_config.TextColumn("Độ khớp", width="small"),
                    "Link Facebook": st.column_config.LinkColumn("Link Facebook", display_text="Mở FB", width="small"),
                    "Link LinkedIn": st.column_config.LinkColumn("Link LinkedIn", display_text="Xem Profile", width="small"),
                    "Tìm trên Google": st.column_config.LinkColumn("Tìm Google", display_text="Tìm kiếm", width="small")
                }
            )

            # Export Excel with LinkedIn
            exp_li_col1, _ = st.columns([3, 4])
            with exp_li_col1:
                li_excel_bytes = export_styled_excel(df_li)
                st.download_button(
                    label="Tải File Excel Đầy Đủ Kèm Link LinkedIn (.xlsx)",
                    data=li_excel_bytes,
                    file_name="facebook_leads_crm_with_linkedin.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )

# ----------------- TAB 5: ANALYTICS -----------------
with tab_analytics:
    if st.session_state.processed_df is None:
        st.markdown(f"""
        <div class="alert-info">
            <span class="icon-pill icon-pill-blue">{get_svg_icon('chart', 18, '#2563EB')}</span>
            <span>Vui lòng xử lý dữ liệu trước để xem biểu đồ phân tích.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        df_an = clean_and_reorder_crm_dataframe(st.session_state.processed_df)

        an_col1, an_col2, an_col3 = st.columns(3)
        with an_col1:
            st.markdown(f'''
            <div class="section-title">
                <span class="icon-pill icon-pill-emerald">{get_svg_icon("building", 18, "#059669")}</span>
                <span>Phân Bổ Loại Hình Đơn Vị</span>
            </div>
            ''', unsafe_allow_html=True)
            if "Loại hình đơn vị" in df_an.columns:
                entity_counts = df_an["Loại hình đơn vị"].value_counts().reset_index()
                entity_counts.columns = ["Loại hình", "Số lượng"]
                st.bar_chart(data=entity_counts, x="Loại hình", y="Số lượng")
            else:
                st.write("Chưa có dữ liệu loại hình đơn vị.")

        with an_col2:
            st.markdown(f'''
            <div class="section-title">
                <span class="icon-pill icon-pill-blue">{get_svg_icon("chart", 18, "#2563EB")}</span>
                <span>Phân Bổ Cấp Bậc</span>
            </div>
            ''', unsafe_allow_html=True)
            level_counts = df_an["Cấp bậc"].value_counts().reset_index()
            level_counts.columns = ["Cấp bậc", "Số lượng"]
            st.bar_chart(data=level_counts, x="Cấp bậc", y="Số lượng")

        with an_col3:
            st.markdown(f'''
            <div class="section-title">
                <span class="icon-pill icon-pill-amber">{get_svg_icon("target", 18, "#D97706")}</span>
                <span>Độ Đầy Đủ Thông Tin</span>
            </div>
            ''', unsafe_allow_html=True)
            tier_col = "Độ đầy đủ thông tin" if "Độ đầy đủ thông tin" in df_an.columns else "Phân loại Lead"
            tier_counts = df_an[tier_col].value_counts().reset_index()
            tier_counts.columns = [tier_col, "Số lượng"]
            st.bar_chart(data=tier_counts, x=tier_col, y="Số lượng")

        st.markdown(f'''
        <div class="section-title">
            <span class="icon-pill icon-pill-purple">{get_svg_icon("building", 18, "#7C3AED")}</span>
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
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
        <span class="icon-pill icon-pill-blue icon-pill-lg">{get_svg_icon('shield', 22, '#2563EB')}</span>
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

#### Bước 2: Tự Động Cuộn & Cào Dữ Liệu Facebook (Không Cần Ngồi Lướt Thủ Công)
Bạn có thể chọn 1 trong 3 cách cực kỳ tiện lợi dưới đây:

* **🚀 Cách 1 (Khuyên dùng - 1 Click): Chạy Tool Tự Động Cuộn `Tu_Dong_Cuon_Facebook.bat`**
  1. Click đúp vào file `Tu_Dong_Cuon_Facebook.bat` trong thư mục dự án.
  2. Tool sẽ tự động mở Google Chrome, truy cập trang bạn bè Facebook của bạn.
  3. Tool tự động cuộn xuống mô phỏng cử chỉ người thật (delay ngẫu nhiên 2s - 3.8s, chống checkpoint an toàn 100%).
  4. Bạn có thể bấm `Ctrl + C` bất kỳ lúc nào để DỪNG và LƯU dữ liệu. File `danh_sach_ban_be_tu_dong.csv` sẽ tự động được tạo ra!

* **⚡ Cách 2: Tiện Ích JavaScript Chạy Ngay Trên Trình Duyệt (`fb_auto_scroll.js`)**
  1. Truy cập: `https://www.facebook.com/me/friends` trên Chrome / Edge / Cốc Cốc.
  2. Bấm phím **F12** (hoặc chuột phải -> Kiểm tra) -> Chọn tab **Console**.
  3. Mở file `fb_auto_scroll.js` trong thư mục dự án, copy toàn bộ nội dung dán vào Console rồi bấm **Enter**.
  4. Bảng điều khiển nổi cực xịn sẽ hiện ngay góc phải màn hình: Bấm nút **[▶ Bắt Đầu Tự Động Cuộn]**.
  5. Khi cuộn xong (hoặc chạm đáy), bấm nút **[📥 Xuất File Excel (CSV) Ngay]** để tải file về máy.

* **🛠 Cách 3: Dùng Tiện Ích Instant Data Scraper (Nếu đã quen dùng)**
  1. Cài đặt tiện ích **Instant Data Scraper** từ Chrome Web Store.
  2. Truy cập: `https://www.facebook.com/me/friends`.
  3. Bấm icon Instant Data Scraper -> Đặt **Min delay: 2.5s, Max delay: 4.0s** -> Bấm **Start Crawling** -> Tải file XLSX/CSV về.

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
