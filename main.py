"""
SEC 8-K Analyzer
=================
Downloads all new 8-K filings from SEC EDGAR,
analyzes them for bullish/bearish signals,
and outputs an HTML report + CSV file.

Run manually:  python3 main.py
Scheduled:     set up via:  bash setup_cron.sh
"""

import os
from datetime import date
from fetcher import fetch_todays_8k_filings
from parser  import analyze_filings
from reporter import generate_html, generate_csv

OUTPUT_DIR = "output"

def run():
    today = date.today().strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"  SEC 8-K ANALYZER — {today}")
    print(f"{'='*60}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # STEP 1 — Fetch
    print("\n[STEP 1] Fetching today's 8-K filings from SEC EDGAR...")
    filings = fetch_todays_8k_filings()
    print(f"   ✅ Found {len(filings)} 8-K filings")

    if not filings:
        print("   ℹ️  No filings today (market may be closed). Exiting.")
        return

    # STEP 2 — Analyze
    print("\n[STEP 2] Parsing and analyzing filings...")
    results = analyze_filings(filings)
    print(f"   ✅ Analyzed {len(results)} filings")

    # STEP 3 — Output HTML
    html_path = os.path.join(OUTPUT_DIR, f"report_{today}.html")
    print(f"\n[STEP 3] Generating HTML report...")
    generate_html(results, html_path, today)
    print(f"   ✅ HTML saved: {html_path}")

    # STEP 4 — Output CSV
    csv_path = os.path.join(OUTPUT_DIR, f"report_{today}.csv")
    print(f"\n[STEP 4] Generating CSV...")
    generate_csv(results, csv_path)
    print(f"   ✅ CSV saved: {csv_path}")

    # STEP 5 — Open HTML in browser automatically
    print(f"\n[STEP 5] Opening report in browser...")
    os.system(f"open {html_path}")

    print(f"\n{'='*60}")
    print(f"  DONE! Report ready: {html_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run()
