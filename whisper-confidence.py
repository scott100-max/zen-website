#!/usr/bin/env python3
"""
Whisper Confidence Analysis — Echo Correlation
================================================
Runs Whisper ASR on all labelled chunks, extracts per-token and per-chunk
confidence metrics, and correlates with human echo verdicts.

Hypothesis: Echo/distortion degrades ASR confidence. If true, low-confidence
chunks correlate with ECHO verdicts.
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import whisper

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "reference" / "echo-training"
AUDIO_DIR = OUTPUT_DIR / "audio"
LABELS_DIR = PROJECT_ROOT / "reference" / "human-labels"

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


def load_labels():
    """Load and deduplicate labels (B2 supersedes B1)."""
    raw = []
    for csv_path in sorted(LABELS_DIR.glob("*-labels.csv")):
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            verdict = str(row['verdict']).strip().upper()
            session = str(row['session']).strip()
            chunk = int(row['chunk'])
            notes = str(row.get('notes', '')) if pd.notna(row.get('notes')) else ''
            text = str(row.get('text', '')) if pd.notna(row.get('text')) else ''

            base_session = session.rsplit('-b', 1)[0] if '-b' in session else session
            build = 2 if session.endswith('-b2') else 1

            raw.append({
                'session': session,
                'base_session': base_session,
                'build': build,
                'chunk': chunk,
                'verdict': verdict,
                'notes': notes,
                'script_text': text,
            })

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
                    'script_text': entry['script_text'],
                    'audio_path': str(audio_path),
                })
    return results


def analyse_chunk(model, audio_path):
    """Run Whisper on a chunk, extract confidence metrics."""
    result = model.transcribe(
        audio_path,
        language='en',
        word_timestamps=True,
        logprob_threshold=None,  # Don't filter low-confidence segments
        no_speech_threshold=0.3,
    )

    metrics = {}

    # Segment-level metrics
    seg_probs = []
    seg_compressions = []
    seg_no_speech = []
    all_token_logprobs = []

    for seg in result.get('segments', []):
        avg_logprob = seg.get('avg_logprob', 0)
        compression = seg.get('compression_ratio', 0)
        no_speech = seg.get('no_speech_prob', 0)

        seg_probs.append(avg_logprob)
        seg_compressions.append(compression)
        seg_no_speech.append(no_speech)

        # Per-token logprobs from the tokens
        if 'tokens' in seg:
            for tok in seg['tokens']:
                if isinstance(tok, dict) and 'logprob' in tok:
                    all_token_logprobs.append(tok['logprob'])

    # Segment-level confidence
    if seg_probs:
        metrics['seg_avg_logprob_mean'] = float(np.mean(seg_probs))
        metrics['seg_avg_logprob_min'] = float(np.min(seg_probs))
        metrics['seg_avg_logprob_std'] = float(np.std(seg_probs))
    else:
        metrics['seg_avg_logprob_mean'] = -1.0
        metrics['seg_avg_logprob_min'] = -1.0
        metrics['seg_avg_logprob_std'] = 0.0

    # Compression ratio (high = repetitive/garbled, echo could cause this)
    if seg_compressions:
        metrics['compression_mean'] = float(np.mean(seg_compressions))
        metrics['compression_max'] = float(np.max(seg_compressions))
    else:
        metrics['compression_mean'] = 0.0
        metrics['compression_max'] = 0.0

    # No-speech probability (echo might raise this)
    if seg_no_speech:
        metrics['no_speech_prob_mean'] = float(np.mean(seg_no_speech))
        metrics['no_speech_prob_max'] = float(np.max(seg_no_speech))
    else:
        metrics['no_speech_prob_mean'] = 0.0
        metrics['no_speech_prob_max'] = 0.0

    # Token-level confidence
    if all_token_logprobs:
        metrics['token_logprob_mean'] = float(np.mean(all_token_logprobs))
        metrics['token_logprob_min'] = float(np.min(all_token_logprobs))
        metrics['token_logprob_std'] = float(np.std(all_token_logprobs))
        metrics['token_logprob_p5'] = float(np.percentile(all_token_logprobs, 5))
        metrics['token_logprob_p10'] = float(np.percentile(all_token_logprobs, 10))
        # Count of very low confidence tokens
        metrics['low_conf_tokens'] = int(sum(1 for lp in all_token_logprobs if lp < -1.0))
        metrics['very_low_conf_tokens'] = int(sum(1 for lp in all_token_logprobs if lp < -2.0))
        metrics['total_tokens'] = len(all_token_logprobs)
        metrics['low_conf_ratio'] = metrics['low_conf_tokens'] / len(all_token_logprobs)
    else:
        metrics['token_logprob_mean'] = -1.0
        metrics['token_logprob_min'] = -1.0
        metrics['token_logprob_std'] = 0.0
        metrics['token_logprob_p5'] = -1.0
        metrics['token_logprob_p10'] = -1.0
        metrics['low_conf_tokens'] = 0
        metrics['very_low_conf_tokens'] = 0
        metrics['total_tokens'] = 0
        metrics['low_conf_ratio'] = 0.0

    # Word-level confidence (from word_timestamps)
    word_probs = []
    for seg in result.get('segments', []):
        for word in seg.get('words', []):
            if 'probability' in word:
                word_probs.append(word['probability'])

    if word_probs:
        metrics['word_prob_mean'] = float(np.mean(word_probs))
        metrics['word_prob_min'] = float(np.min(word_probs))
        metrics['word_prob_std'] = float(np.std(word_probs))
        metrics['word_prob_p5'] = float(np.percentile(word_probs, 5))
        metrics['word_prob_p10'] = float(np.percentile(word_probs, 10))
        metrics['low_word_count'] = int(sum(1 for p in word_probs if p < 0.5))
        metrics['total_words'] = len(word_probs)
        metrics['low_word_ratio'] = metrics['low_word_count'] / len(word_probs)
    else:
        metrics['word_prob_mean'] = 0.0
        metrics['word_prob_min'] = 0.0
        metrics['word_prob_std'] = 0.0
        metrics['word_prob_p5'] = 0.0
        metrics['word_prob_p10'] = 0.0
        metrics['low_word_count'] = 0
        metrics['total_words'] = 0
        metrics['low_word_ratio'] = 0.0

    metrics['transcription'] = result.get('text', '').strip()

    return metrics


def generate_report(results_df):
    """Generate correlation report."""
    report_path = OUTPUT_DIR / "D8-whisper-confidence-report.md"

    has_data = results_df['word_prob_mean'].notna() & (results_df['total_words'] > 0)
    adf = results_df[has_data].copy()

    core = adf[adf['verdict'].isin(['ECHO', 'OK'])]
    echo = core[core['verdict'] == 'ECHO']
    clean = core[core['verdict'] == 'OK']

    confidence_metrics = [
        'word_prob_mean', 'word_prob_min', 'word_prob_std', 'word_prob_p5', 'word_prob_p10',
        'low_word_ratio',
        'seg_avg_logprob_mean', 'seg_avg_logprob_min',
        'compression_mean', 'compression_max',
        'no_speech_prob_mean', 'no_speech_prob_max',
    ]

    lines = []
    lines.append("# Whisper Confidence Analysis: Echo Correlation")
    lines.append("")
    lines.append(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("**Brief:** brief-echo-detection.md (ACTIVE)")
    lines.append("**Hypothesis:** Echo degrades Whisper ASR confidence. Low-confidence chunks = echo.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Dataset")
    lines.append("")
    lines.append(f"- **Chunks analysed:** {len(adf)}")
    lines.append(f"- **ECHO:** {len(echo)}")
    lines.append(f"- **OK:** {len(clean)}")
    lines.append(f"- **Other (HISS/VOICE/BAD):** {len(adf) - len(echo) - len(clean)}")
    lines.append(f"- **Model:** Whisper base (145 MB)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Per-Chunk Results")
    lines.append("")
    lines.append("| Session | Chunk | Verdict | Word Prob Mean | Word Prob Min | Word P5 | Low Words | Compression | No Speech |")
    lines.append("|---------|-------|---------|---------------|--------------|---------|-----------|-------------|-----------|")

    for _, row in adf.iterrows():
        v = row['verdict']
        marker = " **" if v == 'ECHO' else ""
        lines.append(
            f"| {row['session']} | {row['chunk']} | {v}{marker} | "
            f"{row['word_prob_mean']:.3f} | {row['word_prob_min']:.3f} | "
            f"{row['word_prob_p5']:.3f} | "
            f"{row['low_word_count']}/{row['total_words']} | "
            f"{row['compression_mean']:.2f} | {row['no_speech_prob_mean']:.3f} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Statistical Comparison: ECHO vs OK")
    lines.append("")
    lines.append(f"ECHO ({len(echo)}) vs OK ({len(clean)}) chunks.")
    lines.append("")
    lines.append("| Metric | ECHO mean | ECHO std | OK mean | OK std | Cohen d | Direction |")
    lines.append("|--------|-----------|----------|---------|--------|---------|-----------|")

    separation = {}
    for m in confidence_metrics:
        if m not in core.columns:
            continue
        e_vals = echo[m].dropna()
        c_vals = clean[m].dropna()
        if len(e_vals) == 0 or len(c_vals) == 0:
            continue
        e_mean, e_std = e_vals.mean(), e_vals.std()
        c_mean, c_std = c_vals.mean(), c_vals.std()
        pooled = np.sqrt((e_std**2 + c_std**2) / 2) if (e_std + c_std) > 0 else 1
        d = (e_mean - c_mean) / pooled
        separation[m] = d

        if abs(d) < 0.2:
            direction = "negligible"
        elif d > 0:
            direction = "ECHO higher"
        else:
            direction = "ECHO lower"

        lines.append(
            f"| {m} | {e_mean:.4f} | {e_std:.4f} | "
            f"{c_mean:.4f} | {c_std:.4f} | {d:+.3f} | {direction} |"
        )

    best_metric = max(separation, key=lambda k: abs(separation[k])) if separation else None
    best_d = abs(separation[best_metric]) if best_metric else 0

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Does Whisper Confidence Catch Echo?")
    lines.append("")

    if best_d >= 0.8:
        verdict = "YES -- strong separation"
    elif best_d >= 0.5:
        verdict = "MODERATE -- some separation"
    elif best_d >= 0.2:
        verdict = "WEAK -- marginal"
    else:
        verdict = "NO -- no meaningful separation"

    lines.append(f"### Answer: {verdict}")
    lines.append("")
    lines.append(f"Best metric: **`{best_metric}`** (|d| = {best_d:.2f})")
    lines.append("")

    if best_metric:
        d_val = separation[best_metric]
        if d_val < 0:
            lines.append("ECHO chunks have **lower** Whisper confidence (as hypothesised).")
        elif d_val > 0:
            lines.append("ECHO chunks have **higher** Whisper confidence (opposite of hypothesis).")
        else:
            lines.append("No directional pattern.")
        lines.append("")

        # Threshold analysis
        lines.append("### Threshold Analysis")
        lines.append("")
        lines.append(f"Using `{best_metric}`:")
        lines.append("")

        d_sign = 1 if d_val > 0 else -1
        echo_vals = echo[best_metric].dropna()
        clean_vals = clean[best_metric].dropna()
        all_vals = pd.concat([echo_vals, clean_vals])

        for pct in [10, 20, 30, 40, 50]:
            if d_sign > 0:
                threshold = np.percentile(all_vals, 100 - pct)
                flagged_e = int((echo_vals > threshold).sum())
                flagged_c = int((clean_vals > threshold).sum())
                direction_word = "top"
            else:
                threshold = np.percentile(all_vals, pct)
                flagged_e = int((echo_vals < threshold).sum())
                flagged_c = int((clean_vals < threshold).sum())
                direction_word = "bottom"

            recall = flagged_e / max(len(echo_vals), 1)
            prec = flagged_e / max(flagged_e + flagged_c, 1)
            lines.append(
                f"- Flag {direction_word} {pct}%: catches "
                f"**{flagged_e}/{len(echo_vals)} echo** "
                f"({recall:.0%} recall), {flagged_c} false positives "
                f"(precision {prec:.0%})"
            )

    # ML test
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. Predictive Power (Cross-Validated)")
    lines.append("")

    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import RepeatedStratifiedKFold
    from sklearn.metrics import roc_auc_score

    whisper_features = [m for m in confidence_metrics if m in core.columns]
    X = core[whisper_features].values
    y = (core['verdict'] == 'ECHO').astype(int).values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    if len(np.unique(y)) > 1 and len(y) >= 10:
        rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=42)
        probs = np.zeros(len(y))
        counts = np.zeros(len(y))

        for fold_i, (train_idx, test_idx) in enumerate(rskf.split(X, y)):
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(X[train_idx])
            X_te = scaler.transform(X[test_idx])
            clf = GradientBoostingClassifier(
                n_estimators=100, max_depth=2, min_samples_leaf=2,
                learning_rate=0.05, random_state=42 + fold_i,
            )
            clf.fit(X_tr, y[train_idx])
            probs[test_idx] += clf.predict_proba(X_te)[:, 1]
            counts[test_idx] += 1

        avg_probs = probs / np.maximum(counts, 1)
        try:
            auc = roc_auc_score(y, avg_probs)
        except:
            auc = None

        lines.append(f"**Whisper-only AUC-ROC: {auc:.3f}**" if auc else "AUC: N/A")
        lines.append("")

        if auc:
            lines.append("| Feature Set | AUC-ROC |")
            lines.append("|-------------|---------|")
            lines.append(f"| Whisper confidence only | {auc:.3f} |")
            lines.append("| Local DSP only | 0.568 |")
            lines.append("| Auphonic only | 0.341 |")
            lines.append("| Local + Auphonic | 0.527 |")
            lines.append("| Random chance | 0.500 |")

            # FNR at various thresholds
            lines.append("")
            lines.append("### Threshold Sweep")
            lines.append("")
            total_echo = y.sum()
            total_clean = len(y) - total_echo
            for thresh in [0.10, 0.20, 0.30, 0.40, 0.50]:
                preds = (avg_probs >= thresh).astype(int)
                fn = ((preds == 0) & (y == 1)).sum()
                fp = ((preds == 1) & (y == 0)).sum()
                tp = ((preds == 1) & (y == 1)).sum()
                fnr = fn / max(total_echo, 1)
                fpr = fp / max(total_clean, 1)
                lines.append(f"- Threshold {thresh:.2f}: FNR={fnr:.0%}, FPR={fpr:.0%} (catches {tp}/{total_echo})")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 6. Comparison: All Approaches")
    lines.append("")
    lines.append("| Detector | AUC | Best Signal | Catches Echo? |")
    lines.append("|----------|-----|-------------|---------------|")
    lines.append("| Composite scorer | ~0.50 | — | NO |")
    lines.append("| Local DSP | 0.568 | mfcc_11_std | NO |")
    lines.append("| Auphonic | 0.341 | signal_level | NO (anti-correlated) |")
    if auc:
        works = "YES" if auc >= 0.70 else ("MAYBE" if auc >= 0.60 else "NO")
        lines.append(f"| **Whisper confidence** | **{auc:.3f}** | **{best_metric}** | **{works}** |")
    lines.append("| Human review | 1.000 | ears | YES |")
    lines.append("")
    lines.append("---")
    lines.append("")

    if auc and auc >= 0.65:
        lines.append("## 7. Recommendation")
        lines.append("")
        lines.append(f"Whisper confidence (AUC={auc:.3f}) shows the strongest signal yet.")
        lines.append("Consider combining Whisper features with the best local features for")
        lines.append("a combined detector. More labelled data will determine if this holds.")
    else:
        lines.append("## 7. Conclusion")
        lines.append("")
        lines.append("Whisper confidence does not reliably detect Fish Audio echo either.")
        lines.append("Human review remains the only functioning echo gate.")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**END OF REPORT**")

    with open(report_path, 'w') as f:
        f.write("\n".join(lines))
    print(f"\nReport saved: {report_path}")


def main():
    labels = load_labels()
    print(f"Labelled chunks: {len(labels)}")

    # Check for cached results
    cache_path = OUTPUT_DIR / "whisper_results.json"
    cached = {}
    if cache_path.exists():
        with open(cache_path) as f:
            for item in json.load(f):
                key = f"{item['session']}_chunk{item['chunk']}"
                cached[key] = item
        print(f"Cached: {len(cached)}")

    print("Loading Whisper base model...")
    model = whisper.load_model("base")
    print("Model loaded.")

    results = []
    for i, entry in enumerate(labels):
        session = entry['session']
        chunk = entry['chunk']
        verdict = entry['verdict']
        cache_key = f"{session}_chunk{chunk}"

        if cache_key in cached:
            print(f"  [{i+1}/{len(labels)}] {session} chunk {chunk} ({verdict}) — CACHED")
            results.append(cached[cache_key])
            continue

        print(f"  [{i+1}/{len(labels)}] {session} chunk {chunk} ({verdict}) — analysing...")

        metrics = analyse_chunk(model, entry['audio_path'])

        result = {
            'session': session,
            'chunk': chunk,
            'verdict': verdict,
            'notes': entry['notes'],
            'script_text': entry['script_text'],
        }
        result.update(metrics)
        results.append(result)

        # Save cache incrementally
        with open(cache_path, 'w') as f:
            json.dump(results, f, indent=2)

    # Save CSV
    df = pd.DataFrame(results)
    csv_path = OUTPUT_DIR / "whisper_confidence.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nCSV saved: {csv_path} ({len(df)} rows)")

    generate_report(df)


if __name__ == '__main__':
    main()
