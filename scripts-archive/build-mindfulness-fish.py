#!/usr/bin/env python3
"""
Build Science of Mindfulness audio using Fish Audio TTS.
Same voice as morning meditation. Educational/conversational tone.
Shorter pauses than meditation — this is narration, not guided practice.
"""
import os, subprocess, requests, tempfile, shutil

# Load .env
for line in open('.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k] = v

API_KEY = os.environ.get("FISH_API_KEY", "")
VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Same calm male voice
OUTPUT = "content/audio/04-science-of-mindfulness.mp3"

segments = [
    # Hook
    ("text", "What if I told you that sitting quietly for ten minutes a day could physically change the structure of your brain?"),
    ("silence", 2),
    ("text", "That it could calm the part responsible for fear and stress, while strengthening the areas linked to focus, empathy, and decision-making?"),
    ("silence", 3),
    ("text", "This isn't speculation. This is what decades of neuroscience research have shown us about mindfulness meditation."),
    ("silence", 2),
    ("text", "And today, we're going to look at exactly what happens inside your brain when you meditate."),
    ("silence", 3),

    # What is Mindfulness
    ("text", "Before we get into the science, let's define what we mean."),
    ("silence", 2),
    ("text", "Mindfulness is the practice of paying attention to the present moment — deliberately and without judgment."),
    ("silence", 2),
    ("text", "That last part is important. It's not about emptying your mind. It's not about achieving some blissful state."),
    ("silence", 2),
    ("text", "It's about noticing what's happening — your thoughts, your sensations, your emotions — and not reacting automatically."),
    ("silence", 3),
    ("text", "Think of it this way: most of the time, we're on autopilot. We're replaying the past or rehearsing the future."),
    ("silence", 2),
    ("text", "Mindfulness is the practice of stepping off that treadmill, even briefly, and seeing things as they actually are right now."),
    ("silence", 3),

    # Brain Science
    ("text", "So what does the research say? Let's look at three key brain changes."),
    ("silence", 3),

    # 1. Stress response
    ("text", "First: the stress response calms down."),
    ("silence", 2),
    ("text", "The amygdala is your brain's alarm system — it triggers the fight-or-flight response."),
    ("silence", 2),
    ("text", "A 2011 study at Harvard found that after just eight weeks of mindfulness practice, activity in the amygdala became significantly less reactive to stress."),
    ("silence", 2),
    ("text", "In other words, the part of your brain responsible for panic and anxiety learned to respond more calmly."),
    ("silence", 3),
    ("text", "And here's what's remarkable — participants weren't meditating during the brain scans."),
    ("silence", 2),
    ("text", "The changes persisted even when they weren't actively practising. The brain had adapted to a calmer baseline."),
    ("silence", 3),

    # 2. Prefrontal cortex
    ("text", "Second: the prefrontal cortex strengthens."),
    ("silence", 2),
    ("text", "The prefrontal cortex handles decision-making, focus, and self-awareness."),
    ("silence", 2),
    ("text", "Research from UCLA and other institutions has shown that regular meditators have stronger cortical regions in these areas."),
    ("silence", 2),
    ("text", "This supports healthy cognitive function as we age — suggesting meditation helps keep the mind sharp and resilient over time."),
    ("silence", 3),

    # 3. Default mode network
    ("text", "Third: the default mode network quiets down."),
    ("silence", 2),
    ("text", "The default mode network is the brain system active when your mind wanders — when you're ruminating, worrying, or daydreaming."),
    ("silence", 2),
    ("text", "Research from Yale University found that experienced meditators show significantly reduced activity in this network."),
    ("silence", 2),
    ("text", "Less mind-wandering means less rumination, which is strongly linked to anxiety and depression."),
    ("silence", 3),

    # Beyond the Brain
    ("text", "The effects of mindfulness extend beyond the brain."),
    ("silence", 2),
    ("text", "Stress hormones decrease. A meta-analysis of over 200 studies found that mindfulness meditation significantly reduces cortisol — the primary stress hormone."),
    ("silence", 2),
    ("text", "Lower cortisol means lower inflammation, better immune function, and improved sleep."),
    ("silence", 3),
    ("text", "Blood pressure drops. A 2013 study in the American Journal of Hypertension found that mindfulness meditation reduced blood pressure in participants who practised regularly."),
    ("silence", 2),
    ("text", "Comparable to some lifestyle interventions recommended by doctors."),
    ("silence", 3),
    ("text", "Pain perception changes. A study published in the Journal of Neuroscience found that meditation reduced pain intensity by 40 percent and pain unpleasantness by 57 percent."),
    ("silence", 2),
    ("text", "For context, morphine typically reduces pain by about 25 percent."),
    ("silence", 3),
    ("text", "These aren't marginal effects. This is meaningful, measurable change from a practice that requires nothing more than your attention."),
    ("silence", 3),

    # How Much Do You Need
    ("text", "This is the practical question everyone asks, and the research has a reassuring answer."),
    ("silence", 2),
    ("text", "Most studies showing significant results used programs of eight weeks with daily practice of fifteen to forty-five minutes."),
    ("silence", 2),
    ("text", "But more recent research suggests that even shorter sessions produce benefits."),
    ("silence", 2),
    ("text", "A 2018 study found that just ten minutes of daily mindfulness practice improved attention and working memory after two weeks."),
    ("silence", 2),
    ("text", "Another study found that a single fifteen-minute meditation session reduced mind-wandering compared to a control group."),
    ("silence", 2),
    ("text", "The takeaway? Consistency matters more than duration. Ten minutes every day will do more for you than an hour once a week."),
    ("silence", 3),

    # Closing
    ("text", "Here's what I want you to take away from this."),
    ("silence", 2),
    ("text", "Mindfulness isn't mystical. It isn't about belief. It's a trainable skill that produces measurable changes in your brain and body."),
    ("silence", 2),
    ("text", "You don't need to be a monk. You don't need a retreat. You need a few minutes, somewhere reasonably quiet, and the willingness to pay attention."),
    ("silence", 3),
    ("text", "If you'd like to start, try our ten-minute morning meditation — it's a guided session designed for complete beginners."),
    ("silence", 3),
    ("text", "Thank you for listening. If this was helpful, explore Salus for more guided meditations and mindfulness content — built by a family, not a corporation."),
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
                "-ar", "44100", "-ac", "1", "-acodec", "pcm_s16le", part_path
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
