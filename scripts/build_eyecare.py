#!/usr/bin/env python3
"""Render video Eye Care (9:16, 1080x1920, 30fps). Penyampai = footage asal (tidak diubah/disusun semula).
Guna: build_eyecare.py <video> <out_dir> [--frames a,b,c] [--workers N]
Semua grafik = overlay/kad/chip dalam kod (SVG -> PNG melalui cairosvg)."""
import sys, os, json, math, subprocess, io, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cairosvg
sys.path.insert(0, os.path.dirname(__file__))
from eyecare_timeline import *

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FD = os.path.join(ROOT, "assets/fonts/"); ID = os.path.join(ROOT, "assets/icons/")
U = "/root/.claude/uploads/59302a67-5b6f-5ed7-b47e-e009ff29d63d/"
W, H, SW, SH = 1080, 1920, 1080, 1920
SPLIT_Y = 1056            # ~55% grafik atas, ~45% penyampai bawah
WHITE = (255, 255, 255)
PUSH = 0.035; PUNCH_AMT = 0.12
FREEZE = 1728           # 57.6s: selepas perkataan terakhir, penyampai tersenyum; footage selepas ini (melangkah ke kamera) tidak digunakan

# ---------------------------------------------------------------- util
def eo_back(p, s=1.3):   # overshoot kecil
    p = min(max(p, 0), 1); c3 = s + 1
    return 1 + c3 * (p - 1) ** 3 + s * (p - 1) ** 2
def eo(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def ei(p): p = min(max(p, 0), 1); return p ** 3
@functools.lru_cache(None)
def font(name, size): return ImageFont.truetype(FD + name, size)
MONT8, MONT9, MONT7, NOTO6 = "Montserrat_800ExtraBold.ttf", "Montserrat_900Black.ttf", "Montserrat_700Bold.ttf", "NotoSans_600SemiBold.ttf"

def anim(t, t0, t1, tin=0.35, tout=0.12):
    """-> (alpha, scale) dengan entrance overshoot & exit pantas."""
    if t < t0 or t >= t1: return 0.0, 1.0
    a = eo((t - t0) / 0.10); s = 0.72 + 0.28 * eo_back((t - t0) / tin, 1.25)
    if t > t1 - tout:
        q = (t - (t1 - tout)) / tout; a *= 1 - q; s *= 1 - 0.08 * q
    return a, s

def rr(w, h, r, fill, outline=None, ow=0):
    k = 3; im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), r * k, fill=fill, outline=outline, width=ow * k)
    return im.resize((w, h), Image.LANCZOS)

@functools.lru_cache(None)
def svg_png(name, size):
    png = cairosvg.svg2png(url=ID + name + ".svg", output_width=size)
    return Image.open(io.BytesIO(png)).convert("RGBA")

# ---------------------------------------------------------------- teks
def parse(text):
    out, key = [], False
    for tok in text.replace("[", " [ ").replace("]", " ] ").split():
        if tok == "[": key = True
        elif tok == "]": key = False
        else: out.append((tok, key))
    return out

def text_sprite(text, fname, size, fill=WHITE, stroke=0, stroke_fill=PURPLE_DARK, px=14, py=8, max_w=None, boxr=16):
    words = parse(text)
    while True:
        f = font(fname, size)
        sp = f.getlength(" ")
        xs, x = [], 0
        for wd, k in words: xs.append(x); x += f.getlength(wd) + sp
        tot = x - sp
        if not max_w or tot + 2 * px <= max_w or size < 20: break
        size -= 2
    capH = -f.getbbox("H", anchor="ls")[1]; desc = f.getbbox("gpqy", anchor="ls")[3]
    m = px + stroke + 4
    w = int(tot + 2 * m); h = int(capH + desc + 2 * (py + stroke + 4))
    base = py + stroke + 4 + capH
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # kotak teal (satu-satunya bentuk penekanan)
    i = 0
    while i < len(words):
        if words[i][1]:
            j = i
            while j + 1 < len(words) and words[j + 1][1]: j += 1
            x0 = m + xs[i] - px; x1 = m + xs[j] + f.getlength(words[j][0]) + px
            box = rr(int(x1 - x0), int(capH + desc * 0.85 + 2 * py), boxr, TEAL + (255,))
            im.alpha_composite(box, (int(x0), int(base - capH - py))); i = j + 1
        else: i += 1
    d = ImageDraw.Draw(im)
    for (wd, k), x in zip(words, xs):
        if k: d.text((m + x, base), wd, font=f, fill=PURPLE_DARK + (255,), anchor="ls")
        else: d.text((m + x, base), wd, font=f, fill=fill + (255,), anchor="ls", stroke_width=stroke, stroke_fill=stroke_fill + (255,))
    return im

def stack(sprites, gap=14):
    w = max(s.width for s in sprites); h = sum(s.height for s in sprites) + gap * (len(sprites) - 1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for s in sprites: im.alpha_composite(s, ((w - s.width) // 2, y)); y += s.height + gap
    return im

# ---------------------------------------------------------------- sprites (cache)
@functools.lru_cache(None)
def caption_sprite(i): return text_sprite(CAPTIONS[i][2], MONT8, 70, stroke=9, max_w=830, px=14, py=8)
@functools.lru_cache(None)
def slam_sprite(i):
    return stack([text_sprite(l, MONT9, 160, stroke=10, px=22, py=11, max_w=800, boxr=22) for l in SLAMS[i]["lines"]], gap=6)
@functools.lru_cache(None)
def chip_sprite(text):
    t = text_sprite(text, MONT7, 46, fill=PURPLE_DARK, stroke=0, px=12, py=6, boxr=12)
    w, h = t.width + 56, t.height + 28
    im = rr(w, h, h // 2, (255, 255, 255, 245)); im.alpha_composite(t, (28, 14)); return im
@functools.lru_cache(None)
def src_sprite(text):
    f = font(NOTO6, 36); w = int(f.getlength(text)) + 64; h = 66
    im = rr(w, h, 31, (255, 255, 255, 38), (255, 255, 255, 150), 2)
    ImageDraw.Draw(im).text((32, h // 2 + 1), text, font=f, fill=(255, 255, 255, 255), anchor="lm"); return im
@functools.lru_cache(None)
def card_a_sprite():
    w, h = 860, 290; im = rr(w, h, 40, (255, 255, 255, 247))
    im.alpha_composite(svg_png("carrot", 200), (24, 45))
    t1 = text_sprite("beta-karotin", MONT8, 58, fill=PURPLE_DARK, px=8, py=6)
    ar = Image.new("RGBA", (86, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(ar)
    d.line((4, 30, 66, 30), fill=PURPLE + (255,), width=10); d.polygon([(52, 10), (82, 30), (52, 50)], fill=PURPLE + (255,))
    t2 = text_sprite("[vitamin A]", MONT8, 58, fill=PURPLE_DARK, px=14, py=6)
    im.alpha_composite(t1, (240, 52)); im.alpha_composite(ar, (242, 160)); im.alpha_composite(t2, (326, 140)); return im
def round_photo(img, h, r=34):
    w = int(img.width * h / img.height); im = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (w * 3, h * 3), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 3 - 1, h * 3 - 1), r * 3, fill=255)
    im.putalpha(m.resize((w, h), Image.LANCZOS)); return im
@functools.lru_cache(None)
def photo_sprite(name, h):
    if name == "front": img = Image.open(U + "a3264269-image.jpg").crop((0, 640, 1512, 1660))
    else:
        img = Image.open(U + "57dbd78a-image.jpg"); img = img.rotate(-1.5, resample=Image.BICUBIC, center=(750, 1000)).crop((100, 700, 1330, 1360))
    return round_photo(img, h)
@functools.lru_cache(None)
def endcard_sprite():
    ph = photo_sprite("back", 400); t = text_sprite("DS Pharma [Eye Care]", MONT8, 60, px=14, py=8, max_w=880)
    sub = [text_sprite(s, NOTO6, 38, px=4, py=2) for s in ("Digunakan secara tradisional", "untuk kesihatan mata")]
    mal = chip_sprite("MAL22076147T")
    return ph, t, sub, mal

# ---------------------------------------------------------------- infografik
@functools.lru_cache(None)
def node_sprite(icon, r):
    D = 2 * r + 16; im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    sh = Image.new("RGBA", (D, D), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((8, 14, D - 8, D - 2), fill=(0, 0, 0, 70)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    k = 3; c = Image.new("RGBA", (D * k, D * k), (0, 0, 0, 0)); ImageDraw.Draw(c).ellipse((8 * k, 8 * k, (D - 8) * k, (D - 8) * k), fill=(255, 255, 255, 250))
    im.alpha_composite(c.resize((D, D), Image.LANCZOS))
    sz = int(r * 1.25)
    if icon == "A":
        f = font(MONT9, int(r * 1.25)); ImageDraw.Draw(im).text((D / 2, D / 2 + 4), "A", font=f, fill=PURPLE + (255,), anchor="mm")
    elif icon == "oilparticle":
        pa = svg_png("particle", int(r * 1.5)); im.alpha_composite(pa, (D // 2 - pa.width // 2, D // 2 - pa.height // 2))
        for ang, (dx, dy) in enumerate([(-0.62, -0.28), (0.62, -0.18), (0.0, 0.66)]):
            dr = svg_png("droplet", int(r * 0.42)); im.alpha_composite(dr, (int(D / 2 + dx * r - dr.width / 2), int(D / 2 + dy * r - dr.height / 2)))
    else:
        ic = svg_png(icon, sz); im.alpha_composite(ic, (D // 2 - ic.width // 2, D // 2 - ic.height // 2))
    return im
@functools.lru_cache(None)
def label_sprite(text): return text_sprite(text, MONT7, 36, fill=WHITE, stroke=0, px=12, py=6, boxr=12)
@functools.lru_cache(None)
def infocard_sprite(icon, text, w):
    h = 78; im = rr(w, h, h // 2, (255, 255, 255, 247)); ic = svg_png(icon, 54); im.alpha_composite(ic, (22, (h - ic.height) // 2))
    t = text_sprite(text, MONT7, 31, fill=PURPLE_DARK, px=4, py=4); im.alpha_composite(t, (84, (h - t.height) // 2)); return im
@functools.lru_cache(None)
def ingcard_sprite(icon, name, tag, mg):
    w, h = 370, 172; im = rr(w, h, 30, (255, 255, 255, 247)); ic = svg_png(icon, 92); im.alpha_composite(ic, (18, (h - ic.height) // 2))
    d = ImageDraw.Draw(im)
    d.text((132, 38), name, font=font(MONT7, 31), fill=PURPLE_DARK + (255,), anchor="lm")
    d.text((132, 96), mg, font=font(MONT9, 54), fill=PURPLE + (255,), anchor="lm")
    d.text((134, 142), tag, font=font(NOTO6, 26), fill=(110, 100, 140, 255), anchor="lm"); return im
@functools.lru_cache(None)
def tracker_sprite(step, title):
    W2, H2 = 900, 84; im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    t = text_sprite(f"0{step}  {title}", MONT8, 38, fill=WHITE, stroke=0, px=2, py=2); im.alpha_composite(t, (-8, 0))
    d = ImageDraw.Draw(im); seg = (W2 - 3 * 16) // 4
    for k in range(4):
        x0 = k * (seg + 16); d.rounded_rectangle((x0, 66, x0 + seg, 74), 4, fill=(255, 255, 255, 255 if k < step else 60))
    return im
def line_layer(pts, p, w=8, head=True):
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]; pad = 26
    ox, oy = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad; k = 2
    lay = Image.new("RGBA", ((int(math.ceil(max(xs))) - ox + pad) * k, (int(math.ceil(max(ys))) - oy + pad) * k), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = [((x - ox) * k, (y - oy) * k) for x, y in pts]
    segs = [math.dist(P[i], P[i + 1]) for i in range(len(P) - 1)]; tot = sum(segs); goal = tot * p; acc = 0; col = (255, 255, 255, 235)
    cur = [P[0]]
    for i, L in enumerate(segs):
        if acc + L <= goal: cur.append(P[i + 1]); acc += L
        else:
            f = (goal - acc) / L if L else 0; cur.append((P[i][0] + (P[i + 1][0] - P[i][0]) * f, P[i][1] + (P[i + 1][1] - P[i][1]) * f)); break
    if len(cur) > 1: d.line(cur, fill=col, width=w * k, joint="curve")
    for q in cur[1:-1] if len(cur) > 2 else []: d.ellipse((q[0] - w * k / 2, q[1] - w * k / 2, q[0] + w * k / 2, q[1] + w * k / 2), fill=col)
    if head and p >= 0.999:
        a, b = P[-2], P[-1]; ang = math.atan2(b[1] - a[1], b[0] - a[0]); L = 26 * k; W = 15 * k
        tip = (b[0] + math.cos(ang) * 2 * k, b[1] + math.sin(ang) * 2 * k)
        d.polygon([tip, (tip[0] - L * math.cos(ang) + W * math.sin(ang), tip[1] - L * math.sin(ang) - W * math.cos(ang)),
                   (tip[0] - L * math.cos(ang) - W * math.sin(ang), tip[1] - L * math.sin(ang) + W * math.cos(ang))], fill=col)
    return lay.resize((lay.width // k, lay.height // k), Image.LANCZOS), (ox, oy)
def paste_layer(cv, lay, ox, oy, alpha, rects):
    a = lay.getchannel("A")
    if alpha < 0.999: a = a.point(lambda v: int(v * alpha))
    cv.paste(lay.convert("RGB"), (int(ox), int(oy)), a); rects.append((int(ox), int(oy), int(ox) + lay.width, int(oy) + lay.height))
def fade(t, t0, t1, fin=0.12, fout=0.12):
    return min(1, (t - t0) / fin) * (min(1, (t1 - t) / fout) if t1 - t < fout else 1)

# ---------------------------------------------------------------- muka
def load_faces(n=1765):
    d = json.load(open(os.path.join(ROOT, "work/faces.json"))); ks = sorted(int(k) for k in d)
    arr = np.array([d[str(k)] for k in ks], float)                  # x,y,w,h
    from numpy.lib.stride_tricks import sliding_window_view
    def med(a, w=7):
        p = np.pad(a, (w // 2, w // 2), mode="edge"); return np.median(sliding_window_view(p, w), axis=1)
    sm = np.stack([med(arr[:, c]) for c in range(4)], 1)
    def gauss(a, s=5):
        r = np.arange(-3 * s, 3 * s + 1); k = np.exp(-r ** 2 / (2 * s * s)); k /= k.sum()
        p = np.pad(a, (len(r) // 2, len(r) // 2), mode="edge"); return np.convolve(p, k, "valid")
    sm = np.stack([gauss(sm[:, c]) for c in range(4)], 1)
    fr = np.arange(n); out = np.stack([np.interp(fr, ks, sm[:, c]) for c in range(4)], 1)
    raw = np.stack([np.interp(fr, ks, arr[:, c]) for c in range(4)], 1)
    chk = np.stack([np.interp(fr, ks, np.stack([med(arr[:, c]) for c in range(4)], 1)[:, k]) for k, c in enumerate(range(4))], 1)
    return out, chk
FACE, FACE_RAW = load_faces()

def presenter(img, i, scale, ow, oh, ax, ay):
    j = min(i, len(FACE) - 1); x, y, w, h = FACE[j]; fx, fy = x + w / 2, y + h / 2
    ww, wh = ow / scale, oh / scale
    x0 = min(max(fx - ax / scale, 0), SW - ww); y0 = min(max(fy - ay / scale, 0), SH - wh)
    im = img.resize((ow, oh), Image.BILINEAR, box=(x0, y0, x0 + ww, y0 + wh))
    rx, ry, rw, rh = FACE_RAW[j]
    return im, ((rx - x0) * scale, (ry - y0) * scale, (rx + rw - x0) * scale, (ry + rh - y0) * scale)

def seg_at(t):
    for k, (n, a, b) in enumerate(SEGMENTS):
        if a <= t < b + 1e-9: return n, a, b
    return SEGMENTS[-1]
def punch(t):
    v = 0.0
    for p in PUNCH:
        d = t - p
        if 0 <= d < 0.12: v = max(v, eo(d / 0.12))
        elif 0.12 <= d < 0.52: v = max(v, 1)
        elif 0.52 <= d < 0.70: v = max(v, 1 - eo((d - 0.52) / 0.18))
    return v

@functools.lru_cache(None)
def top_bg():
    y = np.linspace(0, 1, SPLIT_Y)[:, None, None]
    a = np.array(PURPLE_DARK, float)[None, None]; b = np.array((0x3B, 0x2A, 0x66), float)[None, None]
    g = (a + (b - a) * y) * np.ones((1, W, 1))
    xx = np.linspace(-1, 1, W)[None, :, None]; g = g * (1 - 0.10 * xx ** 2)
    ys, xs = np.mgrid[0:SPLIT_Y, 0:W]; dots = ((xs % 54) < 3) & ((ys % 54) < 3) & (ys > 250)
    g[dots] = g[dots] * 0.78 + 255 * 0.22
    return Image.fromarray(g.clip(0, 255).astype(np.uint8))

# ---------------------------------------------------------------- komposisi
def paste(cv, spr, cx, cy, scale=1.0, alpha=1.0, rects=None, dy=0):
    if alpha <= 0.003: return
    if abs(scale - 1) > 1e-3: spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BILINEAR)
    x, y = int(cx - spr.width / 2), int(cy - spr.height / 2 + dy)
    a = spr.getchannel("A")
    if alpha < 0.999: a = a.point(lambda v: int(v * alpha))
    cv.paste(spr.convert("RGB"), (x, y), a)
    if rects is not None:
        bb = a.point(lambda v: 255 if v > 24 else 0).getbbox()
        if bb: rects.append((x + bb[0], y + bb[1], x + bb[2], y + bb[3]))

def steam(cv, t, cx, y_base, rects):
    lay = Image.new("RGBA", (300, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k, ox in enumerate((60, 150, 240)):
        ph = t * 2.2 + k * 1.7; pts = []
        for yy in range(190, 10, -6):
            pts.append((ox + 12 * math.sin(yy * 0.045 + ph) + 5 * math.sin(yy * 0.11 + ph * 1.3), yy))
        for q in range(len(pts) - 1):
            fade = (q / len(pts)); al = int(150 * math.sin(math.pi * min(1, fade * 1.0 + 0.05)) * (0.55 + 0.45 * math.sin(ph + q * .3)))
            d.line((pts[q], pts[q + 1]), fill=(255, 255, 255, max(0, al)), width=11)
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    paste(cv, lay, cx, y_base - 100, rects=rects)

def sprite_scene(cv, t, e, rects):
    a, s = anim(t, e["t0"], e["t1"], tin=0.40)
    if a <= 0: return
    cx, cy = 510, 470
    bob = 6 * math.sin(t * 2.6)
    if e.get("pan"):
        paste(cv, svg_png("pan", 520), 510, 735, s, a, rects)
        steam(cv, t, 510, 668, rects)
    paste(cv, svg_png("particle", 290), cx, cy + bob, s, a, rects)
    if e.get("orbit"):
        n = 7
        for k in range(n):
            ang = (t - e["t0"]) * 1.5 + k * 2 * math.pi / n
            ox, oy = 190 * math.cos(ang), 78 * math.sin(ang); depth = 0.78 + 0.22 * math.sin(ang)
            paste(cv, svg_png("droplet", 64), cx + ox * s, cy + oy * s + bob, s * depth, a, rects)

def draw_elements(cv, t, rects):
    for e in ELEMENTS:
        if not (e["t0"] <= t < e["t1"]): continue
        k = e["kind"]; a, s = anim(t, e["t0"], e["t1"])
        if k == "icon":
            bob = 5 * math.sin((t - e["t0"]) * 3.0)
            paste(cv, svg_png(e["name"], e["size"]), e["cx"], e["cy"] + bob, s, a, rects)
        elif k == "node":
            r = e["r"]; paste(cv, node_sprite(e["icon"], r), e["cx"], e["cy"], s, a, rects)
            a2, s2 = anim(t, e["t0"] + 0.10, e["t1"]); paste(cv, label_sprite(e["label"]), e["cx"], e["cy"] + r + 46, s2, a2, rects)
        elif k == "line":
            p = eo((t - e["t0"]) / 0.35); lay, (ox, oy) = line_layer(e["pts"], p); paste_layer(cv, lay, ox, oy, fade(t, e["t0"], e["t1"]), rects)
        elif k == "callout":
            p = eo((t - e["t0"]) / 0.30); cx, cy = e["cx"], e["cy"]; tx, ty = e["target"]
            ch = chip_sprite(e["text"]); ang = math.atan2(ty - cy, tx - cx)
            sx, sy = cx + math.cos(ang) * (ch.width / 2 if abs(math.cos(ang)) * ch.height > abs(math.sin(ang)) * ch.width else ch.height / 2 * abs(math.cos(ang)) / max(1e-6, abs(math.sin(ang)))), 0
            # titik mula: tepi chip paling hampir sasaran
            sx = cx + (ch.width / 2 if tx > cx else -ch.width / 2) if abs(tx - cx) > ch.width / 2 else cx
            sy = cy if abs(tx - cx) > ch.width / 2 else (cy + ch.height / 2 if ty > cy else cy - ch.height / 2)
            lay, (ox, oy) = line_layer([(sx, sy), (tx, ty)], p, w=5, head=False); paste_layer(cv, lay, ox, oy, fade(t, e["t0"], e["t1"]), rects)
            if p >= 0.999:
                dot = Image.new("RGBA", (24, 24), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((2, 2, 22, 22), fill=(255, 255, 255, 255)); paste(cv, dot, tx, ty, 1, fade(t, e["t0"], e["t1"]), rects)
            paste(cv, ch, cx, cy, s, a, rects)
        elif k == "infocard": paste(cv, infocard_sprite(e["icon"], e["text"], e["w"]), e["cx"], e["cy"], s, a, rects)
        elif k == "ingcard": paste(cv, ingcard_sprite(e["icon"], e["name"], e["tag"], e["mg"]), e["cx"], e["cy"], s, a, rects)
        elif k == "tracker": paste(cv, tracker_sprite(e["step"], e["title"]), 510, 305, 1.0, fade(t, e["t0"], e["t1"], 0.15, 0.10), rects)
        elif k == "chip": paste(cv, chip_sprite(e["text"]), e["cx"], e["cy"], s, a, rects)
        elif k == "src": paste(cv, src_sprite(e["text"]), 510, 885, s, a, rects)
        elif k == "particle": sprite_scene(cv, t, e, rects)
        elif k == "photo": paste(cv, photo_sprite(e["name"], e["h"]), e["cx"], e["cy"], s, a, rects)
        elif k == "endcard":
            ph, ttl, sub, mal = endcard_sprite()
            paste(cv, ph, 510, 460, s, a, rects)
            a2, s2 = anim(t, e["t0"] + 0.12, e["t1"] + 1, tout=0.01); paste(cv, ttl, 510, 735, s2, a2, rects)
            a3, s3 = anim(t, e["t0"] + 0.24, e["t1"] + 1, tout=0.01)
            paste(cv, sub[0], 510, 815, s3, a3, rects); paste(cv, sub[1], 510, 865, s3, a3, rects)
            a4, s4 = anim(t, e["t0"] + 0.36, e["t1"] + 1, tout=0.01); paste(cv, mal, 510, 950, s4, a4, rects)

def draw_slams(cv, t, rects):
    for i, s in enumerate(SLAMS):
        if not (s["t0"] <= t < s["t1"]): continue
        d = t - s["t0"]; a = 1.0 if d < 0.1 else min(1, 0.4 + d / 0.1)
        sc = 1 + 0.10 * (1 - eo_back(d / 0.30, 1.4)) if d < 0.45 else 1
        if t > s["t1"] - 0.12: q = (t - (s["t1"] - 0.12)) / 0.12; a *= 1 - q; sc *= 1 - 0.06 * q
        sh = 0 if d > 0.18 else 7 * math.sin(d * 140) * (1 - d / 0.18)
        paste(cv, slam_sprite(i), 510 + sh, 1085, sc, a, rects)

def draw_captions(cv, t, ly, rects):
    for i, (a0, a1, _) in enumerate(CAPTIONS):
        if a0 <= t < a1:
            d = t - a0; al = min(1, d / 0.08); sc = 0.85 + 0.15 * eo_back(d / 0.30, 1.2)
            if t > a1 - 0.10: al *= max(0, (a1 - t) / 0.10)
            paste(cv, caption_sprite(i), 510, ly, sc, al, rects)

def compose(layout, t, i, img, rects):
    n, s0, s1 = seg_at(t)
    prog = min(max((t - s0) / max(1e-6, s1 - s0), 0), 1)
    sc_push = 1 + PUSH * prog; sc_p = 1 + PUNCH_AMT * punch(t)
    if layout == "L1":
        pv, fr = presenter(img, i, 1.15 * sc_push * sc_p, W, H, 540, 640)
        cv = pv; face = fr
        draw_elements(cv, t, rects); draw_slams(cv, t, rects); draw_captions(cv, t, 1410, rects)
    else:
        cv = Image.new("RGB", (W, H)); cv.paste(top_bg(), (0, 0))
        pv, fr = presenter(img, i, 1.10 * sc_push * sc_p, W, H - SPLIT_Y, 540, 270)
        cv.paste(pv, (0, SPLIT_Y)); face = (fr[0], fr[1] + SPLIT_Y, fr[2], fr[3] + SPLIT_Y)
        draw_elements(cv, t, rects); draw_captions(cv, t, 1000, rects)
    for ft in FLASHES:
        d = t - ft
        if 0 <= d < 0.12:
            ov = Image.new("RGB", (W, H), WHITE); cv = Image.blend(cv, ov, 0.5 * (1 - d / 0.12))
    return cv, face

def zoomfx(im, k, blur):
    ww, hh = W / k, H / k; x0, y0 = (W - ww) / 2, (H - hh) / 2
    out = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + ww, y0 + hh))
    return out.filter(ImageFilter.GaussianBlur(blur)) if blur > 0.3 else out

def render_frame(i, img):
    t = i / FPS; rects = []; trans = False; fi = min(i, FREEZE)
    layout = seg_at(t)[0]
    for T in ZOOM_THROUGH:
        if T - 0.15 <= t < T:
            lay = seg_at(T - 1e-3)[0]; cv, face = compose(lay, t, fi, img, rects)
            p = eo((t - (T - 0.15)) / 0.15) if False else ei((t - (T - 0.15)) / 0.15)
            return zoomfx(cv, 1 + 0.35 * p, 7 * p), face, rects, True
        if T <= t < T + 0.15:
            lay = seg_at(T + 1e-3)[0]; cv, face = compose(lay, t, fi, img, rects)
            p = 1 - eo((t - T) / 0.15)
            return zoomfx(cv, 1 + 0.35 * p, 7 * p), face, rects, True
    cv, face = compose(layout, t, fi, img, rects)
    return cv, face, rects, False

# ---------------------------------------------------------------- pipeline
def read_frames(video, start, count):
    """Baca bingkai sumber; selepas FREEZE bingkai dibekukan."""
    s = min(start, FREEZE); real = min(start + count - 1, FREEZE) - s + 1
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{s / FPS:.5f}", "-i", video, "-frames:v", str(real), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE); sz = SW * SH * 3; got = 0; last = None
    while got < real:
        b = p.stdout.read(sz)
        if len(b) < sz: break
        last = Image.frombytes("RGB", (SW, SH), b); got += 1
        if start <= FREEZE: yield last
    p.wait()
    for _ in range(count - (got if start <= FREEZE else 0)): yield last

def work(args):
    video, a, b, outp = args
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(FPS),
        "-x264-params", "keyint=30:min-keyint=30", "-movflags", "+faststart", outp], stdin=subprocess.PIPE)
    log = []
    for k, img in enumerate(read_frames(video, a, b - a)):
        i = a + k; cv, face, rects, tr = render_frame(i, img)
        enc.stdin.write(cv.tobytes()); log.append((i, [round(v, 1) for v in face], rects, tr))
    enc.stdin.close(); enc.wait()
    return log

if __name__ == "__main__":
    video, outd = sys.argv[1], sys.argv[2]; os.makedirs(outd, exist_ok=True)
    if "--frames" in sys.argv:
        for fs in sys.argv[sys.argv.index("--frames") + 1].split(","):
            i = int(round(float(fs) * FPS)); img = next(read_frames(video, min(i, FREEZE), 1))
            cv, face, rects, tr = render_frame(i, img); cv.save(f"{outd}/f_{fs}.png")
        sys.exit()
    nw = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    cuts = [round(NF * k / (nw * 3)) for k in range(nw * 3 + 1)]
    jobs = [(video, cuts[k], cuts[k + 1], f"{outd}/part{k:02d}.mp4") for k in range(nw * 3)]
    from multiprocessing import Pool
    with Pool(nw) as pool: logs = pool.map(work, jobs, chunksize=1)
    allog = [x for l in logs for x in l]; json.dump(allog, open(f"{outd}/framelog.json", "w"))
    with open(f"{outd}/list.txt", "w") as f:
        for j in jobs: f.write(f"file '{os.path.abspath(j[3])}'\n")
    print("ok", len(allog), "frames")
