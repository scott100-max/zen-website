#!/usr/bin/env python3
"""
ElevenLabs Voice Audition Script

Tests candidate voices for sleep stories by generating sample audio
from a passage of Monty's Midnight Feast. Outputs MP3 files to
content/audio/voice-auditions/ for human comparison.

Usage:
    python audition-voices.py
    python audition-voices.py --list-voices          # List available voices
    python audition-voices.py --voice-id XXXX        # Test a specific voice ID
    python audition-voices.py --models v2             # Test only v2 model
"""

import os
import sys
import argparse
import time
import requests
from pathlib import Path

# Load .env
env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())

API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
BASE_URL = "https://api.elevenlabs.io/v1"
OUTPUT_DIR = Path("content/audio/voice-auditions")

# Sample text from the middle of Monty's Midnight Feast (~500 chars)
AUDITION_TEXT = (
    "He's curled into a tight ginger circle, nose tucked under his tail, "
    "one paw covering his eyes. His breathing is slow and deep. His sides "
    "rise and fall with the gentle rhythm of a cat who is completely, "
    "unreservedly at peace with the world. "
    "But something has woken him. Not a noise, exactly. More like a feeling. "
    "A gentle tug somewhere behind his whiskers that says the same thing it "
    "says every night around this time. It says: the kitchen."
)

# Candidate voices to test (name -> voice_id, populated by --list-voices or hardcoded)
CANDIDATE_VOICES = {
    "Daniel": "onwK4e9ZLuTAKqWW03F9",
    "Charlie": "IKne3meq5aSn9XLyUdCD",
    "Callum": "N2lVS1w4EtoT3dr4eOWO",
    "George": "JBFqnCBsd6RMkjVDRZzb",
    "Bill": "pqHfZKP75CvOlQylNhV4",
    "Alice": "Xb7hH8MSUJpSbSDYk0k2",
    "Bella": "hpp4J3VqNfWAUOO0d1Us",
    "Lily": "pFZP5JQG7iQjIQuC4Bku",
    "Rachel": "6AUOG2nbfr0yFEeI0784",
}

# Models to test
MODELS = {
    "v2": "eleven_multilingual_v2",
    "v3": "eleven_v3",
}

# Voice settings per model (v3 requires discrete stability values)
VOICE_SETTINGS = {
    "v2": {
        "stability": 0.75,
        "similarity_boost": 0.75,
        "style": 0.0,
        "use_speaker_boost": True,
    },
    "v3": {
        "stability": 1.0,       # v3 only accepts 0.0, 0.5, 1.0
        "similarity_boost": 0.75,
        "style": 0.0,
    },
}


def list_voices():
    """Fetch and display available voices from ElevenLabs."""
    resp = requests.get(
        f"{BASE_URL}/voices",
        headers={"xi-api-key": API_KEY},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} - {resp.text[:200]}")
        return

    voices = resp.json().get("voices", [])
    print(f"\nFound {len(voices)} voices:\n")
    print(f"{'Name':<25} {'Voice ID':<30} {'Category':<15} {'Labels'}")
    print("-" * 90)
    for v in sorted(voices, key=lambda x: x.get("name", "")):
        name = v.get("name", "?")
        vid = v.get("voice_id", "?")
        cat = v.get("category", "?")
        labels = v.get("labels", {})
        label_str = ", ".join(f"{k}={val}" for k, val in labels.items()) if labels else ""
        print(f"{name:<25} {vid:<30} {cat:<15} {label_str}")


def generate_audition(voice_name, voice_id, model_key, model_id):
    """Generate a single audition clip."""
    output_file = OUTPUT_DIR / f"{voice_name.lower()}_{model_key}.mp3"

    url = f"{BASE_URL}/text-to-speech/{voice_id}?output_format=mp3_44100_128"

    resp = requests.post(
        url,
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": AUDITION_TEXT,
            "model_id": model_id,
            "voice_settings": VOICE_SETTINGS.get(model_key, VOICE_SETTINGS["v2"]),
        },
        timeout=120,
    )

    if resp.status_code != 200:
        print(f"  FAILED: {resp.status_code} - {resp.text[:200]}")
        return False

    output_file.write_bytes(resp.content)
    size_kb = len(resp.content) / 1024
    print(f"  -> {output_file} ({size_kb:.0f} KB)")
    return True


def main():
    parser = argparse.ArgumentParser(description="ElevenLabs Voice Audition")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--voice-id", help="Test a specific voice ID")
    parser.add_argument("--voice-name", default="custom", help="Name for custom voice ID")
    parser.add_argument("--models", nargs="+", choices=["v2", "v3"], default=["v2", "v3"],
                        help="Models to test (default: both)")
    parser.add_argument("--text", help="Custom audition text (default: Monty passage)")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not found in .env")
        sys.exit(1)

    if args.list_voices:
        list_voices()
        return

    global AUDITION_TEXT
    if args.text:
        AUDITION_TEXT = args.text

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build voice list
    voices = {}
    if args.voice_id:
        voices[args.voice_name] = args.voice_id
    else:
        voices = CANDIDATE_VOICES.copy()

    models_to_test = {k: MODELS[k] for k in args.models}

    total = len(voices) * len(models_to_test)
    print(f"Generating {total} audition clips...")
    print(f"Text: \"{AUDITION_TEXT[:80]}...\"")
    print(f"Output: {OUTPUT_DIR}/")
    print()

    count = 0
    for voice_name, voice_id in voices.items():
        for model_key, model_id in models_to_test.items():
            count += 1
            print(f"[{count}/{total}] {voice_name} ({model_key})...")
            generate_audition(voice_name, voice_id, model_key, model_id)
            time.sleep(0.5)  # Rate limiting

    print(f"\nDone! {count} clips saved to {OUTPUT_DIR}/")
    print("Listen and pick your favourite, then update ELEVENLABS_VOICE_ID in build-session-v3.py")


if __name__ == "__main__":
    main()
