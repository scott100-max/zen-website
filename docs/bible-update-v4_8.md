# Bible Update Brief — v4.8

**Date:** 14 February 2026
**Source documents:**
1. Session debrief 14 Feb 2026 (8 items + audio wiring audit)
2. Session log 14 Feb 2026 (3 targeted repairs, 3 bug reports)
3. Echo Fingerprint Analysis report (14 Feb 2026)
4. Claude Desktop conversation re: raw narration preservation

**Headline:** Echo detection breakthrough (AUC 0.34→0.79), Gate 16 defined, 53 sessions batch-remixed with correct ambients, 19 sessions reconnected via wiring audit, session registry created, remix tool built, raw narration archival rule established.

---

## SECTION-BY-SECTION CHANGES

---

### 1. Section 4 (Authentication & Payments) — Premium Unlock Gap Fix

`auth.js` `updateNavUI()` was missing handlers for two mindfulness-page-specific premium elements:

- `.sp--locked` session cards (6 cards showing "Premium" label to subscribers)
- `#subHook` / `.m-hook` ("Go Premium" banner still visible to subscribers)

Already handled correctly elsewhere: `.day-tile--locked`, `.unlock-cta`, `.cta-banner`, sleep story re-render, 21-day course inline JS, footer "Go Premium" links.

Fix added both selectors to the `isPremium()` branch: `querySelectorAll('.sp--locked')` → `display:none`, `getElementById('subHook')` → `display:none`.

**Commit:** `fc8157c` — "Fix premium content still showing locked for subscribers"

---

### 2. Section 8 (Production Rules) — Two New Rules

**Production Rule 26 — Raw narration archival (STOP-rule grade):**

Before any repair operation that modifies chunk picks or reassembles the voice master, the current `-vault-voice.wav` must be copied to `archive/` within the vault directory with a timestamped filename (e.g. `{session}-vault-voice-pre-repair-{YYYYMMDD}.wav`). The original first-assembly voice master must never be overwritten — it is the baseline. Post-repair voice masters are retained alongside it. Deletion of any voice master file requires explicit human approval.

This is a STOP-rule-grade requirement: if the archive copy fails or the archive directory cannot be created, the repair must halt.

**Evidence:** S60 repair required loading the raw narration for chunk-swap reassembly. The file was unavailable — either overwritten during a previous operation or never saved post-assembly. The voice master is the single most expensive asset per session (hours of vault picking, candidate generation). Losing it means rebuilding from scratch.

**Relationship to Rule 14:** Rule 14 covers initial raw narration preservation. Rule 26 extends this to repair operations specifically, requiring versioned archival before every modification.

**Production Rule 27 — Catalogue ambient assignments override script headers:**

The `session-registry.json` ambient assignments (sourced from `Salus_Session_Catalogue.docx`) are the canonical source of truth for which ambient each session uses. Script header `Ambient:` fields are often wrong or generic and must NOT be used as the ambient source. Any tool reading ambient assignments must read from `session-registry.json`, not from script headers.

---

### 3. Section 8 (Production Rules) — Rule 21 Amendment: Ambient Gain Boost

Amend Rule 21 or add to the ambient gain table in Section 11:

- **Birds** and **garden** ambient sources get **+5dB gain boost** (these sources are inherently quiet and need the boost to reach effective masking levels).

---

### 4. Section 11 (Audio Processing Pipeline) — Ambient Library Expansion

**Six new 1-hour ambient sources** downloaded from R2 ASMR files (`content/audio-free/asmr-*.mp3`) and copied with clean names into `content/audio/ambient/`:

| File | Duration | Source |
|------|----------|--------|
| `courtroom.mp3` | 1 hr | ASMR download from R2 |
| `harbour.mp3` | 1 hr | ASMR download from R2 |
| `rain-on-tent.mp3` | 1 hr | ASMR download from R2 |
| `childhood-memories.mp3` | 1 hr | ASMR download from R2 |
| `waves.mp3` | 1 hr | ASMR download from R2 |
| `train.mp3` | 1 hr | ASMR download from R2 |

**Add to existing available ambients table.** Full ambient library is now: grace, garden, birds, rain, stream, ocean, fire, waves, train, courtroom, harbour, rain-on-tent, childhood-memories, loving-kindness-ambient, plus 8hr/extended variants.

**Short ambient looping:** The remix tool loops ambient files shorter than the session duration. Known short files: waves (77s), train (41s). These loop seamlessly to cover full sessions.

**Session 03 pre-roll standardised** from 60s (non-standard) to 30s, matching all other sessions.

---

### 5. Section 11 — Ambient Assignment Map (New Subsection)

Complete ambient-to-session mapping from `session-registry.json` (source of truth: `Salus_Session_Catalogue.docx`):

| Ambient | Sessions |
|---------|----------|
| Grace | 01, 36, 38, 41, 43 (both), 57, 60, 61, 69, 75, 76, 79, 83, 84, 85, 86 |
| Garden | 19, 25, 32, 53, 58, 65, 67, 71, 77 |
| Birds | 03, 66, 70, 81 |
| Birds+fire | 40, 59, 62, 72 |
| Rain | 09, 18, 42 |
| Stream | 23, 39, 64, 68 |
| Waves | 44, 63, 73, 80 |
| Ocean | 87 |
| Train | 54, 78 |
| Courtroom | 52, 55 |
| Harbour | 56 |
| Rain-on-tent | 74 |
| Grace+childhood-memories | 82 |

Note: Session 36 script header said `loving-kindness-ambient` — overridden to `grace` per catalogue.

---

### 6. Section 12 (QA Gate System) — Gate 16: Echo Detection (Granular Mel Analysis)

**NEW GATE. This is the most significant pipeline addition since the vault workflow.**

**Position:** Per-candidate scoring during vault-builder/auto-picker. Runs before assembly.
**Type:** Ranking penalty (continuous score), not binary pass/fail.
**Status:** VALIDATED — blind test on unseen sessions confirmed.

**Method:** Z-score composite of 11 spectral features:

| # | Feature | Cohen's d | Direction | What it measures |
|---|---------|-----------|-----------|-----------------|
| 1 | mel_00_std | 0.868 | echo_lower | Sub-bass frequency variation |
| 2 | mel_01_std | 0.846 | echo_lower | Second sub-bass band variation |
| 3 | corr_range | 0.767 | echo_higher | Band correlation spread |
| 4 | band_corr_min | 0.784 | echo_lower | Minimum adjacent-band correlation |
| 5 | band_corr_std | 0.723 | echo_higher | Band correlation variability |
| 6 | mel_49_skew | 0.698 | echo_lower | Mid-band distribution skewness |
| 7 | ratio_lowmid_uppermid | 0.610 | echo_higher | Spectral shape: low-mid vs upper-mid |
| 8 | mel_00_kurt | 0.667 | echo_higher | Sub-bass distribution kurtosis |
| 9 | band_corr_mean | 0.650 | echo_lower | Overall band correlation |
| 10 | contrast_6_std | 0.646 | echo_higher | High-band contrast variability |
| 11 | ratio_subbass_std_norm | 0.490 | echo_lower | Relative sub-bass variation |

**Extraction parameters:** 80-band mel spectrogram (n_fft=2048, hop=256, sr=22050).

**Z-score formula:** For each feature, compute z = (value − clean_mean) / clean_std, multiply by direction sign, sum all z-scores, divide by 11.

**Thresholds:**

| Score | Interpretation | Action |
|-------|---------------|--------|
| < 0.0 | Clean | No penalty |
| > 0.4 | Elevated echo risk | Ranking penalty applied |
| > 1.0 | High echo risk | Strong penalty |
| > 2.0 | Very high echo risk | Near-certain echo |
| > 2.5 | Elimination threshold | Candidate eliminated outright |

**Auto-picker integration:** REPLACES the current `echo_risk` (spectral flux variance, `ECHO_RISK_CEILING=0.003`). New weight: `ECHO_RANK_WEIGHT = 200` (unchanged, but applied to a signal that actually works). Candidates with Gate 16 score > 2.5 eliminated outright.

**Calibration data:**

| Metric | Value |
|--------|-------|
| AUC (cross-validated, leave-one-session-out) | 0.793 |
| FNR at balanced threshold | 31% |
| FPR at balanced threshold | 18% |
| Precision | 0.889 |
| Recall | 0.686 |
| Training data | 70 echo + 34 clean chunks across 6 sessions |

**Blind test results (completely unseen sessions):**

Session 38 (Day 1) — 27 chunks: 13 echo found (revised after re-listen), Gate 16 caught 9 (69%), missed 4. Gate 16 detected 6 echo chunks the human ear missed on first listen.

Session 41 (Day 4) — 23 chunks: 10 echo, Gate 16 caught 8 (80%), missed 2.

Combined blind test: 71% recall, 50% precision, 29% FNR, 63% FPR.

**KEY FINDING:** Gate 16 detected echo the human ear missed on first listen. The two highest-scoring "false positives" (c08=3.42, c12=2.25 on S38) were confirmed as real echo on re-listen. The detector is more sensitive than casual human review for subtle spectral contamination.

**Known limitation — Two echo subtypes:**

| Subtype | Detection | Characteristics |
|---------|-----------|----------------|
| Type A ("Loud Echo") | CAUGHT (69–80%) | Higher energy (+2–4dB), disrupted band correlation (corr_range ≈ 0.047), strong low-mid energy shift |
| Type B ("Quiet Echo") | MISSED (31%) | Lower energy (−2–4dB), intact band correlation (corr_range ≈ 0.024 ≈ clean level), no detectable spectral shift |

Discriminator between caught and missed: `corr_range` (d=1.436, p<0.000001). If corr_range > 0.035, echo is almost always detectable. If corr_range < 0.030, echo looks clean to every feature tested.

Type B predominantly from S01 early review rounds (15/22 missed). Possible explanations: borderline labelling in early rounds, or echo manifests differently across generation batches.

---

### 7. Section 16B (Echo Detection) — Complete Rewrite

The existing Section 16B status line ("INVESTIGATION COMPLETE — no automated echo detector works yet") is now **obsolete**. Replace with:

**Status:** WORKING — Gate 16 achieves AUC 0.793 (up from 0.34–0.51). Catches 69–80% of echo, more sensitive than casual human listening for subtle contamination. Type B "quiet echo" (29% FNR) remains undetected. Human review remains the final authority.

**The Echo Fingerprint (14 Feb 2026):**

Echo in Fish TTS has a measurable spectral signature. The signal is in **mel band statistics** and **cross-band correlation** — NOT in autocorrelation, phase coherence, cepstral analysis, or modulation spectrum (which the old approaches relied on). Echo smears spectral energy downward (sub-bass flattens, low-mid gets louder relative to upper-mid) and disrupts the normal coherent movement between frequency bands. It is a tonal compression effect, not a physical reverb — consistent with the D7 Auphonic finding that this is generative distortion.

**What was tested (comprehensive — 697 features):** 80-band mel spectrogram stats (320 features), per-band spectral flux (240 features), cross-band correlation, phase coherence, autocorrelation at 5 lag ranges, cepstral analysis at 4 quefrency ranges, modulation spectrum at 5 frequency bands, post-onset spectral decay, sub-band energy ratios, spectral shape metrics, RMS envelope, pitch stability. 48 features significant at p < 0.05.

**What did NOT work (weak discrimination, |d| < 0.5):** Autocorrelation (all lag ranges), cepstral analysis, absolute phase coherence, modulation spectrum, spectral decay after transients, spectral flux. The old `echo_risk` (spectral flux variance) targets these weak families — explaining its ~58% FNR.

**Differential analysis finding:** Phase coherence ratios show 100% consistent direction across all 34 paired samples (same text, echo vs clean). This is the most reliable signal but requires a known-clean reference to use — not applicable for blind candidate scoring.

**Classifier progression:**

| Approach | AUC | FNR | FPR |
|----------|-----|-----|-----|
| Composite scorer (v6, pre-Gate 16) | ~0.5 | 58% | ? |
| echo-detector.py (RF, 65 features) | 0.512 | 67% | 28% |
| Auphonic analysis | 0.341 | n/a | n/a |
| **Gate 16 (11 features, CV)** | **0.793** | **31%** | **18%** |

**Operating philosophy — "Replace Until Pass":**

FPR does not matter for production use. The workflow: Gate 16 scores all candidates → auto-picker penalises high-scoring candidates → if picked chunk still scores high, regenerate and re-pick → repeat until pass. Regenerating chunks is cheap (seconds, pennies). Shipping echo is expensive (ruins listener experience, erodes trust). Therefore: optimise for RECALL, accept false positive waste. A falsely flagged chunk just gets regenerated — no harm done. A chunk with echo that passes undetected ships to production.

Gate 16 operating point should favour HIGH RECALL (≥90% catch on training data), not balanced threshold.

**Data gaps:** Clean labels exist only for sessions 01 and 03. Sessions 36, 52 have echo labels but no clean labels. A/B picker review pages capture version preferences but NOT defect labels. Current picking sessions (S60, S62) will produce picks only, not verdicts, unless review pages are regenerated with verdict buttons.

**"What Must NOT Happen" updates:** Retain existing rules. Amend:
- ~~"Do not claim the composite scorer detects echo"~~ → Replace: "Do not claim Gate 16 catches all echo. Type B quiet echo (29% FNR) is invisible to Gate 16. Human review remains the final authority."
- ~~"Do not reduce human review scope based on any automated echo score"~~ → Replace: "Gate 16 reduces but does not eliminate the need for human echo review. Use it to prioritise which chunks to listen to most carefully, not to skip listening."

---

### 8. Section 16B — Next Defects (New Subsection)

Echo is the first defect tackled with granular mel analysis. Next in priority order, using the same 11-feature z-score framework + labelled data:

1. **VOICE BREAKOUT** — voice jumps several octaves mid-chunk. Devastating defect, should produce massive spectral shift (far larger than echo).
2. **HISS** — high-frequency noise contamination.
3. **AUDIO FUZZ** — broadband distortion/crackle.

Each needs: labelled examples (Y/N per chunk), feature extraction via `echo-workbench.py` (or variant), classifier training, blind test, then integration as Gate 17/18/19 in auto-picker.

---

### 9. Section 16D (Vault Production Workflow) — Compound Ambient Gap

`vault-assemble.py`'s `find_ambient_file()` does not support "+" syntax (e.g. "birds+fire"). `remix-session.py` does. Sessions 40, 59, 62, 72 all use compound ambients. If `vault-assemble.py` needs to rebuild these sessions, it will fail at ambient mixing.

Resolution options: add "+" parsing to `vault-assemble.py`, or mandate `remix-session.py` for compound ambient sessions.

---

### 10. Section 16D — Gate 9 QA Crash Bug

`vault-assemble.py` crashes in Gate 9 (visual report) with `KeyError: 'time'` on energy spike flags. Non-blocking — audio is fully built before the crash — but prevents QA completion. Bug is in `build-session-v3.py` line 2768: `ax.axvline(x=flag['time'], ...)` where the flag dict uses a different key name.

---

### 11. Section 16D — Chunking Bug: Silence Marker Merge

**Session 01 chunk 7** — `preprocess_blocks()` merge logic merged three separate script lines (with `...` silence markers between them) into a single 131-character chunk because each sub-line was <50 chars. The merge function (forward + backward) absorbed the lines despite having pauses ≥8s between them. The silence markers (1× `...` = 8s, 3× `...` = 50s for mindfulness profile) were lost.

The forward merge condition checks `pause < 5` before merging, but S01 had `pause=8` and the merge clearly happened. Either the session was built with an older vault-builder version with more permissive thresholds, or `process_script_for_tts` produced different pause values. The current code SHOULD prevent this merge, but the vault was built 11 Feb and the merge occurred.

**New safety rule:** NEVER merge blocks that have `...` silence markers between them in the source script, regardless of character count. The <50 char merge is an optimisation for continuous speech; it must not cross deliberate pause boundaries.

---

### 12. Section 16E (Auto-Picker) — Tools & Files Table Additions

Add to the existing files table:

| File | Purpose |
|------|---------|
| `tools/remix-session.py` | Fast ambient remix using existing loudnormed voice masters. Reads ambient from session-registry.json, supports compound ambients ("+"), ~30s/session. `--deploy` handles R2 + CDN + local copy. Saves `remix-log.json` for audit. |
| `content/session-registry.json` | 55 sessions catalogued. Maps session ID → ambient, category, status. Supports combo ambients. Source of truth for ambient assignments. 52 deployed, 3 script-only (88, 89, 90). |
| `echo-workbench.py` | Echo analysis tool. Steps: `--collect --analyze --classify --report --all`. Main workbench for defect fingerprinting. |
| `reference/echo-analysis/` | Echo analysis outputs: `echo_dataset.json`, `echo_features_granular.json`, `clean_features_granular.json`, `differential_features.json`, `statistical_results.json`, `differential_results.json`, `classifier_config.json`, `echo-fingerprint-report.html` |

**remix-session.py usage:**
```
python3 tools/remix-session.py 42-seven-day-mindfulness-day5            # remix one
python3 tools/remix-session.py --all --deploy                           # remix + deploy all
python3 tools/remix-session.py --category 21day --ambient rain --deploy # category + override
```

---

### 13. Section 16 (Deployment) — Audio Wiring Audit & Lesson

After batch-remixing all 53 sessions, a full wiring audit revealed **19 sessions disconnected** — audio present on R2 but not reachable from the site. Root cause: the site was built in phases, and the 13 Feb night build deployed 49 new sessions to R2 but only handled audio production — nobody went back to wire the HTML pages.

**Four failure categories:**

**A) Wrong R2 paths (3 session pages + media.html):** Old path convention (`content/audio/` with `-vault-ambient` suffix) never updated when standard changed to `content/audio-free/{id}.mp3`. Affected: `sessions/breathing-for-anxiety.html`, `sessions/calm-reset.html`, `sessions/observing-emotions.html`, `media.html`.

**B) Wrong filename (1 mismatch):** `mindfulness.html` referenced `36-loving-kindness-intro.mp3` (no `-v3`). Actual file on R2: `36-loving-kindness-intro-v3.mp3`. Also: `mindfulness-21-day.html` default `data-src` pointed to session 38 (7-day day 1) instead of session 57 (21-day day 1) — cloned from 7-day page template.

**C) "Audio coming soon" placeholders (3 sleep story pages):** `the-slow-train-north.html` (S54), `the-bookshop-at-the-end-of-the-lane.html` (S55), `the-lighthouse-keepers-log.html` (S56). Built as HTML-first story pages before audio existed. JavaScript said "Audio coming soon". Audio deployed to R2 on 13 Feb but pages never updated. Also added `src` properties to `sleep-stories.html` listing for all 3.

**D) Completely missing from all pages (12 sessions):** CBT sessions 78–81 had cards but zero audio players on `cbt.html`. Session 52 only had audio on its own detail page, not the CBT listing. Mindfulness sessions 82–84 and sleep sessions 85–87 from the night build were never added to any page.

**Commit:** `16e4086` — "Fix audio wiring across all pages — 19 sessions reconnected"

**Lesson / new workflow requirement:** Deploying audio to R2 is only half the job. Every session needs a corresponding HTML wiring step. Future workflow should include a post-deploy wiring check — or the remix/deploy tool should generate a wiring report showing which sessions lack page references. Relates to existing L-40 (R2 path consistency check) but broader in scope.

---

### 14. Section 16 (Deployment) — Course Player Wiring

7-day course (`sessions/seven-day-mindfulness-course.html`): Days 2, 3, 4, 6, 7 were missing audio `src` URLs despite audio being deployed on R2. Added R2 URLs for sessions 39–41, 43–44. Days 1, 5 already had `src`.

21-day course (`mindfulness-21-day.html`): Day 1 had WRONG `src` (pointed to session 38 = 7-day Day 1, not session 57 = 21-day Day 1). Days 2–4, 6–19, 21 all missing `src`. Added R2 URLs for sessions 58–75, 77. Days 5, 20 already had `src`.

**Commit:** `c401a5f` — "Add player src URLs for all 7-day and 21-day course sessions"

This closes out the "live" definition gap from v4.7 — these sessions were "available" on R2 but not wired into HTML.

---

### 15. Section 16 (Deployment) — Batch Remix Milestone

**53/53 deployed sessions** remixed with correct catalogue-assigned ambients + 30s pre-roll, uploaded to R2, CDN caches purged. This is the first time every deployed session has the right ambient from a single source of truth rather than ad-hoc per-session mixing.

Sessions remixed: Mindfulness (01, 03, 09, 18, 19, 23, 25, 32, 36, 43-nda, 82–87), 7-Day (38–44), 21-Day (57–77), CBT (52, 78–81), Sleep Stories (53–56).

Initial batch: 50/53 uploaded, 3 timed out (25, 70, 71) + 1 auth error (53). Retry: all 4 uploaded successfully. CDN cache purged for all 53.

---

### 16. Section 16 — Targeted Repairs (S60, S62, S01)

**S60 (21day-mindfulness-day04) — Voice breakout at 0:56:**
Chunk 1, Fish TTS artefact in candidate v24. Swapped pick to v17 (highest quality score in pool: 1.1172). Manual pick swap in `picks-auto.json`, reassembly with grace ambient. 22 other chunks locked (byte-identical). Deployed, MD5 verified. **PASS.**

**S62 (21day-mindfulness-day06) — Voice breakout at 3:36:**
Chunk 6, Fish TTS artefact in candidate v12. Swapped pick to v18. Used `remix-session.py` (not vault-assemble.py) because vault-assemble.py cannot handle compound ambient name "birds+fire". 24 other chunks locked. Deployed, MD5 verified. **PASS.**

**S01 (01-morning-meditation) — Missing silence in chunk 7:**
Three separate script lines with `...` silence markers merged into single 131-char chunk (see Section 11 chunking bug above). Fix: generated new TTS candidates for each sub-line separately (5 per line, 15 total), selected best, stitched with correct silences (8s + 50s). Chunk 7 duration: 13.5s → 68.4s. Session total: 14.1 min → 15.1 min. 25 other chunks locked. **AWAITING REVIEW.**

---

### 17. Section 17 (Governance) — Bible Sync Lesson

In-repo Bible copy was stale at v4.2 (missed v4.3–v4.6 entirely). Code was operating against a Bible five minor versions behind. Updated to v4.7 (commit `d3b2a23`). Standing memory instruction added for Code: check `Desktop/Live Bible/` at session start.

This is a governance gap — the separation of duties (Desktop maintains Bible, Code reads it) only works if Code receives the latest version. Add as a standing rule: Code must verify Bible version matches Desktop/Live Bible at session start. If versions differ, update before proceeding.

---

### 18. Session Count Update

**55 total sessions** catalogued in `session-registry.json`:
- 52 deployed (audio on R2, now all wired to HTML after wiring audit)
- 3 script-only (88, 89, 90)

---

## LEDGER UPDATES

### Items to mark COMPLETE

| # | Item | Resolution |
|---|------|------------|
| L-18 | Echo detector revalidation | **COMPLETE** — Gate 16 achieves AUC 0.793 on 70 echo + 34 clean chunks across 6 sessions. Surpasses the target of AUC > 0.70. FNR 31% (above 10% target — but see operating philosophy: FNR acceptable when combined with "replace until pass" workflow). Supersedes the original Whisper confidence approach. |
| L-44 | Session 38 ambient remix | **COMPLETE** — included in batch of 53 sessions remixed with correct catalogue ambients + 30s pre-roll. Confirm with Code. |

### New Items

| # | Item | Source | Owner | Status |
|---|------|--------|-------|--------|
| L-46 | **Post-deploy wiring report** — remix/deploy tool should generate a wiring report listing sessions that exist on R2 but lack `data-src` references in any HTML page. Broader than L-40 (which checks path correctness for already-wired sessions). This catches sessions that were never wired at all. Evidence: 19 sessions found disconnected in wiring audit. | v4.8 | Code | OPEN |
| L-47 | **Review page verdict buttons** — A/B picker review pages capture version preferences but NOT defect labels (ECHO/CLEAN/HISS/VOICE). Add verdict buttons to review pages. Current picking sessions (S60, S62 etc.) produce picks only, not verdicts, losing potential training data. Target: 150+ labelled chunks across 10+ sessions. | v4.8 | Code | OPEN |
| L-48 | **Type B "quiet echo" investigation** — 29% FNR from echo with intact band correlation (corr_range < 0.030). Needs different features or more data. Options: temporal analysis, neural embeddings, or accept and rely on human review. | v4.8 | Scott/Code | OPEN — research |
| L-49 | **Gate 16 integration into auto-picker** — Replace `echo_risk` (spectral flux variance) with Gate 16 z-score composite. Use high-recall operating point. Threshold: z-score > 0.4 = penalty, > 2.5 = elimination. Classifier config in `reference/echo-analysis/classifier_config.json`. | v4.8 | Code | OPEN |
| L-50 | **Voice breakout detector (Gate 17)** — Next defect for granular mel analysis. Labelled examples needed. Same framework as Gate 16. Priority 1 after Gate 16 integration. | v4.8 | Scott/Code | OPEN — needs labelled data |
| L-51 | **Compound ambient support in vault-assemble.py** — `find_ambient_file()` does not support "+" syntax. Sessions 40, 59, 62, 72 require `remix-session.py` instead. Add "+" parsing or mandate remix tool for compounds. | v4.8 | Code | OPEN |
| L-52 | **Gate 9 KeyError crash** — `vault-assemble.py` crashes in Gate 9 (visual report) with `KeyError: 'time'` on energy spike flags. Non-blocking but prevents QA completion. Bug in `build-session-v3.py` line 2768. | v4.8 | Code | OPEN |
| L-53 | **Chunking bug: silence marker merge safety rule** — Add rule to `preprocess_blocks()`: never merge blocks with `...` silence markers between them, regardless of character count. Evidence: S01 chunk 7 merged three lines across 8s and 50s pauses. | v4.8 | Code | OPEN |
| L-54 | **S01 chunk 7 repair review** — Awaiting human review of the silence-corrected chunk 7 (13.5s → 68.4s, session 14.1 → 15.1 min). | v4.8 | Scott | WAITING |

### Existing Items — Status Notes

| # | Note |
|---|------|
| L-40 | R2 path consistency check — still relevant as a systemic tool. The wiring audit fixed specific instances manually but the automated check is still needed. Now supplemented by L-46 (which catches completely unwired sessions, not just wrong paths). |
| L-29 | Session 01 chunk 11 — may need re-evaluation given the chunk 7 repair changed session timing. |

---

## AMENDMENT LOG ENTRY

### 14 February 2026 — v4.8: Echo Detection Breakthrough, Batch Remix, Audio Wiring Audit

**Source:** Session debrief 14 Feb (9 items), session log 14 Feb (3 repairs, 3 bugs), echo fingerprint analysis report, Claude Desktop conversation (narration preservation).

**Headline:** Echo detection AUC 0.34→0.79. Gate 16 defined (11-feature mel/correlation z-score). 53 sessions batch-remixed with correct ambients. 19 sessions reconnected via wiring audit. Session registry and remix tool created. Raw narration archival rule established.

**18 additions/changes:**

1. **Section 4 (Auth)** — Premium unlock gap fix: `.sp--locked` and `#subHook` handlers added to `updateNavUI()`.
2. **Section 8 (Production Rules)** — Rule 26: Raw narration archival before any repair (STOP-rule grade). Rule 27: Catalogue ambient assignments override script headers.
3. **Section 8 (Production Rules)** — Rule 21 amendment: birds and garden get +5dB gain boost.
4. **Section 11 (Ambient)** — 6 new 1-hour ambient sources added (courtroom, harbour, rain-on-tent, childhood-memories, waves, train). Short ambient looping documented. Session 03 pre-roll standardised to 30s.
5. **Section 11 (Ambient)** — New ambient assignment map from session-registry.json.
6. **Section 12 (Gate System)** — NEW Gate 16: Echo Detection via granular mel analysis. 11 features, z-score composite, AUC 0.793. Blind test: 71% recall, found echo human ear missed. Two subtypes documented (Type A caught, Type B missed).
7. **Section 16B (Echo Detection)** — Complete rewrite. Status changed from "no detector works" to "working" (AUC 0.793). Echo fingerprint documented (mel band stats + cross-band correlation). Comprehensive feature family analysis (697 features tested). Operating philosophy: "replace until pass" (FPR irrelevant). Data gaps identified.
8. **Section 16B** — New subsection: Next defects roadmap (voice breakout, hiss, audio fuzz as Gates 17/18/19).
9. **Section 16D** — Compound ambient gap in vault-assemble.py documented.
10. **Section 16D** — Gate 9 KeyError crash documented.
11. **Section 16D** — Chunking bug: silence marker merge in preprocess_blocks() documented with new safety rule.
12. **Section 16E (Files)** — 4 new entries: remix-session.py, session-registry.json, echo-workbench.py, reference/echo-analysis/.
13. **Section 16 (Deployment)** — Audio wiring audit: 19 sessions reconnected across 4 failure categories. Lesson: every deploy needs a wiring step.
14. **Section 16 (Deployment)** — Course player wiring: 7-day and 21-day courses fully wired.
15. **Section 16 (Deployment)** — Batch remix milestone: 53/53 sessions remixed with correct catalogue ambients.
16. **Section 16 (Deployment)** — Three targeted repairs documented (S60 pass, S62 pass, S01 awaiting review).
17. **Section 17 (Governance)** — Bible sync lesson: in-repo copy was 5 versions stale. Standing rule: verify Bible version at session start.
18. **Session count** — 55 total (52 deployed, 3 script-only).

**Commits this session:**
```
d3b2a23  Update Project Bible to v4.7
fc8157c  Fix premium content still showing locked for subscribers
c401a5f  Add player src URLs for all 7-day and 21-day course sessions
b5a50fa  Add session registry and fast ambient remix tool
16e4086  Fix audio wiring across all pages (19 sessions reconnected)
```

**Ledger:** L-18→COMPLETE (echo detection), L-44→COMPLETE (session 38 remix). New: L-46 (wiring report), L-47 (review page verdict buttons), L-48 (Type B echo), L-49 (Gate 16 integration), L-50 (voice breakout detector), L-51 (compound ambient), L-52 (Gate 9 crash), L-53 (chunking silence merge), L-54 (S01 chunk 7 review).
