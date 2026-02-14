# Salus Project Bible

**Version:** 4.2
**Updated:** 12 February 2026
**Purpose:** Single source of truth for all Salus website and audio production standards

This document is the canonical reference for Claude Code and all contributors. Where this document conflicts with earlier briefs, amendment logs, or conversation history, **this document wins**.

---

## Contents

### Part A ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Website & Infrastructure
1. [Design Standards](#1-design-standards)
2. [Terminology](#2-terminology)
3. [Deployment & Infrastructure](#3-deployment--infrastructure)
4. [Authentication & Payments](#4-authentication--payments)
5. [SEO](#5-seo)
6. [Self-Validation Process](#6-self-validation-process)
7. [Common Issues & Lessons Learned](#7-common-issues--lessons-learned)

### Part B ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Audio Production
8. [Production Rules (Non-Negotiable)](#8-production-rules-non-negotiable)
9. [TTS Providers](#9-tts-providers)
10. [Marco Master Voice Specification](#10-marco-master-voice-specification)
11. [Audio Processing Pipeline](#11-audio-processing-pipeline)
12. [QA Gate System](#12-qa-gate-system)
13. [Script Writing Rules](#13-script-writing-rules)
13A. [Script Uniqueness & Cross-Session Differentiation](#13a-script-uniqueness--cross-session-differentiation)
14. [Expression Through Punctuation](#14-expression-through-punctuation)
15. [Auphonic Integration](#15-auphonic-integration)
15A. [Production Readiness](#15a-production-readiness)
16. [Build Execution](#16-build-execution)
16A. [Chunk Repair Pipeline](#16a-chunk-repair-pipeline)
16B. [Echo Detection](#16b-echo-detection)
16C. [Vault Production System](#16c-vault-production-system)
16D. [Vault Production Workflow](#16d-vault-production-workflow)
16E. [Auto-Picker](#16e-auto-picker)
17. [Governance](#17-governance)
18. [V3 API Emotion System](#18-v3-api-emotion-system)

### Part C ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Historical Record
19. [Amendment Log](#19-amendment-log)

### Part D Ã¢â‚¬â€ Ledger
20. [Action Ledger](#20-action-ledger)

---

# PART A ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â WEBSITE & INFRASTRUCTURE

---

## 1. Design Standards

### Tile/Card Layout Rules
- **Maximum 2 tiles per row** on all screen sizes (site-wide standard)
- Tiles stack to 1 column on mobile devices
- No coloured gradient tiles/boxes on cards ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â use simple white cards with text only

### Image Guidelines
- **No people in card/tile images** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â use abstract, nature, or texture imagery only
- **No repeating images** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â each card/tile must have a unique image site-wide
- Source images from user photo repository when available
- Large images (>1MB) cause browser rendering issues ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â optimise to 600ÃƒÆ’Ã¢â‚¬â€600px for web
- Always add cache-buster: `?v=YYYYMMDD`

### Card Design Patterns
- **Atmospheric cards** (Sessions, Tools, Education): Full gradient backgrounds with category colours, floating glowing orbs (`filter:blur(40px)`, `opacity:0.4-0.5`), white text on dark backgrounds
- **Glassmorphism elements**: `backdrop-filter:blur(10px)`, `rgba(255,255,255,0.15)` backgrounds, deep coloured shadows

### Category Colour Scheme
| Category | Primary Gradient | Orb Colours |
|----------|-----------------|-------------|
| Beginners/Teal | #0d3d4a ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ #1a5568 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ #0f4c5c | #06b6d4, #22d3ee |
| Stress/Green | #064e3b ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ #065f46 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ #047857 | #10b981, #34d399 |
| Sleep/Purple | #1e1b4b ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ #312e81 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ #3730a3 | #818cf8, #a78bfa |
| Focus/Amber | #451a03 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ #78350f ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ #92400e | #f59e0b, #fbbf24 |

### Dark Theme (Complete ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 8 Feb 2026)
- All pages fully dark-themed: body `#0a0a12`, text `#f0eefc`
- `css/style.css` `:root` includes: `--deep`, `--teal`, `--text-bright`, `--text-muted`, `--text-mid`
- Auth alert colors use dark-compatible rgba (e.g. `rgba(239,68,68,0.12)` not `#fee2e2`)
- No light backgrounds, no `var(--white)` or `var(--off-white)` in visible elements

### Unified Footer (Complete ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 8 Feb 2026)
- All pages use `hb-footer` class (4-column: Brand/tagline, Practice, Discover, Salus)
- CSS in `style.css`, responsive: 2-col at 900px, 1-col at 480px
- Subdirectory pages (`sessions/`, `articles/`, `newsletters/`) use `../` prefix on links
- Health disclaimer in every footer
- Copyright: "&copy; 2026 Salus Mind. All rights reserved."

### Section Background Blending
- Use `background:transparent` for sections (inherits dark body)
- Subtle differentiation via `rgba(255,255,255,0.03)` backgrounds
- Avoid hard colour lines between sections

### Premium Content Flow
- All premium CTAs route to the Subscribe page (`apps.html`)
- Never link premium unlock buttons to Newsletter page
- Premium items display a "Premium" label and navigate to subscribe on click

### Navigation
- Two-row layout applied site-wide
- Row 1: Sessions, Mindfulness, ASMR, Sleep Stories, Learn, About
- Row 2: Tools, Reading, Applied Psychology, Newsletter, Contact (smaller, gray text, `gap:32px`, `font-size:0.9rem`)
- Latin phrase: "SalÃƒâ€¦Ã‚Â«s ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Latin: health, safety, well-being" under hero sections on all pages
- Light backgrounds: `color:var(--mid-gray);opacity:0.7`
- Dark/hero backgrounds: `color:rgba(255,255,255,0.6)`

### Image Mapping (no duplicates site-wide)

| Image | Location |
|-------|----------|
| japanese-fog.jpg | index (hero) |
| zen-stones.jpg | index (Family-Run) |
| forest-path.jpg | index (Psychologist Reviewed) |
| mountain-mist.jpg | index (Reach Us) |
| moonlight.jpg | index (40+ Years) |
| ocean-waves.jpg | index (Everything Included) |
| lotus.jpg | index (Guided Meditations) |
| rain-window.jpg | index (ASMR) |
| sunrise.jpg | index (Learn) |
| lavender.jpg | apps (Guided Meditations) |
| night-stars.jpg | apps (Sleep Stories) |
| breathing-calm.jpg | apps (Breathing) |
| waterfall.jpg | apps (ASMR) |
| aurora.jpg | apps (Learn) |
| beach-sunset.jpg | about (Evidence-Based) |
| first-meditation.jpg | about (Accessible) |
| moon-clouds.jpg | about (Human-First) |

---

## 2. Terminology

| Use | Do Not Use |
|-----|-----------|
| Sample | Free (for sessions/sounds sections) |
| Salus Premium | The Salus app |
| Premium | Subscribe to Unlock |
| Web-only, iOS/Android coming soon | Available on all devices |
| New material unlocked each week | New story every week |

---

## 3. Deployment & Infrastructure

### Architecture
| Service | What it hosts | URL |
|---------|--------------|-----|
| **GitHub Pages** | Website code (HTML, CSS, JS, small images) | `https://salus-mind.com` |
| **Cloudflare R2** | Media files (MP3, MP4) | `https://media.salus-mind.com` |
| **Cloudflare** | DNS for entire domain | Nameservers: `gerald.ns.cloudflare.com`, `megan.ns.cloudflare.com` |

### GitHub Pages
- **Repository:** `https://github.com/scott100-max/Salus-Website.git`
- **Branch:** `main`
- **Auto-deploys** on push within 1-2 minutes

```bash
git add <files>
git commit -m "Description"
git push origin main
```

**Shortcut:** `cpd` = commit, push, and deploy audio to R2 in a single command. Handles all three steps (git commit + git push + wrangler R2 upload). Use for routine deployments where HTML changes and audio uploads happen together.

### Cloudflare R2 (media files)
- **Bucket:** `salus-mind`
- **Account ID:** `e798430a916680159a81cf34de0db9c2`
- **Custom domain:** `media.salus-mind.com` (proxied through Cloudflare CDN)
- **Public dev URL:** Disabled ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â use custom domain only
- **API token** (Edit zone DNS): `yYNUa2enwfPdNnVrfcUQnWHhgMnebTSFntGWbwGe`
- **CORS:** Configured for `https://salus-mind.com` and `https://www.salus-mind.com` (GET/HEAD). Required for cross-origin audio playback from `media.salus-mind.com`.

```bash
# Upload via wrangler CLI:
npx wrangler r2 object put salus-mind/content/audio-free/FILENAME.mp3 --file=./FILENAME.mp3

# Or drag-and-drop in Cloudflare dashboard: R2 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ salus-mind ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Objects ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Upload
```

**File paths in R2:**
- Free audio: `content/audio-free/`
- Sounds (ASMR): `content/sounds/`
- Video: `content/video/`
- Reference: `reference/` (marco master etc.)

### Cloudflare CDN Cache Purge

| | |
|---|---|
| **Purpose** | Purge stale cached content from Cloudflare CDN after R2 uploads |
| **Token** | `8XAFM9HRU8FwrEsfso10pKtOfUqckWF0Am8UWMny` |
| **Permission** | Zone > Cache Purge > Purge (salus-mind.com only) |
| **Zone ID** | `5322a6fb271fa30c2b910369e10d7aab` |
| **Env vars** | `CF_CACHE_PURGE_TOKEN` and `CF_ZONE_ID` in `.env` |

**Usage:** After every R2 upload, purge the specific URL:

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${CF_CACHE_PURGE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"files":["https://media.salus-mind.com/PATH_TO_FILE"]}'
```

Must be integrated into: vault-assemble.py deploy step, any R2 upload workflow, and the `cpd` shortcut.

**Evidence:** Narrator-welcome session served stale audio from CDN after R2 upload until manual purge was performed.

### Verdicts API

| | |
|---|---|
| **Endpoint** | `PUT/GET /verdicts/{session-id}` at `vault-picks.salus-mind.com` |
| **Storage** | R2 at `vault/{session}/verdicts/verdicts.json` |
| **Auth** | Bearer `salus-vault-2026` (same as picks API) |
| **Purpose** | Stores human review verdicts with severity labels (HARD FAIL / SOFT FAIL / PASS + defect tags) |
| **Used by** | Review page generator, auto-picker (loads verdict history to inform selection) |

**ASMR sounds:**
- All ASMR audio is user-provided (downloaded from YouTube, cut to 1 hour each). Not procedurally generated.
- 14 sounds: rain, ocean, forest, thunder, birds, fire, stream, cafe, garden, library, night, temple, waterfall, white noise
- 1-hour cuts stored locally in `content/audio-free/` (e.g. `asmr-stream.mp3`)
- Short clips on R2 at `content/sounds/` for ASMR page playback
- Full-length YouTube source downloads in `content/audio/ambient/youtube-downloads/`

**Media references in HTML ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â two player types:**

Sessions page (`sessions.html`) and session detail pages use `custom-player` (wired by `main.js`):
```html
<div class="custom-player" data-src="https://media.salus-mind.com/content/audio-free/FILENAME.mp3">
```

Mindfulness page (`mindfulness.html`) uses `m-player` (wired by inline JS on that page):
```html
<div class="m-player" data-src="https://media.salus-mind.com/content/audio-free/FILENAME.mp3">
```
Cards without `data-src` show a visual-only player (no audio loaded). Add `data-src` when audio is produced.

### Domain & DNS
- **Registrar:** reg-123 (salus-mind.com), GoDaddy (salus-mind.co.uk)
- **DNS managed by:** Cloudflare (migrated 6 February 2026 from GoDaddy)
- **Registrar holds nameservers only** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â all records in Cloudflare dashboard
- GitHub Pages A records: `185.199.108-111.153`
- `www` CNAME ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `scott100-max.github.io`
- `media` CNAME ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ R2 bucket (proxied)

### Large Files
- **NEVER commit audio/video files to git** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â all media goes to Cloudflare R2
- `.gitignore` excludes `*.mp3`, `*.mp4`, `*.wav`, and media directories

### File Organisation

| Directory | Contents |
|-----------|----------|
| `scripts-archive/` | Old/superseded build scripts |
| `reference/` | Competitor analysis, voice-clone experiments, branding, transcripts |
| `test/` | Test files, audio reports, test HTML pages |
| `docs/` | PROJECT-BIBLE, audio quality analysis, stripe links |
| `content/audio/ambient/` | Ambient tracks (8-hour versions preferred) |
| `content/audio/marco-master/` | Master reference WAVs and measurements |
| `auto-picker.py` | v7 auto-picker (root — alongside vault-builder.py) |
| `sweep-weights.py` | Weight sweep tool (230+ combinations across 5 phases) |
| `tools/review-page-generator.py` | Standard review page template with severity, auto-advance, keyboard shortcuts |
| `docs/auto-picker-validation.json` | v7 final validation (245 chunks, 10 sessions) |
| `docs/weight-sweep-results.json` | Weight sweep phases 1–3 data |
| `docs/weight-sweep-phase4.json` | Tonal/hiss sweep data |

**Root should only contain:** HTML pages, `build-session-v3.py`, `audition-voices.py`, `label-server.py`, `score-chunks-whisper.py`, `echo-detector.py`, `CNAME`, `robots.txt`, `sitemap.xml`, `package.json`.

### Label Server

| | |
|---|---|
| **Script** | `label-server.py` |
| **Port** | localhost:8111 |
| **Purpose** | Receives human review verdicts from the chunk review HTML pages and saves them as standard CSV to `reference/human-labels/` |
| **Endpoints** | POST `/verdict` (individual rating), POST `/sync` (bulk sync from review page), GET `/health` (status check) |
| **Auto-save** | Review pages auto-POST on every rating when the server is running. Session 52+ pages also auto-sync on page load. |
| **CSV format** | `chunk,session,verdict,notes,text,audio_url,score,flagged,timestamp` |
| **Storage** | `reference/human-labels/{session-id}-labels.csv` (git, not R2) |
| **Deduplication** | Updates by chunk number, not appends |

**Usage:** Run `python3 label-server.py` before opening review pages. The server must be running for labels to persist. Historical review pages (pre-session 52) require a one-time "Sync to Label Server" button click to migrate localStorage data.

**Labels must never require manual export.** If `reference/human-labels/` is empty or incomplete after a review session, the label pipeline is broken and must be fixed before any downstream work (echo detection, scorer calibration) proceeds.

### Workflow Summary
| Task | Action |
|------|--------|
| Edit HTML/CSS/JS | Change files ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `git push` |
| Add new audio/video | Upload to R2 ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ reference in HTML ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `git push` |
| Add new HTML page | Create page ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ add to sitemap.xml ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ add to nav on ALL pages ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `git push` |

### Deployment Verification
- GitHub Pages auto-deploys on push to main
- Check `gh run list --limit 3` for deployment status
- Always verify live URL after claiming changes are deployed
- Use `WebFetch` to confirm live site content matches expectations

---

## 4. Authentication & Payments

### Supabase

| File | Purpose |
|------|---------|
| `/js/supabase-config.js` | Client initialisation |
| `/js/auth.js` | Auth module: signUp, signIn, signOut, isPremium, updateNavUI |
| `/login.html` | Email/password login |
| `/signup.html` | Registration |
| `/dashboard.html` | Account overview, subscription status |
| `/reset-password.html` | Password reset flow |
| `/supabase/functions/stripe-webhook/index.ts` | Stripe payment event handler |
| `/supabase/migrations/001_create_auth_tables.sql` | Database schema |

**Credentials:**
- **Project URL:** `https://egywowuyixfqytaucihf.supabase.co`
- **Project ID:** `egywowuyixfqytaucihf`
- **IMPORTANT:** Use the **Legacy** JWT anon key (starts with `eyJ...`), NOT the new `sb_publishable_` format

**Database Tables:**
- `profiles` ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â User data (auto-created on signup via trigger)
- `subscriptions` ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Stripe data (user_id, stripe_customer_id, status, plan_type)

**Premium Logic (in order):**
1. Check Supabase `subscriptions` table for active subscription (cross-device)
2. Fall back to localStorage `salus_premium` (legacy/single-device)
3. Migration banner prompts localStorage-only users to create accounts

### Stripe

**Webhook endpoint:** `https://egywowuyixfqytaucihf.supabase.co/functions/v1/stripe-webhook`

**Events handled:**
- `checkout.session.completed` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Create subscription
- `customer.subscription.updated` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Update status
- `customer.subscription.deleted` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Mark expired
- `invoice.payment_succeeded` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Renew period
- `invoice.payment_failed` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Mark past_due

**Auth Flow:**
1. User signs up ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Supabase creates `auth.users` + `profiles` record
2. User logs in ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Redirected to dashboard (or original page via `?redirect=` param)
3. User subscribes ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Stripe checkout includes `client_reference_id={user_id}`
4. Payment completes ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Webhook creates `subscriptions` record
5. User logs in anywhere ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `SalusAuth.isPremium()` returns true

**Business name:** Salus (changed from "zenscape")

**Tech Notes:**
- Supabase CLI installed via Homebrew
- Edge functions deployed with `--no-verify-jwt` flag for webhooks
- Secrets: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

---

## 5. SEO

- **Google Search Console:** Verified via HTML file (`googleaba2f038193703b2.html`)
- **Sitemap:** `https://salus-mind.com/sitemap.xml` (76 URLs)
- **Canonical tags:** All 75 public HTML pages
- **Open Graph + Twitter cards:** All 75 public HTML pages
- **Default OG image:** `https://salus-mind.com/images/japanese-fog.jpg`
- **robots.txt:** Points to sitemap at `salus-mind.com`

**Excluded from SEO tags:** dashboard.html, login.html, signup.html, reset-password.html, test-audio-player.html, thank-you.html, content/* (internal pages)

---

## 6. Self-Validation Process

### CRITICAL: Validation Must Check FULL Request, Not Just Completed Work

**Lesson learned (5 Feb 2026):** Self-validation reported "16/16 passed" while 11 items remained unresolved. The validation only checked work that was done, not work that was requested.

### Validation Rules
1. **Source of truth:** `docs/FIXES-CHECKLIST.md` ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not the validation script
2. **No "SKIPPED" status:** Items are DONE, PENDING, or DEFERRED (with justification)
3. **DEFERRED requires approval:** Only for items needing separate project scope
4. **Report honestly:** State completion percentage against FULL original request
5. **Pending items must be listed:** Every report must show outstanding work

### Two-Stage Validation

**Stage 1: Code Verification** (`validate-fixes.sh`)
Checks code changes were implemented correctly. Does NOT confirm all requested work is complete.

**Stage 2: Checklist Verification** (manual)
1. Open `docs/FIXES-CHECKLIST.md`
2. Compare against original request
3. Confirm every item has accurate status
4. Calculate true completion percentage
5. List all PENDING items in final report

### Final Report Format

```
COMPLETION REPORT
ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬ÂÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â
Done:     X items
Pending:  Y items  ÃƒÂ¢Ã¢â‚¬Â Ã‚Â WORK REMAINING
Deferred: Z items

Completion: XX%

Outstanding:
- Item description (#number)
- Item description (#number)
```

### Independent Verification

Code self-certification is unreliable. After every Code task batch:
1. Open a SEPARATE Claude conversation (not Code)
2. Provide: (1) the original brief, (2) Code's completion report
3. Second Claude independently verifies each item against the actual site/files/code
4. Any discrepancy flagged before sign-off
5. Treat Code like a subcontractor ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â never let the person who did the work also sign it off

---

## 7. Common Issues & Lessons Learned

### Page Visibility Checklist
When creating any new page:
1. Add to navigation on ALL HTML files (~70 root + 44 sessions)
2. Add to homepage "What's Inside" section if it's a main content type
3. Add to relevant footer sections
4. Verify at least one link exists before marking complete

```bash
# Root pages nav update:
sed -i '' 's|Guided Meditations</a></li>|Guided Meditations</a></li>\n        <li><a href="NEW-PAGE.html">New Page</a></li>|' *.html
# Session pages (use ../ prefix):
sed -i '' 's|../sessions.html">Guided Meditations</a></li>|../sessions.html">Guided Meditations</a></li>\n        <li><a href="../NEW-PAGE.html">New Page</a></li>|' sessions/*.html
```

### Sleep Stories
- Page at `/sleep-stories.html` (Coming Soon)
- 52-book library preview: weeks 1-4 "available", 5-52 locked
- Books display in 6-column grid with 3D book effect
- NOT in main navigation

### Education Tiles
- White card backgrounds with shadow
- Gradient header with centred icon in frosted glass circle
- "Click to read" button with arrow icon
- Hover: `scale(1.02)`, increased shadow, icon scales 1.1

### Tools Tiles
- Grid: `align-items:stretch`
- Links: `display:flex`
- Inner divs: `flex:1;display:flex;flex-direction:column`

### QA Gate Failure Pattern (7 February 2026)

**Pattern:** Code builds tooling that produces quality data (visuals, reports, metrics) without building tooling that acts on it (decision logic, thresholds, fail conditions). Builds pass because no gate evaluates the evidence. Human review catches what the pipeline should have caught.

**Incidents:**
- 4 Feb: Rainfall Sleep Journey ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â analyser reported PASS on a file with voice changes, repeated content, and hiss
- 7 Feb: Loving-kindness ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 9 gates passed on a file with audible hiss spike at 0:30 and catastrophic hiss wall from 12:00, both visible on Auphonic and Gate 9 visuals

**Prevention:** All gates must be pass/fail. No informational-only gates. Visual analysis must include programmatic evaluation, not just image generation.

**ASMR slider mobile touch issues (12 Feb 2026):** Volume slider on ASMR cards was unusable on mobile — browser hijacked touch drags for scrolling. Fix: `touch-action: none` on slider, larger thumb (14px → 22px), `touchmove`/`touchend` stopPropagation, `change` event listener for iOS Safari.

**ASMR slider iPhone fix (14 Feb 2026):** Volume slider still non-functional on iPhone specifically. Root cause: iOS native range input unreliable during CSS transitions, and touch events fired after touch ended. Fix: (1) `@media (hover: none) and (pointer: coarse)` rule to always show slider row on touch devices with `transition: none` to prevent overflow clipping, (2) guard against zero-width bounding rect during CSS transitions, (3) `sliderTouching` flag to discard stale touchmove events after touchend, (4) stopPropagation on slider row touchstart/click to prevent accidental play/pause toggle when adjusting volume.

---

# PART B ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â AUDIO PRODUCTION

---

## 8. Production Rules (Non-Negotiable)

1. **ONE build at a time.** Never run builds in parallel ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â burned 100K credits once.
2. **Always dry-run first.** Check block count and silence totals before spending credits.
3. **Fish has a ~60% rebuild rate on 45-min stories.** This is expected. Rebuild until it lands.
4. **Never identical gaps.** All pauses go through `humanize_pauses()`.
5. **Marco is the only voice.** Do not audition alternatives unless Marco is discontinued.
6. **QA is two-stage.** The pipeline runs 14 automated gates, then human review is MANDATORY before deploy. Automated gates catch measurable defects; human listening catches what metrics miss. Neither stage alone is sufficient. Use `--no-deploy` to hold builds for review.
7. **Deploy after human review.** Default build mode is `--no-deploy`. Build runs ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ 14 gates ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ human review ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ only then deploy to R2. Automatic deploy (without `--no-deploy`) is available but should only be used for re-deploys of already-reviewed sessions.
8. **Email is mandatory.** Every completed build cycle ends with an email to scottripley@icloud.com ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â pass or fail.
9. **Fully autonomous** (except where a STOP rule is triggered ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â see [Section 17](#17-governance)).
10. **No OneDrive.** All files go to git (code) or Cloudflare R2 (media). Never copy files to OneDrive.
11. **No post-build splicing Ã¢â‚¬â€ with one exception.** Never splice individual chunks into an existing build during normal production Ã¢â‚¬â€ splicing causes tonal seams at splice boundaries (tested and failed). Selective regeneration WITHIN a build is permitted: `--focus-chunks` gives problem chunks more generation attempts (best-of-10) while others get best-of-5. **Exception: the Chunk Repair Pipeline (Section 16A)** permits targeted splice repair of deployed sessions under controlled conditions: 100ms cosine crossfade, speechÃ¢â€ â€™silence boundary targeting, tonal distance measurement, and mandatory human A/B review before promotion to live. This exception exists because full rebuilds risk introducing new defects in currently-clean chunks. The repair pipeline was validated on 9 Feb 2026 (session 32 chunk 1).
12. **Automated gates: 100% pass required.** All 14 gates must pass ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no exceptions. Human review: accept a reasonable clean rate and ship. Perfection should not prevent shipping, but the clean rate and any flagged chunks must be documented in the build record. If a session ships below 100% human clean rate, the specific issues accepted are logged for future pipeline improvement.
13. **Lossless pipeline.** All intermediate audio MUST be WAV. MP3 encoding happens exactly ONCE at the final step.
14. **Never overwrite raw narration.** Raw narration WAVs must be preserved before any processing that modifies them. Save timestamped copies: `{session}_raw_v1.wav`, `{session}_raw_v2.wav` etc. If any cleaning service is applied, both pre-clean and post-clean versions must be saved to `content/audio-free/raw/`. Never leave raw files in temp directories, never overwrite without preserving the original.
15. **All audio comparisons must be narration-only.** When evaluating audio quality differences (A/B testing, pipeline changes), always compare raw narration without ambient. Ambient masks differences and makes evaluation invalid. Both A and B files must be provided simultaneously with clear naming.
16. **Garden ambient offset.** `garden-8hr.mp3` has 9.5 seconds of dead digital silence at the file start. Always use `-ss 10` when mixing garden ambient. This is automated in `build-session-v3.py` for Fish mix path (confirmed 9 Feb 2026).

20. **CDN cache purge after every R2 upload.** Cloudflare CDN caches media.salus-mind.com aggressively. After uploading any file to R2, immediately purge the specific URL. See Section 3 for token and curl command. Evidence: narrator-welcome session served stale audio until manual purge.

21. **Ambient is mandatory for all sessions.** All sessions MUST be mixed with ambient before final review and deployment. Grace ambient (or similar warm tonal pad) at −14 dB below voice, **15s fade-in, 8s fade-out** (unchanged from existing Bible spec — Section 11). Ambient effectively masks mild echo, hiss, and transition artefacts — turns ~80% raw pass rate into ~96% perceived pass rate. Echo tolerance relaxed: mild echo marked OK (not soft fail) when ambient is present. This is not optional. **The fade values are locked. Do not modify without a Bible amendment.** Code deployed sessions with 0s fade-in on 12 Feb — this is a critical spec violation.

22. **Fish split threshold is 150 characters (lowered from 300).** Chunks exceeding 150 characters get systematically truncated by Fish. The vault-builder's preprocessing step must split at sentence boundaries before generation. Evidence: 9 persistent-fail chunks in session 01 trial — 5 of 9 were >150 chars with 78–82% cutoff rates. Already implemented in vault-builder.py.

23. **Known-pass versions are sacred.** Human-confirmed clean versions bypass ALL automated filters in future picker runs. Store pass/fail/severity in verdict history, load on every picker run. A candidate rated EXCELLENT by human ears is never re-eliminated by automated metrics, regardless of its composite score. Evidence: session 01 c01 v10 (composite 0.263, below 0.30 floor) was EXCELLENT by ear — the composite floor would have killed it.

24. **UNRESOLVABLE chunks require script-level fix.** When the auto-picker eliminates all candidates for a chunk, it is UNRESOLVABLE. Do not silently fall back to the lowest-scoring candidate. Flag for script revision: split text at sentence boundary, regenerate. Evidence: session 09 had 3 unresolvable chunks (c21, c35, c42) — all were text-level failures.

25. **Audio processing parameters are locked to Bible values.** Fade durations, loudnorm targets, ambient levels, edge fade lengths, and all other numeric audio parameters documented in the Bible must not be modified by Code without an explicit Bible amendment. Any deviation requires Scott's approval via a brief. Evidence: Code changed ambient fade-in from 15s (Bible spec) to 10s to 0s across 12 Feb deploys — three successive deviations from spec, each uncaught because no post-deploy verification existed.

---

## 9. TTS Providers

### Provider Routing

```
Fish Audio is the ONLY TTS provider.
Resemble AI was evaluated and used for early builds but is removed from the pipeline as of 12 Feb 2026.
All sessions — short-phrase, long narrative, sleep stories — use Fish Audio with the vault + auto-picker workflow.
```

### Fish Audio ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â PRIMARY PROVIDER

| Setting | Value |
|---------|-------|
| **Voice** | "Calm male" by ANGEL NSEKUYE |
| **Voice ID** | `0165567b33324f518b02336ad232e31a` |
| **Known as** | "Marco" / "Fish man" |
| **Temperature** | 0.3 (consistent but flat emotionally) |
| **Sample rate** | 44100 Hz |
| **Format** | WAV (not MP3) |
| **Character** | Deep resonance, slight accent (possibly Italian), very soothing |
| **Atempo** | 0.95x (standard Marco speed adjustment) |

**Best for:** Meditation, mindfulness, loving-kindness, body scans, breathwork, mantras, affirmations, sleep stories. All session durations handled via the vault + auto-picker workflow (Section 16D, 16E).

**Architecture:** One TTS call per text block. Pauses stitched in post-production.

**Critical characteristics:**
- Non-deterministic: same input produces different output every time
- ~60% rebuild rate on 45-min stories ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â this is normal
- Cost: negligible ($10 lasts ages)
- Real cost is TIME, not money
- Raw output: ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢16.34 LUFS average, ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢4.39 dBTP peak
- Chunk volume spread: ~8 dB (Auphonic leveller data)
- SNR: 45+ dB (broadcast quality without processing)
- No hum, minimal noise floor

### Fish Speaking Rate (CORRECTED — 12 Feb 2026)

Fish speaks at **10–13 characters per second**, not the previously assumed 7.2 ch/s. The 7.2 figure may apply to Resemble but is wrong for Fish by nearly 2×.

**Evidence (known-good candidates):**

| Chunk | Chars | Duration | Rate |
|-------|-------|----------|------|
| c01 v10 (EXCELLENT) | 58 | 4.3s | 13.5 ch/s |
| c04 v04 (EXCELLENT) | 60 | 6.7s | 9.0 ch/s |
| c08 v10 (EXCELLENT) | 61 | 5.5s | 11.0 ch/s |
| c18 v10 (OK) | 126 | 9.4s | 13.4 ch/s |

**Impact:** All duration estimates and cutoff detection thresholds must use this corrected rate. The auto-picker's Layer 1 cutoff uses `chars/22` (minimum viable duration) and the compound filter uses `cps > 14` (maximum expected rate). Any reference to Fish speaking at ~7 ch/s in the Bible or production tools is incorrect.

**The Fish API is stateless.** There is NO `condition_on_previous_chunks` parameter in the Fish Audio TTS API. Each API call is completely independent. Voice conditioning between chunks is implemented CLIENT-SIDE in `build-session-v3.py` by passing the previous chunk's audio as the `references` input for the next chunk. This is our pipeline's feature, not a Fish feature. Each chunk can be regenerated independently as long as the correct reference audio is provided.

**Possible S1 model degradation (February 2026).** Fish service alert shows generations exceeding 500 characters are temporarily routed to the v1.6 model instead of S1. If some chunks in a build hit S1 and others hit v1.6, different voice characteristics result ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â producing voice shift between chunks within the same session. This is a Fish-side issue outside our control. Story Studio was upgraded in December 2025; infrastructure changes may have side effects. Monitor Fish changelogs for resolution.

**Opening chunk weakness Ã¢â‚¬â€ PROVEN ROOT CAUSE (9 Feb 2026).** Chunk 0 (the very first chunk of any session) has no previous audio to condition from. Fish cold-starts without a voice reference, and the tail end of the sentence degrades Ã¢â‚¬â€ producing echo on every generation regardless of text content.

**Evidence:** Session 19 chunk 0 tested with 30 consecutive generations across 3 different approaches (original text, rewritten text, split text). All 30 flagged with echo risk 0.6Ã¢â‚¬â€œ1.2 by the scoring system. However, human listening confirmed the split-chunk audio was clean. The scoring formulaÃ¢â‚¬â„¢s spectral flux penalty systematically over-penalises unconditioned chunks (see below).

**The fix Ã¢â‚¬â€ Split Chunk Technique (PROVEN):** Split the opening text into two short chunks. Chunk 0a is one short sentence (~40Ã¢â‚¬â€œ60 chars). Chunk 0b carries the rest. Fish can generate a short sentence cleanly without conditioning Ã¢â‚¬â€ it doesnÃ¢â‚¬â„¢t have time to drift. Chunk 0b then uses 0aÃ¢â‚¬â„¢s audio as its conditioning reference, and the chain is anchored from there. Nothing is wasted Ã¢â‚¬â€ both chunks are real session content.

**Script rule:** Opening chunks must be one short sentence, under ~60 characters. The second chunk carries the remainder of the opening and receives conditioning from the first. This replaces the previously proposed "throwaway conditioning chunk" approach.

**Scoring formula bias on chunk 0:** The composite scoring metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance) is calibrated against mid-session chunks that have conditioning context. It systematically produces false catastrophic scores on chunk 0 because unconditioned audio inherently has higher spectral flux variance. A chunk 0 scoring Ã¢Ë†â€™358 combined with 0.7 echo risk may sound perfectly clean to a human ear. **Do not use automated scores for pass/fail decisions on chunk 0. Human listening is the only reliable gate for opening chunks.**

### Mid-Sentence Conditioning for Chunk 0 (PROVEN — 12 Feb 2026)

**Problem:** Even with the split-chunk technique, chunk 0 still has no audio conditioning reference. The `marco-master` WAV used as a fallback reference produces scores of 0.4–0.9 but voice character doesn't match Fish's natural output style.

**The fix — Mid-sentence conditioning:** Use a clean, human-picked chunk from a deployed session as the Fish API `references` parameter for chunk 0 generation. Tricks Fish into continuing a conversation rather than cold-starting.

**Evidence:** Narrator-welcome session chunk 0 — mid-sentence conditioning (using `c04_v19.wav` from session 42): **20/20 passed filter**, scores 7.5–8.8 (vs ~60% pass rate unconditioned).

**vault-builder.py changes:**
- `MARCO_MASTER_WAV` constant added (fallback reference)
- `_generate_one()` accepts `ref_audio_path` and `ref_text` parameters
- Base64-encodes reference audio and adds to Fish API payload as `references`
- Chunk 0: conditions on `MARCO_MASTER_WAV` (interim — should be replaced with curated reference library)
- Chunks 1+: conditions on previous chunk's best-scoring candidate WAV

**This is real audio conditioning at generation time, not just post-hoc MFCC scoring.**

**Fish cleanup chain (CANONICAL ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â use this, nothing else):**
1. Edge fades: 15ms cosine on each chunk before concatenation
2. Concatenate all chunks + silences (WAV)
3. Whole-file loudnorm: `loudnorm=I=-26:TP=-2:LRA=11` on full narration AFTER concatenation
4. Ambient mix (`amix` with `normalize=0`)
5. Final encode: 128kbps MP3 (ONLY lossy step)

Per-chunk loudnorm was REMOVED (8 Feb 2026) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â whole-file approach preserves natural dynamics between chunks. Requires Gate 7 thresholds 9/14 dB + 4s silence margin to accommodate Fish chunk-level swings.

The `highshelf=f=3000:g=3` boost was REMOVED (8 Feb 2026) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â A/B testing confirmed +3dB HF boost causes perceived echo on certain words. Loudnorm-only is cleaner with less hiss.

The HF shelf cut (`highshelf=f=7000:g=-3`) was proposed and tested across the full tuning range (ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢2 to ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢5 dB at 6ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“8 kHz) during the Gate 6 investigation. It failed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â removing the 3 kHz boost entirely produced identical flag counts, proving the root cause of Gate 6 false positives was natural speech sibilants, not pipeline-induced HF noise.

**DO NOT APPLY to Fish output:**
- ~~lowpass=f=10000~~ (kills clarity and consonant detail)
- ~~afftdn=nf=-25~~ (muffles the voice ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â noise floor already clean at 45 dB SNR)
- ~~dynaudnorm~~ (amplifies silence ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â NEVER use)
- ~~aggressive de-essers~~ (removes natural sibilance)
- ~~highpass=80~~ (not needed for Fish ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no low-frequency noise)
- ~~highshelf=f=7000:g=-3~~ (tested and failed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â does not address root cause)
- ~~highshelf=f=3000:g=3~~ (removed 8 Feb ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â causes perceived echo on certain words)

**Hard failure ceiling (9 Feb 2026):** Some chunks are unsalvageable with Fish regardless of regeneration count. Session 36 chunk 7 failed to improve across 10 consecutive best-of-10 attempts. When a chunk fails 10 regenerations without any improvement in composite score, stop retrying. Escalate to human review â€” the options are: accept as-is if not audibly jarring, mask with ambient level adjustment, or flag for script revision and regeneration.

### ElevenLabs ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â ABANDONED (6 Feb 2026)

Evaluated across 11 builds and Ãƒâ€šÃ‚Â£90+ in credits. Every approach failed. Evidence archived at `Desktop/elevenlabs-evidence/`.

**Why it failed:** API cannot hold voice consistency beyond 2-3 sequential calls. Studio "audiobook" feature produces continuous speech with no paragraph gaps and voice breakdown. SSML breaks max 3 seconds (sleep stories need 4-8s). Studio API locked behind sales whitelist (403 error).

**Do not revisit ElevenLabs** unless they release a fundamentally different long-form API.

### Fish Audio Female Voices ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â FAILED (6 Feb 2026)

8 female voices auditioned. All inferior to Marco. None had the warmth or natural pacing. Marco remains sole voice.

---

## 10. Marco Master Voice Specification

### Purpose

The Marco Master is the single definitive reference for what Marco sounds like. Every generated session is measured against this file. If it does not sound like the master, it does not ship ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â regardless of what automated gates report.

### Current Master

| Property | Value |
|----------|-------|
| **File** | `marco-master-v1.wav` |
| **Duration** | 37 seconds |
| **Processing** | 0.95x atempo only |
| **Provider** | Fish Audio |
| **Voice ID** | `0165567b33324f518b02336ad232e31a` |
| **Status** | Human approved, LOCKED |
| **Location** | `/content/audio/marco-master/marco-master-v1.wav` |
| **R2 backup** | `salus-mind/reference/marco-master-v1.wav` |

**The master is raw TTS output + speed correction only.** No filters, no loudnorm, no edge fades, no cleanup of any kind.

### Reference Passage

The master contains Marco speaking this standardised passage, covering all required vocal registers:

> Close your eyes and settle into a comfortable position. Let your shoulders drop away from your ears and feel the weight of your body being fully supported.
>
> Take a slow breath in through your nose, feeling your chest gently rise. And as you breathe out, let go of any tension you have been carrying. There is nowhere else you need to be right now. This moment is yours.
>
> [3-5 second pause]
>
> May I be safe. May I be happy. May I be healthy. May I live with ease.
>
> Now gently bring your attention back to the room around you. Take your time. There is no rush.

### Calibration Results (7 February 2026)

8 test generations: 5 Fish Audio + 3 Resemble.

**Useful metrics (reliably separate GOOD from BAD):**

| Metric | Threshold | Fish GOOD | Fish BAD (fish-4) | Resemble BAD |
|--------|-----------|-----------|-------------------|--------------|
| MFCC cosine distance | ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤0.008 (same-text), ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤0.06 (production) | 0.0003ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“0.0060 | 0.0003 | 0.0100ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“0.0113 |
| F0 deviation | ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤10% | 0.4%ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“5.6% | 0.8% | 14.8%ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“17.4% |

**Not useful metrics (too much variance):** Spectral centroid deviation, RMS deviation. Discarded.

**CRITICAL ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â THE FISH-4 EDGE CASE:** fish-4 was classified as BAD by human listening but measured 0.0003 MFCC / 0.8% F0 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â indistinguishable from GOOD. This proves automated metrics CANNOT catch every subtle quality failure. Human review remains MANDATORY even when all automated gates pass.

### Voice Comparison Gate ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Raw vs Raw

The voice comparison gate MUST compare raw audio against the raw master. Pre-cleanup WAV vs raw master. NOT processed audio vs master ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the cleanup chain changes the spectral fingerprint and causes false failures.

**Implementation:**
1. Save a pre-cleanup copy (`XX-session_precleanup.wav`)
2. Run voice comparison against THIS file
3. Cleanup chain runs afterward on the production copy
4. The precleanup WAV is also what Auphonic receives

### Master Versioning
- NEVER overwrite the current master
- New versions require full human approval + recalibration
- Old versions archived, never deleted
- Build script references a specific master version, not "latest"

| Version | Date | Provider | Notes |
|---------|------|----------|-------|
| v1 | 7 Feb 2026 | Fish | Moonlit garden passage, 37s, 0.95x atempo |

---

## 11. Audio Processing Pipeline

### Processing Philosophy

**LESS IS MORE.** Fish Audio TTS output is already broadcast-quality clean (45 dB SNR, ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢62 dB noise floor). Every processing step trades clarity and character for consistency. Apply the minimum necessary and nothing more.

### Fish Pipeline (CANONICAL)

```
Script (... pause markers)
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
process_script_for_tts() ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ blocks with pause durations
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
generate_tts_chunk() ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Fish API ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ WAV
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬ÂÃ…â€œÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ OVERGENERATION CHECK: If duration > 2x expected, reject and retry (max 3 retries)
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
apply_edge_fades() ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ 15ms cosine fade on each chunk (WAV in, WAV out)
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
generate_silence() ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ WAV (mono, pcm_s16le) via humanize_pauses()
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
concatenate_with_silences() ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ concat demuxer ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ WAV
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
WHOLE-FILE LOUDNORM: loudnorm=I=-26:TP=-2:LRA=11 on full narration
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
mix_ambient() ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ amix (normalize=0) ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ WAV
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
SINGLE MP3 ENCODE (libmp3lame, 128kbps) ÃƒÂ¢Ã¢â‚¬Â Ã‚Â ONLY lossy step
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
qa_loop() ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ 14-GATE QA (see Section 12)
        ÃƒÂ¢Ã¢â‚¬ÂÃ¢â‚¬Å¡
        ÃƒÂ¢Ã¢â‚¬â€œÃ‚Â¼
deploy_to_r2() ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ send_build_email()
```

### Whole-File Loudnorm (Fish only)

Apply `loudnorm` to the full concatenated narration WAV AFTER assembly ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not per-chunk. This preserves the natural dynamic variation between chunks that gives Marco his character. Per-chunk loudnorm was tested and removed (8 Feb 2026) because it flattened the delivery and, combined with the highshelf boost, introduced perceived echo on certain words.

The highshelf boost (`highshelf=f=3000:g=3`) was also removed (8 Feb 2026). A/B testing confirmed the +3dB HF boost was causing perceived echo and hiss on words like "settling", "stillness", "feel/feeling", "peace", "ease", "deeply". The loudnorm-only chain is cleaner.

Gate 7 thresholds were widened to 9/14 dB with 4s silence margin to accommodate Fish's natural chunk-level swings under whole-file normalisation.

### Atempo

Marco standard speed adjustment: 0.95x atempo. Applied to the master and consistently to all production. This gives Marco a slightly slower, more deliberate delivery for meditation pacing.

**Exception:** Sleep stories built with Fish/Marco ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no atempo needed, natural speed is correct.

### Channel Mismatch Bug (RESOLVED)

All files MUST be mono before concatenation. When ffmpeg's concat demuxer joins mono and stereo PCM files, it misinterprets the sample data ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stereo segments play at double duration. Silence files must be generated as mono (`cl=mono`), not stereo.

### Sleep Story Pause Profiles (12 Feb 2026)

The existing "story" pause profile (1.5/3/5s) is designed for continuous narrative, NOT sleep stories. Sleep stories need dramatically longer pauses — ambient fills the silence, lets the mind wander and drift.

**Proposed PAUSE_PROFILES addition:**

| Category | `...` (within-scene) | `......` (scene transition) | End sequence |
|----------|---------------------|---------------------------|-------------|
| `story` (existing) | 1.5s | 3s | 5s |
| `sleep-story` (NEW) | 12s | 35s | 60s |

**Evidence:** Session 53 (The Gardener's Almanac) assembled at 10.3 min with story profile pauses vs 23.2 min target. Manually scaled pauses to 12/35/60s — pacing made narrative sense with `......` markers correctly placed at scene transitions.

**The `...` vs `......` distinction in scripts IS meaningful** and maps correctly to within-scene pauses vs scene-transition pauses. This distinction must be preserved in PAUSE_PROFILES.

**Humanise pauses: RE-ENABLED for sleep stories.** Without humanisation, sleep stories assembled at approximately half their target duration — the rigid short pauses removed the breathing room that gives sleep stories their pacing. Session 53 confirmed: 10.3 min without humanisation vs 23.2 min target. Humanisation restores the intended duration and pacing.

### Ambient Rules

**Core rules:**
- Ambient file MUST be longer than voice track ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â **NEVER loop**
- Looping causes an audible glitch at the loop point
- Use 8-hour ambient files (available in `content/audio/ambient/`)
- Background ambient must not fade in until narrator introduction is complete
- Fade in: 15 seconds, Fade out: 8 seconds
- `mix_ambient()` file search order: `-8hr` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `-extended` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ base name. WAV checked before MP3.

**Ambient as masking (standard practice):**

A well-mixed ambient bed makes minor artifacts (soft echo, slight tonal shifts) disappear into the soundscape. This is standard practice in commercial meditation audio ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â every major app uses ambient beds for both atmosphere and artifact masking. The listener's brain attributes the anomaly to the environment rather than the voice.

Different ambient types mask differently. Broadband ambient (rain, stream, ocean) fills the full frequency spectrum and masks more effectively at a given level. Sparse ambient (nighttime birds, wind chimes, temple bells) has gaps where artifacts can peek through and may need higher relative levels or dynamic adjustment to be effective.

**Per-session ambient level:**

Ambient level is set by ear, per session, based on the ambient type and the chunk quality. There is no universal dB target. The person mixing (Scott) listens to the problem chunks with ambient at the proposed level and decides whether artifacts are sufficiently masked.

**Ceiling rule:** If the ambient has to be raised above ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢8dB relative to the voice to make the session listenable, the chunks have a quality problem that should be solved at the scorer/rebuild level, not the mix level. Ambient is a finishing technique, not a repair tool.

The deployed ambient level is recorded in the Deployed Sessions table (Section 16) for every session, building an empirical reference of what works per ambient type.

**Dynamic ambient (targeted masking):**

Where human review has identified specific problem chunks, the ambient level can be locally adjusted at those timestamps to provide additional masking. Rather than raising the ambient globally (which affects clean sections unnecessarily), the mixer applies a gentle volume swell around the problem spot and settles back to the base level afterward.

Implementation rules:
- Swell must be gradual ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â ramp up over 2ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“3 seconds before the problem chunk, hold through the chunk, ramp down over 2ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“3 seconds after. No sudden jumps.
- Maximum swell: +4dB above the session's base ambient level. Beyond this the ambient draws attention to itself and defeats the purpose.
- The swell should sound like natural variation in the ambient (birds getting busier, rain picking up briefly). Abrupt level changes are more noticeable than the artifact they're trying to mask.
- Dynamic ambient adjustments are driven by human review data ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the chunk numbers and timestamps from the review labels. This connects the human feedback loop directly to the mix stage.
- All dynamic adjustments must be documented in the build record: which chunks were targeted, the swell amount, and the ramp durations.

**Available 8-hour ambients:**

| File | Duration | Location | Notes |
|------|----------|----------|-------|
| `rain-8hr.mp3` | 8 hr | `content/audio/ambient/` | |
| `birds-8hr.mp3` | 8 hr | `content/audio/ambient/` | |
| `garden-8hr.mp3` | 12 hr | `content/audio/ambient/` | ÃƒÂ¢Ã…Â¡Ã‚Â ÃƒÂ¯Ã‚Â¸Ã‚Â 9.5s dead silence at file start ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â always use `-ss 10` |
| `rain-extended.mp3` | 70 min | `content/audio/ambient/` | |
| `stream-3hr.mp3` | 3 hr | `content/audio/ambient/youtube-downloads/` | |
| `stream-extended.mp3` | ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â | `content/audio/ambient/` | Created 9 Feb to cover longer sessions |
| `loving-kindness-ambient.wav` | 15 min | `content/audio/ambient/` | |

**Ambient type masking reference (to be populated as sessions are deployed):**

| Ambient type | Effective base level | Notes |
|-------------|---------------------|-------|
| Nighttime birds | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢42dB (14dB below voice) | Sparse ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â gaps between chirps need dynamic masking on problem chunks |

---

## 12. QA Gate System

### Overview

14 gates. ALL gates must pass ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â any failure blocks deploy. There are no informational-only gates. Every gate has a defined pass/fail condition. If a gate cannot fail a build, it is not a gate. Build time is not a constraint ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â all gates run on every build.

### Gate 1: Quality Benchmarks
Measures noise floor and HF hiss in silence regions via `astats`, compared against master benchmarks.

### Gate 2: Click Artifacts
Scan ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ patch ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ rescan loop. Detects click artifacts in silence regions (sample-level jump > peak analysis). Applies 20ms cosine crossfades at all stitch boundaries. Repeats up to 5 passes.

### Gate 3: Independent Spectral Comparison
Compares frequency profile of build against master reference WAV.

**Sliding window:** Gate 3 uses 1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2 second sliding windows for spectral comparison. If ANY window within a chunk exceeds the hiss threshold, the chunk fails ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â regardless of whole-chunk average.

**Calibrated threshold:** 18 dB above master reference (calibrated against known-good sessions ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â natural speech HF energy reaches up to 17 dB above reference in normal production).

### Gate 4: Voice Comparison
MFCC cosine + F0 deviation vs Marco master. Uses PRE-CLEANUP audio (see Section 10, Voice Comparison Gate).

**Thresholds:** MFCC ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤0.008 (same-text), ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤0.06 (production). F0 deviation ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤10%.

### Gate 5: Loudness Consistency
Per-second RMS sliding window ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â catches per-chunk loudness surges.

### Gate 6: HF Hiss Detector (Speech-Aware)
Sliding-window HF-to-total energy ratio on POST-CLEANUP audio. Evaluates non-speech regions only. Voice activity detection (or build manifest silence regions) excludes speech windows before HF ratio evaluation. This prevents natural vocal sibilants from triggering false positives while retaining full sensitivity for genuine hiss in pauses, silence, and transition regions.

**Thresholds:** 3s minimum duration, 6 dB HF/total ratio ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â unchanged from original calibration.

**Layered hiss coverage:** Gate 6 (non-speech regions) + Gate 1 (whole-file average) + Gate 9 (per-window energy spikes) provide three independent hiss detection systems covering different failure modes.

**History:** Gate 6 originally ran on all audio including speech. This caused 100% build failure rates ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â every build flagged 4ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“11 regions of natural speech sibilants. HF shelf cut was tested across the full tuning range (ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢2 to ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢5 dB at 6ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“8 kHz) and failed. Removing the 3 kHz boost entirely produced identical flag counts, confirming the root cause was speech sibilants, not pipeline-induced noise. Speech-aware detection resolved the issue without threshold changes or pipeline modifications.

### Gate 7: Volume Surge/Drop
Local-mean comparison with silence exclusion. 9/14 dB thresholds, proportional silence margin for transitions: `max(4s, silence_duration ÃƒÆ’Ã¢â‚¬â€ 0.15)`. Short pauses (8s) get 4s margin. Long silences (50s) get 7.5s margin ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â voice ramp-up after extended silence is proportionally longer.

**Low-baseline skip:** Skip detection when local mean energy is below ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢28 dB. This threshold represents ambient/silence regions, not speech. Flagging silence as "surges" is a false positive.

**Non-deterministic TTS level variation (9 Feb 2026):** Gate 7 is the most persistent failure mode during builds. Fish Audio's TTS generation is non-deterministic ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â identical text produces different volume levels on each call. When speech returns after a long silence, this variation can cause surges that exceed the 9.0 dB threshold. The threshold is correctly calibrated (lowering it would mask genuine defects). The correct response is to rebuild ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â eventually a generation set with consistent levels will pass. Sessions 19 and 32 needed 4 and 3 builds respectively; sessions 18 and 23 passed first time. Longer sessions with more chunks have higher failure probability.

### Gate 8: Repeated Content
MFCC fingerprint + Whisper STT with DUAL AGREEMENT ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â both must flag the same timestamps to confirm. 8-word minimum.

**Manifest text guard (8 Feb 2026):** When MFCC finds similar audio segments, the gate checks whether the underlying script text is actually the same. If word overlap between the two segments is <60%, the pair is skipped as a false positive (similar prosody on different text, common in meditation content with repeated cadence patterns).

**Expected-Repetitions metadata:** The `Expected-Repetitions` field in the script header lists phrases excluded from Gate 8's duplicate detection for that session only. This replaces any global ignore list.

```
Expected-Repetitions: May I be, May you be, May they be, May all beings be
```

### Gate 9: Energy Spike Detection (Visual Report)
Generates PNG with waveform, spectrogram, energy plot, and summary. Additionally performs per-window energy analysis (1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2 second windows) to detect anomalous spikes.

**Pass condition:** No window exceeds 12ÃƒÆ’Ã¢â‚¬â€ session median total energy AND no window exceeds 28ÃƒÆ’Ã¢â‚¬â€ session median high-frequency energy (above 4 kHz, speech-only windows used as baseline).

**Fail condition:** Any window exceeds either threshold. Flagged timestamps and energy values included in the visual report PNG.

**Calibration note:** The HF spike threshold was recalibrated at 28ÃƒÆ’Ã¢â‚¬â€ speech-only median and total energy at 12ÃƒÆ’Ã¢â‚¬â€ (8 Feb 2026). No-ambient sessions have lower HF median, so sibilants appear as 16ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“25ÃƒÆ’Ã¢â‚¬â€ spikes. Ambient sessions show sibilants at 4ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“8ÃƒÆ’Ã¢â‚¬â€ and genuine hiss at 32ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“36ÃƒÆ’Ã¢â‚¬â€. The 28ÃƒÆ’Ã¢â‚¬â€ HF threshold catches genuine hiss while passing sibilants in all session types. Fish per-chunk level swings can exceed 10 dB, requiring the generous 12ÃƒÆ’Ã¢â‚¬â€ total energy threshold.

**History:** Previously ran as informational-only with no pass/fail condition. Changed after the loving-kindness build deployed with a catastrophic hiss wall from 12:00 onwards that was clearly visible on the Gate 9 spectrogram but not evaluated programmatically.

### Gate 10: Speech Rate Anomaly Detection
Measures word density per second across the session using sliding windows.

**Silence-aware baseline:** Session average speech rate calculated using speech-only windows. Windows below a speech energy threshold are excluded from the baseline calculation. This prevents long meditation pauses from dragging the average down and causing false positives on normal-paced speech.

**Threshold:** Flag if any 2-second window exceeds 130% of the speech-only session average.

**Meditation-specific rule:** Speech rate should be consistently slow (~100ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“120 wpm / 8ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“10 chars per second). Sudden acceleration to normal conversational pace (~160 wpm) is a defect even if the words are correct.

**Calibration note:** With silence-aware baseline, the session average sits around 3.0ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“3.5 words/second for meditation content. The original implementation included silence windows, dragging the average to ~2.3 w/s and producing 27 false positives per build.

**Known limitation â€” high-silence sessions:** Sessions with silence ratios exceeding ~70% (e.g., extended mindfulness practices with long unguided pauses) will produce false positives even with the silence-aware baseline. The median speech rate drops low enough that normal-paced speech registers as anomalous. When Gate 10 fails on a session with >70% silence content, treat it as a probable false positive and verify by human listening. Do not adjust thresholds to compensate â€” the threshold is correct for standard meditation content.

### Gate 11: Silence Region Integrity
Verifies that every silence region in the manifest actually contains silence. Checks whether pause regions have been filled with audio bleed, stray TTS output, or ambient at the wrong level.

**Implementation:**
1. Reads the build manifest to identify all marked silence/pause regions and their expected durations
2. For each silence region in the RAW narration (pre-ambient mix), measures energy
3. If energy in any silence region exceeds ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢50 dBFS, flags it
4. For the MIXED output, verifies silence regions contain ambient-only energy (no voice bleed) by comparing energy against the ambient-only baseline level Ãƒâ€šÃ‚Â±3 dB

**Pass condition:** All silence regions in raw narration below ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢50 dBFS. All silence regions in mixed output within Ãƒâ€šÃ‚Â±3 dB of ambient-only baseline.
**Fail condition:** Any silence region contains unexpected audio.

### Gate 12: Duration Accuracy
Verifies the final output duration matches the script's target.

**Implementation:**
1. Reads the `Duration-Target` field from the script metadata header
2. Measures the actual duration of the final mixed output
3. Calculates percentage deviation from target

**Pass condition:** Final duration within 15% of Duration-Target.
**Fail condition:** Duration outside 15% tolerance.

15% tolerance rather than 10% because humanised pauses introduce natural variation. A 12-minute target producing 10:12 to 13:48 is acceptable.

**Duration header accuracy (9 Feb 2026):** When rebuilding an existing session, set `Duration-Target` by cross-referencing the previous build's actual output duration â€” not by estimating from character count or guessing. Session 03 was overcorrected from 15 to 20 minutes, producing a 22.9% deviation and a Gate 12 failure. If no previous build output exists, use the build script's dry-run duration estimate. The character-based formula (~10–13 chars/sec for Fish; see Section 9) is for rough planning only and should never be the sole basis for the header value.

### Gate 13: Ambient Continuity
Programmatically enforces the rule that there must be no dead silence anywhere in the final track and ambient must continue through all pauses and silences.

**Implementation:**
1. Identifies all pause/silence regions in the mixed output (using the build manifest)
2. For each region, measures energy in a sliding window (1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2 seconds)
3. Checks the final 30 seconds of the file ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â ambient fade-out must not create dead silence before the track ends
4. Measures ambient level consistency across pause regions

**Pass condition:** All pause regions above ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢80 dBFS. No dead silence anywhere. Ambient energy consistent across regions (within 10 dB).
**Fail condition:** Any dead silence detected, or ambient level inconsistency exceeds 10 dB.

**Calibration note:** Dead silence threshold calibrated at ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢80 dBFS (not the originally proposed ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢55 dBFS). Quiet ambient tracks measure ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢72 to ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢77 dBFS in known-good sessions. Ambient consistency tolerance calibrated at 10 dB (not 6 dB) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â known-good sessions show up to 8 dB range across pause regions.

### Gate 14: Opening Quality (Tighter Thresholds)
The opening is what the listener hears first. TTS glitches concentrate in the first 30ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“60 seconds. A glitch at 8:32 is bad; a glitch at 0:15 is catastrophic.

Runs the following gates with TIGHTER thresholds on the first 60 seconds of the file:

| Gate | Standard threshold | Opening threshold (first 60s) |
|------|-------------------|-------------------------------|
| Gate 1 (Quality Benchmarks) | Noise floor ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢26 dB, HF hiss ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢40 dB | Noise floor ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢30 dB, HF hiss ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢44 dB |
| Gate 6 (HF Hiss) | 6 dB ratio, 3s min | 4 dB ratio, 1s min |
| Gate 5 (Loudness) | 6.5 dB above median | 6 dB above median |
| Gate 10 (Speech Rate) | 130% of session average | 120% of session average |

**Pass condition:** All tightened thresholds met in the first 60 seconds.
**Fail condition:** Any threshold exceeded in the opening ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â even if the same issue would pass later in the track.

**Calibration note:** Gate 5 opening threshold calibrated at 6 dB (not the originally proposed 4 dB). Known-good sessions show 5.3 dB loudness variation in the opening.

### Gate 15: Post-Deploy Live Audio Scanner

**Status:** CRITICAL — added 12 Feb 2026. Two failures on the same day: (1) a deployed session shipped with a massive audio breakdown that the existing 14-gate pipeline missed, (2) Code deployed sessions with 0s ambient fade-in (spec is 15s) with no detection. Both would have been caught by this gate.

**Purpose:** Automated scan of the live deployed MP3 file on R2 to catch obvious audio failures that the pre-deploy pipeline missed. This is not a pre-deploy gate — it runs AFTER deployment, scanning the actual file that listeners will hear.

**What it detects:**

| Check | Method | Threshold | Catches |
|-------|--------|-----------|---------|
| Catastrophic silence | Windowed RMS scan (5s windows) | Any window below −60 dBFS within expected speech region | Audio dropout, failed chunks, missing audio |
| Volume explosion | Windowed peak scan (5s windows) | Any window with peak > −1 dBTP | Loudness spikes, uncontrolled surges |
| Voice breakdown | Windowed spectral centroid variance | Centroid drops below 500 Hz or jumps above 6 kHz for >3s | Voice mush, robotic distortion, Fish model collapse |
| Duration sanity | Total file duration vs script target | More than 30% deviation from expected duration | Assembly errors, missing chunks, wrong pause profile |
| Hiss cascade | Windowed HF scan (10s windows) | HF above −36 dB sustained across 3+ consecutive windows | Conditioning chain contamination |
| **Ambient fade-in** | RMS of first 15s ambient-only region | Ambient reaches full level before 15s | Missing or incorrect fade-in. Spec: 15s fade-in. Code deployed 0s fade-in on 12 Feb — this check would have caught it instantly. |
| **Ambient fade-out** | RMS of final 8s | Ambient does not taper to silence | Missing or incorrect fade-out. Spec: 8s fade-out. |

**Workflow integration:**

```
Deploy to R2 → CDN cache purge → Gate 15 scan of live URL → Report
```

Gate 15 runs automatically after every deployment. If any check fails, the report flags the session for immediate human review with timestamps of detected issues. The session remains live (speed > perfection) but the failure is logged and acted on in the next review round.

**This gate would have caught both 12 Feb failures:**

1. **Audio breakdown:** A deployed session contained a massive audio breakdown audible to any listener. All 14 pre-deploy gates passed. The voice breakdown check (spectral centroid) and/or volume explosion check would have flagged it immediately.

2. **0s ambient fade-in:** Code deployed sessions with ambient slamming in at full volume from the first sample (spec: 15s fade-in). The ambient fade-in check would have detected full-level ambient in the first second and flagged the file. This is a spec violation that no pre-deploy gate currently checks for because pre-deploy gates run on intermediate audio before ambient mixing.

**The pattern:** Both failures occurred in the final deployment stage — after ambient mixing, MP3 encoding, and R2 upload. Pre-deploy gates scan intermediate audio. Gate 15 scans the actual product. Without Gate 15, the only safety net is human listening, which didn't catch these before subscribers could hear them.

### Overgeneration Retry Logic

If a generated chunk's duration exceeds 2ÃƒÆ’Ã¢â‚¬â€ the expected duration for its character count, reject it and regenerate immediately. Up to 3 retries per chunk before flagging as build failure.

**Expected duration:** Character count / speaking rate. Fish meditation speaking rate: 10–13 characters per second (see Section 9, Fish Speaking Rate).

### Threshold Calibration Reference

These thresholds were calibrated against two known-good deployed sessions (25-introduction-to-mindfulness, 36-loving-kindness-intro) on 7 February 2026. They represent production-validated values, not theoretical estimates.

| Gate | Parameter | Brief estimate | Calibrated value | Evidence |
|------|-----------|----------------|------------------|----------|
| Gate 3 | HF sliding window | 10 dB | 18 dB | Natural speech HF up to 17 dB above reference |
| Gate 9 | HF spike threshold | 4ÃƒÆ’Ã¢â‚¬â€ all-window median | 28ÃƒÆ’Ã¢â‚¬â€ speech-only median (HF), 12ÃƒÆ’Ã¢â‚¬â€ total | No-ambient sibilants at 16ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“25ÃƒÆ’Ã¢â‚¬â€, genuine hiss at 32ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“36ÃƒÆ’Ã¢â‚¬â€ |
| Gate 13 | Dead silence | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢55 dBFS | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢80 dBFS | Quiet ambient at ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢72 to ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢77 dBFS |
| Gate 13 | Ambient consistency | 6 dB | 10 dB | 8 dB range on known-good session |
| Gate 14 | Loudness (opening) | 4 dB | 6 dB | 5.3 dB on known-good session |

---

## 13. Script Writing Rules

### Block Size

| | Characters |
|---|---|
| **Minimum** | **50** (below 50 causes TTS instability and hiss ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â root cause of all hiss failures) |
| **Sweet spot** | 50ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“200 |
| **Maximum** | 400 (longer blocks trend toward monotone) |

Blocks under 50 characters must be merged with adjacent blocks or expanded with additional content.

**For loving-kindness/mantra content:** Combine 3ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“4 short phrases into one block with internal ellipses. Each block 76ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“150 characters. This gives TTS enough context while ellipses create internal rhythm.

### Opening Chunk Rule (MANDATORY Ã¢â‚¬â€ 9 Feb 2026)

The first chunk of every session (chunk 0) must be one short sentence, under ~60 characters. The second chunk carries the remainder of the opening.

**Why:** Fish cold-starts chunk 0 with no voice conditioning reference. Long unconditioned passages degrade at the tail end, producing echo. Short sentences complete before degradation begins. Chunk 1 then uses chunk 0Ã¢â‚¬â„¢s audio as its conditioning reference, anchoring the entire session.

**Evidence:** 30 consecutive generations of session 19 chunk 0 across 3 text variants all produced echo. Splitting into two short chunks produced clean audio immediately.

**Example:**
- BAD: "Find somewhere comfortable to lie down. A bed, a sofa, even the floor. Whatever works for you right now." (one long chunk 0)
- GOOD: Chunk 0a: "Find somewhere comfortable to lie down." Ã¢â€ â€™ Chunk 0b: "A bed, a sofa, even the floor. Any spot that feels right."

### Pause Markers

| Marker | Usage |
|--------|-------|
| `...` | Standard pause (duration varies by category profile) |
| `......` | Long pause |
| `........` | Extended pause |
| `[SILENCE: Xs]` | Narrator-announced extended silent practice period |

**Pause Profiles (by category):**

| Category | Single `...` | Double `......` | Triple `........` |
|----------|-------------|-----------------|-------------------|
| sleep | 10s | 30s | 60s |
| mindfulness | 8s | 25s | 50s |
| stress | 6s | 20s | 40s |
| story | 1.5s | 3s | 5s |
| sleep-story (NEW — 12 Feb 2026) | 12s | 35s | 60s |
| default | 8s | 25s | 50s |

### Script Rules

| Rule | Why |
|------|-----|
| All blocks **50ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“400 characters** | Under 50 causes hiss; over 400 causes monotone |
| Combine short phrases with lead-in text | "May I be safe." (14 chars) ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "Silently now, may I be safe." (28 chars) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â still needs combining further to reach 50 |
| Use `...` for pauses (not `ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â`) | Script parser reads `...` as pause markers |
| No ellipsis in spoken text | Fish renders `...` as nervous/hesitant delivery |
| Scripts must contain ZERO parenthetical tags | In-text emotion tags don't work (see Section 18) |
| Estimate ~10–13 chars/second for Fish narration duration (CORRECTED 12 Feb 2026 — was 7.2) | See Section 9, Fish Speaking Rate. The 7.2 figure was wrong by nearly 2x. Use 10–13 ch/s for Fish estimates. The build script's own duration estimate (from actual chunk generation or dry run) remains more reliable than any character-based formula. |

### Script Metadata Header

```
Title: [session name]
Category: [sleep/mindfulness/stress/default]
Duration-Target: [minutes]
API-Emotion: calm
Expected-Repetitions: [comma-separated phrases for Gate 8]
```

- `API-Emotion` is a per-session setting read by the build script. Default: `calm`. Used with V3-HD API calls (see Section 18).
- `Expected-Repetitions` excludes listed phrases from Gate 8's duplicate detection.

### Fish Audio Trigger Words

Certain words cause consistent artifacts in Fish/Marco output. Most are sibilant-heavy words or sustained vowels ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â exactly where Fish struggles to hold a clean, gentle tone. These appear constantly in meditation scripts, making this a high-impact issue.

**Known trigger words (calibrated from Session 36 human review, 8 Feb 2026):**

| Word / Phrase | Defect | Suggested alternatives |
|--------------|--------|----------------------|
| settling | echo | resting, arriving, easing |
| stillness | echo | quiet, calm, silence |
| feel / feeling | echo | notice, sense, become aware of |
| peace | echo | calm, tranquillity, serenity |
| ease | echo | comfort, gentleness, softness |
| deeply | echo | gently, fully, completely |
| hollow | echo | open, spacious, empty |
| simply | echo | just, only, quietly |
| family | hiss | loved ones, those close to you |
| joyful | hiss | happy, glad, filled with joy |
| be (standalone) | voice shift | Embed in longer phrases ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â never isolate |
| breath in | hiss | breathe in, inhale, draw a breath |
| filling your lungs completely | hiss | Rewrite as shorter phrase ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â "breathe in fully" |
| nowhere else | voice shift | "right here", "all you need is to be here" |

**Pattern:** Most triggers are soft, sibilant-heavy words or words with sustained vowels where Fish needs to hold a gentle, open tone. These are the exact words that appear constantly in meditation content.

**Workarounds:**
- Use synonyms from the table above
- Break the word into a longer phrase where it's less exposed (e.g. "deeply" alone is worse than "more deeply now")
- If a trigger word is essential to the meaning and has no good synonym, ensure it falls within a block of 100+ characters so the TTS has surrounding context to stabilise

**Pre-flight scan:** The build script includes an automated pre-flight check that scans all script blocks against this list before any TTS calls. Blocks containing trigger words are flagged with suggested alternatives. This runs during dry-run and at the start of a live build. It is a WARNING, not a build-blocker ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â some trigger words may be unavoidable, but the scriptwriter should make a conscious choice rather than discovering the problem at the listening stage.

**Maintaining the list:** New trigger words discovered during human review are added to this table with their defect type and suggested alternatives. The pre-flight scan reads from this list. The list is expected to grow as more sessions are built and reviewed.

---

## 13A. Script Uniqueness & Cross-Session Differentiation

### The Problem

Salus sessions are starting to sound the same. A customer who listens to two or three sessions back-to-back should feel like they've had three distinct experiences ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not the same session with different words in the middle. When openings blur together, when every session guides the breath the same way, when the same transitional phrases appear across the catalogue, the product feels mass-produced rather than crafted.

This is the single biggest threat to perceived quality that doesn't show up in any automated gate. A session can pass all 14 QA checks and still feel identical to the one before it.

**The rule is simple: no two Salus sessions should feel interchangeable.** Every session must have its own identity ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â its own way in, its own rhythm, its own voice, its own way of closing. A returning customer should be able to tell which session they're listening to within the first 30 seconds.

### Cross-Session Registers (Mandatory)

Three register files track what has already been used across the catalogue. These are the primary tool for preventing internal repetition. They live in `content/scripts/` and are checked before every new script enters the build pipeline.

#### `openings-register.txt`

Every deployed session's opening line and opening approach, one entry per line.

Format: `[Session #] | [Opening line] | [Opening technique]`

**Rule:** No new session may use the same opening technique as any existing session in the register. If three sessions already open with breath awareness, the next session must open differently ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â perhaps with a sound observation, a question, a brief story, a sensory detail, or silence.

#### `closings-register.txt`

Every deployed session's closing line and closing approach.

Format: `[Session #] | [Closing line] | [Closing technique]`

**Rule:** No new session may use the same closing technique as any session in the same category. Across categories, closings should still vary as much as possible. Sleep sessions all end with "Goodnight from Salus" (per existing rules), but the lead-in to that line must differ every time.

#### `phrases-register.txt`

Distinctive phrases, metaphors, breath cues, and transitional language used across all deployed sessions.

Format: `[Session #] | [Phrase or cue] | [Context]`

**Rule:** No phrase of 5+ words from this register may appear in a new script. If a phrase has been used, it's spent ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â find a new way to say it.

### Categories of Repetition to Eliminate

These are the specific areas where "same same" creeps in. Each one needs active variation across every new script.

#### 1. Openings

The opening 30 seconds is where repetition is most damaging. It's the first thing the listener hears, and if it sounds familiar from their last session, they've already mentally checked out.

**What tends to repeat:**
- "Get comfortable" / "Find a comfortable position" / positional setup
- Immediate breath instruction ("Take a deep breath in...")
- "Close your eyes"
- Body settling cues ("Let your shoulders drop...")

**Variation strategies:**
- Open with an environmental observation ("There's a quiet in this moment...")
- Open with a gentle question ("What brought you here today?")
- Open mid-action ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no settling, just start the practice
- Open with a single sensory detail (a sound, a temperature, a texture)
- Open with a brief, unexpected statement that sets the session's theme
- Open with silence ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â let the ambient carry the first few seconds before the voice enters

**Mandatory:** Before writing any opening, check `openings-register.txt`. If the planned approach is already there, change it.

#### 2. Breath Cues

Every meditation involves breathing. The risk is that every session guides the breath using identical language.

**What tends to repeat:**
- "Breathe in... breathe out"
- "Notice your breath" / "Bring your attention to your breathing"
- "Take a deep breath in through your nose"
- "With each exhale, let go of..."

**Variation strategies:**
- Describe the breath indirectly ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â talk about what it does to the body rather than instructing the mechanism
- Vary the sensory focus: one session might notice temperature of air at the nostrils, another might notice the rise of the chest, another the sound of the exhale
- Some sessions can skip explicit breath guidance entirely and let the pacing of the script imply the rhythm
- Use different verbs: draw, gather, release, soften, empty ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not always "breathe in/out"
- Vary the placement: some sessions guide breath early, others introduce it midway as a return point

**Mandatory:** No two sessions in the same category may use the same breath cue phrasing. Check `phrases-register.txt`.

#### 3. Body Awareness Transitions

The pivot from settling into the core practice is where sessions most commonly blur together.

**What tends to repeat:**
- "Now bring your attention to..." (sequential body-part tour)
- "Notice any tension in your [body part]"
- "Allow that area to soften / release / let go"
- "Scan from the top of your head down to your toes"

**Variation strategies:**
- Skip the full body scan ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â focus on one or two areas with genuine depth
- Use movement rather than stillness: "Gently rock your weight side to side and notice where you land"
- Use contrast: "Notice the difference between your left hand and your right"
- Use temperature, weight, or texture rather than tension/release
- Approach the body from the outside in (what the air feels like on skin) rather than inside out

#### 4. Silence Announcements

The Bible requires narrator announcements before extended silences (Section 4.3 of the v1 Bible). The approved phrases are templates, not scripts. Each session must adapt them into something specific to that session's context and theme. The adapted version goes into `phrases-register.txt` so it isn't reused.

Examples of session-specific adaptations:
- Loving-kindness: "Stay with this warmth for a while. I'll be here when you're ready."
- Sleep: "Let the rain hold you now. I'll come back gently."
- Stress: "There's nothing to fix right now. Just be here. I'll return shortly."
- Mindfulness: "Keep noticing. That's all. I'll rejoin you in a moment."

#### 5. Closings

After openings, closings are the highest-repetition risk. If every session ends with "carry this feeling with you," the catalogue sounds formulaic.

**What tends to repeat:**
- "Wiggle your fingers and toes"
- "When you're ready, slowly open your eyes"
- "Carry this sense of [calm/peace/warmth] with you"
- "Take this feeling into the rest of your day"

**Variation strategies:**
- End with a concrete image or memory from the session, not a generic benediction
- End with a question the listener can hold: "What's one thing you noticed today?"
- End with a sound cue rather than a verbal instruction to return
- End abruptly ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â some sessions can simply trail off into ambient, letting the listener decide when they're done
- End with a specific, practical suggestion: "The next time you're waiting in a queue, try this for thirty seconds"
- End with humour or lightness where the session type allows it

**Mandatory:** Before writing any closing, check `closings-register.txt`. If the planned approach is already there, change it.

#### 6. Structural Arc

Even if individual phrases differ, sessions can feel identical if they follow the same structural shape every time.

**The default arc (overused):**
Settle ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ breathe ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ body awareness ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ core practice ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ integration ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ close

**Variation strategies:**
- Start in the core practice immediately ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no preamble
- Move between activity and stillness rather than building linearly toward stillness
- Use a circular structure ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â return to the opening image or phrase at the end
- Use a single extended metaphor as the structural spine rather than a technique sequence
- Vary the ratio of guidance to silence ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â some sessions should be 70% guided, others 40%
- Place the most intense or meaningful moment somewhere unexpected ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not always at the two-thirds mark

### Pre-Build Originality Scan (Automated)

The build script runs a cross-session originality scan during the pre-flight phase, alongside the existing trigger word check and block-size validation.

**The scan:**
1. Loads all three register files (`openings-register.txt`, `closings-register.txt`, `phrases-register.txt`)
2. Extracts all text blocks from the new script
3. Compares each block against register entries using fuzzy matching (threshold: 70% similarity on any phrase of 5+ words)
4. Flags matches with the specific session number and phrase that conflicts
5. Checks the opening line and closing line against their respective registers ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â exact or near-exact matches are flagged
6. Generates an originality report saved to `content/scripts/originality/{session-name}-originality.txt`

This is a WARNING system, not a build-blocker. The scriptwriter (Claude Code or human) reviews the report and either revises the flagged content or documents why the repetition is acceptable (e.g., traditional metta phrases that cannot be meaningfully varied).

### Post-Build Register Update (Mandatory)

After a session is deployed, the three register files must be updated with the new session's entries. This is part of the deployment checklist (Section 16). A build is not considered complete until the registers are current.

### External Originality (Secondary)

While internal differentiation is the primary concern, scripts should also not closely resemble widely published meditation scripts from other platforms or teachers. This is both a legal and a quality concern.

**Process:**
- When writing a new script, Claude Code performs web research on the session topic to understand what already exists
- The purpose of this research is to consciously diverge, not to find material to adapt
- No phrase of 6+ consecutive words should match a published source
- A brief research note is stored in `content/scripts/research/{session-name}-research.txt` listing sources consulted and how the Salus script differs

This is lighter-touch than the internal register system ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â a due diligence step, not a gating mechanism.

### Exceptions

Some repetition across sessions is unavoidable and acceptable:

- **Traditional formulations** (e.g., metta phrases "May I be safe, may I be happy") ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â these are traditional, not anyone's property, and listeners expect consistency in how they're presented
- **Functional micro-instructions** (e.g., "breathe in," "close your eyes") ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â unavoidable, though the framing around them must vary
- **Category conventions** (e.g., sleep sessions ending with "Goodnight from Salus") ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â brand signatures, not repetition
- **Phrases listed in `Expected-Repetitions` metadata** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â intentional structural repetition within a single session (handled by Gate 8)

The key distinction: **functional language can repeat; creative language must not.** "Breathe in" is functional. "Let your breath become a soft tide, washing through you" is creative ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â and once it's been used in one session, it's done.

### Narration Audit (Outstanding)

**Status:** PENDING ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â to be scheduled

A full audit of all deployed sessions is required to retroactively populate the three register files and identify existing cross-session repetition. This is a prerequisite for the register system to function properly.

**Scope:**
1. Retrieve or reconstruct scripts for all deployed sessions (01, 03, 05, 06, 07, 08, 09, 11, 18, 19, 23, 25, 29, 32, 36, 38, 43)
2. Extract opening lines, closing lines, and distinctive phrases from each
3. Populate `openings-register.txt`, `closings-register.txt`, and `phrases-register.txt`
4. Identify any existing cross-session repetition ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â document which sessions share phrasing and flag for future rewrites
5. Listen to a representative sample across categories back-to-back and note where sessions feel interchangeable
6. Produce an audit report with specific recommendations for which scripts need the most differentiation work

**Priority:** Must be completed before any new scripts are written. The registers are worthless if they don't include existing content.

---

## 14. Expression Through Punctuation

**Status:** ACTIVE ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Technique proven, deployed in loving-kindness session.

### The Problem

TTS at temperature 0.3 is deliberately flat. Marco sounds the same whether saying "close your eyes" or "you are deeply loved." Increasing temperature adds instability and artefacts. Temperature is not the solution.

### The Solution: Script-Level Direction

Every comma, ellipsis, fragment, and sentence structure is vocal direction to Marco. The TTS model responds to punctuation cues ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not perfectly, but enough to create natural rhythm and breathing. No API changes, no model tuning, no extra cost. Just better scripts.

### Techniques

**Ellipses within sentences** (breath/hesitation):
> "All you do... is offer gentle wishes"
>
> The ellipsis creates a micro-pause and slight pitch shift.

**Fragments for emotional weight:**
> "Who suffers. Who struggles. Just like you."
>
> Short declarative sentences hit harder than flowing prose.

**Sentence structure that slows pace:**
> "And gently... close your eyes" vs "Close your eyes gently"
>
> The first version forces TTS to slow down at "gently."

**Commas creating micro-pauses:**
> "Your lap, your sides, wherever feels natural"
>
> Each comma is a tiny breath that makes the delivery more human.

**Varying sentence lengths:**
> "Take a moment to notice how it feels to offer these words to yourself. Really feel them."
>
> The contrast between long flowing and short punch creates rhythm.

**Loving-kindness phrases with internal ellipses:**
> "May I be safe... May I be happy... May I be healthy... May I live with ease."
>
> 76ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“84 characters per block. Ellipses create breathing rhythm without splitting into dangerously short chunks.

---

## 15. Auphonic Integration

**Status:** ACTIVE ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Measurement gate ONLY. Do not use Auphonic output as production audio.

### Account

| | |
|---|---|
| **URL** | https://auphonic.com |
| **API** | https://auphonic.com/api/ |
| **Auth** | HTTP Basic (username:password in `.env`) |
| **Free tier** | 2 hours/month, re-processing same file is free |
| **Preset** | "Salus Narration QA" (saved 7 Feb 2026) |

### What Auphonic Is For

- SNR measurement (is the TTS output clean?)
- Noise floor verification (any degradation?)
- Hum detection (electrical interference?)
- Loudness measurement (how far from target?)

### What Auphonic Is NOT For

- Processing/cleaning the audio (Voice AutoEQ damages Marco's bass warmth)
- Leveling (causes breath wobble on meditation content with long silences)
- EQ (cuts defining bass characteristics)

### Pass/Fail Criteria

| Metric | PASS | FAIL |
|--------|------|------|
| Input SNR | ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¥ 40 dB | < 40 dB |
| Background Level | ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤ ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢55 dB | > ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢55 dB |
| Hum detected | No | Yes (any segment) |
| Output loudness | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢26 Ãƒâ€šÃ‚Â±1.0 LUFS | Outside range |
| Output true peak | ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤ ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢2.0 dBTP | > ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢2.0 dBTP |
| Output LRA | ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤ 16 LU | > 16 LU |
| Leveler gain spread | ÃƒÂ¢Ã¢â‚¬Â°Ã‚Â¤ 10 dB | > 10 dB |

SNR threshold at 40 dB based on Fish baseline of 45.26 dB. The old 25 dB threshold was too permissive for TTS content.

### Per-Segment Analysis

**Status: NOT AVAILABLE.** The Auphonic API does not return per-segment SNR data ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â only aggregate file-level metrics. Per-segment analysis was planned but cannot be implemented as a pipeline gate due to this API limitation. If Auphonic exposes per-segment SNR in a future API version, this should be revisited.

Whole-file Auphonic metrics remain in use as a secondary measurement gate alongside the 14-gate pipeline system.

### Auphonic Preset Settings

| Setting | Value |
|---------|-------|
| Adaptive Leveler | Enabled |
| Filtering | Enabled (Voice AutoEQ) |
| Loudness Target | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢26 LUFS |
| Max Peak Level | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢2 dBTP (ATSC A/85) |
| Noise Reduction | Static: remove constant noises only, 6 dB (low) |
| Remove Reverb | Off |
| Automatic Cutting | Off (preserve meditation silences) |
| Output Format | WAV 16-bit PCM, optimal stereo |

**Note:** The "silent segments >30s" warning is a FALSE POSITIVE for meditation content. Ignore it.

### First Baseline Results (7 February 2026)

File: `36-loving-kindness-intro_precleanup.wav`

| Metric | Value |
|--------|-------|
| Program Loudness | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢16.34 LUFS |
| LRA | 15.21 LU |
| Max Peak Level | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢4.39 dBTP |
| SNR mean | 45.26 dB |
| Background Level | ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢62.25 dB |
| Hum | Not detected |

**Key conclusion:** Fish Audio TTS output is broadcast quality (40ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“50 dB SNR standard). The aggressive cleanup chain was solving a problem that barely existed.

### API Usage

Always submit RAW narration (voice-only, no ambient) to Auphonic.

```bash
curl -X POST https://auphonic.com/api/simple/productions.json \
  -u "$AUPHONIC_USERNAME:$AUPHONIC_PASSWORD" \
  -F "input_file=@/path/to/raw_narration.wav" \
  -F "denoise=true" \
  -F "loudnesstarget=-26" \
  -F "output_files[0].format=wav" \
  -F "output_basename=narration_auphonic" \
  -F "action=start"
```

Python integration code available in the build script. Poll status at `/api/production/{uuid}.json` (status 3 = Done, 2 = Error).

### Auphonic Echo Detection — RULED OUT (9 Feb 2026)

Auphonic was tested as an external echo detector against 55 labelled chunks (5 ECHO, 24 OK from sessions with human review). **AUC-ROC: 0.341** — worse than random. Anti-correlated with human echo perception.

| Metric | ECHO chunks | OK chunks | Interpretation |
|--------|------------|-----------|----------------|
| Signal level | −22.4 dB | −19.7 dB | Echo chunks are quieter |
| Loudness | −23.0 LUFS | −20.7 LUFS | Echo chunks are quieter |
| Noise floor | −65.7 dB | −60.4 dB | Echo chunks have less noise |
| SNR | 43.3 dB | 40.7 dB | Echo chunks have better SNR |

The pattern is the opposite of real acoustic reverb. Fish's "echo" is a generative distortion — the TTS model smears or hallucinates certain phonemes, producing lower-energy, smoother output that sounds like echo to human ears but has no physical delay signature. Auphonic sees it as a quieter, cleaner signal.

Adding Auphonic features to local DSP features made the combined detector worse (AUC 0.527 vs 0.568 local-only). **Do not use Auphonic for echo detection.**

---

## 15A. Production Readiness

**Status:** READY FOR SCALE Ã¢â‚¬â€ 9 February 2026

The audio production pipeline is now mature enough for mass production of meditation sessions. The combination of automated QA, proven repair processes, and documented Fish Audio failure modes means sessions can be produced at volume with reliable quality.

### What Makes This Possible

**Automated quality scoring** (8 Feb 2026): Per-chunk composite scoring identifies defects programmatically. The scoring system catches hiss, voice shift, and tonal inconsistency for mid-session chunks. **It does not detect echo** — see Section 16B. Human listening remains the only reliable echo gate.

**Proven repair pipeline** (9 Feb 2026): Defective chunks can be fixed through targeted best-of-10 regeneration and splice repair without rebuilding entire sessions. Repair process validated on sessions 32 and 19.

**Documented failure modes:** Fish AudioÃ¢â‚¬â„¢s behaviour under production conditions is now characterised:
- Trigger words that cause echo/hiss (Section 13)
- Chunk 0 cold-start degradation and the split-chunk fix (Section 9)
- Gate 7 non-deterministic volume variation (Section 12)
- Scoring formula bias on unconditioned chunks (Section 9)
- 30% hit rate on certain phonetic patterns

**Script rules that prevent defects:** Opening chunk length limit, 50Ã¢â‚¬â€œ400 character blocks, trigger word pre-flight, cross-session originality scan. Scripts designed around FishÃ¢â‚¬â„¢s known weaknesses produce cleaner first-generation audio.

### Production Workflow

1. **Script** Ã¢â‚¬â€ Write following all rules (Section 13, 13A). Short opening chunk. Trigger word scan. Originality check.
2. **Build** Ã¢â‚¬â€ `build-session-v3.py --no-deploy`. Best-of-5 per chunk. 14 gates.
3. **Score** Ã¢â‚¬â€ Per-chunk composite scoring identifies any flagged chunks.
4. **Repair** Ã¢â‚¬â€ Flagged chunks get best-of-10 targeted regeneration (Section 16A). Opening chunks assessed by human ear, not score.
5. **Review** Ã¢â‚¬â€ Human listening on headphones at high volume. Focus on flagged chunks and opening/closing.
6. **Deploy** Ã¢â‚¬â€ Upload to R2, wire into HTML, update registers, push, email.

Sessions 18 and 23 passed first build with zero repairs needed. Realistic expectation: most sessions will need 1Ã¢â‚¬â€œ3 chunk repairs, taking the total production time from script to live to approximately 30Ã¢â‚¬â€œ60 minutes per session once the script is written.

### Competitive Position

No competitor in the meditation app space has solved AI voice reliability at this level. Calm and Headspace use human narrators. Smaller apps using AI voice ship the exact defects this pipeline catches and fixes. The Salus pipeline produces AI-narrated content at a quality level that withstands headphone listening at high volume Ã¢â‚¬â€ with a documented, repeatable process. This knowledge compounds with every session built and is not publicly documented anywhere.

---

## 16. Build Execution

### CLI Usage

```bash
# Full pipeline: build ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ QA ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ deploy to R2
python3 build-session-v3.py 25-introduction-to-mindfulness

# Dry run (no API calls)
python3 build-session-v3.py 25-introduction-to-mindfulness --dry-run

# Build + QA but don't deploy
python3 build-session-v3.py 25-introduction-to-mindfulness --no-deploy

# Raw output (no cleanup) for quality testing
python3 build-session-v3.py SESSION --no-cleanup
```

### Pre-Build Checklist

**Script:**
- [ ] Script written with correct metadata header and pause markers
- [ ] All text blocks 50ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“400 characters (MINIMUM 50, not 20)
- [ ] Short phrases combined to exceed 50 chars
- [ ] Pauses humanised (no identical gap durations)
- [ ] Zero parenthetical emotion tags in text
- [ ] `Expected-Repetitions` set if session has intentional structural repetition
- [ ] **Opening chunk is one short sentence, under ~60 characters** (mandatory Ã¢â‚¬â€ Section 13)
- [ ] **Trigger word pre-flight passed** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â script scanned against known trigger word list (Section 13). Any flagged words either replaced with synonyms or consciously accepted
- [ ] **Cross-session originality scan passed** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â script checked against registers (Section 13A). No unresolved conflicts with existing openings, closings, or phrases
- [ ] **Duration-Target cross-referenced** â€” if rebuilding, header set against previous build's actual duration. If new, header set from dry-run output.

**Environment:**
- [ ] Only building ONE session (no parallel builds)
- [ ] Provider set to `fish`
- [ ] `FISH_API_KEY` set in `.env`
- [ ] `RESEND_API_KEY` set in `.env`
- [ ] `AUPHONIC_USERNAME` / `AUPHONIC_PASSWORD` set in `.env`
- [ ] Master reference WAV exists at `content/audio/marco-master/marco-master-v1.wav`

**Build:**
- [ ] Dry run completed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â block count and silence totals verified
- [ ] Ambient file duration exceeds estimated voice duration
- [ ] If no long ambient exists, download one BEFORE building

**Quality:**
- [ ] All 14 QA gates run
- [ ] 0 voice changes in QA results

**Human Review (mandatory before deploy):**
1. Start `label-server.py` (labels auto-save to `reference/human-labels/` — no manual exports)
2. Extract individual chunks from raw narration WAV using manifest timing data
3. Upload chunks to R2 at `test/chunk-test-{version}/` (e.g. `chunk-test-v3b/`)
4. Run `score-chunks-whisper.py` on extracted chunks to generate Whisper confidence scores
5. Create or update interactive HTML review page with Whisper confidence badges and auto-save
6. Scott listens to every chunk on AirPods at high volume (exposes artifacts normal listening misses)
7. Chunks flagged by Whisper (bottom 30% by `word_prob_p10`) are highlighted with a blue border — visual cue only, not a gate
8. Each chunk rated: OK / ECHO / HISS / VOICE / BAD
9. Labels auto-save to `reference/human-labels/` via label server (verify CSVs exist after review)
10. If clean rate is acceptable → proceed to deploy
11. If problem chunks identified → use `--focus-chunks` for targeted rebuild (problem chunks get best-of-10, others best-of-5)
12. Re-review focused chunks. Repeat if needed, but perfection should not prevent shipping.

**Review scope rule:** Scott listens to ALL chunks. Full-chunk human review is mandatory until the echo detector (Section 16B) achieves a validated false negative rate below 10% on cross-validated data across at least 5 sessions and 200+ labelled chunks. No automated system currently detects Fish echo reliably. Do not reduce review scope based on automated scores.

**Chunk review batching:** Scott feeds labelled data into the echo detection system through focused testing sessions (~1 hour) when in the mood. The pipeline must always have chunks extracted, uploaded to R2, and review pages generated so these sessions are not wasted waiting for data preparation. Every reviewed session grows the training dataset for the echo detector.

**Deployment:**
- [ ] Final audio remixed with ambient at per-session level (set by ear ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â see Ambient Rules in Section 11). Dynamic masking applied to problem chunks if needed.
- [ ] Final MP3 uploaded to Cloudflare R2 (NOT committed to git)
- [ ] Audio plays from `media.salus-mind.com` URL (test on both desktop AND mobile)
- [ ] CORS verified: `Access-Control-Allow-Origin` header present in response
- [ ] Website HTML updated ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â ALL pages referencing the session (listing pages, detail pages, mindfulness cards)
- [ ] Players wired up with `data-src` attribute pointing to correct R2 URL
- [ ] HTML changes committed and pushed to main
- [ ] Email sent to scottripley@icloud.com
- [ ] `openings-register.txt` updated with new session's opening line and technique
- [ ] `closings-register.txt` updated with new session's closing line and technique
- [ ] `phrases-register.txt` updated with new session's distinctive phrases, metaphors, and cues

### Email Notification System

| | |
|---|---|
| **Service** | Resend API (free tier, 100 emails/day) |
| **Env var** | `RESEND_API_KEY` in `.env` |
| **Sender** | `onboarding@resend.dev` (switch to `build@salus-mind.com` after domain verification) |
| **Recipient** | `scottripley@icloud.com` |
| **Header** | Uses `curl` subprocess (Python `urllib` blocked by Cloudflare bot protection) |
| **Trigger** | Every completed build ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â pass or fail |

### Deployed Sessions

| Session | Duration | Provider | Ambient | Status |
|---------|----------|----------|---------|--------|
| 01-morning-meditation | 13.7 min | Fish | Grace (-14 dB) | **Redeployed 12 Feb** via auto-picker v7 + grace ambient. 26 chunks, 1,710 candidates, rich verdict history (4 trial runs). Auto-picked 26/26. **Awaiting full-audio review.** |
| 03-breathing-for-anxiety | 15.4 min | Fish | — | v3 rebuild 9 Feb. 12/14 gates (Gate 12 duration overcorrection, Gate 13 bird chirp ambient). Previous: 54% flagged → 6.25% flagged (8.6× improvement). **Rollback (9 Feb):** v3 rebuild deployed but had major voice failure on opening chunk. Rolled back to previous version (16:03 build, 14.9MB). Voice-fail version archived to `archive/03-breathing-for-anxiety_voice-fail_2026-02-09.mp3`. Still needs successful rebuild using split-chunk technique on chunk 0, plus Gate 12 and Gate 13 fixes. |
| 09-rainfall-sleep-journey | 25.7 min | Fish | Grace (-14 dB) | **Redeployed 12 Feb** via auto-picker. 63 chunks, 1,145 candidates. 3 unresolvable chunks (c21, c35, c42). **Awaiting full-audio review** — expect issues at 5:55, 12:10, 14:51. |
| 18-calm-in-three-minutes | 3.2 min | Fish | rain | Deployed (build 1, 14/14 gates, 9 Feb, commit 752752f) |
| 19-release-and-restore | 14.5 min | Fish | garden | Deployed (build 4, 14/14 gates, 9 Feb, commit 752752f). Builds 1Ã¢â‚¬â€œ3 failed Gate 7 (surge). Script rewritten (trigger-word clean, progressive muscle relaxation). **Repair (9 Feb):** Chunk 0 echo Ã¢â‚¬â€ 30 generations across 3 approaches all flagged by scorer, but split-chunk version confirmed clean by human listening. Scoring formula bias on unconditioned chunks proven. Wrong ambient noted (script=garden, build=rain). Chunk 0 split + remixed with correct ambient, deployed. |
| 23-the-calm-reset | 5.5 min | Fish | stream | Deployed (build 1, 14/14 gates, 9 Feb, commit 752752f). Script rewritten (trigger-word clean). |
| 25-introduction-to-mindfulness | 14.4 min | Fish | garden, Ã¢Ë†â€™ss 10 offset | Deployed (rebuild 8 Feb, LALAL-cleaned Ã¢â‚¬â€ voice degraded, trigger word fix "nowhere else", commit acb5842). LALAL removed from pipeline (all modes tested and failed Ã¢â‚¬â€ see v3.4). 4 flagged chunks including opening (worst hiss at Ã¢Ë†â€™7.26 dB) Ã¢â‚¬â€ repair or rebuild decision pending (Ledger L-05). |
| 32-observing-emotions | 9.5 min | Fish | garden | Deployed (build 3, 14/14 gates, 9 Feb, commit 752752f). Builds 1Ã¢â‚¬â€œ2 failed Gate 7 (surge). Gate 12 fix: Duration-Target adjusted from 12 to 10 min (script overestimated). Script new. **Repair trial (9 Feb):** Chunk 1 echo on "something" Ã¢â‚¬â€ best-of-10 regeneration, v4 selected (combined 0.417Ã¢â€ â€™0.467, quality 0.426Ã¢â€ â€™0.490, echo risk Ã¢Ë†â€™15%). 14/14 gates. Splice at speechÃ¢â€ â€™silence boundary, tonal distance 0.000443 (0.09% of threshold). Repaired file at `32-observing-emotions-repair-1.mp3` on R2 Ã¢â‚¬â€ **promoted to live 9 Feb after human A/B review confirmed echo eliminated.** |
| 36-loving-kindness-intro-v3 | 10.5 min | Fish | birds, ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢42dB (14dB below voice) | Deployed (v3b focused rebuild, best-of-10, 14/14 gates, 65% clean rate) |
| 38-seven-day-mindfulness-day1 | 10.7 min | Fish | — | v3 rebuild 9 Feb. 14/14 gates. Cleanest build of batch. |
| 39-seven-day-mindfulness-day2 | 8.1 min | Fish | Grace (-14 dB) | **First auto-picker assembled session.** v7 round 3: 24/25 pass (96%), 1 VOICE fail. 3 review rounds, 5 chunks regenerated. Deployed to R2. |
| 42-seven-day-mindfulness-day5 | ~12 min | Fish | Grace | Vault-assembled 12 Feb. A/B picked, deployed to R2. |
| 53-the-gardeners-almanac | 23.2 min | Fish | Grace (-14 dB) | **First sleep story from auto-picker.** 49 chunks, 980 candidates. Pause scaling issue discovered — story profile pauses (1.5/3/5s) too short, manually scaled to 12/35/60s. **Awaiting full-audio review.** |
| 61-21day-mindfulness-day5 | ~9 min | Fish | Stream (-8.4 dB) | Vault-assembled 12 Feb. A/B picked, deployed to R2. |
| 76-21day-mindfulness-day20 | ~15 min | Fish | Birds (-2.3 dB) | Vault-assembled 12 Feb. Gate overrides: Gate 7 + Gate 12 (expected false positives for "long sit" format). |
| narrator-welcome | 1.3 min | Fish | Grace (-10 dB, 5s in, 10s out — non-standard fades, clip too short for 15/8) | Vault-assembled 12 Feb. c0 conditioned via mid-sentence technique (session 42 c04_v19.wav). Picks: c0=v78, c1=v47, c2=v50, c3=v35, c4=v22. |

---

## 16A. Chunk Repair Pipeline

**Status:** APPROVED Ã¢â‚¬â€ production use authorised 9 February 2026. Trial on session 32 chunk 1 confirmed perceptual improvement (echo on "something" eliminated). Repaired file promoted to live. Code is authorised to run targeted best-of-10 repairs on all flagged chunks in the repair backlog without further approval.

### Why This DidnÃ¢â‚¬â„¢t Exist Earlier

The per-chunk composite scoring system was only added on 8 February 2026. Before that, there was no programmatic way to identify which specific chunks were defective Ã¢â‚¬â€ it was all human listening. The scoring system created the data, the repair trial (9 Feb) proved the fix works, and now Code can run repairs autonomously. The full loop Ã¢â‚¬â€ score Ã¢â€ â€™ identify Ã¢â€ â€™ regenerate Ã¢â€ â€™ splice Ã¢â€ â€™ verify Ã¢â€ â€™ deploy Ã¢â‚¬â€ is a capability that became possible less than 48 hours before it was proven. From v3.4 onwards, this loop runs on every future production and retrospectively across the deployed catalogue.

### When to Use

Chunk repair is for fixing a specific defective chunk in an already-deployed session without rebuilding the entire session. It is a targeted intervention, not a substitute for full rebuilds.

**Use when:**
- A deployed session has a localised defect (echo, hiss, voice shift) in one or two chunks
- The rest of the session is clean and does not need regenerating
- A full rebuild would risk introducing new defects in currently-clean chunks

**Do not use when:**
- Multiple chunks across the session are flagged (>3 Ã¢â‚¬â€ full rebuild is more efficient)
- The defect is in the ambient mix rather than the narration
- The session has never passed human review


**Hard failure rule:** If a chunk fails 10 consecutive regenerations without improvement in composite score, stop. Do not continue retrying. The chunk is a Fish hard failure (e.g., Session 36 chunk 7 â€” 0/10 improved). Options: accept if not audibly jarring in context, mask with ambient level adjustment, or flag for script revision and regeneration.
### Process

1. **Identify the defect.** Per-chunk QA scoring flags chunks below 0.50 composite score. Human listening confirms the specific defect (echo, hiss, voice shift) and its location.

2. **Extract the target chunk** from the master narration WAV using the build manifestÃ¢â‚¬â„¢s timing data.

3. **Best-of-10 regeneration.** Generate 10 replacement versions of the chunk via Fish Audio. Score all 10 using the composite metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance to neighbours). Select the highest-scoring version.

4. **Splice into a copy of the master narration.** Use 100ms cosine crossfade at the splice boundary. Target speechÃ¢â€ â€™silence boundaries for the splice point where possible Ã¢â‚¬â€ silence absorbs any residual discontinuity.

5. **Run all 14 QA gates** on the repaired narration.

6. **Apply ambient** at the same level as the deployed version. Encode to 128kbps MP3.

7. **Upload to R2 as a repair candidate** (e.g. `32-observing-emotions-repair-1.mp3`). Do NOT replace the live file.

8. **Human A/B comparison.** Scott listens to both original and repaired files on headphones at high volume. Only promote to live after human sign-off.

### Splice Rules

- 100ms cosine crossfade Ã¢â‚¬â€ no hard cuts
- Target speechÃ¢â€ â€™silence boundaries (tonal distance is lowest here)
- Measure tonal distance at the splice point Ã¢â‚¬â€ must be <0.50 (threshold from bible)
- Document splice assessment in the repair report: crossfade duration, boundary type, tonal distance, silence absorption

### Trial Results (9 February 2026)

**Session 32, Chunk 1** Ã¢â‚¬â€ echo on "something"

| Metric | Original | Repair (v4) | Change |
|--------|----------|-------------|--------|
| Combined score | 0.417 | 0.467 | +0.050 |
| Quality score | 0.426 | 0.490 | +0.064 |
| Echo risk | 0.00147 | 0.00125 | Ã¢Ë†â€™15% |
| Tonal distance | 0.000192 | 0.000452 | +0.00026 |
| 14-Gate QA | 14/14 | 14/14 | Ã¢â‚¬â€ |

Voice MFCC=0.039, F0 dev=2.6% | 0 clicks, 0 spikes, 0 surges

**Best-of-10 generation results:** 3 of 10 versions scored higher than the original. 7 scored below 0.364. The selected version (v4) had the best combined score + tonal distance balance. v2 had better raw quality (0.522) but worse tonal match (0.0014 vs 0.0005) Ã¢â‚¬â€ tonal match was prioritised for splice quality.

**Splice assessment:** 100ms cosine crossfade at speechÃ¢â€ â€™silence boundary. Tonal distance 0.000443 (0.09% of threshold). +1.33s absorbed by silence region. Very likely inaudible.

**Honest assessment:** Echo risk reduced 15% but replacement still below 0.50 flag threshold. None of 10 Fish generations reached "clean." The repair is measurably better but human listening is required to confirm perceptual improvement. The word "something" may be a phonetic pattern that Fish consistently struggles with Ã¢â‚¬â€ a 30% improvement rate (3/10) is notably low.

### Repair Backlog

Chunks flagged across deployed sessions (composite score <0.50), ranked by severity. Session 32 chunk 1 is the completed trial. All others are candidates if the repair process is approved after human A/B review.

| Session | Chunk | Score | Hiss (dB) | Text | Priority |
|---------|-------|-------|-----------|------|----------|
| 19 | 51 | 0.209 | Ã¢Ë†â€™9.43 | "This has been Salus. Go gentlyÃ¢â‚¬Â¦" | Closing chunk Ã¢â‚¬â€ high exposure |
| 25 | 12 | 0.232 | Ã¢Ë†â€™8.35 | "You donÃ¢â‚¬â„¢t need to stop your thoughtsÃ¢â‚¬Â¦" | Mid-session |
| 32 | 12 | 0.325 | Ã¢Ë†â€™10.19 | "Stay with that sensationÃ¢â‚¬Â¦" | Mid-session |
| 19 | 31 | 0.348 | Ã¢Ë†â€™13.47 | "Your neck. Gently press your head backÃ¢â‚¬Â¦" | Mid-session |
| 25 | 3 | 0.349 | Ã¢Ë†â€™10.26 | "Find somewhere comfortable to sit or lie downÃ¢â‚¬Â¦" | Early chunk |
| 25 | 1 | 0.365 | Ã¢Ë†â€™7.26 | "This is a simple introduction to mindfulnessÃ¢â‚¬Â¦" | Opening chunk Ã¢â‚¬â€ worst hiss, highest exposure |
| 36 | 7 | 0.378 | Ã¢Ë†â€™10.04 | "There is nothing to force hereÃ¢â‚¬Â¦" | Early chunk |
| 23 | 13 | 0.426 | Ã¢Ë†â€™10.67 | "Now imagine all the stress you have accumulatedÃ¢â‚¬Â¦" | Mid-session |
| 25 | 5 | 0.430 | Ã¢Ë†â€™8.54 | "LetÃ¢â‚¬â„¢s start with your breathÃ¢â‚¬Â¦" | Early chunk |
| **32** | **1** | **0.449** | **Ã¢Ë†â€™10.51** | **"Today we are going to practise somethingÃ¢â‚¬Â¦"** | **REPAIRED Ã¢â‚¬â€ LIVE** |

Sessions 01, 03, 09, 38 have no per-chunk QA data (pre-scoring system). Session 18 passed clean (0/12 flagged).

**Session 25 note:** 4 flagged chunks including the opening (worst hiss reading across all sessions at Ã¢Ë†â€™7.26 dB). Full rebuild may be more appropriate than individual chunk repairs for this session.

### Hiss Mitigation

The repair trial included a hiss reduction test (Phase 4). Results:

**LALAL.AI (dereverb=OFF, dehiss only):** INEFFECTIVE. Uniform 3 dB attenuation across all frequencies. SNR unchanged at 21.8 dB. Not selective denoising Ã¢â‚¬â€ equivalent to turning the volume down. **LALAL cannot selectively remove hiss from Fish TTS output.**

**Auphonic:** SKIPPED Ã¢â‚¬â€ no credentials in `.env` at time of trial.

**Conclusion:** Chunk selection (best-of-N scoring) + ambient masking remain the only viable hiss mitigation strategies. No external post-processing service has proven capable of selectively removing Fish-generated hiss without damaging vocal quality. The pipelineÃ¢â‚¬â„¢s hiss defence is: (1) avoid trigger words that cause hiss, (2) score chunks and keep the cleanest, (3) mask residual hiss with ambient.

---

## 16B. Echo Detection

**Status:** INVESTIGATION COMPLETE — no automated echo detector works yet. Human review is the only functioning echo gate. Active brief (`brief-echo-detection.md`) tracks next steps.

### The Core Finding (9 Feb 2026)

Fish Audio's "echo" is not acoustic echo. It is a **generative distortion** — the TTS model smears or hallucinates certain phonemes, producing output that sounds like echo to human ears but has no physical echo signature (no delayed signal copies, no reverb tail, no impulse response). This is why every detection approach has failed: they all measure acoustic properties of echo that this artefact does not possess.

### What Was Tested

| Approach | AUC-ROC | Best metric (Cohen's d) | Result |
|----------|---------|------------------------|--------|
| Composite scorer | ~0.50 | — | Random chance. Anti-correlated on some metrics. |
| Local DSP features | 0.568 | c50_mean (d=0.57) | Weak signal, not predictive |
| Auphonic API | 0.341 | signal_level (d=−0.55) | **Anti-correlated** — flags clean, misses echo |
| Combined (DSP + Auphonic) | 0.527 | — | Adding Auphonic makes it worse |
| Whisper confidence | 0.506 | word_prob_p10 (d=−0.66) | **Strongest signal** but not predictive at n=12 echo |
| Human ears | 1.000 | — | The only thing that works |

**Dataset:** 55 labelled chunks (12 confirmed ECHO, 43 OK) from sessions 36 and 52. All approaches tested with Random Forest, Gradient Boosting, and Logistic Regression. All failed equally.

**Root cause of failure:** Classical echo detection looks for delayed signal copies (autocorrelation at 10–80ms), reverb tails, and impulse response characteristics. Fish's artefact produces lower-energy, smoother output — the opposite of acoustic reverb. The autocorrelation features were actually anti-correlated with echo (ECHO chunks had *lower* values than CLEAN chunks).

### What Shows Promise

**Whisper confidence** (`word_prob_p10` — 10th percentile of per-word probability) shows the strongest descriptive signal of any approach tested (Cohen's d = −0.66). The direction is correct: echo chunks have lower Whisper confidence because the distortion degrades transcription accuracy. At the 30% threshold, it catches 7/12 echo chunks (58% recall) with 10 false positives — already better than the composite scorer (5/12).

AUC remains at 0.506 because 12 ECHO examples is insufficient for any model to generalise from. The signal may become predictive with more data.

### Current Integration

Whisper confidence is integrated into the review page as a **visual cue only**:
- `score-chunks-whisper.py` runs on extracted chunks, computes `word_prob_p10` per chunk
- Chunks in the bottom 30% by `word_prob_p10` are highlighted with a blue right border and "Whisper p10: 0.xxx" badge
- "Whisper Flagged (N)" filter button to view only flagged chunks
- Scores inlined directly in the review page — no external fetch needed
- **Not a gate. Not a pass/fail. Visual guidance only.**

### Next Steps (Dependent on Data)

These approaches require more labelled data before they become viable:

1. **More labelled data** — the single most important factor. 12 ECHO examples is too few. Target: 50+ ECHO examples across 5+ sessions. Every session Scott reviews feeds the dataset via the label server.
2. **Whisper confidence revalidation** — retest at 50+ ECHO examples. If d > 0.66 holds and AUC improves above 0.70, integrate as a formal pre-review filter.
3. **Mel spectrogram CNN** — needs ~200 labelled chunks. A neural network trained on spectrograms could learn the visual pattern of Fish's generative distortion directly. Most promising long-term approach for a non-classical artefact.
4. **Per-word analysis** — echo clusters on specific words/phrases (human review notes confirm: "fills", "question", "speech", "something different"). Word-level segmentation could isolate the artefact to specific phonetic patterns.

### What Must NOT Happen

- Do not claim the composite scorer detects echo. It does not. (See evidence above.)
- Do not reduce human review scope based on any automated echo score. Human listening is the only functioning gate.
- Do not retrain or update the echo detector without approval. Each retraining is a threshold change.
- Do not add echo detection as a formal QA gate until false negative rate is validated below 10% across 200+ labelled chunks.

---

## 16C. Vault Production System

> **Status update (12 Feb 2026):** The A/B tournament picker remains the fallback human review interface but is no longer the primary candidate selection method. The auto-picker (Section 16E) now handles initial candidate selection. Human review shifts from per-chunk A/B comparison (~2 hrs/session) to full-audio review of auto-picked assembly (~45 min/session including regen rounds). The picker's rejection reason tags (Echo, Hiss, Cut Short, Voice) continue to accumulate training data during any manual review sessions.

### Rejection Reason Tags (12 Feb 2026)

**4 tags:** Echo, Hiss, Cut Short, Voice

Colour-coded inline checkboxes below score/duration stats in each A/B candidate panel. Tags auto-collect on pick/reject.

**Data structure (per chunk in picks.json):**

```json
"rejection_reasons": {
  "6": ["Voice"],
  "10": ["Echo"],
  "15": ["Cut Short"],
  "19": ["Echo"],
  "22": ["Cut Short"]
}
```

**Implementation:** `tools/vault-picker/ab_picker_js.js` — `tagCheckboxes()` renders, `collectInlineTags()` harvests. All 54 pickers rebuilt and uploaded to R2.

### Solo Mode Fix (12 Feb 2026)

When A/B tournament reaches last remaining candidate, picker now shows "solo mode" (red border) for explicit accept/reject instead of auto-winning. Fixed `pickSide()` guard blocking solo mode buttons.

### The Critical Finding — Score ≠ Quality

The composite scoring metric cannot separate pass from fail. Quality score overlap between PASS and HARD FAIL is complete.

### Extended Evidence (78 Labelled Verdicts — 12 Feb 2026)

The auto-picker trial produced 78 severity-labelled verdicts across 4 review rounds of session 01 (26 chunks). The results confirm and strengthen the original finding:

| Severity | Avg Quality Score | Range |
|----------|------------------|-------|
| PASS | 0.890 | 0.667–1.293 |
| HARD FAIL | 0.990 | 0.836–1.199 |
| SOFT FAIL | 0.846 | 0.511–1.321 |

Hard fails have a **higher** average quality score than passes. Complete overlap across all severity levels. The composite scoring metric is fundamentally incapable of separating pass from fail. This is not a calibration issue — it is a measurement limitation.

**Implication:** The auto-picker uses ranking weights (echo, tonal distance, quality, flatness) rather than threshold-based pass/fail decisions. Quality score contributes at moderate weight (6.0) as a general signal but never makes the selection decision alone.

### Vault Scope — Current Inventory

| Metric | Value |
|--------|-------|
| Sessions in vault | 54 |
| Total chunks | 1,671 |
| Total candidates generated | ~12,800 |
| Sessions deployed | 13 (see Deployed Sessions table) |
| Sessions parked | 1 (session 01 — was parked for hiss, now redeployed via auto-picker, awaiting review) |
| Sessions waiting | 40 |
| Remaining human review time | ~30 hours (down from ~58 hours — auto-picker reduces per-session time by ~80%) |
| Platform target | 100+ sessions |

---

## 16D. Vault Production Workflow

### Numbered Workflow Sequence (Revised 12 Feb 2026)

```
1. Script → Structural guidelines check + autonomous fixes (Section 13)
2. Generate candidates per chunk (20 standard, split threshold 150 chars)
3. Pre-filter (0.30 composite score — advisory only)
4. Run auto-picker v7 (severity-aware selection — Section 16E)
5. Assemble voice-only (concat + loudnorm)
6. Mix with ambient (grace default, -14dB, 15s fade-in / 8s fade-out per Bible spec)
7. Deploy to R2 + CDN cache purge (Production Rule 20)
8. Human full-audio review (listen end-to-end, report failures at timestamps)
9. Map failures to chunks → regen failing chunks (20 extra candidates per fail)
10. Re-run auto-picker with verdict history → re-assemble → redeploy
11. Repeat rounds 8-10 until pass rate acceptable (typically 1-2 rounds)
```

Steps 1–7 and 9–10 are autonomous. Steps 8 and 11 require Scott. Typically 1–3 rounds to reach 96%+ pass rate.

**Key workflow shift:** Human review moves from per-chunk A/B picking (26 chunks × ~150 comparisons each = ~2 hrs) to full-audio review of pre-selected assembly (~15 min per round, 1–3 rounds = ~45 min total).

**Verdict history:** Every human review round feeds back into the auto-picker. Known-pass chunks are never re-eliminated. Known hard-fails are profiled and similar candidates rejected. This creates a virtuous cycle — each round improves the next.

---

## 16E. Auto-Picker

**Status:** PROVEN — v7 validated across 245 chunks, 10 sessions, 5,146+ candidates. First fully assembled session (39) at 96% pass rate. Replaces manual A/B tournament as primary candidate selection method.

### Why This Exists

The A/B tournament picker required ~58 hours of manual picking across 1,400 chunks. The auto-picker reduces human time from ~2 hours to ~45 minutes per session — an 80% reduction. At scale (54 sessions), this saves approximately 40 hours of human review time.

### Development History (v1→v7, 12 Feb 2026)

| Version | Pass Rate | Key Change |
|---------|-----------|------------|
| v1 | 23% | Quality score ranked (baseline) |
| v2 | 23% | Echo-first ranking — same rate, different composition |
| v3 | 23% raw / 73% effective | Severity tracking — 13 of 20 fails were SOFT (masked by ambient) |
| v4 | 53% | Known-pass bypass + hard-fail elimination + soft-fail penalty |
| v5 | Cross-session validated | Filters loosened — eliminations reduced 89% (95→10 human picks wrongly rejected) |
| v6 | 61.2% top-3 | Weight sweep (230+ combos). Tonal distance discovered as strongest signal (+7.8%) |
| v7 | 96% (session 39 live) | Three-layer cutoff + compound filter. First assembled session from auto-picker. |

### Algorithm (v7 — CURRENT)

**Three mechanisms:**

1. **Known-pass bypass:** Human-confirmed clean versions skip ALL elimination filters. A candidate scoring 0.263 composite (below the 0.30 floor) that was rated EXCELLENT by ear is sacred — never re-eliminated.

2. **Hard-fail profile elimination:** Candidates with metrics within 15% of known hard-fail versions rejected before ranking.

3. **Soft-fail penalty:** Candidates similar to soft-fail profiles penalised in ranking (−500 points). Known-pass candidates receive +1000 bonus.

**Ranking weights (v7 — weight-swept across 230+ combinations):**

```python
ECHO_RANK_WEIGHT = 200        # Echo risk penalty
QUALITY_RANK_WEIGHT = 6.0     # Composite quality score
TONAL_RANK_WEIGHT = 250       # MFCC distance to previous chunk (strongest signal)
FLATNESS_PENALTY = 20         # Spectral monotony
HISS_RANK_WEIGHT = 0          # DISABLED — ambient masks hiss, any weight hurts accuracy
DURATION_PREFER = 0           # DISABLED — "humans prefer longer" was WRONG at every weight tested
```

**Three-layer cutoff detection:**

| Layer | Method | Threshold | What it catches |
|-------|--------|-----------|-----------------|
| 1 | Duration cutoff | `chars/22` | Fish stops mid-text — extreme truncation |
| 2 | Tail cutoff | < 12ms trailing silence | Audio ends mid-waveform. `measure_tail_silence()` reads last 500ms of WAV, finds last sample above −40 dBFS |
| 3 | Compound cutoff | `cps > 14 AND tail < 25ms AND chars > 80` | Fish rushing with abrupt end. Neither tail nor chars/sec alone catches this — the combination is the signal |

**Content cutoff as ranking penalty or elimination: PROVEN HARMFUL** at every weight (50–500) and every threshold (15–18 ch/s) across all test phases. Pushes to worse alternatives because existing human picks include content cutoffs.

**UNRESOLVABLE detection:** When all candidates are eliminated, chunk is flagged UNRESOLVABLE. Action: split text at sentence boundary, regenerate. Do not silently fall back to lowest-scoring candidate.

### Critical Findings

**Quality score does NOT predict human verdict (PROVEN — 78 labelled verdicts):**

| Severity | Avg Quality Score | Range |
|----------|------------------|-------|
| PASS | 0.890 | 0.667–1.293 |
| HARD FAIL | 0.990 | 0.836–1.199 |
| SOFT FAIL | 0.846 | 0.511–1.321 |

Complete overlap between pass and hard fail. A candidate scoring 1.199 can be a hard fail while one scoring 0.667 is EXCELLENT. Composite score is a pre-filter only, not a selection metric.

**Tonal consistency is the strongest ranking signal.** MFCC distance to previous chunk measures voice consistency. Lower = better. Weight sweep Phase 4 discovered this: tonal=500 produced +7.8% top-3 improvement. Final weight settled at 250 (balanced with other signals).

**Duration preference ALWAYS hurts.** Every non-zero duration weight reduced accuracy across all 72 combinations tested. The intuition "humans prefer longer" was wrong for ranking.

**Hiss weight ALWAYS hurts.** Ambient masks hiss. Humans don't penalise it. Zero hiss weight is optimal.

**Human review variance is ~15%.** Across 4 runs, 4 regressions were the same audio file receiving different verdicts. Most flips are between PASS and SOFT FAIL. The severity system helps — it captures the gradient that binary pass/fail misses.

### Defect Priority (from human review data)

1. **Tonal consistency** — voice character shifts between chunks (highest impact)
2. **Cutoff** — zero tolerance, outright unusable
3. **Echo** — noticeable but ambient masks mild cases
4. **Quality** — general audio cleanliness
5. **Flatness** — spectral monotony
6. **Hiss** — lowest priority, ambient masks significantly

### Validation Data (v7 Final)

| Metric | Value |
|--------|-------|
| Exact match (auto-pick = human pick) | 24.5% |
| Top-3 (human pick in auto-picker's top 3) | 59.2% |
| Eliminated (human pick rejected by filters) | 18.8% |
| Chunks validated | 245 |
| Sessions validated | 10 |
| Candidates analysed | 5,146+ |

### Files

| File | Purpose |
|------|---------|
| `auto-picker.py` | v7 auto-picker (severity-aware + weight-swept + three-layer cutoff + compound filter) |
| `sweep-weights.py` | Automated weight sweep tool (230+ combos across 5 phases) |
| `tools/review-page-generator.py` | Standard review page template (auto-advance, severity, auto-save, keyboard shortcuts) |
| `docs/auto-picker-validation.json` | Final v7 validation data (245 chunks, 10 sessions) |
| `docs/weight-sweep-results.json` | Full sweep data (phases 1–3) |
| `docs/weight-sweep-phase4.json` | Tonal/hiss sweep data |

---

## 17. Governance

### Stop Rules

```
Autonomy Level: FULLY AUTONOMOUS ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â except where a STOP rule is triggered.
STOP rules override autonomy. When a STOP condition is met:
1. Output a status report
2. Cease all work immediately
3. Do not attempt fixes
4. Do not modify the pipeline
5. Do not continue with remaining tasks
6. Wait for human input
```

**Code must NEVER modify the build pipeline or override brief instructions without explicit human approval.** Autonomy covers execution strategy, not specification changes.

**Evidence:** Code independently added `afftdn` back into the pipeline (commit aa055a9) after the brief explicitly prohibited it. This is a governance failure.

### No Decorative Gates

Every QA gate must have a defined pass/fail condition that blocks deployment on failure. A gate that runs, produces data, and allows the build to proceed regardless is worse than no gate ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â it creates false confidence. This principle was established after two incidents where the pipeline generated clear visual evidence of defects and failed to act on it.

### No Threshold Loosening Without Approval

Gate thresholds must not be adjusted to make a failing build pass. If a gate catches too many issues, the correct response is to fix the root cause (e.g. script blocks below 50 characters producing hiss at boundaries), not to widen the threshold until the problems fall below it. Any threshold change requires human approval before implementation.

**Incident (7 Feb 2026):** Code raised Gate 6 min_duration from 3s to 5s mid-build because 11 regions at 3ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“4.5s were failing. The root cause was a script chunk at 48 characters ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â below the 50-character minimum known to cause hiss. Code chose to loosen the gate rather than fix the script. Reverted on instruction.

### Build State Persistence

All build state must be persisted to a file after every step. Never rely on conversation context for:
- Strike counter
- Build sequence number
- QA pass/fail results per gate
- Which script version is being built

**Reason:** Context compaction at 200K tokens is lossy. If Code compacts mid-build, it can lose track of state. Persistent state files survive compaction.

### Brief Lifecycle

Briefs are temporary instruction documents. They exist to direct Code, then get absorbed into the bible. A brief is not a permanent reference ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â it has a lifecycle.

```
DRAFT ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ ACTIVE ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ INTEGRATED ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ ARCHIVED
```

| Stage | Meaning |
|-------|---------|
| DRAFT | Being written by Claude Desktop. Not yet issued to Code. |
| ACTIVE | Issued to Code. This is the current work order. |
| INTEGRATED | All content absorbed into the bible. Brief is now redundant. |
| ARCHIVED | Moved to `docs/archive/`. No longer referenced by any active process. |

**Rules:**

1. **One active brief per workstream.** Never issue a second brief that amends a first. Update the original brief instead. If a brief needs amending, consolidate into a single replacement document before issuing.

2. **Briefs are read-only for Code.** Code must not edit, append to, annotate, or mark up a brief under any circumstances. The brief is an instruction ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not a progress tracker.

3. **No brief persists indefinitely.** Once the bible absorbs a brief's content, the brief moves to `docs/archive/` and stops being referenced. If Code is still reading a brief that was issued more than two build cycles ago, something has gone wrong.

4. **Amendments are consolidations, not patches.** If new information changes part of an active brief, Claude Desktop produces a new consolidated brief that replaces the original entirely. The old brief is archived. There must never be two documents where one "partially amends" the other.

### State File Separation

Code maintains a separate state file for each active brief. The brief is the instruction; the state file is the receipt.

**State file rules:**

1. **Code owns the state file.** It creates it at the start of work and updates it after every step. The state file is the only file Code is permitted to write progress into.

2. **The brief stays untouched.** Progress, strike counts, gate results, build logs, and completion markers go in the state file ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â never in the brief.

3. **State file naming:** `[brief-name]-STATE.md`

4. **State file location:** Same directory as the brief (typically `docs/`).

5. **State file contents (minimum):**

```markdown
# State: [Brief Name]
Last updated: [timestamp]

## Progress
| Item | Status | Notes |
|------|--------|-------|
| Phase 1, Step 1 | DONE / IN PROGRESS / PENDING / FAILED | Details |

## Build State
- Strike counter: X
- Build sequence: X
- Current phase: X

## Decisions Made
- [timestamp] ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â [decision and rationale]

## Issues for Human Review
- [anything requiring escalation]
```

6. **Verification:** Scott reviews the state file against the brief to confirm what was delivered. Code's self-reported progress is never treated as sign-off ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â it is a claim to be verified, not a certification.

7. **State files survive context compaction.** This is why they exist. If Code compacts mid-build, it reads the state file to recover position. Never rely on conversation context for build state.

### Document Hierarchy

```
PROJECT-BIBLE (canonical, maintained by Claude Desktop)
    ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“ instructs
Active Briefs (temporary, read-only for Code)
    ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“ tracked by
State Files (owned by Code, verified by Scott)
    ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“ archived alongside
docs/archive/ (retired briefs + their state files)
```

Code reads down. Code writes only to state files and to the codebase. Code never writes up.

### First Action on Receipt

On receiving any brief, Code's first action ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â before any implementation work ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â must be to create the corresponding state file and populate it with the full item list from the brief. This confirms the brief was read and the scope is acknowledged.

### Environment Variables

```
FISH_API_KEY=your_fish_api_key
RESEND_API_KEY=your_resend_api_key
AUPHONIC_USERNAME=your_auphonic_username
AUPHONIC_PASSWORD=your_auphonic_password
CF_CACHE_PURGE_TOKEN=your_cf_cache_purge_token
CF_ZONE_ID=your_cf_zone_id
STRIPE_SECRET_KEY=your_stripe_secret
STRIPE_WEBHOOK_SECRET=your_webhook_secret
```

---

## 18. V3 API Emotion System

**Status:** IMPLEMENTED. V3-HD migration complete. All 4 TTS call sites updated (7 February 2026).

### Background

The original emotion approach (in-text parenthetical tags like `(relaxed)`, `(calm)`) FAILED. Marco's cloned voice read every tag as literal spoken text. The meditation opened with the word "sincere" spoken aloud. **In-text emotion tags do not work with cloned voices on the S1 model.**

Fish Audio's V3 model versions (`v3-turbo` and `v3-hd`) support a separate `emotion` parameter in the API request body. The text stays completely clean.

### Current API Configuration

```json
{
  "reference_id": "<Marco voice ID>",
  "text": "Take a slow breath in... and let it go.",
  "version": "v3-hd",
  "emotion": "calm",
  "format": "wav"
}
```

**Available emotion values:** `happy`, `sad`, `angry`, `fearful`, `disgusted`, `surprised`, `calm`, `fluent`, `auto`

- `calm` = default for all Salus meditation content
- `fluent` = worth testing (may produce smoother delivery)
- Emotion set PER API CALL, not per sentence
- Cannot vary within a single chunk (acceptable for meditation ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â consistent tone is the goal)

### V3 Parameters

- `prosody.speed` replaces atempo in the pipeline (speed adjustment handled at API level)
- `"volume": -20 to 20` (default 0) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â leave at 0, handle in post-processing

### Investigation Results (7 February 2026)

| Test | Result |
|------|--------|
| Marco compatibility with V3-HD | PASS ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â voice works with cloned reference |
| Voice conditioning chain on V3 | PASS ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â consistency maintained across sequential chunks |
| Credit cost | Negligible difference from S1 |

### Fallback

If V3-HD becomes unavailable or degrades:
- Fall back to S1/v1
- No in-text emotion tags (they don't work)
- Rely on expression-through-punctuation (Section 14)
- Punctuation-based control already produced acceptable results

---

# PART C ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â HISTORICAL RECORD

---

## 19. Amendment Log

This section is a historical record of changes made. It is NOT an operating reference ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â all current operating rules are in Parts A and B above. If anything in this log contradicts Parts A or B, Parts A and B are correct.

### 4 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Initial Setup

21 issues completed across ASMR, Breathing, FAQ, Home, About pages. Premium flow standardised, card images deduplicated, site-wide terminology updated (Free ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Sample), 2-column tile grid established. Full image mapping created.

### 4 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Card Image Replacements

Hero image replaced (`meditation-woman-outdoor.jpg` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `japanese-fog.jpg`). All card images across index, apps, about, soundscapes, sessions replaced with unique images. Full image inventory created.

### 5 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Quick Wins

Founder statement rewritten, American testimonials added, "LATIN: HEALTH" subtitle added, contact page reframed, 21 "Subscribe to unlock" instances changed to "Premium".

### 5 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â UI/Visual Fixes & 21-Day Course

Play button fix (mindfulness), breathing ring/countdown sync fix (unified timer), tool buttons simplified, profile pictures made consistent, session cards given player overlay UI, 21-day mindfulness course page created.

### 5 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Supabase Authentication

Cross-device accounts via Supabase replacing localStorage premium system. Stripe webhook integration. 70+ pages updated with auth scripts and nav button.

### 5 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â UI Redesign & Navigation Overhaul

Two-row navigation, Latin phrase placement, atmospheric card design pattern, image optimisation, sleep stories updates, education tiles redesign, tools tiles equal height fix, section background blending.

### 5 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â UI Cleanup & Sleep Stories

Coloured tiles removed site-wide, sessions page redesigned with player bar UI, sleep stories page created (52-book library), navigation streamlined.

### 6 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â SEO & Infrastructure

robots.txt fixed, sitemap rebuilt (13ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢76 URLs), canonical tags + OG + Twitter cards on all 75 pages, Google Search Console verified, Cloudflare zone activated, media.salus-mind.com connected, 49 sleep story titles added.

### 7 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Automated Audio QA Pipeline

Human QA gate replaced with automated 9-gate system. Click artifact detection and crossfade patching. All 5 deployed sessions scanned and patched. Edge fades added to pipeline.

### 7 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â QA Failure: Degraded Audio Shipped

Loving-kindness build passed click QA but had severely degraded voice quality. Root causes: QA blind spot (clicks only), lossless pipeline violation (WAVÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢MP3ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢WAV), wrong cleanup chain. Fixed with 9-gate system, lossless pipeline, calibrated cleanup.

### 7 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Lossless WAV Pipeline & Email

All intermediate audio now WAV. MP3 encoding once at final step. Channel mismatch bug fixed (mono/stereo misinterpretation). Resend email notification system added.

### 7 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Loving-Kindness Session

Session `36-loving-kindness-intro` deployed (12.9 min, Fish/Marco). 3 build attempts. First 2 failed (overgeneration + channel mismatch). Build 3 passed with 0 artifacts.

### 7 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Ambient Track Fix

4 sessions had ambient shorter than voice. Fixed with 8-hour ambient files. Rule established: NEVER loop ambient.

### 7 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Bible Consolidation (v2.0)

Full consolidation pass. Resolved contradictions (loudnorm ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢24 vs ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢26, block minimum 20 vs 50, five conflicting cleanup chains). Integrated Brief Part 2 items 2ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“9 and Brief Part 3. Added Gate 10 (speech rate), Gate 3 sliding window fix, stop rule governance, build state persistence, overgeneration retry logic, per-chunk loudnorm. Restructured from chronological amendments to functional sections.

### 7 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 14-Gate QA System & Governance (v2.1)

Expanded from 10 gates to 14 gates. All gates now pass/fail ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no informational-only gates. Key changes:

**Gate fixes:** Gate 3 sliding window implemented (18 dB calibrated threshold). Gate 6 converted to speech-aware detection (evaluates non-speech regions only ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â resolved 100% build failure rate from sibilant false positives). Gate 8 Expected-Repetitions metadata replaces global ignore list. Gate 9 converted from informational-only to pass/fail with energy spike detection (10ÃƒÆ’Ã¢â‚¬â€ speech-only median threshold). Gate 10 silence-aware baseline (excludes pause windows from speech rate calculation).

**New gates:** Gate 11 (Silence Region Integrity), Gate 12 (Duration Accuracy), Gate 13 (Ambient Continuity ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â calibrated at ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢80 dBFS / 10 dB), Gate 14 (Opening Quality ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â tighter thresholds on first 60 seconds).

**V3-HD migration:** Complete. All TTS calls use V3-HD with `emotion: calm`. prosody.speed replaces atempo.

**HF shelf cut investigation:** Tested across full tuning range (ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢2 to ÃƒÂ¢Ã‹â€ Ã¢â‚¬â„¢5 dB at 6ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“8 kHz). Failed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â removing 3 kHz boost entirely produced identical Gate 6 flag counts, proving root cause was speech sibilants. Pipeline unchanged.

**Auphonic per-segment:** API does not return per-segment SNR. Noted as platform limitation.

**Governance additions:** No decorative gates principle. No threshold loosening without approval. Brief lifecycle (DRAFT ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ ACTIVE ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ INTEGRATED ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ ARCHIVED). State file separation. Document hierarchy.

**Threshold calibration:** All new gate thresholds validated against known-good deployed sessions (25-introduction-to-mindfulness, 36-loving-kindness-intro). Calibrated values replace brief estimates where they differed.

---

### 8 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Pipeline & Website Updates (v2.2)

**Audio pipeline:**
- Per-chunk loudnorm replaced with whole-file loudnorm (preserves natural dynamics)
- Highshelf boost (`highshelf=f=3000:g=3`) removed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â caused perceived echo on certain words
- Per-chunk QA system: generates up to 5 versions of each chunk (best-of-5), scores all via composite metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance), keeps best
- **Known limitation (9 Feb 2026):** Composite scoring is unreliable for chunk 0 (opening chunk). See Section 9, Opening chunk weakness. Human listening is mandatory for all opening chunks regardless of score.
- Tonal consistency: MFCC distance to previous chunk penalised at 50ÃƒÆ’Ã¢â‚¬â€ weight
- Flag threshold: 0.50 (OK avg=0.708, Echo avg=0.542, calibrated on 27 human-labeled chunks)
- Session 36-loving-kindness-intro rebuilt (build 11, 10.5 min, 14/14 gates)
- Per-chunk QA upgraded from best-of-2 to best-of-5 (135 TTS calls for 27 chunks)
- v3 script rewritten: varied benedictions (no formulaic repetition), trigger words avoided
- v3 build: 14/14 gates, 70% clean rate on human review (19/27 OK, up from 58% on v2)
- Known Fish trigger words expanded: "breath in", "be" (standalone), "simply", "family", "joyful"

**Threshold recalibrations (approved by Scott during live testing session, 8 Feb 2026):**
- Gate 7 widened to 9/14 dB + proportional silence margin (`max(4s, durÃƒÆ’Ã¢â‚¬â€0.15)`) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â required to accommodate Fish chunk-level swings under whole-file loudnorm
- Gate 8 manifest text guard added: word overlap <60% skips MFCC pairs as false positives ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â prevents meditation cadence patterns from triggering duplicate detection
- Gate 9 HF threshold recalibrated to 28ÃƒÆ’Ã¢â‚¬â€ speech-only median, total to 12ÃƒÆ’Ã¢â‚¬â€ ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â calibrated against no-ambient and ambient sessions to separate sibilants from genuine hiss

**Website:**
- Navigation Row 2 now includes Applied Psychology
- New page: `articles/anxiety-thinking.html` (first article detail page, `articles/` subdirectory)
- Applied Psychology page: featured article link, "Updated Regularly" approach item
- Mindfulness page restructured: session cards first, then 7-day + 21-day course banners
- `css/style.css` fixed at source: all light-theme backgrounds neutralised (body, hero, hero-bg::after, daily-quote, section:nth-child(even), filter-btn, sound-category-tag ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ transparent). Per-page overrides no longer needed.
- ASMR page (`asmr.html`): "Coming Soon" placeholder replaced with 14-sound card library (rain, ocean, forest, thunder, birds, fire, stream, cafe, garden, library, night, temple, waterfall, white noise). Category filters (All/Nature/Weather/Spaces/Ambient), animated waveform bars, per-card accent colours, staggered entrance animation. Supersedes old `sounds.html`.

---

### 8 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Dark Theme & Routing Fixes

**style.css dark theme completion:**
- 22 text/background color rules converted from light to dark-compatible: body text (`#f0eefc`), links (`#7c8cf5`), nav (bg `rgba(6,8,16,0.92)` + logo + links), hero paragraph (`rgba(240,238,252,0.55)`), daily quote, section headers, feature cards/icons (`rgba(124,108,240,0.12)`), form inputs/labels, filter buttons, session cards, sound cards
- CSS variables (`:root`) retained for backward-compatible selectors (footer, CTA banner, buttons)

**Login buttons:** Fixed `href="#"` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `login.html` across 11 files (22 instances). Articles subdirectory uses `../login.html`.

**Mindfulness page cleanup:** Removed 6 content sections (276 lines): What is Mindfulness, The Science, Core Practices, How to Start, Mindfulness in Daily Life, FAQ. All had light gradient backgrounds causing white bands. Page now shows session cards + course banners + CTA only.

**Footer routing:** `sounds.html` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `asmr.html` across 60 files (root pages + sessions/ + newsletters/).

**Premium CTA routing:** `newsletter.html` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `apps.html` in media.html, sounds.html, newsletter.html.

**Subsequent completion (same day):** All 15 remaining pages converted to dark theme. Unified `hb-footer` applied to all 82 pages. breathe.html and timer.html heroes rebuilt with dark-theme pattern (radial glow, gradient text). Reading page: miniature book covers via Open Library Covers API, increased description font. Mindfulness page: fixed 7-day course 404 link.

---

### 8 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Learn & Applied Psychology Content Launch

**Learn section (education.html):**
- 17 Learn articles deployed to `articles/` directory across 6 categories: Neuroscience (4), Breathwork (3), Sleep (3), Stress (3), Focus (2), Compassion (2)
- education.html rebuilt: placeholder topic grid replaced with interactive topic-card layout linking to all 17 articles
- Learn vs Applied Psychology distinction tiles added (Learn scrolls to #articles, AP links to applied-psychology.html)
- Each article wrapped in site template (nav, footer, supabase auth, scripts), all back links point to `education.html`

**Applied Psychology section:**
- 9 Applied Psychology articles deployed to `articles/` directory
- Liability review conducted: citation mismatches fixed, crisis language softened

**Site-wide updates:**
- "Growing by the Week" added to session stat labels (sessions.html hero, section header; index.html category card)
- Introduction to Mindfulness locked as premium on mindfulness page (badge changed, data-src removed)
- Sleep story cards: ambient sound labels removed (Garden sounds, Train rhythm, Rain on glass, Ocean & fog horn)
- ASMR audio: clarified as user-provided YouTube downloads cut to 1 hour (not procedurally generated)

---

### 8 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Session 36 Shipped & Review Workflow

**Audio production:**
- Session 36-loving-kindness-intro-v3 shipped to production (v3b focused rebuild)
- `--focus-chunks` CLI argument added: problem chunks get best-of-10, others best-of-5
- Ambient level increased from -14dB to -11dB for more present ambient bed
- Resend email fixed: Python `urllib` blocked by Cloudflare ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ switched to `curl` subprocess

**Human review workflow established (mandatory for all future sessions):**
1. Build with `--no-deploy` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ 14-gate QA runs automatically
2. Extract chunks from raw narration WAV using manifest timing data
3. Upload individual chunks to R2 at `test/chunk-test-{version}/`
4. Create interactive HTML review page with export facility (Copy Results + Download TXT)
5. Listen to every chunk on AirPods at high volume (exposes hiss, echo, tonal shifts that speakers miss)
6. Rate each chunk: OK / ECHO / HISS / VOICE / BAD
7. If acceptable ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ remix with ambient, deploy to R2, update all HTML references, commit, push, email
8. If problem chunks ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ `--focus-chunks 1,3,6` for targeted rebuild, re-review
9. Perfection should not prevent shipping ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â accept reasonable clean rate and move forward

**Testing checklist (learned from session 36):**
- Test playback on BOTH desktop and mobile (CORS blocked mobile audio before R2 CORS was configured)
- Check ALL pages that reference the session (detail page, listing pages, mindfulness cards) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â missed references = broken players
- Verify file duration matches expected (stale CDN cache served old file with wrong duration)
- Players without `data-src` attribute are visual-only ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â buttons do nothing by design
- Mindfulness page uses `m-player` class (inline JS), not `custom-player` (main.js) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â different wiring

**Infrastructure:**
- R2 CORS configured: `salus-mind.com` and `www.salus-mind.com` allowed origins (GET/HEAD)
- Mindfulness page players wired up with real audio for Introduction to Mindfulness and Loving-Kindness Introduction

---

### 8 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â LALAL.AI Integration & Session 25 Rebuild (v3.1)

**LALAL.AI evaluation:**
- Integrated LALAL.AI voice_clean API into `build-session-v3.py` as Phase 1.5 (between chunk QA and edge fades)
- A/B tested on session 25 chunk 28 (voice shift at 6:47) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â LALAL made no difference to voice shift (TTS generation problem, not post-processing)
- Full session rebuild with LALAL (`noise_cancelling_level=1`, `dereverb_enabled=True`): hiss removal excellent (almost all hiss gone), but dereverb stripped Marco's vocal resonance
- Dereverb damages Fish output ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Marco's TTS has no room reverb, so dereverb removes legitimate vocal character
- LALAL disabled in build script pending retest with `dereverb=False` (noise cancellation only)

**Session 25 rebuilt:**
- Trigger word "nowhere else" discovered causing voice shift ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â replaced with "All you need to do is be right here, right now"
- 36 chunks generated (best-of-5), LALAL cleaned 36/36
- 13/14 gates passed; Gate 13 (Ambient) failed on garden-8hr.mp3 dead silence ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â fixed with `-ss 10` offset
- Deployed to R2 (commit acb5842) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â voice quality degraded from LALAL dereverb, fresh non-LALAL rebuild initiated
- Introduction to Mindfulness tile reverted to premium locked (commit c986804)

**Fish Audio observations:**
- Possible S1 model degradation: >500 char generations temporarily routed to v1.6, causing voice inconsistency between chunks
- Opening chunks (1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“5) consistently score lowest ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â chunk 1 has no MFCC reference for voice conditioning
- MFCC tonal distance scoring (threshold 0.50) can miss voice character shifts that human ears catch (chunk 28 scored 0.496)

**New production rules:**
- Raw narration WAVs must never be overwritten without preserving originals (timestamped copies)
- All audio quality comparisons must be narration-only ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â ambient invalidates evaluation
- Garden ambient requires `-ss 10` offset (9.5s dead silence at file start)

**Code mistakes logged:** Failed to preserve pre-LALAL narration, provided ambient-mixed files for comparison instead of narration-only, deployed LALAL build without human review, did not test LALAL settings individually before full pipeline integration. All documented for governance improvement.

---

### 8 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Script Uniqueness & Cross-Session Differentiation (v3.2)

New Section 13A added to address internal repetition across the Salus session catalogue. Sessions were beginning to sound interchangeable ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â same openings, same breath cues, same structural arc, same closings. A customer listening to multiple sessions back-to-back should have distinct experiences.

**Cross-session register system:** Three mandatory register files introduced (`openings-register.txt`, `closings-register.txt`, `phrases-register.txt`) in `content/scripts/`. Every deployed session's key phrases are catalogued. New scripts are checked against existing entries before build ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no phrase of 5+ words may be reused, no opening or closing technique may be repeated within a category.

**Six categories of repetition identified:** Openings, breath cues, body awareness transitions, silence announcements, closings, and structural arc. Each has specific variation strategies and mandatory register checks.

**Automated pre-build originality scan:** Runs alongside trigger word check during pre-flight. Fuzzy-matches new script blocks against register entries (70% threshold on 5+ word phrases). WARNING system, not a build-blocker.

**Checklist updates:** Pre-Build Checklist now includes originality scan. Deployment Checklist now requires register file updates after every session deploy.

**Narration audit (outstanding):** Full audit of all 17 deployed sessions required to retroactively populate registers and identify existing cross-session repetition. Must be completed before any new scripts are written. Added to Section 13A as a pending task.

**External originality (secondary):** Lightweight due diligence step ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â web research to consciously diverge from published scripts, no phrase of 6+ words matching a published source. Research notes stored in `content/scripts/research/`.

---

### 9 February 2026 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Four Sessions Deployed & Build Learnings (v3.3)

**Sessions deployed (commit 752752f):**
- 18-calm-in-three-minutes (3.2 min, stress, rain ambient ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â build 1, 14/14 gates)
- 23-the-calm-reset (5.5 min, stress, stream ambient ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â build 1, 14/14 gates)
- 19-release-and-restore (14.5 min, stress, garden ambient ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â build 4, 14/14 gates)
- 32-observing-emotions (9.5 min, mindfulness, garden ambient ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â build 3, 14/14 gates)

Sessions 18 and 23 are new scripts. Sessions 19 and 23 had scripts rewritten (trigger-word clean). Session 32 is a new script. All four wired into sessions.html and relevant detail/category pages.

**Gate 7 (Volume Surge) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â most persistent failure mode:** Fish Audio's non-deterministic TTS generation causes per-chunk volume variation that triggers Gate 7 surges, particularly after long silences. Session 19 needed 4 builds, session 32 needed 3. The 9.0 dB threshold is correctly calibrated ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â rebuilding eventually produces level-consistent generations. Longer sessions with more chunks have higher failure probability. Documented in Gate 7 section.

**Character estimation overestimates duration:** The ~7.2 chars/sec formula overestimated session 32 (scripted for 12 min, TTS produced 9.5 min). The build script's own duration estimate after dry run is more reliable. Updated Section 13 table with caveat: use 7.2 chars/sec for rough planning only, set Duration-Target from dry run output.

**Garden ambient offset confirmed automated:** `-ss 10` offset now applied in both Fish and Resemble mix paths in `build-session-v3.py`. Updated non-negotiable rule 16 to reflect confirmed implementation.

**New ambient file:** `stream-extended.mp3` created for longer sessions using stream ambient.

---

### 9 February 2026 Ã¢â‚¬â€ Repair Trial & LALAL Removal (v3.4)

**Repair trial completed (session 32, chunk 1):**
- Defect: echo on "something" in opening chunk (composite score 0.426)
- Best-of-10 regeneration: 3 of 10 versions beat the original, 7 scored below 0.364
- Selected version (v4): combined 0.417Ã¢â€ â€™0.467, quality 0.426Ã¢â€ â€™0.490, echo risk Ã¢Ë†â€™15%
- Splice: 100ms cosine crossfade at speechÃ¢â€ â€™silence boundary, tonal distance 0.000443 (0.09% of threshold), very likely inaudible
- 14/14 QA gates passed on repaired file
- Repaired file uploaded to R2 as `32-observing-emotions-repair-1.mp3` Ã¢â‚¬â€ human A/B review confirmed echo eliminated, promoted to live same day
- Full report: `docs/repair-trial-RESULTS.md`

**Section 16A added Ã¢â‚¬â€ Chunk Repair Pipeline:** Documented the full repair process (when to use, step-by-step process, splice rules, trial results). Includes repair backlog of 10 flagged chunks across 5 sessions with scores and priorities. **Approved for production use** after human A/B review confirmed session 32 repair. Code authorised to run targeted best-of-10 repairs on all flagged chunks autonomously.

**LALAL.AI removed from pipeline:** Dehiss-only mode (`dereverb_enabled=False`) tested on session 25 chunk 1 (worst hiss at Ã¢Ë†â€™7.26 dB). Result: uniform 3 dB attenuation, SNR unchanged. LALAL applies flat volume reduction, not selective denoising. All LALAL configurations now tested and failed. Architecture table updated, DO NOT APPLY list updated, status changed to DEAD.

**Hiss mitigation conclusion:** No external post-processing service can selectively remove Fish-generated hiss. The only viable strategies remain: (1) trigger word avoidance, (2) best-of-N chunk scoring, (3) ambient masking.

**QA report inspection:** 7 sessions visually inspected. Sessions 18 and 36 warrant focused listening (sibilant density / tonal shift flagged).

**Session 25 wiring fix:** Player class changed from `player` to `custom-player` + `data-src`. Commit 412a546, pushed.

**Master preservation:** 7 sessions preserved (14 WAVs), 7 chunk schedules created, 10 production records created.

**Part D added Ã¢â‚¬â€ Action Ledger:** New section tracking outstanding actions, decisions pending, and items requiring human input.

---

### 9 February 2026 Ã¢â‚¬â€ Chunk 0 Root Cause, Scoring Bias, Production Readiness (v3.5)

**Chunk 0 cold-start root cause proven:**
- Session 19 chunk 0: 30 consecutive generations across 3 text variants (original, rewrite, split) all produced echo
- Root cause: Fish cold-starts chunk 0 with no conditioning reference. Tail end of unconditioned passages degrades regardless of text content
- Words were never the problem Ã¢â‚¬â€ proven by elimination (same result across completely different text)
- This is NOT a trigger word issue and would not be caught by the pre-flight scan

**Split Chunk Technique (PROVEN):**
- Fix: split opening text into two short chunks. Chunk 0a is one short sentence (~40Ã¢â‚¬â€œ60 chars), chunk 0b carries the rest
- Fish generates short sentences cleanly without conditioning Ã¢â‚¬â€ no time to drift
- Chunk 0b gets 0a as its conditioning reference Ã¢â‚¬â€ chain anchored
- Human listening confirmed split-chunk audio was clean despite scoring system flagging all 30 generations
- New mandatory script rule: opening chunk must be one short sentence under ~60 chars (Section 13)

**Scoring formula bias on chunk 0:**
- The composite metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance) systematically over-penalises unconditioned chunks
- Calibrated against mid-session chunks with conditioning context Ã¢â‚¬â€ chunk 0 will always score poorly
- A chunk 0 scoring Ã¢Ë†â€™358 combined with 0.7 echo risk can sound perfectly clean
- **Automated scores must not be used for pass/fail on chunk 0. Human listening is the only reliable gate.**

**Session 19 repaired and deployed:**
- Chunk 0 split into two short chunks, remixed with correct ambient (garden, not rain as originally built)
- Code diagnosed root cause autonomously through systematic elimination: text Ã¢â€ â€™ rewrite Ã¢â€ â€™ structure

**Section 15A added Ã¢â‚¬â€ Production Readiness:**
- Pipeline assessed as ready for mass production of meditation sessions
- Documented: automated QA + proven repair process + characterised Fish failure modes = repeatable quality at volume
- Estimated production time: 30Ã¢â‚¬â€œ60 minutes per session (script to live) once script is written
- Competitive position documented: no competitor has solved AI voice reliability at this level

**Pre-build checklist updated:** Opening chunk length check added as mandatory item.

---

### 9 February 2026 â€” Back-Catalogue Completion, CBT Section Planned (v3.6)

**Back-catalogue milestone:** All pre-v3 sessions rebuilt to current pipeline standard. Sessions 01, 03, 09, 38 rebuilt from scratch (previously had no master WAV or unacceptable flagged chunk rates). Phase 2 chunk repairs completed on sessions 19, 23, 32, 36. The entire deployed catalogue now runs on `build-session-v3.py` with per-chunk QA.

**Gate 10 known limitation documented:** High-silence meditation sessions (e.g., Session 01 at 87% silence) produce false positives on speech rate detection. Added as a known limitation in Gate 10 section â€” human review should override Gate 10 failures on sessions with >70% silence content.

**Fish Audio long-form ceiling formalised:** Session 09 (30 min, narrative sleep story) exhibited volume surges under Fish. New explicit guidance: sessions exceeding 20 minutes of narration content should default to Resemble. Fish can produce longer sessions but quality degrades above this threshold â€” volume inconsistencies, voice drift, and higher rebuild rates. "Best for" line updated in Section 9. **Superseded 12 Feb 2026 — Resemble removed from pipeline.**

**Fish hard failure ceiling documented:** Session 36 chunk 7 failed to improve across 10 regeneration attempts (0/10 improved). New rule in Fish section and Section 16A: when a chunk fails 10 consecutive regenerations without improvement, stop retrying and escalate to human review.

**Duration header verification rule:** Three sessions required header corrections during this rebuild (01, 03, 38). Session 03 was overcorrected (set to 20 min, produced 15.4 min). New pre-build checklist item and Gate 12 note: when setting `Duration-Target` for a rebuild, cross-reference against previous build output rather than estimating from scratch.

**CBT section planned:** New dedicated CBT page approved for development. Will include guided meditation sessions built around CBT principles â€” thought defusion, cognitive restructuring, behavioural activation, and similar exercises framed as self-help practices. No clinical qualifications required for self-help content (consistent with NHS Every Mind Matters approach and existing CBT apps). Key requirements: (1) frame as "CBT-informed guided exercises," not therapy; (2) include disclaimer that these are self-help tools, not a replacement for professional support; (3) maintain the same liability positioning as Applied Psychology articles; (4) scripts require careful psychological review given the territory. Page structure, session count, and placement (standalone vs AP sub-section) to be decided.

**Pre-build checklist updated:** Duration-Target cross-reference added as mandatory item.

---


### 9 February 2026 — Echo Detection Investigation, Label Pipeline, Review Workflow (v3.7)

**Section 16B added — Echo Detection:**
- Comprehensive investigation: composite scorer, local DSP, Auphonic API, combined approach, and Whisper confidence all tested against 55 human-labelled chunks
- Core finding: Fish Audio's "echo" is a generative distortion, not acoustic reverb. No off-the-shelf echo detection tool works because the artefact has no physical echo signature
- Auphonic ruled out for echo detection (AUC 0.341 — anti-correlated, flags clean chunks and misses echo)
- Whisper confidence (`word_prob_p10`, Cohen's d = −0.66) shows strongest signal but insufficient data (12 ECHO examples) for predictive use
- Whisper integrated as visual cue on review page: blue border on bottom 30% chunks, filter button, badge with score
- Next steps documented: 50+ ECHO examples for Whisper revalidation, 200+ for spectrogram CNN approach
- Human ears remain the only functioning echo gate

**Label server documented:**
- `label-server.py` (localhost:8111) added to infrastructure section
- Auto-POST on every review page rating, auto-sync on page load for session 52+
- CSV storage in `reference/human-labels/` — labels must never require manual export
- Root file list updated to include `label-server.py`, `score-chunks-whisper.py`, `echo-detector.py`

**Human review workflow overhauled:**
- Label server start added as step 1 (auto-save, no manual exports)
- Whisper scoring added as step 4 (pre-generates confidence badges)
- Review scope rule formalised: full-chunk review mandatory until echo detector achieves <10% false negative rate across 200+ labels
- Chunk review batching documented: Scott feeds labelled data in focused ~1hr testing sessions. Pipeline must always have chunks ready for review.

**Production Readiness correction:**
- Section 15A previously claimed "The scoring system catches echo." This was disproven by human review data (58% false negative rate on echo). Corrected to state the scorer catches hiss, voice shift, and tonal inconsistency — not echo.

**Auphonic section updated:**
- Echo detection results added with full metrics table
- Ruled out as echo detection tool — anti-correlated with human perception

**Session 03 rollback:**
- v3 rebuild had major voice failure on opening chunk
- Rolled back to previous version (16:03 build)
- Voice-fail version archived. Session still needs successful rebuild with split-chunk technique.

**`cpd` shortcut documented:**
- Commit, push, and deploy audio to R2 in a single command
- Added to GitHub Pages deployment section

**Ledger updates:**
- L-02 (Auphonic credentials) moved to COMPLETE
- L-17 added: Session 03 rebuild with split-chunk technique
- L-18 added: Echo detector revalidation at 50+ ECHO examples

---


### 12 February 2026 — v4.2: Auto-Picker, Ambient Mandate, Workflow Revolution

**Source:** Session debrief 12 Feb 2026, automation trial debrief (auto-picker v1→v7, 245 chunks, 10 sessions, 5,146+ candidates), Code gap analysis of Bible v3.7/v4.1.

**Headline:** Auto-picker v7 achieved 96% pass rate on session 39, reducing human review time by ~80% (from ~2 hrs to ~45 min per session). Production workflow fundamentally changed from per-chunk A/B picking to auto-pick → assemble → full-audio review → regen-at-timestamps.

Changes:

- **NEW Section 16E:** Auto-picker documented — algorithm (severity-aware + weight-swept + three-layer cutoff), v7 configuration, validation data (24.5% exact, 59.2% top-3), critical findings (quality score doesn't predict verdict, tonal distance is strongest signal, duration/hiss weights harmful)
- **Section 16D (Vault Workflow):** Revised from 10-step manual process to 11-step auto-picker workflow. Human review shifts from per-chunk picking to full-audio review.
- **Section 3:** CDN cache purge (token, zone ID, curl command). Verdicts API endpoint documented. File organisation updated with new tools.
- **Section 7:** ASMR mobile volume slider fix.
- **Section 8:** 6 new Production Rules — CDN purge (20), ambient mandatory with locked 15/8 fades (21), 150-char split threshold (22), known-pass sacred (23), UNRESOLVABLE chunks need script fix (24), audio parameters locked to Bible values (25). Rule 25 added after Code deployed 0s ambient fade-in (spec: 15s) without authorisation.
- **Section 9:** Mid-sentence conditioning for chunk 0. Fish speaking rate corrected to 10–13 ch/s (was 7.2). Sleep story pause profiles added (12/35/60s). **Resemble AI removed entirely** — Fish is the only TTS provider. All Resemble references, routing rules, cleanup chains, environment variables, and code paths to be removed.
- **Section 12:** NEW Gate 15 — Post-deploy live material scanner (CRITICAL). Automated scan of deployed MP3 for catastrophic failures including ambient fade verification. Two failures on 12 Feb: audio breakdown undetected by 14 pre-deploy gates, and 0s ambient fade-in (spec: 15s) deployed without detection. Both would have been caught.
- **Section 16:** 7 new deployed sessions (01 redeployed, 09 redeployed, 39, 42, 53, 61, 76, narrator-welcome). 4 awaiting full-audio review.
- **Section 16C:** A/B picker status updated (fallback, no longer primary). Rejection reason tags. Solo mode fix. Score ≠ Quality strengthened with 78-verdict dataset. Vault scope updated (54 sessions, 13 deployed, 40 waiting, ~30 hrs remaining).
- **Ledger:** L-15→CLOSED (Resemble removed), L-16→PARTIAL, L-17→COMPLETE, L-27→COMPLETE, L-25 updated (auto-picker, 40 remaining), L-28 priority downgraded (tail detector mitigates), L-29 updated (01 redeployed, awaiting review), L-30 lower priority (ambient masking). New: L-31 (reference library), L-32 (CDN purge automation), L-33 (sleep story pauses), L-34 (auto-picker rollout), L-35 (Gate 15 live scanner), L-36 (Fish Elevated tier), L-37 (Resemble code cleanup).
- **LALAL.AI:** Removed from Architecture table, LALAL subsection deleted from Section 3, LALAL references cleaned from Production Rules 14/15 and DO NOT APPLY list. LALAL.AI is dead — absent from all active sections, preserved in Amendment Log as historical record.

---

### 14 February 2026 — v4.3: Resemble Cleanup, ASMR iPhone Fix, Ambient Fade-In Metadata

**Source:** Workflow cleanup and ASMR bug fix 14 Feb 2026.

Changes:

- **Section 7:** ASMR volume slider iPhone-specific fix. Previous 12 Feb fix addressed mobile broadly; this fix targets iOS-specific behaviour — zero-width bounding rect during CSS transitions, stale touchmove events, and accidental play/pause on slider interaction.
- **Workflows:** Resemble AI removed from both `build-audio-session.yml` and `build-session.yml` — dropdown option and `.env` variable deleted. Ambient fade-in duration now read from script metadata (`Ambient-Fade-In:` header, default 30s) in remix-only mode, replacing the hardcoded 15s value.
- **Script metadata:** `Ambient-dB` and `Ambient-Fade-In` headers added to session 03 (Breathing for Anxiety) as reference for per-session ambient configuration.

---

*Last updated: 14 February 2026 — v4.3: Resemble removed from workflows. ASMR iPhone volume slider fix. Ambient fade-in reads from script metadata.*

---

# PART D Ã¢â‚¬â€ LEDGER

---

## 20. Action Ledger

Outstanding actions, pending decisions, and items requiring human input. Items are added as they arise and removed when resolved. Each item has a status, source (which bible version or event created it), and owner.

### Pending Human Action

| # | Item | Source | Owner | Status |
|---|------|--------|-------|--------|
| L-01 | ~~A/B listen: session 32 repair~~ | v3.4 repair trial | Scott | **COMPLETE** Ã¢â‚¬â€ moved to Completed |
| L-02 | ~~**Auphonic credentials**~~ | v3.4 repair trial | Scott | **COMPLETE** — credits topped up, echo analysis run |
| L-03 | **Sessions 18 & 36 focused listening** Ã¢â‚¬â€ Visual QA flagged sibilant density (18) and tonal shift (36). Requires human listening to confirm or clear. | v3.4 QA inspection | Scott | WAITING |
| L-04 | **Narration audit** Ã¢â‚¬â€ Full audit of all 17 deployed sessions to populate cross-session registers (openings, closings, phrases). Prerequisite for register system. | v3.2 | Scott/Code | WAITING |

### Pending Technical Decision

| # | Item | Source | Owner | Status |
|---|------|--------|-------|--------|
| L-05 | **Session 25: repair or rebuild?** Ã¢â‚¬â€ 4 flagged chunks including opening (worst hiss at Ã¢Ë†â€™7.26 dB). Individual repair may not be efficient Ã¢â‚¬â€ full rebuild likely better value. Code can now run repairs autonomously. | v3.4 repair backlog | Scott | OPEN |
| L-06 | ~~Repair pipeline approval~~ | v3.4 | Scott | **COMPLETE** Ã¢â‚¬â€ moved to Completed |
| L-07 | ~~"Something" as trigger word?~~ Ã¢â‚¬â€ Session 19 chunk 0 root cause analysis proved the issue was chunk 0 cold-start, not word-level triggers. 30 generations across different text all produced echo. Deprioritised. | v3.4 repair trial | Scott | **CLOSED** Ã¢â‚¬â€ not a trigger word issue |
| L-11 | ~~Catalogue repair run~~ | v3.4 | Code | **COMPLETE** â€” moved to Completed |
| L-13 | ~~Retroactive chunk extraction~~ | v3.5 | Code | **COMPLETE** â€” superseded by v3 rebuilds |
| L-14 | **Scoring formula chunk 0 recalibration** Ã¢â‚¬â€ The composite metric is unreliable for opening chunks. Either add a chunk 0 exemption, apply separate calibration for unconditioned chunks, or remove chunk 0 from automated scoring entirely. Current workaround: human listening. | v3.5 | Scott/Code | OPEN |
| L-12 | **Test run on new material** Ã¢â‚¬â€ Next new session build should use best-of-10 as standard for all chunks (not just focused chunks), with the repair pipeline standing by for any flagged chunks post-build. Validates end-to-end quality on fresh content. | v3.4 | Scott/Code | WAITING |
| L-15 | ~~**Session 09 Resemble evaluation**~~ — Resemble removed from pipeline entirely (12 Feb 2026). Session 09 redeployed via auto-picker with grace ambient. Resemble evaluation no longer applicable. | v3.6 | Scott | **CLOSED** |
| L-16 | **CBT section development** — 4 CBT sessions scripted, vault-built, and in picker (78-The Thought Train, 79-The Evidence Log, 80-One Small Thing, 81-The Worry Window). Remaining: page design, disclaimer text, A/B picking or auto-picker run, assembly, deployment. | v3.6 | Scott/Code | PARTIAL |
| L-17 | ~~**Session 03 rebuild**~~ | v3.7 | Scott/Code | **COMPLETE** |
| L-18 | **Echo detector revalidation** — Rejection reason tags and auto-picker verdict history both accumulating labelled data. With ~30 hrs of review ahead at accelerated pace, the 50-label threshold will be reached during normal production. The auto-picker's three-layer cutoff detection provides a complementary signal — cutoff is now reliably detected without the echo detector. | v3.7 | Scott/Code | BLOCKED — needs 50+ ECHO labels |
| L-25 | **Vault session completion — 40 sessions remaining.** Auto-picker v7 replaces manual A/B picking as primary method. ~80% reduction in human time per session (~45 min vs ~2 hrs). 54 sessions in vault, 13 deployed (4 awaiting review), 1 parked, 40 waiting. Rejection reason tags continue accumulating passively during any manual review. | v4.2 | Scott/Code | OPEN |
| L-27 | ~~**Session 03 full rebuild — breathing silence bugs**~~ | v4.1 | Scott/Code | **COMPLETE** |
| L-28 | **Expendable tail padding in vault-builder.py.** The auto-picker's tail cutoff detector (Layer 2: < 12ms trailing silence) now catches end-of-chunk truncation and rejects affected candidates. This mitigates the impact of the truncation bug by ensuring truncated candidates are never selected. However, the underlying ~30% candidate waste remains — clean candidates are still being generated and then rejected. The code fix (append throwaway phrase, trim in post-processing) would recover those candidates and improve tournament quality. Priority downgraded from HIGH to MEDIUM given the tail detector workaround. | v4.1 | Code | MEDIUM — OPEN |
| L-29 | **Session 01 chunk 11 rewrite** — Session 01 redeployed via auto-picker with grace ambient. c11 remains a persistent fail (191 chars, BAD/voice mush, 82% cutoff rate). Needs text split at 150-char boundary and regeneration. Auto-picker selected least-bad candidate for assembly — ambient may mask the issue. **Awaiting full-audio review** to determine if rewrite still needed. | v4.1 | Scott/Code | OPEN |
| L-30 | **Post-assembly conditioning chain QA gate** — The auto-picker workflow with ambient masking reduces the impact of conditioning chain contamination (ambient covers mild downstream hiss). However, the sequential HF scan remains valuable as a safety net. Lower priority given ambient masking, but still OPEN. | v4.1 | Scott/Code | OPEN |
| L-31 | **Curated chunk 0 reference library** — Replace `MARCO_MASTER_WAV` fallback with 3–5 proven Fish-generated chunks from deployed sessions. Mid-sentence conditioning achieved 20/20 pass rate vs ~60% with marco-master. | v4.2 | Code | OPEN |
| L-32 | **Automate CDN cache purge in deploy workflows** — Integrate purge into vault-assemble.py deploy step, `cpd` shortcut, and any R2 upload script. | v4.2 | Code | OPEN |
| L-33 | **Sleep story pause profile** — Add `sleep-story` category to PAUSE_PROFILES in vault-builder.py (12/35/60s). Override when Category=story AND Duration-Target > 20 min. Evidence: session 53 required manual pause scaling. | v4.2 | Code | OPEN |
| L-34 | **Auto-picker production rollout** — Run auto-picker v7 across remaining 40 vault sessions. Establish verdict history per session through iterative review rounds. Target: all 54 sessions deployed within ~30 hours of human review (down from ~58 hours with A/B picking). | v4.2 | Scott/Code | OPEN |
| L-35 | **Post-deploy live material scanner (Gate 15)** — CRITICAL. Automated scan of deployed MP3 on R2 for catastrophic failures: silence dropouts, volume explosions, voice breakdowns, duration deviation, hiss cascades, ambient fade verification. Runs AFTER every deployment. Evidence: two failures on 12 Feb — (1) massive audio breakdown that all 14 pre-deploy gates missed, (2) Code deployed 0s ambient fade-in (spec: 15s) undetected. Both would have been caught. See Section 12, Gate 15 specification. | v4.2 | Code | CRITICAL — OPEN |
| L-36 | **Fish Elevated tier confirmation** — Fish Audio account upgraded to Elevated tier (15 concurrent connections, up from 5 on Starter). Vault-builder.py `MAX_CONCURRENT` updated from 5 to 15. Total generation cost for session 01 trial: ~$116.69. | v4.2 | Scott | OPEN |
| L-37 | **Resemble AI removal cleanup** — Remove all Resemble references from codebase: `build-session-v3.py` Resemble paths, environment variable references, provider routing logic, and any Resemble-specific cleanup chains. The Bible update documents what to remove; Code should execute the actual code cleanup. | v4.2 | Code | OPEN |

### Completed (Recent)

| # | Item | Source | Resolved | Notes |
|---|------|--------|----------|-------|
| L-01 | A/B listen: session 32 repair | v3.4 repair trial | 9 Feb 2026 | Echo on "something" eliminated. Significant improvement confirmed. Repaired file promoted to live. |
| L-06 | Repair pipeline approval | v3.4 | 9 Feb 2026 | Approved for production use. Code authorised to run best-of-10 repairs on all flagged chunks autonomously. |
| L-07 | "Something" as trigger word? | v3.4 | 9 Feb 2026 | Closed Ã¢â‚¬â€ session 19 proved chunk 0 issue is cold-start, not word-level triggers. |
| L-08 | LALAL dehiss-only test | v3.1 | 9 Feb 2026 | Failed Ã¢â‚¬â€ uniform attenuation, not selective. LALAL removed from pipeline. |
| L-09 | Session 25 wiring fix | v3.3 | 9 Feb 2026 | Commit 412a546. Player class corrected. |
| L-10 | Master narration preservation | v3.4 brief | 9 Feb 2026 | 7 sessions, 14 WAVs, 10 production records. |
| L-11 | Catalogue repair run | v3.4 | 9 Feb 2026 | All 4 unscored sessions rebuilt to v3 standard. Phase 2 repairs deployed. Session 36 chunk 7 = Fish hard failure (0/10). |
| L-13 | Retroactive chunk extraction | v3.5 | 9 Feb 2026 | Superseded by full v3 rebuilds â€” all sessions now have per-chunk scoring data. |
| L-02 | Auphonic credentials | v3.4 | 9 Feb 2026 | Credits topped up. Auphonic echo analysis run on full labelled dataset. Ruled out for echo detection (AUC 0.341). |
| L-15 | Session 09 Resemble evaluation | v3.6 | 12 Feb 2026 | CLOSED — Resemble removed from pipeline. Session 09 redeployed via auto-picker with grace ambient. |
| L-17 | Session 03 rebuild | v3.7 | 12 Feb 2026 | Complete. |
| L-27 | Session 03 full rebuild — breathing silence bugs | v4.1 | 12 Feb 2026 | Complete. |

### Ledger Rules

1. **New items get the next L-number.** Numbers are never reused.
2. **Items move to Completed when resolved,** with the resolution date and a brief note.
3. **BLOCKED items** list which other item they depend on.
4. **The ledger is maintained by Claude Desktop** as part of bible updates. Code does not write to the ledger.
5. **Scott reviews the ledger** at the start of each work session to decide priorities.

---

## Document Governance

**Owner:** Scott (via Claude Desktop ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Scott's conversational Claude instance)
**Consumers:** Claude Code, any future contributors

This document is maintained by Claude Desktop on Scott's behalf. Claude Code reads it as a reference but **must not edit, append to, or modify it under any circumstances.** If Code identifies an error, omission, or outdated information, it must report the issue and wait ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not fix it.

Changes to this document follow this workflow:
1. Scott or Claude Desktop identifies needed change
2. Claude Desktop drafts the update
3. Scott approves
4. Claude Desktop produces the updated bible
5. Code receives the new version via brief

This separation exists because Code previously both wrote and read the bible, leading to contradictions, self-certified completions, and unauthorised pipeline modifications. The contractor does not amend the specification.

**Note (8 Feb 2026):** Code edited this document directly during the 8 Feb session. The edits were largely accurate but introduced governance conflicts and contradicted existing non-negotiable rules. This corrected version (v2.2c) restores Desktop ownership and resolves those conflicts. All future Bible edits go through the workflow above.
