"""
summarizer.py
=============
Uses Google Gemini API (FREE tier) to summarize 8-K filings.
Built-in rate limiter — auto-pauses to stay within 15 req/min free tier.

Get free key at: https://aistudio.google.com/app/apikey
Add to .env:     GEMINI_API_KEY=your_key_here
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ── Rate limiter state ─────────────────────────────────────────────────────
# Free tier: 15 requests per minute = 1 request every 4 seconds
_last_call_time  = 0.0
_call_count      = 0
_window_start    = 0.0
DELAY_SECONDS    = 4.0   # min gap between calls
MAX_PER_MINUTE   = 14    # stay just under the 15/min limit


def _rate_limit():
    """Wait if needed to stay within Gemini free tier limits."""
    global _last_call_time, _call_count, _window_start

    now = time.time()

    # Reset window counter every 60 seconds
    if now - _window_start >= 60:
        _window_start = now
        _call_count   = 0

    # If we've hit 14 calls in this window, wait for the window to reset
    if _call_count >= MAX_PER_MINUTE:
        wait = 60 - (now - _window_start) + 1
        if wait > 0:
            print(f"      ⏳ Rate limit window reached — waiting {wait:.0f}s before continuing...")
            time.sleep(wait)
        _window_start = time.time()
        _call_count   = 0

    # Enforce minimum gap between individual calls
    elapsed = time.time() - _last_call_time
    if elapsed < DELAY_SECONDS:
        time.sleep(DELAY_SECONDS - elapsed)

    _last_call_time = time.time()
    _call_count    += 1


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

Summarize this filing using EXACTLY this format:

📌 What happened: [1 sentence — the single most important thing]

📋 Key facts:
• [specific fact with numbers/names from the filing]
• [specific fact with numbers/names from the filing]
• [third fact if relevant]

📊 Stock impact:
| Signal     | BULLISH / BEARISH / NEUTRAL |
| Reason     | [one line why] |
| Short term | [expected price reaction] |
| Watch out  | [key risk or caveat] |

🔑 Keywords detected — Bullish: {bull_kws} | Bearish: {bear_kws}

Be direct. Use specific numbers and names. No filler sentences.

Filing content:
{items_text}"""

    # ── Apply rate limiter before every call ───────────────────────
    _rate_limit()

    try:
        print(f"      🤖 [{ticker}] Calling Gemini...", end=" ", flush=True)

        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": 600,
                    "temperature"    : 0.2,
                }
            },
            timeout=20
        )

        if resp.status_code == 200:
            data    = resp.json()
            summary = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"✅ ({len(summary)} chars)")
            return summary

        elif resp.status_code == 429:
            # Hit rate limit despite our throttle — back off and retry once
            print(f"⚠️  429 rate limit — waiting 30s and retrying...")
            time.sleep(30)
            _rate_limit()
            resp2 = requests.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 600, "temperature": 0.2}
                },
                timeout=20
            )
            if resp2.status_code == 200:
                data    = resp2.json()
                summary = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                print(f"      ✅ [{ticker}] Retry succeeded ({len(summary)} chars)")
                return summary
            else:
                print(f"      ❌ [{ticker}] Retry also failed ({resp2.status_code})")
                return ""

        elif resp.status_code == 403:
            print(f"\n      ❌ [{ticker}] Invalid API key (403). Check GEMINI_API_KEY in .env")
            return ""

        elif resp.status_code == 404:
            print(f"\n      ❌ [{ticker}] Model not found (404). Check GEMINI_URL in summarizer.py")
            return ""

        else:
            print(f"\n      ❌ [{ticker}] Error {resp.status_code}: {resp.text[:120]}")
            return ""

    except requests.exceptions.Timeout:
        print(f"\n      ❌ [{ticker}] Timed out after 20s")
        return ""

    except Exception as e:
        print(f"\n      ❌ [{ticker}] {type(e).__name__}: {e}")
        return ""
