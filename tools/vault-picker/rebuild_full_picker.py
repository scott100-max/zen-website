#!/usr/bin/env python3
"""Rebuild review.html for any vault session from picker source files + chunk metadata.

Usage:
    python3 tools/vault-picker/rebuild_full_picker.py 52-the-court-of-your-mind
    python3 tools/vault-picker/rebuild_full_picker.py 01-morning-meditation
"""

import argparse
import json
import glob
import os
import re
import sys

# Source files live alongside this script
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_BASE = os.path.join(os.path.dirname(TOOLS_DIR), '..', 'content', 'audio-free', 'vault')
VAULT_BASE = os.path.normpath(VAULT_BASE)


def rebuild(session_id):
    vault_dir = os.path.join(VAULT_BASE, session_id)
    review_path = os.path.join(vault_dir, 'review.html')

    if not os.path.isdir(vault_dir):
        print(f"ERROR: Vault directory not found: {vault_dir}")
        return False

    # Read all chunk metadata files
    chunk_dirs = sorted(glob.glob(os.path.join(vault_dir, 'c[0-9][0-9]')))
    print(f"Found {len(chunk_dirs)} chunk directories")

    all_chunks = []
    for cdir in chunk_dirs:
        dirname = os.path.basename(cdir)
        meta_file = os.path.join(cdir, f"{dirname}_meta.json")
        if not os.path.exists(meta_file):
            print(f"WARNING: No metadata for {dirname}")
            continue

        with open(meta_file, 'r') as f:
            meta = json.load(f)

        candidates = []
        for c in meta['candidates']:
            candidates.append({
                "v": c['version'],
                "file": f"{dirname}/{c['filename']}",
                "score": round(c['composite_score'], 4),
                "dur": round(c['duration_seconds'], 2),
                "tone": round(c.get('tonal_distance_to_prev', 0), 6),
                "filtered": c['filtered']
            })

        all_chunks.append({
            "idx": meta['chunk_index'],
            "text": meta['text'],
            "chars": meta['char_count'],
            "isOpening": meta['is_opening'],
            "isClosing": meta['is_closing'],
            "candidates": candidates
        })

    all_chunks.sort(key=lambda c: c['idx'])
    print(f"Built chunkData with {len(all_chunks)} chunks")
    total_candidates = sum(len(c['candidates']) for c in all_chunks)
    print(f"Total candidates: {total_candidates}")

    # Read the three source parts from tools/vault-picker/
    with open(os.path.join(TOOLS_DIR, 'ab_picker_css.txt'), 'r') as f:
        css = f.read()
    with open(os.path.join(TOOLS_DIR, 'ab_picker_html.txt'), 'r') as f:
        html_body = f.read()
    with open(os.path.join(TOOLS_DIR, 'ab_picker_js.js'), 'r') as f:
        js = f.read()

    # Replace template placeholders in HTML body
    html_body = html_body.replace('{{SESSION_ID}}', session_id)

    # Build data section
    data_json = json.dumps(all_chunks, indent=2)

    # Assemble complete file from scratch
    parts = []
    parts.append('<!DOCTYPE html>\n')
    parts.append('<html lang="en">\n')
    parts.append('<head>\n')
    parts.append('<meta charset="UTF-8">\n')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
    parts.append(f'<title>Vault Picker — {session_id}</title>\n')
    parts.append(css + '\n')
    parts.append('</head>\n')
    parts.append('<body>\n')
    parts.append(html_body + '\n')
    parts.append('\n<script>\n')
    parts.append(f"var SESSION_ID = '{session_id}';\n")
    parts.append(f"var chunkData = {data_json};\n\n")
    parts.append(js + '\n')
    parts.append('</script>\n')
    parts.append('</body>\n')
    parts.append('</html>\n')

    output = ''.join(parts)

    with open(review_path, 'w') as f:
        f.write(output)

    # Verify
    with open(review_path, 'r') as f:
        final = f.read()

    chunk_count = len(re.findall(r'"idx":', final))
    assert chunk_count == len(all_chunks), f"Expected {len(all_chunks)} chunks, found {chunk_count}"
    assert 'Picker v2' in final, "Missing v2 marker"
    assert 'try { saveState()' in final, "Missing try/catch saveState"
    assert 'logDebug' in final, "Missing debug logging"
    assert 'pickCounter' in final, "Missing pick counter"
    assert session_id in final, f"Missing session ID '{session_id}' in output"

    line_count = final.count('\n')
    print(f"Wrote {len(final):,} bytes, {line_count:,} lines")
    print(f"Chunks in file: {chunk_count}")
    print(f"Output: {review_path}")
    print("All checks passed")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Rebuild review.html for a vault session')
    parser.add_argument('session_id',
                        help='Session ID (e.g., 52-the-court-of-your-mind)')
    args = parser.parse_args()

    success = rebuild(args.session_id)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
