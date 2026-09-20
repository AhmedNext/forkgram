#ifndef SOUNDTOUCH_LIVE_CALL_H
#define SOUNDTOUCH_LIVE_CALL_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Process a live audio frame in-place through SoundTouch with low latency.
 *
 * @param samples Array of interleaved 16-bit PCM audio samples.
 * @param numSamples Number of samples per channel (e.g. 480 for 10ms at 48kHz).
 * @param channels Number of audio channels (1 for mono, 2 for stereo).
 * @param sampleRate Sample rate in Hz (e.g. 48000, 32000, 16000).
 * @param pitchSemitones Pitch shift in semitones (e.g. -2.3f).
 */
void soundtouch_process_live_call_frame(short *samples, int numSamples, int channels, int sampleRate, float pitchSemitones);

/**
 * Reset and release live call SoundTouch resources when a call ends.
 */
void soundtouch_clear_call(void);

/**
 * Process a round video note audio frame in-place through SoundTouch with 3-Band Vocal EQ.
 */
void soundtouch_process_video_note_frame(short *samples, int numSamples, int channels, int sampleRate, float pitchSemitones);

/**
 * Reset and release video note SoundTouch resources when recording ends.
 */
void soundtouch_clear_video_note(void);

/**
 * Enable or disable Broadcast Compressor & Warm Tube Saturation.
 */
void soundtouch_set_compressor_enabled(int enabled);

/**
 * Set global pitch shift semitones for calls, voice notes, and video notes.
 */
void soundtouch_set_pitch_semitones(float pitch);

/**
 * Get current global pitch shift semitones.
 */
float soundtouch_get_pitch_semitones(void);

/**
 * Set global vocal style preset (0: Radio, 1: Warm Podcast, 2: Studio Crystal, 3: Cinematic Deep).
 */
void soundtouch_set_vocal_preset(int preset);

/**
 * Get current global vocal style preset.
 */
int soundtouch_get_vocal_preset(void);

#ifdef __cplusplus
}
#endif

#endif // SOUNDTOUCH_LIVE_CALL_H
