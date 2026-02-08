#!/usr/bin/env python3
"""Quick verification: does the Gate 8 manifest text guard fix the false positive?

Reproduces the Gate 8 logic with the new fix to confirm it passes.
"""
import json, re
import numpy as np
import librosa

AUDIO = "/Users/scottripley/salus-website/content/audio-free/raw/36-loving-kindness-intro-v2_precleanup.wav"
MANIFEST = "/Users/scottripley/salus-website/content/audio-free/36-loving-kindness-intro-v2_manifest.json"

EXPECTED_REPS = [
    "may i be", "may you be", "may they be", "may all beings be", "may all beings",
    "a sense of ease", "deep abiding peace", "safe and protected",
    "may you be safe", "may you be happy", "may you be healthy", "may you live with ease"
]

REPETITION_IGNORE_PHRASES = [
    "breathe in", "breathe out", "breathing in", "breathing out",
    "let go", "letting go", "let it go", "gently let",
    "notice the sensations", "notice any sensations",
    "gently bring your attention", "bring your awareness",
    "take a deep breath", "take another breath", "take a slow breath",
    "in and out", "slowly and gently",
    "when youre ready", "when you're ready",
    "and gently", "gently now",
]

with open(MANIFEST) as f:
    manifest = json.load(f)

text_segments = [s for s in manifest['segments'] if s['type'] == 'text' and s.get('duration', 0) > 2]

print(f"Loading audio: {AUDIO}")
y, sr = librosa.load(AUDIO, sr=22050)
print(f"Loaded {len(y)/sr:.1f}s audio, {len(text_segments)} text segments")

# ── Approach A: MFCC fingerprint comparison ──
print("\n[A] MFCC segment comparison...")
segment_mfccs = []
for seg in text_segments:
    start_sample = int(seg['start_time'] * sr)
    end_sample = int(seg['end_time'] * sr)
    if end_sample > len(y):
        end_sample = len(y)
    if end_sample - start_sample < sr:
        segment_mfccs.append(None)
        continue
    segment_audio = y[start_sample:end_sample]
    mfcc = librosa.feature.mfcc(y=segment_audio, sr=sr, n_mfcc=13)
    segment_mfccs.append(mfcc.mean(axis=1))

mfcc_duplicates = []
mfcc_sim_threshold = 0.998
min_gap_sec = 5.0
for i in range(len(segment_mfccs)):
    if segment_mfccs[i] is None:
        continue
    for j in range(i + 1, len(segment_mfccs)):
        if segment_mfccs[j] is None:
            continue
        gap = abs(text_segments[j]['start_time'] - text_segments[i]['end_time'])
        if gap < min_gap_sec:
            continue
        dot = np.dot(segment_mfccs[i], segment_mfccs[j])
        norm_i = np.linalg.norm(segment_mfccs[i])
        norm_j = np.linalg.norm(segment_mfccs[j])
        sim = dot / (norm_i * norm_j) if (norm_i * norm_j) > 0 else 0
        if sim >= mfcc_sim_threshold:
            mfcc_duplicates.append({
                'seg_a': i, 'seg_b': j,
                'time_a': text_segments[i]['start_time'],
                'time_b': text_segments[j]['start_time'],
                'similarity': round(float(sim), 4),
            })

print(f"[A] Found {len(mfcc_duplicates)} MFCC-similar segment pairs")
for d in mfcc_duplicates:
    ta, tb = d['time_a'], d['time_b']
    txt_a = text_segments[d['seg_a']].get('text', '')[:60]
    txt_b = text_segments[d['seg_b']].get('text', '')[:60]
    print(f"    {int(ta//60)}:{ta%60:04.1f} \"{txt_a}...\"")
    print(f"    {int(tb//60)}:{tb%60:04.1f} \"{txt_b}...\"")
    print(f"    sim={d['similarity']}")

# ── Approach B: Whisper STT ──
print("\n[B] Whisper transcription...")
whisper_duplicates = []
try:
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(AUDIO, language="en")
    transcript_segments = result.get('segments', [])

    words = []
    for seg in transcript_segments:
        text = seg['text'].strip().lower()
        text = re.sub(r'[^\w\s]', '', text)
        seg_words = text.split()
        for w_text in seg_words:
            words.append({'word': w_text, 'time': seg['start']})

    min_word_match = 8
    if len(words) >= min_word_match:
        ngram_index = {}
        ignore_list = REPETITION_IGNORE_PHRASES + EXPECTED_REPS
        for i in range(len(words) - min_word_match + 1):
            ngram = ' '.join(w['word'] for w in words[i:i + min_word_match])
            ignored = any(phrase in ngram for phrase in ignore_list)
            if ignored:
                continue
            if ngram in ngram_index:
                prev_time = ngram_index[ngram]
                curr_time = words[i]['time']
                if abs(curr_time - prev_time) > min_gap_sec:
                    whisper_duplicates.append({
                        'phrase': ngram,
                        'first_time': round(prev_time, 1),
                        'second_time': round(curr_time, 1),
                    })
            else:
                ngram_index[ngram] = words[i]['time']

    print(f"[B] Found {len(whisper_duplicates)} repeated phrases")
    for d in whisper_duplicates:
        print(f"    \"{d['phrase']}\" at {d['first_time']}s and {d['second_time']}s")

except Exception as e:
    print(f"[B] Whisper error: {e}")

# ── Combined verdict WITH manifest text guard ──
print("\n[COMBINED] Checking with manifest text guard...")
confirmed_repeats = []
for mfcc_dup in mfcc_duplicates:
    # NEW FIX: Check manifest text
    seg_a_text = text_segments[mfcc_dup['seg_a']].get('text', '').lower().strip()
    seg_b_text = text_segments[mfcc_dup['seg_b']].get('text', '').lower().strip()
    if seg_a_text and seg_b_text:
        words_a = set(seg_a_text.split())
        words_b = set(seg_b_text.split())
        overlap = len(words_a & words_b)
        max_words = max(len(words_a), len(words_b), 1)
        word_overlap_ratio = overlap / max_words
        if word_overlap_ratio < 0.6:
            print(f"  SKIP: seg {mfcc_dup['seg_a']}↔{mfcc_dup['seg_b']} — different text (overlap={word_overlap_ratio:.0%})")
            continue

    for w_dup in whisper_duplicates:
        if (abs(w_dup['first_time'] - mfcc_dup['time_a']) < 10 and
            abs(w_dup['second_time'] - mfcc_dup['time_b']) < 10):
            confirmed_repeats.append({**mfcc_dup, 'phrase': w_dup['phrase']})
            break

print(f"\n{'='*60}")
passed = len(confirmed_repeats) == 0
print(f"Gate 8 result: {'PASSED' if passed else 'FAILED'}")
if confirmed_repeats:
    for r in confirmed_repeats:
        print(f"  CONFIRMED: {r}")
