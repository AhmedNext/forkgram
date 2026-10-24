"""Compare live-call Opus packet sizes using a prebuilt bundled Opus library.

Requires numpy. Example:
    python packet_probe.py --opus-library /absolute/path/to/opus.dll

This is a synthetic codec diagnostic, not a phone or network call test.
"""
import argparse
import ctypes as C
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opus-library", required=True, type=Path)
    args = parser.parse_args()
    lib = C.CDLL(str(args.opus_library.resolve()))
    lib.opus_encoder_create.argtypes = [C.c_int, C.c_int, C.c_int, C.POINTER(C.c_int)]
    lib.opus_encoder_create.restype = C.c_void_p
    lib.opus_encoder_destroy.argtypes = [C.c_void_p]
    lib.opus_encode.argtypes = [C.c_void_p, C.POINTER(C.c_int16), C.c_int,
                               C.POINTER(C.c_ubyte), C.c_int]
    lib.opus_encode.restype = C.c_int
    lib.opus_encoder_ctl.argtypes = [C.c_void_p, C.c_int, C.c_int]
    lib.opus_encoder_ctl.restype = C.c_int

    rate = 48000
    bitrate = 128000
    # EncryptedConnection: 1500-byte full packet - 48 outer bytes - 16 auth bytes.
    # RTP and message headers also consume this budget. A payload alone above
    # this limit is necessarily rejected, regardless of those header lengths.
    serialized_budget = 1500 - 48 - 16
    rng = np.random.default_rng(42)
    t = np.arange(rate * 8) / rate
    signals = {
        "sine": np.sin(t * 2 * np.pi * 220) * 8000,
        "multi_harmonic": sum(np.sin(t * 2 * np.pi * 180 * i) / i
                              for i in range(1, 20)) * 6000,
        "noise": rng.normal(0, 4000, t.size),
        "speech_envelope_synthetic": sum(
            np.sin(t * 2 * np.pi * (115 + 4 * np.sin(2 * np.pi * 1.2 * t)) * i) / i
            for i in range(1, 35)) * 6000 * (np.sin(2 * np.pi * 3 * t) > -.2),
    }
    results = []
    for ptime in (20, 60, 120):
        frame = rate * ptime // 1000
        # AudioEncoderOpusImpl::SufficientOutputBufferSize, not an MTU clamp.
        capacity = 2 * ptime * (bitrate // 8000 + 1)
        for name, signal in signals.items():
            pcm = np.ascontiguousarray(np.clip(signal, -32768, 32767).astype(np.int16))
            error = C.c_int()
            encoder = lib.opus_encoder_create(rate, 1, 2048, C.byref(error))  # VOIP
            if not encoder or error.value != 0:
                raise RuntimeError(f"opus_encoder_create failed: {error.value}")
            try:
                # Bitrate, in-band FEC, DTX off, complexity. VBR is the default.
                for key, value in ((4002, bitrate), (4012, 1), (4016, 0), (4010, 9)):
                    if lib.opus_encoder_ctl(encoder, key, value) != 0:
                        raise RuntimeError(f"opus_encoder_ctl failed: {key}")
                out = (C.c_ubyte * capacity)()
                sizes = []
                for offset in range(0, len(pcm) - frame + 1, frame):
                    size = lib.opus_encode(
                        encoder, pcm[offset:].ctypes.data_as(C.POINTER(C.c_int16)),
                        frame, out, capacity)
                    if size <= 0:
                        raise RuntimeError(f"opus_encode failed: {size}")
                    sizes.append(size)
                result = {
                    "ptime_ms": ptime, "signal": name, "packets": len(sizes),
                    "min_bytes": min(sizes), "max_bytes": max(sizes),
                    "payload_exceeds_serialized_budget": sum(
                        size > serialized_budget for size in sizes),
                }
                results.append(result)
                print(json.dumps(result))
            finally:
                lib.opus_encoder_destroy(encoder)

    if not any(r["payload_exceeds_serialized_budget"] for r in results
               if r["ptime_ms"] == 120):
        raise RuntimeError("120 ms oversized-packet regression was not reproduced")
    if any(r["max_bytes"] > 1200 for r in results if r["ptime_ms"] == 20):
        raise RuntimeError("20 ms packets did not leave sufficient header headroom")
    print("PASS: reproduced oversized 120 ms audio; 20 ms leaves header headroom")


if __name__ == "__main__":
    main()
