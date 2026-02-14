#!/usr/bin/env python3
"""
Generate mel spectrogram comparisons: ECHO vs PASS candidates.
Visual inspection to find the spectral pattern of Fish TTS echo.

Also computes spectrogram DIFFERENCE to isolate the echo signature.

Usage:
    python3 tools/echo-spectrogram-compare.py
"""
import json
import sys
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent))

VAULT = Path("content/audio-free/vault")
V5 = Path("reference/v5-test")
OUT = Path("reference/echo-spectrograms")

SESSION_NAMES = {
    "85": "85-counting-down-to-sleep",
    "63": "63-21day-mindfulness-day07",
}


def load_samples():
    """Load ECHO and PASS samples."""
    echo = []
    clean = []
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


def compute_mel_spectrogram(wav_path, sr=22050, n_fft=2048, hop=256, n_mels=128):
    """Compute mel spectrogram in dB."""
    import librosa
    y, _ = librosa.load(wav_path, sr=sr, mono=True)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=n_fft, hop_length=hop, n_mels=n_mels)
    S_db = librosa.power_to_db(S, ref=np.max)
    return S_db, y


def compute_power_cepstrum(y, sr=22050, n_fft=4096):
    """Compute power cepstrum to detect echo delay."""
    # Use middle segment of audio
    mid = len(y) // 2
    start = max(0, mid - n_fft // 2)
    frame = y[start:start + n_fft]
    if len(frame) < n_fft:
        frame = np.pad(frame, (0, n_fft - len(frame)))
    window = np.hanning(n_fft)
    Y = np.fft.rfft(frame * window)
    power = np.abs(Y) ** 2
    log_power = np.log(power + 1e-10)
    cepstrum = np.fft.irfft(log_power)
    # Convert quefrency to ms
    quefrency_ms = np.arange(len(cepstrum)) / sr * 1000
    return cepstrum, quefrency_ms


def compute_autocorrelation(y, sr=22050, max_lag_ms=200):
    """Compute normalized autocorrelation of amplitude envelope."""
    # Amplitude envelope
    import librosa
    env = np.abs(librosa.onset.onset_strength(y=y, sr=sr, hop_length=256))
    env = env / (np.max(env) + 1e-10)

    max_lag = int(max_lag_ms / 1000 * sr / 256)
    max_lag = min(max_lag, len(env) - 1)

    acf = np.correlate(env - np.mean(env), env - np.mean(env), mode='full')
    acf = acf[len(acf)//2:]
    acf = acf / (acf[0] + 1e-10)

    lag_ms = np.arange(len(acf)) * 256 / sr * 1000
    return acf[:max_lag], lag_ms[:max_lag]


def plot_comparison(echo_s, clean_s, idx, out_dir):
    """Generate side-by-side spectrogram comparison."""
    import librosa

    fig, axes = plt.subplots(4, 2, figsize=(18, 16))
    fig.suptitle(f"ECHO vs CLEAN comparison #{idx+1}", fontsize=14)

    for col, (sample, label) in enumerate([(echo_s, "ECHO"), (clean_s, "CLEAN/PASS")]):
        # Mel spectrogram
        S_db, y = compute_mel_spectrogram(sample["wav"])
        sr = 22050

        ax = axes[0, col]
        img = ax.imshow(S_db, aspect='auto', origin='lower', cmap='magma',
                       extent=[0, S_db.shape[1] * 256 / sr, 0, sr/2])
        ax.set_title(f"{label}: S{sample['session']} c{sample['chunk']} v{sample['version']}\n{','.join(sample['labels'])}")
        ax.set_ylabel('Frequency (Hz)')
        ax.set_xlabel('Time (s)')
        plt.colorbar(img, ax=ax, label='dB')

        # Power cepstrum (echo detection region: 15-200ms)
        cepstrum, quefrency_ms = compute_power_cepstrum(y, sr)
        ax = axes[1, col]
        mask = (quefrency_ms >= 5) & (quefrency_ms <= 200)
        ax.plot(quefrency_ms[mask], np.abs(cepstrum[mask]), 'b-', linewidth=0.5)
        ax.set_title(f"Power Cepstrum ({label})")
        ax.set_xlabel("Quefrency (ms)")
        ax.set_ylabel("|Cepstrum|")
        ax.axvspan(15, 200, alpha=0.1, color='red', label='echo region')
        ax.legend()

        # Envelope autocorrelation
        acf, lag_ms = compute_autocorrelation(y, sr)
        ax = axes[2, col]
        ax.plot(lag_ms, acf, 'g-', linewidth=0.8)
        ax.set_title(f"Envelope Autocorrelation ({label})")
        ax.set_xlabel("Lag (ms)")
        ax.set_ylabel("Correlation")
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)

        # Spectral flux over time
        S_full = np.abs(librosa.stft(y, n_fft=2048, hop_length=256))
        flux = np.sqrt(np.sum(np.diff(S_full, axis=1) ** 2, axis=0))
        t_flux = np.arange(len(flux)) * 256 / sr
        ax = axes[3, col]
        ax.plot(t_flux, flux, 'r-', linewidth=0.5, alpha=0.7)
        ax.set_title(f"Spectral Flux ({label})")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Flux")

    plt.tight_layout()
    out_path = out_dir / f"compare_{idx:02d}.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")
    return out_path


def plot_aggregate(echo_samples, clean_samples, out_dir):
    """Aggregate analysis: average cepstrum and autocorrelation for echo vs clean."""
    import librosa

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f"AGGREGATE: {len(echo_samples)} ECHO vs {len(clean_samples)} CLEAN", fontsize=14)

    # Aggregate cepstra
    echo_cepstra = []
    clean_cepstra = []
    sr = 22050

    for s in echo_samples:
        y, _ = librosa.load(s["wav"], sr=sr, mono=True)
        cepstrum, qms = compute_power_cepstrum(y, sr)
        mask = (qms >= 5) & (qms <= 200)
        echo_cepstra.append(np.abs(cepstrum[mask]))

    for s in clean_samples:
        y, _ = librosa.load(s["wav"], sr=sr, mono=True)
        cepstrum, qms = compute_power_cepstrum(y, sr)
        mask = (qms >= 5) & (qms <= 200)
        clean_cepstra.append(np.abs(cepstrum[mask]))

    # Pad to same length
    max_len = max(max(len(c) for c in echo_cepstra), max(len(c) for c in clean_cepstra))
    echo_cepstra = [np.pad(c, (0, max_len - len(c))) for c in echo_cepstra]
    clean_cepstra = [np.pad(c, (0, max_len - len(c))) for c in clean_cepstra]

    echo_mean = np.mean(echo_cepstra, axis=0)
    clean_mean = np.mean(clean_cepstra, axis=0)
    echo_std = np.std(echo_cepstra, axis=0)
    clean_std = np.std(clean_cepstra, axis=0)

    qms_plot = np.linspace(5, 200, max_len)

    ax = axes[0, 0]
    ax.plot(qms_plot, echo_mean, 'r-', label='ECHO mean', linewidth=2)
    ax.fill_between(qms_plot, echo_mean - echo_std, echo_mean + echo_std, alpha=0.2, color='red')
    ax.plot(qms_plot, clean_mean, 'b-', label='CLEAN mean', linewidth=2)
    ax.fill_between(qms_plot, clean_mean - clean_std, clean_mean + clean_std, alpha=0.2, color='blue')
    ax.set_title("Average Power Cepstrum")
    ax.set_xlabel("Quefrency (ms)")
    ax.set_ylabel("|Cepstrum|")
    ax.legend()

    # Difference
    ax = axes[0, 1]
    diff = echo_mean - clean_mean
    ax.plot(qms_plot, diff, 'k-', linewidth=1.5)
    ax.fill_between(qms_plot, diff, 0, where=diff > 0, alpha=0.3, color='red', label='ECHO > CLEAN')
    ax.fill_between(qms_plot, diff, 0, where=diff < 0, alpha=0.3, color='blue', label='CLEAN > ECHO')
    ax.set_title("Cepstrum Difference (ECHO - CLEAN)")
    ax.set_xlabel("Quefrency (ms)")
    ax.set_ylabel("Difference")
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.legend()

    # Aggregate autocorrelation
    echo_acfs = []
    clean_acfs = []
    for s in echo_samples:
        y, _ = librosa.load(s["wav"], sr=sr, mono=True)
        acf, lms = compute_autocorrelation(y, sr)
        echo_acfs.append(acf)
    for s in clean_samples:
        y, _ = librosa.load(s["wav"], sr=sr, mono=True)
        acf, lms = compute_autocorrelation(y, sr)
        clean_acfs.append(acf)

    max_len2 = min(min(len(a) for a in echo_acfs), min(len(a) for a in clean_acfs))
    echo_acfs = [a[:max_len2] for a in echo_acfs]
    clean_acfs = [a[:max_len2] for a in clean_acfs]
    lms = lms[:max_len2]

    echo_acf_mean = np.mean(echo_acfs, axis=0)
    clean_acf_mean = np.mean(clean_acfs, axis=0)

    ax = axes[1, 0]
    ax.plot(lms, echo_acf_mean, 'r-', label='ECHO', linewidth=2)
    ax.plot(lms, clean_acf_mean, 'b-', label='CLEAN', linewidth=2)
    ax.set_title("Average Envelope Autocorrelation")
    ax.set_xlabel("Lag (ms)")
    ax.set_ylabel("Correlation")
    ax.legend()

    # Per-frequency band energy comparison
    ax = axes[1, 1]
    echo_bands = []
    clean_bands = []
    bands = [(0, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 11025)]
    band_labels = ["0-500", "500-1k", "1k-2k", "2k-4k", "4k-8k", "8k-11k"]

    for s in echo_samples:
        y, _ = librosa.load(s["wav"], sr=sr, mono=True)
        S = np.abs(librosa.stft(y, n_fft=2048, hop_length=256))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        energies = []
        for lo, hi in bands:
            mask = (freqs >= lo) & (freqs < hi)
            energies.append(float(np.mean(S[mask, :])))
        echo_bands.append(energies)

    for s in clean_samples:
        y, _ = librosa.load(s["wav"], sr=sr, mono=True)
        S = np.abs(librosa.stft(y, n_fft=2048, hop_length=256))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        energies = []
        for lo, hi in bands:
            mask = (freqs >= lo) & (freqs < hi)
            energies.append(float(np.mean(S[mask, :])))
        clean_bands.append(energies)

    echo_bands_mean = np.mean(echo_bands, axis=0)
    clean_bands_mean = np.mean(clean_bands, axis=0)

    x = np.arange(len(bands))
    width = 0.35
    ax.bar(x - width/2, echo_bands_mean, width, label='ECHO', color='red', alpha=0.7)
    ax.bar(x + width/2, clean_bands_mean, width, label='CLEAN', color='blue', alpha=0.7)
    ax.set_title("Mean Spectral Energy by Band")
    ax.set_xticks(x)
    ax.set_xticklabels(band_labels)
    ax.set_xlabel("Frequency Band (Hz)")
    ax.set_ylabel("Mean Magnitude")
    ax.legend()

    plt.tight_layout()
    out_path = out_dir / "aggregate.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")
    return out_path


def plot_within_chunk(echo_samples, out_dir):
    """For each echo chunk, compare its spectrogram against alternatives from same pool."""
    import librosa

    comparisons_made = 0
    for s in echo_samples:
        if comparisons_made >= 3:
            break

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

        # Pick a random alternative
        np.random.seed(42 + ci)
        alt_wav = alt_wavs[np.random.randint(len(alt_wavs))]
        alt_version = int(alt_wav.stem.split("_v")[1])

        fig, axes = plt.subplots(3, 2, figsize=(18, 12))
        fig.suptitle(f"WITHIN-CHUNK: S{s['session']} c{s['chunk']} — "
                     f"ECHO v{picked_version} vs ALT v{alt_version}", fontsize=14)

        for col, (wav_path, label) in enumerate([
            (s["wav"], f"ECHO v{picked_version}"),
            (str(alt_wav), f"ALT v{alt_version} (unjudged)")
        ]):
            S_db, y = compute_mel_spectrogram(wav_path)
            sr = 22050

            # Mel spectrogram
            ax = axes[0, col]
            img = ax.imshow(S_db, aspect='auto', origin='lower', cmap='magma',
                           extent=[0, S_db.shape[1] * 256 / sr, 0, sr/2])
            ax.set_title(f"{label}")
            ax.set_ylabel('Frequency (Hz)')
            plt.colorbar(img, ax=ax, label='dB')

            # Cepstrum
            cepstrum, qms = compute_power_cepstrum(y, sr)
            ax = axes[1, col]
            mask = (qms >= 5) & (qms <= 200)
            ax.plot(qms[mask], np.abs(cepstrum[mask]), 'b-', linewidth=0.8)
            ax.set_title(f"Cepstrum ({label})")
            ax.set_xlabel("Quefrency (ms)")
            ax.axvspan(15, 200, alpha=0.1, color='red')

            # Waveform zoom (first 0.5s)
            ax = axes[2, col]
            t = np.arange(min(len(y), int(0.5 * sr))) / sr
            ax.plot(t, y[:len(t)], 'k-', linewidth=0.3)
            ax.set_title(f"Waveform first 0.5s ({label})")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")

        plt.tight_layout()
        out_path = out_dir / f"within_chunk_{s['session']}_c{s['chunk']:0>2s}.png"
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {out_path}")
        comparisons_made += 1


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    echo_samples, clean_samples = load_samples()
    print(f"Loaded: {len(echo_samples)} ECHO, {len(clean_samples)} CLEAN")

    # Generate individual comparisons (first 5 pairs)
    print("\n--- Individual Comparisons ---")
    n_compare = min(5, len(echo_samples), len(clean_samples))
    paths = []
    for i in range(n_compare):
        p = plot_comparison(echo_samples[i], clean_samples[i], i, OUT)
        paths.append(p)

    # Generate aggregate analysis
    print("\n--- Aggregate Analysis ---")
    agg_path = plot_aggregate(echo_samples, clean_samples, OUT)
    paths.append(agg_path)

    # Within-chunk comparison
    print("\n--- Within-Chunk Comparisons ---")
    plot_within_chunk(echo_samples, OUT)

    print(f"\nAll spectrograms saved to: {OUT}")
    print("Open them to visually inspect for echo patterns.")


if __name__ == "__main__":
    main()
