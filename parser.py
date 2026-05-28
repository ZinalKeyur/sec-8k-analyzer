"""
parser.py — analyzes + auto-summarizes 8-K filings using Gemini (free)
Rate-limited to stay within Gemini free tier (15 req/min)
"""

from keywords   import BULLISH, BEARISH, ITEM_LABELS
from summarizer import summarize_filing, GEMINI_API_KEY


def analyze_filings(filings):
    results  = []
    total    = len(filings)
    use_ai   = bool(GEMINI_API_KEY)

    if use_ai:
        with_text = sum(1 for f in filings if f.get("text"))
        print(f"   🤖 Gemini will summarize ~{with_text} filings (4s gap between calls)")
        print(f"      Estimated time: ~{with_text * 4 // 60}m {with_text * 4 % 60}s")
    else:
        print(f"   ⚠️  GEMINI_API_KEY not set — keyword scoring only, no summaries")
        print(f"      Add GEMINI_API_KEY to .env for free AI summaries")

    for i, filing in enumerate(filings, 1):
        text_lower = filing.get("text", "").lower()
        item_texts = filing.get("item_texts", {})
        company    = filing.get("company", "Unknown")
        ticker     = filing.get("ticker", "N/A")
        filed_at   = filing.get("filed_at", "")

        # ── Keyword scoring ───────────────────────────────────────
        bullish_hits = {}
        bearish_hits = {}
        total_score  = 0

        for kw, score in BULLISH.items():
            if kw.lower() in text_lower:
                bullish_hits[kw] = score
                total_score += score

        for kw, score in BEARISH.items():
            if kw.lower() in text_lower:
                bearish_hits[kw] = score
                total_score += score

        # ── Signal ────────────────────────────────────────────────
        if total_score >= 15:
            signal, color = "STRONG BUY",       "#0a7c42"
        elif total_score >= 7:
            signal, color = "BUY",              "#1a9e56"
        elif total_score >= 2:
            signal, color = "SLIGHTLY BULLISH", "#7ab648"
        elif total_score <= -15:
            signal, color = "STRONG SELL",      "#c0392b"
        elif total_score <= -7:
            signal, color = "SELL",             "#e74c3c"
        elif total_score <= -2:
            signal, color = "SLIGHTLY BEARISH", "#e67e22"
        else:
            signal, color = "NEUTRAL",          "#7f8c8d"

        # ── Item summaries ────────────────────────────────────────
        item_summaries = {}
        for item_num in filing.get("items", []):
            item_str  = str(item_num)
            label     = ITEM_LABELS.get(item_str, f"Item {item_str}")
            item_text = item_texts.get(item_str, "")
            item_summaries[item_str] = {
                "label": label,
                "text" : item_text,
            }

        # ── Gemini summary ─────────────────────────────────────────
        ai_summary = ""
        if use_ai and filing.get("text") and item_summaries:
            ai_summary = summarize_filing(
                company, ticker, filed_at,
                item_summaries, bullish_hits, bearish_hits
            )

        results.append({
            "ticker"        : ticker,
            "company"       : company,
            "filed_at"      : filed_at,
            "location"      : filing.get("location", ""),
            "signal"        : signal,
            "signal_color"  : color,
            "score"         : total_score,
            "bullish_hits"  : bullish_hits,
            "bearish_hits"  : bearish_hits,
            "item_summaries": item_summaries,
            "ai_summary"    : ai_summary,
            "filing_url"    : filing.get("filing_url", ""),
            "doc_url"       : filing.get("doc_url", ""),
            "has_text"      : bool(filing.get("text", "")),
        })

        if i % 25 == 0:
            print(f"   📊 Processed {i}/{total} filings...")

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
