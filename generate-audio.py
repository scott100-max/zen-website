import requests
import re
import os
import sys

API_KEY = "sk_400c6d730d0efccda44656815ac3472e985bf51bf4917f13"
BASE = "/Users/scottripley/salus-website"

# ── Voice presets ──
# Each voice has tailored settings for meditation/wellness content.
# ElevenLabs built-in voices (no extra cost, included in all plans).
VOICES = {
    "bella": {
        "id": "hpp4J3VqNfWAUOO0d1Us",
        "name": "Bella",
        "desc": "Female, American, warm & professional",
        "stability": 0.80,
        "similarity_boost": 0.75,
        "style": 0.15,
        "speed": 0.75,
    },
    "lily": {
        "id": "pFZP5JQG7iQjIQuC4Bku",
        "name": "Lily",
        "desc": "Female, British, velvety & soft",
        "stability": 0.90,
        "similarity_boost": 0.65,
        "style": 0.03,
        "speed": 0.70,
    },
    "alice": {
        "id": "Xb7hH8MSUJpSbSDYk0k2",
        "name": "Alice",
        "desc": "Female, British, clear & calm",
        "stability": 0.80,
        "similarity_boost": 0.75,
        "style": 0.10,
        "speed": 0.78,
    },
    "sarah": {
        "id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Sarah",
        "desc": "Female, American, mature & reassuring",
        "stability": 0.82,
        "similarity_boost": 0.75,
        "style": 0.10,
        "speed": 0.75,
    },
    "river": {
        "id": "SAz9YHcvj6GT2YYXdXww",
        "name": "River",
        "desc": "Neutral, American, relaxed & soothing",
        "stability": 0.85,
        "similarity_boost": 0.70,
        "style": 0.05,
        "speed": 0.75,
    },
    "george": {
        "id": "JBFqnCBsd6RMkjVDRZzb",
        "name": "George",
        "desc": "Male, British, warm storyteller",
        "stability": 0.82,
        "similarity_boost": 0.75,
        "style": 0.10,
        "speed": 0.75,
    },
    "daniel": {
        "id": "onwK4e9ZLuTAKqWW03F9",
        "name": "Daniel",
        "desc": "Male, British, steady & calming",
        "stability": 0.85,
        "similarity_boost": 0.70,
        "style": 0.08,
        "speed": 0.78,
    },
    "brian": {
        "id": "nPczCjzI2devNBz1zQrb",
        "name": "Brian",
        "desc": "Male, American, deep & comforting",
        "stability": 0.85,
        "similarity_boost": 0.75,
        "style": 0.08,
        "speed": 0.72,
    },
    "chris": {
        "id": "iP95p4xoKVk53GoZ742B",
        "name": "Chris",
        "desc": "Male, American, warm & down-to-earth",
        "stability": 0.80,
        "similarity_boost": 0.75,
        "style": 0.12,
        "speed": 0.75,
    },
}

DEFAULT_VOICE = "bella"

scripts = [
    ("content/scripts/01-morning-meditation.txt", "content/audio/01-morning-meditation.mp3"),
    ("content/scripts/02-deep-sleep.txt", "content/audio/02-deep-sleep.mp3"),
    ("content/scripts/03-breathing-for-anxiety.txt", "content/audio/03-breathing-for-anxiety.mp3"),
    ("content/scripts/04-science-of-mindfulness.txt", "content/audio/04-science-of-mindfulness.mp3"),
]


def clean_script(text):
    """Clean script text for TTS: remove empty lines, use pauses between paragraphs."""
    lines = text.strip().split("\n")
    paragraphs = []
    current = []

    for line in lines:
        stripped = line.strip()
        if stripped == "" or stripped == "...":
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))

    # Join paragraphs with a longer pause (period + ellipsis)
    # This gives more natural pacing than "..." between every single line
    return " ... ".join(paragraphs)


def check_credits():
    """Check remaining ElevenLabs characters."""
    r = requests.get(
        "https://api.elevenlabs.io/v1/user/subscription",
        headers={"xi-api-key": API_KEY},
    )
    if r.status_code == 200:
        d = r.json()
        used = d.get("character_count", 0)
        limit = d.get("character_limit", 0)
        remaining = limit - used
        print(f"Credits: {remaining:,} / {limit:,} characters remaining")
        return remaining
    return None


def generate_one(script_path, audio_path, voice_key):
    voice = VOICES[voice_key]
    full_script = os.path.join(BASE, script_path)
    full_audio = os.path.join(BASE, audio_path)

    with open(full_script) as f:
        text = f.read()

    text = clean_script(text)

    print(f"Generating: {os.path.basename(audio_path)} ({len(text)} chars)")
    print(f"  Voice: {voice['name']} — {voice['desc']}")

    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice['id']}",
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": voice["stability"],
                "similarity_boost": voice["similarity_boost"],
                "style": voice["style"],
                "speed": voice["speed"],
            },
        },
    )

    if resp.status_code == 200:
        os.makedirs(os.path.dirname(full_audio), exist_ok=True)
        with open(full_audio, "wb") as f:
            f.write(resp.content)
        print(f"  Saved: {full_audio} ({len(resp.content):,} bytes)")
    else:
        print(f"  ERROR {resp.status_code}: {resp.text}")


def print_usage():
    print("Usage: python3 generate-audio.py [options]")
    print()
    print("Options:")
    print("  --voice NAME    Voice preset (default: bella)")
    print("  --only N        Only generate script N (1-4)")
    print("  --list-voices   Show available voices")
    print("  --check-credits Show remaining ElevenLabs credits")
    print("  --dry-run       Show what would be generated without calling API")
    print()
    print("Examples:")
    print("  python3 generate-audio.py                        # All 4 with Bella")
    print("  python3 generate-audio.py --voice lily            # All 4 with Lily")
    print("  python3 generate-audio.py --voice daniel --only 3 # Anxiety script with Daniel")
    print("  python3 generate-audio.py --list-voices           # Show voice options")


if __name__ == "__main__":
    args = sys.argv[1:]

    # Parse args
    voice_key = DEFAULT_VOICE
    only = None
    dry_run = False

    i = 0
    while i < len(args):
        if args[i] == "--voice" and i + 1 < len(args):
            voice_key = args[i + 1].lower()
            i += 2
        elif args[i] == "--only" and i + 1 < len(args):
            only = int(args[i + 1])
            i += 2
        elif args[i] == "--list-voices":
            print("Available voices:\n")
            for key, v in VOICES.items():
                marker = " (default)" if key == DEFAULT_VOICE else ""
                print(f"  {key:12s}  {v['name']:10s}  {v['desc']}{marker}")
            print()
            print("All voices are included in your ElevenLabs plan (no extra cost per voice).")
            print("Each full regeneration of all 4 scripts uses ~14,000 characters.")
            sys.exit(0)
        elif args[i] == "--check-credits":
            check_credits()
            sys.exit(0)
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        elif args[i] in ("-h", "--help"):
            print_usage()
            sys.exit(0)
        else:
            print(f"Unknown option: {args[i]}")
            print_usage()
            sys.exit(1)

    if voice_key not in VOICES:
        print(f"Unknown voice: {voice_key}")
        print(f"Available: {', '.join(VOICES.keys())}")
        sys.exit(1)

    print(f"=== Salus Audio Generator ===")
    print(f"Voice: {VOICES[voice_key]['name']} — {VOICES[voice_key]['desc']}")
    print()

    remaining = check_credits()
    if remaining is not None:
        print()

    to_generate = []
    for idx, (script_path, audio_path) in enumerate(scripts, 1):
        if only is not None and idx != only:
            continue
        to_generate.append((script_path, audio_path))

    if dry_run:
        total_chars = 0
        for script_path, audio_path in to_generate:
            full_script = os.path.join(BASE, script_path)
            with open(full_script) as f:
                text = clean_script(f.read())
            total_chars += len(text)
            print(f"  Would generate: {os.path.basename(audio_path)} ({len(text)} chars)")
        print(f"\nTotal: ~{total_chars:,} characters")
        sys.exit(0)

    for script_path, audio_path in to_generate:
        generate_one(script_path, audio_path, voice_key)
        print()

    print("Done!")
