#!/bin/bash
# Audio player with timestamp display
# Usage: ./play-audio.sh <audio-file>

FILE="$1"
if [ -z "$FILE" ]; then
    echo "Usage: ./play-audio.sh <audio-file.mp3>"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "File not found: $FILE"
    exit 1
fi

# Get duration
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$FILE" 2>/dev/null)
DURATION_INT=${DURATION%.*}

echo "Playing: $(basename "$FILE")"
echo "Duration: $((DURATION_INT/60))m $((DURATION_INT%60))s"
echo "Press Ctrl+C to stop"
echo ""
echo "Timestamp:"

# Start playback in background
afplay "$FILE" &
PID=$!

# Display timer
START=$(date +%s)
while kill -0 $PID 2>/dev/null; do
    ELAPSED=$(($(date +%s) - START))
    MINS=$((ELAPSED / 60))
    SECS=$((ELAPSED % 60))
    printf "\r  %02d:%02d / %02d:%02d  " $MINS $SECS $((DURATION_INT/60)) $((DURATION_INT%60))
    sleep 0.5
done

echo ""
echo "Done."
