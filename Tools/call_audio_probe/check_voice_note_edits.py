"""Native regression probe; run in a VS developer shell with --opus-dir containing
the bundled Opus build's opus.lib and opus.dll. Requires numpy. Compiles the actual
recorder/edit functions with real Ogg/Opusfile; SoundTouch input aborts deliberately
so any reprocessing of saved clips fails the test.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('--opus-dir', type=Path, required=True)
args = p.parse_args()
root = Path(__file__).resolve().parents[2]
xiph = root / 'TMessagesProj/jni/third_party/xiph'
source = (root / 'TMessagesProj/jni/audio.c').read_text()
prefix = source[source.index('typedef struct {'):source.index('JNIEXPORT jint Java_org_telegram_messenger_MediaController_startRecord')]
edits = source[source.index('int cropOpusAudio('):source.index('JNIEXPORT jboolean Java_org_telegram_messenger_MediaController_cropOpusFile')]
headers = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <fcntl.h>
#include <ogg/ogg.h>
#include <opus.h>
#include <opusfile.h>
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define LOGE(...) fprintf(stderr, __VA_ARGS__)
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL line %d\n",__LINE__); exit(1); } } while(0)
void soundtouch_clear_recorder(void) {}
void soundtouch_init_recorder(int rate, float pitch) {}
float soundtouch_get_pitch_semitones(void) { return -2.3f; }
void soundtouch_put_samples(const short *p, int n) { abort(); }
int soundtouch_num_samples(void) { abort(); return 0; }
int soundtouch_receive_samples(short *p, int n) { abort(); return 0; }
'''
main = r'''
static void makeClip(const char *path, int count) {
    CHECK(initRecorder(path, 48000, 256000));
    SavedClipWriter writer = {0};
    short pcm[137];
    for (int i=0; i<count;) {
        int n=MIN(137,count-i);
        for(int j=0;j<n;j++) pcm[j]=(short)(12000*sin(2*3.141592653589793*440*(i+j)/48000));
        CHECK(writeSavedClip(&writer, pcm, n, 0));
        i+=n;
    }
    CHECK(writeSavedClip(&writer,NULL,0,1));
    cleanupRecorder();
}
static void checkClip(const char *path, int count) {
    int error;
    OggOpusFile *f=op_open_file(path,&error);
    CHECK(f != NULL);
    CHECK(op_pcm_total(f,-1)==count);
    FILE *out=fopen("decoded.pcm","wb");
    CHECK(out != NULL);
    short pcm[960]; int total=0,n;
    while((n=op_read(f,pcm,960,NULL))>0) { total+=n; fwrite(pcm,2,n,out); }
    CHECK(n==0 && total==count);
    fclose(out); op_free(f);
}
int main(void) {
    _set_fmode(_O_BINARY);
    int sizes[]={1,312,648,649,959,960,961,1920,48017};
    for(int i=0;i<sizeof(sizes)/sizeof(sizes[0]);i++) {
        makeClip("a.ogg",sizes[i]); checkClip("a.ogg",sizes[i]);
        makeClip("b.ogg",961);
        CHECK(joinOpusAudios("a.ogg","b.ogg","joined.ogg"));
        checkClip("joined.ogg",sizes[i]+961);
    }
    makeClip("a.ogg",48017); makeClip("b.ogg",48123);
    CHECK(joinOpusAudios("a.ogg","b.ogg","joined.ogg"));
    CHECK(joinOpusAudios("joined.ogg","a.ogg","resumed.ogg"));
    checkClip("resumed.ogg",144157);
    CHECK(cropOpusAudio("resumed.ogg","trimmed.ogg",100,2100));
    checkClip("trimmed.ogg",96000);
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='voice-note-edits-') as tmp:
    tmp = Path(tmp)
    (tmp / 'probe.c').write_text(headers + prefix + edits + main)
    shutil.copy2(args.opus_dir / 'opus.dll', tmp)
    sources = [tmp / 'probe.c']
    sources += [xiph / 'ogg/src' / f for f in ['framing.c', 'bitwise.c']]
    sources += [xiph / 'opusfile/src' / f for f in ['info.c', 'internal.c', 'opusfile.c', 'stream.c']]
    includes = [xiph / d for d in ['ogg/include', 'opus/include', 'opusfile/include']]
    command = ['cl', '/nologo', '/O2', '/std:c11', '/D_CRT_SECURE_NO_WARNINGS']
    command += ['/I' + str(d) for d in includes]
    command += [str(s) for s in sources] + [str(args.opus_dir / 'opus.lib'), '/Fe:probe.exe']
    subprocess.run(command, cwd=tmp, check=True)
    subprocess.run([str(tmp / 'probe.exe')], cwd=tmp, check=True)
    pcm = np.fromfile(tmp / 'decoded.pcm', dtype=np.int16).astype(float)
    # Both halves include different original segments and repeated joins.
    for start in [10000, 58000]:
        block = pcm[start:start + 24000]
        peak = np.argmax(abs(np.fft.rfft(block * np.hanning(len(block))))) * 48000 / len(block)
        assert abs(peak - 440) <= 2, peak
    print('PASS: repeated joins and trimming preserve pitch and exact duration; no SoundTouch processing.')
