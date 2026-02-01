#!/usr/bin/env python3
"""Build the breathing exercise audio: Lily narration + gentle tone cues."""
import subprocess
import os
import math
import struct
import wave
import tempfile

BASE = "/Users/scottripley/salus-website"
NARRATION = os.path.join(BASE, "content/audio/03-breathing-for-anxiety-narration.mp3")
OUTPUT = os.path.join(BASE, "content/audio/03-breathing-for-anxiety.mp3")

SR = 44100
VOLUME = 0.06
PING_VOL = 0.05


def gen_tone(path, freq, duration, vol=VOLUME, sweep_to=None):
    """Generate a sine tone WAV. Optional frequency sweep."""
    n = int(SR * duration)
    fade = int(SR * 0.03)
    samples = []
    for i in range(n):
        if sweep_to:
            f = freq + (sweep_to - freq) * (i / n)
        else:
            f = freq
        val = math.sin(2 * math.pi * f * i / SR) * vol
        if i < fade:
            val *= i / fade
        if i > n - fade:
            val *= (n - i) / fade
        samples.append(int(val * 32767))
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))


def gen_ping(path, freq=396, duration=0.15, vol=PING_VOL):
    """Generate a soft ping/tick."""
    n = int(SR * duration)
    samples = []
    for i in range(n):
        decay = math.exp(-6 * i / n)
        val = math.sin(2 * math.pi * freq * i / SR) * vol * decay
        samples.append(int(val * 32767))
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))


def gen_silence(path, duration):
    """Generate silence WAV."""
    n = int(SR * duration)
    samples = [0] * n
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))


def gen_exercise_round(tmpdir, prefix, in_counts, hold_counts, out_counts, hold2_counts=None):
    """Generate one round of breathing exercise as WAV.
    Pattern: in-cue + pings, hold-cue + pings, out-cue + pings, [hold-cue + pings]"""
    parts = []

    # "Breathe in" — ascending tone + count pings
    in_cue = os.path.join(tmpdir, f"{prefix}_in_cue.wav")
    gen_tone(in_cue, 330, 0.6, sweep_to=528)
    parts.append(in_cue)
    for c in range(in_counts - 1):
        sil = os.path.join(tmpdir, f"{prefix}_in_sil{c}.wav")
        gen_silence(sil, 0.85)
        parts.append(sil)
        ping = os.path.join(tmpdir, f"{prefix}_in_ping{c}.wav")
        gen_ping(ping, freq=440)
        parts.append(ping)

    # Brief pause between phases
    gap = os.path.join(tmpdir, f"{prefix}_gap1.wav")
    gen_silence(gap, 0.4)
    parts.append(gap)

    # "Hold" — steady tone + count pings
    hold_cue = os.path.join(tmpdir, f"{prefix}_hold_cue.wav")
    gen_tone(hold_cue, 528, 0.4)
    parts.append(hold_cue)
    for c in range(hold_counts - 1):
        sil = os.path.join(tmpdir, f"{prefix}_hold_sil{c}.wav")
        gen_silence(sil, 0.85)
        parts.append(sil)
        ping = os.path.join(tmpdir, f"{prefix}_hold_ping{c}.wav")
        gen_ping(ping, freq=528)
        parts.append(ping)

    gap2 = os.path.join(tmpdir, f"{prefix}_gap2.wav")
    gen_silence(gap2, 0.4)
    parts.append(gap2)

    # "Breathe out" — descending tone + count pings
    out_cue = os.path.join(tmpdir, f"{prefix}_out_cue.wav")
    gen_tone(out_cue, 528, 0.6, sweep_to=330)
    parts.append(out_cue)
    for c in range(out_counts - 1):
        sil = os.path.join(tmpdir, f"{prefix}_out_sil{c}.wav")
        gen_silence(sil, 0.85)
        parts.append(sil)
        ping = os.path.join(tmpdir, f"{prefix}_out_ping{c}.wav")
        gen_ping(ping, freq=396)
        parts.append(ping)

    # Optional second hold (for box breathing)
    if hold2_counts:
        gap3 = os.path.join(tmpdir, f"{prefix}_gap3.wav")
        gen_silence(gap3, 0.4)
        parts.append(gap3)

        hold2_cue = os.path.join(tmpdir, f"{prefix}_hold2_cue.wav")
        gen_tone(hold2_cue, 528, 0.4)
        parts.append(hold2_cue)
        for c in range(hold2_counts - 1):
            sil = os.path.join(tmpdir, f"{prefix}_hold2_sil{c}.wav")
            gen_silence(sil, 0.85)
            parts.append(sil)
            ping = os.path.join(tmpdir, f"{prefix}_hold2_ping{c}.wav")
            gen_ping(ping, freq=528)
            parts.append(ping)

    # End gap
    end_gap = os.path.join(tmpdir, f"{prefix}_end.wav")
    gen_silence(end_gap, 1.0)
    parts.append(end_gap)

    # Concat all parts
    round_wav = os.path.join(tmpdir, f"{prefix}_round.wav")
    concat_list = os.path.join(tmpdir, f"{prefix}_list.txt")
    with open(concat_list, 'w') as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", round_wav
    ], capture_output=True)
    return round_wav


def main():
    print("Building breathing exercise audio with tones...")

    # Split points in the narration (approximate timestamps from silence detection)
    # After "Let your shoulders drop." → ~69.8s
    # After "Good. Let's do three more rounds together." → ~85.6s
    # After "Keep it there throughout." → ~147.5s
    # After "Let's do that three more times." → ~154.5s
    splits = [69.8, 85.6, 147.5, 154.5]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Split narration into 5 segments
        segments = []
        prev = 0
        for i, t in enumerate(splits):
            seg = os.path.join(tmpdir, f"narr_{i}.mp3")
            subprocess.run([
                "ffmpeg", "-y", "-i", NARRATION,
                "-ss", str(prev), "-t", str(t - prev),
                "-c", "copy", seg
            ], capture_output=True)
            segments.append(seg)
            prev = t
        # Final segment
        seg_final = os.path.join(tmpdir, "narr_4.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-i", NARRATION,
            "-ss", str(prev), "-c", "copy", seg_final
        ], capture_output=True)
        segments.append(seg_final)

        # Generate exercise rounds
        # 1. One round box breathing (4-4-4-4)
        print("  Generating box breathing round 1...")
        ex1 = gen_exercise_round(tmpdir, "box1", 4, 4, 4, hold2_counts=4)

        # 2. Three rounds box breathing
        print("  Generating box breathing rounds 2-4...")
        box_rounds = []
        for r in range(3):
            rnd = gen_exercise_round(tmpdir, f"box{r+2}", 4, 4, 4, hold2_counts=4)
            box_rounds.append(rnd)
        # Concat 3 rounds
        box3_list = os.path.join(tmpdir, "box3_list.txt")
        with open(box3_list, 'w') as f:
            for br in box_rounds:
                f.write(f"file '{br}'\n")
        ex2 = os.path.join(tmpdir, "box3_all.wav")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", box3_list,
            "-c", "copy", ex2
        ], capture_output=True)

        # 3. One round 4-7-8 breathing
        print("  Generating 4-7-8 round 1...")
        ex3 = gen_exercise_round(tmpdir, "478_1", 4, 7, 8)

        # 4. Three rounds 4-7-8
        print("  Generating 4-7-8 rounds 2-4...")
        r478_rounds = []
        for r in range(3):
            rnd = gen_exercise_round(tmpdir, f"478_{r+2}", 4, 7, 8)
            r478_rounds.append(rnd)
        r478_list = os.path.join(tmpdir, "478_list.txt")
        with open(r478_list, 'w') as f:
            for rr in r478_rounds:
                f.write(f"file '{rr}'\n")
        ex4 = os.path.join(tmpdir, "478_all.wav")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", r478_list,
            "-c", "copy", ex4
        ], capture_output=True)

        # Convert exercise WAVs to MP3 for concat compatibility
        exercises = [ex1, ex2, ex3, ex4]
        ex_mp3s = []
        for i, ex in enumerate(exercises):
            mp3 = os.path.join(tmpdir, f"ex_{i}.mp3")
            subprocess.run([
                "ffmpeg", "-y", "-i", ex,
                "-codec:a", "libmp3lame", "-q:a", "2",
                "-ar", "44100", "-ac", "1", mp3
            ], capture_output=True)
            ex_mp3s.append(mp3)

        # Normalize narration segments to same format
        narr_norm = []
        for i, seg in enumerate(segments):
            norm = os.path.join(tmpdir, f"narr_norm_{i}.mp3")
            subprocess.run([
                "ffmpeg", "-y", "-i", seg,
                "-codec:a", "libmp3lame", "-q:a", "2",
                "-ar", "44100", "-ac", "1", norm
            ], capture_output=True)
            narr_norm.append(norm)

        # Interleave: narr0 + ex0 + narr1 + ex1 + narr2 + ex2 + narr3 + ex3 + narr4
        final_list = os.path.join(tmpdir, "final_list.txt")
        with open(final_list, 'w') as f:
            for i in range(4):
                f.write(f"file '{narr_norm[i]}'\n")
                f.write(f"file '{ex_mp3s[i]}'\n")
            f.write(f"file '{narr_norm[4]}'\n")

        print("  Concatenating final audio...")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", final_list,
            "-codec:a", "libmp3lame", "-q:a", "2", OUTPUT
        ], capture_output=True)

    size = os.path.getsize(OUTPUT)
    dur_result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", OUTPUT],
        capture_output=True, text=True
    )
    import json
    dur = float(json.loads(dur_result.stdout)["format"]["duration"])
    print(f"  Saved: {OUTPUT}")
    print(f"  Duration: {dur:.0f}s ({dur/60:.1f} min), Size: {size/1024:.0f} KB")
    print("Done!")


if __name__ == "__main__":
    main()
