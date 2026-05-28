"""
fetcher.py
==========
Downloads all 8-K filings from SEC EDGAR for today.
Uses the free EDGAR full-text search API — no API key needed.
"""

import requests
import re
import time
from datetime import date, timedelta

HEADERS = {
    "User-Agent": "8K-Analyzer research@example.com",
    "Accept-Encoding": "gzip, deflate"
}

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BASE_URL   = "https://www.sec.gov"


def fetch_todays_8k_filings(days_back=1, max_filings=200):
    today     = date.today()
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date   = today.strftime("%Y-%m-%d")

    print(f"   🔍 Searching EDGAR for 8-K filings from {from_date} to {to_date}...")

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
            resp = requests.get(EDGAR_SEARCH_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"   ❌ Error fetching index: {e}")
            break

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            print(f"   ⚠️  No hits returned at offset {start}")
            break

        total_available = data.get("hits", {}).get("total", {}).get("value", 0)
        print(f"   📥 Fetched batch {start}–{start + len(hits)} (total available: {total_available})...")

        for hit in hits:
            src = hit.get("_source", {})

            # Build the filing index URL from CIK + accession number
            ciks         = src.get("ciks", [""])
            cik          = ciks[0] if ciks else ""
            accession    = hit.get("_id", "").replace("-", "")
            file_date    = src.get("file_date", "")

            # Build index URL two ways
            index_href   = src.get("file_index_href", "")
            if index_href:
                index_url = EDGAR_BASE_URL + index_href
            elif cik and accession:
                # Standard EDGAR index URL format
                acc_fmt   = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
                index_url = f"{EDGAR_BASE_URL}/Archives/edgar/data/{int(cik)}/{accession}/{acc_fmt}-index.htm"
            else:
                index_url = ""

            filing = {
                "ticker"     : src.get("tickers", ["N/A"])[0] if src.get("tickers") else "N/A",
                "company"    : src.get("entity_name", "Unknown"),
                "cik"        : cik,
                "filed_at"   : file_date,
                "form_type"  : src.get("form_type", "8-K"),
                "filing_url" : index_url,
                "doc_url"    : "",
                "text"       : "",
                "items"      : src.get("items", []),
            }

            # Try to get filing text — but ALWAYS add the filing even if text fails
            text, doc_url = fetch_filing_text(index_url, cik, accession)
            filing["text"]    = text
            filing["doc_url"] = doc_url

            # ✅ Always append — don't filter on text presence
            all_filings.append(filing)

            time.sleep(0.1)

        start += batch
        if start >= total_available or start >= max_filings:
            break

    return all_filings


def fetch_filing_text(index_url: str, cik: str, accession: str) -> tuple:
    """
    Try multiple strategies to get the text of a filing.
    Returns (text, doc_url). Returns ("", "") on failure — never crashes.
    """
    # Strategy 1 — fetch the filing index page and find the primary document
    if index_url:
        try:
            resp = requests.get(index_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            html = resp.text

            # Find primary document links (.htm files)
            links = re.findall(r'href="(/Archives/edgar/data/[^"]+\.htm)"', html, re.IGNORECASE)
            # Filter out index pages themselves
            links = [l for l in links if "-index" not in l.lower()]

            if not links:
                # Try .txt documents
                links = re.findall(r'href="(/Archives/edgar/data/[^"]+\.txt)"', html, re.IGNORECASE)

            if links:
                doc_url  = EDGAR_BASE_URL + links[0]
                doc_resp = requests.get(doc_url, headers=HEADERS, timeout=10)
                doc_resp.raise_for_status()
                # Strip HTML tags
                clean = re.sub(r'<[^>]+>', ' ', doc_resp.text)
                clean = re.sub(r'\s+', ' ', clean).strip()
                if len(clean) > 100:
                    return clean[:20000], doc_url
        except Exception:
            pass

    # Strategy 2 — try the EDGAR XBRL viewer JSON which contains filing text
    if cik and accession:
        try:
            acc_fmt  = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
            txt_url  = f"{EDGAR_BASE_URL}/Archives/edgar/data/{int(cik)}/{accession}/{acc_fmt}.txt"
            resp     = requests.get(txt_url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                clean = re.sub(r'<[^>]+>', ' ', resp.text)
                clean = re.sub(r'\s+', ' ', clean).strip()
                if len(clean) > 100:
                    return clean[:20000], txt_url
        except Exception:
            pass

    return "", ""
