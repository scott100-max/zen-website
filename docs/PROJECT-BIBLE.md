# Salus Project Bible

This document contains design guidelines, standards, and a record of website amendments.

## Contents

- Design Standards
- Website Amendments
- Self-Validation Process
- Deployment & Infrastructure
- Audio Production
- TTS Provider Comparison: Fish Audio vs ElevenLabs
- Common Issues & Lessons Learned
- Marco Master Audio Standard (Resemble AI)
- Section 13: External Audio Quality Analysis — Auphonic
- Section 14: Marco Master Voice Specification

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

---

### 5 February 2026 — Quick Wins from salus-website-fixes.txt

**Copy & Content Changes:**

| # | Page | Change | Status |
|---|------|--------|--------|
| 6 | index.html | Deleted "takes your money and forgets your name" from Welcome section | DONE |
| 11 | tools.html | Removed "Free" from hero ("Free Tools" → "Tools"), updated meta description | DONE |
| 18 | Site-wide | Added "LATIN: HEALTH" subtitle under nav logo on main pages | DONE |
| 25 | index.html | Founder statement now opens with "Hello and welcome to Salus. I'm so pleased you have found us." + added "journey to inner peace" | DONE |
| 26 | index.html | Added American testimonials: Michelle R., Austin TX and Kevin M., San Francisco CA (replaced 2 UK testimonials) | DONE |
| 27 | soundscapes.html | Changed all "Subscribe to unlock" to "Premium" (21 instances) | DONE |
| 39 | contact.html | Reframed intro to "We're a small family team and we actually read these. One inbox, real people, real responses." | DONE |

**Files Modified:**
- `index.html` — Founder statement, testimonials, logo
- `tools.html` — Hero heading, meta description, logo
- `contact.html` — Hero text, logo
- `soundscapes.html` — Premium text (21 instances), logo
- `about.html` — Logo
- `sessions.html` — Logo
- `apps.html` — Logo
- `thank-you.html` — Logo
- `mindfulness.html` — Logo
- `education.html` — Logo
- `reading.html` — Logo
- `newsletter.html` — Logo
- `docs/PROJECT-BIBLE.md` — Updated

**Note:** Emma testimonial (#8) mentions "Calm Reset" which exists at `sessions/calm-reset.html` — no change needed.

---

### 5 February 2026 — UI/Visual Fixes & 21-Day Course

**Issues Completed:**

| # | Page | Change | Status |
|---|------|--------|--------|
| 10 | mindfulness.html | Fixed play button not round - added `flex-shrink:0` to prevent flexbox compression | DONE |
| 13 | breathe.html | Fixed ring/countdown sync - replaced dual-timer system with single unified `mainTimer` | DONE |
| 12 | tools.html | Simplified tool buttons - removed gradient circles, now simple SVG icons with accent color | DONE |
| 5 | about.html | Profile pictures consistent - Ella & Marco now use `<img>` tags like Scott, removed gradient overlay from Marco | DONE |
| 2 | css/style.css | Session cards look like players - added play button overlay, reduced thumbnail height to 120px | DONE |
| — | mindfulness.html | Added 21-Day Mindfulness Course teaser card below 7-day course | DONE |
| — | mindfulness-21-day.html | NEW PAGE: 21-day course with 3 weeks structure, Day 1 free, Days 2-21 locked | DONE |

**Files Modified:**
- `mindfulness.html` — Play button fix, 21-day teaser
- `breathe.html` — Unified timer system
- `tools.html` — Simplified buttons
- `about.html` — Consistent profile pictures
- `css/style.css` — Session card play overlays
- `mindfulness-21-day.html` — NEW FILE
- `validate-fixes.sh` — NEW FILE (validation script)
- `docs/PROJECT-BIBLE.md` — Updated

---

## Self-Validation Process

### CRITICAL: Validation Must Check FULL Request, Not Just Completed Work

**Lesson learned (5 Feb 2026):** Self-validation reported "16/16 passed" while 11 items remained unresolved. The validation only checked work that was done, not work that was requested. This is a fundamental flaw.

### Validation Rules

1. **Source of truth:** `docs/FIXES-CHECKLIST.md` — not the validation script
2. **No "SKIPPED" status:** Items are DONE, PENDING, or DEFERRED (with justification)
3. **DEFERRED requires approval:** Only for items needing separate project scope
4. **Report honestly:** State completion percentage against FULL original request
5. **Pending items must be listed:** Every report must show outstanding work

### Two-Stage Validation

**Stage 1: Code Verification** (validate-fixes.sh)
```bash
cd /Users/scottripley/salus-website
./validate-fixes.sh
```
This checks code changes were implemented correctly. It does NOT confirm all requested work is complete.

**Stage 2: Checklist Verification** (manual)
1. Open `docs/FIXES-CHECKLIST.md`
2. Compare against original request
3. Confirm every item has accurate status
4. Calculate true completion percentage
5. List all PENDING items in final report

### Final Report Format

Every completion report MUST include:

```
COMPLETION REPORT
─────────────────
Done:     X items
Pending:  Y items  ← WORK REMAINING
Deferred: Z items

Completion: XX%

Outstanding:
- Item description (#number)
- Item description (#number)
```

### Validation Script Usage

The script verifies code changes only:

```bash
# Check something EXISTS:
if grep -q 'expected-pattern' filename.html; then
    check "Description" "true"
fi

# Check something was REMOVED:
if grep -q 'old-pattern' filename.html; then
    check "Old pattern removed" "false"
fi

# Check file EXISTS:
if [ -f "new-file.html" ]; then
    check "New file created" "true"
fi
```

**Remember:** Script passes ≠ Job complete. Always verify against checklist.

---

---

### 5 February 2026 — Supabase Authentication System

**Overview:** Implemented cross-device user accounts using Supabase to replace localStorage-based premium system.

**Architecture:**

| File | Purpose |
|------|---------|
| `/js/supabase-config.js` | Supabase client initialization |
| `/js/auth.js` | Auth module: signUp, signIn, signOut, isPremium, updateNavUI |
| `/login.html` | Email/password login page |
| `/signup.html` | Registration page |
| `/dashboard.html` | Account overview, subscription status |
| `/reset-password.html` | Password reset flow |
| `/supabase/functions/stripe-webhook/index.ts` | Stripe payment event handler |
| `/supabase/migrations/001_create_auth_tables.sql` | Database schema |

**Supabase Credentials:**
- **Project URL:** `https://egywowuyixfqytaucihf.supabase.co`
- **Project ID:** `egywowuyixfqytaucihf`
- **IMPORTANT:** Use the **Legacy** JWT anon key (starts with `eyJ...`), NOT the new `sb_publishable_` format

**Database Tables:**
- `profiles` — User data (auto-created on signup via trigger)
- `subscriptions` — Stripe subscription data (user_id, stripe_customer_id, status, plan_type)

**Premium Logic (in order):**
1. Check Supabase `subscriptions` table for active subscription (cross-device)
2. Fall back to localStorage `salus_premium` (legacy/single-device)
3. Migration banner prompts localStorage-only users to create accounts

**Stripe Webhook Integration:**
- Endpoint: `https://egywowuyixfqytaucihf.supabase.co/functions/v1/stripe-webhook`
- Events handled:
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

**UI Changes:**
- All ~70 HTML pages updated with:
  - Supabase scripts in `<head>`
  - "Log In" button in navigation (changes to "Account" when logged in)
- `apps.html`: Non-logged-in users see "Create Account to Subscribe"
- `thank-you.html`: Shows account creation prompt if paid without logging in
- `signup.html`: Subtitle changed to "Start your Salus journey"
- `login.html` & `signup.html`: Support `?redirect=` param to return user to original page after auth

**Files Modified:**
- All HTML pages (70+) — Supabase scripts, nav auth button
- `js/main.js` — Premium check defers to auth.js when available
- `apps.html` — Require account before subscribing
- `thank-you.html` — Account creation prompt for non-logged-in users

**Stripe Account:**
- Business name changed from "zenscape" to "Salus"
- Webhook configured with signing secret in Supabase secrets

**Tech Notes:**
- Supabase CLI installed via Homebrew
- Edge functions deployed with `--no-verify-jwt` flag for webhooks
- Secrets set: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

---

## Deployment & Infrastructure

### Architecture
| Service | What it hosts | URL |
|---------|--------------|-----|
| **GitHub Pages** | Website code (HTML, CSS, JS, small images) | `https://salus-mind.com` |
| **Cloudflare R2** | Media files (MP3, MP4) | `https://media.salus-mind.com` |
| **Cloudflare** | DNS for entire domain | Nameservers: `gerald.ns.cloudflare.com`, `megan.ns.cloudflare.com` |

### GitHub Pages (website code)
- **Repository:** `https://github.com/scott100-max/Salus-Website.git`
- **Branch:** `main`
- **Auto-deploys** on push within 1-2 minutes

**To deploy website changes:**
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

**To upload new audio/video:**
```bash
# Via wrangler CLI:
npx wrangler r2 object put salus-mind/content/audio-free/FILENAME.mp3 --file=./FILENAME.mp3

# Or drag-and-drop in Cloudflare dashboard:
# R2 → salus-mind bucket → Objects → Upload
```

**To reference media in HTML:**
```html
<div class="custom-player" data-src="https://media.salus-mind.com/content/audio-free/FILENAME.mp3">
```

**File paths in R2 bucket:**
- Free audio: `content/audio-free/`
- Sounds (ASMR): `content/sounds/`
- Video: `content/video/`

### Domain & DNS
- **Registrar:** reg-123 (salus-mind.com), GoDaddy (salus-mind.co.uk)
- **DNS managed by:** Cloudflare (nameservers: `gerald.ns.cloudflare.com`, `megan.ns.cloudflare.com`)
- **Migrated:** 6 February 2026 — moved from GoDaddy DNS (`ns65/ns66.domaincontrol.com`) to Cloudflare
- **Registrar holds nameservers only** — all DNS records managed in Cloudflare dashboard
- GitHub Pages A records: `185.199.108-111.153`
- `www` CNAME → `scott100-max.github.io`
- `media` CNAME → R2 bucket (proxied through Cloudflare CDN)

### SEO
- **Google Search Console:** Verified via HTML file (`googleaba2f038193703b2.html`)
- **Sitemap:** `https://salus-mind.com/sitemap.xml` (76 URLs)
- **Canonical tags:** All 75 public HTML pages
- **Open Graph + Twitter cards:** All 75 public HTML pages
- **Default OG image:** `https://salus-mind.com/images/meditation-woman-outdoor.jpg`
- **robots.txt:** Points to sitemap at `salus-mind.com`

### Workflow Summary
| Task | Action |
|------|--------|
| Edit HTML/CSS/JS | Change files → `git push` |
| Add new audio/video | Upload to R2 → reference in HTML → `git push` |
| Add new HTML page | Create page → add to sitemap.xml → `git push` |

---

### 5 February 2026 — UI Cleanup & Sleep Stories

**Colored Tiles Removed Site-Wide:**

| Page | Section | Status |
|------|---------|--------|
| index.html | "Why We're Different" cards | Removed gradient headers |
| index.html | "What's Inside" cards | Removed gradient headers |
| about.html | "What We Stand For" cards | Removed gradient headers |
| apps.html | "What's Inside Premium" cards | Removed gradient headers |
| sessions.html | Premium session cards | Converted to player UI style |

**Sessions Page Redesign:**
- Removed all colored "session-card" boxes
- Premium sessions now display with player bar UI (play button + progress bar)
- Matches the sample sessions design
- Cards link to individual session pages when clicked

**Sleep Stories Page:**
- Page exists at `/sleep-stories.html` (Coming Soon)
- Linked from homepage "What's Inside" section
- NOT in main navigation (nav was too crowded with 11 items)
- 52-book library preview with weeks 1-4 "available", 5-52 locked

**Navigation:**
- Sleep Stories removed from nav to reduce crowding
- Current nav items: Home, Guided Meditations, Mindfulness, ASMR, Tools, Learn, About, Reading, Newsletter, Contact

**Design Rule Added:**
- No colored gradient tiles/boxes on cards - use simple white cards with text only

---

## Audio Production

### Fish Audio Voice
- **Voice:** "Calm male" by ANGEL NSEKUYE
- **ID:** `0165567b33324f518b02336ad232e31a`
- **Character:** Deep resonance, slight accent (possibly Italian), very soothing
- **User calls him:** "Marco" / "Fish man"
- **Critical:** This voice has a relaxation quality that other TTS (ElevenLabs) cannot replicate

### What DOESN'T Work
- **ffmpeg processing degrades quality** - noise reduction, de-essers, lowpass filters all make it sound "muffled" or "behind a quilt"
- **ElevenLabs cloning** - captures resonance but loses the specific character
- **Adobe Podcast Enhance** - can't fix TTS voice changes, only surface noise
- **Aggressive cleanup pipeline** - `lowpass=f=10000` kills clarity

### What DOES Work
- **Fresh Fish rebuild** - TTS is non-deterministic, rebuilding often fixes issues
- **Minimal processing** - loudness normalization only: `loudnorm=I=-24:TP=-2:LRA=11`
- **Higher bitrate** - 128kbps vs original 51kbps

### Quality Standards
- **100% OR NO SHIP** - any audible glitch = FAIL
- **Automated QA is the gate** - scan→fix→rescan loop runs until clean, then auto-deploys to R2, then emails scottripley@icloud.com. Human out of loop. No manual strike counting — the cycle runs until it passes.

### Analyzer v4 Findings
- Sibilance/click detection has many false positives
- Voice change detection is useful signal
- 0 voice changes = good indicator

### Comparative Benchmarks (vs Calm app)
| Metric | Target | Notes |
|--------|--------|-------|
| Bitrate | 128kbps | Calm uses 92kbps Opus |
| Loudness | -24 LUFS | Industry standard for relaxation |
| True Peak | -2 dBTP min | Calm at -5.67 |
| Channels | Mono OK | Stereo comes from ambient mix |

---

## TTS Provider Comparison: Fish Audio vs ElevenLabs

### When to Use Each Provider

| | Fish Audio | ElevenLabs |
|---|---|---|
| **Best for** | Short meditations (<15 min) | Long sleep stories (30-45 min) |
| **Voice** | "Marco" — deep resonance, slight accent, unique character | Library voices (Daniel, George, etc.) — clean, consistent |
| **Chunks** | ~147 small blocks per 45-min story | ~12 merged blocks per 45-min story |
| **Drift risk** | High on long content (voice changes across many chunks) | Low (fewer chunks = fewer drift points) |
| **First-build success** | ~40% for 45-min stories, ~95% for <15 min | Expected ~90%+ for all lengths |
| **Audio quality** | Needs full cleanup chain (de-esser, noise reduction) | Clean output, just loudnorm needed |
| **API auth** | `Bearer` token | `xi-api-key` header |
| **Pacing** | Explicit silence files between every block | Paragraph breaks (`\n\n`) render as natural pauses |
| **Cost** | Lower per-character | Higher per-character |
| **Rebuild cost** | Cheap per attempt but many attempts needed | More per attempt but fewer needed |

### Provider Architecture in build-session-v3.py

```
Script → process_script_for_tts() → blocks (147 for Monty)
                                          │
                    ┌─────────────────────┴──────────────────────┐
                    │                                            │
              Fish (default)                            ElevenLabs
              147 blocks as-is                   merge_blocks_for_elevenlabs()
              generate_tts_chunk()                      → 12 blocks
              cleanup: full                      generate_tts_chunk_elevenlabs()
              (de-esser, noise gate,             cleanup: light
               lowpass, dynaudnorm)              (loudnorm -24 LUFS only)
                    │                                            │
                    └─────────────────────┬──────────────────────┘
                                          │
                              concatenate_with_silences()
                              mix_ambient()
                              → final MP3
```

### CLI Usage

```bash
# Fish (unchanged default)
python3 build-session-v3.py ss01-montys-midnight-feast

# ElevenLabs
python3 build-session-v3.py ss01-montys-midnight-feast --provider elevenlabs

# ElevenLabs with specific voice and model
python3 build-session-v3.py ss01-montys-midnight-feast --provider elevenlabs --voice VOICE_ID --model v3

# Raw output (no cleanup) for quality testing
python3 build-session-v3.py ss01-montys-midnight-feast --provider elevenlabs --no-cleanup

# Dry run to preview block counts
python3 build-session-v3.py ss01-montys-midnight-feast --dry-run --provider elevenlabs
```

### TTS Voice: Marco (Fish Audio)

**Marco is the sole voice for all sleep stories.** Voice ID: `0165567b33324f518b02336ad232e31a`

Fish Audio with Marco has shipped 3 sessions successfully. No atempo slowdown needed — Marco speaks at natural sleep story pace.

### ElevenLabs — ABANDONED (6 Feb 2026)

ElevenLabs was evaluated as an alternative TTS provider across 11 builds and £90+ in credits. **Every approach failed.** Full evidence archived at `Desktop/elevenlabs-evidence/`.

**Why it failed:**
- API cannot hold voice consistency beyond 2-3 sequential calls (request stitching doesn't work for long-form)
- Studio "audiobook" feature produces continuous speech with no paragraph gaps and voice breakdown
- SSML breaks max 3 seconds (sleep stories need 4-8s gaps)
- Speed parameter inconsistent within chunks
- Studio API locked behind sales whitelist (403 error)
- Every combination of merging, stitching, SSML, and speed produced zero usable output

**Do not revisit ElevenLabs** unless they release a fundamentally different long-form API. The platform is built for short-form content (ads, voiceovers, clips under 5 minutes).

### Fish Audio Female Voice Auditions — FAILED (6 Feb 2026)

8 female Fish voices auditioned. All inferior to Marco for sleep story delivery. None had the warmth or natural pacing. Marco remains sole voice.

### Production Pipeline (Fully Automated — Brief to Live)

The entire pipeline is autonomous. No human in the loop. Runs from script to live deployment without intervention.

```
Script (pause markers)
        │
        ▼
process_script_for_tts() → blocks with pause durations
        │
        ▼
generate_tts_chunk() → Fish API
        │
        ▼
apply_edge_fades() → 15ms cosine fade on each chunk
        │
        ▼
concatenate_with_silences() → cleanup (loudnorm) → mix_ambient()
        │
        ▼
qa_loop():  scan_for_clicks() → patch_stitch_clicks() → rescan
            ↻ repeat until 0 click artifacts
        │
        ▼
deploy_to_r2() → LIVE on media.salus-mind.com
        │
        ▼
send_build_email() → scottripley@icloud.com
```

**Audio processing — DO NOT apply at any stage:**
- ~~lowpass=f=10000~~ (kills clarity)
- ~~afftdn=nf=-25~~ (muffles the voice)
- ~~dynaudnorm~~ (replaced by loudnorm)
- ~~aggressive de-essers or shelf filters~~

**Only processing allowed:** `loudnorm=I=-24:TP=-2:LRA=11`

**Lossless pipeline — all intermediate audio must be WAV:**
1. TTS chunks from API → immediately convert to WAV
2. `apply_edge_fades()` → WAV in, WAV out
3. `concatenate_with_silences()` → WAV
4. Loudness normalisation → WAV
5. Ambient mixing → WAV
6. `scan_for_clicks()` and `patch_stitch_clicks()` → WAV
7. **Final encode to MP3 128kbps** — this is the ONLY lossy step
8. Deploy to R2
9. Email scottripley@icloud.com

No atempo needed for Fish/Marco — natural speed is correct.

### Production Rules (Non-Negotiable)

1. **ONE build at a time.** Never run builds in parallel — burned 100K credits once.
2. **Always dry-run first.** Check block count and silence totals before spending credits.
3. **Fish has a ~60% rebuild rate on 45-min stories.** This is expected. Rebuild until it lands.
4. **Never identical gaps.** All pauses go through `humanize_pauses()`.
5. **Marco is the only voice.** Do not audition alternatives unless Marco is discontinued.
6. **QA is automated.** The pipeline scans, patches, and re-scans until clean. No human listening required before deploy.
7. **Deploy is automatic.** Build passes QA → uploads to R2 → live. Use `--no-deploy` to hold.
8. **Email is mandatory.** Every completed build cycle ends with an email to scottripley@icloud.com — pass or fail.
9. **Fully autonomous.** No human interaction between receiving a brief and the audio being live. Handle every step.
10. **No OneDrive.** All files go to git (code) or Cloudflare R2 (media). Never copy files to OneDrive.

### CLI Usage

```bash
# Full pipeline: build → QA → deploy to R2
python3 build-session-v3.py 25-introduction-to-mindfulness

# Dry run (no API calls)
python3 build-session-v3.py 25-introduction-to-mindfulness --dry-run

# Build + QA but don't deploy
python3 build-session-v3.py 25-introduction-to-mindfulness --no-deploy

# ElevenLabs provider (abandoned, but syntax preserved)
python3 build-session-v3.py SESSION --provider elevenlabs --model v2
```

### Pre-Build Checklist

Before every Fish build:
- [ ] Dry run shows correct block count and silence totals
- [ ] Only building ONE story
- [ ] Provider set to `fish` (default)

---

### Known Issue: Fish 60% Failure Rate on Long Content

Fish Audio TTS generates non-deterministic output. For Monty's Midnight Feast (45 min, 28K chars):
- 147 separate API calls = 147 potential drift points
- Voice character can shift between chunks (pitch, accent, pacing)
- ~60% of first builds have audible voice changes
- Fix: rebuild (TTS is non-deterministic, next attempt may be clean)
- ElevenLabs reduces this to 12 API calls, eliminating 92% of drift points

---

## Common Issues & Lessons Learned

### Page Visibility Checklist (Feb 2026)
**Issue:** Sleep Stories page existed but wasn't accessible - no links from nav or homepage.
**Root cause:** Page was created and deployed but never linked anywhere visible.

**Prevention:** When creating any new page:
1. Add to navigation on ALL HTML files (~70 root + 44 sessions)
2. Add to homepage "What's Inside" section if it's a main content type
3. Add to relevant footer sections
4. Verify at least one link exists before marking complete

**Quick nav update command:**
```bash
# Root pages
sed -i '' 's|Guided Meditations</a></li>|Guided Meditations</a></li>\n        <li><a href="NEW-PAGE.html">New Page</a></li>|' *.html
# Session pages (use ../ prefix)
sed -i '' 's|../sessions.html">Guided Meditations</a></li>|../sessions.html">Guided Meditations</a></li>\n        <li><a href="../NEW-PAGE.html">New Page</a></li>|' sessions/*.html
```

### Deployment Verification
- GitHub Pages auto-deploys on push to main
- Check `gh run list --limit 3` for deployment status
- Always verify live URL after claiming changes are deployed
- Use `WebFetch` to confirm live site content matches expectations

### Large Files in Git
- **NEVER commit audio/video files to git** — all media goes to Cloudflare R2
- `.gitignore` excludes `*.mp3`, `*.mp4`, `*.wav`, and media directories
- Test files, debug files, and downloads should also be in `.gitignore`

---

---

### 5 February 2026 — UI Redesign & Navigation Overhaul

**Two-Row Navigation:**
- Main nav split into two rows for better organization
- Row 1: Sessions, Mindfulness, ASMR, Sleep Stories, Learn, About
- Row 2: Tools, Reading, Newsletter, Contact (smaller, gray text)
- Applied to ALL HTML pages via Python script
- Second row uses `gap:32px` and `font-size:0.9rem`

**Latin Phrase Placement:**
- Removed "LATIN: HEALTH" from under logo
- Added "Salūs — Latin: health, safety, well-being" under hero sections on all pages
- On light backgrounds: `color:var(--mid-gray);opacity:0.7`
- On dark/hero backgrounds: `color:rgba(255,255,255,0.6)`

**Atmospheric Card Design Pattern:**
- Used on: Sessions, Tools, Education tiles
- Full gradient backgrounds (category-specific colors)
- Floating glowing orbs using `filter:blur(40px)` and `opacity:0.4-0.5`
- White text on dark backgrounds
- Glassmorphism elements: `backdrop-filter:blur(10px)`, `rgba(255,255,255,0.15)` backgrounds
- Deep colored shadows: `box-shadow: 0 20px 60px rgba(COLOR,0.25)`

**Category Color Scheme:**
| Category | Primary Gradient | Orb Colors |
|----------|-----------------|------------|
| Beginners/Teal | #0d3d4a → #1a5568 → #0f4c5c | #06b6d4, #22d3ee |
| Stress/Green | #064e3b → #065f46 → #047857 | #10b981, #34d399 |
| Sleep/Purple | #1e1b4b → #312e81 → #3730a3 | #818cf8, #a78bfa |
| Focus/Amber | #451a03 → #78350f → #92400e | #f59e0b, #fbbf24 |

**Image Optimization:**
- Large images (>1MB) cause browser rendering issues
- Created optimized web versions at 600x600px
- Example: `ella.jpg` (10MB, 4006x5008) → `ella-web.jpg` (75KB, 600x600)
- Always add cache-buster: `?v=YYYYMMDD`

**Sleep Stories Updates:**
- Changed "new story every week" → "new material unlocked each week"
- Removed misleading "Unlock them all" text (stories unlock progressively, not all at once)
- Books display in 6-column grid (reduced from 10) for better visibility
- 3D book effect with page edges: `box-shadow` for stacked pages, `::before` for spine

**Education Tiles Redesign:**
- White card backgrounds with shadow
- Gradient header with centered icon in frosted glass circle
- "Click to read" button with arrow icon
- Hover: scale(1.02), increased shadow, icon scales 1.1

**Tools Tiles Equal Height Fix:**
- Grid: `align-items:stretch`
- Links: `display:flex`
- Inner divs: `flex:1;display:flex;flex-direction:column`

**Section Background Blending:**
- Avoid hard color lines between sections
- End color of Section A should match start color of Section B
- Example: Cream (#f4f1ec) → Blue-tint (#eef1f5) creates smooth transition

**Files Modified:**
- All ~70 HTML pages (navigation)
- `sessions.html` — Atmospheric card design
- `tools.html` — Equal height tiles, atmospheric design
- `education.html` — Tile redesign with icons
- `sleep-stories.html` — Text updates, larger books
- `about.html` — Optimized Ella image
- `index.html` — Section blending, nav alignment

---

### 6 February 2026 — SEO Fundamentals & Infrastructure

**SEO Changes:**

| Change | Details |
|--------|---------|
| robots.txt | Fixed sitemap URL from `scott100-max.github.io` to `salus-mind.com` |
| sitemap.xml | Complete rebuild: 13 URLs → 76 URLs with priorities and lastmod dates |
| Canonical tags | Added `<link rel="canonical">` to all 75 public HTML pages |
| Open Graph tags | Added `og:title`, `og:description`, `og:url`, `og:type`, `og:image` to all 75 pages |
| Twitter cards | Added `twitter:card` (summary_large_image) to all 75 pages |
| Google Search Console | Verified via HTML file, sitemap submitted |

**Excluded from SEO tags:** dashboard.html, login.html, signup.html, reset-password.html, test-audio-player.html, thank-you.html, content/* (internal pages)

**Infrastructure Completed:**

| Task | Status |
|------|--------|
| Cloudflare zone activated | Active (nameservers: gerald/megan.ns.cloudflare.com) |
| media.salus-mind.com custom domain | Connected to R2 bucket, serving files |
| Media URLs in HTML | Switched from `pub-...r2.dev` to `media.salus-mind.com` (5 files) |
| R2 public dev URL | Can be disabled — custom domain is now the production path |

**Sleep Stories — 49 Titles Added:**
- All 52 books now have titles (3 with covers, 49 with gradient placeholders)
- Cover brief created at `docs/SLEEP-STORY-COVERS-BRIEF.md` for Claude Desktop
- Covers to be saved as PNG to `content/images/sleep-stories/` using kebab-case filenames
- Once covers are created, they need to be wired into `sleep-stories.html` (replace gradient backgrounds with `background:url(...)`)

**Files Modified:**
- `robots.txt` — Sitemap URL
- `sitemap.xml` — Complete rebuild
- 75 HTML pages — Canonical + OG + Twitter tags
- `googleaba2f038193703b2.html` — NEW (Google verification)
- `media.html`, `soundscapes.html`, `mindfulness.html`, `mindfulness-21-day.html`, `sessions.html` — Media URLs
- `sleep-stories.html` — 49 titled books
- `docs/PROJECT-BIBLE.md` — Infrastructure & deployment docs added
- `docs/SLEEP-STORY-COVERS-BRIEF.md` — NEW (cover generation brief)

---

### 7 February 2026 — Automated Audio QA Pipeline

**Problem:** Human was the only QA gate. Listening to every minute of every build to catch glitches. Tired, angry, ready to quit.

**Root cause:** `concatenate_with_silences()` used ffmpeg's concat demuxer for hard frame joins. Every join point was a potential click artifact. No automated detection or fixing existed.

**Solution:** Fully automated build→QA→deploy pipeline:

| Phase | What it does |
|-------|-------------|
| Build | TTS generation + edge fades on every chunk + concat + ambient mix |
| QA Scan | Detects click artifacts in silence regions (sample-level jump > peak analysis) |
| QA Fix | Applies 20ms cosine crossfades at all stitch boundaries |
| QA Loop | Rescan after fix, repeat up to 5 passes until clean |
| Deploy | Auto-upload to R2 when QA passes |

**Key additions to `build-session-v3.py`:**
- `apply_edge_fades()` — 15ms cosine fade on each voice chunk before concat
- `scan_for_clicks()` — scans mixed audio against manifest silence regions
- `patch_stitch_clicks()` — crossfades at all type-transition boundaries
- `qa_loop()` — scan→fix→rescan until clean
- `deploy_to_r2()` — wrangler upload to salus-mind bucket
- `--no-deploy` flag to build+QA without uploading

**Patched existing sessions:**
All 5 deployed sessions scanned and patched:
- 01-morning-meditation — clean (no clicks)
- 03-breathing-for-anxiety — 68 clicks patched
- 09-rainfall-sleep-journey — 10 clicks patched
- 25-introduction-to-mindfulness — 83 stitch points patched
- 38-seven-day-mindfulness-day1 — 8 clicks patched

**Rule change:** "Human ear is final gate" → "Automated QA is the gate"

---

### 7 February 2026 — QA Failure: Degraded Marco Audio Shipped

**Problem:** Loving-kindness build passed all QA checks despite severely degraded voice quality. User flagged: "audio qualities of marco completely lost." Reverb, hiss, and muffled character.

**Root causes (3 independent failures):**

| Failure | Impact |
|---------|--------|
| **QA blind spot** | QA only checked for click artifacts — zero quality checks for noise floor, HF hiss, or spectral degradation |
| **Lossless pipeline violation** | `generate_tts_chunk_resemble()` converted WAV→MP3→WAV (lossy round-trip), degrading audio at the source |
| **Wrong cleanup chain** | Used `cleanup light` (loudnorm only) which was insufficient for Resemble output |

**Fixes applied:**

1. **Lossless TTS chunk saving** — Resemble API returns native WAV; now saved directly with zero intermediate lossy steps
2. **Triple-gate QA system:**
   - Gate 1 (Quality): Measures noise floor and HF hiss in silence regions via astats, compared against master benchmarks
   - Gate 2 (Clicks): Existing click artifact scan (scan→patch→rescan loop)
   - Gate 3 (Independent Spectral): Compares frequency profile of build against master reference WAV
   - ALL three gates must pass — any failure blocks deploy
3. **Deploy gate hardened** — Deploy was unconditional before; now respects QA rejection
4. **Calibrated cleanup chain** — `highpass=80, lowpass=10000, afftdn=-25, loudnorm I=-26` matches master quality benchmarks
5. **Email always sends** (pass or fail) for visibility

**Lesson:** Click-artifact QA is necessary but NOT sufficient. Quality benchmarks against a known-good master are the only reliable way to prevent degraded audio from shipping. Every new QA mode must be validated against the master before production use.

**Rule change:** "Automated QA (clicks only) is the gate" → "Triple-gate QA (quality + clicks + spectral) is the gate"

---

### 7 February 2026 — Lossless WAV Pipeline & Email Notifications

**Problem:** MP3 intermediate files caused cumulative compression artifacts. Each processing step (TTS → cleanup → edge fades → concat → ambient mix) was re-encoding to MP3, degrading quality at every stage.

**Solution:** All intermediate audio is now WAV (PCM 16-bit). MP3 encoding happens exactly ONCE at the final step.

**Updated Pipeline:**

```
Script (... pause markers)
        │
        ▼
process_script_for_tts() → blocks with pause durations
        │
        ▼
generate_tts_chunk() → Fish API → MP3 (only lossy input)
        │
        ▼
Convert to WAV (pcm_s16le, mono, -ac 1)
        │
        ▼
apply_edge_fades() → WAV in, WAV out (15ms cosine)
        │
        ▼
generate_silence() → WAV (mono, pcm_s16le)
        │
        ▼
concatenate_with_silences() → concat demuxer → WAV
        │
        ▼
cleanup_audio_light() → loudnorm → WAV
        │
        ▼
mix_ambient() → amix → WAV
        │
        ▼
SINGLE MP3 ENCODE (libmp3lame, 128kbps) ← only lossy step
        │
        ▼
qa_loop() → scan → fix → rescan
        │
        ▼
deploy_to_r2() → send_build_email()
```

**Critical Bug Fixed — Channel Mismatch:**

| Component | Before (broken) | After (fixed) |
|-----------|----------------|---------------|
| Voice chunks (Fish) | Mono MP3 | Mono WAV (`-ac 1`) |
| Silence files | **Stereo** WAV (`cl=stereo`) | **Mono** WAV (`cl=mono`) |
| Concat result | Duration doubled (stereo+mono misinterpretation) | Correct duration |

When ffmpeg's concat demuxer joins mono and stereo PCM files, it misinterprets the sample data — stereo segments play at double duration. The fix ensures all files are mono before concatenation.

**Evidence:** Manifest calculated 13.8 min, actual WAV was 20.9 min. Difference (428s) exactly equaled total silence duration.

**Result:** QA went from 300+ false-positive clicks to **0 artifacts**. The lossless pipeline eliminated stitch clicks entirely.

---

### Email Notification System

**Service:** Resend API (free tier, 100 emails/day)
**Env var:** `RESEND_API_KEY` in `.env`
**Sender:** `onboarding@resend.dev` (switch to `build@salus-mind.com` after domain verification in Resend dashboard)
**Recipient:** `scottripley@icloud.com`

Fires automatically after every successful deploy. No UI permissions needed.

**Python note:** Must include `User-Agent: SalusBuild/1.0` header — Cloudflare blocks Python's default user-agent from reaching the Resend API.

---

### Script Writing Rules (for Fish Audio TTS)

| Rule | Why |
|------|-----|
| All text blocks must be **20-400 characters** | Blocks under 20 chars cause Fish TTS instability (timing glitches) |
| Combine short phrases with lead-in text | "May I be safe." (14 chars) → "Silently now, may I be safe." (28 chars) |
| Use `...` for pauses (not `—`) | Script parser reads `...` as pause markers |
| Single `...` = 8s, double `......` = 25s, triple = 50s (mindfulness profile) | Pause profiles defined in `PAUSE_PROFILES` dict |
| `[SILENCE: Xs]` for narrator-announced silences | Used for extended silent practice periods |
| No ellipsis in spoken text | Fish renders `...` as nervous/hesitant delivery |
| Estimate: ~7.2 chars/second for narration duration | Calibrated from Fish/Marco output |

**Pause Profiles (by category):**

| Category | Single `...` | Double `......` | Triple `........` |
|----------|-------------|-----------------|-------------------|
| sleep | 10s | 30s | 60s |
| mindfulness | 8s | 25s | 50s |
| stress | 6s | 20s | 40s |
| default | 8s | 25s | 50s |

---

### 7 February 2026 — Loving-Kindness Introduction Session

**Session:** `36-loving-kindness-intro`
**Duration:** 12.9 min (target 12 min)
**Category:** mindfulness (beginners)
**Voice:** Marco (Fish Audio)
**Ambient:** `loving-kindness-ambient` (YouTube download, trimmed to 15 min WAV, -14dB)

**Build History:**

| Attempt | Duration | Result | Issue |
|---------|----------|--------|-------|
| 1 | 21.4 min | FAIL | Chunk 3 glitch (47.6s for 46 chars) + channel mismatch |
| 2 | 20.9 min | FAIL | Chunk 36 glitch (47.6s for 99 chars) + channel mismatch |
| 3 | 12.9 min | **PASS** | Channel fix applied, no TTS glitches, 0 click artifacts |

**Deployed to:**
- Audio: `https://media.salus-mind.com/content/audio-free/36-loving-kindness-intro.mp3`
- Session page: `sessions/loving-kindness.html` (free, custom-player)
- Sessions listing: `sessions.html` (13 min, Beginners, no Premium tag)

**Website changes:** Converted from premium-locked placeholder to free session with working audio player.

---

### Pre-Build Checklist (Updated)

Before every build:
- [ ] Dry run shows correct block count and silence totals
- [ ] Only building ONE session (no parallel builds)
- [ ] Provider set to `fish` (default)
- [ ] All text blocks are 20-400 characters
- [ ] Short phrases combined with lead-in text to exceed 20 chars
- [ ] `RESEND_API_KEY` set in `.env` for email notification

### Build QA (Automated)

The scan→fix→rescan loop runs autonomously until the audio passes. No manual strike counting — the pipeline handles retries internally. After QA passes, auto-deploy to R2 and email scottripley@icloud.com.

### Execution Checklist

Run through this before considering any build complete:

**Script:**
- [ ] Script written with correct metadata header and pause markers
- [ ] All text blocks 20-400 characters
- [ ] Short phrases combined to exceed 20 chars
- [ ] Pauses humanised (no identical gap durations)

**Build:**
- [ ] Dry run completed — block count and silence totals verified
- [ ] TTS generated block-by-block (not combined)
- [ ] All intermediate files in WAV (lossless throughout pipeline)
- [ ] Edge fades applied (15ms cosine on each chunk)
- [ ] Loudness normalised only (loudnorm — NOT aggressive ffmpeg chain)
- [ ] Final encode to MP3 128kbps as the ONLY lossy step

**Ambient:**
- [ ] Ambient file longer than voice track (NEVER loop)
- [ ] Ambient mixed at correct level for category
- [ ] Ambient continues through ALL pauses and silences
- [ ] Fade in: 15 seconds, Fade out: 8 seconds

**Quality:**
- [ ] QA loop run — scan→fix→rescan until clean
- [ ] 0 voice changes in QA results

**Deployment:**
- [ ] Final audio uploaded to Cloudflare R2 (NOT committed to git)
- [ ] Audio plays from media.salus-mind.com URL
- [ ] Website HTML updated with session listing and player
- [ ] HTML changes committed and pushed to main
- [ ] Email sent to scottripley@icloud.com

---

### 7 February 2026 — Ambient Track Fix (No Looping)

**Problem:** Four sessions had ambient tracks shorter than the voice, causing the ambient to drop out partway through playback.

| Session | Voice | Old Ambient | Duration |
|---------|-------|-------------|----------|
| 03-breathing-for-anxiety | 19.3 min | birds (3.5 min) | Drops at 3.5 min |
| 25-introduction-to-mindfulness | 14.4 min | garden (1.8 min) | Drops at 1.8 min |
| 38-seven-day-mindfulness-day1 | 11.6 min | garden (1.8 min) | Drops at 1.8 min |
| ss02-the-moonlit-garden | 15.6 min | garden (1.8 min) | Drops at 1.8 min |

**Fix:** Used 8-hour ambient files (already downloaded to `youtube-downloads/`). Copied to ambient folder, remixed all 4 sessions from raw narration, redeployed to R2.

**Rule: NEVER loop ambient tracks.** Looping causes an audible glitch/breach at the loop point. Always use ambient files longer than the voice track. 8-hour ambient files exist for this reason.

**Available 8-hour ambients:**

| File | Duration | Location |
|------|----------|----------|
| `rain-8hr.mp3` | 8 hr | `content/audio/ambient/` |
| `birds-8hr.mp3` | 8 hr | `content/audio/ambient/` |
| `garden-8hr.mp3` | 12 hr | `content/audio/ambient/` |
| `rain-extended.mp3` | 70 min | `content/audio/ambient/` |
| `stream-3hr.mp3` | 3 hr | `content/audio/ambient/youtube-downloads/` |
| `loving-kindness-ambient.wav` | 15 min | `content/audio/ambient/` |

**`mix_ambient()` file search order:** `-8hr` → `-extended` → base name. WAV checked before MP3. This means `garden-8hr.mp3` is automatically preferred over `garden.mp3`.

**Pre-build ambient check added:**
- [ ] Ambient file duration exceeds estimated voice duration
- [ ] If no long ambient exists, download one BEFORE building

### File Organisation (7 February 2026)

Loose files in the repo root were organised into proper directories:

| Directory | Contents |
|-----------|----------|
| `scripts-archive/` | Old/superseded build scripts (build-session.py, build-session-v2.py, etc.) |
| `reference/` | Competitor analysis (Calm), voice-clone experiments, branding, transcripts |
| `test/` | Test files, audio reports, test HTML pages |
| `docs/` | PROJECT-BIBLE, audio quality analysis, stripe links |

**Root should only contain:** HTML pages, `build-session-v3.py`, `audition-voices.py`, `CNAME`, `robots.txt`, `sitemap.xml`, `package.json`.

---

## Marco Master Audio Standard (Resemble AI)

### Reference Master
- **Session:** `ss02-the-moonlit-garden` (12.1 min, Resemble Marco T2)
- **Backed up to:** `content/audio/marco-master/` (raw WAV, mixed MP3, final MP3, manifest)
- **Quality benchmarks (astats on silence regions):** Noise floor -27.0 dB, HF hiss (>6kHz) -45.0 dB, 0 click artifacts
- **QA thresholds:** Noise floor ≤ -26.0 dB, HF hiss ≤ -44.0 dB (1 dB margin from master)

### Voice Configuration
| Setting | Value | Why |
|---------|-------|-----|
| **Voice** | Marco T2 (`da18eeca`) | Custom voice clone — master narration voice |
| **Preset** | `expressive-story` (`6199a148-cd33-4ad7-b452-f067fdff3894`) | MUST be included in every API call |
| **pace** | 0.85 | 15% slower than default — natural narration speed for meditation/sleep |
| **pitch** | 0 | Neutral — do not alter |
| **useHd** | true | HD synthesis mode — cleaner output, less noise/hiss |
| **temperature** | 0.8 | Slight variation for natural feel |
| **exaggeration** | 0.75 | Expressive but controlled — not robotic, not over-the-top |

### What Produces Clean Audio (DO)
- Always include `voice_settings_preset_uuid` in API payload
- Use `output_format: wav` from the API (native WAV, no intermediate lossy steps)
- Use `--cleanup resemble` (default for Resemble provider)
- Cleanup chain: `highpass=80, lowpass=10000, afftdn=-25, loudnorm I=-26`
- Keep pace at 0.85 — sounds natural, not rushed
- Let Resemble handle pacing via SSML `<break>` tags with original pause durations
- One final MP3 encode at 128kbps as the only lossy step
- Save native WAV from API directly — no MP3 intermediate conversion

### What Degrades Audio (DO NOT)
- Do NOT omit the voice settings preset — produces noisy, hissy output without HD mode
- Do NOT use pace > 0.9 — too fast for meditation/sleep content
- Do NOT use `loudnorm I=-24` — target is too loud, raises noise floor above QA threshold
- Do NOT use `dynaudnorm` — amplifies silence regions, raising noise floor to -20 dB
- Do NOT convert WAV→MP3→WAV at any point — lossy round-trip degrades audio
- Do NOT use `cleanup full` (Fish chain) — the de-esser is for Fish, not Resemble
- Do NOT use random SSML break durations — use original pause values from the script
- Do NOT use `cleanup light` for Resemble — insufficient to remove residual TTS noise

### Resemble Pipeline (differs from Fish)

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
qa_loop() → TRIPLE-GATE QA:
        │   Gate 1: Quality benchmarks (noise floor, HF hiss vs master)
        │   Gate 2: Click artifact scan (scan → fix → rescan)
        │   Gate 3: Independent spectral comparison vs master WAV
        │   ALL must pass → deploy, ANY fail → block
        │
        ▼
deploy_to_r2() → send_build_email()
```

### CLI Usage (Resemble)

```bash
# Standard Resemble build (recommended — cleanup defaults to 'resemble')
python3 build-session-v3.py SESSION --provider resemble

# Dry run first (always)
python3 build-session-v3.py SESSION --provider resemble --dry-run

# Build without deploying
python3 build-session-v3.py SESSION --provider resemble --no-deploy
```

### Pre-Build Checklist (Resemble)

Before every Resemble build:
- [ ] `RESEMBLE_API_KEY` set in `.env`
- [ ] Voice settings preset UUID matches `expressive-story` in script
- [ ] Dry run shows correct chunk count and silence totals
- [ ] Only building ONE session
- [ ] Cleanup defaults to `resemble` (do NOT override to `light` or `full`)
- [ ] Ambient file longer than estimated voice track
- [ ] Master reference WAV exists at `content/audio/marco-master/marco-master-raw.wav`

### Fish vs Resemble: When to Use Each

| | Fish Audio | Resemble AI |
|---|---|---|
| **When** | Short sessions (<15 min), budget-conscious | All new production builds |
| **Voice** | Marco (Fish clone) | Marco T2 (Resemble clone) |
| **Quality** | Good but needs full cleanup chain | Clean with HD mode, calibrated cleanup |
| **Hiss** | De-esser + noise gate needed | highpass + lowpass + afftdn + loudnorm |
| **Pacing** | Natural speed, no atempo needed | pace=0.85 via voice preset |
| **Cleanup** | `--cleanup full` | `--cleanup resemble` (default) |
| **Status** | Legacy — still works | **Preferred for new builds** |

---

---

================================================================================
SECTION 13: EXTERNAL AUDIO QUALITY ANALYSIS — AUPHONIC
================================================================================
Added: 7 February 2026
Status: ACTIVE — Account registered, free tier (2h/month)

================================================================================
13.1 OVERVIEW
================================================================================

Auphonic is an automated audio post-production web service with a full REST
API. It provides AI-driven audio analysis, noise reduction, loudness
normalisation, and detailed diagnostic reporting. It has been operating since
2012, processes over 2 million tracks, and its ML models are continuously
trained on real-world audio data.

Auphonic replaces the failed Dolby.io approach (enterprise-only, no self-service
access) as the external quality gate in the Salus audio production pipeline.

PURPOSE IN SALUS PIPELINE:
- Analyse raw narration files for signal quality defects
- Provide detailed diagnostic reports (SNR, noise levels, hum, loudness)
- Optionally return a corrected audio file with noise/hum removed
- Act as an independent external validation alongside the internal analyser
- Fill detection gaps the internal analyser cannot cover (subtle hiss, hum,
  broadband noise, loudness inconsistencies)

WHAT AUPHONIC DOES NOT COVER:
- Voice change detection (different speaker mid-file)
- Content verification (repeated phrases, wrong script text)
- Speaker diarisation on single-track narration

These gaps must still be addressed by the internal analyser (voice shift via
MFCC) and optionally by a speech-to-text service for content verification.

================================================================================
13.2 ACCOUNT DETAILS
================================================================================

Service URL:        https://auphonic.com
Dashboard:          https://auphonic.com/engine/
API Base URL:       https://auphonic.com/api/
API Documentation:  https://auphonic.com/help/api/
API Examples:       https://github.com/auphonic/auphonic-api-examples

CREDENTIALS:
Store in the project .env file:
    AUPHONIC_USERNAME=your_auphonic_username
    AUPHONIC_PASSWORD=your_auphonic_password

Authentication: HTTP Basic Authentication (username:password).
No API key required — Auphonic uses account credentials directly.

FREE TIER:
- 2 hours of processed audio per month
- Credits reset monthly
- Re-processing the same input file is FREE (no additional credits)
- Free productions include an Auphonic jingle (appended to output)
- Minimum billing: 3 minutes per production

CAPACITY AT FREE TIER:
- A 12-minute session = 12 minutes of credits per analysis
- 2 hours = 120 minutes = 10 full analyses per month
- Sufficient for all development, testing, and standard production
- If batch-processing the full catalogue (~50 hours), upgrade required

PAID TIERS (if needed):
    One-time 5h    ~£4-5/hour (credits never expire)
    Recurring S    9h/month
    Recurring M    21h/month

CRITICAL: The jingle on free-tier output files does NOT affect the analysis
statistics or diagnostic report. For QA purposes (analysis only, not using
the output file as the final product), the free tier is fully functional.

================================================================================
13.3 WHAT AUPHONIC RETURNS
================================================================================

For every production, Auphonic returns:

A) PROCESSED AUDIO FILE
   - Cleaned version with noise/hum removed, loudness normalised
   - Available in any format (WAV, MP3, FLAC, etc.)
   - Download URL provided in the API response
   - NOTE: Free tier output includes an Auphonic jingle

B) AUDIO PROCESSING STATISTICS (JSON)
   Detailed diagnostic data covering:

   INPUT LEVELS:
   - loudness: integrated loudness in LUFS
   - noise_level: measured noise floor in dB
   - signal_level: signal level in dB
   - snr: signal-to-noise ratio in dB
   - lra: loudness range in LU
   - max_momentary: maximum momentary loudness in LUFS
   - max_shortterm: maximum short-term loudness in LUFS

   OUTPUT LEVELS:
   - loudness: final integrated loudness in LUFS
   - peak: true peak level in dBTP
   - lra: output loudness range in LU
   - gain_mean: average gain applied in dB
   - gain_min / gain_max: range of gain adjustments

   MUSIC/SPEECH CLASSIFICATION:
   - Timestamped segments labelled as "speech" or "music"
   - Segments must be 20+ seconds to appear
   - Useful for verifying ambient vs narration boundaries

   NOISE AND HUM REDUCTION:
   - Per-segment data showing how much noise reduction was applied (in dB)
   - Per-segment hum detection (true/false) with base frequency (50/60Hz)
   - Timestamps for every segment

   Example statistics JSON:
   {
     "statistics": {
       "levels": {
         "input": {
           "loudness": [-17.71, "LUFS"],
           "noise_level": [-49.63, "dB"],
           "snr": [26.12, "dB"],
           "signal_level": [-23.51, "dB"],
           "lra": [19.23, "LU"],
           "max_momentary": [-10.75, "LUFS"],
           "max_shortterm": [-12.71, "LUFS"]
         },
         "output": {
           "loudness": [-16.0, "LUFS"],
           "peak": [-1.0, "dBTP"],
           "lra": [3.0, "LU"],
           "gain_mean": [7.9, "dB"],
           "gain_min": [-2.5, "dB"],
           "gain_max": [21.04, "dB"]
         }
       },
       "noise_hum_reduction": [
         {"denoise": -12, "dehum": false,
          "start": "00:00:00.000", "stop": "00:01:01.528"},
         {"denoise": false, "dehum": "50Hz",
          "start": "00:01:01.528", "stop": "00:02:30.000"}
       ],
       "music_speech": [
         {"label": "speech", "start": "00:00:00.000", "stop": "00:01:13.440"},
         {"label": "music",  "start": "00:01:13.440", "stop": "00:01:35.520"},
         {"label": "speech", "start": "00:01:35.520", "stop": "00:01:59.223"}
       ]
     }
   }

C) OPTIONAL OUTPUT FORMATS
   Statistics can be exported as:
   - JSON (machine-readable, for automated pipeline)
   - YAML (machine-readable)
   - TXT (human-readable summary)

================================================================================
13.4 API USAGE
================================================================================

SIMPLE PRODUCTION (single API call, recommended for Salus):

    curl -X POST https://auphonic.com/api/simple/productions.json \
      -u "$AUPHONIC_USERNAME:$AUPHONIC_PASSWORD" \
      -F "input_file=@/path/to/raw_narration.wav" \
      -F "denoise=true" \
      -F "loudnesstarget=-24" \
      -F "output_files[0].format=wav" \
      -F "output_basename=narration_auphonic" \
      -F "action=start"

PRODUCTION WITH PRESET (for repeated use with same settings):
1. Create a preset via the web dashboard or API
2. Reference the preset UUID in subsequent productions

POLLING FOR COMPLETION:
After submitting, poll the production status:

    curl https://auphonic.com/api/production/{uuid}.json \
      -u "$AUPHONIC_USERNAME:$AUPHONIC_PASSWORD"

Status values:
- 0: File Upload
- 1: Waiting
- 2: Error
- 3: Done
- 4: Audio Processing
- 9: Incomplete

DOWNLOADING RESULTS:
When status = 3 (Done), the response includes:
- output_files[].download_url — the processed audio file
- statistics — the full diagnostic JSON

RECOMMENDED AUPHONIC SETTINGS FOR SALUS:

    Setting                  | Value           | Rationale
    -------------------------|-----------------|----------------------------------
    denoise                  | true            | Detect and remove hiss/noise
    dehum                    | auto            | Detect and remove hum if present
    loudnesstarget           | -24 LUFS        | Match Salus loudnorm target
    output_files[0].format   | wav             | Lossless for pipeline use
    output_files[0].bitrate  | (default)       | WAV ignores bitrate
    filtering                | true            | Adaptive high-pass filter

IMPORTANT: For QA analysis purposes, you may want to submit the RAW narration
(before ambient mixing) to get clean diagnostics on the voice track alone.
Submitting the mixed file would include ambient sound in the noise analysis.

================================================================================
13.5 INTEGRATION INTO QA PIPELINE
================================================================================

Auphonic slots into the existing quality gate workflow as an external
validation step. It does NOT replace the internal analyser — it complements it.

UPDATED QUALITY GATE WORKFLOW:

1. BUILD — Generate audio with TTS + ambient mixing
2. INTERNAL ANALYSE — Run analyze_audio.py on raw narration (no ambient)
   - Voice shift detection (MFCC cosine distance)
   - Click/splice detection
   - Basic hiss detection
3. AUPHONIC ANALYSE — Submit raw narration to Auphonic API
   - Upload raw narration WAV
   - Receive statistics JSON + optionally corrected file
   - Extract: SNR, noise_level, noise_hum_reduction segments
4. GATE CHECK — Evaluate combined results:

   INTERNAL ANALYSER PASS CRITERIA:
   - HIGH severity issues = 0
   - Voice shifts = 0

   AUPHONIC PASS CRITERIA:
   - Input SNR >= 25 dB (good signal quality)
   - No segments with denoise > -20 dB (excessive noise reduction needed)
   - No hum detected (dehum = false for all segments)
   - Output loudness within 1 LUFS of target (-24 LUFS)
   - Output true peak <= -1.0 dBTP

5. DECISION:
   - ALL criteria met = PASS → Proceed to ambient mixing and deployment
   - ANY criteria failed = FAIL → Log which criteria failed → Rebuild

6. IF USING AUPHONIC CORRECTED FILE:
   - Compare Auphonic output against raw narration
   - If corrections are minimal (gain changes < 3dB, denoise < -10dB),
     the raw narration is acceptable — use it directly
   - If corrections are significant, consider using the Auphonic output
     as the narration source (but note free-tier jingle limitation)

WORKFLOW DIAGRAM:

    Raw Narration (WAV)
         |
         +---> Internal Analyser (voice shifts, clicks)
         |         |
         |         v
         +---> Auphonic API (SNR, noise, hum, loudness)
                   |
                   v
              Combined Gate Check
                   |
            PASS --+--> Ambient Mix --> Deploy
                   |
            FAIL --+--> Rebuild (fresh TTS run)

================================================================================
13.6 PYTHON INTEGRATION REFERENCE
================================================================================

Minimal Python implementation for Claude Code to integrate:

    import requests
    import os
    import time

    AUPHONIC_USERNAME = os.getenv("AUPHONIC_USERNAME")
    AUPHONIC_PASSWORD = os.getenv("AUPHONIC_PASSWORD")
    AUPHONIC_API = "https://auphonic.com/api"

    def analyse_with_auphonic(audio_path, loudness_target=-24):
        """
        Submit audio file to Auphonic for analysis and processing.
        Returns the production UUID for status polling.
        """
        with open(audio_path, "rb") as f:
            response = requests.post(
                f"{AUPHONIC_API}/simple/productions.json",
                auth=(AUPHONIC_USERNAME, AUPHONIC_PASSWORD),
                files={"input_file": f},
                data={
                    "denoise": "true",
                    "loudnesstarget": str(loudness_target),
                    "output_files[0].format": "wav",
                    "action": "start"
                }
            )
        result = response.json()
        return result["data"]["uuid"]

    def poll_auphonic(uuid, timeout=300, interval=10):
        """
        Poll production status until complete or timeout.
        Returns full production data including statistics.
        """
        elapsed = 0
        while elapsed < timeout:
            response = requests.get(
                f"{AUPHONIC_API}/production/{uuid}.json",
                auth=(AUPHONIC_USERNAME, AUPHONIC_PASSWORD)
            )
            data = response.json()["data"]
            status = data["status"]
            if status == 3:  # Done
                return data
            elif status == 2:  # Error
                raise Exception(f"Auphonic error: {data.get('error_message')}")
            time.sleep(interval)
            elapsed += interval
        raise TimeoutError(f"Auphonic processing timed out after {timeout}s")

    def evaluate_auphonic_results(stats):
        """
        Evaluate Auphonic statistics against Salus quality criteria.
        Returns (pass: bool, issues: list[str])
        """
        issues = []
        levels = stats.get("levels", {})
        input_levels = levels.get("input", {})
        output_levels = levels.get("output", {})
        noise_hum = stats.get("noise_hum_reduction", [])

        # Check SNR
        snr = input_levels.get("snr", [0])[0]
        if snr < 25:
            issues.append(f"LOW SNR: {snr:.1f} dB (minimum 25 dB)")

        # Check for excessive noise reduction
        for segment in noise_hum:
            denoise = segment.get("denoise", False)
            if denoise and denoise < -20:
                issues.append(
                    f"EXCESSIVE NOISE: {denoise} dB reduction at "
                    f"{segment['start']}-{segment['stop']}"
                )

        # Check for hum
        for segment in noise_hum:
            dehum = segment.get("dehum", False)
            if dehum and dehum != False:
                issues.append(
                    f"HUM DETECTED: {dehum} at "
                    f"{segment['start']}-{segment['stop']}"
                )

        # Check output loudness
        out_loudness = output_levels.get("loudness", [0])[0]
        if abs(out_loudness - (-24)) > 1.0:
            issues.append(
                f"LOUDNESS OFF TARGET: {out_loudness:.1f} LUFS "
                f"(target -24 LUFS)"
            )

        # Check true peak
        peak = output_levels.get("peak", [0])[0]
        if peak > -1.0:
            issues.append(f"TRUE PEAK TOO HIGH: {peak:.1f} dBTP (max -1.0)")

        return (len(issues) == 0, issues)

    # USAGE IN BUILD PIPELINE:
    # uuid = analyse_with_auphonic("raw_narration.wav")
    # production = poll_auphonic(uuid)
    # stats = production["statistics"]
    # passed, issues = evaluate_auphonic_results(stats)
    # if not passed:
    #     for issue in issues:
    #         print(f"  AUPHONIC FAIL: {issue}")

================================================================================
13.7 IMPORTANT RULES
================================================================================

1. SUBMIT RAW NARRATION ONLY
   Always submit the raw narration (voice-only, no ambient) to Auphonic.
   Submitting the mixed file would confuse noise analysis with ambient sound.

2. DO NOT USE AUPHONIC OUTPUT AS FINAL AUDIO (FREE TIER)
   Free-tier output files include an Auphonic jingle. The output file is
   useful for comparison and quality assessment, but cannot be deployed as
   the final meditation audio.

3. AUPHONIC IS ANALYSIS FIRST, CORRECTION SECOND
   The primary value is the diagnostic statistics (SNR, noise segments,
   hum detection). The corrected file is a bonus, not the main purpose.

4. RE-PROCESSING IS FREE
   If you need to resubmit the same file with different settings, no
   additional credits are consumed. Use this for tuning thresholds.

5. AUPHONIC DOES NOT REPLACE HUMAN REVIEW
   Auphonic catches signal quality issues. It does not catch:
   - Voice changes (different speaker)
   - Repeated content
   - Wrong script text
   Human review remains mandatory until the internal analyser addresses
   these gaps (see Section 11.19).

6. CREDIT MANAGEMENT
   Monitor credits at https://auphonic.com/accounts/settings/
   A 12-minute session uses 12 minutes of the 120-minute monthly allowance.
   Plan batch operations to stay within the free tier where possible.

7. ENVIRONMENT VARIABLES
   Add to .env alongside existing credentials:
       FISH_API_KEY=your_fish_api_key
       AUPHONIC_USERNAME=your_auphonic_username
       AUPHONIC_PASSWORD=your_auphonic_password

================================================================================
13.8 AUPHONIC PRESET CONFIGURATION (RECOMMENDED)
================================================================================

Create a reusable preset in Auphonic for all Salus narration analysis.
This avoids specifying settings on every API call.

PRESET NAME: Salus Narration QA
SETTINGS:
    Noise & Hum Reduction:    Enabled (Auto)
    Adaptive Leveler:         Enabled
    Filtering:                Enabled (Adaptive High Pass)
    Loudness Target:          -24 LUFS
    True Peak Limit:          -1.0 dBTP
    Output Format:            WAV
    Output Statistics:        JSON (as additional output file)

To create via API:

    curl -X POST https://auphonic.com/api/preset.json \
      -u "$AUPHONIC_USERNAME:$AUPHONIC_PASSWORD" \
      -H "Content-Type: application/json" \
      -d '{
        "preset_name": "Salus Narration QA",
        "denoise": true,
        "loudnesstarget": -24,
        "output_files": [
          {"format": "wav"},
          {"format": "statistics", "ending": "json"}
        ]
      }'

Then reference the preset UUID in productions:

    curl -X POST https://auphonic.com/api/simple/productions.json \
      -u "$AUPHONIC_USERNAME:$AUPHONIC_PASSWORD" \
      -F "input_file=@narration.wav" \
      -F "preset={preset_uuid}" \
      -F "action=start"

================================================================================
13.9 PASS/FAIL CRITERIA SUMMARY
================================================================================

Metric                          | PASS              | FAIL
--------------------------------|-------------------|----------------------
Input SNR                       | >= 25 dB          | < 25 dB
Noise reduction per segment     | <= -15 dB         | > -20 dB applied
Hum detected                    | No                | Yes (any segment)
Output loudness                 | -24 +/- 1.0 LUFS  | Outside range
Output true peak                | <= -1.0 dBTP      | > -1.0 dBTP
Output loudness range (LRA)     | <= 15 LU          | > 15 LU

NOTE: These thresholds are initial estimates. Calibrate against the benchmark
session (09 - Rainfall Sleep Journey) and adjust based on real results. The
first priority after integration is to run the benchmark file through Auphonic
and use its statistics to establish baseline values.

================================================================================
13.10 FIRST STEPS AFTER INTEGRATION
================================================================================

1. ADD CREDENTIALS to .env file (AUPHONIC_USERNAME, AUPHONIC_PASSWORD)
2. RUN BENCHMARK: Submit the Rainfall Sleep Journey (09) raw narration to
   Auphonic and record the baseline statistics
3. CALIBRATE THRESHOLDS: Adjust pass/fail criteria in Section 13.9 based
   on benchmark results
4. CREATE PRESET: Set up the "Salus Narration QA" preset via the API
5. INTEGRATE INTO build-session-v3.py: Add Auphonic analysis step after
   internal analyser, before ambient mixing
6. TEST END-TO-END: Build one session with the full pipeline including
   Auphonic gate and verify the workflow

================================================================================
— END OF SECTION 13 —
================================================================================

---

================================================================================
SECTION 14: MARCO MASTER VOICE SPECIFICATION
================================================================================
Added: 7 February 2026
Status: DRAFT — Awaiting master file creation and baseline measurements

================================================================================
14.1 PURPOSE
================================================================================

The Marco Master is the single definitive reference for what Marco sounds like
across all Salus audio production. Every generated session is measured against
this file. If it does not sound like the master, it does not ship — regardless
of what automated gates report.

The master removes all ambiguity from quality assessment. Instead of asking
"does this sound good?" the question becomes "does this sound like the master?"

================================================================================
14.2 WHAT THE MASTER FILE IS
================================================================================

A single audio file containing Marco speaking a standardised reference passage.
This file is:

- The ONLY accepted definition of Marco's voice
- The benchmark for all automated comparisons (spectral, MFCC, pitch, timbre)
- The reference for all human listening reviews
- Stored permanently and NEVER overwritten
- Versioned if a new master is ever created (master_v1, master_v2 etc.)

The master is NOT a production session. It is a dedicated reference recording
created under controlled conditions specifically to capture Marco's voice
characteristics without any ambient, processing, or mixing.

================================================================================
14.3 MASTER FILE SPECIFICATION
================================================================================

AUDIO PROPERTIES:
    Format:             WAV (uncompressed, lossless)
    Sample rate:        44100 Hz
    Bit depth:          16-bit (or 24-bit if provider supports)
    Channels:           Mono
    Duration:           30-90 seconds
    Processing:         0.95x atempo only (standard Marco speed adjustment applied before locking)
    Ambient:            NONE
    Normalisation:      NONE
    Noise reduction:    NONE
    Encoding:           NONE (no MP3 conversion)

CRITICAL: The master file is raw TTS output + speed correction only. No filters,
no loudnorm, no edge fades, no cleanup of any kind. The 0.95x atempo is the
standard Marco speed adjustment — Fish Audio's native pace is slightly too fast
for meditation narration. This is the pure voice signature that everything else
is compared against.

FILE LOCATION:
    Primary:    Cloudflare R2: salus-mind/reference/marco-master-v1.wav
    Backup:     OneDrive: Salus_Mind/Reference/marco-master-v1.wav
    Local copy: Keep in project root for build script access

NAMING CONVENTION:
    marco-master-v{version}.wav
    e.g. marco-master-v1.wav, marco-master-v2.wav

================================================================================
14.4 REFERENCE PASSAGE
================================================================================

The master file must contain a passage that exercises Marco's full vocal range
as used in Salus content. The passage should include:

REQUIRED ELEMENTS:
- Opening gentle instruction (matching session openings)
- Mid-length flowing sentences (matching narrative prose)
- Short meditative phrases (matching loving-kindness / mantra style)
- A natural pause of 3-5 seconds (to capture silence characteristics)
- Closing gentle phrase (matching session endings)

SUGGESTED REFERENCE PASSAGE:
(This can be refined, but must cover all the above elements)

    Close your eyes and settle into a comfortable position. Let your
    shoulders drop away from your ears and feel the weight of your body
    being fully supported.

    Take a slow breath in through your nose, feeling your chest gently
    rise. And as you breathe out, let go of any tension you have been
    carrying. There is nowhere else you need to be right now. This
    moment is yours.

    [3-5 second pause]

    May I be safe. May I be happy. May I be healthy. May I live with
    ease.

    Now gently bring your attention back to the room around you. Take
    your time. There is no rush.

WHY THIS PASSAGE:
- "Close your eyes..." tests the gentle opening register
- "Take a slow breath..." tests flowing narrative mid-range
- The pause tests silence behaviour and any ambient noise floor
- "May I be safe..." tests short repeated phrases (the loving-kindness
  pattern that exposed the Resemble problem)
- "Now gently..." tests the closing register
- Total length ~60-70 seconds — long enough for stable measurements,
  short enough for quick generation and comparison

================================================================================
14.5 CREATING THE MASTER
================================================================================

The master must be created with the BEST available provider for Marco's voice.
Based on current evidence:

PROVIDER: Fish Audio
VOICE ID: 0165567b33324f518b02336ad232e31a (Marco)

TTS SETTINGS (IDENTICAL to production settings):
    temperature:                    0.3
    condition_on_previous_chunks:   true
    sample_rate:                    44100
    format:                         wav (NOT mp3)

GENERATION PROCESS:
1. Send the full reference passage as a SINGLE chunk to Fish Audio
2. Request WAV output (not MP3 — avoid any lossy encoding)
3. Download the raw output
4. Apply speed correction: ffmpeg -af "atempo=0.95" (standard Marco pace)
5. DO NOT apply any other processing — no filters, no loudnorm, no cleanup
6. Listen to it. Does it sound like Marco? Warm, deep, soothing, grounded?
7. If yes → this is the master. Store it permanently.
8. If no → regenerate (Fish is non-deterministic, ~60% success rate)
9. Maximum 5 attempts. If none sound right, investigate TTS settings.

HUMAN APPROVAL REQUIRED:
The master file MUST be approved by human listening before it is accepted.
No automated system can determine "this is what Marco should sound like."
The human ear is the only valid authority for establishing the benchmark.

Once approved, the master is LOCKED. It does not change unless a deliberate
decision is made to create a new version (e.g. voice provider change,
intentional voice evolution).

================================================================================
14.6 BASELINE MEASUREMENTS
================================================================================

Once the master file is created and approved, extract and record these
measurements. These become the reference values for all automated comparison.

MEASUREMENTS TO EXTRACT AND RECORD:

A) SPECTRAL CHARACTERISTICS
   - Mean MFCC coefficients (13 coefficients) — the voice "fingerprint"
   - Spectral centroid (mean and standard deviation)
   - Spectral bandwidth (mean and standard deviation)
   - Spectral rolloff frequency

B) PITCH CHARACTERISTICS
   - Mean fundamental frequency (F0) in Hz
   - F0 standard deviation (pitch variation)
   - F0 range (min to max)

C) ENERGY AND DYNAMICS
   - Mean RMS energy
   - RMS standard deviation
   - Dynamic range (peak to trough)

D) LOUDNESS (via Auphonic or pyloudnorm)
   - Integrated loudness (LUFS)
   - Noise floor (dB)
   - Signal-to-noise ratio (dB)
   - Loudness range (LU)

E) TIMING
   - Average syllable rate (syllables per second)
   - Pause duration in the silence section
   - Total duration

STORAGE:
Record all measurements in a JSON file stored alongside the master:

    {
        "version": "v1",
        "created": "2026-02-07",
        "provider": "fish_audio",
        "voice_id": "0165567b33324f518b02336ad232e31a",
        "approved_by": "human",
        "measurements": {
            "mfcc_mean": [values],
            "spectral_centroid_mean": value,
            "spectral_centroid_std": value,
            "f0_mean": value,
            "f0_std": value,
            "f0_range": [min, max],
            "rms_mean": value,
            "rms_std": value,
            "integrated_loudness_lufs": value,
            "noise_floor_db": value,
            "snr_db": value,
            "loudness_range_lu": value,
            "duration_seconds": value
        },
        "pass_thresholds": {
            "mfcc_cosine_distance_max": value,
            "f0_deviation_max_percent": value,
            "spectral_centroid_deviation_max_percent": value,
            "snr_min_db": value
        }
    }

FILE LOCATIONS:
    Master audio:       salus-mind/reference/marco-master-v1.wav
    Master measurements: salus-mind/reference/marco-master-v1-measurements.json
    Auphonic report:    salus-mind/reference/marco-master-v1-auphonic.json

================================================================================
14.7 COMPARISON METHODOLOGY
================================================================================

Every generated session is compared against the master using two methods:

METHOD 1: AUTOMATED COMPARISON (in build-session-v3.py)
Extract the same measurements from the generated audio (raw narration, before
ambient mixing) and compare against the master's baseline values.

COMPARISON METRICS:
    Metric                      | Method                  | Threshold
    ----------------------------|-------------------------|------------------
    Voice similarity (timbre)   | MFCC cosine distance    | <= TBD (calibrate)
    Pitch consistency           | F0 mean % deviation     | <= TBD (calibrate)
    Spectral match              | Centroid % deviation    | <= TBD (calibrate)
    Energy consistency          | RMS % deviation         | <= TBD (calibrate)

TBD thresholds are set during calibration (Section 14.9). They cannot be
guessed — they must be derived from real data by comparing known-good and
known-bad generations against the master.

METHOD 2: AUPHONIC COMPARISON (external validation)
Submit both the master and the generated narration to Auphonic. Compare:
    - Input SNR (should be similar — same voice, same TTS pipeline)
    - Noise floor (should be similar)
    - Gain changes applied (large differences indicate quality issues)
    - Loudness consistency

METHOD 3: HUMAN COMPARISON (final authority)
A/B listening test: play 10 seconds of the master, then 10 seconds of the
generated file. Do they sound like the same person with the same character?

Human comparison is the FINAL GATE. If automated comparison says PASS but
human says "that doesn't sound like Marco," the human wins. Always.

================================================================================
14.8 PROVIDER ROUTING
================================================================================

Not all content types suit every TTS provider. Based on the loving-kindness
failure analysis, the following routing rules apply:

FISH AUDIO — Use for:
    Content Type            | Why
    ------------------------|----------------------------------------------
    Meditation/mindfulness  | Short phrases, individual generation per block
    Loving-kindness/metta   | Repeated phrases need dedicated attention
    Body scans              | Short instructions with long pauses
    Breathwork              | Brief cues between silence
    Mantras/affirmations    | Repetitive short phrases
    Any session < 15 min    | Within Fish's consistency window

    Architecture: One TTS call per text block. Pauses stitched in post.
    Marco's voice was trained on Fish — short meditative phrases are what
    it knows. The ~60% rebuild rate is acceptable with the QA system
    catching failures early.

RESEMBLE — Use for:
    Content Type            | Why
    ------------------------|----------------------------------------------
    Sleep stories           | Long narrative prose, flowing text
    Guided journeys         | Extended storytelling passages
    Any session > 20 min    | Better consistency over long durations

    Architecture: Large ~2000-character chunks, merged with SSML breaks.
    Resemble excels at long flowing text where the model has enough context
    to maintain voice character. Do NOT use for short phrase content — the
    chunking and SSML break approach degrades voice quality on meditation-
    style scripts.

DECISION TREE:
    Is the script mostly short phrases with pauses? → Fish
    Is the script mostly long flowing narrative?    → Resemble
    Mixed content?                                  → Fish (safer default)
    Unsure?                                         → Fish (Marco's home)

CRITICAL: When switching providers for a session, ALWAYS compare the output
against the Marco master. Provider differences can subtly shift the voice
character even with the same voice ID/clone.

================================================================================
14.9 CALIBRATION PROCESS
================================================================================

Thresholds cannot be set in advance. They must be derived from real data.

CALIBRATION STEPS:

1. CREATE THE MASTER (Section 14.5)
   - Generate, listen, approve
   - Extract baseline measurements

2. GENERATE CALIBRATION SET
   - Build 5 generations of the reference passage using Fish Audio
   - Build 3 generations using Resemble (if Resemble remains in use)
   - Listen to each and classify: GOOD (sounds like Marco) or BAD
     (voice degraded, wrong character, artifacts)

3. MEASURE EVERYTHING
   - Extract all metrics from Section 14.6 for each generation
   - Run each through Auphonic and record statistics
   - Record human judgement (GOOD/BAD) for each

4. SET THRESHOLDS
   - For each metric, find the boundary between GOOD and BAD generations
   - Set the pass threshold at the tightest point that passes all GOOD
     generations and fails all BAD ones
   - If no clean boundary exists for a metric, that metric is not useful
     for automated comparison — note this and rely on other metrics

5. VALIDATE
   - Run the thresholds against the next 3 production builds
   - Do the automated results match human judgement?
   - If yes → thresholds are calibrated. Lock them.
   - If no → adjust and repeat

6. DOCUMENT
   - Record all calibration data in marco-master-v1-measurements.json
   - Record which metrics proved useful and which did not
   - Record the final thresholds with rationale

================================================================================
14.10 MASTER VERSIONING
================================================================================

The master may need to be updated if:
- The TTS provider changes or updates their model
- A deliberate decision is made to evolve Marco's voice
- The original master is discovered to have an unnoticed issue

VERSIONING RULES:
- NEVER overwrite the current master. Create a new version.
- New versions require full human approval (same process as Section 14.5)
- New versions require full recalibration (Section 14.9)
- Old versions are archived, never deleted
- The build script must reference a specific master version, not "latest"

VERSION HISTORY:
    Version | Date       | Provider | Notes
    --------|------------|----------|--------------------------------------
    v1      | TBD        | Fish     | Initial master (pending creation)

================================================================================
14.11 INTEGRATION WITH BUILD PIPELINE
================================================================================

The master comparison slots into the build pipeline as follows:

    TTS Generation (Fish or Resemble per routing rules)
         |
         v
    Raw Narration (WAV)
         |
         +---> Internal QA Gates 1-3 (clicks, stitches, qa_loop)
         |
         +---> Master Comparison (MFCC, pitch, spectral vs master)
         |
         +---> Auphonic QA (if enabled — SNR, noise, hum, loudness)
         |
         v
    Combined Gate Check
         |
    PASS: All gates passed + master comparison within thresholds
         |
         v
    Ambient Mix → Final MP3 Encode → R2 Deploy

FAIL CONDITIONS:
- Any internal gate fails → rebuild
- Master comparison outside thresholds → rebuild
- Auphonic criteria failed (if enabled) → rebuild
- Human review says "doesn't sound like Marco" → rebuild (overrides all)

THE MASTER IS THE ULTIMATE AUTHORITY.
If a file passes every automated gate but does not sound like the master
to a human listener, it fails. Full stop.

================================================================================
14.12 IMMEDIATE NEXT STEPS
================================================================================

1. GENERATE MASTER FILE
   - Use Fish Audio with the reference passage from Section 14.4
   - Raw WAV output, no processing
   - Human listens and approves

2. EXTRACT BASELINE MEASUREMENTS
   - Run spectral/pitch/energy analysis
   - Submit to Auphonic for external measurements
   - Record everything in the measurements JSON

3. RUN CALIBRATION SET
   - Generate 5 Fish versions + 3 Resemble versions of the reference passage
   - Classify each as GOOD/BAD by human listening
   - Derive comparison thresholds

4. INTEGRATE INTO BUILD SCRIPT
   - Add master comparison step to build-session-v3.py
   - Load master measurements from JSON
   - Compare each new generation against master
   - Add pass/fail criteria based on calibrated thresholds

5. REBUILD LOVING-KINDNESS
   - Use Fish Audio (per provider routing rules)
   - One TTS call per text block, pauses stitched in post
   - Compare against master before deployment

================================================================================
— END OF SECTION 14 —
================================================================================

---

*Last updated: 7 February 2026 (Sections 13-14 added: Auphonic, Marco Master Voice Specification)*
