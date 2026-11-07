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

# ---------- polaroid pop-up ----------
PW, PH = 460, 580          # kertas polaroid
PX, PY, PPW, PPH = 30, 30, 400, 440   # kawasan gambar
# (mula, tamat, sisi, condong, sumber, param, kapsyen)
# clip: ("clip", no, ss, zoom, cx, cy) ; photo: ("photo", nama, z0, z1, cx, cy)
POLS = [
    (7.60, 10.20, "R", 5, ("clip", 1727, 0.6, 1.0, 0.5, 0.62), "5 pilihan warna"),
    (10.70, 12.35, "L", -5, ("clip", 1729, 1.2, 2.4, 0.22, 0.55), "Tan"),
    (12.45, 14.05, "R", 5, ("clip", 1729, 0.0, 2.4, 0.62, 0.62), "Brown"),
    (17.00, 18.95, "L", -5, ("photo", "trio", 1.2, 1.35, 0.62, 0.78), "Cream"),
    (19.10, 20.90, "R", 5, ("clip", 1729, 7.0, 1.7, 0.45, 0.62), "Pink"),
    (24.50, 26.50, "L", -5, ("clip", 1729, 4.2, 1.7, 0.5, 0.65), "Hitam"),
    (34.00, 37.00, "R", 5, ("clip", 1730, 4.0, 1.25, 0.55, 0.6), "Insole tebal"),
    (38.20, 41.60, "L", -5, ("clip", 1728, 0.2, 1.3, 0.5, 0.6), "Gold chain"),
    (42.80, 45.60, "R", 5, ("photo", "cream_book", 1.5, 1.8, 0.58, 0.66), "PU leather"),
    (47.90, 50.40, "L", -5, ("clip", 1730, 6.5, 1.1, 0.6, 0.65), "Tapak PVC anti-slip"),
]
def polaroid_base(caption):
    key = ("pol", caption)
    if key in cache: return cache[key]
    def dr(d, ss):
        d.rounded_rectangle((0, 0, PW * ss - 1, PH * ss - 1), 10 * ss, fill=(250, 248, 243, 255))
        d.rectangle((PX * ss, PY * ss, (PX + PPW) * ss, (PY + PPH) * ss), fill=(40, 40, 40, 255))
        f = F("ExtraBold", 42 * ss)
        if f.getlength(caption) > (PW - 40) * ss: f = F("ExtraBold", 34 * ss)
        d.text((PW * ss / 2, (PY + PPH + (PH - PY - PPH) / 2) * ss), caption, font=f, fill=(30, 30, 34), anchor="mm")
    arr = sprite_from(dr, PW, PH)
    out = np.asarray(shadow(Image.fromarray(arr), 18, 12, 120)); cache[key] = out; return out
POL_PAD = 54

def pol_content(img, prm):
    """img 1080x1920 -> 400x440 crop."""
    h = int(W * PPH / PPW)
    y0 = (H - h) // 2
    return cv2.resize(img[y0:y0 + h], (PPW, PPH), interpolation=cv2.INTER_AREA)

def draw_polaroid(frame, t, p, content):
    t0, t1, side, tilt, _, cap = p
    spr = polaroid_base(cap).copy()
    spr[POL_PAD + PY:POL_PAD + PY + PPH, POL_PAD + PX:POL_PAD + PX + PPW, :3] = content
    spr[POL_PAD + PY:POL_PAD + PY + PPH, POL_PAD + PX:POL_PAD + PX + PPW, 3] = 255
    cx = 300 if side == "L" else 780; cy = 1010
    inn = (t - t0) / 0.5; out = (t - (t1 - 0.3)) / 0.3
    if inn < 1:
        e = ease_back(inn, 1.5); sc = 0.35 + 0.65 * e; rot = tilt + (-tilt * 3 - 14 if side == "L" else 14) * (1 - e) * 0.6
        dx = (-1 if side == "L" else 1) * 160 * (1 - ease_out(inn)); dy = 160 * (1 - ease_out(inn)); al = clamp(inn * 4)
    else:
        sc, rot, dx, dy, al = 1.0, tilt + 0.9 * math.sin((t - t0) * 3.2), 0, 0, 1
    if out > 0:
        o = ease_io(out); sc *= 1 - 0.12 * o; dy += 70 * o; al *= 1 - o
    blit(frame, spr, cx + dx, cy + dy, sc, al, rot)

SIZES = [36, 37, 38, 39, 40, 41]
def size_chip(sz, hl):
    key = ("size", sz, hl)
    if key in cache: return cache[key]
    wd = ht = 104
    def dr(d, ss):
        fill = (255, 205, 60, 255) if hl else (255, 255, 255, 245)
        d.rounded_rectangle((0, 0, wd * ss - 1, ht * ss - 1), 28 * ss, fill=fill)
        d.text((wd * ss / 2, ht * ss / 2), str(sz), font=F("Black", 50 * ss), fill=INK, anchor="mm")
    arr = np.asarray(shadow(Image.fromarray(sprite_from(dr, wd, ht)), 10, 6, 110)); cache[key] = arr; return arr

def arrow_sprite():
    key = ("arrow",)
    if key in cache: return cache[key]
    wd = ht = 130
    def dr(d, ss):
        d.polygon([(65 * ss, 120 * ss), (10 * ss, 50 * ss), (45 * ss, 50 * ss), (45 * ss, 6 * ss), (85 * ss, 6 * ss),
                   (85 * ss, 50 * ss), (120 * ss, 50 * ss)], fill=GOLD, outline=(10, 10, 12), width=5 * ss)
    arr = np.asarray(shadow(Image.fromarray(sprite_from(dr, wd, ht)), 8, 5, 140)); cache[key] = arr; return arr

def draw_simple(f, t):
    # hook ringkas
    if t < 3.9:
        k = 1 - clamp((t - 3.5) / 0.4)
        s, a = pop(t, 0.25, 0.5)
        blit(f, text_sprite("SANDAL MESH", 112, WHITE, "Black", 10), W // 2, 960, s, a * k)
        s2, a2 = pop(t, 0.5, 0.5)
        blit(f, text_sprite("GOLD CHAIN", 130, GOLD, "Black", 10), W // 2, 1085, s2, a2 * k)
    # saiz: satu kad bersih
    if 50.6 <= t < 55.2:
        k = ease_out((t - 50.6) / 0.35) * (1 - clamp((t - 54.8) / 0.4))
        blit(f, pill("CUTTING KECIL  •  AMBIL UP 1 SIZE", 40, fill=DARK, fg=GOLD, h=92, padx=44),
             W // 2, 930, ease_back((t - 50.6) / 0.45), k)
        gap = 128; x0 = W // 2 - gap * 2.5
        for i, sz in enumerate(SIZES):
            sc, al = pop(t, 51.0 + i * 0.1, 0.45)
            hl = (sz == 37 and t < 52.8) or (sz == 38 and t >= 52.8)
            blit(f, size_chip(sz, hl), x0 + i * gap, 1040, sc * (1.15 if hl else 1), al * k)
        if t > 53.0:
            blit(f, pill("Kaki lebar: UP 2 SIZE", 38, fill=DARK, fg=WHITE, h=84, padx=40), W // 2, 1150,
                 ease_back((t - 53.0) / 0.45), k)
    # CTA
    if t >= 60.9:
        s = ease_back((t - 60.95) / 0.5)
        blit(f, pill("KLIK BEG KUNING", 64, fill=GOLD + (255,), fg=INK, h=140, padx=64), W // 2, 1010, s, 1)
        bob = 18 * math.sin((t - 61) * 7)
        blit(f, arrow_sprite(), W // 2, 1150 + bob, ease_back((t - 61.2) / 0.5), 1)

# ---------- main render ----------
def main():
    T0, T1 = (float(x) for x in os.environ.get("PREVIEW", f"0,{TOTAL}").split(","))
    pm = reader(MAIN, T0, T1 - T0, False)
    photos = {k: load_photo(v) for k, v in PHOTO.items()}
    enc = sp.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                    "-i", "-", "-an", "-c:v", "libx264", "-preset", os.environ.get("PRESET", "slow"), "-crf", "17",
                    "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-profile:v", "high", "-movflags", "+faststart", OUT + ".noaudio.mp4"], stdin=sp.PIPE)
    readers = {}
    for i in range(int(T0 * FPS), int(T1 * FPS)):
        t = i / FPS
        m = read_frame(pm)
        frame = np.array(m) if m is not None else np.zeros((H, W, 3), np.uint8)
        draw_simple(frame, t)
        for idx, p in enumerate(POLS):
            if p[0] <= t < p[1]:
                kind, src = p[4][0], p[4][1]
                if kind == "clip":
                    if idx not in readers:
                        readers[idx] = reader(CLIP[src], p[4][2], p[1] - p[0] + 0.3, True)
                    b = read_frame(readers[idx])
                    if b is None: b = np.zeros((H, W, 3), np.uint8)
                    img = zoom(b, p[4][3], p[4][4], p[4][5])
                else:
                    lt = (t - p[0]) / (p[1] - p[0])
                    img = zoom(photos[src], p[4][2] + (p[4][3] - p[4][2]) * lt, p[4][4], p[4][5])
                draw_polaroid(frame, t, p, pol_content(img, p))
        for (a0, a1, tx, hi) in SUBS:
            if a0 <= t < a1:
                sc = ease_back((t - a0) / 0.22, 1.4) if t - a0 < 0.22 else 1.0
                blit(frame, sub_sprite(tx, hi), W // 2, 1395, 0.9 + 0.1 * sc, clamp((t - a0) / 0.08))
                break
        enc.stdin.write(frame.tobytes())
        if i % 150 == 0: print(f"frame {i}/{int(T1*FPS)}", flush=True)
    enc.stdin.close(); enc.wait()
if __name__ == "__main__":
    main()
