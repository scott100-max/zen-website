#!/usr/bin/env python3
"""
Add soft beep tones to a breathing exercise audio file.

This script takes a TTS-generated MP3 where counting has been removed
and adds soft 396Hz sine tone beeps at regular intervals during the
pause/silence sections (where counting would have been).

Usage:
    python add-beeps.py input.mp3 output.mp3

Requirements:
    - ffmpeg and ffprobe must be installed
    - pip install pydub

The script detects silent regions (the "..." pauses in the TTS output)
and places a soft beep at each ~1 second interval within those regions.
"""

import sys
import subprocess
import json
import struct
import wave
import tempfile
import os
import math

BEEP_FREQ = 396       # Hz - soft, low tone
BEEP_DURATION = 0.3   # seconds
BEEP_VOLUME = 0.08    # 0.0-1.0 (very quiet)
SAMPLE_RATE = 44100
SILENCE_THRESHOLD_DB = -28  # dB below peak to consider "silent"
MIN_SILENCE_MS = 500        # minimum silence duration to consider a pause


def generate_beep_wav(path, freq=BEEP_FREQ, duration=BEEP_DURATION,
                      volume=BEEP_VOLUME, sr=SAMPLE_RATE):
    """Generate a soft sine wave beep as a WAV file."""
    n_samples = int(sr * duration)
    # Apply fade in/out (20ms) to avoid clicks
    fade_samples = int(sr * 0.02)
    samples = []
    for i in range(n_samples):
        val = math.sin(2 * math.pi * freq * i / sr) * volume
        # Fade in
        if i < fade_samples:
            val *= i / fade_samples
        # Fade out
        if i > n_samples - fade_samples:
            val *= (n_samples - i) / fade_samples
        samples.append(int(val * 32767))

    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))


def detect_silences(audio_path):
    """Use ffmpeg silencedetect to find silent regions."""
    cmd = [
        'ffmpeg', '-i', audio_path, '-af',
        f'silencedetect=noise={SILENCE_THRESHOLD_DB}dB:d={MIN_SILENCE_MS / 1000}',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr

    silences = []
    start = None
    for line in stderr.split('\n'):
        if 'silence_start:' in line:
            start = float(line.split('silence_start:')[1].strip().split()[0])
        elif 'silence_end:' in line and start is not None:
            end = float(line.split('silence_end:')[1].strip().split()[0])
            silences.append((start, end))
            start = None
    return silences


def get_duration(audio_path):
    """Get audio duration in seconds via ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    return float(info['format']['duration'])


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input.mp3 output.mp3")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    print("Detecting silent regions...")
    silences = detect_silences(input_path)
    print(f"Found {len(silences)} silent regions")

    if not silences:
        print("No silences detected. Try adjusting SILENCE_THRESHOLD_DB.")
        sys.exit(1)

    # Generate beep positions: one beep per ~1 second of silence
    beep_times = []
    for start, end in silences:
        duration = end - start
        # Skip very short silences (natural speech pauses)
        if duration < 1.2:
            continue
        # Place beeps at 1-second intervals, starting 0.5s into the silence
        t = start + 0.5
        while t < end - 0.3:
            beep_times.append(t)
            t += 1.0

    print(f"Placing {len(beep_times)} beeps")

    if not beep_times:
        print("No counting pauses detected. The silences may be too short.")
        sys.exit(1)

    # Generate beep WAV
    tmpdir = tempfile.mkdtemp()
    beep_path = os.path.join(tmpdir, 'beep.wav')
    generate_beep_wav(beep_path)

    # Build ffmpeg filter to mix beeps at specified times
    # We overlay the beep multiple times using adelay
    inputs = ['-i', input_path]
    filter_parts = []
    for i, t in enumerate(beep_times):
        inputs.extend(['-i', beep_path])
        delay_ms = int(t * 1000)
        filter_parts.append(f'[{i + 1}]adelay={delay_ms}|{delay_ms}[b{i}]')

    # Mix all beeps together, then mix with original
    if len(beep_times) <= 30:
        # Simple approach: mix all at once
        beep_labels = ''.join(f'[b{i}]' for i in range(len(beep_times)))
        filter_parts.append(
            f'{beep_labels}amix=inputs={len(beep_times)}:normalize=0[beeps]'
        )
        filter_parts.append(
            '[0][beeps]amix=inputs=2:weights=1 0.5:normalize=0[out]'
        )
    else:
        # For many beeps, mix in batches of 30
        batch_size = 30
        batch_labels = []
        for batch_start in range(0, len(beep_times), batch_size):
            batch_end = min(batch_start + batch_size, len(beep_times))
            batch_id = batch_start // batch_size
            labels = ''.join(f'[b{i}]' for i in range(batch_start, batch_end))
            count = batch_end - batch_start
            filter_parts.append(
                f'{labels}amix=inputs={count}:normalize=0[batch{batch_id}]'
            )
            batch_labels.append(f'[batch{batch_id}]')

        all_batches = ''.join(batch_labels)
        if len(batch_labels) > 1:
            filter_parts.append(
                f'{all_batches}amix=inputs={len(batch_labels)}:normalize=0[beeps]'
            )
        else:
            filter_parts.append(f'{all_batches}acopy[beeps]')

        filter_parts.append(
            '[0][beeps]amix=inputs=2:weights=1 0.5:normalize=0[out]'
        )

    filter_complex = ';'.join(filter_parts)

    cmd = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-codec:a', 'libmp3lame', '-q:a', '2',
        output_path
    ]

    print("Running ffmpeg...")
    print(f"Command has {len(beep_times)} beep overlays")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("ffmpeg failed:")
        print(result.stderr[-2000:])
        sys.exit(1)

    # Cleanup
    os.remove(beep_path)
    os.rmdir(tmpdir)

    print(f"Done! Output saved to {output_path}")


if __name__ == '__main__':
    main()
