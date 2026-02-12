# Automation Trial — State File

**Brief:** automation-trial-brief.md (ACTIVE, 12 Feb 2026)
**Session:** 01-morning-meditation

## Phase Status

| Phase | Status | Started | Notes |
|-------|--------|---------|-------|
| 1 — Data Harvest | COMPLETE | 12 Feb 2026 | 245 chunks across 10 sessions analysed |
| 2 — Script Fix | COMPLETE | 12 Feb 2026 | 12 trigger words replaced, 0 at-risk remaining |
| 3 — Candidate Generation | COMPLETE | 12 Feb 2026 | 735 candidates, 257 filtered (34.9%), 478 viable |
| 4 — Automated Picker | COMPLETE | 12 Feb 2026 | 26/26 picked, 11 high / 5 medium / 10 low confidence |
| 5 — Assembly | COMPLETE | 12 Feb 2026 | 13.5 min (812.5s), 26 chunks + pauses, no ambient |
| 6 — Post-Assembly QA | COMPLETE | 12 Feb 2026 | 9/10 PASS, 1 FAIL (Gate 12: duration mismatch), 1 SKIP |
| 7 — Upload + Results | COMPLETE | 12 Feb 2026 | R2 uploaded, report generated, email sent |

## Phase 1 Metrics
- Sessions collected: 10/10
- Total chunks: 245, Total candidates: 5,108
- Score #1 match rate: 23.3%
- Top-3 match rate: 58.8%
- Key finding: composite score is best single predictor; tonal penalty counterproductive
- Report: `docs/automation-trial-data-report.md`

## Phase 2 Metrics
- Trigger words found: 15 chunks affected
- Chunks rewritten: 12 changes (3 hiss, 7 echo, 2 ellipsis)
- At-risk triggers remaining: 0 (4 safe in 100+ char blocks)
- Diff log: `docs/session-01-script-changes.md`

## Phase 3 Metrics
- Chunks: 26
- Candidates per chunk: 25-40 (--extra 10)
- Total generated: 735
- Filtered below 0.30: 257 (34.9%)
- Viable candidates: 478
- Chunk 0 conditioning: session 42 c04_v19 (deployed reference, not marco-master)
- Generation time: 1905s (~32 min)
- Estimated cost: £0.23

## Phase 4 Metrics
- Retroactive accuracy (10 sessions): **25.3% exact match, 53.1% in top-3**
- Per-session range: 10.0% (session 23) to 40.0% (narrator-welcome)
- Session 01 (pre-fix candidates): 26.9% exact, 50.0% top-3
- Fresh candidates: 0% exact match (expected — different candidate pool)
- Confidence breakdown: 11 high, 5 medium, 10 low
- Flagged for human review: 10/26 chunks
- Tools built: auto-picker.py, auto-picker-report.py, auto-picker-compare.py
- Validation: `docs/auto-picker-validation.json`

## Phase 5 Metrics
- Assembly duration: 812.5s (13.5 min)
- Chunks assembled: 26/26
- Ambient: none (voice-only assembly for trial)
- Total silence: 596.0s (9.9 min) across 25 pauses

## Phase 6 Metrics
- Gates passed: 9/10 (1 skipped)
- Gate 12 FAIL: 13.5 min vs 25.0 min Duration-Target (45.8% deviation)
  - NOTE: Script header says 25 min but content only generates 13.5 min — pre-existing mismatch
- All other gates PASS: Quality, Clicks, Spectral, Loudness, Surge, Repeat, Speech Rate, Silence, Energy
- Gate 13 SKIP: Ambient Continuity (no ambient mixed)
- QA report: `content/audio-free/vault/01-morning-meditation/final/01-morning-meditation-build-report.json`

## Phase 7 Metrics
- R2 upload: `content/audio-free/01-morning-meditation-auto-trial.mp3`
- R2 URL: `https://media.salus-mind.com/content/audio-free/01-morning-meditation-auto-trial.mp3`
- Results report: `docs/session-01-auto-trial-RESULTS.md`
- Email sent: yes
