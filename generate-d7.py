#!/usr/bin/env python3
"""Generate D7 Auphonic Correlation Report from cached results."""

import json
import numpy as np
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path('/Users/scottripley/salus-website/reference/echo-training')

with open(OUTPUT_DIR / 'auphonic_results.json') as f:
    data = json.load(f)

df = pd.DataFrame(data)
df['is_echo'] = df['verdict'].isin(['ECHO']).astype(int)

has_data = df['noise_level'].notna()
analysis_df = df[has_data].copy()

# Save CSV
analysis_df.to_csv(OUTPUT_DIR / 'auphonic_correlation.csv', index=False)

# Core: ECHO vs OK only
core = analysis_df[analysis_df['verdict'].isin(['ECHO', 'OK'])]
core_echo = core[core['verdict'] == 'ECHO']
core_clean = core[core['verdict'] == 'OK']

metrics = ['noise_level', 'signal_level', 'snr', 'loudness', 'lra',
           'speech_loudness', 'speech_lra', 'speech_percentage', 'max_momentary', 'max_shortterm']

lines = []
lines.append('# Deliverable D7: Auphonic Correlation Report')
lines.append('')
lines.append(f'**Date:** {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}')
lines.append('**Brief:** brief-echo-detection.md (ACTIVE)')
lines.append('**Question:** Does Auphonic catch what human ears catch?')
lines.append('')
lines.append('---')
lines.append('')
lines.append('## 1. Dataset')
lines.append('')
lines.append(f'- **Chunks submitted:** {len(df)}')
lines.append(f'- **With Auphonic data:** {has_data.sum()} (credits ran out after this)')
lines.append(f'- **Remaining:** {(~has_data).sum()} chunks unanalysed')
lines.append(f'- **ECHO (human verdict):** {len(core_echo)}')
lines.append(f'- **OK (human verdict):** {len(core_clean)}')
lines.append(f'- **Other (HISS/VOICE/BAD):** {len(analysis_df) - len(core_echo) - len(core_clean)}')
lines.append('')
lines.append('---')
lines.append('')
lines.append('## 2. Per-Chunk Results')
lines.append('')
lines.append('| Session | Chunk | Verdict | Noise (dB) | Signal (dB) | SNR (dB) | Loudness (LUFS) | LRA (LU) |')
lines.append('|---------|-------|---------|------------|-------------|----------|-----------------|----------|')

for _, row in analysis_df.iterrows():
    v = row['verdict']
    marker = ' **' if v == 'ECHO' else ''
    lines.append(
        f'| {row["session"]} | {row["chunk"]} | {v}{marker} | '
        f'{row["noise_level"]:.1f} | {row["signal_level"]:.1f} | {row["snr"]:.1f} | '
        f'{row["loudness"]:.1f} | {row["lra"]:.2f} |'
    )

lines.append('')
lines.append('---')
lines.append('')
lines.append('## 3. Statistical Comparison: ECHO vs OK')
lines.append('')
lines.append(f'Analysis restricted to ECHO ({len(core_echo)}) vs OK ({len(core_clean)}) chunks only.')
lines.append('')
lines.append('| Metric | ECHO mean | ECHO std | OK mean | OK std | Cohen d | Direction |')
lines.append('|--------|-----------|----------|---------|--------|---------|-----------|')

separation = {}
for m in metrics:
    e_vals = core_echo[m].dropna()
    c_vals = core_clean[m].dropna()
    if len(e_vals) == 0 or len(c_vals) == 0:
        continue
    e_mean, e_std = e_vals.mean(), e_vals.std()
    c_mean, c_std = c_vals.mean(), c_vals.std()
    pooled = np.sqrt((e_std**2 + c_std**2) / 2) if (e_std + c_std) > 0 else 1
    d = (e_mean - c_mean) / pooled
    separation[m] = d

    if abs(d) < 0.2:
        direction = 'negligible'
    elif d > 0:
        direction = 'ECHO higher'
    else:
        direction = 'ECHO lower'

    lines.append(f'| {m} | {e_mean:.2f} | {e_std:.2f} | {c_mean:.2f} | {c_std:.2f} | {d:+.3f} | {direction} |')

best_metric = max(separation, key=lambda k: abs(separation[k]))
best_d = abs(separation[best_metric])

lines.append('')
lines.append('---')
lines.append('')
lines.append('## 4. Does Auphonic Catch Echo?')
lines.append('')

if best_d >= 0.8:
    conclusion = 'YES -- strong separation'
elif best_d >= 0.5:
    conclusion = 'MODERATE -- some separation, not reliable alone'
elif best_d >= 0.2:
    conclusion = 'WEAK -- marginal separation'
else:
    conclusion = 'NO -- no meaningful separation'

lines.append(f'### Answer: {conclusion}')
lines.append('')
lines.append(f'Best discriminating metric: **`{best_metric}`** (|d| = {best_d:.2f})')
lines.append('')

lines.append('### Key Finding')
lines.append('')
lines.append('ECHO chunks are **quieter** than OK chunks across all level metrics:')
lines.append(f'- Signal level: ECHO = {core_echo["signal_level"].mean():.1f} dB vs OK = {core_clean["signal_level"].mean():.1f} dB')
lines.append(f'- Loudness: ECHO = {core_echo["loudness"].mean():.1f} LUFS vs OK = {core_clean["loudness"].mean():.1f} LUFS')
lines.append(f'- Noise floor: ECHO = {core_echo["noise_level"].mean():.1f} dB vs OK = {core_clean["noise_level"].mean():.1f} dB (ECHO has *lower* noise)')
lines.append(f'- SNR: ECHO = {core_echo["snr"].mean():.1f} dB vs OK = {core_clean["snr"].mean():.1f} dB (ECHO has *higher* SNR)')
lines.append('')
lines.append('This is counterintuitive. If echo were adding noise, we would expect higher noise and lower SNR.')
lines.append('Instead, echo chunks are quieter overall with cleaner noise floors.')
lines.append('')
lines.append('**Interpretation:** Fish TTS echo is not additive reverb. It is a generative distortion')
lines.append('where the model produces a smeared, lower-energy output. Auphonic sees this as a')
lines.append('quieter, cleaner signal -- the opposite of what echo detection would flag.')
lines.append('')

# Threshold analysis
lines.append('### Threshold Analysis')
lines.append('')
lines.append(f'Using `{best_metric}` (strongest separator, d={separation[best_metric]:+.2f}):')
lines.append('')

d_sign = 1 if separation[best_metric] > 0 else -1
echo_vals = core_echo[best_metric].dropna()
clean_vals = core_clean[best_metric].dropna()
all_vals = pd.concat([echo_vals, clean_vals])

for pct in [10, 20, 30, 40, 50]:
    if d_sign > 0:
        threshold = np.percentile(all_vals, 100 - pct)
        flagged_e = int((echo_vals > threshold).sum())
        flagged_c = int((clean_vals > threshold).sum())
    else:
        threshold = np.percentile(all_vals, pct)
        flagged_e = int((echo_vals < threshold).sum())
        flagged_c = int((clean_vals < threshold).sum())

    recall = flagged_e / max(len(echo_vals), 1)
    prec = flagged_e / max(flagged_e + flagged_c, 1)
    lines.append(
        f'- Flag {"top" if d_sign > 0 else "bottom"} {pct}%: catches '
        f'**{flagged_e}/{len(echo_vals)} echo** '
        f'({recall:.0%} recall), {flagged_c} false positives (precision {prec:.0%})'
    )

lines.append('')
lines.append('---')
lines.append('')
lines.append('## 5. Comparison: All Detectors vs Human')
lines.append('')
lines.append('| Detector | Approach | Catches Echo? | Notes |')
lines.append('|----------|----------|---------------|-------|')
lines.append('| Composite scorer | Spectral flux/contrast/flatness | NO (58% FNR) | Anti-correlated with echo |')
lines.append('| Local DSP (echo-detector.py) | Autocorrelation + cepstral + decay | NO (67% FNR) | Classical echo features miss TTS artifacts |')
lines.append(f'| Auphonic (`{best_metric}`) | Commercial audio analysis | WEAK (|d|={best_d:.2f}) | Echo chunks are quieter, not noisier |')
lines.append('| Human review (Scott) | Ears + AirPods at volume | YES (0% FNR) | Ground truth |')
lines.append('')
lines.append('---')
lines.append('')
lines.append('## 6. Conclusion')
lines.append('')

if best_d >= 0.5:
    lines.append(f'**Auphonic shows moderate signal** (|d|={best_d:.2f} on `{best_metric}`).')
    lines.append('')
    lines.append('This is not strong enough for standalone detection, but could contribute as')
    lines.append('one feature in a multi-signal detector. Worth buying more credits to analyse')
    lines.append('the remaining chunks and validate whether this holds.')
else:
    lines.append('**Auphonic does not reliably detect Fish Audio echo.**')
    lines.append('')
    lines.append('No Auphonic metric achieves strong separation between ECHO and CLEAN chunks.')

lines.append('')
lines.append('The fundamental problem: Fish echo is a **generative artifact**, not acoustic reverb.')
lines.append('All three approaches (composite scorer, classical DSP, Auphonic) measure acoustic')
lines.append('properties of the output signal. But the defect originates in the TTS model itself --')
lines.append("it produces distorted output that sounds like echo but doesn't have echo's acoustic signature.")
lines.append('')
lines.append('### Paths Forward')
lines.append('')
lines.append('1. **More labelled data** -- 5 ECHO chunks is too few for reliable statistics. 50+ ECHO')
lines.append('   examples across 5+ sessions would narrow confidence intervals and reveal patterns')
lines.append('2. **Mel spectrogram CNN** -- let a neural network learn the pattern from spectrograms')
lines.append('   (needs ~200 labelled chunks minimum)')
lines.append('3. **Whisper confidence** -- echo may reduce ASR confidence, providing an indirect signal')
lines.append('4. **Per-word forced alignment** -- since echo clusters on specific words, word-level')
lines.append('   analysis with the known trigger word list could isolate affected regions')
lines.append('5. **Combination approach** -- Auphonic signal_level + local C50 + MFCC delta features')
lines.append('   together may reach viable accuracy with enough data')
lines.append('')
lines.append('---')
lines.append('')
lines.append('**END OF REPORT**')

report_path = OUTPUT_DIR / 'D7-auphonic-correlation-report.md'
with open(report_path, 'w') as f:
    f.write('\n'.join(lines))

print(f'D7 report: {report_path}')
print(f'CSV: {OUTPUT_DIR / "auphonic_correlation.csv"} ({len(analysis_df)} rows)')
print(f'\nSummary:')
print(f'  Best Auphonic metric: {best_metric} (|d| = {best_d:.2f})')
print(f'  Conclusion: {conclusion}')
