# Brief: Vault Builder — Full Catalogue Generation

**Date:** 10 February 2026
**Status:** ACTIVE
**Owner:** Claude Code
**Bible version:** v3.8
**Priority:** HIGH — this is the next major production milestone

---

## Objective

Build the permanent production infrastructure for generating, organising, and managing Marco voice vault audio across the entire Salus catalogue. The platform target is **100+ sessions**. The narrator welcome trial (5 chunks, manual process) is the reference implementation. This brief builds the reusable tooling that every session — existing and future — will pass through.

**The vault is now the standard production method for all Salus audio.** Brute-force full-session rebuilds are superseded.

### Scope

| Category | Count | Status |
|----------|-------|--------|
| Scripts currently inventoried | 12 | Ready for pre-processing |
| Deployed sessions without scripts | 6 (05, 06, 07, 08, 11, 29) | Scripts need recovery |
| Total deployed sessions | 18 | |
| Future sessions (target) | 82+ | Scripts to be written |
| **Platform total target** | **100+** | |

The tooling must handle all three categories: pre-processing and vaulting the existing 12, recovering and vaulting the missing 6, and serving as the standard pipeline for every new session going forward.

---

## Pre-Requisites — Script Pre-Processing (DO THIS FIRST)

Before generating any vault candidates, the source scripts must be cleaned. Generating candidates from broken scripts wastes API credits.

**These tasks apply to the current 12 inventoried scripts.** Future scripts must be written to vault-ready standards from the outset (see Phase 5 below).

### Task 0: Script Recovery

6 deployed sessions have no script files in `content/scripts/`: sessions 05, 06, 07, 08, 11, 29.

**Action:** Recover or reconstruct scripts from:
1. Build manifests (contain the text blocks that were sent to Fish)
2. Transcripts in `reference/` directory
3. R2 audio (transcribe using Whisper if no other source exists)

**Output:** Script files in `content/scripts/` following the standard format (header with metadata + text blocks + silence markers). Log the source used for each reconstruction.

**If a script cannot be recovered:** Flag it and move on. These sessions can be vaulted later once scripts are available. Do not block the remaining work.

### Task 1: Silence Format Fix

Scripts 09 (`09-rainfall-sleep-journey`) and 38 (`38-seven-day-mindfulness-day1`) use the old `[X second pause]` format instead of `[SILENCE: X]`. The build pipeline silently skips these as comments, causing adjacent text blocks to merge unintentionally.

**Action:** Find all `[X second pause]` entries in scripts 09 and 38 and convert to `[SILENCE: X]`.

**Verification:** Re-parse the scripts and confirm block count matches the inventory (`vault-chunk-inventory.json`). If block counts change after the fix, update the inventory.

### Task 2: Block Merging (Under 50 Characters)

93 blocks are under 50 characters. Fish produces hiss on very short chunks. These must be merged with adjacent blocks to bring them above 50 characters.

**Rules:**
- Merge short blocks with the FOLLOWING block (not preceding), unless the short block is the last block in a section
- The merged result must not exceed 200 characters (the sweet spot ceiling)
- Do NOT merge across silence boundaries of 5 seconds or more — those are intentional section breaks
- Do NOT merge chunk 0 with chunk 1 — chunk 0 must remain short (under 60 chars) per the cold-start split rule
- 6 blocks under 20 chars (e.g., "And exhale." at 11 chars) are the highest priority for merging

**Output:** Updated script files with merged blocks. Log every merge performed: which blocks, original lengths, merged length, which script.

### Task 3: Block Splitting (Over 300 Characters)

20 blocks exceed 300 characters. Long blocks risk monotone delivery and lower quality scores.

**Rules:**
- Split at natural sentence boundaries
- Each resulting block must be between 50 and 200 characters
- Preserve the text exactly — no rewording, just splitting at full stops, semicolons, or ellipses
- Add appropriate `[SILENCE: X]` between split blocks (use 3s as default, adjust for context)

**Output:** Updated script files with split blocks. Log every split performed.

### Task 4: Inventory Refresh

After all pre-processing (including any recovered scripts from Task 0), regenerate `vault-chunk-inventory.json` from the updated scripts.

**The inventory must contain for each block:**
- `script_id` (e.g., "01-morning-meditation")
- `chunk_index` (position within script, 0-indexed)
- `text` (the exact text content)
- `char_count` (character length)
- `category` (from script header: mindfulness, sleep, stress, etc.)
- `emotion` (from script header, default: calm)
- `is_opening` (true if chunk_index == 0)
- `is_closing` (true if last chunk in script)

**Verification:** Confirm zero blocks under 50 chars (except chunk 0s which may be under 60). Confirm zero blocks over 300 chars. Report total block count and total scripts — this will be larger than the original 487/12 if scripts were recovered in Task 0.

**This inventory format is permanent.** Every future session added to the vault must follow this same schema. The inventory is the single source of truth for what the vault contains.

---

## Phase 1 — Vault Builder Tool (`vault-builder.py`)

### Purpose

Automated generation of N candidate versions per text block via Fish Audio API. Stores all candidates with metadata for later human review.

### Input

- `vault-chunk-inventory.json` (from Task 4 above)
- `.env` file with `FISH_API_KEY`
- Command-line arguments for which script(s) to process

### Generation Parameters

| Parameter | Value |
|-----------|-------|
| Voice ID | `0165567b33324f518b02336ad232e31a` (Marco) |
| Version | `v3-hd` |
| Emotion | Per script header (default: `calm`) |
| Format | WAV |
| Temperature | 0.3 |

### Candidates Per Block

| Block Length | Candidates | Rationale |
|-------------|------------|-----------|
| 0–50 chars (chunk 0 openings only) | 30 | Cold-start + pace filtering needed |
| 50–100 chars | 15 | Fish sweet spot, moderate attempts |
| 100–200 chars | 20 | Longer text needs more attempts |
| 200–300 chars | 25 | Higher difficulty |

### API Rate Limiting

Fish Starter tier: 5 concurrent requests maximum. The builder must:
- Run a maximum of 5 concurrent API calls
- Implement retry with exponential backoff on 429 errors
- Log all API calls (timestamp, chunk_id, attempt number, response status, duration)
- Track cumulative character count for cost estimation

### Scoring

After each candidate is generated, run the existing composite scoring function on it (spectral flux variance + contrast + flatness + HF ratio). Store the score. This score is used ONLY as a pre-filter to identify obviously broken generations — it does NOT determine final selection (human review does that).

**Pre-filter threshold:** Discard candidates scoring below 0.30 (clearly broken audio). Keep everything above 0.30 for human review.

### Tonal Distance

For chunk indices > 0, measure tonal distance against the preceding chunk's best candidate (or vault entry if one already exists). Store the tonal distance value. This helps human reviewers identify candidates that will splice smoothly.

---

## Phase 2 — File Organisation

**This is critical. Every file must be findable, traceable, and never overwritten.**

### Directory Structure

```
content/audio-free/vault/
├── inventory.json                          # Master inventory (all sessions, updated as catalogue grows)
├── generation-log.json                     # Complete API call log (append-only, all sessions)
├── 01-morning-meditation/
│   ├── session-manifest.json               # Per-session metadata
│   ├── c00/                                # Chunk 0
│   │   ├── c00_v00.wav                     # Candidate version 0
│   │   ├── c00_v01.wav                     # Candidate version 1
│   │   ├── ...
│   │   ├── c00_scores.json                 # Scores for all candidates
│   │   └── c00_meta.json                   # Text, char count, duration per candidate
│   ├── c01/
│   │   ├── c01_v00.wav
│   │   ├── ...
│   │   └── c01_scores.json
│   ├── ...
│   ├── picks/                              # Human-selected winners (populated after review)
│   │   ├── c00_pick.wav
│   │   ├── c01_pick.wav
│   │   └── picks.json                      # Which version was picked per chunk
│   ├── review.html                         # Interactive picker page for this session
│   └── final/                              # Assembled output
│       ├── 01-morning-meditation-vault.wav  # Spliced WAV
│       └── 01-morning-meditation-vault.mp3  # Final encoded MP3
├── 03-breathing-for-anxiety/
│   ├── ...
├── ...                                     # Structure repeats for all 100+ sessions
└── 99-future-session/
    ├── ...
```

This structure scales to 100+ sessions. Each session is self-contained — its candidates, picks, review page, and final output all live in one directory. Nothing is shared between sessions except the global inventory and generation log.

### Naming Conventions

| Item | Format | Example |
|------|--------|---------|
| Candidate WAV | `c{XX}_v{YY}.wav` | `c07_v03.wav` (chunk 7, version 3) |
| Score file | `c{XX}_scores.json` | `c07_scores.json` |
| Metadata file | `c{XX}_meta.json` | `c07_meta.json` |
| Picked winner | `c{XX}_pick.wav` | `c07_pick.wav` |
| Review page | `review.html` | Per session directory |
| Final splice WAV | `{session-id}-vault.wav` | `01-morning-meditation-vault.wav` |
| Final MP3 | `{session-id}-vault.mp3` | `01-morning-meditation-vault.mp3` |

Chunk indices are zero-padded to 2 digits. Version indices are zero-padded to 2 digits. This ensures correct alphabetical sorting in file browsers.

### Metadata Files

**`c{XX}_meta.json`** per chunk:
```json
{
  "chunk_index": 7,
  "text": "The exact text of this chunk",
  "char_count": 87,
  "is_opening": false,
  "is_closing": false,
  "candidates": [
    {
      "version": 0,
      "filename": "c07_v00.wav",
      "duration_seconds": 6.23,
      "composite_score": 0.672,
      "tonal_distance_to_prev": 0.00034,
      "generated_at": "2026-02-10T14:23:01Z",
      "api_call_id": "abc123"
    },
    ...
  ]
}
```

**`session-manifest.json`** per session:
```json
{
  "script_id": "01-morning-meditation",
  "total_chunks": 51,
  "category": "mindfulness",
  "emotion": "calm",
  "generated_at": "2026-02-10T14:20:00Z",
  "total_candidates": 765,
  "total_api_calls": 820,
  "total_characters_sent": 42100,
  "estimated_cost_usd": 2.45,
  "generation_time_seconds": 1840,
  "chunks_below_prefilter": 12,
  "status": "CANDIDATES_READY"
}
```

**`generation-log.json`** (global):
```json
{
  "runs": [
    {
      "started_at": "2026-02-10T14:00:00Z",
      "completed_at": "2026-02-10T15:30:00Z",
      "scripts_processed": ["01-morning-meditation"],
      "total_api_calls": 820,
      "total_characters": 42100,
      "total_cost_estimate": 2.45,
      "errors": 3,
      "retries": 5
    }
  ]
}
```

### File Integrity Rules

1. **Never overwrite a candidate.** If regeneration is needed, use the next version number.
2. **Never delete candidates** — even failed pre-filter ones. They contribute to understanding Fish's failure patterns.
3. **All WAV files remain WAV** until the single final MP3 encode step.
4. **Score files are append-only** — new candidates add entries, never replace.
5. **The generation log is append-only** — each run adds a new entry.
6. **All vault data backed up to R2 and git.** A vault generation run is NOT complete until both backups are confirmed:
   - **Audio files (WAV/MP3):** Upload to R2 at `vault/{session-id}/` using wrangler CLI. Every candidate, every pick, every final splice.
   - **Metadata files (JSON):** Commit to git under `content/audio-free/vault/{session-id}/`. Scores, manifests, inventory, generation logs, picks.
   - **Picker pages (HTML):** Commit to git alongside the metadata.
   - No vault data may exist only on the local machine. If the machine dies, everything must be recoverable — audio from R2, metadata and tooling from git.
   - The backup step runs automatically at the end of each session's generation, not as a manual afterthought.

---

## Phase 3 — Interactive Picker Pages

### Purpose

HTML pages that present all candidate versions for human selection. One page per session. Based on the narrator welcome trial picker (`content/audio-free/vault-candidates/review.html`).

### Requirements

Each picker page must have:

1. **Per-chunk section** with:
   - The text content displayed
   - Character count and chunk index
   - Audio player for every candidate version
   - Composite score displayed (as reference only, with clear "pre-filter only" label)
   - Duration displayed per candidate
   - Tonal distance to previous chunk displayed (for chunks > 0)
   - **PICK** button and **X** (reject) button per candidate
   - Visual highlight on picked candidate (green border)
   - Notes text box per chunk

2. **Session-level controls:**
   - "Export Picks" button → writes `picks.json` to the picks/ directory
   - Progress indicator: X/Y chunks picked
   - "Play All Picks" button → plays selected candidates in sequence with 8s gaps
   - Filter: show all / show unpicked only / show chunk 0 openings only

3. **Candidate ordering:**
   - Default: by composite score (highest first) — helps human start with the most likely candidates
   - Toggle: by duration (for pace-sensitive chunks)
   - Toggle: by tonal distance (for splice-sensitive chunks)

4. **Audio file access:**
   - Picker pages must work with local file paths (for Scott reviewing on his machine)
   - Also must work with R2 URLs (for remote review via uploaded candidates)
   - Use a configurable base path at the top of the page

### Chunk 0 Openings — Special Handling

For chunk 0 of each session (opening chunks), the picker page must additionally show:
- Duration prominently (pace is critical for openings)
- A target duration range field (Scott enters the desired range)
- Visual flagging of candidates outside the target range
- Sort-by-duration as the default sort for chunk 0 sections

---

## Phase 4 — Assembly Tool

### Purpose

Splice human-picked candidates into a complete session audio file.

### Process

1. Read `picks.json` from the session's `picks/` directory
2. Copy each picked WAV to `picks/c{XX}_pick.wav`
3. Apply 15ms cosine edge fades to each chunk
4. Insert silence pauses between chunks (durations from the script's `[SILENCE: X]` markers, processed through `humanize_pauses()`)
5. Concatenate all chunks + silences (WAV)
6. Whole-file loudnorm: `loudnorm=I=-26:TP=-2:LRA=11`
7. Output as WAV to `final/{session-id}-vault.wav`
8. Encode to 128kbps MP3: `final/{session-id}-vault.mp3`
9. Run all 14 QA gates on the final narration WAV
10. Generate build report

### Ambient Mix

The assembly tool does NOT apply ambient. Ambient mixing is a separate step (per existing pipeline) applied after human review of the vault splice confirms clean narration.

---

## Phase 5 — New Session Workflow (Ongoing)

### Purpose

Establish the vault as the standard pipeline for every new session. This is not a one-off process — it must work smoothly for sessions 19 through 100+.

### New Session Lifecycle

```
1. Script written (by Code or human)
     ↓
2. Pre-flight checks (block sizes, silence format, originality scan — per Bible Section 13/13A)
     ↓
3. vault-builder.py generates candidates for all chunks
     ↓
4. Picker page generated automatically
     ↓
5. STOP — Scott reviews picker page, selects winners
     ↓
6. Assembly tool splices picks → narration WAV
     ↓
7. 14 QA gates on narration
     ↓
8. STOP — Scott listens to final splice (human review, mandatory)
     ↓
9. Ambient mix (per session requirements)
     ↓
10. Deploy to R2 + update HTML + register updates
     ↓
11. Email notification
```

### Script Standards for Vault-Ready Scripts

New scripts must be written to vault-ready standards from the outset. No pre-processing should be needed:

- **All blocks between 50 and 200 characters** (the Fish sweet spot)
- **Chunk 0 under 60 characters** (cold-start split rule)
- **Silence markers in `[SILENCE: X]` format only** (no old-style `[X second pause]`)
- **No blocks under 20 characters** — merge short cues with adjacent blocks during scripting
- **No blocks over 300 characters** — split at sentence boundaries during scripting
- Originality scan against registers before generation begins

### Vault Builder Integration

`vault-builder.py` must accept a single script path as input and run the full candidate generation for that session only. This is the standard mode for new sessions. The batch mode (processing multiple scripts) is for the initial catalogue backfill only.

```bash
# New session (standard)
python3 vault-builder.py content/scripts/55-new-session.txt

# Batch (catalogue backfill only)
python3 vault-builder.py --batch content/scripts/
```

---

## Execution Order

```
1. Script pre-processing (Tasks 0-4)           ← DO FIRST
2. Vault builder tool (Phase 1)                 ← Build the tool
3. Test run: session 52 (The Court of Your Mind) ← Stress test — 60 chunks, 10,350 chars, biggest session in the inventory
4. Scott reviews test session picker page       ← Human validates the workflow at scale
5. STOP — await approval before proceeding
6. Generate remaining inventoried sessions      ← Batch run on current catalogue
7. Interactive picker pages (Phase 3)           ← Generate all pages
8. Assembly tool (Phase 4)                      ← Build the splice tool
9. Confirm new-session workflow (Phase 5)       ← Verify single-session mode works end-to-end
```

**STOP after Step 3.** Do not proceed to the full batch run until Scott has reviewed the session 52 picker page and confirmed the workflow is satisfactory. Session 52 is the hardest test in the catalogue (60 chunks, longest script, most varied content). If the tooling and candidate quality pass muster here, the remaining sessions are lower risk. This is a STOP rule per Bible Section 17.

**Estimated test run (session 52 only):** ~1,200 API calls | ~£3 | ~25 minutes generation time.

**STOP after Step 6.** Email Scott with a summary of the batch run (total candidates generated, total cost, any failures or blocks that never hit the pre-filter threshold). Do not proceed to assembly until Scott has reviewed at least one session's picks.

---

## State File

Create `docs/state-vault-builder.md` as your first action on receipt of this brief. Track all progress there.

---

## Non-Negotiable Rules (from Bible)

- ONE build session at a time (no parallel Fish API usage across tools)
- All intermediate audio is WAV — MP3 only at the final encode step
- Never overwrite raw files — version everything
- Never commit audio to git — vault WAVs go to R2, metadata and picker pages go to git
- **All vault data must be backed up before a generation run is considered complete** — audio to R2, metadata to git. Nothing local-only.
- Composite scores are pre-filters, NOT final selection criteria
- Human review is mandatory before any vault session is deployed
- Email scottripley@icloud.com on completion of each phase
- Do NOT modify the Bible or this brief — report issues and wait
- Do NOT use atempo on any Fish output — use pace filtering for pace-sensitive chunks

---

## Success Criteria

### Immediate (Current Catalogue)
1. All inventoried blocks have candidates generated (after pre-processing adjusts the count)
2. Every candidate has a WAV file, composite score, and metadata entry
3. Every session has an interactive picker page
4. Assembly tool can splice picks into a final session audio
5. File organisation matches the directory structure specified above exactly
6. Generation log accounts for all API calls and estimated costs
7. Zero blocks remain under 50 chars or over 300 chars in the processed inventory

### Ongoing (Platform Infrastructure)
8. `vault-builder.py` works in single-session mode for new scripts
9. New session workflow (Phase 5) runs end-to-end without manual intervention (apart from the two human STOP points)
10. A new session can go from finished script to picker-page-ready in under 30 minutes of compute time
11. All tooling is documented in the state file sufficiently for context recovery after compaction

---

**End of brief.**
