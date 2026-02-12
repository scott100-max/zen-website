#!/usr/bin/env python3
"""
Generate 20 new Fish Audio candidates for each of the 5 chunks (c00-c04)
in the narrator-welcome vault session.

- Sequential by chunk (tonal scoring requires previous chunk's best MFCC)
- 2-second delay between API calls
- Scores each candidate
- Uploads each WAV to R2
- Updates meta.json per chunk
"""

import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.chdir(Path(__file__).parent)

# ---------------------------------------------------------------------------
# Load build-session-v3.py scoring functions
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
VAULT_DIR = Path("content/audio-free/vault/narrator-welcome")
R2_BUCKET = "salus-mind"
FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"
FISH_API_KEY = "0f3ab7558feb4983bc7b4c623ad38eef"
SAMPLE_RATE = 44100
SCORE_FILTER_THRESHOLD = 0.30
CANDIDATES_PER_CHUNK = 20
DELAY_BETWEEN_CALLS = 2.0  # seconds

ALL_CHUNKS = ["c00", "c01", "c02", "c03", "c04", "c05"]
# Only generate for new/changed chunks (c01 & c02 are rescripted)
CHUNKS = ["c01", "c02"]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fish_tts_call(text, wav_path):
    """Call Fish Audio TTS API, save as WAV."""
    import requests

    mp3_tmp = str(wav_path) + ".tmp.mp3"

    payload = {
        "text": text,
        "reference_id": FISH_VOICE_ID,
        "format": "mp3",
        "temperature": 0.3,
        "version": "v3-hd",
        "emotion": "calm",
        "prosody": {"speed": 0.95, "volume": 0},
        "sample_rate": SAMPLE_RATE,
    }
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(4):
        try:
            resp = requests.post(FISH_API_URL, json=payload, headers=headers, timeout=300)
            if resp.status_code == 429:
                wait = 2 ** attempt + 1
                print(f"      429 rate-limit -> wait {wait}s")
                time.sleep(wait)
                continue
            if resp.status_code != 200:
                raise Exception(f"Fish API {resp.status_code}: {resp.text[:200]}")
            Path(mp3_tmp).write_bytes(resp.content)
            break
        except Exception as e:
            if attempt < 3 and ("timeout" in str(e).lower() or "429" in str(e)):
                time.sleep(2 ** attempt)
                continue
            if attempt == 3:
                raise
            raise
    else:
        raise Exception("Failed after 4 attempts")

    # Convert MP3 -> WAV
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


def score_wav(wav_path, prev_mfcc=None):
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

    return details, mfcc


def upload_to_r2(local_path, r2_key):
    """Upload a file to R2."""
    cmd = [
        'npx', 'wrangler', 2, 'object', 'put',
        f'{R2_BUCKET}/{r2_key}',
        f'--file={local_path}',
        '--remote',
        '--content-type=audio/wav'
    ]
    # Fix: r2 must be string
    cmd[2] = 'r2'
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent))
    if result.returncode != 0:
        print(f"R2 FAIL: {result.stderr[:150]}")
        return False
    return True


def get_best_candidate_mfcc(meta):
    """Find best unfiltered candidate from meta, return its MFCC."""
    candidates = meta.get('candidates', [])
    unfiltered = [c for c in candidates if not c.get('filtered', False)
                  and c.get('composite_score') is not None]
    if not unfiltered:
        unfiltered = [c for c in candidates if c.get('composite_score') is not None]
    if not unfiltered:
        return None

    best = max(unfiltered, key=lambda c: c['composite_score'])
    chunk_dir = VAULT_DIR / f"c{meta['chunk_index']:02d}"
    wav_path = chunk_dir / best['filename']
    if wav_path.exists():
        return build.compute_mfcc_profile(str(wav_path))
    return None


def process_chunk(chunk_id, chunk_idx, prev_best_mfcc):
    """Generate 20 new candidates for one chunk, score, upload, update meta."""
    chunk_dir = VAULT_DIR / chunk_id
    meta_path = chunk_dir / f"{chunk_id}_meta.json"

    with open(meta_path, 'r') as f:
        meta = json.load(f)

    text = meta['text']

    # Find highest existing version
    existing_wavs = sorted(chunk_dir.glob(f"{chunk_id}_v*.wav"))
    if existing_wavs:
        last_stem = existing_wavs[-1].stem
        start_v = int(last_stem.split('_v')[1]) + 1
    else:
        start_v = 0

    print(f"\n{'='*70}")
    print(f"  CHUNK {chunk_idx}: \"{text}\"")
    print(f"  ({meta['char_count']} chars, {len(existing_wavs)} existing, "
          f"new versions v{start_v:02d}-v{start_v + CANDIDATES_PER_CHUNK - 1:02d})")
    print(f"{'='*70}")

    new_candidates = []
    best_new_score = None
    best_new_version = None
    best_new_mfcc = None

    for i in range(CANDIDATES_PER_CHUNK):
        v = start_v + i
        wav_path = chunk_dir / f"{chunk_id}_v{v:02d}.wav"
        r2_key = f"vault/narrator-welcome/{chunk_id}/{chunk_id}_v{v:02d}.wav"

        print(f"\n  [{i+1}/{CANDIDATES_PER_CHUNK}] v{v:02d}...", end=" ", flush=True)

        try:
            fish_tts_call(text, wav_path)
            details, mfcc = score_wav(str(wav_path), prev_best_mfcc)

            status = "FILTERED" if details.get('filtered') else "OK"
            tone_info = f" tone={details['tone_dist']:.4f}" if prev_best_mfcc is not None else ""
            print(f"score={details['combined_score']:.3f} "
                  f"(q={details['score']:.3f}{tone_info} "
                  f"dur={details['duration']:.1f}s) {status}", end="", flush=True)

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
                'generated_at': now_iso(),
            }
            new_candidates.append(entry)

            # Track best unfiltered
            if not details.get('filtered'):
                score = details['combined_score']
                if best_new_score is None or score > best_new_score:
                    best_new_score = score
                    best_new_version = v
                    best_new_mfcc = mfcc

            # Upload to R2
            print(" -> R2...", end=" ", flush=True)
            if upload_to_r2(str(wav_path), r2_key):
                print("OK")
            else:
                print("FAIL")

        except Exception as e:
            print(f"FAILED: {e}")
            new_candidates.append({
                'version': v,
                'filename': wav_path.name,
                'error': str(e),
                'filtered': True,
                'generated_at': now_iso(),
            })

        # Rate limit between calls
        if i < CANDIDATES_PER_CHUNK - 1:
            time.sleep(DELAY_BETWEEN_CALLS)

    # Update meta with new candidates appended
    meta['candidates'].extend(new_candidates)
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)

    # Write scores file
    scores = {
        'chunk_index': chunk_idx,
        'total_candidates': len(meta['candidates']),
        'filtered_count': sum(1 for c in meta['candidates'] if c.get('filtered')),
        'scores': [{
            'version': c['version'],
            'composite_score': c.get('composite_score'),
            'quality_score': c.get('quality_score'),
            'tonal_distance': c.get('tonal_distance_to_prev'),
            'duration': c.get('duration_seconds'),
            'filtered': c.get('filtered', False),
        } for c in meta['candidates']],
    }
    scores_path = chunk_dir / f"{chunk_id}_scores.json"
    with open(scores_path, 'w') as f:
        json.dump(scores, f, indent=2)

    # Upload meta + scores to R2
    upload_to_r2(str(meta_path), f"vault/narrator-welcome/{chunk_id}/{chunk_id}_meta.json")
    upload_to_r2(str(scores_path), f"vault/narrator-welcome/{chunk_id}/{chunk_id}_scores.json")

    # Summary
    new_ok = sum(1 for c in new_candidates if not c.get('filtered', False))
    print(f"\n  --- Chunk {chunk_idx} Summary ---")
    print(f"  Generated: {len(new_candidates)}, Passed: {new_ok}, "
          f"Filtered: {len(new_candidates) - new_ok}")
    if best_new_version is not None:
        print(f"  Best new: v{best_new_version:02d} (score={best_new_score:.4f})")

    all_unfiltered = [c for c in meta['candidates']
                      if not c.get('filtered', False)
                      and c.get('composite_score') is not None]
    if all_unfiltered:
        overall_best = max(all_unfiltered, key=lambda c: c['composite_score'])
        print(f"  Overall best: v{overall_best['version']:02d} "
              f"(score={overall_best['composite_score']:.4f})")

    # Return best MFCC for this chunk (for tonal scoring of next chunk)
    if best_new_mfcc is not None:
        return best_new_mfcc
    return get_best_candidate_mfcc(meta)


def main():
    print("=" * 70)
    print(f"  NARRATOR-WELCOME: {CANDIDATES_PER_CHUNK} candidates x {len(CHUNKS)} chunks = {CANDIDATES_PER_CHUNK * len(CHUNKS)} API calls")
    print(f"  Chunks: {', '.join(CHUNKS)}")
    print(f"  Started: {now_iso()}")
    print(f"  Rate limit: {DELAY_BETWEEN_CALLS}s between calls")
    print("=" * 70)

    start_time = time.time()
    prev_best_mfcc = None

    for chunk_id in CHUNKS:
        chunk_idx = int(chunk_id[1:])  # absolute index in session

        # Get EXISTING best MFCC for the previous chunk (tonal scoring)
        if chunk_idx == 0:
            prev_best_mfcc = None  # c00 is opening, no conditioning
        else:
            prev_chunk_id = f"c{chunk_idx - 1:02d}"
            prev_meta_path = VAULT_DIR / prev_chunk_id / f"{prev_chunk_id}_meta.json"
            with open(prev_meta_path, 'r') as f:
                prev_meta = json.load(f)
            prev_best_mfcc = get_best_candidate_mfcc(prev_meta)

        mfcc = process_chunk(chunk_id, chunk_idx, prev_best_mfcc)

    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    print(f"\n{'='*70}")
    print(f"  ALL DONE: {mins}m {secs}s elapsed")
    print(f"  Finished: {now_iso()}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
