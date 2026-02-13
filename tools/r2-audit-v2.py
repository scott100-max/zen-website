#!/usr/bin/env python3
"""R2 Audio Audit V2 — "For Kids" simplified report.

Same data collection as r2-audit.py, but the HTML output is radically simplified:
  - 6 columns instead of 17
  - Plain-English stage names and issue descriptions
  - Big friendly summary cards
  - No jargon (R2, CDN, vault, chunks, ambient, fades, QA gates...)

Usage:
    python3 tools/r2-audit-v2.py                          # default output
    python3 tools/r2-audit-v2.py -o ~/Desktop/report.html # custom output
    python3 tools/r2-audit-v2.py --skip-cdn               # offline mode
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Re-use all the data-collection machinery from v1
sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib.util import spec_from_file_location, module_from_spec

_v1_path = Path(__file__).resolve().parent / "r2-audit.py"
_spec = spec_from_file_location("r2audit", _v1_path)
_v1 = module_from_spec(_spec)
_spec.loader.exec_module(_v1)

# Pull in everything we need
parse_script = _v1.parse_script
discover_local_files = _v1.discover_local_files
discover_sounds_files = _v1.discover_sounds_files
discover_vault_finals = _v1.discover_vault_finals
read_vault_metadata = _v1.read_vault_metadata
scan_html_references = _v1.scan_html_references
batch_head_checks = _v1.batch_head_checks
build_session_list = _v1.build_session_list
build_asmr_list = _v1.build_asmr_list
detect_stage = _v1.detect_stage
detect_issues = _v1.detect_issues
fmt_size = _v1.fmt_size
SCRIPTS_DIR = _v1.SCRIPTS_DIR
AUDIO_DIR = _v1.AUDIO_DIR
VAULT_DIR = _v1.VAULT_DIR
CDN_BASE = _v1.CDN_BASE
SOUNDS_CDN_BASE = _v1.SOUNDS_CDN_BASE
SESSION_RE = _v1.SESSION_RE
PROJECT_ROOT = _v1.PROJECT_ROOT


# ---------------------------------------------------------------------------
# Plain-English translations
# ---------------------------------------------------------------------------

STAGE_FRIENDLY = {
    "live":        ("On the website", "People can listen to this right now."),
    "vault-built": ("Built, not uploaded", "The audio is ready but hasn't been put on the website yet."),
    "picked":      ("Voices chosen", "The best voice recordings have been picked. Needs to be stitched together."),
    "generated":   ("Recordings made", "The computer has made voice recordings but nobody has picked the best ones yet."),
    "legacy":      ("Old version", "This was made with an older method. Might need rebuilding."),
    "outstanding": ("Not started", "There's a script written but no audio has been made yet."),
}

STAGE_EMOJI = {
    "live":        "&#x1F7E2;",  # green circle
    "vault-built": "&#x1F535;",  # blue circle
    "picked":      "&#x1F7E1;",  # yellow circle
    "generated":   "&#x1F7E3;",  # purple circle
    "legacy":      "&#x1F7E0;",  # orange circle
    "outstanding": "&#x26AA;",   # white circle
}


def simplify_issue(sev, msg):
    """Turn a technical issue message into plain English."""
    m = msg.lower()

    if "no ambient fade-in" in m:
        return sev, "Background music starts too suddenly"
    if "no ambient fade-out" in m:
        return sev, "Background music ends too suddenly"
    if "no ambient-db" in m:
        return sev, "Background music volume not set"
    if "duration drift" in m:
        match = re.search(r"target (\d+)m, actual ([\d.]+)m", msg)
        if match:
            target, actual = match.group(1), match.group(2)
            return sev, f"Should be {target} min but came out as {actual} min"
        return sev, "Length doesn't match what was planned"
    if "local/r2 size mismatch" in m:
        return "warn", "Computer version doesn't match website version"
    if "r2 404" in m and "html" in m:
        return "error", "Website page links to a file that doesn't exist!"
    if "not on r2" in m:
        return "info", "Not uploaded to the website yet"
    if "qa failed" in m:
        return sev, "Didn't pass the quality check"
    if "vault built but no html" in m:
        return sev, "Audio is built but no page on the website links to it"
    if "html references file missing" in m:
        return "error", "Website links to a file that's missing from the computer"
    if "mp3 variants" in m:
        match = re.search(r"(\d+) mp3", m)
        n = match.group(1) if match else "multiple"
        return "info", f"{n} different versions sitting around (only need 1)"
    if "assembly review" in m:
        match = re.search(r"(\d+)/(\d+) pass", msg)
        if match:
            ok, total = match.group(1), match.group(2)
            return sev, f"{ok} out of {total} voice clips sound good"
        return sev, "Some voice clips need replacing"
    if "script exists, no audio" in m:
        return "info", "Script is written but audio hasn't been made yet"
    if "r2 http" in m:
        return "error", "Something went wrong checking the website"
    if "r2 check failed" in m:
        return "error", "Couldn't reach the website to check"

    # Fallback — return as-is
    return sev, msg


# ---------------------------------------------------------------------------
# HTML generation — the simple version
# ---------------------------------------------------------------------------

def generate_simple_html(sessions_data, cdn_results, run_time, skip_cdn):
    total = len(sessions_data)
    stages = {}
    problem_count = 0
    ok_count = 0

    for s in sessions_data:
        st = s.get("stage", "outstanding")
        stages[st] = stages.get(st, 0) + 1
        issues = s.get("issues", [])
        has_real_problem = any(sv in ("error", "warn") for sv, _ in issues)
        if has_real_problem:
            problem_count += 1
        elif st == "live":
            ok_count += 1

    live = stages.get("live", 0)
    in_progress = stages.get("vault-built", 0) + stages.get("picked", 0) + stages.get("generated", 0)
    not_started = stages.get("outstanding", 0)
    old = stages.get("legacy", 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Audio Report (Simple) — {datetime.now().strftime('%d %b %Y')}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#FFF1E5; color:#33302E; font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; font-size:14px; padding:24px; max-width:1200px; margin:0 auto; }}

h1 {{ color:#1A1817; font-size:24px; font-weight:700; margin-bottom:4px; }}
.subtitle {{ color:#807973; font-size:13px; margin-bottom:24px; }}

/* Big summary cards */
.cards {{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:32px; }}
.card {{ background:#fff; border:1px solid #E0CDBF; border-radius:12px; padding:20px 24px; min-width:140px; flex:1; text-align:center; }}
.card-num {{ font-size:42px; font-weight:800; line-height:1; }}
.card-label {{ font-size:13px; color:#807973; margin-top:6px; }}
.card-desc {{ font-size:11px; color:#B0A89F; margin-top:2px; }}
.card-green .card-num {{ color:#1B7A3D; }}
.card-blue .card-num {{ color:#2563EB; }}
.card-grey .card-num {{ color:#807973; }}
.card-orange .card-num {{ color:#B45309; }}
.card-red .card-num {{ color:#CC0000; }}

/* Legend */
.legend {{ background:#fff; border:1px solid #E0CDBF; border-radius:12px; padding:16px 20px; margin-bottom:24px; display:flex; flex-wrap:wrap; gap:8px 24px; }}
.legend-item {{ display:flex; align-items:center; gap:6px; font-size:13px; }}
.legend-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}

/* Filters */
.controls {{ display:flex; gap:12px; align-items:center; margin-bottom:16px; flex-wrap:wrap; }}
.controls select, .controls input {{ background:#fff; border:1px solid #E0CDBF; color:#33302E; padding:8px 12px; border-radius:8px; font-size:14px; }}
.controls input {{ width:240px; }}

/* Table */
table {{ width:100%; border-collapse:separate; border-spacing:0; margin-bottom:32px; }}
th {{ background:#F2DFCE; color:#807973; font-size:12px; text-transform:uppercase; letter-spacing:0.5px; padding:10px 12px; text-align:left; border-bottom:2px solid #E0CDBF; cursor:pointer; user-select:none; white-space:nowrap; }}
th:first-child {{ border-radius:8px 0 0 0; }}
th:last-child {{ border-radius:0 8px 0 0; }}
th:hover {{ color:#1A1817; }}
td {{ padding:10px 12px; border-bottom:1px solid #F0E6DC; font-size:13px; }}
tr:hover td {{ background:#FFF7F0; }}
.col-num {{ width:44px; text-align:center; }}
.col-name {{ width:220px; font-weight:600; }}
.col-type {{ width:100px; }}
.col-status {{ width:200px; }}
.col-whats-wrong {{ min-width:280px; }}

/* Stage badges */
.badge {{ display:inline-block; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; white-space:nowrap; }}
.badge-live {{ background:#D4EDDA; color:#1B5E20; }}
.badge-vault-built {{ background:#DBEAFE; color:#1E40AF; }}
.badge-picked {{ background:#FEF3C7; color:#92400E; }}
.badge-generated {{ background:#EDE9FE; color:#5B21B6; }}
.badge-legacy {{ background:#FFEDD5; color:#9A3412; }}
.badge-outstanding {{ background:#F3F4F6; color:#6B7280; }}

/* Issues */
.issue {{ display:inline-block; margin:2px 0; font-size:12px; line-height:1.5; }}
.issue::before {{ content:''; display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; vertical-align:middle; }}
.issue-error::before {{ background:#CC0000; }}
.issue-warn::before {{ background:#D97706; }}
.issue-info::before {{ background:#B0A89F; }}
.all-good {{ color:#1B7A3D; font-weight:600; font-size:12px; }}

/* How it works */
.how-it-works {{ background:#fff; border:1px solid #E0CDBF; border-radius:12px; padding:20px 24px; margin-bottom:24px; }}
.how-it-works h2 {{ font-size:16px; margin-bottom:12px; }}
.pipeline {{ display:flex; align-items:center; gap:0; flex-wrap:wrap; justify-content:center; }}
.pipe-step {{ background:#F9FAFB; border:1px solid #E0CDBF; border-radius:8px; padding:10px 14px; text-align:center; min-width:120px; }}
.pipe-step .step-emoji {{ font-size:24px; }}
.pipe-step .step-label {{ font-size:12px; font-weight:600; margin-top:4px; }}
.pipe-step .step-desc {{ font-size:11px; color:#807973; }}
.pipe-arrow {{ font-size:20px; color:#B0A89F; padding:0 4px; }}
</style>
</head>
<body>

<h1>Audio Report</h1>
<div class="subtitle">The simple version &middot; {datetime.now().strftime('%d %b %Y')} &middot; {total} sessions{' &middot; website checks skipped' if skip_cdn else ''}</div>

<div class="cards">
  <div class="card card-green">
    <div class="card-num">{live}</div>
    <div class="card-label">On the Website</div>
    <div class="card-desc">People can listen now</div>
  </div>
  <div class="card card-blue">
    <div class="card-num">{in_progress}</div>
    <div class="card-label">Work in Progress</div>
    <div class="card-desc">Being built</div>
  </div>
  <div class="card card-grey">
    <div class="card-num">{not_started}</div>
    <div class="card-label">Not Started</div>
    <div class="card-desc">Script only</div>
  </div>
  <div class="card card-orange">
    <div class="card-num">{old}</div>
    <div class="card-label">Old Version</div>
    <div class="card-desc">Might need redoing</div>
  </div>
  <div class="card card-red">
    <div class="card-num">{problem_count}</div>
    <div class="card-label">Need Attention</div>
    <div class="card-desc">Something to fix</div>
  </div>
</div>

<div class="how-it-works">
<h2>How a session gets made</h2>
<div class="pipeline">
  <div class="pipe-step"><div class="step-emoji">&#x1F4DD;</div><div class="step-label">Write Script</div><div class="step-desc">Words to say</div></div>
  <span class="pipe-arrow">&#x27A1;</span>
  <div class="pipe-step"><div class="step-emoji">&#x1F399;</div><div class="step-label">Record Voices</div><div class="step-desc">Computer reads it</div></div>
  <span class="pipe-arrow">&#x27A1;</span>
  <div class="pipe-step"><div class="step-emoji">&#x1F44D;</div><div class="step-label">Pick the Best</div><div class="step-desc">Choose good takes</div></div>
  <span class="pipe-arrow">&#x27A1;</span>
  <div class="pipe-step"><div class="step-emoji">&#x1F3B5;</div><div class="step-label">Build Audio</div><div class="step-desc">Stitch + add music</div></div>
  <span class="pipe-arrow">&#x27A1;</span>
  <div class="pipe-step"><div class="step-emoji">&#x1F310;</div><div class="step-label">Upload</div><div class="step-desc">Put on website</div></div>
  <span class="pipe-arrow">&#x27A1;</span>
  <div class="pipe-step"><div class="step-emoji">&#x2705;</div><div class="step-label">Live!</div><div class="step-desc">People listen</div></div>
</div>
</div>

<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#1B7A3D"></div> On the Website</div>
  <div class="legend-item"><div class="legend-dot" style="background:#2563EB"></div> Built, Not Uploaded</div>
  <div class="legend-item"><div class="legend-dot" style="background:#D97706"></div> Voices Chosen</div>
  <div class="legend-item"><div class="legend-dot" style="background:#7C3AED"></div> Recordings Made</div>
  <div class="legend-item"><div class="legend-dot" style="background:#EA580C"></div> Old Version</div>
  <div class="legend-item"><div class="legend-dot" style="background:#9CA3AF"></div> Not Started</div>
</div>

<div class="controls">
  <select id="stageFilter" onchange="filterTable()">
    <option value="">Show All</option>
    <option value="live">On the Website</option>
    <option value="vault-built">Built, Not Uploaded</option>
    <option value="picked">Voices Chosen</option>
    <option value="generated">Recordings Made</option>
    <option value="legacy">Old Version</option>
    <option value="outstanding">Not Started</option>
  </select>
  <select id="problemFilter" onchange="filterTable()">
    <option value="">All Sessions</option>
    <option value="problems">Only with Problems</option>
    <option value="ok">Only OK ones</option>
  </select>
  <input type="text" id="searchBox" placeholder="Search by name..." oninput="filterTable()">
</div>

<table id="mainTable">
<thead>
<tr>
  <th class="col-num" data-col="0" onclick="sortTable(0,'num')">#</th>
  <th class="col-name" data-col="1" onclick="sortTable(1,'str')">Name</th>
  <th class="col-type" data-col="2" onclick="sortTable(2,'str')">Type</th>
  <th class="col-status" data-col="3" onclick="sortTable(3,'str')">Where Is It?</th>
  <th class="col-whats-wrong" data-col="4" onclick="sortTable(4,'str')">What's Going On?</th>
</tr>
</thead>
<tbody>
"""

    for s in sessions_data:
        sid = s["id"]
        num = s["num"]
        sm = s.get("script_meta") or {}
        stage = s.get("stage", "outstanding")
        issues = s.get("issues", [])

        name = sm.get("title", sid)
        cat = sm.get("category", "").capitalize() or "—"

        stage_label, _ = STAGE_FRIENDLY.get(stage, (stage, ""))

        # Simplify issues
        simple_issues = []
        seen = set()
        for sev, msg in issues:
            new_sev, new_msg = simplify_issue(sev, msg)
            if new_msg not in seen:
                seen.add(new_msg)
                simple_issues.append((new_sev, new_msg))

        # Only show warn/error issues — skip info unless there's nothing else
        important = [(sv, m) for sv, m in simple_issues if sv in ("error", "warn")]
        info_only = [(sv, m) for sv, m in simple_issues if sv == "info"]

        has_problems = len(important) > 0
        problem_attr = "problems" if has_problems else "ok"

        if important:
            issues_html = "<br>".join(
                f'<span class="issue issue-{sv}">{m}</span>' for sv, m in important
            )
            # Add info items collapsed if there are important ones too
            if info_only:
                issues_html += "<br>" + "<br>".join(
                    f'<span class="issue issue-info">{m}</span>' for _, m in info_only
                )
        elif info_only:
            issues_html = "<br>".join(
                f'<span class="issue issue-info">{m}</span>' for _, m in info_only
            )
        else:
            issues_html = '<span class="all-good">All good!</span>'

        html += f"""<tr data-stage="{stage}" data-problems="{problem_attr}" data-search="{num} {name.lower()} {cat.lower()}">
  <td class="col-num">{num}</td>
  <td class="col-name">{name}</td>
  <td class="col-type">{cat}</td>
  <td><span class="badge badge-{stage}">{stage_label}</span></td>
  <td>{issues_html}</td>
</tr>
"""

    html += """</tbody>
</table>

<script>
let sortCol = 0, sortAsc = true;

function sortTable(col, type) {
  const table = document.getElementById('mainTable');
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  if (col === sortCol) sortAsc = !sortAsc;
  else { sortCol = col; sortAsc = true; }

  rows.sort((a, b) => {
    let va = a.cells[col].textContent.trim();
    let vb = b.cells[col].textContent.trim();
    if (type === 'num') { va = parseInt(va) || 0; vb = parseInt(vb) || 0; }
    else { va = va.toLowerCase(); vb = vb.toLowerCase(); }
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  });
  rows.forEach(r => tbody.appendChild(r));
}

function filterTable() {
  const stage = document.getElementById('stageFilter').value;
  const prob = document.getElementById('problemFilter').value;
  const search = document.getElementById('searchBox').value.toLowerCase();
  const rows = document.querySelectorAll('#mainTable tbody tr');

  rows.forEach(row => {
    let show = true;
    if (stage && row.dataset.stage !== stage) show = false;
    if (prob && row.dataset.problems !== prob) show = false;
    if (search && !row.dataset.search.includes(search)) show = false;
    row.style.display = show ? '' : 'none';
  });
}
</script>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Main — same data collection, different output
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="R2 Audio Audit V2 — simplified report")
    parser.add_argument("-o", "--output", default="r2-audit-report-v2.html",
                        help="Output HTML file path")
    parser.add_argument("--skip-cdn", action="store_true",
                        help="Skip CDN HEAD checks (offline mode)")
    args = parser.parse_args()

    start = datetime.now()
    print("R2 Audio Audit — Simple Version")
    print("=" * 50)

    # 1. Parse scripts
    print("Parsing scripts...")
    scripts = {}
    for f in SCRIPTS_DIR.glob("*.txt"):
        m = SESSION_RE.match(f.stem)
        if m:
            scripts[f.stem] = parse_script(f)
    print(f"  {len(scripts)} scripts found")

    # 2. Discover local files
    print("Discovering local files...")
    local_files = discover_local_files()
    sounds_files = discover_sounds_files()
    vault_finals = discover_vault_finals()
    print(f"  {len(local_files)} audio files")

    # 3. Read vault metadata
    print("Reading vault metadata...")
    vault_meta = read_vault_metadata()
    print(f"  {len(vault_meta)} vault sessions")

    # 4. Scan HTML references
    print("Scanning HTML references...")
    html_refs = scan_html_references()
    print(f"  {len(html_refs)} unique files referenced")

    # 5. Build session list
    sessions = build_session_list()
    print(f"  {len(sessions)} total sessions")

    # 6. CDN checks
    urls_to_check = set()
    if not args.skip_cdn:
        for sid in sessions:
            urls_to_check.add(f"{CDN_BASE}/{sid}.mp3")
        for fname, refs in html_refs.items():
            for _, url in refs:
                urls_to_check.add(url)
        print(f"Checking {len(urls_to_check)} URLs on the website...")
        cdn_results = batch_head_checks(urls_to_check)
        ok = sum(1 for r in cdn_results.values() if r.get("status") == 200)
        missing = sum(1 for r in cdn_results.values() if r.get("status") == 404)
        print(f"  {ok} found, {missing} missing")
    else:
        cdn_results = {}
        print("  Website checks skipped")

    # 7. Assemble per-session data
    print("Putting it all together...")
    sessions_data = []
    for sid, sinfo in sorted(sessions.items(), key=lambda x: x[1]["num"]):
        sm = scripts.get(sid)
        vm = vault_meta.get(sid)

        session_local = {}
        for fname, finfo in local_files.items():
            base = fname.rsplit(".", 1)[0]
            if base == sid or base.startswith(sid + "-"):
                session_local[fname] = finfo
            elif base == f"raw_{sid}":
                session_local[fname] = finfo

        session_refs = {}
        for fname, refs in html_refs.items():
            base = fname.rsplit(".", 1)[0]
            if base == sid or base.startswith(sid + "-"):
                session_refs[fname] = refs

        stage = detect_stage(sid, vm, local_files, html_refs, cdn_results)
        issues = detect_issues(sinfo, sm, vm, local_files, session_refs,
                               cdn_results, vault_finals)

        sessions_data.append({
            "id": sid,
            "num": sinfo["num"],
            "script_meta": sm,
            "vault_meta": vm,
            "local_files": session_local,
            "html_refs": session_refs,
            "stage": stage,
            "issues": issues,
        })

    run_time = (datetime.now() - start).total_seconds()

    # 8. Generate simple HTML
    print("Building the simple report...")
    html = generate_simple_html(sessions_data, cdn_results, run_time, args.skip_cdn)

    output_path = Path(args.output).expanduser()
    output_path.write_text(html)
    print(f"\nReport: {output_path}")
    print(f"Done in {run_time:.1f}s")


if __name__ == "__main__":
    main()
