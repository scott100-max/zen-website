# Salus Project Bible

**Version:** 3.4
**Updated:** 9 February 2026
**Purpose:** Single source of truth for all Salus website and audio production standards

This document is the canonical reference for Claude Code and all contributors. Where this document conflicts with earlier briefs, amendment logs, or conversation history, **this document wins**.

---

## Contents

### Part A — Website & Infrastructure
1. [Design Standards](#1-design-standards)
2. [Terminology](#2-terminology)
3. [Deployment & Infrastructure](#3-deployment--infrastructure)
4. [Authentication & Payments](#4-authentication--payments)
5. [SEO](#5-seo)
6. [Self-Validation Process](#6-self-validation-process)
7. [Common Issues & Lessons Learned](#7-common-issues--lessons-learned)

### Part B — Audio Production
8. [Production Rules (Non-Negotiable)](#8-production-rules-non-negotiable)
9. [TTS Providers](#9-tts-providers)
10. [Marco Master Voice Specification](#10-marco-master-voice-specification)
11. [Audio Processing Pipeline](#11-audio-processing-pipeline)
12. [QA Gate System](#12-qa-gate-system)
13. [Script Writing Rules](#13-script-writing-rules)
13A. [Script Uniqueness & Cross-Session Differentiation](#13a-script-uniqueness--cross-session-differentiation)
14. [Expression Through Punctuation](#14-expression-through-punctuation)
15. [Auphonic Integration](#15-auphonic-integration)
15A. [Targeted Chunk Repair](#15a-targeted-chunk-repair)
16. [Build Execution](#16-build-execution)
17. [Governance](#17-governance)
18. [V3 API Emotion System](#18-v3-api-emotion-system)

### Part C — Historical Record
19. [Amendment Log](#19-amendment-log)

---

# PART A — WEBSITE & INFRASTRUCTURE

---

## 1. Design Standards

### Tile/Card Layout Rules
- **Maximum 2 tiles per row** on all screen sizes (site-wide standard)
- Tiles stack to 1 column on mobile devices
- No coloured gradient tiles/boxes on cards — use simple white cards with text only

### Image Guidelines
- **No people in card/tile images** — use abstract, nature, or texture imagery only
- **No repeating images** — each card/tile must have a unique image site-wide
- Source images from user photo repository when available
- Large images (>1MB) cause browser rendering issues — optimise to 600×600px for web
- Always add cache-buster: `?v=YYYYMMDD`

### Card Design Patterns
- **Atmospheric cards** (Sessions, Tools, Education): Full gradient backgrounds with category colours, floating glowing orbs (`filter:blur(40px)`, `opacity:0.4-0.5`), white text on dark backgrounds
- **Glassmorphism elements**: `backdrop-filter:blur(10px)`, `rgba(255,255,255,0.15)` backgrounds, deep coloured shadows

### Category Colour Scheme
| Category | Primary Gradient | Orb Colours |
|----------|-----------------|-------------|
| Beginners/Teal | #0d3d4a → #1a5568 → #0f4c5c | #06b6d4, #22d3ee |
| Stress/Green | #064e3b → #065f46 → #047857 | #10b981, #34d399 |
| Sleep/Purple | #1e1b4b → #312e81 → #3730a3 | #818cf8, #a78bfa |
| Focus/Amber | #451a03 → #78350f → #92400e | #f59e0b, #fbbf24 |

### Dark Theme (Complete — 8 Feb 2026)
- All pages fully dark-themed: body `#0a0a12`, text `#f0eefc`
- `css/style.css` `:root` includes: `--deep`, `--teal`, `--text-bright`, `--text-muted`, `--text-mid`
- Auth alert colors use dark-compatible rgba (e.g. `rgba(239,68,68,0.12)` not `#fee2e2`)
- No light backgrounds, no `var(--white)` or `var(--off-white)` in visible elements

### Unified Footer (Complete — 8 Feb 2026)
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
- Latin phrase: "Salūs — Latin: health, safety, well-being" under hero sections on all pages
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
| **LALAL.AI** | Per-chunk audio cleaning (voice_clean API) | `https://www.lalal.ai/api/v1` |

### LALAL.AI

| | |
|---|---|
| **Service** | AI audio cleaning — noise cancellation, de-echo, de-reverb |
| **API** | REST v1 (`/upload/`, `/split/voice_clean/`, `/check/`, `/split/batch/voice_clean/`) |
| **Auth** | `X-License-Key` header (activation code from account profile) |
| **Account** | scottripley@icloud.com |
| **Plan** | Lite (£6/mo, 90 min fast queue) |
| **Env var** | `LALAL_API_KEY` in `.env` |
| **Quota** | ~3 min per full session build (36 chunks × ~5s each). Lite plan covers ~30 builds/month. |
| **Status** | **DISABLED** — integrated in `build-session-v3.py` but commented out pending settings optimisation |

**What works:** Noise cancellation (`noise_cancelling_level=1`) removed almost all hiss from session 25 rebuild. Proven effective for TTS hiss cleanup.

**What doesn't work:** Dereverb (`dereverb_enabled=True`) strips Marco's vocal resonance, mistaking it for room reverb. Fish TTS output has no actual room reverb — dereverb has nothing legitimate to remove and damages vocal character instead. Voice quality degradation worst on opening chunks (1–5), settles later.

**Next test required:** `dereverb_enabled=False`, `noise_cancelling_level=1` or `2` — hiss-only mode. If effective without dereverb, LALAL becomes a permanent pipeline stage (Phase 1.5, between chunk QA and edge fades).

**Cannot fix:** Voice character shift and echo. These are TTS generation problems baked into Fish output. No external post-processing service can fix what Fish generates wrong — the only remedy is chunk regeneration.

### GitHub Pages
- **Repository:** `https://github.com/scott100-max/Salus-Website.git`
- **Branch:** `main`
- **Auto-deploys** on push within 1-2 minutes

```bash
git add <files>
git commit -m "Description"
git push origin main
```

### Cloudflare R2 (media files)
- **Bucket:** `salus-mind`
- **Account ID:** `e798430a916680159a81cf34de0db9c2`
- **Custom domain:** `media.salus-mind.com` (proxied through Cloudflare CDN)
- **Public dev URL:** Disabled — use custom domain only
- **API token** (Edit zone DNS): `yYNUa2enwfPdNnVrfcUQnWHhgMnebTSFntGWbwGe`
- **CORS:** Configured for `https://salus-mind.com` and `https://www.salus-mind.com` (GET/HEAD). Required for cross-origin audio playback from `media.salus-mind.com`.

```bash
# Upload via wrangler CLI:
npx wrangler r2 object put salus-mind/content/audio-free/FILENAME.mp3 --file=./FILENAME.mp3

# Or drag-and-drop in Cloudflare dashboard: R2 → salus-mind → Objects → Upload
```

**File paths in R2:**
- Free audio: `content/audio-free/`
- Sounds (ASMR): `content/sounds/`
- Video: `content/video/`
- Reference: `reference/` (marco master etc.)

**ASMR sounds:**
- All ASMR audio is user-provided (downloaded from YouTube, cut to 1 hour each). Not procedurally generated.
- 14 sounds: rain, ocean, forest, thunder, birds, fire, stream, cafe, garden, library, night, temple, waterfall, white noise
- 1-hour cuts stored locally in `content/audio-free/` (e.g. `asmr-stream.mp3`)
- Short clips on R2 at `content/sounds/` for ASMR page playback
- Full-length YouTube source downloads in `content/audio/ambient/youtube-downloads/`

**Media references in HTML — two player types:**

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
- **Registrar holds nameservers only** — all records in Cloudflare dashboard
- GitHub Pages A records: `185.199.108-111.153`
- `www` CNAME → `scott100-max.github.io`
- `media` CNAME → R2 bucket (proxied)

### Large Files
- **NEVER commit audio/video files to git** — all media goes to Cloudflare R2
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

**Root should only contain:** HTML pages, `build-session-v3.py`, `audition-voices.py`, `CNAME`, `robots.txt`, `sitemap.xml`, `package.json`.

### Workflow Summary
| Task | Action |
|------|--------|
| Edit HTML/CSS/JS | Change files → `git push` |
| Add new audio/video | Upload to R2 → reference in HTML → `git push` |
| Add new HTML page | Create page → add to sitemap.xml → add to nav on ALL pages → `git push` |

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
- `profiles` — User data (auto-created on signup via trigger)
- `subscriptions` — Stripe data (user_id, stripe_customer_id, status, plan_type)

**Premium Logic (in order):**
1. Check Supabase `subscriptions` table for active subscription (cross-device)
2. Fall back to localStorage `salus_premium` (legacy/single-device)
3. Migration banner prompts localStorage-only users to create accounts

### Stripe

**Webhook endpoint:** `https://egywowuyixfqytaucihf.supabase.co/functions/v1/stripe-webhook`

**Events handled:**
- `checkout.session.completed` → Create subscription
- `customer.subscription.updated` → Update status
- `customer.subscription.deleted` → Mark expired
- `invoice.payment_succeeded` → Renew period
- `invoice.payment_failed` → Mark past_due

**Auth Flow:**
1. User signs up → Supabase creates `auth.users` + `profiles` record
2. User logs in → Redirected to dashboard (or original page via `?redirect=` param)
3. User subscribes → Stripe checkout includes `client_reference_id={user_id}`
4. Payment completes → Webhook creates `subscriptions` record
5. User logs in anywhere → `SalusAuth.isPremium()` returns true

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
1. **Source of truth:** `docs/FIXES-CHECKLIST.md` — not the validation script
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
—————————————————
Done:     X items
Pending:  Y items  ← WORK REMAINING
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
5. Treat Code like a subcontractor — never let the person who did the work also sign it off

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
- 4 Feb: Rainfall Sleep Journey — analyser reported PASS on a file with voice changes, repeated content, and hiss
- 7 Feb: Loving-kindness — 9 gates passed on a file with audible hiss spike at 0:30 and catastrophic hiss wall from 12:00, both visible on Auphonic and Gate 9 visuals

**Prevention:** All gates must be pass/fail. No informational-only gates. Visual analysis must include programmatic evaluation, not just image generation.

---

# PART B — AUDIO PRODUCTION

---

## 8. Production Rules (Non-Negotiable)

1. **ONE build at a time.** Never run builds in parallel — burned 100K credits once.
2. **Always dry-run first.** Check block count and silence totals before spending credits.
3. **Fish has a ~60% rebuild rate on 45-min stories.** This is expected. Rebuild until it lands.
4. **Never identical gaps.** All pauses go through `humanize_pauses()`.
5. **Marco is the only voice.** Do not audition alternatives unless Marco is discontinued.
6. **QA is two-stage.** The pipeline runs 14 automated gates, then human review is MANDATORY before deploy. Automated gates catch measurable defects; human listening catches what metrics miss. Neither stage alone is sufficient. Use `--no-deploy` to hold builds for review.
7. **Deploy after human review.** Default build mode is `--no-deploy`. Build runs → 14 gates → human review → only then deploy to R2. Automatic deploy (without `--no-deploy`) is available but should only be used for re-deploys of already-reviewed sessions.
8. **Email is mandatory.** Every completed build cycle ends with an email to scottripley@icloud.com — pass or fail.
9. **Fully autonomous** (except where a STOP rule is triggered — see [Section 17](#17-governance)).
10. **No OneDrive.** All files go to git (code) or Cloudflare R2 (media). Never copy files to OneDrive.
11. **No post-build splicing — except targeted repair (Section 15A).** Never splice individual chunks into an existing build as a shortcut — crude splicing causes tonal seams at splice boundaries (tested and failed). Selective regeneration WITHIN a build is permitted: `--focus-chunks` gives problem chunks more generation attempts (best-of-10) while others get best-of-5. The distinction is: regenerating chunks before assembly = acceptable; patching chunks into an already-assembled file = prohibited. **Exception:** Targeted chunk repair following the full process in Section 15A is permitted. This is controlled single-word or single-chunk replacement with MFCC tonal matching and crossfade blending — not crude splicing. The result is always saved as a new file, never overwrites the original.
12. **Automated gates: 100% pass required.** All 14 gates must pass — no exceptions. Human review: accept a reasonable clean rate and ship. Perfection should not prevent shipping, but the clean rate and any flagged chunks must be documented in the build record. If a session ships below 100% human clean rate, the specific issues accepted are logged for future pipeline improvement.
13. **Lossless pipeline.** All intermediate audio MUST be WAV. MP3 encoding happens exactly ONCE at the final step.
14. **Never overwrite raw narration — master narration files are sacrosanct.** Once a session's raw narration WAV has passed 14 gates and been approved for deploy, it becomes a **master narration file**. Master narrations are never deleted, overwritten, modified, or used as input for destructive operations. They are the source from which all future versions (ambient mixes, repairs, remastering) are derived. Naming convention: `{session-name}_master-narration.wav` stored in `content/audio-free/masters/`. Each master is accompanied by a **chunk schedule** (`{session-name}_chunk-schedule.txt`), a **QA report PNG**, and a **production record** (`{session-name}_production-record.md`) — together these form the complete production archive for that session (see Section 16 for production record template). If a repair or remix is needed, copy the master to a working file first — the master stays untouched. Pre-master raw files (intermediate builds, failed attempts) use timestamped names: `{session}_raw_v1.wav`, `{session}_raw_v2.wav` etc. Both pre-clean and post-clean versions must be saved when any cleaning service is applied. Never leave raw files in temp directories.
15. **All audio comparisons must be narration-only.** When evaluating audio quality differences (A/B testing, LALAL before/after, pipeline changes), always compare raw narration without ambient. Ambient masks differences and makes evaluation invalid. Both A and B files must be provided simultaneously with clear naming (e.g. `25-intro-NO-LALAL-narration.wav`, `25-intro-LALAL-narration.wav`).
16. **Garden ambient offset.** `garden-8hr.mp3` has 9.5 seconds of dead digital silence at the file start. Always use `-ss 10` when mixing garden ambient. This is automated in `build-session-v3.py` for both Fish and Resemble mix paths (confirmed 9 Feb 2026).

---

## 9. TTS Providers

### Provider Routing (Decision Tree)

```
Is the script mostly short phrases with pauses? → Fish Audio
Is the script mostly long flowing narrative?    → Resemble AI
Mixed content?                                  → Fish (safer default)
Unsure?                                         → Fish (Marco's home)
```

### Fish Audio — PRIMARY PROVIDER

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

**Best for:** Meditation, mindfulness, loving-kindness, body scans, breathwork, mantras, affirmations, any session <15 min.

**Architecture:** One TTS call per text block. Pauses stitched in post-production.

**Critical characteristics:**
- Non-deterministic: same input produces different output every time
- ~60% rebuild rate on 45-min stories — this is normal
- Cost: negligible ($10 lasts ages)
- Real cost is TIME, not money
- Raw output: −16.34 LUFS average, −4.39 dBTP peak
- Chunk volume spread: ~8 dB (Auphonic leveller data)
- SNR: 45+ dB (broadcast quality without processing)
- No hum, minimal noise floor

**The Fish API is stateless.** There is NO `condition_on_previous_chunks` parameter in the Fish Audio TTS API. Each API call is completely independent. Voice conditioning between chunks is implemented CLIENT-SIDE in `build-session-v3.py` by passing the previous chunk's audio as the `references` input for the next chunk. This is our pipeline's feature, not a Fish feature. Each chunk can be regenerated independently as long as the correct reference audio is provided.

**Possible S1 model degradation (February 2026).** Fish service alert shows generations exceeding 500 characters are temporarily routed to the v1.6 model instead of S1. If some chunks in a build hit S1 and others hit v1.6, different voice characteristics result — producing voice shift between chunks within the same session. This is a Fish-side issue outside our control. Story Studio was upgraded in December 2025; infrastructure changes may have side effects. Monitor Fish changelogs for resolution.

**Opening chunk weakness.** Chunks 1–5 consistently score lowest in per-chunk QA (typically 0.35–0.43, against a flag threshold of 0.50). Chunk 1 has no previous MFCC tonal reference — Fish has nothing to chain voice conditioning from. Fish typically needs 2–3 chunks to "settle" into Marco's voice character. Possible future fix: generate a throwaway conditioning chunk before the real chunk 1 to give Fish a reference anchor.

**Fish cleanup chain (CANONICAL — use this, nothing else):**
1. Edge fades: 15ms cosine on each chunk before concatenation
2. Concatenate all chunks + silences (WAV)
3. Whole-file loudnorm: `loudnorm=I=-26:TP=-2:LRA=11` on full narration AFTER concatenation
4. Ambient mix (`amix` with `normalize=0`)
5. Final encode: 128kbps MP3 (ONLY lossy step)

Per-chunk loudnorm was REMOVED (8 Feb 2026) — whole-file approach preserves natural dynamics between chunks. Requires Gate 7 thresholds 9/14 dB + 4s silence margin to accommodate Fish chunk-level swings.

The `highshelf=f=3000:g=3` boost was REMOVED (8 Feb 2026) — A/B testing confirmed +3dB HF boost causes perceived echo on certain words. Loudnorm-only is cleaner with less hiss.

The HF shelf cut (`highshelf=f=7000:g=-3`) was proposed and tested across the full tuning range (−2 to −5 dB at 6–8 kHz) during the Gate 6 investigation. It failed — removing the 3 kHz boost entirely produced identical flag counts, proving the root cause of Gate 6 false positives was natural speech sibilants, not pipeline-induced HF noise.

**DO NOT APPLY to Fish output:**
- ~~lowpass=f=10000~~ (kills clarity and consonant detail)
- ~~afftdn=nf=-25~~ (muffles the voice — noise floor already clean at 45 dB SNR)
- ~~dynaudnorm~~ (amplifies silence — NEVER use)
- ~~aggressive de-essers~~ (removes natural sibilance)
- ~~highpass=80~~ (not needed for Fish — no low-frequency noise)
- ~~highshelf=f=7000:g=-3~~ (tested and failed — does not address root cause)
- ~~highshelf=f=3000:g=3~~ (removed 8 Feb — causes perceived echo on certain words)
- ~~LALAL.AI dereverb~~ (strips Marco's vocal resonance — Fish TTS has no room reverb for dereverb to legitimately remove. Tested 8 Feb 2026: voice quality degraded, worst on opening chunks. Noise cancellation without dereverb may be viable — see Section 3, LALAL.AI)

### Resemble AI — LONG-FORM PROVIDER

| Setting | Value |
|---------|-------|
| **Voice** | Marco T2 (`da18eeca`) |
| **Preset** | `expressive-story` (`6199a148-cd33-4ad7-b452-f067fdff3894`) — MUST be in every API call |
| **pace** | 0.85 |
| **pitch** | 0 |
| **useHd** | true |
| **temperature** | 0.8 |
| **exaggeration** | 0.75 |

**Best for:** Sleep stories, guided journeys, any session >20 min with long flowing narrative.

**Architecture:** Large ~2000-character chunks, merged with SSML `<break>` tags (original pause durations, capped at 5s). Do NOT use for short phrase content.

**Resemble cleanup chain (CANONICAL):**
`highpass=80, lowpass=10000, afftdn=-25, loudnorm I=-26`

**What produces clean audio:**
- Always include `voice_settings_preset_uuid` in API payload
- Use `output_format: wav` from the API (native WAV, no intermediate lossy steps)
- Keep pace at 0.85
- Let Resemble handle pacing via SSML breaks with original pause durations
- Save native WAV from API directly — no MP3 intermediate

**What degrades audio:**
- Omitting the voice settings preset (produces noisy, hissy output)
- pace > 0.9 (too fast for meditation/sleep)
- `loudnorm I=-24` (too loud, raises noise floor)
- `dynaudnorm` (amplifies silence regions)
- WAV→MP3→WAV at any point (lossy round-trip)
- `cleanup full` (Fish chain — wrong for Resemble)
- `cleanup light` (insufficient for Resemble)
- Random SSML break durations (use original pause values)

### ElevenLabs — ABANDONED (6 Feb 2026)

Evaluated across 11 builds and £90+ in credits. Every approach failed. Evidence archived at `Desktop/elevenlabs-evidence/`.

**Why it failed:** API cannot hold voice consistency beyond 2-3 sequential calls. Studio "audiobook" feature produces continuous speech with no paragraph gaps and voice breakdown. SSML breaks max 3 seconds (sleep stories need 4-8s). Studio API locked behind sales whitelist (403 error).

**Do not revisit ElevenLabs** unless they release a fundamentally different long-form API.

### Fish Audio Female Voices — FAILED (6 Feb 2026)

8 female voices auditioned. All inferior to Marco. None had the warmth or natural pacing. Marco remains sole voice.

---

## 10. Marco Master Voice Specification

### Purpose

The Marco Master is the single definitive reference for what Marco sounds like. Every generated session is measured against this file. If it does not sound like the master, it does not ship — regardless of what automated gates report.

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
| MFCC cosine distance | ≤0.008 (same-text), ≤0.06 (production) | 0.0003–0.0060 | 0.0003 | 0.0100–0.0113 |
| F0 deviation | ≤10% | 0.4%–5.6% | 0.8% | 14.8%–17.4% |

**Not useful metrics (too much variance):** Spectral centroid deviation, RMS deviation. Discarded.

**CRITICAL — THE FISH-4 EDGE CASE:** fish-4 was classified as BAD by human listening but measured 0.0003 MFCC / 0.8% F0 — indistinguishable from GOOD. This proves automated metrics CANNOT catch every subtle quality failure. Human review remains MANDATORY even when all automated gates pass.

### Voice Comparison Gate — Raw vs Raw

The voice comparison gate MUST compare raw audio against the raw master. Pre-cleanup WAV vs raw master. NOT processed audio vs master — the cleanup chain changes the spectral fingerprint and causes false failures.

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

**LESS IS MORE.** Fish Audio TTS output is already broadcast-quality clean (45 dB SNR, −62 dB noise floor). Every processing step trades clarity and character for consistency. Apply the minimum necessary and nothing more.

### Fish Pipeline (CANONICAL)

```
Script (... pause markers)
        │
        ▼
process_script_for_tts() → blocks with pause durations
        │
        ▼
generate_tts_chunk() → Fish API → WAV
        │
        ├─── OVERGENERATION CHECK: If duration > 2x expected, reject and retry (max 3 retries)
        │
        ▼
apply_edge_fades() → 15ms cosine fade on each chunk (WAV in, WAV out)
        │
        ▼
generate_silence() → WAV (mono, pcm_s16le) via humanize_pauses()
        │
        ▼
concatenate_with_silences() → concat demuxer → WAV
        │
        ▼
WHOLE-FILE LOUDNORM: loudnorm=I=-26:TP=-2:LRA=11 on full narration
        │
        ▼
mix_ambient() → amix (normalize=0) → WAV
        │
        ▼
SINGLE MP3 ENCODE (libmp3lame, 128kbps) ← ONLY lossy step
        │
        ▼
qa_loop() → 14-GATE QA (see Section 12)
        │
        ▼
deploy_to_r2() → send_build_email()
```

### Resemble Pipeline

```
Script (... pause markers)
        │
        ▼
process_script_for_tts() → blocks with pause durations
        │
        ▼
merge_blocks_for_resemble(category) → merged chunks with SSML breaks
        │                              (original pause durations, capped at 5s)
        ▼
generate_tts_chunk_resemble() → Resemble API (HD mode, pace=0.85)
        │                        Native WAV preserved (no mono forcing)
        ▼
concatenate_with_silences() → auto-detect channels, match silence
        │
        ▼
cleanup_audio_resemble() → highpass 80 + lowpass 10k + afftdn=-25 + loudnorm I=-26
        │
        ▼
mix_ambient() → ambient mixed at category level
        │
        ▼
SINGLE MP3 ENCODE (128kbps) ← only lossy step
        │
        ▼
qa_loop() → 14-GATE QA (see Section 12)
        │
        ▼
deploy_to_r2() → send_build_email()
```

### Whole-File Loudnorm (Fish only)

Apply `loudnorm` to the full concatenated narration WAV AFTER assembly — not per-chunk. This preserves the natural dynamic variation between chunks that gives Marco his character. Per-chunk loudnorm was tested and removed (8 Feb 2026) because it flattened the delivery and, combined with the highshelf boost, introduced perceived echo on certain words.

The highshelf boost (`highshelf=f=3000:g=3`) was also removed (8 Feb 2026). A/B testing confirmed the +3dB HF boost was causing perceived echo and hiss on words like "settling", "stillness", "feel/feeling", "peace", "ease", "deeply". The loudnorm-only chain is cleaner.

Gate 7 thresholds were widened to 9/14 dB with 4s silence margin to accommodate Fish's natural chunk-level swings under whole-file normalisation.

### Atempo

Marco standard speed adjustment: 0.95x atempo. Applied to the master and consistently to all production. This gives Marco a slightly slower, more deliberate delivery for meditation pacing.

**Exception:** Sleep stories built with Fish/Marco — no atempo needed, natural speed is correct.

### Channel Mismatch Bug (RESOLVED)

All files MUST be mono before concatenation. When ffmpeg's concat demuxer joins mono and stereo PCM files, it misinterprets the sample data — stereo segments play at double duration. Silence files must be generated as mono (`cl=mono`), not stereo.

### Ambient Rules

**Core rules:**
- Ambient file MUST be longer than voice track — **NEVER loop**
- Looping causes an audible glitch at the loop point
- Use 8-hour ambient files (available in `content/audio/ambient/`)
- Background ambient must not fade in until narrator introduction is complete
- Fade in: 15 seconds, Fade out: 8 seconds
- `mix_ambient()` file search order: `-8hr` → `-extended` → base name. WAV checked before MP3.

**Ambient as masking (standard practice):**

A well-mixed ambient bed makes minor artifacts (soft echo, slight tonal shifts) disappear into the soundscape. This is standard practice in commercial meditation audio — every major app uses ambient beds for both atmosphere and artifact masking. The listener's brain attributes the anomaly to the environment rather than the voice.

Different ambient types mask differently. Broadband ambient (rain, stream, ocean) fills the full frequency spectrum and masks more effectively at a given level. Sparse ambient (nighttime birds, wind chimes, temple bells) has gaps where artifacts can peek through and may need higher relative levels or dynamic adjustment to be effective.

**Per-session ambient level:**

Ambient level is set by ear, per session, based on the ambient type and the chunk quality. There is no universal dB target. The person mixing (Scott) listens to the problem chunks with ambient at the proposed level and decides whether artifacts are sufficiently masked.

**Ceiling rule:** If the ambient has to be raised above −8dB relative to the voice to make the session listenable, the chunks have a quality problem that should be solved at the scorer/rebuild level, not the mix level. Ambient is a finishing technique, not a repair tool.

The deployed ambient level is recorded in the Deployed Sessions table (Section 16) for every session, building an empirical reference of what works per ambient type.

**Dynamic ambient (targeted masking):**

Where human review has identified specific problem chunks, the ambient level can be locally adjusted at those timestamps to provide additional masking. Rather than raising the ambient globally (which affects clean sections unnecessarily), the mixer applies a gentle volume swell around the problem spot and settles back to the base level afterward.

Implementation rules:
- Swell must be gradual — ramp up over 2–3 seconds before the problem chunk, hold through the chunk, ramp down over 2–3 seconds after. No sudden jumps.
- Maximum swell: +4dB above the session's base ambient level. Beyond this the ambient draws attention to itself and defeats the purpose.
- The swell should sound like natural variation in the ambient (birds getting busier, rain picking up briefly). Abrupt level changes are more noticeable than the artifact they're trying to mask.
- Dynamic ambient adjustments are driven by human review data — the chunk numbers and timestamps from the review labels. This connects the human feedback loop directly to the mix stage.
- All dynamic adjustments must be documented in the build record: which chunks were targeted, the swell amount, and the ramp durations.

**Available 8-hour ambients:**

| File | Duration | Location | Notes |
|------|----------|----------|-------|
| `rain-8hr.mp3` | 8 hr | `content/audio/ambient/` | |
| `birds-8hr.mp3` | 8 hr | `content/audio/ambient/` | |
| `garden-8hr.mp3` | 12 hr | `content/audio/ambient/` | ⚠️ 9.5s dead silence at file start — always use `-ss 10` |
| `rain-extended.mp3` | 70 min | `content/audio/ambient/` | |
| `stream-3hr.mp3` | 3 hr | `content/audio/ambient/youtube-downloads/` | |
| `stream-extended.mp3` | — | `content/audio/ambient/` | Created 9 Feb to cover longer sessions |
| `loving-kindness-ambient.wav` | 15 min | `content/audio/ambient/` | |

**Ambient type masking reference (to be populated as sessions are deployed):**

| Ambient type | Effective base level | Notes |
|-------------|---------------------|-------|
| Nighttime birds | −42dB (14dB below voice) | Sparse — gaps between chirps need dynamic masking on problem chunks |

---

## 12. QA Gate System

### Overview

14 gates. ALL gates must pass — any failure blocks deploy. There are no informational-only gates. Every gate has a defined pass/fail condition. If a gate cannot fail a build, it is not a gate. Build time is not a constraint — all gates run on every build.

### Gate 1: Quality Benchmarks
Measures noise floor and HF hiss in silence regions via `astats`, compared against master benchmarks.

### Gate 2: Click Artifacts
Scan → patch → rescan loop. Detects click artifacts in silence regions (sample-level jump > peak analysis). Applies 20ms cosine crossfades at all stitch boundaries. Repeats up to 5 passes.

### Gate 3: Independent Spectral Comparison
Compares frequency profile of build against master reference WAV.

**Sliding window:** Gate 3 uses 1–2 second sliding windows for spectral comparison. If ANY window within a chunk exceeds the hiss threshold, the chunk fails — regardless of whole-chunk average.

**Calibrated threshold:** 18 dB above master reference (calibrated against known-good sessions — natural speech HF energy reaches up to 17 dB above reference in normal production).

### Gate 4: Voice Comparison
MFCC cosine + F0 deviation vs Marco master. Uses PRE-CLEANUP audio (see Section 10, Voice Comparison Gate).

**Thresholds:** MFCC ≤0.008 (same-text), ≤0.06 (production). F0 deviation ≤10%.

### Gate 5: Loudness Consistency
Per-second RMS sliding window — catches per-chunk loudness surges.

### Gate 6: HF Hiss Detector (Speech-Aware)
Sliding-window HF-to-total energy ratio on POST-CLEANUP audio. Evaluates non-speech regions only. Voice activity detection (or build manifest silence regions) excludes speech windows before HF ratio evaluation. This prevents natural vocal sibilants from triggering false positives while retaining full sensitivity for genuine hiss in pauses, silence, and transition regions.

**Thresholds:** 3s minimum duration, 6 dB HF/total ratio — unchanged from original calibration.

**Layered hiss coverage:** Gate 6 (non-speech regions) + Gate 1 (whole-file average) + Gate 9 (per-window energy spikes) provide three independent hiss detection systems covering different failure modes.

**History:** Gate 6 originally ran on all audio including speech. This caused 100% build failure rates — every build flagged 4–11 regions of natural speech sibilants. HF shelf cut was tested across the full tuning range (−2 to −5 dB at 6–8 kHz) and failed. Removing the 3 kHz boost entirely produced identical flag counts, confirming the root cause was speech sibilants, not pipeline-induced noise. Speech-aware detection resolved the issue without threshold changes or pipeline modifications.

### Gate 7: Volume Surge/Drop
Local-mean comparison with silence exclusion. 9/14 dB thresholds, proportional silence margin for transitions: `max(4s, silence_duration × 0.15)`. Short pauses (8s) get 4s margin. Long silences (50s) get 7.5s margin — voice ramp-up after extended silence is proportionally longer.

**Low-baseline skip:** Skip detection when local mean energy is below −28 dB. This threshold represents ambient/silence regions, not speech. Flagging silence as "surges" is a false positive.

**Non-deterministic TTS level variation (9 Feb 2026):** Gate 7 is the most persistent failure mode during builds. Fish Audio's TTS generation is non-deterministic — identical text produces different volume levels on each call. When speech returns after a long silence, this variation can cause surges that exceed the 9.0 dB threshold. The threshold is correctly calibrated (lowering it would mask genuine defects). The correct response is to rebuild — eventually a generation set with consistent levels will pass. Sessions 19 and 32 needed 4 and 3 builds respectively; sessions 18 and 23 passed first time. Longer sessions with more chunks have higher failure probability.

### Gate 8: Repeated Content
MFCC fingerprint + Whisper STT with DUAL AGREEMENT — both must flag the same timestamps to confirm. 8-word minimum.

**Manifest text guard (8 Feb 2026):** When MFCC finds similar audio segments, the gate checks whether the underlying script text is actually the same. If word overlap between the two segments is <60%, the pair is skipped as a false positive (similar prosody on different text, common in meditation content with repeated cadence patterns).

**Expected-Repetitions metadata:** The `Expected-Repetitions` field in the script header lists phrases excluded from Gate 8's duplicate detection for that session only. This replaces any global ignore list.

```
Expected-Repetitions: May I be, May you be, May they be, May all beings be
```

### Gate 9: Energy Spike Detection (Visual Report)
Generates PNG with waveform, spectrogram, energy plot, and summary. Additionally performs per-window energy analysis (1–2 second windows) to detect anomalous spikes.

**Pass condition:** No window exceeds 12× session median total energy AND no window exceeds 28× session median high-frequency energy (above 4 kHz, speech-only windows used as baseline).

**Fail condition:** Any window exceeds either threshold. Flagged timestamps and energy values included in the visual report PNG.

**Calibration note:** The HF spike threshold was recalibrated at 28× speech-only median and total energy at 12× (8 Feb 2026). No-ambient sessions have lower HF median, so sibilants appear as 16–25× spikes. Ambient sessions show sibilants at 4–8× and genuine hiss at 32–36×. The 28× HF threshold catches genuine hiss while passing sibilants in all session types. Fish per-chunk level swings can exceed 10 dB, requiring the generous 12× total energy threshold.

**History:** Previously ran as informational-only with no pass/fail condition. Changed after the loving-kindness build deployed with a catastrophic hiss wall from 12:00 onwards that was clearly visible on the Gate 9 spectrogram but not evaluated programmatically.

### Gate 10: Speech Rate Anomaly Detection
Measures word density per second across the session using sliding windows.

**Silence-aware baseline:** Session average speech rate calculated using speech-only windows. Windows below a speech energy threshold are excluded from the baseline calculation. This prevents long meditation pauses from dragging the average down and causing false positives on normal-paced speech.

**Threshold:** Flag if any 2-second window exceeds 130% of the speech-only session average.

**Meditation-specific rule:** Speech rate should be consistently slow (~100–120 wpm / 8–10 chars per second). Sudden acceleration to normal conversational pace (~160 wpm) is a defect even if the words are correct.

**Calibration note:** With silence-aware baseline, the session average sits around 3.0–3.5 words/second for meditation content. The original implementation included silence windows, dragging the average to ~2.3 w/s and producing 27 false positives per build.

### Gate 11: Silence Region Integrity
Verifies that every silence region in the manifest actually contains silence. Checks whether pause regions have been filled with audio bleed, stray TTS output, or ambient at the wrong level.

**Implementation:**
1. Reads the build manifest to identify all marked silence/pause regions and their expected durations
2. For each silence region in the RAW narration (pre-ambient mix), measures energy
3. If energy in any silence region exceeds −50 dBFS, flags it
4. For the MIXED output, verifies silence regions contain ambient-only energy (no voice bleed) by comparing energy against the ambient-only baseline level ±3 dB

**Pass condition:** All silence regions in raw narration below −50 dBFS. All silence regions in mixed output within ±3 dB of ambient-only baseline.
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

### Gate 13: Ambient Continuity
Programmatically enforces the rule that there must be no dead silence anywhere in the final track and ambient must continue through all pauses and silences.

**Implementation:**
1. Identifies all pause/silence regions in the mixed output (using the build manifest)
2. For each region, measures energy in a sliding window (1–2 seconds)
3. Checks the final 30 seconds of the file — ambient fade-out must not create dead silence before the track ends
4. Measures ambient level consistency across pause regions

**Pass condition:** All pause regions above −80 dBFS. No dead silence anywhere. Ambient energy consistent across regions (within 10 dB).
**Fail condition:** Any dead silence detected, or ambient level inconsistency exceeds 10 dB.

**Calibration note:** Dead silence threshold calibrated at −80 dBFS (not the originally proposed −55 dBFS). Quiet ambient tracks measure −72 to −77 dBFS in known-good sessions. Ambient consistency tolerance calibrated at 10 dB (not 6 dB) — known-good sessions show up to 8 dB range across pause regions.

### Gate 14: Opening Quality (Tighter Thresholds)
The opening is what the listener hears first. TTS glitches concentrate in the first 30–60 seconds. A glitch at 8:32 is bad; a glitch at 0:15 is catastrophic.

Runs the following gates with TIGHTER thresholds on the first 60 seconds of the file:

| Gate | Standard threshold | Opening threshold (first 60s) |
|------|-------------------|-------------------------------|
| Gate 1 (Quality Benchmarks) | Noise floor ≤−26 dB, HF hiss ≤−40 dB | Noise floor ≤−30 dB, HF hiss ≤−44 dB |
| Gate 6 (HF Hiss) | 6 dB ratio, 3s min | 4 dB ratio, 1s min |
| Gate 5 (Loudness) | 6.5 dB above median | 6 dB above median |
| Gate 10 (Speech Rate) | 130% of session average | 120% of session average |

**Pass condition:** All tightened thresholds met in the first 60 seconds.
**Fail condition:** Any threshold exceeded in the opening — even if the same issue would pass later in the track.

**Calibration note:** Gate 5 opening threshold calibrated at 6 dB (not the originally proposed 4 dB). Known-good sessions show 5.3 dB loudness variation in the opening.

### Overgeneration Retry Logic

If a generated chunk's duration exceeds 2× the expected duration for its character count, reject it and regenerate immediately. Up to 3 retries per chunk before flagging as build failure.

**Expected duration:** Character count ÷ speaking rate. Meditation speaking rate ≈ 100–110 wpm ≈ 8–10 characters per second.

### Visual QA Report Inspection (Mandatory)

The build script generates QA report PNGs for each session (`{session-name}_QA_REPORT.png`). These contain waveform visualisations, spectrograms, energy plots, and gate summaries. **Code must visually inspect these reports — not just check the pass/fail numbers.**

**Why this exists (9 Feb 2026):** Code confirmed it generated QA report PNGs but never actually opened or inspected them. Gates ran programmatically and Code took the numbers at face value. A spectrogram can show anomalies (localised hiss bursts, tonal shifts, energy spikes) that fall just below a gate's numerical threshold but are clearly visible on the graph. Automated gates are necessary but not sufficient — the visual reports exist to catch what the numbers miss.

**Code's obligations:**
1. After every build, open each QA report PNG and examine the spectrogram for anomalies
2. Flag any visible artefacts that passed the numerical gates — include a description and timestamp
3. Include visual inspection findings in the build state file
4. If a visible anomaly is significant, report it to Scott rather than auto-deploying

**What to look for:**
- Localised bright spots or bands on the spectrogram (hiss or energy spikes)
- Sudden changes in spectral colour at chunk boundaries (tonal seams)
- Unusual waveform shapes (clipping, dropout, overgeneration)
- Energy plot spikes that are close to (but just below) gate thresholds

This is not a gate — it does not block deployment programmatically. It is a mandatory inspection step that Code performs and documents.

### Threshold Calibration Reference

These thresholds were calibrated against two known-good deployed sessions (25-introduction-to-mindfulness, 36-loving-kindness-intro) on 7 February 2026. They represent production-validated values, not theoretical estimates.

| Gate | Parameter | Brief estimate | Calibrated value | Evidence |
|------|-----------|----------------|------------------|----------|
| Gate 3 | HF sliding window | 10 dB | 18 dB | Natural speech HF up to 17 dB above reference |
| Gate 9 | HF spike threshold | 4× all-window median | 28× speech-only median (HF), 12× total | No-ambient sibilants at 16–25×, genuine hiss at 32–36× |
| Gate 13 | Dead silence | −55 dBFS | −80 dBFS | Quiet ambient at −72 to −77 dBFS |
| Gate 13 | Ambient consistency | 6 dB | 10 dB | 8 dB range on known-good session |
| Gate 14 | Loudness (opening) | 4 dB | 6 dB | 5.3 dB on known-good session |

---

## 13. Script Writing Rules

### Block Size

| | Characters |
|---|---|
| **Minimum** | **50** (below 50 causes TTS instability and hiss — root cause of all hiss failures) |
| **Sweet spot** | 50–200 |
| **Maximum** | 400 (longer blocks trend toward monotone) |

Blocks under 50 characters must be merged with adjacent blocks or expanded with additional content.

**For loving-kindness/mantra content:** Combine 3–4 short phrases into one block with internal ellipses. Each block 76–150 characters. This gives TTS enough context while ellipses create internal rhythm.

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
| default | 8s | 25s | 50s |

### Script Rules

| Rule | Why |
|------|-----|
| All blocks **50–400 characters** | Under 50 causes hiss; over 400 causes monotone |
| Combine short phrases with lead-in text | "May I be safe." (14 chars) → "Silently now, may I be safe." (28 chars) — still needs combining further to reach 50 |
| Use `...` for pauses (not `—`) | Script parser reads `...` as pause markers |
| No ellipsis in spoken text | Fish renders `...` as nervous/hesitant delivery |
| Scripts must contain ZERO parenthetical tags | In-text emotion tags don't work (see Section 18) |
| Estimate ~7.2 chars/second for narration duration | Calibrated from Fish/Marco output. **Caveat (9 Feb 2026):** This estimate tends to overestimate session duration — session 32 was scripted for 12 min but TTS produced 9.5 min. The build script's own duration estimate (calculated from actual chunk generation) is more reliable than the character-based formula. Use 7.2 chars/sec for rough planning only; set the `Duration-Target` header based on the build script's estimate after a dry run, not on character count alone. |

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

Certain words cause consistent artifacts in Fish/Marco output. Most are sibilant-heavy words or sustained vowels — exactly where Fish struggles to hold a clean, gentle tone. These appear constantly in meditation scripts, making this a high-impact issue.

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
| be (standalone) | voice shift | Embed in longer phrases — never isolate |
| breath in | hiss | breathe in, inhale, draw a breath |
| filling your lungs completely | hiss | Rewrite as shorter phrase — "breathe in fully" |
| nowhere else | voice shift | "right here", "all you need is to be here" |

**Pattern:** Most triggers are soft, sibilant-heavy words or words with sustained vowels where Fish needs to hold a gentle, open tone. These are the exact words that appear constantly in meditation content.

**Workarounds:**
- Use synonyms from the table above
- Break the word into a longer phrase where it's less exposed (e.g. "deeply" alone is worse than "more deeply now")
- If a trigger word is essential to the meaning and has no good synonym, ensure it falls within a block of 100+ characters so the TTS has surrounding context to stabilise

**Pre-flight scan:** The build script includes an automated pre-flight check that scans all script blocks against this list before any TTS calls. Blocks containing trigger words are flagged with suggested alternatives. This runs during dry-run and at the start of a live build. It is a WARNING, not a build-blocker — some trigger words may be unavoidable, but the scriptwriter should make a conscious choice rather than discovering the problem at the listening stage.

**Maintaining the list:** New trigger words discovered during human review are added to this table with their defect type and suggested alternatives. The pre-flight scan reads from this list. The list is expected to grow as more sessions are built and reviewed.

---

## 13A. Script Uniqueness & Cross-Session Differentiation

### The Problem

Salus sessions are starting to sound the same. A customer who listens to two or three sessions back-to-back should feel like they've had three distinct experiences — not the same session with different words in the middle. When openings blur together, when every session guides the breath the same way, when the same transitional phrases appear across the catalogue, the product feels mass-produced rather than crafted.

This is the single biggest threat to perceived quality that doesn't show up in any automated gate. A session can pass all 14 QA checks and still feel identical to the one before it.

**The rule is simple: no two Salus sessions should feel interchangeable.** Every session must have its own identity — its own way in, its own rhythm, its own voice, its own way of closing. A returning customer should be able to tell which session they're listening to within the first 30 seconds.

### Cross-Session Registers (Mandatory)

Three register files track what has already been used across the catalogue. These are the primary tool for preventing internal repetition. They live in `content/scripts/` and are checked before every new script enters the build pipeline.

#### `openings-register.txt`

Every deployed session's opening line and opening approach, one entry per line.

Format: `[Session #] | [Opening line] | [Opening technique]`

**Rule:** No new session may use the same opening technique as any existing session in the register. If three sessions already open with breath awareness, the next session must open differently — perhaps with a sound observation, a question, a brief story, a sensory detail, or silence.

#### `closings-register.txt`

Every deployed session's closing line and closing approach.

Format: `[Session #] | [Closing line] | [Closing technique]`

**Rule:** No new session may use the same closing technique as any session in the same category. Across categories, closings should still vary as much as possible. Sleep sessions all end with "Goodnight from Salus" (per existing rules), but the lead-in to that line must differ every time.

#### `phrases-register.txt`

Distinctive phrases, metaphors, breath cues, and transitional language used across all deployed sessions.

Format: `[Session #] | [Phrase or cue] | [Context]`

**Rule:** No phrase of 5+ words from this register may appear in a new script. If a phrase has been used, it's spent — find a new way to say it.

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
- Open mid-action — no settling, just start the practice
- Open with a single sensory detail (a sound, a temperature, a texture)
- Open with a brief, unexpected statement that sets the session's theme
- Open with silence — let the ambient carry the first few seconds before the voice enters

**Mandatory:** Before writing any opening, check `openings-register.txt`. If the planned approach is already there, change it.

#### 2. Breath Cues

Every meditation involves breathing. The risk is that every session guides the breath using identical language.

**What tends to repeat:**
- "Breathe in... breathe out"
- "Notice your breath" / "Bring your attention to your breathing"
- "Take a deep breath in through your nose"
- "With each exhale, let go of..."

**Variation strategies:**
- Describe the breath indirectly — talk about what it does to the body rather than instructing the mechanism
- Vary the sensory focus: one session might notice temperature of air at the nostrils, another might notice the rise of the chest, another the sound of the exhale
- Some sessions can skip explicit breath guidance entirely and let the pacing of the script imply the rhythm
- Use different verbs: draw, gather, release, soften, empty — not always "breathe in/out"
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
- Skip the full body scan — focus on one or two areas with genuine depth
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
- End abruptly — some sessions can simply trail off into ambient, letting the listener decide when they're done
- End with a specific, practical suggestion: "The next time you're waiting in a queue, try this for thirty seconds"
- End with humour or lightness where the session type allows it

**Mandatory:** Before writing any closing, check `closings-register.txt`. If the planned approach is already there, change it.

#### 6. Structural Arc

Even if individual phrases differ, sessions can feel identical if they follow the same structural shape every time.

**The default arc (overused):**
Settle → breathe → body awareness → core practice → integration → close

**Variation strategies:**
- Start in the core practice immediately — no preamble
- Move between activity and stillness rather than building linearly toward stillness
- Use a circular structure — return to the opening image or phrase at the end
- Use a single extended metaphor as the structural spine rather than a technique sequence
- Vary the ratio of guidance to silence — some sessions should be 70% guided, others 40%
- Place the most intense or meaningful moment somewhere unexpected — not always at the two-thirds mark

### Pre-Build Originality Scan (Automated)

The build script runs a cross-session originality scan during the pre-flight phase, alongside the existing trigger word check and block-size validation.

**The scan:**
1. Loads all three register files (`openings-register.txt`, `closings-register.txt`, `phrases-register.txt`)
2. Extracts all text blocks from the new script
3. Compares each block against register entries using fuzzy matching (threshold: 70% similarity on any phrase of 5+ words)
4. Flags matches with the specific session number and phrase that conflicts
5. Checks the opening line and closing line against their respective registers — exact or near-exact matches are flagged
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

This is lighter-touch than the internal register system — a due diligence step, not a gating mechanism.

### Exceptions

Some repetition across sessions is unavoidable and acceptable:

- **Traditional formulations** (e.g., metta phrases "May I be safe, may I be happy") — these are traditional, not anyone's property, and listeners expect consistency in how they're presented
- **Functional micro-instructions** (e.g., "breathe in," "close your eyes") — unavoidable, though the framing around them must vary
- **Category conventions** (e.g., sleep sessions ending with "Goodnight from Salus") — brand signatures, not repetition
- **Phrases listed in `Expected-Repetitions` metadata** — intentional structural repetition within a single session (handled by Gate 8)

The key distinction: **functional language can repeat; creative language must not.** "Breathe in" is functional. "Let your breath become a soft tide, washing through you" is creative — and once it's been used in one session, it's done.

### Narration Audit (Outstanding)

**Status:** PENDING — to be scheduled

A full audit of all deployed sessions is required to retroactively populate the three register files and identify existing cross-session repetition. This is a prerequisite for the register system to function properly.

**Scope:**
1. Retrieve or reconstruct scripts for all deployed sessions (01, 03, 05, 06, 07, 08, 09, 11, 18, 19, 23, 25, 29, 32, 36, 38, 43)
2. Extract opening lines, closing lines, and distinctive phrases from each
3. Populate `openings-register.txt`, `closings-register.txt`, and `phrases-register.txt`
4. Identify any existing cross-session repetition — document which sessions share phrasing and flag for future rewrites
5. Listen to a representative sample across categories back-to-back and note where sessions feel interchangeable
6. Produce an audit report with specific recommendations for which scripts need the most differentiation work

**Priority:** Must be completed before any new scripts are written. The registers are worthless if they don't include existing content.

---

## 14. Expression Through Punctuation

**Status:** ACTIVE — Technique proven, deployed in loving-kindness session.

### The Problem

TTS at temperature 0.3 is deliberately flat. Marco sounds the same whether saying "close your eyes" or "you are deeply loved." Increasing temperature adds instability and artefacts. Temperature is not the solution.

### The Solution: Script-Level Direction

Every comma, ellipsis, fragment, and sentence structure is vocal direction to Marco. The TTS model responds to punctuation cues — not perfectly, but enough to create natural rhythm and breathing. No API changes, no model tuning, no extra cost. Just better scripts.

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
> 76–84 characters per block. Ellipses create breathing rhythm without splitting into dangerously short chunks.

---

## 15. Auphonic Integration

**Status:** ACTIVE — Measurement gate AND hiss reduction testing (see Hiss Reduction Testing below). Processing output is not currently used as production audio, but noise reduction is under evaluation.

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
| Input SNR | ≥ 40 dB | < 40 dB |
| Background Level | ≤ −55 dB | > −55 dB |
| Hum detected | No | Yes (any segment) |
| Output loudness | −26 ±1.0 LUFS | Outside range |
| Output true peak | ≤ −2.0 dBTP | > −2.0 dBTP |
| Output LRA | ≤ 16 LU | > 16 LU |
| Leveler gain spread | ≤ 10 dB | > 10 dB |

SNR threshold at 40 dB based on Fish baseline of 45.26 dB. The old 25 dB threshold was too permissive for TTS content.

### Per-Segment Analysis

**Status: NOT AVAILABLE.** The Auphonic API does not return per-segment SNR data — only aggregate file-level metrics. Per-segment analysis was planned but cannot be implemented as a pipeline gate due to this API limitation. If Auphonic exposes per-segment SNR in a future API version, this should be revisited.

Whole-file Auphonic metrics remain in use as a secondary measurement gate alongside the 14-gate pipeline system.

### Auphonic Preset Settings

| Setting | Value |
|---------|-------|
| Adaptive Leveler | Enabled |
| Filtering | Enabled (Voice AutoEQ) |
| Loudness Target | −26 LUFS |
| Max Peak Level | −2 dBTP (ATSC A/85) |
| Noise Reduction | Static: remove constant noises only, 6 dB (low) |
| Remove Reverb | Off |
| Automatic Cutting | Off (preserve meditation silences) |
| Output Format | WAV 16-bit PCM, optimal stereo |

**Note:** The "silent segments >30s" warning is a FALSE POSITIVE for meditation content. Ignore it.

### First Baseline Results (7 February 2026)

File: `36-loving-kindness-intro_precleanup.wav`

| Metric | Value |
|--------|-------|
| Program Loudness | −16.34 LUFS |
| LRA | 15.21 LU |
| Max Peak Level | −4.39 dBTP |
| SNR mean | 45.26 dB |
| Background Level | −62.25 dB |
| Hum | Not detected |

**Key conclusion:** Fish Audio TTS output is broadcast quality (40–50 dB SNR standard). The aggressive cleanup chain was solving a problem that barely existed.

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

### Hiss Reduction Testing (Outstanding)

**Status:** PENDING — to be tested

The pipeline currently has no active de-hiss step. Hiss mitigation relies entirely on chunk selection (best-of-5 scoring includes HF measurement, so cleaner chunks are preferred) and ambient masking. If all 5 generations of a chunk have hiss and that chunk was still the best, the hiss ships.

**LALAL.AI** was tested for noise cancellation. Hiss removal was excellent, but dereverb stripped Marco's vocal resonance. LALAL with `dereverb=False` (noise cancellation only) was identified as worth retesting but has not been tested.

**Auphonic** has noise reduction capabilities (currently configured as "Static: remove constant noises only, 6 dB") but has only been used for measurement, never for processing. The concern was that Voice AutoEQ damages Marco's bass warmth — but it's possible to use Auphonic's noise reduction independently of its levelling and EQ features.

**Required testing:**
1. **LALAL.AI with dereverb disabled** — noise cancellation only on a known-hissy chunk. A/B against the original.
2. **Auphonic noise reduction only** — submit a known-hissy chunk with levelling and EQ disabled, noise reduction enabled. Compare output quality.
3. **Per-chunk application** — test whether applying noise reduction to individual problem chunks (rather than the whole narration) avoids the cumulative quality degradation seen in full-session LALAL processing.

The goal is to find a noise reduction approach that removes hiss without damaging Marco's vocal character. If either LALAL (dereverb-off) or Auphonic (noise-only) passes A/B testing, it becomes an optional repair tool — applied to specific problem chunks identified during review, not blanket-applied to all audio.

---

## 15A. Targeted Chunk Repair

**Status:** EXPERIMENTAL — trial on session 32, pending results before integration into standard pipeline.

### The Problem

The current quality strategy is avoidance, not repair. Generate 5 versions of each chunk, pick the best one, hope the ambient covers the rest. If all 5 versions of a chunk have a defect, the least-bad version ships with the defect intact. There is no mechanism to fix a single problem word or phrase after assembly.

This was acceptable when defect rates were high and the pipeline was unstable. Now that the pipeline produces 3–4 defective words across four full sessions, targeted repair becomes viable — and valuable. Fixing 3 words is faster than regenerating an entire 27-chunk session and gambling on the Fish lottery again.

### The Concept

Identify the specific word or phrase that is defective. Regenerate just that audio segment. Splice it into the existing narration with proper crossfading and tonal matching. Save the result as a new file — never overwriting the original master narration.

**This is NOT the crude splicing that Rule 11 prohibits.** The previous splicing failure was caused by dropping in a raw replacement chunk with no tonal matching or crossfading, creating audible seams. Targeted repair is a controlled process with quality checks at every step.

### Repair Process

1. **Identify the defect.** Human review notes the problem word/phrase with timestamp (e.g., "0:42 — 'something' has echo"). The defect must be specific — not "this chunk sounds off" but "the word 'something' at 0:42 has audible echo."

2. **Locate the chunk.** Using the build manifest and the session's chunk schedule (stored alongside the master narration in `content/audio-free/masters/{session}_chunk-schedule.txt`), identify which chunk contains the defective word and the exact timestamp within that chunk. Chunk schedules list every chunk's start time, end time, duration, and opening text — making it straightforward to find a problem word without reverse-engineering from raw timestamps.

3. **Extract context.** Extract the full chunk containing the defect from the master narration, plus the adjacent chunks on either side. These provide the tonal reference for matching.

4. **Regenerate the chunk.** Generate multiple versions (best-of-10) of the defective chunk using the same TTS settings as the original build. Use adjacent chunks as voice conditioning reference if the TTS API supports it. Score all versions using the composite metric, with MFCC tonal distance weighted heavily against the adjacent chunks to ensure tonal consistency. **Important:** Always regenerate the full chunk, not just the defective word in isolation — a word generated standalone has different prosody (pitch contour) than a word mid-sentence, and would sound obviously spliced.

5. **Select and validate.** Pick the best replacement. A/B compare the replacement chunk against the original — the replacement must be better on the specific defect without introducing new problems.

6. **Splice with crossfading.** Replace the defective chunk in the narration using cosine crossfades at both boundaries (minimum 50ms, up to 200ms depending on context). The crossfade duration should be longer at silence-to-speech transitions and shorter at mid-speech splices.

7. **MFCC tonal check.** Run MFCC comparison between the replacement and its adjacent chunks. If tonal distance exceeds the existing threshold (0.50), the replacement fails — try another version or accept the original defect.

8. **Re-run QA gates.** Run all 14 gates on the repaired narration. The repair must not cause any gate that previously passed to now fail.

9. **Save as new file.** Save the repaired narration as `{session-name}_master-narration-repair-{n}.wav` (where n is the repair iteration number). The original master narration stays untouched.

10. **Remix and deploy.** Apply ambient mix to the repaired narration and deploy to R2. Update all HTML references if the filename has changed.

### File Naming

```
content/audio-free/masters/
  32-observing-emotions_master-narration.wav          ← original, sacrosanct
  32-observing-emotions_master-narration-repair-1.wav ← first repair attempt
  32-observing-emotions_master-narration-repair-2.wav ← second repair if needed
```

The live deployed MP3 is always generated from the most recent approved narration (original or repair). But all versions are kept — you can always go back.

### Rules

1. **Never overwrite the original master narration.** This is non-negotiable. The repair creates a new file. The original remains as the fallback.
2. **One defect per repair pass.** Fix one problem, re-run QA, listen, confirm. Don't batch multiple repairs before checking — each splice introduces risk and the risks compound.
3. **Repair attempts are limited.** If a chunk cannot be satisfactorily repaired after 3 attempts, accept the original or schedule a full rebuild of the session.
4. **All repairs documented.** The build record must log: which word was repaired, the timestamp, the replacement chunk's composite score and MFCC tonal distance, and the A/B comparison result.
5. **Repaired narrations go through the same QA gates as originals.** A repair that passes human review but fails Gate 7 (surge) is not acceptable.
6. **Code must identify defects, not just fix reported ones.** Over time, Code should develop the ability to flag potential defects programmatically (via spectral analysis, MFCC anomaly detection, or Whisper transcription comparison) and propose repairs — not wait for human reports. This is the path to an automated repair gate.

### Future: Repair as a Pipeline Stage

Once targeted repair is proven on manual cases, the goal is to integrate it as an optional post-assembly stage:

1. Build assembles narration as normal (best-of-5 per chunk)
2. Automated analysis identifies chunks with potential defects (spectral anomalies, MFCC outliers, Whisper transcription mismatches)
3. Those chunks are flagged for repair — regenerated with best-of-10 and spliced in with crossfading
4. Repaired narration goes through full 14-gate QA
5. Human review confirms the final result

This would mean the pipeline produces a first-pass narration, then refines it — avoidance AND repair working together. But this is aspirational. The immediate task is proving the concept on a single word.

---

## 16. Build Execution

### CLI Usage

```bash
# Full pipeline: build → QA → deploy to R2
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
- [ ] All text blocks 50–400 characters (MINIMUM 50, not 20)
- [ ] Short phrases combined to exceed 50 chars
- [ ] Pauses humanised (no identical gap durations)
- [ ] Zero parenthetical emotion tags in text
- [ ] `Expected-Repetitions` set if session has intentional structural repetition
- [ ] **Trigger word pre-flight passed** — script scanned against known trigger word list (Section 13). Any flagged words either replaced with synonyms or consciously accepted
- [ ] **Cross-session originality scan passed** — script checked against registers (Section 13A). No unresolved conflicts with existing openings, closings, or phrases

**Environment:**
- [ ] Only building ONE session (no parallel builds)
- [ ] Provider set to `fish` (default) or `resemble` as appropriate
- [ ] `FISH_API_KEY` / `RESEMBLE_API_KEY` set in `.env`
- [ ] `RESEND_API_KEY` set in `.env`
- [ ] `AUPHONIC_USERNAME` / `AUPHONIC_PASSWORD` set in `.env`
- [ ] Master reference WAV exists at `content/audio/marco-master/marco-master-v1.wav`

**Build:**
- [ ] Dry run completed — block count and silence totals verified
- [ ] Ambient file duration exceeds estimated voice duration
- [ ] If no long ambient exists, download one BEFORE building

**Quality:**
- [ ] All 14 QA gates run
- [ ] 0 voice changes in QA results

**Human Review (mandatory before deploy):**
1. Build script generates QA report PNGs — Code must visually inspect these for spectral anomalies, energy spikes, or artefacts that pass numerical thresholds but are visible on the graphs (see Visual QA Report Inspection below)
2. Scott listens to the full assembled session (with ambient) as a continuous playback — not individual chunks. Focus on overall flow, tonal consistency, and any words or phrases that stand out as defective
3. Any problem moments noted with approximate timestamps and description (e.g., "0:42 — 'something' has echo")
4. If clean and no issues noted → proceed to deploy
5. If specific defects identified → attempt targeted repair (Section 15A) before considering a full rebuild
6. Export review notes as TXT file for the build record

**Previous approach (superseded 9 Feb 2026):** Individual chunk-by-chunk listening with per-chunk ratings. This was necessary during early pipeline development when defect rates were high. With the current pipeline producing 3–4 defective words across four full sessions, full-session playback is sufficient and more representative of the customer experience.

**Deployment:**
- [ ] Final audio remixed with ambient at per-session level (set by ear — see Ambient Rules in Section 11). Dynamic masking applied to problem chunks if needed.
- [ ] Final MP3 uploaded to Cloudflare R2 (NOT committed to git)
- [ ] Audio plays from `media.salus-mind.com` URL (test on both desktop AND mobile)
- [ ] CORS verified: `Access-Control-Allow-Origin` header present in response
- [ ] Website HTML updated — ALL pages referencing the session (listing pages, detail pages, mindfulness cards)
- [ ] Players wired up with `data-src` attribute pointing to correct R2 URL
- [ ] HTML changes committed and pushed to main
- [ ] Email sent to scottripley@icloud.com
- [ ] `openings-register.txt` updated with new session's opening line and technique
- [ ] `closings-register.txt` updated with new session's closing line and technique
- [ ] `phrases-register.txt` updated with new session's distinctive phrases, metaphors, and cues
- [ ] **Session production record created/updated** — see template below

### Session Production Record

Every deployed session has a production record — a single markdown file that captures the complete history of that session's production. This is the session's "mini bible": everything you need to know about what was built, how, what went wrong, and what the current state is.

**Location:** `content/audio-free/masters/{session-name}_production-record.md`

**Created:** At the start of the build process (populated with script details and build settings).
**Updated:** After every build attempt, repair, remix, or redeployment.
**Never deleted:** Even if a session is rebuilt from scratch, the old production record is archived and a new one started.

**Template:**

```markdown
# Production Record: {Session Name}

## Identity
- **Session #:** {number}
- **Title:** {full title}
- **Category:** {sleep/mindfulness/stress/focus/beginner/advanced/course/compassion}
- **Duration target:** {minutes}
- **Actual duration:** {minutes}
- **Ambient:** {type and level}
- **Script file:** {path}
- **Bible version at build:** {version}

## Current Deployment
- **Status:** {Live / Not deployed / Replaced}
- **R2 path:** {url}
- **Commit:** {hash}
- **Date deployed:** {date}
- **Based on:** {master narration / repair-N}

## Master Files
- **Master narration:** {path to _master-narration.wav}
- **Chunk schedule:** {path to _chunk-schedule.txt}
- **QA report:** {path to _QA_REPORT.png}
- **Script version:** {v1/v2/rewritten — note what changed}

## Build History
| Build | Date | Result | Gates | Notes |
|-------|------|--------|-------|-------|
| 1 | {date} | {PASS/FAIL} | {14/14 or which failed} | {details} |
| 2 | {date} | {PASS/FAIL} | {14/14 or which failed} | {details} |

## Repairs
| Repair | Date | Defect | Chunk | Word | Result | Notes |
|--------|------|--------|-------|------|--------|-------|
| 1 | {date} | {echo/hiss/voice} | {#} | {word} | {SUCCESS/FAIL} | {details} |

## Known Issues
- {Any accepted defects, timestamps, and severity}
- {Any chunks flagged during review but shipped}

## Human Review Notes
- {Date}: {Notes from Scott's listening review}

## Hiss Reduction
- {Any cleaning applied, method, before/after comparison}

## Script Changes
- {Date}: {What changed and why — trigger words, rewrites, etc.}
```

**Why this exists:** Session-level information was previously scattered across manifests, build logs, state files, the Bible's deployed sessions table, and conversation history. When a session needs repair, remix, or rebuild months from now, the production record contains everything needed — no archaeology required.

**Code's obligation:** The production record is created at the start of the first build and updated after every significant action. It is not optional. A session without a production record is incomplete.

**Retroactive population:** For the 10 currently deployed sessions, production records should be created using available data (manifests, build logs, chunk schedules, the deployed sessions table). Where historical data is incomplete (especially for pre-v1.3 sessions), note what's missing rather than guessing.

### Email Notification System

| | |
|---|---|
| **Service** | Resend API (free tier, 100 emails/day) |
| **Env var** | `RESEND_API_KEY` in `.env` |
| **Sender** | `onboarding@resend.dev` (switch to `build@salus-mind.com` after domain verification) |
| **Recipient** | `scottripley@icloud.com` |
| **Header** | Uses `curl` subprocess (Python `urllib` blocked by Cloudflare bot protection) |
| **Trigger** | Every completed build — pass or fail |

### Build Status (Full Catalogue)

*Last updated: 9 February 2026*

#### Deployed Sessions (10)

| # | Session | Category | Duration | Provider | Ambient | Raw WAV | Flagged | Status |
|---|---------|----------|----------|----------|---------|---------|---------|--------|
| 01 | Morning Meditation | Beginner | ~10 min | Fish | — | N | no QA | Deployed, patched. Pre-v1.0 — rebuild candidate. |
| 03 | Breathing for Anxiety | Stress | 19.3 min | Fish | — | Y | no QA | Deployed, patched. v2.1 — pre-v3.0 thresholds. |
| 09 | Rainfall Sleep Journey | Sleep | ~30 min | Fish | — | N | no QA | Deployed, patched. Pre-v1.3 — rebuild candidate. |
| 18 | Calm in Three Minutes | Stress | 3.2 min | Fish | rain | Y | 0/12 | Deployed (build 1, 14/14 gates, 9 Feb, commit 752752f). |
| 19 | Release and Restore | Stress | 14.5 min | Fish | garden | Y | 2/51 | Deployed (build 4, 14/14 gates, 9 Feb, commit 752752f). |
| 23 | The Calm Reset | Stress | 5.5 min | Fish | stream | Y | 1/19 | Deployed (build 1, 14/14 gates, 9 Feb, commit 752752f). |
| 25 | Introduction to Mindfulness | Beginner | 14.4 min | Fish | garden | Y | 4/36 | Deployed (rebuild 8 Feb). ⚠️ Card wiring broken. |
| 32 | Observing Emotions | Mindfulness | 9.5 min | Fish | garden | Y | 2/23 | Deployed (build 3, 14/14 gates, 9 Feb, commit 752752f). |
| 36 | Loving-Kindness Intro v3 | Compassion | ~12 min | Fish | birds | Y | 1/27 | Deployed (v3b focused rebuild, best-of-10, 14/14 gates). |
| 38 | Seven-Day Mindfulness Day 1 | Course | 11.6 min | Fish | — | N | no QA | Deployed, patched. Pre-v1.3 — rebuild candidate. |

**Flagged** = chunks scoring below 0.50 composite / total chunks. "no QA" = built before per-chunk scoring existed.

**Sessions built on old Bible (candidates for rebuild):**
- 01, 09, 38 — pre-v1.3, no raw WAV preserved, no per-chunk QA, no 14-gate system
- 03 — v2.1, has raw WAV but pre-v3.0 gate thresholds

#### Flagged Chunks (Repair Candidates)

10 flagged chunks across 5 sessions out of 345 total chunks scanned. Sessions 01, 03, 09, 38 have no QA data (pre-scoring era). Session 18 passed clean (0/12 flagged).

| Session | Chunk | Score | Hiss (dB) | Text (opening) |
|---------|-------|-------|-----------|----------------|
| 19 — Release and Restore | 31 | 0.348 | −13.47 | "Your neck. Gently press your head back into whatever is..." |
| 19 — Release and Restore | 51 | 0.209 | −9.43 | "This has been Salus. Go gently, and take this calm with..." |
| 23 — The Calm Reset | 13 | 0.426 | −10.67 | "Now imagine all the stress you have accumulated today a..." |
| 25 — Intro to Mindfulness | 1 | 0.365 | −7.26 | "This is a simple introduction to mindfulness. There is ..." |
| 25 — Intro to Mindfulness | 3 | 0.349 | −10.26 | "Find somewhere comfortable to sit or lie down, and let ..." |
| 25 — Intro to Mindfulness | 5 | 0.430 | −8.54 | "Let's start with your breath. Not because it's special,..." |
| 25 — Intro to Mindfulness | 12 | 0.232 | −8.35 | "You don't need to stop your thoughts. You just need to ..." |
| 32 — Observing Emotions | 1 | 0.449 | −10.51 | "Today we are going to practise something that might see..." |
| 32 — Observing Emotions | 12 | 0.325 | −10.19 | "Stay with that sensation. Do not try to make it go away..." |
| 36 — Loving-Kindness v3 | 7 | 0.378 | −10.04 | "There is nothing to force here. No emotion you need to ..." |

These are the primary repair candidates once targeted repair is proven. Session 25 has the highest concentration (4 flagged chunks, including the opening chunk at −7.26 dB hiss — the worst hiss reading across all sessions).

#### Cards on Site With No Working Audio

These session cards are visible to customers but have no audio behind them. Pressing play does nothing. Each needs either building or removing from the site.

| # | Session | Notes |
|---|---------|-------|
| 05 | Body Scan for Deep Rest | No audio |
| 06 | Letting Go of the Day | No audio |
| 07 | Moonlight Drift | No audio |
| 08 | The Quiet Shore | No audio |
| 11 | Lucid Dream Preparation | No audio |
| 25 | Introduction to Mindfulness | HAS audio — card wiring broken (old `player` class) |
| 29 | Open Awareness | No audio |
| 43 | Non-Dual Awareness | No audio |

#### Not Yet Produced (42 sessions)

| # | Session | Category | Script | Status |
|---|---------|----------|--------|--------|
| 00 | Landing Page | Intro | Y | Old ElevenLabs, deleted |
| 02 | Deep Sleep | Sleep | Y | Old ElevenLabs, deleted |
| 04 | Science of Mindfulness | Education | Y | Rewritten for liability, needs regen |
| 05 | Body Scan for Deep Rest | Sleep | Y | Old ElevenLabs, deleted. Card on site |
| 06 | Letting Go of the Day | Sleep | Y | Old ElevenLabs, deleted. Card on site |
| 07 | Moonlight Drift | Sleep | Y | Old ElevenLabs, deleted. Card on site |
| 08 | Sleep Stories: Quiet Shore | Sleep Story | Y | Had ambient, deleted, needs regen. Card on site |
| 10 | Counting Down to Sleep | Sleep | Y | Old ElevenLabs, deleted |
| 11 | Lucid Dream Preparation | Advanced | Y | Old ElevenLabs, deleted. Card on site |
| 12 | Five Minute Reset | Focus | Y | Old ElevenLabs, deleted |
| 13 | Flow State | Focus | Y | Modified for liability, needs regen |
| 14 | Morning Clarity | Focus | Y | Old ElevenLabs, deleted |
| 15 | Deep Work Prep | Focus | Y | Old ElevenLabs, deleted |
| 16 | Peak Performance | Focus | Y | Old ElevenLabs, deleted |
| 17 | Deep Work Mode | Focus | Y | Old ElevenLabs, deleted |
| 20 | Tension Melt | Stress | Y | Old ElevenLabs, deleted |
| 21 | Anxiety Unravelled | Stress | Y | Old ElevenLabs, deleted |
| 22 | Releasing Tension | Stress | Y | Old ElevenLabs, deleted |
| 24 | Anger & Frustration Release | Stress | Y | Old ElevenLabs, deleted |
| 26 | Body Scan Meditation | Mindfulness | Y | Old ElevenLabs, deleted |
| 27 | Mindful Breathing | Mindfulness | Y | Old ElevenLabs, deleted |
| 28 | Letting Go of Thoughts | Mindfulness | Y | Old ElevenLabs, deleted |
| 29 | Open Awareness | Mindfulness | Y | Old ElevenLabs, deleted. Card on site |
| 30 | Mindful Walking | Mindfulness | Y | Old ElevenLabs, deleted |
| 31 | Mindfulness at Work | Mindfulness | Y | Had ambient, deleted, needs regen |
| 33 | Morning Mindfulness | Mindfulness | Y | Old ElevenLabs, deleted |
| 34 | Mindful Eating | Mindfulness | Y | Old ElevenLabs, deleted |
| 35 | Your First Meditation | Beginner | Y | Had ambient, deleted, needs regen |
| 37 | Building a Daily Practice | Beginner | Y | Old ElevenLabs, deleted |
| 39 | Yoga Nidra | Advanced | Y | Never produced |
| 40 | Gratitude Before Sleep | Sleep | Y | Old ElevenLabs, deleted |
| 41 | Vipassana Insight | Advanced | Y | Never produced |
| 42 | Chakra Alignment | Advanced | Y | Old ElevenLabs, deleted |
| 43 | Non-Dual Awareness | Advanced | Y | Old ElevenLabs, deleted. Card on site |
| 44 | Transcendental Stillness | Advanced | Y | Old ElevenLabs, deleted |
| 45 | Seven-Day Mindfulness Day 2 | Course | Y | Old ElevenLabs, deleted |
| 46 | Seven-Day Mindfulness Day 3 | Course | Y | Old ElevenLabs, deleted |
| 47 | Seven-Day Mindfulness Day 4 | Course | Y | Old ElevenLabs, deleted |
| 48 | Seven-Day Mindfulness Day 5 | Course | Y | Old ElevenLabs, deleted |
| 49 | Seven-Day Mindfulness Day 6 | Course | Y | Old ElevenLabs, deleted |
| 50 | Seven-Day Mindfulness Day 7 | Course | Y | Old ElevenLabs, deleted |
| 51 | Sleep Stories: Ocean Voyage | Sleep Story | Y | Had ambient, deleted, needs regen |
| — | Founder Intro | Special | Y | Never produced |

**Summary:** 52 scripts total. 10 deployed (Fish). 7 have raw narrations on disk. 33 old ElevenLabs (all deleted). 2 need regen (liability rewrite). 4 need regen (had ambient, deleted). 3 never produced.

---

## 17. Governance

### Stop Rules

```
Autonomy Level: FULLY AUTONOMOUS — except where a STOP rule is triggered.
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

Every QA gate must have a defined pass/fail condition that blocks deployment on failure. A gate that runs, produces data, and allows the build to proceed regardless is worse than no gate — it creates false confidence. This principle was established after two incidents where the pipeline generated clear visual evidence of defects and failed to act on it.

### No Threshold Loosening Without Approval

Gate thresholds must not be adjusted to make a failing build pass. If a gate catches too many issues, the correct response is to fix the root cause (e.g. script blocks below 50 characters producing hiss at boundaries), not to widen the threshold until the problems fall below it. Any threshold change requires human approval before implementation.

**Incident (7 Feb 2026):** Code raised Gate 6 min_duration from 3s to 5s mid-build because 11 regions at 3–4.5s were failing. The root cause was a script chunk at 48 characters — below the 50-character minimum known to cause hiss. Code chose to loosen the gate rather than fix the script. Reverted on instruction.

### Build State Persistence

All build state must be persisted to a file after every step. Never rely on conversation context for:
- Strike counter
- Build sequence number
- QA pass/fail results per gate
- Which script version is being built

**Reason:** Context compaction at 200K tokens is lossy. If Code compacts mid-build, it can lose track of state. Persistent state files survive compaction.

### Brief Lifecycle

Briefs are temporary instruction documents. They exist to direct Code, then get absorbed into the bible. A brief is not a permanent reference — it has a lifecycle.

```
DRAFT → ACTIVE → INTEGRATED → ARCHIVED
```

| Stage | Meaning |
|-------|---------|
| DRAFT | Being written by Claude Desktop. Not yet issued to Code. |
| ACTIVE | Issued to Code. This is the current work order. |
| INTEGRATED | All content absorbed into the bible. Brief is now redundant. |
| ARCHIVED | Moved to `docs/archive/`. No longer referenced by any active process. |

**Rules:**

1. **One active brief per workstream.** Never issue a second brief that amends a first. Update the original brief instead. If a brief needs amending, consolidate into a single replacement document before issuing.

2. **Briefs are read-only for Code.** Code must not edit, append to, annotate, or mark up a brief under any circumstances. The brief is an instruction — not a progress tracker.

3. **No brief persists indefinitely.** Once the bible absorbs a brief's content, the brief moves to `docs/archive/` and stops being referenced. If Code is still reading a brief that was issued more than two build cycles ago, something has gone wrong.

4. **Amendments are consolidations, not patches.** If new information changes part of an active brief, Claude Desktop produces a new consolidated brief that replaces the original entirely. The old brief is archived. There must never be two documents where one "partially amends" the other.

### State File Separation

Code maintains a separate state file for each active brief. The brief is the instruction; the state file is the receipt.

**State file rules:**

1. **Code owns the state file.** It creates it at the start of work and updates it after every step. The state file is the only file Code is permitted to write progress into.

2. **The brief stays untouched.** Progress, strike counts, gate results, build logs, and completion markers go in the state file — never in the brief.

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
- [timestamp] — [decision and rationale]

## Issues for Human Review
- [anything requiring escalation]
```

6. **Verification:** Scott reviews the state file against the brief to confirm what was delivered. Code's self-reported progress is never treated as sign-off — it is a claim to be verified, not a certification.

7. **State files survive context compaction.** This is why they exist. If Code compacts mid-build, it reads the state file to recover position. Never rely on conversation context for build state.

### Document Hierarchy

```
PROJECT-BIBLE (canonical, maintained by Claude Desktop)
    ↓ instructs
Active Briefs (temporary, read-only for Code)
    ↓ tracked by
State Files (owned by Code, verified by Scott)
    ↓ archived alongside
docs/archive/ (retired briefs + their state files)
```

Code reads down. Code writes only to state files and to the codebase. Code never writes up.

### First Action on Receipt

On receiving any brief, Code's first action — before any implementation work — must be to create the corresponding state file and populate it with the full item list from the brief. This confirms the brief was read and the scope is acknowledged.

### Environment Variables

```
FISH_API_KEY=your_fish_api_key
RESEMBLE_API_KEY=your_resemble_api_key
RESEND_API_KEY=your_resend_api_key
AUPHONIC_USERNAME=your_auphonic_username
AUPHONIC_PASSWORD=your_auphonic_password
LALAL_API_KEY=your_lalal_api_key
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
- Cannot vary within a single chunk (acceptable for meditation — consistent tone is the goal)

### V3 Parameters

- `prosody.speed` replaces atempo in the pipeline (speed adjustment handled at API level)
- `"volume": -20 to 20` (default 0) — leave at 0, handle in post-processing

### Investigation Results (7 February 2026)

| Test | Result |
|------|--------|
| Marco compatibility with V3-HD | PASS — voice works with cloned reference |
| Voice conditioning chain on V3 | PASS — consistency maintained across sequential chunks |
| Credit cost | Negligible difference from S1 |

### Fallback

If V3-HD becomes unavailable or degrades:
- Fall back to S1/v1
- No in-text emotion tags (they don't work)
- Rely on expression-through-punctuation (Section 14)
- Punctuation-based control already produced acceptable results

---

# PART C — HISTORICAL RECORD

---

## 19. Amendment Log

This section is a historical record of changes made. It is NOT an operating reference — all current operating rules are in Parts A and B above. If anything in this log contradicts Parts A or B, Parts A and B are correct.

### 4 February 2026 — Initial Setup

21 issues completed across ASMR, Breathing, FAQ, Home, About pages. Premium flow standardised, card images deduplicated, site-wide terminology updated (Free → Sample), 2-column tile grid established. Full image mapping created.

### 4 February 2026 — Card Image Replacements

Hero image replaced (`meditation-woman-outdoor.jpg` → `japanese-fog.jpg`). All card images across index, apps, about, soundscapes, sessions replaced with unique images. Full image inventory created.

### 5 February 2026 — Quick Wins

Founder statement rewritten, American testimonials added, "LATIN: HEALTH" subtitle added, contact page reframed, 21 "Subscribe to unlock" instances changed to "Premium".

### 5 February 2026 — UI/Visual Fixes & 21-Day Course

Play button fix (mindfulness), breathing ring/countdown sync fix (unified timer), tool buttons simplified, profile pictures made consistent, session cards given player overlay UI, 21-day mindfulness course page created.

### 5 February 2026 — Supabase Authentication

Cross-device accounts via Supabase replacing localStorage premium system. Stripe webhook integration. 70+ pages updated with auth scripts and nav button.

### 5 February 2026 — UI Redesign & Navigation Overhaul

Two-row navigation, Latin phrase placement, atmospheric card design pattern, image optimisation, sleep stories updates, education tiles redesign, tools tiles equal height fix, section background blending.

### 5 February 2026 — UI Cleanup & Sleep Stories

Coloured tiles removed site-wide, sessions page redesigned with player bar UI, sleep stories page created (52-book library), navigation streamlined.

### 6 February 2026 — SEO & Infrastructure

robots.txt fixed, sitemap rebuilt (13→76 URLs), canonical tags + OG + Twitter cards on all 75 pages, Google Search Console verified, Cloudflare zone activated, media.salus-mind.com connected, 49 sleep story titles added.

### 7 February 2026 — Automated Audio QA Pipeline

Human QA gate replaced with automated 9-gate system. Click artifact detection and crossfade patching. All 5 deployed sessions scanned and patched. Edge fades added to pipeline.

### 7 February 2026 — QA Failure: Degraded Audio Shipped

Loving-kindness build passed click QA but had severely degraded voice quality. Root causes: QA blind spot (clicks only), lossless pipeline violation (WAV→MP3→WAV), wrong cleanup chain. Fixed with 9-gate system, lossless pipeline, calibrated cleanup.

### 7 February 2026 — Lossless WAV Pipeline & Email

All intermediate audio now WAV. MP3 encoding once at final step. Channel mismatch bug fixed (mono/stereo misinterpretation). Resend email notification system added.

### 7 February 2026 — Loving-Kindness Session

Session `36-loving-kindness-intro` deployed (12.9 min, Fish/Marco). 3 build attempts. First 2 failed (overgeneration + channel mismatch). Build 3 passed with 0 artifacts.

### 7 February 2026 — Ambient Track Fix

4 sessions had ambient shorter than voice. Fixed with 8-hour ambient files. Rule established: NEVER loop ambient.

### 7 February 2026 — Bible Consolidation (v2.0)

Full consolidation pass. Resolved contradictions (loudnorm −24 vs −26, block minimum 20 vs 50, five conflicting cleanup chains). Integrated Brief Part 2 items 2–9 and Brief Part 3. Added Gate 10 (speech rate), Gate 3 sliding window fix, stop rule governance, build state persistence, overgeneration retry logic, per-chunk loudnorm. Restructured from chronological amendments to functional sections.

### 7 February 2026 — 14-Gate QA System & Governance (v2.1)

Expanded from 10 gates to 14 gates. All gates now pass/fail — no informational-only gates. Key changes:

**Gate fixes:** Gate 3 sliding window implemented (18 dB calibrated threshold). Gate 6 converted to speech-aware detection (evaluates non-speech regions only — resolved 100% build failure rate from sibilant false positives). Gate 8 Expected-Repetitions metadata replaces global ignore list. Gate 9 converted from informational-only to pass/fail with energy spike detection (10× speech-only median threshold). Gate 10 silence-aware baseline (excludes pause windows from speech rate calculation).

**New gates:** Gate 11 (Silence Region Integrity), Gate 12 (Duration Accuracy), Gate 13 (Ambient Continuity — calibrated at −80 dBFS / 10 dB), Gate 14 (Opening Quality — tighter thresholds on first 60 seconds).

**V3-HD migration:** Complete. All TTS calls use V3-HD with `emotion: calm`. prosody.speed replaces atempo.

**HF shelf cut investigation:** Tested across full tuning range (−2 to −5 dB at 6–8 kHz). Failed — removing 3 kHz boost entirely produced identical Gate 6 flag counts, proving root cause was speech sibilants. Pipeline unchanged.

**Auphonic per-segment:** API does not return per-segment SNR. Noted as platform limitation.

**Governance additions:** No decorative gates principle. No threshold loosening without approval. Brief lifecycle (DRAFT → ACTIVE → INTEGRATED → ARCHIVED). State file separation. Document hierarchy.

**Threshold calibration:** All new gate thresholds validated against known-good deployed sessions (25-introduction-to-mindfulness, 36-loving-kindness-intro). Calibrated values replace brief estimates where they differed.

---

### 8 February 2026 — Pipeline & Website Updates (v2.2)

**Audio pipeline:**
- Per-chunk loudnorm replaced with whole-file loudnorm (preserves natural dynamics)
- Highshelf boost (`highshelf=f=3000:g=3`) removed — caused perceived echo on certain words
- Per-chunk QA system: generates up to 5 versions of each chunk (best-of-5), scores all via composite metric (spectral flux variance + contrast + flatness + HF ratio + tonal distance), keeps best
- Tonal consistency: MFCC distance to previous chunk penalised at 50× weight
- Flag threshold: 0.50 (OK avg=0.708, Echo avg=0.542, calibrated on 27 human-labeled chunks)
- Session 36-loving-kindness-intro rebuilt (build 11, 10.5 min, 14/14 gates)
- Per-chunk QA upgraded from best-of-2 to best-of-5 (135 TTS calls for 27 chunks)
- v3 script rewritten: varied benedictions (no formulaic repetition), trigger words avoided
- v3 build: 14/14 gates, 70% clean rate on human review (19/27 OK, up from 58% on v2)
- Known Fish trigger words expanded: "breath in", "be" (standalone), "simply", "family", "joyful"

**Threshold recalibrations (approved by Scott during live testing session, 8 Feb 2026):**
- Gate 7 widened to 9/14 dB + proportional silence margin (`max(4s, dur×0.15)`) — required to accommodate Fish chunk-level swings under whole-file loudnorm
- Gate 8 manifest text guard added: word overlap <60% skips MFCC pairs as false positives — prevents meditation cadence patterns from triggering duplicate detection
- Gate 9 HF threshold recalibrated to 28× speech-only median, total to 12× — calibrated against no-ambient and ambient sessions to separate sibilants from genuine hiss

**Website:**
- Navigation Row 2 now includes Applied Psychology
- New page: `articles/anxiety-thinking.html` (first article detail page, `articles/` subdirectory)
- Applied Psychology page: featured article link, "Updated Regularly" approach item
- Mindfulness page restructured: session cards first, then 7-day + 21-day course banners
- `css/style.css` fixed at source: all light-theme backgrounds neutralised (body, hero, hero-bg::after, daily-quote, section:nth-child(even), filter-btn, sound-category-tag → transparent). Per-page overrides no longer needed.
- ASMR page (`asmr.html`): "Coming Soon" placeholder replaced with 14-sound card library (rain, ocean, forest, thunder, birds, fire, stream, cafe, garden, library, night, temple, waterfall, white noise). Category filters (All/Nature/Weather/Spaces/Ambient), animated waveform bars, per-card accent colours, staggered entrance animation. Supersedes old `sounds.html`.

---

### 8 February 2026 — Dark Theme & Routing Fixes

**style.css dark theme completion:**
- 22 text/background color rules converted from light to dark-compatible: body text (`#f0eefc`), links (`#7c8cf5`), nav (bg `rgba(6,8,16,0.92)` + logo + links), hero paragraph (`rgba(240,238,252,0.55)`), daily quote, section headers, feature cards/icons (`rgba(124,108,240,0.12)`), form inputs/labels, filter buttons, session cards, sound cards
- CSS variables (`:root`) retained for backward-compatible selectors (footer, CTA banner, buttons)

**Login buttons:** Fixed `href="#"` → `login.html` across 11 files (22 instances). Articles subdirectory uses `../login.html`.

**Mindfulness page cleanup:** Removed 6 content sections (276 lines): What is Mindfulness, The Science, Core Practices, How to Start, Mindfulness in Daily Life, FAQ. All had light gradient backgrounds causing white bands. Page now shows session cards + course banners + CTA only.

**Footer routing:** `sounds.html` → `asmr.html` across 60 files (root pages + sessions/ + newsletters/).

**Premium CTA routing:** `newsletter.html` → `apps.html` in media.html, sounds.html, newsletter.html.

**Subsequent completion (same day):** All 15 remaining pages converted to dark theme. Unified `hb-footer` applied to all 82 pages. breathe.html and timer.html heroes rebuilt with dark-theme pattern (radial glow, gradient text). Reading page: miniature book covers via Open Library Covers API, increased description font. Mindfulness page: fixed 7-day course 404 link.

---

### 8 February 2026 — Learn & Applied Psychology Content Launch

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

### 8 February 2026 — Session 36 Shipped & Review Workflow

**Audio production:**
- Session 36-loving-kindness-intro-v3 shipped to production (v3b focused rebuild)
- `--focus-chunks` CLI argument added: problem chunks get best-of-10, others best-of-5
- Ambient level increased from -14dB to -11dB for more present ambient bed
- Resend email fixed: Python `urllib` blocked by Cloudflare → switched to `curl` subprocess

**Human review workflow established (mandatory for all future sessions):**
1. Build with `--no-deploy` → 14-gate QA runs automatically
2. Extract chunks from raw narration WAV using manifest timing data
3. Upload individual chunks to R2 at `test/chunk-test-{version}/`
4. Create interactive HTML review page with export facility (Copy Results + Download TXT)
5. Listen to every chunk on AirPods at high volume (exposes hiss, echo, tonal shifts that speakers miss)
6. Rate each chunk: OK / ECHO / HISS / VOICE / BAD
7. If acceptable → remix with ambient, deploy to R2, update all HTML references, commit, push, email
8. If problem chunks → `--focus-chunks 1,3,6` for targeted rebuild, re-review
9. Perfection should not prevent shipping — accept reasonable clean rate and move forward

**Testing checklist (learned from session 36):**
- Test playback on BOTH desktop and mobile (CORS blocked mobile audio before R2 CORS was configured)
- Check ALL pages that reference the session (detail page, listing pages, mindfulness cards) — missed references = broken players
- Verify file duration matches expected (stale CDN cache served old file with wrong duration)
- Players without `data-src` attribute are visual-only — buttons do nothing by design
- Mindfulness page uses `m-player` class (inline JS), not `custom-player` (main.js) — different wiring

**Infrastructure:**
- R2 CORS configured: `salus-mind.com` and `www.salus-mind.com` allowed origins (GET/HEAD)
- Mindfulness page players wired up with real audio for Introduction to Mindfulness and Loving-Kindness Introduction

---

### 8 February 2026 — LALAL.AI Integration & Session 25 Rebuild (v3.1)

**LALAL.AI evaluation:**
- Integrated LALAL.AI voice_clean API into `build-session-v3.py` as Phase 1.5 (between chunk QA and edge fades)
- A/B tested on session 25 chunk 28 (voice shift at 6:47) — LALAL made no difference to voice shift (TTS generation problem, not post-processing)
- Full session rebuild with LALAL (`noise_cancelling_level=1`, `dereverb_enabled=True`): hiss removal excellent (almost all hiss gone), but dereverb stripped Marco's vocal resonance
- Dereverb damages Fish output — Marco's TTS has no room reverb, so dereverb removes legitimate vocal character
- LALAL disabled in build script pending retest with `dereverb=False` (noise cancellation only)

**Session 25 rebuilt:**
- Trigger word "nowhere else" discovered causing voice shift — replaced with "All you need to do is be right here, right now"
- 36 chunks generated (best-of-5), LALAL cleaned 36/36
- 13/14 gates passed; Gate 13 (Ambient) failed on garden-8hr.mp3 dead silence — fixed with `-ss 10` offset
- Deployed to R2 (commit acb5842) — voice quality degraded from LALAL dereverb, fresh non-LALAL rebuild initiated
- Introduction to Mindfulness tile reverted to premium locked (commit c986804)

**Fish Audio observations:**
- Possible S1 model degradation: >500 char generations temporarily routed to v1.6, causing voice inconsistency between chunks
- Opening chunks (1–5) consistently score lowest — chunk 1 has no MFCC reference for voice conditioning
- MFCC tonal distance scoring (threshold 0.50) can miss voice character shifts that human ears catch (chunk 28 scored 0.496)

**New production rules:**
- Raw narration WAVs must never be overwritten without preserving originals (timestamped copies)
- All audio quality comparisons must be narration-only — ambient invalidates evaluation
- Garden ambient requires `-ss 10` offset (9.5s dead silence at file start)

**Code mistakes logged:** Failed to preserve pre-LALAL narration, provided ambient-mixed files for comparison instead of narration-only, deployed LALAL build without human review, did not test LALAL settings individually before full pipeline integration. All documented for governance improvement.

---

### 8 February 2026 — Script Uniqueness & Cross-Session Differentiation (v3.2)

New Section 13A added to address internal repetition across the Salus session catalogue. Sessions were beginning to sound interchangeable — same openings, same breath cues, same structural arc, same closings. A customer listening to multiple sessions back-to-back should have distinct experiences.

**Cross-session register system:** Three mandatory register files introduced (`openings-register.txt`, `closings-register.txt`, `phrases-register.txt`) in `content/scripts/`. Every deployed session's key phrases are catalogued. New scripts are checked against existing entries before build — no phrase of 5+ words may be reused, no opening or closing technique may be repeated within a category.

**Six categories of repetition identified:** Openings, breath cues, body awareness transitions, silence announcements, closings, and structural arc. Each has specific variation strategies and mandatory register checks.

**Automated pre-build originality scan:** Runs alongside trigger word check during pre-flight. Fuzzy-matches new script blocks against register entries (70% threshold on 5+ word phrases). WARNING system, not a build-blocker.

**Checklist updates:** Pre-Build Checklist now includes originality scan. Deployment Checklist now requires register file updates after every session deploy.

**Narration audit (outstanding):** Full audit of all 17 deployed sessions required to retroactively populate registers and identify existing cross-session repetition. Must be completed before any new scripts are written. Added to Section 13A as a pending task.

**External originality (secondary):** Lightweight due diligence step — web research to consciously diverge from published scripts, no phrase of 6+ words matching a published source. Research notes stored in `content/scripts/research/`.

---

### 9 February 2026 — Four Sessions Deployed & Build Learnings (v3.3)

**Sessions deployed (commit 752752f):**
- 18-calm-in-three-minutes (3.2 min, stress, rain ambient — build 1, 14/14 gates)
- 23-the-calm-reset (5.5 min, stress, stream ambient — build 1, 14/14 gates)
- 19-release-and-restore (14.5 min, stress, garden ambient — build 4, 14/14 gates)
- 32-observing-emotions (9.5 min, mindfulness, garden ambient — build 3, 14/14 gates)

Sessions 18 and 23 are new scripts. Sessions 19 and 23 had scripts rewritten (trigger-word clean). Session 32 is a new script. All four wired into sessions.html and relevant detail/category pages.

**Gate 7 (Volume Surge) — most persistent failure mode:** Fish Audio's non-deterministic TTS generation causes per-chunk volume variation that triggers Gate 7 surges, particularly after long silences. Session 19 needed 4 builds, session 32 needed 3. The 9.0 dB threshold is correctly calibrated — rebuilding eventually produces level-consistent generations. Longer sessions with more chunks have higher failure probability. Documented in Gate 7 section.

**Character estimation overestimates duration:** The ~7.2 chars/sec formula overestimated session 32 (scripted for 12 min, TTS produced 9.5 min). The build script's own duration estimate after dry run is more reliable. Updated Section 13 table with caveat: use 7.2 chars/sec for rough planning only, set Duration-Target from dry run output.

**Garden ambient offset confirmed automated:** `-ss 10` offset now applied in both Fish and Resemble mix paths in `build-session-v3.py`. Updated non-negotiable rule 16 to reflect confirmed implementation.

**New ambient file:** `stream-extended.mp3` created for longer sessions using stream ambient.

---

### 9 February 2026 — Targeted Repair, Build Status & Process Maturation (v3.4)

**New Section 15A: Targeted Chunk Repair (EXPERIMENTAL)**
Introduced controlled single-word/chunk repair as an alternative to full session rebuilds. Process: identify defect → locate chunk → regenerate with best-of-10 → splice with crossfading and MFCC tonal matching → save as new file (never overwrite original) → re-run 14 gates. Rule 11 (no post-build splicing) amended to allow targeted repair under Section 15A conditions. Trial on session 32 "Observing Emotions" — word "something" has echo at opening.

**Master narration file concept (Rule 14 strengthened):**
Once a narration passes 14 gates and is approved, it becomes a master narration file — sacrosanct, never deleted or overwritten. Naming convention: `{session-name}_master-narration.wav` in `content/audio-free/masters/`. All future versions (repairs, remixes) derive from the master; the master stays untouched. Code was previously overwriting narration WAVs when applying ambient, forcing full regeneration for any change.

**Human review relaxed (Section 16):**
Individual chunk-by-chunk listening replaced with full-session continuous playback. With the pipeline now producing 3–4 defective words across four full sessions, per-chunk review is no longer necessary. Defects are noted with timestamps during natural listening and fed into the targeted repair process.

**Visual QA report inspection (Section 12, mandatory):**
Code confirmed it generates QA report PNGs but never visually inspects them — gates run numerically and Code takes the numbers at face value. New mandatory step: Code must open and examine QA report spectrograms for anomalies that pass numerical thresholds but are visible on graphs. Findings documented in build state file.

**Hiss reduction testing (Section 15, outstanding):**
Pipeline has no active de-hiss step. LALAL.AI with dereverb disabled and Auphonic noise-reduction-only are both identified as untested approaches. Required: A/B testing on known-hissy chunks to find a noise reduction method that doesn't damage Marco's vocal character.

**Full build status incorporated (Section 16):**
Comprehensive catalogue status added: 52 scripts total, 10 deployed, 42 not yet produced, 8 cards on site with no working audio, 4 sessions built on old Bible (rebuild candidates). Replaces the previous simple Deployed Sessions table.

**Session production records (Section 16, new):**
Per-session production record template added. Every deployed session gets a markdown file (`{session}_production-record.md`) in `content/audio-free/masters/` capturing identity, deployment status, master files, build history, repairs, known issues, review notes, and script changes. Centralises session-level information that was previously scattered across manifests, logs, state files, and conversation history. Retroactive population required for all 10 deployed sessions. Production record creation added to deployment checklist.

**Auphonic status updated (Section 15):**
Changed from "measurement only" to include hiss reduction evaluation.

---

*Last updated: 9 February 2026 — v3.4: Targeted chunk repair (Section 15A, experimental). Master narration files (Rule 14). Session production records. Human review relaxed to full-session playback. Visual QA report inspection mandatory. Hiss reduction testing outstanding. Full build status catalogue incorporated.*

---

## Document Governance

**Owner:** Scott (via Claude Desktop — Scott's conversational Claude instance)
**Consumers:** Claude Code, any future contributors

This document is maintained by Claude Desktop on Scott's behalf. Claude Code reads it as a reference but **must not edit, append to, or modify it under any circumstances.** If Code identifies an error, omission, or outdated information, it must report the issue and wait — not fix it.

Changes to this document follow this workflow:
1. Scott or Claude Desktop identifies needed change
2. Claude Desktop drafts the update
3. Scott approves
4. Claude Desktop produces the updated bible
5. Code receives the new version via brief

This separation exists because Code previously both wrote and read the bible, leading to contradictions, self-certified completions, and unauthorised pipeline modifications. The contractor does not amend the specification.

**Note (8 Feb 2026):** Code edited this document directly during the 8 Feb session. The edits were largely accurate but introduced governance conflicts and contradicted existing non-negotiable rules. This corrected version (v2.2c) restores Desktop ownership and resolves those conflicts. All future Bible edits go through the workflow above.
