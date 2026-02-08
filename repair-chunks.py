#!/usr/bin/env python3
"""Targeted chunk repair for build-session-v3.py builds.

Regenerates specific bad chunks while keeping all good chunks intact.
Rebuilds the full WAV from scratch using original good audio + fresh TTS for bad chunks.

Usage:
    python3 repair-chunks.py 36-loving-kindness-intro --chunks 22,36,11,34,39
"""

import sys
import os
import json
import tempfile
import shutil
import subprocess
import numpy as np
import wave
from pathlib import Path

# Import from build script
sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module

# We need these from the build script
build = import_module('build-session-v3')

SAMPLE_RATE = build.SAMPLE_RATE
OUTPUT_DIR = build.OUTPUT_DIR
OUTPUT_RAW_DIR = build.OUTPUT_RAW_DIR


def load_wav_samples(wav_path):
    """Load WAV file as numpy float64 array."""
    w = wave.open(str(wav_path), 'r')
    n = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw = w.readframes(n)
    w.close()
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)
    return samples, sr


def samples_to_wav(samples, sr, output_path):
    """Save numpy float64 samples as 16-bit WAV."""
    int_samples = np.clip(samples, -32768, 32767).astype(np.int16)
    w = wave.open(str(output_path), 'w')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(int_samples.tobytes())
    w.close()


def extract_text_segments(manifest):
    """Get text segment info from manifest, with 1-based chunk numbers."""
    text_segs = []
    chunk_num = 0
    for seg in manifest['segments']:
        if seg['type'] == 'text':
            chunk_num += 1
            text_segs.append({
                'chunk_num': chunk_num,
                'text': seg['text'],
                'start_time': seg['start_time'],
                'end_time': seg['end_time'],
                'duration': seg['duration'],
            })
    return text_segs


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Targeted chunk repair')
    parser.add_argument('session_name', help='Session name (e.g., 36-loving-kindness-intro)')
    parser.add_argument('--chunks', required=True, help='Comma-separated chunk numbers to regenerate (1-based)')
    parser.add_argument('--no-deploy', action='store_true', default=True)
    args = parser.parse_args()

    session_name = args.session_name
    bad_chunks = set(int(c.strip()) for c in args.chunks.split(','))

    # Load manifest
    manifest_path = OUTPUT_DIR / f"{session_name}_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Load pre-cleanup WAV
    precleanup_path = OUTPUT_RAW_DIR / f"{session_name}_precleanup.wav"
    if not precleanup_path.exists():
        print(f"ERROR: Pre-cleanup WAV not found: {precleanup_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  TARGETED REPAIR: {session_name}")
    print(f"  Chunks to regenerate: {sorted(bad_chunks)}")
    print(f"{'='*60}")

    text_segs = extract_text_segments(manifest)
    original_samples, sr = load_wav_samples(precleanup_path)
    print(f"  Original pre-cleanup: {len(original_samples)/sr:.1f}s ({len(original_samples)} samples)")

    with tempfile.TemporaryDirectory() as temp_dir:
        # For each bad chunk, regenerate via Fish TTS
        new_chunk_audio = {}  # chunk_num -> numpy samples

        for seg in text_segs:
            if seg['chunk_num'] not in bad_chunks:
                continue

            print(f"\n  Regenerating chunk {seg['chunk_num']}: \"{seg['text'][:60]}...\"")

            expected_dur = seg.get('expected', len(seg['text']) / 15.0)
            max_dur = max(expected_dur * 2.5, 20.0)  # Allow 2.5x expected, min 20s

            # Generate new TTS with retry on overgeneration
            chunk_path = os.path.join(temp_dir, f"repair_{seg['chunk_num']}.mp3")
            for attempt in range(3):
                build.generate_tts_chunk(seg['text'], chunk_path, seg['chunk_num'] - 1)
                gen_dur = build.get_audio_duration(chunk_path)
                if gen_dur <= max_dur:
                    break
                print(f"    OVERGENERATION: {gen_dur:.1f}s (max {max_dur:.1f}s) — retrying ({attempt+1}/3)")
            else:
                print(f"    WARNING: Overgeneration persisted after 3 retries ({gen_dur:.1f}s)")

            # Convert to WAV
            wav_path = os.path.join(temp_dir, f"repair_{seg['chunk_num']}.wav")
            subprocess.run([
                'ffmpeg', '-y', '-i', chunk_path,
                '-c:a', 'pcm_s16le', '-ar', str(sr), '-ac', '1',
                wav_path
            ], capture_output=True, check=True)

            # Normalize (per-chunk loudnorm)
            normed_path = os.path.join(temp_dir, f"repair_{seg['chunk_num']}_normed.wav")
            build.normalize_chunk(wav_path, normed_path)

            # Apply edge fades
            faded_path = os.path.join(temp_dir, f"repair_{seg['chunk_num']}_faded.wav")
            build.apply_edge_fades(normed_path, faded_path)

            # Load as samples
            new_samples, _ = load_wav_samples(faded_path)
            new_chunk_audio[seg['chunk_num']] = new_samples

            old_dur = seg['duration']
            new_dur = len(new_samples) / sr
            print(f"    Old: {old_dur:.2f}s → New: {new_dur:.2f}s (delta: {new_dur - old_dur:+.2f}s)")

        # Now rebuild the full pre-cleanup WAV
        # Walk through manifest segments, extracting from original or using new audio
        print(f"\n  Rebuilding pre-cleanup WAV...")
        rebuilt_parts = []
        new_manifest_segments = []
        current_time = 0.0

        chunk_idx = 0
        for seg in manifest['segments']:
            if seg['type'] == 'text':
                chunk_idx += 1

                if chunk_idx in new_chunk_audio:
                    # Use regenerated audio
                    audio = new_chunk_audio[chunk_idx]
                    duration = len(audio) / sr
                    print(f"    Chunk {chunk_idx}: REPLACED ({seg['duration']:.2f}s → {duration:.2f}s)")
                else:
                    # Extract from original pre-cleanup WAV
                    start_sample = int(seg['start_time'] * sr)
                    end_sample = int(seg['end_time'] * sr)
                    end_sample = min(end_sample, len(original_samples))
                    audio = original_samples[start_sample:end_sample]
                    duration = len(audio) / sr

                rebuilt_parts.append(audio)
                new_manifest_segments.append({
                    'index': len(new_manifest_segments),
                    'type': 'text',
                    'start_time': current_time,
                    'text': seg['text'],
                    'duration': round(duration, 2),
                    'expected': seg.get('expected', round(len(seg['text']) / 15.0, 2)),
                    'end_time': round(current_time + duration, 2),
                })
                current_time += duration

            elif seg['type'] == 'silence':
                # Generate silence of same duration
                silence_duration = seg['duration']
                silence_samples = np.zeros(int(silence_duration * sr))
                rebuilt_parts.append(silence_samples)
                new_manifest_segments.append({
                    'index': len(new_manifest_segments),
                    'type': 'silence',
                    'start_time': round(current_time, 2),
                    'duration': round(silence_duration, 1),
                    'end_time': round(current_time + silence_duration, 2),
                })
                current_time += silence_duration

        # Concatenate all parts
        rebuilt_wav = np.concatenate(rebuilt_parts)
        print(f"  Rebuilt: {len(rebuilt_wav)/sr:.1f}s (was {len(original_samples)/sr:.1f}s)")

        # Save new pre-cleanup WAV
        rebuilt_precleanup = os.path.join(temp_dir, "rebuilt_precleanup.wav")
        samples_to_wav(rebuilt_wav, sr, rebuilt_precleanup)

        # Overwrite the pre-cleanup file
        shutil.copy(rebuilt_precleanup, str(precleanup_path))
        print(f"  Saved: {precleanup_path}")

        # Run cleanup (Fish chain)
        print(f"\n  Running cleanup (full Fish chain)...")
        voice_path = os.path.join(temp_dir, "voice_cleaned.wav")
        build.cleanup_audio(rebuilt_precleanup, voice_path)

        # Save as raw narration WAV
        raw_wav_path = OUTPUT_RAW_DIR / f"{session_name}.wav"
        shutil.copy(voice_path, str(raw_wav_path))
        print(f"  Cleaned narration: {raw_wav_path}")

        voice_duration = build.get_audio_duration(voice_path)
        print(f"  Duration: {voice_duration/60:.1f} min")

        # Update manifest
        new_manifest = {
            'generated': manifest['generated'],
            'script': manifest['script'],
            'category': manifest.get('category', 'mindfulness'),
            'ambient': manifest.get('ambient'),
            'total_tts_duration': round(sum(s['duration'] for s in new_manifest_segments if s['type'] == 'text'), 2),
            'total_silence': round(sum(s['duration'] for s in new_manifest_segments if s['type'] == 'silence'), 2),
            'text_segments': sum(1 for s in new_manifest_segments if s['type'] == 'text'),
            'segments': new_manifest_segments,
        }
        with open(manifest_path, 'w') as f:
            json.dump(new_manifest, f, indent=2)
        print(f"  Manifest updated: {manifest_path}")

        # Mix ambient
        ambient_name = manifest.get('ambient')
        if ambient_name:
            print(f"\n  Mixing ambient '{ambient_name}'...")
            final_path = OUTPUT_DIR / f"{session_name}.mp3"
            mixed_path = os.path.join(temp_dir, "mixed.wav")
            build.mix_ambient(voice_path, ambient_name, mixed_path)
            # Encode final MP3
            print(f"\n  Encoding final MP3 at 128kbps...")
            subprocess.run([
                'ffmpeg', '-y', '-i', mixed_path,
                '-c:a', 'libmp3lame', '-b:a', '128k',
                str(final_path)
            ], capture_output=True, check=True)
        else:
            final_path = OUTPUT_DIR / f"{session_name}.mp3"
            subprocess.run([
                'ffmpeg', '-y', '-i', voice_path,
                '-c:a', 'libmp3lame', '-b:a', '128k',
                str(final_path)
            ], capture_output=True, check=True)

        print(f"\n  BUILD COMPLETE: {final_path}")

        # Run QA
        raw_mp3_path = OUTPUT_DIR / f"raw_{session_name}.mp3"
        # Create raw MP3 for click detection
        subprocess.run([
            'ffmpeg', '-y', '-i', str(raw_wav_path),
            '-c:a', 'libmp3lame', '-b:a', '128k',
            str(raw_mp3_path)
        ], capture_output=True, check=True)

        qa_passed = build.qa_loop(
            str(final_path), str(raw_mp3_path), new_manifest,
            ambient_name=ambient_name,
            raw_narration_wav=str(raw_wav_path),
            pre_cleanup_wav=str(precleanup_path),
            session_name=session_name,
        )

        if qa_passed:
            print(f"\n  REPAIR SUCCESSFUL — All QA gates passed!")
            print(f"  Human review still MANDATORY.")
        else:
            print(f"\n  REPAIR FAILED — QA rejected the repaired build")

        return qa_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
