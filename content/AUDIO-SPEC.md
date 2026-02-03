# Salus Audio Session Specifications

Guidelines for structuring meditation and sleep audio sessions.

---

## Silence Requirements by Duration

**ALL sessions have existing short pauses (5s, 10s, 15s, etc.) - these remain unchanged.**

The following MUST be added based on duration:

### Short Sessions (Under 10 minutes)
- **Add ONE 30-second pause** (ambient continues so listener knows it hasn't stopped)
- No narrator announcement needed

### Medium Sessions (10-20 minutes)
- **Add ONE 30-second pause**
- **Add ONE 60-second silence** with narrator announcement
- Narrator announces: *"I'm going to be quiet for a little while now..."*

### Long Sessions (20+ minutes)
- **Add ONE 30-second pause**
- **Add ONE 60-second silence** with narrator announcement (around 40-50% mark)
- **Add ONE 90-second silence** with narrator announcement (around 70-80% mark)

**Ambient continues through ALL pauses and silences.**

---

## Silence Announcement Phrases

Before a long silence (60+ seconds), narrator MUST announce it:

- "I'm going to be quiet now for a little while. Just let the [rain/waves/sounds] hold you..."
- "I'll be silent for a moment. There's nothing you need to do..."
- "Take this time in stillness. I'll return in a moment..."
- "Rest here now. I'll be back soon..."

**IMPORTANT:** Never have extended silence without ambient sound - listener must know audio is still playing.

---

## Ambient Sound Levels

**Standard mix level: -15 dB** (relative to narration)

This is the baseline for all ambient mixing. Provides presence without overpowering voice.

| Setting | Value | Notes |
|---------|-------|-------|
| **Ambient volume** | -15 dB | Main mix level for all sessions |
| **Fade in** | 5 seconds | Gentle start |
| **Fade out** | 8 seconds | Longer tail for smooth ending |

### FFmpeg command reference:
```bash
ffmpeg -y -i voice.mp3 \
  -stream_loop -1 -i ambient.mp3 \
  -filter_complex "[1:a]volume=-15dB,afade=t=in:st=0:d=5,afade=t=out:st=${fade_out}:d=8[amb];[0:a][amb]amix=inputs=2:duration=first:dropout_transition=2" \
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

**Rainfall Sleep Journey (34 min)**
- 22:00 - 90 second silence (announced)

**Ocean Voyage (35 min)**
- ~18:00 - 60 second silence (announced)
- ~28:00 - 90 second silence (announced)

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

---

*Last updated: February 2026*
