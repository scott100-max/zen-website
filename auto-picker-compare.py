#!/usr/bin/env python3
"""
Auto-Picker Comparison Tool — Compares runs against human picks and previous runs.

Outputs accuracy metrics and trend data for tracking improvement over time.

Usage:
    python3 auto-picker-compare.py 01-morning-meditation
    python3 auto-picker-compare.py 01-morning-meditation --previous-run docs/prev-validation.json
"""

import argparse
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

VAULT_DIR = Path("content/audio-free/vault")
PICKS_API = "https://vault-picks.salus-mind.com"
AUTH_TOKEN = "salus-vault-2026"


def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load_auto_picks(session_id):
    """Load auto-picks."""
    picks_path = VAULT_DIR / session_id / "picks-auto.json"
    if picks_path.exists():
        return json.loads(picks_path.read_text())
    return {}


def fetch_human_picks(session_id):
    """Fetch human picks from API."""
    try:
        result = subprocess.run([
            'curl', '-s', '-H', f'Authorization: Bearer {AUTH_TOKEN}',
            f'{PICKS_API}/picks/{session_id}'
        ], capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        picks = {}
        for p in data.get('picks', []):
            picks[p['chunk']] = p.get('picked')
        return picks
    except Exception:
        return {}


def compare(session_id, previous_run_path=None):
    """Compare auto-picks against human picks and optionally a previous run."""
    auto_picks = load_auto_picks(session_id)
    human_picks = fetch_human_picks(session_id)

    if not auto_picks.get('picks'):
        print(f"  No auto-picks found for {session_id}")
        return

    # Compare auto vs human
    results = {
        'session': session_id,
        'compared_at': _now_iso(),
        'auto_method': auto_picks.get('method', 'unknown'),
        'chunks': [],
    }

    match = 0
    total = 0
    for p in auto_picks.get('picks', []):
        ci = p['chunk']
        auto_v = p.get('picked')
        human_v = human_picks.get(ci)
        is_match = auto_v == human_v if (auto_v is not None and human_v is not None) else None

        if auto_v is not None and human_v is not None:
            total += 1
            if is_match:
                match += 1

        results['chunks'].append({
            'chunk': ci,
            'auto': auto_v,
            'human': human_v,
            'match': is_match,
        })

    results['exact_match'] = match
    results['total'] = total
    results['pct'] = round(100 * match / max(total, 1), 1)

    print(f"\n  {session_id}: {match}/{total} ({results['pct']}%) exact match")

    # Compare against previous run if provided
    if previous_run_path:
        prev = json.loads(Path(previous_run_path).read_text())
        prev_session = None
        for s in prev.get('sessions', []):
            if s.get('session') == session_id:
                prev_session = s
                break

        if prev_session:
            prev_pct = prev_session.get('exact_match_pct', 0)
            delta = results['pct'] - prev_pct
            direction = "improved" if delta > 0 else "regressed" if delta < 0 else "unchanged"
            print(f"  vs previous: {prev_pct}% → {results['pct']}% ({'+' if delta >= 0 else ''}{delta:.1f}%, {direction})")
            results['previous_pct'] = prev_pct
            results['delta'] = delta
            results['direction'] = direction

    # Per-chunk detail
    mismatches = [c for c in results['chunks'] if c.get('match') is False]
    if mismatches:
        print(f"\n  Mismatches ({len(mismatches)}):")
        for c in mismatches[:15]:
            print(f"    c{c['chunk']:02d}: auto=v{c['auto']}, human=v{c['human']}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Auto-Picker Comparison Tool')
    parser.add_argument('session_id',
                        help='Session ID to compare')
    parser.add_argument('--previous-run', metavar='PATH',
                        help='Path to previous validation JSON for trend comparison')
    args = parser.parse_args()
    compare(args.session_id, args.previous_run)


if __name__ == '__main__':
    main()
