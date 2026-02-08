#!/usr/bin/env python3
"""
Salus A/B Audio Comparison Tool

Generates pipeline-stage comparison files for any built session,
uploads to R2, and creates an HTML listening page.

Usage:
    python3 compare-audio.py <session-name>
    python3 compare-audio.py 36-loving-kindness-intro

Requires: ffmpeg, wrangler CLI (for R2 upload)
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Paths (match build-session-v3.py)
OUTPUT_DIR = Path("content/audio-free")
OUTPUT_RAW_DIR = Path("content/audio-free/raw")
MASTER_REF_WAV = Path("content/audio/marco-master/marco-master-v1.wav")
SAMPLE_RATE = 44100
R2_BUCKET = "salus-mind"
CDN_BASE = "https://media.salus-mind.com"


def run(cmd, **kwargs):
    """Run a command, raise on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"  FAILED: {' '.join(str(c) for c in cmd[:4])}...")
        print(f"  {result.stderr[:200]}")
        sys.exit(1)
    return result


def generate_comparisons(session_name, duration=None):
    """Generate A/B comparison files at each pipeline stage."""

    precleanup = OUTPUT_RAW_DIR / f"{session_name}_precleanup.wav"
    post_cleanup = OUTPUT_RAW_DIR / f"{session_name}.wav"
    final_mp3 = OUTPUT_DIR / f"{session_name}.mp3"

    if not precleanup.exists():
        print(f"ERROR: Precleanup WAV not found: {precleanup}")
        sys.exit(1)

    # Duration flag: clip to first N seconds, or full file
    dur_args = ['-t', str(duration)] if duration else []

    tracks = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # A: Raw TTS (zero processing)
        print("  [A] Raw TTS (zero processing)...")
        out_a = tmp / "A_raw_tts.mp3"
        run(['ffmpeg', '-y', '-i', str(precleanup)] + dur_args +
            ['-c:a', 'libmp3lame', '-b:a', '128k', str(out_a)])
        tracks['A'] = {
            'file': out_a,
            'title': 'Raw TTS — Zero Processing',
            'desc': 'Straight from Fish. Edge fades only, no loudnorm, no EQ, no ambient.',
        }

        # B: Loudnorm only
        print("  [B] Loudnorm only...")
        out_b = tmp / "B_loudnorm_only.mp3"
        run(['ffmpeg', '-y', '-i', str(precleanup)] + dur_args +
            ['-af', 'loudnorm=I=-26:TP=-2:LRA=11',
             '-c:a', 'libmp3lame', '-b:a', '128k', str(out_b)])
        tracks['B'] = {
            'file': out_b,
            'title': 'Loudnorm Only',
            'desc': 'loudnorm=I=-26:TP=-2:LRA=11. No EQ, no ambient.',
        }

        # C: Full cleanup (current chain from build script)
        if post_cleanup.exists():
            print("  [C] Full cleanup (post-build)...")
            out_c = tmp / "C_full_cleanup.mp3"
            run(['ffmpeg', '-y', '-i', str(post_cleanup)] + dur_args +
                ['-c:a', 'libmp3lame', '-b:a', '128k', str(out_c)])
            tracks['C'] = {
                'file': out_c,
                'title': 'Full Cleanup (no ambient)',
                'desc': 'Build script cleanup chain applied. Voice only, no ambient mix.',
            }

        # D: Final deployed (cleanup + ambient)
        if final_mp3.exists():
            print("  [D] Final deployed...")
            out_d = tmp / "D_final_deployed.mp3"
            if duration:
                run(['ffmpeg', '-y', '-i', str(final_mp3),
                     '-t', str(duration),
                     '-c:a', 'libmp3lame', '-b:a', '128k', str(out_d)])
            else:
                import shutil
                shutil.copy(str(final_mp3), str(out_d))
            tracks['D'] = {
                'file': out_d,
                'title': 'Final Deployed',
                'desc': 'Full cleanup + ambient mix. What\'s live on the site.',
            }

        # M: Marco master reference
        if MASTER_REF_WAV.exists():
            print("  [M] Marco master reference...")
            out_m = tmp / "M_marco_master.mp3"
            run(['ffmpeg', '-y', '-i', str(MASTER_REF_WAV),
                 '-c:a', 'libmp3lame', '-b:a', '128k', str(out_m)])
            tracks['M'] = {
                'file': out_m,
                'title': 'Marco Master (Reference)',
                'desc': 'Raw TTS + 0.95x atempo. No cleanup. The benchmark.',
            }

        # Upload to R2
        r2_prefix = f"test/compare/{session_name}"
        print(f"\n  Uploading to R2 ({r2_prefix})...")
        urls = {}
        for key, track in tracks.items():
            r2_key = f"{R2_BUCKET}/{r2_prefix}/{track['file'].name}"
            run(['npx', 'wrangler', 'r2', 'object', 'put', r2_key,
                 f'--file={track["file"]}', '--remote'])
            urls[key] = f"{CDN_BASE}/{r2_prefix}/{track['file'].name}"
            print(f"    [{key}] uploaded")

        # Generate HTML comparison page
        print("\n  Generating comparison page...")
        html_path = Path("test") / f"compare-{session_name}.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        for key in sorted(tracks.keys()):
            t = tracks[key]
            rows.append(f'''  <div class="track">
    <h2>{key}. {t['title']}</h2>
    <p>{t['desc']}</p>
    <audio controls preload="none" src="{urls[key]}"></audio>
  </div>''')

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Compare: {session_name}</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; max-width: 600px; margin: 0 auto; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
    p.sub {{ color: #888; font-size: 0.85rem; margin-bottom: 24px; }}
    .track {{ background: #16213e; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; }}
    .track h2 {{ font-size: 1rem; margin: 0 0 4px 0; }}
    .track p {{ color: #aaa; font-size: 0.8rem; margin: 0 0 12px 0; }}
    audio {{ width: 100%; height: 40px; }}
  </style>
</head>
<body>
  <h1>A/B Compare: {session_name}</h1>
  <p class="sub">Listen in order. Which step introduces the issue?</p>
{"".join(rows)}
</body>
</html>'''

        html_path.write_text(html)
        print(f"  Saved: {html_path}")
        print(f"\n  Open with: open {html_path}")

    return html_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 compare-audio.py <session-name> [--duration 60]")
        sys.exit(1)

    session = sys.argv[1]
    duration = None
    if '--duration' in sys.argv:
        idx = sys.argv.index('--duration')
        duration = int(sys.argv[idx + 1])

    print(f"Generating A/B comparison for: {session}")
    if duration:
        print(f"  Clipping to first {duration}s")

    os.chdir(Path(__file__).parent)
    html = generate_comparisons(session, duration)
    subprocess.run(['open', str(html)])
