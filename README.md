# SEC 8-K Analyzer

Automatically downloads every 8-K filing published on SEC EDGAR each day,
analyzes them for bullish/bearish signals, summarizes each one using Gemini AI (free),
and opens an interactive HTML report in your browser — all with one command.

---

## What it does

1. Fetches all 8-K (Current Report) filings from SEC EDGAR for today
2. Deduplicates — counts real filings only, not attachments or exhibits
3. Extracts the text of each filing (Items 1.01, 2.02, 5.02, etc.)
4. Scores each filing using 60+ bullish/bearish keywords
5. Summarizes each filing using Gemini AI (free Google account, no credit card)
6. Generates an HTML report with filters, sorting, and inline summaries
7. Also exports a CSV you can open in Excel

---

## Files in this project

| File | What it does |
|---|---|
| `main.py` | Entry point — runs everything in order |
| `fetcher.py` | Downloads 8-K filings from SEC EDGAR |
| `parser.py` | Scores filings with keywords + calls Gemini |
| `summarizer.py` | Calls Gemini API to summarize each filing |
| `reporter.py` | Builds the HTML report and CSV |
| `keywords.py` | All bullish/bearish keywords — edit freely |
| `setup_cron.sh` | Schedules daily run (Mac only) |
| `remove_cron.sh` | Removes the daily schedule (Mac only) |
| `debug.py` | Shows raw EDGAR API response — for troubleshooting |
| `.env` | Your credentials — never share this file |
| `requirements.txt` | Python packages needed |

---

## Setup — Mac

### Step 1 — Check Python is installed
```bash
python3 --version
```
You need Python 3.9 or higher. If not installed, download from https://python.org

---

### Step 2 — Open Terminal
Press `Command + Space` → type `Terminal` → press Enter.

---

### Step 3 — Create your project folder
```bash
cd ~/Documents
mkdir sec-8k-analyzer
cd sec-8k-analyzer
```

---

### Step 4 — Download the project files
Download all files from this repo and place them in `~/Documents/sec-8k-analyzer/`.

---

### Step 5 — Install Python dependencies
```bash
pip3 install requests python-dotenv
```

---

### Step 6 — Create your .env credentials file

**Important:** `.env` starts with a dot — it is a hidden file on Mac.
Do NOT create a file called `env` (without the dot) — that is a different file.

```bash
cd ~/Documents/sec-8k-analyzer
nano .env
```

The `nano` editor opens. Type exactly this (no quotes around the key):
```
GEMINI_API_KEY=paste_your_key_here
```

Save: press `Control + X` → then `Y` → then `Enter`.

Verify it saved correctly:
```bash
cat .env
```
You should see your key printed.

---

### Step 7 — Get your free Gemini API key

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key (starts with `AIza...`)
5. Open your `.env` file and replace `paste_your_key_here` with your actual key:

```bash
nano .env
```

---

### Step 8 — Test it
```bash
cd ~/Documents/sec-8k-analyzer
python3 main.py
```

The browser will open automatically with today's report when done.

---

### Step 9 — Schedule it to run every weekday at 8 AM (optional)
```bash
bash setup_cron.sh
```

To remove the schedule:
```bash
bash remove_cron.sh
```

To check what schedules are active:
```bash
crontab -l
```

---

## Setup — Windows

### Step 1 — Install Python
Download from https://python.org/downloads
During install, check **"Add Python to PATH"** — this is important.

Verify in Command Prompt:
```cmd
python --version
```

---

### Step 2 — Open Command Prompt
Press `Windows + R` → type `cmd` → press Enter.

---

### Step 3 — Create your project folder
```cmd
cd %USERPROFILE%\Documents
mkdir sec-8k-analyzer
cd sec-8k-analyzer
```

---

### Step 4 — Download the project files
Download all files from this repo and place them in
`C:\Users\YourName\Documents\sec-8k-analyzer\`

---

### Step 5 — Install Python dependencies
```cmd
pip install requests python-dotenv
```

---

### Step 6 — Create your .env credentials file

**Important on Windows:** Notepad may save the file as `.env.txt` by default.
Use the method below to avoid that.

Open Command Prompt and run:
```cmd
cd %USERPROFILE%\Documents\sec-8k-analyzer
copy nul .env
notepad .env
```

Notepad opens. Type exactly this (no quotes around the key):
```
GEMINI_API_KEY=paste_your_key_here
```

Save: `Ctrl + S` → close Notepad.

Verify:
```cmd
type .env
```

---

### Step 7 — Get your free Gemini API key

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key (starts with `AIza...`)
5. Open `.env` and replace `paste_your_key_here`:

```cmd
notepad .env
```

---

### Step 8 — Test it
```cmd
cd %USERPROFILE%\Documents\sec-8k-analyzer
python main.py
```

The browser opens automatically with today's report when done.

---

### Step 9 — Schedule daily run on Windows (optional)

Windows uses Task Scheduler instead of cron.

1. Press `Windows + S` → search **Task Scheduler** → open it
2. Click **Create Basic Task** (right side)
3. Name: `SEC 8K Analyzer`
4. Trigger: **Daily** → set time to **8:00 AM** → check **Monday–Friday only**
5. Action: **Start a program**
6. Program: `python`
7. Arguments: `main.py`
8. Start in: `C:\Users\YourName\Documents\sec-8k-analyzer`
9. Click Finish

---

## Run manually anytime

**Mac:**
```bash
cd ~/Documents/sec-8k-analyzer
python3 main.py
```

**Windows:**
```cmd
cd %USERPROFILE%\Documents\sec-8k-analyzer
python main.py
```

---

## How signals are scored

Each filing is scored based on keywords found in the text:

| Score | Signal |
|---|---|
| +15 or more | STRONG BUY |
| +7 to +14 | BUY |
| +2 to +6 | SLIGHTLY BULLISH |
| -1 to +1 | NEUTRAL |
| -2 to -6 | SLIGHTLY BEARISH |
| -7 to -14 | SELL |
| -15 or less | STRONG SELL |

### Bullish keywords (examples)
```
quantum, fault-tolerant, plans to invest, billion investment,
letter of intent, strategic partnership, design win,
record revenue, raised guidance, beat estimates,
fda approval, department of commerce, government contract ...
```

### Bearish keywords (examples)
```
going concern, material weakness, sec investigation,
class action, layoffs, bankruptcy, chapter 11,
secondary offering, ceo resigned, lowered guidance ...
```

To add or change keywords, open `keywords.py` — each keyword has a score.
Higher score = stronger signal. Run `python3 main.py` to apply changes.

---

## Why keyword scoring sometimes misses

Keyword matching only catches phrases we thought of in advance.
For example, IBM's $10B quantum announcement scored NEUTRAL at first because
the exact phrase "plans to invest" wasn't in the list yet.

This is why Gemini summaries are important — Gemini reads the full text and
understands meaning, not just exact words.

---

## Gemini rate limits

The free Gemini tier allows **15 requests per minute**.
The summarizer automatically waits 4 seconds between each call to stay within this limit.

For ~150 filings with text, summarization takes about 10–15 minutes.
If a 429 rate-limit error occurs, the script waits 30 seconds and retries once automatically.

You will see in Terminal:
```
🤖 [IBM]  Calling Gemini... ✅ (412 chars)
🤖 [BBY]  Calling Gemini... ✅ (389 chars)
⏳ Rate limit window reached — waiting 4s...
🤖 [DLTR] Calling Gemini... ✅ (445 chars)
```

---

## HTML report features

- **Search** — filter by ticker or company name
- **Signal filter** — show only Strong Buy, Sell, etc.
- **Item filter** — show only filings with specific items (e.g. 2.02 Earnings, 5.02 CEO change)
- **Score filter** — show only filings with score ≥ a number
- **Text filter** — show only filings where text was successfully fetched
- **Sortable columns** — click any column header to sort, click again to reverse
- **Row numbers** — each row numbered for easy reference
- **Expandable items** — click any item badge (e.g. `7.01 📄`) to read the full item text
- **Gemini summary** — green box showing AI-generated summary with signal, key facts, and stock impact

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: dotenv` | Run `pip3 install python-dotenv` |
| `ModuleNotFoundError: requests` | Run `pip3 install requests` |
| `No filings today` | Market may be closed. Try `days_back=3` in `main.py` |
| Gemini 403 error | Invalid API key — check `.env` has correct key, no quotes |
| Gemini 429 error | Rate limit — script retries automatically. If persistent, wait 1 min |
| Gemini 404 error | Model name changed — update `GEMINI_URL` in `summarizer.py` |
| `.env` not found | Make sure file is named `.env` not `env` or `.env.txt` |
| Zero summaries | Run `cat .env` to confirm key is there and correct |
| Ticker shows N/A | Company has no ticker (private LLC or trust) — normal |
| No text fetched | Filing may use a format the fetcher can't parse — click Index link to read manually |

---

## Want better summaries? (Optional upgrade)

Instead of Gemini, you can run a completely free local AI model on your machine
using **Ollama** — no API key, no rate limits, no internet needed.

**Mac:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```

**Windows:**
Download installer from https://ollama.com/download

Then update `summarizer.py` to call `http://localhost:11434` instead of Gemini.
Ask Claude to help update the summarizer to use Ollama if you want to go this route.

---

## Security notes

- Never share your `.env` file — it contains your API key
- Your filing data is only sent to Gemini if `GEMINI_API_KEY` is set
- The script only reads from SEC EDGAR — it never writes or submits anything
- Cron/Task Scheduler runs the script with your user permissions only

---

## Disclaimer

This tool is for informational purposes only. It is not financial advice.
Keyword scoring and AI summaries can be wrong. Always do your own research
before making any investment decisions.
