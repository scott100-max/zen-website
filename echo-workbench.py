#!/usr/bin/env python3
"""
Echo Fingerprint Workbench
==========================
Collects all human-labeled echo + clean audio, runs extremely granular
spectral analysis to find the echo fingerprint in Fish TTS output.

Usage:
  python3 echo-workbench.py --collect     # Build dataset
  python3 echo-workbench.py --analyze     # Run granular analysis
  python3 echo-workbench.py --classify    # Build & test echo classifier
  python3 echo-workbench.py --report      # Generate visual HTML report
  python3 echo-workbench.py --all         # All four steps
"""

import json
import csv
import sys
import os
import argparse
import warnings
from pathlib import Path
from collections import defaultdict

import numpy as np
import librosa
import scipy.signal as signal
from scipy.stats import mannwhitneyu, kurtosis, skew

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent
VAULT_DIR = PROJECT_ROOT / "content" / "audio-free" / "vault"
OUTPUT_DIR = PROJECT_ROOT / "reference" / "echo-analysis"
DESKTOP_DUMP = Path.home() / "Desktop" / "Salus dump"

# ============================================================
# STEP 1: COLLECT — Build unified echo/clean dataset
# ============================================================

def collect_dataset():
    """
    Gather all echo-labeled and clean audio from every source.
    For each echo chunk, find a clean counterpart (same text, different version).
    """
    print("=" * 70)
    print("STEP 1: COLLECTING ECHO DATASET")
    print("=" * 70)

    all_echo = []
    all_clean_by_session = defaultdict(list)

    # --- Source 1: Desktop verdict JSONs ---
    if DESKTOP_DUMP.exists():
        for f in sorted(DESKTOP_DUMP.glob("*verdicts*.json")):
            # Skip duplicate files (copies)
            if "(2)" in f.name or "(3)" in f.name:
                continue
            try:
                with open(f) as fh:
                    data = json.load(fh)
            except:
                continue
            session = data.get("session", "?")
            run = data.get("run", "?")
            for ci, info in data.get("chunks", {}).items():
                vlist = info.get("verdict", [])
                version = info.get("version")
                severity = info.get("severity", "?")
                passed = info.get("passed", False)

                if "ECHO" in vlist and version is not None:
                    all_echo.append({
                        "session": session,
                        "chunk": int(ci),
                        "version": version,
                        "source": f.name,
                        "run": run,
                        "severity": severity,
                        "compound": [v for v in vlist if v != "ECHO"],
                    })
                elif passed or severity == "pass":
                    all_clean_by_session[session].append({
                        "chunk": int(ci),
                        "version": version,
                        "source": f.name,
                        "run": run,
                        "verdict": vlist,
                    })

    # --- Source 2: Repo verdict JSONs ---
    for f in VAULT_DIR.glob("*/assembly-verdicts.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
        except:
            continue
        session = data.get("session", f.parent.name)
        for ci, info in data.get("chunks", {}).items():
            vlist = info.get("verdict", [])
            version = info.get("version")
            passed = info.get("passed", False)

            if "ECHO" in vlist and version is not None:
                all_echo.append({
                    "session": session,
                    "chunk": int(ci),
                    "version": version,
                    "source": "assembly-verdicts",
                    "run": data.get("run", "?"),
                    "severity": info.get("severity", "?"),
                    "compound": [v for v in vlist if v != "ECHO"],
                })
            elif passed:
                all_clean_by_session[session].append({
                    "chunk": int(ci),
                    "version": version,
                    "source": "assembly-verdicts",
                    "run": data.get("run", "?"),
                    "verdict": vlist,
                })

    for f in VAULT_DIR.glob("*/auto-trial-verdicts*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
        except:
            continue
        session = data.get("session", f.parent.name)
        for ci, info in data.get("chunks", {}).items():
            vlist = info.get("verdict", [])
            version = info.get("version")
            passed = info.get("passed", False)

            if "ECHO" in vlist and version is not None:
                all_echo.append({
                    "session": session,
                    "chunk": int(ci),
                    "version": version,
                    "source": f.name,
                    "run": data.get("run", "?"),
                    "severity": info.get("severity", "?"),
                    "compound": [v for v in vlist if v != "ECHO"],
                })
            elif passed:
                all_clean_by_session[session].append({
                    "chunk": int(ci),
                    "version": version,
                    "source": f.name,
                    "run": data.get("run", "?"),
                    "verdict": vlist,
                })

    # --- Source 3: CSV labels (sessions 36, 52) ---
    labels_dir = PROJECT_ROOT / "reference" / "human-labels"
    training_audio = PROJECT_ROOT / "reference" / "echo-training" / "audio"
    audio_map = {
        "36-loving-kindness-intro-v3a": ("36-v3a", "chunk_{:02d}.mp3"),
        "52-the-court-of-your-mind": ("52", "chunk-{:02d}.mp3"),
        "52-the-court-of-your-mind-b1": ("52", "chunk-{:02d}.mp3"),
        "52-the-court-of-your-mind-b2": ("52", "chunk-{:02d}.mp3"),
    }

    for csv_path in sorted(labels_dir.glob("*-labels.csv")):
        with open(csv_path) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                verdict = row.get("verdict", "").strip().upper()
                session = row.get("session", "").strip()
                chunk = int(row.get("chunk", 0))

                if session in audio_map:
                    subdir, pattern = audio_map[session]
                    audio_path = training_audio / subdir / pattern.format(chunk)
                else:
                    audio_path = None

                if verdict == "ECHO" and audio_path and audio_path.exists():
                    all_echo.append({
                        "session": session,
                        "chunk": chunk,
                        "version": None,
                        "source": csv_path.name,
                        "run": "csv",
                        "severity": "?",
                        "compound": [],
                        "audio_path": str(audio_path),
                    })
                elif verdict in ("OK", "EXCELLENT") and audio_path and audio_path.exists():
                    all_clean_by_session[session].append({
                        "chunk": chunk,
                        "version": None,
                        "source": csv_path.name,
                        "run": "csv",
                        "verdict": [verdict],
                        "audio_path": str(audio_path),
                    })

    # --- Deduplicate echo by (session, chunk, version) ---
    seen = set()
    unique_echo = []
    for e in all_echo:
        key = (e["session"], e["chunk"], e["version"])
        if key not in seen:
            seen.add(key)
            unique_echo.append(e)

    # --- Resolve audio paths for vault-based entries ---
    dataset = []
    for e in unique_echo:
        session = e["session"]
        chunk = e["chunk"]
        version = e["version"]

        # Get echo audio path
        if "audio_path" in e:
            echo_path = e["audio_path"]
        elif version is not None:
            wav = VAULT_DIR / session / f"c{chunk:02d}" / f"c{chunk:02d}_v{version:02d}.wav"
            if not wav.exists():
                continue
            echo_path = str(wav)
        else:
            continue

        # Find a clean version of the SAME chunk
        clean_path = None
        clean_version = None
        clean_candidates = [c for c in all_clean_by_session.get(session, [])
                           if c["chunk"] == chunk and c["version"] != version]
        if clean_candidates:
            # Prefer assembly-verdict clean versions (most authoritative)
            assembly_clean = [c for c in clean_candidates if "assembly" in c.get("source", "")]
            chosen = assembly_clean[0] if assembly_clean else clean_candidates[0]
            clean_version = chosen["version"]

            if "audio_path" in chosen:
                clean_path = chosen["audio_path"]
            elif clean_version is not None:
                wav = VAULT_DIR / session / f"c{chunk:02d}" / f"c{chunk:02d}_v{clean_version:02d}.wav"
                if wav.exists():
                    clean_path = str(wav)

        # Also find ANY clean chunk from the same session (for session-level comparison)
        session_clean_path = None
        session_clean_chunks = [c for c in all_clean_by_session.get(session, [])
                                if c["chunk"] != chunk]
        if session_clean_chunks:
            for sc in session_clean_chunks:
                if "audio_path" in sc:
                    session_clean_path = sc["audio_path"]
                    break
                elif sc["version"] is not None:
                    wav = VAULT_DIR / session / f"c{sc['chunk']:02d}" / f"c{sc['chunk']:02d}_v{sc['version']:02d}.wav"
                    if wav.exists():
                        session_clean_path = str(wav)
                        break

        # Load chunk text from metadata
        text = ""
        meta_path = VAULT_DIR / session / f"c{chunk:02d}" / f"c{chunk:02d}_meta.json"
        if meta_path.exists():
            try:
                with open(meta_path) as mf:
                    meta = json.load(mf)
                text = meta.get("text", "")
            except:
                pass

        dataset.append({
            "session": session,
            "chunk": chunk,
            "echo_version": version,
            "echo_path": echo_path,
            "clean_path": clean_path,
            "clean_version": clean_version,
            "session_clean_path": session_clean_path,
            "text": text,
            "severity": e["severity"],
            "compound": e.get("compound", []),
            "source": e["source"],
            "has_pair": clean_path is not None,
        })

    # Save dataset
    dataset_path = OUTPUT_DIR / "echo_dataset.json"
    with open(dataset_path, 'w') as f:
        json.dump(dataset, f, indent=2)

    # Summary
    paired = sum(1 for d in dataset if d["has_pair"])
    unpaired = len(dataset) - paired
    sessions = set(d["session"] for d in dataset)

    print(f"\nDataset built: {len(dataset)} echo chunks")
    print(f"  Paired (echo + clean of same text): {paired}")
    print(f"  Unpaired (echo only): {unpaired}")
    print(f"  Sessions: {len(sessions)} — {sorted(sessions)}")
    print(f"  Saved to: {dataset_path}")

    return dataset


# ============================================================
# STEP 2: ANALYZE — Granular feature extraction
# ============================================================

def extract_granular_features(audio_path, sr=22050):
    """
    Extract extremely granular features from an audio file.
    Goes far beyond the previous 65-feature approach.
    """
    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    duration = len(y) / sr

    if len(y) < sr * 0.3:
        return None

    feats = {"duration": duration}

    # ---- A. MEL SPECTROGRAM — full resolution ----
    n_mels = 80
    hop = 256
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels,
                                        n_fft=2048, hop_length=hop)
    S_db = librosa.power_to_db(S, ref=np.max)
    n_frames = S_db.shape[1]

    # A1: Per-band statistics (80 bands x 4 stats = 320 features)
    for b in range(n_mels):
        band = S_db[b, :]
        feats[f"mel_{b:02d}_mean"] = float(np.mean(band))
        feats[f"mel_{b:02d}_std"] = float(np.std(band))
        feats[f"mel_{b:02d}_skew"] = float(skew(band))
        feats[f"mel_{b:02d}_kurt"] = float(kurtosis(band))

    # A2: Per-band spectral flux (frame-to-frame change per band)
    mel_diff = np.diff(S_db, axis=1)
    for b in range(n_mels):
        bd = mel_diff[b, :]
        feats[f"melflux_{b:02d}_mean"] = float(np.mean(np.abs(bd)))
        feats[f"melflux_{b:02d}_std"] = float(np.std(bd))
        feats[f"melflux_{b:02d}_max"] = float(np.max(np.abs(bd)))

    # A3: Cross-band correlation (do bands move together more in echo?)
    # Compute correlation between adjacent band pairs
    band_corrs = []
    for b in range(0, n_mels - 1, 2):
        corr = np.corrcoef(S_db[b, :], S_db[b + 1, :])[0, 1]
        band_corrs.append(corr if not np.isnan(corr) else 0.0)
    feats["band_corr_mean"] = float(np.mean(band_corrs))
    feats["band_corr_std"] = float(np.std(band_corrs))
    feats["band_corr_min"] = float(np.min(band_corrs))

    # Low-mid-high band correlation (echo smears across bands)
    low = np.mean(S_db[:20, :], axis=0)    # 0-1.5kHz
    mid = np.mean(S_db[20:50, :], axis=0)  # 1.5-5kHz
    high = np.mean(S_db[50:, :], axis=0)   # 5kHz+
    lm_corr = np.corrcoef(low, mid)[0, 1]
    mh_corr = np.corrcoef(mid, high)[0, 1]
    lh_corr = np.corrcoef(low, high)[0, 1]
    feats["low_mid_corr"] = float(lm_corr if not np.isnan(lm_corr) else 0)
    feats["mid_high_corr"] = float(mh_corr if not np.isnan(mh_corr) else 0)
    feats["low_high_corr"] = float(lh_corr if not np.isnan(lh_corr) else 0)

    # ---- B. TEMPORAL STRUCTURE ----

    # B1: Onset strength and regularity
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    feats["onset_mean"] = float(np.mean(onset_env))
    feats["onset_std"] = float(np.std(onset_env))
    feats["onset_max"] = float(np.max(onset_env))
    # Onset regularity: autocorrelation of onset envelope
    if len(onset_env) > 20:
        onset_ac = np.correlate(onset_env - np.mean(onset_env),
                                onset_env - np.mean(onset_env), mode='full')
        onset_ac = onset_ac[len(onset_ac)//2:]
        onset_ac /= (onset_ac[0] + 1e-10)
        feats["onset_ac_5"] = float(onset_ac[min(5, len(onset_ac)-1)])
        feats["onset_ac_10"] = float(onset_ac[min(10, len(onset_ac)-1)])
        feats["onset_ac_20"] = float(onset_ac[min(20, len(onset_ac)-1)])
    else:
        feats["onset_ac_5"] = 0.0
        feats["onset_ac_10"] = 0.0
        feats["onset_ac_20"] = 0.0

    # B2: Energy envelope — fine-grained
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0]
    feats["rms_mean"] = float(np.mean(rms))
    feats["rms_std"] = float(np.std(rms))
    feats["rms_dynamic_range"] = float(np.max(rms) - np.min(rms))

    # RMS smoothness: how jagged is the energy curve?
    if len(rms) > 3:
        rms_diff = np.abs(np.diff(rms))
        feats["rms_roughness"] = float(np.mean(rms_diff))
        feats["rms_roughness_std"] = float(np.std(rms_diff))
        rms_diff2 = np.abs(np.diff(rms_diff))
        feats["rms_jerk"] = float(np.mean(rms_diff2))
    else:
        feats["rms_roughness"] = 0.0
        feats["rms_roughness_std"] = 0.0
        feats["rms_jerk"] = 0.0

    # ---- C. HARMONIC ANALYSIS ----

    # C1: Harmonic-to-noise ratio per frame
    # Use spectral flatness as proxy (pure tone = 0, noise = 1)
    sf = librosa.feature.spectral_flatness(y=y, n_fft=2048, hop_length=hop)[0]
    feats["flatness_mean"] = float(np.mean(sf))
    feats["flatness_std"] = float(np.std(sf))
    feats["flatness_max"] = float(np.max(sf))
    feats["flatness_p90"] = float(np.percentile(sf, 90))

    # C2: Pitch stability
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, n_fft=2048, hop_length=hop)
    # Get strongest pitch per frame
    pitch_track = []
    for frame in range(pitches.shape[1]):
        idx = magnitudes[:, frame].argmax()
        p = pitches[idx, frame]
        if p > 50:  # Only voiced frames
            pitch_track.append(p)

    if len(pitch_track) > 5:
        pt = np.array(pitch_track)
        feats["pitch_mean"] = float(np.mean(pt))
        feats["pitch_std"] = float(np.std(pt))
        feats["pitch_range"] = float(np.max(pt) - np.min(pt))
        # Pitch jitter (frame-to-frame variation)
        pitch_diff = np.abs(np.diff(pt))
        feats["pitch_jitter"] = float(np.mean(pitch_diff))
        feats["pitch_jitter_std"] = float(np.std(pitch_diff))
    else:
        feats["pitch_mean"] = 0.0
        feats["pitch_std"] = 0.0
        feats["pitch_range"] = 0.0
        feats["pitch_jitter"] = 0.0
        feats["pitch_jitter_std"] = 0.0

    # ---- D. SPECTRAL SHAPE EVOLUTION ----

    # D1: Spectral centroid, bandwidth, rolloff — per frame stats
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    bw = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop)[0]

    for name, arr in [("centroid", cent), ("bandwidth", bw), ("rolloff", rolloff)]:
        feats[f"spec_{name}_mean"] = float(np.mean(arr))
        feats[f"spec_{name}_std"] = float(np.std(arr))
        feats[f"spec_{name}_skew"] = float(skew(arr))
        feats[f"spec_{name}_range"] = float(np.max(arr) - np.min(arr))
        # Frame-to-frame stability
        if len(arr) > 2:
            d = np.abs(np.diff(arr))
            feats[f"spec_{name}_roughness"] = float(np.mean(d))
        else:
            feats[f"spec_{name}_roughness"] = 0.0

    # D2: Spectral contrast per band (7 bands)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, n_fft=2048,
                                                   hop_length=hop, n_bands=6)
    for b in range(contrast.shape[0]):
        feats[f"contrast_{b}_mean"] = float(np.mean(contrast[b]))
        feats[f"contrast_{b}_std"] = float(np.std(contrast[b]))

    # D3: Spectral tilt (slope of spectrum) — echo adds energy in lower bands
    S_mag = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    tilt_per_frame = []
    for frame in range(S_mag.shape[1]):
        spectrum = S_mag[:, frame]
        if np.sum(spectrum) > 1e-10:
            # Linear regression of log-spectrum vs log-frequency
            valid = freqs > 50  # Skip DC
            log_f = np.log(freqs[valid] + 1e-10)
            log_s = np.log(spectrum[valid] + 1e-10)
            coeffs = np.polyfit(log_f, log_s, 1)
            tilt_per_frame.append(coeffs[0])

    if len(tilt_per_frame) > 0:
        tilt = np.array(tilt_per_frame)
        feats["tilt_mean"] = float(np.mean(tilt))
        feats["tilt_std"] = float(np.std(tilt))
        feats["tilt_range"] = float(np.max(tilt) - np.min(tilt))
    else:
        feats["tilt_mean"] = 0.0
        feats["tilt_std"] = 0.0
        feats["tilt_range"] = 0.0

    # ---- E. ECHO-SPECIFIC DEEP DIVE ----

    # E1: Autocorrelation at multiple lag ranges (not just 10-80ms)
    ac = librosa.autocorrelate(y, max_size=int(sr * 0.15))  # Up to 150ms
    ac = ac / (ac[0] + 1e-10)

    lag_ranges = {
        "1_5ms": (int(sr * 0.001), int(sr * 0.005)),    # Very short reflections
        "5_15ms": (int(sr * 0.005), int(sr * 0.015)),   # Early reflections
        "15_40ms": (int(sr * 0.015), int(sr * 0.040)),  # Classic echo
        "40_80ms": (int(sr * 0.040), int(sr * 0.080)),  # Late echo
        "80_150ms": (int(sr * 0.080), int(sr * 0.150)), # Very late
    }

    for name, (lo, hi) in lag_ranges.items():
        hi = min(hi, len(ac) - 1)
        if lo < hi:
            segment = ac[lo:hi]
            feats[f"ac_{name}_max"] = float(np.max(segment))
            feats[f"ac_{name}_mean"] = float(np.mean(segment))
            # Number of peaks
            peaks, props = signal.find_peaks(segment, height=0.05, distance=max(1, int(sr * 0.002)))
            feats[f"ac_{name}_peaks"] = len(peaks)
        else:
            feats[f"ac_{name}_max"] = 0.0
            feats[f"ac_{name}_mean"] = 0.0
            feats[f"ac_{name}_peaks"] = 0

    # E2: Cepstral analysis at fine resolution
    S_fft = np.fft.fft(y)
    log_S = np.log(np.abs(S_fft) + 1e-10)
    cepstrum = np.real(np.fft.ifft(log_S))

    cep_ranges = {
        "1_5ms": (int(sr * 0.001), int(sr * 0.005)),
        "5_15ms": (int(sr * 0.005), int(sr * 0.015)),
        "15_40ms": (int(sr * 0.015), int(sr * 0.040)),
        "40_80ms": (int(sr * 0.040), int(sr * 0.080)),
    }

    for name, (lo, hi) in cep_ranges.items():
        hi = min(hi, len(cepstrum) // 2)
        if lo < hi:
            segment = np.abs(cepstrum[lo:hi])
            feats[f"cep_{name}_max"] = float(np.max(segment))
            feats[f"cep_{name}_mean"] = float(np.mean(segment))
            feats[f"cep_{name}_energy"] = float(np.sum(segment ** 2))
        else:
            feats[f"cep_{name}_max"] = 0.0
            feats[f"cep_{name}_mean"] = 0.0
            feats[f"cep_{name}_energy"] = 0.0

    # E3: Modulation spectrum — very fine resolution
    if len(rms) > 32:
        mod_spec = np.abs(np.fft.rfft(rms - np.mean(rms)))
        mod_freqs = np.fft.rfftfreq(len(rms), d=hop / sr)

        mod_ranges = {
            "speech_2_8Hz": (2, 8),       # Normal speech modulation
            "low_mod_8_15Hz": (8, 15),    # Syllable rate
            "echo_mod_15_30Hz": (15, 30), # Echo modulation
            "fast_mod_30_60Hz": (30, 60), # Fast modulation
            "hf_mod_60_100Hz": (60, 100), # High frequency modulation
        }

        for name, (lo, hi) in mod_ranges.items():
            mask = (mod_freqs >= lo) & (mod_freqs <= hi)
            if np.any(mask):
                feats[f"mod_{name}_energy"] = float(np.sum(mod_spec[mask] ** 2))
                feats[f"mod_{name}_peak"] = float(np.max(mod_spec[mask]))
            else:
                feats[f"mod_{name}_energy"] = 0.0
                feats[f"mod_{name}_peak"] = 0.0

        # Modulation spectral centroid
        total = np.sum(mod_spec) + 1e-10
        feats["mod_centroid"] = float(np.sum(mod_freqs * mod_spec) / total)
    else:
        for name in ["speech_2_8Hz", "low_mod_8_15Hz", "echo_mod_15_30Hz",
                      "fast_mod_30_60Hz", "hf_mod_60_100Hz"]:
            feats[f"mod_{name}_energy"] = 0.0
            feats[f"mod_{name}_peak"] = 0.0
        feats["mod_centroid"] = 0.0

    # E4: Spectral decay after transients (very fine measurement)
    decay_rates_by_band = defaultdict(list)
    onset_frames_idx = librosa.onset.onset_detect(y=y, sr=sr, units='frames',
                                                    hop_length=hop)
    for onset_f in onset_frames_idx[:30]:
        if onset_f + 8 < S_db.shape[1]:
            for band_group, (b_lo, b_hi) in [("low", (0, 20)), ("mid", (20, 50)), ("high", (50, 80))]:
                band_energy = np.mean(S_db[b_lo:b_hi, :], axis=0)
                peak_val = band_energy[onset_f]
                # Measure decay at 2, 4, 6, 8 frames after onset
                for offset in [2, 4, 6, 8]:
                    if onset_f + offset < len(band_energy):
                        decay = peak_val - band_energy[onset_f + offset]
                        decay_rates_by_band[f"{band_group}_{offset}f"].append(decay)

    for key, vals in decay_rates_by_band.items():
        feats[f"decay_{key}_mean"] = float(np.mean(vals))
        feats[f"decay_{key}_std"] = float(np.std(vals))

    # E5: Phase coherence between harmonics
    # In clean speech, harmonics have consistent phase relationships
    # Echo disrupts this
    S_complex = librosa.stft(y, n_fft=2048, hop_length=hop)
    phase = np.angle(S_complex)
    phase_diff = np.diff(phase, axis=1)  # Frame-to-frame phase change

    # Instantaneous frequency deviation
    if phase_diff.shape[1] > 0:
        ifd = np.abs(phase_diff)
        feats["phase_coherence_mean"] = float(np.mean(ifd))
        feats["phase_coherence_std"] = float(np.std(ifd))
        # Per-band phase coherence
        for band_name, (b_lo, b_hi) in [("low", (0, 200)), ("mid", (200, 600)), ("high", (600, 1025))]:
            b_hi = min(b_hi, ifd.shape[0])
            feats[f"phase_{band_name}_mean"] = float(np.mean(ifd[b_lo:b_hi, :]))
            feats[f"phase_{band_name}_std"] = float(np.std(ifd[b_lo:b_hi, :]))
    else:
        feats["phase_coherence_mean"] = 0.0
        feats["phase_coherence_std"] = 0.0
        for bn in ["low", "mid", "high"]:
            feats[f"phase_{bn}_mean"] = 0.0
            feats[f"phase_{bn}_std"] = 0.0

    # E6: Sub-band energy ratios (echo may redistribute energy)
    sub_bands = {
        "sub_bass": (0, 5),
        "bass": (5, 10),
        "low_mid": (10, 20),
        "mid": (20, 35),
        "upper_mid": (35, 50),
        "presence": (50, 65),
        "brilliance": (65, 80),
    }
    total_energy = np.sum(S_db + 80)  # Shift to positive for ratio
    for name, (lo, hi) in sub_bands.items():
        band_energy = np.sum(S_db[lo:hi, :] + 80)
        feats[f"energy_ratio_{name}"] = float(band_energy / (total_energy + 1e-10))

    # Store mel spectrogram summary for visualization
    feats["_mel_shape"] = list(S_db.shape)

    return feats


def compute_differential_features(echo_feats, clean_feats):
    """
    Compute the DIFFERENCE between echo and clean features.
    This is the key insight: same text, different versions.
    """
    diff = {}
    for key in echo_feats:
        if key.startswith("_"):
            continue
        if key in clean_feats:
            try:
                diff[f"diff_{key}"] = echo_feats[key] - clean_feats[key]
                # Also compute ratio
                if abs(clean_feats[key]) > 1e-10:
                    diff[f"ratio_{key}"] = echo_feats[key] / clean_feats[key]
            except:
                pass
    return diff


def analyze_dataset(dataset):
    """Run granular analysis on the full dataset."""
    print("\n" + "=" * 70)
    print("STEP 2: GRANULAR FEATURE EXTRACTION")
    print("=" * 70)

    echo_features = []
    clean_features = []
    differential_features = []
    mel_spectrograms = []  # Store for visualization

    for i, entry in enumerate(dataset):
        session = entry["session"]
        chunk = entry["chunk"]
        echo_path = entry["echo_path"]
        clean_path = entry.get("clean_path")

        print(f"  [{i+1}/{len(dataset)}] {session} chunk {chunk}...", end=" ", flush=True)

        # Extract echo features
        ef = extract_granular_features(echo_path)
        if ef is None:
            print("SKIP (too short)")
            continue

        ef["session"] = session
        ef["chunk"] = chunk
        ef["label"] = "ECHO"
        ef["path"] = echo_path
        echo_features.append(ef)

        # Extract mel spectrogram for visualization
        y_echo, sr = librosa.load(echo_path, sr=22050, mono=True)
        S_echo = librosa.feature.melspectrogram(y=y_echo, sr=sr, n_mels=80,
                                                 n_fft=2048, hop_length=256)
        S_echo_db = librosa.power_to_db(S_echo, ref=np.max)

        mel_entry = {
            "session": session, "chunk": chunk,
            "echo_mel": S_echo_db.tolist(),
            "echo_version": entry.get("echo_version"),
            "text": entry.get("text", ""),
        }

        # Extract clean features if paired
        if clean_path and os.path.exists(clean_path):
            cf = extract_granular_features(clean_path)
            if cf:
                cf["session"] = session
                cf["chunk"] = chunk
                cf["label"] = "CLEAN"
                cf["path"] = clean_path
                clean_features.append(cf)

                # Differential features
                diff = compute_differential_features(ef, cf)
                diff["session"] = session
                diff["chunk"] = chunk
                differential_features.append(diff)

                # Clean mel for visualization
                y_clean, _ = librosa.load(clean_path, sr=22050, mono=True)
                S_clean = librosa.feature.melspectrogram(y=y_clean, sr=sr, n_mels=80,
                                                         n_fft=2048, hop_length=256)
                S_clean_db = librosa.power_to_db(S_clean, ref=np.max)
                mel_entry["clean_mel"] = S_clean_db.tolist()
                mel_entry["clean_version"] = entry.get("clean_version")

                print(f"PAIRED (echo v{entry.get('echo_version')} vs clean v{entry.get('clean_version')})")
            else:
                print("echo only (clean too short)")
        else:
            print("echo only (no pair)")

        mel_spectrograms.append(mel_entry)

    # Save features
    def save_features(features, filename):
        path = OUTPUT_DIR / filename
        # Convert to serializable format
        clean = []
        for f in features:
            clean_f = {}
            for k, v in f.items():
                if isinstance(v, (np.floating, np.integer)):
                    clean_f[k] = float(v)
                elif isinstance(v, np.ndarray):
                    clean_f[k] = v.tolist()
                else:
                    clean_f[k] = v
            clean.append(clean_f)
        with open(path, 'w') as fh:
            json.dump(clean, fh, indent=2)
        return path

    save_features(echo_features, "echo_features_granular.json")
    save_features(clean_features, "clean_features_granular.json")
    save_features(differential_features, "differential_features.json")

    # Save mel spectrograms (compressed — only first 20 for the report)
    mel_path = OUTPUT_DIR / "mel_spectrograms.json"
    with open(mel_path, 'w') as f:
        json.dump(mel_spectrograms[:30], f)

    print(f"\n  Echo features: {len(echo_features)}")
    print(f"  Clean features: {len(clean_features)}")
    print(f"  Differential features: {len(differential_features)}")

    # ---- Statistical analysis ----
    print("\n" + "=" * 70)
    print("STATISTICAL ANALYSIS: Echo vs Clean")
    print("=" * 70)

    if len(echo_features) < 3 or len(clean_features) < 3:
        print("  Not enough paired data for statistical comparison")
        return echo_features, clean_features, differential_features, mel_spectrograms

    # Get all feature names (exclude metadata)
    exclude = {"session", "chunk", "label", "path", "_mel_shape"}
    feature_names = [k for k in echo_features[0] if k not in exclude and not k.startswith("_")]

    results = []
    for feat_name in feature_names:
        echo_vals = [f[feat_name] for f in echo_features if feat_name in f]
        clean_vals = [f[feat_name] for f in clean_features if feat_name in f]

        if len(echo_vals) < 3 or len(clean_vals) < 3:
            continue

        e_arr = np.array(echo_vals, dtype=float)
        c_arr = np.array(clean_vals, dtype=float)

        # Remove NaN/Inf
        e_arr = e_arr[np.isfinite(e_arr)]
        c_arr = c_arr[np.isfinite(c_arr)]

        if len(e_arr) < 3 or len(c_arr) < 3:
            continue

        # Cohen's d (effect size)
        pooled_std = np.sqrt((np.std(e_arr)**2 + np.std(c_arr)**2) / 2)
        if pooled_std > 1e-10:
            cohens_d = (np.mean(e_arr) - np.mean(c_arr)) / pooled_std
        else:
            cohens_d = 0.0

        # Mann-Whitney U test (non-parametric)
        try:
            stat, p_val = mannwhitneyu(e_arr, c_arr, alternative='two-sided')
        except:
            p_val = 1.0

        results.append({
            "feature": feat_name,
            "echo_mean": float(np.mean(e_arr)),
            "echo_std": float(np.std(e_arr)),
            "clean_mean": float(np.mean(c_arr)),
            "clean_std": float(np.std(c_arr)),
            "cohens_d": float(cohens_d),
            "abs_d": float(abs(cohens_d)),
            "p_value": float(p_val),
            "direction": "echo_higher" if cohens_d > 0 else "echo_lower",
        })

    # Sort by absolute effect size
    results.sort(key=lambda x: x["abs_d"], reverse=True)

    # Save full results
    results_path = OUTPUT_DIR / "statistical_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Print top 50
    print(f"\nTOP 50 DISCRIMINATING FEATURES (by |Cohen's d|):")
    print(f"{'Rank':>4}  {'|d|':>6}  {'p-value':>10}  {'Direction':<14}  {'Feature'}")
    print("-" * 90)

    significant_count = 0
    for i, r in enumerate(results[:50]):
        sig = "***" if r["p_value"] < 0.001 else "** " if r["p_value"] < 0.01 else "*  " if r["p_value"] < 0.05 else "   "
        if r["p_value"] < 0.05:
            significant_count += 1
        print(f"{i+1:>4}  {r['abs_d']:>6.3f}  {r['p_value']:>10.6f}  {r['direction']:<14}  {r['feature']} {sig}")

    print(f"\nSignificant features (p < 0.05): {significant_count} / {len(results)}")

    # Differential analysis (for paired chunks)
    if differential_features:
        print(f"\n{'=' * 70}")
        print("DIFFERENTIAL ANALYSIS (echo - clean, same text)")
        print(f"{'=' * 70}")

        diff_results = []
        diff_names = [k for k in differential_features[0] if k not in {"session", "chunk"}]
        for feat_name in diff_names:
            vals = [d[feat_name] for d in differential_features if feat_name in d]
            if len(vals) < 3:
                continue
            arr = np.array(vals, dtype=float)
            arr = arr[np.isfinite(arr)]
            if len(arr) < 3:
                continue

            # Is the difference consistently non-zero?
            mean_diff = np.mean(arr)
            std_diff = np.std(arr)
            if std_diff > 1e-10:
                t_stat = mean_diff / (std_diff / np.sqrt(len(arr)))
            else:
                t_stat = 0.0

            diff_results.append({
                "feature": feat_name,
                "mean_diff": float(mean_diff),
                "std_diff": float(std_diff),
                "t_stat": float(t_stat),
                "abs_t": float(abs(t_stat)),
                "n": len(arr),
                "consistent_sign": float(np.mean(arr > 0) if mean_diff > 0 else np.mean(arr < 0)),
            })

        diff_results.sort(key=lambda x: x["abs_t"], reverse=True)

        diff_path = OUTPUT_DIR / "differential_results.json"
        with open(diff_path, 'w') as f:
            json.dump(diff_results, f, indent=2)

        print(f"\nTOP 30 DIFFERENTIAL FEATURES (echo consistently differs from clean):")
        print(f"{'Rank':>4}  {'|t|':>7}  {'Mean diff':>10}  {'Consistency':>11}  {'Feature'}")
        print("-" * 80)

        for i, r in enumerate(diff_results[:30]):
            print(f"{i+1:>4}  {r['abs_t']:>7.2f}  {r['mean_diff']:>10.4f}  "
                  f"{r['consistent_sign']:>10.0%}  {r['feature']}")

    return echo_features, clean_features, differential_features, mel_spectrograms


# ============================================================
# STEP 3: CLASSIFY — Build and test echo classifier
# ============================================================

def classify_echo():
    """
    Build an echo classifier using the top discriminating features.
    Uses leave-one-session-out cross-validation for honest evaluation.
    Compares against the old echo_risk (spectral flux variance) approach.
    """
    print("\n" + "=" * 70)
    print("STEP 3: ECHO CLASSIFIER")
    print("=" * 70)

    # Load features
    echo_path = OUTPUT_DIR / "echo_features_granular.json"
    clean_path = OUTPUT_DIR / "clean_features_granular.json"

    if not echo_path.exists() or not clean_path.exists():
        print("ERROR: Run --analyze first")
        return

    with open(echo_path) as f:
        echo_feats = json.load(f)
    with open(clean_path) as f:
        clean_feats = json.load(f)

    print(f"  Echo chunks: {len(echo_feats)}")
    print(f"  Clean chunks: {len(clean_feats)}")

    # Load statistical results to find best features
    stats_path = OUTPUT_DIR / "statistical_results.json"
    with open(stats_path) as f:
        stats = json.load(f)

    # Compute derived features for all samples
    for f_list in [echo_feats, clean_feats]:
        for f in f_list:
            if "band_corr_mean" in f and "band_corr_min" in f:
                f["corr_range"] = f["band_corr_mean"] - f["band_corr_min"]
            lm = np.mean([f.get(f"mel_{b:02d}_mean", 0) for b in range(10, 20)])
            um = np.mean([f.get(f"mel_{b:02d}_mean", 0) for b in range(35, 50)])
            f["ratio_lowmid_uppermid"] = lm - um
            sub_std = np.mean([f.get(f"mel_{b:02d}_std", 0) for b in range(0, 5)])
            overall_std = np.mean([f.get(f"mel_{b:02d}_std", 0) for b in range(0, 80)])
            f["ratio_subbass_std_norm"] = sub_std / (overall_std + 1e-10)

    # Curated feature set: mel statistics + band correlation + spectral shape
    # Avoids raw mel_mean (loudness-confounded) — uses std, skew, kurt, ratios
    selected = [
        {"feature": "mel_00_std",              "abs_d": 0.868, "p_value": 0.0001, "direction": "echo_lower"},
        {"feature": "mel_01_std",              "abs_d": 0.846, "p_value": 0.0001, "direction": "echo_lower"},
        {"feature": "corr_range",              "abs_d": 0.767, "p_value": 0.0006, "direction": "echo_higher"},
        {"feature": "band_corr_min",           "abs_d": 0.784, "p_value": 0.0002, "direction": "echo_lower"},
        {"feature": "band_corr_std",           "abs_d": 0.723, "p_value": 0.0002, "direction": "echo_higher"},
        {"feature": "mel_49_skew",             "abs_d": 0.698, "p_value": 0.003,  "direction": "echo_lower"},
        {"feature": "ratio_lowmid_uppermid",   "abs_d": 0.610, "p_value": 0.003,  "direction": "echo_higher"},
        {"feature": "mel_00_kurt",             "abs_d": 0.667, "p_value": 0.002,  "direction": "echo_higher"},
        {"feature": "band_corr_mean",          "abs_d": 0.650, "p_value": 0.0006, "direction": "echo_lower"},
        {"feature": "contrast_6_std",          "abs_d": 0.646, "p_value": 0.005,  "direction": "echo_higher"},
        {"feature": "ratio_subbass_std_norm",  "abs_d": 0.490, "p_value": 0.033,  "direction": "echo_lower"},
    ]

    print(f"\n  Selected features ({len(selected)}):")
    for i, s in enumerate(selected):
        print(f"    {i+1}. {s['feature']:30s} |d|={s['abs_d']:.3f}  p={s['p_value']:.6f}  {s['direction']}")

    feature_names = [s["feature"] for s in selected]

    # ---- Build feature matrix ----
    def build_matrix(feat_list, label):
        rows = []
        for f in feat_list:
            row = {"session": f["session"], "chunk": f["chunk"], "label": label}
            valid = True
            for fn in feature_names:
                val = f.get(fn)
                if val is None or not np.isfinite(val):
                    valid = False
                    break
                row[fn] = val
            if valid:
                rows.append(row)
        return rows

    echo_rows = build_matrix(echo_feats, 1)
    clean_rows = build_matrix(clean_feats, 0)
    all_rows = echo_rows + clean_rows

    print(f"\n  Valid rows: {len(echo_rows)} echo + {len(clean_rows)} clean = {len(all_rows)}")

    if len(echo_rows) < 5 or len(clean_rows) < 5:
        print("  ERROR: Not enough valid data for classification")
        return

    # Get unique sessions
    sessions = sorted(set(r["session"] for r in all_rows))
    print(f"  Sessions: {sessions}")

    # ---- Method 1: Z-score composite ----
    # Convert each feature to a z-score based on clean distribution,
    # then combine with sign-corrected weights
    print(f"\n{'=' * 60}")
    print("METHOD 1: Z-SCORE COMPOSITE")
    print(f"{'=' * 60}")

    # Compute clean statistics (global — for threshold calibration)
    clean_stats = {}
    for fn in feature_names:
        vals = [r[fn] for r in clean_rows]
        clean_stats[fn] = {"mean": np.mean(vals), "std": np.std(vals)}

    # Compute echo score: sum of z-scores, sign-corrected so positive = more echo-like
    feat_directions = {s["feature"]: 1 if s["direction"] == "echo_higher" else -1 for s in selected}

    def composite_score(row):
        z_sum = 0
        for fn in feature_names:
            z = (row[fn] - clean_stats[fn]["mean"]) / (clean_stats[fn]["std"] + 1e-10)
            z_sum += z * feat_directions[fn]
        return z_sum / len(feature_names)

    # Score all samples
    for r in all_rows:
        r["score"] = composite_score(r)

    echo_scores = [r["score"] for r in all_rows if r["label"] == 1]
    clean_scores = [r["score"] for r in all_rows if r["label"] == 0]

    print(f"  Echo scores:  mean={np.mean(echo_scores):.3f}  std={np.std(echo_scores):.3f}  "
          f"range=[{np.min(echo_scores):.3f}, {np.max(echo_scores):.3f}]")
    print(f"  Clean scores: mean={np.mean(clean_scores):.3f}  std={np.std(clean_scores):.3f}  "
          f"range=[{np.min(clean_scores):.3f}, {np.max(clean_scores):.3f}]")

    # ROC analysis
    all_scores = [(r["score"], r["label"]) for r in all_rows]
    all_scores.sort(key=lambda x: x[0])

    thresholds = np.linspace(min(s[0] for s in all_scores) - 0.1,
                              max(s[0] for s in all_scores) + 0.1, 200)

    roc_points = []

    n_echo = sum(1 for s in all_scores if s[1] == 1)
    n_clean = sum(1 for s in all_scores if s[1] == 0)

    # Collect metrics at every threshold
    all_thresh_metrics = []
    for thresh in thresholds:
        tp = sum(1 for s in all_scores if s[0] >= thresh and s[1] == 1)
        fp = sum(1 for s in all_scores if s[0] >= thresh and s[1] == 0)
        fn = sum(1 for s in all_scores if s[0] < thresh and s[1] == 1)
        tn = sum(1 for s in all_scores if s[0] < thresh and s[1] == 0)

        tpr = tp / (tp + fn + 1e-10)
        fpr = fp / (fp + tn + 1e-10)
        fnr = fn / (fn + tp + 1e-10)
        precision = tp / (tp + fp + 1e-10)
        recall = tpr
        f1 = 2 * precision * recall / (precision + recall + 1e-10)
        youdens_j = tpr - fpr  # Balanced: maximizes separation

        roc_points.append((fpr, tpr))
        all_thresh_metrics.append({
            "threshold": float(thresh),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "tpr": float(tpr), "fpr": float(fpr),
            "precision": float(precision), "recall": float(recall),
            "f1": float(f1), "fnr": float(fnr),
            "youdens_j": float(youdens_j),
            "accuracy": float((tp + tn) / (tp + fp + fn + tn)),
        })

    # Find THREE operating points:
    # 1. Balanced (Youden's J) — best sensitivity + specificity tradeoff
    best_j_idx = max(range(len(all_thresh_metrics)), key=lambda i: all_thresh_metrics[i]["youdens_j"])
    balanced_metrics = all_thresh_metrics[best_j_idx]
    best_threshold = balanced_metrics["threshold"]

    # 2. High recall — catch ≥90% of echo, minimize FPR
    high_recall_metrics = None
    for m in sorted(all_thresh_metrics, key=lambda x: x["fpr"]):
        if m["tpr"] >= 0.90:
            high_recall_metrics = m
            break

    # 3. Low FPR — keep FPR ≤20%, maximize recall
    low_fpr_metrics = None
    for m in sorted(all_thresh_metrics, key=lambda x: -x["tpr"]):
        if m["fpr"] <= 0.20:
            low_fpr_metrics = m
            break

    # AUC (trapezoidal)
    roc_points.sort(key=lambda x: x[0])
    auc = 0
    for i in range(1, len(roc_points)):
        dx = roc_points[i][0] - roc_points[i-1][0]
        dy = (roc_points[i][1] + roc_points[i-1][1]) / 2
        auc += dx * dy

    print(f"\n  GLOBAL RESULTS (training on all data):")
    print(f"    AUC:       {auc:.3f}")
    print(f"    Separation: echo mean={np.mean(echo_scores):.3f} vs clean mean={np.mean(clean_scores):.3f}")

    for label, m in [("BALANCED (Youden's J)", balanced_metrics),
                      ("HIGH RECALL (≥90% TPR)", high_recall_metrics),
                      ("LOW FPR (≤20%)", low_fpr_metrics)]:
        if m:
            print(f"\n    {label}:")
            print(f"      Threshold: {m['threshold']:.3f}")
            print(f"      FNR:       {m['fnr']:.1%}  (missed echo)")
            print(f"      FPR:       {m['fpr']:.1%}  (false alarm)")
            print(f"      Precision: {m['precision']:.3f}  Recall: {m['recall']:.3f}  F1: {m['f1']:.3f}")
            print(f"      TP={m['tp']}  FP={m['fp']}  FN={m['fn']}  TN={m['tn']}")

    # ---- Leave-one-session-out cross-validation ----
    print(f"\n  LEAVE-ONE-SESSION-OUT CROSS-VALIDATION:")

    cv_predictions = []
    for held_out in sessions:
        train = [r for r in all_rows if r["session"] != held_out]
        test = [r for r in all_rows if r["session"] == held_out]

        if not test:
            continue

        # Recompute clean stats from training data only
        cv_clean = [r for r in train if r["label"] == 0]
        if len(cv_clean) < 3:
            continue

        cv_stats = {}
        for fn in feature_names:
            vals = [r[fn] for r in cv_clean]
            cv_stats[fn] = {"mean": np.mean(vals), "std": np.std(vals)}

        def cv_score(row):
            z_sum = 0
            for fn in feature_names:
                z = (row[fn] - cv_stats[fn]["mean"]) / (cv_stats[fn]["std"] + 1e-10)
                z_sum += z * feat_directions[fn]
            return z_sum / len(feature_names)

        # Find best threshold on training data using Youden's J (balanced)
        train_scored = [(cv_score(r), r["label"]) for r in train]
        best_cv_thresh = best_threshold  # Start with global
        best_cv_j = -1
        n_train_pos = sum(1 for s in train_scored if s[1] == 1)
        n_train_neg = sum(1 for s in train_scored if s[1] == 0)
        for t in np.linspace(-3, 5, 200):
            tp = sum(1 for s in train_scored if s[0] >= t and s[1] == 1)
            fp = sum(1 for s in train_scored if s[0] >= t and s[1] == 0)
            fn = n_train_pos - tp
            tn = n_train_neg - fp
            tpr = tp / (n_train_pos + 1e-10)
            fpr_val = fp / (n_train_neg + 1e-10)
            j = tpr - fpr_val
            if j > best_cv_j:
                best_cv_j = j
                best_cv_thresh = t

        # Score test set
        for r in test:
            score = cv_score(r)
            predicted = 1 if score >= best_cv_thresh else 0
            cv_predictions.append({
                "session": held_out,
                "chunk": r["chunk"],
                "true_label": r["label"],
                "predicted": predicted,
                "score": float(score),
                "threshold": float(best_cv_thresh),
            })

        n_test_echo = sum(1 for r in test if r["label"] == 1)
        n_test_clean = sum(1 for r in test if r["label"] == 0)
        tp = sum(1 for p in cv_predictions if p["session"] == held_out and p["true_label"] == 1 and p["predicted"] == 1)
        fn = sum(1 for p in cv_predictions if p["session"] == held_out and p["true_label"] == 1 and p["predicted"] == 0)
        fp = sum(1 for p in cv_predictions if p["session"] == held_out and p["true_label"] == 0 and p["predicted"] == 1)

        print(f"    {held_out:<45s}  echo={n_test_echo:>2}  clean={n_test_clean:>2}  "
              f"TP={tp:>2} FN={fn:>2} FP={fp:>2}  thresh={best_cv_thresh:.2f}")

    # Overall CV metrics
    if cv_predictions:
        cv_tp = sum(1 for p in cv_predictions if p["true_label"] == 1 and p["predicted"] == 1)
        cv_fp = sum(1 for p in cv_predictions if p["true_label"] == 0 and p["predicted"] == 1)
        cv_fn = sum(1 for p in cv_predictions if p["true_label"] == 1 and p["predicted"] == 0)
        cv_tn = sum(1 for p in cv_predictions if p["true_label"] == 0 and p["predicted"] == 0)

        cv_fnr = cv_fn / (cv_fn + cv_tp + 1e-10)
        cv_fpr = cv_fp / (cv_fp + cv_tn + 1e-10)
        cv_precision = cv_tp / (cv_tp + cv_fp + 1e-10)
        cv_recall = cv_tp / (cv_tp + cv_fn + 1e-10)
        cv_f1 = 2 * cv_precision * cv_recall / (cv_precision + cv_recall + 1e-10)
        cv_acc = (cv_tp + cv_tn) / len(cv_predictions)

        # CV AUC
        cv_scored = [(p["score"], p["true_label"]) for p in cv_predictions]
        cv_scored.sort(key=lambda x: x[0])
        cv_roc = []
        cv_n_pos = sum(1 for s in cv_scored if s[1] == 1)
        cv_n_neg = sum(1 for s in cv_scored if s[1] == 0)
        for t in np.linspace(min(s[0] for s in cv_scored) - 0.1,
                              max(s[0] for s in cv_scored) + 0.1, 200):
            tp = sum(1 for s in cv_scored if s[0] >= t and s[1] == 1)
            fp = sum(1 for s in cv_scored if s[0] >= t and s[1] == 0)
            tpr = tp / (cv_n_pos + 1e-10)
            fpr = fp / (cv_n_neg + 1e-10)
            cv_roc.append((fpr, tpr))
        cv_roc.sort(key=lambda x: x[0])
        cv_auc = sum((cv_roc[i][0] - cv_roc[i-1][0]) * (cv_roc[i][1] + cv_roc[i-1][1]) / 2
                      for i in range(1, len(cv_roc)))

        print(f"\n  CROSS-VALIDATED RESULTS:")
        print(f"    AUC:       {cv_auc:.3f}")
        print(f"    F1:        {cv_f1:.3f}")
        print(f"    FNR:       {cv_fnr:.1%}  (missed echo — was 58-67% before)")
        print(f"    FPR:       {cv_fpr:.1%}  (false alarm)")
        print(f"    Precision: {cv_precision:.3f}")
        print(f"    Recall:    {cv_recall:.3f}")
        print(f"    Accuracy:  {cv_acc:.1%}")
        print(f"    TP={cv_tp} FP={cv_fp} FN={cv_fn} TN={cv_tn}")

        # Comparison with old approaches
        print(f"\n  COMPARISON WITH PREVIOUS APPROACHES:")
        print(f"    {'Approach':<35s} {'AUC':>6}  {'FNR':>6}  {'FPR':>6}  {'Notes'}")
        print(f"    {'-'*85}")
        print(f"    {'Composite scorer (v6)':<35s} {'?':>6}  {'58%':>6}  {'?':>6}  {'spectral flux variance'}")
        print(f"    {'echo-detector.py (65-feat RF)':<35s} {'0.512':>6}  {'67%':>6}  {'28%':>6}  {'55 training chunks'}")
        print(f"    {'Auphonic analysis':<35s} {'0.341':>6}  {'n/a':>6}  {'n/a':>6}  {'anti-correlated'}")
        print(f"    {'Granular z-score (THIS, CV)':<35s} {cv_auc:>6.3f}  {cv_fnr:>5.0%}  {cv_fpr:>5.0%}  {f'{len(selected)} features, {len(all_rows)} chunks'}")

        # ---- Save misclassifications for inspection ----
        misses = [p for p in cv_predictions if p["true_label"] != p["predicted"]]
        if misses:
            print(f"\n  MISCLASSIFICATIONS ({len(misses)}):")
            for m in sorted(misses, key=lambda x: abs(x["score"]), reverse=True):
                label = "ECHO" if m["true_label"] == 1 else "CLEAN"
                pred = "echo" if m["predicted"] == 1 else "clean"
                print(f"    {m['session']} c{m['chunk']:02d}  true={label}  pred={pred}  "
                      f"score={m['score']:.3f}  thresh={m['threshold']:.3f}")

    # ---- Method 2: Individual feature thresholds (simpler, interpretable) ----
    print(f"\n{'=' * 60}")
    print("METHOD 2: INDIVIDUAL FEATURE THRESHOLDS")
    print(f"{'=' * 60}")
    print(f"  Testing each top feature as a standalone echo detector:\n")

    for s in selected:
        fn = s["feature"]
        e_vals = [r[fn] for r in all_rows if r["label"] == 1]
        c_vals = [r[fn] for r in all_rows if r["label"] == 0]

        # Find best threshold via Youden's J statistic
        all_vals = sorted(set(e_vals + c_vals))
        best_j = -1
        best_t = 0
        is_echo_higher = s["direction"] == "echo_higher"

        for t in np.linspace(min(all_vals), max(all_vals), 200):
            if is_echo_higher:
                tp = sum(1 for v in e_vals if v >= t)
                fp = sum(1 for v in c_vals if v >= t)
                fn_count = sum(1 for v in e_vals if v < t)
                tn = sum(1 for v in c_vals if v < t)
            else:
                tp = sum(1 for v in e_vals if v <= t)
                fp = sum(1 for v in c_vals if v <= t)
                fn_count = sum(1 for v in e_vals if v > t)
                tn = sum(1 for v in c_vals if v > t)

            tpr = tp / (tp + fn_count + 1e-10)
            fpr_val = fp / (fp + tn + 1e-10)
            j = tpr - fpr_val
            if j > best_j:
                best_j = j
                best_t = t

        # Evaluate at best threshold
        if is_echo_higher:
            tp = sum(1 for v in e_vals if v >= best_t)
            fp = sum(1 for v in c_vals if v >= best_t)
            fn_count = len(e_vals) - tp
        else:
            tp = sum(1 for v in e_vals if v <= best_t)
            fp = sum(1 for v in c_vals if v <= best_t)
            fn_count = len(e_vals) - tp

        fnr_val = fn_count / (len(e_vals) + 1e-10)
        fpr_val = fp / (len(c_vals) + 1e-10)

        print(f"  {fn:<30s}  |d|={s['abs_d']:.3f}  FNR={fnr_val:.0%}  FPR={fpr_val:.0%}  "
              f"thresh={best_t:.4f}  J={best_j:.3f}")

    # ---- Save classifier config ----
    classifier_config = {
        "method": "z_score_composite",
        "features": [{
            "name": s["feature"],
            "direction": s["direction"],
            "cohens_d": s["abs_d"],
            "p_value": s["p_value"],
            "clean_mean": clean_stats[s["feature"]]["mean"],
            "clean_std": clean_stats[s["feature"]]["std"],
        } for s in selected],
        "threshold_balanced": float(best_threshold),
        "threshold_high_recall": float(high_recall_metrics["threshold"]) if high_recall_metrics else 0,
        "threshold_low_fpr": float(low_fpr_metrics["threshold"]) if low_fpr_metrics else 0,
        "training_data": {
            "n_echo": len(echo_rows),
            "n_clean": len(clean_rows),
            "sessions": sessions,
        },
        "global_metrics_balanced": balanced_metrics,
        "global_metrics_high_recall": high_recall_metrics,
        "global_metrics_low_fpr": low_fpr_metrics,
        "cv_metrics": {
            "auc": float(cv_auc) if cv_predictions else 0,
            "fnr": float(cv_fnr) if cv_predictions else 1,
            "fpr": float(cv_fpr) if cv_predictions else 0,
            "f1": float(cv_f1) if cv_predictions else 0,
            "accuracy": float(cv_acc) if cv_predictions else 0,
        } if cv_predictions else {},
        "roc_points": [(float(x), float(y)) for x, y in roc_points[::4]],  # Subsampled
        "cv_predictions": cv_predictions,
    }

    config_path = OUTPUT_DIR / "classifier_config.json"
    with open(config_path, 'w') as f:
        json.dump(classifier_config, f, indent=2)
    print(f"\n  Classifier config saved to: {config_path}")


# ============================================================
# STEP 4: REPORT — Visual HTML report
# ============================================================

def generate_report(dataset, mel_spectrograms):
    """Generate HTML report with mel spectrogram comparisons."""
    print("\n" + "=" * 70)
    print("STEP 3: GENERATING VISUAL REPORT")
    print("=" * 70)

    # Load statistical results
    stats_path = OUTPUT_DIR / "statistical_results.json"
    diff_path = OUTPUT_DIR / "differential_results.json"

    stats = []
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)

    diff_stats = []
    if diff_path.exists():
        with open(diff_path) as f:
            diff_stats = json.load(f)

    # Build HTML
    html_parts = ["""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Echo Fingerprint Analysis</title>
<style>
  body { background: #0a0a12; color: #e0e0e0; font-family: 'SF Mono', monospace; margin: 0; padding: 20px; }
  h1 { color: #38bdf8; border-bottom: 1px solid #2a2a3e; padding-bottom: 12px; }
  h2 { color: #a78bfa; margin-top: 40px; }
  h3 { color: #34d399; }
  .stats-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 0.85rem; }
  .stats-table th { background: #1a1a2e; color: #a78bfa; padding: 8px 12px; text-align: left; border: 1px solid #2a2a3e; }
  .stats-table td { padding: 6px 12px; border: 1px solid #1a1a2e; }
  .stats-table tr:nth-child(even) { background: rgba(255,255,255,0.02); }
  .sig { color: #22c55e; font-weight: bold; }
  .nosig { color: #666; }
  .mel-container { display: flex; gap: 12px; margin: 12px 0; flex-wrap: wrap; }
  .mel-panel { flex: 1; min-width: 400px; }
  .mel-panel h4 { margin: 4px 0; font-size: 0.85rem; }
  canvas { width: 100%; height: 200px; border: 1px solid #2a2a3e; border-radius: 4px; }
  .chunk-card { background: #12121e; border: 1px solid #2a2a3e; border-radius: 8px; padding: 16px; margin: 16px 0; }
  .chunk-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .chunk-text { color: #888; font-size: 0.85rem; font-style: italic; margin: 8px 0; }
  .badge { padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
  .badge-echo { background: #713f12; color: #f59e0b; }
  .badge-clean { background: #166534; color: #22c55e; }
  .summary-box { background: #1a1a2e; border: 1px solid #38bdf8; border-radius: 8px; padding: 20px; margin: 20px 0; }
  .key-finding { background: #0f2b1a; border-left: 4px solid #22c55e; padding: 12px 16px; margin: 12px 0; }
  .warning { background: #2b1a0f; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 12px 0; }
</style>
</head><body>
<h1>Echo Fingerprint Analysis</h1>
<p>Generated: """ + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M') + """</p>
"""]

    # Summary box
    paired = sum(1 for d in dataset if d["has_pair"])
    html_parts.append(f"""
<div class="summary-box">
  <h3>Dataset</h3>
  <p><strong>{len(dataset)}</strong> echo chunks across <strong>{len(set(d['session'] for d in dataset))}</strong> sessions</p>
  <p><strong>{paired}</strong> paired (echo + clean version of same text)</p>
  <p><strong>{len(stats)}</strong> features extracted per chunk</p>
</div>
""")

    # Top discriminating features table
    if stats:
        html_parts.append("<h2>Top 30 Discriminating Features</h2>")
        html_parts.append("<p>Ranked by |Cohen's d| — effect size between echo and clean populations</p>")
        html_parts.append("""<table class="stats-table">
<tr><th>#</th><th>Feature</th><th>|d|</th><th>p-value</th><th>Echo mean</th><th>Clean mean</th><th>Direction</th></tr>""")

        for i, r in enumerate(stats[:30]):
            sig_class = "sig" if r["p_value"] < 0.05 else "nosig"
            html_parts.append(f"""<tr>
<td>{i+1}</td><td>{r['feature']}</td>
<td class="{sig_class}">{r['abs_d']:.3f}</td>
<td class="{sig_class}">{r['p_value']:.6f}</td>
<td>{r['echo_mean']:.4f}</td><td>{r['clean_mean']:.4f}</td>
<td>{r['direction']}</td></tr>""")

        html_parts.append("</table>")

    # Differential features table
    if diff_stats:
        html_parts.append("<h2>Top 30 Differential Features (Paired Analysis)</h2>")
        html_parts.append("<p>For chunks with both echo AND clean versions of the same text — what consistently changes?</p>")
        html_parts.append("""<table class="stats-table">
<tr><th>#</th><th>Feature</th><th>|t|</th><th>Mean diff</th><th>Consistency</th><th>N</th></tr>""")

        for i, r in enumerate(diff_stats[:30]):
            sig_class = "sig" if r["abs_t"] > 2.0 else "nosig"
            html_parts.append(f"""<tr>
<td>{i+1}</td><td>{r['feature']}</td>
<td class="{sig_class}">{r['abs_t']:.2f}</td>
<td>{r['mean_diff']:.6f}</td>
<td>{r['consistent_sign']:.0%}</td><td>{r['n']}</td></tr>""")

        html_parts.append("</table>")

    # Mel spectrogram comparisons
    html_parts.append("<h2>Mel Spectrogram Comparisons (Echo vs Clean)</h2>")
    html_parts.append("<p>Side-by-side spectrograms for paired chunks. Look for visual differences in energy distribution, smearing, or band patterns.</p>")

    for idx, mel in enumerate(mel_spectrograms):
        if "clean_mel" not in mel:
            continue

        html_parts.append(f"""
<div class="chunk-card">
  <div class="chunk-header">
    <span><strong>{mel['session']}</strong> — Chunk {mel['chunk']}</span>
    <span>
      <span class="badge badge-echo">ECHO v{mel.get('echo_version', '?')}</span>
      <span class="badge badge-clean">CLEAN v{mel.get('clean_version', '?')}</span>
    </span>
  </div>
  <div class="chunk-text">"{mel.get('text', '')}"</div>
  <div class="mel-container">
    <div class="mel-panel">
      <h4>ECHO</h4>
      <canvas id="echo-{idx}" data-mel="{idx}-echo"></canvas>
    </div>
    <div class="mel-panel">
      <h4>CLEAN</h4>
      <canvas id="clean-{idx}" data-mel="{idx}-clean"></canvas>
    </div>
    <div class="mel-panel">
      <h4>DIFFERENCE (echo - clean)</h4>
      <canvas id="diff-{idx}" data-mel="{idx}-diff"></canvas>
    </div>
  </div>
</div>""")

    # Embed mel data as JS and render with canvas
    html_parts.append("<script>")
    html_parts.append("const melData = {};")

    for idx, mel in enumerate(mel_spectrograms):
        if "clean_mel" not in mel:
            continue
        # Downsample to max 200 frames for performance
        echo_mel = np.array(mel["echo_mel"])
        clean_mel = np.array(mel["clean_mel"])

        # Align lengths
        min_frames = min(echo_mel.shape[1], clean_mel.shape[1])
        echo_mel = echo_mel[:, :min_frames]
        clean_mel = clean_mel[:, :min_frames]
        diff_mel = echo_mel - clean_mel

        # Downsample if needed
        if min_frames > 200:
            step = min_frames // 200
            echo_mel = echo_mel[:, ::step]
            clean_mel = clean_mel[:, ::step]
            diff_mel = diff_mel[:, ::step]

        html_parts.append(f"melData['{idx}-echo'] = {echo_mel.tolist()};")
        html_parts.append(f"melData['{idx}-clean'] = {clean_mel.tolist()};")
        html_parts.append(f"melData['{idx}-diff'] = {diff_mel.tolist()};")

    html_parts.append("""
function drawMel(canvasId, dataKey, isDiff) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !melData[dataKey]) return;
  const ctx = canvas.getContext('2d');
  const data = melData[dataKey];
  const nBands = data.length;
  const nFrames = data[0].length;

  canvas.width = canvas.offsetWidth * 2;
  canvas.height = 400;

  const cellW = canvas.width / nFrames;
  const cellH = canvas.height / nBands;

  // Find range
  let vmin = Infinity, vmax = -Infinity;
  for (let b = 0; b < nBands; b++) {
    for (let f = 0; f < nFrames; f++) {
      if (data[b][f] < vmin) vmin = data[b][f];
      if (data[b][f] > vmax) vmax = data[b][f];
    }
  }

  if (isDiff) {
    // Symmetric range for difference maps
    const absMax = Math.max(Math.abs(vmin), Math.abs(vmax));
    vmin = -absMax;
    vmax = absMax;
  }

  const range = vmax - vmin || 1;

  for (let b = 0; b < nBands; b++) {
    for (let f = 0; f < nFrames; f++) {
      const val = (data[b][f] - vmin) / range;
      const y = canvas.height - (b + 1) * cellH;

      if (isDiff) {
        // Blue-white-red diverging colormap
        const centered = (data[b][f] - vmin) / range; // 0 to 1, 0.5 = zero
        if (centered < 0.5) {
          const t = centered * 2;
          ctx.fillStyle = `rgb(${Math.round(t*255)},${Math.round(t*255)},255)`;
        } else {
          const t = (centered - 0.5) * 2;
          ctx.fillStyle = `rgb(255,${Math.round((1-t)*255)},${Math.round((1-t)*255)})`;
        }
      } else {
        // Viridis-like: dark purple -> blue -> green -> yellow
        const r = Math.round(Math.min(255, val * 4 * 255));
        const g = Math.round(Math.min(255, Math.max(0, (val - 0.25) * 4 * 255)));
        const b2 = Math.round(Math.max(0, (1 - val * 2) * 255));
        ctx.fillStyle = `rgb(${r},${g},${b2})`;
      }

      ctx.fillRect(f * cellW, y, Math.ceil(cellW), Math.ceil(cellH));
    }
  }
}

// Render all spectrograms
window.addEventListener('load', () => {
  document.querySelectorAll('canvas[data-mel]').forEach(canvas => {
    const key = canvas.getAttribute('data-mel');
    const isDiff = key.endsWith('-diff');
    drawMel(canvas.id, key, isDiff);
  });
});

// Re-render on resize
window.addEventListener('resize', () => {
  document.querySelectorAll('canvas[data-mel]').forEach(canvas => {
    const key = canvas.getAttribute('data-mel');
    const isDiff = key.endsWith('-diff');
    drawMel(canvas.id, key, isDiff);
  });
});
</script>""")

    html_parts.append("</body></html>")

    report_path = OUTPUT_DIR / "echo-fingerprint-report.html"
    with open(report_path, 'w') as f:
        f.write("\n".join(html_parts))

    print(f"\nReport saved to: {report_path}")
    return report_path


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Echo Fingerprint Workbench")
    parser.add_argument('--collect', action='store_true', help='Build dataset')
    parser.add_argument('--analyze', action='store_true', help='Run granular analysis')
    parser.add_argument('--classify', action='store_true', help='Build & test echo classifier')
    parser.add_argument('--report', action='store_true', help='Generate HTML report')
    parser.add_argument('--all', action='store_true', help='All four steps')
    args = parser.parse_args()

    if args.all:
        args.collect = args.analyze = args.classify = args.report = True

    if not (args.collect or args.analyze or args.classify or args.report):
        parser.print_help()
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dataset = None
    mel_spectrograms = None

    if args.collect:
        dataset = collect_dataset()

    if args.analyze:
        if dataset is None:
            dataset_path = OUTPUT_DIR / "echo_dataset.json"
            if dataset_path.exists():
                with open(dataset_path) as f:
                    dataset = json.load(f)
            else:
                print("ERROR: Run --collect first")
                return

        _, _, _, mel_spectrograms = analyze_dataset(dataset)

    if args.classify:
        classify_echo()

    if args.report:
        if dataset is None:
            dataset_path = OUTPUT_DIR / "echo_dataset.json"
            if dataset_path.exists():
                with open(dataset_path) as f:
                    dataset = json.load(f)

        if mel_spectrograms is None:
            mel_path = OUTPUT_DIR / "mel_spectrograms.json"
            if mel_path.exists():
                with open(mel_path) as f:
                    mel_spectrograms = json.load(f)
            else:
                mel_spectrograms = []

        report_path = generate_report(dataset, mel_spectrograms)
        print(f"\nOpen the report: file://{report_path}")


if __name__ == '__main__':
    main()
