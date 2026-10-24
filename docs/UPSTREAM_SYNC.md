# Forkgram update — 2026-10-24

The repository was cloned into `D:\Development\telegram-soundtouch` from
`https://github.com/AhmedNext/forkgram.git`, branch `dev`.

- Original fork: `2521942630` (Telegram version 12.10.4).
- Upstream: `https://github.com/forkgram/TelegramAndroid.git`, branch `dev`.
- Integrated upstream revision: `97371ac75be9a1660d5c249d8beedd6883b66241`,
  `[Optional] 13.0.5.`
- Backup branch: `backup/pre-upstream-sync-2026-10-24`.

The histories had diverged (273 commits on the fork side and 285 on the upstream
side), including rewritten historical Forkgram commits. To avoid carrying stale
versions of upstream features through artificial conflicts, the final tree uses
the current upstream code plus the fork's actual customization delta: the 27
commits after its last unmodified Forkgram revision, `55db14e02`.
The merge retains both histories.

Preserved customizations include SoundTouch, the nine vocal profiles, pitch,
voice-note tempo, microphone gain, 128 kbps voice notes, video-note processing,
the audio lab, custom app configuration and the ARM64 debug workflow.

## Native call-engine migration

Upstream moved tgcalls into a pinned submodule. The fork's modifications to the
old vendored tgcalls files are now stored in
`TMessagesProj/jni/soundtouch/patches/tgcalls-audio.patch`.

At CMake configuration time, the three affected source files are copied into the
build directory and patched there. The build compiles those copies and keeps
the upstream submodule clean. The patch was checked against the pinned tgcalls
revision `03d7b8662512af7528f476c02094862c1a37177d`.

The requested call-quality changes and their validation are described in
`CALL_AUDIO_FINDINGS.md`. The voice-note recorder remains on its original
SoundTouch-compatible path because upstream's new recorder bypasses that DSP.
Porting the new recorder is separate work; the current migration preserves the
existing recording sound.

## Validation

- Native call diagnostics compiled and ran with MSVC on Windows x64.
- Call processing versus voice-note conversion: all 27 comparisons passed.
- Original versus updated 48 kHz voice-note PCM: all 27 fingerprints matched.
- Call filter stability and normal-speed queue checks passed.
- The native overlay patch applied successfully to clean copies of the pinned
  upstream files; the tgcalls submodule remained unmodified.
- All 20 top-level submodules were downloaded at their pinned revisions.
  OpenH264's source checkout excludes its `res/` sample videos and `testbin/`
  binaries; those fixtures are not required to build the library. To retrieve
  them later, run `git -C TMessagesProj/jni/third_party/openh264 sparse-checkout disable`.
- No full APK build or real-device call test was possible without Java and the
  Android SDK/NDK.

## Future upstream updates

The `upstream` remote tracks Forkgram's `dev` branch. Update with:

```sh
git fetch upstream
git merge upstream/dev
git submodule update --init --recursive
```

Check the native patch after tgcalls changes and run the standalone diagnostic:

```sh
cmake -S Tools/call_audio_probe -B build/call_audio_probe
cmake --build build/call_audio_probe --config Release
```

Run `call_audio_probe` from the build output, then perform an Android build and
a real call test. Future updates are not automatic. Changes in this session are
local; nothing was pushed to GitHub.
