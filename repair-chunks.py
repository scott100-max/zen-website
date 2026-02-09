#!/usr/bin/env python3
"""Targeted chunk repair for build-session-v3.py builds.

Regenerates specific bad chunks while keeping all good chunks intact.
Rebuilds the full WAV from scratch using original good audio + fresh TTS for bad chunks.

Supports:
  - Text overrides: change the spoken text of a chunk
  - Chunk splitting: replace one chunk with two (cold-start echo fix)
  - Best-of-N scored generation (per Bible 16A)

Usage:
    # Basic repair (same text, best-of-10)
    python3 repair-chunks.py 36-loving-kindness-intro --chunks 22,36

    # With text override (change spoken text)
    python3 repair-chunks.py 01-morning-meditation --chunks 48 \
        --text-override '48:New text for chunk 48 here.'

    # With chunk split (cold-start echo fix — Bible Section 13)
    python3 repair-chunks.py 01-morning-meditation --chunks 1 \
        --split-chunk '1:This is your morning meditation.|A gentle way to start your day.'

    # Combined
    python3 repair-chunks.py 01-morning-meditation --chunks 1,48 \
        --split-chunk '1:Short opening.|Rest of the opening.' \
        --text-override '48:New closing text here.'
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


def generate_scored_chunk(text, output_name, chunk_num, temp_dir, sr,
                          best_of=10, prev_mfcc=None):
    """Generate a chunk with best-of-N scoring per Bible 16A.

    Uses generate_chunk_with_qa() for scored generation, then converts
    to WAV and applies edge fades. NO per-chunk loudnorm (whole-file only).

    output_name: unique filename (e.g. "repair_1.mp3", "split_1a.mp3")
    Returns (samples, mfcc_profile, score_details, flagged).
    """
    base = os.path.splitext(output_name)[0]
    mp3_path = os.path.join(temp_dir, output_name)
    _, details, flagged, mfcc = build.generate_chunk_with_qa(
        text, mp3_path, chunk_num - 1,
        n_versions=best_of, max_retries=best_of,
        prev_chunk_mfcc=prev_mfcc,
    )

    # Convert to WAV (lossless pipeline)
    wav_path = os.path.join(temp_dir, f"{base}.wav")
    subprocess.run([
        'ffmpeg', '-y', '-i', mp3_path,
        '-c:a', 'pcm_s16le', '-ar', str(sr), '-ac', '1',
        wav_path
    ], capture_output=True, check=True)

    # Apply edge fades (15ms cosine) — NO per-chunk loudnorm
    faded_path = os.path.join(temp_dir, f"{base}_faded.wav")
    build.apply_edge_fades(wav_path, faded_path)

    samples, _ = load_wav_samples(faded_path)
    return samples, mfcc, details, flagged


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Targeted chunk repair')
    parser.add_argument('session_name', help='Session name (e.g., 36-loving-kindness-intro)')
    parser.add_argument('--chunks', required=True, help='Comma-separated chunk numbers to regenerate (1-based)')
    parser.add_argument('--text-override', action='append', default=[],
                        help='Override chunk text: CHUNK:NEW_TEXT (can repeat)')
    parser.add_argument('--split-chunk', action='append', default=[],
                        help='Split chunk into two: CHUNK:TEXT_A|TEXT_B (can repeat)')
    parser.add_argument('--best-of', type=int, default=10,
                        help='Number of versions to generate per chunk (default: 10)')
    parser.add_argument('--no-deploy', action='store_true', default=True)
    args = parser.parse_args()

    session_name = args.session_name
    bad_chunks = set(int(c.strip()) for c in args.chunks.split(','))

    # Parse text overrides: {chunk_num: new_text}
    text_overrides = {}
    for ov in args.text_override:
        chunk_str, text = ov.split(':', 1)
        text_overrides[int(chunk_str)] = text

    # Parse chunk splits: {chunk_num: (text_a, text_b)}
    split_chunks = {}
    for sp in args.split_chunk:
        chunk_str, texts = sp.split(':', 1)
        parts = texts.split('|', 1)
        if len(parts) != 2:
            print(f"ERROR: --split-chunk must have format CHUNK:TEXT_A|TEXT_B, got: {sp}")
            sys.exit(1)
        split_chunks[int(chunk_str)] = (parts[0].strip(), parts[1].strip())

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

    # Get category for pause duration
    category = manifest.get('category', 'mindfulness')
    pause_duration = build.PAUSE_PROFILES.get(category, build.PAUSE_PROFILES['mindfulness'])[1]

    print(f"\n{'='*60}")
    print(f"  TARGETED REPAIR: {session_name}")
    print(f"  Category: {category}")
    print(f"  Chunks to regenerate: {sorted(bad_chunks)}")
    if text_overrides:
        print(f"  Text overrides: chunks {sorted(text_overrides.keys())}")
    if split_chunks:
        print(f"  Chunk splits: chunks {sorted(split_chunks.keys())}")
    print(f"  Best-of-N: {args.best_of} versions per chunk")
    print(f"{'='*60}")

    text_segs = extract_text_segments(manifest)
    original_samples, sr = load_wav_samples(precleanup_path)
    print(f"  Original pre-cleanup: {len(original_samples)/sr:.1f}s ({len(original_samples)} samples)")

    with tempfile.TemporaryDirectory() as temp_dir:
        # For each bad chunk, regenerate via Fish TTS with scoring
        # new_chunk_audio: chunk_num -> numpy samples (for simple replacements)
        # split_chunk_audio: chunk_num -> (samples_a, silence_samples, samples_b)
        new_chunk_audio = {}
        new_chunk_text = {}
        new_chunk_details = {}
        split_chunk_audio = {}
        split_chunk_texts = {}

        for seg in text_segs:
            if seg['chunk_num'] not in bad_chunks:
                continue

            chunk_num = seg['chunk_num']

            if chunk_num in split_chunks:
                # --- CHUNK SPLIT (cold-start echo fix) ---
                text_a, text_b = split_chunks[chunk_num]
                print(f"\n  SPLITTING chunk {chunk_num}:")
                print(f"    0a: \"{text_a}\"")
                print(f"    0b: \"{text_b}\"")
                print(f"    Pause: {pause_duration}s ({category})")

                # Generate chunk 0a (no conditioning — cold-start, but short = safe)
                print(f"\n    Generating chunk {chunk_num}a (cold-start, no conditioning)...")
                samples_a, mfcc_a, details_a, flagged_a = generate_scored_chunk(
                    text_a, f"split_{chunk_num}a.mp3", chunk_num, temp_dir, sr,
                    best_of=args.best_of, prev_mfcc=None,
                )
                score_a = details_a.get('combined_score', details_a.get('score', 0))
                print(f"    Chunk {chunk_num}a: {len(samples_a)/sr:.2f}s, score={score_a:.3f}, flagged={flagged_a}")

                # Generate chunk 0b (conditioned on 0a's MFCC)
                print(f"\n    Generating chunk {chunk_num}b (conditioned on {chunk_num}a)...")
                samples_b, mfcc_b, details_b, flagged_b = generate_scored_chunk(
                    text_b, f"split_{chunk_num}b.mp3", chunk_num, temp_dir, sr,
                    best_of=args.best_of, prev_mfcc=mfcc_a,
                )
                score_b = details_b.get('combined_score', details_b.get('score', 0))
                print(f"    Chunk {chunk_num}b: {len(samples_b)/sr:.2f}s, score={score_b:.3f}, flagged={flagged_b}")

                # Silence between the two
                silence_samples = np.zeros(int(pause_duration * sr))

                old_dur = seg['duration']
                new_dur = (len(samples_a) + len(silence_samples) + len(samples_b)) / sr
                print(f"    Total: {old_dur:.2f}s → {new_dur:.2f}s (delta: {new_dur - old_dur:+.2f}s)")

                split_chunk_audio[chunk_num] = (samples_a, silence_samples, samples_b)
                split_chunk_texts[chunk_num] = (text_a, text_b)
                new_chunk_details[chunk_num] = {'a': details_a, 'b': details_b}

            else:
                # --- SIMPLE REPLACEMENT (same or overridden text) ---
                text = text_overrides.get(chunk_num, seg['text'])
                if chunk_num in text_overrides:
                    print(f"\n  Regenerating chunk {chunk_num} (TEXT OVERRIDE):")
                    print(f"    Old: \"{seg['text'][:80]}...\"")
                    print(f"    New: \"{text[:80]}...\"")
                else:
                    print(f"\n  Regenerating chunk {chunk_num}: \"{text[:60]}...\"")

                # Get MFCC of the previous chunk for tonal consistency
                prev_mfcc = None
                if chunk_num > 1:
                    # Find previous text segment in manifest
                    for prev_seg in text_segs:
                        if prev_seg['chunk_num'] == chunk_num - 1:
                            # Extract previous chunk audio and compute MFCC
                            start_s = int(prev_seg['start_time'] * sr)
                            end_s = int(prev_seg['end_time'] * sr)
                            end_s = min(end_s, len(original_samples))
                            prev_wav = os.path.join(temp_dir, f"prev_{chunk_num}.wav")
                            samples_to_wav(original_samples[start_s:end_s], sr, prev_wav)
                            prev_mfcc = build.compute_mfcc_profile(prev_wav)
                            break

                samples, mfcc, details, flagged = generate_scored_chunk(
                    text, f"repair_{chunk_num}.mp3", chunk_num, temp_dir, sr,
                    best_of=args.best_of, prev_mfcc=prev_mfcc,
                )
                score = details.get('combined_score', details.get('score', 0))
                old_dur = seg['duration']
                new_dur = len(samples) / sr
                print(f"    {old_dur:.2f}s → {new_dur:.2f}s (delta: {new_dur - old_dur:+.2f}s), score={score:.3f}, flagged={flagged}")

                new_chunk_audio[chunk_num] = samples
                new_chunk_text[chunk_num] = text
                new_chunk_details[chunk_num] = details

        # Now rebuild the full pre-cleanup WAV
        print(f"\n  Rebuilding pre-cleanup WAV...")
        rebuilt_parts = []
        new_manifest_segments = []
        current_time = 0.0

        chunk_idx = 0
        for seg in manifest['segments']:
            if seg['type'] == 'text':
                chunk_idx += 1

                if chunk_idx in split_chunk_audio:
                    # SPLIT: insert chunk_a + silence + chunk_b
                    samples_a, silence, samples_b = split_chunk_audio[chunk_idx]
                    text_a, text_b = split_chunk_texts[chunk_idx]

                    # Chunk A
                    dur_a = len(samples_a) / sr
                    rebuilt_parts.append(samples_a)
                    new_manifest_segments.append({
                        'index': len(new_manifest_segments),
                        'type': 'text',
                        'start_time': round(current_time, 4),
                        'text': text_a,
                        'duration': round(dur_a, 2),
                        'expected': round(len(text_a) / 15.0, 2),
                        'end_time': round(current_time + dur_a, 4),
                    })
                    current_time += dur_a
                    print(f"    Chunk {chunk_idx}a: SPLIT INSERT ({dur_a:.2f}s) \"{text_a[:40]}\"")

                    # Silence between
                    dur_sil = len(silence) / sr
                    rebuilt_parts.append(silence)
                    new_manifest_segments.append({
                        'index': len(new_manifest_segments),
                        'type': 'silence',
                        'start_time': round(current_time, 4),
                        'duration': round(dur_sil, 1),
                        'end_time': round(current_time + dur_sil, 4),
                    })
                    current_time += dur_sil

                    # Chunk B
                    dur_b = len(samples_b) / sr
                    rebuilt_parts.append(samples_b)
                    new_manifest_segments.append({
                        'index': len(new_manifest_segments),
                        'type': 'text',
                        'start_time': round(current_time, 4),
                        'text': text_b,
                        'duration': round(dur_b, 2),
                        'expected': round(len(text_b) / 15.0, 2),
                        'end_time': round(current_time + dur_b, 4),
                    })
                    current_time += dur_b
                    print(f"    Chunk {chunk_idx}b: SPLIT INSERT ({dur_b:.2f}s) \"{text_b[:40]}\"")

                elif chunk_idx in new_chunk_audio:
                    # Use regenerated audio (possibly with text override)
                    audio = new_chunk_audio[chunk_idx]
                    duration = len(audio) / sr
                    text = new_chunk_text.get(chunk_idx, seg['text'])
                    print(f"    Chunk {chunk_idx}: REPLACED ({seg['duration']:.2f}s → {duration:.2f}s)")

                    rebuilt_parts.append(audio)
                    new_manifest_segments.append({
                        'index': len(new_manifest_segments),
                        'type': 'text',
                        'start_time': round(current_time, 4),
                        'text': text,
                        'duration': round(duration, 2),
                        'expected': round(len(text) / 15.0, 2),
                        'end_time': round(current_time + duration, 4),
                    })
                    current_time += duration

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
                        'start_time': round(current_time, 4),
                        'text': seg['text'],
                        'duration': round(duration, 2),
                        'expected': seg.get('expected', round(len(seg['text']) / 15.0, 2)),
                        'end_time': round(current_time + duration, 4),
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
                    'start_time': round(current_time, 4),
                    'duration': round(silence_duration, 1),
                    'end_time': round(current_time + silence_duration, 4),
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

        # Run cleanup (Fish chain — whole-file loudnorm only)
        print(f"\n  Running cleanup (whole-file loudnorm)...")
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

        # Print summary
        print(f"\n{'='*60}")
        print(f"  REPAIR SUMMARY: {session_name}")
        print(f"{'='*60}")
        for cn in sorted(bad_chunks):
            if cn in split_chunk_audio:
                ta, tb = split_chunk_texts[cn]
                d = new_chunk_details.get(cn, {})
                sa = d.get('a', {}).get('combined_score', d.get('a', {}).get('score', '?'))
                sb = d.get('b', {}).get('combined_score', d.get('b', {}).get('score', '?'))
                print(f"  Chunk {cn}: SPLIT → \"{ta[:30]}\" ({sa}) + \"{tb[:30]}\" ({sb})")
            elif cn in new_chunk_audio:
                d = new_chunk_details.get(cn, {})
                s = d.get('combined_score', d.get('score', '?'))
                t = new_chunk_text.get(cn, '(original text)')
                label = "TEXT OVERRIDE" if cn in text_overrides else "REGENERATED"
                print(f"  Chunk {cn}: {label} → score={s}, \"{t[:50]}\"")
        print(f"  QA: {'PASSED' if qa_passed else 'FAILED'}")
        print(f"  Duration: {voice_duration/60:.1f} min")
        print(f"{'='*60}")

        return qa_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
