# SoundTouch & Telegram Voice Tuning Lab

This folder contains the complete testing suite to process any MP3 voice recording through **10 distinct variations** of SoundTouch and Telegram DSP settings, all locked to **-2.3 semitones**.

---

## Quick Start (How to Use)

### Option 1: Drag and Drop (Easiest)
1. Drag and drop any `.mp3` file onto `run_test.bat`.
2. The script will automatically process the audio and generate 10 MP3s in the `output/` folder.
3. It will automatically open the interactive comparison player in your browser (`output/compare_player.html`).

### Option 2: Command Line
Open a terminal in this directory and run:
```bash
python test_variations.py "path/to/your/audio.mp3"
```

---

## What Gets Generated in `output/`

You will get:
1. **10 High-Quality MP3s (320 kbps)**:
   - `01_Studio_Speech_Pure.mp3`: Pure Studio Speech (Full Precision WSOLA, Anti-Alias ON, Clean Uncolored Voice)
   - `02_Radio_Broadcaster_EQ.mp3`: Telegram Radio Broadcaster Preset (+4dB @ 125Hz, +2.5dB Air @ 9kHz, Boxiness cut)
   - `03_Warm_Velvet_Podcast.mp3`: Warm Velvet / Podcast Preset (+2.8dB @ 140Hz, Gentle Highs @ 8.5kHz, Low Cut 70Hz)
   - `04_Studio_Crystal_Clarity.mp3`: Studio Crystal Preset (+3.5dB High Air @ 10kHz, Tight Lows @ 110Hz, Deep Mud Cut)
   - `05_Cinematic_Deep_Resonance.mp3`: Cinematic Deep Preset (+5dB Heavy Sub-Warmth @ 95Hz, Low HPF 60Hz)
   - `06_Broadcast_Tube_Saturation.mp3`: Radio Broadcaster EQ + Broadcast Soft-Knee Compressor & Analog Triode Tube Saturation
   - `07_Extended_Sequence_Smooth.mp3`: Extended Sequence Window (Sequence: 60ms, Seek: 20ms, Overlap: 12ms)
   - `08_Short_Sequence_Fast_Speech.mp3`: Short Sequence Window (Sequence: 28ms, Seek: 12ms, Overlap: 6ms)
   - `09_QuickSeek_Comparison.mp3`: QuickSeek Algorithm Enabled (Coarse Correlation vs Full Precision)
   - `10_Raw_AntiAlias_Bypass.mp3`: Anti-Aliasing Filter Bypassed (Raw Highs, AA Filter = 0)

2. **`compare_player.html`**:
   - An interactive web audio player you can open in Chrome, Edge, or Safari.
   - Allows instant A/B switching between any of the 10 tracks at the exact same playhead timestamp.

3. **`VARIATIONS_GUIDE.md` & `VARIATIONS_GUIDE.txt`**:
   - A complete reference guide showing which file belongs to which parameter combination and what sonic characteristics to listen for.
