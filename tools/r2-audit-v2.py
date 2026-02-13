#!/usr/bin/env python3
"""R2 Audio Audit V2 — "Five-Year-Old" report.

Ultra-simplified visual report:
  - Giant progress bar at the top
  - Card tiles grouped by status (not a table)
  - One emoji + one sentence per session
  - Zero jargon

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
load_approvals = _v1.load_approvals
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
    "live":        ("Done!", "People can listen to this right now."),
    "vault-built": ("Almost done", "Just needs uploading."),
    "picked":      ("Halfway there", "Best voices picked — needs stitching."),
    "generated":   ("Early days", "Voices recorded — need picking."),
    "legacy":      ("Old one", "Made the old way."),
    "outstanding": ("Not started", "Just a script so far."),
}

# Simple 3-bucket grouping for the visual layout
BUCKET_ORDER = ["done", "working", "todo"]
BUCKET_INFO = {
    "done":    {"label": "Done",        "emoji": "&#x2705;", "color": "#1B7A3D", "bg": "#D4EDDA", "border": "#A3D9A5"},
    "working": {"label": "Working on it", "emoji": "&#x1F528;", "color": "#B45309", "bg": "#FEF3C7", "border": "#FCD34D"},
    "todo":    {"label": "To do",       "emoji": "&#x1F4DD;", "color": "#6B7280", "bg": "#F3F4F6", "border": "#D1D5DB"},
}

def stage_to_bucket(stage):
    if stage == "live":
        return "done"
    elif stage in ("vault-built", "picked", "generated", "legacy"):
        return "working"
    else:
        return "todo"


def simplify_issue_v2(sev, msg):
    """Turn a technical issue into one tiny sentence a kid could understand."""
    m = msg.lower()

    if "no ambient fade-in" in m:
        return "warn", "Music starts too suddenly"
    if "no ambient fade-out" in m:
        return "warn", "Music ends too suddenly"
    if "no ambient-db" in m:
        return "warn", "Music volume not set"
    if "duration drift" in m:
        match = re.search(r"target (\d+)m, actual ([\d.]+)m", msg)
        if match:
            return "warn", f"Too short ({match.group(2)} min, wanted {match.group(1)})"
        return "warn", "Wrong length"
    if "local/r2 size mismatch" in m:
        return "warn", "Local file doesn't match website"
    if "r2 404" in m and "html" in m:
        return "error", "Broken link on website!"
    if "not on r2" in m:
        return "info", "Not uploaded yet"
    if "qa failed" in m:
        return "warn", "Didn't pass quality check"
    if "vault built but no html" in m:
        return "info", "Built but no page links to it"
    if "html references file missing" in m:
        return "error", "Website points to missing file!"
    if "mp3 variants" in m:
        return "info", "Extra copies lying around"
    if "assembly review" in m:
        match = re.search(r"(\d+)/(\d+) pass", msg)
        if match:
            return "warn", f"{match.group(1)}/{match.group(2)} clips OK"
        return "warn", "Some clips need replacing"
    if "script exists, no audio" in m:
        return "info", "Script only — no audio yet"
    if "r2 http" in m or "r2 check failed" in m:
        return "error", "Couldn't check website"
    if m.startswith("approved"):
        return "approved", msg

    return sev, msg


# ---------------------------------------------------------------------------
# HTML generation — the simple version
# ---------------------------------------------------------------------------

def generate_simple_html(sessions_data, cdn_results, run_time, skip_cdn):
    total = len(sessions_data)

    # Count buckets
    buckets = {"done": [], "working": [], "todo": []}
    problem_sessions = []

    for s in sessions_data:
        stage = s.get("stage", "outstanding")
        bucket = stage_to_bucket(stage)
        issues = s.get("issues", [])

        # Simplify issues
        simple = []
        seen = set()
        for sev, msg in issues:
            new_sev, new_msg = simplify_issue_v2(sev, msg)
            if new_msg not in seen:
                seen.add(new_msg)
                simple.append((new_sev, new_msg))

        important = [(sv, m) for sv, m in simple if sv in ("error", "warn")]
        has_problem = len(important) > 0

        s["_bucket"] = bucket
        s["_simple_issues"] = simple
        s["_has_problem"] = has_problem
        s["_important"] = important

        buckets[bucket].append(s)
        if has_problem:
            problem_sessions.append(s)

    done_count = len(buckets["done"])
    working_count = len(buckets["working"])
    todo_count = len(buckets["todo"])
    pct = round(done_count / total * 100) if total else 0

    # Count "done and clean" vs "done but has issues"
    done_clean = sum(1 for s in buckets["done"] if not s["_has_problem"])
    done_issues = done_count - done_clean

    # Sub-stage counts for "working on it"
    working_stages = {}
    for s in buckets["working"]:
        st = s.get("stage", "?")
        friendly, _ = STAGE_FRIENDLY.get(st, (st, ""))
        working_stages[friendly] = working_stages.get(friendly, 0) + 1

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Audio Report &mdash; {datetime.now().strftime('%d %b %Y')}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#FFF1E5; color:#33302E; font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; padding:24px; max-width:960px; margin:0 auto; }}

h1 {{ font-size:28px; font-weight:800; margin-bottom:4px; }}
.sub {{ color:#807973; font-size:13px; margin-bottom:28px; }}

/* === Big progress bar === */
.progress-wrap {{ background:#fff; border:1px solid #E0CDBF; border-radius:16px; padding:24px; margin-bottom:28px; }}
.progress-title {{ font-size:18px; font-weight:700; margin-bottom:4px; }}
.progress-subtitle {{ font-size:13px; color:#807973; margin-bottom:14px; }}
.bar-outer {{ background:#F0E6DC; border-radius:12px; height:40px; overflow:hidden; display:flex; }}
.bar-done {{ background:linear-gradient(135deg, #22C55E, #16A34A); height:100%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-size:15px; min-width:40px; transition:width 0.5s; }}
.bar-working {{ background:linear-gradient(135deg, #FBBF24, #F59E0B); height:100%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-size:15px; min-width:40px; transition:width 0.5s; }}
.bar-todo {{ height:100%; display:flex; align-items:center; justify-content:center; color:#9CA3AF; font-weight:700; font-size:14px; min-width:30px; }}
.bar-labels {{ display:flex; justify-content:space-between; margin-top:10px; font-size:13px; }}
.bar-labels span {{ display:flex; align-items:center; gap:5px; }}
.dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}

/* === Three big number cards === */
.three-cards {{ display:flex; gap:16px; margin-bottom:28px; }}
.big-card {{ flex:1; background:#fff; border-radius:14px; padding:20px; text-align:center; border:2px solid #E0CDBF; }}
.big-card-emoji {{ font-size:36px; line-height:1; }}
.big-card-num {{ font-size:48px; font-weight:900; line-height:1.1; }}
.big-card-label {{ font-size:14px; font-weight:600; margin-top:4px; }}
.big-card-detail {{ font-size:11px; color:#807973; margin-top:2px; }}
.bc-done {{ border-color:#A3D9A5; }}
.bc-done .big-card-num {{ color:#16A34A; }}
.bc-working {{ border-color:#FCD34D; }}
.bc-working .big-card-num {{ color:#D97706; }}
.bc-todo {{ border-color:#D1D5DB; }}
.bc-todo .big-card-num {{ color:#9CA3AF; }}

/* === Pipeline (how it works) === */
.pipeline-box {{ background:#fff; border:1px solid #E0CDBF; border-radius:14px; padding:20px; margin-bottom:28px; text-align:center; }}
.pipeline-box h2 {{ font-size:15px; font-weight:700; margin-bottom:14px; }}
.pipe {{ display:flex; align-items:center; justify-content:center; gap:0; flex-wrap:wrap; }}
.pipe-step {{ display:flex; flex-direction:column; align-items:center; padding:8px 10px; }}
.pipe-step .pe {{ font-size:28px; }}
.pipe-step .pl {{ font-size:11px; font-weight:700; margin-top:2px; }}
.pipe-arrow {{ font-size:22px; color:#D1D5DB; }}

/* === Section groups === */
.section {{ margin-bottom:28px; }}
.section-head {{ display:flex; align-items:center; gap:10px; margin-bottom:12px; }}
.section-head h2 {{ font-size:18px; font-weight:700; }}
.section-count {{ background:#F0E6DC; color:#807973; font-size:12px; font-weight:700; padding:2px 10px; border-radius:10px; }}

/* === Session tiles === */
.tiles {{ display:flex; flex-wrap:wrap; gap:10px; }}
.tile {{ background:#fff; border:2px solid #E0CDBF; border-radius:10px; padding:10px 14px; width:calc(50% - 5px); display:flex; align-items:flex-start; gap:10px; transition:border-color 0.2s; }}
.tile:hover {{ border-color:#B0A89F; }}
.tile-emoji {{ font-size:24px; flex-shrink:0; padding-top:1px; }}
.tile-body {{ flex:1; min-width:0; }}
.tile-name {{ font-size:14px; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.tile-num {{ color:#B0A89F; font-size:12px; font-weight:600; }}
.tile-stage {{ font-size:11px; color:#807973; margin-top:1px; }}
.tile-issue {{ font-size:11px; margin-top:3px; display:flex; align-items:center; gap:4px; }}
.tile-issue .idot {{ width:6px; height:6px; border-radius:50%; flex-shrink:0; }}
.idot-error {{ background:#DC2626; }}
.idot-warn {{ background:#F59E0B; }}
.idot-info {{ background:#D1D5DB; }}
.tile-ok {{ font-size:11px; color:#16A34A; font-weight:600; margin-top:3px; }}

.tile-done {{ border-color:#A3D9A5; }}
.tile-done.has-problem {{ border-color:#FCD34D; }}
.tile-working {{ border-color:#FCD34D; }}
.tile-todo {{ border-color:#D1D5DB; }}

/* === Footer === */
.foot {{ text-align:center; color:#B0A89F; font-size:11px; padding:16px 0; }}

/* Responsive */
@media (max-width: 640px) {{
  .three-cards {{ flex-direction:column; }}
  .tile {{ width:100%; }}
}}
</style>
</head>
<body>

<h1>Audio Report</h1>
<div class="sub">{datetime.now().strftime('%d %b %Y')} &middot; {total} sessions total{' &middot; website checks skipped' if skip_cdn else ''}</div>

<!-- PROGRESS BAR -->
<div class="progress-wrap">
  <div class="progress-title">{pct}% done</div>
  <div class="progress-subtitle">{done_count} finished, {working_count} being worked on, {todo_count} still to do</div>
  <div class="bar-outer">
    <div class="bar-done" style="width:{done_count/total*100 if total else 0:.1f}%">{done_count}</div>
    <div class="bar-working" style="width:{working_count/total*100 if total else 0:.1f}%">{working_count}</div>
    <div class="bar-todo" style="width:{todo_count/total*100 if total else 0:.1f}%">{todo_count}</div>
  </div>
  <div class="bar-labels">
    <span><span class="dot" style="background:#16A34A"></span> Done</span>
    <span><span class="dot" style="background:#F59E0B"></span> Working on it</span>
    <span><span class="dot" style="background:#D1D5DB"></span> To do</span>
  </div>
</div>

<!-- THREE BIG CARDS -->
<div class="three-cards">
  <div class="big-card bc-done">
    <div class="big-card-emoji">&#x2705;</div>
    <div class="big-card-num">{done_count}</div>
    <div class="big-card-label">Done</div>
    <div class="big-card-detail">{done_clean} perfect, {done_issues} have small issues</div>
  </div>
  <div class="big-card bc-working">
    <div class="big-card-emoji">&#x1F528;</div>
    <div class="big-card-num">{working_count}</div>
    <div class="big-card-label">Working on it</div>
    <div class="big-card-detail">{', '.join(f'{v} {k.lower()}' for k, v in working_stages.items()) if working_stages else 'None right now'}</div>
  </div>
  <div class="big-card bc-todo">
    <div class="big-card-emoji">&#x1F4DD;</div>
    <div class="big-card-num">{todo_count}</div>
    <div class="big-card-label">To do</div>
    <div class="big-card-detail">Script written, nothing else yet</div>
  </div>
</div>

<!-- HOW IT WORKS -->
<div class="pipeline-box">
<h2>How each session gets made</h2>
<div class="pipe">
  <div class="pipe-step"><div class="pe">&#x1F4DD;</div><div class="pl">Write it</div></div>
  <span class="pipe-arrow">&#x27A1;&#xFE0F;</span>
  <div class="pipe-step"><div class="pe">&#x1F399;&#xFE0F;</div><div class="pl">Record it</div></div>
  <span class="pipe-arrow">&#x27A1;&#xFE0F;</span>
  <div class="pipe-step"><div class="pe">&#x1F44D;</div><div class="pl">Pick best</div></div>
  <span class="pipe-arrow">&#x27A1;&#xFE0F;</span>
  <div class="pipe-step"><div class="pe">&#x1F3B5;</div><div class="pl">Build it</div></div>
  <span class="pipe-arrow">&#x27A1;&#xFE0F;</span>
  <div class="pipe-step"><div class="pe">&#x1F680;</div><div class="pl">Upload</div></div>
  <span class="pipe-arrow">&#x27A1;&#xFE0F;</span>
  <div class="pipe-step"><div class="pe">&#x2705;</div><div class="pl">Live!</div></div>
</div>
</div>
"""

    # Render each bucket as a section of tiles
    for bucket_key in BUCKET_ORDER:
        items = buckets[bucket_key]
        if not items:
            continue

        info = BUCKET_INFO[bucket_key]
        html += f"""
<div class="section">
  <div class="section-head">
    <h2>{info['emoji']} {info['label']}</h2>
    <span class="section-count">{len(items)}</span>
  </div>
  <div class="tiles">
"""
        for s in items:
            sm = s.get("script_meta") or {}
            name = sm.get("title", s["id"])
            num = s["num"]
            stage = s.get("stage", "outstanding")
            stage_label, _ = STAGE_FRIENDLY.get(stage, (stage, ""))
            has_problem = s["_has_problem"]
            important = s["_important"]
            simple = s["_simple_issues"]

            is_approved = any(sv == "approved" for sv, _ in simple)

            # Pick tile emoji based on stage
            if stage == "live" and not has_problem:
                emoji = "&#x2705;"
            elif stage == "live" and has_problem:
                emoji = "&#x26A0;&#xFE0F;"
            elif stage == "vault-built":
                emoji = "&#x1F4E6;"
            elif stage == "picked":
                emoji = "&#x1F44D;"
            elif stage == "generated":
                emoji = "&#x1F399;&#xFE0F;"
            elif stage == "legacy":
                emoji = "&#x1F504;"
            else:
                emoji = "&#x1F4DD;"

            problem_class = " has-problem" if has_problem else ""
            tile_class = f"tile tile-{bucket_key}{problem_class}"

            # Build issue HTML — max 2 issues shown
            if important:
                issue_html = ""
                for sv, m in important[:2]:
                    issue_html += f'<div class="tile-issue"><span class="idot idot-{sv}"></span> {m}</div>'
                if len(important) > 2:
                    issue_html += f'<div class="tile-issue" style="color:#B0A89F;">+{len(important)-2} more</div>'
            elif bucket_key == "done" and is_approved:
                issue_html = '<div class="tile-ok">Approved &#x2714;&#xFE0F;</div>'
            elif bucket_key == "done":
                issue_html = '<div class="tile-ok">All good!</div>'
            else:
                # For working/todo, show the stage as a hint
                issue_html = f'<div class="tile-stage">{stage_label}</div>'

            html += f"""    <div class="{tile_class}">
      <div class="tile-emoji">{emoji}</div>
      <div class="tile-body">
        <div class="tile-name"><span class="tile-num">{num}.</span> {name}</div>
        {issue_html}
      </div>
    </div>
"""

        html += """  </div>
</div>
"""

    html += f"""
<div class="foot">Generated {datetime.now().strftime('%d %b %Y at %H:%M')} in {run_time:.1f}s</div>

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

    # 7. Load approvals
    approvals = load_approvals()
    if approvals:
        print(f"  {len(approvals)} session(s) approved")

    # 8. Assemble per-session data
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
                               cdn_results, vault_finals, approvals=approvals)

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
