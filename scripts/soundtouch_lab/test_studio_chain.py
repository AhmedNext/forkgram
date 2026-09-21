#!/usr/bin/env python3
"""
Test Previously Excluded Parameters on Top of User's Maximum SoundTouch Settings:
- User's Max SoundTouch Baseline: Seq=100ms, Seek=35ms, Overlap=18ms, QS=0, AA=128 taps, Pitch=-2.3 st
- Excluded Parameters Tested:
  1. Broadcast Vocal Soft-Knee Compressor / Leveler (Threshold -18dB, 3.5:1 ratio)
  2. Analog Vacuum Tube Triode Saturation (2nd-order warm even harmonics)
  3. High-Pass Filter (HPF / Low-cut) eliminating plosives & mic handling rumble
  4. Peaking Chest Warmth EQ (95Hz - 140Hz boost)
  5. Peaking De-Box EQ (380Hz - 450Hz mud cut)
  6. Peaking Vocal Air EQ (8kHz - 10kHz sparkle boost)
  7. The 4 Specialized Studio Vocal Presets
  8. SoundTouch Tempo / Speed stretching
"""

import os
import sys
import math
import time
import json
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from soundtouch_engine import (
    SoundTouchDLL,
    load_audio_as_pcm,
    save_pcm_as_mp3
)

# User's locked max SoundTouch parameters
USER_MAX_SEQ = 100
USER_MAX_SEEK = 35
USER_MAX_OVERLAP = 18
USER_MAX_QS = 0
USER_MAX_AA = 1
USER_MAX_AA_LEN = 128
USER_MAX_PITCH = -2.3


# =========================================================================
# Biquad Filter Implementation (Python port of SoundTouch.cpp)
# =========================================================================

class VocalBiquad:
    def __init__(self):
        self.b0 = 1.0; self.b1 = 0.0; self.b2 = 0.0
        self.a1 = 0.0; self.a2 = 0.0
        self.s1 = [0.0, 0.0]; self.s2 = [0.0, 0.0]

    def reset(self):
        self.s1 = [0.0, 0.0]; self.s2 = [0.0, 0.0]

    def set_highpass(self, sample_rate, fc, Q=0.7071):
        w0 = 2.0 * math.pi * fc / sample_rate
        cosw0 = math.cos(w0); sinw0 = math.sin(w0)
        alpha = sinw0 / (2.0 * Q)
        a0 = 1.0 + alpha
        self.b0 = ((1.0 + cosw0) / 2.0) / a0
        self.b1 = (-(1.0 + cosw0)) / a0
        self.b2 = ((1.0 + cosw0) / 2.0) / a0
        self.a1 = (-2.0 * cosw0) / a0
        self.a2 = (1.0 - alpha) / a0
        self.reset()

    def set_peaking(self, sample_rate, f0, gain_db, Q):
        A = math.pow(10.0, gain_db / 40.0)
        w0 = 2.0 * math.pi * f0 / sample_rate
        cosw0 = math.cos(w0); sinw0 = math.sin(w0)
        alpha = sinw0 / (2.0 * Q)
        a0 = 1.0 + alpha / A
        self.b0 = (1.0 + alpha * A) / a0
        self.b1 = (-2.0 * cosw0) / a0
        self.b2 = (1.0 - alpha * A) / a0
        self.a1 = (-2.0 * cosw0) / a0
        self.a2 = (1.0 - alpha / A) / a0
        self.reset()

    def process(self, x, ch=0):
        y = self.b0 * x + self.s1[ch]
        self.s1[ch] = self.b1 * x - self.a1 * y + self.s2[ch]
        self.s2[ch] = self.b2 * x - self.a2 * y
        return y


class BroadcastCompressorOnly:
    def __init__(self, sample_rate=48000.0):
        self.envelope = [0.0, 0.0]
        self.attack_alpha = math.exp(-1.0 / (sample_rate * 0.004))
        self.release_alpha = math.exp(-1.0 / (sample_rate * 0.090))

    def process(self, sample, ch=0):
        abs_in = abs(sample) / 32768.0
        if abs_in > self.envelope[ch]:
            self.envelope[ch] = self.attack_alpha * self.envelope[ch] + (1.0 - self.attack_alpha) * abs_in
        else:
            self.envelope[ch] = self.release_alpha * self.envelope[ch] + (1.0 - self.release_alpha) * abs_in

        threshold = 0.125
        gain_reduction = 1.0
        if self.envelope[ch] > threshold:
            excess = self.envelope[ch] - threshold
            gain_reduction = (threshold + excess / 3.5) / self.envelope[ch]

        # Makeup gain +2.8 dB without tube saturation
        out = sample * gain_reduction * 1.38
        return max(-32768.0, min(32767.0, out))


class TubeSaturationOnly:
    def process(self, sample):
        x = sample / 32768.0
        driven = x * 1.35
        if driven > 0.0:
            warm = driven + 0.12 * driven * driven
            sat = math.tanh(warm * 0.95)
        else:
            sat = math.tanh(driven)
        return sat * 32767.0


class FullBroadcastVocalProcessor:
    def __init__(self, sample_rate=48000.0):
        self.comp = BroadcastCompressorOnly(sample_rate)
        self.tube = TubeSaturationOnly()

    def process(self, sample, ch=0):
        c = self.comp.process(sample, ch)
        return self.tube.process(c)


def apply_eq_preset(pcm_samples, sr=48000, preset_id=0):
    float_buf = pcm_samples.astype(np.float32)
    hpf = VocalBiquad()
    warmth = VocalBiquad()
    debox = VocalBiquad()
    air = VocalBiquad()

    if preset_id == 0:  # Radio Broadcaster
        hpf.set_highpass(sr, 75.0, 0.7071)
        warmth.set_peaking(sr, 125.0, 4.0, 2.0)
        debox.set_peaking(sr, 400.0, -3.0, 1.4)
        air.set_peaking(sr, 9000.0, 2.5, 1.0)
    elif preset_id == 1:  # Warm Velvet / Podcast
        hpf.set_highpass(sr, 70.0, 0.7071)
        warmth.set_peaking(sr, 140.0, 2.8, 1.8)
        debox.set_peaking(sr, 450.0, -2.0, 1.4)
        air.set_peaking(sr, 8500.0, 1.8, 1.0)
    elif preset_id == 2:  # Studio Crystal Clarity
        hpf.set_highpass(sr, 80.0, 0.7071)
        warmth.set_peaking(sr, 110.0, 1.8, 2.0)
        debox.set_peaking(sr, 380.0, -3.5, 1.5)
        air.set_peaking(sr, 10000.0, 3.5, 1.0)
    elif preset_id == 3:  # Cinematic Deep Sub-Bass
        hpf.set_highpass(sr, 60.0, 0.7071)
        warmth.set_peaking(sr, 95.0, 5.0, 2.2)
        debox.set_peaking(sr, 420.0, -3.0, 1.4)
        air.set_peaking(sr, 8000.0, 1.5, 1.0)

    for i in range(len(float_buf)):
        s = float_buf[i]
        s = hpf.process(s, 0)
        s = warmth.process(s, 0)
        s = debox.process(s, 0)
        s = air.process(s, 0)
        float_buf[i] = s

    return float_buf


TRACKS_CONFIG = [
    {
        "id": "1",
        "file_name": "01_Base_Max_Pure_SoundTouch",
        "title": "01: Your Settings (Pure SoundTouch, Flat Baseline)",
        "feature": "PURE SOUNDTOUCH (NO EQ, NO COMP)",
        "badge": "YOUR CURRENT BASE",
        "badge_color": "#10b981",
        "tempo": 1.0,
        "eq_preset": None,
        "compressor": False,
        "tube": False,
        "desc": "Your exact max settings. Completely flat, no EQ, no dynamics. The reference point."
    },
    {
        "id": "2",
        "file_name": "02_Base_Max_Plus_Broadcast_Compressor",
        "title": "02: Your Settings + Vocal Compressor / Leveler",
        "feature": "SOFT-KNEE COMPRESSOR (RATIO 3.5:1)",
        "badge": "DYNAMIC LEVELER",
        "badge_color": "#38bdf8",
        "tempo": 1.0,
        "eq_preset": None,
        "compressor": True,
        "tube": False,
        "desc": "Levels your volume smoothly. When you talk softly, it brings you forward; when you speak loudly, it gently compresses peaks to protect the caller's ear."
    },
    {
        "id": "3",
        "file_name": "03_Base_Max_Plus_Vacuum_Tube_Saturation",
        "title": "03: Your Settings + Analog Tube Saturation",
        "feature": "TRIODE TUBE PREAMP (2ND HARMONICS)",
        "badge": "ANALOG WARMTH",
        "badge_color": "#f59e0b",
        "tempo": 1.0,
        "eq_preset": None,
        "compressor": False,
        "tube": True,
        "desc": "Emulates an expensive vacuum tube microphone preamp. Injects warm 2nd-order even harmonics that make deep chest voices sound rich, thick, and vintage."
    },
    {
        "id": "4",
        "file_name": "04_Base_Max_Plus_Compressor_And_Tube",
        "title": "04: Your Settings + Compressor + Tube Saturation",
        "feature": "FULL DYNAMICS (COMP + TUBE GLOW)",
        "badge": "STUDIO DYNAMICS",
        "badge_color": "#ec4899",
        "tempo": 1.0,
        "eq_preset": None,
        "compressor": True,
        "tube": True,
        "desc": "Combines volume leveling with analog tube saturation. Glues the voice together with radio-grade density and presence."
    },
    {
        "id": "5",
        "file_name": "05_Base_Max_Plus_Radio_Broadcaster_EQ",
        "title": "05: Your Settings + Radio Broadcaster Vocal EQ",
        "feature": "EQ: HPF 75Hz | Warmth 125Hz +4dB | De-Box -3dB | Air +2.5dB",
        "badge": "RADIO EQ PRESET",
        "badge_color": "#8b5cf6",
        "tempo": 1.0,
        "eq_preset": 0,
        "compressor": False,
        "tube": False,
        "desc": "The signature broadcast curve: cuts room rumble below 75Hz, boosts 125Hz chest weight (+4dB), scoops 400Hz cardboard boxiness (-3dB), and boosts 9kHz vocal air (+2.5dB)."
    },
    {
        "id": "6",
        "file_name": "06_Base_Max_Plus_Warm_Velvet_Podcast_EQ",
        "title": "06: Your Settings + Warm Velvet Podcast EQ",
        "feature": "EQ: HPF 70Hz | Warmth 140Hz +2.8dB | De-Box -2dB | Air +1.8dB",
        "badge": "PODCAST EQ PRESET",
        "badge_color": "#6366f1",
        "tempo": 1.0,
        "eq_preset": 1,
        "compressor": False,
        "tube": False,
        "desc": "Intimate, warm, and gentle podcast sound. Softer highs and a round low-mid presence."
    },
    {
        "id": "7",
        "file_name": "07_Base_Max_Plus_Studio_Crystal_EQ",
        "title": "07: Your Settings + Studio Crystal Clarity EQ",
        "feature": "EQ: HPF 80Hz | Warmth 110Hz +1.8dB | De-Box 380Hz -3.5dB | Air 10kHz +3.5dB",
        "badge": "CRYSTAL CLARITY EQ",
        "badge_color": "#06b6d4",
        "tempo": 1.0,
        "eq_preset": 2,
        "compressor": False,
        "tube": False,
        "desc": "Compensates for the 100ms sequence softness by boosting crisp 10kHz top-end sparkle and aggressively carving out 380Hz mud."
    },
    {
        "id": "8",
        "file_name": "08_Base_Max_Plus_Cinematic_Deep_EQ",
        "title": "08: Your Settings + Cinematic Deep Sub-Bass EQ",
        "feature": "EQ: HPF 60Hz | Warmth 95Hz +5.0dB (Sub-Bass) | De-Box -3dB | Air +1.5dB",
        "badge": "CINEMATIC BASS EQ",
        "badge_color": "#d946ef",
        "tempo": 1.0,
        "eq_preset": 3,
        "compressor": False,
        "tube": False,
        "desc": "Heavy movie-trailer chest rumble. Massive +5.0dB boost down at 95Hz fundamental frequency."
    },
    {
        "id": "9",
        "file_name": "09_Base_Max_FULL_STUDIO_CHANNEL_STRIP",
        "title": "09: Your Settings + The Complete Broadcast Channel Strip",
        "feature": "THE WORKS: Radio EQ + Compressor + Tube Saturation",
        "badge": "GOLDEN MASTER",
        "badge_color": "#eab308",
        "tempo": 1.0,
        "eq_preset": 0,
        "compressor": True,
        "tube": True,
        "desc": "The ultimate chain: SoundTouch Max (-2.3 st) -> 4-Band Radio EQ -> Soft-Knee Compressor -> Vacuum Tube Saturation."
    },
    {
        "id": "10",
        "file_name": "10_Base_Max_Relaxed_Tempo_0.95x",
        "title": "10: Your Settings + 5% Relaxed Tempo (0.95x Speed)",
        "feature": "TEMPO STRETCH: 0.95x (Pitch Locked at -2.3 st)",
        "badge": "TEMPO STRETCH",
        "badge_color": "#64748b",
        "tempo": 0.95,
        "eq_preset": None,
        "compressor": False,
        "tube": False,
        "desc": "Tests SoundTouch tempo time-stretching. Slows down your speech by 5% without changing pitch (-2.3 st), giving a very deliberate, authoritative cadence."
    }
]


def generate_html_player(out_dir, base_input_name):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SoundTouch Extras: Auditioning EQ, Compression, Tube & Tempo</title>
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    body {{ background: #090d16; color: #e2e8f0; padding: 24px; min-height: 100vh; }}
    .container {{ max-width: 940px; margin: 0 auto; }}
    h1 {{ font-size: 26px; font-weight: 800; color: #f8fafc; margin-bottom: 6px; }}
    .subtitle {{ color: #94a3b8; font-size: 14px; margin-bottom: 20px; line-height: 1.5; }}
    .highlight {{ color: #38bdf8; font-weight: 600; }}

    /* Sticky Dock */
    .dock {{
        background: #131d31; border: 1px solid #1e293b; border-radius: 14px;
        padding: 16px 20px; position: sticky; top: 16px; z-index: 100;
        box-shadow: 0 10px 30px rgba(0,0,0,0.7); margin-bottom: 20px;
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

    /* Cards */
    .card {{
        background: #101827; border: 1px solid #1e293b; border-radius: 12px;
        padding: 16px 20px; margin-bottom: 12px; cursor: pointer;
        transition: all 0.15s; display: flex; gap: 16px; align-items: center;
    }}
    .card:hover {{ border-color: #38bdf8; background: #142036; transform: translateX(4px); }}
    .card.active {{ border-color: #38bdf8; background: #142542; box-shadow: 0 0 20px rgba(56, 189, 248, 0.25); }}
    .num {{ font-size: 18px; font-weight: 800; font-family: monospace; color: #64748b; min-width: 32px; }}
    .card.active .num {{ color: #38bdf8; }}
    .card-content {{ flex: 1; }}
    .header-line {{ display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }}
    .title {{ font-size: 16px; font-weight: 700; color: #f1f5f9; }}
    .badge {{ font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 9999px; text-transform: uppercase; color: #fff; }}
    .feature-line {{ font-size: 12.5px; color: #38bdf8; font-family: monospace; margin-bottom: 6px; }}
    .notes {{ font-size: 13px; color: #94a3b8; line-height: 1.4; }}
    .listen-btn {{ background: transparent; border: 1px solid #334155; color: #e2e8f0; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }}
    .card:hover .listen-btn {{ background: #38bdf8; color: #090d16; border-color: #38bdf8; }}

    .shortcuts {{ background: #101726; border: 1px solid #1e293b; border-radius: 10px; padding: 14px 18px; margin-top: 24px; font-size: 13px; color: #94a3b8; }}
    .key {{ background: #090d16; border: 1px solid #334155; border-radius: 4px; padding: 2px 6px; font-family: monospace; color: #38bdf8; font-weight: bold; }}
</style>
</head>
<body>
<div class="container">
    <h1>SoundTouch Extras: EQ, Compressor, Tube & Tempo Lab</h1>
    <div class="subtitle">
        Auditioning the studio processing layers we previously excluded, tested on top of your locked settings:<br>
        <span class="highlight">Seq=100ms | Seek=35ms | Overlap=18ms | QuickSeek=0 (Full) | Anti-Alias=128 taps | Pitch=-2.3 st</span>
    </div>

    <div class="dock">
        <div class="dock-top">
            <button class="play-btn" id="playBtn" onclick="togglePlay()"><span id="playIcon">▶</span> <span id="btnText">Play</span></button>
            <div class="track-meta">
                <div class="meta-tag" id="trackTag">Track 1 of 10</div>
                <div class="meta-title" id="trackTitle">01: Your Settings (Pure SoundTouch, Flat Baseline)</div>
            </div>
            <div class="time-badge" id="timeDisplay">0:00 / 0:00</div>
        </div>
        <input type="range" class="scrubber" id="scrubber" min="0" max="100" value="0" step="0.1" oninput="onScrub(this.value)">
    </div>

    <audio id="audioPlayer" preload="auto"></audio>

    <div id="cardsList">
"""
    tracks_js = []
    for t in TRACKS_CONFIG:
        tracks_js.append({
            "id": t["id"],
            "file": f"{t['file_name']}.mp3",
            "title": t["title"],
            "tag": t["badge"],
            "notes": t["desc"]
        })
        num_str = f"{int(t['id']):02d}"
        html += f"""
        <div class="card {'active' if t['id']=='1' else ''}" id="card-{t['id']}" onclick="playTrackById('{t['id']}')">
            <div class="num">{num_str}</div>
            <div class="card-content">
                <div class="header-line">
                    <span class="title">{t['title']}</span>
                    <span class="badge" style="background: {t['badge_color']}">{t['badge']}</span>
                </div>
                <div class="feature-line">⚙️ {t['feature']}</div>
                <div class="notes">🎧 {t['desc']}</div>
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
        • <span class="key">1</span> to <span class="key">0</span> : Jump between tracks 1 to 10 at exact same timestamp &nbsp;|&nbsp;
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
        else if (e.key >= '1' && e.key <= '9') {{
            e.preventDefault();
            playTrackByIndex(parseInt(e.key) - 1, true);
        }} else if (e.key === '0') {{
            e.preventDefault();
            playTrackByIndex(9, true);
        }}
    }});

    window.addEventListener('DOMContentLoaded', () => playTrackByIndex(0, false));
</script>
</body>
</html>
"""
    with open(os.path.join(out_dir, "studio_extras_compare.html"), "w", encoding="utf-8") as f:
        f.write(html)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "voice.mp3")
    if not os.path.exists(input_file):
        input_file = os.path.join(script_dir, "test_sample.mp3")

    out_dir = os.path.join(script_dir, "output", "STUDIO_EXTRAS")
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 80)
    print(" TESTING PREVIOUSLY EXCLUDED PARAMETERS ON TOP OF YOUR MAX SETTINGS")
    print(" (EQ PRESETS | COMPRESSOR | ANALOG TUBE SATURATION | TEMPO)")
    print("=" * 80)
    print(f"Input file  : {input_file}")
    print(f"Output dir  : {out_dir}")
    print(f"Pitch shift : {USER_MAX_PITCH} semitones (Locked)")
    print(f"SoundTouch  : Seq={USER_MAX_SEQ}ms | Seek={USER_MAX_SEEK}ms | Ovl={USER_MAX_OVERLAP}ms | QS=0 | AA=128t")
    print("-" * 80)

    st = SoundTouchDLL()
    print("[*] Decoding input audio to 48kHz 16-bit Mono PCM...")
    samples, sr, ch = load_audio_as_pcm(input_file, target_sr=48000, target_channels=1)

    for idx, trk in enumerate(TRACKS_CONFIG, 1):
        t0 = time.time()
        print(f"[{idx:02d}/10] Generating: {trk['file_name']}.mp3 ...")
        print(f"        Tempo={trk['tempo']} | EQ={trk['eq_preset']} | Comp={trk['compressor']} | Tube={trk['tube']}")

        # Step 1: Run through SoundTouch with user's max parameters
        st_pcm = st.process(
            samples,
            sample_rate=sr,
            channels=ch,
            pitch_semitones=USER_MAX_PITCH,
            tempo=trk["tempo"],
            sequence_ms=USER_MAX_SEQ,
            seekwindow_ms=USER_MAX_SEEK,
            overlap_ms=USER_MAX_OVERLAP,
            quickseek=USER_MAX_QS,
            aa_filter=USER_MAX_AA,
            aa_filter_length=USER_MAX_AA_LEN
        )

        # Step 2: Apply EQ if configured
        processed_float = st_pcm.astype(np.float32)
        if trk["eq_preset"] is not None:
            processed_float = apply_eq_preset(st_pcm, sr=sr, preset_id=trk["eq_preset"])

        # Step 3: Apply Compressor & Tube Saturation if configured
        if trk["compressor"] and trk["tube"]:
            comp_proc = FullBroadcastVocalProcessor(sr)
            for i in range(len(processed_float)):
                processed_float[i] = comp_proc.process(processed_float[i], 0)
        elif trk["compressor"]:
            comp_only = BroadcastCompressorOnly(sr)
            for i in range(len(processed_float)):
                processed_float[i] = comp_only.process(processed_float[i], 0)
        elif trk["tube"]:
            tube_only = TubeSaturationOnly()
            for i in range(len(processed_float)):
                processed_float[i] = tube_only.process(processed_float[i])
        else:
            # Clean boost with transparent limiter
            gain = 1.15
            for i in range(len(processed_float)):
                val = processed_float[i] * gain
                if val > 30000.0:
                    val = 30000.0 + 2767.0 * math.tanh((val - 30000.0) / 2767.0)
                elif val < -30000.0:
                    val = -30000.0 + 2768.0 * math.tanh((val + 30000.0) / 2768.0)
                processed_float[i] = val

        final_pcm = np.clip(processed_float, -32768.0, 32767.0).astype(np.int16)

        out_file = os.path.join(out_dir, f"{trk['file_name']}.mp3")
        save_pcm_as_mp3(
            final_pcm,
            out_file,
            sample_rate=sr,
            channels=ch,
            title=trk["title"],
            artist="SoundTouch Studio Lab",
            comment=trk["desc"]
        )
        print(f"        -> Done in {time.time() - t0:.2f}s!")

    print("[*] Generating studio_extras_compare.html...")
    generate_html_player(out_dir, os.path.splitext(os.path.basename(input_file))[0])

    print("=" * 80)
    print(" ALL 10 STUDIO EXTRAS TRACKS GENERATED SUCCESSFULLY!")
    print(f" Location: {out_dir}")
    print(" Double click 'studio_extras_compare.html' to A/B test with keys 1 to 0!")
    print("=" * 80)


if __name__ == "__main__":
    main()
