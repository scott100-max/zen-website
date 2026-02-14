# State: Session 03 Full Rebuild (Bible v4.5 + V8)
Last updated: 13 Feb 2026

## Config
- Session: 03-breathing-for-anxiety
- Category: stress (pause profile: 6s/20s/40s)
- Ambient: birds-8hr, -14dB, 30s fade-in / 60s fade-out
- Candidates: 50 per chunk
- Closing chunk: 150ms tail fade
- Script: trigger-word cleaned (0 flags)
- Opening chunk: 37 chars (under 60 limit)

## Progress
| Step | Status | Notes |
|------|--------|-------|
| 1. Wipe old vault | DONE | |
| 2. Dry run (verify chunks) | DONE | 49 chunks, silence boundaries preserved, 35 under 50 chars |
| 3. Generate 50 candidates/chunk | DONE | 2,974 candidates across 49 chunks |
| 4. Auto-picker v8 | DONE | 48/49 pass, 1 unresolvable (c05), 43 high / 2 medium / 3 low confidence |
| 5. Assemble + tail fade | DONE | 150ms tail fade on c48. All 10 QA gates PASSED. Voice: 17.0 min |
| 6. Mix birds-8hr 30s/60s | DONE | -14dB, 30s fade-in, 60s fade-out. Final: 18.0 min |
| 7. Deploy + CDN purge | DONE | MD5 verified: 6719089cca37947c4414545346e902b3 |
| 8. Review page for Scott | DONE | auto-trial-review-v8-rebuild.html |
| 9. Human review R1 | DONE | 33/49 pass (67.3%), 16 hard fails |
| 10. Rechunk R2 (16 chunks) | DONE | 41/49 pass (83.7%) |
| 11. Rechunk R3 (8 chunks) | DONE | 42/49 pass (87.5%) |
| 12. Rechunk R4 (5 chunks) | DONE | 46/49 pass (95.8%) — focused review page |
| 13. Rechunk R5 (2 chunks) | DONE | 47/49 pass (95.9%) — c09 exhausted, c14 contaminated |
| 14. Final deploy | DONE | MD5: 94b354da7f3acb344e1376d8c692ff7a, uploaded to both R2 paths |

## Flagged Chunks
| Chunk | Text | Confidence | Issue |
|-------|------|------------|-------|
| c05 | Let your shoulders drop. Unclench your jaw. | UNRESOLVABLE | All 65 candidates eliminated (cutoff=34, duration=32) |
| c06 | Let your eyes fall shut when you're ready. | low | |
| c12 | Now hold your breath gently. | low | |
| c31 | And a long, slow breath out. | medium | |
| c41 | It won't make everything perfect... | medium | |
| c45 | Wiggle your fingers if you'd like. | low | |
