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
- **DNS managed by:** Cloudflare
- GitHub Pages A records: `185.199.108-111.153`
- `www` CNAME → `scott100-max.github.io`
- `media` CNAME → R2 bucket (proxied)

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
- **3-Strike Rule** - max 3 rebuild attempts before escalating
- **Human ear is final gate** - analyzer is pre-screening only

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

*Last updated: 6 February 2026*
