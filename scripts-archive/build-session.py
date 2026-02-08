#!/usr/bin/env python3
"""
Salus Audio Session Builder v3

Builds meditation sessions from script files using Fish TTS API.
Incorporates: auto-retry, duration validation, manifest generation.

Usage:
    python3 build-session.py <session-name>              # Build raw narration
    python3 build-session.py <session-name> --with-ambient  # Build + mix ambient
    python3 build-session.py <session-name> --mix-only   # Add ambient to existing
    python3 build-session.py --list                      # List all sessions

Bible workflow:
    1. Build raw narration (no ambient)
    2. Analyze with analyze_audio_v5.py
    3. If PASS → mix ambient (--mix-only)
    4. Human review
    5. Deploy to audio-free/
"""

import os, sys, re, subprocess, tempfile, shutil, json, time, random, argparse
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path("content/scripts")
OUTPUT_DIR = Path("content/audio-free")
AMBIENT_DIR = Path("content/audio/ambient")

FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Marco

SAMPLE_RATE = 44100
AMBIENT_VOLUME_DB = -14
AMBIENT_FADE_IN = 15
AMBIENT_FADE_OUT = 8

# Pause durations: category -> {dot_count: (min_s, max_s)}
PAUSE_PROFILES = {
    'sleep':       {1: (5, 10),  2: (12, 20),  3: (25, 45)},
    'focus':       {1: (2, 4),   2: (5, 10),   3: (10, 20)},
    'stress':      {1: (3, 7),   2: (8, 15),   3: (15, 30)},
    'mindfulness': {1: (3, 7),   2: (10, 20),  3: (20, 40)},
    'beginner':    {1: (3, 6),   2: (8, 15),   3: (15, 25)},
    'advanced':    {1: (5, 10),  2: (15, 30),  3: (30, 60)},
}

# ============================================================================
# LOAD ENVIRONMENT
# ============================================================================

env_path = Path(__file__).parent / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

API_KEY = os.environ.get("FISH_API_KEY", "")

# ============================================================================
# SCRIPT PARSING
# ============================================================================

def parse_script(script_path):
    """Parse script file into metadata + list of (type, value) segments."""
    text = Path(script_path).read_text(encoding='utf-8')

    if '---' not in text:
        print("ERROR: Script missing --- separator")
        sys.exit(1)

    header, body = text.split('---', 1)
    body = body.strip()

    # Parse metadata
    metadata = {'category': 'mindfulness', 'ambient': None}
    for line in header.strip().split('\n'):
        line = line.strip()
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip().lower()
            val = val.strip()
            if key in ('duration', 'category', 'ambient', 'style'):
                metadata[key] = val.lower() if key in ('category', 'ambient') else val
                if key == 'ambient' and val.lower() == 'none':
                    metadata['ambient'] = None
        elif line and 'title' not in metadata:
            metadata['title'] = line

    category = metadata.get('category', 'mindfulness')
    profile = PAUSE_PROFILES.get(category, PAUSE_PROFILES['mindfulness'])

    # Parse body into segments
    segments = []
    lines = body.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Explicit pause: [45 second pause] or [PAUSE: 60 seconds]
        m = re.match(r'\[(?:PAUSE:\s*)?(\d+)\s*second\s*pause\]', line, re.I)
        if not m:
            m = re.match(r'\[(?:SILENCE:\s*)?(\d+)\s*seconds?\]', line, re.I)
        if m:
            segments.append(("silence", int(m.group(1))))
            i += 1
            continue

        # ... pause markers — count consecutive
        if line == '...':
            dot_count = 1
            j = i + 1
            while j < len(lines):
                nl = lines[j].strip()
                if nl == '...':
                    dot_count += 1
                    j += 1
                elif nl == '':
                    j += 1
                else:
                    break
            level = min(dot_count, 3)
            lo, hi = profile[level]
            duration = round(random.uniform(lo, hi), 1)
            segments.append(("silence", duration))
            i = j
            continue

        # Text block
        segments.append(("text", line))
        i += 1

    return metadata, segments


# ============================================================================
# TTS GENERATION
# ============================================================================

def estimate_duration(text):
    """Meditation pace ~0.065s per char."""
    return len(text) * 0.065


def generate_tts(text, output_path, max_retries=3):
    """Generate TTS via Fish Audio with validation and retry."""
    import requests

    if not API_KEY:
        print("ERROR: FISH_API_KEY not set")
        sys.exit(1)

    expected = estimate_duration(text)

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"       Retry {attempt}/{max_retries}...")
            time.sleep(1)

        try:
            resp = requests.post(
                FISH_API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "model": "s1",
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "format": "mp3",
                    "reference_id": FISH_VOICE_ID,
                },
                timeout=30,
            )
        except Exception as e:
            print(f"       Network error: {e}")
            continue

        if resp.status_code != 200:
            print(f"       API error: {resp.status_code}")
            continue

        Path(output_path).write_bytes(resp.content)

        if os.path.getsize(output_path) < 1000:
            print(f"       File too small ({os.path.getsize(output_path)} bytes)")
            continue

        # Get actual duration
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", output_path
        ], capture_output=True, text=True)

        try:
            duration = float(result.stdout.strip())
        except:
            print(f"       Could not read duration")
            continue

        if duration < 0.5:
            print(f"       Too short ({duration:.2f}s)")
            continue

        return True, duration, expected

    print(f"       *** ALL {max_retries} ATTEMPTS FAILED ***")
    return False, 0, expected


def generate_silence(seconds, output_path):
    """Generate silence WAV file."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"anullsrc=r={SAMPLE_RATE}:cl=stereo",
        "-t", str(seconds),
        "-acodec", "pcm_s16le", output_path
    ], capture_output=True)


# ============================================================================
# AMBIENT MIXING
# ============================================================================

def mix_ambient(voice_path, ambient_name, output_path):
    """Mix ambient loop under voice track."""
    ambient_path = AMBIENT_DIR / f"{ambient_name}.mp3"
    if not ambient_path.exists():
        print(f"  WARNING: Ambient '{ambient_name}' not found, skipping")
        shutil.copy(voice_path, output_path)
        return

    duration = float(subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", voice_path
    ], capture_output=True, text=True).stdout.strip())

    fade_out_start = max(0, duration - AMBIENT_FADE_OUT)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", voice_path,
        "-stream_loop", "-1", "-i", str(ambient_path),
        "-filter_complex",
        f"[1:a]volume={AMBIENT_VOLUME_DB}dB,"
        f"afade=t=in:st=0:d={AMBIENT_FADE_IN}:curve=log,"
        f"afade=t=out:st={fade_out_start}:d={AMBIENT_FADE_OUT}[amb];"
        f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2",
        "-t", str(duration),
        "-c:a", "libmp3lame", "-b:a", "128k", output_path
    ], capture_output=True)
    print(f"  Ambient '{ambient_name}' mixed at {AMBIENT_VOLUME_DB}dB")


# ============================================================================
# MAIN BUILD
# ============================================================================

def build_session(session_name, with_ambient=False, mix_only=False):
    script_path = SCRIPT_DIR / f"{session_name}.txt"
    output_path = OUTPUT_DIR / f"{session_name}.mp3"
    manifest_path = OUTPUT_DIR / f"{session_name}_manifest.json"

    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        sys.exit(1)

    metadata, segments = parse_script(script_path)
    ambient = metadata.get('ambient')

    print(f"=== Building: {session_name} ===")
    print(f"Title:    {metadata.get('title', '?')}")
    print(f"Category: {metadata.get('category', '?')}")
    print(f"Ambient:  {ambient or 'none'}")

    text_segs = [s for s in segments if s[0] == 'text']
    sil_segs = [s for s in segments if s[0] == 'silence']
    total_planned_silence = sum(s[1] for s in sil_segs)
    print(f"Segments: {len(text_segs)} text, {len(sil_segs)} silence ({total_planned_silence:.0f}s planned)")
    print()

    if mix_only:
        if not output_path.exists():
            print(f"ERROR: No audio file to mix: {output_path}")
            sys.exit(1)
        if ambient:
            mixed_path = output_path.with_name(output_path.stem + "-mixed.mp3")
            mix_ambient(str(output_path), ambient, str(mixed_path))
            print(f"Mixed output: {mixed_path}")
        else:
            print("No ambient specified.")
        return

    # --- Full build ---
    tmpdir = tempfile.mkdtemp()
    part_files = []
    text_count = 0
    total_tts_duration = 0
    total_expected_duration = 0
    total_silence_actual = 0
    manifest_segments = []
    cumulative = 0

    for i, (stype, value) in enumerate(segments):
        part_path = os.path.join(tmpdir, f"part_{i:03d}.wav")
        seg_info = {"index": i, "type": stype, "start_time": round(cumulative, 2)}

        if stype == "text":
            text_count += 1
            mp3_path = os.path.join(tmpdir, f"tts_{i:03d}.mp3")
            display = value[:60] + "..." if len(value) > 60 else value
            print(f"  [{text_count:02d}] {display}")

            success, duration, expected = generate_tts(value, mp3_path)
            if not success:
                print(f"\n*** BUILD FAILED — TTS failed for segment {text_count} ***")
                shutil.rmtree(tmpdir)
                sys.exit(1)

            print(f"       {duration:.2f}s (expected ~{expected:.1f}s)")
            total_tts_duration += duration
            total_expected_duration += expected

            seg_info["text"] = value
            seg_info["duration"] = round(duration, 2)
            seg_info["expected"] = round(expected, 2)
            cumulative += duration

            subprocess.run([
                "ffmpeg", "-y", "-i", mp3_path,
                "-ar", str(SAMPLE_RATE), "-ac", "2", "-acodec", "pcm_s16le", part_path
            ], capture_output=True)

        else:  # silence
            sil_dur = value
            print(f"  [--] {sil_dur}s silence")
            generate_silence(sil_dur, part_path)
            seg_info["duration"] = sil_dur
            total_silence_actual += sil_dur
            cumulative += sil_dur

        seg_info["end_time"] = round(cumulative, 2)
        manifest_segments.append(seg_info)
        part_files.append(part_path)

    # Summary
    print(f"\n{'='*50}")
    print(f"TTS segments:  {text_count}")
    print(f"TTS duration:  {total_tts_duration:.1f}s")
    print(f"Silence:       {total_silence_actual:.0f}s")
    print(f"Est. total:    {cumulative:.0f}s ({cumulative/60:.1f} min)")
    print(f"{'='*50}")

    # Save manifest
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump({
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "script": session_name,
            "category": metadata.get('category', ''),
            "ambient": ambient,
            "total_tts_duration": round(total_tts_duration, 2),
            "total_silence": round(total_silence_actual, 2),
            "text_segments": text_count,
            "segments": manifest_segments
        }, f, indent=2)
    print(f"Manifest: {manifest_path}")

    # Concatenate all parts
    concat_list = os.path.join(tmpdir, "concat.txt")
    with open(concat_list, 'w') as f:
        for p in part_files:
            f.write(f"file '{p}'\n")

    concat_wav = os.path.join(tmpdir, "full.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-acodec", "pcm_s16le", concat_wav
    ], capture_output=True)

    # Normalize and encode (no ambient yet — raw narration)
    subprocess.run([
        "ffmpeg", "-y", "-i", concat_wav,
        "-af", "loudnorm=I=-24:TP=-2:LRA=11",
        "-codec:a", "libmp3lame", "-b:a", "128k", str(output_path)
    ], capture_output=True)

    # If requested, mix ambient on top
    if with_ambient and ambient:
        raw_path = output_path.with_name(output_path.stem + "-raw.mp3")
        shutil.copy(str(output_path), str(raw_path))
        mix_ambient(str(raw_path), ambient, str(output_path))
        os.remove(str(raw_path))

    # Final info
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)
    ], capture_output=True, text=True)
    final_dur = float(result.stdout.strip())

    print(f"\nOutput: {output_path}")
    print(f"Duration: {final_dur:.0f}s ({final_dur/60:.1f} min)")

    shutil.rmtree(tmpdir)

    if not with_ambient:
        print(f"\nNext step: python3 analyze_audio_v5.py {output_path}")


def list_sessions():
    """List all scripts."""
    print("\nAvailable sessions:")
    for script in sorted(SCRIPT_DIR.glob("*.txt")):
        if script.name in ("TEMPLATE.txt", "liability-check.sh"):
            continue
        name = script.stem
        audio = OUTPUT_DIR / f"{name}.mp3"
        status = "BUILT" if audio.exists() else "    "
        print(f"  [{status}] {name}")


def main():
    parser = argparse.ArgumentParser(description="Salus Session Builder v3")
    parser.add_argument('session', nargs='?', help='Session name')
    parser.add_argument('--with-ambient', action='store_true', help='Mix ambient after build')
    parser.add_argument('--mix-only', action='store_true', help='Only add ambient to existing audio')
    parser.add_argument('--list', action='store_true', help='List sessions')
    args = parser.parse_args()

    if args.list:
        list_sessions()
    elif args.session:
        build_session(args.session, with_ambient=args.with_ambient, mix_only=args.mix_only)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
