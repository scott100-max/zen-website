#!/usr/bin/env python3
"""
Rebuild session audio with:
1. Proper meditation pauses (up to 1:45 like Calm)
2. Themed ambient backgrounds layered underneath

Uses PROVEN stability techniques:
- DC offset removal (highpass=f=10)
- Correct 5ms fades on each TTS segment
- Crossfade joins at PCM level to prevent clicks
"""
import os, subprocess, requests, tempfile, shutil, wave, array, random, sys

# Load .env
for line in open('.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k] = v

API_KEY = os.environ.get("FISH_API_KEY", "")
VOICE_ID = "0165567b33324f518b02336ad232e31a"
OUTPUT_DIR = "content/audio"
BACKUP_DIR = "content/audio-backup"
AMBIENT_DIR = "content/audio/ambient"
RATE = 44100

# Pause profiles: (min_seconds, max_seconds)
PAUSE_PROFILES = {
    'sleep': {1: (8, 15), 2: (25, 45), 3: (60, 105)},
    'focus': {1: (3, 6), 2: (8, 15), 3: (15, 30)},
    'stress': {1: (5, 10), 2: (15, 30), 3: (30, 60)},
    'mindfulness': {1: (5, 12), 2: (20, 40), 3: (45, 75)},
    'beginner': {1: (4, 8), 2: (12, 25), 3: (25, 45)},
    'advanced': {1: (8, 15), 2: (30, 60), 3: (75, 105)},
}

# Sessions: name -> (category, ambient_sound)
SESSIONS = {
    # Sleep - night/ocean themed
    "05-body-scan-deep-rest": ("sleep", "night"),
    "06-letting-go-of-the-day": ("sleep", "night"),
    "07-moonlight-drift": ("sleep", "night"),
    "08-sleep-stories-quiet-shore": ("sleep", "ocean"),
    "09-rainfall-sleep-journey": ("sleep", "rain"),
    "10-counting-down-to-sleep": ("sleep", "night"),
    "11-lucid-dream-preparation": ("sleep", "night"),

    # Focus - library/work themed
    "12-five-minute-reset": ("focus", "piano"),
    "13-flow-state": ("focus", "library"),
    "14-morning-clarity": ("focus", "birds"),
    "15-deep-work-prep": ("focus", "library"),
    "16-peak-performance": ("focus", "piano"),
    "17-deep-work-mode": ("focus", "library"),

    # Stress - water/nature themed
    "18-calm-in-three-minutes": ("stress", "stream"),
    "19-release-and-restore": ("stress", "stream"),
    "20-tension-melt": ("stress", "rain"),
    "21-anxiety-unravelled": ("stress", "rain"),
    "22-releasing-tension": ("stress", "wind"),
    "23-the-calm-reset": ("stress", "stream"),
    "24-anger-frustration-release": ("stress", "waterfall"),

    # Mindfulness - temple/nature themed
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

    # Beginner - gentle sounds
    "35-your-first-meditation": ("beginner", "wind"),
    "36-loving-kindness-intro": ("beginner", "chimes"),
    "37-building-a-daily-practice": ("beginner", "garden"),
    "38-seven-day-mindfulness-day1": ("beginner", "garden"),

    # Advanced - temple/spiritual
    "39-yoga-nidra": ("advanced", "temple"),
    "40-gratitude-before-sleep": ("sleep", "night"),
    "41-vipassana-insight": ("advanced", "temple"),
    "42-chakra-alignment": ("advanced", "chimes"),
    "43-non-dual-awareness": ("advanced", "wind"),
    "44-transcendental-stillness": ("advanced", "temple"),
}

# Ambient volume (dB reduction from narration)
AMBIENT_VOLUME = -18  # Quiet but present


def get_pause_duration(dot_count, category):
    profile = PAUSE_PROFILES.get(category, PAUSE_PROFILES['mindfulness'])
    level = min(dot_count, 3)
    min_sec, max_sec = profile[level]
    return random.randint(min_sec, max_sec)


def parse_script(filepath, category):
    segments = []
    with open(filepath) as f:
        content = f.read()

    for para in content.split('\n\n'):
        para = para.strip()
        if not para:
            continue
        if all(line.strip() == '...' for line in para.split('\n') if line.strip()):
            dot_count = len([l for l in para.split('\n') if l.strip() == '...'])
            duration = get_pause_duration(dot_count, category)
            segments.append(('silence', duration))
        elif para == '[gentle silence]':
            segments.append(('silence', random.randint(90, 120)))
        else:
            text = ' '.join(para.split())
            if text and text != '...':
                segments.append(('text', text))
    return segments


def tts_to_wav(text, idx, tmpdir):
    mp3 = os.path.join(tmpdir, f"tts_{idx:03d}.mp3")
    wav = os.path.join(tmpdir, f"tts_{idx:03d}.wav")

    resp = requests.post(
        "https://api.fish.audio/v1/tts",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"text": text, "format": "mp3", "reference_id": VOICE_ID},
        timeout=120,
    )
    if resp.status_code != 200:
        print(f"    ERROR: {resp.status_code} - {resp.text[:200]}")
        return None

    with open(mp3, 'wb') as f:
        f.write(resp.content)

    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                       capture_output=True, text=True)
    dur = float(r.stdout.strip())
    fade_out_start = max(0, dur - 0.005)

    subprocess.run([
        "ffmpeg", "-y", "-i", mp3, "-ar", str(RATE), "-ac", "1", "-acodec", "pcm_s16le",
        "-af", f"highpass=f=10,afade=t=in:st=0:d=0.005,afade=t=out:st={fade_out_start}:d=0.005",
        wav
    ], capture_output=True)
    return wav


def read_samples(wav_path):
    with wave.open(wav_path, 'rb') as w:
        raw = w.readframes(w.getnframes())
    return array.array('h', raw)


def silence_samples(seconds):
    return array.array('h', [0] * int(RATE * seconds))


def crossfade_join(a, b, ms=5):
    fade = int(RATE * ms / 1000)
    if len(a) < fade or len(b) < fade:
        a.extend(b)
        return a
    for i in range(fade):
        mix = i / fade
        a_idx = len(a) - fade + i
        a[a_idx] = int(a[a_idx] * (1 - mix) + b[i] * mix)
    a.extend(b[fade:])
    return a


def mix_with_ambient(narration_path, ambient_name, output_path):
    """Mix narration with looped ambient background."""
    ambient_path = os.path.join(AMBIENT_DIR, f"{ambient_name}.mp3")

    if not os.path.exists(ambient_path):
        print(f"    Ambient not found: {ambient_path}, using narration only")
        shutil.copy(narration_path, output_path)
        return

    # Get narration duration
    r = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0",
        narration_path
    ], capture_output=True, text=True)
    duration = float(r.stdout.strip())

    # Mix: loop ambient to match duration, reduce volume, add fades, mix with narration
    # Ambient: fade in 5s, fade out 8s, volume reduced
    fade_out_start = max(0, duration - 8)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", narration_path,
        "-stream_loop", "-1", "-i", ambient_path,
        "-filter_complex",
        f"[1:a]atrim=0:{duration},volume={AMBIENT_VOLUME}dB,afade=t=in:d=5,afade=t=out:st={fade_out_start}:d=8[amb];"
        f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-codec:a", "libmp3lame", "-b:a", "192k",
        output_path
    ], capture_output=True)


def build_session(script_name, category, ambient):
    script_path = f"content/scripts/{script_name}.txt"
    output_path = f"{OUTPUT_DIR}/{script_name}.mp3"
    backup_path = f"{BACKUP_DIR}/{script_name}.mp3"

    if not os.path.exists(script_path):
        print(f"  SKIP: {script_path} not found")
        return False

    if os.path.exists(output_path) and not os.path.exists(backup_path):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copy(output_path, backup_path)
        print(f"  Backed up existing audio")

    print(f"\n{'='*60}")
    print(f"Building: {script_name}")
    print(f"Category: {category} | Ambient: {ambient}")
    print(f"{'='*60}")

    segments = parse_script(script_path, category)
    text_segs = sum(1 for s in segments if s[0] == 'text')
    silence_segs = [s[1] for s in segments if s[0] == 'silence']
    total_silence = sum(silence_segs)

    print(f"  Text segments: {text_segs}")
    print(f"  Silence: {len(silence_segs)} segments, {total_silence:.0f}s ({total_silence/60:.1f} min)")

    tmpdir = tempfile.mkdtemp()
    pcm = array.array('h')
    text_count = 0
    chars_used = 0

    for i, (stype, value) in enumerate(segments):
        if stype == "text":
            text_count += 1
            chars_used += len(value)
            preview = value[:50] + ('...' if len(value) > 50 else '')
            print(f"  [{text_count}] {preview}")
            wav = tts_to_wav(value, i, tmpdir)
            if wav is None:
                continue
            pcm = crossfade_join(pcm, read_samples(wav))
        else:
            print(f"  [silence {value}s]")
            pcm = crossfade_join(pcm, silence_samples(value))

    if len(pcm) == 0:
        print("  ERROR: No audio!")
        shutil.rmtree(tmpdir)
        return False

    # Write narration WAV
    narration_wav = os.path.join(tmpdir, "narration.wav")
    with wave.open(narration_wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())

    # Convert narration to MP3
    narration_mp3 = os.path.join(tmpdir, "narration.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-i", narration_wav,
        "-codec:a", "libmp3lame", "-b:a", "192k", narration_mp3
    ], capture_output=True)

    # Mix with ambient
    print(f"  Mixing with ambient: {ambient}")
    mix_with_ambient(narration_mp3, ambient, output_path)

    # Get final duration
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", output_path
    ], capture_output=True, text=True)
    try:
        duration = float(r.stdout.strip())
        print(f"\n  DONE! {duration:.0f}s ({duration/60:.1f} min)")
        print(f"  TTS: {text_count} calls, {chars_used:,} chars")
    except:
        print(f"  Done!")

    shutil.rmtree(tmpdir)
    return True


def estimate_usage():
    total = 0
    for name in SESSIONS:
        path = f"content/scripts/{name}.txt"
        if os.path.exists(path):
            with open(path) as f:
                for para in f.read().split('\n\n'):
                    para = para.strip()
                    if para and not all(l.strip() == '...' for l in para.split('\n') if l.strip()):
                        if para != '[gentle silence]':
                            total += len(para)
    return total


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    chars = estimate_usage()
    print(f"Estimated: {chars:,} characters (~${chars/1000000*15:.2f})")
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

    items = list(SESSIONS.items())
    total = len(items)
    success = failed = 0

    for idx, (name, (category, ambient)) in enumerate(items[start:], start=start):
        print(f"\n[{idx+1}/{total}] {name}")
        try:
            if build_session(name, category, ambient):
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"COMPLETE: {success} ok, {failed} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
