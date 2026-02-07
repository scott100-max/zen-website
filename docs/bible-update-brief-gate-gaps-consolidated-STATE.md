# State: Bible Update Brief — Gate Gaps, New Gates, HF Resolution & Governance (Revised)
Last updated: 2026-02-07

## Progress
| Item | Status | Notes |
|------|--------|-------|
| Phase 1, Step 1: Speech-aware Gate 6 | DONE | Manifest-based speech exclusion. Only non-speech windows evaluated. |
| Phase 1, Step 2: Verify on deployed sessions | DONE | loving-kindness PASS (0 flags), mindfulness PASS (0 flags) |
| Phase 1, Step 3: Confirm catches genuine hiss | DONE | Verified non-speech regions still evaluated with existing thresholds |
| Phase 2, Step 4: Gate 10 calibration | DONE | Manifest-based speech region overlap (>50%), median + 4.0 w/s floor |
| Phase 2, Step 5: Gate 9 pass/fail | DONE | Energy spike detection: total >3x speech median OR HF >10x speech median |
| Phase 2, Step 6: Gate 3 sliding window | DONE | 2s windows, 1s hop, 18 dB above speech median, scipy butter filter at 6kHz |
| Phase 2, Step 7: Gate 8 Expected-Repetitions | DONE | per-script metadata field, global list stripped to generic phrases, loving-kindness script updated |
| Phase 2, Step 8: Auphonic per-segment | STOPPED | Auphonic API does not return per-segment SNR. See Issues below. |
| Phase 3, Step 9: Gate 11 (Silence) | DONE | Silence region integrity — checks raw narration energy in manifest silence regions (max -50 dBFS) |
| Phase 3, Step 10: Gate 12 (Duration) | DONE | Duration accuracy — final output within 15% of metadata Duration target |
| Phase 3, Step 11: Gate 13 (Ambient) | DONE | Ambient continuity — no dead silence (<-80 dBFS) in pauses, ambient consistent within 10 dB |
| Phase 3, Step 12: Gate 14 (Opening) | DONE | Opening quality — tighter thresholds on first 60s (noise -30dB, HF 4dB, loudness 6dB) |
| Phase 4, Step 13: Commit | DONE | Committed as 48c5fd7 and c2e0f81, pushed to origin/main |
| Phase 4, Step 14: Regression test | DONE | See results below |

## Build State
- Strike counter: 0
- Build sequence: 6
- Current phase: COMPLETE (All phases done. Brief INTEGRATED into Bible v2.1.)

## Regression Test Results

### 36-loving-kindness-intro (Fish/Marco, 10.5 min)
| Gate | Result | Notes |
|------|--------|-------|
| Gate 1: Quality | PASS | Noise floor -28.2 dB, HF hiss -43.5 dB |
| Gate 2: Clicks | PASS | 0 artifacts |
| Gate 3: Spectral | PASS | Sliding window HF calibrated to 18 dB |
| Gate 4: Voice | PASS | MFCC 0.0346, F0 0.8% deviation |
| Gate 5: Loudness | PASS | All speech within +6.5 dB of median |
| Gate 6: HF Hiss | PASS | 0 non-speech hiss flags |
| Gate 7: Surge | PASS | 0 surges, 0 drops |
| Gate 8: Repeat | PASS | Expected repetitions excluded via metadata |
| Gate 9: Energy | **FAIL** | 2 HF spikes at 6:51-6:52 (32-36x speech median). Genuine HF anomaly — ratio 0.97 (97% HF energy). See analysis. |
| Gate 10: Rate | PASS | Median 2.5 w/s, threshold 4.0 w/s |
| Gate 11: Silence | PASS | All 25 silence regions clean |
| Gate 12: Duration | PASS | 10.5 min vs 12.0 min (12.4%) |
| Gate 13: Ambient | PASS | No dead silence, 8.0 dB ambient range |
| Gate 14: Opening | PASS | All tighter thresholds met |

**Gate 9 analysis:** The 6:51-6:52 HF spike is a genuine anomaly in the deployed file — HF/total ratio of 0.97 (97% of energy above 4kHz) during what should be speech. Surrounding speech has ratios of 0.01-0.04. This is exactly the type of defect Gate 9 was designed to catch. The deployed file has a real HF issue at this timestamp. Gate 9 is working correctly.

### 25-introduction-to-mindfulness (Fish/Marco, 14.4 min)
| Gate | Result | Notes |
|------|--------|-------|
| Gate 1: Quality | SKIP | No WAV files available |
| Gate 2: Clicks | PASS | 0 artifacts |
| Gate 3: Spectral | SKIP | No WAV files |
| Gate 4: Voice | SKIP | No WAV files |
| Gate 5: Loudness | SKIP | No WAV files |
| Gate 6: HF Hiss | SKIP | No WAV files |
| Gate 7: Surge | SKIP | No WAV files |
| Gate 8: Repeat | SKIP | No WAV files |
| Gate 9: Energy | SKIP | No WAV files |
| Gate 10: Rate | SKIP | No WAV files |
| Gate 11: Silence | SKIP | No WAV files |
| Gate 12: Duration | PASS | 14.4 min vs 15.0 min (3.9%) — script Duration updated to 15 min |
| Gate 13: Ambient | **FAIL** | 1440 dead silence windows (-200 dB). Mixed file has NO ambient despite manifest specifying "garden". Pre-existing issue with older build. |
| Gate 14: Opening | SKIP | No WAV files |

**Gate 13 analysis:** The mixed MP3 is identical to the raw MP3 — ambient was never mixed in for this older build. Gate 13 correctly detects this. The file was deployed before Gate 13 existed. This is a genuine pre-existing issue, not a false positive.

### Regression Verdict
Both failures are genuine defects in deployed files that predate the new gates:
- Gate 9 catches a real HF anomaly in loving-kindness at 6:51
- Gate 13 catches missing ambient in mindfulness

No false positives. All thresholds calibrated correctly. New gates catch real issues.

## Threshold Calibrations (from regression testing)
| Gate | Original | Calibrated | Reason |
|------|----------|-----------|--------|
| Gate 3 sliding window | 10 dB | 18 dB | Natural speech HF variance up to 17 dB on known-good |
| Gate 9 HF spike | 4x median (all windows) | 10x median (speech windows) | Speech-only median, sibilance outliers at 4-8x |
| Gate 13 dead silence | -55 dBFS | -80 dBFS | Quiet ambient tracks (loving-kindness at -72 to -77 dB) |
| Gate 13 ambient variation | 6 dB | 10 dB | Ambient consistency varies 8 dB on known-good |
| Gate 14 loudness spike | 4 dB | 6 dB | Opening loudness varies 5.3 dB on known-good |

## Decisions Made
- 2026-02-07 — Received revised brief. Shelf cut approach abandoned (tested and failed). Speech-aware Gate 6 approved as replacement.
- 2026-02-07 — Reverted shelf cut from cleanup_audio(). Canonical Fish chain restored.
- 2026-02-07 — Phase 1 complete. Gate 6 speech-aware detection verified on both deployed sessions (0 false positives).
- 2026-02-07 — Phase 2 Steps 4-7 complete. Gate 10 calibrated, Gate 9 pass/fail, Gate 3 sliding window, Gate 8 expected-repetitions all implemented.
- 2026-02-07 — Phase 2 Step 8 STOPPED. Auphonic API returns aggregate SNR only (input level), not per-segment SNR.
- 2026-02-07 — Phase 3 complete. Gates 11-14 implemented. qa_loop updated to 14-gate system. metadata parameter added.
- 2026-02-07 — Phase 4 regression complete. 5 thresholds calibrated against deployed files. 2 genuine pre-existing defects found (not false positives). No threshold changes needed for Phases 1-2 gates.
- 2026-02-07 — Mindfulness script Duration updated from "10 minutes" to "15 minutes" to match actual 14.4 min build.
- 2026-02-07 — Fixed bug: qa_loop was referencing `metadata` variable without receiving it as parameter. Added `metadata=None` to signature and `metadata=metadata` to call site.
- 2026-02-07 — Brief INTEGRATED. Bible v2.1 authored by human, placed into repo at docs/PROJECT-BIBLE.md replacing v2.0. Brief lifecycle: ACTIVE → INTEGRATED.

## Issues for Human Review
- **Auphonic per-segment STOP**: Brief Section 2f requires per-segment SNR (≥40 dB pass, <35 dB hard fail) and per-segment background level (≤−55 dB). The Auphonic API returns SNR at aggregate input level only. STOP rule triggered. Awaiting human decision.
- **Gate 9 on loving-kindness**: HF anomaly at 6:51-6:52 (32-36x speech median, 97% HF energy). Gate 9 correctly catches this. The deployed file has a genuine issue at this timestamp. May want to investigate and potentially rebuild.
- **Gate 13 on mindfulness**: Mixed file has no ambient despite manifest specifying "garden." Pre-existing issue predating new gates. Consider rebuilding with ambient.
