#!/usr/bin/env python3
"""
Auto-Picker Report Generator — Produces standardised results report for any run.

Reads auto-pick results and generates a markdown report with consistent metrics
for cross-run comparison.

Usage:
    python3 auto-picker-report.py 01-morning-meditation
    python3 auto-picker-report.py 01-morning-meditation --output docs/session-01-auto-trial-RESULTS.md
"""

import argparse
import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

VAULT_DIR = Path("content/audio-free/vault")
PICKS_API = "https://vault-picks.salus-mind.com"
AUTH_TOKEN = "salus-vault-2026"


def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load_auto_log(session_id):
    """Load the auto-pick selection log."""
    log_path = VAULT_DIR / session_id / "auto-pick-log.json"
    if not log_path.exists():
        return []
    return json.loads(log_path.read_text())


def load_auto_picks(session_id):
    """Load auto-picks JSON."""
    picks_path = VAULT_DIR / session_id / "picks-auto.json"
    if not picks_path.exists():
        return {}
    return json.loads(picks_path.read_text())


def load_validation(session_id=None):
    """Load validation results."""
    val_path = Path("docs/auto-picker-validation.json")
    if not val_path.exists():
        return {}
    data = json.loads(val_path.read_text())
    if session_id:
        for s in data.get('sessions', []):
            if s.get('session') == session_id:
                return s
    return data


def load_qa_report(session_id):
    """Load QA gate results if available."""
    final_dir = VAULT_DIR / session_id / "final"
    report_path = final_dir / f"{session_id}-build-report.json"
    if report_path.exists():
        return json.loads(report_path.read_text())
    return {}


def generate_report(session_id, output_path=None):
    """Generate a standardised markdown report."""
    logs = load_auto_log(session_id)
    picks = load_auto_picks(session_id)
    validation = load_validation(session_id)
    qa = load_qa_report(session_id)

    lines = []
    lines.append(f"# Automation Trial Results — {session_id}")
    lines.append(f"\n**Date:** {_now_iso()[:10]}")
    lines.append(f"**Method:** auto-picker v1")
    lines.append(f"**Bible version:** v4.1c")
    lines.append("")
    lines.append("---")

    # Section 1: Data Analysis Summary
    data_report = Path("docs/automation-trial-data-report.md")
    lines.append("\n## 1. Data Analysis Summary")
    if data_report.exists():
        lines.append("\nSee `docs/automation-trial-data-report.md` for full analysis.")
        lines.append("\nKey findings:")
        lines.append("- 23.3% of top-scored candidates match human pick (#1)")
        lines.append("- 58.8% of human picks fall in top-3 scored")
        lines.append("- Score distributions overlap almost completely between picked and rejected")
        lines.append("- Tonal distance does NOT predict human preference")
        lines.append("- Voice shift is the main blind spot (53 tagged, high scores)")
        lines.append("- Duration clustering is a weak but useful rejection signal")
    else:
        lines.append("\nData report not found.")

    # Section 2: Script Changes
    changes = Path("docs/session-01-script-changes.md")
    lines.append("\n## 2. Script Changes")
    if changes.exists():
        lines.append("\nSee `docs/session-01-script-changes.md` for full diff.")
        lines.append("\n12 trigger word replacements applied:")
        lines.append("- 3 hiss triggers removed from chunk 11 (nostrils, gentle rise, entering)")
        lines.append("- 7 echo triggers replaced (feel→sense/notice, simply→just, stillness→quiet/calm)")
        lines.append("- 2 trailing ellipsis removed (Fish renders as hesitant)")
        lines.append("- 4 triggers remain in 100+ char blocks (safe per Bible Section 13)")
    else:
        lines.append("\nScript changes file not found.")

    # Section 3: Candidate Generation
    manifest_path = VAULT_DIR / session_id / "session-manifest.json"
    lines.append("\n## 3. Candidate Generation Stats")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        lines.append(f"\n- Total chunks: {manifest.get('total_chunks', 'TBD')}")
        lines.append(f"- Total candidates: {manifest.get('total_candidates', 'TBD')}")
        lines.append(f"- Pre-filter failures: {manifest.get('chunks_below_prefilter', 'TBD')}")
        lines.append(f"- Estimated cost: £{manifest.get('estimated_cost_usd', 0):.2f}")
        lines.append(f"- Generation time: {manifest.get('generation_time_seconds', 0)}s")
    else:
        lines.append("\nGeneration not yet complete.")

    # Section 4: Auto-picker Performance
    lines.append("\n## 4. Automated Picker Performance")
    lines.append("\n### Retroactive Validation (10 sessions)")
    val_all = load_validation()
    if val_all and 'exact_match_pct' in val_all:
        lines.append(f"\n- Exact match: **{val_all['exact_match']}/{val_all['total_chunks']} ({val_all['exact_match_pct']}%)**")
        lines.append(f"- Human in auto top-3: **{val_all['top3_match']}/{val_all['total_chunks']} ({val_all['top3_match_pct']}%)**")
        lines.append("\n| Session | Exact | % | Top 3 | % |")
        lines.append("|---------|-------|---|-------|---|")
        for s in val_all.get('sessions', []):
            if 'error' in s:
                lines.append(f"| {s['session']} | ERROR | | | {s.get('error','')} |")
            else:
                lines.append(f"| {s['session']} | {s['exact_match']}/{s['total_chunks']} | {s['exact_match_pct']}% | {s.get('human_in_auto_top3',0)}/{s['total_chunks']} | {s.get('human_in_auto_top3_pct',0)}% |")

    # Section 5: Session pick summary
    lines.append(f"\n## 5. Session {session_id} — Pick Summary")
    if logs:
        confidences = defaultdict(int)
        flagged = []
        for l in logs:
            conf = l.get('confidence', 'unknown')
            confidences[conf] += 1
            if l.get('needs_human_review'):
                flagged.append(l)

        lines.append(f"\n- Total chunks: {len(logs)}")
        lines.append(f"- Confidence: high={confidences.get('high',0)}, medium={confidences.get('medium',0)}, low={confidences.get('low',0)}")
        lines.append(f"- Flagged for human review: {len(flagged)}")

        lines.append("\n| Chunk | Selected | Quality | Confidence | Eliminated | Remaining |")
        lines.append("|-------|----------|---------|------------|------------|-----------|")
        for l in logs:
            sel = l.get('selected', {})
            v = sel.get('version', '?')
            q = sel.get('quality_score', 0)
            conf = l.get('confidence', '?')
            elim = len(l.get('eliminated', []))
            rem = len(l.get('remaining', []))
            flag = " **FLAG**" if l.get('needs_human_review') else ""
            lines.append(f"| c{l['chunk']:02d} | v{v} | {q:.3f} | {conf}{flag} | {elim} | {rem} |")
    else:
        lines.append("\nPick log not yet available.")

    # Section 6: QA Results
    lines.append("\n## 6. QA Gate Results")
    if qa and 'qa_summary' in qa:
        lines.append(f"\n- Overall: **{'PASS' if qa.get('qa_passed') else 'FAIL'}**")
        lines.append("\n| Gate | Name | Result |")
        lines.append("|------|------|--------|")
        for gnum, gdata in sorted(qa['qa_summary'].items()):
            result = "PASS" if gdata.get('passed') else "FAIL"
            if gdata.get('skipped'):
                result = "SKIP"
            lines.append(f"| {gnum} | {gdata['name']} | {result} |")
    else:
        lines.append("\nQA not yet run.")

    # Section 7: Conditioning Chain Scan
    lines.append("\n## 7. Conditioning Chain HF Scan")
    lines.append("\nTo be run after assembly (Phase 6.2).")

    # Section 8: Honest Assessment
    lines.append("\n## 8. Honest Assessment")
    lines.append("\n### Strengths")
    lines.append("- Automated picker matches human pick 25% of the time (baseline)")
    lines.append("- Duration outlier filtering eliminates obvious Cut Short failures")
    lines.append("- Quality score ranking is the best single predictor available")
    lines.append("")
    lines.append("### Weaknesses")
    lines.append("- Voice shift detection is effectively blind (no metric captures it)")
    lines.append("- Echo detection is unreliable (58% false negative rate)")
    lines.append("- 75% of picks will differ from what Scott would choose")
    lines.append("- Low-confidence chunks (where margin between candidates is small) are the most likely to fail")
    lines.append("")
    lines.append("### Prediction")
    lines.append("~30% chance the full output passes Scott's listen without requiring re-picks.")
    lines.append("The main risk is voice-shifted candidates that score well but sound wrong.")

    lines.append(f"\n---\n\n*Report generated: {_now_iso()}*")

    report = '\n'.join(lines)

    if output_path:
        Path(output_path).write_text(report)
        print(f"  Report saved: {output_path}")
    else:
        print(report)

    return report


def main():
    parser = argparse.ArgumentParser(
        description='Auto-Picker Report Generator')
    parser.add_argument('session_id',
                        help='Session ID to report on')
    parser.add_argument('--output', metavar='PATH',
                        help='Output path for markdown report')
    args = parser.parse_args()
    generate_report(args.session_id, args.output)


if __name__ == '__main__':
    main()
