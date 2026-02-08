# Audio Echo Diagnostic Report — Session 36 (Loving-Kindness Intro)

## Summary

The echo in `36-loving-kindness-intro.mp3` is **not caused by post-processing**. The file currently served is the **original build** from `build-all-audio.py`, which has zero audio processing — no crossfade patching, no loudnorm, no gate system. The echo originates from the **Fish Audio TTS output itself**.

## Key Findings

### 1. The served audio file is the original, unmodified build

- File: `content/audio/36-loving-kindness-intro.mp3` (11,397,790 bytes)
- Added in commit `e515526` ("Add all session audio (40 files)")
- **Never modified since** — file size is identical to the original commit
- Referenced by `sessions/loving-kindness.html` via relative path `../content/audio/36-loving-kindness-intro.mp3`
- No references to `media.salus-mind.com` or `content/audio-free/` anywhere in the codebase

### 2. `build-all-audio.py` has zero echo-causing processing

The pipeline that built this file is trivially simple:

1. **Fish Audio TTS** → raw MP3 per text segment
2. **ffmpeg** → convert each MP3 to WAV (44100Hz, mono, PCM s16le) — no filters applied
3. **ffmpeg concat demuxer** → join WAV files sequentially (no crossfade, no overlap)
4. **ffmpeg** → encode concatenated WAV to MP3 at 192kbps

There is:
- No crossfading at segment boundaries
- No loudness normalization (`loudnorm`)
- No DC offset removal
- No shelf boost
- No gate system or QA processing
- No `patch_stitch_clicks()` function

### 3. `build-session-v3.py` does not exist in this repository

- Not in the working tree
- Not in any branch (`git log --all --diff-filter=A`)
- Not in git history (searched all object store commits)
- Not recoverable from available session transcripts (3 sessions searched)

A previous Claude Code session (evidenced by screenshots) created `build-session-v3.py` with a 14-gate QA system and committed it as `9615318`. However:
- Commit `9615318` is **not in the current git history** (likely removed by force-push or rebase)
- The `content/audio-free/` directory (where rebuilt audio would be stored) does not exist
- No HTML pages reference the CDN or audio-free paths
- The session's rebuild of `36-loving-kindness` was stored separately and is not what's currently served

### 4. `build-morning-v2.py` crossfade is correct (for reference)

The only crossfade implementation in the codebase (used only for session 01) does **in-place replacement**, not overlay:

```python
def crossfade_join(a, b, ms=5):
    fade = int(RATE * ms / 1000)  # 5ms = ~220 samples
    for i in range(fade):
        mix = i / fade
        a_idx = len(a) - fade + i
        a[a_idx] = int(a[a_idx] * (1 - mix) + b[i] * mix)  # replaces, not adds
    a.extend(b[fade:])  # appends rest, skipping crossfaded portion
    return a
```

This cannot produce echo — it blends at the boundary and extends, never duplicating audio.

## Conclusion

The echo is baked into the **Fish Audio TTS response**. Since `build-all-audio.py` passes text directly to the API and writes the raw response to disk with no post-processing, the echo must be a characteristic of:

- The specific voice model (`0165567b33324f518b02336ad232e31a`)
- The Fish Audio `s1` model's rendering of this particular script
- Possible room reverb/ambience in the reference voice

## Recommended Fix

1. **Regenerate the audio** using `build-all-audio.py` with a fresh TTS call — Fish Audio model updates may have resolved the echo
2. If echo persists, try a **different voice ID** or add a `--dry` parameter to the API request
3. If the echo is acceptable but excessive, apply a **de-reverb filter** post-build:
   ```bash
   ffmpeg -i input.mp3 -af "highpass=f=80,lowpass=f=12000,acompressor=threshold=-20dB:ratio=4" output.mp3
   ```
4. Consider whether `build-session-v3.py`'s gate system (now lost) needs to be **reconstructed** for future builds

## Environment Notes

- Repository: `scott100-max/Salus-Website`
- Deployment: GitHub Pages (no Cloudflare Workers/Pages/R2 configured)
- TTS Provider: Fish Audio API (voice `0165567b33324f518b02336ad232e31a`, model `s1`)
- No `ffprobe` or audio analysis tools available in current environment
- Git clone is shallow (depth 50) — full history not available
