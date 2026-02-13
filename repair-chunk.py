#!/usr/bin/env python3
"""Targeted chunk repair trial — Session 32, Chunk 1.

Regenerates the opening chunk (containing "something" with echo),
selects the best of 10 generations, splices into master narration copy,
applies loudnorm + ambient mix, and encodes to MP3.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import librosa
import numpy as np
import requests

# ── Config ──────────────────────────────────────────────────────────────────

env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())

FISH_API_KEY = os.getenv("FISH_API_KEY")
FISH_VOICE_ID = "0165567b33324f518b02336ad232e31a"
FISH_API_URL = "https://api.fish.audio/v1/tts"
SAMPLE_RATE = 44100

MASTER_DIR = Path("content/audio-free/masters")
WORK_DIR = Path("content/audio-free/repair-work")
AMBIENT_DIR = Path("content/audio/ambient")

AMBIENT_VOLUME_DB = -14
AMBIENT_FADE_IN_START = 0
AMBIENT_FADE_IN_DURATION = 10    # Bible v4.5 locked
AMBIENT_FADE_OUT_DURATION = 60   # Bible v4.5 locked

# Session 32 chunk 1 data (from manifest)
CHUNK1_TEXT = "Today we are going to practise something that might seem uncomfortable at first. Sitting with our emotions. Not fixing them. Not pushing them away. Just observing."
CHUNK1_START = 0.0
CHUNK1_END = 12.62
CHUNK2_START = 20.617125
CHUNK2_END = 38.67


# ── Helper functions ────────────────────────────────────────────────────────

def get_audio_duration(audio_path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def extract_segment(source_wav, output_wav, start_sec, end_sec):
    """Extract a time segment from a WAV file."""
    duration = end_sec - start_sec
    cmd = ['ffmpeg', '-y', '-i', str(source_wav),
           '-ss', str(start_sec), '-t', str(duration),
           '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
           str(output_wav)]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_wav


def score_chunk_quality(audio_path):
    """Score a single TTS chunk for quality (echo, hiss, voice consistency)."""
    y, sr = librosa.load(str(audio_path), sr=22050)
    if len(y) < 2048:
        return {'score': 0.0, 'echo_risk': 1.0, 'hiss_risk': 0.0,
                'sp_contrast': 0.0, 'sp_flatness': 1.0, 'too_short': True}

    S = np.abs(librosa.stft(y, n_fft=2048))
    S_norm = S / (S.sum(axis=0, keepdims=True) + 1e-10)
    flux = np.sqrt(np.sum(np.diff(S_norm, axis=1)**2, axis=0))
    echo_risk = float(np.var(flux))

    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    hf_mask = freqs >= 6000
    hf_energy = float(np.mean(S[hf_mask, :] ** 2))
    total_energy = float(np.mean(S ** 2))
    hiss_risk = 10 * np.log10(hf_energy / (total_energy + 1e-10) + 1e-10)

    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    sp_contrast = float(np.mean(contrast))

    sp_flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))

    score = (
        -echo_risk * 500.0
        + sp_contrast * 0.05
        - sp_flatness * 10.0
        - hiss_risk * 0.05
    )

    return {
        'score': round(float(score), 4),
        'echo_risk': round(echo_risk, 6),
        'hiss_risk': round(hiss_risk, 2),
        'sp_contrast': round(sp_contrast, 3),
        'sp_flatness': round(sp_flatness, 5),
    }


def compute_mfcc_profile(audio_path):
    y, sr = librosa.load(str(audio_path), sr=22050)
    if len(y) < 2048:
        return None
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return mfcc.mean(axis=1)


def tonal_distance(mfcc_a, mfcc_b):
    if mfcc_a is None or mfcc_b is None:
        return 0.0
    cos_sim = np.dot(mfcc_a, mfcc_b) / (
        np.linalg.norm(mfcc_a) * np.linalg.norm(mfcc_b) + 1e-10
    )
    return round(float(1.0 - cos_sim), 6)


def generate_tts_chunk(text, output_path, chunk_num=0, emotion='calm'):
    """Generate TTS for a single chunk via Fish Audio V3-HD."""
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
    }
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

    response = requests.post(FISH_API_URL, headers=headers, json=payload, timeout=300)
    if response.status_code != 200:
        raise Exception(f"Fish API error: {response.status_code} - {response.text}")

    Path(output_path).write_bytes(response.content)
    # Convert MP3 to WAV for lossless pipeline
    wav_path = str(output_path).replace('.mp3', '.wav')
    cmd = ['ffmpeg', '-y', '-i', str(output_path),
           '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE), '-ac', '1', wav_path]
    subprocess.run(cmd, capture_output=True, check=True)
    duration = get_audio_duration(wav_path)
    return wav_path, duration


def apply_edge_fades(audio_path, output_path, fade_ms=15):
    """Apply 15ms cosine fades at edges."""
    fade_sec = fade_ms / 1000
    duration = get_audio_duration(str(audio_path))
    fade_out_start = max(0, duration - fade_sec)
    cmd = ['ffmpeg', '-y', '-i', str(audio_path),
           '-af', f'afade=t=in:st=0:d={fade_sec}:curve=hsin,afade=t=out:st={fade_out_start}:d={fade_sec}:curve=hsin',
           '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE), str(output_path)]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


# ── Main repair process ────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("TARGETED REPAIR TRIAL — Session 32, Chunk 1")
    print("=" * 60)

    master = MASTER_DIR / "32-observing-emotions_master-narration.wav"
    if not master.exists():
        print(f"ERROR: Master narration not found at {master}")
        sys.exit(1)

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 3.2: Extract context chunks ─────────────────────────────────
    print("\n── Step 3.2: Extracting context chunks ──")

    chunk1_orig = WORK_DIR / "chunk1_original.wav"
    chunk2_ref = WORK_DIR / "chunk2_reference.wav"

    extract_segment(master, chunk1_orig, CHUNK1_START, CHUNK1_END)
    extract_segment(master, chunk2_ref, CHUNK2_START, CHUNK2_END)

    print(f"  Chunk 1 (target): {CHUNK1_START:.1f}s - {CHUNK1_END:.1f}s ({get_audio_duration(str(chunk1_orig)):.2f}s)")
    print(f"  Chunk 2 (reference): {CHUNK2_START:.1f}s - {CHUNK2_END:.1f}s ({get_audio_duration(str(chunk2_ref)):.2f}s)")

    # Score original chunk 1
    orig_score = score_chunk_quality(str(chunk1_orig))
    orig_mfcc = compute_mfcc_profile(str(chunk1_orig))
    chunk2_mfcc = compute_mfcc_profile(str(chunk2_ref))
    orig_tone_dist = tonal_distance(orig_mfcc, chunk2_mfcc)

    print(f"\n  Original chunk 1 score: {orig_score['score']:.4f}")
    print(f"  Original hiss risk: {orig_score['hiss_risk']:.2f} dB")
    print(f"  Original echo risk: {orig_score['echo_risk']:.6f}")
    print(f"  Original tonal distance to chunk 2: {orig_tone_dist:.6f}")

    # ── Step 3.3: Generate 10 versions ───────────────────────────────────
    print("\n── Step 3.3: Generating 10 replacement versions ──")

    candidates = []
    for i in range(10):
        print(f"\n  Version {i+1}/10: ", end="", flush=True)
        try:
            mp3_path = WORK_DIR / f"chunk1_v{i+1}.mp3"
            wav_path, duration = generate_tts_chunk(CHUNK1_TEXT, str(mp3_path), chunk_num=0)
            print(f"{duration:.1f}s", end=" ", flush=True)

            # Check for overgeneration (> 2x expected ~12.6s)
            if duration > 25.0:
                print("REJECTED (overgeneration)")
                continue

            # Apply edge fades
            faded_path = WORK_DIR / f"chunk1_v{i+1}_faded.wav"
            apply_edge_fades(wav_path, str(faded_path))

            # Score quality
            score = score_chunk_quality(str(faded_path))
            chunk_mfcc = compute_mfcc_profile(str(faded_path))
            tone_dist = tonal_distance(chunk_mfcc, chunk2_mfcc)
            tone_penalty = tone_dist * 50.0
            combined = score['score'] - tone_penalty

            print(f"| quality={score['score']:.3f} | hiss={score['hiss_risk']:.1f}dB | echo={score['echo_risk']:.6f} | tone_dist={tone_dist:.4f} | combined={combined:.3f}")

            candidates.append({
                'version': i + 1,
                'wav_path': str(faded_path),
                'duration': duration,
                'quality_score': score['score'],
                'echo_risk': score['echo_risk'],
                'hiss_risk': score['hiss_risk'],
                'sp_contrast': score['sp_contrast'],
                'sp_flatness': score['sp_flatness'],
                'tonal_distance': tone_dist,
                'tone_penalty': tone_penalty,
                'combined_score': combined,
                'mfcc': chunk_mfcc,
            })
            time.sleep(1)  # Rate limit courtesy
        except Exception as e:
            print(f"FAILED: {e}")

    if not candidates:
        print("\nERROR: All 10 generations failed!")
        sys.exit(1)

    # ── Step 3.4: Select best ────────────────────────────────────────────
    print("\n── Step 3.4: Selecting best replacement ──")

    # Sort by combined score (quality - tonal penalty)
    candidates.sort(key=lambda c: c['combined_score'], reverse=True)

    best = candidates[0]
    print(f"\n  BEST: Version {best['version']}")
    print(f"    Combined score: {best['combined_score']:.4f} (orig: {orig_score['score'] - orig_tone_dist * 50:.4f})")
    print(f"    Quality score: {best['quality_score']:.4f} (orig: {orig_score['score']:.4f})")
    print(f"    Echo risk: {best['echo_risk']:.6f} (orig: {orig_score['echo_risk']:.6f})")
    print(f"    Hiss risk: {best['hiss_risk']:.2f} dB (orig: {orig_score['hiss_risk']:.2f} dB)")
    print(f"    Tonal distance to chunk 2: {best['tonal_distance']:.6f} (orig: {orig_tone_dist:.6f})")
    print(f"    Duration: {best['duration']:.2f}s (orig: {CHUNK1_END - CHUNK1_START:.2f}s)")

    # Print all candidates ranked
    print("\n  All candidates ranked:")
    for c in candidates:
        marker = " ← BEST" if c['version'] == best['version'] else ""
        print(f"    v{c['version']:2d}: combined={c['combined_score']:.3f} quality={c['quality_score']:.3f} tone={c['tonal_distance']:.4f} hiss={c['hiss_risk']:.1f}dB{marker}")

    # Check tonal distance threshold (brief says fail if > 0.50)
    if best['tonal_distance'] > 0.50:
        print(f"\n  WARNING: Tonal distance {best['tonal_distance']:.4f} exceeds 0.50 threshold!")
        print("  Trying other candidates...")
        for c in candidates[1:]:
            if c['tonal_distance'] <= 0.50:
                best = c
                print(f"  Using version {best['version']} instead (tone_dist={best['tonal_distance']:.4f})")
                break
        else:
            print("  ERROR: No candidate passes tonal distance threshold. Trial FAILED.")
            sys.exit(1)

    # ── Step 3.5: Splice ─────────────────────────────────────────────────
    print("\n── Step 3.5: Splicing into master narration copy ──")

    repair_narration = MASTER_DIR / "32-observing-emotions_master-narration-repair-1.wav"
    shutil.copy(str(master), str(repair_narration))

    # Load master audio
    master_y, master_sr = librosa.load(str(master), sr=SAMPLE_RATE, mono=True)
    replacement_y, _ = librosa.load(best['wav_path'], sr=SAMPLE_RATE, mono=True)

    # Calculate sample positions
    chunk1_start_sample = int(CHUNK1_START * SAMPLE_RATE)
    chunk1_end_sample = int(CHUNK1_END * SAMPLE_RATE)

    # Crossfade parameters (100ms cosine at end of chunk 1 / start of silence)
    crossfade_samples = int(0.1 * SAMPLE_RATE)  # 100ms

    # Build the repaired audio:
    # [replacement chunk with fade] + [silence + rest of master from chunk1_end onwards]
    # Since chunk 1 starts at 0.0, there's nothing before it — just replace the first segment

    # Apply cosine crossfade at the splice boundary (end of replacement → start of silence after chunk1)
    # The silence starts at chunk1_end in the original
    fade_len = min(crossfade_samples, len(replacement_y), len(master_y) - chunk1_end_sample)

    # Create output array
    new_audio = np.zeros_like(master_y, dtype=np.float32)

    # Copy replacement chunk (up to where crossfade begins)
    rep_len = len(replacement_y)
    if rep_len > len(master_y):
        rep_len = len(master_y)

    # If replacement is shorter than original chunk, pad with silence up to original end
    # If replacement is longer, we need to shift everything — but let's just use the
    # replacement duration and adjust the total narration accordingly

    # Simpler approach: use ffmpeg concat demuxer for precision
    # Split master into: [before chunk1] [chunk1] [after chunk1]
    # Replace [chunk1] with [replacement], crossfade at boundaries

    print(f"  Master duration: {len(master_y)/SAMPLE_RATE:.2f}s")
    print(f"  Replacement duration: {len(replacement_y)/SAMPLE_RATE:.2f}s")
    print(f"  Original chunk 1 duration: {CHUNK1_END - CHUNK1_START:.2f}s")

    # Since chunk 1 starts at 0.0, the splice is simpler:
    # [replacement with fade-out] + crossfade zone + [rest of master from chunk1_end with fade-in]

    # Crossfade at the boundary
    xfade_len = min(crossfade_samples, len(replacement_y), len(master_y) - chunk1_end_sample)

    # Build output:
    # Part 1: replacement up to (end - xfade_len)
    # Part 2: crossfade zone
    # Part 3: master from (chunk1_end + xfade_len) onwards

    pre_xfade = replacement_y[:-xfade_len] if xfade_len < len(replacement_y) else np.array([], dtype=np.float32)
    xfade_out = replacement_y[-xfade_len:]  # end of replacement
    xfade_in = master_y[chunk1_end_sample:chunk1_end_sample + xfade_len]  # start of what follows

    # Cosine crossfade
    t = np.linspace(0, np.pi / 2, xfade_len)
    fade_out_curve = np.cos(t).astype(np.float32)
    fade_in_curve = np.sin(t).astype(np.float32)

    xfade_zone = xfade_out * fade_out_curve + xfade_in * fade_in_curve
    post_xfade = master_y[chunk1_end_sample + xfade_len:]

    repaired = np.concatenate([pre_xfade, xfade_zone, post_xfade])

    # Save as WAV using soundfile
    import soundfile as sf
    sf.write(str(repair_narration), repaired, SAMPLE_RATE, subtype='PCM_16')

    repair_duration = len(repaired) / SAMPLE_RATE
    print(f"  Repaired narration duration: {repair_duration:.2f}s")
    print(f"  Duration difference: {repair_duration - len(master_y)/SAMPLE_RATE:+.2f}s")

    # ── Step 3.6: MFCC tonal check ──────────────────────────────────────
    print("\n── Step 3.6: MFCC tonal check ──")

    # Extract the replacement chunk region from the repaired narration
    repaired_chunk1 = WORK_DIR / "repaired_chunk1_extracted.wav"
    extract_segment(str(repair_narration), str(repaired_chunk1), 0.0, len(replacement_y) / SAMPLE_RATE)

    repaired_mfcc = compute_mfcc_profile(str(repaired_chunk1))
    tone_dist_post = tonal_distance(repaired_mfcc, chunk2_mfcc)
    print(f"  Tonal distance (repaired chunk 1 → chunk 2): {tone_dist_post:.6f}")
    print(f"  Threshold: 0.50")
    if tone_dist_post > 0.50:
        print("  FAIL — tonal distance exceeds threshold")
    else:
        print("  PASS")

    # ── Step 3.7: Apply loudnorm ─────────────────────────────────────────
    print("\n── Step 3.7: Applying whole-file loudnorm ──")

    repair_normed = WORK_DIR / "32-repair-1_normed.wav"
    cmd = ['ffmpeg', '-y', '-i', str(repair_narration),
           '-af', 'loudnorm=I=-26:TP=-2:LRA=11',
           '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
           str(repair_normed)]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  Loudnorm applied. Duration: {get_audio_duration(str(repair_normed)):.2f}s")

    # ── Step 3.8: Mix ambient ────────────────────────────────────────────
    print("\n── Step 3.8: Mixing garden ambient ──")

    repair_mixed = WORK_DIR / "32-repair-1_mixed.wav"
    voice_duration = get_audio_duration(str(repair_normed))
    fade_out_start = max(0, voice_duration - AMBIENT_FADE_OUT_DURATION)

    # Find garden ambient
    ambient_path = None
    for ext in ['wav', 'mp3']:
        for suffix in ['-8hr', '-extended', '']:
            candidate = AMBIENT_DIR / f"garden{suffix}.{ext}"
            if candidate.exists():
                ambient_path = candidate
                break
        if ambient_path:
            break

    if not ambient_path:
        print("  ERROR: Garden ambient not found!")
        sys.exit(1)

    print(f"  Ambient: {ambient_path}")
    print(f"  Volume: {AMBIENT_VOLUME_DB}dB, Fade in: {AMBIENT_FADE_IN_DURATION}s, Fade out: {AMBIENT_FADE_OUT_DURATION}s")

    cmd = ['ffmpeg', '-y',
           '-i', str(repair_normed),
           '-ss', '10', '-i', str(ambient_path),
           '-filter_complex',
           f"[1:a]volume={AMBIENT_VOLUME_DB}dB,"
           f"afade=t=in:st={AMBIENT_FADE_IN_START}:d={AMBIENT_FADE_IN_DURATION},"
           f"afade=t=out:st={fade_out_start}:d={AMBIENT_FADE_OUT_DURATION}[amb];"
           f"[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2:normalize=0",
           '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
           str(repair_mixed)]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  Mixed duration: {get_audio_duration(str(repair_mixed)):.2f}s")

    # ── Encode to MP3 ───────────────────────────────────────────────────
    print("\n── Encoding to 128kbps MP3 ──")

    repair_mp3 = WORK_DIR / "32-observing-emotions-repair-1.mp3"
    cmd = ['ffmpeg', '-y', '-i', str(repair_mixed),
           '-c:a', 'libmp3lame', '-b:a', '128k',
           str(repair_mp3)]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  MP3: {repair_mp3} ({os.path.getsize(str(repair_mp3)) / 1024 / 1024:.1f} MB)")

    # ── Save results ─────────────────────────────────────────────────────
    results = {
        'session': '32-observing-emotions',
        'chunk_repaired': 1,
        'chunk_text': CHUNK1_TEXT,
        'defect': 'echo on word "something"',
        'generations': len(candidates),
        'best_version': best['version'],
        'best_combined_score': best['combined_score'],
        'best_quality_score': best['quality_score'],
        'best_echo_risk': best['echo_risk'],
        'best_hiss_risk': best['hiss_risk'],
        'best_tonal_distance': best['tonal_distance'],
        'original_quality_score': orig_score['score'],
        'original_echo_risk': orig_score['echo_risk'],
        'original_hiss_risk': orig_score['hiss_risk'],
        'original_tonal_distance': orig_tone_dist,
        'post_splice_tonal_distance': tone_dist_post,
        'all_candidates': [{k: v for k, v in c.items() if k != 'mfcc'} for c in candidates],
        'repair_narration': str(repair_narration),
        'repair_mp3': str(repair_mp3),
    }

    results_path = WORK_DIR / "repair-results.json"
    with open(str(results_path), 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n  Results saved to: {results_path}")
    print(f"  Repair narration: {repair_narration}")
    print(f"  Repair MP3: {repair_mp3}")

    print("\n" + "=" * 60)
    print("REPAIR COMPLETE — Ready for QA gates and R2 upload")
    print("=" * 60)

    return results


if __name__ == "__main__":
    results = main()
