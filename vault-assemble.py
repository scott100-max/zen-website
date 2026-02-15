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
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

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
AMBIENT_DIR = Path("content/audio/ambient")
SAMPLE_RATE = 44100

# Per-source ambient gain (Bible v4.6 Section 11)
DEFAULT_AMBIENT_GAINS = {
    'grace': -12,
    'rain-8hr': -19,
    'rain': -19,
    'garden-8hr': -19,
    'garden': -19,
    'birds-8hr': -14,
    'birds': -14,
    'stream': -8,
    'stream-3hr': -8,
    'stream-extended': -8,
}

# Garden ambient has 9.5s dead silence at start (Bible Production Rule 16)
GARDEN_OFFSET_SEC = 10

# CDN cache purge — load from .env
_env_path = Path(__file__).parent / ".env"
_env_vars = {}
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            _env_vars[k.strip()] = v.strip()
CF_CACHE_PURGE_TOKEN = _env_vars.get('CF_CACHE_PURGE_TOKEN', '')
CF_ZONE_ID = _env_vars.get('CF_ZONE_ID', '')
CDN_BASE = "https://media.salus-mind.com"


def purge_cdn_cache(r2_key):
    """Purge a specific file from Cloudflare CDN cache after R2 upload.

    Purges both the base URL and any ?v= query string variants found in
    HTML files, since Cloudflare caches each query string as a separate object.
    """
    if not CF_CACHE_PURGE_TOKEN or not CF_ZONE_ID:
        print("  WARNING: CDN purge skipped — CF_CACHE_PURGE_TOKEN/CF_ZONE_ID not set in .env")
        return False

    # Collect all URLs to purge: base + any ?v= variants in HTML
    purge_urls = [f"{CDN_BASE}/{r2_key}"]
    project_root = Path(__file__).parent
    for html_dir in [project_root, project_root / "sessions", project_root / "articles",
                     project_root / "newsletters"]:
        if html_dir.is_dir():
            for html_file in html_dir.glob("*.html"):
                try:
                    content = html_file.read_text()
                    # Find r2_key?v=... patterns
                    import re as _re
                    for match in _re.finditer(_re.escape(r2_key) + r'\?v=[^"\'&\s]+', content):
                        variant_url = f"{CDN_BASE}/{match.group()}"
                        if variant_url not in purge_urls:
                            purge_urls.append(variant_url)
                except Exception:
                    pass

    import urllib.request
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/purge_cache"
    data = json.dumps({"files": purge_urls}).encode()
    req = urllib.request.Request(url, data=data, method='POST', headers={
        'Authorization': f'Bearer {CF_CACHE_PURGE_TOKEN}',
        'Content-Type': 'application/json',
    })
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        if result.get('success'):
            print(f"  CDN purge: OK — {len(purge_urls)} URL(s) purged ({CDN_BASE}/{r2_key})")
            return True
        else:
            print(f"  CDN purge: FAILED — {result}")
            return False
    except Exception as e:
        print(f"  CDN purge: ERROR — {e}")
        return False


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


def apply_closing_tail_fade(wav_path, output_path, fade_ms=150):
    """Apply 150ms fade-out to closing chunk WAV (Bible Section 13).

    Fish truncates final generations regardless of text. The tail fade
    smooths any abrupt ending on the last chunk of a session.
    """
    fade_sec = fade_ms / 1000
    duration = build.get_audio_duration(str(wav_path))
    fade_out_start = max(0, duration - fade_sec)
    subprocess.run([
        'ffmpeg', '-y', '-i', str(wav_path),
        '-af', f'afade=t=out:st={fade_out_start}:d={fade_sec}:curve=hsin',
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


def _read_wav_as_int16(wav_path):
    """Read a WAV file and return (samples_int16, sample_rate, n_channels)."""
    with wave.open(str(wav_path), 'rb') as wf:
        sr = wf.getframerate()
        nc = wf.getnchannels()
        frames = wf.readframes(wf.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16)
    return samples, sr, nc


def _write_wav_int16(samples, sample_rate, n_channels, output_path):
    """Write int16 samples to a WAV file."""
    with wave.open(str(output_path), 'wb') as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(samples.astype(np.int16).tobytes())


def _load_ambient_as_mono_int16(ambient_path, offset_sec=0):
    """Load an ambient file (MP3 or WAV) as mono int16 numpy array.

    Uses ffmpeg to decode to raw PCM, skipping offset_sec from start.
    """
    cmd = ['ffmpeg', '-y']
    if offset_sec > 0:
        cmd += ['-ss', str(offset_sec)]
    cmd += [
        '-i', str(ambient_path),
        '-ac', '1', '-ar', str(SAMPLE_RATE),
        '-f', 's16le', '-acodec', 'pcm_s16le',
        'pipe:1'
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to decode ambient: {result.stderr[:500]}")
    return np.frombuffer(result.stdout, dtype=np.int16)


def find_ambient_file(ambient_name):
    """Find an ambient file by name, preferring 8hr versions then extended."""
    project_root = Path(__file__).parent
    ambient_dir = project_root / AMBIENT_DIR

    # Search order per Bible: -8hr → -extended → base name. WAV before MP3.
    candidates = [
        f"{ambient_name}-8hr.wav", f"{ambient_name}-8hr.mp3",
        f"{ambient_name}-extended.wav", f"{ambient_name}-extended.mp3",
        f"{ambient_name}.wav", f"{ambient_name}.mp3",
    ]
    for fname in candidates:
        path = ambient_dir / fname
        if path.exists():
            return path

    # Also check youtube-downloads
    yt_dir = ambient_dir / "youtube-downloads"
    if yt_dir.is_dir():
        for fname in candidates:
            path = yt_dir / fname
            if path.exists():
                return path

    return None


def mix_ambient(voice_wav, ambient_name, output_wav, gain_db=None,
                fade_in_sec=30, fade_out_sec=60):
    """Mix ambient into voice track using numpy direct addition.

    Bible v4.6 pipeline (Section 11, Section 16D):
      voice WAV → prepend 30s silence → loudnorm voice-only → mix ambient → MP3

    This function handles: prepend silence + mix ambient (post-loudnorm).
    The input voice_wav should ALREADY be loudnormed.

    Args:
        voice_wav: Path to loudnormed voice-only WAV
        ambient_name: Name of ambient source (e.g. 'grace', 'rain', 'garden')
        output_wav: Path for mixed output WAV
        gain_db: Ambient gain in dB (negative). If None, uses DEFAULT_AMBIENT_GAINS.
        fade_in_sec: Ambient fade-in duration (structural pre-roll). Default 30s.
        fade_out_sec: Ambient fade-out duration. Default 60s.
    """
    # Find ambient file
    ambient_path = find_ambient_file(ambient_name)
    if ambient_path is None:
        raise FileNotFoundError(
            f"No ambient file found for '{ambient_name}' in {AMBIENT_DIR}")

    # Determine gain
    if gain_db is None:
        gain_db = DEFAULT_AMBIENT_GAINS.get(ambient_name, -14)
    gain_linear = 10 ** (gain_db / 20.0)

    # Determine garden offset
    offset_sec = GARDEN_OFFSET_SEC if 'garden' in ambient_name else 0

    print(f"  Ambient: {ambient_path.name} @ {gain_db}dB"
          f" (fade-in={fade_in_sec}s, fade-out={fade_out_sec}s)")
    if offset_sec:
        print(f"  Garden offset: skipping first {offset_sec}s")

    # Load voice (already loudnormed)
    voice_samples, sr, nc = _read_wav_as_int16(voice_wav)
    voice_len = len(voice_samples)

    # Prepend structural pre-roll silence (voice delayed by fade_in_sec)
    preroll_samples = int(fade_in_sec * sr)
    silence_preroll = np.zeros(preroll_samples, dtype=np.int16)

    # Append post-roll silence (ambient fades out after voice ends)
    postroll_samples = int(fade_out_sec * sr)
    silence_postroll = np.zeros(postroll_samples, dtype=np.int16)

    voice_with_preroll = np.concatenate([silence_preroll, voice_samples, silence_postroll])
    total_len = len(voice_with_preroll)

    voice_dur = voice_len / sr
    total_dur = total_len / sr
    print(f"  Voice: {voice_dur:.1f}s → with {fade_in_sec}s pre-roll + {fade_out_sec}s post-roll: {total_dur:.1f}s")

    # Load ambient
    ambient_raw = _load_ambient_as_mono_int16(ambient_path, offset_sec=offset_sec)
    if len(ambient_raw) < total_len:
        raise ValueError(
            f"Ambient too short ({len(ambient_raw)/sr:.0f}s) for voice "
            f"({total_dur:.0f}s). Bible: ambient must be longer than voice, NEVER loop.")

    # Trim ambient to match voice length
    ambient = ambient_raw[:total_len].astype(np.float64)

    # Apply gain
    ambient *= gain_linear

    # Apply fade-in ramp (linear, over first fade_in_sec)
    fade_in_samples = int(fade_in_sec * sr)
    if fade_in_samples > 0 and fade_in_samples <= len(ambient):
        fade_in_ramp = np.linspace(0.0, 1.0, fade_in_samples)
        ambient[:fade_in_samples] *= fade_in_ramp

    # Apply fade-out ramp (linear, over last fade_out_sec)
    fade_out_samples = int(fade_out_sec * sr)
    if fade_out_samples > 0 and fade_out_samples <= len(ambient):
        fade_out_ramp = np.linspace(1.0, 0.0, fade_out_samples)
        ambient[-fade_out_samples:] *= fade_out_ramp

    # Mix using numpy direct addition (Bible: NEVER use ffmpeg amix)
    voice_float = voice_with_preroll.astype(np.float64)
    mixed = np.clip(voice_float + ambient, -32768, 32767).astype(np.int16)

    # Write output
    _write_wav_int16(mixed, sr, 1, output_wav)

    # Verification checklist (Bible Section 11)
    _verify_mix(mixed, sr, fade_in_sec, voice_dur)

    mixed_dur = len(mixed) / sr
    print(f"  Mixed output: {mixed_dur:.1f}s ({mixed_dur/60:.1f} min)")
    return output_wav


def _verify_mix(mixed, sr, fade_in_sec, voice_dur):
    """Run Bible verification checklist on the mixed audio."""
    def rms_db(samples):
        rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
        return 20 * np.log10(max(rms, 1e-10) / 32768)

    # Check 1: Pre-roll RMS should rise from ~-76dB to ~-38dB over fade_in_sec
    window = int(5 * sr)  # 5s windows
    preroll_end = int(fade_in_sec * sr)
    if preroll_end > window:
        rms_start = rms_db(mixed[:window])
        rms_end = rms_db(mixed[preroll_end - window:preroll_end])
        print(f"  Verify: Pre-roll RMS 0-5s={rms_start:.1f}dB, "
              f"{fade_in_sec-5}-{fade_in_sec}s={rms_end:.1f}dB "
              f"(should rise)")
        if rms_end <= rms_start:
            print(f"  WARNING: Pre-roll RMS not rising — check ambient mix")

    # Check 2: Voice entry should show >20dB RMS jump
    voice_start = preroll_end
    if voice_start + window < len(mixed):
        rms_before = rms_db(mixed[voice_start - window:voice_start])
        rms_after = rms_db(mixed[voice_start:voice_start + window])
        jump = rms_after - rms_before
        print(f"  Verify: Voice entry RMS jump={jump:.1f}dB (should be >20dB)")

    # Check 3: Tail should fade
    tail_5s = int(5 * sr)
    if len(mixed) > tail_5s:
        rms_tail = rms_db(mixed[-tail_5s:])
        print(f"  Verify: Tail 5s RMS={rms_tail:.1f}dB (should be < -60dB)")


def conditioning_chain_hf_scan(wav_path, window_sec=10, threshold_db=-36):
    """Post-assembly sequential HF scan for conditioning chain contamination (L-30).

    Bible Production Rule 19: No vault-assembled session deploys without this scan.
    Scans 10-second windows for HF energy above threshold. A single hissy chunk
    can cascade through the entire session via Fish conditioning.

    Returns (passed, flagged_windows) where flagged_windows is a list of
    (start_sec, end_sec, hf_db) tuples.
    """
    samples, sr, nc = _read_wav_as_int16(wav_path)
    samples_float = samples.astype(np.float64) / 32768.0

    window_samples = int(window_sec * sr)
    total_samples = len(samples_float)
    flagged = []

    for start in range(0, total_samples - window_samples, window_samples):
        chunk = samples_float[start:start + window_samples]

        # Compute FFT and get HF energy (above 4kHz)
        fft = np.fft.rfft(chunk)
        freqs = np.fft.rfftfreq(len(chunk), 1.0 / sr)
        hf_mask = freqs >= 4000
        hf_energy = np.mean(np.abs(fft[hf_mask]) ** 2)
        hf_db = 10 * np.log10(max(hf_energy, 1e-20))

        start_sec = start / sr
        end_sec = (start + window_samples) / sr

        if hf_db > threshold_db:
            flagged.append((start_sec, end_sec, hf_db))

    passed = len(flagged) == 0
    if passed:
        print(f"  HF scan: PASS — no windows above {threshold_db}dB")
    else:
        print(f"  HF scan: FAIL — {len(flagged)} window(s) above {threshold_db}dB")
        for s, e, db in flagged[:5]:
            print(f"    {s:.0f}-{e:.0f}s: HF={db:.1f}dB")
        if len(flagged) > 5:
            print(f"    ... and {len(flagged) - 5} more")

    return passed, flagged


def run_vault_qa(session_id, final_wav, raw_wav, final_mp3, assembly_manifest,
                 metadata, output_dir):
    """Run post-assembly QA gates (1,2,3,5,7,8,9,10,11,12,13) per Bible v4.1.

    Gates 4, 6, 14 are pre-vault advisory only (handled by human A/B picking).
    Returns True if all gates pass, False otherwise.
    """
    gate_results = {}
    any_failed = False
    normed = str(final_wav)
    raw = str(raw_wav)

    # Gate 1: Quality Benchmarks
    print(f"\n  --- Gate 1: Quality Benchmarks ---")
    passed, details = build.qa_quality_check(normed, assembly_manifest)
    gate_results[1] = {'name': 'Quality Benchmarks', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Gate 2: Click Scan (detection only — no auto-patching in vault)
    print(f"\n  --- Gate 2: Click Artifacts ---")
    clicks = build.scan_for_clicks(normed, assembly_manifest)
    passed = len(clicks) == 0
    gate_results[2] = {'name': 'Click Artifacts', 'passed': passed,
                       'details': {'clicks_found': len(clicks), 'clicks': clicks}}
    if not passed:
        any_failed = True
        print(f"  FAIL: {len(clicks)} click(s) detected")
    else:
        print(f"  PASS: No clicks detected")

    # Gate 3: Spectral Comparison
    print(f"\n  --- Gate 3: Spectral Comparison ---")
    passed, details = build.qa_independent_check(normed, assembly_manifest)
    gate_results[3] = {'name': 'Spectral Comparison', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Gate 5: Loudness Consistency
    print(f"\n  --- Gate 5: Loudness Consistency ---")
    passed, details = build.qa_loudness_consistency_check(normed, assembly_manifest)
    gate_results[5] = {'name': 'Loudness Consistency', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Gate 7: Volume Surge/Drop (raw pre-loudnorm for natural dynamics)
    print(f"\n  --- Gate 7: Volume Surge/Drop ---")
    passed, details = build.qa_volume_surge_check(raw, assembly_manifest)
    gate_results[7] = {'name': 'Volume Surge/Drop', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Gate 8: Repeated Content
    print(f"\n  --- Gate 8: Repeated Content ---")
    expected_reps = metadata.get('expected_repetitions')
    passed, details = build.qa_repeated_content_check(normed, assembly_manifest,
                                                       expected_repetitions=expected_reps)
    gate_results[8] = {'name': 'Repeated Content', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Gate 10: Speech Rate
    print(f"\n  --- Gate 10: Speech Rate ---")
    passed, details = build.qa_speech_rate_check(normed, assembly_manifest)
    gate_results[10] = {'name': 'Speech Rate', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Gate 11: Silence Integrity
    print(f"\n  --- Gate 11: Silence Integrity ---")
    passed, details = build.qa_silence_integrity_check(normed, assembly_manifest)
    gate_results[11] = {'name': 'Silence Integrity', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Gate 12: Duration Accuracy
    print(f"\n  --- Gate 12: Duration Accuracy ---")
    passed, details = build.qa_duration_accuracy_check(str(final_mp3), metadata)
    gate_results[12] = {'name': 'Duration Accuracy', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Gate 13: Ambient Continuity — skipped (ambient not mixed yet at assembly)
    print(f"\n  --- Gate 13: Ambient Continuity --- SKIPPED (pre-ambient)")
    gate_results[13] = {'name': 'Ambient Continuity', 'passed': True, 'skipped': True}

    # Gate 9: Energy Spike + Visual Report (always last — uses cumulative results)
    print(f"\n  --- Gate 9: Energy Spike + Visual Report ---")
    g9_input = {f"Gate {k}: {v['name']}": v for k, v in gate_results.items()}
    passed, details, report_path = build.qa_visual_report(
        normed, assembly_manifest, session_id, g9_input, output_dir=str(output_dir))
    gate_results[9] = {'name': 'Energy Spike', 'passed': passed, 'details': details}
    if not passed:
        any_failed = True

    # Summary
    passed_count = sum(1 for v in gate_results.values()
                       if v.get('passed') and not v.get('skipped'))
    failed_count = sum(1 for v in gate_results.values()
                       if not v.get('passed'))
    skipped_count = sum(1 for v in gate_results.values() if v.get('skipped'))
    total = len(gate_results)

    print(f"\n{'='*70}")
    verdict = "PASS" if not any_failed else "FAIL"
    print(f"  QA VERDICT: {verdict}  ({passed_count} passed, "
          f"{failed_count} failed, {skipped_count} skipped / {total} gates)")
    print(f"{'='*70}")

    if any_failed:
        for gnum, result in sorted(gate_results.items()):
            if not result.get('passed'):
                print(f"  FAILED: Gate {gnum} — {result['name']}")

    return not any_failed, gate_results


def assemble(session_id, skip_qa=False, no_humanize=False,
             ambient=None, ambient_gain=None, fade_in=30, fade_out=60,
             picks_path=None, output_dir=None):
    """Full assembly pipeline for a vault session.

    Bible v4.6 Section 16D pipeline:
      voice WAV → prepend silence → loudnorm voice-only →
      mix ambient (post-loudnorm, numpy) → MP3 (no second loudnorm)
    """
    session_dir = VAULT_DIR / session_id

    if not session_dir.exists():
        print(f"ERROR: Session directory not found: {session_dir}")
        return False

    print(f"\n{'='*70}")
    print(f"  VAULT ASSEMBLY — {session_id}")
    print(f"{'='*70}")

    # Load picks and manifest
    if picks_path:
        picks_data = json.loads(Path(picks_path).read_text())
        print(f"  Loaded picks from: {picks_path}")
    else:
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
    explicit_pauses = {b['index'] for b in manifest.get('blocks', [])
                       if b.get('explicit_pause')}

    # Humanize pauses (skip for stories — creates silences too long for narrative)
    # Explicit [SILENCE: X] pauses are sacred — exact duration, no humanisation.
    # Pass as negative so humanize_pauses() skips them natively (pause <= 0 check).
    blocks_for_humanize = []
    n_explicit = 0
    for ci, _ in copied:
        text = next((p['text'] for p in picks_data['picks'] if p['chunk'] == ci), '')
        pause = pauses.get(ci, 0)
        if ci in explicit_pauses:
            pause = -pause  # Negative = "do not humanize"
            n_explicit += 1
        blocks_for_humanize.append((text, pause))

    if no_humanize:
        humanized = [(t, abs(p)) for t, p in blocks_for_humanize]
        print(f"  Pauses: using raw durations (--no-humanize)")
    else:
        humanized_raw = build.humanize_pauses(blocks_for_humanize)
        # Convert back to positive (explicit pauses passed through unchanged)
        humanized = [(t, abs(p)) for t, p in humanized_raw]
        if n_explicit:
            print(f"  Pauses: {n_explicit} explicit [SILENCE] kept exact, rest humanized")

    # Process in temp directory
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        concat_files = []
        segments = []
        current_time = 0.0

        is_last_chunk = {copied[-1][0]} if copied else set()

        for i, (ci, pick_wav) in enumerate(copied):
            text, pause = humanized[i]

            # Apply 150ms closing tail fade on final chunk (Bible Section 13)
            if ci in is_last_chunk:
                tail_faded = tmp / f"c{ci:02d}_tailfade.wav"
                apply_closing_tail_fade(pick_wav, tail_faded, fade_ms=150)
                pick_wav = tail_faded
                print(f"  c{ci:02d}: 150ms closing tail fade applied")

            # Apply edge fades
            faded = tmp / f"c{ci:02d}_faded.wav"
            apply_edge_fades(pick_wav, faded)
            concat_files.append(str(faded))

            dur = build.get_audio_duration(str(faded))
            segments.append({
                'type': 'text', 'index': ci,
                'start_time': current_time,
                'end_time': current_time + dur,
                'duration': dur, 'text': text
            })
            current_time += dur
            print(f"  c{ci:02d}: {dur:.1f}s", end="")

            # Insert silence after chunk (if any)
            if pause > 0:
                silence = tmp / f"silence_{ci:02d}_{pause:.1f}s.wav"
                generate_silence(pause, silence)
                concat_files.append(str(silence))
                segments.append({
                    'type': 'silence',
                    'start_time': current_time,
                    'end_time': current_time + pause,
                    'duration': pause
                })
                current_time += pause
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
        if output_dir:
            final_dir = Path(output_dir)
        else:
            final_dir = session_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)

        # Save voice-only loudnormed WAV (always useful for re-mixing)
        voice_wav = final_dir / f"{session_id}-vault-voice.wav"
        shutil.copy2(normed, voice_wav)
        print(f"  Voice WAV (loudnormed): {voice_wav}")

        # Also save raw concat for QA (click scanner needs pre-loudnorm)
        raw_copy = final_dir / f"{session_id}-vault-raw.wav"
        shutil.copy2(raw_concat, raw_copy)

        # Post-assembly HF scan for conditioning chain contamination (L-30)
        print(f"\n  --- Conditioning Chain HF Scan (Production Rule 19) ---")
        hf_passed, hf_flagged = conditioning_chain_hf_scan(voice_wav)
        if not hf_passed:
            print(f"  WARNING: HF scan flagged {len(hf_flagged)} windows — "
                  f"review for conditioning chain contamination before deploy")

        # Ambient mixing (Bible v4.6: voice-first loudnorm, then ambient)
        if ambient:
            print(f"\n  --- Ambient Mixing (voice-first loudnorm pipeline) ---")
            mixed_wav = final_dir / f"{session_id}-vault.wav"
            mix_ambient(voice_wav, ambient, mixed_wav,
                        gain_db=ambient_gain, fade_in_sec=fade_in,
                        fade_out_sec=fade_out)
            final_wav = mixed_wav
        else:
            # No ambient — just copy voice-only as final
            final_wav = final_dir / f"{session_id}-vault.wav"
            if final_wav != voice_wav:
                shutil.copy2(voice_wav, final_wav)
            print(f"  No ambient specified — voice-only output")

        final_mp3 = final_dir / f"{session_id}-vault.mp3"

        # Encode MP3 (the ONLY lossy step — no second loudnorm)
        encode_mp3(final_wav, final_mp3)
        mp3_size = final_mp3.stat().st_size / (1024 * 1024)
        print(f"  Final MP3: {final_mp3} ({mp3_size:.1f} MB)")

    # Duration check
    final_dur = build.get_audio_duration(str(final_wav))
    print(f"\n  Final duration: {final_dur:.1f}s ({final_dur/60:.1f} min)")

    # Save assembly manifest (segment timings for QA gates)
    assembly_manifest = {'segments': segments}
    manifest_out = final_dir / "assembly-manifest.json"
    manifest_out.write_text(json.dumps(assembly_manifest, indent=2))
    print(f"  Assembly manifest: {manifest_out}")

    # Parse script metadata for Gate 12 (Duration Accuracy)
    script_path = Path("content/scripts") / f"{session_id}.txt"
    script_metadata = {}
    if script_path.exists():
        script_metadata = build.parse_script(script_path)
        # parse_script captures 'duration' but not 'duration-target' —
        # vault scripts use Duration-Target header (just a number)
        if not script_metadata.get('duration'):
            header = script_path.read_text().split('---')[0]
            match = re.search(r'Duration-Target:\s*(\d+)', header)
            if match:
                script_metadata['duration'] = f"{match.group(1)} min"
    else:
        print(f"  WARNING: No script found at {script_path} — Gate 12 will skip")

    # Run post-assembly QA gates (1,2,3,5,7,8,9,10,11,12,13)
    qa_passed = None
    qa_gate_results = None
    if not skip_qa:
        print(f"\n{'='*70}")
        print(f"  RUNNING POST-ASSEMBLY QA (Gates 1,2,3,5,7,8,9,10,11,12,13)")
        print(f"{'='*70}")
        qa_passed, qa_gate_results = run_vault_qa(
            session_id, final_wav, raw_copy, final_mp3,
            assembly_manifest, script_metadata, final_dir)
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
    if qa_passed is not None:
        report['qa_passed'] = qa_passed
        report['qa_gates'] = 'post-assembly (1,2,3,5,7,8,9,10,11,12,13)'
        report['qa_summary'] = {
            str(gnum): {'name': r['name'], 'passed': r['passed'],
                        **({'skipped': True} if r.get('skipped') else {})}
            for gnum, r in sorted(qa_gate_results.items())
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

    if qa_passed is False:
        print(f"\n  QA FAILED — do NOT deploy. Fix issues and re-assemble.")
    elif qa_passed is True:
        print(f"\n  QA PASSED — ready for human end-to-end listen.")
        print(f"  NEXT: Listen to the full splice, then mix ambient if needed.")
    else:
        print(f"\n  NEXT: Listen to the full splice, then mix ambient if needed.")

    return qa_passed is not False


def main():
    parser = argparse.ArgumentParser(
        description='Vault Assembly — Splice picked candidates into final audio')
    parser.add_argument('session_id',
                        help='Session ID (e.g., 52-the-court-of-your-mind)')
    parser.add_argument('--skip-qa', action='store_true',
                        help='Skip 14-gate QA (for testing)')
    parser.add_argument('--no-humanize', action='store_true',
                        help='Skip pause humanization (for stories — raw pause durations)')
    parser.add_argument('--ambient', type=str, default=None,
                        help='Ambient source name (e.g. grace, rain, garden, birds, stream)')
    parser.add_argument('--ambient-gain', type=float, default=None,
                        help='Ambient gain in dB (e.g. -14, -19). Default: per-source Bible values.')
    parser.add_argument('--fade-in', type=float, default=30,
                        help='Ambient fade-in / structural pre-roll in seconds (default: 30)')
    parser.add_argument('--fade-out', type=float, default=60,
                        help='Ambient fade-out in seconds (default: 60)')
    parser.add_argument('--picks', type=str, default=None,
                        help='Path to custom picks JSON (overrides vault picks)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for assembled audio (default: vault dir)')
    args = parser.parse_args()

    success = assemble(args.session_id, skip_qa=args.skip_qa,
                       no_humanize=args.no_humanize, ambient=args.ambient,
                       ambient_gain=args.ambient_gain,
                       fade_in=args.fade_in, fade_out=args.fade_out,
                       picks_path=args.picks, output_dir=args.output_dir)

    # Auto-regenerate the audit report
    try:
        audit_script = Path(__file__).resolve().parent / "tools" / "r2-audit-v2.py"
        report_path = Path(__file__).resolve().parent / "r2-audit-report-v2.html"
        print(f"\nRegenerating audit report...")
        import subprocess
        subprocess.run(
            [sys.executable, str(audit_script), "--skip-cdn", "-o", str(report_path)],
            cwd=str(Path(__file__).resolve().parent),
            timeout=30,
        )
        print(f"  Report updated: {report_path}")
    except Exception as e:
        print(f"  (Audit report skipped: {e})")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
