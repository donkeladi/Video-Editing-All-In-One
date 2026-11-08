"""Soundtrack + SFX procedural (numpy/scipy) + VO + ducking. Semua masa dari src/events.json & src/vo.json.
Output: work/audio/mix_raw.wav (48k stereo, belum loudnorm)."""
import json, pathlib, subprocess
import numpy as np, soundfile as sf
from scipy import signal
ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 48000
ev = json.loads((ROOT/"src/events.json").read_text()); vo = json.loads((ROOT/"src/vo.json").read_text())
END = ev["duration"]; N = int(END*SR) + SR
rng = np.random.default_rng(20261108)
t_ax = lambda d: np.arange(int(d*SR))/SR
def put(buf, x, t0, gain=1.0, pan=0.0):
    i = int(t0*SR); n = min(len(x), buf.shape[1]-i)
    if n <= 0 or i < 0: return
    buf[0, i:i+n] += x[:n]*gain*(1-max(0,pan)); buf[1, i:i+n] += x[:n]*gain*(1+min(0,pan))
def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, f1, f2, o=2): return signal.sosfilt(signal.butter(o, [f1, f2], "band", fs=SR, output="sos"), x)
def env_exp(n, tau): return np.exp(-np.arange(n)/SR/tau)
mtof = lambda m: 440*2**((m-69)/12)

# ---------- instrumen ----------
def pluck(m, d=0.6):   # kalimba/marimba lembut
    t = t_ax(d); f = mtof(m)
    x = np.sin(2*np.pi*f*t)*env_exp(len(t), 0.28) + 0.35*np.sin(2*np.pi*f*4.01*t)*env_exp(len(t), 0.06) + 0.12*np.sin(2*np.pi*f*2*t)*env_exp(len(t), 0.15)
    a = np.minimum(1, t/0.003); return x*a*np.minimum(1, (d-t)/0.05)
def bass(m, d=0.5):
    t = t_ax(d); f = mtof(m); x = np.sin(2*np.pi*f*t) + 0.25*np.sin(2*np.pi*2*f*t)
    x = np.tanh(1.6*x)*np.minimum(1, t/0.008)*np.exp(-t/0.35); return lp(x, 400)*np.minimum(1, (d-t)/0.04)
def kick():
    t = t_ax(0.28); f = 48+90*np.exp(-t/0.035); ph = 2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-t/0.11)*np.minimum(1, t/0.002)
def wood():
    t = t_ax(0.09); return (np.sin(2*np.pi*880*t)*0.6 + bp(rng.standard_normal(len(t)), 1500, 4500)*0.3)*env_exp(len(t), 0.018)
def shaker(): 
    t = t_ax(0.07); return hp(rng.standard_normal(len(t)), 5500)*env_exp(len(t), 0.02)*np.minimum(1, t/0.004)
def pad(ms, d):
    t = t_ax(d); x = sum(np.sin(2*np.pi*mtof(m)*t) + 0.3*np.sin(2*np.pi*mtof(m)*2.003*t) for m in ms)/len(ms)
    return lp(x, 1800)*np.minimum(1, t/0.6)*np.minimum(1, (d-t)/0.7)
# ---------- SFX ----------
def sfx(kind):
    if kind == "whoosh":
        d = 0.38; t = t_ax(d); n = rng.standard_normal(len(t)); out = np.zeros_like(n)
        for k in range(8):
            a, b = k*len(t)//8, (k+1)*len(t)//8; fc = 500*(1+k*0.9)
            out[a:b] = bp(n, fc, fc*1.8, 2)[a:b]
        return out*np.sin(np.pi*t/d)**2*0.8
    if kind == "pop":
        t = t_ax(0.16); f = 260+420*np.exp(-t/0.03); return np.sin(2*np.pi*np.cumsum(f)/SR)*env_exp(len(t), 0.05)*np.minimum(1, t/0.002)
    if kind == "tick":
        t = t_ax(0.06); return (np.sin(2*np.pi*1850*t)*0.7 + np.sin(2*np.pi*2700*t)*0.2)*env_exp(len(t), 0.012)
    if kind == "tap":
        t = t_ax(0.12); return (np.sin(2*np.pi*(180+80*np.exp(-t/0.02))*t)*env_exp(len(t), 0.03) + lp(rng.standard_normal(len(t)), 3000)*env_exp(len(t), 0.008)*0.5)
    if kind == "impact":
        t = t_ax(0.7); f = 38+110*np.exp(-t/0.06); x = np.sin(2*np.pi*np.cumsum(f)/SR)*env_exp(len(t), 0.22) + lp(rng.standard_normal(len(t)), 1200)*env_exp(len(t), 0.06)*0.45
        return x*np.minimum(1, t/0.002)
    if kind == "stroke":   # bunyi pen/penanda
        d = 0.42; t = t_ax(d); n = bp(rng.standard_normal(len(t)), 1200, 5200)
        m = (0.55+0.45*np.sin(2*np.pi*9*t)); return n*m*np.sin(np.pi*t/d)**1.5*0.5
    if kind == "chime":
        t = t_ax(1.6); return (np.sin(2*np.pi*1318.5*t) + 0.6*np.sin(2*np.pi*1760*t) + 0.3*np.sin(2*np.pi*2637*t))*env_exp(len(t), 0.45)*np.minimum(1, t/0.004)*0.6
    raise ValueError(kind)

# ---------- muzik ----------
BPM = 96; BEAT = 60/BPM; BAR = 4*BEAT
CH = [(57, [57, 60, 64], 45), (53, [53, 57, 60], 41), (48, [48, 52, 55], 36), (55, [55, 59, 62], 43)]   # Am F C G
PENT = [69, 72, 74, 76, 79, 81]   # A minor pentatonic
sc = {s["id"]: (s["start"], s["end"]) for s in ev["scenes"]}
def section(t):
    s5b = ev["events"]["s5_swap"]["t"]; s8b = vo["L9"]["start"] - 0.2
    if t < sc["S2"][0]: return "hook"
    if t < sc["S3"][0]: return "q"
    if t < sc["S5"][0]: return "full"
    if t < s5b: return "full"
    if t < sc["S6"][0]: return "soft"
    if t < sc["S7"][0]: return "bright"
    if t < sc["S8"][0]: return "break"
    if t < s8b: return "gentle"
    return "outro"
M = np.zeros((2, N))
nbar = int(END/BAR)+2
for bar in range(nbar):
    t0 = bar*BAR; prog = CH[bar % 4]; root, tones, bassn = prog
    sec = section(t0 + 0.01)
    if sec in ("break", "outro", "soft"): put(M, pad(tones+[tones[0]+12], BAR+0.3), t0, 0.16)
    for step in range(16):
        ts = t0 + step*BEAT/4; sec = section(ts + 0.01)
        beat, sub = divmod(step, 4)
        drums = sec in ("full", "bright", "gentle", "q", "hook")
        if sec in ("full", "bright", "q", "hook") and step in (0, 8): put(M, kick(), ts, 0.55 if sec != "hook" else 0.4)
        if drums and sec != "hook" and step in (4, 12): put(M, wood(), ts, 0.35, 0.2)
        if sec in ("full", "bright", "gentle", "q", "hook") and sub in (0, 2): put(M, shaker(), ts + (0.012 if sub == 2 else 0), 0.10 if sec != "bright" else 0.13, -0.25)
        if sec == "bright" and sub == 3: put(M, shaker(), ts, 0.06, 0.25)
        if sec in ("full", "bright", "q", "gentle") and step in (0, 6, 10) and not (sec == "q" and step != 0): put(M, bass(bassn if step != 6 else bassn+7, 0.5), ts, 0.5)
        # melodi pluck (deterministik)
        dens = {"hook": 0.5, "q": 0.55, "full": 0.5, "soft": 0.3, "bright": 0.7, "break": 0.18, "gentle": 0.35, "outro": 0.22}[sec]
        if sub in (0, 2) and (rng.random() < dens or step == 0):
            m = int(rng.choice(PENT)) if step else tones[0]+12
            put(M, pluck(m), ts, 0.34, rng.uniform(-0.35, 0.35))
        if sec == "hook" and sub == 0 and beat in (0, 2): put(M, pluck(tones[(beat//2) % 3]+12, 0.5), ts, 0.28)
# riser kecil sebelum S3 dan S6 dikelaskan sebagai whoosh dalam events. Resolve akhir:
tc = ev["events"]["s8_chime"]["t"]
put(M, pad([57, 60, 64, 69], 2.6), tc - 0.05, 0.22); put(M, pluck(81, 1.2), tc, 0.34); put(M, pluck(76, 1.2), tc+0.12, 0.26)
# beat-stop: senyap muzik sekejap sebelum "terbiasa" (S7)
bs0 = ev["events"]["s7_ok"]["t"] - 0.35; bs1 = ev["events"]["s7_ok"]["t"] + 0.05
g = np.ones(N); g[int(bs0*SR):int(bs1*SR)] = 0.15; M *= signal.sosfilt(signal.butter(2, 30, "low", fs=SR, output="sos"), g)

# ---------- SFX ----------
S = np.zeros((2, N))
for name, e in ev["events"].items():
    if "sfx" in e: put(S, sfx(e["sfx"]), e["t"], 0.55*e.get("vol", 1.0))
# ---------- VO ----------
V = np.zeros((2, N))
for lid, v in vo.items():
    x, sr = sf.read(ROOT/f"work/vo/clean/{lid}.wav"); assert sr == SR
    put(V, x, v["start"], 1.0)
# envelop VO -> ducking
mono = np.abs(V[0]); win = int(0.02*SR)
rms = np.sqrt(np.convolve(mono**2, np.ones(win)/win, "same"))
act = (rms > 0.01).astype(float)
sm = np.zeros(N); a_att, a_rel = np.exp(-1/(0.04*SR)), np.exp(-1/(0.28*SR)); y = 0.0
for i in range(N):   # attack/release
    y = a_att*y + (1-a_att)*act[i] if act[i] > y else a_rel*y + (1-a_rel)*act[i]
    sm[i] = y
duck_m = 1 - sm*(1-10**(-9/20)); duck_s = 1 - sm*(1-10**(-3/20))
# kalibrasi tahap: muzik (ducked) ~ -15 dB di bawah VO semasa bercakap
Md, Sd = M*duck_m, S*duck_s
vact = sm > 0.5
rv = np.sqrt(np.mean(V[:, vact]**2)); rm = np.sqrt(np.mean(Md[:, vact]**2))
k = rv*10**(-18/20)/rm; M *= k; Md *= k
mix = V + M*duck_m + S*duck_s*1.0
# poket suara: kurangkan muzik 1-5 kHz semasa VO (EQ dinamik ringkas)
Mpock = np.stack([bp(M[c], 1000, 5000, 2) for c in range(2)])
mix -= Mpock*duck_m*sm*0.35
# fade ekor 300ms, trim
mix = mix[:, :int(END*SR)]; fi = int(0.3*SR); mix[:, -fi:] *= np.linspace(1, 0, fi)
(ROOT/"work/audio").mkdir(parents=True, exist_ok=True)
sf.write(ROOT/"work/audio/mix_raw.wav", mix.T.astype(np.float32), SR)
sf.write(ROOT/"work/audio/vo_only.wav", V[:, :int(END*SR)].T.astype(np.float32), SR)
print("peak", float(np.max(np.abs(mix))), "music offset dB", 20*np.log10(k), "vo rms", rv)
