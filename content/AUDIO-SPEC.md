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

#### 5-minute production
| Silence | Quantity | Placement |
|---------|----------|-----------|
| 5s | 8-12x | Throughout, between sentences |
| 10s | 3-4x | Section transitions |
| 15s | 1-2x | Key moments |

#### 10-minute production
| Silence | Quantity | Placement |
|---------|----------|-----------|
| 5s | 15-20x | Throughout |
| 10s | 5-6x | Section transitions |
| 15s | 3-4x | Key moments |
| 30s | 1x | Around 60% mark |

#### 15-minute production
| Silence | Quantity | Placement |
|---------|----------|-----------|
| 5s | 20-30x | Throughout |
| 10s | 6-8x | Section transitions |
| 15s | 4-5x | Key moments |
| 30s | 2x | At 40% and 70% |
| 45s | 1x | Around 50% |
| 60s | 1x | Around 75% — announce |

#### 20-minute production
| Silence | Quantity | Placement |
|---------|----------|-----------|
| 5s | 25-35x | Throughout |
| 10s | 8-10x | Section transitions |
| 15s | 5-6x | Key moments |
| 30s | 2-3x | Distributed |
| 45s | 1-2x | Mid-session |
| 60s | 1x | Around 60% — announce |
| 75s | 1x | Around 80% — announce |

#### 30-minute production
| Silence | Quantity | Placement |
|---------|----------|-----------|
| 5s | 35-50x | Throughout |
| 10s | 10-12x | Section transitions |
| 15s | 6-8x | Key moments |
| 30s | 3-4x | Distributed |
| 45s | 2x | At 35% and 55% |
| 60s | 1-2x | At 45% and 70% — announce |
| 75s | 1x | Around 80% — announce |
| 90s | 1x | Around 85% — announce |

#### 45-minute+ production (Sleep/Stories)
| Silence | Quantity | Placement |
|---------|----------|-----------|
| 5s | 50-70x | Throughout |
| 10s | 12-15x | Section transitions |
| 15s | 8-10x | Key moments |
| 30s | 4-5x | Distributed |
| 45s | 2-3x | Distributed |
| 60s | 2x | At 40% and 65% — announce |
| 75s | 1-2x | At 75% and 85% — announce |
| 90s | 1x | Around 90% — announce |

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

**Current voice:** Marco (ID: `0165567b33324f518b02336ad232e31a`)

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
- Jump straight into the content or a gentle opening like "Get comfortable..." or "Close your eyes..."
- Exception: Landing page / intro content can mention Salus

**Closing:**
- End with "Goodnight from Salus" (sleep sessions) or just fade out naturally
- No need for lengthy sign-offs

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

### Analyzer v2 Detection Types

| Type | Severity | What it detects |
|------|----------|-----------------|
| VOICE_SHIFT | HIGH | TTS voice tone/timbre changes between blocks |
| HISSING | MEDIUM | Sustained high-frequency noise regions |
| LONG_SILENCE | LOW | Pauses over 45 seconds (informational) |

**Note:** Click/glitch detection removed in v2 - too many false positives at splice points.
The cleanup filter handles splice artifacts; real issues are sustained voice changes.

### Targeted Repair

Instead of full rebuild, use `targeted_repair.py` to fix individual blocks:
```bash
python3 targeted_repair.py <block_number> <input.mp3> <output.mp3>
```

### Workflow

```
1. BUILD: Generate audio with TTS + ambient mixing
2. ANALYZE: Run analyze_audio.py on raw master (no ambient)
3. REVIEW: Check report for HIGH/MEDIUM issues
4. GATE CHECK:
   - HIGH issues = 0?
   - MEDIUM issues ≤ 5?
   - No glitches in opening 30 seconds?
   → YES to all = PASS → Deploy
   → NO to any = FAIL → Rebuild
5. REBUILD: Regenerate full session (fresh TTS run)
6. REPEAT: Steps 2-5 until PASS
```

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

*Last updated: 5 February 2026*
