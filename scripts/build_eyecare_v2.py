#!/usr/bin/env python3
"""Render v2: penyampai SAIZ ASAL (matte MODNet) di hadapan; semua grafik di BELAKANG (latar jenama bergerak + infografik).
Guna: build_eyecare_v2.py <video> <out_dir> [--frames a,b,c] [--workers N]   (perlukan work/matte/ daripada eyecare_matte.py)"""
import sys, os, json, math, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import build_eyecare as v1
from build_eyecare import (text_sprite, node_sprite, label_sprite, tracker_sprite, line_layer, paste_layer, paste, anim, fade, eo, ei, eo_back,
                           svg_png, rr, font, photo_sprite, round_photo, chip_sprite, src_sprite, caption_sprite, punch, zoomfx,
                           MONT7, MONT8, MONT9, NOTO6, read_frames, FACE_RAW)
from eyecare_timeline_v2 import *

W, H = 1080, 1920
ROOT = v1.ROOT; MATTE = os.path.join(ROOT, "work/matte")
DY = 290            # anjak penyampai ke bawah (saiz kekal 1.0) untuk ruang grafik di atas kepala
FY = 760            # titik tumpu push/punch
FREEZE = v1.FREEZE
PUSH = 0.035; PUNCH_AMT = 0.12

# ------------------------------------------------------------------ matte
@functools.lru_cache(8)
def matte_raw(i):
    i = min(max(i, 0), FREEZE)
    return cv2.imread(f"{MATTE}/{i:05d}.png", cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
def matte(i):
    a = 0.25 * matte_raw(i - 1) + 0.5 * matte_raw(i) + 0.25 * matte_raw(i + 1)         # penghalusan masa
    a = cv2.resize(a, (W, H), interpolation=cv2.INTER_CUBIC).clip(0, 1)
    a = ((a - 0.22) / 0.62).clip(0, 1)                                               # ketatkan tepi (kurangkan jidar langsir)
    a = a * a * (3 - 2 * a)
    return cv2.GaussianBlur(a, (0, 0), 0.9)

# ------------------------------------------------------------------ sprite v2
@functools.lru_cache(None)
def slam_sprite2(i):
    from build_eyecare import stack
    return stack([text_sprite(l, MONT9, 118, stroke=8, px=18, py=8, max_w=800, boxr=18) for l in SLAMS[i]["lines"]], gap=4)
@functools.lru_cache(None)
def pill2_sprite(icon, l1, l2):
    w, h = 270, 106; im = rr(w, h, 30, (255, 255, 255, 247)); ic = svg_png(icon, 46); im.alpha_composite(ic, (18, (h - ic.height) // 2))
    d = ImageDraw.Draw(im); d.text((76, 34), l1, font=font(MONT7, 28), fill=v1.PURPLE_DARK + (255,), anchor="lm"); d.text((76, 70), l2, font=font(MONT7, 28), fill=v1.PURPLE_DARK + (255,), anchor="lm"); return im
@functools.lru_cache(None)
def ing2_sprite(icon, name, tag, mg):
    w, h = 250, 215; im = rr(w, h, 30, (255, 255, 255, 247)); ic = svg_png(icon, 78); im.alpha_composite(ic, ((w - ic.width) // 2, 12))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 118), name, font=font(MONT7, 26), fill=v1.PURPLE_DARK + (255,), anchor="mm")
    d.text((w / 2, 158), mg, font=font(MONT9, 46), fill=v1.PURPLE + (255,), anchor="mm")
    d.text((w / 2, 196), tag, font=font(NOTO6, 22), fill=(110, 100, 140, 255), anchor="mm"); return im
@functools.lru_cache(None)
def chipS_sprite(text):
    t = text_sprite(text, MONT7, 30, fill=v1.PURPLE_DARK, px=6, py=4, boxr=8); w, h = t.width + 36, t.height + 20
    im = rr(w, h, h // 2, (255, 255, 255, 245)); im.alpha_composite(t, (18, 10)); return im
@functools.lru_cache(None)
def end2_parts():
    ph = photo_sprite("back", 190)
    l1 = text_sprite("DS Pharma", MONT8, 46, px=6, py=4); l2 = text_sprite("[Eye Care]", MONT8, 46, px=14, py=6)
    sub = [text_sprite(s_, NOTO6, 28, px=2, py=2) for s_ in ("Digunakan secara", "tradisional untuk", "kesihatan mata")]
    return ph, l1, l2, sub, chipS_sprite("MAL22076147T")
@functools.lru_cache(None)
def label2(text): return text_sprite(text, MONT7, 36, fill=(255, 255, 255), stroke=0, px=12, py=6, boxr=12)
@functools.lru_cache(None)
def src2(text):
    f = font(NOTO6, 36); w = int(f.getlength(text)) + 64; h = 66
    im = rr(w, h, 33, (24, 14, 52, 215), (255, 255, 255, 170), 2); ImageDraw.Draw(im).text((32, h // 2 + 1), text, font=f, fill=(255, 255, 255, 255), anchor="lm"); return im


# ------------------------------------------------------------------ bahan rujukan sebenar (foto bahan + petikan akhbar yang dibekalkan pengguna)
REF = os.path.join(ROOT, "assets/ref/")
@functools.lru_cache(None)
def ref(name): return Image.open(REF + name).convert("RGB")
def cover(img, w, h, fx, fy, zoom=1.0):
    iw, ih = img.size; sc = max(w / iw, h / ih) * zoom; cw, ch = w / sc, h / sc
    x0 = min(max(fx * iw - cw / 2, 0), iw - cw); y0 = min(max(fy * ih - ch / 2, 0), ih - ch)
    return img.resize((w, h), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
PHOTO = {"carrot": ("carrot.webp", 0.45, 0.62, 1.7), "avocado": ("avocado.webp", 0.52, 0.58, 1.5), "goji": ("goji.webp", 0.62, 0.45, 1.3), "eyebright": ("eyebright.jpg", 0.50, 0.40, 1.15)}
def circ_photo(name, d):
    f, fx, fy, z = PHOTO[name]; im = cover(ref(f), d, d, fx, fy, z).convert("RGBA")
    m = Image.new("L", (d * 3, d * 3), 0); ImageDraw.Draw(m).ellipse((0, 0, d * 3 - 1, d * 3 - 1), fill=255); im.putalpha(m.resize((d, d), Image.LANCZOS)); return im
@functools.lru_cache(None)
def node_photo_sprite(name, r):
    D = 2 * r + 16; im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    sh = Image.new("RGBA", (D, D), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((8, 14, D - 8, D - 2), fill=(0, 0, 0, 70)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    k = 3; c = Image.new("RGBA", (D * k, D * k), (0, 0, 0, 0)); ImageDraw.Draw(c).ellipse((8 * k, 8 * k, (D - 8) * k, (D - 8) * k), fill=(255, 255, 255, 255))
    im.alpha_composite(c.resize((D, D), Image.LANCZOS)); ph = circ_photo(name, 2 * r - 12); im.alpha_composite(ph, (D // 2 - ph.width // 2, D // 2 - ph.height // 2)); return im
@functools.lru_cache(None)
def tile_sprite(name, label, tag, mg):
    w, h = 205, 215; im = rr(w, h, 26, (255, 255, 255, 250))
    f, fx, fy, z = PHOTO[name]; ph = cover(ref(f), w, 112, fx, fy, z).convert("RGBA")
    m = Image.new("L", (w * 3, 112 * 3), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 3 - 1, 112 * 3 + 80), 26 * 3, fill=255); ph.putalpha(m.resize((w, 112), Image.LANCZOS)); im.alpha_composite(ph, (0, 0))
    d = ImageDraw.Draw(im); d.text((w / 2, 134), label, font=font(MONT7, 24), fill=v1.PURPLE_DARK + (255,), anchor="mm")
    d.text((w / 2, 168), mg, font=font(MONT9, 38), fill=v1.PURPLE + (255,), anchor="mm"); d.text((w / 2, 199), tag, font=font(NOTO6, 20), fill=(110, 100, 140, 255), anchor="mm"); return im
@functools.lru_cache(None)
def article_sprite():
    from PIL import ImageChops
    b1, b3 = ref("bh1.png"), ref("bh3.png")
    logo = b1.crop((515, 205, 700, 375)); head = b1.crop((40, 575, 905, 800)); date = b1.crop((40, 925, 500, 990)); q = b3.crop((30, 1995, 1140, 2155)).convert("RGB")
    hl = Image.new("RGB", q.size, (255, 255, 255)); ImageDraw.Draw(hl).rounded_rectangle((14, 83, 482, 153), 14, fill=TEAL)   # serlah "menyerap lemak larut"
    q = ImageChops.multiply(q, hl)
    sz = lambda im, k: im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    logo, head, date, q = sz(logo, 0.47), sz(head, 0.47), sz(date, 0.56), sz(q, 0.76)
    W2, H2 = 880, 302; card = rr(W2, H2, 30, (255, 255, 255, 252)).convert("RGBA")
    card.alpha_composite(logo.convert("RGBA"), (22, 16)); card.alpha_composite(head.convert("RGBA"), (122, 14)); card.alpha_composite(date.convert("RGBA"), (122, 124))
    card.alpha_composite(q.convert("RGBA"), (18, 168)); av = circ_photo("avocado", 108); card.alpha_composite(av, (W2 - 108 - 36, 22)); return card

# ------------------------------------------------------------------ latar
@functools.lru_cache(None)
def bg_base():
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array(PURPLE_DARK, float)[None, None]; b = np.array((0x3B, 0x2A, 0x66), float)[None, None]
    g = (a + (b - a) * y) * np.ones((1, W, 1))
    xx = np.linspace(-1, 1, W)[None, :, None]; g = g * (1 - 0.14 * xx ** 2)
    ys, xs = np.mgrid[0:H, 0:W]; dots = ((xs % 54) < 3) & ((ys % 54) < 3)
    g[dots] = g[dots] * 0.85 + 255 * 0.15
    return g.clip(0, 255).astype(np.uint8)
def bokeh(t):
    lay = Image.new("RGBA", (270, 480), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(7):
        x = (60 + k * 41 + 18 * math.sin(t * 0.35 + k * 1.3)) % 300 - 15; y = (40 + k * 67 - t * (3 + k % 3)) % 520 - 20; r = 26 + 14 * (k % 3)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 12 + 5 * (k % 3)))
    return lay.resize((W, H), Image.BICUBIC)
def ghost(cv, t, e):
    a = fade(t, e["t0"], e["t1"], 0.5, 0.4) * 0.19
    if a <= 0: return
    ang = e.get("ang", 0) + 5 * math.sin(t * 0.25); spr = svg_png(e["name"], 860).rotate(ang, resample=Image.BICUBIC, expand=True)
    paste(cv, spr, e.get("gx", 540) + 14 * math.sin(t * 0.2), e.get("gy", 1130) + 10 * math.cos(t * 0.17), 1.0, a)

# ------------------------------------------------------------------ elemen belakang
def steam2(cv, t, cx, yb):
    lay = Image.new("RGBA", (300, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k, ox in enumerate((90, 150, 210)):
        ph = t * 2.2 + k * 1.7; pts = [(ox + 9 * math.sin(yy * 0.07 + ph), yy) for yy in range(104, 6, -5)]
        for q in range(len(pts) - 1):
            al = int(150 * math.sin(math.pi * q / len(pts)) * (0.6 + 0.4 * math.sin(ph + q * .3))); d.line((pts[q], pts[q + 1]), fill=(255, 255, 255, max(0, al)), width=8)
    paste(cv, lay.filter(ImageFilter.GaussianBlur(1.1)), cx, yb - 55)
def scene2(cv, t, e, R):
    a, s = anim(t, e["t0"], e["t1"], tin=0.40)
    if a <= 0: return
    cx, cy = 285, 490; bob = 4 * math.sin(t * 2.6)
    paste(cv, svg_png("particle", 250), cx, cy + bob, s, a, R)
    for k in range(7):
        ang = (t - e["t0"]) * 1.5 + k * 2 * math.pi / 7; ox, oy = 150 * math.cos(ang), 58 * math.sin(ang); dp = 0.8 + 0.2 * math.sin(ang)
        paste(cv, svg_png("droplet", 58), cx + ox * s, cy + oy * s + bob, s * dp, a, R)
    paste(cv, svg_png("pan", 400), 715, 545, s, a, R); steam2(cv, t, 715, 500)

def draw_bg_elements(cv, t, R):
    for e in ELEMENTS:
        if not (e["t0"] <= t < e["t1"]): continue
        k = e["kind"]; a, s = anim(t, e["t0"], e["t1"])
        if k == "ghost": ghost(cv, t, e)
        elif k == "icon": paste(cv, svg_png(e["name"], e["size"]), e["cx"], e["cy"] + 5 * math.sin((t - e["t0"]) * 3), s, a, R)
        elif k == "tracker": paste(cv, tracker_sprite(e["step"], e["title"]), 510, 300, 1.0, fade(t, e["t0"], e["t1"], 0.15, 0.10), R)
        elif k == "photoicon": paste(cv, node_photo_sprite(e["name"], e["d"] // 2), e["cx"], e["cy"] + 5 * math.sin((t - e["t0"]) * 3), s, a, R)
        elif k == "tile": paste(cv, tile_sprite(e["name"], e["label"], e["tag"], e["mg"]), e["cx"], e["cy"], s, a, R)
        elif k == "article": paste(cv, article_sprite(), e["cx"], e["cy"], s, a, R)
        elif k == "node":
            r = e["r"]; paste(cv, node_photo_sprite(e["icon"][:-6], r) if e["icon"].endswith("_photo") else node_sprite(e["icon"], r), e["cx"], e["cy"], s, a, R)
            a2, s2 = anim(t, e["t0"] + 0.10, e["t1"]); paste(cv, label2(e["label"]), e["cx"], e["cy"] + r + 42, s2, a2, R)
        elif k == "line":
            p = eo((t - e["t0"]) / 0.35); lay, (ox, oy) = line_layer(e["pts"], p); paste_layer(cv, lay, ox, oy, fade(t, e["t0"], e["t1"]), R)
        elif k == "pill2": paste(cv, pill2_sprite(e["icon"], e["l1"], e["l2"]), e["cx"], e["cy"], s, a, R)
        elif k == "scene2": scene2(cv, t, e, R)
        elif k == "tag": paste(cv, label2(e["text"]), e["cx"], e["cy"], s, a, R)
        elif k == "photo": paste(cv, photo_sprite(e["name"], e["h"]), e["cx"], e["cy"], s, a, R)
        elif k == "chipS": paste(cv, chipS_sprite(e["text"]), e["cx"], e["cy"], s, a, R)
        elif k == "ing2": paste(cv, ing2_sprite(e["icon"], e["name"], e["tag"], e["mg"]), e["cx"], e["cy"], s, a, R)
        elif k == "end2":
            ph, l1, l2, sub, mal = end2_parts()
            paste(cv, ph, 245, 465, s, a, R)
            for dl, spr, cx, cy in ((0.10, l1, 740, 400), (0.18, l2, 740, 458), (0.28, sub[0], 830, 548), (0.28, sub[1], 830, 582), (0.28, sub[2], 830, 616), (0.38, mal, 237, 600)):
                a2, s2 = anim(t, e["t0"] + dl, e["t1"] + 1, tout=0.01); paste(cv, spr, cx, cy, s2, a2, R)
def draw_slams(cv, t, R):
    for i, s in enumerate(SLAMS):
        if not (s["t0"] <= t < s["t1"]): continue
        d = t - s["t0"]; a = 1.0 if d < 0.1 else min(1, 0.4 + d / 0.1)
        sc = 1 + 0.10 * (1 - eo_back(d / 0.30, 1.4)) if d < 0.45 else 1
        if t > s["t1"] - 0.12: q = (t - (s["t1"] - 0.12)) / 0.12; a *= 1 - q; sc *= 1 - 0.06 * q
        sh = 0 if d > 0.18 else 7 * math.sin(d * 140) * (1 - d / 0.18)
        paste(cv, slam_sprite2(i), 510 + sh, 405, sc, a, R)

# ------------------------------------------------------------------ komposisi
def compose(t, i, rgb, R_bg, R_fg):
    fi = min(i, FREEZE)
    g = Image.fromarray(bg_base()); g.paste(bokeh(t).convert("RGB"), (0, 0), bokeh(t).getchannel("A"))
    draw_bg_elements(g, t, R_bg); draw_slams(g, t, R_bg)
    n, s0, s1 = 0, 0, 0
    prog = min(t / 56.54, 1) if t < 56.54 else 1
    sc = (1 + PUSH * prog) * (1 + PUNCH_AMT * punch(t))
    M = np.array([[sc, 0, 540 * (1 - sc)], [0, sc, FY * (1 - sc) + DY]], np.float32)
    pres = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    al = cv2.warpAffine(matte(fi), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None]
    out = (np.asarray(g, np.float32) * (1 - al) + pres.astype(np.float32) * al).astype(np.uint8)
    cv = Image.fromarray(out)
    # depan: kapsyen + chip sumber (jauh dari muka)
    for e in ELEMENTS:
        if e["kind"] == "src" and e["t0"] <= t < e["t1"]:
            a, s = anim(t, e["t0"], e["t1"]); paste(cv, src2(e["text"]), 510, 1465, s, a, R_fg)
    for k, (a0, a1, _) in enumerate(v1.CAPTIONS):
        if a0 <= t < a1:
            d = t - a0; alp = min(1, d / 0.08); s2 = 0.85 + 0.15 * eo_back(d / 0.30, 1.2)
            if t > a1 - 0.10: alp *= max(0, (a1 - t) / 0.10)
            paste(cv, caption_sprite(k), 510, 1370, s2, alp, R_fg)
    for ft in FLASHES:
        d = t - ft
        if 0 <= d < 0.12: cv = Image.blend(cv, Image.new("RGB", (W, H), (255, 255, 255)), 0.45 * (1 - d / 0.12))
    rx, ry, rw, rh = FACE_RAW[fi]
    fx0, fy0 = M[0, 0] * rx + M[0, 2], M[1, 1] * ry + M[1, 2]
    return cv, (fx0, fy0, fx0 + rw * sc, fy0 + rh * sc)

def render_frame(i, rgb):
    t = i / v1.FPS; Rb, Rf = [], []
    for T in ZOOM_THROUGH:
        if T - 0.15 <= t < T:
            cv, face = compose(t, i, rgb, Rb, Rf); p = ei((t - (T - 0.15)) / 0.15); return zoomfx(cv, 1 + 0.35 * p, 7 * p), face, Rb, Rf, True
        if T <= t < T + 0.15:
            cv, face = compose(t, i, rgb, Rb, Rf); p = 1 - eo((t - T) / 0.15); return zoomfx(cv, 1 + 0.35 * p, 7 * p), face, Rb, Rf, True
    cv, face = compose(t, i, rgb, Rb, Rf); return cv, face, Rb, Rf, False

def work(args):
    video, a, b, outp = args
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", "30",
        "-x264-params", "keyint=30:min-keyint=30", "-movflags", "+faststart", outp], stdin=subprocess.PIPE)
    log = []
    for k, img in enumerate(read_frames(video, a, b - a)):
        i = a + k; cv, face, Rb, Rf, tr = render_frame(i, np.asarray(img))
        enc.stdin.write(cv.tobytes()); log.append((i, [round(float(v), 1) for v in face], Rb, Rf, tr))
    enc.stdin.close(); enc.wait(); return log

if __name__ == "__main__":
    video, outd = sys.argv[1], sys.argv[2]; os.makedirs(outd, exist_ok=True)
    if "--frames" in sys.argv:
        for fs in sys.argv[sys.argv.index("--frames") + 1].split(","):
            i = int(round(float(fs) * 30)); img = next(read_frames(video, min(i, FREEZE), 1)); cv, *_ = render_frame(i, np.asarray(img)); cv.save(f"{outd}/g_{fs}.png")
        sys.exit()
    nw = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    NF = v1.NF; cuts = [round(NF * k / (nw * 3)) for k in range(nw * 3 + 1)]
    jobs = [(video, cuts[k], cuts[k + 1], f"{outd}/part{k:02d}.mp4") for k in range(nw * 3)]
    from multiprocessing import Pool
    with Pool(nw) as pool: logs = pool.map(work, jobs, chunksize=1)
    allog = [x for l in logs for x in l]; json.dump(allog, open(f"{outd}/framelog.json", "w"))
    with open(f"{outd}/list.txt", "w") as f:
        for j in jobs: f.write(f"file '{os.path.abspath(j[3])}'\n")
    print("ok", len(allog), "frames")
