#!/usr/bin/env python3
"""Rebuild review.html: fresh CSS + HTML + all 66 chunks + new v2 JS."""

import json, glob, os

VAULT = '/Users/scottripley/salus-website/content/audio-free/vault/52-the-court-of-your-mind'
REVIEW = os.path.join(VAULT, 'review.html')

# Read all chunk metadata files
chunk_dirs = sorted(glob.glob(os.path.join(VAULT, 'c[0-9][0-9]')))
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

# Read the three replacement parts from temp files
with open('/tmp/ab_picker_css.txt', 'r') as f:
    css = f.read()
with open('/tmp/ab_picker_html.txt', 'r') as f:
    html_body = f.read()
with open('/tmp/ab_picker_js.js', 'r') as f:
    js = f.read()

# Build data section
data_json = json.dumps(all_chunks, indent=2)

# Assemble complete file from scratch
parts = []
parts.append('<!DOCTYPE html>\n')
parts.append('<html lang="en">\n')
parts.append('<head>\n')
parts.append('<meta charset="UTF-8">\n')
parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
parts.append('<title>Vault Picker — 52-the-court-of-your-mind</title>\n')
parts.append(css + '\n')
parts.append('</head>\n')
parts.append('<body>\n')
parts.append(html_body + '\n')
parts.append('\n<script>\n')
parts.append(f"var SESSION_ID = '52-the-court-of-your-mind';\n")
parts.append(f"var chunkData = {data_json};\n\n")
parts.append(js + '\n')
parts.append('</script>\n')
parts.append('</body>\n')
parts.append('</html>\n')

output = ''.join(parts)

with open(REVIEW, 'w') as f:
    f.write(output)

# Verify
with open(REVIEW, 'r') as f:
    final = f.read()

import re
chunk_count = len(re.findall(r'"idx":', final))
assert chunk_count == len(all_chunks), f"Expected {len(all_chunks)} chunks, found {chunk_count}"
assert 'Picker v2' in final, "Missing v2 marker"
assert 'try { saveState()' in final, "Missing try/catch saveState"
assert 'logDebug' in final, "Missing debug logging"
assert 'pickCounter' in final, "Missing pick counter"

line_count = final.count('\n')
print(f"Wrote {len(final):,} bytes, {line_count:,} lines")
print(f"Chunks in file: {chunk_count}")
print("All checks passed")
