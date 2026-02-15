#!/usr/bin/env python3
"""
Vault Top-Up — Bring all vaults to a minimum pool size per chunk.

Scans all vault directories, identifies chunks below the target pool size,
and uses vault-builder's regen_chunks to add candidates.

Usage:
    python3 tools/vault-topup.py              # Default target: 35/chunk
    python3 tools/vault-topup.py --target 50  # Custom target
    python3 tools/vault-topup.py --dry-run    # Show plan without generating
    python3 tools/vault-topup.py --session 09-rainfall-sleep-journey  # Single session
"""

import asyncio
import argparse
import json
import importlib.util
import sys
from pathlib import Path

VAULT_DIR = Path(__file__).parent.parent / "content" / "audio-free" / "vault"
PRIORITY_FILE = Path(__file__).parent.parent / "vault-topup-priority.json"
STATE_FILE = Path(__file__).parent.parent / "vault-topup-state.json"

# Import vault-builder
_vb_spec = importlib.util.spec_from_file_location(
    "vault_builder",
    Path(__file__).parent.parent / "vault-builder.py"
)
vb = importlib.util.module_from_spec(_vb_spec)
_vb_spec.loader.exec_module(vb)


def scan_session(session_dir, target):
    """Scan a vault session and return chunks needing topup.

    Returns dict: {chunk_idx: (current_count, needed)} or empty if all OK.
    """
    needs = {}
    chunk_dirs = sorted(session_dir.glob("c[0-9][0-9]"))

    for chunk_dir in chunk_dirs:
        ci = int(chunk_dir.name[1:])
        prefix = f"c{ci:02d}"
        meta_path = chunk_dir / f"{prefix}_meta.json"

        if not meta_path.exists():
            continue

        existing = list(chunk_dir.glob(f"{prefix}_v*.wav"))
        count = len(existing)

        if count < target:
            needed = target - count
            needs[ci] = (count, needed)

    return needs


async def topup_all(target, dry_run=False, session_filter=None, no_upload=False):
    """Scan all vaults and top up to target pool size."""

    sessions = sorted(d.name for d in VAULT_DIR.iterdir()
                      if d.is_dir()
                      and not d.name.endswith('-backup')
                      and not d.name.endswith('-pre-fix')
                      and d.name != 'narrator-welcome')

    if session_filter:
        sessions = [s for s in sessions if session_filter in s]

    print(f"{'='*70}")
    print(f"  VAULT TOP-UP — Target: {target} candidates/chunk")
    print(f"  Sessions to scan: {len(sessions)}")
    print(f"{'='*70}\n")

    total_sessions_ok = 0
    total_sessions_need = 0
    total_chunks_need = 0
    total_new_candidates = 0
    plan = []

    for session_id in sessions:
        session_dir = VAULT_DIR / session_id
        needs = scan_session(session_dir, target)

        if not needs:
            total_sessions_ok += 1
            print(f"  OK  {session_id}")
            continue

        total_sessions_need += 1
        total_chunks_need += len(needs)

        counts = [n[1] for n in needs.values()]
        max_needed = max(counts)
        total_for_session = sum(counts)
        total_new_candidates += len(needs) * max_needed  # upper bound (some over-gen)

        current_counts = [n[0] for n in needs.values()]
        min_current = min(current_counts)
        avg_current = sum(current_counts) / len(current_counts)

        print(f"  TOP {session_id}: {len(needs)} chunks need topup "
              f"(min={min_current}, avg={avg_current:.0f}, generating +{max_needed}/chunk)")

        plan.append({
            'session_id': session_id,
            'chunks': sorted(needs.keys()),
            'max_needed': max_needed,
            'total_chunks': len(needs),
            'min_current': min_current,
        })

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"  Sessions OK: {total_sessions_ok}")
    print(f"  Sessions needing topup: {total_sessions_need}")
    print(f"  Total chunks to top up: {total_chunks_need}")
    print(f"  Estimated new candidates: ~{total_new_candidates}")
    print(f"{'='*70}")

    if dry_run:
        print("\n  DRY RUN — no generation performed")
        return

    if not plan:
        print("\n  All sessions already at target. Nothing to do.")
        return

    print(f"\n  Starting generation...\n")

    completed = 0
    processed_ids = set()

    # Load any previously completed sessions (resume support)
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            processed_ids = set(state.get("completed", []))
            if processed_ids:
                print(f"  Resuming — {len(processed_ids)} sessions already done")
        except Exception:
            pass

    while True:
        # Hot-reload priority file before each session
        remaining = [p for p in plan if p['session_id'] not in processed_ids]
        if not remaining:
            break

        remaining = _apply_priority(remaining)

        item = remaining[0]
        session_id = item['session_id']
        chunks = item['chunks']
        count = item['max_needed']

        done_count = len(processed_ids)
        total_count = len(plan)

        print(f"\n{'='*70}")
        print(f"  [{done_count + 1}/{total_count}] {session_id}")
        print(f"  Chunks: {len(chunks)} | Adding: +{count}/chunk")

        # Show what's next in queue
        upcoming = [p['session_id'] for p in remaining[1:4]]
        if upcoming:
            print(f"  Queue: {' → '.join(upcoming)}")
        print(f"{'='*70}")

        try:
            result = await vb.regen_chunks(session_id, chunks, count)
            if result:
                print(f"  Done: +{result['generated']} candidates, "
                      f"{result['uploaded']} uploaded, {result['errors']} errors")
        except Exception as e:
            print(f"  ERROR: {e}")
            print(f"  Continuing to next session...")

        processed_ids.add(session_id)
        completed += 1

        # Save state for resume
        _save_state(processed_ids)

    print(f"\n{'='*70}")
    print(f"  TOP-UP COMPLETE")
    print(f"  Sessions processed: {completed}/{len(plan)}")
    print(f"{'='*70}")

    # Clean up state file
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def _apply_priority(plan):
    """Re-sort plan based on hot-reloaded priority file."""
    if not PRIORITY_FILE.exists():
        # Default: fewest chunks first
        return sorted(plan, key=lambda p: p['total_chunks'])

    try:
        priority = json.loads(PRIORITY_FILE.read_text())
        priority_list = priority if isinstance(priority, list) else priority.get("order", [])

        # Build priority index — lower = higher priority
        priority_idx = {name: i for i, name in enumerate(priority_list)}

        def sort_key(p):
            sid = p['session_id']
            if sid in priority_idx:
                return (0, priority_idx[sid])  # Priority sessions first, in order
            return (1, p['total_chunks'])  # Then default sort

        return sorted(plan, key=sort_key)
    except Exception:
        return sorted(plan, key=lambda p: p['total_chunks'])


def _save_state(processed_ids):
    """Save progress state for resume."""
    STATE_FILE.write_text(json.dumps({
        "completed": sorted(processed_ids),
    }, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vault Top-Up — bring all vaults to minimum pool size')
    parser.add_argument('--target', type=int, default=35,
                        help='Minimum candidates per chunk (default: 35)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show plan without generating')
    parser.add_argument('--session', type=str, default=None,
                        help='Only process sessions matching this string')
    parser.add_argument('--no-upload', action='store_true',
                        help='Skip R2 upload')
    args = parser.parse_args()

    asyncio.run(topup_all(args.target, dry_run=args.dry_run,
                          session_filter=args.session))
