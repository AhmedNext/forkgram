# Outgoing call dropouts — 2026-10-24

The user reports that outgoing voice quality is now good, but speech sometimes
cuts to complete silence and returns. The test sends the Android phone's
microphone to Telegram on Windows, heard through desktop headphones. A sudden
lighter sound near the phone microphone preceded one observed dropout.
After the 20 ms change, the user reported worse sound quality. No actual call
trace has yet established the active backend, encoder bitrate, or packet loss.

## Packetization risk at 128 kbps

The high-quality call configuration requests 128,000 bps while the legacy
private-call `MediaManager` and group sender retain 120 ms Opus packets. This
can produce packets too large for the transport. The initial synthetic test
forced the encoder to 128 kbps. It did not account for the separate 32 kbps
allocation override discovered later, so it does not establish that oversized
packets caused the reported phone-call dropouts.

For legacy private calls, RTP follows `MediaManager::SendRtp` through
`AudioDataMessage`, `Manager`, and `NetworkManager` into `EncryptedConnection`.
That connection allows a 1,452-byte outer packet and requires
`16 + serialized_message_size <= 1452`. Oversized audio is rejected locally
with `Too large packet`, before the network can deliver it. The encoder and RTP
buffer do not impose a smaller payload cap or fragment this message.

The bundled Opus encoder was compiled on Windows and tested with synthetic
signals at mono 48 kHz, VOIP mode, 128 kbps, FEC enabled, DTX disabled, and
complexity 9. Each signal runs for eight seconds:

| Packet duration | Largest payload across four signals | Synthetic speech payloads exceeding the entire 1,436-byte serialized-message budget |
| --- | ---: | ---: |
| 120 ms | 1,916 bytes | 36 / 66 |
| 60 ms | 959 bytes | 0 / 133 |
| 20 ms | 539 bytes | 0 / 400 |

For continuous sine, harmonics, and noise, all 66 packets at 120 ms measured
1,916 bytes. RTP/message headers make the actual usable payload budget smaller
than 1,436 bytes. The oversized results above therefore establish rejection
without relying on a guessed header size. Fast Ethernet or Wi-Fi does not
prevent a packet from being rejected locally.

## Follow-up: incomplete bitrate configuration

The legacy private-call and group constructors still initialized the field trial
`WebRTC-Audio-Allocation/min:32kbps,max:32kbps/`. `AudioSendStream` explicitly
applies this override over the configured bitrate range. The earlier 128 kbps
transport changes therefore did not remove every lower limit.

The codec's `x-google-start-bitrate` and `x-google-max-bitrate` parameters set
transport constraints. Opus initializes its own bitrate from `maxaveragebitrate`,
which was absent, leaving its mono full-band default at 32 kbps. This also
affected initialization in the v2 backend, although later bandwidth updates
could raise its bitrate.

The overlay now permits a 32–128 kbps allocation range in legacy/group calls
and explicitly sets `maxaveragebitrate=128000` on all three outgoing Opus
configurations. The lower bound retains bandwidth adaptation. The 128 kbps
value is a configured encoder target, not a guarantee of measured network
bitrate; transport overhead and congestion control still apply.

This change keeps the current packet durations, encoder application/complexity,
capture settings, SoundTouch, and voice-note processing. It corrects the verified
bitrate mismatch without changing additional audio-processing variables.

The follow-up synthetic check at 32 kbps, Android's default complexity 5, mono
48 kHz and VOIP mode produced no oversized packets at either 20 or 120 ms for
synthetic speech and noise. This further limits the earlier dropout diagnosis.

`python Tools/call_audio_probe/check_call_bitrates.py` applies the real overlay
to temporary copies of the pinned sources and checks the allocation bounds,
encoder bitrate units, and outgoing packet duration. Running it with
`--patch-ref 0c53f1a22` reproduces the missing-target/32 kbps configuration errors.

## Repair and validation

- The tracked tgcalls overlay now sets outgoing `ptime=20` and `maxptime=20` in
  legacy private calls and groups, retaining the 128 kbps target. The maximum
  prevents audio network adaptation from restoring long packets.
- The separate group receive descriptor stays at 120 ms; the Opus decoder reads
  each packet's actual duration. The independent v2 sender stays at its safe
  existing 60 ms packet duration.
- The source submodule remains untouched. The overlay applies cleanly to the
  pinned sources through the actual CMake working directory, including paths
  with spaces; all source-local copied-header lookups still resolve.
- SoundTouch and voice-note processing are unchanged. The native audio probe
  passes all 27 call/recorder profile-and-gain comparisons and reports no steady
  silent frames in its normal-speed scenarios.

`Tools/call_audio_probe/packet_probe.py` reproduces the packet-size difference.
It needs numpy and a prebuilt shared library compiled from this checkout's
bundled Opus. Pass that library with `--opus-library`; the script exits nonzero
if it cannot reproduce oversized 120 ms packets or 20 ms leaves insufficient
header headroom. It does not need a Telegram account or record microphone audio.

## Limits of the diagnosis

The oversized-packet risk at 128 kbps and the leftover bitrate overrides are
established. Neither establishes the cause of the user's specific interruption
or subsequent quality regression without a call trace. If the call selected v2,
the legacy packet-duration change did not change that backend. The sudden-noise
observation also does not prove that the physical microphone stopped capturing.

WebRTC noise suppression and AGC are disabled in the private-call configuration,
but echo cancellation remains enabled. Android calls also use the
`VOICE_COMMUNICATION` capture source, whereas voice notes use `DEFAULT`; device
processing may differ. Group RNNoise is separately controlled by the saved
noise-suppression setting. None of these is proven to be the cause on this phone.
Headphones reduce the likelihood of a desktop-to-phone acoustic feedback loop.
These capture settings were left unchanged pending device evidence.
