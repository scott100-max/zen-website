// --- A/B Tournament Picker v2 (fixed: try/catch save, green toasts, version labels) ---
var PICKS_API = 'https://vault-picks.salus-mind.com';
var AUTH_TOKEN = 'salus-vault-2026';
var basePath = document.getElementById('basePath').value.replace(/\/+$/, '');
var initialState = {};
var abState = {};
var currentChunkArrayIdx = 0;
var pickCounter = 0;
var pickedThisSession = {}; // chunkIdx -> 'a' or 'b'
var rejectionReasons = {}; // chunkIdx -> { version: ['echo','hiss',...] }
var REASON_TAGS = [
  { key: 'e', label: 'Echo', color: '#f87171' },
  { key: 'h', label: 'Hiss', color: '#fbbf24' },
  { key: 'c', label: 'Cut Short', color: '#fb923c' },
  { key: 'v', label: 'Voice Shift', color: '#a78bfa' },
  { key: 'p', label: 'Pace', color: '#60a5fa' },
  { key: 'x', label: 'Other', color: '#7c809a' }
];
var pendingRejectTag = null; // { chunkIdx, versions: [v1,v2], callback }

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
            if (p.rejection_reasons) rejectionReasons[p.chunk] = p.rejection_reasons;
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

// --- All non-filtered candidates sorted by score (fallback: all if every candidate filtered) ---
function getTop(chunk) {
  var result = [];
  for (var i = 0; i < chunk.candidates.length; i++) {
    if (!chunk.candidates[i].filtered) result.push(chunk.candidates[i]);
  }
  if (result.length === 0) {
    for (var i = 0; i < chunk.candidates.length; i++) {
      result.push(chunk.candidates[i]);
    }
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
    // Last candidate — show in solo mode for accept/reject, do NOT auto-pick
    abState[chunkIdx] = { top5: top5, champion: available[0], challengerIdx: -1, winner: null, rejected: rejected, done: false, soloMode: true, notes: notes, round: 1 };
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

    // Solo mode: last candidate standing, accept or reject
    if (state.soloMode && a && !b) {
      html += '<div class="round-info" style="color:#ef4444;font-weight:700">Last candidate — accept or reject</div>';
      html += '<div class="ab-compare" id="abCompare">';
      html += '<div class="ab-side" style="border:2px solid #ef4444;border-radius:12px;padding:1rem;">';
      html += '<div class="ab-label label-a">LAST <span style="font-size:.6em;opacity:.7">(v' + a.v + ')</span></div>';
      html += '<audio controls preload="auto" src="' + basePath + '/' + a.file + '"></audio>';
      html += '<div class="ab-stats"><span class="score">' + a.score.toFixed(3) + '</span><span class="dur">' + a.dur.toFixed(1) + 's</span>';
      if (chunk.idx > 0) html += '<span class="tone">t' + a.tone.toFixed(4) + '</span>';
      html += '</div></div>';
      html += '</div>';
      html += '<div class="ab-actions">';
      html += '<button class="btn-a" onclick="pickSide(\'a\')" style="flex:1">Accept (A)</button>';
      html += '<button class="btn-same" onclick="pickSide(\'same\')" style="flex:1;background:rgba(239,68,68,0.2);color:#ef4444;border-color:#ef4444">Reject all (S)</button>';
      html += '</div>';
      html += '<div class="shortcuts">Keyboard: <kbd>A</kbd> Accept \u00b7 <kbd>S</kbd> Reject (no winner)</div>';
      area.innerHTML = html;
      var cmp = document.getElementById('abCompare');
      if (cmp) { cmp.style.opacity = '0.5'; setTimeout(function() { cmp.style.opacity = '1'; }, 50); }
      var navBtns = document.querySelectorAll('.chunk-nav button');
      for (var i = 0; i < navBtns.length; i++) navBtns[i].classList.remove('current');
      var navBtn = document.getElementById('nav-' + chunk.idx);
      if (navBtn) navBtn.classList.add('current');
      logDebug('Solo mode: chunk ' + chunk.idx + ', last candidate v' + a.v);
      return;
    }

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

  pickCounter++;

  // Solo mode handling (must come before a/b guard — b is null in solo mode)
  if (state.soloMode) {
    if (side === 'a') {
      // Accept the last candidate
      state.winner = a.v;
      state.done = true;
      state.soloMode = false;
      state.round = 0;
      pickedThisSession[chunk.idx] = 'a';
      logDebug('Accepted last candidate v' + a.v + ' for chunk ' + chunk.idx);
      showToast('PICKED: v' + a.v);
      try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }
      renderChunk();
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
      return;
    } else {
      // Reject last candidate — no winner
      state.rejected.push(a.v);
      state.done = true;
      state.winner = null;
      state.soloMode = false;
      state.round = 0;
      logDebug('All candidates rejected for chunk ' + chunk.idx);
      showToast('No winner \u2014 all rejected');
      try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }
      renderChunk();
      return;
    }
  }

  if (!a || !b) { logDebug('pickSide: missing a or b'); return; }

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
      // Only one left — show it solo for accept/reject, do NOT auto-pick
      state.champion = state.top5[remaining[0]];
      state.challengerIdx = -1;
      state.soloMode = true;
      state.round = (state.round || 0) + 1;
      logDebug('Last candidate v' + state.champion.v + ' — accept or reject');
      showToast('Last candidate — accept or reject');
    } else {
      // Remaining candidates exist — load next pair on same chunk
      state.champion = state.top5[remaining[0]];
      state.challengerIdx = remaining[1];
      state.round = (state.round || 0) + 1;
      logDebug('Both rejected, ' + remaining.length + ' remain. Loading next pair.');
    }

    // Save, render, then show tag bar for rejected pair
    try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }
    renderChunk();
    showRejectTagBar(chunk.idx, [a.v, b.v], function() {
      try { saveState(); } catch (e) {}
    });
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

  // Show tag bar for the loser, then auto-advance
  var _loser = (side === 'a') ? b : a;
  var _state = state;
  showRejectTagBar(chunk.idx, [_loser.v], function() {
    try { saveState(); } catch (e) {}
    if (_state.done && _state.winner != null) {
      for (var i = currentChunkArrayIdx + 1; i < chunkData.length; i++) {
        if (abState[chunkData[i].idx] && !abState[chunkData[i].idx].done) {
          currentChunkArrayIdx = i;
          renderChunk();
          return;
        }
      }
    }
  });
}

// --- Rejection reason tag bar ---
function showRejectTagBar(chunkIdx, versions, callback) {
  pendingRejectTag = { chunkIdx: chunkIdx, versions: versions, callback: callback };
  if (!rejectionReasons[chunkIdx]) rejectionReasons[chunkIdx] = {};
  for (var i = 0; i < versions.length; i++) {
    if (!rejectionReasons[chunkIdx][versions[i]]) rejectionReasons[chunkIdx][versions[i]] = [];
  }
  var bar = document.getElementById('rejectTagBar');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'rejectTagBar';
    bar.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#1e2030;border-top:2px solid #ef4444;padding:12px 20px;z-index:999;display:flex;align-items:center;gap:10px;flex-wrap:wrap;';
    document.body.appendChild(bar);
  }
  var vLabel = versions.map(function(v) { return 'v' + v; }).join(' + ');
  var html = '<span style="color:#ef4444;font-weight:700;font-size:0.85rem;">Tag ' + vLabel + ':</span>';
  for (var i = 0; i < REASON_TAGS.length; i++) {
    var t = REASON_TAGS[i];
    html += '<button onclick="tagReason(\'' + t.label + '\')" style="background:rgba(255,255,255,0.08);border:1px solid ' + t.color + ';color:' + t.color + ';padding:6px 14px;border-radius:6px;font-size:0.8rem;font-weight:600;cursor:pointer;">';
    html += '<kbd style="opacity:0.6;margin-right:4px">' + t.key.toUpperCase() + '</kbd>' + t.label + '</button>';
  }
  html += '<button onclick="dismissTagBar()" style="background:rgba(255,255,255,0.05);border:1px solid #7c809a;color:#7c809a;padding:6px 14px;border-radius:6px;font-size:0.8rem;cursor:pointer;">';
  html += '<kbd style="opacity:0.6;margin-right:4px">SPACE</kbd>Skip</button>';
  bar.innerHTML = html;
  bar.style.display = 'flex';
}

function tagReason(reason) {
  if (!pendingRejectTag) return;
  var ci = pendingRejectTag.chunkIdx;
  var versions = pendingRejectTag.versions;
  if (!rejectionReasons[ci]) rejectionReasons[ci] = {};
  for (var i = 0; i < versions.length; i++) {
    if (!rejectionReasons[ci][versions[i]]) rejectionReasons[ci][versions[i]] = [];
    if (rejectionReasons[ci][versions[i]].indexOf(reason) === -1) {
      rejectionReasons[ci][versions[i]].push(reason);
    }
  }
  showToast('Tagged: ' + reason);
  dismissTagBar();
}

function dismissTagBar() {
  var bar = document.getElementById('rejectTagBar');
  if (bar) bar.style.display = 'none';
  var cb = pendingRejectTag ? pendingRejectTag.callback : null;
  pendingRejectTag = null;
  if (cb) cb();
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
      rejection_reasons: rejectionReasons[c.idx] || {},
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
  // Tag bar intercepts keys when visible
  if (pendingRejectTag) {
    var k = e.key.toLowerCase();
    if (k === ' ') { e.preventDefault(); dismissTagBar(); return; }
    for (var i = 0; i < REASON_TAGS.length; i++) {
      if (k === REASON_TAGS[i].key) { tagReason(REASON_TAGS[i].label); return; }
    }
    return; // swallow other keys while tag bar is open
  }
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
