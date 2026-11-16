#!/usr/bin/env python3
"""DS Pharma Eye Care - gaya clinical, overlay beranimasi (ASS) + CTA beranimasi + SFX halus.
Input : output/eyecare_raw_cut.mp4, work/words.json (scripts/transcribe_local.py)
Output: output/eyecare_final.mp4"""
import re, json, subprocess

V = "output/eyecare_raw_cut.mp4"
END = 5.0
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", V]))
T0 = dur                      # mula kad penutup
TOT = dur + END
TEAL, NAVY, WHITE, MINT = "&HB6C42E&", "&H401E0A&", "&HFFFFFF&", "&HD9E86B&"

def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"

# ---------- kapsyen per perkataan ----------
raw = json.load(open("work/words.json"))
W = []
for a, b, t in raw:
    if t.startswith("-") and W: W[-1][2] += t; W[-1][1] = b
    else: W.append([a, b, t])
chunks = []; cur = []
def flush():
    global cur
    if cur: chunks.append(cur); cur = []
for i, w in enumerate(W):
    cur.append(w)
    gap = (W[i + 1][0] - w[1]) if i + 1 < len(W) else 9
    if w[2][-1] in ".?!" or (w[2][-1] == "," and len(cur) >= 3) or len(cur) >= 7 or gap > .45 or sum(len(x[2]) + 1 for x in cur) > 40: flush()
flush()
KEYS = [["8", "jam"], ["24", "jam,"], ["16", "jam."], ["blue", "light"], ["20-20-20"], ["20", "minit,"], ["20", "kaki,"], ["20", "saat."],
        ["masalah", "mata"], ["Jaga", "elok-elok."], ["sepasang"]]
norm = lambda s: re.sub(r"[.,?!]", "", s).lower()
def keyflags(ch):
    f = [False] * len(ch); ws = [norm(w[2]) for w in ch]
    for k in KEYS:
        kk = [norm(x) for x in k]
        for i in range(len(ws) - len(kk) + 1):
            if ws[i:i + len(kk)] == kk: f[i:i + len(kk)] = [True] * len(kk)
    return f

ev = []
ev.append(f"Dialogue: 0,{ts(0)},{ts(TOT)},Tag,,0,0,0,,DS PHARMA EYE CARE  ·  MAL22076147T")
for ci, ch in enumerate(chunks):
    fl = keyflags(ch)
    cend = min(ch[-1][1] + .12, (chunks[ci + 1][0][0] - .02) if ci + 1 < len(chunks) else dur - .05)
    for j, w in enumerate(ch):
        s0 = max(w[0], 0); s1 = ch[j + 1][0] if j + 1 < len(ch) else cend
        if s1 <= s0 + .03: s1 = s0 + .08
        parts = []
        for k, x in enumerate(ch):
            base = TEAL if fl[k] else WHITE
            if k == j:
                parts.append(f"{{\\c{MINT if not fl[k] else TEAL}\\t(0,90,\\fscx114\\fscy114)\\t(90,190,\\fscx100\\fscy100)}}{x[2]}{{\\c{base}\\fscx100\\fscy100}}")
            else:
                parts.append(f"{{\\c{base}}}{x[2]}")
        pre = ""
        if j == 0: pre += "\\fad(90,0)\\fscx92\\fscy92\\t(0,130,\\fscx100\\fscy100)"
        if j == len(ch) - 1: pre = pre.replace("\\fad(90,0)", "\\fad(90,70)") if j == 0 else pre + "\\fad(0,70)"
        ev.append(f"Dialogue: 1,{ts(s0)},{ts(min(s1, cend if j == len(ch) - 1 else s1))},Sub,,0,0,0,,{{{pre}}}{' '.join(parts)}")

# ---------- overlay: pill / kad ----------
def pop(over=112): return f"\\fscx0\\fscy0\\t(0,150,\\fscx{over}\\fscy{over})\\t(150,270,\\fscx100\\fscy100)"
def pill(t0, t1, cx, cy, w, h, big, small, bigfs=54, smfs=28, fill=False):
    b = 24; hw, hh = w // 2 - b, h // 2 - b
    path = f"m 0 0 l {2*hw} 0 {2*hw} {2*hh} 0 {2*hh}"
    f = f"\\an5\\pos({cx},{cy})\\fad(0,160)"
    s0, s1 = ts(t0), ts(t1)
    ev.append(f"Dialogue: 3,{s0},{s1},Ov,,0,0,0,,{{{f}\\p1\\bord{b}\\1c{TEAL}\\3c{TEAL}{pop()}}}{path}")
    if not fill:
        ev.append(f"Dialogue: 4,{s0},{s1},Ov,,0,0,0,,{{{f}\\p1\\bord{b - 5}\\1c{NAVY}\\3c{NAVY}{pop()}}}{path}")
    col = WHITE if not fill else NAVY
    ev.append(f"Dialogue: 5,{s0},{s1},Ov,,0,0,0,,{{\\an5\\pos({cx},{cy - (14 if small else 0)})\\fad(0,160)\\fs{bigfs}\\b1\\1c{col}{pop()}}}{big}")
    if small:
        ev.append(f"Dialogue: 5,{s0},{s1},Ov,,0,0,0,,{{\\an5\\pos({cx},{cy + 30})\\fad(0,160)\\fs{smfs}\\b1\\fsp3\\1c{TEAL}{pop()}}}{small}")

SFX = []   # masa bunyi pop
def card(t0, t1, *a, **k): pill(t0, t1, *a, **k); SFX.append(t0)

# "8 jam sehari online"
card(2.30, 4.15, 540, 250, 380, 130, "8 JAM", "ONLINE SEHARI", 62)
# 24 - 8 = 16
card(9.90, 14.75, 235, 250, 300, 130, "24 JAM", "SEHARI", 50)
card(11.16, 14.75, 540, 250, 300, 130, "– 8 JAM", "TOLAK", 50)
card(13.48, 14.75, 845, 250, 300, 130, "= 16 JAM", "BAKI", 50)
# 8 jam skrin
card(15.26, 20.60, 540, 250, 520, 130, "8 JAM", "DI DEPAN SKRIN", 62)
# 20-20-20
a = 33.92; z = 41.00
ev.append(f"Dialogue: 5,{ts(a)},{ts(z)},Ov,,0,0,0,,{{\\an5\\pos(540,215)\\fad(0,200)\\fs150\\b1\\1c{TEAL}\\3c{NAVY}\\bord7\\blur1.5\\fscx0\\fscy0\\t(0,200,\\fscx132\\fscy132)\\t(200,340,\\fscx100\\fscy100)}}20-20-20")
SFX.append(a)
card(36.26, z, 195, 395, 320, 120, "20 MINIT", "SETIAP", 46, 26)
card(38.36, z, 540, 395, 320, 120, "20 KAKI", "TENGOK JAUH", 46, 26)
card(39.62, z, 885, 395, 320, 120, "20 SAAT", "TEMPOH", 46, 26)

# ---------- kad penutup beranimasi ----------
e = lambda t: ts(T0 + t)
ev.append(f"Dialogue: 5,{e(.9)},{ts(TOT)},Ov,,0,0,0,,{{\\an5\\pos(540,1300)\\fad(250,0)\\move(540,1325,540,1300,0,300)\\fs46\\b1\\fsp2\\1c{WHITE}\\3c{NAVY}\\bord4}}Jaga mata dari sekarang")
# CTA pill berdenyut
pulse = "".join(f"\\t({1200 + 900 * k},{1650 + 900 * k},\\fscx106\\fscy106)\\t({1650 + 900 * k},{2100 + 900 * k},\\fscx100\\fscy100)" for k in range(4))
w_, h_ = 800, 140; b = 24; hw, hh = w_ // 2 - b, h_ // 2 - b
ev.append(f"Dialogue: 3,{e(.7)},{ts(TOT)},Ov,,0,0,0,,{{\\an5\\pos(540,1430)\\p1\\bord{b}\\1c{TEAL}\\3c{TEAL}{pop(116)}{pulse}}}m 0 0 l {2*hw} 0 {2*hw} {2*hh} 0 {2*hh}")
ev.append(f"Dialogue: 5,{e(.7)},{ts(TOT)},Ov,,0,0,0,,{{\\an5\\pos(540,1430)\\fs46\\b1\\fsp1\\1c{NAVY}{pop(116)}{pulse}}}DAPATKAN DI TIKTOK SHOP")
SFX.append(T0 + .7)
# anak panah melantun
for k in range(6):
    t = 1.3 + k * .6
    ev.append(f"Dialogue: 5,{e(t)},{e(t + .6)},Ov,,0,0,0,,{{\\an5\\move(540,1522,540,1546)\\p1\\bord3\\1c{TEAL}\\3c{TEAL}}}m -22 -12 l 22 -12 0 14")
ev.append(f"Dialogue: 5,{e(1.5)},{ts(TOT)},Ov,,0,0,0,,{{\\an8\\fad(300,0)\\move(540,1640,540,1620,0,350)\\fs32\\b1\\1c{WHITE}\\3c{NAVY}\\bord3}}Ambil 1 tablet, 2 kali sehari, 30 minit sebelum makan,\\Nmengikut arahan pada label produk.")
ev.append(f"Dialogue: 5,{e(2.0)},{ts(TOT)},Ov,,0,0,0,,{{\\an8\\fad(300,0)\\fs25\\1c&HE6E6E6&\\3c{NAVY}\\bord3}}Gunakan mengikut arahan pada label produk. Jika mempunyai masalah\\Nmata atau sedang mengambil ubat lain, dapatkan nasihat profesional\\Nkesihatan sebelum menggunakannya.".replace("\\fs25", "\\pos(540,1760)\\fs25"))

hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter,68,&H00FFFFFF,&H00FFFFFF,&H66401E0A,&H00000000,1,0,0,0,100,100,0,0,3,18,0,2,70,70,600,1
Style: Tag,Inter,32,&H00FFFFFF,&H00FFFFFF,&H66401E0A,&H00000000,1,0,0,0,100,100,1,0,3,12,0,8,40,40,70,1
Style: Ov,Inter,50,&H00FFFFFF,&H00FFFFFF,&H00401E0A,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
open("work/eyecare.ass", "w").write(hdr + "\n".join(ev) + "\n")

# ---------- SFX ----------
def sh(*a): subprocess.run(list(a), check=True)
sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "aevalsrc=0.6*sin(2*PI*(700+5000*t)*t)*exp(-26*t):d=0.16:s=48000", "-ac", "2", "work/pop.wav")
sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anoisesrc=d=0.6:c=pink:a=0.5:r=48000", "-af",
   "bandpass=f=1800:w=1800,afade=t=in:d=0.3,afade=t=out:st=0.3:d=0.3,volume=0.6", "-ac", "2", "work/whoosh.wav")
SF = sorted(SFX)
pops = [t for t in SF if abs(t - (T0 + .7)) > .01]
# ---------- video ----------
Z = "if(lt(t,9.49),1,if(lt(t,18.31),1.06,if(lt(t,28.63),1,if(lt(t,35.87),1.06,1))))"
vf = (f"eq=saturation=0.88:contrast=1.06:brightness=0.02,colorbalance=rs=-0.04:bs=0.06:rm=-0.03:bm=0.05,"
      f"scale=w='trunc(1080*({Z})/2)*2':h='trunc(1920*({Z})/2)*2':eval=frame,"
      f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*0.95',fps=60,format=yuv420p")
sh("ffmpeg", "-y", "-v", "error", "-i", V, "-vf", vf, "-af", "highpass=f=80,afftdn=nr=10", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "work/eyecare_main.mp4")
# end card: latar kabur bergerak perlahan + kad slide-up
ease = "(1-pow(1-min(t/0.75,1),3))"
fc = ("[0:v]scale=w='trunc(1080*(1.18+0.025*t)/2)*2':h='trunc(1920*(1.18+0.025*t)/2)*2':eval=frame,crop=1080:1920,boxblur=40:6,eq=brightness=-0.10[bg0];"
      "[0:v]scale=1080:-2[fg];"
      f"[bg0][fg]overlay=x=0:y='150+(1-{ease})*900'[v1];[v1]fade=t=in:d=0.25,fps=60,format=yuv420p[v]")
sh("ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", str(END), "-i", "assets/eyecare/ingredients_card.jpg", "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "16", "work/eyecare_end.mp4")
# ---------- gabung + overlay + audio ----------
ins = ["-i", "work/eyecare_main.mp4", "-i", "work/eyecare_end.mp4", "-i", "work/pop.wav", "-i", "work/whoosh.wav"]
n = len(pops)
fa = ["[0:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur=%.2f[va]" % TOT]
fa.append(f"[2:a]asplit={n}" + "".join(f"[p{i}]" for i in range(n)))
mix = ["[va]"]
for i, t in enumerate(pops):
    fa.append(f"[p{i}]adelay={int(t * 1000)}|{int(t * 1000)}[d{i}]"); mix.append(f"[d{i}]")
fa.append(f"[3:a]adelay={int(T0 * 1000)}|{int(T0 * 1000)}[wh]"); mix.append("[wh]")
fa.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,volume=0.2dB,alimiter=limit=0.89[a]")
fcx = ";".join(["[0:v][1:v]concat=n=2:v=1:a=0[c];[c]ass=work/eyecare.ass[v]"] + fa)
sh("ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", fcx, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
   "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "output/eyecare_final.mp4")
print("siap", TOT)
