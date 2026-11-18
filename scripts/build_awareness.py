#!/usr/bin/env python3
"""Video awareness AMD / dark adaptation: overlay graf + fakta + sumber (zon atas, tak lindung muka).

Guna: python3 scripts/build_awareness.py <video.mov> [out.mp4]
Masa overlay (TIMING) dianggar dari jeda senyap + skrip -> laraskan jika ada transkrip tepat.
Fakta dalam kad hanya yang disahkan (lihat FAKTA di bawah).
"""
import subprocess as sp, sys, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "output/amd_dark_adaptation.mp4"
WORK = "work/awareness"; os.makedirs(WORK, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
SHOT = os.environ.get("CARDIFF_SHOT", "assets/ref/cardiff_research.png")

def F(w, s): return ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", s)
NAVY = (14, 22, 42); TEAL = (0, 214, 190); AMBER = (255, 184, 48); RED = (255, 99, 99)
WHITE = (255, 255, 255); MUTE = (170, 184, 208); GRID = (60, 76, 108)
CX0, CX1, CY0, CY1 = 50, 1030, 150, 535   # kad: zon langsir di atas kepala
CW, CH = CX1 - CX0, CY1 - CY0
SS = 2  # supersample

def canvas(w=CW, h=CH, pad=40):
    """RGBA besar (SS x) + bayang. Pulangkan (img, draw, scale) ; lukis dalam koordinat 1x via S()."""
    im = Image.new("RGBA", ((w + pad * 2) * SS, (h + pad * 2) * SS), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad * SS, (pad + 8) * SS, (pad + w) * SS, (pad + h + 8) * SS), 34 * SS, fill=(0, 0, 0, 120))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14 * SS)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad * SS, pad * SS, (pad + w) * SS, (pad + h) * SS), 34 * SS, fill=NAVY + (238,), outline=(255, 255, 255, 40), width=2 * SS)
    d.rounded_rectangle((pad * SS, pad * SS, (pad + w) * SS, (pad + 10) * SS), 5 * SS, fill=TEAL + (255,))
    return im, d, pad

def finish(im): return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)

class P:  # pembantu lukis 1x -> SS x
    def __init__(s, d, pad): s.d, s.pad = d, pad
    def pt(s, x, y): return ((s.pad + x) * SS, (s.pad + y) * SS)
    def text(s, x, y, t, size, col=WHITE, w="Bold", anchor="la"):
        s.d.text(s.pt(x, y), t, font=F(w, size * SS), fill=col, anchor=anchor)
    def rect(s, x0, y0, x1, y1, col, r=10):
        s.d.rounded_rectangle((*s.pt(x0, y0), *s.pt(x1, y1)), r * SS, fill=col)
    def line(s, pts, col, wd=5):
        s.d.line([s.pt(*p) for p in pts], fill=col, width=wd * SS, joint="curve")
    def ell(s, x, y, r, col): s.d.ellipse((*s.pt(x - r, y - r), *s.pt(x + r, y + r)), fill=col)
    def chip(s, x, y, t, size=26, fill=TEAL, fg=NAVY, padx=20, h=None):
        f = F("Bold", size * SS); tw = f.getlength(t) / SS; h = h or size * 1.9
        s.rect(x, y, x + tw + padx * 2, y + h, fill, r=h / 2)
        s.d.text(s.pt(x + padx, y + h / 2), t, font=f, fill=fg, anchor="lm"); return x + tw + padx * 2


PADX = 44                      # jidar kiri/kanan kad
CHT = 390                      # tinggi kad standard
def tw(t, size, w="Bold"): return F(w, size * SS).getlength(t) / SS
def fit(p, x, y, t, size, maxw, col=WHITE, w="Bold", anchor="la", minsize=18):
    """Teks yang mengecil sendiri supaya muat dalam maxw (tak boleh terkeluar kad)."""
    while tw(t, size, w) > maxw and size > minsize: size -= 1
    assert tw(t, size, w) <= maxw + 1, f"teks terlalu panjang: {t!r}"
    p.text(x, y, t, size, col, w, anchor); return size
def chip2(p, x, y, t, size=24, fill=TEAL, fg=NAVY, h=44, padx=20):
    wd = tw(t, size) + padx * 2
    assert x + wd <= CW - PADX + 1, f"chip keluar kad: {t!r}"
    p.rect(x, y, x + wd, y + h, fill, r=h / 2)
    p.d.text(p.pt(x + padx, y + h / 2), t, font=F("Bold", size * SS), fill=fg, anchor="lm"); return x + wd
def header(p, tag, title, sub=None):
    chip2(p, PADX, 28, tag, 21, TEAL, NAVY, 38, 18)
    fit(p, PADX, 78, title, 46, CW - PADX * 2, WHITE, "ExtraBold")
    if sub: fit(p, PADX, 138, sub, 27, CW - PADX * 2, MUTE, "Medium")
def source(p, t, h=CHT): fit(p, CW - PADX, h - 20, t, 21, CW - PADX * 2, MUTE, "Medium", "rb")

# ---------- graf: lengkung dark adaptation (ilustrasi konsep) ----------
def da_curve(t, t0, tau):
    cone = 1 + 2 * (1 - math.exp(-t / 2.0))
    rod = 0.5 + 5.5 * (1 - math.exp(-(t - t0) / tau)) if t > t0 else 0.5
    return max(cone, rod)

def card_curve(both):
    im, d, pad = canvas(CW, CHT); p = P(d, pad)
    header(p, "SAINS MATA", "Mata sedang adjust ke gelap")
    # legenda (satu baris, tak bertindih graf)
    p.ell(PADX + 9, 150, 9, TEAL); fit(p, PADX + 26, 150, "Biasa", 24, 120, WHITE, "SemiBold", "lm")
    if both:
        p.ell(PADX + 170, 150, 9, AMBER); fit(p, PADX + 187, 150, "Lebih berumur: lebih lambat", 24, 500, WHITE, "SemiBold", "lm")
    gx0, gy0, gx1, gy1 = 96, 190, CW - PADX - 10, 296
    for i in range(4):
        y = gy0 + (gy1 - gy0) * i / 3; p.line([(gx0, y), (gx1, y)], GRID, 1)
    p.line([(gx0, gy0 - 6), (gx0, gy1), (gx1, gy1)], MUTE, 2)
    p.text(PADX - 4, (gy0 + gy1) / 2, "Pulih", 20, MUTE, "Medium", "lm")
    for m in (0, 10, 20, 30):
        x = gx0 + (gx1 - gx0) * m / 30
        p.text(x, gy1 + 10, f"{m} min" if m else "0", 21, MUTE, "Medium", "ma" if m < 30 else "ra")
    def pts(t0, tau):
        return [(gx0 + (gx1 - gx0) * t / 30, gy1 - (gy1 - gy0 - 8) * (da_curve(t, t0, tau) - 0.5) / 5.6) for t in [i * 0.25 for i in range(121)]]
    if both: p.line(pts(5, 14), AMBER, 6)
    p.line(pts(2.5, 5.5), TEAL, 6)
    source(p, "Ilustrasi konsep  •  rujukan: Cardiff University")
    return finish(im)

# ---------- hook ----------
def card_hook():
    im, d, pad = canvas(CW, 310); p = P(d, pad)
    chip2(p, PADX, 28, "PERNAH ALAMI?", 21, AMBER, NAVY, 38, 18)
    fit(p, PADX, 86, "Duduk bawah lampu terang,", 52, CW - PADX * 2, WHITE, "ExtraBold")
    fit(p, PADX, 154, "pandangan jadi gelap?", 52, CW - PADX * 2, TEAL, "ExtraBold")
    fit(p, PADX, 232, "Mata mungkin sedang beritahu sesuatu.", 29, CW - PADX * 2, MUTE, "Medium")
    return finish(im)

# ---------- berdiri tiba-tiba ----------
def card_bp():
    im, d, pad = canvas(CW, CHT); p = P(d, pad)
    header(p, "PUNCA 2", "Gelap bila bangun berdiri", "Aliran darah ke kepala turun sekejap")
    base = 322; bw = 240; gap = (CW - PADX * 2 - bw * 3) / 2
    for i, (lab, col, hh) in enumerate([("Duduk", TEAL, 120), ("Berdiri", AMBER, 55), ("Beberapa saat", TEAL, 115)]):
        x = PADX + i * (bw + gap); p.rect(x, base - hh, x + bw, base, col, 14)
        p.text(x + bw / 2, base + 12, lab, 24, WHITE, "SemiBold", "ma")
    return finish(im)
def card_bp_note():
    im, d, pad = canvas(CW, 130); p = P(d, pad)
    fit(p, CW / 2, 68, "Biasanya tak membimbangkan", 44, CW - PADX * 2, WHITE, "ExtraBold", "mm")
    return finish(im)

# ---------- 40+ ----------
def card_40():
    im, d, pad = canvas(CW, 300); p = P(d, pad)
    fit(p, 200, 150, "40+", 170, 300, TEAL, "Black", "mm")
    for i, t in enumerate(["Untuk yang berumur", "40 tahun ke atas,", "ada satu benda", "yang perlu tahu."]):
        fit(p, 410, 56 + i * 56, t, 42, CW - 410 - PADX, WHITE, "ExtraBold")
    return finish(im)

# ---------- Owsley: 2x ----------
def card_owsley():
    im, d, pad = canvas(CW, CHT); p = P(d, pad)
    header(p, "KAJIAN", "Adjust ke gelap lambat = ±2× risiko AMD", "Dewasa 60+ dengan makula normal, dipantau 3 tahun")
    base = 292; bw = 250
    for lab, val, col, x in [("Adjust normal", 1, TEAL, 190), ("Adjust terlalu lambat", 2, AMBER, 540)]:
        hh = 56 * val; p.rect(x, base - hh, x + bw, base, col, 14)
        p.text(x + bw / 2, base - hh / 2, "1×" if val == 1 else "±2×", 48, NAVY, "Black", "mm")
        p.text(x + bw / 2, base + 10, lab, 23, WHITE, "SemiBold", "ma")
    source(p, "Owsley et al., Ophthalmology 2016  •  Research to Prevent Blindness")
    return finish(im)

# ---------- makula ----------
def card_macula():
    im, d, pad = canvas(CW, CHT); p = P(d, pad)
    header(p, "APA ITU AMD?", "Penyakit di bahagian tengah retina", "Bahagian itu dinamakan makula")
    cx, cy, R = 170, 250, 56
    p.ell(cx, cy, R + 24, (235, 240, 250)); p.ell(cx, cy, R + 4, (150, 30, 40)); p.ell(cx, cy, R - 12, (225, 90, 70))
    p.ell(cx + 5, cy, 20, AMBER); p.ell(cx + 5, cy, 9, (255, 235, 170))
    p.text(cx, cy + R + 34, "Makula", 25, AMBER, "ExtraBold", "ma")
    fit(p, 380, 186, "Beri penglihatan tajam untuk:", 26, CW - 380 - PADX, MUTE, "Medium")
    for i, t in enumerate(["Membaca", "Memandu", "Kenal muka"]):
        chip2(p, 380, 226 + i * 54, t, 28, TEAL if i % 2 == 0 else AMBER, NAVY, 46, 24)
    return finish(im)

# ---------- 196 -> 288 juta ----------
def card_global():
    im, d, pad = canvas(CW, CHT); p = P(d, pad)
    header(p, "TIADA TANDA AWAL", "AMD sering senyap pada peringkat awal", "Anggaran pesakit AMD di seluruh dunia")
    base = 292; bw = 250
    for lab, val, col, x in [("2020", 196, TEAL, 190), ("2040 (unjuran)", 288, AMBER, 540)]:
        hh = val / 288 * 95; p.rect(x, base - hh, x + bw, base, col, 14)
        p.text(x + bw / 2, base - hh / 2, f"{val} juta", 40, NAVY, "Black", "mm")
        p.text(x + bw / 2, base + 10, lab, 23, WHITE, "SemiBold", "ma")
    source(p, "Wong et al., Lancet Global Health 2014")
    return finish(im)

# ---------- CTA ----------
def card_cta():
    im, d, pad = canvas(CW, 260); p = P(d, pad)
    chip2(p, PADX, 28, "NASIHAT", 21, RED, WHITE, 38, 18)
    fit(p, PADX, 86, "Kerap berlaku?", 58, CW - PADX * 2, WHITE, "ExtraBold")
    fit(p, PADX, 164, "Pergi buat pemeriksaan mata.", 46, CW - PADX * 2, TEAL, "ExtraBold")
    return finish(im)

# ---------- produk ----------
def card_product():
    im, d, pad = canvas(CW, 280); p = P(d, pad)
    chip2(p, PADX, 28, "SOKONGAN HARIAN", 21, TEAL, NAVY, 38, 18)
    fit(p, PADX, 84, "DS Pharma Eye Care", 60, CW - PADX * 2, WHITE, "ExtraBold")
    fit(p, PADX, 162, "Digunakan secara tradisional untuk kesihatan mata", 28, CW - PADX * 2, MUTE, "Medium")
    chip2(p, PADX, 208, "MAL22076147T", 25, AMBER, NAVY, 42, 20)
    return finish(im)
def card_disclaimer():
    im, d, pad = canvas(CW, 150); p = P(d, pad)
    fit(p, CW / 2, 80, "Bukan ganti pemeriksaan mata", 46, CW - PADX * 2, AMBER, "ExtraBold", "mm")
    return finish(im)

# ---------- sumber ----------
def card_sources():
    im, d, pad = canvas(CW, 400); p = P(d, pad)
    chip2(p, PADX, 28, "SUMBER RUJUKAN", 21, TEAL, NAVY, 38, 18)
    sh = Image.open(SHOT).convert("RGB")
    sh = sh.crop((0, 190, sh.width, 1230)); sw = 320; shh = int(sh.height * sw / sh.width)
    sh = sh.resize((sw * SS, shh * SS), Image.LANCZOS)
    m = Image.new("L", sh.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, sh.width, sh.height), 18 * SS, fill=255)
    im.paste(sh, ((pad + PADX) * SS, (pad + 84) * SS), m)
    x0 = PADX + sw + 36
    for i, (a, b) in enumerate([("Cardiff University", "School of Optometry & Vision Sciences"), ("Research to Prevent Blindness", "Dark adaptation & AMD"),
                                ("LiveScience", "Sains kesihatan mata"), ("AAO", "American Academy of Ophthalmology")]):
        y = 84 + i * 76; p.rect(x0, y, CW - PADX, y + 66, (34, 50, 84), 14); p.rect(x0, y, x0 + 8, y + 66, TEAL, 4)
        fit(p, x0 + 26, y + 8, a, 27, CW - PADX - x0 - 40, WHITE, "ExtraBold")
        fit(p, x0 + 26, y + 40, b, 19, CW - PADX - x0 - 40, MUTE, "Medium")
    return finish(im)

S = lambda n, im: (im.save(f"{WORK}/{n}.png"), f"{WORK}/{n}.png")[1]
# Masa dari transkrip faster-whisper (work/awareness_whisper.json)
TIMING = [
    ("hook",   card_hook(),      1.3,  7.4, 175),
    ("curveA", card_curve(False), 7.7, 16.9, 150),
    ("curveB", card_curve(True), 14.3, 16.9, 150),
    ("bp",     card_bp(),        17.2, 23.5, 150),
    ("bpnote", card_bp_note(),   23.9, 27.0, 565),
    ("h40",    card_40(),        27.2, 33.7, 175),
    ("owsley", card_owsley(),    34.0, 41.0, 150),
    ("macula", card_macula(),    41.8, 54.0, 150),
    ("global", card_global(),    54.2, 57.6, 150),
    ("cta",    card_cta(),       58.4, 63.4, 175),
    ("product", card_product(), 63.9, 72.4, 175),
    ("discl",  card_disclaimer(), 72.8, 79.0, 190),
    ("sources", card_sources(),  80.9, 87.3, 130),
]
# ---------- video utama: flip (betulkan tulisan terbalik) + zoom in/out smooth ----------
# (masa, zoom): antara dua titik berturutan = smoothstep. Pusat zoom dikunci pada atas kepala supaya kepala tak naik ke zon kad.
ZOOM = [(0,1.00),(1.3,1.00),(3.4,1.10),(7.2,1.10),(8.6,1.02),(12.0,1.02),(14.2,1.12),(16.9,1.12),(18.2,1.03),
        (22.0,1.03),(23.8,1.10),(27.0,1.10),(28.4,1.02),(32.0,1.02),(34.0,1.13),(40.8,1.13),(42.2,1.03),
        (47.0,1.03),(48.6,1.10),(54.0,1.10),(55.4,1.02),(58.0,1.02),(60.8,1.09),(63.4,1.09),(64.6,1.12),
        (72.2,1.12),(73.8,1.03),(79.5,1.03),(81.5,1.10),(86.0,1.10),(88.4,1.16)]
ZX, ZY = 540, 620
def zexpr():
    e = f"{ZOOM[-1][1]}"
    for (t0, z0), (t1, z1) in reversed(list(zip(ZOOM, ZOOM[1:]))):
        x = f"((t-{t0})/{t1-t0:.3f})"
        e = f"if(lt(t,{t1}),{z0}+({z1}-{z0})*{x}*{x}*(3-2*{x}),{e})"
    return e
inputs, fc, prev = [], [], "[0:v]"
fc.append(f"[0:v]hflip,crop=w='trunc(1080/({zexpr()})/2)*2':h='trunc(1920/({zexpr()})/2)*2':"
          f"x='{ZX}*(1-1/({zexpr()}))':y='{ZY}*(1-1/({zexpr()}))':exact=1,scale=1080:1920:flags=lanczos,setsar=1[base]")
prev = "[base]"
for k, (n, im, a, b, y0) in enumerate(TIMING, start=1):
    path = S(n, im); dur = b - a
    inputs += ["-loop", "1", "-framerate", "30", "-t", f"{dur:.2f}", "-i", path]
    fc.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=0.35:alpha=1,fade=t=out:st={dur-0.3:.2f}:d=0.3:alpha=1,setpts=PTS+{a}/TB[o{k}]")
    x = (W - im.width) // 2
    y = f"{y0 - 40}+40*pow(1-min(max((t-{a})/0.4,0),1),3)"
    fc.append(f"{prev}[o{k}]overlay=x={x}:y='{y}':eof_action=pass:enable='between(t,{a},{b})'[v{k}]")
    prev = f"[v{k}]"

# ---------- subtitle (teks dibetulkan ikut apa yang dituturkan) ----------
import json, wave, random
SUBS = [  # (mula, tamat, teks)
 (1.24,7.44,"Duduk bawah lampu lama, lepas tu pandangan jadi semakin gelap? Ada dua kemungkinan."),
 (7.62,13.94,"Pertama, mata tengah adjust. Lepas kena cahaya terang, mata perlukan beberapa minit untuk pulih semula."),
 (14.26,16.86,"Makin berumur, makin lambat."),
 (17.20,23.36,"Yang kedua, kalau gelap bila bangun berdiri, itu tekanan darah turun sekejap."),
 (23.84,27.02,"Biasanya tidak terlalu membimbangkan."),
 (27.02,33.66,"Tetapi, untuk korang yang dah berumur 40 tahun ke atas, ada satu benda yang kena tahu."),
 (33.96,40.88,"Penyelidik percaya mata yang terlalu lambat adjust ke gelap dikaitkan dengan risiko AMD."),
 (41.72,47.46,"AMD ni penyakit di bahagian tengah retina, namanya makula."),
 (47.90,54.08,"Bahagian ni yang bagi penglihatan tajam untuk baca, memandu dan kenal muka."),
 (54.08,57.58,"Selalunya tiada tanda amaran awal."),
 (58.30,63.44,"Sebab tu, kalau kerap berlaku, pergi check mata untuk sokongan harian."),
 (63.68,72.36,"Kita ada DS Pharma Eye Care, berdaftar dengan MAL, dan digunakan secara tradisional untuk kesihatan mata."),
 (72.74,80.92,"Bukan ganti rawatan mata, tapi ini adalah bantuan untuk melancarkan lagi penglihatan."),
 (80.92,85.44,"Jadi, kalau nak dapatkan ini, boleh tengok di profil atau bawah."),
 (86.36,87.44,"Sampai jumpa lagi."),
]
wh = json.load(open("work/awareness_whisper.json"))
def wtimes(a, b):
    ws = [w for sg in wh for w in sg["w"] if a - 0.05 <= w[1] <= b]
    return [w[1] for w in ws] or [a]
def ts(t, srt=False):
    h, m, sec = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",") if srt else f"{h}:{m:02d}:{sec:05.2f}"
cues = []
for a, b, txt in SUBS:
    words = txt.split(); n = len(words); st = wtimes(a, b); i = 0
    while i < n:
        j = min(n, i + 4)
        if n - j == 1: j = n
        t0 = st[min(len(st) - 1, int(i / n * len(st)))]
        t1 = st[min(len(st) - 1, int(j / n * len(st)))] if j < n else b
        cues.append((t0, max(t1, t0 + 0.4), " ".join(words[i:j]))); i = j
for k in range(len(cues) - 1):
    if cues[k][1] > cues[k + 1][0]: cues[k] = (cues[k][0], cues[k + 1][0], cues[k][2])
SRT = "work/awareness.srt"
open(SRT, "w").write("\n".join(f"{k+1}\n{ts(a,True)} --> {ts(b,True)}\n{t}\n" for k, (a, b, t) in enumerate(cues)))
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
       "[V4+ Styles]", "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
       "Style: D,Inter,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,70,70,330,1", "",
       "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
for a, b, t in cues: ass.append(f"Dialogue: 0,{ts(a)},{ts(b)},D,,0,0,0,,{t}")
open(f"{WORK}/sub.ass", "w").write("\n".join(ass))
fc.append(f"{prev}ass={WORK}/sub.ass[vs]"); prev = "[vs]"

# ---------- SFX (sintesis) pada setiap kad masuk ----------
SR = 44100; buf = [0.0] * int(SR * 88.5)
def add_sfx(t0, kind):
    random.seed(int(t0 * 100)); i0 = int(t0 * SR)
    if kind == "whoosh":
        n = int(SR * 0.38); lp = 0.0
        for i in range(n):
            x = i / n; env = (x / 0.25) if x < 0.25 else (1 - x) ** 1.6
            a = 0.04 + 0.5 * math.sin(math.pi * min(1, x * 1.1)) ** 2   # lowpass naik -> bunyi terbuka
            lp += a * (random.uniform(-1, 1) - lp)
            if i0 + i < len(buf): buf[i0 + i] += lp * env * 0.9
    elif kind == "pop":
        n = int(SR * 0.16)
        for i in range(n):
            x = i / n; f = 700 - 450 * x; buf_i = i0 + i
            if buf_i < len(buf): buf[buf_i] += math.sin(2 * math.pi * f * i / SR) * (1 - x) ** 3 * 0.6
for n_, im_, a_, b_, y_ in TIMING:
    if n_ in ("curveB",): add_sfx(a_, "pop")
    else: add_sfx(a_, "whoosh")
for t_ in (34.9, 55.0): add_sfx(t_, "pop")   # bar Owsley / graf global muncul
pk = max(abs(v) for v in buf) or 1
with wave.open(f"{WORK}/sfx.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes(b"".join(int(max(-1, min(1, v / pk * 0.9)) * 32767).to_bytes(2, "little", signed=True) for v in buf))
inputs += ["-i", f"{WORK}/sfx.wav"]; sfx_idx = len(TIMING) + 1
open(f"{WORK}/fc.txt", "w").write(";\n".join(fc + [f"[0:a]loudnorm=I=-15:TP=-2:LRA=9[va];[{sfx_idx}:a]volume=0.32[sf];[va][sf]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[aout]"]))
sp.run(["ffmpeg", "-y", "-i", SRC, *inputs, "-filter_complex_script", f"{WORK}/fc.txt", "-map", prev, "-map", "[aout]",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT], check=True)
print(OUT)
