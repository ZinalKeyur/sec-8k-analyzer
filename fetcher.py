"""
fetcher.py — SEC EDGAR 8-K fetcher with robust text extraction
"""

import requests
import re
import time
from datetime import date, timedelta

HEADERS = {
    "User-Agent": "8K-Analyzer your@email.com",
    "Accept-Encoding": "gzip, deflate",
}

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BASE_URL   = "https://www.sec.gov"


def fetch_todays_8k_filings(days_back=1, max_filings=200):
    today     = date.today()
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date   = today.strftime("%Y-%m-%d")

    print(f"   🔍 Searching EDGAR: {from_date} → {to_date}")

    all_filings = []
    start = 0
    batch = 40

    while len(all_filings) < max_filings:
        params = {
            "forms"    : "8-K",
            "dateRange": "custom",
            "startdt"  : from_date,
            "enddt"    : to_date,
            "from"     : start,
            "size"     : batch,
        }
        try:
            resp  = requests.get(EDGAR_SEARCH_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data  = resp.json()
        except Exception as e:
            print(f"   ❌ Search error at offset {start}: {e}")
            break

        hits  = data.get("hits", {}).get("hits", [])
        total = data.get("hits", {}).get("total", {}).get("value", 0)

        if not hits:
            break

        print(f"   📥 Fetched batch {start}–{start+len(hits)} (total: {total})...")

        for hit in hits:
            src  = hit.get("_source", {})
            adsh = src.get("adsh", "")
            ciks = src.get("ciks", [])
            cik  = ciks[0].lstrip("0") if ciks else ""

            # ── Parse display_names string ─────────────────────────────
            company   = "Unknown"
            ticker    = "N/A"
            raw_names = src.get("display_names", [])

            if raw_names:
                name_str = raw_names[0] if isinstance(raw_names, list) else raw_names
                m = re.match(r'^([^(]+)', name_str)
                if m:
                    company = m.group(1).strip()
                all_parens = re.findall(r'\(([^)]+)\)', name_str)
                for group in all_parens:
                    group = group.strip()
                    if group.upper().startswith("CIK"):
                        continue
                    first = group.split(",")[0].strip()
                    if re.match(r'^[A-Z][A-Z0-9\-\.]{0,8}$', first):
                        ticker = first
                        break

            # ── Build filing index URL ─────────────────────────────────
            adsh_no_dashes = adsh.replace("-", "")
            index_url = ""
            doc_hint  = hit.get("_id", "")   # e.g. "0000051143-26-000047:ibm-20260528.htm"
            hint_file = doc_hint.split(":")[-1] if ":" in doc_hint else ""

            if cik and adsh:
                index_url = (
                    f"{EDGAR_BASE_URL}/Archives/edgar/data/{cik}"
                    f"/{adsh_no_dashes}/{adsh}-index.htm"
                )

            filing = {
                "ticker"    : ticker,
                "company"   : company,
                "cik"       : cik,
                "filed_at"  : src.get("file_date", ""),
                "form_type" : src.get("file_type", "8-K"),
                "filing_url": index_url,
                "doc_url"   : "",
                "text"      : "",
                "item_texts": {},
                "items"     : src.get("items", []),
                "location"  : src.get("biz_locations", [""])[0] if src.get("biz_locations") else "",
            }

            # Try direct document URL first using the hint from _id
            text, doc_url = fetch_filing_text(
                cik, adsh_no_dashes, adsh, hint_file, index_url
            )
            filing["text"]    = text
            filing["doc_url"] = doc_url

            # Parse item sections from text
            if text:
                filing["item_texts"] = extract_item_sections(text)

            all_filings.append(filing)
            time.sleep(0.1)

        start += batch
        if start >= total or start >= max_filings:
            break

    return all_filings


def fetch_filing_text(cik, adsh_no_dashes, adsh, hint_file, index_url):
    """
    Try multiple strategies to get full filing text.
    Returns (text, doc_url).
    """

    # Strategy 1 — use the _id hint to go directly to the primary document
    # _id format: "0000051143-26-000047:ibm-20260528.htm"
    if cik and adsh_no_dashes and hint_file:
        try:
            doc_url  = f"{EDGAR_BASE_URL}/Archives/edgar/data/{cik}/{adsh_no_dashes}/{hint_file}"
            resp     = requests.get(doc_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                text = strip_html(resp.text)
                if len(text) > 300:
                    return text[:50000], doc_url
        except Exception:
            pass

    # Strategy 2 — parse the index page and find primary htm document
    if index_url:
        try:
            resp = requests.get(index_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            # Find all .htm links, skip index files
            links = re.findall(
                r'href="(/Archives/edgar/data/[^"]+\.htm)"',
                resp.text, re.IGNORECASE
            )
            links = [l for l in links if "index" not in l.lower()]
            if links:
                doc_url  = EDGAR_BASE_URL + links[0]
                doc_resp = requests.get(doc_url, headers=HEADERS, timeout=12)
                doc_resp.raise_for_status()
                text = strip_html(doc_resp.text)
                if len(text) > 300:
                    return text[:50000], doc_url
        except Exception:
            pass

    # Strategy 3 — full submission .txt file
    if cik and adsh:
        try:
            txt_url  = f"{EDGAR_BASE_URL}/Archives/edgar/data/{cik}/{adsh_no_dashes}/{adsh}.txt"
            resp     = requests.get(txt_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                text = strip_html(resp.text)
                if len(text) > 300:
                    return text[:50000], txt_url
        except Exception:
            pass

    return "", ""


def extract_item_sections(text):
    """
    Parse the filing text and extract each Item section.
    Returns dict like:
    {
      "7.01": "Item 7.01. Regulation FD Disclosure. The information...",
      "8.01": "Item 8.01. Other Events. ...",
    }
    """
    items = {}

    # Find all "Item X.XX" occurrences and split text at each
    pattern = r'(Item\s+(\d+\.\d+)[^\n]*(?:\n|\.)[^\n]*)'
    splits  = re.split(r'(?=Item\s+\d+\.\d+)', text, flags=re.IGNORECASE)

    for chunk in splits:
        m = re.match(r'Item\s+(\d+\.\d+)', chunk, re.IGNORECASE)
        if m:
            item_num = m.group(1)
            # Clean up and take up to 2000 chars of this item's text
            clean = re.sub(r'\s+', ' ', chunk).strip()
            items[item_num] = clean[:2000]

    return items


def strip_html(html):
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&nbsp;',  ' ', text)
    text = re.sub(r'&amp;',   '&', text)
    text = re.sub(r'&lt;',    '<', text)
    text = re.sub(r'&gt;',    '>', text)
    text = re.sub(r'&#\d+;',  ' ', text)
    text = re.sub(r'\s+',     ' ', text)
    return text.strip()
