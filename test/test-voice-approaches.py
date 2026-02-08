#!/usr/bin/env python3
"""
Test two approaches for TTS voice consistency:

Test 1: Single API call with punctuation markers for pauses
        - Send entire script with ellipsis/em-dashes
        - Use silencedetect to find natural pauses
        - Extend pauses with silence insertion

Test 2: Section-based approach
        - Split script into 3 sections
        - One API call per section at temperature 0.3
        - Insert silence between sections
"""

import os
import subprocess
import tempfile
import requests
from pathlib import Path

# Load API key
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
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Marco voice

OUTPUT_DIR = Path("content/audio/test-consistency")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Test script content (without pause markers)
SECTION_1 = """Welcome to this brief mindfulness exercise. Take a moment to settle into wherever you are right now. Feel your feet on the ground, your body supported by your chair or cushion. Let your shoulders drop away from your ears and allow your jaw to soften."""

SECTION_2 = """Good. Now bring your attention to your breath. You don't need to change anything about it. Simply notice the natural rhythm of breathing in and breathing out. Feel the gentle rise and fall of your chest. The subtle expansion and release of your belly."""

SECTION_3 = """As you continue breathing naturally, I want you to imagine a warm, golden light beginning to form just above the crown of your head. With each inhale, this light grows brighter and warmer. With each exhale, it begins to flow down through your body, melting away any tension it encounters."""

SECTION_4 = """Feel this light moving through your forehead, relaxing the space between your eyebrows. Down through your face, softening your cheeks and jaw. Flowing through your neck and into your shoulders, releasing any tightness held there. Let it continue down through your arms to your fingertips.

Now gently begin to bring your awareness back to the room around you. Notice the sounds, the temperature, the space you're in. Take one more deep breath in, and as you exhale, slowly open your eyes. You are present, you are calm, you are ready to continue your day."""


def generate_tts(text, output_path, temperature=0.3):
    """Generate TTS audio using Fish API with specified temperature."""
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

    print(f"  Generating TTS ({len(text)} chars, temp={temperature})...")
    response = requests.post(FISH_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Fish TTS API error: {response.status_code} - {response.text}")

    Path(output_path).write_bytes(response.content)
    return output_path


def generate_silence(duration_seconds, output_path):
    """Generate silent audio file."""
    cmd = [
        'ffmpeg', '-y', '-f', 'lavfi',
        '-i', f'anullsrc=r=44100:cl=stereo',
        '-t', str(duration_seconds),
        '-c:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def get_duration(audio_path):
    """Get audio duration in seconds."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def detect_silences(audio_path, noise_threshold="-35dB", min_duration=0.3):
    """Detect silent sections in audio file."""
    cmd = [
        'ffmpeg', '-i', audio_path,
        '-af', f'silencedetect=n={noise_threshold}:d={min_duration}',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse silence detection output
    silences = []
    lines = result.stderr.split('\n')

    current_start = None
    for line in lines:
        if 'silence_start:' in line:
            parts = line.split('silence_start:')
            if len(parts) > 1:
                current_start = float(parts[1].strip().split()[0])
        elif 'silence_end:' in line and current_start is not None:
            parts = line.split('silence_end:')
            if len(parts) > 1:
                end_parts = parts[1].strip().split()
                end_time = float(end_parts[0])
                silences.append((current_start, end_time))
                current_start = None

    return silences


def concatenate_audio(audio_files, output_path):
    """Concatenate multiple audio files."""
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


def test1_single_call_with_markers():
    """
    Test 1: Single API call with punctuation markers
    - Use em-dashes (—) to indicate pause points
    - Detect resulting silences and extend them
    """
    print("\n" + "="*60)
    print("TEST 1: Single API call with pause markers")
    print("="*60)

    # Combine all sections with em-dash pause markers
    full_script = f"""{SECTION_1}

— — —

{SECTION_2}

— — —

{SECTION_3}

— — —

{SECTION_4}"""

    # Generate single TTS
    tts_path = str(OUTPUT_DIR / "test1_raw.mp3")
    generate_tts(full_script, tts_path, temperature=0.3)

    raw_duration = get_duration(tts_path)
    print(f"  Raw audio duration: {raw_duration:.1f}s")

    # Detect silences
    print("  Detecting silences...")
    silences = detect_silences(tts_path, noise_threshold="-30dB", min_duration=0.4)
    print(f"  Found {len(silences)} silence points:")
    for i, (start, end) in enumerate(silences):
        duration = end - start
        print(f"    {i+1}. {start:.2f}s - {end:.2f}s (duration: {duration:.2f}s)")

    # For now, just copy the raw output as our test result
    # (In a full implementation, we'd extend these silences)
    final_path = str(OUTPUT_DIR / "test1_final.mp3")

    # Simple approach: just use the raw output for comparison
    # The em-dashes should create natural pauses
    import shutil
    shutil.copy(tts_path, final_path)

    print(f"  Final audio: {final_path}")
    print(f"  Duration: {get_duration(final_path):.1f}s")

    return final_path


def test2_section_based():
    """
    Test 2: Section-based approach
    - One API call per section at temperature 0.3
    - 8-second silence between sections
    """
    print("\n" + "="*60)
    print("TEST 2: Section-based (3 sections + silences)")
    print("="*60)

    sections = [SECTION_1, SECTION_2, SECTION_3, SECTION_4]
    silence_duration = 8  # seconds between sections

    audio_files = []

    with tempfile.TemporaryDirectory() as temp_dir:
        for i, section in enumerate(sections):
            # Generate TTS for section
            section_path = os.path.join(temp_dir, f"section_{i}.mp3")
            generate_tts(section, section_path, temperature=0.3)
            audio_files.append(section_path)

            # Add silence after each section except the last
            if i < len(sections) - 1:
                silence_path = os.path.join(temp_dir, f"silence_{i}.mp3")
                generate_silence(silence_duration, silence_path)
                audio_files.append(silence_path)
                print(f"  Added {silence_duration}s silence")

        # Concatenate all
        final_path = str(OUTPUT_DIR / "test2_final.mp3")
        concatenate_audio(audio_files, final_path)

    print(f"  Final audio: {final_path}")
    print(f"  Duration: {get_duration(final_path):.1f}s")

    return final_path


def main():
    print("Voice Consistency Test")
    print("=" * 60)

    if not FISH_API_KEY:
        print("ERROR: FISH_API_KEY not set in .env file")
        return

    # Run both tests
    test1_path = test1_single_call_with_markers()
    test2_path = test2_section_based()

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"\nTest 1 (single call): {test1_path}")
    print(f"Test 2 (sections):    {test2_path}")
    print("\nListen to both files and compare:")
    print("- Voice consistency throughout")
    print("- Natural pause points")
    print("- Overall quality")
    print("\nTest 1 uses 1 API call, Test 2 uses 4 API calls")


if __name__ == "__main__":
    main()
