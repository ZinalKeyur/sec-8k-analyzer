"""
fetcher.py — SEC EDGAR 8-K fetcher
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
            adsh = src.get("adsh", "")          # e.g. "0001104659-26-067209"
            ciks = src.get("ciks", [])
            cik  = ciks[0].lstrip("0") if ciks else ""   # strip leading zeros for URL

            # ── Parse display_names string ─────────────────────────────
            # Format: "Hyatt Hotels Corp  (H)  (CIK 0001468174)"
            # or with multiple tickers: "Regency Centers Corp  (REG, REGCO)  (CIK 0000910606)"
            company = "Unknown"
            ticker  = "N/A"
            raw_names = src.get("display_names", [])

            if raw_names:
                name_str = raw_names[0] if isinstance(raw_names, list) else raw_names
                # Extract company name — everything before the first (
                m_company = re.match(r'^([^(]+)', name_str)
                if m_company:
                    company = m_company.group(1).strip()

                # Extract first ticker — first word inside first ()
                m_ticker = re.search(r'\(([^C][^I][^K][^)]+)\)', name_str)
                if m_ticker:
                    # Could be "H" or "REG, REGCO, REGCP" — take first
                    ticker = m_ticker.group(1).split(",")[0].strip()

            # ── Build filing index URL ─────────────────────────────────
            # URL format: /Archives/edgar/data/{cik}/{adsh_no_dashes}/{adsh}-index.htm
            adsh_no_dashes = adsh.replace("-", "")
            if cik and adsh:
                index_url = (
                    f"{EDGAR_BASE_URL}/Archives/edgar/data/{cik}"
                    f"/{adsh_no_dashes}/{adsh}-index.htm"
                )
            else:
                index_url = ""

            filing = {
                "ticker"    : ticker,
                "company"   : company,
                "cik"       : cik,
                "filed_at"  : src.get("file_date", ""),
                "form_type" : src.get("form_type", src.get("file_type", "8-K")),
                "filing_url": index_url,
                "doc_url"   : "",
                "text"      : "",
                "items"     : src.get("items", []),
                "location"  : src.get("biz_locations", [""])[0] if src.get("biz_locations") else "",
            }

            # Fetch actual filing text
            text, doc_url = fetch_filing_text(index_url, cik, adsh_no_dashes, adsh)
            filing["text"]    = text
            filing["doc_url"] = doc_url

            all_filings.append(filing)
            time.sleep(0.1)

        start += batch
        if start >= total or start >= max_filings:
            break

    return all_filings


def fetch_filing_text(index_url, cik, adsh_no_dashes, adsh):
    """
    Fetch the actual 8-K document text.
    Returns (text, doc_url). Never crashes.
    """
    # Strategy 1 — parse the index page to find the primary .htm document
    if index_url:
        try:
            resp = requests.get(index_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            # Find .htm links that are NOT the index itself
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
                if len(text) > 200:
                    return text[:20000], doc_url
        except Exception:
            pass

    # Strategy 2 — try the raw .txt full submission file
    if cik and adsh:
        try:
            txt_url  = f"{EDGAR_BASE_URL}/Archives/edgar/data/{cik}/{adsh_no_dashes}/{adsh}.txt"
            resp     = requests.get(txt_url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                text = strip_html(resp.text)
                if len(text) > 200:
                    return text[:20000], txt_url
        except Exception:
            pass

    return "", ""


def strip_html(html):
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;',  '&', text)
    text = re.sub(r'&lt;',   '<', text)
    text = re.sub(r'&gt;',   '>', text)
    text = re.sub(r'\s+',    ' ', text)
    return text.strip()
