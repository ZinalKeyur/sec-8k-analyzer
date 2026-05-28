"""
debug.py
========
Run this FIRST to see exactly what EDGAR returns for your filings.
This helps diagnose any field name issues.

Run with:  python3 debug.py
"""
import requests
import json
from datetime import date, timedelta

HEADERS = {"User-Agent": "8K-Analyzer your@email.com"}

today     = date.today()
from_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
to_date   = today.strftime("%Y-%m-%d")

print(f"Fetching 3 sample 8-K filings from {from_date} to {to_date}...\n")

resp = requests.get(
    "https://efts.sec.gov/LATEST/search-index",
    params={"forms": "8-K", "dateRange": "custom",
            "startdt": from_date, "enddt": to_date,
            "from": 0, "size": 3},
    headers=HEADERS, timeout=15
)
data = resp.json()
hits = data.get("hits", {}).get("hits", [])
total = data.get("hits", {}).get("total", {}).get("value", 0)

print(f"Total filings available today: {total}")
print(f"Showing first {len(hits)} raw _source fields:\n")
print("=" * 60)

for i, hit in enumerate(hits, 1):
    src = hit.get("_source", {})
    print(f"\n--- FILING {i} ---")
    print(f"  _id (accession): {hit.get('_id', '')}")
    print(f"  All available fields: {list(src.keys())}")
    print(f"\n  Full _source dump:")
    print(json.dumps(src, indent=4))
    print("-" * 60)
