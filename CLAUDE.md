# CLAUDE.md — Salus Website Project Instructions

## Architecture

|Service      |Purpose                |URL                                                           |
|-------------|-----------------------|--------------------------------------------------------------|
|GitHub Pages |Website (HTML, CSS, JS)|https://salus-mind.com                                        |
|Cloudflare R2|Media files (MP3, MP4) |https://media.salus-mind.com                                  |
|Cloudflare   |DNS                    |Nameservers: gerald.ns.cloudflare.com, megan.ns.cloudflare.com|
|Supabase     |Auth & user data       |https://egywowuyixfqytaucihf.supabase.co                      |

## Cloudflare R2 Credentials

- **Bucket:** salus-mind
- **Account ID:** e798430a916680159a81cf34de0db9c2
- **API Token:** yYNUa2enwfPdNnVrfcUQnWHhgMnebTSFntGWbwGe

### Upload Commands

```bash
# Upload audio file to R2:
npx wrangler r2 object put salus-mind/content/audio-free/FILENAME.mp3 --file=./FILENAME.mp3

# Upload sound/ASMR file:
npx wrangler r2 object put salus-mind/content/sounds/FILENAME.mp3 --file=./FILENAME.mp3

# Upload video:
npx wrangler r2 object put salus-mind/content/video/FILENAME.mp4 --file=./FILENAME.mp4
```

### R2 File Paths

|Content Type|R2 Path            |
|------------|-------------------|
|Free audio  |content/audio-free/|
|Sounds/ASMR |content/sounds/    |
|Video       |content/video/     |
|Reference   |reference/         |

## Fish API Key

FISH_API_KEY: (stored in GitHub repository secrets — retrieve from GitHub Actions if needed for TTS tasks)

## Git Workflow

Always push directly to main. Do not create branches or PRs. The GitHub API is blocked by the network proxy.

## Critical Rules

1. **NEVER commit audio or video files to Git.** All media goes to Cloudflare R2. The .gitignore excludes *.mp3, *.mp4, *.wav and media directories.
1. **Website deploys automatically** when code is pushed to the main branch via GitHub Pages. No manual deployment needed.
1. **Media references in HTML** must use the R2 URL:

   ```html
   <div class="custom-player" data-src="https://media.salus-mind.com/content/audio-free/FILENAME.mp3">
   ```
1. **Always verify the live site** after claiming changes are deployed. Use WebFetch to confirm.
1. **Root directory should only contain:** HTML pages, build-session-v3.py, audition-voices.py, CNAME, robots.txt, sitemap.xml, package.json.

## Directory Structure

|Directory                  |Contents                                                           |
|---------------------------|-------------------------------------------------------------------|
|scripts-archive/           |Old/superseded build scripts                                       |
|reference/                 |Competitor analysis, voice-clone experiments, branding, transcripts|
|test/                      |Test files, audio reports, test HTML pages                         |
|docs/                      |PROJECT-BIBLE, audio quality analysis, stripe links                |
|content/audio-free/vault/  |TTS vault dirs per session (gitignored — local only, NOT in git)   |
|content/audio-free/        |Final deployed MP3s per session (gitignored — local only)          |
|content/audio/ambient/     |Ambient tracks (8-hour versions preferred)                         |
|content/audio/marco-master/|Master reference WAVs and measurements                             |

## Supabase

- **Project URL:** https://egywowuyixfqytaucihf.supabase.co
- **Project ID:** egywowuyixfqytaucihf
- **IMPORTANT:** Use the Legacy JWT anon key (starts with eyJ…), NOT the new sb_publishable_ format.

## Terminology

|Use                              |Do Not Use                         |
|---------------------------------|-----------------------------------|
|Sample                           |Free (for sessions/sounds sections)|
|Salus Premium                    |The Salus app                      |
|Premium                          |Subscribe to Unlock                |
|Web-only, iOS/Android coming soon|Available on all devices           |
|New material unlocked each week  |New story every week               |

## Vault Safety — STOP before building

**Vaults are gitignored** (`content/audio-free/` is in `.gitignore`). You CANNOT determine vault existence from git — you MUST check the local filesystem.

**Vault path:** `content/audio-free/vault/{session-slug}/` (e.g. `content/audio-free/vault/91-the-body-scan/`)
Each vault contains: `c00/`, `c01/`, ... chunk dirs with WAV candidates, plus `chunks.json`, `live-picks.json`, `unified-review.html`.

Before running `vault-builder.py` or generating TTS for ANY session:
1. **Check `content/session-registry.json`** — if status is `"deployed"`, the session is DONE. Do NOT rebuild.
2. **Check the local vault directory** — `ls content/audio-free/vault/{session}/` to see if candidates already exist.
3. **Check for `live-picks.json`** in the vault dir — if it exists, a human has already picked candidates. Rebuilding would DESTROY those picks.

**Sessions with completed human picks:** S91 (The Body Scan) — 49 chunks, 100 candidates each, fully hand-picked 15 Feb 2026.

## Style Notes

- Latin phrase on all pages: "Salūs — Latin: health, safety, well-being"
- Light backgrounds: color:var(–mid-gray);opacity:0.7
- Dark/hero backgrounds: color:rgba(255,255,255,0.6)
