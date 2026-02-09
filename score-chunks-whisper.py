#!/usr/bin/env python3
"""
Whisper Confidence Scorer for Chunk Review
============================================
Runs Whisper on a directory of chunk MP3s, computes per-word confidence,
and outputs a JSON file that the review page consumes for visual flagging.

Usage:
  python3 score-chunks-whisper.py <chunk-dir> [--output review-whisper.json]

Example:
  python3 score-chunks-whisper.py reference/echo-training/audio/52/

Output JSON format (consumed by review page):
  {
    "threshold_p10": 0.785,
    "percentile": 30,
    "chunks": {
      "1":  {"word_prob_mean": 0.955, "word_prob_min": 0.697, "word_prob_p10": 0.786, "flagged_whisper": false},
      "4":  {"word_prob_mean": 0.939, "word_prob_min": 0.485, "word_prob_p10": 0.595, "flagged_whisper": true},
      ...
    }
  }
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import whisper

warnings.filterwarnings('ignore')


def score_chunk(model, audio_path):
    """Run Whisper, return per-word confidence metrics."""
    result = model.transcribe(
        str(audio_path),
        language='en',
        word_timestamps=True,
        logprob_threshold=None,
        no_speech_threshold=0.3,
    )

    word_probs = []
    for seg in result.get('segments', []):
        for word in seg.get('words', []):
            if 'probability' in word:
                word_probs.append(word['probability'])

    if not word_probs:
        return None

    return {
        'word_prob_mean': round(float(np.mean(word_probs)), 4),
        'word_prob_min': round(float(np.min(word_probs)), 4),
        'word_prob_p5': round(float(np.percentile(word_probs, 5)), 4),
        'word_prob_p10': round(float(np.percentile(word_probs, 10)), 4),
        'word_prob_std': round(float(np.std(word_probs)), 4),
        'total_words': len(word_probs),
        'low_word_count': sum(1 for p in word_probs if p < 0.5),
    }


def main():
    parser = argparse.ArgumentParser(description='Whisper confidence scorer for chunk review')
    parser.add_argument('chunk_dir', help='Directory containing chunk MP3 files')
    parser.add_argument('--output', '-o', default=None, help='Output JSON path (default: <chunk_dir>/whisper-scores.json)')
    parser.add_argument('--percentile', type=int, default=30, help='Bottom N%% to flag (default: 30)')
    parser.add_argument('--model', default='base', help='Whisper model size (default: base)')
    args = parser.parse_args()

    chunk_dir = Path(args.chunk_dir)
    if not chunk_dir.is_dir():
        print(f"ERROR: {chunk_dir} is not a directory")
        sys.exit(1)

    output_path = Path(args.output) if args.output else chunk_dir / 'whisper-scores.json'

    # Find chunk files (chunk-01.mp3, chunk_01.mp3, etc.)
    mp3s = sorted(chunk_dir.glob('chunk*.mp3'))
    if not mp3s:
        print(f"ERROR: No chunk*.mp3 files found in {chunk_dir}")
        sys.exit(1)

    print(f"Loading Whisper {args.model} model...")
    model = whisper.load_model(args.model)

    print(f"Scoring {len(mp3s)} chunks...")
    scores = {}

    for i, mp3 in enumerate(mp3s):
        # Extract chunk number from filename
        name = mp3.stem
        # Handle both "chunk-01" and "chunk_01" patterns
        num_str = name.replace('chunk-', '').replace('chunk_', '').lstrip('0') or '0'
        try:
            chunk_num = int(num_str)
        except ValueError:
            print(f"  SKIP: can't parse chunk number from {name}")
            continue

        print(f"  [{i+1}/{len(mp3s)}] chunk {chunk_num}...", end='', flush=True)
        result = score_chunk(model, mp3)

        if result:
            scores[str(chunk_num)] = result
            print(f" p10={result['word_prob_p10']:.3f} mean={result['word_prob_mean']:.3f}")
        else:
            print(" SKIP (no words detected)")

    if not scores:
        print("ERROR: No chunks scored")
        sys.exit(1)

    # Compute threshold: bottom N% of word_prob_p10
    p10_values = [s['word_prob_p10'] for s in scores.values()]
    threshold = float(np.percentile(p10_values, args.percentile))

    print(f"\nThreshold (bottom {args.percentile}%): word_prob_p10 < {threshold:.4f}")

    # Flag chunks below threshold
    flagged_count = 0
    for chunk_num, data in scores.items():
        data['flagged_whisper'] = data['word_prob_p10'] < threshold
        if data['flagged_whisper']:
            flagged_count += 1

    output = {
        'threshold_p10': round(threshold, 4),
        'percentile': args.percentile,
        'total_chunks': len(scores),
        'flagged_count': flagged_count,
        'chunks': scores,
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults: {flagged_count}/{len(scores)} flagged (bottom {args.percentile}%)")
    print(f"Output: {output_path}")

    # Print flagged chunks
    if flagged_count > 0:
        print(f"\nFlagged chunks:")
        for num in sorted(scores.keys(), key=int):
            if scores[num]['flagged_whisper']:
                print(f"  chunk {num}: p10={scores[num]['word_prob_p10']:.3f} mean={scores[num]['word_prob_mean']:.3f}")


if __name__ == '__main__':
    main()
