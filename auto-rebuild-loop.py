#!/usr/bin/env python3
"""
Auto-Rebuild Loop — Iteratively rechunk failing chunks until QA passes.

Runs: auto-picker → vault-assemble → QA analysis → detect failures → rechunk → repeat
Stops when: all QA gates pass (except duration/ambient) OR max rounds reached.

Usage:
    python3 auto-rebuild-loop.py 01-morning-meditation
    python3 auto-rebuild-loop.py 01-morning-meditation --max-rounds 20
    python3 auto-rebuild-loop.py 01-morning-meditation --rechunk 3,6,7,9,11  # start with known failures
"""

import argparse
import json
import subprocess
import sys
import shutil
import numpy as np
from pathlib import Path
from datetime import datetime

VAULT_DIR = Path("content/audio-free/vault")
SAMPLE_RATE = 44100


def run_auto_picker(session_id, rechunk_indices=None):
    """Run auto-picker, optionally with --rechunk."""
    cmd = ["python3", "auto-picker.py", session_id]
    if rechunk_indices:
        cmd += ["--rechunk", ",".join(str(i) for i in sorted(rechunk_indices))]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print(f"  AUTO-PICKER FAILED: {result.stderr[-300:]}")
        return False
    return True


def filter_and_save_picks(session_id, max_chunk=25):
    """Filter picks-auto.json to max_chunk and save as picks/picks.json."""
    vault = VAULT_DIR / session_id
    auto_picks = json.load(open(vault / "picks-auto.json"))
    filtered = [p for p in auto_picks["picks"] if p["chunk"] <= max_chunk]
    auto_picks["picks"] = filtered
    with open(vault / "picks" / "picks.json", "w") as f:
        json.dump(auto_picks, f, indent=2)
    return len(filtered)


def run_assembly(session_id):
    """Run vault-assemble and return build report."""
    result = subprocess.run(
        ["python3", "vault-assemble.py", session_id],
        capture_output=True, text=True
    )
    # Print last part of output
    lines = result.stdout.strip().split("\n")
    for line in lines[-15:]:
        print(f"  {line}")

    vault = VAULT_DIR / session_id
    report_path = vault / "final" / f"{session_id}-build-report.json"
    if report_path.exists():
        return json.load(open(report_path))
    return None


def detect_hf_spikes(wav_path, manifest_path):
    """
    Run HF spike detection on assembled audio (Gate 3/9 logic).
    Returns list of (chunk_index, spike_time, hf_ratio) for detected spikes.
    """
    import wave as _wave
    from scipy.signal import butter, sosfilt

    # Load audio
    w = _wave.open(str(wav_path), 'r')
    n_frames = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw_data = w.readframes(n_frames)
    w.close()

    samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)

    # 4th-order Butterworth highpass at 4kHz
    sos_hf = butter(4, 4000, btype='high', fs=sr, output='sos')
    hf_signal = sosfilt(sos_hf, samples)

    # 2s sliding window, 1s hop
    win_samples = int(2.0 * sr)
    hop = int(1.0 * sr)

    hf_energies = []
    times = []
    for start in range(0, len(samples) - win_samples, hop):
        hf_chunk = hf_signal[start:start + win_samples]
        hf_energies.append(float(np.mean(hf_chunk ** 2)))
        times.append(start / sr)

    hf_energies = np.array(hf_energies)
    times = np.array(times)

    # Load manifest for speech regions
    manifest = json.load(open(manifest_path))
    speech_ranges = []
    for seg in manifest["segments"]:
        if seg["type"] == "text":
            speech_ranges.append((seg["start_time"], seg["end_time"], seg.get("index")))

    # Speech mask
    speech_mask = np.zeros(len(times), dtype=bool)
    for i, t in enumerate(times):
        for s_start, s_end, _ in speech_ranges:
            if s_start <= t < s_end:
                speech_mask[i] = True
                break

    speech_hf = hf_energies[speech_mask & (hf_energies > 0)]
    if len(speech_hf) < 5:
        return []

    median_hf = float(np.median(speech_hf))
    if median_hf <= 0:
        return []

    # Find spikes > 20x median (slightly looser than Gate 9's 28x to catch more)
    spikes = []
    for i in range(len(times)):
        if not speech_mask[i]:
            continue
        ratio = hf_energies[i] / median_hf if median_hf > 0 else 0
        if ratio > 20.0:
            t = times[i]
            # Map to chunk index
            chunk_idx = None
            for s_start, s_end, idx in speech_ranges:
                if s_start - 1 <= t <= s_end + 1:
                    chunk_idx = idx
                    break
            if chunk_idx is not None:
                spikes.append((chunk_idx, float(t), float(ratio)))

    # Deduplicate by chunk
    seen = set()
    unique = []
    for idx, t, ratio in spikes:
        if idx not in seen:
            seen.add(idx)
            unique.append((idx, t, ratio))

    return unique


def detect_cutoff_candidates(session_id, picks_data):
    """Check for candidates that are suspiciously short (possible cutoff)."""
    vault = VAULT_DIR / session_id
    suspects = []

    for pick in picks_data["picks"]:
        ci = pick["chunk"]
        ver = pick.get("picked")
        if ver is None or pick.get("locked"):
            continue

        text = pick["text"]
        expected_min = len(text) / 13  # Fish speaks 10-13 chars/sec, use fast end
        expected_max = len(text) / 8   # Slow end with pauses

        wav_path = vault / f"c{ci:02d}" / f"c{ci:02d}_v{ver:02d}.wav"
        if not wav_path.exists():
            continue

        try:
            import wave as _wave
            w = _wave.open(str(wav_path), 'r')
            dur = w.getnframes() / w.getframerate()
            w.close()

            if dur < expected_min * 0.5:  # Less than half expected minimum
                suspects.append((ci, dur, expected_min, "too_short"))
            elif dur > expected_max * 2.0:  # More than double expected maximum
                suspects.append((ci, dur, expected_max, "too_long"))
        except:
            pass

    return suspects


def main():
    parser = argparse.ArgumentParser(description="Auto-rebuild loop")
    parser.add_argument("session_id")
    parser.add_argument("--max-rounds", type=int, default=15)
    parser.add_argument("--rechunk", type=str, default=None,
                        help="Starting rechunk indices (comma-separated)")
    parser.add_argument("--max-chunk", type=int, default=25,
                        help="Maximum chunk index to include")
    args = parser.parse_args()

    session_id = args.session_id
    vault = VAULT_DIR / session_id

    if not vault.exists():
        print(f"ERROR: Session not found: {vault}")
        sys.exit(1)

    # Parse initial rechunk set
    rechunk_set = None
    if args.rechunk:
        rechunk_set = set(int(x) for x in args.rechunk.split(","))

    print(f"\n{'='*70}")
    print(f"  AUTO-REBUILD LOOP — {session_id}")
    print(f"  Max rounds: {args.max_rounds}, Max chunk: {args.max_chunk}")
    if rechunk_set:
        print(f"  Starting rechunk: {sorted(rechunk_set)}")
    print(f"{'='*70}\n")

    # Track history
    history = []
    all_failed_versions = {}  # chunk_idx -> set of failed versions
    best_score = 0
    best_round = 0
    consecutive_no_improve = 0

    for round_num in range(1, args.max_rounds + 1):
        print(f"\n{'─'*50}")
        print(f"  ROUND {round_num}")
        print(f"{'─'*50}")

        # Step 1: Auto-pick
        print(f"\n  [1/4] Auto-picking...")
        if not run_auto_picker(session_id, rechunk_set):
            print(f"  ABORT: Auto-picker failed")
            break

        n_picks = filter_and_save_picks(session_id, args.max_chunk)
        print(f"  Filtered to {n_picks} picks")

        # Step 2: Assemble
        print(f"\n  [2/4] Assembling...")
        report = run_assembly(session_id)
        if not report:
            print(f"  ABORT: Assembly failed")
            break

        # Step 3: Detect issues
        print(f"\n  [3/4] Analyzing for issues...")

        final_dir = vault / "final"
        wav_path = final_dir / f"{session_id}-vault.wav"
        manifest_path = final_dir / "assembly-manifest.json"

        # HF spike detection (echo)
        hf_spikes = detect_hf_spikes(wav_path, manifest_path)
        echo_chunks = set()
        if hf_spikes:
            print(f"  HF SPIKES DETECTED:")
            for idx, t, ratio in hf_spikes:
                m, s = int(t // 60), t % 60
                print(f"    c{idx:02d} @ {m}:{s:04.1f} — {ratio:.1f}x median")
                echo_chunks.add(idx)
        else:
            print(f"  No HF spikes — echo-clean")

        # Cutoff detection
        picks_data = json.load(open(vault / "picks" / "picks.json"))
        cutoff_suspects = detect_cutoff_candidates(session_id, picks_data)
        cutoff_chunks = set()
        if cutoff_suspects:
            print(f"  CUTOFF SUSPECTS:")
            for ci, dur, expected, issue in cutoff_suspects:
                print(f"    c{ci:02d}: {dur:.1f}s ({issue}, expected ~{expected:.1f}s)")
                cutoff_chunks.add(ci)

        # Combine failures
        auto_failures = echo_chunks | cutoff_chunks

        # QA gate summary
        qa = report.get("qa_summary", {})
        gates_failed = [k for k, v in qa.items() if not v.get("passed", True) and not v.get("skipped", False)]
        # Exclude gate 12 (duration) and 13 (ambient) from failure count
        real_failures = [g for g in gates_failed if g not in ("12", "13")]

        n_pass = sum(1 for v in qa.values() if v.get("passed", False))
        n_fail = len(real_failures)

        score = n_pass
        round_info = {
            "round": round_num,
            "gates_pass": n_pass,
            "gates_fail": n_fail,
            "echo_chunks": sorted(echo_chunks),
            "cutoff_chunks": sorted(cutoff_chunks),
            "auto_failures": sorted(auto_failures),
        }
        history.append(round_info)

        print(f"\n  QA: {n_pass} pass, {n_fail} fail (excluding duration/ambient)")
        print(f"  Auto-detected failures: {sorted(auto_failures) if auto_failures else 'NONE'}")

        # Step 4: Decide next action
        if not auto_failures and n_fail == 0:
            print(f"\n  ALL GATES PASS — stopping loop")
            break

        if not auto_failures:
            print(f"\n  No auto-detectable failures remaining.")
            print(f"  Remaining QA failures are beyond auto-detection (need human ears).")
            print(f"  Stopping loop — ready for human review.")
            break

        # Track failed versions
        for ci in auto_failures:
            pick = next((p for p in picks_data["picks"] if p["chunk"] == ci), None)
            if pick:
                ver = pick.get("picked")
                if ver is not None:
                    if ci not in all_failed_versions:
                        all_failed_versions[ci] = set()
                    all_failed_versions[ci].add(ver)

        # Check for improvement
        if score > best_score:
            best_score = score
            best_round = round_num
            consecutive_no_improve = 0
            # Save best assembly
            best_dir = vault / "final" / "best"
            best_dir.mkdir(exist_ok=True)
            for f in final_dir.glob(f"{session_id}*"):
                if f.is_file():
                    shutil.copy2(f, best_dir / f.name)
            print(f"  New best: round {round_num} (score {score})")
        else:
            consecutive_no_improve += 1
            if consecutive_no_improve >= 5:
                print(f"\n  No improvement for 5 rounds — stopping")
                break

        # Set up rechunk for next round
        rechunk_set = auto_failures
        print(f"\n  Rechunking {sorted(rechunk_set)} for round {round_num + 1}...")

    # Summary
    print(f"\n{'='*70}")
    print(f"  AUTO-REBUILD COMPLETE — {session_id}")
    print(f"{'='*70}")
    print(f"  Rounds: {len(history)}")
    print(f"  Best round: {best_round} (score {best_score})")

    if all_failed_versions:
        print(f"  Failed versions accumulated:")
        for ci in sorted(all_failed_versions):
            vers = sorted(all_failed_versions[ci])
            print(f"    c{ci:02d}: {len(vers)} versions tried — {vers}")

    # Save loop log
    log_path = vault / "final" / "auto-rebuild-log.json"
    log = {
        "session_id": session_id,
        "completed": datetime.now().isoformat(),
        "rounds": history,
        "best_round": best_round,
        "failed_versions": {str(k): sorted(v) for k, v in all_failed_versions.items()},
    }
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"  Log: {log_path}")

    # Final audio
    mp3 = vault / "final" / f"{session_id}-vault.mp3"
    print(f"  Audio: {mp3}")
    print(f"\n  Ready for human review of remaining non-auto-detectable issues.")


if __name__ == "__main__":
    main()
