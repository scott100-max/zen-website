#!/usr/bin/env python3
"""
Build 10-minute morning meditation audio using Fish Audio TTS.
Generates each segment, splices with FFmpeg silence.
"""
import os, subprocess, requests, tempfile, shutil

# Load .env
for line in open('.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k] = v

API_KEY = os.environ.get("FISH_API_KEY", "")
VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Calm voice
OUTPUT = "content/audio-free/01-morning-meditation.mp3"

segments = [
    ("text", "Welcome to Salus."),
    ("silence", 3),
    ("text", "This is your ten-minute morning meditation — a gentle way to start your day with clarity and intention."),
    ("silence", 4),
    ("text", "Find a comfortable position. You can sit upright or lie down — whatever feels right for you this morning."),
    ("silence", 4),
    ("text", "Let your hands rest naturally. Close your eyes when you're ready."),
    ("silence", 5),
    ("text", "Take a deep breath in through your nose."),
    ("silence", 5),
    ("text", "And slowly out through your mouth."),
    ("silence", 5),
    ("text", "Again. Breathe in, filling your lungs completely."),
    ("silence", 5),
    ("text", "And release, letting go of anything you carried from sleep."),
    ("silence", 6),
    ("text", "Begin to notice your body."),
    ("silence", 3),
    ("text", "Feel the weight of your head. Your shoulders. Let them soften."),
    ("silence", 5),
    ("text", "Feel the support beneath you — the chair, the floor, the bed."),
    ("silence", 4),
    ("text", "You're held. You're safe."),
    ("silence", 5),
    ("text", "Scan down through your arms. Your hands."),
    ("silence", 4),
    ("text", "Notice any tension and let it dissolve with your next exhale."),
    ("silence", 6),
    ("text", "Move your awareness down through your torso. Your hips. Your legs. All the way to your feet."),
    ("silence", 5),
    ("text", "Just noticing. No need to change anything."),
    ("silence", 7),
    ("text", "Now bring your attention to your breath."),
    ("silence", 4),
    ("text", "Don't try to control it — just observe."),
    ("silence", 5),
    ("text", "Notice the cool air entering your nostrils. The gentle rise of your chest. The warm air leaving your body."),
    ("silence", 8),
    ("text", "Each breath is a small beginning."),
    ("silence", 4),
    ("text", "Each inhale is an invitation."),
    ("silence", 4),
    ("text", "Each exhale is a release."),
    ("silence", 8),
    ("text", "If your mind wanders — and it will — that's perfectly natural."),
    ("silence", 4),
    ("text", "Simply notice where it went, and gently guide your attention back to the breath."),
    ("silence", 4),
    ("text", "No judgment. Just returning."),
    ("silence", 10),
    ("text", "You're doing beautifully. Stay with the breath."),
    ("silence", 15),
    ("text", "Now, keeping your eyes closed, I'd like you to think about the day ahead."),
    ("silence", 4),
    ("text", "Not the tasks or the schedule — just the feeling you want to carry with you."),
    ("silence", 6),
    ("text", "Maybe it's calm."),
    ("silence", 3),
    ("text", "Maybe it's focus."),
    ("silence", 3),
    ("text", "Maybe it's kindness — toward yourself and others."),
    ("silence", 5),
    ("text", "Choose one word. One intention. Let it settle in your mind like a stone in still water."),
    ("silence", 8),
    ("text", "Hold that word gently. Don't grip it — just let it be there."),
    ("silence", 5),
    ("text", "This is your anchor for the day. When things feel rushed or uncertain, you can return to this word."),
    ("silence", 4),
    ("text", "It's always there for you."),
    ("silence", 8),
    ("text", "Before we begin to close, take a moment to feel grateful."),
    ("silence", 4),
    ("text", "Not for anything specific — though you can if you'd like — but simply for this moment."),
    ("silence", 4),
    ("text", "For the fact that you chose to be here, to begin your day with stillness."),
    ("silence", 6),
    ("text", "Gratitude has a way of softening us. It opens a small door that lets light in."),
    ("silence", 4),
    ("text", "Even on difficult days, this moment is yours."),
    ("silence", 8),
    ("text", "Now, gently begin to bring your awareness back to the room."),
    ("silence", 4),
    ("text", "Feel the surface beneath you."),
    ("silence", 3),
    ("text", "Notice any sounds around you — the hum of the morning."),
    ("silence", 5),
    ("text", "Wiggle your fingers and toes."),
    ("silence", 4),
    ("text", "Take one more deep breath in."),
    ("silence", 5),
    ("text", "And a long, slow exhale."),
    ("silence", 6),
    ("text", "When you're ready, open your eyes."),
    ("silence", 4),
    ("text", "Take in the light."),
    ("silence", 5),
    ("text", "You've given yourself a gift this morning — ten minutes of stillness that will carry through the hours ahead."),
    ("silence", 5),
    ("text", "Thank you for practising with Salus."),
    ("silence", 3),
    ("text", "Sleep. Relax. Restore."),
    ("silence", 3),
]


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
        f"anullsrc=r=44100:cl=stereo", "-t", str(seconds),
        "-acodec", "pcm_s16le", output_path
    ], capture_output=True)


def main():
    tmpdir = tempfile.mkdtemp()
    print(f"Working in {tmpdir}")

    part_files = []
    text_count = 0

    for i, (stype, value) in enumerate(segments):
        part_path = os.path.join(tmpdir, f"part_{i:03d}.wav")

        if stype == "text":
            text_count += 1
            mp3_path = os.path.join(tmpdir, f"tts_{i:03d}.mp3")
            print(f"  [{text_count}] TTS: {value[:60]}...")
            if not generate_tts(value, mp3_path):
                print("    Failed! Skipping.")
                continue
            subprocess.run([
                "ffmpeg", "-y", "-i", mp3_path,
                "-ar", "44100", "-ac", "2", "-acodec", "pcm_s16le", part_path
            ], capture_output=True)
        else:
            print(f"  [silence] {value}s")
            generate_silence(value, part_path)

        part_files.append(part_path)

    concat_list = os.path.join(tmpdir, "concat.txt")
    with open(concat_list, 'w') as f:
        for p in part_files:
            f.write(f"file '{p}'\n")

    concat_wav = os.path.join(tmpdir, "full.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-acodec", "pcm_s16le", concat_wav
    ], capture_output=True)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    # Normalize to -24 LUFS with -2 dBTP ceiling, encode at 128kbps stereo
    subprocess.run([
        "ffmpeg", "-y", "-i", concat_wav,
        "-af", "loudnorm=I=-24:TP=-2:LRA=11",
        "-codec:a", "libmp3lame", "-b:a", "128k", OUTPUT
    ], capture_output=True)

    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", OUTPUT
    ], capture_output=True, text=True)
    duration = float(result.stdout.strip())
    print(f"\nDone! Output: {OUTPUT}")
    print(f"Duration: {duration:.0f}s ({duration/60:.1f} min)")
    print(f"TTS calls: {text_count}")

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    main()
