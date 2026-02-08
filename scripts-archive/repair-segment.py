#!/usr/bin/env python3
"""
Targeted segment repair with crossfade for smooth splicing.
"""
import os, subprocess, requests, tempfile, shutil

# Load .env
for line in open('.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k] = v

API_KEY = os.environ.get("FISH_API_KEY", "")
VOICE_ID = "0165567b33324f518b02336ad232e31a"

# We need the ORIGINAL audio before any repairs
# Let me rebuild just the problem segment area fresh
INPUT = "content/audio-free/01-morning-meditation.mp3"
OUTPUT = "content/audio-free/01-morning-meditation.mp3"

# The glitch is at 0:38 - that's in "Take a deep breath in through your nose."
# Cut during SILENCE (cleaner) - before and after the text segment
# Segment 7 = 5s silence ending at ~34s
# Segment 8 = text "Take a deep breath..."
# Segment 9 = 5s silence starting at ~38s

# Cut in the middle of silences for cleanest splice
CUT_BEFORE = 32.0   # Middle of silence before the text
CUT_AFTER = 41.0    # Middle of silence after the text

REPAIR_TEXT = "Take a deep breath in through your nose."
CROSSFADE_MS = 50  # 50ms crossfade

def generate_tts(text, output_path):
    resp = requests.post(
        "https://api.fish.audio/v1/tts",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "model": "s1",
            "Content-Type": "application/json",
        },
        json={"text": text, "format": "mp3", "reference_id": VOICE_ID},
    )
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code} - {resp.text[:200]}")
        return False
    with open(output_path, 'wb') as f:
        f.write(resp.content)
    return True


def main():
    if not API_KEY:
        print("ERROR: FISH_API_KEY not found")
        return

    tmpdir = tempfile.mkdtemp()
    print(f"Working in {tmpdir}")
    print(f"Cutting at silence points: {CUT_BEFORE}s and {CUT_AFTER}s")

    # Step 1: Generate new TTS
    print("\n[1] Generating fresh TTS...")
    tts_mp3 = os.path.join(tmpdir, "tts_new.mp3")
    if not generate_tts(REPAIR_TEXT, tts_mp3):
        shutil.rmtree(tmpdir)
        return

    tts_wav = os.path.join(tmpdir, "tts_new.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", tts_mp3,
        "-ar", "44100", "-ac", "2", "-acodec", "pcm_s16le", tts_wav
    ], capture_output=True)

    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", tts_wav
    ], capture_output=True, text=True)
    tts_duration = float(result.stdout.strip())
    print(f"  TTS duration: {tts_duration:.2f}s")

    # Step 2: Create silence padding (to match original timing)
    # Original segment was ~4s text + we're cutting 9s total (32-41)
    # So we need: silence + tts + silence = 9s
    silence_before = 2.0  # 2s silence before text
    silence_after = 9.0 - tts_duration - silence_before  # remaining silence

    print(f"  Padding: {silence_before}s silence + {tts_duration:.1f}s TTS + {silence_after:.1f}s silence")

    silence_a = os.path.join(tmpdir, "silence_a.wav")
    silence_b = os.path.join(tmpdir, "silence_b.wav")

    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(silence_before), "-acodec", "pcm_s16le", silence_a
    ], capture_output=True)

    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(max(0.5, silence_after)), "-acodec", "pcm_s16le", silence_b
    ], capture_output=True)

    # Create the replacement chunk: silence + tts + silence
    chunk_list = os.path.join(tmpdir, "chunk.txt")
    with open(chunk_list, 'w') as f:
        f.write(f"file '{silence_a}'\n")
        f.write(f"file '{tts_wav}'\n")
        f.write(f"file '{silence_b}'\n")

    chunk_wav = os.path.join(tmpdir, "chunk.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", chunk_list, "-acodec", "pcm_s16le", chunk_wav
    ], capture_output=True)

    # Step 3: Extract parts from original with slight overlap for crossfade
    print("\n[2] Extracting with crossfade overlap...")

    fade_sec = CROSSFADE_MS / 1000.0

    part_a = os.path.join(tmpdir, "part_a.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", INPUT,
        "-t", str(CUT_BEFORE + fade_sec),
        "-ar", "44100", "-ac", "2", "-acodec", "pcm_s16le", part_a
    ], capture_output=True)

    part_b = os.path.join(tmpdir, "part_b.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", INPUT,
        "-ss", str(CUT_AFTER - fade_sec),
        "-ar", "44100", "-ac", "2", "-acodec", "pcm_s16le", part_b
    ], capture_output=True)

    # Step 4: Apply fades to chunk
    chunk_faded = os.path.join(tmpdir, "chunk_faded.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", chunk_wav,
        "-af", f"afade=t=in:st=0:d={fade_sec},afade=t=out:st={9.0-fade_sec}:d={fade_sec}",
        "-acodec", "pcm_s16le", chunk_faded
    ], capture_output=True)

    # Apply fades to parts
    part_a_faded = os.path.join(tmpdir, "part_a_faded.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", part_a,
        "-af", f"afade=t=out:st={CUT_BEFORE}:d={fade_sec}",
        "-acodec", "pcm_s16le", part_a_faded
    ], capture_output=True)

    part_b_faded = os.path.join(tmpdir, "part_b_faded.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", part_b,
        "-af", f"afade=t=in:st=0:d={fade_sec}",
        "-acodec", "pcm_s16le", part_b_faded
    ], capture_output=True)

    # Step 5: Concatenate with acrossfade filter
    print("\n[3] Splicing with crossfade...")

    # Use filter_complex for proper crossfade
    merged_wav = os.path.join(tmpdir, "merged.wav")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", part_a, "-i", chunk_wav, "-i", part_b,
        "-filter_complex",
        f"[0][1]acrossfade=d={fade_sec}:c1=tri:c2=tri[a01];[a01][2]acrossfade=d={fade_sec}:c1=tri:c2=tri[out]",
        "-map", "[out]",
        "-acodec", "pcm_s16le", merged_wav
    ], capture_output=True)

    # Step 6: Normalize and encode
    print("\n[4] Normalizing...")
    subprocess.run([
        "ffmpeg", "-y", "-i", merged_wav,
        "-af", "loudnorm=I=-24:TP=-2:LRA=11",
        "-codec:a", "libmp3lame", "-b:a", "128k", OUTPUT
    ], capture_output=True)

    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", OUTPUT
    ], capture_output=True, text=True)
    duration = float(result.stdout.strip())

    print(f"\nDone! {OUTPUT}")
    print(f"Duration: {duration:.0f}s ({duration/60:.1f} min)")

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    main()
