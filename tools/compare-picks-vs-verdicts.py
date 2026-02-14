#!/usr/bin/env python3
"""
Compare auto-picker picks against human verdicts.
Shows whether new echo_v2 picks avoid the chunks that failed review.

Usage:
    python3 tools/compare-picks-vs-verdicts.py 85
    python3 tools/compare-picks-vs-verdicts.py 63
"""
import json
import sys
from pathlib import Path

VAULT = Path("content/audio-free/vault")
V5 = Path("reference/v5-test")

SESSION_NAMES = {
    "85": "85-counting-down-to-sleep",
    "63": "63-21day-mindfulness-day07",
    "09": "09-rainfall-sleep-journey",
}


def compare(session_short):
    sname = SESSION_NAMES[session_short]

    # Load current picks
    picks_path = VAULT / sname / "picks-auto.json"
    if not picks_path.exists():
        print(f"ERROR: {picks_path} not found")
        return
    with open(picks_path) as f:
        picks = json.load(f)

    # Load old picks (v5 test)
    old_picks_path = V5 / f"{session_short}-picks-auto-v5.json"
    old_picks = None
    if old_picks_path.exists():
        with open(old_picks_path) as f:
            old_picks = json.load(f)

    # Load verdicts
    verdict_path = V5 / f"{session_short}-verdicts-r2.json"
    if not verdict_path.exists():
        print(f"WARNING: {verdict_path} not found — no verdicts to compare")
        return
    with open(verdict_path) as f:
        verdicts = json.load(f)

    # Build pick maps
    new_pick_map = {}
    for p in picks.get("picks", []):
        new_pick_map[str(p["chunk"])] = p.get("picked", -1)

    old_pick_map = {}
    if old_picks:
        for p in old_picks.get("picks", []):
            old_pick_map[str(p["chunk"])] = p.get("picked", -1)

    print(f"Session: {sname}")
    print(f"Verdicts: {verdicts['ok']}/{verdicts['reviewed']} pass ({verdicts['ok']/verdicts['reviewed']:.0%})")
    print()

    # Compare
    same = 0
    changed = 0
    echo_avoided = 0
    echo_still_hit = 0
    defect_avoided = 0
    defect_still_hit = 0

    print(f"{'Chunk':>5} {'Old':>5} {'New':>5} {'Verdict':>20} {'Change':>15}")
    print("─" * 60)

    for chunk_id in sorted(verdicts["chunks"].keys(), key=int):
        vd = verdicts["chunks"][chunk_id]
        old_v = old_pick_map.get(chunk_id, "?")
        new_v = new_pick_map.get(chunk_id, "?")
        verdict_v = vd["version"]
        labels = ",".join(vd["verdict"])
        passed = vd["passed"]

        # The verdict was for the OLD pick (verdict_v should match old_v)
        if old_v == new_v:
            change = "same"
            same += 1
            if not passed and "ECHO" in vd["verdict"]:
                echo_still_hit += 1
            if not passed:
                defect_still_hit += 1
        else:
            change = "CHANGED"
            changed += 1
            if not passed and "ECHO" in vd["verdict"]:
                echo_avoided += 1
                change = "ECHO AVOIDED"
            elif not passed:
                defect_avoided += 1
                change = "defect avoided?"

        marker = "" if passed else "FAIL"
        print(f"  c{chunk_id:>2s}   v{old_v:>3}  v{new_v:>3}  {labels:>20}  {change:>15}  {marker}")

    print()
    print(f"Same picks: {same}/{same+changed}")
    print(f"Changed picks: {changed}/{same+changed}")
    if echo_avoided + echo_still_hit > 0:
        print(f"ECHO chunks: {echo_avoided} avoided, {echo_still_hit} still same pick")
    if defect_avoided + defect_still_hit > 0:
        print(f"Other defects: {defect_avoided} changed, {defect_still_hit} same pick")
    print(f"\nNote: 'avoided' means the picker chose a DIFFERENT version than the one")
    print(f"that failed review. It may or may not be better — needs re-review to confirm.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/compare-picks-vs-verdicts.py <session_short>")
        sys.exit(1)
    compare(sys.argv[1])
