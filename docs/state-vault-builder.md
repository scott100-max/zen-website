# Vault Builder — State File

**Brief:** vault-builder (ACTIVE)
**Created:** 2026-02-10
**Last updated:** 2026-02-10

---

## Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| Step 1: State file | COMPLETE | This file |
| Step 2: Script pre-processing | IN PROGRESS | Tasks 0-4 |
| Step 3: vault-builder.py | PENDING | Generation + file org + picker |
| Step 4: Test run (session 52) | PENDING | Blocked on Step 3 |
| Step 5: vault-assemble.py | PENDING | Assembly tool |
| Step 6: New session workflow | PENDING | End-to-end verify |

---

## Step 2: Script Pre-Processing

### Task 0: Script Recovery

Scripts in `/content/scripts/`: 16 files found.
Inventory claims 51 production scripts — only 16 .txt files exist on disk.

**Missing scripts (no .txt file, no manifest):**
- 02, 04, 05, 06, 07, 08, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 24, 26, 27, 28, 29, 30, 31, 33, 34, 35, 37, 39, 40, 41, 42, 44, 45, 46, 47, 48, 49, 50, 51

**Status:** UNRECOVERABLE — no manifests, no source files. Scripts must be recreated separately.
Non-blocking for vault builder — we process what exists.

### Task 1: Silence Format Fix

| Script | Instances | Status |
|--------|-----------|--------|
| 09-rainfall-sleep-journey.txt | 6 (`[X second pause]` → `[SILENCE: X]`) | COMPLETE |
| 38-seven-day-mindfulness-day1.txt | 8 (`[X second pause]` → `[SILENCE: X]`) | COMPLETE |

### Task 2: Block Merging (under 50 chars)

Scripts with blocks under 50 chars (from analysis):
- 01-morning-meditation: 27/51 blocks under 50
- 03-breathing-for-anxiety: 34/49 blocks under 50
- 09-rainfall-sleep-journey: 17/75 blocks under 50
- 36-loving-kindness-intro (all versions): 1 each (borderline ~48 chars)
- 38-seven-day-mindfulness-day1: 7/44 blocks under 50
- 43-non-dual-awareness: 7/40 blocks under 50
- narrator-welcome: 1/5 (chunk 0, 35 chars — cold start, leave as-is)
- marco-clone-sample: 2/7 under 50

Rules: merge with FOLLOWING block, no cross-5s+ silence, no chunk 0+1 merge, result ≤200 chars.

### Task 3: Block Splitting (over 300 chars)

Scripts with blocks over 300 chars:
- 43-non-dual-awareness: 13 blocks over 300 (up to 757 chars)
- 52-the-court-of-your-mind: 6 blocks over 300 (up to 386 chars)
- 09-rainfall-sleep-journey: 1 block over 300 (caused by old pause format — should fix after Task 1)

### Task 4: Inventory Refresh

Status: PENDING — blocked on Tasks 1-3 completion.

---

## Decisions Log

- 2026-02-10: Missing scripts (35+ of 51) are unrecoverable from current data. Vault builder proceeds with 16 available scripts.
- 2026-02-10: User requirement — all vault candidates must be uploaded to R2 at `vault/{session-id}/` after generation completes.

---

## Blockers

None currently.
