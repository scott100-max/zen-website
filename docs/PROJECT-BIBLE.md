# Salus Project Bible

**Version:** 2.0
**Consolidated:** 7 February 2026
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
14. [Expression Through Punctuation](#14-expression-through-punctuation)
15. [Auphonic Integration](#15-auphonic-integration)
16. [Build Execution](#16-build-execution)
17. [Governance](#17-governance)
18. [V3 API Emotion System (Pending Investigation)](#18-v3-api-emotion-system-pending-investigation)

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

### Section Background Blending
- Avoid hard colour lines between sections
- End colour of Section A should match start colour of Section B
- Example: Cream (#f4f1ec) → Blue-tint (#eef1f5) creates smooth transition

### Premium Content Flow
- All premium CTAs route to the Subscribe page (`apps.html`)
- Never link premium unlock buttons to Newsletter page
- Premium items display a "Premium" label and navigate to subscribe on click

### Navigation
- Two-row layout applied site-wide
- Row 1: Sessions, Mindfulness, ASMR, Sleep Stories, Learn, About
- Row 2: Tools, Reading, Newsletter, Contact (smaller, gray text, `gap:32px`, `font-size:0.9rem`)
- Sleep Stories NOT in main nav (linked from homepage "What's Inside" section)
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

**Media references in HTML:**
```html
<div class="custom-player" data-src="https://media.salus-mind.com/content/audio-free/FILENAME.mp3">
```

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
─────────────────
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

---

# PART B — AUDIO PRODUCTION

---

## 8. Production Rules (Non-Negotiable)

1. **ONE build at a time.** Never run builds in parallel — burned 100K credits once.
2. **Always dry-run first.** Check block count and silence totals before spending credits.
3. **Fish has a ~60% rebuild rate on 45-min stories.** This is expected. Rebuild until it lands.
4. **Never identical gaps.** All pauses go through `humanize_pauses()`.
5. **Marco is the only voice.** Do not audition alternatives unless Marco is discontinued.
6. **QA is automated.** The pipeline scans, patches, and re-scans until clean. No human listening required before deploy.
7. **Deploy is automatic.** Build passes QA → uploads to R2 → live. Use `--no-deploy` to hold.
8. **Email is mandatory.** Every completed build cycle ends with an email to scottripley@icloud.com — pass or fail.
9. **Fully autonomous** (except where a STOP rule is triggered — see [Section 17](#17-governance)).
10. **No OneDrive.** All files go to git (code) or Cloudflare R2 (media). Never copy files to OneDrive.
11. **Full rebuilds only.** No targeted repair, no splicing individual chunks. Splicing causes tonal seams at splice boundaries. Tested and failed.
12. **100% OR NO SHIP** — any audible glitch = FAIL.
13. **Lossless pipeline.** All intermediate audio MUST be WAV. MP3 encoding happens exactly ONCE at the final step.

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
- Raw output: -16.34 LUFS average, -4.39 dBTP peak
- Chunk volume spread: ~8 dB (Auphonic leveller data)
- SNR: 45+ dB (broadcast quality without processing)
- No hum, minimal noise floor

**The Fish API is stateless.** There is NO `condition_on_previous_chunks` parameter in the Fish Audio TTS API. Each API call is completely independent. Voice conditioning between chunks is implemented CLIENT-SIDE in `build-session-v3.py` by passing the previous chunk's audio as the `references` input for the next chunk. This is our pipeline's feature, not a Fish feature. Each chunk can be regenerated independently as long as the correct reference audio is provided.

**Fish cleanup chain (CANONICAL — use this, nothing else):**
1. Edge fades: 15ms cosine on each chunk before concatenation
2. Per-chunk loudnorm: `loudnorm=I=-26:TP=-2:LRA=11` on each chunk BEFORE concatenation
3. High shelf boost: `highshelf=f=3000:g=3` (restores presence lost by loudnorm)
4. Final encode: 128kbps MP3

**DO NOT APPLY to Fish output:**
- ~~lowpass=f=10000~~ (kills clarity and consonant detail)
- ~~afftdn=nf=-25~~ (muffles the voice — noise floor already clean at 45 dB SNR)
- ~~dynaudnorm~~ (amplifies silence — NEVER use)
- ~~aggressive de-essers~~ (removes natural sibilance)
- ~~highpass=80~~ (not needed for Fish — no low-frequency noise)

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

**LESS IS MORE.** Fish Audio TTS output is already broadcast-quality clean (45 dB SNR, -62 dB noise floor). Every processing step trades clarity and character for consistency. Apply the minimum necessary and nothing more.

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
PER-CHUNK LOUDNORM: loudnorm=I=-26:TP=-2:LRA=11 on EACH chunk individually
        │
        ▼
generate_silence() → WAV (mono, pcm_s16le) via humanize_pauses()
        │
        ▼
concatenate_with_silences() → concat demuxer → WAV
        │
        ▼
HIGH SHELF BOOST: highshelf=f=3000:g=3 (restores presence after loudnorm)
        │
        ▼
mix_ambient() → amix → WAV
        │
        ▼
SINGLE MP3 ENCODE (libmp3lame, 128kbps) ← ONLY lossy step
        │
        ▼
qa_loop() → 10-GATE QA (see Section 12)
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
qa_loop() → 10-GATE QA (see Section 12)
        │
        ▼
deploy_to_r2() → send_build_email()
```

### Per-Chunk Loudnorm (Fish only)

Apply `loudnorm` to each chunk individually to -26 LUFS BEFORE concatenation. This fixes the 6-8 dB volume swings between chunks at source rather than relying on whole-file normalisation after assembly. Previously, chunks were concatenated raw and then the whole file was normalised — this masked volume inconsistencies rather than fixing them.

### Known Trade-Off: Loudnorm vs Presence

Loudnorm slightly reduces Marco's presence and "sharpness" — the voice sounds slightly muted compared to raw Fish output (the "behind a sheet" problem).

**Fix:** High shelf boost `highshelf=f=3000:g=3` — lifts everything above 3kHz by 3dB (presence and articulation range). Applied AFTER loudnorm, BEFORE ambient mixing. Start at +3dB, test up to +4 or +5 if 3 feels subtle.

**Experimental option:** Skip loudnorm entirely. Given Fish's 45 dB SNR, raw TTS with edge fades only, straight to ambient mix. Risk: volume inconsistency between chunks (~8 dB spread). Worth testing on a future build.

### Atempo

Marco standard speed adjustment: 0.95x atempo. Applied to the master and consistently to all production. This gives Marco a slightly slower, more deliberate delivery for meditation pacing.

**Exception:** Sleep stories built with Fish/Marco — no atempo needed, natural speed is correct.

### Channel Mismatch Bug (RESOLVED)

All files MUST be mono before concatenation. When ffmpeg's concat demuxer joins mono and stereo PCM files, it misinterprets the sample data — stereo segments play at double duration. Silence files must be generated as mono (`cl=mono`), not stereo.

### Ambient Rules
- Ambient file MUST be longer than voice track — **NEVER loop**
- Looping causes an audible glitch at the loop point
- Use 8-hour ambient files (available in `content/audio/ambient/`)
- Background ambient must not fade in until narrator introduction is complete
- Fade in: 15 seconds, Fade out: 8 seconds
- `mix_ambient()` file search order: `-8hr` → `-extended` → base name. WAV checked before MP3.

**Available 8-hour ambients:**

| File | Duration | Location |
|------|----------|----------|
| `rain-8hr.mp3` | 8 hr | `content/audio/ambient/` |
| `birds-8hr.mp3` | 8 hr | `content/audio/ambient/` |
| `garden-8hr.mp3` | 12 hr | `content/audio/ambient/` |
| `rain-extended.mp3` | 70 min | `content/audio/ambient/` |
| `stream-3hr.mp3` | 3 hr | `content/audio/ambient/youtube-downloads/` |
| `loving-kindness-ambient.wav` | 15 min | `content/audio/ambient/` |

---

## 12. QA Gate System

### Overview

10 gates. Gates 1-8 and 10 must ALL pass — any failure blocks deploy. Gate 9 runs regardless for debugging. Gate 10 is new (speech rate anomaly detection).

### Gate 1: Quality Benchmarks
Measures noise floor and HF hiss in silence regions via `astats`, compared against master benchmarks.

### Gate 2: Click Artifacts
Scan → patch → rescan loop. Detects click artifacts in silence regions (sample-level jump > peak analysis). Applies 20ms cosine crossfades at all stitch boundaries. Repeats up to 5 passes.

### Gate 3: Independent Spectral Comparison
Compares frequency profile of build against master reference WAV.

**CRITICAL FIX REQUIRED — SLIDING WINDOW:** Gate 3 currently evaluates hiss across the full chunk duration. A 3-second hiss burst inside a 15-second chunk gets averaged out and falls below threshold. Replace whole-chunk hiss measurement with a **sliding window of 1-2 seconds**. If ANY window within a chunk exceeds the hiss threshold, the chunk fails.

### Gate 4: Voice Comparison
MFCC cosine + F0 deviation vs Marco master. Uses PRE-CLEANUP audio (see Section 10, Voice Comparison Gate).

**Thresholds:** MFCC ≤0.008 (same-text), ≤0.06 (production). F0 deviation ≤10%.

### Gate 5: Loudness Consistency
Per-second RMS sliding window — catches per-chunk loudness surges.

### Gate 6: HF Hiss Detector
Sliding-window HF-to-total energy ratio on POST-CLEANUP audio. Catches sustained hiss that survives cleanup. 10s minimum duration, 6 dB threshold. Runs post-cleanup.

### Gate 7: Volume Surge/Drop
Local-mean comparison with silence exclusion. 8/12 dB thresholds.

**Low-baseline skip:** Skip detection when local mean energy is below -28 dB. This threshold represents ambient/silence regions, not speech. Flagging silence as "surges" is a false positive.

### Gate 8: Repeated Content
MFCC fingerprint + Whisper STT with DUAL AGREEMENT — both must flag the same timestamps to confirm. 8-word minimum.

**Expected-Repetitions metadata:** Add an `Expected-Repetitions` field to the script header. Phrases listed there are excluded from Gate 8's duplicate detection for that session. This replaces the growing global ignore list.

```
Expected-Repetitions: May I be, May you be, May they be, May all beings be
```

### Gate 9: Visual Report
PNG with waveform, spectrogram, energy plot, summary. Runs ALWAYS, not pass/fail.

### Gate 10: Speech Rate Anomaly Detection (NEW)

No gate previously existed for detecting sudden acceleration or deceleration in speech tempo.

**Implementation:**
- Measure syllable rate (or word density per second) across the session
- Establish a baseline pace from the first N chunks
- Flag any chunk or segment where speech rate exceeds 1.5× the session baseline
- Use sliding windows of 2 seconds
- Threshold: flag if any 2-second window exceeds 130% of session average speech rate

**Meditation-specific rule:** Speech rate should be consistently slow (~100-120 wpm / 8-10 chars per second). Sudden acceleration to normal conversational pace (~160 wpm) is a defect even if the words are correct.

### Gate Coverage Audit (Required)

Before the next build, review ALL gates for:
- Are all gates using per-window analysis or whole-chunk averaging?
- Which gates would benefit from sliding window detection?
- Are there other common TTS artefacts (clicks, pops, breath sounds, mouth sounds) not covered?

Report audit findings before building.

### Overgeneration Retry Logic

If a generated chunk's duration exceeds 2× the expected duration for its character count, reject it and regenerate immediately. Up to 3 retries per chunk before flagging as build failure.

**Expected duration:** Character count ÷ speaking rate. Meditation speaking rate ≈ 100-110 wpm ≈ 8-10 characters per second.

---

## 13. Script Writing Rules

### Block Size

| | Characters |
|---|---|
| **Minimum** | **50** (below 50 causes TTS instability and hiss — root cause of all hiss failures) |
| **Sweet spot** | 50-200 |
| **Maximum** | 400 (longer blocks trend toward monotone) |

Blocks under 50 characters must be merged with adjacent blocks or expanded with additional content.

**For loving-kindness/mantra content:** Combine 3-4 short phrases into one block with internal ellipses. Each block 76-150 characters. This gives TTS enough context while ellipses create internal rhythm.

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
| All blocks **50-400 characters** | Under 50 causes hiss; over 400 causes monotone |
| Combine short phrases with lead-in text | "May I be safe." (14 chars) → "Silently now, may I be safe." (28 chars) — still needs combining further to reach 50 |
| Use `...` for pauses (not `—`) | Script parser reads `...` as pause markers |
| No ellipsis in spoken text | Fish renders `...` as nervous/hesitant delivery |
| Scripts must contain ZERO parenthetical tags | In-text emotion tags don't work (see Section 18) |
| Estimate ~7.2 chars/second for narration duration | Calibrated from Fish/Marco output |

### Script Metadata Header

```
Title: [session name]
Category: [sleep/mindfulness/stress/default]
Duration-Target: [minutes]
API-Emotion: calm
Expected-Repetitions: [comma-separated phrases for Gate 8]
```

- `API-Emotion` is a per-session setting read by the build script. Default: `calm`. Only relevant if V3 migration passes investigation (see Section 18).
- `Expected-Repetitions` excludes listed phrases from Gate 8's duplicate detection.

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
> 76-84 characters per block. Ellipses create breathing rhythm without splitting into dangerously short chunks.

---

## 15. Auphonic Integration

**Status:** ACTIVE — Measurement gate ONLY. Do not use Auphonic output as production audio.

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
- Per-segment analysis (problem localisation)

### What Auphonic Is NOT For

- Processing/cleaning the audio (Voice AutoEQ damages Marco's bass warmth)
- Leveling (causes breath wobble on meditation content with long silences)
- EQ (cuts defining bass characteristics)

### Pass/Fail Criteria

| Metric | PASS | FAIL |
|--------|------|------|
| Input SNR | ≥ 40 dB | < 40 dB |
| Background Level | ≤ -55 dB | > -55 dB |
| Hum detected | No | Yes (any segment) |
| Output loudness | -26 ±1.0 LUFS | Outside range |
| Output true peak | ≤ -2.0 dBTP | > -2.0 dBTP |
| Output LRA | ≤ 16 LU | > 16 LU |
| Leveler gain spread | ≤ 10 dB | > 10 dB |

SNR threshold at 40 dB based on Fish baseline of 45.26 dB. The old 25 dB threshold was too permissive for TTS content.

### Auphonic Preset Settings

| Setting | Value |
|---------|-------|
| Adaptive Leveler | Enabled |
| Filtering | Enabled (Voice AutoEQ) |
| Loudness Target | -26 LUFS |
| Max Peak Level | -2 dBTP (ATSC A/85) |
| Noise Reduction | Static: remove constant noises only, 6 dB (low) |
| Remove Reverb | Off |
| Automatic Cutting | Off (preserve meditation silences) |
| Output Format | WAV 16-bit PCM, optimal stereo |

**Note:** The "silent segments >30s" warning is a FALSE POSITIVE for meditation content. Ignore it.

### First Baseline Results (7 February 2026)

File: `36-loving-kindness-intro_precleanup.wav`

| Metric | Value |
|--------|-------|
| Program Loudness | -16.34 LUFS |
| LRA | 15.21 LU |
| Max Peak Level | -4.39 dBTP |
| SNR mean | 45.26 dB |
| Background Level | -62.25 dB |
| Hum | Not detected |

**Key conclusion:** Fish Audio TTS output is broadcast quality (40-50 dB SNR standard). The aggressive cleanup chain was solving a problem that barely existed.

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
- [ ] All text blocks 50-400 characters (MINIMUM 50, not 20)
- [ ] Short phrases combined to exceed 50 chars
- [ ] Pauses humanised (no identical gap durations)
- [ ] Zero parenthetical emotion tags in text
- [ ] `Expected-Repetitions` set if session has intentional structural repetition

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
- [ ] All 10 QA gates run
- [ ] 0 voice changes in QA results

**Deployment:**
- [ ] Final audio uploaded to Cloudflare R2 (NOT committed to git)
- [ ] Audio plays from `media.salus-mind.com` URL
- [ ] Website HTML updated with session listing and player
- [ ] HTML changes committed and pushed to main
- [ ] Email sent to scottripley@icloud.com

### Email Notification System

| | |
|---|---|
| **Service** | Resend API (free tier, 100 emails/day) |
| **Env var** | `RESEND_API_KEY` in `.env` |
| **Sender** | `onboarding@resend.dev` (switch to `build@salus-mind.com` after domain verification) |
| **Recipient** | `scottripley@icloud.com` |
| **Header** | Must include `User-Agent: SalusBuild/1.0` (Cloudflare blocks Python default) |
| **Trigger** | Every completed build — pass or fail |

### Deployed Sessions

| Session | Duration | Provider | Status |
|---------|----------|----------|--------|
| 01-morning-meditation | — | Fish | Deployed, patched (0 clicks) |
| 03-breathing-for-anxiety | 19.3 min | Fish | Deployed, patched (68 clicks) |
| 09-rainfall-sleep-journey | — | Fish | Deployed, patched (10 clicks) |
| 25-introduction-to-mindfulness | 14.4 min | Fish | Deployed, patched (83 stitch points) |
| 36-loving-kindness-intro | 12.9 min | Fish | Deployed (build 3, 0 click artifacts) |
| 38-seven-day-mindfulness-day1 | 11.6 min | Fish | Deployed, patched (8 clicks) |

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

### Build State Persistence

All build state must be persisted to a file after every step. Never rely on conversation context for:
- Strike counter
- Build sequence number
- QA pass/fail results per gate
- Which script version is being built

**Reason:** Context compaction at 200K tokens is lossy. If Code compacts mid-build, it can lose track of state. Persistent state files survive compaction.

### Environment Variables

```
FISH_API_KEY=your_fish_api_key
RESEMBLE_API_KEY=your_resemble_api_key
RESEND_API_KEY=your_resend_api_key
AUPHONIC_USERNAME=your_auphonic_username
AUPHONIC_PASSWORD=your_auphonic_password
STRIPE_SECRET_KEY=your_stripe_secret
STRIPE_WEBHOOK_SECRET=your_webhook_secret
```

---

## 18. V3 API Emotion System (Pending Investigation)

**Status:** NOT YET IMPLEMENTED. Investigation required before any build attempt.

### Background

The original emotion approach (in-text parenthetical tags like `(relaxed)`, `(calm)`) FAILED. Marco's cloned voice read every tag as literal spoken text. The meditation opened with the word "sincere" spoken aloud. **In-text emotion tags do not work with cloned voices on the S1 model.**

Fish Audio's V3 model versions (`v3-turbo` and `v3-hd`) support a separate `emotion` parameter in the API request body. The text stays completely clean.

### Proposed API Change

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

### V3 Bonus Parameters

- `"speed": 0.5-2.0` (default 1.0) — test 0.85-0.9 for meditation pacing
- `"volume": -20 to 20` (default 0) — leave at 0, handle in post-processing

### Investigation Steps (STOP rules apply)

**3a. Marco compatibility with V3**
- Test ONE chunk with Marco's reference_id + `"version": "v3-hd"` + `"emotion": "calm"`
- If fails → test `v3-turbo`
- **STOP if neither works with cloned voice**

**3b. Voice conditioning chain on V3**
- Test 3 sequential chunks
- Compare voice consistency vs S1 output
- **STOP if conditioning breaks**

**3c. Credit cost comparison**
- Check V3-hd vs S1 cost per character
- **STOP if >3× cost without human approval**

**3d. M Series investigation**
- Fish M Series: "Stable, better emotion" (turbo/HD variants)
- Determine if separate from V3 or same
- Test Marco compatibility if separate

### Pipeline Changes (conditional on investigation passing)

- Add `"version": "v3-hd"` to all TTS requests
- Add `"emotion": "calm"` to all TTS requests (or read from `API-Emotion` metadata)
- Remove any code parsing or injecting emotion tags
- Remove any code stripping parenthetical content
- Test `speed=0.9` with first build

### Fallback (if V3 incompatible)

- Stay on S1/v1
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

Full consolidation pass. Resolved contradictions (loudnorm -24 vs -26, block minimum 20 vs 50, five conflicting cleanup chains). Integrated Brief Part 2 items 2-9 and Brief Part 3. Added Gate 10 (speech rate), Gate 3 sliding window fix, stop rule governance, build state persistence, overgeneration retry logic, per-chunk loudnorm. Restructured from chronological amendments to functional sections.

---

*Last updated: 7 February 2026 — Bible v2.0: Full consolidation. All contradictions resolved. Brief Parts 2 and 3 integrated.*
