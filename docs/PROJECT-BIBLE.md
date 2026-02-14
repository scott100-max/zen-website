# Salus Project Bible

**Version:** 5.0
**Updated:** 14 February 2026
**Purpose:** Single source of truth for all Salus website and audio production standards

This document is the canonical reference for Claude Code and all contributors. Where this document conflicts with earlier briefs, amendment logs, or conversation history, **this document wins**.

---

## Contents

### Part A â€” Website & Infrastructure
1. [Design Standards](#1-design-standards)
2. [Terminology](#2-terminology)
3. [Deployment & Infrastructure](#3-deployment--infrastructure)
4. [Authentication & Payments](#4-authentication--payments)
5. [SEO](#5-seo)
6. [Self-Validation Process](#6-self-validation-process)
7. [Common Issues & Lessons Learned](#7-common-issues--lessons-learned)

### Part B â€” Audio Production
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
16C. [Marco Voice Vault](#16c-marco-voice-vault)
16D. [Vault Production Workflow for Code](#16d-vault-production-workflow-for-code)
16E. [Auto-Picker](#16e-auto-picker)
16F. [Voice Breakout Detection](#16f-voice-breakout-detection)
17. [Governance](#17-governance)
18. [V3 API Emotion System](#18-v3-api-emotion-system)

### Part C â€” Historical Record
19. [Amendment Log](#19-amendment-log)

### Part D â€” Ledger
20. [Action Ledger](#20-action-ledger)

### Appendix
A. [A/B Tournament Picker â€” Complete Source Code](#appendix-a-ab-tournament-picker--complete-source-code)

---

# PART A â€” WEBSITE & INFRASTRUCTURE

---

## 1. Design Standards

### Tile/Card Layout Rules
- **Maximum 2 tiles per row** on all screen sizes (site-wide standard)
- Tiles stack to 1 column on mobile devices
- No coloured gradient tiles/boxes on cards â€” use simple white cards with text only

### Image Guidelines
- **No people in card/tile images** â€” use abstract, nature, or texture imagery only
- **No repeating images** â€” each card/tile must have a unique image site-wide
- Source images from user photo repository when available
- Large images (>1MB) cause browser rendering issues â€” optimise to 600Ã—600px for web
- Always add cache-buster: `?v=YYYYMMDD`

### Card Design Patterns
- **Atmospheric cards** (Sessions, Tools, Education): Full gradient backgrounds with category colours, floating glowing orbs (`filter:blur(40px)`, `opacity:0.4-0.5`), white text on dark backgrounds
- **Glassmorphism elements**: `backdrop-filter:blur(10px)`, `rgba(255,255,255,0.15)` backgrounds, deep coloured shadows

### Category Colour Scheme
| Category | Primary Gradient | Orb Colours |
|----------|-----------------|-------------|
| Beginners/Teal | #0d3d4a â†’ #1a5568 â†’ #0f4c5c | #06b6d4, #22d3ee |
| Stress/Green | #064e3b â†’ #065f46 â†’ #047857 | #10b981, #34d399 |
| Sleep/Purple | #1e1b4b â†’ #312e81 â†’ #3730a3 | #818cf8, #a78bfa |
| Focus/Amber | #451a03 â†’ #78350f â†’ #92400e | #f59e0b, #fbbf24 |

### Dark Theme (Complete â€” 8 Feb 2026)
- All pages fully dark-themed: body `#0a0a12`, text `#f0eefc`
- `css/style.css` `:root` includes: `--deep`, `--teal`, `--text-bright`, `--text-muted`, `--text-mid`
- Auth alert colors use dark-compatible rgba (e.g. `rgba(239,68,68,0.12)` not `#fee2e2`)
- No light backgrounds, no `var(--white)` or `var(--off-white)` in visible elements

### Unified Footer (Complete â€” 8 Feb 2026)
- All pages use `hb-footer` class (4-column: Brand/tagline, Practice, Discover, Salus)
- CSS in `style.css`, responsive: 2-col at 900px, 1-col at 480px
- Subdirectory pages (`sessions/`, `articles/`, `newsletters/`) use `../` prefix on links
- Health disclaimer in every footer
- Copyright: "Â© 2026 Salus Mind. All rights reserved."

### Section Background Blending
- Use `background:transparent` for sections (inherits dark body)
- Subtle differentiation via `rgba(255,255,255,0.03)` backgrounds
- Avoid hard colour lines between sections

### Home Page Layout (12 Feb 2026)

**Hero card hierarchy (12 Feb 2026).** The home page uses a two-tier card hierarchy to signal content depth at £5.99/month:

- **Top row (2 flagship cards):** Guided Meditations and Sleep Stories — larger cards with prominent imagery, positioned as the primary value proposition.
- **Bottom row (4 supporting cards):** Mindfulness, ASMR & Sound Mixer, Learn, Tools — smaller cards, secondary positioning.

**Reframed statistics:** Aggregate numbers to feel abundant without overpromising: "100+ guided experiences", "25+ hours of audio". Individual card counts (e.g. "20+ sessions") read as early-stage when benchmarked against Calm/Headspace. "New content weekly" badges reinforce subscription value.

### Premium Content Flow
- All premium CTAs route to the Subscribe page (`apps.html`)
- Never link premium unlock buttons to Newsletter page
- Premium items display a "Premium" label and navigate to subscribe on click

### Navigation
- Two-row layout applied site-wide
- Row 1: Sessions, Mindfulness, ASMR, Sleep Stories, Learn, About
- Row 2: Tools, Reading, Applied Psychology, Newsletter, Contact (smaller, gray text, `gap:32px`, `font-size:0.9rem`)
- Latin phrase: "SalÅ«s â€” Latin: health, safety, well-being" under hero sections on all pages
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

### Brand Name: SÄlus (with macron)

As of 12 Feb 2026, all instances of "Salus" site-wide use the macron spelling **SÄlus** (813 instances updated across 111 files). The macron reflects the Latin pronunciation and distinguishes the brand. Use "SÄlus" in all user-facing text, HTML, scripts, and documentation. The only exception is code identifiers, filenames, and URLs where special characters cause issues (e.g. `salus-mind.com`, CSS class names).

| Use | Do Not Use |
|-----|-----------|
| SÄlus | Salus (in user-facing text) |
| Sample | Free (for sessions/sounds sections) |
| SÄlus Premium | The SÄlus app |
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


### Stripe Webhook Deployment Rule

The Stripe webhook edge function MUST be deployed with the `--no-verify-jwt` flag. Stripe sends its own `stripe-signature` header, not a Supabase JWT. Without this flag, the Supabase gateway rejects all Stripe requests.

```bash
supabase functions deploy stripe-webhook --project-ref egywowuyixfqytaucihf --no-verify-jwt
```

**Incident (6â€“9 Feb 2026):** Function was redeployed on 5 Feb (v3â†’v4) without the flag. 22 consecutive webhook deliveries failed. Stripe would have disabled the endpoint by 15 Feb. Fixed 9 Feb by redeploying with `--no-verify-jwt`. All secrets verified present.

### Cloudflare R2 (media files)
- **Bucket:** `salus-mind`
- **Account ID:** `e798430a916680159a81cf34de0db9c2`
- **Custom domain:** `media.salus-mind.com` (proxied through Cloudflare CDN)
- **Public dev URL:** Disabled â€” use custom domain only
- **API token** (Edit zone DNS): `yYNUa2enwfPdNnVrfcUQnWHhgMnebTSFntGWbwGe`
- **CORS:** Configured for `https://salus-mind.com` and `https://www.salus-mind.com` (GET/HEAD). Required for cross-origin audio playback from `media.salus-mind.com`.

```bash
# Upload via wrangler CLI:
npx wrangler r2 object put salus-mind/content/audio-free/FILENAME.mp3 --file=./FILENAME.mp3

# Or drag-and-drop in Cloudflare dashboard: R2 â†’ salus-mind â†’ Objects â†’ Upload
```

**File paths in R2:**
- Free audio: `content/audio-free/`
- Sounds (ASMR): `content/sounds/`
- Video: `content/video/`
- Reference: `reference/` (marco master etc.)
- Vault candidates: `vault/{session-id}/` (candidate WAVs, picker pages, manifests)

**Upload reliability (11 Feb 2026 data):** Transient upload failures occur at approximately 0.04% rate (3 of ~7,800 uploads during the catalogue build). All resolve on immediate retry. No systematic patterns â€” these are wrangler/network transients. The vault-builder logs failures and retries automatically.

**ASMR sounds:**
- All ASMR audio is user-provided (downloaded from YouTube, cut to 1 hour each). Not procedurally generated.
- 14 sounds: rain, ocean, forest, thunder, birds, fire, stream, cafe, garden, library, night, temple, waterfall, white noise
- 1-hour cuts stored locally in `content/audio-free/` (e.g. `asmr-stream.mp3`)
- Short clips on R2 at `content/sounds/` for ASMR page playback
- Full-length YouTube source downloads in `content/audio/ambient/youtube-downloads/`

**Media references in HTML â€” two player types:**

Sessions page (`sessions.html`) and session detail pages use `custom-player` (wired by `main.js`):
```html
<div class="custom-player" data-src="https://media.salus-mind.com/content/audio-free/FILENAME.mp3">
```

Mindfulness page (`mindfulness.html`) uses `m-player` (wired by inline JS on that page):
```html
<div class="m-player" data-src="https://media.salus-mind.com/content/audio-free/FILENAME.mp3">
```
Cards without `data-src` show a visual-only player (no audio loaded). Add `data-src` when audio is produced.

### Cloudflare CDN Cache Purge (12 Feb 2026)

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

**Query string variants (12 Feb 2026):** Cloudflare treats each `?v=` cache-buster parameter as a separate cached object. Purging `narrator-welcome.mp3` does NOT purge `narrator-welcome.mp3?v=20260212b`. Both `tools/r2-upload.sh` and `purge_cdn_cache()` in vault-assemble.py scan all HTML files (`*.html`, `sessions/*.html`, `articles/*.html`, `newsletters/*.html`) for `?v=` variants of the R2 key and purge ALL of them in a single API call. Evidence: user tested in incognito after purge and still heard old audio â€” the browser was requesting the `?v=` variant which remained cached.

**Evidence:** Narrator-welcome session served stale audio from CDN after R2 upload until manual purge was performed.

### Domain & DNS
- **Registrar:** reg-123 (salus-mind.com), GoDaddy (salus-mind.co.uk)
- **DNS managed by:** Cloudflare (migrated 6 February 2026 from GoDaddy)
- **Registrar holds nameservers only** â€” all records in Cloudflare dashboard
- GitHub Pages A records: `185.199.108-111.153`
- `www` CNAME â†’ `scott100-max.github.io`
- `media` CNAME â†’ R2 bucket (proxied)

### Large Files
- **NEVER commit audio/video files to git** â€” all media goes to Cloudflare R2
- `.gitignore` excludes `*.mp3`, `*.mp4`, `*.wav`, and media directories

### File Organisation

| Directory | Contents |
|-----------|----------|
| `scripts-archive/` | Old/superseded build scripts |
| `reference/` | Competitor analysis, voice-clone experiments, branding, transcripts |
| `test/` | Test files, audio reports, test HTML pages |
| `docs/` | PROJECT-BIBLE, audio quality analysis, stripe links |
| `batch-rebuild.py` | Automated N-build quality search tool (runs build-session-v3.py in a loop, archives every build, tracks per-chunk scores) |
| `content/audio/ambient/` | Ambient tracks (8-hour versions preferred) |
| `content/audio/marco-master/` | Master reference WAVs and measurements |

**Root should only contain:** HTML pages, `build-session-v3.py`, `audition-voices.py`, `label-server.py`, `score-chunks-whisper.py`, `echo-detector.py`, `CNAME`, `robots.txt`, `sitemap.xml`, `package.json`.

### Verdicts API (12 Feb 2026)

| | |
|---|---|
| **Endpoint** | `PUT/GET /verdicts/{session-id}` at `vault-picks.salus-mind.com` |
| **Storage** | R2 at `vault/{session}/verdicts/verdicts.json` |
| **Auth** | Bearer `salus-vault-2026` (same as picks API) |
| **Purpose** | Stores human review verdicts with severity labels (HARD FAIL / SOFT FAIL / PASS + defect tags) |
| **Used by** | Review page generator, auto-picker (loads verdict history to inform selection) |

### Additional Files (12 Feb 2026)

| File | Purpose |
|------|---------|
| `auto-picker.py` | v7 auto-picker (severity-aware + weight-swept + three-layer cutoff + compound filter) |
| `sweep-weights.py` | Weight sweep tool (230+ combinations across 5 phases) |
| `tools/review-page-generator.py` | Standard review page template with severity, auto-advance, keyboard shortcuts |
| `tools/r2-upload.sh` | Bash wrapper: uploads to R2, purges CDN cache (including ?v= variants), verifies served file md5 matches local |
| `.git/hooks/pre-commit` | Blocks commits if narrator-welcome script text and homepage HTML text diverge |
| `docs/auto-picker-validation.json` | v7 final validation (245 chunks, 10 sessions) |
| `docs/weight-sweep-results.json` | Weight sweep phases 1â€“3 data |
| `docs/weight-sweep-phase4.json` | Tonal/hiss sweep data |
| `tools/remix-session.py` | Fast ambient remix using existing loudnormed voice masters. Reads ambient from session-registry.json, supports compound ambients ("+"), ~30s/session. `--deploy` handles R2 + CDN + local copy. Saves `remix-log.json` for audit. |
| `content/session-registry.json` | 55 sessions catalogued. Maps session ID → ambient, category, status. Supports combo ambients. Source of truth for ambient assignments. 52 deployed, 3 script-only (88, 89, 90). |
| `echo-workbench.py` | Echo analysis tool. Steps: `--collect --analyze --classify --report --all`. Main workbench for defect fingerprinting. |
| `reference/echo-analysis/` | Echo analysis outputs: `echo_dataset.json`, `echo_features_granular.json`, `clean_features_granular.json`, `classifier_config.json`, `statistical_results.json` (697 features ranked by Cohen's d), `echo-fingerprint-report.html` |
| `breakout-scanner.py` | Voice breakout scanner. `--scan --all` for full catalogue (~8 min), `--label` for verdict UI. |
| `reference/breakout-analysis/` | Breakout analysis outputs: `breakout-scan-results.json` (population baselines), `breakout-suspects.json`, `breakout-verdicts.json`, `breakout-picker.html` |

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
| Edit HTML/CSS/JS | Change files â†’ `git push` |
| Add new audio/video | Upload to R2 â†’ reference in HTML â†’ `git push` |
| Add new HTML page | Create page â†’ add to sitemap.xml â†’ add to nav on ALL pages â†’ `git push` |

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
- `profiles` â€” User data (auto-created on signup via trigger)
- `subscriptions` â€” Stripe data (user_id, stripe_customer_id, status, plan_type)

**Premium Logic (in order):**
1. Check Supabase `subscriptions` table for active subscription (cross-device)
2. Fall back to localStorage `salus_premium` (legacy/single-device)
3. Migration banner prompts localStorage-only users to create accounts

**Premium Unlock Gap Fix (14 Feb 2026):** `auth.js` `updateNavUI()` was missing handlers for `.sp--locked` session cards and `#subHook` / `.m-hook` ("Go Premium" banner) on the mindfulness page. Both selectors now added to the `isPremium()` branch: `querySelectorAll('.sp--locked')` → `display:none`, `getElementById('subHook')` → `display:none`. Commit: `fc8157c`.

### Stripe

**Webhook endpoint:** `https://egywowuyixfqytaucihf.supabase.co/functions/v1/stripe-webhook`

**Events handled:**
- `checkout.session.completed` â†’ Create subscription
- `customer.subscription.updated` â†’ Update status
- `customer.subscription.deleted` â†’ Mark expired
- `invoice.payment_succeeded` â†’ Renew period
- `invoice.payment_failed` â†’ Mark past_due

**Auth Flow:**
1. User signs up â†’ Supabase creates `auth.users` + `profiles` record
2. User logs in â†’ Redirected to dashboard (or original page via `?redirect=` param)
3. User subscribes â†’ Stripe checkout includes `client_reference_id={user_id}`
4. Payment completes â†’ Webhook creates `subscriptions` record
5. User logs in anywhere â†’ `SalusAuth.isPremium()` returns true

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
1. **Source of truth:** `docs/FIXES-CHECKLIST.md` â€” not the validation script
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
â€”â€”â€”â€”â€”â€”â€”â€”â€”â€”â€”â€”â€”â€”â€”â€”â€”
Done:     X items
Pending:  Y items  â† WORK REMAINING
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
5. Treat Code like a subcontractor â€” never let the person who did the work also sign it off

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

### ASMR Mobile Volume Slider Fix (12 Feb 2026)

Volume slider on ASMR cards was unusable on mobile â€” browser hijacked touch drags for scrolling. Fix: `touch-action: none` on slider, larger thumb (14px â†’ 22px), `touchmove`/`touchend` stopPropagation, `change` event listener for iOS Safari.

### iOS Safari: audio.volume Is Read-Only (14 Feb 2026)

**Rule: Any per-track volume control must use Web Audio API GainNode, never `HTMLMediaElement.volume`.**

The ASMR player was broken on iPhone from launch until 14 Feb 2026 because every `audio.volume = v` call was silently ignored. iOS Safari treats `audio.volume` as read-only â€” the assignment succeeds without error but the value never changes.

**Fix:** Create a shared `AudioContext`, route each `<audio>` element through `createMediaElementSource()` â†’ `GainNode` â†’ `destination`, then set `gain.gain.value` instead of `audio.volume`. Must also call `ctx.resume()` on first user interaction (iOS suspends AudioContext until a gesture).

**Scope:** This applies to ANY future audio player on the site â€” the meditation player, any mixer, anything with a volume slider. If it uses `audio.volume`, it is broken on iOS.

### Narrator Script/HTML Sync (12 Feb 2026)

The narrator-welcome text appears in two places: the script file (`content/scripts/narrator-welcome.txt`) and the homepage HTML (`index.html`). When the script is edited, both must be updated. A pre-commit hook (`.git/hooks/pre-commit`) extracts chunk texts from the script file and verifies each line exists in `index.html`. Blocks the commit with a clear error if they diverge. Evidence: script was updated with "In a world built for speed" line but homepage HTML still showed old wording â€” audio and visible text were out of sync.

### QA Gate Failure Pattern (7 February 2026)

**Pattern:** Code builds tooling that produces quality data (visuals, reports, metrics) without building tooling that acts on it (decision logic, thresholds, fail conditions). Builds pass because no gate evaluates the evidence. Human review catches what the pipeline should have caught.

**Incidents:**
- 4 Feb: Rainfall Sleep Journey â€” analyser reported PASS on a file with voice changes, repeated content, and hiss
- 7 Feb: Loving-kindness â€” 9 gates passed on a file with audible hiss spike at 0:30 and catastrophic hiss wall from 12:00, both visible on Auphonic and Gate 9 visuals

**Prevention:** All gates must be pass/fail. No informational-only gates. Visual analysis must include programmatic evaluation, not just image generation.

---

# PART B â€” AUDIO PRODUCTION

---

## 8. Production Rules (Non-Negotiable)

1. **One vault build PER SESSION at a time.** Do not run vault-builder.py on the same session concurrently â€” this will produce duplicate candidates and corrupt the manifest. Running vault-builder.py on DIFFERENT sessions concurrently is permitted but expect heavy 429 rate-limiting under the Fish Starter tier (5 concurrent connections shared across all agents). Generation failures from rate exhaustion are acceptable if sufficient candidates are generated per chunk (minimum 10 OK candidates). If generation failures exceed 30% of a chunk's attempts, pause and let the other agent complete before retrying. *Note: the original single-build rule ("never run builds in parallel") was for the pre-vault world where parallel full-session builds burned 100K credits. The vault workflow generates individual chunks, making per-session isolation sufficient.*
2. **Always dry-run first.** Check block count and silence totals before spending credits.
3. **Fish has a ~60% rebuild rate on 45-min stories.** This is expected. Rebuild until it lands.
4. **Never identical gaps.** All pauses go through `humanize_pauses()`. **Exception 1: explicit `[SILENCE: X]` directives in breathing exercises are sacred.** When a script specifies `[SILENCE: 4]` / `[SILENCE: 5]` / `[SILENCE: 6]` for breathing phases (inhale/hold/exhale), those durations must be rendered exactly â€” no Â±30% randomisation. The breathing rhythm is intentionally precise. `humanize_pauses()` must either skip `[SILENCE: X]` directives entirely, or vault-assemble.py must accept a `--no-humanize` flag for breathing sessions. Ellipsis pauses (`...`, `......`, `........`) still humanise normally. *Root cause (session 03): `humanize_pauses()` applied Â±30% variance to all pauses indiscriminately, turning a precise 4-5-6 breathing rhythm into 3.1-6.2-4.8.* ~~**Exception 2: sleep stories â€” never humanise.**~~ **REMOVED 12 Feb 2026.** Humanise pauses re-enabled for sleep stories. Without humanisation, sleep stories assembled at approximately half their target duration (session 53: 10.3 min vs 23.2 min target). The rigid short pauses removed the breathing room that gives sleep stories their pacing. All sleep stories now use humanised pauses with the `sleep-story` pause profile (see Section 9).
5. **Marco is the only voice.** Do not audition alternatives unless Marco is discontinued.
6. **QA is two-stage.** For vault-built sessions: the A/B tournament picker is the primary per-chunk quality gate (human ears on every chunk), followed by post-assembly automated gates on the spliced output **including mandatory sequential HF scan (Production Rule 19)**. For legacy single-build sessions: the pipeline runs 14 automated gates, then human review is MANDATORY before deploy. Neither stage alone is sufficient in either workflow. Use `--no-deploy` to hold builds for review.
7. **Deploy after human review.** Default build mode is `--no-deploy`. Build runs â†’ 14 gates â†’ human review â†’ only then deploy to R2. Automatic deploy (without `--no-deploy`) is available but should only be used for re-deploys of already-reviewed sessions.
8. **Email is mandatory.** Every completed build cycle ends with an email to scottripley@icloud.com â€” pass or fail.
9. **Fully autonomous** (except where a STOP rule is triggered â€” see [Section 17](#17-governance)).
10. **No OneDrive.** All files go to git (code) or Cloudflare R2 (media). Never copy files to OneDrive.
11. **No post-build splicing â€” with two exceptions.** Never splice individual chunks into an existing build during normal production â€” splicing causes tonal seams at splice boundaries (tested and failed). Selective regeneration WITHIN a build is permitted: `--focus-chunks` gives problem chunks more generation attempts (best-of-10) while others get best-of-5. **Exception: the Chunk Repair Pipeline (Section 16A)** permits targeted splice repair of deployed sessions under controlled conditions: 100ms cosine crossfade, speechâ†’silence boundary targeting, tonal distance measurement, and mandatory human A/B review before promotion to live. This exception exists because full rebuilds risk introducing new defects in currently-clean chunks. The repair pipeline was validated on 9 Feb 2026 (session 32 chunk 1).
**Exception 2: Vault assembly (Section 16C)** concatenates human-picked chunks with 15ms cosine edge fades. Vault assembly is the standard production method â€” the splicing prohibition applies to ad hoc patching of single-build outputs, not to controlled vault assembly from verified picks.
12. **Automated gates: 100% pass required.** All 14 gates must pass â€” no exceptions. Human review: accept a reasonable clean rate and ship. Perfection should not prevent shipping, but the clean rate and any flagged chunks must be documented in the build record. If a session ships below 100% human clean rate, the specific issues accepted are logged for future pipeline improvement.
13. **Lossless pipeline.** All intermediate audio MUST be WAV. MP3 encoding happens exactly ONCE at the final step.
14. **Never overwrite raw narration.** Raw narration WAVs must be preserved before any processing that modifies them. Save timestamped copies: `{session}_raw_v1.wav`, `{session}_raw_v2.wav` etc. If any cleaning service is applied, both pre-clean and post-clean versions must be saved to `content/audio-free/raw/`. Never leave raw files in temp directories, never overwrite without preserving the original.
15. **All audio comparisons must be narration-only.** When evaluating audio quality differences (A/B testing, LALAL before/after, pipeline changes), always compare raw narration without ambient. Ambient masks differences and makes evaluation invalid. Both A and B files must be provided simultaneously with clear naming (e.g. `session-A-narration.wav`, `session-B-narration.wav`).
16. **Garden ambient offset.** `garden-8hr.mp3` has 9.5 seconds of dead digital silence at the file start. Always use `-ss 10` when mixing garden ambient. This is automated in `build-session-v3.py` for the Fish mix path (confirmed 9 Feb 2026).
17. **No atempo on Fish output.** Do not use ffmpeg atempo filter on Fish TTS audio at any ratio. It distorts Marco's voice character. For pace adjustment, use pace filtering: generate extra candidates and select those that naturally fall within the desired duration range. Tested and failed at 0.85Ã—, 0.90Ã—, 0.95Ã— (9 Feb 2026).
18. **All vault data backed up to R2 and git.** Vault candidate WAV/MP3 files upload to R2 at `vault/{session-id}/` after generation completes. Metadata files (scores JSON, manifests, inventory, generation logs, picks) commit to git under `content/audio-free/vault/{session-id}/`. No vault data exists only on a local machine. If the machine dies, everything is recoverable â€” audio from R2, metadata from git. This backup step is part of the vault-builder workflow, not an afterthought. A vault generation run is not complete until both R2 upload and git commit are confirmed.
19. **No vault-assembled session deploys without post-assembly sequential HF scan (pre-deploy).** After vault-assemble.py produces the final narration WAV, a windowed HF scan (10-second windows) must confirm no conditioning chain contamination before deployment. A single hissy chunk (even one that sounded acceptable in isolation during A/B picking) can cascade hiss through every subsequent chunk in the assembled audio because Fish uses the previous chunk as voice conditioning reference. This defect is **invisible during A/B picking** â€” it only manifests in the assembled sequence. Evidence: session 01 shipped with hiss from 5:10 onwards (chunk 11 contaminated all downstream chunks), despite all chunks passing isolated A/B review. The old single-pass build of the same session was clean. The vault was reverted and the old build restored. **This rule exists because the vault workflow broke the conditioning chain assumption that single-pass builds got for free.** Scan threshold: any 10-second window with HF above âˆ’36 dB flags the session for human review before deploy. **Threshold calibration note (14 Feb 2026):** The âˆ’36dB threshold flags virtually every Fish V3-HD session (40â€“120 windows per session). This is normal Fish spectral content, not conditioning chain contamination. The threshold should be raised to ~âˆ’30dB, or the check should compare against a Fish baseline rather than absolute silence. Currently non-blocking (warning only) but noisy. [L-45]
20. **CDN cache purge after every R2 upload.** Cloudflare CDN caches media.salus-mind.com aggressively. After uploading any file to R2, immediately purge the specific URL **and all `?v=` query string variants** (Cloudflare treats each variant as a separate cached object). Use `tools/r2-upload.sh` (bash) or `purge_cdn_cache()` in vault-assemble.py (Python) â€” both scan HTML for variants automatically. See Section 3 for token and curl command. Evidence: narrator-welcome served stale audio even after purging the base URL because the HTML referenced it with `?v=20260212b`.
21. **Ambient is mandatory for all sessions.** All sessions MUST be mixed with ambient before final review and deployment. Grace ambient (or similar warm tonal pad) at per-source gain level (see Section 11), **30s fade-in (structural pre-roll), 60s fade-out** (canonical spec â€” amended 13 Feb 2026). Ambient effectively masks mild echo, hiss, and transition artefacts â€” turns ~80% raw pass rate into ~96% perceived pass rate. Echo tolerance relaxed: mild echo marked OK (not soft fail) when ambient is present. This is not optional. **The fade values are locked. Do not modify without a Bible amendment.**
22. **Fish split threshold is 150 characters (lowered from 300).** Chunks exceeding 150 characters get systematically truncated by Fish. The vault-builder's preprocessing step must split at sentence boundaries before generation. Evidence: 9 persistent-fail chunks in session 01 trial â€” 5 of 9 were >150 chars with 78â€“82% cutoff rates. Already implemented in vault-builder.py.
23. **Known-pass versions are sacred.** Human-confirmed clean versions bypass ALL automated filters in future picker runs. Store pass/fail/severity in verdict history, load on every picker run. A candidate rated EXCELLENT by human ears is never re-eliminated by automated metrics, regardless of its composite score. Evidence: session 01 c01 v10 (composite 0.263, below 0.30 floor) was EXCELLENT by ear â€” the composite floor would have killed it.
24. **UNRESOLVABLE chunks require script-level fix.** When the auto-picker eliminates all candidates for a chunk, it is UNRESOLVABLE. Do not silently fall back to the lowest-scoring candidate. Flag for script revision: split text at sentence boundary, regenerate. Evidence: session 09 had 3 unresolvable chunks (c21, c35, c42) â€” all were text-level failures.
25. **Audio processing parameters are locked to Bible values.** Fade durations, loudnorm targets, ambient levels, edge fade lengths, and all other numeric audio parameters documented in the Bible must not be modified by Code without an explicit Bible amendment. Any deviation requires Scott's approval via a brief. Evidence: Code changed ambient fade-in from spec to 0s across 12 Feb deploys â€” uncaught because no post-deploy verification existed.
26. **Raw narration archival before any repair (STOP-rule grade).** Before any repair operation that modifies chunk picks or reassembles the voice master, the current `-vault-voice.wav` must be copied to `archive/` within the vault directory with a timestamped filename (e.g. `{session}-vault-voice-pre-repair-{YYYYMMDD}.wav`). The original first-assembly voice master must never be overwritten – it is the baseline. Post-repair voice masters are retained alongside it. Deletion of any voice master file requires explicit human approval. **This is a STOP-rule-grade requirement:** if the archive copy fails or the archive directory cannot be created, the repair must halt. Evidence: S60 repair required loading the raw narration for chunk-swap reassembly. The file was unavailable – either overwritten during a previous operation or never saved post-assembly. The voice master is the single most expensive asset per session (hours of vault picking, candidate generation). Losing it means rebuilding from scratch. **Relationship to Rule 14:** Rule 14 covers initial raw narration preservation. Rule 26 extends this to repair operations specifically, requiring versioned archival before every modification.
27. **Catalogue ambient assignments override script headers.** The `session-registry.json` ambient assignments (sourced from `Salus_Session_Catalogue.docx`) are the canonical source of truth for which ambient each session uses. Script header `Ambient:` fields are often wrong or generic and must NOT be used as the ambient source. Any tool reading ambient assignments must read from `session-registry.json`, not from script headers.

---

## 9. TTS Providers

### Provider Routing

Fish Audio is the **ONLY** TTS provider. Resemble AI was evaluated and used for early builds but is removed from the pipeline as of 12 Feb 2026. All sessions â€” short-phrase, long narrative, sleep stories â€” use Fish Audio with the vault + auto-picker workflow. The original Resemble routing rule (sessions >20 min default to Resemble) was created before the vault workflow existed. With auto-picker v7 achieving 96% pass rates, there is no quality gap that a second provider would fill.

### Fish Audio â€” PRIMARY PROVIDER

| Setting | Value |
|---------|-------|
| **Voice** | "Calm male" by ANGEL NSEKUYE |
| **Voice ID** | `0165567b33324f518b02336ad232e31a` |
| **Known as** | "Marco" / "Fish man" |
| **Temperature** | 0.3 (consistent but flat emotionally) |
| **Sample rate** | 44100 Hz |
| **Format** | WAV (not MP3) |
| **Character** | Deep resonance, slight accent (possibly Italian), very soothing |
| **Atempo** | ~~0.95x~~ **REMOVED** â€” see pace filtering below and Production Rule 17 |

**Best for:** Meditation, mindfulness, loving-kindness, body scans, breathwork, mantras, affirmations. Reliable up to ~20 minutes of narration content. The previous <15 min guidance was too conservative for short-phrase meditation content. The vault + auto-picker workflow handles sessions of any length â€” session 09 (25.7 min narrative sleep story) and session 53 (23.2 min sleep story) both deployed successfully via auto-picker on 12 Feb 2026.

**Architecture:** One TTS call per text block. Pauses stitched in post-production.

**Critical characteristics:**
- Non-deterministic: same input produces different output every time
- ~60% rebuild rate on 45-min stories â€” this is normal
- Cost: negligible ($10 lasts ages)
- Real cost is TIME, not money
- Raw output: âˆ’16.34 LUFS average, âˆ’4.39 dBTP peak
- Chunk volume spread: ~8 dB (Auphonic leveller data)
- SNR: 45+ dB (broadcast quality without processing)
- No hum, minimal noise floor

**The Fish API is stateless.** There is NO `condition_on_previous_chunks` parameter in the Fish Audio TTS API. Each API call is completely independent. Voice conditioning between chunks is implemented CLIENT-SIDE in `build-session-v3.py` by passing the previous chunk's audio as the `references` input for the next chunk. This is our pipeline's feature, not a Fish feature. Each chunk can be regenerated independently as long as the correct reference audio is provided.

**Possible S1 model degradation (February 2026).** Fish service alert shows generations exceeding 500 characters are temporarily routed to the v1.6 model instead of S1. If some chunks in a build hit S1 and others hit v1.6, different voice characteristics result â€” producing voice shift between chunks within the same session. This is a Fish-side issue outside our control. Story Studio was upgraded in December 2025; infrastructure changes may have side effects. Monitor Fish changelogs for resolution.

**Opening chunk weakness â€” PROVEN ROOT CAUSE (9 Feb 2026).** Chunk 0 (the very first chunk of any session) has no previous audio to condition from. Fish cold-starts without a voice reference, and the tail end of the sentence degrades â€” producing echo on every generation regardless of text content.

**Evidence:** Session 19 chunk 0 tested with 30 consecutive generations across 3 different approaches (original text, rewritten text, split text). All 30 flagged with echo risk 0.6â€“1.2 by the scoring system. However, human listening confirmed the split-chunk audio was clean. The scoring formula's spectral flux penalty systematically over-penalises unconditioned chunks (see below).

**The fix â€” Split Chunk Technique (PROVEN):** Split the opening text into two short chunks. Chunk 0a is one short sentence (~40â€“60 chars). Chunk 0b carries the rest. Fish can generate a short sentence cleanly without conditioning â€” it doesn't have time to drift. Chunk 0b then uses 0a's audio as its conditioning reference, and the chain is anchored from there. Nothing is wasted â€” both chunks are real session content.

**Script rule:** Opening chunks must be one short sentence, under ~60 characters. The second chunk carries the remainder of the opening and receives conditioning from the first. This replaces the previously proposed "throwaway conditioning chunk" approach.

**Merge rule (inverse of split â€” 10 Feb 2026).** If the opening text is split across two very short blocks (both under ~40 chars), merge them into a single chunk 0 of 40â€“60 chars. A 16-character opening gives Fish so little audio that subsequent chunks have insufficient conditioning reference. The merge gives Fish enough material to establish Marco's voice while remaining short enough to avoid cold-start drift. Session 38: merged 16 + 35 chars â†’ 51 chars.

**Runaway generation (50s ceiling â€” 11 Feb 2026).** Fish occasionally enters a mode where the model fails to terminate, producing audio that hits a hard 50-second API ceiling. Runaway candidates have extreme negative composite scores (âˆ’5 to âˆ’17) and tonal distances 50â€“300Ã— normal (e.g., session 56 chunk 6 v05: score âˆ’17.246, duration 50.0s, tonal distance 0.337). The pre-filter eliminates all runaways. They are harmless but consume credits and generation time. No upstream fix is possible â€” this is a Fish model behaviour.

**Systematic truncation (11 Feb 2026).** Certain phrase structures trigger premature end-of-utterance detection in Fish's model, producing audio at roughly half the expected duration. Unlike random quality variation, truncation is 100% reproducible â€” every candidate truncates identically. Regeneration cannot fix this. The fix is upstream: split the affected chunk into two shorter phrases. Evidence: narrator welcome chunk 2 (80 chars, 35 candidates, all truncated to 4.9â€“6.3s against 11.1s expected). List-style constructions ("to help you X, Y, and Z") appear vulnerable.

**End-of-chunk truncation / candidate waste (11 Feb 2026).** Distinct from the systematic truncation above. During vault production, approximately 30% of otherwise clean candidates are lost because Fish clips the final word or syllable of a chunk â€” the audio sounds good throughout but cuts off prematurely at the very end. These candidates pass all other quality checks and would be selectable in A/B picking if complete. The fix is an **"expendable tail"** padding technique: before generation, append a short throwaway closing phrase (e.g. "Right here. Right now.") to any chunk ending in a short closing phrase. Fish generates the full padded text, and the expendable tail is trimmed from the resulting audio in post-processing. This must be applied *before* generation, not after. **Requires code fix in vault-builder.py.**

**Hiss trigger words â€” systematic text-driven failure (11 Feb 2026).** Certain words and phrases cause Fish to produce hiss on every single candidate, regardless of regeneration count. Evidence: session 01 chunk 11 (200 chars, "Notice the cool air entering your nostrils... the gentle rise of your chest...") â€” ALL 21 candidates had hiss, HF ranging from âˆ’34.6 to âˆ’14.7 dB (all above âˆ’40 dB threshold). This is not random quality variation; the text itself triggers the artefact. Identified trigger words: "nostrils", "gentle rise", "entering". Fix is upstream: rewrite the chunk text to avoid trigger words, then regenerate.

**Conditioning chain contamination â€” CRITICAL ASSEMBLY RISK (11 Feb 2026).** Fish is stateless: each chunk uses the previous chunk's audio as a voice conditioning reference. A chunk with hiss (or other artefacts) contaminates every subsequent chunk in the assembled session because each downstream chunk inherits the hiss through the conditioning chain. The contamination compounds â€” it never recovers. Evidence: session 01, hiss breakout at 5:10 (chunk 11) persisted through the entire remaining session (HF jumped from âˆ’49 dB to âˆ’36 dB and stayed). **This defect is invisible during A/B picking** because candidates are auditioned in isolation, where they sound acceptable. It only manifests once chunks are assembled in sequence. Fix: identify and fix the source chunk (the first one with the artefact); once a clean source chunk is in place, all downstream chunks should recover because the conditioning chain is clean again. **Implication for vault-assemble.py:** post-assembly QA must include a sequential hiss scan (e.g. 10-second windowed HF analysis) to detect conditioning chain contamination that isolated chunk review cannot catch.

**Scoring formula limitations â€” GENERAL PRINCIPLE (broadened 10 Feb 2026):** The composite scoring metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance) is calibrated against mid-session chunks that have conditioning context. It systematically produces false catastrophic scores on chunk 0 because unconditioned audio inherently has higher spectral flux variance. A chunk 0 scoring âˆ’358 combined with 0.7 echo risk may sound perfectly clean to a human ear. **Do not use automated scores for pass/fail decisions on chunk 0 or any chunk where the text structure is complex, emotionally charged, or near session boundaries. Human listening is the only reliable gate.

**Additional evidence (10 Feb 2026):** Session 52 chunk 29 (278 chars, emotionally charged courtroom language) had its winner found at v3 scoring only 0.469 â€” below the old 0.50 flag threshold. A score of 0.469 on a chunk that sounds clean to human ears proves the flag threshold would have rejected a good pick. Chunk 53 was wiped entirely by the 0.30 pre-filter â€” all 40 candidates filtered, yet a clean pick was found 3 deep when unfiltered. Automated scoring is a pre-filter only. Human ears make the final selection. This is not a calibration issue â€” it is a fundamental limitation of spectral metrics for detecting Fish's generative artefacts.**

**Fish cleanup chain (CANONICAL â€” use this, nothing else):**
1. Edge fades: 15ms cosine on each chunk before concatenation
2. Concatenate all chunks + silences (WAV)
3. Whole-file loudnorm: `loudnorm=I=-26:TP=-2:LRA=11` on full narration AFTER concatenation
4. Ambient mix (`amix` with `normalize=0`)
5. Final encode: 128kbps MP3 (ONLY lossy step)

Per-chunk loudnorm was REMOVED (8 Feb 2026) â€” whole-file approach preserves natural dynamics between chunks. Requires Gate 7 thresholds 9/14 dB + 4s silence margin to accommodate Fish chunk-level swings.

The `highshelf=f=3000:g=3` boost was REMOVED (8 Feb 2026) â€” A/B testing confirmed +3dB HF boost causes perceived echo on certain words. Loudnorm-only is cleaner with less hiss.

The HF shelf cut (`highshelf=f=7000:g=-3`) was proposed and tested across the full tuning range (âˆ’2 to âˆ’5 dB at 6â€“8 kHz) during the Gate 6 investigation. It failed â€” removing the 3 kHz boost entirely produced identical flag counts, proving the root cause of Gate 6 false positives was natural speech sibilants, not pipeline-induced HF noise.

**DO NOT APPLY to Fish output:**
- ~~lowpass=f=10000~~ (kills clarity and consonant detail)
- ~~afftdn=nf=-25~~ (muffles the voice â€” noise floor already clean at 45 dB SNR)
- ~~dynaudnorm~~ (amplifies silence â€” NEVER use)
- ~~aggressive de-essers~~ (removes natural sibilance)
- ~~highpass=80~~ (not needed for Fish â€” no low-frequency noise)
- ~~highshelf=f=7000:g=-3~~ (tested and failed â€” does not address root cause)
- ~~highshelf=f=3000:g=3~~ (removed 8 Feb â€” causes perceived echo on certain words)
- ~~atempo~~ (any value â€” distorts Marco's voice character. Use pace filtering instead. Tested 0.85Ã—, 0.90Ã—, 0.95Ã— on narrator welcome, all rejected by human review. 9 Feb 2026.)
- ~~LALAL.AI~~ (all modes tested and failed. Dereverb strips vocal resonance. Dehiss-only applies uniform attenuation, not selective denoising. Tested 8â€“9 Feb 2026. Removed from pipeline.)


#### Pace Filtering (replaces atempo â€” 9 Feb 2026)

**Rule: Do NOT use atempo post-processing on Fish output.** Testing on the narrator welcome vault trial confirmed that atempo (tested at 0.85Ã—, 0.90Ã—, 0.95Ã—) distorts Marco's voice character. Post-processing pitch/tempo shift is not viable for Fish TTS output.

**Instead, use pace filtering:** Generate extra candidate versions and filter by natural duration range. Fish's pace varies naturally between generations. For pace-sensitive chunks (openings, short phrases, closings):

1. Define an acceptable duration range for the chunk (e.g., 3.5â€“4.5 seconds for a short greeting)
2. Generate 20+ candidates
3. Keep only those falling naturally within the target range
4. Select the best-sounding candidate from the filtered set

**Evidence:** Narrator welcome chunk 0 ("Hello. I'm Marco. Welcome to Salus." â€” 35 chars). First 20 generations rejected for pace. Third batch of 22 attempts yielded 10 candidates in the 3.5â€“4.5s range (45% hit rate). Selected v20 at 4.46s â€” natural pace, no post-processing. All three atempo-adjusted versions were rejected by human review.

#### Fish Structural Performance Patterns (10 Feb 2026 â€” Court of Your Mind data)

The Court of Your Mind session (66 chunks, ~1,570 candidates, 199 total rejections) produced hard data on what causes Fish to fail at the chunk level. Deep rejections (5+ per chunk) are NOT driven by trigger words. They are driven by structural properties of the text.

**Fish struggles with:**

| Pattern | Evidence | Why it fails |
|---------|----------|--------------|
| Long complex sentences (250+ chars) | Chunks 38 and 41 were the worst performers (9 rejections each) | Fish loses coherence over long syntactic spans â€” voice drifts, pace destabilises |
| Emotionally charged language | "land in your chest", "prosecution returns", "you become the judge" caused consistent rejections | Fish's calm delivery model conflicts with dramatic register â€” it cannot modulate intensity without distorting |
| Short punchy phrases demanding gravitas | "Hold that memory. That is evidence." â€” chunk 40 had 7 rejections | Fish either goes flat (no weight) or overly breathy (forced emphasis) |
| Near-closing long emotional passages | Chunk 62: 17 rejections (session worst). Long + emotionally loaded + near end = trifecta of Fish weaknesses | End-of-session fatigue compounds the long-sentence and emotional-register problems |
| Stacked short phrases in a single chunk | Multiple short declarative sentences back-to-back | Fish cannot hold varied cadence across rapid phrase changes |

**Fish handles well:**

| Pattern | Notes |
|---------|-------|
| Mid-length, evenly paced instructional language | The sweet spot â€” clear, direct, moderate complexity |
| Calm, guiding tone | This is what meditation scripts mostly are, and what Marco's voice was trained on |
| Conversational register without dramatic peaks | Emotional neutrality gives Fish room to deliver naturally |

**Implication for production:** These patterns are structural, not fixable by regeneration. A chunk with a 278-character emotionally charged courtroom monologue will fail repeatedly regardless of how many candidates are generated. The fix is upstream â€” in the script, not the pipeline.

#### Content Category Filter Rate Benchmarks (11 Feb 2026 â€” full catalogue data)

The full catalogue vault build (23 sessions, 12,793 candidates) produced quantified filter rates by content category. Use these for planning candidate counts and picking time estimates.

| Category | Sessions | Avg Filter Rate | Range | Notes |
|----------|----------|----------------|-------|-------|
| Breathing/repetitive | 1 (session 03) | 12.3% | â€” | Fish's sweet spot â€” short, structured, repetitive |
| Stress (short-phrase) | 4 (18, 23, 19, 25) | 19.7% | 12â€“21% | Good performance on direct instructional content |
| Story (narrative prose) | 4 (53â€“56) | 22.9% | 22â€“28% | Remarkably consistent across different story content |
| Mindfulness (standard) | 8 | 20â€“29% | â€” | Varies with complexity |
| Mindfulness (abstract/philosophical) | 3 (42, 43-day6, 44) | 31â€“36% | â€” | Abstract content degrades Fish quality significantly |
| Non-dual/philosophical | 1 (session 43) | 36.4% | â€” | Worst overall â€” 10 blocks required preprocessing merges |

**Structural fixes measurably reduce filter rates.** Session 36 had 7 blocks split before generation and achieved 15.3% â€” the best of any non-breathing session. This directly validates the 200-character ceiling and structural guidelines with production evidence at scale.

**Progressive course difficulty scaling (7-day mindfulness data).** Later days in a progressive course have higher filter rates because content becomes more abstract: Day 1 (basic breath) 16%, Day 2 (anchor) 24%, Day 3 (body) 17%, Day 4 (thoughts) 18%, Day 5 (sounds) 30%, Day 6 (emotions) 32%, Day 7 (open awareness) 32%. Budget more candidates and more picking time for abstract content in later course days.

**Story sessions production profile.** Narrative prose produces remarkably consistent filter rates (22â€“28%) across different story content. Stories require 2â€“5 preprocessing merges (short action sentences like "You step inside." or "You sit down." need merging with adjacent blocks). Story scripts are naturally well-structured for Fish â€” no blocks exceeded 300 chars across any of the 4 stories tested.

**Closing summary chunks.** When a session's closing shifts register â€” from meditative guidance to a conversational summary or wrap-up â€” the tonal distance scorer penalises the shift even when the audio sounds natural. This is expected behaviour, not a scorer defect: the closing genuinely sounds different from the body. Evidence: 7-day course Days 4â€“7 closing chunks were consistently the worst performers; Day 6 chunk 23 had 19/20 candidates filtered (best 0.370). Mitigation: (1) keep closings short and simple (already in structural guidelines), (2) accept that closing chunks will have higher filter rates and lower scores, (3) the picker will present the best available options for human judgement. Do not regenerate closing chunks endlessly chasing better scores â€” the tonal shift is real and unavoidable.

**High-filter-rate chunks: scan filtered pool before regenerating (11 Feb 2026).** When a chunk has 70%+ of candidates filtered, present the filtered candidates for human listening before spending credits on regeneration. The filter's true-rejection rate is high (~92% on tested sample) but it occasionally catches a good candidate. One quick listen through 10â€“12 filtered candidates is cheaper than 20 new API calls. Evidence: session 38 chunk 26 had 15 candidates, 12 filtered â€” v07 (filtered) was the only good one out of all 15. The picker already supports this via the fallback mechanism (presents all candidates when all are filtered). For chunks where some pass and some don't, Code should build a filtered-candidates listening page for the high-filter chunks before regeneration.

**Hard failure ceiling (9 Feb 2026):** Some chunks are unsalvageable with Fish regardless of regeneration count. Session 36 chunk 7 failed to improve across 10 consecutive best-of-10 attempts. When a chunk fails 10 regenerations without any improvement in composite score, stop retrying. Escalate to human review â€” the options are: accept as-is if not audibly jarring, mask with ambient level adjustment, or flag for script revision and regeneration.


### Mid-Sentence Conditioning for Chunk 0 (PROVEN â€” 12 Feb 2026)

**Problem:** Even with the split-chunk technique, chunk 0 still has no audio conditioning reference. The `marco-master` WAV used as a fallback reference produces scores of 0.4â€“0.9 but voice character doesn't match Fish's natural output style.

**The fix â€” Mid-sentence conditioning:** Use a clean, human-picked chunk from a deployed session as the Fish API `references` parameter for chunk 0 generation. Tricks Fish into continuing a conversation rather than cold-starting.

**Evidence:** Narrator-welcome session chunk 0 â€” mid-sentence conditioning (using `c04_v19.wav` from session 42): **20/20 passed filter**, scores 7.5â€“8.8 (vs ~60% pass rate unconditioned).

**vault-builder.py changes:**
- `MARCO_MASTER_WAV` constant added (fallback reference)
- `_generate_one()` accepts `ref_audio_path` and `ref_text` parameters
- Base64-encodes reference audio and adds to Fish API payload as `references`
- Chunk 0: conditions on `MARCO_MASTER_WAV` (interim â€” should be replaced with curated reference library, see Ledger L-31)
- Chunks 1+: conditions on previous chunk's best-scoring candidate WAV

**This is real audio conditioning at generation time, not just post-hoc MFCC scoring.**

### Fish Speaking Rate (CORRECTED â€” 12 Feb 2026)

Fish speaks at **10â€“13 characters per second**, not the previously assumed 7.2 ch/s. The 7.2 figure may apply to Resemble but is wrong for Fish by nearly 2Ã—.

**Evidence (known-good candidates):**

| Chunk | Chars | Duration | Rate |
|-------|-------|----------|------|
| c01 v10 (EXCELLENT) | 58 | 4.3s | 13.5 ch/s |
| c04 v04 (EXCELLENT) | 60 | 6.7s | 9.0 ch/s |
| c08 v10 (EXCELLENT) | 61 | 5.5s | 11.0 ch/s |
| c18 v10 (OK) | 126 | 9.4s | 13.4 ch/s |

**Impact:** All duration estimates and cutoff detection thresholds must use this corrected rate. The auto-picker's Layer 1 cutoff uses `chars/22` (minimum viable duration) and the compound filter uses `cps > 14` (maximum expected rate). Any reference to Fish speaking at ~7 ch/s is incorrect.

### Sleep Story Pause Profiles (12 Feb 2026)

The existing "story" pause profile (1.5/3/5s) is designed for continuous narrative, NOT sleep stories. Sleep stories need dramatically longer pauses â€” ambient fills the silence, lets the mind wander and drift.

| Category | `...` (within-scene) | `......` (scene transition) | End sequence |
|----------|---------------------|---------------------------|-------------|
| `story` (existing) | 1.5s | 3s | 5s |
| `sleep-story` (NEW) | 12s | 35s | 60s |

**Evidence:** Session 53 (The Gardener's Almanac) assembled at 10.3 min with story profile pauses vs 23.2 min target. Manually scaled pauses to 12/35/60s â€” pacing made narrative sense with `......` markers correctly placed at scene transitions.

**The `...` vs `......` distinction in scripts IS meaningful** and maps correctly to within-scene pauses vs scene-transition pauses. This distinction must be preserved in PAUSE_PROFILES.

### ElevenLabs â€” ABANDONED (6 Feb 2026)

Evaluated across 11 builds and Â£90+ in credits. Every approach failed. Evidence archived at `Desktop/elevenlabs-evidence/`.

**Why it failed:** API cannot hold voice consistency beyond 2-3 sequential calls. Studio "audiobook" feature produces continuous speech with no paragraph gaps and voice breakdown. SSML breaks max 3 seconds (sleep stories need 4-8s). Studio API locked behind sales whitelist (403 error).

**Do not revisit ElevenLabs** unless they release a fundamentally different long-form API.

### Fish Audio Female Voices â€” FAILED (6 Feb 2026)

8 female voices auditioned. All inferior to Marco. None had the warmth or natural pacing. Marco remains sole voice.

---

## 10. Marco Master Voice Specification

### Purpose

The Marco Master is the single definitive reference for what Marco sounds like. Every generated session is measured against this file. If it does not sound like the master, it does not ship â€” regardless of what automated gates report.

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
| MFCC cosine distance | â‰¤0.008 (same-text), â‰¤0.06 (production) | 0.0003â€“0.0060 | 0.0003 | 0.0100â€“0.0113 |
| F0 deviation | â‰¤10% | 0.4%â€“5.6% | 0.8% | 14.8%â€“17.4% |

**Not useful metrics (too much variance):** Spectral centroid deviation, RMS deviation. Discarded.

**CRITICAL â€” THE FISH-4 EDGE CASE:** fish-4 was classified as BAD by human listening but measured 0.0003 MFCC / 0.8% F0 â€” indistinguishable from GOOD. This proves automated metrics CANNOT catch every subtle quality failure. Human review remains MANDATORY even when all automated gates pass.

### Voice Comparison Gate â€” Raw vs Raw

The voice comparison gate MUST compare raw audio against the raw master. Pre-cleanup WAV vs raw master. NOT processed audio vs master â€” the cleanup chain changes the spectral fingerprint and causes false failures.

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

**LESS IS MORE.** Fish Audio TTS output is already broadcast-quality clean (45 dB SNR, âˆ’62 dB noise floor). Every processing step trades clarity and character for consistency. Apply the minimum necessary and nothing more.

### Fish Pipeline (CANONICAL)

```
Script (... pause markers)
        â”‚
        Ã¢â€“Â¼
process_script_for_tts() â†’ blocks with pause durations
        â”‚
        Ã¢â€“Â¼
generate_tts_chunk() â†’ Fish API â†’ WAV
        â”‚
        â”œâ”€â”€â”€ OVERGENERATION CHECK: If duration > 2x expected, reject and retry (max 3 retries)
        â”‚
        Ã¢â€“Â¼
apply_edge_fades() â†’ 15ms cosine fade on each chunk (WAV in, WAV out)
        â”‚
        Ã¢â€“Â¼
generate_silence() â†’ WAV (mono, pcm_s16le) via humanize_pauses()
        â”‚
        Ã¢â€“Â¼
concatenate_with_silences() â†’ concat demuxer â†’ WAV
        â”‚
        Ã¢â€“Â¼
WHOLE-FILE LOUDNORM: loudnorm=I=-26:TP=-2:LRA=11 on full narration
        â”‚
        Ã¢â€“Â¼
mix_ambient() â†’ amix (normalize=0) â†’ WAV
        â”‚
        Ã¢â€“Â¼
SINGLE MP3 ENCODE (libmp3lame, 128kbps) â† ONLY lossy step
        â”‚
        Ã¢â€“Â¼
qa_loop() â†’ 14-GATE QA (see Section 12)
        â”‚
        Ã¢â€“Â¼
deploy_to_r2() â†’ send_build_email()
```

### Whole-File Loudnorm (Fish only)

Apply `loudnorm` to the full concatenated narration WAV AFTER assembly â€” not per-chunk. This preserves the natural dynamic variation between chunks that gives Marco his character. Per-chunk loudnorm was tested and removed (8 Feb 2026) because it flattened the delivery and, combined with the highshelf boost, introduced perceived echo on certain words.

The highshelf boost (`highshelf=f=3000:g=3`) was also removed (8 Feb 2026). A/B testing confirmed the +3dB HF boost was causing perceived echo and hiss on words like "settling", "stillness", "feel/feeling", "peace", "ease", "deeply". The loudnorm-only chain is cleaner.

Gate 7 thresholds were widened to 9/14 dB with 4s silence margin to accommodate Fish's natural chunk-level swings under whole-file normalisation.

### Atempo â€” PROHIBITED ON FISH OUTPUT (9 Feb 2026)

~~Marco standard speed adjustment: 0.95x atempo.~~ **REMOVED.** Testing on the narrator welcome vault trial confirmed that atempo at all ratios (0.85Ã—, 0.90Ã—, 0.95Ã—) distorts Marco's voice character. Post-processing pitch/tempo shift is not viable for Fish TTS output. The master file retains its original 0.95x processing but no new production audio receives atempo. Use pace filtering instead (see Section 9).

**Note:** The Marco Master (v1) was processed at 0.95x atempo. This is a historical artefact of the master recording, not a production standard. New masters, if created, would use natural pace with pace filtering.

### Channel Mismatch Bug (RESOLVED)

All files MUST be mono before concatenation. When ffmpeg's concat demuxer joins mono and stereo PCM files, it misinterprets the sample data â€” stereo segments play at double duration. Silence files must be generated as mono (`cl=mono`), not stereo.

### Ambient Rules

**Core rules:**
- Ambient file should be longer than voice track. 8-hour variants are preferred.
- **Short ambient looping (14 Feb 2026):** `remix-session.py` loops ambient files shorter than the session duration. Known short files: waves (77s), train (41s). These loop seamlessly to cover full sessions. The original "NEVER loop" rule (pre-v5) applied to older tooling that produced audible glitches at loop points; the remix tool handles crossfade splicing.
- Use 8-hour ambient files (available in `content/audio/ambient/`)
- Background ambient must not fade in until narrator introduction is complete
- Fade in: 30 seconds, Fade out: 60 seconds
- Fade curve: logarithmic (both in and out)
- `mix_ambient()` file search order: `-8hr` â†’ `-extended` â†’ base name. WAV checked before MP3.

**60-second fade-out was missing from all production (14 Feb 2026 -- CORRECTED).** Discovery during the ambient volume reference audit: no deployed session had the 60s fade-out applied. All sessions ended with an abrupt ambient cut or minimal fade. Corrected across all 53 deployed sessions as part of the batch remix. This was a spec that existed in the Bible but was never implemented in any build.

**Ambient fade-in is a structural pre-roll (MANDATORY â€” 13 Feb 2026).** The fade-in duration (e.g. 30 seconds) defines a period of ambient-only audio BEFORE the narrator begins speaking. The voice track is delayed by the fade-in duration. At t=0 the listener hears silence; the ambient fades in over 30 seconds; the narrator's first words begin at t=30s. The voice must NOT start at t=0 with quiet ambient underneath â€” that is a volume ramp, not a fade-in.

Implementation: Prepend N seconds of silence to the voice-only WAV (where N = fade-in duration), then mix the ambient over the full duration with a logarithmic fade-in curve of N seconds. The result: N seconds of ambient-only audio, then voice + ambient together.

**Evidence:** Line 1333 of the v4.5 Bible already stated this concept ("let the ambient carry the first few seconds before the voice enters") but the implementation was repeatedly misunderstood as a volume adjustment applied concurrently with the voice. Session 01 was deployed 3 times with the narrator starting at t=1s despite "30s fade-in" being specified. The structural definition removes all ambiguity: fade-in duration = voice delay.

**Voice-first loudnorm is mandatory (13 Feb 2026).** Loudnorm the voice track BEFORE mixing ambient. No second loudnorm on the final mix. When loudnorm runs on the combined voice+ambient signal, LRA compression ducks ambient during speech (loud = gain reduction) and boosts ambient during pre-roll (quiet = gain boost). The result is ambient that sounds louder in the pre-roll than during speech. Voice-first loudnorm normalises voice independently, then ambient is added at a flat level.

Correct pipeline:
```
voice WAV â†’ prepend 30s silence â†’ loudnorm voice-only â†’ mix ambient (post-loudnorm) â†’ MP3 (no second loudnorm)
```

**Ambient Volume Reference (14 Feb 2026 — supersedes all previous ambient gain guidance).**

Grace at −14 dB relative to narration is the benchmark level. All other ambient types are expressed as adjustments from this reference point. Grace is considered the ideal balance between ambient presence and vocal clarity.

| Ambient | Adjustment | Effective Level | Notes |
|---------|-----------|----------------|-------|
| **Grace** | −0 | **−14 dB** | Benchmark. All other levels derived from this. |
| Birds | +5 | **−9 dB** | Quieter source format — boost required. |
| Garden | +5 | **−9 dB** | Quieter source format — boost required. |
| Fire | +5 | **−9 dB** | Quieter source format — boost required. |
| Courtroom | −0 | **−14 dB** | Matches benchmark. |
| Ocean | −2 | **−16 dB** | Broadband — naturally prominent. |
| Waves | −2 | **−16 dB** | Broadband — naturally prominent. |
| Rain | −3 | **−17 dB** | Broadband — naturally prominent. |
| Rain-on-tent | −3 | **−17 dB** | Broadband — naturally prominent. |
| Stream | −3 | **−17 dB** | Broadband — naturally prominent. |
| Train | −3 | **−17 dB** | Broadband — naturally prominent. |

*Broadband ambients (rain, ocean, waves, stream, train) sit 2–3 dB below benchmark because their full-spectrum energy naturally fills the mix. Sparse or quieter-source ambients (birds, garden, fire) require a +5 dB boost to achieve comparable presence.*

**Any new ambient types added to the library must be assigned a level in this table before deployment.**

**Mixing method: numpy direct addition only (13 Feb 2026).** ffmpeg `amix` with `normalize=0` silently eats the ambient signal â€” the ambient disappears entirely with no error or warning. Always use numpy:
```python
mixed = np.clip(voice_normed + ambient, -32768, 32767).astype(np.int16)
```

**Fade type:** Linear ramp (`np.linspace`) for both fade-in and fade-out.

**Verification checklist (run on every mix):**
1. Pre-roll RMS rises from ~-76dB to ~-38dB over 30s (5s windows)
2. Voice entry at t=30s shows >20dB RMS jump
3. Ambient RMS consistent during speech (sample at t=60, 300, 600, 1200s â€” should be within 3dB)
4. Tail fading: last 5s RMS < -60dB

**Ambient as masking (standard practice):**

A well-mixed ambient bed makes minor artifacts (soft echo, slight tonal shifts) disappear into the soundscape. This is standard practice in commercial meditation audio â€” every major app uses ambient beds for both atmosphere and artifact masking. The listener's brain attributes the anomaly to the environment rather than the voice.

Different ambient types mask differently. Broadband ambient (rain, stream, ocean) fills the full frequency spectrum and masks more effectively at a given level. Sparse ambient (nighttime birds, wind chimes, temple bells) has gaps where artifacts can peek through and may need higher relative levels or dynamic adjustment to be effective.

**Per-session ambient level:**

Ambient level is set by ear, per session, based on the ambient type and the chunk quality. There is no universal dB target. The person mixing (Scott) listens to the problem chunks with ambient at the proposed level and decides whether artifacts are sufficiently masked.

~~**Ceiling rule:**~~ **REMOVED (14 Feb 2026).** Previously: "If the ambient has to be raised above −8dB, the chunks have a quality problem." Redundant now that the per-ambient volume table defines explicit levels per source. The table itself enforces reasonable limits.

The deployed ambient level is recorded in the Deployed Sessions table (Section 16) for every session, building an empirical reference of what works per ambient type.

**Dynamic ambient (targeted masking) — PARKED (14 Feb 2026):**

Dynamic ambient (per-chunk volume swells to mask specific problem spots) was documented in earlier Bible versions and remains here for reference. **Not currently active.** With breakthroughs in automated fault-finding (Gate 16 echo detection, Gate 17 breakout detection), the need for per-chunk volume swells may be eliminated entirely. Status to be reviewed when fault-finding tooling matures.

*Previous specification (retained for reference):* Swell must be gradual (ramp up over 2–3 seconds, hold through chunk, ramp down 2–3 seconds). Maximum swell: +4dB above session base ambient level. Swell should sound like natural variation. All adjustments documented in build record.

**Available Ambients:**

| File | Duration | Location | Notes |
|------|----------|----------|-------|
| `rain-8hr.mp3` | 8 hr | `content/audio/ambient/` | |
| `birds-8hr.mp3` | 8 hr | `content/audio/ambient/` | |
| `garden-8hr.mp3` | 12 hr | `content/audio/ambient/` | ⚠️ 9.5s dead silence at file start — always use `-ss 10` |
| `rain-extended.mp3` | 70 min | `content/audio/ambient/` | |
| `stream-3hr.mp3` | 3 hr | `content/audio/ambient/youtube-downloads/` | |
| `stream-extended.mp3` | — | `content/audio/ambient/` | Created 9 Feb to cover longer sessions |
| `loving-kindness-ambient.wav` | 15 min | `content/audio/ambient/` | |
| `courtroom.mp3` | 1 hr | `content/audio/ambient/` | New — sourced from R2 ASMR files |
| `harbour.mp3` | 1 hr | `content/audio/ambient/` | New — sourced from R2 ASMR files |
| `rain-on-tent.mp3` | 1 hr | `content/audio/ambient/` | New — sourced from R2 ASMR files |
| `childhood-memories.mp3` | 1 hr | `content/audio/ambient/` | New — sourced from R2 ASMR files |
| `waves.mp3` | 77s | `content/audio/ambient/` | New — short file, loops seamlessly |
| `train.mp3` | 41s | `content/audio/ambient/` | New — short file, loops seamlessly |

Full ambient library: grace, garden, birds, rain, stream, ocean, fire, waves, train, courtroom, harbour, rain-on-tent, childhood-memories, loving-kindness-ambient, plus 8hr/extended variants.

### Ambient Assignment Map (14 Feb 2026)

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

## 12. QA Gate System

### Gate System Restructure â€” Vault World (10 Feb 2026)

The 14-gate system was designed for a single-build world: generate one build â†’ run through automated QA â†’ hope it passes. The vault workflow fundamentally changes what gates need to do, because the failure model has shifted.

**Old world (single build):** Per-chunk defects (hiss, echo, voice drift) are the primary failure mode. Gates must catch them because there is no human review of individual chunks before assembly.

**New world (vault + A/B tournament):** Per-chunk defects are now largely handled by human ears during the A/B pick. The reviewer hears every chunk, compares candidates, and rejects anything that sounds wrong. Gates that catch per-chunk artefacts become advisory pre-filters. Assembly defect gates become more important â€” splicing 66 chunks creates 65 stitch boundaries.

**Gate categorisation under vault workflow:**

| Category | Gates | When | Failure = |
|----------|-------|------|-----------|
| Pre-vault (advisory) | 4, 6, 14 | Before human review | Data for Scott, not a build blocker |
| Post-assembly (mandatory) | 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13 | After vault-assemble.py | Build blocker â€” must pass before deploy |
| Human (primary) | A/B tournament | During picking | Scott decides â€” this is the real quality gate |

**Key instruction for Code:** The vault picker IS the new primary quality gate. The automated gates serve the assembly stage. Do not restructure gate numbering or remove any gates â€” categorise them and adjust their role from "build blocker" to "advisory pre-filter" or "assembly verification" as appropriate. All 14 gates still run. The change is in how failures are interpreted, not whether gates execute.

### Overview

14 gates. ALL gates must pass â€” any failure blocks deploy. There are no informational-only gates. Every gate has a defined pass/fail condition. If a gate cannot fail a build, it is not a gate. Build time is not a constraint â€” all gates run on every build.

### Gate 1: Quality Benchmarks
Measures noise floor and HF hiss in silence regions via `astats`, compared against master benchmarks.

### Gate 2: Click Artifacts
Scan â†’ patch â†’ rescan loop. Detects click artifacts in silence regions (sample-level jump > peak analysis). Applies 20ms cosine crossfades at all stitch boundaries. Repeats up to 5 passes.

### Gate 3: Independent Spectral Comparison
Compares frequency profile of build against master reference WAV.

**Sliding window:** Gate 3 uses 1â€“2 second sliding windows for spectral comparison. If ANY window within a chunk exceeds the hiss threshold, the chunk fails â€” regardless of whole-chunk average.

**Calibrated threshold:** 18 dB above master reference (calibrated against known-good sessions â€” natural speech HF energy reaches up to 17 dB above reference in normal production).

### Gate 4: Voice Comparison
MFCC cosine + F0 deviation vs Marco master. Uses PRE-CLEANUP audio (see Section 10, Voice Comparison Gate).

**Thresholds:** MFCC â‰¤0.008 (same-text), â‰¤0.06 (production). F0 deviation â‰¤10%.

### Gate 5: Loudness Consistency
Per-second RMS sliding window â€” catches per-chunk loudness surges.

### Gate 6: HF Hiss Detector (Speech-Aware)
Sliding-window HF-to-total energy ratio on POST-CLEANUP audio. Evaluates non-speech regions only. Voice activity detection (or build manifest silence regions) excludes speech windows before HF ratio evaluation. This prevents natural vocal sibilants from triggering false positives while retaining full sensitivity for genuine hiss in pauses, silence, and transition regions.

**Thresholds:** 3s minimum duration, 6 dB HF/total ratio â€” unchanged from original calibration.

**Layered hiss coverage:** Gate 6 (non-speech regions) + Gate 1 (whole-file average) + Gate 9 (per-window energy spikes) provide three independent hiss detection systems covering different failure modes.

**History:** Gate 6 originally ran on all audio including speech. This caused 100% build failure rates â€” every build flagged 4â€“11 regions of natural speech sibilants. HF shelf cut was tested across the full tuning range (âˆ’2 to âˆ’5 dB at 6â€“8 kHz) and failed. Removing the 3 kHz boost entirely produced identical flag counts, confirming the root cause was speech sibilants, not pipeline-induced noise. Speech-aware detection resolved the issue without threshold changes or pipeline modifications.

### Gate 7: Volume Surge/Drop
Local-mean comparison with silence exclusion. 9/14 dB thresholds, proportional silence margin for transitions: `max(4s, silence_duration Ã— 0.15)`. Short pauses (8s) get 4s margin. Long silences (50s) get 7.5s margin â€” voice ramp-up after extended silence is proportionally longer.

**Low-baseline skip:** Skip detection when local mean energy is below âˆ’28 dB. This threshold represents ambient/silence regions, not speech. Flagging silence as "surges" is a false positive.

**Non-deterministic TTS level variation (9 Feb 2026):** Gate 7 is the most persistent failure mode during builds. Fish Audio's TTS generation is non-deterministic â€” identical text produces different volume levels on each call. When speech returns after a long silence, this variation can cause surges that exceed the 9.0 dB threshold. The threshold is correctly calibrated (lowering it would mask genuine defects). The correct response is to rebuild â€” eventually a generation set with consistent levels will pass. Sessions 19 and 32 needed 4 and 3 builds respectively; sessions 18 and 23 passed first time. Longer sessions with more chunks have higher failure probability.

### Gate 8: Repeated Content
MFCC fingerprint + Whisper STT with DUAL AGREEMENT â€” both must flag the same timestamps to confirm. 8-word minimum.

**Manifest text guard (8 Feb 2026):** When MFCC finds similar audio segments, the gate checks whether the underlying script text is actually the same. If word overlap between the two segments is <60%, the pair is skipped as a false positive (similar prosody on different text, common in meditation content with repeated cadence patterns).

**Expected-Repetitions metadata:** The `Expected-Repetitions` field in the script header lists phrases excluded from Gate 8's duplicate detection for that session only. This replaces any global ignore list.

```
Expected-Repetitions: May I be, May you be, May they be, May all beings be
```

### Gate 9: Energy Spike Detection (Visual Report)
Generates PNG with waveform, spectrogram, energy plot, and summary. Additionally performs per-window energy analysis (1â€“2 second windows) to detect anomalous spikes.

**Pass condition:** No window exceeds 12Ã— session median total energy AND no window exceeds 28Ã— session median high-frequency energy (above 4 kHz, speech-only windows used as baseline).

**Fail condition:** Any window exceeds either threshold. Flagged timestamps and energy values included in the visual report PNG.

**Calibration note:** The HF spike threshold was recalibrated at 28Ã— speech-only median and total energy at 12Ã— (8 Feb 2026). No-ambient sessions have lower HF median, so sibilants appear as 16â€“25Ã— spikes. Ambient sessions show sibilants at 4â€“8Ã— and genuine hiss at 32â€“36Ã—. The 28Ã— HF threshold catches genuine hiss while passing sibilants in all session types. Fish per-chunk level swings can exceed 10 dB, requiring the generous 12Ã— total energy threshold.

**History:** Previously ran as informational-only with no pass/fail condition. Changed after the loving-kindness build deployed with a catastrophic hiss wall from 12:00 onwards that was clearly visible on the Gate 9 spectrogram but not evaluated programmatically.

### Gate 10: Speech Rate Anomaly Detection
Measures word density per second across the session using sliding windows.

**Silence-aware baseline:** Session average speech rate calculated using speech-only windows. Windows below a speech energy threshold are excluded from the baseline calculation. This prevents long meditation pauses from dragging the average down and causing false positives on normal-paced speech.

**Threshold:** Flag if any 2-second window exceeds 130% of the speech-only session average.

**Meditation-specific rule:** Speech rate should be consistently slow (~100â€“120 wpm / 8â€“10 chars per second). Sudden acceleration to normal conversational pace (~160 wpm) is a defect even if the words are correct.

**Calibration note:** With silence-aware baseline, the session average sits around 3.0â€“3.5 words/second for meditation content. The original implementation included silence windows, dragging the average to ~2.3 w/s and producing 27 false positives per build.

**Known limitation â€” high-silence sessions:** Sessions with silence ratios exceeding ~70% (e.g., extended mindfulness practices with long unguided pauses) will produce false positives even with the silence-aware baseline. The median speech rate drops low enough that normal-paced speech registers as anomalous. When Gate 10 fails on a session with >70% silence content, treat it as a probable false positive and verify by human listening. Do not adjust thresholds to compensate â€” the threshold is correct for standard meditation content.

### Gate 11: Silence Region Integrity
Verifies that every silence region in the manifest actually contains silence. Checks whether pause regions have been filled with audio bleed, stray TTS output, or ambient at the wrong level.

**Implementation:**
1. Reads the build manifest to identify all marked silence/pause regions and their expected durations
2. For each silence region in the RAW narration (pre-ambient mix), measures energy
3. If energy in any silence region exceeds âˆ’50 dBFS, flags it
4. For the MIXED output, verifies silence regions contain ambient-only energy (no voice bleed) by comparing energy against the ambient-only baseline level Â±3 dB

**Pass condition:** All silence regions in raw narration below âˆ’50 dBFS. All silence regions in mixed output within Â±3 dB of ambient-only baseline.
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

**Duration header accuracy (9 Feb 2026):** When rebuilding an existing session, set `Duration-Target` by cross-referencing the previous build's actual output duration â€” not by estimating from character count or guessing. Session 03 was overcorrected from 15 to 20 minutes, producing a 22.9% deviation and a Gate 12 failure. If no previous build output exists, use the build script's dry-run duration estimate. The character-based formula (~7.2 chars/sec) is for rough planning only and should never be the sole basis for the header value.

### Gate 13: Ambient Continuity
Programmatically enforces the rule that there must be no dead silence anywhere in the final track and ambient must continue through all pauses and silences.

**Implementation:**
1. Identifies all pause/silence regions in the mixed output (using the build manifest)
2. For each region, measures energy in a sliding window (1â€“2 seconds)
3. Checks the final 30 seconds of the file â€” ambient fade-out must not create dead silence before the track ends
4. Measures ambient level consistency across pause regions

**Pass condition:** All pause regions above âˆ’80 dBFS. No dead silence anywhere. Ambient energy consistent across regions (within 10 dB).
**Fail condition:** Any dead silence detected, or ambient level inconsistency exceeds 10 dB.

**Calibration note:** Dead silence threshold calibrated at âˆ’80 dBFS (not the originally proposed âˆ’55 dBFS). Quiet ambient tracks measure âˆ’72 to âˆ’77 dBFS in known-good sessions. Ambient consistency tolerance calibrated at 10 dB (not 6 dB) â€” known-good sessions show up to 8 dB range across pause regions.

### Gate 14: Opening Quality (Tighter Thresholds)
The opening is what the listener hears first. TTS glitches concentrate in the first 30â€“60 seconds. A glitch at 8:32 is bad; a glitch at 0:15 is catastrophic.

Runs the following gates with TIGHTER thresholds on the first 60 seconds of the file:

| Gate | Standard threshold | Opening threshold (first 60s) |
|------|-------------------|-------------------------------|
| Gate 1 (Quality Benchmarks) | Noise floor â‰¤âˆ’26 dB, HF hiss â‰¤âˆ’40 dB | Noise floor â‰¤âˆ’30 dB, HF hiss â‰¤âˆ’44 dB |
| Gate 6 (HF Hiss) | 6 dB ratio, 3s min | 4 dB ratio, 1s min |
| Gate 5 (Loudness) | 6.5 dB above median | 6 dB above median |
| Gate 10 (Speech Rate) | 130% of session average | 120% of session average |

**Pass condition:** All tightened thresholds met in the first 60 seconds.
**Fail condition:** Any threshold exceeded in the opening â€” even if the same issue would pass later in the track.

**Calibration note:** Gate 5 opening threshold calibrated at 6 dB (not the originally proposed 4 dB). Known-good sessions show 5.3 dB loudness variation in the opening.

### Overgeneration Retry Logic

If a generated chunk's duration exceeds 2Ã— the expected duration for its character count, reject it and regenerate immediately. Up to 3 retries per chunk before flagging as build failure.

**Expected duration:** Character count Ã· speaking rate. Meditation speaking rate â‰ˆ 100â€“110 wpm â‰ˆ 8â€“10 characters per second.

### Threshold Calibration Reference

These thresholds were calibrated against two known-good deployed sessions (25-introduction-to-mindfulness, 36-loving-kindness-intro) on 7 February 2026. They represent production-validated values, not theoretical estimates.

| Gate | Parameter | Brief estimate | Calibrated value | Evidence |
|------|-----------|----------------|------------------|----------|
| Gate 3 | HF sliding window | 10 dB | 18 dB | Natural speech HF up to 17 dB above reference |
| Gate 9 | HF spike threshold | 4Ã— all-window median | 28Ã— speech-only median (HF), 12Ã— total | No-ambient sibilants at 16â€“25Ã—, genuine hiss at 32â€“36Ã— |
| Gate 13 | Dead silence | âˆ’55 dBFS | âˆ’80 dBFS | Quiet ambient at âˆ’72 to âˆ’77 dBFS |
| Gate 13 | Ambient consistency | 6 dB | 10 dB | 8 dB range on known-good session |
| Gate 14 | Loudness (opening) | 4 dB | 6 dB | 5.3 dB on known-good session |

---

### Gate 15: Post-Deploy Live Audio Scanner (IMPLEMENTED â€” 13 Feb 2026)

**Status:** IMPLEMENTED. File: `tools/gate15-post-deploy.py` (~280 lines). Auto-runs from `tools/r2-upload.sh` after every MP3 deploy (non-blocking per Bible: session remains live, failure is logged). Sends URGENT email via Resend on any check failure.

**Purpose:** Automated scan of the live deployed MP3 file on R2 to catch obvious audio failures that the pre-deploy pipeline missed. This is not a pre-deploy gate â€” it runs AFTER deployment, scanning the actual file that listeners will hear.

**7 Checks:**

| # | Check | Method | Threshold | Catches |
|---|-------|--------|-----------|---------|
| 1 | Catastrophic silence | 5s windowed RMS | < -80 dBFS in speech region | Audio dropout, failed chunks, missing audio |
| 2 | Volume explosion | 5s windowed peak | > -1 dBFS peak | Loudness spikes, uncontrolled surges |
| 3 | Voice breakdown | 1s spectral centroid (numpy FFT) | Centroid <500Hz or >6kHz for >3s | Voice mush, robotic distortion, Fish model collapse |
| 4 | Duration sanity | Total duration vs --duration-min | >30% deviation from expected | Assembly errors, missing chunks, wrong pause profile |
| 5 | Hiss cascade | Butterworth 4kHz HP, 10s windows | HF > -36dB for 3+ consecutive windows | Conditioning chain contamination |
| 6 | Ambient pre-roll | 1s RMS windows, Q1â€“Q4 comparison | Q1-to-Q4 RMS rise < 6dB across pre-roll | Missing or incorrect fade-in |
| 7 | Ambient fade-out | RMS comparison | Final 2s louder than preceding 6s | Missing or incorrect fade-out |

**Threshold calibration (Check 1):** Adjusted from Bible spec -60 dBFS to **-80 dBFS**. At -60, every normal meditation pause with ambient underneath triggered false positives (48 hits on session 03). True catastrophic silence (codec failures, missing chunks) produces near-digital-zero signal well below -80 dBFS. Ambient-level gaps (-55 to -70 dB) are normal meditation design, not catastrophic.

**Check 6 fix (14 Feb 2026 â€” L-42 COMPLETE):** The old -70dBFS absolute threshold false-positived on every session with a correct 30s pre-roll, because the fade starts from silence (by design). New check: divide the pre-roll into quartiles (Q1â€“Q4), measure RMS in each, require at least 6dB rise from Q1 to Q4. This validates the fade-in shape rather than the starting level. A flat pre-roll (no ambient, or ambient not fading in) will fail; a correctly rising fade will pass regardless of absolute starting level.

**CLI usage:**

```bash
# R2 key (auto-prepends CDN base)
python3 tools/gate15-post-deploy.py content/audio-free/01-morning-meditation.mp3

# Full URL with options
python3 tools/gate15-post-deploy.py https://media.salus-mind.com/content/audio-free/01.mp3 \
  --duration-min 14 --fade-in-sec 30 --verbose

# Exit codes: 0 = all pass, 1 = any fail, 2 = download/decode error
```

**Email notification:** On any check failure, sends URGENT email via Resend API to `scott@salus-mind.com`. Subject: `[URGENT] Gate 15 FAIL â€” {session filename}`. Body: full check results with pass/fail status and failure reasons. Requires `RESEND_API_KEY` in `.env`. Non-blocking: email failure does not affect exit code.

**Workflow integration:**

```
Deploy to R2 â†’ CDN cache purge â†’ Gate 15 scan of live URL â†’ Report
```

Gate 15 runs automatically after every deployment. If any check fails, the report flags the session for immediate human review with timestamps of detected issues. The session remains live (speed > perfection) but the failure is logged and acted on in the next review round.


### Gate 16: Echo Detection — Granular Mel Analysis (VALIDATED — 14 Feb 2026)

**The most significant pipeline addition since the vault workflow.**

**Position:** Per-candidate scoring during vault-builder/auto-picker. Runs before assembly.
**Type:** Ranking penalty (continuous score), not binary pass/fail.
**Status:** VALIDATED — blind test on unseen sessions confirmed. AUC 0.793.

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

**Auto-picker integration:** REPLACES the old `echo_risk` (spectral flux variance, `ECHO_RISK_CEILING=0.003`). New weight: `ECHO_RANK_WEIGHT = 200` (unchanged, applied to a signal that actually works). Candidates with Gate 16 score > 2.5 eliminated outright.

**Calibration data:**

| Metric | Value |
|--------|-------|
| AUC (cross-validated, leave-one-session-out) | 0.793 |
| FNR at balanced threshold | 31% |
| FPR at balanced threshold | 18% |
| Precision | 0.889 |
| Recall | 0.686 |
| Training data | 70 echo + 34 clean chunks across 6 sessions |

**Blind test (completely unseen sessions):** Session 38 (Day 1) — 27 chunks: 13 echo found, Gate 16 caught 9 (69%), missed 4. Gate 16 detected 6 echo chunks the human ear missed on first listen. Session 41 (Day 4) — 23 chunks: 10 echo, Gate 16 caught 8 (80%), missed 2. Combined: 71% recall, 50% precision, 29% FNR.

**KEY FINDING:** Gate 16 detected echo the human ear missed on first listen. The two highest-scoring "false positives" (c08=3.42, c12=2.25 on S38) were confirmed as real echo on re-listen. The detector is more sensitive than casual human review for subtle spectral contamination.

**Known limitation — Two echo subtypes:**

| Subtype | Detection | Characteristics |
|---------|-----------|----------------|
| Type A ("Loud Echo") | CAUGHT (69–80%) | Higher energy (+2–4dB), disrupted band correlation (corr_range ≈ 0.047), strong low-mid energy shift |
| Type B ("Quiet Echo") | MISSED (31%) | Lower energy (−2–4dB), intact band correlation (corr_range ≈ 0.024 ≈ clean level), no detectable spectral shift |

Discriminator between caught and missed: `corr_range` (d=1.436, p<0.000001). If corr_range > 0.035, echo is almost always detectable. If corr_range < 0.030, echo looks clean to every feature tested.

**Operating philosophy — "Replace Until Pass":** FPR does not matter for production use. Gate 16 scores all candidates → auto-picker penalises high-scoring candidates → if picked chunk still scores high, regenerate and re-pick → repeat until pass. Regenerating chunks is cheap (seconds, pennies). Shipping echo is expensive (ruins listener experience, erodes trust). Optimise for RECALL, accept false positive waste.

---

### Gate 17: Voice Breakout Detection (VALIDATED — 14 Feb 2026)

**Position:** Per-candidate scoring during vault-builder/auto-picker. Runs before assembly.
**Type:** Ranking penalty (continuous score), not binary pass/fail.
**Status:** VALIDATED — full catalogue scan across 1,721 picked WAVs in 52 deployed sessions. 441 flagged (25.6%), 440 labelled.

**Scan Results:**

| Metric | Value |
|--------|-------|
| Total WAVs scanned | 1,721 |
| Flagged suspects | 441 (25.6%) |
| Confirmed breakout | 237 (53.9% of flagged) |
| Confirmed clean | 187 (42.5% of flagged) |
| Other defect (echo, repeat) | 16 (3.6% of flagged) |
| Sessions with ≥1 breakout | 51 of 53 |
| Scan runtime | ~8 minutes for full catalogue |

**Labelling caveat:** CLEAN was used strictly to mean "no breakout" for the first half of the labelling pass (~#1-200). Echo defects were not tagged during this phase. From roughly #200 onwards, echo was recorded as OTHER_DEFECT. The true defect count is therefore higher than 237+16 = 253 -- some chunks labelled CLEAN contain echo that was not being tracked at that point. The 187 "clean" figure is contaminated and should not be treated as a reliable false positive count.

**Worst sessions:** S09 (11/15 = 73%), S43 (10/17 = 59%), S85 (10/14 = 71%), S63 (8/9 = 89%), S80 (8/9 = 89%). The 21-day mindfulness course is heavily represented in worst sessions -- those scripts may have characteristics that provoke breakouts at elevated rates.

**Two breakout phenotypes:**

| Subtype | Detection | Characteristics |
|---------|-----------|----------------|
| Type A (pitch jump) | CAUGHT | F0 max semitone jump strongest signal. Voice jumps several octaves mid-chunk. |
| Type B (timbral/register shift) | MISSED | No extreme F0/spectral discontinuity. Subtle tonal shift without pitch spike. |

**Known test case results:** S60 c01/v24 (CAUGHT, rank 10), S62 c06/v12 (flagged, rank 334), S43 c23/v14 (MISSED, rank 971).

**Type B research direction:** The current feature set is blind to timbral/register breakouts that do not produce large F0 or spectral discontinuities. Formant-tracking features (F1/F2 discontinuity) and voice-quality measures (jitter, shimmer, HNR shift) may catch this class. S43 c23 is the reference case for validation.

**Score vs reality:** Breakout rate is 49–60% across ALL score ranges — the z-score provides no ranking lift. The scanner is a binary net, not a ranked classifier. It catches defects or it doesn't; score magnitude does not predict severity.

**Operating philosophy — "Replace Until Pass":** Same as Gate 16. The scanner is a net, not a sniper. 237 defects caught, some severe enough to damage the brand. FPR is irrelevant when every chunk has 24 alternatives.

**Cold-start observation:** Breakouts happen in the first ~2 seconds of a chunk or not at all. Feature extraction *could* be optimised to the opening window, but full-chunk scanning retained because echo surfaces later in the chunk.

**Number-word destabilisation:** "Day Two", "five minutes", "three breaths" and similar number-words produce pitch/timbral artefacts at elevated rates. Likely Fish Audio's model struggling with number pronunciation.

**"Thank you for practising with Sālus" closing line:** Problematic across many sessions. Candidate for script rewrite to a simpler closing phrase.

**Bonus defects found:** 4 repeat/loop failures (Fish generating a phrase twice). These are a separate defect class — Gate 17 spectral features will not catch them. Likely needs a Whisper transcription comparison against input text (future Gate 18).

**Three defect classes now identified:** breakout, echo, repeat. Labelling UI allows all three, with overlap flagged. **Overlap observation:** from roughly suspect #200 onwards in the labelling pass, most flags were echo rather than breakout -- the same spectral features catch both defect types. This does not affect QA (all defective, all need replacing) but matters for classifier training: echo, breakout, and repeat must be tagged as separate classes to avoid contaminating training data.

**Critical implementation notes for auto-picker integration:**

1. **Gate 16 is the architectural pattern** — Gate 17 follows the same wiring: extract features at pick time, score, eliminate flagged candidates from pool. Look at how `echo-workbench.py` features were integrated into `auto-picker.py`.
2. **Scope change: picked WAVs → all candidates** — the standalone scanner checks only the picked version. As an auto-picker gate, it must score every candidate in the vault pool so it can pick *around* defective ones.
3. **1,280 unflagged WAVs were never labelled** — false negatives in the clean set are unknown (S43 c23 proves at least one exists). Gate should flag conservatively.
4. **⚠️ Catalogue-wide baselines are sacred** — z-scores are tuned from 1,721-WAV population statistics in `breakout_scan_results.json`. The gate must use those catalogue-wide means/stds as reference, NEVER recompute per session or per candidate pool. Without catalogue-wide baselines, z-scores become meaningless on a 25-candidate pool. This is a footgun that would silently break the gate if someone "improved" it by recalculating baselines per session.

**Files:**

| File | Purpose |
|------|---------|
| `breakout-scanner.py` | Standalone scanner with `extract_breakout_features()`. `--scan --all` for full catalogue. |
| `reference/breakout-analysis/breakout-scan-results.json` | Scan results for 1,721 WAVs (population baselines) |
| `reference/breakout-analysis/breakout-suspects.json` | 441 flagged suspects with scores |
| `reference/breakout-analysis/breakout-verdicts.json` | 440 labelled verdicts |
| `reference/breakout-analysis/breakout-picker.html` | Labelling UI with autoplay for suspect review |



## 13. Script Writing Rules

### Block Size

| | Characters |
|---|---|
| **Minimum** | **50** (below 50 causes TTS instability and hiss â€” root cause of all hiss failures) |
| **Sweet spot** | 50â€“200 |
| **Maximum** | 400 (longer blocks trend toward monotone) |

Blocks under 50 characters must be merged with adjacent blocks or expanded with additional content.

**Silence boundaries are merge barriers (MANDATORY â€” 11 Feb 2026).** The preprocessor must never merge blocks across a `[SILENCE: X]` directive, regardless of the silence duration or the block's character count. If block A is 27 chars, followed by `[SILENCE: 4]`, followed by block B at 30 chars â€” both blocks stay independent. The silence directive is not part of either block's character count and must be preserved exactly as written in the script. This applies to all silence values including breathing phase gaps (4â€“6s) and dramatic pauses (30â€“60s).

**Root cause (session 03):** `vault-builder.py`'s forward merge threshold was `pause < 5`, which treated `[SILENCE: 4]` (a breathing gap) as mergeable. Blocks like "Now hold your breath gently." (27 chars) were swallowed into the previous block, destroying the 4-second breathing gap after "breathe in". The 60-second silence after "Let the birds hold you" was truncated to 6 seconds by the same mechanism. Fix: the merge check must be `pause < 1` or â€” safer â€” never merge across any `[SILENCE: X]` boundary at all.

**For loving-kindness/mantra content:** Combine 3â€“4 short phrases into one block with internal ellipses. Each block 76â€“150 characters. This gives TTS enough context while ellipses create internal rhythm.

### Opening Chunk Rule (MANDATORY â€” 9 Feb 2026)

The first chunk of every session (chunk 0) must be one short sentence, under ~60 characters. The second chunk carries the remainder of the opening.

**Why:** Fish cold-starts chunk 0 with no voice conditioning reference. Long unconditioned passages degrade at the tail end, producing echo. Short sentences complete before degradation begins. Chunk 1 then uses chunk 0's audio as its conditioning reference, anchoring the entire session.

**Evidence:** 30 consecutive generations of session 19 chunk 0 across 3 text variants all produced echo. Splitting into two short chunks produced clean audio immediately.

**Example:**
- BAD: "Find somewhere comfortable to lie down. A bed, a sofa, even the floor. Whatever works for you right now." (one long chunk 0)
- GOOD: Chunk 0a: "Find somewhere comfortable to lie down." â†’ Chunk 0b: "A bed, a sofa, even the floor. Any spot that feels right."

### Opening Tone Rule (MANDATORY â€” 13 Feb 2026)

The first line of any session must not be declarative or jarring. Openings should use a warm, invitational tone â€” the listener has just pressed play and needs a gentle entry point. Avoid cold announcements ("This is your X session"). Prefer affirmations, observations, or sensory invitations that ease the listener in rather than telling them what they are about to do.

**Why:** Session 01 ("This is your morning meditation") demonstrated that a declarative opening feels harsh, especially when the ambient bed is still fading in. The listener's ears are cold â€” the first words set the entire emotional tone. Combined with the 30-second ambient pre-roll (Section 11), a soft opening ensures the listener is eased into the experience rather than jolted.

**Interaction with other rules:**
- Opening chunk must still be <60 characters (above)
- Opening technique must still be unique in `openings-register.txt` (Section 13A)
- This rule adds a tonal constraint on top of existing structural and uniqueness constraints

**Existing sessions to review:** Sessions using "Theme statement" technique (03, 25, 38) should be assessed for harshness during next rebuild cycle. Not urgent â€” these sessions have different ambient/category contexts that may soften the impact.

### Closing Chunk Rules (MANDATORY â€” 13 Feb 2026)

**Tail fade:** Apply 150ms fade-out to the final chunk WAV before assembly. This is standard for all sessions â€” Fish truncates final generations regardless of text, and the tail fade smooths any abrupt ending.

**Soft ending words:** Closing lines must end on soft, multi-syllable words. Avoid hard consonants as the final word (e.g. "Five" â†’ "tomorrow", "this." â†’ "yourself."). Hard final consonants cause systematic Fish truncation â€” all candidates for a hard-ending chunk will clip identically.

**Evidence:** Session 41 c22: 4 different versions of "See you tomorrow for Day Five." ALL had cutoff. Script rewrite to "We continue tomorrow." + 150ms tail fade resolved it. Session 01 chunk 0: all 41 candidates with "...time for this." had -1ms tail. Changed to "...time for yourself." â€” all new candidates clean (13-29ms tails).

**Known limitation:** The Bible's 3-layer tail detection (`tail_silence_ms`, compound cutoff) does NOT catch Fish closing-chunk truncation. All candidates can measure >12ms trailing silence yet human hears cutoff. Document as known gap â€” human review of closing chunks remains mandatory.

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
| sleep (guided) | 10s | 30s | 60s |
| mindfulness | 8s | 25s | 50s |
| stress | 6s | 20s | 40s |
| default | 8s | 25s | 50s |

**Sleep stories do not use ellipsis pause profiles.** Stories use only authored `[SILENCE: X]` pauses at exact durations for narrative beats and scene transitions. The ellipsis profiles above (10s/30s/60s) are for guided sleep meditations with silent practice periods â€” not for narrative storytelling. Story scripts must specify every pause explicitly as `[SILENCE: X]` with the appropriate duration for the narrative moment.

### Script Rules

| Rule | Why |
|------|-----|
| All blocks **50â€“400 characters** | Under 50 causes hiss; over 400 causes monotone |
| Combine short phrases with lead-in text | "May I be safe." (14 chars) â†’ "Silently now, may I be safe." (28 chars) â€” still needs combining further to reach 50 |
| Use `...` for pauses (not `â€”`) | Script parser reads `...` as pause markers |
| No ellipsis in spoken text | Fish renders `...` as nervous/hesitant delivery |
| Scripts must contain ZERO parenthetical tags | In-text emotion tags don't work (see Section 18) |
| Estimate ~7.2 chars/second for narration duration | Calibrated from Fish/Marco output. **Caveat (9 Feb 2026):** This estimate tends to overestimate session duration â€” session 32 was scripted for 12 min but TTS produced 9.5 min. The build script's own duration estimate (calculated from actual chunk generation) is more reliable than the character-based formula. Use 7.2 chars/sec for rough planning only; set the `Duration-Target` header based on the build script's estimate after a dry run, not on character count alone. |

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


#### Script Writing for Fish â€” Structural Guidelines (10 Feb 2026)

These guidelines address the structural performance patterns discovered during the Court of Your Mind vault pick (session 52, 66 chunks). Trigger words cause specific artefacts on specific words. These guidelines address the deeper problem: entire chunks that fail repeatedly because of how the text is structured, not which words it contains.

**Character ceiling:** Keep sentences under 200 characters. The Court of Your Mind data shows chunks above 250 characters consistently generate the highest rejection rates (chunks 38 and 41 at 9 rejections each). Fish loses coherence over long syntactic spans.

**Emotional weight through pacing, not vocabulary:** Where a script needs emotional weight, achieve it through pause placement and sentence rhythm â€” let the silence do the heavy lifting, not the words. Dramatic vocabulary ("prosecution returns", "land in your chest", "you become the judge") conflicts with Fish's calm delivery model. Fish cannot modulate emotional intensity without distorting. Write the emotion into the structure, not the diction.

**Break long narrative into independent clauses:** Long flowing passages should be chunked into shorter independent clauses that can each stand alone syntactically. A chunk containing one clear thought generates cleaner than a chunk containing a complex multi-clause argument.

**Do not stack short punchy phrases:** Avoid putting multiple short declarative sentences back-to-back in a single chunk ("Hold that memory. That is evidence." or "Strong words. Certain words."). Fish cannot hold varied cadence across rapid phrase changes â€” it either goes flat or breathy. Spread punchy phrases across chunks with breathing room between them.

**Closing sections â€” simpler and shorter than the body:** This is the opposite of how you would naturally write a climactic ending. Fish's quality degrades towards the end of long sessions (chunk 62: 17 rejections). For closing passages, keep the language simpler, sentences shorter, and emotional register lower than the body. Let the content carry the weight, not the performance.

**The upstream principle:** These guidelines exist because Fish's limitations are structural, not random. A chunk that fails 17 times will fail 17 more times if the text stays the same. The fix is in the script, not the pipeline. When writing new scripts or revising existing ones, shape the input to give Fish the best chance rather than fighting it at the generation stage.

### Fish Audio Trigger Words

Certain words cause consistent artifacts in Fish/Marco output. Most are sibilant-heavy words or sustained vowels â€” exactly where Fish struggles to hold a clean, gentle tone. These appear constantly in meditation scripts, making this a high-impact issue.

**Known trigger words (calibrated from Session 36 human review 8 Feb 2026, Session 01 hiss investigation 11 Feb 2026, V8 auto-picker sessions 13 Feb 2026):**

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
| pulse | echo | rhythm, beat, gentle throb |
| soften | echo/hiss | relax, loosen, release |
| family | hiss | loved ones, those close to you |
| joyful | hiss | happy, glad, filled with joy |
| close (verb) | hiss | fall shut, rest closed, finish |
| soft lift | hiss | quiet rise, gentle shift, subtle movement |
| be (standalone) | voice shift | Embed in longer phrases â€” never isolate |
| breath in | hiss | breathe in, inhale, draw a breath |
| filling your lungs completely | hiss | Rewrite as shorter phrase â€” "breathe in fully" |
| nowhere else | voice shift | "right here", "all you need is to be here" |
| nostrils | hiss | nose, the tip of your nose, each breath |
| gentle rise | hiss | soft movement, quiet lift, subtle shift |
| entering | hiss | flowing into, moving through, arriving in |

**Pattern:** Most triggers are soft, sibilant-heavy words or words with sustained vowels where Fish needs to hold a gentle, open tone. These are the exact words that appear constantly in meditation content.

**"Soft" root pattern (13 Feb 2026):** The sibilant "s" + sustained "f" + "t" combination is systematically problematic for Fish/Marco. Words containing the "soft" root (soften, softly, soft lift) should be treated as high-risk. Evidence: c06 (soften) and c11 (soft lift) in session 01 failed across multiple versions.

**Machine-readable trigger word list:** `content/trigger-words.json` (17 trigger words + 1 regex pattern). Used by `tools/trigger-word-scan.py` and integrated into auto-picker pre-flight scan. Each entry has: word/pattern, defect type, evidence session, and suggested alternatives.

**Workarounds:**
- Use synonyms from the table above
- Break the word into a longer phrase where it's less exposed (e.g. "deeply" alone is worse than "more deeply now")
- If a trigger word is essential to the meaning and has no good synonym, ensure it falls within a block of 100+ characters so the TTS has surrounding context to stabilise

**Pre-flight scan:** The build script includes an automated pre-flight check that scans all script blocks against this list before any TTS calls. Blocks containing trigger words are flagged with suggested alternatives. This runs during dry-run and at the start of a live build. It is a WARNING, not a build-blocker â€” some trigger words may be unavoidable, but the scriptwriter should make a conscious choice rather than discovering the problem at the listening stage.

**Standalone trigger word scanner:**
```bash
# Scan a single script
python3 tools/trigger-word-scan.py content/scripts/01-morning-meditation.txt

# Scan all scripts
python3 tools/trigger-word-scan.py --all

# Output: line numbers, matched words, suggested rewrites
```

Reads from `content/trigger-words.json`. Each entry has: word/pattern, defect type, evidence session, and suggested alternatives.

**FUZZ vs HISS distinction (13 Feb 2026):**
- **HISS** = sustained high-frequency sibilance (narrowband, TTS generation artefact)
- **FUZZ** = background noise when speech gate opens (broadband, noise-floor)

Review pages now have both verdict buttons. Verdict tracking should differentiate between the two â€” they have different root causes and different mitigation strategies.

**Maintaining the list:** New trigger words discovered during human review are added to this table with their defect type and suggested alternatives. The pre-flight scan reads from this list. The list is expected to grow as more sessions are built and reviewed.

---

## 13A. Script Uniqueness & Cross-Session Differentiation

### The Problem

Salus sessions are starting to sound the same. A customer who listens to two or three sessions back-to-back should feel like they've had three distinct experiences â€” not the same session with different words in the middle. When openings blur together, when every session guides the breath the same way, when the same transitional phrases appear across the catalogue, the product feels mass-produced rather than crafted.

This is the single biggest threat to perceived quality that doesn't show up in any automated gate. A session can pass all 14 QA checks and still feel identical to the one before it.

**The rule is simple: no two Salus sessions should feel interchangeable.** Every session must have its own identity â€” its own way in, its own rhythm, its own voice, its own way of closing. A returning customer should be able to tell which session they're listening to within the first 30 seconds.

### Cross-Session Registers (Mandatory)

Three register files track what has already been used across the catalogue. These are the primary tool for preventing internal repetition. They live in `content/scripts/` and are checked before every new script enters the build pipeline.

#### `openings-register.txt`

Every deployed session's opening line and opening approach, one entry per line.

Format: `[Session #] | [Opening line] | [Opening technique]`

**Rule:** No new session may use the same opening technique as any existing session in the register. If three sessions already open with breath awareness, the next session must open differently â€” perhaps with a sound observation, a question, a brief story, a sensory detail, or silence.

#### `closings-register.txt`

Every deployed session's closing line and closing approach.

Format: `[Session #] | [Closing line] | [Closing technique]`

**Rule:** No new session may use the same closing technique as any session in the same category. Across categories, closings should still vary as much as possible. Sleep sessions all end with "Goodnight from Salus" (per existing rules), but the lead-in to that line must differ every time.

#### `phrases-register.txt`

Distinctive phrases, metaphors, breath cues, and transitional language used across all deployed sessions.

Format: `[Session #] | [Phrase or cue] | [Context]`

**Rule:** No phrase of 5+ words from this register may appear in a new script. If a phrase has been used, it's spent â€” find a new way to say it.

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
- Open mid-action â€” no settling, just start the practice
- Open with a single sensory detail (a sound, a temperature, a texture)
- Open with a brief, unexpected statement that sets the session's theme
- Open with silence â€” the 30-second ambient pre-roll (Section 11) lets the ambient carry the opening before the voice enters

**Mandatory:** Before writing any opening, check `openings-register.txt`. If the planned approach is already there, change it.

#### 2. Breath Cues

Every meditation involves breathing. The risk is that every session guides the breath using identical language.

**What tends to repeat:**
- "Breathe in... breathe out"
- "Notice your breath" / "Bring your attention to your breathing"
- "Take a deep breath in through your nose"
- "With each exhale, let go of..."

**Variation strategies:**
- Describe the breath indirectly â€” talk about what it does to the body rather than instructing the mechanism
- Vary the sensory focus: one session might notice temperature of air at the nostrils, another might notice the rise of the chest, another the sound of the exhale
- Some sessions can skip explicit breath guidance entirely and let the pacing of the script imply the rhythm
- Use different verbs: draw, gather, release, soften, empty â€” not always "breathe in/out"
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
- Skip the full body scan â€” focus on one or two areas with genuine depth
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
- End abruptly â€” some sessions can simply trail off into ambient, letting the listener decide when they're done
- End with a specific, practical suggestion: "The next time you're waiting in a queue, try this for thirty seconds"
- End with humour or lightness where the session type allows it

**Mandatory:** Before writing any closing, check `closings-register.txt`. If the planned approach is already there, change it.

#### 6. Structural Arc

Even if individual phrases differ, sessions can feel identical if they follow the same structural shape every time.

**The default arc (overused):**
Settle â†’ breathe â†’ body awareness â†’ core practice â†’ integration â†’ close

**Variation strategies:**
- Start in the core practice immediately â€” no preamble
- Move between activity and stillness rather than building linearly toward stillness
- Use a circular structure â€” return to the opening image or phrase at the end
- Use a single extended metaphor as the structural spine rather than a technique sequence
- Vary the ratio of guidance to silence â€” some sessions should be 70% guided, others 40%
- Place the most intense or meaningful moment somewhere unexpected â€” not always at the two-thirds mark

### Pre-Build Originality Scan (Automated)

The build script runs a cross-session originality scan during the pre-flight phase, alongside the existing trigger word check and block-size validation.

**The scan:**
1. Loads all three register files (`openings-register.txt`, `closings-register.txt`, `phrases-register.txt`)
2. Extracts all text blocks from the new script
3. Compares each block against register entries using fuzzy matching (threshold: 70% similarity on any phrase of 5+ words)
4. Flags matches with the specific session number and phrase that conflicts
5. Checks the opening line and closing line against their respective registers â€” exact or near-exact matches are flagged
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

This is lighter-touch than the internal register system â€” a due diligence step, not a gating mechanism.

### Exceptions

Some repetition across sessions is unavoidable and acceptable:

- **Traditional formulations** (e.g., metta phrases "May I be safe, may I be happy") â€” these are traditional, not anyone's property, and listeners expect consistency in how they're presented
- **Functional micro-instructions** (e.g., "breathe in," "close your eyes") â€” unavoidable, though the framing around them must vary
- **Category conventions** (e.g., sleep sessions ending with "Goodnight from Salus") â€” brand signatures, not repetition
- **Phrases listed in `Expected-Repetitions` metadata** â€” intentional structural repetition within a single session (handled by Gate 8)

The key distinction: **functional language can repeat; creative language must not.** "Breathe in" is functional. "Let your breath become a soft tide, washing through you" is creative â€” and once it's been used in one session, it's done.

### Narration Audit (Outstanding)

**Status:** PENDING â€” to be scheduled

A full audit of all deployed sessions is required to retroactively populate the three register files and identify existing cross-session repetition. This is a prerequisite for the register system to function properly.

**Scope:**
1. Retrieve or reconstruct scripts for all deployed sessions (01, 03, 05, 06, 07, 08, 09, 11, 18, 19, 23, 25, 29, 32, 36, 38, 43)
2. Extract opening lines, closing lines, and distinctive phrases from each
3. Populate `openings-register.txt`, `closings-register.txt`, and `phrases-register.txt`
4. Identify any existing cross-session repetition â€” document which sessions share phrasing and flag for future rewrites
5. Listen to a representative sample across categories back-to-back and note where sessions feel interchangeable
6. Produce an audit report with specific recommendations for which scripts need the most differentiation work

**Priority:** Must be completed before any new scripts are written. The registers are worthless if they don't include existing content.

---

## 14. Expression Through Punctuation

**Status:** ACTIVE â€” Technique proven, deployed in loving-kindness session.

### The Problem

TTS at temperature 0.3 is deliberately flat. Marco sounds the same whether saying "close your eyes" or "you are deeply loved." Increasing temperature adds instability and artefacts. Temperature is not the solution.

### The Solution: Script-Level Direction

Every comma, ellipsis, fragment, and sentence structure is vocal direction to Marco. The TTS model responds to punctuation cues â€” not perfectly, but enough to create natural rhythm and breathing. No API changes, no model tuning, no extra cost. Just better scripts.

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
> 76â€“84 characters per block. Ellipses create breathing rhythm without splitting into dangerously short chunks.

---

## 15. Auphonic Integration

**Status:** ACTIVE â€” Measurement gate ONLY. Do not use Auphonic output as production audio.

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
| Input SNR | â‰¥ 40 dB | < 40 dB |
| Background Level | â‰¤ âˆ’55 dB | > âˆ’55 dB |
| Hum detected | No | Yes (any segment) |
| Output loudness | âˆ’26 Â±1.0 LUFS | Outside range |
| Output true peak | â‰¤ âˆ’2.0 dBTP | > âˆ’2.0 dBTP |
| Output LRA | â‰¤ 16 LU | > 16 LU |
| Leveler gain spread | â‰¤ 10 dB | > 10 dB |

SNR threshold at 40 dB based on Fish baseline of 45.26 dB. The old 25 dB threshold was too permissive for TTS content.

### Per-Segment Analysis

**Status: NOT AVAILABLE.** The Auphonic API does not return per-segment SNR data â€” only aggregate file-level metrics. Per-segment analysis was planned but cannot be implemented as a pipeline gate due to this API limitation. If Auphonic exposes per-segment SNR in a future API version, this should be revisited.

Whole-file Auphonic metrics remain in use as a secondary measurement gate alongside the 14-gate pipeline system.

### Auphonic Preset Settings

| Setting | Value |
|---------|-------|
| Adaptive Leveler | Enabled |
| Filtering | Enabled (Voice AutoEQ) |
| Loudness Target | âˆ’26 LUFS |
| Max Peak Level | âˆ’2 dBTP (ATSC A/85) |
| Noise Reduction | Static: remove constant noises only, 6 dB (low) |
| Remove Reverb | Off |
| Automatic Cutting | Off (preserve meditation silences) |
| Output Format | WAV 16-bit PCM, optimal stereo |

**Note:** The "silent segments >30s" warning is a FALSE POSITIVE for meditation content. Ignore it.

### First Baseline Results (7 February 2026)

File: `36-loving-kindness-intro_precleanup.wav`

| Metric | Value |
|--------|-------|
| Program Loudness | âˆ’16.34 LUFS |
| LRA | 15.21 LU |
| Max Peak Level | âˆ’4.39 dBTP |
| SNR mean | 45.26 dB |
| Background Level | âˆ’62.25 dB |
| Hum | Not detected |

**Key conclusion:** Fish Audio TTS output is broadcast quality (40â€“50 dB SNR standard). The aggressive cleanup chain was solving a problem that barely existed.

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

### Auphonic Echo Detection â€” RULED OUT (9 Feb 2026)

Auphonic was tested as an external echo detector against 55 labelled chunks (5 ECHO, 24 OK from sessions with human review). **AUC-ROC: 0.341** â€” worse than random. Anti-correlated with human echo perception.

| Metric | ECHO chunks | OK chunks | Interpretation |
|--------|------------|-----------|----------------|
| Signal level | âˆ’22.4 dB | âˆ’19.7 dB | Echo chunks are quieter |
| Loudness | âˆ’23.0 LUFS | âˆ’20.7 LUFS | Echo chunks are quieter |
| Noise floor | âˆ’65.7 dB | âˆ’60.4 dB | Echo chunks have less noise |
| SNR | 43.3 dB | 40.7 dB | Echo chunks have better SNR |

The pattern is the opposite of real acoustic reverb. Fish's "echo" is a generative distortion â€” the TTS model smears or hallucinates certain phonemes, producing lower-energy, smoother output that sounds like echo to human ears but has no physical delay signature. Auphonic sees it as a quieter, cleaner signal.

Adding Auphonic features to local DSP features made the combined detector worse (AUC 0.527 vs 0.568 local-only). **Do not use Auphonic for echo detection.**

---

## 15A. Production Readiness

**Status:** READY FOR SCALE â€” 9 February 2026

The audio production pipeline is now mature enough for mass production of meditation sessions. The combination of automated QA, proven repair processes, and documented Fish Audio failure modes means sessions can be produced at volume with reliable quality.

### What Makes This Possible

**Automated quality scoring** (8 Feb 2026): Per-chunk composite scoring identifies defects programmatically. The scoring system catches hiss, voice shift, and tonal inconsistency for mid-session chunks. **It does not detect echo** â€” see Section 16B. Human listening remains the only reliable echo gate.

**Proven repair pipeline** (9 Feb 2026): Defective chunks can be fixed through targeted best-of-10 regeneration and splice repair without rebuilding entire sessions. Repair process validated on sessions 32 and 19.

**Documented failure modes:** Fish Audio's behaviour under production conditions is now characterised:
- Trigger words that cause echo/hiss (Section 13)
- Chunk 0 cold-start degradation and the split-chunk fix (Section 9)
- Gate 7 non-deterministic volume variation (Section 12)
- Scoring formula bias on unconditioned chunks (Section 9)
- 30% hit rate on certain phonetic patterns

**Script rules that prevent defects:** Opening chunk length limit, 50â€“400 character blocks, trigger word pre-flight, cross-session originality scan. Scripts designed around Fish's known weaknesses produce cleaner first-generation audio.

### Production Workflow

1. **Script** â€” Write following all rules (Section 13, 13A). Short opening chunk. Trigger word scan. Originality check.
2. **Build** â€” `build-session-v3.py --no-deploy`. Best-of-5 per chunk. 14 gates.
3. **Score** â€” Per-chunk composite scoring identifies any flagged chunks.
4. **Repair** â€” Flagged chunks get best-of-10 targeted regeneration (Section 16A). Opening chunks assessed by human ear, not score.
5. **Review** â€” Human listening on headphones at high volume. Focus on flagged chunks and opening/closing.
6. **Deploy** â€” Upload to R2, wire into HTML, update registers, push, email.

Sessions 18 and 23 passed first build with zero repairs needed. Realistic expectation: most sessions will need 1â€“3 chunk repairs, taking the total production time from script to live to approximately 30â€“60 minutes per session once the script is written.

### Competitive Position

No competitor in the meditation app space has solved AI voice reliability at this level. Calm and Headspace use human narrators. Smaller apps using AI voice ship the exact defects this pipeline catches and fixes. The Salus pipeline produces AI-narrated content at a quality level that withstands headphone listening at high volume â€” with a documented, repeatable process. This knowledge compounds with every session built and is not publicly documented anywhere.

---

## 16. Build Execution

### CLI Usage

```bash
# Full pipeline: build â†’ QA â†’ deploy to R2
python3 build-session-v3.py 25-introduction-to-mindfulness

# Dry run (no API calls)
python3 build-session-v3.py 25-introduction-to-mindfulness --dry-run

# Build + QA but don't deploy
python3 build-session-v3.py 25-introduction-to-mindfulness --no-deploy

# Resemble provider
python3 build-session-v3.py SESSION --provider resemble

# Raw output (no cleanup) for quality testing
python3 build-session-v3.py SESSION --no-cleanup
```

### Pre-Build Checklist

**Script:**
- [ ] Script written with correct metadata header and pause markers
- [ ] All text blocks 50â€“400 characters (MINIMUM 50, not 20)
- [ ] Short phrases combined to exceed 50 chars
- [ ] Pauses humanised (no identical gap durations)
- [ ] Zero parenthetical emotion tags in text
- [ ] `Expected-Repetitions` set if session has intentional structural repetition
- [ ] **Opening chunk is one short sentence, under ~60 characters** (mandatory â€” Section 13)
- [ ] **Trigger word pre-flight passed** â€” script scanned against known trigger word list (Section 13). Any flagged words either replaced with synonyms or consciously accepted
- [ ] **Cross-session originality scan passed** â€” script checked against registers (Section 13A). No unresolved conflicts with existing openings, closings, or phrases
- [ ] **Duration-Target cross-referenced** â€” if rebuilding, header set against previous build's actual duration. If new, header set from dry-run output.

**Environment:**
- [ ] Only building ONE session (no parallel builds)
- [ ] Provider set to `fish` (default) or `resemble` as appropriate
- [ ] `FISH_API_KEY` set in `.env`
- [ ] `RESEND_API_KEY` set in `.env`
- [ ] `AUPHONIC_USERNAME` / `AUPHONIC_PASSWORD` set in `.env`
- [ ] Master reference WAV exists at `content/audio/marco-master/marco-master-v1.wav`

**Build:**
- [ ] Dry run completed â€” block count and silence totals verified
- [ ] Ambient file duration exceeds estimated voice duration
- [ ] If no long ambient exists, download one BEFORE building

**Quality:**
- [ ] All 14 QA gates run
- [ ] 0 voice changes in QA results


**Vault Workflow (additional checks):**
- [ ] **Script passes structural guidelines** â€” no sentences over 200 characters, emotional weight through pacing not vocabulary, no stacked short punchy phrases, closing sections simpler than body (Section 13, Script Writing for Fish)
- [ ] **Vault candidates generated** â€” minimum 20 per chunk (more for difficult chunks identified by structural guidelines)
- [ ] **A/B tournament completed** â€” all chunks picked, picks.json exported
- [ ] **vault-assemble.py run** â€” picked WAVs assembled with edge fades, silence, loudnorm
- [ ] **Post-assembly gates passed** â€” Gates 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13 on assembled output

**Human Review (mandatory before deploy):**
1. Start `label-server.py` (labels auto-save to `reference/human-labels/` â€” no manual exports)
2. Extract individual chunks from raw narration WAV using manifest timing data
3. Upload chunks to R2 at `test/chunk-test-{version}/` (e.g. `chunk-test-v3b/`)
4. Run `score-chunks-whisper.py` on extracted chunks to generate Whisper confidence scores
5. Create or update interactive HTML review page with Whisper confidence badges and auto-save
6. Scott listens to every chunk on AirPods at high volume (exposes artifacts normal listening misses)
7. Chunks flagged by Whisper (bottom 30% by `word_prob_p10`) are highlighted with a blue border â€” visual cue only, not a gate
8. Each chunk rated: OK / ECHO / HISS / VOICE / BAD
9. Labels auto-save to `reference/human-labels/` via label server (verify CSVs exist after review)
10. If clean rate is acceptable â†’ proceed to deploy
11. If problem chunks identified â†’ use `--focus-chunks` for targeted rebuild (problem chunks get best-of-10, others best-of-5)
12. Re-review focused chunks. Repeat if needed, but perfection should not prevent shipping.


**Human Review under vault workflow:**

The A/B tournament picker replaces the old post-build chunk review workflow. Under the vault workflow, human review happens TWICE:

1. **During picking** (the A/B tournament) â€” every chunk heard, compared, and selected. This is the primary quality gate.
2. **After assembly** â€” the complete assembled session listened through end-to-end to catch assembly-level issues (stitch artefacts, pacing problems, loudness jumps between chunks). This is a final sanity check, not a per-chunk review.

The old workflow (build â†’ extract chunks â†’ upload to R2 â†’ generate review page â†’ rate each chunk) is superseded for vault-built sessions. The chunk-level review happened during picking.

**Review scope rule (legacy single-build sessions):** Scott listens to ALL chunks. Full-chunk human review is mandatory until the echo detector (Section 16B) achieves a validated false negative rate below 10% on cross-validated data across at least 5 sessions and 200+ labelled chunks. No automated system currently detects Fish echo reliably. Do not reduce review scope based on automated scores.

**Chunk review batching:** Scott feeds labelled data into the echo detection system through focused testing sessions (~1 hour) when in the mood. The pipeline must always have chunks extracted, uploaded to R2, and review pages generated so these sessions are not wasted waiting for data preparation. Every reviewed session grows the training dataset for the echo detector.

**Deployment:**
- [ ] Final audio remixed with ambient at per-session level (set by ear â€” see Ambient Rules in Section 11). Dynamic masking applied to problem chunks if needed.
- [ ] Final MP3 uploaded to Cloudflare R2 (NOT committed to git)
- [ ] Audio plays from `media.salus-mind.com` URL (test on both desktop AND mobile)
- [ ] CORS verified: `Access-Control-Allow-Origin` header present in response
- [ ] Website HTML updated â€” ALL pages referencing the session (listing pages, detail pages, mindfulness cards)
- [ ] Players wired up with `data-src` attribute pointing to correct R2 URL
- [ ] HTML changes committed and pushed to main
- [ ] Email sent to scottripley@icloud.com
- [ ] `openings-register.txt` updated with new session's opening line and technique
- [ ] `closings-register.txt` updated with new session's closing line and technique
- [ ] `phrases-register.txt` updated with new session's distinctive phrases, metaphors, and cues

### Definition of "Live" (14 Feb 2026)

A session is NOT "live" just because its MP3 exists on R2. **A session is live when ALL of the following are true:**

1. MP3 deployed to R2 and returns HTTP 200 from the CDN
2. A `data-src` reference exists in the relevant HTML page(s) pointing to the correct R2 URL
3. The player element is wired up (correct class: `custom-player` or `m-player`)

Deploying to R2 alone makes a session "available" â€” not "live in the audit." ~40 sessions currently have scripts and/or vault audio on R2 but have no HTML wiring (sessions 88â€“90 and others). These are NOT live. Sessions without vaults (script-only, no audio generated) are NOT live regardless of HTML status.

**Implication for session counts:** Any audit, catalogue count, or status report must distinguish between "on R2" and "live on site." The deployed sessions table below tracks R2 status. HTML wiring status should be verified separately against the actual site pages.

### Email Notification System

| | |
|---|---|
| **Service** | Resend API (free tier, 100 emails/day) |
| **Env var** | `RESEND_API_KEY` in `.env` |
| **Sender** | `onboarding@resend.dev` (switch to `build@salus-mind.com` after domain verification) |
| **Recipient** | `scottripley@icloud.com` |
| **Header** | Uses `curl` subprocess (Python `urllib` blocked by Cloudflare bot protection) |
| **Trigger** | Every completed build â€” pass or fail |

### Deployed Sessions

| Session | Duration | Provider | Ambient | Status |
|---------|----------|----------|---------|--------|
| 01-morning-meditation | 14.1 min | Fish | Grace (âˆ’14 dB), 30s/60s | **Rebuilt 13 Feb** â€” opening rewritten ("Good morning. You made time for yourself."), 30s structural pre-roll, numpy mix. 26 chunks, v141 picked (EXCELLENT). c09 rechunked (v0â†’v15), c19 rechunked (v47â†’v19). MD5: 82df9eb3b838b7e6344d659757580dba. |
| 03-breathing-for-anxiety | 18 min | Fish | Birds (âˆ’14 dB), 30s/60s | **Full rebuild 13 Feb** via auto-picker v8. 49 chunks, 2,974 candidates, 5 rechunk rounds, 47/49 clean (95.9%). 2 stubborn: c09 (CUTOFF, pool exhausted), c14 (ECHO/VOICE, contaminated). MD5: 94b354da7f3acb344e1376d8c692ff7a. |
| 09-rainfall-sleep-journey | 26.2 min | Fish | Rain (âˆ’19 dB), 30s/60s (voice-first loudnorm) | **L-38 remix 13 Feb.** MD5: 7b2e02d33d1c6ff3e533deab93a752c2. |
| 18-calm-in-three-minutes | 3.2 min | Fish | rain | Deployed (build 1, 14/14 gates, 9 Feb, commit 752752f) |
| 19-release-and-restore | 14.5 min | Fish | garden | Deployed (build 4, 14/14 gates, 9 Feb, commit 752752f). Builds 1â€“3 failed Gate 7 (surge). Script rewritten (trigger-word clean, progressive muscle relaxation). **Repair (9 Feb):** Chunk 0 echo â€” 30 generations across 3 approaches all flagged by scorer, but split-chunk version confirmed clean by human listening. Scoring formula bias on unconditioned chunks proven. Wrong ambient noted (script=garden, build=rain). Chunk 0 split + remixed with correct ambient, deployed. |
| 23-the-calm-reset | 5.5 min | Fish | stream | Deployed (build 1, 14/14 gates, 9 Feb, commit 752752f). Script rewritten (trigger-word clean). |
| 25-introduction-to-mindfulness | 14.4 min | Fish | garden, âˆ’ss 10 offset | Deployed (rebuild 8 Feb, LALAL-cleaned â€” voice degraded, trigger word fix "nowhere else", commit acb5842). LALAL removed from pipeline (all modes tested and failed â€” see v3.4). 4 flagged chunks including opening (worst hiss at âˆ’7.26 dB) â€” repair or rebuild decision pending (Ledger L-05). |
| 32-observing-emotions | 9.5 min | Fish | garden | Deployed (build 3, 14/14 gates, 9 Feb, commit 752752f). **Repair (9 Feb):** Chunk 1 echo on "something" eliminated via best-of-10 regen. Promoted to live after human A/B review. |
| 36-loving-kindness-intro-v3 | 10.5 min | Fish | birds, âˆ’42dB (14dB below voice) | Deployed (v3b focused rebuild, best-of-10, 14/14 gates, 65% clean rate) |
| 38-seven-day-mindfulness-day1 | 8 min | Fish | Grace (âˆ’16 dB) | Human tournament picks. Assembled, deployed 13 Feb. **Needs ambient remix to 30s/60s pre-roll.** |
| 39-seven-day-mindfulness-day2 | 9 min | Fish | Grace (âˆ’16 dB) | Auto-picked from prior trial. Assembled, deployed 13 Feb. |
| 40-seven-day-mindfulness-day3 | 10 min | Fish | Grace (âˆ’16 dB) | Auto v8 fresh build. R1: 24/29 (82.8%). Deployed R1 as production-passable. |
| 41-seven-day-mindfulness-day4 | 11 min | Fish | Grace (âˆ’16 dB), 30s/60s | Auto v8 fresh + trigger scan. R1: 20/23 (87%). 5 rounds (c22 stubborn â€” script rewrite + 150ms tail fade). 23/23 PASS. |
| 42-seven-day-mindfulness-day5 | ~12 min | Fish | Grace | Vault-assembled 12 Feb. |
| 52-the-court-of-your-mind | ~20 min | Fish | TBD | Auto v8: 66/66 picked, 100% pass, 0 flagged. **Awaiting assembly + deploy.** |
| 53-the-gardeners-almanac | 30.6 min | Fish | Garden (âˆ’19 dB), 30s/60s (voice-first loudnorm, skip 10s dead start) | **L-38 remix 13 Feb.** MD5: b858fb4c58b76b9d9361f60fe880fa56. |
| 61-21day-mindfulness-day5 | ~9 min | Fish | Stream (âˆ’8.4 dB) | Vault-assembled 12 Feb. |
| 76-21day-mindfulness-day20 | ~15 min | Fish | Birds (âˆ’2.3 dB) | Vault-assembled 12 Feb. Gate overrides: Gate 7 + Gate 12 (expected false positives for "long sit" format). |
| narrator-welcome | 1.3 min | Fish | Grace (âˆ’10 dB, 5s in, 10s out â€” non-standard, clip too short for 30/60) | Rescripted 12 Feb from 5â†’6 chunks (added "In a world built for speed" line). Auto-picked with pick locking (c0 locked to v78). c0 conditioned via mid-sentence technique (session 42 c04_v19.wav). |

### Deployment Milestones (14 Feb 2026)

**Batch Remix:** 53/53 deployed sessions remixed with correct catalogue-assigned ambients + 30s pre-roll, uploaded to R2, CDN caches purged. First time every deployed session has the right ambient from a single source of truth (`session-registry.json`) rather than ad-hoc per-session mixing.

**Audio Wiring Audit:** 19 sessions found disconnected — audio present on R2 but not reachable from the site. Four failure categories: (A) wrong R2 paths (3 sessions + media.html), (B) wrong filename (1 mismatch), (C) "audio coming soon" placeholders (3 sleep stories), (D) completely missing from all pages (12 sessions). Commit: `16e4086`. Lesson: every deploy needs a corresponding HTML wiring step.

**Course Player Wiring:** 7-day course days 2, 3, 4, 6, 7 and 21-day course days 1–19, 21 had missing or wrong `src` URLs. All wired. Commit: `c401a5f`.

**Targeted Repairs:** S60 (voice breakout at 0:56, pick swap to v17 — PASS), S62 (voice breakout at 3:36, pick swap to v18 — PASS), S01 (missing silence in chunk 7, script lines merged across pauses — AWAITING REVIEW).

**Session Count:** 55 total catalogued in `session-registry.json`: 52 deployed (audio on R2, all wired to HTML after audit), 3 script-only (88, 89, 90).

---

## 16A. Chunk Repair Pipeline

**Status:** APPROVED â€” production use authorised 9 February 2026. Trial on session 32 chunk 1 confirmed perceptual improvement (echo on "something" eliminated). Repaired file promoted to live. Code is authorised to run targeted best-of-10 repairs on all flagged chunks in the repair backlog without further approval.

### Why This Didn't Exist Earlier

The per-chunk composite scoring system was only added on 8 February 2026. Before that, there was no programmatic way to identify which specific chunks were defective â€” it was all human listening. The scoring system created the data, the repair trial (9 Feb) proved the fix works, and now Code can run repairs autonomously. The full loop â€” score â†’ identify â†’ regenerate â†’ splice â†’ verify â†’ deploy â€” is a capability that became possible less than 48 hours before it was proven. From v3.4 onwards, this loop runs on every future production and retrospectively across the deployed catalogue.

### When to Use

Chunk repair is for fixing a specific defective chunk in an already-deployed session without rebuilding the entire session. It is a targeted intervention, not a substitute for full rebuilds.

**Use when:**
- A deployed session has a localised defect (echo, hiss, voice shift) in one or two chunks
- The rest of the session is clean and does not need regenerating
- A full rebuild would risk introducing new defects in currently-clean chunks

**Do not use when:**
- Multiple chunks across the session are flagged (>3 â€” full rebuild is more efficient)
- The defect is in the ambient mix rather than the narration
- The session has never passed human review


**Hard failure rule:** If a chunk fails 10 consecutive regenerations without improvement in composite score, stop. Do not continue retrying. The chunk is a Fish hard failure (e.g., Session 36 chunk 7 â€” 0/10 improved). Options: accept if not audibly jarring in context, mask with ambient level adjustment, or flag for script revision and regeneration.
### Process

1. **Identify the defect.** Per-chunk QA scoring flags chunks below 0.50 composite score. Human listening confirms the specific defect (echo, hiss, voice shift) and its location.

2. **Extract the target chunk** from the master narration WAV using the build manifest's timing data.

3. **Best-of-10 regeneration.** Generate 10 replacement versions of the chunk via Fish Audio. Score all 10 using the composite metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance to neighbours). Select the highest-scoring version.

4. **Splice into a copy of the master narration.** Use 100ms cosine crossfade at the splice boundary. Target speechâ†’silence boundaries for the splice point where possible â€” silence absorbs any residual discontinuity.

5. **Run all 14 QA gates** on the repaired narration.

6. **Apply ambient** at the same level as the deployed version. Encode to 128kbps MP3.

7. **Upload to R2 as a repair candidate** (e.g. `32-observing-emotions-repair-1.mp3`). Do NOT replace the live file.

8. **Human A/B comparison.** Scott listens to both original and repaired files on headphones at high volume. Only promote to live after human sign-off.

### Splice Rules

- 100ms cosine crossfade â€” no hard cuts
- Target speechâ†’silence boundaries (tonal distance is lowest here)
- Measure tonal distance at the splice point â€” must be <0.50 (threshold from bible)
- Document splice assessment in the repair report: crossfade duration, boundary type, tonal distance, silence absorption

### Trial Results (9 February 2026)

**Session 32, Chunk 1** â€” echo on "something"

| Metric | Original | Repair (v4) | Change |
|--------|----------|-------------|--------|
| Combined score | 0.417 | 0.467 | +0.050 |
| Quality score | 0.426 | 0.490 | +0.064 |
| Echo risk | 0.00147 | 0.00125 | âˆ’15% |
| Tonal distance | 0.000192 | 0.000452 | +0.00026 |
| 14-Gate QA | 14/14 | 14/14 | â€” |

Voice MFCC=0.039, F0 dev=2.6% | 0 clicks, 0 spikes, 0 surges

**Best-of-10 generation results:** 3 of 10 versions scored higher than the original. 7 scored below 0.364. The selected version (v4) had the best combined score + tonal distance balance. v2 had better raw quality (0.522) but worse tonal match (0.0014 vs 0.0005) â€” tonal match was prioritised for splice quality.

**Splice assessment:** 100ms cosine crossfade at speechâ†’silence boundary. Tonal distance 0.000443 (0.09% of threshold). +1.33s absorbed by silence region. Very likely inaudible.

**Honest assessment:** Echo risk reduced 15% but replacement still below 0.50 flag threshold. None of 10 Fish generations reached "clean." The repair is measurably better but human listening is required to confirm perceptual improvement. The word "something" may be a phonetic pattern that Fish consistently struggles with â€” a 30% improvement rate (3/10) is notably low.

### Repair Backlog

Chunks flagged across deployed sessions (composite score <0.50), ranked by severity. Session 32 chunk 1 is the completed trial. All others are candidates if the repair process is approved after human A/B review.

| Session | Chunk | Score | Hiss (dB) | Text | Priority |
|---------|-------|-------|-----------|------|----------|
| 19 | 51 | 0.209 | âˆ’9.43 | "This has been Salus. Go gentlyâ€¦" | Closing chunk â€” high exposure |
| 25 | 12 | 0.232 | âˆ’8.35 | "You don't need to stop your thoughtsâ€¦" | Mid-session |
| 32 | 12 | 0.325 | âˆ’10.19 | "Stay with that sensationâ€¦" | Mid-session |
| 19 | 31 | 0.348 | âˆ’13.47 | "Your neck. Gently press your head backâ€¦" | Mid-session |
| 25 | 3 | 0.349 | âˆ’10.26 | "Find somewhere comfortable to sit or lie downâ€¦" | Early chunk |
| 25 | 1 | 0.365 | âˆ’7.26 | "This is a simple introduction to mindfulnessâ€¦" | Opening chunk â€” worst hiss, highest exposure |
| 36 | 7 | 0.378 | âˆ’10.04 | "There is nothing to force hereâ€¦" | Early chunk |
| 23 | 13 | 0.426 | âˆ’10.67 | "Now imagine all the stress you have accumulatedâ€¦" | Mid-session |
| 25 | 5 | 0.430 | âˆ’8.54 | "Let's start with your breathâ€¦" | Early chunk |
| **32** | **1** | **0.449** | **âˆ’10.51** | **"Today we are going to practise somethingâ€¦"** | **REPAIRED â€” LIVE** |

Sessions 01, 03, 09, 38 have no per-chunk QA data (pre-scoring system). Session 18 passed clean (0/12 flagged).

**Session 25 note:** 4 flagged chunks including the opening (worst hiss reading across all sessions at âˆ’7.26 dB). Full rebuild may be more appropriate than individual chunk repairs for this session.

### Hiss Mitigation

The repair trial included a hiss reduction test (Phase 4). Results:

**LALAL.AI (dereverb=OFF, dehiss only):** INEFFECTIVE. Uniform 3 dB attenuation across all frequencies. SNR unchanged at 21.8 dB. Not selective denoising â€” equivalent to turning the volume down. **LALAL cannot selectively remove hiss from Fish TTS output.**

**Auphonic:** SKIPPED â€” no credentials in `.env` at time of trial.

**Conclusion:** Chunk selection (best-of-N scoring) + ambient masking remain the only viable hiss mitigation strategies. No external post-processing service has proven capable of selectively removing Fish-generated hiss without damaging vocal quality. The pipeline's hiss defence is: (1) avoid trigger words that cause hiss, (2) score chunks and keep the cleanest, (3) mask residual hiss with ambient.

---

## 16B. Echo Detection

**Status:** WORKING — Gate 16 achieves AUC 0.793 (up from 0.34–0.51). Catches 69–80% of echo, more sensitive than casual human listening for subtle contamination. Type B "quiet echo" (29% FNR) remains undetected. Human review remains the final authority.

### The Echo Fingerprint (14 Feb 2026)

Echo in Fish TTS has a measurable spectral signature. The signal is in **mel band statistics** and **cross-band correlation** — NOT in autocorrelation, phase coherence, cepstral analysis, or modulation spectrum (which the old approaches relied on). Echo smears spectral energy downward (sub-bass flattens, low-mid gets louder relative to upper-mid) and disrupts the normal coherent movement between frequency bands. It is a tonal compression effect, not a physical reverb — consistent with the finding that this is generative distortion, not acoustic echo.

### What Was Tested (Comprehensive — 697 Features)

80-band mel spectrogram stats (320 features), per-band spectral flux (240 features), cross-band correlation, phase coherence, autocorrelation at 5 lag ranges, cepstral analysis at 4 quefrency ranges, modulation spectrum at 5 frequency bands, post-onset spectral decay, sub-band energy ratios, spectral shape metrics, RMS envelope, pitch stability. 48 features significant at p < 0.05.

**What did NOT work (weak discrimination, |d| < 0.5):** Autocorrelation (all lag ranges), cepstral analysis, absolute phase coherence, modulation spectrum, spectral decay after transients, spectral flux. The old `echo_risk` (spectral flux variance) targets these weak families — explaining its ~58% FNR.

### Classifier Progression

| Approach | AUC | FNR | FPR |
|----------|-----|-----|-----|
| Composite scorer (v6, pre-Gate 16) | ~0.5 | 58% | ? |
| echo-detector.py (RF, 65 features) | 0.512 | 67% | 28% |
| Auphonic analysis | 0.341 | n/a | n/a |
| **Gate 16 (11 features, CV)** | **0.793** | **31%** | **18%** |

### Operating Philosophy — "Replace Until Pass"

FPR does not matter for production use. The workflow: Gate 16 scores all candidates → auto-picker penalises high-scoring candidates → if picked chunk still scores high, regenerate and re-pick → repeat until pass. Regenerating chunks is cheap (seconds, pennies). Shipping echo is expensive (ruins listener experience, erodes trust). Optimise for RECALL, accept false positive waste.

### Current Integration

Gate 16 z-score composite replaces the old `echo_risk` (spectral flux variance) in the auto-picker. Whisper confidence remains as a visual cue in review pages (not a gate, not pass/fail).

### Next Defects Roadmap

Echo is the first defect tackled with granular mel analysis. Next in priority order, using the same z-score framework + labelled data:

1. **VOICE BREAKOUT (Gate 17)** — VALIDATED. Full catalogue scan complete. 237 confirmed breakouts across 51/53 sessions. See Section 12 Gate 17 and Section 16F.
2. **REPEAT DEFECT (future Gate 18)** — Fish generating words/phrases twice. Spectral features won't catch these. Likely needs Whisper transcription comparison against input text.
3. **HISS** — high-frequency noise contamination.
4. **AUDIO FUZZ** — broadband distortion/crackle.

### What Must NOT Happen

- Do not claim Gate 16 catches all echo. Type B quiet echo (29% FNR) is invisible to Gate 16. Human review remains the final authority.
- Gate 16 reduces but does not eliminate the need for human echo review. Use it to prioritise which chunks to listen to most carefully, not to skip listening.
- Do not retrain or update the echo detector without approval. Each retraining is a threshold change.
- Do not add echo detection as a formal binary pass/fail gate until false negative rate is validated below 10% across 200+ labelled chunks.

---

## 16C. Marco Voice Vault

**Status update (12 Feb 2026):** The A/B tournament picker remains the fallback human review interface but is no longer the primary candidate selection method. The auto-picker (Section 16E) now handles initial candidate selection. Human review shifts from per-chunk A/B comparison (~2 hrs/session) to full-audio review of auto-picked assembly (~45 min/session including regen rounds). The picker's rejection reason tags (Echo, Hiss, Cut Short, Voice) continue to accumulate training data during any manual review sessions.

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

**Implementation:** `tools/vault-picker/ab_picker_js.js` â€” `tagCheckboxes()` renders, `collectInlineTags()` harvests. All 54 pickers rebuilt and uploaded to R2.

### Solo Mode Fix (12 Feb 2026)

When A/B tournament reaches last remaining candidate, picker now shows "solo mode" (red border) for explicit accept/reject instead of auto-winning. Fixed `pickSide()` guard blocking solo mode buttons.



**Status:** VALIDATED â€” narrator welcome trial complete and deployed. Court of Your Mind (session 52) full-scale pick complete. Vault established as the standard production method for all Salus audio.

### Concept

The vault is a library of pre-generated, human-verified Marco phrase recordings. Instead of generating sessions end-to-end and hoping every chunk lands clean, the vault approach generates multiple candidate versions of each individual phrase, presents them for human selection, and assembles sessions from proven audio.

**The vault is now the standard production method for all Salus audio.** This applies to both the existing catalogue and all future sessions. The platform target is 100+ sessions. Every new session follows the vault workflow: script â†’ structural guidelines check â†’ generate candidates â†’ human A/B pick â†’ assemble â†’ review â†’ deploy. Brute-force full-session rebuilding is superseded.

**Why this exists:** Brute-force rebuilding wastes API credits fighting Fish's randomness. The narrator welcome session demonstrated the ceiling: 14 consecutive full builds produced zero builds with all chunks clean. The vault approach achieved 100% clean on the first human selection pass.

### The Critical Finding â€” Score â‰  Quality

The narrator welcome trial produced hard evidence that the composite scoring metric does not predict human-perceived quality:

| Approach | Method | Human clean rate |
|----------|--------|-----------------|
| Build 1 (standard) | Automated build | 1/5 (20%) |
| Build 2 (focus rebuild) | Best-of-10 on problem chunks | 2/5 (40%) |
| 14 batch builds | Automated quality search | 0/14 all-clean (0%) |
| Cherry-pick splice | Highest-scoring chunk from each of 14 builds (avg 0.811) | 1/5 (20%) |
| **Vault + human picks** | **Human selects versions that sound right** | **5/5 (100%)** |

**Implication:** Automated scoring is a useful pre-filter (eliminates the worst candidates) but CANNOT make final selection decisions. Human ears must make the final pick. This is not a temporary limitation â€” it reflects the fundamental gap between measurable spectral properties and human perception of Fish's generative artefacts.

### A/B Tournament Picker (ONLY permitted picker format â€” 10 Feb 2026)

The A/B tournament picker is the standard human review interface for all vault picks. The original per-candidate PICK/X interface is deprecated and must not be built. Use the preserved 4-file picker code from `debrief-vault-picker-session52.md` Section 3 verbatim.

**How it works:**

1. Two candidates are presented side by side (A and B) with audio players, composite scores, duration, and tonal distance displayed
2. The reviewer listens to both and picks one: **A wins**, **B wins**, or **Reject both**
3. If A or B wins â€” the winner is locked immediately (one click, done). The loser goes to the rejected list. Auto-advances to next unpicked chunk.
4. If Reject both â€” both candidates go to the rejected list. The next two non-rejected candidates load. If only one remains, it auto-wins. If none remain, the chunk is flagged as all-rejected.
5. Keyboard shortcuts: `A` = A wins, `B` = B wins, `S` = Reject both, `â†`/`â†’` = navigate chunks
6. State saves to both localStorage and a Cloudflare Worker API (merge on load for cross-device continuity)
7. Chunk navigation grid shows pick status: green (A won), amber (B won), red (all rejected), grey (unpicked)
8. Export to `picks.json` for assembly pipeline consumption

**Reject-both behaviour (fixed 10 Feb 2026, commit 60396ee):** Clicking "Reject Both" stays on the current chunk and loads the next candidate pair. Previously it auto-advanced to the next chunk after 600ms, which was wrong â€” the reviewer needs to hear more pairs for the same chunk, not skip ahead.

**Why A/B is faster than scanning:** Side-by-side comparison eliminates the cognitive load of remembering previous candidates. The reviewer only ever compares two things. "Reject both, load another pair" prevents forced mediocre picks.

**Labelled training data:** Every pick and rejection generates labelled data for the echo detector. The A/B selection process itself becomes a quality signal: rejected candidates are negative examples, picked candidates are positive examples.

**Picker code:** The complete working code (4 files: JS 529 lines, CSS 64 lines, HTML 16 lines, Python assembly 101 lines) is preserved in `debrief-vault-picker-session52.md` Section 3. This code took 6â€“7 error iterations to reach its working state and MUST be output verbatim, not recreated from description. The bugs were subtle (version 0 falsy comparisons, saveState exceptions blocking renders, tournament bracket requiring 4 clicks instead of 1, "reject both" semantics wrong).

**Performance data (Court of Your Mind â€” 66 chunks):**

| Metric | Value |
|--------|-------|
| Chunks picked | 65/66 in session (66/66 total after chunk 53 regeneration) |
| Time to pick | 1.5 hours |
| Average time per chunk | ~80 seconds |
| Ratio: picking time to session length | 4.5:1 |
| Total rejections | 199 |
| Average rejections per chunk | 3.0 |
| Zero-rejection picks (first pair) | 4 (6%) |
| Deep rejections (5+) | 12 (18%) |
| Deepest single chunk | Chunk 62 â€” 17 rejections |

### Validated Workflow

1. **Script** â†’ Structural guidelines check (Section 13) + autonomous fixes for quantifiable rules
2. **Generate N candidates per chunk** (20 standard, more for difficult chunks)
3. **Pre-filter:** Composite score pre-filter at 0.30 removes the worst candidates. This is a coarse filter only â€” it eliminates obvious failures, not a quality gate.
4. **Build review.html** with `rebuild_full_picker.py` (from preserved picker code)
5. **A/B tournament picker:** Human selects best version per chunk via side-by-side comparison (listening at high volume on AirPods)
6. **Export picks.json** from the picker interface
7. **Run vault-assemble.py** (see Section 16D for specification)
8. **Post-assembly QA gates** (mandatory: Gates 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13)
9. **Human end-to-end listen** (mandatory â€” catches assembly-level issues)
10. **Deploy**

For pace-sensitive chunks (openings, short phrases): generate extra candidates (20+ instead of 10), filter by natural duration range before presenting for selection. Do NOT use atempo post-processing (Production Rule 17).

### Vault Scope â€” Current Inventory

| Metric | Value |
|--------|-------|
| Sessions in vault | 54 |
| Total chunks | 782 |
| Total candidates generated | 12,793 |
| Pre-filter failures | 3,148 (24.6%) |
| Total R2 objects | ~13,000 |
| Estimated total generation cost | Â£2.70â€“Â£4.52 |
| Sessions awaiting human picks | 23 |
| Picks completed | 0 (of 23) |
| Estimated human review time | ~32 hours (782 chunks Ã— 5 rounds Ã— 30s) |
| Scripts to recover or reconstruct | 6 (05, 06, 07, 08, 11, 29) |
| Platform target | 100+ sessions |

### Data Files

| File | Contents |
|------|----------|
| `content/audio-free/batch-archive/` | 14 build archives (MP3 + WAV + manifest + scores JSON per build) |
| `content/audio-free/vault-candidates/` | Candidate chunks from vault trials |
| `content/audio-free/vault-candidates/review.html` | Interactive vault picker page |
| `debrief-vault-picker-session52.md` | Historical record: bug history, 66-row picks data, architecture. Code superseded by Appendix A of this document. |


---

## 16D. Vault Production Workflow for Code

**Status:** ACTIVE â€” this section governs all vault production runs. Code reads this as its operational reference for vault work.

### Purpose

This section absorbs the code debrief into the Bible itself, so Code has a single document to reference for vault production. Briefs to Code become shorter â€” they reference Bible sections rather than carrying their own operational instructions.

### Numbered Workflow Sequence (Revised 13 Feb 2026)

```
1. Script â†’ Structural guidelines check + autonomous fixes (Section 13)
2. Generate candidates per chunk (20 standard, split threshold 150 chars)
3. Pre-filter (0.30 composite score â€” advisory only)
4. Run auto-picker v8 (severity-aware selection â€” Section 16E)
5. Assemble voice-only (concat + loudnorm on voice track BEFORE ambient)
6. Prepend 30s silence to voice track (structural pre-roll â€” Section 11)
7. Mix with ambient (per-source gain, numpy direct addition, 30s fade-in / 60s fade-out per Bible spec)
8. Deploy to R2 + CDN cache purge (Production Rule 20) + Gate 15 post-deploy scan
9. Human full-audio review (listen end-to-end, report failures at timestamps)
10. Map failures to chunks â†’ rechunk failing chunks via --rechunk flag (20 extra candidates per fail)
11. Re-run auto-picker with verdict history + rechunk-history.json â†’ re-assemble â†’ redeploy
12. Repeat rounds 9-11 until pass rate acceptable (typically 1-3 rounds)
```

Steps 1â€“8 and 10â€“11 are autonomous. Steps 9 and 12 require Scott. Typically 1â€“3 rounds to reach 96%+ pass rate.

**Key workflow shift (13 Feb 2026):** Auto-picker v8 adds `--rechunk` for targeted re-picking of failing chunks (locking all passing ones), `--regen-chunks` for expanding candidate pools on stubborn chunks, and pool contamination detection that warns when the same defect persists across rounds. Human review moves from per-chunk A/B picking to full-audio review of pre-selected assembly (~15 min per round, 1â€“3 rounds = ~45 min total).

**Assembly pipeline (MANDATORY ORDER):**
```
voice WAV â†’ prepend 30s silence â†’ loudnorm voice-only â†’ mix ambient (post-loudnorm, numpy) â†’ MP3 (no second loudnorm)
```

Never loudnorm the combined voice+ambient signal. Never use ffmpeg `amix`. See Section 11 Ambient Rules for full specification.

### vault-assemble.py Specification

**Status:** PRODUCTION â€” full end-to-end pipeline including ambient mixing (14 Feb 2026). Located at `vault-assemble.py`. Previously ambient mixing was manual ffmpeg; now codified as CLI flags. Voice-first loudnorm, numpy direct addition, per-source gain table, verification checklist â€” all single-command.

**Input:** `picks.json` from the Worker API (or from local export)

**CLI ambient flags (14 Feb 2026):**
```bash
vault-assemble.py SESSION --ambient rain --fade-in 30 --fade-out 60
```

| Flag | Purpose | Notes |
|------|---------|-------|
| `--ambient` | Ambient source name | Looks up per-source gain from internal table |
| `--fade-in` | Fade-in duration (seconds) | Also sets structural pre-roll (voice delayed by this value) |
| `--fade-out` | Fade-out duration (seconds) | Applied to final N seconds |

Per-source gain table (built into vault-assemble.py):

| Source | Gain | Rationale |
|--------|------|-----------|
| grace | -14dB | Benchmark level |
| birds / birds-8hr | -9dB | Quieter source, +5dB boost |
| garden / garden-8hr | -9dB | Quieter source, +5dB boost |
| fire | -9dB | Quieter source, +5dB boost |
| courtroom | -14dB | Matches benchmark |
| ocean | -16dB | Broadband, naturally prominent |
| waves | -16dB | Broadband, naturally prominent |
| rain / rain-8hr | -17dB | Broadband, naturally prominent |
| rain-on-tent | -17dB | Broadband, naturally prominent |
| stream / stream-3hr | -17dB | Broadband, naturally prominent |
| train | -17dB | Broadband, naturally prominent |

**Note:** This table must stay in sync with the Ambient Volume Reference in Section 11. Section 11 is the canonical source of truth.

Garden ambient has a 10-second offset skip (first 10s contain a recording artefact).

**Compound ambient gap (14 Feb 2026):** `vault-assemble.py`'s `find_ambient_file()` does not support "+" syntax (e.g. "birds+fire"). `remix-session.py` does. Sessions 40, 59, 62, 72 all use compound ambients. If `vault-assemble.py` needs to rebuild these sessions, it will fail at ambient mixing. Resolution: add "+" parsing to `vault-assemble.py`, or mandate `remix-session.py` for compound ambient sessions. [L-51]

**Gate 9 KeyError crash (14 Feb 2026):** `vault-assemble.py` crashes in Gate 9 (visual report) with `KeyError: 'time'` on energy spike flags. Non-blocking — audio is fully built before the crash — but prevents QA completion. Bug is in `build-session-v3.py` line 2768: `ax.axvline(x=flag['time'], ...)` where the flag dict uses a different key name. [L-52]

**Chunking bug: silence marker merge (14 Feb 2026):** `preprocess_blocks()` merge logic can merge separate script lines (with `...` silence markers between them) into a single chunk when each sub-line is <50 chars. Evidence: S01 chunk 7 merged three lines across 8s and 50s pauses into a single 131-char chunk. **New safety rule:** NEVER merge blocks that have `...` silence markers between them in the source script, regardless of character count. The <50 char merge is an optimisation for continuous speech; it must not cross deliberate pause boundaries. [L-53]

**Process:**
1. Read picks.json â€” get the picked version number and file path for each chunk
2. Copy picked WAVs to `picks/c{XX}_pick.wav`
3. Apply 15ms cosine edge fades to each chunk before concatenation
4. Insert silence pauses from the script (read pause markers from the script metadata). Builds segments manifest (`final/assembly-manifest.json`) with timing data (type, start_time, end_time, duration, text) for each chunk and silence.
5. Concatenate all chunks + silences into a single WAV
6. **Voice-first loudnorm:** `loudnorm=I=âˆ’26:TP=âˆ’2:LRA=11` on voice-only WAV BEFORE ambient mixing
7. **Prepend structural pre-roll:** N seconds silence prepended to loudnormed voice (N = `--fade-in` value, default 30s)
8. **Mix ambient:** numpy direct addition (`np.clip(voice + ambient, -32768, 32767)`). Ambient faded in over N seconds (logarithmic curve), faded out over M seconds (`--fade-out`, default 60s). No ffmpeg `amix`. No second loudnorm on combined signal.
9. **Run verification checklist** (automated):
   - Pre-roll RMS rises from ~-76dB to ~-38dB over 30s (5s windows)
   - Voice entry at t=30s shows >20dB RMS jump
   - Ambient RMS consistent during speech (sample at t=60, 300, 600, 1200s â€” within 3dB)
   - Tail fading: last 5s RMS < -60dB
10. Output WAV + 128kbps MP3 to `final/`
11. Run `run_vault_qa()` â€” 11 mandatory post-assembly gates via `build.qa_*()` functions:
   - Gates 1, 3, 5, 8, 10, 11 â†’ on loudnormed WAV
   - Gate 2 (click scan) â†’ on raw pre-loudnorm WAV, detection only (no auto-patching)
   - Gate 7 (volume surge) â†’ on raw pre-loudnorm WAV
   - Gate 12 (duration) â†’ on final MP3 + script metadata (parses `Duration-Target:` header)
   - Gate 13 (ambient) â†’ now covered by step 9 verification checklist
   - Gate 9 (energy spike) â†’ runs last with cumulative results, produces visual report
12. Build report â€” includes `qa_passed`, `qa_gates`, and per-gate `qa_summary`
13. Returns False / exit code 1 on QA failure with "do NOT deploy" message

**Architectural significance (14 Feb 2026):** This is a major shift. Previously, ambient mixing required manual numpy scripts or ffmpeg commands outside the pipeline. Now vault-assemble.py is the single entry point for the entire voice â†’ ambient â†’ QA â†’ output workflow. No manual mixing steps remain.

**First target:** Session 52 (The Court of Your Mind). picks.json is available from the Worker API at `https://vault-picks.salus-mind.com/picks/52-the-court-of-your-mind` (Bearer token: `salus-vault-2026`).

### Picker Code Location

The complete working A/B tournament picker code is embedded in **Appendix A** of this document. This is the authoritative source â€” Code must use this code directly, not rebuild from description. The picker took 6â€“7 error iterations to reach its working state.

Four files (all preserved in Appendix A):
- `ab_picker_js.js` â€” 525 lines, the full A/B tournament engine
- `ab_picker_css.txt` â€” 64 lines, complete styling
- `ab_picker_html.txt` â€” 16 lines, the page structure
- `rebuild_full_picker.py` â€” 101 lines, reads chunk metadata and assembles review.html

On disk, these files live at `tools/vault-picker/`. The `rebuild_full_picker.py` script reads the other three files from the same directory and assembles them with chunk metadata into `review.html`.

### Config, Paths, Environment

| Item | Value |
|------|-------|
| Vault base directory | `content/audio-free/vault/{session-id}/` |
| Chunk directories | `c00/`, `c01/`, ... `c{NN}/` |
| Chunk metadata | `c{XX}/c{XX}_meta.json` |
| Candidate audio | `c{XX}/c{XX}_v{NN}.wav` |
| Review page | `vault/{session-id}/review.html` |
| R2 audio base | `https://media.salus-mind.com/vault/{session-id}` |
| Worker API | `https://vault-picks.salus-mind.com` |
| Worker auth | `Bearer salus-vault-2026` |
| Picks endpoint | `GET/PUT /picks/{session-id}` |
| Pre-filter threshold | 0.30 composite score (coarse filter â€” NOT a quality gate) |
| Edge fades | 15ms cosine on each chunk before concatenation |
| Loudnorm | `I=âˆ’26:TP=âˆ’2:LRA=11` whole-file after concatenation |
| Final encode | 128kbps MP3 (single lossy step) |

### Catalogue Generation Workflow

When Scott provides a session list with target durations, Code does everything else autonomously:

1. Apply structural guidelines to each script (200 char ceiling, no stacked punchy phrases, closing sections simpler than body) â€” these are quantifiable rules, not subjective judgments. No approval required.
2. Set the `Duration-Target` header from Scott's specified length
3. Generate 20 candidates per chunk (more for chunks that were borderline on structural guidelines)
4. Build the review.html picker page per session
5. Upload candidates to R2 at `vault/{session-id}/`
6. Commit metadata to git
7. Notify Scott that picker pages are ready for A/B review

Scott then picks at his own pace. After picking, Code assembles, runs post-assembly gates, uploads for final listen, and deploys on Scott's approval.

### Known Issues

1. **Chunk pre-filter wipe:** Some chunks have all candidates filtered by the 0.30 threshold (session 52 chunk 53). Consider a mechanism to present unfiltered candidates when all are filtered, rather than requiring manual intervention.
2. **Picker template mismatch (workaround in place).** `vault-builder.py`'s internal `generate_picker_html()` function still produces the deprecated PICK/X interface. Every vault-builder run MUST be followed by `rebuild_full_picker.py {session-id}` to replace `review.html` with the A/B tournament picker. This is a two-step process until the vault-builder is updated to embed the A/B code directly. `rebuild_full_picker.py` has been generalised (10 Feb 2026): accepts any session ID, reads source files from `tools/vault-picker/`, and uses `{{SESSION_ID}}` template placeholders. Tested across all 23 sessions.
3. **Picker localStorage dependency:** The picker uses localStorage for state persistence alongside the Worker API. State is device-specific until synced to the Worker. The merge-on-load logic handles this.
4. **vault-builder `--regen-chunks` reads meta, not script (13 Feb 2026).** When regenerating candidates for a specific chunk, `vault-builder.py` reads the chunk text from `c{XX}_meta.json`, NOT from the script file. If the script has been updated (e.g. opening line rewrite) but the meta file has not, `--regen-chunks` will generate candidates with the OLD text. **Gotcha discovered during Session 01 rebuild:** chunk 0 was regenerated with 50 candidates â€” all contained the old opening line because meta hadn't been updated. Fix: always update `c{XX}_meta.json` text field BEFORE running `--regen-chunks`, or delete and recreate the chunk directory. This is a data-source priority issue, not a bug per se, but it will bite anyone who changes script text and then expects regen to pick up the change automatically.

### Do Not

- Do not modify the PROJECT-BIBLE. Read it as reference only. If you find errors, report them.
- Do not change gate thresholds without approval.
- Do not use atempo on Fish output (Production Rule 17).
- Do not overwrite raw narration WAVs (Production Rule 14).
- Do not deploy without human review (Production Rule 7).
- Do not recreate the picker code from description â€” use the preserved code from Appendix A of this document.


---

---

## 16E. Auto-Picker

**Status:** PROVEN â€” v8 validated across 245+ chunks, 9 sessions, 5,146+ candidates. V8 automation trial (13 Feb): 100% R1 pass on 7 of 8 sessions (01, 38, 39, 40, 41, 09, 52), 93% on session 53. First fully assembled session (39) at 96% pass rate. Session 03 full rebuild: 47/49 clean after 5 rechunk rounds. Replaces manual A/B tournament as primary candidate selection method.

### Why This Exists

The A/B tournament picker required ~58 hours of manual picking across 1,400 chunks. The auto-picker reduces human time from ~2 hours to ~45 minutes per session â€” an 80% reduction. At scale (54 sessions), this saves approximately 40 hours of human review time.

### Development History (v1â†’v8, 13 Feb 2026)

| Version | Pass Rate | Key Change |
|---------|-----------|------------|
| v1 | 23% | Quality score ranked (baseline) |
| v2 | 23% | Echo-first ranking â€” same rate, different composition |
| v3 | 23% raw / 73% effective | Severity tracking â€” 13 of 20 fails were SOFT (masked by ambient) |
| v4 | 53% | Known-pass bypass + hard-fail elimination + soft-fail penalty |
| v5 | Cross-session validated | Filters loosened â€” eliminations reduced 89% (95â†’10 human picks wrongly rejected) |
| v6 | 61.2% top-3 | Weight sweep (230+ combos). Tonal distance discovered as strongest signal (+7.8%) |
| v7 | 96% (session 39 live) | Three-layer cutoff + compound filter. First assembled session from auto-picker. |
| v8 | 100% (7/8 automation trial) | `--rechunk`, `--regen-chunks`, assembly verdict loading, rechunk history, pool contamination detection, trigger word pre-flight |

### Algorithm (v8 â€” CURRENT)

**Three mechanisms (unchanged from v7):**

1. **Known-pass bypass:** Human-confirmed clean versions skip ALL elimination filters. A candidate scoring 0.263 composite (below the 0.30 floor) that was rated EXCELLENT by ear is sacred â€” never re-eliminated.

2. **Hard-fail profile elimination:** Candidates with metrics within 15% of known hard-fail versions rejected before ranking.

3. **Soft-fail penalty:** Candidates similar to soft-fail profiles penalised in ranking (âˆ’500 points). Known-pass candidates receive +1000 bonus.

**Ranking weights (v8 â€” unchanged from v7 weight sweep):**

```python
ECHO_RANK_WEIGHT = 200        # Echo risk penalty
QUALITY_RANK_WEIGHT = 6.0     # Composite quality score
TONAL_RANK_WEIGHT = 250       # MFCC distance to previous chunk (strongest signal)
FLATNESS_PENALTY = 20         # Spectral monotony
HISS_RANK_WEIGHT = 0          # DISABLED â€” ambient masks hiss, any weight hurts accuracy
DURATION_PREFER = 0           # DISABLED â€” "humans prefer longer" was WRONG at every weight tested
```

**Three-layer cutoff detection (unchanged from v7):**

| Layer | Method | Threshold | What it catches |
|-------|--------|-----------|-----------------|
| 1 | Duration cutoff | `chars/22` | Fish stops mid-text â€” extreme truncation |
| 2 | Tail cutoff | < 12ms trailing silence | Audio ends mid-waveform. `measure_tail_silence()` reads last 500ms of WAV, finds last sample above âˆ’40 dBFS |
| 3 | Compound cutoff | `cps > 14 AND tail < 25ms AND chars > 80` | Fish rushing with abrupt end. Neither tail nor chars/sec alone catches this â€” the combination is the signal |

**Content cutoff as ranking penalty or elimination: PROVEN HARMFUL** at every weight (50â€“500) and every threshold (15â€“18 ch/s) across all test phases. Pushes to worse alternatives because existing human picks include content cutoffs.

**UNRESOLVABLE detection:** When all candidates are eliminated, chunk is flagged UNRESOLVABLE. Action: split text at sentence boundary, regenerate. Do not silently fall back to lowest-scoring candidate.

### V8 New Features (13 Feb 2026)

**`--rechunk` flag:** Re-pick only failing chunks. All other chunks are LOCKED (text match â†’ preserve pick). Loads `rechunk-history.json` to avoid re-picking known-bad versions. Assembly verdicts from `assembly-verdicts.json` feed failed versions into the hard_versions elimination list.

**`--regen-chunks` flag:** Works with vault-builder to expand candidate pool for stubborn chunks without a full rebuild. Usage: `vault-builder.py SESSION --regen-chunks 9,14 --count 50` generates 50 fresh candidates for chunks 9 and 14.

**`rechunk-history.json`:** Persists failed versions across rechunk rounds per chunk. Prevents the auto-picker from re-selecting a version that already failed human review. Accumulates across rounds â€” each round's failures are appended, not overwritten.

**Assembly verdict loading:** `_load_assembly_verdicts()` reads `assembly-verdicts.json` (exported from review page). Failed versions are added to the `hard_versions` elimination list. Known-pass versions are protected.

**Trigger word pre-flight scan:** Before picking, runs `trigger-word-scan.py` logic on chunk text. Chunks with trigger words get a ranking penalty.

**Pool contamination detection:** `detect_pool_contamination()` runs automatically during `--rechunk` before picking begins. Scans `rechunk-history.json._defect_log` for the same defect type persisting 2+ rounds on the same chunk. Prints `*** POOL CONTAMINATION DETECTED ***` warning with escalation recommendation:
- 2 rounds same defect â†’ `--regen-chunks X --count 50`
- 3+ rounds same defect â†’ SCRIPT REWRITE

Non-blocking â€” rechunk still proceeds, but contaminated picks are tagged in `picks-auto.json` and `auto-pick-log.json`.

**`rechunk-history.json` extended format:**
```json
{
  "14": [26, 22, 17],
  "_defect_log": {
    "14": [
      {"version": 26, "defects": ["VOICE", "BAD"], "round": "v8-R1"},
      {"version": 22, "defects": ["VOICE", "BAD"], "round": "v8-R2"},
      {"version": 17, "defects": ["ECHO"], "round": "v8-R3"}
    ]
  }
}
```
Backwards-compatible â€” old rechunk-history files without `_defect_log` work fine (no detection, no crash).

**Detection timing:**
- R2 rechunk: Saves R1 defects to log. Only 1 entry per chunk â†’ no detection yet.
- R3 rechunk: Saves R2 defects. Now 2 entries â†’ CAN detect 2-round contamination.
- R4+: Escalates recommendation from `--regen-chunks` to SCRIPT REWRITE at 3+ rounds.

### V8 Bugs Found & Fixed (13 Feb 2026)

| # | Bug | Impact | Fix |
|---|-----|--------|-----|
| 1 | **pass_versions override** | Versions in both hard + pass lists got +1000 bonus, bypassing elimination | Assembly failures now remove from pass_versions |
| 2 | **Assembly verdict format** | Verdict field is list not string, code called `.upper()` on list | Handle both formats |
| 3 | **R2 upload math** | Fragile version arithmetic for regen uploads | Explicit `regen_start_versions` tracking |
| 4 | **Vault text mismatch** | 23/26 session 01 meta files had wrong text (51-chunk split text while WAVs contained 26-chunk merged audio) | Restored from pre-rechunk backup |
| 5 | **Rechunk history not persisting** | Only blocked current pick, not all prior failures | `rechunk-history.json` accumulates across rounds |
| 6 | **`_load_existing_picks` stale read** | Read `picks/picks.json` (assembly copy) instead of `picks-auto.json` | Reversed priority: auto-picks first |

### Honest Assessment (13 Feb 2026)

- **R1 pass rate improving:** Trigger word scan adds ~4% (87% vs 83%)
- **Rechunk loop is re-rolling, not learning** â€” no metric predicts echo or closing-chunk cutoff. Document honestly.
- **Closing chunks need structural fix** (tail fade + soft-ending script rule) not algorithmic improvement
- **The algorithm is a reliable shortlister but human review remains mandatory**
- **Auto-picker confidence â‰  human verdict:** 12/16 R1 failures in session 03 had HIGH confidence. c05 marked UNRESOLVABLE â†’ human rated EXCELLENT (false alarm).
- **Human review variance is ~15%.** Locked chunks can regress between rounds â€” same audio, different verdict. Most flips are between PASS and SOFT FAIL.

### Critical Findings

**Quality score does NOT predict human verdict (PROVEN â€” 78 labelled verdicts):**

| Severity | Avg Quality Score | Range |
|----------|------------------|-------|
| PASS | 0.890 | 0.667â€“1.293 |
| HARD FAIL | 0.990 | 0.836â€“1.199 |
| SOFT FAIL | 0.846 | 0.511â€“1.321 |

Complete overlap between pass and hard fail. A candidate scoring 1.199 can be a hard fail while one scoring 0.667 is EXCELLENT. Composite score is a pre-filter only, not a selection metric.

**Tonal consistency is the strongest ranking signal.** MFCC distance to previous chunk measures voice consistency. Lower = better. Weight sweep Phase 4 discovered this: tonal=500 produced +7.8% top-3 improvement. Final weight settled at 250 (balanced with other signals).

**Duration preference ALWAYS hurts.** Every non-zero duration weight reduced accuracy across all 72 combinations tested. The intuition "humans prefer longer" was wrong for ranking.

**Hiss weight ALWAYS hurts.** Ambient masks hiss. Humans don't penalise it. Zero hiss weight is optimal.

**Human review variance is ~15%.** Across 4 runs, 4 regressions were the same audio file receiving different verdicts. Most flips are between PASS and SOFT FAIL. The severity system helps â€” it captures the gradient that binary pass/fail misses.

**Pick locking (12 Feb 2026):** When re-running the auto-picker after script changes or vault restructuring, existing human-verified picks for unchanged chunks are LOCKED and skip re-picking. The `_load_existing_picks()` function loads existing `picks.json`, and `auto_pick_session()` checks each chunk: if the text is unchanged AND an existing pick exists, it marks the pick as LOCKED. Handles minor text variants (e.g. Salus/SÄlus macron differences) via normalisation. **Evidence for need:** Narrator-welcome rescript (5â†’6 chunks) caused the auto-picker to re-pick ALL chunks including c00. It chose v08 ("Hello") instead of the known-good v78 ("Welcome to SÄlus"). A human-verified pick was overwritten by an automated re-run â€” this must never happen.

### Defect Priority (from human review data)

1. **Tonal consistency** â€” voice character shifts between chunks (highest impact)
2. **Cutoff** â€” zero tolerance, outright unusable
3. **Echo** â€” noticeable but ambient masks mild cases
4. **Quality** â€” general audio cleanliness
5. **Flatness** â€” spectral monotony
6. **Hiss** â€” lowest priority, ambient masks significantly

### Validation Data (v8 Final)

| Metric | Value |
|--------|-------|
| Exact match (auto-pick = human pick) | 68.6% (168/245) |
| Top-3 (human pick in auto-picker's top 3) | 77.1% (189/245) |
| Eliminated (human pick rejected by filters) | 4.9% (12/245) |
| Chunks validated | 245 |
| Sessions validated | 10 |
| Candidates analysed | 5,146+ |

**V8 algorithm performance across sessions:**

| Session | Chunks | R1 Pass | R1 % | Rounds to Clean | Status |
|---------|--------|---------|------|-----------------|--------|
| 01 (prior data) | 26 | 16 | 61.5% | 5 | DEPLOYED |
| 38 (human picks) | 27 | 27 | 100% | 0 | DEPLOYED |
| 39 (prior auto) | 25 | 25 | 100% | 0 | DEPLOYED |
| 40 (fresh) | 29 | 24 | 82.8% | 2+ | DEPLOYED |
| 41 (fresh + trigger scan) | 23 | 20 | 87.0% | 5 (c22 stubborn) | DEPLOYED |
| 03 (full rebuild) | 49 | 33 | 67.3% | 5 (2 stubborn) | DEPLOYED (47/49) |
| 09 (auto v8) | 63 | 63 | 100% | 0 | DEPLOYED |
| 52 (auto v8) | 66 | 66 | 100% | 0 | PICKED â€” awaiting assembly |
| 53 (auto v8) | 59 | 55 | 93.2% | â€” | DEPLOYED (4 flagged) |

**Note:** Session 03 R1 drop due to 49 chunks (vs 23-29 for others). Per-chunk fail rate: 03=32.7% vs 41=13.0% â€” breathing sessions have more short chunks that Fish handles inconsistently.

### Review Page Generator (`tools/review-page-generator.py`)

Production-quality HTML review tool for human verdict collection. Two modes:

**Single mode** (`--mode single`): 1 pre-picked candidate per chunk
```bash
python3 tools/review-page-generator.py 03-breathing-for-anxiety --run v8-R2 --mode single
```

**Top-3 mode** (`--mode top3`): 3 auto-picker candidates per chunk (A/B/C selection)
```bash
python3 tools/review-page-generator.py 03-breathing-for-anxiety --run v8-R2 --mode top3
```

**Features:**
- Dark theme, keyboard-driven: 1=EXCELLENT 2=OK 3=ECHO 4=HISS 5=VOICE 6=CUTOFF 7=BAD
- H=Hard fail, S=Soft fail severity
- Autoplay with auto-advance (Space=pause, Enter=next)
- Auto-save to Worker API (`vault-picks.salus-mind.com/verdicts/`)
- Export verdicts as JSON (feeds into `assembly-verdicts.json` for rechunk)
- Per-chunk metadata: quality_score, margin, confidence, version
- Top-3 mode: A/B/C pick buttons, plays all options sequentially

File: `tools/review-page-generator.py` (830 lines, self-contained). Output: `{vault-dir}/auto-trial-review-{run}.html` or `top3-review-{run}.html`. Audio paths default to R2 URLs â€” for local review, replace `https://media.salus-mind.com/vault/{session}/` with `./`.

### Auto-Rebuild Loop (`auto-rebuild-loop.py`)

Automated rechunk loop: runs auto-picker â†’ generates review page â†’ waits for verdicts â†’ rechunks failures â†’ repeats until clean or max rounds. Handles pool contamination escalation.

```bash
python3 auto-rebuild-loop.py 03-breathing-for-anxiety --max-rounds 5
```

### Files

| File | Purpose |
|------|---------|
| `auto-picker.py` | v8 auto-picker (v7 algorithm + rechunk + regen-chunks + assembly verdicts + rechunk history + pool contamination + trigger word pre-flight) |
| `auto-rebuild-loop.py` | Automated rechunk loop (pick â†’ review â†’ rechunk â†’ repeat) |
| `sweep-weights.py` | Automated weight sweep tool (230+ combos across 5 phases) |
| `tools/review-page-generator.py` | Review page generator (single mode + top-3 mode, keyboard-driven, auto-save) |
| `tools/trigger-word-scan.py` | Standalone script scanner (reads trigger-words.json, reports hits with line numbers) |
| `content/trigger-words.json` | Machine-readable trigger word list (17 words + 1 regex pattern) |
| `docs/auto-picker-validation.json` | v8 validation data (245 chunks, 10 sessions) |
| `docs/weight-sweep-results.json` | Full sweep data (phases 1â€“3) |
| `docs/weight-sweep-phase4.json` | Tonal/hiss sweep data |


## 16F. Voice Breakout Detection

**Status:** VALIDATED — standalone scanner tested against 1,721 WAVs. Awaiting auto-picker integration (L-50).

This section documents the full-catalogue retrospective scanner. For Gate 17 specification (features, thresholds, operating philosophy), see Section 12 Gate 17.

### Two Roles

**Role 1 — Per-candidate gate in auto-picker (pre-assembly).** Same pattern as Gate 16 echo. During vault picking, each candidate WAV gets scored by the breakout scanner. High z-scores get a penalty, extreme z-scores get eliminated from the pool. The auto-picker swaps to the highest-ranked unflagged alternative. This happens BEFORE assembly — it's a candidate filter. L-50 tracks this integration.

**Role 2 — Full-catalogue post-deployment scanner.** `breakout-scanner.py --scan --all` across all 1,721 deployed WAVs in ~8 minutes. Retrospective quality net — catches defects from older builds or that slipped through. Labelling UI (`breakout-picker.html`) with autoplay for suspect review. Verdicts feed back into classifier training.

### Full-Catalogue Scan as Standard QA Method

The breakout scanner established a new QA pattern: scan the entire deployed catalogue, label everything flagged, action in batch. This is distinct from per-session QA — it catches defects across all historical builds simultaneously. ~8 minutes for 1,721 WAVs. The same pattern applies to Gate 16 echo scanning.

### Known Blind Spots

- **Type B timbral/register shifts** — subtle tonal changes without extreme F0/spectral discontinuity. S43 c23/v14 is the known example (rank 971, MISSED). Research direction: formant-tracking features (F1/F2 discontinuity) and voice-quality measures (jitter, shimmer, HNR shift) may catch this class.
- **Repeat defects** — Fish generating phrases twice. Not detectable by spectral features. Future Gate 18 via Whisper transcription comparison.
- **1,280 unflagged WAVs were never labelled** — false negatives in the "clean" set are unknown.
- **Labelling data contamination** — CLEAN label used strictly as "no breakout" for the first ~200 suspects. Echo defects not tagged until the second half of the pass. True defect count higher than reported totals. Affects classifier training if CLEAN is treated as ground truth for "no defect".

### Files

| File | Purpose |
|------|---------|
| `breakout-scanner.py` | Standalone scanner. `--scan --all` for full catalogue, `--label` for verdict UI. |
| `reference/breakout-analysis/breakout-scan-results.json` | Population baselines (1,721 WAVs) — SACRED, do not recompute per session. |
| `reference/breakout-analysis/breakout-suspects.json` | 441 flagged suspects with scores |
| `reference/breakout-analysis/breakout-verdicts.json` | 440 labelled verdicts (237 breakout, 187 clean, 16 other) |
| `reference/breakout-analysis/breakout-picker.html` | Labelling UI with autoplay |

---


## 17. Governance

### Stop Rules

```
Autonomy Level: FULLY AUTONOMOUS â€” except where a STOP rule is triggered.
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

### Read the Bible Before Acting

Code must read the relevant Bible sections BEFORE starting any task â€” not during debugging, not after failure. The Bible exists specifically so Code doesn't have to guess at specifications.

**Incident (13 Feb 2026 â€” Session 01 ambient remix):** A 2-minute ambient parameter fix (change -16dB to -14dB and add fade-in) consumed ~4 hours because Code did not read Bible Section 11 (Ambient Rules) before starting. Specific failures:
- Used -16dB instead of Bible-specified -14dB. Had to be told twice to check the spec.
- Fundamentally misunderstood "30-second ambient fade-in" as a volume ramp starting at t=0 instead of a structural pre-roll where the voice is delayed by 30 seconds. The Bible stated this plainly ("let the ambient carry the first few seconds before the voice enters"). Code applied a volume adjustment while starting the narrator at t=1s â€” and did this three times, requiring the user to explain the concept repeatedly before Code understood.
- Used ffmpeg `amix` which silently ate the ambient signal, then tried 6 different approaches instead of diagnosing the root cause.
- Deployed broken audio to R2 production without human review.
- Ran auto-picker across 51 chunks when only chunk 0 needed attention, forcing the user to review 51 chunks unnecessarily.

**The correct approach was simple:** (1) Read Bible Section 11. (2) Take the existing approved voice WAV. (3) Prepend 30s silence. (4) Mix ambient at -14dB. (5) Generate review page. (6) Deploy only after approval. Six steps, two minutes, zero ambiguity â€” if the Bible had been read first.

**Rule reinforcement:** When a brief references a Bible section, Code reads that section in full before writing any code. Not skimming, not paraphrasing from memory â€” reading the actual text.

### Bible Version Sync (14 Feb 2026)

Code must verify its Bible copy matches the latest version at the start of every session. If versions differ, update before proceeding. The separation of duties (Desktop maintains Bible, Code reads it) only works if Code receives the latest version.

**Incident (14 Feb 2026):** In-repo Bible copy was stale at v4.2 (missed v4.3–v4.6 entirely). Code was operating against a Bible five versions behind. Updated to v4.7 (commit `d3b2a23`).

**Standing rule:** Check `Desktop/Live Bible/` at session start. If the version number differs from the in-repo copy, update before proceeding with any work.

### No Decorative Gates

Every QA gate must have a defined pass/fail condition that blocks deployment on failure. A gate that runs, produces data, and allows the build to proceed regardless is worse than no gate â€” it creates false confidence. This principle was established after two incidents where the pipeline generated clear visual evidence of defects and failed to act on it.

### No Threshold Loosening Without Approval

Gate thresholds must not be adjusted to make a failing build pass. If a gate catches too many issues, the correct response is to fix the root cause (e.g. script blocks below 50 characters producing hiss at boundaries), not to widen the threshold until the problems fall below it. Any threshold change requires human approval before implementation.

**Incident (7 Feb 2026):** Code raised Gate 6 min_duration from 3s to 5s mid-build because 11 regions at 3â€“4.5s were failing. The root cause was a script chunk at 48 characters â€” below the 50-character minimum known to cause hiss. Code chose to loosen the gate rather than fix the script. Reverted on instruction.

### Build State Persistence

All build state must be persisted to a file after every step. Never rely on conversation context for:
- Strike counter
- Build sequence number
- QA pass/fail results per gate
- Which script version is being built

**Reason:** Context compaction at 200K tokens is lossy. If Code compacts mid-build, it can lose track of state. Persistent state files survive compaction.

### Brief Lifecycle

Briefs are temporary instruction documents. They exist to direct Code, then get absorbed into the bible. A brief is not a permanent reference â€” it has a lifecycle.

```
DRAFT â†’ ACTIVE â†’ INTEGRATED â†’ ARCHIVED
```

| Stage | Meaning |
|-------|---------|
| DRAFT | Being written by Claude Desktop. Not yet issued to Code. |
| ACTIVE | Issued to Code. This is the current work order. |
| INTEGRATED | All content absorbed into the bible. Brief is now redundant. |
| ARCHIVED | Moved to `docs/archive/`. No longer referenced by any active process. |

**Rules:**

1. **One active brief per workstream.** Never issue a second brief that amends a first. Update the original brief instead. If a brief needs amending, consolidate into a single replacement document before issuing.

2. **Briefs are read-only for Code.** Code must not edit, append to, annotate, or mark up a brief under any circumstances. The brief is an instruction â€” not a progress tracker.

3. **No brief persists indefinitely.** Once the bible absorbs a brief's content, the brief moves to `docs/archive/` and stops being referenced. If Code is still reading a brief that was issued more than two build cycles ago, something has gone wrong.

4. **Amendments are consolidations, not patches.** If new information changes part of an active brief, Claude Desktop produces a new consolidated brief that replaces the original entirely. The old brief is archived. There must never be two documents where one "partially amends" the other.

### State File Separation

Code maintains a separate state file for each active brief. The brief is the instruction; the state file is the receipt.

**State file rules:**

1. **Code owns the state file.** It creates it at the start of work and updates it after every step. The state file is the only file Code is permitted to write progress into.

2. **The brief stays untouched.** Progress, strike counts, gate results, build logs, and completion markers go in the state file â€” never in the brief.

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
- [timestamp] â€” [decision and rationale]

## Issues for Human Review
- [anything requiring escalation]
```

6. **Verification:** Scott reviews the state file against the brief to confirm what was delivered. Code's self-reported progress is never treated as sign-off â€” it is a claim to be verified, not a certification.

7. **State files survive context compaction.** This is why they exist. If Code compacts mid-build, it reads the state file to recover position. Never rely on conversation context for build state.

### Document Hierarchy

```
PROJECT-BIBLE (canonical, maintained by Claude Desktop)
    â†“ instructs
Active Briefs (temporary, read-only for Code)
    â†“ tracked by
State Files (owned by Code, verified by Scott)
    â†“ archived alongside
docs/archive/ (retired briefs + their state files)
```

Code reads down. Code writes only to state files and to the codebase. Code never writes up.

### First Action on Receipt

On receiving any brief, Code's first action â€” before any implementation work â€” must be to create the corresponding state file and populate it with the full item list from the brief. This confirms the brief was read and the scope is acknowledged.

### Environment Variables

```
FISH_API_KEY=your_fish_api_key
CF_CACHE_PURGE_TOKEN=your_cf_cache_purge_token
CF_ZONE_ID=your_cf_zone_id
RESEND_API_KEY=your_resend_api_key
AUPHONIC_USERNAME=your_auphonic_username
AUPHONIC_PASSWORD=your_auphonic_password
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
- Cannot vary within a single chunk (acceptable for meditation â€” consistent tone is the goal)

### V3 Parameters

- `prosody.speed` replaces atempo in the pipeline (speed adjustment handled at API level)
- `"volume": -20 to 20` (default 0) â€” leave at 0, handle in post-processing

### Investigation Results (7 February 2026)

| Test | Result |
|------|--------|
| Marco compatibility with V3-HD | PASS â€” voice works with cloned reference |
| Voice conditioning chain on V3 | PASS â€” consistency maintained across sequential chunks |
| Credit cost | Negligible difference from S1 |

### Fallback

If V3-HD becomes unavailable or degrades:
- Fall back to S1/v1
- No in-text emotion tags (they don't work)
- Rely on expression-through-punctuation (Section 14)
- Punctuation-based control already produced acceptable results

---

# PART C â€” HISTORICAL RECORD

---

## 19. Amendment Log

This section is a historical record of changes made. It is NOT an operating reference â€” all current operating rules are in Parts A and B above. If anything in this log contradicts Parts A or B, Parts A and B are correct.

### 4 February 2026 â€” Initial Setup

21 issues completed across ASMR, Breathing, FAQ, Home, About pages. Premium flow standardised, card images deduplicated, site-wide terminology updated (Free â†’ Sample), 2-column tile grid established. Full image mapping created.

### 4 February 2026 â€” Card Image Replacements

Hero image replaced (`meditation-woman-outdoor.jpg` â†’ `japanese-fog.jpg`). All card images across index, apps, about, soundscapes, sessions replaced with unique images. Full image inventory created.

### 5 February 2026 â€” Quick Wins

Founder statement rewritten, American testimonials added, "LATIN: HEALTH" subtitle added, contact page reframed, 21 "Subscribe to unlock" instances changed to "Premium".

### 5 February 2026 â€” UI/Visual Fixes & 21-Day Course

Play button fix (mindfulness), breathing ring/countdown sync fix (unified timer), tool buttons simplified, profile pictures made consistent, session cards given player overlay UI, 21-day mindfulness course page created.

### 5 February 2026 â€” Supabase Authentication

Cross-device accounts via Supabase replacing localStorage premium system. Stripe webhook integration. 70+ pages updated with auth scripts and nav button.

### 5 February 2026 â€” UI Redesign & Navigation Overhaul

Two-row navigation, Latin phrase placement, atmospheric card design pattern, image optimisation, sleep stories updates, education tiles redesign, tools tiles equal height fix, section background blending.

### 5 February 2026 â€” UI Cleanup & Sleep Stories

Coloured tiles removed site-wide, sessions page redesigned with player bar UI, sleep stories page created (52-book library), navigation streamlined.

### 6 February 2026 â€” SEO & Infrastructure

robots.txt fixed, sitemap rebuilt (13â†’76 URLs), canonical tags + OG + Twitter cards on all 75 pages, Google Search Console verified, Cloudflare zone activated, media.salus-mind.com connected, 49 sleep story titles added.

### 7 February 2026 â€” Automated Audio QA Pipeline

Human QA gate replaced with automated 9-gate system. Click artifact detection and crossfade patching. All 5 deployed sessions scanned and patched. Edge fades added to pipeline.

### 7 February 2026 â€” QA Failure: Degraded Audio Shipped

Loving-kindness build passed click QA but had severely degraded voice quality. Root causes: QA blind spot (clicks only), lossless pipeline violation (WAVâ†’MP3â†’WAV), wrong cleanup chain. Fixed with 9-gate system, lossless pipeline, calibrated cleanup.

### 7 February 2026 â€” Lossless WAV Pipeline & Email

All intermediate audio now WAV. MP3 encoding once at final step. Channel mismatch bug fixed (mono/stereo misinterpretation). Resend email notification system added.

### 7 February 2026 â€” Loving-Kindness Session

Session `36-loving-kindness-intro` deployed (12.9 min, Fish/Marco). 3 build attempts. First 2 failed (overgeneration + channel mismatch). Build 3 passed with 0 artifacts.

### 7 February 2026 â€” Ambient Track Fix

4 sessions had ambient shorter than voice. Fixed with 8-hour ambient files. Rule established: NEVER loop ambient.

### 7 February 2026 â€” Bible Consolidation (v2.0)

Full consolidation pass. Resolved contradictions (loudnorm âˆ’24 vs âˆ’26, block minimum 20 vs 50, five conflicting cleanup chains). Integrated Brief Part 2 items 2â€“9 and Brief Part 3. Added Gate 10 (speech rate), Gate 3 sliding window fix, stop rule governance, build state persistence, overgeneration retry logic, per-chunk loudnorm. Restructured from chronological amendments to functional sections.

### 7 February 2026 â€” 14-Gate QA System & Governance (v2.1)

Expanded from 10 gates to 14 gates. All gates now pass/fail â€” no informational-only gates. Key changes:

**Gate fixes:** Gate 3 sliding window implemented (18 dB calibrated threshold). Gate 6 converted to speech-aware detection (evaluates non-speech regions only â€” resolved 100% build failure rate from sibilant false positives). Gate 8 Expected-Repetitions metadata replaces global ignore list. Gate 9 converted from informational-only to pass/fail with energy spike detection (10Ã— speech-only median threshold). Gate 10 silence-aware baseline (excludes pause windows from speech rate calculation).

**New gates:** Gate 11 (Silence Region Integrity), Gate 12 (Duration Accuracy), Gate 13 (Ambient Continuity â€” calibrated at âˆ’80 dBFS / 10 dB), Gate 14 (Opening Quality â€” tighter thresholds on first 60 seconds).

**V3-HD migration:** Complete. All TTS calls use V3-HD with `emotion: calm`. prosody.speed replaces atempo.

**HF shelf cut investigation:** Tested across full tuning range (âˆ’2 to âˆ’5 dB at 6â€“8 kHz). Failed â€” removing 3 kHz boost entirely produced identical Gate 6 flag counts, proving root cause was speech sibilants. Pipeline unchanged.

**Auphonic per-segment:** API does not return per-segment SNR. Noted as platform limitation.

**Governance additions:** No decorative gates principle. No threshold loosening without approval. Brief lifecycle (DRAFT â†’ ACTIVE â†’ INTEGRATED â†’ ARCHIVED). State file separation. Document hierarchy.

**Threshold calibration:** All new gate thresholds validated against known-good deployed sessions (25-introduction-to-mindfulness, 36-loving-kindness-intro). Calibrated values replace brief estimates where they differed.

---

### 8 February 2026 â€” Pipeline & Website Updates (v2.2)

**Audio pipeline:**
- Per-chunk loudnorm replaced with whole-file loudnorm (preserves natural dynamics)
- Highshelf boost (`highshelf=f=3000:g=3`) removed â€” caused perceived echo on certain words
- Per-chunk QA system: generates up to 5 versions of each chunk (best-of-5), scores all via composite metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance), keeps best
- **Known limitation (9 Feb 2026):** Composite scoring is unreliable for chunk 0 (opening chunk). See Section 9, Opening chunk weakness. Human listening is mandatory for all opening chunks regardless of score.
- Tonal consistency: MFCC distance to previous chunk penalised at 50Ã— weight
- Flag threshold: 0.50 (OK avg=0.708, Echo avg=0.542, calibrated on 27 human-labeled chunks)
- Session 36-loving-kindness-intro rebuilt (build 11, 10.5 min, 14/14 gates)
- Per-chunk QA upgraded from best-of-2 to best-of-5 (135 TTS calls for 27 chunks)
- v3 script rewritten: varied benedictions (no formulaic repetition), trigger words avoided
- v3 build: 14/14 gates, 70% clean rate on human review (19/27 OK, up from 58% on v2)
- Known Fish trigger words expanded: "breath in", "be" (standalone), "simply", "family", "joyful"

**Threshold recalibrations (approved by Scott during live testing session, 8 Feb 2026):**
- Gate 7 widened to 9/14 dB + proportional silence margin (`max(4s, durÃ—0.15)`) â€” required to accommodate Fish chunk-level swings under whole-file loudnorm
- Gate 8 manifest text guard added: word overlap <60% skips MFCC pairs as false positives â€” prevents meditation cadence patterns from triggering duplicate detection
- Gate 9 HF threshold recalibrated to 28Ã— speech-only median, total to 12Ã— â€” calibrated against no-ambient and ambient sessions to separate sibilants from genuine hiss

**Website:**
- Navigation Row 2 now includes Applied Psychology
- New page: `articles/anxiety-thinking.html` (first article detail page, `articles/` subdirectory)
- Applied Psychology page: featured article link, "Updated Regularly" approach item
- Mindfulness page restructured: session cards first, then 7-day + 21-day course banners
- `css/style.css` fixed at source: all light-theme backgrounds neutralised (body, hero, hero-bg::after, daily-quote, section:nth-child(even), filter-btn, sound-category-tag â†’ transparent). Per-page overrides no longer needed.
- ASMR page (`asmr.html`): "Coming Soon" placeholder replaced with 14-sound card library (rain, ocean, forest, thunder, birds, fire, stream, cafe, garden, library, night, temple, waterfall, white noise). Category filters (All/Nature/Weather/Spaces/Ambient), animated waveform bars, per-card accent colours, staggered entrance animation. Supersedes old `sounds.html`.

---

### 8 February 2026 â€” Dark Theme & Routing Fixes

**style.css dark theme completion:**
- 22 text/background color rules converted from light to dark-compatible: body text (`#f0eefc`), links (`#7c8cf5`), nav (bg `rgba(6,8,16,0.92)` + logo + links), hero paragraph (`rgba(240,238,252,0.55)`), daily quote, section headers, feature cards/icons (`rgba(124,108,240,0.12)`), form inputs/labels, filter buttons, session cards, sound cards
- CSS variables (`:root`) retained for backward-compatible selectors (footer, CTA banner, buttons)

**Login buttons:** Fixed `href="#"` â†’ `login.html` across 11 files (22 instances). Articles subdirectory uses `../login.html`.

**Mindfulness page cleanup:** Removed 6 content sections (276 lines): What is Mindfulness, The Science, Core Practices, How to Start, Mindfulness in Daily Life, FAQ. All had light gradient backgrounds causing white bands. Page now shows session cards + course banners + CTA only.

**Footer routing:** `sounds.html` â†’ `asmr.html` across 60 files (root pages + sessions/ + newsletters/).

**Premium CTA routing:** `newsletter.html` â†’ `apps.html` in media.html, sounds.html, newsletter.html.

**Subsequent completion (same day):** All 15 remaining pages converted to dark theme. Unified `hb-footer` applied to all 82 pages. breathe.html and timer.html heroes rebuilt with dark-theme pattern (radial glow, gradient text). Reading page: miniature book covers via Open Library Covers API, increased description font. Mindfulness page: fixed 7-day course 404 link.

---

### 8 February 2026 â€” Learn & Applied Psychology Content Launch

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

### 8 February 2026 â€” Session 36 Shipped & Review Workflow

**Audio production:**
- Session 36-loving-kindness-intro-v3 shipped to production (v3b focused rebuild)
- `--focus-chunks` CLI argument added: problem chunks get best-of-10, others best-of-5
- Ambient level increased from -14dB to -11dB for more present ambient bed
- Resend email fixed: Python `urllib` blocked by Cloudflare â†’ switched to `curl` subprocess

**Human review workflow established (mandatory for all future sessions):**
1. Build with `--no-deploy` â†’ 14-gate QA runs automatically
2. Extract chunks from raw narration WAV using manifest timing data
3. Upload individual chunks to R2 at `test/chunk-test-{version}/`
4. Create interactive HTML review page with export facility (Copy Results + Download TXT)
5. Listen to every chunk on AirPods at high volume (exposes hiss, echo, tonal shifts that speakers miss)
6. Rate each chunk: OK / ECHO / HISS / VOICE / BAD
7. If acceptable â†’ remix with ambient, deploy to R2, update all HTML references, commit, push, email
8. If problem chunks â†’ `--focus-chunks 1,3,6` for targeted rebuild, re-review
9. Perfection should not prevent shipping â€” accept reasonable clean rate and move forward

**Testing checklist (learned from session 36):**
- Test playback on BOTH desktop and mobile (CORS blocked mobile audio before R2 CORS was configured)
- Check ALL pages that reference the session (detail page, listing pages, mindfulness cards) â€” missed references = broken players
- Verify file duration matches expected (stale CDN cache served old file with wrong duration)
- Players without `data-src` attribute are visual-only â€” buttons do nothing by design
- Mindfulness page uses `m-player` class (inline JS), not `custom-player` (main.js) â€” different wiring

**Infrastructure:**
- R2 CORS configured: `salus-mind.com` and `www.salus-mind.com` allowed origins (GET/HEAD)
- Mindfulness page players wired up with real audio for Introduction to Mindfulness and Loving-Kindness Introduction

---

### 8 February 2026 â€” LALAL.AI Integration & Session 25 Rebuild (v3.1)

**LALAL.AI evaluation:**
- Integrated LALAL.AI voice_clean API into `build-session-v3.py` as Phase 1.5 (between chunk QA and edge fades)
- A/B tested on session 25 chunk 28 (voice shift at 6:47) â€” LALAL made no difference to voice shift (TTS generation problem, not post-processing)
- Full session rebuild with LALAL (`noise_cancelling_level=1`, `dereverb_enabled=True`): hiss removal excellent (almost all hiss gone), but dereverb stripped Marco's vocal resonance
- Dereverb damages Fish output â€” Marco's TTS has no room reverb, so dereverb removes legitimate vocal character
- LALAL disabled in build script pending retest with `dereverb=False` (noise cancellation only)

**Session 25 rebuilt:**
- Trigger word "nowhere else" discovered causing voice shift â€” replaced with "All you need to do is be right here, right now"
- 36 chunks generated (best-of-5), LALAL cleaned 36/36
- 13/14 gates passed; Gate 13 (Ambient) failed on garden-8hr.mp3 dead silence â€” fixed with `-ss 10` offset
- Deployed to R2 (commit acb5842) â€” voice quality degraded from LALAL dereverb, fresh non-LALAL rebuild initiated
- Introduction to Mindfulness tile reverted to premium locked (commit c986804)

**Fish Audio observations:**
- Possible S1 model degradation: >500 char generations temporarily routed to v1.6, causing voice inconsistency between chunks
- Opening chunks (1â€“5) consistently score lowest â€” chunk 1 has no MFCC reference for voice conditioning
- MFCC tonal distance scoring (threshold 0.50) can miss voice character shifts that human ears catch (chunk 28 scored 0.496)

**New production rules:**
- Raw narration WAVs must never be overwritten without preserving originals (timestamped copies)
- All audio quality comparisons must be narration-only â€” ambient invalidates evaluation
- Garden ambient requires `-ss 10` offset (9.5s dead silence at file start)

**Code mistakes logged:** Failed to preserve pre-LALAL narration, provided ambient-mixed files for comparison instead of narration-only, deployed LALAL build without human review, did not test LALAL settings individually before full pipeline integration. All documented for governance improvement.

---

### 8 February 2026 â€” Script Uniqueness & Cross-Session Differentiation (v3.2)

New Section 13A added to address internal repetition across the Salus session catalogue. Sessions were beginning to sound interchangeable â€” same openings, same breath cues, same structural arc, same closings. A customer listening to multiple sessions back-to-back should have distinct experiences.

**Cross-session register system:** Three mandatory register files introduced (`openings-register.txt`, `closings-register.txt`, `phrases-register.txt`) in `content/scripts/`. Every deployed session's key phrases are catalogued. New scripts are checked against existing entries before build â€” no phrase of 5+ words may be reused, no opening or closing technique may be repeated within a category.

**Six categories of repetition identified:** Openings, breath cues, body awareness transitions, silence announcements, closings, and structural arc. Each has specific variation strategies and mandatory register checks.

**Automated pre-build originality scan:** Runs alongside trigger word check during pre-flight. Fuzzy-matches new script blocks against register entries (70% threshold on 5+ word phrases). WARNING system, not a build-blocker.

**Checklist updates:** Pre-Build Checklist now includes originality scan. Deployment Checklist now requires register file updates after every session deploy.

**Narration audit (outstanding):** Full audit of all 17 deployed sessions required to retroactively populate registers and identify existing cross-session repetition. Must be completed before any new scripts are written. Added to Section 13A as a pending task.

**External originality (secondary):** Lightweight due diligence step â€” web research to consciously diverge from published scripts, no phrase of 6+ words matching a published source. Research notes stored in `content/scripts/research/`.

---

### 9 February 2026 â€” Four Sessions Deployed & Build Learnings (v3.3)

**Sessions deployed (commit 752752f):**
- 18-calm-in-three-minutes (3.2 min, stress, rain ambient â€” build 1, 14/14 gates)
- 23-the-calm-reset (5.5 min, stress, stream ambient â€” build 1, 14/14 gates)
- 19-release-and-restore (14.5 min, stress, garden ambient â€” build 4, 14/14 gates)
- 32-observing-emotions (9.5 min, mindfulness, garden ambient â€” build 3, 14/14 gates)

Sessions 18 and 23 are new scripts. Sessions 19 and 23 had scripts rewritten (trigger-word clean). Session 32 is a new script. All four wired into sessions.html and relevant detail/category pages.

**Gate 7 (Volume Surge) â€” most persistent failure mode:** Fish Audio's non-deterministic TTS generation causes per-chunk volume variation that triggers Gate 7 surges, particularly after long silences. Session 19 needed 4 builds, session 32 needed 3. The 9.0 dB threshold is correctly calibrated â€” rebuilding eventually produces level-consistent generations. Longer sessions with more chunks have higher failure probability. Documented in Gate 7 section.

**Character estimation overestimates duration:** The ~7.2 chars/sec formula overestimated session 32 (scripted for 12 min, TTS produced 9.5 min). The build script's own duration estimate after dry run is more reliable. Updated Section 13 table with caveat: use 7.2 chars/sec for rough planning only, set Duration-Target from dry run output.

**Garden ambient offset confirmed automated:** `-ss 10` offset now applied in both Fish and Resemble mix paths in `build-session-v3.py`. Updated non-negotiable rule 16 to reflect confirmed implementation.

**New ambient file:** `stream-extended.mp3` created for longer sessions using stream ambient.

---

### 9 February 2026 â€” Repair Trial & LALAL Removal (v3.4)

**Repair trial completed (session 32, chunk 1):**
- Defect: echo on "something" in opening chunk (composite score 0.426)
- Best-of-10 regeneration: 3 of 10 versions beat the original, 7 scored below 0.364
- Selected version (v4): combined 0.417â†’0.467, quality 0.426â†’0.490, echo risk âˆ’15%
- Splice: 100ms cosine crossfade at speechâ†’silence boundary, tonal distance 0.000443 (0.09% of threshold), very likely inaudible
- 14/14 QA gates passed on repaired file
- Repaired file uploaded to R2 as `32-observing-emotions-repair-1.mp3` â€” human A/B review confirmed echo eliminated, promoted to live same day
- Full report: `docs/repair-trial-RESULTS.md`

**Section 16A added â€” Chunk Repair Pipeline:** Documented the full repair process (when to use, step-by-step process, splice rules, trial results). Includes repair backlog of 10 flagged chunks across 5 sessions with scores and priorities. **Approved for production use** after human A/B review confirmed session 32 repair. Code authorised to run targeted best-of-10 repairs on all flagged chunks autonomously.

**LALAL.AI removed from pipeline:** Dehiss-only mode (`dereverb_enabled=False`) tested on session 25 chunk 1 (worst hiss at âˆ’7.26 dB). Result: uniform 3 dB attenuation, SNR unchanged. LALAL applies flat volume reduction, not selective denoising. All LALAL configurations now tested and failed. Architecture table updated, DO NOT APPLY list updated, status changed to DEAD.

**Hiss mitigation conclusion:** No external post-processing service can selectively remove Fish-generated hiss. The only viable strategies remain: (1) trigger word avoidance, (2) best-of-N chunk scoring, (3) ambient masking.

**QA report inspection:** 7 sessions visually inspected. Sessions 18 and 36 warrant focused listening (sibilant density / tonal shift flagged).

**Session 25 wiring fix:** Player class changed from `player` to `custom-player` + `data-src`. Commit 412a546, pushed.

**Master preservation:** 7 sessions preserved (14 WAVs), 7 chunk schedules created, 10 production records created.

**Part D added â€” Action Ledger:** New section tracking outstanding actions, decisions pending, and items requiring human input.

---

### 9 February 2026 â€” Chunk 0 Root Cause, Scoring Bias, Production Readiness (v3.5)

**Chunk 0 cold-start root cause proven:**
- Session 19 chunk 0: 30 consecutive generations across 3 text variants (original, rewrite, split) all produced echo
- Root cause: Fish cold-starts chunk 0 with no conditioning reference. Tail end of unconditioned passages degrades regardless of text content
- Words were never the problem â€” proven by elimination (same result across completely different text)
- This is NOT a trigger word issue and would not be caught by the pre-flight scan

**Split Chunk Technique (PROVEN):**
- Fix: split opening text into two short chunks. Chunk 0a is one short sentence (~40â€“60 chars), chunk 0b carries the rest
- Fish generates short sentences cleanly without conditioning â€” no time to drift
- Chunk 0b gets 0a as its conditioning reference â€” chain anchored
- Human listening confirmed split-chunk audio was clean despite scoring system flagging all 30 generations
- New mandatory script rule: opening chunk must be one short sentence under ~60 chars (Section 13)

**Scoring formula limitations â€” GENERAL PRINCIPLE (broadened 10 Feb 2026):**
- The composite metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance) systematically over-penalises unconditioned chunks
- Calibrated against mid-session chunks with conditioning context â€” chunk 0 will always score poorly
- A chunk 0 scoring âˆ’358 combined with 0.7 echo risk can sound perfectly clean
- **Automated scores must not be used for pass/fail on chunk 0. Human listening is the only reliable gate.**

**Session 19 repaired and deployed:**
- Chunk 0 split into two short chunks, remixed with correct ambient (garden, not rain as originally built)
- Code diagnosed root cause autonomously through systematic elimination: text â†’ rewrite â†’ structure

**Section 15A added â€” Production Readiness:**
- Pipeline assessed as ready for mass production of meditation sessions
- Documented: automated QA + proven repair process + characterised Fish failure modes = repeatable quality at volume
- Estimated production time: 30â€“60 minutes per session (script to live) once script is written
- Competitive position documented: no competitor has solved AI voice reliability at this level

**Pre-build checklist updated:** Opening chunk length check added as mandatory item.

---

### 9 February 2026 â€” Back-Catalogue Completion, CBT Section Planned (v3.6)

**Back-catalogue milestone:** All pre-v3 sessions rebuilt to current pipeline standard. Sessions 01, 03, 09, 38 rebuilt from scratch (previously had no master WAV or unacceptable flagged chunk rates). Phase 2 chunk repairs completed on sessions 19, 23, 32, 36. The entire deployed catalogue now runs on `build-session-v3.py` with per-chunk QA.

**Gate 10 known limitation documented:** High-silence meditation sessions (e.g., Session 01 at 87% silence) produce false positives on speech rate detection. Added as a known limitation in Gate 10 section â€” human review should override Gate 10 failures on sessions with >70% silence content.

**Fish Audio long-form ceiling formalised:** Session 09 (30 min, narrative sleep story) exhibited volume surges under Fish. New explicit guidance: sessions exceeding 20 minutes of narration content should default to Resemble. Fish can produce longer sessions but quality degrades above this threshold â€” volume inconsistencies, voice drift, and higher rebuild rates. "Best for" line updated in Section 9.

**Fish hard failure ceiling documented:** Session 36 chunk 7 failed to improve across 10 regeneration attempts (0/10 improved). New rule in Fish section and Section 16A: when a chunk fails 10 consecutive regenerations without improvement, stop retrying and escalate to human review.

**Duration header verification rule:** Three sessions required header corrections during this rebuild (01, 03, 38). Session 03 was overcorrected (set to 20 min, produced 15.4 min). New pre-build checklist item and Gate 12 note: when setting `Duration-Target` for a rebuild, cross-reference against previous build output rather than estimating from scratch.

**CBT section planned:** New dedicated CBT page approved for development. Will include guided meditation sessions built around CBT principles â€” thought defusion, cognitive restructuring, behavioural activation, and similar exercises framed as self-help practices. No clinical qualifications required for self-help content (consistent with NHS Every Mind Matters approach and existing CBT apps). Key requirements: (1) frame as "CBT-informed guided exercises," not therapy; (2) include disclaimer that these are self-help tools, not a replacement for professional support; (3) maintain the same liability positioning as Applied Psychology articles; (4) scripts require careful psychological review given the territory. Page structure, session count, and placement (standalone vs AP sub-section) to be decided.

**Pre-build checklist updated:** Duration-Target cross-reference added as mandatory item.

---


### 9 February 2026 â€” Echo Detection Investigation, Label Pipeline, Review Workflow (v3.7)

**Section 16B added â€” Echo Detection:**
- Comprehensive investigation: composite scorer, local DSP, Auphonic API, combined approach, and Whisper confidence all tested against 55 human-labelled chunks
- Core finding: Fish Audio's "echo" is a generative distortion, not acoustic reverb. No off-the-shelf echo detection tool works because the artefact has no physical echo signature
- Auphonic ruled out for echo detection (AUC 0.341 â€” anti-correlated, flags clean chunks and misses echo)
- Whisper confidence (`word_prob_p10`, Cohen's d = âˆ’0.66) shows strongest signal but insufficient data (12 ECHO examples) for predictive use
- Whisper integrated as visual cue on review page: blue border on bottom 30% chunks, filter button, badge with score
- Next steps documented: 50+ ECHO examples for Whisper revalidation, 200+ for spectrogram CNN approach
- Human ears remain the only functioning echo gate

**Label server documented:**
- `label-server.py` (localhost:8111) added to infrastructure section
- Auto-POST on every review page rating, auto-sync on page load for session 52+
- CSV storage in `reference/human-labels/` â€” labels must never require manual export
- Root file list updated to include `label-server.py`, `score-chunks-whisper.py`, `echo-detector.py`

**Human review workflow overhauled:**
- Label server start added as step 1 (auto-save, no manual exports)
- Whisper scoring added as step 4 (pre-generates confidence badges)
- Review scope rule formalised: full-chunk review mandatory until echo detector achieves <10% false negative rate across 200+ labels
- Chunk review batching documented: Scott feeds labelled data in focused ~1hr testing sessions. Pipeline must always have chunks ready for review.

**Production Readiness correction:**
- Section 15A previously claimed "The scoring system catches echo." This was disproven by human review data (58% false negative rate on echo). Corrected to state the scorer catches hiss, voice shift, and tonal inconsistency â€” not echo.

**Auphonic section updated:**
- Echo detection results added with full metrics table
- Ruled out as echo detection tool â€” anti-correlated with human perception

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


### 10 February 2026 (morning) â€” Marco Voice Vault Validated, Atempo Prohibition, Score â‰  Quality (v3.8)

**Section 16C added â€” Marco Voice Vault:**
- Vault concept validated through narrator welcome trial: 5/5 clean chunks (100%) where 14 batch builds achieved 0/14 all-clean
- Critical finding: composite score does NOT predict human-perceived quality. Cherry-pick splice (highest scores, avg 0.811) achieved only 1/5 clean. Human selection achieved 5/5.
- Vault established as the standard production method for all Salus audio. Platform target: 100+ sessions.
- Narrator welcome deployed to R2 (vault-spliced, 61.4s)

**Atempo prohibited on Fish output:**
- Testing confirmed atempo at all ratios (0.85Ã—, 0.90Ã—, 0.95Ã—) distorts Marco's voice character
- New approach: pace filtering â€” generate extra candidates and filter by natural duration range
- Added to "DO NOT APPLY" list in Section 9 and as new Production Rule 17

**Vault backup rule added (Production Rule 18)**

**Stripe webhook fix:** Edge function redeployed with `--no-verify-jwt` flag. 22 failed deliveries recovered. Deployment rule added to Section 3.

**Batch rebuild tool created:** `batch-rebuild.py` added to root file list.

### 10 February 2026 (afternoon) â€” Court of Your Mind Full-Scale Vault Pick, A/B Tournament, Gate Restructure, Script Writing for Fish (v3.9)

**Section 16C updated â€” A/B Tournament Picker validated at scale:**
- Court of Your Mind (session 52): 66 chunks, ~1,570 candidates, 199 total rejections
- 65/66 chunks picked in 1.5 hours. Average ~80 seconds per chunk. 4.5:1 ratio.
- A/B tournament replaced original PICK/X interface. Picker code preserved in full (4 files, 710 lines).
- Every pick/rejection generates labelled training data for echo detector.

**Section 13 updated â€” Script Writing for Fish structural guidelines:**
- 200 character ceiling on sentences
- Emotional weight through pacing, not dramatic vocabulary
- Break long narrative into independent clauses
- Do not stack short punchy phrases
- Closing sections simpler and shorter than body

**Section 12 updated â€” Gate system restructured for vault workflow:**
- Gates categorised into pre-vault (advisory), post-assembly (mandatory), and human (A/B tournament)
- All 14 gates still run. The change is interpretation, not execution.

**Section 9 updated â€” Fish structural performance patterns documented from production data**

**Section 8 updated â€” Rules 6 and 11 adjusted for vault workflow**

### 11 February 2026 â€” v4.1 Vault Catalogue Production Data

**Source:** Vault catalogue build debrief, 4 story session build logs (53â€“56), 7-day mindfulness course interim report, narrator welcome full build log, vault interim session report.

Changes:
- Two new Fish failure modes documented in Section 9: runaway generation (50s API ceiling) and systematic truncation (100% reproducible, requires script split)
- Opening block merge rule added to Section 9 (inverse of split-chunk technique â€” merge blocks under 40 chars)
- Production Rule 1 revised for vault world: one build per session (not one build total), concurrent multi-session builds permitted with rate-limiting caveat
- Content category filter rate benchmarks added to Section 9 with quantified data from 23 sessions and 12,793 candidates
- Progressive course difficulty scaling pattern documented (Days 5â€“7 abstract content = ~2Ã— filter rate of Days 1â€“4)
- Closing summary chunk tonal distance pattern documented
- Story session production profile documented (22â€“28% filter rate, remarkably consistent)
- R2 upload reliability data added to Section 3 (0.04% transient failure rate)
- Reject-both bug fix documented in Section 16C (commit 60396ee)
- Vault scope table updated with full catalogue data (23 sessions, 782 chunks, 12,793 candidates)
- vault-assemble.py status updated to BUILT AND TESTED in Section 16D
- Picker template mismatch workaround documented in Section 16D (generalised rebuild_full_picker.py)
- **Appendix A added: Complete A/B tournament picker source code (4 files) embedded directly in Bible â€” eliminates dependency on external debrief document**
- Ledger: L-19, L-20, L-22, L-23, L-24 moved to COMPLETE. L-14 CLOSED (won't fix). L-04 updated to PARTIAL. L-25 (human picking) and L-26 (picker integration) added.

### 11 February 2026 â€” v4.1a Hotfix: Silence Boundary Bugs

**Source:** Session 03 (Breathing for Anxiety) vault build â€” Code identified two bugs during assembly.

Changes:
- **Section 13 (Block Size): New mandatory rule â€” silence boundaries are merge barriers.** Preprocessor must never merge blocks across `[SILENCE: X]` directives, regardless of duration or block character count. Root cause: `vault-builder.py` forward merge threshold was `pause < 5`, treating `[SILENCE: 4]` breathing gaps as mergeable. Destroyed breathing rhythm in session 03.
- **Production Rule 4: Humanisation exemption for explicit `[SILENCE: X]` directives.** Breathing exercise pauses (4/5/6s inhale-hold-exhale) must be rendered at exact specified duration â€” `humanize_pauses()` Â±30% variance turns precise breathing rhythm into chaos. Ellipsis pauses still humanise normally.
- **Production Rule 4: Sleep stories â€” never humanise.** All pauses in sleep stories use `--no-humanize`. Story pacing is authored, not randomised. Stories use only explicit `[SILENCE: X]` for narrative beats and scene transitions, not ellipsis pause profiles.
- **Section 9: High-filter-rate chunks â€” scan filtered pool before regenerating.** On chunks with 70%+ filter rate, listen to filtered candidates before burning credits on regeneration. Evidence: session 38 chunk 26, v07 (filtered) was the only good candidate out of 15.
- **Section 16D: vault-assemble.py post-assembly QA gates wired.** 166 â†’ 506 lines. `run_vault_qa()` function calls all 11 mandatory gates via `build.qa_*()`. Each gate routed to correct audio stage. Gate 13 (ambient) skipped at assembly. Build report includes per-gate results. Exit code 1 on failure.
- Ledger: L-27 added (session 03 full rebuild with both fixes).

### 11 February 2026 â€” v4.1b: End-of-Chunk Truncation Fix

**Source:** Vault production observation â€” ~30% of otherwise clean candidates rejected during A/B picking due to audio clipping the final word/syllable.

Changes:
- **Section 9: New failure mode documented â€” end-of-chunk truncation.** Distinct from systematic truncation (which is 100% reproducible and requires script split). This affects individual candidates unpredictably â€” audio is clean throughout but clips prematurely at the end. ~30% waste rate of otherwise selectable candidates.
- **Section 9: "Expendable tail" padding technique documented.** Append a throwaway closing phrase to short closing chunks before generation; trim in post-processing. Applied pre-generation, not post.
- Ledger: L-28 added (vault-builder.py expendable tail implementation).

### 11 February 2026 â€” v4.1c: Hiss Trigger Words, Conditioning Chain Contamination, Production Rule 19

**Source:** Session 01 (Morning Meditation) live playback â€” massive hiss breakout from 5:10 onwards, never recovers. Root cause investigation traced to chunk 11. Vault build reverted; old single-pass build restored to live.

Changes:
- **Section 9: Hiss trigger words documented.** Certain words ("nostrils", "gentle rise", "entering") cause systematic hiss on every candidate (21/21 in session 01 chunk 11). Text-driven, not random. Fix: rewrite chunk text to avoid triggers.
- **Section 9: Conditioning chain contamination documented â€” CRITICAL.** Fish's stateless conditioning means a hissy chunk poisons every subsequent chunk in the assembled session. Invisible during A/B picking (chunks auditioned in isolation). Only manifests in assembled audio. Post-assembly sequential hiss scan required.
- **Section 13: Trigger word table updated.** Added "nostrils", "gentle rise", "entering" with hiss defect type and suggested alternatives. Table header updated with new evidence source.
- **Production Rule 19 added: No vault-assembled session deploys without post-assembly sequential HF scan.** 10-second windowed HF analysis on assembled narration, âˆ’36 dB threshold. The vault workflow broke the conditioning chain assumption that single-pass builds got for free. Session 01 is the evidence â€” vault was a step backwards, old build was clean, vault build shipped hiss.
- Ledger: L-29 added (session 01 chunk 11 rewrite + regenerate), L-30 added (post-assembly conditioning chain QA gate).

### 11 February 2026 â€” v4.0 Consolidation

**Major version bump. Consolidation of three unintegrated update briefs (v3.8, v3.9, code debrief) into the canonical Bible.**

Changes:
- v3.8 content (vault concept, atempo prohibition, pace filtering, Stripe webhook, batch rebuild) integrated into Sections 3, 8, 9, 11
- v3.9 content (A/B tournament, Fish structural patterns, script writing guidelines, gate restructure) integrated into Sections 9, 12, 13, 16
- Code debrief (vault production regulations) fully absorbed into new Section 16D
- New Section 16C: Marco Voice Vault (consolidated from v3.8 + v3.9)
- New Section 16D: Vault Production Workflow for Code (absorbed from code debrief)
- Gate system restructure preamble added to Section 12
- Fish structural performance patterns added to Section 9
- Script Writing for Fish structural guidelines added to Section 13
- Ledger updated with L-19 through L-24
- All encoding corruption fixed
- Brief lifecycle status: v3.8 â†’ INTEGRATED, v3.9 â†’ INTEGRATED, code debrief â†’ INTEGRATED

**Briefs archived:** bible-update-v3_8.md, bible-update-v3_9.md, code-debrief-vault-production.md â†’ `docs/archive/`


*Last updated: 14 February 2026 â€” v4.7: vault-assemble.py full ambient pipeline, Gate 15 Check 6 rising-RMS, HF threshold calibration, "Live" definition, iOS Safari volume fix, echo HF spike finding, v8 bugs table, vault-builder meta gotcha, governance incident. Previous: v4.6 (13 Feb) auto-picker v8, ambient pre-roll, Gate 15, session 03 rebuilt.*

---
### 12 February 2026 â€” v4.2: Auto-Picker, Ambient Mandate, Workflow Revolution

**Source:** Session debrief 12 Feb 2026, automation trial debrief (auto-picker v1â†’v7, 245 chunks, 10 sessions, 5,146+ candidates), Code gap analysis.

**Headline:** Auto-picker v7 achieved 96% pass rate on session 39, reducing human review time by ~80% (from ~2 hrs to ~45 min per session). Production workflow fundamentally changed from per-chunk A/B picking to auto-pick â†’ assemble â†’ full-audio review â†’ regen-at-timestamps.

Changes:
- **NEW Section 16E:** Auto-picker documented â€” algorithm (severity-aware + weight-swept + three-layer cutoff + pick locking), v7 configuration, validation data (24.5% exact, 59.2% top-3), critical findings (quality score doesn't predict verdict, tonal distance is strongest signal, duration/hiss weights harmful)
- **Section 16D (Vault Workflow):** Revised from 10-step manual process to 11-step auto-picker workflow. Human review shifts from per-chunk picking to full-audio review.
- **Section 2:** SÄlus macron branding added â€” 813 instances across 111 files updated from "Salus" to "SÄlus". Terminology table updated.
- **Section 3:** CDN cache purge (token, zone ID, curl command, **query string variant purging**). Verdicts API endpoint. File organisation updated with new tools (r2-upload.sh, pre-commit hook). LALAL.AI subsection removed (was already DEAD).
- **Section 7:** ASMR mobile volume slider fix. Narrator script/HTML sync issue and pre-commit hook failsafe.
- **Section 8:** 6 new Production Rules (20â€“25) â€” CDN purge, ambient mandatory with locked 30/60 fades (amended 13 Feb), 150-char split threshold, known-pass sacred, UNRESOLVABLE chunks need script fix, audio parameters locked to Bible values.
- **Section 9:** Mid-sentence conditioning for chunk 0 (proven 20/20 pass rate). Fish speaking rate corrected to 10â€“13 ch/s (was 7.2). Sleep story pause profiles added (12/35/60s). **Resemble AI removed entirely** â€” Fish is the only TTS provider. All Resemble references, routing rules, cleanup chains, and environment variables removed.
- **Section 12:** NEW Gate 15 â€” Post-deploy live material scanner (CRITICAL). Automated scan of deployed MP3 for catastrophic failures including ambient fade verification. Two failures on 12 Feb: audio breakdown undetected by 14 pre-deploy gates, and 0s ambient fade-in deployed without detection.
- **Section 16C:** A/B picker status updated (fallback, no longer primary). Rejection reason tags (Echo, Hiss, Cut Short, Voice). Solo mode fix. Score â‰  Quality strengthened with 78-verdict dataset.
- **Section 17:** Environment variables updated (Resemble/LALAL removed, CF cache purge added).
- **Ledger:** L-15â†’CLOSED (Resemble removed), L-16â†’PARTIAL, L-17â†’COMPLETE, L-27â†’COMPLETE, L-25 updated (auto-picker, 40 remaining), L-28 priority downgraded (tail detector mitigates), L-29 updated (01 redeployed). New: L-31 (reference library), L-32 (CDN purge automation), L-33 (sleep story pauses), L-34 (auto-picker rollout), L-35 (Gate 15 â€” CRITICAL), L-36 (Fish Elevated tier), L-37 (Resemble code cleanup), L-38 (remix 3 sessions with correct 30/60 fades â€” COMPLETE 13 Feb).

---

### 13 February 2026 â€” v4.6: Auto-Picker V8, Ambient Pre-Roll, Gate 15 Implemented, Session 03 Rebuilt

**Source:** Bible amendment brief (4 amendments), Auto-Picker V8 complete report (9 sessions, 6 bugs, 10 files changed).

**Headline:** Auto-picker v8 achieved 100% R1 pass on 7 of 8 automation trial sessions. Session 03 fully rebuilt (47/49 clean after 5 rechunk rounds). Gate 15 post-deploy scanner implemented. Ambient fade-in corrected from 10s to 30s and structurally defined as a pre-roll (voice delayed by fade duration). L-38 ambient remixes completed for sessions 01, 09, 53.

**Bible Amendments (4):**
1. **Ambient fade-in corrected:** 10s â†’ 30s across Section 11, Section 16D, Production Rule 21, and all references. 10s was incorrectly documented â€” 30s allows ambient to reach full level before narration starts.
2. **Session 01 opening rewritten:** "This is your morning meditation." â†’ "Good morning. You made time for yourself." Warm affirmation replaces harsh declarative. v141 picked (EXCELLENT, q=1.038, dur=3.2s).
3. **Soft opening rule added to Section 13:** First line must not be declarative or jarring. Prefer affirmations, observations, or sensory invitations. Sessions using "Theme statement" technique (03, 25, 38) flagged for review.
4. **Ambient fade-in structurally defined as pre-roll:** 30s fade-in = 30s of ambient-only audio before narrator begins. Voice delayed by fade duration. Not a volume ramp applied concurrently. Prepend silence to voice track, then mix ambient. This clarification was needed after Session 01 was deployed 3 times with voice starting at t=1s.

**Section 11 (Ambient Rules) â€” major update:**
- Structural pre-roll definition (Amendment 4)
- Voice-first loudnorm mandatory â€” loudnorm voice track BEFORE mixing ambient, no second loudnorm
- Per-source ambient gain levels documented (grace=-14dB, rain/garden=-19dB, birds=-14dB)
- Mixing method: numpy direct addition only. ffmpeg `amix` with `normalize=0` silently eats ambient signal.
- Verification checklist for every mix (pre-roll RMS, voice entry, ambient consistency, tail fade)

**Section 12 (QA Gates) â€” Gate 15 implemented:**
- `tools/gate15-post-deploy.py` (~280 lines), 7 checks, auto-runs from r2-upload.sh
- Checks: catastrophic silence, volume explosion, voice breakdown, duration sanity, hiss cascade, ambient pre-roll, ambient fade-out
- Check 1 threshold adjusted from -60dBFS to -80dBFS (48 false positives at -60)
- Check 6 false positive on correct 30s pre-roll (threshold needs adjusting â€” L-42)
- URGENT email via Resend on any failure

**Section 13 (Script Writing) â€” new rules:**
- Opening tone rule (Amendment 3): warm, invitational openings only
- Closing chunk rules: 150ms tail fade + soft multi-syllable ending words
- 4 new trigger words: pulse (echo), close/verb (hiss), soften (echo/hiss), soft lift (hiss)
- "Soft" root pattern documented: sibilant s + sustained f + t problematic for Fish
- FUZZ vs HISS distinction: different root causes, different categories in review
- Machine-readable trigger word list: `content/trigger-words.json` (17 words + 1 regex)
- Standalone scanner: `tools/trigger-word-scan.py`
- `tail_silence_ms` known limitation documented: does NOT catch Fish closing-chunk truncation

**Section 16D (Vault Workflow) â€” revised for v8:**
- Workflow updated from 11 steps to 12 steps with pre-roll and rechunk
- Assembly pipeline order mandated: voice â†’ silence â†’ loudnorm â†’ ambient â†’ MP3
- Auto-picker reference updated from v7 to v8

**Section 16E (Auto-Picker) â€” updated to v8:**
- 6 new features: `--rechunk`, `--regen-chunks`, assembly verdict loading, rechunk-history.json, pool contamination detection, trigger word pre-flight
- Validation: 68.6% exact match (up from 24.5%), 77.1% top-3 (up from 59.2%), 4.9% eliminated (down from 18.8%)
- V8 session performance table (9 sessions)
- Review page generator documented (single + top-3 modes, 830 lines)
- Auto-rebuild loop documented (`auto-rebuild-loop.py`)
- Honest assessment: rechunk loop re-rolls not learns, human review mandatory
- 3 bug fixes: pass_versions override, assembly verdict format, stale picks read

**Deployed Sessions â€” 6 updates:**
- 01: Rebuilt with new opening, 30s pre-roll, numpy mix (MD5: 82df9eb3...)
- 03: Full rebuild, 49 chunks, 47/49 clean (MD5: 94b354da...)
- 09: L-38 remix with rain -19dB, voice-first loudnorm (MD5: 7b2e02d3...)
- 38-41: V8 automation trial data added
- 52: 66/66 picked, awaiting assembly
- 53: L-38 remix with garden -19dB, voice-first loudnorm (MD5: b858fb4c...)

**Code changes:** 10 files, 1264 insertions, 1245 deletions (commit 0541bde). 3 new files: `auto-rebuild-loop.py`, `tools/trigger-word-scan.py`, `content/trigger-words.json`. 3 script updates (01, 03, 41 trigger word cleanup).

**Ledger:** L-17â†’COMPLETE, L-27â†’COMPLETE, L-35â†’COMPLETE, L-38â†’COMPLETE. New: L-39 (session 03 deferred chunks), L-40 (R2 path check), L-41 (focused review pages), L-42 (Gate 15 Check 6 fix), L-43 (vault-assemble pre-roll integration), L-44 (session 38 ambient remix).

---

### 14 February 2026 â€” v4.7: Pipeline Codification & Documentation Hardening

**Source:** Code session debrief (5 items: vault-assemble pipeline, HF threshold, Gate 15 Check 6, "Live" definition, iOS Safari volume), plus review of V8 complete report for items not yet captured (4 items: echo HF spike, v8 bugs, vault-builder meta gotcha, governance incident).

**9 additions:**

1. **Section 16D (vault-assemble.py) â€” Full ambient pipeline ownership.** vault-assemble.py now handles the entire voice â†’ ambient â†’ QA â†’ output workflow via CLI flags (`--ambient rain --fade-in 30 --fade-out 60`). Voice-first loudnorm, numpy direct addition, per-source gain table, garden 10s offset skip, verification checklist. Previously required manual ffmpeg/numpy scripts. L-43 â†’ COMPLETE.

2. **Production Rule 19 â€” HF threshold calibration note.** The -36dB threshold flags 40â€“120 windows per Fish V3-HD session (normal spectral content). Needs raising to ~-30dB or baseline comparison. Currently warning-only. L-45 added.

3. **Section 12 (Gate 15 Check 6) â€” Rising-RMS fix.** Replaced -70dBFS absolute threshold (which false-positived on every correct 30s pre-roll) with Q1-to-Q4 RMS comparison requiring â‰¥6dB rise. Validates fade-in shape, not starting level. L-42 â†’ COMPLETE.

4. **Section 16 (Deployment) â€” "Live" definition.** A session is not "live" just because its MP3 exists on R2. Requires: HTTP 200 from CDN, `data-src` reference in HTML, player element wired. ~40 sessions on R2 without HTML wiring are "available" not "live."

5. **Section 7 â€” iOS Safari `audio.volume` is read-only.** The ASMR player was broken on iPhone from launch until 14 Feb. `HTMLMediaElement.volume` is silently ignored on iOS Safari. Fix: Web Audio API GainNode via `createMediaElementSource()`. Applies to all future audio players on the site.

6. **Section 16B (Echo Detection) â€” HF spike analysis finding.** Gate 3/9 HF energy spike detection caught known echo at 41.9â€“47.6Ã— median in session 01 c07. Per-candidate `echo_risk` (autocorrelation) confirmed non-functional, but per-candidate HF spike detection is a viable next investigation.

7. **Section 16E (Auto-Picker) â€” V8 bugs fixed table.** 6 bugs documented with impact and fix: pass_versions override, assembly verdict format, R2 upload arithmetic, vault text mismatch, rechunk history persistence, stale picks read.

8. **Section 16D (Known Issues) â€” vault-builder reads meta not script.** `--regen-chunks` reads chunk text from `c{XX}_meta.json`, not from the script file. Must update meta before regen if script text has changed.

9. **Section 17 (Governance) â€” "Read the Bible Before Acting" rule.** Session 01 ambient remix incident documented: 2-minute task consumed ~4 hours because Code didn't read Section 11 before starting. Correct 6-step approach documented.

**Ledger:** L-42â†’COMPLETE (Gate 15 Check 6), L-43â†’COMPLETE (vault-assemble pipeline). New: L-45 (HF threshold calibration).

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
7. **Section 16B (Echo Detection)** — Complete rewrite. Status changed from "no detector works" to "working" (AUC 0.793). Echo fingerprint documented. Comprehensive feature family analysis (697 features tested). Operating philosophy: "replace until pass" (FPR irrelevant). Data gaps identified.
8. **Section 16B** — New subsection: Next defects roadmap (Gate 17 voice breakout, Gate 18 repeat defect, then hiss and audio fuzz).
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

**Commits this session:** `d3b2a23`, `fc8157c`, `c401a5f`, `b5a50fa`, `16e4086`.

**Ledger:** L-18→COMPLETE, L-44→COMPLETE. New: L-46 (wiring report), L-47 (verdict buttons), L-48 (Type B echo), L-49 (Gate 16 integration), L-50 (breakout detector), L-51 (compound ambient), L-52 (Gate 9 crash), L-53 (chunking merge), L-54 (S01 chunk 7 review).

### 14 February 2026 — v5.0: Full Consolidation (Gate 17, Ambient Volume Reference, Home Page Redesign)

**Source:** Gate 17 voice breakout full catalogue scan + 6 Code implementation points, ambient-volume-reference.docx, home page redesign (12 Feb chat), v4.8 integration brief.

**Headline:** V5.0 consolidation. Gate 17 voice breakout detection validated (1,721 WAVs, 237 confirmed breakouts, 51/53 sessions affected). Comprehensive ambient volume reference table replaces ad-hoc per-session levels. Home page hero card hierarchy documented. Three defect classes now identified (echo, breakout, repeat).

**Key additions:**

1. **Section 1** — Home page hero card layout: 2 flagship + 4 supporting cards, reframed statistics.
2. **Section 4** — Premium unlock gap fix documented.
3. **Section 8** — Production Rules 26 (raw narration archival) and 27 (catalogue ambient override) added.
4. **Section 11** — Complete ambient volume reference table (Grace benchmark at −14 dB, 11 ambient types with adjustments). Ceiling rule removed. Dynamic ambient parked. 6 new ambient sources added. Ambient assignment map added. Short ambient looping documented.
5. **Section 12** — Gate 16 (Echo Detection) full specification. Gate 17 (Voice Breakout Detection) full specification with catalogue scan results, two phenotypes, cold-start observation, number-word destabilisation, and 6 critical implementation notes for auto-picker integration.
6. **Section 16B** — Complete rewrite from "no detector works" to "WORKING". Echo fingerprint, classifier progression, next defects roadmap.
7. **Section 16D** — Updated per-source gain table (all 11 ambient types). Compound ambient gap, Gate 9 crash, and chunking bug documented.
8. **Section 16E** — 6 new files: remix-session.py, session-registry.json, echo-workbench.py, reference/echo-analysis/, breakout-scanner.py, reference/breakout-analysis/.
9. **Section 16F** — NEW: Voice Breakout Detection (full-catalogue scanner, two roles, known blind spots).
10. **Section 17** — Bible version sync governance rule added.
11. **Ledger** — L-50 updated (scanner validated, awaiting auto-picker integration). L-55 added (repeat defect detector). L-18, L-44 moved to COMPLETE.

**Ledger:** L-50 status updated. New: L-55 (repeat defect detector).


---


# PART D â€” LEDGER

---

## 20. Action Ledger

Outstanding actions, pending decisions, and items requiring human input. Items are added as they arise and removed when resolved. Each item has a status, source (which bible version or event created it), and owner.

### Pending Human Action

| # | Item | Source | Owner | Status |
|---|------|--------|-------|--------|
| L-01 | ~~A/B listen: session 32 repair~~ | v3.4 repair trial | Scott | **COMPLETE** â€” moved to Completed |
| L-02 | ~~**Auphonic credentials**~~ | v3.4 repair trial | Scott | **COMPLETE** â€” credits topped up, echo analysis run |
| L-03 | **Sessions 18 & 36 focused listening** â€” Visual QA flagged sibilant density (18) and tonal shift (36). Requires human listening to confirm or clear. | v3.4 QA inspection | Scott | WAITING |
| L-04 | **Narration audit** â€” Full audit of all deployed sessions to populate cross-session registers (openings, closings, phrases). Registers now exist with 22 openings, 22 closings, and 90+ phrases from the 7-day course. Still needs retrospective population from all other deployed sessions. | v3.2 | Scott/Code | PARTIAL â€” registers created, retrospective population outstanding |

### Pending Technical Decision

| # | Item | Source | Owner | Status |
|---|------|--------|-------|--------|
| L-05 | **Session 25: repair or rebuild?** â€” 4 flagged chunks including opening (worst hiss at âˆ’7.26 dB). Individual repair may not be efficient â€” full rebuild likely better value. Code can now run repairs autonomously. | v3.4 repair backlog | Scott | OPEN |
| L-06 | ~~Repair pipeline approval~~ | v3.4 | Scott | **COMPLETE** â€” moved to Completed |
| L-07 | ~~"Something" as trigger word?~~ â€” Session 19 chunk 0 root cause analysis proved the issue was chunk 0 cold-start, not word-level triggers. 30 generations across different text all produced echo. Deprioritised. | v3.4 repair trial | Scott | **CLOSED** â€” not a trigger word issue |
| L-11 | ~~Catalogue repair run~~ | v3.4 | Code | **COMPLETE** â€” moved to Completed |
| L-13 | ~~Retroactive chunk extraction~~ | v3.5 | Code | **COMPLETE** â€” superseded by v3 rebuilds |
| L-14 | ~~**Scoring formula recalibration**~~ â€” Evidence from 12,793 candidates across 23 sessions confirms scoring is a useful pre-filter but fundamentally cannot replace human ears. Filter rates vary 12â€“36% by content type regardless of calibration. The vault + A/B picker workflow makes this a non-issue. | v3.5 | Scott/Code | **CLOSED** â€” superseded by vault workflow |
| L-12 | **Test run on new material** â€” Next new session build should use best-of-10 as standard for all chunks (not just focused chunks), with the repair pipeline standing by for any flagged chunks post-build. Validates end-to-end quality on fresh content. | v3.4 | Scott/Code | WAITING |
| L-15 | ~~Session 09 Resemble evaluation~~ â€” Resemble removed from pipeline entirely (12 Feb 2026). Session 09 redeployed via auto-picker with grace ambient. | v3.6 | â€” | **CLOSED** |
| L-16 | **CBT section development** â€” New dedicated page with CBT-informed guided meditation sessions. Requires: page design, session scripting (thought defusion, cognitive restructuring, behavioural activation), disclaimer text, placement decision (standalone vs AP sub-section). First CBT scripts should go through the standard pipeline with extra attention to psychological accuracy. | v3.6 | Scott/Code | OPEN |
| L-17 | ~~**Session 03 rebuild**~~ â€” Full rebuild via auto-picker v8 (13 Feb). 49 chunks, 2,974 candidates, 5 rechunk rounds, 47/49 clean. 2 stubborn chunks deferred (c09 CUTOFF pool exhausted, c14 ECHO/VOICE contaminated). | v3.7 | Scott/Code | **COMPLETE** â€” moved to Completed |
| L-19 | ~~**Vault builder development**~~ | v3.8 | Scott/Code | **COMPLETE** â€” moved to Completed |
| L-20 | ~~**Script pre-processing for vault**~~ | v3.8 | Code | **COMPLETE** â€” moved to Completed |
| L-21 | **Script recovery** â€” Recover or reconstruct scripts for 6 deployed sessions not in the current inventory (05, 06, 07, 08, 11, 29). Reconstruct from transcripts, build manifests, or R2 audio if originals cannot be found. | v3.8 | Code | OPEN |
| L-22 | ~~**vault-assemble.py build**~~ | v3.9 | Code | **COMPLETE** â€” moved to Completed |
| L-23 | ~~**Full catalogue vault rebuild**~~ | v3.9 | Scott/Code | **COMPLETE** â€” moved to Completed |
| L-24 | ~~**A/B tournament picker generalisation**~~ | v3.9 | Code | **COMPLETE** â€” moved to Completed |
| L-25 | **Human A/B picking â€” 23 sessions** â€” All 23 picker pages live on R2. Estimated ~32 hours of picking work across 782 chunks. Pick at own pace, batched into ~1hr sessions. Keyboard shortcuts: A/B/S for decisions, arrow keys for navigation. After picks complete per session: run `vault-assemble.py`, post-assembly QA, human end-to-end listen, then deploy. | v4.1 | Scott | OPEN |
| L-26 | **vault-builder.py picker integration** â€” Update `generate_picker_html()` to embed the A/B tournament code directly or call `rebuild_full_picker.py` automatically, eliminating the two-step workaround. | v4.1 | Code | OPEN |
| L-27 | ~~**Session 03 full rebuild (breathing silence bugs)**~~ â€” Full rebuild completed 13 Feb via auto-picker v8. Both bugs fixed (silence boundary merging + humanize_pauses). 49 chunks, 5 rounds, 47/49 clean. c09/c14 deferred for `--regen-chunks` in future. | v4.1a | Code | **COMPLETE** â€” moved to Completed |
| L-18 | ~~**Echo detector revalidation**~~ | v3.7 | Scott/Code | **COMPLETE** — Gate 16 achieves AUC 0.793 on 70 echo + 34 clean chunks across 6 sessions. Supersedes Whisper confidence approach. |
| L-28 | **Expendable tail padding in vault-builder.py** â€” Implement pre-generation padding for chunks ending in short closing phrases. Append throwaway phrase (e.g. "Right here. Right now.") before Fish generation, trim from audio in post-processing. Eliminates ~30% candidate waste from end-of-chunk truncation. | v4.1b | Code | OPEN |
| L-29 | **Session 01 chunk 11 rewrite + regenerate** â€” All 21 candidates have hiss (HF âˆ’34.6 to âˆ’14.7 dB). Text triggers: "nostrils", "gentle rise", "entering". Rewrite chunk text to avoid trigger words, regenerate candidates, re-pick, reassemble. Downstream chunks should recover once conditioning chain source is clean. Vault build reverted; old single-pass build restored to live. | v4.1c | Code | OPEN |
| L-30 | **Post-assembly conditioning chain QA gate** â€” Add sequential hiss scan to vault-assemble.py post-assembly QA. Windowed HF analysis (e.g. 10s windows) across assembled audio to detect conditioning chain contamination that isolated chunk A/B picking cannot catch. Current QA gates run per-chunk; this gap allowed session 01 hiss cascade to reach production. | v4.1c | Code | OPEN |

### Completed (Recent)

| # | Item | Source | Resolved | Notes |
|---|------|--------|----------|-------|
| L-18 | Echo detector revalidation | v3.7 | 14 Feb 2026 | Gate 16 achieves AUC 0.793 on 70 echo + 34 clean chunks across 6 sessions. Supersedes Whisper confidence approach. |
| L-44 | Session 38 ambient remix | v4.6 | 14 Feb 2026 | Included in batch of 53 sessions remixed with correct catalogue ambients + 30s pre-roll. |
| L-42 | Gate 15 Check 6 threshold fix | v4.6 | 14 Feb 2026 | Replaced -70dBFS absolute threshold with rising-RMS Q1-to-Q4 check (â‰¥6dB rise required). |
| L-43 | vault-assemble.py pre-roll integration | v4.6 | 14 Feb 2026 | Full ambient pipeline codified: `--ambient`, `--fade-in`, `--fade-out` flags. Voice-first loudnorm, numpy mixing, per-source gain, verification checklist. Single-command end-to-end. |
| L-35 | Post-deploy live audio scanner (Gate 15) | v4.2 | 13 Feb 2026 | `tools/gate15-post-deploy.py` (~280 lines). 7 checks, auto-runs from r2-upload.sh. URGENT email on failure. Check 6 threshold issue noted (L-42). |
| L-38 | Remix 3 deployed sessions with correct ambient fades | v4.5 | 13 Feb 2026 | Sessions 01, 09, 53 remixed with 30s pre-roll, 60s fade-out, voice-first loudnorm, numpy mix. CDN purged, MD5 verified. |
| L-17 | Session 03 rebuild | v3.7 | 13 Feb 2026 | Full rebuild via auto-picker v8. 49 chunks, 2,974 candidates, 5 rechunk rounds, 47/49 clean (95.9%). 2 stubborn chunks deferred to L-39. |
| L-27 | Session 03 full rebuild (breathing silence bugs) | v4.1a | 13 Feb 2026 | Both bugs fixed. Full rebuild completed with correct chunk boundaries. |
| L-19 | Vault builder development | v3.8 | 11 Feb 2026 | `vault-builder.py` operational. 23 sessions built across full catalogue. Candidate generation, R2 upload, metadata commit, picker generation all functional. |
| L-20 | Script pre-processing for vault | v3.8 | 11 Feb 2026 | 5 scripts fixed (19, 23, 32, 36, 38). Merges and splits applied automatically during vault-builder preprocessing. |
| L-22 | vault-assemble.py build | v3.9 | 11 Feb 2026 | Built and tested. 328 lines. Session 52 assembled (66/66 chunks). Narrator welcome assembled (5/5 chunks, 3 builds). |
| L-23 | Full catalogue vault rebuild | v3.9 | 11 Feb 2026 | 23 sessions, 12,793 candidates, Â£2.70â€“Â£4.52 total cost. All picker pages live on R2. Awaiting human picks. |
| L-24 | A/B tournament picker generalisation | v3.9 | 11 Feb 2026 | `rebuild_full_picker.py` generalised â€” accepts any session ID, reads from `tools/vault-picker/`, `{{SESSION_ID}}` placeholders. Tested on all 23 sessions. |
| L-14 | Scoring formula recalibration | v3.5 | 11 Feb 2026 | Closed (won't fix). 12,793 candidates confirm scoring is a pre-filter, not a quality gate. Vault + A/B picker workflow supersedes. |
| L-01 | A/B listen: session 32 repair | v3.4 repair trial | 9 Feb 2026 | Echo on "something" eliminated. Significant improvement confirmed. Repaired file promoted to live. |
| L-06 | Repair pipeline approval | v3.4 | 9 Feb 2026 | Approved for production use. Code authorised to run best-of-10 repairs on all flagged chunks autonomously. |
| L-07 | "Something" as trigger word? | v3.4 | 9 Feb 2026 | Closed â€” session 19 proved chunk 0 issue is cold-start, not word-level triggers. |
| L-08 | LALAL dehiss-only test | v3.1 | 9 Feb 2026 | Failed â€” uniform attenuation, not selective. LALAL removed from pipeline. |
| L-09 | Session 25 wiring fix | v3.3 | 9 Feb 2026 | Commit 412a546. Player class corrected. |
| L-10 | Master narration preservation | v3.4 brief | 9 Feb 2026 | 7 sessions, 14 WAVs, 10 production records. |
| L-11 | Catalogue repair run | v3.4 | 9 Feb 2026 | All 4 unscored sessions rebuilt to v3 standard. Phase 2 repairs deployed. Session 36 chunk 7 = Fish hard failure (0/10). |
| L-13 | Retroactive chunk extraction | v3.5 | 9 Feb 2026 | Superseded by full v3 rebuilds â€” all sessions now have per-chunk scoring data. |
| L-02 | Auphonic credentials | v3.4 | 9 Feb 2026 | Credits topped up. Auphonic echo analysis run on full labelled dataset. Ruled out for echo detection (AUC 0.341). |


| L-31 | **Curated chunk 0 reference library** â€” Replace `MARCO_MASTER_WAV` fallback with 3â€“5 proven Fish-generated chunks from deployed sessions. Mid-sentence conditioning achieved 20/20 pass rate vs ~60% with marco-master. | v4.2 | Code | OPEN |
| L-32 | **Automate CDN cache purge in deploy workflows** â€” Integrate purge into vault-assemble.py deploy step, `cpd` shortcut, and any R2 upload script. | v4.2 | Code | OPEN |
| L-33 | **Sleep story pause profile** â€” Add `sleep-story` category to PAUSE_PROFILES in vault-builder.py (12/35/60s). Override when Category=story AND Duration-Target > 20 min. Evidence: session 53 required manual pause scaling. | v4.2 | Code | OPEN |
| L-34 | **Auto-picker production rollout** â€” Run auto-picker v7 across remaining 40 vault sessions. Establish verdict history per session through iterative review rounds. Target: all 54 sessions deployed within ~30 hours of human review (down from ~58 hours with A/B picking). | v4.2 | Scott/Code | OPEN |
| L-35 | ~~**Post-deploy live material scanner (Gate 15)**~~ â€” Implemented 13 Feb. `tools/gate15-post-deploy.py` (~280 lines), 7 checks, auto-runs from `tools/r2-upload.sh`. URGENT email via Resend on failure. Check 6 threshold needs adjustment for 30s pre-roll (false positive on correct sessions). | v4.2 | Code | **COMPLETE** â€” moved to Completed |
| L-36 | **Fish Elevated tier confirmation** â€” Fish Audio account upgraded to Elevated tier (15 concurrent connections). Vault-builder.py `MAX_CONCURRENT` updated from 5 to 15. Total generation cost for session 01 trial: ~Â£116.69. | v4.2 | Scott | OPEN |
| L-37 | **Resemble AI removal cleanup** â€” Remove all Resemble references from codebase: `build-session-v3.py` Resemble paths, environment variable references, provider routing logic, and Resemble-specific cleanup chains. | v4.2 | Code | OPEN |
| L-38 | ~~**Remix 3 deployed sessions with correct ambient fades**~~ â€” Sessions 01, 09, 53 remixed with 30s structural pre-roll / 60s fade-out, voice-first loudnorm, numpy mix. All three deployed 13 Feb with CDN purge and MD5 verification. | v4.5 | Code | **COMPLETE** â€” moved to Completed |
| L-39 | **Session 03 deferred chunks (c09, c14)** â€” c09: `--regen-chunks 9 --count 50` + script review ("And breathe out through your mouth. Let it all go." â€” CUTOFF, pool exhausted). c14: `--regen-chunks 14 --count 50` or script micro-rewrite ("Good. You're already doing something kind for yourself." â€” ECHO/VOICE, contaminated). | v4.6 | Code | OPEN |
| L-40 | **R2 path consistency check** â€” Pre-deploy script that verifies HTML `data-src` path matches R2 upload key. Session 03 deployed to `content/audio-free/03-breathing-for-anxiety.mp3` but HTML referenced `content/audio/03-breathing-for-anxiety-vault-ambient.mp3`. Must be automated. | v4.6 | Code | OPEN |
| L-41 | **Focused review pages for rechunk rounds** â€” Integrate into review-page-generator.py as `--mode rechunk --chunks 9,14` so rechunk rounds R4+ only show changed chunks, not the full session. Saves human time. | v4.6 | Code | OPEN |
| L-42 | ~~**Gate 15 Check 6 threshold fix**~~ â€” Implemented 14 Feb. Replaced -70dBFS absolute threshold with rising-RMS check: Q1-to-Q4 RMS must rise by at least 6dB across the pre-roll. Validates fade-in shape, not starting level. | v4.6 | Code | **COMPLETE** |
| L-43 | ~~**vault-assemble.py pre-roll integration**~~ â€” Implemented 14 Feb. vault-assemble.py now owns full ambient pipeline: `--ambient rain --fade-in 30 --fade-out 60`. Voice-first loudnorm, numpy direct addition, per-source gain table, garden 10s offset skip, verification checklist. Single-command end-to-end. | v4.6 | Code | **COMPLETE** |
| L-44 | ~~**Session 38 ambient remix**~~ | v4.6 | Code | **COMPLETE** — included in batch of 53 sessions remixed with correct catalogue ambients + 30s pre-roll. |
| L-45 | **Production Rule 19 HF threshold calibration** â€” Current -36dB threshold flags 40-120 windows per Fish V3-HD session (normal spectral content, not contamination). Raise to ~-30dB or compare against Fish baseline rather than absolute silence. Currently warning-only but noisy. | v4.7 | Code | OPEN |
| L-46 | **Post-deploy wiring report** — remix/deploy tool should generate a wiring report listing sessions on R2 that lack `data-src` references in any HTML page. Broader than L-40. Evidence: 19 sessions found disconnected in wiring audit. | v4.8 | Code | OPEN |
| L-47 | **Review page verdict buttons** — A/B picker review pages capture version preferences but NOT defect labels (ECHO/CLEAN/HISS/VOICE). Add verdict buttons. Target: 150+ labelled chunks across 10+ sessions. | v4.8 | Code | OPEN |
| L-48 | **Type B "quiet echo" investigation** — 29% FNR from echo with intact band correlation (corr_range < 0.030). Needs different features or more data. Options: temporal analysis, neural embeddings, or accept and rely on human review. | v4.8 | Scott/Code | OPEN — research |
| L-49 | **Gate 16 integration into auto-picker** — Replace `echo_risk` (spectral flux variance) with Gate 16 z-score composite. Use high-recall operating point. Threshold: z-score > 0.4 = penalty, > 2.5 = elimination. Classifier config in `reference/echo-analysis/classifier_config.json`. | v4.8 | Code | OPEN |
| L-50 | **Gate 17 integration into auto-picker** — Voice breakout scanner validated on 1,721 WAVs with 237 confirmed breakouts. Needs wiring into auto-picker following Gate 16 pattern. Must score ALL candidates (not just picked versions). Must use catalogue-wide baselines from `breakout_scan_results.json` (never recompute per session). | v4.8/v5.0 | Code | OPEN — scanner validated, awaiting integration |
| L-51 | **Compound ambient support in vault-assemble.py** — `find_ambient_file()` does not support "+" syntax. Sessions 40, 59, 62, 72 require `remix-session.py` instead. Add "+" parsing or mandate remix tool for compounds. | v4.8 | Code | OPEN |
| L-52 | **Gate 9 KeyError crash** — `vault-assemble.py` crashes in Gate 9 (visual report) with `KeyError: 'time'` on energy spike flags. Non-blocking but prevents QA completion. Bug in `build-session-v3.py` line 2768. | v4.8 | Code | OPEN |
| L-53 | **Chunking bug: silence marker merge safety rule** — Add rule to `preprocess_blocks()`: never merge blocks with `...` silence markers between them, regardless of character count. Evidence: S01 chunk 7. | v4.8 | Code | OPEN |
| L-54 | **S01 chunk 7 repair review** — Awaiting human review of the silence-corrected chunk 7 (13.5s → 68.4s, session 14.1 → 15.1 min). | v4.8 | Scott | WAITING |
| L-55 | **Repeat defect detector (future Gate 18)** — Fish generating words/phrases twice. 4 confirmed instances found during Gate 17 breakout scan. Spectral features won't catch these. Needs Whisper transcription comparison against input text. Separate from echo (Gate 16) and breakout (Gate 17). | v5.0 | Scott/Code | OPEN — research |

### Ledger Rules

1. **New items get the next L-number.** Numbers are never reused.
2. **Items move to Completed when resolved,** with the resolution date and a brief note.
3. **BLOCKED items** list which other item they depend on.
4. **The ledger is maintained by Claude Desktop** as part of bible updates. Code does not write to the ledger.
5. **Scott reviews the ledger** at the start of each work session to decide priorities.

---

## Document Governance

**Owner:** Scott (via Claude Desktop â€” Scott's conversational Claude instance)
**Consumers:** Claude Code, any future contributors

This document is maintained by Claude Desktop on Scott's behalf. Claude Code reads it as a reference but **must not edit, append to, or modify it under any circumstances.** If Code identifies an error, omission, or outdated information, it must report the issue and wait â€” not fix it.

Changes to this document follow this workflow:
1. Scott or Claude Desktop identifies needed change
2. Claude Desktop drafts the update
3. Scott approves
4. Claude Desktop produces the updated bible
5. Code receives the new version via brief

This separation exists because Code previously both wrote and read the bible, leading to contradictions, self-certified completions, and unauthorised pipeline modifications. The contractor does not amend the specification.

**Note (14 Feb 2026 — v5.0):** This version consolidates the v4.8 integration brief (18 changes), the ambient volume reference document, the home page redesign, and the Gate 17 voice breakout detection breakthrough into the canonical Bible. Section 16F (Voice Breakout Detection) is new. The document now covers three defect detection gates (Gate 15 post-deploy, Gate 16 echo, Gate 17 breakout) and identifies a fourth defect class (repeat) for future investigation.

**Note (8 Feb 2026):** Code edited this document directly during the 8 Feb session. The edits were largely accurate but introduced governance conflicts and contradicted existing non-negotiable rules. This corrected version (v2.2c) restores Desktop ownership and resolves those conflicts. All future Bible edits go through the workflow above.

---

# APPENDIX

---

## Appendix A: A/B Tournament Picker â€” Complete Source Code

**Status:** PRODUCTION â€” validated on 23 sessions. This code is the authoritative reference.
**On disk:** `tools/vault-picker/` (4 files)
**Warning:** This code took 6â€“7 error iterations to reach its working state. Bugs were subtle (version 0 falsy comparisons, saveState exceptions blocking renders, tournament bracket requiring 4 clicks instead of 1, "reject both" semantics wrong). Do not rebuild from description â€” use this code directly.

### File 1: `ab_picker_css.txt` (64 lines â€” complete styling)

```css
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a12;color:#f0eefc;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:32px 20px;max-width:900px;margin:0 auto}
h1{font-size:1.3rem;font-weight:300;margin-bottom:4px}
.meta{font-size:.78rem;color:#888;margin-bottom:6px}
.save-status{font-size:.72rem;padding:3px 10px;border-radius:4px;margin-bottom:8px;display:inline-block}
.save-status.ok{background:rgba(52,211,153,.1);color:#34d399}
.save-status.saving{background:rgba(250,204,21,.1);color:#facc15}
.save-status.error{background:rgba(239,68,68,.1);color:#ef4444}
.progress{font-size:.82rem;color:#34d399;margin-bottom:16px}
.chunk-nav{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:20px;padding:12px;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:8px}
.chunk-nav button{width:36px;height:28px;border-radius:4px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:#888;cursor:pointer;font-size:.68rem;transition:all .15s}
.chunk-nav button:hover{background:rgba(255,255,255,.08);color:#f0eefc}
.chunk-nav button.picked-old{background:rgba(52,211,153,.15);border-color:rgba(52,211,153,.3);color:#34d399;font-weight:400}
.chunk-nav button.rejected{background:rgba(239,68,68,.25);border-color:#ef4444;color:#ef4444;font-weight:700}
.chunk-nav button.picked-a{background:#34d399;border-color:#34d399;color:#0a0a12;font-weight:700}
.chunk-nav button.picked-b{background:#f59e0b;border-color:#f59e0b;color:#0a0a12;font-weight:700}
.chunk-nav button.has-reject{background:rgba(239,68,68,.15);border-color:rgba(239,68,68,.3);color:#ef4444}
.chunk-nav button.current{outline:2px solid #f0eefc;outline-offset:1px}
.pick-toast{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) scale(0.8);background:#0f2a20;color:#34d399;border:2px solid #34d399;padding:20px 48px;border-radius:14px;font-size:1.3rem;font-weight:700;z-index:9999;pointer-events:none;opacity:0;transition:opacity .15s,transform .15s}
.pick-toast.show{opacity:1;transform:translate(-50%,-50%) scale(1)}
.pick-toast.reject{background:#2a0f0f;color:#ef4444;border-color:#ef4444}
.ab-header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px}
.ab-title{font-size:1rem;font-weight:500;color:#34d399}
.ab-badge{font-size:.72rem;padding:2px 8px;border-radius:4px;background:rgba(167,139,250,.12);color:#a78bfa}
.ab-text{font-size:.85rem;color:#999;font-style:italic;margin-bottom:14px;line-height:1.5}
.ab-notes{width:100%;padding:6px 10px;margin-bottom:14px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:6px;color:#ccc;font-size:.78rem;resize:vertical;min-height:28px}
.ab-notes::placeholder{color:#555}
.round-info{font-size:.78rem;color:#888;margin-bottom:12px;text-align:center}
.ab-compare{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.ab-side{padding:16px;background:rgba(255,255,255,.02);border:2px solid rgba(255,255,255,.08);border-radius:10px;text-align:center;transition:border-color .2s}
.ab-side:hover{border-color:rgba(255,255,255,.15)}
.ab-label{font-size:1.4rem;font-weight:700;margin-bottom:8px;letter-spacing:2px}
.ab-label.label-a{color:#60a5fa}
.ab-label.label-b{color:#f59e0b}
.ab-stats{font-size:.72rem;color:#777;margin-top:8px}
.ab-stats span{margin:0 6px}
.ab-stats .score{color:#34d399}
.ab-stats .dur{color:#a78bfa}
.ab-stats .tone{color:#f59e0b}
.ab-side audio{width:100%;margin:8px 0}
.ab-actions{display:flex;justify-content:center;gap:12px;margin-bottom:20px}
.ab-actions button{padding:10px 28px;border-radius:8px;border:2px solid;font-size:.9rem;font-weight:600;cursor:pointer;transition:all .15s}
.btn-a{background:rgba(96,165,250,.1);border-color:rgba(96,165,250,.3);color:#60a5fa}
.btn-a:hover{background:rgba(96,165,250,.2)}
.btn-same{background:rgba(255,255,255,.04);border-color:rgba(255,255,255,.12);color:#888}
.btn-same:hover{background:rgba(255,255,255,.08)}
.btn-b{background:rgba(245,158,11,.1);border-color:rgba(245,158,11,.3);color:#f59e0b}
.btn-b:hover{background:rgba(245,158,11,.2)}
.ab-result{text-align:center;padding:24px;background:rgba(52,211,153,.04);border:1px solid rgba(52,211,153,.15);border-radius:10px;margin-bottom:16px}
.ab-result .winner-label{font-size:1rem;color:#34d399;margin-bottom:8px}
.ab-result audio{width:80%;margin:10px 0}
.ab-result .winner-stats{font-size:.78rem;color:#888;margin-bottom:12px}
.btn-repick{padding:6px 16px;border-radius:6px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);color:#f0eefc;cursor:pointer;font-size:.78rem}
.btn-repick:hover{background:rgba(255,255,255,.08)}
.shortcuts{font-size:.72rem;color:#555;text-align:center;margin-top:12px}
.shortcuts kbd{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:3px;padding:1px 5px;font-family:inherit}
.export-bar{margin-top:36px;display:flex;gap:10px;align-items:center}
.export-bar button{padding:8px 20px;border-radius:7px;border:1px solid rgba(52,211,153,.3);background:rgba(52,211,153,.1);color:#34d399;cursor:pointer;font-size:.82rem;font-weight:500}
.export-bar button:hover{background:rgba(52,211,153,.18)}
.export-bar .status{font-size:.78rem;color:#888}
.summary{margin-top:16px;padding:14px;background:rgba(52,211,153,.04);border:1px solid rgba(52,211,153,.12);border-radius:8px;display:none}
.summary pre{white-space:pre-wrap;color:#ccc;font-size:.75rem}
</style>```

### File 2: `ab_picker_html.txt` (16 lines â€” page structure)

Template placeholders: `{{SESSION_ID}}` is replaced by `rebuild_full_picker.py` at build time.

```html
<h1>Vault Picker &mdash; {{SESSION_ID}}</h1>
<p class="meta">A/B Tournament v2</p>
<p class="meta">Audio base: <input id="basePath" value="https://media.salus-mind.com/vault/{{SESSION_ID}}" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:4px;color:#f0eefc;padding:2px 6px;font-size:.72rem;width:420px" onchange="updateBasePath()"></p>
<div class="save-status ok" id="saveStatus">Auto-save active</div>
<div class="progress" id="progress">0 / 0 picked</div>
<div class="chunk-nav" id="chunkNav"></div>
<div id="abArea"></div>
<div class="pick-toast" id="toast"></div>
<div class="export-bar">
  <button onclick="exportPicks()">Download picks.json</button>
  <button onclick="exportTxt()">Download TXT</button>
  <button onclick="playAllPicks()" id="btnPlayAll">Play All Picks</button>
  <span class="status" id="exportStatus"></span>
</div>
<div class="summary" id="summaryBox"><pre id="summaryJson"></pre></div>
<div id="debugLog" style="margin-top:16px;font-size:.7rem;color:#555;font-family:monospace"></div>```

### File 3: `ab_picker_js.js` (525 lines â€” full A/B tournament engine)

Core logic: state management, merge server+localStorage, pick/reject/auto-advance, keyboard shortcuts (A/B/S/arrows), export (JSON/TXT), play-all, save-remote.

**Key implementation details:**
- `try/catch` on every `saveState()` call â€” rendering must always happen even if save fails
- `pickCounter` tracks total decisions made (debug)
- `pickedThisSession` tracks which side (a/b) won for colour-coding the nav grid (green = A, amber = B, muted green = from previous session)
- Toast notifications â€” green for picks, appears centred on screen for 900ms
- Flash animation on the compare area when new pair loads (opacity 0.5 â†’ 1.0)
- Keyboard shortcuts skip textarea/input â€” won't fire when typing notes
- Audio base path is editable â€” the input field at the top allows changing the R2 URL base without rebuilding
- Reject-both stays on current chunk and loads next pair (fixed commit 60396ee)

```javascript
// --- A/B Tournament Picker v2 (fixed: try/catch save, green toasts, version labels) ---
var PICKS_API = 'https://vault-picks.salus-mind.com';
var AUTH_TOKEN = 'salus-vault-2026';
var basePath = document.getElementById('basePath').value.replace(/\/+$/, '');
var initialState = {};
var abState = {};
var currentChunkArrayIdx = 0;
var pickCounter = 0;
var pickedThisSession = {}; // chunkIdx -> 'a' or 'b'

// --- Load state: MERGE remote + localStorage ---
async function loadState() {
  var serverState = {}, localState = {};
  try {
    if (PICKS_API && AUTH_TOKEN) {
      var resp = await fetch(PICKS_API + '/picks/' + SESSION_ID, {
        headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN }
      });
      if (resp.ok) {
        var data = await resp.json();
        if (data.picks && data.picks.length > 0) {
          for (var i = 0; i < data.picks.length; i++) {
            var p = data.picks[i];
            serverState[p.chunk] = { picked: p.picked, rejected: p.rejected || [], notes: p.notes || '', side: p.side || null };
          }
        }
      }
    }
  } catch (e) { console.warn('Remote load failed:', e); }

  try {
    var saved = localStorage.getItem('vault-picks-' + SESSION_ID);
    if (saved) localState = JSON.parse(saved);
  } catch (e) { console.warn('localStorage parse failed:', e); }

  initialState = {};
  var serverKeys = Object.keys(serverState);
  var localKeys = Object.keys(localState);
  var allKeys = {};
  for (var i = 0; i < serverKeys.length; i++) allKeys[serverKeys[i]] = true;
  for (var i = 0; i < localKeys.length; i++) allKeys[localKeys[i]] = true;

  var keys = Object.keys(allKeys);
  for (var i = 0; i < keys.length; i++) {
    var k = keys[i];
    var s = serverState[k] || {};
    var l = localState[k] || {};
    if (l.picked != null) initialState[k] = l;
    else if (s.picked != null) initialState[k] = s;
    else initialState[k] = ((s.rejected || []).length >= (l.rejected || []).length) ? s : l;
  }

  var src = serverKeys.length > 0 && localKeys.length > 0 ? 'Merged server+local' :
    serverKeys.length > 0 ? 'Loaded from server' :
    localKeys.length > 0 ? 'Loaded from localStorage' : 'No saved state';
  setSaveStatus('ok', src);
  logDebug('loadState: ' + keys.length + ' chunks loaded (' + src + ')');
}

function setSaveStatus(cls, text) {
  var el = document.getElementById('saveStatus');
  if (el) { el.className = 'save-status ' + cls; el.textContent = text; }
}

function logDebug(msg) {
  var el = document.getElementById('debugLog');
  if (el) el.textContent = msg;
  console.log('[picker] ' + msg);
}

function updateBasePath() {
  basePath = document.getElementById('basePath').value.replace(/\/+$/, '');
  renderChunk();
}

// --- All non-filtered candidates sorted by score (fallback: all if every candidate filtered) ---
function getTop(chunk) {
  var result = [];
  for (var i = 0; i < chunk.candidates.length; i++) {
    if (!chunk.candidates[i].filtered) result.push(chunk.candidates[i]);
  }
  if (result.length === 0) {
    for (var i = 0; i < chunk.candidates.length; i++) {
      result.push(chunk.candidates[i]);
    }
  }
  result.sort(function(a, b) { return b.score - a.score; });
  return result;
}

// --- Initialize tournament state ---
function initABState(chunkIdx, reset) {
  var chunk = null;
  for (var i = 0; i < chunkData.length; i++) {
    if (chunkData[i].idx === chunkIdx) { chunk = chunkData[i]; break; }
  }
  if (!chunk) return;

  var top5 = getTop(chunk);
  if (top5.length === 0) return;

  var saved = reset ? {} : (initialState[chunkIdx] || {});
  var notes = (abState[chunkIdx] && abState[chunkIdx].notes) || saved.notes || '';

  // If previously picked and not resetting
  if (!reset && saved.picked != null) {
    abState[chunkIdx] = { top5: top5, winner: saved.picked, rejected: saved.rejected || [], done: true, notes: notes, round: 0, side: saved.side || null };
    if (saved.side) pickedThisSession[chunkIdx] = saved.side;
    return;
  }

  var rejected = reset ? [] : (saved.rejected || []);
  var available = [];
  for (var i = 0; i < top5.length; i++) {
    if (rejected.indexOf(top5[i].v) === -1) available.push(top5[i]);
  }

  if (available.length === 0) {
    // All rejected â€” full reset
    abState[chunkIdx] = { top5: top5, champion: top5[0], challengerIdx: 1, winner: null, rejected: [], done: false, notes: notes, round: 1 };
  } else if (available.length === 1) {
    abState[chunkIdx] = { top5: top5, winner: available[0].v, rejected: rejected, done: true, notes: notes, round: 0 };
  } else {
    var challIdx = -1;
    for (var i = 0; i < top5.length; i++) {
      if (top5[i] === available[1]) { challIdx = i; break; }
    }
    abState[chunkIdx] = { top5: top5, champion: available[0], challengerIdx: challIdx, winner: null, rejected: rejected, done: false, notes: notes, round: 1 };
  }
}

// --- Render current chunk ---
function renderChunk() {
  var chunk = chunkData[currentChunkArrayIdx];
  var state = abState[chunk.idx];
  var area = document.getElementById('abArea');
  if (!area) { logDebug('ERROR: no abArea element'); return; }
  if (!state) { area.innerHTML = '<p style="color:#ef4444">No candidates for chunk ' + chunk.idx + '</p>'; return; }

  var html = '';
  html += '<div class="ab-header">';
  html += '<span class="ab-title">Chunk ' + chunk.idx + '</span>';
  html += '<span class="ab-badge">' + chunk.chars + ' chars' + (chunk.isOpening ? ' \u00b7 opening' : '') + (chunk.isClosing ? ' \u00b7 closing' : '') + '</span>';
  html += '</div>';
  html += '<div class="ab-text">\u201c' + chunk.text + '\u201d</div>';
  html += '<textarea class="ab-notes" id="notes-' + chunk.idx + '" placeholder="Notes..." oninput="updateNotes(' + chunk.idx + ')">' + (state.notes || '') + '</textarea>';

  if (state.done && state.winner != null) {
    // Winner display
    var w = null;
    for (var i = 0; i < state.top5.length; i++) {
      if (state.top5[i].v === state.winner) { w = state.top5[i]; break; }
    }
    html += '<div class="ab-result">';
    html += '<div class="winner-label">\u2705 Winner: v' + state.winner + '</div>';
    if (w) {
      html += '<audio controls preload="auto" src="' + basePath + '/' + w.file + '"></audio>';
      html += '<div class="winner-stats">';
      html += '<span class="score">Score: ' + w.score.toFixed(3) + '</span>';
      html += ' \u00b7 <span class="dur">' + w.dur.toFixed(1) + 's</span>';
      if (chunk.idx > 0) html += ' \u00b7 <span class="tone">Tonal: ' + w.tone.toFixed(4) + '</span>';
      html += '</div>';
    }
    html += '<button class="btn-repick" onclick="resetChunk(' + chunk.idx + ')">Re-pick this chunk</button>';
    html += '</div>';
  } else if (!state.done) {
    // A/B comparison
    var a = state.champion;
    var bIdx = state.challengerIdx;
    var b = (bIdx >= 0 && bIdx < state.top5.length) ? state.top5[bIdx] : null;

    if (!a || !b) {
      html += '<p style="color:#ef4444">Not enough candidates (a=' + !!a + ', b=' + !!b + ', challIdx=' + bIdx + ')</p>';
      area.innerHTML = html;
      return;
    }

    var remaining = 0;
    for (var ri = 0; ri < state.top5.length; ri++) {
      if (state.rejected.indexOf(state.top5[ri].v) === -1) remaining++;
    }
    html += '<div class="round-info">' + remaining + ' candidates remaining</div>';

    html += '<div class="ab-compare" id="abCompare">';
    // Side A (champion)
    html += '<div class="ab-side">';
    html += '<div class="ab-label label-a">A <span style="font-size:.6em;opacity:.7">(v' + a.v + ')</span></div>';
    html += '<audio controls preload="auto" src="' + basePath + '/' + a.file + '"></audio>';
    html += '<div class="ab-stats"><span class="score">' + a.score.toFixed(3) + '</span><span class="dur">' + a.dur.toFixed(1) + 's</span>';
    if (chunk.idx > 0) html += '<span class="tone">t' + a.tone.toFixed(4) + '</span>';
    html += '</div></div>';
    // Side B (challenger)
    html += '<div class="ab-side">';
    html += '<div class="ab-label label-b">B <span style="font-size:.6em;opacity:.7">(v' + b.v + ')</span></div>';
    html += '<audio controls preload="auto" src="' + basePath + '/' + b.file + '"></audio>';
    html += '<div class="ab-stats"><span class="score">' + b.score.toFixed(3) + '</span><span class="dur">' + b.dur.toFixed(1) + 's</span>';
    if (chunk.idx > 0) html += '<span class="tone">t' + b.tone.toFixed(4) + '</span>';
    html += '</div></div>';
    html += '</div>';

    html += '<div class="ab-actions">';
    html += '<button class="btn-a" onclick="pickSide(\'a\')">A wins (A)</button>';
    html += '<button class="btn-same" onclick="pickSide(\'same\')">Reject both (S)</button>';
    html += '<button class="btn-b" onclick="pickSide(\'b\')">B wins (B)</button>';
    html += '</div>';
    html += '<div class="shortcuts">Keyboard: <kbd>A</kbd> A wins \u00b7 <kbd>S</kbd> Reject both \u00b7 <kbd>B</kbd> B wins \u00b7 <kbd>\u2190</kbd><kbd>\u2192</kbd> Navigate</div>';
  } else {
    html += '<p style="color:#f59e0b">Chunk in unexpected state (done=' + state.done + ', winner=' + state.winner + ')</p>';
  }

  area.innerHTML = html;

  // Flash animation on the compare area
  var cmp = document.getElementById('abCompare');
  if (cmp) {
    cmp.style.opacity = '0.5';
    setTimeout(function() { cmp.style.opacity = '1'; }, 50);
  }

  // Update nav highlight
  var navBtns = document.querySelectorAll('.chunk-nav button');
  for (var i = 0; i < navBtns.length; i++) navBtns[i].classList.remove('current');
  var navBtn = document.getElementById('nav-' + chunk.idx);
  if (navBtn) navBtn.classList.add('current');

  logDebug('Rendered chunk ' + chunk.idx + (state.done ? ' (done, winner=v' + state.winner + ')' : ' (round ' + state.round + ', A=v' + (state.champion ? state.champion.v : '?') + ' vs B=v' + ((state.top5[state.challengerIdx] || {}).v || '?') + ')'));
}

// --- Tournament: pick a side ---
function pickSide(side) {
  var chunk = chunkData[currentChunkArrayIdx];
  var state = abState[chunk.idx];

  if (!state) { logDebug('pickSide: no state for chunk ' + chunk.idx); return; }
  if (state.done) { logDebug('pickSide: chunk ' + chunk.idx + ' already done'); return; }

  var a = state.champion;
  var b = state.top5[state.challengerIdx];

  if (!a || !b) { logDebug('pickSide: missing a or b'); return; }

  pickCounter++;

  if (side === 'same') {
    // REJECT BOTH â€” neither wins
    state.rejected.push(a.v);
    state.rejected.push(b.v);
    showToast('Rejected both v' + a.v + ' + v' + b.v);

    // Find next TWO non-rejected candidates
    var remaining = [];
    for (var i = 0; i < state.top5.length; i++) {
      if (state.rejected.indexOf(state.top5[i].v) === -1) remaining.push(i);
    }

    if (remaining.length === 0) {
      // All rejected â€” no winner
      state.done = true;
      state.winner = null;
      state.round = 0;
      logDebug('All candidates rejected for chunk ' + chunk.idx);
      showToast('No winner \u2014 all rejected');
    } else if (remaining.length === 1) {
      // Only one left â€” auto-wins
      state.winner = state.top5[remaining[0]].v;
      state.done = true;
      state.round = 0;
      pickedThisSession[chunk.idx] = 'a';
      logDebug('Last candidate wins chunk ' + chunk.idx + ': v' + state.winner);
      showToast('PICKED: v' + state.winner + ' (last standing)');
    } else {
      // Remaining candidates exist â€” load next pair on same chunk
      state.champion = state.top5[remaining[0]];
      state.challengerIdx = remaining[1];
      state.round = (state.round || 0) + 1;
      logDebug('Both rejected, ' + remaining.length + ' remain. Loading next pair.');
    }

    // Stay on current chunk â€” show next pair (no auto-advance)
    try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }
    renderChunk();
    return;
  } else {
    // A wins or B wins â€” PICK IMMEDIATELY
    var winner = (side === 'a') ? a : b;
    var loser = (side === 'a') ? b : a;

    state.rejected.push(loser.v);
    state.winner = winner.v;
    state.done = true;
    state.round = 0;
    pickedThisSession[chunk.idx] = side;
    logDebug('Picked v' + winner.v + ' for chunk ' + chunk.idx);
    showToast('PICKED: v' + winner.v);
  }

  // Save with try/catch so rendering always happens
  try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }

  // Always render regardless of save success
  renderChunk();

  // Auto-advance to next unpicked chunk after tournament completes
  if (state.done && state.winner != null) {
    setTimeout(function() {
      for (var i = currentChunkArrayIdx + 1; i < chunkData.length; i++) {
        if (abState[chunkData[i].idx] && !abState[chunkData[i].idx].done) {
          currentChunkArrayIdx = i;
          renderChunk();
          return;
        }
      }
    }, 800);
  }
}

function resetChunk(chunkIdx) {
  initABState(chunkIdx, true);
  try { saveState(); } catch (e) { logDebug('saveState error: ' + e.message); }
  renderChunk();
}

function updateNotes(chunkIdx) {
  var el = document.getElementById('notes-' + chunkIdx);
  if (el && abState[chunkIdx]) {
    abState[chunkIdx].notes = el.value;
    try { saveState(); } catch (e) {}
  }
}

function goToChunk(arrayIdx) {
  if (arrayIdx >= 0 && arrayIdx < chunkData.length) {
    currentChunkArrayIdx = arrayIdx;
    renderChunk();
  }
}

function showToast(text) {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = text;
  t.className = 'pick-toast show';
  setTimeout(function() { t.className = 'pick-toast'; }, 900);
}

// --- Collect picks from abState ---
function collectPicks() {
  var picks = { session: SESSION_ID, reviewed: new Date().toISOString(), picks: [] };
  for (var i = 0; i < chunkData.length; i++) {
    var c = chunkData[i];
    var s = abState[c.idx] || {};
    var winnerFile = null;
    if (s.winner != null && s.top5) {
      for (var j = 0; j < s.top5.length; j++) {
        if (s.top5[j].v === s.winner) { winnerFile = s.top5[j].file; break; }
      }
    }
    picks.picks.push({
      chunk: c.idx,
      text: c.text,
      picked: s.winner != null ? s.winner : null,
      picked_file: winnerFile,
      rejected: s.rejected || [],
      notes: s.notes || '',
      side: pickedThisSession[c.idx] || s.side || null
    });
  }
  return picks;
}

// --- Save: immediate, no debounce ---
function saveState() {
  var picks = collectPicks();
  var ls = {};
  for (var i = 0; i < picks.picks.length; i++) {
    var p = picks.picks[i];
    ls[p.chunk] = { picked: p.picked, rejected: p.rejected, notes: p.notes, side: p.side };
  }
  try {
    localStorage.setItem('vault-picks-' + SESSION_ID, JSON.stringify(ls));
  } catch (e) {
    console.warn('localStorage write failed:', e);
  }
  updateProgress();
  updateChunkNav();
  setSaveStatus('saving', 'Saving...');
  saveRemote(picks);
}

async function saveRemote(picks) {
  if (!PICKS_API || !AUTH_TOKEN) { setSaveStatus('ok', 'Local only'); return; }
  try {
    var resp = await fetch(PICKS_API + '/picks/' + SESSION_ID, {
      method: 'PUT',
      headers: { 'Authorization': 'Bearer ' + AUTH_TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify(picks)
    });
    setSaveStatus(resp.ok ? 'ok' : 'error', resp.ok ? 'Saved ' + new Date().toLocaleTimeString() : 'Save failed: ' + resp.status);
  } catch (e) { setSaveStatus('error', 'Save failed: ' + e.message); }
}

function updateProgress() {
  var n = 0;
  for (var i = 0; i < chunkData.length; i++) {
    var s = abState[chunkData[i].idx];
    if (s && s.done && s.winner != null) n++;
  }
  var el = document.getElementById('progress');
  if (el) el.textContent = n + ' / ' + chunkData.length + ' picked';
}

function updateChunkNav() {
  for (var i = 0; i < chunkData.length; i++) {
    var c = chunkData[i];
    var btn = document.getElementById('nav-' + c.idx);
    if (!btn) continue;
    btn.className = '';
    if (i === currentChunkArrayIdx) btn.classList.add('current');
    var s = abState[c.idx];
    if (s && s.done && s.winner != null) {
      var ps = pickedThisSession[c.idx];
      btn.classList.add(ps ? (ps === 'b' ? 'picked-b' : 'picked-a') : 'picked-old');
    } else if (s && s.rejected && s.rejected.length > 0) {
      btn.classList.add('rejected');
    }
  }
}

// --- Export ---
function exportPicks() {
  var picks = collectPicks();
  var json = JSON.stringify(picks, null, 2);
  var blob = new Blob([json], { type: 'application/json' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION_ID + '-vault-picks.json';
  a.click();
  document.getElementById('exportStatus').textContent = 'Downloaded!';
  document.getElementById('summaryBox').style.display = 'block';
  document.getElementById('summaryJson').textContent = json;
}

function exportTxt() {
  var picks = collectPicks();
  var txt = 'VAULT PICKS: ' + picks.session + '\nDate: ' + picks.reviewed + '\n\n';
  for (var i = 0; i < picks.picks.length; i++) {
    var p = picks.picks[i];
    txt += 'Chunk ' + p.chunk + ': picked v' + (p.picked != null ? p.picked : 'NONE') + ' (' + (p.picked_file || 'none') + ')\n';
    txt += '  Text: "' + p.text + '"\n';
    if (p.notes) txt += '  Notes: ' + p.notes + '\n';
    if (p.rejected.length) txt += '  Rejected: ' + p.rejected.map(function(v) { return 'v' + v; }).join(', ') + '\n';
    txt += '\n';
  }
  var blob = new Blob([txt], { type: 'text/plain' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SESSION_ID + '-vault-picks.txt';
  a.click();
}

async function playAllPicks() {
  var btn = document.getElementById('btnPlayAll');
  if (btn) btn.textContent = 'Playing...';
  for (var i = 0; i < chunkData.length; i++) {
    var c = chunkData[i];
    var s = abState[c.idx];
    if (!s || s.winner == null || !s.top5) continue;
    var w = null;
    for (var j = 0; j < s.top5.length; j++) {
      if (s.top5[j].v === s.winner) { w = s.top5[j]; break; }
    }
    if (!w) continue;
    var audio = new Audio(basePath + '/' + w.file);
    audio.play();
    await new Promise(function(r) { audio.onended = r; });
    await new Promise(function(r) { setTimeout(r, 800); });
  }
  if (btn) btn.textContent = 'Play All Picks';
}

// --- Keyboard shortcuts ---
document.addEventListener('keydown', function(e) {
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  if (e.key === 'a' || e.key === 'A') pickSide('a');
  else if (e.key === 'b' || e.key === 'B') pickSide('b');
  else if (e.key === 's' || e.key === 'S') pickSide('same');
  else if (e.key === 'ArrowLeft') goToChunk(currentChunkArrayIdx - 1);
  else if (e.key === 'ArrowRight') goToChunk(currentChunkArrayIdx + 1);
});

// --- Init ---
async function init() {
  logDebug('Initializing...');
  await loadState();

  var nav = document.getElementById('chunkNav');
  for (var i = 0; i < chunkData.length; i++) {
    (function(idx) {
      var btn = document.createElement('button');
      btn.id = 'nav-' + chunkData[idx].idx;
      btn.textContent = chunkData[idx].idx;
      btn.onclick = function() { goToChunk(idx); };
      nav.appendChild(btn);
    })(i);
  }

  for (var i = 0; i < chunkData.length; i++) {
    initABState(chunkData[i].idx, false);
  }

  // Start at first unpicked chunk
  var first = -1;
  for (var i = 0; i < chunkData.length; i++) {
    if (!abState[chunkData[i].idx] || !abState[chunkData[i].idx].done) { first = i; break; }
  }
  if (first >= 0) currentChunkArrayIdx = first;

  updateProgress();
  updateChunkNav();
  renderChunk();
  logDebug('Ready. ' + chunkData.length + ' chunks loaded.');
}

init();
```

### File 4: `rebuild_full_picker.py` (101 lines â€” assembly script)

Reads chunk metadata from vault directories (`c00/`, `c01/`, etc.), builds `chunkData` JSON array, injects CSS + HTML + JS, writes `review.html`. Includes verification assertions (chunk count, v2 marker, try/catch saveState, debug logging, pick counter, session ID).

**Usage:**
```
python3 tools/vault-picker/rebuild_full_picker.py 52-the-court-of-your-mind
python3 tools/vault-picker/rebuild_full_picker.py 01-morning-meditation
```

```python
#!/usr/bin/env python3
"""Rebuild review.html for any vault session from picker source files + chunk metadata.

Usage:
    python3 tools/vault-picker/rebuild_full_picker.py 52-the-court-of-your-mind
    python3 tools/vault-picker/rebuild_full_picker.py 01-morning-meditation
"""

import argparse
import json
import glob
import os
import re
import sys

# Source files live alongside this script
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_BASE = os.path.join(os.path.dirname(TOOLS_DIR), '..', 'content', 'audio-free', 'vault')
VAULT_BASE = os.path.normpath(VAULT_BASE)


def rebuild(session_id):
    vault_dir = os.path.join(VAULT_BASE, session_id)
    review_path = os.path.join(vault_dir, 'review.html')

    if not os.path.isdir(vault_dir):
        print(f"ERROR: Vault directory not found: {vault_dir}")
        return False

    # Read all chunk metadata files
    chunk_dirs = sorted(glob.glob(os.path.join(vault_dir, 'c[0-9][0-9]')))
    print(f"Found {len(chunk_dirs)} chunk directories")

    all_chunks = []
    for cdir in chunk_dirs:
        dirname = os.path.basename(cdir)
        meta_file = os.path.join(cdir, f"{dirname}_meta.json")
        if not os.path.exists(meta_file):
            print(f"WARNING: No metadata for {dirname}")
            continue

        with open(meta_file, 'r') as f:
            meta = json.load(f)

        candidates = []
        for c in meta['candidates']:
            candidates.append({
                "v": c['version'],
                "file": f"{dirname}/{c['filename']}",
                "score": round(c['composite_score'], 4),
                "dur": round(c['duration_seconds'], 2),
                "tone": round(c.get('tonal_distance_to_prev', 0), 6),
                "filtered": c['filtered']
            })

        all_chunks.append({
            "idx": meta['chunk_index'],
            "text": meta['text'],
            "chars": meta['char_count'],
            "isOpening": meta['is_opening'],
            "isClosing": meta['is_closing'],
            "candidates": candidates
        })

    all_chunks.sort(key=lambda c: c['idx'])
    print(f"Built chunkData with {len(all_chunks)} chunks")
    total_candidates = sum(len(c['candidates']) for c in all_chunks)
    print(f"Total candidates: {total_candidates}")

    # Read the three source parts from tools/vault-picker/
    with open(os.path.join(TOOLS_DIR, 'ab_picker_css.txt'), 'r') as f:
        css = f.read()
    with open(os.path.join(TOOLS_DIR, 'ab_picker_html.txt'), 'r') as f:
        html_body = f.read()
    with open(os.path.join(TOOLS_DIR, 'ab_picker_js.js'), 'r') as f:
        js = f.read()

    # Replace template placeholders in HTML body
    html_body = html_body.replace('{{SESSION_ID}}', session_id)

    # Build data section
    data_json = json.dumps(all_chunks, indent=2)

    # Assemble complete file from scratch
    parts = []
    parts.append('<!DOCTYPE html>\n')
    parts.append('<html lang="en">\n')
    parts.append('<head>\n')
    parts.append('<meta charset="UTF-8">\n')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
    parts.append(f'<title>Vault Picker â€” {session_id}</title>\n')
    parts.append(css + '\n')
    parts.append('</head>\n')
    parts.append('<body>\n')
    parts.append(html_body + '\n')
    parts.append('\n<script>\n')
    parts.append(f"var SESSION_ID = '{session_id}';\n")
    parts.append(f"var chunkData = {data_json};\n\n")
    parts.append(js + '\n')
    parts.append('</script>\n')
    parts.append('</body>\n')
    parts.append('</html>\n')

    output = ''.join(parts)

    with open(review_path, 'w') as f:
        f.write(output)

    # Verify
    with open(review_path, 'r') as f:
        final = f.read()

    chunk_count = len(re.findall(r'"idx":', final))
    assert chunk_count == len(all_chunks), f"Expected {len(all_chunks)} chunks, found {chunk_count}"
    assert 'Picker v2' in final, "Missing v2 marker"
    assert 'try { saveState()' in final, "Missing try/catch saveState"
    assert 'logDebug' in final, "Missing debug logging"
    assert 'pickCounter' in final, "Missing pick counter"
    assert session_id in final, f"Missing session ID '{session_id}' in output"

    line_count = final.count('\n')
    print(f"Wrote {len(final):,} bytes, {line_count:,} lines")
    print(f"Chunks in file: {chunk_count}")
    print(f"Output: {review_path}")
    print("All checks passed")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Rebuild review.html for a vault session')
    parser.add_argument('session_id',
                        help='Session ID (e.g., 52-the-court-of-your-mind)')
    args = parser.parse_args()

    success = rebuild(args.session_id)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
```

---

*End of Appendix A. These four files constitute the complete A/B tournament picker system. When `rebuild_full_picker.py` runs, it reads the CSS, HTML, and JS files from the same directory, combines them with chunk metadata from the vault directory, and outputs a self-contained `review.html` page.*
