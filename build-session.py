#!/usr/bin/env python3
"""
Salus Audio Session Builder

Builds meditation sessions from scripts with:
- Voice generation via Fish TTS API
- Category-based pause durations
- Ambient background mixing

Usage:
    python build-session.py <session-name>           # Build single session
    python build-session.py --all                    # Rebuild all sessions
    python build-session.py --list                   # List all sessions
    python build-session.py --mix-only <session>     # Only add ambient to existing audio

Examples:
    python build-session.py 08-sleep-stories-quiet-shore
    python build-session.py --all
    python build-session.py --mix-only 08-sleep-stories-quiet-shore
"""

import os
import sys
import re
import subprocess
import tempfile
import shutil
import random
import argparse
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Directories
SCRIPT_DIR = Path("content/scripts")
AUDIO_DIR = Path("content/audio")
AMBIENT_DIR = Path("content/audio/ambient")
BACKUP_DIR = Path("content/audio/backup")

# Fish TTS API
FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Marco voice

# Audio settings
SAMPLE_RATE = 44100
AMBIENT_VOLUME_DB = -15  # Ambient mixed at this level (matches AUDIO-SPEC.md)
AMBIENT_FADE_IN = 15     # Seconds (15s logarithmic fade per spec)
AMBIENT_FADE_OUT = 8     # Seconds

# Pause profiles: dots -> (min_seconds, max_seconds)
PAUSE_PROFILES = {
    'sleep': {
        1: (8, 15),
        2: (25, 45),
        3: (60, 105),
    },
    'focus': {
        1: (3, 6),
        2: (8, 15),
        3: (15, 30),
    },
    'stress': {
        1: (5, 10),
        2: (15, 30),
        3: (30, 60),
    },
    'mindfulness': {
        1: (5, 12),
        2: (20, 40),
        3: (45, 75),
    },
    'beginner': {
        1: (4, 8),
        2: (12, 25),
        3: (25, 45),
    },
    'advanced': {
        1: (8, 15),
        2: (30, 60),
        3: (75, 105),
    },
}

# Default category/ambient mappings (used if not specified in script)
DEFAULT_MAPPINGS = {
    "05-body-scan-deep-rest": ("sleep", "night"),
    "06-letting-go-of-the-day": ("sleep", "night"),
    "07-moonlight-drift": ("sleep", "night"),
    "08-sleep-stories-quiet-shore": ("sleep", "ocean"),
    "09-rainfall-sleep-journey": ("sleep", "rain"),
    "10-counting-down-to-sleep": ("sleep", "night"),
    "11-lucid-dream-preparation": ("sleep", "night"),
    "12-five-minute-reset": ("focus", "piano"),
    "13-flow-state": ("focus", "library"),
    "14-morning-clarity": ("focus", "birds"),
    "15-deep-work-prep": ("focus", "library"),
    "16-peak-performance": ("focus", "piano"),
    "17-deep-work-mode": ("focus", "library"),
    "18-calm-in-three-minutes": ("stress", "stream"),
    "19-release-and-restore": ("stress", "stream"),
    "20-tension-melt": ("stress", "rain"),
    "21-anxiety-unravelled": ("stress", "rain"),
    "22-releasing-tension": ("stress", "wind"),
    "23-the-calm-reset": ("stress", "stream"),
    "24-anger-frustration-release": ("stress", "waterfall"),
    "25-introduction-to-mindfulness": ("mindfulness", "temple"),
    "26-body-scan-meditation": ("mindfulness", "wind"),
    "27-mindful-breathing": ("mindfulness", "wind"),
    "28-letting-go-of-thoughts": ("mindfulness", "stream"),
    "29-open-awareness": ("mindfulness", "garden"),
    "30-mindful-walking": ("mindfulness", "forest"),
    "31-mindfulness-at-work": ("mindfulness", "library"),
    "32-observing-emotions": ("mindfulness", "stream"),
    "33-morning-mindfulness": ("mindfulness", "birds"),
    "34-mindful-eating": ("mindfulness", "garden"),
    "35-your-first-meditation": ("beginner", "wind"),
    "36-loving-kindness-intro": ("beginner", "chimes"),
    "37-building-a-daily-practice": ("beginner", "garden"),
    "38-seven-day-mindfulness-day1": ("beginner", None),
    "39-yoga-nidra": ("advanced", "temple"),
    "40-gratitude-before-sleep": ("sleep", "night"),
    "41-vipassana-insight": ("advanced", "temple"),
    "42-chakra-alignment": ("advanced", "chimes"),
    "43-non-dual-awareness": ("advanced", "wind"),
    "44-transcendental-stillness": ("advanced", "temple"),
    "45-seven-day-mindfulness-day2": ("mindfulness", None),
    "46-seven-day-mindfulness-day3": ("mindfulness", None),
    "47-seven-day-mindfulness-day4": ("mindfulness", None),
    "48-seven-day-mindfulness-day5": ("mindfulness", None),
    "49-seven-day-mindfulness-day6": ("mindfulness", None),
    "50-seven-day-mindfulness-day7": ("mindfulness", None),
}

# ============================================================================
# LOAD ENVIRONMENT
# ============================================================================

def load_env():
    """Load .env file into environment."""
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
    """
    Parse a script file and extract metadata + content.

    Returns dict with:
        - title: str
        - duration: str
        - category: str
        - ambient: str or None
        - style: str
        - content: str (everything after ---)
    """
    text = Path(script_path).read_text(encoding='utf-8')

    # Split header and content
    if '---' in text:
        header, content = text.split('---', 1)
    else:
        header = ""
        content = text

    # Parse header fields
    metadata = {
        'title': '',
        'duration': '',
        'category': 'mindfulness',
        'ambient': None,
        'style': 'Warm, grounded male narrator',
        'content': content.strip(),
    }

    # Extract title (first line of header)
    header_lines = header.strip().split('\n')
    if header_lines:
        first_line = header_lines[0].strip()
        if not ':' in first_line or first_line.split(':')[0].lower() not in ['duration', 'category', 'ambient', 'style']:
            metadata['title'] = first_line

    # Extract other fields
    for line in header_lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            if key == 'duration':
                metadata['duration'] = value
            elif key == 'category':
                metadata['category'] = value.lower()
            elif key == 'ambient':
                metadata['ambient'] = value.lower() if value.lower() != 'none' else None
            elif key == 'style':
                metadata['style'] = value

    return metadata

def get_session_config(session_name):
    """Get category and ambient for a session, checking script first, then defaults."""
    script_path = SCRIPT_DIR / f"{session_name}.txt"

    if script_path.exists():
        metadata = parse_script(script_path)
        category = metadata.get('category', 'mindfulness')
        ambient = metadata.get('ambient')

        # Fall back to defaults if not in script
        if session_name in DEFAULT_MAPPINGS:
            default_cat, default_amb = DEFAULT_MAPPINGS[session_name]
            if category == 'mindfulness' and metadata.get('category') is None:
                category = default_cat
            if ambient is None and metadata.get('ambient') is None:
                ambient = default_amb

        return category, ambient, metadata

    # No script, use defaults
    if session_name in DEFAULT_MAPPINGS:
        cat, amb = DEFAULT_MAPPINGS[session_name]
        return cat, amb, None

    return 'mindfulness', None, None

# ============================================================================
# PAUSE CALCULATION
# ============================================================================

def count_consecutive_pauses(lines, start_idx):
    """Count consecutive lines that are just '...'"""
    count = 0
    for i in range(start_idx, len(lines)):
        if lines[i].strip() == '...':
            count += 1
        else:
            break
    return max(1, count)

def get_pause_duration(dot_count, category):
    """Get pause duration in seconds based on dot count and category."""
    profile = PAUSE_PROFILES.get(category, PAUSE_PROFILES['mindfulness'])
    level = min(dot_count, 3)
    min_sec, max_sec = profile[level]
    return random.uniform(min_sec, max_sec)

def parse_script_segments(content, category):
    """
    Parse script content into segments of text and pauses.

    Returns list of:
        ('text', "spoken text here")
        ('pause', duration_in_seconds)

    Supports explicit pause markers:
        [PAUSE: 30 seconds] or [SILENCE: 90 seconds]
    """
    lines = content.split('\n')
    segments = []
    current_text = []
    i = 0

    # Regex for explicit pause markers like [PAUSE: 30 seconds] or [SILENCE: 60 seconds]
    pause_pattern = re.compile(r'\[(PAUSE|SILENCE):\s*(\d+)\s*seconds?\]', re.IGNORECASE)

    while i < len(lines):
        line = lines[i].strip()

        # Check for explicit pause marker
        pause_match = pause_pattern.match(line)
        if pause_match:
            # Save any accumulated text
            if current_text:
                text = ' '.join(current_text).strip()
                if text:
                    segments.append(('text', text))
                current_text = []

            # Get explicit duration
            duration = int(pause_match.group(2))
            segments.append(('pause', duration))
            print(f"    Found explicit {pause_match.group(1)}: {duration} seconds")
            i += 1

        elif line == '...':
            # Save any accumulated text
            if current_text:
                text = ' '.join(current_text).strip()
                if text:
                    segments.append(('text', text))
                current_text = []

            # Count consecutive pause markers
            pause_count = count_consecutive_pauses(lines, i)
            duration = get_pause_duration(pause_count, category)
            segments.append(('pause', duration))

            # Skip all the pause lines we counted
            i += pause_count
        elif line:
            current_text.append(line)
            i += 1
        else:
            # Empty line - paragraph break, add to current text
            if current_text:
                current_text.append('')
            i += 1

    # Don't forget remaining text
    if current_text:
        text = ' '.join(current_text).strip()
        if text:
            segments.append(('text', text))

    return segments

# ============================================================================
# FISH TTS API
# ============================================================================

def generate_tts(text, output_path):
    """Generate TTS audio using Fish API."""
    import requests

    if not FISH_API_KEY:
        raise ValueError("FISH_API_KEY not set in environment or .env file")

    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "reference_id": FISH_VOICE_ID,
        "format": "mp3",
    }

    response = requests.post(FISH_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Fish TTS API error: {response.status_code} - {response.text}")

    Path(output_path).write_bytes(response.content)
    return output_path

# ============================================================================
# AUDIO PROCESSING
# ============================================================================

def generate_silence(duration_seconds, output_path):
    """Generate a silent audio file."""
    cmd = [
        'ffmpeg', '-y', '-f', 'lavfi',
        '-i', f'anullsrc=r={SAMPLE_RATE}:cl=stereo',
        '-t', str(duration_seconds),
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path

def get_audio_duration(audio_path):
    """Get duration of an audio file in seconds."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def concatenate_audio(audio_files, output_path):
    """Concatenate multiple audio files."""
    # Create concat list file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for audio_file in audio_files:
            f.write(f"file '{os.path.abspath(audio_file)}'\n")
        concat_list = f.name

    try:
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_list,
            '-c:a', 'libmp3lame', '-q:a', '2',
            output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
    finally:
        os.unlink(concat_list)

    return output_path

def mix_ambient(voice_path, ambient_name, output_path):
    """Mix ambient background under voice track."""
    ambient_path = AMBIENT_DIR / f"{ambient_name}.mp3"

    if not ambient_path.exists():
        print(f"  Warning: Ambient '{ambient_name}' not found, skipping mix")
        shutil.copy(voice_path, output_path)
        return output_path

    # Get voice duration
    duration = get_audio_duration(voice_path)

    # Mix with ambient looped, faded, and at lower volume
    cmd = [
        'ffmpeg', '-y',
        '-i', voice_path,
        '-stream_loop', '-1', '-i', str(ambient_path),
        '-filter_complex', (
            f"[1:a]volume={AMBIENT_VOLUME_DB}dB,"
            f"afade=t=in:st=0:d={AMBIENT_FADE_IN}:curve=log,"
            f"afade=t=out:st={duration - AMBIENT_FADE_OUT}:d={AMBIENT_FADE_OUT}[amb];"
            f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2"
        ),
        '-t', str(duration),
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path

# ============================================================================
# MAIN BUILD FUNCTIONS
# ============================================================================

def build_session(session_name, mix_only=False):
    """Build a complete session from script."""
    print(f"\n{'='*60}")
    print(f"Building: {session_name}")
    print(f"{'='*60}")

    script_path = SCRIPT_DIR / f"{session_name}.txt"
    output_path = AUDIO_DIR / f"{session_name}.mp3"

    if not script_path.exists():
        print(f"  ERROR: Script not found: {script_path}")
        return False

    # Get configuration
    category, ambient, metadata = get_session_config(session_name)
    print(f"  Category: {category}")
    print(f"  Ambient: {ambient or 'none'}")

    if mix_only:
        # Just add ambient to existing audio
        if not output_path.exists():
            print(f"  ERROR: Audio file not found for mix-only: {output_path}")
            return False

        if ambient:
            print(f"  Mixing ambient '{ambient}' into existing audio...")
            temp_output = output_path.with_suffix('.tmp.mp3')
            mix_ambient(str(output_path), ambient, str(temp_output))
            shutil.move(temp_output, output_path)
            print(f"  Done: {output_path}")
        else:
            print(f"  No ambient specified, nothing to do")
        return True

    # Full build
    if not metadata:
        print(f"  ERROR: Could not parse script")
        return False

    content = metadata['content']
    segments = parse_script_segments(content, category)

    print(f"  Parsed {len(segments)} segments")

    # Create temp directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_files = []

        for i, (seg_type, seg_data) in enumerate(segments):
            if seg_type == 'text':
                print(f"  [{i+1}/{len(segments)}] Generating TTS ({len(seg_data)} chars)...")
                tts_path = os.path.join(temp_dir, f"segment_{i:04d}.mp3")
                generate_tts(seg_data, tts_path)
                audio_files.append(tts_path)

            elif seg_type == 'pause':
                print(f"  [{i+1}/{len(segments)}] Adding {seg_data:.1f}s pause...")
                silence_path = os.path.join(temp_dir, f"silence_{i:04d}.mp3")
                generate_silence(seg_data, silence_path)
                audio_files.append(silence_path)

        # Concatenate all segments
        print(f"  Concatenating {len(audio_files)} audio files...")
        voice_path = os.path.join(temp_dir, "voice_complete.mp3")
        concatenate_audio(audio_files, voice_path)

        # Mix ambient if specified
        if ambient:
            print(f"  Mixing ambient '{ambient}'...")
            mix_ambient(voice_path, ambient, str(output_path))
        else:
            shutil.copy(voice_path, output_path)

    duration = get_audio_duration(str(output_path))
    print(f"  Done: {output_path} ({duration/60:.1f} minutes)")
    return True

def list_sessions():
    """List all available sessions."""
    print("\nAvailable sessions:")
    print("-" * 60)

    scripts = sorted(SCRIPT_DIR.glob("*.txt"))
    for script in scripts:
        if script.name == "TEMPLATE.txt":
            continue
        name = script.stem
        category, ambient, _ = get_session_config(name)
        audio_exists = (AUDIO_DIR / f"{name}.mp3").exists()
        status = "✓" if audio_exists else " "
        print(f"  [{status}] {name}")
        print(f"       Category: {category}, Ambient: {ambient or 'none'}")

def build_all():
    """Build all sessions."""
    scripts = sorted(SCRIPT_DIR.glob("*.txt"))

    success = 0
    failed = 0

    for script in scripts:
        if script.name == "TEMPLATE.txt":
            continue
        name = script.stem
        try:
            if build_session(name):
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Complete: {success} succeeded, {failed} failed")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Salus Audio Session Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('session', nargs='?', help='Session name to build')
    parser.add_argument('--all', action='store_true', help='Build all sessions')
    parser.add_argument('--list', action='store_true', help='List all sessions')
    parser.add_argument('--mix-only', action='store_true',
                       help='Only mix ambient into existing audio (no TTS)')

    args = parser.parse_args()

    if args.list:
        list_sessions()
    elif args.all:
        build_all()
    elif args.session:
        build_session(args.session, mix_only=args.mix_only)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
