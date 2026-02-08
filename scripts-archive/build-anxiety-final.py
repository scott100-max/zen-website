#!/usr/bin/env python3
"""
Build breathing-for-anxiety audio using Fish Audio TTS.
Single call, no splicing. Ellipsis pauses for breathing gaps.
"""
import os, requests

# Load .env
for line in open('.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k] = v

API_KEY = os.environ.get("FISH_API_KEY", "")
VOICE_ID = "0165567b33324f518b02336ad232e31a"  # Calm voice
OUTPUT = "content/audio/03-breathing-for-anxiety.mp3"

script = """Welcome to Salus. If you're feeling anxious right now, I want you to know, you're in the right place. And you're going to feel better.

...

When you're anxious, your body activates its fight-or-flight response. Your heart rate increases, your breathing gets shallow, and your muscles tense. This is your nervous system trying to protect you.

...

But here's the key. Your breath is the one part of this system you can control consciously. When you slow your exhale, you activate the vagus nerve, which signals your brain to switch from alert mode to rest and digest mode. It's not a trick. It's biology.

...

Today I'm going to teach you two breathing techniques you can use anywhere, anytime. Let's begin.

...

The first technique is called box breathing. It's used by everyone from Navy SEALs to therapists because it works quickly and reliably.

The pattern is simple. Breathe in for four counts, then breathe out for four. A steady, calming rhythm.

...

Let's try it. Sit comfortably. Let your shoulders drop. I'll guide you through each phase. Just follow my voice.

...

...

Now, gently and slowly, breathe in through your nose, filling your lungs completely.

...

...

And now, slowly and gently, breathe all the way out through your mouth, letting everything go.

...

...

Good. Let's do three more rounds together.

...

Once again, gently and slowly, breathe in through your nose, all the way in.

...

...

And now, slowly and gently, let all of that air flow back out through your mouth.

...

...

Breathing in once more, nice and slow, filling your chest and your belly with air.

...

...

And releasing it all, slowly and completely, letting everything go with your exhale.

...

...

One last round now. Gently breathing in, all the way in, nice and slow.

...

...

And slowly breathing out, letting your body soften and relax as the air leaves.

...

...

Notice how you feel right now. Even after just a few rounds, most people report feeling noticeably calmer. That's the vagus nerve doing its job.

...

...

The second technique was developed by Dr Andrew Weil and is particularly effective for acute anxiety and for falling asleep.

The pattern is this. Breathe in through your nose for four counts, then exhale slowly through your mouth for eight counts. The long exhale is what activates your relaxation response.

...

Let's practise together now. Place the tip of your tongue gently on the roof of your mouth, just behind your front teeth. Keep it there throughout.

...

...

Now, gently and slowly, breathe in through your nose, nice and deep.

...

...

And now, very slowly, exhale all the way out through your mouth, letting it take as long as it needs.

...

...

...

Let's do that three more times together.

...

Once again, gently and slowly, breathe in through your nose, filling your lungs completely.

...

...

And now, slowly and softly, breathe all the way out through your mouth, nice and long.

...

...

...

Breathing in once more, gently through your nose, taking your time with each breath.

...

...

And letting it all go now, breathing out slowly and completely through your mouth.

...

...

...

One last round. Gently breathing in through your nose, all the way in, nice and slow.

...

...

And now, slowly and gently, releasing everything with one long, soft exhale.

...

...

...

Beautiful. You might feel a little lightheaded. That's perfectly normal when you first practise. It passes quickly.

...

You now have two tools that are always with you.

Box breathing is best for in-the-moment calm. Before a meeting, during a stressful conversation, or whenever you feel your chest tightening.

...

Four-seven-eight breathing is ideal for winding down. Before sleep, after a long day, or when anxious thoughts are spiralling.

...

Start with four rounds and build up as it feels comfortable. The more you practise, the faster your body responds.

...

You showed up for yourself today, and that matters. I'll see you next time on Salus.

...

...

Sleep. Relax. Restore."""


def main():
    print("Generating full anxiety script (single call, Fish Audio calm voice)...")
    resp = requests.post(
        "https://api.fish.audio/v1/tts",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "model": "s1",
            "Content-Type": "application/json",
        },
        json={"text": script, "format": "mp3", "reference_id": VOICE_ID, "prosody": {"speed": 1.0, "volume": 0}},
    )
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} - {resp.text[:300]}")
        return

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'wb') as f:
        f.write(resp.content)

    size_mb = len(resp.content) / 1024 / 1024
    print(f"Done! Output: {OUTPUT}")
    print(f"Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
