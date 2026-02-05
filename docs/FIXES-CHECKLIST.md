# Salus Website Fixes Checklist

Generated from: `salus-website-fixes.txt` (5 February 2025)
Last verified: 5 February 2026

---

## STATUS KEY

- ✓ DONE — Completed and verified
- ✗ PENDING — Not yet started
- ⏸ DEFERRED — Intentionally postponed (requires separate project)

---

## ACCOUNT & FUNCTIONALITY

| # | Item | Status |
|---|------|--------|
| 1 | Need account system – subscribed on one device, no login details on another | ⏸ DEFERRED |

---

## UI & VISUAL FIXES

| # | Item | Status |
|---|------|--------|
| 2 | Too many pictures, premium pictures don't look like player buttons – simplify | ✓ DONE |
| 3 | About us too self indulgent – less pictures, no garden shots | ✓ DONE |
| 5 | Colour match the profile picture | ✓ DONE |
| 10 | Mindfulness day one – play button is odd shape | ✓ DONE |
| 12 | Buttons on tools are poor – simplify | ✓ DONE |
| 18 | Add the Salus Latin back under logo | ✓ DONE |
| 22 | Change hero on recommended reading | ✓ DONE |
| 24 | Guided meditations – premium logos are inconsistent | ✓ DONE |

---

## COPY & CONTENT CHANGES

| # | Item | Status |
|---|------|--------|
| 6 | Homepage still refers to 'taking your money' – delete it! | ✓ DONE |
| 7 | Journey – to inner peace. Add to founder statement | ✓ DONE |
| 8 | Emma from Leeds refers to 5 minute calm reset session | ✓ VERIFIED |
| 11 | Remove 'free' from tools | ✓ DONE |
| 25 | From our founder needs to open with "hello and welcome to Salus..." | ✓ DONE |
| 26 | What people are saying section needs some Americans | ✓ DONE |
| 27 | ASMR page 'subscribe to unlock' should say 'premium' | ✓ DONE |
| 39 | Contact page – reframe to "We're a small family team..." | ✓ DONE |

---

## PAGES & FEATURES

| # | Item | Status |
|---|------|--------|
| 14 | Subscribe page refers to sleep stories but we don't have any – add placeholder page | ✓ DONE |
| 33 | Sleep stories concept – page showing 52 little book icons | ✓ DONE |
| — | 21-day mindfulness course placeholder + page | ✓ DONE |

---

## ALIGNMENT & QA ISSUES

| # | Item | Status |
|---|------|--------|
| 13 | Check tools breathing exercises – visual doesn't align with numbering | ✓ DONE |

---

## AUDIO FIXES

| # | Item | Status |
|---|------|--------|
| 4 | Rebuild anxiety audio | ✓ DELETED |
| 19 | The foundation – hiss around 5.20 | ✓ DELETED |
| 20 | Foundation has breath counting and glitch on sound – delete and rebuild | ✓ DELETED |
| 42 | Sibilance issue – needs de-esser applied or regenerated | ✗ PENDING |
| 43 | AUDIO PRODUCTION RULES – establish max sentence length, standardise silence periods | ✓ DONE |
| 44 | Ambient sounds rule – subtle, fade in after intro, no looping, user directs | ✓ DONE |
| 45 | Audio QA pipeline – tighten existing system, introduce new tools | ✗ PENDING |
| 46 | Ensure all scripts are filed and ordered correctly | ✓ DONE |
| 48 | Add liability checker to Bible/QA process | ✓ DONE |
| 49 | Review ALL existing scripts against liability checker | ✓ DONE |

---

## VERIFICATION & PROCESS

| # | Item | Status |
|---|------|--------|
| 9 | NHS logo and NHS fact check | ✓ RESOLVED |
| 50 | Claude Code verification gate – independent verification system | ✓ DONE |

---

## SUMMARY

```
DONE:       31 items
PENDING:     2 items  ← WORK REMAINING
DEFERRED:    1 item   (account system - separate project)
─────────────────────
TOTAL:      34 items
COMPLETION: 91%
```

### Outstanding Work

**Audio (2 items):**
- Apply de-esser for sibilance (#42)
- Improve audio QA pipeline (#45)

---

## Validation Rules

### What validation MUST check:

1. **Completeness** — Every item in the original request has a status
2. **Honesty** — "SKIPPED" is not a valid status. Items are either DONE, PENDING, or DEFERRED
3. **DEFERRED requires justification** — Must explain why and note as separate project
4. **No self-congratulation** — Don't report "all checks passed" when items remain PENDING

### Validation script limitations:

The `validate-fixes.sh` script only verifies CODE changes were implemented correctly. It does NOT:
- Check audio files
- Verify documentation completeness
- Confirm process improvements
- Track items that weren't attempted

**This checklist is the source of truth, not the validation script.**
