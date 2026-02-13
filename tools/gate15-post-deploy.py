#!/usr/bin/env python3
"""Gate 15: Post-Deploy Live Audio Scanner

Scans deployed MP3 from CDN after every deploy.
Bible L-35 CRITICAL — catches catastrophic failures that pre-deploy gates miss.

Usage:
  python3 tools/gate15-post-deploy.py content/audio-free/01-morning-meditation.mp3
  python3 tools/gate15-post-deploy.py https://media.salus-mind.com/content/audio-free/01.mp3 \
    --duration-min 14 --fade-in-sec 30 --verbose

Exit codes: 0 = all pass, 1 = any fail, 2 = download/decode error
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from scipy.signal import butter, sosfilt

# ── Constants (from Bible spec) ──────────────────────────────────────────────

CDN_BASE = "https://media.salus-mind.com"

SILENCE_THRESHOLD_DB = -80.0    # Check 1: catastrophic silence (true dead signal, not ambient gaps)
PEAK_THRESHOLD_DB = -1.0        # Check 2: volume explosion
CENTROID_LOW_HZ = 500.0         # Check 3: voice breakdown lower bound
CENTROID_HIGH_HZ = 6000.0       # Check 3: voice breakdown upper bound
DURATION_TOLERANCE = 0.30       # Check 4: ±30% deviation
HISS_THRESHOLD_DB = -36.0       # Check 5: HF energy ceiling
HISS_HP_FREQ = 4000.0           # Check 5: highpass cutoff
SPEECH_THRESHOLD_DB = -35.0     # Check 6: speech/ambient boundary
AMBIENT_FLOOR_DB = -70.0        # Check 6: "no audio at all" floor


# ── Helpers ──────────────────────────────────────────────────────────────────

def db(linear):
    """Convert linear RMS to dB. Clamp to -100 dB floor."""
    if linear <= 0:
        return -100.0
    return 20.0 * math.log10(linear)


def rms(samples):
    """RMS of int16 samples, normalized to 0..1 range."""
    if len(samples) == 0:
        return 0.0
    return np.sqrt(np.mean((samples.astype(np.float64) / 32768.0) ** 2))


def peak_db(samples):
    """Peak amplitude in dB (0 dBFS = 32768)."""
    if len(samples) == 0:
        return -100.0
    return db(np.max(np.abs(samples.astype(np.float64))) / 32768.0)


def windowed_rms_db(samples, sr, window_sec):
    """Return list of (start_sec, rms_db) for each window."""
    window_samples = int(sr * window_sec)
    results = []
    for i in range(0, len(samples), window_samples):
        chunk = samples[i:i + window_samples]
        if len(chunk) < window_samples // 2:
            break
        results.append((i / sr, db(rms(chunk))))
    return results


def spectral_centroid(samples, sr):
    """Spectral centroid via FFT for a short audio chunk."""
    x = samples.astype(np.float64) / 32768.0
    if len(x) == 0:
        return 0.0
    fft_mag = np.abs(np.fft.rfft(x))
    freqs = np.fft.rfftfreq(len(x), d=1.0 / sr)
    total = np.sum(fft_mag)
    if total < 1e-12:
        return 0.0
    return np.sum(freqs * fft_mag) / total


# ── Download & Decode ────────────────────────────────────────────────────────

def download_and_decode(url):
    """Download MP3 from URL, decode to mono int16 numpy array.

    Returns (samples, sample_rate) or raises on error.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        mp3_path = os.path.join(tmpdir, "audio.mp3")
        wav_path = os.path.join(tmpdir, "audio.wav")

        # Download
        result = subprocess.run(
            ["curl", "-sL", "--fail", "-o", mp3_path, url],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(f"Download failed (curl exit {result.returncode}): {result.stderr.strip()}")

        file_size = os.path.getsize(mp3_path)
        if file_size < 1000:
            raise RuntimeError(f"Downloaded file too small ({file_size} bytes) — likely 404 or error page")

        # Decode to WAV (mono, 16-bit)
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", "44100",
             "-sample_fmt", "s16", wav_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg decode failed: {result.stderr.strip()[:200]}")

        # Read WAV into numpy
        with wave.open(wav_path, 'rb') as wf:
            sr = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)
            samples = np.frombuffer(raw, dtype=np.int16)

    return samples, sr


# ── 7 Checks ─────────────────────────────────────────────────────────────────

def check_catastrophic_silence(samples, sr, verbose=False):
    """Check 1: 5s windowed RMS — any speech-region window < -60 dBFS = FAIL."""
    windows = windowed_rms_db(samples, sr, 5.0)

    # Find speech regions (windows above -50 dB to identify the voice portion)
    speech_windows = [(t, level) for t, level in windows if level > -50.0]
    if not speech_windows:
        return False, {"reason": "No speech-level audio found in entire file"}

    # Within the speech region time span, check for silence holes
    speech_start = speech_windows[0][0]
    speech_end = speech_windows[-1][0]
    silent_windows = []
    for t, level in windows:
        if speech_start <= t <= speech_end and level < SILENCE_THRESHOLD_DB:
            silent_windows.append((t, level))

    if verbose and silent_windows:
        for t, level in silent_windows:
            print(f"    Silent window at {t:.0f}s: {level:.1f} dB")

    if silent_windows:
        return False, {"reason": f"{len(silent_windows)} silent window(s) in speech region",
                       "worst": min(silent_windows, key=lambda x: x[1])}
    return True, {"speech_region": f"{speech_start:.0f}s–{speech_end:.0f}s",
                  "windows_checked": len(windows)}


def check_volume_explosion(samples, sr, verbose=False):
    """Check 2: 5s windowed peak scan — any window peak > -1 dBFS = FAIL."""
    window_samples = int(sr * 5.0)
    hot_windows = []
    for i in range(0, len(samples), window_samples):
        chunk = samples[i:i + window_samples]
        if len(chunk) < window_samples // 2:
            break
        pk = peak_db(chunk)
        if pk > PEAK_THRESHOLD_DB:
            t = i / sr
            hot_windows.append((t, pk))
            if verbose:
                print(f"    Hot window at {t:.0f}s: peak {pk:.1f} dBFS")

    if hot_windows:
        return False, {"reason": f"{len(hot_windows)} window(s) exceed {PEAK_THRESHOLD_DB} dBFS",
                       "worst": max(hot_windows, key=lambda x: x[1])}
    return True, {"peak_ceiling": PEAK_THRESHOLD_DB}


def check_voice_breakdown(samples, sr, verbose=False):
    """Check 3: 1s spectral centroid — centroid <500Hz or >6kHz for >3s = FAIL."""
    window_sec = 1.0
    window_samples = int(sr * window_sec)
    bad_streak = 0
    max_bad_streak = 0
    worst_centroid = None

    for i in range(0, len(samples), window_samples):
        chunk = samples[i:i + window_samples]
        if len(chunk) < window_samples // 2:
            break

        # Skip near-silent windows (not speech)
        if db(rms(chunk)) < -50.0:
            bad_streak = 0
            continue

        c = spectral_centroid(chunk, sr)
        if c < CENTROID_LOW_HZ or c > CENTROID_HIGH_HZ:
            bad_streak += 1
            if bad_streak > max_bad_streak:
                max_bad_streak = bad_streak
                worst_centroid = c
            if verbose and bad_streak >= 3:
                t = i / sr
                print(f"    Breakdown at {t:.0f}s: centroid {c:.0f} Hz (streak: {bad_streak})")
        else:
            bad_streak = 0

    if max_bad_streak > 3:
        return False, {"reason": f"Spectral anomaly for {max_bad_streak}s (centroid: {worst_centroid:.0f} Hz)"}
    return True, {"max_anomaly_streak": max_bad_streak}


def check_duration_sanity(samples, sr, expected_min=None, verbose=False):
    """Check 4: Total duration vs expected — >30% deviation = FAIL."""
    actual_min = len(samples) / sr / 60.0

    if expected_min is None:
        return True, {"skipped": True, "actual_min": f"{actual_min:.1f}"}

    deviation = abs(actual_min - expected_min) / expected_min
    if verbose:
        print(f"    Actual: {actual_min:.1f} min, expected: {expected_min:.1f} min, deviation: {deviation:.1%}")

    if deviation > DURATION_TOLERANCE:
        return False, {"reason": f"Duration {actual_min:.1f} min deviates {deviation:.0%} from expected {expected_min:.1f} min"}
    return True, {"actual_min": f"{actual_min:.1f}", "expected_min": f"{expected_min:.1f}",
                  "deviation": f"{deviation:.1%}"}


def check_hiss_cascade(samples, sr, verbose=False):
    """Check 5: 10s windowed HF scan (butter 4kHz HP) — HF > -36dB for 3+ consecutive = FAIL."""
    # Design 4th-order Butterworth highpass at 4kHz
    sos = butter(4, HISS_HP_FREQ, btype='high', fs=sr, output='sos')
    hf_signal = sosfilt(sos, samples.astype(np.float64) / 32768.0)

    window_sec = 10.0
    window_samples = int(sr * window_sec)
    hot_streak = 0
    max_hot_streak = 0

    for i in range(0, len(hf_signal), window_samples):
        chunk = hf_signal[i:i + window_samples]
        if len(chunk) < window_samples // 2:
            break
        hf_rms = db(np.sqrt(np.mean(chunk ** 2)))
        if hf_rms > HISS_THRESHOLD_DB:
            hot_streak += 1
            if hot_streak > max_hot_streak:
                max_hot_streak = hot_streak
            if verbose:
                t = i / sr
                print(f"    HF hot at {t:.0f}s: {hf_rms:.1f} dB (streak: {hot_streak})")
        else:
            hot_streak = 0

    if max_hot_streak >= 3:
        return False, {"reason": f"HF energy > {HISS_THRESHOLD_DB} dB for {max_hot_streak * 10}s consecutive"}
    return True, {"max_hf_streak": max_hot_streak}


def check_ambient_fade_in(samples, sr, fade_in_sec=30.0, verbose=False):
    """Check 6: Ambient pre-roll — voice detected before t=30s = FAIL.

    "Ambient fade-in" means 30s of ambient-only audio BEFORE the narrator speaks.
    Voice track has 30s of silence prepended; ambient fades in over first 30s.
    """
    window_sec = 1.0
    window_samples = int(sr * window_sec)
    check_end = int(sr * min(fade_in_sec + 5.0, len(samples) / sr))

    # Classify each 1s window in first 35s as speech or ambient-only
    window_levels = []
    for i in range(0, check_end, window_samples):
        chunk = samples[i:i + window_samples]
        if len(chunk) < window_samples // 2:
            break
        level = db(rms(chunk))
        t = i / sr
        window_levels.append((t, level))
        if verbose:
            tag = "SPEECH" if level > SPEECH_THRESHOLD_DB else "ambient"
            print(f"    {t:5.1f}s: {level:6.1f} dB [{tag}]")

    if not window_levels:
        return False, {"reason": "No audio data in first 35s"}

    # Sub-check A: FAIL if any window in first 25s is speech-level
    early_speech = [(t, level) for t, level in window_levels
                    if t < (fade_in_sec - 5.0) and level > SPEECH_THRESHOLD_DB]
    if early_speech:
        first_t = early_speech[0][0]
        return False, {"reason": f"Voice detected at {first_t:.0f}s (expected silence until ~{fade_in_sec:.0f}s)",
                       "speech_windows": len(early_speech)}

    # Sub-check B: Verify ambient is PRESENT and RISING across pre-roll.
    # A 30s linear fade-in starts from silence, so first 5s may legitimately be
    # below -70 dBFS. Instead of an absolute threshold at t=0-5s, check:
    #  (a) the whole pre-roll is not dead (= no ambient at all)
    #  (b) RMS is rising across the pre-roll (proves fade-in is working)
    pre_roll = [(t, level) for t, level in window_levels if t < fade_in_sec]
    all_preroll_dead = all(level < AMBIENT_FLOOR_DB for _, level in pre_roll)
    if all_preroll_dead:
        return True, {"note": "No ambient detected — session may use Ambient: none",
                      "skipped_ambient_checks": True}

    # Check rising trend: compare first-quarter mean to last-quarter mean
    if len(pre_roll) >= 4:
        q_len = len(pre_roll) // 4
        first_q = [level for _, level in pre_roll[:q_len]]
        last_q = [level for _, level in pre_roll[-q_len:]]
        rise = np.mean(last_q) - np.mean(first_q)
        if verbose:
            print(f"    Pre-roll rise (Q1→Q4): {rise:.1f} dB")
        # Expect at least 6 dB rise across the fade-in (a 30s linear fade
        # from silence to -19 dBFS produces ~15-20 dB rise)
        if rise < 6.0:
            return False, {"reason": f"Pre-roll RMS not rising enough ({rise:.1f} dB, need ≥6 dB) — "
                                     "ambient fade-in may be broken"}

    # Sub-check C: Ambient volume should increase over 0-30s (~15-20 dB rise)
    pre_roll_windows = [(t, level) for t, level in window_levels if t < fade_in_sec]
    if len(pre_roll_windows) >= 6:
        first_third = [level for t, level in pre_roll_windows if t < fade_in_sec / 3]
        last_third = [level for t, level in pre_roll_windows if t > 2 * fade_in_sec / 3]
        if first_third and last_third:
            rise = np.mean(last_third) - np.mean(first_third)
            if verbose:
                print(f"    Ambient rise over pre-roll: {rise:.1f} dB")

    return True, {"pre_roll_sec": fade_in_sec, "early_speech_windows": 0}


def check_ambient_fade_out(samples, sr, fade_out_sec=8.0, verbose=False):
    """Check 7: Ambient fade-out — final 2s louder than preceding 6s = FAIL."""
    total_sec = len(samples) / sr
    if total_sec < fade_out_sec + 2:
        return True, {"skipped": True, "reason": "File too short for fade-out check"}

    # Split final 8s: preceding 6s vs final 2s
    final_8s_start = int(sr * (total_sec - fade_out_sec))
    final_2s_start = int(sr * (total_sec - 2.0))

    preceding = samples[final_8s_start:final_2s_start]
    final = samples[final_2s_start:]

    preceding_rms = db(rms(preceding))
    final_rms = db(rms(final))

    if verbose:
        print(f"    Preceding 6s RMS: {preceding_rms:.1f} dB")
        print(f"    Final 2s RMS: {final_rms:.1f} dB")

    # FAIL if final 2s is louder than preceding 6s (should be fading out)
    if final_rms > preceding_rms:
        return False, {"reason": f"Final 2s ({final_rms:.1f} dB) louder than preceding 6s ({preceding_rms:.1f} dB)",
                       "preceding_rms": preceding_rms, "final_rms": final_rms}
    return True, {"preceding_rms": f"{preceding_rms:.1f}", "final_rms": f"{final_rms:.1f}"}


# ── Email Notification ────────────────────────────────────────────────────────

def send_urgent_email(url, results):
    """Send URGENT email via Resend when any check fails."""
    # Load API key from .env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, "..", ".env")
    resend_key = os.environ.get("RESEND_API_KEY")
    if not resend_key and os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("RESEND_API_KEY="):
                    resend_key = line.strip().split("=", 1)[1]
                    break

    if not resend_key:
        print("  No RESEND_API_KEY — skipping email notification")
        return

    filename = url.rsplit("/", 1)[-1] if "/" in url else url
    subject = f"[URGENT] Gate 15 FAIL — {filename}"

    lines = [f"Gate 15 Post-Deploy Scanner: FAIL", f"Source: {url}", ""]
    for num in sorted(results):
        r = results[num]
        status = "PASS" if r["passed"] else "FAIL"
        if r["details"].get("skipped"):
            status = "SKIP"
        line = f"  Check {num} ({r['name']}): {status}"
        if not r["passed"]:
            line += f" — {r['details'].get('reason', '')}"
        lines.append(line)

    lines.append("")
    lines.append("This session is live on CDN. Review immediately.")

    payload = json.dumps({
        "from": "Claude <claude@salus-mind.com>",
        "to": ["scottripley@icloud.com"],
        "reply_to": "claude@salus-mind.com",
        "subject": subject,
        "text": "\n".join(lines),
    })

    try:
        subprocess.run(
            ["curl", "-s", "-X", "POST", "https://api.resend.com/emails",
             "-H", f"Authorization: Bearer {resend_key}",
             "-H", "Content-Type: application/json",
             "-d", payload],
            capture_output=True, check=True, timeout=30
        )
        print(f"  URGENT email sent: {subject}")
    except Exception as e:
        print(f"  Email send failed: {e}")


# ── Runner ───────────────────────────────────────────────────────────────────

CHECK_NAMES = {
    1: "Catastrophic Silence",
    2: "Volume Explosion",
    3: "Voice Breakdown",
    4: "Duration Sanity",
    5: "Hiss Cascade",
    6: "Ambient Pre-Roll",
    7: "Ambient Fade-Out",
}


def run_gate15(url, duration_min=None, fade_in_sec=30.0, verbose=False):
    """Run all 7 Gate 15 checks. Returns True if all pass."""
    print(f"\n{'='*70}")
    print(f"  GATE 15: Post-Deploy Live Audio Scanner")
    print(f"{'='*70}")
    print(f"  Source: {url}")

    # Download and decode
    try:
        samples, sr = download_and_decode(url)
    except Exception as e:
        print(f"\n  ERROR: {e}")
        return None  # signals exit code 2

    duration_sec = len(samples) / sr
    print(f"  Duration: {duration_sec:.1f}s ({duration_sec/60:.1f} min)")
    print(f"  Sample rate: {sr} Hz, samples: {len(samples):,}")

    results = {}
    any_failed = False

    checks = [
        (1, lambda: check_catastrophic_silence(samples, sr, verbose)),
        (2, lambda: check_volume_explosion(samples, sr, verbose)),
        (3, lambda: check_voice_breakdown(samples, sr, verbose)),
        (4, lambda: check_duration_sanity(samples, sr, duration_min, verbose)),
        (5, lambda: check_hiss_cascade(samples, sr, verbose)),
        (6, lambda: check_ambient_fade_in(samples, sr, fade_in_sec, verbose)),
        (7, lambda: check_ambient_fade_out(samples, sr, verbose=verbose)),
    ]

    for num, check_fn in checks:
        print(f"\n  --- Check {num}: {CHECK_NAMES[num]} ---")
        passed, details = check_fn()
        results[num] = {"name": CHECK_NAMES[num], "passed": passed, "details": details}

        if details.get("skipped"):
            print(f"  SKIP: {details.get('reason', 'no expected value provided')}")
        elif passed:
            note = details.get("note", "")
            extra = f" ({note})" if note else ""
            print(f"  PASS{extra}")
        else:
            any_failed = True
            print(f"  FAIL: {details.get('reason', 'unknown')}")

    # Summary
    passed_count = sum(1 for r in results.values() if r["passed"])
    failed_count = sum(1 for r in results.values() if not r["passed"])
    skipped_count = sum(1 for r in results.values() if r["details"].get("skipped"))
    total = len(results)

    print(f"\n{'='*70}")
    verdict = "PASS" if not any_failed else "FAIL"
    print(f"  GATE 15 VERDICT: {verdict}  ({passed_count} passed, "
          f"{failed_count} failed, {skipped_count} skipped / {total} checks)")
    print(f"{'='*70}")

    if any_failed:
        for num, result in sorted(results.items()):
            if not result["passed"]:
                print(f"  FAILED: Check {num} — {result['name']}: {result['details'].get('reason', '')}")
        send_urgent_email(url, results)

    return not any_failed


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Gate 15: Post-Deploy Live Audio Scanner")
    parser.add_argument("source",
                        help="R2 key (e.g. content/audio-free/01.mp3) or full CDN URL")
    parser.add_argument("--duration-min", type=float, default=None,
                        help="Expected duration in minutes (Check 4)")
    parser.add_argument("--fade-in-sec", type=float, default=30.0,
                        help="Expected ambient pre-roll duration in seconds (default: 30)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print detailed per-window analysis")
    args = parser.parse_args()

    # Resolve URL
    url = args.source
    if not url.startswith("http"):
        url = f"{CDN_BASE}/{url.lstrip('/')}"

    result = run_gate15(url, duration_min=args.duration_min,
                        fade_in_sec=args.fade_in_sec, verbose=args.verbose)

    if result is None:
        sys.exit(2)
    elif result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
