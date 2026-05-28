"""
reporter.py — HTML report and CSV generator
"""

import csv
from datetime import datetime


def generate_csv(results, path):
    if not results:
        return
    fields = ["ticker","company","filed_at","location","signal","score",
              "bullish_keywords","bearish_keywords","items","filing_url","doc_url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "ticker"          : r["ticker"],
                "company"         : r["company"],
                "filed_at"        : r["filed_at"],
                "location"        : r["location"],
                "signal"          : r["signal"],
                "score"           : r["score"],
                "bullish_keywords": " | ".join(r["bullish_hits"].keys()),
                "bearish_keywords": " | ".join(r["bearish_hits"].keys()),
                "items"           : " | ".join(f"{k} — {v['label']}" for k,v in r["item_summaries"].items()),
                "filing_url"      : r["filing_url"],
                "doc_url"         : r["doc_url"],
            })


def generate_html(results, path, today):
    strong_buy = sum(1 for r in results if r["signal"] == "STRONG BUY")
    buy        = sum(1 for r in results if r["signal"] == "BUY")
    sl_bull    = sum(1 for r in results if r["signal"] == "SLIGHTLY BULLISH")
    neutral    = sum(1 for r in results if r["signal"] == "NEUTRAL")
    sl_bear    = sum(1 for r in results if r["signal"] == "SLIGHTLY BEARISH")
    sell       = sum(1 for r in results if r["signal"] in ("SELL","STRONG SELL"))
    no_text    = sum(1 for r in results if not r["has_text"])

    rows_html = ""
    for idx, r in enumerate(results):

        # ── Keyword badges ─────────────────────────────────────────
        bull_badges = "".join(
            f'<span class="badge bull">{kw} +{s}</span>'
            for kw, s in r["bullish_hits"].items()
        )
        bear_badges = "".join(
            f'<span class="badge bear">{kw} {s}</span>'
            for kw, s in r["bearish_hits"].items()
        )

        # ── Item pills + expandable text ──────────────────────────
        items_html  = ""
        detail_html = ""
        for item_num, info in r["item_summaries"].items():
            label     = info["label"]
            item_text = info.get("text","")
            detail_id = f"detail_{idx}_{item_num.replace('.','_')}"
            if item_text:
                items_html += (
                    f'<span class="badge item clickable" '
                    f'onclick="toggleDetail(\'{detail_id}\')">'
                    f'{item_num} — {label} 📄</span> '
                )
                safe = (item_text.replace("&","&amp;").replace("<","&lt;")
                        .replace(">","&gt;").replace('"',"&quot;"))
                detail_html += (
                    f'<div class="item-detail" id="{detail_id}">'
                    f'<strong>Item {item_num} — {label}</strong>'
                    f'<div class="raw-text"><p>{safe}</p></div>'
                    f'</div>'
                )
            else:
                items_html += f'<span class="badge item">{item_num} — {label}</span> '

        text_status = '<span class="no-text">⚠️ text not fetched</span>' if not r["has_text"] else ""

        idx_plus_1 = idx + 1

        # AI summary block (shown directly in table if Gemini key is set)
        raw_ai = r.get("ai_summary", "")
        if raw_ai:
            safe_ai = (raw_ai
                .replace("&","&amp;").replace("<","&lt;")
                .replace(">","&gt;").replace('"',"&quot;"))
            ai_summary_html = (
                f'<div class="gemini-summary">'
                f'<span class="gemini-label">✨ Gemini Summary</span>'
                f'<pre>{safe_ai}</pre>'
                f'</div>'
            )
        else:
            ai_summary_html = ""
        score_sign = f'+{r["score"]}' if r["score"] > 0 else str(r["score"])

        # ── Links ──────────────────────────────────────────────────
        links = ""
        if r["doc_url"]:
            links += f'<a href="{r["doc_url"]}" target="_blank">📄 Filing</a> '
        if r["filing_url"]:
            links += f'<a href="{r["filing_url"]}" target="_blank">🗂 Index</a>'

        # ── Summary paste area ─────────────────────────────────────
        rows_html += f"""
        <tr data-signal="{r['signal']}" data-score="{r['score']}"
            data-filed="{r['filed_at']}" data-has-text="{'1' if r['has_text'] else '0'}"
            data-items="{','.join(r['item_summaries'].keys())}">
          <td style="text-align:center;color:#aaa;font-size:11px;font-weight:500">{idx_plus_1}</td>
          <td><strong>{r['ticker']}</strong></td>
          <td>{r['company']}<br><small style="color:#999">{r['location']}</small></td>
          <td>{r['filed_at']}</td>
          <td><span class="signal" style="background:{r['signal_color']}">{r['signal']}</span></td>
          <td class="score" style="color:{r['signal_color']}">{score_sign}</td>
          <td>{bull_badges}</td>
          <td>{bear_badges}</td>
          <td>
            {items_html}
            {text_status}
            {detail_html}
            {ai_summary_html}
          </td>
          <td>{links}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SEC 8-K Analysis — {today}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
      background:#f5f6fa;color:#2c3e50;font-size:13px}}

header{{background:#1a1a2e;color:white;padding:18px 28px}}
header h1{{font-size:19px;font-weight:500;margin-bottom:3px}}
header p{{font-size:11px;opacity:.7}}

.summary{{display:flex;gap:10px;padding:14px 28px;flex-wrap:wrap}}
.stat{{background:white;border-radius:8px;padding:10px 18px;
       border:1px solid #e0e0e0;text-align:center;min-width:85px}}
.stat .num{{font-size:22px;font-weight:600}}
.stat .lbl{{font-size:11px;color:#888;margin-top:2px}}
.s-green{{color:#0a7c42}} .s-red{{color:#c0392b}}
.s-orange{{color:#e67e22}} .s-gray{{color:#7f8c8d}} .s-warn{{color:#e67e22}}

.filters{{padding:10px 28px 12px;background:white;border-bottom:1px solid #eee;
           display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.filters label{{font-size:11px;color:#666;margin-right:2px}}
.filters input,.filters select{{
  padding:5px 10px;border:1px solid #ddd;border-radius:6px;font-size:12px}}
.filters input{{width:200px}}
.filter-group{{display:flex;align-items:center;gap:4px}}

.table-wrap{{padding:0 28px 28px;overflow-x:auto;margin-top:12px}}
table{{width:100%;border-collapse:collapse;background:white;
       border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
thead th{{background:#1a1a2e;color:white;padding:9px 11px;
          text-align:left;font-weight:500;font-size:12px;
          white-space:nowrap;cursor:pointer;user-select:none}}
thead th:hover{{background:#2d2d4e}}
thead th.sorted-asc::after{{content:" ↑"}}
thead th.sorted-desc::after{{content:" ↓"}}
tbody tr{{border-bottom:1px solid #f0f0f0}}
tbody tr:hover{{background:#fafbff}}
tbody td{{padding:8px 11px;vertical-align:top}}

.signal{{display:inline-block;color:white;padding:3px 8px;
         border-radius:20px;font-size:11px;font-weight:500;white-space:nowrap}}
.score{{font-weight:600;font-size:14px;text-align:center}}

.badge{{display:inline-block;font-size:10px;padding:2px 6px;
        border-radius:4px;margin:2px 2px 2px 0;white-space:nowrap}}
.bull{{background:#e8f5e9;color:#1b5e20;border:1px solid #a5d6a7}}
.bear{{background:#fce4ec;color:#880e4f;border:1px solid #f48fb1}}
.item{{background:#e3f2fd;color:#0d47a1;border:1px solid #90caf9}}
.clickable{{cursor:pointer}} .clickable:hover{{background:#bbdefb}}

.item-detail{{display:none;margin-top:8px;padding:8px 10px;
              background:#f8fbff;border-left:3px solid #2196f3;
              border-radius:0 6px 6px 0;font-size:11px;max-width:560px}}
.item-detail strong{{font-size:12px;display:block;margin-bottom:5px;color:#0d47a1}}
.raw-text p{{color:#333;font-size:11px;line-height:1.5;white-space:pre-wrap;word-break:break-word}}
.gemini-summary{{margin-top:8px;padding:10px 12px;background:#f0fdf4;
  border-left:3px solid #10b981;border-radius:0 6px 6px 0;max-width:580px}}
.gemini-label{{font-size:10px;font-weight:600;color:#059669;display:block;margin-bottom:6px}}
.gemini-summary pre{{font-family:inherit;font-size:11px;color:#1f2937;
  line-height:1.6;white-space:pre-wrap;word-break:break-word}}

.no-text{{font-size:10px;color:#e67e22}}


.links a{{color:#3498db;text-decoration:none;margin-right:6px;font-size:11px}}
.links a:hover{{text-decoration:underline}}
.hidden{{display:none !important}}

footer{{text-align:center;padding:18px;font-size:11px;color:#aaa}}
</style>
</head>
<body>

<header>
  <h1>📊 SEC 8-K Filing Analyzer</h1>
  <p>Report date: {today} &nbsp;·&nbsp; Generated: {datetime.now().strftime('%H:%M:%S')}
     &nbsp;·&nbsp; {len(results)} unique 8-K filings</p>
</header>

<div class="summary">
  <div class="stat"><div class="num s-green">{strong_buy}</div><div class="lbl">Strong Buy</div></div>
  <div class="stat"><div class="num s-green">{buy}</div><div class="lbl">Buy</div></div>
  <div class="stat"><div class="num s-green">{sl_bull}</div><div class="lbl">Sl. Bullish</div></div>
  <div class="stat"><div class="num s-gray">{neutral}</div><div class="lbl">Neutral</div></div>
  <div class="stat"><div class="num s-orange">{sl_bear}</div><div class="lbl">Sl. Bearish</div></div>
  <div class="stat"><div class="num s-red">{sell}</div><div class="lbl">Sell</div></div>
  <div class="stat"><div class="num s-gray">{len(results)}</div><div class="lbl">Total</div></div>
  <div class="stat"><div class="num s-warn">{no_text}</div><div class="lbl">⚠️ No Text</div></div>
</div>

<div class="filters">
  <div class="filter-group">
    <label>🔍</label>
    <input type="text" id="f-search" placeholder="Ticker or company..." oninput="applyFilters()">
  </div>
  <div class="filter-group">
    <label>Signal</label>
    <select id="f-signal" onchange="applyFilters()">
      <option value="">All signals</option>
      <option value="STRONG BUY">🟢 Strong Buy</option>
      <option value="BUY">🟢 Buy</option>
      <option value="SLIGHTLY BULLISH">🟡 Slightly Bullish</option>
      <option value="NEUTRAL">⚪ Neutral</option>
      <option value="SLIGHTLY BEARISH">🟠 Slightly Bearish</option>
      <option value="SELL">🔴 Sell</option>
      <option value="STRONG SELL">🔴 Strong Sell</option>
    </select>
  </div>
  <div class="filter-group">
    <label>8-K Item</label>
    <select id="f-item" onchange="applyFilters()">
      <option value="">All items</option>
      <option value="1.01">1.01 — Major agreement</option>
      <option value="2.01">2.01 — Acquisition</option>
      <option value="2.02">2.02 — Earnings</option>
      <option value="2.04">2.04 — Debt default</option>
      <option value="3.01">3.01 — Delisting</option>
      <option value="4.02">4.02 — Restatement</option>
      <option value="5.02">5.02 — CEO/CFO change</option>
      <option value="7.01">7.01 — Press release</option>
      <option value="8.01">8.01 — Other events</option>
    </select>
  </div>
  <div class="filter-group">
    <label>Text</label>
    <select id="f-text" onchange="applyFilters()">
      <option value="">All</option>
      <option value="1">Has text ✅</option>
      <option value="0">No text ⚠️</option>
    </select>
  </div>
  <div class="filter-group">
    <label>Score ≥</label>
    <input type="number" id="f-score" placeholder="e.g. 5"
      style="width:70px" oninput="applyFilters()">
  </div>
  <button onclick="clearFilters()"
    style="padding:5px 12px;font-size:11px;border:1px solid #ddd;
    border-radius:6px;background:white;cursor:pointer">✖ Clear</button>
  <span id="f-count" style="font-size:11px;color:#888;margin-left:4px"></span>
</div>

<div class="table-wrap">
<table id="main-table">
  <thead>
    <tr>
      <th style="width:36px;text-align:center">#</th>
      <th onclick="sortTable(1,'text')">Ticker</th>
      <th onclick="sortTable(2,'text')">Company</th>
      <th onclick="sortTable(3,'date')" id="th-filed">Filed</th>
      <th onclick="sortTable(4,'text')">Signal</th>
      <th onclick="sortTable(5,'num')" id="th-score">Score</th>
      <th>Bullish Keywords</th>
      <th>Bearish Keywords</th>
      <th>Items (click 📄 to expand)</th>
      <th>Links</th>
    </tr>
  </thead>
  <tbody id="table-body">
    {rows_html}
  </tbody>
</table>
</div>

<footer>
  Data: SEC EDGAR &nbsp;·&nbsp; Not financial advice &nbsp;·&nbsp; Do your own research
</footer>

<script>
// ── Sort ──────────────────────────────────────────────────────────────────
let sortCol = 5, sortDir = 'desc', sortType = 'num';

function sortTable(col, type) {{
  if (sortCol === col) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
  else {{ sortCol = col; sortDir = 'desc'; sortType = type; }}

  // Update header indicators
  document.querySelectorAll('thead th').forEach(th => {{
    th.classList.remove('sorted-asc','sorted-desc');
  }});
  const ths = document.querySelectorAll('thead th');
  ths[col].classList.add(sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');

  const tbody = document.getElementById('table-body');
  const rows  = Array.from(tbody.querySelectorAll('tr'));
  rows.sort((a, b) => {{
    let av = a.cells[col].textContent.trim();
    let bv = b.cells[col].textContent.trim();
    let result;
    if (type === 'num') {{
      result = (parseFloat(av)||0) - (parseFloat(bv)||0);
    }} else if (type === 'date') {{
      result = new Date(av) - new Date(bv);
    }} else {{
      result = av.localeCompare(bv);
    }}
    return sortDir === 'asc' ? result : -result;
  }});
  rows.forEach(r => tbody.appendChild(r));
  updateCount();
}}

// ── Filter ────────────────────────────────────────────────────────────────
function applyFilters() {{
  const search  = document.getElementById('f-search').value.toLowerCase();
  const signal  = document.getElementById('f-signal').value;
  const item    = document.getElementById('f-item').value;
  const hasText = document.getElementById('f-text').value;
  const minScore= parseFloat(document.getElementById('f-score').value) || null;

  document.querySelectorAll('#table-body tr').forEach(row => {{
    const text      = row.textContent.toLowerCase();
    const rowSignal = row.dataset.signal || '';
    const rowScore  = parseFloat(row.dataset.score) || 0;
    const rowText   = row.dataset.hasText || '0';
    const rowItems  = row.dataset.items   || '';

    const ok = (
      (!search   || text.includes(search)) &&
      (!signal   || rowSignal === signal) &&
      (!item     || rowItems.includes(item)) &&
      (!hasText  || rowText === hasText) &&
      (minScore === null || rowScore >= minScore)
    );
    row.classList.toggle('hidden', !ok);
  }});
  updateCount();
}}

function clearFilters() {{
  ['f-search','f-score'].forEach(id => document.getElementById(id).value = '');
  ['f-signal','f-item','f-text'].forEach(id => document.getElementById(id).value = '');
  applyFilters();
}}

function updateCount() {{
  const total   = document.querySelectorAll('#table-body tr').length;
  const visible = document.querySelectorAll('#table-body tr:not(.hidden)').length;
  document.getElementById('f-count').textContent =
    visible < total ? `Showing ${{visible}} of ${{total}}` : `${{total}} filings`;
}}

// ── Toggle item detail ────────────────────────────────────────────────────
function toggleDetail(id) {{
  const el = document.getElementById(id);
  if (el) el.style.display = el.style.display === 'block' ? 'none' : 'block';
}}

// ── Init ──────────────────────────────────────────────────────────────────
updateCount();
// Default sort by score descending
document.querySelectorAll('thead th')[5].classList.add('sorted-desc');
</script>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
