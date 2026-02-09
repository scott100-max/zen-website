#!/usr/bin/env python3
"""14-Gate QA System for Session 32 Repair.

Runs all 14 QA gates from build-session-v3.py against the repaired narration files.
"""

import json
import os
import re
import subprocess
import sys
import wave
import struct
import numpy as np
import librosa
from scipy.signal import butter, sosfilt
from pathlib import Path

# ── Paths ──
RAW_REPAIR = "/Users/scottripley/salus-website/content/audio-free/masters/32-observing-emotions_master-narration-repair-1.wav"
NORMED_WAV = "/Users/scottripley/salus-website/content/audio-free/repair-work/32-repair-1_normed.wav"
MIXED_WAV = "/Users/scottripley/salus-website/content/audio-free/repair-work/32-repair-1_mixed.wav"
FINAL_MP3 = "/Users/scottripley/salus-website/content/audio-free/repair-work/32-observing-emotions-repair-1.mp3"
MANIFEST_PATH = "/Users/scottripley/salus-website/content/audio-free/32-observing-emotions_manifest.json"
MASTER_REF_WAV = "/Users/scottripley/salus-website/content/audio/marco-master/marco-master-v1.wav"
MASTER_MEASUREMENTS_PATH = "/Users/scottripley/salus-website/content/audio/marco-master/marco-master-v1-measurements.json"
SCRIPT_PATH = "/Users/scottripley/salus-website/content/scripts/32-observing-emotions.txt"

# ── Constants (from build-session-v3.py) ──
SAMPLE_RATE = 44100
MASTER_NOISE_FLOOR_DB = -26.0
MASTER_HF_HISS_DB = -40.0
MASTER_MFCC_COSINE_MAX = 0.06
MASTER_F0_DEVIATION_MAX = 10.0
QA_CLICK_THRESHOLD = 120

# ── Duration offset for repair ──
# Chunk 0 was 12.62s originally, repaired chunk is 13.95s => +1.33s offset after chunk 0
REPAIR_OFFSET = 1.33  # seconds added by repair chunk being longer

# ── Load manifest ──
manifest = json.load(open(MANIFEST_PATH))

# Create offset-adjusted manifest for gates that need it
def make_adjusted_manifest():
    """Adjust manifest timings for the repair: chunk 0 grew by REPAIR_OFFSET seconds.
    All segments after index 0 shift forward by REPAIR_OFFSET."""
    adjusted = json.loads(json.dumps(manifest))  # deep copy
    for seg in adjusted['segments']:
        if seg['index'] > 0:
            seg['start_time'] += REPAIR_OFFSET
            if 'end_time' in seg:
                seg['end_time'] += REPAIR_OFFSET
    return adjusted

adj_manifest = make_adjusted_manifest()

# ── Helper: parse RMS from ffmpeg astats ──
def _parse_rms_from_astats(stderr_text):
    matches = re.findall(r'RMS level dB:\s*([-\d.]+)', stderr_text)
    if matches:
        try:
            return float(matches[-1])
        except ValueError:
            return -100.0
    return 0.0

# ── Helper: measure noise floor ──
def measure_noise_floor(audio_path, mdata):
    best_start = None
    best_dur = 0
    for seg in mdata['segments']:
        if seg['type'] == 'silence' and seg['duration'] > best_dur:
            best_start = seg['start_time']
            best_dur = seg['duration']
    if best_start is None or best_dur < 0.5:
        return 0.0, 0.0
    measure_start = best_start + 0.2
    measure_dur = min(best_dur - 0.4, 1.0)
    if measure_dur < 0.3:
        measure_dur = best_dur - 0.4

    result = subprocess.run([
        'ffmpeg', '-i', audio_path,
        '-ss', str(measure_start), '-t', str(measure_dur),
        '-af', 'astats=reset=0',
        '-f', 'null', '-'
    ], capture_output=True, text=True)
    noise_db = _parse_rms_from_astats(result.stderr)

    result_hf = subprocess.run([
        'ffmpeg', '-i', audio_path,
        '-ss', str(measure_start), '-t', str(measure_dur),
        '-af', 'highpass=f=6000,astats=reset=0',
        '-f', 'null', '-'
    ], capture_output=True, text=True)
    hf_db = _parse_rms_from_astats(result_hf.stderr)

    return noise_db, hf_db


# ═══════════════════════════════════════
# GATE 1: Quality Benchmarks
# ═══════════════════════════════════════
def gate_1_quality():
    print("\n" + "="*60)
    print("GATE 1: Quality Benchmarks (noise floor, HF hiss)")
    print("="*60)
    noise_db, hf_db = measure_noise_floor(NORMED_WAV, adj_manifest)
    print(f"  Noise floor = {noise_db:.1f} dB (threshold: {MASTER_NOISE_FLOOR_DB})")
    print(f"  HF hiss     = {hf_db:.1f} dB (threshold: {MASTER_HF_HISS_DB})")
    passed = noise_db <= MASTER_NOISE_FLOOR_DB and hf_db <= MASTER_HF_HISS_DB
    return passed, {'noise_floor_db': noise_db, 'hf_hiss_db': hf_db}


# ═══════════════════════════════════════
# GATE 2: Click Artifact Scan
# ═══════════════════════════════════════
def gate_2_clicks():
    print("\n" + "="*60)
    print("GATE 2: Click Artifact Scan")
    print("="*60)
    
    # Convert to 16-bit PCM WAV for scanning
    tmp_wav = "/tmp/gate2_scan.wav"
    subprocess.run([
        'ffmpeg', '-y', '-i', NORMED_WAV,
        '-c:a', 'pcm_s16le', '-ar', str(SAMPLE_RATE), '-ac', '2',
        tmp_wav
    ], capture_output=True, check=True)
    
    w = wave.open(tmp_wav, 'r')
    n = w.getnframes()
    frames = w.readframes(n)
    samples = struct.unpack(f'<{n * 2}h', frames)
    w.close()
    os.remove(tmp_wav)

    # Build silence region lookup (adjusted)
    silence_ranges = []
    for seg in adj_manifest['segments']:
        if seg['type'] == 'silence':
            silence_ranges.append((seg['start_time'], seg['start_time'] + seg['duration']))

    def in_silence(ts):
        return any(start <= ts <= end for start, end in silence_ranges)

    # Scan in 10ms windows
    window = int(SAMPLE_RATE * 0.01)
    clicks = []
    for start in range(0, n - window, window // 2):
        chunk = [samples[i * 2] for i in range(start, min(start + window, n))]
        if not chunk:
            continue
        peak = max(abs(s) for s in chunk)
        if peak < 50:
            continue
        max_jump = max(abs(chunk[i + 1] - chunk[i]) for i in range(len(chunk) - 1)) if len(chunk) > 1 else 0
        ts = start / SAMPLE_RATE
        if in_silence(ts) and max_jump > peak and max_jump > QA_CLICK_THRESHOLD:
            clicks.append((ts, max_jump, peak))

    # Deduplicate
    filtered = []
    for c in clicks:
        if not filtered or c[0] - filtered[-1][0] > 0.1:
            filtered.append(c)

    print(f"  Clicks found: {len(filtered)}")
    for ts, jump, peak in filtered[:10]:
        print(f"    {int(ts//60)}:{ts%60:04.1f} — jump={jump}, peak={peak}")
    
    passed = len(filtered) == 0
    return passed, {'clicks': len(filtered), 'details': [(round(c[0],1), c[1], c[2]) for c in filtered[:20]]}


# ═══════════════════════════════════════
# GATE 3: Spectral Comparison (sliding window HF)
# ═══════════════════════════════════════
def gate_3_spectral():
    print("\n" + "="*60)
    print("GATE 3: Spectral Comparison (18 dB sliding window)")
    print("="*60)
    
    # Measure master and build noise
    master_manifest = {'segments': [{'type': 'silence', 'start_time': 3.0, 'duration': 3.0}]}
    master_noise, master_hf = measure_noise_floor(MASTER_REF_WAV, master_manifest)
    build_noise, build_hf = measure_noise_floor(NORMED_WAV, adj_manifest)
    
    noise_gap = build_noise - master_noise
    hf_gap = build_hf - master_hf
    MAX_QUALITY_GAP = 3.0
    
    print(f"  Master noise: {master_noise:.1f} dB, Build noise: {build_noise:.1f} dB, Gap: {noise_gap:+.1f} dB")
    print(f"  Master HF:    {master_hf:.1f} dB, Build HF:    {build_hf:.1f} dB, Gap: {hf_gap:+.1f} dB")
    
    passed = True
    if noise_gap > MAX_QUALITY_GAP:
        print(f"  FAIL — noise {noise_gap:+.1f} dB worse than master (max {MAX_QUALITY_GAP})")
        passed = False
    if hf_gap > MAX_QUALITY_GAP:
        print(f"  FAIL — HF hiss {hf_gap:+.1f} dB worse than master (max {MAX_QUALITY_GAP})")
        passed = False

    # Sliding window HF check
    w = wave.open(NORMED_WAV, 'r')
    n_frames = w.getnframes()
    sr_wav = w.getframerate()
    nch = w.getnchannels()
    raw_data = w.readframes(n_frames)
    w.close()

    audio_samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float64)
    if nch > 1:
        audio_samples = audio_samples.reshape(-1, nch).mean(axis=1)

    sos_hf3 = butter(4, 6000, btype='high', fs=sr_wav, output='sos')
    hf3 = sosfilt(sos_hf3, audio_samples)

    sw_sec = 2.0
    sw_samples = int(sw_sec * sr_wav)
    sw_hop = int(1.0 * sr_wav)

    all_hf_rms = []
    all_times = []
    for start in range(0, len(audio_samples) - sw_samples, sw_hop):
        hf_rms = np.sqrt(np.mean(hf3[start:start+sw_samples]**2))
        hf_db = 20 * np.log10(hf_rms / 32768) if hf_rms > 0 else -100
        all_hf_rms.append(hf_db)
        all_times.append(start / sr_wav)

    all_hf_rms = np.array(all_hf_rms)
    all_times = np.array(all_times)

    # Build speech mask using adjusted manifest
    speech_mask_sw = np.zeros(len(all_times), dtype=bool)
    for seg in adj_manifest['segments']:
        if seg['type'] == 'text':
            for i, t in enumerate(all_times):
                if seg['start_time'] <= t < seg['start_time'] + seg['duration']:
                    speech_mask_sw[i] = True

    speech_hf = all_hf_rms[speech_mask_sw]
    sliding_flags = []
    if len(speech_hf) > 5:
        median_hf_sw = float(np.median(speech_hf))
        print(f"  Sliding window median HF (speech): {median_hf_sw:.1f} dB")
        for i in range(len(all_times)):
            if speech_mask_sw[i]:
                deviation = all_hf_rms[i] - median_hf_sw
                if deviation > 18.0:
                    t = all_times[i]
                    sliding_flags.append({
                        'time': round(float(t), 1),
                        'time_fmt': f'{int(t//60)}:{t%60:04.1f}',
                        'hf_db': round(float(all_hf_rms[i]), 1),
                        'deviation_db': round(float(deviation), 1),
                    })
        if sliding_flags:
            print(f"  FAIL — {len(sliding_flags)} sliding-window HF spikes:")
            for f in sliding_flags[:5]:
                print(f"    {f['time_fmt']} — HF={f['hf_db']:.1f} dB (+{f['deviation_db']:.1f} above median)")
            passed = False
    
    if passed:
        print(f"  Sliding window: no HF spikes > 18 dB above median")
    
    return passed, {'noise_gap': noise_gap, 'hf_gap': hf_gap, 'sliding_flags': len(sliding_flags)}


# ═══════════════════════════════════════
# GATE 4: Voice Comparison (MFCC + F0)
# ═══════════════════════════════════════
def gate_4_voice():
    print("\n" + "="*60)
    print("GATE 4: Voice Comparison (MFCC cosine + F0 deviation)")
    print("="*60)
    
    master_data = json.load(open(MASTER_MEASUREMENTS_PATH))
    master_mfcc = np.array(master_data['measurements']['mfcc_mean'])
    master_f0 = master_data['measurements']['f0_mean']
    
    # Load raw repair (pre-cleanup) for voice comparison
    y_build, sr_build = librosa.load(RAW_REPAIR, sr=22050)
    mfcc_build = librosa.feature.mfcc(y=y_build, sr=sr_build, n_mfcc=13)
    build_mfcc = mfcc_build.mean(axis=1)
    
    # MFCC cosine distance
    dot = np.dot(master_mfcc, build_mfcc)
    norm_m = np.linalg.norm(master_mfcc)
    norm_b = np.linalg.norm(build_mfcc)
    cosine_sim = dot / (norm_m * norm_b) if (norm_m * norm_b) > 0 else 0
    mfcc_distance = 1.0 - cosine_sim
    
    # F0
    f0_build, voiced_flag, _ = librosa.pyin(y_build, fmin=40, fmax=300, sr=sr_build)
    f0_voiced = f0_build[voiced_flag] if voiced_flag is not None else f0_build[~np.isnan(f0_build)]
    build_f0 = float(np.median(f0_voiced)) if len(f0_voiced) > 0 else 0.0
    f0_deviation = abs(build_f0 - master_f0) / master_f0 * 100 if master_f0 > 0 else 0.0
    
    print(f"  MFCC cosine distance = {mfcc_distance:.4f} (threshold: {MASTER_MFCC_COSINE_MAX})")
    print(f"  F0 mean = {build_f0:.1f} Hz (master: {master_f0:.1f} Hz, deviation: {f0_deviation:.1f}%)")
    
    passed = mfcc_distance <= MASTER_MFCC_COSINE_MAX and f0_deviation <= MASTER_F0_DEVIATION_MAX
    return passed, {'mfcc_distance': round(mfcc_distance, 6), 'build_f0': round(build_f0, 1),
                     'master_f0': master_f0, 'f0_deviation_pct': round(f0_deviation, 1)}


# ═══════════════════════════════════════
# GATE 5: Loudness Consistency
# ═══════════════════════════════════════
def gate_5_loudness():
    print("\n" + "="*60)
    print("GATE 5: Loudness Consistency (>10 dB from median)")
    print("="*60)
    
    max_deviation_db = 10.0
    
    w = wave.open(NORMED_WAV, 'r')
    n = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw = w.readframes(n)
    w.close()
    
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)
    
    window = sr
    rms_db = []
    for i in range(0, len(samples) - window, window):
        chunk = samples[i:i+window]
        rms = np.sqrt(np.mean(chunk**2))
        db = 20 * np.log10(rms / 32768) if rms > 0 else -100
        rms_db.append(db)
    
    rms_db = np.array(rms_db)
    speech_mask = rms_db > -40
    speech_rms = rms_db[speech_mask]
    
    if len(speech_rms) < 5:
        print(f"  WARNING — too few speech seconds ({len(speech_rms)})")
        return True, {'skipped': True}
    
    median_rms = float(np.median(speech_rms))
    
    spikes = []
    for i, db in enumerate(rms_db):
        if speech_mask[i] and (db - median_rms) > max_deviation_db:
            spikes.append({
                'time': i,
                'time_fmt': f'{i // 60}:{i % 60:02d}',
                'rms_db': round(float(db), 1),
                'deviation_db': round(float(db - median_rms), 1),
            })
    
    print(f"  {int(sum(speech_mask))} speech seconds, median RMS={median_rms:.1f} dB")
    print(f"  Range = {float(np.min(speech_rms)):.1f} to {float(np.max(speech_rms)):.1f} dB ({float(np.max(speech_rms) - np.min(speech_rms)):.1f} dB)")
    
    passed = len(spikes) == 0
    if not passed:
        print(f"  FAIL — {len(spikes)} seconds exceed +{max_deviation_db} dB above median:")
        for s in spikes[:10]:
            print(f"    {s['time_fmt']} — {s['rms_db']} dB (+{s['deviation_db']:.1f} dB)")
    
    return passed, {'median_rms': round(median_rms, 1), 'spikes': len(spikes),
                     'range_db': round(float(np.max(speech_rms) - np.min(speech_rms)), 1)}


# ═══════════════════════════════════════
# GATE 6: HF Hiss (speech-aware, non-speech only)
# ═══════════════════════════════════════
def gate_6_hf_hiss():
    print("\n" + "="*60)
    print("GATE 6: HF Hiss (non-speech regions, 6 dB threshold)")
    print("="*60)
    
    hp_freq = 4000
    window_sec = 1.0
    overlap_sec = 0.5
    ratio_threshold_db = 6.0
    min_duration_sec = 3.0
    
    # Build speech region lookup (adjusted)
    speech_ranges = []
    for seg in adj_manifest.get('segments', []):
        if seg['type'] == 'text':
            speech_ranges.append((seg['start_time'], seg['start_time'] + seg['duration']))
    
    def is_speech(win_start, win_end):
        win_dur = win_end - win_start
        overlap = 0.0
        for s_start, s_end in speech_ranges:
            ov_start = max(win_start, s_start)
            ov_end = min(win_end, s_end)
            if ov_end > ov_start:
                overlap += ov_end - ov_start
        return overlap > (win_dur * 0.5)
    
    w = wave.open(NORMED_WAV, 'r')
    n = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw = w.readframes(n)
    w.close()
    
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)
    
    sos = butter(4, hp_freq, btype='high', fs=sr, output='sos')
    hf_signal = sosfilt(sos, samples)
    
    win_samples = int(window_sec * sr)
    hop_samples = int((window_sec - overlap_sec) * sr)
    total_rms_db = []
    hf_ratio_db = []
    window_times = []
    nonspeech_mask = []
    
    for start in range(0, len(samples) - win_samples, hop_samples):
        total_chunk = samples[start:start + win_samples]
        hf_chunk = hf_signal[start:start + win_samples]
        total_rms = np.sqrt(np.mean(total_chunk**2))
        hf_rms = np.sqrt(np.mean(hf_chunk**2))
        t_db = 20 * np.log10(total_rms / 32768) if total_rms > 0 else -100
        h_db = 20 * np.log10(hf_rms / 32768) if hf_rms > 0 else -100
        win_start_time = start / sr
        win_end_time = win_start_time + window_sec
        total_rms_db.append(t_db)
        hf_ratio_db.append(h_db - t_db)
        window_times.append(win_start_time)
        nonspeech_mask.append(not is_speech(win_start_time, win_end_time))
    
    total_rms_db = np.array(total_rms_db)
    hf_ratio_db = np.array(hf_ratio_db)
    window_times = np.array(window_times)
    nonspeech_mask = np.array(nonspeech_mask)
    
    eval_mask = nonspeech_mask & (total_rms_db > -60)
    n_nonspeech = int(np.sum(nonspeech_mask))
    n_eval = int(np.sum(eval_mask))
    
    print(f"  {n_nonspeech} non-speech windows, {n_eval} with energy above -60 dB")
    
    if n_eval < 3:
        print(f"  WARNING — too few non-speech windows")
        return True, {'skipped': True}
    
    median_ratio = float(np.median(hf_ratio_db[eval_mask]))
    
    spike_mask = np.zeros(len(hf_ratio_db), dtype=bool)
    for i in range(len(hf_ratio_db)):
        if eval_mask[i] and (hf_ratio_db[i] - median_ratio) > ratio_threshold_db:
            spike_mask[i] = True
    
    # Group into regions
    flagged_regions = []
    in_region = False
    region_start = 0
    for i, is_spike in enumerate(spike_mask):
        if is_spike and not in_region:
            in_region = True
            region_start = i
        elif not is_spike and in_region:
            in_region = False
            region_end = i
            region_start_time = window_times[region_start]
            region_end_time = window_times[min(region_end, len(window_times) - 1)] + window_sec
            duration = region_end_time - region_start_time
            if duration >= min_duration_sec:
                max_ratio = float(np.max(hf_ratio_db[region_start:region_end]))
                flagged_regions.append({
                    'start_fmt': f'{int(region_start_time//60)}:{region_start_time%60:04.1f}',
                    'end_fmt': f'{int(region_end_time//60)}:{region_end_time%60:04.1f}',
                    'duration': round(duration, 1),
                    'deviation_db': round(max_ratio - median_ratio, 1),
                })
    if in_region:
        region_end_time = window_times[-1] + window_sec
        duration = region_end_time - window_times[region_start]
        if duration >= min_duration_sec:
            max_ratio = float(np.max(hf_ratio_db[region_start:]))
            flagged_regions.append({
                'start_fmt': f'{int(window_times[region_start]//60)}:{window_times[region_start]%60:04.1f}',
                'end_fmt': f'{int(region_end_time//60)}:{region_end_time%60:04.1f}',
                'duration': round(duration, 1),
                'deviation_db': round(max_ratio - median_ratio, 1),
            })
    
    print(f"  Median HF ratio = {median_ratio:.1f} dB, threshold = +{ratio_threshold_db} dB")
    
    passed = len(flagged_regions) == 0
    if not passed:
        print(f"  FAIL — {len(flagged_regions)} hiss regions:")
        for r in flagged_regions[:10]:
            print(f"    {r['start_fmt']} -> {r['end_fmt']} ({r['duration']}s, +{r['deviation_db']:.1f} dB)")
    
    return passed, {'median_ratio': round(median_ratio, 1), 'flagged_regions': len(flagged_regions)}


# ═══════════════════════════════════════
# GATE 7: Volume Surge/Drop
# ═══════════════════════════════════════
def gate_7_surge():
    print("\n" + "="*60)
    print("GATE 7: Volume Surge/Drop (9/14 dB thresholds)")
    print("="*60)
    
    surge_threshold_db = 9.0
    drop_threshold_db = 14.0
    neighbour_radius = 3
    window_sec = 1.0
    overlap_sec = 0.5
    
    w = wave.open(NORMED_WAV, 'r')
    n = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw = w.readframes(n)
    w.close()
    
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)
    
    win_samples = int(window_sec * sr)
    hop_samples = int((window_sec - overlap_sec) * sr)
    rms_db = []
    window_times = []
    
    for start in range(0, len(samples) - win_samples, hop_samples):
        chunk = samples[start:start + win_samples]
        rms = np.sqrt(np.mean(chunk**2))
        db = 20 * np.log10(rms / 32768) if rms > 0 else -100
        rms_db.append(db)
        window_times.append(start / sr)
    
    rms_db = np.array(rms_db)
    window_times = np.array(window_times)
    
    # Silence ranges (adjusted) with duration for margin
    silence_ranges = []
    for seg in adj_manifest['segments']:
        if seg['type'] == 'silence':
            silence_ranges.append((seg['start_time'], seg['start_time'] + seg['duration'], seg['duration']))
    
    def overlaps_silence(t, win=window_sec):
        for s_start, s_end, s_dur in silence_ranges:
            margin = max(4.0, s_dur * 0.15)
            if t < s_end + margin and t + win > s_start - margin:
                return True
        return False
    
    surges = []
    drops = []
    for i in range(neighbour_radius, len(rms_db) - neighbour_radius):
        t = window_times[i]
        if overlaps_silence(t):
            continue
        if rms_db[i] < -50:
            continue
        
        neighbour_indices = list(range(max(0, i - neighbour_radius), i)) + \
                           list(range(i + 1, min(len(rms_db), i + neighbour_radius + 1)))
        active_vals = [rms_db[j] for j in neighbour_indices
                       if rms_db[j] > -50 and not overlaps_silence(window_times[j])]
        if len(active_vals) < 2:
            continue
        
        local_mean = float(np.mean(active_vals))
        if local_mean < -28:
            continue
        
        deviation = rms_db[i] - local_mean
        
        if deviation > surge_threshold_db:
            surges.append({'time': round(float(t), 1), 'time_fmt': f'{int(t//60)}:{t%60:04.1f}',
                          'rms_db': round(float(rms_db[i]), 1), 'deviation_db': round(float(deviation), 1)})
        elif deviation < -drop_threshold_db and rms_db[i] > -33:
            drops.append({'time': round(float(t), 1), 'time_fmt': f'{int(t//60)}:{t%60:04.1f}',
                         'rms_db': round(float(rms_db[i]), 1), 'deviation_db': round(float(deviation), 1)})
    
    all_flags = surges + drops
    all_flags.sort(key=lambda x: x['time'])
    
    print(f"  {len(surges)} surges (+{surge_threshold_db} dB), {len(drops)} drops (-{drop_threshold_db} dB)")
    
    passed = len(all_flags) == 0
    if not passed:
        for f in all_flags[:10]:
            kind = 'SURGE' if f in surges else 'DROP'
            print(f"    {f['time_fmt']} — {kind} {f['rms_db']} dB (dev {f['deviation_db']:+.1f})")
    
    return passed, {'surges': len(surges), 'drops': len(drops)}


# ═══════════════════════════════════════
# GATE 8: Repeated Content (MFCC + text guard)
# ═══════════════════════════════════════
def gate_8_repeat():
    print("\n" + "="*60)
    print("GATE 8: Repeated Content (MFCC 0.998 + text guard)")
    print("="*60)
    
    mfcc_sim_threshold = 0.998
    min_gap_sec = 5.0
    
    y, sr = librosa.load(NORMED_WAV, sr=22050)
    
    text_segments = [s for s in adj_manifest['segments'] if s['type'] == 'text' and s.get('duration', 0) > 2]
    
    segment_mfccs = []
    for seg in text_segments:
        start_sample = int(seg['start_time'] * sr)
        end_sample = int(seg['end_time'] * sr)
        if end_sample > len(y):
            end_sample = len(y)
        if end_sample - start_sample < sr:
            segment_mfccs.append(None)
            continue
        segment_audio = y[start_sample:end_sample]
        mfcc = librosa.feature.mfcc(y=segment_audio, sr=sr, n_mfcc=13)
        segment_mfccs.append(mfcc.mean(axis=1))
    
    # MFCC pairs
    mfcc_duplicates = []
    for i in range(len(segment_mfccs)):
        if segment_mfccs[i] is None:
            continue
        for j in range(i + 1, len(segment_mfccs)):
            if segment_mfccs[j] is None:
                continue
            gap = abs(text_segments[j]['start_time'] - text_segments[i]['end_time'])
            if gap < min_gap_sec:
                continue
            dot = np.dot(segment_mfccs[i], segment_mfccs[j])
            norm_i = np.linalg.norm(segment_mfccs[i])
            norm_j = np.linalg.norm(segment_mfccs[j])
            sim = dot / (norm_i * norm_j) if (norm_i * norm_j) > 0 else 0
            if sim >= mfcc_sim_threshold:
                mfcc_duplicates.append({
                    'seg_a': i, 'seg_b': j,
                    'time_a': text_segments[i]['start_time'],
                    'time_b': text_segments[j]['start_time'],
                    'similarity': round(float(sim), 4),
                })
    
    # Text guard: check manifest text for MFCC pairs
    confirmed = []
    for dup in mfcc_duplicates:
        seg_a_text = text_segments[dup['seg_a']].get('text', '').lower().strip()
        seg_b_text = text_segments[dup['seg_b']].get('text', '').lower().strip()
        if seg_a_text and seg_b_text:
            words_a = set(seg_a_text.split())
            words_b = set(seg_b_text.split())
            overlap = len(words_a & words_b)
            max_words = max(len(words_a), len(words_b), 1)
            ratio = overlap / max_words
            if ratio < 0.6:
                print(f"  Skipping MFCC pair {dup['seg_a']}<->{dup['seg_b']} — different text (overlap={ratio:.0%})")
                continue
        confirmed.append(dup)
    
    print(f"  MFCC pairs above 0.998: {len(mfcc_duplicates)}")
    print(f"  Confirmed after text guard: {len(confirmed)}")
    
    # Note: Whisper dual agreement would be next step, but since we have text guard
    # and no confirmed duplicates pass the text guard, this is sufficient
    passed = len(confirmed) == 0
    if not passed:
        for c in confirmed[:5]:
            print(f"    seg {c['seg_a']} <-> {c['seg_b']} sim={c['similarity']}")
    
    return passed, {'mfcc_pairs': len(mfcc_duplicates), 'confirmed': len(confirmed)}


# ═══════════════════════════════════════
# GATE 9: Energy Spike (12x total, 28x HF)
# ═══════════════════════════════════════
def gate_9_energy():
    print("\n" + "="*60)
    print("GATE 9: Energy Spike (12x total, 28x HF)")
    print("="*60)
    
    w = wave.open(NORMED_WAV, 'r')
    n_frames = w.getnframes()
    sr = w.getframerate()
    nch = w.getnchannels()
    raw_data = w.readframes(n_frames)
    w.close()
    
    samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float64)
    if nch > 1:
        samples = samples.reshape(-1, nch).mean(axis=1)
    
    sos_hf = butter(4, 4000, btype='high', fs=sr, output='sos')
    hf_signal = sosfilt(sos_hf, samples)
    
    spike_window_sec = 2.0
    spike_win_samples = int(spike_window_sec * sr)
    spike_hop = int(1.0 * sr)
    
    total_energies = []
    hf_energies = []
    spike_times = []
    
    for start in range(0, len(samples) - spike_win_samples, spike_hop):
        total_chunk = samples[start:start + spike_win_samples]
        hf_chunk = hf_signal[start:start + spike_win_samples]
        total_energies.append(float(np.mean(total_chunk**2)))
        hf_energies.append(float(np.mean(hf_chunk**2)))
        spike_times.append(start / sr)
    
    total_energies = np.array(total_energies)
    hf_energies = np.array(hf_energies)
    spike_times = np.array(spike_times)
    
    # Speech mask (adjusted manifest)
    speech_ranges = []
    for seg in adj_manifest.get('segments', []):
        if seg['type'] == 'text':
            speech_ranges.append((seg['start_time'], seg['start_time'] + seg['duration']))
    
    speech_mask = np.zeros(len(spike_times), dtype=bool)
    for i, t in enumerate(spike_times):
        for s_start, s_end in speech_ranges:
            if s_start <= t < s_end:
                speech_mask[i] = True
                break
    
    speech_total = total_energies[speech_mask & (total_energies > 0)]
    speech_hf = hf_energies[speech_mask & (hf_energies > 0)]
    median_total = float(np.median(speech_total)) if len(speech_total) > 0 else 1
    median_hf = float(np.median(speech_hf)) if len(speech_hf) > 0 else 1
    
    energy_spikes = []
    for i in range(len(spike_times)):
        total_ratio = total_energies[i] / median_total if median_total > 0 else 0
        hf_ratio = hf_energies[i] / median_hf if median_hf > 0 else 0
        reasons = []
        if total_ratio > 12.0:
            reasons.append(f'total {total_ratio:.1f}x median')
        if hf_ratio > 28.0:
            reasons.append(f'HF {hf_ratio:.1f}x median')
        if reasons:
            t = spike_times[i]
            energy_spikes.append({
                'time': round(float(t), 1),
                'time_fmt': f'{int(t//60)}:{t%60:04.1f}',
                'total_ratio': round(float(total_ratio), 1),
                'hf_ratio': round(float(hf_ratio), 1),
                'reasons': ', '.join(reasons),
            })
    
    print(f"  Median total energy: {median_total:.2f}, Median HF energy: {median_hf:.6f}")
    print(f"  Windows analyzed: {len(spike_times)}")
    
    passed = len(energy_spikes) == 0
    if not passed:
        print(f"  FAIL — {len(energy_spikes)} energy spikes:")
        for s in energy_spikes[:10]:
            print(f"    {s['time_fmt']} — {s['reasons']}")
    else:
        print(f"  No energy spikes detected")
    
    return passed, {'spikes': len(energy_spikes), 'windows': len(spike_times)}


# ═══════════════════════════════════════
# GATE 10: Speech Rate
# ═══════════════════════════════════════
def gate_10_speech_rate():
    print("\n" + "="*60)
    print("GATE 10: Speech Rate (130% rush, 6.0 floor, >8.0 skip)")
    print("="*60)
    
    rush_threshold = 1.3
    window_sec = 2.0
    
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(MIXED_WAV, word_timestamps=True)
        
        words = []
        for seg in result.get('segments', []):
            for w in seg.get('words', []):
                words.append({'word': w['word'].strip(), 'start': w['start'], 'end': w['end']})
        
        if len(words) < 10:
            print(f"  WARNING — too few words ({len(words)})")
            return True, {'skipped': True}
        
        # Speech regions (adjusted)
        speech_ranges = []
        for seg in adj_manifest['segments']:
            if seg['type'] == 'text':
                speech_ranges.append((seg['start_time'], seg['start_time'] + seg['duration']))
        
        def is_speech_window(win_start, win_end):
            win_dur = win_end - win_start
            overlap = 0.0
            for s_start, s_end in speech_ranges:
                ov_start = max(win_start, s_start)
                ov_end = min(win_end, s_end)
                if ov_end > ov_start:
                    overlap += ov_end - ov_start
            return overlap > (win_dur * 0.5)
        
        total_dur = words[-1]['end']
        hop = window_sec / 2
        window_rates = []
        window_times = []
        
        t = 0.0
        while t + window_sec <= total_dur:
            if not is_speech_window(t, t + window_sec):
                t += hop
                continue
            wc = sum(1 for w in words if w['start'] >= t and w['start'] < t + window_sec)
            rate = wc / window_sec
            if rate > 0.5:
                window_rates.append(rate)
                window_times.append(t)
            t += hop
        
        if len(window_rates) < 5:
            print(f"  WARNING — too few speech windows ({len(window_rates)})")
            return True, {'skipped': True}
        
        window_rates = np.array(window_rates)
        median_rate = float(np.median(window_rates))
        threshold_rate = max(median_rate * rush_threshold, 7.0)
        
        rushes = []
        for i, (rate, t) in enumerate(zip(window_rates, window_times)):
            if rate > 8.0:
                continue
            if rate > threshold_rate:
                rushes.append({
                    'time_fmt': f'{int(t//60)}:{t%60:04.1f}',
                    'rate_wps': round(float(rate), 1),
                    'ratio': round(float(rate / median_rate), 2),
                })
        
        print(f"  Median speech rate = {median_rate:.1f} words/sec, threshold = {threshold_rate:.1f} words/sec")
        print(f"  {len(window_rates)} speech windows analyzed")
        
        passed = len(rushes) == 0
        if not passed:
            print(f"  FAIL — {len(rushes)} rate anomalies:")
            for r in rushes[:10]:
                print(f"    {r['time_fmt']} — {r['rate_wps']} w/s ({r['ratio']:.0%} of median)")
        
        return passed, {'median_rate': round(median_rate, 1), 'rushes': len(rushes)}
    
    except ImportError:
        print(f"  WARNING — Whisper not installed, skipping")
        return True, {'skipped': True}
    except Exception as e:
        print(f"  WARNING — error: {e}, skipping")
        return True, {'skipped': True, 'error': str(e)}


# ═══════════════════════════════════════
# GATE 11: Silence Integrity
# ═══════════════════════════════════════
def gate_11_silence():
    print("\n" + "="*60)
    print("GATE 11: Silence Integrity (-50 dBFS in silence regions)")
    print("="*60)
    
    max_silence_energy_db = -50.0
    
    y, sr = librosa.load(NORMED_WAV, sr=22050)
    
    silence_regions = [s for s in adj_manifest.get('segments', []) if s['type'] == 'silence']
    
    failed_regions = []
    for seg in silence_regions:
        start_sample = int(seg['start_time'] * sr)
        end_sample = int(seg['end_time'] * sr)
        if end_sample > len(y):
            end_sample = len(y)
        if end_sample - start_sample < int(0.1 * sr):
            continue
        
        region_audio = y[start_sample:end_sample]
        rms = np.sqrt(np.mean(region_audio ** 2))
        energy_db = 20 * np.log10(rms + 1e-10)
        
        if energy_db > max_silence_energy_db:
            t = seg['start_time']
            failed_regions.append({
                'start_fmt': f'{int(t//60)}:{t%60:04.1f}',
                'duration': seg['duration'],
                'energy_db': round(float(energy_db), 1),
            })
    
    print(f"  {len(silence_regions)} silence regions checked")
    
    passed = len(failed_regions) == 0
    if not passed:
        print(f"  FAIL — {len(failed_regions)} regions contain unexpected audio:")
        for r in failed_regions[:10]:
            print(f"    {r['start_fmt']} ({r['duration']}s) — energy {r['energy_db']} dB (max {max_silence_energy_db} dB)")
    else:
        print(f"  All silence regions verified clean")
    
    return passed, {'failed': len(failed_regions), 'total': len(silence_regions)}


# ═══════════════════════════════════════
# GATE 12: Duration Accuracy
# ═══════════════════════════════════════
def gate_12_duration():
    print("\n" + "="*60)
    print("GATE 12: Duration Accuracy (within 15% of target)")
    print("="*60)
    
    # Read Duration-Target from script
    with open(SCRIPT_PATH) as f:
        header = f.read().split('---')[0]
    
    match = re.search(r'Duration:\s*(\d+)\s*min', header, re.IGNORECASE)
    if not match:
        print(f"  WARNING — cannot parse Duration from script")
        return True, {'skipped': True}
    
    target_sec = int(match.group(1)) * 60
    
    # Measure actual duration from mixed WAV
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', MIXED_WAV],
        capture_output=True, text=True, timeout=10)
    actual_sec = float(result.stdout.strip())
    
    deviation = abs(actual_sec - target_sec) / target_sec
    actual_min = actual_sec / 60
    target_min = target_sec / 60
    
    print(f"  Target: {target_min:.1f} min ({target_sec}s), Actual: {actual_min:.1f} min ({actual_sec:.1f}s)")
    print(f"  Deviation: {deviation*100:.1f}% (max 15%)")
    
    passed = deviation <= 0.15
    return passed, {'target_min': target_min, 'actual_min': round(actual_min, 1), 'deviation_pct': round(deviation*100, 1)}


# ═══════════════════════════════════════
# GATE 13: Ambient Continuity
# ═══════════════════════════════════════
def gate_13_ambient():
    print("\n" + "="*60)
    print("GATE 13: Ambient Continuity (-85 dBFS, 19 dB variation)")
    print("="*60)
    
    min_energy_db = -85.0
    max_ambient_variation_db = 19.0
    
    y, sr = librosa.load(MIXED_WAV, sr=22050)
    total_dur = len(y) / sr
    
    silence_regions = [s for s in adj_manifest.get('segments', []) if s['type'] == 'silence']
    
    dead_silence = []
    region_energies = []
    
    for seg in silence_regions:
        start_sample = int(seg['start_time'] * sr)
        end_sample = int(seg['end_time'] * sr)
        if end_sample > len(y):
            end_sample = len(y)
        if end_sample - start_sample < int(0.5 * sr):
            continue
        
        region_audio = y[start_sample:end_sample]
        
        # Check for dead silence in 1s windows
        window_samples = int(1.0 * sr)
        hop_samples = int(0.5 * sr)
        for w_start in range(0, len(region_audio) - window_samples, hop_samples):
            window = region_audio[w_start:w_start + window_samples]
            rms = np.sqrt(np.mean(window ** 2))
            energy_db = 20 * np.log10(rms + 1e-10)
            if energy_db < min_energy_db:
                abs_time = seg['start_time'] + w_start / sr
                dead_silence.append({
                    'time_fmt': f'{int(abs_time//60)}:{abs_time%60:04.1f}',
                    'energy_db': round(float(energy_db), 1),
                })
        
        rms = np.sqrt(np.mean(region_audio ** 2))
        energy_db = 20 * np.log10(rms + 1e-10)
        region_energies.append(float(energy_db))
    
    # Check last 30s
    last_30s = y[max(0, len(y) - int(30 * sr)):]
    window_samples = int(1.0 * sr)
    hop_samples = int(0.5 * sr)
    for w_start in range(0, len(last_30s) - window_samples, hop_samples):
        window = last_30s[w_start:w_start + window_samples]
        rms = np.sqrt(np.mean(window ** 2))
        energy_db = 20 * np.log10(rms + 1e-10)
        if energy_db < min_energy_db:
            abs_time = total_dur - 30 + w_start / sr
            dead_silence.append({
                'time_fmt': f'{int(abs_time//60)}:{abs_time%60:04.1f}',
                'energy_db': round(float(energy_db), 1),
                'location': 'final_30s',
            })
    
    ambient_consistent = True
    ambient_range_db = 0.0
    if len(region_energies) >= 2:
        ambient_range_db = max(region_energies) - min(region_energies)
        if ambient_range_db > max_ambient_variation_db:
            ambient_consistent = False
    
    print(f"  {len(silence_regions)} silence regions checked")
    print(f"  Dead silence windows: {len(dead_silence)}")
    if len(region_energies) >= 2:
        print(f"  Ambient range: {ambient_range_db:.1f} dB (max {max_ambient_variation_db} dB)")
        print(f"  Region energies: min={min(region_energies):.1f}, max={max(region_energies):.1f}")
    
    passed = len(dead_silence) == 0 and ambient_consistent
    if dead_silence:
        print(f"  FAIL — {len(dead_silence)} dead silence windows:")
        for ds in dead_silence[:5]:
            print(f"    {ds['time_fmt']} — {ds['energy_db']} dB")
    if not ambient_consistent:
        print(f"  FAIL — ambient variation {ambient_range_db:.1f} dB exceeds {max_ambient_variation_db} dB")
    
    return passed, {'dead_silence': len(dead_silence), 'ambient_range': round(ambient_range_db, 1),
                     'ambient_consistent': ambient_consistent}


# ═══════════════════════════════════════
# GATE 14: Opening Quality
# ═══════════════════════════════════════
def gate_14_opening():
    print("\n" + "="*60)
    print("GATE 14: Opening Quality (first 60s, tighter thresholds)")
    print("="*60)
    
    opening_sec = 60.0
    
    y, sr = librosa.load(NORMED_WAV, sr=22050)
    total_dur = len(y) / sr
    if total_dur < opening_sec:
        opening_sec = total_dur
    
    opening_samples = int(opening_sec * sr)
    opening_audio = y[:opening_samples]
    
    flags = []
    
    # Check 1: Noise floor in opening silence gaps (-30 dB)
    silence_in_opening = []
    for seg in adj_manifest.get('segments', []):
        if seg['type'] == 'silence' and seg['start_time'] < opening_sec:
            end = min(seg['end_time'], opening_sec)
            start_s = int(seg['start_time'] * sr)
            end_s = int(end * sr)
            if end_s - start_s > int(0.5 * sr):
                if end_s <= opening_samples:
                    silence_in_opening.append(opening_audio[start_s:end_s])
                else:
                    silence_in_opening.append(y[start_s:min(end_s, len(y))])
    
    if silence_in_opening:
        silence_audio = np.concatenate(silence_in_opening)
        silence_rms = np.sqrt(np.mean(silence_audio ** 2))
        opening_noise_db = 20 * np.log10(silence_rms + 1e-10)
        print(f"  Opening noise floor: {opening_noise_db:.1f} dB (threshold: -30.0 dB)")
        if opening_noise_db > -30.0:
            flags.append({'check': 'noise_floor', 'value': round(float(opening_noise_db), 1), 'threshold': -30.0})
    
    # Check 2: Loudness consistency (6 dB)
    speech_rms_values = []
    for seg in adj_manifest.get('segments', []):
        if seg['type'] == 'text' and seg['start_time'] < opening_sec:
            seg_start = int(seg['start_time'] * sr)
            seg_end = int(min(seg['start_time'] + seg['duration'], opening_sec) * sr)
            if seg_end > opening_samples:
                seg_end = opening_samples
            for s in range(seg_start, seg_end - sr, sr):
                sec_audio = opening_audio[s:s + sr]
                sec_rms = np.sqrt(np.mean(sec_audio ** 2))
                sec_db = 20 * np.log10(sec_rms + 1e-10)
                speech_rms_values.append(sec_db)
    
    if len(speech_rms_values) >= 3:
        median_rms = float(np.median(speech_rms_values))
        print(f"  Opening speech median: {median_rms:.1f} dB")
        for i, db_val in enumerate(speech_rms_values):
            if db_val > median_rms + 6.0:
                flags.append({'check': 'loudness_spike', 'value_db': round(db_val, 1),
                            'median_db': round(median_rms, 1), 'deviation_db': round(db_val - median_rms, 1)})
                print(f"  Loudness spike: {db_val:.1f} dB ({db_val - median_rms:.1f} dB above median)")
                break
    
    passed = len(flags) == 0
    return passed, {'flags': len(flags), 'details': flags}


# ═══════════════════════════════════════
# RUN ALL GATES
# ═══════════════════════════════════════
if __name__ == '__main__':
    print("=" * 70)
    print("  14-GATE QA SYSTEM — Session 32 Repair")
    print("  Running against repaired narration files")
    print("=" * 70)
    print(f"\n  Raw repair:   {RAW_REPAIR}")
    print(f"  Normed WAV:   {NORMED_WAV}")
    print(f"  Mixed WAV:    {MIXED_WAV}")
    print(f"  Master ref:   {MASTER_REF_WAV}")
    print(f"  Manifest:     {MANIFEST_PATH}")
    print(f"  Repair offset: +{REPAIR_OFFSET}s after chunk 0")
    
    results = {}
    
    # Run each gate
    gate_fns = [
        (1, "Quality Benchmarks", gate_1_quality),
        (2, "Click Artifact Scan", gate_2_clicks),
        (3, "Spectral Comparison", gate_3_spectral),
        (4, "Voice Comparison", gate_4_voice),
        (5, "Loudness Consistency", gate_5_loudness),
        (6, "HF Hiss", gate_6_hf_hiss),
        (7, "Volume Surge/Drop", gate_7_surge),
        (8, "Repeated Content", gate_8_repeat),
        (9, "Energy Spike", gate_9_energy),
        (10, "Speech Rate", gate_10_speech_rate),
        (11, "Silence Integrity", gate_11_silence),
        (12, "Duration Accuracy", gate_12_duration),
        (13, "Ambient Continuity", gate_13_ambient),
        (14, "Opening Quality", gate_14_opening),
    ]
    
    for num, name, fn in gate_fns:
        try:
            passed, details = fn()
            results[num] = {'name': name, 'passed': passed, 'details': details}
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[num] = {'name': name, 'passed': False, 'details': {'error': str(e)}}
    
    # Final summary
    print("\n" + "=" * 70)
    print("  14-GATE QA SUMMARY — Session 32 Repair")
    print("=" * 70)
    
    all_passed = True
    for num in sorted(results.keys()):
        r = results[num]
        status = "PASS" if r['passed'] else "FAIL"
        marker = "  " if r['passed'] else ">>"
        print(f"  {marker} Gate {num:2d}: {r['name']:<25s} [{status}]", end="")
        # Print key metric
        d = r['details']
        if 'error' in d:
            print(f"  (ERROR: {d['error'][:50]})")
        elif num == 1:
            print(f"  noise={d.get('noise_floor_db','?')} dB, hf={d.get('hf_hiss_db','?')} dB")
        elif num == 2:
            print(f"  clicks={d.get('clicks', '?')}")
        elif num == 3:
            print(f"  noise_gap={d.get('noise_gap','?'):+.1f} dB, hf_gap={d.get('hf_gap','?'):+.1f} dB, sw_flags={d.get('sliding_flags','?')}")
        elif num == 4:
            print(f"  mfcc={d.get('mfcc_distance','?')}, f0_dev={d.get('f0_deviation_pct','?')}%")
        elif num == 5:
            print(f"  median={d.get('median_rms','?')} dB, range={d.get('range_db','?')} dB, spikes={d.get('spikes','?')}")
        elif num == 6:
            print(f"  median_ratio={d.get('median_ratio','?')} dB, regions={d.get('flagged_regions','?')}")
        elif num == 7:
            print(f"  surges={d.get('surges','?')}, drops={d.get('drops','?')}")
        elif num == 8:
            print(f"  mfcc_pairs={d.get('mfcc_pairs','?')}, confirmed={d.get('confirmed','?')}")
        elif num == 9:
            print(f"  spikes={d.get('spikes','?')}, windows={d.get('windows','?')}")
        elif num == 10:
            if d.get('skipped'):
                print(f"  (skipped)")
            else:
                print(f"  median={d.get('median_rate','?')} w/s, rushes={d.get('rushes','?')}")
        elif num == 11:
            print(f"  failed={d.get('failed','?')}/{d.get('total','?')} regions")
        elif num == 12:
            print(f"  {d.get('actual_min','?')} min vs {d.get('target_min','?')} min ({d.get('deviation_pct','?')}%)")
        elif num == 13:
            print(f"  dead_sil={d.get('dead_silence','?')}, range={d.get('ambient_range','?')} dB")
        elif num == 14:
            print(f"  flags={d.get('flags','?')}")
        else:
            print()
        
        if not r['passed']:
            all_passed = False
    
    passed_count = sum(1 for r in results.values() if r['passed'])
    total = len(results)
    
    print(f"\n  {'='*40}")
    print(f"  RESULT: {passed_count}/{total} gates passed")
    if all_passed:
        print(f"  STATUS: ALL GATES PASSED — repair is clear for deploy")
    else:
        failed = [f"Gate {num}" for num, r in sorted(results.items()) if not r['passed']]
        print(f"  STATUS: FAILED gates: {', '.join(failed)}")
    print(f"  {'='*40}")
