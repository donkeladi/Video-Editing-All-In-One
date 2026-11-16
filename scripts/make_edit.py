#!/usr/bin/env python3
"""Rancang suntingan (mod silih ganti A/B + zoom orang aktif) -> work/edl.json, work/fx.json, work/subs.ass"""
import json, random, numpy as np

random.seed(11)
S = json.load(open("work/A.json"))
rms = np.load("work/rmsA.npy")          # 0.25s
M = np.load("work/motion_B.npy")        # 30fps: [kiriBadan, kananBadan, kiriKepala, kananKepala]
DUR = 187.5
words = [w for s in S for w in s["words"]]

# ---- 1. julat disimpan: buang senyap panjang (>4.2s) tapi tinggalkan 1.5s tiap hujung
def has_word(t): return any(w["s"] - .1 <= t <= w["e"] + .1 for w in words)
quiet = [(not has_word(i * .25 + .125)) and rms[i] < 0.12 for i in range(len(rms))]
cuts = []; i = 0
while i < len(quiet):
    if quiet[i]:
        j = i
        while j < len(quiet) and quiet[j]: j += 1
        a, b = i * .25, j * .25
        if b - a > 4.2: cuts.append((a + 1.5, b - 1.5))
        i = j
    else: i += 1
keep = []; p = 0.0
for a, b in cuts: keep.append((p, a)); p = b
keep.append((p, DUR))
print("senyap dibuang:", [(round(a, 1), round(b, 1)) for a, b in cuts])

# ---- 2. momen kelakar (ketawa) -> sticker + sfx
FUN = [(34.2, "haha", "boing"), (54.2, "serius", "scratch"), (73.2, "bruh", "boom"), (76.8, "ngapa", "boing"),
       (79.5, "mati", "boom"), (94.5, "takut", "boom"), (100.2, "loading", "scratch"), (104.8, "wah", "airhorn"),
       (120.0, "noway", "boom"), (129.5, "genius", "ding"), (133.5, "kayuapi", "badumtss"),
       (147.0, "siapatanya", "scratch"), (160.8, "sigma", "sadtrombone"), (170.2, "haha", "badumtss"),
       (174.2, "mati", "boing")]
def kept(t): return any(a <= t <= b for a, b in keep)
FUN = [f for f in FUN if kept(f[0] - .3) and kept(f[0] + 1.8)]

# ---- 3. potong shot
gaps = sorted(set(round((a["e"] + b["s"]) / 2, 2) for a, b in zip(words, words[1:]) if b["s"] - a["e"] >= .1))
def snap(t, lo, hi):
    c = [g for g in gaps if lo < g < hi and abs(g - t) < .6]
    return min(c, key=lambda g: abs(g - t)) if c else t

shots = []
forced = [(max(t - .3, 0), min(t + 1.9, DUR)) for t, _, _ in FUN]
for a, b in keep:
    t = a
    while t < b - .05:
        nxt = [f for f in forced if f[0] >= t - .01 and f[0] < b]
        fa = nxt[0] if nxt else None
        if fa and abs(fa[0] - t) < .01:
            shots.append((fa[0], min(fa[1], b), "F")); t = min(fa[1], b); continue
        end = t + random.uniform(1.9, 3.1)
        if fa and end > fa[0] - .5: end = fa[0]
        end = min(end, b)
        if b - end < 1.0 and not (fa and end == fa[0]): end = b
        if end < b: end = snap(end, t + 1.0, b)
        if end - t < .3: t = end; continue
        shots.append((t, end, "N")); t = end

import cv2
_capA = cv2.VideoCapture("input/A.mp4")
def a_subject(a, b, z):
    """Anggar siapa dalam bingkai A: share merah (0..1) ikut jumlah piksel hijab/baju merah."""
    _capA.set(cv2.CAP_PROP_POS_MSEC, (a + b) / 2 * 1000); ok, f = _capA.read()
    if not ok: return .5
    r = cv2.resize(f, (108, 192)); hs = cv2.cvtColor(r, cv2.COLOR_BGR2HSV)
    m = (((hs[..., 0] > 165) | (hs[..., 0] < 6)) & (hs[..., 1] > 110) & (hs[..., 2] > 40))[:130].mean()
    return 1.0 if m > .12 else 0.0 if m < .025 else .5

POS = {"L": (.22, .37), "R": (.78, .37)}     # L = baju putih (Pija), R = baju merah (Hasha)
# lulus 1: tetapkan kamera (silih ganti) dan ukur masa A bagi setiap orang
plan = []; cam = "A"; nA = 0; acc = {"L": 0.0, "R": 0.0}
for a, b, kind in shots:
    d = b - a
    if kind == "F": plan.append(("B", a, b, "F")); cam = "A"; continue
    if cam == "A":
        nA += 1; share = a_subject(a, b, 1.0); acc["R"] += d * share; acc["L"] += d * (1 - share)
        plan.append(("A", a, b, nA)); cam = "B"
    else:
        plan.append(("B", a, b, "N")); cam = "A"
# lulus 2: shot B zoom ke orang yang kurang masa (seimbang 50/50)
edl = []; nB = 0
for c, a, b, tag in plan:
    d = b - a
    if c == "A":
        edl.append(dict(t0=a, t1=b, cam="A", z=1.3 if tag % 3 == 0 else 1.0, cx=.5, cy=.42)); continue
    nB += 1
    if tag == "N" and nB % 5 == 0:                        # sesekali shot lebar (kedua-duanya)
        acc["L"] += d / 2; acc["R"] += d / 2
        edl.append(dict(t0=a, t1=b, cam="B", z=1.0, cx=.5, cy=.5)); continue
    sd = "L" if acc["L"] <= acc["R"] else "R"; acc[sd] += d; cx, cy = POS[sd]
    edl.append(dict(t0=a, t1=b, cam="B", z=1.9 if tag == "F" else 1.65, cx=cx, cy=cy + (.02 if tag == "F" else 0), who=sd))
print("masa fokus  Pija(putih)=%.1fs  Hasha(merah)=%.1fs" % (acc["L"], acc["R"]))
for e in edl:  # kunci tempoh kepada gandaan 1/30s supaya video & audio tak melarat
    e["t0"] = round(e["t0"], 3); e["t1"] = round(e["t0"] + round((e["t1"] - e["t0"]) * 30) / 30, 4)
json.dump(edl, open("work/edl.json", "w"), indent=1)

# ---- 4. masa asal -> masa output
tmap = []; acc = 0.0
for e in edl: tmap.append((e["t0"], e["t1"], acc)); acc += e["t1"] - e["t0"]
TOTAL = acc
def to_out(t):
    for a, b, o in tmap:
        if a - 1e-6 <= t <= b + 1e-6: return o + t - a
    return None

fx = {"memes": [], "sfx": [], "mute": []}
for t, st, sf in FUN:   # sticker dibuang -> SFX sahaja
    fx["sfx"].append(dict(t=t, file=f"assets/sfx/{sf}.wav", vol=.75))
json.dump(fx, open("work/fx.json", "w"), indent=1)

# ---- 5. subtitle ASS: ayat-ayat bersih, perkataan aktif diserlahkan (kuning)
import os, re
A2W = [w for sg in json.load(open("work/A2.json")) for w in sg["words"]]
A1W = words
def span_words(a, b, text):   # ganti perkataan dalam [a,b) dengan teks baru, masa diagih sekata
    global A2W
    rm = [w for w in A2W if a <= w["s"] < b]
    A2W = [w for w in A2W if not (a <= w["s"] < b)]
    if not text or not rm: return
    t0, t1 = rm[0]["s"], rm[-1]["e"]; toks = text.split(); d = (t1 - t0) / len(toks)
    A2W += [dict(w=tk, s=t0 + i * d, e=t0 + (i + 1) * d, k=1) for i, tk in enumerate(toks)]
for a, b in ((0, 1.2), (54.3, 54.9), (149.1, 152.3), (152.9, 154.4), (177.5, 178.3)): span_words(a, b, "")      # tak pasti -> buang
for a, b, tx in ((24.6, 28.9, "Kita ada warna"), (125.4, 126.5, "Okey, kita try lah"), (139.4, 141.3, "Lagi, lagi, lagi"),
                 (142.7, 144.3, "Kenapa bagi sekarang?"), (145.1, 145.9, "Kenapa nak retake?"),
                 (146.1, 147.4, "Kenapa tak boleh retake?"), (154.5, 156.1, "Okey lah, boleh lah"),
                 (160.7, 162.4, "Oh, closing lah!")): span_words(a, b, tx)
A2W = [w for w in A2W if not (62.7 <= w["s"] < 124.5)] + [w for w in A1W if 62.7 <= w["s"] < 124.5]  # pusingan permainan: transkrip pertama lebih tepat
SUBW = sorted(A2W, key=lambda w: w["s"])
FIX = {"bijak": "Pija", "syah": "Hasha", "aisyah": "Hasha", "okay": "Okey", "ok": "Okey", "hishan": "Hasha"}
FILLER = {"okey", "hmm", "ahai", "aduh"}
def clean(w):
    w = w.strip()
    core = w.strip(".,?!…").lstrip("-")
    core = FIX.get(core.lower().replace("-", ""), core)
    return core + ("?" if w.endswith("?") else "!" if w.endswith("!") else "")
groups = []; cur = []
def flush():
    global cur
    if cur: groups.append(cur)
    cur = []
for w in SUBW:
    txt = clean(w["w"])
    if not txt or (txt.strip("?!").lower() in FILLER and not w.get("k")): continue
    if cur and (w["s"] - cur[-1]["e"] > .5 or len(cur) >= 4 or sum(len(c["t"]) + 1 for c in cur) + len(txt) > 20): flush()
    cur.append(dict(t=txt, s=w["s"], e=w["e"]))
    raw = w["w"].strip()
    if raw.endswith((".", "?", "!", "…")) or (raw.endswith(",") and len(cur) >= 2): flush()
flush()
for g in groups: g[0]["t"] = g[0]["t"][:1].upper() + g[0]["t"][1:]
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); sec = x % 60
    return f"{h}:{m:02d}:{sec:05.2f}"
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Inter ExtraBold,80,&H00FFFFFF,&H000000FF,&H00101010,&H96000000,0,0,0,0,100,100,0,0,1,7,3,2,70,70,430,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
YEL = r"{\c&H00E6FF&\fscx108\fscy108}"; WHT = r"{\c&HFFFFFF&\fscx100\fscy100}"
ev = []
for g in groups:
    for k, w in enumerate(g):
        a = to_out(w["s"]); nxt = g[k + 1]["s"] if k + 1 < len(g) else None
        e_src = (nxt if nxt is not None and nxt - w["e"] < .35 else w["e"] + .12)
        b = to_out(e_src) if to_out(e_src) is not None else None
        if a is None or b is None: continue
        if k == 0 and False: pass
        b = max(b, a + .12)
        line = " ".join((YEL + x["t"] + WHT) if j == k else x["t"] for j, x in enumerate(g))
        ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Default,,0,0,0,,{line}")
open("work/subs.ass", "w").write(hdr + "\n".join(ev) + "\n")
print(f"shots={len(edl)} jumlah={TOTAL:.1f}s sfx={len(fx['sfx'])} baris_sub={len(groups)} acara={len(ev)}")
