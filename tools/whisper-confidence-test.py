#!/usr/bin/env python3
"""
Test if Whisper transcription confidence differs between ECHO and PASS.
Hypothesis: echo degrades speech clarity → lower per-token confidence.

Also tests: compression ratio, no_speech_prob, avg_logprob from Whisper.
"""
import json
import sys
import numpy as np
from pathlib import Path
import whisper

VAULT = Path("content/audio-free/vault")
V5 = Path("reference/v5-test")

SESSION_NAMES = {
    "85": "85-counting-down-to-sleep",
    "63": "63-21day-mindfulness-day07",
}


def load_samples():
    echo, clean = [], []
    for sid, sname in SESSION_NAMES.items():
        vf = V5 / f"{sid}-verdicts-r2.json"
        if not vf.exists():
            continue
        with open(vf) as f:
            data = json.load(f)
        for cid, vd in data["chunks"].items():
            ci, vi = int(cid), vd["version"]
            wav = VAULT / sname / f"c{ci:02d}" / f"c{ci:02d}_v{vi:02d}.wav"
            if not wav.exists():
                continue
            entry = {"session": sid, "chunk": cid, "version": vi,
                     "wav": str(wav), "labels": vd["verdict"],
                     "sname": sname, "passed": vd.get("passed", False)}
            if "ECHO" in vd["verdict"]:
                echo.append(entry)
            elif vd.get("passed", False):
                clean.append(entry)
    return echo, clean


def compute_auc(echo_vals, pass_vals):
    from scipy.stats import mannwhitneyu
    if len(echo_vals) < 2 or len(pass_vals) < 2:
        return 0.5, "?", 1.0
    try:
        U, p = mannwhitneyu(echo_vals, pass_vals, alternative='two-sided')
        auc = U / (len(echo_vals) * len(pass_vals))
        if auc < 0.5:
            return 1 - auc, "lower=echo", p
        return auc, "higher=echo", p
    except:
        return 0.5, "?", 1.0


def main():
    echo_samples, pass_samples = load_samples()
    all_samples = echo_samples + pass_samples
    print(f"Samples: {len(echo_samples)} ECHO, {len(pass_samples)} PASS\n")

    print("Loading Whisper base...")
    model = whisper.load_model("base")

    print("Transcribing with detailed output...")
    for i, s in enumerate(all_samples):
        result = model.transcribe(
            s["wav"],
            language="en",
            word_timestamps=True,
        )

        # Segment-level features
        segs = result.get("segments", [])
        if segs:
            avg_logprobs = [seg["avg_logprob"] for seg in segs]
            no_speech_probs = [seg["no_speech_prob"] for seg in segs]
            compression_ratios = [seg["compression_ratio"] for seg in segs]

            s["w_avg_logprob"] = float(np.mean(avg_logprobs))
            s["w_min_logprob"] = float(np.min(avg_logprobs))
            s["w_no_speech"] = float(np.mean(no_speech_probs))
            s["w_max_no_speech"] = float(np.max(no_speech_probs))
            s["w_compression"] = float(np.mean(compression_ratios))
            s["w_compression_max"] = float(np.max(compression_ratios))

            # Token-level analysis from word timestamps
            all_words = []
            for seg in segs:
                words = seg.get("words", [])
                all_words.extend(words)

            if all_words:
                word_probs = [w.get("probability", 0) for w in all_words if "probability" in w]
                if word_probs:
                    s["w_word_prob_mean"] = float(np.mean(word_probs))
                    s["w_word_prob_min"] = float(np.min(word_probs))
                    s["w_word_prob_std"] = float(np.std(word_probs))
                    s["w_word_prob_p10"] = float(np.percentile(word_probs, 10))
                else:
                    s["w_word_prob_mean"] = 0
                    s["w_word_prob_min"] = 0
                    s["w_word_prob_std"] = 0
                    s["w_word_prob_p10"] = 0
            else:
                s["w_word_prob_mean"] = 0
                s["w_word_prob_min"] = 0
                s["w_word_prob_std"] = 0
                s["w_word_prob_p10"] = 0

            s["w_text"] = result["text"].strip()
            s["w_n_segments"] = len(segs)
        else:
            for k in ["w_avg_logprob", "w_min_logprob", "w_no_speech", "w_max_no_speech",
                       "w_compression", "w_compression_max", "w_word_prob_mean",
                       "w_word_prob_min", "w_word_prob_std", "w_word_prob_p10"]:
                s[k] = 0
            s["w_text"] = ""
            s["w_n_segments"] = 0

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(all_samples)}")

    print(f"  {len(all_samples)}/{len(all_samples)} done\n")

    # Evaluate
    feats = ["w_avg_logprob", "w_min_logprob", "w_no_speech", "w_max_no_speech",
             "w_compression", "w_compression_max", "w_word_prob_mean",
             "w_word_prob_min", "w_word_prob_std", "w_word_prob_p10", "w_n_segments"]

    print(f"{'Feature':>25s}  {'AUC':>6s}  {'Direction':>15s}  {'Echo Mean':>10s}  {'Pass Mean':>10s}  {'p':>8s}")
    print("─" * 85)

    results = []
    for feat in feats:
        echo_vals = [s.get(feat, 0) for s in echo_samples]
        pass_vals = [s.get(feat, 0) for s in pass_samples]
        auc, direction, p = compute_auc(echo_vals, pass_vals)
        results.append({"feat": feat, "auc": auc, "dir": direction, "p": p,
                        "echo_mean": np.mean(echo_vals), "pass_mean": np.mean(pass_vals)})

    results.sort(key=lambda x: x["auc"], reverse=True)
    for r in results:
        m = "***" if r["auc"] >= 0.70 else "   "
        print(f"{m} {r['feat']:>22s}  {r['auc']:.3f}  {r['dir']:>15s}  "
              f"{r['echo_mean']:>10.4f}  {r['pass_mean']:>10.4f}  {r['p']:.4f}")

    # Within-chunk ranking
    print(f"\n{'='*70}")
    print("WITHIN-CHUNK RANKING (Whisper confidence features)")
    print(f"{'='*70}")

    best_feat = results[0]["feat"] if results else None
    best_dir = results[0]["dir"] if results else None

    if best_feat:
        correct = 0
        total = 0
        for s in echo_samples:
            ci = int(s["chunk"])
            sname = s["sname"]
            chunk_dir = VAULT / sname / f"c{ci:02d}"
            if not chunk_dir.exists():
                continue

            picked_version = s["version"]
            alt_wavs = sorted(chunk_dir.glob("c*_v*.wav"))
            alt_wavs = [w for w in alt_wavs if int(w.stem.split("_v")[1]) != picked_version]
            if not alt_wavs:
                continue

            np.random.seed(42 + ci)
            if len(alt_wavs) > 5:
                indices = np.random.choice(len(alt_wavs), 5, replace=False)
                alt_wavs = [alt_wavs[i] for i in indices]

            echo_val = s.get(best_feat)
            if echo_val is None:
                continue

            for alt_wav in alt_wavs:
                result = model.transcribe(str(alt_wav), language="en", word_timestamps=True)
                segs = result.get("segments", [])
                if not segs:
                    continue

                if best_feat == "w_avg_logprob":
                    alt_val = float(np.mean([seg["avg_logprob"] for seg in segs]))
                elif best_feat == "w_compression":
                    alt_val = float(np.mean([seg["compression_ratio"] for seg in segs]))
                elif best_feat == "w_no_speech":
                    alt_val = float(np.mean([seg["no_speech_prob"] for seg in segs]))
                elif best_feat == "w_word_prob_mean":
                    all_words = []
                    for seg in segs:
                        all_words.extend(seg.get("words", []))
                    word_probs = [w.get("probability", 0) for w in all_words if "probability" in w]
                    alt_val = float(np.mean(word_probs)) if word_probs else 0
                elif best_feat == "w_word_prob_min":
                    all_words = []
                    for seg in segs:
                        all_words.extend(seg.get("words", []))
                    word_probs = [w.get("probability", 0) for w in all_words if "probability" in w]
                    alt_val = float(np.min(word_probs)) if word_probs else 0
                else:
                    continue

                total += 1
                if best_dir == "lower=echo":
                    if echo_val < alt_val:
                        correct += 1
                else:
                    if echo_val > alt_val:
                        correct += 1

        if total > 0:
            print(f"\n  {best_feat}: {correct}/{total} correct ({correct/total:.1%})")
        else:
            print("  No comparisons available")

    # Print individual sample details
    print(f"\n{'='*70}")
    print("INDIVIDUAL SAMPLES (best feature + transcription)")
    print(f"{'='*70}")
    for s in sorted(all_samples, key=lambda x: (x["session"], int(x["chunk"]))):
        marker = "ECHO" if "ECHO" in s["labels"] else "pass"
        feat_val = s.get(results[0]["feat"], 0) if results else 0
        print(f"  S{s['session']} c{s['chunk']:>2s} [{marker:>4s}]  {results[0]['feat'] if results else '?'}={feat_val:.4f}  "
              f"logprob={s.get('w_avg_logprob', 0):.3f}  "
              f"no_speech={s.get('w_no_speech', 0):.3f}  "
              f"wp_mean={s.get('w_word_prob_mean', 0):.3f}")


if __name__ == "__main__":
    main()
