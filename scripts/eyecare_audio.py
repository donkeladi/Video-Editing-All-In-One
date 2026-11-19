#!/usr/bin/env python3
"""Audio Eye Care: suara asal (utama) + muzik instrumental procedural + SFX procedural, ducking, -14 LUFS.
Tiada TTS. Keluaran: work/audio_final.wav"""
import os, subprocess, json, re
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDL = json.load(open(os.path.join(ROOT, "scripts/eyecare_edl.json")))
CUTS = [tuple(c) for c in EDL["cuts"]]; CUT = EDL["cut_end"]; SR = 44100
REMOVED = sum(b - a for a, b in CUTS)
TOTAL = CUT + EDL["tail"] - REMOVED          # tempoh output
def s2o(ts): return ts - sum(min(max(ts - a, 0), b - a) for a, b in CUTS)
N = int(TOTAL * SR)
rng = np.random.default_rng(7)
def tt(n): return np.arange(n) / SR

# ---- suara asal: hanya buang bahagian gagap (EDL); tiada susunan semula ----
keep, s = [], 0.0
for a, b in CUTS: keep.append((s, a)); s = b
keep.append((s, CUT))
parts, labels = [], []
for i, (a, b) in enumerate(keep):
    f = f"atrim={a}:{b},asetpts=PTS-STARTPTS"
    if i > 0: f += ",afade=t=in:d=0.01"
    f += f",afade=t=out:st={b - a - (0.06 if i == len(keep) - 1 else 0.01):.3f}:d={0.06 if i == len(keep) - 1 else 0.01}"
    parts.append(f"[0:a]{f}[a{i}]"); labels.append(f"[a{i}]")
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(keep)}:v=0:a=1,highpass=f=75,acompressor=threshold=-24dB:ratio=2.2:attack=8:release=160:makeup=2[o]"
raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", os.path.join(ROOT, "input/raw.mov"), "-filter_complex", fc, "-map", "[o]",
    "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"])
v = np.frombuffer(raw, np.float32).copy()
voice = np.zeros(N, np.float32); voice[:len(v)] = v[:N]

# ---- envelope suara untuk ducking ----
def smooth_env(x, win=0.05):
    w = int(win * SR); k = np.ones(w) / w
    e = np.sqrt(np.convolve(x ** 2, k, "same"))
    return e
env = smooth_env(voice)
speech = np.clip((env - 0.004) / 0.03, 0, 1)
# serangan pantas, lepas perlahan
duck = np.zeros(N); cur = 0.0
a_att, a_rel = 1 - np.exp(-1 / (0.04 * SR)), 1 - np.exp(-1 / (0.45 * SR))
sp = speech[::20]
d_small = np.zeros(len(sp))
for i, s in enumerate(sp):
    cur += (s - cur) * (a_att if s > cur else a_rel); d_small[i] = cur
duck = np.interp(np.arange(N), np.arange(len(sp)) * 20, d_small)
duck_gain = 1 - 0.62 * duck

# ---- muzik: pad + arpeggio lembut, A minor, 72 bpm ----
def note(f): return 440 * 2 ** ((f - 69) / 12)
chords = [[57, 60, 64, 71], [53, 57, 60, 67], [48, 55, 64, 67], [55, 59, 62, 69]]  # Am9, Fmaj7, Cmaj7, G6
bpm = 72; beat = 60 / bpm; bar = 4 * beat
music = np.zeros((2, N), np.float32)
t_all = tt(N)
for ci in range(int(TOTAL / (2 * bar)) + 2):
    t0 = ci * 2 * bar; ch = chords[ci % 4]
    i0 = int(t0 * SR); i1 = min(N, int((t0 + 2 * bar + 1.2) * SR))
    if i0 >= N: break
    tl = np.arange(i1 - i0) / SR; L = 2 * bar
    env_p = np.clip(tl / 1.6, 0, 1) * np.where(tl < L, 1, np.exp(-(tl - L) * 3.0))
    pad = np.zeros(len(tl))
    for m in ch:
        f = note(m)
        for det in (-0.4, 0, 0.4):
            pad += np.sin(2 * np.pi * (f + det) * tl) * 0.5 + np.sin(2 * np.pi * 2 * (f + det) * tl) * 0.12
    pad *= env_p * 0.05
    bass = np.sin(2 * np.pi * note(ch[0] - 12) * tl) * env_p * 0.12
    music[0, i0:i1] += (pad + bass)[: i1 - i0]; music[1, i0:i1] += (pad + bass)[: i1 - i0]
    # arpeggio (kalimba lembut)
    seq = [0, 2, 3, 2, 1, 2, 3, 2, 0, 2, 3, 2, 1, 3, 2, 1]
    for si, idx in enumerate(seq):
        ts = t0 + si * beat / 2
        j0 = int(ts * SR)
        if j0 >= N: break
        f = note(ch[idx] + 12); n = int(0.9 * SR); tl2 = np.arange(n) / SR
        pl = (np.sin(2 * np.pi * f * tl2) + 0.25 * np.sin(2 * np.pi * 2.01 * f * tl2)) * np.exp(-tl2 * 5.5) * 0.045
        j1 = min(N, j0 + n); pan = 0.35 + 0.3 * ((si % 4) / 3)
        music[0, j0:j1] += pl[: j1 - j0] * (1 - pan) * 1.3; music[1, j0:j1] += pl[: j1 - j0] * pan * 1.3
# lowpass ringan (one-pole) + stereo delay
def lp(x, fc):
    a = 1 - np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s += a * (x[i] - s); y[i] = s
    return y
for c in range(2): music[c] = lp(music[c], 2600)
dly = int(0.31 * SR); music[1, dly:] += music[0, :-dly] * 0.25; music[0, dly:] += music[1, :-dly] * 0.18
# automasi tahap muzik
def lerp_env(points):
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    return np.interp(t_all, xs, ys)
mg = lerp_env([(0, 0), (s2o(1.5), 0.8), (s2o(46.0), 0.8), (s2o(46.8), 0.22), (s2o(57.0), 0.22), (s2o(58.4), 0.8), (s2o(74.0), 0.8), (s2o(74.6), 1.15), (s2o(76.6), 1.0), (TOTAL, 0)])
music *= (mg * duck_gain).astype(np.float32)[None, :]

# ---- SFX procedural ----
sfx = np.zeros((2, N), np.float32)
def add(x, t0, g=1.0, pan=0.5):
    i0 = int(t0 * SR)
    if i0 >= N or i0 < 0: return
    i1 = min(N, i0 + len(x)); sfx[0, i0:i1] += x[: i1 - i0] * g * (1 - pan) * 2; sfx[1, i0:i1] += x[: i1 - i0] * g * pan * 2
def whoosh(dur=0.36):
    n = int(dur * SR); x = rng.standard_normal(n); y = np.zeros(n); s1 = s2 = 0.0
    for i in range(n):
        u = i / n; fc = 300 + 5200 * (u ** 2)
        a = 1 - np.exp(-2 * np.pi * fc / SR)
        s1 += a * (x[i] - s1); s2 += a * (s1 - s2); y[i] = s1 - s2
    y *= np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return (y / (np.abs(y).max() + 1e-9) * 0.5).astype(np.float32)
def slam():
    n = int(0.7 * SR); tl = np.arange(n) / SR
    f = 42 + 90 * np.exp(-tl * 18); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tl * 6.5)
    nz = rng.standard_normal(n) * np.exp(-tl * 40) * 0.35
    nz = lp(nz.astype(np.float64), 4000)
    return ((body * 0.95 + nz) * 0.9).astype(np.float32)
def bloop():
    n = int(0.22 * SR); tl = np.arange(n) / SR
    f = 380 + 520 * np.exp(-tl * 22); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-tl * 18) * 0.5).astype(np.float32)
def tick():
    n = int(0.02 * SR); tl = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1500 * tl) * np.exp(-tl * 220) * 0.35).astype(np.float32)
def pop():
    n = int(0.12 * SR); tl = np.arange(n) / SR
    return (np.sin(2 * np.pi * (620 + 300 * np.exp(-tl * 30)) * tl) * np.exp(-tl * 28) * 0.35).astype(np.float32)
def chime(f):
    n = int(1.6 * SR); tl = np.arange(n) / SR
    return ((np.sin(2 * np.pi * f * tl) + 0.3 * np.sin(2 * np.pi * 2 * f * tl)) * np.exp(-tl * 2.6) * 0.22).astype(np.float32)
EV = []  # (jenis, masa) - untuk laporan
W = whoosh()
for tc in (3.9, 46.4, 71.6): add(W, s2o(tc) - 0.20, 0.75); EV.append(("whoosh", tc))
for ts in (0.0, 47.0): add(slam(), s2o(ts), 0.9); EV.append(("slam", ts))
for tb in (4.47, 4.72, 4.97): add(bloop(), tb, 0.8, pan=0.5); EV.append(("bloop", tb))
for i in range(22):
    tk = s2o(11.82 + 1.4 * (i / 22) ** 0.6); add(tick(), tk, 0.5)
add(pop(), s2o(13.2), 0.9)
for tp in (9.55, 15.4, 22.3, 31.6, 49.0, 58.06, 66.7): add(pop(), s2o(tp), 0.55)
add(chime(note(81)), s2o(74.55), 0.8, 0.4); add(chime(note(76)), s2o(74.85), 0.7, 0.6)
sfx *= (0.35 + 0.65 * (1 - duck_gain / 1.0 * 0 )).astype(np.float32)[None, :] if False else 1.0

# ---- mix ----
mix = np.stack([voice, voice]) * 1.0 + music + sfx * 0.9
mix = np.clip(mix, -4, 4).astype(np.float32)
raw = mix.T.copy().tobytes()
def run_ln(extra):
    return subprocess.run(["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", extra, "-f", "null", "-"],
                          input=raw, capture_output=True)
m = run_ln("loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json").stderr.decode()
js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", m, re.S).group(0))
flt = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
       f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,volume=-1.4dB,alimiter=limit=0.85")
out = os.path.join(ROOT, "work/audio_final.wav")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", flt, "-ar", "48000", out], input=raw, check=True)
print(json.dumps({"measured": js, "events": EV}, indent=1))
