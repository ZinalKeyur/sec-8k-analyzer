"""
fetcher.py
==========
Downloads all 8-K filings from SEC EDGAR using the official EDGAR REST API.
No API key needed. Free.
"""

import requests
import re
import time
import json
from datetime import date, timedelta

HEADERS = {
    "User-Agent": "8K-Analyzer your@email.com",  # SEC requires real contact info
    "Accept"    : "application/json",
}

EDGAR_FULL_TEXT  = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BROWSE     = "https://www.sec.gov/cgi-bin/browse-edgar"
EDGAR_BASE_URL   = "https://www.sec.gov"
SUBMISSIONS_URL  = "https://data.sec.gov/submissions"


def fetch_todays_8k_filings(days_back=1, max_filings=200):
    """
    Fetch all 8-K filings from the last N days.
    Uses EDGAR full-text search + submissions API for company/ticker data.
    """
    today     = date.today()
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date   = today.strftime("%Y-%m-%d")

    print(f"   🔍 Searching EDGAR: {from_date} → {to_date}")

    # Step 1: get filing list from full-text search
    raw_filings = get_filing_list(from_date, to_date, max_filings)
    print(f"   📋 Raw filings found: {len(raw_filings)}")

    # Step 2: enrich each filing with company info + text
    enriched = []
    for i, f in enumerate(raw_filings, 1):
        filing = enrich_filing(f)
        enriched.append(filing)
        if i % 25 == 0:
            print(f"   ⏳ Enriched {i}/{len(raw_filings)} filings...")
        time.sleep(0.12)  # respect SEC rate limit

    return enriched


def get_filing_list(from_date, to_date, max_filings):
    """Get list of 8-K filings from EDGAR search."""
    filings = []
    start   = 0
    batch   = 40

    while len(filings) < max_filings:
        params = {
            "forms"    : "8-K",
            "dateRange": "custom",
            "startdt"  : from_date,
            "enddt"    : to_date,
            "from"     : start,
            "size"     : batch,
        }
        try:
            resp = requests.get(
                EDGAR_FULL_TEXT, params=params,
                headers=HEADERS, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"   ❌ Search API error at offset {start}: {e}")
            break

        hits  = data.get("hits", {}).get("hits", [])
        total = data.get("hits", {}).get("total", {}).get("value", 0)

        if not hits:
            break

        print(f"   📥 Got batch {start}–{start+len(hits)} of {total} total...")

        for hit in hits:
            src = hit.get("_source", {})
            filings.append({
                "_id"        : hit.get("_id", ""),
                "source"     : src,
            })

        start += batch
        if start >= total or start >= max_filings:
            break

    return filings


def enrich_filing(raw):
    """
    Given a raw hit from EDGAR search, extract all useful fields.
    Tries multiple field name variants since EDGAR API field names vary.
    """
    src = raw.get("source", {})
    _id = raw.get("_id", "")

    # ── COMPANY NAME ──────────────────────────────────────────────────────
    # Try every known field name EDGAR uses
    company = (
        src.get("entity_name") or
        src.get("display_names", [{}])[0].get("name", "") if src.get("display_names") else "" or
        src.get("company_name") or
        src.get("name") or
        "Unknown"
    )
    # display_names is a list of dicts like [{"name": "Apple Inc", "ticker": "AAPL"}]
    display_names = src.get("display_names", [])
    if display_names and isinstance(display_names, list):
        first = display_names[0]
        if isinstance(first, dict):
            company = first.get("name", company)

    # ── TICKER ────────────────────────────────────────────────────────────
    ticker = "N/A"
    # Try display_names first (most reliable)
    if display_names and isinstance(display_names, list):
        first = display_names[0]
        if isinstance(first, dict) and first.get("ticker"):
            ticker = first.get("ticker")
    # Fallback to tickers list
    if ticker == "N/A":
        tickers_list = src.get("tickers", [])
        if tickers_list:
            ticker = tickers_list[0]

    # ── CIK ───────────────────────────────────────────────────────────────
    ciks = src.get("ciks", []) or src.get("cik", [])
    cik  = ciks[0] if ciks else ""
    if not cik and display_names:
        first = display_names[0]
        if isinstance(first, dict):
            cik = str(first.get("cik", ""))

    # ── ACCESSION / URLS ──────────────────────────────────────────────────
    accession    = _id.replace("-", "")
    index_href   = src.get("file_index_href", "")
    filing_url   = (EDGAR_BASE_URL + index_href) if index_href else ""

    # ── DATES ─────────────────────────────────────────────────────────────
    filed_at = (
        src.get("file_date") or
        src.get("period_of_report") or
        src.get("filed") or ""
    )

    # ── ITEMS ─────────────────────────────────────────────────────────────
    items = src.get("items", []) or src.get("form_items", [])

    # ── TEXT ──────────────────────────────────────────────────────────────
    text, doc_url = fetch_filing_text(filing_url, cik, accession)

    return {
        "ticker"     : ticker,
        "company"    : company,
        "cik"        : cik,
        "filed_at"   : filed_at,
        "form_type"  : src.get("form_type", "8-K"),
        "filing_url" : filing_url,
        "doc_url"    : doc_url,
        "text"       : text,
        "items"      : items,
    }


def fetch_filing_text(index_url, cik, accession):
    """
    Try to get the actual filing text.
    Returns (text, doc_url). Never crashes.
    """
    # Strategy 1 — parse the index page HTML for the primary document link
    if index_url:
        try:
            resp = requests.get(index_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            # Find .htm links in the index page (exclude index files themselves)
            links = re.findall(
                r'href="(/Archives/edgar/data/[^"]+\.htm)"',
                resp.text, re.IGNORECASE
            )
            links = [l for l in links if "index" not in l.lower()]
            if not links:
                links = re.findall(
                    r'href="(/Archives/edgar/data/[^"]+\.txt)"',
                    resp.text, re.IGNORECASE
                )
            if links:
                doc_url  = EDGAR_BASE_URL + links[0]
                doc_resp = requests.get(doc_url, headers=HEADERS, timeout=10)
                doc_resp.raise_for_status()
                text = strip_html(doc_resp.text)
                if len(text) > 200:
                    return text[:20000], doc_url
        except Exception:
            pass

    # Strategy 2 — EDGAR submissions API for company info fallback
    if cik:
        try:
            cik_padded = str(cik).zfill(10)
            url  = f"{SUBMISSIONS_URL}/CIK{cik_padded}.json"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                # We at least have company data — text not available via this endpoint
                pass
        except Exception:
            pass

    # Strategy 3 — direct .txt filing URL
    if cik and accession and len(accession) >= 18:
        try:
            acc_fmt  = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
            txt_url  = f"{EDGAR_BASE_URL}/Archives/edgar/data/{cik}/{accession}/{acc_fmt}.txt"
            resp     = requests.get(txt_url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                text = strip_html(resp.text)
                if len(text) > 200:
                    return text[:20000], txt_url
        except Exception:
            pass

    return "", ""


def strip_html(html_text):
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;',  '&', text)
    text = re.sub(r'&lt;',   '<', text)
    text = re.sub(r'&gt;',   '>', text)
    text = re.sub(r'\s+',    ' ', text)
    return text.strip()
