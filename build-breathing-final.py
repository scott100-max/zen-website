#!/usr/bin/env python3
"""Build breathing exercise audio: narration + bell tones at counting points."""
import subprocess
import os
import math
import struct
import wave
import tempfile
import json

BASE = "/Users/scottripley/salus-website"
NARRATION = os.path.join(BASE, "content/audio/03-breathing-for-anxiety-narration.mp3")
OUTPUT = os.path.join(BASE, "content/audio/03-breathing-for-anxiety.mp3")
SR = 44100

# Split points in narration audio (seconds)
# These are where exercises should be inserted
# After "Let your shoulders drop." → ~69s (1 round box 4-4-4-4)
# After "Good. Let's do three more rounds together." → ~86s (3 rounds box)
# After "Keep it there throughout." → ~148s (1 round 4-7-8)
# After "Let's do that three more times." → ~155s (3 rounds 4-7-8)
SPLITS = [69.0, 86.0, 148.0, 155.0]

# Exercise definitions: list of (phase_name, count) tuples per round
BOX_ROUND = [("in", 4), ("hold", 4), ("out", 4), ("hold", 4)]
ROUND_478 = [("in", 4), ("hold", 7), ("out", 8)]


def gen_bell(path, freq=528, duration=1.2, vol=0.12):
    """Generate a soft bell/chime tone."""
    n = int(SR * duration)
    samples = []
    for i in range(n):
        t = i / SR
        # Bell = fundamental + harmonic, with exponential decay
        decay = math.exp(-3.5 * t)
        val = (math.sin(2 * math.pi * freq * t) * 0.7 +
               math.sin(2 * math.pi * freq * 2.0 * t) * 0.2 +
               math.sin(2 * math.pi * freq * 3.0 * t) * 0.1) * vol * decay
        samples.append(int(max(-1, min(1, val)) * 32767))
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))


def gen_tick(path, freq=396, duration=0.12, vol=0.08):
    """Generate a soft tick/ping for each count."""
    n = int(SR * duration)
    samples = []
    for i in range(n):
        decay = math.exp(-8 * i / n)
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
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(struct.pack(f'<{n}h', *([0] * n)))


def gen_phase(tmpdir, prefix, phase, count):
    """Generate audio for one phase: bell + count ticks with gaps.
    Bell frequencies: in=440, hold=528, out=396"""
    freq_map = {"in": 440, "hold": 528, "out": 396}
    parts = []

    # Opening bell for this phase
    bell = os.path.join(tmpdir, f"{prefix}_bell.wav")
    gen_bell(bell, freq=freq_map.get(phase, 528), duration=1.0, vol=0.10)
    parts.append(bell)

    # Gap after bell
    gap = os.path.join(tmpdir, f"{prefix}_gap0.wav")
    gen_silence(gap, 0.5)
    parts.append(gap)

    # Count ticks (one per second)
    for c in range(count):
        tick = os.path.join(tmpdir, f"{prefix}_tick{c}.wav")
        gen_tick(tick, freq=440 if phase == "in" else (528 if phase == "hold" else 350))
        parts.append(tick)
        if c < count - 1:
            sil = os.path.join(tmpdir, f"{prefix}_sil{c}.wav")
            gen_silence(sil, 0.88)  # ~1s per count total
            parts.append(sil)

    # End gap between phases
    end = os.path.join(tmpdir, f"{prefix}_end.wav")
    gen_silence(end, 0.8)
    parts.append(end)

    return parts


def gen_round(tmpdir, prefix, phases):
    """Generate one full breathing round."""
    all_parts = []
    for i, (phase, count) in enumerate(phases):
        parts = gen_phase(tmpdir, f"{prefix}_p{i}_{phase}", phase, count)
        all_parts.extend(parts)
    return all_parts


def concat_wavs(tmpdir, parts, output_name):
    """Concatenate WAV files using ffmpeg."""
    list_file = os.path.join(tmpdir, f"{output_name}_list.txt")
    with open(list_file, 'w') as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    out = os.path.join(tmpdir, f"{output_name}.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", out
    ], capture_output=True)
    return out


def wav_to_mp3(wav_path, mp3_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", wav_path,
        "-codec:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "1",
        mp3_path
    ], capture_output=True)


def main():
    print("Building breathing exercise audio (narration + bell tones)...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Split narration into segments
        segments = []
        prev = 0
        for i, t in enumerate(SPLITS):
            seg = os.path.join(tmpdir, f"narr_{i}.mp3")
            subprocess.run([
                "ffmpeg", "-y", "-i", NARRATION,
                "-ss", str(prev), "-t", str(t - prev),
                "-c", "copy", seg
            ], capture_output=True)
            segments.append(seg)
            prev = t

        # Final segment
        seg_final = os.path.join(tmpdir, "narr_final.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-i", NARRATION,
            "-ss", str(prev), "-c", "copy", seg_final
        ], capture_output=True)
        segments.append(seg_final)

        # Generate exercise audio for each insertion point
        # 1. One round box breathing
        print("  Exercise 1: Box breathing round 1...")
        parts1 = gen_round(tmpdir, "ex1", BOX_ROUND)
        ex1 = concat_wavs(tmpdir, parts1, "ex1")

        # 2. Three rounds box breathing
        print("  Exercise 2: Box breathing rounds 2-4...")
        parts2 = []
        for r in range(3):
            parts2.extend(gen_round(tmpdir, f"ex2r{r}", BOX_ROUND))
            # Gap between rounds
            rg = os.path.join(tmpdir, f"ex2_roundgap{r}.wav")
            gen_silence(rg, 1.5)
            parts2.append(rg)
        ex2 = concat_wavs(tmpdir, parts2, "ex2")

        # 3. One round 4-7-8
        print("  Exercise 3: 4-7-8 round 1...")
        parts3 = gen_round(tmpdir, "ex3", ROUND_478)
        ex3 = concat_wavs(tmpdir, parts3, "ex3")

        # 4. Three rounds 4-7-8
        print("  Exercise 4: 4-7-8 rounds 2-4...")
        parts4 = []
        for r in range(3):
            parts4.extend(gen_round(tmpdir, f"ex4r{r}", ROUND_478))
            rg = os.path.join(tmpdir, f"ex4_roundgap{r}.wav")
            gen_silence(rg, 1.5)
            parts4.append(rg)
        ex4 = concat_wavs(tmpdir, parts4, "ex4")

        # Convert exercises to mp3
        exercises = [ex1, ex2, ex3, ex4]
        ex_mp3s = []
        for i, ex in enumerate(exercises):
            mp3 = os.path.join(tmpdir, f"ex{i}.mp3")
            wav_to_mp3(ex, mp3)
            ex_mp3s.append(mp3)
            dur = float(json.loads(subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", mp3],
                capture_output=True, text=True
            ).stdout)["format"]["duration"])
            print(f"    → {dur:.1f}s")

        # Normalize narration segments
        narr_mp3s = []
        for i, seg in enumerate(segments):
            norm = os.path.join(tmpdir, f"narr_norm_{i}.mp3")
            subprocess.run([
                "ffmpeg", "-y", "-i", seg,
                "-codec:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "1",
                norm
            ], capture_output=True)
            narr_mp3s.append(norm)

        # Interleave: narr0 + ex0 + narr1 + ex1 + narr2 + ex2 + narr3 + ex3 + narr4
        final_list = os.path.join(tmpdir, "final_list.txt")
        with open(final_list, 'w') as f:
            for i in range(4):
                f.write(f"file '{narr_mp3s[i]}'\n")
                f.write(f"file '{ex_mp3s[i]}'\n")
            f.write(f"file '{narr_mp3s[4]}'\n")

        print("  Concatenating final audio...")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", final_list,
            "-codec:a", "libmp3lame", "-q:a", "2", OUTPUT
        ], capture_output=True)

    dur = float(json.loads(subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", OUTPUT],
        capture_output=True, text=True
    ).stdout)["format"]["duration"])
    size = os.path.getsize(OUTPUT)
    print(f"\n  Saved: {OUTPUT}")
    print(f"  Duration: {dur:.0f}s ({dur/60:.1f} min), Size: {size//1024} KB")
    print("Done!")


if __name__ == "__main__":
    main()
