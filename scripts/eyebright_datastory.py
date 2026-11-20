#!/usr/bin/env python3
"""Eyebright (Skrip 7) - tema DATA STORY: #101f32 / #edf6ff / #66d5c0.
Jump-cut + zoom + kad carta berlabel (tajuk=takeaway, sumber di dalam kad) + subtitle + end card + audio kod.

Guna:
  eyebright_datastory.py render                  -> work/eyebright_ds.mp4 (belum normalize)
  eyebright_datastory.py stills 1.0,9.5,20       -> work/still_<t>.png (semakan layout; overlay atas frame edit lama)

Perlu: work/eyebright.json (faster-whisper word timestamps), work/eyebright_corr.json,
       assets/product_box.png (still kotak produk), input/eyebright.mov
Skrip ini khusus untuk video Eyebright; ubah ANCHOR/ZOOM di bawah untuk video lain.
"""
import json, subprocess, sys, os, math, random
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
CX = 510          # pusat visual: ofset ke kiri supaya jauh dari butang TikTok di kanan
# Zon selamat TikTok: x 100-920, y 180-1500 (atas ~170px, bawah ~420px, kanan ~160px dikecualikan)
VID, NAME = "input/eyebright.mov", "eyebright"
OUT = "eyebright_ds"
GAP, PAD_IN, PAD_OUT, XF, XF_HARD = 0.30, 0.12, 0.20, 0.12, 0.034
FX, FY = 0.55, 0.35
END = 2.5
FORCE_BREAKS = {101}         # sebelum "DS Pharma" -> hard cut
HARD = {101}

# ---------- warna (Data Story) ----------
BG, TEXT, ACCENT = (16, 31, 50), (237, 246, 255), (102, 213, 192)       # #101f32 / #edf6ff / #66d5c0
ORANGE, RED, YELLOW = (255, 150, 60), (240, 86, 100), (255, 214, 70)    # warna siri pigmen: lobak / goji / lutein
TEAL, NAVY, WHITE, GOLD = ACCENT, BG, TEXT, ACCENT

# ================= timeline =================
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", VID]))
words = [x for s in json.load(open(f"work/{NAME}.json")) for x in s["words"]]
corr = json.load(open(f"work/{NAME}_corr.json"))
for i, w in enumerate(words):
    w["t"] = corr.get(str(i), w["w"].strip())

groups, cur = [], [0]
for i in range(1, len(words)):
    if words[i]["s"] - words[i - 1]["e"] >= GAP or i in FORCE_BREAKS:
        groups.append(cur); cur = []
    cur.append(i)
groups.append(cur)
segs = []
for k, g in enumerate(groups):
    a = max(words[g[0]]["s"] - PAD_IN, 0)
    b = words[g[-1]]["e"] + (0.35 if k == len(groups) - 1 else PAD_OUT)
    segs.append([a, min(b, dur), g])
for k in range(len(segs) - 1):          # elak potongan bertindih
    if segs[k][1] > segs[k + 1][0]:
        mid = (words[segs[k][2][-1]]["e"] + words[segs[k + 1][2][0]]["s"]) / 2
        segs[k][1] = segs[k + 1][0] = mid
xfs = [0] + [XF_HARD if segs[i][2][0] in HARD else XF for i in range(1, len(segs))]
offs, cum = [], 0.0
for i, (a, b, g) in enumerate(segs):
    if i == 0: offs.append(0.0); cum = b - a
    else: offs.append(cum - xfs[i]); cum += (b - a) - xfs[i]
TOTAL = cum                  # tamat ucapan
ALL = TOTAL + END

def T(src):
    for i, (a, b, g) in enumerate(segs):
        if src <= b: return offs[i] + max(src - a, 0)
    return TOTAL
def Ts(i): return T(words[i]["s"])
def Te(i): return T(words[i]["e"])

# zoom asas per segmen: (z0, z1, [indeks perkataan untuk punch-in])
SEGZ = [(1.15, 1.17, [8]), (1.16, 1.18, [15]), (1.10, 1.04, []), (1.00, 1.08, []), (1.10, 1.00, []),
        (1.04, 1.14, []), (1.12, 1.02, []), (1.02, 1.10, []), (1.15, 1.27, []), (1.00, 1.05, []), (1.05, 1.00, [])]
assert len(SEGZ) == len(segs), (len(SEGZ), len(segs))

# ================= masa anchor motion graphic =================
A = dict(
    carrot=Ts(0) + 0.30, goji=Ts(3), hook_out=Te(15) + 0.2,
    split_in=Ts(18), pigmen=Ts(20), karot=Ts(23), split_out=Te(23) + 0.45,
    lobak_in=Ts(28) - 0.2, arrow=Ts(32), vitA=Ts(36), chip1=Ts(43), chip2=Ts(49), lobak_out=Te(51) + 0.3,
    goji_in=Ts(52), zea=Ts(56), eye=Ts(62), macula=Ts(70), goji_out=Te(76) + 0.3,
    avo_in=Ts(77), avo_split=Ts(84), lutein=Ts(85), avo_out=Te(87) + 0.3,
    pig_in=Ts(97), pig_out=Te(100) + 0.12,
    prod_in=Ts(101), prod_zoom_end=Ts(128) + 0.3, trad=Ts(116), mal=Ts(121), prod_out=Te(141) + 0.3,
)

# ================= util grafik =================
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo3(x): x = clamp(x); return 1 - (1 - x) ** 3
def eob(x, s=1.70158): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)

FB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
_f = {}
def font(sz, heavy=True):
    k = (sz, heavy)
    if k not in _f: _f[k] = ImageFont.truetype(FB if heavy else FM, sz)
    return _f[k]

def SS(w, h, fn, k=3):
    im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)); fn(ImageDraw.Draw(im), k)
    return im.resize((w, h), Image.LANCZOS)

def fade(sp, a):
    sp = sp.copy(); sp.putalpha(sp.getchannel("A").point(lambda v: int(v * a))); return sp

def blit(dst, sp, x, y, alpha=1.0):
    if alpha <= 0.003: return
    if alpha < 0.997: sp = fade(sp, alpha)
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + sp.width, dst.width), min(y + sp.height, dst.height)
    if x1 <= x0 or y1 <= y0: return
    if (x0, y0, x1, y1) != (x, y, x + sp.width, y + sp.height): sp = sp.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    dst.alpha_composite(sp, (x0, y0))

def place(dst, sp, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if abs(scale - 1) > 1e-3: sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    blit(dst, sp, cx - sp.width / 2, cy - sp.height / 2, alpha)

_c = {}
def cached(key, fn):
    if key not in _c: _c[key] = fn()
    return _c[key]

def text_sp(txt, size, fill=TEXT, heavy=True, stroke=0, sfill=(0, 0, 0)):
    def mk():
        f = font(size, heavy); bb = f.getbbox(txt, stroke_width=stroke); p = 6
        im = Image.new("RGBA", (bb[2] - bb[0] + 2 * p + 2 * stroke, bb[3] - bb[1] + 2 * p + 2 * stroke), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((p + stroke - bb[0], p + stroke - bb[1]), txt, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=sfill + (255,))
        return im
    return cached(("t", txt, size, fill, heavy, stroke), mk)

def plate_sp(lines, size, fgs, padx=54, pady=26, r=30):
    def mk():
        f = font(size); lh = int(size * 1.12)
        ws = [f.getlength(l) for l in lines]; w = int(max(ws) + 2 * padx); h = int(lh * len(lines) + 2 * pady)
        k = 2; im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), r * k, fill=BG + (250,))
        d.rounded_rectangle((3 * k, 3 * k, w * k - 4 * k, h * k - 4 * k), r * k, outline=ACCENT + (255,), width=5 * k)
        f2 = font(size * k)
        for n, l in enumerate(lines):
            bb = f2.getbbox(l)
            d.text(((w * k - (bb[2] - bb[0])) / 2 - bb[0], (pady + n * lh) * k + (lh * k - (bb[3] - bb[1])) / 2 - bb[1] - size * 0.02 * k), l, font=f2, fill=fgs[n] + (255,))
        return im.resize((w, h), Image.LANCZOS)
    return cached(("p", tuple(lines), size, tuple(fgs)), mk)

def chip_sp(txt, size, bg, fg, padx=30, pady=16, outline=None, bga=255, heavy=True):
    def mk():
        f = font(size, heavy); w = int(f.getlength(txt) + 2 * padx); h = int(size * 1.2 + 2 * pady)
        k = 3; im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), (h // 2) * k, fill=bg + (bga,), outline=(outline + (255,)) if outline else None, width=4 * k)
        im = im.resize((w, h), Image.LANCZOS)
        t = text_sp(txt, size, fg, heavy)
        im.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2 - 1))
        return im
    return cached(("c", txt, size, bg, fg, outline, bga, heavy), mk)

CARD_W, CARD_H, CARD_CY = 820, 410, 1080
CONTENT_CY = 215                      # pusat kawasan kandungan dalam kad (y 84-350)

def card_bg(w, h, accent=None):
    def mk():
        return SS(w, h, lambda d, k: (d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), 28 * k, fill=BG + (244,)),
                                      d.rounded_rectangle((1 * k, 1 * k, w * k - 2 * k, h * k - 2 * k), 27 * k, outline=TEXT + (46,), width=2 * k)))
    return cached(("cb", w, h), mk).copy()

def chart_card(title, source=None, footer=None):
    """Kad carta: tajuk = takeaway, kandungan di tengah, sumber/nota di bawah."""
    def mk():
        L = card_bg(CARD_W, CARD_H)
        d = ImageDraw.Draw(L)
        d.rectangle((36, 22, 36 + 56, 26), fill=ACCENT + (255,))                       # penanda aksen
        L.alpha_composite(text_sp(title, 34, TEXT), (30, 28))
        d.line((36, 80, CARD_W - 36, 80), fill=TEXT + (50,), width=2)
        note = source and ("Sumber: " + source) or footer
        if note: L.alpha_composite(text_sp(note, 28, (170, 190, 210), heavy=False), (30, CARD_H - 52))
        return L
    return cached(("chart", title, source, footer), mk).copy()

def draw_path(L, pts, p, col, width=4):
    """Lukis polyline dari titik pertama sehingga bahagian p (0-1)."""
    if p <= 0: return
    segs_ = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    lens = [math.dist(a, b) for a, b in segs_]; goal = sum(lens) * clamp(p); d = ImageDraw.Draw(L)
    for (a, b), ln in zip(segs_, lens):
        if goal <= 0: break
        f = min(1.0, goal / ln) if ln else 1
        d.line((a[0], a[1], a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), fill=col + (255,), width=width, joint="curve")
        goal -= ln

def pop_img(L, sp, cx, cy, s):
    if s <= 0.02: return
    q = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BILINEAR)
    L.alpha_composite(q, (int(cx - q.width / 2), int(cy - q.height / 2)))

# ---------- ikon ----------
def poly_ellipse(cx, cy, rx, ry, ang, n=40):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang)); pts = []
    for i in range(n):
        t = 2 * math.pi * i / n; x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts

def carrot_sp(S=260):
    def mk():
        def fn(d, k):
            def P(pts): return [(x * k, y * k) for x, y in pts]
            for a, col in ((-30, (46, 125, 50)), (30, (46, 125, 50)), (0, (76, 175, 80))):
                bx, by = 120, 105; tx, ty = bx + math.sin(math.radians(a)) * 95, by - math.cos(math.radians(a)) * 95
                mx, my = (bx + tx) / 2, (by + ty) / 2; nx, ny = math.cos(math.radians(a)) * 17, math.sin(math.radians(a)) * 17
                d.polygon(P([(bx, by), (mx - nx, my - ny), (tx, ty), (mx + nx, my + ny)]), fill=col + (255,))
            d.ellipse(P([(66, 80), (174, 130)]) if False else (66 * k, 80 * k, 174 * k, 130 * k), fill=ORANGE + (255,))
            d.polygon(P([(66, 105), (174, 105), (124, 292), (116, 292)]), fill=ORANGE + (255,))
            for y, ox in ((140, 22), (178, 15), (214, 9)):
                d.line(P([(120 - ox, y), (120 - ox + 18, y + 4)]), fill=(214, 98, 8, 255), width=5 * k)
                d.line(P([(120 + ox - 18, y + 14), (120 + ox, y + 10)]), fill=(214, 98, 8, 255), width=5 * k)
        im = SS(240, 300, fn); return im.resize((int(240 * S / 300), S), Image.LANCZOS)
    return cached(("carrot", S), mk)

def goji_sp(S=260):
    def mk():
        def fn(d, k):
            def P(pts): return [(x * k, y * k) for x, y in pts]
            for cx, cy, rx, ry, a in ((62, 105, 27, 52, -30), (142, 85, 27, 52, 14), (195, 160, 27, 52, 58), (112, 180, 26, 48, 100)):
                d.polygon(P(poly_ellipse(cx, cy, rx, ry, a)), fill=RED + (255,))
                d.polygon(P(poly_ellipse(cx - 10, cy - 14, 8, 20, a)), fill=(255, 255, 255, 90))
                ex = cx + math.sin(math.radians(a)) * -ry; ey = cy - math.cos(math.radians(a)) * ry
                d.ellipse(((ex - 9) * k, (ey - 9) * k, (ex + 9) * k, (ey + 9) * k), fill=(56, 142, 60, 255))
        im = SS(260, 240, fn); return im.resize((S, int(240 * S / 260)), Image.LANCZOS)
    return cached(("goji", S), mk)

def avocado_sp(S=300):
    def mk():
        def fn(d, k):
            def pear(cx, sc, col):
                def P(pts): return [(cx * k + (x - 100) * sc * k, (140 + (y - 140) * sc) * k) for x, y in pts]
                d.polygon(P([(50, 95), (150, 95), (188, 165), (12, 165)]), fill=col)
                d.ellipse(P([(48, 28), (152, 132)])[0] + P([(48, 28), (152, 132)])[1], fill=col)
                d.ellipse(P([(10, 85), (190, 265)])[0] + P([(10, 85), (190, 265)])[1], fill=col)
            pear(100, 1.0, (59, 107, 31, 255)); pear(100, 0.86, (205, 226, 120, 255))
            d.ellipse((58 * k, 143 * k, 142 * k, 227 * k), fill=(139, 90, 43, 255))
            d.ellipse((72 * k, 154 * k, 96 * k, 178 * k), fill=(190, 140, 90, 255))
        im = SS(200, 280, fn); return im.resize((int(200 * S / 280), S), Image.LANCZOS)
    return cached(("avo", S), mk)

def soft_dot(r, col):
    def mk():
        k = 4; n = (r * 2 + 8)
        im = Image.new("RGBA", (n * k, n * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = n * k / 2
        for i in range(10, 0, -1):
            rr = r * k * (0.55 + 0.45 * i / 10); d.ellipse((c - rr, c - rr, c + rr, c + rr), fill=col + (int(255 * (1 - i / 10) ** 1.4 * 0.35 + 255 * (i == 1) * 0.65),))
        d.ellipse((c - r * k * 0.55, c - r * k * 0.55, c + r * k * 0.55, c + r * k * 0.55), fill=col + (255,))
        return im.resize((n, n), Image.LANCZOS)
    return cached(("dot", r, col), mk)

def eye_sp():
    def mk():
        def fn(d, k):
            def e(x0, y0, x1, y1, **kw): d.ellipse((x0 * k, y0 * k, x1 * k, y1 * k), **kw)
            c = (285, 210); r = 150
            e(c[0] - r, c[1] - r, c[0] + r, c[1] + r, outline=(255, 255, 255, 255), width=8 * k)
            d.arc(((c[0] - 205) * k, (c[1] - 75) * k, (c[0] - 55) * k, (c[1] + 75) * k), 110, 250, fill=(255, 255, 255, 255), width=8 * k)
            e(c[0] - 85, c[1] - 55, c[0] - 45, c[1] + 55, outline=(120, 200, 255, 255), width=6 * k)
            d.arc(((c[0] - r - 9) * k, (c[1] - r - 9) * k, (c[0] + r + 9) * k, (c[1] + r + 9) * k), -48, 48, fill=TEAL + (255,), width=16 * k)
            a = math.radians(24); x1, y1 = c[0] + (r + 4) * math.cos(a), c[1] + (r + 4) * math.sin(a)
            d.line((x1 * k, y1 * k, (x1 + 50) * k, (y1 + 40) * k), fill=(170, 180, 195, 255), width=14 * k)
            e(c[0] + r - 12, c[1] - 12, c[0] + r + 12, c[1] + 12, fill=YELLOW + (255,), outline=(255, 255, 255, 255), width=3 * k)
            d.line(((c[0] - 215) * k, c[1] * k, (c[0] + r - 14) * k, c[1] * k), fill=(255, 255, 255, 70), width=3 * k)
        return SS(560, 420, fn)
    return cached(("eye",), mk)

# ---------- partikel ----------
_rng = random.Random(7)
PARTS = [(side, _rng.random(), _rng.uniform(-90, 90), _rng.choice((9, 12, 15))) for side in (0, 1) for _ in range(22)]

# ================= render satu frame =================
def card_xform(t, t_in, t_out):
    u = t - t_in
    if u < 0 or t > t_out + 0.25: return None
    a = clamp(u / 0.15) * clamp((t_out + 0.25 - t) / 0.25)
    s = (0.88 + 0.12 * eo3(u / 0.32)) * (1 - 0.04 * (1 - clamp((t_out + 0.25 - t) / 0.25)))
    return s, a

def draw_slam(cv, t, t0, t1, sp, cx, cy, rot=0.0):
    u = t - t0
    if u < 0 or t > t1: return False
    s = 1 + 0.45 * (1 - eo3(u / 0.16))
    sh = max(0.0, 1 - u / 0.3)
    place(cv, sp, cx + math.sin(u * 90) * 8 * sh, cy, s, clamp(u / 0.05) * clamp((t1 - t) / 0.14), rot)
    return True

def hook_icons(cv, t):
    used = False
    for t0, sp_fn, cx, rot, lab in ((A["carrot"], carrot_sp, 195, 28, "lobak"), (A["goji"], goji_sp, 830, -12, "goji")):
        u = t - t0
        if u < 0 or t > A["hook_out"] + 0.25: continue
        out = clamp((A["hook_out"] + 0.25 - t) / 0.25)
        s = eob(u / 0.35) * (1 + 0.03 * math.sin(u * 5)) * out
        if s > 0.02: place(cv, sp_fn(190), cx, 1150, s, 1.0, rot); used = True
    return used

def scene_split(cv, t):
    if t < A["split_in"] or t > A["split_out"] + 0.4: return False
    u = t - A["split_in"]
    top = 1920 - (1920 - 880) * eio(u / 0.38) + (1920 - 880) * eio((t - A["split_out"]) / 0.4)
    panel = cached(("panel",), lambda: SS(W, 1040, lambda d, k: (d.rectangle((0, 0, W * k, 1040 * k), fill=BG + (246,)),
                                                                 d.rectangle((0, 0, W * k, 5 * k), fill=ACCENT + (255,))), 1))
    blit(cv, panel, 0, top)
    dy = top - 880
    place(cv, text_sp("Karotenoid memberi warna pada makanan", 34, TEXT), CX, 922 + dy, 1, clamp((u - 0.2) / 0.3))
    IY = 1035 + dy; c = (CX, 1120 + dy)
    place(cv, carrot_sp(150), 190, IY, eob((u - 0.15) / 0.35), 1, 20)
    place(cv, goji_sp(150), 790, IY, eob((u - 0.25) / 0.35), 1, -10)
    place(cv, text_sp("lobak", 30, (165, 185, 205), heavy=False), 190, IY + 105, 1, clamp((u - 0.35) / 0.3))
    place(cv, text_sp("goji", 30, (165, 185, 205), heavy=False), 790, IY + 105, 1, clamp((u - 0.45) / 0.3))
    if t >= A["pigmen"]:
        up = t - A["pigmen"]
        for side, ph, off, r in PARTS:
            p = ((up * 0.85 + ph) % 1.0)
            sx, sy = (190, IY) if side == 0 else (790, IY)
            cx_, cy_ = (sx + c[0]) / 2, (sy + c[1]) / 2 + off
            x = (1 - p) ** 2 * sx + 2 * (1 - p) * p * cx_ + p * p * c[0]
            y = (1 - p) ** 2 * sy + 2 * (1 - p) * p * cy_ + p * p * c[1]
            al = clamp(p / 0.12) * clamp((1 - p) / 0.15)
            place(cv, soft_dot(r, ORANGE if side == 0 else RED), x, y, 1, al * clamp(up / 0.2))
        pulse = 1 + 0.04 * math.sin(up * 7)
        ring = cached(("ring",), lambda: SS(250, 250, lambda d, k: (d.ellipse((6 * k, 6 * k, 244 * k, 244 * k), fill=ACCENT + (34,)),
                                                                     d.ellipse((6 * k, 6 * k, 244 * k, 244 * k), outline=ACCENT + (255,), width=8 * k))))
        place(cv, ring, c[0], c[1], eob(up / 0.3) * pulse)
        place(cv, text_sp("pigmen", 48, TEXT), c[0], c[1], eob((up - 0.1) / 0.3))
    return True

def layer_lobak(t):
    L = chart_card("Badan tukar beta-karotin jadi vitamin A", source="Klarity Health; Kemenkes Indonesia")
    ic = carrot_sp(96); tb = text_sp("beta-karotin", 40, TEXT)
    pill = chip_sp("vitamin A", 44, ACCENT, BG, padx=26, pady=12)
    AW = 100
    gw = 96 + 16 + tb.width + 26 + AW + 26 + pill.width
    x = (CARD_W - gw) // 2; cy = 150
    icr = ic.rotate(25, resample=Image.BICUBIC, expand=True); L.alpha_composite(icr, (x - (icr.width - 96) // 2, cy - icr.height // 2)); x += 112
    L.alpha_composite(tb, (x, cy - tb.height // 2)); x += tb.width + 26
    p = eio((t - A["arrow"]) / 0.55)                       # anak panah dilukis
    if p > 0:
        lay = Image.new("RGBA", (AW * 3, 60 * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.line((8 * 3, 30 * 3, (8 + 82 * p) * 3, 30 * 3), fill=ACCENT + (255,), width=8 * 3)
        if p > 0.82:
            hp = clamp((p - 0.82) / 0.18); hx = 92
            for sg in (-1, 1): d.line((hx * 3, 30 * 3, (hx - 22 * hp) * 3, (30 + sg * 20 * hp) * 3), fill=ACCENT + (255,), width=8 * 3)
        L.alpha_composite(lay.resize((AW, 60), Image.LANCZOS), (x, cy - 30))
    x += AW + 26
    pcx = x + pill.width // 2
    s = eob((t - A["vitA"]) / 0.35)
    pop_img(L, pill, pcx, cy, s)
    cs = [("mata", A["chip1"]), ("daya tahan badan", A["chip2"])]
    sps = [chip_sp(tx, 34, BG, TEXT, padx=24, pady=12, outline=ACCENT) for tx, _ in cs]
    gap = 28; tw = sum(s_.width for s_ in sps) + gap; x0 = (CARD_W - tw) // 2 - 60; cyc = 292
    xs = []
    for sp_ in sps: xs.append(x0 + sp_.width // 2); x0 += sp_.width + gap
    for sp_, (tx, t0), cxx in zip(sps, cs, xs):
        draw_path(L, [(pcx, cy + 34), (pcx, 222), (cxx, 222), (cxx, cyc - sp_.height // 2 - 2)], clamp((t - t0 + 0.3) / 0.3), ACCENT)
        pop_img(L, sp_, cxx, cyc, eob((t - t0) / 0.3))
    return L

def layer_goji(t):
    L = chart_card("Goji dikaitkan dengan pigmen makula", source="Nutrition Advance; Healthline")
    k = clamp((t - A["eye"]) / 0.35); cy = CONTENT_CY - 6
    if k < 1:                                              # fasa 1: goji + zeaxanthin
        o = 1 - eio(k)
        pop_img(L, goji_sp(200), 220, cy, eob((t - A["goji_in"] - 0.1) / 0.35) * o)
        pop_img(L, chip_sp("zeaxanthin", 50, BG, ACCENT, padx=32, pady=16, outline=ACCENT), 560, cy, eob((t - A["zea"]) / 0.3) * o)
    if k > 0:                                              # fasa 2: "1 kajian" + rajah mata
        a = eio(k)
        L.alpha_composite(fade(text_sp("1", 150, ACCENT), a), (40, 100))
        L.alpha_composite(fade(text_sp("kajian", 40, TEXT), a), (118, 176))
        L.alpha_composite(fade(text_sp("suplemen goji harian", 28, (165, 185, 205), heavy=False), a), (44, 252))
        e = eye_sp(); s = 0.56 * eob(k); ox, oy = 420, 84
        q = e.resize((max(1, int(e.width * s)), max(1, int(e.height * s))), Image.BILINEAR); L.alpha_composite(fade(q, a), (ox, oy))
        ex = ox + (285 + 150) * 0.56; ey = oy + 210 * 0.56                                   # kedudukan makula
        if t >= A["macula"]:
            up = t - A["macula"]; lay = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            for off in (0, 0.45):
                if up >= off:
                    p = ((up - off) % 0.9) / 0.9; r = 10 + 28 * p; d.ellipse((ex - r, ey - r, ex + r, ey + r), outline=YELLOW + (int(255 * (1 - p)),), width=3)
            L.alpha_composite(lay)
            lab = chip_sp("makula", 34, BG, YELLOW, padx=22, pady=10, outline=YELLOW); lx, ly = ex + 52, oy + 62
            draw_path(L, [(ex, ey - 8), (lx, ly + lab.height // 2 + 6)], clamp(up / 0.2), YELLOW, 3)
            pop_img(L, lab, lx, ly, eob((up - 0.05) / 0.3))
        for n, ln in enumerate(("Rajah ringkas,", "untuk pendidikan sahaja")):
            c_ = text_sp(ln, 24, (170, 190, 210), heavy=False); L.alpha_composite(fade(c_, a), (CARD_W - 30 - c_.width, 296 + n * 28))
    return L

def layer_avo(t):
    L = chart_card("Avokado hijau pun ada lutein", source="Klikdokter Indonesia")
    cx, cy = 250, CONTENT_CY - 4
    pop = eob((t - A["avo_in"] - 0.05) / 0.35)
    av = avocado_sp(235); half = av.width // 2
    sp = clamp((t - A["avo_split"]) / 0.35); gap = 36 * eo3(sp)
    if pop > 0.02:
        lh = av.crop((0, 0, half, av.height)); rh = av.crop((half, 0, av.width, av.height))
        if sp > 0:
            glow = soft_dot(30, YELLOW); gw_ = glow.resize((int(glow.width * (1 + 1.0 * sp)), int(glow.height * (1 + 3.0 * sp))), Image.BILINEAR)
            L.alpha_composite(fade(gw_, 0.3), (int(cx - gw_.width / 2), int(cy - gw_.height / 2)))
        for h_, dx, rot in ((lh, -gap, 5 * sp), (rh, gap, -5 * sp)):
            q = h_.resize((max(1, int(h_.width * pop)), max(1, int(h_.height * pop))), Image.BILINEAR).rotate(rot, resample=Image.BICUBIC, expand=True)
            L.alpha_composite(q, (int(cx + dx - (q.width if h_ is lh else 0)), int(cy - q.height / 2)))
    if t >= A["avo_split"] + 0.1:
        up = t - A["avo_split"] - 0.1
        for n in range(24):
            ph = (n * 0.173 + up * 0.7) % 1.0; ang = math.radians(-60 + 120 * ((n * 0.618) % 1.0))
            dist = 30 + 250 * ph; x = cx + math.cos(ang) * dist; y = cy + math.sin(ang) * dist * 0.6
            d_ = soft_dot((8, 10, 13)[n % 3], YELLOW)
            if x < CARD_W - 60: L.alpha_composite(fade(d_, clamp(ph / 0.1) * clamp((1 - ph) / 0.25)), (int(x - d_.width / 2), int(y - d_.height / 2)))
    pop_img(L, chip_sp("lutein", 52, BG, YELLOW, padx=36, pady=16, outline=YELLOW), CARD_W - 190, cy, eob((t - A["lutein"]) / 0.35))
    return L

PROD = Image.open("assets/product_box.png").convert("RGB")
HOLO = (234, 38)                                           # kedudukan sticker pada product_box.png (selepas flip)

def prod_window(p, aspect):
    w0, h0 = PROD.size; x0, y0, ww, hh = 0, 0, w0, h0
    if w0 / h0 > aspect: ww = h0 * aspect; x0 = (w0 - ww) / 2
    else: hh = w0 / aspect; y0 = (h0 - hh) / 2
    w1 = 330; h1 = w1 / aspect; x1 = clamp(HOLO[0] - w1 / 2, 0, w0 - w1); y1 = clamp(HOLO[1] - h1 / 2, 0, h0 - h1)
    p = eio(p)
    return (x0 + (x1 - x0) * p, y0 + (y1 - y0) * p, x0 + (x1 - x0) * p + ww + (w1 - ww) * p, y0 + (y1 - y0) * p + hh + (h1 - hh) * p)

def rounded_img(im, r):
    m = SS(im.width, im.height, lambda d, k: d.rounded_rectangle((0, 0, im.width * k - 1, im.height * k - 1), r * k, fill=(255, 255, 255, 255)))
    out = im.convert("RGBA"); out.putalpha(m.getchannel("A")); return out

def layer_prod(t):
    L = chart_card("Berdaftar dengan MAL", footer=None)
    iw, ih = 760, 236
    p = clamp((t - A["prod_in"]) / (A["prod_zoom_end"] - A["prod_in"]))
    im = PROD.resize((iw, ih), Image.LANCZOS, box=prod_window(p, iw / ih))
    L.alpha_composite(rounded_img(im, 20), (30, 94))
    u = t - A["trad"]
    if u > 0:
        tsp = text_sp("Digunakan secara tradisional untuk kesihatan mata", 28, (170, 190, 210), heavy=False)
        L.alpha_composite(fade(tsp, clamp(u / 0.3)), ((CARD_W - tsp.width) // 2, CARD_H - 52))
    return L

def render(t):
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0)); used = False
    if t >= TOTAL:                                           # end card
        return end_card(t), True
    used |= hook_icons(cv, t)
    used |= scene_split(cv, t)
    for lay_fn, t_in, t_out in ((layer_lobak, A["lobak_in"], A["lobak_out"]), (layer_goji, A["goji_in"], A["goji_out"]),
                                (layer_avo, A["avo_in"], A["avo_out"])):
        xf = card_xform(t, t_in, t_out)
        if xf: s, a = xf; place(cv, lay_fn(t), CX, CARD_CY, s, a); used = True
    xf = card_xform(t, A["prod_in"], A["prod_out"])
    if xf:
        s, a = xf; place(cv, layer_prod(t), CX, CARD_CY, s, a); used = True
        u = t - A["mal"]
        if 0 <= u and t < A["prod_out"] + 0.2:                # nombor kunci
            place(cv, chip_sp("MAL22076147T", 56, BG, ACCENT, padx=38, pady=14, outline=ACCENT), CX, 812, eob(u / 0.32), clamp((A["prod_out"] + 0.2 - t) / 0.2))
    slam_hook = plate_sp(["KENAPA", "WARNA?"], 92, (TEXT, ACCENT))
    slam_kar = plate_sp(["KAROTENOID"], 80, (TEXT,))
    slam_pig = plate_sp(["PIGMEN"], 120, (ACCENT,))
    used |= draw_slam(cv, t, 0.0, 1.55, slam_hook, CX, 335)
    used |= draw_slam(cv, t, A["karot"], A["split_out"], slam_kar, CX, 320)
    used |= draw_slam(cv, t, A["pig_in"], A["pig_out"], slam_pig, CX, 320)
    return cv, used

def end_card(t):
    u = t - TOTAL
    cv = cached(("endbg",), _grad).copy()
    a = clamp(u / 0.25)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ph = rounded_img(PROD.resize((800, int(800 * PROD.height / PROD.width)), Image.LANCZOS), 24)
    place(lay, ph, CX, 520 + 20 * (1 - eo3(u / 0.5)), 1, 1)
    place(lay, text_sp("DS Pharma Eye Care", 76, TEXT), CX, 800, 1, 1)
    place(lay, text_sp("NO. PENDAFTARAN MAL", 26, (165, 185, 205), heavy=False), CX, 905, 1, 1)
    place(lay, text_sp("MAL22076147T", 78, ACCENT), CX, 972, 1, 1)
    place(lay, text_sp("Digunakan secara tradisional", 40, TEXT, heavy=False), CX, 1090, 1, 1)
    place(lay, text_sp("untuk kesihatan mata.", 40, TEXT, heavy=False), CX, 1146, 1, 1)
    place(lay, text_sp("Bukan ganti pemeriksaan mata.", 32, (165, 185, 205), heavy=False), CX, 1240, 1, 1)
    place(lay, chip_sp("Dapatkan di profile / beg kuning", 36, ACCENT, BG, padx=36, pady=16), CX, 1380, 1, 1)
    cv.alpha_composite(fade(lay, a))
    return fade(cv, a)

def _grad():
    import numpy as np
    y = np.linspace(0, 1, H)[:, None, None]; c0 = np.array([16, 31, 50]); c1 = np.array([9, 17, 29])
    arr = (c0[None, None, :] * (1 - y) + c1[None, None, :] * y).repeat(W, 1)
    return Image.fromarray(arr.astype("uint8"), "RGB").convert("RGBA")

# ================= subtitle =================
def build_subs():
    cues = []
    for si, (a, b, g) in enumerate(segs):
        toks = [(words[i]["t"], words[i]["s"], words[i]["e"]) for i in g]
        chunk = []
        def flush():
            tx = " ".join(c[0] for c in chunk if c[0])
            if tx:
                last = max(c[2] for c in chunk)
                cues.append([offs[si] + chunk[0][1] - a, offs[si] + last - a, tx])
            chunk.clear()
        for tk in toks:
            chunk.append(tk); tx = " ".join(c[0] for c in chunk if c[0])
            if tk[0] and (tk[0][-1] in ".?!," or sum(1 for c in chunk if c[0]) >= 4 or len(tx) >= 24): flush()
        flush()
    for k in range(len(cues) - 1):
        if cues[k + 1][0] - cues[k][1] < 0.35: cues[k][1] = cues[k + 1][0]
        cues[k][1] = min(cues[k][1], cues[k + 1][0])
    cues[-1][1] = min(cues[-1][1] + 0.2, TOTAL)
    def ts(t):
        ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000); return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(f"work/{OUT}.srt", "w") as f:
        for k, (t0, t1, tx) in enumerate(cues, 1): f.write(f"{k}\n{ts(t0)} --> {ts(t1)}\n{tx}\n\n")
    def ats(t): h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02}:{s:05.2f}"
    with open(f"work/{OUT}.ass", "w") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
                "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
                "Style: Default,Inter,68,&H00FFF6ED,&H00FFF6ED,&H00501F10,&H80000000,1,0,0,0,100,100,0,0,1,6,1,2,90,170,430,1\n\n"
                "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
        for t0, t1, tx in cues:
            tx = tx.replace("zeaxanthin", "{\\c&HC0D566&}zeaxanthin{\\c&HFFF6ED&}")      # teal #14B8A6
            f.write(f"Dialogue: 0,{ats(t0)},{ats(t1)},Default,,0,0,0,,{{\\fad(40,0)\\fscx88\\fscy88\\t(0,120,\\fscx100\\fscy100)}}{tx}\n")
    return len(cues)

# ================= audio (dijana dengan kod) =================
SR = 48000

def make_audio():
    """Bed: denyut bersih + pad lembut. Ticks: bunyi tonal pendek pada saat data didedahkan. Tiada muzik/suara berbayar."""
    import numpy as np, wave
    n = int(ALL * SR); t = np.arange(n) / SR
    bed = np.zeros(n)
    bpm = 96; beat = 60 / bpm
    for b in np.arange(0, ALL, beat):                     # denyut: thump sinus 55Hz yang reput
        i = int(b * SR); L = int(0.28 * SR); tt = np.arange(min(L, n - i)) / SR
        if len(tt): bed[i:i + len(tt)] += np.sin(2 * np.pi * (55 + 25 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 11) * 0.9
    pad = sum(np.sin(2 * np.pi * f * t + ph) for f, ph in ((110, 0), (164.81, 1), (220, 2), (329.63, 3), (246.94, 4)))
    bed += pad * (0.07 + 0.03 * np.sin(2 * np.pi * t / 8)) * 0.6
    env = np.minimum(1, t / 1.5) * np.minimum(1, (ALL - t) / 2.0)
    bed *= env; bed = bed / np.max(np.abs(bed)) * 0.16     # puncak bed ~ -16 dBFS (kemudian di-duck bawah ucapan)
    ticks = np.zeros(n)
    ev = [(A["karot"], 0), (A["pigmen"], 1), (A["arrow"] + 0.5, 1), (A["vitA"], 1), (A["chip1"], 0), (A["chip2"], 0),
          (A["zea"], 1), (A["eye"] + 0.25, 0), (A["macula"], 1), (A["avo_split"] + 0.1, 0), (A["lutein"], 1),
          (A["pig_in"], 1), (A["mal"], 1), (TOTAL + 0.05, 1)]
    for te, hi in ev:
        i = int(te * SR); L = int(0.16 * SR)
        if i + L >= n: continue
        tt = np.arange(L) / SR; f = 1318.5 if hi else 987.8
        ticks[i:i + L] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 28) * (1 - np.exp(-tt * 900)) * 0.16
    for nm, x in (("bed", bed), ("ticks", ticks)):
        st = np.stack([x, x], 1); pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
        with wave.open(f"work/{OUT}_{nm}.wav", "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ================= ffmpeg =================
def build_filter():
    vf, af = [], []
    for i, (a, b, g) in enumerate(segs):
        z0, z1, pw = SEGZ[i]; n = max(int(round((b - a) * FPS)), 1)
        z = f"{z0}+({z1}-{z0})*on/{n}"
        for wi in pw:
            f0 = int(round((words[wi]["s"] - a) * FPS)); f1, f2 = f0 + 4, f0 + 4 + 16
            z += f"+0.12*(between(on,{f0},{f1})*(on-{f0})/4+between(on,{f1 + 1},{f2})*(1-(on-{f1})/16))"
        vf.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,fps={FPS},scale=2160:3840:flags=bicubic,"
                  f"zoompan=z='{z}':x='{FX}*(iw-iw/zoom)':y='{FY}*(ih-ih/zoom)':d=1:s=1080x1920:fps={FPS},setsar=1[v{i}]")
        af.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,aresample=48000[a{i}]")
    last = "v0"
    for i in range(1, len(segs)):
        vf.append(f"[{last}][v{i}]xfade=transition=fade:duration={xfs[i]}:offset={offs[i]:.3f}[x{i}]"); last = f"x{i}"
    # grade Data Story: sejuk/biru-navy lembut + vignette halus supaya serasi dengan #101f32
    vf.append(f"[{last}]eq=saturation=0.94:contrast=1.04:brightness=-0.01,colorbalance=bs=0.05:bm=0.03:rs=-0.02,vignette=angle=PI/7,"
              f"tpad=stop_mode=clone:stop_duration={END}[vp]")
    last = "a0"
    for i in range(1, len(segs)):
        af.append(f"[{last}][a{i}]acrossfade=d={max(xfs[i], 0.03)}:c1=tri:c2=tri[y{i}]"); last = f"y{i}"
    af.append(f"[{last}]apad=pad_dur={END},aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[sp1][sp2]")
    af.append("[2:a]aformat=sample_rates=48000:channel_layouts=stereo[bed]")
    af.append("[bed][sp2]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=300[bd]")      # bed ditekan bawah ucapan
    af.append("[3:a]aformat=sample_rates=48000:channel_layouts=stereo[tk]")
    af.append("[sp1][bd][tk]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.95[am]")
    return ";".join(vf + af) + f";[vp][1:v]overlay=format=auto[o];[o]ass=work/{OUT}.ass[vout]"

def do_render():
    n = build_subs(); make_audio(); out = f"work/{OUT}.mp4"
    print(f"{len(segs)} segmen, ucapan {TOTAL:.1f}s + end card {END}s = {ALL:.1f}s, {n} cue", flush=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", VID, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", f"work/{OUT}_bed.wav", "-i", f"work/{OUT}_ticks.wav",
           "-filter_complex", build_filter(), "-map", "[vout]", "-map", "[am]", "-t", f"{ALL:.3f}",
           "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    blank = bytes(W * H * 4); N = int(math.ceil(ALL * FPS))
    for f in range(N):
        im, used = render(f / FPS)
        pr.stdin.write(im.tobytes() if used else blank)
        if f % 150 == 0: print(f"overlay {f}/{N}", flush=True)
    pr.stdin.close(); rc = pr.wait()
    if rc: sys.exit(rc)
    print(out)

def do_stills(ts_):
    for s in ts_:
        t = float(s); im, _ = render(t); p = f"work/ov_{s}.png"; im.save(p)
        o = f"work/still_{s}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{min(t, 75):.2f}", "-i", f"work/{NAME}_edit.mp4", "-i", p, "-filter_complex",
                        "[0:v][1:v]overlay,scale=540:-1", "-frames:v", "1", o], check=True)
        print(o)

if __name__ == "__main__":
    os.makedirs("work", exist_ok=True)
    if sys.argv[1] == "render": do_render()
    else: build_subs(); do_stills(sys.argv[2].split(","))
