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
AUDIO_DIR = Path("content/audio")
AMBIENT_DIR = Path("content/audio/ambient")

# Fish TTS API
FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Marco voice
FISH_API_KEY = os.getenv("FISH_API_KEY")

# Audio settings
SAMPLE_RATE = 44100
MAX_DURATION_SECONDS = 30 * 60  # 30 minutes max

# Chunking settings
CHUNK_SIZE = 8000  # chars per chunk
MIN_BLOCK_SIZE = 500  # combine small blocks until this size
CROSSFADE_MS = 150  # crossfade duration between chunks

# Pause durations by category (seconds)
PAUSE_PROFILES = {
    'sleep': {1: 8, 2: 30, 3: 60},
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
            # Count consecutive ... lines
            count = 0
            while i < len(lines) and re.match(r'^\s*\.{2,}\s*$', lines[i].strip()):
                count += 1
                i += 1

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
    """Clean up TTS audio - remove hiss, sibilance, and artifacts."""
    # Audio cleanup filter chain:
    # - highpass at 80Hz (cuts low rumble)
    # - De-esser: notch filter at 6kHz to reduce sibilance ('s' sounds)
    # - De-esser: shelf reduction above 7kHz for harsh consonants
    # - lowpass at 10000Hz (cuts high-freq hiss)
    # - afftdn with stronger noise reduction (-25dB floor)
    # - dynaudnorm for consistent levels
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


def concatenate_with_silences(voice_chunks, silences, output_path, temp_dir):
    """Concatenate voice chunks with silence gaps."""
    all_files = []

    for i, (voice_file, silence_duration) in enumerate(zip(voice_chunks, silences)):
        all_files.append(voice_file)
        if silence_duration > 0:
            silence_file = os.path.join(temp_dir, f"silence_{i}.mp3")
            generate_silence(silence_duration, silence_file)
            all_files.append(silence_file)

    # Use concat demuxer for clean joins
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

    # Clean up audio (remove hiss)
    print("  Cleaning up audio (removing hiss)...")
    cleanup_audio(concat_output, output_path)
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

def build_session(session_name, dry_run=False):
    """Build a complete session."""
    script_path = SCRIPT_DIR / f"{session_name}.txt"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    output_path = AUDIO_DIR / f"{session_name}.mp3"

    print("=" * 60)
    print(f"Building: {session_name} (v3 chunked)")
    print("=" * 60)

    metadata = parse_script(script_path)
    category = metadata['category']
    ambient = metadata['ambient']

    print(f"  Title: {metadata['title']}")
    print(f"  Category: {category}")
    print(f"  Ambient: {ambient or 'none'}")

    # Process script into blocks with pauses
    blocks = process_script_for_tts(metadata['content'], category)

    total_text = ' '.join(text for text, _ in blocks)
    total_silence = sum(pause for _, pause in blocks)

    print(f"  Text blocks: {len(blocks)}")
    print(f"  Total chars: {len(total_text)}")
    print(f"  Est. narration: {len(total_text)/1000*1.2:.1f} min")
    print(f"  Total silence: {total_silence/60:.1f} min")
    print(f"  Est. total: {len(total_text)/1000*1.2 + total_silence/60:.1f} min")

    if dry_run:
        print(f"\n  DRY RUN - would generate {len(blocks)} voice blocks")
        return True

    with tempfile.TemporaryDirectory() as temp_dir:
        # DON'T combine blocks - preserve all pauses for natural rhythm
        # Each block with its pause goes separately to maintain meditation pacing
        combined_blocks = blocks

        print(f"  Processing {len(combined_blocks)} blocks (preserving all pauses)")

        voice_files = []
        silences = []

        print(f"\n  Generating TTS chunks...")

        for i, (text, pause) in enumerate(combined_blocks):
            # Split large blocks into chunks
            if len(text) > CHUNK_SIZE:
                chunks = chunk_text_at_sentences(text)
                chunk_files = []
                for j, chunk in enumerate(chunks):
                    chunk_path = os.path.join(temp_dir, f"block_{i}_chunk_{j}.mp3")
                    generate_tts_chunk(chunk, chunk_path, len(voice_files) + j)
                    chunk_files.append(chunk_path)

                # Crossfade chunks together
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
        concatenate_with_silences(voice_files, silences, voice_path, temp_dir)

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

    args = parser.parse_args()

    try:
        build_session(args.session, dry_run=args.dry_run)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
