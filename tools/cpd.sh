#!/bin/bash
# CPD: Commit, Push, Deploy audio to R2
# Usage: tools/cpd.sh "commit message"
# Detects changed MP3 files in content/audio-free/ and uploads them to R2 with CDN purge.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

COMMIT_MSG="${1:-}"

if [ -z "$COMMIT_MSG" ]; then
  echo "Usage: tools/cpd.sh \"commit message\""
  exit 1
fi

# ── 1. Git commit & push ──
echo "═══ Git Commit & Push ═══"
git add -A
git commit -m "$COMMIT_MSG" || echo "(nothing to commit)"
git push origin main

# ── 2. Detect changed audio files ──
echo ""
echo "═══ Audio Deploy ═══"

# Find MP3 files modified in the last 30 minutes (likely just-built audio)
CHANGED_AUDIO=()
while IFS= read -r -d '' file; do
  # Get the R2 key (relative path from project root)
  R2_KEY="${file#$PROJECT_DIR/}"
  CHANGED_AUDIO+=("$file|$R2_KEY")
done < <(find "$PROJECT_DIR/content/audio-free" -maxdepth 1 -name "*.mp3" -mmin -30 -print0 2>/dev/null)

if [ ${#CHANGED_AUDIO[@]} -eq 0 ]; then
  echo "No recently changed audio files found in content/audio-free/"
  echo "  (Looking for MP3s modified in last 30 minutes)"
  echo "  Tip: If you built audio earlier, run: tools/r2-upload.sh <file> <r2-key>"
  exit 0
fi

echo "Found ${#CHANGED_AUDIO[@]} changed audio file(s):"
for entry in "${CHANGED_AUDIO[@]}"; do
  IFS='|' read -r file key <<< "$entry"
  echo "  → $key ($(du -h "$file" | cut -f1 | xargs))"
done

echo ""

# ── 3. Upload each to R2 + CDN purge ──
FAILED=0
for entry in "${CHANGED_AUDIO[@]}"; do
  IFS='|' read -r file key <<< "$entry"
  echo "── Deploying: $key ──"
  if bash "$SCRIPT_DIR/r2-upload.sh" "$file" "$key" "audio/mpeg"; then
    echo "  ✓ Deployed + verified"
  else
    echo "  ✗ FAILED"
    FAILED=$((FAILED + 1))
  fi
  echo ""
done

if [ $FAILED -gt 0 ]; then
  echo "WARNING: $FAILED file(s) failed to deploy"
  exit 1
else
  echo "═══ All done: committed, pushed, ${#CHANGED_AUDIO[@]} audio file(s) deployed ═══"
fi
