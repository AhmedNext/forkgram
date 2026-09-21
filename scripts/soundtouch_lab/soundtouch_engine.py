"""
SoundTouch & Vocal DSP Engine for Testing & Parameter Exploration.
Directly interfaces with SoundTouchDLL_x64.dll and implements
Telegram's 4-band Studio EQ Presets, Broadcast Compressor, and Tube Saturation.
"""

import os
import sys
import ctypes
import subprocess
import math
import numpy as np

# Setting IDs from SoundTouch.h
SETTING_USE_AA_FILTER = 0
SETTING_AA_FILTER_LENGTH = 1
SETTING_USE_QUICKSEEK = 2
SETTING_SEQUENCE_MS = 3
SETTING_SEEKWINDOW_MS = 4
SETTING_OVERLAP_MS = 5

class SoundTouchDLL:
    def __init__(self, dll_path=None):
        if dll_path is None:
            dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SoundTouchDLL_x64.dll")
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"SoundTouch DLL not found at: {dll_path}")
        
        self.lib = ctypes.CDLL(dll_path)
        
        # Function signatures
        self.lib.soundtouch_getVersionString.restype = ctypes.c_char_p
        self.lib.soundtouch_createInstance.restype = ctypes.c_void_p
        self.lib.soundtouch_destroyInstance.argtypes = [ctypes.c_void_p]
        
        self.lib.soundtouch_setChannels.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        self.lib.soundtouch_setChannels.restype = ctypes.c_int
        
        self.lib.soundtouch_setSampleRate.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        self.lib.soundtouch_setSampleRate.restype = ctypes.c_int
        
        self.lib.soundtouch_setPitchSemiTones.argtypes = [ctypes.c_void_p, ctypes.c_float]
        self.lib.soundtouch_setTempo.argtypes = [ctypes.c_void_p, ctypes.c_float]
        self.lib.soundtouch_setRate.argtypes = [ctypes.c_void_p, ctypes.c_float]
        
        self.lib.soundtouch_setSetting.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        self.lib.soundtouch_setSetting.restype = ctypes.c_int
        
        self.lib.soundtouch_putSamples_i16.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_short), ctypes.c_uint]
        self.lib.soundtouch_receiveSamples_i16.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_short), ctypes.c_uint]
        self.lib.soundtouch_receiveSamples_i16.restype = ctypes.c_uint
        
        self.lib.soundtouch_numSamples.argtypes = [ctypes.c_void_p]
        self.lib.soundtouch_numSamples.restype = ctypes.c_uint
        
        self.lib.soundtouch_flush.argtypes = [ctypes.c_void_p]
        self.lib.soundtouch_flush.restype = ctypes.c_int
        
        self.lib.soundtouch_clear.argtypes = [ctypes.c_void_p]

    def get_version(self):
        return self.lib.soundtouch_getVersionString().decode("utf-8")

    def process(self, samples_int16, sample_rate=48000, channels=1, pitch_semitones=-2.3,
                tempo=1.0, sequence_ms=40, seekwindow_ms=15, overlap_ms=8,
                quickseek=0, aa_filter=1):
        """
        Process an int16 numpy array through SoundTouch with custom settings.
        """
        handle = self.lib.soundtouch_createInstance()
        try:
            self.lib.soundtouch_setChannels(handle, channels)
            self.lib.soundtouch_setSampleRate(handle, sample_rate)
            self.lib.soundtouch_setPitchSemiTones(handle, pitch_semitones)
            self.lib.soundtouch_setTempo(handle, tempo)
            
            self.lib.soundtouch_setSetting(handle, SETTING_USE_AA_FILTER, int(aa_filter))
            self.lib.soundtouch_setSetting(handle, SETTING_USE_QUICKSEEK, int(quickseek))
            self.lib.soundtouch_setSetting(handle, SETTING_SEQUENCE_MS, int(sequence_ms))
            self.lib.soundtouch_setSetting(handle, SETTING_SEEKWINDOW_MS, int(seekwindow_ms))
            self.lib.soundtouch_setSetting(handle, SETTING_OVERLAP_MS, int(overlap_ms))

            total_input_samples = len(samples_int16) // channels
            chunk_size = 4800  # 100ms chunks for smooth feeding
            out_blocks = []
            
            c_samples = samples_int16.ctypes.data_as(ctypes.POINTER(ctypes.c_short))
            
            # Feed in chunks
            for offset in range(0, total_input_samples, chunk_size):
                curr_samples = min(chunk_size, total_input_samples - offset)
                chunk_ptr = ctypes.cast(
                    ctypes.byref(samples_int16.ctypes.data_as(ctypes.POINTER(ctypes.c_short)).contents, offset * channels * 2),
                    ctypes.POINTER(ctypes.c_short)
                )
                self.lib.soundtouch_putSamples_i16(handle, chunk_ptr, curr_samples)
                
                # Receive available samples
                while True:
                    avail = self.lib.soundtouch_numSamples(handle)
                    if avail == 0:
                        break
                    temp_buf = np.zeros(avail * channels, dtype=np.int16)
                    rec = self.lib.soundtouch_receiveSamples_i16(handle, temp_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_short)), avail)
                    if rec > 0:
                        out_blocks.append(temp_buf[:rec * channels])
                    else:
                        break

            # Flush remaining
            self.lib.soundtouch_flush(handle)
            while True:
                avail = self.lib.soundtouch_numSamples(handle)
                if avail == 0:
                    break
                temp_buf = np.zeros(avail * channels, dtype=np.int16)
                rec = self.lib.soundtouch_receiveSamples_i16(handle, temp_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_short)), avail)
                if rec > 0:
                    out_blocks.append(temp_buf[:rec * channels])
                else:
                    break

            if out_blocks:
                return np.concatenate(out_blocks)
            else:
                return np.array([], dtype=np.int16)

        finally:
            self.lib.soundtouch_destroyInstance(handle)


# =========================================================================
# Telegram Vocal Biquad Filters (Direct Python Port of SoundTouch.cpp)
# =========================================================================

class VocalBiquad:
    def __init__(self):
        self.b0 = 1.0
        self.b1 = 0.0
        self.b2 = 0.0
        self.a1 = 0.0
        self.a2 = 0.0
        self.s1 = [0.0, 0.0]
        self.s2 = [0.0, 0.0]

    def reset(self):
        self.s1 = [0.0, 0.0]
        self.s2 = [0.0, 0.0]

    def set_highpass(self, sample_rate, fc, Q=0.7071):
        w0 = 2.0 * math.pi * fc / sample_rate
        cosw0 = math.cos(w0)
        sinw0 = math.sin(w0)
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
        cosw0 = math.cos(w0)
        sinw0 = math.sin(w0)
        alpha = sinw0 / (2.0 * Q)
        a0 = 1.0 + alpha / A
        self.b0 = (1.0 + alpha * A) / a0
        self.b1 = (-2.0 * cosw0) / a0
        self.b2 = (1.0 - alpha * A) / a0
        self.a1 = (-2.0 * cosw0) / a0
        self.a2 = (1.0 - alpha / A) / a0
        self.reset()

    def process(self, x, ch):
        y = self.b0 * x + self.s1[ch]
        self.s1[ch] = self.b1 * x - self.a1 * y + self.s2[ch]
        self.s2[ch] = self.b2 * x - self.a2 * y
        return y


class BroadcastVocalProcessor:
    def __init__(self, sample_rate=48000.0):
        self.sample_rate = sample_rate
        self.envelope = [0.0, 0.0]
        self.attack_alpha = math.exp(-1.0 / (sample_rate * 0.004))
        self.release_alpha = math.exp(-1.0 / (sample_rate * 0.090))

    def reset(self):
        self.envelope = [0.0, 0.0]

    def process_sample(self, sample, ch):
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

        comp_sample = sample * gain_reduction * 1.38

        # Analog triode tube saturation
        x = comp_sample / 32768.0
        driven = x * 1.25
        if driven > 0.0:
            warm = driven + 0.10 * driven * driven
            saturated = math.tanh(warm * 0.95)
        else:
            saturated = math.tanh(driven)

        return saturated * 32767.0


def apply_vocal_chain(samples_int16, sample_rate=48000, channels=1, preset_id=None, compressor_enabled=False):
    """
    Applies Telegram's 4-band Studio EQ presets and Broadcast Tube Saturation.
    """
    if preset_id is None and not compressor_enabled:
        # Clean / flat bypass
        return samples_int16

    num_samples = len(samples_int16) // channels
    float_buf = samples_int16.astype(np.float32)

    if preset_id is not None:
        hpf = VocalBiquad()
        warmth = VocalBiquad()
        debox = VocalBiquad()
        air = VocalBiquad()

        if preset_id == 0:  # Radio Broadcaster
            hpf.set_highpass(sample_rate, 75.0, 0.7071)
            warmth.set_peaking(sample_rate, 125.0, 4.0, 2.0)
            debox.set_peaking(sample_rate, 400.0, -3.0, 1.4)
            air.set_peaking(sample_rate, 9000.0, 2.5, 1.0)
        elif preset_id == 1:  # Warm Velvet / Podcast
            hpf.set_highpass(sample_rate, 70.0, 0.7071)
            warmth.set_peaking(sample_rate, 140.0, 2.8, 1.8)
            debox.set_peaking(sample_rate, 450.0, -2.0, 1.4)
            air.set_peaking(sample_rate, 8500.0, 1.8, 1.0)
        elif preset_id == 2:  # Studio Crystal
            hpf.set_highpass(sample_rate, 80.0, 0.7071)
            warmth.set_peaking(sample_rate, 110.0, 1.8, 2.0)
            debox.set_peaking(sample_rate, 380.0, -3.5, 1.5)
            air.set_peaking(sample_rate, 10000.0, 3.5, 1.0)
        elif preset_id == 3:  # Cinematic Deep
            hpf.set_highpass(sample_rate, 60.0, 0.7071)
            warmth.set_peaking(sample_rate, 95.0, 5.0, 2.2)
            debox.set_peaking(sample_rate, 420.0, -3.0, 1.4)
            air.set_peaking(sample_rate, 8000.0, 1.5, 1.0)

        for i in range(num_samples):
            for ch in range(min(channels, 2)):
                idx = i * channels + ch
                s = float_buf[idx]
                s = hpf.process(s, ch)
                s = warmth.process(s, ch)
                s = debox.process(s, ch)
                s = air.process(s, ch)
                float_buf[idx] = s

    if compressor_enabled:
        comp = BroadcastVocalProcessor(sample_rate)
        for i in range(num_samples):
            for ch in range(min(channels, 2)):
                idx = i * channels + ch
                float_buf[idx] = comp.process_sample(float_buf[idx], ch)
    else:
        # Clean broadcast boost with transparent soft limiting
        gain = 1.15
        for i in range(len(float_buf)):
            val = float_buf[i] * gain
            if val > 30000.0:
                val = 30000.0 + 2767.0 * math.tanh((val - 30000.0) / 2767.0)
            elif val < -30000.0:
                val = -30000.0 + 2768.0 * math.tanh((val + 30000.0) / 2768.0)
            float_buf[i] = val

    float_buf = np.clip(float_buf, -32768.0, 32767.0)
    return float_buf.astype(np.int16)


# =========================================================================
# Audio File Conversion Helpers (using FFmpeg)
# =========================================================================

def load_audio_as_pcm(input_path, target_sr=48000, target_channels=1):
    """
    Decodes input audio file (MP3, WAV, M4A, etc.) to int16 PCM array using FFmpeg.
    """
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", input_path,
        "-f", "s16le",
        "-ar", str(target_sr),
        "-ac", str(target_channels),
        "-"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg decoding failed: {stderr_data.decode('utf-8', errors='ignore')}")
    
    samples = np.frombuffer(stdout_data, dtype=np.int16)
    return samples, target_sr, target_channels


def save_pcm_as_mp3(samples_int16, output_path, sample_rate=48000, channels=1, title="", artist="Telegram Voice Lab", comment=""):
    """
    Encodes int16 PCM array to broadcast-quality 320 kbps MP3 using FFmpeg with ID3 tags.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "s16le",
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-i", "-",
        "-codec:a", "libmp3lame",
        "-b:a", "320k",
        "-metadata", f"title={title}",
        "-metadata", f"artist={artist}",
        "-metadata", f"album=SoundTouch Tuning Lab",
        "-metadata", f"comment={comment}",
        output_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate(input=samples_int16.tobytes())
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg encoding failed: {stderr_data.decode('utf-8', errors='ignore')}")
