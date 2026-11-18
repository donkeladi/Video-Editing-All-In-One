#!/usr/bin/env python3
"""Potong audio ikut KEEP, jana SFX (ffmpeg synth), campur, loudnorm -14 LUFS, mux dengan video senyap.
Guna: python3 -I scripts/sfx_mix.py input/main.mov work/silent.mp4 output/out.mp4"""
import sys, subprocess, wave, numpy as np
src, vid, dst = sys.argv[1:4]
FPS = 30; SR = 48000
KEEP = [(9,896),(916,1063),(1080,1253),(1265,1282),(1297,1398)]
def sh(*a): subprocess.run(a, check=True, stderr=subprocess.DEVNULL)

# 1) suara dipotong, fade 10ms di setiap sambungan
parts = []; fc = []
for i, (a, b) in enumerate(KEEP):
    s, e = a / FPS, b / FPS
    fc.append(f'[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={e-s-0.01}:d=0.01[a{i}]'); parts.append(f'[a{i}]')
fc.append(''.join(parts) + f'concat=n={len(KEEP)}:v=0:a=1,aresample={SR}[o]')
sh('ffmpeg','-y','-i',src,'-filter_complex',';'.join(fc),'-map','[o]','-ac','1','work/voice.wav')

# 2) SFX
def gen(name, expr):
    sh('ffmpeg','-y','-f','lavfi','-i',expr,'-ar',str(SR),'-ac','1',f'work/sfx_{name}.wav')
gen('whoosh','anoisesrc=d=0.55:c=pink:a=0.6,highpass=f=250,lowpass=f=4200,afade=t=in:d=0.22,afade=t=out:st=0.22:d=0.33,tremolo=f=9:d=0.4')
gen('pop',   'aevalsrc=0.5*sin(2*PI*(700+1400*t)*t)*exp(-t*28):d=0.18:s=48000')
gen('ding',  'aevalsrc=0.35*(sin(2*PI*1568*t)+0.5*sin(2*PI*2349*t))*exp(-t*7):d=0.7:s=48000')
gen('alert', 'aevalsrc=0.35*sin(2*PI*if(lt(t\\,0.14)\\,740\\,988)*t)*if(lt(t\\,0.3)\\,1\\,0)*exp(-mod(t\\,0.14)*9):d=0.35:s=48000')
def load(n):
    w = wave.open(f'work/sfx_{n}.wav'); d = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return d

# 3) peta masa sumber -> masa baharu (frame)
def newt(ts):
    f = ts * FPS; off = 0
    for a, b in KEEP:
        if a <= f < b: return (off + f - a) / FPS
        off += b - a
    return None
EV = [(0.5,'whoosh'),(3.7,'alert'),(5.4,'whoosh'),(10.2,'alert'),(12.4,'whoosh'),(13.6,'pop'),(15.3,'pop'),
      (18.0,'whoosh'),(18.2,'pop'),(23.6,'ding'),(25.4,'ding'),(27.2,'ding'),(28.5,'ding'),
      (30.55,'whoosh'),(33.3,'whoosh'),(36.3,'pop'),(37.9,'pop'),(39.2,'pop'),(40.2,'pop'),(42.2,'whoosh'),(42.5,'ding')]
voice = wave.open('work/voice.wav'); v = np.frombuffer(voice.readframes(voice.getnframes()), np.int16).astype(np.float32) / 32768
mix = np.zeros_like(v)
gain = {'whoosh': 0.35, 'pop': 0.5, 'ding': 0.4, 'alert': 0.35}
for ts, k in EV:
    t = newt(ts)
    if t is None: continue
    d = load(k) * gain[k]; i = int(t * SR); mix[i:i+len(d)] += d[:len(mix)-i]
out = np.clip(v + mix, -1, 1)
w = wave.open('work/mixed.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()

# 4) loudnorm + mux
sh('ffmpeg','-y','-i',vid,'-i','work/mixed.wav','-map','0:v','-map','1:a','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89',
   '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-shortest','-movflags','+faststart',dst)
