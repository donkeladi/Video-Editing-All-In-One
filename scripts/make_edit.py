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

def side(a, b):
    seg = M[int(a * 30):max(int(b * 30), int(a * 30) + 2)]
    l, r = seg[:, 2].mean() + 1e-6, seg[:, 3].mean() + 1e-6
    return ("L" if l > r else "R"), max(l, r) / min(l, r)

POS = {"L": (.22, .37), "R": (.78, .37)}
edl = []; cam = "A"; nA = 0; lastside = None
for a, b, kind in shots:
    if kind == "F":
        sd, _ = side(a, b); cx, cy = POS[sd]
        edl.append(dict(t0=a, t1=b, cam="B", z=1.9, cx=cx, cy=cy + .02)); cam = "A"; continue
    if cam == "B":
        sd, ratio = side(a, b)
        if ratio < 1.12: edl.append(dict(t0=a, t1=b, cam="B", z=1.0, cx=.5, cy=.5))
        else:
            cx, cy = POS[sd]; edl.append(dict(t0=a, t1=b, cam="B", z=1.65, cx=cx, cy=cy))
        cam = "A"
    else:
        nA += 1
        edl.append(dict(t0=a, t1=b, cam="A", z=1.3 if nA % 3 == 0 else 1.0, cx=.5, cy=.42)); cam = "B"
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
for t, st, sf in FUN:
    fx["memes"].append(dict(t=t, d=1.5, png=f"assets/memes/{st}.png", w=760, y=230))
    fx["sfx"] += [dict(t=t, file="assets/sfx/pop.wav", vol=.5), dict(t=t + .05, file=f"assets/sfx/{sf}.wav", vol=.75)]
json.dump(fx, open("work/fx.json", "w"), indent=1)

# ---- 5. subtitle ASS
FIX = {"Hishan": "Hasha", "hishan": "Hasha"}
def clean(w):
    w = FIX.get(w.strip(" .,"), w.strip())
    return w.rstrip(".,")
groups = []; cur = []
for w in words:
    txt = clean(w["w"])
    if not txt: continue
    if cur and (w["s"] - cur[-1]["e"] > .45 or len(cur) >= 3 or sum(len(c["t"]) for c in cur) + len(txt) > 13):
        groups.append(cur); cur = []
    cur.append(dict(t=txt, s=w["s"], e=w["e"]))
    if txt.endswith(("?", "!")): groups.append(cur); cur = []
if cur: groups.append(cur)
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Inter Black,96,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,8,2,2,60,60,470,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
ev = []
for g in groups:
    a, b = to_out(g[0]["s"]), to_out(g[-1]["e"])
    if a is None or b is None or b <= a: continue
    b = max(b, a + .45)
    txt = " ".join(x["t"] for x in g).upper()
    ev.append(f"Dialogue: 0,{ts(a)},{ts(b + .05)},Default,,0,0,0,,{{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}}{txt}")
open("work/subs.ass", "w").write(hdr + "\n".join(ev) + "\n")
print(f"shots={len(edl)} jumlah={TOTAL:.1f}s sticker={len(fx['memes'])} sub={len(ev)}")
