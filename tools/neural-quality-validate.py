#!/usr/bin/env python3
"""
Validate neural perceptual quality models against human echo verdicts.
Tests whether DNSMOS / UTMOS can distinguish ECHO from PASS.

Usage:
    python3 tools/neural-quality-validate.py
"""
import json
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

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
            entry = {"session": sid, "chunk": cid, "version": vi, "wav": str(wav), "labels": labels}

            if "ECHO" in labels:
                echo_samples.append(entry)
            elif vd.get("passed", False):
                pass_samples.append(entry)

    return echo_samples, pass_samples


def load_all_labelled():
    """Load ALL labelled samples (ECHO, PASS, and other defects)."""
    samples = []
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
            samples.append({
                "session": sid, "chunk": cid, "version": vi,
                "wav": str(wav), "labels": vd["verdict"],
                "passed": vd.get("passed", False),
            })
    return samples


def score_dnsmos(samples):
    """Score all samples with DNSMOS."""
    from speechmos import dnsmos
    import librosa
    import soundfile as sf

    for i, s in enumerate(samples):
        audio, sr = sf.read(s["wav"])
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        result = dnsmos.run(audio, sr=16000)
        s["dnsmos_ovrl"] = float(result["ovrl_mos"])
        s["dnsmos_sig"] = float(result["sig_mos"])
        s["dnsmos_bak"] = float(result["bak_mos"])
        s["dnsmos_p808"] = float(result["p808_mos"])
        if (i + 1) % 10 == 0:
            print(f"  DNSMOS: {i+1}/{len(samples)}")
    print(f"  DNSMOS: {len(samples)}/{len(samples)} done")


def score_utmos(samples):
    """Score all samples with UTMOS via torch.hub."""
    import torch
    import librosa

    try:
        model = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
        model.eval()
    except Exception as e:
        print(f"  UTMOS load failed: {e}")
        return False

    for i, s in enumerate(samples):
        audio, sr = librosa.load(s["wav"], sr=16000, mono=True)
        wav_tensor = torch.from_numpy(audio).unsqueeze(0)
        with torch.no_grad():
            score = model(wav_tensor, sr)
        s["utmos"] = float(score.item())
        if (i + 1) % 10 == 0:
            print(f"  UTMOS: {i+1}/{len(samples)}")
    print(f"  UTMOS: {len(samples)}/{len(samples)} done")
    return True


def compute_auc(echo_vals, pass_vals):
    """Compute AUC using Mann-Whitney U."""
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


def find_best_threshold(values_labels, direction):
    """Find threshold with best Youden's J."""
    best_j, best_t, best_r, best_s = 0, 0, 0, 0
    vals = sorted(set(v for v, _ in values_labels))
    for t in np.linspace(min(vals), max(vals), 500):
        if direction == "higher=echo":
            tp = sum(1 for v, e in values_labels if v >= t and e)
            fn = sum(1 for v, e in values_labels if v < t and e)
            fp = sum(1 for v, e in values_labels if v >= t and not e)
            tn = sum(1 for v, e in values_labels if v < t and not e)
        else:
            tp = sum(1 for v, e in values_labels if v <= t and e)
            fn = sum(1 for v, e in values_labels if v > t and e)
            fp = sum(1 for v, e in values_labels if v <= t and not e)
            tn = sum(1 for v, e in values_labels if v > t and not e)
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        s = tn / (tn + fp) if (tn + fp) > 0 else 0
        j = r + s - 1
        if j > best_j:
            best_j, best_t, best_r, best_s = j, t, r, s
    return best_j, best_t, best_r, best_s


def evaluate_feature(feat_name, echo_samples, pass_samples):
    """Full evaluation of a single feature."""
    echo_vals = [s[feat_name] for s in echo_samples if feat_name in s]
    pass_vals = [s[feat_name] for s in pass_samples if feat_name in s]

    if not echo_vals or not pass_vals:
        return None

    auc, direction, p = compute_auc(echo_vals, pass_vals)
    d = abs(np.mean(echo_vals) - np.mean(pass_vals)) / (
        np.sqrt((np.std(echo_vals)**2 + np.std(pass_vals)**2) / 2) + 1e-10)

    vl = [(v, True) for v in echo_vals] + [(v, False) for v in pass_vals]
    j, t, r, s = find_best_threshold(vl, direction)

    return {
        "feat": feat_name, "auc": auc, "d": d, "p": p,
        "dir": direction, "j": j, "threshold": t,
        "recall": r, "specificity": s,
        "echo_mean": np.mean(echo_vals), "echo_std": np.std(echo_vals),
        "pass_mean": np.mean(pass_vals), "pass_std": np.std(pass_vals),
    }


def within_chunk_ranking(feat_name, echo_samples, direction):
    """Test within-chunk ranking: for each echo sample, compare against
    alternative candidates from the same chunk pool."""
    from importlib.machinery import SourceFileLoader
    from speechmos import dnsmos
    import librosa
    import soundfile as sf

    correct = 0
    total = 0

    for s in echo_samples:
        ci = int(s["chunk"])
        sname = SESSION_NAMES[s["session"]]
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

        echo_val = s.get(feat_name)
        if echo_val is None:
            continue

        for alt_wav in alt_wavs:
            # Score the alternative
            audio, sr = sf.read(str(alt_wav))
            if sr != 16000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            result = dnsmos.run(audio, sr=16000)

            if feat_name == "dnsmos_ovrl":
                alt_val = float(result["ovrl_mos"])
            elif feat_name == "dnsmos_sig":
                alt_val = float(result["sig_mos"])
            elif feat_name == "dnsmos_bak":
                alt_val = float(result["bak_mos"])
            elif feat_name == "dnsmos_p808":
                alt_val = float(result["p808_mos"])
            else:
                continue

            total += 1
            # For "lower=echo": echo should have lower score
            if direction == "lower=echo":
                if echo_val < alt_val:
                    correct += 1
            else:
                if echo_val > alt_val:
                    correct += 1

    return correct, total


def main():
    print("=" * 70)
    print("NEURAL PERCEPTUAL QUALITY — ECHO vs PASS VALIDATION")
    print("=" * 70)

    echo_samples, pass_samples = load_echo_vs_pass()
    print(f"\nSamples: {len(echo_samples)} ECHO, {len(pass_samples)} PASS")

    if not echo_samples or not pass_samples:
        print("ERROR: Need both ECHO and PASS samples")
        return

    all_samples = echo_samples + pass_samples

    # Score with DNSMOS
    print("\n--- DNSMOS Scoring ---")
    score_dnsmos(all_samples)

    # Score with UTMOS
    print("\n--- UTMOS Scoring ---")
    has_utmos = score_utmos(all_samples)

    # Evaluate features
    print("\n" + "=" * 70)
    print("RESULTS: ECHO vs PASS (clean only)")
    print("=" * 70)

    feats = ["dnsmos_ovrl", "dnsmos_sig", "dnsmos_bak", "dnsmos_p808"]
    if has_utmos:
        feats.append("utmos")

    results = []
    for feat in feats:
        r = evaluate_feature(feat, echo_samples, pass_samples)
        if r:
            results.append(r)

    results.sort(key=lambda x: x["auc"], reverse=True)

    print(f"\n{'Feature':>15s}  {'AUC':>6s}  {'d':>5s}  {'J':>5s}  {'Recall':>7s}  {'Spec':>6s}  {'Direction':>15s}  {'Echo Mean':>10s}  {'Pass Mean':>10s}")
    print("─" * 100)

    for r in results:
        m = "***" if r["auc"] >= 0.70 else "   "
        print(f"{m} {r['feat']:>12s}  {r['auc']:.3f}  {r['d']:.2f}  {r['j']:.3f}  "
              f"{r['recall']:.0%}      {r['specificity']:.0%}     {r['dir']:>15s}  "
              f"{r['echo_mean']:.4f}     {r['pass_mean']:.4f}")

    # Print individual scores for inspection
    print(f"\n{'='*70}")
    print("INDIVIDUAL SCORES")
    print(f"{'='*70}")

    best_feat = results[0]["feat"] if results else None

    for s in sorted(all_samples, key=lambda x: (x["session"], int(x["chunk"]))):
        is_echo = "ECHO" in s["labels"]
        labels = ",".join(s["labels"])
        scores = "  ".join(f"{f}={s.get(f, 0):.3f}" for f in feats)
        marker = "ECHO" if is_echo else "pass"
        print(f"  S{s['session']} c{s['chunk']:>2s} v{s['version']:>2}  [{marker:>4s}]  {scores}  ({labels})")

    # Within-chunk ranking test
    if results and results[0]["auc"] >= 0.55:
        print(f"\n{'='*70}")
        print("WITHIN-CHUNK RANKING TEST")
        print(f"{'='*70}")

        for r in results:
            if r["auc"] >= 0.55:
                print(f"\n  Testing {r['feat']} ({r['dir']})...")
                correct, total = within_chunk_ranking(r["feat"], echo_samples, r["dir"])
                if total > 0:
                    print(f"  {r['feat']}: {correct}/{total} correct ({correct/total:.1%})")
                else:
                    print(f"  {r['feat']}: no comparisons available")

    # Combo test: DNSMOS + echo_v2 physics features
    print(f"\n{'='*70}")
    print("COMBO: Neural + Physics features")
    print(f"{'='*70}")

    # Load echo_v2 physics features if available
    try:
        from importlib.machinery import SourceFileLoader
        det = SourceFileLoader("det", "echo-detector-v2.py").load_module()
        print("\n  Loading echo_v2 physics features...")
        for i, s in enumerate(all_samples):
            feats_phys = det.extract_all_features(s["wav"])
            if feats_phys:
                s["ceps_prom_max"] = feats_phys.get("ceps_prom_max", 0)
                s["edr_slope"] = feats_phys.get("edr_slope", 0)
                s["spectral_flux_std"] = feats_phys.get("spectral_flux_std", 0)
            if (i + 1) % 10 == 0:
                print(f"    {i+1}/{len(all_samples)}")

        # Test combos
        from itertools import combinations
        combo_feats = feats + ["ceps_prom_max", "edr_slope", "spectral_flux_std"]

        best_combos = []
        for n in [2, 3]:
            for combo in combinations(combo_feats, n):
                # Skip pure-physics combos (already tested)
                if all(f in ["ceps_prom_max", "edr_slope", "spectral_flux_std"] for f in combo):
                    continue
                # Need at least one neural and one physics
                has_neural = any(f in feats for f in combo)
                has_physics = any(f in ["ceps_prom_max", "edr_slope", "spectral_flux_std"] for f in combo)

                scores = []
                for s in all_samples:
                    score = 0
                    for f in combo:
                        vals = [s2.get(f, 0) for s2 in all_samples]
                        v = s.get(f, 0)
                        mn, mx = min(vals), max(vals)
                        nv = (v - mn) / (mx - mn + 1e-10)
                        # Check direction
                        ev = [s2.get(f, 0) for s2 in echo_samples]
                        pv = [s2.get(f, 0) for s2 in pass_samples]
                        if np.mean(ev) < np.mean(pv):
                            nv = 1 - nv  # lower = echo, so invert
                        score += nv
                    is_echo = "ECHO" in s["labels"]
                    scores.append((score, is_echo))

                e_sc = [sc for sc, is_e in scores if is_e]
                c_sc = [sc for sc, is_e in scores if not is_e]
                from scipy.stats import mannwhitneyu
                try:
                    U, _ = mannwhitneyu(e_sc, c_sc)
                    auc = U / (len(e_sc) * len(c_sc))
                    if auc < 0.5:
                        auc = 1 - auc
                except:
                    auc = 0.5

                j, _, r, sp = find_best_threshold(scores, "higher=echo")
                best_combos.append({
                    "feats": " + ".join(combo),
                    "auc": auc, "j": j, "r": r, "s": sp,
                    "has_neural": has_neural, "has_physics": has_physics,
                })

        best_combos.sort(key=lambda x: x["auc"], reverse=True)
        for r in best_combos[:15]:
            tag = "N+P" if r["has_neural"] and r["has_physics"] else "N" if r["has_neural"] else "P"
            m = "***" if r["auc"] >= 0.80 else "   "
            print(f"  {m} [{tag}] {r['feats']}")
            print(f"      AUC={r['auc']:.3f}  J={r['j']:.3f}  R={r['r']:.0%}  S={r['s']:.0%}")

    except Exception as e:
        print(f"  Physics features unavailable: {e}")

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    if results:
        best = results[0]
        if best["auc"] >= 0.80:
            print(f"  PROMISING: {best['feat']} AUC={best['auc']:.3f} — worth integrating")
        elif best["auc"] >= 0.65:
            print(f"  MODERATE: {best['feat']} AUC={best['auc']:.3f} — better than physics, may help in combo")
        else:
            print(f"  WEAK: {best['feat']} AUC={best['auc']:.3f} — neural quality doesn't help either")


if __name__ == "__main__":
    main()
