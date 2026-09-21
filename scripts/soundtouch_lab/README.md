# SoundTouch Pure Speech Tuning Lab: Categorized Parameter Suite

This lab takes your voice recording and generates **43 systematic SoundTouch variations**, grouped into **5 distinct categories**, with each parameter ordered strictly from **lowest to highest** at a constant **-2.3 semitones**.

**NO EQ. NO COMPRESSOR. PURE SOUNDTOUCH DSP PARAMETERS ONLY.**

---

## Quick Start (Beginner Friendly)

### Method 1: Double Click (Simplest)
1. Place your voice recording inside this folder (`scripts\soundtouch_lab`) and name it `voice.mp3`.
2. Double-click **`run_test.bat`**.
3. It generates all 43 tracks across 5 subfolders and automatically pops open the interactive comparison player (`compare_player.html`) in your browser.

### Method 2: Drag & Drop
1. Drag and drop any voice `.mp3` directly onto **`run_test.bat`**.

### Method 3: Command Line
```powershell
python test_variations.py "path/to/your_voice.mp3"
```

---

## The 5 Systematic Categories (All Shifted -2.3 Semitones)

### Category 1: Sequence Duration (`SETTING_SEQUENCE_MS`) — 10 Tracks
*Slice length in milliseconds. Shorter slices preserve fast articulation; longer slices prevent vowel buzz.*
* **Seq_01**: `20 ms` (Lowest safe slice duration)
* **Seq_02**: `25 ms`
* **Seq_03**: `30 ms`
* **Seq_04**: `35 ms`
* **Seq_05**: `40 ms` (Standard SoundTouch Speech Baseline)
* **Seq_06**: `50 ms`
* **Seq_07**: `60 ms` (Smooth vowel continuity)
* **Seq_08**: `70 ms`
* **Seq_09**: `82 ms` (SoundTouch music default)
* **Seq_10**: `100 ms` (Highest slice duration)

### Category 2: Seek Window Length (`SETTING_SEEKWINDOW_MS`) — 10 Tracks
*How far SoundTouch scans for fundamental pitch waves (F0). Deep male voices (85-110 Hz) have longer wavelengths.*
* **Seek_01**: `4 ms` (Lowest search window — notice robotic phasing)
* **Seek_02**: `8 ms`
* **Seek_03**: `10 ms`
* **Seek_04**: `12 ms`
* **Seek_05**: `15 ms` (Standard SoundTouch Speech Baseline)
* **Seek_06**: `18 ms`
* **Seek_07**: `20 ms` (Deep male chest voice optimization)
* **Seek_08**: `24 ms`
* **Seek_09**: `28 ms` (SoundTouch music default)
* **Seek_10**: `35 ms` (Highest search window)

### Category 3: Overlap Duration (`SETTING_OVERLAP_MS`) — 9 Tracks
*Linear crossfade duration between slices. Shorter = punchy transient attack; longer = softer, seamless blend.*
* **Overlap_01**: `2 ms` (Lowest crossfade — razor-sharp attacks)
* **Overlap_02**: `4 ms`
* **Overlap_03**: `6 ms`
* **Overlap_04**: `8 ms` (Standard SoundTouch Speech Baseline)
* **Overlap_05**: `10 ms`
* **Overlap_06**: `12 ms` (SoundTouch music default)
* **Overlap_07**: `14 ms` (Airy, mellow blend)
* **Overlap_08**: `16 ms`
* **Overlap_09**: `18 ms` (Highest crossfade)

### Category 4: QuickSeek Algorithm (`SETTING_USE_QUICKSEEK`) — 6 Tracks
*Direct comparison pairs: Full-Precision Correlation Search (0) vs Coarse Approximation (1).*
* **QS_01** vs **QS_02**: Full Precision vs QuickSeek @ 15ms Seek (Speech Baseline)
* **QS_03** vs **QS_04**: Full Precision vs QuickSeek @ 20ms Seek (Deep Voice)
* **QS_05** vs **QS_06**: Full Precision vs QuickSeek @ 28ms Seek (Music Default)

### Category 5: Anti-Alias Filter & Taps (`SETTING_USE_AA_FILTER` & `LENGTH`) — 8 Tracks
*FIR low-pass filter to reject folded pitch-down aliasing harmonics.*
* **AA_01**: Filter Bypassed / OFF (Raw breath, grit, folded harmonics)
* **AA_02**: 8 Taps (Lowest FIR filter order)
* **AA_03**: 16 Taps
* **AA_04**: 32 Taps (Light mobile filter)
* **AA_05**: 48 Taps
* **AA_06**: 64 Taps (Standard SoundTouch Speech Baseline)
* **AA_07**: 96 Taps
* **AA_08**: 128 Taps (Highest studio brickwall resolution)

---

## Interactive Comparison Player (`compare_player.html`)

Inside `output/`, open `compare_player.html` in your browser:
* **Category Tabs**: Filter by any category or view all 43.
* **Instant A/B Switching**: Click any track or press keys **`1` through `0`** to switch tracks **at the exact same playback millisecond**.
* **Spacebar**: Play / Pause.
* **Arrow Up / Down**: Next / Previous track.
* **Arrow Left / Right**: Seek +/- 2 seconds.
