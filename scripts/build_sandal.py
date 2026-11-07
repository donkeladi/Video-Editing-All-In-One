#!/usr/bin/env python3
"""Sandal Candia TikTok: buang filler -> jump-cut punch-in -> B-roll warna -> badge -> subtitle word-highlight -> -14 LUFS.
Guna: python3 scripts/build_sandal.py   (perlukan work/main.mov + work/words.json + B-roll dalam work/broll/)"""
import json, subprocess as sp, os, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
os.makedirs("work/spr", exist_ok=True)
words = json.load(open("work/words.json"))  # [text,start,end,prob]

# ---- 1. Pembetulan teks (salah dengar ASR) & filler yang dibuang ----------------
FIX = {28: "span", 65: "Gold", 66: "chain", 71: "sandal", 83: "sandal", 75: "Saki",
       78: "Lelaki", 81: "Kasi", 91: "PU", 124: "kuning", 95: "melecet"}
DROP = {0, 5, 29, 74, 85, 98}          # Eh, aa, aa, Okay, Okay, Okay
CAPEND = {28: 0.5}                      # timestamp 'spun' meleret

kept = []
for i, (t, s, e, p) in enumerate(words):
    if i in DROP: continue
    t = FIX.get(i, t.strip()); t = re.sub(r"[,.]+$", "", t)
    nxt = words[i + 1][1] if i + 1 < len(words) else e
    e = min(e, s + CAPEND.get(i, 0.9)) if i < 126 else e
    if t in ("%",) or t.startswith("-"):   # sambung ke perkataan sebelum (100%, macam-macam)
        kept[-1]["t"] += t; kept[-1]["e"] = e; kept[-1]["ix"] = i; continue
    kept.append(dict(i=i, t=t, s=s, e=e))

# ---- 2. Segmen potongan ----------------------------------------------------------
segs = []; cur = None
for k, w in enumerate(kept):
    prev = kept[k - 1] if k else None
    brk = (prev is None) or (w["i"] - prev["i"] > 1) or (w["s"] - prev["e"] > 0.30)
    if brk:
        cur = dict(a=max(w["s"] - 0.05, 0), b=w["e"] + 0.07, ws=[w]); segs.append(cur)
    else:
        cur["b"] = w["e"] + 0.07; cur["ws"].append(w)
for k in range(len(segs) - 1):          # elak bertindih
    if segs[k]["b"] > segs[k + 1]["a"]: segs[k]["b"] = segs[k + 1]["a"] - 0.005
segs[-1]["b"] = min(segs[-1]["b"], 49.6)
T = 0.0
for s in segs:
    s["o"] = T; T += s["b"] - s["a"]
total = T
tm = {}                                  # index perkataan -> masa baru
for s in segs:
    for w in s["ws"]:
        w["ns"] = s["o"] + (w["s"] - s["a"]); w["ne"] = s["o"] + (w["e"] - s["a"])
        tm[w["i"]] = w
print(f"{len(segs)} segmen, jumlah {total:.2f}s (asal 49.7s)")

# ---- 3. Overlay B-roll & badge (anchor pada perkataan) --------------------------
def at(i, end=False): return tm[i]["ne" if end else "ns"]
broll = []   # (fail, mula, tamat)
t0 = at(43); span = (at(47, True) - t0)
for j, f in enumerate(["1689", "1690", "1691", "1692"]):
    a = t0 + j * span / 4; broll.append((f, a, a + span / 4))
broll.append(("1694", at(48), at(53, True) + 0.1))
broll.append(("1693", at(55), at(59, True)))
broll.append(("1696", at(122), at(125, True) + 0.15))

F = lambda w, s: ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", s)
def pill(name, text, size=46, fill=(255, 255, 255, 240), fg=(28, 28, 30)):
    f = F("Bold", size); tw = int(f.getlength(text)); h = int(size * 2.2); w = tw + 100; pad = 50
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + w, pad + h + 10), h // 2, fill=(0, 0, 0, 80))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((pad, pad, pad + w, pad + h), h // 2, fill=fill)
    d.ellipse((pad + 30, pad + h / 2 - 9, pad + 48, pad + h / 2 + 9), fill=(212, 170, 60))
    d.text((pad + 62 + (w - 100) / 2 - 0, pad + h / 2), text, font=f, fill=fg, anchor="mm") if False else \
        d.text((pad + 60, pad + h / 2), text, font=f, fill=fg, anchor="lm")
    im.save(f"work/spr/{name}.png"); return f"work/spr/{name}.png", im.size
badges = [  # (png, mula, tamat, y)
    (*pill("pu", "100% PU Leather"), at(8), at(11, True) + 0.6, 330),
    (*pill("lima", "5 Pilihan Warna"), at(50), at(52, True) + 0.5, 330),
    (*pill("grip", "Anti-slip • Extra Grip"), at(108), at(113, True) + 0.4, 330),
]


# ---- CTA beranimasi: "Check out beg kuning sekarang" ---------------------------
import math
FPS = 30; CW, CH = 1000, 460
ct0 = at(121); ct1 = min(at(125, True) + 1.3, total - 0.05); cD = ct1 - ct0
def ease_back(x, c=1.9):
    x = min(max(x, 0), 1); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def cta_frame(t):
    S = 2; im = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    pw, ph = 900 * S, 190 * S; px, py = (CW * S - pw) // 2, 40 * S
    sc = ease_back(t / 0.45) if t < 0.45 else 1 + 0.03 * math.sin(2 * math.pi * (t - 0.45) * 1.7)
    al = min(t / 0.2, 1.0) * (min((cD - t) / 0.25, 1.0))
    L = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((px, py + 16 * S, px + pw, py + ph + 16 * S), ph // 2, fill=(0, 0, 0, 110))
    L = Image.alpha_composite(L, sh.filter(ImageFilter.GaussianBlur(18 * S)))
    # badan butang gradien kuning
    body = Image.new("RGBA", im.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(body)
    for yy in range(ph):
        k = yy / ph; c = (255, int(214 - 34 * k), int(70 - 30 * k), 255)
        bd.line((px, py + yy, px + pw, py + yy), fill=c)
    mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).rounded_rectangle((px, py, px + pw, py + ph), ph // 2, fill=255)
    L.paste(body, (0, 0), mask)
    # kilat sapu
    ph_s = (t * 0.9) % 1.6 - 0.3; sx = px + int(ph_s * (pw + 300 * S)) - 150 * S
    sw = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sw)
    sd.polygon([(sx, py), (sx + 90 * S, py), (sx + 30 * S, py + ph), (sx - 60 * S, py + ph)], fill=(255, 255, 255, 120))
    sw.putalpha(Image.composite(sw.getchannel("A"), Image.new("L", im.size, 0), mask)); L = Image.alpha_composite(L, sw)
    d = ImageDraw.Draw(L)
    # ikon troli dalam bulatan gelap
    cx, cy, r = px + 105 * S, py + ph // 2, 62 * S
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(28, 28, 30, 255))
    wh = (255, 214, 70, 255); lw = 7 * S
    d.line((cx - 38 * S, cy - 30 * S, cx - 26 * S, cy - 30 * S, cx - 14 * S, cy + 14 * S, cx + 30 * S, cy + 14 * S), fill=wh, width=lw, joint="curve")
    d.polygon([(cx - 22 * S, cy - 20 * S), (cx + 38 * S, cy - 20 * S), (cx + 30 * S, cy + 6 * S), (cx - 15 * S, cy + 6 * S)], fill=wh)
    for wx in (cx - 8 * S, cx + 24 * S): d.ellipse((wx - 7 * S, cy + 22 * S, wx + 7 * S, cy + 36 * S), fill=wh)
    d.text((px + 205 * S, py + 68 * S), "CHECK OUT BEG KUNING", font=F("ExtraBold", 54 * S), fill=(28, 28, 30, 255), anchor="lm")
    d.text((px + 205 * S, py + 140 * S), "SEKARANG!", font=F("ExtraBold", 50 * S), fill=(28, 28, 30, 255), anchor="lm")
    # anak panah melantun ke bawah
    bob = int(abs(math.sin(t * 2 * math.pi * 1.7)) * 22 * S); ax = CW * S // 2; ay = py + ph + 50 * S + bob
    for k, a in ((0, 255), (1, 150)):
        yy = ay + k * 34 * S
        d.line((ax - 44 * S, yy, ax, yy + 34 * S, ax + 44 * S, yy), fill=(255, 214, 70, a), width=14 * S, joint="curve")
    # percikan
    for n in range(5):
        a0 = (t * 1.3 + n / 5) % 1; ang = n * 1.256 + 0.4
        rr = (170 + 400 * a0) * S; sxp = CW * S // 2 + math.cos(ang) * rr * 1.4; syp = py + ph // 2 + math.sin(ang) * rr * 0.28
        rs = (10 * (1 - a0)) * S; d.ellipse((sxp - rs, syp - rs, sxp + rs, syp + rs), fill=(255, 235, 150, int(220 * (1 - a0))))
    # skala + alpha
    sc = max(sc, 0.05); w2, h2 = int(CW * sc), int(CH * sc)
    out = L.resize((CW, CH), Image.LANCZOS)
    out = out.resize((w2, h2), Image.LANCZOS); canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    canvas.paste(out, ((CW - w2) // 2, (CH - h2) // 2), out)
    canvas.putalpha(canvas.getchannel("A").point(lambda v: int(v * al))); return canvas
import shutil; shutil.rmtree("work/cta", ignore_errors=True); os.makedirs("work/cta")
nfr = int(cD * FPS) + 1
for n in range(nfr): cta_frame(n / FPS).save(f"work/cta/{n:04d}.png")

# ---- 4. Subtitle ASS (kata demi kata, highlight) ---------------------------------
def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
BREAK = {60, 65, 69, 75, 81, 86, 90, 93, 99, 114, 126}; NOBREAK_AFTER = {65}
chunks = []; c = []
for w in kept:
    if c and w["i"] in BREAK: chunks.append(c); c = []     # mula ayat/frasa baru
    c.append(w)
    raw = words[w["i"]][0].strip()
    if w["i"] in NOBREAK_AFTER: continue                    # "Gold chain" jangan dipisah
    if len(c) >= 3 or raw.endswith((",", ".")) and len(c) >= 2: chunks.append(c); c = []
if c: chunks.append(c)
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter,84,&H00FFFFFF,&H00FFFFFF,&H00181818,&H80000000,1,0,0,0,100,100,0,0,1,7,3,2,60,60,520,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
for ci, ch in enumerate(chunks):
    cend = ch[-1]["ne"] + 0.12
    if ci + 1 < len(chunks): cend = min(cend, chunks[ci + 1][0]["ns"])
    for k, w in enumerate(ch):
        a = w["ns"]; b = ch[k + 1]["ns"] if k + 1 < len(ch) else cend
        txt = " ".join((r"{\c&H003DC8FF&}" + x["t"] + r"{\c&H00FFFFFF&}") if m == k else x["t"] for m, x in enumerate(ch))
        pop = r"{\fscx92\fscy92\t(0,90,\fscx100\fscy100)}" if k == 0 else ""
        ass += f"Dialogue: 0,{ts(a)},{ts(b)},Sub,,0,0,0,,{pop}{txt}\n"
open("work/subs.ass", "w").write(ass)
# SRT (untuk semak / edit)
with open("work/subs.srt", "w") as f:
    for n, ch in enumerate(chunks, 1):
        e = ch[-1]["ne"] + 0.12
        sr = lambda t: ts(t).replace(".", ",").replace("0:", "00:", 1) if False else f"{int(t//3600):02d}:{int(t%3600//60):02d}:{t%60:06.3f}".replace(".", ",")
        f.write(f"{n}\n{sr(ch[0]['ns'])} --> {sr(e)}\n{' '.join(x['t'] for x in ch)}\n\n")

# ---- 5. ffmpeg filter_complex ---------------------------------------------------
inp = ["-i", "work/main.mov"]
for b in broll: inp += ["-i", f"work/broll/{b[0]}.mov"]
for bd in badges: inp += ["-loop", "1", "-i", bd[0]]
inp += ["-framerate", "30", "-i", "work/cta/%04d.png"]
fc = []
for k, s in enumerate(segs):
    z = 1.0 if k % 2 == 0 else 1.09
    zf = "" if z == 1.0 else f",scale={int(W*z)}:{int(H*z)}:flags=lanczos,crop={W}:{H}"
    fc.append(f"[0:v]trim={s['a']:.3f}:{s['b']:.3f},setpts=PTS-STARTPTS{zf},fps=30[v{k}]")
    d = s["b"] - s["a"]
    fc.append(f"[0:a]atrim={s['a']:.3f}:{s['b']:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d-0.015:.3f}:d=0.015[a{k}]")
n = len(segs)
fc.append("".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0,eq=contrast=1.05:saturation=1.10:brightness=0.01,unsharp=5:5:0.45[base]")
fc.append("".join(f"[a{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[araw]")
cur = "base"
for j, (f, a, b) in enumerate(broll):
    idx = 1 + j; d = b - a
    fc.append(f"[{idx}:v]trim=0.25:{0.25+d+0.1:.3f},setpts=PTS-STARTPTS,scale=w='{W}*(1+0.07*t/{d:.3f})':h=-2:eval=frame:flags=bicubic,"
              f"crop={W}:{H},fps=30,format=yuva420p,fade=t=in:st=0:d=0.12:alpha=1,fade=t=out:st={d-0.12:.3f}:d=0.12:alpha=1,setpts=PTS+{a:.3f}/TB[b{j}]")
    fc.append(f"[{cur}][b{j}]overlay=eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[o{j}]"); cur = f"o{j}"
base = 1 + len(broll)
for j, (png, (pw, ph), a, b, y) in enumerate(badges):
    idx = base + j
    fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={a:.3f}:d=0.18:alpha=1,fade=t=out:st={b-0.18:.3f}:d=0.18:alpha=1[g{j}]")
    fc.append(f"[{cur}][g{j}]overlay=x=(W-w)/2:y={y}-h/2+'if(lt(t-{a:.3f},0.18),(0.18-(t-{a:.3f}))*60,0)':enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[p{j}]"); cur = f"p{j}"
fc.append(f"[{base+len(badges)}:v]format=rgba,setpts=PTS-STARTPTS+{ct0:.3f}/TB[ctav]")
fc.append(f"[{cur}][ctav]overlay=x=(W-w)/2:y=300:eof_action=pass:enable='between(t,{ct0:.3f},{ct1:.3f})'[pc]"); cur = "pc"
fc.append(f"[{cur}]subtitles=work/subs.ass:fontsdir=/usr/share/fonts/opentype/inter,format=yuv420p[vout]")
fc.append("[araw]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
os.makedirs("output", exist_ok=True)
out = "output/sandal_candia_tiktok.mp4"
sp.run(["ffmpeg", "-y", *inp, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart", out], check=True)
print(out)
