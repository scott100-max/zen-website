#!/bin/bash
# Batch vault builder for 21-day mindfulness course
# Runs sequentially, one session at a time (Production Rule 1)

set -e
cd /Users/scottripley/salus-website
source .env
export FISH_API_KEY

LOGFILE="vault-21day-batch-$(date +%Y%m%d-%H%M%S).log"
TOTAL=21
DONE=0
FAILED=0

echo "========================================" | tee -a "$LOGFILE"
echo "21-Day Mindfulness Course — Vault Batch" | tee -a "$LOGFILE"
echo "Started: $(date)" | tee -a "$LOGFILE"
echo "========================================" | tee -a "$LOGFILE"

for DAY in $(seq -w 1 21); do
    SESSION_NUM=$((56 + 10#$DAY))
    SCRIPT="content/scripts/${SESSION_NUM}-21day-mindfulness-day${DAY}.txt"
    
    if [ ! -f "$SCRIPT" ]; then
        echo "SKIP: $SCRIPT not found" | tee -a "$LOGFILE"
        continue
    fi
    
    echo "" | tee -a "$LOGFILE"
    echo "[$((DONE+1))/$TOTAL] Processing Day $DAY (Session $SESSION_NUM)..." | tee -a "$LOGFILE"
    echo "Started: $(date)" | tee -a "$LOGFILE"
    
    if python3 vault-builder.py "$SCRIPT" >> "$LOGFILE" 2>&1; then
        DONE=$((DONE + 1))
        echo "  ✓ Day $DAY complete ($DONE/$TOTAL)" | tee -a "$LOGFILE"
    else
        FAILED=$((FAILED + 1))
        echo "  ✗ Day $DAY FAILED ($FAILED failures so far)" | tee -a "$LOGFILE"
    fi
    
    echo "Completed: $(date)" | tee -a "$LOGFILE"
    
    # Brief pause between sessions to avoid rate limits
    if [ $DONE -lt $TOTAL ]; then
        sleep 10
    fi
done

echo "" | tee -a "$LOGFILE"
echo "========================================" | tee -a "$LOGFILE"
echo "Batch complete: $DONE succeeded, $FAILED failed" | tee -a "$LOGFILE"
echo "Finished: $(date)" | tee -a "$LOGFILE"
echo "========================================" | tee -a "$LOGFILE"
