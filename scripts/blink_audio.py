#!/usr/bin/env python3
"""Sound effect sintetik + muzik latar halus, mix dengan suara. Guna: blink_audio.py cut.mov out_mix.wav"""
import numpy as np, subprocess, sys, wave
SR = 44100
rng = np.random.default_rng(7)
vid, out = sys.argv[1:3]
raw = subprocess.run(["ffmpeg","-v","error","-i",vid,"-f","s16le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout
voice = np.frombuffer(raw,np.int16).astype(np.float32)/32768
N = len(voice)
sfx = np.zeros(N, np.float32)

def t_(d): return np.arange(int(d*SR))/SR
def env(n, a=.005, r=.1):
    e = np.ones(n); na=max(1,int(a*SR)); nr=max(1,int(r*SR))
    e[:na]=np.linspace(0,1,na); e[-nr:]=np.minimum(e[-nr:],np.linspace(1,0,nr)); return e
def put(t, s, g=1.0):
    i=int(t*SR)
    if i>=N: return
    s=s[:N-i]; sfx[i:i+len(s)]+=s*g
def lp(x, k):  # one-pole lowpass k in 0..1
    y=np.zeros_like(x); a=0
    for i in range(len(x)): a+=k*(x[i]-a); y[i]=a
    return y
def sweep(f0,f1,d,exp=True):
    t=t_(d); f=f0*(f1/f0)**(t/d) if exp else np.linspace(f0,f1,len(t))
    return np.sin(2*np.pi*np.cumsum(f)/SR)
def pop(f=520,d=.14):
    t=t_(d); return np.sin(2*np.pi*(f*(1+1.2*np.exp(-t*40)))*t)*np.exp(-t*28)*.9
def whoosh(d=.5,f0=300,f1=3500,up=True):
    n=rng.standard_normal(int(d*SR)).astype(np.float32); t=np.linspace(0,1,len(n))
    fc=f0*(f1/f0)**(t if up else 1-t)
    # band-pass sweep via time-varying one-pole filters (cheap)
    k=np.clip(2*np.pi*fc/SR,0,.9); y=np.zeros_like(n); a=0; b=0
    for i in range(len(n)): a+=k[i]*(n[i]-a); b+=k[i]*(a-b); y[i]=a-b
    y/= (np.abs(y).max()+1e-6); e=np.sin(np.pi*t)**1.5
    return y*e
def tick(f=1800,d=.05): t=t_(d); return np.sin(2*np.pi*f*t)*np.exp(-t*90)*.8
def bell(f,d=1.2):
    t=t_(d); return (np.sin(2*np.pi*f*t)+.4*np.sin(2*np.pi*f*2.01*t)+.2*np.sin(2*np.pi*f*3.2*t))*np.exp(-t*3.2)*.5
def boom(d=.9,f=70):
    t=t_(d); return np.sin(2*np.pi*(f+80*np.exp(-t*12))*t)*np.exp(-t*4.5)
def thump(d=.25): t=t_(d); return np.sin(2*np.pi*(55+40*np.exp(-t*30))*t)*np.exp(-t*14)
def noise_hit(d=.3,k=.3): n=lp(rng.standard_normal(int(d*SR)).astype(np.float32),k); return n*np.exp(-t_(d)*14)*1.2
def riser(d=1.3):
    t=t_(d); n=lp(rng.standard_normal(len(t)).astype(np.float32),.15); s=sweep(120,1400,d)
    return (s*.5+n*.8)*np.linspace(0,1,len(t))**2
def alert(d=.35): t=t_(d); return (np.sign(np.sin(2*np.pi*880*t))*.18+np.sin(2*np.pi*660*t)*.4)*env(len(t),.003,.08)*(np.sin(2*np.pi*14*t)>-.2)
def sparkle(d=.7):
    s=np.zeros(int(d*SR))
    for i,f in enumerate([1568,2093,2637,3136]):
        o=int(i*.06*SR); t=t_(d-i*.06)[:len(s)-o]; s[o:o+len(t)]+=np.sin(2*np.pi*f*t)*np.exp(-t*9)*.35
    return s
def notif(): return np.concatenate([pop(880,.12)*.9,np.zeros(int(.05*SR)),pop(1175,.16)])

# ---- garis masa (masa selepas potong) ----
put(0.00, whoosh(.45,400,4000), .45); put(0.12, pop(600), .7)
put(1.02, tick(900,.07), .5); put(1.47, tick(900,.07), .5)   # kelip mata
put(2.00, whoosh(.3,800,3000), .25)
for i in range(9): put(2.1+i*.1, tick(1400,.03), .35)           # jam
put(3.12, whoosh(.5,200,3000), .45); put(3.2, pop(700), .75)
for i in range(18): put(4.3+i*.06, tick(900+i*60,.04), .5)      # kiraan
put(5.45, bell(1046,1.0), .6); put(5.45, pop(900), .5)
put(6.8, whoosh(.45,300,3500,False), .4)
put(7.65, pop(560), .6); put(9.15, pop(420), .7); put(9.2, whoosh(.3,500,2500), .3)
for i in range(5): put(9.4+i*.12, tick(2400,.02), .25)
put(9.95, whoosh(.5,200,1800), .3)
put(10.76, boom(1.1,60), 1.0); put(10.76, noise_hit(.4,.4), .8); put(10.74, sweep(1400,90,.5)*np.exp(-t_(.5)*1.5), .45); put(11.0, alert(.35), .35)
put(12.9, whoosh(.5,2500,250,True), .35)
put(13.3, whoosh(.4,300,2500), .3)
put(15.38, noise_hit(.35,.7), .55); put(15.38, pop(480), .5)       # kering
put(15.98, sweep(2200,500,.18)*np.exp(-t_(.18)*10), .5); put(15.98, pop(700), .5)  # pedih
put(16.8, alert(.3), .55)                                                           # merah
put(18.52, sweep(300,100,.9)*np.exp(-t_(.9)*2), .6); put(18.52, whoosh(.7,2500,200), .45)  # kabur
put(19.32, riser(1.3), .6); put(20.5, boom(1.0,50), .95); put(20.5, noise_hit(.3,.5), .4)
for k in range(5): put(20.9+k*1.1, thump(), .9); put(21.1+k*1.1, thump(), .6)    # degup
put(22.5, whoosh(.4,400,3000), .3); put(22.95, tick(300,.15), .8)
put(23.86, whoosh(.7,2500,200), .4)
put(24.0, sparkle(.7), .3)
put(26.0, whoosh(.85,300,1200), .3); put(27.0, whoosh(.85,300,1200), .3)
put(27.5, pop(800), .7)
for i in range(10): put(27.7+i*.1, bell(880*2**(i/12),.25), .22)
put(28.9, whoosh(.6,300,3500), .35)
put(31.46, bell(523,1.6), .55); put(32.56, bell(659,1.6), .55); put(33.72, bell(784,2.0), .6)
for tt in (31.46,32.56,33.72): put(tt, whoosh(.35,800,4000), .2)
put(34.9, sparkle(.8), .35)
put(35.75, pop(560), .6); put(36.05, notif(), .75)
for i in range(8): put(36.2+i*.22, pop(900+i*40,.08), .25)
put(38.7, whoosh(.5,3000,200), .3)

# ---- muzik latar halus (pad Am-F-C-G) ----
t=np.arange(N)/SR; mus=np.zeros(N,np.float32)
chords=[[220,261.6,329.6],[174.6,220,261.6],[261.6,329.6,392],[196,246.9,392*.75*2/1.5]]
seg=4.0
for i,ch in enumerate(chords*3):
    a=int(i*seg*SR); b=min(N,int((i+1)*seg*SR+.4*SR))
    if a>=N: break
    tt=np.arange(b-a)/SR; e=np.minimum(1,tt/1.2)*np.minimum(1,(b-a)/SR-tt+0.0)**.5
    for f in ch: mus[a:b]+=(np.sin(2*np.pi*f*tt)+.3*np.sin(2*np.pi*f*2*tt))*e*(.5+.5*np.sin(tt*1.3+f))/3
mus*=.5/np.abs(mus).max()

# ---- mix ----
vo = voice
# duck muzik/sfx ringan bila suara bercakap
sm = np.convolve(np.abs(vo), np.ones(int(.08*SR))/int(.08*SR), 'same')
duck = 1-.45*np.clip(sm/0.05,0,1)
mix = vo*1.0 + sfx*0.55*(0.6+0.4*duck) + mus*0.10*duck
mix = np.tanh(mix*1.1)/1.1 if False else mix
pk=np.abs(mix).max(); mix=mix/max(pk,1)*0.95 if pk>.95 else mix
with wave.open(out,'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix,-1,1)*32767).astype(np.int16).tobytes())
print("ok", N/SR)
