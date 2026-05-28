"""
parser.py
=========
Analyzes each 8-K filing text for bullish/bearish keywords.
Returns a scored, sorted results list.
"""

from keywords import BULLISH, BEARISH, ITEM_LABELS


def analyze_filings(filings: list) -> list:
    """
    Score each filing and return sorted results list.
    Most bullish first, most bearish last.
    """
    results = []

    for i, filing in enumerate(filings, 1):
        text_lower = filing.get("text", "").lower()
        if not text_lower:
            continue

        bullish_hits  = {}
        bearish_hits  = {}
        total_score   = 0

        # Check bullish keywords
        for kw, score in BULLISH.items():
            if kw.lower() in text_lower:
                bullish_hits[kw] = score
                total_score += score

        # Check bearish keywords
        for kw, score in BEARISH.items():
            if kw.lower() in text_lower:
                bearish_hits[kw] = score
                total_score += score  # score is already negative

        # Determine signal
        if total_score >= 15:
            signal = "STRONG BUY"
            color  = "#0a7c42"
        elif total_score >= 7:
            signal = "BUY"
            color  = "#1a9e56"
        elif total_score >= 2:
            signal = "SLIGHTLY BULLISH"
            color  = "#7ab648"
        elif total_score <= -15:
            signal = "STRONG SELL"
            color  = "#c0392b"
        elif total_score <= -7:
            signal = "SELL"
            color  = "#e74c3c"
        elif total_score <= -2:
            signal = "SLIGHTLY BEARISH"
            color  = "#e67e22"
        else:
            signal = "NEUTRAL"
            color  = "#7f8c8d"

        # Resolve item labels
        items = filing.get("items", [])
        item_labels = []
        for item in items:
            item_str = str(item)
            label = ITEM_LABELS.get(item_str, f"Item {item_str}")
            item_labels.append(f"{item_str} — {label}")

        results.append({
            "ticker"       : filing.get("ticker", "N/A"),
            "company"      : filing.get("company", "Unknown"),
            "filed_at"     : filing.get("filed_at", ""),
            "signal"       : signal,
            "signal_color" : color,
            "score"        : total_score,
            "bullish_hits" : bullish_hits,
            "bearish_hits" : bearish_hits,
            "items"        : item_labels,
            "filing_url"   : filing.get("filing_url", ""),
            "doc_url"      : filing.get("doc_url", ""),
            "snippet"      : filing.get("text", "")[:400].strip(),
        })

        if i % 20 == 0:
            print(f"   📊 Analyzed {i}/{len(filings)} filings...")

    # Sort: most bullish first
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
