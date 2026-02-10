# Vault Picker Debrief — Session 52: The Court of Your Mind

**Date:** 10 February 2026
**Status:** 66/66 chunks picked. Ready for `vault-assemble.py`.

---

## Table of Contents

1. [Session Overview](#1-session-overview)
2. [Architecture](#2-architecture)
3. [Vault Picker Code — Complete Final Version](#3-vault-picker-code--complete-final-version)
4. [Rebuild Script](#4-rebuild-script)
5. [Cloudflare Worker API](#5-cloudflare-worker-api)
6. [A/B Tournament Mechanic — How It Works](#6-ab-tournament-mechanic--how-it-works)
7. [The Court of Your Mind Build](#7-the-court-of-your-mind-build)
8. [Patterns Discovered](#8-patterns-discovered)
9. [Config, Paths, Environment](#9-config-paths-environment)
10. [Known Issues and Workarounds](#10-known-issues-and-workarounds)
11. [Bug History — The 7 Iterations](#11-bug-history--the-7-iterations)
12. [Final Picks Data](#12-final-picks-data)

---

## 1. Session Overview

Built the Vault Picker: a browser-based A/B comparison tool for human review of Fish Audio TTS candidates. Used to review session 52 ("The Court of Your Mind") — 66 chunks, ~1570 candidates total.

The picker went through 6-7 error iterations before reaching its final working state. The bugs were subtle (version 0 falsy comparisons, saveState exceptions blocking renders, tournament bracket requiring 4 clicks instead of 1, "reject both" semantics wrong) and cannot be reconstructed from description alone. The complete working code is captured below.

**Final stats:**
- 66/66 chunks picked
- 199 total individual rejections across all chunks
- Average 3.0 rejections per chunk
- 4 chunks picked on first pair (zero rejections)
- 12 chunks went 5+ deep
- Chunk 62 was the deepest at 17 rejections
- Chunk 53 required regeneration (all 20 original candidates filtered; 20 more generated, all still filtered; unfiltered and picked by ear — 3 deep)

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│  review.html (served from R2)                           │
│  ┌──────────┐ ┌──────────┐ ┌────────────────────────┐  │
│  │  CSS     │ │  HTML    │ │  chunkData (JSON)      │  │
│  │  (inline)│ │  (body)  │ │  66 chunks × ~25 cands │  │
│  └──────────┘ └──────────┘ └────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  JavaScript (A/B Picker v2)                      │   │
│  │  - loadState() → merge server + localStorage     │   │
│  │  - saveState() → immediate write to both         │   │
│  │  - pickSide('a'|'b'|'same') → one-click pick     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌─────────────┐ ┌───────────┐ ┌──────────────┐
   │ R2 (WAVs)   │ │ Worker API│ │ localStorage │
   │ media.salus │ │ vault-picks│ │ (browser)    │
   │ -mind.com   │ │ .salus-   │ │              │
   │             │ │ mind.com  │ │              │
   └─────────────┘ └───────────┘ └──────────────┘
```

**Files involved:**

| File | Location | Purpose |
|------|----------|---------|
| `review.html` | `content/audio-free/vault/52-the-court-of-your-mind/review.html` | Self-contained picker page (307KB, ~13,800 lines) |
| CSS source | `/tmp/ab_picker_css.txt` | Picker styles |
| HTML source | `/tmp/ab_picker_html.txt` | Body markup |
| JS source | `/tmp/ab_picker_js.js` | All picker logic |
| Rebuild script | `/tmp/rebuild_full_picker.py` | Assembles review.html from parts + metadata |
| Worker source | `workers/vault-picks/src/worker.js` | Cloudflare Worker for picks persistence |
| Worker config | `workers/vault-picks/wrangler.toml` | Worker deployment config |
| Chunk metadata | `content/audio-free/vault/52-the-court-of-your-mind/c{XX}/c{XX}_meta.json` | Per-chunk candidate data |

---

## 3. Vault Picker Code — Complete Final Version

### 3.1 CSS (`/tmp/ab_picker_css.txt`)

```html
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a12;color:#f0eefc;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:32px 20px;max-width:900px;margin:0 auto}
h1{font-size:1.3rem;font-weight:300;margin-bottom:4px}
.meta{font-size:.78rem;color:#888;margin-bottom:6px}
.save-status{font-size:.72rem;padding:3px 10px;border-radius:4px;margin-bottom:8px;display:inline-block}
.save-status.ok{background:rgba(52,211,153,.1);color:#34d399}
.save-status.saving{background:rgba(250,204,21,.1);color:#facc15}
.save-status.error{background:rgba(239,68,68,.1);color:#ef4444}
.progress{font-size:.82rem;color:#34d399;margin-bottom:16px}
.chunk-nav{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:20px;padding:12px;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:8px}
.chunk-nav button{width:36px;height:28px;border-radius:4px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:#888;cursor:pointer;font-size:.68rem;transition:all .15s}
.chunk-nav button:hover{background:rgba(255,255,255,.08);color:#f0eefc}
.chunk-nav button.picked-old{background:rgba(52,211,153,.15);border-color:rgba(52,211,153,.3);color:#34d399;font-weight:400}
.chunk-nav button.rejected{background:rgba(239,68,68,.25);border-color:#ef4444;color:#ef4444;font-weight:700}
.chunk-nav button.picked-a{background:#34d399;border-color:#34d399;color:#0a0a12;font-weight:700}
.chunk-nav button.picked-b{background:#f59e0b;border-color:#f59e0b;color:#0a0a12;font-weight:700}
.chunk-nav button.has-reject{background:rgba(239,68,68,.15);border-color:rgba(239,68,68,.3);color:#ef4444}
.chunk-nav button.current{outline:2px solid #f0eefc;outline-offset:1px}
.pick-toast{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) scale(0.8);background:#0f2a20;color:#34d399;border:2px solid #34d399;padding:20px 48px;border-radius:14px;font-size:1.3rem;font-weight:700;z-index:9999;pointer-events:none;opacity:0;transition:opacity .15s,transform .15s}
.pick-toast.show{opacity:1;transform:translate(-50%,-50%) scale(1)}
.pick-toast.reject{background:#2a0f0f;color:#ef4444;border-color:#ef4444}
.ab-header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px}
.ab-title{font-size:1rem;font-weight:500;color:#34d399}
.ab-badge{font-size:.72rem;padding:2px 8px;border-radius:4px;background:rgba(167,139,250,.12);color:#a78bfa}
.ab-text{font-size:.85rem;color:#999;font-style:italic;margin-bottom:14px;line-height:1.5}
.ab-notes{width:100%;padding:6px 10px;margin-bottom:14px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:6px;color:#ccc;font-size:.78rem;resize:vertical;min-height:28px}
.ab-notes::placeholder{color:#555}
.round-info{font-size:.78rem;color:#888;margin-bottom:12px;text-align:center}
.ab-compare{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.ab-side{padding:16px;background:rgba(255,255,255,.02);border:2px solid rgba(255,255,255,.08);border-radius:10px;text-align:center;transition:border-color .2s}
.ab-side:hover{border-color:rgba(255,255,255,.15)}
.ab-label{font-size:1.4rem;font-weight:700;margin-bottom:8px;letter-spacing:2px}
.ab-label.label-a{color:#60a5fa}
.ab-label.label-b{color:#f59e0b}
.ab-stats{font-size:.72rem;color:#777;margin-top:8px}
.ab-stats span{margin:0 6px}
.ab-stats .score{color:#34d399}
.ab-stats .dur{color:#a78bfa}
.ab-stats .tone{color:#f59e0b}
.ab-side audio{width:100%;margin:8px 0}
.ab-actions{display:flex;justify-content:center;gap:12px;margin-bottom:20px}
.ab-actions button{padding:10px 28px;border-radius:8px;border:2px solid;font-size:.9rem;font-weight:600;cursor:pointer;transition:all .15s}
.btn-a{background:rgba(96,165,250,.1);border-color:rgba(96,165,250,.3);color:#60a5fa}
.btn-a:hover{background:rgba(96,165,250,.2)}
.btn-same{background:rgba(255,255,255,.04);border-color:rgba(255,255,255,.12);color:#888}
.btn-same:hover{background:rgba(255,255,255,.08)}
.btn-b{background:rgba(245,158,11,.1);border-color:rgba(245,158,11,.3);color:#f59e0b}
.btn-b:hover{background:rgba(245,158,11,.2)}
.ab-result{text-align:center;padding:24px;background:rgba(52,211,153,.04);border:1px solid rgba(52,211,153,.15);border-radius:10px;margin-bottom:16px}
.ab-result .winner-label{font-size:1rem;color:#34d399;margin-bottom:8px}
.ab-result audio{width:80%;margin:10px 0}
.ab-result .winner-stats{font-size:.78rem;color:#888;margin-bottom:12px}
.btn-repick{padding:6px 16px;border-radius:6px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);color:#f0eefc;cursor:pointer;font-size:.78rem}
.btn-repick:hover{background:rgba(255,255,255,.08)}
.shortcuts{font-size:.72rem;color:#555;text-align:center;margin-top:12px}
.shortcuts kbd{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:3px;padding:1px 5px;font-family:inherit}
.export-bar{margin-top:36px;display:flex;gap:10px;align-items:center}
.export-bar button{padding:8px 20px;border-radius:7px;border:1px solid rgba(52,211,153,.3);background:rgba(52,211,153,.1);color:#34d399;cursor:pointer;font-size:.82rem;font-weight:500}
.export-bar button:hover{background:rgba(52,211,153,.18)}
.export-bar .status{font-size:.78rem;color:#888}
.summary{margin-top:16px;padding:14px;background:rgba(52,211,153,.04);border:1px solid rgba(52,211,153,.12);border-radius:8px;display:none}
.summary pre{white-space:pre-wrap;color:#ccc;font-size:.75rem}
</style>
```

### 3.2 HTML Body (`/tmp/ab_picker_html.txt`)

```html
<h1>Vault Picker &mdash; 52-the-court-of-your-mind</h1>
<p class="meta">A/B Tournament v2</p>
<p class="meta">Audio base: <input id="basePath" value="https://media.salus-mind.com/vault/52-the-court-of-your-mind" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:4px;color:#f0eefc;padding:2px 6px;font-size:.72rem;width:420px" onchange="updateBasePath()"></p>
<div class="save-status ok" id="saveStatus">Auto-save active</div>
<div class="progress" id="progress">0 / 0 picked</div>
<div class="chunk-nav" id="chunkNav"></div>
<div id="abArea"></div>
<div class="pick-toast" id="toast"></div>
<div class="export-bar">
  <button onclick="exportPicks()">Download picks.json</button>
  <button onclick="exportTxt()">Download TXT</button>
  <button onclick="playAllPicks()" id="btnPlayAll">Play All Picks</button>
  <span class="status" id="exportStatus"></span>
</div>
<div class="summary" id="summaryBox"><pre id="summaryJson"></pre></div>
<div id="debugLog" style="margin-top:16px;font-size:.7rem;color:#555;font-family:monospace"></div>
```

### 3.3 JavaScript — A/B Picker v2 (`/tmp/ab_picker_js.js`)

```javascript
// --- A/B Tournament Picker v2 (fixed: try/catch save, green toasts, version labels) ---
var PICKS_API = 'https://vault-picks.salus-mind.com';
var AUTH_TOKEN = 'salus-vault-2026';
var basePath = document.getElementById('basePath').value.replace(/\/+$/, '');
var initialState = {};
var abState = {};
var currentChunkArrayIdx = 0;
var pickCounter = 0;
var pickedThisSession = {}; // chunkIdx -> 'a' or 'b'

// --- Load state: MERGE remote + localStorage ---
async function loadState() {
  var serverState = {}, localState = {};
  try {
    if (PICKS_API && AUTH_TOKEN) {
      var resp = await fetch(PICKS_API + '/picks/' + SESSION_ID, {
        headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN }
      });
      if (resp.ok) {
        var data = await resp.json();
        if (data.picks && data.picks.length > 0) {
          for (var i = 0; i < data.picks.length; i++) {
            var p = data.picks[i];
            serverState[p.chunk] = { picked: p.picked, rejected: p.rejected || [], notes: p.notes || '', side: p.side || null };
          }
        }
      }
    }
  } catch (e) { console.warn('Remote load failed:', e); }

  try {
    var saved = localStorage.getItem('vault-picks-' + SESSION_ID);
    if (saved) localState = JSON.parse(saved);
  } catch (e) { console.warn('localStorage parse failed:', e); }

  initialState = {};
  var serverKeys = Object.keys(serverState);
  var localKeys = Object.keys(localState);
  var allKeys = {};
  for (var i = 0; i < serverKeys.length; i++) allKeys[serverKeys[i]] = true;
  for (var i = 0; i < localKeys.length; i++) allKeys[localKeys[i]] = true;

  var keys = Object.keys(allKeys);
  for (var i = 0; i < keys.length; i++) {
    var k = keys[i];
    var s = serverState[k] || {};
    var l = localState[k] || {};
    if (l.picked != null) initialState[k] = l;
    else if (s.picked != null) initialState[k] = s;
    else initialState[k] = ((s.rejected || []).length >= (l.rejected || []).length) ? s : l;
  }

  var src = serverKeys.length > 0 && localKeys.length > 0 ? 'Merged server+local' :
    serverKeys.length > 0 ? 'Loaded from server' :
    localKeys.length > 0 ? 'Loaded from localStorage' : 'No saved state';
  setSaveStatus('ok', src);
  logDebug('loadState: ' + keys.length + ' chunks loaded (' + src + ')');
}

function setSaveStatus(cls, text) {
  var el = document.getElementById('saveStatus');
  if (el) { el.className = 'save-status ' + cls; el.textContent = text; }
}

function logDebug(msg) {
  var el = document.getElementById('debugLog');
  if (el) el.textContent = msg;
  console.log('[picker] ' + msg);
}

function updateBasePath() {
  basePath = document.getElementById('basePath').value.replace(/\/+$/, '');
  renderChunk();
}

// --- All non-filtered candidates sorted by score ---
function getTop(chunk) {
  var result = [];
  for (var i = 0; i < chunk.candidates.length; i++) {
    if (!chunk.candidates[i].filtered) result.push(chunk.candidates[i]);
  }
  result.sort(function(a, b) { return b.score - a.score; });
  return result;
}

// --- Initialize tournament state ---
function initABState(chunkIdx, reset) {
  var chunk = null;
  for (var i = 0; i < chunkData.length; i++) {
    if (chunkData[i].idx === chunkIdx) { chunk = chunkData[i]; break; }
  }
  if (!chunk) return;

  var top5 = getTop(chunk);
  if (top5.length === 0) return;

  var saved = reset ? {} : (initialState[chunkIdx] || {});
  var notes = (abState[chunkIdx] && abState[chunkIdx].notes) || saved.notes || '';

  // If previously picked and not resetting
  if (!reset && saved.picked != null) {
    abState[chunkIdx] = { top5: top5, winner: saved.picked, rejected: saved.rejected || [], done: true, notes: notes, round: 0, side: saved.side || null };
    if (saved.side) pickedThisSession[chunkIdx] = saved.side;
    return;
  }

  var rejected = reset ? [] : (saved.rejected || []);
  var available = [];
  for (var i = 0; i < top5.length; i++) {
    if (rejected.indexOf(top5[i].v) === -1) available.push(top5[i]);
  }

  if (available.length === 0) {
    // All rejected — full reset
    abState[chunkIdx] = { top5: top5, champion: top5[0], challengerIdx: 1, winner: null, rejected: [], done: false, notes: notes, round: 1 };
  } else if (available.length === 1) {
    abState[chunkIdx] = { top5: top5, winner: available[0].v, rejected: rejected, done: true, notes: notes, round: 0 };
  } else {
    var challIdx = -1;
    for (var i = 0; i < top5.length; i++) {
      if (top5[i] === available[1]) { challIdx = i; break; }
    }
    abState[chunkIdx] = { top5: top5, champion: available[0], challengerIdx: challIdx, winner: null, rejected: rejected, done: false, notes: notes, round: 1 };
  }
}

// --- Render current chunk ---
function renderChunk() {
  var chunk = chunkData[currentChunkArrayIdx];
  var state = abState[chunk.idx];
  var area = document.getElementById('abArea');
  if (!area) { logDebug('ERROR: no abArea element'); return; }
  if (!state) { area.innerHTML = '<p style="color:#ef4444">No candidates for chunk ' + chunk.idx + '</p>'; return; }

  var html = '';
  html += '<div class="ab-header">';
  html += '<span class="ab-title">Chunk ' + chunk.idx + '</span>';
  html += '<span class="ab-badge">' + chunk.chars + ' chars' + (chunk.isOpening ? ' \u00b7 opening' : '') + (chunk.isClosing ? ' \u00b7 closing' : '') + '</span>';
  html += '</div>';
  html += '<div class="ab-text">\u201c' + chunk.text + '\u201d</div>';
  html += '<textarea class="ab-notes" id="notes-' + chunk.idx + '" placeholder="Notes..." oninput="updateNotes(' + chunk.idx + ')">' + (state.notes || '') + '</textarea>';

  if (state.done && state.winner != null) {
    // Winner display
    var w = null;
    for (var i = 0; i < state.top5.length; i++) {
      if (state.top5[i].v === state.winner) { w = state.top5[i]; break; }
    }
    html += '<div class="ab-result">';
    html += '<div class="winner-label">\u2705 Winner: v' + state.winner + '</div>';
    if (w) {
      html += '<audio controls preload="auto" src="' + basePath + '/' + w.file + '"></audio>';
      html += '<div class="winner-stats">';
      html += '<span class="score">Score: ' + w.score.toFixed(3) + '</span>';
      html += ' \u00b7 <span class="dur">' + w.dur.toFixed(1) + 's</span>';
      if (chunk.idx > 0) html += ' \u00b7 <span class="tone">Tonal: ' + w.tone.toFixed(4) + '</span>';
      html += '</div>';
    }
    html += '<button class="btn-repick" onclick="resetChunk(' + chunk.idx + ')">Re-pick this chunk</button>';
    html += '</div>';
  } else if (!state.done) {
    // A/B comparison
    var a = state.champion;
    var bIdx = state.challengerIdx;
    var b = (bIdx >= 0 && bIdx < state.top5.length) ? state.top5[bIdx] : null;

    if (!a || !b) {
      html += '<p style="color:#ef4444">Not enough candidates (a=' + !!a + ', b=' + !!b + ', challIdx=' + bIdx + ')</p>';
      area.innerHTML = html;
      return;
    }

    var remaining = 0;
    for (var ri = 0; ri < state.top5.length; ri++) {
      if (state.rejected.indexOf(state.top5[ri].v) === -1) remaining++;
    }
    html += '<div class="round-info">' + remaining + ' candidates remaining</div>';

    html += '<div class="ab-compare" id="abCompare">';
    // Side A (champion)
    html += '<div class="ab-side">';
    html += '<div class="ab-label label-a">A <span style="font-size:.6em;opacity:.7">(v' + a.v + ')</span></div>';
    html += '<audio controls preload="auto" src="' + basePath + '/' + a.file + '"></audio>';
    html += '<div class="ab-stats"><span class="score">' + a.score.toFixed(3) + '</span><span class="dur">' + a.dur.toFixed(1) + 's</span>';
    if (chunk.idx > 0) html += '<span class="tone">t' + a.tone.toFixed(4) + '</span>';
    html += '</div></div>';
    // Side B (challenger)
    html += '<div class="ab-side">';
    html += '<div class="ab-label label-b">B <span style="font-size:.6em;opacity:.7">(v' + b.v + ')</span></div>';
    html += '<audio controls preload="auto" src="' + basePath + '/' + b.file + '"></audio>';
    html += '<div class="ab-stats"><span class="score">' + b.score.toFixed(3) + '</span><span class="dur">' + b.dur.toFixed(1) + 's</span>';
    if (chunk.idx > 0) html += '<span class="tone">t' + b.tone.toFixed(4) + '</span>';
    html += '</div></div>';
    html += '</div>';

    html += '<div class="ab-actions">';
    html += '<button class="btn-a" onclick="pickSide(\'a\')">A wins (A)</button>';
    html += '<button class="btn-same" onclick="pickSide(\'same\')">Reject both (S)</button>';
    html += '<button class="btn-b" onclick="pickSide(\'b\')">B wins (B)</button>';
    html += '</div>';
    html += '<div class="shortcuts">Keyboard: <kbd>A</kbd> A wins \u00b7 <kbd>S</kbd> Reject both \u00b7 <kbd>B</kbd> B wins \u00b7 <kbd>\u2190</kbd><kbd>\u2192</kbd> Navigate</div>';
  } else {
    html += '<p style="color:#f59e0b">Chunk in unexpected state (done=' + state.done + ', winner=' + state.winner + ')</p>';
  }

  area.innerHTML = html;

  // Flash animation on the compare area
  var cmp = document.getElementById('abCompare');
  if (cmp) {
    cmp.style.opacity = '0.5';
    setTimeout(function() { cmp.style.opacity = '1'; }, 50);
  }

  // Update nav highlight
  var navBtns = document.querySelectorAll('.chunk-nav button');
  for (var i = 0; i < navBtns.length; i++) navBtns[i].classList.remove('current');
  var navBtn = document.getElementById('nav-' + chunk.idx);
  if (navBtn) navBtn.classList.add('current');

  logDebug('Rendered chunk ' + chunk.idx + (state.done ? ' (done, winner=v' + state.winner + ')' : ' (round ' + state.round + ', A=v' + (state.champion ? state.champion.v : '?') + ' vs B=v' + ((state.top5[state.challengerIdx] || {}).v || '?') + ')'));
}

// --- Tournament: pick a side ---
function pickSide(side) {
  var chunk = chunkData[currentChunkArrayIdx];
  var state = abState[chunk.idx];

  if (!state) { logDebug('pickSide: no state for chunk ' + chunk.idx); return; }
  if (state.done) { logDebug('pickSide: chunk ' + chunk.idx + ' already done'); return; }

  var a = state.champion;
  var b = state.top5[state.challengerIdx];

  if (!a || !b) { logDebug('pickSide: missing a or b'); return; }

  pickCounter++;

  if (side === 'same') {
    // REJECT BOTH — neither wins
    state.rejected.push(a.v);
    state.rejected.push(b.v);
    showToast('Rejected both v' + a.v + ' + v' + b.v);

    // Find next TWO non-rejected candidates
    var remaining = [];
    for (var i = 0; i < state.top5.length; i++) {
      if (state.rejected.indexOf(state.top5[i].v) === -1) remaining.push(i);
    }

    if (remaining.length === 0) {
      // All rejected — no winner
      state.done = true;
      state.winner = null;
      state.round = 0;
      logDebug('All candidates rejected for chunk ' + chunk.idx);
      showToast('No winner \u2014 all rejected');
    } else if (remaining.length === 1) {
      // Only one left — auto-wins
      state.winner = state.top5[remaining[0]].v;
      state.done = true;
      state.round = 0;
      pickedThisSession[chunk.idx] = 'a';
      logDebug('Last candidate wins chunk ' + chunk.idx + ': v' + state.winner);
      showToast('PICKED: v' + state.winner + ' (last standing)');
    } else {
      // Remaining candidates exist — queue them, advance to next chunk
      state.champion = state.top5[remaining[0]];
      state.challengerIdx = remaining[1];
      state.round = (state.round || 0) + 1;
      logDebug('Both rejected, ' + remaining.length + ' remain. Moving to next chunk.');
    }

    // Auto-advance after reject both
    try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }
    renderChunk();
    setTimeout(function() {
      for (var i = currentChunkArrayIdx + 1; i < chunkData.length; i++) {
        if (abState[chunkData[i].idx] && !abState[chunkData[i].idx].done && !(abState[chunkData[i].idx].rejected && abState[chunkData[i].idx].rejected.length > 0)) {
          currentChunkArrayIdx = i;
          renderChunk();
          return;
        }
      }
    }, 600);
    return;
  } else {
    // A wins or B wins — PICK IMMEDIATELY
    var winner = (side === 'a') ? a : b;
    var loser = (side === 'a') ? b : a;

    state.rejected.push(loser.v);
    state.winner = winner.v;
    state.done = true;
    state.round = 0;
    pickedThisSession[chunk.idx] = side;
    logDebug('Picked v' + winner.v + ' for chunk ' + chunk.idx);
    showToast('PICKED: v' + winner.v);
  }

  // Save with try/catch so rendering always happens
  try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }

  // Always render regardless of save success
  renderChunk();

  // Auto-advance to next unpicked chunk after tournament completes
  if (state.done && state.winner != null) {
    setTimeout(function() {
      for (var i = currentChunkArrayIdx + 1; i < chunkData.length; i++) {
        if (abState[chunkData[i].idx] && !abState[chunkData[i].idx].done) {
          currentChunkArrayIdx = i;
          renderChunk();
          return;
        }
      }
    }, 800);
  }
}

function resetChunk(chunkIdx) {
  initABState(chunkIdx, true);
  try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }
  renderChunk();
}

function updateNotes(chunkIdx) {
  var el = document.getElementById('notes-' + chunkIdx);
  if (el && abState[chunkIdx]) {
    abState[chunkIdx].notes = el.value;
    try { saveState(); } catch (e) {}
  }
}

function goToChunk(arrayIdx) {
  if (arrayIdx >= 0 && arrayIdx < chunkData.length) {
    currentChunkArrayIdx = arrayIdx;
    renderChunk();
  }
}

function showToast(text) {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = text;
  t.className = 'pick-toast show';
  setTimeout(function() { t.className = 'pick-toast'; }, 900);
}

// --- Collect picks from abState ---
function collectPicks() {
  var picks = { session: SESSION_ID, reviewed: new Date().toISOString(), picks: [] };
  for (var i = 0; i < chunkData.length; i++) {
    var c = chunkData[i];
    var s = abState[c.idx] || {};
    var winnerFile = null;
    if (s.winner != null && s.top5) {
      for (var j = 0; j < s.top5.length; j++) {
        if (s.top5[j].v === s.winner) { winnerFile = s.top5[j].file; break; }
      }
    }
    picks.picks.push({
      chunk: c.idx,
      text: c.text,
      picked: s.winner != null ? s.winner : null,
      picked_file: winnerFile,
      rejected: s.rejected || [],
      notes: s.notes || '',
      side: pickedThisSession[c.idx] || s.side || null
    });
  }
  return picks;
}

// --- Save: immediate, no debounce ---
function saveState() {
  var picks = collectPicks();
  var ls = {};
  for (var i = 0; i < picks.picks.length; i++) {
    var p = picks.picks[i];
    ls[p.chunk] = { picked: p.picked, rejected: p.rejected, notes: p.notes, side: p.side };
  }
  try {
    localStorage.setItem('vault-picks-' + SESSION_ID, JSON.stringify(ls));
  } catch (e) {
    console.warn('localStorage write failed:', e);
  }
  updateProgress();
  updateChunkNav();
  setSaveStatus('saving', 'Saving...');
  saveRemote(picks);
}

async function saveRemote(picks) {
  if (!PICKS_API || !AUTH_TOKEN) { setSaveStatus('ok', 'Local only'); return; }
  try {
    var resp = await fetch(PICKS_API + '/picks/' + SESSION_ID, {
      method: 'PUT',
      headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify(picks)
    });
    setSaveStatus(resp.ok ? 'ok' : 'error', resp.ok ? 'Saved ' + new Date().toLocaleTimeString() : 'Save failed: ' + resp.status);
  } catch (e) { setSaveStatus('error', 'Save failed: ' + e.message); }
}

function updateProgress() {
  var n = 0;
  for (var i = 0; i < chunkData.length; i++) {
    var s = abState[chunkData[i].idx];
    if (s && s.done && s.winner != null) n++;
  }
  var el = document.getElementById('progress');
  if (el) el.textContent = n + ' / ' + chunkData.length + ' picked';
}

function updateChunkNav() {
  for (var i = 0; i < chunkData.length; i++) {
    var c = chunkData[i];
    var btn = document.getElementById('nav-' + c.idx);
    if (!btn) continue;
    btn.className = '';
    if (i === currentChunkArrayIdx) btn.classList.add('current');
    var s = abState[c.idx];
    if (s && s.done && s.winner != null) {
      var ps = pickedThisSession[c.idx];
      btn.classList.add(ps ? (ps === 'b' ? 'picked-b' : 'picked-a') : 'picked-old');
    } else if (s && s.rejected && s.rejected.length > 0) {
      btn.classList.add('rejected');
    }
  }
}

// --- Export ---
function exportPicks() {
  var picks = collectPicks();
  var json = JSON.stringify(picks, null, 2);
  var blob = new Blob([json], { type: 'application/json' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION_ID + '-vault-picks.json';
  a.click();
  document.getElementById('exportStatus').textContent = 'Downloaded!';
  document.getElementById('summaryBox').style.display = 'block';
  document.getElementById('summaryJson').textContent = json;
}

function exportTxt() {
  var picks = collectPicks();
  var txt = 'VAULT PICKS: ' + picks.session + '\nDate: ' + picks.reviewed + '\n\n';
  for (var i = 0; i < picks.picks.length; i++) {
    var p = picks.picks[i];
    txt += 'Chunk ' + p.chunk + ': picked v' + (p.picked != null ? p.picked : 'NONE') + ' (' + (p.picked_file || 'none') + ')\n';
    txt += '  Text: "' + p.text + '"\n';
    if (p.notes) txt += '  Notes: ' + p.notes + '\n';
    if (p.rejected.length) txt += '  Rejected: ' + p.rejected.map(function(v) { return 'v' + v; }).join(', ') + '\n';
    txt += '\n';
  }
  var blob = new Blob([txt], { type: 'text/plain' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION_ID + '-vault-picks.txt';
  a.click();
}

async function playAllPicks() {
  var btn = document.getElementById('btnPlayAll');
  if (btn) btn.textContent = 'Playing...';
  for (var i = 0; i < chunkData.length; i++) {
    var c = chunkData[i];
    var s = abState[c.idx];
    if (!s || s.winner == null || !s.top5) continue;
    var w = null;
    for (var j = 0; j < s.top5.length; j++) {
      if (s.top5[j].v === s.winner) { w = s.top5[j]; break; }
    }
    if (!w) continue;
    var audio = new Audio(basePath + '/' + w.file);
    audio.play();
    await new Promise(function(r) { audio.onended = r; });
    await new Promise(function(r) { setTimeout(r, 800); });
  }
  if (btn) btn.textContent = 'Play All Picks';
}

// --- Keyboard shortcuts ---
document.addEventListener('keydown', function(e) {
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  if (e.key === 'a' || e.key === 'A') pickSide('a');
  else if (e.key === 'b' || e.key === 'B') pickSide('b');
  else if (e.key === 's' || e.key === 'S') pickSide('same');
  else if (e.key === 'ArrowLeft') goToChunk(currentChunkArrayIdx - 1);
  else if (e.key === 'ArrowRight') goToChunk(currentChunkArrayIdx + 1);
});

// --- Init ---
async function init() {
  logDebug('Initializing...');
  await loadState();

  var nav = document.getElementById('chunkNav');
  for (var i = 0; i < chunkData.length; i++) {
    (function(idx) {
      var btn = document.createElement('button');
      btn.id = 'nav-' + chunkData[idx].idx;
      btn.textContent = chunkData[idx].idx;
      btn.onclick = function() { goToChunk(idx); };
      nav.appendChild(btn);
    })(i);
  }

  for (var i = 0; i < chunkData.length; i++) {
    initABState(chunkData[i].idx, false);
  }

  // Start at first unpicked chunk
  var first = -1;
  for (var i = 0; i < chunkData.length; i++) {
    if (!abState[chunkData[i].idx] || !abState[chunkData[i].idx].done) { first = i; break; }
  }
  if (first >= 0) currentChunkArrayIdx = first;

  updateProgress();
  updateChunkNav();
  renderChunk();
  logDebug('Ready. ' + chunkData.length + ' chunks loaded.');
}

init();
```

---

## 4. Rebuild Script

File: `/tmp/rebuild_full_picker.py`

This script assembles `review.html` from the three source files (CSS, HTML, JS) plus all chunk metadata files. Run it any time you change the picker code.

```python
#!/usr/bin/env python3
"""Rebuild review.html: fresh CSS + HTML + all 66 chunks + new v2 JS."""

import json, glob, os

VAULT = '/Users/scottripley/salus-website/content/audio-free/vault/52-the-court-of-your-mind'
REVIEW = os.path.join(VAULT, 'review.html')

# Read all chunk metadata files
chunk_dirs = sorted(glob.glob(os.path.join(VAULT, 'c[0-9][0-9]')))
print(f"Found {len(chunk_dirs)} chunk directories")

all_chunks = []
for cdir in chunk_dirs:
    dirname = os.path.basename(cdir)
    meta_file = os.path.join(cdir, f"{dirname}_meta.json")
    if not os.path.exists(meta_file):
        print(f"WARNING: No metadata for {dirname}")
        continue

    with open(meta_file, 'r') as f:
        meta = json.load(f)

    candidates = []
    for c in meta['candidates']:
        candidates.append({
            "v": c['version'],
            "file": f"{dirname}/{c['filename']}",
            "score": round(c['composite_score'], 4),
            "dur": round(c['duration_seconds'], 2),
            "tone": round(c.get('tonal_distance_to_prev', 0), 6),
            "filtered": c['filtered']
        })

    all_chunks.append({
        "idx": meta['chunk_index'],
        "text": meta['text'],
        "chars": meta['char_count'],
        "isOpening": meta['is_opening'],
        "isClosing": meta['is_closing'],
        "candidates": candidates
    })

all_chunks.sort(key=lambda c: c['idx'])
print(f"Built chunkData with {len(all_chunks)} chunks")
total_candidates = sum(len(c['candidates']) for c in all_chunks)
print(f"Total candidates: {total_candidates}")

# Read the three replacement parts from temp files
with open('/tmp/ab_picker_css.txt', 'r') as f:
    css = f.read()
with open('/tmp/ab_picker_html.txt', 'r') as f:
    html_body = f.read()
with open('/tmp/ab_picker_js.js', 'r') as f:
    js = f.read()

# Build data section
data_json = json.dumps(all_chunks, indent=2)

# Assemble complete file from scratch
parts = []
parts.append('<!DOCTYPE html>\n')
parts.append('<html lang="en">\n')
parts.append('<head>\n')
parts.append('<meta charset="UTF-8">\n')
parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
parts.append('<title>Vault Picker — 52-the-court-of-your-mind</title>\n')
parts.append(css + '\n')
parts.append('</head>\n')
parts.append('<body>\n')
parts.append(html_body + '\n')
parts.append('\n<script>\n')
parts.append(f"var SESSION_ID = '52-the-court-of-your-mind';\n")
parts.append(f"var chunkData = {data_json};\n\n")
parts.append(js + '\n')
parts.append('</script>\n')
parts.append('</body>\n')
parts.append('</html>\n')

output = ''.join(parts)

with open(REVIEW, 'w') as f:
    f.write(output)

# Verify
with open(REVIEW, 'r') as f:
    final = f.read()

import re
chunk_count = len(re.findall(r'"idx":', final))
assert chunk_count == len(all_chunks), f"Expected {len(all_chunks)} chunks, found {chunk_count}"
assert 'Picker v2' in final, "Missing v2 marker"
assert 'try { saveState()' in final, "Missing try/catch saveState"
assert 'logDebug' in final, "Missing debug logging"
assert 'pickCounter' in final, "Missing pick counter"

line_count = final.count('\n')
print(f"Wrote {len(final):,} bytes, {line_count:,} lines")
print(f"Chunks in file: {chunk_count}")
print("All checks passed")
```

**To rebuild and upload:**
```bash
python3 /tmp/rebuild_full_picker.py
npx wrangler r2 object put "salus-mind/vault/52-the-court-of-your-mind/review.html" \
  --file=content/audio-free/vault/52-the-court-of-your-mind/review.html \
  --remote --content-type="text/html"
```

**To make it session-generic:** Change `VAULT` path and `SESSION_ID` in the script. The HTML title and basePath input also need updating.

---

## 5. Cloudflare Worker API

### Worker Source (`workers/vault-picks/src/worker.js`)

```javascript
/**
 * Vault Picks Worker — Cloudflare Worker for persisting picker page selections.
 *
 * GET  /picks/{session-id}  → returns picks.json from R2
 * PUT  /picks/{session-id}  → saves picks.json to R2
 *
 * Auth: Bearer token in Authorization header (matches AUTH_TOKEN env var).
 * CORS: Allows requests from salus-mind.com and media.salus-mind.com.
 */

export default {
  async fetch(request, env) {
    // CORS headers
    const origin = request.headers.get('Origin') || '';
    const allowedOrigins = [
      'https://salus-mind.com',
      'https://www.salus-mind.com',
      'https://media.salus-mind.com',
      'http://localhost',
      'null', // file:// origin
    ];
    const corsOrigin = allowedOrigins.includes(origin) ? origin : allowedOrigins[0];

    const corsHeaders = {
      'Access-Control-Allow-Origin': corsOrigin,
      'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Authorization, Content-Type',
      'Access-Control-Max-Age': '86400',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // Parse path: /picks/{session-id}
    const url = new URL(request.url);
    const match = url.pathname.match(/^\/picks\/([a-zA-Z0-9_-]+)$/);
    if (!match) {
      return new Response(JSON.stringify({ error: 'Invalid path. Use /picks/{session-id}' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const sessionId = match[1];
    const r2Key = `vault/${sessionId}/picks/picks.json`;

    // Auth check
    const authHeader = request.headers.get('Authorization') || '';
    const token = authHeader.replace('Bearer ', '');
    if (token !== env.AUTH_TOKEN) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (request.method === 'GET') {
      const object = await env.VAULT_BUCKET.get(r2Key);
      if (!object) {
        return new Response(JSON.stringify({ picks: [], session: sessionId }), {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
      const data = await object.text();
      return new Response(data, {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (request.method === 'PUT') {
      const body = await request.text();
      try {
        JSON.parse(body);
      } catch {
        return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
      await env.VAULT_BUCKET.put(r2Key, body, {
        httpMetadata: { contentType: 'application/json' },
      });
      return new Response(JSON.stringify({ ok: true, key: r2Key }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  },
};
```

### Worker Config (`workers/vault-picks/wrangler.toml`)

```toml
name = "vault-picks"
main = "src/worker.js"
compatibility_date = "2024-01-01"

[[r2_buckets]]
binding = "VAULT_BUCKET"
bucket_name = "salus-mind"

[vars]
AUTH_TOKEN = "salus-vault-2026"

[[routes]]
pattern = "vault-picks.salus-mind.com/*"
custom_domain = true
```

### API Usage

```bash
# Read picks
curl -H "Authorization: Bearer salus-vault-2026" \
  "https://vault-picks.salus-mind.com/picks/52-the-court-of-your-mind"

# Write picks
curl -X PUT -H "Authorization: Bearer salus-vault-2026" \
  -H "Content-Type: application/json" \
  -d @picks.json \
  "https://vault-picks.salus-mind.com/picks/52-the-court-of-your-mind"
```

R2 storage key: `vault/{session-id}/picks/picks.json`

---

## 6. A/B Tournament Mechanic — How It Works

### Flow

1. **Page load:** `init()` calls `loadState()` which merges server (Worker API) + localStorage picks. Merge rule: if localStorage has a pick, prefer it; else if server has a pick, prefer it; else keep whichever has more rejections.

2. **For each chunk:** `initABState()` builds the candidate list (ALL non-filtered candidates sorted by score descending), checks saved state, and either marks the chunk as done (if previously picked) or sets up champion (rank 1) vs challenger (rank 2) for A/B comparison.

3. **Chunk grid:** Top of page shows numbered buttons 0-65. Colors:
   - **Bright green** (`picked-a`): Picked this session, A side won
   - **Amber** (`picked-b`): Picked this session, B side won
   - **Dim green** (`picked-old`): Picked in a previous session (loaded from save)
   - **Red** (`rejected`): Rejected both, no winner yet
   - **Grey** (default): Untouched
   - **White outline** (`current`): Currently viewing

4. **Picking (one click):**
   - **A wins:** Champion (left side) wins immediately. Challenger goes to rejected list. Chunk marked done. Auto-advances to next unpicked chunk after 800ms.
   - **B wins:** Challenger (right side) wins immediately. Champion goes to rejected list. Chunk marked done. Auto-advances.
   - **Reject both:** BOTH champion and challenger go to rejected list. Next two non-rejected candidates are loaded as the new champion/challenger. Nav square turns red. Page auto-advances to next unpicked chunk after 600ms. On return visit, the chunk shows the fresh pair.

5. **Exhaustion:** If all candidates are rejected, chunk shows "No winner — all rejected". If only one candidate remains, it auto-wins.

6. **Re-pick:** Each completed chunk has a "Re-pick this chunk" button that resets the tournament (clears rejections, starts fresh with all candidates).

7. **Save:** Every pick immediately saves to both localStorage and the Worker API (no debounce). All save calls wrapped in try/catch to prevent render blocking.

### picks.json Output Format

```json
{
  "session": "52-the-court-of-your-mind",
  "reviewed": "2026-02-10T10:46:51.040Z",
  "picks": [
    {
      "chunk": 0,
      "text": "Your mind has been busy building a case against you.",
      "picked": 16,
      "picked_file": "c00/c00_v16.wav",
      "rejected": [13, 28, 22],
      "notes": "",
      "side": "a"
    },
    ...
  ]
}
```

Fields per chunk:
- `chunk`: chunk index (0-65)
- `text`: the narration text
- `picked`: version number of winner (integer), or `null` if no winner
- `picked_file`: relative path to WAV (e.g. `c00/c00_v16.wav`), or `null`
- `rejected`: array of rejected version numbers
- `notes`: free-text notes entered by reviewer
- `side`: `"a"`, `"b"`, or `null` (which side won — null means loaded from previous session without side tracking)

### Merge Strategy (loadState)

On page load, picks are loaded from BOTH the Worker API and localStorage, then merged per-chunk:

```
if (localStorage has a pick for this chunk) → use localStorage
else if (server has a pick) → use server
else → use whichever has more rejections
```

This ensures: if you pick on device A and then open on device B, the pick is there. If you pick on device B while offline, it takes precedence when you go online.

### Side Tracking

The `side` field records whether the user chose A or B. This persists to the Worker API so that on page reload, nav buttons show the correct color (green for A, amber for B). Chunks loaded from a previous session without side tracking show as dim green (`picked-old`).

---

## 7. The Court of Your Mind Build

### Session Details

| Field | Value |
|-------|-------|
| Session ID | `52-the-court-of-your-mind` |
| Script | `content/scripts/52-the-court-of-your-mind.txt` |
| Category | stress |
| API Emotion | calm |
| Raw blocks | 60 |
| After preprocessing | 66 (6 blocks split) |
| Provider | Fish Audio |

### Preprocessing

6 blocks were split (all >300 chars):
- Block 1: 326ch → 2 fragments (140, 185)
- Block 33: 342ch → 2 fragments (183, 158)
- Block 41: 386ch → 2 fragments (188, 197)
- Block 46: 312ch → 2 fragments (177, 134)
- Block 53: 322ch → 2 fragments (135, 186)
- Block 57: 339ch → 2 fragments (167, 171)

### Candidate Counts

Standard counts (from `vault-builder.py`):
- 0-50 chars: 30 candidates (chunk 0 opening)
- 50-100 chars: 15 candidates
- 100-200 chars: 20 candidates
- 200-300 chars: 25 candidates

Total standard candidates generated: ~1330 across 66 chunks.
Pre-filter failures (score < 0.30): 91 candidates filtered.

### Chunk 53 — The Problem Chunk

Text: *"The judge closes the folder. Straightens the papers. Looks once more at the prosecution. Then speaks two words. Case dismissed."*

- 127 chars → standard allocation: 20 candidates
- All 20 candidates scored below 0.30 pre-filter threshold → ALL filtered → "No candidates" in picker
- Root cause: tonal distance penalty. The raw quality scores (q=) ranged 0.03–0.33 (reasonable), but tonal distance to chunk 52's best candidate crushed every composite score below 0.30.
- Fix: ran `vault-builder.py --only-chunks 53 --extra 20` to generate 20 more (v20-v39). All 40 still filtered.
- Final fix: unfiltered all candidates in `c53_meta.json` (`"filtered": false`), rebuilt picker, uploaded. Scott picked v11 after only 3 rejections.
- Lesson: the 0.30 pre-filter is too aggressive for chunks with high tonal distance to predecessor. The audio quality was fine — the score was wrong.

### Chunk 62 — Deepest Rejections

Text: *"Whenever the prosecution returns, and it will, it always does, remember this. The defence has something the prosecution never will. A record. Every time you showed up."*

- 17 rejections (deepest in the session)
- 167 chars, near-closing, emotionally loaded
- Eventually picked v0 (the lowest-scored candidate!)
- Lesson: composite score rankings did not predict human preference at all for this chunk.

### Status

- **66/66 picked** as of 2026-02-10T10:46:51Z
- Ready for `vault-assemble.py`
- Picks stored in Worker API and localStorage

---

## 8. Patterns Discovered

### Rejection Depth Distribution

| Depth | Count | % |
|-------|-------|---|
| 0 (first pair) | 4 | 6% |
| 1-2 | 29 | 44% |
| 3-4 | 21 | 32% |
| 5-9 | 10 | 15% |
| 10+ | 2 | 3% |

### Deep Rejection Causes

**1. Long, complex sentences (>200 chars):**
- Chunks 38 (261ch, 9 rejects) and 41 (252ch, 9 rejects)
- Fish struggles to maintain consistent tone across long narrative passages
- The `calm` emotion setting may fight against the dramatic delivery these passages need

**2. Emotional intensity:**
- Chunks 22 ("land in your chest"), 62 ("prosecution returns"), 57 ("you become the judge")
- Dramatically charged lines where Fish's calm delivery creates a mismatch between content and tone

**3. Short punchy lines demanding gravitas:**
- Chunk 40 ("Hold that memory. That is evidence." — 7 rejects)
- Chunk 32 ("Search your memory now." — 5 rejects)
- Short but require weight and authority. Fish goes either flat or breathy on these.

**4. NOT trigger-word driven:**
- Only 1 of the 12 deep-rejection chunks (chunk 46) contains a known Fish problem word ("feel")
- The established problem word list (settling, stillness, feel, peace, ease, deeply, etc.) does NOT predict rejection depth
- Rejection correlates more with passage character (emotional weight, dramatic tone, sentence complexity) than with specific trigger words

### Scoring System Findings

**Pre-filter at 0.30 is too aggressive for high tonal-distance chunks:**
- Chunk 53: all 40 candidates filtered. Raw quality was fine (q=0.03-0.33). Tonal distance penalty crushed composites.
- The tonal distance is weighted 50x in the composite — when the preceding chunk has a very different tonal profile, every candidate for the next chunk gets hammered regardless of actual audio quality.

**Composite score does not predict human preference:**
- Chunk 62: picked v0, which had the LOWEST composite score (-0.427)
- Average rejections per chunk was 3.0 — meaning the top-2 ranked candidates were rejected ~half the time
- The scoring system correctly identifies obviously bad audio (echo, hiss) but does not reliably rank "good" candidates in preference order

---

## 9. Config, Paths, Environment

### File Locations

```
Vault root:    content/audio-free/vault/52-the-court-of-your-mind/
Chunk dirs:    content/audio-free/vault/52-the-court-of-your-mind/c00/ through c65/
Metadata:      c{XX}/c{XX}_meta.json
Candidates:    c{XX}/c{XX}_v{NN}.wav
Picker page:   content/audio-free/vault/52-the-court-of-your-mind/review.html
Script:        content/scripts/52-the-court-of-your-mind.txt
Worker source: workers/vault-picks/src/worker.js
Worker config: workers/vault-picks/wrangler.toml
```

### R2 URLs

```
Picker:     https://media.salus-mind.com/vault/52-the-court-of-your-mind/review.html
Audio:      https://media.salus-mind.com/vault/52-the-court-of-your-mind/c{XX}/c{XX}_v{NN}.wav
Picks JSON: vault/52-the-court-of-your-mind/picks/picks.json (R2 key, accessed via Worker)
```

### API Settings

```
Worker URL:  https://vault-picks.salus-mind.com
Auth token:  salus-vault-2026 (Bearer auth)
R2 bucket:   salus-mind
Fish voice:  0165567b33324f518b02336ad232e31a (Marco, V3-HD, calm)
```

### Temp Files (needed for rebuild)

```
/tmp/ab_picker_css.txt    — CSS
/tmp/ab_picker_html.txt   — HTML body
/tmp/ab_picker_js.js      — JavaScript
/tmp/rebuild_full_picker.py — Assembly script
```

**WARNING:** These are in `/tmp/` and will be lost on reboot. Copy them somewhere persistent if needed. All code is also captured in this document.

### Candidate Metadata Format (`c{XX}_meta.json`)

```json
{
  "chunk_index": 53,
  "text": "The judge closes the folder...",
  "char_count": 127,
  "is_opening": false,
  "is_closing": false,
  "candidates": [
    {
      "version": 0,
      "filename": "c53_v00.wav",
      "duration_seconds": 10.5,
      "composite_score": -0.4274,
      "tonal_distance_to_prev": 0.0046,
      "filtered": false
    }
  ]
}
```

### vault-builder.py CLI

```bash
# Single session
python3 vault-builder.py content/scripts/52-the-court-of-your-mind.txt

# Specific chunks only
python3 vault-builder.py content/scripts/52-the-court-of-your-mind.txt --only-chunks 53

# Extra candidates (adds N on top of standard count)
python3 vault-builder.py content/scripts/52-the-court-of-your-mind.txt --only-chunks 53 --extra 20

# Dry run
python3 vault-builder.py content/scripts/52-the-court-of-your-mind.txt --dry-run

# Skip R2 upload
python3 vault-builder.py content/scripts/52-the-court-of-your-mind.txt --no-upload
```

---

## 10. Known Issues and Workarounds

### Critical

1. **Temp files in `/tmp/`**: The CSS, HTML, JS, and rebuild script are all in `/tmp/`. They will be lost on reboot. The code is captured in this document and in the assembled `review.html`, but the separate source files need to be copied to a persistent location for future use.

2. **Pre-filter at 0.30 is too aggressive**: Chunk 53 demonstrated this. High tonal-distance chunks get all candidates filtered even when audio quality is acceptable. Workaround: manually unfilter in `c{XX}_meta.json` and rebuild. Proper fix: either lower the threshold or reduce the tonal distance weight (currently 50x) in the composite score.

3. **Tonal distance penalty dominates composite**: The 50x weight on tonal distance means chunks following a tonally dissimilar predecessor will always score poorly, regardless of raw audio quality. This needs recalibration.

### Moderate

4. **Side tracking incomplete on first-pass picks**: Chunks picked before the side-tracking feature was added (early in the session) show `side: null`. This means those chunks appear as dim green (`picked-old`) instead of bright green/amber. Does not affect functionality or picks.json output — the winner version is correctly recorded.

5. **`vault-builder.py` stdout is buffered**: When run from a background task, Python's print buffering means no output appears until the process completes. Add `-u` flag (`python3 -u vault-builder.py ...`) for unbuffered output, or run in foreground.

6. **`npx` not available in for-loops**: Shell PATH doesn't persist into loops in the Claude Code bash environment. Workaround: use Python subprocess with explicit PATH, or run uploads individually. Example:
   ```python
   import subprocess, os
   env = os.environ.copy()
   env['PATH'] = '/opt/homebrew/bin:' + env.get('PATH','')
   subprocess.run(['npx', 'wrangler', 'r2', 'object', 'put', key, '--file', path,
                    '--remote', '--content-type', 'audio/wav'], env=env)
   ```

### Low

7. **Reject-both auto-advance skips rejected chunks**: After reject-both, the auto-advance goes to the next chunk that has no rejections. This means if you reject-both on chunk 4 and chunk 5 was also previously rejected, it skips to chunk 6. On second pass, you navigate to red chunks manually.

8. **Play All Picks plays sequentially**: No skip/pause/stop control. If you start it accidentally, you have to close the tab.

9. **`has-reject` CSS class unused**: The CSS contains `.chunk-nav button.has-reject` but the JS uses `.rejected` for rejected chunks. The `has-reject` class is dead CSS from an earlier iteration.

---

## 11. Bug History — The 7 Iterations

These are the bugs encountered during development, in order. Understanding them prevents re-introduction.

### Bug 1: Only 11 chunks in review.html
**Cause:** `vault-builder.py --only-chunks` mode only writes regenerated chunks to the picker page, not all chunks.
**Fix:** Created `rebuild_full_picker.py` that reads ALL chunk metadata directories.

### Bug 2: Nav square turns red on A wins
**Cause:** `updateChunkNav()` was using `has-reject` class for any chunk with rejections. Tournament rounds count rejected losers, so even won chunks had rejections.
**Fix:** Changed to only show red for chunks that are done with no winner, and later to `rejected` class for reject-both chunks.

### Bug 3: B wins and Reject Both don't update UI
**Cause:** `saveState()` was throwing an exception (likely localStorage quota or structure issue), which blocked `renderChunk()` from executing.
**Fix:** Wrapped ALL `saveState()` calls in try/catch. `renderChunk()` always executes regardless of save success.

### Bug 4: Red toast for B wins
**Cause:** `showToast('B wins', true)` was passing `isReject=true`, which applied red styling.
**Fix:** Removed the isReject parameter entirely. All toasts are green.

### Bug 5: Version 0 picks lost
**Cause:** `s.winner || null` evaluates to `null` when `winner` is `0` (falsy in JavaScript).
**Fix:** Changed to `s.winner != null ? s.winner : null` throughout all code.

### Bug 6: "Both same" meant wrong thing
**Cause:** Implemented as "keep the champion (A), reject the challenger" — i.e., a soft A-wins.
**Scott's meaning:** Reject BOTH candidates. Neither wins. Move to next pair from remaining pool.
**Fix:** Complete rewrite of the `same` branch in `pickSide()`. Both candidates go to rejected list. Next two non-rejected candidates are loaded. Nav turns red.

### Bug 7: Required 4 clicks to pick
**Cause:** Tournament bracket system — champion had to beat 4 challengers before being declared winner.
**Scott's expectation:** One click. A wins = done. B wins = done.
**Fix:** Removed multi-round tournament. A wins or B wins immediately sets winner and marks chunk done.

### Supplementary fixes (not full iterations but required):
- **Amber on refresh:** Side info (a/b) was only in memory. Added `side` field to Worker API save/load.
- **Reject-both no color change:** Nav square stayed grey. Added `rejected` class application in `updateChunkNav()`.
- **Reject-both no advance:** Page stayed on current chunk. Added `setTimeout` auto-advance after reject-both.
- **Only top 5 candidates:** `getTop()` returned only top 5. Changed to return ALL non-filtered candidates so reject-both cycles through the full pool.

---

## 12. Final Picks Data

### Summary Statistics

| Metric | Value |
|--------|-------|
| Total chunks | 66 |
| Picked | 66 (100%) |
| Total rejections | 199 |
| Avg rejections/chunk | 3.0 |
| Zero-rejection picks | 4 (6%) |
| Deep rejections (5+) | 12 (18%) |
| Deepest | Chunk 62 (17 rejections) |

### All Picks

| Chunk | Picked | Rejects | Side | Text (60 chars) |
|-------|--------|---------|------|------------------|
| 0 | v16 | 3 | a | Your mind has been busy building a case against you. |
| 1 | v17 | 0 | - | It happens to all of us. A thought arrives, uninvited... |
| 2 | v14 | 4 | - | And before you can question it, the thought has taken the... |
| 3 | v12 | 4 | - | This is something most of us carry and never examine... |
| 4 | v24 | 7 | b | Today we are going to do something different... |
| 5 | v10 | 4 | - | Sit somewhere comfortable. Let your hands rest... |
| 6 | v1 | 4 | - | Breathe in through your nose now... |
| 7 | v4 | 4 | - | And let it go through your mouth... |
| 8 | v1 | 1 | - | One more now. In through your nose... |
| 9 | v11 | 5 | a | And out. Good. Let your breathing return... |
| 10 | v13 | 1 | - | Now I want you to picture a courtroom... |
| 11 | v11 | 1 | - | A gallery behind you, mostly empty... |
| 12 | v6 | 1 | - | You are sitting in that chair... |
| 13 | v2 | 3 | - | At the table on your left sits the prosecution... |
| 14 | v10 | 1 | - | The one that tightens your chest before a meeting... |
| 15 | v5 | 1 | - | This voice does not whisper. It states... |
| 16 | v1 | 1 | - | And because the voice is so certain... |
| 17 | v23 | 1 | - | At the table on your right sits the defence... |
| 18 | v6 | 1 | - | The judge looks to the prosecution and nods... |
| 19 | v18 | 1 | - | The prosecution stands. Confident. Practised... |
| 20 | v2 | 1 | - | This person is not capable... |
| 21 | v4 | 1 | - | The prosecution pauses, then continues... |
| 22 | v11 | 11 | b | Strong words. Certain words... |
| 23 | v7 | 1 | - | The judge turns to the table on the right... |
| 24 | v5 | 0 | - | The defence does not stand immediately... |
| 25 | v14 | 1 | - | Can you provide specific evidence... |
| 26 | v3 | 4 | - | The courtroom goes quiet... |
| 27 | v28 | 3 | - | The prosecution clears its throat... |
| 28 | v15 | 3 | b | Because the prosecution has never needed evidence... |
| 29 | v3 | 5 | b | The defence speaks again. Without hostility... |
| 30 | v2 | 1 | b | Think about that now. Genuinely... |
| 31 | v18 | 3 | b | When did the thing you feared most actually come true... |
| 32 | v3 | 5 | b | Search your memory now... |
| 33 | v19 | 1 | b | What most people discover... |
| 34 | v19 | 1 | b | Maybe there was a time. Perhaps one... |
| 35 | v25 | 4 | a | And from those few moments, it has built an entire case... |
| 36 | v30 | 3 | b | The defence turns to the judge... |
| 37 | v4 | 3 | b | This person has shown up. Repeatedly... |
| 38 | v43 | 9 | b | I am going to ask you to do something now... |
| 39 | v8 | 3 | a | Let that specific memory surface now... |
| 40 | v1 | 7 | a | Hold that memory. That is evidence... |
| 41 | v26 | 9 | b | Now think of a time when you were certain... |
| 42 | v3 | 1 | a | That is exhibit two... |
| 43 | v19 | 3 | b | And one more. Think about the last time... |
| 44 | v18 | 4 | - | It might be a small thing. A boundary you held... |
| 45 | v14 | 1 | b | Exhibit three. Another fact... |
| 46 | v9 | 7 | b | The defence looks at the judge. Three pieces... |
| 47 | v7 | 3 | a | The prosecution offered predictions... |
| 48 | v6 | 1 | b | The prosecution describes a person who cannot cope... |
| 49 | v9 | 5 | b | Let that land. Not as a motivational speech... |
| 50 | v4 | 1 | b | You may not have handled it the way you wished... |
| 51 | v2 | 1 | b | The judge looks at the prosecution... |
| 52 | v1 | 1 | b | The prosecution does not. It never does... |
| 53 | v11 | 5 | b | The judge closes the folder... |
| 54 | v5 | 1 | a | The courtroom begins to empty... |
| 55 | v15 | 1 | b | Here is what I want you to take from this room... |
| 56 | v15 | 3 | b | But now you know something you did not know before... |
| 57 | v13 | 7 | a | That single question changes the entire dynamic... |
| 58 | v5 | 1 | b | And from that bench, you can look... |
| 59 | v7 | 1 | b | Breathe in through your nose now... |
| 60 | v16 | 1 | a | And let it out. Let the courtroom dissolve... |
| 61 | v18 | 1 | a | And if you want, keep one image from that room... |
| 62 | v0 | 17 | a | Whenever the prosecution returns... |
| 63 | v19 | 3 | a | Every time you were afraid and did it anyway... |
| 64 | v1 | 3 | b | When you are ready, let your eyes open... |
| 65 | v3 | 0 | - | Thank you for practising with Salus... |

---

## Next Step

Run `vault-assemble.py` to concatenate the 66 picked WAVs into the final session audio. This tool:

1. Reads `picks.json` from the Worker API (or from export)
2. Copies picked WAVs to `picks/c{XX}_pick.wav`
3. Applies 15ms cosine edge fades
4. Inserts silence pauses from script
5. Concatenates to WAV → whole-file loudnorm (I=-26, TP=-2, LRA=11)
6. Outputs WAV + 128kbps MP3 to `final/`
7. Runs 14 QA gates
8. Builds report

Note: `vault-assemble.py` has NOT been built yet. It is Step 5 in the vault-builder plan (`docs/plans/elegant-watching-crescent.md`).
