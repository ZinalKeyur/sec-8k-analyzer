"""
reporter.py — generates HTML report and CSV
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
                "items"           : " | ".join(
                    f"{k} — {v['label']}" for k, v in r["item_summaries"].items()
                ),
                "filing_url"      : r["filing_url"],
                "doc_url"         : r["doc_url"],
            })


def generate_html(results, path, today):
    strong_buy  = sum(1 for r in results if r["signal"] == "STRONG BUY")
    buy         = sum(1 for r in results if r["signal"] == "BUY")
    sl_bull     = sum(1 for r in results if r["signal"] == "SLIGHTLY BULLISH")
    neutral     = sum(1 for r in results if r["signal"] == "NEUTRAL")
    sl_bear     = sum(1 for r in results if r["signal"] == "SLIGHTLY BEARISH")
    sell        = sum(1 for r in results if r["signal"] in ("SELL","STRONG SELL"))
    no_text     = sum(1 for r in results if not r["has_text"])

    rows_html = ""
    for idx, r in enumerate(results):
        # Keyword badges
        bull_badges = "".join(
            f'<span class="badge bull">{kw} +{s}</span>'
            for kw, s in r["bullish_hits"].items()
        )
        bear_badges = "".join(
            f'<span class="badge bear">{kw} {s}</span>'
            for kw, s in r["bearish_hits"].items()
        )

        # Item pills + expandable text
        items_html = ""
        detail_html = ""
        for item_num, info in r["item_summaries"].items():
            label     = info["label"]
            item_text = info["text"]
            detail_id = f"detail_{idx}_{item_num.replace('.','_')}"

            if item_text:
                items_html += (
                    f'<span class="badge item clickable" '
                    f'onclick="toggleDetail(\'{detail_id}\')">'
                    f'{item_num} — {label} 📄</span> '
                )
                # Escape for HTML
                safe_text = (item_text
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;"))
                detail_html += (
                    f'<div class="item-detail" id="{detail_id}">'
                    f'<strong>Item {item_num} — {label}</strong><br>'
                    f'<p>{safe_text}</p>'
                    f'</div>'
                )
            else:
                items_html += f'<span class="badge item">{item_num} — {label}</span> '

        # No text warning
        text_status = (
            '<span class="no-text">⚠️ text not fetched</span>'
            if not r["has_text"] else ""
        )

        # Links
        links = ""
        if r["doc_url"]:
            links += f'<a href="{r["doc_url"]}" target="_blank">📄 Filing</a> '
        if r["filing_url"]:
            links += f'<a href="{r["filing_url"]}" target="_blank">🗂 Index</a>'

        score_sign = f'+{r["score"]}' if r["score"] > 0 else str(r["score"])

        rows_html += f"""
        <tr>
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
* {{ box-sizing:border-box; margin:0; padding:0 }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        background:#f5f6fa; color:#2c3e50; font-size:13px }}

header {{ background:#1a1a2e; color:white; padding:18px 28px }}
header h1 {{ font-size:19px; font-weight:500; margin-bottom:3px }}
header p  {{ font-size:11px; opacity:.7 }}

.summary {{ display:flex; gap:10px; padding:14px 28px; flex-wrap:wrap }}
.stat {{ background:white; border-radius:8px; padding:10px 18px;
         border:1px solid #e0e0e0; text-align:center; min-width:90px }}
.stat .num {{ font-size:22px; font-weight:600 }}
.stat .lbl {{ font-size:11px; color:#888; margin-top:2px }}
.s-green {{ color:#0a7c42 }} .s-red {{ color:#c0392b }}
.s-orange {{ color:#e67e22 }} .s-gray {{ color:#7f8c8d }}
.s-warn  {{ color:#e67e22 }}

.controls {{ padding:0 28px 10px; display:flex; gap:8px; flex-wrap:wrap }}
.controls input  {{ padding:6px 11px; border:1px solid #ddd; border-radius:6px; font-size:12px; width:220px }}
.controls select {{ padding:6px 11px; border:1px solid #ddd; border-radius:6px; font-size:12px }}

.table-wrap {{ padding:0 28px 28px; overflow-x:auto }}
table {{ width:100%; border-collapse:collapse; background:white;
         border-radius:10px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08) }}
thead th {{ background:#1a1a2e; color:white; padding:9px 11px;
            text-align:left; font-weight:500; font-size:12px;
            white-space:nowrap; cursor:pointer }}
thead th:hover {{ background:#2d2d4e }}
tbody tr {{ border-bottom:1px solid #f0f0f0 }}
tbody tr:hover {{ background:#fafbff }}
tbody td {{ padding:8px 11px; vertical-align:top }}

.signal {{ display:inline-block; color:white; padding:3px 8px;
           border-radius:20px; font-size:11px; font-weight:500; white-space:nowrap }}
.score  {{ font-weight:600; font-size:14px; text-align:center }}

.badge {{ display:inline-block; font-size:10px; padding:2px 6px;
          border-radius:4px; margin:2px 2px 2px 0; white-space:nowrap }}
.bull {{ background:#e8f5e9; color:#1b5e20; border:1px solid #a5d6a7 }}
.bear {{ background:#fce4ec; color:#880e4f; border:1px solid #f48fb1 }}
.item {{ background:#e3f2fd; color:#0d47a1; border:1px solid #90caf9 }}
.clickable {{ cursor:pointer }}
.clickable:hover {{ background:#bbdefb }}

.item-detail {{
  display:none;
  margin-top:8px;
  padding:10px 12px;
  background:#f8fbff;
  border-left:3px solid #2196f3;
  border-radius:0 6px 6px 0;
  font-size:11px;
  line-height:1.6;
  max-width:600px;
  white-space:pre-wrap;
  word-break:break-word;
}}
.item-detail strong {{ font-size:12px; display:block; margin-bottom:6px; color:#0d47a1 }}
.item-detail p {{ color:#333 }}

.no-text {{ font-size:10px; color:#e67e22 }}

.links a {{ color:#3498db; text-decoration:none; margin-right:6px; font-size:11px }}
.links a:hover {{ text-decoration:underline }}
.hidden {{ display:none }}

footer {{ text-align:center; padding:18px; font-size:11px; color:#aaa }}
</style>
</head>
<body>

<header>
  <h1>📊 SEC 8-K Filing Analyzer</h1>
  <p>Report date: {today} &nbsp;·&nbsp; Generated: {datetime.now().strftime('%H:%M:%S')}
     &nbsp;·&nbsp; Total: {len(results)} filings analyzed</p>
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

<div class="controls">
  <input type="text" id="search" placeholder="🔍 Search ticker or company..." oninput="filterTable()">
  <select id="signal-filter" onchange="filterTable()">
    <option value="">All signals</option>
    <option value="STRONG BUY">Strong Buy</option>
    <option value="BUY">Buy</option>
    <option value="SLIGHTLY BULLISH">Slightly Bullish</option>
    <option value="NEUTRAL">Neutral</option>
    <option value="SLIGHTLY BEARISH">Slightly Bearish</option>
    <option value="SELL">Sell</option>
    <option value="STRONG SELL">Strong Sell</option>
  </select>
  <select id="text-filter" onchange="filterTable()">
    <option value="">All filings</option>
    <option value="has-text">Has text ✅</option>
    <option value="no-text">No text ⚠️</option>
  </select>
</div>

<div class="table-wrap">
<table id="main-table">
  <thead>
    <tr>
      <th onclick="sortTable(0)">Ticker ↕</th>
      <th onclick="sortTable(1)">Company ↕</th>
      <th onclick="sortTable(2)">Filed ↕</th>
      <th onclick="sortTable(3)">Signal ↕</th>
      <th onclick="sortTable(4)">Score ↕</th>
      <th>Bullish Keywords</th>
      <th>Bearish Keywords</th>
      <th>Items (click 📄 to read)</th>
      <th>Links</th>
    </tr>
  </thead>
  <tbody id="table-body">
    {rows_html}
  </tbody>
</table>
</div>

<footer>
  Data source: SEC EDGAR &nbsp;·&nbsp; Not financial advice &nbsp;·&nbsp;
  Always do your own research before making investment decisions.
</footer>

<script>
function toggleDetail(id) {{
  const el = document.getElementById(id);
  if (el) el.style.display = el.style.display === 'block' ? 'none' : 'block';
}}

function filterTable() {{
  const search     = document.getElementById('search').value.toLowerCase();
  const signal     = document.getElementById('signal-filter').value;
  const textFilter = document.getElementById('text-filter').value;
  document.querySelectorAll('#table-body tr').forEach(row => {{
    const text      = row.textContent.toLowerCase();
    const sigTd     = row.cells[3].textContent.trim();
    const hasNoText = row.cells[7].textContent.includes('text not fetched');
    const matchS    = !search || text.includes(search);
    const matchF    = !signal || sigTd === signal;
    const matchT    = !textFilter
      || (textFilter === 'has-text' && !hasNoText)
      || (textFilter === 'no-text'  &&  hasNoText);
    row.classList.toggle('hidden', !(matchS && matchF && matchT));
  }});
}}

function sortTable(col) {{
  const tbody = document.getElementById('table-body');
  const rows  = Array.from(tbody.querySelectorAll('tr'));
  const dir   = tbody.dataset.sortDir === 'asc' ? 'desc' : 'asc';
  tbody.dataset.sortDir = dir;
  rows.sort((a, b) => {{
    const av = a.cells[col].textContent.trim();
    const bv = b.cells[col].textContent.trim();
    const an = parseFloat(av), bn = parseFloat(bv);
    if (!isNaN(an) && !isNaN(bn)) return dir === 'asc' ? an-bn : bn-an;
    return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
