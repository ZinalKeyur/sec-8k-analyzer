"""
reporter.py
===========
Generates HTML report and CSV from analyzed results.
"""

import csv
from datetime import datetime


def generate_csv(results: list, path: str):
    """Write results to a CSV file."""
    if not results:
        return

    fields = ["ticker", "company", "filed_at", "signal", "score",
              "bullish_keywords", "bearish_keywords", "items", "filing_url"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "ticker"          : r["ticker"],
                "company"         : r["company"],
                "filed_at"        : r["filed_at"],
                "signal"          : r["signal"],
                "score"           : r["score"],
                "bullish_keywords": " | ".join(r["bullish_hits"].keys()),
                "bearish_keywords": " | ".join(r["bearish_hits"].keys()),
                "items"           : " | ".join(r["items"]),
                "filing_url"      : r["filing_url"],
            })


def generate_html(results: list, path: str, today: str):
    """Generate a clean HTML report."""

    # Summary counts
    strong_buy   = sum(1 for r in results if r["signal"] == "STRONG BUY")
    buy          = sum(1 for r in results if r["signal"] == "BUY")
    neutral      = sum(1 for r in results if r["signal"] == "NEUTRAL")
    sell         = sum(1 for r in results if r["signal"] in ("SELL", "STRONG SELL"))
    bearish      = sum(1 for r in results if r["signal"] == "SLIGHTLY BEARISH")
    bullish      = sum(1 for r in results if r["signal"] == "SLIGHTLY BULLISH")

    # Build rows
    rows_html = ""
    for r in results:
        bullish_badges = "".join(
            f'<span class="badge bull">{kw} (+{score})</span>'
            for kw, score in r["bullish_hits"].items()
        )
        bearish_badges = "".join(
            f'<span class="badge bear">{kw} ({score})</span>'
            for kw, score in r["bearish_hits"].items()
        )
        item_badges = "".join(
            f'<span class="badge item">{item}</span>'
            for item in r["items"]
        )
        links = ""
        if r["filing_url"]:
            links += f'<a href="{r["filing_url"]}" target="_blank">Index</a> '
        if r["doc_url"]:
            links += f'<a href="{r["doc_url"]}" target="_blank">Filing</a>'

        score_sign = f'+{r["score"]}' if r["score"] > 0 else str(r["score"])

        rows_html += f"""
        <tr>
          <td><strong>{r['ticker']}</strong></td>
          <td>{r['company']}</td>
          <td>{r['filed_at']}</td>
          <td><span class="signal" style="background:{r['signal_color']}">{r['signal']}</span></td>
          <td class="score" style="color:{r['signal_color']}">{score_sign}</td>
          <td>{bullish_badges}</td>
          <td>{bearish_badges}</td>
          <td>{item_badges}</td>
          <td class="links">{links}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEC 8-K Analysis — {today}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #f5f6fa; color: #2c3e50; font-size: 13px; }}

  header {{ background: #1a1a2e; color: white; padding: 20px 30px; }}
  header h1 {{ font-size: 20px; font-weight: 500; margin-bottom: 4px; }}
  header p  {{ font-size: 12px; opacity: 0.7; }}

  .summary {{ display: flex; gap: 12px; padding: 16px 30px; flex-wrap: wrap; }}
  .stat {{ background: white; border-radius: 8px; padding: 12px 20px;
           border: 1px solid #e0e0e0; min-width: 100px; text-align: center; }}
  .stat .num {{ font-size: 24px; font-weight: 600; }}
  .stat .lbl {{ font-size: 11px; color: #888; margin-top: 2px; }}
  .s-green {{ color: #0a7c42; }} .s-red {{ color: #c0392b; }}
  .s-orange {{ color: #e67e22; }} .s-gray {{ color: #7f8c8d; }}

  .controls {{ padding: 0 30px 12px; display: flex; gap: 10px; flex-wrap: wrap; }}
  .controls input {{ padding: 7px 12px; border: 1px solid #ddd; border-radius: 6px;
                     font-size: 12px; width: 220px; }}
  .controls select {{ padding: 7px 12px; border: 1px solid #ddd; border-radius: 6px;
                      font-size: 12px; cursor: pointer; }}

  .table-wrap {{ padding: 0 30px 30px; overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; background: white;
           border-radius: 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  thead th {{ background: #1a1a2e; color: white; padding: 10px 12px;
              text-align: left; font-weight: 500; font-size: 12px;
              white-space: nowrap; cursor: pointer; }}
  thead th:hover {{ background: #2d2d4e; }}
  tbody tr {{ border-bottom: 1px solid #f0f0f0; }}
  tbody tr:hover {{ background: #fafbff; }}
  tbody td {{ padding: 9px 12px; vertical-align: top; }}

  .signal {{ display: inline-block; color: white; padding: 3px 8px;
             border-radius: 20px; font-size: 11px; font-weight: 500;
             white-space: nowrap; }}
  .score {{ font-weight: 600; font-size: 14px; text-align: center; }}

  .badge {{ display: inline-block; font-size: 10px; padding: 2px 6px;
            border-radius: 4px; margin: 2px; white-space: nowrap; }}
  .bull {{ background: #e8f5e9; color: #1b5e20; border: 1px solid #a5d6a7; }}
  .bear {{ background: #fce4ec; color: #880e4f; border: 1px solid #f48fb1; }}
  .item {{ background: #e3f2fd; color: #0d47a1; border: 1px solid #90caf9; }}

  .links a {{ color: #3498db; text-decoration: none; margin-right: 6px;
              font-size: 11px; }}
  .links a:hover {{ text-decoration: underline; }}

  .hidden {{ display: none; }}

  footer {{ text-align: center; padding: 20px; font-size: 11px; color: #aaa; }}
</style>
</head>
<body>

<header>
  <h1>📊 SEC 8-K Filing Analyzer</h1>
  <p>Report date: {today} &nbsp;·&nbsp; Generated: {datetime.now().strftime('%H:%M:%S')}
     &nbsp;·&nbsp; Total filings analyzed: {len(results)}</p>
</header>

<div class="summary">
  <div class="stat"><div class="num s-green">{strong_buy}</div><div class="lbl">Strong Buy</div></div>
  <div class="stat"><div class="num s-green">{buy}</div><div class="lbl">Buy</div></div>
  <div class="stat"><div class="num s-green">{bullish}</div><div class="lbl">Slightly Bullish</div></div>
  <div class="stat"><div class="num s-gray">{neutral}</div><div class="lbl">Neutral</div></div>
  <div class="stat"><div class="num s-orange">{bearish}</div><div class="lbl">Slightly Bearish</div></div>
  <div class="stat"><div class="num s-red">{sell}</div><div class="lbl">Sell / Strong Sell</div></div>
  <div class="stat"><div class="num s-gray">{len(results)}</div><div class="lbl">Total Analyzed</div></div>
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
      <th>8-K Items</th>
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
function filterTable() {{
  const search = document.getElementById('search').value.toLowerCase();
  const signal = document.getElementById('signal-filter').value;
  const rows   = document.querySelectorAll('#table-body tr');
  rows.forEach(row => {{
    const text   = row.textContent.toLowerCase();
    const sigTd  = row.cells[3].textContent.trim();
    const matchS = !search || text.includes(search);
    const matchF = !signal || sigTd === signal;
    row.classList.toggle('hidden', !(matchS && matchF));
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
    if (!isNaN(an) && !isNaN(bn)) return dir === 'asc' ? an - bn : bn - an;
    return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
