#!/usr/bin/env python3
"""
Extend silence gaps in meditation audio files using ffmpeg.

Professional meditation apps like Calm include substantial silences (up to 1:45)
to let listeners actually practice rather than just listen. This script:
1. Detects existing silent segments in the audio using ffmpeg's silencedetect
2. Extends them based on session type and pause context
3. Creates more authentic, professional-feeling meditation experiences
"""

import os
import subprocess
import json
import random
import re
import tempfile
import shutil

# Session categories and their pause profiles (min_ms, max_ms)
PAUSE_PROFILES = {
    'sleep': {
        'short': (8000, 15000),      # 8-15 seconds
        'medium': (25000, 45000),    # 25-45 seconds
        'long': (60000, 105000),     # 60-105 seconds (1:45 max)
    },
    'relaxation': {
        'short': (6000, 12000),      # 6-12 seconds
        'medium': (20000, 40000),    # 20-40 seconds
        'long': (45000, 90000),      # 45-90 seconds
    },
    'stress': {
        'short': (5000, 10000),      # 5-10 seconds
        'medium': (15000, 30000),    # 15-30 seconds
        'long': (30000, 60000),      # 30-60 seconds
    },
    'mindfulness': {
        'short': (5000, 12000),      # 5-12 seconds
        'medium': (20000, 40000),    # 20-40 seconds
        'long': (45000, 75000),      # 45-75 seconds
    },
    'focus': {
        'short': (3000, 6000),       # 3-6 seconds
        'medium': (8000, 15000),     # 8-15 seconds
        'long': (15000, 30000),      # 15-30 seconds
    },
    'beginner': {
        'short': (4000, 8000),       # 4-8 seconds
        'medium': (12000, 25000),    # 12-25 seconds
        'long': (25000, 45000),      # 25-45 seconds
    },
    'advanced': {
        'short': (8000, 15000),      # 8-15 seconds
        'medium': (30000, 60000),    # 30-60 seconds
        'long': (75000, 105000),     # 75-105 seconds
    },
}

# Map audio files to their categories
SESSION_CATEGORIES = {
    # Sleep sessions (05-11)
    '05-body-scan-deep-rest': 'sleep',
    '06-letting-go-of-the-day': 'sleep',
    '07-moonlight-drift': 'sleep',
    '08-sleep-stories-quiet-shore': 'sleep',
    '09-rainfall-sleep-journey': 'sleep',
    '10-counting-down-to-sleep': 'sleep',
    '11-lucid-dream-preparation': 'sleep',

    # Focus sessions (12-17)
    '12-five-minute-reset': 'focus',
    '13-flow-state': 'focus',
    '14-morning-clarity': 'focus',
    '15-deep-work-prep': 'focus',
    '16-peak-performance': 'focus',
    '17-deep-work-mode': 'focus',

    # Stress sessions (18-24)
    '18-calm-in-three-minutes': 'stress',
    '19-release-and-restore': 'stress',
    '20-tension-melt': 'stress',
    '21-anxiety-unravelled': 'stress',
    '22-releasing-tension': 'stress',
    '23-the-calm-reset': 'stress',
    '24-anger-frustration-release': 'stress',

    # Mindfulness sessions (25-34)
    '25-introduction-to-mindfulness': 'mindfulness',
    '26-body-scan-meditation': 'mindfulness',
    '27-mindful-breathing': 'mindfulness',
    '28-letting-go-of-thoughts': 'mindfulness',
    '29-open-awareness': 'mindfulness',
    '30-mindful-walking': 'mindfulness',
    '31-mindfulness-at-work': 'mindfulness',
    '32-observing-emotions': 'mindfulness',
    '33-morning-mindfulness': 'mindfulness',
    '34-mindful-eating': 'mindfulness',

    # Beginner sessions (35-38)
    '35-your-first-meditation': 'beginner',
    '36-loving-kindness-intro': 'beginner',
    '37-building-a-daily-practice': 'beginner',
    '38-seven-day-mindfulness-day1': 'beginner',

    # Advanced sessions (39-44)
    '39-yoga-nidra': 'advanced',
    '40-gratitude-before-sleep': 'sleep',  # Sleep category
    '41-vipassana-insight': 'advanced',
    '42-chakra-alignment': 'advanced',
    '43-non-dual-awareness': 'advanced',
    '44-transcendental-stillness': 'advanced',
}

def get_category(filename):
    """Get the category for an audio file."""
    base = os.path.splitext(os.path.basename(filename))[0]
    return SESSION_CATEGORIES.get(base, 'mindfulness')

def get_duration(filepath):
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])

def detect_silences(filepath, min_duration=0.4, threshold=-45):
    """Detect silent segments using ffmpeg's silencedetect filter."""
    cmd = [
        'ffmpeg', '-i', filepath, '-af',
        f'silencedetect=n={threshold}dB:d={min_duration}',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse silence detection output
    silences = []
    silence_start = None

    for line in result.stderr.split('\n'):
        if 'silence_start:' in line:
            match = re.search(r'silence_start:\s*([\d.]+)', line)
            if match:
                silence_start = float(match.group(1))
        elif 'silence_end:' in line and silence_start is not None:
            match = re.search(r'silence_end:\s*([\d.]+)', line)
            if match:
                silence_end = float(match.group(1))
                silences.append((silence_start, silence_end))
                silence_start = None

    return silences

def classify_silence_length(duration_sec):
    """Classify original silence as short, medium, or long based on duration."""
    if duration_sec < 0.8:
        return 'short'
    elif duration_sec < 1.5:
        return 'medium'
    else:
        return 'long'

def extend_silences(input_path, output_path):
    """
    Extend silent segments in an audio file using ffmpeg.
    """
    print(f"\nProcessing: {os.path.basename(input_path)}")

    # Get original duration
    original_duration = get_duration(input_path)
    print(f"  Original duration: {original_duration:.1f}s ({original_duration/60:.1f}min)")

    # Get category and pause profile
    category = get_category(input_path)
    profile = PAUSE_PROFILES.get(category, PAUSE_PROFILES['mindfulness'])
    print(f"  Category: {category}")

    # Detect silences
    silences = detect_silences(input_path)
    print(f"  Found {len(silences)} silence segments")

    if not silences:
        print("  No silences found, copying original...")
        shutil.copy(input_path, output_path)
        return False

    # Filter out very short silences (natural speech pauses < 0.35s)
    significant_silences = [(s, e) for s, e in silences if (e - s) >= 0.35]
    print(f"  Significant silences (>=0.35s): {len(significant_silences)}")

    if not significant_silences:
        print("  No significant silences, copying original...")
        shutil.copy(input_path, output_path)
        return False

    # Create temporary directory for segments
    with tempfile.TemporaryDirectory() as tmpdir:
        segments = []
        prev_end = 0
        total_added = 0

        for i, (start, end) in enumerate(significant_silences):
            original_silence_len = end - start
            silence_type = classify_silence_length(original_silence_len)

            # Get target silence range
            min_target, max_target = profile[silence_type]
            target_silence_ms = random.randint(min_target, max_target)
            target_silence_sec = target_silence_ms / 1000

            # Extract audio segment before silence
            if start > prev_end:
                segment_file = os.path.join(tmpdir, f'seg_{i:04d}_audio.mp3')
                cmd = [
                    'ffmpeg', '-y', '-i', input_path,
                    '-ss', str(prev_end), '-t', str(start - prev_end),
                    '-c:a', 'libmp3lame', '-b:a', '192k',
                    segment_file
                ]
                subprocess.run(cmd, capture_output=True)
                segments.append(segment_file)

            # Create silence segment (or extended silence)
            silence_file = os.path.join(tmpdir, f'seg_{i:04d}_silence.mp3')

            if target_silence_sec > original_silence_len:
                # Generate silence
                cmd = [
                    'ffmpeg', '-y', '-f', 'lavfi',
                    '-i', f'anullsrc=r=44100:cl=stereo',
                    '-t', str(target_silence_sec),
                    '-c:a', 'libmp3lame', '-b:a', '192k',
                    silence_file
                ]
                subprocess.run(cmd, capture_output=True)
                total_added += (target_silence_sec - original_silence_len)
            else:
                # Keep original silence
                cmd = [
                    'ffmpeg', '-y', '-i', input_path,
                    '-ss', str(start), '-t', str(original_silence_len),
                    '-c:a', 'libmp3lame', '-b:a', '192k',
                    silence_file
                ]
                subprocess.run(cmd, capture_output=True)

            segments.append(silence_file)
            prev_end = end

        # Add final segment after last silence
        if prev_end < original_duration:
            final_file = os.path.join(tmpdir, f'seg_final.mp3')
            cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-ss', str(prev_end),
                '-c:a', 'libmp3lame', '-b:a', '192k',
                final_file
            ]
            subprocess.run(cmd, capture_output=True)
            segments.append(final_file)

        # Create concat file
        concat_file = os.path.join(tmpdir, 'concat.txt')
        with open(concat_file, 'w') as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")

        # Concatenate all segments
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-c:a', 'libmp3lame', '-b:a', '192k',
            output_path
        ]
        subprocess.run(cmd, capture_output=True)

    # Get new duration
    new_duration = get_duration(output_path)
    print(f"  New duration: {new_duration:.1f}s ({new_duration/60:.1f}min)")
    print(f"  Added: {total_added:.1f}s of silence")

    return True

def main():
    audio_dir = 'content/audio'
    output_dir = 'content/audio-extended'

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Get all session audio files (05 onwards have the meditation content)
    files_to_process = []
    for f in sorted(os.listdir(audio_dir)):
        if not f.endswith('.mp3'):
            continue
        # Skip non-session files (00-04 are intro/educational)
        if f.startswith('00-') or f.startswith('01-') or f.startswith('02-') or f.startswith('03-') or f.startswith('04-'):
            continue
        # Skip backup files
        if 'backup' in f:
            continue
        files_to_process.append(f)

    print(f"Found {len(files_to_process)} session files to process")
    print("=" * 60)

    processed = 0
    for filename in files_to_process:
        input_path = os.path.join(audio_dir, filename)
        output_path = os.path.join(output_dir, filename)

        try:
            if extend_silences(input_path, output_path):
                processed += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Processed {processed} files")
    print(f"Extended audio saved to: {output_dir}/")
    print("\nTo replace originals, run:")
    print(f"  cp {output_dir}/*.mp3 {audio_dir}/")

if __name__ == '__main__':
    main()
