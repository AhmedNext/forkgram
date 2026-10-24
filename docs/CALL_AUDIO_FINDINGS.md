# Outgoing call audio investigation — 2026-10-24

The reported problem is the user's voice sounding bad to the other person in
live calls. Voice notes already sound right and must retain their sound. After
the initial investigation, the user requested: "make them like voicenotes".
The fixes below were applied following that instruction.

## Confirmed defect at normal speed

The existing SoundTouch studio profiles include EQ, compression and tube
saturation. These effects were already present in the fork, including the
recording path; they were not introduced by the upstream update.

In `TMessagesProj/jni/soundtouch/SoundTouch.cpp`, the default profile configures
the air EQ at 9,000 Hz without validating the current sample rate.
`VocalBiquad::setPeaking` calculates coefficients directly from that frequency.
At 16,000 samples/second, 9,000 Hz exceeds the 8,000 Hz Nyquist frequency. The
resulting filter is unstable: its internal state grows until it becomes
non-finite. The final conversion to PCM cannot recover the original voice.

A native diagnostic compiled from the existing, unchanged SoundTouch source
reproduced this at **normal tempo, 1.00x**, with the existing default -2.3 semitone
pitch setting. The input was a continuous 220 Hz sine wave, 8,000 peak PCM
amplitude, mono, in the 10 ms blocks used by WebRTC. After excluding the first
second:

| Sample rate | Profile | Result |
| --- | --- | --- |
| 16 kHz | Default studio / The Works | Non-finite filter state; output was entirely silence in this Windows diagnostic |
| 16 kHz | Pure Flat | Finite state; RMS about 6,506; no silent frames |
| 32 kHz | Default studio / The Works | Finite state; RMS about 6,556; no silent frames |
| 48 kHz | Default studio / The Works | Finite state; RMS about 6,556; no silent frames |

The precise audible result of invalid floating-point values can differ by
compiler/platform. The unstable coefficients are the underlying defect; the
Windows silence result is not a claim about exactly what Android outputs.

The call transport selects its processing rate from capture and encoder rates
in `InitializeCaptureFrame` in
`TMessagesProj/jni/voip/webrtc/audio/audio_transport_impl.cc`. It passes the actual
frame rate to the SoundTouch call bridge. The original voice recorder uses
48 kHz. This rate difference can therefore explain why the same profile works
for voice notes but fails on some call configurations.

**Not yet established:** the sample rate and route used during an actual bad
call on the user's phone. Without a call trace or controlled device reproduction,
this remains a confirmed code defect and a plausible explanation, not a proven
diagnosis of every reported bad call. At 48 kHz and normal tempo, this synthetic
test did not reproduce ongoing silence or clipping.

## Additional findings before the fixes

- **The 128 kbps change is incomplete for calls.** The codec configuration was
  raised, but `MediaManager::getMaxAudioBitrate()` still returns 32,000 bps, or
  16,000 bps with data saving; `adjustBitratePreferences` passes those limits to
  the send transport. Its post-video audio branch also sets a 32,000 bps maximum.
  The group-call audio-only transport likewise retains a 32,000 bps budget.
  These limits already existed in the user's original fork. Raising codec
  settings alone does not establish a 128 kbps end-to-end call. This is another
  concrete difference from the 128 kbps voice-note encoder; actual bitrate and
  the active backend still need device verification.
- Noise suppression, automatic gain control and WebRTC's high-pass filter are
  explicitly disabled in multiple layers. That can expose room noise and uneven
  microphone levels, but it is not proof of the reported failure.
- Pitch shifting is enabled by default at -2.3 semitones. The call bridge uses
  100 ms sequences, a 35 ms seek window, an 18 ms overlap and 160 ms of priming
  silence. The diagnostic observed 160 ms of startup silence at normal tempo.
- The original normal tempo is **1.00x**. No tempo adjustment is necessary to
  obtain normal speech. The existing optional 0.95x and 0.90x settings build a
  growing call-audio queue: about 1.17 seconds and 2.95 seconds respectively
  after 30 seconds in the diagnostic. This does not explain bad calls when the
  user's tempo is 1.00x.
- A call is a real-time codec/network path; voice-note playback is a local/file
  path. A higher configured bitrate alone does not make their output identical.

## Changes applied

- Call capture is resampled to 48 kHz before WebRTC/SoundTouch processing, matching
  the voice-note processing rate. The negotiated codec can still resample for
  transmission.
- Call EQ, dynamics, microphone gain and final soft clipping now match the
  voice-note conversion. Independent filter state remains per call/recorder.
- Calls always use normal 1.00x tempo, irrespective of the voice-note tempo
  preference. The existing pitch and selected vocal profile are preserved.
- Peaking filter frequencies are constrained below Nyquist as a defensive guard.
  This changes no coefficients in the 48 kHz voice-note profiles.
- The migrated MediaManager, group-call and v2 backend patches now request a
  128,000 bps audio ceiling, with a 128,000 bps starting target where configured.
  This replaces the previous 16/32 kbps transport ceilings, including the
  MediaManager data-saving ceiling. Congestion control and peer negotiation can
  still reduce actual network bitrate.
- The original SoundTouch voice-note recording path remains selected. The new
  upstream recorder does not yet invoke this fork's SoundTouch bridge, so enabling
  it would silently lose the user's desired recording sound.

## Validation and remaining limits

- The previously failing 16 kHz default-profile diagnostic now produces finite,
  non-silent output. Tests at 8, 16, 32 and 48 kHz pass.
- Call sample processing matches the actual recorder sample conversion exactly
  for all nine profiles at -30, 0 and +3 dB: 27 comparisons passed.
- A separate before/after comparison against the original fork's recorder at
  48 kHz produced identical PCM fingerprints in all 27 profile/gain cases.
- The call queue stays below 200 ms in the diagnostic, including when a saved
  voice-note tempo preference is 0.95x or 0.90x. Calls remain at normal speed.
- These are native desktop diagnostics, not an Android call or listening test.
  Microphone routing, Android's capture effects, codec negotiation, the other
  participant's device and network conditions still affect the final sound.
- The existing pitch-shifter still introduces startup/buffering latency. Matching
  processing does not make a live network call byte-identical to a voice-note
  file.
- A complete APK build was unavailable on this machine: no Java runtime or
  Android SDK/NDK is installed. `gradlew.bat --version` stops at missing Java.

## Reproduction

`Tools/call_audio_probe` is a standalone native diagnostic. It does not modify
production code and does not require Android or a Telegram account:

```sh
cmake -S Tools/call_audio_probe -B build/call_audio_probe
cmake --build build/call_audio_probe --config Release
```

Run the resulting `call_audio_probe` executable (under `Release/` for Visual
Studio generators). The source was also compiled and run directly with MSVC
19.44 on Windows x64 during this investigation. The executable returns nonzero
if any check fails. CPU-specific x86 SIMD is disabled in this diagnostic.
