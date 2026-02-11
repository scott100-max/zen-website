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
</head>
<body>
<h1>Vault Picker &mdash; __SESSION_ID__</h1>
<p class="meta">A/B Tournament v2</p>
<p class="meta">Audio base: <input id="basePath" value="__DEFAULT_BASE_PATH__" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:4px;color:#f0eefc;padding:2px 6px;font-size:.72rem;width:420px" onchange="updateBasePath()"></p>
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

<script>
var SESSION_ID = '__SESSION_ID__';
var chunkData = __CHUNKS_DATA__;

var PICKS_API = '__PICKS_API_URL__';
var AUTH_TOKEN = '__PICKS_AUTH_TOKEN__';
var basePath = document.getElementById('basePath').value.replace(/\/+$/, '');
var initialState = {};
var abState = {};
var currentChunkArrayIdx = 0;
var pickCounter = 0;
var pickedThisSession = {};

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

function getTop(chunk) {
  var result = [];
  for (var i = 0; i < chunk.candidates.length; i++) {
    if (!chunk.candidates[i].filtered) result.push(chunk.candidates[i]);
  }
  result.sort(function(a, b) { return b.score - a.score; });
  return result;
}

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
    html += '<div class="ab-side">';
    html += '<div class="ab-label label-a">A <span style="font-size:.6em;opacity:.7">(v' + a.v + ')</span></div>';
    html += '<audio controls preload="auto" src="' + basePath + '/' + a.file + '"></audio>';
    html += '<div class="ab-stats"><span class="score">' + a.score.toFixed(3) + '</span><span class="dur">' + a.dur.toFixed(1) + 's</span>';
    if (chunk.idx > 0) html += '<span class="tone">t' + a.tone.toFixed(4) + '</span>';
    html += '</div></div>';
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

  var cmp = document.getElementById('abCompare');
  if (cmp) {
    cmp.style.opacity = '0.5';
    setTimeout(function() { cmp.style.opacity = '1'; }, 50);
  }

  var navBtns = document.querySelectorAll('.chunk-nav button');
  for (var i = 0; i < navBtns.length; i++) navBtns[i].classList.remove('current');
  var navBtn = document.getElementById('nav-' + chunk.idx);
  if (navBtn) navBtn.classList.add('current');

  logDebug('Rendered chunk ' + chunk.idx + (state.done ? ' (done, winner=v' + state.winner + ')' : ' (round ' + state.round + ', A=v' + (state.champion ? state.champion.v : '?') + ' vs B=v' + ((state.top5[state.challengerIdx] || {}).v || '?') + ')'));
}

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
    state.rejected.push(a.v);
    state.rejected.push(b.v);
    showToast('Rejected both v' + a.v + ' + v' + b.v);

    var remaining = [];
    for (var i = 0; i < state.top5.length; i++) {
      if (state.rejected.indexOf(state.top5[i].v) === -1) remaining.push(i);
    }

    if (remaining.length === 0) {
      state.done = true;
      state.winner = null;
      state.round = 0;
      logDebug('All candidates rejected for chunk ' + chunk.idx);
      showToast('No winner \u2014 all rejected');
    } else if (remaining.length === 1) {
      state.winner = state.top5[remaining[0]].v;
      state.done = true;
      state.round = 0;
      pickedThisSession[chunk.idx] = 'a';
      logDebug('Last candidate wins chunk ' + chunk.idx + ': v' + state.winner);
      showToast('PICKED: v' + state.winner + ' (last standing)');
    } else {
      state.champion = state.top5[remaining[0]];
      state.challengerIdx = remaining[1];
      state.round = (state.round || 0) + 1;
      logDebug('Both rejected, ' + remaining.length + ' remain. Loading next pair.');
    }

    try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }
    renderChunk();
    return;
  } else {
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

document.addEventListener('keydown', function(e) {
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  if (e.key === 'a' || e.key === 'A') pickSide('a');
  else if (e.key === 'b' || e.key === 'B') pickSide('b');
  else if (e.key === 's' || e.key === 'S') pickSide('same');
  else if (e.key === 'ArrowLeft') goToChunk(currentChunkArrayIdx - 1);
  else if (e.key === 'ArrowRight') goToChunk(currentChunkArrayIdx + 1);
});

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
