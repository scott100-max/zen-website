# Brief: Repair Trial

**Status:** ACTIVE
**Issued:** 9 February 2026
**Issued by:** Scott (via Claude Desktop)
**Bible version:** 3.4

---

## Purpose

This brief directs you to trial the targeted chunk repair process described in Bible Section 15A. The goal is to prove that a single defective word can be repaired in an existing deployed session without regenerating the entire narration. If this trial succeeds, targeted repair becomes a standard part of the production pipeline.

---

## Context: Known Flagged Chunks

For reference, these are all chunks currently flagged across deployed sessions (score < 0.50). This trial targets only session 32 chunk 1. The rest form the repair backlog if the trial succeeds.

| Session | Chunk | Score | Hiss (dB) | Text |
|---------|-------|-------|-----------|------|
| 19 | 31 | 0.348 | −13.47 | "Your neck. Gently press your head back..." |
| 19 | 51 | 0.209 | −9.43 | "This has been Salus. Go gently..." |
| 23 | 13 | 0.426 | −10.67 | "Now imagine all the stress you have accumulated..." |
| 25 | 1 | 0.365 | −7.26 | "This is a simple introduction to mindfulness..." |
| 25 | 3 | 0.349 | −10.26 | "Find somewhere comfortable to sit or lie down..." |
| 25 | 5 | 0.430 | −8.54 | "Let's start with your breath..." |
| 25 | 12 | 0.232 | −8.35 | "You don't need to stop your thoughts..." |
| **32** | **1** | **0.449** | **−10.51** | **"Today we are going to practise something..."** ← THIS TRIAL |
| 32 | 12 | 0.325 | −10.19 | "Stay with that sensation..." |
| 36 | 7 | 0.378 | −10.04 | "There is nothing to force here..." |

Sessions 01, 03, 09, 38 have no QA data (pre-scoring). Session 18 passed clean (0/12 flagged).

---

## Phase 1: Master Narration Preservation & Chunk Schedules

Before any repair work, establish the master narration file system and extract chunk-level data for all sessions.

### 1.1 Create the masters directory

```
content/audio-free/masters/
```

### 1.2 Preserve existing raw narrations

For every deployed session that has a raw narration WAV on disk, copy it to the masters directory with the canonical naming convention. Do NOT move — copy. The originals stay where they are as a safety net.

Sessions with raw narrations (from build status):
- 03-breathing-for-anxiety
- 18-calm-in-three-minutes
- 19-release-and-restore
- 23-the-calm-reset
- 25-introduction-to-mindfulness
- 32-observing-emotions
- 36-loving-kindness-intro

Naming: `{session-name}_master-narration.wav`

Example:
```
content/audio-free/masters/32-observing-emotions_master-narration.wav
```

### 1.3 Extract chunk schedules

For every deployed session that has a manifest JSON, extract the chunk-level data and produce a readable chunk schedule. This makes it straightforward to identify which chunk contains a given word and where it sits in the narration.

Format (one file per session, stored alongside the master):
```
content/audio-free/masters/32-observing-emotions_chunk-schedule.txt
```

Contents:
```
Chunk | Start     | End       | Duration | Text (first 60 chars)
------+-----------+-----------+----------+-------------------------------
1     | 00:00.000 | 00:04.312 | 4.312s   | Today we are going to practice something that might...
2     | 00:06.812 | 00:11.450 | 4.638s   | It is simply the act of watching your emotions...
...
```

This is essential reference material for the repair process — without it, identifying which chunk contains a problem word means reverse-engineering from timestamps every time.

### 1.4 Create production records

For every deployed session, create a production record using the template from Bible Section 16. One file per session:

```
content/audio-free/masters/{session-name}_production-record.md
```

Populate using available data — manifests, build logs, chunk schedules, the deployed sessions table in the Bible, and any state files from previous briefs. For pre-v1.3 sessions (01, 09, 38) where historical data is incomplete, note what's missing rather than guessing.

This is the session's "mini bible" — everything about what was built, how, what went wrong, and what the current state is. From now on, every build, repair, remix, or redeployment updates the production record. A session without a production record is incomplete.

### 1.5 Verify

Confirm each master file exists, is a valid WAV, and matches the duration of the deployed version (excluding ambient). Log file sizes and durations in your state file.

**CRITICAL:** From this point forward, master narration files are sacrosanct. You must NEVER delete, overwrite, or use them as input for any destructive operation. When you need to apply ambient, repair, or remix — copy the master to a working file first.

---

## Phase 2: Visual QA Report Inspection

### 2.1 Locate existing QA reports

The build script generated QA report PNGs for the sessions built on 8–9 Feb. Find them:
- `content/audio-free/32-observing-emotions_QA_REPORT.png`
- `content/audio-free/19-release-and-restore_QA_REPORT.png`
- `content/audio-free/18-calm-in-three-minutes_QA_REPORT.png`
- Any others that exist

### 2.2 Inspect them

Open each QA report PNG. Examine the spectrogram, waveform, and energy plots. Look for:
- Localised bright spots or bands (potential hiss or energy spikes)
- Sudden spectral changes at chunk boundaries (tonal seams)
- Energy plot spikes close to gate thresholds
- Any anomaly that the numerical gates may have passed but is visible

### 2.3 Report findings

Document what you see in the state file. For each report:
- File name
- Any anomalies observed (with approximate timestamps)
- Whether you consider the anomaly significant or negligible
- If significant, describe what the anomaly looks like

This is a one-off catch-up — from now on, visual inspection is mandatory after every build (Bible Section 12).

---

## Phase 3: Targeted Repair Trial — Session 32

### Technical questions to validate

This trial is answering three fundamental questions:

1. **Can Fish generate a single word that tonally matches the surrounding chunk?** Voice conditioning with the existing chunk as reference should help, but it's unproven at single-word granularity.
2. **Can we splice it in without an audible seam?** Crossfade technique and spectral matching need to hold up at a word boundary, not just a chunk boundary.
3. **Does the prosody hold?** A word generated in isolation has a different pitch contour than a word mid-sentence. The replacement must sound like it belongs in the sentence, not like it was dropped in from elsewhere.

If any of these three fail, document which one and why. A negative result on any of them is valuable — it tells us whether repair is viable or whether we're stuck with regeneration.

### The defect

Session: **32 — Observing Emotions**
Location: **Chunk 1** (0:00.0 — opening of the session)
Composite score: **0.449** (below 0.50 threshold — flagged)
Hiss: **−10.51 dB**
Defect: The word **"something"** has audible **echo**
Full text: "Today we are going to practise **something** that might seem..."

Note: Session 32 also has a second flagged chunk — **Chunk 12** (score 0.325, hiss −10.19 dB, "Stay with that sensation. Do not try to make it go away..."). Do NOT attempt to repair chunk 12 in this trial. One defect at a time. If the chunk 1 repair succeeds, chunk 12 becomes the next candidate.

### 3.1 Locate the chunk

Using the build manifest for session 32, identify which chunk contains the word "something" and the exact timestamp within both the chunk and the full narration.

### 3.2 Extract context

From the master narration (`32-observing-emotions_master-narration.wav`), extract:
- The chunk containing "something" (the target chunk)
- The chunk immediately before it
- The chunk immediately after it

Save these as individual WAV files in a working directory (NOT in masters/).

### 3.3 Regenerate the target chunk

Generate 10 versions (best-of-10) of the chunk containing "something" using the same TTS settings as the original build:
- Fish Audio V3-HD
- Marco voice
- emotion=calm
- speed=0.95

**Voice conditioning:** Use the adjacent chunks (extracted in 3.2) as voice reference material if Fish's API supports conditioning from reference audio. This should help the replacement match the tonal character of the surrounding narration. If Fish doesn't support this, rely on MFCC scoring to select the most tonally consistent generation.

**Important:** You are regenerating the full chunk, not just the word "something" in isolation. A word generated alone would have wrong prosody — the pitch contour of "something" mid-sentence differs from "something" spoken standalone. Generating the complete chunk preserves natural sentence prosody.

Score all 10 versions using the composite metric. Weight MFCC tonal distance against the adjacent chunks heavily — the replacement must match the tonal character of its neighbours.

### 3.4 Select and validate

Pick the best replacement. Specifically check:
- Does the word "something" sound clean (no echo)?
- Is the tonal character consistent with the adjacent chunks?
- Are there any new defects introduced?

If none of the 10 generations fix the echo on "something" without introducing new problems, report this and stop. The trial has produced a negative result — document it.

### 3.5 Splice

Replace the target chunk in a COPY of the master narration (never the master itself):
- Working file: `content/audio-free/masters/32-observing-emotions_master-narration-repair-1.wav`
- Cosine crossfades at both splice boundaries (minimum 50ms, up to 200ms)
- The splice must not be audible — listen to the transition

### 3.6 MFCC tonal check

Run MFCC comparison between the replacement chunk and its neighbours. If tonal distance exceeds 0.50, the replacement fails. Try another version from the 10 candidates, or report failure.

### 3.7 Re-run QA

Run all 14 gates on the repaired narration. Every gate that passed on the original must still pass. If any gate fails, the repair is rejected.

### 3.8 Create repaired deployment

Apply ambient mix to the repaired narration at the same level as the original session 32 deployment (garden ambient). Encode to MP3.

Upload the repaired MP3 to R2 alongside (not replacing) the current deployment. Naming: `32-observing-emotions-repair-1.mp3`

**DO NOT replace the live deployed file.** Scott will A/B compare the original and repaired versions before deciding which goes live.

### 3.9 Document everything

In the state file, record:
- Which chunk was repaired (number, timestamp, text content)
- How many of the 10 generations were clean on "something"
- The composite score and MFCC tonal distance of the selected replacement
- Whether the splice is audible
- All 14 gate results on the repaired narration
- The R2 URL of the repaired MP3

Update session 32's production record (`32-observing-emotions_production-record.md`) with the repair details — the Repairs table, any new Known Issues, and the Human Review Notes section.

---

## Phase 4: Hiss Reduction Testing

### The problem

The pipeline has no active de-hiss step. The only hiss mitigation is chunk selection (best-of-5 prefers cleaner chunks) and ambient masking. If all 5 versions of a chunk have hiss, the hiss ships.

LALAL.AI was tested — hiss removal was excellent but dereverb stripped Marco's vocal resonance. LALAL with `dereverb=False` was identified as worth retesting but has never been tested.

Auphonic has noise reduction capabilities but has only been used for measurement, never for processing.

### 4.1 Find a hissy chunk

From the flagged chunks data, the best candidates for hiss reduction testing (ranked by worst hiss):

| Session | Chunk | Hiss (dB) | Notes |
|---------|-------|-----------|-------|
| 25 | 1 | −7.26 | Worst hiss reading across all sessions. Opening chunk. |
| 25 | 12 | −8.35 | Second worst. |
| 25 | 5 | −8.54 | Third worst. |
| 19 | 51 | −9.43 | Closing chunk — also lowest composite score (0.209). |

Session 25 chunk 1 is the ideal test candidate — it has the most pronounced hiss and it's the opening of the session (highest customer exposure). Extract this chunk from the session 25 master narration.

### 4.2 Test LALAL.AI (dereverb disabled)

Submit the hissy chunk to LALAL.AI with:
- `noise_cancelling_level=1`
- `dereverb_enabled=False`

Save the output. A/B compare against the original:
- Is hiss reduced or eliminated?
- Is Marco's vocal character preserved? (bass warmth, presence, resonance)
- Any new artefacts introduced?

### 4.3 Test Auphonic (noise reduction only)

Submit the same hissy chunk to Auphonic with:
- Adaptive Leveler: **Disabled**
- Filtering (Voice AutoEQ): **Disabled**
- Noise Reduction: **Enabled** (try both "low" and "medium" settings)
- Remove Reverb: **Off**

The key difference from previous Auphonic usage: leveller and EQ are OFF. Only noise reduction is active. Previous quality concerns were about Voice AutoEQ damaging Marco's bass — this test isolates whether noise reduction alone is safe.

Save the output. A/B compare against both the original and the LALAL version.

### 4.4 Report

For each approach, document:
- Before/after SNR measurement
- Before/after spectral comparison (MFCC distance from original)
- Subjective quality assessment: does Marco still sound like Marco?
- Recommendation: safe for production use on individual chunks? Yes/No/Conditional

---

## Phase 5: Session 25 Wiring Fix

While you're in the codebase, fix the known issue:

Session 25 (Introduction to Mindfulness) is deployed to R2 but `sessions.html` card still uses the old `player` class instead of `custom-player` with `data-src`. Wire it up properly. Commit separately from the repair work.

---

## What You Must NOT Do

- Do not edit the Bible
- Do not overwrite any master narration file
- Do not replace the live deployed session 32 MP3 — create a separate repair file
- Do not loosen gate thresholds
- Do not apply hiss reduction to full sessions — test on individual chunks only
- Do not skip the visual QA inspection
- Do not batch multiple repairs before checking each one

---

## Governance

- This brief is **read-only** for Code
- Create a state file immediately: `repair-trial-STATE.md`
- Update the state file after every step
- If a STOP rule is triggered, output status report and cease work
- If the repair trial produces a negative result (cannot fix "something" without introducing new problems), that is a valid outcome — document it honestly

---

## Success Criteria

This trial is successful if:
1. Master narrations are preserved and catalogued
2. Visual QA reports have been inspected and findings documented
3. The word "something" in session 32 has been repaired (or an honest report explains why it couldn't be)
4. The repaired narration passes all 14 gates
5. Scott can A/B compare original vs repaired versions
6. At least one hiss reduction approach has been tested with documented results
7. Session 25 wiring is fixed

---

END OF BRIEF
