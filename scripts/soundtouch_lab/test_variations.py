#!/usr/bin/env python3
"""
SoundTouch Pure Speech Tuning Lab: 10 Parameter Variations Tester
Pure SoundTouch algorithmic parameters ONLY.
NO EQ, NO COMPRESSION.
All 10 variations pitch-shifted to -2.3 semitones for human speech & voice notes.
"""

import os
import sys
import argparse
import time
from soundtouch_engine import (
    SoundTouchDLL,
    load_audio_as_pcm,
    save_pcm_as_mp3
)

# 10 Pure SoundTouch Variations Specifically Tuned for Speaking Voice & Voice Notes
VARIATIONS = [
    {
        "id": "01",
        "name": "01_Standard_Speech_Baseline",
        "title": "01: Standard Speech Baseline (Recommended Standard)",
        "description": "Sequence: 40ms | Seek: 15ms | Overlap: 8ms | QuickSeek: OFF | Anti-Alias: ON (64 taps)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 64,
        "listening_notes": "The official SoundTouch speech baseline with full precision. Balanced natural blend of vowels and consonants. Your primary reference track."
    },
    {
        "id": "02",
        "name": "02_Deep_Male_Voice_Optimized",
        "title": "02: Deep Male Voice Optimized",
        "description": "Sequence: 48ms | Seek: 20ms | Overlap: 10ms | QuickSeek: OFF | Anti-Alias: ON (64 taps)",
        "pitch": -2.3,
        "sequence_ms": 48,
        "seekwindow_ms": 20,
        "overlap_ms": 10,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 64,
        "listening_notes": "Tailored for low male fundamental frequencies (85-110 Hz). Longer seek window (20ms) tracks deep chest resonance without phase cancellation or flutter."
    },
    {
        "id": "03",
        "name": "03_Ultra_Smooth_Vowels",
        "title": "03: Ultra Smooth Vowels",
        "description": "Sequence: 56ms | Seek: 18ms | Overlap: 12ms | QuickSeek: OFF | Anti-Alias: ON (64 taps)",
        "pitch": -2.3,
        "sequence_ms": 56,
        "seekwindow_ms": 18,
        "overlap_ms": 12,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 64,
        "listening_notes": "Extended sequence (56ms) and wider overlap (12ms). Completely eliminates any micro-buzz or robotic flutter on sustained vowels (like 'ah', 'oh', 'ee')."
    },
    {
        "id": "04",
        "name": "04_Crisp_Fast_Consonants",
        "title": "04: Crisp Fast Consonants (Snappy Plosives)",
        "description": "Sequence: 28ms | Seek: 12ms | Overlap: 6ms | QuickSeek: OFF | Anti-Alias: ON (32 taps)",
        "pitch": -2.3,
        "sequence_ms": 28,
        "seekwindow_ms": 12,
        "overlap_ms": 6,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 32,
        "listening_notes": "Short 28ms correlation slices. Keeps fast consonants ('p', 't', 'k', 's') razor-sharp with immediate response. Best for fast talkers."
    },
    {
        "id": "05",
        "name": "05_Natural_Conversational",
        "title": "05: Natural Conversational Voice",
        "description": "Sequence: 35ms | Seek: 14ms | Overlap: 8ms | QuickSeek: OFF | Anti-Alias: ON (48 taps)",
        "pitch": -2.3,
        "sequence_ms": 35,
        "seekwindow_ms": 14,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 48,
        "listening_notes": "Slightly tighter sequence (35ms) tuned specifically for everyday voice notes and natural conversational rhythm."
    },
    {
        "id": "06",
        "name": "06_High_Precision_AntiAlias_128",
        "title": "06: High Precision Anti-Alias (128-Tap FIR)",
        "description": "Sequence: 40ms | Seek: 15ms | Overlap: 8ms | QuickSeek: OFF | Anti-Alias: ON (128 taps)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 128,
        "listening_notes": "Maximum 128-tap FIR filter resolution. Eliminates high-frequency spectral foldover, delivering silky smooth top-end clarity."
    },
    {
        "id": "07",
        "name": "07_Raw_AntiAlias_Bypass",
        "title": "07: Raw Anti-Alias Bypass (Unfiltered Highs)",
        "description": "Sequence: 40ms | Seek: 15ms | Overlap: 8ms | QuickSeek: OFF | Anti-Alias: OFF",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 0,
        "aa_filter_length": 0,
        "listening_notes": "Anti-aliasing filter completely bypassed. Preserves raw unfiltered vocal breath, acoustic presence, and crisp edge."
    },
    {
        "id": "08",
        "name": "08_Wide_Overlap_Air",
        "title": "08: Wide Overlap Air (Soft Crossfade)",
        "description": "Sequence: 44ms | Seek: 16ms | Overlap: 14ms | QuickSeek: OFF | Anti-Alias: ON (64 taps)",
        "pitch": -2.3,
        "sequence_ms": 44,
        "seekwindow_ms": 16,
        "overlap_ms": 14,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 64,
        "listening_notes": "Deep 14ms crossfade blending across window boundaries. Gives a softer, mellow spoken tone with zero rough slice edges."
    },
    {
        "id": "09",
        "name": "09_Punchy_Transient_Short_Overlap",
        "title": "09: Punchy Transients (Dry Attack)",
        "description": "Sequence: 38ms | Seek: 15ms | Overlap: 5ms | QuickSeek: OFF | Anti-Alias: ON (32 taps)",
        "pitch": -2.3,
        "sequence_ms": 38,
        "seekwindow_ms": 15,
        "overlap_ms": 5,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 32,
        "listening_notes": "Short 5ms crossfade. Preserves maximum acoustic punch and direct punchy transient impact."
    },
    {
        "id": "10",
        "name": "10_QuickSeek_Coarse_Comparison",
        "title": "10: QuickSeek Coarse Approximation",
        "description": "Sequence: 40ms | Seek: 15ms | Overlap: 8ms | QuickSeek: ON (Decimated) | Anti-Alias: ON",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 1,
        "aa_filter": 1,
        "aa_filter_length": 64,
        "listening_notes": "Enables QuickSeek coarse search approximation. Compare directly against Track 01 to hear how coarse correlation sounds on speech."
    }
]


def generate_html_player(output_dir, base_input_name):
    """
    Generates an interactive A/B comparison HTML player in the output folder.
    """
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SoundTouch Speech Variations Lab - A/B Player</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: #090d16;
        color: #f8fafc;
        margin: 0;
        padding: 24px;
    }}
    .container {{
        max-width: 980px;
        margin: 0 auto;
    }}
    h1 {{
        color: #38bdf8;
        font-size: 28px;
        margin-bottom: 6px;
    }}
    .subtitle {{
        color: #94a3b8;
        font-size: 14.5px;
        margin-bottom: 22px;
    }}
    .highlight {{
        color: #38bdf8;
        font-weight: 600;
    }}
    .global-bar {{
        background: #151f32;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        position: sticky;
        top: 16px;
        z-index: 100;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }}
    .global-bar button {{
        background: #38bdf8;
        color: #090d16;
        font-weight: 700;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.15s;
    }}
    .global-bar button:hover {{
        background: #7dd3fc;
        transform: translateY(-1px);
    }}
    .sync-info {{
        color: #e2e8f0;
        font-size: 14px;
        flex: 1;
    }}
    .card {{
        background: #111a2e;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: border-color 0.2s, background 0.2s;
    }}
    .card:hover {{
        border-color: #38bdf8;
    }}
    .card.active {{
        border-color: #38bdf8;
        background: #142442;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
    }}
    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }}
    .card-title {{
        font-size: 17px;
        font-weight: 700;
        color: #f1f5f9;
    }}
    .badge {{
        background: #0369a1;
        color: #e0f2fe;
        font-size: 12px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
    }}
    .badge.recommended {{
        background: #15803d;
        color: #dcfce7;
    }}
    .card-desc {{
        color: #94a3b8;
        font-size: 13.5px;
        margin-bottom: 10px;
    }}
    .card-notes {{
        color: #cbd5e1;
        font-size: 13px;
        background: #090d16;
        padding: 9px 12px;
        border-radius: 6px;
        margin-bottom: 12px;
        border-left: 3px solid #38bdf8;
    }}
    .params-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 8px;
        margin-bottom: 12px;
        font-size: 12px;
    }}
    .param-item {{
        background: #090d16;
        padding: 6px 10px;
        border-radius: 6px;
        color: #64748b;
    }}
    .param-item strong {{
        color: #cbd5e1;
    }}
    audio {{
        width: 100%;
        outline: none;
        border-radius: 8px;
    }}
</style>
</head>
<body>
<div class="container">
    <h1>SoundTouch Speech Variations Lab</h1>
    <div class="subtitle">Comparing 10 Pure SoundTouch Speech Variations from <span class="highlight">{base_input_name}</span> | Fixed Pitch: <span class="highlight">-2.3 Semitones</span> (NO EQ, NO Compression)</div>

    <div class="global-bar">
        <button onclick="stopAll()">Stop All</button>
        <div class="sync-info" id="statusText">Click play on any track. Switching preserves the exact playhead position for instant A/B testing!</div>
    </div>

    <div class="cards-list">
"""

    for var in VARIATIONS:
        fname = f"{var['name']}.mp3"
        badge_class = "recommended" if var["id"] in ["01", "02", "05"] else ""
        badge_text = "TOP PICK" if var["id"] in ["01", "02", "05"] else f"TRACK {var['id']}"
        aa_text = f"ON ({var['aa_filter_length']} taps)" if var["aa_filter"] else "OFF (Bypass)"

        html_content += f"""
        <div class="card" id="card-{var['id']}">
            <div class="card-header">
                <span class="card-title">{var['title']}</span>
                <span class="badge {badge_class}">{badge_text}</span>
            </div>
            <div class="card-desc">{var['description']}</div>
            <div class="card-notes">🎧 <strong>What to listen for:</strong> {var['listening_notes']}</div>
            <div class="params-grid">
                <div class="param-item"><strong>Sequence:</strong> {var['sequence_ms']}ms</div>
                <div class="param-item"><strong>Seek:</strong> {var['seekwindow_ms']}ms</div>
                <div class="param-item"><strong>Overlap:</strong> {var['overlap_ms']}ms</div>
                <div class="param-item"><strong>QuickSeek:</strong> {'ON' if var['quickseek'] else 'OFF'}</div>
                <div class="param-item"><strong>Anti-Alias:</strong> {aa_text}</div>
            </div>
            <audio id="audio-{var['id']}" controls src="{fname}" onplay="onAudioPlay('{var['id']}')"></audio>
        </div>
"""

    html_content += """
    </div>
</div>

<script>
    function stopAll() {
        document.querySelectorAll('audio').forEach(a => a.pause());
        document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
        document.getElementById('statusText').innerText = "Playback stopped.";
    }

    function onAudioPlay(id) {
        let activeAudio = document.getElementById('audio-' + id);
        let currTime = activeAudio.currentTime;

        document.querySelectorAll('audio').forEach(a => {
            if (a.id !== 'audio-' + id) {
                a.pause();
                a.currentTime = currTime;
            }
        });

        document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
        document.getElementById('card-' + id).classList.add('active');
        document.getElementById('statusText').innerText = "Now Playing: " + document.querySelector('#card-' + id + ' .card-title').innerText;
    }
</script>
</body>
</html>
"""
    with open(os.path.join(output_dir, "compare_player.html"), "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_markdown_guide(output_dir, base_input_name):
    """
    Generates a detailed summary markdown and text file mapping all variations.
    """
    lines = [
        "# SoundTouch Speech Variations Map (10 Audio Tracks)",
        f"Input source: `{base_input_name}`",
        "Constant pitch shift: **-2.3 semitones** | **PURE SOUNDTOUCH ONLY (NO EQ, NO COMPRESSION)**",
        "",
        "---",
        "",
        "## Comparison Table",
        "",
        "| Track | File Name | Sequence | Seek | Overlap | QuickSeek | Anti-Alias | What to Listen For |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for v in VARIATIONS:
        aa_text = f"ON ({v['aa_filter_length']}t)" if v['aa_filter'] else "OFF"
        qs_text = "ON" if v['quickseek'] else "OFF"
        lines.append(f"| **{v['id']}** | **`{v['name']}.mp3`** | `{v['sequence_ms']}ms` | `{v['seekwindow_ms']}ms` | `{v['overlap_ms']}ms` | `{qs_text}` | `{aa_text}` | {v['listening_notes']} |")

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Parameter Descriptions & Acoustic Targets",
        ""
    ])

    for v in VARIATIONS:
        aa_desc = f"Enabled ({v['aa_filter_length']}-tap FIR filter)" if v['aa_filter'] else "Disabled (Raw Unfiltered Highs)"
        qs_desc = "Enabled (Coarse Correlation Search)" if v['quickseek'] else "Disabled (Full Precision Cross-Correlation)"
        lines.extend([
            f"### Track {v['id']}: {v['title']}",
            f"- **Filename**: `{v['name']}.mp3`",
            f"- **Pitch Shift**: `{v['pitch']}` semitones",
            f"- **Parameters**:",
            f"  - `SETTING_SEQUENCE_MS` = `{v['sequence_ms']}` ms",
            f"  - `SETTING_SEEKWINDOW_MS` = `{v['seekwindow_ms']}` ms",
            f"  - `SETTING_OVERLAP_MS` = `{v['overlap_ms']}` ms",
            f"  - `SETTING_USE_QUICKSEEK` = `{v['quickseek']}` ({qs_desc})",
            f"  - `SETTING_USE_AA_FILTER` = `{v['aa_filter']}` ({aa_desc})",
            f"- **Acoustic Focus**: {v['listening_notes']}",
            ""
        ])

    guide_path = os.path.join(output_dir, "VARIATIONS_GUIDE.md")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    txt_path = os.path.join(output_dir, "VARIATIONS_GUIDE.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Convert 1 MP3 into 10 Pure SoundTouch Speech Variations (-2.3 semitones).")
    parser.add_argument("input_file", nargs="?", default=None, help="Path to input MP3 file")
    parser.add_argument("--output_dir", "-o", default=None, help="Directory to save the 10 MP3s")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = args.input_file

    if not input_file:
        mp3s_in_dir = [f for f in os.listdir(script_dir) if f.lower().endswith(".mp3")]
        if mp3s_in_dir:
            input_file = os.path.join(script_dir, mp3s_in_dir[0])
            print(f"[*] No file argument given. Using audio found in folder: {mp3s_in_dir[0]}")
        else:
            print("[!] Usage: python test_variations.py <path_to_voice.mp3>")
            input_file = input("Enter path to your voice MP3 file: ").strip().strip('"')

    if not os.path.exists(input_file):
        print(f"[ERROR] File does not exist: {input_file}")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = args.output_dir or os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 75)
    print(" SOUNDTOUCH SPEECH TUNING LAB: 10 PURE SPEECH VARIATIONS")
    print(" (NO EQ | NO COMPRESSOR | PURE SOUNDTOUCH PARAMETERS ONLY)")
    print("=" * 75)
    print(f"Input file     : {input_file}")
    print(f"Output folder  : {output_dir}")
    print(f"Pitch shift    : -2.3 semitones")
    print("-" * 75)

    # 1. Initialize SoundTouch
    st_engine = SoundTouchDLL()
    print(f"[*] Loaded SoundTouch Engine: v{st_engine.get_version()}")

    # 2. Decode Input Audio to 48kHz PCM
    print("[*] Decoding voice to 48kHz 16-bit PCM...")
    samples, sr, channels = load_audio_as_pcm(input_file, target_sr=48000, target_channels=1)
    duration_sec = len(samples) / sr
    print(f"[*] Loaded {len(samples)} samples ({duration_sec:.2f}s, {sr}Hz mono voice)")
    print("-" * 75)

    # 3. Process each of the 10 speech variations
    for idx, var in enumerate(VARIATIONS, 1):
        t0 = time.time()
        print(f"[{idx:02d}/10] Generating: {var['name']}.mp3 ...")
        print(f"       Seq={var['sequence_ms']}ms | Seek={var['seekwindow_ms']}ms | Overlap={var['overlap_ms']}ms | QS={var['quickseek']} | AA={var['aa_filter']} ({var['aa_filter_length']}t)")

        # Run through SoundTouch pure WSOLA pitch shifter
        shifted_pcm = st_engine.process(
            samples,
            sample_rate=sr,
            channels=channels,
            pitch_semitones=var["pitch"],
            tempo=1.0,
            sequence_ms=var["sequence_ms"],
            seekwindow_ms=var["seekwindow_ms"],
            overlap_ms=var["overlap_ms"],
            quickseek=var["quickseek"],
            aa_filter=var["aa_filter"],
            aa_filter_length=var["aa_filter_length"]
        )

        # Encode directly to 320 kbps MP3 without EQ or compression
        out_path = os.path.join(output_dir, f"{var['name']}.mp3")
        save_pcm_as_mp3(
            shifted_pcm,
            out_path,
            sample_rate=sr,
            channels=channels,
            title=var["title"],
            artist="SoundTouch Speech Lab",
            comment=var["description"]
        )
        elapsed = time.time() - t0
        print(f"       -> Done in {elapsed:.2f}s! Saved: {out_path}\n")

    # 4. Generate Guides & Interactive Comparison Player
    print("[*] Generating VARIATIONS_GUIDE.md & VARIATIONS_GUIDE.txt...")
    generate_markdown_guide(output_dir, base_name)

    print("[*] Generating interactive compare_player.html...")
    generate_html_player(output_dir, base_name)

    print("=" * 75)
    print(" ALL 10 PURE SPEECH VARIATIONS CREATED SUCCESSFULLY!")
    print("=" * 75)
    print(f"Location: {output_dir}")
    print("Double-click 'compare_player.html' to A/B test between all 10 tracks!")
    print("Open 'VARIATIONS_GUIDE.txt' to see the exact parameter map.")
    print("=" * 75)


if __name__ == "__main__":
    main()
