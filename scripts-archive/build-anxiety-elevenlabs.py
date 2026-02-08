#!/usr/bin/env python3
"""
Build breathing-for-anxiety audio using ElevenLabs TTS with SSML break tags.
Single API call - no splicing. Pauses baked into the generation.
"""
import os, requests

# Load .env
for line in open('.env'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k] = v

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
VOICE_ID = "pFZP5JQG7iQjIQuC4Bku"  # Lily
OUTPUT = "content/audio/03-breathing-for-anxiety.mp3"

# Use <break> tags for pauses (max 3s each, chain for longer)
P2 = '<break time="2.0s" />'
P3 = '<break time="3.0s" />'
P4 = '<break time="3.0s" /><break time="1.0s" />'
P5 = '<break time="3.0s" /><break time="2.0s" />'
P7 = '<break time="3.0s" /><break time="3.0s" /><break time="1.0s" />'

script = f"""Welcome to Salus. If you're feeling anxious right now, I want you to know: you're in the right place. And you're going to feel better.

{P2}

When you're anxious, your body activates its fight-or-flight response. Your heart rate increases, your breathing gets shallow, and your muscles tense. This is your nervous system trying to protect you.

{P2}

But here's the key: your breath is the one part of this system you can control consciously. When you slow your exhale, you activate the vagus nerve, which signals your brain to switch from alert mode to rest and digest mode. It's not a trick. It's biology.

{P2}

Today I'm going to teach you two breathing techniques you can use anywhere, anytime. Let's begin.

{P2}

The first technique is called box breathing. It's used by everyone from Navy SEALs to therapists because it works quickly and reliably.

{P2}

The pattern is simple: breathe in for four counts, then breathe out for four. A steady, calming rhythm.

{P2}

Let's try it. Sit comfortably. Let your shoulders drop. I'll guide you through each phase. Just follow my voice.

{P3}

Now, gently and slowly, breathe in through your nose, filling your lungs completely.

{P4}

And now, slowly and gently, breathe all the way out through your mouth.

{P4}

Good. That was your first round. Let's do three more rounds together, nice and easy.

{P2}

Once again, gently and slowly, breathe in through your nose, all the way in.

{P4}

And now, slowly and gently, let all of that air flow back out through your mouth.

{P4}

Breathing in once more, nice and slow, filling your chest and your belly with air.

{P4}

And releasing it all, slowly and completely, letting everything go with your exhale.

{P4}

One last round now. Gently breathing in, all the way in, nice and slow.

{P4}

And slowly breathing out, letting your body soften and relax as the air leaves.

{P4}

Notice how you feel right now. Even after just a few rounds, most people report feeling noticeably calmer. That's the vagus nerve doing its job.

{P3}

The second technique was developed by Dr Andrew Weil and is particularly effective for acute anxiety and for falling asleep.

{P2}

The pattern is this: breathe in through your nose for four counts, then exhale slowly through your mouth for eight counts. The long exhale is what activates your relaxation response.

{P2}

Let's practise together now. Place the tip of your tongue gently on the roof of your mouth, just behind your front teeth. Keep it there throughout.

{P3}

Now, gently and slowly, breathe in through your nose, nice and deep.

{P4}

And now, very slowly, exhale all the way out through your mouth, letting it take as long as it needs.

{P7}

Let's do that three more times together.

{P2}

Once again, gently and slowly, breathe in through your nose, filling your lungs completely.

{P4}

And now, slowly and softly, breathe all the way out through your mouth, nice and long.

{P7}

Breathing in once more, gently through your nose, taking your time with each breath.

{P4}

And letting it all go now, breathing out slowly and completely through your mouth.

{P7}

One last round. Gently breathing in through your nose, all the way in, nice and slow.

{P4}

And now, slowly and gently, releasing everything with one long, soft exhale.

{P7}

Beautiful. You might feel a little lightheaded. That's normal when you first practise. It passes quickly.

{P2}

You now have two tools that are always with you.

{P2}

Box breathing is best for in-the-moment calm. Before a meeting, during a stressful conversation, or whenever you feel your chest tightening.

{P2}

Four-seven-eight breathing is ideal for winding down. Before sleep, after a long day, or when anxious thoughts are spiralling.

{P2}

Start with four rounds and build up as it feels comfortable. The more you practise, the faster your body responds.

{P2}

You showed up for yourself today, and that matters. I'll see you next time on Salus.

{P2}

Sleep. Relax. Restore."""


def main():
    print("Generating full script with SSML breaks (single API call)...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    resp = requests.post(url, headers={
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }, json={
        "text": script,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.90,
            "similarity_boost": 0.65,
            "style": 0.03,
            "use_speaker_boost": True,
            "speed": 0.90
        }
    })
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
