"""
parser.py — analyzes 8-K filings for bullish/bearish signals + item summaries
"""

from keywords import BULLISH, BEARISH, ITEM_LABELS


def analyze_filings(filings):
    results = []

    for i, filing in enumerate(filings, 1):
        text_lower = filing.get("text", "").lower()
        item_texts = filing.get("item_texts", {})

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

        # Signal
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

        # Build item summaries with labels
        item_summaries = {}
        for item_num in filing.get("items", []):
            item_str   = str(item_num)
            label      = ITEM_LABELS.get(item_str, f"Item {item_str}")
            item_text  = item_texts.get(item_str, "")
            item_summaries[item_str] = {
                "label": label,
                "text" : item_text,
            }

        results.append({
            "ticker"        : filing.get("ticker", "N/A"),
            "company"       : filing.get("company", "Unknown"),
            "filed_at"      : filing.get("filed_at", ""),
            "location"      : filing.get("location", ""),
            "signal"        : signal,
            "signal_color"  : color,
            "score"         : total_score,
            "bullish_hits"  : bullish_hits,
            "bearish_hits"  : bearish_hits,
            "item_summaries": item_summaries,
            "filing_url"    : filing.get("filing_url", ""),
            "doc_url"       : filing.get("doc_url", ""),
            "has_text"      : bool(filing.get("text", "")),
        })

        if i % 25 == 0:
            print(f"   📊 Analyzed {i}/{len(filings)} filings...")

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
