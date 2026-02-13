#!/usr/bin/env python3
"""
Trigger Word Scanner — scans scripts against known Fish Audio trigger words.

Reads from content/trigger-words.json. Reports chunks containing trigger words
with defect type and suggested alternatives.

Usage:
    python3 tools/trigger-word-scan.py content/scripts/40-seven-day-mindfulness-day3.txt
    python3 tools/trigger-word-scan.py content/scripts/40-seven-day-mindfulness-day3.txt --fix
    python3 tools/trigger-word-scan.py --all                # scan all scripts
"""

import argparse
import json
import re
import sys
from pathlib import Path

TRIGGER_WORDS_PATH = Path(__file__).parent.parent / 'content' / 'trigger-words.json'
SCRIPTS_DIR = Path(__file__).parent.parent / 'content' / 'scripts'


def load_trigger_words():
    """Load trigger words from JSON file."""
    data = json.loads(TRIGGER_WORDS_PATH.read_text())
    words = []
    for w in data.get('words', []):
        words.append({
            'word': w['word'].lower(),
            'defect': w.get('defect', 'unknown'),
            'alternatives': w.get('alternatives', []),
            'notes': w.get('notes', ''),
        })
    patterns = []
    for p in data.get('patterns', []):
        patterns.append({
            'pattern': re.compile(p['pattern'], re.IGNORECASE),
            'defect': p.get('defect', 'unknown'),
            'description': p.get('description', ''),
            'alternatives': p.get('alternatives', []),
        })
    return words, patterns


def parse_script(script_path):
    """Parse a script file into chunks (text blocks separated by pauses)."""
    lines = Path(script_path).read_text().strip().split('\n')

    # Skip header (everything before ---)
    chunks = []
    in_body = False
    current_text = []

    for line in lines:
        if line.strip() == '---':
            in_body = True
            continue
        if not in_body:
            continue

        stripped = line.strip()

        # Pause markers end a chunk
        if stripped in ('...', '......') or stripped.startswith('[SILENCE'):
            if current_text:
                text = ' '.join(current_text).strip()
                if text:
                    chunks.append(text)
                current_text = []
            continue

        # Empty lines within body
        if not stripped:
            continue

        current_text.append(stripped)

    # Final chunk
    if current_text:
        text = ' '.join(current_text).strip()
        if text:
            chunks.append(text)

    return chunks


def scan_chunk(text, words, patterns):
    """Scan a single chunk for trigger words. Returns list of matches."""
    matches = []
    text_lower = text.lower()

    for w in words:
        # Multi-word phrases: exact substring match
        if ' ' in w['word']:
            if w['word'] in text_lower:
                matches.append(w)
        else:
            # Single words: word boundary match
            if re.search(r'\b' + re.escape(w['word']) + r'\w*\b', text_lower):
                matches.append(w)

    for p in patterns:
        if p['pattern'].search(text):
            matches.append({
                'word': p['description'],
                'defect': p['defect'],
                'alternatives': p['alternatives'],
                'notes': '',
            })

    return matches


def scan_script(script_path, words, patterns):
    """Scan a full script and return results."""
    chunks = parse_script(script_path)
    results = []

    for i, text in enumerate(chunks):
        matches = scan_chunk(text, words, patterns)
        if matches:
            results.append({
                'chunk': i,
                'text': text,
                'char_count': len(text),
                'matches': matches,
            })

    return chunks, results


def print_results(script_path, chunks, results):
    """Print scan results."""
    name = Path(script_path).stem
    print(f"\n{'='*70}")
    print(f"  TRIGGER WORD SCAN — {name}")
    print(f"  {len(chunks)} chunks, {len(results)} flagged")
    print(f"{'='*70}\n")

    if not results:
        print("  CLEAN — no trigger words found.\n")
        return 0

    for r in results:
        ci = r['chunk']
        text = r['text']
        chars = r['char_count']
        print(f"  c{ci:02d} ({chars} chars):")
        print(f"    \"{text[:100]}{'...' if len(text) > 100 else ''}\"")
        for m in r['matches']:
            defect = m['defect'].upper()
            alts = ', '.join(m['alternatives']) if m['alternatives'] else 'no alternatives listed'
            print(f"    ⚠ \"{m['word']}\" → {defect} — try: {alts}")
            if m.get('notes'):
                print(f"      Note: {m['notes']}")
        print()

    # Summary
    total_flags = sum(len(r['matches']) for r in results)
    echo_count = sum(1 for r in results for m in r['matches'] if m['defect'] == 'echo')
    hiss_count = sum(1 for r in results for m in r['matches'] if m['defect'] == 'hiss')
    other_count = total_flags - echo_count - hiss_count

    print(f"  Summary: {total_flags} trigger words in {len(results)}/{len(chunks)} chunks")
    if echo_count:
        print(f"    Echo risk: {echo_count}")
    if hiss_count:
        print(f"    Hiss risk: {hiss_count}")
    if other_count:
        print(f"    Other: {other_count}")
    print()

    return len(results)


def main():
    parser = argparse.ArgumentParser(description='Trigger Word Scanner')
    parser.add_argument('script', nargs='?', help='Script file to scan')
    parser.add_argument('--all', action='store_true', help='Scan all scripts')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    if not TRIGGER_WORDS_PATH.exists():
        print(f"ERROR: Trigger words file not found: {TRIGGER_WORDS_PATH}")
        sys.exit(1)

    words, patterns = load_trigger_words()
    print(f"  Loaded {len(words)} trigger words + {len(patterns)} patterns")

    if args.all:
        scripts = sorted(SCRIPTS_DIR.glob('*.txt'))
        total_flagged = 0
        flagged_scripts = []
        for s in scripts:
            chunks, results = scan_script(s, words, patterns)
            if results:
                flagged_scripts.append((s, chunks, results))
                total_flagged += len(results)

        print(f"\n  Scanned {len(scripts)} scripts")
        print(f"  {len(flagged_scripts)} scripts have trigger words ({total_flagged} chunks total)\n")

        for s, chunks, results in flagged_scripts:
            print_results(s, chunks, results)
        return

    if not args.script:
        parser.print_help()
        sys.exit(1)

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        sys.exit(1)

    chunks, results = scan_script(script_path, words, patterns)

    if args.json:
        output = {
            'script': str(script_path),
            'total_chunks': len(chunks),
            'flagged_chunks': len(results),
            'results': results,
        }
        print(json.dumps(output, indent=2))
    else:
        flagged = print_results(script_path, chunks, results)
        if flagged:
            print(f"  ⚠ Review flagged chunks before building. Replace trigger words or accept the risk.\n")


if __name__ == '__main__':
    main()
