#!/usr/bin/env python3
"""Build breathing exercise audio: narration + individually-generated number words with proper gaps."""
import subprocess
import os
import json
import requests
import tempfile
import time

BASE = "/Users/scottripley/salus-website"
NARRATION = os.path.join(BASE, "content/audio/03-breathing-for-anxiety-narration.mp3")
OUTPUT = os.path.join(BASE, "content/audio/03-breathing-for-anxiety.mp3")

API_KEY = "sk_400c6d730d0efccda44656815ac3472e985bf51bf4917f13"
VOICE_ID = "pFZP5JQG7iQjIQuC4Bku"  # Lily

# Split points in narration-only audio (seconds)
# After "Let your shoulders drop." → ~69s (1 round box 4-4-4-4)
# After "Good. Let's do three more rounds together." → ~86s (3 rounds box)
# After "Keep it there throughout." → ~148s (1 round 4-7-8)
# After "Let's do that three more times." → ~155s (3 rounds 4-7-8)
SPLITS = [69.0, 86.0, 148.0, 155.0]

# Exercises
BOX_ROUND = [("Breathe in.", 4), ("Hold.", 4), ("Breathe out.", 4), ("Hold.", 4)]
ROUND_478 = [("Breathe in through your nose.", 4), ("Hold.", 7), ("Exhale through your mouth.", 8)]


def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def tts(text, out_path):
    """Generate a single word/phrase via ElevenLabs."""
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.90,
                "similarity_boost": 0.65,
                "style": 0.03,
                "speed": 0.70,
            },
        },
    )
    if resp.status_code == 200:
        with open(out_path, "wb") as f:
            f.write(resp.content)
        return True
    else:
        print(f"  TTS ERROR {resp.status_code}: {resp.text}")
        return False


def gen_silence(path, duration):
    """Generate silence MP3."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
        "-t", str(duration), "-codec:a", "libmp3lame", "-q:a", "2", path
    ], capture_output=True)


def gen_exercise(tmpdir, prefix, phases, rounds=1):
    """Generate exercise audio with individually spoken numbers and gaps."""
    parts = []

    for rnd in range(rounds):
        for pi, (cue, count) in enumerate(phases):
            # Generate the cue phrase ("Breathe in.", "Hold.", etc.)
            cue_path = os.path.join(tmpdir, f"{prefix}_r{rnd}_p{pi}_cue.mp3")
            print(f"    TTS: '{cue}'")
            tts(cue, cue_path)
            parts.append(cue_path)
            time.sleep(0.3)

            # Gap after cue before counting starts
            gap = os.path.join(tmpdir, f"{prefix}_r{rnd}_p{pi}_gap.mp3")
            gen_silence(gap, 0.8)
            parts.append(gap)

            # Generate each number individually with gaps
            number_words = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight"]
            for c in range(count):
                num_path = os.path.join(tmpdir, f"{prefix}_r{rnd}_p{pi}_n{c}.mp3")
                word = number_words[c]
                print(f"    TTS: '{word}'")
                tts(f"{word}.", num_path)
                parts.append(num_path)
                time.sleep(0.3)

                # Gap between numbers (1 second of silence for proper pacing)
                if c < count - 1:
                    sil = os.path.join(tmpdir, f"{prefix}_r{rnd}_p{pi}_s{c}.mp3")
                    gen_silence(sil, 0.8)
                    parts.append(sil)

            # Gap between phases
            phase_gap = os.path.join(tmpdir, f"{prefix}_r{rnd}_p{pi}_end.mp3")
            gen_silence(phase_gap, 1.0)
            parts.append(phase_gap)

        # Gap between rounds
        if rnd < rounds - 1:
            rg = os.path.join(tmpdir, f"{prefix}_r{rnd}_roundgap.mp3")
            gen_silence(rg, 1.5)
            parts.append(rg)

    return parts


def concat_mp3s(tmpdir, parts, name):
    """Concatenate MP3 files."""
    list_file = os.path.join(tmpdir, f"{name}_list.txt")
    with open(list_file, 'w') as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    out = os.path.join(tmpdir, f"{name}.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-codec:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "1", out
    ], capture_output=True)
    return out


def main():
    print("Building breathing exercise audio (narration + spaced counting)...")
    print(f"Narration: {NARRATION}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Split narration into segments at the split points
        segments = []
        prev = 0
        for i, t in enumerate(SPLITS):
            seg = os.path.join(tmpdir, f"narr_{i}.mp3")
            subprocess.run([
                "ffmpeg", "-y", "-i", NARRATION,
                "-ss", str(prev), "-t", str(t - prev),
                "-codec:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "1", seg
            ], capture_output=True)
            dur = get_duration(seg)
            print(f"  Narration segment {i}: {prev:.0f}s-{t:.0f}s ({dur:.1f}s)")
            segments.append(seg)
            prev = t

        # Final segment (from last split to end)
        seg_final = os.path.join(tmpdir, "narr_final.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-i", NARRATION,
            "-ss", str(prev),
            "-codec:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "1", seg_final
        ], capture_output=True)
        dur = get_duration(seg_final)
        print(f"  Narration segment final: {prev:.0f}s-end ({dur:.1f}s)")
        segments.append(seg_final)

        # Generate exercise segments with individually-spoken numbers
        print("\n  Exercise 1: Box breathing (1 round)...")
        ex1_parts = gen_exercise(tmpdir, "ex1", BOX_ROUND, rounds=1)
        ex1 = concat_mp3s(tmpdir, ex1_parts, "ex1")
        print(f"    → {get_duration(ex1):.1f}s")

        print("\n  Exercise 2: Box breathing (3 rounds)...")
        ex2_parts = gen_exercise(tmpdir, "ex2", BOX_ROUND, rounds=3)
        ex2 = concat_mp3s(tmpdir, ex2_parts, "ex2")
        print(f"    → {get_duration(ex2):.1f}s")

        print("\n  Exercise 3: 4-7-8 breathing (1 round)...")
        ex3_parts = gen_exercise(tmpdir, "ex3", ROUND_478, rounds=1)
        ex3 = concat_mp3s(tmpdir, ex3_parts, "ex3")
        print(f"    → {get_duration(ex3):.1f}s")

        print("\n  Exercise 4: 4-7-8 breathing (3 rounds)...")
        ex4_parts = gen_exercise(tmpdir, "ex4", ROUND_478, rounds=3)
        ex4 = concat_mp3s(tmpdir, ex4_parts, "ex4")
        print(f"    → {get_duration(ex4):.1f}s")

        exercises = [ex1, ex2, ex3, ex4]

        # Interleave: narr0 + ex0 + narr1 + ex1 + narr2 + ex2 + narr3 + ex3 + narr4
        final_list = os.path.join(tmpdir, "final_list.txt")
        with open(final_list, 'w') as f:
            for i in range(4):
                f.write(f"file '{segments[i]}'\n")
                f.write(f"file '{exercises[i]}'\n")
            f.write(f"file '{segments[4]}'\n")

        print("\n  Concatenating final audio...")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", final_list,
            "-codec:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "1", OUTPUT
        ], capture_output=True)

    dur = get_duration(OUTPUT)
    size = os.path.getsize(OUTPUT)
    print(f"\n  Saved: {OUTPUT}")
    print(f"  Duration: {dur:.0f}s ({dur/60:.1f} min), Size: {size//1024} KB")
    print("Done!")


if __name__ == "__main__":
    main()
