# SoundTouch Pure Speech Tuning Lab

This lab processes any MP3 voice note through **10 pure SoundTouch variations**, all shifted to **-2.3 semitones**.

**NO EQ. NO COMPRESSOR. PURE SOUNDTOUCH PARAMETERS ONLY.**

---

## Quick Start

### Drag & Drop
1. Drag and drop your voice `.mp3` file directly onto **`run_test.bat`**.
2. It will process all 10 tracks into the `output/` folder and launch the interactive comparison player.

### Command Line
```bash
python test_variations.py "path/to/your/voice.mp3"
```

---

## The 10 Pure Speech Variations (-2.3 Semitones)

| Track | File Name | Sequence | Seek | Overlap | QuickSeek | Anti-Alias | What It Does |
|---|---|---|---|---|---|---|---|
| **01** | `01_Standard_Speech_Baseline.mp3` | `40ms` | `15ms` | `8ms` | `OFF (0)` | `ON (64t)` | Official speech baseline. Natural balance of vowels and consonants. |
| **02** | `02_Deep_Male_Voice_Optimized.mp3` | `48ms` | `20ms` | `10ms` | `OFF (0)` | `ON (64t)` | **Deep Chest Resonance**: Extended seek window (20ms) tracks low male fundamental frequencies (85-110 Hz) with zero phase cancellation. |
| **03** | `03_Ultra_Smooth_Vowels.mp3` | `56ms` | `18ms` | `12ms` | `OFF (0)` | `ON (64t)` | **Vowel Stability**: Long sequence (56ms) + wide overlap (12ms). Completely eliminates vowel flutter or buzz. |
| **04** | `04_Crisp_Fast_Consonants.mp3` | `28ms` | `12ms` | `6ms` | `OFF (0)` | `ON (32t)` | **Plosives & Articulation**: Fast 28ms slices preserve crisp consonants ('p', 't', 'k', 's') without blurring. |
| **05** | `05_Natural_Conversational.mp3` | `35ms` | `14ms` | `8ms` | `OFF (0)` | `ON (48t)` | **Conversational Cadence**: Snappy 35ms cycles tuned for natural Telegram voice message cadence. |
| **06** | `06_High_Precision_AntiAlias_128.mp3` | `40ms` | `15ms` | `8ms` | `OFF (0)` | `ON (128t)` | **Silky Highs**: Max 128-tap FIR anti-alias filter. Completely purges spectral reflection artifacts. |
| **07** | `07_Raw_AntiAlias_Bypass.mp3` | `40ms` | `15ms` | `8ms` | `OFF (0)` | `OFF (0)` | **Raw Edge**: Anti-aliasing completely off. Preserves raw unfiltered vocal breath and crisp edge. |
| **08** | `08_Wide_Overlap_Air.mp3` | `44ms` | `16ms` | `14ms` | `OFF (0)` | `ON (64t)` | **Soft Acoustic Blend**: Extended 14ms crossfade overlap deeply blends slice boundaries for a mellow tone. |
| **09** | `09_Punchy_Transient_Short_Overlap.mp3` | `38ms` | `15ms` | `5ms` | `OFF (0)` | `ON (32t)` | **Dry Punch**: Short 5ms crossfade. Gives dry, punchy attack with immediate acoustic transients. |
| **10** | `10_QuickSeek_Coarse_Comparison.mp3` | `40ms` | `15ms` | `8ms` | `ON (1)` | `ON (64t)` | **QuickSeek Comparison**: Enables coarse search approximation. Compare directly against Track 01. |
