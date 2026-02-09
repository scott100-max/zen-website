#!/usr/bin/env python3
"""
Auphonic Batch Analysis — Deliverable D7
=========================================
Submits all labelled audio chunks to Auphonic API, collects statistics,
and correlates with human echo verdicts.

Usage: python3 auphonic-analysis.py
"""

import os
import sys
import json
import time
import csv
from pathlib import Path

import requests
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent
LABELS_DIR = PROJECT_ROOT / "reference" / "human-labels"
AUDIO_DIR = PROJECT_ROOT / "reference" / "echo-training" / "audio"
OUTPUT_DIR = PROJECT_ROOT / "reference" / "echo-training"

# Audio mapping
AUDIO_MAP = {
    "36-loving-kindness-intro-v3a": {
        "dir": AUDIO_DIR / "36-v3a",
        "pattern": "chunk_{:02d}.mp3",
    },
    "52-the-court-of-your-mind-b1": {
        "dir": AUDIO_DIR / "52",
        "pattern": "chunk-{:02d}.mp3",
    },
    "52-the-court-of-your-mind-b2": {
        "dir": AUDIO_DIR / "52",
        "pattern": "chunk-{:02d}.mp3",
    },
}


def load_env():
    env_path = PROJECT_ROOT / ".env"
    env = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env


def load_labels():
    """Load labels with deduplication (B2 supersedes B1 for same chunks)."""
    raw = []
    for csv_path in sorted(LABELS_DIR.glob("*-labels.csv")):
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            verdict = str(row['verdict']).strip().upper()
            session = str(row['session']).strip()
            chunk = int(row['chunk'])
            notes = str(row.get('notes', '')) if pd.notna(row.get('notes')) else ''

            base_session = session.rsplit('-b', 1)[0] if '-b' in session else session
            build = 2 if session.endswith('-b2') else 1

            raw.append({
                'session': session,
                'base_session': base_session,
                'build': build,
                'chunk': chunk,
                'verdict': verdict,
                'notes': notes,
            })

    # Deduplicate
    best = {}
    for entry in raw:
        key = (entry['base_session'], entry['chunk'])
        if key not in best or entry['build'] > best[key]['build']:
            best[key] = entry

    results = []
    for (base_session, chunk), entry in sorted(best.items()):
        session = entry['session']
        if session in AUDIO_MAP:
            mapping = AUDIO_MAP[session]
            audio_path = mapping["dir"] / mapping["pattern"].format(chunk)
            if audio_path.exists():
                results.append({
                    'session': entry['base_session'],
                    'chunk': chunk,
                    'verdict': entry['verdict'],
                    'notes': entry['notes'],
                    'audio_path': str(audio_path),
                })
    return results


def submit_to_auphonic(audio_path, api_key, title="echo-analysis"):
    """Submit a chunk to Auphonic and return statistics."""
    headers = {'Authorization': f'Bearer {api_key}'}

    # Create production with NO processing (analysis only)
    resp = requests.post(
        'https://auphonic.com/api/simple/productions.json',
        headers=headers,
        data={
            'title': title,
            'action': 'start',
            'algorithms[denoise]': '0',
            'algorithms[dehum]': '0',
            'algorithms[leveler]': '0',
            'algorithms[filtering]': '0',
            'algorithms[normloudness]': '0',
        },
        files={'input_file': open(audio_path, 'rb')},
        timeout=60,
    )

    if resp.status_code != 200:
        print(f"    Create failed: {resp.status_code} — {resp.text[:200]}")
        return None

    uuid = resp.json().get('data', {}).get('uuid')
    if not uuid:
        return None

    # Poll for completion
    for i in range(24):
        time.sleep(3)
        resp = requests.get(
            f'https://auphonic.com/api/production/{uuid}.json',
            headers=headers, timeout=15,
        )
        if resp.status_code != 200:
            continue

        prod = resp.json().get('data', {})
        status = prod.get('status')

        if status == 3:  # Done
            stats = prod.get('statistics', {})
            levels = stats.get('levels', {}).get('input', {})
            fmt = stats.get('format', {})

            # Delete the production to keep account clean
            requests.delete(
                f'https://auphonic.com/api/production/{uuid}.json',
                headers=headers, timeout=15,
            )

            return {
                'noise_level': levels.get('noise_level', [None])[0],
                'signal_level': levels.get('signal_level', [None])[0],
                'snr': levels.get('snr', [None])[0],
                'loudness': levels.get('loudness', [None])[0],
                'max_momentary': levels.get('max_momentary', [None])[0],
                'max_shortterm': levels.get('max_shortterm', [None])[0],
                'lra': levels.get('lra', [None])[0],
                'speech_loudness': levels.get('speech_loudness', [None])[0],
                'speech_lra': levels.get('speech_lra', [None])[0],
                'speech_percentage': levels.get('speech_percentage', [None])[0],
                'length_sec': fmt.get('length_sec'),
                'uuid': uuid,
            }
        elif status in (9, 11, 13):  # Error
            print(f"    Auphonic error: {prod.get('error_message', 'unknown')}")
            return None

    print(f"    Timeout waiting for Auphonic")
    return None


def main():
    env = load_env()
    api_key = env.get('AUPHONIC_API_KEY')
    if not api_key:
        print("ERROR: AUPHONIC_API_KEY not found in .env")
        sys.exit(1)

    # Check credits
    resp = requests.get('https://auphonic.com/api/user.json',
                        headers={'Authorization': f'Bearer {api_key}'}, timeout=15)
    if resp.status_code == 200:
        credits = resp.json().get('data', {}).get('credits', 0)
        print(f"Auphonic credits: {credits:.2f} hours")
    else:
        print(f"Auth check failed: {resp.status_code}")
        sys.exit(1)

    labels = load_labels()
    print(f"Labelled chunks: {len(labels)}")

    # Estimate time needed
    total_secs = sum(15 for _ in labels)  # ~15s average per chunk
    print(f"Estimated audio: ~{total_secs/60:.1f} minutes ({total_secs/3600:.2f} hours)")

    if credits < total_secs / 3600:
        print("WARNING: May not have enough credits")

    # Check for cached results
    cache_path = OUTPUT_DIR / "auphonic_results.json"
    cached = {}
    if cache_path.exists():
        with open(cache_path) as f:
            cached_list = json.load(f)
            for item in cached_list:
                cache_key = f"{item['session']}_chunk{item['chunk']}"
                cached[cache_key] = item
        print(f"Cached results: {len(cached)}")

    # Process each chunk
    results = []
    for i, entry in enumerate(labels):
        session = entry['session']
        chunk = entry['chunk']
        verdict = entry['verdict']
        audio_path = entry['audio_path']
        cache_key = f"{session}_chunk{chunk}"

        if cache_key in cached:
            print(f"  [{i+1}/{len(labels)}] {session} chunk {chunk} ({verdict}) — CACHED")
            results.append(cached[cache_key])
            continue

        print(f"  [{i+1}/{len(labels)}] {session} chunk {chunk} ({verdict}) — submitting...")

        stats = submit_to_auphonic(
            audio_path, api_key,
            title=f"echo-{session}-chunk{chunk:02d}",
        )

        result = {
            'session': session,
            'chunk': chunk,
            'verdict': verdict,
            'notes': entry['notes'],
        }

        if stats:
            result.update(stats)
            print(f"    noise={stats['noise_level']} dB, SNR={stats['snr']} dB, loudness={stats['loudness']} LUFS")
        else:
            print(f"    FAILED — no Auphonic data")

        results.append(result)

        # Save cache after each chunk (resume-safe)
        with open(cache_path, 'w') as f:
            json.dump(results, f, indent=2)

    # Save full results CSV
    csv_path = OUTPUT_DIR / "auphonic_correlation.csv"
    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)
    print(f"\nResults saved to {csv_path}")

    # Generate D7 report
    generate_report(df)

    # Show credits remaining
    resp = requests.get('https://auphonic.com/api/user.json',
                        headers={'Authorization': f'Bearer {api_key}'}, timeout=15)
    if resp.status_code == 200:
        remaining = resp.json().get('data', {}).get('credits', 0)
        print(f"\nCredits remaining: {remaining:.2f} hours (used {credits - remaining:.2f})")


def generate_report(df):
    """Generate Deliverable D7: Auphonic correlation report."""

    # Binary label for echo
    df['is_echo'] = df['verdict'].isin(['ECHO']).astype(int)

    # Only include chunks with Auphonic data
    has_data = df['noise_level'].notna()
    analysis_df = df[has_data].copy()

    if len(analysis_df) == 0:
        print("ERROR: No Auphonic data to analyze")
        return

    echo = analysis_df[analysis_df['is_echo'] == 1]
    clean = analysis_df[analysis_df['is_echo'] == 0]

    # Only include ECHO and OK verdicts for the core analysis
    core = analysis_df[analysis_df['verdict'].isin(['ECHO', 'OK'])]
    core_echo = core[core['is_echo'] == 1]
    core_clean = core[core['is_echo'] == 0]

    metrics = ['noise_level', 'signal_level', 'snr', 'loudness', 'lra',
               'speech_loudness', 'speech_lra', 'speech_percentage', 'max_momentary']

    lines = [
        "# Deliverable D7: Auphonic Correlation Report",
        "",
        f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Brief:** brief-echo-detection.md (ACTIVE)",
        f"**Question:** Does Auphonic's analysis catch what human ears catch?",
        "",
        "---",
        "",
        "## 1. Dataset",
        "",
        f"- **Chunks analysed:** {len(analysis_df)}",
        f"- **With Auphonic data:** {has_data.sum()}",
        f"- **ECHO (human):** {len(echo)}",
        f"- **CLEAN/OK (human):** {len(clean)}",
        f"- **Other verdicts (HISS/VOICE/BAD):** {len(analysis_df) - len(echo) - len(clean)}",
        "",
        "---",
        "",
        "## 2. Per-Chunk Results",
        "",
        "| Session | Chunk | Verdict | Noise (dB) | Signal (dB) | SNR (dB) | Loudness (LUFS) | LRA (LU) | Speech % | Notes |",
        "|---------|-------|---------|------------|-------------|----------|-----------------|----------|----------|-------|",
    ]

    for _, row in analysis_df.iterrows():
        noise = f"{row['noise_level']:.1f}" if pd.notna(row.get('noise_level')) else "—"
        sig = f"{row['signal_level']:.1f}" if pd.notna(row.get('signal_level')) else "—"
        snr = f"{row['snr']:.1f}" if pd.notna(row.get('snr')) else "—"
        loud = f"{row['loudness']:.1f}" if pd.notna(row.get('loudness')) else "—"
        lra = f"{row['lra']:.2f}" if pd.notna(row.get('lra')) else "—"
        sp = f"{row['speech_percentage']:.0f}" if pd.notna(row.get('speech_percentage')) else "—"
        notes = str(row.get('notes', ''))[:40]
        verdict = row['verdict']
        marker = " **ECHO**" if verdict == 'ECHO' else ""

        lines.append(
            f"| {row['session']} | {row['chunk']} | {verdict}{marker} | "
            f"{noise} | {sig} | {snr} | {loud} | {lra} | {sp} | {notes} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Statistical Comparison: ECHO vs CLEAN",
        "",
        "Core analysis uses only ECHO and OK chunks (excludes HISS/VOICE/BAD).",
        "",
        "| Metric | ECHO mean | ECHO std | CLEAN mean | CLEAN std | Cohen's d | Direction |",
        "|--------|-----------|----------|------------|-----------|-----------|-----------|",
    ])

    separation_results = {}
    for metric in metrics:
        if metric not in core.columns:
            continue
        e_vals = core_echo[metric].dropna()
        c_vals = core_clean[metric].dropna()

        if len(e_vals) == 0 or len(c_vals) == 0:
            continue

        e_mean = e_vals.mean()
        c_mean = c_vals.mean()
        e_std = e_vals.std()
        c_std = c_vals.std()
        pooled = np.sqrt((e_std**2 + c_std**2) / 2) if (e_std + c_std) > 0 else 1
        d = (e_mean - c_mean) / pooled

        if abs(d) < 0.2:
            direction = "negligible"
        elif d > 0:
            direction = "ECHO higher"
        else:
            direction = "ECHO lower"

        separation_results[metric] = d

        lines.append(
            f"| {metric} | {e_mean:.2f} | {e_std:.2f} | "
            f"{c_mean:.2f} | {c_std:.2f} | {d:+.3f} | {direction} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Can Auphonic Catch Echo?",
        "",
    ])

    # Determine the answer
    best_metric = max(separation_results, key=lambda k: abs(separation_results[k])) if separation_results else None
    best_d = abs(separation_results[best_metric]) if best_metric else 0

    if best_d >= 0.8:
        conclusion = "YES — strong separation"
        detail = f"`{best_metric}` shows strong effect size (|d|={best_d:.2f}). Auphonic metrics can discriminate echo from clean."
    elif best_d >= 0.5:
        conclusion = "MAYBE — moderate separation"
        detail = f"`{best_metric}` shows moderate effect size (|d|={best_d:.2f}). May be useful as one signal among several."
    elif best_d >= 0.2:
        conclusion = "WEAK — small separation"
        detail = f"`{best_metric}` shows only small effect size (|d|={best_d:.2f}). Not reliable as a standalone detector."
    else:
        conclusion = "NO — no meaningful separation"
        detail = "No Auphonic metric shows meaningful separation between echo and clean chunks."

    lines.extend([
        f"### Answer: {conclusion}",
        "",
        detail,
        "",
    ])

    # Would Auphonic have caught the false negatives?
    if best_metric and len(core_echo) > 0 and len(core_clean) > 0:
        # Use the best metric to see if a threshold would catch echo
        all_vals = core[best_metric].dropna()
        echo_vals = core_echo[best_metric].dropna()
        clean_vals = core_clean[best_metric].dropna()

        lines.extend([
            f"### Threshold Analysis on `{best_metric}`",
            "",
        ])

        # Try percentile-based thresholds
        d_sign = 1 if separation_results[best_metric] > 0 else -1
        for percentile in [10, 20, 30, 40, 50]:
            if d_sign > 0:
                # ECHO is higher — flag above threshold
                threshold = np.percentile(all_vals, 100 - percentile)
                flagged_echo = (echo_vals > threshold).sum()
                flagged_clean = (clean_vals > threshold).sum()
            else:
                # ECHO is lower — flag below threshold
                threshold = np.percentile(all_vals, percentile)
                flagged_echo = (echo_vals < threshold).sum()
                flagged_clean = (clean_vals < threshold).sum()

            recall = flagged_echo / max(len(echo_vals), 1)
            precision = flagged_echo / max(flagged_echo + flagged_clean, 1)
            lines.append(
                f"- Flag top {percentile}%: catches {flagged_echo}/{len(echo_vals)} echo "
                f"({recall:.0%} recall), {flagged_clean} false positives "
                f"(precision={precision:.0%})"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Composite Scorer Comparison",
        "",
        "The original composite scorer had a **58% false negative rate** on echo.",
        "",
    ])

    if best_metric and len(core_echo) > 0:
        # At the threshold that catches at least 50% of echo
        echo_vals = core_echo[best_metric].dropna()
        clean_vals = core_clean[best_metric].dropna()
        d_sign = 1 if separation_results[best_metric] > 0 else -1

        best_fnr = 1.0
        best_fpr = 1.0
        for p in np.arange(5, 95, 1):
            if d_sign > 0:
                t = np.percentile(pd.concat([echo_vals, clean_vals]), 100 - p)
                caught = (echo_vals > t).sum()
                fp = (clean_vals > t).sum()
            else:
                t = np.percentile(pd.concat([echo_vals, clean_vals]), p)
                caught = (echo_vals < t).sum()
                fp = (clean_vals < t).sum()

            fnr = 1 - caught / max(len(echo_vals), 1)
            fpr = fp / max(len(clean_vals), 1)

            if fnr < best_fnr or (fnr == best_fnr and fpr < best_fpr):
                best_fnr = fnr
                best_fpr = fpr

        lines.extend([
            f"| Detector | False Negative Rate | Notes |",
            f"|----------|---------------------|-------|",
            f"| Composite scorer | 58% | Proven anti-correlated with echo |",
            f"| Local DSP features (echo-detector.py) | 67% | Classical echo features fail on TTS artifacts |",
            f"| Auphonic `{best_metric}` (best metric) | {best_fnr:.0%} | Effect size |d|={best_d:.2f} |",
            f"| Human review | 0% | Ground truth |",
        ])
    else:
        lines.append("Insufficient Auphonic data for comparison.")

    lines.extend([
        "",
        "---",
        "",
        "## 6. Recommendations",
        "",
        "Based on this analysis:",
        "",
    ])

    if best_d >= 0.5:
        lines.extend([
            f"1. **Include `{best_metric}` as a feature** in the echo detector — it provides signal the local DSP features lack",
            "2. **Retrain the echo detector** with Auphonic features added",
            "3. **Continue human review** — Auphonic alone is not sufficient for reliable echo detection",
        ])
    else:
        lines.extend([
            "1. **Auphonic does not reliably detect Fish Audio echo** — its noise/signal analysis doesn't capture TTS generation artifacts",
            "2. **Human review remains the only functioning echo gate**",
            "3. **Next approaches to try:**",
            "   - Mel spectrogram CNN (needs 200+ labelled chunks)",
            "   - Word-level forced alignment + per-word spectral analysis",
            "   - Self-supervised anomaly detection trained only on CLEAN chunks",
        ])

    lines.extend([
        "",
        "---",
        "",
        "**END OF REPORT**",
    ])

    report_path = OUTPUT_DIR / "D7-auphonic-correlation-report.md"
    with open(report_path, 'w') as f:
        f.write("\n".join(lines))
    print(f"\nD7 report saved to {report_path}")


if __name__ == '__main__':
    main()
