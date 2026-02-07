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
RESEMBLE_VOICE_ID = "9f1fb457"  # Amanda — most expressive voice design
RESEMBLE_CHUNK_MAX = 2500  # Stay under 3000 char API limit
RESEMBLE_DELAY_MS = 500  # Rate limiting between API calls

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
AMBIENT_VOLUME_DB = -12          # Louder ambient for rain sessions
AMBIENT_VOLUME_SILENCE_DB = -13  # Raise 1dB during 30s+ gaps (per spec)
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

def merge_blocks_for_resemble(blocks):
    """Merge adjacent blocks into chunks under RESEMBLE_CHUNK_MAX chars.

    SSML <break> tags are inserted between merged paragraphs to preserve pacing.
    Blocks separated by long pauses (>= 10s) are NOT merged — those gaps stay
    as separate silence files for precise control.
    """
    merged = []
    current_texts = []
    current_chars = 0
    current_pause = 0

    for text, pause in blocks:
        # Don't merge across structural pauses (>= 10s)
        if current_texts and (pause >= 10 or current_chars + len(text) + 50 > RESEMBLE_CHUNK_MAX):
            # Flush current chunk
            merged_text = _join_with_ssml_breaks(current_texts)
            merged.append((merged_text, current_pause))
            current_texts = [text]
            current_chars = len(text)
            current_pause = pause
        else:
            current_texts.append(text)
            current_chars += len(text) + 50  # Account for SSML break tags
            current_pause = pause

    if current_texts:
        merged_text = _join_with_ssml_breaks(current_texts)
        merged.append((merged_text, current_pause))

    return merged


def _join_with_ssml_breaks(texts):
    """Join multiple text blocks with SSML break tags between them."""
    if len(texts) == 1:
        return texts[0]
    parts = []
    for i, text in enumerate(texts):
        parts.append(text)
        if i < len(texts) - 1:
            # Mostly 1-2s breaks, occasional 3s — no long silences for stories
            break_ms = random.choice([1000, 1500, 1500, 2000, 2000, 2500, 3000])
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
    }

    print(f"    Chunk {chunk_num + 1}: {len(text)} chars...", end=" ", flush=True)

    # Retry logic for transient errors
    for attempt in range(3):
        response = requests.post(RESEMBLE_SYNTH_URL, json=payload, headers=headers, timeout=120)
        data = response.json()

        if data.get("success"):
            audio_bytes = base64.b64decode(data["audio_content"])
            # Write as WAV, then convert to MP3 for pipeline compatibility
            wav_path = output_path.replace('.mp3', '.wav')
            Path(wav_path).write_bytes(audio_bytes)
            # Convert WAV to MP3
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


def generate_silence(duration, output_path):
    """Generate silence audio file."""
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'anullsrc=r={SAMPLE_RATE}:cl=stereo',
        '-t', str(duration),
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def cleanup_audio(input_path, output_path):
    """Clean up TTS audio - remove hiss, sibilance, and artifacts (Fish full chain)."""
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
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def cleanup_audio_light(input_path, output_path):
    """Light cleanup for ElevenLabs — loudness normalization only.

    Speed is handled natively by the API (speed: 0.75 in voice_settings).
    No atempo post-processing — it degrades audio quality.
    """
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-af', 'loudnorm=I=-24:TP=-2:LRA=11',
        '-c:a', 'libmp3lame', '-b:a', '128k',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def apply_edge_fades(audio_path, output_path, fade_ms=15):
    """Apply brief fade-in at start and fade-out at end of an audio file.

    Prevents click artifacts when files are concatenated with the concat demuxer.
    15ms cosine fades are inaudible but eliminate sample-level discontinuities.
    """
    fade_sec = fade_ms / 1000
    duration = get_audio_duration(audio_path)
    fade_out_start = max(0, duration - fade_sec)
    cmd = [
        'ffmpeg', '-y', '-i', audio_path,
        '-af', f'afade=t=in:st=0:d={fade_sec}:curve=hsin,afade=t=out:st={fade_out_start}:d={fade_sec}:curve=hsin',
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def concatenate_with_silences(voice_chunks, silences, output_path, temp_dir, cleanup_mode='full'):
    """Concatenate voice chunks with silence gaps.

    cleanup_mode: 'full' (Fish chain), 'light' (loudnorm only), 'none' (raw)

    Each voice chunk gets a 15ms fade-in/out applied before concatenation
    to prevent click artifacts at join boundaries.
    """
    all_files = []

    for i, (voice_file, silence_duration) in enumerate(zip(voice_chunks, silences)):
        # Apply edge fades to voice chunk to prevent clicks at concat boundaries
        faded_file = os.path.join(temp_dir, f"faded_{i}.mp3")
        apply_edge_fades(voice_file, faded_file)
        all_files.append(faded_file)
        if silence_duration > 0:
            silence_file = os.path.join(temp_dir, f"silence_{i}.mp3")
            generate_silence(silence_duration, silence_file)
            all_files.append(silence_file)

    # Use concat demuxer — now safe because edges are faded
    concat_list = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_list, 'w') as f:
        for file in all_files:
            f.write(f"file '{file}'\n")

    # Concatenate
    concat_output = os.path.join(temp_dir, "concat_raw.mp3")
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_list,
        '-c:a', 'libmp3lame', '-q:a', '2',
        concat_output
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    if cleanup_mode == 'full':
        print("  Cleaning up audio (full Fish chain)...")
        cleanup_audio(concat_output, output_path)
    elif cleanup_mode == 'light':
        print("  Cleaning up audio (loudnorm only)...")
        cleanup_audio_light(concat_output, output_path)
    else:
        print("  No audio cleanup (raw).")
        shutil.copy(concat_output, output_path)
    return output_path


def mix_ambient(voice_path, ambient_name, output_path):
    """Mix ambient background with voice."""
    # Try extended version first, then 8hr version, then regular
    for suffix in ['-8hr', '-extended', '']:
        ambient_path = AMBIENT_DIR / f"{ambient_name}{suffix}.mp3"
        if ambient_path.exists():
            break

    if not ambient_path.exists():
        print(f"  WARNING: Ambient '{ambient_name}' not found, skipping mix")
        shutil.copy(voice_path, output_path)
        return output_path

    voice_duration = get_audio_duration(voice_path)
    ambient_duration = get_audio_duration(str(ambient_path))

    print(f"  Voice: {voice_duration/60:.1f} min, Ambient: {ambient_duration/60:.1f} min")

    if ambient_duration < voice_duration:
        print(f"  WARNING: Ambient shorter than voice!")

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
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


# ============================================================================
# MAIN BUILD
# ============================================================================

def build_session(session_name, dry_run=False, provider='fish', voice_id=None, model='v2', cleanup_mode='full'):
    """Build a complete session.

    provider: 'fish', 'elevenlabs', or 'resemble'
    voice_id: override voice ID (or None for default)
    model: ElevenLabs model key ('v2'/'v3', ignored for Fish/Resemble)
    cleanup_mode: 'full', 'light', or 'none'
    """
    script_path = SCRIPT_DIR / f"{session_name}.txt"
    if not script_path.exists():
        script_path = SLEEP_STORY_DIR / f"{session_name}.txt"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found in content/scripts/ or content/sleep-stories/")

    output_path = AUDIO_DIR / f"{session_name}.mp3"

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
        # ElevenLabs: merge only tiny blocks (<20 chars), send paragraphs individually
        combined_blocks = merge_short_blocks(blocks)
        if len(combined_blocks) != len(blocks):
            print(f"  After merging short blocks: {len(combined_blocks)} (from {len(blocks)} raw)")
    elif provider == 'resemble':
        # Resemble: merge blocks into chunks under 2500 chars with SSML breaks
        combined_blocks = merge_blocks_for_resemble(blocks)
        print(f"  Resemble chunks: {len(combined_blocks)} (from {len(blocks)} raw)")
    else:
        combined_blocks = blocks

    # Humanize pauses (natural variation instead of robotic equal gaps)
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

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"  Processing {len(combined_blocks)} blocks")

        voice_files = []
        silences = []
        request_ids = []  # Rolling list for ElevenLabs request stitching

        print(f"\n  Generating TTS chunks ({provider})...")

        for i, (text, pause) in enumerate(combined_blocks):
            if provider == 'resemble':
                # Resemble: merged chunks with SSML breaks baked in
                block_path = os.path.join(temp_dir, f"block_{i}.mp3")
                generate_tts_chunk_resemble(
                    text, block_path, i,
                    voice_id=voice_id,
                )
            elif provider == 'elevenlabs':
                # ElevenLabs: one paragraph per API call with request stitching
                block_path = os.path.join(temp_dir, f"block_{i}.mp3")
                _, req_id = generate_tts_chunk_elevenlabs(
                    text, block_path, i,
                    voice_id=voice_id, model=model,
                    previous_request_ids=request_ids,
                )
                if req_id:
                    request_ids.append(req_id)
                    # Keep only last 3 for stitching
                    if len(request_ids) > 3:
                        request_ids = request_ids[-3:]
            else:
                # Fish: original chunking logic
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

            voice_files.append(block_path)
            silences.append(pause)

        # Concatenate all blocks with silences
        print(f"\n  Concatenating {len(voice_files)} blocks with silences...")
        voice_path = os.path.join(temp_dir, "voice_complete.mp3")
        concatenate_with_silences(voice_files, silences, voice_path, temp_dir, cleanup_mode=cleanup_mode)

        voice_duration = get_audio_duration(voice_path)
        print(f"  Voice track: {voice_duration/60:.1f} min")

        if voice_duration > MAX_DURATION_SECONDS:
            print(f"  WARNING: Exceeds 30 min limit!")

        # Save raw narration (no ambient) for quality analysis
        raw_output = AUDIO_DIR / f"{session_name}-raw.mp3"
        shutil.copy(voice_path, str(raw_output))
        print(f"  Raw narration saved: {raw_output}")

        # Mix ambient
        if ambient:
            print(f"\n  Mixing ambient '{ambient}'...")
            mix_ambient(voice_path, ambient, str(output_path))
        else:
            shutil.copy(voice_path, str(output_path))

    final_duration = get_audio_duration(str(output_path))
    print(f"\n  COMPLETE: {output_path}")
    print(f"  Duration: {final_duration/60:.1f} min")

    if final_duration > MAX_DURATION_SECONDS:
        print(f"  ⚠️  EXCEEDS 30 MIN LIMIT")

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

    args = parser.parse_args()

    # Determine cleanup mode
    if args.no_cleanup:
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
        )
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
