#!/usr/bin/env python3
"""
Build breathing-for-anxiety audio using Fish Audio TTS.
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
OUTPUT = "content/audio/03-breathing-for-anxiety.mp3"

segments = [
    ("text", "Welcome to Salus. If you're feeling anxious right now, I want you to know: you're in the right place. And you're going to feel better."),
    ("silence", 2),
    ("text", "When you're anxious, your body activates its fight-or-flight response. Your heart rate increases, your breathing gets shallow, and your muscles tense. This is your nervous system trying to protect you."),
    ("silence", 1.5),
    ("text", "But here's the key: your breath is the one part of this system you can control consciously. When you slow your exhale, you activate the vagus nerve, which signals your brain to switch from alert mode to rest and digest mode. It's not a trick. It's biology."),
    ("silence", 2),
    ("text", "Today I'm going to teach you two breathing techniques you can use anywhere, anytime. Let's begin."),
    ("silence", 2),
    ("text", "The first technique is called box breathing. It's used by everyone from Navy SEALs to therapists because it works quickly and reliably."),
    ("silence", 1),
    ("text", "The pattern is simple: breathe in for four counts, then breathe out for four. A steady, calming rhythm."),
    ("silence", 2),
    ("text", "Let's try it. Sit comfortably. Let your shoulders drop. I'll guide you through each phase. Just follow my voice."),
    ("silence", 3),

    # Box breathing round 1
    ("text", "Breathe in."),
    ("silence", 4),
    ("text", "Breathe out."),
    ("silence", 4),

    ("text", "Good. Let's do three more rounds together."),
    ("silence", 2),

    # Box breathing rounds 2-4
    ("text", "Breathe in."),
    ("silence", 4),
    ("text", "Breathe out."),
    ("silence", 4),

    ("text", "Breathe in."),
    ("silence", 4),
    ("text", "Breathe out."),
    ("silence", 4),

    ("text", "Breathe in."),
    ("silence", 4),
    ("text", "Breathe out."),
    ("silence", 4),

    ("text", "Notice how you feel. Even after a few rounds, most people report feeling noticeably calmer. That's the vagus nerve doing its job."),
    ("silence", 3),

    ("text", "The second technique was developed by Dr Andrew Weil and is particularly effective for acute anxiety and falling asleep."),
    ("silence", 1.5),
    ("text", "The pattern: breathe in through your nose for four counts, then exhale slowly through your mouth for eight. The long exhale is what activates your relaxation response."),
    ("silence", 2),
    ("text", "Let's practise. Place the tip of your tongue on the roof of your mouth, just behind your front teeth. Keep it there throughout."),
    ("silence", 3),

    # 4-7-8 round 1
    ("text", "Breathe in."),
    ("silence", 4),
    ("text", "Exhale slowly."),
    ("silence", 7),

    ("text", "Let's do that three more times."),
    ("silence", 2),

    # 4-7-8 rounds 2-4
    ("text", "Breathe in gently."),
    ("silence", 4),
    ("text", "And slowly breathe out."),
    ("silence", 7),

    ("text", "Breathe in again."),
    ("silence", 4),
    ("text", "And let it go."),
    ("silence", 7),

    ("text", "One more. Breathe in."),
    ("silence", 4),
    ("text", "And slowly breathe out."),
    ("silence", 7),

    ("silence", 2),
    ("text", "Beautiful. You might feel a little lightheaded. That's normal when you first practise. It passes quickly."),
    ("silence", 2),

    ("text", "You now have two tools that are always with you."),
    ("silence", 1),
    ("text", "Box breathing is best for in-the-moment calm. Before a meeting, during a stressful conversation, or whenever you feel your chest tightening."),
    ("silence", 1.5),
    ("text", "Four-seven-eight breathing is ideal for winding down. Before sleep, after a long day, or when anxious thoughts are spiralling."),
    ("silence", 2),
    ("text", "Start with four rounds and build up as it feels comfortable. The more you practise, the faster your body responds."),
    ("silence", 2),
    ("text", "You showed up for yourself today, and that matters. I'll see you next time on Salus."),
    ("silence", 2),
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
        json={"text": text, "format": "mp3", "reference_id": "0165567b33324f518b02336ad232e31a"},
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
                "-ar", "44100", "-ac", "1",
                "-acodec", "pcm_s16le", part_path
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
    subprocess.run([
        "ffmpeg", "-y", "-i", concat_wav,
        "-codec:a", "libmp3lame", "-b:a", "192k", OUTPUT
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
