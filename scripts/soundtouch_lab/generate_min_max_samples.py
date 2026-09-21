#!/usr/bin/env python3
"""
Generate Minimum vs Maximum Comparison Samples.
Compares the User's Maximum Settings against Absolute Minimum
and isolates each parameter's Min vs Max against the user's base.
All at -2.3 semitones (Pure SoundTouch DSP, NO EQ, NO Compression).
"""

import os
import sys
import time
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from soundtouch_engine import (
    SoundTouchDLL,
    load_audio_as_pcm,
    save_pcm_as_mp3
)

MIN_MAX_TRACKS = [
    {
        "id": "1",
        "file_name": "01_USER_MAX_ALL_PARAMETERS",
        "title": "01: YOUR SETTINGS (All Maximum)",
        "subtitle": "Seq=100ms | Seek=35ms | Overlap=18ms | QuickSeek=0 (Full) | AA=128 taps",
        "badge": "YOUR CURRENT SETTINGS",
        "badge_color": "#10b981",
        "sequence_ms": 100,
        "seekwindow_ms": 35,
        "overlap_ms": 18,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 128,
        "notes": "Your exact production settings. Maximum vowel smoothness, rock-solid deep chest voice tracking, zero buzz, and pristine studio highs."
    },
    {
        "id": "2",
        "file_name": "02_ABSOLUTE_MIN_ALL_PARAMETERS",
        "title": "02: ABSOLUTE MINIMUM (Everything at Lowest)",
        "subtitle": "Seq=20ms | Seek=4ms | Overlap=2ms | QuickSeek=1 (Coarse) | AA=OFF",
        "badge": "ABSOLUTE WORST-CASE",
        "badge_color": "#ef4444",
        "sequence_ms": 20,
        "seekwindow_ms": 4,
        "overlap_ms": 2,
        "quickseek": 1,
        "aa_filter": 0,
        "aa_filter_length": 0,
        "notes": "Opposite extreme. Robotic, buzzing vowels, pitch wobble/tremor, harsh metallic tin-can ring, and gritty unfiltered aliasing."
    },
    {
        "id": "3",
        "file_name": "03_Sequence_MIN_20ms_vs_Your_Max",
        "title": "03: SEQUENCE AT MINIMUM (20 ms)",
        "subtitle": "Seq=20ms (Min) | Seek=35ms | Overlap=8ms | QS=0 | AA=128 taps",
        "badge": "MIN SEQUENCE TEST",
        "badge_color": "#38bdf8",
        "sequence_ms": 20,
        "seekwindow_ms": 35,
        "overlap_ms": 8,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 128,
        "notes": "Your settings, but Sequence is dropped from 100ms to 20ms. Notice how consonants ('T', 'P', 'S') become razor-sharp, but vowels start to get a subtle buzzing vibration."
    },
    {
        "id": "4",
        "file_name": "04_SeekWindow_MIN_4ms_vs_Your_Max",
        "title": "04: SEEK WINDOW AT MINIMUM (4 ms)",
        "subtitle": "Seq=100ms | Seek=4ms (Min) | Overlap=18ms | QS=0 | AA=128 taps",
        "badge": "MIN SEEK WINDOW TEST",
        "badge_color": "#f59e0b",
        "sequence_ms": 100,
        "seekwindow_ms": 4,
        "overlap_ms": 18,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 128,
        "notes": "Your settings, but Seek Window is dropped from 35ms to 4ms. Notice how your deep voice loses its solid grip and starts wobbling / trembling like talking through a vibrating fan."
    },
    {
        "id": "5",
        "file_name": "05_Overlap_MIN_2ms_vs_Your_Max",
        "title": "05: OVERLAP AT MINIMUM (2 ms)",
        "subtitle": "Seq=100ms | Seek=35ms | Overlap=2ms (Min) | QS=0 | AA=128 taps",
        "badge": "MIN OVERLAP TEST",
        "badge_color": "#8b5cf6",
        "sequence_ms": 100,
        "seekwindow_ms": 35,
        "overlap_ms": 2,
        "quickseek": 0,
        "aa_filter": 1,
        "aa_filter_length": 128,
        "notes": "Your settings, but Overlap is dropped from 18ms to 2ms. Notice how the voice becomes dry, raw, and punchy. Word attacks hit immediately with zero soft crossfade."
    },
    {
        "id": "6",
        "file_name": "06_QuickSeek_COARSE_vs_Your_Max",
        "title": "06: QUICKSEEK TURNED ON (Coarse 1)",
        "subtitle": "Seq=100ms | Seek=35ms | Overlap=18ms | QuickSeek=1 (ON) | AA=128 taps",
        "badge": "QUICKSEEK COARSE TEST",
        "badge_color": "#ec4899",
        "sequence_ms": 100,
        "seekwindow_ms": 35,
        "overlap_ms": 18,
        "quickseek": 1,
        "aa_filter": 1,
        "aa_filter_length": 128,
        "notes": "Your settings, but QuickSeek is turned ON (1). Listen closely to sustained vowel bodies for a harsh, unnatural metallic sheen compared to your Track 01."
    },
    {
        "id": "7",
        "file_name": "07_AntiAlias_OFF_vs_Your_Max",
        "title": "07: ANTI-ALIAS FILTER TURNED OFF (0)",
        "subtitle": "Seq=100ms | Seek=35ms | Overlap=18ms | QuickSeek=0 | AA=OFF (Bypass)",
        "badge": "AA FILTER OFF TEST",
        "badge_color": "#64748b",
        "sequence_ms": 100,
        "seekwindow_ms": 35,
        "overlap_ms": 18,
        "quickseek": 0,
        "aa_filter": 0,
        "aa_filter_length": 0,
        "notes": "Your settings, but Anti-Alias filter is turned OFF. Notice the gritty bite and subtle folded high-frequency digital noise compared to the 128-tap studio smoothness of Track 01."
    }
]


def generate_html_player(out_dir, base_input_name):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SoundTouch: Your Settings vs Parameter Extremes</title>
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    body {{ background: #090d16; color: #e2e8f0; padding: 24px; min-height: 100vh; }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    h1 {{ font-size: 26px; font-weight: 800; color: #f8fafc; margin-bottom: 6px; }}
    .subtitle {{ color: #94a3b8; font-size: 14px; margin-bottom: 20px; }}
    .highlight {{ color: #38bdf8; font-weight: 600; }}

    /* Sticky Master Dock */
    .dock {{
        background: #131d31;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 16px 20px;
        position: sticky;
        top: 16px;
        z-index: 100;
        box-shadow: 0 10px 30px rgba(0,0,0,0.7);
        margin-bottom: 20px;
    }}
    .dock-top {{ display: flex; align-items: center; gap: 16px; margin-bottom: 10px; }}
    .play-btn {{
        background: #38bdf8; color: #090d16; font-weight: 800; border: none;
        padding: 10px 22px; border-radius: 9999px; cursor: pointer; font-size: 15px;
        transition: all 0.15s;
    }}
    .play-btn:hover {{ background: #7dd3fc; transform: scale(1.02); }}
    .track-meta {{ flex: 1; overflow: hidden; }}
    .meta-tag {{ font-size: 11px; text-transform: uppercase; color: #38bdf8; font-weight: 700; }}
    .meta-title {{ font-size: 16px; font-weight: 700; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .time-badge {{ font-family: monospace; font-size: 13px; color: #94a3b8; background: #090d16; padding: 6px 12px; border-radius: 6px; }}
    .scrubber {{ width: 100%; -webkit-appearance: none; height: 6px; border-radius: 3px; background: #1e293b; outline: none; cursor: pointer; }}
    .scrubber::-webkit-slider-thumb {{ -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%; background: #38bdf8; cursor: pointer; }}

    /* Card list */
    .card {{
        background: #101827; border: 1px solid #1e293b; border-radius: 12px;
        padding: 16px 20px; margin-bottom: 12px; cursor: pointer;
        transition: all 0.15s; display: flex; gap: 16px; align-items: center;
    }}
    .card:hover {{ border-color: #38bdf8; background: #142036; transform: translateX(4px); }}
    .card.active {{ border-color: #38bdf8; background: #142542; box-shadow: 0 0 20px rgba(56, 189, 248, 0.25); }}
    .num {{ font-size: 18px; font-weight: 800; font-family: monospace; color: #64748b; min-width: 30px; }}
    .card.active .num {{ color: #38bdf8; }}
    .card-content {{ flex: 1; }}
    .header-line {{ display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }}
    .title {{ font-size: 16px; font-weight: 700; color: #f1f5f9; }}
    .badge {{ font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 9999px; text-transform: uppercase; color: #fff; }}
    .subtitle-line {{ font-size: 13px; color: #38bdf8; font-family: monospace; margin-bottom: 6px; }}
    .notes {{ font-size: 13px; color: #94a3b8; line-height: 1.4; }}
    .listen-btn {{ background: transparent; border: 1px solid #334155; color: #e2e8f0; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }}
    .card:hover .listen-btn {{ background: #38bdf8; color: #090d16; border-color: #38bdf8; }}

    .shortcuts {{ background: #101726; border: 1px solid #1e293b; border-radius: 10px; padding: 14px 18px; margin-top: 24px; font-size: 13px; color: #94a3b8; }}
    .key {{ background: #090d16; border: 1px solid #334155; border-radius: 4px; padding: 2px 6px; font-family: monospace; color: #38bdf8; font-weight: bold; }}
</style>
</head>
<body>
<div class="container">
    <h1>SoundTouch: Your Settings vs Min/Max Extremes</h1>
    <div class="subtitle">Comparing Your Applied Production Settings (-2.3 st) Against Minimum and Maximum Extremes from <span class="highlight">{base_input_name}</span></div>

    <div class="dock">
        <div class="dock-top">
            <button class="play-btn" id="playBtn" onclick="togglePlay()"><span id="playIcon">▶</span> <span id="btnText">Play</span></button>
            <div class="track-meta">
                <div class="meta-tag" id="trackTag">Track 1 of 7</div>
                <div class="meta-title" id="trackTitle">01: YOUR SETTINGS (All Maximum)</div>
            </div>
            <div class="time-badge" id="timeDisplay">0:00 / 0:00</div>
        </div>
        <input type="range" class="scrubber" id="scrubber" min="0" max="100" value="0" step="0.1" oninput="onScrub(this.value)">
    </div>

    <audio id="audioPlayer" preload="auto"></audio>

    <div id="cardsList">
"""
    tracks_js = []
    for t in MIN_MAX_TRACKS:
        tracks_js.append({
            "id": t["id"],
            "file": f"{t['file_name']}.mp3",
            "title": t["title"],
            "tag": t["badge"],
            "notes": t["notes"]
        })
        html += f"""
        <div class="card {'active' if t['id']=='1' else ''}" id="card-{t['id']}" onclick="playTrackById('{t['id']}')">
            <div class="num">0{t['id']}</div>
            <div class="card-content">
                <div class="header-line">
                    <span class="title">{t['title']}</span>
                    <span class="badge" style="background: {t['badge_color']}">{t['badge']}</span>
                </div>
                <div class="subtitle-line">{t['subtitle']}</div>
                <div class="notes">🎧 {t['notes']}</div>
            </div>
            <button class="listen-btn">Listen</button>
        </div>
        """

    tracks_json_str = json.dumps(tracks_js)
    html += f"""
    </div>

    <div class="shortcuts">
        <strong>⚡ Instant Keyboard A/B Testing:</strong> &nbsp;
        • <span class="key">Space</span> : Play / Pause &nbsp;|&nbsp;
        • <span class="key">1</span> to <span class="key">7</span> : Instant jump between tracks at exact same timestamp &nbsp;|&nbsp;
        • <span class="key">↑</span> / <span class="key">↓</span> : Next / Previous track
    </div>
</div>

<script>
    const tracks = {tracks_json_str};
    let currentIdx = 0;
    const audio = document.getElementById('audioPlayer');
    const playBtn = document.getElementById('playBtn');
    const playIcon = document.getElementById('playIcon');
    const btnText = document.getElementById('btnText');
    const trackTag = document.getElementById('trackTag');
    const trackTitle = document.getElementById('trackTitle');
    const timeDisplay = document.getElementById('timeDisplay');
    const scrubber = document.getElementById('scrubber');

    function formatTime(s) {{
        if (isNaN(s) || s < 0) return "0:00";
        let m = Math.floor(s / 60), sec = Math.floor(s % 60);
        return m + ":" + (sec < 10 ? "0" : "") + sec;
    }}

    function playTrackByIndex(idx, autoPlay = true) {{
        if (idx < 0 || idx >= tracks.length) return;
        const prevTime = audio.currentTime || 0;
        const wasPaused = audio.paused;

        currentIdx = idx;
        const trk = tracks[idx];
        trackTag.innerText = trk.tag;
        trackTitle.innerText = trk.title;

        document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
        const el = document.getElementById('card-' + trk.id);
        if (el) el.classList.add('active');

        audio.src = trk.file;
        audio.load();
        audio.onloadedmetadata = () => {{
            audio.currentTime = Math.min(prevTime, audio.duration || 0);
            if (autoPlay && !wasPaused) audio.play();
        }};
        if (autoPlay) audio.play().catch(e => {{}});
    }}

    function playTrackById(id) {{
        const idx = tracks.findIndex(t => t.id === id);
        if (idx !== -1) playTrackByIndex(idx, true);
    }}

    function togglePlay() {{
        if (audio.paused) audio.play();
        else audio.pause();
    }}

    audio.addEventListener('play', () => {{ playIcon.innerText = "⏸"; btnText.innerText = "Pause"; }});
    audio.addEventListener('pause', () => {{ playIcon.innerText = "▶"; btnText.innerText = "Play"; }});
    audio.addEventListener('timeupdate', () => {{
        if (!isNaN(audio.duration) && audio.duration > 0) {{
            scrubber.value = (audio.currentTime / audio.duration) * 100;
            timeDisplay.innerText = formatTime(audio.currentTime) + " / " + formatTime(audio.duration);
        }}
    }});
    function onScrub(val) {{
        if (!isNaN(audio.duration) && audio.duration > 0) audio.currentTime = (val / 100) * audio.duration;
    }}

    window.addEventListener('keydown', (e) => {{
        if (e.code === 'Space') {{ e.preventDefault(); togglePlay(); }}
        else if (e.code === 'ArrowUp') {{ e.preventDefault(); playTrackByIndex((currentIdx - 1 + tracks.length) % tracks.length, true); }}
        else if (e.code === 'ArrowDown') {{ e.preventDefault(); playTrackByIndex((currentIdx + 1) % tracks.length, true); }}
        else if (e.key >= '1' && e.key <= '7') {{
            e.preventDefault();
            playTrackByIndex(parseInt(e.key) - 1, true);
        }}
    }});

    window.addEventListener('DOMContentLoaded', () => playTrackByIndex(0, false));
</script>
</body>
</html>
"""
    with open(os.path.join(out_dir, "min_max_compare.html"), "w", encoding="utf-8") as f:
        f.write(html)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "voice.mp3")
    if not os.path.exists(input_file):
        input_file = os.path.join(script_dir, "test_sample.mp3")

    out_dir = os.path.join(script_dir, "output", "MIN_MAX_SHOWDOWN")
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 75)
    print(" GENERATING MINIMUM VS MAXIMUM COMPARISON SAMPLES (-2.3 SEMITONES)")
    print("=" * 75)
    print(f"Input file  : {input_file}")
    print(f"Output dir  : {out_dir}")
    print("-" * 75)

    st = SoundTouchDLL()
    print("[*] Decoding audio to 48kHz PCM...")
    samples, sr, ch = load_audio_as_pcm(input_file, target_sr=48000, target_channels=1)

    for idx, trk in enumerate(MIN_MAX_TRACKS, 1):
        t0 = time.time()
        print(f"[{idx}/7] Generating: {trk['file_name']}.mp3 ...")
        print(f"       Seq={trk['sequence_ms']}ms | Seek={trk['seekwindow_ms']}ms | Overlap={trk['overlap_ms']}ms | QS={trk['quickseek']} | AA={trk['aa_filter']} ({trk['aa_filter_length']}t)")

        shifted = st.process(
            samples,
            sample_rate=sr,
            channels=ch,
            pitch_semitones=-2.3,
            sequence_ms=trk["sequence_ms"],
            seekwindow_ms=trk["seekwindow_ms"],
            overlap_ms=trk["overlap_ms"],
            quickseek=trk["quickseek"],
            aa_filter=trk["aa_filter"],
            aa_filter_length=trk["aa_filter_length"]
        )

        out_file = os.path.join(out_dir, f"{trk['file_name']}.mp3")
        save_pcm_as_mp3(
            shifted,
            out_file,
            sample_rate=sr,
            channels=ch,
            title=trk["title"],
            artist="SoundTouch Lab",
            comment=trk["notes"]
        )
        print(f"       -> Done in {time.time() - t0:.2f}s!")

    print("[*] Generating min_max_compare.html...")
    generate_html_player(out_dir, os.path.splitext(os.path.basename(input_file))[0])

    print("=" * 75)
    print(" ALL 7 MIN/MAX COMPARISON TRACKS GENERATED SUCCESSFULLY!")
    print(f" Location: {out_dir}")
    print(" Double click 'min_max_compare.html' to A/B test with keys 1 to 7!")
    print("=" * 75)


if __name__ == "__main__":
    main()
