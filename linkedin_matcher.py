import re
import time
import unicodedata
import requests
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed

def remove_vietnamese_accents(input_str: str) -> str:
    """Removes Vietnamese tone marks and accents for broader search matching."""
    if not input_str or not isinstance(input_str, str):
        return ""
    s = unicodedata.normalize("NFD", input_str)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    return s.strip()

LOCATIONS_KEYWORDS = [
    "hanoi", "ha noi", "hà nội", "tp.hcm", "tphcm", "ho chi minh", "hồ chí minh",
    "saigon", "sài gòn", "da nang", "đà nẵng", "vietnam", "việt nam", "hải phòng",
    "hai phong", "cần thơ", "can tho", "bình dương", "binh duong", "đồng nai", "dong nai",
    "bà rịa", "ba ria", "vũng tàu", "vung tau", "nha trang", "huế", "hue", "quảng ninh",
    "thành phố hồ chí minh", "thành phố hà nội", "thành phố đà lạt", "đà lạt"
]

GENERIC_COMP_STOPWORDS = {
    "cong", "ty", "co", "phan", "tnhh", "mtv", "tap", "doan", "jsc", "corp", "group",
    "ltd", "co.,", "thuong", "hieu", "ho", "kinh", "doanh", "chi", "nhanh", "vietnam",
    "viet", "nam", "education", "solutions", "trading", "services", "media", "global",
    "holding", "international", "investment", "consulting", "technology", "tech", "system",
    "chua", "cap", "nhat", "nan", "none", "khong", "co", "tu", "do", "freelance"
}

def is_location_only(text: str) -> bool:
    """Returns True if the text represents only a geographic location rather than a business name."""
    if not text:
        return False
    t = remove_vietnamese_accents(text).lower().strip(" ,.-/()")
    for loc in LOCATIONS_KEYWORDS:
        t = re.sub(r"\b" + re.escape(loc) + r"\b", "", t).strip(" ,.-/()")
    return len(t) == 0

def clean_person_name(name: str) -> Tuple[str, str]:
    """
    Cleans a person's name by removing FB nicknames in parentheses or brackets,
    emojis, and numbers.
    Returns: (cleaned_accented_name, unaccented_name)
    """
    if not name or not isinstance(name, str):
        return "", ""
    n = name.strip()
    # Remove content in brackets/parentheses e.g. 'Lê Văn A (David Lê)' -> 'Lê Văn A'
    n = re.sub(r"[\(\[\{].*?[\)\]\}]", "", n).strip()
    # Remove numbers or special symbols
    n = re.sub(r"[0-9\-_:·|/*+@#!?]", " ", n).strip()
    n = re.sub(r"\s+", " ", n).strip()
    
    unacc = remove_vietnamese_accents(n)
    return n, unacc

def clean_company_name_for_search(company: str) -> str:
    """
    Extracts the core business name, stripping generic legal words like 'Công ty Cổ phần', 'TNHH', etc.
    Also detects if the input is purely a location and returns empty so it is not mistaken for a company.
    """
    if not company or str(company).strip() in ["Chưa cập nhật", "Ảo", "nan", "None", "Tự do", "Freelance"]:
        return ""
    comp = str(company).strip()
    
    # Check if purely location
    if is_location_only(comp):
        return ""

    # Strip common legal prefixes and suffixes
    comp = re.sub(r"(?i)\b(công ty cổ phần|công ty cp|công ty tnhh mtv|công ty tnhh|công ty|tập đoàn|doanh nghiệp / đơn vị|hộ kinh doanh / thương hiệu|thương hiệu|chi nhánh|tổng công ty)\b", "", comp)
    comp = re.sub(r"(?i)\b(jsc|ltd|co\.,\s*ltd|corp|holding|group)\b", "", comp)
    comp = comp.strip(" -–:·,")
    
    # If the remaining is too short or is a location, return empty
    if len(comp) < 2 or is_location_only(comp):
        return ""
    return comp

def clean_school_name_for_search(school: str) -> str:
    """Extracts the core university or school name for query dorking."""
    if not school or str(school).strip() in ["Chưa cập nhật", "Ảo", "nan", "None", "THPT", "Cấp 3"]:
        return ""
    sch = str(school).strip()
    sch_lower = sch.lower()
    if "kinh tế quốc dân" in sch_lower or "neu" in sch_lower:
        return "NEU"
    if "ngoại thương" in sch_lower or "ftu" in sch_lower:
        return "FTU"
    if "bách khoa" in sch_lower or "hust" in sch_lower:
        return "Bách Khoa"
    if "kinh tế tp.hcm" in sch_lower or "kinh tế tphcm" in sch_lower or "ueh" in sch_lower:
        return "UEH"
    if "quốc gia hà nội" in sch_lower or "vnu" in sch_lower:
        return "Đại học Quốc gia"
    if "rmit" in sch_lower:
        return "RMIT"
    if "fpt" in sch_lower:
        return "FPT"
    if "ngân hàng" in sch_lower or "hub" in sch_lower:
        return "Đại học Ngân hàng"
    if "y dược" in sch_lower or "ump" in sch_lower:
        return "Đại học Y Dược"

    # General cleaning
    sch_clean = re.sub(r"(?i)\b(trường đại học|đại học|trường cao đẳng|cao đẳng|học viện|viện đào tạo|trường)\b", "", sch).strip(" -–:·,")
    return sch_clean if len(sch_clean) >= 3 else ""

def build_google_dork_query(name: str, company: str, job: str = "", school: str = "") -> str:
    """
    Constructs an optimized, localized Google Dork query to find authentic LinkedIn profiles in Vietnam.
    Always includes Vietnam localization and avoids pollution from generic or location strings.
    """
    name_clean, name_unaccent = clean_person_name(name)
    if not name_clean:
        return ""
        
    comp_clean = clean_company_name_for_search(company)
    school_clean = clean_school_name_for_search(school)
    
    # Accented vs unaccented name clause
    if name_unaccent and name_unaccent.lower() != name_clean.lower():
        name_clause = f'("{name_clean}" OR "{name_unaccent}")'
    else:
        name_clause = f'"{name_clean}"'

    # Dork Priority:
    # 1. Name + Company + Vietnam
    if comp_clean:
        return f'site:linkedin.com/in {name_clause} "{comp_clean}" "Vietnam"'
    # 2. Name + School + Vietnam (when company is empty/generic)
    elif school_clean:
        return f'site:linkedin.com/in {name_clause} "{school_clean}" "Vietnam"'
    # 3. Name + Specific Job + Vietnam
    elif job and job not in ["Chưa cập nhật", "Worked", "University", "Former Management", "Ảo / Đùa cợt", "nan"]:
        clean_job = re.sub(r"(?i)\b(works at|worked at|làm việc tại)\b", "", job).strip()
        if len(clean_job) >= 3:
            return f'site:linkedin.com/in {name_clause} "{clean_job}" "Vietnam"'
        else:
            return f'site:linkedin.com/in {name_clause} "Vietnam"'
    # 4. Name + Vietnam
    else:
        return f'site:linkedin.com/in {name_clause} "Vietnam"'

def generate_google_search_url(name: str, company: str, job: str = "", school: str = "") -> str:
    """Generates direct 1-click Google Search link for manual inspection."""
    query = build_google_dork_query(name, company, job, school)
    return f"https://www.google.com/search?q={quote_plus(query)}"

def search_serper_single(query: str, api_key: str, timeout: int = 15) -> List[Dict[str, Any]]:
    """
    Executes a single search request via Serper.dev API.
    Returns list of organic search results with 'title', 'link', 'snippet'.
    """
    if not api_key or not query:
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

def extract_profile_name_from_candidate(title: str, url: str) -> str:
    """
    Extracts the individual's profile name from the Google title (e.g. 'Phan Hữu Lộc - Trainer | Author')
    or from the LinkedIn URL slug.
    """
    if title:
        parts = re.split(r"[-–—|·:]", title)
        if parts:
            cand = parts[0].strip()
            # Remove academic/honorary prefixes
            cand = re.sub(r"^(dr|mr|mrs|ms|ts|th\s*s)\.?\s+", "", cand, flags=re.IGNORECASE)
            if len(cand) >= 2:
                return cand

    if "linkedin.com/in/" in url.lower():
        slug = url.lower().split("/in/")[-1].split("?")[0].strip("/")
        parts = slug.split("-")
        words = [p for p in parts if not re.match(r"^[0-9a-f]{4,}$", p) and not p.isdigit()]
        if words:
            return " ".join(words)

    return ""

def evaluate_linkedin_candidate(
    lead_name: str,
    lead_company: str,
    lead_job: str,
    lead_school: str,
    search_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Strict multi-point verification for LinkedIn matching.
    Guarantees zero false fallbacks: if confidence threshold or name verification fails,
    returns empty URL rather than misattributing another person's profile.
    """
    empty_result = {
        "linkedin_url": "",
        "linkedin_title": "Chưa tìm thấy profile trùng khớp",
        "linkedin_snippet": "",
        "match_score": "Chưa tìm thấy",
        "match_percent": 0,
        "confidence_level": "Không có"
    }

    if not search_results:
        return empty_result

    lead_name_clean, lead_name_unaccent = clean_person_name(lead_name)
    name_words = [w for w in lead_name_unaccent.lower().split() if len(w) > 1]
    if not name_words:
        return empty_result

    first_name = name_words[-1]  # Tên chính (Given name in Vietnamese naming convention)
    family_name = name_words[0]  # Họ

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

        # Profile name extracted from title / slug
        cand_name = extract_profile_name_from_candidate(title, link)
        cand_name_unaccent = remove_vietnamese_accents(cand_name).lower()
        url_slug = remove_vietnamese_accents(link.lower().split("/in/")[-1].split("?")[0].replace("-", " "))

        # ==========================================
        # GATE 1: STRICT NAME VERIFICATION
        # ==========================================
        # 1. The first name (tên chính) MUST appear in the candidate's name or url slug
        first_name_in_cand = (
            re.search(r"\b" + re.escape(first_name) + r"\b", cand_name_unaccent) is not None or
            first_name in url_slug.split() or
            (len(cand_name_unaccent) < 3 and re.search(r"\b" + re.escape(first_name) + r"\b", combined_unaccent) is not None)
        )
        if not first_name_in_cand:
            # Does not match the lead's first name -> REJECT CANDIDATE IMMEDIATELY!
            continue

        # 2. Check multi-word name overlap
        matched_words = [
            w for w in name_words
            if (re.search(r"\b" + re.escape(w) + r"\b", cand_name_unaccent) or
                w in url_slug.split() or
                re.search(r"\b" + re.escape(w) + r"\b", combined_unaccent))
        ]

        all_words_matched = (len(matched_words) == len(name_words))

        if len(name_words) == 1:
            name_score = 25
        elif len(name_words) == 2:
            if not all_words_matched:
                continue  # 2-word name must match both words!
            name_score = 45
        elif len(name_words) >= 3:
            if len(matched_words) < 2:
                continue
            if all_words_matched:
                name_score = 60  # Rare full name match
            elif family_name in matched_words and first_name in matched_words:
                name_score = 50
            elif len(matched_words) >= len(name_words) - 1:
                name_score = 45
            else:
                continue

        # ==========================================
        # GATE 2: SECONDARY CONFIRMATION SIGNALS
        # ==========================================
        has_secondary = False
        comp_score = 0
        school_score = 0
        job_score = 0

        # A. Company / Brand Core
        comp_clean = clean_company_name_for_search(lead_company)
        if comp_clean:
            comp_unacc = remove_vietnamese_accents(comp_clean).lower()
            comp_tokens = [w for w in re.split(r"[^a-zA-Z0-9]+", comp_unacc) if len(w) > 1 and w not in GENERIC_COMP_STOPWORDS and w not in name_words]
            if comp_tokens:
                comp_phrase = " ".join(comp_tokens)
                if comp_phrase in combined_unaccent:
                    comp_score = 45
                    has_secondary = True
                elif len(comp_tokens) >= 2 and all(w in combined_unaccent for w in comp_tokens):
                    comp_score = 40
                    has_secondary = True
                elif any(len(w) >= 4 and re.search(r"\b" + re.escape(w) + r"\b", combined_unaccent) for w in comp_tokens):
                    comp_score = 30
                    has_secondary = True

        # B. University / School
        sch_clean = clean_school_name_for_search(lead_school)
        if sch_clean:
            sch_unacc = remove_vietnamese_accents(sch_clean).lower()
            sch_tokens = [w for w in re.split(r"[^a-zA-Z0-9]+", sch_unacc) if len(w) >= 3 and w not in ["truong", "dai", "hoc", "cao", "dang", "vien"]]
            if sch_tokens:
                if all(w in combined_unaccent for w in sch_tokens):
                    school_score = 35
                    has_secondary = True
                elif any(w in combined_unaccent for w in sch_tokens if len(w) >= 3):
                    school_score = 25
                    has_secondary = True

        # C. Job / Professional Role
        if lead_job and lead_job not in ["Chưa cập nhật", "Worked", "University", "Former Management", "Ảo / Đùa cợt", "nan"]:
            j_unacc = remove_vietnamese_accents(lead_job).lower()
            role_synonyms = []
            if any(k in j_unacc for k in ["ceo", "giam doc", "chu tich", "founder"]):
                role_synonyms.extend(["ceo", "founder", "director", "owner", "president", "chief", "co-founder", "executive"])
            if "marketing" in j_unacc:
                role_synonyms.extend(["marketing", "growth", "brand", "cmo"])
            if any(k in j_unacc for k in ["quan ly", "manager"]):
                role_synonyms.extend(["manager", "lead", "head"])
            if any(k in j_unacc for k in ["ban hang", "sales", "kinh doanh"]):
                role_synonyms.extend(["sales", "business", "bd", "account"])
            if any(k in j_unacc for k in ["ky su", "engineer", "developer", "cntt", "lap trinh"]):
                role_synonyms.extend(["engineer", "developer", "software", "tech"])
            if any(k in j_unacc for k in ["bac si", "doctor", "nha khoa", "duoc si"]):
                role_synonyms.extend(["doctor", "dentist", "pharmacist", "dr", "clinic"])

            j_tokens = [w for w in re.split(r"[^a-zA-Z0-9]+", j_unacc) if len(w) >= 3 and w not in ["lam", "tai", "viec", "cua", "nguoi"]]
            matched_job = any(w in combined_unaccent for w in j_tokens) or any(re.search(r"\b" + re.escape(syn) + r"\b", combined_unaccent) for syn in role_synonyms)
            if matched_job:
                job_score = 20
                has_secondary = True

        # D. Vietnam Geographic confirmation
        geo_score = 0
        if "vietnam" in combined_unaccent or "viet nam" in combined_unaccent or "hanoi" in combined_unaccent or "ho chi minh" in combined_unaccent:
            geo_score = 10
            # If full unique 3-4 word name matched in Vietnam, that serves as valid confirmation
            if name_score >= 60:
                has_secondary = True

        total_candidate_score = name_score + comp_score + school_score + job_score + geo_score

        # Must have at least 1 secondary confirmation to avoid matching strangers with the same name!
        if not has_secondary:
            continue

        if total_candidate_score > best_score:
            best_score = total_candidate_score
            best_match = {
                "linkedin_url": link,
                "linkedin_title": title,
                "linkedin_snippet": snippet,
                "score": total_candidate_score
            }

    # ==========================================
    # GATE 3: STRICT THRESHOLD & ZERO FALLBACK
    # ==========================================
    if not best_match or best_score < 50:
        # NO FALLBACK! Return clean empty
        return empty_result

    if best_score >= 75:
        conf_label = "Khớp cao (90-100%)"
        conf_tier = "Cao"
    elif best_score >= 50:
        conf_label = "Khớp vừa (60-80%)"
        conf_tier = "Trung bình"
    else:
        return empty_result

    return {
        "linkedin_url": best_match["linkedin_url"],
        "linkedin_title": best_match["linkedin_title"],
        "linkedin_snippet": best_match["linkedin_snippet"],
        "match_score": conf_label,
        "match_percent": best_score,
        "confidence_level": conf_tier
    }

def recheck_and_clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Re-evaluates existing matched leads in a DataFrame using the stored Title, Snippet,
    and metadata against the strict verification rules.
    Safely eliminates false positives (clearing their Link LinkedIn) without consuming any Serper API calls!
    Returns (cleaned_df, retained_count, cleaned_count).
    """
    cleaned_df = df.copy()
    if "Link LinkedIn" not in cleaned_df.columns:
        return cleaned_df, 0, 0

    has_li = cleaned_df["Link LinkedIn"].fillna("").astype(str).str.contains("linkedin.com/in", na=False)
    indices_to_check = cleaned_df[has_li].index

    retained_count = 0
    cleaned_count = 0

    for idx in indices_to_check:
        row = cleaned_df.loc[idx]
        name = str(row.get("Họ và tên", ""))
        comp = str(row.get("Tên công ty / Đơn vị", ""))
        job = str(row.get("Chức vụ", ""))
        school = str(row.get("Trường học / Học vấn", ""))
        url = str(row.get("Link LinkedIn", ""))
        title = str(row.get("Tiêu đề LinkedIn", ""))
        snippet = str(row.get("Tóm tắt LinkedIn", ""))

        pseudo_results = [{
            "link": url,
            "title": title,
            "snippet": snippet
        }]

        eval_res = evaluate_linkedin_candidate(name, comp, job, school, pseudo_results)

        if eval_res["linkedin_url"]:
            # Valid match confirmed!
            cleaned_df.at[idx, "Độ khớp LinkedIn"] = eval_res["match_score"]
            retained_count += 1
        else:
            # False positive or unverified match -> Clear link!
            cleaned_df.at[idx, "Link LinkedIn"] = ""
            cleaned_df.at[idx, "Độ khớp LinkedIn"] = "Chưa tìm thấy"
            if "Tìm trên Google" not in cleaned_df.columns or not cleaned_df.at[idx, "Tìm trên Google"]:
                cleaned_df.at[idx, "Tìm trên Google"] = generate_google_search_url(name, comp, job, school)
            cleaned_count += 1

    # Drop verbose columns
    for c in ["Tiêu đề LinkedIn", "Tóm tắt LinkedIn", "Mô tả gốc", "Ghi chú AI"]:
        if c in cleaned_df.columns:
            cleaned_df.drop(columns=[c], inplace=True)

    return cleaned_df, retained_count, cleaned_count

def match_single_lead(row_dict: Dict[str, Any], serper_key: str) -> Dict[str, Any]:
    """Helper to process a single lead row with full contextual signals."""
    name = str(row_dict.get("Họ và tên", "")).strip()
    comp = str(row_dict.get("Tên công ty / Đơn vị", "")).strip()
    job = str(row_dict.get("Chức vụ", "")).strip()
    school = str(row_dict.get("Trường học / Học vấn", "")).strip()

    search_url = generate_google_search_url(name, comp, job, school)
    
    if not serper_key:
        return {
            "Link LinkedIn": "",
            "Độ khớp LinkedIn": "Chưa tra cứu tự động",
            "Tìm trên Google": search_url
        }

    query = build_google_dork_query(name, comp, job, school)
    results = search_serper_single(query, serper_key)
    eval_res = evaluate_linkedin_candidate(name, comp, job, school, results)

    return {
        "Link LinkedIn": eval_res["linkedin_url"],
        "Độ khớp LinkedIn": eval_res["match_score"],
        "Tìm trên Google": search_url
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
    rows_data = [row.to_dict() for _, row in out_df.iterrows()]
    total_leads = len(rows_data)
    results_list = [None] * total_leads

    if not serper_key:
        # Just generate 1-click Google search links instantly without API
        for pos, r_dict in enumerate(rows_data):
            match_res = match_single_lead(r_dict, "")
            results_list[pos] = match_res
            if progress_callback:
                progress_callback(pos + 1, total_leads, f"Tạo liên kết tra cứu: {pos+1}/{total_leads}")
    else:
        # Concurrent API calls
        done_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_pos = {
                executor.submit(match_single_lead, r_dict, serper_key): pos
                for pos, r_dict in enumerate(rows_data)
            }
            for future in as_completed(future_to_pos):
                pos = future_to_pos[future]
                r_dict = rows_data[pos]
                name = str(r_dict.get("Họ và tên", ""))
                comp = str(r_dict.get("Tên công ty / Đơn vị", ""))
                job = str(r_dict.get("Chức vụ", ""))
                school = str(r_dict.get("Trường học / Học vấn", ""))
                try:
                    res = future.result()
                    results_list[pos] = res
                except Exception:
                    results_list[pos] = {
                        "Link LinkedIn": "",
                        "Độ khớp LinkedIn": "Chưa tìm thấy",
                        "Tìm trên Google": generate_google_search_url(name, comp, job, school)
                    }
                done_count += 1
                if progress_callback:
                    progress_callback(done_count, total_leads, f"Đang tra cứu LinkedIn ({done_count}/{total_leads}): {name}")

    # Assign new columns to DataFrame
    out_df["Link LinkedIn"] = [r.get("Link LinkedIn", "") if r else "" for r in results_list]
    out_df["Độ khớp LinkedIn"] = [r.get("Độ khớp LinkedIn", "") if r else "" for r in results_list]
    out_df["Tìm trên Google"] = [r.get("Tìm trên Google", "") if r else "" for r in results_list]

    # Drop verbose columns
    for c in ["Tiêu đề LinkedIn", "Tóm tắt LinkedIn", "Mô tả gốc", "Ghi chú AI"]:
        if c in out_df.columns:
            out_df.drop(columns=[c], inplace=True)

    return out_df
