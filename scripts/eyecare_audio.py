#!/usr/bin/env python3
"""Audio Eye Care: suara asal (tidak diubah) + muzik lembut procedural (ducking) + SFX procedural.
Guna: eyecare_audio.py <video> <out_dir>  -> out_dir/voice.wav, music.wav, sfx.wav, mix_raw.wav"""
import sys, os, subprocess, wave
import numpy as np
from scipy.signal import lfilter, butter, fftconvolve
sys.path.insert(0, os.path.dirname(__file__))
from eyecare_timeline import *
SR = 44100; N = int(DUR * SR); rng = np.random.default_rng(7)
db = lambda x: 10 ** (x / 20)

def load_voice(video):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", video, "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"])
    a = np.frombuffer(raw, np.float32).reshape(-1, 2); out = np.zeros((N, 2), np.float32); n = min(N, len(a)); out[:n] = a[:n]; return out

def env(x, win=0.05):
    m = np.abs(x).mean(1); k = int(win * SR); c = np.convolve(m ** 2, np.ones(k) / k, "same"); return np.sqrt(c)

def smooth_gain(target, attack=0.04, release=0.45):
    out = np.empty_like(target); g = target[0]; ca = np.exp(-1 / (attack * SR)); cr = np.exp(-1 / (release * SR))
    # blok 64 sampel supaya pantas
    B = 64
    for i in range(0, len(target), B):
        tg = target[i:i + B].min()
        g = tg + (g - tg) * (ca if tg < g else cr) ** B
        out[i:i + B] = g
    return out

# ---------------- muzik: pad + pluck lembut, 84 BPM, Cmaj7-Am7-Fmaj7-G6
def midi(n): return 440 * 2 ** ((n - 69) / 12)
def music():
    bpm = 84; beat = 60 / bpm; bar = 4 * beat
    chords = [[48, 55, 59, 64], [45, 52, 60, 64], [41, 48, 57, 64], [43, 50, 59, 64]]
    t = np.arange(N) / SR; L = np.zeros(N); R = np.zeros(N)
    nb = int(DUR / bar) + 2
    for b in range(nb):
        ch = chords[b % 4]; t0 = b * bar; i0 = int(t0 * SR); i1 = min(N, int((t0 + bar + 0.8) * SR))
        if i0 >= N: break
        tt = (np.arange(i0, i1) / SR) - t0
        e = np.minimum(1, tt / 0.9) * np.where(tt < bar, 1, np.maximum(0, 1 - (tt - bar) / 0.8))
        for k, n in enumerate(ch):
            f = midi(n)
            for det, pan in ((0.997, 0.35), (1.003, 0.65)):
                w = np.sin(2 * np.pi * f * det * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * det * tt)
                w *= e * 0.045 / (1 + 0.15 * k)
                L[i0:i1] += w * (1 - pan); R[i0:i1] += w * pan
        sub = np.sin(2 * np.pi * midi(ch[0] - 12) * tt) * e * 0.05; L[i0:i1] += sub; R[i0:i1] += sub
        # pluck arpeggio (not 8)
        pat = [0, 2, 3, 2, 1, 2, 3, 2]
        for s, pi in enumerate(pat):
            ts = t0 + s * beat / 2; j0 = int(ts * SR)
            if j0 >= N: break
            j1 = min(N, j0 + int(0.9 * SR)); tt2 = np.arange(j1 - j0) / SR; f = midi(ch[pi] + 12)
            w = (np.sin(2 * np.pi * f * tt2) + 0.3 * np.sin(2 * np.pi * 2 * f * tt2)) * np.exp(-tt2 * 5.5) * 0.030 * (1 if s % 2 == 0 else 0.7)
            w[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
            p = 0.3 + 0.4 * ((s * 0.37) % 1); L[j0:j1] += w * (1 - p); R[j0:j1] += w * p
    m = np.stack([L, R], 1)
    # reverb ringkas
    ir = rng.standard_normal(int(0.9 * SR)) * np.exp(-np.arange(int(0.9 * SR)) / SR * 4.5); ir[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    wet = np.stack([fftconvolve(m[:, c], ir, "full")[:N] for c in range(2)], 1) * 0.05
    m = m * 0.8 + wet
    fi = np.minimum(1, t / 0.8); fo = np.clip((DUR - t) / 2.2, 0, 1); m *= (fi * fo)[:, None]
    b, a = butter(2, 5200 / (SR / 2)); m = lfilter(b, a, m, axis=0)
    return m.astype(np.float32)

# ---------------- SFX procedural
def place(buf, snd, t, gain_db, pan=0.5):
    i = int(t * SR);
    if i >= N or i < 0: return
    n = min(len(snd), N - i); g = db(gain_db)
    buf[i:i + n, 0] += snd[:n] * g * (1 - pan) * 1.4; buf[i:i + n, 1] += snd[:n] * g * pan * 1.4
def sweep_noise(dur, f0, f1):
    n = int(dur * SR); x = rng.standard_normal(n); out = np.zeros(n); blk = 256; zi = None
    for i in range(0, n, blk):
        f = f0 * (f1 / f0) ** (i / n); b, a = butter(2, [max(80, f * 0.6) / (SR / 2), min(0.98, f * 1.5 / (SR / 2))], "band")
        y, zi = lfilter(b, a, x[i:i + blk], zi=zi if zi is not None else np.zeros(max(len(a), len(b)) - 1)); out[i:i + blk] = y
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5; return out * e * 2.2
def pop():
    n = int(0.14 * SR); t = np.arange(n) / SR; f = 620 * np.exp(-t * 14) + 240
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28) * 0.9
def tick():
    n = int(0.05 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 110) * 0.7
def slam():
    n = int(0.55 * SR); t = np.arange(n) / SR; f = 46 + 90 * np.exp(-t * 18)
    th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    b, a = butter(2, 2400 / (SR / 2)); ns = lfilter(b, a, rng.standard_normal(n)) * np.exp(-t * 38) * 0.6
    return th * 1.1 + ns
def shimmer():
    n = int(0.45 * SR); t = np.arange(n) / SR; x = sum(np.sin(2 * np.pi * f * t) for f in (1568, 2093, 2637)) / 3
    return x * np.exp(-t * 9) * np.minimum(1, t / 0.01) * 0.6
def sizzle(dur):
    n = int(dur * SR); x = np.zeros(n); k = 0
    imp = rng.random(n) < 0.0035; x[imp] = rng.standard_normal(imp.sum()) * 1.5
    d = np.exp(-np.arange(int(0.012 * SR)) / (0.003 * SR)); x = np.convolve(x, d, "same")
    b, a = butter(2, [2500 / (SR / 2), 9500 / (SR / 2)], "band"); x = lfilter(b, a, x)
    x += lfilter(b, a, rng.standard_normal(n)) * 0.05
    e = np.minimum(1, np.linspace(0, dur, n) / 0.5) * np.clip((dur - np.linspace(0, dur, n)) / 0.6, 0, 1); return x * e

if __name__ == "__main__":
    video, outd = sys.argv[1], sys.argv[2]; os.makedirs(outd, exist_ok=True)
    voice = load_voice(video)
    mus = music()
    # ducking: muzik turun ~10 dB bawah suara
    ve = env(voice); thr = db(-46)
    target = np.where(ve > thr, db(-10), 1.0).astype(np.float64); gain = smooth_gain(target)
    mus = (mus * gain[:, None] * db(-4)).astype(np.float32)
    sfx = np.zeros((N, 2), np.float32)
    for t, kind, g in sfx_cues():
        if kind == "slam": place(sfx, slam(), t, g)
        elif kind == "whoosh": place(sfx, sweep_noise(0.34, 500, 4500), t, g)
        elif kind == "pop": place(sfx, pop(), t, g, 0.5 + 0.1 * np.sin(t))
        elif kind == "tick": place(sfx, tick(), t, g, 0.5 + 0.15 * np.cos(t))
        elif kind == "shimmer": place(sfx, shimmer(), t, g)
        elif kind == "sizzle": place(sfx, sizzle(7.04), t, g)
    mix = voice + mus + sfx
    def wr(name, a):
        a = np.clip(a, -1, 1); w = wave.open(os.path.join(outd, name), "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype("<i2").tobytes()); w.close()
    wr("voice.wav", voice); wr("music.wav", mus); wr("sfx.wav", sfx); wr("mix_raw.wav", mix)
    print("peak", np.abs(mix).max(), "len", len(mix) / SR)
