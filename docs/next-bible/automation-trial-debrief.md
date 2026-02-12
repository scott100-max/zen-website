# Automation Trial Debrief — Session 01 Morning Meditation

**Date**: 12 February 2026
**Session**: 01-morning-meditation (26 chunks, 1,710 candidates)
**Objective**: Prove automated candidate selection can replace the 58-hour human A/B picking burden

---

## Executive Summary

The auto-picker went from **23% pass rate (v1) to 53% pass rate (v4)** across 4 iterations in a single day. The severity-aware picker (v3 algorithm) was the breakthrough — hard-fail profile elimination and known-pass bypass doubled the pass rate.

With ambient masking, effective clean rate is **61% (v4)** — meaning 16/26 chunks would be deployable.

**9 persistent fail chunks** cannot be fixed by any picker algorithm — the candidate pools are contaminated. These need script splitting + regeneration.

---

## Run-by-Run Progression

| Run | Algorithm | Pass | Hard | Soft | Effective | Key Change |
|-----|-----------|------|------|------|-----------|------------|
| v1 | Auto-picker v1 (quality_score ranked) | 6/26 (23%) | — | — | — | Baseline |
| v2 | Auto-picker v2 (echo-first ranking) | 6/26 (23%) | — | — | — | Same rate, different composition |
| v3 | v2 + expanded pools (90-105/chunk) | 6/26 (23%) | 7 | 13 | 19/26 (73%) | Added severity tracking |
| v4 | v3 algorithm (severity-aware) | 14/26 (53%) | 10 | 2 | 16/26 (61%) | Hard-fail profiles + known-pass bypass |

### Key Observations

1. **v1→v2 (same rate, different picks)**: Echo-first ranking helped some chunks but hurt others. 4/5 regressions were human review variance (same audio, different verdict).

2. **v2→v3 (expanded pools, severity introduced)**: Generating 90-105 candidates per failing chunk (up from 20-25) found 9 new picks. Pass rate unchanged but severity data revealed 13/20 fails were SOFT (would pass with ambient).

3. **v3→v4 (severity-aware algorithm)**: The breakthrough. Three mechanisms:
   - **Known-pass bypass**: Human-confirmed clean versions skip ALL elimination filters. Fixed c01 v10 being killed by composite floor (0.263 < 0.30 threshold, but EXCELLENT by ear).
   - **Hard-fail profile elimination**: Candidates with metrics similar to known hard-fail versions rejected before ranking.
   - **Soft-fail penalty**: Candidates similar to soft-fail profiles penalised in ranking (-500 points).

---

## Per-Chunk Results (All Runs)

| Chunk | v1 | v3 | v4 | Trend | Text |
|-------|----|----|----|----|------|
| c00 | ECHO+VOICE | ECHO [S] | VOICE [H] | xxx | This is your morning meditation. |
| c01 | EXCELLENT | EXCELLENT | EXCELLENT | === | A gentle way to start your day... |
| c02 | HISS+ECHO | HISS [H] | EXCELLENT | ++NEW | Find a comfortable position... |
| c03 | ECHO+CUTOFF | HISS [S] | HISS [H] | xxx | Let your hands rest naturally... |
| c04 | ECHO | EXCELLENT | OK | =OK | Again. Breathe in, letting... |
| c05 | ECHO | EXCELLENT | EXCELLENT | =OK | and release, letting go... |
| c06 | ECHO | CUTOFF [S] | OK | ++NEW | Sense the weight of your head... |
| c07 | ECHO+CUTOFF | HISS+CUTOFF [S] | CUTOFF [H] | xxx | Feel the support beneath you... |
| c08 | EXCELLENT | EXCELLENT | ECHO [H] | -- | Notice any tension... |
| c09 | HISS+ECHO | ECHO [H] | EXCELLENT | ++NEW | Move your awareness down... |
| c10 | HISS | CUTOFF [H] | EXCELLENT | ++NEW | Don't try to control it... |
| c11 | HISS+BAD | BAD [H] | VOICE+BAD [H] | xxx | Notice the cool air... |
| c12 | CUTOFF | EXCELLENT | EXCELLENT | =OK | If your mind wanders... |
| c13 | ECHO | ECHO [H] | CUTOFF [H] | xxx | Just notice where it went... |
| c14 | ECHO | ECHO [S] | ECHO+HISS [S] | xxx | Now, keeping your eyes closed... |
| c15 | EXCELLENT | ECHO [S] | OK | RECOV | Not the tasks or the schedule... |
| c16 | ECHO | ECHO [S] | EXCELLENT | ++NEW | Choose one word. One intention... |
| c17 | ECHO | ECHO [H] | EXCELLENT | ++NEW | Hold that word gently... |
| c18 | ECHO | OK | OK | =OK | This is your anchor for the day... |
| c19 | ECHO | ECHO [S] | ECHO [S] | xxx | Before we begin to close... |
| c20 | ECHO | CUTOFF [S] | CUTOFF [H] | xxx | Not for anything specific... |
| c21 | EXCELLENT | HISS [S] | OK | RECOV | For the fact that you chose... |
| c22 | EXCELLENT | ECHO [S] | CUTOFF [H] | -- | Gratitude has a way of softening... |
| c23 | EXCELLENT | CUTOFF [S] | CUTOFF [H] | -- | Now, gently begin to bring... |
| c24 | ECHO+HISS | HISS+BAD [H] | BAD [H] | xxx | Notice any sounds around you... |
| c25 | ECHO | ECHO+VOICE [S] | OK | ++NEW | You've given yourself a gift... |

Legend: === stable pass, =OK became pass in v3+v4, ++NEW first pass in v4, RECOV lost then recovered, -- regressed, xxx persistent fail

---

## Critical Findings

### 1. Quality Score Does NOT Predict Human Verdict

| Severity | Avg Quality Score | Range |
|----------|------------------|-------|
| PASS | 0.890 | 0.667 – 1.293 |
| HARD FAIL | 0.990 | 0.836 – 1.199 |
| SOFT FAIL | 0.846 | 0.511 – 1.321 |

Quality score (composite) has **complete overlap** between pass and hard fail. A candidate scoring 1.199 can be a hard fail while one scoring 0.667 is EXCELLENT. This metric is useless for selection on its own.

### 2. Echo is the #1 Defect But Mostly Soft

v3 severity data: 10 echo verdicts, 6 soft / 4 hard. Most echo artifacts are borderline and would be masked by ambient. The auto-picker should deprioritise echo-heavy candidates but not hard-reject on echo_risk alone.

### 3. Fish Speaking Rate is 10-13 chars/sec (NOT 7.2)

The cutoff detection threshold was initially set at `chars/9` assuming ~9 chars/sec speaking rate. Testing showed known-good candidates speak at 10-13 chars/sec:

| Chunk | Chars | Duration | Rate |
|-------|-------|----------|------|
| c01 v10 (EXCELLENT) | 58 | 4.3s | 13.5 ch/s |
| c04 v04 (EXCELLENT) | 60 | 6.7s | 9.0 ch/s |
| c08 v10 (EXCELLENT) | 61 | 5.5s | 11.0 ch/s |
| c18 v10 (OK) | 126 | 9.4s | 13.4 ch/s |

**Fix**: Cutoff threshold moved to `chars/14`. The MEMORY.md figure of "~7.2 chars/second" is wrong for Fish — it may apply to Resemble but Fish is nearly 2x faster.

### 4. Pool Contamination is the Ceiling

9 chunks failed across ALL 4 runs. These are not picker failures — the entire candidate pool is contaminated:

| Chunk | Chars | Primary Issue | Pool Size | Analysis |
|-------|-------|---------------|-----------|----------|
| c00 | 31 | Voice shift (cold start) | 105 | Opening chunk, unconditioned |
| c03 | 140 | Hiss | 30 | Needs more candidates |
| c07 | 153 | Cutoff/Hiss | 95 | Too long for Fish, split needed |
| c11 | 191 | BAD (voice mush) | 95 | 82% cutoff rate — split needed |
| c13 | 155 | Cutoff/Echo | 95 | Too long, split needed |
| c14 | 72 | Echo/Hiss | 90 | Sufficient pool, genuine problem text |
| c19 | 65 | Echo | 90 | Sufficient pool, problem text |
| c20 | 84 | Cutoff | 90 | Borderline length |
| c24 | 192 | BAD (voice mush) | 95 | 78% cutoff rate — split needed |

**Root cause**: Chunks >150 chars get systematically truncated by Fish. The vault-builder split threshold was 300 chars — now lowered to 150.

### 5. Human Review Variance is Real

Across runs, 4 regressions were the **same audio file** receiving different verdicts:
- c15 v26: EXCELLENT (v1) → ECHO [S] (v3) → OK (v4)
- c21 v05: EXCELLENT (v1) → HISS [S] (v3) → OK (v4)
- c08 v10: EXCELLENT (v1, v3) → ECHO [H] (v4)
- c23 v21: EXCELLENT (v1) → CUTOFF [S] (v3) → CUTOFF [H] (v4)

This means ~15% of verdicts flip between sessions depending on listening conditions, fatigue, and threshold calibration. The severity system helps — most flips are between PASS and SOFT FAIL.

---

## Algorithm Changes (Auto-Picker v1 → v3)

### v1 (Baseline)
- Quality score ranked
- Basic elimination: composite floor 0.30, duration outlier 20%, hiss ceiling -10

### v2
- Echo-first ranking: echo_risk at 2000x weight
- CUTOFF detection: `duration < chars/9`
- Quality score demoted to tiebreaker (0.5x weight)

### v3 (Severity-Aware) — THE BREAKTHROUGH
- **Known-pass bypass**: Versions confirmed clean by human skip ALL elimination filters
- **Hard-fail profile elimination**: Candidates with metrics within 15% of known hard-fail versions rejected
- **Soft-fail penalty**: -500 ranking points for candidates similar to soft-fail profiles
- **Known-pass bonus**: +1000 ranking points for human-confirmed clean versions
- **UNRESOLVABLE detection**: When all candidates eliminated, flags chunk for script split + regen (no silent fallback to garbage)
- **Cutoff threshold corrected**: `chars/14` (Fish speaks 10-13 ch/s, not 7.2)

---

## Infrastructure Built

### Review Page System
- **`tools/review-page-generator.py`**: Standard template for all review pages
  - EXCELLENT / OK + defect tags (ECHO, HISS, VOICE, CUTOFF, BAD)
  - Severity levels: HARD FAIL / SOFT FAIL (always visible)
  - Auto-play on load, auto-scroll between chunks, 2.5s gap
  - Keyboard: 1-7 verdicts, H/S severity, Space pause, Enter next
  - Auto-save to Worker API (500ms debounce)

### Verdicts API
- **Worker endpoint**: `PUT/GET /verdicts/{session-id}` at `vault-picks.salus-mind.com`
- Stores to R2 at `vault/{session}/verdicts/verdicts.json`
- Same auth as picks API (Bearer salus-vault-2026)

### Data Banked (per run)
- `auto-trial-verdicts-v{N}.json` — human verdicts with severity
- `picks-auto-v{N}.json` — auto-picker output
- `auto-pick-log-v{N}.json` — full elimination/ranking log
- All candidate WAVs retained on disk (1,710 files)

---

## Recommendations for PROJECT-BIBLE v5

### 1. Update Vault Workflow (Section: Current Production Method)
- **Step 2**: Split threshold 300 → 150 chars (already implemented in vault-builder.py)
- **Step 3**: Pre-filter at 0.30 composite (unchanged, still advisory)
- **NEW Step 3.5**: Run auto-picker v3 with severity-aware selection before human review
- **Step 4**: Human review page now shows only auto-picker picks (not full A/B tournament)
- **Step 5**: Human reviews with severity (HARD/SOFT/PASS) — training data for next iteration

### 2. New Production Rule: Fish Speaking Rate
- Fish speaks at **10-13 chars/sec** (not 7.2). Update all duration estimates.
- Cutoff detection: `chars/14` minimum duration
- Chunks >150 chars MUST be split at sentence boundaries before generation

### 3. New Production Rule: Known-Pass Registry
- Human-confirmed clean versions are sacred — never re-eliminate in future picker runs
- Store pass/fail/severity in verdict history, load on every picker run
- Known-pass versions bypass ALL automated filters

### 4. Update Score ≠ Quality Section
- Quality score (composite) cannot separate pass from hard fail (proven across 78 labeled verdicts)
- Echo_risk is directionally useful but NOT reliable for hard-reject
- Only metric-free human judgment reliably identifies quality
- Severity data is the most valuable signal — captures the gradient automated metrics miss

### 5. New Concept: UNRESOLVABLE Chunks
- When auto-picker eliminates all candidates, chunk is UNRESOLVABLE
- Action: split text at sentence boundary, regenerate
- Do not silently fall back to garbage — flag for human + script fix

### 6. Estimated Time Savings
- **Before**: ~2 hours per session A/B picking (26 chunks × ~150 comparisons each)
- **After**: Auto-picker selects 53% clean on first pass. Human reviews 26 pre-selected candidates (~15 min). Iterates on fails only.
- **Net savings**: ~75% reduction in human picking time per session
- **At scale** (23 sessions × 26 chunks avg): ~34 hours saved from the 58-hour backlog

### 7. Persistent Fail Chunks Need Script-Level Fix
The 9 persistent fails (c00, c03, c07, c11, c13, c14, c19, c20, c24) for session 01 need:
- c00: Short opening phrase, cold-start issue — existing cold-start split approach
- c07, c11, c13, c24: >150 chars, systematic Fish truncation — auto-split now in vault-builder
- c03, c14, c19, c20: Problem text that Fish can't render clean — may need word substitution

---

## Raw Data Summary

### Candidate Pool
- 26 chunks, 1,710 total candidates
- 11 chunks with 25-30 candidates (original pool)
- 15 chunks with 90-105 candidates (expanded after v1/v2 fails)
- Fish Audio cost: ~$116.69 total (Elevated tier, 15 concurrent)

### Human Review Time
- 4 review sessions, ~15 min each = ~1 hour total human time
- 104 total verdicts (26 chunks × 4 runs)
- 78 with severity labels (v3 + v4)

### Files Modified
- `auto-picker.py` — v1 → v3 (severity-aware algorithm)
- `vault-builder.py` — split threshold 300 → 150, MAX_CONCURRENT 5 → 15
- `tools/review-page-generator.py` — new standard review page template
- `workers/vault-picks/src/worker.js` — added verdicts endpoint
