#!/usr/bin/env python3
"""R2 Audio Audit Tool — generates HTML report of all audio assets.

Scans local files, scripts, vault data, HTML references, and CDN status
to produce a comprehensive self-contained HTML report.

Usage:
    python3 tools/r2-audit.py                          # default output
    python3 tools/r2-audit.py -o ~/Desktop/report.html # custom output
    python3 tools/r2-audit.py --skip-cdn               # offline mode
    python3 tools/r2-audit.py --skip-md5               # skip local MD5s
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "content" / "scripts"
AUDIO_DIR = PROJECT_ROOT / "content" / "audio-free"
VAULT_DIR = AUDIO_DIR / "vault"
SOUNDS_DIR = PROJECT_ROOT / "content" / "sounds"
CDN_BASE = "https://media.salus-mind.com/content/audio-free"
SOUNDS_CDN_BASE = "https://media.salus-mind.com/content/sounds"
MAX_CDN_WORKERS = 20
SESSION_RE = re.compile(r"^(\d+)-(.+)$")
ASMR_RE = re.compile(r"^asmr-(.+)\.mp3$")

# Files/dirs to ignore in vault listing
VAULT_IGNORE = {
    "generation-log.json", "inventory.json",
    "validation-sweep-v3.json", "validation-sweep-v5.json",
}

# Session approvals — manually signed-off sessions skip QA/assembly warnings
APPROVALS_FILE = PROJECT_ROOT / "content" / "session-approvals.json"

def load_approvals():
    """Load session-approvals.json. Returns dict of sid -> approval info."""
    if APPROVALS_FILE.exists():
        try:
            return json.loads(APPROVALS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


# ---------------------------------------------------------------------------
# Script parsing (mirrors build-session-v3.py:163-223)
# ---------------------------------------------------------------------------

def parse_script(script_path):
    """Parse script file with metadata header."""
    content = script_path.read_text(errors="replace")
    lines = content.split("\n")

    metadata = {
        "title": script_path.stem,
        "duration": "",
        "duration_target": "",
        "category": "",
        "ambient": None,
        "ambient_db": None,
        "ambient_fade_in": None,
        "ambient_fade_out": None,
        "style": "",
        "api_emotion": "",
    }

    header_lines = []
    content_start = 0

    for i, line in enumerate(lines):
        if line.strip() == "---":
            content_start = i + 1
            break
        header_lines.append(line)
    else:
        # No --- found — treat entire file as having a header-only zone
        # (some CBT scripts omit the separator)
        content_start = 0

    # Title: first non-key-value line
    if header_lines:
        first_line = header_lines[0].strip()
        if first_line and ":" not in first_line:
            metadata["title"] = first_line

    for line in header_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "title":
                metadata["title"] = value
            elif key == "duration":
                metadata["duration"] = value
            elif key == "duration-target":
                metadata["duration_target"] = value
            elif key == "category":
                metadata["category"] = value.lower()
            elif key == "ambient":
                metadata["ambient"] = value.lower() if value.lower() != "none" else None
            elif key == "ambient-db":
                try:
                    metadata["ambient_db"] = float(value)
                except ValueError:
                    pass
            elif key == "ambient-fade-in":
                try:
                    metadata["ambient_fade_in"] = float(value)
                except ValueError:
                    pass
            elif key == "ambient-fade-out":
                try:
                    metadata["ambient_fade_out"] = float(value)
                except ValueError:
                    pass
            elif key == "style":
                metadata["style"] = value
            elif key in ("api-emotion", "api_emotion"):
                metadata["api_emotion"] = value.lower()

    body = "\n".join(lines[content_start:]).strip()
    # Count chunks (separated by ...)
    chunks = [c.strip() for c in re.split(r"\.{3,}", body) if c.strip()]
    metadata["chunk_count"] = len(chunks)

    return metadata


# ---------------------------------------------------------------------------
# Local file discovery
# ---------------------------------------------------------------------------

def discover_local_files():
    """Find all MP3 files in audio-free/ (not vault subdirs)."""
    files = {}
    if not AUDIO_DIR.exists():
        return files
    for f in AUDIO_DIR.iterdir():
        if f.is_file() and f.suffix == ".mp3":
            stat = f.stat()
            files[f.name] = {
                "path": f,
                "size": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            }
    return files


def discover_sounds_files():
    """Find all MP3 files in content/sounds/."""
    files = {}
    if not SOUNDS_DIR.exists():
        return files
    for f in SOUNDS_DIR.iterdir():
        if f.is_file() and f.suffix == ".mp3":
            stat = f.stat()
            files[f.name] = {
                "path": f,
                "size": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            }
    return files


def discover_vault_finals():
    """Find MP3/WAV files in vault/*/final/ directories."""
    finals = {}
    if not VAULT_DIR.exists():
        return finals
    for vdir in VAULT_DIR.iterdir():
        if not vdir.is_dir() or vdir.name in VAULT_IGNORE:
            continue
        final_dir = vdir / "final"
        if final_dir.exists():
            session_files = []
            for f in final_dir.iterdir():
                if f.is_file() and f.suffix in (".mp3", ".wav"):
                    stat = f.stat()
                    session_files.append({
                        "name": f.name,
                        "size": stat.st_size,
                        "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    })
            finals[vdir.name] = session_files
    return finals


# ---------------------------------------------------------------------------
# Vault metadata
# ---------------------------------------------------------------------------

def read_vault_metadata():
    """Read session-manifest.json and build-report.json from each vault."""
    vault_data = {}
    if not VAULT_DIR.exists():
        return vault_data
    for vdir in VAULT_DIR.iterdir():
        if not vdir.is_dir() or vdir.name in VAULT_IGNORE:
            continue
        entry = {"has_manifest": False, "has_build_report": False,
                 "has_picks": False, "has_auto_picks": False, "has_final": False,
                 "vault_candidates": 0}

        # Count total candidate WAVs and track latest modification
        latest_mtime = 0
        for child in vdir.iterdir():
            if child.is_dir() and re.match(r"c\d{2}$", child.name):
                for wav in child.glob("c*_v*.wav"):
                    entry["vault_candidates"] += 1
                    mt = wav.stat().st_mtime
                    if mt > latest_mtime:
                        latest_mtime = mt
        # Also check final/ and manifest
        for check in [vdir / "session-manifest.json",
                      vdir / "picks-auto.json"]:
            if check.exists():
                mt = check.stat().st_mtime
                if mt > latest_mtime:
                    latest_mtime = mt
        final_dir = vdir / "final"
        if final_dir.exists():
            for f in final_dir.iterdir():
                mt = f.stat().st_mtime
                if mt > latest_mtime:
                    latest_mtime = mt
        if latest_mtime:
            entry["last_modified"] = datetime.fromtimestamp(latest_mtime, tz=timezone.utc)

        # Session manifest
        manifest_path = vdir / "session-manifest.json"
        if manifest_path.exists():
            entry["has_manifest"] = True
            try:
                data = json.loads(manifest_path.read_text())
                entry["total_chunks"] = data.get("total_chunks")
                entry["total_candidates"] = data.get("total_candidates")
                entry["status"] = data.get("status", "")
            except (json.JSONDecodeError, OSError):
                pass

        # Picks directory
        picks_dir = vdir / "picks"
        if picks_dir.exists() and any(picks_dir.iterdir()):
            entry["has_picks"] = True
            entry["picks_count"] = sum(1 for f in picks_dir.iterdir()
                                       if f.suffix == ".wav" and "pick" in f.name)

        # Auto picks
        for name in ("picks-auto.json", "picks-auto-v5.json", "picks-auto-v4.json"):
            if (vdir / name).exists():
                entry["has_auto_picks"] = True
                break

        # Final directory + build report
        final_dir = vdir / "final"
        if final_dir.exists():
            entry["has_final"] = True
            for f in final_dir.iterdir():
                if f.name.endswith("-build-report.json"):
                    entry["has_build_report"] = True
                    try:
                        report = json.loads(f.read_text())
                        entry["build_duration_s"] = report.get("duration_seconds")
                        entry["build_duration_m"] = report.get("duration_minutes")
                        entry["qa_passed"] = report.get("qa_passed")
                        entry["qa_summary"] = report.get("qa_summary", {})
                        entry["chunks_assembled"] = report.get("chunks_assembled")
                        entry["build_total_chunks"] = report.get("total_chunks")
                    except (json.JSONDecodeError, OSError):
                        pass
                    break

        # Assembly verdicts (human review of assembled audio)
        verdicts_path = vdir / "assembly-verdicts.json"
        if verdicts_path.exists():
            try:
                vdata = json.loads(verdicts_path.read_text())
                entry["has_assembly_verdicts"] = True
                entry["assembly_verdicts"] = vdata
            except (json.JSONDecodeError, OSError):
                pass

        vault_data[vdir.name] = entry
    return vault_data


# ---------------------------------------------------------------------------
# HTML scanning
# ---------------------------------------------------------------------------

def scan_html_references():
    """Scan all HTML files for media.salus-mind.com references."""
    refs = {}  # filename.mp3 -> [(page, url)]
    url_pattern = re.compile(
        r"""(?:src|data-src|href)\s*[=:]\s*['"]?(https://media\.salus-mind\.com/[^'">\s,}]+\.mp3)"""
    )
    for html_file in PROJECT_ROOT.glob("**/*.html"):
        # Skip vault review pages and node_modules
        rel = html_file.relative_to(PROJECT_ROOT)
        if "vault" in str(rel) or "node_modules" in str(rel):
            continue
        try:
            text = html_file.read_text(errors="replace")
        except OSError:
            continue
        for match in url_pattern.finditer(text):
            url = match.group(1)
            filename = url.rsplit("/", 1)[-1]
            page = str(rel)
            refs.setdefault(filename, []).append((page, url))
    return refs


# ---------------------------------------------------------------------------
# CDN HEAD checks
# ---------------------------------------------------------------------------

def head_check_url(url):
    """HEAD request to CDN, return dict with status, size, last_modified, etag."""
    result = {"url": url, "status": None, "size": None,
              "last_modified": None, "etag": None, "error": None}
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "salus-r2-audit/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result["status"] = resp.status
            result["size"] = int(resp.headers.get("Content-Length", 0)) or None
            result["last_modified"] = resp.headers.get("Last-Modified")
            etag = resp.headers.get("ETag", "")
            # Strip quotes from etag
            result["etag"] = etag.strip('"').strip("'") if etag else None
    except urllib.error.HTTPError as e:
        result["status"] = e.code
    except Exception as e:
        result["error"] = str(e)
    return result


def batch_head_checks(urls):
    """Parallel HEAD checks."""
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_CDN_WORKERS) as pool:
        futures = {pool.submit(head_check_url, url): url for url in urls}
        for future in as_completed(futures):
            res = future.result()
            results[res["url"]] = res
    return results


# ---------------------------------------------------------------------------
# MD5 for local files
# ---------------------------------------------------------------------------

def md5_file(path):
    """Compute MD5 hex digest of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Issue detection
# ---------------------------------------------------------------------------

def detect_issues(session, script_meta, vault_meta, local_files, html_refs,
                  cdn_results, vault_finals, approvals=None):
    """Auto-detect problems for a session. Returns list of (severity, message)."""
    issues = []
    sid = session["id"]
    primary_mp3 = f"{sid}.mp3"
    approved = (approvals or {}).get(sid)

    # If session is approved, skip QA/assembly/duration warnings
    if approved:
        issues.append(("info", f"Approved ({approved.get('date', '?')})"))

    # Ambient configured but no fade-in
    if script_meta:
        amb = script_meta.get("ambient")
        if amb and amb != "none":
            if script_meta.get("ambient_fade_in") is None:
                issues.append(("warn", "No ambient fade-in configured"))
            if script_meta.get("ambient_fade_out") is None:
                issues.append(("info", "No ambient fade-out configured"))
            if script_meta.get("ambient_db") is None:
                issues.append(("info", "No ambient-dB configured"))

    # No HTML reference for a vault-built session
    if vault_meta and vault_meta.get("has_build_report"):
        if primary_mp3 not in html_refs:
            issues.append(("warn", "Vault built but no HTML reference"))

    # HTML references a file that doesn't exist locally
    if primary_mp3 in html_refs:
        if primary_mp3 not in local_files:
            issues.append(("warn", "HTML references file missing locally"))

    # R2 404
    primary_url = f"{CDN_BASE}/{primary_mp3}"
    cdn_res = cdn_results.get(primary_url)
    if cdn_res:
        if cdn_res["status"] == 404:
            if primary_mp3 in html_refs:
                issues.append(("error", "R2 404 — HTML points to missing file"))
            else:
                issues.append(("info", "Not on R2"))
        elif cdn_res["status"] and cdn_res["status"] != 200:
            issues.append(("error", f"R2 HTTP {cdn_res['status']}"))
        elif cdn_res["error"]:
            issues.append(("error", f"R2 check failed: {cdn_res['error']}"))

    # Local != R2 size mismatch
    if cdn_res and cdn_res["status"] == 200 and cdn_res["size"]:
        local = local_files.get(primary_mp3)
        if local and local["size"] != cdn_res["size"]:
            diff_kb = abs(local["size"] - cdn_res["size"]) / 1024
            issues.append(("warn", f"Local/R2 size mismatch ({diff_kb:.0f} KB diff)"))

    # QA failures (skip if approved)
    if not approved and vault_meta and vault_meta.get("has_build_report"):
        if vault_meta.get("qa_passed") is False:
            failed_gates = []
            for gate_num, gate_info in vault_meta.get("qa_summary", {}).items():
                if isinstance(gate_info, dict) and not gate_info.get("passed", True):
                    if not gate_info.get("skipped"):
                        failed_gates.append(gate_info.get("name", f"Gate {gate_num}"))
            if failed_gates:
                issues.append(("warn", f"QA failed: {', '.join(failed_gates)}"))

    # Duration drift (skip if approved)
    if not approved and script_meta and vault_meta and vault_meta.get("build_duration_m"):
        target = None
        if script_meta.get("duration"):
            m = re.search(r"(\d+)", script_meta["duration"])
            if m:
                target = int(m.group(1))
        elif script_meta.get("duration_target"):
            m = re.search(r"(\d+)", str(script_meta["duration_target"]))
            if m:
                target = int(m.group(1))
        if target:
            actual = vault_meta["build_duration_m"]
            drift_pct = abs(actual - target) / target * 100
            if drift_pct > 25:
                issues.append(("warn",
                    f"Duration drift: target {target}m, actual {actual:.1f}m ({drift_pct:.0f}%)"))

    # Stale variants (multiple MP3s in vault final)
    finals = vault_finals.get(sid, [])
    mp3_count = sum(1 for f in finals if f["name"].endswith(".mp3"))
    if mp3_count > 1:
        issues.append(("info", f"{mp3_count} MP3 variants in vault/final"))

    # Has script but no vault at all
    if script_meta and not vault_meta:
        if primary_mp3 not in local_files:
            issues.append(("info", "Script exists, no audio generated"))

    # Assembly verdicts (skip if approved)
    if not approved and vault_meta and vault_meta.get("has_assembly_verdicts"):
        av = vault_meta["assembly_verdicts"]
        ok = av.get("ok", 0)
        fail = av.get("fail", 0)
        total_rev = av.get("reviewed", ok + fail)
        if fail > 0:
            # Collect fail types
            fail_types = {}
            for cid, cdata in av.get("chunks", {}).items():
                if not cdata.get("passed", True):
                    for v in cdata.get("verdict", []):
                        fail_types[v] = fail_types.get(v, 0) + 1
            type_str = ", ".join(f"{cnt} {t}" for t, cnt in
                                sorted(fail_types.items(), key=lambda x: -x[1]))
            issues.append(("warn",
                f"Assembly review: {ok}/{total_rev} pass ({type_str})"))
        else:
            issues.append(("info", f"Assembly review: {ok}/{total_rev} pass"))

    return issues


# ---------------------------------------------------------------------------
# Stage detection
# ---------------------------------------------------------------------------

def detect_stage(sid, vault_meta, local_files, html_refs, cdn_results):
    """Determine pipeline stage: live, vault-built, picked, generated, legacy, outstanding."""
    primary_mp3 = f"{sid}.mp3"
    primary_url = f"{CDN_BASE}/{primary_mp3}"
    cdn_res = cdn_results.get(primary_url)

    on_r2 = cdn_res and cdn_res.get("status") == 200
    in_html = primary_mp3 in html_refs
    has_local = primary_mp3 in local_files

    if in_html and on_r2:
        return "live"
    if vault_meta:
        if vault_meta.get("has_build_report"):
            return "vault-built"
        if vault_meta.get("has_picks"):
            return "picked"
        if vault_meta.get("has_manifest"):
            return "generated"
    if has_local:
        return "legacy"
    return "outstanding"


# ---------------------------------------------------------------------------
# Build session list
# ---------------------------------------------------------------------------

def build_session_list():
    """Collect all known session IDs from scripts, vault dirs, and local files."""
    sessions = {}

    # From scripts
    for f in SCRIPTS_DIR.glob("*.txt"):
        m = SESSION_RE.match(f.stem)
        if m:
            num = int(m.group(1))
            sid = f.stem
            sessions[sid] = {"id": sid, "num": num, "script_path": f}

    # From vault dirs
    if VAULT_DIR.exists():
        for d in VAULT_DIR.iterdir():
            if not d.is_dir() or d.name in VAULT_IGNORE:
                continue
            m = SESSION_RE.match(d.name)
            if m and d.name not in sessions:
                num = int(m.group(1))
                sessions[d.name] = {"id": d.name, "num": num}

    # From local MP3s (not asmr, not raw_, not narrator, not chunk)
    for f in AUDIO_DIR.glob("*.mp3"):
        name = f.stem
        # Skip variants — only consider base names
        if name.startswith(("asmr-", "raw_", "narrator-", "chunk-", "c0", "ss0")):
            continue
        # Strip known suffixes to find base
        base = re.sub(r"-(repair-\d+|v\d+|noambient|mixed|vault|voice-only)$", "", name)
        m = SESSION_RE.match(base)
        if m and base not in sessions:
            num = int(m.group(1))
            sessions[base] = {"id": base, "num": num}

    return sessions


def build_asmr_list(local_files):
    """Collect ASMR tracks from local files."""
    asmr = []
    for name, info in local_files.items():
        m = ASMR_RE.match(name)
        if m:
            asmr.append({
                "name": m.group(1),
                "filename": name,
                "size": info["size"],
                "mtime": info["mtime"],
            })
    asmr.sort(key=lambda x: x["name"])
    return asmr


# ---------------------------------------------------------------------------
# HTML report generation
# ---------------------------------------------------------------------------

def fmt_size(size_bytes):
    """Format bytes as human-readable."""
    if size_bytes is None:
        return "—"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def fmt_date(dt):
    """Format datetime as short date."""
    if dt is None:
        return "—"
    return dt.strftime("%d %b %y")


def severity_class(sev):
    return {"error": "cell-error", "warn": "cell-warn", "info": "cell-info"}.get(sev, "")


def stage_class(stage):
    return {
        "live": "stage-live", "vault-built": "stage-built",
        "picked": "stage-picked", "generated": "stage-generated",
        "legacy": "stage-legacy", "outstanding": "stage-outstanding",
    }.get(stage, "")


def generate_html(sessions_data, asmr_data, sounds_data, cdn_results, run_time, skip_cdn):
    """Generate self-contained HTML report."""

    # Summary stats
    total = len(sessions_data)
    stages = {}
    issue_counts = {"error": 0, "warn": 0, "info": 0}
    flag_counts = {"green": 0, "amber": 0, "red": 0}
    for s in sessions_data:
        st = s.get("stage", "outstanding")
        stages[st] = stages.get(st, 0) + 1
        issues = s.get("issues", [])
        has_error = any(sv == "error" for sv, _ in issues)
        has_warn = any(sv == "warn" for sv, _ in issues)
        if has_error or (st == "legacy" and has_warn):
            flag_counts["red"] += 1
        elif has_warn or st in ("picked", "generated", "legacy", "vault-built"):
            flag_counts["amber"] += 1
        else:
            flag_counts["green"] += 1
        for sev, _ in issues:
            issue_counts[sev] = issue_counts.get(sev, 0) + 1

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>R2 Audio Audit — {datetime.now().strftime('%d %b %Y %H:%M')}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#FFF1E5; color:#33302E; font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; font-size:13px; padding:20px; }}
h1 {{ color:#1A1817; font-size:22px; font-weight:700; margin-bottom:4px; }}
.subtitle {{ color:#807973; font-size:13px; margin-bottom:20px; }}
.summary {{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:24px; }}
.stat {{ background:#F2DFCE; border:1px solid #E0CDBF; border-radius:4px; padding:12px 18px; min-width:120px; }}
.stat-num {{ font-size:28px; font-weight:700; color:#1A1817; }}
.stat-label {{ font-size:11px; color:#807973; text-transform:uppercase; letter-spacing:0.5px; margin-top:2px; }}
.stat-live .stat-num {{ color:#0D7680; }}
.stat-error .stat-num {{ color:#CC0000; }}
.stat-warn .stat-num {{ color:#A64D00; }}
.controls {{ display:flex; gap:12px; align-items:center; margin-bottom:16px; flex-wrap:wrap; }}
.controls select, .controls input {{ background:#FFF7F0; border:1px solid #E0CDBF; color:#33302E; padding:6px 10px; border-radius:4px; font-size:13px; }}
.controls input {{ width:220px; }}
table {{ width:100%; border-collapse:collapse; margin-bottom:32px; border:1px solid #E0CDBF; }}
#mainTable {{ table-layout:fixed; }}
#mainTable colgroup {{ display:table-column-group; }}
td {{ padding:6px 8px; border:1px solid #E0CDBF; vertical-align:middle; font-size:12px; overflow:hidden; text-overflow:ellipsis; }}
th {{ background:#F2DFCE; color:#807973; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; padding:8px; text-align:left; border:1px solid #E0CDBF; cursor:pointer; user-select:none; white-space:nowrap; }}
th:hover {{ color:#1A1817; }}
th .arrow {{ font-size:10px; margin-left:4px; }}
tr:hover {{ background:#FFF7F0; }}
tr:nth-child(even) {{ background:#FFF9F2; }}
.cell-error {{ color:#CC0000; font-weight:600; }}
.cell-warn {{ color:#A64D00; }}
.cell-info {{ color:#998F85; }}
.cell-ok {{ color:#0D7680; }}
.stage-live {{ background:#D4EDDA; color:#1B5E20; padding:2px 8px; border-radius:3px; font-size:11px; font-weight:600; }}
.stage-built {{ background:#D6E9F8; color:#1A4971; padding:2px 8px; border-radius:3px; font-size:11px; }}
.stage-picked {{ background:#FFF3CD; color:#856404; padding:2px 8px; border-radius:3px; font-size:11px; }}
.stage-generated {{ background:#E8DEF8; color:#4A148C; padding:2px 8px; border-radius:3px; font-size:11px; }}
.stage-legacy {{ background:#F8D7DA; color:#842029; padding:2px 8px; border-radius:3px; font-size:11px; }}
.stage-outstanding {{ background:#E8E5E3; color:#807973; padding:2px 8px; border-radius:3px; font-size:11px; }}
.r2-200 {{ color:#0D7680; }}
.r2-404 {{ color:#CC0000; }}
.issue-list {{ list-style:none; display:flex; flex-wrap:wrap; gap:2px 10px; }}
.issue-list li {{ white-space:nowrap; font-size:11px; }}
.issue-list li::before {{ content:''; display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:4px; vertical-align:middle; }}
.issue-error::before {{ background:#CC0000; }}
.issue-warn::before {{ background:#A64D00; }}
.issue-info::before {{ background:#998F85; }}
.files-list {{ font-size:11px; color:#807973; }}
.files-list span {{ display:inline; white-space:nowrap; }}
.files-list span+span::before {{ content:', '; }}
h2 {{ color:#1A1817; font-size:16px; font-weight:700; margin:28px 0 12px; }}
.section-sep {{ border:none; border-top:1px solid #E0CDBF; margin:32px 0; }}
.match {{ color:#0D7680; }}
.mismatch {{ color:#CC0000; }}
.skipped {{ color:#998F85; font-style:italic; }}
.flag {{ display:inline-block; width:10px; height:10px; border-radius:50%; }}
.flag-green {{ background:#1B5E20; }}
.flag-amber {{ background:#A64D00; }}
.flag-red {{ background:#CC0000; }}
</style>
</head>
<body>
<h1>R2 Audio Audit Report</h1>
<div class="subtitle">Generated {datetime.now().strftime('%d %b %Y at %H:%M')} &middot; {run_time:.1f}s &middot; {total} sessions{' &middot; CDN checks skipped' if skip_cdn else ''}</div>

<div class="summary">
  <div class="stat stat-live"><div class="stat-num">{stages.get('live', 0)}</div><div class="stat-label">Live</div></div>
  <div class="stat"><div class="stat-num">{stages.get('vault-built', 0)}</div><div class="stat-label">Vault Built</div></div>
  <div class="stat"><div class="stat-num">{stages.get('picked', 0)}</div><div class="stat-label">Picked</div></div>
  <div class="stat"><div class="stat-num">{stages.get('generated', 0)}</div><div class="stat-label">Generated</div></div>
  <div class="stat"><div class="stat-num">{stages.get('legacy', 0)}</div><div class="stat-label">Legacy</div></div>
  <div class="stat"><div class="stat-num">{stages.get('outstanding', 0)}</div><div class="stat-label">Outstanding</div></div>
  <div class="stat stat-error"><div class="stat-num">{issue_counts['error']}</div><div class="stat-label">Errors</div></div>
  <div class="stat stat-warn"><div class="stat-num">{issue_counts['warn']}</div><div class="stat-label">Warnings</div></div>
  <div class="stat"><div class="stat-num" style="color:#1B5E20">{flag_counts['green']}</div><div class="stat-label"><span class="flag flag-green"></span> No Action</div></div>
  <div class="stat"><div class="stat-num" style="color:#A64D00">{flag_counts['amber']}</div><div class="stat-label"><span class="flag flag-amber"></span> Needs Work</div></div>
  <div class="stat"><div class="stat-num" style="color:#CC0000">{flag_counts['red']}</div><div class="stat-label"><span class="flag flag-red"></span> Action Req</div></div>
</div>

<div class="controls">
  <select id="stageFilter" onchange="filterTable()">
    <option value="">All Stages</option>
    <option value="live">Live</option>
    <option value="vault-built">Vault Built</option>
    <option value="picked">Picked</option>
    <option value="generated">Generated</option>
    <option value="legacy">Legacy</option>
    <option value="outstanding">Outstanding</option>
  </select>
  <select id="catFilter" onchange="filterTable()">
    <option value="">All Categories</option>
    <option value="mindfulness">Mindfulness</option>
    <option value="stress">Stress</option>
    <option value="sleep">Sleep</option>
  </select>
  <select id="issueFilter" onchange="filterTable()">
    <option value="">All Issues</option>
    <option value="has-error">Has Errors</option>
    <option value="has-warn">Has Warnings</option>
    <option value="has-issues">Has Any Issues</option>
    <option value="no-issues">No Issues</option>
  </select>
  <select id="flagFilter" onchange="filterTable()">
    <option value="">All Flags</option>
    <option value="red">Red</option>
    <option value="amber">Amber</option>
    <option value="green">Green</option>
  </select>
  <input type="text" id="searchBox" placeholder="Search name or ID..." oninput="filterTable()">
</div>

<table id="mainTable">
<colgroup>
  <col style="width:20px">
  <col style="width:36px">
  <col style="width:150px">
  <col style="width:80px">
  <col style="width:50px">
  <col style="width:50px">
  <col style="width:70px">
  <col style="width:110px">
  <col style="width:90px">
  <col style="width:90px">
  <col style="width:140px">
  <col style="width:120px">
  <col style="width:80px">
  <col style="width:70px">
  <col style="width:44px">
  <col style="width:72px">
  <col>
</colgroup>
<thead>
<tr>
  <th data-col="0" onclick="sortTable(0,'str')"><span class="arrow"></span></th>
  <th data-col="1" onclick="sortTable(1,'num')"># <span class="arrow"></span></th>
  <th data-col="2" onclick="sortTable(2,'str')">Name <span class="arrow"></span></th>
  <th data-col="3" onclick="sortTable(3,'str')">Category <span class="arrow"></span></th>
  <th data-col="4" onclick="sortTable(4,'num')">Chunks <span class="arrow"></span></th>
  <th data-col="5" onclick="sortTable(5,'num')">In Vault <span class="arrow"></span></th>
  <th data-col="6" onclick="sortTable(6,'str')">Last Edit <span class="arrow"></span></th>
  <th data-col="7" onclick="sortTable(7,'str')">Duration <span class="arrow"></span></th>
  <th data-col="8" onclick="sortTable(8,'str')">Ambient <span class="arrow"></span></th>
  <th data-col="9" onclick="sortTable(9,'str')">Fades <span class="arrow"></span></th>
  <th data-col="10" onclick="sortTable(10,'str')">Local Files <span class="arrow"></span></th>
  <th data-col="11" onclick="sortTable(11,'str')">R2 URL <span class="arrow"></span></th>
  <th data-col="12" onclick="sortTable(12,'str')">R2 Status <span class="arrow"></span></th>
  <th data-col="13" onclick="sortTable(13,'str')">Local=R2? <span class="arrow"></span></th>
  <th data-col="14" onclick="sortTable(14,'str')">QA <span class="arrow"></span></th>
  <th data-col="15" onclick="sortTable(15,'str')">Stage <span class="arrow"></span></th>
  <th data-col="16" onclick="sortTable(16,'str')">Issues <span class="arrow"></span></th>
</tr>
</thead>
<tbody>
"""

    for s in sessions_data:
        sid = s["id"]
        num = s["num"]
        sm = s.get("script_meta") or {}
        vm = s.get("vault_meta") or {}
        stage = s.get("stage", "outstanding")
        issues = s.get("issues", [])
        primary_mp3 = f"{sid}.mp3"
        primary_url = f"{CDN_BASE}/{primary_mp3}"
        cdn_res = cdn_results.get(primary_url, {})

        # Name
        name = sm.get("title", sid)

        # Category
        cat = sm.get("category", "")

        # Chunks required (from script), candidates in vault, last edit
        chunks_required = sm.get("chunk_count") if sm else None
        vault_candidates = vm.get("vault_candidates", 0) if vm else 0
        last_edit = fmt_date(vm.get("last_modified")) if vm and vm.get("last_modified") else "—"

        # Duration
        dur_target = sm.get("duration") or sm.get("duration_target") or "—"
        dur_actual = ""
        if vm.get("build_duration_m"):
            dur_actual = f" / {vm['build_duration_m']:.1f}m actual"
        dur_str = f"{dur_target}{dur_actual}"

        # Ambient
        amb = sm.get("ambient") or "—"
        amb_db = sm.get("ambient_db")
        if amb != "—" and amb_db is not None:
            amb = f"{amb} ({amb_db}dB)"

        # Fades
        fade_in = sm.get("ambient_fade_in")
        fade_out = sm.get("ambient_fade_out")
        if sm.get("ambient") and sm["ambient"] != "none":
            parts = []
            if fade_in is not None:
                parts.append(f"in:{fade_in}s")
            else:
                parts.append('<span class="cell-warn">in:none</span>')
            if fade_out is not None:
                parts.append(f"out:{fade_out}s")
            else:
                parts.append('<span class="cell-info">out:none</span>')
            fades = " ".join(parts)
        else:
            fades = "—"

        # Local files — find all variants for this session
        local_variants = []
        for fname, finfo in s.get("local_files", {}).items():
            local_variants.append(f"<span>{fname} ({fmt_size(finfo['size'])})</span>")
        local_html = '<div class="files-list">' + "".join(local_variants) + "</div>" if local_variants else '<span class="cell-info">none</span>'

        # R2 URL column — what HTML references
        html_refs = s.get("html_refs", {})
        if primary_mp3 in html_refs:
            pages = [p for p, _ in html_refs[primary_mp3]]
            r2_url_html = f'<span style="font-size:11px">{", ".join(pages)}</span>'
        else:
            r2_url_html = '<span class="cell-info">not referenced</span>'

        # R2 Status
        if skip_cdn:
            r2_status_html = '<span class="skipped">skipped</span>'
        elif cdn_res.get("status") == 200:
            size_str = fmt_size(cdn_res.get("size"))
            r2_status_html = f'<span class="r2-200">200</span> ({size_str})'
        elif cdn_res.get("status") == 404:
            r2_status_html = '<span class="r2-404">404</span>'
        elif cdn_res.get("status"):
            r2_status_html = f'<span class="cell-warn">{cdn_res["status"]}</span>'
        elif cdn_res.get("error"):
            r2_status_html = f'<span class="cell-error">err</span>'
        else:
            r2_status_html = '<span class="cell-info">—</span>'

        # Local=R2 match
        if skip_cdn:
            match_html = '<span class="skipped">—</span>'
        elif cdn_res.get("status") == 200 and cdn_res.get("size"):
            local_info = s.get("local_files", {}).get(primary_mp3)
            if local_info and local_info["size"] == cdn_res["size"]:
                match_html = '<span class="match">match</span>'
            elif local_info:
                match_html = '<span class="mismatch">MISMATCH</span>'
            else:
                match_html = '<span class="cell-info">no local</span>'
        else:
            match_html = '<span class="cell-info">—</span>'

        # QA
        if vm.get("has_build_report"):
            if vm.get("qa_passed"):
                qa_html = '<span class="cell-ok">PASS</span>'
            elif vm.get("qa_passed") is False:
                qa_html = '<span class="cell-warn">FAIL</span>'
            else:
                qa_html = '<span class="cell-info">—</span>'
        else:
            qa_html = '<span class="cell-info">—</span>'

        # Stage
        stage_html = f'<span class="{stage_class(stage)}">{stage}</span>'

        # Issues
        if issues:
            items = ""
            for sev, msg in issues:
                items += f'<li class="issue-{sev}">{msg}</li>'
            issues_html = f'<ul class="issue-list">{items}</ul>'
        else:
            issues_html = '<span class="cell-ok">none</span>'

        # Issue severity for filtering
        has_error = any(s == "error" for s, _ in issues)
        has_warn = any(s == "warn" for s, _ in issues)
        has_issues = len(issues) > 0
        issue_attr = "error" if has_error else ("warn" if has_warn else ("info" if has_issues else "none"))

        # Traffic light flag
        if has_error or (stage == "legacy" and has_warn):
            flag = "red"
        elif has_warn or stage in ("picked", "generated", "legacy", "vault-built"):
            flag = "amber"
        else:
            flag = "green"

        html += f"""<tr data-stage="{stage}" data-cat="{cat}" data-issues="{issue_attr}" data-flag="{flag}" data-search="{num} {name.lower()} {sid.lower()} {cat}">
  <td style="text-align:center"><span class="flag flag-{flag}"></span></td>
  <td>{num}</td>
  <td>{name}</td>
  <td>{cat or '—'}</td>
  <td style="text-align:right">{chunks_required or '—'}</td>
  <td style="text-align:right">{vault_candidates or '—'}</td>
  <td>{last_edit}</td>
  <td>{dur_str}</td>
  <td>{amb}</td>
  <td>{fades}</td>
  <td>{local_html}</td>
  <td>{r2_url_html}</td>
  <td>{r2_status_html}</td>
  <td>{match_html}</td>
  <td>{qa_html}</td>
  <td>{stage_html}</td>
  <td>{issues_html}</td>
</tr>
"""

    html += """</tbody>
</table>
"""

    # Assembly Reviews section — chunk-level verdicts from human review
    review_sessions = [s for s in sessions_data
                       if (s.get("vault_meta") or {}).get("has_assembly_verdicts")]
    if review_sessions:
        html += """<hr class="section-sep">
<h2>Assembly Reviews</h2>
"""
        for s in review_sessions:
            av = s["vault_meta"]["assembly_verdicts"]
            sid = s["id"]
            ok = av.get("ok", 0)
            fail = av.get("fail", 0)
            total_rev = av.get("reviewed", ok + fail)
            pct = (ok / total_rev * 100) if total_rev else 0
            date = av.get("date", "—")
            notes = av.get("notes", "")
            run = av.get("run", "")

            html += f"""<h3 style="margin:16px 0 4px;font-size:14px">{sid} <span style="font-weight:400;color:#807973">— {date} — {run}</span></h3>
<div style="font-size:12px;color:#807973;margin-bottom:8px">{notes} &middot; <strong>{ok}/{total_rev} pass ({pct:.0f}%)</strong></div>
<table style="max-width:900px">
<thead>
<tr>
  <th style="width:50px">Chunk</th>
  <th style="width:50px">Ver</th>
  <th style="width:60px">Time</th>
  <th style="width:60px">Result</th>
  <th style="width:120px">Issue</th>
  <th>Comment</th>
</tr>
</thead>
<tbody>
"""
            chunks = av.get("chunks", {})
            for cid in sorted(chunks.keys(), key=lambda x: int(x)):
                cdata = chunks[cid]
                passed = cdata.get("passed", True)
                ver = cdata.get("version", "—")
                ts = cdata.get("timestamp", "")
                verdict = cdata.get("verdict", [])
                comment = cdata.get("comment", "")

                if passed:
                    result_html = '<span class="cell-ok">PASS</span>'
                    verdict_html = ""
                    comment_html = ""
                else:
                    result_html = '<span class="cell-error">FAIL</span>'
                    verdict_tags = " ".join(
                        f'<span class="cell-{"error" if v in ("VOICE","CUTOFF","BAD") else "warn"}">{v}</span>'
                        for v in verdict)
                    verdict_html = verdict_tags
                    comment_html = f'<span style="color:#33302E">{comment}</span>'

                html += f"""<tr{"" if not passed else ' style="opacity:0.5"'}>
  <td>c{int(cid):02d}</td>
  <td>{ver if ver != "—" else "—"}</td>
  <td>{ts or "—"}</td>
  <td>{result_html}</td>
  <td>{verdict_html}</td>
  <td>{comment_html}</td>
</tr>
"""
            html += """</tbody>
</table>
"""

    # ASMR section
    html += """<hr class="section-sep">
<h2>ASMR / Ambient Tracks</h2>
<table id="asmrTable">
<thead>
<tr>
  <th>Name</th>
  <th>Filename</th>
  <th>Local Size</th>
  <th>Local Date</th>
  <th>R2 Status</th>
  <th>Local=R2?</th>
</tr>
</thead>
<tbody>
"""
    for a in asmr_data:
        url = f"{CDN_BASE}/{a['filename']}"
        cdn_res = cdn_results.get(url, {})
        if skip_cdn:
            r2_html = '<span class="skipped">skipped</span>'
            match_html = '<span class="skipped">—</span>'
        elif cdn_res.get("status") == 200:
            r2_html = f'<span class="r2-200">200</span> ({fmt_size(cdn_res.get("size"))})'
            if cdn_res.get("size") and a["size"] == cdn_res["size"]:
                match_html = '<span class="match">match</span>'
            elif cdn_res.get("size"):
                match_html = '<span class="mismatch">MISMATCH</span>'
            else:
                match_html = '<span class="cell-info">—</span>'
        elif cdn_res.get("status") == 404:
            r2_html = '<span class="r2-404">404</span>'
            match_html = '<span class="cell-info">—</span>'
        else:
            r2_html = '<span class="cell-info">—</span>'
            match_html = '<span class="cell-info">—</span>'

        html += f"""<tr>
  <td>{a['name']}</td>
  <td>{a['filename']}</td>
  <td>{fmt_size(a['size'])}</td>
  <td>{fmt_date(a['mtime'])}</td>
  <td>{r2_html}</td>
  <td>{match_html}</td>
</tr>
"""

    html += """</tbody>
</table>
"""

    # Sounds section
    if sounds_data:
        html += """<hr class="section-sep">
<h2>Sounds (content/sounds/)</h2>
<table>
<thead>
<tr>
  <th>Filename</th>
  <th>Local Size</th>
  <th>Local Date</th>
  <th>R2 Status</th>
</tr>
</thead>
<tbody>
"""
        for fname in sorted(sounds_data.keys()):
            info = sounds_data[fname]
            url = f"{SOUNDS_CDN_BASE}/{fname}"
            cdn_res = cdn_results.get(url, {})
            if skip_cdn:
                r2_html = '<span class="skipped">skipped</span>'
            elif cdn_res.get("status") == 200:
                r2_html = f'<span class="r2-200">200</span> ({fmt_size(cdn_res.get("size"))})'
            elif cdn_res.get("status") == 404:
                r2_html = '<span class="r2-404">404</span>'
            else:
                r2_html = '<span class="cell-info">—</span>'

            html += f"""<tr>
  <td>{fname}</td>
  <td>{fmt_size(info['size'])}</td>
  <td>{fmt_date(info['mtime'])}</td>
  <td>{r2_html}</td>
</tr>
"""
        html += """</tbody></table>
"""

    # JavaScript for sorting and filtering
    html += """
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

  // Update arrows
  table.querySelectorAll('th .arrow').forEach(a => a.textContent = '');
  const th = table.querySelector(`th[data-col="${col}"] .arrow`);
  if (th) th.textContent = sortAsc ? ' \\u25B2' : ' \\u25BC';
}

function filterTable() {
  const stage = document.getElementById('stageFilter').value;
  const cat = document.getElementById('catFilter').value;
  const issue = document.getElementById('issueFilter').value;
  const flag = document.getElementById('flagFilter').value;
  const search = document.getElementById('searchBox').value.toLowerCase();
  const rows = document.querySelectorAll('#mainTable tbody tr');

  rows.forEach(row => {
    let show = true;
    if (stage && row.dataset.stage !== stage) show = false;
    if (cat && row.dataset.cat !== cat) show = false;
    if (flag && row.dataset.flag !== flag) show = false;
    if (issue) {
      const ri = row.dataset.issues;
      if (issue === 'has-error' && ri !== 'error') show = false;
      if (issue === 'has-warn' && ri !== 'warn' && ri !== 'error') show = false;
      if (issue === 'has-issues' && ri === 'none') show = false;
      if (issue === 'no-issues' && ri !== 'none') show = false;
    }
    if (search && !row.dataset.search.includes(search)) show = false;
    row.style.display = show ? '' : 'none';
  });
}
</script>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="R2 Audio Audit — generate HTML report")
    parser.add_argument("-o", "--output", default="r2-audit-report.html",
                        help="Output HTML file path")
    parser.add_argument("--skip-cdn", action="store_true",
                        help="Skip CDN HEAD checks (offline mode)")
    parser.add_argument("--skip-md5", action="store_true",
                        help="Skip local MD5 hashing")
    args = parser.parse_args()

    start = datetime.now()
    print("R2 Audio Audit")
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
    print(f"  {len(local_files)} audio-free MP3s, {len(sounds_files)} sounds, {len(vault_finals)} vault finals")

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
    print(f"  {len(sessions)} total sessions identified")

    # 6. Build ASMR list
    asmr_list = build_asmr_list(local_files)
    print(f"  {len(asmr_list)} ASMR tracks")

    # 7. Collect all URLs to check
    urls_to_check = set()
    if not args.skip_cdn:
        # Primary URL for every session
        for sid in sessions:
            urls_to_check.add(f"{CDN_BASE}/{sid}.mp3")
        # Every URL referenced in HTML
        for fname, refs in html_refs.items():
            for _, url in refs:
                urls_to_check.add(url)
        # ASMR tracks
        for a in asmr_list:
            urls_to_check.add(f"{CDN_BASE}/{a['filename']}")
        # Sounds
        for fname in sounds_files:
            urls_to_check.add(f"{SOUNDS_CDN_BASE}/{fname}")

        print(f"HEAD-checking {len(urls_to_check)} URLs...")
        cdn_results = batch_head_checks(urls_to_check)
        ok_count = sum(1 for r in cdn_results.values() if r.get("status") == 200)
        not_found = sum(1 for r in cdn_results.values() if r.get("status") == 404)
        print(f"  {ok_count} OK, {not_found} 404, {len(cdn_results) - ok_count - not_found} other")
    else:
        cdn_results = {}
        print("  CDN checks skipped")

    # 8. Load approvals
    approvals = load_approvals()
    if approvals:
        print(f"  {len(approvals)} session(s) approved")

    # 9. Assemble per-session data
    print("Assembling report data...")
    sessions_data = []
    for sid, sinfo in sorted(sessions.items(), key=lambda x: x[1]["num"]):
        sm = scripts.get(sid)
        vm = vault_meta.get(sid)

        # Collect local file variants for this session
        session_local = {}
        for fname, finfo in local_files.items():
            base = fname.rsplit(".", 1)[0]
            # Match if it's the primary file or a variant (e.g. -repair-1, -v2, etc.)
            if base == sid or base.startswith(sid + "-"):
                session_local[fname] = finfo
            # Also match raw_ prefixed
            elif base == f"raw_{sid}":
                session_local[fname] = finfo

        # Collect HTML refs for this session
        session_refs = {}
        for fname, refs in html_refs.items():
            base = fname.rsplit(".", 1)[0]
            if base == sid or base.startswith(sid + "-"):
                session_refs[fname] = refs

        stage = detect_stage(sid, vm, local_files, html_refs, cdn_results)
        issues = detect_issues(
            sinfo, sm, vm, local_files, session_refs,
            cdn_results, vault_finals, approvals=approvals,
        )

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

    # 9. Generate HTML
    print("Generating HTML report...")
    html = generate_html(sessions_data, asmr_list, sounds_files,
                         cdn_results, run_time, args.skip_cdn)

    output_path = Path(args.output).expanduser()
    output_path.write_text(html)
    print(f"\nReport written to: {output_path}")
    print(f"Total time: {run_time:.1f}s")


if __name__ == "__main__":
    main()
