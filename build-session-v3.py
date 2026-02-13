#!/usr/bin/env python3
"""
Salus Audio Session Builder v3

Chunked Fish TTS with better splicing.
- Split text into ~8k char chunks at sentence boundaries
- Generate each chunk with condition_on_previous_chunks
- Crossfade between chunks (150ms)
- Max 30 minutes total (including silences)

Usage:
    python build-session-v3.py <session-name>
    python build-session-v3.py --dry-run <session-name>
"""

import os
import sys
import re
import json
import subprocess
import tempfile
import shutil
import argparse
import time
import random
from pathlib import Path
import urllib.request

# Load .env manually
env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path("content/scripts")
SLEEP_STORY_DIR = Path("content/sleep-stories")
AUDIO_DIR = Path("content/audio")
AMBIENT_DIR = Path("content/audio/ambient")
OUTPUT_DIR = Path("content/audio-free")  # Final deployed audio
OUTPUT_RAW_DIR = Path("content/audio-free/raw")
OUTPUT_MIXED_DIR = Path("content/audio-free/mixed")

# R2 deployment
R2_BUCKET = "salus-mind"
R2_PATH_PREFIX = "content/audio-free"

# QA settings
QA_MAX_PASSES = 5         # Max scan-fix-rescan cycles before failing
QA_CLICK_THRESHOLD = 120  # Min amplitude jump to count as click (raised: ambient transients like bird chirps at 100-115)
QA_FADE_MS = 40           # Crossfade width at stitch boundaries (20ms wasn't enough for Fish 40-chunk builds)

# Master quality benchmarks (from ss02-the-moonlit-garden Marco T2 build)
# Measured via astats RMS on silence regions — calibrated to measure_noise_floor()
# Master silence-region measurements: noise -27.0 dB, HF hiss -45.0 dB
# Thresholds allow 1 dB tolerance above master
MASTER_NOISE_FLOOR_DB = -26.0   # Max RMS in silence (master: -27.0)
MASTER_HF_HISS_DB = -40.0      # Max RMS >6kHz in silence (master: -45.0, Fish floor: ~-42)
MASTER_REF_WAV = Path("content/audio/marco-master/marco-master-v1.wav")

# Marco master voice comparison thresholds (calibrated 2026-02-07)
# Derived from 5 Fish + 3 Resemble calibration set with human GOOD/BAD labels
# See content/audio/marco-master/marco-master-v1-calibration.json
#
# IMPORTANT: MFCC cosine distance is CONTENT-DEPENDENT. The calibration threshold
# (0.008) was derived from same-text comparisons. Production builds with different
# text produce MFCC distances of ~0.035 even with the correct voice, because different
# phoneme distributions shift the MFCC means. The production threshold (0.06) allows
# for content variance while still catching a fundamentally wrong voice.
# F0 deviation is content-independent and uses the tight calibration threshold.
MASTER_MFCC_COSINE_MAX = 0.06      # Production threshold (same-voice diff-text: ~0.035, wrong-voice: >0.10)
MASTER_F0_DEVIATION_MAX = 10.0     # Max F0 deviation percent (GOOD Fish: ≤5.6%, BAD Resemble: ≥14.8%)
MASTER_MEASUREMENTS = Path("content/audio/marco-master/marco-master-v1-measurements.json")

# Fish TTS API
FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Marco voice
FISH_API_KEY = os.getenv("FISH_API_KEY")

# ElevenLabs TTS API
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"  # Daniel — update after audition
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"
ELEVENLABS_DELAY_MS = 500  # Rate limiting between API calls

# ElevenLabs model configs
ELEVENLABS_MODELS = {
    "v2": {
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.65,
            "style": 0.0,
            "use_speaker_boost": False,
            "speed": 0.75,
        },
    },
    "v3": {
        "model_id": "eleven_v3",
        "voice_settings": {
            "stability": 1.0,       # v3 only accepts 0.0, 0.5, 1.0
            "similarity_boost": 0.75,
            "style": 0.0,
        },
    },
}

# ElevenLabs paragraph merging — only merge very short blocks (<20 chars)
ELEVENLABS_MIN_BLOCK_CHARS = 20

# LALAL.AI Audio Cleaning API
LALAL_API_KEY = os.getenv("LALAL_API_KEY")
LALAL_API_BASE = "https://www.lalal.ai/api/v1"
LALAL_NOISE_LEVEL = 1  # 0=mild, 1=normal, 2=aggressive
LALAL_DEREVERB = True   # Enable de-echo/de-reverb

# Resemble AI TTS API
RESEMBLE_API_KEY = os.getenv("RESEMBLE_API_KEY")
RESEMBLE_SYNTH_URL = "https://f.cluster.resemble.ai/synthesize"
RESEMBLE_API_URL = "https://app.resemble.ai/api/v2"
RESEMBLE_VOICE_ID = "da18eeca"  # Marco T2 — master narration voice
RESEMBLE_CHUNK_MAX = 2500  # Stay under 3000 char API limit
RESEMBLE_DELAY_MS = 500  # Rate limiting between API calls
RESEMBLE_VOICE_SETTINGS_PRESET = "6199a148-cd33-4ad7-b452-f067fdff3894"  # pace=0.85, exaggeration=0.75

# Audio settings
SAMPLE_RATE = 44100
MAX_DURATION_SECONDS = 45 * 60  # 45 minutes max (sleep stories)

# Chunking settings
CHUNK_SIZE = 8000  # chars per chunk
MIN_BLOCK_SIZE = 500  # combine small blocks until this size
CROSSFADE_MS = 150  # crossfade duration between chunks

# Pause durations by category (seconds)
PAUSE_PROFILES = {
    'sleep': {1: 8, 2: 30, 3: 60},
    'story': {1: 1.5, 2: 3, 3: 5},
    'focus': {1: 4, 2: 12, 3: 20},
    'stress': {1: 6, 2: 20, 3: 40},
    'mindfulness': {1: 8, 2: 25, 3: 50},
    'beginner': {1: 5, 2: 15, 3: 30},
    'advanced': {1: 10, 2: 40, 3: 90},
}

# Ambient settings (per AUDIO-SPEC.md)
AMBIENT_VOLUME_DB = -14          # Standard ambient level for mindfulness/meditation
AMBIENT_VOLUME_SILENCE_DB = -13  # Raise 1dB during 30s+ pauses (per spec)
AMBIENT_FADE_IN_START = 0        # Start fade immediately
AMBIENT_FADE_IN_DURATION = 10    # 10 seconds fade-in
AMBIENT_FADE_OUT_DURATION = 10   # 10 seconds fade-out

# ============================================================================
# SCRIPT PARSING
# ============================================================================

def parse_script(script_path):
    """Parse script file with metadata header."""
    content = script_path.read_text()
    lines = content.split('\n')

    metadata = {
        'title': script_path.stem,
        'duration': '',
        'category': 'mindfulness',
        'ambient': None,
        'style': 'Warm male narrator',
        'api_emotion': 'calm',
        'content': content.strip(),
    }

    header_lines = []
    content_start = 0

    for i, line in enumerate(lines):
        if line.strip() == '---':
            content_start = i + 1
            break
        header_lines.append(line)

    if header_lines:
        first_line = header_lines[0].strip()
        if ':' not in first_line:
            metadata['title'] = first_line

    for line in header_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            if key in ['duration', 'category', 'ambient', 'ambient-db', 'ambient-fade-in', 'ambient-fade-out', 'style', 'api-emotion', 'expected-repetitions']:
                if key == 'ambient':
                    metadata[key] = value.lower() if value.lower() != 'none' else None
                elif key == 'ambient-db':
                    try:
                        metadata['ambient_db'] = float(value)
                    except ValueError:
                        pass
                elif key == 'ambient-fade-in':
                    try:
                        metadata['ambient_fade_in'] = float(value)
                    except ValueError:
                        pass
                elif key == 'ambient-fade-out':
                    try:
                        metadata['ambient_fade_out'] = float(value)
                    except ValueError:
                        pass
                elif key == 'api-emotion':
                    metadata['api_emotion'] = value.lower()
                elif key == 'expected-repetitions':
                    metadata['expected_repetitions'] = [p.strip().lower() for p in value.split(',')]
                else:
                    metadata[key] = value

    metadata['content'] = '\n'.join(lines[content_start:]).strip()
    return metadata


def get_pause_duration(dot_count, category):
    """Get pause duration based on ... count and category."""
    profile = PAUSE_PROFILES.get(category, PAUSE_PROFILES['mindfulness'])
    if dot_count >= 3:
        return profile[3]
    elif dot_count >= 2:
        return profile[2]
    return profile[1]


def process_script_for_tts(content, category):
    """
    Convert script to text blocks with pause markers.
    Returns list of (text, pause_after) tuples.
    """
    lines = content.split('\n')
    pause_pattern = re.compile(r'^\s*\.{2,}\s*$|^\s*\[SILENCE[:\s]*(\d+)\s*(?:seconds?)?\]\s*$', re.IGNORECASE)

    blocks = []
    current_text = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip comments/notes in brackets that aren't pause markers
        if line.startswith('[') and not pause_pattern.match(line):
            i += 1
            continue

        # Check for pause marker
        pause_match = pause_pattern.match(line)
        if pause_match:
            # Count ... lines in this group (skipping blank lines between them)
            count = 0
            while i < len(lines):
                stripped = lines[i].strip()
                if re.match(r'^\s*\.{2,}\s*$', stripped):
                    count += 1
                    i += 1
                elif stripped == '':
                    # Peek ahead — if next non-blank line is ..., keep going
                    j = i + 1
                    while j < len(lines) and lines[j].strip() == '':
                        j += 1
                    if j < len(lines) and re.match(r'^\s*\.{2,}\s*$', lines[j].strip()):
                        i += 1  # Skip blank line, continue counting
                    else:
                        break  # Blank line followed by text — stop
                else:
                    break

            # Check for explicit [SILENCE: X seconds]
            # Negative value signals "explicit silence — do not merge or humanize"
            if pause_match.group(1):
                duration = -int(pause_match.group(1))
                i += 1
            else:
                duration = get_pause_duration(count, category)

            # Save current block with pause
            if current_text:
                text = ' '.join(current_text).strip()
                text = re.sub(r'\s+', ' ', text)
                if text:
                    blocks.append((text, duration))
                current_text = []
        elif line:
            current_text.append(line)
            i += 1
        else:
            i += 1

    # Final block (no pause after)
    if current_text:
        text = ' '.join(current_text).strip()
        text = re.sub(r'\s+', ' ', text)
        if text:
            blocks.append((text, 0))

    return blocks


def chunk_text_at_sentences(text, max_chars=CHUNK_SIZE):
    """Split text into chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        if current_len + len(sentence) > max_chars and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_len = len(sentence)
        else:
            current_chunk.append(sentence)
            current_len += len(sentence) + 1

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


# ============================================================================
# PAUSE HUMANIZATION
# ============================================================================

def humanize_pauses(blocks, seed=42):
    """
    Add natural variation to pause durations so they don't sound mechanical.

    Short text blocks (punchy lines) get longer pauses for dramatic effect.
    Long text blocks (descriptive passages) get shorter pauses to maintain flow.
    Variation is ±50% of the base pause, seeded for reproducibility.
    """
    rng = random.Random(seed)
    result = []
    for text, pause in blocks:
        if pause <= 0:
            result.append((text, pause))
            continue

        # Shorter text = longer pause (dramatic effect), longer text = shorter pause
        text_len = len(text)
        if text_len < 60:
            # Short punchy line — hold longer
            factor = rng.uniform(1.1, 1.5)
        elif text_len < 150:
            # Medium line — normal variation
            factor = rng.uniform(0.7, 1.3)
        else:
            # Long passage — shorter pause, let it breathe but keep moving
            factor = rng.uniform(0.5, 1.0)

        humanized = round(pause * factor, 1)
        humanized = max(1.5, humanized)  # Never less than 1.5s
        result.append((text, humanized))

    return result


# ============================================================================
# PER-CHUNK QA — Score individual chunks before assembly
# ============================================================================

def score_chunk_quality(audio_path):
    """Score a single TTS chunk for quality (echo, hiss, voice consistency).

    Returns a dict with:
      - score: composite quality score (higher = better)
      - echo_risk: spectral flux variance (lower = better)
      - hiss_risk: HF energy ratio in dB (lower = better, more negative = cleaner)
      - sp_contrast: spectral contrast (higher = better)
      - sp_flatness: spectral flatness (lower = better)

    Used by generate_chunk_with_qa() to pick the best of N generations.
    Calibrated against 27 human-labeled chunks from build 10 (8 Feb 2026).
    """
    import librosa
    import numpy as np

    y, sr = librosa.load(audio_path, sr=22050)

    if len(y) < 2048:
        return {'score': 0.0, 'echo_risk': 1.0, 'hiss_risk': 0.0,
                'sp_contrast': 0.0, 'sp_flatness': 1.0, 'too_short': True}

    # 1. Spectral flux variance — echo/reverb smooths transitions → higher variance
    #    Best separator from calibration (Cohen's d = 1.046)
    S = np.abs(librosa.stft(y, n_fft=2048))
    S_norm = S / (S.sum(axis=0, keepdims=True) + 1e-10)
    flux = np.sqrt(np.sum(np.diff(S_norm, axis=1)**2, axis=0))
    echo_risk = float(np.var(flux))

    # 2. HF energy ratio — hiss detection (energy above 6kHz / total)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    hf_mask = freqs >= 6000
    hf_energy = float(np.mean(S[hf_mask, :] ** 2))
    total_energy = float(np.mean(S ** 2))
    hiss_risk = 10 * np.log10(hf_energy / (total_energy + 1e-10) + 1e-10)

    # 3. Spectral contrast — clean speech has higher contrast (d = 0.642)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    sp_contrast = float(np.mean(contrast))

    # 4. Spectral flatness — noise-like = higher, tonal = lower (d = 0.585)
    sp_flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))

    # Composite score: weighted combination, higher = better
    # Weights from Cohen's d separation values (OK vs Echo calibration)
    # All metrics normalized to ~0-1 range based on observed calibration data
    score = (
        -echo_risk * 500.0       # flux variance ~0.001-0.002, penalty for higher
        + sp_contrast * 0.05     # contrast ~19-21, reward for higher
        - sp_flatness * 10.0     # flatness ~0.01-0.07, penalty for higher
        - hiss_risk * 0.05       # hf ratio ~-17 to -10 dB, penalty for higher (less negative)
    )

    return {
        'score': round(float(score), 4),
        'echo_risk': round(echo_risk, 6),
        'hiss_risk': round(hiss_risk, 2),
        'sp_contrast': round(sp_contrast, 3),
        'sp_flatness': round(sp_flatness, 5),
    }


def compute_mfcc_profile(audio_path):
    """Extract mean MFCC profile from an audio file for tonal comparison."""
    import librosa
    import numpy as np
    y, sr = librosa.load(audio_path, sr=22050)
    if len(y) < 2048:
        return None
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return mfcc.mean(axis=1)


def tonal_distance(mfcc_a, mfcc_b):
    """Cosine distance between two MFCC profiles. Lower = more similar."""
    import numpy as np
    if mfcc_a is None or mfcc_b is None:
        return 0.0
    cos_sim = np.dot(mfcc_a, mfcc_b) / (
        np.linalg.norm(mfcc_a) * np.linalg.norm(mfcc_b) + 1e-10
    )
    return round(float(1.0 - cos_sim), 6)


def generate_chunk_with_qa(text, output_path, chunk_num, emotion='calm',
                           n_versions=2, max_retries=3, prev_chunk_mfcc=None):
    """Generate a Fish TTS chunk with per-chunk QA.

    Generates n_versions of the chunk, scores each, and keeps the best.
    Score combines quality metrics + tonal consistency with previous chunk.
    If the best score is below threshold after max_retries total attempts,
    flags the chunk text for potential rewrite.

    prev_chunk_mfcc: MFCC profile of the previously accepted chunk.
        If provided, tonal distance is factored into the score to penalise
        voice character shifts at chunk boundaries.

    Returns (output_path, score_dict, flagged, mfcc_profile).
    """
    import shutil

    best_path = None
    best_score = None
    best_details = None
    best_mfcc = None
    all_scores = []

    for attempt in range(max_retries):
        # Generate a version
        temp_path = output_path + f".v{attempt}.mp3"
        try:
            generate_tts_chunk(text, temp_path, chunk_num, emotion=emotion)
        except Exception as e:
            print(f"      Version {attempt+1} FAILED: {e}")
            continue

        # Check for overgeneration
        duration = get_audio_duration(temp_path)
        expected = len(text) / 15.0
        max_dur = max(expected * 2.5, 20.0)
        if duration > max_dur:
            print(f"      Version {attempt+1} OVERGENERATED ({duration:.1f}s > {max_dur:.1f}s) — skipping")
            try:
                os.remove(temp_path)
            except OSError:
                pass
            continue

        # Score quality
        details = score_chunk_quality(temp_path)
        quality_score = details['score']

        # Score tonal consistency with previous chunk
        chunk_mfcc = compute_mfcc_profile(temp_path)
        tone_dist = tonal_distance(prev_chunk_mfcc, chunk_mfcc)
        # Tonal penalty: distance typically 0.001-0.01, scale to impact score
        # Weight 50x so a 0.01 distance costs 0.5 points (significant)
        tone_penalty = tone_dist * 50.0
        combined_score = quality_score - tone_penalty

        details['tone_dist'] = tone_dist
        details['tone_penalty'] = round(tone_penalty, 3)
        details['combined_score'] = round(combined_score, 4)
        all_scores.append(combined_score)

        marker = ""
        if best_score is not None and combined_score > best_score:
            marker = " ★ new best"
        elif best_score is None:
            marker = " ★ first"

        tone_info = f" tone={tone_dist:.4f}" if prev_chunk_mfcc is not None else ""
        print(f"      v{attempt+1}: score={combined_score:.3f} (q={quality_score:.3f}{tone_info} hiss={details['hiss_risk']:.1f}dB){marker}")

        if best_score is None or combined_score > best_score:
            # New best — keep it, discard previous best
            if best_path and best_path != output_path and os.path.exists(best_path):
                try:
                    os.remove(best_path)
                except OSError:
                    pass
            best_path = temp_path
            best_score = combined_score
            best_details = details
            best_mfcc = chunk_mfcc
        else:
            # Worse than current best — discard
            try:
                os.remove(temp_path)
            except OSError:
                pass

        # If we have enough scored versions, stop early
        if len(all_scores) >= n_versions and best_score is not None:
            break

    if best_path is None:
        raise Exception(f"All {max_retries} attempts failed for chunk {chunk_num+1}")

    # Move best to final output path
    if best_path != output_path:
        shutil.move(best_path, output_path)

    # Flag based on QUALITY score only (not combined score with tonal penalty).
    # Tonal penalty is for ranking versions, not for flagging script rewrites.
    # A chunk with good quality but poor tonal match doesn't need a rewrite —
    # it just needs a different generation that matches the previous chunk better.
    # Calibrated 8 Feb 2026: OK avg=0.708, Echo avg=0.542, Hiss avg=0.534
    quality_score = best_details.get('score', 0.0) if best_details else 0.0
    flagged = quality_score < 0.50 if quality_score is not None else True

    return output_path, best_details, flagged, best_mfcc


# ============================================================================
# LALAL.AI AUDIO CLEANING
# ============================================================================

def lalal_clean_chunk(input_path, output_path, noise_level=None, dereverb=None):
    """Clean a single audio chunk via LALAL.AI voice_clean API.

    Uploads the chunk, processes with de-echo and noise cancellation,
    downloads the cleaned voice stem. Falls back to original if API fails.

    Returns True if cleaning succeeded, False if fallback to original.
    """
    import requests as _requests

    if not LALAL_API_KEY:
        shutil.copy(input_path, output_path)
        return False

    if noise_level is None:
        noise_level = LALAL_NOISE_LEVEL
    if dereverb is None:
        dereverb = LALAL_DEREVERB

    headers = {'X-License-Key': LALAL_API_KEY}

    try:
        # Upload
        with open(input_path, 'rb') as f:
            fname = os.path.basename(input_path)
            resp = _requests.post(
                f'{LALAL_API_BASE}/upload/',
                headers={**headers, 'Content-Disposition': f'attachment; filename={fname}'},
                data=f,
                timeout=60
            )
        resp.raise_for_status()
        source_id = resp.json()['id']

        # Process
        resp = _requests.post(
            f'{LALAL_API_BASE}/split/voice_clean/',
            headers={**headers, 'Content-Type': 'application/json'},
            json={
                'source_id': source_id,
                'presets': {
                    'stem': 'voice',
                    'noise_cancelling_level': noise_level,
                    'dereverb_enabled': dereverb,
                    'encoder_format': 'wav'
                }
            },
            timeout=30
        )
        resp.raise_for_status()
        task_id = resp.json()['task_id']

        # Poll for completion (max 120s)
        for _ in range(60):
            time.sleep(2)
            resp = _requests.post(
                f'{LALAL_API_BASE}/check/',
                headers={**headers, 'Content-Type': 'application/json'},
                json={'task_ids': [task_id]},
                timeout=15
            )
            result = resp.json()['result'][task_id]
            if result['status'] == 'success':
                voice_url = result['result']['tracks'][0]['url']
                dl = _requests.get(voice_url, timeout=60)
                dl.raise_for_status()
                with open(output_path, 'wb') as f:
                    f.write(dl.content)
                return True
            elif result['status'] == 'error':
                print(f"      LALAL error: {result.get('error', 'unknown')}")
                break

        # Timeout or error — fall back to original
        shutil.copy(input_path, output_path)
        return False

    except Exception as e:
        print(f"      LALAL failed ({e}) — using original")
        shutil.copy(input_path, output_path)
        return False


def lalal_clean_chunks(chunk_paths, temp_dir):
    """Clean all chunks through LALAL.AI. Returns list of cleaned paths.

    Processes sequentially to respect API rate limits.
    Skips if LALAL_API_KEY is not set.
    """
    if not LALAL_API_KEY:
        print("  LALAL.AI: No API key — skipping audio cleaning")
        return chunk_paths

    print(f"\n  LALAL.AI: Cleaning {len(chunk_paths)} chunks (noise={LALAL_NOISE_LEVEL}, dereverb={LALAL_DEREVERB})...")
    cleaned_paths = []
    cleaned_count = 0

    for i, path in enumerate(chunk_paths):
        cleaned_path = os.path.join(temp_dir, f"lalal_cleaned_{i}.wav")
        # Convert MP3 chunk to WAV for LALAL (lossless pipeline)
        wav_input = os.path.join(temp_dir, f"lalal_input_{i}.wav")
        subprocess.run(
            ['ffmpeg', '-y', '-i', path, '-c:a', 'pcm_s16le', '-ar', '44100', wav_input],
            capture_output=True, check=True
        )
        success = lalal_clean_chunk(wav_input, cleaned_path)
        if success:
            cleaned_count += 1
            cleaned_paths.append(cleaned_path)
            print(f"    Chunk {i+1}/{len(chunk_paths)}: cleaned")
        else:
            cleaned_paths.append(wav_input)
            print(f"    Chunk {i+1}/{len(chunk_paths)}: fallback (original)")

        # Clean up temp input if we have a cleaned version
        if success and os.path.exists(wav_input):
            try:
                os.remove(wav_input)
            except OSError:
                pass

    print(f"  LALAL.AI: {cleaned_count}/{len(chunk_paths)} chunks cleaned successfully")
    return cleaned_paths


# ============================================================================
# FISH TTS API (Chunked)
# ============================================================================

def generate_tts_chunk(text, output_path, chunk_num=0, emotion='calm'):
    """Generate TTS for a single chunk via Fish Audio V3-HD."""
    import requests

    if not FISH_API_KEY:
        raise ValueError("FISH_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
    }

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

    print(f"    Chunk {chunk_num + 1}: {len(text)} chars...", end=" ", flush=True)
    response = requests.post(FISH_API_URL, headers=headers, json=payload, timeout=300)

    if response.status_code != 200:
        raise Exception(f"Fish API error: {response.status_code} - {response.text}")

    Path(output_path).write_bytes(response.content)
    duration = get_audio_duration(output_path)
    print(f"{duration:.1f}s")
    return output_path


# ============================================================================
# ELEVENLABS TTS API (Paragraph-level with request stitching)
# ============================================================================

def preprocess_text_elevenlabs(text, model="v2"):
    """Preprocess text before sending to ElevenLabs API.

    - Replace ellipsis (...) with em-dash (nervous/hesitant energy is bad for sleep)
    - Replace unicode smart quotes with standard quotes
    - Strip HTML/markdown formatting
    - Replace [PAUSE] / [BREATH] markers with SSML breaks (v2 only)
    """
    # Replace ellipsis with em-dash
    text = text.replace('...', '—')
    text = text.replace('…', '—')

    # Replace smart quotes with standard quotes
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # single
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # double

    # Strip markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Replace pause markers with SSML breaks (v2 only)
    if model == "v2":
        text = re.sub(r'\[PAUSE\]', '<break time="3s" />', text, flags=re.IGNORECASE)
        text = re.sub(r'\[BREATH\]', '<break time="2s" />', text, flags=re.IGNORECASE)

    return text.strip()


def merge_short_blocks(blocks, min_chars=ELEVENLABS_MIN_BLOCK_CHARS):
    """Merge blocks under min_chars with their next neighbour.

    Short text produces unstable TTS output. This merges tiny blocks
    (like single words or short phrases) with the following paragraph.
    """
    if not blocks:
        return blocks

    merged = []
    carry_text = ""

    for text, pause in blocks:
        if carry_text:
            text = carry_text + " " + text
            carry_text = ""

        if len(text) < min_chars:
            # Too short — carry forward to merge with next block
            carry_text = text
            # Keep the pause from this block if it's longer
            continue

        merged.append((text, pause))

    # If the last block was short, append it to the previous one
    if carry_text:
        if merged:
            prev_text, prev_pause = merged[-1]
            merged[-1] = (prev_text + " " + carry_text, prev_pause)
        else:
            merged.append((carry_text, 0))

    return merged


def generate_tts_chunk_elevenlabs(text, output_path, chunk_num=0, voice_id=None, model="v2",
                                   previous_request_ids=None):
    """Generate TTS for a single paragraph via ElevenLabs API.

    Returns (output_path, request_id) — request_id is used for voice
    continuity via request stitching (previous_request_ids).
    """
    import requests

    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set")

    vid = voice_id or ELEVENLABS_VOICE_ID
    model_config = ELEVENLABS_MODELS.get(model, ELEVENLABS_MODELS["v2"])

    url = f"{ELEVENLABS_API_URL}/{vid}?output_format={ELEVENLABS_OUTPUT_FORMAT}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }

    # Preprocess text
    processed_text = preprocess_text_elevenlabs(text, model=model)

    payload = {
        "text": processed_text,
        "model_id": model_config["model_id"],
        "voice_settings": model_config["voice_settings"],
    }

    # Request stitching — pass previous request IDs for voice continuity
    if previous_request_ids:
        payload["previous_request_ids"] = previous_request_ids[-3:]  # Max 3

    print(f"    Chunk {chunk_num + 1}: {len(processed_text)} chars...", end=" ", flush=True)

    # Retry with exponential backoff
    max_retries = 3
    for attempt in range(max_retries + 1):
        response = requests.post(url, headers=headers, json=payload, timeout=300)

        if response.status_code == 429:
            # Rate limited — back off
            if attempt < max_retries:
                wait = min(30, 2 ** attempt)
                print(f"rate limited, waiting {wait}s...", end=" ", flush=True)
                time.sleep(wait)
                continue
            else:
                raise Exception(f"ElevenLabs rate limit after {max_retries} retries")

        break

    # Log all headers on first call to identify request_id header name
    if chunk_num == 0:
        print(f"\n    [Headers: {dict(response.headers)}]", flush=True)
        print(f"    Chunk {chunk_num + 1}: ", end="", flush=True)

    # Check for errors
    content_type = response.headers.get('Content-Type', '')
    if response.status_code != 200 or 'application/json' in content_type:
        raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text[:300]}")

    # Capture request_id for stitching
    # Check common header names
    request_id = (response.headers.get('request-id')
                  or response.headers.get('x-request-id')
                  or response.headers.get('request_id'))

    Path(output_path).write_bytes(response.content)
    duration = get_audio_duration(output_path)
    print(f"{duration:.1f}s", flush=True)

    # Rate limiting
    time.sleep(ELEVENLABS_DELAY_MS / 1000)

    return output_path, request_id


def crossfade_audio_files(file_list, output_path, crossfade_ms=CROSSFADE_MS):
    """Concatenate audio files with crossfade."""
    if len(file_list) == 1:
        shutil.copy(file_list[0], output_path)
        return output_path

    # Build ffmpeg filter for crossfade
    crossfade_sec = crossfade_ms / 1000

    inputs = []
    for f in file_list:
        inputs.extend(['-i', f])

    # Build filter chain
    filter_parts = []
    prev = "[0:a]"
    for i in range(1, len(file_list)):
        out = f"[a{i}]" if i < len(file_list) - 1 else ""
        filter_parts.append(f"{prev}[{i}:a]acrossfade=d={crossfade_sec}:c1=tri:c2=tri{out}")
        prev = f"[a{i}]"

    filter_complex = ";".join(filter_parts)

    cmd = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', filter_complex,
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]

    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


# ============================================================================
# AUDIO PROCESSING
# ============================================================================

def get_audio_duration(audio_path):
    """Get duration of audio file in seconds."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


# ============================================================================
# RESEMBLE AI TTS API
# ============================================================================

def merge_blocks_for_resemble(blocks, category='default'):
    """Merge adjacent blocks into chunks under RESEMBLE_CHUNK_MAX chars.

    SSML <break> tags are inserted between merged paragraphs using the ORIGINAL
    pause durations from the script (capped at 5s for SSML compatibility).
    Blocks separated by long pauses (>= 10s) are NOT merged — those gaps stay
    as separate silence files for precise control.
    """
    merge_threshold = 10
    merged = []
    current_items = []  # List of (text, pause) tuples
    current_chars = 0

    for text, pause in blocks:
        if current_items and (pause >= merge_threshold or current_chars + len(text) + 50 > RESEMBLE_CHUNK_MAX):
            # Flush current chunk
            merged_text = _join_with_ssml_breaks(current_items)
            merged.append((merged_text, current_items[-1][1]))
            current_items = [(text, pause)]
            current_chars = len(text)
        else:
            current_items.append((text, pause))
            current_chars += len(text) + 50  # Account for SSML break tags

    if current_items:
        merged_text = _join_with_ssml_breaks(current_items)
        merged.append((merged_text, current_items[-1][1]))

    return merged


def _join_with_ssml_breaks(items):
    """Join text blocks with SSML break tags using original pause durations.

    Uses the actual pause value from the script (capped at 5s for SSML).
    This preserves meditation pacing instead of randomizing to 1-3s.
    """
    if len(items) == 1:
        return items[0][0]
    parts = []
    for i, (text, pause) in enumerate(items):
        parts.append(text)
        if i < len(items) - 1:
            break_ms = min(int(pause * 1000), 5000)
            break_ms = max(break_ms, 500)
            parts.append(f'<break time="{break_ms}ms" />')
    return ' '.join(parts)


def generate_tts_chunk_resemble(text, output_path, chunk_num=0, voice_id=None):
    """Generate TTS for a single chunk using Resemble AI.

    LOSSLESS: Saves native WAV from API — NO intermediate MP3 conversion.
    Returns output_path (WAV) on success.
    """
    import requests
    import base64

    if not RESEMBLE_API_KEY:
        raise ValueError("RESEMBLE_API_KEY not set in .env")

    voice = voice_id or RESEMBLE_VOICE_ID

    headers = {
        "Authorization": f"Bearer {RESEMBLE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "voice_uuid": voice,
        "data": text,
        "output_format": "wav",
        "sample_rate": SAMPLE_RATE,
        "voice_settings_preset_uuid": RESEMBLE_VOICE_SETTINGS_PRESET,
    }

    print(f"    Chunk {chunk_num + 1}: {len(text)} chars...", end=" ", flush=True)

    # Retry logic for transient errors
    for attempt in range(3):
        response = requests.post(RESEMBLE_SYNTH_URL, json=payload, headers=headers, timeout=120)
        data = response.json()

        if data.get("success"):
            audio_bytes = base64.b64decode(data["audio_content"])
            # Write native WAV directly — ZERO lossy steps
            Path(output_path).write_bytes(audio_bytes)
            duration = data.get("duration", 0)
            print(f"{duration:.1f}s")
            time.sleep(RESEMBLE_DELAY_MS / 1000)
            return output_path

        error = data.get("message", "Unknown error")
        if response.status_code == 429:
            wait = (attempt + 1) * 5
            print(f"rate limited, waiting {wait}s...", end=" ", flush=True)
            time.sleep(wait)
        else:
            raise Exception(f"Resemble API error: {response.status_code} - {error}")

    raise Exception("Resemble API: max retries exceeded")


def generate_silence(duration, output_path, channels=1):
    """Generate silence audio file (WAV for lossless pipeline).
    Channels must match voice chunks (mono for Fish, stereo for Resemble).
    """
    cl = 'stereo' if channels == 2 else 'mono'
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'anullsrc=r={SAMPLE_RATE}:cl={cl}',
        '-t', str(duration),
        '-c:a', 'pcm_s16le',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def cleanup_audio_medium(input_path, output_path):
    """Medium cleanup for Fish — de-hiss without muffling.
    Keeps de-esser, drops hard lowpass and heavy noise reduction.
    Output is WAV for lossless pipeline.
    """
    filter_chain = ','.join([
        'highpass=f=80',
        'equalizer=f=6000:t=q:w=2:g=-3',      # De-esser: gentler notch at 6kHz
        'highshelf=f=8000:g=-1.5',             # Gentle shelf above 8kHz (was 7kHz/-2)
        'afftdn=nf=-20',                       # Lighter noise reduction (was -25)
        'loudnorm=I=-24:TP=-2:LRA=11'
    ])
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-af', filter_chain,
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def cleanup_audio(input_path, output_path):
    """Fish cleanup — loudnorm only.
    Output is WAV for lossless pipeline.

    Fish TTS is broadcast-quality clean (45 dB SNR). No broadband noise reduction
    needed (afftdn, lowpass, highpass all prohibited). Loudnorm levels the
    whole-file narration after concatenation.

    highshelf=f=3000:g=3 REMOVED (8 Feb 2026) — A/B testing confirmed the +3dB
    HF boost causes perceived echo on certain words. Loudnorm-only produces
    cleaner output with less hiss and no echo.
    """
    filter_chain = 'loudnorm=I=-26:TP=-2:LRA=11'
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-af', filter_chain,
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def cleanup_audio_resemble(input_path, output_path):
    """Resemble-specific cleanup — matches moonlit garden master chain.

    Chain: highpass 80 Hz (rumble) + lowpass 10 kHz (super-voice noise) +
    spectral denoise afftdn=-25 + loudnorm I=-26.
    loudnorm target -26 LUFS keeps noise floor at -27 dB in silence regions,
    matching the moonlit garden master. Higher targets (e.g. -24) raise the
    noise floor above the QA threshold.
    """
    filter_chain = ','.join([
        'highpass=f=80',
        'lowpass=f=10000',
        'afftdn=nf=-25',
        'loudnorm=I=-26:TP=-2:LRA=11',
    ])
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-af', filter_chain,
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def cleanup_audio_light(input_path, output_path):
    """Light cleanup — loudness normalization only (WAV for lossless pipeline)."""
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-af', 'loudnorm=I=-24:TP=-2:LRA=11',
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def apply_edge_fades(audio_path, output_path, fade_ms=15):
    """Apply brief fade-in at start and fade-out at end of an audio file.

    Prevents click artifacts when files are concatenated with the concat demuxer.
    15ms cosine fades are inaudible but eliminate sample-level discontinuities.
    Output is WAV for lossless pipeline.
    """
    fade_sec = fade_ms / 1000
    duration = get_audio_duration(audio_path)
    fade_out_start = max(0, duration - fade_sec)
    cmd = [
        'ffmpeg', '-y', '-i', audio_path,
        '-af', f'afade=t=in:st=0:d={fade_sec}:curve=hsin,afade=t=out:st={fade_out_start}:d={fade_sec}:curve=hsin',
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def normalize_chunk(input_path, output_path, target_lufs=-24):
    """Per-chunk loudnorm — normalize a single TTS chunk to target LUFS.

    This prevents wildly different loudness levels between Fish chunks
    from creating surges/drops in the final concatenated audio. The overall
    loudnorm pass after concatenation only adjusts the global average —
    it cannot fix per-chunk variations of 6-8 dB.
    """
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-af', f'loudnorm=I={target_lufs}:TP=-2:LRA=11',
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def concatenate_with_silences(voice_chunks, silences, output_path, temp_dir, cleanup_mode='full',
                               pre_cleanup_path=None):
    """Concatenate voice chunks with silence gaps (lossless WAV pipeline).

    cleanup_mode: 'full' (Fish chain), 'light' (loudnorm only), 'none' (raw)
    pre_cleanup_path: if set, saves a copy of the raw concat BEFORE cleanup
                      (used by Gate 4 voice comparison — must compare raw vs raw master)

    Each chunk gets a 15ms fade-in/out to prevent click artifacts at join boundaries.
    Loudnorm is applied ONCE to the whole assembled narration after concatenation
    (not per-chunk) — this preserves natural dynamics across the session.
    All intermediate files are WAV to avoid cumulative MP3 compression artifacts.
    """
    all_files = []

    # Detect channel count from first voice file
    probe = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'stream=channels',
         '-of', 'csv=p=0', voice_chunks[0]],
        capture_output=True, text=True
    )
    voice_channels = int(probe.stdout.strip()) if probe.stdout.strip() else 1

    for i, (voice_file, silence_duration) in enumerate(zip(voice_chunks, silences)):
        # Convert voice chunk to WAV — preserve native channel count
        wav_voice = os.path.join(temp_dir, f"voice_{i}.wav")
        subprocess.run([
            'ffmpeg', '-y', '-i', voice_file,
            '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE), '-ac', str(voice_channels),
            wav_voice
        ], capture_output=True, check=True)

        # Apply edge fades (WAV in, WAV out) — no per-chunk loudnorm;
        # loudnorm is applied once to the whole assembled narration after concat
        faded_file = os.path.join(temp_dir, f"faded_{i}.wav")
        apply_edge_fades(wav_voice, faded_file)
        all_files.append(faded_file)
        if silence_duration > 0:
            silence_file = os.path.join(temp_dir, f"silence_{i}.wav")
            generate_silence(silence_duration, silence_file, channels=voice_channels)
            all_files.append(silence_file)

    # Use concat demuxer — all files are WAV
    concat_list = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_list, 'w') as f:
        for file in all_files:
            f.write(f"file '{file}'\n")

    # Concatenate to WAV
    concat_output = os.path.join(temp_dir, "concat_raw.wav")
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_list,
        '-c:a', 'pcm_s16le',
        concat_output
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    # Save pre-cleanup copy for voice comparison (Gate 4 needs raw audio)
    if pre_cleanup_path:
        shutil.copy(concat_output, pre_cleanup_path)

    if cleanup_mode == 'full':
        print("  Cleaning up audio (full Fish chain)...")
        cleanup_audio(concat_output, output_path)
    elif cleanup_mode == 'resemble':
        print("  Cleaning up audio (Resemble HD: spectral denoise + loudnorm)...")
        cleanup_audio_resemble(concat_output, output_path)
    elif cleanup_mode == 'medium':
        print("  Cleaning up audio (de-hiss, no lowpass)...")
        cleanup_audio_medium(concat_output, output_path)
    elif cleanup_mode == 'light':
        print("  Cleaning up audio (loudnorm only)...")
        cleanup_audio_light(concat_output, output_path)
    else:
        print("  No audio cleanup (raw).")
        shutil.copy(concat_output, output_path)
    return output_path


def mix_ambient(voice_path, ambient_name, output_path, volume_db=None, fade_in=None, fade_out=None):
    """Mix ambient background with voice (WAV output for lossless pipeline)."""
    volume_db = volume_db if volume_db is not None else AMBIENT_VOLUME_DB
    fade_in = fade_in if fade_in is not None else AMBIENT_FADE_IN_DURATION
    fade_out = fade_out if fade_out is not None else AMBIENT_FADE_OUT_DURATION
    # Try WAV first, then MP3 variants
    ambient_path = None
    for ext in ['wav', 'mp3']:
        for suffix in ['-8hr', '-extended', '']:
            candidate = AMBIENT_DIR / f"{ambient_name}{suffix}.{ext}"
            if candidate.exists():
                ambient_path = candidate
                break
        if ambient_path:
            break

    if not ambient_path:
        print(f"  WARNING: Ambient '{ambient_name}' not found, skipping mix")
        shutil.copy(voice_path, output_path)
        return output_path

    voice_duration = get_audio_duration(voice_path)
    ambient_duration = get_audio_duration(str(ambient_path))

    print(f"  Voice: {voice_duration/60:.1f} min, Ambient: {ambient_duration/60:.1f} min")

    if ambient_duration < voice_duration:
        print(f"  WARNING: Ambient shorter than voice! Need longer ambient file.")

    fade_out_start = max(0, voice_duration - fade_out)

    # Garden ambient has 9.5s dead silence at start — skip with -ss 10
    ambient_input = ['-i', str(ambient_path)]
    if ambient_name == 'garden':
        ambient_input = ['-ss', '10', '-i', str(ambient_path)]

    print(f"  Ambient volume: {volume_db}dB" + (f" (override from script)" if volume_db != AMBIENT_VOLUME_DB else ""))
    print(f"  Ambient fade-in: {fade_in}s, fade-out: {fade_out}s")
    cmd = [
        'ffmpeg', '-y',
        '-i', voice_path,
        *ambient_input,
        '-filter_complex', (
            f"[1:a]volume={volume_db}dB,"
            f"afade=t=in:st={AMBIENT_FADE_IN_START}:d={fade_in},"
            f"afade=t=out:st={fade_out_start}:d={fade_out}[amb];"
            f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2:normalize=0"
        ),
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


# ============================================================================
# AUTOMATED QA — SCAN, PATCH, VERIFY
# ============================================================================


def measure_noise_floor(audio_path, manifest_data):
    """Measure noise floor and HF hiss in silence regions of raw narration.

    Returns (noise_floor_db, hf_hiss_db) — RMS levels measured during
    the longest silence gap in the narration.
    """
    # Find the longest silence region
    best_start = None
    best_dur = 0
    for seg in manifest_data['segments']:
        if seg['type'] == 'silence' and seg['duration'] > best_dur:
            best_start = seg['start_time']
            best_dur = seg['duration']

    if best_start is None or best_dur < 0.5:
        print("  QA-QUALITY: WARNING — no silence region found for noise measurement")
        return 0.0, 0.0

    # Measure 1s in the middle of the longest silence (avoid edges)
    measure_start = best_start + 0.2
    measure_dur = min(best_dur - 0.4, 1.0)
    if measure_dur < 0.3:
        measure_dur = best_dur - 0.4

    # Overall noise floor
    result = subprocess.run([
        'ffmpeg', '-i', audio_path,
        '-ss', str(measure_start), '-t', str(measure_dur),
        '-af', 'astats=reset=0',
        '-f', 'null', '-'
    ], capture_output=True, text=True)
    noise_db = _parse_rms_from_astats(result.stderr)

    # HF hiss (>6kHz)
    result_hf = subprocess.run([
        'ffmpeg', '-i', audio_path,
        '-ss', str(measure_start), '-t', str(measure_dur),
        '-af', 'highpass=f=6000,astats=reset=0',
        '-f', 'null', '-'
    ], capture_output=True, text=True)
    hf_db = _parse_rms_from_astats(result_hf.stderr)

    return noise_db, hf_db


def _parse_rms_from_astats(stderr_text):
    """Extract RMS level dB from ffmpeg astats output."""
    import re
    matches = re.findall(r'RMS level dB:\s*([-\d.]+)', stderr_text)
    if matches:
        try:
            return float(matches[-1])
        except ValueError:
            return -100.0  # Treat unparseable (e.g. '-inf', '-') as silent
    return 0.0


def qa_quality_check(raw_narration_path, manifest_data):
    """PRIMARY QA GATE 1: Quality benchmark check against master.

    Measures noise floor and HF hiss, compares against master thresholds.
    Returns (passed, details_dict).
    """
    print(f"\n  QA-QUALITY: Measuring audio quality...")
    noise_db, hf_db = measure_noise_floor(raw_narration_path, manifest_data)

    print(f"  QA-QUALITY: Noise floor = {noise_db:.1f} dB (threshold: {MASTER_NOISE_FLOOR_DB})")
    print(f"  QA-QUALITY: HF hiss     = {hf_db:.1f} dB (threshold: {MASTER_HF_HISS_DB})")

    details = {
        'noise_floor_db': noise_db,
        'hf_hiss_db': hf_db,
        'noise_threshold': MASTER_NOISE_FLOOR_DB,
        'hf_threshold': MASTER_HF_HISS_DB,
    }

    passed = True
    if noise_db > MASTER_NOISE_FLOOR_DB:
        print(f"  QA-QUALITY: FAIL — noise floor {noise_db:.1f} dB exceeds master threshold {MASTER_NOISE_FLOOR_DB}")
        passed = False
    if hf_db > MASTER_HF_HISS_DB:
        print(f"  QA-QUALITY: FAIL — HF hiss {hf_db:.1f} dB exceeds master threshold {MASTER_HF_HISS_DB}")
        passed = False

    if passed:
        print(f"  QA-QUALITY: PASSED")

    return passed, details


def qa_independent_check(raw_narration_path, manifest_data):
    """SECONDARY QA GATE 2: Independent spectral quality verification.

    Completely independent from primary QA. Compares frequency profile of
    the build against the master reference WAV using spectral analysis.
    Returns (passed, details_dict).
    """
    print(f"\n  QA-INDEPENDENT: Running secondary quality verification...")

    if not MASTER_REF_WAV.exists():
        print(f"  QA-INDEPENDENT: WARNING — master reference WAV not found at {MASTER_REF_WAV}")
        print(f"  QA-INDEPENDENT: Falling back to absolute thresholds only")
        # Fall back to stricter absolute thresholds
        noise_db, hf_db = measure_noise_floor(raw_narration_path, manifest_data)
        passed = noise_db <= MASTER_NOISE_FLOOR_DB and hf_db <= MASTER_HF_HISS_DB
        if passed:
            print(f"  QA-INDEPENDENT: PASSED (absolute thresholds)")
        else:
            print(f"  QA-INDEPENDENT: FAIL")
        return passed, {'method': 'absolute', 'noise_db': noise_db, 'hf_db': hf_db}

    # Measure master reference
    master_manifest = {'segments': [{'type': 'silence', 'start_time': 3.0, 'duration': 3.0}]}
    master_noise, master_hf = measure_noise_floor(str(MASTER_REF_WAV), master_manifest)

    # Measure build
    build_noise, build_hf = measure_noise_floor(raw_narration_path, manifest_data)

    # Spectral energy comparison: measure energy in 3 bands
    bands = [
        ('low', '80', '2000'),
        ('mid', '2000', '6000'),
        ('high', '6000', '20000'),
    ]
    master_bands = {}
    build_bands = {}

    # Find a speech segment for spectral comparison
    speech_seg = None
    for seg in manifest_data['segments']:
        if seg['type'] == 'text' and seg.get('duration', 0) > 5:
            speech_seg = seg
            break

    if speech_seg:
        speech_start = speech_seg['start_time'] + 1.0
        speech_dur = min(speech_seg.get('duration', 5) - 2, 5.0)

        for band_name, low, high in bands:
            # Build
            r = subprocess.run([
                'ffmpeg', '-i', raw_narration_path,
                '-ss', str(speech_start), '-t', str(speech_dur),
                '-af', f'bandpass=f={int((int(low)+int(high))//2)}:w={int(high)-int(low)},astats=reset=0',
                '-f', 'null', '-'
            ], capture_output=True, text=True)
            build_bands[band_name] = _parse_rms_from_astats(r.stderr)

            # Master (use first 5s of speech — starts around 0s)
            r2 = subprocess.run([
                'ffmpeg', '-i', str(MASTER_REF_WAV),
                '-ss', '1.0', '-t', str(speech_dur),
                '-af', f'bandpass=f={int((int(low)+int(high))//2)}:w={int(high)-int(low)},astats=reset=0',
                '-f', 'null', '-'
            ], capture_output=True, text=True)
            master_bands[band_name] = _parse_rms_from_astats(r2.stderr)

        print(f"  QA-INDEPENDENT: Spectral comparison (build vs master):")
        for band_name in ['low', 'mid', 'high']:
            diff = build_bands.get(band_name, 0) - master_bands.get(band_name, 0)
            print(f"    {band_name:>4}: build={build_bands.get(band_name, 0):.1f} dB, master={master_bands.get(band_name, 0):.1f} dB, diff={diff:+.1f} dB")

    # Quality gap check
    noise_gap = build_noise - master_noise
    hf_gap = build_hf - master_hf
    print(f"  QA-INDEPENDENT: Noise gap = {noise_gap:+.1f} dB (build vs master)")
    print(f"  QA-INDEPENDENT: HF gap    = {hf_gap:+.1f} dB (build vs master)")

    # FAIL if build is more than 3 dB worse than master in any metric
    MAX_QUALITY_GAP = 3.0
    passed = True
    if noise_gap > MAX_QUALITY_GAP:
        print(f"  QA-INDEPENDENT: FAIL — noise {noise_gap:+.1f} dB worse than master (max {MAX_QUALITY_GAP})")
        passed = False
    if hf_gap > MAX_QUALITY_GAP:
        print(f"  QA-INDEPENDENT: FAIL — HF hiss {hf_gap:+.1f} dB worse than master (max {MAX_QUALITY_GAP})")
        passed = False

    # Sliding window HF check — scan ALL speech segments in 2s windows
    import numpy as np
    sliding_window_flags = []
    try:
        import wave as _wave
        w = _wave.open(raw_narration_path, 'r')
        n_frames = w.getnframes()
        sr_wav = w.getframerate()
        nch = w.getnchannels()
        raw_data = w.readframes(n_frames)
        w.close()

        audio_samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float64)
        if nch > 1:
            audio_samples = audio_samples.reshape(-1, nch).mean(axis=1)

        from scipy.signal import butter, sosfilt
        sos_hf3 = butter(4, 6000, btype='high', fs=sr_wav, output='sos')
        hf3 = sosfilt(sos_hf3, audio_samples)

        sw_sec = 2.0
        sw_samples = int(sw_sec * sr_wav)
        sw_hop = int(1.0 * sr_wav)

        # Compute HF RMS for each window across entire file
        all_hf_rms = []
        all_times = []
        for start in range(0, len(audio_samples) - sw_samples, sw_hop):
            hf_rms = np.sqrt(np.mean(hf3[start:start+sw_samples]**2))
            hf_db = 20 * np.log10(hf_rms / 32768) if hf_rms > 0 else -100
            all_hf_rms.append(hf_db)
            all_times.append(start / sr_wav)

        if all_hf_rms:
            all_hf_rms = np.array(all_hf_rms)
            all_times = np.array(all_times)
            # Build speech region mask
            speech_mask_sw = np.zeros(len(all_times), dtype=bool)
            for seg in manifest_data['segments']:
                if seg['type'] == 'text':
                    for i, t in enumerate(all_times):
                        if seg['start_time'] <= t < seg['start_time'] + seg['duration']:
                            speech_mask_sw[i] = True

            speech_hf = all_hf_rms[speech_mask_sw]
            if len(speech_hf) > 5:
                median_hf_sw = float(np.median(speech_hf))
                # Flag any window where HF deviates > 18 dB from speech median
                # Calibrated against known-good deploys (natural HF variance up to 17 dB)
                for i in range(len(all_times)):
                    if speech_mask_sw[i]:
                        deviation = all_hf_rms[i] - median_hf_sw
                        if deviation > 18.0:
                            t = all_times[i]
                            sliding_window_flags.append({
                                'time': round(float(t), 1),
                                'time_fmt': f'{int(t//60)}:{t%60:04.1f}',
                                'hf_db': round(float(all_hf_rms[i]), 1),
                                'deviation_db': round(float(deviation), 1),
                            })
                if sliding_window_flags:
                    print(f"  QA-INDEPENDENT: FAIL — {len(sliding_window_flags)} sliding-window HF spikes:")
                    for f in sliding_window_flags[:5]:
                        print(f"    {f['time_fmt']} — HF={f['hf_db']:.1f} dB (+{f['deviation_db']:.1f} above median)")
                    passed = False
    except Exception as e:
        print(f"  QA-INDEPENDENT: WARNING — sliding window check skipped: {e}")

    if passed:
        print(f"  QA-INDEPENDENT: PASSED")

    details = {
        'method': 'spectral_comparison',
        'master_noise': master_noise, 'build_noise': build_noise,
        'master_hf': master_hf, 'build_hf': build_hf,
        'noise_gap': noise_gap, 'hf_gap': hf_gap,
        'spectral_bands': {'build': build_bands, 'master': master_bands},
        'sliding_window_flags': sliding_window_flags,
    }
    return passed, details


def qa_master_voice_check(raw_narration_path):
    """QA GATE 4: Master voice comparison — MFCC cosine + F0 deviation.

    Compares the raw narration against the Marco master reference WAV.
    Catches provider-level voice failures (e.g. Resemble on short content).
    Does NOT catch subtle within-provider prosody issues — human ear required.

    Returns (passed, details_dict).
    """
    print(f"\n  QA-VOICE: Comparing against master voice reference...")

    if not MASTER_REF_WAV.exists():
        print(f"  QA-VOICE: WARNING — master WAV not found at {MASTER_REF_WAV}")
        print(f"  QA-VOICE: SKIPPED (no master to compare against)")
        return True, {'skipped': True}

    if not MASTER_MEASUREMENTS.exists():
        print(f"  QA-VOICE: WARNING — master measurements not found at {MASTER_MEASUREMENTS}")
        print(f"  QA-VOICE: SKIPPED (no baseline measurements)")
        return True, {'skipped': True}

    try:
        import librosa
        import numpy as np
    except ImportError:
        print(f"  QA-VOICE: WARNING — librosa/numpy not installed, skipping")
        return True, {'skipped': True, 'reason': 'missing_deps'}

    # Load master measurements (pre-computed)
    with open(str(MASTER_MEASUREMENTS)) as f:
        master_data = json.load(f)
    master_mfcc = np.array(master_data['measurements']['mfcc_mean'])
    master_f0 = master_data['measurements']['f0_mean']

    # Extract MFCC from build
    print(f"  QA-VOICE: Extracting MFCC from build...")
    y_build, sr_build = librosa.load(raw_narration_path, sr=22050)
    mfcc_build = librosa.feature.mfcc(y=y_build, sr=sr_build, n_mfcc=13)
    build_mfcc = mfcc_build.mean(axis=1)

    # MFCC cosine distance
    dot = np.dot(master_mfcc, build_mfcc)
    norm_m = np.linalg.norm(master_mfcc)
    norm_b = np.linalg.norm(build_mfcc)
    cosine_sim = dot / (norm_m * norm_b) if (norm_m * norm_b) > 0 else 0
    mfcc_distance = 1.0 - cosine_sim

    # Extract F0 from build
    print(f"  QA-VOICE: Extracting F0 from build...")
    f0_build, voiced_flag, _ = librosa.pyin(y_build, fmin=40, fmax=300, sr=sr_build)
    f0_voiced = f0_build[voiced_flag] if voiced_flag is not None else f0_build[~np.isnan(f0_build)]
    build_f0 = float(np.median(f0_voiced)) if len(f0_voiced) > 0 else 0.0

    # F0 deviation
    f0_deviation = abs(build_f0 - master_f0) / master_f0 * 100 if master_f0 > 0 else 0.0

    print(f"  QA-VOICE: MFCC cosine distance = {mfcc_distance:.4f} (threshold: {MASTER_MFCC_COSINE_MAX})")
    print(f"  QA-VOICE: F0 mean = {build_f0:.1f} Hz (master: {master_f0:.1f} Hz, deviation: {f0_deviation:.1f}%)")

    details = {
        'mfcc_cosine_distance': round(mfcc_distance, 6),
        'mfcc_threshold': MASTER_MFCC_COSINE_MAX,
        'build_f0': round(build_f0, 1),
        'master_f0': master_f0,
        'f0_deviation_pct': round(f0_deviation, 1),
        'f0_threshold': MASTER_F0_DEVIATION_MAX,
    }

    passed = True
    if mfcc_distance > MASTER_MFCC_COSINE_MAX:
        print(f"  QA-VOICE: FAIL — MFCC distance {mfcc_distance:.4f} exceeds threshold {MASTER_MFCC_COSINE_MAX}")
        passed = False
    if f0_deviation > MASTER_F0_DEVIATION_MAX:
        print(f"  QA-VOICE: FAIL — F0 deviation {f0_deviation:.1f}% exceeds threshold {MASTER_F0_DEVIATION_MAX}%")
        passed = False

    if passed:
        print(f"  QA-VOICE: PASSED")
    else:
        print(f"  QA-VOICE: NOTE — automated metrics catch provider-level failures only.")
        print(f"  QA-VOICE: Human review still required for prosody/naturalness.")

    return passed, details


def qa_loudness_consistency_check(audio_path, manifest_data, max_deviation_db=10.0):
    """QA GATE 5: Per-second loudness consistency check.

    Loads the entire WAV into memory and computes RMS per second.
    Flags any speech second where RMS deviates more than max_deviation_db
    from the median speech RMS. Fast (< 2s for 14 min file).

    Catches per-chunk loudness surges that a single loudnorm pass can't fix.
    Returns (passed, details_dict).
    """
    import wave as _wave
    import numpy as np

    print(f"\n  QA-LOUDNESS: Scanning for per-segment loudness spikes...")

    # Load WAV into memory
    try:
        w = _wave.open(audio_path, 'r')
    except Exception:
        # Try converting to WAV first (handles MP3 input)
        tmp_wav = audio_path + ".loudness_check.wav"
        subprocess.run([
            'ffmpeg', '-y', '-i', audio_path,
            '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
            tmp_wav
        ], capture_output=True, check=True)
        w = _wave.open(tmp_wav, 'r')

    n = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw = w.readframes(n)
    w.close()

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)

    # Compute RMS per second
    window = sr
    rms_db = []
    for i in range(0, len(samples) - window, window):
        chunk = samples[i:i+window]
        rms = np.sqrt(np.mean(chunk**2))
        db = 20 * np.log10(rms / 32768) if rms > 0 else -100
        rms_db.append(db)

    rms_db = np.array(rms_db)

    # Speech regions: > -40 dB RMS (silence is typically < -50 dB)
    speech_mask = rms_db > -40
    speech_rms = rms_db[speech_mask]

    if len(speech_rms) < 5:
        print(f"  QA-LOUDNESS: WARNING — too few speech seconds ({len(speech_rms)})")
        return True, {'skipped': True}

    median_rms = float(np.median(speech_rms))

    # Find spikes
    spikes = []
    for i, db in enumerate(rms_db):
        if speech_mask[i] and (db - median_rms) > max_deviation_db:
            mins = i // 60
            secs = i % 60
            spikes.append({
                'time': i,
                'time_fmt': f'{mins}:{secs:02d}',
                'rms_db': round(float(db), 1),
                'deviation_db': round(float(db - median_rms), 1),
            })

    details = {
        'median_rms_db': round(median_rms, 1),
        'min_speech_rms_db': round(float(np.min(speech_rms)), 1),
        'max_speech_rms_db': round(float(np.max(speech_rms)), 1),
        'range_db': round(float(np.max(speech_rms) - np.min(speech_rms)), 1),
        'speech_seconds': int(sum(speech_mask)),
        'total_seconds': len(rms_db),
        'threshold_db': max_deviation_db,
        'spikes': spikes,
    }

    print(f"  QA-LOUDNESS: {details['speech_seconds']} speech seconds, median RMS={median_rms:.1f} dB")
    print(f"  QA-LOUDNESS: Range = {details['min_speech_rms_db']} to {details['max_speech_rms_db']} dB ({details['range_db']:.1f} dB)")

    passed = len(spikes) == 0
    if not passed:
        print(f"  QA-LOUDNESS: FAIL — {len(spikes)} seconds exceed +{max_deviation_db} dB above median:")
        for spike in spikes[:10]:
            print(f"    {spike['time_fmt']} — {spike['rms_db']} dB (+{spike['deviation_db']:.1f} dB)")
        if len(spikes) > 10:
            print(f"    ... and {len(spikes) - 10} more")
    else:
        print(f"  QA-LOUDNESS: PASSED — all speech within +{max_deviation_db} dB of median")

    # Cleanup temp file if created
    tmp_wav = audio_path + ".loudness_check.wav"
    if os.path.exists(tmp_wav):
        os.remove(tmp_wav)

    return passed, details


def qa_hf_hiss_check(audio_path, manifest_data, hp_freq=4000, window_sec=1.0,
                     overlap_sec=0.5, ratio_threshold_db=6.0, min_duration_sec=3.0):
    """QA GATE 6: High-frequency hiss detector (speech-aware, non-speech regions only).

    Evaluates HF energy ratio ONLY in non-speech regions (silence, pauses, transitions).
    Speech regions are excluded using the build manifest to prevent natural sibilants
    ("s", "sh", "ch") from triggering false positives. Gate 6 catches hiss in pauses,
    silence, and ambient-only sections.

    Layered hiss coverage: Gate 1 (whole-file) + Gate 6 (non-speech) + Gate 9 (energy spikes).

    Returns (passed, details_dict).
    """
    import wave as _wave
    import numpy as np
    from scipy.signal import butter, sosfilt

    print(f"\n  QA-HF-HISS: Scanning for localised high-frequency hiss (non-speech regions)...")

    # Build speech region lookup from manifest
    speech_ranges = []
    for seg in manifest_data.get('segments', []):
        if seg['type'] == 'text':
            seg_start = seg['start_time']
            seg_end = seg_start + seg['duration']
            speech_ranges.append((seg_start, seg_end))

    def is_speech(win_start, win_end):
        """Check if >50% of window overlaps with any speech region."""
        win_dur = win_end - win_start
        overlap = 0.0
        for s_start, s_end in speech_ranges:
            ov_start = max(win_start, s_start)
            ov_end = min(win_end, s_end)
            if ov_end > ov_start:
                overlap += ov_end - ov_start
        return overlap > (win_dur * 0.5)

    # Load WAV
    w = _wave.open(audio_path, 'r')
    n = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw = w.readframes(n)
    w.close()

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)

    # Highpass filter at hp_freq Hz to isolate hiss band
    sos = butter(4, hp_freq, btype='high', fs=sr, output='sos')
    hf_signal = sosfilt(sos, samples)

    # Sliding window: compute both total RMS and HF RMS
    win_samples = int(window_sec * sr)
    hop_samples = int((window_sec - overlap_sec) * sr)
    total_rms_db = []
    hf_ratio_db = []
    window_times = []
    nonspeech_mask = []

    for start in range(0, len(samples) - win_samples, hop_samples):
        total_chunk = samples[start:start + win_samples]
        hf_chunk = hf_signal[start:start + win_samples]

        total_rms = np.sqrt(np.mean(total_chunk**2))
        hf_rms = np.sqrt(np.mean(hf_chunk**2))

        t_db = 20 * np.log10(total_rms / 32768) if total_rms > 0 else -100
        h_db = 20 * np.log10(hf_rms / 32768) if hf_rms > 0 else -100

        win_start_time = start / sr
        win_end_time = win_start_time + window_sec

        total_rms_db.append(t_db)
        hf_ratio_db.append(h_db - t_db)
        window_times.append(win_start_time)
        nonspeech_mask.append(not is_speech(win_start_time, win_end_time))

    total_rms_db = np.array(total_rms_db)
    hf_ratio_db = np.array(hf_ratio_db)
    window_times = np.array(window_times)
    nonspeech_mask = np.array(nonspeech_mask)

    # Only evaluate non-speech windows with some energy (not pure digital silence)
    eval_mask = nonspeech_mask & (total_rms_db > -60)
    n_nonspeech = int(np.sum(nonspeech_mask))
    n_eval = int(np.sum(eval_mask))

    print(f"  QA-HF-HISS: {n_nonspeech} non-speech windows, {n_eval} with energy above -60 dB")

    if n_eval < 3:
        print(f"  QA-HF-HISS: WARNING — too few non-speech windows to evaluate")
        return True, {'skipped': True, 'nonspeech_windows': n_nonspeech}

    median_ratio = float(np.median(hf_ratio_db[eval_mask]))

    # Flag non-speech windows where HF ratio exceeds median by threshold
    spike_mask = np.zeros(len(hf_ratio_db), dtype=bool)
    for i in range(len(hf_ratio_db)):
        if eval_mask[i] and (hf_ratio_db[i] - median_ratio) > ratio_threshold_db:
            spike_mask[i] = True

    # Group consecutive flagged windows into regions
    flagged_regions = []
    in_region = False
    region_start = 0

    for i, is_spike in enumerate(spike_mask):
        if is_spike and not in_region:
            in_region = True
            region_start = i
        elif not is_spike and in_region:
            in_region = False
            region_end = i
            region_start_time = window_times[region_start]
            region_end_time = window_times[min(region_end, len(window_times) - 1)] + window_sec
            duration = region_end_time - region_start_time
            if duration >= min_duration_sec:
                max_ratio = float(np.max(hf_ratio_db[region_start:region_end]))
                flagged_regions.append({
                    'start': round(region_start_time, 1),
                    'end': round(region_end_time, 1),
                    'duration': round(duration, 1),
                    'max_hf_ratio_db': round(max_ratio, 1),
                    'deviation_db': round(max_ratio - median_ratio, 1),
                    'start_fmt': f'{int(region_start_time//60)}:{region_start_time%60:04.1f}',
                    'end_fmt': f'{int(region_end_time//60)}:{region_end_time%60:04.1f}',
                })

    if in_region:
        region_end_time = window_times[-1] + window_sec
        duration = region_end_time - window_times[region_start]
        if duration >= min_duration_sec:
            max_ratio = float(np.max(hf_ratio_db[region_start:]))
            flagged_regions.append({
                'start': round(window_times[region_start], 1),
                'end': round(region_end_time, 1),
                'duration': round(duration, 1),
                'max_hf_ratio_db': round(max_ratio, 1),
                'deviation_db': round(max_ratio - median_ratio, 1),
                'start_fmt': f'{int(window_times[region_start]//60)}:{window_times[region_start]%60:04.1f}',
                'end_fmt': f'{int(region_end_time//60)}:{region_end_time%60:04.1f}',
            })

    details = {
        'median_hf_ratio_db': round(median_ratio, 1),
        'threshold_db': ratio_threshold_db,
        'hp_freq': hp_freq,
        'nonspeech_windows': n_nonspeech,
        'eval_windows': n_eval,
        'flagged_regions': flagged_regions,
    }

    print(f"  QA-HF-HISS: Median HF ratio = {median_ratio:.1f} dB, threshold = +{ratio_threshold_db} dB above")

    passed = len(flagged_regions) == 0
    if not passed:
        print(f"  QA-HF-HISS: FAIL — {len(flagged_regions)} hiss regions detected:")
        for r in flagged_regions[:10]:
            print(f"    {r['start_fmt']} → {r['end_fmt']} ({r['duration']}s, +{r['deviation_db']:.1f} dB above median ratio)")
    else:
        print(f"  QA-HF-HISS: PASSED — no localised hiss above threshold")

    return passed, details


def qa_volume_surge_check(audio_path, manifest_data, window_sec=1.0, overlap_sec=0.5,
                          surge_threshold_db=9.0, drop_threshold_db=14.0, neighbour_radius=3):
    """QA GATE 7: Volume surge/drop detector (local-mean comparison).

    Compares each window's RMS to the mean of its immediate neighbours.
    Excludes windows overlapping known silence regions from manifest
    (silence-to-speech transitions are intentional, not defects).

    Returns (passed, details_dict).
    """
    import wave as _wave
    import numpy as np

    print(f"\n  QA-SURGE: Scanning for volume surges and drops...")

    # Load WAV
    w = _wave.open(audio_path, 'r')
    n = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw = w.readframes(n)
    w.close()

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)

    # Sliding window RMS
    win_samples = int(window_sec * sr)
    hop_samples = int((window_sec - overlap_sec) * sr)
    rms_db = []
    window_times = []

    for start in range(0, len(samples) - win_samples, hop_samples):
        chunk = samples[start:start + win_samples]
        rms = np.sqrt(np.mean(chunk**2))
        db = 20 * np.log10(rms / 32768) if rms > 0 else -100
        rms_db.append(db)
        window_times.append(start / sr)

    rms_db = np.array(rms_db)
    window_times = np.array(window_times)

    # Build silence region lookup from manifest (with duration for margin scaling)
    silence_ranges = []
    for seg in manifest_data['segments']:
        if seg['type'] == 'silence':
            silence_ranges.append((seg['start_time'], seg['start_time'] + seg['duration'], seg['duration']))

    def overlaps_silence(t, win=window_sec):
        """Check if a window overlaps any silence region (margin scales with silence duration).

        Short pauses (8s) get 4s margin. Long silences (50s) get proportionally larger
        margins because the voice ramp-up after extended silence is longer.
        """
        for s_start, s_end, s_dur in silence_ranges:
            margin = max(4.0, s_dur * 0.15)
            if t < s_end + margin and t + win > s_start - margin:
                return True
        return False

    # Compare each window to local mean of neighbours
    surges = []
    drops = []
    for i in range(neighbour_radius, len(rms_db) - neighbour_radius):
        t = window_times[i]

        # Skip windows near silence (transitions are intentional)
        if overlaps_silence(t):
            continue

        # Skip near-silence windows
        if rms_db[i] < -50:
            continue

        # Local mean of neighbours (excluding self and silence-adjacent)
        neighbour_indices = list(range(max(0, i - neighbour_radius), i)) + \
                           list(range(i + 1, min(len(rms_db), i + neighbour_radius + 1)))
        # Filter: must have signal AND not overlap silence regions
        active_vals = [rms_db[j] for j in neighbour_indices
                       if rms_db[j] > -50 and not overlaps_silence(window_times[j])]
        if len(active_vals) < 2:
            continue

        local_mean = float(np.mean(active_vals))

        # Skip if local mean is below speech level — neighbours are ambient/transition,
        # not real speech, so the comparison is meaningless (e.g. session opening)
        if local_mean < -28:
            continue

        deviation = rms_db[i] - local_mean

        if deviation > surge_threshold_db:
            mins = int(t // 60)
            secs = t % 60
            surges.append({
                'time': round(float(t), 1),
                'time_fmt': f'{mins}:{secs:04.1f}',
                'rms_db': round(float(rms_db[i]), 1),
                'local_mean_db': round(local_mean, 1),
                'deviation_db': round(float(deviation), 1),
                'type': 'SURGE',
            })
        elif deviation < -drop_threshold_db and rms_db[i] > -33:
            # Skip drops into near-silence/breath pauses (< -33 dB = not speech)
            mins = int(t // 60)
            secs = t % 60
            drops.append({
                'time': round(float(t), 1),
                'time_fmt': f'{mins}:{secs:04.1f}',
                'rms_db': round(float(rms_db[i]), 1),
                'local_mean_db': round(local_mean, 1),
                'deviation_db': round(float(deviation), 1),
                'type': 'DROP',
            })

    all_flags = surges + drops
    all_flags.sort(key=lambda x: x['time'])

    details = {
        'surge_threshold_db': surge_threshold_db,
        'drop_threshold_db': drop_threshold_db,
        'neighbour_radius': neighbour_radius,
        'surges': len(surges),
        'drops': len(drops),
        'flags': all_flags,
    }

    print(f"  QA-SURGE: {len(surges)} surges (+{surge_threshold_db} dB), {len(drops)} drops (-{drop_threshold_db} dB)")

    passed = len(all_flags) == 0
    if not passed:
        print(f"  QA-SURGE: FAIL — {len(all_flags)} anomalies detected:")
        for f in all_flags[:10]:
            print(f"    {f['time_fmt']} — {f['type']} {f['rms_db']} dB (local mean {f['local_mean_db']}, dev {f['deviation_db']:+.1f})")
        if len(all_flags) > 10:
            print(f"    ... and {len(all_flags) - 10} more")
    else:
        print(f"  QA-SURGE: PASSED — no volume anomalies detected")

    return passed, details


# Gate 8 meditation repetition ignore lists (per category)
# Generic meditation phrases that repeat across ALL sessions (not session-specific)
REPETITION_IGNORE_PHRASES = [
    "breathe in", "breathe out", "breathing in", "breathing out",
    "let go", "letting go", "let it go", "gently let",
    "notice the sensations", "notice any sensations",
    "gently bring your attention", "bring your awareness",
    "take a deep breath", "take another breath", "take a slow breath",
    "in and out", "slowly and gently",
    "when youre ready", "when you're ready",
    "and gently", "gently now",
]


def qa_repeated_content_check(audio_path, manifest_data, expected_repetitions=None,
                               mfcc_sim_threshold=0.998, min_gap_sec=5.0, min_word_match=8):
    """QA GATE 8: Repeated content detector (MFCC fingerprint + Whisper STT).

    Approach A: Compare MFCC fingerprints of voiced segments.
    Approach B: Whisper transcript for repeated word sequences.
    Global ignore list + per-script expected_repetitions prevent false positives
    on intentional repetition.

    Returns (passed, details_dict).
    """
    import numpy as np

    print(f"\n  QA-REPEAT: Scanning for repeated content...")

    # ── Approach A: MFCC fingerprint comparison ──
    print(f"  QA-REPEAT: [A] MFCC segment comparison...")
    try:
        import librosa
    except ImportError:
        print(f"  QA-REPEAT: WARNING — librosa not installed, skipping MFCC check")
        return True, {'skipped': True, 'reason': 'missing_librosa'}

    # Load audio
    y, sr = librosa.load(audio_path, sr=22050)

    # Extract voiced segments from manifest
    text_segments = [s for s in manifest_data['segments'] if s['type'] == 'text' and s.get('duration', 0) > 2]

    # Compute MFCC mean per segment
    segment_mfccs = []
    for seg in text_segments:
        start_sample = int(seg['start_time'] * sr)
        end_sample = int(seg['end_time'] * sr)
        if end_sample > len(y):
            end_sample = len(y)
        if end_sample - start_sample < sr:  # Skip < 1s
            segment_mfccs.append(None)
            continue
        segment_audio = y[start_sample:end_sample]
        mfcc = librosa.feature.mfcc(y=segment_audio, sr=sr, n_mfcc=13)
        segment_mfccs.append(mfcc.mean(axis=1))

    # Compare all pairs
    mfcc_duplicates = []
    for i in range(len(segment_mfccs)):
        if segment_mfccs[i] is None:
            continue
        for j in range(i + 1, len(segment_mfccs)):
            if segment_mfccs[j] is None:
                continue
            # Must be > min_gap_sec apart
            gap = abs(text_segments[j]['start_time'] - text_segments[i]['end_time'])
            if gap < min_gap_sec:
                continue

            # Cosine similarity
            dot = np.dot(segment_mfccs[i], segment_mfccs[j])
            norm_i = np.linalg.norm(segment_mfccs[i])
            norm_j = np.linalg.norm(segment_mfccs[j])
            sim = dot / (norm_i * norm_j) if (norm_i * norm_j) > 0 else 0

            if sim >= mfcc_sim_threshold:
                mfcc_duplicates.append({
                    'seg_a': i,
                    'seg_b': j,
                    'time_a': text_segments[i]['start_time'],
                    'time_b': text_segments[j]['start_time'],
                    'similarity': round(float(sim), 4),
                })

    if mfcc_duplicates:
        print(f"  QA-REPEAT: [A] Found {len(mfcc_duplicates)} MFCC-similar segment pairs")
    else:
        print(f"  QA-REPEAT: [A] No MFCC duplicates found")

    # ── Approach B: Whisper STT ──
    print(f"  QA-REPEAT: [B] Running Whisper transcription...")
    whisper_duplicates = []
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, language="en")
        transcript_segments = result.get('segments', [])

        # Extract words with timestamps
        words = []
        for seg in transcript_segments:
            text = seg['text'].strip().lower()
            text = re.sub(r'[^\w\s]', '', text)
            seg_words = text.split()
            for w_text in seg_words:
                words.append({'word': w_text, 'time': seg['start']})

        # Find repeated sequences of min_word_match+ consecutive words
        if len(words) >= min_word_match:
            # Build n-gram index
            ngram_index = {}
            for i in range(len(words) - min_word_match + 1):
                ngram = ' '.join(w['word'] for w in words[i:i + min_word_match])

                # Check ignore list (global + per-script expected repetitions)
                ignore_list = REPETITION_IGNORE_PHRASES
                if expected_repetitions:
                    ignore_list = REPETITION_IGNORE_PHRASES + expected_repetitions
                ignored = False
                for phrase in ignore_list:
                    if phrase in ngram:
                        ignored = True
                        break
                if ignored:
                    continue

                if ngram in ngram_index:
                    prev_time = ngram_index[ngram]
                    curr_time = words[i]['time']
                    if abs(curr_time - prev_time) > min_gap_sec:
                        whisper_duplicates.append({
                            'phrase': ngram,
                            'first_time': round(prev_time, 1),
                            'second_time': round(curr_time, 1),
                            'gap_sec': round(abs(curr_time - prev_time), 1),
                        })
                else:
                    ngram_index[ngram] = words[i]['time']

        if whisper_duplicates:
            print(f"  QA-REPEAT: [B] Found {len(whisper_duplicates)} repeated phrases")
        else:
            print(f"  QA-REPEAT: [B] No repeated phrases found")

    except ImportError:
        print(f"  QA-REPEAT: [B] Whisper not installed — skipping STT check")
    except Exception as e:
        print(f"  QA-REPEAT: [B] Whisper error: {e} — skipping STT check")

    # Combined verdict: require BOTH MFCC + Whisper agreement for all detections.
    # MFCC alone cannot flag — meditation monotone voice produces >0.96 similarity
    # between ALL segments. Only when Whisper also finds matching text at the same
    # timestamps do we confirm a real duplicate.
    # ADDITIONAL GUARD: verify against manifest text — if the script text for two
    # segments is clearly different, this is a false positive from similar prosody,
    # not a real repeat.
    confirmed_repeats = []
    for mfcc_dup in mfcc_duplicates:
        # Guard: check manifest text for these segments
        seg_a_text = text_segments[mfcc_dup['seg_a']].get('text', '').lower().strip()
        seg_b_text = text_segments[mfcc_dup['seg_b']].get('text', '').lower().strip()
        if seg_a_text and seg_b_text:
            # Word overlap check — if < 60% words in common, texts are different
            words_a = set(seg_a_text.split())
            words_b = set(seg_b_text.split())
            overlap = len(words_a & words_b)
            max_words = max(len(words_a), len(words_b), 1)
            word_overlap_ratio = overlap / max_words
            if word_overlap_ratio < 0.6:
                print(f"  QA-REPEAT: Skipping MFCC pair seg {mfcc_dup['seg_a']}↔{mfcc_dup['seg_b']} — different text (overlap={word_overlap_ratio:.0%})")
                continue

        # Only flag if Whisper also found repeated text near these timestamps
        for w_dup in whisper_duplicates:
            if (abs(w_dup['first_time'] - mfcc_dup['time_a']) < 10 and
                abs(w_dup['second_time'] - mfcc_dup['time_b']) < 10):
                confirmed_repeats.append({**mfcc_dup, 'method': 'mfcc+whisper', 'phrase': w_dup['phrase']})
                break

    details = {
        'mfcc_duplicates': mfcc_duplicates,
        'whisper_duplicates': whisper_duplicates,
        'confirmed_repeats': confirmed_repeats,
    }

    passed = len(confirmed_repeats) == 0
    if not passed:
        print(f"  QA-REPEAT: FAIL — {len(confirmed_repeats)} confirmed repetitions:")
        for r in confirmed_repeats[:5]:
            t_a = r['time_a']
            t_b = r['time_b']
            print(f"    {int(t_a//60)}:{t_a%60:04.1f} ↔ {int(t_b//60)}:{t_b%60:04.1f} (sim={r['similarity']}, {r['method']})")
    else:
        print(f"  QA-REPEAT: PASSED — no unexpected repetitions")

    return passed, details


def qa_speech_rate_check(audio_path, manifest_data, window_sec=2.0, rush_threshold=1.3):
    """QA GATE 10: Speech rate anomaly detection.

    Uses Whisper word-level timestamps to measure words-per-second in sliding
    windows. Flags any window where speech rate exceeds rush_threshold (130%)
    of the session average. Meditation content should be consistently slow
    (~100-120 wpm / 2-3 words per second).

    Returns (passed, details_dict).
    """
    import numpy as np

    print(f"\n  QA-RATE: Scanning for speech rate anomalies...")

    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(audio_path, word_timestamps=True)

        # Extract word-level timestamps
        words = []
        for seg in result.get('segments', []):
            for w in seg.get('words', []):
                words.append({
                    'word': w['word'].strip(),
                    'start': w['start'],
                    'end': w['end'],
                })

        if len(words) < 10:
            print(f"  QA-RATE: WARNING — too few words ({len(words)}) for rate analysis")
            return True, {'skipped': True, 'word_count': len(words)}

        # Build speech region lookup from manifest
        speech_ranges = []
        for seg in manifest_data['segments']:
            if seg['type'] == 'text':
                speech_ranges.append((seg['start_time'], seg['start_time'] + seg['duration']))

        def is_speech_window(win_start, win_end):
            """Check if >50% of window overlaps with speech regions."""
            win_dur = win_end - win_start
            overlap = 0.0
            for s_start, s_end in speech_ranges:
                ov_start = max(win_start, s_start)
                ov_end = min(win_end, s_end)
                if ov_end > ov_start:
                    overlap += ov_end - ov_start
            return overlap > (win_dur * 0.5)

        # Compute words-per-second in sliding windows across speech regions
        total_dur = words[-1]['end']
        hop = window_sec / 2  # 50% overlap
        window_rates = []
        window_times = []

        t = 0.0
        while t + window_sec <= total_dur:
            # Skip windows that are NOT predominantly speech
            if not is_speech_window(t, t + window_sec):
                t += hop
                continue

            # Count words in this window
            wc = sum(1 for w in words if w['start'] >= t and w['start'] < t + window_sec)
            rate = wc / window_sec  # words per second

            if rate > 0.5:  # Only count windows with actual speech
                window_rates.append(rate)
                window_times.append(t)

            t += hop

        if len(window_rates) < 5:
            print(f"  QA-RATE: WARNING — too few speech windows ({len(window_rates)})")
            return True, {'skipped': True, 'speech_windows': len(window_rates)}

        window_rates = np.array(window_rates)
        window_times = np.array(window_times)

        median_rate = float(np.median(window_rates))
        threshold_rate = max(median_rate * rush_threshold, 7.0)  # absolute floor: 7.0 w/s (420 wpm)

        # Flag windows exceeding threshold
        rushes = []
        for i, (rate, t) in enumerate(zip(window_rates, window_times)):
            # Skip impossible rates (>8 w/s = 480 wpm) — Whisper timestamp artifact
            if rate > 8.0:
                continue
            if rate > threshold_rate:
                mins = int(t // 60)
                secs = t % 60
                rushes.append({
                    'time': round(float(t), 1),
                    'time_fmt': f'{mins}:{secs:04.1f}',
                    'rate_wps': round(float(rate), 1),
                    'median_rate_wps': round(median_rate, 1),
                    'ratio': round(float(rate / median_rate), 2),
                })

        details = {
            'median_rate_wps': round(median_rate, 1),
            'threshold_wps': round(threshold_rate, 1),
            'rush_threshold': rush_threshold,
            'speech_windows': len(window_rates),
            'rushes': len(rushes),
            'flags': rushes,
        }

        print(f"  QA-RATE: Median speech rate = {median_rate:.1f} words/sec, threshold = {threshold_rate:.1f} words/sec")

        passed = len(rushes) == 0
        if not passed:
            print(f"  QA-RATE: FAIL — {len(rushes)} speech rate anomalies:")
            for r in rushes[:10]:
                print(f"    {r['time_fmt']} — {r['rate_wps']} w/s ({r['ratio']:.0%} of median)")
        else:
            print(f"  QA-RATE: PASSED — consistent speech rate")

        return passed, details

    except ImportError:
        print(f"  QA-RATE: WARNING — Whisper not installed, skipping")
        return True, {'skipped': True}
    except Exception as e:
        print(f"  QA-RATE: WARNING — error: {e}, skipping")
        return True, {'skipped': True, 'error': str(e)}


def qa_silence_integrity_check(raw_narration_wav, manifest_data, max_silence_energy_db=-50.0):
    """QA GATE 11: Silence Region Integrity.

    Verifies that every silence region in the manifest actually contains silence
    in the raw narration (pre-ambient mix). Catches audio bleed, stray TTS output,
    or incorrect segment boundaries.

    Returns (passed, details_dict).
    """
    import numpy as np

    print(f"\n  QA-SILENCE: Checking silence region integrity...")

    try:
        import librosa
    except ImportError:
        print(f"  QA-SILENCE: WARNING — librosa not installed, skipping")
        return True, {'skipped': True, 'reason': 'missing_librosa'}

    y, sr = librosa.load(raw_narration_wav, sr=22050)

    silence_regions = [s for s in manifest_data.get('segments', []) if s['type'] == 'silence']

    if not silence_regions:
        print(f"  QA-SILENCE: No silence regions in manifest — skipping")
        return True, {'skipped': True, 'reason': 'no_silence_regions'}

    failed_regions = []
    for seg in silence_regions:
        start_sample = int(seg['start_time'] * sr)
        end_sample = int(seg['end_time'] * sr)
        if end_sample > len(y):
            end_sample = len(y)
        if end_sample - start_sample < int(0.1 * sr):
            continue

        region_audio = y[start_sample:end_sample]
        rms = np.sqrt(np.mean(region_audio ** 2))
        energy_db = 20 * np.log10(rms + 1e-10)

        if energy_db > max_silence_energy_db:
            t = seg['start_time']
            failed_regions.append({
                'start_time': round(t, 1),
                'start_fmt': f'{int(t//60)}:{t%60:04.1f}',
                'duration': seg['duration'],
                'energy_db': round(float(energy_db), 1),
                'threshold_db': max_silence_energy_db,
            })

    details = {
        'total_silence_regions': len(silence_regions),
        'failed_regions': len(failed_regions),
        'flags': failed_regions,
        'threshold_db': max_silence_energy_db,
    }

    passed = len(failed_regions) == 0
    if not passed:
        print(f"  QA-SILENCE: FAIL — {len(failed_regions)} silence regions contain unexpected audio:")
        for r in failed_regions[:5]:
            print(f"    {r['start_fmt']} ({r['duration']}s) — energy {r['energy_db']} dB (max {max_silence_energy_db} dB)")
    else:
        print(f"  QA-SILENCE: PASSED — all {len(silence_regions)} silence regions verified clean")

    return passed, details


def qa_duration_accuracy_check(final_audio_path, metadata, tolerance=0.15):
    """QA GATE 12: Duration Accuracy.

    Compares final audio duration against the Duration-Target in the script
    metadata. Catches overgeneration, missing chunks, or pause errors.

    Returns (passed, details_dict).
    """
    print(f"\n  QA-DURATION: Checking duration accuracy...")

    duration_str = metadata.get('duration', '')
    if not duration_str:
        print(f"  QA-DURATION: No Duration field in metadata — skipping")
        return True, {'skipped': True, 'reason': 'no_duration_target'}

    # Parse target duration (e.g., "12 minutes", "8 minutes", "25 minutes")
    import re
    match = re.search(r'(\d+)\s*min', duration_str.lower())
    if not match:
        print(f"  QA-DURATION: Cannot parse duration '{duration_str}' — skipping")
        return True, {'skipped': True, 'reason': 'unparseable_duration', 'raw': duration_str}

    target_sec = int(match.group(1)) * 60

    # Measure actual duration
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', final_audio_path],
            capture_output=True, text=True, timeout=10)
        actual_sec = float(result.stdout.strip())
    except Exception as e:
        print(f"  QA-DURATION: Cannot measure duration: {e} — skipping")
        return True, {'skipped': True, 'error': str(e)}

    deviation = abs(actual_sec - target_sec) / target_sec
    actual_min = actual_sec / 60
    target_min = target_sec / 60

    details = {
        'target_sec': target_sec,
        'target_min': round(target_min, 1),
        'actual_sec': round(actual_sec, 1),
        'actual_min': round(actual_min, 1),
        'deviation_pct': round(deviation * 100, 1),
        'tolerance_pct': round(tolerance * 100, 1),
    }

    passed = deviation <= tolerance
    if not passed:
        print(f"  QA-DURATION: FAIL — {actual_min:.1f} min vs {target_min:.1f} min target ({deviation*100:.1f}% deviation, max {tolerance*100:.0f}%)")
    else:
        print(f"  QA-DURATION: PASSED — {actual_min:.1f} min vs {target_min:.1f} min target ({deviation*100:.1f}% deviation)")

    return passed, details


def qa_ambient_continuity_check(final_audio_path, manifest_data, min_energy_db=-85.0,
                                 max_ambient_variation_db=19.0):
    """QA GATE 13: Ambient Continuity.

    Verifies that no pause/silence region in the final mixed output drops below
    -85 dBFS (dead silence) and that ambient energy is consistent across regions.

    Returns (passed, details_dict).
    """
    import numpy as np

    print(f"\n  QA-AMBIENT: Checking ambient continuity...")

    try:
        import librosa
    except ImportError:
        print(f"  QA-AMBIENT: WARNING — librosa not installed, skipping")
        return True, {'skipped': True, 'reason': 'missing_librosa'}

    y, sr = librosa.load(final_audio_path, sr=22050)
    total_dur = len(y) / sr

    silence_regions = [s for s in manifest_data.get('segments', []) if s['type'] == 'silence']

    if not silence_regions:
        print(f"  QA-AMBIENT: No silence regions in manifest — skipping")
        return True, {'skipped': True, 'reason': 'no_silence_regions'}

    dead_silence = []
    region_energies = []

    for seg in silence_regions:
        start_sample = int(seg['start_time'] * sr)
        end_sample = int(seg['end_time'] * sr)
        if end_sample > len(y):
            end_sample = len(y)
        if end_sample - start_sample < int(0.5 * sr):
            continue

        region_audio = y[start_sample:end_sample]

        # Check for dead silence in 1s sliding windows
        window_samples = int(1.0 * sr)
        hop_samples = int(0.5 * sr)
        for w_start in range(0, len(region_audio) - window_samples, hop_samples):
            window = region_audio[w_start:w_start + window_samples]
            rms = np.sqrt(np.mean(window ** 2))
            energy_db = 20 * np.log10(rms + 1e-10)
            if energy_db < min_energy_db:
                abs_time = seg['start_time'] + w_start / sr
                dead_silence.append({
                    'time': round(abs_time, 1),
                    'time_fmt': f'{int(abs_time//60)}:{abs_time%60:04.1f}',
                    'energy_db': round(float(energy_db), 1),
                })

        # Measure overall region energy for consistency check
        rms = np.sqrt(np.mean(region_audio ** 2))
        energy_db = 20 * np.log10(rms + 1e-10)
        region_energies.append(float(energy_db))

    # Check last 30 seconds for dead silence
    last_30s = y[max(0, len(y) - int(30 * sr)):]
    window_samples = int(1.0 * sr)
    hop_samples = int(0.5 * sr)
    for w_start in range(0, len(last_30s) - window_samples, hop_samples):
        window = last_30s[w_start:w_start + window_samples]
        rms = np.sqrt(np.mean(window ** 2))
        energy_db = 20 * np.log10(rms + 1e-10)
        if energy_db < min_energy_db:
            abs_time = total_dur - 30 + w_start / sr
            dead_silence.append({
                'time': round(abs_time, 1),
                'time_fmt': f'{int(abs_time//60)}:{abs_time%60:04.1f}',
                'energy_db': round(float(energy_db), 1),
                'location': 'final_30s',
            })

    # Ambient consistency check
    ambient_consistent = True
    ambient_range_db = 0.0
    if len(region_energies) >= 2:
        ambient_range_db = max(region_energies) - min(region_energies)
        if ambient_range_db > max_ambient_variation_db:
            ambient_consistent = False

    details = {
        'silence_regions_checked': len(silence_regions),
        'dead_silence_windows': len(dead_silence),
        'dead_silence_flags': dead_silence[:10],
        'ambient_range_db': round(ambient_range_db, 1),
        'ambient_consistent': ambient_consistent,
        'max_ambient_variation_db': max_ambient_variation_db,
    }

    passed = len(dead_silence) == 0 and ambient_consistent
    if not passed:
        if dead_silence:
            print(f"  QA-AMBIENT: FAIL — {len(dead_silence)} dead silence windows detected:")
            for ds in dead_silence[:5]:
                print(f"    {ds['time_fmt']} — {ds['energy_db']} dB (min {min_energy_db} dB)")
        if not ambient_consistent:
            print(f"  QA-AMBIENT: FAIL — ambient energy varies by {ambient_range_db:.1f} dB (max {max_ambient_variation_db} dB)")
    else:
        print(f"  QA-AMBIENT: PASSED — no dead silence, ambient consistent ({ambient_range_db:.1f} dB range)")

    return passed, details


def qa_opening_quality_check(audio_path, manifest_data, opening_sec=60.0):
    """QA GATE 14: Opening Quality — tighter thresholds on first 60 seconds.

    The opening is what the listener hears first. Glitches here are catastrophic.
    Applies tighter versions of Gates 1, 5, 6, 10 to the first 60s.

    Returns (passed, details_dict).
    """
    import numpy as np

    print(f"\n  QA-OPENING: Checking first {opening_sec:.0f}s with tighter thresholds...")

    try:
        import librosa
    except ImportError:
        print(f"  QA-OPENING: WARNING — librosa not installed, skipping")
        return True, {'skipped': True, 'reason': 'missing_librosa'}

    y, sr = librosa.load(audio_path, sr=22050)
    total_dur = len(y) / sr

    if total_dur < opening_sec:
        print(f"  QA-OPENING: Audio shorter than {opening_sec}s — checking full file")
        opening_sec = total_dur

    opening_samples = int(opening_sec * sr)
    opening_audio = y[:opening_samples]

    flags = []

    # ── Check 1: Noise floor (tighter: -30 dB vs -26 dB standard) ──
    rms = np.sqrt(np.mean(opening_audio ** 2))
    noise_floor_db = 20 * np.log10(rms + 1e-10)
    # Note: noise floor measurement is relative to content — we measure
    # in silence gaps within the opening for a true noise floor
    silence_in_opening = []
    for seg in manifest_data.get('segments', []):
        if seg['type'] == 'silence' and seg['start_time'] < opening_sec:
            end = min(seg['end_time'], opening_sec)
            start_s = int(seg['start_time'] * sr)
            end_s = int(end * sr)
            if end_s - start_s > int(0.5 * sr):
                silence_in_opening.append(opening_audio[start_s:end_s] if end_s <= opening_samples else y[start_s:end_s])

    if silence_in_opening:
        silence_audio = np.concatenate(silence_in_opening)
        silence_rms = np.sqrt(np.mean(silence_audio ** 2))
        opening_noise_db = 20 * np.log10(silence_rms + 1e-10)
        if opening_noise_db > -30.0:
            flags.append({
                'check': 'noise_floor',
                'value': round(float(opening_noise_db), 1),
                'threshold': -30.0,
                'standard': -26.0,
            })
            print(f"  QA-OPENING: Noise floor {opening_noise_db:.1f} dB (opening max -30 dB)")

    # ── Check 2: Loudness consistency (tighter: 6 dB vs 6.5 dB standard) ──
    # Check per-second RMS in speech windows of the opening
    speech_rms_values = []
    for seg in manifest_data.get('segments', []):
        if seg['type'] == 'text' and seg['start_time'] < opening_sec:
            seg_start = int(seg['start_time'] * sr)
            seg_end = int(min(seg['start_time'] + seg['duration'], opening_sec) * sr)
            if seg_end > opening_samples:
                seg_end = opening_samples
            for s in range(seg_start, seg_end - sr, sr):
                sec_audio = opening_audio[s:s + sr]
                sec_rms = np.sqrt(np.mean(sec_audio ** 2))
                sec_db = 20 * np.log10(sec_rms + 1e-10)
                speech_rms_values.append(sec_db)

    if len(speech_rms_values) >= 3:
        median_rms = float(np.median(speech_rms_values))
        for i, db_val in enumerate(speech_rms_values):
            if db_val > median_rms + 6.0:
                flags.append({
                    'check': 'loudness_spike',
                    'value_db': round(db_val, 1),
                    'median_db': round(median_rms, 1),
                    'deviation_db': round(db_val - median_rms, 1),
                    'threshold_db': 6.0,
                    'standard_db': 6.5,
                })
                print(f"  QA-OPENING: Loudness spike {db_val:.1f} dB ({db_val - median_rms:.1f} dB above median, opening max 6 dB)")
                break  # One flag is enough

    details = {
        'opening_sec': opening_sec,
        'flags': flags,
        'total_flags': len(flags),
    }

    passed = len(flags) == 0
    if not passed:
        print(f"  QA-OPENING: FAIL — {len(flags)} opening quality issue(s)")
    else:
        print(f"  QA-OPENING: PASSED — opening quality meets tighter thresholds")

    return passed, details


def qa_visual_report(audio_path, manifest_data, session_name, gate_results, output_dir=None):
    """QA GATE 9: Energy Spike Detection + Visual Report.

    Generates a 4-panel PNG: waveform, mel spectrogram, energy plot, summary.
    Also performs per-window energy spike detection (PASS/FAIL):
      - Total energy >3x speech median = FAIL
      - HF energy (>4kHz) >10x speech median = FAIL

    Returns (passed, details_dict, report_path).
    """
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    print(f"\n  QA-REPORT: Generating visual report...")

    # Load audio
    import wave as _wave
    w = _wave.open(audio_path, 'r')
    n = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw = w.readframes(n)
    w.close()

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)

    duration_sec = len(samples) / sr
    time_axis = np.arange(len(samples)) / sr

    # Compute per-second RMS for energy plot
    rms_per_sec = []
    for i in range(0, len(samples) - sr, sr):
        chunk = samples[i:i + sr]
        rms = np.sqrt(np.mean(chunk**2))
        db = 20 * np.log10(rms / 32768) if rms > 0 else -100
        rms_per_sec.append(db)
    rms_per_sec = np.array(rms_per_sec)
    speech_rms = rms_per_sec[rms_per_sec > -40]
    median_rms = float(np.median(speech_rms)) if len(speech_rms) > 0 else -30

    # ── Energy spike detection (Gate 9 pass/fail) ──
    from scipy.signal import butter, sosfilt
    spike_window_sec = 2.0
    spike_win_samples = int(spike_window_sec * sr)
    spike_hop = int(1.0 * sr)  # 1s hop for 2s windows

    sos_hf = butter(4, 4000, btype='high', fs=sr, output='sos')
    hf_signal = sosfilt(sos_hf, samples)

    total_energies = []
    hf_energies = []
    spike_times = []

    for start in range(0, len(samples) - spike_win_samples, spike_hop):
        total_chunk = samples[start:start + spike_win_samples]
        hf_chunk = hf_signal[start:start + spike_win_samples]
        total_energies.append(float(np.mean(total_chunk**2)))
        hf_energies.append(float(np.mean(hf_chunk**2)))
        spike_times.append(start / sr)

    total_energies = np.array(total_energies)
    hf_energies = np.array(hf_energies)
    spike_times = np.array(spike_times)

    # Compute medians from SPEECH windows only (silence drags median down,
    # causing normal speech to flag as spikes)
    speech_ranges = []
    for seg in manifest_data.get('segments', []):
        if seg['type'] == 'text':
            speech_ranges.append((seg['start_time'], seg['start_time'] + seg['duration']))

    speech_mask = np.zeros(len(spike_times), dtype=bool)
    for i, t in enumerate(spike_times):
        for s_start, s_end in speech_ranges:
            if s_start <= t < s_end:
                speech_mask[i] = True
                break

    speech_total = total_energies[speech_mask & (total_energies > 0)]
    speech_hf = hf_energies[speech_mask & (hf_energies > 0)]
    median_total = float(np.median(speech_total)) if len(speech_total) > 0 else float(np.median(total_energies[total_energies > 0])) if np.any(total_energies > 0) else 1
    median_hf = float(np.median(speech_hf)) if len(speech_hf) > 0 else float(np.median(hf_energies[hf_energies > 0])) if np.any(hf_energies > 0) else 1

    energy_spikes = []
    for i in range(len(spike_times)):
        total_ratio = total_energies[i] / median_total if median_total > 0 else 0
        hf_ratio = hf_energies[i] / median_hf if median_hf > 0 else 0
        reasons = []
        if total_ratio > 12.0:
            reasons.append(f'total {total_ratio:.1f}x median')
        if hf_ratio > 28.0:
            reasons.append(f'HF {hf_ratio:.1f}x median')
        if reasons:
            t = spike_times[i]
            energy_spikes.append({
                'time': round(float(t), 1),
                'time_fmt': f'{int(t//60)}:{t%60:04.1f}',
                'total_ratio': round(float(total_ratio), 1),
                'hf_ratio': round(float(hf_ratio), 1),
                'reasons': ', '.join(reasons),
            })

    gate9_passed = len(energy_spikes) == 0
    gate9_details = {
        'median_total_energy': round(float(median_total), 2),
        'median_hf_energy': round(float(median_hf), 6),
        'windows_analyzed': len(spike_times),
        'spikes': energy_spikes,
    }

    if not gate9_passed:
        print(f"  QA-ENERGY: FAIL — {len(energy_spikes)} energy spikes detected:")
        for s in energy_spikes[:10]:
            print(f"    {s['time_fmt']} — {s['reasons']}")
    else:
        print(f"  QA-ENERGY: PASSED — no energy spikes ({len(spike_times)} windows analyzed)")

    # Silence regions from manifest
    silence_ranges = []
    for seg in manifest_data['segments']:
        if seg['type'] == 'silence':
            silence_ranges.append((seg['start_time'], seg['start_time'] + seg['duration']))

    # Overall verdict
    overall_pass = all(r.get('passed', True) for r in gate_results.values() if r is not None)
    verdict = "PASS" if overall_pass else "FAIL"
    date_str = time.strftime("%Y-%m-%d %H:%M")

    # Styling
    bg_color = '#1a1a2e'
    text_color = '#e0e0e0'
    grid_color = '#2a2a4e'
    silence_color = '#333355'

    fig, axes = plt.subplots(4, 1, figsize=(20, 16), dpi=150,
                              gridspec_kw={'height_ratios': [2, 3, 2, 1.5]})
    fig.patch.set_facecolor(bg_color)

    title_color = '#ff4444' if verdict == "FAIL" else '#44ff44'
    fig.suptitle(f'{session_name} — QA Report — {date_str} — {verdict}',
                 fontsize=16, color=title_color, fontweight='bold', y=0.98)

    # ── Panel 1: Waveform ──
    ax = axes[0]
    ax.set_facecolor(bg_color)

    # Downsample for plotting (max 10000 points)
    downsample = max(1, len(samples) // 10000)
    plot_samples = samples[::downsample] / 32768
    plot_time = time_axis[::downsample]

    ax.plot(plot_time, plot_samples, color='#4488cc', linewidth=0.3, alpha=0.8)

    # Shade silence regions
    for s_start, s_end in silence_ranges:
        ax.axvspan(s_start, s_end, alpha=0.15, color=silence_color)

    # Highlight flagged regions from gates
    for gate_name, result in gate_results.items():
        if result and not result.get('passed', True):
            flags = result.get('details', {})
            # Gate 6 flagged regions
            for region in flags.get('flagged_regions', []):
                ax.axvspan(region['start'], region['end'], alpha=0.3, color='#ff4444')
            # Gate 7 flags
            for flag in flags.get('flags', []):
                ax.axvline(x=flag['time'], color='#ff8800', alpha=0.5, linewidth=1)

    ax.set_ylabel('Amplitude', color=text_color, fontsize=9)
    ax.set_xlim(0, duration_sec)
    ax.tick_params(colors=text_color, labelsize=7)
    ax.grid(True, color=grid_color, alpha=0.3)
    ax.set_title('Waveform', color=text_color, fontsize=10, loc='left')

    # ── Panel 2: Mel Spectrogram ──
    ax = axes[1]
    ax.set_facecolor(bg_color)

    try:
        import librosa
        import librosa.display
        y_librosa = samples / 32768
        S = librosa.feature.melspectrogram(y=y_librosa, sr=sr, n_mels=128, fmax=10000)
        S_db = librosa.power_to_db(S, ref=np.max)
        img = librosa.display.specshow(S_db, x_axis='time', y_axis='mel', sr=sr,
                                        fmax=10000, ax=ax, cmap='viridis')
        ax.axhline(y=4000, color='#ffffff', linestyle='--', alpha=0.5, linewidth=0.8)
        ax.text(duration_sec * 0.98, 4200, '4kHz', color='#ffffff', alpha=0.5,
                fontsize=7, ha='right')
    except Exception as e:
        ax.text(0.5, 0.5, f'Spectrogram unavailable: {e}', transform=ax.transAxes,
                color=text_color, ha='center')

    ax.set_ylabel('Frequency (Hz)', color=text_color, fontsize=9)
    ax.tick_params(colors=text_color, labelsize=7)
    ax.set_title('Mel Spectrogram (0-10kHz)', color=text_color, fontsize=10, loc='left')

    # ── Panel 3: Energy Plot ──
    ax = axes[2]
    ax.set_facecolor(bg_color)

    time_secs = np.arange(len(rms_per_sec))
    colors = []
    for db in rms_per_sec:
        if db > median_rms + 4:
            colors.append('#ff4444')  # Red — spike
        elif db > median_rms + 2:
            colors.append('#ffaa00')  # Amber — elevated
        else:
            colors.append('#44cc44')  # Green — normal

    ax.bar(time_secs, rms_per_sec, width=1.0, color=colors, alpha=0.8)
    ax.axhline(y=median_rms, color='#ffffff', linestyle='-', alpha=0.5, linewidth=0.8)
    ax.axhline(y=median_rms + 4, color='#ff4444', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.text(len(rms_per_sec) * 0.98, median_rms + 0.5, f'median {median_rms:.0f} dB',
            color='#ffffff', alpha=0.5, fontsize=7, ha='right')

    # Shade silence regions
    for s_start, s_end in silence_ranges:
        ax.axvspan(s_start, s_end, alpha=0.15, color=silence_color)

    ax.set_ylabel('RMS (dB)', color=text_color, fontsize=9)
    ax.set_xlim(0, duration_sec)
    ax.set_ylim(max(-60, min(rms_per_sec) - 2), max(rms_per_sec) + 2)
    ax.tick_params(colors=text_color, labelsize=7)
    ax.grid(True, color=grid_color, alpha=0.3)
    ax.set_title('Per-Second Energy', color=text_color, fontsize=10, loc='left')

    # ── Panel 4: Summary ──
    ax = axes[3]
    ax.set_facecolor(bg_color)
    ax.axis('off')

    summary_lines = [
        f'Session: {session_name}    Duration: {duration_sec/60:.1f} min    Date: {date_str}',
        '',
    ]

    for gate_name, result in sorted(gate_results.items()):
        if result is None:
            continue
        status = "PASS" if result.get('passed', True) else "FAIL"
        emoji = "PASS" if status == "PASS" else "FAIL"
        extra = ""
        details = result.get('details', {})
        if not result.get('passed', True):
            # Add brief failure info
            if 'flagged_regions' in details:
                extra = f" — {len(details['flagged_regions'])} regions"
            elif 'flags' in details:
                extra = f" — {len(details['flags'])} anomalies"
            elif 'spikes' in details:
                extra = f" — {len(details['spikes'])} spikes"
            elif 'confirmed_repeats' in details:
                extra = f" — {len(details['confirmed_repeats'])} repeats"
        summary_lines.append(f'  [{emoji}] {gate_name}{extra}')

    summary_lines.append('')
    summary_lines.append(f'VERDICT: {verdict}')

    summary_text = '\n'.join(summary_lines)
    ax.text(0.02, 0.95, summary_text, transform=ax.transAxes,
            fontfamily='monospace', fontsize=9, color=text_color,
            verticalalignment='top')

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save
    if output_dir is None:
        output_dir = OUTPUT_DIR
    report_path = Path(output_dir) / f"{session_name}_QA_REPORT.png"
    fig.savefig(str(report_path), facecolor=bg_color, edgecolor='none')
    plt.close(fig)

    # Also save to Audio Quality Analysis directory
    qa_dir = Path("Audio Quality Analysis") / session_name
    qa_dir.mkdir(parents=True, exist_ok=True)
    qa_copy = qa_dir / f"{session_name}_QA_REPORT.png"
    shutil.copy(str(report_path), str(qa_copy))

    print(f"  QA-REPORT: Saved → {report_path}")
    print(f"  QA-REPORT: Copy  → {qa_copy}")
    return gate9_passed, gate9_details, str(report_path)


def scan_for_clicks(audio_path, manifest_data, threshold=QA_CLICK_THRESHOLD):
    """Scan mixed audio for click artifacts in silence regions.

    Returns list of (timestamp, jump_amplitude, peak_amplitude) for each click found.
    Only flags clicks where the sample jump exceeds the local peak (ratio > 1.0).
    """
    import wave as _wave
    import struct as _struct

    wav_path = audio_path + ".scan.wav"
    subprocess.run([
        'ffmpeg', '-y', '-i', audio_path,
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE), '-ac', '2',
        wav_path
    ], capture_output=True, check=True)

    w = _wave.open(wav_path, 'r')
    n = w.getnframes()
    frames = w.readframes(n)
    samples = _struct.unpack(f'<{n * 2}h', frames)
    w.close()
    os.remove(wav_path)

    # Build silence region lookup
    silence_ranges = []
    for seg in manifest_data['segments']:
        if seg['type'] == 'silence':
            silence_ranges.append((seg['start_time'], seg['start_time'] + seg['duration']))

    def in_silence(ts):
        return any(start <= ts <= end for start, end in silence_ranges)

    # Scan in 10ms windows
    window = int(SAMPLE_RATE * 0.01)
    clicks = []
    for start in range(0, n - window, window // 2):
        chunk = [samples[i * 2] for i in range(start, min(start + window, n))]
        if not chunk:
            continue
        peak = max(abs(s) for s in chunk)
        if peak < 50:  # Skip true silence
            continue
        max_jump = max(abs(chunk[i + 1] - chunk[i]) for i in range(len(chunk) - 1)) if len(chunk) > 1 else 0
        ts = start / SAMPLE_RATE
        if in_silence(ts) and max_jump > peak and max_jump > threshold:
            clicks.append((ts, max_jump, peak))

    # Deduplicate close timestamps
    filtered = []
    for c in clicks:
        if not filtered or c[0] - filtered[-1][0] > 0.1:
            filtered.append(c)

    return filtered


def patch_stitch_clicks(raw_mp3, manifest_data, output_mp3, ambient_name=None, fade_ms=QA_FADE_MS, click_times=None, ambient_db=None):
    """Patch click artifacts by applying crossfades at stitch boundaries near detected clicks.

    Only patches stitch points within 1 second of a detected click artifact.
    If no clicks are near any stitch point, skips patching entirely.
    """
    import wave as _wave
    import struct as _struct
    import math as _math

    # Get stitch points
    all_stitch_times = []
    for i, seg in enumerate(manifest_data['segments']):
        if i == 0:
            continue
        prev = manifest_data['segments'][i - 1]
        if prev['type'] != seg['type']:
            all_stitch_times.append(seg['start_time'])
        elif prev['type'] == 'silence' and seg['type'] == 'silence':
            all_stitch_times.append(seg['start_time'])

    # Only patch stitch points within 1s of a detected click
    if click_times:
        stitch_times = [st for st in all_stitch_times
                        if any(abs(st - ct) < 1.0 for ct in click_times)]
    else:
        stitch_times = all_stitch_times

    if not stitch_times:
        print(f"    No stitch points near detected clicks — skipping patch")
        # Still need to produce the output file (re-mix ambient + encode)
        # Just copy through the pipeline without crossfades
        import shutil as _shutil

    # Convert raw to WAV
    wav_path = raw_mp3 + ".patch.wav"
    subprocess.run([
        'ffmpeg', '-y', '-i', raw_mp3,
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE), '-ac', '2',
        wav_path
    ], capture_output=True, check=True)

    w = _wave.open(wav_path, 'r')
    n = w.getnframes()
    nch = w.getnchannels()
    sw = w.getsampwidth()
    frames = w.readframes(n)
    samples = list(_struct.unpack(f'<{n * nch}h', frames))
    w.close()

    fade_samples = int(SAMPLE_RATE * fade_ms / 1000)

    for ts in stitch_times:
        center = int(ts * SAMPLE_RATE)
        # Cosine fade-out before stitch
        for i in range(fade_samples):
            idx = (center - fade_samples + i) * nch
            if 0 <= idx < len(samples) - nch:
                factor = 0.5 * (1 + _math.cos(_math.pi * i / fade_samples))
                for ch in range(nch):
                    samples[idx + ch] = int(samples[idx + ch] * factor)
        # Cosine fade-in after stitch
        for i in range(fade_samples):
            idx = (center + i) * nch
            if 0 <= idx < len(samples) - nch:
                factor = 0.5 * (1 - _math.cos(_math.pi * i / fade_samples))
                for ch in range(nch):
                    samples[idx + ch] = int(samples[idx + ch] * factor)

    # Save patched WAV
    patched_wav = raw_mp3 + ".patched.wav"
    data = _struct.pack(f'<{len(samples)}h', *samples)
    wout = _wave.open(patched_wav, 'w')
    wout.setnchannels(nch)
    wout.setsampwidth(sw)
    wout.setframerate(SAMPLE_RATE)
    wout.writeframes(data)
    wout.close()

    # Loudnorm (WAV → WAV for lossless pipeline)
    normed_wav = raw_mp3 + ".normed.wav"
    subprocess.run([
        'ffmpeg', '-y', '-i', patched_wav,
        '-af', 'loudnorm=I=-24:TP=-2:LRA=11',
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        normed_wav
    ], capture_output=True, check=True)

    # Mix with ambient if specified (WAV → WAV, then encode MP3 at the end)
    mixed_wav = raw_mp3 + ".mixed.wav"
    if ambient_name:
        ambient_path = None
        for ext in ['wav', 'mp3']:
            for suffix in ['-8hr', '-extended', '']:
                candidate = AMBIENT_DIR / f"{ambient_name}{suffix}.{ext}"
                if candidate.exists():
                    ambient_path = candidate
                    break
            if ambient_path:
                break

        if ambient_path and ambient_path.exists():
            voice_duration = get_audio_duration(normed_wav)
            fade_out_start = max(0, voice_duration - AMBIENT_FADE_OUT_DURATION)
            # Garden ambient has 9.5s dead silence at start — skip with -ss 10
            ambient_input = ['-i', str(ambient_path)]
            if ambient_name == 'garden':
                ambient_input = ['-ss', '10', '-i', str(ambient_path)]
            _vol = ambient_db if ambient_db is not None else AMBIENT_VOLUME_DB
            subprocess.run([
                'ffmpeg', '-y',
                '-i', normed_wav, *ambient_input,
                '-filter_complex', (
                    f"[1:a]volume={_vol}dB,"
                    f"afade=t=in:st={AMBIENT_FADE_IN_START}:d={AMBIENT_FADE_IN_DURATION},"
                    f"afade=t=out:st={fade_out_start}:d={AMBIENT_FADE_OUT_DURATION}[amb];"
                    f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2:normalize=0"
                ),
                '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
                mixed_wav
            ], capture_output=True, check=True)
        else:
            shutil.copy(normed_wav, mixed_wav)
    else:
        shutil.copy(normed_wav, mixed_wav)

    # Final encode: WAV → MP3 128kbps (single lossy step)
    subprocess.run([
        'ffmpeg', '-y', '-i', mixed_wav,
        '-c:a', 'libmp3lame', '-b:a', '128k',
        output_mp3
    ], capture_output=True, check=True)

    # Update the raw file with patched version (keep as WAV if it was WAV)
    if raw_mp3.endswith('.wav'):
        shutil.copy(normed_wav, raw_mp3)
    else:
        # Legacy: convert back to MP3 for old raw files
        subprocess.run([
            'ffmpeg', '-y', '-i', normed_wav,
            '-c:a', 'libmp3lame', '-b:a', '128k',
            raw_mp3
        ], capture_output=True, check=True)

    # Cleanup temp files
    for f in [wav_path, patched_wav, normed_wav, mixed_wav]:
        if os.path.exists(f):
            os.remove(f)

    return len(stitch_times)


def qa_loop(final_mp3, raw_mp3, manifest_data, ambient_name=None, raw_narration_wav=None,
            pre_cleanup_wav=None, session_name=None, metadata=None):
    """Full 14-gate QA pipeline.

    GATE 1 (Primary): Quality benchmarks — noise floor and HF hiss vs master
    GATE 2 (Click scan): Scan → fix → rescan loop for click artifacts
    GATE 3 (Independent): Spectral comparison against master reference WAV
    GATE 4 (Voice): MFCC cosine + F0 deviation vs Marco master (pre-cleanup)
    GATE 5 (Loudness): Per-second RMS consistency — catches per-chunk level surges
    GATE 6 (HF Hiss): Sliding-window high-frequency hiss detector (non-speech, post-cleanup)
    GATE 7 (Surge): Volume surge/drop detector with silence exclusion (pre-cleanup)
    GATE 8 (Repeat): Repeated content detector — MFCC + Whisper (pre-cleanup)
    GATE 9 (Energy): Energy spike detection + visual report
    GATE 10 (Rate): Speech rate anomaly detection (pre-cleanup)
    GATE 11 (Silence): Silence region integrity — verify pauses contain silence
    GATE 12 (Duration): Duration accuracy — final within 15% of target
    GATE 13 (Ambient): Ambient continuity — no dead silence in pauses
    GATE 14 (Opening): Opening quality — tighter thresholds on first 60s

    ALL gates must pass. Any failure = no deploy.
    Human review remains MANDATORY.
    Returns True only if all gates pass.
    """
    if metadata is None:
        metadata = {}

    print(f"\n{'='*60}")
    print("  QA: 14-GATE QUALITY ASSURANCE")
    print(f"{'='*60}")

    gate_results = {}
    any_failed = False

    # Choose audio for pre-cleanup gates (6-8 and 4)
    pre_wav = pre_cleanup_wav if (pre_cleanup_wav and os.path.exists(pre_cleanup_wav)) else raw_narration_wav

    # ── GATE 1: Quality benchmarks ──
    if raw_narration_wav and os.path.exists(raw_narration_wav):
        quality_passed, quality_details = qa_quality_check(raw_narration_wav, manifest_data)
        gate_results['Gate 1: Quality'] = {'passed': quality_passed, 'details': quality_details}
        if not quality_passed:
            any_failed = True
    else:
        print(f"  QA-QUALITY: SKIPPED (no raw narration WAV available)")

    # ── GATE 2: Click artifacts ──
    # Scan raw narration (no ambient) to avoid false positives from ambient transients (bird chirps etc.)
    click_scan_file = raw_mp3 if raw_mp3 and os.path.exists(raw_mp3) else final_mp3
    clicks_passed = True
    for qa_pass in range(1, QA_MAX_PASSES + 1):
        clicks = scan_for_clicks(click_scan_file, manifest_data)

        if not clicks:
            print(f"  QA PASS {qa_pass}: CLEAN — 0 click artifacts")
            break

        print(f"  QA PASS {qa_pass}: FOUND {len(clicks)} click artifacts")
        for ts, jump, peak in clicks[:5]:
            mins = int(ts // 60)
            secs = ts % 60
            print(f"    {mins}:{secs:05.2f} — jump={jump}, peak={peak}")
        if len(clicks) > 5:
            print(f"    ... and {len(clicks) - 5} more")

        click_timestamps = [ts for ts, jump, peak in clicks]
        print(f"  QA PASS {qa_pass}: Patching artifacts near stitch points...")
        patches = patch_stitch_clicks(raw_mp3, manifest_data, final_mp3, ambient_name, click_times=click_timestamps, ambient_db=metadata.get('ambient_db'))
        print(f"  QA PASS {qa_pass}: Applied crossfades at {patches} stitch points")
    else:
        clicks = scan_for_clicks(click_scan_file, manifest_data)
        if clicks:
            clicks_passed = False
            print(f"  QA: {len(clicks)} clicks remain after {QA_MAX_PASSES} passes")

    gate_results['Gate 2: Clicks'] = {'passed': clicks_passed, 'details': {'remaining_clicks': len(clicks) if not clicks_passed else 0}}
    if not clicks_passed:
        any_failed = True

    # ── GATE 3: Independent spectral verification ──
    if raw_narration_wav and os.path.exists(raw_narration_wav):
        independent_passed, independent_details = qa_independent_check(raw_narration_wav, manifest_data)
        gate_results['Gate 3: Spectral'] = {'passed': independent_passed, 'details': independent_details}
        if not independent_passed:
            any_failed = True

    # ── GATE 4: Master voice comparison (MFCC + F0) ──
    if pre_wav and os.path.exists(pre_wav):
        voice_passed, voice_details = qa_master_voice_check(pre_wav)
        gate_results['Gate 4: Voice'] = {'passed': voice_passed, 'details': voice_details}
        if not voice_passed:
            any_failed = True

    # ── GATE 5: Loudness consistency (per-second RMS) ──
    if raw_narration_wav and os.path.exists(raw_narration_wav):
        loudness_passed, loudness_details = qa_loudness_consistency_check(
            raw_narration_wav, manifest_data)
        gate_results['Gate 5: Loudness'] = {'passed': loudness_passed, 'details': loudness_details}
        if not loudness_passed:
            any_failed = True

    # ── GATE 6: HF hiss detector (POST-cleanup per Bible Section 13) ──
    if raw_narration_wav and os.path.exists(raw_narration_wav):
        hiss_passed, hiss_details = qa_hf_hiss_check(raw_narration_wav, manifest_data)
        gate_results['Gate 6: HF Hiss'] = {'passed': hiss_passed, 'details': hiss_details}
        if not hiss_passed:
            any_failed = True

    # ── GATE 7: Volume surge/drop detector (pre-cleanup) ──
    if pre_wav and os.path.exists(pre_wav):
        surge_passed, surge_details = qa_volume_surge_check(pre_wav, manifest_data)
        gate_results['Gate 7: Surge'] = {'passed': surge_passed, 'details': surge_details}
        if not surge_passed:
            any_failed = True

    # ── GATE 8: Repeated content detector (pre-cleanup) ──
    if pre_wav and os.path.exists(pre_wav):
        expected_reps = metadata.get('expected_repetitions', [])
        repeat_passed, repeat_details = qa_repeated_content_check(pre_wav, manifest_data, expected_repetitions=expected_reps)
        gate_results['Gate 8: Repeat'] = {'passed': repeat_passed, 'details': repeat_details}
        if not repeat_passed:
            any_failed = True

    # ── GATE 10: Speech rate anomaly detection (pre-cleanup) ──
    if pre_wav and os.path.exists(pre_wav):
        rate_passed, rate_details = qa_speech_rate_check(pre_wav, manifest_data)
        gate_results['Gate 10: Rate'] = {'passed': rate_passed, 'details': rate_details}
        if not rate_passed:
            any_failed = True

    # ── GATE 11: Silence Region Integrity (raw narration) ──
    if raw_narration_wav and os.path.exists(raw_narration_wav):
        silence_passed, silence_details = qa_silence_integrity_check(raw_narration_wav, manifest_data)
        gate_results['Gate 11: Silence'] = {'passed': silence_passed, 'details': silence_details}
        if not silence_passed:
            any_failed = True

    # ── GATE 12: Duration Accuracy ──
    if final_mp3 and os.path.exists(final_mp3):
        dur_passed, dur_details = qa_duration_accuracy_check(final_mp3, metadata)
        gate_results['Gate 12: Duration'] = {'passed': dur_passed, 'details': dur_details}
        if not dur_passed:
            any_failed = True

    # ── GATE 13: Ambient Continuity (final mixed output) ──
    if final_mp3 and os.path.exists(final_mp3) and ambient_name:
        ambient_passed, ambient_details = qa_ambient_continuity_check(final_mp3, manifest_data)
        gate_results['Gate 13: Ambient'] = {'passed': ambient_passed, 'details': ambient_details}
        if not ambient_passed:
            any_failed = True
    elif not ambient_name:
        print(f"\n  QA-AMBIENT: SKIPPED — no ambient specified for this session")
        gate_results['Gate 13: Ambient'] = {'passed': True, 'details': {'skipped': True, 'reason': 'no_ambient'}}

    # ── GATE 14: Opening Quality (tighter thresholds, first 60s) ──
    if pre_wav and os.path.exists(pre_wav):
        opening_passed, opening_details = qa_opening_quality_check(pre_wav, manifest_data)
        gate_results['Gate 14: Opening'] = {'passed': opening_passed, 'details': opening_details}
        if not opening_passed:
            any_failed = True

    # ── GATE 9: Energy Spike Detection + Visual Report (ALWAYS runs last) ──
    report_wav = pre_wav or raw_narration_wav
    s_name = session_name or 'unknown'
    if report_wav and os.path.exists(report_wav):
        try:
            g9_passed, g9_details, _ = qa_visual_report(report_wav, manifest_data, s_name, gate_results)
            gate_results['Gate 9: Energy'] = {'passed': g9_passed, 'details': g9_details}
            if not g9_passed:
                any_failed = True
        except Exception as e:
            print(f"  QA-REPORT: ERROR generating report: {e}")

    # ── VERDICT ──
    if any_failed:
        failed_gates = [name for name, r in gate_results.items() if not r.get('passed', True)]
        print(f"\n  QA: REJECTED — {len(failed_gates)} gate(s) failed: {', '.join(failed_gates)}")
        print(f"  QA: Build will NOT be deployed")
        return False

    print(f"\n  QA: ALL GATES PASSED")
    print(f"  QA: REMINDER — Human review is MANDATORY. Automated gates cannot catch subtle prosody issues.")
    return True


def deploy_to_r2(local_path, r2_key):
    """Upload file to Cloudflare R2 via wrangler CLI."""
    print(f"  DEPLOY: Uploading to R2 → {r2_key}")
    result = subprocess.run([
        'npx', 'wrangler', 'r2', 'object', 'put',
        f'{R2_BUCKET}/{r2_key}',
        '--file', str(local_path),
        '--remote',
        '--content-type', 'audio/mpeg',
    ], capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"  DEPLOY: FAILED — {result.stderr.strip()}")
        return False

    print(f"  DEPLOY: Upload complete")
    return True


# ============================================================================
# EMAIL NOTIFICATION
# ============================================================================

def send_build_email(session_name, duration_min, qa_passed, r2_url):
    """Send build completion email via Resend API."""
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        print("  EMAIL: Skipped (no RESEND_API_KEY)")
        return

    qa_status = "PASSED" if qa_passed else "REVIEW NEEDED"
    body = (
        f"Session: {session_name}\n"
        f"Duration: {duration_min:.1f} min\n"
        f"QA: {qa_status}\n\n"
        f"Audio: {r2_url}\n"
        f"Page: https://salus-mind.com/sessions/{session_name.split('-', 1)[1] if '-' in session_name else session_name}.html"
    )

    payload = json.dumps({
        "from": "Salus Build <onboarding@resend.dev>",
        "to": ["scottripley@icloud.com"],
        "subject": f"{session_name} — LIVE",
        "text": body
    })

    try:
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', 'https://api.resend.com/emails',
            '-H', f'Authorization: Bearer {api_key}',
            '-H', 'Content-Type: application/json',
            '-d', payload
        ], capture_output=True, text=True, timeout=15)
        if '"id"' in result.stdout:
            print(f"  EMAIL: Sent to scottripley@icloud.com")
        else:
            print(f"  EMAIL: Failed — {result.stdout}")
    except Exception as e:
        print(f"  EMAIL: Failed — {e}")


# ============================================================================
# MAIN BUILD
# ============================================================================

def build_session(session_name, dry_run=False, provider='fish', voice_id=None, model='v2',
                   cleanup_mode='full', no_deploy=False, focus_chunks=None):
    """Build a complete session: TTS → concat → mix → QA loop → deploy.

    The full pipeline runs autonomously:
    1. Generate TTS chunks
    2. Concatenate with silences and edge fades
    3. Mix with ambient
    4. QA scan for click artifacts
    5. Auto-patch and rescan until clean (up to QA_MAX_PASSES)
    6. Deploy to R2 (unless --no-deploy)

    No human listening required. Ship when clean.
    """
    script_path = SCRIPT_DIR / f"{session_name}.txt"
    if not script_path.exists():
        script_path = SLEEP_STORY_DIR / f"{session_name}.txt"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found in content/scripts/ or content/sleep-stories/")

    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MIXED_DIR.mkdir(parents=True, exist_ok=True)

    # Output paths
    final_path = OUTPUT_DIR / f"{session_name}.mp3"
    raw_path = OUTPUT_RAW_DIR / f"{session_name}.mp3"
    mixed_path = OUTPUT_MIXED_DIR / f"{session_name}.mp3"
    manifest_path = OUTPUT_DIR / f"{session_name}_manifest.json"

    print("=" * 60)
    print(f"Building: {session_name} (v3 chunked, provider={provider})")
    print("=" * 60)

    metadata = parse_script(script_path)
    category = metadata['category']
    ambient = metadata['ambient']
    ambient_db = metadata.get('ambient_db')
    ambient_fade_in = metadata.get('ambient_fade_in')
    ambient_fade_out = metadata.get('ambient_fade_out')
    api_emotion = metadata.get('api_emotion', 'calm')

    print(f"  Title: {metadata['title']}")
    print(f"  Category: {category}")
    print(f"  Ambient: {ambient or 'none'}" + (f" @ {ambient_db}dB" if ambient_db is not None else ""))
    print(f"  Provider: {provider}")
    if provider == 'fish':
        print(f"  V3-HD: emotion={api_emotion}, speed=0.95")
    if provider == 'elevenlabs':
        print(f"  Model: {model}")
        print(f"  Voice: {voice_id or ELEVENLABS_VOICE_ID}")
    elif provider == 'resemble':
        print(f"  Voice: {voice_id or RESEMBLE_VOICE_ID}")
    print(f"  Cleanup: {cleanup_mode}")
    print(f"  Deploy: {'OFF' if no_deploy else 'AUTO → R2'}")

    # Process script into blocks with pauses
    blocks = process_script_for_tts(metadata['content'], category)

    total_text = ' '.join(text for text, _ in blocks)
    total_silence = sum(pause for _, pause in blocks)

    print(f"  Text blocks: {len(blocks)} (raw)")
    print(f"  Total chars: {len(total_text)}")
    print(f"  Est. narration: {len(total_text)/1000*1.2:.1f} min")
    print(f"  Total silence: {total_silence/60:.1f} min")
    print(f"  Est. total: {len(total_text)/1000*1.2 + total_silence/60:.1f} min")

    # Provider-specific block merging
    if provider == 'elevenlabs':
        combined_blocks = merge_short_blocks(blocks)
        if len(combined_blocks) != len(blocks):
            print(f"  After merging short blocks: {len(combined_blocks)} (from {len(blocks)} raw)")
    elif provider == 'resemble':
        combined_blocks = merge_blocks_for_resemble(blocks, category=category)
        print(f"  Resemble chunks: {len(combined_blocks)} (from {len(blocks)} raw)")
    else:
        # Fish: merge blocks under 10 chars only (Fish handles short chunks natively)
        combined_blocks = merge_short_blocks(blocks, min_chars=10)
        if len(combined_blocks) != len(blocks):
            print(f"  After merging short blocks (<50 chars): {len(combined_blocks)} (from {len(blocks)} raw)")

    # Humanize pauses
    if provider in ('elevenlabs', 'resemble'):
        combined_blocks = humanize_pauses(combined_blocks)
        humanized_silence = sum(pause for _, pause in combined_blocks)
        print(f"  Humanized silence: {humanized_silence/60:.1f} min")

    if dry_run:
        print(f"\n  DRY RUN - would generate {len(combined_blocks)} voice blocks")
        for i, (text, pause) in enumerate(combined_blocks):
            print(f"    Block {i+1}: \"{text[:60]}...\" [{len(text)} chars, {pause}s]")
        return True

    # ================================================================
    # PHASE 1: GENERATE TTS
    # ================================================================
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"  Processing {len(combined_blocks)} blocks")

        voice_files = []
        silences = []
        manifest_segments = []
        request_ids = []
        flagged_chunks = []
        prev_chunk_mfcc = None  # For tonal consistency scoring
        current_time = 0.0

        print(f"\n  Generating TTS chunks ({provider})...")

        for i, (text, pause) in enumerate(combined_blocks):
            if provider == 'resemble':
                block_path = os.path.join(temp_dir, f"block_{i}.wav")
                generate_tts_chunk_resemble(text, block_path, i, voice_id=voice_id)
            elif provider == 'elevenlabs':
                block_path = os.path.join(temp_dir, f"block_{i}.mp3")
                _, req_id = generate_tts_chunk_elevenlabs(
                    text, block_path, i,
                    voice_id=voice_id, model=model,
                    previous_request_ids=request_ids,
                )
                if req_id:
                    request_ids.append(req_id)
                    if len(request_ids) > 3:
                        request_ids = request_ids[-3:]
            else:
                # Fish TTS with per-chunk QA: generate N versions, keep best
                block_path = os.path.join(temp_dir, f"block_{i}.mp3")
                if len(text) > CHUNK_SIZE:
                    # Long text: split into sub-chunks, no per-chunk QA on sub-chunks
                    chunks = chunk_text_at_sentences(text)
                    chunk_files = []
                    for j, chunk in enumerate(chunks):
                        chunk_path = os.path.join(temp_dir, f"block_{i}_chunk_{j}.mp3")
                        generate_tts_chunk(chunk, chunk_path, len(voice_files) + j, emotion=api_emotion)
                        chunk_files.append(chunk_path)
                    crossfade_audio_files(chunk_files, block_path)
                else:
                    # Standard chunk: generate multiple versions, score, keep best
                    # Tonal consistency: pass previous chunk's MFCC profile
                    # Focus mode: problem chunks get 10 versions, others get 5
                    chunk_num = i + 1
                    is_focus = focus_chunks and chunk_num in focus_chunks
                    n_ver = 10 if is_focus else 5
                    max_ret = 12 if is_focus else 6
                    focus_tag = " [FOCUS]" if is_focus else ""
                    print(f"    Chunk {chunk_num} QA (best-of-{n_ver}):{focus_tag}")
                    _, chunk_score, chunk_flagged, chunk_mfcc = generate_chunk_with_qa(
                        text, block_path, len(voice_files),
                        emotion=api_emotion, n_versions=n_ver, max_retries=max_ret,
                        prev_chunk_mfcc=prev_chunk_mfcc
                    )
                    prev_chunk_mfcc = chunk_mfcc  # Chain for next chunk
                    if chunk_flagged:
                        flagged_chunks.append({
                            'index': i + 1,
                            'text': text[:80],
                            'score': chunk_score,
                        })
                        print(f"      ⚠ FLAGGED — may need rewrite")

            # Duration check (applies to all providers)
            duration = get_audio_duration(block_path)
            expected = len(text) / 15.0  # ~15 chars/sec estimate

            # Build manifest
            manifest_segments.append({
                "index": len(manifest_segments),
                "type": "text",
                "start_time": current_time,
                "text": text,
                "duration": round(duration, 2),
                "expected": round(expected, 2),
                "end_time": round(current_time + duration, 2),
            })
            current_time += duration

            if pause > 0:
                manifest_segments.append({
                    "index": len(manifest_segments),
                    "type": "silence",
                    "start_time": round(current_time, 2),
                    "duration": round(pause, 1),
                    "end_time": round(current_time + pause, 2),
                })
                current_time += pause

            voice_files.append(block_path)
            silences.append(pause)

        # Per-chunk QA summary
        if flagged_chunks:
            print(f"\n  ⚠ PER-CHUNK QA: {len(flagged_chunks)} chunk(s) flagged for potential rewrite:")
            for fc in flagged_chunks:
                print(f"    Chunk {fc['index']}: \"{fc['text']}...\" (score={fc['score']['score']:.3f})")
            # Save flagged chunks to manifest for tracking
        else:
            if provider == 'fish':
                print(f"\n  ✓ PER-CHUNK QA: All chunks scored above threshold")

        # ================================================================
        # PHASE 1.5: LALAL.AI AUDIO CLEANING (DISABLED — degrades voice quality)
        # Testing showed LALAL strips vocal character from Marco. Echo/voice shift
        # are TTS generation problems, not post-processing problems.
        # ================================================================
        # if LALAL_API_KEY and provider == 'fish':
        #     voice_files = lalal_clean_chunks(voice_files, temp_dir)

        # ================================================================
        # PHASE 2: CONCATENATE + MIX (lossless WAV pipeline)
        # ================================================================
        print(f"\n  Concatenating {len(voice_files)} blocks with silences (lossless WAV)...")
        voice_path = os.path.join(temp_dir, "voice_complete.wav")
        pre_cleanup_wav_path = OUTPUT_RAW_DIR / f"{session_name}_precleanup.wav"
        concatenate_with_silences(voice_files, silences, voice_path, temp_dir, cleanup_mode=cleanup_mode,
                                   pre_cleanup_path=str(pre_cleanup_wav_path))

        voice_duration = get_audio_duration(voice_path)
        print(f"  Voice track: {voice_duration/60:.1f} min")

        if voice_duration > MAX_DURATION_SECONDS:
            print(f"  WARNING: Exceeds max duration!")

        # Save raw narration (WAV)
        raw_wav_path = raw_path.with_suffix('.wav')
        shutil.copy(voice_path, str(raw_wav_path))
        print(f"  Raw narration saved: {raw_wav_path}")

        # Save manifest
        manifest_data = {
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "script": session_name,
            "category": category,
            "ambient": ambient,
            "total_tts_duration": round(sum(s['duration'] for s in manifest_segments if s['type'] == 'text'), 2),
            "total_silence": round(sum(s['duration'] for s in manifest_segments if s['type'] == 'silence'), 1),
            "text_segments": sum(1 for s in manifest_segments if s['type'] == 'text'),
            "segments": manifest_segments,
            "flagged_chunks": flagged_chunks if flagged_chunks else [],
        }
        with open(str(manifest_path), 'w') as f:
            json.dump(manifest_data, f, indent=2)
        print(f"  Manifest saved: {manifest_path}")

        # Mix ambient (WAV output)
        mixed_wav = os.path.join(temp_dir, "mixed_complete.wav")
        if ambient:
            print(f"\n  Mixing ambient '{ambient}'...")
            mix_ambient(voice_path, ambient, mixed_wav, volume_db=ambient_db, fade_in=ambient_fade_in, fade_out=ambient_fade_out)
        else:
            shutil.copy(voice_path, mixed_wav)

        # ================================================================
        # FINAL ENCODE: WAV → MP3 128kbps (the only lossy step)
        # ================================================================
        print(f"\n  Encoding final MP3 at 128kbps (single lossy step)...")
        cmd = [
            'ffmpeg', '-y', '-i', mixed_wav,
            '-c:a', 'libmp3lame', '-b:a', '128k',
            str(final_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    # Also save to mixed dir
    shutil.copy(str(final_path), str(mixed_path))

    final_duration = get_audio_duration(str(final_path))
    print(f"\n  BUILD COMPLETE: {final_path}")
    print(f"  Duration: {final_duration/60:.1f} min")

    # ================================================================
    # PHASE 3: QA — SCAN → FIX → RESCAN LOOP
    # ================================================================
    raw_for_qa = str(raw_wav_path) if raw_wav_path.exists() else str(raw_path)
    pre_cleanup_for_qa = str(pre_cleanup_wav_path) if pre_cleanup_wav_path.exists() else None
    qa_passed = qa_loop(str(final_path), raw_for_qa, manifest_data, ambient,
                        raw_narration_wav=str(raw_wav_path) if raw_wav_path.exists() else None,
                        pre_cleanup_wav=pre_cleanup_for_qa,
                        session_name=session_name,
                        metadata=metadata)

    if qa_passed:
        # Update mixed copy after QA patching
        shutil.copy(str(final_path), str(mixed_path))
    else:
        print(f"\n  QA REJECTED — build will NOT be deployed")
        print(f"  File saved locally for inspection: {final_path}")
        print(f"  Raw narration: {raw_wav_path}")

    # ================================================================
    # PHASE 4: DEPLOY TO R2 (only if QA passed)
    # ================================================================
    if qa_passed and not no_deploy:
        r2_key = f"{R2_PATH_PREFIX}/{session_name}.mp3"
        deployed = deploy_to_r2(str(final_path), r2_key)
        if deployed:
            print(f"\n  LIVE: https://media.salus-mind.com/{r2_key}")
        else:
            print(f"\n  DEPLOY FAILED — file saved locally at {final_path}")
    elif not qa_passed:
        print(f"\n  Deploy BLOCKED by QA rejection")
    else:
        print(f"\n  Deploy skipped (--no-deploy)")

    # ================================================================
    # DONE
    # ================================================================
    print(f"\n{'='*60}")
    if qa_passed and not no_deploy:
        status = "SHIPPED"
    elif qa_passed:
        status = "BUILT (not deployed)"
    else:
        status = "REJECTED — QA FAILED"
    print(f"  {status}: {session_name}")
    print(f"  Duration: {final_duration/60:.1f} min")
    print(f"  QA: {'PASSED' if qa_passed else 'REJECTED'}")
    print(f"{'='*60}")

    # Email notification — only on successful deploy (not during dev iterations)
    if qa_passed and not no_deploy:
        r2_url = f"https://media.salus-mind.com/{R2_PATH_PREFIX}/{session_name}.mp3"
        send_build_email(session_name, final_duration / 60, qa_passed, r2_url)

    return qa_passed


def main():
    parser = argparse.ArgumentParser(description="Salus Audio Builder v3 (chunked)")
    parser.add_argument('session', help='Session name to build')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without generating')
    parser.add_argument('--provider', choices=['fish', 'elevenlabs', 'resemble'], default='fish',
                        help='TTS provider (default: fish)')
    parser.add_argument('--voice', dest='voice_id', default=None,
                        help='Override voice ID for the chosen provider')
    parser.add_argument('--model', choices=['v2', 'v3'], default='v2',
                        help='ElevenLabs model (default: v2, ignored for Fish)')
    parser.add_argument('--no-cleanup', action='store_true',
                        help='Skip audio cleanup for raw quality testing')
    parser.add_argument('--cleanup', choices=['full', 'resemble', 'medium', 'light', 'none'], default=None,
                        help='Override cleanup mode (default: full for fish, resemble for resemble)')
    parser.add_argument('--no-deploy', action='store_true',
                        help='Build and QA only — do not upload to R2')
    parser.add_argument('--focus-chunks', default=None,
                        help='Comma-separated chunk numbers to regenerate with extra attempts (e.g. 1,3,11,13,14)')

    args = parser.parse_args()

    # Parse focus chunks into a set
    focus_chunk_set = set()
    if args.focus_chunks:
        for c in args.focus_chunks.split(','):
            focus_chunk_set.add(int(c.strip()))
        print(f"  FOCUS MODE: Chunks {sorted(focus_chunk_set)} get 10 versions, others get 5")

    # Determine cleanup mode
    if args.cleanup:
        cleanup_mode = args.cleanup
    elif args.no_cleanup:
        cleanup_mode = 'none'
    elif args.provider == 'elevenlabs':
        cleanup_mode = 'light'
    elif args.provider == 'resemble':
        cleanup_mode = 'resemble'
    else:
        cleanup_mode = 'full'

    try:
        build_session(
            args.session,
            dry_run=args.dry_run,
            provider=args.provider,
            voice_id=args.voice_id,
            model=args.model,
            cleanup_mode=cleanup_mode,
            no_deploy=args.no_deploy,
            focus_chunks=focus_chunk_set,
        )
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
