"""
summarizer.py
=============
Uses Google Gemini API (FREE tier) to summarize 8-K filings.
Model: gemini-1.5-flash (fast, free, great quality)

Get your FREE API key (no credit card):
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Add to .env as: GEMINI_API_KEY=your_key_here

Free tier limits: 15 requests/min, 1500 requests/day — more than enough!
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def summarize_filing(company, ticker, filed_at, item_summaries, bullish_hits, bearish_hits):
    """
    Summarize a filing using Gemini (free).
    Returns formatted summary string, or "" if key not set / call fails.
    """
    if not GEMINI_API_KEY:
        return ""

    # Build item text
    items_text = ""
    for item_num, info in item_summaries.items():
        text = info.get("text", "")
        if text:
            items_text += f"\nItem {item_num} ({info['label']}):\n{text[:1200]}\n"

    if not items_text.strip():
        return ""

    bull_kws = ", ".join(bullish_hits.keys()) if bullish_hits else "none"
    bear_kws = ", ".join(bearish_hits.keys()) if bearish_hits else "none"

    prompt = f"""You are analyzing an SEC 8-K filing for {company} (ticker: {ticker}, filed: {filed_at}).

Summarize this filing using EXACTLY this format — no deviations:

📌 What happened: [1 sentence — the single most important thing]

📋 Key facts:
• [fact 1 with specifics — numbers, dates, names]
• [fact 2 with specifics]
• [fact 3 if relevant]

📊 Stock impact:
| Signal     | BULLISH / BEARISH / NEUTRAL |
| Reason     | [one line why] |
| Short term | [expected price reaction] |
| Watch out  | [key risk or caveat] |

🔑 Keywords: Bullish: {bull_kws} | Bearish: {bear_kws}

Be direct. Use specific numbers and names from the filing. No filler.

Filing:
{items_text}"""

    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={{
                "contents": [{{"parts": [{{"text": prompt}}]}}],
                "generationConfig": {{
                    "maxOutputTokens": 600,
                    "temperature"    : 0.2,
                }}
            }},
            timeout=20
        )
        resp.raise_for_status()
        data    = resp.json()
        summary = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return summary

    except Exception as e:
        print(f"   ⚠️  Gemini error for {ticker}: {e}")
        return ""
