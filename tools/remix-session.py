#!/usr/bin/env python3
"""Fast ambient remix tool for Salus sessions.

Reads session-registry.json for ambient assignments.
Uses the existing loudnormed voice master WAV (-vault-voice.wav)
and mixes with ambient — skipping all vault picking, concatenation,
loudnorm, and QA gates. Typically runs in <10 seconds per session.

Usage:
    # Remix one session with its registered ambient
    python3 tools/remix-session.py 57-21day-mindfulness-day01

    # Remix with a different ambient (override)
    python3 tools/remix-session.py 57-21day-mindfulness-day01 --ambient rain

    # Remix all sessions that need it
    python3 tools/remix-session.py --all

    # Remix + upload to R2
    python3 tools/remix-session.py --all --deploy

    # Remix a category
    python3 tools/remix-session.py --category 21day --deploy

    # Dry run (show what would be done)
    python3 tools/remix-session.py --all --dry-run
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
VAULT_DIR = PROJECT_ROOT / "content/audio-free/vault"
AMBIENT_DIR = PROJECT_ROOT / "content/audio/ambient"
SOUNDS_DIR = PROJECT_ROOT / "content/sounds"
REGISTRY_PATH = PROJECT_ROOT / "content/session-registry.json"
SAMPLE_RATE = 44100

# Per-source ambient gain (Bible v4.6 Section 11)
# Note from catalogue: birds and garden need +5dB boost (already quiet)
DEFAULT_AMBIENT_GAINS = {
    'grace': -14,
    'rain': -19,
    'garden': -14,      # -19 + 5 boost
    'birds': -9,        # -14 + 5 boost
    'stream': -8,
    'ocean': -14,
    'fire': -14,
    'waves': -14,
    'train': -14,
    'courtroom': -14,
    'harbour': -14,
    'rain-on-tent': -19,
    'childhood-memories': -14,
    'loving-kindness-ambient': -14,
}

GARDEN_OFFSET_SEC = 10  # Garden has 9.5s dead silence at start


def load_registry():
    """Load session registry."""
    with open(REGISTRY_PATH) as f:
        data = json.load(f)
    return data['sessions']


def find_ambient_file(ambient_name):
    """Find an ambient file by name. Searches ambient dir, then sounds dir."""
    for search_dir in [AMBIENT_DIR, SOUNDS_DIR]:
        candidates = [
            f"{ambient_name}-8hr.wav", f"{ambient_name}-8hr.mp3",
            f"{ambient_name}-extended.wav", f"{ambient_name}-extended.mp3",
            f"{ambient_name}.wav", f"{ambient_name}.mp3",
        ]
        for fname in candidates:
            path = search_dir / fname
            if path.exists():
                return path

    # Also check youtube-downloads
    yt_dir = AMBIENT_DIR / "youtube-downloads"
    if yt_dir.is_dir():
        for fname in candidates:
            path = yt_dir / fname
            if path.exists():
                return path

    return None


def _read_wav_as_int16(wav_path):
    """Read WAV file as mono int16 using ffmpeg."""
    result = subprocess.run(
        ['ffmpeg', '-i', str(wav_path), '-f', 's16le', '-ac', '1',
         '-ar', str(SAMPLE_RATE), '-acodec', 'pcm_s16le', '-'],
        capture_output=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to decode {wav_path}: {result.stderr[:300]}")
    samples = np.frombuffer(result.stdout, dtype=np.int16)
    return samples, SAMPLE_RATE, 1


def _load_ambient_as_mono_int16(path, offset_sec=0):
    """Load ambient file as mono int16, optionally skipping initial silence."""
    cmd = ['ffmpeg', '-i', str(path)]
    if offset_sec > 0:
        cmd = ['ffmpeg', '-ss', str(offset_sec), '-i', str(path)]
    cmd += ['-f', 's16le', '-ac', '1', '-ar', str(SAMPLE_RATE),
            '-acodec', 'pcm_s16le', '-']
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to decode ambient: {result.stderr[:300]}")
    return np.frombuffer(result.stdout, dtype=np.int16)


def _write_wav_int16(samples, sr, channels, path):
    """Write int16 samples to WAV using ffmpeg."""
    process = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 's16le', '-ar', str(sr), '-ac', str(channels),
         '-i', '-', str(path)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    process.communicate(input=samples.tobytes())
    if process.returncode != 0:
        raise RuntimeError(f"Failed to write WAV: {path}")


def mix_single_ambient(voice_samples, ambient_name, gain_db, fade_in_sec, fade_out_sec):
    """Load and prepare a single ambient layer."""
    ambient_path = find_ambient_file(ambient_name)
    if ambient_path is None:
        raise FileNotFoundError(f"No ambient file for '{ambient_name}'")

    if gain_db is None:
        gain_db = DEFAULT_AMBIENT_GAINS.get(ambient_name, -14)
    gain_linear = 10 ** (gain_db / 20.0)

    offset_sec = GARDEN_OFFSET_SEC if 'garden' in ambient_name else 0

    total_len = len(voice_samples)
    ambient_raw = _load_ambient_as_mono_int16(ambient_path, offset_sec=offset_sec)

    if len(ambient_raw) < total_len:
        # Loop the ambient if too short
        repeats = (total_len // len(ambient_raw)) + 1
        ambient_raw = np.tile(ambient_raw, repeats)

    ambient = ambient_raw[:total_len].astype(np.float64)
    ambient *= gain_linear

    # Fade-in ramp
    fade_in_samples = int(fade_in_sec * SAMPLE_RATE)
    if fade_in_samples > 0 and fade_in_samples <= len(ambient):
        ambient[:fade_in_samples] *= np.linspace(0.0, 1.0, fade_in_samples)

    # Fade-out ramp
    fade_out_samples = int(fade_out_sec * SAMPLE_RATE)
    if fade_out_samples > 0 and fade_out_samples <= len(ambient):
        ambient[-fade_out_samples:] *= np.linspace(1.0, 0.0, fade_out_samples)

    print(f"    Layer: {ambient_path.name} @ {gain_db}dB"
          f" (offset={offset_sec}s)")

    return ambient


def remix(session_id, ambient_override=None, fade_in=30, fade_out=60, dry_run=False):
    """Remix a session with its ambient.

    Returns path to final MP3, or None on failure.
    """
    registry = load_registry()
    entry = registry.get(session_id)
    if not entry:
        print(f"  SKIP: {session_id} not in registry")
        return None

    ambient_spec = ambient_override or entry.get('ambient')
    if not ambient_spec:
        print(f"  SKIP: {session_id} has no ambient assigned")
        return None

    # Find voice master
    session_dir = VAULT_DIR / session_id / "final"
    voice_wav = session_dir / f"{session_id}-vault-voice.wav"
    if not voice_wav.exists():
        # Fallback: some sessions use -vault.wav as voice-only
        voice_wav = session_dir / f"{session_id}-vault.wav"
        if not voice_wav.exists():
            print(f"  ERROR: No voice WAV found for {session_id}")
            return None

    print(f"\n{'='*60}")
    print(f"  REMIX: {session_id}")
    print(f"  Ambient: {ambient_spec}")
    print(f"  Voice: {voice_wav.name}")

    if dry_run:
        print(f"  [DRY RUN — would remix here]")
        return None

    t0 = time.time()

    # Load voice
    voice_samples, sr, nc = _read_wav_as_int16(voice_wav)
    voice_len = len(voice_samples)
    voice_dur = voice_len / sr

    # Prepend 30s silence for pre-roll
    preroll_samples = int(fade_in * sr)
    voice_with_preroll = np.concatenate([
        np.zeros(preroll_samples, dtype=np.int16),
        voice_samples
    ])
    total_len = len(voice_with_preroll)
    total_dur = total_len / sr

    print(f"  Voice: {voice_dur:.1f}s → with {fade_in}s pre-roll: {total_dur:.1f}s")

    # Parse ambient spec (supports "birds+fire" combos)
    ambient_names = [a.strip() for a in ambient_spec.split('+')]
    print(f"  Layers: {len(ambient_names)}")

    # Mix all ambient layers
    combined_ambient = np.zeros(total_len, dtype=np.float64)
    for amb_name in ambient_names:
        layer = mix_single_ambient(
            voice_with_preroll, amb_name, None, fade_in, fade_out)
        combined_ambient += layer

    # Final mix: voice + ambient
    voice_float = voice_with_preroll.astype(np.float64)
    mixed = np.clip(voice_float + combined_ambient, -32768, 32767).astype(np.int16)

    # Verify pre-roll
    def rms_db(s):
        rms = np.sqrt(np.mean(s.astype(np.float64) ** 2))
        return 20 * np.log10(max(rms, 1e-10) / 32768)

    window = int(5 * sr)
    preroll_end = int(fade_in * sr)
    if preroll_end > window:
        rms_start = rms_db(mixed[:window])
        rms_end = rms_db(mixed[preroll_end - window:preroll_end])
        print(f"  Pre-roll: 0-5s={rms_start:.1f}dB → "
              f"{fade_in-5}-{fade_in}s={rms_end:.1f}dB "
              f"({'OK' if rms_end > rms_start else 'WARNING'})")

    # Save mixed WAV
    mixed_wav = session_dir / f"{session_id}-vault.wav"
    _write_wav_int16(mixed, sr, 1, mixed_wav)

    # Encode MP3
    mixed_mp3 = session_dir / f"{session_id}-vault.mp3"
    subprocess.run(
        ['ffmpeg', '-y', '-i', str(mixed_wav),
         '-codec:a', 'libmp3lame', '-b:a', '128k',
         '-ar', '44100', '-ac', '1', str(mixed_mp3)],
        capture_output=True, timeout=120)

    mp3_size = mixed_mp3.stat().st_size / (1024 * 1024)
    elapsed = time.time() - t0
    print(f"  Output: {mixed_mp3.name} ({mp3_size:.1f} MB) in {elapsed:.1f}s")

    # Save remix metadata
    remix_log = session_dir / "remix-log.json"
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'ambient': ambient_spec,
        'fade_in': fade_in,
        'fade_out': fade_out,
        'duration_s': round(total_dur, 1),
        'mp3_size_mb': round(mp3_size, 1),
    }
    # Append to log
    log_data = []
    if remix_log.exists():
        log_data = json.loads(remix_log.read_text())
    log_data.append(log_entry)
    remix_log.write_text(json.dumps(log_data, indent=2))

    return mixed_mp3


def deploy_to_r2(session_id, mp3_path):
    """Upload MP3 to R2 and purge CDN cache."""
    r2_key = f"content/audio-free/{session_id}.mp3"
    print(f"  Uploading to R2: {r2_key}")

    result = subprocess.run(
        ['npx', 'wrangler', 'r2', 'object', 'put',
         f'salus-mind/{r2_key}',
         f'--file={mp3_path}',
         '--remote',
         '--content-type=audio/mpeg'],
        capture_output=True, text=True, timeout=120,
        cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        print(f"  ERROR uploading: {result.stderr[:200]}")
        return False

    print(f"  Upload OK")

    # Copy to local audio-free for consistency
    local_copy = PROJECT_ROOT / "content/audio-free" / f"{session_id}.mp3"
    shutil.copy2(mp3_path, local_copy)

    # Purge CDN cache
    try:
        from dotenv import load_dotenv
        import os, requests
        load_dotenv(PROJECT_ROOT / ".env")
        zone_id = os.getenv("CF_ZONE_ID")
        api_token = os.getenv("CF_API_TOKEN")
        if zone_id and api_token:
            url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
            purge_url = f"https://media.salus-mind.com/{r2_key}"
            resp = requests.post(url,
                headers={"Authorization": f"Bearer {api_token}",
                         "Content-Type": "application/json"},
                json={"files": [purge_url]})
            if resp.ok:
                print(f"  CDN purged: {purge_url}")
            else:
                print(f"  CDN purge failed: {resp.text[:100]}")
    except Exception as e:
        print(f"  CDN purge skipped: {e}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Fast ambient remix for Salus sessions')
    parser.add_argument('session_id', nargs='?',
                        help='Session ID to remix (e.g. 57-21day-mindfulness-day01)')
    parser.add_argument('--ambient', type=str, default=None,
                        help='Override ambient (e.g. rain, grace, birds+fire)')
    parser.add_argument('--all', action='store_true',
                        help='Remix all sessions in registry')
    parser.add_argument('--category', type=str, default=None,
                        help='Remix all sessions in a category (7day, 21day, cbt, etc.)')
    parser.add_argument('--fade-in', type=float, default=30,
                        help='Pre-roll duration in seconds (default: 30)')
    parser.add_argument('--fade-out', type=float, default=60,
                        help='Fade-out duration in seconds (default: 60)')
    parser.add_argument('--deploy', action='store_true',
                        help='Upload to R2 after remixing')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without doing it')
    args = parser.parse_args()

    if not args.session_id and not args.all and not args.category:
        parser.error('Specify a session_id, --all, or --category')

    registry = load_registry()

    # Build session list
    if args.all:
        sessions = [sid for sid, info in registry.items()
                     if info.get('status') == 'deployed' and info.get('ambient')]
    elif args.category:
        sessions = [sid for sid, info in registry.items()
                     if info.get('category') == args.category
                     and info.get('status') == 'deployed'
                     and info.get('ambient')]
    else:
        sessions = [args.session_id]

    print(f"Sessions to remix: {len(sessions)}")

    success = 0
    failed = 0
    skipped = 0

    for sid in sessions:
        try:
            mp3 = remix(sid, ambient_override=args.ambient,
                        fade_in=args.fade_in, fade_out=args.fade_out,
                        dry_run=args.dry_run)
            if mp3:
                success += 1
                if args.deploy and not args.dry_run:
                    deploy_to_r2(sid, mp3)
            else:
                skipped += 1
        except Exception as e:
            print(f"  FAILED: {sid} — {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"  Done: {success} remixed, {skipped} skipped, {failed} failed")


if __name__ == '__main__':
    main()
