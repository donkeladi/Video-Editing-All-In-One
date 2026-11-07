#!/usr/bin/env python3
"""Candia Sandal Mesh Gold Chain (TP28111L) — TikTok 1080x1920 30fps.
Video utama full-frame + cutaway footage/gambar (zoom) + sub-title + animasi warna/saiz/harga/CTA.
Guna:  python3 scripts/build_sandal.py <upload_dir> <out.mp4>
Perlu: ffmpeg (zscale), numpy, pillow, opencv-python-headless.
"""
import subprocess as sp, numpy as np, cv2, sys, os, glob, math, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
UP = sys.argv[1]; OUT = sys.argv[2]
def up(pat): return glob.glob(f"{UP}/{pat}")[0]
MAIN = up("46e75197-*.mov")
CLIP = {n: up(f"*IMG_{n}.mov") for n in (1727, 1728, 1729, 1730, 1731)}
PHOTO = {"cream_book": up("6b36d40f-image.jpg"), "trio": up("b4374380-image.jpg"), "pink_black": up("bca80efb-image.jpg")}
TOTAL = 66.95
NF = int(TOTAL * FPS)

# ---------- helpers ----------
FD = "/usr/share/fonts/opentype/inter/"
def F(w, s): return ImageFont.truetype(f"{FD}Inter-{w}.otf", s)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def ease_back(x, c=1.9): x = clamp(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

HDR_VF = ("zscale=t=linear:npl=203:tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv,format=gbrpf32le,"
          "zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=rgb24")
def reader(path, ss, dur, hdr, pre=""):
    vf = f"fps={FPS},scale={W}:{H}:flags=lanczos," + (HDR_VF if hdr else "format=rgb24")
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur + 0.2), "-i", path, "-an", "-vf", vf,
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return sp.Popen(cmd, stdout=sp.PIPE, bufsize=W * H * 3 * 4)
def read_frame(p):
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: return None
    return np.frombuffer(b, np.uint8).reshape(H, W, 3)

def zoom(img, z, cx=0.5, cy=0.5):
    """crop zoom (z>=1) di sekitar (cx,cy) pecahan, output WxH."""
    h, w = img.shape[:2]
    cw, ch = w / z, h / z
    x0 = clamp(cx * w - cw / 2, 0, w - cw); y0 = clamp(cy * h - ch / 2, 0, h - ch)
    M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC)

def load_photo(path):
    im = np.asarray(Image.open(path).convert("RGB"))
    h, w = im.shape[:2]
    # cover-fit ke 9:16 (kekalkan resolusi asal, zoom dibuat dari sumber besar)
    tw = int(h * 9 / 16)
    if tw <= w:
        x0 = (w - tw) // 2; im = im[:, x0:x0 + tw]
    return im
def photo_frame(im, z, cx, cy):
    return zoom(im, z, cx, cy)

# ---------- sprites ----------
SS = 2
def sprite_from(draw_fn, w, h):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    draw_fn(d, SS)
    im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im)
def shadow(im, blur=18, off=10, a=90):
    pad = blur * 3
    big = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    al = im.split()[3].point(lambda v: int(v * a / 255))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 255)); sh.putalpha(al)
    big.paste(sh, (pad, pad + off)); big = big.filter(ImageFilter.GaussianBlur(blur))
    big.alpha_composite(im, (pad, pad)); return big

INK = (22, 22, 26); WHITE = (255, 255, 255); GOLD = (255, 205, 60); DARK = (24, 24, 28, 235)
cache = {}
def pill(text, size=50, fill=(255, 255, 255, 245), fg=INK, h=None, padx=46, dot=None, weight="ExtraBold",
         check=False, outline=None):
    key = ("pill", text, size, fill, fg, h, padx, dot, weight, check, outline)
    if key in cache: return cache[key]
    f = F(weight, size * SS); h = h or int(size * 2.0)
    tw = int(f.getlength(text) / SS)
    lead = 0
    if dot: lead = int(h * 0.42) + 24
    if check: lead = int(h * 0.5) + 22
    w = padx * 2 + lead + tw
    base = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(base)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), h * SS // 2, fill=fill,
                        outline=outline, width=(3 * SS if outline else 0))
    x = padx * SS
    cy = h * SS // 2
    if dot:
        r = int(h * 0.21) * SS
        d.ellipse((x, cy - r, x + 2 * r, cy + r), fill=dot, outline=(0, 0, 0, 90), width=2 * SS)
        x += 2 * r + 24 * SS
    if check:
        r = int(h * 0.25) * SS
        d.ellipse((x, cy - r, x + 2 * r, cy + r), fill=GOLD)
        d.line([(x + r * .5, cy + r * .02), (x + r * .88, cy + r * .42), (x + r * 1.5, cy - r * .4)],
               fill=INK, width=int(r * .28), joint="curve")
        x += 2 * r + 22 * SS
    d.text((x, cy), text, font=f, fill=fg, anchor="lm")
    base = base.resize((w, h), Image.LANCZOS)
    out = shadow(base); arr = np.asarray(out); cache[key] = arr; return arr

def text_sprite(text, size, fill=WHITE, weight="Black", stroke=0, stroke_fill=(0, 0, 0), spacing=1.0, align="center"):
    key = ("txt", text, size, fill, weight, stroke, stroke_fill)
    if key in cache: return cache[key]
    f = F(weight, size * SS)
    lines = text.split("\n")
    lh = int(size * 1.12 * SS)
    wmax = max(int(f.getlength(l)) for l in lines)
    pad = (stroke + 30) * SS
    im = Image.new("RGBA", (wmax + pad * 2, lh * len(lines) + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((im.width / 2, pad + lh * i + lh / 2), l, font=f, fill=fill, anchor="mm",
               stroke_width=stroke * SS, stroke_fill=stroke_fill)
    im = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    arr = np.asarray(shadow(im, 12, 6, 120) if stroke == 0 and False else im); cache[key] = arr; return arr

def blit(frame, spr, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if alpha <= 0.003 or scale <= 0.01: return
    h, w = spr.shape[:2]
    if scale != 1.0 or rot:
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
        nw, nh = int(w * scale) + 2, int(h * scale) + 2
        if rot:  # beri ruang
            nw, nh = int(max(w, h) * scale * 1.3), int(max(w, h) * scale * 1.3)
        M[0, 2] += nw / 2 - w / 2; M[1, 2] += nh / 2 - h / 2
        spr = cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR,
                             borderValue=(0, 0, 0, 0)); h, w = spr.shape[:2]
    x0 = int(round(cx - w / 2)); y0 = int(round(cy - h / 2))
    X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(W, x0 + w), min(H, y0 + h)
    if X1 <= X0 or Y1 <= Y0: return
    s = spr[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32)
    a = (s[..., 3:4] / 255.0) * alpha
    roi = frame[Y0:Y1, X0:X1].astype(np.float32)
    frame[Y0:Y1, X0:X1] = (roi * (1 - a) + s[..., :3] * a).astype(np.uint8)

def pop(t, t0, dur=0.38):
    """scale overshoot + fade-in. return (scale, alpha)"""
    x = (t - t0) / dur
    if x <= 0: return 0, 0
    return ease_back(x), clamp(x * 3)
def fade_out(t, t1, dur=0.25): return 1 - clamp((t - t1) / dur)

# ---------- palette warna ----------
COL = {"Tan": (184, 98, 52), "Brown": (150, 128, 112), "Cream": (240, 232, 214), "Pink": (232, 182, 208), "Black": (28, 28, 30)}

# ---------- sub-title (disemak manual drpd whisper) ----------
# (mula, tamat, teks, perkataan_highlight)
SUBS = [
    (0.00, 2.10, "Hai, kat sini saya ada", []),
    (2.10, 3.90, "sandal yang berkualiti", ["berkualiti"]),
    (4.00, 5.80, "siapa yang tengah cari sandal?", ["sandal?"]),
    (6.90, 8.75, "kita ada macam-macam", []),
    (8.75, 10.30, "pilihan warna", ["warna"]),
    (10.35, 11.95, "kita ada warna TAN", ["TAN"]),
    (11.95, 13.40, "kita ada warna BROWN", ["BROWN"]),
    (13.50, 15.40, "Tapi kalau cari tone colour\nyang cerah", ["cerah"]),
    (15.40, 18.40, "kita ada warna CREAM", ["CREAM"]),
    (18.40, 20.00, "kita ada warna PINK juga", ["PINK"]),
    (20.00, 22.40, "Tapi kalau nak pakai untuk\ncasual ataupun", ["casual"]),
    (22.40, 24.10, "nak pakai untuk\naktiviti formal", ["formal"]),
    (24.10, 25.45, "kita ada warna HITAM", ["HITAM"]),
    (25.50, 27.70, "Tapi kalau nak ambil\nsemua pun boleh", ["semua"]),
    (28.10, 30.00, "harga murah-murah saja", ["murah-murah"]),
    (30.00, 31.40, "boleh tengok terus\ndalam BEG KUNING", ["BEG", "KUNING"]),
    (31.70, 33.60, "Harga cukup-cukup berbaloi", ["berbaloi"]),
    (33.70, 35.55, "insole agak tebal", ["insole", "tebal"]),
    (35.55, 37.30, "extra span kita bagi", ["extra", "span"]),
    (37.40, 40.40, "Lepas itu dengan finishing\nGOLD CHAIN macam ni", ["GOLD", "CHAIN"]),
    (40.40, 42.55, "dan juga tali\nyang lembut tau", ["lembut"]),
    (42.60, 44.10, "Material PU leather", ["PU", "leather"]),
    (44.10, 45.90, "jangan risau selesa", ["selesa"]),
    (45.90, 47.70, "pakai tak melecet\ndekat bahagian tapak", ["melecet"]),
    (47.70, 50.40, "tapak PVC anti-slip", ["PVC", "anti-slip"]),
    (50.60, 52.60, "Jadi kalau nak dapatkan\nsemua ni", ["semua"]),
    (52.60, 54.85, "harga cukup-cukup berbaloi", ["berbaloi"]),
    (54.85, 57.00, "harga yang cukup-cukup jimat", ["jimat"]),
    (57.00, 59.80, "boleh dapatkan dalam\nBEG KUNING kita sekarang", ["BEG", "KUNING"]),
    (60.90, 62.10, "Bye, jumpa lagi!", []),
    (62.10, 64.00, "Jangan lupa check out", ["check", "out"]),
    (64.00, 66.60, "Jangan lupa follow kita\njuga dan komen", ["follow", "komen"]),
]
def sub_sprite(text, hi):
    key = ("sub", text, tuple(hi))
    if key in cache: return cache[key]
    size = 68; f = F("Black", size * SS)
    lines = text.split("\n"); lh = int(size * 1.2 * SS)
    pad = 24 * SS
    wmax = max(int(f.getlength(l)) for l in lines)
    im = Image.new("RGBA", (wmax + pad * 2, lh * len(lines) + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        words = l.split(" "); total = int(f.getlength(l)); x = (im.width - total) / 2
        sp_w = f.getlength(" ")
        cy = pad + lh * i + lh / 2
        for wd in words:
            col = GOLD if wd in hi else (255, 255, 255)
            d.text((x, cy), wd, font=f, fill=col, anchor="lm", stroke_width=9 * SS, stroke_fill=(10, 10, 12))
            x += f.getlength(wd) + sp_w
    im = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    if im.width > 1000:
        r = 1000 / im.width; im = im.resize((1000, int(im.height * r)), Image.LANCZOS)
    arr = np.asarray(im); cache[key] = arr; return arr

# ---------- cutaway ----------
# (mula, tamat, jenis, sumber, ss_klip/zoom params, label)
CUTS = [
    (7.40, 10.20, "clip", 1727, 0.4, "5 PILIHAN WARNA"),
    (16.60, 19.00, "photo", "trio", (1.00, 1.18, 0.50, 0.65), "CREAM"),
    (19.00, 21.30, "photo", "pink_black", (1.00, 1.16, 0.30, 0.68), "PINK  •  HITAM"),
    (23.70, 27.40, "clip", 1729, 3.0, "HITAM  •  FORMAL"),
    (33.60, 38.00, "clip", 1730, 3.0, "INSOLE TEBAL"),
    (38.00, 41.80, "clip", 1728, 0.0, "GOLD CHAIN"),
    (42.70, 45.60, "photo", "cream_book", (1.00, 1.30, 0.60, 0.62), "MESH + PU LEATHER"),
]
XF = 0.18  # tempoh transisi

def cut_alpha(t):
    for c in CUTS:
        a, b = c[0], c[1]
        if a - 1e-6 <= t <= b + 1e-6:
            return c, min(ease_io((t - a) / XF), ease_io((b - t) / XF))
    return None, 0.0

# ---------- timeline overlay ----------
SIZES = [36, 37, 38, 39, 40, 41]
FEATS = [(34.0, "Insole tebal + extra span"), (38.2, "Gold chain finishing"),
         (42.8, "Material PU leather"), (47.9, "Tapak PVC anti-slip")]

def gold_glint(frame, t, t0, cy, wd=720, ht=140):
    pass

def draw_overlay(f, t, cutinfo):
    c, ca = cutinfo
    # ----- HUD (tema digital) pada cutaway -----
    if c is not None and ca > 0.01:
        a = ca
        L = 70; m = 56; th = 6
        col = (255, 205, 60)
        ov = f  # corner brackets
        for (x, y, dx, dy) in [(m, 110, 1, 1), (W - m, 110, -1, 1), (m, H - 500, 1, -1), (W - m, H - 500, -1, -1)]:
            cv2.line(ov, (x, y), (x + dx * L, y), col, th, cv2.LINE_AA)
            cv2.line(ov, (x, y), (x, y + dy * L), col, th, cv2.LINE_AA)
        blit(f, pill(c[5], 44, fill=DARK, fg=GOLD, h=92, padx=40), W // 2, 190, ease_back((t - c[0]) / 0.4), a)
        # scan line
        sy = int(((t - c[0]) * 520) % (H - 700)) + 150
        band = f[sy:sy + 5].astype(np.float32); f[sy:sy + 5] = np.clip(band * 0.65 + 255 * 0.35, 0, 255).astype(np.uint8)

    # ----- HOOK -----
    if t < 4.4:
        k = 1 - clamp((t - 3.9) / 0.4)
        s, a = pop(t, 0.25, 0.5)
        blit(f, text_sprite("SANDAL MESH", 112, WHITE, "Black", 10), W // 2, 960, s, a * k)
        s2, a2 = pop(t, 0.5, 0.5)
        blit(f, text_sprite("GOLD CHAIN", 130, GOLD, "Black", 10), W // 2, 1085, s2, a2 * k)
        s3, a3 = pop(t, 0.9, 0.45)
        blit(f, pill("CANDIA  •  TP28111L", 40, fill=DARK, fg=WHITE, h=84, padx=40), W // 2, 1215, s3, a3 * k)
    elif t < 6.9:
        # lencana kecil kekal
        s, a = pop(t, 4.4, 0.4)
        blit(f, pill("CANDIA  Sandal Mesh Gold Chain", 34, fill=DARK, fg=WHITE, h=72, padx=34), W // 2, 128, s, a)
    # lencana kekal selepas hook (kecuali semasa cutaway HUD label ada di y=190)
    if 6.9 <= t < 60.6 and ca < 0.01:
        blit(f, pill("CANDIA  Sandal Mesh Gold Chain", 34, fill=DARK, fg=WHITE, h=72, padx=34), W // 2, 128, 1, 1)

    # ----- WARNA (swatch bar animasi) -----
    order = [("Tan", 10.8), ("Brown", 12.4), ("Cream", 17.0), ("Pink", 19.1), ("Black", 24.6)]
    if 8.0 <= t < 31.0:
        bar_k = ease_out((t - 8.0) / 0.4) * (1 - clamp((t - 30.6) / 0.4))
        # tajuk
        blit(f, pill("5 PILIHAN WARNA", 40, fill=DARK, fg=GOLD, h=84, padx=40), W // 2, 1005, ease_back((t - 8.0) / 0.45), bar_k)
        n = len(order); gap = 160; x0 = W // 2 - gap * (n - 1) / 2
        for i, (nm, ts) in enumerate(order):
            sc, al = pop(t, 8.6 + i * 0.08, 0.5)
            active = ts - 0.1 <= t < ts + 1.9
            pulse = 1 + 0.12 * math.sin((t - ts) * 9) * (1 if active else 0) * (1 - clamp((t - ts) / 1.9))
            big = 1.22 if active else 1.0
            cx = x0 + i * gap; cy = 1110
            sp = chip_sprite(nm, active)
            blit(f, sp, cx, cy, sc * big * pulse, al * bar_k)
    # "semua" – semua warna pop bersama selepas 25.6
    # ----- SENARAI CIRI -----
    if 34.0 <= t < 50.4:
        k = 1 - clamp((t - 50.0) / 0.4)
        for i, (ts, label) in enumerate(FEATS):
            s, a = pop(t, ts, 0.45)
            sp = pill(label, 44, fill=(255, 255, 255, 245), fg=INK, h=94, padx=40, check=True)
            blit(f, sp, 60 + sp.shape[1] / 2 - 60, 880 + i * 122, s, a * k)

    # ----- SAIZ -----
    if 50.4 <= t < 54.9:
        k = ease_out((t - 50.4) / 0.35) * (1 - clamp((t - 54.5) / 0.4))
        blit(f, pill("CUTTING KECIL", 52, fill=(214, 60, 60, 255), fg=WHITE, h=104, padx=50),
             W // 2, 880, ease_back((t - 50.4) / 0.45), k)
        gap = 128; x0 = W // 2 - gap * 2.5
        for i, sz in enumerate(SIZES):
            sc, al = pop(t, 50.7 + i * 0.1, 0.45)
            # chip "highlight" bergerak: biasa 37 -> naik 38
            move = ease_io((t - 52.3) / 0.6)
            hl_i = 1 + move  # 37 -> 38
            is_hl = abs(i - hl_i) < 0.5
            sp = size_chip(sz, is_hl)
            blit(f, sp, x0 + i * gap, 1000, sc * (1.18 if is_hl and t > 52.3 else 1), al * k)
        if t > 51.7:
            blit(f, pill("Kaki normal: UP 1 SIZE", 44, fill=DARK, fg=GOLD, h=92, padx=44), W // 2, 1118,
                 ease_back((t - 51.7) / 0.45), k)
        if t > 53.2:
            blit(f, pill("Kaki lebar: UP 2 SIZE", 44, fill=DARK, fg=WHITE, h=92, padx=44), W // 2, 1228,
                 ease_back((t - 53.2) / 0.45), k)

    # ----- HARGA -----
    if 54.9 <= t < 60.9:
        k = ease_out((t - 54.9) / 0.3) * (1 - clamp((t - 60.5) / 0.4))
        s = ease_back((t - 54.9) / 0.5)
        blit(f, price_card(), W // 2, 1010, s, k)
        gl = ((t - 55.6) * 1.6) % 2.2  # kilauan
        if gl < 1:
            pass
    # ----- CTA -----
    if t >= 60.9:
        s = ease_back((t - 60.95) / 0.5)
        blit(f, pill("KLIK BEG KUNING", 64, fill=GOLD + (255,), fg=INK, h=140, padx=64), W // 2, 1010, s, 1)
        bob = 18 * math.sin((t - 61) * 7)
        blit(f, arrow_sprite(), W // 2, 1150 + bob, ease_back((t - 61.2) / 0.5), 1)
        s2 = ease_back((t - 61.6) / 0.45)
        blit(f, pill("FOLLOW  •  KOMEN", 46, fill=DARK, fg=WHITE, h=96, padx=48), W // 2, 1275, s2 * (1 if t > 61.6 else 0), 1)

def chip_sprite(name, active):
    key = ("chip", name, active)
    if key in cache: return cache[key]
    r = 52; wd = 150; ht = 190
    def dr(d, ss):
        col = COL[name]
        cx = wd * ss // 2; cy = 70 * ss
        d.ellipse((cx - (r + 7) * ss, cy - (r + 7) * ss, cx + (r + 7) * ss, cy + (r + 7) * ss),
                  fill=(255, 205, 60, 255) if active else (255, 255, 255, 255))
        d.ellipse((cx - r * ss, cy - r * ss, cx + r * ss, cy + r * ss), fill=col + (255,))
        # kilau
        d.ellipse((cx - r * .55 * ss, cy - r * .7 * ss, cx - r * .05 * ss, cy - r * .3 * ss), fill=(255, 255, 255, 70))
        f = F("ExtraBold", 34 * ss); tw = f.getlength(name.upper()); pw = tw + 36 * ss
        d.rounded_rectangle((cx - pw / 2, 138 * ss, cx + pw / 2, 184 * ss), 23 * ss, fill=(24, 24, 28, 240))
        d.text((cx, 161 * ss), name.upper(), font=f, fill=GOLD if active else WHITE, anchor="mm")
    arr = sprite_from(dr, wd + 40, ht)
    cache[key] = arr; return arr

def size_chip(sz, hl):
    key = ("size", sz, hl)
    if key in cache: return cache[key]
    wd = 112; ht = 112
    def dr(d, ss):
        fill = (255, 205, 60, 255) if hl else (255, 255, 255, 245)
        d.rounded_rectangle((0, 0, wd * ss - 1, ht * ss - 1), 30 * ss, fill=fill)
        d.text((wd * ss / 2, ht * ss / 2), str(sz), font=F("Black", 54 * ss), fill=INK, anchor="mm")
    arr = np.asarray(shadow(Image.fromarray(sprite_from(dr, wd, ht)), 10, 6, 110)); cache[key] = arr; return arr

def price_card():
    key = ("price",)
    if key in cache: return cache[key]
    wd, ht = 800, 520
    def dr(d, ss):
        d.rounded_rectangle((0, 0, wd * ss - 1, ht * ss - 1), 56 * ss, fill=(255, 255, 255, 248))
        d.rounded_rectangle((0, 0, wd * ss - 1, 100 * ss), 56 * ss, fill=(22, 22, 26, 255))
        d.rectangle((0, 60 * ss, wd * ss - 1, 100 * ss), fill=(22, 22, 26, 255))
        d.text((wd * ss / 2, 52 * ss), "HARGA PROMO", font=F("ExtraBold", 40 * ss), fill=GOLD, anchor="mm")
        d.text((wd * ss / 2, 230 * ss), "RM37.90", font=F("Black", 150 * ss), fill=(218, 30, 70), anchor="mm")
        # harga asal bergaris
        f = F("Bold", 50 * ss); txt = "RM59.90"; tw = f.getlength(txt)
        x = 215 * ss; y = 372 * ss
        d.text((x, y), txt, font=f, fill=(110, 110, 116), anchor="lm")
        d.line((x - 8 * ss, y, x + tw + 8 * ss, y), fill=(218, 30, 70), width=7 * ss)
        d.rounded_rectangle((470 * ss, 340 * ss, 640 * ss, 404 * ss), 30 * ss, fill=(218, 30, 70))
        d.text((555 * ss, 372 * ss), "-37%", font=F("Black", 42 * ss), fill=WHITE, anchor="mm")
        d.text((wd * ss / 2, 456 * ss), "Percuma pos  •  Bayar masa terima (COD)", font=F("SemiBold", 34 * ss), fill=(60, 60, 66), anchor="mm")
    arr = np.asarray(shadow(Image.fromarray(sprite_from(dr, wd, ht)), 22, 12, 110)); cache[key] = arr; return arr

def arrow_sprite():
    key = ("arrow",)
    if key in cache: return cache[key]
    wd = ht = 130
    def dr(d, ss):
        d.polygon([(65 * ss, 120 * ss), (10 * ss, 50 * ss), (45 * ss, 50 * ss), (45 * ss, 6 * ss), (85 * ss, 6 * ss),
                   (85 * ss, 50 * ss), (120 * ss, 50 * ss)], fill=GOLD, outline=(10, 10, 12), width=5 * ss)
    arr = np.asarray(shadow(Image.fromarray(sprite_from(dr, wd, ht)), 8, 5, 140)); cache[key] = arr; return arr

# ---------- main render ----------
def main():
    # sumber
    T0, T1 = (float(x) for x in os.environ.get("PREVIEW", f"0,{TOTAL}").split(","))
    pm = reader(MAIN, T0, T1 - T0, False)
    photos = {k: load_photo(v) for k, v in PHOTO.items()}
    active_clip = {"key": None, "p": None, "buf": []}
    enc = sp.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                    "-i", "-", "-an", "-c:v", "libx264", "-preset", os.environ.get("PRESET", "slow"), "-crf", "17", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-profile:v", "high", "-movflags", "+faststart", OUT + ".noaudio.mp4"], stdin=sp.PIPE)
    clip_readers = {}
    for i in range(int(T0 * FPS), int(T1 * FPS)):
        t = i / FPS
        m = read_frame(pm)
        if m is None: m = np.zeros((H, W, 3), np.uint8)
        frame = np.array(m)  # salinan boleh tulis
        # ZOOM halus pada video utama (punch-in hook)
        c, ca = cut_alpha(t)
        if c is not None:
            kind, src, prm = c[2], c[3], c[4]
            lt = t - c[0]; dur = c[1] - c[0]
            if kind == "clip":
                key = (src, c[0])
                if key not in clip_readers:
                    clip_readers[key] = reader(CLIP[src], prm + max(0.0, T0 - c[0]) if False else prm, dur + 0.3, True)
                b = read_frame(clip_readers[key])
                if b is None: b = frame
                z = 1.0 + 0.07 * (lt / dur)
                b = zoom(b, z) if z > 1.001 else b
            else:
                z0, z1, cx, cy = prm
                z = z0 + (z1 - z0) * ease_io(lt / dur)
                b = photo_frame(photos[src], z, cx, cy)
            # whip: bawa sedikit zoom punch masa transisi
            a = ca
            frame = (frame.astype(np.float32) * (1 - a) + b.astype(np.float32) * a).astype(np.uint8)
        draw_overlay(frame, t, (c, ca))
        # subtitle
        for (a0, a1, tx, hi) in SUBS:
            if a0 <= t < a1:
                sc = ease_back((t - a0) / 0.22, 1.4) if t - a0 < 0.22 else 1.0
                blit(frame, sub_sprite(tx, hi), W // 2, 1395, 0.9 + 0.1 * sc, clamp((t - a0) / 0.08))
                break
        enc.stdin.write(frame.tobytes())
        if i % 150 == 0: print(f"frame {i}/{NF}", flush=True)
    enc.stdin.close(); enc.wait()
    pm.stdout.close()
if __name__ == "__main__":
    main()
