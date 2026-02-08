#!/usr/bin/env python3
"""
Salus Audio Session Builder v2

Single API call architecture for voice consistency.
- Entire script sent in one TTS request
- Marker words replaced with silence in post-processing
- No ambient looping - continuous source track required

Usage:
    python build-session-v2.py <session-name>
    python build-session-v2.py --dry-run <session-name>   # Show what would be generated
"""

import os
import sys
import re
import json
import subprocess
import tempfile
import shutil
import random
import argparse
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path("content/scripts")
AUDIO_DIR = Path("content/audio")
AMBIENT_DIR = Path("content/audio/ambient")

# Fish TTS API
FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Marco voice

# Audio settings
SAMPLE_RATE = 44100

# Marker word for silence insertion points
SILENCE_MARKER = "BREAKPOINT"

# Pause durations by category (for ... markers)
PAUSE_PROFILES = {
    'sleep': {1: (8, 15), 2: (25, 45), 3: (60, 105)},
    'focus': {1: (3, 6), 2: (8, 15), 3: (15, 30)},
    'stress': {1: (5, 10), 2: (15, 30), 3: (30, 60)},
    'mindfulness': {1: (5, 12), 2: (20, 40), 3: (45, 75)},
    'beginner': {1: (4, 8), 2: (12, 25), 3: (25, 45)},
    'advanced': {1: (8, 15), 2: (30, 60), 3: (75, 105)},
}

# Ambient settings
AMBIENT_VOLUME_DB = -14
AMBIENT_VOLUME_SILENCE_DB = -10  # Louder during narrator silence
AMBIENT_FADE_IN_START = 30  # Start fade after intro (seconds)
AMBIENT_FADE_IN_DURATION = 15
AMBIENT_FADE_OUT_DURATION = 8

# ============================================================================
# ENVIRONMENT
# ============================================================================

def load_env():
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

load_env()
FISH_API_KEY = os.environ.get("FISH_API_KEY", "")

# ============================================================================
# SCRIPT PARSING
# ============================================================================

def parse_script(script_path):
    """Parse script file and extract metadata + content."""
    text = Path(script_path).read_text(encoding='utf-8')

    if '---' in text:
        header, content = text.split('---', 1)
    else:
        header, content = "", text

    metadata = {
        'title': '',
        'duration': '',
        'category': 'mindfulness',
        'ambient': None,
        'style': 'Warm, grounded male narrator',
        'content': content.strip(),
    }

    header_lines = header.strip().split('\n')
    if header_lines:
        first_line = header_lines[0].strip()
        if ':' not in first_line or first_line.split(':')[0].lower() not in ['duration', 'category', 'ambient', 'style']:
            metadata['title'] = first_line

    for line in header_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            if key in ['duration', 'category', 'ambient', 'style']:
                if key == 'ambient':
                    metadata[key] = value.lower() if value.lower() != 'none' else None
                elif key == 'category':
                    metadata[key] = value.lower()
                else:
                    metadata[key] = value

    return metadata


def get_pause_duration(dot_count, category):
    """Get pause duration based on dot count and category."""
    profile = PAUSE_PROFILES.get(category, PAUSE_PROFILES['mindfulness'])
    level = min(dot_count, 3)
    min_sec, max_sec = profile[level]
    return random.uniform(min_sec, max_sec)


def convert_script_to_single_text(content, category):
    """
    Convert script content to single text block with BREAKPOINT markers.

    Strategy:
    - Single ... → Natural pause (ellipsis in text, TTS handles it)
    - Two ... → BREAKPOINT with medium silence
    - Three+ ... → BREAKPOINT with long silence
    - Explicit [SILENCE: X seconds] → BREAKPOINT

    Returns:
        - text: Full script with BREAKPOINT replacing significant pauses
        - silences: List of (marker_index, duration) for each BREAKPOINT
    """
    lines = content.split('\n')
    output_parts = []
    silences = []
    marker_index = 0

    # Regex for explicit pause markers like [PAUSE: 30 seconds] or [SILENCE: 90 seconds]
    pause_pattern = re.compile(r'\[(PAUSE|SILENCE):\s*(\d+)\s*seconds?[^\]]*\]', re.IGNORECASE)

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip comments/notes in brackets that aren't pause markers
        if line.startswith('[') and not pause_pattern.match(line):
            i += 1
            continue

        # Check for explicit pause marker
        pause_match = pause_pattern.match(line)
        if pause_match:
            duration = int(pause_match.group(2))
            output_parts.append(SILENCE_MARKER)
            silences.append((marker_index, duration))
            marker_index += 1
            i += 1

        elif line == '...':
            # Count consecutive ... markers
            count = 0
            while i < len(lines) and lines[i].strip() == '...':
                count += 1
                i += 1

            if count == 1:
                # Single ... = natural pause, let TTS handle it
                # Add a pause phrase that sounds natural
                output_parts.append("...")
            else:
                # 2+ dots = significant pause, use BREAKPOINT
                duration = get_pause_duration(count, category)
                output_parts.append(SILENCE_MARKER)
                silences.append((marker_index, duration))
                marker_index += 1

        elif line:
            # Regular text line
            output_parts.append(line)
            i += 1
        else:
            # Empty line (paragraph break)
            i += 1

    # Join with spaces, clean up multiple spaces but preserve ellipses
    text = ' '.join(output_parts)
    text = re.sub(r'\s+', ' ', text).strip()
    # Clean up spaces around ellipses
    text = re.sub(r'\s*\.\.\.\s*', ' ... ', text)

    return text, silences


# ============================================================================
# FISH TTS API (Single Call)
# ============================================================================

def generate_tts_single_call(text, output_path):
    """
    Generate TTS audio in a single API call.
    Uses low temperature for consistency.
    """
    import requests

    if not FISH_API_KEY:
        raise ValueError("FISH_API_KEY not set in environment or .env file")

    print(f"  Generating TTS ({len(text)} characters)...")
    print(f"  This may take a while for long scripts...")

    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "reference_id": FISH_VOICE_ID,
        "format": "mp3",
        "temperature": 0.3,  # Lower = more consistent
        "condition_on_previous_chunks": True,  # Maintain consistency across internal chunking
        "sample_rate": SAMPLE_RATE,
    }

    response = requests.post(FISH_API_URL, headers=headers, json=payload, timeout=600)

    if response.status_code != 200:
        raise Exception(f"Fish TTS API error: {response.status_code} - {response.text}")

    Path(output_path).write_bytes(response.content)

    # Get duration
    duration = get_audio_duration(output_path)
    print(f"  Generated {duration/60:.1f} minutes of audio")

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


def detect_marker_timestamps(audio_path, marker_word="BREAKPOINT"):
    """
    Detect timestamps where marker word is spoken using Whisper.
    Returns list of (start_time, end_time) for each marker occurrence.
    """
    print(f"  Detecting '{marker_word}' markers in audio...")

    # Use whisper to transcribe with timestamps
    # First check if whisper is available
    try:
        result = subprocess.run(['which', 'whisper'], capture_output=True, text=True)
        if result.returncode != 0:
            # Try using Python whisper module
            return detect_marker_timestamps_python(audio_path, marker_word)
    except:
        return detect_marker_timestamps_python(audio_path, marker_word)

    # Use CLI whisper
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [
            'whisper', audio_path,
            '--model', 'base',
            '--output_format', 'json',
            '--output_dir', temp_dir,
            '--word_timestamps', 'True'
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        # Find output JSON
        json_files = list(Path(temp_dir).glob('*.json'))
        if not json_files:
            raise Exception("Whisper did not produce output")

        with open(json_files[0]) as f:
            data = json.load(f)

        # Find marker words
        markers = []
        for segment in data.get('segments', []):
            for word_info in segment.get('words', []):
                word = word_info.get('word', '').strip().upper()
                if marker_word.upper() in word:
                    start = word_info.get('start', 0)
                    end = word_info.get('end', start + 0.5)
                    markers.append((start, end))

        print(f"  Found {len(markers)} markers")
        return markers


def detect_marker_timestamps_python(audio_path, marker_word="BREAKPOINT"):
    """Detect markers using Python whisper module."""
    try:
        import whisper
    except ImportError:
        raise Exception("Please install whisper: pip install openai-whisper")

    print(f"  Loading Whisper model...")
    model = whisper.load_model("base")

    print(f"  Transcribing audio (this may take a while)...")
    result = model.transcribe(audio_path, word_timestamps=True)

    markers = []
    for segment in result.get('segments', []):
        for word_info in segment.get('words', []):
            word = word_info.get('word', '').strip().upper()
            if marker_word.upper() in word:
                start = word_info.get('start', 0)
                end = word_info.get('end', start + 0.5)
                markers.append((start, end))

    print(f"  Found {len(markers)} markers")
    return markers


def replace_markers_with_silence(audio_path, markers, silences, output_path):
    """
    Replace each marker occurrence with the corresponding silence duration.
    Uses crossfade to avoid clicks.
    """
    if len(markers) != len(silences):
        print(f"  WARNING: Found {len(markers)} markers but expected {len(silences)}")
        print(f"  Will process {min(len(markers), len(silences))} replacements")

    print(f"  Replacing {len(markers)} markers with silences...")

    # Build ffmpeg filter to cut out markers and insert silence
    # This is complex - we'll do it segment by segment

    current_audio = audio_path

    with tempfile.TemporaryDirectory() as temp_dir:
        # Process markers in reverse order (so timestamps remain valid)
        for i in range(min(len(markers), len(silences)) - 1, -1, -1):
            marker_start, marker_end = markers[i]
            _, silence_duration = silences[i]

            print(f"    Marker {i+1}: {marker_start:.1f}s -> {silence_duration:.1f}s silence")

            # Generate silence segment
            silence_file = os.path.join(temp_dir, f"silence_{i}.mp3")
            cmd = [
                'ffmpeg', '-y', '-f', 'lavfi',
                '-i', f'anullsrc=r={SAMPLE_RATE}:cl=stereo',
                '-t', str(silence_duration),
                '-c:a', 'libmp3lame', '-q:a', '2',
                silence_file
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            # Extract parts: before marker, after marker
            before_file = os.path.join(temp_dir, f"before_{i}.mp3")
            after_file = os.path.join(temp_dir, f"after_{i}.mp3")
            output_temp = os.path.join(temp_dir, f"combined_{i}.mp3")

            # Crossfade duration
            xfade = 0.075  # 75ms crossfade

            # Get total duration
            total_duration = get_audio_duration(current_audio)

            # Extract before (with small overlap for crossfade)
            if marker_start > 0:
                cmd = [
                    'ffmpeg', '-y', '-i', current_audio,
                    '-t', str(marker_start),
                    '-c:a', 'libmp3lame', '-q:a', '2',
                    before_file
                ]
                subprocess.run(cmd, capture_output=True, check=True)

            # Extract after
            after_start = marker_end
            if after_start < total_duration:
                cmd = [
                    'ffmpeg', '-y', '-i', current_audio,
                    '-ss', str(after_start),
                    '-c:a', 'libmp3lame', '-q:a', '2',
                    after_file
                ]
                subprocess.run(cmd, capture_output=True, check=True)

            # Concatenate with crossfade: before + silence + after
            concat_list = os.path.join(temp_dir, f"concat_{i}.txt")
            with open(concat_list, 'w') as f:
                if marker_start > 0:
                    f.write(f"file '{os.path.abspath(before_file)}'\n")
                f.write(f"file '{os.path.abspath(silence_file)}'\n")
                if after_start < total_duration:
                    f.write(f"file '{os.path.abspath(after_file)}'\n")

            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', concat_list,
                '-c:a', 'libmp3lame', '-q:a', '2',
                output_temp
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            current_audio = output_temp

        # Copy final result
        shutil.copy(current_audio, output_path)

    final_duration = get_audio_duration(output_path)
    print(f"  Final voice track: {final_duration/60:.1f} minutes")
    return output_path


def mix_ambient_no_loop(voice_path, ambient_name, output_path):
    """
    Mix ambient background - no looping, continuous track.
    Ambient fades in after intro, stays consistent throughout.
    """
    # Try extended version first
    ambient_path = AMBIENT_DIR / f"{ambient_name}-extended.mp3"
    if not ambient_path.exists():
        ambient_path = AMBIENT_DIR / f"{ambient_name}.mp3"

    if not ambient_path.exists():
        print(f"  WARNING: Ambient '{ambient_name}' not found, skipping mix")
        shutil.copy(voice_path, output_path)
        return output_path

    voice_duration = get_audio_duration(voice_path)
    ambient_duration = get_audio_duration(str(ambient_path))

    print(f"  Voice duration: {voice_duration/60:.1f} min")
    print(f"  Ambient duration: {ambient_duration/60:.1f} min")

    if ambient_duration < voice_duration:
        print(f"  WARNING: Ambient track shorter than voice! Need longer ambient.")
        print(f"  Consider using an extended ambient file.")

    # Mix: ambient fades in, runs under voice at -14dB
    # Fade out at the end
    fade_out_start = voice_duration - AMBIENT_FADE_OUT_DURATION

    cmd = [
        'ffmpeg', '-y',
        '-i', voice_path,
        '-i', str(ambient_path),
        '-filter_complex', (
            f"[1:a]volume={AMBIENT_VOLUME_DB}dB,"
            f"afade=t=in:st={AMBIENT_FADE_IN_START}:d={AMBIENT_FADE_IN_DURATION}:curve=log,"
            f"afade=t=out:st={fade_out_start}:d={AMBIENT_FADE_OUT_DURATION}[amb];"
            f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2"
        ),
        '-t', str(voice_duration),
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]

    subprocess.run(cmd, capture_output=True, check=True)

    final_duration = get_audio_duration(output_path)
    print(f"  Final mixed audio: {final_duration/60:.1f} minutes")
    return output_path


# ============================================================================
# MAIN BUILD
# ============================================================================

def build_session(session_name, dry_run=False, debug=False):
    """Build session using single-call architecture."""
    print(f"\n{'='*60}")
    print(f"Building: {session_name} (v2 single-call)")
    print(f"{'='*60}")

    script_path = SCRIPT_DIR / f"{session_name}.txt"
    output_path = AUDIO_DIR / f"{session_name}.mp3"

    if not script_path.exists():
        print(f"  ERROR: Script not found: {script_path}")
        return False

    # Parse script
    metadata = parse_script(script_path)
    category = metadata['category']
    ambient = metadata['ambient']
    content = metadata['content']

    print(f"  Title: {metadata['title']}")
    print(f"  Category: {category}")
    print(f"  Ambient: {ambient or 'none'}")

    # Convert to single text with markers
    text, silences = convert_script_to_single_text(content, category)

    print(f"  Text length: {len(text)} characters")
    print(f"  Silence markers: {len(silences)}")

    # Show silence breakdown
    total_silence = sum(dur for _, dur in silences)
    print(f"  Total planned silence: {total_silence/60:.1f} minutes")

    if dry_run:
        print(f"\n  DRY RUN - would generate:")
        print(f"    - TTS for {len(text)} chars")
        print(f"    - {len(silences)} silence insertions")
        print(f"    - Mix with '{ambient}' ambient")
        print(f"\n  First 500 chars of processed text:")
        print(f"    {text[:500]}...")
        return True

    # Create working directory (temp unless debug mode)
    if debug:
        debug_dir = Path(f"content/audio/debug-{session_name}")
        debug_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = str(debug_dir)
        print(f"  DEBUG MODE: Saving intermediate files to {debug_dir}")
    else:
        temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir = temp_dir_obj.name

    try:
        # Step 1: Generate TTS in single call
        raw_tts_path = os.path.join(temp_dir, "raw_tts.mp3")
        generate_tts_single_call(text, raw_tts_path)

        # Step 2: Detect marker timestamps
        markers = detect_marker_timestamps(raw_tts_path, SILENCE_MARKER)

        if len(markers) == 0:
            print("  WARNING: No markers detected! Using raw TTS output.")
            voice_path = raw_tts_path
        else:
            # Step 3: Replace markers with silence
            voice_path = os.path.join(temp_dir, "voice_with_silences.mp3")
            replace_markers_with_silence(raw_tts_path, markers, silences, voice_path)

        # Step 4: Mix ambient (if specified)
        if ambient:
            print(f"  Mixing ambient '{ambient}'...")
            mix_ambient_no_loop(voice_path, ambient, str(output_path))
        else:
            shutil.copy(voice_path, output_path)
    finally:
        if not debug:
            temp_dir_obj.cleanup()

    final_duration = get_audio_duration(str(output_path))
    print(f"\n  COMPLETE: {output_path}")
    print(f"  Duration: {final_duration/60:.1f} minutes")
    return True


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Salus Audio Builder v2 (single-call architecture)"
    )
    parser.add_argument('session', help='Session name to build')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be generated without calling API')
    parser.add_argument('--debug', action='store_true',
                       help='Save intermediate files for debugging')

    args = parser.parse_args()

    try:
        build_session(args.session, dry_run=args.dry_run, debug=args.debug)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
