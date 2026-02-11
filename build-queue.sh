#!/bin/bash
# Build 6 new meditation sessions sequentially
# Session 82 is already running — start from 83
cd /Users/scottripley/salus-website

echo "=== Starting vault builds for sessions 83-87 ==="
echo "Session 82 is already building separately"
echo ""

for session in 83-five-minute-reset 84-anxiety-unravelled 85-counting-down-to-sleep 86-deep-sleep 87-ocean-voyage; do
    echo ""
    echo "=========================================="
    echo "  Starting: $session"
    echo "  Time: $(date)"
    echo "=========================================="
    python3 vault-builder.py "content/scripts/${session}.txt" 2>&1
    echo ""
    echo "  Completed: $session at $(date)"
    echo ""
    
    # Run rebuild_full_picker.py after each build
    echo "  Building picker page for $session..."
    python3 tools/vault-picker/rebuild_full_picker.py "$session" 2>&1
    echo ""
done

echo ""
echo "=========================================="
echo "  ALL 5 SESSIONS COMPLETE at $(date)"
echo "=========================================="
