//////////////////////////////////////////////////////////////////////////////
///
/// SoundTouch - main class for tempo/pitch/rate adjusting routines.
///
/// Notes:
/// - Initialize the SoundTouch object instance by setting up the sound stream
///   parameters with functions 'setSampleRate' and 'setChannels', then set
///   desired tempo/pitch/rate settings with the corresponding functions.
///
/// - The SoundTouch class behaves like a first-in-first-out pipeline: The
///   samples that are to be processed are fed into one of the pipe by calling
///   function 'putSamples', while the ready processed samples can be read
///   from the other end of the pipeline with function 'receiveSamples'.
///
/// - The SoundTouch processing classes require certain sized 'batches' of
///   samples in order to process the sound. For this reason the classes buffer
///   incoming samples until there are enough of samples available for
///   processing, then they carry out the processing step and consequently
///   make the processed samples available for outputting.
///
/// - For the above reason, the processing routines introduce a certain
///   'latency' between the input and output, so that the samples input to
///   SoundTouch may not be immediately available in the output, and neither
///   the amount of outputtable samples may not immediately be in direct
///   relationship with the amount of previously input samples.
///
/// - The tempo/pitch/rate control parameters can be altered during processing.
///   Please notice though that they aren't currently protected by semaphores,
///   so in multi-thread application external semaphore protection may be
///   required.
///
/// - This class utilizes classes 'TDStretch' for tempo change (without modifying
///   pitch) and 'RateTransposer' for changing the playback rate (that is, both
///   tempo and pitch in the same ratio) of the sound. The third available control
///   'pitch' (change pitch but maintain tempo) is produced by a combination of
///   combining the two other controls.
///
/// Author        : Copyright (c) Olli Parviainen
/// Author e-mail : oparviai 'at' iki.fi
/// SoundTouch WWW: http://www.surina.net/soundtouch
///
////////////////////////////////////////////////////////////////////////////////
//
// License :
//
//  SoundTouch audio processing library
//  Copyright (c) Olli Parviainen
//
//  This library is free software; you can redistribute it and/or
//  modify it under the terms of the GNU Lesser General Public
//  License as published by the Free Software Foundation; either
//  version 2.1 of the License, or (at your option) any later version.
//
//  This library is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//  Lesser General Public License for more details.
//
//  You should have received a copy of the GNU Lesser General Public
//  License along with this library; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//
////////////////////////////////////////////////////////////////////////////////

#include <assert.h>
#include <stdlib.h>
#include <memory.h>
#include <math.h>
#include <stdio.h>

#include "SoundTouch.h"
#include "TDStretch.h"
#include "RateTransposer.h"
#include "cpu_detect.h"

using namespace soundtouch;

/// test if two floating point numbers are equal
#define TEST_FLOAT_EQUAL(a, b)  (fabs(a - b) < 1e-10)


/// Print library version string for autoconf
extern "C" void soundtouch_ac_test()
{
    printf("SoundTouch Version: %s\n",SOUNDTOUCH_VERSION);
}


SoundTouch::SoundTouch()
{
    // Initialize rate transposer and tempo changer instances

    pRateTransposer = new RateTransposer();
    pTDStretch = TDStretch::newInstance();

    setOutPipe(pTDStretch);

    rate = tempo = 0;

    virtualPitch =
    virtualRate =
    virtualTempo = 1.0;

    calcEffectiveRateAndTempo();

    samplesExpectedOut = 0;
    samplesOutput = 0;

    channels = 0;
    bSrateSet = false;
}


SoundTouch::~SoundTouch()
{
    delete pRateTransposer;
    delete pTDStretch;
}


/// Get SoundTouch library version string
const char *SoundTouch::getVersionString()
{
    static const char *_version = SOUNDTOUCH_VERSION;

    return _version;
}


/// Get SoundTouch library version Id
uint SoundTouch::getVersionId()
{
    return SOUNDTOUCH_VERSION_ID;
}


// Sets the number of channels, 1 = mono, 2 = stereo
void SoundTouch::setChannels(uint numChannels)
{
    if (!verifyNumberOfChannels(numChannels)) return;

    channels = numChannels;
    pRateTransposer->setChannels((int)numChannels);
    pTDStretch->setChannels((int)numChannels);
}


// Sets new rate control value. Normal rate = 1.0, smaller values
// represent slower rate, larger faster rates.
void SoundTouch::setRate(double newRate)
{
    virtualRate = newRate;
    calcEffectiveRateAndTempo();
}


// Sets new rate control value as a difference in percents compared
// to the original rate (-50 .. +100 %)
void SoundTouch::setRateChange(double newRate)
{
    virtualRate = 1.0 + 0.01 * newRate;
    calcEffectiveRateAndTempo();
}


// Sets new tempo control value. Normal tempo = 1.0, smaller values
// represent slower tempo, larger faster tempo.
void SoundTouch::setTempo(double newTempo)
{
    virtualTempo = newTempo;
    calcEffectiveRateAndTempo();
}


// Sets new tempo control value as a difference in percents compared
// to the original tempo (-50 .. +100 %)
void SoundTouch::setTempoChange(double newTempo)
{
    virtualTempo = 1.0 + 0.01 * newTempo;
    calcEffectiveRateAndTempo();
}


// Sets new pitch control value. Original pitch = 1.0, smaller values
// represent lower pitches, larger values higher pitch.
void SoundTouch::setPitch(double newPitch)
{
    virtualPitch = newPitch;
    calcEffectiveRateAndTempo();
}


// Sets pitch change in octaves compared to the original pitch
// (-1.00 .. +1.00)
void SoundTouch::setPitchOctaves(double newPitch)
{
    virtualPitch = exp(0.69314718056 * newPitch);
    calcEffectiveRateAndTempo();
}


// Sets pitch change in semi-tones compared to the original pitch
// (-12 .. +12)
void SoundTouch::setPitchSemiTones(int newPitch)
{
    setPitchOctaves((double)newPitch / 12.0);
}


void SoundTouch::setPitchSemiTones(double newPitch)
{
    setPitchOctaves(newPitch / 12.0);
}


// Calculates 'effective' rate and tempo values from the
// nominal control values.
void SoundTouch::calcEffectiveRateAndTempo()
{
    double oldTempo = tempo;
    double oldRate = rate;

    tempo = virtualTempo / virtualPitch;
    rate = virtualPitch * virtualRate;

    if (!TEST_FLOAT_EQUAL(rate,oldRate)) pRateTransposer->setRate(rate);
    if (!TEST_FLOAT_EQUAL(tempo, oldTempo)) pTDStretch->setTempo(tempo);

#ifndef SOUNDTOUCH_PREVENT_CLICK_AT_RATE_CROSSOVER
    if (rate <= 1.0f)
    {
        if (output != pTDStretch)
        {
            FIFOSamplePipe *tempoOut;

            assert(output == pRateTransposer);
            // move samples in the current output buffer to the output of pTDStretch
            tempoOut = pTDStretch->getOutput();
            tempoOut->moveSamples(*output);
            // move samples in pitch transposer's store buffer to tempo changer's input
            // deprecated : pTDStretch->moveSamples(*pRateTransposer->getStore());

            output = pTDStretch;
        }
    }
    else
#endif
    {
        if (output != pRateTransposer)
        {
            FIFOSamplePipe *transOut;

            assert(output == pTDStretch);
            // move samples in the current output buffer to the output of pRateTransposer
            transOut = pRateTransposer->getOutput();
            transOut->moveSamples(*output);
            // move samples in tempo changer's input to pitch transposer's input
            pRateTransposer->moveSamples(*pTDStretch->getInput());

            output = pRateTransposer;
        }
    }
}


// Sets sample rate.
void SoundTouch::setSampleRate(uint srate)
{
    // set sample rate, leave other tempo changer parameters as they are.
    pTDStretch->setParameters((int)srate);
    bSrateSet = true;
}


// Adds 'numSamples' pcs of samples from the 'samples' memory position into
// the input of the object.
void SoundTouch::putSamples(const SAMPLETYPE *samples, uint nSamples)
{
    if (bSrateSet == false)
    {
        ST_THROW_RT_ERROR("SoundTouch : Sample rate not defined");
    }
    else if (channels == 0)
    {
        ST_THROW_RT_ERROR("SoundTouch : Number of channels not defined");
    }

    // accumulate how many samples are expected out from processing, given the current
    // processing setting
    samplesExpectedOut += (double)nSamples / ((double)rate * (double)tempo);

#ifndef SOUNDTOUCH_PREVENT_CLICK_AT_RATE_CROSSOVER
    if (rate <= 1.0f)
    {
        // transpose the rate down, output the transposed sound to tempo changer buffer
        assert(output == pTDStretch);
        pRateTransposer->putSamples(samples, nSamples);
        pTDStretch->moveSamples(*pRateTransposer);
    }
    else
#endif
    {
        // evaluate the tempo changer, then transpose the rate up,
        assert(output == pRateTransposer);
        pTDStretch->putSamples(samples, nSamples);
        pRateTransposer->moveSamples(*pTDStretch);
    }
}


// Flushes the last samples from the processing pipeline to the output.
// Clears also the internal processing buffers.
//
// Note: This function is meant for extracting the last samples of a sound
// stream. This function may introduce additional blank samples in the end
// of the sound stream, and thus it's not recommended to call this function
// in the middle of a sound stream.
void SoundTouch::flush()
{
    int i;
    int numStillExpected;
    SAMPLETYPE *buff = new SAMPLETYPE[128 * channels];

    // how many samples are still expected to output
    numStillExpected = (int)((long)(samplesExpectedOut + 0.5) - samplesOutput);
    if (numStillExpected < 0) numStillExpected = 0;

    memset(buff, 0, 128 * channels * sizeof(SAMPLETYPE));
    // "Push" the last active samples out from the processing pipeline by
    // feeding blank samples into the processing pipeline until new,
    // processed samples appear in the output (not however, more than
    // 24ksamples in any case)
    for (i = 0; (numStillExpected > (int)numSamples()) && (i < 200); i ++)
    {
        putSamples(buff, 128);
    }

    adjustAmountOfSamples(numStillExpected);

    delete[] buff;

    // Clear input buffers
    pTDStretch->clearInput();
    // yet leave the output intouched as that's where the
    // flushed samples are!
}


// Changes a setting controlling the processing system behaviour. See the
// 'SETTING_...' defines for available setting ID's.
bool SoundTouch::setSetting(int settingId, int value)
{
    int sampleRate, sequenceMs, seekWindowMs, overlapMs;

    // read current tdstretch routine parameters
    pTDStretch->getParameters(&sampleRate, &sequenceMs, &seekWindowMs, &overlapMs);

    switch (settingId)
    {
        case SETTING_USE_AA_FILTER :
            // enables / disabless anti-alias filter
            pRateTransposer->enableAAFilter((value != 0) ? true : false);
            return true;

        case SETTING_AA_FILTER_LENGTH :
            // sets anti-alias filter length
            pRateTransposer->getAAFilter()->setLength(value);
            return true;

        case SETTING_USE_QUICKSEEK :
            // enables / disables tempo routine quick seeking algorithm
            pTDStretch->enableQuickSeek((value != 0) ? true : false);
            return true;

        case SETTING_SEQUENCE_MS:
            // change time-stretch sequence duration parameter
            pTDStretch->setParameters(sampleRate, value, seekWindowMs, overlapMs);
            return true;

        case SETTING_SEEKWINDOW_MS:
            // change time-stretch seek window length parameter
            pTDStretch->setParameters(sampleRate, sequenceMs, value, overlapMs);
            return true;

        case SETTING_OVERLAP_MS:
            // change time-stretch overlap length parameter
            pTDStretch->setParameters(sampleRate, sequenceMs, seekWindowMs, value);
            return true;

        default :
            return false;
    }
}


// Reads a setting controlling the processing system behaviour. See the
// 'SETTING_...' defines for available setting ID's.
//
// Returns the setting value.
int SoundTouch::getSetting(int settingId) const
{
    int temp;

    switch (settingId)
    {
        case SETTING_USE_AA_FILTER :
            return (uint)pRateTransposer->isAAFilterEnabled();

        case SETTING_AA_FILTER_LENGTH :
            return pRateTransposer->getAAFilter()->getLength();

        case SETTING_USE_QUICKSEEK :
            return (uint)pTDStretch->isQuickSeekEnabled();

        case SETTING_SEQUENCE_MS:
            pTDStretch->getParameters(nullptr, &temp, nullptr, nullptr);
            return temp;

        case SETTING_SEEKWINDOW_MS:
            pTDStretch->getParameters(nullptr, nullptr, &temp, nullptr);
            return temp;

        case SETTING_OVERLAP_MS:
            pTDStretch->getParameters(nullptr, nullptr, nullptr, &temp);
            return temp;

        case SETTING_NOMINAL_INPUT_SEQUENCE :
        {
            int size = pTDStretch->getInputSampleReq();

#ifndef SOUNDTOUCH_PREVENT_CLICK_AT_RATE_CROSSOVER
            if (rate <= 1.0)
            {
                // transposing done before timestretch, which impacts latency
                return (int)(size * rate + 0.5);
            }
#endif
            return size;
        }

        case SETTING_NOMINAL_OUTPUT_SEQUENCE :
        {
            int size = pTDStretch->getOutputBatchSize();

            if (rate > 1.0)
            {
                // transposing done after timestretch, which impacts latency
                return (int)(size / rate + 0.5);
            }
            return size;
        }

        case SETTING_INITIAL_LATENCY:
        {
            double latency = pTDStretch->getLatency();
            int latency_tr = pRateTransposer->getLatency();

#ifndef SOUNDTOUCH_PREVENT_CLICK_AT_RATE_CROSSOVER
            if (rate <= 1.0)
            {
                // transposing done before timestretch, which impacts latency
                latency = (latency + latency_tr) * rate;
            }
            else
#endif
            {
                latency += (double)latency_tr / rate;
            }

            return (int)(latency + 0.5);
        }

        default :
            return 0;
    }
}


// Clears all the samples in the object's output and internal processing
// buffers.
void SoundTouch::clear()
{
    samplesExpectedOut = 0;
    samplesOutput = 0;
    pRateTransposer->clear();
    pTDStretch->clear();
}


/// Returns number of samples currently unprocessed.
uint SoundTouch::numUnprocessedSamples() const
{
    FIFOSamplePipe * psp;
    if (pTDStretch)
    {
        psp = pTDStretch->getInput();
        if (psp)
        {
            return psp->numSamples();
        }
    }
    return 0;
}


/// Output samples from beginning of the sample buffer. Copies requested samples to
/// output buffer and removes them from the sample buffer. If there are less than
/// 'numsample' samples in the buffer, returns all that available.
///
/// \return Number of samples returned.
uint SoundTouch::receiveSamples(SAMPLETYPE *output, uint maxSamples)
{
    uint ret = FIFOProcessor::receiveSamples(output, maxSamples);
    samplesOutput += (long)ret;
    return ret;
}


/// Adjusts book-keeping so that given number of samples are removed from beginning of the
/// sample buffer without copying them anywhere.
///
/// Used to reduce the number of samples in the buffer when accessing the sample buffer directly
/// with 'ptrBegin' function.
uint SoundTouch::receiveSamples(uint maxSamples)
{
    uint ret = FIFOProcessor::receiveSamples(maxSamples);
    samplesOutput += (long)ret;
    return ret;
}


/// Get ratio between input and output audio durations, useful for calculating
/// processed output duration: if you'll process a stream of N samples, then
/// you can expect to get out N * getInputOutputSampleRatio() samples.
double SoundTouch::getInputOutputSampleRatio()
{
    return 1.0 / (tempo * rate);
}

/* ========================================================================= */
/* Safe C-Bridge for Telegram Voice Recording (Float/Short Converter & EQ)   */
/* ========================================================================= */

#include <cmath>

struct VocalBiquad {
    float b0, b1, b2, a1, a2;
    float s1[2], s2[2];

    void reset() {
        s1[0] = s1[1] = s2[0] = s2[1] = 0.0f;
    }

    void setHighPass(float sampleRate, float fc, float Q = 0.7071f) {
        float w0 = 2.0f * 3.14159265358979323846f * fc / sampleRate;
        float cosw0 = cosf(w0);
        float sinw0 = sinf(w0);
        float alpha = sinw0 / (2.0f * Q);

        float a0 = 1.0f + alpha;
        b0 = ((1.0f + cosw0) / 2.0f) / a0;
        b1 = (-(1.0f + cosw0)) / a0;
        b2 = ((1.0f + cosw0) / 2.0f) / a0;
        a1 = (-2.0f * cosw0) / a0;
        a2 = (1.0f - alpha) / a0;
        reset();
    }

    void setPeaking(float sampleRate, float f0, float gainDB, float Q) {
        float A = powf(10.0f, gainDB / 40.0f);
        float w0 = 2.0f * 3.14159265358979323846f * f0 / sampleRate;
        float cosw0 = cosf(w0);
        float sinw0 = sinf(w0);
        float alpha = sinw0 / (2.0f * Q);

        float a0 = 1.0f + alpha / A;
        b0 = (1.0f + alpha * A) / a0;
        b1 = (-2.0f * cosw0) / a0;
        b2 = (1.0f - alpha * A) / a0;
        a1 = (-2.0f * cosw0) / a0;
        a2 = (1.0f - alpha / A) / a0;
        reset();
    }

    inline float process(float x, int ch) {
        float y = b0 * x + s1[ch];
        s1[ch] = b1 * x - a1 * y + s2[ch];
        s2[ch] = b2 * x - a2 * y;
        return y;
    }
};

/* ========================================================================= */
/* Broadcast Vocal Compressor & Warm Analog Vacuum Tube Saturation           */
/* ========================================================================= */

class BroadcastVocalProcessor {
private:
    float m_sampleRate;
    float m_envelope[2]; // Per-channel envelope follower
    float m_attackAlpha;
    float m_releaseAlpha;

public:
    BroadcastVocalProcessor() : m_sampleRate(48000.0f) {
        m_envelope[0] = 0.0f;
        m_envelope[1] = 0.0f;
        init(48000.0f);
    }

    void init(float sampleRate) {
        m_sampleRate = (sampleRate > 8000.0f) ? sampleRate : 48000.0f;
        // Fast attack ~4ms, musical broadcast release ~90ms
        m_attackAlpha = expf(-1.0f / (m_sampleRate * 0.004f));
        m_releaseAlpha = expf(-1.0f / (m_sampleRate * 0.090f));
        reset();
    }

    void reset() {
        m_envelope[0] = 0.0f;
        m_envelope[1] = 0.0f;
    }

    // Process a single sample through compressor and/or tube saturation
    inline float processSample(float sample, int ch, bool compEnabled, bool tubeEnabled) {
        if (ch < 0 || ch > 1) ch = 0;
        float current = sample;

        if (compEnabled) {
            float absIn = fabsf(current) / 32768.0f;
            if (absIn > m_envelope[ch]) {
                m_envelope[ch] = m_attackAlpha * m_envelope[ch] + (1.0f - m_attackAlpha) * absIn;
            } else {
                m_envelope[ch] = m_releaseAlpha * m_envelope[ch] + (1.0f - m_releaseAlpha) * absIn;
            }

            const float threshold = 0.125f;
            float gainReduction = 1.0f;
            if (m_envelope[ch] > threshold) {
                float excess = m_envelope[ch] - threshold;
                gainReduction = (threshold + excess / 3.5f) / m_envelope[ch];
            }

            current = current * gainReduction * 1.38f;
        }

        if (tubeEnabled) {
            float x = current / 32768.0f;
            float driven = x * 1.25f;
            float saturated;
            if (driven > 0.0f) {
                float warm = driven + 0.10f * driven * driven;
                saturated = tanhf(warm * 0.95f);
            } else {
                saturated = tanhf(driven);
            }
            current = saturated * 32767.0f;
        }

        return current;
    }

    void processBuffer(float *buffer, int numSamples, int channels, bool compEnabled, bool tubeEnabled) {
        for (int i = 0; i < numSamples; ++i) {
            for (int ch = 0; ch < channels && ch < 2; ++ch) {
                int idx = i * channels + ch;
                buffer[idx] = processSample(buffer[idx], ch, compEnabled, tubeEnabled);
            }
        }
    }
};

static bool g_compressorEnabled = true;
static bool g_tubeEnabled = true;
static bool g_eqEnabled = true;
static float g_voicePitchSemitones = -2.3f;
static float g_voiceTempo = 1.0f;
static int g_vocalPreset = 0; // Default: 0 = The Works (Radio EQ + Comp + Tube)

static void apply_vocal_preset(int preset, float sampleRate, VocalBiquad &hpf, VocalBiquad &warmth, VocalBiquad &debox, VocalBiquad &air, BroadcastVocalProcessor &comp) {
    comp.init(sampleRate);
    hpf.reset(); warmth.reset(); debox.reset(); air.reset();

    switch (preset) {
        case 0: // The Works (Radio Broadcaster EQ + Compressor + Tube Saturation) [Default]
            g_eqEnabled = true;
            g_compressorEnabled = true;
            g_tubeEnabled = true;
            hpf.setHighPass(sampleRate, 75.0f, 0.7071f);
            warmth.setPeaking(sampleRate, 125.0f, 4.0f, 2.0f);
            debox.setPeaking(sampleRate, 400.0f, -3.0f, 1.4f);
            air.setPeaking(sampleRate, 9000.0f, 2.5f, 1.0f);
            break;
        case 1: // Radio Broadcaster Vocal EQ Only
            g_eqEnabled = true;
            g_compressorEnabled = false;
            g_tubeEnabled = false;
            hpf.setHighPass(sampleRate, 75.0f, 0.7071f);
            warmth.setPeaking(sampleRate, 125.0f, 4.0f, 2.0f);
            debox.setPeaking(sampleRate, 400.0f, -3.0f, 1.4f);
            air.setPeaking(sampleRate, 9000.0f, 2.5f, 1.0f);
            break;
        case 2: // Warm Velvet / Podcast Vocal EQ Only
            g_eqEnabled = true;
            g_compressorEnabled = false;
            g_tubeEnabled = false;
            hpf.setHighPass(sampleRate, 70.0f, 0.7071f);
            warmth.setPeaking(sampleRate, 140.0f, 2.8f, 1.8f);
            debox.setPeaking(sampleRate, 450.0f, -2.0f, 1.4f);
            air.setPeaking(sampleRate, 8500.0f, 1.8f, 1.0f);
            break;
        case 3: // Studio Crystal Clarity Vocal EQ Only
            g_eqEnabled = true;
            g_compressorEnabled = false;
            g_tubeEnabled = false;
            hpf.setHighPass(sampleRate, 80.0f, 0.7071f);
            warmth.setPeaking(sampleRate, 110.0f, 1.8f, 2.0f);
            debox.setPeaking(sampleRate, 380.0f, -3.5f, 1.5f);
            air.setPeaking(sampleRate, 10000.0f, 3.5f, 1.0f);
            break;
        case 4: // Cinematic Deep Sub-Bass Vocal EQ Only
            g_eqEnabled = true;
            g_compressorEnabled = false;
            g_tubeEnabled = false;
            hpf.setHighPass(sampleRate, 60.0f, 0.7071f);
            warmth.setPeaking(sampleRate, 95.0f, 5.0f, 2.2f);
            debox.setPeaking(sampleRate, 420.0f, -3.0f, 1.4f);
            air.setPeaking(sampleRate, 8000.0f, 1.5f, 1.0f);
            break;
        case 5: // Pure SoundTouch Max (Flat / Bypass all EQ and Dynamics)
            g_eqEnabled = false;
            g_compressorEnabled = false;
            g_tubeEnabled = false;
            break;
        case 6: // Broadcast Compressor / Leveler Only
            g_eqEnabled = false;
            g_compressorEnabled = true;
            g_tubeEnabled = false;
            break;
        case 7: // Vacuum Tube Saturation Only
            g_eqEnabled = false;
            g_compressorEnabled = false;
            g_tubeEnabled = true;
            break;
        case 8: // Full Dynamics Only (Compressor + Tube Saturation, No EQ)
            g_eqEnabled = false;
            g_compressorEnabled = true;
            g_tubeEnabled = true;
            break;
        default:
            g_eqEnabled = true;
            g_compressorEnabled = true;
            g_tubeEnabled = true;
            hpf.setHighPass(sampleRate, 75.0f, 0.7071f);
            warmth.setPeaking(sampleRate, 125.0f, 4.0f, 2.0f);
            debox.setPeaking(sampleRate, 400.0f, -3.0f, 1.4f);
            air.setPeaking(sampleRate, 9000.0f, 2.5f, 1.0f);
            break;
    }
}

extern "C" {
void soundtouch_set_compressor_enabled(int enabled) {
    g_compressorEnabled = (enabled != 0);
}

void soundtouch_set_pitch_semitones(float pitch) {
    g_voicePitchSemitones = pitch;
}

float soundtouch_get_pitch_semitones(void) {
    return g_voicePitchSemitones;
}

void soundtouch_set_vocal_preset(int preset) {
    if (preset < 0 || preset > 8) preset = 0;
    g_vocalPreset = preset;
}

int soundtouch_get_vocal_preset(void) {
    return g_vocalPreset;
}

void soundtouch_set_tempo(float tempo) {
    if (tempo >= 0.5f && tempo <= 2.0f) {
        g_voiceTempo = tempo;
    }
}

float soundtouch_get_tempo(void) {
    return g_voiceTempo;
}

static int g_micGainDb = 0;
static float g_micGainLinear = 1.0f;

void soundtouch_set_mic_gain_db(int gainDb) {
    g_micGainDb = gainDb;
    if (gainDb == 0) {
        g_micGainLinear = 1.0f;
    } else {
        g_micGainLinear = powf(10.0f, (float)gainDb / 20.0f);
    }
}

int soundtouch_get_mic_gain_db(void) {
    return g_micGainDb;
}
}

static soundtouch::SoundTouch *g_soundTouchRecorder = nullptr;
static VocalBiquad g_recorderHpf;
static VocalBiquad g_recorderWarmth;
static VocalBiquad g_recorderDebox;
static VocalBiquad g_recorderAir;
static BroadcastVocalProcessor g_recorderCompressor;

extern "C" {

void soundtouch_init_recorder(int sampleRate, float pitchSemitones) {
    if (!g_soundTouchRecorder) {
        g_soundTouchRecorder = new soundtouch::SoundTouch();
    }
    g_soundTouchRecorder->clear();
    g_soundTouchRecorder->setSampleRate(sampleRate);
    g_soundTouchRecorder->setChannels(1); // Mono for voice notes
    g_soundTouchRecorder->setPitchSemiTones(pitchSemitones);
    g_soundTouchRecorder->setTempo(g_voiceTempo); // User's delivery tempo
    g_soundTouchRecorder->setSetting(SETTING_USE_AA_FILTER, 1);
    g_soundTouchRecorder->setSetting(SETTING_AA_FILTER_LENGTH, 128);
    g_soundTouchRecorder->setSetting(SETTING_USE_QUICKSEEK, 0);
    g_soundTouchRecorder->setSetting(SETTING_SEQUENCE_MS, 100);
    g_soundTouchRecorder->setSetting(SETTING_SEEKWINDOW_MS, 35);
    g_soundTouchRecorder->setSetting(SETTING_OVERLAP_MS, 18);

    // Configure Vocal Profile according to selected Profile
    apply_vocal_preset(g_vocalPreset, (float)sampleRate, g_recorderHpf, g_recorderWarmth, g_recorderDebox, g_recorderAir, g_recorderCompressor);
}

void soundtouch_put_samples(const short *samples, int numSamples) {
    if (!g_soundTouchRecorder || !samples || numSamples <= 0) return;

    // Convert 16-bit short to float safely
    float *floatBuffer = (float *)malloc(numSamples * sizeof(float));
    if (!floatBuffer) return;

    for (int i = 0; i < numSamples; ++i) {
        floatBuffer[i] = (float)samples[i];
    }

    g_soundTouchRecorder->putSamples(floatBuffer, (uint)numSamples);
    free(floatBuffer);
}

int soundtouch_receive_samples(short *output, int maxSamples) {
    if (!g_soundTouchRecorder || !output || maxSamples <= 0) return 0;

    float *floatBuffer = (float *)malloc(maxSamples * sizeof(float));
    if (!floatBuffer) return 0;

    uint received = g_soundTouchRecorder->receiveSamples(floatBuffer, (uint)maxSamples);
    if (received > 0) {
        // Apply EQ if active
        if (g_eqEnabled) {
            for (uint i = 0; i < received; ++i) {
                float s = floatBuffer[i];
                s = g_recorderHpf.process(s, 0);
                s = g_recorderWarmth.process(s, 0);
                s = g_recorderDebox.process(s, 0);
                s = g_recorderAir.process(s, 0);
                floatBuffer[i] = s;
            }
        }

        if (g_compressorEnabled || g_tubeEnabled) {
            // Apply Broadcast Compressor & Warm Tube Saturation
            for (uint i = 0; i < received; ++i) {
                floatBuffer[i] = g_recorderCompressor.processSample(floatBuffer[i], 0, g_compressorEnabled, g_tubeEnabled);
            }
            for (uint i = 0; i < received; ++i) {
                float val = floatBuffer[i] * g_micGainLinear;
                if (val > 30000.0f) {
                    val = 30000.0f + 2767.0f * tanhf((val - 30000.0f) / 2767.0f);
                } else if (val < -30000.0f) {
                    val = -30000.0f + 2768.0f * tanhf((val + 30000.0f) / 2768.0f);
                }
                output[i] = (short)val;
            }
        } else {
            const float gain = 1.15f * g_micGainLinear;
            for (uint i = 0; i < received; ++i) {
                float val = floatBuffer[i] * gain;
                if (val > 30000.0f) {
                    val = 30000.0f + 2767.0f * tanhf((val - 30000.0f) / 2767.0f);
                } else if (val < -30000.0f) {
                    val = -30000.0f + 2768.0f * tanhf((val + 30000.0f) / 2768.0f);
                }
                output[i] = (short)val;
            }
        }
    }

    free(floatBuffer);
    return (int)received;
}

int soundtouch_num_samples(void) {
    if (!g_soundTouchRecorder) return 0;
    return (int)g_soundTouchRecorder->numSamples();
}

void soundtouch_clear_recorder(void) {
    if (g_soundTouchRecorder) {
        g_soundTouchRecorder->clear();
    }
    g_recorderHpf.reset();
    g_recorderWarmth.reset();
    g_recorderDebox.reset();
    g_recorderAir.reset();
    g_recorderCompressor.reset();
}

}

/* ========================================================================= */
/* Safe C-Bridge for Live VoIP Calls (Low-Latency SoundTouch Voice Changer)  */
/* ========================================================================= */

#include "soundtouch_live_call.h"
#include <mutex>
#include <vector>

static soundtouch::SoundTouch *g_soundTouchCall = nullptr;
static int g_callSampleRate = 0;
static int g_callChannels = 0;
static float g_callPitch = 0.0f;
static std::mutex g_callMutex;

// 4-Band Vocal Studio EQ for Live Calls
static VocalBiquad g_callHpf;    // Cut sub-bass <= 75Hz
static VocalBiquad g_callWarmth; // Boost 125Hz +3.5dB (masculine chest resonance)
static VocalBiquad g_callDebox;  // Reduce boxiness around 400Hz -2.5dB
static VocalBiquad g_callAir;    // High-frequency air at 9kHz +2.2dB (condenser mic presence)
static BroadcastVocalProcessor g_callCompressor;
static std::vector<float> g_callFifo;
static int g_callPreset = -1;

static float g_callTempo = 1.0f;

extern "C" {

void soundtouch_process_live_call_frame(short *samples, int numSamples, int channels, int sampleRate, float pitchSemitones) {
    if (!samples || numSamples <= 0 || channels <= 0 || sampleRate <= 0) return;

    std::lock_guard<std::mutex> lock(g_callMutex);

    if (g_callPreset != g_vocalPreset) {
        apply_vocal_preset(g_vocalPreset, (float)sampleRate, g_callHpf, g_callWarmth, g_callDebox, g_callAir, g_callCompressor);
        g_callPreset = g_vocalPreset;
    }

    if (fabsf(pitchSemitones) < 0.01f && fabsf(g_voiceTempo - 1.0f) < 0.001f) {
        if (g_eqEnabled) {
            for (int i = 0; i < numSamples; ++i) {
                for (int ch = 0; ch < channels && ch < 2; ++ch) {
                    int idx = i * channels + ch;
                    float s = (float)samples[idx];
                    s = g_callHpf.process(s, ch);
                    s = g_callWarmth.process(s, ch);
                    s = g_callDebox.process(s, ch);
                    s = g_callAir.process(s, ch);
                    samples[idx] = (short)(s > 32767.0f ? 32767.0f : (s < -32768.0f ? -32768.0f : s));
                }
            }
        }
        if (g_compressorEnabled || g_tubeEnabled) {
            for (int i = 0; i < numSamples; ++i) {
                for (int ch = 0; ch < channels && ch < 2; ++ch) {
                    int idx = i * channels + ch;
                    float val = g_callCompressor.processSample((float)samples[idx], ch, g_compressorEnabled, g_tubeEnabled);
                    if (val > 32767.0f) val = 32767.0f;
                    else if (val < -32768.0f) val = -32768.0f;
                    samples[idx] = (short)val;
                }
            }
        }
        return;
    }

    if (!g_soundTouchCall || g_callSampleRate != sampleRate || g_callChannels != channels || fabsf(g_callPitch - pitchSemitones) > 0.001f || fabsf(g_callTempo - g_voiceTempo) > 0.001f) {
        if (!g_soundTouchCall) {
            g_soundTouchCall = new soundtouch::SoundTouch();
        }
        g_soundTouchCall->clear();
        g_soundTouchCall->setSampleRate(sampleRate);
        g_soundTouchCall->setChannels(channels);
        g_soundTouchCall->setPitchSemiTones(pitchSemitones);
        g_soundTouchCall->setTempo(g_voiceTempo);

        // Studio-grade pitch shifting parameters requested by user (Seq=100ms, Seek=35ms, Overlap=18ms, AA=128t, QS=0)
        g_soundTouchCall->setSetting(SETTING_SEQUENCE_MS, 100);
        g_soundTouchCall->setSetting(SETTING_SEEKWINDOW_MS, 35);
        g_soundTouchCall->setSetting(SETTING_OVERLAP_MS, 18);
        g_soundTouchCall->setSetting(SETTING_USE_AA_FILTER, 1);
        g_soundTouchCall->setSetting(SETTING_AA_FILTER_LENGTH, 128);
        g_soundTouchCall->setSetting(SETTING_USE_QUICKSEEK, 0); // 0 = Full precision cross-correlation (Studio Broadcast Quality, NO metallic artifacts)

        // Configure Vocal EQ Filters according to selected preset
        apply_vocal_preset(g_vocalPreset, (float)sampleRate, g_callHpf, g_callWarmth, g_callDebox, g_callAir, g_callCompressor);
        g_callPreset = g_vocalPreset;

        g_callSampleRate = sampleRate;
        g_callChannels = channels;
        g_callPitch = pitchSemitones;
        g_callTempo = g_voiceTempo;

        g_callFifo.clear();

        // Prime pipeline with silence to satisfy 100ms+35ms SoundTouch requirement and drain immediately into FIFO
        int primeSamples = (sampleRate * 160) / 1000;
        std::vector<float> primeSilence(primeSamples * channels, 0.0f);
        g_soundTouchCall->putSamples(primeSilence.data(), (uint)primeSamples);
        uint primeAvail = g_soundTouchCall->numSamples();
        if (primeAvail > 0) {
            std::vector<float> primeDrain(primeAvail * channels);
            uint received = g_soundTouchCall->receiveSamples(primeDrain.data(), primeAvail);
            if (received > 0) {
                g_callFifo.insert(g_callFifo.end(), primeDrain.begin(), primeDrain.begin() + (received * channels));
            }
        }
    }

    int totalSamples = numSamples * channels;
    std::vector<float> floatIn(totalSamples);
    for (int i = 0; i < totalSamples; ++i) {
        floatIn[i] = (float)samples[i];
    }

    g_soundTouchCall->putSamples(floatIn.data(), (uint)numSamples);

    // Drain all available processed samples from SoundTouch into FIFO
    uint avail = g_soundTouchCall->numSamples();
    if (avail > 0) {
        std::vector<float> tempDrain(avail * channels);
        uint received = g_soundTouchCall->receiveSamples(tempDrain.data(), avail);
        if (received > 0) {
            g_callFifo.insert(g_callFifo.end(), tempDrain.begin(), tempDrain.begin() + (received * channels));
        }
    }

    // Deliver exactly totalSamples from FIFO into output samples
    if ((int)g_callFifo.size() >= totalSamples) {
        std::vector<float> outBlock(g_callFifo.begin(), g_callFifo.begin() + totalSamples);
        g_callFifo.erase(g_callFifo.begin(), g_callFifo.begin() + totalSamples);

        // Apply 4-Band Vocal Studio EQ if enabled
        if (g_eqEnabled) {
            for (int i = 0; i < numSamples; ++i) {
                for (int ch = 0; ch < channels && ch < 2; ++ch) {
                    int idx = i * channels + ch;
                    float s = outBlock[idx];
                    s = g_callHpf.process(s, ch);
                    s = g_callWarmth.process(s, ch);
                    s = g_callDebox.process(s, ch);
                    s = g_callAir.process(s, ch);
                    outBlock[idx] = s;
                }
            }
        }

        // Apply Broadcast Compressor & Warm Analog Tube Saturation
        if (g_compressorEnabled || g_tubeEnabled) {
            for (int i = 0; i < numSamples; ++i) {
                for (int ch = 0; ch < channels && ch < 2; ++ch) {
                    int idx = i * channels + ch;
                    float val = g_callCompressor.processSample(outBlock[idx], ch, g_compressorEnabled, g_tubeEnabled);
                    if (val > 32767.0f) val = 32767.0f;
                    else if (val < -32768.0f) val = -32768.0f;
                    samples[idx] = (short)val;
                }
            }
        } else {
            const float gain = 1.15f; // +1.2 dB clean broadcast presence
            for (int i = 0; i < totalSamples; ++i) {
                float val = outBlock[i] * gain;
                if (val > 30000.0f) {
                    val = 30000.0f + 2767.0f * tanhf((val - 30000.0f) / 2767.0f);
                } else if (val < -30000.0f) {
                    val = -30000.0f + 2768.0f * tanhf((val + 30000.0f) / 2768.0f);
                }
                samples[i] = (short)val;
            }
        }
    } else {
        // Underflow protection: NEVER leak raw unpitched microphone voice.
        // Deliver pure silence to preserve the user's voice privacy and prevent comb filtering.
        memset(samples, 0, totalSamples * sizeof(short));
    }

    // Manage buffer drift to keep conversational latency bounded without cutting audio
    int maxFifoSamples = ((sampleRate * 200) / 1000) * channels;
    if ((int)g_callFifo.size() > maxFifoSamples) {
        int excess = (int)g_callFifo.size() - maxFifoSamples;
        if (excess > 8 * channels) excess = 8 * channels;
        g_callFifo.erase(g_callFifo.begin(), g_callFifo.begin() + excess);
    }
}

void soundtouch_clear_call(void) {
    std::lock_guard<std::mutex> lock(g_callMutex);
    if (g_soundTouchCall) {
        delete g_soundTouchCall;
        g_soundTouchCall = nullptr;
    }
    g_callHpf.reset();
    g_callWarmth.reset();
    g_callDebox.reset();
    g_callAir.reset();
    g_callCompressor.reset();
    g_callFifo.clear();
    g_callSampleRate = 0;
    g_callChannels = 0;
    g_callPitch = 0.0f;
    g_callTempo = 1.0f;
    g_callPreset = -1;
}

/* ========================================================================= */
/* Safe C-Bridge for Round Video Notes (SoundTouch Voice Changer + EQ)       */
/* ========================================================================= */

static soundtouch::SoundTouch *g_soundTouchVideoNote = nullptr;
static int g_vnSampleRate = 0;
static int g_vnChannels = 0;
static float g_vnPitch = 0.0f;
static float g_vnTempo = 1.0f;
static std::mutex g_vnMutex;

static VocalBiquad g_vnHpf;
static VocalBiquad g_vnWarmth;
static VocalBiquad g_vnDebox;
static VocalBiquad g_vnAir;
static BroadcastVocalProcessor g_vnCompressor;
static int g_vnPreset = -1;

void soundtouch_process_video_note_frame(short *samples, int numSamples, int channels, int sampleRate, float pitchSemitones) {
    if (!samples || numSamples <= 0 || channels <= 0 || sampleRate <= 0) return;

    std::lock_guard<std::mutex> lock(g_vnMutex);

    if (g_vnPreset != g_vocalPreset) {
        apply_vocal_preset(g_vocalPreset, (float)sampleRate, g_vnHpf, g_vnWarmth, g_vnDebox, g_vnAir, g_vnCompressor);
        g_vnPreset = g_vocalPreset;
    }

    if (fabsf(pitchSemitones) < 0.01f && fabsf(g_voiceTempo - 1.0f) < 0.001f) {
        if (g_eqEnabled) {
            for (int i = 0; i < numSamples; ++i) {
                for (int ch = 0; ch < channels && ch < 2; ++ch) {
                    int idx = i * channels + ch;
                    float s = (float)samples[idx];
                    s = g_vnHpf.process(s, ch);
                    s = g_vnWarmth.process(s, ch);
                    s = g_vnDebox.process(s, ch);
                    s = g_vnAir.process(s, ch);
                    samples[idx] = (short)(s > 32767.0f ? 32767.0f : (s < -32768.0f ? -32768.0f : s));
                }
            }
        }
        if (g_compressorEnabled || g_tubeEnabled) {
            for (int i = 0; i < numSamples; ++i) {
                for (int ch = 0; ch < channels && ch < 2; ++ch) {
                    int idx = i * channels + ch;
                    float val = g_vnCompressor.processSample((float)samples[idx], ch, g_compressorEnabled, g_tubeEnabled);
                    if (val > 32767.0f) val = 32767.0f;
                    else if (val < -32768.0f) val = -32768.0f;
                    samples[idx] = (short)val;
                }
            }
        }
        return;
    }

    if (!g_soundTouchVideoNote || g_vnSampleRate != sampleRate || g_vnChannels != channels || fabsf(g_vnPitch - pitchSemitones) > 0.001f || fabsf(g_vnTempo - g_voiceTempo) > 0.001f) {
        if (!g_soundTouchVideoNote) {
            g_soundTouchVideoNote = new soundtouch::SoundTouch();
        }
        g_soundTouchVideoNote->clear();
        g_soundTouchVideoNote->setSampleRate(sampleRate);
        g_soundTouchVideoNote->setChannels(channels);
        g_soundTouchVideoNote->setPitchSemiTones(pitchSemitones);
        g_soundTouchVideoNote->setTempo(g_voiceTempo);

        // Maximum quality settings matching user preference (Seq=100, Seek=35, Overlap=18, AA=128t, QS=0)
        g_soundTouchVideoNote->setSetting(SETTING_USE_AA_FILTER, 1);
        g_soundTouchVideoNote->setSetting(SETTING_AA_FILTER_LENGTH, 128);
        g_soundTouchVideoNote->setSetting(SETTING_USE_QUICKSEEK, 0);
        g_soundTouchVideoNote->setSetting(SETTING_SEQUENCE_MS, 100);
        g_soundTouchVideoNote->setSetting(SETTING_SEEKWINDOW_MS, 35);
        g_soundTouchVideoNote->setSetting(SETTING_OVERLAP_MS, 18);

        // Configure 4-Band Studio Vocal EQ according to selected preset
        apply_vocal_preset(g_vocalPreset, (float)sampleRate, g_vnHpf, g_vnWarmth, g_vnDebox, g_vnAir, g_vnCompressor);
        g_vnPreset = g_vocalPreset;

        g_vnSampleRate = sampleRate;
        g_vnChannels = channels;
        g_vnPitch = pitchSemitones;
        g_vnTempo = g_voiceTempo;

        // Pre-prime with initial latency silence so output never starves on first frame (keeps AV sync)
        int initialLatency = (int)g_soundTouchVideoNote->getSetting(SETTING_INITIAL_LATENCY);
        if (initialLatency <= 0) {
            initialLatency = (sampleRate * 160) / 1000;
        }
        std::vector<float> silence(initialLatency * channels, 0.0f);
        g_soundTouchVideoNote->putSamples(silence.data(), (uint)initialLatency);
    }

    int totalSamples = numSamples * channels;
    std::vector<float> floatBuffer(totalSamples);
    for (int i = 0; i < totalSamples; ++i) {
        floatBuffer[i] = (float)samples[i];
    }

    g_soundTouchVideoNote->putSamples(floatBuffer.data(), (uint)numSamples);

    uint received = g_soundTouchVideoNote->receiveSamples(floatBuffer.data(), (uint)numSamples);

    // Apply 4-Band Studio Vocal EQ if enabled
    if (g_eqEnabled) {
        for (uint i = 0; i < received; ++i) {
            for (int ch = 0; ch < channels && ch < 2; ++ch) {
                int idx = i * channels + ch;
                float s = floatBuffer[idx];
                s = g_vnHpf.process(s, ch);
                s = g_vnWarmth.process(s, ch);
                s = g_vnDebox.process(s, ch);
                s = g_vnAir.process(s, ch);
                floatBuffer[idx] = s;
            }
        }
    }

    if (g_compressorEnabled || g_tubeEnabled) {
        // Apply Broadcast Compressor & Warm Tube Saturation
        for (uint i = 0; i < received; ++i) {
            for (int ch = 0; ch < channels && ch < 2; ++ch) {
                int idx = i * channels + ch;
                float val = g_vnCompressor.processSample(floatBuffer[idx], ch, g_compressorEnabled, g_tubeEnabled);
                val *= g_micGainLinear;
                if (val > 30000.0f) {
                    val = 30000.0f + 2767.0f * tanhf((val - 30000.0f) / 2767.0f);
                } else if (val < -30000.0f) {
                    val = -30000.0f + 2768.0f * tanhf((val + 30000.0f) / 2768.0f);
                }
                samples[idx] = (short)val;
            }
        }
    } else {
        const float gain = 1.15f * g_micGainLinear;
        for (uint i = 0; i < received * (uint)channels; ++i) {
            float val = floatBuffer[i] * gain;
            if (val > 30000.0f) {
                val = 30000.0f + 2767.0f * tanhf((val - 30000.0f) / 2767.0f);
            } else if (val < -30000.0f) {
                val = -30000.0f + 2768.0f * tanhf((val + 30000.0f) / 2768.0f);
            }
            samples[i] = (short)val;
        }
    }

    // Pad remaining with silence if received was less than numSamples
    for (uint i = received * (uint)channels; i < (uint)totalSamples; ++i) {
        samples[i] = 0;
    }

    // Manage buffer drift to keep audio-video sync exact
    uint curAvailable = g_soundTouchVideoNote->numSamples();
    uint maxAllowedBuffer = (uint)((sampleRate * 200) / 1000);
    if (curAvailable > maxAllowedBuffer + (uint)numSamples) {
        uint excess = curAvailable - maxAllowedBuffer;
        if (excess > 48) excess = 48; // drain max 1ms per frame
        std::vector<float> drain(excess * channels);
        g_soundTouchVideoNote->receiveSamples(drain.data(), excess);
    }
}

void soundtouch_clear_video_note(void) {
    std::lock_guard<std::mutex> lock(g_vnMutex);
    if (g_soundTouchVideoNote) {
        delete g_soundTouchVideoNote;
        g_soundTouchVideoNote = nullptr;
    }
    g_vnHpf.reset();
    g_vnWarmth.reset();
    g_vnDebox.reset();
    g_vnAir.reset();
    g_vnCompressor.reset();
    g_vnSampleRate = 0;
    g_vnChannels = 0;
    g_vnPitch = 0.0f;
    g_vnTempo = 1.0f;
    g_vnPreset = -1;
}

}