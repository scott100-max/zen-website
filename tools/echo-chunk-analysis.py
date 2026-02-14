#!/usr/bin/env python3
"""Analyze echo chunks: elimination stats, ranking position, feature comparison."""
import json

log_data = json.loads(open('content/audio-free/vault/85-counting-down-to-sleep/auto-pick-log.json').read())
log_by_chunk = {str(item['chunk']): item for item in log_data}

verdicts = json.loads(open('reference/v5-test/85-verdicts-r2.json').read())
echo_chunks = {cid: vd for cid, vd in verdicts['chunks'].items() if 'ECHO' in vd['verdict']}

# Also show overall elimination stats
total_candidates = sum(item['total_candidates'] for item in log_data)
total_eliminated = sum(len(item['eliminated']) for item in log_data)
total_remaining = sum(len(item['remaining']) for item in log_data)

g17_total = 0
cutoff_total = 0
echo_risk_total = 0
for item in log_data:
    for e in item['eliminated']:
        reasons = e.get('reasons', [])
        if any('gate17' in r for r in reasons):
            g17_total += 1
        if any('cutoff' in r.lower() for r in reasons):
            cutoff_total += 1
        if any('echo_risk' in r for r in reasons):
            echo_risk_total += 1

print("=" * 70)
print("OVERALL ELIMINATION STATS")
print("=" * 70)
print(f"Total candidates: {total_candidates}")
print(f"Eliminated: {total_eliminated} ({total_eliminated/total_candidates:.1%})")
print(f"  Gate 17 (breakout): {g17_total} ({g17_total/total_candidates:.1%})")
print(f"  Cutoff (all types): {cutoff_total} ({cutoff_total/total_candidates:.1%})")
print(f"  Echo risk (legacy): {echo_risk_total}")
print(f"Remaining: {total_remaining} ({total_remaining/total_candidates:.1%})")

print()
print("=" * 70)
print("ECHO CHUNK DETAIL")
print("=" * 70)

for cid in sorted(echo_chunks.keys(), key=int):
    vd = echo_chunks[cid]
    echo_v = vd['version']

    chunk_log = log_by_chunk.get(str(cid), {})
    n_total = chunk_log.get('total_candidates', 0)
    eliminated = chunk_log.get('eliminated', [])
    remaining = chunk_log.get('remaining', [])
    selected = chunk_log.get('selected', {})

    n_elim = len(eliminated)
    n_remain = len(remaining)

    echo_elim_reasons = []
    for e in eliminated:
        if e['version'] == echo_v:
            echo_elim_reasons = e.get('reasons', [])

    echo_rank = None
    echo_score = None
    for i, r in enumerate(remaining):
        if r['version'] == echo_v:
            echo_rank = i + 1
            echo_score = r.get('rank_score')

    g17_elim = sum(1 for e in eliminated if any('gate17' in r for r in e.get('reasons', [])))

    print(f"\nc{cid:>2s} (reviewed: v{echo_v} = ECHO):")
    print(f"  Pool: {n_total} total → {n_elim} eliminated (gate17: {g17_elim}) → {n_remain} remaining")

    if echo_elim_reasons:
        print(f"  Echo v{echo_v}: ELIMINATED by {echo_elim_reasons}")
    elif echo_rank is not None:
        print(f"  Echo v{echo_v}: ranked #{echo_rank}/{n_remain} (score={echo_score:.1f})")
        # Find its echo_v2 features
        echo_entry = [r for r in remaining if r['version'] == echo_v][0]
        ceps = echo_entry.get('echo_v2_ceps', '?')
        edr = echo_entry.get('echo_v2_edr', '?')
        bz = echo_entry.get('breakout_z', '?')
        print(f"    ceps={ceps}, edr={edr}, breakout_z={bz}")
    else:
        print(f"  Echo v{echo_v}: NOT IN POOL")

    sel_v = selected.get('version')
    sel_score = selected.get('rank_score', 0)
    print(f"  Selected: v{sel_v} (score={sel_score:.1f})")
    sel_entry = [r for r in remaining if r['version'] == sel_v]
    if sel_entry:
        se = sel_entry[0]
        ceps = se.get('echo_v2_ceps', '?')
        edr = se.get('echo_v2_edr', '?')
        bz = se.get('breakout_z', '?')
        print(f"    ceps={ceps}, edr={edr}, breakout_z={bz}")

    avoided = "YES" if str(sel_v) != str(echo_v) else "NO — SAME VERSION PICKED"
    print(f"  Avoided echo version: {avoided}")
