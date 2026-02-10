#!/usr/bin/env python3
"""
Batch rebuild — runs build-session-v3.py up to N times,
keeps the build where ALL chunks meet a minimum score threshold.
Saves every build's manifest for comparison.
"""

import subprocess
import json
import shutil
import sys
import os
from pathlib import Path
from datetime import datetime

SESSION = "narrator-welcome"
MAX_BUILDS = 25
MIN_CHUNK_SCORE = 0.75  # Every chunk must be at or above this
OUTPUT_DIR = Path("content/audio-free")
RAW_DIR = Path("content/audio-free/raw")
ARCHIVE_DIR = Path("content/audio-free/batch-archive")
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

def get_chunk_scores(manifest_path):
    """Extract per-chunk scores from the build manifest."""
    with open(manifest_path) as f:
        manifest = json.load(f)

    # The manifest stores flagged chunks with scores, but we need ALL chunk scores.
    # The build script prints scores to stdout — we'll parse those instead.
    return manifest

def parse_scores_from_output(output):
    """Parse per-chunk best scores from build stdout."""
    scores = {}
    current_chunk = None
    best_score = None

    for line in output.split('\n'):
        line = line.strip()

        # Detect chunk start: "Chunk N QA (best-of-X):"
        if 'Chunk' in line and 'QA (best-of' in line:
            # Save previous chunk's best
            if current_chunk is not None and best_score is not None:
                scores[current_chunk] = best_score

            # Parse chunk number (1-indexed in output)
            parts = line.split()
            for i, p in enumerate(parts):
                if p == 'Chunk':
                    current_chunk = int(parts[i+1]) - 1  # Convert to 0-indexed
                    best_score = None
                    break

        # Detect score lines: "vN: score=X.XXX"
        if line.startswith('v') and 'score=' in line:
            try:
                score_part = line.split('score=')[1].split()[0].rstrip(')')
                score = float(score_part)
                if '★' in line or best_score is None:
                    if best_score is None or score > best_score:
                        best_score = score
            except (ValueError, IndexError):
                pass

    # Don't forget the last chunk
    if current_chunk is not None and best_score is not None:
        scores[current_chunk] = best_score

    return scores

def run_build(build_num):
    """Run a single build and return (scores_dict, passed_bool)."""
    print(f"\n{'='*60}")
    print(f"  BUILD {build_num}/{MAX_BUILDS}")
    print(f"  {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")

    result = subprocess.run(
        ['python3', 'build-session-v3.py', SESSION, '--no-deploy'],
        capture_output=True, text=True, timeout=600
    )

    output = result.stdout + result.stderr

    # Parse scores from build output
    scores = parse_scores_from_output(result.stdout)

    if not scores:
        print(f"  ERROR: Could not parse scores from build output")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        return {}, False, output

    # Check if all chunks meet threshold
    min_score = min(scores.values()) if scores else 0
    avg_score = sum(scores.values()) / len(scores) if scores else 0
    all_pass = all(s >= MIN_CHUNK_SCORE for s in scores.values())

    # Check QA gate status
    qa_passed = 'QA: PASSED' in result.stdout or 'DEPLOYED' in result.stdout
    qa_status = "QA PASSED" if qa_passed else "QA FAILED"

    print(f"\n  BUILD {build_num} RESULTS:")
    for chunk_idx in sorted(scores.keys()):
        status = "PASS" if scores[chunk_idx] >= MIN_CHUNK_SCORE else "FAIL"
        print(f"    Chunk {chunk_idx}: {scores[chunk_idx]:.3f} [{status}]")
    print(f"    Min: {min_score:.3f} | Avg: {avg_score:.3f} | {qa_status}")
    print(f"    ALL CHUNKS >= {MIN_CHUNK_SCORE}: {'YES' if all_pass else 'NO'}")

    return scores, all_pass, output

def archive_build(build_num, scores):
    """Save current build files to archive."""
    prefix = f"build-{build_num:02d}"

    mp3_src = OUTPUT_DIR / f"{SESSION}.mp3"
    wav_src = RAW_DIR / f"{SESSION}.wav"
    manifest_src = OUTPUT_DIR / f"{SESSION}_manifest.json"

    if mp3_src.exists():
        shutil.copy2(mp3_src, ARCHIVE_DIR / f"{prefix}_{SESSION}.mp3")
    if wav_src.exists():
        shutil.copy2(wav_src, ARCHIVE_DIR / f"{prefix}_{SESSION}.wav")
    if manifest_src.exists():
        shutil.copy2(manifest_src, ARCHIVE_DIR / f"{prefix}_{SESSION}_manifest.json")

    # Save scores
    score_file = ARCHIVE_DIR / f"{prefix}_scores.json"
    with open(score_file, 'w') as f:
        json.dump({
            'build': build_num,
            'scores': {str(k): v for k, v in scores.items()},
            'min': min(scores.values()) if scores else 0,
            'avg': sum(scores.values()) / len(scores) if scores else 0,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)

def main():
    print(f"BATCH REBUILD: {SESSION}")
    print(f"Max builds: {MAX_BUILDS}")
    print(f"Min chunk score: {MIN_CHUNK_SCORE}")
    print(f"Archive: {ARCHIVE_DIR}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_results = []
    best_build = None
    best_min_score = -999

    for build_num in range(1, MAX_BUILDS + 1):
        scores, all_pass, output = run_build(build_num)

        if not scores:
            print(f"  Skipping build {build_num} (no scores)")
            continue

        min_score = min(scores.values())
        avg_score = sum(scores.values()) / len(scores)

        all_results.append({
            'build': build_num,
            'scores': scores,
            'min': min_score,
            'avg': avg_score,
            'all_pass': all_pass
        })

        # Archive every build
        archive_build(build_num, scores)

        # Track best build (by minimum chunk score — we want ALL chunks good)
        if min_score > best_min_score:
            best_min_score = min_score
            best_build = build_num
            # Copy best to a "best" file
            shutil.copy2(OUTPUT_DIR / f"{SESSION}.mp3", ARCHIVE_DIR / f"BEST_{SESSION}.mp3")
            shutil.copy2(RAW_DIR / f"{SESSION}.wav", ARCHIVE_DIR / f"BEST_{SESSION}.wav")
            shutil.copy2(OUTPUT_DIR / f"{SESSION}_manifest.json", ARCHIVE_DIR / f"BEST_{SESSION}_manifest.json")
            print(f"\n  ★ NEW BEST: Build {build_num} (min={min_score:.3f})")

        # Stop if all chunks pass
        if all_pass:
            print(f"\n{'='*60}")
            print(f"  SUCCESS! Build {build_num} — all chunks >= {MIN_CHUNK_SCORE}")
            print(f"{'='*60}")
            break
    else:
        print(f"\n{'='*60}")
        print(f"  EXHAUSTED {MAX_BUILDS} builds without all chunks passing")
        print(f"  Best build: {best_build} (min={best_min_score:.3f})")
        print(f"{'='*60}")

    # Final summary
    print(f"\n{'='*60}")
    print(f"  BATCH SUMMARY")
    print(f"{'='*60}")
    print(f"  Total builds: {len(all_results)}")
    print(f"  Best build: {best_build} (min chunk = {best_min_score:.3f})")

    if all_results:
        print(f"\n  Per-build min scores:")
        for r in all_results:
            marker = " ★ BEST" if r['build'] == best_build else ""
            passing = " ✓ ALL PASS" if r['all_pass'] else ""
            scores_str = " | ".join(f"c{k}={v:.3f}" for k, v in sorted(r['scores'].items()))
            print(f"    Build {r['build']:2d}: min={r['min']:.3f} avg={r['avg']:.3f} | {scores_str}{marker}{passing}")

    # Restore best build as the current output
    if best_build:
        best_mp3 = ARCHIVE_DIR / f"BEST_{SESSION}.mp3"
        best_wav = ARCHIVE_DIR / f"BEST_{SESSION}.wav"
        best_manifest = ARCHIVE_DIR / f"BEST_{SESSION}_manifest.json"

        if best_mp3.exists():
            shutil.copy2(best_mp3, OUTPUT_DIR / f"{SESSION}.mp3")
        if best_wav.exists():
            shutil.copy2(best_wav, RAW_DIR / f"{SESSION}.wav")
        if best_manifest.exists():
            shutil.copy2(best_manifest, OUTPUT_DIR / f"{SESSION}_manifest.json")

        print(f"\n  Best build ({best_build}) restored as current output.")

    # Save comprehensive data for the Bible
    bible_data = {
        'session': SESSION,
        'threshold': MIN_CHUNK_SCORE,
        'max_builds': MAX_BUILDS,
        'total_builds': len(all_results),
        'success': any(r['all_pass'] for r in all_results),
        'best_build': best_build,
        'best_min_score': best_min_score,
        'started': all_results[0]['scores'] if all_results else {},
        'chunk_texts': {
            0: "Hello. I'm Marco. Welcome to Salus.",
            1: "A small team built this place with one aim. To help you slow down, take a breath, and come back to yourself.",
            2: "New material is added each and every week to help you sleep, relax, and restore.",
            3: "Do get in touch if there is something you would like to see or hear. We are here to support you, genuinely.",
            4: "I'm so glad you found us. Take care, and I hope to see you in our sessions."
        },
        'per_chunk_stats': {},
        'all_builds': []
    }

    # Per-chunk score distributions
    for chunk_idx in range(5):
        chunk_scores = [r['scores'].get(chunk_idx, 0) for r in all_results if chunk_idx in r['scores']]
        if chunk_scores:
            bible_data['per_chunk_stats'][str(chunk_idx)] = {
                'text': bible_data['chunk_texts'][chunk_idx],
                'n_builds': len(chunk_scores),
                'min': min(chunk_scores),
                'max': max(chunk_scores),
                'mean': sum(chunk_scores) / len(chunk_scores),
                'median': sorted(chunk_scores)[len(chunk_scores)//2],
                'pct_above_threshold': sum(1 for s in chunk_scores if s >= MIN_CHUNK_SCORE) / len(chunk_scores) * 100,
                'all_scores': chunk_scores
            }

    # All build data
    for r in all_results:
        bible_data['all_builds'].append({
            'build': r['build'],
            'scores': {str(k): v for k, v in r['scores'].items()},
            'min': r['min'],
            'avg': r['avg'],
            'all_pass': r['all_pass']
        })

    bible_path = ARCHIVE_DIR / f"{SESSION}_batch_data.json"
    with open(bible_path, 'w') as f:
        json.dump(bible_data, f, indent=2)
    print(f"\n  Bible data saved: {bible_path}")

    # Print per-chunk analysis
    print(f"\n  PER-CHUNK ANALYSIS (for Bible):")
    for idx in range(5):
        stats = bible_data['per_chunk_stats'].get(str(idx))
        if stats:
            print(f"    Chunk {idx}: mean={stats['mean']:.3f} min={stats['min']:.3f} max={stats['max']:.3f} pass_rate={stats['pct_above_threshold']:.0f}%")
            print(f"      \"{stats['text'][:60]}...\"")

    print(f"\n  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
