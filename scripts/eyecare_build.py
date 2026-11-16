#!/usr/bin/env python3
"""DS Pharma Eye Care — bina video akhir (zoom, popup, subtitle karaoke, teks overlay, SFX).
Prasyarat: work/cut.mp4 (eyecare_cut.py) + work/cut_words.json (transkrip whisper pada cut.mp4).
Guna: python3 scripts/eyecare_build.py [--test]   (--test = render pantas resolusi rendah)
Semua masa dalam saat pada timeline cut.mp4.
"""
import json, os, subprocess, sys, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
W, H, FPS = 1080, 1920, 30
UP = "/root/.claude/uploads/f6d0048b-b12b-5c1a-b5c6-9e624bc0aed8/"
IMG = {  # fail yang user bagi
    "goji": UP + "6d95529d-image.webp", "avokado": UP + "46ef0f02-image.webp",
    "lobak": UP + "135e8fcb-image.webp", "eyebright": UP + "e1884fb7-image.jpg",
    "hologram": UP + "c348fa3c-image.jpg", "poster": UP + "15d75b0c-image.jpg",
    "pack": UP + "229d533d-image.jpg", "screen": UP + "de747c66-image.jpg",
}
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
PURPLE, TEAL, RED, YELLOW = "&H912D5A&", "&HB6C42E&", "&H4A33E8&", "&H00C4FF&"  # BGR ASS
TEST = "--test" in sys.argv

words = json.load(open("work/cut_words.json"))
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "work/cut.mp4"]))

# ---------- 1. betulkan perkataan (salah dengar whisper) ----------
fix = {"diwina": "digunakan"}
W2 = []
for s, e, w in words:
    w = fix.get(w, w)
    if w.startswith("-") and W2:               # "Hati" + "-hati" -> "Hati-hati"
        ps, pe, pw = W2[-1]; W2[-1] = (ps, e, pw + w); continue
    W2.append((s, e, w))
words = W2

# ---------- 2. kumpul kepada kapsyen ----------
groups, cur = [], []
for s, e, w in words:
    if cur and (len(cur) >= 3 or cur[-1][2][-1] in ".,?!" or s - cur[-1][1] > 0.35
                or len(" ".join(x[2] for x in cur + [(s, e, w)])) > 20):
        groups.append(cur); cur = []
    cur.append((s, e, w))
if cur: groups.append(cur)

def t(x):
    x = max(0, x); h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"
def srt_t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"

# SRT (kapsyen kumpulan, ejaan betul)
with open("subs/eyecare.srt" if os.path.isdir("subs") else "work/eyecare.srt", "w") as f:
    for i, g in enumerate(groups, 1):
        f.write(f"{i}\n{srt_t(g[0][0])} --> {srt_t(g[-1][1])}\n{' '.join(x[2] for x in g)}\n\n")

# ---------- 3. ASS ----------
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter ExtraBold,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,8,3,5,40,40,0,1
Style: Chip,Inter ExtraBold,64,&H00FFFFFF,&H00FFFFFF,{PURPLE},&H80000000,0,0,0,0,100,100,0,0,3,20,0,5,40,40,0,1
Style: Big,Inter ExtraBold,230,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,10,5,5,40,40,0,1
Style: Draw,Inter ExtraBold,40,{YELLOW},{YELLOW},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"""]
def ev(s, e, style, text, layer=0):
    ass.append(f"Dialogue: {layer},{t(s)},{t(e)},{style},,0,0,0,,{text}")

# 3a. subtitle karaoke (perkataan semasa kuning + sedikit membesar)
SUBPOS = r"{\an5\pos(540,1120)}"
for g in groups:
    for i, (s, e, w) in enumerate(g):
        end = g[i + 1][0] if i + 1 < len(g) else e + 0.10
        txt = " ".join((r"{\1c&H00D7FF&\fscx110\fscy110}" + x[2] + r"{\r}") if j == i else x[2] for j, x in enumerate(g))
        ev(s, end, "Sub", SUBPOS + txt, 1)

POP = r"\fscx45\fscy45\t(0,170,\fscx112\fscy112)\t(170,300,\fscx100\fscy100)"
def chip(s, e, text, pos, color=PURPLE, an=5, size=None, slide=None, shake=False, tcolor=None):
    tags = rf"\an{an}\3c{color}"
    if size: tags += rf"\fs{size}"
    if tcolor: tags += rf"\1c{tcolor}"
    if slide:   # slide masuk dari tepi
        x0, y0 = slide; tags += rf"\move({x0},{y0},{pos[0]},{pos[1]},0,220)"
    else:
        tags += rf"\pos({pos[0]},{pos[1]})" + POP
    tags += rf"\fad(0,120)"
    if shake:
        for k in range(0, 600, 100):
            tags += rf"\t({k},{k+50},\frz{2 if k%200==0 else -2})\t({k+50},{k+100},\frz0)"
    ev(s, e, "Chip", "{" + tags + "}" + text, 2)

TOPY, BOTY = 150, 1640
# hook
chip(0.0, 3.72, "SIANG = LAPTOP", (60, 150), PURPLE, an=4, slide=(-700, 150))
chip(2.10, 3.72, "MALAM = TIKTOK", (60, 270), TEAL, an=4, slide=(1300, 270))
chip(3.78, 4.95, "HATI-HATI!", (540, 270), RED, size=120, shake=True)
# statistik kelip mata
chip(6.28, 12.95, "KELIP MATA / MINIT", (540, 120), PURPLE, size=56)
ev(7.74, 10.30, "Big", r"{\an5\pos(540,330)\fad(0,120)\1c&H00FFFFFF&" + POP + r"}18x", 2)
ev(10.42, 12.95, "Big", r"{\an5\pos(540,330)\fad(0,120)\1c&H4A33E8&\fs250" + POP + r"\t(300,800,\frz3)\t(800,1300,\frz-3)\t(1300,1800,\frz0)}3–4x", 2)
# mata kering / pedih / kabur
chip(14.48, 16.95, "MATA KERING", (60, 150), RED, an=4, slide=(-700, 150))
chip(15.52, 16.95, "PEDIH", (60, 270), RED, an=4, slide=(-700, 270))
chip(16.14, 16.95, "KABUR", (60, 390), RED, an=4, slide=(-700, 390))
# rehat + jaga dalam
chip(17.18, 18.60, "REHATKAN MATA", (540, 200), TEAL)
chip(18.64, 21.10, "JAGA DARI DALAM", (540, 200), PURPLE, size=72)
# produk
chip(24.02, 26.30, "TABLET KUNYAH", (540, BOTY), TEAL)
chip(26.30, 28.78, "SECARA TRADISIONAL", (540, BOTY), PURPLE, size=58)
chip(28.78, 31.40, "1 TABLET = 4 BAHAN", (540, BOTY), YELLOW, tcolor="&H00000000&")
# golongan sasaran (satu slot, bertukar)
for s, e, txt, c in [(37.12, 38.00, "ORANG OFIS", PURPLE), (38.00, 38.72, "STUDENT", TEAL),
                     (38.72, 39.54, "KAKI SCROLL", PURPLE), (39.54, 41.60, "SCREEN TIME TINGGI", RED)]:
    chip(s, e, txt, (540, BOTY), c)
# MAL + KKM
chip(41.96, 43.30, "MAL22076147T", (540, 220), TEAL, size=84)
chip(43.36, 45.30, "HOLOGRAM KKM", (540, BOTY), PURPLE)
chip(45.30, 46.60, "BOLEH SEMAK SENDIRI", (540, BOTY), TEAL, size=58)
# harga + free shipping
chip(47.40, 49.40, "HARGA SANGAT MURAH!", (540, 220), YELLOW, size=70, tcolor="&H00000000&", shake=True)
chip(50.72, 53.50, "FREE SHIPPING", (540, 230), TEAL, size=96, shake=True)
chip(52.96, 53.65, "SEKARANG!", (540, BOTY), RED)
# CTA beg kuning
chip(53.68, DUR, "TEKAN BEG KUNING", (540, BOTY + 60), YELLOW, size=84, tcolor="&H00000000&")
chip(54.66, DUR, r"JAGA MATA\NSEBELUM TERLAMBAT", (540, 220), PURPLE, size=70)
# anak panah kuning melantun (lukisan vektor)
arrow = r"m 0 0 l 150 0 l 75 90"
for k in range(3):   # 3 pengulangan lantunan
    ss = 53.68 + k * 0.95
    ev(ss, min(ss + 0.95, DUR), "Draw", r"{\an7\fad(80,0)\move(465,1480,465,1535,0,450)\move(465,1535,465,1480,450,900)\p1\3c&H00000000&\bord4}" + arrow + r"{\p0}", 3)
open("work/eyecare.ass", "w").write("\n".join(ass) + "\n")

# ---------- 4. kad popup ----------
def cover(im, w, h, box=None):
    if box: im = im.crop(box)
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
    l, tp = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, tp, l + w, tp + h))

def make_card(key, name, size=(380, 380), label=None, sub=None, box=None):
    iw, ih = size; b = 12; pill_h = 70 if label else 0; m = 34
    im = Image.open(IMG[key]).convert("RGB")
    im = cover(im, iw, ih, box)
    cw, ch = iw + 2 * b, ih + 2 * b
    canvas = Image.new("RGBA", (cw + 2 * m, ch + pill_h // 2 + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 10, m + cw, m + ch + 10), 40, fill=(0, 0, 0, 150))
    canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((m, m, m + cw, m + ch), 38, fill=(255, 255, 255, 255))
    mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, iw, ih), 28, fill=255)
    canvas.paste(im, (m + b, m + b), mask)
    if label:
        f1 = ImageFont.truetype(FONT, 38); f2 = ImageFont.truetype(FONT, 30)
        tw = d.textlength(label, font=f1) + (d.textlength("  " + sub, font=f2) if sub else 0)
        pw = int(tw + 60); px = m + (cw - pw) // 2; py = m + ch - pill_h // 2
        d.rounded_rectangle((px, py, px + pw, py + pill_h), pill_h // 2, fill=(90, 45, 145, 255), outline=(255, 255, 255, 255), width=5)
        d.text((px + 30, py + pill_h // 2), label, font=f1, fill=(255, 255, 255, 255), anchor="lm")
        if sub: d.text((px + 30 + d.textlength(label + "  ", font=f1), py + pill_h // 2 + 2), sub, font=f2, fill=(76, 224, 211, 255), anchor="lm")
    p = f"work/card_{name}.png"; canvas.save(p); return p, canvas.size

HOLO = (440, 880, 1100, 1190)   # kawasan pelekat hologram KKM pada foto
cards_spec = [  # key, nama, mula, tamat, tinggi_atas, saiz, label, sub, box
    ("pack",     "pack",   21.26, 28.78, 40, (380, 380), "DS PHARMA EYE CARE", None, None),
    ("poster",   "poster", 29.60, 31.40, 40, (380, 380), "4 BAHAN UTAMA", None, None),
    ("lobak",    "lobak",  31.44, 32.94, 40, (380, 380), "LOBAK MERAH", "60mg", None),
    ("goji",     "goji",   32.96, 34.04, 40, (380, 380), "BUAH GOJI", "50mg", None),
    ("avokado",  "avokado",34.06, 34.92, 40, (380, 380), "AVOKADO", "15mg", None),
    ("eyebright","eyebright",34.94, 36.30, 40, (380, 380), "BUNGA EYEBRIGHT", "40mg", None),
    ("screen",   "screen", 36.24, 41.70, 40, (380, 380), None, None, None),
    ("hologram", "holo",   43.36, 45.40, 70, (600, 300), "HOLOGRAM KKM", None, HOLO),
]
overlays = []  # (png, s, e, cx, cy, w, h)
for key, name, s, e, top, size, label, sub, box in cards_spec:
    p, (cw, ch) = make_card(key, name, size, label, sub, box)
    overlays.append((p, s, e, 540, top + ch / 2, cw, ch))

# ---------- 5. zoom ----------
FY = 700   # titik fokus (muka)
Z_EVENTS = [  # (mula, tamat, tambahan zoom, ramp masuk, ramp keluar)
    (-0.5, 1.75, 0.10, 0.1, 0.35), (3.78, 4.90, 0.16, 0.15, 0.30),
    (6.28, 10.30, 0.12, 3.0, 0.30), (9.98, 12.95, 0.20, 0.15, 0.40),
    (13.08, 16.90, 0.12, 2.0, 0.30), (18.64, 20.90, 0.14, 0.20, 0.40),
    (21.26, 23.50, 0.18, 0.18, 0.40), (24.00, 28.70, 0.08, 3.5, 0.40),
    (28.78, 31.40, 0.16, 0.15, 0.30),
    (31.44, 32.30, 0.08, 0.12, 0.40), (32.96, 33.80, 0.08, 0.12, 0.40),
    (34.06, 34.90, 0.08, 0.12, 0.40), (34.94, 35.90, 0.08, 0.12, 0.40),
    (37.12, 38.00, 0.08, 0.12, 0.40), (38.00, 38.70, 0.08, 0.12, 0.40),
    (38.72, 39.50, 0.08, 0.12, 0.40), (39.54, 41.00, 0.10, 0.12, 0.50),
    (41.82, 45.00, 0.20, 2.5, 0.40), (47.28, 49.00, 0.12, 0.15, 0.40),
    (50.72, 53.00, 0.16, 0.15, 0.40), (53.68, DUR + 1, 0.20, 2.5, 0.30),
]
def zexpr():
    terms = [f"{a}*(st(1,min(clip((t-{s})/{ri},0,1),clip(({e}-t)/{ro},0,1)))*0+ld(1)*ld(1)*(3-2*ld(1)))" for s, e, a, ri, ro in Z_EVENTS]
    return "(1+" + "+".join(terms) + ")"
Z = zexpr()

# ---------- 6. SFX ----------
def sh(*a): subprocess.run(a, check=True)
sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "aevalsrc='sin(2*PI*(420+2600*t)*t)*exp(-28*t)':d=0.18:s=44100", "-af", "volume=0.9", "work/pop.wav")
sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:r=44100:a=0.6", "-af", "bandpass=f=1400:w=1.2,afade=t=in:d=0.18,afade=t=out:st=0.18:d=0.27,volume=1.6", "work/whoosh.wav")
pops = sorted({round(o[1], 2) for o in overlays} | {c for c in [0.0, 2.10, 3.78, 7.74, 10.42, 14.48, 15.52, 16.14, 17.18, 18.64, 24.02, 28.78, 37.12, 38.0, 38.72, 39.54, 41.96, 45.30, 47.40, 50.72, 52.96, 53.68, 54.66]})
woosh = [3.78, 9.98, 21.26, 28.78, 47.28, 50.72, 41.82]
fc, labs = [], []
n = len(pops) + len(woosh)
fc.append(f"[1:a]asplit={len(pops)}" + "".join(f"[p{i}]" for i in range(len(pops))))
fc.append(f"[2:a]asplit={len(woosh)}" + "".join(f"[w{i}]" for i in range(len(woosh))))
mix = "[0:a]"
for i, s in enumerate(pops): fc.append(f"[p{i}]adelay={int(s*1000)}|{int(s*1000)},volume=0.22[q{i}]"); mix += f"[q{i}]"
for i, s in enumerate(woosh): fc.append(f"[w{i}]adelay={int(s*1000)}|{int(s*1000)},volume=0.30[x{i}]"); mix += f"[x{i}]"
fc.append(mix + f"amix=inputs={1+n}:normalize=0:duration=first,alimiter=limit=0.95[m]")
sh("ffmpeg", "-y", "-v", "error", "-i", "work/cut.mp4", "-i", "work/pop.wav", "-i", "work/whoosh.wav", "-filter_complex", ";".join(fc), "-map", "[m]", "-ar", "44100", "work/mix.wav")
# loudnorm 2-pas -> -14 LUFS
log = subprocess.run(["ffmpeg", "-i", "work/mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(log[log.rindex("{"):])
sh("ffmpeg", "-y", "-v", "error", "-i", "work/mix.wav", "-af",
   f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true",
   "-ar", "44100", "work/mix_norm.wav")

# ---------- 7. render video ----------
cmd = ["ffmpeg", "-y", "-v", "error", "-i", "work/cut.mp4"]
for p, s, e, *_ in overlays: cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{e - s + 0.2:.2f}", "-i", p]
f = [f"[0:v]scale=w='{W}*{Z}':h='{H}*{Z}':eval=frame:flags=bicubic,crop={W}:{H}:x='(iw-{W})/2':y='{FY}*({Z}-1)',setsar=1[b0]"]
for i, (p, s, e, cx, cy, cw, ch) in enumerate(overlays):
    u = f"(t-{s})"
    pin = f"(1+2.70158*pow(clip({u}/0.28,0,1)-1,3)+1.70158*pow(clip({u}/0.28,0,1)-1,2))"
    pout = f"clip(({e}-t)/0.15,0.02,1)"
    F = f"max(0.02,{pin}*{pout})"
    f.append(f"[{i+1}:v]format=rgba,setpts=PTS+{s}/TB,scale=w='max(2,trunc({cw}*{F}/2)*2)':h='max(2,trunc({ch}*{F}/2)*2)':eval=frame[c{i}]")
    f.append(f"[b{i}][c{i}]overlay=x='{cx}-w/2':y='{cy}-h/2':enable='between(t,{s},{e})'[b{i+1}]")
f.append(f"[b{len(overlays)}]ass=work/eyecare.ass[v]")
os.makedirs("output", exist_ok=True)
out = "output/eyecare_test.mp4" if TEST else "output/eyecare_final.mp4"
cmd += ["-i", "work/mix_norm.wav", "-filter_complex", ";".join(f), "-map", "[v]", "-map", f"{len(overlays)+1}:a",
        "-r", str(FPS), "-c:v", "libx264", "-crf", "30" if TEST else "18", "-preset", "ultrafast" if TEST else "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out]
sh(*cmd)
print(out)
