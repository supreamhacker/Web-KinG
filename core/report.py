"""
Web KinG - Report Generator
=============================
Turns the dict-of-ToolResults produced by each module into one
self-contained HTML report (no external template engine needed)
plus a machine-readable JSON dump for feeding into other tooling.
"""
import json
import html
from pathlib import Path
from datetime import datetime

STYLE = """
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f1117;color:#e6e6e6;margin:0;padding:2rem}
h1{color:#4fd1c5} h2{color:#63b3ed;border-bottom:1px solid #2d3748;padding-bottom:.3rem;margin-top:2rem}
.meta{color:#a0aec0;font-size:.9rem;margin-bottom:1.5rem}
.tool{background:#1a202c;border:1px solid #2d3748;border-radius:8px;margin:.7rem 0;padding:.8rem 1rem}
.tool summary{cursor:pointer;font-weight:600;display:flex;justify-content:space-between}
.ok{color:#68d391} .fail{color:#fc8181} .skip{color:#f6ad55}
pre{white-space:pre-wrap;word-break:break-word;background:#0d0f14;padding:.8rem;border-radius:6px;
    font-size:.82rem;max-height:400px;overflow:auto;margin-top:.6rem}
table{border-collapse:collapse;width:100%;margin:1rem 0}
th,td{border:1px solid #2d3748;padding:.4rem .7rem;text-align:left;font-size:.85rem}
th{background:#1a202c}
"""


def _status_class(r):
    if r.get("returncode") == -1 and "not found" in r.get("stderr", ""):
        return "skip", "SKIPPED (not installed)"
    if r.get("success"):
        return "ok", "OK"
    return "fail", "FAILED"


def generate_report(target, all_results: dict, output_dir="webking_output", title="Web KinG Report"):
    """
    all_results: { "Recon": {tool: ToolResult, ...}, "Web": {...}, ... }
    Writes report.html and report.json into output_dir. Returns the html path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Flatten for JSON
    json_blob = {"target": target, "generated": datetime.now().isoformat(), "sections": {}}
    for section, tools in all_results.items():
        json_blob["sections"][section] = {name: r.to_dict() for name, r in tools.items()}
    with open(out / "report.json", "w", encoding="utf-8") as f:
        json.dump(json_blob, f, indent=2)

    # Summary counts
    total = ok = failed = skipped = 0
    body_sections = []
    for section, tools in all_results.items():
        rows = []
        for name, r in tools.items():
            d = r.to_dict()
            total += 1
            cls, label = _status_class(d)
            if cls == "ok":
                ok += 1
            elif cls == "skip":
                skipped += 1
            else:
                failed += 1
            rows.append(f"""
            <details class="tool">
              <summary>{html.escape(name)} — <span class="{cls}">{label}</span>
                <span style="color:#718096">{d['duration_sec']}s</span></summary>
              <p style="color:#a0aec0;font-size:.8rem">$ {html.escape(d['command'])}</p>
              <pre>{html.escape(d['stdout'][:8000]) or '(no stdout)'}</pre>
              {'<pre style="color:#fc8181">' + html.escape(d['stderr'][:3000]) + '</pre>' if d['stderr'] else ''}
            </details>""")
        body_sections.append(f"<h2>{html.escape(section)}</h2>" + "".join(rows))

    html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{STYLE}</style></head>
<body>
<h1>🛡 Web KinG — Pentest Report</h1>
<div class="meta">
  Target: <b>{html.escape(target)}</b> &nbsp;|&nbsp;
  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp;
  Tools run: {total} (<span class="ok">{ok} ok</span>,
  <span class="fail">{failed} failed</span>,
  <span class="skip">{skipped} skipped</span>)
</div>
{''.join(body_sections)}
</body></html>"""

    html_path = out / "report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return str(html_path)
