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
QA_CLICK_THRESHOLD = 100  # Min amplitude jump to count as click
QA_FADE_MS = 20           # Crossfade width at stitch boundaries

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
AMBIENT_FADE_IN_DURATION = 15    # 15 seconds fade-in (per spec)
AMBIENT_FADE_OUT_DURATION = 8    # 8 seconds fade-out (per spec)

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
            if key in ['duration', 'category', 'ambient', 'style']:
                if key == 'ambient':
                    metadata[key] = value.lower() if value.lower() != 'none' else None
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
            if pause_match.group(1):
                duration = int(pause_match.group(1))
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
# FISH TTS API (Chunked)
# ============================================================================

def generate_tts_chunk(text, output_path, chunk_num=0):
    """Generate TTS for a single chunk."""
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
        "condition_on_previous_chunks": True,
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

    Returns output_path on success.
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
            # Write native WAV (keep stereo — HD mode quality)
            wav_path = output_path.replace('.mp3', '.wav')
            Path(wav_path).write_bytes(audio_bytes)
            # Convert WAV to MP3 (intermediate — concat will re-extract WAV)
            cmd = [
                'ffmpeg', '-y', '-i', wav_path,
                '-c:a', 'libmp3lame', '-b:a', '128k',
                output_path
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            os.remove(wav_path)
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
    """Clean up TTS audio - remove hiss, sibilance, and artifacts (Fish full chain).
    Output is WAV for lossless pipeline.
    """
    filter_chain = ','.join([
        'highpass=f=80',
        'equalizer=f=6000:t=q:w=2:g=-4',      # De-esser: notch at 6kHz
        'highshelf=f=7000:g=-2',               # De-esser: gentle shelf above 7kHz
        'lowpass=f=10000',
        'afftdn=nf=-25',
        'dynaudnorm=p=0.9:m=10'
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


def concatenate_with_silences(voice_chunks, silences, output_path, temp_dir, cleanup_mode='full'):
    """Concatenate voice chunks with silence gaps (lossless WAV pipeline).

    cleanup_mode: 'full' (Fish chain), 'light' (loudnorm only), 'none' (raw)

    Each voice chunk gets a 15ms fade-in/out applied before concatenation
    to prevent click artifacts at join boundaries.
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

        # Apply edge fades (WAV in, WAV out)
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

    if cleanup_mode == 'full':
        print("  Cleaning up audio (full Fish chain)...")
        cleanup_audio(concat_output, output_path)
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


def mix_ambient(voice_path, ambient_name, output_path):
    """Mix ambient background with voice (WAV output for lossless pipeline)."""
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

    fade_out_start = max(0, voice_duration - AMBIENT_FADE_OUT_DURATION)

    cmd = [
        'ffmpeg', '-y',
        '-i', voice_path,
        '-i', str(ambient_path),
        '-filter_complex', (
            f"[1:a]volume={AMBIENT_VOLUME_DB}dB,"
            f"afade=t=in:st={AMBIENT_FADE_IN_START}:d={AMBIENT_FADE_IN_DURATION},"
            f"afade=t=out:st={fade_out_start}:d={AMBIENT_FADE_OUT_DURATION}[amb];"
            f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2"
        ),
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


# ============================================================================
# AUTOMATED QA — SCAN, PATCH, VERIFY
# ============================================================================

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


def patch_stitch_clicks(raw_mp3, manifest_data, output_mp3, ambient_name=None, fade_ms=QA_FADE_MS, click_times=None):
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
            subprocess.run([
                'ffmpeg', '-y',
                '-i', normed_wav, '-i', str(ambient_path),
                '-filter_complex', (
                    f"[1:a]volume={AMBIENT_VOLUME_DB}dB,"
                    f"afade=t=in:st={AMBIENT_FADE_IN_START}:d={AMBIENT_FADE_IN_DURATION},"
                    f"afade=t=out:st={fade_out_start}:d={AMBIENT_FADE_OUT_DURATION}[amb];"
                    f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2"
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


def qa_loop(final_mp3, raw_mp3, manifest_data, ambient_name=None):
    """Scan → fix → rescan loop until audio passes QA.

    Returns True if audio is clean, False if max passes exceeded.
    """
    print(f"\n{'='*60}")
    print("  QA: AUTOMATED QUALITY ASSURANCE")
    print(f"{'='*60}")

    for qa_pass in range(1, QA_MAX_PASSES + 1):
        clicks = scan_for_clicks(final_mp3, manifest_data)

        if not clicks:
            print(f"  QA PASS {qa_pass}: CLEAN — 0 click artifacts")
            print(f"  QA: PASSED")
            return True

        print(f"  QA PASS {qa_pass}: FOUND {len(clicks)} click artifacts")
        for ts, jump, peak in clicks[:5]:  # Show first 5
            mins = int(ts // 60)
            secs = ts % 60
            print(f"    {mins}:{secs:05.2f} — jump={jump}, peak={peak}")
        if len(clicks) > 5:
            print(f"    ... and {len(clicks) - 5} more")

        click_timestamps = [ts for ts, jump, peak in clicks]
        print(f"  QA PASS {qa_pass}: Patching artifacts near stitch points...")
        patches = patch_stitch_clicks(raw_mp3, manifest_data, final_mp3, ambient_name, click_times=click_timestamps)
        print(f"  QA PASS {qa_pass}: Applied crossfades at {patches} stitch points")

    # Final check after last pass
    clicks = scan_for_clicks(final_mp3, manifest_data)
    if not clicks:
        print(f"  QA: PASSED (after {QA_MAX_PASSES} passes)")
        return True

    print(f"  QA: FAILED — {len(clicks)} clicks remain after {QA_MAX_PASSES} passes")
    print(f"  These may be ambient track artifacts (not fixable by stitch patching)")
    return False


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
    }).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SalusBuild/1.0"
        }
    )
    try:
        urllib.request.urlopen(req)
        print(f"  EMAIL: Sent to scottripley@icloud.com")
    except Exception as e:
        print(f"  EMAIL: Failed — {e}")


# ============================================================================
# MAIN BUILD
# ============================================================================

def build_session(session_name, dry_run=False, provider='fish', voice_id=None, model='v2',
                   cleanup_mode='full', no_deploy=False):
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

    print(f"  Title: {metadata['title']}")
    print(f"  Category: {category}")
    print(f"  Ambient: {ambient or 'none'}")
    print(f"  Provider: {provider}")
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
        combined_blocks = blocks

    # Humanize pauses
    if provider in ('elevenlabs', 'resemble'):
        combined_blocks = humanize_pauses(combined_blocks)
        humanized_silence = sum(pause for _, pause in combined_blocks)
        print(f"  Humanized silence: {humanized_silence/60:.1f} min")

    if dry_run:
        print(f"\n  DRY RUN - would generate {len(combined_blocks)} voice blocks")
        if provider == 'elevenlabs':
            for i, (text, pause) in enumerate(combined_blocks):
                print(f"    Block {i+1}: {len(text)} chars, {pause}s pause")
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
        current_time = 0.0

        print(f"\n  Generating TTS chunks ({provider})...")

        for i, (text, pause) in enumerate(combined_blocks):
            if provider == 'resemble':
                block_path = os.path.join(temp_dir, f"block_{i}.mp3")
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
                if len(text) > CHUNK_SIZE:
                    chunks = chunk_text_at_sentences(text)
                    chunk_files = []
                    for j, chunk in enumerate(chunks):
                        chunk_path = os.path.join(temp_dir, f"block_{i}_chunk_{j}.mp3")
                        generate_tts_chunk(chunk, chunk_path, len(voice_files) + j)
                        chunk_files.append(chunk_path)
                    block_path = os.path.join(temp_dir, f"block_{i}.mp3")
                    crossfade_audio_files(chunk_files, block_path)
                else:
                    block_path = os.path.join(temp_dir, f"block_{i}.mp3")
                    generate_tts_chunk(text, block_path, len(voice_files))

            # Build manifest
            duration = get_audio_duration(block_path)
            expected = len(text) / 15.0  # ~15 chars/sec estimate
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

        # ================================================================
        # PHASE 2: CONCATENATE + MIX (lossless WAV pipeline)
        # ================================================================
        print(f"\n  Concatenating {len(voice_files)} blocks with silences (lossless WAV)...")
        voice_path = os.path.join(temp_dir, "voice_complete.wav")
        concatenate_with_silences(voice_files, silences, voice_path, temp_dir, cleanup_mode=cleanup_mode)

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
        }
        with open(str(manifest_path), 'w') as f:
            json.dump(manifest_data, f, indent=2)
        print(f"  Manifest saved: {manifest_path}")

        # Mix ambient (WAV output)
        mixed_wav = os.path.join(temp_dir, "mixed_complete.wav")
        if ambient:
            print(f"\n  Mixing ambient '{ambient}'...")
            mix_ambient(voice_path, ambient, mixed_wav)
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
    qa_passed = qa_loop(str(final_path), raw_for_qa, manifest_data, ambient)

    if qa_passed:
        # Update mixed copy after QA patching
        shutil.copy(str(final_path), str(mixed_path))
    else:
        print(f"\n  WARNING: QA did not fully pass — review manually")
        print(f"  Remaining artifacts may be from ambient track (not narration)")

    # ================================================================
    # PHASE 4: DEPLOY TO R2
    # ================================================================
    if not no_deploy:
        r2_key = f"{R2_PATH_PREFIX}/{session_name}.mp3"
        deployed = deploy_to_r2(str(final_path), r2_key)
        if deployed:
            print(f"\n  LIVE: https://media.salus-mind.com/{r2_key}")
        else:
            print(f"\n  DEPLOY FAILED — file saved locally at {final_path}")
    else:
        print(f"\n  Deploy skipped (--no-deploy)")

    # ================================================================
    # DONE
    # ================================================================
    print(f"\n{'='*60}")
    status = "SHIPPED" if not no_deploy else "BUILT (not deployed)"
    print(f"  {status}: {session_name}")
    print(f"  Duration: {final_duration/60:.1f} min")
    print(f"  QA: {'PASSED' if qa_passed else 'REVIEW NEEDED'}")
    print(f"{'='*60}")

    # Email notification
    if not no_deploy:
        r2_url = f"https://media.salus-mind.com/{R2_PATH_PREFIX}/{session_name}.mp3"
        send_build_email(session_name, final_duration / 60, qa_passed, r2_url)

    return True


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
    parser.add_argument('--cleanup', choices=['full', 'medium', 'light', 'none'], default=None,
                        help='Override cleanup mode (default: full for fish, light for elevenlabs/resemble)')
    parser.add_argument('--no-deploy', action='store_true',
                        help='Build and QA only — do not upload to R2')

    args = parser.parse_args()

    # Determine cleanup mode
    if args.cleanup:
        cleanup_mode = args.cleanup
    elif args.no_cleanup:
        cleanup_mode = 'none'
    elif args.provider == 'elevenlabs':
        cleanup_mode = 'light'
    elif args.provider == 'resemble':
        cleanup_mode = 'light'
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
        )
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
