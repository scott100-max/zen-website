#!/bin/bash
# Full pipeline for session 91 — runs after vault-builder completes
# Autonomous mode: auto-picker → vault-assemble → review page → email
set -e
cd /Users/scottripley/salus-website
export $(grep FISH_API_KEY .env)
export $(grep RESEND_API_KEY .env)

SESSION="91-the-body-scan"
VAULT_DIR="content/audio-free/vault/$SESSION"
RUN="v1"

echo "=== STAGE 1: Waiting for vault-builder to finish ==="
# Wait for vault-builder process to complete
while pgrep -f "vault-builder.py" > /dev/null 2>&1; do
    DONE=$(find "$VAULT_DIR" -name "*.wav" -type f | wc -l | tr -d ' ')
    echo "  $(date '+%H:%M:%S') — $DONE WAVs generated..."
    sleep 60
done
echo "  Vault build complete at $(date)"

# Count final WAVs
TOTAL_WAVS=$(find "$VAULT_DIR" -name "*.wav" -type f | wc -l | tr -d ' ')
echo "  Total WAVs: $TOTAL_WAVS"

echo ""
echo "=== STAGE 2: Auto-picker ==="
python3 auto-picker.py "$SESSION" 2>&1 | tee /tmp/autopicker-91.log
echo "  Auto-picker complete"

echo ""
echo "=== STAGE 3: Vault assemble ==="
python3 vault-assemble.py "$SESSION" 2>&1 | tee /tmp/assemble-91.log
echo "  Assembly complete"

echo ""
echo "=== STAGE 4: Review page ==="
python3 tools/review-page-generator.py "$SESSION" --run "$RUN" --local 2>&1
REVIEW_PAGE="$VAULT_DIR/auto-trial-review-${RUN}.html"
echo "  Review page: $REVIEW_PAGE"

echo ""
echo "=== STAGE 5: Email notification ==="
# Get pick stats from auto-pick log
PICKS_FILE="$VAULT_DIR/picks-auto.json"
if [ -f "$PICKS_FILE" ]; then
    CHUNK_COUNT=$(python3 -c "import json; d=json.load(open('$PICKS_FILE')); print(len(d['picks']))")
    HIGH_CONF=$(python3 -c "
import json
log = json.load(open('$VAULT_DIR/auto-pick-log.json'))
print(sum(1 for l in log if l.get('confidence') == 'high'))
")
    MED_CONF=$(python3 -c "
import json
log = json.load(open('$VAULT_DIR/auto-pick-log.json'))
print(sum(1 for l in log if l.get('confidence') == 'medium'))
")
    LOW_CONF=$(python3 -c "
import json
log = json.load(open('$VAULT_DIR/auto-pick-log.json'))
print(sum(1 for l in log if l.get('confidence') == 'low'))
")
else
    CHUNK_COUNT="?"
    HIGH_CONF="?"
    MED_CONF="?"
    LOW_CONF="?"
fi

# Send email via Resend
curl -s -X POST "https://api.resend.com/emails" \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"from\": \"Claude <claude@salus-mind.com>\",
    \"to\": [\"scottripley@icloud.com\"],
    \"reply_to\": \"claude@salus-mind.com\",
    \"subject\": \"Session 91 — The Body Scan — Ready for Review\",
    \"text\": \"Session 91 (The Body Scan) is built and ready for your review.\n\nPipeline summary:\n- Total WAVs generated: $TOTAL_WAVS\n- Pool size: 100 per chunk\n- Chunks: $CHUNK_COUNT\n- Auto-picker confidence: $HIGH_CONF high / $MED_CONF medium / $LOW_CONF low\n\nReview page (open in browser):\nfile://$PWD/$REVIEW_PAGE\n\nVault location:\n$PWD/$VAULT_DIR\n\nThe review page has:\n- Full chunk text (no truncation)\n- Auto-advance after verdict click\n- localStorage persistence (survives refresh)\n- Click-to-start overlay\n\nKeyboard shortcuts:\n1=EXCELLENT 2=OK 3=ECHO 4=HISS 5=VOICE 6=CUTOFF 7=BAD\nH=Hard S=Soft | Space=Pause | Enter=Next\n\nWhen done reviewing, click Export Verdicts to download the JSON.\n\n— Claude\"
  }"

echo ""
echo "=== PIPELINE COMPLETE ==="
echo "Review page: file://$PWD/$REVIEW_PAGE"
echo "Email sent to scottripley@icloud.com"
