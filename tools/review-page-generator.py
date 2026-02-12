#!/usr/bin/env python3
"""
Review Page Generator — Builds interactive HTML review pages for vault sessions.

Standard template for all picking and testing. Features:
  - EXCELLENT / OK / defect tags (ECHO, HISS, VOICE, CUTOFF, BAD)
  - Severity levels: HARD FAIL / SOFT FAIL / PASS
  - Auto-save to Worker API (vault-picks.salus-mind.com/verdicts/)
  - Keyboard shortcuts, auto-scroll, pause/play
  - Per-chunk metadata for correlation analysis

Usage:
    python3 tools/review-page-generator.py 01-morning-meditation --run v3
    python3 tools/review-page-generator.py 01-morning-meditation --run v3 --picks picks-auto.json
"""

import argparse
import json
from pathlib import Path

VAULT_DIR = Path("content/audio-free/vault")
R2_BASE = "https://media.salus-mind.com/vault"


def generate_review_page(session_id, run_id, picks_path=None, subtitle=""):
    session_dir = VAULT_DIR / session_id

    # Load picks
    if picks_path:
        picks = json.loads(Path(picks_path).read_text())
    else:
        # Try auto picks first, then human picks
        for candidate in ['picks-auto.json', 'picks/picks.json']:
            p = session_dir / candidate
            if p.exists():
                picks = json.loads(p.read_text())
                break
        else:
            raise FileNotFoundError(f"No picks found in {session_dir}")

    # Load logs if available
    log_path = session_dir / "auto-pick-log.json"
    logs = json.loads(log_path.read_text()) if log_path.exists() else None

    total_chunks = len(picks['picks'])
    chunks_html = []
    meta_js = {}

    for i, pick in enumerate(picks['picks']):
        ci = pick['chunk']
        ver = pick['picked']
        if ver is None:
            continue
        text = pick.get('text', '')[:80]
        notes = pick.get('notes', '')

        # Extract metadata from log if available
        q_score = 0
        margin = 0
        conf = 'unknown'
        if logs and i < len(logs):
            log = logs[i]
            sel = log.get('selected', {})
            q_score = sel.get('quality_score', 0) or 0
            margin = sel.get('margin_over_second', 0) or 0
            conf = log.get('confidence', 'unknown')

        conf_class = f'conf-{conf}' if conf in ('high', 'medium', 'low') else 'conf-low'
        flag_html = ''
        if logs and i < len(logs) and logs[i].get('needs_human_review'):
            flag_html = '<span class="flag">FLAG</span>'

        meta_js[ci] = {
            'v': ver, 'conf': conf,
            'q': round(q_score, 3), 'margin': round(margin, 3),
        }

        chunks_html.append(f'''    <div class="chunk" id="chunk-{ci}" data-chunk="{ci}">
      <div class="chunk-header">
        <span class="chunk-id">c{ci:02d}</span>
        <span class="version">v{ver:02d}</span>
        <span class="quality">q={q_score:.3f}</span>
        <span class="{conf_class}">{conf}</span>
        <span class="margin">margin={margin:.3f}</span>
        {flag_html}
      </div>
      <div class="chunk-text">{text}</div>
      <audio controls preload="{'auto' if i == 0 else 'none'}" src="{R2_BASE}/{session_id}/c{ci:02d}/c{ci:02d}_v{ver:02d}.wav"></audio>
      <div class="verdict-row">
        <button class="verdict-btn excellent" onclick="setVerdict({ci},'EXCELLENT')">EXCELLENT</button>
        <button class="verdict-btn ok" onclick="setVerdict({ci},'OK')">OK</button>
        <button class="verdict-btn echo" onclick="setVerdict({ci},'ECHO')">ECHO</button>
        <button class="verdict-btn hiss" onclick="setVerdict({ci},'HISS')">HISS</button>
        <button class="verdict-btn voice" onclick="setVerdict({ci},'VOICE')">VOICE</button>
        <button class="verdict-btn cutoff" onclick="setVerdict({ci},'CUTOFF')">CUT OFF</button>
        <button class="verdict-btn bad" onclick="setVerdict({ci},'BAD')">BAD</button>
        <span class="verdict-label" id="verdict-{ci}"></span>
      </div>
      <div class="severity-row" id="severity-row-{ci}" style="margin-top:6px">
        <span style="color:#888;font-size:0.8rem;margin-right:8px">Severity:</span>
        <button class="sev-btn hard" onclick="setSeverity({ci},'hard')">HARD FAIL</button>
        <button class="sev-btn soft" onclick="setSeverity({ci},'soft')">SOFT FAIL</button>
      </div>
    </div>''')

    meta_json = json.dumps(meta_js, indent=2)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Review {run_id} — {session_id}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a12; color: #f0eefc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; max-width: 900px; margin: 0 auto; }}
h1 {{ font-size: 1.4rem; margin-bottom: 5px; }}
.subtitle {{ color: #888; margin-bottom: 20px; font-size: 0.9rem; }}
.stats {{ background: #1a1a2e; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 20px; flex-wrap: wrap; }}
.stat {{ font-size: 0.85rem; }}
.stat b {{ color: #7dd3fc; }}
.chunk {{ background: #12121e; border: 1px solid #2a2a3e; border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
.chunk.reviewed {{ border-color: #2d5a3d; }}
.chunk.failed {{ border-color: #5a2d2d; }}
.chunk.soft-fail {{ border-color: #92400e; }}
.chunk-header {{ display: flex; gap: 12px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }}
.chunk-id {{ font-weight: bold; font-size: 1.1rem; color: #7dd3fc; }}
.version {{ color: #aaa; }}
.quality {{ color: #a78bfa; }}
.conf-high {{ color: #4ade80; }}
.conf-medium {{ color: #facc15; }}
.conf-low {{ color: #f87171; }}
.conf-unknown {{ color: #888; }}
.margin {{ color: #888; font-size: 0.8rem; }}
.flag {{ background: #dc2626; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
.chunk-text {{ color: #ccc; font-size: 0.85rem; margin-bottom: 10px; line-height: 1.4; }}
audio {{ width: 100%; margin-bottom: 10px; }}
.verdict-row {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
.verdict-btn {{ padding: 6px 16px; border: 1px solid #444; border-radius: 6px; background: #1a1a2e; color: #f0eefc; cursor: pointer; font-size: 0.85rem; transition: all 0.15s; }}
.verdict-btn:hover {{ border-color: #666; }}
.verdict-btn.excellent:hover, .verdict-btn.excellent.active {{ background: #1e3a5f; border-color: #38bdf8; }}
.verdict-btn.ok:hover, .verdict-btn.ok.active {{ background: #166534; border-color: #22c55e; }}
.verdict-btn.echo:hover, .verdict-btn.echo.active {{ background: #713f12; border-color: #f59e0b; }}
.verdict-btn.hiss:hover, .verdict-btn.hiss.active {{ background: #7c2d12; border-color: #f97316; }}
.verdict-btn.voice:hover, .verdict-btn.voice.active {{ background: #581c87; border-color: #a855f7; }}
.verdict-btn.cutoff:hover, .verdict-btn.cutoff.active {{ background: #064e3b; border-color: #10b981; }}
.verdict-btn.bad:hover, .verdict-btn.bad.active {{ background: #7f1d1d; border-color: #ef4444; }}
.verdict-label {{ font-weight: bold; font-size: 0.9rem; margin-left: 8px; }}
.severity-row {{ display: flex; gap: 8px; align-items: center; }}
.sev-btn {{ padding: 4px 12px; border: 1px solid #444; border-radius: 6px; background: #1a1a2e; color: #f0eefc; cursor: pointer; font-size: 0.78rem; transition: all 0.15s; }}
.sev-btn:hover {{ border-color: #666; }}
.sev-btn.hard:hover, .sev-btn.hard.active {{ background: #7f1d1d; border-color: #ef4444; color: #fca5a5; }}
.sev-btn.soft:hover, .sev-btn.soft.active {{ background: #78350f; border-color: #f59e0b; color: #fcd34d; }}
.export-bar {{ position: sticky; bottom: 0; background: #0a0a12; padding: 12px 0; border-top: 1px solid #2a2a3e; display: flex; gap: 12px; align-items: center; }}
.export-btn {{ padding: 10px 24px; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; }}
.export-btn:hover {{ background: #1d4ed8; }}
.counter {{ color: #888; }}
</style>
</head>
<body>
<h1>Review {run_id} — {session_id}</h1>
<div class="subtitle">{subtitle} | {total_chunks} chunks</div>
<div class="stats">
  <div class="stat">Keys: 1=EXCELLENT 2=OK 3=ECHO 4=HISS 5=VOICE 6=CUTOFF 7=BAD | H=Hard S=Soft | Space=Pause Enter=Next</div>
</div>

{"".join(chunks_html)}

<div class="export-bar">
  <button class="export-btn" id="pause-btn" onclick="togglePause()" style="background:#16a34a">&#9654; Play</button>
  <button class="export-btn" onclick="exportVerdicts()">Export Verdicts</button>
  <span class="counter" id="counter">0/{total_chunks} reviewed</span>
  <span class="counter" id="save-status" style="color:#4ade80"></span>
</div>

<script>
const verdicts = {{}};
const severities = {{}};
const totalChunks = {total_chunks};
const SESSION = '{session_id}';
const RUN = '{run_id}';
const chunkMeta = {meta_json};

function setVerdict(chunk, verdict) {{
  if (!verdicts[chunk]) verdicts[chunk] = new Set();
  const el = document.getElementById('chunk-' + chunk);
  const btn = el.querySelector('.verdict-btn.' + verdict.toLowerCase());
  const positive = verdict === 'EXCELLENT' || verdict === 'OK';

  if (positive) {{
    verdicts[chunk] = new Set([verdict]);
    el.querySelectorAll('.verdict-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    // PASS clears severity, hide severity row
    severities[chunk] = 'pass';
    el.querySelectorAll('.sev-btn').forEach(b => b.classList.remove('active'));
  }} else {{
    verdicts[chunk].delete('OK');
    verdicts[chunk].delete('EXCELLENT');
    el.querySelector('.verdict-btn.ok').classList.remove('active');
    el.querySelector('.verdict-btn.excellent').classList.remove('active');
    if (verdicts[chunk].has(verdict)) {{
      verdicts[chunk].delete(verdict);
      btn.classList.remove('active');
    }} else {{
      verdicts[chunk].add(verdict);
      btn.classList.add('active');
    }}
    // Default to hard on first defect tag
    if (verdicts[chunk].size > 0) {{
      if (!severities[chunk] || severities[chunk] === 'pass') {{
        setSeverity(chunk, 'hard');
      }}
    }} else {{
      delete severities[chunk];
      el.querySelectorAll('.sev-btn').forEach(b => b.classList.remove('active'));
    }}
  }}

  updateChunkDisplay(chunk);
  autoSave();
}}

function setSeverity(chunk, sev) {{
  severities[chunk] = sev;
  const el = document.getElementById('chunk-' + chunk);
  el.querySelectorAll('.sev-btn').forEach(b => b.classList.remove('active'));
  el.querySelector('.sev-btn.' + sev).classList.add('active');
  updateChunkDisplay(chunk);
  autoSave();
}}

function updateChunkDisplay(chunk) {{
  const el = document.getElementById('chunk-' + chunk);
  const tags = verdicts[chunk] ? [...verdicts[chunk]] : [];
  const label = document.getElementById('verdict-' + chunk);
  const isPositive = verdicts[chunk] && (verdicts[chunk].has('OK') || verdicts[chunk].has('EXCELLENT'));
  const sev = severities[chunk];

  let labelText = tags.join(' + ') || '';
  if (!isPositive && sev && tags.length > 0) {{
    labelText += ' [' + sev.toUpperCase() + ']';
  }}
  label.textContent = labelText;
  label.style.color = isPositive ? '#4ade80' : sev === 'soft' ? '#fcd34d' : tags.length ? '#f87171' : '';

  el.classList.toggle('reviewed', tags.length > 0);
  el.classList.toggle('failed', tags.length > 0 && !isPositive && sev === 'hard');
  el.classList.toggle('soft-fail', tags.length > 0 && !isPositive && sev === 'soft');

  const reviewed = Object.values(verdicts).filter(s => s.size > 0).length;
  document.getElementById('counter').textContent = reviewed + '/' + totalChunks + ' reviewed';
}}

function buildExportData() {{
  const total = Object.values(verdicts).filter(s => s.size > 0).length;
  const ok = Object.values(verdicts).filter(s => s.has('OK') || s.has('EXCELLENT')).length;
  const hardFails = Object.entries(severities).filter(([c,s]) => s === 'hard' && verdicts[c] && verdicts[c].size > 0).length;
  const softFails = Object.entries(severities).filter(([c,s]) => s === 'soft' && verdicts[c] && verdicts[c].size > 0).length;
  const chunks = {{}};
  for (const [c, tags] of Object.entries(verdicts)) {{
    if (tags.size === 0) continue;
    const meta = chunkMeta[c] || {{}};
    const isPositive = tags.has('OK') || tags.has('EXCELLENT');
    chunks[c] = {{
      verdict: [...tags],
      severity: isPositive ? 'pass' : (severities[c] || 'hard'),
      version: meta.v,
      confidence: meta.conf,
      quality_score: meta.q,
      margin: meta.margin,
      passed: isPositive
    }};
  }}
  return {{
    session: SESSION, run: RUN, method: 'review-' + RUN,
    reviewed: total, ok: ok, fail: total - ok,
    hard_fails: hardFails, soft_fails: softFails,
    chunks: chunks
  }};
}}

let saveTimer = null;
function autoSave() {{
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {{
    const data = buildExportData();
    fetch('https://vault-picks.salus-mind.com/verdicts/' + SESSION, {{
      method: 'PUT',
      headers: {{'Authorization':'Bearer salus-vault-2026','Content-Type':'application/json'}},
      body: JSON.stringify(data)
    }}).then(r=>r.json()).then(j=>{{
      document.getElementById('save-status').textContent = j.ok ? 'Saved '+new Date().toLocaleTimeString() : 'Save failed';
    }}).catch(()=>{{
      document.getElementById('save-status').textContent = 'Save failed';
    }});
  }}, 500);
}}

function exportVerdicts() {{
  const results = buildExportData();
  const blob = new Blob([JSON.stringify(results,null,2)],{{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION+'-'+RUN+'-verdicts.json';
  a.click();
}}

let lastChunk = 0;
let paused = true;

function togglePause() {{
  paused = !paused;
  const btn = document.getElementById('pause-btn');
  btn.textContent = paused ? '\\u25B6 Play' : '\\u23F8 Pause';
  btn.style.background = paused ? '#16a34a' : '#d97706';
  if (paused) document.querySelectorAll('.chunk audio').forEach(a => a.pause());
  else {{
    const cur = document.getElementById('chunk-'+lastChunk);
    if (cur) cur.querySelector('audio').play();
  }}
}}

function advanceToChunk(n) {{
  if (paused) {{ lastChunk = n - 1; return; }}
  const next = document.getElementById('chunk-'+n);
  if (next) {{
    next.scrollIntoView({{behavior:'smooth',block:'center'}});
    setTimeout(()=>next.querySelector('audio').play(), 2500);
    lastChunk = n;
  }}
}}

document.addEventListener('keydown', e => {{
  let chunk = lastChunk;
  const map = {{'1':'EXCELLENT','2':'OK','3':'ECHO','4':'HISS','5':'VOICE','6':'CUTOFF','7':'BAD'}};
  if (map[e.key]) {{
    e.preventDefault();
    setVerdict(chunk, map[e.key]);
    lastChunk = chunk;
  }}
  if (e.key === 'h' || e.key === 'H') {{
    e.preventDefault();
    setSeverity(chunk, 'hard');
  }}
  if (e.key === 's' || e.key === 'S') {{
    e.preventDefault();
    setSeverity(chunk, 'soft');
  }}
  if (e.key === 'Enter' && verdicts[chunk] && verdicts[chunk].size > 0) {{
    e.preventDefault();
    advanceToChunk(chunk + 1);
  }}
  if (e.key === ' ') {{
    e.preventDefault();
    togglePause();
  }}
}});

document.querySelectorAll('.chunk audio').forEach(audio => {{
  audio.addEventListener('ended', () => {{
    const chunk = parseInt(audio.closest('.chunk').dataset.chunk);
    lastChunk = chunk;
    advanceToChunk(chunk + 1);
  }});
}});

window.addEventListener('load', () => {{
  const first = document.querySelector('#chunk-0 audio');
  if (first) {{
    paused = false;
    const btn = document.getElementById('pause-btn');
    if (btn) {{ btn.textContent = '\u23F8 Pause'; btn.style.background = '#d97706'; }}
    first.play().catch(()=>{{}});
  }}
}});
</script>
</body>
</html>'''

    return html


def generate_top3_review_page(session_id, run_id, subtitle=""):
    """Generate a review page showing top-3 auto-picker candidates per chunk.

    Instead of showing 1 pre-picked candidate, shows 3 options (A/B/C) for
    human selection. Replaces the 150-comparison A/B tournament with a
    3-option review.
    """
    session_dir = VAULT_DIR / session_id

    # Load auto-pick log (required for top-3)
    log_path = session_dir / "auto-pick-log.json"
    if not log_path.exists():
        raise FileNotFoundError(f"No auto-pick log found at {log_path}. Run auto-picker first.")
    logs = json.loads(log_path.read_text())

    total_chunks = len(logs)
    chunks_html = []
    meta_js = {}

    for i, log in enumerate(logs):
        ci = log['chunk']
        text = log.get('text', '')[:100]
        remaining = log.get('remaining', [])
        conf = log.get('confidence', 'unknown')
        is_unresolvable = log.get('unresolvable', False)

        # Get top 3 (or fewer if not enough survivors)
        top3 = remaining[:3]
        if not top3:
            # Fallback: use selected version only
            sel = log.get('selected', {})
            if sel and sel.get('version') is not None:
                top3 = [{'version': sel['version'], 'quality_score': sel.get('quality_score', 0),
                          'rank_score': 0, 'echo_risk': 0, 'duration': sel.get('duration', 0)}]

        if not top3:
            continue

        labels = ['A', 'B', 'C']
        players_html = []
        for j, cand in enumerate(top3):
            ver = cand['version']
            q = cand.get('quality_score', 0) or 0
            echo = cand.get('echo_risk', 0) or 0
            dur = cand.get('duration', 0) or 0
            label = labels[j]
            preload = 'auto' if i == 0 and j == 0 else 'none'

            players_html.append(f'''        <div class="option" id="opt-{ci}-{j}" data-chunk="{ci}" data-idx="{j}" data-version="{ver}">
          <div class="opt-header">
            <button class="pick-btn" onclick="pickOption({ci},{j})">{label}</button>
            <span class="version">v{ver:02d}</span>
            <span class="quality">q={q:.3f}</span>
            <span class="opt-dur">{dur:.1f}s</span>
            <span class="opt-echo">echo={echo:.6f}</span>
          </div>
          <audio controls preload="{preload}" src="{R2_BASE}/{session_id}/c{ci:02d}/c{ci:02d}_v{ver:02d}.wav"></audio>
        </div>''')

        meta_js[ci] = {
            'options': [{'v': c['version'], 'q': round(c.get('quality_score', 0) or 0, 3)} for c in top3],
            'conf': conf,
            'n_options': len(top3),
        }

        unres_badge = '<span class="flag">UNRESOLVABLE</span>' if is_unresolvable else ''
        conf_class = f'conf-{conf}' if conf in ('high', 'medium', 'low') else 'conf-low'

        chunks_html.append(f'''    <div class="chunk" id="chunk-{ci}" data-chunk="{ci}">
      <div class="chunk-header">
        <span class="chunk-id">c{ci:02d}</span>
        <span class="{conf_class}">{conf}</span>
        <span class="n-options">{len(top3)} options</span>
        {unres_badge}
      </div>
      <div class="chunk-text">{text}</div>
      <div class="options-grid">
{chr(10).join(players_html)}
      </div>
      <div class="pick-label" id="pick-label-{ci}"></div>
      <div class="verdict-row" id="verdict-row-{ci}" style="margin-top:8px">
        <button class="verdict-btn excellent" onclick="setVerdict({ci},'EXCELLENT')">EXCELLENT</button>
        <button class="verdict-btn ok" onclick="setVerdict({ci},'OK')">OK</button>
        <button class="verdict-btn echo" onclick="setVerdict({ci},'ECHO')">ECHO</button>
        <button class="verdict-btn hiss" onclick="setVerdict({ci},'HISS')">HISS</button>
        <button class="verdict-btn voice" onclick="setVerdict({ci},'VOICE')">VOICE</button>
        <button class="verdict-btn cutoff" onclick="setVerdict({ci},'CUTOFF')">CUT OFF</button>
        <button class="verdict-btn bad" onclick="setVerdict({ci},'BAD')">BAD</button>
        <span class="verdict-label" id="verdict-{ci}"></span>
      </div>
      <div class="severity-row" id="severity-row-{ci}" style="margin-top:6px">
        <span style="color:#888;font-size:0.8rem;margin-right:8px">Severity:</span>
        <button class="sev-btn hard" onclick="setSeverity({ci},'hard')">HARD FAIL</button>
        <button class="sev-btn soft" onclick="setSeverity({ci},'soft')">SOFT FAIL</button>
      </div>
    </div>''')

    meta_json = json.dumps(meta_js, indent=2)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Top-3 Review {run_id} — {session_id}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a12; color: #f0eefc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; max-width: 1000px; margin: 0 auto; }}
h1 {{ font-size: 1.4rem; margin-bottom: 5px; }}
.subtitle {{ color: #888; margin-bottom: 20px; font-size: 0.9rem; }}
.stats {{ background: #1a1a2e; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; }}
.stat {{ font-size: 0.85rem; line-height: 1.6; }}
.stat b {{ color: #7dd3fc; }}
.chunk {{ background: #12121e; border: 1px solid #2a2a3e; border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
.chunk.reviewed {{ border-color: #2d5a3d; }}
.chunk.failed {{ border-color: #5a2d2d; }}
.chunk.soft-fail {{ border-color: #92400e; }}
.chunk-header {{ display: flex; gap: 12px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }}
.chunk-id {{ font-weight: bold; font-size: 1.1rem; color: #7dd3fc; }}
.n-options {{ color: #888; font-size: 0.85rem; }}
.conf-high {{ color: #4ade80; }}
.conf-medium {{ color: #facc15; }}
.conf-low {{ color: #f87171; }}
.flag {{ background: #dc2626; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
.chunk-text {{ color: #ccc; font-size: 0.85rem; margin-bottom: 12px; line-height: 1.4; }}
.options-grid {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }}
.option {{ background: #1a1a2e; border: 2px solid #2a2a3e; border-radius: 8px; padding: 10px; transition: all 0.15s; }}
.option.selected {{ border-color: #2563eb; background: #1e293b; }}
.opt-header {{ display: flex; gap: 10px; align-items: center; margin-bottom: 6px; }}
.pick-btn {{ padding: 4px 16px; border: 2px solid #444; border-radius: 6px; background: #0a0a12; color: #f0eefc; cursor: pointer; font-size: 1rem; font-weight: bold; transition: all 0.15s; }}
.pick-btn:hover {{ border-color: #2563eb; background: #1e293b; }}
.option.selected .pick-btn {{ background: #2563eb; border-color: #2563eb; color: white; }}
.version {{ color: #aaa; font-size: 0.85rem; }}
.quality {{ color: #a78bfa; font-size: 0.85rem; }}
.opt-dur {{ color: #888; font-size: 0.8rem; }}
.opt-echo {{ color: #888; font-size: 0.75rem; }}
.pick-label {{ font-weight: bold; font-size: 0.95rem; color: #38bdf8; min-height: 1.2em; }}
audio {{ width: 100%; }}
.verdict-row {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
.verdict-btn {{ padding: 6px 16px; border: 1px solid #444; border-radius: 6px; background: #1a1a2e; color: #f0eefc; cursor: pointer; font-size: 0.85rem; transition: all 0.15s; }}
.verdict-btn:hover {{ border-color: #666; }}
.verdict-btn.excellent:hover, .verdict-btn.excellent.active {{ background: #1e3a5f; border-color: #38bdf8; }}
.verdict-btn.ok:hover, .verdict-btn.ok.active {{ background: #166534; border-color: #22c55e; }}
.verdict-btn.echo:hover, .verdict-btn.echo.active {{ background: #713f12; border-color: #f59e0b; }}
.verdict-btn.hiss:hover, .verdict-btn.hiss.active {{ background: #7c2d12; border-color: #f97316; }}
.verdict-btn.voice:hover, .verdict-btn.voice.active {{ background: #581c87; border-color: #a855f7; }}
.verdict-btn.cutoff:hover, .verdict-btn.cutoff.active {{ background: #064e3b; border-color: #10b981; }}
.verdict-btn.bad:hover, .verdict-btn.bad.active {{ background: #7f1d1d; border-color: #ef4444; }}
.verdict-label {{ font-weight: bold; font-size: 0.9rem; margin-left: 8px; }}
.severity-row {{ display: flex; gap: 8px; align-items: center; }}
.sev-btn {{ padding: 4px 12px; border: 1px solid #444; border-radius: 6px; background: #1a1a2e; color: #f0eefc; cursor: pointer; font-size: 0.78rem; transition: all 0.15s; }}
.sev-btn:hover {{ border-color: #666; }}
.sev-btn.hard:hover, .sev-btn.hard.active {{ background: #7f1d1d; border-color: #ef4444; color: #fca5a5; }}
.sev-btn.soft:hover, .sev-btn.soft.active {{ background: #78350f; border-color: #f59e0b; color: #fcd34d; }}
.export-bar {{ position: sticky; bottom: 0; background: #0a0a12; padding: 12px 0; border-top: 1px solid #2a2a3e; display: flex; gap: 12px; align-items: center; }}
.export-btn {{ padding: 10px 24px; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; }}
.export-btn:hover {{ background: #1d4ed8; }}
.counter {{ color: #888; }}
</style>
</head>
<body>
<h1>Top-3 Review {run_id} — {session_id}</h1>
<div class="subtitle">{subtitle} | {total_chunks} chunks | Pick A, B, or C then rate quality</div>
<div class="stats">
  <div class="stat">Keys: <b>A/B/C</b> = pick option | <b>1</b>=EXCELLENT <b>2</b>=OK <b>3</b>=ECHO <b>4</b>=HISS <b>5</b>=VOICE <b>6</b>=CUTOFF <b>7</b>=BAD</div>
  <div class="stat">H=Hard S=Soft | Space=Pause | Enter=Next chunk</div>
</div>

{"".join(chunks_html)}

<div class="export-bar">
  <button class="export-btn" id="pause-btn" onclick="togglePause()" style="background:#16a34a">&#9654; Play</button>
  <button class="export-btn" onclick="exportPicks()">Export Picks</button>
  <span class="counter" id="counter">0/{total_chunks} picked</span>
  <span class="counter" id="save-status" style="color:#4ade80"></span>
</div>

<script>
const picks = {{}};       // chunk -> option index (0,1,2)
const verdicts = {{}};    // chunk -> Set of verdict tags
const severities = {{}};  // chunk -> 'hard'|'soft'|'pass'
const totalChunks = {total_chunks};
const SESSION = '{session_id}';
const RUN = '{run_id}';
const chunkMeta = {meta_json};

let lastChunk = 0;
let paused = true;

function pickOption(chunk, idx) {{
  picks[chunk] = idx;
  const chunkEl = document.getElementById('chunk-' + chunk);
  // Stop any playing audio in this chunk
  chunkEl.querySelectorAll('audio').forEach(a => a.pause());
  chunkEl.querySelectorAll('.option').forEach((opt, i) => {{
    opt.classList.toggle('selected', i === idx);
  }});
  const meta = chunkMeta[chunk];
  if (meta && meta.options[idx]) {{
    document.getElementById('pick-label-' + chunk).textContent =
      'Selected: ' + ['A','B','C'][idx] + ' (v' + String(meta.options[idx].v).padStart(2,'0') + ')';
  }}
  updateCounter();
  autoSave();
  // Auto-advance to next chunk after picking
  setTimeout(() => advanceToChunk(chunk + 1), 400);
}}

function setVerdict(chunk, verdict) {{
  if (!verdicts[chunk]) verdicts[chunk] = new Set();
  const el = document.getElementById('chunk-' + chunk);
  const btn = el.querySelector('.verdict-btn.' + verdict.toLowerCase());
  const positive = verdict === 'EXCELLENT' || verdict === 'OK';

  if (positive) {{
    verdicts[chunk] = new Set([verdict]);
    el.querySelectorAll('.verdict-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    severities[chunk] = 'pass';
    el.querySelectorAll('.sev-btn').forEach(b => b.classList.remove('active'));
  }} else {{
    verdicts[chunk].delete('OK');
    verdicts[chunk].delete('EXCELLENT');
    el.querySelector('.verdict-btn.ok').classList.remove('active');
    el.querySelector('.verdict-btn.excellent').classList.remove('active');
    if (verdicts[chunk].has(verdict)) {{
      verdicts[chunk].delete(verdict);
      btn.classList.remove('active');
    }} else {{
      verdicts[chunk].add(verdict);
      btn.classList.add('active');
    }}
    if (verdicts[chunk].size > 0) {{
      if (!severities[chunk] || severities[chunk] === 'pass') setSeverity(chunk, 'hard');
    }} else {{
      delete severities[chunk];
      el.querySelectorAll('.sev-btn').forEach(b => b.classList.remove('active'));
    }}
  }}
  updateChunkDisplay(chunk);
  autoSave();
}}

function setSeverity(chunk, sev) {{
  severities[chunk] = sev;
  const el = document.getElementById('chunk-' + chunk);
  el.querySelectorAll('.sev-btn').forEach(b => b.classList.remove('active'));
  el.querySelector('.sev-btn.' + sev).classList.add('active');
  updateChunkDisplay(chunk);
  autoSave();
}}

function updateChunkDisplay(chunk) {{
  const el = document.getElementById('chunk-' + chunk);
  const tags = verdicts[chunk] ? [...verdicts[chunk]] : [];
  const label = document.getElementById('verdict-' + chunk);
  const isPositive = verdicts[chunk] && (verdicts[chunk].has('OK') || verdicts[chunk].has('EXCELLENT'));
  const sev = severities[chunk];

  let labelText = tags.join(' + ') || '';
  if (!isPositive && sev && tags.length > 0) labelText += ' [' + sev.toUpperCase() + ']';
  label.textContent = labelText;
  label.style.color = isPositive ? '#4ade80' : sev === 'soft' ? '#fcd34d' : tags.length ? '#f87171' : '';

  const hasPick = picks[chunk] !== undefined;
  el.classList.toggle('reviewed', hasPick && tags.length > 0);
  el.classList.toggle('failed', tags.length > 0 && !isPositive && sev === 'hard');
  el.classList.toggle('soft-fail', tags.length > 0 && !isPositive && sev === 'soft');
}}

function updateCounter() {{
  const picked = Object.keys(picks).length;
  document.getElementById('counter').textContent = picked + '/' + totalChunks + ' picked';
}}

function buildExportData() {{
  const result = {{
    session: SESSION, run: RUN, method: 'top3-review-' + RUN,
    reviewed: Object.keys(picks).length,
    picks: []
  }};
  for (const [cStr, idx] of Object.entries(picks)) {{
    const c = parseInt(cStr);
    const meta = chunkMeta[c];
    if (!meta) continue;
    const opt = meta.options[idx];
    const tags = verdicts[c] ? [...verdicts[c]] : [];
    const isPositive = tags.includes('OK') || tags.includes('EXCELLENT');
    result.picks.push({{
      chunk: c,
      picked: opt.v,
      picked_file: 'c' + String(c).padStart(2,'0') + '/c' + String(c).padStart(2,'0') + '_v' + String(opt.v).padStart(2,'0') + '.wav',
      option_index: idx,
      options_shown: meta.options.map(o => o.v),
      verdict: tags,
      severity: isPositive ? 'pass' : (severities[c] || 'hard'),
      passed: isPositive,
      quality_score: opt.q
    }});
  }}
  return result;
}}

let saveTimer = null;
function autoSave() {{
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {{
    const data = buildExportData();
    fetch('https://vault-picks.salus-mind.com/picks/' + SESSION, {{
      method: 'PUT',
      headers: {{'Authorization':'Bearer salus-vault-2026','Content-Type':'application/json'}},
      body: JSON.stringify(data)
    }}).then(r=>r.json()).then(j=>{{
      document.getElementById('save-status').textContent = j.ok ? 'Saved '+new Date().toLocaleTimeString() : 'Save failed';
    }}).catch(()=>{{
      document.getElementById('save-status').textContent = 'Save failed';
    }});
  }}, 500);
}}

function exportPicks() {{
  const data = buildExportData();
  const blob = new Blob([JSON.stringify(data,null,2)],{{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION+'-'+RUN+'-top3-picks.json';
  a.click();
}}

function togglePause() {{
  paused = !paused;
  const btn = document.getElementById('pause-btn');
  btn.textContent = paused ? '\\u25B6 Play' : '\\u23F8 Pause';
  btn.style.background = paused ? '#16a34a' : '#d97706';
  if (paused) document.querySelectorAll('audio').forEach(a => a.pause());
  else {{
    // Play option A of current chunk
    const cur = document.getElementById('chunk-'+lastChunk);
    if (cur) {{
      const firstAudio = cur.querySelector('.option audio');
      if (firstAudio) firstAudio.play();
    }}
  }}
}}

function advanceToChunk(n) {{
  const next = document.getElementById('chunk-'+n);
  if (next) {{
    next.scrollIntoView({{behavior:'smooth',block:'center'}});
    lastChunk = n;
    if (!paused) {{
      setTimeout(()=>{{
        const firstAudio = next.querySelector('.option audio');
        if (firstAudio) firstAudio.play();
      }}, 800);
    }}
  }}
}}

// Keyboard shortcuts
document.addEventListener('keydown', e => {{
  let chunk = lastChunk;

  // A/B/C to pick option
  if (e.key === 'a' || e.key === 'A') {{ e.preventDefault(); pickOption(chunk, 0); }}
  if (e.key === 'b' || e.key === 'B') {{ e.preventDefault(); pickOption(chunk, 1); }}
  if (e.key === 'c' || e.key === 'C') {{ e.preventDefault(); pickOption(chunk, 2); }}

  // 1-7 for verdicts
  const map = {{'1':'EXCELLENT','2':'OK','3':'ECHO','4':'HISS','5':'VOICE','6':'CUTOFF','7':'BAD'}};
  if (map[e.key]) {{ e.preventDefault(); setVerdict(chunk, map[e.key]); }}

  // H/S for severity
  if (e.key === 'h' || e.key === 'H') {{ e.preventDefault(); setSeverity(chunk, 'hard'); }}
  if ((e.key === 's' || e.key === 'S') && !e.ctrlKey && !e.metaKey) {{ e.preventDefault(); setSeverity(chunk, 'soft'); }}

  // Enter to advance
  if (e.key === 'Enter' && picks[chunk] !== undefined) {{ e.preventDefault(); advanceToChunk(chunk + 1); }}

  // Space to toggle pause
  if (e.key === ' ') {{ e.preventDefault(); togglePause(); }}
}});

// Auto-advance when each option's audio ends — play next option in same chunk
document.querySelectorAll('.option audio').forEach(audio => {{
  audio.addEventListener('ended', () => {{
    const optEl = audio.closest('.option');
    const chunkEl = optEl.closest('.chunk');
    const chunk = parseInt(chunkEl.dataset.chunk);
    lastChunk = chunk;

    // Find next option in same chunk
    const options = chunkEl.querySelectorAll('.option');
    const idx = parseInt(optEl.dataset.idx);
    if (idx + 1 < options.length) {{
      // Play next option in same chunk
      setTimeout(()=>options[idx+1].querySelector('audio').play(), 500);
    }}
    // After all options played, wait for user pick + Enter
  }});
}});

// Auto-play first chunk on load
window.addEventListener('load', () => {{
  const first = document.querySelector('#chunk-0 .option audio');
  if (first) {{
    paused = false;
    const btn = document.getElementById('pause-btn');
    if (btn) {{ btn.textContent = '\u23F8 Pause'; btn.style.background = '#d97706'; }}
    first.play().catch(()=>{{}});
  }}
}});
</script>
</body>
</html>'''

    return html


def main():
    parser = argparse.ArgumentParser(description='Generate review page for vault session')
    parser.add_argument('session_id', help='Session ID')
    parser.add_argument('--run', default='v1', help='Run identifier (e.g., v3)')
    parser.add_argument('--mode', default='single', choices=['single', 'top3'],
                        help='Review mode: single (1 pick) or top3 (3 options per chunk)')
    parser.add_argument('--picks', help='Path to picks JSON (single mode only)')
    parser.add_argument('--subtitle', default='', help='Subtitle text')
    parser.add_argument('--output', help='Output path (default: vault dir)')
    args = parser.parse_args()

    if args.mode == 'top3':
        html = generate_top3_review_page(args.session_id, args.run, args.subtitle)
        default_name = f"top3-review-{args.run}.html"
    else:
        html = generate_review_page(args.session_id, args.run, args.picks, args.subtitle)
        default_name = f"auto-trial-review-{args.run}.html"

    if args.output:
        out = Path(args.output)
    else:
        out = VAULT_DIR / args.session_id / default_name

    out.write_text(html)
    print(f"Review page: {out}")


if __name__ == '__main__':
    main()
