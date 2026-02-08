#!/usr/bin/env python3
"""
Test Fish Audio's maximum text input length per API call.
Tests 5K, 10K, 20K characters to find limits.
"""

import os
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
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"

OUTPUT_DIR = Path("content/audio/test-consistency")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Sample meditation text to repeat (about 500 chars)
SAMPLE_TEXT = """Take a moment to settle into a comfortable position. Allow your eyes to gently close. Begin to notice your breath, the natural rhythm of inhaling and exhaling. With each breath, feel yourself becoming more relaxed, more present. Let go of any tension you may be holding. """

def test_char_limit(target_chars):
    """Test if Fish can handle a specific character count."""
    # Generate text of approximately target length
    repeats = (target_chars // len(SAMPLE_TEXT)) + 1
    text = (SAMPLE_TEXT * repeats)[:target_chars]

    actual_chars = len(text)
    print(f"\nTesting {actual_chars:,} characters...")

    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "reference_id": FISH_VOICE_ID,
        "format": "mp3",
        "temperature": 0.3,
    }

    try:
        response = requests.post(FISH_API_URL, headers=headers, json=payload, timeout=300)

        if response.status_code == 200:
            output_path = OUTPUT_DIR / f"test_{actual_chars}_chars.mp3"
            output_path.write_bytes(response.content)

            # Get file size and duration
            file_size = output_path.stat().st_size / 1024  # KB

            # Get duration via ffprobe
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(output_path)
            ], capture_output=True, text=True)
            duration = float(result.stdout.strip()) if result.stdout.strip() else 0

            print(f"  ✓ SUCCESS: {actual_chars:,} chars → {duration:.1f}s audio ({file_size:.0f} KB)")
            return True, duration
        else:
            print(f"  ✗ FAILED: Status {response.status_code}")
            print(f"    Response: {response.text[:500]}")
            return False, 0

    except requests.exceptions.Timeout:
        print(f"  ✗ TIMEOUT: Request timed out after 300s")
        return False, 0
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False, 0


def main():
    print("Fish Audio Character Limit Test")
    print("=" * 50)

    if not FISH_API_KEY:
        print("ERROR: FISH_API_KEY not set")
        return

    # Test progressively larger inputs
    test_sizes = [5000, 10000, 20000, 30000, 50000]

    results = {}
    for size in test_sizes:
        success, duration = test_char_limit(size)
        results[size] = (success, duration)

        if not success:
            print(f"\n⚠ Limit likely reached at {size:,} characters")
            break

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for size, (success, duration) in results.items():
        status = "✓" if success else "✗"
        if success:
            print(f"  {status} {size:,} chars → {duration:.1f}s")
        else:
            print(f"  {status} {size:,} chars → FAILED")


if __name__ == "__main__":
    main()
