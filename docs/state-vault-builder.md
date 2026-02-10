# Vault Builder — State File

**Brief:** vault-builder (ACTIVE)
**Created:** 2026-02-10
**Last updated:** 2026-02-10

---

## Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| Step 1: State file | COMPLETE | This file |
| Step 2: Script pre-processing | COMPLETE | Tasks 0-4 all done |
| Step 3: vault-builder.py | COMPLETE | Built with gen + file org + picker + R2 upload |
| Step 4: Test run (session 52) | COMPLETE | 66 chunks, 1330 candidates, R2 uploaded, picker live with auto-save |
| Step 5: vault-assemble.py | COMPLETE | Built — reads picks, splices, loudnorm, QA |
| Step 6: New session workflow | PENDING | Verify end-to-end after Step 4 |

---

## Step 2: Script Pre-Processing — COMPLETE

### Task 0: Script Recovery

16 scripts on disk out of 51 in inventory. Missing scripts have no manifests and no source files.
**Status:** UNRECOVERABLE — non-blocking. Vault builder processes what exists.

### Task 1: Silence Format Fix — COMPLETE

| Script | Instances | Status |
|--------|-----------|--------|
| 09-rainfall-sleep-journey.txt | 6 → `[SILENCE: X]` | DONE |
| 38-seven-day-mindfulness-day1.txt | 8 → `[SILENCE: X]` | DONE |

### Task 2: Block Merging — COMPLETE (built into vault-builder.py)

Two-pass merge in `preprocess_blocks()`:
- Pass 1: Forward merge (short block + following block, pause < 5s, result ≤ 200 chars)
- Pass 1b: Backward merge (short block merged into preceding block if forward failed)

Result: ~98 short blocks → 4 remaining (all surrounded by ≥5s pauses, can't merge further).

### Task 3: Block Splitting — COMPLETE (built into vault-builder.py)

Automatic sentence-boundary splitting for blocks > 300 chars. Each fragment 50-200 chars with `[SILENCE: 3]` between.

Session 52 dry run: 6 blocks split (326→2, 342→2, 386→2, 312→2, 322→2, 339→2).

### Task 4: Inventory — COMPLETE

`content/audio-free/vault/inventory.json`:
- **457 blocks** across **14 scripts**
- Non-opening blocks <50 chars: **4** (0.9%)
- Blocks >300 chars: **0**
- Opening blocks >60 chars: **6** (existing scripts, acceptable)

---

## Step 3: Tools Built

### vault-builder.py

Single-session and batch modes. Features:
- Imports from build-session-v3.py (score_chunk_quality, compute_mfcc_profile, tonal_distance, etc.)
- Async generation with aiohttp + Semaphore(5) for Fish rate limit
- Exponential backoff on 429s
- Resume support (skips existing versions)
- Per-chunk metadata + scores JSON files
- Session manifest with cost tracking
- Global generation log (append-only)
- Interactive picker HTML with: sorting, notes, PICK/X buttons, localStorage, export
- R2 upload of all WAV candidates + review.html
- Email notification via Resend

CLI:
```bash
python3 vault-builder.py content/scripts/52-the-court-of-your-mind.txt   # single
python3 vault-builder.py --batch content/scripts/                         # batch
python3 vault-builder.py --dry-run content/scripts/52-the-court-of-your-mind.txt
python3 vault-builder.py --inventory-only                                 # inventory only
```

### vault-assemble.py

Reads picks.json → copies picked WAVs → edge fades → humanized pauses → concat → loudnorm → WAV + MP3 → QA gates.

CLI:
```bash
python3 vault-assemble.py 52-the-court-of-your-mind
python3 vault-assemble.py 52-the-court-of-your-mind --skip-qa
```

---

## Session 52 Dry Run Results

| Metric | Value |
|--------|-------|
| Raw blocks | 60 |
| Processed blocks | 66 (6 splits) |
| Total candidates | 1,330 |
| Total characters | 223,430 |
| Estimated cost | £0.67 |
| Blocks <50 chars | 0 |
| Blocks >300 chars | 0 |

---

## Decisions Log

- 2026-02-10: Missing scripts (35+ of 51) are unrecoverable. Vault builder proceeds with 14 available scripts (excluding variants).
- 2026-02-10: Merge/split logic built into vault-builder.py as preprocessing (not manual script edits). Original scripts preserved as creative source.
- 2026-02-10: All vault candidates uploaded to R2 at `vault/{session-id}/` after generation completes.
- 2026-02-10: Brief received and copied to `brief-vault-builder.md` in project root.

---

## Blockers

None. Ready for Step 4 test run on Scott's approval.
