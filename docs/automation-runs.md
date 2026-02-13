# Automation Trial — Run Log

| Run | Date | Session | Chunks | Auto-pick accuracy vs human | Labelled data size | Notes |
|-----|------|---------|--------|---------------------------|-------------------|-------|
| 1   | 12 Feb 2026 | 01-morning-meditation | 26 | Retro: 25.3% exact, 53.1% top-3 | 10 sessions, 245 chunks | Baseline — 9/10 QA gates pass, Gate 12 duration mismatch |

---

## Gate 15: Post-Deploy Live Audio Scanner

**Implemented:** 13 Feb 2026
**File:** `tools/gate15-post-deploy.py`
**Integration:** Auto-runs from `tools/r2-upload.sh` after every MP3 deploy (non-blocking)
**Bible ref:** L-35 CRITICAL (Section 12)

### 7 Checks

| # | Check | Threshold | Method |
|---|-------|-----------|--------|
| 1 | Catastrophic Silence | < -80 dBFS in speech region | 5s windowed RMS |
| 2 | Volume Explosion | > -1 dBFS peak | 5s windowed peak |
| 3 | Voice Breakdown | Centroid <500Hz or >6kHz for >3s | 1s spectral centroid (numpy FFT) |
| 4 | Duration Sanity | >30% deviation | Total vs --duration-min |
| 5 | Hiss Cascade | HF > -36dB for 3+ consecutive 10s windows | Butterworth 4kHz HP |
| 6 | Ambient Pre-Roll | Voice in first 25s | 1s RMS windows, speech > -35 dBFS |
| 7 | Ambient Fade-Out | Final 2s louder than preceding 6s | RMS comparison |

### Threshold Calibration Notes

- **Check 1** adjusted from Bible spec -60 dBFS to -80 dBFS. At -60, every meditation pause with ambient underneath triggers (48 false positives on session 03). True catastrophic silence (codec failures, missing chunks) is near-digital-zero, well below -80 dBFS. Ambient-level gaps (-55 to -70 dB) are normal meditation design.

### Validation Results (13 Feb 2026)

| Session | Checks 1-5,7 | Check 6 (Pre-Roll) | Notes |
|---------|---------------|---------------------|-------|
| 03-breathing-for-anxiety | All PASS | FAIL — voice at 0s | No pre-roll (predates requirement) |
| 01-morning-meditation | All PASS | FAIL — voice at 19s | L-38: 10s fade-in instead of 30s |
| 38-seven-day-mindfulness-day1 | All PASS | FAIL — voice at 0s | No pre-roll (v8 deploy without ambient remix) |

**Finding:** All 3 tested sessions fail Check 6. L-38 scope may be wider than the 3 sessions listed (01, 09, 53) — session 38 (v8 automation deploy) also lacks the 30s structural pre-roll. Every deployed session likely needs ambient remix before Check 6 can pass.
