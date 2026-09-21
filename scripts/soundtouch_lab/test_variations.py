#!/usr/bin/env python3
"""
SoundTouch Pure Speech Tuning Lab: Categorized Parameter Suite.
Pure SoundTouch algorithmic parameters ONLY.
NO EQ, NO COMPRESSION.
All variations pitch-shifted to -2.3 semitones for human speaking voice & voice notes.

Categories:
1. Sequence (SETTING_SEQUENCE_MS): Lowest (20ms) to Highest (100ms)
2. Seek Window (SETTING_SEEKWINDOW_MS): Lowest (4ms) to Highest (35ms)
3. Overlap (SETTING_OVERLAP_MS): Lowest (2ms) to Highest (18ms)
4. QuickSeek (SETTING_USE_QUICKSEEK): Full Precision (0) vs Coarse Approximation (1)
5. Anti-Alias (SETTING_USE_AA_FILTER & LENGTH): OFF to Lowest (8 taps) to Highest (128 taps)
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

# =========================================================================
# 5 Systematic Speech Parameter Categories (Ordered Lowest to Highest)
# All holding other parameters constant at the neutral speech baseline.
# =========================================================================

BASELINE_PITCH = -2.3
BASELINE_SEQ = 40
BASELINE_SEEK = 15
BASELINE_OVERLAP = 8
BASELINE_QS = 0
BASELINE_AA = 1
BASELINE_AA_LEN = 64

CATEGORIES = [
    {
        "folder": "01_Sequence",
        "title": "Category 1: Sequence Duration (SETTING_SEQUENCE_MS)",
        "short_name": "Sequence",
        "desc": "Length of each processing slice in milliseconds. Shorter slices preserve fast articulation and crisp consonants; longer slices prevent vowel buzz but can blur fast words.",
        "baseline_info": f"Constants: Seek={BASELINE_SEEK}ms | Overlap={BASELINE_OVERLAP}ms | QuickSeek=OFF | Anti-Alias=ON ({BASELINE_AA_LEN}t)",
        "tracks": [
            {
                "id": "Seq_01",
                "val_str": "20 ms (Lowest)",
                "file_name": "Seq_01_20ms",
                "sequence_ms": 20, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Lowest safe slice duration. Extreme responsiveness to fast speech transients; listen for rapid consonants vs subtle vowel flutter."
            },
            {
                "id": "Seq_02",
                "val_str": "25 ms",
                "file_name": "Seq_02_25ms",
                "sequence_ms": 25, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Very fast slicing. Excellent for rapid-fire talkers and punchy syllables."
            },
            {
                "id": "Seq_03",
                "val_str": "30 ms",
                "file_name": "Seq_03_30ms",
                "sequence_ms": 30, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Crisp conversational slicing with immediate consonant articulation."
            },
            {
                "id": "Seq_04",
                "val_str": "35 ms",
                "file_name": "Seq_04_35ms",
                "sequence_ms": 35, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Snappy speech pacing, slightly tighter than standard baseline."
            },
            {
                "id": "Seq_05",
                "val_str": "40 ms (Speech Baseline)",
                "file_name": "Seq_05_40ms_Baseline",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Official SoundTouch speech baseline. Balanced trade-off between consonant clarity and vowel continuity."
            },
            {
                "id": "Seq_06",
                "val_str": "50 ms",
                "file_name": "Seq_06_50ms",
                "sequence_ms": 50, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Relaxed conversational pacing. Smooth vocal body on sustained phrases."
            },
            {
                "id": "Seq_07",
                "val_str": "60 ms",
                "file_name": "Seq_07_60ms",
                "sequence_ms": 60, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Smooth vowel priority. Notice how prolonged vowel tones ('ah', 'ee', 'oh') become silky without micro-buzz."
            },
            {
                "id": "Seq_08",
                "val_str": "70 ms",
                "file_name": "Seq_08_70ms",
                "sequence_ms": 70, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Extended speech sequence. High vowel stability, slightly slower transient recovery."
            },
            {
                "id": "Seq_09",
                "val_str": "82 ms (Music Default)",
                "file_name": "Seq_09_82ms_MusicDefault",
                "sequence_ms": 82, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "SoundTouch default designed for polyphonic music. Notice how speech sounds slightly drawn out compared to 40ms."
            },
            {
                "id": "Seq_10",
                "val_str": "100 ms (Highest)",
                "file_name": "Seq_10_100ms",
                "sequence_ms": 100, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Highest sequence length. Maximum acoustic smoothing; tests the upper limit of slice duration."
            }
        ]
    },
    {
        "folder": "02_SeekWindow",
        "title": "Category 2: Seek Window Length (SETTING_SEEKWINDOW_MS)",
        "short_name": "Seek Window",
        "desc": "How far in milliseconds SoundTouch scans to find the best correlation match for your fundamental pitch period (F0). Deep male voices (85-110Hz) have longer wavelengths and require longer seek windows to prevent robotic flutter.",
        "baseline_info": f"Constants: Sequence={BASELINE_SEQ}ms | Overlap={BASELINE_OVERLAP}ms | QuickSeek=OFF | Anti-Alias=ON ({BASELINE_AA_LEN}t)",
        "tracks": [
            {
                "id": "Seek_01",
                "val_str": "4 ms (Lowest)",
                "file_name": "Seek_01_04ms",
                "sequence_ms": 40, "seekwindow_ms": 4, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Lowest search window. Too short to catch full fundamental vocal pitch waves; notice robotic phasing / flutter."
            },
            {
                "id": "Seek_02",
                "val_str": "8 ms",
                "file_name": "Seek_02_08ms",
                "sequence_ms": 40, "seekwindow_ms": 8, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Short search window. Works for higher-pitched voices, but may wobble on deep chest notes."
            },
            {
                "id": "Seek_03",
                "val_str": "10 ms",
                "file_name": "Seek_03_10ms",
                "sequence_ms": 40, "seekwindow_ms": 10, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "100Hz half-period search. Solid tracking for medium voice registers."
            },
            {
                "id": "Seek_04",
                "val_str": "12 ms",
                "file_name": "Seek_04_12ms",
                "sequence_ms": 40, "seekwindow_ms": 12, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Moderate speech search window with solid correlation stability."
            },
            {
                "id": "Seek_05",
                "val_str": "15 ms (Speech Baseline)",
                "file_name": "Seek_05_15ms_Baseline",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Standard SoundTouch speech recommendation. Covers most normal speech fundamentals."
            },
            {
                "id": "Seek_06",
                "val_str": "18 ms",
                "file_name": "Seek_06_18ms",
                "sequence_ms": 40, "seekwindow_ms": 18, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Extended search window. Better lock on low vocal resonances (below 100Hz)."
            },
            {
                "id": "Seek_07",
                "val_str": "20 ms (Deep Voice Opt)",
                "file_name": "Seek_07_20ms_DeepVoice",
                "sequence_ms": 40, "seekwindow_ms": 20, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Deep male voice optimization. Allows the algorithm to track full 85-95Hz fundamental chest pitch periods cleanly."
            },
            {
                "id": "Seek_08",
                "val_str": "24 ms",
                "file_name": "Seek_08_24ms",
                "sequence_ms": 40, "seekwindow_ms": 24, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Very wide search window. Highly stable pitch tracking across broad dynamic pitch inflections."
            },
            {
                "id": "Seek_09",
                "val_str": "28 ms (Music Default)",
                "file_name": "Seek_09_28ms_MusicDefault",
                "sequence_ms": 40, "seekwindow_ms": 28, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Default SoundTouch search window for general audio/music."
            },
            {
                "id": "Seek_10",
                "val_str": "35 ms (Highest)",
                "file_name": "Seek_10_35ms",
                "sequence_ms": 40, "seekwindow_ms": 35, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Maximum search window. Tests the wide correlation boundary for bass pitch tracking."
            }
        ]
    },
    {
        "folder": "03_Overlap",
        "title": "Category 3: Overlap Duration (SETTING_OVERLAP_MS)",
        "short_name": "Overlap",
        "desc": "The linear crossfade duration in milliseconds between adjacent audio slices. Shorter overlap preserves punchy transient attacks; longer overlap creates a smoother, softer blend between slices.",
        "baseline_info": f"Constants: Sequence={BASELINE_SEQ}ms | Seek={BASELINE_SEEK}ms | QuickSeek=OFF | Anti-Alias=ON ({BASELINE_AA_LEN}t)",
        "tracks": [
            {
                "id": "Ovl_01",
                "val_str": "2 ms (Lowest)",
                "file_name": "Overlap_01_02ms",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 2, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Minimal 2ms crossfade. Razor-sharp acoustic attacks with zero phase smearing; listen for edge on plosives."
            },
            {
                "id": "Ovl_02",
                "val_str": "4 ms",
                "file_name": "Overlap_02_04ms",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 4, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Short 4ms crossfade. Tight, dry transient response."
            },
            {
                "id": "Ovl_03",
                "val_str": "6 ms",
                "file_name": "Overlap_03_06ms",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 6, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Crisp crossfade. Great clarity on consonant attacks."
            },
            {
                "id": "Ovl_04",
                "val_str": "8 ms (Speech Baseline)",
                "file_name": "Overlap_04_08ms_Baseline",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Official SoundTouch speech baseline. Natural crossfade balance for human voice."
            },
            {
                "id": "Ovl_05",
                "val_str": "10 ms",
                "file_name": "Overlap_05_10ms",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 10, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Smooth vocal blend. Softens harsh slice transitions."
            },
            {
                "id": "Ovl_06",
                "val_str": "12 ms (Music Default)",
                "file_name": "Overlap_06_12ms_MusicDefault",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 12, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "SoundTouch default for music. Seamless crossfading on continuous harmonic tones."
            },
            {
                "id": "Ovl_07",
                "val_str": "14 ms",
                "file_name": "Overlap_07_14ms",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 14, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Wide crossfade. Notice the airy, mellow transition between spoken phonemes."
            },
            {
                "id": "Ovl_08",
                "val_str": "16 ms",
                "file_name": "Overlap_08_16ms",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 16, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Very wide crossfade. Highly continuous blending."
            },
            {
                "id": "Ovl_09",
                "val_str": "18 ms (Highest)",
                "file_name": "Overlap_09_18ms",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 18, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Maximum crossfade length. Deepest blending window possible for a 40ms sequence."
            }
        ]
    },
    {
        "folder": "04_QuickSeek",
        "title": "Category 4: QuickSeek Algorithm (SETTING_USE_QUICKSEEK)",
        "short_name": "QuickSeek",
        "desc": "Direct comparison between Full-Precision Cross-Correlation (0) and Coarse QuickSeek (1). Full precision evaluates every single sample for the best match; QuickSeek skips samples to save CPU but introduces metallic/robotic phase artifacts.",
        "baseline_info": "Comparison pairs across 3 different seek window lengths",
        "tracks": [
            {
                "id": "QS_01",
                "val_str": "Full Precision @ 15ms Seek",
                "file_name": "QS_01_FullPrecision_Seek15",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Full precision correlation search at 15ms seek. Pure, natural vocal timbre without metallic artifacts."
            },
            {
                "id": "QS_02",
                "val_str": "QuickSeek Coarse @ 15ms Seek",
                "file_name": "QS_02_QuickSeek_Seek15",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 1, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "QuickSeek enabled at 15ms seek. Listen closely to sustained vowels for robotic roughness vs Track QS_01."
            },
            {
                "id": "QS_03",
                "val_str": "Full Precision @ 20ms Seek (Deep Voice)",
                "file_name": "QS_03_FullPrecision_Seek20",
                "sequence_ms": 48, "seekwindow_ms": 20, "overlap_ms": 10, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Full precision correlation search at 20ms seek. Deep chest fundamental resonance tracked with zero flutter."
            },
            {
                "id": "QS_04",
                "val_str": "QuickSeek Coarse @ 20ms Seek (Deep Voice)",
                "file_name": "QS_04_QuickSeek_Seek20",
                "sequence_ms": 48, "seekwindow_ms": 20, "overlap_ms": 10, "quickseek": 1, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "QuickSeek enabled at 20ms seek. Check if deep frequencies lose warmth and gain a metallic ring."
            },
            {
                "id": "QS_05",
                "val_str": "Full Precision @ 28ms Seek (Music Default)",
                "file_name": "QS_05_FullPrecision_Seek28",
                "sequence_ms": 82, "seekwindow_ms": 28, "overlap_ms": 12, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Full precision at default 28ms seek window."
            },
            {
                "id": "QS_06",
                "val_str": "QuickSeek Coarse @ 28ms Seek (Music Default)",
                "file_name": "QS_06_QuickSeek_Seek28",
                "sequence_ms": 82, "seekwindow_ms": 28, "overlap_ms": 12, "quickseek": 1, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "QuickSeek enabled at default 28ms seek window."
            }
        ]
    },
    {
        "folder": "05_AntiAlias",
        "title": "Category 5: Anti-Alias Filter & Taps (SETTING_USE_AA_FILTER & LENGTH)",
        "short_name": "Anti-Alias",
        "desc": "Controls low-pass filtering during pitch transposition. Bypassing leaves raw high-frequency edge (with aliasing); enabling uses a linear-phase FIR filter. More taps (8 -> 128) mean a steeper transition band, preserving maximum vocal presence while cutting aliasing.",
        "baseline_info": f"Constants: Sequence={BASELINE_SEQ}ms | Seek={BASELINE_SEEK}ms | Overlap={BASELINE_OVERLAP}ms | QuickSeek=OFF",
        "tracks": [
            {
                "id": "AA_01",
                "val_str": "Filter OFF (Bypassed)",
                "file_name": "AA_01_Filter_Off_Bypass",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 0, "aa_filter_length": 0,
                "notes": "Anti-alias filter completely bypassed. Raw high-frequency breath and grit; notice any crisp aliasing harmonics."
            },
            {
                "id": "AA_02",
                "val_str": "8 Taps (Lowest)",
                "file_name": "AA_02_Filter_On_08taps",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 8,
                "notes": "Minimal 8-tap FIR filter. Softest transition slope; light attenuation of folded harmonics."
            },
            {
                "id": "AA_03",
                "val_str": "16 Taps",
                "file_name": "AA_03_Filter_On_16taps",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 16,
                "notes": "16-tap FIR filter. Gentle high-frequency roll-off."
            },
            {
                "id": "AA_04",
                "val_str": "32 Taps",
                "file_name": "AA_04_Filter_On_32taps",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 32,
                "notes": "32-tap FIR filter. Fast, clean cutoff often used for lightweight mobile speech."
            },
            {
                "id": "AA_05",
                "val_str": "48 Taps",
                "file_name": "AA_05_Filter_On_48taps",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 48,
                "notes": "48-tap FIR filter. Solid compromise between cutoff sharpness and acoustic transparency."
            },
            {
                "id": "AA_06",
                "val_str": "64 Taps (Speech Baseline)",
                "file_name": "AA_06_Filter_On_64taps_Baseline",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 64,
                "notes": "Official SoundTouch speech default (64 taps). Clean high-frequency rejection with zero audible resonance."
            },
            {
                "id": "AA_07",
                "val_str": "96 Taps",
                "file_name": "AA_07_Filter_On_96taps",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 96,
                "notes": "96-tap FIR filter. Very steep transition band preserving crisp sibilance ('s', 'z')."
            },
            {
                "id": "AA_08",
                "val_str": "128 Taps (Highest Resolution)",
                "file_name": "AA_08_Filter_On_128taps_Max",
                "sequence_ms": 40, "seekwindow_ms": 15, "overlap_ms": 8, "quickseek": 0, "aa_filter": 1, "aa_filter_length": 128,
                "notes": "Maximum studio-grade 128-tap brickwall FIR filter. Highest theoretical stopband attenuation and clarity."
            }
        ]
    }
]


def generate_html_player(output_dir, base_input_name):
    """
    Generates an interactive, categorized, dark-themed HTML comparison player.
    Supports tabbed category browsing, instant synchronized A/B playback switching,
    and intuitive keyboard shortcuts (1-9, 0, Space, Arrows).
    """
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SoundTouch Pure Speech Tuning Lab - Categorized Comparison</title>
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}
    body {{
        background: #090d16;
        color: #e2e8f0;
        padding: 24px;
        min-height: 100vh;
    }}
    .container {{
        max-width: 1060px;
        margin: 0 auto;
    }}
    header {{
        margin-bottom: 24px;
    }}
    h1 {{
        font-size: 26px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }}
    .subtitle {{
        color: #94a3b8;
        font-size: 14px;
        line-height: 1.5;
    }}
    .highlight {{
        color: #38bdf8;
        font-weight: 600;
    }}

    /* Global Sticky Player */
    .player-dock {{
        background: #131d31;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 16px 22px;
        margin-bottom: 20px;
        position: sticky;
        top: 16px;
        z-index: 1000;
        box-shadow: 0 12px 36px rgba(0,0,0,0.7);
        backdrop-filter: blur(10px);
    }}
    .player-top {{
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;
    }}
    .play-btn {{
        background: #38bdf8;
        color: #090d16;
        font-weight: 800;
        font-size: 15px;
        border: none;
        padding: 10px 22px;
        border-radius: 9999px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.15s ease;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.35);
    }}
    .play-btn:hover {{
        background: #7dd3fc;
        transform: scale(1.02);
    }}
    .track-meta {{
        flex: 1;
        overflow: hidden;
    }}
    .now-playing-label {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #38bdf8;
        font-weight: 700;
        margin-bottom: 2px;
    }}
    .current-track-title {{
        font-size: 16px;
        font-weight: 700;
        color: #ffffff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .time-badge {{
        font-family: monospace;
        font-size: 14px;
        color: #94a3b8;
        background: #090d16;
        padding: 6px 12px;
        border-radius: 6px;
        border: 1px solid #1e293b;
    }}
    .scrubber-container {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .scrubber {{
        flex: 1;
        -webkit-appearance: none;
        height: 6px;
        border-radius: 3px;
        background: #1e293b;
        outline: none;
        cursor: pointer;
    }}
    .scrubber::-webkit-slider-thumb {{
        -webkit-appearance: none;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #38bdf8;
        cursor: pointer;
        box-shadow: 0 0 10px #38bdf8;
    }}

    /* Category Navigation Tabs */
    .tabs-bar {{
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding-bottom: 8px;
        margin-bottom: 20px;
    }}
    .tab-btn {{
        background: #111a2e;
        color: #94a3b8;
        border: 1px solid #1e293b;
        padding: 9px 16px;
        border-radius: 8px;
        font-size: 13.5px;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        transition: all 0.15s;
    }}
    .tab-btn:hover {{
        background: #152340;
        color: #f1f5f9;
        border-color: #38bdf8;
    }}
    .tab-btn.active {{
        background: #0369a1;
        color: #ffffff;
        border-color: #38bdf8;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
    }}

    /* Category Section */
    .category-section {{
        margin-bottom: 32px;
    }}
    .cat-header {{
        background: #101726;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }}
    .cat-title {{
        font-size: 18px;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 4px;
    }}
    .cat-desc {{
        color: #94a3b8;
        font-size: 13px;
        margin-bottom: 6px;
    }}
    .cat-baseline {{
        color: #38bdf8;
        font-size: 12px;
        font-family: monospace;
    }}

    /* Track Cards */
    .card {{
        background: #101827;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.15s ease;
        display: flex;
        align-items: center;
        gap: 16px;
    }}
    .card:hover {{
        border-color: #38bdf8;
        background: #142036;
        transform: translateX(4px);
    }}
    .card.active {{
        border-color: #38bdf8;
        background: #142542;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
    }}
    .track-num-badge {{
        font-family: monospace;
        font-weight: 700;
        font-size: 13px;
        background: #090d16;
        border: 1px solid #1e293b;
        padding: 6px 10px;
        border-radius: 6px;
        color: #94a3b8;
        min-width: 44px;
        text-align: center;
    }}
    .card.active .track-num-badge {{
        background: #38bdf8;
        color: #090d16;
        border-color: #38bdf8;
    }}
    .card-body {{
        flex: 1;
        overflow: hidden;
    }}
    .card-title-line {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }}
    .card-param-val {{
        font-size: 16px;
        font-weight: 700;
        color: #ffffff;
    }}
    .pill {{
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
        text-transform: uppercase;
    }}
    .pill-baseline {{
        background: #15803d;
        color: #dcfce7;
    }}
    .pill-opt {{
        background: #0369a1;
        color: #e0f2fe;
    }}
    .card-notes {{
        font-size: 13px;
        color: #94a3b8;
        line-height: 1.4;
    }}
    .card-quick-btn {{
        background: transparent;
        border: 1px solid #334155;
        color: #e2e8f0;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s;
    }}
    .card:hover .card-quick-btn {{
        background: #38bdf8;
        color: #090d16;
        border-color: #38bdf8;
    }}

    /* Shortcuts Footer */
    .shortcuts-box {{
        background: #101726;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 30px;
        font-size: 13px;
        color: #94a3b8;
    }}
    .shortcuts-box strong {{
        color: #f1f5f9;
    }}
    .key {{
        background: #090d16;
        border: 1px solid #334155;
        border-radius: 4px;
        padding: 2px 6px;
        font-family: monospace;
        color: #38bdf8;
        font-weight: bold;
    }}
</style>
</head>
<body>

<div class="container">
    <header>
        <h1>SoundTouch Pure Speech Tuning Lab</h1>
        <div class="subtitle">
            Systematic Categorized Parameter Explorer from: <span class="highlight">{base_input_name}</span><br>
            All Tracks Shifted <span class="highlight">-2.3 Semitones</span> | <strong>NO EQ, NO Compression, 100% Pure SoundTouch DSP</strong>
        </div>
    </header>

    <!-- Global Master Player Dock -->
    <div class="player-dock">
        <div class="player-top">
            <button class="play-btn" id="masterPlayBtn" onclick="togglePlay()">
                <span id="playIcon">▶</span> <span id="playBtnText">Play</span>
            </button>
            <div class="track-meta">
                <div class="now-playing-label" id="categoryLabel">Category 1: Sequence</div>
                <div class="current-track-title" id="trackTitleLabel">Seq_05_40ms_Baseline (Speech Baseline)</div>
            </div>
            <div class="time-badge" id="timeDisplay">0:00 / 0:00</div>
        </div>
        <div class="scrubber-container">
            <input type="range" class="scrubber" id="timeScrubber" min="0" max="100" value="0" step="0.1" oninput="onScrub(this.value)">
        </div>
    </div>

    <!-- Category Filter Tabs -->
    <div class="tabs-bar">
        <button class="tab-btn active" onclick="switchCategoryTab('all', this)">All Categories (43)</button>
        <button class="tab-btn" onclick="switchCategoryTab('01_Sequence', this)">1. Sequence (10)</button>
        <button class="tab-btn" onclick="switchCategoryTab('02_SeekWindow', this)">2. Seek Window (10)</button>
        <button class="tab-btn" onclick="switchCategoryTab('03_Overlap', this)">3. Overlap (9)</button>
        <button class="tab-btn" onclick="switchCategoryTab('04_QuickSeek', this)">4. QuickSeek (6)</button>
        <button class="tab-btn" onclick="switchCategoryTab('05_AntiAlias', this)">5. Anti-Alias (8)</button>
    </div>

    <!-- Hidden Master Audio Element -->
    <audio id="masterAudio" preload="auto"></audio>

    <div id="categoriesContainer">
"""

    all_tracks_js = []

    for cat_idx, cat in enumerate(CATEGORIES, 1):
        cat_folder = cat["folder"]
        html_content += f"""
        <div class="category-section" id="cat-section-{cat_folder}">
            <div class="cat-header">
                <div class="cat-title">{cat['title']}</div>
                <div class="cat-desc">{cat['desc']}</div>
                <div class="cat-baseline">📌 {cat['baseline_info']}</div>
            </div>
            <div class="cards-list">
        """

        for t_idx, trk in enumerate(cat["tracks"], 1):
            file_rel = f"{cat_folder}/{trk['file_name']}.mp3"
            track_js_obj = {
                "id": trk["id"],
                "cat_folder": cat_folder,
                "cat_name": cat["title"],
                "title": f"{trk['file_name']} ({trk['val_str']})",
                "val_str": trk["val_str"],
                "file": file_rel,
                "notes": trk["notes"],
                "cat_idx": cat_idx,
                "trk_idx": t_idx
            }
            all_tracks_js.append(track_js_obj)

            pill_html = ""
            if "Baseline" in trk["val_str"]:
                pill_html = '<span class="pill pill-baseline">Baseline Reference</span>'
            elif "Lowest" in trk["val_str"]:
                pill_html = '<span class="pill pill-opt">Lowest</span>'
            elif "Highest" in trk["val_str"] or "Max" in trk["val_str"]:
                pill_html = '<span class="pill pill-opt">Highest</span>'
            elif "Opt" in trk["val_str"]:
                pill_html = '<span class="pill pill-opt">Optimized</span>'

            html_content += f"""
                <div class="card" id="card-{trk['id']}" onclick="playTrackById('{trk['id']}')">
                    <div class="track-num-badge">{t_idx:02d}</div>
                    <div class="card-body">
                        <div class="card-title-line">
                            <span class="card-param-val">{trk['val_str']}</span>
                            {pill_html}
                        </div>
                        <div class="card-notes">🎧 {trk['notes']}</div>
                    </div>
                    <button class="card-quick-btn">Listen</button>
                </div>
            """

        html_content += """
            </div>
        </div>
        """

    import json
    tracks_json_str = json.dumps(all_tracks_js)

    html_content += f"""
    </div>

    <!-- Keyboard Shortcuts Legend -->
    <div class="shortcuts-box">
        <strong>⚡ Keyboard Shortcuts (Instant A/B Testing):</strong><br>
        • <span class="key">Space</span> : Play / Pause &nbsp;|&nbsp;
        • <span class="key">1</span> to <span class="key">0</span> : Instant switch to tracks 1 to 10 in active category (preserves playback position) &nbsp;|&nbsp;
        • <span class="key">↑</span> / <span class="key">↓</span> : Next / Previous track &nbsp;|&nbsp;
        • <span class="key">←</span> / <span class="key">→</span> : Seek -2s / +2s
    </div>
</div>

<script>
    const tracks = {tracks_json_str};
    let currentTrackIndex = 4; // Default to Seq_05_40ms_Baseline
    let currentCategoryFilter = 'all';
    const audio = document.getElementById('masterAudio');
    const playBtn = document.getElementById('masterPlayBtn');
    const playBtnText = document.getElementById('playBtnText');
    const playIcon = document.getElementById('playIcon');
    const categoryLabel = document.getElementById('categoryLabel');
    const trackTitleLabel = document.getElementById('trackTitleLabel');
    const timeDisplay = document.getElementById('timeDisplay');
    const scrubber = document.getElementById('timeScrubber');

    function formatTime(sec) {{
        if (isNaN(sec) || sec < 0) return "0:00";
        let m = Math.floor(sec / 60);
        let s = Math.floor(sec % 60);
        return m + ":" + (s < 10 ? "0" : "") + s;
    }}

    function switchCategoryTab(catFolder, btnEl) {{
        currentCategoryFilter = catFolder;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btnEl.classList.add('active');

        document.querySelectorAll('.category-section').forEach(sec => {{
            if (catFolder === 'all' || sec.id === 'cat-section-' + catFolder) {{
                sec.style.display = 'block';
            }} else {{
                sec.style.display = 'none';
            }}
        }});
    }}

    function playTrackByIndex(idx, autoPlay = true) {{
        if (idx < 0 || idx >= tracks.length) return;
        const prevTime = audio.currentTime || 0;
        const wasPaused = audio.paused;

        currentTrackIndex = idx;
        const trk = tracks[idx];

        categoryLabel.innerText = trk.cat_name;
        trackTitleLabel.innerText = trk.title;

        // Highlight active card
        document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
        const cardEl = document.getElementById('card-' + trk.id);
        if (cardEl) {{
            cardEl.classList.add('active');
            cardEl.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
        }}

        audio.src = trk.file;
        audio.load();

        audio.onloadedmetadata = () => {{
            audio.currentTime = Math.min(prevTime, audio.duration || 0);
            if (autoPlay && !wasPaused) {{
                audio.play();
            }}
        }};

        if (autoPlay) {{
            audio.play().catch(e => console.log('Autoplay handled:', e));
        }}
    }}

    function playTrackById(id) {{
        const idx = tracks.findIndex(t => t.id === id);
        if (idx !== -1) {{
            playTrackByIndex(idx, true);
        }}
    }}

    function togglePlay() {{
        if (audio.paused) {{
            audio.play();
        }} else {{
            audio.pause();
        }}
    }}

    audio.addEventListener('play', () => {{
        playIcon.innerText = "⏸";
        playBtnText.innerText = "Pause";
        playBtn.style.background = "#38bdf8";
    }});

    audio.addEventListener('pause', () => {{
        playIcon.innerText = "▶";
        playBtnText.innerText = "Play";
        playBtn.style.background = "#7dd3fc";
    }});

    audio.addEventListener('timeupdate', () => {{
        if (!isNaN(audio.duration) && audio.duration > 0) {{
            scrubber.value = (audio.currentTime / audio.duration) * 100;
            timeDisplay.innerText = formatTime(audio.currentTime) + " / " + formatTime(audio.duration);
        }}
    }});

    function onScrub(val) {{
        if (!isNaN(audio.duration) && audio.duration > 0) {{
            audio.currentTime = (val / 100) * audio.duration;
        }}
    }}

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {{
        if (e.target.tagName === 'INPUT') return;

        // Space: Play/Pause
        if (e.code === 'Space') {{
            e.preventDefault();
            togglePlay();
        }}
        // Left / Right Arrow: Seek 2s
        else if (e.code === 'ArrowLeft') {{
            e.preventDefault();
            audio.currentTime = Math.max(0, audio.currentTime - 2);
        }}
        else if (e.code === 'ArrowRight') {{
            e.preventDefault();
            audio.currentTime = Math.min(audio.duration, audio.currentTime + 2);
        }}
        // Up / Down Arrow: Switch Tracks
        else if (e.code === 'ArrowUp') {{
            e.preventDefault();
            let newIdx = (currentTrackIndex - 1 + tracks.length) % tracks.length;
            playTrackByIndex(newIdx, true);
        }}
        else if (e.code === 'ArrowDown') {{
            e.preventDefault();
            let newIdx = (currentTrackIndex + 1) % tracks.length;
            playTrackByIndex(newIdx, true);
        }}
        // Number keys 1-9, 0
        else if (e.key >= '0' && e.key <= '9') {{
            e.preventDefault();
            let targetNum = e.key === '0' ? 10 : parseInt(e.key);
            
            // If filtering by a category, pick the track inside that category
            let visibleTracks = tracks;
            if (currentCategoryFilter !== 'all') {{
                visibleTracks = tracks.filter(t => t.cat_folder === currentCategoryFilter);
            }}
            if (targetNum <= visibleTracks.length) {{
                const targetTrk = visibleTracks[targetNum - 1];
                const globalIdx = tracks.findIndex(t => t.id === targetTrk.id);
                playTrackByIndex(globalIdx, true);
            }}
        }}
    }});

    // Initialize with default baseline track
    window.addEventListener('DOMContentLoaded', () => {{
        playTrackByIndex(4, false);
    }});
</script>

</body>
</html>
"""
    with open(os.path.join(output_dir, "compare_player.html"), "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_guides(output_dir, base_input_name):
    """
    Generates CATEGORIES_GUIDE.md and CATEGORIES_GUIDE.txt plain-text manuals.
    """
    lines = [
        "=" * 80,
        "SOUNDTOUCH PURE SPEECH TUNING LAB: CATEGORIZED PARAMETER SUITE",
        "=" * 80,
        f"Input Audio Source : {base_input_name}",
        f"Pitch Shift        : {BASELINE_PITCH} semitones (LOCKED ACROSS ALL TRACKS)",
        "Audio Processing   : 100% PURE SOUNDTOUCH DSP (NO EQ, NO COMPRESSOR, NO GATES)",
        "Sample Rate        : 48,000 Hz 16-bit Mono",
        "=" * 80,
        "",
        "SUMMARY OF THE 5 SYSTEMATIC CATEGORIES:",
        "--------------------------------------------------------------------------------",
        "1. Sequence Duration (10 files) : 20ms -> 100ms (Slice length for phonemes)",
        "2. Seek Window Length (10 files): 4ms  -> 35ms  (Pitch period correlation scanner)",
        "3. Overlap Duration (9 files)   : 2ms  -> 18ms  (Crossfade window between slices)",
        "4. QuickSeek Precision (6 files): Full Precision (0) vs Coarse Approximation (1)",
        "5. Anti-Alias Filter (8 files)  : Filter OFF -> 8 taps -> 128 taps FIR",
        "--------------------------------------------------------------------------------",
        "",
        "HOW TO A/B TEST IN THE BROWSER:",
        "1. Double-click 'compare_player.html' in the output folder.",
        "2. Put on headphones.",
        "3. Press Spacebar to Play.",
        "4. Click any category tab at the top to focus on one parameter at a time.",
        "5. Press keys 1 through 0 to instantly switch tracks at the EXACT same timestamp!",
        "",
        "=" * 80,
        "DETAILED PARAMETER MAP",
        "=" * 80,
        ""
    ]

    for cat in CATEGORIES:
        lines.append(f"[{cat['title'].upper()}]")
        lines.append(f"Explanation: {cat['desc']}")
        lines.append(f"Baseline   : {cat['baseline_info']}")
        lines.append("-" * 80)

        for trk in cat["tracks"]:
            lines.append(f"  File : {cat['folder']}/{trk['file_name']}.mp3")
            lines.append(f"  Value: {trk['val_str']}")
            lines.append(f"  Specs: Seq={trk['sequence_ms']}ms | Seek={trk['seekwindow_ms']}ms | Overlap={trk['overlap_ms']}ms | QS={trk['quickseek']} | AA={trk['aa_filter']} ({trk['aa_filter_length']}t)")
            lines.append(f"  Notes: {trk['notes']}")
            lines.append("")
        lines.append("")

    content = "\n".join(lines)
    with open(os.path.join(output_dir, "CATEGORIES_GUIDE.txt"), "w", encoding="utf-8") as f:
        f.write(content)
    with open(os.path.join(output_dir, "CATEGORIES_GUIDE.md"), "w", encoding="utf-8") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="SoundTouch Categorized Parameter Suite (Lowest to Highest).")
    parser.add_argument("input_file", nargs="?", default=None, help="Path to input voice MP3")
    parser.add_argument("--output_dir", "-o", default=None, help="Directory to save output files")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = args.input_file

    if not input_file:
        # Check if voice.mp3 or any user mp3 is in the folder
        candidates = ["voice.mp3", "my_voice.mp3"]
        for cand in candidates:
            cand_path = os.path.join(script_dir, cand)
            if os.path.exists(cand_path):
                input_file = cand_path
                print(f"[*] Detected voice file: {cand}")
                break

    if not input_file:
        mp3s_in_dir = [
            f for f in os.listdir(script_dir)
            if f.lower().endswith(".mp3") and not f.startswith("Seq_") and not f.startswith("Seek_")
        ]
        # Exclude test_sample if there's another mp3
        user_mp3s = [f for f in mp3s_in_dir if f != "test_sample.mp3"]
        if user_mp3s:
            input_file = os.path.join(script_dir, user_mp3s[0])
            print(f"[*] Found user audio in folder: {user_mp3s[0]}")
        elif mp3s_in_dir:
            input_file = os.path.join(script_dir, mp3s_in_dir[0])
            print(f"[*] Using sample audio: {mp3s_in_dir[0]}")
        else:
            print("[!] Usage: python test_variations.py <path_to_voice.mp3>")
            input_file = input("Enter path to your voice MP3 file: ").strip().strip('"')

    if not os.path.exists(input_file):
        print(f"[ERROR] Audio file does not exist: {input_file}")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = args.output_dir or os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print(" SOUNDTOUCH SYSTEMATIC SPEECH LAB: CATEGORIZED PARAMETER SUITE")
    print(" (NO EQ | NO COMPRESSOR | PURE SOUNDTOUCH DSP PARAMETERS ONLY)")
    print("=" * 80)
    print(f"Input file    : {input_file}")
    print(f"Output folder : {output_dir}")
    print(f"Pitch shift   : {BASELINE_PITCH} semitones (Constant)")
    print("-" * 80)

    # 1. Initialize SoundTouch Engine
    st_engine = SoundTouchDLL()
    print(f"[*] Loaded SoundTouch Engine: v{st_engine.get_version()}")

    # 2. Decode Input Audio to 48kHz PCM
    print("[*] Decoding voice to 48,000 Hz 16-bit Mono PCM...")
    samples, sr, channels = load_audio_as_pcm(input_file, target_sr=48000, target_channels=1)
    duration_sec = len(samples) / sr
    print(f"[*] Ingested {len(samples)} samples ({duration_sec:.2f}s, {sr}Hz mono voice)")
    print("-" * 80)

    # Count total tracks
    total_tracks = sum(len(cat["tracks"]) for cat in CATEGORIES)
    current_count = 0

    t_start = time.time()

    # 3. Process each category and each track
    for cat in CATEGORIES:
        cat_dir = os.path.join(output_dir, cat["folder"])
        os.makedirs(cat_dir, exist_ok=True)

        print(f"\n>>> Processing {cat['title']} ({len(cat['tracks'])} files)...")

        for trk in cat["tracks"]:
            current_count += 1
            out_file = os.path.join(cat_dir, f"{trk['file_name']}.mp3")

            t0 = time.time()
            shifted_pcm = st_engine.process(
                samples,
                sample_rate=sr,
                channels=channels,
                pitch_semitones=BASELINE_PITCH,
                sequence_ms=trk["sequence_ms"],
                seekwindow_ms=trk["seekwindow_ms"],
                overlap_ms=trk["overlap_ms"],
                quickseek=trk["quickseek"],
                aa_filter=trk["aa_filter"],
                aa_filter_length=trk["aa_filter_length"]
            )

            save_pcm_as_mp3(
                shifted_pcm,
                out_file,
                sample_rate=sr,
                channels=channels,
                title=f"{trk['file_name']} ({trk['val_str']})",
                artist="SoundTouch Speech Lab",
                comment=trk["notes"]
            )
            elapsed = time.time() - t0
            print(f"  [{current_count:02d}/{total_tracks:02d}] Saved {cat['folder']}/{trk['file_name']}.mp3 ({elapsed:.2f}s) -> {trk['val_str']}")

    total_time = time.time() - t_start

    # 4. Generate Guides and HTML Player
    print("-" * 80)
    print("[*] Generating CATEGORIES_GUIDE.txt and CATEGORIES_GUIDE.md...")
    generate_guides(output_dir, base_name)

    print("[*] Generating interactive compare_player.html...")
    generate_html_player(output_dir, base_name)

    print("=" * 80)
    print(f" ALL {total_tracks} TRACKS PROCESSED IN {total_time:.2f}s!")
    print("=" * 80)
    print(f"All files saved in: {output_dir}")
    print("Open 'compare_player.html' in your browser to A/B test by category!")
    print("=" * 80)


if __name__ == "__main__":
    main()
