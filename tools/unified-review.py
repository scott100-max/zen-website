#!/usr/bin/env python3
"""
Unified Review Page — Two-layer human review in a single page.

Layer 1: Pick phase — listen to top-3 candidates per chunk, pick A/B/C
Layer 2: Review phase — play all picks back-to-back as continuous session, verdict each chunk

Usage:
    python3 tools/unified-review.py 91-the-body-scan --local
    python3 tools/unified-review.py 91-the-body-scan --local --output ~/Desktop/review.html
"""

import argparse
import json
from pathlib import Path

VAULT_DIR = Path("content/audio-free/vault")
R2_BASE = "https://media.salus-mind.com/vault"


def generate_unified_page(session_id, local=False):
    session_dir = VAULT_DIR / session_id

    # Load auto-pick log (required for top-3)
    log_path = session_dir / "auto-pick-log.json"
    if not log_path.exists():
        raise FileNotFoundError(f"No auto-pick log at {log_path}")
    logs = json.loads(log_path.read_text())

    # Load picks for pre-selected defaults
    picks_path = session_dir / "picks-auto.json"
    picks = json.loads(picks_path.read_text()) if picks_path.exists() else None

    total_chunks = len(logs)
    chunks_data = []

    for i, log in enumerate(logs):
        ci = log['chunk']
        text = log.get('text', '')
        conf = log.get('confidence', 'unknown')
        remaining = log.get('remaining', [])
        top3 = remaining[:3]

        if not top3:
            sel = log.get('selected', {})
            if sel and sel.get('version') is not None:
                top3 = [{'version': sel['version'], 'quality_score': sel.get('quality_score', 0), 'duration': sel.get('duration', 0)}]

        if not top3:
            continue

        # Get auto-picked version
        auto_pick = None
        if picks:
            for p in picks['picks']:
                if p['chunk'] == ci:
                    auto_pick = p['picked']
                    break

        options = []
        for j, cand in enumerate(top3):
            ver = cand['version']
            q = cand.get('quality_score', 0) or 0
            dur = cand.get('duration', 0) or 0
            if local:
                src = f"file://{(session_dir / f'c{ci:02d}' / f'c{ci:02d}_v{ver:02d}.wav').resolve()}"
            else:
                src = f"{R2_BASE}/{session_id}/c{ci:02d}/c{ci:02d}_v{ver:02d}.wav"
            is_auto = ver == auto_pick
            options.append({'ver': ver, 'q': round(q, 3), 'dur': round(dur, 1), 'src': src, 'is_auto': is_auto})

        chunks_data.append({
            'ci': ci, 'text': text, 'conf': conf, 'options': options, 'auto_pick': auto_pick
        })

    chunks_json = json.dumps(chunks_data)

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

/* Phase tabs */
.phase-tabs {{ display: flex; gap: 0; margin-bottom: 20px; }}
.phase-tab {{ flex: 1; padding: 14px; text-align: center; cursor: pointer; font-size: 1rem; font-weight: bold; border: 2px solid #2a2a3e; background: #12121e; transition: all 0.15s; }}
.phase-tab:first-child {{ border-radius: 10px 0 0 10px; }}
.phase-tab:last-child {{ border-radius: 0 10px 10px 0; }}
.phase-tab.active {{ background: #1e3a5f; border-color: #2563eb; color: #7dd3fc; }}
.phase-tab .count {{ font-size: 0.8rem; color: #888; display: block; margin-top: 2px; }}
.phase-tab.active .count {{ color: #7dd3fc; }}

/* Progress bar */
.progress {{ background: #1a1a2e; height: 6px; border-radius: 3px; margin-bottom: 20px; overflow: hidden; }}
.progress-fill {{ height: 100%; background: #2563eb; border-radius: 3px; transition: width 0.3s; }}

/* Chunk card */
.chunk {{ background: #12121e; border: 1px solid #2a2a3e; border-radius: 10px; padding: 18px; margin-bottom: 14px; display: none; }}
.chunk.visible {{ display: block; }}
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

/* Options */
.option {{ background: #1a1a2e; border: 2px solid #2a2a3e; border-radius: 8px; padding: 12px; margin-bottom: 8px; transition: all 0.15s; }}
.option.selected {{ border-color: #2563eb; background: #1e293b; }}
.opt-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
.pick-btn {{ padding: 6px 20px; border: 2px solid #444; border-radius: 6px; background: #0a0a12; color: #f0eefc; cursor: pointer; font-size: 1rem; font-weight: bold; transition: all 0.15s; }}
.pick-btn:hover {{ border-color: #2563eb; }}
.option.selected .pick-btn {{ background: #2563eb; border-color: #2563eb; color: white; }}
.opt-meta {{ color: #888; font-size: 0.8rem; }}
audio {{ width: 100%; }}

/* Verdict row (review phase) */
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

/* Review phase: single player per chunk */
.review-player {{ margin-top: 10px; }}

/* Bottom bar */
.bar {{ position: sticky; bottom: 0; background: #0a0a12ee; backdrop-filter: blur(8px); padding: 14px 0; border-top: 1px solid #2a2a3e; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
.bar-btn {{ padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 0.95rem; font-weight: bold; }}
.bar-btn.primary {{ background: #2563eb; color: white; }}
.bar-btn.primary:hover {{ background: #1d4ed8; }}
.bar-btn.green {{ background: #16a34a; color: white; }}
.bar-btn.green:hover {{ background: #15803d; }}
.bar-btn.outline {{ background: transparent; border: 1px solid #444; color: #f0eefc; }}
.bar-btn.outline:hover {{ border-color: #888; }}
.bar-status {{ color: #888; font-size: 0.85rem; }}

/* Overlay */
.overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); display: flex; align-items: center; justify-content: center; z-index: 9999; cursor: pointer; }}
.overlay-content {{ text-align: center; }}
.overlay-content .play-icon {{ font-size: 5rem; }}
.overlay-content .overlay-text {{ font-size: 1.2rem; margin-top: 12px; color: #aaa; }}
</style>
</head>
<body>

<h1>Session Review — {session_id}</h1>
<div class="sub">{total_chunks} chunks | Pick &rarr; Review &rarr; Export</div>

<div class="phase-tabs">
  <div class="phase-tab active" id="tab-pick" onclick="switchPhase('pick')">
    PICK<span class="count" id="pick-count">0/{total_chunks} picked</span>
  </div>
  <div class="phase-tab" id="tab-review" onclick="switchPhase('review')">
    REVIEW<span class="count" id="review-count">0/{total_chunks} reviewed</span>
  </div>
</div>

<div class="progress"><div class="progress-fill" id="progress" style="width:0%"></div></div>

<div id="chunks-container"></div>

<div class="bar">
  <button class="bar-btn green" id="play-btn" onclick="togglePlay()">&#9654; Play</button>
  <button class="bar-btn primary" onclick="advanceNext()">Next &rarr;</button>
  <button class="bar-btn outline" onclick="exportAll()">Export JSON</button>
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
const SESSION = '{session_id}';
const chunksData = {chunks_json};
const totalChunks = chunksData.length;

let phase = 'pick'; // 'pick' or 'review'
let currentIdx = 0;
let playing = false;

// State
const humanPicks = {{}}; // chunkIdx -> optionIdx (0,1,2)
const verdicts = {{}};   // chunkIdx -> Set of tags
const severities = {{}};  // chunkIdx -> 'pass'|'hard'|'soft'

// Build DOM
const container = document.getElementById('chunks-container');
chunksData.forEach((chunk, idx) => {{
  const div = document.createElement('div');
  div.className = 'chunk';
  div.id = `chunk-${{idx}}`;
  div.dataset.idx = idx;
  div.dataset.ci = chunk.ci;

  const confClass = chunk.conf === 'high' ? 'conf-high' : chunk.conf === 'medium' ? 'conf-medium' : 'conf-low';

  // Pick phase content
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
        <audio controls preload="none" src="${{opt.src}}"></audio>
      </div>`;
  }});
  pickHtml += '</div>';

  // Review phase content
  let reviewHtml = '<div class="review-phase" style="display:none">';
  reviewHtml += '<div class="review-player"><audio controls preload="none" id="review-audio-' + idx + '"></audio></div>';
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
    <div class="chunk-head">
      <span class="chunk-id">c${{String(chunk.ci).padStart(2,'0')}}</span>
      <span class="chunk-conf ${{confClass}}">${{chunk.conf}} | ${{chunk.options.length}} options</span>
    </div>
    <div class="chunk-text">${{chunk.text}}</div>
    ${{pickHtml}}
    ${{reviewHtml}}
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

  // In review phase, set audio src to picked version
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
  currentIdx = idx;
  document.querySelectorAll('.chunk').forEach(el => el.classList.remove('visible'));
  const el = document.getElementById(`chunk-${{idx}}`);
  el.classList.add('visible');
  el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  document.getElementById('status').textContent = `Chunk ${{idx + 1}}/${{totalChunks}}`;
}}

function pickOption(idx, oi) {{
  // Stop all audio in this chunk
  document.querySelectorAll(`#chunk-${{idx}} audio`).forEach(a => a.pause());

  humanPicks[idx] = oi;
  document.querySelectorAll(`#chunk-${{idx}} .option`).forEach(el => el.classList.remove('selected'));
  document.getElementById(`opt-${{idx}}-${{oi}}`).classList.add('selected');
  document.getElementById(`chunk-${{idx}}`).classList.add('picked');
  updateProgress();
  saveLocal();

  // Auto-advance after pick
  setTimeout(() => {{
    if (currentIdx + 1 < totalChunks) {{
      showChunk(currentIdx + 1);
      if (playing) {{
        // Play first option of next chunk
        setTimeout(() => {{
          const nextAudio = document.querySelector(`#chunk-${{currentIdx}} .option:first-child audio`);
          if (nextAudio) nextAudio.play();
        }}, 400);
      }}
    }} else {{
      // All picked — switch to review
      switchPhase('review');
    }}
  }}, 500);
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

  // Update label
  const label = document.getElementById(`vlabel-${{idx}}`);
  const tags = [...(verdicts[idx] || [])];
  label.textContent = tags.join(' + ');
  label.style.color = tags.includes('PASS') ? '#4ade80' : tags.length ? '#f87171' : '';

  updateProgress();
  saveLocal();

  // Auto-advance on PASS
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

  const pct = phase === 'pick'
    ? (picked / totalChunks * 100)
    : (reviewed / totalChunks * 100);
  document.getElementById('progress').style.width = pct + '%';
}}

function buildExport() {{
  const picks = [];
  chunksData.forEach((chunk, idx) => {{
    const oi = humanPicks[idx];
    if (oi === undefined) return;
    const opt = chunk.options[oi];
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

function saveLocal() {{
  try {{
    const state = {{
      picks: humanPicks,
      verdicts: Object.fromEntries(Object.entries(verdicts).map(([k,v]) => [k, [...v]])),
      severities: severities,
      phase: phase,
      currentIdx: currentIdx
    }};
    localStorage.setItem('unified-' + SESSION, JSON.stringify(state));
  }} catch(e) {{}}
}}

function restoreLocal() {{
  try {{
    const stored = localStorage.getItem('unified-' + SESSION);
    if (!stored) return false;
    const state = JSON.parse(stored);

    // Restore picks
    if (state.picks) {{
      for (const [idx, oi] of Object.entries(state.picks)) {{
        humanPicks[idx] = oi;
        const optEl = document.getElementById(`opt-${{idx}}-${{oi}}`);
        if (optEl) optEl.classList.add('selected');
        document.getElementById(`chunk-${{idx}}`).classList.add('picked');
      }}
    }}

    // Restore verdicts
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
    if (state.phase) switchPhase(state.phase);
    if (state.currentIdx) showChunk(state.currentIdx);

    updateProgress();
    return true;
  }} catch(e) {{ return false; }}
}}

// Audio ended → auto-advance in pick phase (play next option, then next chunk)
document.addEventListener('ended', (e) => {{
  if (e.target.tagName !== 'AUDIO') return;
  const chunkEl = e.target.closest('.chunk');
  if (!chunkEl) return;
  const idx = parseInt(chunkEl.dataset.idx);

  if (phase === 'pick') {{
    // Find which option this was
    const optEl = e.target.closest('.option');
    if (optEl) {{
      const oi = parseInt(optEl.dataset.oi);
      const nextOpt = chunkEl.querySelector(`[data-oi="${{oi + 1}}"] audio`);
      if (nextOpt) {{
        setTimeout(() => nextOpt.play(), 300);
        return;
      }}
    }}
    // All options played — wait for pick
  }} else {{
    // Review phase — auto-advance to next chunk
    if (playing && idx + 1 < totalChunks) {{
      setTimeout(() => {{
        showChunk(idx + 1);
        const nextAudio = document.getElementById(`review-audio-${{idx + 1}}`);
        if (nextAudio) nextAudio.play();
      }}, 500);
    }}
  }}
}}, true);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {{
  if (phase === 'pick') {{
    if (e.key === 'a' || e.key === 'A') {{ e.preventDefault(); pickOption(currentIdx, 0); }}
    if (e.key === 'b' || e.key === 'B') {{ e.preventDefault(); pickOption(currentIdx, 1); }}
    if (e.key === 'c' || e.key === 'C') {{ e.preventDefault(); pickOption(currentIdx, 2); }}
  }}
  if (phase === 'review') {{
    if (e.key === '1') {{ e.preventDefault(); setVerdict(currentIdx, 'PASS'); }}
    if (e.key === '2') {{ e.preventDefault(); setVerdict(currentIdx, 'ECHO'); }}
    if (e.key === '3') {{ e.preventDefault(); setVerdict(currentIdx, 'HISS'); }}
    if (e.key === '4') {{ e.preventDefault(); setVerdict(currentIdx, 'VOICE'); }}
    if (e.key === '5') {{ e.preventDefault(); setVerdict(currentIdx, 'CUTOFF'); }}
    if (e.key === '6') {{ e.preventDefault(); setVerdict(currentIdx, 'BAD'); }}
  }}
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

// Init
if (!restoreLocal()) {{
  showChunk(0);
}}
updateProgress();

window.addEventListener('beforeunload', saveLocal);
</script>
</body>
</html>'''

    return html


def main():
    parser = argparse.ArgumentParser(description='Generate unified pick + review page')
    parser.add_argument('session_id', help='Session ID')
    parser.add_argument('--local', action='store_true', help='Use local file:// paths')
    parser.add_argument('--output', help='Output path')
    args = parser.parse_args()

    html = generate_unified_page(args.session_id, local=args.local)

    if args.output:
        out = Path(args.output)
    else:
        out = VAULT_DIR / args.session_id / "unified-review.html"

    out.write_text(html)
    print(f"Unified review page: {out}")
    print(f"\nWorkflow:")
    print(f"  1. PICK phase: listen to A/B/C per chunk, pick winner")
    print(f"  2. REVIEW phase: listen to picks back-to-back, verdict each")
    print(f"  3. Export JSON when done")
    print(f"\nKeys: A/B/C=pick | 1=PASS 2=ECHO 3=HISS 4=VOICE 5=CUTOFF 6=BAD | Space=pause | Enter/Arrow=next")


if __name__ == '__main__':
    main()
