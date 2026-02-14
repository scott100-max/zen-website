#!/usr/bin/env python3
"""Quick inspection: compare echo vs clean WAVs to understand the defect."""
import json
import numpy as np
import librosa
from pathlib import Path

VAULT = Path("content/audio-free/vault")
V5 = Path("reference/v5-test")
SR = 22050

def inspect(wav_path, label):
    y, _ = librosa.load(wav_path, sr=SR, mono=True)
    dur = len(y) / SR

    # Basic stats
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=256))
    S_db = librosa.power_to_db(S, ref=np.max)

    # Pitch
    f0 = librosa.yin(y, fmin=60, fmax=300, sr=SR, frame_length=2048, hop_length=256)
    f0_valid = f0[(f0 > 60) & (f0 < 300)]
    f0_mean = np.mean(f0_valid) if len(f0_valid) > 0 else 0
    f0_std = np.std(f0_valid) if len(f0_valid) > 0 else 0

    # HNR approximation: energy at harmonics vs between
    # Simple: spectral flatness (lower = more harmonic = cleaner)
    sf = librosa.feature.spectral_flatness(S=S)[0]

    # Autocorrelation at various delays
    acf = np.correlate(y[:SR], y[:SR], mode='full')[len(y[:SR])-1:]
    acf_norm = acf / (acf[0] + 1e-10)

    # First 500ms of signal: look for pre-echo
    first_500ms = y[:int(0.5 * SR)]
    first_rms = np.sqrt(np.mean(first_500ms**2))

    # Last 200ms: reverb tail
    last_200ms = y[-int(0.2 * SR):]
    last_rms = np.sqrt(np.mean(last_200ms**2))

    # Energy in very quiet frames (bottom 10%)
    q10 = np.percentile(rms, 10)
    quiet_rms = np.mean(rms[rms <= q10]) if q10 > 0 else 0

    # Inter-harmonic noise
    # Take a voiced frame near the middle
    mid_idx = len(y) // 2
    frame = y[mid_idx:mid_idx+4096]
    if len(frame) == 4096:
        spec = np.abs(np.fft.rfft(frame * np.hanning(4096)))
        freqs = np.fft.rfftfreq(4096, 1/SR)

        # Find harmonics of F0
        if f0_mean > 60:
            harmonic_energy = 0
            inter_energy = 0
            for h in range(1, 20):
                hf = f0_mean * h
                if hf > SR/2:
                    break
                # Find nearest bin
                bin_idx = int(hf / (SR / 4096))
                # Harmonic: ±2 bins around harmonic
                h_start = max(0, bin_idx - 2)
                h_end = min(len(spec), bin_idx + 3)
                harmonic_energy += np.sum(spec[h_start:h_end]**2)

                # Inter-harmonic: between this and next harmonic
                next_hf = f0_mean * (h + 0.5)
                next_bin = int(next_hf / (SR / 4096))
                i_start = max(0, next_bin - 2)
                i_end = min(len(spec), next_bin + 3)
                inter_energy += np.sum(spec[i_start:i_end]**2)

            hnr = 10 * np.log10(harmonic_energy / (inter_energy + 1e-10) + 1e-10)
        else:
            hnr = 0
    else:
        hnr = 0

    print(f"\n{'ECHO' if 'ECHO' in label else 'CLEAN':>5} | {Path(wav_path).name} | {label}")
    print(f"  dur={dur:.2f}s  f0={f0_mean:.1f}±{f0_std:.1f}Hz")
    print(f"  rms: mean={np.mean(rms):.6f} min={np.min(rms):.6f} q10={quiet_rms:.6f}")
    print(f"  spectral_flatness: mean={np.mean(sf):.6f} std={np.std(sf):.6f}")
    print(f"  first_500ms_rms={first_rms:.6f}  last_200ms_rms={last_rms:.6f}")
    print(f"  HNR={hnr:.1f}dB")
    print(f"  acf[15ms]={acf_norm[int(0.015*SR)]:.6f} acf[30ms]={acf_norm[int(0.030*SR)]:.6f} "
          f"acf[50ms]={acf_norm[int(0.050*SR)]:.6f} acf[100ms]={acf_norm[int(0.100*SR)]:.6f}")
    return {
        "label": label, "dur": dur, "f0_mean": f0_mean, "f0_std": f0_std,
        "rms_mean": float(np.mean(rms)), "rms_min": float(np.min(rms)),
        "sf_mean": float(np.mean(sf)), "hnr": hnr,
        "first_500_rms": first_rms, "last_200_rms": last_rms,
        "acf_15ms": float(acf_norm[int(0.015*SR)]),
        "acf_30ms": float(acf_norm[int(0.030*SR)]),
        "acf_50ms": float(acf_norm[int(0.050*SR)]),
        "acf_100ms": float(acf_norm[int(0.100*SR)]),
    }

# Load S85 verdicts
with open(V5 / "85-verdicts-r2.json") as f:
    v85 = json.load(f)

echo_results = []
clean_results = []

for chunk_id, vd in v85["chunks"].items():
    ci = int(chunk_id)
    vi = vd["version"]
    wav = VAULT / "85-counting-down-to-sleep" / f"c{ci:02d}" / f"c{ci:02d}_v{vi:02d}.wav"
    if not wav.exists():
        continue
    label = ",".join(vd["verdict"])
    r = inspect(str(wav), label)
    if vd.get("passed"):
        clean_results.append(r)
    elif "ECHO" in vd["verdict"]:
        echo_results.append(r)

# Summary comparison
print(f"\n{'='*60}")
print(f"SUMMARY: {len(echo_results)} ECHO vs {len(clean_results)} CLEAN")
print(f"{'='*60}")
for key in ["f0_mean", "f0_std", "rms_mean", "rms_min", "sf_mean", "hnr",
            "first_500_rms", "last_200_rms", "acf_15ms", "acf_30ms", "acf_50ms", "acf_100ms"]:
    echo_vals = [r[key] for r in echo_results]
    clean_vals = [r[key] for r in clean_results]
    print(f"  {key:20s}  ECHO={np.mean(echo_vals):10.4f}  CLEAN={np.mean(clean_vals):10.4f}  "
          f"diff={np.mean(echo_vals)-np.mean(clean_vals):+10.4f}")
