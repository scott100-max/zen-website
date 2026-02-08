#!/bin/bash

# Salus Website Fixes Validation Script
# Validates that all requested fixes have been implemented correctly

PASS=0
FAIL=0
TOTAL=0

check() {
    TOTAL=$((TOTAL + 1))
    DESC="$1"
    RESULT="$2"

    if [ "$RESULT" = "true" ]; then
        echo "✓ PASS: $DESC"
        PASS=$((PASS + 1))
    else
        echo "✗ FAIL: $DESC"
        FAIL=$((FAIL + 1))
    fi
}

echo "========================================"
echo "SALUS WEBSITE FIXES VALIDATION"
echo "========================================"
echo ""

# -------------------------------------------
# #10 - Play button not round (mindfulness.html)
# Fix: Added flex-shrink:0 to play buttons
# -------------------------------------------
echo "--- #10: Play button fix (mindfulness.html) ---"

COUNT=$(grep -c 'flex-shrink:0.*cp-play\|cp-play.*flex-shrink:0' mindfulness.html 2>/dev/null || echo "0")
if [ "$COUNT" -ge 1 ]; then
    check "Play buttons have flex-shrink:0 in mindfulness.html" "true"
else
    # Check alternative pattern
    COUNT=$(grep -c 'style="flex-shrink:0;background:var(--accent)' mindfulness.html 2>/dev/null || echo "0")
    if [ "$COUNT" -ge 1 ]; then
        check "Play buttons have flex-shrink:0 in mindfulness.html" "true"
    else
        check "Play buttons have flex-shrink:0 in mindfulness.html" "false"
    fi
fi

# -------------------------------------------
# #13 - Breathing ring/countdown sync (breathe.html)
# Fix: Single unified timer instead of two separate timers
# -------------------------------------------
echo ""
echo "--- #13: Breathing ring/countdown sync (breathe.html) ---"

# Check that mainTimer exists (unified timer)
if grep -q 'var mainTimer = null' breathe.html 2>/dev/null; then
    check "Single mainTimer variable exists" "true"
else
    check "Single mainTimer variable exists" "false"
fi

# Check that old separate ringTimer pattern is removed
if grep -q 'ringTimer = setInterval(updateRing' breathe.html 2>/dev/null; then
    check "Old separate ringTimer removed" "false"
else
    check "Old separate ringTimer removed" "true"
fi

# Check unified tick function updates both countdown and ring
if grep -q 'cycleElapsed++' breathe.html 2>/dev/null && grep -q 'phaseElapsed++' breathe.html 2>/dev/null; then
    check "Unified tick updates both counters" "true"
else
    check "Unified tick updates both counters" "false"
fi

# -------------------------------------------
# #12 - Tools buttons simplified (tools.html)
# Fix: Removed gradient circles, simple SVG icons
# -------------------------------------------
echo ""
echo "--- #12: Tools buttons simplified (tools.html) ---"

# Check gradient circles are removed
if grep -q 'linear-gradient(135deg,#e8f5e9,#81c784)' tools.html 2>/dev/null; then
    check "Gradient circles removed from tools.html" "false"
else
    check "Gradient circles removed from tools.html" "true"
fi

# Check simple SVG icons exist with accent color
if grep -q 'stroke="var(--accent)"' tools.html 2>/dev/null; then
    check "Simple SVG icons with accent color" "true"
else
    check "Simple SVG icons with accent color" "false"
fi

# -------------------------------------------
# #5 - Profile pictures consistent (about.html)
# Fix: Ella and Marco use img tags, no gradient overlays
# -------------------------------------------
echo ""
echo "--- #5: Profile pictures consistent (about.html) ---"

# Check Ella uses img tag
if grep -q '<img src="content/images/team/ella.jpg"' about.html 2>/dev/null; then
    check "Ella photo uses img tag" "true"
else
    check "Ella photo uses img tag" "false"
fi

# Check Marco uses img tag
if grep -q '<img src="content/images/narrator-marco.jpg"' about.html 2>/dev/null; then
    check "Marco photo uses img tag" "true"
else
    check "Marco photo uses img tag" "false"
fi

# Check gradient overlay removed from Marco
if grep -q 'linear-gradient.*narrator-marco' about.html 2>/dev/null; then
    check "Marco gradient overlay removed" "false"
else
    check "Marco gradient overlay removed" "true"
fi

# -------------------------------------------
# #2 - Session cards look like players (css/style.css)
# Fix: Play button overlay on session thumbnails
# -------------------------------------------
echo ""
echo "--- #2: Session cards look like players (style.css) ---"

# Check play button overlay exists in CSS
if grep -q 'session-thumb::after' css/style.css 2>/dev/null && grep -q 'polygon points' css/style.css 2>/dev/null; then
    check "Play button overlay in session-thumb::after" "true"
else
    check "Play button overlay in session-thumb::after" "false"
fi

# Check thumbnail height reduced
if grep -q 'session-thumb' css/style.css 2>/dev/null && grep -q 'height: 120px' css/style.css 2>/dev/null; then
    check "Session thumbnail height reduced to 120px" "true"
else
    check "Session thumbnail height reduced to 120px" "false"
fi

# -------------------------------------------
# 21-Day Mindfulness Course
# Fix: Teaser on mindfulness.html, new page created
# -------------------------------------------
echo ""
echo "--- 21-Day Mindfulness Course ---"

# Check teaser exists on mindfulness.html
if grep -q '21-Day Mindfulness Course' mindfulness.html 2>/dev/null && grep -q 'mindfulness-21-day.html' mindfulness.html 2>/dev/null; then
    check "21-day course teaser on mindfulness.html" "true"
else
    check "21-day course teaser on mindfulness.html" "false"
fi

# Check new page exists
if [ -f "mindfulness-21-day.html" ]; then
    check "mindfulness-21-day.html file exists" "true"
else
    check "mindfulness-21-day.html file exists" "false"
fi

# Check 21-day page has 3 weeks
if grep -q 'Week 1' mindfulness-21-day.html 2>/dev/null && grep -q 'Week 2' mindfulness-21-day.html 2>/dev/null && grep -q 'Week 3' mindfulness-21-day.html 2>/dev/null; then
    check "21-day page has 3 weeks structure" "true"
else
    check "21-day page has 3 weeks structure" "false"
fi

# Check Day 1 is free with audio player
if grep -q 'day-card active' mindfulness-21-day.html 2>/dev/null && grep -q 'custom-player' mindfulness-21-day.html 2>/dev/null; then
    check "Day 1 is free with audio player" "true"
else
    check "Day 1 is free with audio player" "false"
fi

# Check locked days exist
LOCKED_COUNT=$(grep -c 'day-card locked' mindfulness-21-day.html 2>/dev/null || echo "0")
if [ "$LOCKED_COUNT" -ge 20 ]; then
    check "Days 2-21 are locked ($LOCKED_COUNT locked cards)" "true"
else
    check "Days 2-21 are locked ($LOCKED_COUNT locked cards)" "false"
fi

# -------------------------------------------
# Summary
# -------------------------------------------
echo ""
echo "========================================"
echo "VALIDATION SUMMARY"
echo "========================================"
echo "Passed: $PASS / $TOTAL"
echo "Failed: $FAIL / $TOTAL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "STATUS: ALL CHECKS PASSED"
    exit 0
else
    echo "STATUS: SOME CHECKS FAILED"
    exit 1
fi
