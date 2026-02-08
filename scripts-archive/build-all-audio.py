#!/usr/bin/env python3
"""
Batch build ALL session audio using Fish Audio TTS.
Reads each script .txt file, splits into text segments and pauses,
generates TTS for each text segment, adds silence for pauses,
concatenates into final MP3.
"""
import os, subprocess, requests, tempfile, shutil, sys, re

# Load .env
for line in open('.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k] = v

API_KEY = os.environ.get("FISH_API_KEY", "")
VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Same calm male voice
OUTPUT_DIR = "content/audio"

# Scripts to process (05-44)
SCRIPTS = [
    "05-body-scan-deep-rest",
    "06-letting-go-of-the-day",
    "07-moonlight-drift",
    "08-sleep-stories-quiet-shore",
    "09-rainfall-sleep-journey",
    "10-counting-down-to-sleep",
    "11-lucid-dream-preparation",
    "12-five-minute-reset",
    "13-flow-state",
    "14-morning-clarity",
    "15-deep-work-prep",
    "16-peak-performance",
    "17-deep-work-mode",
    "18-calm-in-three-minutes",
    "19-release-and-restore",
    "20-tension-melt",
    "21-anxiety-unravelled",
    "22-releasing-tension",
    "23-the-calm-reset",
    "24-anger-frustration-release",
    "25-introduction-to-mindfulness",
    "26-body-scan-meditation",
    "27-mindful-breathing",
    "28-letting-go-of-thoughts",
    "29-open-awareness",
    "30-mindful-walking",
    "31-mindfulness-at-work",
    "32-observing-emotions",
    "33-morning-mindfulness",
    "34-mindful-eating",
    "35-your-first-meditation",
    "36-loving-kindness-intro",
    "37-building-a-daily-practice",
    "38-seven-day-mindfulness-day1",
    "39-yoga-nidra",
    "40-gratitude-before-sleep",
    "41-vipassana-insight",
    "42-chakra-alignment",
    "43-non-dual-awareness",
    "44-transcendental-stillness",
]


def parse_script(filepath):
    """Parse a script .txt file into segments of (type, value).
    Text paragraphs become ('text', paragraph).
    Lines with just '...' become ('silence', 2.5) seconds each.
    """
    segments = []
    with open(filepath) as f:
        content = f.read()

    paragraphs = content.split('\n\n')
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Check if it's a silence marker
        if all(line.strip() == '...' for line in para.split('\n') if line.strip()):
            count = len([l for l in para.split('\n') if l.strip() == '...'])
            segments.append(('silence', count * 2.5))
        elif para == '[gentle silence]':
            segments.append(('silence', 10))
        else:
            # It's narration text - clean it up
            text = ' '.join(para.split())
            if text and text != '...':
                segments.append(('text', text))

    return segments


def generate_tts(text, output_path):
    """Generate TTS audio via Fish Audio."""
    resp = requests.post(
        "https://api.fish.audio/v1/tts",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "model": "s1",
            "Content-Type": "application/json",
        },
        json={"text": text, "format": "mp3", "reference_id": VOICE_ID},
        timeout=120,
    )
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code} - {resp.text[:200]}")
        return False
    with open(output_path, 'wb') as f:
        f.write(resp.content)
    return True


def generate_silence(seconds, output_path):
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"anullsrc=r=44100:cl=mono", "-t", str(seconds),
        "-acodec", "pcm_s16le", output_path
    ], capture_output=True)


def build_session(script_name):
    """Build a single session audio from its script."""
    script_path = f"content/scripts/{script_name}.txt"
    output_path = f"{OUTPUT_DIR}/{script_name}.mp3"

    if not os.path.exists(script_path):
        print(f"  SKIP: {script_path} not found")
        return False

    if os.path.exists(output_path):
        print(f"  SKIP: {output_path} already exists")
        return True

    print(f"\n{'='*60}")
    print(f"Building: {script_name}")
    print(f"{'='*60}")

    segments = parse_script(script_path)
    print(f"  Segments: {len(segments)} ({sum(1 for s in segments if s[0]=='text')} text, {sum(1 for s in segments if s[0]=='silence')} silence)")

    tmpdir = tempfile.mkdtemp()
    part_files = []
    text_count = 0

    for i, (stype, value) in enumerate(segments):
        part_path = os.path.join(tmpdir, f"part_{i:04d}.wav")

        if stype == "text":
            text_count += 1
            mp3_path = os.path.join(tmpdir, f"tts_{i:04d}.mp3")
            preview = value[:70] + ('...' if len(value) > 70 else '')
            print(f"  [{text_count}] TTS: {preview}")
            if not generate_tts(value, mp3_path):
                print("    Failed! Skipping segment.")
                continue
            subprocess.run([
                "ffmpeg", "-y", "-i", mp3_path,
                "-ar", "44100", "-ac", "1", "-acodec", "pcm_s16le", part_path
            ], capture_output=True)
        else:
            print(f"  [silence] {value}s")
            generate_silence(value, part_path)

        if os.path.exists(part_path):
            part_files.append(part_path)

    if not part_files:
        print("  ERROR: No parts generated!")
        shutil.rmtree(tmpdir)
        return False

    # Concatenate
    concat_list = os.path.join(tmpdir, "concat.txt")
    with open(concat_list, 'w') as f:
        for p in part_files:
            f.write(f"file '{p}'\n")

    concat_wav = os.path.join(tmpdir, "full.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-acodec", "pcm_s16le", concat_wav
    ], capture_output=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", concat_wav,
        "-codec:a", "libmp3lame", "-b:a", "192k", output_path
    ], capture_output=True)

    # Get duration
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", output_path
    ], capture_output=True, text=True)
    try:
        duration = float(result.stdout.strip())
        print(f"  Done! Duration: {duration:.0f}s ({duration/60:.1f} min)")
    except:
        print(f"  Done! (couldn't read duration)")

    print(f"  TTS calls: {text_count}")
    shutil.rmtree(tmpdir)
    return True


def main():
    # Allow specifying start index
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total = len(SCRIPTS)
    success = 0
    failed = 0

    for idx, name in enumerate(SCRIPTS[start:], start=start):
        print(f"\n[{idx+1}/{total}] Processing {name}...")
        try:
            if build_session(name):
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"COMPLETE: {success} succeeded, {failed} failed out of {total}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
