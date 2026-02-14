#!/usr/bin/env python3
"""
echo-detector-v2.py — Physics-based echo detector (L-57).
Replaces Gate 16 z-score classifier.

Detection methods:
  1. Silence-region energy: echo bleeds into silence
  2. LPC residual autocorrelation: removes pitch, isolates echo
  3. Onset/offset sharpness: echo smears transitions
  4. Cepstral peak prominence
  5. Mel-band temporal coherence (cross-band correlation without pop stats)
  6. Spectral self-similarity
  7. Envelope autocorrelation

No population statistics. No training data. Works on any audio source.

Usage:
    python3 echo-detector-v2.py --file chunk.wav
    python3 echo-detector-v2.py --validate
    python3 echo-detector-v2.py --validate --verbose
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import librosa
from scipy.signal import hilbert, lfilter
from scipy.stats import mannwhitneyu

SR = 22050
MIN_DELAY_MS = 15
MAX_DELAY_MS = 200
FRAME_SIZE = 4096
HOP_SIZE = 1024

VAULT_DIR = Path("content/audio-free/vault")
V5_TEST_DIR = Path("reference/v5-test")

SESSION_NAMES = {
    "09": "09-rainfall-sleep-journey",
    "63": "63-21day-mindfulness-day07",
    "85": "85-counting-down-to-sleep",
}


# ─── Utility ─────────────────────────────────────────────────────────

def autocorrelation_fft(signal):
    """Normalized autocorrelation via FFT."""
    N = len(signal)
    signal = signal - np.mean(signal)
    if np.std(signal) < 1e-10:
        return np.zeros(N)
    fft_size = 2 ** int(np.ceil(np.log2(2 * N)))
    F = np.fft.rfft(signal, n=fft_size)
    acf = np.fft.irfft(F * np.conj(F))[:N]
    if acf[0] > 1e-10:
        acf = acf / acf[0]
    return acf


# ─── Feature Groups ─────────────────────────────────────────────────

def silence_energy_features(y, sr=SR):
    """
    Echo bleeds energy into silence regions.
    Measure energy ratio between silence and speech frames.
    """
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]

    # Adaptive threshold: bottom 25% of frames = "silence"
    threshold = np.percentile(rms, 25)
    silence_mask = rms < threshold
    speech_mask = rms >= np.percentile(rms, 75)

    silence_energy = np.mean(rms[silence_mask]) if np.any(silence_mask) else 0
    speech_energy = np.mean(rms[speech_mask]) if np.any(speech_mask) else 1e-10

    # Higher ratio = more echo bleeding into silence
    silence_ratio = silence_energy / (speech_energy + 1e-10)

    # Also measure the minimum RMS (absolute floor)
    min_rms = float(np.min(rms))

    # Energy in bottom 10% of frames (very quiet regions)
    q10 = np.percentile(rms, 10)
    quiet_mask = rms < q10 if q10 > 0 else rms == 0
    quiet_energy = float(np.mean(rms[quiet_mask])) if np.any(quiet_mask) else 0

    # Spectral energy in silence frames (broadband vs narrowband)
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
    # Average spectrum in silence frames
    if np.any(silence_mask[:S.shape[1]]):
        silence_spec = np.mean(S[:, silence_mask[:S.shape[1]]], axis=1)
        # Spectral flatness of silence (echo = broadband, noise = also broadband,
        # but clean silence = very low energy)
        silence_spec_flat = float(np.exp(np.mean(np.log(silence_spec + 1e-10))) /
                                  (np.mean(silence_spec) + 1e-10))
    else:
        silence_spec_flat = 0.0

    return {
        "silence_ratio": float(silence_ratio),
        "min_rms": min_rms,
        "quiet_energy": quiet_energy,
        "silence_spec_flat": silence_spec_flat,
    }


def lpc_residual_features(y, sr=SR):
    """
    LPC residual autocorrelation.
    LPC removes spectral envelope (formants + pitch harmonics).
    Echo shows up in the residual as peaks at the echo delay.
    """
    min_lag = int(MIN_DELAY_MS * sr / 1000)
    max_lag = int(MAX_DELAY_MS * sr / 1000)

    # LPC analysis (order 16 typical for speech at 22050 Hz)
    order = 16
    try:
        a = librosa.lpc(y, order=order)
    except Exception:
        return {"lpc_acf_peak": 0.0, "lpc_acf_mean": 0.0, "lpc_acf_energy": 0.0}

    residual = lfilter(a, 1, y)

    acf = autocorrelation_fft(residual)
    echo_region = acf[min_lag:min(max_lag, len(acf))]

    if len(echo_region) == 0:
        return {"lpc_acf_peak": 0.0, "lpc_acf_mean": 0.0, "lpc_acf_energy": 0.0}

    return {
        "lpc_acf_peak": float(np.max(echo_region)),
        "lpc_acf_mean": float(np.mean(echo_region)),
        "lpc_acf_energy": float(np.sum(echo_region ** 2)),
    }


def transition_features(y, sr=SR):
    """
    Echo smears onsets and extends offsets.
    Measure attack/decay sharpness of energy transitions.
    """
    rms = librosa.feature.rms(y=y, frame_length=512, hop_length=128)[0]
    if len(rms) < 10:
        return {"attack_sharpness": 0.0, "decay_sharpness": 0.0,
                "onset_spread": 0.0}

    # Find onsets
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=128)

    # Attack sharpness: how steep are the energy rises?
    energy_diff = np.diff(rms)
    positive_diffs = energy_diff[energy_diff > 0]
    attack_sharpness = float(np.percentile(positive_diffs, 90)) if len(positive_diffs) > 0 else 0.0

    # Decay sharpness: how steep are the energy falls?
    negative_diffs = energy_diff[energy_diff < 0]
    decay_sharpness = float(np.abs(np.percentile(negative_diffs, 10))) if len(negative_diffs) > 0 else 0.0

    # Onset spread: ratio of onset strength peak to surrounding area
    if len(onset_env) > 0:
        onset_peak = np.max(onset_env)
        onset_mean = np.mean(onset_env)
        onset_spread = float(onset_peak / (onset_mean + 1e-10))
    else:
        onset_spread = 0.0

    return {
        "attack_sharpness": attack_sharpness,
        "decay_sharpness": decay_sharpness,
        "onset_spread": onset_spread,
    }


def cepstral_echo_features(y, sr=SR):
    """Power cepstrum analysis. Echo → cepstral peak at echo delay."""
    min_q = int(MIN_DELAY_MS * sr / 1000)
    max_q = int(MAX_DELAY_MS * sr / 1000)

    frame_peaks = []
    frame_prominences = []

    for start in range(0, len(y) - FRAME_SIZE, HOP_SIZE):
        frame = y[start:start + FRAME_SIZE]
        window = np.hanning(FRAME_SIZE)
        Y = np.fft.rfft(frame * window)
        power = np.abs(Y) ** 2
        log_power = np.log(power + 1e-10)
        cepstrum = np.fft.irfft(log_power)
        echo_region = np.abs(cepstrum[min_q:min(max_q, len(cepstrum))])
        if len(echo_region) == 0:
            continue
        peak = np.max(echo_region)
        baseline = np.median(echo_region)
        frame_peaks.append(peak)
        frame_prominences.append(peak - baseline)

    if not frame_peaks:
        return {"ceps_prom_90": 0.0, "ceps_prom_max": 0.0}

    return {
        "ceps_prom_90": float(np.percentile(frame_prominences, 90)),
        "ceps_prom_max": float(np.max(frame_prominences)),
    }


def mel_coherence_features(y, sr=SR):
    """
    Cross-band temporal correlation.
    Echo = broadband copy → ALL mel bands correlate.
    Clean speech = different bands have different patterns.
    Directly computes corr_range without population normalization.
    """
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=80,
                                        n_fft=2048, hop_length=256)
    S_db = librosa.power_to_db(S, ref=np.max)

    # Compute pairwise correlation between adjacent mel bands
    n_bands = S_db.shape[0]
    correlations = []
    for i in range(n_bands - 1):
        band_a = S_db[i, :]
        band_b = S_db[i + 1, :]
        if np.std(band_a) < 1e-10 or np.std(band_b) < 1e-10:
            continue
        r = np.corrcoef(band_a, band_b)[0, 1]
        if not np.isnan(r):
            correlations.append(r)

    if not correlations:
        return {"mel_corr_mean": 0.0, "mel_corr_min": 0.0,
                "mel_corr_range": 0.0, "mel_corr_std": 0.0}

    correlations = np.array(correlations)

    return {
        "mel_corr_mean": float(np.mean(correlations)),
        "mel_corr_min": float(np.min(correlations)),
        "mel_corr_range": float(np.mean(correlations) - np.min(correlations)),
        "mel_corr_std": float(np.std(correlations)),
    }


def spectral_similarity_features(y, sr=SR):
    """Spectrogram frame self-similarity at various lags."""
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=256))
    S_log = np.log1p(S)
    norms = np.linalg.norm(S_log, axis=0, keepdims=True)
    S_norm = S_log / (norms + 1e-10)
    n_frames = S_norm.shape[1]

    if n_frames < 5:
        return {"spec_sim_peak": 0.0, "spec_sim_contrast": 0.0}

    min_lag = max(1, int(MIN_DELAY_MS * sr / (256 * 1000)))
    max_lag = min(n_frames - 1, int(MAX_DELAY_MS * sr / (256 * 1000)))

    lag_sims = []
    for d in range(min_lag, max_lag + 1):
        sims = np.sum(S_norm[:, :n_frames - d] * S_norm[:, d:], axis=0)
        lag_sims.append(float(np.mean(sims)))

    if not lag_sims:
        return {"spec_sim_peak": 0.0, "spec_sim_contrast": 0.0}

    lag_sims = np.array(lag_sims)
    return {
        "spec_sim_peak": float(np.max(lag_sims)),
        "spec_sim_contrast": float(np.max(lag_sims) - np.median(lag_sims)),
    }


def envelope_echo_features(y, sr=SR):
    """Amplitude envelope autocorrelation (pitch-independent)."""
    min_lag = int(MIN_DELAY_MS * sr / 1000)
    max_lag = int(MAX_DELAY_MS * sr / 1000)

    analytic = hilbert(y)
    envelope = np.abs(analytic)

    trend_win = int(0.3 * sr)
    if trend_win % 2 == 0:
        trend_win += 1
    if len(envelope) > trend_win:
        kernel = np.ones(trend_win) / trend_win
        trend = np.convolve(envelope, kernel, mode='same')
        envelope_hp = envelope - trend
    else:
        envelope_hp = envelope - np.mean(envelope)

    acf = autocorrelation_fft(envelope_hp)
    echo_region = acf[min_lag:min(max_lag, len(acf))]

    if len(echo_region) == 0:
        return {"env_acf_peak": 0.0, "env_acf_mean": 0.0}

    return {
        "env_acf_peak": float(np.max(echo_region)),
        "env_acf_mean": float(np.mean(echo_region)),
    }


def raw_acf_features(y, sr=SR):
    """Raw signal autocorrelation in echo delay region."""
    min_lag = int(MIN_DELAY_MS * sr / 1000)
    max_lag = int(MAX_DELAY_MS * sr / 1000)

    acf = autocorrelation_fft(y)

    pitch_min = int(5 * sr / 1000)
    pitch_max = int(15 * sr / 1000)
    pitch_region = acf[pitch_min:pitch_max]
    pitch_peak = float(np.max(pitch_region)) if len(pitch_region) > 0 else 0.0

    echo_region = acf[min_lag:min(max_lag, len(acf))]
    if len(echo_region) == 0:
        return {"raw_acf_peak": 0.0, "raw_acf_ratio": 0.0}

    echo_peak = float(np.max(echo_region))
    ratio = echo_peak / (pitch_peak + 1e-10) if pitch_peak > 0.01 else echo_peak

    return {
        "raw_acf_peak": echo_peak,
        "raw_acf_ratio": float(ratio),
    }


def reverb_tail_features(y, sr=SR):
    """
    Measure reverberant tail characteristics.
    Echo/reverb extends energy decay after speech segments end.
    """
    rms = librosa.feature.rms(y=y, frame_length=512, hop_length=128)[0]

    if len(rms) < 20:
        return {"decay_rate": 0.0, "tail_energy_ratio": 0.0, "edr_slope": 0.0}

    # Energy Decay Rate: fit exponential to energy envelope
    # Use the last portion of each speech segment
    # Simple approach: compute ratio of energy in final 20% vs first 80%
    n = len(rms)
    first_80 = rms[:int(0.8 * n)]
    last_20 = rms[int(0.8 * n):]

    tail_energy_ratio = float(np.mean(last_20) / (np.mean(first_80) + 1e-10))

    # Energy Decay Relief (EDR): integrate squared signal from end
    y_sq = y ** 2
    edr = np.cumsum(y_sq[::-1])[::-1]
    edr_db = 10 * np.log10(edr / (edr[0] + 1e-10) + 1e-10)

    # Slope of EDR in the -5 to -20 dB region
    mask = (edr_db > -20) & (edr_db < -5)
    if np.sum(mask) > 10:
        indices = np.where(mask)[0]
        x = indices.astype(float) / sr
        y_fit = edr_db[indices]
        # Linear regression
        coeffs = np.polyfit(x, y_fit, 1)
        edr_slope = float(coeffs[0])  # dB/sec — more negative = faster decay
    else:
        edr_slope = 0.0

    # Decay rate from RMS
    rms_db = 20 * np.log10(rms + 1e-10)
    diffs = np.diff(rms_db)
    neg_diffs = diffs[diffs < 0]
    decay_rate = float(np.median(neg_diffs)) if len(neg_diffs) > 0 else 0.0

    return {
        "decay_rate": decay_rate,
        "tail_energy_ratio": tail_energy_ratio,
        "edr_slope": edr_slope,
    }


def spectral_decay_features(y, sr=SR):
    """
    Measure how spectral energy decays over time.
    Echo prolongs spectral energy, especially in certain bands.
    """
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=256))

    # Spectral flux: frame-to-frame change in spectrum
    flux = np.sqrt(np.sum(np.diff(S, axis=1) ** 2, axis=0))
    spectral_flux_mean = float(np.mean(flux))
    spectral_flux_std = float(np.std(flux))

    # Spectral centroid stability: echo makes centroid more stable
    # (because echo is a broadband copy with same centroid)
    centroid = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
    centroid_std = float(np.std(centroid))
    centroid_cv = float(np.std(centroid) / (np.mean(centroid) + 1e-10))

    return {
        "spectral_flux_mean": spectral_flux_mean,
        "spectral_flux_std": spectral_flux_std,
        "centroid_std": centroid_std,
        "centroid_cv": centroid_cv,
    }


def extract_all_features(wav_path, sr=SR):
    """Extract all echo features from a WAV file."""
    y, _ = librosa.load(wav_path, sr=sr, mono=True)
    if len(y) < sr * 0.3:
        return None

    features = {}
    features.update(silence_energy_features(y, sr))
    features.update(lpc_residual_features(y, sr))
    features.update(transition_features(y, sr))
    features.update(cepstral_echo_features(y, sr))
    features.update(mel_coherence_features(y, sr))
    features.update(spectral_similarity_features(y, sr))
    features.update(envelope_echo_features(y, sr))
    features.update(raw_acf_features(y, sr))
    features.update(reverb_tail_features(y, sr))
    features.update(spectral_decay_features(y, sr))

    return features


# ─── Validation ──────────────────────────────────────────────────────

def load_validation_data():
    """Load verdict files → (wav_path, labels, passed) tuples."""
    samples = []

    configs = [
        ("85", "85-verdicts-r2.json"),
        ("63", "63-verdicts-r2.json"),
    ]

    for session_short, verdict_file in configs:
        session_name = SESSION_NAMES[session_short]
        verdict_path = V5_TEST_DIR / verdict_file

        if not verdict_path.exists():
            print(f"  WARNING: {verdict_path} not found")
            continue

        with open(verdict_path) as f:
            verdicts = json.load(f)

        for chunk_id, verdict in verdicts.get("chunks", {}).items():
            ci = int(chunk_id)
            vi = verdict.get("version", 0)
            wav_path = VAULT_DIR / session_name / f"c{ci:02d}" / f"c{ci:02d}_v{vi:02d}.wav"

            if not wav_path.exists():
                print(f"  WARNING: {wav_path} not found")
                continue

            labels = verdict.get("verdict", [])
            passed = verdict.get("passed", True)

            samples.append({
                "session": session_short,
                "chunk": chunk_id,
                "wav_path": str(wav_path),
                "labels": labels,
                "passed": passed,
                "is_echo": "ECHO" in labels,
            })

    return samples


def find_optimal_threshold(values_labels, higher_is_echo=True):
    """Find threshold maximizing Youden's J index."""
    if not values_labels:
        return 0, 0, 0, 0

    vals = [v for v, _ in values_labels]
    thresholds = np.linspace(min(vals), max(vals), 300)

    best_j, best_thresh, best_recall, best_spec = 0, 0, 0, 0

    for thresh in thresholds:
        if higher_is_echo:
            tp = sum(1 for v, e in values_labels if v >= thresh and e)
            fn = sum(1 for v, e in values_labels if v < thresh and e)
            fp = sum(1 for v, e in values_labels if v >= thresh and not e)
            tn = sum(1 for v, e in values_labels if v < thresh and not e)
        else:
            tp = sum(1 for v, e in values_labels if v <= thresh and e)
            fn = sum(1 for v, e in values_labels if v > thresh and e)
            fp = sum(1 for v, e in values_labels if v <= thresh and not e)
            tn = sum(1 for v, e in values_labels if v > thresh and not e)

        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        j = recall + spec - 1

        if j > best_j:
            best_j = j
            best_thresh = thresh
            best_recall = recall
            best_spec = spec

    return best_thresh, best_recall, best_spec, best_j


def validate(verbose=False):
    """Run validation against labelled data."""
    print("Loading validation data...")
    samples = load_validation_data()

    if not samples:
        print("ERROR: No validation samples found!")
        return

    echo_count = sum(1 for s in samples if s["is_echo"])
    clean_count = sum(1 for s in samples if not s["is_echo"])
    print(f"Loaded {len(samples)} samples: {echo_count} ECHO, {clean_count} non-ECHO")
    print()

    print("Extracting features...")
    for i, sample in enumerate(samples):
        features = extract_all_features(sample["wav_path"])
        sample["features"] = features
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(samples)}")

    samples = [s for s in samples if s["features"] is not None]
    echo_count = sum(1 for s in samples if s["is_echo"])
    clean_count = sum(1 for s in samples if not s["is_echo"])
    print(f"\nValid: {len(samples)} ({echo_count} ECHO, {clean_count} non-ECHO)")

    feature_names = sorted(samples[0]["features"].keys())

    print(f"\n{'='*80}")
    print("FEATURE ANALYSIS: ECHO vs non-ECHO")
    print(f"{'='*80}")

    results = []

    for feat in feature_names:
        echo_vals = [s["features"][feat] for s in samples if s["is_echo"]]
        clean_vals = [s["features"][feat] for s in samples if not s["is_echo"]]

        echo_mean = np.mean(echo_vals)
        clean_mean = np.mean(clean_vals)
        pooled_std = np.sqrt((np.std(echo_vals)**2 + np.std(clean_vals)**2) / 2)
        cohens_d = abs(echo_mean - clean_mean) / (pooled_std + 1e-10)

        try:
            U, p = mannwhitneyu(echo_vals, clean_vals, alternative='two-sided')
            auc = U / (len(echo_vals) * len(clean_vals))
            higher_is_echo = auc >= 0.5
            if auc < 0.5:
                auc = 1 - auc
        except Exception:
            auc, p, higher_is_echo = 0.5, 1.0, True

        vl = [(s["features"][feat], s["is_echo"]) for s in samples]
        thresh_hi, recall_hi, spec_hi, j_hi = find_optimal_threshold(vl, True)
        thresh_lo, recall_lo, spec_lo, j_lo = find_optimal_threshold(vl, False)

        if j_hi >= j_lo:
            thresh, recall, spec, j = thresh_hi, recall_hi, spec_hi, j_hi
            direction = "higher=echo"
        else:
            thresh, recall, spec, j = thresh_lo, recall_lo, spec_lo, j_lo
            direction = "lower=echo"

        results.append({
            "feature": feat, "auc": auc, "cohens_d": cohens_d, "p": p,
            "direction": direction, "threshold": thresh,
            "recall": recall, "specificity": spec, "youdens_j": j,
            "echo_mean": echo_mean, "clean_mean": clean_mean,
        })

    results.sort(key=lambda r: r["auc"], reverse=True)

    for r in results:
        marker = "***" if r["auc"] >= 0.70 else "   "
        print(f"\n{marker} {r['feature']}:")
        print(f"    ECHO={r['echo_mean']:.6f}  CLEAN={r['clean_mean']:.6f}  "
              f"d={r['cohens_d']:.3f}")
        print(f"    AUC={r['auc']:.3f}  p={r['p']:.2e}  ({r['direction']})")
        print(f"    Thresh={r['threshold']:.6f}  Recall={r['recall']:.0%}  "
              f"Spec={r['specificity']:.0%}  J={r['youdens_j']:.3f}")

    # Top 5 features summary
    print(f"\n{'='*80}")
    print("TOP 5 FEATURES:")
    for i, r in enumerate(results[:5]):
        print(f"  {i+1}. {r['feature']:25s}  AUC={r['auc']:.3f}  "
              f"J={r['youdens_j']:.3f}  Recall={r['recall']:.0%}")
    print(f"{'='*80}")

    # Try simple combinations of top features
    print(f"\n{'='*80}")
    print("FEATURE COMBINATIONS (sum of top features, normalized):")
    print(f"{'='*80}")

    top_feats = [r for r in results if r["auc"] >= 0.60]
    if len(top_feats) >= 2:
        # Try pairwise and triple combinations
        from itertools import combinations
        combo_results = []

        for n_combo in [2, 3]:
            for combo in combinations(top_feats[:8], n_combo):
                feat_names = [c["feature"] for c in combo]
                # Combine: normalize each feature to [0,1] then sum
                combo_scores = []
                for s in samples:
                    score = 0
                    for c in combo:
                        vals = [s2["features"][c["feature"]] for s2 in samples]
                        v = s["features"][c["feature"]]
                        mn, mx = min(vals), max(vals)
                        if mx - mn > 1e-10:
                            norm_v = (v - mn) / (mx - mn)
                        else:
                            norm_v = 0.5
                        if c["direction"] == "lower=echo":
                            norm_v = 1 - norm_v
                        score += norm_v
                    combo_scores.append((score, s["is_echo"]))

                thresh, recall, spec, j = find_optimal_threshold(combo_scores, True)

                # AUC
                echo_scores = [sc for sc, e in combo_scores if e]
                clean_scores = [sc for sc, e in combo_scores if not e]
                try:
                    U, _ = mannwhitneyu(echo_scores, clean_scores, alternative='two-sided')
                    auc = U / (len(echo_scores) * len(clean_scores))
                    if auc < 0.5:
                        auc = 1 - auc
                except:
                    auc = 0.5

                combo_results.append({
                    "features": "+".join(feat_names),
                    "auc": auc, "recall": recall, "spec": spec, "j": j,
                })

        combo_results.sort(key=lambda r: r["auc"], reverse=True)
        for r in combo_results[:10]:
            print(f"  {r['features']}")
            print(f"    AUC={r['auc']:.3f}  Recall={r['recall']:.0%}  "
                  f"Spec={r['spec']:.0%}  J={r['j']:.3f}")

    # Per-sample detail for best feature
    if verbose and results:
        best = results[0]
        best_feat = best["feature"]
        higher_is_echo = best["direction"] == "higher=echo"
        thresh = best["threshold"]

        print(f"\nPer-sample ({best_feat}, thresh={thresh:.6f}):")
        print("─" * 90)

        sorted_samples = sorted(samples,
            key=lambda s: s["features"][best_feat],
            reverse=higher_is_echo)

        tp = fn = fp = tn = 0
        for s in sorted_samples:
            val = s["features"][best_feat]
            is_echo = s["is_echo"]
            if higher_is_echo:
                predicted = val >= thresh
            else:
                predicted = val <= thresh

            if is_echo and predicted:
                marker, tp = " TP", tp + 1
            elif is_echo and not predicted:
                marker, fn = " FN", fn + 1
            elif not is_echo and predicted:
                marker, fp = " FP", fp + 1
            else:
                marker, tn = "   ", tn + 1

            labels = ",".join(s["labels"])
            print(f"  {marker}  S{s['session']}-c{s['chunk']:>2s}  "
                  f"{best_feat}={val:.6f}  [{labels}]")

        print(f"\n  TP={tp} FN={fn} FP={fp} TN={tn}")

    # Save
    output = {
        "feature_rankings": results,
        "n_samples": len(samples), "n_echo": echo_count, "n_clean": clean_count,
        "samples": [{
            "session": s["session"], "chunk": s["chunk"],
            "is_echo": s["is_echo"], "labels": s["labels"],
            "features": s["features"],
        } for s in samples],
    }
    out_path = V5_TEST_DIR / "echo-v2-validation.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {out_path}")


def analyze_file(wav_path):
    """Analyze a single WAV file."""
    features = extract_all_features(wav_path)
    if features is None:
        print("ERROR: Could not extract features (file too short?)")
        return
    print(f"Echo analysis: {wav_path}")
    print("─" * 60)
    for name, value in sorted(features.items()):
        print(f"  {name:25s} = {value:.6f}")


def main():
    parser = argparse.ArgumentParser(description="Physics-based echo detector (L-57)")
    parser.add_argument("--file", type=str, help="Analyze single WAV file")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.file:
        analyze_file(args.file)
    elif args.validate:
        validate(verbose=args.verbose)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
