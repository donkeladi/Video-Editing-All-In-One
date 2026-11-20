#!/usr/bin/env python3
"""Eyebright (Skrip 7): jump-cut + zoom + motion graphic + subtitle + end card.

Guna:
  eyebright_motion.py render                  -> work/eyebright_v2.mp4 (belum normalize)
  eyebright_motion.py stills 1.0,9.5,20       -> work/still_<t>.png (semakan layout; overlay atas frame edit lama)

Perlu: work/eyebright.json (faster-whisper word timestamps), work/eyebright_corr.json,
       assets/product_box.png (still kotak produk), input/eyebright.mov
Skrip ini khusus untuk video Eyebright; ubah ANCHOR/ZOOM di bawah untuk video lain.
"""
import json, subprocess, sys, os, math, random
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
VID, NAME = "input/eyebright.mov", "eyebright"
GAP, PAD_IN, PAD_OUT, XF, XF_HARD = 0.30, 0.12, 0.20, 0.12, 0.034
FX, FY = 0.55, 0.35
END = 2.5
FORCE_BREAKS = {101}         # sebelum "DS Pharma" -> hard cut
HARD = {101}

# ---------- warna ----------
ORANGE, RED, TEAL = (255, 138, 31), (232, 52, 74), (20, 184, 166)
YELLOW, GOLD, NAVY = (255, 210, 31), (255, 197, 61), (14, 22, 40)
WHITE = (255, 255, 255)

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

def text_sp(txt, size, fill=WHITE, heavy=True, stroke=0, sfill=(0, 0, 0)):
    def mk():
        f = font(size, heavy); bb = f.getbbox(txt, stroke_width=stroke); p = 6
        im = Image.new("RGBA", (bb[2] - bb[0] + 2 * p + 2 * stroke, bb[3] - bb[1] + 2 * p + 2 * stroke), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((p + stroke - bb[0], p + stroke - bb[1]), txt, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=sfill + (255,))
        return im
    return cached(("t", txt, size, fill, heavy, stroke), mk)

def plate_sp(lines, size, bg, fg, padx=56, pady=28, r=38):
    def mk():
        f = font(size); lh = int(size * 1.12)
        ws = [f.getlength(l) for l in lines]; w = int(max(ws) + 2 * padx); h = int(lh * len(lines) + 2 * pady)
        k = 2; im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), r * k, fill=bg + (255,))
        d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), r * k, outline=(0, 0, 0, 255), width=6 * k)
        f2 = font(size * k)
        for n, l in enumerate(lines):
            bb = f2.getbbox(l); d.text(((w * k - (bb[2] - bb[0])) / 2 - bb[0], (pady + n * lh) * k + (lh * k - (bb[3] - bb[1])) / 2 - bb[1] - size * 0.02 * k), l, font=f2, fill=fg + (255,))
        return im.resize((w, h), Image.LANCZOS)
    return cached(("p", tuple(lines), size, bg, fg), mk)

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

def card_bg(w, h, accent):
    def mk():
        return SS(w, h, lambda d, k: (d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), 40 * k, fill=NAVY + (236,)),
                                      d.rounded_rectangle((2 * k, 2 * k, w * k - 3 * k, h * k - 3 * k), 38 * k, outline=accent + (255,), width=4 * k)))
    return cached(("cb", w, h, accent), mk).copy()

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
CARD_W, CARD_H, CARD_CY = 900, 380, 1075

def card_xform(t, t_in, t_out):
    u = t - t_in
    if u < 0 or t > t_out + 0.25: return None
    a = clamp(u / 0.15) * clamp((t_out + 0.25 - t) / 0.25)
    s = (0.82 + 0.18 * eob(u / 0.32)) * (1 - 0.04 * (1 - clamp((t_out + 0.25 - t) / 0.25)))
    return s, a

def draw_slam(cv, t, t0, t1, sp, cx, cy, rot=-3.0):
    u = t - t0
    if u < 0 or t > t1: return False
    s = 1 + 1.15 * (1 - eo3(u / 0.14))
    sh = max(0.0, 1 - u / 0.4)
    dx, dy = math.sin(u * 95) * 14 * sh, math.cos(u * 80) * 10 * sh
    place(cv, sp, cx + dx, cy + dy, s, clamp(u / 0.04) * clamp((t1 - t) / 0.14), rot)
    return True

def src_chip(cv, t, t_in, t_out, txt):
    u = t - t_in
    if u < 0 or t > t_out + 0.2: return
    sp = chip_sp(txt, 30, (10, 14, 26), (225, 232, 245), padx=26, pady=12, outline=(120, 135, 160), bga=215, heavy=False)
    blit(cv, sp, (W - sp.width) / 2, 1550 + 22 * (1 - eo3(u / 0.3)), clamp(u / 0.25) * clamp((t_out + 0.2 - t) / 0.2))

def hook_icons(cv, t):
    used = False
    for t0, sp_fn, cx, rot in ((A["carrot"], carrot_sp, 190, 28), (A["goji"], goji_sp, 880, -12)):
        u = t - t0
        if u < 0 or t > A["hook_out"] + 0.25: continue
        out = clamp((A["hook_out"] + 0.25 - t) / 0.25)
        s = eob(u / 0.35) * (1 + 0.035 * math.sin(u * 5)) * out
        if s > 0.02: place(cv, sp_fn(250), cx, 1700, s, 1.0, rot); used = True
    return used

def scene_split(cv, t):
    if t < A["split_in"] or t > A["split_out"] + 0.4: return False
    u = t - A["split_in"]
    top = 1920 - (1920 - 880) * eio(u / 0.38)
    top += (1920 - 880) * eio((t - A["split_out"]) / 0.4)
    panel = cached(("panel",), lambda: SS(W, 1040, lambda d, k: (d.rectangle((0, 0, W * k, 1040 * k), fill=NAVY + (240,)),
                                                                 d.rectangle((0, 0, W * k // 2, 8 * k), fill=ORANGE + (255,)),
                                                                 d.rectangle((W * k // 2, 0, W * k, 8 * k), fill=RED + (255,))), 1))
    blit(cv, panel, 0, top)
    dy = top - 880
    place(cv, carrot_sp(180), 235, 1010 + dy, eob((u - 0.15) / 0.35), 1, 20)
    place(cv, goji_sp(180), 845, 1010 + dy, eob((u - 0.25) / 0.35), 1, -10)
    c = (540, 1100 + dy)
    if t >= A["pigmen"]:
        up = t - A["pigmen"]
        for side, ph, off, r in PARTS:
            p = ((up * 0.85 + ph) % 1.0)
            sx, sy = (235, 1010 + dy) if side == 0 else (845, 1010 + dy)
            cx_, cy_ = (sx + c[0]) / 2, (sy + c[1]) / 2 + off
            x = (1 - p) ** 2 * sx + 2 * (1 - p) * p * cx_ + p * p * c[0]
            y = (1 - p) ** 2 * sy + 2 * (1 - p) * p * cy_ + p * p * c[1]
            al = clamp(p / 0.12) * clamp((1 - p) / 0.15)
            place(cv, soft_dot(r, ORANGE if side == 0 else RED), x, y, 1, al * clamp(up / 0.2))
        pulse = 1 + 0.045 * math.sin(up * 7)
        ring = cached(("ring",), lambda: SS(250, 250, lambda d, k: (d.ellipse((6 * k, 6 * k, 244 * k, 244 * k), fill=(255, 255, 255, 38)),
                                                                     d.arc((6 * k, 6 * k, 244 * k, 244 * k), 90, 270, fill=ORANGE + (255,), width=10 * k),
                                                                     d.arc((6 * k, 6 * k, 244 * k, 244 * k), 270, 450, fill=RED + (255,), width=10 * k))))
        place(cv, ring, c[0], c[1], eob(up / 0.3) * pulse)
        place(cv, text_sp("pigmen", 50, WHITE), c[0], c[1], eob((up - 0.1) / 0.3))
    return True

def layer_lobak(t):
    L = card_bg(CARD_W, CARD_H, ORANGE)
    ic = carrot_sp(120); fa, fb = font(44), font(48)
    tb = text_sp("beta-karotin", 44, ORANGE); pill = chip_sp("vitamin A", 48, GOLD, (20, 20, 20), padx=30, pady=14)
    gw = 120 + 18 + tb.width + 40 + 120 + 36 + pill.width
    x = (CARD_W - gw) // 2; cy = 150
    L.alpha_composite(ic.rotate(25, resample=Image.BICUBIC, expand=True), (x - 10, cy - 70)); x += 138
    L.alpha_composite(tb, (x, cy - tb.height // 2)); x += tb.width + 40
    p = eio((t - A["arrow"]) / 0.55)                       # anak panah dilukis
    if p > 0:
        lay = Image.new("RGBA", (120 * 3, 60 * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        xe = 10 + 100 * p
        d.line((10 * 3, 30 * 3, xe * 3, 30 * 3), fill=WHITE + (255,), width=9 * 3)
        if p > 0.82:
            hp = clamp((p - 0.82) / 0.18); hx = 112
            d.line((hx * 3, 30 * 3, (hx - 22 * hp) * 3, (30 - 20 * hp) * 3), fill=WHITE + (255,), width=9 * 3)
            d.line((hx * 3, 30 * 3, (hx - 22 * hp) * 3, (30 + 20 * hp) * 3), fill=WHITE + (255,), width=9 * 3)
        L.alpha_composite(lay.resize((120, 60), Image.LANCZOS), (x, cy - 30))
    x += 120 + 36
    s = eob((t - A["vitA"]) / 0.35)
    if s > 0.02:
        q = pill.resize((max(1, int(pill.width * s)), max(1, int(pill.height * s))), Image.BILINEAR)
        L.alpha_composite(q, (x + (pill.width - q.width) // 2, cy - q.height // 2))
    cs = [("mata", A["chip1"], TEAL), ("daya tahan badan", A["chip2"], ORANGE)]
    sps = [chip_sp(tx, 38, WHITE, (20, 20, 30), padx=28, pady=14, outline=col) for tx, _, col in cs]
    tw = sum(s_.width for s_ in sps) + 30; x = (CARD_W - tw) // 2
    for sp_, (tx, t0, col) in zip(sps, cs):
        s = eob((t - t0) / 0.3)
        if s > 0.02:
            q = sp_.resize((max(1, int(sp_.width * s)), max(1, int(sp_.height * s))), Image.BILINEAR)
            L.alpha_composite(q, (x + (sp_.width - q.width) // 2, 285 - q.height // 2))
        x += sp_.width + 30
    return L

def layer_goji(t):
    L = card_bg(CARD_W, CARD_H, TEAL)
    k = clamp((t - A["eye"]) / 0.35)
    if k < 1:                                              # ikon goji + chip zeaxanthin
        o = 1 - eio(k)
        g = goji_sp(240); s = eob((t - A["goji_in"] - 0.1) / 0.35) * o
        if s > 0.02:
            q = g.resize((max(1, int(g.width * s)), max(1, int(g.height * s))), Image.BILINEAR); L.alpha_composite(q, (240 - q.width // 2, CARD_H // 2 - q.height // 2))
        zs = eob((t - A["zea"]) / 0.3) * o
        if zs > 0.02:
            c = chip_sp("zeaxanthin", 54, TEAL, (255, 255, 255), padx=36, pady=18)
            q = c.resize((max(1, int(c.width * zs)), max(1, int(c.height * zs))), Image.BILINEAR); L.alpha_composite(q, (610 - q.width // 2, CARD_H // 2 - q.height // 2))
    if k > 0:                                              # rajah mata ringkas
        e = eye_sp(); s = 0.88 * eob(k)
        q = e.resize((max(1, int(e.width * s)), max(1, int(e.height * s))), Image.BILINEAR); q = fade(q, k)
        L.alpha_composite(q, (CARD_W // 2 - q.width // 2 - 30, 14))
        ex = CARD_W // 2 - 30 - e.width * s / 2 + (285 + 150) * s; ey = 14 + 210 * s     # kedudukan makula
        if t >= A["macula"]:
            up = t - A["macula"]
            lay = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            for off in (0, 0.45):
                p = ((up - off) % 0.9) / 0.9 if up >= off else None
                if p is not None:
                    r = 14 + 40 * p; d.ellipse((ex - r, ey - r, ex + r, ey + r), outline=YELLOW + (int(255 * (1 - p)),), width=4)
            L.alpha_composite(lay)
            lab = chip_sp("makula", 40, YELLOW, (20, 20, 20), padx=28, pady=12); ls = eob(up / 0.3)
            lx, ly = ex + 30, ey - 120
            d2 = ImageDraw.Draw(L); d2.line((ex, ey - 12, lx + 20, ly + lab.height), fill=YELLOW + (255,), width=4)
            q = lab.resize((max(1, int(lab.width * ls)), max(1, int(lab.height * ls))), Image.BILINEAR)
            L.alpha_composite(q, (int(lx + 20 - q.width / 2), int(ly + lab.height / 2 - q.height / 2)))
        cap = text_sp("Rajah ringkas, untuk pendidikan sahaja", 28, (200, 210, 225), heavy=False)
        L.alpha_composite(fade(cap, k), ((CARD_W - cap.width) // 2, CARD_H - cap.height - 12))
    return L

def layer_avo(t):
    L = card_bg(CARD_W, CARD_H, YELLOW)
    cx, cy = CARD_W // 2 - 90, CARD_H // 2 - 10
    pop = eob((t - A["avo_in"] - 0.05) / 0.35)
    av = avocado_sp(300); half = av.width // 2
    sp = clamp((t - A["avo_split"]) / 0.35); gap = 46 * eo3(sp)
    if pop > 0.02:
        s = pop
        lh = av.crop((0, 0, half, av.height)); rh = av.crop((half, 0, av.width, av.height))
        if sp > 0:                                         # cahaya kuning di celah
            glow = soft_dot(34, YELLOW); gw_ = glow.resize((int(glow.width * (1 + 1.2 * sp)), int(glow.height * (1 + 3.2 * sp))), Image.BILINEAR)
            L.alpha_composite(fade(gw_, 0.35), (int(cx - gw_.width / 2), int(cy - gw_.height / 2)))
        for h_, dx, rot in ((lh, -gap, 5 * sp), (rh, gap, -5 * sp)):
            q = h_.resize((max(1, int(h_.width * s)), max(1, int(h_.height * s))), Image.BILINEAR).rotate(rot, resample=Image.BICUBIC, expand=True)
            px = cx + dx - (q.width if h_ is lh else 0) + (0 if h_ is lh else 0)
            L.alpha_composite(q, (int(cx + dx - (q.width if h_ is lh else 0)), int(cy - q.height / 2)))
    if t >= A["avo_split"] + 0.1:
        up = t - A["avo_split"] - 0.1
        for n in range(24):
            ph = (n * 0.173 + up * 0.7) % 1.0; ang = math.radians(-70 + 140 * ((n * 0.618) % 1.0))
            dist = 40 + 260 * ph; x = cx + math.cos(ang) * dist * 1.1; y = cy + math.sin(ang) * dist * 0.75
            d_ = soft_dot((10, 13, 17)[n % 3], YELLOW); L.alpha_composite(fade(d_, clamp(ph / 0.1) * clamp((1 - ph) / 0.25)), (int(x - d_.width / 2), int(y - d_.height / 2)))
    ls = eob((t - A["lutein"]) / 0.35)
    if ls > 0.02:
        lab = chip_sp("lutein", 56, YELLOW, (20, 20, 20), padx=40, pady=18)
        q = lab.resize((max(1, int(lab.width * ls)), max(1, int(lab.height * ls))), Image.BILINEAR)
        L.alpha_composite(q, (int(CARD_W - 190 - q.width / 2), int(CARD_H / 2 - q.height / 2)))
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
    L = card_bg(CARD_W, CARD_H, GOLD)
    iw, ih = 840, 340
    p = clamp((t - A["prod_in"]) / (A["prod_zoom_end"] - A["prod_in"]))
    im = PROD.resize((iw, ih), Image.LANCZOS, box=prod_window(p, iw / ih))
    L.alpha_composite(rounded_img(im, 26), (30, 20))
    return L

def render(t):
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0)); used = False
    if t >= TOTAL:                                           # end card
        return end_card(t), True
    used |= hook_icons(cv, t)
    used |= scene_split(cv, t)
    for lay_fn, t_in, t_out, src in ((layer_lobak, A["lobak_in"], A["lobak_out"], "Sumber: Klarity Health; Kemenkes Indonesia"),
                                     (layer_goji, A["goji_in"], A["goji_out"], "Sumber: Nutrition Advance; Healthline"),
                                     (layer_avo, A["avo_in"], A["avo_out"], "Sumber: Klikdokter Indonesia")):
        xf = card_xform(t, t_in, t_out)
        if xf:
            s, a = xf; L = lay_fn(t); place(cv, L, W / 2, CARD_CY, s, a); src_chip(cv, t, t_in + 0.25, t_out, src); used = True
    xf = card_xform(t, A["prod_in"], A["prod_out"])
    if xf:
        s, a = xf; place(cv, layer_prod(t), W / 2, CARD_CY, s, a); used = True
        for t0, txt, size, bg, fg, y in ((A["mal"], "MAL22076147T", 58, YELLOW, (20, 20, 20), 815),):
            u = t - t0
            if 0 <= u and t < A["prod_out"] + 0.2:
                place(cv, chip_sp(txt, size, bg, fg, padx=40, pady=16), W / 2, y, eob(u / 0.32), clamp((A["prod_out"] + 0.2 - t) / 0.2))
        u = t - A["trad"]
        if 0 <= u and t < A["prod_out"] + 0.2:
            c = chip_sp("Digunakan secara tradisional untuk kesihatan mata", 33, (10, 90, 82), WHITE, padx=30, pady=14, heavy=False)
            blit(cv, c, (W - c.width) / 2, 1550 + 22 * (1 - eo3(u / 0.3)), clamp(u / 0.25) * clamp((A["prod_out"] + 0.2 - t) / 0.2))
    slam_hook = plate_sp(["KENAPA", "WARNA?"], 118, YELLOW, (20, 20, 20))
    slam_kar = plate_sp(["KAROTENOID"], 104, ORANGE, WHITE)
    slam_pig = plate_sp(["PIGMEN"], 150, TEAL, WHITE)
    used |= draw_slam(cv, t, 0.0, 1.55, slam_hook, W / 2, 285)
    used |= draw_slam(cv, t, A["karot"], A["split_out"], slam_kar, W / 2, 285, -2.5)
    used |= draw_slam(cv, t, A["pig_in"], A["pig_out"], slam_pig, W / 2, 285, 2.5)
    return cv, used

def end_card(t):
    u = t - TOTAL
    bg = cached(("endbg",), lambda: _grad())
    cv = bg.copy()
    a = clamp(u / 0.25)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ph = rounded_img(PROD.resize((900, int(900 * PROD.height / PROD.width)), Image.LANCZOS), 30)
    place(lay, ph, W / 2, 560 + 20 * (1 - eo3(u / 0.5)), 1, 1)
    place(lay, text_sp("DS Pharma Eye Care", 78, WHITE), W / 2, 850, 1, 1)
    place(lay, chip_sp("MAL22076147T", 56, YELLOW, (20, 20, 20), padx=40, pady=16), W / 2, 990, 1, 1)
    place(lay, text_sp("Digunakan secara tradisional", 42, WHITE, heavy=False), W / 2, 1110, 1, 1)
    place(lay, text_sp("untuk kesihatan mata.", 42, WHITE, heavy=False), W / 2, 1170, 1, 1)
    place(lay, text_sp("Bukan ganti pemeriksaan mata.", 34, (190, 205, 225), heavy=False), W / 2, 1270, 1, 1)
    place(lay, chip_sp("Dapatkan di profile / beg kuning", 38, TEAL, WHITE, padx=36, pady=16), W / 2, 1450, 1, 1)
    cv.alpha_composite(fade(lay, a))
    return fade(cv, a)

def _grad():
    import numpy as np
    y = np.linspace(0, 1, H)[:, None]; c0 = np.array([8, 60, 70]); c1 = np.array([14, 22, 40])
    arr = (c0 * (1 - y) + c1 * y)[:, None, :].repeat(W, 1) if False else (c0[None, None, :] * (1 - y[:, :, None]) + c1[None, None, :] * y[:, :, None]).repeat(W, 1)
    im = Image.fromarray(arr.astype("uint8"), "RGB").convert("RGBA"); return im

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
            if tk[0] and (tk[0][-1] in ".?!," or sum(1 for c in chunk if c[0]) >= 4 or len(tx) >= 26): flush()
        flush()
    for k in range(len(cues) - 1):
        if cues[k + 1][0] - cues[k][1] < 0.35: cues[k][1] = cues[k + 1][0]
        cues[k][1] = min(cues[k][1], cues[k + 1][0])
    cues[-1][1] = min(cues[-1][1] + 0.2, TOTAL)
    def ts(t):
        ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000); return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(f"work/{NAME}.srt", "w") as f:
        for k, (t0, t1, tx) in enumerate(cues, 1): f.write(f"{k}\n{ts(t0)} --> {ts(t1)}\n{tx}\n\n")
    def ats(t): h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02}:{s:05.2f}"
    with open(f"work/{NAME}.ass", "w") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
                "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
                "Style: Default,DejaVu Sans,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,70,70,430,1\n\n"
                "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
        for t0, t1, tx in cues:
            tx = tx.replace("zeaxanthin", "{\\c&HA6B814&}zeaxanthin{\\c&HFFFFFF&}")      # teal #14B8A6
            f.write(f"Dialogue: 0,{ats(t0)},{ats(t1)},Default,,0,0,0,,{{\\fad(40,0)\\fscx88\\fscy88\\t(0,120,\\fscx100\\fscy100)}}{tx}\n")
    return len(cues)

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
    vf.append(f"[{last}]tpad=stop_mode=clone:stop_duration={END}[vp]")
    last = "a0"
    for i in range(1, len(segs)):
        af.append(f"[{last}][a{i}]acrossfade=d={max(xfs[i], 0.03)}:c1=tri:c2=tri[y{i}]"); last = f"y{i}"
    af.append(f"[{last}]apad=pad_dur={END}[ap]")
    return ";".join(vf + af) + f";[vp][1:v]overlay=format=auto[o];[o]ass=work/{NAME}.ass[vout]"

def do_render():
    n = build_subs(); out = f"work/{NAME}_v2.mp4"
    print(f"{len(segs)} segmen, ucapan {TOTAL:.1f}s + end card {END}s = {ALL:.1f}s, {n} cue", flush=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", VID, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-filter_complex", build_filter(), "-map", "[vout]", "-map", "[ap]", "-t", f"{ALL:.3f}",
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
