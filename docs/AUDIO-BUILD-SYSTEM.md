# Salus Audio Build System

## Overview

The build system creates meditation sessions from scripts with:
- Voice narration via Fish TTS API (pay-as-you-go)
- Category-based pause durations
- Optional ambient background mixing

## Directory Structure

```
content/
├── scripts/           # Source scripts with metadata
│   ├── TEMPLATE.txt   # Template for new sessions
│   └── XX-name.txt    # Individual session scripts
├── audio/             # Generated audio files
│   └── ambient/       # Ambient sound loops for mixing
```

## Script Format

Every script should have a metadata header:

```
SESSION TITLE
Duration: 10 minutes
Category: mindfulness
Ambient: ocean
Style: Warm, grounded male narrator
---

Script content here...

...

More content with pauses...
```

### Metadata Fields

| Field | Required | Options |
|-------|----------|---------|
| Title | Yes | First line (free text) |
| Duration | Yes | e.g., "10 minutes" |
| Category | Yes | sleep, focus, stress, mindfulness, beginner, advanced |
| Ambient | No | ocean, rain, forest, birds, stream, wind, night, fire, garden, temple, chimes, piano, library, waterfall, none |
| Style | No | Voice direction for narrator |

### Pause Markers

Use `...` on its own line for pauses. More consecutive lines = longer pause:

- Single `...` = short pause (4-15 seconds depending on category)
- Two lines of `...` = medium pause (12-45 seconds)
- Three lines of `...` = long pause (25-105 seconds)

### Pause Duration by Category

| Category | Short | Medium | Long |
|----------|-------|--------|------|
| sleep | 8-15s | 25-45s | 60-105s |
| focus | 3-6s | 8-15s | 15-30s |
| stress | 5-10s | 15-30s | 30-60s |
| mindfulness | 5-12s | 20-40s | 45-75s |
| beginner | 4-8s | 12-25s | 25-45s |
| advanced | 8-15s | 30-60s | 75-105s |

## Usage

### Build a single session
```bash
python build-session.py 08-sleep-stories-quiet-shore
```

### Build all sessions
```bash
python build-session.py --all
```

### List all sessions
```bash
python build-session.py --list
```

### Mix ambient only (no TTS regeneration)
```bash
python build-session.py --mix-only 08-sleep-stories-quiet-shore
```

## Requirements

### Environment Variables

Create a `.env` file:
```
FISH_API_KEY=your_fish_api_key_here
```

### System Dependencies

- Python 3.8+
- ffmpeg (for audio processing)
- requests library (`pip install requests`)

### Fish TTS API

- Uses pay-as-you-go TTS
- Voice ID: `0165567b33324f518b02336ad232e31a` (Marco)
- Endpoint: `https://api.fish.audio/v1/tts`

## Ambient Sounds

Available ambient loops in `content/audio/ambient/`:

| Sound | Best for |
|-------|----------|
| ocean | Sleep stories, beach themes |
| rain | Sleep, stress relief |
| forest | Walking meditations |
| birds | Morning sessions |
| stream | Stress relief, mindfulness |
| wind | Body scans, breathing |
| night | Sleep, evening sessions |
| fire | Cozy, grounding |
| garden | Gentle sessions |
| temple | Advanced, spiritual |
| chimes | Loving-kindness |
| piano | Focus sessions |
| library | Work/focus themes |
| waterfall | Intense release |

## Adding a New Session

1. Create script: `content/scripts/XX-session-name.txt`
2. Add metadata header with Category and Ambient
3. Write content with `...` pause markers
4. Run: `python build-session.py XX-session-name`
5. Commit: `git add content/audio/XX-session-name.mp3 && git commit`
6. Push: `git push origin main`

## Maintenance

### Regenerate with different pauses
Edit the script's Category field and rebuild.

### Change ambient sound
Edit the script's Ambient field and run with `--mix-only`.

### Update voice
Change `FISH_VOICE_ID` in build-session.py and rebuild all.
