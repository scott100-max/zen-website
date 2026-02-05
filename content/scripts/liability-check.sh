#!/bin/bash
# liability-check.sh - Scan script for problematic language
# Part of Salus Audio QA Pipeline
# Created: 5 February 2026

SCRIPT="$1"
if [ -z "$SCRIPT" ]; then
    echo "Usage: liability-check.sh <script.txt>"
    exit 1
fi

echo "=== LIABILITY CHECK: $SCRIPT ==="
echo ""

ISSUES=0

# Medical language
echo "--- Medical/Treatment Terms ---"
FOUND=$(grep -in "cure\|treat\|heal\|therap\|clinical\|prescription\|diagnosis\|symptom\|medication\|dose" "$SCRIPT" 2>/dev/null | head -20)
if [ -n "$FOUND" ]; then
    echo "$FOUND"
    ISSUES=$((ISSUES + $(echo "$FOUND" | wc -l)))
else
    echo "None found ✓"
fi

echo ""
echo "--- Brain/Body Claims ---"
FOUND=$(grep -in "brain\|cortisol\|hormone\|neural\|nervous system\|amygdala\|prefrontal" "$SCRIPT" 2>/dev/null | head -20)
if [ -n "$FOUND" ]; then
    echo "$FOUND"
    ISSUES=$((ISSUES + $(echo "$FOUND" | wc -l)))
else
    echo "None found ✓"
fi

echo ""
echo "--- Outcome Promises ---"
FOUND=$(grep -in "will make\|will help you\|proven\|guaranteed\|definitely\|always work\|scientific" "$SCRIPT" 2>/dev/null | head -20)
if [ -n "$FOUND" ]; then
    echo "$FOUND"
    ISSUES=$((ISSUES + $(echo "$FOUND" | wc -l)))
else
    echo "None found ✓"
fi

echo ""
echo "--- Alarming Language ---"
FOUND=$(grep -in "damage\|destroy\|kill\|shrink\|deteriorat\|harm\|toxic\|poison" "$SCRIPT" 2>/dev/null | head -20)
if [ -n "$FOUND" ]; then
    echo "$FOUND"
    ISSUES=$((ISSUES + $(echo "$FOUND" | wc -l)))
else
    echo "None found ✓"
fi

echo ""
echo "================================"
if [ "$ISSUES" -gt 0 ]; then
    echo "⚠ REVIEW NEEDED: $ISSUES potential issues found"
    echo "Review each flagged line and rewrite if necessary."
    exit 1
else
    echo "✓ PASSED: No liability issues detected"
    exit 0
fi
