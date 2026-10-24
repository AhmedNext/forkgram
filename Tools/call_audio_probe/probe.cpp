// Diagnostic only: include the existing implementation to inspect its private
// filter state and FIFO without adding instrumentation to production code.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>
#include "SoundTouch.cpp"

static bool runProbe(int rate, int preset, float tempo, float pitch, int frames) {
    soundtouch_clear_call();
    soundtouch_set_vocal_preset(preset);
    soundtouch_set_tempo(tempo);
    const int block = rate / 100;
    std::vector<short> audio(block);
    int silentFrames = 0;
    int clippedSamples = 0;
    double energy = 0;
    size_t maxQueue = 0;
    for (int frame = 0; frame < frames; ++frame) {
        for (int i = 0; i < block; ++i) {
            audio[i] = static_cast<short>(8000 * std::sin(
                    6.283185307179586 * 220 * (frame * block + i) / rate));
        }
        soundtouch_process_live_call_frame(audio.data(), block, 1, rate, pitch);
        maxQueue = std::max(maxQueue, g_callFifo.size());
        // Exclude the first second, including startup latency, from signal metrics.
        if (frame >= 100) {
            if (std::all_of(audio.begin(), audio.end(), [](short v) { return v == 0; })) {
                ++silentFrames;
            }
            for (short v : audio) {
                if (std::abs(static_cast<int>(v)) >= 32760) ++clippedSamples;
                energy += static_cast<double>(v) * v;
            }
        }
    }
    const int measuredFrames = frames - 100;
    std::printf("rate=%d profile=%d note_tempo_setting=%.2f pitch=%.1f "
                "silent_frames=%d/%d rms=%.1f clipped_pct=%.2f "
                "filter_finite=%d final_queue_ms=%.1f max_queue_ms=%.1f\n",
                rate, preset, tempo, pitch, silentFrames, measuredFrames,
                std::sqrt(energy / (measuredFrames * block)),
                clippedSamples * 100.0 / (measuredFrames * block),
                std::isfinite(g_callAir.s1[0]) ? 1 : 0,
                g_callFifo.size() * 1000.0 / rate,
                maxQueue * 1000.0 / rate);
    const bool passed = std::isfinite(g_callAir.s1[0]) && silentFrames == 0
            && maxQueue * 1000.0 / rate <= 200.0;
    soundtouch_clear_call();
    return passed;
}

static bool verifyRecordingStyle() {
    // Compare the actual public recorder output with call sample processing
    // using the same SoundTouch output. This catches differences in EQ,
    // dynamics, gain and clipping without conflating real-time startup delay.
    for (int profile = 0; profile < 9; ++profile) {
        for (int gain : {-30, 0, 3}) {
            soundtouch_set_vocal_preset(profile);
            soundtouch_set_mic_gain_db(gain);
            soundtouch_set_tempo(1.0f);
            std::vector<short> input(48000), reference(48000), actual;
            for (int i = 0; i < 48000; ++i) {
                input[i] = static_cast<short>(18000 * std::sin(
                        6.283185307179586 * 220 * i / 48000));
            }
            delete g_soundTouchRecorder;
            g_soundTouchRecorder = nullptr;
            soundtouch_init_recorder(48000, -2.3f);
            soundtouch_put_samples(input.data(), static_cast<int>(input.size()));
            const int count = soundtouch_receive_samples(reference.data(), 48000);
            reference.resize(count);

            delete g_soundTouchRecorder;
            g_soundTouchRecorder = nullptr;
            soundtouch_init_recorder(48000, -2.3f);
            soundtouch_clear_call();
            apply_vocal_preset(profile, 48000, g_callHpf, g_callWarmth,
                    g_callDebox, g_callAir, g_callCompressor);
            soundtouch_put_samples(input.data(), static_cast<int>(input.size()));
            std::vector<float> raw(48000);
            const int received = g_soundTouchRecorder->receiveSamples(raw.data(), 48000);
            for (int i = 0; i < received; ++i) actual.push_back(process_call_sample(raw[i], 0));
            if (reference.empty() || reference != actual) {
                std::printf("Parity mismatch: profile=%d gain=%d notes=%zu calls=%zu\n",
                        profile, gain, reference.size(), actual.size());
                for (size_t i = 0; i < std::min(reference.size(), actual.size()); ++i) {
                    if (reference[i] != actual[i]) {
                        std::printf("First difference at %zu: note=%d call=%d\n", i, reference[i], actual[i]);
                        break;
                    }
                }
                soundtouch_set_mic_gain_db(0);
                return false;
            }
        }
    }
    soundtouch_set_mic_gain_db(0);
    std::puts("PASS: call EQ, dynamics, gain and clipping match recorder output in all 27 cases");
    return true;
}

int main() {
    int failures = verifyRecordingStyle() ? 0 : 1;
    std::puts("Normal speed: default studio profile (0) versus flat profile (5)");
    for (int rate : {8000, 16000, 32000, 48000}) {
        for (int preset : {0, 5}) {
            if (!runProbe(rate, preset, 1.0f, -2.3f, 300)) ++failures;
        }
    }
    std::puts("Calls stay at normal speed regardless of the voice-note tempo preference");
    for (float tempo : {1.0f, 0.95f, 0.90f}) {
        if (!runProbe(48000, 5, tempo, -2.3f, 3000)) ++failures;
    }
    // Exercise the no-pitch path as well as the default shifted voice.
    if (!runProbe(48000, 0, 1.0f, 0.0f, 300)) ++failures;
    std::printf("%s: %d failing checks\n", failures ? "FAIL" : "PASS", failures);
    return failures ? 1 : 0;
}
