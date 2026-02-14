#!/usr/bin/env python3
"""One-off repair: Split S01 chunk 7 into 3 sub-lines with proper silences."""

import asyncio
import aiohttp
import json
import subprocess
import numpy as np
import struct
import wave
from pathlib import Path
import os
import time

# Load .env manually
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

FISH_API_KEY = os.getenv('FISH_API_KEY')
FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"
SAMPLE_RATE = 44100
CANDIDATES_PER_LINE = 5

VAULT_DIR = Path(__file__).parent.parent / "content/audio-free/vault/01-morning-meditation"

SUB_LINES = [
    ("Feel the support beneath you — the chair, the floor, the bed.", 8.0),
    ("You're held. You're safe.", 50.0),
    ("Scan down through your arms... your hands.", 0.0),  # no trailing silence — vault-assemble adds it
]


def read_wav_mono(path):
    """Read WAV file as mono int16 numpy array."""
    with wave.open(str(path), 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16)
        if wf.getnchannels() == 2:
            samples = samples[::2]
        return samples, wf.getframerate()


def write_wav(path, samples, sr=44100):
    """Write mono int16 WAV."""
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())


async def generate_candidate(session, text, out_path, emotion='calm'):
    """Generate one TTS candidate via Fish API."""
    payload = {
        "text": text,
        "reference_id": FISH_VOICE_ID,
        "format": "mp3",
        "temperature": 0.3,
        "version": "v3-hd",
        "emotion": emotion,
        "prosody": {"speed": 0.95, "volume": 0},
        "sample_rate": SAMPLE_RATE,
    }
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
    }

    mp3_tmp = str(out_path) + ".tmp.mp3"
    for attempt in range(4):
        try:
            async with session.post(FISH_API_URL, json=payload, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status == 429:
                    await asyncio.sleep(2 ** attempt + 1)
                    continue
                if resp.status != 200:
                    body = await resp.text()
                    raise Exception(f"Fish API {resp.status}: {body[:200]}")
                data = await resp.read()
                Path(mp3_tmp).write_bytes(data)
                break
        except (asyncio.TimeoutError, aiohttp.ClientError):
            if attempt < 3:
                await asyncio.sleep(2 ** attempt)
            continue
    else:
        raise Exception(f"Failed after 4 attempts for: {text[:50]}")

    # Convert MP3 to WAV
    subprocess.run([
        'ffmpeg', '-y', '-i', mp3_tmp,
        '-ar', str(SAMPLE_RATE), '-ac', '1', '-sample_fmt', 's16',
        str(out_path)
    ], capture_output=True, timeout=30)
    Path(mp3_tmp).unlink(missing_ok=True)
    return out_path


def score_candidate(wav_path, text):
    """Simple scoring: duration sanity + RMS energy."""
    samples, sr = read_wav_mono(wav_path)
    duration = len(samples) / sr
    chars = len(text)

    # Expected duration range (10-13 chars/sec for Fish)
    expected_min = chars / 13.0
    expected_max = chars / 10.0

    # Penalize if outside expected range (truncation or too slow)
    if duration < expected_min * 0.7:
        return -1.0, duration  # Likely truncated
    if duration > expected_max * 1.5:
        return -0.5, duration  # Too slow

    # RMS as quality proxy
    rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
    rms_db = 20 * np.log10(max(rms, 1e-10) / 32768)

    # Prefer moderate RMS (-25 to -15 dB range)
    score = 1.0
    if rms_db < -30:
        score -= 0.3
    if rms_db > -10:
        score -= 0.3

    return score, duration


async def main():
    work_dir = VAULT_DIR / "c07_repair"
    work_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  S01 CHUNK 7 REPAIR — Generating sub-line candidates")
    print(f"{'='*60}")

    async with aiohttp.ClientSession() as session:
        tasks = []
        for li, (text, _) in enumerate(SUB_LINES):
            for ci in range(CANDIDATES_PER_LINE):
                out = work_dir / f"sub{li}_v{ci:02d}.wav"
                tasks.append((li, ci, text, generate_candidate(session, text, out)))

        results = {}
        for li, ci, text, coro in tasks:
            try:
                path = await coro
                score, dur = score_candidate(path, text)
                results.setdefault(li, []).append((ci, path, score, dur))
                print(f"  sub{li}_v{ci:02d}: {dur:.2f}s  score={score:.2f}  \"{text[:50]}\"")
            except Exception as e:
                print(f"  sub{li}_v{ci:02d}: FAILED — {e}")

    # Pick best for each sub-line
    print(f"\n  --- Best picks ---")
    best_wavs = []
    for li, (text, silence_after) in enumerate(SUB_LINES):
        candidates = results.get(li, [])
        if not candidates:
            print(f"  ERROR: No candidates for sub-line {li}")
            return
        candidates.sort(key=lambda x: x[2], reverse=True)
        best = candidates[0]
        print(f"  sub{li}: v{best[0]:02d} ({best[3]:.2f}s, score={best[2]:.2f}) — \"{text[:60]}\"")
        best_wavs.append((best[1], silence_after))

    # Stitch together with silences
    print(f"\n  --- Stitching ---")
    segments = []
    for wav_path, silence_sec in best_wavs:
        samples, sr = read_wav_mono(wav_path)
        segments.append(samples)
        if silence_sec > 0:
            silence_samples = np.zeros(int(silence_sec * sr), dtype=np.int16)
            segments.append(silence_samples)
            print(f"  + {len(samples)/sr:.2f}s speech + {silence_sec}s silence")
        else:
            print(f"  + {len(samples)/sr:.2f}s speech (final)")

    combined = np.concatenate(segments)
    total_dur = len(combined) / SAMPLE_RATE

    # Write replacement pick
    pick_path = VAULT_DIR / "picks" / "c07_pick.wav"
    write_wav(pick_path, combined, SAMPLE_RATE)
    print(f"\n  Replacement: {pick_path}")
    print(f"  Total duration: {total_dur:.1f}s (was 13.5s)")
    print(f"  Done.\n")


if __name__ == '__main__':
    asyncio.run(main())
