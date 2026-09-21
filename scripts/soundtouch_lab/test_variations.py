#!/usr/bin/env python3
"""
SoundTouch Tuning Lab: 10 Parameter Variations Tester
Processes a single MP3 input file into 10 distinct MP3 files,
all shifted to -2.3 semitones with different SoundTouch and Telegram vocal DSP settings.
"""

import os
import sys
import argparse
import time
from soundtouch_engine import (
    SoundTouchDLL,
    apply_vocal_chain,
    load_audio_as_pcm,
    save_pcm_as_mp3
)

# 10 Curated Variations exploring SoundTouch parameters & Telegram vocal DSP
VARIATIONS = [
    {
        "id": "01",
        "name": "01_Studio_Speech_Pure",
        "title": "01: Pure Studio Speech (Flat Reference)",
        "description": "Full Precision WSOLA, Anti-Alias ON, Clean Uncolored Voice (No EQ, No Tube)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "preset_id": None,
        "compressor": False,
        "listening_notes": "Optimal clean baseline. Natural vocal formants, zero coloration, zero metallic phasing. Use as reference."
    },
    {
        "id": "02",
        "name": "02_Radio_Broadcaster_EQ",
        "title": "02: Radio Broadcaster (Telegram Default EQ)",
        "description": "Telegram Broadcaster Profile (+4dB @ 125Hz, +2.5dB Air @ 9kHz, Boxiness cut @ 400Hz)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "preset_id": 0,
        "compressor": False,
        "listening_notes": "Deep masculine chest warmth with condenser mic presence. Removes muddy room reverberation."
    },
    {
        "id": "03",
        "name": "03_Warm_Velvet_Podcast",
        "title": "03: Warm Velvet / Podcast Preset",
        "description": "Podcast Profile (+2.8dB @ 140Hz, Gentle Highs @ 8.5kHz, Low Cut @ 70Hz)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "preset_id": 1,
        "compressor": False,
        "listening_notes": "Intimate podcast warmth with softer, non-fatiguing treble roll-off. Ideal for close-mic voices."
    },
    {
        "id": "04",
        "name": "04_Studio_Crystal_Clarity",
        "title": "04: Studio Crystal Clarity Preset",
        "description": "Crystal Profile (+3.5dB High Air @ 10kHz, Tight Lows @ 110Hz, Deep Boxiness Cut @ 380Hz)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "preset_id": 2,
        "compressor": False,
        "listening_notes": "Razor-sharp consonant articulation and ultra-crisp highs. Great for cutting through ambient noise."
    },
    {
        "id": "05",
        "name": "05_Cinematic_Deep_Resonance",
        "title": "05: Cinematic Deep Resonance Preset",
        "description": "Cinematic Profile (+5.0dB Heavy Sub-Warmth @ 95Hz, Low HPF @ 60Hz)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "preset_id": 3,
        "compressor": False,
        "listening_notes": "Movie-trailer baritone presence. Maximum low-frequency fullness and commanding vocal weight."
    },
    {
        "id": "06",
        "name": "06_Broadcast_Tube_Saturation",
        "title": "06: Radio EQ + Analog Tube Saturation",
        "description": "Radio Broadcaster EQ + Soft-Knee Compressor & Triode Tube 2nd-Order Harmonics",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "preset_id": 0,
        "compressor": True,
        "listening_notes": "Simulates speaking through a vintage analog vacuum-tube preamp. Rich even harmonics and volume leveling."
    },
    {
        "id": "07",
        "name": "07_Extended_Sequence_Smooth",
        "title": "07: Extended Sequence Window (Long WSOLA)",
        "description": "Sequence: 60ms, Seek Window: 20ms, Overlap: 12ms (Clean Flat EQ)",
        "pitch": -2.3,
        "sequence_ms": 60,
        "seekwindow_ms": 20,
        "overlap_ms": 12,
        "quickseek": 0,
        "aa_filter": 1,
        "preset_id": None,
        "compressor": False,
        "listening_notes": "Wider correlation window. Eliminates any pitch flutter or micro-warble on long, sustained vowels."
    },
    {
        "id": "08",
        "name": "08_Short_Sequence_Fast_Speech",
        "title": "08: Short Sequence Window (Snappy WSOLA)",
        "description": "Sequence: 28ms, Seek Window: 12ms, Overlap: 6ms (Clean Flat EQ)",
        "pitch": -2.3,
        "sequence_ms": 28,
        "seekwindow_ms": 12,
        "overlap_ms": 6,
        "quickseek": 0,
        "aa_filter": 1,
        "preset_id": None,
        "compressor": False,
        "listening_notes": "Tighter correlation slices. Highly responsive to rapid speech, fast consonants, and fast cadence."
    },
    {
        "id": "09",
        "name": "09_QuickSeek_Comparison",
        "title": "09: QuickSeek Algorithmic (Coarse Search)",
        "description": "QuickSeek = 1 (Approximation Algorithm, Sequence: 40ms, Anti-Alias: ON)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 1,
        "aa_filter": 1,
        "preset_id": None,
        "compressor": False,
        "listening_notes": "Enable QuickSeek to compare directly against Full Precision (Var 01). Notice the difference in roughness."
    },
    {
        "id": "10",
        "name": "10_Raw_AntiAlias_Bypass",
        "title": "10: Raw Anti-Alias Bypass (Unfiltered)",
        "description": "Anti-Aliasing Filter OFF (AA = 0, Sequence: 40ms, Full Precision)",
        "pitch": -2.3,
        "sequence_ms": 40,
        "seekwindow_ms": 15,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 0,
        "preset_id": None,
        "compressor": False,
        "listening_notes": "Bypasses the anti-aliasing filter to allow raw unfiltered high-frequency edge and brightness."
    }
]


def generate_html_player(output_dir, base_input_name):
    """
    Generates a modern, interactive A/B comparison HTML player in the output folder.
    """
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SoundTouch Tuning Lab - 10 Variations Comparison</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: #0f172a;
        color: #f8fafc;
        margin: 0;
        padding: 24px;
    }}
    .container {{
        max-width: 960px;
        margin: 0 auto;
    }}
    h1 {{
        color: #38bdf8;
        font-size: 28px;
        margin-bottom: 8px;
    }}
    .subtitle {{
        color: #94a3b8;
        font-size: 15px;
        margin-bottom: 24px;
    }}
    .global-bar {{
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        position: sticky;
        top: 16px;
        z-index: 100;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }}
    .global-bar button {{
        background: #38bdf8;
        color: #0f172a;
        font-weight: 700;
        border: none;
        padding: 10px 18px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.15s;
    }}
    .global-bar button:hover {{
        background: #7dd3fc;
        transform: translateY(-1px);
    }}
    .sync-info {{
        color: #cbd5e1;
        font-size: 14px;
        flex: 1;
    }}
    .card {{
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
        transition: border-color 0.2s;
    }}
    .card:hover {{
        border-color: #38bdf8;
    }}
    .card.active {{
        border-color: #38bdf8;
        background: #1e2e4a;
        box-shadow: 0 0 16px rgba(56, 189, 248, 0.2);
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
        background: #0f172a;
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 12px;
        border-left: 3px solid #38bdf8;
    }}
    .params-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 8px;
        margin-bottom: 14px;
        font-size: 12px;
        color: #64748b;
    }}
    .param-item {{
        background: #0f172a;
        padding: 6px 10px;
        border-radius: 6px;
    }}
    .param-item strong {{
        color: #94a3b8;
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
    <h1>SoundTouch Tuning Lab</h1>
    <div class="subtitle">Comparing 10 Variations from <strong>{base_input_name}</strong> | Constant Pitch: -2.3 Semitones</div>

    <div class="global-bar">
        <button onclick="stopAll()">Stop All</button>
        <div class="sync-info" id="statusText">Select any track to listen. Switching maintains playback position for easy A/B testing!</div>
    </div>

    <div class="cards-list">
"""

    for var in VARIATIONS:
        fname = f"{var['name']}.mp3"
        badge_class = "recommended" if var["id"] in ["01", "02", "06"] else ""
        badge_text = "RECOMMENDED" if var["id"] in ["01", "02", "06"] else f"VARIATION {var['id']}"
        eq_text = f"Preset {var['preset_id']}" if var["preset_id"] is not None else "Clean Flat"
        comp_text = "ON (Tube Sat)" if var["compressor"] else "Clean Boost"
        
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
                <div class="param-item"><strong>Anti-Alias:</strong> {'ON' if var['aa_filter'] else 'OFF'}</div>
                <div class="param-item"><strong>Vocal EQ:</strong> {eq_text}</div>
                <div class="param-item"><strong>Tube Comp:</strong> {comp_text}</div>
            </div>
            <audio id="audio-{var['id']}" controls src="{fname}" onplay="onAudioPlay('{var['id']}')"></audio>
        </div>
"""

    html_content += """
    </div>
</div>

<script>
    let currentActiveId = null;

    function stopAll() {
        document.querySelectorAll('audio').forEach(a => a.pause());
        document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
        document.getElementById('statusText').innerText = "All playback stopped.";
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
        "# SoundTouch Tuning Lab: 10 Audio Variations Map",
        f"Generated from input: `{base_input_name}`",
        "All variations share the constant user pitch shift: **-2.3 semitones**.",
        "",
        "---",
        "",
        "## Summary Table",
        "",
        "| File | SoundTouch Parameters | Telegram EQ & Dynamics | Sonic Character |",
        "|---|---|---|---|",
    ]

    for v in VARIATIONS:
        eq_name = f"Preset {v['preset_id']}" if v['preset_id'] is not None else "Clean Flat"
        comp_name = "+ Tube Saturation" if v['compressor'] else "Clean Boost"
        st_summary = f"Seq={v['sequence_ms']}ms, Seek={v['seekwindow_ms']}ms, Overlap={v['overlap_ms']}ms, QS={v['quickseek']}, AA={v['aa_filter']}"
        lines.append(f"| **`{v['name']}.mp3`** | `{st_summary}` | `{eq_name} {comp_name}` | {v['listening_notes']} |")

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Breakdown by Variation",
        ""
    ])

    for v in VARIATIONS:
        lines.extend([
            f"### {v['title']}",
            f"- **Filename**: `{v['name']}.mp3`",
            f"- **Pitch Shift**: `{v['pitch']}` semitones",
            f"- **SoundTouch Settings**:",
            f"  - `SETTING_SEQUENCE_MS`: `{v['sequence_ms']}` ms",
            f"  - `SETTING_SEEKWINDOW_MS`: `{v['seekwindow_ms']}` ms",
            f"  - `SETTING_OVERLAP_MS`: `{v['overlap_ms']}` ms",
            f"  - `SETTING_USE_QUICKSEEK`: `{v['quickseek']}` ({'Quick Approximation' if v['quickseek'] else 'Full Precision Cross-Correlation'})",
            f"  - `SETTING_USE_AA_FILTER`: `{v['aa_filter']}` ({'Anti-Aliasing Filter ON' if v['aa_filter'] else 'OFF'})",
            f"- **Telegram Audio Processing**:",
            f"  - **Vocal EQ Preset**: `{v['preset_id']}`",
            f"  - **Analog Tube Compressor**: `{'Enabled' if v['compressor'] else 'Disabled'}`",
            f"- **Why this variation**: {v['listening_notes']}",
            ""
        ])

    guide_path = os.path.join(output_dir, "VARIATIONS_GUIDE.md")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Also save as clean plain-text for quick notepad viewing
    txt_path = os.path.join(output_dir, "VARIATIONS_GUIDE.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Process 1 MP3 into 10 SoundTouch variations (-2.3 semitones).")
    parser.add_argument("input_file", nargs="?", default=None, help="Path to input MP3/audio file")
    parser.add_argument("--output_dir", "-o", default=None, help="Directory to save the 10 MP3s")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = args.input_file

    if not input_file:
        # Check if an mp3 is placed in the script folder
        mp3s_in_dir = [f for f in os.listdir(script_dir) if f.lower().endswith(".mp3")]
        if mp3s_in_dir:
            input_file = os.path.join(script_dir, mp3s_in_dir[0])
            print(f"[*] No input file specified. Automatically using: {mp3s_in_dir[0]}")
        else:
            print("[!] Usage: python test_variations.py <path_to_audio.mp3>")
            input_file = input("Please enter path to your MP3 file: ").strip().strip('"')

    if not os.path.exists(input_file):
        print(f"[ERROR] Input file does not exist: {input_file}")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = args.output_dir or os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 72)
    print(" SOUNDTOUCH TUNING LAB: 10 VARIATIONS GENERATOR")
    print("=" * 72)
    print(f"Input file : {input_file}")
    print(f"Output dir : {output_dir}")
    print(f"Constant pitch : -2.3 semitones")
    print("-" * 72)

    # 1. Initialize SoundTouch
    st_engine = SoundTouchDLL()
    print(f"[*] Loaded SoundTouch Core: v{st_engine.get_version()}")

    # 2. Decode Input Audio to 48kHz PCM
    print("[*] Decoding input file to 48kHz 16-bit PCM...")
    samples, sr, channels = load_audio_as_pcm(input_file, target_sr=48000, target_channels=1)
    duration_sec = len(samples) / sr
    print(f"[*] Loaded {len(samples)} samples ({duration_sec:.2f} seconds, {sr}Hz mono)")
    print("-" * 72)

    # 3. Process each of the 10 variations
    for idx, var in enumerate(VARIATIONS, 1):
        t0 = time.time()
        print(f"[{idx}/10] Processing: {var['name']}.mp3 ...")
        print(f"       SoundTouch: Seq={var['sequence_ms']}ms, Seek={var['seekwindow_ms']}ms, Overlap={var['overlap_ms']}ms, QS={var['quickseek']}, AA={var['aa_filter']}")
        print(f"       Telegram  : Preset={var['preset_id']}, Tube={var['compressor']}")

        # Step A: Run through SoundTouch WSOLA pitch shifter
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
            aa_filter=var["aa_filter"]
        )

        # Step B: Apply Telegram Studio EQ & Dynamics
        final_pcm = apply_vocal_chain(
            shifted_pcm,
            sample_rate=sr,
            channels=channels,
            preset_id=var["preset_id"],
            compressor_enabled=var["compressor"]
        )

        # Step C: Encode to 320 kbps MP3 with full metadata
        out_path = os.path.join(output_dir, f"{var['name']}.mp3")
        save_pcm_as_mp3(
            final_pcm,
            out_path,
            sample_rate=sr,
            channels=channels,
            title=var["title"],
            artist="SoundTouch Lab",
            comment=var["description"]
        )
        elapsed = time.time() - t0
        print(f"       -> Done in {elapsed:.2f}s! Saved: {out_path}\n")

    # 4. Generate Guides & Interactive Comparison Player
    print("[*] Generating VARIATIONS_GUIDE.md & VARIATIONS_GUIDE.txt...")
    generate_markdown_guide(output_dir, base_name)

    print("[*] Generating interactive compare_player.html...")
    generate_html_player(output_dir, base_name)

    print("=" * 72)
    print(" ALL 10 MP3 VARIATIONS SUCCESSFULLY CREATED!")
    print("=" * 72)
    print(f"All files saved in: {output_dir}")
    print("Open 'compare_player.html' in your browser to A/B test between all 10 tracks!")
    print("Or open 'VARIATIONS_GUIDE.txt' for the complete parameter map.")
    print("=" * 72)


if __name__ == "__main__":
    main()
