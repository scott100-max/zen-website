#!/usr/bin/env python3
"""
Use Whisper encoder embeddings to detect echo.
Whisper was trained on 680k hours of speech — its internal representations
capture fine-grained acoustic patterns beyond what hand-crafted features can.

Approach:
1. Extract Whisper encoder embeddings for all labelled samples
2. Use embedding statistics as features
3. Compute AUC for ECHO vs PASS classification
4. Test within-chunk ranking using embedding distance from pool centroid

Usage:
    python3 tools/whisper-echo-validate.py
"""
import json
import sys
import numpy as np
from pathlib import Path

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


def extract_whisper_embeddings(wav_paths, model_name="base"):
    """Extract Whisper encoder embeddings for a list of WAV files."""
    import whisper
    import torch
    import librosa

    print(f"  Loading Whisper {model_name}...")
    model = whisper.load_model(model_name)
    model.eval()

    embeddings = []
    for i, wav_path in enumerate(wav_paths):
        # Load and preprocess audio (Whisper expects 16kHz, padded to 30s)
        audio = whisper.load_audio(wav_path)
        audio = whisper.pad_or_trim(audio)  # 30s at 16kHz

        # Get mel spectrogram (Whisper's input format)
        mel = whisper.log_mel_spectrogram(audio).unsqueeze(0).to(model.device)

        # Extract encoder output (all layers)
        with torch.no_grad():
            # Run through encoder
            encoder_output = model.encoder(mel)
            # encoder_output shape: (1, time_steps, d_model)
            emb = encoder_output.squeeze(0).cpu().numpy()  # (T, D)

        embeddings.append(emb)
        if (i + 1) % 10 == 0:
            print(f"  Extracted: {i+1}/{len(wav_paths)}")

    print(f"  Extracted: {len(wav_paths)}/{len(wav_paths)} done")
    return embeddings


def embedding_to_features(emb):
    """Convert a (T, D) embedding matrix to a fixed-size feature vector."""
    # Statistics across time dimension
    features = {}

    # Global stats
    mean = np.mean(emb, axis=0)  # (D,)
    std = np.std(emb, axis=0)    # (D,)
    features["emb_mean_norm"] = float(np.linalg.norm(mean))
    features["emb_std_mean"] = float(np.mean(std))
    features["emb_std_std"] = float(np.std(std))

    # Temporal variation (how much the embedding changes over time)
    diffs = np.diff(emb, axis=0)
    features["emb_temporal_var"] = float(np.mean(np.linalg.norm(diffs, axis=1)))
    features["emb_temporal_var_std"] = float(np.std(np.linalg.norm(diffs, axis=1)))

    # Self-similarity (cosine similarity between frames)
    # Sample pairs for efficiency
    n_frames = emb.shape[0]
    if n_frames > 20:
        indices = np.random.choice(n_frames, 20, replace=False)
        sample = emb[indices]
    else:
        sample = emb

    norms = np.linalg.norm(sample, axis=1, keepdims=True) + 1e-10
    normalized = sample / norms
    sim_matrix = normalized @ normalized.T
    # Take upper triangle (excluding diagonal)
    triu_indices = np.triu_indices_from(sim_matrix, k=1)
    similarities = sim_matrix[triu_indices]
    features["emb_self_sim_mean"] = float(np.mean(similarities))
    features["emb_self_sim_std"] = float(np.std(similarities))
    features["emb_self_sim_min"] = float(np.min(similarities))

    # Spectral analysis of embedding time series (modulation patterns)
    # Use first 10 principal components
    from numpy.linalg import svd
    U, S, Vt = svd(emb - mean, full_matrices=False)
    # Singular value distribution
    features["emb_sv_ratio"] = float(S[0] / (S[1] + 1e-10))  # dominance of first component
    features["emb_sv_entropy"] = float(-np.sum((S/S.sum()) * np.log(S/S.sum() + 1e-10)))

    # Energy in first few PCs vs total
    total_energy = float(np.sum(S**2))
    features["emb_pc1_energy"] = float(S[0]**2 / total_energy) if total_energy > 0 else 0
    features["emb_pc3_energy"] = float(np.sum(S[:3]**2) / total_energy) if total_energy > 0 else 0
    features["emb_pc10_energy"] = float(np.sum(S[:10]**2) / total_energy) if total_energy > 0 else 0

    # Modulation spectrum of the temporal trajectory in PC1
    pc1_trajectory = U[:, 0] * S[0]
    fft_pc1 = np.abs(np.fft.rfft(pc1_trajectory))
    features["emb_mod_low"] = float(np.mean(fft_pc1[:10]))  # low modulation frequencies
    features["emb_mod_high"] = float(np.mean(fft_pc1[10:50]))  # higher modulation
    features["emb_mod_ratio"] = float(features["emb_mod_low"] / (features["emb_mod_high"] + 1e-10))

    return features


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


def within_chunk_ranking_embeddings(echo_samples, echo_embeddings, model_name="base"):
    """For each echo chunk, compute embedding distance from pool centroid.
    If echo candidates are outliers, they should be farther from centroid."""
    import whisper
    import torch

    print("\n  Loading Whisper for within-chunk ranking...")
    model = whisper.load_model(model_name)
    model.eval()

    correct_centroid = 0
    correct_nearest = 0
    total = 0

    for idx, s in enumerate(echo_samples):
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

        # Sample up to 10 alternatives
        np.random.seed(42 + ci)
        if len(alt_wavs) > 10:
            indices = np.random.choice(len(alt_wavs), 10, replace=False)
            alt_wavs = [alt_wavs[i] for i in indices]

        # Extract embeddings for alternatives
        all_embeddings = [echo_embeddings[idx]]  # echo candidate embedding
        all_labels = [True]  # True = echo

        for alt_wav in alt_wavs:
            audio = whisper.load_audio(str(alt_wav))
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).unsqueeze(0).to(model.device)
            with torch.no_grad():
                enc = model.encoder(mel).squeeze(0).cpu().numpy()
            all_embeddings.append(enc)
            all_labels.append(False)

        # Compute mean embedding for each candidate (collapse time)
        mean_embs = [np.mean(e, axis=0) for e in all_embeddings]
        mean_embs = np.array(mean_embs)

        # Centroid of ALL candidates
        centroid = np.mean(mean_embs, axis=0)

        # Distance from centroid
        distances = [np.linalg.norm(e - centroid) for e in mean_embs]

        # Is echo candidate the farthest from centroid?
        echo_dist = distances[0]
        alt_dists = distances[1:]

        for alt_d in alt_dists:
            total += 1
            # Centroid method: echo should be farther from centroid
            if echo_dist > alt_d:
                correct_centroid += 1

        if (idx + 1) % 5 == 0:
            print(f"    Processed {idx+1}/{len(echo_samples)} echo chunks")

    return correct_centroid, total


def main():
    np.random.seed(42)

    print("=" * 70)
    print("WHISPER ENCODER EMBEDDINGS — ECHO vs PASS VALIDATION")
    print("=" * 70)

    echo_samples, pass_samples = load_samples()
    print(f"\nSamples: {len(echo_samples)} ECHO, {len(pass_samples)} PASS")
    all_samples = echo_samples + pass_samples

    # Extract embeddings
    print("\n--- Extracting Whisper Embeddings ---")
    wav_paths = [s["wav"] for s in all_samples]
    embeddings = extract_whisper_embeddings(wav_paths, model_name="base")

    # Convert to features
    print("\n--- Computing Embedding Features ---")
    for i, (s, emb) in enumerate(zip(all_samples, embeddings)):
        s["emb"] = emb
        feats = embedding_to_features(emb)
        s.update(feats)

    # Evaluate each embedding feature
    print("\n" + "=" * 70)
    print("RESULTS: Whisper Embedding Features")
    print("=" * 70)

    feat_names = sorted(embedding_to_features(embeddings[0]).keys())
    results = []
    for feat in feat_names:
        echo_vals = [s[feat] for s in echo_samples]
        pass_vals = [s[feat] for s in pass_samples]
        auc, direction, p = compute_auc(echo_vals, pass_vals)
        d = abs(np.mean(echo_vals) - np.mean(pass_vals)) / (
            np.sqrt((np.std(echo_vals)**2 + np.std(pass_vals)**2) / 2) + 1e-10)
        results.append({"feat": feat, "auc": auc, "d": d, "dir": direction, "p": p,
                        "echo_mean": np.mean(echo_vals), "pass_mean": np.mean(pass_vals)})

    results.sort(key=lambda x: x["auc"], reverse=True)
    print(f"\n{'Feature':>25s}  {'AUC':>6s}  {'d':>5s}  {'Direction':>15s}  {'p':>8s}")
    print("─" * 75)
    for r in results:
        m = "***" if r["auc"] >= 0.70 else "   "
        print(f"{m} {r['feat']:>22s}  {r['auc']:.3f}  {r['d']:.2f}  {r['dir']:>15s}  {r['p']:.4f}")

    # Raw embedding distance analysis
    print(f"\n{'='*70}")
    print("RAW EMBEDDING ANALYSIS")
    print(f"{'='*70}")

    # Compute mean embedding for each sample
    echo_means = np.array([np.mean(s["emb"], axis=0) for s in echo_samples])
    pass_means = np.array([np.mean(s["emb"], axis=0) for s in pass_samples])

    # Centroid of all clean samples
    clean_centroid = np.mean(pass_means, axis=0)

    # Distance from clean centroid
    echo_dists = [np.linalg.norm(e - clean_centroid) for e in echo_means]
    pass_dists = [np.linalg.norm(e - clean_centroid) for e in pass_means]

    auc_centroid, dir_centroid, p_centroid = compute_auc(echo_dists, pass_dists)
    print(f"\n  Distance from CLEAN centroid:")
    print(f"    ECHO mean dist: {np.mean(echo_dists):.4f} +/- {np.std(echo_dists):.4f}")
    print(f"    PASS mean dist: {np.mean(pass_dists):.4f} +/- {np.std(pass_dists):.4f}")
    print(f"    AUC: {auc_centroid:.3f}  direction: {dir_centroid}  p={p_centroid:.4f}")

    # Linear probe: simple logistic regression on mean embeddings
    print(f"\n{'='*70}")
    print("LINEAR PROBE (Logistic Regression on Mean Embeddings)")
    print(f"{'='*70}")

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import LeaveOneOut, cross_val_predict
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import roc_auc_score, classification_report

        X = np.vstack([echo_means, pass_means])
        y = np.array([1] * len(echo_means) + [0] * len(pass_means))

        # Leave-one-out cross-validation (small sample)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Use PCA to reduce dimensionality (more samples than features needed)
        from sklearn.decomposition import PCA
        for n_components in [5, 10, 20, 50]:
            pca = PCA(n_components=n_components)
            X_pca = pca.fit_transform(X_scaled)

            loo = LeaveOneOut()
            y_scores = np.zeros(len(y), dtype=float)
            for train_idx, test_idx in loo.split(X_pca):
                clf = LogisticRegression(C=0.01, max_iter=1000)
                clf.fit(X_pca[train_idx], y[train_idx])
                y_scores[test_idx] = clf.predict_proba(X_pca[test_idx])[:, 1]

            auc_loo = roc_auc_score(y, y_scores)
            print(f"\n  PCA({n_components}) + LogReg LOO-CV: AUC = {auc_loo:.3f}")

            # Threshold analysis
            from sklearn.metrics import precision_recall_curve
            precision, recall, thresholds = precision_recall_curve(y, y_scores)
            # Find threshold for 80% recall
            for i, r in enumerate(recall):
                if r <= 0.80:
                    break
            if i > 0:
                print(f"    At 80% recall: precision={precision[i-1]:.0%}")

    except ImportError:
        print("  sklearn not available — skipping linear probe")

    # Within-chunk ranking test
    print(f"\n{'='*70}")
    print("WITHIN-CHUNK RANKING (Embedding Centroid Distance)")
    print(f"{'='*70}")

    echo_embeddings = embeddings[:len(echo_samples)]
    correct, total = within_chunk_ranking_embeddings(
        echo_samples, echo_embeddings, model_name="base")
    if total > 0:
        print(f"\n  Centroid distance: {correct}/{total} correct ({correct/total:.1%})")
        print(f"  (correct = echo candidate farther from pool centroid than alternative)")
    else:
        print("  No comparisons available")

    # Combo: Whisper features + physics + DNSMOS
    print(f"\n{'='*70}")
    print("COMBO: Best Whisper + Physics + Neural features")
    print(f"{'='*70}")

    # Load physics features
    try:
        from importlib.machinery import SourceFileLoader
        det = SourceFileLoader("det", "echo-detector-v2.py").load_module()
        for s in all_samples:
            feats_phys = det.extract_all_features(s["wav"])
            if feats_phys:
                s["ceps_prom_max"] = feats_phys.get("ceps_prom_max", 0)

        from speechmos import dnsmos
        import librosa
        import soundfile as sf
        for s in all_samples:
            audio, sr = sf.read(s["wav"])
            if sr != 16000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            result = dnsmos.run(audio, sr=16000)
            s["dnsmos_p808"] = float(result["p808_mos"])

        # Find best whisper features
        best_whisper = [r["feat"] for r in results if r["auc"] >= 0.60][:3]
        combo_feats = best_whisper + ["ceps_prom_max", "dnsmos_p808"]

        print(f"\n  Testing combo: {' + '.join(combo_feats)}")

        # Simple scoring: normalize and sum
        scores = []
        for s in all_samples:
            score = 0
            for f in combo_feats:
                vals = [s2.get(f, 0) for s2 in all_samples]
                v = s.get(f, 0)
                mn, mx = min(vals), max(vals)
                nv = (v - mn) / (mx - mn + 1e-10)
                # Check direction
                ev = [s2.get(f, 0) for s2 in echo_samples]
                pv = [s2.get(f, 0) for s2 in pass_samples]
                if np.mean(ev) < np.mean(pv):
                    nv = 1 - nv
                score += nv
            is_echo = "ECHO" in s["labels"]
            scores.append((score, is_echo))

        from scipy.stats import mannwhitneyu
        e_sc = [sc for sc, e in scores if e]
        c_sc = [sc for sc, e in scores if not e]
        U, _ = mannwhitneyu(e_sc, c_sc)
        auc_combo = U / (len(e_sc) * len(c_sc))
        if auc_combo < 0.5:
            auc_combo = 1 - auc_combo
        print(f"  Combo AUC: {auc_combo:.3f}")

    except Exception as e:
        print(f"  Combo test failed: {e}")


if __name__ == "__main__":
    main()
