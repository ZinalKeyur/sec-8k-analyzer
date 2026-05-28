"""
fetcher.py — SEC EDGAR 8-K fetcher
Fetches only primary 8-K documents (sequence=1, form=8-K, deduplicated by adsh)
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


def fetch_todays_8k_filings(days_back=1, max_filings=300):
    today     = date.today()
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date   = today.strftime("%Y-%m-%d")

    print(f"   🔍 Searching EDGAR: {from_date} → {to_date}")

    raw_hits   = []
    seen_adsh  = set()
    start      = 0
    batch      = 40

    # We fetch more than max_filings because many hits are exhibits/duplicates
    # We keep fetching until we have enough UNIQUE primary filings
    fetch_limit = max_filings * 4  # fetch up to 4x to account for duplicates

    while len(raw_hits) < fetch_limit:
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

        # ── Filter: only primary 8-K documents ─────────────────────
        # sequence=1   → primary document (not an exhibit)
        # root_forms   → must contain exactly "8-K" (not 8-K/A amendment)
        # adsh         → deduplicate (same filing can appear multiple times)
        kept = 0
        for hit in hits:
            src        = hit.get("_source", {})
            adsh       = src.get("adsh", "")
            sequence   = src.get("sequence", 99)
            root_forms = src.get("root_forms", [])
            file_type  = src.get("file_type", "")

            # Skip if not the primary document
            if sequence != 1:
                continue

            # Skip if not a pure 8-K (skip 8-K/A amendments)
            if "8-K" not in root_forms:
                continue
            if file_type not in ("8-K", ""):
                continue

            # Skip duplicates
            if adsh in seen_adsh:
                continue

            seen_adsh.add(adsh)
            raw_hits.append(hit)
            kept += 1

        print(f"   📥 Offset {start}: {len(hits)} hits → {kept} new unique 8-K filings "
              f"(total unique so far: {len(raw_hits)} of {total} available)")

        start += batch
        if start >= total:
            break

        # Stop if we have enough unique filings
        if len(raw_hits) >= max_filings:
            break

    print(f"\n   ✅ Total unique 8-K filings found: {len(raw_hits)}")

    # ── Now enrich each unique filing ──────────────────────────────
    all_filings = []
    for i, hit in enumerate(raw_hits, 1):
        filing = enrich_filing(hit)
        all_filings.append(filing)
        if i % 25 == 0:
            print(f"   ⏳ Fetching text for {i}/{len(raw_hits)} filings...")
        time.sleep(0.1)

    return all_filings


def enrich_filing(hit):
    src  = hit.get("_source", {})
    adsh = src.get("adsh", "")
    ciks = src.get("ciks", [])
    cik  = ciks[0].lstrip("0") if ciks else ""

    # ── Company & ticker from display_names ───────────────────────
    company   = "Unknown"
    ticker    = "N/A"
    raw_names = src.get("display_names", [])

    if raw_names:
        name_str = raw_names[0] if isinstance(raw_names, list) else raw_names
        m = re.match(r'^([^(]+)', name_str)
        if m:
            company = m.group(1).strip()
        for group in re.findall(r'\(([^)]+)\)', name_str):
            group = group.strip()
            if group.upper().startswith("CIK"):
                continue
            first = group.split(",")[0].strip()
            if re.match(r'^[A-Z][A-Z0-9\-\.]{0,8}$', first):
                ticker = first
                break

    # ── Filing URL ─────────────────────────────────────────────────
    adsh_no_dashes = adsh.replace("-", "")
    hint_file      = hit.get("_id", "").split(":")[-1] if ":" in hit.get("_id", "") else ""
    index_url = ""
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
        "form_type" : "8-K",
        "filing_url": index_url,
        "doc_url"   : "",
        "text"      : "",
        "item_texts": {},
        "items"     : src.get("items", []),
        "location"  : src.get("biz_locations", [""])[0] if src.get("biz_locations") else "",
    }

    # Fetch text
    text, doc_url = fetch_filing_text(cik, adsh_no_dashes, adsh, hint_file, index_url)
    filing["text"]    = text
    filing["doc_url"] = doc_url
    if text:
        filing["item_texts"] = extract_item_sections(text)

    return filing


def fetch_filing_text(cik, adsh_no_dashes, adsh, hint_file, index_url):
    # Strategy 1 — direct document via _id hint
    if cik and adsh_no_dashes and hint_file:
        try:
            doc_url = f"{EDGAR_BASE_URL}/Archives/edgar/data/{cik}/{adsh_no_dashes}/{hint_file}"
            resp    = requests.get(doc_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                text = strip_html(resp.text)
                if len(text) > 300:
                    return text[:50000], doc_url
        except Exception:
            pass

    # Strategy 2 — parse index page
    if index_url:
        try:
            resp  = requests.get(index_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
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

    # Strategy 3 — raw .txt submission
    if cik and adsh:
        try:
            txt_url = f"{EDGAR_BASE_URL}/Archives/edgar/data/{cik}/{adsh_no_dashes}/{adsh}.txt"
            resp    = requests.get(txt_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                text = strip_html(resp.text)
                if len(text) > 300:
                    return text[:50000], txt_url
        except Exception:
            pass

    return "", ""


def extract_item_sections(text):
    """Split text into per-item sections."""
    items = {}
    splits = re.split(r'(?=Item\s+\d+\.\d+)', text, flags=re.IGNORECASE)
    for chunk in splits:
        m = re.match(r'Item\s+(\d+\.\d+)', chunk, re.IGNORECASE)
        if m:
            item_num = m.group(1)
            clean    = re.sub(r'\s+', ' ', chunk).strip()
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
