#!/usr/bin/env python3
"""Jana muzik ambient romantik (pad + pluck piano-ish) sebagai WAV. Guna: music_pad.py out.wav durasi"""
import sys, numpy as np
out, dur = sys.argv[1], float(sys.argv[2])
sr = 44100
n = int(dur*sr); t = np.arange(n)/sr
L = np.zeros(n); R = np.zeros(n)
def hz(m): return 440*2**((m-69)/12)
# Cmaj7 - Am7 - Fmaj7 - G6, 9.5s setiap satu, diulang
chords = [[48,55,59,64],[45,52,55,60],[41,48,52,57],[43,50,55,59]]
cl = 9.5
for ci in range(int(dur//cl)+1):
    s = ci*cl; ch = chords[ci%4]
    for k,m in enumerate(ch):
        f = hz(m)
        for det,pan in ((-0.15,0.35),(0.15,0.65)):
            w = np.sin(2*np.pi*(f+det)*t)+0.3*np.sin(2*np.pi*2*(f+det)*t)
            e = np.clip((t-s)/3.0,0,1)*np.clip((s+cl+2.0-t)/3.0,0,1)
            e = np.where((t>=s)&(t<s+cl+2.0), e, 0)
            e *= 0.5+0.5*np.sin(2*np.pi*0.1*t+k)
            w = w*e*0.035
            L += w*(1-pan); R += w*pan
    # pluck arpeggio (hujung lagu lebih jarang)
    notes = [ch[0]+12, ch[2]+12, ch[3]+12, ch[1]+24, ch[3]+12, ch[2]+12, ch[1]+24, ch[3]+24]
    for j,m in enumerate(notes):
        st = s + j*1.1875
        if st >= dur: break
        tt = t-st; mk = tt>=0
        f = hz(m)
        w = np.zeros(n)
        w[mk] = (np.sin(2*np.pi*f*tt[mk])+0.4*np.sin(2*np.pi*2*f*tt[mk])*np.exp(-6*tt[mk])) * np.exp(-2.2*tt[mk]) * np.minimum(tt[mk]*200,1)
        pan = 0.3+0.4*((j*37)%10)/10
        L += w*0.09*(1-pan); R += w*0.09*pan
fade = np.clip(t/2.0,0,1)*np.clip((dur-t)/3.0,0,1)
L*=fade; R*=fade
m = max(abs(L).max(), abs(R).max()); L/=m; R/=m
import wave
d = (np.stack([L,R],1)*0.8*32767).astype('<i2')
with wave.open(out,'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(d.tobytes())
