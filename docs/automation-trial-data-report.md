# Automation Trial — Data Report (Phase 1)

**Date:** 12 February 2026
**Sessions analysed:** 10 (01, 03, 18, 23, 32, 42, 52, 61, 76, narrator-welcome)
**Total chunks:** 245
**Total candidates scored:** 5,108
**Human rejections:** 800

---

## 1. Score Distribution — Picked vs Rejected

| Metric | N | Mean | Std | Median | P25 | P75 | Min | Max |
|--------|---|------|-----|--------|-----|-----|-----|-----|
| **Picked composite** | 245 | 0.674 | 0.544 | 0.611 | 0.480 | 0.769 | 0.102 | 8.282 |
| **Rejected composite** | 790 | 0.692 | 0.660 | 0.614 | 0.504 | 0.762 | 0.045 | 8.836 |
| **Picked quality** | 244 | 0.792 | 0.536 | 0.710 | 0.601 | 0.880 | 0.260 | 8.282 |
| **Rejected quality** | 789 | 0.801 | 0.650 | 0.722 | 0.612 | 0.852 | 0.239 | 8.836 |

**Key finding:** Distributions almost completely overlap. 100% of picked candidates fall within the rejected score range. Scores alone cannot discriminate picked from rejected.

---

## 2. Rank Analysis — How Often Does Score Predict the Human Pick?

| Metric | Value |
|--------|-------|
| #1 scored = human pick | **57/245 (23.3%)** |
| Top 3 scored | **144/245 (58.8%)** |
| Top 5 scored | **185/245 (75.5%)** |
| Bottom half | 19/245 (7.8%) |

**Corrects the debrief estimate:** The debrief said 8% #1 match — that was from a smaller 12-chunk sample. Across all 245 chunks and 10 sessions, **23.3% of top-scored candidates match the human pick**. This is a much stronger baseline than expected.

### Rank distribution

| Rank | Count | % |
|------|-------|---|
| 1 | 57 | 23.3% |
| 2 | 62 | 25.3% |
| 3 | 25 | 10.2% |
| 4 | 25 | 10.2% |
| 5 | 16 | 6.5% |
| 6 | 12 | 4.9% |
| 7 | 9 | 3.7% |
| 8 | 7 | 2.9% |
| 9 | 7 | 2.9% |
| 10 | 9 | 3.7% |
| 11-19 | 16 | 6.5% |

The human pick is **rank 1 or 2 in 48.6%** of cases and **top 5 in 75.5%** — the scoring system is a much better guide than previously believed.

---

## 3. Rejection Reason Tags

Tags available from sessions 42, 61, 76, narrator-welcome (72 tagged rejections total):

| Tag | Count | Mean Score | Median Score | Notes |
|-----|-------|-----------|--------------|-------|
| **Voice** | 53 | 1.395 | 0.799 | Highest scores — voice shift not captured by scoring |
| **Echo** | 15 | 0.988 | 0.417 | Lower scores — echo partially captured |
| **Cut Short** | 3 | 0.321 | 0.315 | Lowest scores — duration-based, easily detectable |
| **Hiss** | 1 | 0.940 | 0.940 | Single sample, high score — hiss not well captured |

**Key finding:** Voice-shifted candidates score **higher than average** (mean 1.395 vs overall 0.692) — the scoring system is blind to voice character shifts. Echo candidates score lower but overlap heavily with acceptable candidates. Cut Short candidates are reliably low-scoring and detectable by duration analysis.

---

## 4. Chunk Position Patterns

| Position | N | Avg Rejection Rate | Avg Picked Score |
|----------|---|-------------------|-----------------|
| Opening (c00) | 10 | 0.104 | 1.624 |
| Early (c01-c02) | 20 | 0.157 | 0.541 |
| Body | 205 | 0.167 | 0.647 |
| Closing | 10 | 0.200 | 0.553 |

Opening chunks have the **lowest rejection rate** (10.4%) but highest picked score (inflated by cold-start score calibration issues per Bible). Closing chunks have the **highest rejection rate** (20%).

---

## 5. Text Length Correlation

| Length | N | Avg Picked Score | Avg Rejection Rate |
|--------|---|-----------------|-------------------|
| <50 chars | 17 | 1.192 | 0.054 |
| 50-100 chars | 94 | 0.720 | 0.163 |
| 100-200 chars | 103 | 0.587 | 0.181 |
| 200+ chars | 31 | 0.540 | 0.177 |

Short chunks (<50 chars) have dramatically lower rejection rates (5.4% vs 16-18% for longer chunks). Longer chunks are harder for Fish and produce more rejects. Scores decrease with length.

---

## 6. Tonal Distance

| Group | N | Mean | Std | Median | P25 | P75 |
|-------|---|------|-----|--------|-----|-----|
| Picked | 234 | 0.0024 | 0.0025 | 0.0016 | 0.0009 | 0.0032 |
| Rejected | 763 | 0.0022 | 0.0018 | 0.0017 | 0.0010 | 0.0029 |

**Key finding:** Tonal distance does NOT predict human preference. Picked and rejected candidates have nearly identical tonal distributions. The 50x tonal penalty in the composite score is actively harmful — it shifts rankings without improving prediction.

---

## 7. Per-Session Accuracy

| Session | Chunks | #1 Match | Top 3 | Top 5 |
|---------|--------|----------|-------|-------|
| 01-morning-meditation | 26 | 31% | 62% | 77% |
| 03-breathing-for-anxiety | 31 | 16% | 42% | 58% |
| 18-calm-in-three-minutes | 12 | 8% | 58% | 83% |
| 23-the-calm-reset | 20 | 30% | 80% | 90% |
| 32-observing-emotions | 26 | 19% | 62% | 77% |
| 42-seven-day-mindfulness-day5 | 22 | 23% | 55% | 68% |
| 52-the-court-of-your-mind | 66 | 27% | 64% | 82% |
| 61-21day-mindfulness-day05 | 19 | 11% | 32% | 58% |
| 76-21day-mindfulness-day20 | 18 | 28% | 72% | 83% |
| narrator-welcome | 5 | 40% | 60% | 80% |

Session 03 and 61 have lowest accuracy — these may have more subtle quality issues that scores miss.

---

## 8. Individual Metric Separation — Picked vs Rejected

| Metric | Picked Mean | Rejected Mean | Separation |
|--------|------------|---------------|-----------|
| echo_risk | 0.0012 | 0.0012 | **None** |
| hiss_risk | -13.91 | -13.69 | Minimal (0.22 dB) |
| sp_contrast | 19.98 | 19.94 | Minimal |
| sp_flatness | 0.0335 | 0.0343 | Minimal |

**No individual metric separates picked from rejected.** The echo_risk metric is indistinguishable between groups. This confirms the Bible's statement that automated scoring has a 58% false negative rate on echo.

---

## 9. Duration Analysis

- **78.8%** of picked candidates are within 10% of the chunk's median duration
- Average distance from median: **10.4%**
- Duration clustering is a weak but usable signal for rejecting extreme outliers

---

## 10. Predictive Power — Single vs Multi-Signal

### Single-metric #1 prediction accuracy

| Metric | #1 Match | % |
|--------|----------|---|
| composite | 57/244 | **23.4%** |
| quality (no tonal penalty) | 53/244 | 21.7% |
| sp_flatness (lowest) | 51/244 | 20.9% |
| hiss_risk (lowest) | 34/244 | 13.9% |
| sp_contrast (highest) | 21/244 | 8.6% |
| echo_risk (lowest) | 17/244 | 7.0% |

### Multi-signal combination

Weighted: quality 40% + echo 30% + contrast 20% + hiss 10% + duration penalty:
- #1 match: **49/244 (20.1%)**
- Top 3: **115/244 (47.1%)**

**Worse than composite alone.** The current composite formula, despite its crudeness, is the best single predictor. Adding more signals with naive weighting introduces noise.

---

## Key Conclusions for Phase 4

1. **Score is a better predictor than believed**: 23% #1, 59% top-3 (not 8%/50% as debrief estimated)
2. **Rejection filtering > ranking**: The path to automation is eliminating failures, not predicting winners
3. **Tonal penalty is counterproductive**: Remove the 50x tonal distance penalty — it adds noise
4. **Voice shift is the blind spot**: 53 tagged rejections, high scores — this is the hardest failure mode to detect
5. **Duration outliers are detectable**: Cut Short candidates reliably score low and have extreme durations
6. **Short chunks are Fish's sweet spot**: <50 chars → 5.4% rejection rate
7. **The automated picker strategy should be**: (a) eliminate definite failures via duration + score thresholds, (b) pick the highest quality-score from remaining candidates, (c) flag low-confidence chunks for human review

---

## Raw Data

Full analysis data: `/tmp/automation-trial-analysis.json`
Raw pick data: `/tmp/automation-trial-raw-data.json`
Individual picks: `/tmp/picks_{session-id}.json` for all 10 sessions
