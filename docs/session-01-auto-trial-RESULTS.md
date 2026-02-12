# Automation Trial Results — 01-morning-meditation

**Date:** 2026-02-12
**Method:** auto-picker v1
**Bible version:** v4.1c

---

## 1. Data Analysis Summary

See `docs/automation-trial-data-report.md` for full analysis.

Key findings:
- 23.3% of top-scored candidates match human pick (#1)
- 58.8% of human picks fall in top-3 scored
- Score distributions overlap almost completely between picked and rejected
- Tonal distance does NOT predict human preference
- Voice shift is the main blind spot (53 tagged, high scores)
- Duration clustering is a weak but useful rejection signal

## 2. Script Changes

See `docs/session-01-script-changes.md` for full diff.

12 trigger word replacements applied:
- 3 hiss triggers removed from chunk 11 (nostrils, gentle rise, entering)
- 7 echo triggers replaced (feel→sense/notice, simply→just, stillness→quiet/calm)
- 2 trailing ellipsis removed (Fish renders as hesitant)
- 4 triggers remain in 100+ char blocks (safe per Bible Section 13)

## 3. Candidate Generation Stats

- Total chunks: 26
- Total candidates: 735
- Pre-filter failures: 257
- Estimated cost: £0.23
- Generation time: 1905s

## 4. Automated Picker Performance

### Retroactive Validation (10 sessions)

- Exact match: **62/245 (25.3%)**
- Human in auto top-3: **130/245 (53.1%)**

| Session | Exact | % | Top 3 | % |
|---------|-------|---|-------|---|
| 01-morning-meditation | 7/26 | 26.9% | 13/26 | 50.0% |
| 03-breathing-for-anxiety | 10/31 | 32.3% | 14/31 | 45.2% |
| 18-calm-in-three-minutes | 2/12 | 16.7% | 7/12 | 58.3% |
| 23-the-calm-reset | 2/20 | 10.0% | 12/20 | 60.0% |
| 32-observing-emotions | 6/26 | 23.1% | 16/26 | 61.5% |
| 42-seven-day-mindfulness-day5 | 8/22 | 36.4% | 9/22 | 40.9% |
| 52-the-court-of-your-mind | 17/66 | 25.8% | 40/66 | 60.6% |
| 61-21day-mindfulness-day05 | 2/19 | 10.5% | 5/19 | 26.3% |
| 76-21day-mindfulness-day20 | 6/18 | 33.3% | 12/18 | 66.7% |
| narrator-welcome | 2/5 | 40.0% | 2/5 | 40.0% |

## 5. Session 01-morning-meditation — Pick Summary

- Total chunks: 26
- Confidence: high=11, medium=5, low=10
- Flagged for human review: 10

| Chunk | Selected | Quality | Confidence | Eliminated | Remaining |
|-------|----------|---------|------------|------------|-----------|
| c00 | v0 | 1.321 | high | 3 | 37 |
| c01 | v10 | 0.667 | low **FLAG** | 25 | 0 |
| c02 | v3 | 0.934 | medium | 14 | 16 |
| c03 | v18 | 0.831 | low **FLAG** | 21 | 9 |
| c04 | v1 | 1.211 | high | 7 | 18 |
| c05 | v21 | 0.876 | low **FLAG** | 2 | 23 |
| c06 | v13 | 0.511 | low **FLAG** | 22 | 3 |
| c07 | v4 | 0.874 | high | 12 | 18 |
| c08 | v10 | 0.838 | low **FLAG** | 10 | 15 |
| c09 | v12 | 0.962 | medium | 1 | 29 |
| c10 | v11 | 0.778 | high | 34 | 6 |
| c11 | v9 | 0.714 | low **FLAG** | 13 | 17 |
| c12 | v4 | 1.253 | high | 1 | 24 |
| c13 | v5 | 0.706 | high | 15 | 15 |
| c14 | v4 | 0.965 | medium | 4 | 21 |
| c15 | v26 | 0.556 | medium | 19 | 11 |
| c16 | v0 | 0.657 | high | 4 | 21 |
| c17 | v19 | 1.162 | low **FLAG** | 4 | 21 |
| c18 | v12 | 0.689 | low **FLAG** | 3 | 27 |
| c19 | v2 | 0.786 | medium | 10 | 15 |
| c20 | v14 | 0.805 | low **FLAG** | 6 | 19 |
| c21 | v5 | 1.085 | high | 1 | 24 |
| c22 | v14 | 0.664 | low **FLAG** | 9 | 21 |
| c23 | v21 | 0.757 | high | 13 | 12 |
| c24 | v20 | 0.916 | high | 7 | 23 |
| c25 | v23 | 0.676 | high | 10 | 20 |

## 6. QA Gate Results

- Overall: **FAIL**

| Gate | Name | Result |
|------|------|--------|
| 1 | Quality Benchmarks | PASS |
| 10 | Speech Rate | PASS |
| 11 | Silence Integrity | PASS |
| 12 | Duration Accuracy | FAIL |
| 13 | Ambient Continuity | SKIP |
| 2 | Click Artifacts | PASS |
| 3 | Spectral Comparison | PASS |
| 5 | Loudness Consistency | PASS |
| 7 | Volume Surge/Drop | PASS |
| 8 | Repeated Content | PASS |
| 9 | Energy Spike | PASS |

## 7. Conditioning Chain HF Scan

To be run after assembly (Phase 6.2).

## 8. Honest Assessment

### Strengths
- Automated picker matches human pick 25% of the time (baseline)
- Duration outlier filtering eliminates obvious Cut Short failures
- Quality score ranking is the best single predictor available

### Weaknesses
- Voice shift detection is effectively blind (no metric captures it)
- Echo detection is unreliable (58% false negative rate)
- 75% of picks will differ from what Scott would choose
- Low-confidence chunks (where margin between candidates is small) are the most likely to fail

### Prediction
~30% chance the full output passes Scott's listen without requiring re-picks.
The main risk is voice-shifted candidates that score well but sound wrong.

---

*Report generated: 2026-02-12T08:42:28Z*