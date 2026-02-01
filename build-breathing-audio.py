#!/usr/bin/env python3
"""
build-breathing-audio.py

Takes the narration-only MP3 (no breathing cues) and inserts gentle sine-tone
breathing exercises into the silent pauses between speech segments.

Usage:
    python build-breathing-audio.py [--narration PATH] [--output PATH]

Defaults:
    --narration  content/audio/03-breathing-for-anxiety-narration.mp3
    --output     content/audio/03-breathing-for-anxiety.mp3

Requirements:
    - ffmpeg and ffprobe on PATH
    - Python 3.8+
"""

import argparse
import json
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import wave

SAMPLE_RATE = 44100

# ── Breathing exercise definitions ──────────────────────────────────────────
# Each exercise is a sequence of (phase, duration_seconds) tuples.
# Phases: "in", "hold", "out"

BOX_ROUND = [("in", 4), ("hold", 4), ("out", 4), ("hold", 4)]
FOUR_SEVEN_EIGHT_ROUND = [("in", 4), ("hold", 7), ("out", 8)]

# The narration script has these silent gaps (in order) where exercises go:
#   Gap 1: after "Let your shoulders drop." → 1 round box breathing
#   Gap 2: after "Let's do three more rounds together." → 3 rounds box
#   Gap 3: after "Keep it there throughout." → 1 round 4-7-8
#   Gap 4: after "Let's do that three more times." → 3 rounds 4-7-8
EXERCISE_SEQUENCE = [
    BOX_ROUND * 1,
    BOX_ROUND * 3,
    FOUR_SEVEN_EIGHT_ROUND * 1,
    FOUR_SEVEN_EIGHT_ROUND * 3,
]

# ── Tone parameters ─────────────────────────────────────────────────────────
VOLUME = 0.06
PING_VOLUME = 0.04
PING_DURATION = 0.12
FADE_MS = 15  # fade in/out to avoid clicks


def generate_sine(freq, duration, volume=VOLUME):
    """Generate a sine wave as a list of float samples."""
    n = int(SAMPLE_RATE * duration)
    fade_samples = int(SAMPLE_RATE * FADE_MS / 1000)
    samples = []
    for i in range(n):
        s = math.sin(2 * math.pi * freq * i / SAMPLE_RATE) * volume
        # fade in
        if i < fade_samples:
            s *= i / fade_samples
        # fade out
        if i > n - fade_samples:
            s *= (n - i) / fade_samples
        samples.append(s)
    return samples


def generate_sweep(freq_start, freq_end, duration, volume=VOLUME):
    """Generate a linear frequency sweep."""
    n = int(SAMPLE_RATE * duration)
    fade_samples = int(SAMPLE_RATE * FADE_MS / 1000)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        frac = i / n
        freq = freq_start + (freq_end - freq_start) * frac
        phase = 2 * math.pi * (freq_start * t + (freq_end - freq_start) * t * frac / 2)
        s = math.sin(phase) * volume
        if i < fade_samples:
            s *= i / fade_samples
        if i > n - fade_samples:
            s *= (n - i) / fade_samples
        samples.append(s)
    return samples


def generate_ping(freq=396, duration=PING_DURATION, volume=PING_VOLUME):
    """A short, soft ping for counting seconds."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 20)  # fast exponential decay
        s = math.sin(2 * math.pi * freq * t) * volume * env
        samples.append(s)
    return samples


def silence(duration):
    """Generate silence."""
    return [0.0] * int(SAMPLE_RATE * duration)


def build_phase_audio(phase, count_seconds):
    """
    Build audio for one breathing phase.

    Structure per phase:
      - A 0.5s cue tone at the start
      - Then (count_seconds) seconds total, with a ping at each second boundary
        (the cue occupies the first 0.5s of second 1)
    """
    audio = []

    # Leading cue tone (0.5s)
    if phase == "in":
        cue = generate_sweep(396, 528, 0.5, VOLUME)
    elif phase == "hold":
        cue = generate_sine(528, 0.3, VOLUME * 0.6)
        cue += silence(0.2)
    else:  # "out"
        cue = generate_sweep(528, 396, 0.5, VOLUME)

    audio.extend(cue)
    # Fill rest of first second
    remaining_first = 1.0 - 0.5
    audio.extend(silence(remaining_first))

    # Seconds 2 through count_seconds: ping at start, silence for rest
    for _ in range(count_seconds - 1):
        ping = generate_ping()
        audio.extend(ping)
        audio.extend(silence(1.0 - PING_DURATION))

    return audio


def build_exercise_audio(phases):
    """Build full audio for a list of (phase, duration) tuples, plus a trailing 1s pause."""
    audio = []
    for phase, dur in phases:
        audio.extend(build_phase_audio(phase, dur))
    # Small trailing silence before narration resumes
    audio.extend(silence(1.0))
    return audio


def samples_to_wav(samples, path):
    """Write float samples to a 16-bit mono WAV file."""
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        data = b""
        for s in samples:
            s = max(-1.0, min(1.0, s))
            data += struct.pack("<h", int(s * 32767))
        wf.writeframes(data)


def detect_silences(mp3_path, min_duration=2.0, noise_db=-35):
    """Use ffmpeg silencedetect to find silent gaps in the narration."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", mp3_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    total_duration = float(json.loads(result.stdout)["format"]["duration"])

    cmd = [
        "ffmpeg", "-i", mp3_path, "-af",
        f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr

    silences = []
    starts = re.findall(r"silence_start: ([\d.]+)", stderr)
    ends = re.findall(r"silence_end: ([\d.]+)", stderr)

    for s, e in zip(starts, ends):
        silences.append((float(s), float(e)))

    return silences, total_duration


def run(narration_path, output_path):
    if not os.path.isfile(narration_path):
        print(f"Error: narration file not found: {narration_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Detecting silences in {narration_path}...")
    silences, total_dur = detect_silences(narration_path)
    print(f"  Total duration: {total_dur:.1f}s")
    print(f"  Found {len(silences)} silent gaps (>2s)")

    for i, (s, e) in enumerate(silences):
        print(f"    Gap {i + 1}: {s:.1f}s – {e:.1f}s  ({e - s:.1f}s)")

    # We expect at least 4 gaps for the 4 exercise insertions.
    # Pick the 4 longest gaps if there are more than 4.
    if len(silences) < 4:
        print(
            f"Warning: expected at least 4 silent gaps, found {len(silences)}. "
            f"Will insert exercises into available gaps.",
            file=sys.stderr,
        )
        exercise_gaps = silences
        exercises = EXERCISE_SEQUENCE[: len(silences)]
    else:
        # Sort by duration descending, take top 4, then re-sort by time
        ranked = sorted(silences, key=lambda x: -(x[1] - x[0]))[:4]
        exercise_gaps = sorted(ranked, key=lambda x: x[0])
        exercises = EXERCISE_SEQUENCE

    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate exercise WAVs
        exercise_wavs = []
        for i, ex in enumerate(exercises):
            samples = build_exercise_audio(ex)
            wav_path = os.path.join(tmpdir, f"exercise_{i}.wav")
            samples_to_wav(samples, wav_path)
            dur = len(samples) / SAMPLE_RATE
            print(f"  Exercise {i + 1}: {dur:.1f}s")
            exercise_wavs.append(wav_path)

        # Build the ffmpeg complex filter to:
        #   1. Split narration at gap points
        #   2. Insert exercise audio in each gap
        #   3. Concatenate everything

        # Strategy: extract narration segments between exercises, convert
        # exercise WAVs to same format, then concatenate all pieces.

        segments = []  # list of file paths in order

        prev_end = 0.0
        for i, ((gap_start, gap_end), ex_wav) in enumerate(
            zip(exercise_gaps, exercise_wavs)
        ):
            # Narration segment before this gap
            narr_seg = os.path.join(tmpdir, f"narr_{i}.wav")
            duration = gap_start - prev_end
            if duration > 0.05:
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", narration_path,
                        "-ss", str(prev_end), "-t", str(duration),
                        "-ar", str(SAMPLE_RATE), "-ac", "1",
                        "-acodec", "pcm_s16le", narr_seg,
                    ],
                    capture_output=True, check=True,
                )
                segments.append(narr_seg)

            # Exercise audio
            segments.append(ex_wav)

            prev_end = gap_end

        # Final narration segment after last gap
        remaining = total_dur - prev_end
        if remaining > 0.05:
            narr_final = os.path.join(tmpdir, "narr_final.wav")
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", narration_path,
                    "-ss", str(prev_end), "-t", str(remaining),
                    "-ar", str(SAMPLE_RATE), "-ac", "1",
                    "-acodec", "pcm_s16le", narr_final,
                ],
                capture_output=True, check=True,
            )
            segments.append(narr_final)

        # Write concat list
        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, "w") as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")

        # Concatenate and encode to MP3
        print(f"Concatenating {len(segments)} segments...")
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_list,
                "-acodec", "libmp3lame", "-ab", "192k",
                "-ar", str(SAMPLE_RATE), "-ac", "1",
                output_path,
            ],
            capture_output=True, check=True,
        )

    print(f"Done! Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Build breathing exercise audio by inserting tones into narration pauses."
    )
    parser.add_argument(
        "--narration",
        default="content/audio/03-breathing-for-anxiety-narration.mp3",
        help="Path to narration-only MP3",
    )
    parser.add_argument(
        "--output",
        default="content/audio/03-breathing-for-anxiety.mp3",
        help="Output MP3 path",
    )
    args = parser.parse_args()
    run(args.narration, args.output)


if __name__ == "__main__":
    main()
