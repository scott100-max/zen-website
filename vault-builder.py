#!/usr/bin/env python3
"""
Vault Builder — Full Catalogue Candidate Generation

Generates multiple TTS candidates per chunk via Fish Audio API for human review.
Scores each candidate, organises into vault directory structure, generates
interactive picker pages, and uploads audio to R2.

Usage:
    python3 vault-builder.py content/scripts/52-the-court-of-your-mind.txt
    python3 vault-builder.py --batch content/scripts/
    python3 vault-builder.py --dry-run content/scripts/52-the-court-of-your-mind.txt
"""

import asyncio
import aiohttp
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Load build-session-v3.py via importlib (hyphenated filename can't be imported normally)
# ---------------------------------------------------------------------------
_build_spec = importlib.util.spec_from_file_location(
    "build_session_v3",
    Path(__file__).parent / "build-session-v3.py"
)
build = importlib.util.module_from_spec(_build_spec)
_build_spec.loader.exec_module(build)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VAULT_DIR = Path("content/audio-free/vault")
R2_BUCKET = "salus-mind"
FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"
FISH_API_KEY = os.getenv("FISH_API_KEY")
SAMPLE_RATE = 44100
MAX_CONCURRENT = 5  # Fish Starter tier limit

# Candidate counts by character range
CANDIDATE_COUNTS = [
    (0,   50,  30),   # Chunk 0 openings — cold-start + pace filtering
    (50,  100, 15),   # Short — Fish sweet spot
    (100, 200, 20),   # Medium — more attempts needed
    (200, 300, 25),   # Long — highest difficulty
]

SCORE_FILTER_THRESHOLD = 0.30  # Below this = pre-filter flagged (kept, not deleted)

# ---------------------------------------------------------------------------
# Script Pre-Processing
# ---------------------------------------------------------------------------

def get_candidate_count(char_count, is_chunk_0=False):
    """Determine how many candidates to generate for a block."""
    if is_chunk_0 and char_count <= 60:
        return 30
    for lo, hi, count in CANDIDATE_COUNTS:
        if lo <= char_count < hi:
            return count
    return 25  # 300+ chars (shouldn't happen after preprocessing)


def preprocess_blocks(blocks):
    """Merge short blocks (<50 chars) and split long blocks (>300 chars).

    Rules:
      Merge: with FOLLOWING block, no cross-5s+ silence, no chunk-0+1 merge, result ≤200.
      Split: at sentence boundaries, each result 50-200 chars, [SILENCE: 3] between.

    Returns (processed_blocks, log_entries).
    """
    merge_log = []
    split_log = []

    # --- Pass 1: Forward merge short blocks ---
    merged = []
    i = 0
    while i < len(blocks):
        text, pause = blocks[i]

        # Chunk 0: keep short (cold-start rule, up to 60 chars)
        if i == 0:
            merged.append((text, pause))
            i += 1
            continue

        if len(text) < 50 and i + 1 < len(blocks):
            next_text, next_pause = blocks[i + 1]
            # Don't merge across silences ≥5s
            if pause < 5:
                combined = text + " " + next_text
                if len(combined) <= 200:
                    merge_log.append(
                        f"MERGE→: block {i} ({len(text)}ch \"{text[:40]}\") "
                        f"+ block {i+1} ({len(next_text)}ch) → {len(combined)}ch"
                    )
                    merged.append((combined, next_pause))
                    i += 2
                    continue
            # Can't merge forward — keep as-is (backward merge in pass 1b)
            merged.append((text, pause))
            i += 1
        else:
            merged.append((text, pause))
            i += 1

    # --- Pass 1b: Backward merge remaining short blocks ---
    backward = []
    for i, (text, pause) in enumerate(merged):
        if (len(text) < 50 and i > 0 and backward
                and i != 0  # Never merge into chunk 0
                and len(backward[-1][0]) + len(text) + 1 <= 200):
            prev_text, prev_pause = backward[-1]
            # Only backward-merge if the previous block's pause was small
            # (the short block was after a big pause, so we attach to previous section)
            combined = prev_text + " " + text
            merge_log.append(
                f"MERGE←: block {i} ({len(text)}ch \"{text[:40]}\") "
                f"into prev ({len(prev_text)}ch) → {len(combined)}ch"
            )
            backward[-1] = (combined, pause)
        else:
            backward.append((text, pause))
    merged = backward

    # --- Pass 2: Split long blocks ---
    final = []
    for idx, (text, pause) in enumerate(merged):
        if len(text) > 300:
            fragments = _split_at_sentences(text)
            split_log.append(
                f"SPLIT: block {idx} ({len(text)}ch) → {len(fragments)} fragments "
                f"({[len(f) for f in fragments]})"
            )
            for j, frag in enumerate(fragments):
                if j < len(fragments) - 1:
                    final.append((frag, 3))  # 3s silence between fragments
                else:
                    final.append((frag, pause))
        else:
            final.append((text, pause))

    return final, merge_log + split_log


def _split_at_sentences(text, target_max=200, target_min=50):
    """Split text at sentence boundaries into 50-200 char fragments."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    fragments = []
    current = []
    current_len = 0

    for sent in sentences:
        new_len = current_len + len(sent) + (1 if current_len > 0 else 0)
        if new_len > target_max and current:
            fragments.append(' '.join(current))
            current = [sent]
            current_len = len(sent)
        else:
            current.append(sent)
            current_len = new_len

    if current:
        frag = ' '.join(current)
        if len(frag) < target_min and fragments:
            fragments[-1] = fragments[-1] + ' ' + frag
        else:
            fragments.append(frag)

    return fragments


# ---------------------------------------------------------------------------
# Inventory Generation
# ---------------------------------------------------------------------------

def generate_inventory(scripts_dir, output_path=None):
    """Parse all scripts and generate the master vault inventory.

    Returns list of inventory entries and writes to output_path if given.
    """
    scripts_dir = Path(scripts_dir)
    inventory = []

    skip_files = {'TEMPLATE.txt', 'test-voice-consistency.txt', 'SCRIPT-INVENTORY.md'}

    for script_file in sorted(scripts_dir.glob("*.txt")):
        if script_file.name in skip_files:
            continue
        # Skip variant scripts (contain -v2, -v3 etc. in name AND a base version exists)
        if re.search(r'-v\d+\.txt$', script_file.name):
            base = re.sub(r'-v\d+(\.txt)$', r'\1', script_file.name)
            if (scripts_dir / base).exists():
                continue

        meta = build.parse_script(script_file)
        blocks = build.process_script_for_tts(meta['content'], meta.get('category', 'mindfulness'))
        blocks, preprocess_log = preprocess_blocks(blocks)

        script_id = script_file.stem
        for ci, (text, pause) in enumerate(blocks):
            inventory.append({
                'script_id': script_id,
                'chunk_index': ci,
                'text': text,
                'char_count': len(text),
                'pause_after': pause,
                'category': meta.get('category', 'mindfulness'),
                'emotion': meta.get('api_emotion', 'calm'),
                'is_opening': ci == 0,
                'is_closing': ci == len(blocks) - 1,
            })

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(inventory, indent=2))
        print(f"Inventory: {len(inventory)} blocks across "
              f"{len(set(e['script_id'] for e in inventory))} scripts → {output_path}")

    return inventory


# ---------------------------------------------------------------------------
# Async TTS Generation
# ---------------------------------------------------------------------------

async def _generate_one(session, text, wav_path, chunk_num, semaphore,
                        emotion='calm', api_log=None):
    """Generate a single TTS candidate via Fish API, save as WAV.

    Returns wav_path on success, raises on failure.
    """
    mp3_tmp = str(wav_path) + ".tmp.mp3"
    call_id = f"c{chunk_num:02d}_{Path(wav_path).stem}"
    started = time.time()

    async with semaphore:
        payload = {
            "text": text,
            "reference_id": FISH_VOICE_ID,
            "format": "mp3",
            "temperature": 0.3,
            "version": "v3-hd",
            "emotion": emotion,
            "prosody": {"speed": 0.95, "volume": 0},
            "sample_rate": SAMPLE_RATE,
        }
        headers = {
            "Authorization": f"Bearer {FISH_API_KEY}",
            "Content-Type": "application/json",
        }

        last_err = None
        for attempt in range(4):
            try:
                async with session.post(
                    FISH_API_URL, json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status == 429:
                        wait = 2 ** attempt + 1
                        print(f"      429 rate-limit → wait {wait}s")
                        if api_log is not None:
                            api_log.append({
                                'call_id': call_id, 'status': 429,
                                'attempt': attempt, 'ts': _now_iso()
                            })
                        await asyncio.sleep(wait)
                        continue
                    if resp.status != 200:
                        body = await resp.text()
                        raise Exception(f"Fish API {resp.status}: {body[:200]}")
                    data = await resp.read()
                    Path(mp3_tmp).write_bytes(data)
                    elapsed = time.time() - started
                    if api_log is not None:
                        api_log.append({
                            'call_id': call_id, 'status': 200,
                            'attempt': attempt, 'ts': _now_iso(),
                            'elapsed_s': round(elapsed, 2),
                            'chars': len(text),
                        })
                    break
            except asyncio.TimeoutError:
                last_err = "timeout"
                if attempt < 3:
                    await asyncio.sleep(2 ** attempt)
                continue
            except aiohttp.ClientError as e:
                last_err = str(e)
                if attempt < 3:
                    await asyncio.sleep(2 ** attempt)
                continue
        else:
            raise Exception(f"Failed after 4 attempts: {last_err}")

    # Convert MP3 → WAV
    subprocess.run([
        'ffmpeg', '-y', '-i', mp3_tmp,
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE), '-ac', '1',
        str(wav_path)
    ], capture_output=True, check=True)

    try:
        os.remove(mp3_tmp)
    except OSError:
        pass

    return str(wav_path)


def _score_wav(wav_path, prev_mfcc=None):
    """Score a WAV candidate. Returns (details_dict, mfcc_array)."""
    details = build.score_chunk_quality(str(wav_path))
    mfcc = build.compute_mfcc_profile(str(wav_path))

    quality = details['score']
    tone_dist = build.tonal_distance(prev_mfcc, mfcc)
    tone_penalty = tone_dist * 50.0
    combined = quality - tone_penalty

    details['tone_dist'] = round(tone_dist, 6)
    details['tone_penalty'] = round(tone_penalty, 3)
    details['combined_score'] = round(combined, 4)
    details['duration'] = round(build.get_audio_duration(str(wav_path)), 2)
    details['filtered'] = combined < SCORE_FILTER_THRESHOLD

    # Over-generation check
    char_count = details.get('_char_count', 0)
    if char_count > 0:
        expected = char_count / 15.0
        max_dur = max(expected * 2.5, 20.0)
        if details['duration'] > max_dur:
            details['filtered'] = True
            details['filter_reason'] = 'overgenerated'

    return details, mfcc


async def generate_chunk_candidates(
    http_session, chunk_idx, text, chunk_dir, semaphore,
    emotion='calm', prev_best_mfcc=None, executor=None, api_log=None,
    extra=0
):
    """Generate all candidates for one chunk. Chunks are processed sequentially
    (tonal distance needs previous chunk's best), but candidates within a chunk
    run in parallel up to the semaphore limit.

    Returns (chunk_meta_dict, best_mfcc, scores_list).
    """
    n_candidates = get_candidate_count(len(text), is_chunk_0=(chunk_idx == 0)) + extra
    chunk_dir = Path(chunk_dir)
    chunk_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"c{chunk_idx:02d}"

    # Resume support: find existing versions
    existing = sorted(chunk_dir.glob(f"{prefix}_v*.wav"))
    start_v = 0
    if existing:
        last = existing[-1].stem  # e.g. c07_v14
        start_v = int(last.split('_v')[1]) + 1
        print(f"  Chunk {chunk_idx}: resuming from v{start_v:02d} "
              f"({len(existing)} existing)")

    remaining = max(0, n_candidates - start_v)
    total = start_v + remaining

    print(f"\n  Chunk {chunk_idx}: \"{text[:60]}{'...' if len(text) > 60 else ''}\" "
          f"({len(text)} chars, {remaining} new / {total} total candidates)")

    if remaining == 0 and existing:
        print(f"    All {n_candidates} candidates already exist — scoring only")

    # Generate new candidates
    loop = asyncio.get_event_loop()
    gen_tasks = []
    for v in range(start_v, start_v + remaining):
        wav_path = chunk_dir / f"{prefix}_v{v:02d}.wav"
        gen_tasks.append(
            _generate_one(http_session, text, wav_path, chunk_idx,
                          semaphore, emotion, api_log)
        )

    if gen_tasks:
        results = await asyncio.gather(*gen_tasks, return_exceptions=True)
        failures = sum(1 for r in results if isinstance(r, Exception))
        if failures:
            print(f"    {failures} generation(s) failed")
            for r in results:
                if isinstance(r, Exception):
                    print(f"      → {r}")

    # Score ALL candidates (existing + new)
    all_wavs = sorted(chunk_dir.glob(f"{prefix}_v*.wav"))
    candidates = []
    best_score = None
    best_mfcc = prev_best_mfcc
    best_version = None

    for wav_path in all_wavs:
        v = int(wav_path.stem.split('_v')[1])
        try:
            details, mfcc = await loop.run_in_executor(
                executor, _score_wav, str(wav_path), prev_best_mfcc
            )
            details['_char_count'] = len(text)  # For overgen check
            status = "FILTERED" if details.get('filtered') else "OK"
            tone_info = (f" tone={details['tone_dist']:.4f}"
                         if prev_best_mfcc is not None else "")
            print(f"    v{v:02d}: {details['combined_score']:.3f} "
                  f"(q={details['score']:.3f}{tone_info} "
                  f"dur={details['duration']:.1f}s) {status}")

            entry = {
                'version': v,
                'filename': wav_path.name,
                'duration_seconds': details['duration'],
                'composite_score': details['combined_score'],
                'quality_score': details['score'],
                'echo_risk': details['echo_risk'],
                'hiss_risk': details['hiss_risk'],
                'sp_contrast': details['sp_contrast'],
                'sp_flatness': details['sp_flatness'],
                'tonal_distance_to_prev': details['tone_dist'],
                'filtered': details.get('filtered', False),
                'filter_reason': details.get('filter_reason', ''),
                'generated_at': _now_iso(),
            }
            candidates.append(entry)

            # Track best unfiltered (or best overall if all filtered)
            if not details.get('filtered') or best_score is None:
                score = details['combined_score']
                if best_score is None or score > best_score:
                    if not details.get('filtered') or best_version is None:
                        best_score = score
                        best_mfcc = mfcc
                        best_version = v

        except Exception as e:
            print(f"    v{v:02d}: SCORE FAILED — {e}")
            candidates.append({
                'version': v, 'filename': wav_path.name,
                'error': str(e), 'filtered': True,
            })

    if best_version is not None:
        print(f"    → Best: v{best_version:02d} ({best_score:.3f})")
    else:
        print(f"    → No valid candidates")

    # Write metadata files
    meta = {
        'chunk_index': chunk_idx,
        'text': text,
        'char_count': len(text),
        'is_opening': chunk_idx == 0,
        'is_closing': False,  # Caller updates this
        'candidates': candidates,
    }
    scores = {
        'chunk_index': chunk_idx,
        'best_version': best_version,
        'best_score': best_score,
        'total_candidates': len(candidates),
        'filtered_count': sum(1 for c in candidates if c.get('filtered')),
        'scores': [{
            'version': c['version'],
            'composite_score': c.get('composite_score'),
            'quality_score': c.get('quality_score'),
            'tonal_distance': c.get('tonal_distance_to_prev'),
            'duration': c.get('duration_seconds'),
            'filtered': c.get('filtered', False),
        } for c in candidates],
    }

    (chunk_dir / f"{prefix}_meta.json").write_text(json.dumps(meta, indent=2))
    (chunk_dir / f"{prefix}_scores.json").write_text(json.dumps(scores, indent=2))

    return meta, best_mfcc, scores


# ---------------------------------------------------------------------------
# Picker Page Generation
# ---------------------------------------------------------------------------

def generate_picker_html(session_id, session_dir, blocks, all_meta):
    """Generate review.html for human candidate selection."""
    session_dir = Path(session_dir)
    chunks_js = []

    for meta in all_meta:
        ci = meta['chunk_index']
        candidates_js = []
        for c in meta.get('candidates', []):
            if c.get('error'):
                continue
            candidates_js.append({
                'v': c['version'],
                'file': f"c{ci:02d}/{c['filename']}",
                'score': c.get('composite_score', 0),
                'dur': c.get('duration_seconds', 0),
                'tone': c.get('tonal_distance_to_prev', 0),
                'filtered': c.get('filtered', False),
            })
        chunks_js.append({
            'idx': ci,
            'text': meta['text'],
            'chars': meta['char_count'],
            'isOpening': meta.get('is_opening', False),
            'isClosing': meta.get('is_closing', False),
            'candidates': candidates_js,
        })

    r2_base = f"https://media.salus-mind.com/vault/{session_id}"
    picks_api = "https://vault-picks.salus-mind.com"
    picks_token = "salus-vault-2026"

    html = _PICKER_TEMPLATE.replace('__SESSION_ID__', session_id)
    html = html.replace('__CHUNKS_DATA__', json.dumps(chunks_js, indent=2))
    html = html.replace('__GENERATED_AT__', _now_iso())
    html = html.replace('__DEFAULT_BASE_PATH__', r2_base)
    html = html.replace('__PICKS_API_URL__', picks_api)
    html = html.replace('__PICKS_AUTH_TOKEN__', picks_token)

    out = session_dir / 'review.html'
    out.write_text(html)
    print(f"  Picker page → {out}")
    return out


_PICKER_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vault Picker — __SESSION_ID__</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a12;color:#f0eefc;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:32px 20px;max-width:1100px;margin:0 auto}
h1{font-size:1.3rem;font-weight:300;margin-bottom:4px}
.meta{font-size:.78rem;color:#888;margin-bottom:6px}
.save-status{font-size:.72rem;padding:3px 10px;border-radius:4px;margin-bottom:16px;display:inline-block}
.save-status.ok{background:rgba(52,211,153,.1);color:#34d399}
.save-status.saving{background:rgba(250,204,21,.1);color:#facc15}
.save-status.error{background:rgba(239,68,68,.1);color:#ef4444}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px;align-items:center}
.controls button,.controls select{padding:6px 14px;border-radius:6px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);color:#f0eefc;cursor:pointer;font-size:.78rem}
.controls button:hover{background:rgba(255,255,255,.08)}
.controls button.active{background:rgba(52,211,153,.15);border-color:#34d399;color:#34d399}
.progress{font-size:.82rem;color:#34d399;margin-left:auto}
.chunk-section{margin-bottom:44px;border-top:1px solid rgba(255,255,255,.06);padding-top:20px}
.chunk-header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px}
.chunk-title{font-size:.9rem;font-weight:500;color:#34d399}
.chunk-badge{font-size:.7rem;padding:2px 8px;border-radius:4px;background:rgba(167,139,250,.12);color:#a78bfa}
.chunk-text{font-size:.82rem;color:#999;font-style:italic;margin-bottom:8px;line-height:1.5}
.chunk-notes{width:100%;padding:6px 10px;margin-bottom:12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:6px;color:#ccc;font-size:.78rem;resize:vertical;min-height:28px}
.chunk-notes::placeholder{color:#555}
.sort-bar{display:flex;gap:8px;margin-bottom:10px;font-size:.72rem}
.sort-bar button{padding:3px 10px;border-radius:4px;border:1px solid rgba(255,255,255,.08);background:transparent;color:#888;cursor:pointer;font-size:.72rem}
.sort-bar button.active{color:#34d399;border-color:rgba(52,211,153,.3)}
.version{display:flex;align-items:center;gap:10px;padding:8px 12px;margin-bottom:5px;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);border-radius:8px;transition:all .15s}
.version:hover{border-color:rgba(255,255,255,.1)}
.version.picked{border-color:#34d399;background:rgba(52,211,153,.06)}
.version.rejected{border-color:rgba(239,68,68,.25);background:rgba(239,68,68,.03);opacity:.45}
.version.filtered{opacity:.35}
.v-label{font-size:.7rem;color:#888;min-width:28px;font-weight:600;text-align:center}
.v-audio{flex:1}
.v-audio audio{width:100%;height:30px}
.v-stats{display:flex;gap:12px;font-size:.68rem;color:#777;flex-shrink:0;min-width:180px}
.v-stats span{white-space:nowrap}
.v-stats .score{color:#34d399}
.v-stats .dur{color:#a78bfa}
.v-stats .tone{color:#f59e0b}
.v-btns{display:flex;gap:5px;flex-shrink:0}
.v-btns button{padding:3px 10px;border-radius:5px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:#f0eefc;cursor:pointer;font-size:.7rem;transition:all .15s}
.v-btns .pick-btn.active{background:rgba(52,211,153,.2);border-color:#34d399;color:#34d399}
.v-btns .rej-btn.active{background:rgba(239,68,68,.2);border-color:#ef4444;color:#ef4444}
.export-bar{margin-top:36px;display:flex;gap:10px;align-items:center}
.export-bar button{padding:8px 20px;border-radius:7px;border:1px solid rgba(52,211,153,.3);background:rgba(52,211,153,.1);color:#34d399;cursor:pointer;font-size:.82rem;font-weight:500}
.export-bar button:hover{background:rgba(52,211,153,.18)}
.export-bar .status{font-size:.78rem;color:#888}
.summary{margin-top:16px;padding:14px;background:rgba(52,211,153,.04);border:1px solid rgba(52,211,153,.12);border-radius:8px;display:none}
.summary pre{white-space:pre-wrap;color:#ccc;font-size:.75rem}
.chunk0-dur{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.7rem;font-weight:600;margin-left:8px}
.chunk0-dur.in-range{background:rgba(52,211,153,.15);color:#34d399}
.chunk0-dur.out-range{background:rgba(239,68,68,.15);color:#ef4444}
.dur-target{font-size:.72rem;color:#888;margin-bottom:8px}
.dur-target input{width:50px;padding:2px 5px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:4px;color:#f0eefc;font-size:.72rem;text-align:center}
</style>
</head>
<body>
<h1>Vault Picker — __SESSION_ID__</h1>
<p class="meta">Generated __GENERATED_AT__</p>
<p class="meta">Audio base: <input id="basePath" value="__DEFAULT_BASE_PATH__" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:4px;color:#f0eefc;padding:2px 6px;font-size:.72rem;width:420px" onchange="updateBasePath()"></p>
<div class="save-status ok" id="saveStatus">Auto-save active</div>

<div class="controls">
  <button onclick="filterChunks('all')" class="active" id="fAll">All Chunks</button>
  <button onclick="filterChunks('unpicked')" id="fUnpicked">Unpicked Only</button>
  <button onclick="filterChunks('opening')" id="fOpening">Chunk 0 Only</button>
  <button onclick="playAllPicks()" id="btnPlayAll">Play All Picks</button>
  <span class="progress" id="progress">0 / 0 picked</span>
</div>

<div id="chunks"></div>

<div class="export-bar">
  <button onclick="exportPicks()">Download picks.json</button>
  <button onclick="exportTxt()">Download TXT</button>
  <span class="status" id="exportStatus"></span>
</div>
<div class="summary" id="summaryBox"><pre id="summaryJson"></pre></div>

<script>
const SESSION_ID = '__SESSION_ID__';
const chunkData = __CHUNKS_DATA__;

// --- Auto-save configuration ---
const PICKS_API = '__PICKS_API_URL__';
const AUTH_TOKEN = '__PICKS_AUTH_TOKEN__';
let basePath = document.getElementById('basePath').value.replace(/\/+$/, '');
let durTargetMin = 3.0, durTargetMax = 5.0;
let currentFilter = 'all';
let saveTimer = null;
let initialState = null;

// --- Load state: try remote first, fall back to localStorage ---
async function loadState() {
  // Try remote
  if (PICKS_API && AUTH_TOKEN) {
    try {
      const resp = await fetch(PICKS_API + '/picks/' + SESSION_ID, {
        headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN }
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.picks && data.picks.length > 0) {
          initialState = {};
          data.picks.forEach(p => {
            initialState[p.chunk] = {
              picked: p.picked,
              rejected: p.rejected || [],
              notes: p.notes || '',
            };
          });
          setSaveStatus('ok', 'Loaded from server');
          return initialState;
        }
      }
    } catch (e) {
      console.warn('Remote load failed, using localStorage:', e);
    }
  }
  // Fall back to localStorage
  const saved = localStorage.getItem('vault-picks-' + SESSION_ID);
  if (saved) {
    initialState = JSON.parse(saved);
    setSaveStatus('ok', 'Loaded from localStorage');
    return initialState;
  }
  initialState = {};
  return {};
}

function setSaveStatus(cls, text) {
  const el = document.getElementById('saveStatus');
  el.className = 'save-status ' + cls;
  el.textContent = text;
}

function updateBasePath() {
  basePath = document.getElementById('basePath').value.replace(/\/+$/, '');
  document.querySelectorAll('.v-audio audio').forEach(a => {
    const rel = a.dataset.rel;
    a.src = basePath + '/' + rel;
  });
}

function collectPicks() {
  const picks = {session: SESSION_ID, reviewed: new Date().toISOString(), picks: []};
  chunkData.forEach(c => {
    const picked = document.querySelector(`.version[data-chunk="${c.idx}"] .pick-btn.active`);
    const rejected = document.querySelectorAll(`.version[data-chunk="${c.idx}"] .rej-btn.active`);
    const notes = document.getElementById('notes-' + c.idx);
    picks.picks.push({
      chunk: c.idx,
      text: c.text,
      picked: picked ? parseInt(picked.closest('.version').dataset.version) : null,
      picked_file: picked ? picked.closest('.version').querySelector('audio').dataset.rel : null,
      rejected: Array.from(rejected).map(b => parseInt(b.closest('.version').dataset.version)),
      notes: notes ? notes.value : '',
    });
  });
  return picks;
}

// --- Auto-save: localStorage immediately, remote debounced ---
function saveState() {
  const picks = collectPicks();
  // localStorage — instant
  const localState = {};
  picks.picks.forEach(p => {
    localState[p.chunk] = { picked: p.picked, rejected: p.rejected, notes: p.notes };
  });
  localStorage.setItem('vault-picks-' + SESSION_ID, JSON.stringify(localState));
  updateProgress();

  // Remote — debounce 500ms to avoid hammering on rapid clicks
  if (saveTimer) clearTimeout(saveTimer);
  setSaveStatus('saving', 'Saving...');
  saveTimer = setTimeout(() => saveRemote(picks), 500);
}

async function saveRemote(picks) {
  if (!PICKS_API || !AUTH_TOKEN) {
    setSaveStatus('ok', 'Local only (no API configured)');
    return;
  }
  try {
    const resp = await fetch(PICKS_API + '/picks/' + SESSION_ID, {
      method: 'PUT',
      headers: {
        'Authorization': 'Bearer ' + AUTH_TOKEN,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(picks),
    });
    if (resp.ok) {
      setSaveStatus('ok', 'Saved ' + new Date().toLocaleTimeString());
    } else {
      setSaveStatus('error', 'Save failed: ' + resp.status);
    }
  } catch (e) {
    setSaveStatus('error', 'Save failed: ' + e.message);
  }
}

function updateProgress() {
  let picked = 0;
  chunkData.forEach(c => {
    if (document.querySelector(`.version[data-chunk="${c.idx}"] .pick-btn.active`)) picked++;
  });
  document.getElementById('progress').textContent = `${picked} / ${chunkData.length} picked`;
}

function pickVersion(chunk, version, btn) {
  document.querySelectorAll(`.version[data-chunk="${chunk}"] .pick-btn`).forEach(b => {
    b.classList.remove('active');
    b.closest('.version').classList.remove('picked');
  });
  btn.classList.add('active');
  btn.closest('.version').classList.add('picked');
  btn.closest('.version').classList.remove('rejected');
  const rej = btn.closest('.version').querySelector('.rej-btn');
  if (rej) rej.classList.remove('active');
  saveState();
}

function rejectVersion(chunk, version, btn) {
  const ver = btn.closest('.version');
  btn.classList.toggle('active');
  ver.classList.toggle('rejected');
  ver.classList.remove('picked');
  const pick = ver.querySelector('.pick-btn');
  if (pick) pick.classList.remove('active');
  saveState();
}

function sortChunk(chunkIdx, field) {
  const section = document.querySelector(`.chunk-section[data-chunk="${chunkIdx}"]`);
  const versions = Array.from(section.querySelectorAll('.version'));
  versions.sort((a, b) => {
    const av = parseFloat(a.dataset[field] || 0);
    const bv = parseFloat(b.dataset[field] || 0);
    return field === 'score' ? bv - av : av - bv;
  });
  const container = section.querySelector('.versions-container');
  versions.forEach(v => container.appendChild(v));
  section.querySelectorAll('.sort-bar button').forEach(b => b.classList.remove('active'));
  section.querySelector(`.sort-bar button[data-sort="${field}"]`).classList.add('active');
}

function filterChunks(mode) {
  currentFilter = mode;
  document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
  document.getElementById(mode === 'all' ? 'fAll' : mode === 'unpicked' ? 'fUnpicked' : 'fOpening').classList.add('active');
  document.querySelectorAll('.chunk-section').forEach(s => {
    const idx = parseInt(s.dataset.chunk);
    const hasPick = !!document.querySelector(`.version[data-chunk="${idx}"] .pick-btn.active`);
    if (mode === 'all') s.style.display = '';
    else if (mode === 'unpicked') s.style.display = hasPick ? 'none' : '';
    else if (mode === 'opening') s.style.display = idx === 0 ? '' : 'none';
  });
}

async function playAllPicks() {
  const btn = document.getElementById('btnPlayAll');
  btn.textContent = 'Playing...';
  for (const c of chunkData) {
    const picked = document.querySelector(`.version[data-chunk="${c.idx}"] .pick-btn.active`);
    if (!picked) continue;
    const audio = picked.closest('.version').querySelector('audio');
    audio.currentTime = 0;
    audio.play();
    await new Promise(r => audio.onended = r);
    await new Promise(r => setTimeout(r, 800));
  }
  btn.textContent = 'Play All Picks';
}

function exportPicks() {
  const picks = collectPicks();
  const json = JSON.stringify(picks, null, 2);
  const blob = new Blob([json], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION_ID + '-vault-picks.json';
  a.click();
  document.getElementById('exportStatus').textContent = 'Downloaded!';
  document.getElementById('summaryBox').style.display = 'block';
  document.getElementById('summaryJson').textContent = json;
}

function exportTxt() {
  const picks = collectPicks();
  let txt = `VAULT PICKS: ${picks.session}\nDate: ${picks.reviewed}\n\n`;
  picks.picks.forEach(p => {
    txt += `Chunk ${p.chunk}: picked v${p.picked !== null ? p.picked : 'NONE'} (${p.picked_file || 'none'})\n`;
    txt += `  Text: "${p.text}"\n`;
    if (p.notes) txt += `  Notes: ${p.notes}\n`;
    if (p.rejected.length) txt += `  Rejected: ${p.rejected.map(v => 'v' + v).join(', ')}\n`;
    txt += '\n';
  });
  const allPicked = picks.picks.every(p => p.picked !== null);
  txt += allPicked ? 'STATUS: All chunks picked — ready to assemble\n' : 'STATUS: Not all chunks picked yet\n';
  const blob = new Blob([txt], {type: 'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION_ID + '-vault-picks.txt';
  a.click();
}

// --- Build UI then load state ---
async function init() {
  const savedState = await loadState();
  const container = document.getElementById('chunks');

  chunkData.forEach(c => {
    const section = document.createElement('div');
    section.className = 'chunk-section';
    section.dataset.chunk = c.idx;

    let html = '<div class="chunk-header">';
    html += `<span class="chunk-title">Chunk ${c.idx}</span>`;
    html += `<span class="chunk-badge">${c.chars} chars${c.isOpening ? ' \u00b7 opening' : ''}${c.isClosing ? ' \u00b7 closing' : ''}</span>`;
    html += '</div>';
    html += `<div class="chunk-text">"${c.text}"</div>`;

    const savedNote = savedState[c.idx] ? savedState[c.idx].notes || '' : '';
    html += `<textarea class="chunk-notes" id="notes-${c.idx}" placeholder="Notes..." oninput="saveState()">${savedNote}</textarea>`;

    if (c.isOpening) {
      html += `<div class="dur-target">Duration target: <input id="durMin-${c.idx}" value="${durTargetMin}" onchange="durTargetMin=parseFloat(this.value)"> \u2013 <input id="durMax-${c.idx}" value="${durTargetMax}" onchange="durTargetMax=parseFloat(this.value)"> seconds</div>`;
    }

    const defaultSort = c.isOpening ? 'dur' : 'score';
    html += `<div class="sort-bar">Sort: `;
    html += `<button data-sort="score" class="${defaultSort==='score'?'active':''}" onclick="sortChunk(${c.idx},'score')">Score</button>`;
    html += `<button data-sort="dur" class="${defaultSort==='dur'?'active':''}" onclick="sortChunk(${c.idx},'dur')">Duration</button>`;
    if (c.idx > 0) html += `<button data-sort="tone" onclick="sortChunk(${c.idx},'tone')">Tonal Dist</button>`;
    html += '</div>';

    let sorted = [...c.candidates];
    if (defaultSort === 'score') sorted.sort((a, b) => b.score - a.score);
    else sorted.sort((a, b) => a.dur - b.dur);

    html += '<div class="versions-container">';
    sorted.forEach(cand => {
      const vid = `c${String(c.idx).padStart(2,'0')}_v${String(cand.v).padStart(2,'0')}`;
      const filteredCls = cand.filtered ? ' filtered' : '';
      const savedPick = savedState[c.idx] && savedState[c.idx].picked === cand.v;
      const savedRej = savedState[c.idx] && savedState[c.idx].rejected && savedState[c.idx].rejected.includes(cand.v);
      const pickedCls = savedPick ? ' picked' : '';
      const rejCls = savedRej ? ' rejected' : '';

      let durBadge = '';
      if (c.isOpening) {
        const inRange = cand.dur >= durTargetMin && cand.dur <= durTargetMax;
        durBadge = `<span class="chunk0-dur ${inRange ? 'in-range' : 'out-range'}">${cand.dur.toFixed(1)}s</span>`;
      }

      html += `<div class="version${filteredCls}${pickedCls}${rejCls}" id="${vid}" data-chunk="${c.idx}" data-version="${cand.v}" data-score="${cand.score}" data-dur="${cand.dur}" data-tone="${cand.tone}">`;
      html += `<span class="v-label">v${cand.v}</span>`;
      html += `<div class="v-audio"><audio controls preload="none" src="${basePath}/${cand.file}" data-rel="${cand.file}"></audio></div>`;
      html += `<div class="v-stats">`;
      html += `<span class="score">${cand.score.toFixed(3)}</span>`;
      html += `<span class="dur">${cand.dur.toFixed(1)}s${durBadge}</span>`;
      if (c.idx > 0) html += `<span class="tone">t${cand.tone.toFixed(4)}</span>`;
      html += `</div>`;
      html += `<div class="v-btns">`;
      html += `<button class="pick-btn${savedPick ? ' active' : ''}" onclick="pickVersion(${c.idx},${cand.v},this)">PICK</button>`;
      html += `<button class="rej-btn${savedRej ? ' active' : ''}" onclick="rejectVersion(${c.idx},${cand.v},this)">X</button>`;
      html += `</div></div>`;
    });
    html += '</div>';
    section.innerHTML = html;
    container.appendChild(section);
  });

  updateProgress();
}

init();
</script>
</body>
</html>
'''


# ---------------------------------------------------------------------------
# R2 Upload
# ---------------------------------------------------------------------------

def upload_session_to_r2(session_dir, session_id):
    """Upload all vault candidate WAVs + review.html to R2."""
    session_dir = Path(session_dir)
    r2_prefix = f"vault/{session_id}"
    uploaded = 0
    errors = 0

    # Collect files to upload: all .wav files + review.html
    files_to_upload = []
    for wav in session_dir.rglob("*.wav"):
        rel = wav.relative_to(session_dir)
        files_to_upload.append((wav, f"{r2_prefix}/{rel}"))
    review = session_dir / "review.html"
    if review.exists():
        files_to_upload.append((review, f"{r2_prefix}/review.html"))

    print(f"\n  Uploading {len(files_to_upload)} files to R2 at {r2_prefix}/...")

    for local_path, r2_key in files_to_upload:
        ct = "audio/wav" if local_path.suffix == ".wav" else "text/html"
        try:
            subprocess.run([
                "npx", "wrangler", "r2", "object", "put",
                f"{R2_BUCKET}/{r2_key}",
                f"--file={local_path}",
                "--remote",
                f"--content-type={ct}",
            ], capture_output=True, check=True, timeout=120)
            uploaded += 1
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"    FAILED: {r2_key} — {e}")
            errors += 1

        if uploaded % 50 == 0 and uploaded > 0:
            print(f"    ...{uploaded}/{len(files_to_upload)} uploaded")

    print(f"  R2 upload complete: {uploaded} succeeded, {errors} failed")
    return uploaded, errors


# ---------------------------------------------------------------------------
# Email Notification
# ---------------------------------------------------------------------------

def send_notification(subject, body):
    """Send build notification via Resend (uses curl, NOT urllib)."""
    resend_key = os.getenv("RESEND_API_KEY")
    if not resend_key:
        print("  (No RESEND_API_KEY — skipping email)")
        return

    payload = json.dumps({
        "from": "onboarding@resend.dev",
        "to": ["scottripley@icloud.com"],
        "subject": subject,
        "text": body,
    })

    try:
        subprocess.run([
            "curl", "-s", "-X", "POST", "https://api.resend.com/emails",
            "-H", f"Authorization: Bearer {resend_key}",
            "-H", "Content-Type: application/json",
            "-d", payload,
        ], capture_output=True, check=True, timeout=30)
        print(f"  Email sent: {subject}")
    except Exception as e:
        print(f"  Email failed: {e}")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _load_gen_log(path):
    """Load or create the global generation log."""
    if path.exists():
        return json.loads(path.read_text())
    return {"runs": []}


def _save_gen_log(log, path):
    path.write_text(json.dumps(log, indent=2))


# ---------------------------------------------------------------------------
# Main Build Orchestration
# ---------------------------------------------------------------------------

async def build_session(script_path, dry_run=False, extra=0, only_chunks=None):
    """Generate vault candidates for a single session script.

    Returns session manifest dict.
    """
    script_path = Path(script_path)
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return None

    if not FISH_API_KEY:
        print("ERROR: FISH_API_KEY not set in .env")
        return None

    # Parse script
    meta = build.parse_script(script_path)
    session_id = script_path.stem
    category = meta.get('category', 'mindfulness')
    emotion = meta.get('api_emotion', 'calm')

    # Process blocks
    raw_blocks = build.process_script_for_tts(meta['content'], category)
    blocks, preprocess_log = preprocess_blocks(raw_blocks)

    print(f"\n{'='*70}")
    print(f"  VAULT BUILDER — {session_id}")
    print(f"  Category: {category} | Emotion: {emotion}")
    print(f"  Raw blocks: {len(raw_blocks)} → Processed: {len(blocks)}")
    print(f"{'='*70}")

    if preprocess_log:
        print(f"\n  Pre-processing:")
        for entry in preprocess_log:
            print(f"    {entry}")

    # Calculate stats
    total_candidates = 0
    total_chars = 0
    for ci, (text, pause) in enumerate(blocks):
        n = get_candidate_count(len(text), is_chunk_0=(ci == 0))
        total_candidates += n
        total_chars += len(text) * n

    short_blocks = sum(1 for t, _ in blocks if len(t) < 50)
    long_blocks = sum(1 for t, _ in blocks if len(t) > 300)

    print(f"\n  Chunks: {len(blocks)}")
    print(f"  Total candidates to generate: {total_candidates}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Estimated cost: £{total_chars / 1000 * 0.003:.2f}")
    print(f"  Blocks <50 chars: {short_blocks} (chunk 0s exempt up to 60)")
    print(f"  Blocks >300 chars: {long_blocks}")

    if dry_run:
        print(f"\n  DRY RUN — block detail:")
        for ci, (text, pause) in enumerate(blocks):
            n = get_candidate_count(len(text), is_chunk_0=(ci == 0))
            print(f"    c{ci:02d}: {len(text):3d} chars, {n:2d} candidates, "
                  f"pause={pause}s — \"{text[:70]}{'...' if len(text) > 70 else ''}\"")
        return None

    # Create directory structure
    session_dir = VAULT_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    picks_dir = session_dir / "picks"
    picks_dir.mkdir(exist_ok=True)
    final_dir = session_dir / "final"
    final_dir.mkdir(exist_ok=True)

    # Load generation log
    gen_log_path = VAULT_DIR / "generation-log.json"
    gen_log = _load_gen_log(gen_log_path)

    # Track run
    run_started = _now_iso()
    api_log = []
    all_meta = []
    total_api_calls = 0
    total_chars_sent = 0
    total_filtered = 0

    # Generate candidates chunk-by-chunk (sequential for tonal distance)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    executor = ThreadPoolExecutor(max_workers=4)

    async with aiohttp.ClientSession() as http_session:
        prev_best_mfcc = None

        only_set = None
        if only_chunks:
            only_set = set(int(x) for x in only_chunks.split(',')) if isinstance(only_chunks, str) else set(only_chunks)

        for ci, (text, pause) in enumerate(blocks):
            if only_set is not None and ci not in only_set:
                # Still need prev_best_mfcc for tonal distance
                chunk_dir = session_dir / f"c{ci:02d}"
                scores_file = chunk_dir / f"c{ci:02d}_scores.json"
                if scores_file.exists():
                    sd = json.loads(scores_file.read_text())
                    best_v = sd.get('best_version', 0)
                    best_wav = chunk_dir / f"c{ci:02d}_v{best_v:02d}.wav"
                    if best_wav.exists():
                        prev_best_mfcc = build.compute_mfcc_profile(str(best_wav))
                print(f"  Chunk {ci}: skipped (not in --only-chunks)")
                continue

            chunk_dir = session_dir / f"c{ci:02d}"

            chunk_meta, prev_best_mfcc, scores = await generate_chunk_candidates(
                http_session, ci, text, chunk_dir, semaphore,
                emotion=emotion, prev_best_mfcc=prev_best_mfcc,
                executor=executor, api_log=api_log,
                extra=extra
            )

            # Mark closing chunk
            if ci == len(blocks) - 1:
                chunk_meta['is_closing'] = True
                (chunk_dir / f"c{ci:02d}_meta.json").write_text(
                    json.dumps(chunk_meta, indent=2))

            all_meta.append(chunk_meta)
            total_api_calls += sum(1 for c in chunk_meta['candidates'] if not c.get('error'))
            total_chars_sent += len(text) * len(chunk_meta['candidates'])
            total_filtered += scores['filtered_count']

    executor.shutdown(wait=False)

    # Generate picker page
    generate_picker_html(session_id, session_dir, blocks, all_meta)

    # Write session manifest
    run_ended = _now_iso()
    manifest = {
        'script_id': session_id,
        'total_chunks': len(blocks),
        'category': category,
        'emotion': emotion,
        'generated_at': run_started,
        'completed_at': run_ended,
        'total_candidates': total_api_calls,
        'total_api_calls': len(api_log),
        'total_characters_sent': total_chars_sent,
        'estimated_cost_usd': round(total_chars_sent / 1000 * 0.003, 2),
        'generation_time_seconds': round(
            (datetime.fromisoformat(run_ended.replace('Z', '+00:00')) -
             datetime.fromisoformat(run_started.replace('Z', '+00:00'))).total_seconds()
        ),
        'chunks_below_prefilter': total_filtered,
        'preprocessing_log': preprocess_log,
        'blocks': [{'index': i, 'text': t, 'chars': len(t), 'pause': p}
                   for i, (t, p) in enumerate(blocks)],
        'status': 'CANDIDATES_READY',
    }
    (session_dir / 'session-manifest.json').write_text(json.dumps(manifest, indent=2))

    # Update generation log
    gen_log['runs'].append({
        'started_at': run_started,
        'completed_at': run_ended,
        'scripts_processed': [session_id],
        'total_api_calls': len(api_log),
        'total_characters': total_chars_sent,
        'total_cost_estimate': manifest['estimated_cost_usd'],
        'errors': sum(1 for a in api_log if a.get('status', 200) != 200),
        'retries': sum(1 for a in api_log if a.get('attempt', 0) > 0),
    })
    _save_gen_log(gen_log, gen_log_path)

    # Upload to R2
    print(f"\n{'='*70}")
    print(f"  UPLOADING TO R2")
    print(f"{'='*70}")
    uploaded, r2_errors = upload_session_to_r2(session_dir, session_id)

    # Summary
    print(f"\n{'='*70}")
    print(f"  VAULT BUILD COMPLETE — {session_id}")
    print(f"{'='*70}")
    print(f"  Chunks: {len(blocks)}")
    print(f"  Candidates generated: {total_api_calls}")
    print(f"  Pre-filter failures: {total_filtered}")
    print(f"  API calls logged: {len(api_log)}")
    print(f"  Estimated cost: £{manifest['estimated_cost_usd']:.2f}")
    print(f"  R2: {uploaded} uploaded, {r2_errors} errors")
    print(f"  Picker: {session_dir / 'review.html'}")
    print(f"\n  NEXT: Open review.html, pick winners, then run vault-assemble.py")

    return manifest


async def main():
    parser = argparse.ArgumentParser(
        description='Vault Builder — Generate TTS candidates for human review')
    parser.add_argument('script', nargs='?',
                        help='Path to script .txt file')
    parser.add_argument('--batch', metavar='DIR',
                        help='Process all scripts in directory')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show plan without generating audio')
    parser.add_argument('--inventory-only', action='store_true',
                        help='Only generate inventory.json, no audio')
    parser.add_argument('--no-upload', action='store_true',
                        help='Skip R2 upload')
    parser.add_argument('--extra', type=int, default=0,
                        help='Generate N extra candidates per chunk (on top of standard count)')
    parser.add_argument('--only-chunks', metavar='LIST',
                        help='Only process these chunk indices (comma-separated, e.g. 13,27,28)')
    args = parser.parse_args()

    # Ensure vault directory exists
    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    if args.inventory_only:
        inv = generate_inventory("content/scripts", VAULT_DIR / "inventory.json")
        # Validation
        under_50 = [e for e in inv if e['char_count'] < 50 and not e['is_opening']]
        over_300 = [e for e in inv if e['char_count'] > 300]
        opening_over_60 = [e for e in inv if e['is_opening'] and e['char_count'] > 60]
        print(f"\nValidation:")
        print(f"  Non-opening blocks <50 chars: {len(under_50)}")
        print(f"  Blocks >300 chars: {len(over_300)}")
        print(f"  Opening blocks >60 chars: {len(opening_over_60)}")
        if under_50:
            for e in under_50[:10]:
                print(f"    {e['script_id']} c{e['chunk_index']}: "
                      f"{e['char_count']}ch \"{e['text'][:50]}\"")
        return

    if args.batch:
        scripts_dir = Path(args.batch)
        skip = {'TEMPLATE.txt', 'test-voice-consistency.txt', 'SCRIPT-INVENTORY.md'}
        scripts = sorted([
            f for f in scripts_dir.glob("*.txt")
            if f.name not in skip
            and not re.search(r'-v\d+\.txt$', f.name)
        ])
        print(f"Batch mode: {len(scripts)} scripts")

        results = []
        for script in scripts:
            manifest = await build_session(script, dry_run=args.dry_run, extra=args.extra, only_chunks=args.only_chunks)
            if manifest:
                results.append(manifest)

        if results and not args.dry_run:
            total_cost = sum(m['estimated_cost_usd'] for m in results)
            total_calls = sum(m['total_api_calls'] for m in results)
            send_notification(
                f"Vault Batch Complete — {len(results)} sessions",
                f"Sessions: {', '.join(m['script_id'] for m in results)}\n"
                f"Total API calls: {total_calls}\n"
                f"Estimated cost: £{total_cost:.2f}\n"
                f"Pre-filter failures: {sum(m['chunks_below_prefilter'] for m in results)}"
            )
    elif args.script:
        manifest = await build_session(args.script, dry_run=args.dry_run, extra=args.extra, only_chunks=args.only_chunks)
        if manifest and not args.dry_run:
            send_notification(
                f"Vault Build Complete — {manifest['script_id']}",
                f"Session: {manifest['script_id']}\n"
                f"Chunks: {manifest['total_chunks']}\n"
                f"Candidates: {manifest['total_candidates']}\n"
                f"Cost: £{manifest['estimated_cost_usd']:.2f}\n"
                f"Pre-filter failures: {manifest['chunks_below_prefilter']}\n"
                f"Picker: content/audio-free/vault/{manifest['script_id']}/review.html"
            )
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
