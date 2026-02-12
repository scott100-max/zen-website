#!/usr/bin/env python3
"""
Automated Candidate Picker v6 — Selects TTS candidates without human A/B tournament.

v6 changes (12 Feb 2026):
  - Tonal consistency ADDED to ranking: -tonal_distance * 250 (MFCC distance to prev chunk)
    Sweep across 80 combos found this is the strongest new signal: +7.8% top-3 vs v5 baseline
  - Quality weight increased 3.0→6.0 (sweep showed 5-7 optimal for top-3)
  - Echo weight reduced 300→200 (tonal provides complementary signal, echo can be lighter)
  - Hiss ranking DISABLED (sweep proved harmful at every weight)
  - Duration preference DISABLED (sweep proved harmful at every weight)
  - Validation function fixed to use actual ranking logs for top-3 measurement
  - Sweep validated: 245 chunks / 10 sessions → 22.9% exact, 61.2% top-3 (v5: 21.6%/51.4%)
  - TAIL CUTOFF detector: measures trailing silence in WAV, rejects if < 10ms
    (catches audio ending abruptly mid-syllable — zero tolerance defect)
    10ms calibrated: 3.3% of human picks at <5ms, 7% at <10ms.
    Net effect: exact +2.4%, top-3 -1.2%, eliminations +6.6% (25.3%/60.0%/13.9%)

v5 changes (12 Feb 2026):
  - Validated against 224 human-picked chunks across 9 sessions (v3 baseline: 17.4% match)
  - Cutoff threshold loosened: chars/14 → chars/22 (was eliminating 70 human picks)
  - Hiss ceiling loosened: -10.0 → -5.0 (was eliminating 16 human picks at borderline)
  - Duration outlier loosened: 20% → 40% (was eliminating 14 human picks)
  - Composite floor REMOVED (proven useless — complete overlap between pass and hard-fail ranges)
  - Echo ceiling loosened: 0.0016 → 0.003
  - Ranking rebalanced: echo weight 2000→300, quality weight 0.5→3.0 (quality-first ranking)

v3 changes (12 Feb 2026):
  - Severity-aware: loads prior verdicts, builds hard-fail/soft-fail audio profiles
  - Two-stage elimination: first reject hard-fail-like candidates, then penalise soft-fail-like
  - UNRESOLVABLE detection: refuses to pick when all candidates eliminated (no silent fallback)
  - Trained on 3 runs of session 01 (78 human-labeled verdicts with severity)

v2 changes (12 Feb 2026):
  - CUTOFF detection, echo-first ranking, tighter hiss ceiling

Usage:
    python3 auto-picker.py 01-morning-meditation
    python3 auto-picker.py 01-morning-meditation --validate
    python3 auto-picker.py --validate-all
"""

import argparse
import importlib.util
import json
import math
import os
import re
import struct
import subprocess
import sys
import wave
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Load build-session-v3.py for scoring functions
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
PICKS_API = "https://vault-picks.salus-mind.com"
AUTH_TOKEN = "salus-vault-2026"

# Selection thresholds — v5 calibrated from 224 human-picked chunks across 9 sessions
# COMPOSITE_FLOOR removed — proven useless (complete overlap pass vs hard-fail, killed EXCELLENT candidates)
DURATION_OUTLIER_PCT = 0.40     # Reject if duration >40% from chunk median (was 20%, eliminated 14 human picks)
ECHO_RISK_CEILING = 0.003      # Hard ceiling on echo_risk (was 0.0016, eliminated 2 human picks)
HISS_RISK_CEILING = -5.0       # Loosened from -10.0 (was eliminating 16 human picks at borderline -6.9 to -9.8)
CUT_SHORT_RATIO = 0.60         # Reject if duration < 60% of chunk median
CUTOFF_CHARS_PER_SEC = 22.0    # Loosened from 14.0 (was eliminating 70 human picks; chars/22 keeps 94%)
ECHO_RANK_WEIGHT = 200.0       # v6: Reduced from 300 (sweep: lower echo weight + tonal = better)
FLATNESS_PENALTY_WEIGHT = 20.0 # Flatness penalty (sweep confirmed 20 optimal)
QUALITY_RANK_WEIGHT = 6.0      # v6: Increased from 3.0 (sweep: 5-7 optimal for top-3)
DURATION_PREFER_WEIGHT = 0.0   # v6: Disabled (sweep proved harmful across all weights)
TONAL_RANK_WEIGHT = 250.0      # v6: NEW — tonal consistency (MFCC distance to prev chunk, sweep: huge signal)
HISS_RANK_WEIGHT = 0.0         # v6: Disabled (sweep proved harmful)
TAIL_SILENCE_MIN_MS = 10       # Reject if trailing silence < 10ms (tail cutoff — audio ends abruptly)
TAIL_SILENCE_DB = -40          # dBFS threshold for silence detection
CONFIDENCE_MARGIN = 0.05       # Score margin for high vs low confidence
HARD_FAIL_SIMILARITY = 0.15    # Reject if metrics within 15% of a known hard-fail
SOFT_FAIL_PENALTY = 500.0      # Ranking penalty for soft-fail-like candidates


def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def measure_tail_silence(wav_path, threshold_db=TAIL_SILENCE_DB):
    """Measure trailing silence duration in milliseconds.

    Reads last 500ms of WAV file, finds last sample above threshold.
    Returns trailing silence duration in ms, or None on error.
    """
    try:
        with wave.open(str(wav_path), 'rb') as wf:
            framerate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()

            # Only read last 500ms
            tail_frames = min(n_frames, int(framerate * 0.5))
            wf.setpos(n_frames - tail_frames)
            raw = wf.readframes(tail_frames)

        n_samples = tail_frames * n_channels
        if sampwidth == 2:
            samples = struct.unpack(f'<{n_samples}h', raw)
            max_val = 32768.0
        elif sampwidth == 4:
            samples = struct.unpack(f'<{n_samples}i', raw)
            max_val = 2147483648.0
        else:
            return None

        # Convert to mono absolute values
        if n_channels > 1:
            mono = [abs(samples[i]) for i in range(0, len(samples), n_channels)]
        else:
            mono = [abs(s) for s in samples]

        threshold_linear = max_val * (10 ** (threshold_db / 20))

        # Search backwards for last sample above threshold
        for i in range(len(mono) - 1, -1, -1):
            if mono[i] > threshold_linear:
                trailing = len(mono) - 1 - i
                return (trailing / framerate) * 1000

        # Entire tail is silence
        return (tail_frames / framerate) * 1000
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_vault_candidates(session_id):
    """Load all candidate scores and metadata from a vault session directory.

    Returns dict: {chunk_idx: [candidate_dicts]}
    """
    session_dir = VAULT_DIR / session_id
    if not session_dir.exists():
        raise FileNotFoundError(f"Vault directory not found: {session_dir}")

    chunks = {}
    for chunk_dir in sorted(session_dir.iterdir()):
        if not chunk_dir.is_dir() or not re.match(r'^c\d+$', chunk_dir.name):
            continue

        ci = int(chunk_dir.name[1:])
        meta_file = chunk_dir / f"{chunk_dir.name}_meta.json"
        if not meta_file.exists():
            continue

        meta = json.loads(meta_file.read_text())
        candidates = []
        for c in meta.get('candidates', []):
            if c.get('error'):
                continue
            candidates.append({
                'version': c['version'],
                'filename': c.get('filename', ''),
                'wav_path': str(chunk_dir / c.get('filename', '')),
                'composite_score': c.get('composite_score'),
                'quality_score': c.get('quality_score'),
                'echo_risk': c.get('echo_risk'),
                'hiss_risk': c.get('hiss_risk'),
                'sp_contrast': c.get('sp_contrast'),
                'sp_flatness': c.get('sp_flatness'),
                'tonal_distance': c.get('tonal_distance_to_prev'),
                'duration': c.get('duration_seconds'),
                'tail_silence_ms': c.get('tail_silence_ms'),  # from metadata if available
                'filtered': c.get('filtered', False),
                'filter_reason': c.get('filter_reason', ''),
            })

        chunks[ci] = {
            'text': meta.get('text', ''),
            'char_count': meta.get('char_count', 0),
            'is_opening': meta.get('is_opening', ci == 0),
            'is_closing': meta.get('is_closing', False),
            'candidates': candidates,
        }

    return chunks


def load_verdict_history(session_id):
    """Load all prior verdict files to build hard-fail/soft-fail audio profiles.

    Returns dict: {chunk_idx: {'hard_versions': set, 'soft_versions': set, 'pass_versions': set,
                                'hard_profiles': [metric_dicts], 'soft_profiles': [metric_dicts]}}
    """
    session_dir = VAULT_DIR / session_id
    history = defaultdict(lambda: {
        'hard_versions': set(), 'soft_versions': set(), 'pass_versions': set(),
        'hard_profiles': [], 'soft_profiles': [],
    })

    # Load all verdict files
    for vf in sorted(session_dir.glob('auto-trial-verdicts*.json')):
        try:
            data = json.loads(vf.read_text())
            chunks = data.get('chunks', {})
            for cstr, ch in chunks.items():
                ci = int(cstr)
                ver = ch.get('version')
                sev = ch.get('severity', 'pass')
                if ch.get('passed'):
                    history[ci]['pass_versions'].add(ver)
                elif sev == 'hard':
                    history[ci]['hard_versions'].add(ver)
                elif sev == 'soft':
                    history[ci]['soft_versions'].add(ver)
                else:
                    history[ci]['hard_versions'].add(ver)
        except Exception:
            continue

    # Also check API for latest verdicts
    try:
        result = subprocess.run([
            'curl', '-s', '-H', f'Authorization: Bearer {AUTH_TOKEN}',
            f'{PICKS_API}/verdicts/{session_id}'
        ], capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        for cstr, ch in data.get('chunks', {}).items():
            ci = int(cstr)
            ver = ch.get('version')
            sev = ch.get('severity', 'pass')
            if ch.get('passed'):
                history[ci]['pass_versions'].add(ver)
            elif sev == 'hard':
                history[ci]['hard_versions'].add(ver)
            elif sev == 'soft':
                history[ci]['soft_versions'].add(ver)
            else:
                history[ci]['hard_versions'].add(ver)
    except Exception:
        pass

    return dict(history)


def build_fail_profiles(chunk_idx, history, candidates):
    """Build metric profiles from known hard-fail and soft-fail versions.

    Returns (hard_profiles, soft_profiles) — lists of metric dicts.
    """
    ch_hist = history.get(chunk_idx, {})
    hard_versions = ch_hist.get('hard_versions', set())
    soft_versions = ch_hist.get('soft_versions', set())

    hard_profiles = []
    soft_profiles = []

    for c in candidates:
        ver = c['version']
        profile = {
            'echo_risk': c.get('echo_risk'),
            'hiss_risk': c.get('hiss_risk'),
            'sp_flatness': c.get('sp_flatness'),
            'quality_score': c.get('quality_score'),
            'duration': c.get('duration'),
        }
        if ver in hard_versions:
            hard_profiles.append(profile)
        elif ver in soft_versions:
            soft_profiles.append(profile)

    return hard_profiles, soft_profiles


def is_similar_to_profile(candidate, profiles, threshold=HARD_FAIL_SIMILARITY):
    """Check if a candidate's metrics are within threshold of any fail profile."""
    if not profiles:
        return False

    for prof in profiles:
        matches = 0
        comparisons = 0
        for key in ['echo_risk', 'hiss_risk', 'sp_flatness', 'quality_score']:
            cv = candidate.get(key)
            pv = prof.get(key)
            if cv is not None and pv is not None and pv != 0:
                comparisons += 1
                if abs(cv - pv) / abs(pv) <= threshold:
                    matches += 1
        # Similar if >50% of comparable metrics are within threshold
        if comparisons > 0 and matches / comparisons > 0.5:
            return True
    return False


def soft_fail_penalty(candidate, soft_profiles):
    """Calculate ranking penalty based on similarity to soft-fail profiles."""
    if not soft_profiles:
        return 0.0

    max_similarity = 0.0
    for prof in soft_profiles:
        sim = 0.0
        count = 0
        for key in ['echo_risk', 'hiss_risk', 'sp_flatness']:
            cv = candidate.get(key)
            pv = prof.get(key)
            if cv is not None and pv is not None and pv != 0:
                count += 1
                rel_diff = abs(cv - pv) / abs(pv)
                sim += max(0, 1.0 - rel_diff)  # 1.0 = identical, 0 = very different
        if count > 0:
            max_similarity = max(max_similarity, sim / count)

    return max_similarity * SOFT_FAIL_PENALTY


def fetch_human_picks(session_id):
    """Fetch human picks from the API for validation."""
    try:
        result = subprocess.run([
            'curl', '-s', '-H', f'Authorization: Bearer {AUTH_TOKEN}',
            f'{PICKS_API}/picks/{session_id}'
        ], capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        picks = {}
        for p in data.get('picks', []):
            picks[p['chunk']] = {
                'picked': p.get('picked'),
                'rejected': p.get('rejected', []),
            }
        return picks
    except Exception as e:
        print(f"  WARNING: Could not fetch picks for {session_id}: {e}")
        return {}


# ---------------------------------------------------------------------------
# Automated Selection Algorithm
# ---------------------------------------------------------------------------

def select_candidate(chunk_idx, chunk_data, prev_best_mfcc=None, session_log=None,
                     verdict_history=None):
    """Select the best candidate for a chunk using multi-signal analysis.

    Strategy v3 (severity-aware):
    1. Eliminate definite failures (pre-filter, duration, hiss, cutoff, echo ceiling)
    2. Eliminate candidates similar to known hard-fail audio profiles
    3. Rank remaining with penalty for soft-fail similarity
    4. Report confidence + unresolvable status

    Returns (picked_version, selection_log_dict)
    """
    candidates = chunk_data['candidates']
    text = chunk_data['text']
    is_opening = chunk_data.get('is_opening', False)

    if not candidates:
        return None, {'reason': 'no candidates', 'confidence': 'none'}

    log = {
        'chunk': chunk_idx,
        'text': text[:80],
        'char_count': chunk_data['char_count'],
        'total_candidates': len(candidates),
        'eliminated': [],
        'remaining': [],
        'selected': None,
        'confidence': None,
    }

    # --- Stage 1: Elimination filters ---
    # Exempt known-pass versions from all filters (human confirmed clean)
    pass_versions = set()
    if verdict_history:
        pass_versions = verdict_history.get(chunk_idx, {}).get('pass_versions', set())

    remaining = []
    for c in candidates:
        version = c['version']

        # Known-pass bypass — never eliminate human-confirmed clean audio
        if version in pass_versions:
            remaining.append(c)
            continue

        reasons = []

        # 1a: Composite score floor — REMOVED in v5 (proven useless: complete overlap pass vs hard-fail)

        # 1b: Duration outlier detection
        # Compute duration stats for this chunk
        durations = [x['duration'] for x in candidates
                     if x.get('duration') is not None and x['duration'] > 0]
        if durations and c.get('duration') is not None and c['duration'] > 0:
            durations.sort()
            median_dur = durations[len(durations) // 2]

            # Cut Short detection
            if c['duration'] < median_dur * CUT_SHORT_RATIO:
                reasons.append(f"cut short: {c['duration']:.1f}s vs median {median_dur:.1f}s")

            # Duration outlier (too long or too short)
            if abs(c['duration'] - median_dur) / median_dur > DURATION_OUTLIER_PCT:
                reasons.append(f"duration outlier: {c['duration']:.1f}s ({100*abs(c['duration']-median_dur)/median_dur:.0f}% from median)")

        # 1c: Extreme hiss
        if c.get('hiss_risk') is not None and c['hiss_risk'] > HISS_RISK_CEILING:
            reasons.append(f"hiss_risk {c['hiss_risk']:.1f} > {HISS_RISK_CEILING}")

        # 1d: CUTOFF detection — duration too short for text length
        if c.get('duration') is not None and chunk_data.get('char_count', 0) > 0:
            min_dur = chunk_data['char_count'] / CUTOFF_CHARS_PER_SEC
            if c['duration'] < min_dur:
                reasons.append(f"cutoff: {c['duration']:.1f}s < {min_dur:.1f}s expected for {chunk_data['char_count']} chars")

        # 1e: Tail cutoff — audio ends abruptly without trailing silence
        tail_ms = c.get('tail_silence_ms')
        if tail_ms is None and c.get('wav_path') and os.path.exists(c['wav_path']):
            tail_ms = measure_tail_silence(c['wav_path'])
            c['tail_silence_ms'] = tail_ms
        if tail_ms is not None and tail_ms < TAIL_SILENCE_MIN_MS:
            reasons.append(f"tail_cutoff: {tail_ms:.0f}ms trailing silence (min {TAIL_SILENCE_MIN_MS}ms)")

        # 1f: Echo risk hard ceiling
        if c.get('echo_risk') is not None and c['echo_risk'] > ECHO_RISK_CEILING:
            reasons.append(f"echo_risk {c['echo_risk']:.6f} > {ECHO_RISK_CEILING}")

        # 1g: Over-generation (already flagged by vault-builder)
        if c.get('filtered') and c.get('filter_reason') == 'overgenerated':
            reasons.append("overgenerated")

        if reasons:
            log['eliminated'].append({
                'version': version,
                'reasons': reasons,
                'composite': c.get('composite_score'),
                'quality': c.get('quality_score'),
                'duration': c.get('duration'),
            })
        else:
            remaining.append(c)

    # --- Stage 1h: Eliminate candidates similar to known hard-fail profiles ---
    if verdict_history:
        hard_profiles, soft_profiles = build_fail_profiles(
            chunk_idx, verdict_history, candidates)

        if hard_profiles:
            pre_count = len(remaining)
            hard_eliminated = []
            kept = []
            for c in remaining:
                # Never eliminate known-pass versions
                pass_versions = verdict_history.get(chunk_idx, {}).get('pass_versions', set())
                if c['version'] in pass_versions:
                    kept.append(c)
                    continue
                if is_similar_to_profile(c, hard_profiles):
                    hard_eliminated.append(c)
                    log['eliminated'].append({
                        'version': c['version'],
                        'reasons': ['similar_to_hard_fail_profile'],
                        'composite': c.get('composite_score'),
                        'quality': c.get('quality_score'),
                        'duration': c.get('duration'),
                    })
                else:
                    kept.append(c)
            remaining = kept
            if hard_eliminated:
                log['hard_fail_eliminated'] = len(hard_eliminated)
    else:
        soft_profiles = []

    # If all eliminated, mark as UNRESOLVABLE but still pick least-bad for review
    if not remaining:
        log['unresolvable'] = True
        log['confidence'] = 'none'
        log['needs_human_review'] = True

        # Least-bad fallback: sort by fewest elimination reasons, then longest duration
        fallback = sorted(candidates,
                         key=lambda x: (len([r for e in log['eliminated']
                                            if e['version'] == x['version']
                                            for r in e.get('reasons', [])]),
                                       -(x.get('duration') or 0)))
        selected = fallback[0] if fallback else None
        cutoff_count = sum(1 for e in log['eliminated'] if any('cutoff' in r for r in e.get('reasons', [])))
        dur_count = sum(1 for e in log['eliminated'] if any('duration' in r for r in e.get('reasons', [])))
        hiss_count = sum(1 for e in log['eliminated'] if any('hiss' in r for r in e.get('reasons', [])))

        log['selected'] = {
            'version': selected['version'] if selected else None,
            'reason': 'unresolvable_least_bad',
            'action': 'split_chunk_and_regen',
            'note': f'All {len(candidates)} candidates eliminated. '
                    f'Top reasons: cutoff={cutoff_count}, duration={dur_count}, hiss={hiss_count}. '
                    f'Picked least-bad for review.',
            'quality_score': selected.get('quality_score') if selected else None,
            'duration': selected.get('duration') if selected else None,
        }
        return selected['version'] if selected else None, log

    # --- Stage 2: Ranking ---
    # Use quality score as primary signal (23.4% #1 match — best single predictor)
    # with weak secondary tiebreakers

    # Compute chunk duration median for penalty
    all_durations = [c['duration'] for c in remaining
                     if c.get('duration') is not None and c['duration'] > 0]
    dur_median = sorted(all_durations)[len(all_durations) // 2] if all_durations else None

    def rank_score(c):
        """Combined ranking score. Higher = better.

        v6: echo + quality + tonal + flatness. Tonal consistency is the strongest signal.
        Known-pass versions get a bonus. Known-soft-fail-like get penalised.
        """
        echo = c.get('echo_risk') or 0
        flatness = c.get('sp_flatness') or 0
        quality = c.get('quality_score') or 0
        tonal = c.get('tonal_distance') or 0
        hiss = c.get('hiss_risk') or -20  # More negative = better

        base = (
            -echo * ECHO_RANK_WEIGHT
            - flatness * FLATNESS_PENALTY_WEIGHT
            + quality * QUALITY_RANK_WEIGHT
            - tonal * TONAL_RANK_WEIGHT       # Lower tonal distance = more consistent = better
            + hiss * HISS_RANK_WEIGHT          # hiss is negative; more negative = better, so + weight rewards lower hiss
        )

        # Duration preference: reward above-median, penalise below-median
        if dur_median and c.get('duration') and c['duration'] > 0:
            dur_ratio = (c['duration'] - dur_median) / dur_median  # positive = longer than median
            base += dur_ratio * DURATION_PREFER_WEIGHT

        # Soft-fail penalty from verdict history
        if soft_profiles:
            base -= soft_fail_penalty(c, soft_profiles)

        # Bonus for known-pass versions
        if verdict_history:
            pass_versions = verdict_history.get(chunk_idx, {}).get('pass_versions', set())
            if c['version'] in pass_versions:
                base += 1000.0  # Strong bonus — human confirmed clean

        return base

    scored = [(c, rank_score(c)) for c in remaining]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Record remaining candidates
    for c, score in scored:
        log['remaining'].append({
            'version': c['version'],
            'rank_score': round(score, 4),
            'quality_score': c.get('quality_score'),
            'composite_score': c.get('composite_score'),
            'duration': c.get('duration'),
            'echo_risk': c.get('echo_risk'),
            'hiss_risk': c.get('hiss_risk'),
            'sp_flatness': c.get('sp_flatness'),
        })

    # --- Stage 3: Selection + confidence ---
    selected_c, selected_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0
    margin = selected_score - second_score

    if margin > CONFIDENCE_MARGIN:
        confidence = 'high'
    elif margin > CONFIDENCE_MARGIN / 2:
        confidence = 'medium'
    else:
        confidence = 'low'

    log['selected'] = {
        'version': selected_c['version'],
        'rank_score': round(selected_score, 4),
        'quality_score': selected_c.get('quality_score'),
        'composite_score': selected_c.get('composite_score'),
        'duration': selected_c.get('duration'),
        'margin_over_second': round(margin, 4),
        'reason': 'ranked_selection',
    }
    log['confidence'] = confidence
    log['needs_human_review'] = confidence == 'low'

    return selected_c['version'], log


def auto_pick_session(session_id, chunks_data=None):
    """Run the automated picker on a session.

    Returns (picks_dict, selection_logs).
    """
    if chunks_data is None:
        chunks_data = load_vault_candidates(session_id)

    # Load verdict history for severity-aware picking
    verdict_history = load_verdict_history(session_id)
    if verdict_history:
        total_hard = sum(len(h.get('hard_versions', set())) for h in verdict_history.values())
        total_soft = sum(len(h.get('soft_versions', set())) for h in verdict_history.values())
        total_pass = sum(len(h.get('pass_versions', set())) for h in verdict_history.values())
        print(f"  Loaded verdict history: {total_hard} hard, {total_soft} soft, {total_pass} pass")

    picks = {
        'session': session_id,
        'reviewed': _now_iso(),
        'method': 'auto-picker v6',
        'picks': [],
    }
    selection_logs = []

    chunk_indices = sorted(chunks_data.keys())
    for ci in chunk_indices:
        chunk = chunks_data[ci]
        version, log = select_candidate(ci, chunk, verdict_history=verdict_history)

        is_unresolvable = log.get('unresolvable', False)
        pick_entry = {
            'chunk': ci,
            'text': chunk['text'],
            'picked': version,
            'picked_file': f"c{ci:02d}/c{ci:02d}_v{version:02d}.wav" if version is not None else None,
            'rejected': [],
            'side': None,
        }
        if is_unresolvable:
            pick_entry['notes'] = 'UNRESOLVABLE — all candidates eliminated, needs script split + regen'
            pick_entry['unresolvable'] = True
        else:
            pick_entry['notes'] = f"auto-picked (confidence: {log.get('confidence', 'unknown')})"
        picks['picks'].append(pick_entry)
        selection_logs.append(log)

    return picks, selection_logs


# ---------------------------------------------------------------------------
# Validation — Compare auto-picks against human picks
# ---------------------------------------------------------------------------

def validate_against_human(session_id, auto_picks=None, human_picks=None, chunks_data=None,
                           selection_logs=None):
    """Compare automated picks against human A/B picks.

    Returns validation report dict.
    """
    if chunks_data is None:
        chunks_data = load_vault_candidates(session_id)
    if auto_picks is None:
        auto_picks, selection_logs = auto_pick_session(session_id, chunks_data)
    if human_picks is None:
        human_picks = fetch_human_picks(session_id)

    if not human_picks:
        return {'session': session_id, 'error': 'no human picks available'}

    # Build lookup: chunk_idx → ranked version list from selection logs
    log_ranking = {}
    if selection_logs:
        for sl in selection_logs:
            ci = sl.get('chunk')
            ranked = [r['version'] for r in sl.get('remaining', [])]
            if ranked:
                log_ranking[ci] = ranked

    matches = 0
    top3_matches = 0
    eliminated = 0
    total = 0
    mismatches = []

    for pick in auto_picks.get('picks', []):
        ci = pick['chunk']
        auto_v = pick.get('picked')
        human_v = human_picks.get(ci, {}).get('picked')

        if human_v is None or auto_v is None:
            continue

        total += 1
        if auto_v == human_v:
            matches += 1
            top3_matches += 1
        else:
            # Use actual ranking from selection logs (not quality_score sort)
            ranked_versions = log_ranking.get(ci, [])
            if ranked_versions:
                top3_versions = ranked_versions[:3]
                if human_v in top3_versions:
                    top3_matches += 1
                elif human_v not in ranked_versions:
                    eliminated += 1

            # Record mismatch details
            chunk = chunks_data.get(ci, {})
            candidates = chunk.get('candidates', [])
            auto_score = next((c.get('quality_score') for c in candidates
                              if c['version'] == auto_v), None)
            human_score = next((c.get('quality_score') for c in candidates
                               if c['version'] == human_v), None)
            human_rank = None
            if ranked_versions and human_v in ranked_versions:
                human_rank = ranked_versions.index(human_v) + 1
            mismatches.append({
                'chunk': ci,
                'auto_picked': auto_v,
                'human_picked': human_v,
                'auto_quality': auto_score,
                'human_quality': human_score,
                'auto_rank_of_human': human_rank,
                'human_eliminated': human_v not in ranked_versions if ranked_versions else None,
            })

    return {
        'session': session_id,
        'total_chunks': total,
        'exact_match': matches,
        'exact_match_pct': round(100 * matches / max(total, 1), 1),
        'human_in_auto_top3': top3_matches,
        'human_in_auto_top3_pct': round(100 * top3_matches / max(total, 1), 1),
        'human_eliminated': eliminated,
        'human_eliminated_pct': round(100 * eliminated / max(total, 1), 1),
        'mismatches': mismatches,
    }


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Automated Candidate Picker — select TTS candidates without human A/B')
    parser.add_argument('session_id', nargs='?',
                        help='Session ID to pick (e.g., 01-morning-meditation)')
    parser.add_argument('--validate', action='store_true',
                        help='Validate auto-picks against human picks for this session')
    parser.add_argument('--validate-all', action='store_true',
                        help='Validate auto-picks against human picks for ALL sessions')
    parser.add_argument('--output', metavar='PATH',
                        help='Output path for picks JSON (default: vault dir)')
    parser.add_argument('--log', metavar='PATH',
                        help='Output path for selection log (default: vault dir)')
    args = parser.parse_args()

    if args.validate_all:
        # Retroactive validation across all human-picked sessions
        sessions = [
            '01-morning-meditation', '03-breathing-for-anxiety',
            '18-calm-in-three-minutes', '23-the-calm-reset',
            '32-observing-emotions', '42-seven-day-mindfulness-day5',
            '52-the-court-of-your-mind', '61-21day-mindfulness-day05',
            '76-21day-mindfulness-day20', 'narrator-welcome',
        ]

        print(f"\n{'='*70}")
        print(f"  AUTO-PICKER RETROACTIVE VALIDATION — {len(sessions)} sessions")
        print(f"{'='*70}")

        all_results = []
        total_match = 0
        total_chunks = 0
        total_top3 = 0
        total_elim = 0

        for sid in sessions:
            try:
                # Use pre-fix vault dir for session 01
                vault_id = sid
                pre_fix_dir = VAULT_DIR / f"{sid}-pre-fix"
                if pre_fix_dir.exists():
                    vault_id = f"{sid}-pre-fix"

                chunks = load_vault_candidates(vault_id)
                picks, logs = auto_pick_session(sid, chunks)
                result = validate_against_human(sid, picks, chunks_data=chunks,
                                                selection_logs=logs)
                all_results.append(result)

                m = result['exact_match']
                t = result['total_chunks']
                t3 = result.get('human_in_auto_top3', 0)
                el = result.get('human_eliminated', 0)
                total_match += m
                total_chunks += t
                total_top3 += t3
                total_elim += el

                print(f"  {sid:40s}: {m:2d}/{t:2d} ({result['exact_match_pct']:5.1f}%) exact, "
                      f"{t3:2d}/{t:2d} ({result['human_in_auto_top3_pct']:5.1f}%) top3, "
                      f"{el:2d} elim")

            except Exception as e:
                print(f"  {sid:40s}: ERROR — {e}")
                all_results.append({'session': sid, 'error': str(e)})

        print(f"\n{'='*70}")
        print(f"  OVERALL: {total_match}/{total_chunks} "
              f"({100*total_match/max(total_chunks,1):.1f}%) exact match")
        print(f"  TOP 3:   {total_top3}/{total_chunks} "
              f"({100*total_top3/max(total_chunks,1):.1f}%)")
        print(f"  ELIM:    {total_elim}/{total_chunks} "
              f"({100*total_elim/max(total_chunks,1):.1f}%) human picks eliminated")
        print(f"{'='*70}")

        # Save results
        results_path = Path("docs/auto-picker-validation.json")
        results_path.write_text(json.dumps({
            'validated_at': _now_iso(),
            'total_sessions': len(sessions),
            'total_chunks': total_chunks,
            'exact_match': total_match,
            'exact_match_pct': round(100 * total_match / max(total_chunks, 1), 1),
            'top3_match': total_top3,
            'top3_match_pct': round(100 * total_top3 / max(total_chunks, 1), 1),
            'human_eliminated': total_elim,
            'human_eliminated_pct': round(100 * total_elim / max(total_chunks, 1), 1),
            'sessions': all_results,
        }, indent=2))
        print(f"\n  Results saved: {results_path}")
        return

    if not args.session_id:
        parser.print_help()
        return

    session_id = args.session_id

    # Load candidates
    print(f"\n  Loading vault candidates for {session_id}...")
    chunks = load_vault_candidates(session_id)
    print(f"  Found {len(chunks)} chunks, "
          f"{sum(len(c['candidates']) for c in chunks.values())} candidates")

    # Run auto-picker
    print(f"\n  Running automated picker...")
    picks, logs = auto_pick_session(session_id, chunks)

    # Summary
    picked = sum(1 for p in picks['picks'] if p['picked'] is not None)
    unresolvable = [l for l in logs if l.get('unresolvable')]
    flagged = sum(1 for l in logs if l.get('needs_human_review'))
    confidences = defaultdict(int)
    for l in logs:
        confidences[l.get('confidence', 'unknown')] += 1

    print(f"\n  Results:")
    print(f"    Picked: {picked}/{len(picks['picks'])}")
    print(f"    Confidence: high={confidences['high']}, "
          f"medium={confidences['medium']}, low={confidences['low']}")
    print(f"    Flagged for human review: {flagged}")

    if unresolvable:
        print(f"\n  *** UNRESOLVABLE CHUNKS ({len(unresolvable)}) ***")
        print(f"  These chunks had ALL candidates eliminated — need script split + regen:")
        for u in unresolvable:
            ci = u['chunk']
            sel = u.get('selected', {})
            note = sel.get('note', '')
            print(f"    c{ci:02d}: {note}")
        print()

    # Save picks
    output_dir = VAULT_DIR / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    picks_path = Path(args.output) if args.output else output_dir / "picks-auto.json"
    picks_path.write_text(json.dumps(picks, indent=2))
    print(f"\n  Picks saved: {picks_path}")

    # Save selection log
    log_path = Path(args.log) if args.log else output_dir / "auto-pick-log.json"
    log_path.write_text(json.dumps(logs, indent=2))
    print(f"  Log saved: {log_path}")

    # Validation against human picks if requested
    if args.validate:
        print(f"\n  Validating against human picks...")
        result = validate_against_human(session_id, picks, chunks_data=chunks)
        print(f"  Exact match: {result['exact_match']}/{result['total_chunks']} "
              f"({result['exact_match_pct']}%)")
        print(f"  Human in auto top-3: {result['human_in_auto_top3']}/{result['total_chunks']} "
              f"({result['human_in_auto_top3_pct']}%)")
        if result.get('mismatches'):
            print(f"\n  Mismatches:")
            for mm in result['mismatches'][:10]:
                print(f"    c{mm['chunk']:02d}: auto=v{mm['auto_picked']} "
                      f"(q={mm['auto_quality']:.3f}) vs "
                      f"human=v{mm['human_picked']} "
                      f"(q={mm['human_quality']:.3f}, "
                      f"rank={mm['auto_rank_of_human']})")


if __name__ == '__main__':
    main()
