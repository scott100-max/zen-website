#!/usr/bin/env python3
"""
Salus Audio Quality Analyzer v5
Ultra-sensitive detection for:
- AUDIO DROPOUTS (silence where speech should be) - NEW
- Sibilance (harsh 's' sounds)
- Clicks/glitches/pops
- Voice changes
- Hissing artifacts

v5 changes:
1. AUDIO DROPOUT DETECTION - finds gaps/silence inside speech segments
2. This catches TTS failures and concat errors that v4 missed
"""

import os
import sys
import numpy as np
import librosa
import scipy.signal as signal
from scipy.spatial.distance import cosine
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class AudioQualityAnalyzerV5:
    def __init__(self, audio_path, output_dir=None):
        self.audio_path = audio_path
        self.filename = os.path.basename(audio_path)
        self.output_dir = output_dir or os.path.dirname(audio_path) or '.'

        print(f"Loading: {self.filename}")
        self.y, self.sr = librosa.load(audio_path, sr=22050)
        self.duration = librosa.get_duration(y=self.y, sr=self.sr)
        print(f"Duration: {self.duration/60:.1f} minutes ({self.duration:.1f}s)")

        self.hop_length = 512
        self.frame_length = 2048
        self.issues = []
        self.baseline_voice = None
        self.manifest = None

        # Try to load manifest for better analysis
        manifest_path = audio_path.replace('.mp3', '_manifest.json')
        if os.path.exists(manifest_path):
            try:
                import json
                with open(manifest_path) as f:
                    self.manifest = json.load(f)
                print(f"Manifest loaded: {len(self.manifest.get('segments', []))} segments")
            except:
                pass

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{mins:02d}:{secs:02d}.{ms:02d}"

    def detect_sibilance(self):
        """
        Detect harsh sibilant 's' sounds.
        Sibilance shows as energy spikes in 4-8kHz range during voiced segments.
        """
        print("\n[1/6] Detecting sibilance (harsh 's' sounds)...")

        # Compute spectrogram
        S = np.abs(librosa.stft(self.y, n_fft=self.frame_length, hop_length=self.hop_length))
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.frame_length)

        # Sibilance frequency bands
        sib_low = 4000
        sib_high = 8000
        sib_mask = (freqs >= sib_low) & (freqs <= sib_high)

        # Voice frequency band (for comparison)
        voice_mask = (freqs >= 100) & (freqs < 3000)

        sib_energy = np.sum(S[sib_mask, :], axis=0)
        voice_energy = np.sum(S[voice_mask, :], axis=0)

        # Sibilance ratio - when sibilant energy dominates voice energy
        sib_ratio = sib_energy / (voice_energy + 1e-10)

        # Establish baseline from voiced regions
        # Use median to avoid outliers
        baseline_sib = np.median(sib_ratio[sib_ratio > 0.01])

        # Detect frames where sibilance is excessive
        # Threshold: 2.5x baseline (sensitive)
        sib_threshold = baseline_sib * 2.5
        sib_frames = np.where(sib_ratio > sib_threshold)[0]

        sibilance_issues = []
        if len(sib_frames) > 0:
            # Cluster into regions
            regions = []
            start = sib_frames[0]
            for i in range(1, len(sib_frames)):
                if sib_frames[i] - sib_frames[i-1] > 3:  # Gap of 3 frames
                    # Minimum 2 frames duration (very sensitive)
                    if sib_frames[i-1] - start >= 2:
                        regions.append((start, sib_frames[i-1]))
                    start = sib_frames[i]

            if len(sib_frames) > 0 and sib_frames[-1] - start >= 2:
                regions.append((start, sib_frames[-1]))

            for start, end in regions[:30]:  # Limit to 30
                t_start = librosa.frames_to_time(start, sr=self.sr, hop_length=self.hop_length)
                t_end = librosa.frames_to_time(end, sr=self.sr, hop_length=self.hop_length)

                intensity = np.mean(sib_ratio[start:end]) / baseline_sib
                severity = 'HIGH' if intensity > 4 else 'MEDIUM'

                sibilance_issues.append({
                    'type': 'SIBILANCE',
                    'time': t_start,
                    'severity': severity,
                    'description': f"Harsh 's' sound at {self.format_time(t_start)} (intensity={intensity:.1f}x baseline)",
                    'intensity': intensity
                })

        print(f"   Found {len(sibilance_issues)} sibilance issues")
        self.issues.extend(sibilance_issues)
        return sibilance_issues

    def detect_clicks_glitches(self):
        """
        Detect clicks, pops, and glitches.
        These show as sudden transients - rapid amplitude changes.
        """
        print("\n[2/6] Detecting clicks and glitches...")

        # Method 1: First derivative (rate of change)
        diff = np.abs(np.diff(self.y))

        # Method 2: Local variance in small windows
        window = 64
        local_var = np.array([np.var(self.y[max(0,i-window):i+window])
                              for i in range(0, len(self.y), window)])

        # Establish baseline
        baseline_diff = np.percentile(diff, 95)  # 95th percentile
        baseline_var = np.median(local_var)

        # Detect sudden spikes - threshold 5x baseline (very sensitive)
        click_threshold = baseline_diff * 5
        click_samples = np.where(diff > click_threshold)[0]

        # Also check for sudden variance changes
        var_threshold = baseline_var * 8
        var_spikes = np.where(local_var > var_threshold)[0] * window

        # Combine detections
        all_clicks = set()
        for s in click_samples:
            all_clicks.add(s // self.sr)  # Convert to seconds
        for s in var_spikes:
            all_clicks.add(int(s // self.sr))

        click_issues = []
        for t in sorted(all_clicks)[:20]:  # Limit to 20
            # Verify it's a real click by checking surrounding context
            start_sample = max(0, int(t * self.sr - 1000))
            end_sample = min(len(self.y), int(t * self.sr + 1000))

            local_max = np.max(np.abs(self.y[start_sample:end_sample]))
            local_mean = np.mean(np.abs(self.y[start_sample:end_sample]))

            # Click shows as spike relative to local context
            if local_max > local_mean * 4:
                intensity = local_max / local_mean
                severity = 'HIGH' if intensity > 8 else 'MEDIUM'

                click_issues.append({
                    'type': 'CLICK_GLITCH',
                    'time': float(t),
                    'severity': severity,
                    'description': f"Click/glitch detected at {self.format_time(t)} (spike={intensity:.1f}x local)",
                    'intensity': intensity
                })

        # Deduplicate within 1 second
        filtered = []
        last_time = -2
        for c in click_issues:
            if c['time'] - last_time >= 1:
                filtered.append(c)
                last_time = c['time']

        print(f"   Found {len(filtered)} click/glitch issues")
        self.issues.extend(filtered)
        return filtered

    def detect_audio_dropouts(self):
        """
        Detect audio dropouts by analyzing silence patterns.

        Expected intentional silences: 3, 4, 5, 6, 7, 8, 10, 15 seconds
        Anything else is suspicious.
        """
        print("\n[3/7] Detecting audio dropouts...")

        # Get RMS energy
        frame_length = 2048
        hop = 512
        rms = librosa.feature.rms(y=self.y, frame_length=frame_length, hop_length=hop)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        times = librosa.frames_to_time(np.arange(len(rms_db)), sr=self.sr, hop_length=hop)

        # Silence threshold: -35dB (fairly strict)
        silence_threshold = -35
        silent_frames = rms_db < silence_threshold

        # Find silence regions
        silence_regions = []
        in_silence = False
        start_time = 0

        for i, is_silent in enumerate(silent_frames):
            if is_silent and not in_silence:
                in_silence = True
                start_time = times[i]
            elif not is_silent and in_silence:
                in_silence = False
                duration = times[i] - start_time
                silence_regions.append((start_time, times[i], duration))

        # Expected silence durations (with tolerance)
        expected_silences = [3, 4, 5, 6, 7, 8, 10, 15]
        tolerance = 0.8  # seconds

        dropout_issues = []

        for start, end, duration in silence_regions:
            # Skip very short gaps (< 0.5s) - these are natural speech pauses
            if duration < 0.5:
                continue

            # Skip the very beginning
            if start < 0.5:
                continue

            # Check if this silence matches an expected duration
            matches_expected = False
            for exp in expected_silences:
                if abs(duration - exp) < tolerance:
                    matches_expected = True
                    break

            # Also allow silences slightly shorter than expected (TTS might trim)
            for exp in expected_silences:
                if exp - 1.5 < duration < exp + 0.5:
                    matches_expected = True
                    break

            if not matches_expected:
                # This silence doesn't match any expected pattern
                # Only flag the "gray zone": 1.8-2.8s
                # Shorter could be natural speech pause, longer matches intentional 3s
                if 1.8 < duration < 2.8:
                    dropout_issues.append({
                        'type': 'UNEXPECTED_SILENCE',
                        'time': start,
                        'severity': 'CRITICAL',
                        'description': f"Unexpected {duration:.1f}s silence at {self.format_time(start)} (not a speech pause, not an intentional 3s+ gap)",
                        'duration': duration
                    })

        print(f"   Found {len(dropout_issues)} dropout/gap issues")
        self.issues.extend(dropout_issues)
        return dropout_issues

    def detect_segment_issues(self):
        """
        If manifest is available, check for segment timing anomalies.
        """
        if not self.manifest:
            print("\n[4/8] Segment analysis: No manifest available (skipped)")
            return []

        print("\n[4/8] Analyzing segment timings from manifest...")

        segment_issues = []
        segments = self.manifest.get('segments', [])

        for seg in segments:
            if seg.get('type') != 'text':
                continue

            duration = seg.get('duration', 0)
            expected = seg.get('expected_duration', 0)
            start_time = seg.get('start_time', 0)
            text = seg.get('text', '')[:40]

            # Check if duration is way off from expected
            if expected > 0:
                ratio = duration / expected
                if ratio < 0.5:
                    segment_issues.append({
                        'type': 'SEGMENT_TOO_SHORT',
                        'time': start_time,
                        'severity': 'HIGH',
                        'description': f"Segment at {self.format_time(start_time)} is {duration:.1f}s (expected ~{expected:.1f}s): \"{text}...\"",
                        'ratio': ratio
                    })
                elif ratio > 1.8:
                    segment_issues.append({
                        'type': 'SEGMENT_TOO_LONG',
                        'time': start_time,
                        'severity': 'MEDIUM',
                        'description': f"Segment at {self.format_time(start_time)} is {duration:.1f}s (expected ~{expected:.1f}s): \"{text}...\"",
                        'ratio': ratio
                    })

        print(f"   Found {len(segment_issues)} segment timing issues")
        self.issues.extend(segment_issues)
        return segment_issues

    def detect_tempo_variations(self):
        """
        Detect tempo/speed variations within speech.
        TTS sometimes speeds up on certain words - this catches that.
        """
        print("\n[5/8] Detecting tempo variations...")

        # Use onset detection to find speech rhythm
        onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr, hop_length=self.hop_length)

        # Get tempo estimate for each segment using sliding window
        window_size = int(10 * self.sr / self.hop_length)  # 10 second windows
        hop = int(2 * self.sr / self.hop_length)  # 2 second hop

        tempos = []
        times = []

        for i in range(0, len(onset_env) - window_size, hop):
            window = onset_env[i:i + window_size]
            # Estimate local tempo
            tempo = librosa.feature.tempo(onset_envelope=window, sr=self.sr, hop_length=self.hop_length)
            if len(tempo) > 0:
                tempos.append(tempo[0])
                time = librosa.frames_to_time(i + window_size // 2, sr=self.sr, hop_length=self.hop_length)
                times.append(time)

        if len(tempos) < 3:
            print("   Not enough data for tempo analysis")
            return []

        tempos = np.array(tempos)
        times = np.array(times)

        # Calculate baseline tempo (median of first 60 seconds)
        early_mask = times < 60
        if np.sum(early_mask) > 0:
            baseline_tempo = np.median(tempos[early_mask])
        else:
            baseline_tempo = np.median(tempos)

        # Find segments where tempo deviates significantly
        # Meditation audio has natural tempo variation - use higher thresholds
        # BPM-based detection is imprecise for speech - only flag egregious cases
        # 40% faster threshold catches truly rushed phrases (e.g., closing "thank you")
        tempo_issues = []

        for i, (t, tempo) in enumerate(zip(times, tempos)):
            if tempo > baseline_tempo * 1.40:  # 40% faster than baseline
                # Check it's not already flagged nearby
                if not tempo_issues or t - tempo_issues[-1]['time'] > 10:
                    tempo_issues.append({
                        'type': 'TEMPO_SPEEDUP',
                        'time': t,
                        'severity': 'LOW',  # Experimental - BPM not reliable for speech
                        'description': f"[EXPERIMENTAL] Speech may speed up at {self.format_time(t)} ({tempo:.0f} vs baseline {baseline_tempo:.0f} BPM)",
                        'tempo': tempo,
                        'baseline': baseline_tempo
                    })
            elif tempo < baseline_tempo * 0.55:  # 45% slower than baseline
                if not tempo_issues or t - tempo_issues[-1]['time'] > 10:
                    tempo_issues.append({
                        'type': 'TEMPO_SLOWDOWN',
                        'time': t,
                        'severity': 'LOW',
                        'description': f"Speech slows down at {self.format_time(t)} ({tempo:.0f} vs baseline {baseline_tempo:.0f} BPM, {((tempo/baseline_tempo)-1)*100:.0f}%)",
                        'tempo': tempo,
                        'baseline': baseline_tempo
                    })

        print(f"   Baseline tempo: {baseline_tempo:.0f} BPM")
        print(f"   Found {len(tempo_issues)} tempo variation issues")
        self.issues.extend(tempo_issues)
        return tempo_issues

    def detect_voice_blocks(self):
        """Segment audio into voiced blocks"""
        print("\n[6/9] Segmenting into voice blocks...")

        intervals = librosa.effects.split(
            self.y, top_db=25,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )

        blocks = []
        for start_sample, end_sample in intervals:
            start_time = start_sample / self.sr
            end_time = end_sample / self.sr
            duration = end_time - start_time

            if duration > 0.5:
                blocks.append({
                    'start': start_time,
                    'end': end_time,
                    'duration': duration,
                    'start_sample': start_sample,
                    'end_sample': end_sample
                })

        print(f"   Found {len(blocks)} voice blocks")
        return blocks

    def extract_voice_features(self, block):
        """Extract voice features for comparison"""
        y_block = self.y[block['start_sample']:block['end_sample']]

        # MFCCs - voice fingerprint
        mfccs = librosa.feature.mfcc(y=y_block, sr=self.sr, n_mfcc=20, hop_length=self.hop_length)
        mfcc_mean = np.mean(mfccs, axis=1)

        # Pitch
        f0, _, _ = librosa.pyin(
            y_block, fmin=50, fmax=300, sr=self.sr,
            frame_length=self.frame_length, hop_length=self.hop_length
        )
        valid_f0 = f0[~np.isnan(f0)]
        pitch_mean = np.mean(valid_f0) if len(valid_f0) > 0 else 0

        # Spectral centroid (brightness)
        centroid = librosa.feature.spectral_centroid(y=y_block, sr=self.sr, hop_length=self.hop_length)[0]
        brightness_mean = np.mean(centroid)

        return {
            'pitch_mean': pitch_mean,
            'mfcc_mean': mfcc_mean,
            'brightness_mean': brightness_mean,
        }

    def establish_baseline_voice(self, blocks):
        """Establish baseline voice from first 60 seconds"""
        print("\n[7/9] Establishing baseline voice...")

        baseline_blocks = [b for b in blocks if b['end'] <= 60]
        if len(baseline_blocks) < 3:
            baseline_blocks = blocks[:min(5, len(blocks))]

        print(f"   Using {len(baseline_blocks)} blocks for baseline")

        baseline_features = []
        for block in baseline_blocks:
            feat = self.extract_voice_features(block)
            baseline_features.append(feat)

        self.baseline_voice = {
            'pitch_mean': np.mean([f['pitch_mean'] for f in baseline_features if f['pitch_mean'] > 0]),
            'mfcc_mean': np.mean([f['mfcc_mean'] for f in baseline_features], axis=0),
            'brightness_mean': np.mean([f['brightness_mean'] for f in baseline_features]),
        }

        print(f"   Baseline pitch: {self.baseline_voice['pitch_mean']:.1f}Hz")
        return self.baseline_voice

    def detect_voice_changes(self, blocks):
        """Detect voice changes from baseline - STRICTER thresholds"""
        print("\n[8/9] Detecting voice changes...")

        if not self.baseline_voice or len(blocks) < 2:
            return []

        voice_changes = []

        for i, block in enumerate(blocks):
            if block['end'] <= 60 and i < 5:
                continue

            feat = self.extract_voice_features(block)
            if feat['pitch_mean'] == 0:
                continue

            # MFCC distance - PRIMARY metric (threshold 0.25, stricter than v3's 0.35)
            mfcc_distance = cosine(feat['mfcc_mean'], self.baseline_voice['mfcc_mean'])

            # Pitch difference
            pitch_diff = abs(feat['pitch_mean'] - self.baseline_voice['pitch_mean'])

            # STRICTER thresholds
            if mfcc_distance > 0.25 or pitch_diff > 20:
                severity = 'CRITICAL' if mfcc_distance > 0.4 else 'HIGH'

                voice_changes.append({
                    'type': 'VOICE_CHANGE',
                    'time': block['start'],
                    'severity': severity,
                    'description': f"Voice differs at {self.format_time(block['start'])} (MFCC={mfcc_distance:.3f}, pitch diff={pitch_diff:.1f}Hz)",
                    'mfcc_distance': mfcc_distance,
                    'pitch_diff': pitch_diff
                })

        # Deduplicate - keep first in 20-second windows
        filtered = []
        last_time = -20
        for vc in voice_changes:
            if vc['time'] - last_time >= 20:
                filtered.append(vc)
                last_time = vc['time']

        print(f"   Found {len(filtered)} voice change issues")
        self.issues.extend(filtered)
        return filtered

    def detect_hissing(self):
        """Detect sustained high-frequency hissing"""
        print("\n[9/9] Detecting hissing artifacts...")

        S = np.abs(librosa.stft(self.y, n_fft=self.frame_length, hop_length=self.hop_length))
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.frame_length)

        # High frequency (6-10kHz for hiss)
        hf_mask = (freqs >= 6000) & (freqs <= 10000)
        lf_mask = (freqs >= 100) & (freqs < 4000)

        hf_energy = np.sum(S[hf_mask, :], axis=0)
        lf_energy = np.sum(S[lf_mask, :], axis=0)

        hf_ratio = hf_energy / (lf_energy + 1e-10)

        # Baseline from first 30 seconds
        baseline_frames = int(30 * self.sr / self.hop_length)
        baseline_hf = np.percentile(hf_ratio[:baseline_frames], 75)

        # Threshold 2.5x baseline (more sensitive than v3's 3x)
        hiss_threshold = baseline_hf * 2.5
        hiss_frames = np.where(hf_ratio > hiss_threshold)[0]

        hiss_issues = []
        if len(hiss_frames) > 0:
            regions = []
            start = hiss_frames[0]
            for i in range(1, len(hiss_frames)):
                if hiss_frames[i] - hiss_frames[i-1] > 5:
                    if hiss_frames[i-1] - start > 15:  # ~0.3s minimum
                        regions.append((start, hiss_frames[i-1]))
                    start = hiss_frames[i]

            if len(hiss_frames) > 0 and hiss_frames[-1] - start > 15:
                regions.append((start, hiss_frames[-1]))

            for start, end in regions[:15]:
                t_start = librosa.frames_to_time(start, sr=self.sr, hop_length=self.hop_length)
                t_end = librosa.frames_to_time(end, sr=self.sr, hop_length=self.hop_length)

                intensity = np.mean(hf_ratio[start:end]) / baseline_hf
                severity = 'HIGH' if intensity > 3.5 else 'MEDIUM'

                hiss_issues.append({
                    'type': 'HISSING',
                    'time': t_start,
                    'severity': severity,
                    'description': f"Hissing at {self.format_time(t_start)}-{self.format_time(t_end)} (intensity={intensity:.1f}x)",
                    'intensity': intensity
                })

        print(f"   Found {len(hiss_issues)} hissing regions")
        self.issues.extend(hiss_issues)
        return hiss_issues

    def generate_report(self):
        """Generate report"""
        print("\n" + "="*70)
        print("GENERATING REPORT")
        print("="*70)

        self.issues.sort(key=lambda x: x['time'])

        report_path = os.path.join(self.output_dir, f"{os.path.splitext(self.filename)[0]}_REPORT_v4.txt")

        with open(report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("SALUS AUDIO QUALITY ANALYZER v5 (DROPOUT DETECTION)\n")
            f.write("="*70 + "\n\n")
            f.write(f"File: {self.filename}\n")
            f.write(f"Duration: {self.format_time(self.duration)}\n")
            f.write(f"Analysis: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

            # Summary by type
            type_counts = {}
            severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0}
            for issue in self.issues:
                type_counts[issue['type']] = type_counts.get(issue['type'], 0) + 1
                severity_counts[issue['severity']] = severity_counts.get(issue['severity'], 0) + 1

            f.write("-"*70 + "\n")
            f.write("SUMMARY\n")
            f.write("-"*70 + "\n")
            f.write(f"Total Issues: {len(self.issues)}\n")
            f.write(f"  CRITICAL: {severity_counts['CRITICAL']}\n")
            f.write(f"  HIGH: {severity_counts['HIGH']}\n")
            f.write(f"  MEDIUM: {severity_counts['MEDIUM']}\n\n")

            f.write("By Type:\n")
            for t, count in sorted(type_counts.items()):
                f.write(f"  {t}: {count}\n")

            # Verdict
            f.write("\n" + "-"*70 + "\n")
            f.write("VERDICT\n")
            f.write("-"*70 + "\n")

            if severity_counts['CRITICAL'] > 0:
                f.write("*** CRITICAL FAIL ***\n")
            elif severity_counts['HIGH'] > 0:
                f.write(f"FAIL - {severity_counts['HIGH']} HIGH issues\n")
            elif severity_counts['MEDIUM'] > 0:
                f.write(f"WARNING - {severity_counts['MEDIUM']} MEDIUM issues\n")
            else:
                f.write("PASS\n")

            # All issues
            f.write("\n" + "-"*70 + "\n")
            f.write("ALL ISSUES (by timestamp)\n")
            f.write("-"*70 + "\n\n")

            for i, issue in enumerate(self.issues, 1):
                f.write(f"{i:3d}. [{issue['severity']:8s}] {self.format_time(issue['time'])} {issue['type']}\n")
                f.write(f"     {issue['description']}\n\n")

            if not self.issues:
                f.write("No issues detected.\n")

        print(f"Report saved: {report_path}")

        # Quick summary to stdout
        print("\n" + "="*70)
        print("ISSUES FOUND:")
        print("="*70)
        for issue in self.issues:
            print(f"  {self.format_time(issue['time'])} [{issue['severity']}] {issue['type']}")

        if not self.issues:
            print("  None")

        return report_path

    def run(self):
        """Run full analysis"""
        print("\n" + "="*70)
        print("SALUS AUDIO ANALYZER v5 (DROPOUT DETECTION)")
        print("="*70)
        print("Detects: Audio Dropouts, Sibilance, Clicks, Voice Changes, Hissing")

        self.detect_sibilance()
        self.detect_clicks_glitches()
        self.detect_audio_dropouts()
        self.detect_segment_issues()
        self.detect_tempo_variations()

        blocks = self.detect_voice_blocks()
        self.establish_baseline_voice(blocks)
        self.detect_voice_changes(blocks)
        self.detect_hissing()

        self.generate_report()

        return self.issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_audio_v4.py <audio_file.mp3> [output_dir]")
        sys.exit(1)

    audio_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(audio_path):
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)

    analyzer = AudioQualityAnalyzerV5(audio_path, output_dir)
    analyzer.run()


if __name__ == "__main__":
    main()
