"""
SEC 8-K Analyzer
=================
Downloads all new 8-K filings from SEC EDGAR every morning,
analyzes them for bullish/bearish signals,
auto-summarizes using Gemini (free), and opens an HTML report.

Run manually:  python3 main.py
Scheduled:     bash setup_cron.sh
"""

import os
from datetime import date
from fetcher   import fetch_todays_8k_filings
from parser    import analyze_filings
from reporter  import generate_html, generate_csv

OUTPUT_DIR = "output"

def run():
    today = date.today().strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"  SEC 8-K ANALYZER — {today}")
    print(f"{'='*60}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── STEP 1: FETCH ──────────────────────────────────────────────
    print("\n[STEP 1] Fetching today's 8-K filings from SEC EDGAR...")
    filings = fetch_todays_8k_filings()
    print(f"   ✅ Found {len(filings)} unique 8-K filings")

    if not filings:
        print("   ℹ️  No filings today (market may be closed). Exiting.")
        return

    # How many have text
    with_text = sum(1 for f in filings if f.get("text"))
    print(f"   📄 Filings with text fetched: {with_text}/{len(filings)}")
    print(f"   ⚠️  Filings without text: {len(filings)-with_text}/{len(filings)} (will show in report but no summary)")

    # ── STEP 2: ANALYZE + SUMMARIZE ────────────────────────────────
    print("\n[STEP 2] Analyzing filings + generating Gemini summaries...")
    results = analyze_filings(filings)

    with_summary = sum(1 for r in results if r.get("ai_summary"))
    print(f"   ✅ Analyzed: {len(results)} filings")
    print(f"   ✨ Summaries generated: {with_summary}/{len(results)}")
    if with_summary == 0:
        print("   ⚠️  Zero summaries — filings may have no text extracted")
    elif with_summary < with_text:
        print(f"   ⚠️  Some summaries missing — those filings had no extractable text")

    # ── STEP 3: HTML REPORT ────────────────────────────────────────
    html_path = os.path.join(OUTPUT_DIR, f"report_{today}.html")
    print(f"\n[STEP 3] Generating HTML report → {html_path}")
    generate_html(results, html_path, today)
    print(f"   ✅ HTML saved")

    # ── STEP 4: CSV ────────────────────────────────────────────────
    csv_path = os.path.join(OUTPUT_DIR, f"report_{today}.csv")
    print(f"\n[STEP 4] Generating CSV → {csv_path}")
    generate_csv(results, csv_path)
    print(f"   ✅ CSV saved")

    # ── STEP 5: OPEN ───────────────────────────────────────────────
    print(f"\n[STEP 5] Opening report in browser...")
    os.system(f"open {html_path}")

    print(f"\n{'='*60}")
    print(f"  DONE!")
    print(f"  Filings analyzed : {len(results)}")
    print(f"  With summaries   : {with_summary}")
    print(f"  Report           : {html_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run()
