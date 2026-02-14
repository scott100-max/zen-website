#!/usr/bin/env python3
"""
Voice Breakout Scanner (Gate 17 — L-50)
========================================
Unsupervised screening pass for voice breakout defects in Fish TTS output.
Voice breakout = voice suddenly jumps several octaves mid-chunk.

Known positives: S60/c01/v24 (breakout at 0:56), S62/c06/v12 (breakout at 3:36).

Usage:
  python3 breakout-scanner.py --scan                     # 5 random + 2 controls
  python3 breakout-scanner.py --scan --sessions 01 38    # specific sessions + controls
  python3 breakout-scanner.py --scan --all               # all 52 deployed sessions
  python3 breakout-scanner.py --picker                   # generate HTML from last scan
"""

import json
import sys
import os
import argparse
import random
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import librosa
from scipy.spatial.distance import cosine as cosine_dist

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent
VAULT_DIR = PROJECT_ROOT / "content" / "audio-free" / "vault"
REGISTRY_PATH = PROJECT_ROOT / "content" / "session-registry.json"
OUTPUT_DIR = PROJECT_ROOT / "reference" / "breakout-analysis"

# Known breakout controls
CONTROLS = [
    {"session": "60-21day-mindfulness-day04", "chunk": 1, "version": 24,
     "note": "voice breakout at 0:56"},
    {"session": "62-21day-mindfulness-day06", "chunk": 6, "version": 12,
     "note": "voice breakout at 3:36"},
]
CONTROL_SESSIONS = {"60-21day-mindfulness-day04", "62-21day-mindfulness-day06"}

# Scoring weights
SCORE_WEIGHTS = {
    "f0_max_semitone_jump": 3.0,
    "centroid_max_jump_ratio": 2.0,
    "mfcc_max_cosine_dist": 2.0,
    "mel_flux_max": 1.5,
    "f0_range_semitones": 1.0,
    "mel_half_shift_db": 1.0,
    "mfcc_half_split_dist": 0.5,
}
SCORE_TOTAL_WEIGHT = sum(SCORE_WEIGHTS.values())

# Flagging thresholds — tuned so ~10-15% of WAVs are flagged
# Normal speech f0 median ~9.4st, so 12st = genuine full-octave jump
SCORE_FLAG_THRESHOLD = 0.4
F0_JUMP_FLAG_THRESHOLD = 12.0  # semitones (full octave)


# ============================================================
# STEP 1: SESSION SELECTION
# ============================================================

def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def select_sessions(registry, requested_sessions=None, scan_all=False):
    """Select sessions to scan. Always includes control sessions."""
    deployed = {sid: info for sid, info in registry["sessions"].items()
                if info.get("status") == "deployed"}

    if scan_all:
        selected = set(deployed.keys())
    elif requested_sessions:
        # Match by prefix (e.g. "01" matches "01-morning-meditation")
        selected = set()
        for req in requested_sessions:
            for sid in deployed:
                if sid.startswith(req):
                    selected.add(sid)
                    break
            else:
                print(f"  WARNING: No deployed session matching '{req}'")
    else:
        # 5 random (excluding controls)
        pool = [s for s in deployed if s not in CONTROL_SESSIONS]
        n = min(5, len(pool))
        selected = set(random.sample(pool, n))

    # Always include controls
    selected |= CONTROL_SESSIONS

    print(f"  Sessions to scan: {len(selected)}")
    for s in sorted(selected):
        tag = " [CONTROL]" if s in CONTROL_SESSIONS else ""
        print(f"    {s}{tag}")

    return sorted(selected)


def resolve_wavs_for_session(session_id):
    """Load picks-auto.json and resolve WAV paths for picked versions."""
    session_dir = VAULT_DIR / session_id
    picks_path = session_dir / "picks-auto.json"

    if not picks_path.exists():
        print(f"    SKIP {session_id} — no picks-auto.json")
        return []

    with open(picks_path) as f:
        picks = json.load(f)

    wavs = []
    for pick in picks["picks"]:
        ci = pick["chunk"]
        ver = pick["picked"]
        if ver is None:
            continue
        wav_path = session_dir / f"c{ci:02d}" / f"c{ci:02d}_v{ver:02d}.wav"
        if not wav_path.exists():
            continue

        # Load chunk text from meta if available
        text = pick.get("text", "")
        if not text:
            meta_path = session_dir / f"c{ci:02d}" / f"c{ci:02d}_meta.json"
            if meta_path.exists():
                try:
                    with open(meta_path) as mf:
                        text = json.load(mf).get("text", "")
                except Exception:
                    pass

        wavs.append({
            "session": session_id,
            "chunk": ci,
            "version": ver,
            "wav_path": str(wav_path),
            "text": text,
            "is_control": False,
        })

    # For control sessions, also include the known-breakout WAVs if not already picked
    for ctrl in CONTROLS:
        if ctrl["session"] != session_id:
            continue
        # Check if control version is already in picks (it shouldn't be — it was rejected)
        already = any(w["chunk"] == ctrl["chunk"] and w["version"] == ctrl["version"]
                      for w in wavs)
        if not already:
            wav_path = (session_dir / f"c{ctrl['chunk']:02d}" /
                        f"c{ctrl['chunk']:02d}_v{ctrl['version']:02d}.wav")
            if wav_path.exists():
                # Get text from existing pick for same chunk
                text = ""
                for w in wavs:
                    if w["chunk"] == ctrl["chunk"]:
                        text = w["text"]
                        break
                wavs.append({
                    "session": session_id,
                    "chunk": ctrl["chunk"],
                    "version": ctrl["version"],
                    "wav_path": str(wav_path),
                    "text": text,
                    "is_control": True,
                    "control_note": ctrl["note"],
                })

    return wavs


# ============================================================
# STEP 2: FEATURE EXTRACTION
# ============================================================

def extract_breakout_features(wav_path, sr=22050):
    """Extract ~25 breakout-specific features from a WAV file."""
    y, sr = librosa.load(wav_path, sr=sr, mono=True)
    duration = len(y) / sr

    if duration < 0.5:
        return None

    # Edge trimming: skip first/last 100ms
    trim_samples = int(sr * 0.1)
    if len(y) > trim_samples * 3:
        y = y[trim_samples:-trim_samples]

    feats = {"duration": float(duration)}
    hop = 256
    n_fft = 2048

    # ---- A. Pitch continuity (6 features) — primary signal ----
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y, fmin=50, fmax=600, sr=sr, hop_length=hop
    )

    # Get voiced frames
    voiced_mask = ~np.isnan(f0)
    f0_voiced = f0[voiced_mask]

    if len(f0_voiced) > 2:
        # Semitone jumps between adjacent voiced frames
        ratios = f0_voiced[1:] / f0_voiced[:-1]
        semitone_jumps = np.abs(12.0 * np.log2(ratios + 1e-10))

        feats["f0_max_semitone_jump"] = float(np.max(semitone_jumps))
        feats["f0_range_semitones"] = float(
            12.0 * np.log2((np.max(f0_voiced) / np.min(f0_voiced)) + 1e-10)
        )
        feats["f0_std_normalized"] = float(np.std(f0_voiced) / (np.mean(f0_voiced) + 1e-10))
        feats["f0_jumps_above_6st"] = int(np.sum(semitone_jumps > 6))

        # Voicing dropout: voiced→unvoiced→voiced transitions lasting <5 frames
        dropout_count = 0
        in_dropout = False
        dropout_len = 0
        for i in range(len(voiced_mask)):
            if voiced_mask[i]:
                if in_dropout and dropout_len < 5:
                    dropout_count += 1
                in_dropout = False
                dropout_len = 0
            else:
                if i > 0 and voiced_mask[i - 1]:
                    in_dropout = True
                if in_dropout:
                    dropout_len += 1
        feats["voicing_dropout_count"] = dropout_count

        # Min voicing confidence in any 5-frame window
        if voiced_prob is not None and len(voiced_prob) >= 5:
            min_conf = 1.0
            for i in range(len(voiced_prob) - 4):
                window_conf = np.mean(voiced_prob[i:i+5])
                if window_conf < min_conf:
                    min_conf = window_conf
            feats["voicing_confidence_min_5frame"] = float(min_conf)
        else:
            feats["voicing_confidence_min_5frame"] = 0.0
    else:
        feats["f0_max_semitone_jump"] = 0.0
        feats["f0_range_semitones"] = 0.0
        feats["f0_std_normalized"] = 0.0
        feats["f0_jumps_above_6st"] = 0
        feats["voicing_dropout_count"] = 0
        feats["voicing_confidence_min_5frame"] = 0.0

    # ---- B. Spectral centroid discontinuity (4 features) ----
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop)[0]

    if len(centroid) > 2:
        centroid_jumps = np.abs(np.diff(centroid))
        mean_centroid = np.mean(centroid) + 1e-10

        feats["centroid_max_jump_hz"] = float(np.max(centroid_jumps))
        feats["centroid_max_jump_ratio"] = float(np.max(centroid_jumps) / mean_centroid)
        feats["centroid_jump_p95"] = float(np.percentile(centroid_jumps, 95))
        feats["centroid_std_normalized"] = float(np.std(centroid) / mean_centroid)
    else:
        feats["centroid_max_jump_hz"] = 0.0
        feats["centroid_max_jump_ratio"] = 0.0
        feats["centroid_jump_p95"] = 0.0
        feats["centroid_std_normalized"] = 0.0

    # ---- C. MFCC temporal coherence (4 features) ----
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=n_fft, hop_length=hop)
    n_frames = mfcc.shape[1]

    if n_frames > 2:
        # Cosine distance between adjacent MFCC frames
        cosine_dists = []
        for i in range(n_frames - 1):
            a = mfcc[:, i]
            b = mfcc[:, i + 1]
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a > 1e-10 and norm_b > 1e-10:
                d = 1.0 - np.dot(a, b) / (norm_a * norm_b)
                cosine_dists.append(max(0.0, d))

        if cosine_dists:
            feats["mfcc_max_cosine_dist"] = float(np.max(cosine_dists))
            feats["mfcc_cosine_dist_p95"] = float(np.percentile(cosine_dists, 95))
        else:
            feats["mfcc_max_cosine_dist"] = 0.0
            feats["mfcc_cosine_dist_p95"] = 0.0

        # Half-split distance
        half = n_frames // 2
        first_half_mean = np.mean(mfcc[:, :half], axis=1)
        second_half_mean = np.mean(mfcc[:, half:], axis=1)
        norm1 = np.linalg.norm(first_half_mean)
        norm2 = np.linalg.norm(second_half_mean)
        if norm1 > 1e-10 and norm2 > 1e-10:
            feats["mfcc_half_split_dist"] = float(
                1.0 - np.dot(first_half_mean, second_half_mean) / (norm1 * norm2)
            )
        else:
            feats["mfcc_half_split_dist"] = 0.0

        # Mean of per-coefficient std
        feats["mfcc_temporal_std"] = float(np.mean(np.std(mfcc, axis=1)))
    else:
        feats["mfcc_max_cosine_dist"] = 0.0
        feats["mfcc_cosine_dist_p95"] = 0.0
        feats["mfcc_half_split_dist"] = 0.0
        feats["mfcc_temporal_std"] = 0.0

    # ---- D. Mel band energy redistribution (4 features) ----
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=80, n_fft=n_fft, hop_length=hop)
    S_db = librosa.power_to_db(S, ref=np.max)
    mel_frames = S_db.shape[1]

    if mel_frames > 2:
        # Total spectral flux per frame
        mel_diff = np.diff(S_db, axis=1)
        flux_per_frame = np.sqrt(np.mean(mel_diff ** 2, axis=0))

        feats["mel_flux_max"] = float(np.max(flux_per_frame))
        feats["mel_flux_p99"] = float(np.percentile(flux_per_frame, 99))

        # Max dB diff in any mel band between first-half and second-half mean
        half = mel_frames // 2
        first_half = np.mean(S_db[:, :half], axis=1)
        second_half = np.mean(S_db[:, half:], axis=1)
        band_diffs = np.abs(first_half - second_half)
        feats["mel_half_shift_db"] = float(np.max(band_diffs))

        # Low/high energy ratio range across frames
        low_energy = np.mean(S_db[:30, :], axis=0)
        high_energy = np.mean(S_db[50:, :], axis=0)
        ratio = low_energy - high_energy  # dB difference
        feats["mel_low_high_ratio_range"] = float(np.max(ratio) - np.min(ratio))
    else:
        feats["mel_flux_max"] = 0.0
        feats["mel_flux_p99"] = 0.0
        feats["mel_half_shift_db"] = 0.0
        feats["mel_low_high_ratio_range"] = 0.0

    # ---- E. Temporal location (3 features) ----
    if mel_frames > 2:
        breakout_frame = int(np.argmax(flux_per_frame))
        feats["breakout_frame"] = breakout_frame
        feats["breakout_time_sec"] = float(breakout_frame * hop / sr)
        feats["breakout_time_frac"] = float(breakout_frame / (mel_frames - 1))
    else:
        feats["breakout_frame"] = 0
        feats["breakout_time_sec"] = 0.0
        feats["breakout_time_frac"] = 0.0

    return feats


# ============================================================
# STEP 3: SCORING
# ============================================================

def compute_scores(all_results):
    """Compute z-score-based breakout scores for all WAVs."""
    # Collect feature values for population stats
    scored_features = list(SCORE_WEIGHTS.keys())
    feature_vals = {f: [] for f in scored_features}

    for r in all_results:
        feats = r.get("features")
        if feats is None:
            continue
        for f in scored_features:
            if f in feats:
                feature_vals[f].append(feats[f])

    # Compute population mean/std
    pop_stats = {}
    for f in scored_features:
        vals = np.array(feature_vals[f])
        pop_stats[f] = {"mean": float(np.mean(vals)), "std": float(np.std(vals) + 1e-10)}

    # Score each WAV
    for r in all_results:
        feats = r.get("features")
        if feats is None:
            r["breakout_score"] = 0.0
            r["flagged"] = False
            continue

        weighted_z_sum = 0.0
        r["z_scores"] = {}
        for f, weight in SCORE_WEIGHTS.items():
            val = feats.get(f, 0.0)
            z = (val - pop_stats[f]["mean"]) / pop_stats[f]["std"]
            r["z_scores"][f] = round(z, 3)
            weighted_z_sum += weight * z

        r["breakout_score"] = round(weighted_z_sum / SCORE_TOTAL_WEIGHT, 4)
        r["flagged"] = (
            r["breakout_score"] > SCORE_FLAG_THRESHOLD or
            feats.get("f0_max_semitone_jump", 0) > F0_JUMP_FLAG_THRESHOLD
        )

    return pop_stats


def validate_controls(all_results):
    """Check whether the known breakout controls score in the top 5%."""
    scored = [r for r in all_results if r.get("features") is not None]
    scored.sort(key=lambda x: x["breakout_score"], reverse=True)
    n = len(scored)
    top5_cutoff = max(1, int(n * 0.05))

    print(f"\n  CONTROL VALIDATION ({n} total WAVs, top 5% = rank ≤{top5_cutoff}):")

    for ctrl in CONTROLS:
        for i, r in enumerate(scored):
            if (r["session"] == ctrl["session"] and
                    r["chunk"] == ctrl["chunk"] and
                    r["version"] == ctrl["version"]):
                rank = i + 1
                in_top5 = rank <= top5_cutoff
                status = "PASS" if in_top5 else "FAIL"
                print(f"    {ctrl['session']} c{ctrl['chunk']:02d}/v{ctrl['version']:02d}: "
                      f"rank {rank}/{n} (score={r['breakout_score']:.4f}) "
                      f"{'top 5%' if in_top5 else 'NOT in top 5%'} [{status}]")
                break
        else:
            print(f"    {ctrl['session']} c{ctrl['chunk']:02d}/v{ctrl['version']:02d}: NOT FOUND")


# ============================================================
# STEP 4: HTML PICKER
# ============================================================

def generate_picker_html(suspects, all_results):
    """Generate interactive HTML picker for labelling breakout suspects."""
    n_total = len(all_results)
    n_flagged = len(suspects)

    cards_html = []
    meta_js = {}

    for idx, s in enumerate(suspects):
        feats = s.get("features", {})
        is_ctrl = s.get("is_control", False)
        ctrl_badge = '<span class="badge control">CONTROL</span>' if is_ctrl else ''
        ctrl_note = f'<div class="ctrl-note">{s.get("control_note", "")}</div>' if is_ctrl else ''

        listen_hint = ""
        bt = feats.get("breakout_time_sec", 0)
        if bt > 0:
            listen_hint = f'<span class="listen-hint">Listen at {bt:.1f}s</span>'

        key_feats_html = ""
        for fname in ["f0_max_semitone_jump", "f0_range_semitones", "centroid_max_jump_ratio",
                       "mfcc_max_cosine_dist", "mel_flux_max", "mel_half_shift_db"]:
            val = feats.get(fname, 0)
            z = s.get("z_scores", {}).get(fname, 0)
            z_class = "z-high" if z > 2 else "z-med" if z > 1 else "z-low"
            key_feats_html += f'<span class="feat-item"><b>{fname.split("_", 1)[1] if "_" in fname else fname}</b>: {val:.3f} <span class="{z_class}">(z={z:.1f})</span></span>'

        meta_js[idx] = {
            "session": s["session"], "chunk": s["chunk"], "version": s["version"],
            "score": s["breakout_score"],
        }

        cards_html.append(f'''    <div class="card" id="card-{idx}" data-idx="{idx}">
      <div class="card-header">
        <span class="rank">#{idx + 1}</span>
        <span class="session-id">{s["session"]}</span>
        <span class="chunk-ver">c{s["chunk"]:02d}/v{s["version"]:02d}</span>
        <span class="score">score={s["breakout_score"]:.4f}</span>
        {ctrl_badge}
        {listen_hint}
      </div>
      {ctrl_note}
      <div class="chunk-text">"{s.get("text", "")[:120]}"</div>
      <div class="key-feats">{key_feats_html}</div>
      <audio controls preload="{'auto' if idx == 0 else 'none'}"
             src="file://{s["wav_path"]}"></audio>
      <div class="verdict-row">
        <button class="vbtn breakout" onclick="setVerdict({idx},'BREAKOUT')">BREAKOUT</button>
        <button class="vbtn clean" onclick="setVerdict({idx},'CLEAN')">CLEAN</button>
        <button class="vbtn unsure" onclick="setVerdict({idx},'UNSURE')">UNSURE</button>
        <button class="vbtn other" onclick="setVerdict({idx},'OTHER_DEFECT')">OTHER DEFECT</button>
        <span class="verdict-label" id="vlabel-{idx}"></span>
      </div>
    </div>''')

    meta_json = json.dumps(meta_js, indent=2)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Breakout Scanner — Picker</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a12; color: #f0eefc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; max-width: 900px; margin: 0 auto; }}
h1 {{ font-size: 1.4rem; margin-bottom: 5px; color: #f59e0b; }}
.subtitle {{ color: #888; margin-bottom: 20px; font-size: 0.9rem; }}
.stats-bar {{ background: #1a1a2e; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; }}
.stats-bar .stat {{ font-size: 0.85rem; line-height: 1.6; }}
.stats-bar b {{ color: #7dd3fc; }}
.card {{ background: #12121e; border: 1px solid #2a2a3e; border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
.card.labelled {{ border-color: #2d5a3d; }}
.card-header {{ display: flex; gap: 12px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }}
.rank {{ font-weight: bold; font-size: 1.1rem; color: #f59e0b; }}
.session-id {{ color: #7dd3fc; font-weight: bold; }}
.chunk-ver {{ color: #aaa; }}
.score {{ color: #a78bfa; font-weight: bold; }}
.badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
.badge.control {{ background: #dc2626; color: white; }}
.listen-hint {{ color: #facc15; font-size: 0.8rem; }}
.ctrl-note {{ color: #f87171; font-size: 0.8rem; margin-bottom: 4px; }}
.chunk-text {{ color: #ccc; font-size: 0.85rem; margin-bottom: 8px; line-height: 1.4; font-style: italic; }}
.key-feats {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }}
.feat-item {{ font-size: 0.75rem; color: #888; }}
.feat-item b {{ color: #bbb; }}
.z-high {{ color: #ef4444; font-weight: bold; }}
.z-med {{ color: #f59e0b; }}
.z-low {{ color: #666; }}
audio {{ width: 100%; margin-bottom: 10px; }}
.verdict-row {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
.vbtn {{ padding: 6px 16px; border: 1px solid #444; border-radius: 6px; background: #1a1a2e; color: #f0eefc; cursor: pointer; font-size: 0.85rem; transition: all 0.15s; }}
.vbtn:hover {{ border-color: #666; }}
.vbtn.breakout:hover, .vbtn.breakout.active {{ background: #7f1d1d; border-color: #ef4444; color: #fca5a5; }}
.vbtn.clean:hover, .vbtn.clean.active {{ background: #166534; border-color: #22c55e; color: #86efac; }}
.vbtn.unsure:hover, .vbtn.unsure.active {{ background: #713f12; border-color: #f59e0b; color: #fcd34d; }}
.vbtn.other:hover, .vbtn.other.active {{ background: #581c87; border-color: #a855f7; color: #d8b4fe; }}
.verdict-label {{ font-weight: bold; font-size: 0.9rem; margin-left: 8px; }}
.export-bar {{ position: sticky; bottom: 0; background: #0a0a12; padding: 12px 0; border-top: 1px solid #2a2a3e; display: flex; gap: 12px; align-items: center; }}
.export-btn {{ padding: 10px 24px; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; }}
.export-btn:hover {{ background: #1d4ed8; }}
.counter {{ color: #888; }}
</style>
</head>
<body>
<h1>Voice Breakout Scanner — Picker</h1>
<div class="subtitle">Generated: {timestamp} | {n_flagged} suspects from {n_total} WAVs scanned</div>
<div class="stats-bar">
  <div class="stat">Keys: <b>1</b>=BREAKOUT  <b>2</b>=CLEAN  <b>3</b>=UNSURE  <b>4</b>=OTHER DEFECT  |  <b>Space</b>=Pause  <b>Enter</b>=Next</div>
  <div class="stat">Flagging: score &gt; {SCORE_FLAG_THRESHOLD} OR f0_max_semitone_jump &gt; {F0_JUMP_FLAG_THRESHOLD} semitones</div>
</div>

{"".join(cards_html)}

<div class="export-bar">
  <button class="export-btn" id="pause-btn" onclick="togglePause()" style="background:#16a34a">&#9654; Play</button>
  <button class="export-btn" onclick="exportVerdicts()">Export Verdicts</button>
  <span class="counter" id="counter">0/{n_flagged} labelled</span>
</div>

<script>
const verdicts = {{}};
const totalCards = {n_flagged};
const cardMeta = {meta_json};
let currentCard = 0;
let paused = true;

function setVerdict(idx, verdict) {{
  verdicts[idx] = verdict;
  const card = document.getElementById('card-' + idx);
  card.querySelectorAll('.vbtn').forEach(b => b.classList.remove('active'));
  card.querySelector('.vbtn.' + verdict.toLowerCase().replace('_', '-').replace('other-defect','other')).classList.add('active');
  document.getElementById('vlabel-' + idx).textContent = verdict;
  document.getElementById('vlabel-' + idx).style.color =
    verdict === 'BREAKOUT' ? '#ef4444' :
    verdict === 'CLEAN' ? '#4ade80' :
    verdict === 'UNSURE' ? '#fcd34d' : '#d8b4fe';
  card.classList.add('labelled');
  updateCounter();
  // Auto-advance to next card after verdict
  setTimeout(() => advanceToCard(idx + 1), 400);
}}

function updateCounter() {{
  const n = Object.keys(verdicts).length;
  document.getElementById('counter').textContent = n + '/' + totalCards + ' labelled';
}}

function togglePause() {{
  paused = !paused;
  const btn = document.getElementById('pause-btn');
  btn.textContent = paused ? '\\u25B6 Play' : '\\u23F8 Pause';
  btn.style.background = paused ? '#16a34a' : '#d97706';
  if (paused) document.querySelectorAll('audio').forEach(a => a.pause());
  else {{
    const cur = document.getElementById('card-' + currentCard);
    if (cur) cur.querySelector('audio').play();
  }}
}}

function advanceToCard(n) {{
  if (n >= totalCards) return;
  // Stop current audio
  const prev = document.getElementById('card-' + currentCard);
  if (prev) prev.querySelector('audio').pause();
  currentCard = n;
  const next = document.getElementById('card-' + n);
  if (next) {{
    next.scrollIntoView({{behavior:'smooth', block:'center'}});
    if (!paused) setTimeout(() => next.querySelector('audio').play(), 600);
  }}
}}

function exportVerdicts() {{
  const data = {{
    generated: '{timestamp}',
    total_scanned: {n_total},
    total_flagged: {n_flagged},
    labelled: Object.keys(verdicts).length,
    verdicts: []
  }};
  for (const [idxStr, v] of Object.entries(verdicts)) {{
    const meta = cardMeta[parseInt(idxStr)];
    if (meta) {{
      data.verdicts.push({{
        session: meta.session,
        chunk: meta.chunk,
        version: meta.version,
        breakout_score: meta.score,
        verdict: v
      }});
    }}
  }}
  const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'breakout-verdicts.json';
  a.click();
}}

document.addEventListener('keydown', e => {{
  const map = {{'1':'BREAKOUT','2':'CLEAN','3':'UNSURE','4':'OTHER_DEFECT'}};
  if (map[e.key]) {{
    e.preventDefault();
    setVerdict(currentCard, map[e.key]);
  }}
  if (e.key === 'Enter') {{
    e.preventDefault();
    advanceToCard(currentCard + 1);
  }}
  if (e.key === ' ') {{
    e.preventDefault();
    togglePause();
  }}
}});

document.querySelectorAll('.card audio').forEach(audio => {{
  audio.addEventListener('play', () => {{
    const idx = parseInt(audio.closest('.card').dataset.idx);
    currentCard = idx;
  }});
  audio.addEventListener('ended', () => {{
    const idx = parseInt(audio.closest('.card').dataset.idx);
    currentCard = idx;
    advanceToCard(idx + 1);
  }});
}});
</script>
</body>
</html>'''

    return html


# ============================================================
# MAIN: SCAN
# ============================================================

def run_scan(sessions):
    """Run the full scan pipeline."""
    print("=" * 70)
    print("VOICE BREAKOUT SCANNER — Gate 17 (L-50)")
    print("=" * 70)

    registry = load_registry()
    selected = select_sessions(registry, sessions if sessions else None,
                                scan_all=False)

    # Resolve all WAV paths
    print(f"\n  Resolving WAV paths...")
    all_wavs = []
    for sid in selected:
        wavs = resolve_wavs_for_session(sid)
        all_wavs.extend(wavs)
        print(f"    {sid}: {len(wavs)} WAVs")

    print(f"\n  Total WAVs to scan: {len(all_wavs)}")

    # Extract features
    print(f"\n  Extracting breakout features...")
    for i, entry in enumerate(all_wavs):
        tag = " [CONTROL]" if entry["is_control"] else ""
        sys.stdout.write(f"\r    [{i+1}/{len(all_wavs)}] {entry['session']} "
                         f"c{entry['chunk']:02d}/v{entry['version']:02d}{tag}    ")
        sys.stdout.flush()

        feats = extract_breakout_features(entry["wav_path"])
        entry["features"] = feats

    print()

    # Score
    print(f"\n  Computing breakout scores...")
    pop_stats = compute_scores(all_wavs)

    # Sort by score
    all_wavs.sort(key=lambda x: x.get("breakout_score", 0), reverse=True)

    flagged = [w for w in all_wavs if w.get("flagged", False)]
    print(f"    Flagged: {len(flagged)} / {len(all_wavs)} WAVs")

    # Validate controls
    validate_controls(all_wavs)

    # Print top 20
    print(f"\n  TOP 20 SUSPECTS:")
    print(f"  {'Rank':>4}  {'Score':>7}  {'f0_jump':>8}  {'Session':<40}  {'Chunk':>6}  {'Notes'}")
    print(f"  {'-' * 100}")
    for i, w in enumerate(all_wavs[:20]):
        f = w.get("features", {})
        ctrl = " [CONTROL]" if w.get("is_control") else ""
        flag = " ***" if w.get("flagged") else ""
        print(f"  {i+1:>4}  {w.get('breakout_score', 0):>7.4f}  "
              f"{f.get('f0_max_semitone_jump', 0):>7.2f}st  "
              f"{w['session']:<40}  c{w['chunk']:02d}/v{w['version']:02d}  "
              f"{ctrl}{flag}")

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def make_serializable(obj):
        """Convert numpy types for JSON serialization."""
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    # Full results
    full_results = make_serializable({
        "generated": datetime.now().isoformat(),
        "n_scanned": len(all_wavs),
        "n_flagged": len(flagged),
        "population_stats": pop_stats,
        "score_weights": SCORE_WEIGHTS,
        "flag_thresholds": {
            "score": SCORE_FLAG_THRESHOLD,
            "f0_max_semitone_jump": F0_JUMP_FLAG_THRESHOLD,
        },
        "results": [{
            "session": w["session"], "chunk": w["chunk"], "version": w["version"],
            "wav_path": w["wav_path"], "text": w.get("text", ""),
            "is_control": w.get("is_control", False),
            "control_note": w.get("control_note", ""),
            "breakout_score": w.get("breakout_score", 0),
            "flagged": w.get("flagged", False),
            "features": w.get("features"),
            "z_scores": w.get("z_scores", {}),
        } for w in all_wavs],
    })

    full_path = OUTPUT_DIR / "breakout_scan_results.json"
    with open(full_path, 'w') as f:
        json.dump(full_results, f, indent=2)
    print(f"\n  Full results: {full_path}")

    # Suspects only
    suspects_data = make_serializable({
        "generated": datetime.now().isoformat(),
        "n_flagged": len(flagged),
        "suspects": [{
            "session": w["session"], "chunk": w["chunk"], "version": w["version"],
            "wav_path": w["wav_path"], "text": w.get("text", ""),
            "is_control": w.get("is_control", False),
            "breakout_score": w.get("breakout_score", 0),
            "features": w.get("features"),
            "z_scores": w.get("z_scores", {}),
        } for w in flagged],
    })

    suspects_path = OUTPUT_DIR / "breakout_suspects.json"
    with open(suspects_path, 'w') as f:
        json.dump(suspects_data, f, indent=2)
    print(f"  Suspects:     {suspects_path}")

    return all_wavs, flagged


def run_scan_all(sessions=None):
    """Scan all deployed sessions."""
    print("=" * 70)
    print("VOICE BREAKOUT SCANNER — Gate 17 (L-50) — FULL SCAN")
    print("=" * 70)

    registry = load_registry()
    selected = select_sessions(registry, sessions, scan_all=(sessions is None))

    all_wavs = []
    for sid in selected:
        wavs = resolve_wavs_for_session(sid)
        all_wavs.extend(wavs)

    print(f"\n  Total WAVs to scan: {len(all_wavs)}")

    print(f"\n  Extracting breakout features...")
    for i, entry in enumerate(all_wavs):
        tag = " [CONTROL]" if entry["is_control"] else ""
        sys.stdout.write(f"\r    [{i+1}/{len(all_wavs)}] {entry['session']} "
                         f"c{entry['chunk']:02d}/v{entry['version']:02d}{tag}    ")
        sys.stdout.flush()
        feats = extract_breakout_features(entry["wav_path"])
        entry["features"] = feats

    print()

    pop_stats = compute_scores(all_wavs)
    all_wavs.sort(key=lambda x: x.get("breakout_score", 0), reverse=True)
    flagged = [w for w in all_wavs if w.get("flagged", False)]

    print(f"    Flagged: {len(flagged)} / {len(all_wavs)} WAVs")
    validate_controls(all_wavs)

    print(f"\n  TOP 20 SUSPECTS:")
    print(f"  {'Rank':>4}  {'Score':>7}  {'f0_jump':>8}  {'Session':<40}  {'Chunk':>6}  {'Notes'}")
    print(f"  {'-' * 100}")
    for i, w in enumerate(all_wavs[:20]):
        f = w.get("features", {})
        ctrl = " [CONTROL]" if w.get("is_control") else ""
        flag = " ***" if w.get("flagged") else ""
        print(f"  {i+1:>4}  {w.get('breakout_score', 0):>7.4f}  "
              f"{f.get('f0_max_semitone_jump', 0):>7.2f}st  "
              f"{w['session']:<40}  c{w['chunk']:02d}/v{w['version']:02d}  "
              f"{ctrl}{flag}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    full_results = make_serializable({
        "generated": datetime.now().isoformat(),
        "n_scanned": len(all_wavs),
        "n_flagged": len(flagged),
        "population_stats": pop_stats,
        "score_weights": SCORE_WEIGHTS,
        "flag_thresholds": {
            "score": SCORE_FLAG_THRESHOLD,
            "f0_max_semitone_jump": F0_JUMP_FLAG_THRESHOLD,
        },
        "results": [{
            "session": w["session"], "chunk": w["chunk"], "version": w["version"],
            "wav_path": w["wav_path"], "text": w.get("text", ""),
            "is_control": w.get("is_control", False),
            "control_note": w.get("control_note", ""),
            "breakout_score": w.get("breakout_score", 0),
            "flagged": w.get("flagged", False),
            "features": w.get("features"),
            "z_scores": w.get("z_scores", {}),
        } for w in all_wavs],
    })

    with open(OUTPUT_DIR / "breakout_scan_results.json", 'w') as f:
        json.dump(full_results, f, indent=2)

    suspects_data = make_serializable({
        "generated": datetime.now().isoformat(),
        "n_flagged": len(flagged),
        "suspects": [{
            "session": w["session"], "chunk": w["chunk"], "version": w["version"],
            "wav_path": w["wav_path"], "text": w.get("text", ""),
            "is_control": w.get("is_control", False),
            "breakout_score": w.get("breakout_score", 0),
            "features": w.get("features"),
            "z_scores": w.get("z_scores", {}),
        } for w in flagged],
    })

    with open(OUTPUT_DIR / "breakout_suspects.json", 'w') as f:
        json.dump(suspects_data, f, indent=2)

    print(f"\n  Results saved to {OUTPUT_DIR}/")
    return all_wavs, flagged


def run_picker():
    """Generate HTML picker from last scan results."""
    suspects_path = OUTPUT_DIR / "breakout_suspects.json"
    results_path = OUTPUT_DIR / "breakout_scan_results.json"

    if not suspects_path.exists() or not results_path.exists():
        print("ERROR: Run --scan first to generate scan results")
        sys.exit(1)

    with open(suspects_path) as f:
        suspects_data = json.load(f)
    with open(results_path) as f:
        results_data = json.load(f)

    suspects = suspects_data["suspects"]
    n_total = results_data["n_scanned"]

    if not suspects:
        print("No suspects flagged — nothing to label.")
        return

    # Sort: controls first, then by score descending
    suspects.sort(key=lambda x: (not x.get("is_control", False), -x.get("breakout_score", 0)))

    print(f"  Generating picker for {len(suspects)} suspects...")
    html = generate_picker_html(suspects, results_data["results"])

    picker_path = OUTPUT_DIR / "breakout-picker.html"
    with open(picker_path, 'w') as f:
        f.write(html)

    print(f"  Picker: {picker_path}")
    print(f"  Open: file://{picker_path}")
    return picker_path


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Voice Breakout Scanner (Gate 17)")
    parser.add_argument('--scan', action='store_true',
                        help='Scan 5 random sessions + 2 controls')
    parser.add_argument('--sessions', nargs='+',
                        help='Specific session prefixes to scan (+ controls)')
    parser.add_argument('--all', action='store_true',
                        help='Scan all deployed sessions')
    parser.add_argument('--picker', action='store_true',
                        help='Generate HTML picker from last scan')
    args = parser.parse_args()

    if not (args.scan or args.picker or args.all):
        parser.print_help()
        return

    if args.scan or args.all:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if args.all:
            run_scan_all(args.sessions)
        elif args.sessions:
            run_scan(args.sessions)
        else:
            run_scan(None)

    if args.picker or args.scan or args.all:
        if args.scan or args.all:
            # Auto-generate picker after scan
            run_picker()
        elif args.picker:
            run_picker()


if __name__ == '__main__':
    main()
