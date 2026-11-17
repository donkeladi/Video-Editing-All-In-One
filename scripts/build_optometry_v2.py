#!/usr/bin/env python3
"""Edit korporat optometri v2: subtitle sync (timestamp Whisper) + overlay sumber + grafik data animasi.
Guna: build_optometry_v2.py input.mov output.mp4 [--preview] [--stills]
Keperluan: work/words.json tidak wajib; masa isyarat (CUES) ditulis tangan berdasarkan transkrip."""
import os, subprocess, sys, shutil, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, S = 1080, 1920, 30, 2
NAVY, TEAL, WHITE, SLATE = (11, 37, 69), (25, 181, 196), (255, 255, 255), (60, 84, 118)
GOLD = (255, 200, 61)
F = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
T0, T1 = 0.70, 59.40
WORK = os.path.join(ROOT, "work"); OV = os.path.join(WORK, "ov2")
REF = os.path.join(ROOT, "assets", "ref")
shutil.rmtree(OV, ignore_errors=True); os.makedirs(OV)

# ---------- subtitle (masa asal video, saat) ----------
CUES = [
 (0.86, 2.30, "Korang ingat rabun tua ni"), (2.32, 4.60, "masalah orang 40 tahun ke atas je?"),
 (4.92, 7.55, "Pakar oftalmologi KPJ,"), (7.62, 10.45, "Dr Helen Tan, cakap dalam Berita Harian,"),
 (10.78, 13.15, "sekarang 10 hingga 12 peratus"), (13.20, 15.95, "orang umur 30-an dah boleh kena"),
 (16.00, 17.20, "presbiopia pramatang."), (17.43, 20.70, "Selalunya mula umur 36."),
 (21.15, 22.40, "Salah satu faktornya,"), (22.46, 23.28, "kerap guna gajet."),
 (23.32, 25.80, "Mayo Clinic pulak cakap,"), (25.88, 27.25, "tanda awal dia ialah"),
 (27.28, 29.30, "kena pegang bacaan jauh-jauh"), (29.80, 31.55, "baru nampak jelas."),
 (31.62, 33.50, "Kalau dah perasan tanda ni,"), (33.79, 35.20, "pergi check mata."),
 (36.34, 38.55, "Untuk penjagaan harian,"), (38.64, 41.25, "saya amalkan DS Pharma Eye Care."),
 (41.30, 43.90, "Tablet kunyah yang digunakan secara tradisional"), (44.34, 46.00, "untuk kesihatan mata."),
 (46.48, 48.00, "Jadi kalau nak dapatkan ni,"), (48.02, 48.95, "boleh pergi klik profile,"),
 (49.58, 50.55, "boleh pergi klik profile"), (50.58, 52.30, "dan tengok kalau ada"),
 (52.89, 54.20, "bakul kuning untuk produk ni."), (54.28, 55.20, "Jangan risau,"),
 (55.24, 57.85, "ada KKM dan juga hologram."), (57.95, 59.30, "Jumpa lagi, bye-bye!"),
]
tm = lambda t: t - T0
ts = lambda t: "%d:%02d:%05.2f" % (int(t // 3600), int(t % 3600 // 60), t % 60)
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter,50,&H00FFFFFF,&H00FFFFFF,&H0045250B,&H00452500,1,0,0,0,100,100,0,0,3,16,0,2,70,70,685,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
for a, b, c in CUES:
    ass += f"Dialogue: 0,{ts(tm(a))},{ts(tm(b))},Sub,,0,0,0,,{{\\fad(100,80)}}{c}\n"
open(os.path.join(WORK, "main_v2.ass"), "w").write(ass)

# ---------- helper lukisan (supersample S x) ----------
_fc = {}
def font(sz, wt="Bold"):
    k = (sz, wt)
    if k not in _fc: _fc[k] = ImageFont.truetype(F % wt, int(sz * S))
    return _fc[k]
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3
clamp = lambda x: max(0, min(1, x))
class P:
    def __init__(s, w, h):
        s.im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im, "RGBA")
    def sc(s, b): return [(v[0] * S, v[1] * S) if isinstance(v, tuple) else v * S for v in b]
    def rr(s, b, r, fill, outline=None, w=0): s.d.rounded_rectangle(s.sc(b), r * S, fill=fill, outline=outline, width=int(w * S))
    def el(s, b, fill=None, outline=None, w=0): s.d.ellipse(s.sc(b), fill=fill, outline=outline, width=int(w * S))
    def ln(s, pts, fill, w): s.d.line(s.sc(pts), fill=fill, width=int(w * S), joint="curve")
    def pg(s, pts, fill): s.d.polygon(s.sc(pts), fill=fill)
    def tx(s, xy, t, sz, fill=WHITE, wt="Bold", anchor="la"): s.d.text((xy[0] * S, xy[1] * S), t, font=font(sz, wt), fill=fill, anchor=anchor)
    def tw(s, t, sz, wt="Bold"): return font(sz, wt).getlength(t) / S

CW, CH = 960, 250
def base(p, accent=TEAL):
    p.rr((0, 20, CW, 240), 22, NAVY + (238,)); p.rr((0, 20, 12, 240), 6, accent + (255,))
def label(p, t, x=40, y=40): p.tx((x, y), t, 21, TEAL + (255,))
def check(p, cx, cy, r, a=255):
    p.el((cx - r, cy - r, cx + r, cy + r), fill=TEAL + (a,)); p.ln([(cx - r * .45, cy), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)], WHITE + (a,), r * .22)
def eye(p, cx, cy, w, col=WHITE):
    p.el((cx - w / 2, cy - w * .27, cx + w / 2, cy + w * .27), outline=col + (255,), w=4); p.el((cx - w * .15, cy - w * .15, cx + w * .15, cy + w * .15), fill=TEAL + (255,))
def phone(p, x, y, w, h, col=WHITE):
    col = col if len(col) == 4 else col + (255,)
    p.rr((x, y, x + w, y + h), 8, None, outline=col, w=4); p.ln([(x + w * .35, y + h - 9), (x + w * .65, y + h - 9)], col, 3)
def person(p, cx, cy, r, col):
    p.el((cx - r * .45, cy - r, cx + r * .45, cy - r * .1), fill=col); p.rr((cx - r * .8, cy + r * .05, cx + r * .8, cy + r), r * .4, col)
def basket(p, cx, cy, r, col=GOLD):
    col = col[:3]
    p.pg([(cx - r, cy - r * .2), (cx + r, cy - r * .2), (cx + r * .7, cy + r * .8), (cx - r * .7, cy + r * .8)], col + (255,))
    p.ln([(cx - r * .6, cy - r * .2), (cx - r * .3, cy - r * .9), (cx + r * .3, cy - r * .9), (cx + r * .6, cy - r * .2)], col + (255,), 5)
def circ_img(name, d):
    im = Image.open(os.path.join(REF, name + ".jpg")).convert("RGBA").resize((d * S, d * S), Image.LANCZOS)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse((0, 0, im.size[0] - 1, im.size[1] - 1), fill=255); im.putalpha(m); return im

# ---------- panel ----------
def panel_stat(p, t, d):
    base(p); label(p, "PAKAR KPJ · UMUR 30-AN")
    k = ease((t - 0.8) / 1.3); v = int(12 * k)
    txt = "10–12%" if k >= 1 else f"{v}%"
    p.tx((40, 78), txt, 92, WHITE); p.tx((40, 190), "berisiko presbiopia pramatang", 24, (190, 208, 230), "Medium")
    cols, rows, x0, y0, pitch = 20, 5, 400, 72, 27
    on = int(11 * k)
    for i in range(100):
        r_, c_ = divmod(i, cols); x = x0 + c_ * pitch; y = y0 + r_ * pitch
        lit = i < on; sc_ = 1.0 + (0.35 * clamp(1 - abs(i - on) / 2) if k < 1 else 0)
        rad = 8 * sc_
        p.el((x + 8 - rad, y + 8 - rad, x + 8 + rad, y + 8 + rad), fill=(TEAL if lit else SLATE) + (255,))
    p.tx((x0, y0 + 5 * pitch + 2), "100 orang umur 30-an", 19, (150, 175, 205), "Medium")
def panel_age(p, t, d):
    base(p); label(p, "SELALUNYA MULA PADA UMUR")
    x0, x1, y = 70, 890, 120
    p.rr((x0, y - 5, x1, y + 5), 5, SLATE + (255,))
    k = ease((t - 1.4) / 1.5); age = 30 + 6 * k; mx = x0 + (x1 - x0) * (age - 30) / 20
    p.rr((x0, y - 5, mx, y + 5), 5, TEAL + (255,))
    for a in (30, 35, 40, 45, 50):
        x = x0 + (x1 - x0) * (a - 30) / 20; p.ln([(x, y + 12), (x, y + 24)], (150, 175, 205, 255), 3); p.tx((x, y + 30), str(a), 22, (190, 208, 230), "Medium", "ma")
    p.el((mx - 17, y - 17, mx + 17, y + 17), fill=WHITE + (255,), outline=TEAL + (255,), w=6)
    bw = 150; bx = min(max(mx - bw / 2, 20), CW - bw - 20)
    p.rr((bx, 52, bx + bw, 94), 12, TEAL + (255,)); p.tx((bx + bw / 2, 73), f"{int(round(age))} tahun", 26, NAVY + (255,), "Bold", "mm")
    g = ease((t - 3.9) / 0.5)
    if g > 0:
        a = int(255 * g); off = (1 - g) * 14
        p.rr((220, 172 + off, 740, 222 + off), 25, (34, 64, 108, int(255 * g))); phone(p, 242, 180 + off, 22, 34, WHITE + (a,))
        p.tx((284, 197 + off), "Faktor: kerap guna gajet", 27, WHITE + (a,), "Bold", "lm")
def panel_mayo(p, t, d):
    base(p); label(p, "TANDA AWAL · MAYO CLINIC")
    eye(p, 90, 150, 90)
    k = ease((t - 3.9) / 1.6); dx = 210 + 390 * k           # dokumen dijauhkan
    blur = max(0.0, 7 * (1 - clamp((t - 5.2) / 1.6)))
    doc = P(CW, CH); doc.rr((dx, 100, dx + 110, 200), 8, WHITE + (255,))
    for i in range(5): doc.rr((dx + 14, 116 + i * 16, dx + 96 - (i % 2) * 20, 122 + i * 16), 3, (80, 100, 135, 255))
    di = doc.im.filter(ImageFilter.GaussianBlur(blur * S)) if blur > 0.2 else doc.im
    p.im.alpha_composite(di)
    ar = clamp((t - 3.7) / 0.5)
    if ar > 0:
        p.ln([(150, 150), (dx - 14, 150)], TEAL + (int(255 * ar),), 4)
        p.pg([(dx - 14, 138), (dx - 14, 162), (dx + 2, 150)], TEAL + (int(255 * ar),))
    t1 = "Bacaan kabur dekat" if t < 3.8 else ("Perlu dijauhkan…" if t < 6.0 else "Baru nampak jelas")
    col = (190, 208, 230) if t < 6.0 else TEAL
    p.tx((CW - 40, 215), t1, 25, col + (255,), "Bold", "rs")
    p.tx((CW - 40, 58), "Perlu pegang bacaan jauh-jauh", 28, WHITE + (255,), "Bold", "ra")
def panel_eyecheck(p, t, d):
    base(p); label(p, "LANGKAH SELANJUTNYA")
    eye(p, 100, 135, 110); k = ease((t - 0.9) / 0.6)
    if k > 0: check(p, 100, 135, 38 * k, int(255 * k))
    p.tx((200, 98), "Perasan tanda ini?", 44, WHITE + (255,)); p.tx((200, 154), "Dapatkan pemeriksaan mata.", 36, TEAL + (255,))
def panel_prod(p, t, d):
    base(p); label(p, "DS PHARMA")
    p.tx((40, 72), "Eye Care Chewable Tablet", 46, WHITE + (255,)); p.tx((40, 130), "650mg · 10 tablet kunyah", 32, TEAL + (255,))
    p.tx((40, 182), "Digunakan secara tradisional untuk kesihatan mata", 24, (190, 208, 230), "Medium"); p.tx((CW - 40, 52), "MAL22076147T", 22, (190, 208, 230), "Medium", "ra")
    p.tx((40, 214), "Ini ubat tradisional. Sila rujuk ahli farmasi / doktor sebelum mengambil produk ini.", 17, (150, 175, 205), "Medium")
ING = [("lobak", "Serbuk lobak merah", "60mg"), ("avokado", "Ekstrak avokado", "15mg"), ("goji", "Ekstrak goji", "50mg"), ("eyebright", "Ekstrak Eyebright", "40mg")]
def panel_ing(p, t, d):
    base(p); label(p, "KANDUNGAN SETIAP TABLET 650mg")
    for i, (k, nm, mg) in enumerate(ING):
        a = ease((t - 0.25 - 0.4 * i) / 0.45)
        if a <= 0: continue
        x = 30 + i * 230; off = (1 - a) * 26
        p.rr((x, 70 + off, x + 214, 218 + off), 16, (34, 64, 108, int(255 * a)))
        im = circ_img(k, 84); al = im.split()[3].point(lambda v: int(v * a)); im.putalpha(al)
        p.im.alpha_composite(im, (int((x + 12) * S), int((88 + off) * S)))
        p.tx((x + 106, 118 + off), mg, 31, TEAL + (int(255 * a),), "Bold", "lm")
        p.tx((x + 107, 190 + off), nm, 19, WHITE + (int(255 * a),), "Medium", "mm")
def panel_cta(p, t, d):
    base(p, GOLD); p.tx((40, 40), "CARA DAPATKAN", 21, GOLD + (255,))
    steps = [(1.3, "Klik profil", "profile"), (5.6, "Tekan bakul kuning", "basket"), (6.7, "Produk ni", "check")]
    xs = [170, 480, 790]
    for (st, nm, ic), x in zip(steps, xs):
        a = ease((t - st) / 0.45)
        if a <= 0: continue
        pulse = 1 + 0.06 * math.sin((t - st) * 6) if ic == "basket" else 1
        r = 40 * pulse
        p.el((x - r, 112 - r, x + r, 112 + r), fill=(34, 64, 108, int(255 * a)), outline=(GOLD if ic != "check" else TEAL) + (int(255 * a),), w=4)
        cc = (WHITE + (int(255 * a),))
        if ic == "profile": person(p, x, 112, 24, cc)
        elif ic == "basket": basket(p, x, 112, 26, GOLD)
        else: check(p, x, 112, 24, int(255 * a))
        p.tx((x, 186), nm, 27, cc, "Bold", "ma")
    for (a0, x0, x1) in ((2.0, 220, 430), (6.0, 530, 740)):
        pass
    for st, x0, x1 in ((5.0, 225, 425), (6.2, 535, 735)):
        a = ease((t - st) / 0.4)
        if a > 0:
            xe = x0 + (x1 - x0) * a; p.ln([(x0, 112), (xe, 112)], GOLD + (200,), 4);
            if a > .95: p.pg([(x1 - 6, 100), (x1 - 6, 124), (x1 + 12, 112)], GOLD + (200,))
def panel_kkm(p, t, d):
    base(p); label(p, "KEASLIAN PRODUK")
    im = Image.open(os.path.join(REF, "kkm.jpg")).convert("RGBA"); sw = 300; sh = int(sw * im.size[1] / im.size[0])
    im = im.resize((sw * S, sh * S), Image.LANCZOS); m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), 14 * S, fill=255); im.putalpha(m)
    a = ease(t / 0.5); im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    p.im.alpha_composite(im, (40 * S, int((148 - sh / 2) * S)))
    h = clamp((t - 1.7) / 0.4)
    if h > 0:
        pu = 1 + 0.08 * math.sin(t * 7); x = 40; y = 148 - sh / 2
        p.rr((x - 6, y - 6, x + sw * 0.34 * pu + 6, y + sh + 6), 16, None, outline=GOLD + (int(255 * h),), w=4)
    for i, (st, txt, sub) in enumerate([(0.9, "Berdaftar KKM", "MAL22076147T"), (1.8, "Hologram keselamatan KKM", "pada setiap pek")]):
        k = ease((t - st) / 0.45)
        if k <= 0: continue
        y = 70 + i * 80; check(p, 420, y + 28, 22, int(255 * k))
        p.tx((460, y + 12), txt, 32, WHITE + (int(255 * k),), "Bold", "lm"); p.tx((460, y + 46), sub, 22, (190, 208, 230, int(255 * k)), "Medium", "lm")

def chip(name, label_, title, sub, dur, start):
    def f(p, t, d):
        pass
    return None

PANELS = [  # nama, mula(asal), tamat(asal), fungsi
 ("stat", 10.78, 17.30, panel_stat), ("age", 17.43, 23.40, panel_age), ("mayo", 23.32, 31.65, panel_mayo),
 ("eyecheck", 31.62, 35.30, panel_eyecheck), ("prod", 36.34, 41.28, panel_prod), ("ing", 41.30, 46.30, panel_ing),
 ("cta", 46.48, 54.30, panel_cta), ("kkm", 54.28, 58.00, panel_kkm)]
STILLS = "--stills" in sys.argv
inputs, flt = [], []
for name, a, b, fn in PANELS:
    d = b - a; os.makedirs(os.path.join(OV, name))
    n = int(d * FPS) + 1
    for i in range(n):
        t = i / FPS
        p = P(CW, CH + 30); fn(p, t, d)
        env = min(1, t / 0.3, max(0, (d - t) / 0.3)); env = ease(env)
        im = p.im; al = im.split()[3].point(lambda v: int(v * env)); im.putalpha(al)
        off = int((1 - env) * 24 * S)
        out = Image.new("RGBA", im.size, (0, 0, 0, 0)); out.paste(im, (0, off))
        out.resize((CW, CH + 30), Image.LANCZOS).save(os.path.join(OV, name, "%04d.png" % i), compress_level=1)
    inputs.append((name, a))

# ---------- chip sumber ----------
def chip_png(name, label_, title, sub):
    p = P(520, 150); p.rr((0, 0, 500, 130), 18, NAVY + (232,)); p.rr((0, 0, 12, 130), 6, TEAL + (255,))
    p.tx((40, 18), label_, 22, TEAL + (255,)); p.tx((40, 48), title, 34, WHITE + (255,)); p.tx((40, 92), sub, 25, (190, 208, 230, 255), "Medium")
    p.im.resize((520, 150), Image.LANCZOS).save(os.path.join(OV, name + ".png"))
chip_png("bh", "SUMBER", "Berita Harian", "Pakar Oftalmologi KPJ · Mac 2024")
chip_png("mayo", "SUMBER", "Mayo Clinic", "Presbyopia: Symptoms & causes")
CHIPS = [("bh", 4.92, 11.0), ("mayo", 23.32, 31.6)]

cmd = ["ffmpeg", "-y", "-i", SRC]
for name, a in inputs: cmd += ["-framerate", str(FPS), "-i", os.path.join(OV, name, "%04d.png")]
for name, a, b in CHIPS: cmd += ["-loop", "1", "-i", os.path.join(OV, name + ".png")]
fg = [f"[0:v]trim={T0}:{T1},setpts=PTS-STARTPTS,eq=contrast=1.04:saturation=1.06,unsharp=5:5:0.4,"
      f"drawbox=x=0:y=0:w=iw:h=7:color=0x0B2545@0.35:t=fill,drawbox=x=0:y=0:w='iw*t/{T1 - T0:.2f}':h=7:color=0x19B5C4@1:t=fill[v0]"]
cur = "v0"; i = 1
for name, a in inputs:
    fg.append(f"[{i}:v]format=rgba,setpts=PTS+{tm(a):.3f}/TB[p{i}]")
    fg.append(f"[{cur}][p{i}]overlay=x=60:y={1250 - 20}:eof_action=pass:enable='gte(t,{tm(a):.3f})'[v{i}]"); cur = f"v{i}"; i += 1
for name, a, b in CHIPS:
    fg.append(f"[{i}:v]format=rgba,fade=t=in:st={tm(a):.2f}:d=0.3:alpha=1,fade=t=out:st={tm(b) - .3:.2f}:d=0.3:alpha=1[p{i}]")
    fg.append(f"[{cur}][p{i}]overlay=x=48:y=140:enable='between(t,{tm(a):.2f},{tm(b):.2f})'[v{i}]"); cur = f"v{i}"; i += 1
fg.append(f"[{cur}]subtitles={os.path.join(WORK, 'main_v2.ass')}:fontsdir=/usr/share/fonts/opentype/inter[vout]")
af = f"atrim={T0}:{T1},asetpts=PTS-STARTPTS,highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11"
cmd += ["-filter_complex", ";".join(fg), "-af", af, "-map", "[vout]", "-map", "0:a", "-t", f"{T1 - T0:.2f}",
        "-c:v", "libx264", "-crf", "26" if "--preview" in sys.argv else "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
print("siap", OUT)
