#!/usr/bin/env python3
"""
Unified Review Page — generates the picker HTML from the S91 canonical template.

Reads auto-pick-log.json, builds chunk data, injects into the proven S91 UX.
Skips locked chunks (nothing to pick).

Usage:
    python3 tools/unified-review.py narrator-welcome
    python3 tools/unified-review.py 91-the-body-scan --output ~/Desktop/review.html

Serve with: python3 tools/review-server.py {session}
Then open: http://localhost:9191/review
"""

import argparse
import json
from pathlib import Path

VAULT_DIR = Path("content/audio-free/vault")


def generate_unified_page(session_id):
    session_dir = VAULT_DIR / session_id

    log_path = session_dir / "auto-pick-log.json"
    if not log_path.exists():
        raise FileNotFoundError(f"No auto-pick log at {log_path}")
    logs = json.loads(log_path.read_text())

    picks_path = session_dir / "picks-auto.json"
    picks = json.loads(picks_path.read_text()) if picks_path.exists() else None

    chunks_data = []
    for log in logs:
        ci = log['chunk']
        text = log.get('text', '')
        conf = log.get('confidence', 'unknown')
        locked = log.get('locked', False)

        if locked:
            continue

        remaining = log.get('remaining', [])
        top3 = remaining[:3]
        if not top3:
            sel = log.get('selected', {})
            if sel and sel.get('version') is not None:
                top3 = [{'version': sel['version'], 'quality_score': sel.get('quality_score', 0), 'duration': sel.get('duration', 0)}]
        if not top3:
            continue

        auto_pick = None
        if picks:
            for p in picks['picks']:
                if p['chunk'] == ci:
                    auto_pick = p['picked']
                    break

        options = []
        for cand in top3:
            ver = cand['version']
            q = cand.get('quality_score', 0) or 0
            dur = cand.get('duration', 0) or 0
            src = f"c{ci:02d}/c{ci:02d}_v{ver:02d}.wav"
            is_auto = ver == auto_pick
            options.append({'ver': ver, 'q': round(q, 3), 'dur': round(dur, 1), 'src': src, 'is_auto': is_auto})

        chunks_data.append({
            'ci': ci, 'text': text, 'conf': conf,
            'options': options, 'auto_pick': auto_pick
        })

    total_chunks = len(chunks_data)
    chunks_json = json.dumps(chunks_data)

    # S91 canonical template — proven UX, do not modify structure
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Review — {session_id}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a12; color: #f0eefc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; max-width: 1000px; margin: 0 auto; }}
h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
.sub {{ color: #888; font-size: 0.9rem; margin-bottom: 20px; }}

.phase-tabs {{ display: flex; gap: 0; margin-bottom: 20px; }}
.phase-tab {{ flex: 1; padding: 14px; text-align: center; cursor: pointer; font-size: 1rem; font-weight: bold; border: 2px solid #2a2a3e; background: #12121e; transition: all 0.15s; }}
.phase-tab:first-child {{ border-radius: 10px 0 0 10px; }}
.phase-tab:last-child {{ border-radius: 0 10px 10px 0; }}
.phase-tab.active {{ background: #1e3a5f; border-color: #2563eb; color: #7dd3fc; }}
.phase-tab .count {{ font-size: 0.8rem; color: #888; display: block; margin-top: 2px; }}
.phase-tab.active .count {{ color: #7dd3fc; }}

.progress {{ background: #1a1a2e; height: 6px; border-radius: 3px; margin-bottom: 20px; overflow: hidden; }}
.progress-fill {{ height: 100%; background: #2563eb; border-radius: 3px; transition: width 0.3s; }}

.chunk {{ background: #12121e; border: 1px solid #2a2a3e; border-radius: 10px; padding: 18px; margin-bottom: 14px; display: none; position: relative; }}
.chunk.visible {{ display: flex; gap: 14px; }}
.chunk-content {{ flex: 1; min-width: 0; }}

.pool-bar-wrap {{ width: 52px; flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 4px; padding-top: 28px; }}
.pool-bar-header {{ font-size: 0.6rem; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }}
.pool-bar-count {{ font-size: 0.9rem; font-weight: 700; color: #7dd3fc; margin-bottom: 4px; }}
.pool-bar-outer {{ width: 18px; flex: 1; background: #1a1a2e; border-radius: 9px; position: relative; overflow: hidden; min-height: 100px; border: 1px solid #2a2a3e; }}
.pool-bar-fill {{ position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, #2563eb, #7dd3fc); border-radius: 0 0 8px 8px; transition: height 0.4s ease; }}
.pool-bar-total {{ font-size: 0.6rem; color: #555; margin-top: 4px; }}
.chunk.picked {{ border-color: #2d5a3d; }}
.chunk.failed {{ border-color: #5a2d2d; }}
.chunk-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.chunk-id {{ font-weight: bold; font-size: 1.1rem; color: #7dd3fc; }}
.chunk-conf {{ font-size: 0.8rem; }}
.conf-high {{ color: #4ade80; }}
.conf-medium {{ color: #facc15; }}
.conf-low {{ color: #f87171; }}
.chunk-text {{ color: #ccc; font-size: 0.9rem; line-height: 1.5; margin-bottom: 14px; padding: 10px; background: #0a0a12; border-radius: 6px; }}
.auto-badge {{ background: #16a34a33; color: #4ade80; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; margin-left: 8px; }}

.option {{ background: #1a1a2e; border: 2px solid #2a2a3e; border-radius: 8px; padding: 12px; margin-bottom: 8px; transition: all 0.15s; }}
.option.selected {{ border-color: #2563eb; background: #1e293b; }}
.opt-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
.pick-btn {{ padding: 6px 20px; border: 2px solid #444; border-radius: 6px; background: #0a0a12; color: #f0eefc; cursor: pointer; font-size: 1rem; font-weight: bold; transition: all 0.15s; }}
.pick-btn:hover {{ border-color: #2563eb; }}
.option.selected .pick-btn {{ background: #2563eb; border-color: #2563eb; color: white; }}
.opt-meta {{ color: #888; font-size: 0.8rem; }}
audio {{ width: 100%; height: 40px; border-radius: 8px; }}
.audio-bar {{ height: 5px; background: #22d3ee; border-radius: 3px; width: 0%; margin-top: 4px; }}

.verdict-row {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-top: 10px; }}
.v-btn {{ padding: 5px 14px; border: 1px solid #444; border-radius: 6px; background: #1a1a2e; color: #f0eefc; cursor: pointer; font-size: 0.82rem; transition: all 0.15s; }}
.v-btn:hover {{ border-color: #666; }}
.v-btn.active.pass {{ background: #166534; border-color: #22c55e; }}
.v-btn.active.echo {{ background: #713f12; border-color: #f59e0b; }}
.v-btn.active.hiss {{ background: #7c2d12; border-color: #f97316; }}
.v-btn.active.voice {{ background: #581c87; border-color: #a855f7; }}
.v-btn.active.cutoff {{ background: #064e3b; border-color: #10b981; }}
.v-btn.active.bad {{ background: #7f1d1d; border-color: #ef4444; }}
.verdict-label {{ font-weight: bold; font-size: 0.85rem; margin-left: 6px; }}

.review-player {{ margin-top: 10px; }}

.bar {{ position: sticky; bottom: 0; background: #0a0a12ee; backdrop-filter: blur(8px); padding: 14px 0; border-top: 1px solid #2a2a3e; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
.bar-btn {{ padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 0.95rem; font-weight: bold; }}
.bar-btn.primary {{ background: #2563eb; color: white; }}
.bar-btn.primary:hover {{ background: #1d4ed8; }}
.bar-btn.green {{ background: #16a34a; color: white; }}
.bar-btn.green:hover {{ background: #15803d; }}
.bar-btn.outline {{ background: transparent; border: 1px solid #444; color: #f0eefc; }}
.bar-btn.outline:hover {{ border-color: #888; }}
.bar-status {{ color: #888; font-size: 0.85rem; }}

.overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); display: flex; align-items: center; justify-content: center; z-index: 9999; cursor: pointer; }}
.overlay-content {{ text-align: center; }}
.overlay-content .play-icon {{ font-size: 5rem; }}
.overlay-content .overlay-text {{ font-size: 1.2rem; margin-top: 12px; color: #aaa; }}
</style>
</head>
<body>

<h1>Session Review &mdash; {session_id}</h1>
<div class="sub">{total_chunks} chunks | Pick &rarr; Review &rarr; Export</div>

<div class="phase-tabs">
  <div class="phase-tab active" id="tab-pick" onclick="switchPhase('pick')">
    PICK<span class="count" id="pick-count">0/{total_chunks} picked</span>
  </div>
  <div class="phase-tab" id="tab-review" onclick="switchPhase('review')">
    REVIEW<span class="count" id="review-count">0/{total_chunks} reviewed</span>
  </div>
</div>

<div class="chunk-nav" style="display:flex;align-items:center;gap:14px;margin-bottom:14px">
  <span id="chunk-counter" style="font-size:1.1rem;font-weight:bold;white-space:nowrap;min-width:120px">Chunk 1 of {total_chunks}</span>
  <div style="flex:1;position:relative;height:20px;background:#1a1a2e;border-radius:10px;overflow:hidden;cursor:pointer" onclick="jumpToChunk(event)" id="nav-bar">
    <div id="pos-fill" style="height:100%;background:#2563eb44;border-radius:10px;transition:width 0.2s"></div>
    <div id="done-pips" style="position:absolute;top:0;left:0;width:100%;height:100%"></div>
    <div id="pos-marker" style="position:absolute;top:2px;width:12px;height:16px;background:#2563eb;border-radius:4px;transition:left 0.2s"></div>
  </div>
  <span id="done-label" style="font-size:0.85rem;color:#888;white-space:nowrap">0 done</span>
</div>
<div id="eta-label" style="font-size:0.95rem;color:#7dd3fc;margin-bottom:12px;min-height:1.2em"></div>

<div id="chunks-container"></div>

<div class="bar">
  <button class="bar-btn outline" onclick="goBack()">&larr; Back</button>
  <button class="bar-btn green" id="play-btn" onclick="togglePlay()">&#9654; Play</button>
  <button class="bar-btn outline" onclick="skipToNextOption()" style="color:#f59e0b;border-color:#f59e0b66">&#9197; Skip (S)</button>
  <button class="bar-btn outline" onclick="replayCurrent()">&#8634; Repeat (R)</button>
  <button class="bar-btn primary" onclick="advanceNext()">Next &rarr;</button>
  <button class="bar-btn outline" onclick="exportAll()">Export JSON</button>
  <button class="bar-btn outline" style="color:#f87171;border-color:#f8717144" onclick="startOver()">Start Over</button>
  <span class="bar-status" id="status"></span>
  <span class="bar-status" id="save-status" style="color:#4ade80"></span>
</div>

<div class="overlay" id="overlay" onclick="startSession()">
  <div class="overlay-content">
    <div class="play-icon">&#9654;</div>
    <div class="overlay-text">Click to start review</div>
  </div>
</div>

<script>
window.onerror = function(msg, url, line, col, err) {{
  const d = document.createElement('div');
  d.style.cssText = 'position:fixed;top:0;left:0;right:0;padding:10px;background:red;color:white;font-size:14px;z-index:99999';
  d.textContent = 'JS ERROR line ' + line + ': ' + msg;
  document.body.appendChild(d);
}};
const SESSION = '{session_id}';
const chunksData = {chunks_json};
const totalChunks = chunksData.length;

let phase = 'pick';
let currentIdx = 0;
let playing = false;

const humanPicks = {{}};
const verdicts = {{}};
const severities = {{}};

const chunkTiming = {{}};
let reviewStartTime = Date.now();
let sessionPicksMade = 0;
let sessionLoadTime = Date.now();
const visitedChunks = new Set();

// Build DOM
const container = document.getElementById('chunks-container');
chunksData.forEach((chunk, idx) => {{
  const div = document.createElement('div');
  div.className = 'chunk';
  div.id = `chunk-${{idx}}`;
  div.dataset.idx = idx;
  div.dataset.ci = chunk.ci;

  const confClass = chunk.conf === 'high' ? 'conf-high' : chunk.conf === 'medium' ? 'conf-medium' : 'conf-low';

  let pickHtml = '<div class="pick-phase">';
  chunk.options.forEach((opt, oi) => {{
    const label = ['A','B','C'][oi];
    const autoBadge = opt.is_auto ? '<span class="auto-badge">AUTO-PICK</span>' : '';
    pickHtml += `
      <div class="option" id="opt-${{idx}}-${{oi}}" data-oi="${{oi}}">
        <div class="opt-row">
          <button class="pick-btn" onclick="pickOption(${{idx}},${{oi}})">${{label}}</button>
          <span class="opt-meta">v${{String(opt.ver).padStart(2,'0')}} | q=${{opt.q}} | ${{opt.dur}}s</span>
          ${{autoBadge}}
        </div>
        <audio controls preload="none" src="${{opt.src}}"></audio><div class="audio-bar"></div>
      </div>`;
  }});
  pickHtml += `
      <div class="option" id="opt-${{idx}}-none" data-oi="none" style="border-color:#7f1d1d44">
        <div class="opt-row">
          <button class="pick-btn" onclick="pickNone(${{idx}})" style="color:#f87171;border-color:#f8717166">NONE</button>
          <span class="opt-meta" style="color:#f87171">Reject all three &mdash; flag for re-pick</span>
        </div>
      </div>
      <div class="option" id="opt-${{idx}}-cutoff" data-oi="cutoff" style="border-color:#f59e0b44">
        <div class="opt-row">
          <button class="pick-btn" onclick="pickCutoff(${{idx}})" style="color:#f59e0b;border-color:#f59e0b66">CUTOFF (X)</button>
          <span class="opt-meta" style="color:#f59e0b">Skip all short takes &mdash; find longer candidates</span>
        </div>
      </div>`;
  pickHtml += '</div>';

  let reviewHtml = '<div class="review-phase" style="display:none">';
  reviewHtml += '<div class="review-player"><audio controls preload="none" id="review-audio-' + idx + '"></audio><div class="audio-bar"></div></div>';
  reviewHtml += `<div class="verdict-row">
    <button class="v-btn pass" onclick="setVerdict(${{idx}},'PASS')">PASS</button>
    <button class="v-btn echo" onclick="setVerdict(${{idx}},'ECHO')">ECHO</button>
    <button class="v-btn hiss" onclick="setVerdict(${{idx}},'HISS')">HISS</button>
    <button class="v-btn voice" onclick="setVerdict(${{idx}},'VOICE')">VOICE</button>
    <button class="v-btn cutoff" onclick="setVerdict(${{idx}},'CUTOFF')">CUT OFF</button>
    <button class="v-btn bad" onclick="setVerdict(${{idx}},'BAD')">BAD</button>
    <span class="verdict-label" id="vlabel-${{idx}}"></span>
  </div>`;
  reviewHtml += '</div>';

  div.innerHTML = `
    <div class="chunk-content">
      <div class="chunk-head">
        <span class="chunk-id">c${{String(chunk.ci).padStart(2,'0')}}</span>
        <span class="chunk-conf ${{confClass}}">${{chunk.conf}} | ${{chunk.options.length}} options</span>
      </div>
      <div class="chunk-text">${{chunk.text}}</div>
      ${{pickHtml}}
      ${{reviewHtml}}
    </div>
    <div class="pool-bar-wrap">
      <div class="pool-bar-header">POOL</div>
      <div class="pool-bar-count" id="pool-label-${{idx}}">&mdash;</div>
      <div class="pool-bar-outer">
        <div class="pool-bar-fill" id="pool-fill-${{idx}}" style="height:100%"></div>
      </div>
      <div class="pool-bar-total" id="pool-total-${{idx}}"></div>
    </div>
  `;
  container.appendChild(div);
}});

// Pre-select auto-picks
chunksData.forEach((chunk, idx) => {{
  if (chunk.auto_pick !== null) {{
    const autoIdx = chunk.options.findIndex(o => o.ver === chunk.auto_pick);
    if (autoIdx >= 0) {{
      humanPicks[idx] = autoIdx;
      const optEl = document.getElementById(`opt-${{idx}}-${{autoIdx}}`);
      if (optEl) optEl.classList.add('selected');
      document.getElementById(`chunk-${{idx}}`).classList.add('picked');
    }}
  }}
}});

function switchPhase(p) {{
  phase = p;
  document.getElementById('tab-pick').classList.toggle('active', p === 'pick');
  document.getElementById('tab-review').classList.toggle('active', p === 'review');
  document.querySelectorAll('.pick-phase').forEach(el => el.style.display = p === 'pick' ? '' : 'none');
  document.querySelectorAll('.review-phase').forEach(el => el.style.display = p === 'review' ? '' : 'none');
  if (p === 'review') {{
    chunksData.forEach((chunk, idx) => {{
      const pickIdx = humanPicks[idx];
      const audio = document.getElementById(`review-audio-${{idx}}`);
      if (audio && pickIdx !== undefined && chunk.options[pickIdx]) {{
        audio.src = chunk.options[pickIdx].src;
        audio.preload = 'auto';
      }}
    }});
  }}
  showChunk(0);
  updateProgress();
}}

function showChunk(idx) {{
  if (idx < 0 || idx >= totalChunks) return;
  document.querySelectorAll('audio').forEach(a => {{ if (!a.paused) a.pause(); }});
  if (!chunkTiming[idx]) chunkTiming[idx] = {{}};
  if (!chunkTiming[idx].start) chunkTiming[idx].start = Date.now();
  visitedChunks.add(idx);
  currentIdx = idx;
  document.querySelectorAll('.chunk').forEach(el => el.classList.remove('visible'));
  const el = document.getElementById(`chunk-${{idx}}`);
  el.classList.add('visible');
  el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  document.getElementById('status').textContent = `Chunk ${{idx + 1}}/${{totalChunks}}`;
  document.getElementById('chunk-counter').textContent = `Chunk ${{idx + 1}} of ${{totalChunks}}`;
  const pct = ((idx + 1) / totalChunks) * 100;
  document.getElementById('pos-fill').style.width = pct + '%';
  document.getElementById('pos-marker').style.left = `calc(${{pct}}% - 6px)`;
  updateNavPips();
}}

function jumpToChunk(e) {{
  const bar = document.getElementById('nav-bar');
  const rect = bar.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const pct = x / rect.width;
  const idx = Math.max(0, Math.min(totalChunks - 1, Math.floor(pct * totalChunks)));
  document.querySelectorAll('audio').forEach(a => a.pause());
  showChunk(idx);
}}

function updateNavPips() {{
  const pips = document.getElementById('done-pips');
  let html = '';
  for (let i = 0; i < totalChunks; i++) {{
    const x = ((i + 0.5) / totalChunks) * 100;
    const hasPick = humanPicks[i] !== undefined;
    const hasVerdict = verdicts[i] && verdicts[i].size > 0;
    const done = phase === 'pick' ? hasPick : hasVerdict;
    const isPassed = verdicts[i] && verdicts[i].has('PASS');
    const isFailed = hasVerdict && !isPassed;
    let color = 'transparent';
    if (done) {{
      if (phase === 'review') color = isPassed ? '#4ade80' : isFailed ? '#f87171' : '#2563eb';
      else color = '#4ade80';
    }}
    html += `<div style="position:absolute;left:${{x}}%;top:6px;width:3px;height:8px;background:${{color}};border-radius:1px;transform:translateX(-1px)"></div>`;
  }}
  pips.innerHTML = html;
  const doneCount = phase === 'pick'
    ? Object.keys(humanPicks).length
    : Object.keys(verdicts).filter(k => verdicts[k].size > 0).length;
  document.getElementById('done-label').textContent = `${{doneCount}}/${{totalChunks}} done`;
}}

const chunkSkips = {{}};
const poolData = {{}};

chunksData.forEach((chunk, idx) => {{
  poolData[idx] = {{ total: 100, shown: chunk.options.length }};
  updatePoolBar(idx);
}});
fetch('/pool-sizes').then(r => r.json()).then(sizes => {{
  Object.keys(sizes).forEach(ci => {{
    const idx = chunksData.findIndex(c => c.ci === parseInt(ci));
    if (idx >= 0 && poolData[idx]) {{
      poolData[idx].total = sizes[ci];
      updatePoolBar(idx);
    }}
  }});
}}).catch(() => {{}});

function updatePoolBar(idx) {{
  const fill = document.getElementById(`pool-fill-${{idx}}`);
  const label = document.getElementById(`pool-label-${{idx}}`);
  const total = document.getElementById(`pool-total-${{idx}}`);
  if (!fill || !label) return;
  const p = poolData[idx];
  if (!p) return;
  const remaining = Math.max(0, p.total - p.shown);
  const pct = (remaining / p.total) * 100;
  fill.style.height = pct + '%';
  if (pct > 50) fill.style.background = 'linear-gradient(to top, #2563eb, #7dd3fc)';
  else if (pct > 20) fill.style.background = 'linear-gradient(to top, #f59e0b, #fbbf24)';
  else fill.style.background = 'linear-gradient(to top, #dc2626, #f87171)';
  label.textContent = remaining;
  label.style.color = pct > 50 ? '#7dd3fc' : pct > 20 ? '#fbbf24' : '#f87171';
  if (total) total.textContent = `of ${{p.total}}`;
}}

function pickNone(idx) {{
  document.querySelectorAll(`#chunk-${{idx}} audio`).forEach(a => a.pause());
  delete humanPicks[idx];
  document.querySelectorAll(`#chunk-${{idx}} .option`).forEach(el => el.classList.remove('selected'));
  document.getElementById(`chunk-${{idx}}`).classList.remove('picked');

  const ci = chunksData[idx].ci;
  const skip = (chunkSkips[idx] || 0) + chunksData[idx].options.length;
  chunkSkips[idx] = skip;

  fetch(`/more?chunk=${{ci}}&skip=${{skip}}&count=3`).then(r => r.json()).then(data => {{
    if (!data.options || data.options.length === 0) {{
      alert(`No more candidates for chunk ${{ci}} — all ${{data.total_remaining}} exhausted`);
      return;
    }}
    if (poolData[idx]) {{
      poolData[idx].total = data.total_remaining + 3;
      poolData[idx].shown = skip + data.options.length;
      updatePoolBar(idx);
    }}
    const chunk = chunksData[idx];
    chunk.options = data.options.map(o => ({{...o, is_auto: false}}));
    const pickPhase = document.querySelector(`#chunk-${{idx}} .pick-phase`);
    let html = '';
    data.options.forEach((opt, oi) => {{
      const label = ['A','B','C'][oi];
      html += `
        <div class="option" id="opt-${{idx}}-${{oi}}" data-oi="${{oi}}">
          <div class="opt-row">
            <button class="pick-btn" onclick="pickOption(${{idx}},${{oi}})">${{label}}</button>
            <span class="opt-meta">v${{String(opt.ver).padStart(2,'0')}} | q=${{opt.q}} | ${{opt.dur}}s</span>
          </div>
          <audio controls preload="auto" src="${{opt.src}}"></audio><div class="audio-bar"></div>
        </div>`;
    }});
    html += `
      <div class="option" id="opt-${{idx}}-none" data-oi="none" style="border-color:#7f1d1d44">
        <div class="opt-row">
          <button class="pick-btn" onclick="pickNone(${{idx}})" style="color:#f87171;border-color:#f8717166">NONE</button>
          <span class="opt-meta" style="color:#f87171">Reject all three &mdash; load 3 more (${{skip + data.options.length}}/${{data.total_remaining}} shown)</span>
        </div>
      </div>
      <div class="option" id="opt-${{idx}}-cutoff" data-oi="cutoff" style="border-color:#f59e0b44">
        <div class="opt-row">
          <button class="pick-btn" onclick="pickCutoff(${{idx}})" style="color:#f59e0b;border-color:#f59e0b66">CUTOFF (X)</button>
          <span class="opt-meta" style="color:#f59e0b">Skip all short takes &mdash; find longer candidates</span>
        </div>
      </div>`;
    pickPhase.innerHTML = html;
    const firstAudio = pickPhase.querySelector('audio');
    if (firstAudio) setTimeout(() => firstAudio.play(), 300);
  }}).catch(err => {{
    console.error('Failed to load more candidates:', err);
    alert('Could not load more candidates — is the review server running?');
  }});
}}

function pickCutoff(idx) {{
  document.querySelectorAll(`#chunk-${{idx}} audio`).forEach(a => a.pause());
  delete humanPicks[idx];
  document.querySelectorAll(`#chunk-${{idx}} .option`).forEach(el => el.classList.remove('selected'));
  document.getElementById(`chunk-${{idx}}`).classList.remove('picked');

  const chunk = chunksData[idx];
  const maxDur = Math.max(...chunk.options.map(o => o.dur || 0));
  const minDur = maxDur + 0.1;
  const ci = chunk.ci;
  const skip = (chunkSkips[idx] || 0) + chunk.options.length;
  chunkSkips[idx] = skip;

  fetch(`/more?chunk=${{ci}}&skip=${{skip}}&count=3&min_dur=${{minDur}}`).then(r => r.json()).then(data => {{
    if (!data.options || data.options.length === 0) {{
      alert(`No longer candidates found for chunk ${{ci}} (needed >${{maxDur}}s). ${{data.skipped_short || 0}} short ones skipped.`);
      return;
    }}
    chunkSkips[idx] = data.skip;
    if (poolData[idx]) {{
      poolData[idx].total = data.total_remaining + 3;
      poolData[idx].shown = data.skip;
      updatePoolBar(idx);
    }}
    chunk.options = data.options.map(o => ({{...o, is_auto: false}}));
    const pickPhase = document.querySelector(`#chunk-${{idx}} .pick-phase`);
    let html = '';
    data.options.forEach((opt, oi) => {{
      const label = ['A','B','C'][oi];
      html += `
        <div class="option" id="opt-${{idx}}-${{oi}}" data-oi="${{oi}}">
          <div class="opt-row">
            <button class="pick-btn" onclick="pickOption(${{idx}},${{oi}})">${{label}}</button>
            <span class="opt-meta">v${{String(opt.ver).padStart(2,'0')}} | q=${{opt.q}} | ${{opt.dur}}s</span>
          </div>
          <audio controls preload="auto" src="${{opt.src}}"></audio><div class="audio-bar"></div>
        </div>`;
    }});
    html += `
      <div class="option" id="opt-${{idx}}-none" data-oi="none" style="border-color:#7f1d1d44">
        <div class="opt-row">
          <button class="pick-btn" onclick="pickNone(${{idx}})" style="color:#f87171;border-color:#f8717166">NONE</button>
          <span class="opt-meta" style="color:#f87171">Reject all three &mdash; load 3 more (${{data.skip}}/${{data.total_remaining}} shown, ${{data.skipped_short || 0}} short skipped)</span>
        </div>
      </div>
      <div class="option" id="opt-${{idx}}-cutoff" data-oi="cutoff" style="border-color:#f59e0b44">
        <div class="opt-row">
          <button class="pick-btn" onclick="pickCutoff(${{idx}})" style="color:#f59e0b;border-color:#f59e0b66">CUTOFF (X)</button>
          <span class="opt-meta" style="color:#f59e0b">Skip all short takes &mdash; find longer candidates</span>
        </div>
      </div>`;
    pickPhase.innerHTML = html;
    const firstAudio = pickPhase.querySelector('audio');
    if (firstAudio) setTimeout(() => firstAudio.play(), 300);
  }}).catch(err => {{
    console.error('Failed to load cutoff candidates:', err);
    alert('Could not load candidates — is the review server running?');
  }});
}}

function pickOption(idx, oi) {{
  document.querySelectorAll(`#chunk-${{idx}} audio`).forEach(a => a.pause());
  if (!chunkTiming[idx]) chunkTiming[idx] = {{}};
  if (!chunkTiming[idx].end) chunkTiming[idx].end = Date.now();
  sessionPicksMade++;
  humanPicks[idx] = oi;
  document.querySelectorAll(`#chunk-${{idx}} .option`).forEach(el => el.classList.remove('selected'));
  document.getElementById(`opt-${{idx}}-${{oi}}`).classList.add('selected');
  document.getElementById(`chunk-${{idx}}`).classList.add('picked');
  document.getElementById(`chunk-${{idx}}`).classList.remove('failed');
  updateProgress();
  try {{ updateETA(); }} catch(e) {{ console.error('ETA error:', e); }}
  saveLocal();
  const nextIdx = idx + 1;
  setTimeout(() => {{
    if (nextIdx < totalChunks) {{
      showChunk(nextIdx);
      setTimeout(() => {{
        const nextAudio = document.querySelector(`#chunk-${{nextIdx}} .option:first-child audio`);
        if (nextAudio) nextAudio.play();
      }}, 300);
    }}
  }}, 400);
}}

function setVerdict(idx, tag) {{
  if (!verdicts[idx]) verdicts[idx] = new Set();
  const el = document.getElementById(`chunk-${{idx}}`);
  const btn = el.querySelector(`.v-btn.${{tag.toLowerCase()}}`);
  if (tag === 'PASS') {{
    verdicts[idx] = new Set(['PASS']);
    el.querySelectorAll('.v-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    severities[idx] = 'pass';
    el.classList.remove('failed');
  }} else {{
    verdicts[idx].delete('PASS');
    el.querySelector('.v-btn.pass').classList.remove('active');
    if (verdicts[idx].has(tag)) {{
      verdicts[idx].delete(tag);
      btn.classList.remove('active');
    }} else {{
      verdicts[idx].add(tag);
      btn.classList.add('active');
    }}
    if (verdicts[idx].size > 0) {{
      severities[idx] = 'hard';
      el.classList.add('failed');
    }}
  }}
  const label = document.getElementById(`vlabel-${{idx}}`);
  const tags = [...(verdicts[idx] || [])];
  label.textContent = tags.join(' + ');
  label.style.color = tags.includes('PASS') ? '#4ade80' : tags.length ? '#f87171' : '';
  updateProgress();
  saveLocal();
  if (tag === 'PASS') {{
    setTimeout(() => {{
      if (currentIdx + 1 < totalChunks) {{
        showChunk(currentIdx + 1);
        if (playing) {{
          const nextAudio = document.getElementById(`review-audio-${{currentIdx}}`);
          if (nextAudio) nextAudio.play();
        }}
      }}
    }}, 500);
  }}
}}

function skipToNextOption() {{
  const audios = [...document.querySelectorAll(`#chunk-${{currentIdx}} .option audio`)];
  const playingIdx = audios.findIndex(a => !a.paused);
  audios.forEach(a => {{ a.pause(); a.currentTime = 0; }});
  const nextIdx = playingIdx + 1;
  if (nextIdx < audios.length) audios[nextIdx].play();
}}

function goBack() {{
  document.querySelectorAll('audio').forEach(a => a.pause());
  if (currentIdx > 0) showChunk(currentIdx - 1);
}}

function replayCurrent() {{
  if (phase === 'pick') {{
    const audios = document.querySelectorAll(`#chunk-${{currentIdx}} .option audio`);
    audios.forEach(a => {{ a.pause(); a.currentTime = 0; }});
    if (audios.length > 0) audios[0].play();
  }} else {{
    const audio = document.getElementById(`review-audio-${{currentIdx}}`);
    if (audio) {{ audio.pause(); audio.currentTime = 0; audio.play(); }}
  }}
  playing = true;
  const btn = document.getElementById('play-btn');
  btn.innerHTML = '&#9208; Pause';
  btn.className = 'bar-btn outline';
}}

function advanceNext() {{
  if (currentIdx + 1 < totalChunks) {{
    showChunk(currentIdx + 1);
    if (playing) {{
      setTimeout(() => {{
        if (phase === 'pick') {{
          const audio = document.querySelector(`#chunk-${{currentIdx}} .option:first-child audio`);
          if (audio) audio.play();
        }} else {{
          const audio = document.getElementById(`review-audio-${{currentIdx}}`);
          if (audio) audio.play();
        }}
      }}, 400);
    }}
  }}
}}

function togglePlay() {{
  playing = !playing;
  const btn = document.getElementById('play-btn');
  btn.innerHTML = playing ? '&#9208; Pause' : '&#9654; Play';
  btn.className = playing ? 'bar-btn outline' : 'bar-btn green';
  if (!playing) {{
    document.querySelectorAll('audio').forEach(a => a.pause());
  }} else {{
    if (phase === 'pick') {{
      const audio = document.querySelector(`#chunk-${{currentIdx}} .option:first-child audio`);
      if (audio) audio.play();
    }} else {{
      const audio = document.getElementById(`review-audio-${{currentIdx}}`);
      if (audio) audio.play();
    }}
  }}
}}

function updateProgress() {{
  const picked = Object.keys(humanPicks).length;
  const reviewed = Object.keys(verdicts).filter(k => verdicts[k].size > 0).length;
  document.getElementById('pick-count').textContent = `${{picked}}/${{totalChunks}} picked`;
  document.getElementById('review-count').textContent = `${{reviewed}}/${{totalChunks}} reviewed`;
  const pct = phase === 'pick' ? (picked / totalChunks * 100) : (reviewed / totalChunks * 100);
  const progEl = document.getElementById('progress');
  if (progEl) progEl.style.width = pct + '%';
  updateNavPips();
}}

function updateETA() {{
  const el = document.getElementById('eta-label');
  const visited = visitedChunks.size;
  const remaining = totalChunks - visited;
  const elapsed = Math.round((Date.now() - sessionLoadTime) / 1000);
  const eMins = Math.floor(elapsed / 60);
  const eSecs = elapsed % 60;
  if (visited < 1 || elapsed < 5) {{
    el.textContent = `${{visited}}/${{totalChunks}} reviewed | ${{remaining}} left | Elapsed: ${{eMins}}m ${{eSecs < 10 ? '0' : ''}}${{eSecs}}s`;
    return;
  }}
  const avgSec = Math.round(elapsed / visited);
  const etaSec = avgSec * remaining;
  const etaMins = Math.floor(etaSec / 60);
  const etaS = etaSec % 60;
  if (remaining <= 0) {{
    el.textContent = `All ${{totalChunks}} reviewed | ${{avgSec}}s/chunk | Total: ${{eMins}}m ${{eSecs < 10 ? '0' : ''}}${{eSecs}}s`;
    return;
  }}
  el.textContent = `${{visited}}/${{totalChunks}} reviewed | ${{avgSec}}s/chunk | ETA: ${{etaMins}}m ${{etaS}}s | Elapsed: ${{eMins}}m ${{eSecs < 10 ? '0' : ''}}${{eSecs}}s`;
}}
setInterval(updateETA, 1000);

function buildExport() {{
  const picks = [];
  chunksData.forEach((chunk, idx) => {{
    const oi = humanPicks[idx];
    if (oi === undefined) return;
    const opt = chunk.options[oi];
    if (!opt) return;
    const tags = verdicts[idx] ? [...verdicts[idx]] : [];
    picks.push({{
      chunk: chunk.ci,
      picked: opt.ver,
      picked_file: `c${{String(chunk.ci).padStart(2,'0')}}/c${{String(chunk.ci).padStart(2,'0')}}_v${{String(opt.ver).padStart(2,'0')}}.wav`,
      option_index: oi,
      options_shown: chunk.options.map(o => o.ver),
      verdict: tags,
      passed: tags.includes('PASS') || tags.length === 0,
      quality_score: opt.q
    }});
  }});
  const reviewed = Object.keys(verdicts).filter(k => verdicts[k].size > 0).length;
  const passed = Object.values(verdicts).filter(s => s.has('PASS')).length;
  return {{
    session: SESSION,
    method: 'unified-human-review',
    total_chunks: totalChunks,
    picked: Object.keys(humanPicks).length,
    reviewed: reviewed,
    passed: passed,
    failed: reviewed - passed,
    picks: picks
  }};
}}

function exportAll() {{
  const data = buildExport();
  const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION + '-human-review.json';
  a.click();
}}

function startOver() {{
  if (!confirm('Clear all picks and verdicts and start from chunk 1?')) return;
  document.querySelectorAll('audio').forEach(a => a.pause());
  Object.keys(humanPicks).forEach(k => delete humanPicks[k]);
  Object.keys(verdicts).forEach(k => delete verdicts[k]);
  Object.keys(severities).forEach(k => delete severities[k]);
  document.querySelectorAll('.option').forEach(el => el.classList.remove('selected'));
  document.querySelectorAll('.chunk').forEach(el => {{ el.classList.remove('picked','failed'); }});
  document.querySelectorAll('.v-btn').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.verdict-label').forEach(el => {{ el.textContent = ''; }});
  chunksData.forEach((chunk, idx) => {{
    if (chunk.auto_pick !== null) {{
      const autoIdx = chunk.options.findIndex(o => o.ver === chunk.auto_pick);
      if (autoIdx >= 0) {{
        humanPicks[idx] = autoIdx;
        const optEl = document.getElementById(`opt-${{idx}}-${{autoIdx}}`);
        if (optEl) optEl.classList.add('selected');
        document.getElementById(`chunk-${{idx}}`).classList.add('picked');
      }}
    }}
  }});
  localStorage.removeItem('unified-' + SESSION);
  switchPhase('pick');
  showChunk(0);
  updateProgress();
}}

function saveLocal() {{
  try {{
    const state = {{
      picks: humanPicks,
      verdicts: Object.fromEntries(Object.entries(verdicts).map(([k,v]) => [k, [...v]])),
      severities: severities,
      phase: phase,
      currentIdx: currentIdx,
      chunkTiming: chunkTiming,
      reviewStartTime: reviewStartTime
    }};
    localStorage.setItem('unified-' + SESSION, JSON.stringify(state));
  }} catch(e) {{}}
  saveToDisk();
}}

function saveToDisk() {{
  const el = document.getElementById('save-status');
  try {{
    const data = buildExport();
    data.phase = phase;
    data.currentIdx = currentIdx;
    data.chunkTimingData = chunkTiming;
    fetch(location.origin, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(data)
    }}).then(r => {{
      if (r.ok) {{
        el.textContent = 'saved';
        el.style.color = '#4ade80';
        setTimeout(() => el.textContent = '', 1500);
      }} else {{
        el.textContent = 'save failed: ' + r.status;
        el.style.color = '#f87171';
      }}
    }}).catch(err => {{
      el.textContent = 'save error: ' + err.message;
      el.style.color = '#f87171';
    }});
  }} catch(e) {{
    el.textContent = 'JS error: ' + e.message;
    el.style.color = '#f87171';
  }}
}}

function restoreLocal() {{
  try {{
    const stored = localStorage.getItem('unified-' + SESSION);
    if (!stored) return false;
    const state = JSON.parse(stored);
    if (state.picks) {{
      for (const [idx, oi] of Object.entries(state.picks)) {{
        humanPicks[idx] = oi;
        document.querySelectorAll(`#chunk-${{idx}} .option`).forEach(el => el.classList.remove('selected'));
        const optEl = document.getElementById(`opt-${{idx}}-${{oi}}`);
        if (optEl) optEl.classList.add('selected');
        document.getElementById(`chunk-${{idx}}`).classList.add('picked');
      }}
    }}
    if (state.verdicts) {{
      for (const [idx, tags] of Object.entries(state.verdicts)) {{
        verdicts[idx] = new Set(tags);
        tags.forEach(tag => {{
          const btn = document.querySelector(`#chunk-${{idx}} .v-btn.${{tag.toLowerCase()}}`);
          if (btn) btn.classList.add('active');
        }});
        const label = document.getElementById(`vlabel-${{idx}}`);
        if (label) {{
          label.textContent = tags.join(' + ');
          label.style.color = tags.includes('PASS') ? '#4ade80' : tags.length ? '#f87171' : '';
        }}
        if (!tags.includes('PASS') && tags.length > 0) {{
          document.getElementById(`chunk-${{idx}}`).classList.add('failed');
        }}
      }}
    }}
    if (state.severities) Object.assign(severities, state.severities);
    if (state.chunkTiming) Object.assign(chunkTiming, state.chunkTiming);
    if (state.reviewStartTime) reviewStartTime = state.reviewStartTime;
    if (state.phase) switchPhase(state.phase);
    if (state.currentIdx) showChunk(state.currentIdx);
    updateETA();
    updateProgress();
    return true;
  }} catch(e) {{ return false; }}
}}

// Cyan progress bar — track active audio only
let activeAudio = null;
let activeBar = null;
(function tickBar() {{
  if (activeAudio && activeBar && activeAudio.duration > 0) {{
    activeBar.style.width = (activeAudio.currentTime / activeAudio.duration * 100) + '%';
  }}
  requestAnimationFrame(tickBar);
}})();

document.addEventListener('play', (e) => {{
  if (e.target.tagName !== 'AUDIO') return;
  document.querySelectorAll('audio').forEach(a => {{
    if (a !== e.target && !a.paused) a.pause();
  }});
  activeAudio = e.target;
  activeBar = e.target.nextElementSibling;
  if (activeBar && !activeBar.classList.contains('audio-bar')) activeBar = null;
}}, true);

document.addEventListener('ended', (e) => {{
  if (e.target.tagName !== 'AUDIO') return;
  const chunkEl = e.target.closest('.chunk');
  if (!chunkEl) return;
  const idx = parseInt(chunkEl.dataset.idx);
  if (phase === 'pick') {{
    const optEl = e.target.closest('.option');
    if (optEl) {{
      const oi = parseInt(optEl.dataset.oi);
      const nextOpt = chunkEl.querySelector(`[data-oi="${{oi + 1}}"] audio`);
      if (nextOpt) {{
        setTimeout(() => nextOpt.play(), 300);
        return;
      }}
    }}
  }} else {{
    if (playing && idx + 1 < totalChunks) {{
      setTimeout(() => {{
        showChunk(idx + 1);
        const nextAudio = document.getElementById(`review-audio-${{idx + 1}}`);
        if (nextAudio) nextAudio.play();
      }}, 500);
    }}
  }}
}}, true);

document.addEventListener('keydown', (e) => {{
  if (phase === 'pick') {{
    if (e.key === 'a' || e.key === 'A') {{ e.preventDefault(); pickOption(currentIdx, 0); }}
    if (e.key === 'b' || e.key === 'B') {{ e.preventDefault(); pickOption(currentIdx, 1); }}
    if (e.key === 'c' || e.key === 'C') {{ e.preventDefault(); pickOption(currentIdx, 2); }}
    if (e.key === 'n' || e.key === 'N') {{ e.preventDefault(); pickNone(currentIdx); }}
    if (e.key === 'x' || e.key === 'X') {{ e.preventDefault(); pickCutoff(currentIdx); }}
  }}
  if (phase === 'review') {{
    if (e.key === '1') {{ e.preventDefault(); setVerdict(currentIdx, 'PASS'); }}
    if (e.key === '2') {{ e.preventDefault(); setVerdict(currentIdx, 'ECHO'); }}
    if (e.key === '3') {{ e.preventDefault(); setVerdict(currentIdx, 'HISS'); }}
    if (e.key === '4') {{ e.preventDefault(); setVerdict(currentIdx, 'VOICE'); }}
    if (e.key === '5') {{ e.preventDefault(); setVerdict(currentIdx, 'CUTOFF'); }}
    if (e.key === '6') {{ e.preventDefault(); setVerdict(currentIdx, 'BAD'); }}
  }}
  if (e.key === 's' || e.key === 'S') {{ e.preventDefault(); skipToNextOption(); }}
  if (e.key === 'r' || e.key === 'R') {{ e.preventDefault(); replayCurrent(); }}
  if (e.key === ' ') {{ e.preventDefault(); togglePlay(); }}
  if (e.key === 'Enter') {{ e.preventDefault(); advanceNext(); }}
  if (e.key === 'ArrowRight') {{ e.preventDefault(); advanceNext(); }}
  if (e.key === 'ArrowLeft' && currentIdx > 0) {{ e.preventDefault(); showChunk(currentIdx - 1); }}
}});

function startSession() {{
  document.getElementById('overlay').remove();
  showChunk(0);
  playing = true;
  const btn = document.getElementById('play-btn');
  btn.innerHTML = '&#9208; Pause';
  btn.className = 'bar-btn outline';
  const firstAudio = document.querySelector('#chunk-0 .option:first-child audio');
  if (firstAudio) firstAudio.play();
}}

if (!restoreLocal()) {{
  showChunk(0);
}}
updateProgress();
window.addEventListener('beforeunload', saveLocal);
setTimeout(saveToDisk, 1000);
</script>

</body>
</html>'''

    return html


def main():
    parser = argparse.ArgumentParser(description='Generate unified pick + review page (S91 template)')
    parser.add_argument('session_id', help='Session ID')
    parser.add_argument('--local', action='store_true', help='Legacy flag (ignored — always uses relative paths for review-server)')
    parser.add_argument('--output', help='Output path')
    args = parser.parse_args()

    html = generate_unified_page(args.session_id)

    if args.output:
        out = Path(args.output)
    else:
        out = VAULT_DIR / args.session_id / "unified-review.html"

    out.write_text(html)
    print(f"Unified review page: {out}")
    print(f"\nServe with: python3 tools/review-server.py {args.session_id}")
    print(f"Then open:  http://localhost:9191/review")


if __name__ == '__main__':
    main()
