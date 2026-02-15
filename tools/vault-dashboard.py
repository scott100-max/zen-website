#!/usr/bin/env python3
"""
Vault Dashboard — Interactive HTML showing pool depth for all vault silos.

Scans all vault directories and generates a JS-rendered HTML page with:
- Bar charts showing pool depth per chunk
- Category tabs, search, sort, show/hide completed
- Click-to-prioritise with drag-to-reorder
- Chunk detail modal (text, scores, candidate counts)
- Topup ETA when vault-topup.py is running
- Per-category summary with progress bars

Usage:
    python3 tools/vault-dashboard.py                # Generate + open
    python3 tools/vault-dashboard.py --target 35    # Custom target
    python3 tools/vault-dashboard.py --no-open      # Generate only
    python3 tools/vault-dashboard.py --no-meta       # Skip chunk meta (faster)
    python3 tools/vault-dashboard.py --no-scan-duration  # Skip ffprobe (faster)
    python3 tools/vault-dashboard.py --prioritise "s1,s2,s3"  # Set priority directly
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
VAULT_DIR = BASE_DIR / "content" / "audio-free" / "vault"
AUDIO_DIR = BASE_DIR / "content" / "audio-free"
REGISTRY_PATH = BASE_DIR / "content" / "session-registry.json"
OUTPUT_PATH = BASE_DIR / "tools" / "vault-dashboard.html"
PRIORITY_FILE = BASE_DIR / "vault-topup-priority.json"
TOPUP_STATE_FILE = BASE_DIR / "vault-topup-state.json"
DESKTOP_COPY = Path.home() / "Desktop" / "salus Docs" / "vault-dashboard.html"

SKIP_DIRS = {"generation-log.json", "inventory.json", "validation-sweep-v3.json"}

CATEGORY_COLORS = {
    "mindfulness": "#4ade80",
    "7day": "#38bdf8",
    "21day": "#34d399",
    "cbt": "#f59e0b",
    "sleep-story": "#a78bfa",
    "homepage": "#e879f9",
}


def get_mp3_duration(session_name):
    """Get duration of deployed MP3 via ffprobe. Returns formatted string or None."""
    mp3_path = AUDIO_DIR / f"{session_name}.mp3"
    if not mp3_path.exists():
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(mp3_path)],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            secs = float(result.stdout.strip())
            mins = int(secs // 60)
            remaining = int(secs % 60)
            return f"{mins}m {remaining:02d}s"
    except Exception:
        pass
    return None


def read_chunk_meta(chunk_dir, chunk_idx):
    """Read c*_meta.json for a chunk. Returns enriched dict or None."""
    meta_file = chunk_dir / f"c{chunk_idx:02d}_meta.json"
    if not meta_file.exists():
        return None
    try:
        data = json.loads(meta_file.read_text())
        candidates = data.get("candidates", [])
        passing = [c for c in candidates if not c.get("filtered", False)]
        scores = [c.get("composite_score", 0) for c in passing if c.get("composite_score")]

        return {
            "text": (data.get("text", "")[:120] + "...") if len(data.get("text", "")) > 120 else data.get("text", ""),
            "full_text": data.get("text", ""),
            "char_count": data.get("char_count", 0),
            "total_candidates": len(candidates),
            "passing": len(passing),
            "avg_score": round(sum(scores) / len(scores), 3) if scores else 0,
            "best_score": round(max(scores), 3) if scores else 0,
        }
    except Exception:
        return None


def scan_vaults(target, scan_meta=True, scan_duration=True):
    """Scan all vault directories and return enriched session data."""
    sessions = []

    registry = {}
    if REGISTRY_PATH.exists():
        reg = json.loads(REGISTRY_PATH.read_text())
        registry = reg.get("sessions", reg)

    # Load topup state
    topup_completed = []
    if TOPUP_STATE_FILE.exists():
        try:
            ts = json.loads(TOPUP_STATE_FILE.read_text())
            topup_completed = ts.get("completed", [])
        except Exception:
            pass

    for d in sorted(VAULT_DIR.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        if name in SKIP_DIRS or name.endswith("-backup") or name.endswith("-pre-fix"):
            continue

        chunk_dirs = sorted(d.glob("c[0-9][0-9]"))
        if not chunk_dirs:
            continue

        chunks = []
        for cd in chunk_dirs:
            idx = int(cd.name[1:])
            wavs = len(list(cd.glob("c*_v*.wav")))

            chunk_data = {"idx": idx, "count": wavs}

            if scan_meta:
                meta = read_chunk_meta(cd, idx)
                if meta:
                    chunk_data.update(meta)

            chunks.append(chunk_data)

        counts = [c["count"] for c in chunks]
        total_wavs = sum(counts)
        avg = total_wavs / len(counts) if counts else 0
        mn = min(counts) if counts else 0
        mx = max(counts) if counts else 0
        at_target = all(c >= target for c in counts)
        wavs_needed = sum(max(0, target - c["count"]) for c in chunks)

        has_human_picks = (d / "live-picks.json").exists()
        has_auto_picks = (d / "auto-pick-log.json").exists()

        reg_entry = registry.get(name, {}) if isinstance(registry.get(name), dict) else {}
        category = reg_entry.get("category", "")
        ambient = reg_entry.get("ambient", "")
        status = reg_entry.get("status", "")

        duration = None
        if scan_duration:
            duration = get_mp3_duration(name)

        sessions.append({
            "name": name,
            "chunks": chunks,
            "num_chunks": len(chunks),
            "total_wavs": total_wavs,
            "avg": round(avg, 1),
            "min": mn,
            "max": mx,
            "at_target": at_target,
            "wavs_needed": wavs_needed,
            "has_human_picks": has_human_picks,
            "has_auto_picks": has_auto_picks,
            "category": category,
            "ambient": ambient,
            "status": status,
            "duration": duration,
            "topup_done": name in topup_completed,
        })

    return sessions


def check_topup_running():
    """Check if vault-topup.py is currently running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "vault-topup"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def load_current_priority():
    """Load current priority file if it exists."""
    if PRIORITY_FILE.exists():
        try:
            data = json.loads(PRIORITY_FILE.read_text())
            return data if isinstance(data, list) else data.get("order", [])
        except Exception:
            pass
    return []


def compute_category_stats(sessions, target):
    """Compute per-category aggregate stats."""
    cats = {}
    for s in sessions:
        cat = s["category"] or "uncategorised"
        if cat not in cats:
            cats[cat] = {"total": 0, "at_target": 0, "wavs": 0, "chunks": 0, "wavs_needed": 0, "deployed": 0}
        cats[cat]["total"] += 1
        cats[cat]["at_target"] += 1 if s["at_target"] else 0
        cats[cat]["wavs"] += s["total_wavs"]
        cats[cat]["chunks"] += s["num_chunks"]
        cats[cat]["wavs_needed"] += s["wavs_needed"]
        cats[cat]["deployed"] += 1 if s["status"] == "deployed" else 0
    return cats


def generate_html(sessions, target):
    """Generate the dashboard HTML with embedded JSON + JS rendering."""
    now = datetime.now().strftime("%d %b %Y %H:%M")
    topup_running = check_topup_running()
    current_priority = load_current_priority()

    total_sessions = len(sessions)
    sessions_at_target = sum(1 for s in sessions if s["at_target"])
    total_wavs = sum(s["total_wavs"] for s in sessions)
    total_chunks = sum(s["num_chunks"] for s in sessions)
    human_picked = sum(1 for s in sessions if s["has_human_picks"])
    deployed = sum(1 for s in sessions if s["status"] == "deployed")
    total_wavs_needed = sum(s["wavs_needed"] for s in sessions)

    category_stats = compute_category_stats(sessions, target)

    # ETA: ~7.5s per WAV generation
    eta_hours = None
    if topup_running and total_wavs_needed > 0:
        eta_hours = round(total_wavs_needed * 7.5 / 3600, 1)

    # Serialise session data for JS
    sessions_json = json.dumps(sessions, default=str)
    priority_json = json.dumps(current_priority)
    category_stats_json = json.dumps(category_stats)
    category_colors_json = json.dumps(CATEGORY_COLORS)
    priority_file_path = str(PRIORITY_FILE)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vault Dashboard</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
        background: #0a0a0f;
        color: #e0e0e0;
        padding: 24px;
        padding-bottom: 120px;
        min-height: 100vh;
    }}

    /* Header */
    .header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 24px;
        flex-wrap: wrap;
        gap: 16px;
    }}
    .header h1 {{ font-size: 24px; font-weight: 600; color: #fff; letter-spacing: -0.5px; }}
    .header .subtitle {{ font-size: 13px; color: #888; margin-top: 4px; }}
    .header-right {{ display: flex; gap: 10px; align-items: center; }}
    .topup-badge {{
        background: #22c55e; color: #000; padding: 6px 14px;
        border-radius: 20px; font-size: 12px; font-weight: 700;
        letter-spacing: 0.5px; animation: pulse 2s ease-in-out infinite;
    }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.6; }} }}

    /* Toolbar */
    .toolbar {{
        position: sticky; top: 0; z-index: 50;
        background: #0a0a0f; padding: 12px 0 16px 0;
        border-bottom: 1px solid #1a1a2a;
        margin-bottom: 20px;
        display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
    }}
    .cat-tabs {{
        display: flex; gap: 4px; flex-wrap: wrap;
    }}
    .cat-tab {{
        padding: 5px 12px; border-radius: 16px; font-size: 11px;
        font-weight: 600; cursor: pointer; border: 1px solid #252535;
        background: #151520; color: #888; transition: all 0.15s;
        user-select: none; white-space: nowrap;
    }}
    .cat-tab:hover {{ border-color: #404060; color: #ccc; }}
    .cat-tab.active {{ background: #7c3aed; color: #fff; border-color: #7c3aed; }}
    .cat-tab .cat-count {{
        display: inline-block; margin-left: 4px; font-size: 10px;
        opacity: 0.7; font-weight: 400;
    }}
    .search-box {{
        background: #151520; border: 1px solid #252535; border-radius: 8px;
        padding: 6px 12px; color: #e0e0e0; font-size: 12px; width: 180px;
        outline: none; font-family: inherit;
    }}
    .search-box:focus {{ border-color: #7c3aed; }}
    .search-box::placeholder {{ color: #555; }}
    .sort-select {{
        background: #151520; border: 1px solid #252535; border-radius: 8px;
        padding: 6px 10px; color: #e0e0e0; font-size: 12px;
        outline: none; cursor: pointer; font-family: inherit;
    }}
    .toggle-btn {{
        padding: 5px 12px; border-radius: 16px; font-size: 11px;
        font-weight: 600; cursor: pointer; border: 1px solid #252535;
        background: #151520; color: #888; transition: all 0.15s;
        user-select: none;
    }}
    .toggle-btn.active {{ background: #1e293b; color: #60a5fa; border-color: #334155; }}

    /* Summary cards */
    .summary {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px; margin-bottom: 20px;
    }}
    .stat-card {{
        background: #151520; border: 1px solid #252535;
        border-radius: 10px; padding: 14px;
    }}
    .stat-card .label {{
        font-size: 10px; color: #888; text-transform: uppercase;
        letter-spacing: 0.8px; margin-bottom: 4px;
    }}
    .stat-card .value {{ font-size: 26px; font-weight: 700; color: #fff; }}
    .stat-card .value.green {{ color: #4ade80; }}
    .stat-card .value.amber {{ color: #fbbf24; }}
    .stat-card .value.blue {{ color: #60a5fa; }}
    .stat-card .value.red {{ color: #f87171; }}
    .stat-card .value.purple {{ color: #a78bfa; }}

    /* Category summary */
    .cat-summary {{
        background: #151520; border: 1px solid #252535;
        border-radius: 10px; padding: 16px; margin-bottom: 20px;
    }}
    .cat-summary-header {{
        display: flex; justify-content: space-between; align-items: center;
        cursor: pointer; user-select: none;
    }}
    .cat-summary-header h3 {{ font-size: 13px; color: #aaa; font-weight: 600; }}
    .cat-summary-header .toggle {{ font-size: 11px; color: #555; }}
    .cat-summary-grid {{
        display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px; margin-top: 12px;
    }}
    .cat-summary-grid.collapsed {{ display: none; }}
    .cat-stat {{
        display: flex; align-items: center; gap: 10px;
        padding: 8px 10px; border-radius: 8px; background: #1a1a2a;
    }}
    .cat-dot {{
        width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
    }}
    .cat-stat-info {{ flex: 1; min-width: 0; }}
    .cat-stat-name {{ font-size: 12px; font-weight: 600; color: #ddd; text-transform: capitalize; }}
    .cat-stat-detail {{ font-size: 10px; color: #666; margin-top: 2px; }}
    .cat-mini-bar {{
        height: 4px; background: #252535; border-radius: 2px; margin-top: 4px; overflow: hidden;
    }}
    .cat-mini-fill {{ height: 100%; border-radius: 2px; }}

    /* Overall bar */
    .overall-bar {{
        background: #151520; border: 1px solid #252535;
        border-radius: 10px; padding: 16px; margin-bottom: 20px;
    }}
    .overall-bar .label {{ font-size: 13px; color: #aaa; margin-bottom: 10px; }}
    .overall-track {{
        height: 24px; background: #1a1a2a; border-radius: 12px; overflow: hidden;
    }}
    .overall-fill {{
        height: 100%; background: linear-gradient(90deg, #4ade80, #22c55e);
        border-radius: 12px; display: flex; align-items: center;
        justify-content: center; font-size: 12px; font-weight: 700;
        color: #000; min-width: 40px; transition: width 0.3s;
    }}

    /* Topup info */
    .topup-info {{
        background: #0f2918; border: 1px solid #166534;
        border-radius: 10px; padding: 14px 16px; margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: center;
        flex-wrap: wrap; gap: 8px;
    }}
    .topup-info .ti-label {{ font-size: 12px; color: #4ade80; font-weight: 600; }}
    .topup-info .ti-detail {{ font-size: 12px; color: #86efac; }}

    /* Legend */
    .legend {{
        display: flex; gap: 16px; margin-bottom: 16px;
        font-size: 11px; color: #666; flex-wrap: wrap;
    }}
    .legend-item {{ display: flex; align-items: center; gap: 5px; }}
    .legend-swatch {{ width: 10px; height: 10px; border-radius: 3px; }}

    /* Sessions grid */
    .sessions {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }}
    @media (max-width: 860px) {{
        .sessions {{ grid-template-columns: 1fr; }}
    }}
    .session {{
        background: #151520; border: 1px solid #252535;
        border-radius: 10px; padding: 14px 16px;
        transition: border-color 0.2s, background 0.2s;
        cursor: pointer; user-select: none;
    }}
    .session:hover {{ border-color: #404060; }}
    .session-complete {{ border-left: 3px solid #4ade80; opacity: 0.5; }}
    .session-incomplete {{ border-left: 3px solid #f87171; }}
    .session.prioritised {{ border-color: #7c3aed; background: #1a1528; opacity: 1; }}
    .session-header {{
        display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 5px;
    }}
    .session-left {{ display: flex; align-items: center; gap: 8px; min-width: 0; }}
    .priority-num {{
        width: 22px; height: 22px; border-radius: 50%;
        display: none; align-items: center; justify-content: center;
        font-size: 10px; font-weight: 800; color: #fff;
        background: #7c3aed; flex-shrink: 0;
    }}
    .priority-num.active {{ display: flex; }}
    .session-name {{
        font-size: 13px; font-weight: 600; color: #fff;
        font-family: 'SF Mono', 'Fira Code', monospace;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .session-name a {{ color: inherit; text-decoration: none; }}
    .session-name a:hover {{ text-decoration: underline; }}
    .status-dot {{
        width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    }}
    .session-badges {{ display: flex; gap: 4px; flex-shrink: 0; flex-wrap: wrap; }}
    .badge {{
        font-size: 9px; font-weight: 600; padding: 2px 7px;
        border-radius: 10px; letter-spacing: 0.3px; white-space: nowrap;
    }}
    .badge-human {{ background: #7c3aed; color: #fff; }}
    .badge-auto {{ background: #334155; color: #94a3b8; }}
    .badge-ready {{ background: #166534; color: #4ade80; }}
    .badge-cat {{ color: #fff; }}
    .badge-ambient {{ background: #1e293b; color: #94a3b8; }}
    .session-stats {{ font-size: 10px; color: #555; margin-bottom: 8px; line-height: 1.6; }}
    .session-stats .needs {{ color: #f87171; font-weight: 600; }}
    .chunk-bars-container {{
        display: flex; gap: 2px; height: 36px;
        align-items: flex-end; margin-bottom: 5px;
    }}
    .chunk-bar {{
        flex: 1; height: 100%; background: #1a1a2a; border-radius: 2px;
        display: flex; align-items: flex-end; min-width: 3px; max-width: 14px;
        cursor: pointer; transition: opacity 0.15s;
    }}
    .chunk-bar:hover {{ opacity: 0.8; }}
    .chunk-fill {{ width: 100%; border-radius: 2px; transition: height 0.3s; }}
    .session-progress {{
        height: 3px; background: #1a1a2a; border-radius: 2px; overflow: hidden;
    }}
    .session-progress-fill {{ height: 100%; background: #4ade80; border-radius: 2px; }}

    /* Empty state */
    .empty-state {{
        text-align: center; padding: 60px 20px; color: #555;
        font-size: 14px; grid-column: 1 / -1;
    }}

    /* Priority panel */
    .priority-panel {{
        position: fixed; bottom: 0; left: 0; right: 0;
        background: #151520; border-top: 2px solid #7c3aed;
        padding: 10px 24px; display: none; z-index: 100;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.5);
    }}
    .priority-panel.visible {{ display: flex; align-items: center; gap: 12px; }}
    .priority-panel .queue-label {{
        font-size: 11px; color: #7c3aed; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.5px; flex-shrink: 0;
    }}
    .priority-panel .queue-items {{
        flex: 1; display: flex; gap: 6px; overflow-x: auto;
        padding: 4px 0;
    }}
    .queue-chip {{
        background: #2a2040; color: #c4b5fd; border: 1px solid #7c3aed;
        border-radius: 16px; padding: 4px 8px 4px 10px; font-size: 10px;
        font-family: 'SF Mono', monospace; white-space: nowrap;
        display: flex; align-items: center; gap: 5px;
        cursor: grab; user-select: none;
    }}
    .queue-chip.dragging {{ opacity: 0.4; }}
    .queue-chip .chip-num {{
        background: #7c3aed; color: #fff; width: 16px; height: 16px;
        border-radius: 50%; display: flex; align-items: center;
        justify-content: center; font-size: 9px; font-weight: 800;
    }}
    .queue-chip .chip-x {{
        width: 16px; height: 16px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; color: #888; cursor: pointer;
        transition: color 0.15s, background 0.15s;
    }}
    .queue-chip .chip-x:hover {{ color: #f87171; background: rgba(248,113,113,0.15); }}
    .priority-actions {{ display: flex; gap: 6px; flex-shrink: 0; align-items: center; }}
    .cat-add-select {{
        background: #151520; border: 1px solid #252535; border-radius: 8px;
        padding: 5px 8px; color: #888; font-size: 11px; cursor: pointer;
        font-family: inherit;
    }}
    .btn {{
        padding: 6px 14px; border-radius: 8px; border: none;
        font-size: 11px; font-weight: 700; cursor: pointer;
        letter-spacing: 0.3px;
    }}
    .btn-save {{ background: #7c3aed; color: #fff; }}
    .btn-save:hover {{ background: #6d28d9; }}
    .btn-clear {{ background: #1e1e2e; color: #888; border: 1px solid #333; }}
    .btn-clear:hover {{ background: #2a2a3a; }}
    .btn-copy {{ background: #1e293b; color: #60a5fa; border: 1px solid #334155; }}
    .btn-copy:hover {{ background: #1e3a5f; }}

    /* Toast */
    .toast {{
        position: fixed; top: 20px; right: 20px; background: #22c55e;
        color: #000; padding: 10px 20px; border-radius: 10px;
        font-size: 13px; font-weight: 600; z-index: 200;
        opacity: 0; transition: opacity 0.3s; pointer-events: none;
    }}
    .toast.show {{ opacity: 1; }}

    /* Chunk detail modal */
    .modal-overlay {{
        position: fixed; inset: 0; background: rgba(0,0,0,0.7);
        z-index: 300; display: none; align-items: center; justify-content: center;
    }}
    .modal-overlay.visible {{ display: flex; }}
    .modal {{
        background: #1a1a2a; border: 1px solid #333; border-radius: 14px;
        padding: 24px; max-width: 500px; width: 90%; max-height: 80vh;
        overflow-y: auto;
    }}
    .modal h3 {{ font-size: 16px; color: #fff; margin-bottom: 12px; }}
    .modal .modal-close {{
        float: right; cursor: pointer; font-size: 18px; color: #888;
        background: none; border: none; padding: 4px 8px;
    }}
    .modal .modal-close:hover {{ color: #fff; }}
    .modal-field {{ margin-bottom: 10px; }}
    .modal-field .mf-label {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }}
    .modal-field .mf-value {{ font-size: 13px; color: #ddd; line-height: 1.5; }}
    .modal-field .mf-value.mono {{ font-family: 'SF Mono', monospace; font-size: 12px; }}

    .footer {{
        margin-top: 40px; text-align: center; font-size: 11px; color: #444;
    }}
</style>
</head>
<body>

    <div class="header">
        <div>
            <h1>Vault Dashboard</h1>
            <div class="subtitle">Target: {target} candidates/chunk &middot; Generated {now}</div>
        </div>
        <div class="header-right">
            {"<div class='topup-badge'>TOPUP RUNNING</div>" if topup_running else ""}
        </div>
    </div>

    <div class="summary">
        <div class="stat-card">
            <div class="label">Sessions</div>
            <div class="value">{total_sessions}</div>
        </div>
        <div class="stat-card">
            <div class="label">At Target</div>
            <div class="value green">{sessions_at_target}</div>
        </div>
        <div class="stat-card">
            <div class="label">Below Target</div>
            <div class="value amber">{total_sessions - sessions_at_target}</div>
        </div>
        <div class="stat-card">
            <div class="label">Total WAVs</div>
            <div class="value blue">{total_wavs:,}</div>
        </div>
        <div class="stat-card">
            <div class="label">Total Chunks</div>
            <div class="value">{total_chunks}</div>
        </div>
        <div class="stat-card">
            <div class="label">Human Picked</div>
            <div class="value purple">{human_picked}</div>
        </div>
        <div class="stat-card">
            <div class="label">Deployed</div>
            <div class="value green">{deployed}</div>
        </div>
        <div class="stat-card">
            <div class="label">WAVs Needed</div>
            <div class="value red">{total_wavs_needed:,}</div>
        </div>
    </div>

    <div id="cat-summary" class="cat-summary">
        <div class="cat-summary-header" onclick="toggleCatSummary()">
            <h3>Category Breakdown</h3>
            <span class="toggle" id="cat-toggle">&#9660;</span>
        </div>
        <div class="cat-summary-grid" id="cat-grid"></div>
    </div>

    <div class="overall-bar">
        <div class="label">Overall replenishment: {sessions_at_target}/{total_sessions} sessions at {target}+ per chunk</div>
        <div class="overall-track">
            <div class="overall-fill" style="width:{sessions_at_target / max(total_sessions,1) * 100:.1f}%">
                {sessions_at_target / max(total_sessions,1) * 100:.0f}%
            </div>
        </div>
    </div>

    {"<div class='topup-info'><span class='ti-label'>Topup ETA</span><span class='ti-detail'>" + str(total_wavs_needed) + " WAVs remaining &middot; ~" + str(eta_hours) + " hours at 7.5s/WAV</span></div>" if eta_hours else ""}

    <div class="toolbar">
        <div class="cat-tabs" id="cat-tabs"></div>
        <input type="text" class="search-box" id="search" placeholder="Search name, ambient...">
        <select class="sort-select" id="sort-select">
            <option value="name">Name (A-Z)</option>
            <option value="avg-fill-asc">Avg Fill (lowest)</option>
            <option value="needed-desc">Chunks Needed (most)</option>
            <option value="category">Category</option>
        </select>
        <div class="toggle-btn active" id="toggle-completed" onclick="toggleShowCompleted()">Hide completed</div>
    </div>

    <div class="legend">
        <div class="legend-item"><div class="legend-swatch" style="background:#4ade80"></div>{target}+ candidates</div>
        <div class="legend-item"><div class="legend-swatch" style="background:#fbbf24"></div>70-99% of target</div>
        <div class="legend-item"><div class="legend-swatch" style="background:#f87171"></div>Below 70%</div>
        <div class="legend-item"><span class="badge badge-human">HUMAN</span> Human picks</div>
        <div class="legend-item"><span class="badge badge-auto">AUTO</span> Auto picks</div>
        <div class="legend-item"><div class="legend-swatch" style="background:#7c3aed"></div>Click to prioritise</div>
    </div>

    <div class="sessions" id="sessions-grid"></div>

    <div class="priority-panel" id="priority-panel">
        <div class="queue-label">Priority</div>
        <div class="queue-items" id="queue-items"></div>
        <div class="priority-actions">
            <select class="cat-add-select" id="cat-add-select" onchange="addCategoryToQueue(this.value); this.value='';">
                <option value="">+ Add category...</option>
            </select>
            <button class="btn btn-clear" onclick="clearQueue()">Clear</button>
            <button class="btn btn-copy" onclick="copyCommand()">Copy</button>
            <button class="btn btn-save" onclick="saveQueue()">Save</button>
        </div>
    </div>

    <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
        <div class="modal" id="modal"></div>
    </div>

    <div class="toast" id="toast"></div>

    <div class="footer">
        S&#x101;lus Vault Dashboard &middot; {total_wavs:,} WAVs across {total_chunks} chunks in {total_sessions} sessions
    </div>

<script>
// ——— Data ———
const SESSIONS = {sessions_json};
const TARGET = {target};
const CATEGORY_COLORS = {category_colors_json};
const CATEGORY_STATS = {category_stats_json};
const PRIORITY_PATH = {json.dumps(priority_file_path)};

// ——— State ———
let queue = {priority_json};
let activeCategory = 'all';
let searchQuery = '';
let sortMode = 'name';
let showCompleted = true;

// Restore state from localStorage
try {{
    const saved = JSON.parse(localStorage.getItem('vault-dash-state') || '{{}}');
    if (saved.queue && Array.isArray(saved.queue)) queue = saved.queue;
    if (saved.activeCategory) activeCategory = saved.activeCategory;
    if (saved.sortMode) sortMode = saved.sortMode;
    if (saved.showCompleted !== undefined) showCompleted = saved.showCompleted;
}} catch(e) {{}}

// Migrate old key
try {{
    const oldQ = JSON.parse(localStorage.getItem('vault-priority-queue') || 'null');
    if (oldQ && Array.isArray(oldQ) && oldQ.length > 0 && queue.length === 0) {{
        queue = oldQ;
        localStorage.removeItem('vault-priority-queue');
    }}
}} catch(e) {{}}

function saveState() {{
    localStorage.setItem('vault-dash-state', JSON.stringify({{
        queue, activeCategory, sortMode, showCompleted
    }}));
}}

// ——— Category Tabs ———
function buildCatTabs() {{
    const tabs = document.getElementById('cat-tabs');
    const cats = ['all', ...Object.keys(CATEGORY_COLORS)];
    const catCounts = {{}};
    SESSIONS.forEach(s => {{
        const c = s.category || 'uncategorised';
        catCounts[c] = (catCounts[c] || 0) + 1;
    }});
    catCounts['all'] = SESSIONS.length;

    tabs.innerHTML = cats.map(c => {{
        const label = c === 'all' ? 'All' : c.charAt(0).toUpperCase() + c.slice(1);
        const count = catCounts[c] || 0;
        if (c !== 'all' && count === 0) return '';
        const active = activeCategory === c ? 'active' : '';
        return `<div class="cat-tab ${{active}}" onclick="setCategory('${{c}}')">${{label}}<span class="cat-count">${{count}}</span></div>`;
    }}).join('');
}}

function setCategory(cat) {{
    activeCategory = cat;
    saveState();
    buildCatTabs();
    renderSessions();
}}

// ——— Category Summary ———
function buildCatSummary() {{
    const grid = document.getElementById('cat-grid');
    let html = '';
    for (const [cat, stats] of Object.entries(CATEGORY_STATS)) {{
        const color = CATEGORY_COLORS[cat] || '#888';
        const pct = stats.total > 0 ? Math.round(stats.at_target / stats.total * 100) : 0;
        html += `
            <div class="cat-stat">
                <div class="cat-dot" style="background:${{color}}"></div>
                <div class="cat-stat-info">
                    <div class="cat-stat-name">${{cat}}</div>
                    <div class="cat-stat-detail">${{stats.total}} sessions &middot; ${{stats.at_target}} at target &middot; ${{stats.wavs.toLocaleString()}} WAVs</div>
                    <div class="cat-mini-bar">
                        <div class="cat-mini-fill" style="width:${{pct}}%;background:${{color}}"></div>
                    </div>
                </div>
            </div>`;
    }}
    grid.innerHTML = html;
}}

let catSummaryCollapsed = false;
function toggleCatSummary() {{
    catSummaryCollapsed = !catSummaryCollapsed;
    document.getElementById('cat-grid').classList.toggle('collapsed', catSummaryCollapsed);
    document.getElementById('cat-toggle').textContent = catSummaryCollapsed ? '\\u25B6' : '\\u25BC';
}}

// ——— Category batch-add dropdown ———
function buildCatAddDropdown() {{
    const sel = document.getElementById('cat-add-select');
    let html = '<option value="">+ Add category...</option>';
    for (const cat of Object.keys(CATEGORY_COLORS)) {{
        const count = SESSIONS.filter(s => s.category === cat && !s.at_target).length;
        if (count > 0) {{
            html += `<option value="${{cat}}">Add all ${{cat}} (${{count}})</option>`;
        }}
    }}
    sel.innerHTML = html;
}}

function addCategoryToQueue(cat) {{
    if (!cat) return;
    SESSIONS.filter(s => s.category === cat && !s.at_target).forEach(s => {{
        if (!queue.includes(s.name)) queue.push(s.name);
    }});
    renderQueue();
    saveState();
}}

// ——— Filtering & Sorting ———
function getFilteredSessions() {{
    let filtered = SESSIONS.slice();

    // Category filter
    if (activeCategory !== 'all') {{
        filtered = filtered.filter(s => s.category === activeCategory);
    }}

    // Show/hide completed
    if (!showCompleted) {{
        filtered = filtered.filter(s => !s.at_target);
    }}

    // Search
    if (searchQuery) {{
        const q = searchQuery.toLowerCase();
        filtered = filtered.filter(s =>
            s.name.toLowerCase().includes(q) ||
            (s.category || '').toLowerCase().includes(q) ||
            (s.ambient || '').toLowerCase().includes(q)
        );
    }}

    // Sort
    switch (sortMode) {{
        case 'name':
            filtered.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'avg-fill-asc':
            filtered.sort((a, b) => a.avg - b.avg);
            break;
        case 'needed-desc':
            filtered.sort((a, b) => b.wavs_needed - a.wavs_needed);
            break;
        case 'category':
            filtered.sort((a, b) => (a.category || 'zzz').localeCompare(b.category || 'zzz') || a.name.localeCompare(b.name));
            break;
    }}

    return filtered;
}}

function toggleShowCompleted() {{
    showCompleted = !showCompleted;
    const btn = document.getElementById('toggle-completed');
    btn.classList.toggle('active', showCompleted);
    btn.textContent = showCompleted ? 'Hide completed' : 'Show completed';
    saveState();
    renderSessions();
}}

// ——— Build Card ———
function buildCard(s) {{
    const priIdx = queue.indexOf(s.name);
    const isPri = priIdx >= 0;

    // Chunk bars
    let chunkBars = '';
    for (const c of s.chunks) {{
        const pct = Math.min(100, (c.count / TARGET) * 100);
        let color;
        if (c.count >= TARGET) color = '#4ade80';
        else if (c.count >= TARGET * 0.7) color = '#fbbf24';
        else color = '#f87171';

        const hasDetail = c.text !== undefined;
        const clickAttr = hasDetail ? `onclick="event.stopPropagation(); showChunkDetail('${{s.name}}', ${{c.idx}})"` : '';
        const title = `c${{String(c.idx).padStart(2,'0')}}: ${{c.count}}/${{TARGET}}`;

        chunkBars += `<div class="chunk-bar" title="${{title}}" ${{clickAttr}}>` +
            `<div class="chunk-fill" style="height:${{pct}}%;background:${{color}}"></div></div>`;
    }}

    // Badges
    let badges = '';
    if (s.has_human_picks) badges += '<span class="badge badge-human">HUMAN</span>';
    else if (s.has_auto_picks) badges += '<span class="badge badge-auto">AUTO</span>';
    if (s.at_target) badges += '<span class="badge badge-ready">35+</span>';
    if (s.category) {{
        const catColor = CATEGORY_COLORS[s.category] || '#888';
        badges += `<span class="badge badge-cat" style="background:${{catColor}}30;color:${{catColor}}">${{s.category}}</span>`;
    }}
    if (s.ambient) badges += `<span class="badge badge-ambient">${{s.ambient}}</span>`;

    // Status dot
    const dotColor = s.status === 'deployed' ? '#4ade80' : s.status === 'script-only' ? '#fbbf24' : '#555';

    // Stats line
    let stats = `${{s.num_chunks}} chunks &middot; ${{s.total_wavs.toLocaleString()}} WAVs &middot; avg ${{Math.round(s.avg)}} &middot; min ${{s.min}} &middot; max ${{s.max}}`;
    if (s.duration) stats += ` &middot; ${{s.duration}}`;
    if (s.wavs_needed > 0) stats += ` &middot; <span class="needs">needs +${{s.wavs_needed}}</span>`;

    // Progress
    const overallPct = Math.min(100, (s.avg / TARGET) * 100);

    const cls = [
        'session',
        s.at_target ? 'session-complete' : 'session-incomplete',
        isPri ? 'prioritised' : ''
    ].filter(Boolean).join(' ');

    return `
        <div class="${{cls}}" data-name="${{s.name}}" data-complete="${{s.at_target}}"
             onclick="togglePriority('${{s.name}}')">
            <div class="session-header">
                <div class="session-left">
                    <div class="priority-num ${{isPri ? 'active' : ''}}" id="pri-${{s.name}}">${{isPri ? priIdx + 1 : ''}}</div>
                    <div class="status-dot" style="background:${{dotColor}}" title="${{s.status || 'unknown'}}"></div>
                    <div class="session-name">${{s.name}}</div>
                </div>
                <div class="session-badges">${{badges}}</div>
            </div>
            <div class="session-stats">${{stats}}</div>
            <div class="chunk-bars-container">${{chunkBars}}</div>
            <div class="session-progress">
                <div class="session-progress-fill" style="width:${{overallPct}}%"></div>
            </div>
        </div>`;
}}

// ——— Render Sessions ———
function renderSessions() {{
    const grid = document.getElementById('sessions-grid');
    const filtered = getFilteredSessions();

    if (filtered.length === 0) {{
        grid.innerHTML = '<div class="empty-state">No sessions match the current filters</div>';
        return;
    }}

    grid.innerHTML = filtered.map(s => buildCard(s)).join('');
}}

// ——— Chunk Detail Modal ———
function showChunkDetail(sessionName, chunkIdx) {{
    const session = SESSIONS.find(s => s.name === sessionName);
    if (!session) return;
    const chunk = session.chunks.find(c => c.idx === chunkIdx);
    if (!chunk) return;

    const modal = document.getElementById('modal');
    const idx = String(chunkIdx).padStart(2, '0');

    let html = `<button class="modal-close" onclick="closeModal()">&times;</button>`;
    html += `<h3>${{sessionName}} / c${{idx}}</h3>`;

    if (chunk.text !== undefined) {{
        html += `<div class="modal-field"><div class="mf-label">Text</div><div class="mf-value">${{chunk.full_text || chunk.text}}</div></div>`;
        html += `<div class="modal-field"><div class="mf-label">Chars</div><div class="mf-value mono">${{chunk.char_count || '—'}}</div></div>`;
    }}

    html += `<div class="modal-field"><div class="mf-label">WAV Candidates</div><div class="mf-value mono">${{chunk.count}} / ${{TARGET}}</div></div>`;

    if (chunk.passing !== undefined) {{
        html += `<div class="modal-field"><div class="mf-label">Passing (not filtered)</div><div class="mf-value mono">${{chunk.passing}}</div></div>`;
    }}
    if (chunk.avg_score !== undefined) {{
        html += `<div class="modal-field"><div class="mf-label">Avg Composite Score</div><div class="mf-value mono">${{chunk.avg_score}}</div></div>`;
    }}
    if (chunk.best_score !== undefined) {{
        html += `<div class="modal-field"><div class="mf-label">Best Composite Score</div><div class="mf-value mono">${{chunk.best_score}}</div></div>`;
    }}

    modal.innerHTML = html;
    document.getElementById('modal-overlay').classList.add('visible');
}}

function closeModal(event) {{
    if (event && event.target !== document.getElementById('modal-overlay')) return;
    document.getElementById('modal-overlay').classList.remove('visible');
}}
// Also close on Escape
document.addEventListener('keydown', e => {{
    if (e.key === 'Escape') document.getElementById('modal-overlay').classList.remove('visible');
}});

// ——— Priority Queue ———
function togglePriority(name) {{
    const session = SESSIONS.find(s => s.name === name);
    if (session && session.at_target) return;

    const idx = queue.indexOf(name);
    if (idx >= 0) {{
        queue.splice(idx, 1);
    }} else {{
        queue.push(name);
    }}
    saveState();
    renderQueue();
    renderSessions();
}}

function removeFromQueue(name) {{
    const idx = queue.indexOf(name);
    if (idx >= 0) queue.splice(idx, 1);
    saveState();
    renderQueue();
    renderSessions();
}}

function renderQueue() {{
    const panel = document.getElementById('priority-panel');
    const items = document.getElementById('queue-items');

    if (queue.length > 0) {{
        panel.classList.add('visible');
        items.innerHTML = queue.map((name, i) =>
            `<div class="queue-chip" draggable="true" data-name="${{name}}"
                  ondragstart="onDragStart(event)" ondragover="onDragOver(event)"
                  ondrop="onDrop(event)" ondragend="onDragEnd(event)">
                <span class="chip-num">${{i + 1}}</span>
                ${{name.replace(/^\\d+-/, '')}}
                <span class="chip-x" onclick="event.stopPropagation(); removeFromQueue('${{name}}')">&times;</span>
            </div>`
        ).join('');
    }} else {{
        panel.classList.remove('visible');
    }}
}}

// Drag-and-drop reordering
let dragName = null;
function onDragStart(e) {{
    dragName = e.currentTarget.dataset.name;
    e.currentTarget.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}}
function onDragOver(e) {{
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}}
function onDrop(e) {{
    e.preventDefault();
    const targetName = e.currentTarget.dataset.name;
    if (!dragName || dragName === targetName) return;

    const fromIdx = queue.indexOf(dragName);
    const toIdx = queue.indexOf(targetName);
    if (fromIdx < 0 || toIdx < 0) return;

    queue.splice(fromIdx, 1);
    queue.splice(toIdx, 0, dragName);
    saveState();
    renderQueue();
    renderSessions();
}}
function onDragEnd(e) {{
    e.currentTarget.classList.remove('dragging');
    dragName = null;
}}

function clearQueue() {{
    queue = [];
    saveState();
    renderQueue();
    renderSessions();
}}

function copyCommand() {{
    const names = queue.join(',');
    const cmd = `python3 tools/vault-dashboard.py --prioritise "${{names}}"`;
    navigator.clipboard.writeText(cmd).then(() => {{
        showToast('Command copied');
    }}).catch(() => {{
        const ta = document.createElement('textarea');
        ta.value = cmd;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('Command copied');
    }});
}}

function saveQueue() {{
    const data = JSON.stringify(queue, null, 2);
    const blob = new Blob([data], {{ type: 'application/json' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vault-topup-priority.json';
    a.click();
    URL.revokeObjectURL(url);
    showToast('Priority file downloaded');
}}

function showToast(msg) {{
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}}

// ——— Init ———
function init() {{
    buildCatTabs();
    buildCatSummary();
    buildCatAddDropdown();

    // Restore sort
    document.getElementById('sort-select').value = sortMode;
    document.getElementById('toggle-completed').classList.toggle('active', showCompleted);

    renderSessions();
    renderQueue();

    // Event listeners
    document.getElementById('search').addEventListener('input', e => {{
        searchQuery = e.target.value;
        renderSessions();
    }});

    document.getElementById('sort-select').addEventListener('change', e => {{
        sortMode = e.target.value;
        saveState();
        renderSessions();
    }});
}}

init();
</script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Vault Dashboard — visual pool depth overview")
    parser.add_argument("--target", type=int, default=35, help="Target candidates per chunk (default: 35)")
    parser.add_argument("--no-open", action="store_true", help="Don't open in browser")
    parser.add_argument("--no-meta", action="store_true", help="Skip reading chunk meta files (faster)")
    parser.add_argument("--no-scan-duration", action="store_true", help="Skip ffprobe duration calls (faster)")
    parser.add_argument("--output", type=str, default=None, help="Custom output path")
    parser.add_argument("--prioritise", type=str, default=None,
                        help="Set priority queue directly: comma-separated session names")
    args = parser.parse_args()

    # Handle direct priority setting
    if args.prioritise:
        names = [n.strip() for n in args.prioritise.split(",") if n.strip()]
        PRIORITY_FILE.write_text(json.dumps(names, indent=2))
        print(f"Priority file written: {PRIORITY_FILE}")
        print(f"  Queue: {' -> '.join(names)}")
        print(f"  Topup will pick this up before the next session")
        return

    print("Scanning vaults...")
    sessions = scan_vaults(
        args.target,
        scan_meta=not args.no_meta,
        scan_duration=not args.no_scan_duration
    )
    print(f"  Found {len(sessions)} sessions")

    html = generate_html(sessions, args.target)

    out_path = Path(args.output) if args.output else OUTPUT_PATH
    out_path.write_text(html)
    print(f"Dashboard written to {out_path}")
    print(f"  {len(sessions)} sessions | {sum(s['total_wavs'] for s in sessions):,} WAVs")
    print(f"  {sum(1 for s in sessions if s['at_target'])}/{len(sessions)} at target ({args.target}/chunk)")

    # Auto-copy to Desktop
    if DESKTOP_COPY.parent.exists():
        shutil.copy2(str(out_path), str(DESKTOP_COPY))
        print(f"  Copied to {DESKTOP_COPY}")

    if not args.no_open:
        subprocess.run(["open", str(out_path)])


if __name__ == "__main__":
    main()
