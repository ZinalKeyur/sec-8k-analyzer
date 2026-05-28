"""
fetcher.py
==========
Downloads all 8-K filings from SEC EDGAR for today.
Uses the free EDGAR full-text search API — no API key needed.
"""

import requests
import time
from datetime import date, timedelta

HEADERS = {
    "User-Agent": "8K-Analyzer research@example.com",  # SEC requires a user-agent
    "Accept-Encoding": "gzip, deflate"
}

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BASE_URL   = "https://www.sec.gov"


def fetch_todays_8k_filings(days_back=1, max_filings=200):
    """
    Fetches all 8-K filings from the last N days.
    Returns a list of dicts with filing metadata + text.

    days_back=1  → today only
    days_back=3  → last 3 days (useful for Monday to catch Friday filings)
    """
    today     = date.today()
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date   = today.strftime("%Y-%m-%d")

    print(f"   🔍 Searching EDGAR for 8-K filings from {from_date} to {to_date}...")

    all_filings = []
    start = 0
    batch = 40  # EDGAR returns max 40 per request

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
            break

        print(f"   📥 Fetched batch {start}–{start+len(hits)} of filings...")

        for hit in hits:
            src = hit.get("_source", {})
            filing = {
                "ticker"      : src.get("tickers", ["N/A"])[0] if src.get("tickers") else "N/A",
                "company"     : src.get("entity_name", "Unknown"),
                "cik"         : src.get("ciks", [""])[0] if src.get("ciks") else "",
                "filed_at"    : src.get("file_date", ""),
                "form_type"   : src.get("form_type", "8-K"),
                "filing_url"  : EDGAR_BASE_URL + src.get("file_index_href", ""),
                "doc_url"     : "",
                "text"        : "",
                "items"       : src.get("items", []),
            }

            # Fetch the actual filing text
            text, doc_url = fetch_filing_text(src)
            filing["text"]    = text
            filing["doc_url"] = doc_url

            if text:
                all_filings.append(filing)

            time.sleep(0.12)  # be polite to SEC servers

        start += batch
        total_available = data.get("hits", {}).get("total", {}).get("value", 0)
        if start >= total_available or start >= max_filings:
            break

    return all_filings


def fetch_filing_text(source: dict) -> tuple:
    """
    Given a filing source dict from EDGAR search,
    fetch the actual document text.
    Returns (text, doc_url).
    """
    try:
        # Try inline text first (fastest)
        inline = source.get("file_text") or source.get("period_of_report", "")
        if inline and len(inline) > 200:
            return inline, ""

        # Get filing index page
        index_href = source.get("file_index_href", "")
        if not index_href:
            return "", ""

        index_url = EDGAR_BASE_URL + index_href
        resp = requests.get(index_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()

        # Find the primary document link
        import re
        # Look for .htm or .txt doc links
        matches = re.findall(r'href="(/Archives/edgar/data/[^"]+\.htm)"', resp.text, re.IGNORECASE)
        if not matches:
            matches = re.findall(r'href="(/Archives/edgar/data/[^"]+\.txt)"', resp.text, re.IGNORECASE)

        if not matches:
            return "", index_url

        doc_url = EDGAR_BASE_URL + matches[0]
        doc_resp = requests.get(doc_url, headers=HEADERS, timeout=10)
        doc_resp.raise_for_status()

        # Strip HTML tags for plain text
        clean_text = re.sub(r'<[^>]+>', ' ', doc_resp.text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        return clean_text[:15000], doc_url  # cap at 15k chars per filing

    except Exception:
        return "", ""
