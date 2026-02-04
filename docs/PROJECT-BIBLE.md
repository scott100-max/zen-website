# Salus Project Bible

This document contains design guidelines, standards, and a record of website amendments.

---

## Design Standards

### Tile/Card Layout Rules
- **Maximum 2 tiles per row** on all screen sizes (site-wide standard)
- Tiles should stack to 1 column on mobile devices
- This ensures readability and prevents layout breaking on smaller screens

### Image Guidelines
- **No people in card/tile images** - use abstract, nature, or texture imagery only
- **No repeating images** - each card/tile must have a unique image site-wide
- Source images from user photo repository when available

### Premium Content Flow
- All premium CTAs must route to the Subscribe page (`apps.html`)
- Never link premium unlock buttons to Newsletter page
- Premium items should display a "Premium" label and navigate to subscribe on click

### Terminology
- Use "Sample" instead of "Free" for sessions/sounds sections
- Avoid references to "app" - Salus is currently web-only
- iOS/Android apps are "coming soon"

---

## Website Amendments

### 4 February 2026 — 16:30 GMT (Initial)

**Issues Completed:**

| # | Page | Change | Status |
|---|------|--------|--------|
| 1 | ASMR (soundscapes.html) | Premium sound cards now match Meditations logic - clicking navigates to Subscribe page | DONE |
| 2 | ASMR | "Subscribe to Unlock" buttons now link to apps.html instead of newsletter.html | DONE |
| 3 | ASMR | Deleted Piano and Singing Bowls from premium sounds | DONE |
| 4 | ASMR | Moved Thunder from Premium to Sample Sounds section | DONE |
| 5 | ASMR | Removed "No account needed" text from section header | DONE |
| 6 | ASMR | Changed "Free Sounds" heading to "Sample Sounds" | DONE |
| 7 | ASMR | Replaced "The Salus app" with "Salus Premium" in CTA section | DONE |
| 8 | Breathing (breathe.html) | Differentiated all 6 breathing techniques with unique timings and descriptions (Resonant 5-5, Box 4-4-4-4, Sleep 4-7-8, Bellows 2-2, Calm 4-4-6, Extended 4-8) | DONE |
| 9 | Subscription (apps.html) | Removed "We're not a corporation — we're a family..." text from CTA banner | DONE |
| 10 | Home (index.html) | Fixed gradient blending - increased height to 180px and added intermediate colour stop for smoother transition to dark footer | DONE |
| 11 | ASMR | Added "History & Science of ASMR" educational section covering origins (2010) and research (Sheffield 2018) | DONE |
| 12 | Site-wide | Card images - see additional update below | IN PROGRESS |
| 13 | FAQ (faq.html) | Added yearly rate (£49.99/year, save 30%) to pricing answer | DONE |
| 14 | FAQ | Fixed device availability to state web-only, iOS/Android coming soon | DONE |
| 15 | FAQ | Deleted offline download FAQ (feature not available) | DONE |
| 16 | FAQ | Deleted Family Plan FAQ (feature does not exist) | DONE |
| 17 | Home + Site-wide | Changed "Why We're Different" grid from 3 columns to 2 columns. Rule added to bible: max 2 tiles per row | DONE |
| 18 | Home/Footer (style.css) | Added mobile centering for newsletter form Join button | DONE |
| 19 | About (about.html) | Removed bold (font-weight:500→400) from "We're here because..." paragraph | DONE |
| 20 | About | Replaced 4 image placeholders with actual photos from Japan collection (founders-garden, scott-ryokan, kinkakuji, scott-temple) | DONE |
| 21 | About | "What We Stand For" section reviewed - kept as informational content. Tiles are decorative values display, no links needed | REVIEWED - KEPT |

---

### 4 February 2026 — 17:00 GMT (Additional)

**Issue 12 - Site-wide Card Image Replacements:**

| Page | Change | Status |
|------|--------|--------|
| index.html | Replaced hero image `meditation-woman-outdoor.jpg` (person) with `japanese-fog.jpg` | DONE |
| index.html | "Why We're Different" cards: replaced hero images with unique session images (zen-stones, forest-path, mountain-mist, moonlight, ocean-waves) | DONE |
| index.html | "What's Inside" cards: replaced hero images with unique session images (lotus, rain-window, sunrise) | DONE |
| apps.html | "What's Inside Premium" cards: replaced hero images with unique session images (lavender, night-stars, breathing-calm, waterfall, aurora) | DONE |
| about.html | "What We Stand For" cards: replaced hero images with unique session images (beach-sunset, first-meditation, moon-clouds) | DONE |
| soundscapes.html | Fixed duplicate Unsplash images: Woodland and Ocean Breeze now use unique images | DONE |
| sessions.html | Changed "Free Sessions" to "Sample Sessions", removed "no account needed" | DONE |
| apps.html | Changed "4 free ASMR sounds" to "4 sample ASMR sounds" | DONE |

**Image Mapping (no duplicates):**

Session images used in cards:
- zen-stones.jpg → index (Family-Run)
- forest-path.jpg → index (Psychologist Reviewed)
- mountain-mist.jpg → index (Reach Us)
- moonlight.jpg → index (40+ Years)
- ocean-waves.jpg → index (Everything Included)
- lotus.jpg → index (Guided Meditations)
- rain-window.jpg → index (ASMR)
- sunrise.jpg → index (Learn)
- lavender.jpg → apps (Guided Meditations)
- night-stars.jpg → apps (Sleep Stories)
- breathing-calm.jpg → apps (Breathing)
- waterfall.jpg → apps (ASMR)
- aurora.jpg → apps (Learn)
- beach-sunset.jpg → about (Evidence-Based)
- first-meditation.jpg → about (Accessible)
- moon-clouds.jpg → about (Human-First)

**Files Modified (this update):**
- `index.html` — Hero image, card images
- `apps.html` — Card images, terminology
- `about.html` — Card images
- `soundscapes.html` — Duplicate image fixes
- `sessions.html` — Terminology
- `docs/PROJECT-BIBLE.md` — Updated

---

*Last updated: 4 February 2026, 17:00 GMT*
