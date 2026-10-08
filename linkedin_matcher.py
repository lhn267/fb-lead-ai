import re
import time
import unicodedata
import requests
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

def remove_vietnamese_accents(input_str: str) -> str:
    """Removes Vietnamese tone marks and accents for broader search matching."""
    if not input_str or not isinstance(input_str, str):
        return ""
    s = unicodedata.normalize("NFD", input_str)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    return s.strip()

def clean_company_name_for_search(company: str) -> str:
    """Extracts the core business name, stripping generic legal words like 'Công ty Cổ phần', 'TNHH', etc."""
    if not company or company in ["Chưa cập nhật", "Ảo", "nan"]:
        return ""
    comp = str(company)
    # Strip common prefixes
    comp = re.sub(r"(?i)\b(công ty cổ phần|công ty tnhh mtv|công ty tnhh|công ty|tập đoàn|doanh nghiệp / đơn vị|hộ kinh doanh / thương hiệu|chi nhánh|tổng công ty)\b", "", comp)
    comp = re.sub(r"(?i)\b(jsc|ltd|co\.,\s*ltd|corp|holding|group)\b", "", comp)
    return comp.strip(" -–:·,")

def build_google_dork_query(name: str, company: str, job: str = "") -> str:
    """
    Constructs an optimized Google Dork query to find LinkedIn profiles in Vietnam.
    Example: site:linkedin.com/in ("Vương Thanh Long" OR "Vuong Thanh Long") "Rebox"
    """
    name_clean = str(name).strip() if name else ""
    name_unaccent = remove_vietnamese_accents(name_clean)
    comp_clean = clean_company_name_for_search(company)
    
    # Name part with accented and unaccented variants
    if name_unaccent and name_unaccent.lower() != name_clean.lower():
        name_clause = f'("{name_clean}" OR "{name_unaccent}")'
    else:
        name_clause = f'"{name_clean}"'

    if comp_clean:
        return f'site:linkedin.com/in {name_clause} "{comp_clean}"'
    elif job and job != "Chưa cập nhật":
        return f'site:linkedin.com/in {name_clause} "{job}"'
    else:
        return f'site:linkedin.com/in {name_clause}'

def generate_google_search_url(name: str, company: str, job: str = "") -> str:
    """Generates direct 1-click Google Search link for manual inspection."""
    query = build_google_dork_query(name, company, job)
    from urllib.parse import quote_plus
    return f"https://www.google.com/search?q={quote_plus(query)}"

def search_serper_single(query: str, api_key: str, timeout: int = 15) -> List[Dict[str, Any]]:
    """
    Executes a single search request via Serper.dev API.
    Returns list of organic search results with 'title', 'link', 'snippet'.
    """
    if not api_key:
        return []
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key.strip(),
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "gl": "vn",
        "hl": "vi",
        "num": 5
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("organic", [])
        else:
            return []
    except Exception:
        return []

def evaluate_linkedin_candidate(
    lead_name: str,
    lead_company: str,
    lead_job: str,
    search_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates Google search results to extract the best matching LinkedIn profile
    and assigns a match confidence score.
    """
    if not search_results:
        return {
            "linkedin_url": "",
            "linkedin_title": "Không tìm thấy kết quả",
            "linkedin_snippet": "",
            "match_score": "Chưa tìm thấy",
            "match_percent": 0,
            "confidence_level": "Không có"
        }

    lead_name_clean = str(lead_name).lower().strip()
    lead_name_unaccent = remove_vietnamese_accents(lead_name_clean)
    comp_clean = clean_company_name_for_search(lead_company).lower()
    comp_unaccent = remove_vietnamese_accents(comp_clean)
    job_clean = str(lead_job).lower() if lead_job != "Chưa cập nhật" else ""

    best_match = None
    best_score = 0

    for item in search_results:
        link = item.get("link", "")
        if "linkedin.com/in/" not in link.lower():
            continue

        title = item.get("title", "")
        snippet = item.get("snippet", "")
        combined_text = (title + " " + snippet).lower()
        combined_unaccent = remove_vietnamese_accents(combined_text)

        score = 0

        # Name matching
        # Check if full name or unaccented name is in title
        name_words = lead_name_unaccent.split()
        if lead_name_clean in combined_text or lead_name_unaccent in combined_unaccent:
            score += 50
        elif len(name_words) >= 2 and all(w in combined_unaccent for w in name_words):
            score += 45
        elif len(name_words) >= 2 and sum(1 for w in name_words if w in combined_unaccent) >= len(name_words) - 1:
            score += 30

        # Company matching
        if comp_clean and (comp_clean in combined_text or comp_unaccent in combined_unaccent):
            score += 40
        elif comp_clean:
            comp_words = [w for w in comp_unaccent.split() if len(w) > 2]
            if comp_words and any(cw in combined_unaccent for cw in comp_words):
                score += 25

        # Job matching
        if job_clean and any(jk in combined_text for jk in job_clean.split() if len(jk) > 3):
            score += 10

        if score > best_score:
            best_score = score
            best_match = {
                "linkedin_url": link,
                "linkedin_title": title,
                "linkedin_snippet": snippet,
                "score": score
            }

    if not best_match or best_score < 30:
        # Fallback to the first LinkedIn URL if available with low confidence
        first_item = next((it for it in search_results if "linkedin.com/in/" in it.get("link", "").lower()), None)
        if first_item:
            return {
                "linkedin_url": first_item.get("link", ""),
                "linkedin_title": first_item.get("title", ""),
                "linkedin_snippet": first_item.get("snippet", ""),
                "match_score": "Cần đối soát",
                "match_percent": 40,
                "confidence_level": "Thấp"
            }
        return {
            "linkedin_url": "",
            "linkedin_title": "Không có profile phù hợp",
            "linkedin_snippet": "",
            "match_score": "Chưa tìm thấy",
            "match_percent": 0,
            "confidence_level": "Không có"
        }

    if best_score >= 80:
        conf_label = "Khớp cao (90-100%)"
        conf_tier = "Cao"
    elif best_score >= 50:
        conf_label = "Khớp vừa (60-80%)"
        conf_tier = "Trung bình"
    else:
        conf_label = "Cần đối soát (<50%)"
        conf_tier = "Thấp"

    return {
        "linkedin_url": best_match["linkedin_url"],
        "linkedin_title": best_match["linkedin_title"],
        "linkedin_snippet": best_match["linkedin_snippet"],
        "match_score": conf_label,
        "match_percent": best_score,
        "confidence_level": conf_tier
    }

def match_single_lead(row_dict: Dict[str, Any], serper_key: str) -> Dict[str, Any]:
    """Helper to process a single lead row."""
    name = str(row_dict.get("Họ và tên", "")).strip()
    comp = str(row_dict.get("Tên công ty / Đơn vị", "")).strip()
    job = str(row_dict.get("Chức vụ", "")).strip()

    search_url = generate_google_search_url(name, comp, job)
    
    if not serper_key:
        return {
            "Link LinkedIn": "",
            "Tiêu đề LinkedIn": "Bấm link để xem trên Google",
            "Tóm tắt LinkedIn": "",
            "Độ khớp LinkedIn": "Chưa tra cứu tự động",
            "Link Google Search": search_url
        }

    query = build_google_dork_query(name, comp, job)
    results = search_serper_single(query, serper_key)
    eval_res = evaluate_linkedin_candidate(name, comp, job, results)

    return {
        "Link LinkedIn": eval_res["linkedin_url"],
        "Tiêu đề LinkedIn": eval_res["linkedin_title"],
        "Tóm tắt LinkedIn": eval_res["linkedin_snippet"],
        "Độ khớp LinkedIn": eval_res["match_score"],
        "Link Google Search": search_url
    }

def match_leads_dataframe(
    df: pd.DataFrame,
    serper_key: str = "",
    max_workers: int = 5,
    progress_callback = None
) -> pd.DataFrame:
    """
    Matches a dataframe of leads against LinkedIn via Serper Google Search API.
    Uses multi-threading for rapid execution.
    """
    out_df = df.copy()
    total_leads = len(out_df)
    results_map = {}

    rows_data = [(idx, row.to_dict()) for idx, row in out_df.iterrows()]

    if not serper_key:
        # Just generate 1-click Google search links instantly without API
        for idx, r_dict in rows_data:
            match_res = match_single_lead(r_dict, "")
            results_map[idx] = match_res
            if progress_callback:
                progress_callback(idx + 1, total_leads, f"Tạo liên kết tra cứu: {idx+1}/{total_leads}")
    else:
        # Concurrent API calls
        done_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(match_single_lead, r_dict, serper_key): idx
                for idx, r_dict in rows_data
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    res = future.result()
                    results_map[idx] = res
                except Exception:
                    name = str(rows_data[idx][1].get("Họ và tên", ""))
                    comp = str(rows_data[idx][1].get("Tên công ty / Đơn vị", ""))
                    results_map[idx] = {
                        "Link LinkedIn": "",
                        "Tiêu đề LinkedIn": "Lỗi kết nối tra cứu",
                        "Tóm tắt LinkedIn": "",
                        "Độ khớp LinkedIn": "Chưa tìm thấy",
                        "Link Google Search": generate_google_search_url(name, comp)
                    }
                done_count += 1
                if progress_callback:
                    name_cur = str(rows_data[idx][1].get("Họ và tên", ""))
                    progress_callback(done_count, total_leads, f"Đang tra cứu LinkedIn ({done_count}/{total_leads}): {name_cur}")

    # Assign new columns to DataFrame
    linkedin_links = []
    linkedin_titles = []
    linkedin_snippets = []
    linkedin_matches = []
    google_links = []

    for idx in range(len(out_df)):
        r = results_map.get(idx, {})
        linkedin_links.append(r.get("Link LinkedIn", ""))
        linkedin_titles.append(r.get("Tiêu đề LinkedIn", ""))
        linkedin_snippets.append(r.get("Tóm tắt LinkedIn", ""))
        linkedin_matches.append(r.get("Độ khớp LinkedIn", ""))
        google_links.append(r.get("Link Google Search", ""))

    out_df["Link LinkedIn"] = linkedin_links
    out_df["Tiêu đề LinkedIn"] = linkedin_titles
    out_df["Tóm tắt LinkedIn"] = linkedin_snippets
    out_df["Độ khớp LinkedIn"] = linkedin_matches
    out_df["Tìm trên Google"] = google_links

    return out_df
