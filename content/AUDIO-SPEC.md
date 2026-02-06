# Salus Audio Session Specifications

Guidelines for structuring meditation and sleep audio sessions.

---

## Sentence Length Rules

**Shorter sentences = calmer delivery.** Long sentences rush the listener and create anxiety.

### Maximum Word Counts

| Sentence Type | Max Words | Example |
|---------------|-----------|---------|
| **Opening sentences** | 8-10 | "Welcome. Get comfortable. Close your eyes." |
| **Standard narration** | 15-18 | "Now bring your attention to the breath moving in and out." |
| **Instructional** | 20 | "When you notice your mind has wandered, gently bring your attention back to the breath." |
| **Absolute maximum** | 25 | Never exceed — split into two sentences |

### Breaking Long Sentences

**Before (too long — 32 words):**
> "As you settle into this moment and allow your body to relax into the surface beneath you, notice how the weight of your body is fully supported and there's nothing you need to do."

**After (split — 12 + 15 words):**
> "Settle into this moment. Allow your body to relax into the surface beneath you."
> ...
> "Notice how your weight is fully supported. There's nothing you need to do."

### Script Writing Rules

1. **One idea per sentence** — Don't chain concepts with "and"
2. **Use periods, not commas** — Each thought gets its own sentence
3. **Count words** — If over 20, split it
4. **Read aloud** — If you run out of breath, it's too long
5. **Add pauses liberally** — Use `...` between sentences for natural breathing rhythm

---

## Silence Requirements by Duration

### Standard Silence Durations

All Salus audio uses these standardised silence lengths:

| Duration | Script Notation | Use |
|----------|-----------------|-----|
| 5s | `...` | Brief breath pause between sentences |
| 10s | `[10 second pause]` | End of thought/section |
| 15s | `[15 second pause]` | Transition between themes |
| 30s | `[30 second pause]` | Reflective pause (no announcement needed) |
| 45s | `[45 second pause]` | Extended reflection |
| 60s | `[60 second pause]` | Deep pause — MUST announce |
| 75s | `[75 second pause]` | Extended deep pause — MUST announce |
| 90s | `[90 second pause]` | Maximum silence — MUST announce |

### Required Silences by Production Length

**Ambient continues through ALL silences.**
**Silences 60s+ MUST be announced.**

| Silence | 5 min | 10 min | 15 min | 20 min | 30 min | 45 min+ |
|---------|-------|--------|--------|--------|--------|---------|
| 5s | 8-12x | 15-20x | 20-30x | 25-35x | 35-50x | 50-70x |
| 10s | 3-4x | 5-6x | 6-8x | 8-10x | 10-12x | 12-15x |
| 15s | 2-3x | 4-5x | 5-6x | 6-7x | 7-9x | 9-11x |
| 30s | 2x | 2x | 3x | 3-4x | 4-5x | 5-6x |
| 45s | - | 2x | 2x | 2-3x | 3x | 3-4x |
| 60s | - | 2x | 2x | 2x | 2-3x | 3x |
| 75s | - | 2x | 2x | 2x | 2x | 2-3x |
| 90s | - | - | 2x | 2x | 2x | 2-3x |
| 120s | - | - | - | 2x | 2x | 2x |
| **Max** | 30s | 75s | 90s | 120s | 120s | 120s |
| **Total %** | 20-30% | 35-45% | 35-45% | 35-45% | 35-45% | 35-45% |

*Updated Feb 2026 after Calm benchmarking (they use 2x 120s in 10-min sessions = 40% silence)*

### Silence Distribution Formula

**Quick calculation for any duration:**

```
5s pauses:  ~4 per minute of content
10s pauses: ~1 per 2 minutes
15s pauses: ~1 per 3 minutes
30s+ pauses: See tables above
```

**Total silence should be 15-25% of production length.**
- 10 min production → 1.5-2.5 min total silence
- 20 min production → 3-5 min total silence
- 45 min production → 7-11 min total silence

---

## Silence Announcement Phrases

**Silences of 60 seconds or longer MUST be announced.** Otherwise listeners think audio has stopped.

Announcement phrases:

- "I'm going to be quiet now for a little while. Just let the [rain/waves/sounds] hold you..."
- "I'll be silent for a moment. There's nothing you need to do..."
- "Take this time in stillness. I'll return in a moment..."
- "Rest here now. I'll be back soon..."
- "Let's sit together in silence for a while..."
- "I'm going to stop talking now. Just breathe..."

**IMPORTANT:** Never have extended silence without ambient sound — listener must know audio is still playing.

---

## CRITICAL SAFETY: Breathing Exercise Pauses

**HEALTH RISK — AUTOMATIC REJECT IF VIOLATED**

Pauses between breathing instructions (inhale, hold, exhale) **MUST** use explicit `[X second pause]` markers. **NEVER** use `...` markers for breathing gaps. The randomised pause profiles will inflate breathing cycles to dangerous durations (30-40+ seconds observed on 6 Feb 2026).

**Mandatory breathing pause format:**
```
Breathe in slowly.
[4 second pause]

Now hold your breath gently.
[5 second pause]

And breathe out through your mouth.
[6 second pause]
```

**Rules:**
- Total breathing cycle must not exceed **15 seconds** (4 in + 5 hold + 6 out)
- `...` markers are ONLY for non-breathing pauses (scene-setting, reflection, transitions)
- Any pause where the listener is actively holding breath or controlling breathing MUST be explicit
- This applies to ALL breathing patterns (basic, box, 4-7-8)

---

## Ambient Sound Rules

### CRITICAL: User Direction Required

**NO ambient sound is applied automatically.**

Scott will direct ambient usage per track. Do not assume ambient is needed.

| Rule | Detail |
|------|--------|
| **Application** | Only when Scott directs |
| **Volume** | Subtle — gentle background, not prominent |
| **Fade in** | After intro, not from the start |
| **During silence** | Raise slightly so listener knows audio is playing |
| **Looping** | One continuous run preferred over obvious loops |

If in doubt, produce WITHOUT ambient. It can be added later; removing it requires rebuild.

---

## Ambient Sound Levels

**Standard mix level: -14 dB** (relative to narration)

This is the baseline for all ambient mixing. Provides presence without overpowering voice.

| Setting | Value | Notes |
|---------|-------|-------|
| **Ambient volume** | -14 dB | Main mix level during narration |
| **Ambient during pauses** | -13 dB | Raise by 1dB during 30s+ gaps |
| **Fade in** | 15 seconds | Logarithmic curve - starts quiet, builds naturally |
| **Fade out** | 8 seconds | Longer tail for smooth ending |

### Ambient Loop Requirements

**CRITICAL: Ambient files must loop seamlessly.**

- **No silence at start or end** - Even 0.5s gaps become obvious when looped
- **Ideal length**: 5-10 minutes (long enough to avoid obvious repetition)
- **Crossfade points**: Files should fade smoothly at boundaries
- **Test loops**: Before using, verify with `ffmpeg -stream_loop 3 -i file.mp3 -t 600 test.mp3`

To check for silence at boundaries:
```bash
ffmpeg -i ambient.mp3 -af "silencedetect=n=-30dB:d=0.3" -f null - 2>&1 | grep silence
```

**Known issues to avoid:**
- Downloaded files often have silence padding at start
- Trim with: `ffmpeg -ss 2 -i input.mp3 -c:a libmp3lame -q:a 2 output.mp3`

### FFmpeg command reference:
```bash
ffmpeg -y -i voice.mp3 \
  -stream_loop -1 -i ambient.mp3 \
  -filter_complex "[1:a]volume=-15dB,afade=t=in:st=0:d=15:curve=log,afade=t=out:st=${fade_out}:d=8[amb];[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2" \
  -t $duration -c:a libmp3lame -q:a 2 output.mp3
```

### If ambient feels too quiet/loud:
- Too quiet: Try -12 dB
- Too loud: Try -18 dB
- Standard: -15 dB (default)

---

## Ambient Sound Assignments

### Sleep Sessions
- **ocean** - Beach, shore, voyage themes
- **rain** - Cozy, indoor, journey themes
- **night** - Evening, stars, crickets themes

### Stress/Anxiety
- **stream** - Gentle, flowing relief
- **rain** - Grounding, present moment
- **wind** - Release, letting go
- **waterfall** - Powerful release

### Focus
- **library** - Quiet productivity
- **piano** - Creative work
- **birds** - Morning, clarity

### Mindfulness
- **temple** - Traditional practice
- **garden** - Nature awareness
- **forest** - Walking meditation
- **wind** - Open awareness
- **chimes** - Energy work

---

## TTS Voice Consistency

**Problem:** Segment-by-segment TTS generation can produce voice variations at boundaries.

**Best practices:**
- Generate larger text chunks where possible (fewer API calls = fewer boundaries)
- Use TTS providers with better consistency (Azure, ElevenLabs > Fish)
- Avoid very short segments (under 20 chars) which are more prone to variation
- If voice shifts noticeably, regenerate that specific segment

**Provider comparison:**
| Provider | Consistency | Best for |
|----------|-------------|----------|
| Azure Speech | Excellent | Long sessions needing consistency |
| ElevenLabs | Very good | Premium quality, natural sound |
| Fish TTS | Variable | Quick prototyping |

---

## Fish Audio TTS Build Settings

**Current voice:** Marco - "Calm male" by ANGEL NSEKUYE
**Voice ID:** `0165567b33324f518b02336ad232e31a`
**API:** `https://api.fish.audio/v1/tts`

### CRITICAL: TTS Non-Determinism

**Fish Audio TTS is non-deterministic.** The same text can produce:
- Different voice characteristics between segments
- Slight timing variations
- Occasional artifacts/glitches

**Implications:**
- Rebuilding often fixes issues (fresh TTS generation)
- Some builds will fail quality gate - this is normal
- Auto-rebuild loop is essential (expect 1-3 attempts)
- Perfect first-build is luck, not skill

### What Works

| Approach | Result |
|----------|--------|
| Fresh rebuild | Usually fixes voice changes and glitches |
| Auto-retry on TTS failure | Catches transient API errors |
| Build-time validation | Catches missing/corrupt segments early |
| Manifest generation | Enables timing comparison in analyzer |

### What Doesn't Work

| Approach | Problem |
|----------|---------|
| Splicing/repairing segments | Audible transitions, worse than rebuild |
| Audio processing to fix voice changes | Can't fix what's baked into TTS |
| Silence trimming filters | Cuts into speech, destroys audio |
| Speed adjustment (atempo) | Amplifies existing issues |
| ElevenLabs voice cloning | Captures resonance but not character |

**Lesson:** Fresh rebuild > any repair attempt

### API Settings

| Setting | Value | Notes |
|---------|-------|-------|
| **temperature** | 0.3 | Lower = more consistent. 0.4-0.5 = warmer/more expressive |
| **condition_on_previous_chunks** | true | Helps maintain voice consistency |
| **sample_rate** | 44100 | Standard quality |
| **format** | mp3 | |

### Build Architecture

**CRITICAL: Generate one TTS chunk per text block, preserving ALL pauses.**

DO NOT combine text blocks to reduce API calls - this destroys the meditation rhythm.
Each `...` marker in the script = one pause. Each text block between pauses = one TTS call.

```
Script structure:
  Text block 1 → TTS call 1 → [pause]
  Text block 2 → TTS call 2 → [pause]
  ...
```

### Audio Cleanup Pipeline

Applied to all TTS output before mixing:

```
highpass=f=80              # Cut low rumble
equalizer=f=6000:t=q:w=2:g=-4   # De-esser: notch at 6kHz for sibilance
highshelf=f=7000:g=-2      # De-esser: gentle shelf above 7kHz
lowpass=f=10000            # Cut high-freq hiss (aggressive)
afftdn=nf=-25              # Noise reduction (stronger setting)
dynaudnorm=p=0.9:m=10      # Normalize levels
```

**De-esser notes:** The two de-esser stages reduce harsh 's' sounds:
- Notch at 6kHz (-4dB) targets the main sibilance frequency
- High shelf above 7kHz (-2dB) softens harsh consonants
- Together they prevent the "hissing 's'" artifact common in TTS

### Known Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| **Continuous monotone voice** | Text blocks combined, pauses lost | Generate each block separately, don't combine |
| **Opening too fast** | First text block too long | Break opening into shorter sentences with `...` pauses between |
| **High-frequency hiss/glitch** | TTS artifact in specific chunk | Aggressive lowpass filter (10kHz), stronger noise reduction |
| **Audio degradation mid-session** | Bad TTS chunk from API | Regenerate session; random API issues |
| **Voice inconsistency** | Too many short chunks | Maintain reasonable chunk sizes (50-400 chars ideal) |
| **Glitch near end (~30s out)** | Random TTS artifact | Regenerate; if persists, deploy at 95%+ quality |

### Script Writing Rules for TTS

1. **Break up long openings** - First 3-4 sentences should each be separate blocks with pauses
2. **Avoid single-word blocks** - Chunks under 20 chars are unreliable
3. **Use `...` liberally** - Each creates a natural breath/pause for meditation pacing
4. **Double `...` = 30 sec pause** (sleep category)
5. **Triple `...` = 60 sec pause** (sleep category)

### Recommended Ambient Levels

After testing (Feb 2026):
- **-12dB**: Louder ambient, good for rain/ocean where sound is the feature ✓ VERIFIED
- **-14dB**: Standard, balanced mix
- **-16dB**: Quieter ambient, voice-focused

---

## Production Notes: Rainfall-2 (Feb 2026)

**Baseline reference session** - use these settings for similar sleep/rain sessions.

### What Worked
- **45 text blocks** for 17.7 min session (preserve all pauses)
- **-12dB ambient** for rain - immersive without overpowering voice
- **Temperature 0.3** - consistent voice throughout
- **Spaced opening** - first paragraph broken into 4 short sentences:
  ```
  Tonight, it's raining.
  ...
  And I know that might not sound like much, but stay with me.
  ...
  Because rain, the right kind of rain, on the right kind of night...
  ...
  There's a reason people put on rain sounds to fall asleep...
  ...
  ```

### Persistent Issues (RESOLVED)
- **End glitch (~30s from end)**: High-frequency hiss/spike appeared randomly
  - Fix: **Regenerate the full session** - fresh TTS generation resolved the issue
  - The glitch was a random TTS artifact, not a systematic problem
  - Lesson: If glitch persists after one rebuild, try again - TTS output varies

### Final Settings Used
```python
AMBIENT_VOLUME_DB = -12
temperature = 0.3
lowpass = 10000Hz
afftdn = -25dB
```

---

## Opening & Closing

**Opening:**
- Do NOT say "Welcome to Salus" at the start of every session
- Start with a soft, contextual intro that sets the scene (e.g. "This is a gentle breathing session for when anxiety feels heavy.")
- **No extended silence until the scene is set.** The first 3-4 sentences must flow with only short pauses (single `...`). Extended pauses (double/triple `...`) only after the listener knows what they're in and is settled.
- Exception: Landing page / intro content can mention Salus

**Opening structure (mandatory):**
```
[Contextual intro — what this session is]     <- single ...
[Second scene-setting sentence]               <- single ...
[Third — instruction or reassurance]          <- single ...
[Physical instruction — sit, close eyes etc]  <- NOW double/triple ... OK
```

**Closing (MANDATORY):**
- Every session MUST end with: "Thank you for practicing with Salus. Sleep, relax, restore."
- This is the ONLY acceptable closing. No variations. No exceptions.
- Sleep sessions: Add "Goodnight" after the closing phrase
- Other sessions: Fade out after the closing phrase

---

## Quality Check: Pause Positions

**Glitches tend to occur at splice points (start/end of pauses).** When checking a session, focus on these timestamps.

To generate pause timestamps for any session, run:
```bash
python3 -c "
import re
from pathlib import Path

script = Path('content/scripts/SESSION_NAME.txt').read_text()
content = script.split('---', 1)[1] if '---' in script else script

time = 0
for line in content.split('\n'):
    line = line.strip()
    if line == '...':
        print(f'{int(time//60)}:{int(time%60):02d} - pause')
        time += 10  # approximate
    elif re.match(r'\[PAUSE.*seconds\]', line, re.I):
        secs = int(re.search(r'(\d+)', line).group(1))
        print(f'{int(time//60)}:{int(time%60):02d} - {secs}s SILENCE')
        time += secs
    elif line:
        time += len(line) * 0.06  # rough estimate
"
```

### Known pause positions (key sessions):

**Rainfall Sleep Journey (17.7 min)** ✓ DEPLOYED
- Multiple 8s pauses throughout
- 30s pauses at key transitions (double `...`)
- 60s silence at ~12:00 (announced: "I'm going to be quiet now...")
- Known glitch point: ~30s before end

**Ocean Voyage (35 min)**
- ~18:00 - 60 second silence (announced)
- ~28:00 - 90 second silence (announced)

---

## Session Duration Guidelines

**Soft limit: 30 minutes** for standard sessions to maintain TTS voice consistency.

| Session Type | Target Duration | Notes |
|--------------|-----------------|-------|
| Focus/Stress | 5-15 min | Short, targeted |
| Mindfulness | 10-20 min | Standard practice |
| Beginner | 5-15 min | Accessible length |
| Sleep/Stories | Up to 45 min | Can exceed limit, accept some variation |
| Advanced | 20-30 min | Longer practice |

Longer sessions = more TTS API calls = higher chance of voice variation at segment boundaries.

---

## Audio Quality Gate (MANDATORY)

**Rule: 100% OR NO SHIP.**

ANY audible glitch = FAIL. No exceptions. No "acceptable" threshold.
One glitch destroys the meditation experience. Ship perfection or rebuild.

### Quality Threshold

| Metric | Pass | Fail |
|--------|------|------|
| Audible glitches | 0 | ANY |
| Audible hissing/artifacts | 0 | ANY |
| Voice breaks/distortion | 0 | ANY |

**Automated analysis is PRE-SCREENING only.**
Human review with `test-audio-player.html` is MANDATORY.
Human ear is the final gate.

### Analyzer v5 (Current - Feb 2026)

**Location:** `/Users/scottripley/salus-website/analyze_audio_v5.py`

| Detection | Severity | What it detects |
|-----------|----------|-----------------|
| VOICE_CHANGE | CRITICAL | TTS voice tone/timbre changes (MFCC-based) |
| UNEXPECTED_SILENCE | CRITICAL | Silences 1.8-2.8s (between speech pauses and intentional gaps) |
| TEMPO_SPEEDUP | LOW | [EXPERIMENTAL] Speech >40% faster than baseline - BPM-based, needs tuning |
| TEMPO_SLOWDOWN | LOW | [EXPERIMENTAL] Speech >45% slower than baseline - BPM-based, needs tuning |
| SEGMENT_TOO_SHORT | HIGH | TTS segment <50% of expected duration |
| SEGMENT_TOO_LONG | MEDIUM | TTS segment >180% of expected duration |
| SIBILANCE | LOW | Harsh 's' sounds — almost always false positives with Marco voice. Ignore unless human hears it. |
| HISSING | LOW | High-frequency noise — almost always false positives. Downgraded 6 Feb after 03 review (15 flags, 0 audible). Ignore unless human hears it. |

**Key improvement:** v5 loads the build manifest (if available) to compare expected vs actual segment timings.

```bash
# Run analyzer
python3 analyze_audio_v5.py <audio-file.mp3>

# Outputs:
# - <filename>_REPORT_v4.txt - Detailed issue list
# - Console summary with timestamps
```

**Pass criteria:**
- VOICE_CHANGE = 0 (mandatory)
- UNEXPECTED_SILENCE = 0 (mandatory)
- Everything else = informational only, ignore unless human ear catches it
- SIBILANCE and HISSING are almost always false positives with Marco — downgraded to LOW (6 Feb 2026)

**Tempo detection notes (EXPERIMENTAL):**
- Uses librosa BPM estimation with 10-second sliding windows
- BPM-based detection is designed for music, not speech - results are approximate
- Thresholds set high (40%/45%) to minimize false positives
- Marked as LOW severity - informational only, human ear is the final judge
- Future improvement: consider speech rate analysis (phonemes/second) instead of BPM

### Build Script v2 (Current - Feb 2026)

**Location:** `/Users/scottripley/salus-website/build-morning-fish.py`

**Improvements over v1:**
1. **Auto-retry** - Failed TTS segments retry up to 3 times
2. **Duration validation** - Each segment shows expected vs actual duration
3. **Manifest generation** - Saves `_manifest.json` with all segment timings
4. **Better logging** - Shows validation status per segment

```bash
# Run build
python3 build-morning-fish.py

# Outputs:
# - content/audio-free/01-morning-meditation.mp3
# - content/audio-free/01-morning-meditation_manifest.json
```

**Manifest format:**
```json
{
  "generated": "2026-02-05 14:30:00",
  "total_tts_duration": 196.5,
  "total_expected_duration": 172.6,
  "segments": [
    {"index": 0, "type": "text", "text": "...", "duration": 1.7, "expected_duration": 1.2, ...},
    {"index": 1, "type": "silence", "duration": 3, ...}
  ]
}
```

### Human Review Tool

**Location:** `/Users/scottripley/salus-website/test-audio-player.html`

Open in browser for timestamp-based review. Seek to flagged timestamps and verify by ear.

### Workflow (Updated Feb 2026)

```
1. BUILD: Run build script (e.g., build-morning-fish.py)
   - Script validates each TTS segment (>0.5s, >1KB)
   - Auto-retries failed segments up to 3 times
   - Generates timing manifest for debugging

2. ANALYZE: Run analyze_audio_v5.py
   - Loads manifest for timing comparison
   - Checks for voice changes (MFCC-based)
   - Checks for unexpected silences

3. GATE CHECK:
   - VOICE_CHANGE = 0? (mandatory)
   - UNEXPECTED_SILENCE = 0? (mandatory)
   → PASS = Proceed to human review
   → FAIL = Auto-rebuild

4. AUTO-REBUILD LOOP:
   for attempt in 1..N:
     BUILD → ANALYZE → GATE CHECK
     if PASS: break

   Default: N=3 (3-Strike Rule)
   Override: Can extend if user directs

5. HUMAN REVIEW:
   - Open test-audio-player.html
   - Listen to FULL audio (no shortcuts)
   - Check flagged timestamps
   - Verdict: PASS or specific failure (timestamp + description)

6. DEPLOY or REBUILD based on human verdict
```

### Auto-Rebuild Loop (Script Pattern)

```bash
for attempt in 1 2 3; do
  python3 build-morning-fish.py 2>&1 | grep "Duration:"
  VOICE=$(python3 analyze_audio_v5.py file.mp3 2>/dev/null | grep "Found.*voice change" | grep -oE "[0-9]+" | head -1)
  echo "Attempt $attempt: voice=$VOICE"
  if [ "$VOICE" = "0" ]; then
    echo "*** PASS ***"
    break
  fi
done
```

### 3-Strike Rule

**After 3 failed rebuild attempts, STOP automated retries.**

Escalate to human review because repeated failures indicate:
- Script issue (sentence structure, problematic words)
- Voice model issue (certain phrases trigger artifacts)
- Systematic problem that rebuilding won't fix

Human must investigate root cause before further attempts.

### 3-Strike Override

**When user explicitly directs, the 3-Strike limit can be overridden.**

Valid reasons to override:
- TTS is known to be "having a bad day" (API issues)
- Previous builds were close to passing
- User has time and wants to keep trying

Override by extending the loop limit:
```bash
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  # ... build and check ...
done
```

**Do NOT override if:**
- Same specific issue persists across all attempts (systematic)
- Script has problematic phrases that trigger issues
- Analyzer is producing false positives (fix analyzer first)

### Why This Matters

- TTS output is non-deterministic - same text can produce different artifacts
- Glitches are random API artifacts, not systematic bugs
- Rebuilding typically resolves issues within 1-3 attempts
- Opening quality is critical - users judge in first 30 seconds
- This system applies to ALL audio production, not just one file

### Analysis Tool

Location: `/Users/scottripley/Library/CloudStorage/OneDrive-Personal/Salus/Audio Quality Analysis/analyze_audio.py`

```bash
python3 analyze_audio.py <audio-file.mp3>
```

Outputs:
- `<filename>_REPORT.txt` - Detailed issue list with timestamps
- `<filename>_ANALYSIS.png` - Visual waveform/spectrogram

---

## Liability Checker (MANDATORY)

**Rule: All scripts MUST pass liability review BEFORE audio production.**

Salus provides relaxation and mindfulness content, not medical treatment. Scripts must never contain language that could alarm listeners, imply medical outcomes, or create liability for Salus.

### Banned Language Categories

| Category | Why Banned | Example of Violation |
|----------|------------|----------------------|
| **Brain structure claims** | Alarming even if true | "Part of your brain will shrink" |
| **Medical diagnoses** | We're not doctors | "This will cure your anxiety" |
| **Treatment promises** | Creates expectation | "After 21 days you'll be free of depression" |
| **Specific health outcomes** | Unmeasurable claims | "Your cortisol levels will drop" |
| **Alarming science** | Scares listeners | "Stress is literally killing your cells" |
| **Comparative medicine** | Implies medical parity | "Better than medication" |
| **Urgency/fear language** | Creates anxiety | "If you don't do this, your stress will..." |
| **Absolute claims** | Unprovable | "This will always work" / "Guaranteed results" |

### Specific Banned Phrases

These exact phrases or similar constructions must NEVER appear:

```
❌ "shrink" + "brain" (in any combination)
❌ "cure" / "treat" / "heal" (medical context)
❌ "scientifically proven to..."
❌ "studies show this will..."
❌ "your [organ] will..."
❌ "reverse the damage"
❌ "repair your..."
❌ "fix your..."
❌ "clinical" / "therapeutic" / "treatment"
❌ "prescription" / "dose" / "therapy"
❌ "diagnosis" / "symptoms" / "condition"
❌ "guaranteed" / "certain" / "definitely will"
```

### Approved Alternatives

| Instead of... | Write... |
|---------------|----------|
| "This will cure anxiety" | "This may help you feel calmer" |
| "Reduces cortisol" | "Many find this relaxing" |
| "Proven to help depression" | "A moment of peace for difficult days" |
| "Heals your mind" | "A gentle practice for your wellbeing" |
| "Scientifically backed" | "Inspired by mindfulness traditions" |
| "Part of your brain shrinks" | (Remove entirely - no alternative) |
| "Reverses stress damage" | "Gives your mind a rest" |
| "Clinical meditation" | "Guided relaxation" |

### Approved Framing

**DO use:**
- "May help you feel..."
- "Many people find..."
- "A practice for..."
- "Inspired by..."
- "Take a moment to..."
- "Give yourself permission to..."
- "Some find this helpful for..."

**DO NOT use:**
- "Will make you..."
- "Proven to..."
- "Scientifically..."
- "Clinically..."
- "Treats..."
- "Cures..."

### Educational Content Rules

When discussing science/research in educational tracks:

1. **Never state outcomes as certain** — Use "research suggests" not "science proves"
2. **Avoid alarming facts** — Even true facts can scare (e.g., brain shrinkage)
3. **Focus on positive framing** — What mindfulness offers, not what stress destroys
4. **No medical comparisons** — Never compare to medication or therapy effectiveness
5. **Source vaguely** — "Many practitioners find" not "Oxford study showed 47%..."

### Liability Review Process

**Before generating ANY audio:**

1. Run script through liability check (manual or automated)
2. Flag any banned phrases or categories
3. Rewrite flagged sections using approved alternatives
4. Verify no medical claims, outcome promises, or alarming language
5. Sign off on script before TTS generation

### Quick Scan Patterns

Use these grep patterns to scan scripts for potential issues:

```bash
# Medical/treatment language
grep -in "cure\|treat\|heal\|therapy\|clinical\|prescription\|diagnosis\|symptom" script.txt

# Brain/body claims
grep -in "brain\|cortisol\|hormone\|cell\|neural\|nervous system" script.txt

# Outcome promises
grep -in "will make\|will help\|proven\|guaranteed\|definitely\|always\|scientific" script.txt

# Alarming language
grep -in "damage\|destroy\|kill\|shrink\|deteriorat\|harm" script.txt
```

### Liability Checker Script

Run before audio production:

```bash
#!/bin/bash
# liability-check.sh - Scan script for problematic language

SCRIPT="$1"
if [ -z "$SCRIPT" ]; then
    echo "Usage: liability-check.sh <script.txt>"
    exit 1
fi

echo "=== LIABILITY CHECK: $SCRIPT ==="
echo ""

ISSUES=0

# Medical language
echo "--- Medical/Treatment Terms ---"
FOUND=$(grep -in "cure\|treat\|heal\|therap\|clinical\|prescription\|diagnosis\|symptom\|medication\|dose" "$SCRIPT" | head -20)
if [ -n "$FOUND" ]; then
    echo "$FOUND"
    ISSUES=$((ISSUES + $(echo "$FOUND" | wc -l)))
else
    echo "None found ✓"
fi

echo ""
echo "--- Brain/Body Claims ---"
FOUND=$(grep -in "brain\|cortisol\|hormone\|neural\|nervous system\|amygdala\|prefrontal" "$SCRIPT" | head -20)
if [ -n "$FOUND" ]; then
    echo "$FOUND"
    ISSUES=$((ISSUES + $(echo "$FOUND" | wc -l)))
else
    echo "None found ✓"
fi

echo ""
echo "--- Outcome Promises ---"
FOUND=$(grep -in "will make\|will help you\|proven\|guaranteed\|definitely\|always work\|scientific" "$SCRIPT" | head -20)
if [ -n "$FOUND" ]; then
    echo "$FOUND"
    ISSUES=$((ISSUES + $(echo "$FOUND" | wc -l)))
else
    echo "None found ✓"
fi

echo ""
echo "--- Alarming Language ---"
FOUND=$(grep -in "damage\|destroy\|kill\|shrink\|deteriorat\|harm\|toxic\|poison" "$SCRIPT" | head -20)
if [ -n "$FOUND" ]; then
    echo "$FOUND"
    ISSUES=$((ISSUES + $(echo "$FOUND" | wc -l)))
else
    echo "None found ✓"
fi

echo ""
echo "================================"
if [ "$ISSUES" -gt 0 ]; then
    echo "⚠ REVIEW NEEDED: $ISSUES potential issues found"
    echo "Review each flagged line and rewrite if necessary."
    exit 1
else
    echo "✓ PASSED: No liability issues detected"
    exit 0
fi
```

Save as `/Users/scottripley/salus-website/content/scripts/liability-check.sh`

### The Golden Rule

**When in doubt, remove it.**

If a sentence makes you pause and wonder "could someone take this the wrong way?" — delete it. The meditation will work without it. No scientific fact is worth a lawsuit.

---

## Session Checklist

Before publishing any session:

- [ ] Duration category identified (under 10 / 10-20 / 20+)
- [ ] Required silences added per spec above
- [ ] Narrator announces 60+ second silences
- [ ] Ambient sound assigned and mixed
- [ ] Ambient continues through ALL pauses/silences
- [ ] No dead silence anywhere in track
- [ ] No "Welcome to Salus" at start (unless intro content)
- [ ] **Opening broken into short blocks** (not one long continuous paragraph)
- [ ] **Listen to full audio** - check for hiss/glitches especially near start and end
- [ ] **Pauses feel natural** - rhythm matches meditation pacing

---

## Build Command Reference

```bash
# Build a session
python3 build-session-v3.py <session-name>

# Dry run (shows plan without generating)
python3 build-session-v3.py --dry-run <session-name>

# Build multiple variations for testing
python3 build-variations.py
```

Output goes to: `content/audio/<session-name>.mp3`

---

---

## Scanner Baseline (Approved Audio Reference)

**01-morning-meditation.mp3** - Approved 5 Feb 2026

Scanner results for human-approved audio (benchmark for expected false positives):

| Detection | Count | Notes |
|-----------|-------|-------|
| VOICE_CHANGE | 0 | Must be 0 to pass |
| UNEXPECTED_SILENCE | 0 | Must be 0 to pass |
| TEMPO_SPEEDUP | 14 | LOW severity, experimental - ignore |
| SIBILANCE | 30 | Mostly first 40s - normal TTS 's' sounds |
| HISSING | 12 | Scattered - acceptable levels |
| CLICK_GLITCH | 8 | First 21s - speech transients, not artifacts |
| SEGMENT_TOO_LONG | 2 | MEDIUM - acceptable |

**Key insight:** Sibilance, hissing, and click detections are often false positives. The mandatory gates are VOICE_CHANGE=0 and UNEXPECTED_SILENCE=0. Everything else is informational for human review.

---

## Audio Reset — 6 February 2026

**All previous audio has been archived.** Only one approved session remains.

### Approved Audio (Production)
| # | Session | File | Status |
|---|---------|------|--------|
| 01 | Morning Meditation | `content/audio-free/01-morning-meditation.mp3` | APPROVED — BENCHMARK |
| 03 | Breathing for Anxiety | `content/audio-free/03-breathing-for-anxiety.mp3` | APPROVED (6 Feb 2026) |

01 is the quality benchmark. Every new session must match or exceed this standard.

### Archive Location
All previous audio moved to `content/audio-archive/` (2.2GB). Organised by original folder:
- `audio-archive/audio-free/` — previous deployed files
- `audio-archive/audio/` — previous working copies
- `audio-archive/audio-backup/` — previous backups
- `audio-archive/audio-extended/` — previous extended versions

Archive is reference only. Nothing in archive is approved for deployment.

### Rebuild Queue (Starting Fresh)
All sessions except 01 need to be built from scratch to benchmark quality.

**Next up:** Session 02 — Deep Sleep

### What Remains Active
- `content/audio-free/01-morning-meditation.mp3` — approved production audio
- `content/audio-free/01-morning-meditation_manifest.json` — build manifest
- `content/audio-free/01-morning-meditation_REPORT_v4.txt` — analyzer report
- `content/audio/ambient/` — ambient loops for mixing
- `content/sounds/` — ASMR library (unchanged)

---

## Claude Session Management

**NO MEMORY FILES.** All project knowledge lives in this bible.

Future Claude sessions should:
1. Read this bible at session start
2. Update this bible with learnings at session end
3. Never create separate memory files

**Key file locations:**
| File | Path |
|------|------|
| Build script (v2) | `/Users/scottripley/salus-website/build-morning-fish.py` |
| Analyzer (v5) | `/Users/scottripley/salus-website/analyze_audio_v5.py` |
| Human review player | `/Users/scottripley/salus-website/test-audio-player.html` |
| This bible | `/Users/scottripley/salus-website/content/AUDIO-SPEC.md` |

---

*Last updated: 6 February 2026 - Audio reset: all previous audio archived, 01-morning-meditation is sole approved benchmark, rebuilding from scratch*
