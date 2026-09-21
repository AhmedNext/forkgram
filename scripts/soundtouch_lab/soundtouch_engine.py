"""
SoundTouch Pure Speech DSP Engine.
Interfaces directly with SoundTouchDLL_x64.dll.
NO EQ, NO COMPRESSOR - 100% Pure SoundTouch algorithmic parameter processing.
"""

import os
import sys
import ctypes
import subprocess
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
        self.lib.soundtouch_getSetting.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.lib.soundtouch_getSetting.restype = ctypes.c_int
        
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
                quickseek=0, aa_filter=1, aa_filter_length=64):
        """
        Processes an int16 numpy array through pure SoundTouch with custom algorithmic parameters.
        NO EQ, NO Compressor, NO coloration.
        """
        handle = self.lib.soundtouch_createInstance()
        try:
            self.lib.soundtouch_setChannels(handle, channels)
            self.lib.soundtouch_setSampleRate(handle, sample_rate)
            self.lib.soundtouch_setPitchSemiTones(handle, pitch_semitones)
            self.lib.soundtouch_setTempo(handle, tempo)
            
            self.lib.soundtouch_setSetting(handle, SETTING_USE_AA_FILTER, int(aa_filter))
            if aa_filter_length > 0:
                self.lib.soundtouch_setSetting(handle, SETTING_AA_FILTER_LENGTH, int(aa_filter_length))
            self.lib.soundtouch_setSetting(handle, SETTING_USE_QUICKSEEK, int(quickseek))
            self.lib.soundtouch_setSetting(handle, SETTING_SEQUENCE_MS, int(sequence_ms))
            self.lib.soundtouch_setSetting(handle, SETTING_SEEKWINDOW_MS, int(seekwindow_ms))
            self.lib.soundtouch_setSetting(handle, SETTING_OVERLAP_MS, int(overlap_ms))

            total_input_samples = len(samples_int16) // channels
            chunk_size = 4800  # 100ms chunks for smooth feeding
            out_blocks = []
            
            # Feed samples in chunks
            for offset in range(0, total_input_samples, chunk_size):
                curr_samples = min(chunk_size, total_input_samples - offset)
                chunk_ptr = ctypes.cast(
                    ctypes.byref(samples_int16.ctypes.data_as(ctypes.POINTER(ctypes.c_short)).contents, offset * channels * 2),
                    ctypes.POINTER(ctypes.c_short)
                )
                self.lib.soundtouch_putSamples_i16(handle, chunk_ptr, curr_samples)
                
                # Receive processed samples
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

            # Flush final samples
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


def save_pcm_as_mp3(samples_int16, output_path, sample_rate=48000, channels=1, title="", artist="SoundTouch Speech Lab", comment=""):
    """
    Encodes int16 PCM array to broadcast-quality 320 kbps MP3 using FFmpeg with ID3 tags.
    Pure raw output without any volume normalization or filtering.
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
        "-metadata", f"album=SoundTouch Speech Variations",
        "-metadata", f"comment={comment}",
        output_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate(input=samples_int16.tobytes())
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg encoding failed: {stderr_data.decode('utf-8', errors='ignore')}")
