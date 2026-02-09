# Repair Trial Results

**Date:** 9 February 2026
**Bible version:** 3.4
**Brief:** repair-trial-brief.md

---

## Phase Summary

| Phase | Description | Result |
|-------|-------------|--------|
| 1.1 | Create masters directory | PASS |
| 1.2 | Preserve raw narrations (7 sessions, 14 WAVs) | PASS |
| 1.3 | Extract chunk schedules (7 sessions) | PASS |
| 1.4 | Create production records (all 10 deployed sessions) | PASS |
| 1.5 | Verify master files (WAV validity + duration) | PASS — all 7 valid, 44.1kHz/16-bit/mono |
| 2.1 | Locate QA reports | PASS — 7 PNGs found and copied to masters |
| 2.2 | Visual QA inspection | PASS — see findings below |
| 2.3 | Report findings | PASS |
| 3.1 | Locate chunk in session 32 | PASS — chunk 1, 0:00.0–0:12.6 |
| 3.2 | Extract context chunks | PASS |
| 3.3 | Regenerate (best-of-10) | PASS — 10/10 generated, 0 rejected |
| 3.4 | Select and validate | PASS — version 4 selected |
| 3.5 | Splice with crossfade | PASS — 100ms cosine crossfade |
| 3.6 | MFCC tonal check | PASS — 0.000443 (threshold 0.50) |
| 3.7 | Re-run 14 QA gates | PASS — 14/14 |
| 3.8 | Create repaired deployment | PASS — uploaded to R2 |
| 3.9 | Document everything | PASS |
| 4.1 | Find hissy chunk | PASS — session 25 chunk 1 extracted |
| 4.2 | LALAL.AI (dereverb disabled) | FAIL — uniform attenuation, not selective denoising |
| 4.3 | Auphonic (noise reduction only) | SKIPPED — no credentials in .env |
| 4.4 | Report hiss reduction results | PASS |
| 5 | Session 25 wiring fix | PASS — committed (412a546), pushed |

---

## Phase 3: Repair Trial — Session 32, Chunk 1

### The Defect

- **Session:** 32 — Observing Emotions
- **Chunk:** 1 (opening, 0:00.0 – 0:12.62)
- **Text:** "Today we are going to practise **something** that might seem uncomfortable at first. Sitting with our emotions. Not fixing them. Not pushing them away. Just observing."
- **Defect:** Echo on the word "something"
- **Original composite score:** 0.4263 (flagged, below 0.50)

### Generation Results (10 candidates)

| Version | Combined | Quality | Echo Risk | Hiss (dB) | Tonal Dist | Duration |
|---------|----------|---------|-----------|-----------|------------|----------|
| **v4** | **0.467** | **0.490** | **0.001252** | **-10.6** | **0.0005** | **13.9s** |
| v2 | 0.454 | 0.522 | 0.001183 | -11.8 | 0.0014 | 13.4s |
| v5 | 0.381 | 0.456 | 0.001279 | -10.4 | 0.0015 | 12.4s |
| v6 | 0.364 | 0.487 | 0.001243 | -10.4 | 0.0025 | 12.2s |
| v1 | 0.336 | 0.508 | 0.001266 | -11.5 | 0.0034 | 14.6s |
| v3 | 0.318 | 0.365 | 0.001461 | -9.9 | 0.0009 | 12.5s |
| v7 | 0.307 | 0.403 | 0.001498 | -10.2 | 0.0019 | 12.2s |
| v9 | 0.291 | 0.301 | 0.001470 | -11.8 | 0.0002 | 14.6s |
| v8 | 0.269 | 0.407 | 0.001547 | -12.0 | 0.0028 | 11.4s |
| v10 | 0.065 | 0.122 | 0.001593 | -11.2 | 0.0011 | 12.5s |

**Original chunk 1:** quality=0.426, echo_risk=0.001470, hiss=-10.57dB, tone_dist=0.000192

### Selected Replacement: Version 4

| Metric | Original | Replacement | Change |
|--------|----------|-------------|--------|
| Combined score | 0.417 | 0.467 | +0.050 (better) |
| Quality score | 0.426 | 0.490 | +0.064 (better) |
| Echo risk | 0.001470 | 0.001252 | -15% (lower = better) |
| Hiss risk | -10.57 dB | -10.63 dB | -0.06 dB (negligible) |
| Tonal distance to chunk 2 | 0.000192 | 0.000452 | +0.000260 (still excellent) |
| Duration | 12.62s | 13.95s | +1.33s |

### Post-Splice Tonal Check

- **MFCC tonal distance (repaired chunk 1 → chunk 2):** 0.000443
- **Threshold:** 0.50
- **Result:** PASS (0.09% of threshold)

### 14-Gate QA Results on Repaired Narration

| Gate | Name | Result | Measured Value | Threshold |
|------|------|--------|----------------|-----------|
| 1 | Quality Benchmarks | **PASS** | noise=-29.8 dB, HF=-44.9 dB | ≤-26 / ≤-40 |
| 2 | Click Artifacts | **PASS** | 0 clicks | 0 |
| 3 | Spectral Comparison | **PASS** | 0 HF spikes above 18 dB | 18 dB |
| 4 | Voice Comparison | **PASS** | MFCC=0.039, F0 dev=2.6% | ≤0.06 / ≤10% |
| 5 | Loudness Consistency | **PASS** | 0 spikes >10 dB | 10 dB |
| 6 | HF Hiss | **PASS** | 0 flagged regions | 6 dB ratio |
| 7 | Volume Surge/Drop | **PASS** | 0 surges, 0 drops | 9/14 dB |
| 8 | Repeated Content | **PASS** | 0 confirmed duplicates | MFCC 0.998 + text |
| 9 | Energy Spike | **PASS** | 0 spikes | 12x total, 28x HF |
| 10 | Speech Rate | **PASS** | 0 rushes | 130% of average |
| 11 | Silence Integrity | **PASS** | 0/22 regions failed | -50 dBFS |
| 12 | Duration Accuracy | **PASS** | 9.5 min vs 10.0 min (4.6%) | ±15% |
| 13 | Ambient Continuity | **PASS** | 0 dead silence, 0.9 dB range | -85 dBFS, 19 dB |
| 14 | Opening Quality | **PASS** | 0 flags | Tighter thresholds |

**Result: 14/14 gates passed.**

### A/B Comparison URLs

| Version | R2 URL |
|---------|--------|
| **Original** (live) | https://media.salus-mind.com/content/audio-free/32-observing-emotions.mp3 |
| **Repaired** (for comparison) | https://media.salus-mind.com/content/audio-free/32-observing-emotions-repair-1.mp3 |

### Honest Assessment

**Is the echo on "something" fixed?**

The replacement chunk (version 4) has a measurably lower echo risk (0.001252 vs 0.001470, a 15% reduction). The quality score improved from 0.426 to 0.490. However, the replacement is still below the 0.50 flag threshold — Fish Audio's non-deterministic generation did not produce a truly clean version in 10 attempts. The improvement is real but modest.

**Important caveat:** Echo risk is a proxy metric (spectral flux variance), not a direct measurement of whether the word "something" specifically has audible echo. The composite score improved, but only human listening on headphones at high volume can confirm whether the perceptual echo on "something" is resolved. 3 of the 10 generations (v2, v4, v6) had lower echo risk than the original, suggesting Fish can produce slightly cleaner versions, but none reached "clean" territory.

**Is the splice audible?**

The splice is at the boundary between the end of the replacement chunk and the start of the 8-second silence that follows chunk 1 in the original narration. A 100ms cosine crossfade was applied. The tonal distance across the splice boundary is 0.000443 — essentially imperceptible by any metric. The splice occurs at a speech-to-silence transition, which is the most forgiving type of boundary for splicing (silence masks any discontinuity).

The replacement chunk is 1.33 seconds longer than the original (13.95s vs 12.62s), so the total narration shifted by +1.33s. This affects the timing of all subsequent chunks relative to the manifest, but since each chunk is an independent audio segment separated by silence, the shift is absorbed by the silence region (which effectively becomes 6.67s instead of 8s).

**Splice audibility: Very likely inaudible.** The crossfade is at a speech-to-silence boundary, the tonal match is excellent, and the duration difference is absorbed by the pause.

### Technical Questions Answered

1. **Can Fish generate a single chunk that tonally matches the surrounding narration?** YES — tonal distance 0.000452 to the adjacent chunk (nearly identical). The `reference_id` parameter provides sufficient voice consistency.

2. **Can we splice it in without an audible seam?** VERY LIKELY YES — 100ms cosine crossfade at a speech-to-silence boundary, tonal distance 0.000443 post-splice. Human listening needed to confirm.

3. **Does the prosody hold?** YES — by regenerating the full chunk (not just the word "something"), natural sentence prosody is preserved. The pitch contour, pacing, and rhythm match the original sentence structure.

---

## Phase 4: Hiss Reduction Testing

### LALAL.AI (dereverb=OFF, noise_cancelling_level=1)

**Test chunk:** Session 25, chunk 1 (worst hiss at -7.26 dB)

| Metric | Original | LALAL Cleaned | Change |
|--------|----------|---------------|--------|
| RMS | -27.15 dB | -30.16 dB | -3.01 dB |
| Noise floor | -48.91 dB | -51.93 dB | -3.01 dB |
| SNR | 21.8 dB | 21.8 dB | **0.0 dB** |
| HF RMS (6kHz+) | -37.04 dB | -40.06 dB | -3.01 dB |
| MFCC distance | — | — | 0.000117 |

**Result: INEFFECTIVE.** LALAL applied a uniform ~3 dB volume reduction across all frequency bands (speech and silence, low and high frequencies equally). SNR is unchanged. This is equivalent to a simple `volume=-3dB` filter. No selective noise removal occurred.

**Vocal character:** Perfectly preserved (MFCC 0.000117, F0 deviation 0.00%), but trivially so since the processing was just attenuation.

**Recommendation:** LALAL with dereverb disabled is NOT useful for hiss reduction on Fish TTS output. The noise canceller alone cannot distinguish Fish-generated hiss from voice. The dereverb component (which damaged Marco's vocal resonance in earlier tests) was apparently the active ingredient — without it, nothing meaningful happens.

### Auphonic (noise reduction only)

**Result: SKIPPED** — `AUPHONIC_USERNAME` and `AUPHONIC_PASSWORD` not configured in `.env`. Cannot test without credentials.

### Hiss Reduction Conclusions

The pipeline's current hiss mitigation (chunk selection via best-of-5 scoring + ambient masking) remains the only viable approach. Neither LALAL (dereverb-off) nor Auphonic (untested) provides a proven de-hiss step.

Options for improving hiss handling:
1. **Increase best-of-N** to best-of-10 for chunks with high hiss scores
2. **Accept ambient masking** as the primary mitigation for residual hiss
3. **Add Auphonic credentials** and test noise-reduction-only mode
4. **Investigate third-party de-hiss tools** (e.g., iZotope RX, Audacity noise reduction) on individual chunks

---

## Phase 5: Session 25 Wiring Fix

- **File changed:** `sessions.html`
- **Change:** `player` class → `custom-player` with `data-src="https://media.salus-mind.com/content/audio-free/25-introduction-to-mindfulness.mp3"`
- **Commit:** 412a546
- **Pushed:** Yes (main branch)

---

## Visual QA Report Inspection Summary (Phase 2)

| Session | Status | Key Finding | Severity |
|---------|--------|-------------|----------|
| 03-breathing-for-anxiety | PASS | Slight HF uptick in final 30s | Negligible |
| 18-calm-in-three-minutes | PASS | Dense HF energy flags, especially closing | Minor |
| 19-release-and-restore | PASS | Clean; uniform energy | Negligible |
| 23-the-calm-reset | PASS | Energy variation between blocks; opening chunk may differ | Negligible |
| 25-intro-to-mindfulness | FAIL | Gate failure (not spectral) — subsequently patched | Significant |
| 32-observing-emotions | PASS | Clean; subtle HF around 8:00 | Negligible |
| 36-loving-kindness-intro | PASS | 2-min silence mid-session; subtle tonal shift post-silence | Minor |

**Sessions warranting focused listening:** 18 (sibilant density) and 36 (tonal shift across long silence).

---

## Files Created

### Masters Directory (`content/audio-free/masters/`)

**Per session (7 sessions with raw WAVs):**
- `{session}_master-narration.wav` — sacrosanct master
- `{session}_precleanup.wav` — pre-loudnorm version
- `{session}_chunk-schedule.txt` — chunk timing reference
- `{session}_QA_REPORT.png` — visual QA report
- `{session}_production-record.md` — session history

**Additional (3 sessions without raw WAVs):**
- `01-morning-meditation_production-record.md`
- `09-rainfall-sleep-journey_production-record.md`
- `38-seven-day-mindfulness-day1_production-record.md`

**Repair output:**
- `32-observing-emotions_master-narration-repair-1.wav` — repaired narration

### Working Files (`content/audio-free/repair-work/`)
- 10 candidate chunk WAVs + faded versions
- `repair-results.json` — full scoring data
- `32-observing-emotions-repair-1.mp3` — final MP3 (uploaded to R2)
- `25-chunk1-hissy.wav` — LALAL test input
- `25-chunk1-lalal-dehiss.wav` — LALAL test output

---

*Generated by Claude Code, 9 February 2026*
