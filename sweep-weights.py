#!/usr/bin/env python3
"""Sweep ranking weight combinations to find optimal v6 settings.
Phase 4: Test tonal_distance + hiss_risk as new ranking signals."""
import json
import sys
from pathlib import Path

import importlib.util
spec = importlib.util.spec_from_file_location("auto_picker", Path(__file__).parent / "auto-picker.py")
ap = importlib.util.module_from_spec(spec)

import io
old_stdout = sys.stdout
sys.stdout = io.StringIO()
spec.loader.exec_module(ap)
sys.stdout = old_stdout

SESSIONS = [
    '01-morning-meditation', '03-breathing-for-anxiety',
    '18-calm-in-three-minutes', '23-the-calm-reset',
    '32-observing-emotions', '42-seven-day-mindfulness-day5',
    '52-the-court-of-your-mind', '61-21day-mindfulness-day05',
    '76-21day-mindfulness-day20', 'narrator-welcome',
]

print("Loading all vault data...")
all_data = {}
all_human = {}
for sid in SESSIONS:
    vault_id = sid
    pre_fix_dir = ap.VAULT_DIR / f"{sid}-pre-fix"
    if pre_fix_dir.exists():
        vault_id = f"{sid}-pre-fix"
    try:
        all_data[sid] = ap.load_vault_candidates(vault_id)
        all_human[sid] = ap.fetch_human_picks(sid)
    except Exception as e:
        print(f"  Skip {sid}: {e}")
print(f"Loaded {len(all_data)} sessions\n")

# Phase 5: Full final sweep with tonal locked in
echo_weights = [200.0, 300.0, 400.0, 500.0]
quality_weights = [4.0, 5.0, 6.0, 7.0, 8.0]
tonal_weights = [250.0, 300.0, 350.0, 400.0]
flatness_w_fixed = 20.0

results = []
total_combos = len(echo_weights) * len(quality_weights) * len(tonal_weights)
combo = 0

for ew in echo_weights:
    for qw in quality_weights:
        for tw in tonal_weights:
            combo += 1
            ap.ECHO_RANK_WEIGHT = ew
            ap.QUALITY_RANK_WEIGHT = qw
            ap.FLATNESS_PENALTY_WEIGHT = flatness_w_fixed
            ap.TONAL_RANK_WEIGHT = tw
            ap.HISS_RANK_WEIGHT = 0.0
            ap.DURATION_PREFER_WEIGHT = 0.0

            total_match = 0
            total_chunks = 0
            total_top3 = 0
            total_elim = 0

            for sid in SESSIONS:
                if sid not in all_data:
                    continue
                chunks = all_data[sid]
                try:
                    old_out = sys.stdout
                    sys.stdout = io.StringIO()
                    picks, logs = ap.auto_pick_session(sid, chunks)
                    sys.stdout = old_out

                    result = ap.validate_against_human(sid, picks, human_picks=all_human.get(sid),
                                                       chunks_data=chunks, selection_logs=logs)
                    total_match += result.get('exact_match', 0)
                    total_chunks += result.get('total_chunks', 0)
                    total_top3 += result.get('human_in_auto_top3', 0)
                    total_elim += result.get('human_eliminated', 0)
                except Exception:
                    sys.stdout = old_out

            exact_pct = 100 * total_match / max(total_chunks, 1)
            top3_pct = 100 * total_top3 / max(total_chunks, 1)
            elim_pct = 100 * total_elim / max(total_chunks, 1)

            results.append({
                'echo_w': ew, 'quality_w': qw, 'tonal_w': tw,
                'exact': total_match, 'exact_pct': round(exact_pct, 1),
                'top3': total_top3, 'top3_pct': round(top3_pct, 1),
                'elim': total_elim, 'elim_pct': round(elim_pct, 1),
                'chunks': total_chunks,
            })

            marker = ""
            if exact_pct > 24.5 or top3_pct > 59.6:
                marker = " ***"
            print(f"  [{combo:3d}/{total_combos}] e={ew:.0f} q={qw:.1f} t={tw:.0f} → "
                  f"exact={exact_pct:5.1f}% top3={top3_pct:5.1f}%{marker}")

# Baseline reference
print(f"\n  BASELINE (tonal=0, hiss=0): echo=400 quality=6.0 flatness=20 → exact=22.0% top3=53.5%")

results.sort(key=lambda r: (r['top3_pct'], r['exact_pct']), reverse=True)
print(f"\n{'='*70}")
print("TOP 10 (by top-3 rate):")
print(f"{'='*70}")
for i, r in enumerate(results[:10]):
    print(f"  #{i+1}: e={r.get('echo_w',400):.0f} q={r.get('quality_w',6):.1f} t={r['tonal_w']:.0f} → "
          f"exact={r['exact_pct']:5.1f}% top3={r['top3_pct']:5.1f}%")

results.sort(key=lambda r: (r['exact_pct'], r['top3_pct']), reverse=True)
print(f"\nTOP 10 (by exact match):")
print(f"{'='*70}")
for i, r in enumerate(results[:10]):
    print(f"  #{i+1}: e={r.get('echo_w',400):.0f} q={r.get('quality_w',6):.1f} t={r['tonal_w']:.0f} → "
          f"exact={r['exact_pct']:5.1f}% top3={r['top3_pct']:5.1f}%")

Path("docs/weight-sweep-phase4.json").write_text(json.dumps(results, indent=2))
print(f"\nResults saved: docs/weight-sweep-phase4.json")
