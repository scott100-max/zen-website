#!/usr/bin/env python3
"""Generate individual session detail pages for all premium sessions."""
import os

BASE = "/Users/scottripley/salus-website"
OUT_DIR = os.path.join(BASE, "sessions")
os.makedirs(OUT_DIR, exist_ok=True)

sessions = [
    {
        "slug": "deep-sleep",
        "title": "Deep Sleep Meditation",
        "duration": "25 min",
        "category": "Sleep",
        "gradient": "linear-gradient(160deg,#0d1b2a 0%,#1b2838 50%,#2a4365 100%)",
        "emoji": "&#127769;",
        "desc": "A deeply calming meditation designed to guide you from wakefulness to restful sleep. Using progressive relaxation, gentle visualisation, and slow breathing cues, this session helps quiet the racing mind and prepare your body for a full night's rest.",
        "learn": ["Progressive muscle relaxation techniques", "Visualisation for sleep onset", "How to quiet racing thoughts at bedtime", "Building a pre-sleep wind-down routine"],
        "best_for": "Insomnia, difficulty switching off, restless nights",
        "narrator": "Lily",
    },
    {
        "slug": "moonlight-body-scan",
        "title": "Moonlight Body Scan",
        "duration": "30 min",
        "category": "Sleep",
        "gradient": "linear-gradient(160deg,#0a0e27 0%,#1a1a40 40%,#3d3580 100%)",
        "emoji": "&#127765;",
        "desc": "Journey through your entire body under the soft glow of imagined moonlight. Each body part is gently acknowledged, relaxed, and released — creating a wave of calm that carries you toward sleep.",
        "learn": ["Full-body awareness scanning", "Systematic tension release", "Breath-synchronised relaxation", "Transitioning from awareness to sleep"],
        "best_for": "Physical tension, body-held stress, difficulty falling asleep",
        "narrator": "Lily",
    },
    {
        "slug": "sleep-stories-forest",
        "title": "Sleep Story: The Quiet Forest",
        "duration": "40 min",
        "category": "Sleep",
        "gradient": "linear-gradient(160deg,#1b4332 0%,#2d6a4f 50%,#40916c 100%)",
        "emoji": "&#127794;",
        "desc": "A slow, meandering narrative that takes you on a walk through an ancient forest at dusk. The story is deliberately gentle and uneventful — designed to bore your overactive mind into peaceful sleep.",
        "learn": ["Using narrative to distract from anxious thoughts", "Engaging the imagination for sleep", "Slow-paced listening as a wind-down tool"],
        "best_for": "Overthinking at bedtime, anxiety-related insomnia",
        "narrator": "Lily",
    },
    {
        "slug": "sleep-stories-ocean",
        "title": "Sleep Story: Ocean Voyage",
        "duration": "35 min",
        "category": "Sleep",
        "gradient": "linear-gradient(160deg,#03045e 0%,#0077b6 40%,#90e0ef 100%)",
        "emoji": "&#9973;",
        "desc": "Drift across a calm ocean on a warm evening as the gentle rhythm of waves rocks you to sleep. A soothing narrative with ambient ocean sounds woven throughout.",
        "learn": ["Rhythmic breathing synchronised to waves", "Visualisation techniques for deep relaxation", "Using ambient sound for sleep onset"],
        "best_for": "Restlessness, needing a mental escape, light sleepers",
        "narrator": "Lily",
    },
    {
        "slug": "rainfall-sleep-journey",
        "title": "Rainfall Sleep Journey",
        "duration": "35 min",
        "category": "Sleep",
        "gradient": "linear-gradient(160deg,#03045e 0%,#023e8a 40%,#0077b6 100%)",
        "emoji": "&#127752;",
        "desc": "Drift off to the sound of gentle rain with a soothing narrative guiding you to rest. The rainfall gradually takes over as the narration fades, leaving you in a cocoon of natural white noise.",
        "learn": ["Rain-synchronised breathing", "Using natural sounds as a sleep anchor", "Letting go of the day's events"],
        "best_for": "Difficulty falling asleep, noise-sensitive sleepers, travel",
        "narrator": "Lily",
    },
    {
        "slug": "counting-down-to-sleep",
        "title": "Counting Down to Sleep",
        "duration": "20 min",
        "category": "Sleep",
        "gradient": "linear-gradient(160deg,#1b263b 0%,#415a77 40%,#778da9 100%)",
        "emoji": "&#128716;",
        "desc": "A gentle countdown technique that quiets the mind and eases you into deep sleep. Starting from 300 and breathing with each number, your attention narrows until sleep arrives naturally.",
        "learn": ["Countdown meditation technique", "Breath counting for sleep", "Mental focus narrowing", "When to use counting vs. body scan"],
        "best_for": "Racing mind, first-time meditators, jet lag",
        "narrator": "Lily",
    },
    {
        "slug": "lucid-dream-preparation",
        "title": "Lucid Dream Preparation",
        "duration": "30 min",
        "category": "Sleep",
        "gradient": "linear-gradient(160deg,#240046 0%,#5a189a 40%,#9d4edd 100%)",
        "emoji": "&#127769;",
        "desc": "Techniques to maintain awareness as you fall asleep, opening the door to lucid dreaming. Combines MILD and WILD techniques with guided relaxation to help you recognise when you're dreaming.",
        "learn": ["MILD technique (Mnemonic Induction of Lucid Dreams)", "Reality testing habits", "Maintaining awareness during sleep onset", "Dream journalling practices"],
        "best_for": "Experienced meditators, dream exploration, creative problem solving",
        "narrator": "Lily",
    },
    {
        "slug": "gratitude-before-sleep",
        "title": "Gratitude Before Sleep",
        "duration": "15 min",
        "category": "Sleep",
        "gradient": "linear-gradient(160deg,#10002b 0%,#3c096c 30%,#7b2cbf 60%,#c77dff 100%)",
        "emoji": "&#128156;",
        "desc": "End your day by reflecting on what you're grateful for, easing into peaceful rest. Research shows gratitude practices before bed improve both sleep quality and duration.",
        "learn": ["Structured gratitude reflection", "Replacing negative thought loops with appreciation", "The science of gratitude and sleep quality", "Building a nightly gratitude habit"],
        "best_for": "Negative thought spirals at bedtime, building positive habits",
        "narrator": "Lily",
    },
    {
        "slug": "morning-energy",
        "title": "Morning Energy Boost",
        "duration": "10 min",
        "category": "Focus",
        "gradient": "linear-gradient(160deg,#ff6b35 0%,#f7c59f 50%,#efefd0 100%)",
        "emoji": "&#9889;",
        "desc": "Replace your morning scroll with 10 minutes of energising breathwork and intention-setting. This session uses stimulating breath patterns to wake up your body and a short visualisation to set your focus for the day ahead.",
        "learn": ["Energising breath techniques (Kapalabhati)", "Morning intention-setting", "Replacing screen habits with mindful ones", "Creating energy without caffeine"],
        "best_for": "Groggy mornings, low motivation, building a morning routine",
        "narrator": "Lily",
    },
    {
        "slug": "laser-focus",
        "title": "Laser Focus",
        "duration": "15 min",
        "category": "Focus",
        "gradient": "linear-gradient(160deg,#1d3557 0%,#457b9d 50%,#a8dadc 100%)",
        "emoji": "&#127919;",
        "desc": "Sharpen your concentration with a practice designed for knowledge workers. Using a single-point focus technique, this session trains your attention to stay on task and gently return when it wanders.",
        "learn": ["Single-point concentration (Samatha)", "Recognising and managing distractions", "The attention muscle — how focus improves with practice", "Transitioning from meditation to deep work"],
        "best_for": "Before study sessions, creative work, or deep focus tasks",
        "narrator": "Lily",
    },
    {
        "slug": "creative-flow",
        "title": "Creative Flow State",
        "duration": "12 min",
        "category": "Focus",
        "gradient": "linear-gradient(160deg,#7209b7 0%,#b5179e 50%,#f72585 100%)",
        "emoji": "&#127912;",
        "desc": "Open the channels of creativity with a meditation that combines open awareness with gentle visualisation. Ideal before writing, designing, brainstorming, or any creative endeavour.",
        "learn": ["Open monitoring meditation for creativity", "Releasing perfectionism and self-judgement", "Accessing flow state through relaxed attention", "The neuroscience of creativity and meditation"],
        "best_for": "Creative blocks, brainstorming, artistic work, writing",
        "narrator": "Lily",
    },
    {
        "slug": "exam-preparation",
        "title": "Exam &amp; Interview Prep",
        "duration": "8 min",
        "category": "Focus",
        "gradient": "linear-gradient(160deg,#0b3d0b 0%,#2d6a4f 40%,#95d5b2 100%)",
        "emoji": "&#128218;",
        "desc": "A pre-performance meditation to calm nerves, sharpen recall, and boost confidence. Use this 10 minutes before any high-pressure situation to arrive calm and mentally prepared.",
        "learn": ["Performance anxiety management", "Confidence visualisation techniques", "Calming the nervous system before pressure", "Quick grounding when stakes are high"],
        "best_for": "Exams, job interviews, presentations, performances",
        "narrator": "Lily",
    },
    {
        "slug": "peak-performance",
        "title": "Peak Performance",
        "duration": "12 min",
        "category": "Focus",
        "gradient": "linear-gradient(160deg,#432818 0%,#6f1d1b 40%,#bb9457 100%)",
        "emoji": "&#128640;",
        "desc": "Mental preparation for high-stakes moments. Combines breathwork, visualisation, and positive reinforcement to help you perform at your best when it matters most.",
        "learn": ["Pre-performance mental routines", "Visualising success without pressure", "Managing adrenaline constructively", "Techniques used by elite athletes"],
        "best_for": "Sports, competitions, presentations, auditions",
        "narrator": "Lily",
    },
    {
        "slug": "deep-work-mode",
        "title": "Deep Work Mode",
        "duration": "5 min",
        "category": "Focus",
        "gradient": "linear-gradient(160deg,#14213d 0%,#003049 40%,#669bbc 100%)",
        "emoji": "&#127911;",
        "desc": "A quick mental reset to enter a state of focused, uninterrupted concentration. Five minutes to clear mental clutter and prime your brain for sustained attention.",
        "learn": ["Rapid mental clearing technique", "Setting a focus intention", "Creating a distraction-free mindset", "Pairing meditation with productivity systems"],
        "best_for": "Before deep work blocks, after meetings, task switching",
        "narrator": "Lily",
    },
    {
        "slug": "anxiety-relief",
        "title": "Anxiety Relief",
        "duration": "15 min",
        "category": "Stress",
        "gradient": "linear-gradient(160deg,#264653 0%,#2a9d8f 50%,#e9c46a 100%)",
        "emoji": "&#128154;",
        "desc": "When anxiety strikes, this session meets you where you are. Beginning with grounding techniques to bring you into the present moment, it then guides you through calming breathwork and a body-based release of anxious energy.",
        "learn": ["5-4-3-2-1 grounding technique", "Physiological sigh for instant calm", "Recognising anxiety vs. danger", "Building an anxiety toolkit"],
        "best_for": "Generalised anxiety, panic onset, overwhelming moments",
        "narrator": "Lily",
    },
    {
        "slug": "stress-dissolve",
        "title": "Stress Dissolve",
        "duration": "20 min",
        "category": "Stress",
        "gradient": "linear-gradient(160deg,#606c38 0%,#283618 50%,#dda15e 100%)",
        "emoji": "&#127810;",
        "desc": "A comprehensive stress-release session that works through the body, breath, and mind. Particularly effective after a difficult day — it helps you process what happened and let it go before it accumulates.",
        "learn": ["Three-stage stress release (body, breath, mind)", "Processing difficult events mindfully", "Preventing stress accumulation", "The cortisol cycle and how to complete it"],
        "best_for": "End-of-day decompression, chronic stress, burnout prevention",
        "narrator": "Lily",
    },
    {
        "slug": "self-compassion",
        "title": "Self-Compassion Practice",
        "duration": "18 min",
        "category": "Stress",
        "gradient": "linear-gradient(160deg,#9d4edd 0%,#c77dff 50%,#e0aaff 100%)",
        "emoji": "&#128149;",
        "desc": "We're often our own harshest critics. This session guides you through a loving-kindness meditation focused inward — learning to treat yourself with the same kindness you'd offer a close friend.",
        "learn": ["Loving-kindness (Metta) meditation", "Replacing self-criticism with self-compassion", "The three components of self-compassion", "Research on self-compassion and mental health"],
        "best_for": "Self-criticism, perfectionism, low self-esteem, grief",
        "narrator": "Lily",
    },
    {
        "slug": "worry-release",
        "title": "Letting Go of Worry",
        "duration": "12 min",
        "category": "Stress",
        "gradient": "linear-gradient(160deg,#3d405b 0%,#81b29a 50%,#f2cc8f 100%)",
        "emoji": "&#127744;",
        "desc": "A targeted meditation for when your mind is caught in worry loops. Using a 'catch, label, release' technique, you'll learn to notice worrying thoughts without feeding them.",
        "learn": ["The catch-label-release technique", "Understanding productive vs. unproductive worry", "Cognitive defusion (unhooking from thoughts)", "When to seek professional support"],
        "best_for": "Rumination, catastrophising, health anxiety, future worry",
        "narrator": "Lily",
    },
    {
        "slug": "releasing-tension",
        "title": "Releasing Tension",
        "duration": "15 min",
        "category": "Stress",
        "gradient": "linear-gradient(160deg,#582f0e 0%,#7f4f24 40%,#b08968 100%)",
        "emoji": "&#129693;",
        "desc": "A guided progressive muscle relaxation to physically release the stress you're carrying. Systematically tense and release each muscle group, teaching your body the difference between tension and relaxation.",
        "learn": ["Progressive muscle relaxation (PMR)", "Identifying where you hold tension", "The tension-release cycle", "Using PMR as a daily stress management tool"],
        "best_for": "Physical tension, headaches, jaw clenching, shoulder pain",
        "narrator": "Lily",
    },
    {
        "slug": "calm-reset",
        "title": "The Calm Reset",
        "duration": "5 min",
        "category": "Stress",
        "gradient": "linear-gradient(160deg,#2b2d42 0%,#8d99ae 40%,#edf2f4 100%)",
        "emoji": "&#127754;",
        "desc": "An emergency calm-down for overwhelming moments. Five minutes to reset your nervous system using the physiological sigh and grounding techniques. Keep this one bookmarked.",
        "learn": ["The physiological sigh (double inhale + long exhale)", "30-second grounding technique", "Vagal tone activation", "Building a personal emergency calm toolkit"],
        "best_for": "Panic moments, before difficult conversations, overwhelm",
        "narrator": "Lily",
    },
    {
        "slug": "anger-frustration-release",
        "title": "Anger &amp; Frustration Release",
        "duration": "12 min",
        "category": "Stress",
        "gradient": "linear-gradient(160deg,#370617 0%,#6a040f 40%,#d00000 60%,#e85d04 100%)",
        "emoji": "&#128293;",
        "desc": "Channel and release intense emotions through breathwork and guided visualisation. This session doesn't ask you to suppress anger — it helps you feel it fully and let it pass safely.",
        "learn": ["Safe emotional release techniques", "Breath of fire for processing intensity", "Visualisation for releasing anger", "The difference between expressing and processing anger"],
        "best_for": "After arguments, workplace frustration, road rage recovery",
        "narrator": "Lily",
    },
    {
        "slug": "introduction-to-mindfulness",
        "title": "Introduction to Mindfulness",
        "duration": "10 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#2d6a4f 0%,#40916c 40%,#74c69d 100%)",
        "emoji": "&#127793;",
        "desc": "Your first step into mindful awareness. This session explains what mindfulness actually is (and isn't), then guides you through a simple practice of noticing your breath and surroundings without judgement.",
        "learn": ["What mindfulness really means", "The difference between mindfulness and meditation", "A simple 3-step mindfulness practice", "Common misconceptions debunked"],
        "best_for": "Complete beginners, the curious, those who've tried and given up",
        "narrator": "Lily",
    },
    {
        "slug": "body-scan-meditation",
        "title": "Body Scan Meditation",
        "duration": "20 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#1b4332 0%,#2d6a4f 40%,#52b788 100%)",
        "emoji": "&#129528;",
        "desc": "Gently move your attention through each part of your body, from the crown of your head to the tips of your toes. Notice sensations without trying to change them — simply observe and release.",
        "learn": ["Systematic body awareness", "Noticing sensation without reaction", "The connection between body and emotion", "Using body scan for pain management"],
        "best_for": "Physical tension, chronic pain, disconnection from body, pre-sleep",
        "narrator": "Lily",
    },
    {
        "slug": "mindful-breathing",
        "title": "Mindful Breathing",
        "duration": "15 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#184e77 0%,#1a759f 40%,#76c893 100%)",
        "emoji": "&#127800;",
        "desc": "Anchor your attention on the breath — the most fundamental mindfulness practice. Learn to follow each inhale and exhale with gentle curiosity, returning patiently each time your mind wanders.",
        "learn": ["Breath as an anchor for attention", "The wandering mind is normal — not failure", "Three styles of breath awareness", "Building from 5 to 15 minutes of practice"],
        "best_for": "Daily practice, building concentration, stress reduction",
        "narrator": "Lily",
    },
    {
        "slug": "letting-go-of-thoughts",
        "title": "Letting Go of Thoughts",
        "duration": "12 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#3a5a40 0%,#588157 40%,#a3b18a 100%)",
        "emoji": "&#127807;",
        "desc": "Learn to observe your thoughts without attachment. Using the 'leaves on a stream' technique, you'll practise placing each thought on a leaf and watching it float away — building distance between you and your mental chatter.",
        "learn": ["Leaves on a stream visualisation", "Cognitive defusion techniques", "The difference between thinking and awareness", "Why fighting thoughts makes them louder"],
        "best_for": "Overthinking, rumination, difficulty meditating, busy minds",
        "narrator": "Lily",
    },
    {
        "slug": "open-awareness",
        "title": "Open Awareness",
        "duration": "25 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#0b525b 0%,#168aad 40%,#76c893 100%)",
        "emoji": "&#128167;",
        "desc": "Expand your attention to include all sensations, sounds, and thoughts simultaneously. Rather than focusing on one thing, you become aware of everything at once — a practice sometimes called 'choiceless awareness'.",
        "learn": ["Open monitoring meditation", "Expanding from narrow to wide attention", "Choiceless awareness technique", "When to use focused vs. open awareness"],
        "best_for": "Experienced meditators, deepening practice, creative thinking",
        "narrator": "Lily",
    },
    {
        "slug": "mindful-walking",
        "title": "Mindful Walking",
        "duration": "10 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#344e41 0%,#3a5a40 40%,#a3b18a 100%)",
        "emoji": "&#129717;",
        "desc": "Bring awareness to each step — the lift, the movement, the placement. A moving meditation for when sitting still feels difficult or when you want to bring mindfulness into everyday activity.",
        "learn": ["Walking meditation technique", "Mindfulness in movement", "Bringing meditation off the cushion", "Using walks as mini mindfulness sessions"],
        "best_for": "Restless meditators, lunch breaks, nature walks, ADHD",
        "narrator": "Lily",
    },
    {
        "slug": "mindfulness-at-work",
        "title": "Mindfulness at Work",
        "duration": "8 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#2b2d42 0%,#3a5a40 40%,#588157 100%)",
        "emoji": "&#127758;",
        "desc": "Quick reset for the workplace. Calm your mind before meetings, presentations, or difficult conversations. Designed to be done at your desk with your eyes open if needed.",
        "learn": ["Desk-friendly meditation techniques", "Managing workplace anxiety", "Mindful transitions between tasks", "The 3-breath reset for meetings"],
        "best_for": "Pre-meeting anxiety, workplace stress, difficult colleagues, burnout",
        "narrator": "Lily",
    },
    {
        "slug": "observing-emotions",
        "title": "Observing Emotions",
        "duration": "18 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#132a13 0%,#31572c 40%,#4f772d 100%)",
        "emoji": "&#128161;",
        "desc": "Develop the skill of sitting with difficult emotions without reacting or suppressing them. Learn to name what you feel, locate it in your body, and watch it change — building emotional resilience over time.",
        "learn": ["RAIN technique (Recognise, Allow, Investigate, Nurture)", "Emotional labelling for regulation", "Where emotions live in the body", "Building emotional resilience through observation"],
        "best_for": "Emotional reactivity, mood swings, anger management, grief",
        "narrator": "Lily",
    },
    {
        "slug": "morning-mindfulness",
        "title": "Morning Mindfulness",
        "duration": "7 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#006466 0%,#0b525b 40%,#144552 100%)",
        "emoji": "&#127774;",
        "desc": "Set an intentional tone for the day ahead with this gentle morning awareness practice. Before the rush begins, take seven minutes to arrive in your body and choose how you want to show up today.",
        "learn": ["Morning intention setting", "Waking up mindfully vs. reactively", "A simple gratitude-awareness practice", "Building a morning mindfulness habit"],
        "best_for": "Starting the day well, replacing phone scrolling, building habits",
        "narrator": "Lily",
    },
    {
        "slug": "mindful-eating",
        "title": "Mindful Eating",
        "duration": "10 min",
        "category": "Mindfulness",
        "gradient": "linear-gradient(160deg,#283618 0%,#606c38 40%,#dda15e 100%)",
        "emoji": "&#127860;",
        "desc": "Transform mealtimes into moments of presence. This guided practice walks you through eating a single meal (or snack) with full attention — noticing taste, texture, temperature, and gratitude.",
        "learn": ["The raisin exercise (classic mindfulness practice)", "Eating with all five senses", "Recognising hunger vs. emotional eating", "Slowing down to improve digestion"],
        "best_for": "Emotional eating, rushed meals, digestive issues, food appreciation",
        "narrator": "Lily",
    },
    {
        "slug": "meditation-for-beginners",
        "title": "Your First Meditation",
        "duration": "5 min",
        "category": "Beginners",
        "gradient": "linear-gradient(160deg,#006d77 0%,#83c5be 40%,#edf6f9 100%)",
        "emoji": "&#127795;",
        "desc": "Never meditated before? Start here. A gentle, no-pressure introduction that takes just five minutes. No special position required — sit however you're comfortable. We'll simply practise noticing the breath.",
        "learn": ["What to actually do when you meditate", "Why your mind wandering is not failure", "Finding a comfortable position", "The only instruction you really need"],
        "best_for": "Absolute beginners, the sceptical, those who think they can't meditate",
        "narrator": "Lily",
    },
    {
        "slug": "building-a-daily-practice",
        "title": "Building a Daily Practice",
        "duration": "10 min",
        "category": "Beginners",
        "gradient": "linear-gradient(160deg,#386641 0%,#6a994e 40%,#a7c957 100%)",
        "emoji": "&#128197;",
        "desc": "You know meditation works — but how do you make it stick? This session is part meditation, part coaching. Learn the science of habit formation applied specifically to a daily meditation practice.",
        "learn": ["The habit loop: cue, routine, reward", "Why 2 minutes beats 20 (at first)", "Anchoring meditation to existing habits", "What to do when you miss a day"],
        "best_for": "Anyone who starts and stops, building consistency",
        "narrator": "Lily",
    },
    {
        "slug": "meditation-foundations",
        "title": "Meditation Foundations",
        "duration": "15 min",
        "category": "Beginners",
        "gradient": "linear-gradient(160deg,#457b9d 0%,#1d3557 50%,#a8dadc 100%)",
        "emoji": "&#127959;",
        "desc": "The essential techniques every meditator needs. This session covers posture, breath, attention, and attitude — the four pillars that support every meditation style from mindfulness to mantra.",
        "learn": ["The four pillars of meditation", "Common posture mistakes and fixes", "Three breath techniques for different goals", "The attitude of gentle curiosity"],
        "best_for": "Beginners ready to deepen, self-taught meditators wanting foundations",
        "narrator": "Lily",
    },
    {
        "slug": "seven-day-mindfulness-course",
        "title": "7-Day Mindfulness Course",
        "duration": "Day 1 of 7",
        "category": "Beginners",
        "gradient": "linear-gradient(160deg,#264653 0%,#2a9d8f 40%,#e9c46a 100%)",
        "emoji": "&#128220;",
        "desc": "A structured week-long programme to build your mindfulness habit from scratch. Each day introduces a new concept and practice, gradually building your skills and confidence over seven days.",
        "learn": ["Day 1: Breath awareness", "Day 2: Body scan basics", "Day 3: Noting thoughts", "Day 4: Emotional awareness", "Day 5: Mindful movement", "Day 6: Loving-kindness", "Day 7: Integration and daily life"],
        "best_for": "Structured learners, complete beginners, building a 7-day streak",
        "narrator": "Lily",
    },
    {
        "slug": "yoga-nidra",
        "title": "Yoga Nidra",
        "duration": "45 min",
        "category": "Advanced",
        "gradient": "linear-gradient(160deg,#1a1a2e 0%,#16213e 40%,#533483 100%)",
        "emoji": "&#128718;",
        "desc": "The ancient practice of yogic sleep — profound rest while remaining fully conscious. One session of Yoga Nidra is said to be equivalent to several hours of sleep. This extended practice takes you through all five layers of being (koshas).",
        "learn": ["The five koshas (layers of being)", "Sankalpa: setting a heartfelt resolve", "Rotation of consciousness technique", "The hypnagogic state and its benefits"],
        "best_for": "Deep rest, burnout recovery, spiritual practice, insomnia",
        "narrator": "Lily",
    },
    {
        "slug": "loving-kindness",
        "title": "Loving-Kindness (Metta)",
        "duration": "20 min",
        "category": "Advanced",
        "gradient": "linear-gradient(160deg,#ff006e 0%,#fb5607 40%,#ffbe0b 100%)",
        "emoji": "&#128150;",
        "desc": "Systematically cultivate feelings of warmth and goodwill — first toward yourself, then loved ones, then neutral people, and finally difficult people. A transformative practice backed by extensive research.",
        "learn": ["The four stages of Metta meditation", "Generating genuine warmth on demand", "Working with resistance and difficult people", "Research: Metta changes brain structure in 8 weeks"],
        "best_for": "Relationship difficulties, self-criticism, expanding empathy, loneliness",
        "narrator": "Lily",
    },
    {
        "slug": "transcendental-stillness",
        "title": "Transcendental Stillness",
        "duration": "30 min",
        "category": "Advanced",
        "gradient": "linear-gradient(160deg,#000000 0%,#1a1a2e 50%,#2d2d44 100%)",
        "emoji": "&#9733;",
        "desc": "An extended silent meditation with minimal guidance. After a brief settling-in period, you'll sit in stillness with only occasional gentle reminders. For practitioners ready to sit with themselves.",
        "learn": ["Extended silent sitting", "Working with discomfort and restlessness", "Finding the stillness beneath thought", "Why silence is the deepest teacher"],
        "best_for": "Experienced meditators wanting less guidance, retreats, deepening practice",
        "narrator": "Lily",
    },
    {
        "slug": "vipassana-insight",
        "title": "Vipassana: Insight Meditation",
        "duration": "40 min",
        "category": "Advanced",
        "gradient": "linear-gradient(160deg,#0d1b2a 0%,#1b2838 40%,#415a77 100%)",
        "emoji": "&#9775;",
        "desc": "An extended insight meditation practice rooted in the Buddhist Theravada tradition. Observe the three characteristics of experience — impermanence, unsatisfactoriness, and non-self — through direct investigation.",
        "learn": ["The three marks of existence", "Noting practice (Mahasi style)", "Investigating impermanence in real-time", "The stages of insight"],
        "best_for": "Serious practitioners, Buddhist meditation path, retreat preparation",
        "narrator": "Lily",
    },
    {
        "slug": "chakra-alignment",
        "title": "Chakra Alignment",
        "duration": "35 min",
        "category": "Advanced",
        "gradient": "linear-gradient(160deg,#001219 0%,#005f73 40%,#94d2bd 100%)",
        "emoji": "&#9883;",
        "desc": "Journey through each of the seven energy centres with breath, visualisation, and intention. Whether you approach chakras as literal energy or useful metaphors, this practice offers deep self-exploration.",
        "learn": ["The seven chakras and their qualities", "Breath and colour visualisation for each centre", "Recognising blocked vs. balanced energy", "Integrating chakra work into daily life"],
        "best_for": "Energy work, holistic practice, self-exploration, yoga practitioners",
        "narrator": "Lily",
    },
    {
        "slug": "non-dual-awareness",
        "title": "Non-Dual Awareness",
        "duration": "30 min",
        "category": "Advanced",
        "gradient": "linear-gradient(160deg,#1a1a2e 0%,#16213e 40%,#0f3460 100%)",
        "emoji": "&#128302;",
        "desc": "Explore the space between observer and observed. This practice points you toward the awareness that is always present — before thought, beneath emotion, beyond the sense of a separate self.",
        "learn": ["What non-dual awareness means", "Self-inquiry: 'Who is aware?'", "The difference between experience and the experiencer", "Practices from Advaita Vedanta and Dzogchen traditions"],
        "best_for": "Advanced meditators, philosophical inquiry, spiritual deepening",
        "narrator": "Lily",
    },
]

NAV = """  <div class="promo-banner">Start your free 7-day trial<a href="../apps.html">Premium</a></div>

  <nav class="nav" style="position:relative;">
    <div class="container">
      <a href="../index.html" class="nav-logo"><img src="../Salus.PNG" alt="Salus" class="nav-icon" style="height:32px;border-radius:6px;margin-right:8px;">SALUS</a>
      <ul class="nav-links">
        <li><a href="../index.html">Home</a></li>
        <li><a href="../sessions.html">Sessions</a></li>
        <li><a href="../soundscapes.html">Soundscapes</a></li>
        <li><a href="../education.html">Learn</a></li>
        <li><a href="../mindfulness.html">Mindfulness</a></li>
        <li><a href="../about.html">About</a></li>
        <li><a href="../apps.html">Apps</a></li>
        <li><a href="../contact.html">Contact</a></li>
        <li><a href="../newsletter.html">Newsletter</a></li>
      </ul>
      <button class="nav-toggle" aria-label="Toggle menu">&#9776;</button>
    </div>
  </nav>"""

FOOTER = """  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          <h4 style="letter-spacing:2px;">SALUS</h4>
          <p>SLEEP &middot; RELAX &middot; RESTORE</p>
          <p style="margin-top:8px;">Meditation and mindfulness for everyday life.</p>
        </div>
        <div>
          <h4>Pages</h4>
          <ul>
            <li><a href="../index.html">Home</a></li>
            <li><a href="../sessions.html">Sessions</a></li>
            <li><a href="../soundscapes.html">Soundscapes</a></li>
            <li><a href="../education.html">Learn</a></li>
            <li><a href="../mindfulness.html">Mindfulness</a></li>
            <li><a href="../about.html">About</a></li>
            <li><a href="../apps.html">Apps</a></li>
          </ul>
        </div>
        <div>
          <h4>Support</h4>
          <ul>
            <li><a href="../contact.html">Contact</a></li>
            <li><a href="../faq.html">FAQ</a></li>
            <li><a href="../privacy.html">Privacy</a></li>
            <li><a href="../terms.html">Terms</a></li>
          </ul>
        </div>
        <div>
          <h4>Tools</h4>
          <ul>
            <li><a href="../breathe.html">Breathing Timer</a></li>
            <li><a href="../timer.html">Meditation Timer</a></li>
            <li><a href="../sounds.html">Sleep Sounds</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        &copy; 2026 Salus. All rights reserved.
      </div>
    </div>
  </footer>"""


def build_page(s):
    learn_items = "\n".join(f'            <li>{item}</li>' for item in s["learn"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{s['title']} — Salus</title>
  <meta name="description" content="{s['desc'][:155]}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Cormorant+Garamond:wght@600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <style>
    .session-detail-hero {{
      background: {s['gradient']};
      padding: 80px 0 60px;
      text-align: center;
      color: #fff;
    }}
    .session-detail-hero .emoji {{ font-size: 4rem; display: block; margin-bottom: 16px; }}
    .session-detail-hero h1 {{ font-size: 2.2rem; margin-bottom: 8px; }}
    .session-detail-hero .meta {{ opacity: 0.8; font-size: 0.95rem; }}
    .session-detail-hero .meta span {{ margin: 0 8px; }}
    .session-body {{ max-width: 720px; margin: 0 auto; padding: 48px 24px; }}
    .session-body h2 {{ font-size: 1.4rem; margin: 32px 0 16px; color: var(--forest); }}
    .session-body p {{ color: var(--mid-gray); line-height: 1.8; margin-bottom: 16px; font-size: 1rem; }}
    .session-body ul {{ color: var(--mid-gray); line-height: 2; padding-left: 24px; margin-bottom: 24px; }}
    .session-body li {{ margin-bottom: 4px; }}
    .best-for {{ background: var(--off-white); border-radius: 12px; padding: 20px 24px; margin: 24px 0; }}
    .best-for strong {{ color: var(--forest); }}
    .unlock-cta {{
      text-align: center; padding: 48px 24px; margin: 32px 0;
      background: var(--off-white); border-radius: 16px;
    }}
    .unlock-cta h2 {{ margin-bottom: 12px; color: var(--forest); }}
    .unlock-cta p {{ color: var(--mid-gray); margin-bottom: 20px; }}
    .back-link {{ display: inline-block; margin-bottom: 24px; color: var(--accent); text-decoration: none; font-weight: 600; }}
    .back-link:hover {{ text-decoration: underline; }}
    .narrator-badge {{
      display: inline-flex; align-items: center; gap: 8px;
      background: rgba(255,255,255,0.15); border-radius: 50px;
      padding: 8px 16px; margin-top: 16px; font-size: 0.85rem;
    }}
  </style>
</head>
<body>

{NAV}

  <section class="session-detail-hero">
    <div class="container">
      <span class="emoji">{s['emoji']}</span>
      <h1>{s['title']}</h1>
      <div class="meta">
        <span>{s['duration']}</span> &middot;
        <span>{s['category']}</span>
      </div>
      <div class="narrator-badge">&#127908; Narrated by {s['narrator']}</div>
    </div>
  </section>

  <div class="session-body">
    <a href="../sessions.html" class="back-link">&larr; All Sessions</a>

    <h2>About This Session</h2>
    <p>{s['desc']}</p>

    <h2>What You'll Learn</h2>
    <ul>
{learn_items}
    </ul>

    <div class="best-for">
      <strong>Best for:</strong> {s['best_for']}
    </div>

    <div class="unlock-cta">
      <h2>&#128274; Premium Session</h2>
      <p>Unlock this session and hundreds more with Salus Premium.</p>
      <a href="../apps.html" class="btn">Start Free Trial</a>
    </div>
  </div>

{FOOTER}

  <script src="../js/main.js"></script>
</body>
</html>
"""
    return html


count = 0
for s in sessions:
    path = os.path.join(OUT_DIR, f"{s['slug']}.html")
    with open(path, 'w') as f:
        f.write(build_page(s))
    count += 1
    print(f"  {s['slug']}.html")

print(f"\nGenerated {count} session pages in sessions/")
