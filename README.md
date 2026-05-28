# 📊 SEC 8-K Analyzer

Downloads ALL new 8-K filings from SEC EDGAR every morning,
analyzes them for bullish/bearish signals, and opens a report
in your browser automatically.

**Output:** Interactive HTML report + CSV file saved in `output/`

---

## What it does

- Downloads every 8-K filing published on SEC EDGAR that day
- Scans each filing for 60+ bullish and bearish keywords
- Scores each filing and assigns a signal: STRONG BUY → STRONG SELL
- Generates an HTML report you can filter, search, and sort
- Also exports a CSV you can open in Excel
- Runs automatically every weekday morning at 8:00 AM

---

## Setup (one time only — takes ~3 minutes)

### Step 1 — Clone the repo
```bash
cd ~/Downloads
git clone https://github.com/YOUR_USERNAME/sec-8k-analyzer.git
cd sec-8k-analyzer
```

### Step 2 — Install Python dependencies
```bash
pip3 install -r requirements.txt
```

### Step 3 — Test it manually
```bash
python3 main.py
```
This will fetch today's filings, analyze them, and open the report in your browser.

### Step 4 — Set up the daily schedule (runs every weekday at 8 AM)
```bash
bash setup_cron.sh
```

That's it! Every weekday morning at 8:00 AM a new report will appear in `output/`.

---

## Run manually anytime
```bash
cd ~/Downloads/sec-8k-analyzer
python3 main.py
```

---

## Output files

All reports are saved in the `output/` folder:

| File | Description |
|---|---|
| `report_YYYY-MM-DD.html` | Interactive report — opens in browser |
| `report_YYYY-MM-DD.csv`  | Spreadsheet — open in Excel / Numbers |
| `cron.log`               | Log of scheduled runs |

---

## How signals are scored

| Score | Signal |
|---|---|
| 15+ | 🟢 STRONG BUY |
| 7–14 | 🟢 BUY |
| 2–6 | 🟡 SLIGHTLY BULLISH |
| -1 to 1 | ⚪ NEUTRAL |
| -2 to -6 | 🟠 SLIGHTLY BEARISH |
| -7 to -14 | 🔴 SELL |
| -15 or less | 🔴 STRONG SELL |

---

## Customize keywords

Open `keywords.py` to add or remove keywords and adjust their scores anytime.

---

## Remove the daily schedule
```bash
bash remove_cron.sh
```

---

## Disclaimer

This tool is for informational purposes only. It is not financial advice.
Always do your own research before making investment decisions.
