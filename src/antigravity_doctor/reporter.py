"""Single-file HTML diagnostic report renderer for antigravity-doctor."""

from __future__ import annotations

import html
from datetime import datetime

from .checks import CheckResult


def render_html_report(results: list[CheckResult]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    passed = sum(1 for r in results if r.status == "pass")
    warns = sum(1 for r in results if r.status == "warn")
    fails = sum(1 for r in results if r.status == "fail")

    cards = []
    for r in results:
        detail_html = "".join(f"<li><code>{html.escape(d)}</code></li>" for d in r.details)
        rec_html = (
            f"<div class='rec'><b>Recommendation:</b> {html.escape(r.recommendation)}</div>"
            if r.recommendation
            else ""
        )
        cards.append(
            f"""
            <article class="card {r.status}">
              <div class="head">
                <h3>{html.escape(r.name)}</h3>
                <span class="badge {r.status}">{r.status.upper()}</span>
              </div>
              <p>{html.escape(r.summary)}</p>
              {'<ul>' + detail_html + '</ul>' if detail_html else ''}
              {rec_html}
            </article>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Antigravity Doctor Report</title>
<style>
  body {{ background:#090d16; color:#e2e8f0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; margin:0; padding:32px 20px; }}
  .wrap {{ max-width:920px; margin:0 auto; }}
  h1 {{ margin:0 0 8px; font-size:1.7rem; }}
  .meta {{ color:#94a3b8; font-size:0.9rem; margin-bottom:24px; }}
  .summary {{ display:flex; gap:12px; margin-bottom:24px; flex-wrap:wrap; }}
  .pill {{ padding:8px 14px; border-radius:10px; font-family:monospace; font-size:0.86rem; background:#111827; border:1px solid #1f2937; }}
  .card {{ background:#111827; border:1px solid #1f2937; border-radius:12px; padding:18px; margin-bottom:14px; }}
  .card.pass {{ border-left:4px solid #34d399; }}
  .card.warn {{ border-left:4px solid #fbbf24; }}
  .card.fail {{ border-left:4px solid #f87171; }}
  .head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
  h3 {{ margin:0; font-size:1.05rem; }}
  .badge {{ font-family:monospace; font-size:0.75rem; padding:3px 9px; border-radius:999px; }}
  .badge.pass {{ background:rgba(52,211,153,.15); color:#34d399; }}
  .badge.warn {{ background:rgba(251,191,36,.15); color:#fbbf24; }}
  .badge.fail {{ background:rgba(248,113,113,.15); color:#f87171; }}
  p {{ margin:0 0 10px; color:#cbd5e1; }}
  ul {{ margin:8px 0 0 18px; padding:0; color:#94a3b8; font-size:0.86rem; }}
  li {{ margin-bottom:4px; }}
  .rec {{ margin-top:12px; padding:10px 12px; background:#0f172a; border-radius:8px; font-size:0.86rem; color:#7dd3fc; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Antigravity Doctor · Diagnostic Report</h1>
  <div class="meta">Generated at {now} · Zero-dependency local diagnostics</div>
  <div class="summary">
    <span class="pill">PASS: {passed}</span>
    <span class="pill">WARN: {warns}</span>
    <span class="pill">FAIL: {fails}</span>
  </div>
  {''.join(cards)}
</div>
</body>
</html>
"""
