#!/usr/bin/env python3
"""
Resemble AI Voice Audition Script

Creates voices from text prompts and generates test clips.
Uses the Voice Design API to iterate on the perfect sleep narrator voice.

Usage:
    python audition-resemble.py                    # Create new voices + test
    python audition-resemble.py --test-existing    # Test all existing voices
    python audition-resemble.py --voice UUID       # Test a specific voice
"""

import os
import sys
import json
import time
import base64
import requests
import argparse
from pathlib import Path

# Load .env
env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())

API_KEY = os.getenv("RESEMBLE_API_KEY")
SYNTH_URL = "https://f.cluster.resemble.ai/synthesize"
API_URL = "https://app.resemble.ai/api/v2"
OUTPUT_DIR = Path("content/audio/resemble-auditions")

SYNTH_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

MGMT_HEADERS = {
    "Authorization": f"Token token={API_KEY}",
    "Content-Type": "application/json",
}

# Test passage — middle of Moonlit Garden, with SSML breaks
TEST_PASSAGE = (
    'There is a garden, an old walled garden hidden behind a stone house '
    'somewhere in the English countryside.'
    '<break time="4s" />'
    'You have been walking gently along a gravel path between tall hedges. '
    'The air is warm. It is a summer night, and the heat of the day is still '
    'held in the stone and the soil.'
    '<break time="5s" />'
    'You come to a gate. A wooden gate, painted blue once, long ago. '
    'The paint is peeling now, faded by years of sun and rain.'
    '<break time="6s" />'
    'You push it open and step through into a place that feels like it has '
    'been waiting for you.'
)

# Voice design prompts to try
VOICE_DESIGNS = [
    {
        "name": "Luna-warm",
        "prompt": "Warm, soft female voice with a gentle British accent. "
                  "Slow, soothing pace like a bedtime storyteller. Intimate, "
                  "calm tone. Low pitch, slightly breathy. Like whispering a "
                  "lullaby to help someone fall asleep.",
    },
    {
        "name": "Luna-deep",
        "prompt": "Deep, rich female voice. British. Very slow and measured, "
                  "like reading poetry by candlelight. Warm and maternal. "
                  "The kind of voice that makes you feel safe and drowsy.",
    },
    {
        "name": "Luna-young",
        "prompt": "Young woman, early twenties, soft British accent. Gentle "
                  "and dreamy, like telling a story under the stars. Airy, "
                  "light, with natural warmth. Not childish, just youthful "
                  "and calming.",
    },
    {
        "name": "Luna-husky",
        "prompt": "Slightly husky female voice, warm and low. British accent. "
                  "Speaks slowly with natural pauses. Sounds like late-night "
                  "radio, intimate and comforting. Perfect for bedtime stories.",
    },
]


def list_voices():
    """List all voices on the account."""
    r = requests.get(f"{API_URL}/voices?page=1&page_size=50", headers=MGMT_HEADERS)
    data = r.json()
    if not data.get("success"):
        print(f"Error listing voices: {data.get('message')}")
        return []
    return data.get("items", [])


def create_voice_design(name, prompt):
    """Create a voice using Voice Design (text prompt)."""
    print(f"\n  Creating voice design: {name}")
    print(f"  Prompt: {prompt[:80]}...")

    # Step 1: Generate voice samples
    r = requests.post(
        f"{API_URL}/voice-design",
        headers=MGMT_HEADERS,
        json={"user_prompt": prompt},
    )
    data = r.json()

    if not data.get("success"):
        print(f"  Error: {data.get('message')}")
        return None

    design_uuid = data.get("uuid") or data.get("voice_design_uuid")
    samples = data.get("samples", [])
    print(f"  Design UUID: {design_uuid}")
    print(f"  Got {len(samples)} samples")

    # Return the design data for the user to pick from
    return data


def synthesize_test(voice_uuid, voice_name, output_dir):
    """Generate a test clip with a voice."""
    output_path = output_dir / f"{voice_name}.wav"
    mp3_path = output_dir / f"{voice_name}.mp3"

    payload = {
        "voice_uuid": voice_uuid,
        "data": TEST_PASSAGE,
        "output_format": "wav",
        "sample_rate": 44100,
    }

    print(f"  Synthesizing {voice_name} ({voice_uuid})...", end=" ", flush=True)

    r = requests.post(SYNTH_URL, json=payload, headers=SYNTH_HEADERS)
    data = r.json()

    if not data.get("success"):
        print(f"FAILED: {data.get('message')}")
        return None

    audio_bytes = base64.b64decode(data["audio_content"])
    output_path.write_bytes(audio_bytes)

    # Convert to MP3
    import subprocess
    subprocess.run(
        ['ffmpeg', '-y', '-i', str(output_path), '-c:a', 'libmp3lame', '-b:a', '128k', str(mp3_path)],
        capture_output=True, check=True,
    )
    output_path.unlink()  # Remove WAV

    duration = data.get("duration", 0)
    print(f"{duration:.1f}s -> {mp3_path.name}")
    return mp3_path


def main():
    parser = argparse.ArgumentParser(description="Resemble AI Voice Audition")
    parser.add_argument("--test-existing", action="store_true", help="Test all existing voices")
    parser.add_argument("--voice", help="Test a specific voice UUID")
    parser.add_argument("--design", action="store_true", help="Create new voice designs from prompts")
    parser.add_argument("--list", action="store_true", help="List all voices")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: RESEMBLE_API_KEY not set in .env")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.list:
        voices = list_voices()
        print(f"\n{len(voices)} voices:")
        for v in voices:
            print(f"  {v['uuid']}: {v['name']} ({v.get('status', '?')})")
        return

    if args.voice:
        synthesize_test(args.voice, f"test-{args.voice}", OUTPUT_DIR)
        return

    if args.test_existing:
        voices = list_voices()
        print(f"\nTesting {len(voices)} voices...")
        for v in voices:
            synthesize_test(v["uuid"], v["name"], OUTPUT_DIR)
            time.sleep(0.5)
        print(f"\nAll auditions saved to {OUTPUT_DIR}/")
        return

    if args.design:
        print("Creating voice designs...")
        for design in VOICE_DESIGNS:
            result = create_voice_design(design["name"], design["prompt"])
            if result:
                print(f"  Result: {json.dumps(result, indent=2)[:500]}")
            time.sleep(2)
        return

    # Default: test all existing voices with the test passage
    voices = list_voices()
    # Filter to custom voices only (skip stock library)
    custom = [v for v in voices if v["uuid"] in [
        "3bd5acc8", "6b9e7f95", "54756dd0", "d1bd5b13"  # User-created voices
    ]]

    if not custom:
        print("No custom voices found. Use --design to create some, or --test-existing to test all.")
        return

    print(f"\nTesting {len(custom)} custom voices...")
    for v in custom:
        synthesize_test(v["uuid"], v["name"], OUTPUT_DIR)
        time.sleep(0.5)

    print(f"\nAuditions saved to {OUTPUT_DIR}/")
    print("Listen and tell me which voice you like best.")


if __name__ == "__main__":
    main()
