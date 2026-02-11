#!/bin/bash
set -euo pipefail
cd /Users/scottripley/salus-website
source .env

LOG="vault-21day-remaining-$(date +%Y%m%d-%H%M%S).log"

echo "========================================" | tee "$LOG"
echo "21-Day Mindfulness — Remaining Sessions" | tee -a "$LOG"
echo "Started: $(date -u)" | tee -a "$LOG"
echo "========================================" | tee -a "$LOG"

SUCCESS=0
FAIL=0

for DAY in $(seq 8 21); do
    NUM=$((56 + DAY))
    PADDAY=$(printf "%02d" $DAY)
    SCRIPT="content/scripts/${NUM}-21day-mindfulness-day${PADDAY}.txt"
    
    echo "" | tee -a "$LOG"
    echo "[$(( DAY - 7 ))/14] Processing Day ${DAY} (Session ${NUM})..." | tee -a "$LOG"
    echo "Started: $(date -u)" | tee -a "$LOG"
    
    if python3 vault-builder.py "$SCRIPT" 2>&1 | tee -a "$LOG"; then
        echo "  ✓ Day ${DAY} complete" | tee -a "$LOG"
        echo "Completed: $(date -u)" | tee -a "$LOG"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "  ✗ Day ${DAY} FAILED" | tee -a "$LOG"
        FAIL=$((FAIL + 1))
    fi
    
    # 10s pause between sessions for rate limiting
    if [ $DAY -lt 21 ]; then
        sleep 10
    fi
done

echo "" | tee -a "$LOG"
echo "========================================" | tee -a "$LOG"
echo "BATCH COMPLETE: ${SUCCESS} succeeded, ${FAIL} failed" | tee -a "$LOG"
echo "Finished: $(date -u)" | tee -a "$LOG"
echo "========================================" | tee -a "$LOG"
