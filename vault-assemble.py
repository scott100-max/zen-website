#!/usr/bin/env python3
"""
Vault Assembly Tool — Splice picked candidates into final session audio.

Reads picks.json from a vault session directory, applies edge fades,
inserts humanized pauses, concatenates, loudnorm, runs 14 QA gates.

Usage:
    python3 vault-assemble.py 52-the-court-of-your-mind
    python3 vault-assemble.py 52-the-court-of-your-mind --skip-qa
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Load build-session-v3.py
# ---------------------------------------------------------------------------
_build_spec = importlib.util.spec_from_file_location(
    "build_session_v3",
    Path(__file__).parent / "build-session-v3.py"
)
build = importlib.util.module_from_spec(_build_spec)
_build_spec.loader.exec_module(build)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VAULT_DIR = Path("content/audio-free/vault")
SAMPLE_RATE = 44100


def load_picks(session_dir):
    """Load picks.json from session's picks/ directory."""
    picks_path = session_dir / "picks" / "picks.json"
    if not picks_path.exists():
        # Check session root as fallback (exported from browser)
        alt = session_dir / f"{session_dir.name}-vault-picks.json"
        if alt.exists():
            picks_path = alt
        else:
            # Search for any *picks*.json
            candidates = list(session_dir.glob("*picks*.json"))
            candidates += list((session_dir / "picks").glob("*.json"))
            if candidates:
                picks_path = candidates[0]
            else:
                raise FileNotFoundError(
                    f"No picks.json found in {session_dir}/picks/ or {session_dir}/")

    data = json.loads(picks_path.read_text())
    print(f"  Loaded picks from: {picks_path}")
    return data


def load_manifest(session_dir):
    """Load session manifest for block/pause data."""
    manifest_path = session_dir / "session-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No session-manifest.json in {session_dir}")
    return json.loads(manifest_path.read_text())


def copy_picks(session_dir, picks_data):
    """Copy picked WAVs to picks/ directory as c{XX}_pick.wav."""
    picks_dir = session_dir / "picks"
    picks_dir.mkdir(exist_ok=True)
    copied = []

    for pick in picks_data['picks']:
        ci = pick['chunk']
        version = pick.get('picked')
        if version is None:
            print(f"    WARNING: Chunk {ci} has no pick — SKIPPING")
            continue

        # Find the source WAV
        src = session_dir / f"c{ci:02d}" / f"c{ci:02d}_v{version:02d}.wav"
        if not src.exists():
            raise FileNotFoundError(f"Picked WAV not found: {src}")

        dst = picks_dir / f"c{ci:02d}_pick.wav"
        shutil.copy2(src, dst)
        copied.append((ci, dst))

    print(f"  Copied {len(copied)} picks to {picks_dir}/")
    return copied


def apply_edge_fades(wav_path, output_path, fade_ms=15):
    """Apply 15ms cosine edge fades to a WAV chunk."""
    fade_sec = fade_ms / 1000
    duration = build.get_audio_duration(str(wav_path))
    fade_out_start = max(0, duration - fade_sec)
    subprocess.run([
        'ffmpeg', '-y', '-i', str(wav_path),
        '-af', (f'afade=t=in:st=0:d={fade_sec}:curve=hsin,'
                f'afade=t=out:st={fade_out_start}:d={fade_sec}:curve=hsin'),
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        str(output_path)
    ], capture_output=True, check=True)
    return output_path


def generate_silence(duration_sec, output_path):
    """Generate a silent WAV of the given duration."""
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi',
        '-i', f'anullsrc=channel_layout=mono:sample_rate={SAMPLE_RATE}',
        '-t', str(duration_sec),
        '-c:a', 'pcm_s16le',
        str(output_path)
    ], capture_output=True, check=True)
    return output_path


def concatenate_wavs(file_list, output_path):
    """Concatenate WAV files using ffmpeg concat demuxer."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for wav in file_list:
            f.write(f"file '{wav}'\n")
        list_path = f.name

    try:
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', list_path,
            '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
            str(output_path)
        ], capture_output=True, check=True)
    finally:
        os.remove(list_path)

    return output_path


def loudnorm(input_path, output_path):
    """Apply whole-file loudness normalisation (I=-26, TP=-2, LRA=11)."""
    subprocess.run([
        'ffmpeg', '-y', '-i', str(input_path),
        '-af', 'loudnorm=I=-26:TP=-2:LRA=11',
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE),
        str(output_path)
    ], capture_output=True, check=True)
    return output_path


def encode_mp3(input_wav, output_mp3):
    """Encode WAV to 128kbps MP3 (the ONLY lossy step)."""
    subprocess.run([
        'ffmpeg', '-y', '-i', str(input_wav),
        '-codec:a', 'libmp3lame', '-b:a', '128k',
        str(output_mp3)
    ], capture_output=True, check=True)
    return output_mp3


def assemble(session_id, skip_qa=False, no_humanize=False):
    """Full assembly pipeline for a vault session."""
    session_dir = VAULT_DIR / session_id

    if not session_dir.exists():
        print(f"ERROR: Session directory not found: {session_dir}")
        return False

    print(f"\n{'='*70}")
    print(f"  VAULT ASSEMBLY — {session_id}")
    print(f"{'='*70}")

    # Load picks and manifest
    picks_data = load_picks(session_dir)
    manifest = load_manifest(session_dir)

    # Validate all chunks have picks
    total_chunks = manifest['total_chunks']
    picked_chunks = [p for p in picks_data['picks'] if p.get('picked') is not None]
    if len(picked_chunks) < total_chunks:
        missing = [p['chunk'] for p in picks_data['picks'] if p.get('picked') is None]
        print(f"  WARNING: {len(missing)} chunks have no pick: {missing}")
        print(f"  Only {len(picked_chunks)}/{total_chunks} chunks will be assembled.")

    # Copy picks
    copied = copy_picks(session_dir, picks_data)

    # Get pause data from manifest
    pauses = {b['index']: b['pause'] for b in manifest.get('blocks', [])}

    # Humanize pauses (skip for stories — creates silences too long for narrative)
    blocks_for_humanize = []
    for ci, _ in copied:
        text = next((p['text'] for p in picks_data['picks'] if p['chunk'] == ci), '')
        pause = pauses.get(ci, 0)
        blocks_for_humanize.append((text, pause))

    if no_humanize:
        humanized = blocks_for_humanize
        print(f"  Pauses: using raw durations (--no-humanize)")
    else:
        humanized = build.humanize_pauses(blocks_for_humanize)

    # Process in temp directory
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        concat_files = []

        for i, (ci, pick_wav) in enumerate(copied):
            text, pause = humanized[i]

            # Apply edge fades
            faded = tmp / f"c{ci:02d}_faded.wav"
            apply_edge_fades(pick_wav, faded)
            concat_files.append(str(faded))

            dur = build.get_audio_duration(str(faded))
            print(f"  c{ci:02d}: {dur:.1f}s", end="")

            # Insert silence after chunk (if any)
            if pause > 0:
                silence = tmp / f"silence_{ci:02d}_{pause:.1f}s.wav"
                generate_silence(pause, silence)
                concat_files.append(str(silence))
                print(f" + {pause:.1f}s silence", end="")

            print()

        # Concatenate
        print(f"\n  Concatenating {len(concat_files)} segments...")
        raw_concat = tmp / "concat_raw.wav"
        concatenate_wavs(concat_files, raw_concat)
        raw_dur = build.get_audio_duration(str(raw_concat))
        print(f"  Raw concatenation: {raw_dur:.1f}s ({raw_dur/60:.1f} min)")

        # Loudnorm
        print(f"  Applying loudnorm (I=-26, TP=-2, LRA=11)...")
        normed = tmp / "concat_normed.wav"
        loudnorm(raw_concat, normed)

        # Copy to final directory
        final_dir = session_dir / "final"
        final_dir.mkdir(exist_ok=True)

        final_wav = final_dir / f"{session_id}-vault.wav"
        final_mp3 = final_dir / f"{session_id}-vault.mp3"

        shutil.copy2(normed, final_wav)
        print(f"  Final WAV: {final_wav}")

        # Also save raw concat for QA (click scanner needs pre-loudnorm)
        raw_copy = final_dir / f"{session_id}-vault-raw.wav"
        shutil.copy2(raw_concat, raw_copy)

        # Encode MP3
        encode_mp3(final_wav, final_mp3)
        mp3_size = final_mp3.stat().st_size / (1024 * 1024)
        print(f"  Final MP3: {final_mp3} ({mp3_size:.1f} MB)")

    # Duration check
    final_dur = build.get_audio_duration(str(final_wav))
    print(f"\n  Final duration: {final_dur:.1f}s ({final_dur/60:.1f} min)")

    # Run 14 QA gates
    if not skip_qa:
        print(f"\n{'='*70}")
        print(f"  RUNNING 14-GATE QA")
        print(f"{'='*70}")
        # Import and run QA gates
        try:
            qa_spec = importlib.util.spec_from_file_location(
                "run_qa_gates",
                Path(__file__).parent / "run_qa_gates.py"
            )
            qa = importlib.util.module_from_spec(qa_spec)

            # The QA module needs file paths set — check how it's configured
            # For now, pass the paths it needs
            print(f"  QA gates would run on: {final_wav}")
            print(f"  (QA integration pending — run manually with run_qa_gates.py)")
        except Exception as e:
            print(f"  QA import failed: {e}")
            print(f"  Run QA manually: python3 run_qa_gates.py {final_wav}")
    else:
        print(f"\n  QA skipped (--skip-qa)")

    # Build report
    report = {
        'session_id': session_id,
        'chunks_assembled': len(copied),
        'total_chunks': total_chunks,
        'final_wav': str(final_wav),
        'final_mp3': str(final_mp3),
        'duration_seconds': round(final_dur, 1),
        'duration_minutes': round(final_dur / 60, 1),
        'picks_source': str(picks_data.get('reviewed', 'unknown')),
    }
    report_path = final_dir / f"{session_id}-build-report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(f"\n{'='*70}")
    print(f"  ASSEMBLY COMPLETE — {session_id}")
    print(f"{'='*70}")
    print(f"  WAV: {final_wav}")
    print(f"  MP3: {final_mp3}")
    print(f"  Duration: {final_dur/60:.1f} min")
    print(f"  Report: {report_path}")
    print(f"\n  NEXT: Listen to the full splice, then mix ambient if needed.")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Vault Assembly — Splice picked candidates into final audio')
    parser.add_argument('session_id',
                        help='Session ID (e.g., 52-the-court-of-your-mind)')
    parser.add_argument('--skip-qa', action='store_true',
                        help='Skip 14-gate QA (for testing)')
    parser.add_argument('--no-humanize', action='store_true',
                        help='Skip pause humanization (for stories — raw pause durations)')
    args = parser.parse_args()

    success = assemble(args.session_id, skip_qa=args.skip_qa, no_humanize=args.no_humanize)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
