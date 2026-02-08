#!/usr/bin/env python3
"""
Test Option A: Single API call with marker words for pauses
Target: 09-rainfall-sleep-journey

Approach:
1. Replace ... markers with spoken word "break" (distinctive, easy to detect)
2. Send entire script in ONE API call with temperature 0.3
3. Detect "break" instances using speech recognition or audio analysis
4. Replace each "break" with appropriate silence duration
"""

import os
import re
import subprocess
import tempfile
import requests
import json
from pathlib import Path

# Load environment
def load_env():
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

load_env()

FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_API_KEY = os.environ.get("FISH_API_KEY", "")
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"

OUTPUT_DIR = Path("content/audio/test-option-a")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pause durations for sleep category (in seconds)
PAUSE_DURATIONS = {
    1: 10,   # Single ... → 10 seconds
    2: 35,   # Double ... → 35 seconds
    3: 75,   # Triple ... → 75 seconds
}

MARKER_WORD = "break"  # Distinctive word to mark pause positions


def parse_script(script_path):
    """Parse script and extract content after ---"""
    text = Path(script_path).read_text()
    if '---' in text:
        _, content = text.split('---', 1)
    else:
        content = text
    return content.strip()


def prepare_script_with_markers(content):
    """
    Replace pause markers with spoken marker words.
    Returns: (text_with_markers, pause_info_list)

    pause_info_list contains tuples of (marker_index, pause_duration_seconds)
    """
    lines = content.split('\n')
    output_lines = []
    pause_info = []
    marker_index = 0
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Check for explicit silence markers like [SILENCE: 90 seconds]
        silence_match = re.match(r'\[(SILENCE|PAUSE):\s*(\d+)\s*seconds?\]', line, re.I)
        if silence_match:
            duration = int(silence_match.group(2))
            output_lines.append(f"{MARKER_WORD}.")
            pause_info.append((marker_index, duration))
            marker_index += 1
            i += 1
            continue

        # Check for ... pause markers
        if line == '...':
            # Count consecutive ... lines
            count = 0
            while i < len(lines) and lines[i].strip() == '...':
                count += 1
                i += 1

            # Map count to duration
            level = min(count, 3)
            duration = PAUSE_DURATIONS[level]

            # Add marker word
            output_lines.append(f"{MARKER_WORD}.")
            pause_info.append((marker_index, duration))
            marker_index += 1
        elif line:
            output_lines.append(line)
            i += 1
        else:
            # Empty line - keep for paragraph structure
            output_lines.append('')
            i += 1

    # Join with single newlines, collapse multiple empty lines
    text = '\n'.join(output_lines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text, pause_info


def generate_tts(text, output_path, temperature=0.3):
    """Generate TTS using Fish API."""
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
        "temperature": temperature,
    }

    print(f"  Sending {len(text):,} characters to Fish API (temp={temperature})...")
    response = requests.post(FISH_API_URL, headers=headers, json=payload, timeout=600)

    if response.status_code != 200:
        raise Exception(f"Fish API error: {response.status_code} - {response.text[:500]}")

    Path(output_path).write_bytes(response.content)
    return output_path


def get_duration(audio_path):
    """Get audio duration in seconds."""
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def transcribe_with_whisper(audio_path):
    """
    Use Whisper to transcribe audio and get word timestamps.
    Returns list of (word, start_time, end_time)
    """
    print("  Transcribing with Whisper to find marker positions...")

    # Check if whisper is available
    try:
        result = subprocess.run(['which', 'whisper'], capture_output=True)
        if result.returncode != 0:
            # Try whisper.cpp or similar
            result = subprocess.run(['which', 'whisper-cpp'], capture_output=True)
            if result.returncode != 0:
                print("  WARNING: Whisper not found, using fallback detection method")
                return None
    except:
        return None

    # Run Whisper with word timestamps
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run([
            'whisper', audio_path,
            '--model', 'base',
            '--output_format', 'json',
            '--word_timestamps', 'True',
            '--output_dir', temp_dir
        ], capture_output=True, text=True)

        # Find the JSON output
        json_files = list(Path(temp_dir).glob('*.json'))
        if not json_files:
            print("  WARNING: Whisper produced no JSON output")
            return None

        with open(json_files[0]) as f:
            data = json.load(f)

        # Extract word timestamps
        words = []
        for segment in data.get('segments', []):
            for word_info in segment.get('words', []):
                words.append((
                    word_info['word'].strip().lower(),
                    word_info['start'],
                    word_info['end']
                ))

        return words


def detect_markers_by_silence(audio_path, marker_word="break"):
    """
    Fallback: Detect marker positions by finding short silences
    that likely follow the spoken marker word.
    """
    print("  Using silence detection as fallback...")

    # Run silence detection with tight parameters
    result = subprocess.run([
        'ffmpeg', '-i', audio_path,
        '-af', 'silencedetect=n=-28dB:d=0.3',
        '-f', 'null', '-'
    ], capture_output=True, text=True)

    # Parse silence points
    silences = []
    lines = result.stderr.split('\n')

    current_start = None
    for line in lines:
        if 'silence_start:' in line:
            try:
                start = float(line.split('silence_start:')[1].strip().split()[0])
                current_start = start
            except:
                pass
        elif 'silence_end:' in line and current_start is not None:
            try:
                end = float(line.split('silence_end:')[1].strip().split()[0])
                silences.append((current_start, end))
                current_start = None
            except:
                pass

    return silences


def find_marker_timestamps(audio_path, expected_count):
    """
    Find timestamps of marker words in the audio.
    Returns list of (start_time, end_time) for each marker.
    """
    # Try Whisper first for accurate word detection
    words = transcribe_with_whisper(audio_path)

    if words:
        # Find all instances of the marker word
        markers = []
        for word, start, end in words:
            if MARKER_WORD in word.lower().replace('.', '').replace(',', ''):
                markers.append((start, end))

        print(f"  Found {len(markers)} '{MARKER_WORD}' markers via Whisper")

        if len(markers) == expected_count:
            return markers
        elif len(markers) > 0:
            print(f"  WARNING: Expected {expected_count} markers, found {len(markers)}")
            return markers

    # Fallback to silence-based detection
    silences = detect_markers_by_silence(audio_path)
    print(f"  Found {len(silences)} silence points")

    # Filter to likely marker positions (silences of 0.3-1.5 seconds)
    likely_markers = [(s, e) for s, e in silences if 0.3 <= (e - s) <= 1.5]
    print(f"  {len(likely_markers)} likely marker silences")

    return likely_markers


def replace_markers_with_silence(audio_path, marker_timestamps, pause_info, output_path):
    """
    Replace marker word sections with appropriate silence durations.

    This is complex because we need to:
    1. Cut out each marker word
    2. Insert silence of the appropriate duration
    3. Keep everything else intact
    """
    print(f"  Replacing {len(marker_timestamps)} markers with silences...")

    if len(marker_timestamps) != len(pause_info):
        print(f"  WARNING: Marker count mismatch. Timestamps: {len(marker_timestamps)}, Expected: {len(pause_info)}")
        # Use minimum of the two
        count = min(len(marker_timestamps), len(pause_info))
        marker_timestamps = marker_timestamps[:count]
        pause_info = pause_info[:count]

    # Get total duration
    total_duration = get_duration(audio_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        segments = []
        current_pos = 0

        for i, ((marker_start, marker_end), (_, pause_duration)) in enumerate(zip(marker_timestamps, pause_info)):
            # Extract audio segment before this marker
            if marker_start > current_pos:
                segment_path = os.path.join(temp_dir, f"segment_{i:04d}_audio.mp3")
                subprocess.run([
                    'ffmpeg', '-y', '-i', audio_path,
                    '-ss', str(current_pos),
                    '-t', str(marker_start - current_pos),
                    '-c:a', 'libmp3lame', '-q:a', '2',
                    segment_path
                ], capture_output=True, check=True)
                segments.append(segment_path)

            # Generate silence of appropriate duration
            silence_path = os.path.join(temp_dir, f"segment_{i:04d}_silence.mp3")
            subprocess.run([
                'ffmpeg', '-y', '-f', 'lavfi',
                '-i', 'anullsrc=r=44100:cl=stereo',
                '-t', str(pause_duration),
                '-c:a', 'libmp3lame', '-q:a', '2',
                silence_path
            ], capture_output=True, check=True)
            segments.append(silence_path)

            current_pos = marker_end

            if (i + 1) % 20 == 0:
                print(f"    Processed {i + 1}/{len(marker_timestamps)} markers...")

        # Add final segment after last marker
        if current_pos < total_duration:
            final_path = os.path.join(temp_dir, "segment_final.mp3")
            subprocess.run([
                'ffmpeg', '-y', '-i', audio_path,
                '-ss', str(current_pos),
                '-c:a', 'libmp3lame', '-q:a', '2',
                final_path
            ], capture_output=True, check=True)
            segments.append(final_path)

        # Concatenate all segments
        print(f"  Concatenating {len(segments)} segments...")
        concat_list = os.path.join(temp_dir, "concat.txt")
        with open(concat_list, 'w') as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")

        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_list,
            '-c:a', 'libmp3lame', '-q:a', '2',
            output_path
        ], capture_output=True, check=True)

    return output_path


def mix_ambient(voice_path, ambient_name, output_path):
    """Mix ambient sound under voice track."""
    ambient_path = Path(f"content/audio/ambient/{ambient_name}.mp3")

    if not ambient_path.exists():
        print(f"  WARNING: Ambient '{ambient_name}' not found")
        import shutil
        shutil.copy(voice_path, output_path)
        return output_path

    duration = get_duration(voice_path)

    print(f"  Mixing ambient '{ambient_name}' (-14dB)...")
    subprocess.run([
        'ffmpeg', '-y',
        '-i', voice_path,
        '-stream_loop', '-1', '-i', str(ambient_path),
        '-filter_complex', (
            f"[1:a]volume=-14dB,"
            f"afade=t=in:st=0:d=15:curve=log,"
            f"afade=t=out:st={duration - 8}:d=8[amb];"
            f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2"
        ),
        '-t', str(duration),
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ], capture_output=True, check=True)

    return output_path


def main():
    print("="*60)
    print("OPTION A TEST: Single API Call with Marker Words")
    print("Target: 09-rainfall-sleep-journey")
    print("="*60)

    if not FISH_API_KEY:
        print("ERROR: FISH_API_KEY not set")
        return

    script_path = Path("content/scripts/09-rainfall-sleep-journey.txt")
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return

    # Step 1: Parse and prepare script
    print("\n[1/5] Parsing script and adding markers...")
    content = parse_script(script_path)
    text_with_markers, pause_info = prepare_script_with_markers(content)

    print(f"  Original content: {len(content):,} chars")
    print(f"  With markers: {len(text_with_markers):,} chars")
    print(f"  Total pause markers: {len(pause_info)}")

    # Save prepared script for review
    prepared_path = OUTPUT_DIR / "prepared_script.txt"
    prepared_path.write_text(text_with_markers)
    print(f"  Saved prepared script: {prepared_path}")

    # Step 2: Generate TTS in single call
    print("\n[2/5] Generating TTS (single API call)...")
    raw_audio_path = str(OUTPUT_DIR / "01_raw_tts.mp3")
    generate_tts(text_with_markers, raw_audio_path, temperature=0.3)

    raw_duration = get_duration(raw_audio_path)
    print(f"  Raw audio: {raw_duration:.1f}s ({raw_duration/60:.1f} min)")

    # Step 3: Find marker timestamps
    print("\n[3/5] Finding marker timestamps...")
    marker_timestamps = find_marker_timestamps(raw_audio_path, len(pause_info))

    if not marker_timestamps:
        print("  ERROR: Could not detect markers. Stopping.")
        return

    # Step 4: Replace markers with silences
    print("\n[4/5] Replacing markers with appropriate silences...")
    voice_path = str(OUTPUT_DIR / "02_voice_with_silences.mp3")
    replace_markers_with_silence(raw_audio_path, marker_timestamps, pause_info, voice_path)

    voice_duration = get_duration(voice_path)
    print(f"  Voice track: {voice_duration:.1f}s ({voice_duration/60:.1f} min)")

    # Step 5: Mix ambient
    print("\n[5/5] Mixing ambient...")
    final_path = str(OUTPUT_DIR / "03_final_with_ambient.mp3")
    mix_ambient(voice_path, "rain", final_path)

    final_duration = get_duration(final_path)

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"\nOutput files:")
    print(f"  1. Raw TTS:     {raw_audio_path} ({raw_duration/60:.1f} min)")
    print(f"  2. With pauses: {voice_path} ({voice_duration/60:.1f} min)")
    print(f"  3. Final:       {final_path} ({final_duration/60:.1f} min)")
    print(f"\nAPI calls made: 1")
    print(f"Expected voice consistency: HIGH (single generation)")


if __name__ == "__main__":
    main()
