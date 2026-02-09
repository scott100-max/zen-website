# State: Echo Detection System

Last updated: 9 February 2026 17:15

## Progress

| # | Item | Status | Notes |
|---|------|--------|-------|
| 4-PRE | Fix label pipeline (auto-save + CSV export) | DONE | label-server.py created, all 3 review pages updated |
| 4a | Data preparation | DONE | 55 chunks (12 ECHO, 43 CLEAN) from 2 sessions, deduped across builds |
| 4b | Feature engineering (local) | DONE | 65 echo-specific features (autocorrelation, cepstral, decay, modulation, MFCC, spectral, clarity) |
| 4b-i | Auphonic API integration | DONE | 58 chunks analysed. signal_level |d|=0.55 descriptive but AUC=0.341 predictive (anti-correlated). 1.15 hrs used. |
| 4c | Model training | DONE | Tried RF, GB, LR with LOSO + stratified k-fold CV |
| 4d | Validation | **STOP RULE 2 TRIGGERED** | AUC=0.512 (random), FNR=66.7% (>40% threshold). Model is not learning echo. |
| D1 | Training dataset | DONE | reference/echo-training/echo_features.csv |
| D2 | Echo detector script | DONE | echo-detector.py (functional but model is ineffective) |
| D3 | Validation report | DONE | reference/echo-training/echo_detector_validation_report.md |
| D4 | Baseline comparison | DONE | Neither detector works — both near random for echo |
| D5 | Integration proposal | BLOCKED | Cannot recommend integration of a random classifier |
| D6 | Feature analysis | DONE | See analysis below |
| D7 | Auphonic correlation report | DONE | 58/62 chunks analysed. Auphonic AUC=0.341 (anti-correlated). Does NOT detect echo. Combined model worse than local-only. |

## STOP Condition: Why the Model Failed

**STOP Rule 2 triggered:** FNR=66.7% (>40% threshold), AUC=0.512 (random chance).

### Root Cause Analysis

Fish Audio "echo" is NOT classical acoustic echo. Traditional echo detection features look for:
- Delayed signal copies (autocorrelation peaks at 10-80ms)
- Reverb tails (slow spectral decay after transients)
- Room impulse response characteristics

But Fish's echo is a **TTS generation artifact** — the model hallucinates or smears certain phonemes/words, creating a perceptual effect humans call "echo" but which has no physical delay signature. Evidence:

1. **Autocorrelation features are anti-correlated**: ECHO chunks have LOWER ac_echo_max (0.587) vs CLEAN (0.628). Classical echo would be higher.
2. **Cepstral features show no separation**: Cohen's d = -0.40 (wrong direction) for cep_echo_max.
3. **Best features are generic MFCC/spectral stats** (mfcc_1_std, spectral_bandwidth), not echo-specific. Effect sizes are small (d < 0.6).
4. **C50 clarity index** showed weak positive signal (d=0.57) — the only echo-adjacent feature with correct direction. But too weak alone.

### What might work instead

1. **Auphonic API** — commercial algorithm may detect TTS artifacts differently than classical DSP. Worth testing before giving up.
2. **Mel spectrogram CNN** — a neural network trained directly on spectrograms might learn the visual/auditory pattern that humans perceive as "echo" without relying on hand-crafted features. Needs more data (200+ labelled chunks).
3. **More labelled data** — 12 ECHO examples is very small. Effect sizes may become clearer with 50+ ECHO examples.
4. **Word-level features** — echo often occurs on specific words/phonemes. Cross-referencing the known trigger word list with per-word audio analysis could help.

## Key Results

- **AUC-ROC: 0.512** (random — model learns nothing)
- **FNR at best threshold (0.08): 66.7%** — worse than the composite scorer's 58%
- **LOSO FNR: 100%** — zero cross-session generalisation
- **K-Fold FNR (0.5): 100%** — no within-session learning either
- All three classifiers (RF, GB, LR) failed equally

## Dataset

- 55 labelled chunks (12 ECHO, 43 CLEAN)
- Sessions: 36-loving-kindness-intro-v3a, 52-the-court-of-your-mind
- B1/B2 deduplication: B2 labels supersede B1 for overlapping chunks (same audio)
- Audio: reference/echo-training/audio/

## Next Steps (for Scott's decision)

1. ~~Try Auphonic~~ — DONE. AUC=0.341, makes model worse. Not viable.
2. **Generate more labelled data** — review more sessions, especially noting ECHO chunks. Target: 50+ ECHO examples
3. **Mel spectrogram CNN** — most promising next approach (needs ~200 labelled chunks)
4. **Whisper/ASR confidence** — echo may reduce transcription confidence (cheap to test)
5. **Accept that human review remains the only echo gate** for now

## Issues for Human Review

- STOP rule 2 triggered — model does not detect echo
- Classical DSP echo features are the wrong tool for TTS generation artifacts
- Auphonic integration is the most promising next step
- More labelled data will help regardless of approach
