#!/usr/bin/env python3
"""DS Pharma Eye Care — edutainment 9:16. Semua timecode diambil daripada transkrip sebenar
(work/raw_words.json). Jalankan:  python3 projects/eyecare/build_eyecare.py all
Mod: all | render i0 i1 out | audio | check
"""
import json, math, os, re, subprocess as sp, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
SRC = os.environ.get("EYECARE_SRC", "input/eyecare_raw.mov")
OUT = "output/eyecare_edutainment_9x16.mp4"
W, H, FPS = 1080, 1920, 30
DUR = 78.3
NF = int(DUR * FPS)
SR = 44100

# ---- warna jenama (sampel piksel gambar kotak) ----
PURPLE = (60, 39, 96)
DEEP = (36, 22, 64)
TEAL = (123, 203, 205)
WHITE = (255, 255, 255)
INK = (34, 20, 58)
SOFT = (226, 216, 246)
CARD = (26, 15, 52, 238)

# ---- jadual layout (masa sebenar) ----
T_SPLIT0, T_FULL1, T_END = 11.28, 55.50, 75.56
T_SKIP0 = 65.94  # tiada kapsyen/grafik pada dua ayat ini (lihat nota)
ZT = [T_SPLIT0, T_FULL1]
FLASH = [0.0, 28.40, 55.50, 75.56]  # <=4
PUNCH = [8.36, 57.50, 63.42]        # kata tekanan: bukan / keempat-empat / tradisional
FACE = (535, 750)

_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(f"assets/fonts/{name}.ttf", int(size))
    return _fc[k]
MX, MB, MS = "Montserrat-ExtraBold", "Montserrat-Bold", "Montserrat-SemiBold"
NM, NB = "NotoSans-Medium", "NotoSans-Bold"

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def out_back(x, c=1.1):
    x = clamp(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3

# ======================= ikon vektor (kod) =======================
SS, C = 3, 400
def _cv():
    im = Image.new("RGBA", (C * SS, C * SS), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def _s(p): return [(x * SS, y * SS) for x, y in p]
def lens(cx, cy, L, Wd, ang, n=28):
    pts = [((i / n - .5) * L, math.sin(math.pi * i / n) * Wd / 2) for i in range(n + 1)]
    pts += [((i / n - .5) * L, -math.sin(math.pi * i / n) * Wd / 2) for i in range(n, -1, -1)]
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]
def epoly(cx, cy, a, b, ang, n=60):
    c, s = math.cos(ang), math.sin(ang)
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n; x, y = a * math.cos(t), b * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out
def _fin(im, sz): return im.resize((sz, sz), Image.LANCZOS)

def icon_carrot(sz):
    im, d = _cv()
    for a in (-1.95, -1.57, -1.2):
        d.polygon(_s(lens(200 + 55 * math.cos(a), 112 + 55 * math.sin(a), 120, 40, a)), fill=(84, 176, 92))
    d.polygon(_s([(158, 128), (242, 128), (206, 372), (194, 372)]), fill=(244, 138, 40))
    d.ellipse(_s([(158, 108), (242, 148)]), fill=(244, 138, 40))
    d.polygon(_s([(176, 130), (196, 130), (199, 340), (196, 360)]), fill=(250, 164, 72))
    for y, w in ((180, 32), (232, 22), (284, 13)):
        d.line(_s([(200 - w, y), (200 - w + 20, y + 4)]), fill=(214, 100, 22), width=5 * SS)
    return _fin(im.rotate(32, resample=Image.BICUBIC, center=(C * SS / 2, C * SS / 2)), sz)

def icon_goji(sz):
    im, d = _cv()
    d.polygon(_s(lens(250, 120, 130, 46, -0.5)), fill=(84, 176, 92))
    for cx, cy, ang in ((150, 250, 0.6), (250, 255, -0.55), (200, 160, 1.4)):
        d.polygon(_s(epoly(cx, cy, 84, 52, ang)), fill=(214, 42, 54))
        d.polygon(_s(epoly(cx - 20, cy - 16, 30, 12, ang)), fill=(244, 110, 118))
        d.ellipse(_s([(cx - 9, cy - 9), (cx + 9, cy + 9)]), fill=(96, 150, 70))
    return _fin(im, sz)

def icon_avocado(sz):
    im, d = _cv()
    def pear(cx, k, fill):
        d.ellipse(_s([(cx - 118 * k, 237 - 118 * k + 0), (cx + 118 * k, 237 + 118 * k)]), fill=fill)
        d.ellipse(_s([(cx - 70 * k, 125 - 70 * k), (cx + 70 * k, 125 + 70 * k)]), fill=fill)
        d.polygon(_s([(cx - 70 * k, 125), (cx + 70 * k, 125), (cx + 116 * k, 225), (cx - 116 * k, 225)]), fill=fill)
    pear(200, 1.0, (46, 108, 56)); pear(200, 0.86, (198, 224, 112))
    d.ellipse(_s([(150, 205), (250, 305)]), fill=(142, 90, 54))
    d.ellipse(_s([(164, 218), (196, 244)]), fill=(184, 128, 88))
    return _fin(im, sz)

def icon_flower(sz):
    im, d = _cv()
    for a in (0.35, 2.8):
        d.polygon(_s(lens(200 + 110 * math.cos(a), 205 + 110 * math.sin(a), 130, 46, a)), fill=(84, 176, 92))
    for k in range(5):
        a = math.radians(k * 72 - 90)
        cx, cy = 200 + 72 * math.cos(a), 200 + 72 * math.sin(a)
        d.polygon(_s(lens(cx, cy, 150, 92, a)), fill=(250, 247, 255), outline=(196, 176, 232))
        d.line(_s([(200 + 28 * math.cos(a), 200 + 28 * math.sin(a)), (200 + 120 * math.cos(a), 200 + 120 * math.sin(a))]),
               fill=(150, 112, 206), width=4 * SS)
    d.ellipse(_s([(172, 172), (228, 228)]), fill=(255, 202, 62))
    d.ellipse(_s([(190, 190), (210, 210)]), fill=(222, 150, 20))
    return _fin(im, sz)

ICONS = {"lobak": icon_carrot, "goji": icon_goji, "avokado": icon_avocado, "bunga": icon_flower}

def badge(kind, d_, ring=TEAL):
    m = 10; im = Image.new("RGBA", (d_ + 2 * m, d_ + 2 * m), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.ellipse([m, m, m + d_, m + d_], fill=(26, 15, 52, 245), outline=ring, width=max(3, d_ // 38))
    ic = ICONS[kind](int(d_ * 0.72)); im.alpha_composite(ic, (m + (d_ - ic.width) // 2, m + (d_ - ic.height) // 2))
    return im

# ======================= binaan sprite =======================
def shadow_wrap(img, blur=14, off=8, alpha=95, margin=26):
    w, h = img.size
    big = Image.new("RGBA", (w + 2 * margin, h + 2 * margin), (0, 0, 0, 0))
    sh = Image.new("RGBA", big.size, (0, 0, 0, 0))
    sh.paste((10, 4, 24, alpha), (margin, margin + off), img.getchannel("A"))
    big.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    big.alpha_composite(img, (margin, margin))
    return big, margin

def rr(w, h, r, fill, ring=None, rw=3):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=fill, outline=ring, width=rw if ring else 0)
    return im

def tw(font, text): return font.getlength(text)
def put(d, x, cy, text, font, fill, anchor="l", stroke=0, sfill=None):
    """teks dengan tengah-huruf-besar pada cy (baseline = cy + 0.35*size)."""
    d.text((x, cy + 0.35 * font.size), text, font=font, fill=fill, anchor=anchor + "s",
           stroke_width=stroke, stroke_fill=sfill or INK)
def kwbox(d, x, cy, text, font, anchor="l", padx=20, fill=TEAL, fg=INK):
    w = tw(font, text); x0 = x if anchor == "l" else x - w / 2
    d.rounded_rectangle([x0 - padx, cy - font.size * 0.62, x0 + w + padx, cy + font.size * 0.62], int(font.size * 0.26), fill=fill)
    put(d, x0, cy, text, font, fg, "l")
    return x0 + w + padx

def chip(text, size=44, fill=CARD, fg=WHITE, ring=TEAL, font=MB, padx=40, h=None, wmin=0):
    f = F(font, size); w = max(int(tw(f, text)) + 2 * padx, wmin); h = h or int(size * 1.9)
    base = rr(w, h, h // 2, fill, ring, 3); d = ImageDraw.Draw(base)
    put(d, w / 2, h / 2, text, f, fg, "m")
    return shadow_wrap(base, 10, 6, 80, 16)

def source_chip(name):
    f1, f2 = F(NM, 38), F(NB, 38)
    a, b = "Sumber: ", name
    w = int(tw(f1, a) + tw(f2, b)) + 80; h = 72
    base = rr(w, h, h // 2, (246, 242, 252, 244)); d = ImageDraw.Draw(base)
    put(d, 40, h / 2, a, f1, (90, 74, 126), "l"); put(d, 40 + tw(f1, a), h / 2, b, f2, INK, "l")
    return shadow_wrap(base, 8, 4, 70, 14)

def card_title(kind, kw, rest, sub=None):
    w = 840; bd = 196; x = 22 + bd + 20 + 14
    size = 76; full = kw + (" " + rest if rest else "")
    while tw(F(MX, size), full) + 40 > w - x - 24 and size > 40: size -= 2
    fsub = F(NM, 40); lines = []
    if sub:
        lines = [sub]
        if tw(fsub, sub) > w - x - 24:
            ws_ = sub.split(); k = len(ws_) // 2; lines = [" ".join(ws_[:k]), " ".join(ws_[k:])]
    h = 260 if not sub else (290 if len(lines) == 1 else 340)
    base = rr(w, h, 42, CARD, TEAL, 3); d = ImageDraw.Draw(base)
    bg = badge(kind, bd); base.alpha_composite(bg, (22, h // 2 - bg.height // 2))
    cy = h // 2 - (34 if sub else 0); f = F(MX, size)
    xe = kwbox(d, x + 20, cy, kw, f, "l") + 18
    if rest: put(d, xe, cy, rest, f, WHITE, "l")
    for k, ln in enumerate(lines): put(d, x, cy + 80 + k * 48, ln, fsub, SOFT, "l")
    return shadow_wrap(base)

def card_conv():
    w, h = 840, 420
    base = rr(w, h, 42, CARD, TEAL, 3); d = ImageDraw.Draw(base)
    put(d, w / 2, 50, "badan tukar", F(NM, 40), SOFT, "m")
    put(d, w / 2, 122, "beta-karotin", F(MB, 64), WHITE, "m")
    cx = w / 2; d.rectangle([cx - 8, 172, cx + 8, 218], fill=TEAL); d.polygon([(cx - 32, 212), (cx + 32, 212), (cx, 252)], fill=TEAL)
    fa = F(MX, 78); t2 = "vitamin"; tot = tw(fa, t2) + 44 + tw(fa, "A") + 44
    x = (w - tot) / 2; cy = 332
    put(d, x, cy, t2, fa, WHITE, "l"); kwbox(d, x + tw(fa, t2) + 44, cy, "A", fa, "l")
    return shadow_wrap(base)

def card_chips_label(label):
    f = F(NM, 44); w = int(tw(f, label)) + 70; h = 76
    base = rr(w, h, 38, (26, 15, 52, 200)); d = ImageDraw.Draw(base); put(d, w / 2, h / 2, label, f, SOFT, "m")
    return shadow_wrap(base, 8, 4, 60, 14)

def image_card(path, wd, crop=None, ring=TEAL):
    im = Image.open(path).convert("RGB")
    if crop: im = im.crop(crop)
    h = int(im.height * wd / im.width); im = im.resize((wd, h), Image.LANCZOS)
    base = Image.new("RGBA", (wd, h), (0, 0, 0, 0)); m = Image.new("L", (wd, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, wd - 1, h - 1], 26, fill=255); base.paste(im, (0, 0), m)
    ImageDraw.Draw(base).rounded_rectangle([0, 0, wd - 1, h - 1], 26, outline=ring, width=4)
    return shadow_wrap(base)

def _fill(im, w, h, fx=0.5, fy=0.5):
    sc = max(w / im.width, h / im.height); im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    x = int((im.width - w) * fx); y = int((im.height - h) * fy); return im.crop((x, y, x + w, y + h))
FOCUS = {"lobak": (0.5, 0.6), "goji": (0.55, 0.45), "avokado": (0.55, 0.55), "bunga": (0.5, 0.4)}
def pbadge(kind, d_, ring=TEAL):
    m = 10; im = _fill(Image.open(f"projects/eyecare/assets/ing_{kind}.jpg").convert("RGB"), d_, d_, *FOCUS[kind])
    out = Image.new("RGBA", (d_ + 2 * m, d_ + 2 * m), (0, 0, 0, 0)); mk = Image.new("L", (d_ * 3, d_ * 3), 0)
    ImageDraw.Draw(mk).ellipse([0, 0, d_ * 3 - 1, d_ * 3 - 1], fill=255); mk = mk.resize((d_, d_), Image.LANCZOS)
    out.paste(im, (m, m), mk); ImageDraw.Draw(out).ellipse([m, m, m + d_, m + d_], outline=ring, width=max(4, d_ // 28))
    return out

def photo_card(kind, w, h, kw, rest=None, sub=None):
    im = _fill(Image.open(f"projects/eyecare/assets/ing_{kind}.jpg").convert("RGB"), w, h, *FOCUS[kind]).convert("RGBA")
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for y in range(int(h * 0.45), h):
        gd.line([0, y, w, y], fill=(22, 10, 46, int(225 * (y - h * 0.45) / (h * 0.55))))
    im.alpha_composite(g); d = ImageDraw.Draw(im)
    f = F(MX, 58); cy = h - (96 if sub else 62)
    xe = kwbox(d, 52, cy, kw, f, "l") + 18
    if rest: put(d, xe, cy, rest, f, WHITE, "l")
    if sub: put(d, 34, h - 40, sub, F(NM, 36), SOFT, "l")
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0)); mk = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mk).rounded_rectangle([0, 0, w - 1, h - 1], 38, fill=255); base.paste(im, (0, 0), mk)
    ImageDraw.Draw(base).rounded_rectangle([0, 0, w - 1, h - 1], 38, outline=TEAL, width=4)
    return shadow_wrap(base)

def mal_chip():
    f1, f2 = F(NM, 30), F(MB, 44); a, b = "Berdaftar", "MAL22076147T"
    w = int(tw(f1, a) + 26 + tw(f2, b)) + 80; h = 84
    base = rr(w, h, h // 2, CARD, TEAL, 3); d = ImageDraw.Draw(base)
    put(d, 40, h / 2, a, f1, TEAL, "l"); put(d, 40 + tw(f1, a) + 26, h / 2, b, f2, WHITE, "l")
    return shadow_wrap(base, 10, 6, 80, 16)

def claim_chip():
    f1, f2 = F(NM, 30), F(MB, 40); a, b = "Tuntutan produk:", "kesihatan mata (tradisional)"
    w = int(max(tw(f1, a), tw(f2, b))) + 80; h = 118
    base = rr(w, h, 44, CARD, TEAL, 3); d = ImageDraw.Draw(base)
    put(d, w / 2, 34, a, f1, TEAL, "m"); put(d, w / 2, 78, b, f2, WHITE, "m")
    return shadow_wrap(base, 10, 6, 80, 16)

def slam_sprite():
    f1, f2 = F(MX, 86), F(MX, 108)
    w, h = 860, 240; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    put(d, w / 2, 60, "BUKAN SETAKAT", f1, WHITE, "m", stroke=7, sfill=DEEP)
    tm = tw(f2, "MATA"); bx = w / 2 - tm / 2
    d.rounded_rectangle([bx - 30, 108, bx + tm + 30, 230], 30, fill=TEAL)
    put(d, w / 2, 169, "MATA", f2, INK, "m")
    return shadow_wrap(im, 10, 6, 90, 10)

# ======================= elemen & animasi =======================
class El:
    def __init__(s, spr, cx, cy, t0, t1, enter=0.35, ex=0.12, c=1.1, fs=0.6, shake=None, sfx="pop",
                 fn=None, size=None, margin=0, face_ok=False, a0=0.0, mode="pop"):
        s.spr, s.cx, s.cy, s.t0, s.t1, s.enter, s.ex, s.c, s.fs, s.shake, s.sfx, s.fn = spr, cx, cy, t0, t1, enter, ex, c, fs, shake, sfx, fn
        s.margin = margin
        s.a0, s.mode = a0, mode
        if mode != "pop" and fs == 0.6: s.fs = 0.9
        if isinstance(spr, tuple): s.spr, s.margin = spr
        s.size = size or (s.spr.size if s.spr is not None else None)

    def cyv(s, t): return s.cy(t) if callable(s.cy) else s.cy

    def draw(s, fr, t):
        if t < s.t0 or t >= s.t1: return
        spr = s.fn(t) if s.fn else s.spr
        a = max(s.a0, clamp((t - s.t0) / s.enter * 2.5)); sc = s.fs + (1 - s.fs) * out_back((t - s.t0) / s.enter, s.c)
        if t > s.t1 - s.ex:
            x = (s.t1 - t) / s.ex; a = min(a, x); sc *= 0.93 + 0.07 * x
        dx = dy = 0
        if s.shake:
            st, du, am = s.shake; u = (t - st) / du
            if 0 <= u < 1: dx, dy = am * math.sin(90 * (t - st)) * (1 - u), am * math.cos(70 * (t - st)) * (1 - u)
        mv = {"up": (0, 70), "down": (0, -50), "left": (-150, 0), "right": (150, 0)}.get(s.mode)
        if mv: o = 1 - out_cubic((t - s.t0) / s.enter); dx += mv[0] * o; dy += mv[1] * o
        if abs(sc - 1) > 0.003: spr = spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
        if a < 0.999: spr = spr.copy(); spr.putalpha(spr.getchannel("A").point(lambda v: int(v * a)))
        fr.paste(spr, (int(s.cx - spr.width / 2 + dx), int(s.cyv(t) - spr.height / 2 + dy)), spr)

# ======================= pandangan & jejak muka =======================
def seg_prog(t, a, b): return clamp((t - a) / (b - a))
def punch_mul(t):
    m = 1.0
    for p in PUNCH:
        u = t - p
        if 0 <= u < 0.85:
            k = out_cubic(u / 0.12) if u < 0.12 else (1.0 if u < 0.55 else 1 - out_cubic((u - 0.55) / 0.30))
            m = max(m, 1 + 0.10 * k)
    return m

def window(x0, y0, ww, hw, mx, my):
    x0 = min(max(x0, 0), mx - ww); y0 = min(max(y0, 0), my - hw); return (x0, y0, x0 + ww, y0 + hw)

def face_yo(t): return 700 if t < T_SPLIT0 else 580

def view(t):
    a, b = (0, T_SPLIT0) if t < T_SPLIT0 else ((T_SPLIT0, T_FULL1) if t < T_FULL1 else (T_FULL1, T_END))
    s_ = 1.15 * (1 + 0.035 * seg_prog(t, a, b)) * punch_mul(t); yo = face_yo(t)
    return s_, window(FACE[0] - 540 / s_, FACE[1] - yo / s_, W / s_, H / s_, W, H)

def track_face():
    """Jejak muka (Haar, 10fps) -> projects/eyecare/face_track.json. Perlukan opencv-python-headless==4.10."""
    import cv2
    w, h, fps = 540, 960, 10
    raw = sp.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], stdout=sp.PIPE)
    c = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); out = []; i = 0
    while True:
        b = raw.stdout.read(w * h)
        if len(b) < w * h: break
        g = np.frombuffer(b, np.uint8).reshape(h, w)
        f = [x for x in c.detectMultiScale(g, 1.1, 6, minSize=(90, 90), maxSize=(400, 400)) if 120 < x[1] + x[3] / 2 < 700 and 100 < x[0] + x[2] / 2 < 440]
        out.append([i / fps] + ([float(v * 2) for v in max(f, key=lambda r: r[2] * r[3])] if f else [None] * 4)); i += 1
    json.dump(out, open("projects/eyecare/face_track.json", "w"))

def _load_track():
    from scipy.signal import medfilt
    from scipy.ndimage import maximum_filter1d
    d = [o for o in json.load(open("projects/eyecare/face_track.json")) if o[1] is not None]
    t = np.array([o[0] for o in d]); bot = np.array([o[2] + o[4] for o in d])
    return t, maximum_filter1d(medfilt(bot, 5), 7)   # buang outlier, kemudian ambil maksimum ±0.3s
FT_T, FT_BOT = _load_track()

def face_bot_out(t):
    s_, box = view(t); return (float(np.interp(t, FT_T, FT_BOT)) - box[1]) * s_
def zone_top(t0, t1, margin=12):
    return max(face_bot_out(t) for t in np.arange(t0, t1, 0.1)) + margin
def GD(t0, t1, top): return max(0.0, zone_top(t0, t1) - top)   # anjakan ke bawah supaya overlay di bawah dagu

EL = []
TEXTS = []
def add(*a, **k):
    e = El(*a, **k); EL.append(e); return e

def layout_at(t):
    return "full" if t < T_END else "end"

CX = 510  # pusat safe-area x 60..960

# ---------- HOOK ----------
add(slam_sprite(), CX, 372, 0.0, 2.35, enter=0.16, c=0.6, fs=1.22, shake=(0.0, 0.28, 8), sfx="slam", a0=1.0)
for kind, t, x in (("lobak", 0.0, 210), ("goji", 1.56, 410), ("bunga", 2.46, 610), ("avokado", 3.18, 810)):
    add(pbadge(kind, 140), x, 1285, t, 11.20, margin=10)

# ---------- LOBAK (11.36–24.36): overlay di bawah dagu; sumber di atas kepala ----------
d = GD(11.45, 14.50, 810); add(photo_card("lobak", 760, 350, "LOBAK", "MERAH"), CX, 985 + d, 11.45, 14.50, mode="up")
d = GD(14.55, 21.40, 840); add(card_conv(), CX, 1050 + d, 14.55, 21.40, mode="up")
add(source_chip("Klarity Health"), CX, 292, 15.20, 19.60, mode="down")
d = GD(21.45, 24.25, 842)
add(card_chips_label("vitamin A juga penting untuk"), CX, 880 + d, 21.45, 24.25, mode="up")
add(chip("pertumbuhan", 64, wmin=720), CX, 1010 + d, 21.52, 24.25, mode="left")
add(chip("sistem imun", 64, wmin=720), CX, 1160 + d, 22.80, 24.25, mode="right")

# ---------- GOJI (24.36–34.46) ----------
d = GD(24.95, 28.30, 810); add(photo_card("goji", 760, 350, "GOJI", None, sub="dalam perubatan tradisional Cina"), CX, 985 + d, 24.95, 28.30, mode="up")

def counter_fn(t):
    n = int(2000 * out_cubic((t - 28.40) / 0.55)); txt = f"{n:,}" + ("+" if n >= 2000 else "")
    w, h = 840, 430; base = rr(w, h, 42, CARD, TEAL, 3); d_ = ImageDraw.Draw(base)
    full = "2,000+"; size = 190
    while tw(F(MX, size), full) > 660: size -= 4
    f = F(MX, size); wb = tw(f, full); x0 = w / 2 - wb / 2; cy = 160
    d_.rounded_rectangle([x0 - 34, cy - size * 0.68, x0 + wb + 34, cy + size * 0.68], 38, fill=TEAL)
    put(d_, w / 2, cy, txt, f, INK, "m")
    put(d_, w / 2, 352, "tahun", F(MB, 76), WHITE, "m")
    bg = pbadge("goji", 96); base.alpha_composite(bg, (w - 116 - 16, 8))
    return shadow_wrap(base)[0]
d = GD(28.40, 31.45, 830)
add(None, CX, 1045 + d, 28.40, 31.45, enter=0.2, c=0.8, fn=counter_fn, size=(840, 430), shake=(28.95, 0.28, 7), sfx="tick")
add(source_chip("News-Medical"), CX, 292, 29.80, 33.20, mode="down")
d = GD(31.50, 34.42, 842)
add(card_chips_label("dalam kajian:"), CX, 880 + d, 31.50, 34.42, mode="up")
add(chip("antioksidan", 64, wmin=720), CX, 1010 + d, 31.58, 34.42, mode="left")
add(chip("imun", 64, wmin=720), CX, 1160 + d, 33.62, 34.42, mode="right")

# ---------- AVOKADO (34.62–43.18) ----------
TILES = [240, 420, 600, 780]
LAND = [41.00, 41.20, 41.40, 41.60]
DROP = 0.55
def avo_fn(t):
    w, h = 840, 430; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d_ = ImageDraw.Draw(im)
    pb = pbadge("avokado", 120); im.alpha_composite(pb, (w // 2 - pb.width // 2, 0))
    if t >= 40.50:
        s_ = clamp((t - 40.50) / 0.3); ft = F(MX, 72)
        for i, (cx, tl) in enumerate(zip(TILES, LAND)):
            lit = t >= tl
            sc = 1 + (0.14 * math.sin(math.pi * clamp((t - tl) / 0.25)) if lit else 0)
            half = int(56 * sc * (0.5 + 0.5 * s_))
            d_.rounded_rectangle([cx - half, 290 - half, cx + half, 290 + half], 20, fill=TEAL if lit else (26, 15, 52, 235), outline=TEAL, width=4)
            put(d_, cx, 290, "ADEK"[i], ft, INK if lit else TEAL, "m")
            u = (t - (tl - DROP)) / DROP
            if 0 <= u < 1:
                x = 420 + (cx - 420) * (0.35 * u + 0.65 * u * u); y = 128 + (230 - 128) * u * u
                d_.polygon([(x, y - 34), (x - 17, y + 6), (x, y + 18), (x + 17, y + 6)], fill=(255, 206, 70))
                d_.ellipse([x - 17, y - 2, x + 17, y + 32], fill=(255, 206, 70))
        lab = F(NB, 42); wl = tw(lab, "vitamin larut lemak") + 56
        d_.rounded_rectangle([w / 2 - wl / 2, 366, w / 2 + wl / 2, 420], 27, fill=(26, 15, 52, 225)); put(d_, w / 2, 393, "vitamin larut lemak", lab, SOFT, "m")
    return im
d = GD(35.00, 39.20, 810); add(photo_card("avokado", 760, 350, "AVOKADO"), CX, 985 + d, 35.00, 39.20, mode="up")
d = GD(40.45, 43.08, 830); add(None, CX, 1045 + d, 40.45, 43.08, fn=avo_fn, size=(840, 430), sfx="pop", mode="up")
add(source_chip("Berita Harian 2019"), CX, 292, 36.20, 39.70, mode="down")

# ---------- EYEBRIGHT (43.2–55.4) ----------
d = GD(43.90, 48.70, 800); add(photo_card("bunga", 760, 330, "EYEBRIGHT", None, sub="bunga Eropah"), CX, 965 + d, 43.90, 48.70, mode="up")
add(source_chip("Planta Medica 2023"), CX, 292, 45.90, 49.20, mode="down")
add(source_chip("Christopher Hobbs"), CX, 292, 50.10, 53.60, mode="down")
d = GD(48.75, 55.40, 842)
add(card_chips_label("KEGUNAAN TRADISIONAL"), CX, 880 + d, 48.75, 55.40, mode="up")
_cm, _cs, _ca = chip("mata", 52, padx=34, wmin=210), chip("selsema", 52, padx=34, wmin=210), chip("alahan", 52, padx=34, wmin=210)
_wm, _ws, _wa = _cm[0].width, _cs[0].width, _ca[0].width; _gap = 4
_x0 = CX - (_wm + _ws + _wa + 2 * _gap) / 2
add(_cm, _x0 + _wm / 2, 995 + d, 48.95, 55.40, mode="left")
add(_cs, _x0 + _wm + _gap + _ws / 2, 995 + d, 53.65, 55.40, mode="up")
add(_ca, _x0 + _wm + _ws + 2 * _gap + _wa / 2, 995 + d, 54.85, 55.40, mode="right")

# ---------- PRODUK (55.62–65.94) ----------
d = GD(56.40, T_SKIP0, 934)
add(image_card("projects/eyecare/assets/box_packshot.png", 560), CX, 1062 + d, 56.40, 61.70, mode="up")
add(image_card("projects/eyecare/assets/hologram_real.png", 560, crop=(14, 4, 396, 186)), CX, 1068 + d, 61.70, T_SKIP0 - 0.05, fs=0.75, c=0.9)
for kind, t, x in (("lobak", 57.50, CX - 216), ("goji", 57.72, CX - 72), ("bunga", 57.94, CX + 72), ("avokado", 58.16, CX + 216)):
    add(pbadge(kind, 100), x, 1255 + d, t, 60.80, margin=10)
add(mal_chip(), CX, 1255 + d, 60.90, 63.35, mode="right")
add(claim_chip(), CX, 1262 + d, 63.40, T_SKIP0 - 0.05, mode="left")

# ---------- END CARD ----------
def _line(text, fname, size, kw=None, maxw=860):
    if kw:
        while tw(F(fname, size), text + " ") + tw(F(fname, size), kw) + 44 > maxw: size -= 4
    else:
        while tw(F(fname, size), text) > maxw: size -= 2
    f = F(fname, size); w, h = 900, int(size * 1.7); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kw:
        tot = tw(f, text + " ") + tw(f, kw) + 44; x = w / 2 - tot / 2
        put(d, x, h / 2, text + " ", f, WHITE, "l"); kwbox(d, x + tw(f, text + " ") + 22, h / 2, kw, f, "l")
    else: put(d, w / 2, h / 2, text, f, WHITE, "m")
    return im
add(image_card("projects/eyecare/assets/box_packshot.png", 848), CX, 600, T_END + 0.05, DUR + 1, enter=0.4, mode="up")
add(_line("EYE", MX, 150, kw="CARE"), CX, 950, T_END + 0.12, DUR + 1, enter=0.35, c=0.6, fs=1.4, shake=(T_END + 0.12, 0.25, 7), sfx="slam")
add(chip("MAL22076147T", 46, font=NB), CX, 1095, T_END + 0.30, DUR + 1, mode="up")
add(_line("Digunakan secara tradisional", NM, 40), CX, 1200, T_END + 0.40, DUR + 1, mode="up")
add(_line("untuk kesihatan mata", NM, 40), CX, 1250, T_END + 0.44, DUR + 1, mode="up")
add(_line("Fakta bahan, bukan tuntutan produk.", NM, 34), CX, 1335, T_END + 0.55, DUR + 1, mode="up")

# ======================= kapsyen =======================
def load_tokens():
    d = json.load(open("work/raw_words.json")); T = []
    for s in d:
        for w in s["words"]: T.append([w["w"].strip(), w["s"], w["e"], w["p"]])
    # gabung token yang bermula '-' dengan token sebelumnya
    M = []
    for t in T:
        if t[0].startswith("-") and M: M[-1][0] += t[0]; M[-1][2] = t[2]
        else: M.append(t)
    # baiki ejaan standard (bukan teka: rujuk skrip pengguna + ejaan BM standard)
    out = []; i = 0
    while i < len(M):
        w = M[i][0]; lw = re.sub(r"[.,!?]", "", w).lower(); p = w[len(w.rstrip(".,!?")):]
        nxt = re.sub(r"[.,!?]", "", M[i + 1][0]).lower() if i + 1 < len(M) else ""
        if lw == "beta" and nxt == "keratin": out.append(["beta-karotin" + (M[i+1][0][len(M[i+1][0].rstrip('.,!?')):]), M[i][1], M[i + 1][2], 1]); i += 2; continue
        if lw == "bright" and nxt == "ice": out.append(["Eyebright", M[i][1], M[i + 1][2], 1]); i += 2; continue
        if lw == "sel" and nxt == "semua": out.append(["selsema", M[i][1], M[i + 1][2], 1]); i += 2; continue
        if lw == "di" and nxt.startswith("s-pharma"): out.append(["DS Pharma", M[i][1], M[i + 1][2], 1]); i += 2; continue
        if lw == "so": i += 1; continue   # p=0.12, tidak jelas — tidak dikapsyenkan
        fix = {"lobok": "Lobak", "avocado": "avokado", "china": "Cina", "2000": "2,000", "hybride": "Eyebright", "mal": "MAL"}
        if lw in fix: w = fix[lw] + p
        out.append([w, M[i][1], M[i][2], M[i][3]]); i += 1
    return out

KW = {"lobak", "goji", "avokado", "eyebright", "vitamin", "beta-karotin", "pertumbuhan", "imunisasi", "antioksidan", "2,000",
      "tradisional", "selsema", "alahan", "radang", "setakat", "keempat-empat", "kesihatan", "cina", "tablet", "bukan"}

def make_chunks():
    T = load_tokens(); ch = []; cur = []
    def flush():
        nonlocal cur
        if cur: ch.append(cur); cur = []
    for k, t in enumerate(T):
        if t[1] >= T_SKIP0 - 0.02 and t[1] < T_END + 5: flush(); continue
        if cur and t[1] - cur[-1][2] > 0.28: flush()
        cur.append(t)
        nw = sum(len(x[0].split()) for x in cur)
        if nw >= 3 or t[0][-1] in ".,!?": flush()
    flush()
    res = []
    for i, c in enumerate(ch):
        a = c[0][1] - 0.04
        nxt = ch[i + 1][0][1] - 0.04 if i + 1 < len(ch) else 1e9
        b = min(nxt, c[-1][2] + 0.18)
        res.append((a, max(b, a + 0.30), [x[0].rstrip(".,!?") for x in c]))
    return res

def cap_sprite(words):
    size = 66; fn = F(MX, size)
    while sum(tw(F(MX, size), w) for w in words) + 22 * (len(words) - 1) + 60 > 880 and size > 40: size -= 2
    fn = F(MX, size)
    ws = [tw(fn, w) for w in words]; tot = sum(ws) + 24 * (len(words) - 1)
    kwi = next((i for i, w in enumerate(words) if w.lower() in KW), None)
    w, h = int(tot + 80), int(size * 1.7); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 40
    for i, wd in enumerate(words):
        if i == kwi:
            d.rounded_rectangle([x - 14, h / 2 - size * 0.66, x + ws[i] + 14, h / 2 + size * 0.66], int(size * 0.26), fill=TEAL)
            put(d, x, h / 2, wd, fn, INK, "l")
        else:
            put(d, x, h / 2, wd, fn, WHITE, "l", stroke=6, sfill=DEEP)
        x += ws[i] + 24
    return im

CHUNKS = make_chunks()
def _capcy(t): return 1440
for a, b, words in CHUNKS:
    TEXTS.append(" ".join(words))
    add(cap_sprite(words), CX, _capcy, a, b, enter=0.30, ex=0.10, c=0.9, fs=0.72, sfx=None)

# ======================= latar & layout =======================
def gradient(w, h, c0, c1):
    t = np.linspace(0, 1, h)[:, None, None]; a = np.array(c0)[None, None, :] * (1 - t) + np.array(c1)[None, None, :] * t
    return Image.fromarray(np.repeat(a, w, axis=1).astype(np.uint8), "RGB")

def _bubble(r, col, a):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=col + (a,))
    return im.filter(ImageFilter.GaussianBlur(r * 0.16))
LAV = (150, 110, 220)
BUBS = [(_bubble(170, TEAL, 40), 180, 300, 0.30, 0.21, 0.0), (_bubble(240, LAV, 46), 820, 700, 0.17, 0.25, 1.7),
        (_bubble(130, TEAL, 32), 620, 150, 0.35, 0.15, 3.1), (_bubble(200, LAV, 38), 120, 900, 0.22, 0.19, 4.4),
        (_bubble(180, TEAL, 34), 900, 1300, 0.20, 0.23, 2.2), (_bubble(260, LAV, 42), 200, 1650, 0.16, 0.18, 5.0)]
_fan = Image.new("RGBA", (900, 900), (0, 0, 0, 0)); _fd = ImageDraw.Draw(_fan)
for k in range(24):
    a = math.radians(k * 15); l1 = 330 + (k % 3) * 70
    _fd.line([450 + 150 * math.cos(a), 450 + 150 * math.sin(a), 450 + l1 * math.cos(a), 450 + l1 * math.sin(a)], fill=(123, 203, 205, 84), width=9)
GRAD = {1056: gradient(W, 1056, PURPLE, DEEP), H: gradient(W, H, PURPLE, DEEP)}
def bg_frame(t, h):
    im = GRAD[h].copy()
    for spr, x, y, s1, s2, ph in BUBS:
        if y > h: continue
        im.paste(spr, (int(x - spr.width / 2 + 70 * math.sin(t * s1 + ph)), int(y - spr.height / 2 + 50 * math.cos(t * s2 + ph))), spr)
    fan = _fan.rotate(10 * math.sin(t * 0.25), resample=Image.BILINEAR)
    im.paste(fan, (W - 70 - 450, 70 - 450), fan)
    return im

def base_frame(src, t):
    if layout_at(t) == "end": return bg_frame(t, H)
    s_, box = view(t)
    return src.resize((W, H), Image.BILINEAR, box=box)

def zoom_through(fr, k):
    z = 1 + 0.38 * k * k
    ww, hw = W / z, H / z
    out = fr.resize((W, H), Image.BILINEAR, box=((W - ww) / 2, (H - hw) / 2, (W + ww) / 2, (H + hw) / 2))
    if k > 0.2: out = out.filter(ImageFilter.GaussianBlur(5 * k))
    return out

def compose(src, t):
    fr = base_frame(src, t)
    for e in EL: e.draw(fr, t)
    for ft in FLASH:
        if ft <= t < ft + 0.12:
            a = 0.30 * (1 - (t - ft) / 0.12); fr = Image.blend(fr, Image.new("RGB", (W, H), WHITE), a)
    for T in ZT:
        if T - 0.15 <= t < T: fr = zoom_through(fr, (t - (T - 0.15)) / 0.15)
        elif T <= t < T + 0.15: fr = zoom_through(fr, 1 - (t - T) / 0.15)
    return fr

# ======================= render =======================
def render(i0, i1, out):
    n = i1 - i0
    dec = sp.Popen(["ffmpeg", "-v", "error", "-ss", f"{i0 / FPS:.5f}", "-i", SRC, "-vf", f"fps={FPS}", "-frames:v", str(n),
                    "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=sp.PIPE)
    enc = sp.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=sp.PIPE)
    last = None
    for i in range(i0, i1):
        raw = dec.stdout.read(W * H * 3)
        src = Image.frombuffer("RGB", (W, H), raw, "raw", "RGB", 0, 1) if len(raw) == W * H * 3 else last
        last = src
        enc.stdin.write(compose(src, i / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.wait()

# ======================= audio =======================
def synth_audio():
    from scipy.signal import lfilter
    rng = np.random.RandomState(7); n = int(DUR * SR); t = np.arange(n) / SR
    raw = np.frombuffer(sp.run(["ffmpeg", "-v", "error", "-i", SRC, "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout, np.float32).reshape(-1, 2)
    voice = np.zeros((n, 2), np.float32); voice[:min(n, len(raw))] = raw[:n]
    mono = voice.mean(1); blk = int(0.02 * SR)
    rms = np.sqrt(np.convolve(mono ** 2, np.ones(blk) / blk, "same")); sp_rms = np.sqrt(np.mean(mono[rms > 0.02] ** 2))
    env = lfilter([1 - math.exp(-1 / (0.05 * SR))], [1, -math.exp(-1 / (0.05 * SR))], rms)
    rel = lfilter([1 - math.exp(-1 / (0.35 * SR))], [1, -math.exp(-1 / (0.35 * SR))], np.maximum(rms, 0))
    duck = 1 - 0.50 * np.clip(np.maximum(env, rel) / (0.6 * sp_rms), 0, 1)
    # --- muzik lembut instrumental (pad + arpeggio) ---
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [(48, 52, 55, 59, 62), (45, 48, 52, 55, 59), (41, 45, 48, 52, 55), (43, 47, 50, 52, 57)]
    bar = 60 / 84 * 4; music = np.zeros(n)
    for k in range(int(DUR / (2 * bar)) + 2):
        ch = chords[k % 4]; s0 = k * 2 * bar; s1 = s0 + 2 * bar
        e = np.clip((t - (s0 - 1.0)) / 1.2, 0, 1) * np.clip(((s1 + 1.4) - t) / 1.6, 0, 1)
        for m in ch:
            f = midi(m); music += e * (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.004 * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t))
        step = 60 / 84 / 2; j = 0; ts = s0
        while ts < s1 and ts < DUR:
            m = ch[[2, 4, 3, 4, 2, 3, 4, 3][j % 8]] + 12; f = midi(m); i0 = int(ts * SR); L = int(0.6 * SR); tt = np.arange(min(L, n - i0)) / SR
            music[i0:i0 + len(tt)] += 0.9 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5.5) * (1 - np.exp(-tt * 300)); ts += step; j += 1
    music *= 1 + 0.08 * np.sin(2 * np.pi * 0.2 * t)
    music *= (10 ** (-15 / 20) * sp_rms) / np.sqrt(np.mean(music ** 2))
    music *= np.clip((DUR - t) / 0.8, 0, 1) * np.clip(t / 0.5, 0, 1)
    mus = np.stack([music * duck, np.roll(music, 220) * duck], 1)
    # --- SFX prosedural ---
    sfx = np.zeros((n, 2)); lvl = lambda db: 10 ** (db / 20) * sp_rms
    def put_(sig, at, g):
        i = int(at * SR); sig = sig[:max(0, n - i)]; sfx[i:i + len(sig)] += (sig * g)[:, None]
    def tone(f0, f1, d, dec_):
        tt = np.arange(int(d * SR)) / SR; f = f0 + (f1 - f0) * tt / d; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * dec_) * (1 - np.exp(-tt * 400))
    def whoosh(d):
        tt = np.arange(int(d * SR)) / SR; nz = rng.randn(len(tt)); a = 0.02 + 0.5 * (tt / d)
        y = lfilter([1], [1, -0.97], nz) * 0.1 + nz * 0.05; return y * np.sin(np.pi * tt / d) ** 2
    pop, plink = tone(480, 900, 0.11, 30), tone(1200, 800, 0.16, 20)
    nzb = lfilter([1], [1, -0.9], rng.randn(int(0.12 * SR))); slam = tone(110, 38, 0.55, 7); slam[:len(nzb)] += 0.35 * nzb * np.exp(-np.arange(len(nzb)) / SR * 40)
    for e in EL:
        if e.sfx == "pop": put_(pop, e.t0, lvl(-24))
        elif e.sfx == "slam": put_(slam, e.t0, lvl(-15))
        elif e.sfx == "tick":
            for q in range(10): put_(tone(1800, 1800, 0.02, 160), e.t0 + q * 0.05, lvl(-30))
    for T in ZT: put_(whoosh(0.34), T - 0.18, lvl(-18))
    for tl in LAND: put_(plink, tl, lvl(-26))
    mix = voice + mus + sfx
    np.save("work/mix.npy", mix.astype(np.float32))
    import wave
    w = wave.open("work/mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

def finalize_audio():
    r = sp.run(["ffmpeg", "-hide_banner", "-i", "work/mix.wav", "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    sp.run(["ffmpeg", "-y", "-v", "error", "-i", "work/mix.wav", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "work/mix.m4a"], check=True)

# ======================= semakan =======================
BAN = re.compile(r"rawat|cegah|terbukti|klinikal|blue ?light|tajam|sebelum|selepas|✓|harga|rm\s?\d|beg kuning|beli", re.I)
def check():
    bad = []
    for e in EL:
        if e.size is None or e.t0 >= T_END: continue
        w, h = e.size; w -= 2 * e.margin; h -= 2 * e.margin
        if callable(e.cy): continue
        x0, x1, y0, y1 = e.cx - w / 2, e.cx + w / 2, e.cy - h / 2, e.cy + h / 2
        if x0 < 60 or x1 > 960 or y0 < 250 or y1 > 1500: bad.append(("safe-area", e.t0, round(x0), round(x1), round(y0), round(y1)))
        if y1 <= 345 or (e.t0 < T_SPLIT0 and y1 <= 495): continue      # di atas kepala (sumber / slam hook)
        zt = zone_top(e.t0, e.t1, 6)
        if y0 < zt: bad.append(("muka", round(e.t0, 2), round(y0), "dagu+", round(zt)))
        if y1 > 1405 and not (e.t0 < T_SPLIT0): bad.append(("rapat-kapsyen", round(e.t0, 2), round(y1)))
    for a, b, wd in CHUNKS:
        if BAN.search(" ".join(wd)): bad.append(("larangan", a, wd))
    return bad

def write_srt():
    def ts(t): return f"{int(t // 3600):02}:{int(t % 3600 // 60):02}:{int(t % 60):02},{int(round((t % 1) * 1000)) % 1000:03}"
    with open("projects/eyecare/captions.srt", "w") as f:
        for i, (a, b, wd) in enumerate(CHUNKS, 1): f.write(f"{i}\n{ts(max(a, 0))} --> {ts(b)}\n{' '.join(wd)}\n\n")

if __name__ == "__main__":
    m = sys.argv[1]
    if m == "track": track_face()
    elif m == "check":
        print(check()); write_srt(); print(len(CHUNKS), "chunks; slam=", sum(e.sfx in ("slam",) for e in EL), "flash=", len(FLASH))
    elif m == "render": render(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif m == "audio": synth_audio(); finalize_audio()
    elif m == "all":
        os.makedirs("work/chunks", exist_ok=True); k = 4; bnd = [NF * i // k for i in range(k + 1)]
        ps = [sp.Popen([sys.executable, __file__, "render", str(bnd[i]), str(bnd[i + 1]), f"work/chunks/c{i}.mp4"]) for i in range(k)]
        for p in ps: p.wait()
        open("work/chunks/list.txt", "w").write("".join(f"file 'c{i}.mp4'\n" for i in range(k)))
        sp.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-i", "work/chunks/list.txt", "-c", "copy", "work/video_silent.mp4"], check=True)
        synth_audio(); finalize_audio()
        sp.run(["ffmpeg", "-y", "-v", "error", "-i", "work/video_silent.mp4", "-i", "work/mix.m4a", "-map", "0:v", "-map", "1:a", "-c", "copy",
                "-t", str(DUR), "-movflags", "+faststart", OUT], check=True)
        print("OK", OUT)
