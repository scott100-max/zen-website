#!/usr/bin/env python3
"""
Validate echo features: ECHO vs PASS-only (excluding other defects).
Also check if features can do relative ranking within chunks.
"""
import json
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scipy.stats import mannwhitneyu

# Import feature extraction from the main detector
from importlib.machinery import SourceFileLoader
detector = SourceFileLoader("detector", "echo-detector-v2.py").load_module()

VAULT = Path("content/audio-free/vault")
V5 = Path("reference/v5-test")

SESSION_NAMES = {
    "85": "85-counting-down-to-sleep",
    "63": "63-21day-mindfulness-day07",
}


def load_echo_vs_pass():
    """Load only ECHO and PASS (EXCELLENT/OK) samples."""
    echo_samples = []
    pass_samples = []

    for sid, sname in SESSION_NAMES.items():
        verdict_file = V5 / f"{sid}-verdicts-r2.json"
        if not verdict_file.exists():
            continue
        with open(verdict_file) as f:
            data = json.load(f)

        for cid, vd in data["chunks"].items():
            ci, vi = int(cid), vd["version"]
            wav = VAULT / sname / f"c{ci:02d}" / f"c{ci:02d}_v{vi:02d}.wav"
            if not wav.exists():
                continue

            labels = vd["verdict"]
            entry = {"session": sid, "chunk": cid, "wav": str(wav), "labels": labels}

            if "ECHO" in labels:
                echo_samples.append(entry)
            elif vd.get("passed", False):
                pass_samples.append(entry)
            # Skip other defects entirely

    return echo_samples, pass_samples


def main():
    echo_samples, pass_samples = load_echo_vs_pass()
    print(f"ECHO: {len(echo_samples)} samples")
    print(f"PASS: {len(pass_samples)} samples")
    all_samples = echo_samples + pass_samples

    print("\nExtracting features...")
    for i, s in enumerate(all_samples):
        s["features"] = detector.extract_all_features(s["wav"])
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(all_samples)}")

    all_samples = [s for s in all_samples if s["features"] is not None]
    echo_samples = [s for s in all_samples if "ECHO" in s["labels"]]
    pass_samples = [s for s in all_samples if "ECHO" not in s["labels"]]
    print(f"\nValid: {len(echo_samples)} ECHO, {len(pass_samples)} PASS")

    feat_names = sorted(all_samples[0]["features"].keys())

    print(f"\n{'='*80}")
    print("ECHO vs PASS (clean only, no other defects)")
    print(f"{'='*80}")

    results = []
    for feat in feat_names:
        ev = [s["features"][feat] for s in echo_samples]
        pv = [s["features"][feat] for s in pass_samples]

        try:
            U, p = mannwhitneyu(ev, pv, alternative='two-sided')
            auc = U / (len(ev) * len(pv))
            if auc < 0.5:
                auc = 1 - auc
                direction = "lower=echo"
            else:
                direction = "higher=echo"
        except:
            auc, p, direction = 0.5, 1.0, "?"

        d = abs(np.mean(ev) - np.mean(pv)) / (
            np.sqrt((np.std(ev)**2 + np.std(pv)**2) / 2) + 1e-10)

        # Find high-recall threshold
        vl = [(s["features"][feat], "ECHO" in s["labels"]) for s in all_samples]

        # Best J
        best_j, best_t, best_r, best_s = 0, 0, 0, 0
        vals = sorted(set(v for v, _ in vl))
        for t in np.linspace(min(vals), max(vals), 300):
            if direction == "higher=echo":
                tp = sum(1 for v, e in vl if v >= t and e)
                fn = sum(1 for v, e in vl if v < t and e)
                fp = sum(1 for v, e in vl if v >= t and not e)
                tn = sum(1 for v, e in vl if v < t and not e)
            else:
                tp = sum(1 for v, e in vl if v <= t and e)
                fn = sum(1 for v, e in vl if v > t and e)
                fp = sum(1 for v, e in vl if v <= t and not e)
                tn = sum(1 for v, e in vl if v > t and not e)
            r = tp / (tp + fn) if (tp+fn) > 0 else 0
            s = tn / (tn + fp) if (tn+fp) > 0 else 0
            j = r + s - 1
            if j > best_j:
                best_j, best_t, best_r, best_s = j, t, r, s

        results.append({
            "feat": feat, "auc": auc, "d": d, "p": p,
            "dir": direction, "j": best_j, "r": best_r, "s": best_s,
            "echo_mean": np.mean(ev), "pass_mean": np.mean(pv),
        })

    results.sort(key=lambda x: x["auc"], reverse=True)

    for r in results:
        m = "***" if r["auc"] >= 0.70 else "   "
        print(f"{m} {r['feat']:25s}  AUC={r['auc']:.3f}  d={r['d']:.2f}  "
              f"J={r['j']:.3f}  R={r['r']:.0%}  S={r['s']:.0%}  "
              f"({r['dir']})  p={r['p']:.3f}")

    # Feature combos
    print(f"\n{'='*80}")
    print("TOP COMBOS (ECHO vs PASS only):")
    print(f"{'='*80}")

    from itertools import combinations
    top = [r for r in results if r["auc"] >= 0.60][:10]
    combo_results = []

    for n in [2, 3]:
        for combo in combinations(top, n):
            names = [c["feat"] for c in combo]
            scores = []
            for s in all_samples:
                score = 0
                for c in combo:
                    vals = [s2["features"][c["feat"]] for s2 in all_samples]
                    v = s["features"][c["feat"]]
                    mn, mx = min(vals), max(vals)
                    nv = (v - mn) / (mx - mn + 1e-10)
                    if c["dir"] == "lower=echo":
                        nv = 1 - nv
                    score += nv
                scores.append((score, "ECHO" in s["labels"]))

            e_sc = [sc for sc, is_e in scores if is_e]
            c_sc = [sc for sc, is_e in scores if not is_e]
            try:
                U, _ = mannwhitneyu(e_sc, c_sc)
                auc = U / (len(e_sc) * len(c_sc))
                if auc < 0.5: auc = 1 - auc
            except:
                auc = 0.5

            # Find threshold for 90%+ recall
            best_j = 0
            for t in np.linspace(min(sc for sc,_ in scores), max(sc for sc,_ in scores), 300):
                tp = sum(1 for sc, e in scores if sc >= t and e)
                fn = sum(1 for sc, e in scores if sc < t and e)
                fp = sum(1 for sc, e in scores if sc >= t and not e)
                tn = sum(1 for sc, e in scores if sc < t and not e)
                r = tp / (tp+fn) if (tp+fn) > 0 else 0
                sp = tn / (tn+fp) if (tn+fp) > 0 else 0
                j = r + sp - 1
                if j > best_j:
                    best_j, best_r, best_sp = j, r, sp

            combo_results.append({
                "feats": "+".join(names), "auc": auc,
                "j": best_j, "r": best_r, "s": best_sp,
            })

    combo_results.sort(key=lambda x: x["auc"], reverse=True)
    for r in combo_results[:15]:
        m = "***" if r["auc"] >= 0.80 else "   "
        print(f"{m} {r['feats']}")
        print(f"    AUC={r['auc']:.3f}  J={r['j']:.3f}  R={r['r']:.0%}  S={r['s']:.0%}")

    # === CANDIDATE COMPARISON ANALYSIS ===
    print(f"\n{'='*80}")
    print("CANDIDATE COMPARISON: within-chunk ranking")
    print(f"{'='*80}")

    # For each echo chunk, compare the picked (echo) version against
    # 5 random alternative versions and check if the feature correctly
    # ranks the echo version worse
    correct_rankings = {f: 0 for f in feat_names}
    total_comparisons = 0

    for s in echo_samples:
        ci = int(s["chunk"])
        sname = SESSION_NAMES[s["session"]]
        chunk_dir = VAULT / sname / f"c{ci:02d}"
        if not chunk_dir.exists():
            continue

        # Get alternative WAVs
        picked_version = int(Path(s["wav"]).stem.split("_v")[1])
        alt_wavs = sorted(chunk_dir.glob("c*_v*.wav"))
        alt_wavs = [w for w in alt_wavs if int(w.stem.split("_v")[1]) != picked_version]

        if len(alt_wavs) == 0:
            continue

        # Sample up to 5 alternatives
        np.random.seed(42 + ci)
        if len(alt_wavs) > 5:
            indices = np.random.choice(len(alt_wavs), 5, replace=False)
            alt_wavs = [alt_wavs[i] for i in indices]

        echo_feats = s["features"]
        for alt_wav in alt_wavs:
            alt_feats = detector.extract_all_features(str(alt_wav))
            if alt_feats is None:
                continue
            total_comparisons += 1
            for feat in feat_names:
                # For "higher=echo" features: echo should be higher
                # We check if the echo version has a "more echo-like" value
                r = [x for x in results if x["feat"] == feat][0]
                if r["dir"] == "higher=echo":
                    if echo_feats[feat] > alt_feats[feat]:
                        correct_rankings[feat] += 1
                else:
                    if echo_feats[feat] < alt_feats[feat]:
                        correct_rankings[feat] += 1

    if total_comparisons > 0:
        print(f"\n{total_comparisons} pairwise comparisons (echo-picked vs random alternative)")
        print(f"Correct ranking = echo version scores worse than alternative\n")

        ranking_results = [(f, correct_rankings[f] / total_comparisons)
                          for f in feat_names]
        ranking_results.sort(key=lambda x: x[1], reverse=True)

        for feat, acc in ranking_results:
            m = "***" if acc >= 0.60 else "   "
            print(f"{m} {feat:25s}  {acc:.1%} correct ({correct_rankings[feat]}/{total_comparisons})")
    else:
        print("No candidate comparisons available")


if __name__ == "__main__":
    main()
