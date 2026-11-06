#!/usr/bin/env python3
"""Candia chalkboard TikTok: video utama dalam bingkai papan hitam, HDR->SDR, caption kapur.
Guna: python3 scripts/build_chalkboard.py   (sumber di UPLOADS, hasil output/candia_chalkboard.mp4)
"""
import subprocess, re, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

U = "/root/.claude/uploads/b67edffa-698a-5b53-b30f-d33b7e563e32/"
SRC = {"1700": "57f97fac-IMG_1700", "1699": "cc8b997c-IMG_1699_2", "1689": "8f507ccf-IMG_1689",
       "1690": "60525b87-IMG_1690", "1691": "ffc41c8f-IMG_1691", "1692": "266f9166-IMG_1692",
       "1693": "f0eb3433-IMG_1693", "1696": "5c3833a9-IMG_1696", "1694": "2bc833b2-IMG_1694"}
W = "work/cb"; os.makedirs(W, exist_ok=True)
FONT = [p for p in __import__("glob").glob("/usr/local/lib/python3*/site-packages/font_amatic_sc/files/AmaticSC-Bold.ttf")][0]
random.seed(7); np.random.seed(7)

# ---------- video ----------
TM = ("zscale=tin=arib-std-b67:t=linear:npl=100:min=bt2020nc:pin=bt2020:rin=tv,format=gbrpf32le,"
      "tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p")
SC = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p"
ENC = ["-c:v", "libx264", "-crf", "14", "-preset slow".split()[0], "-preset", "slow", "-pix_fmt", "yuv420p",
       "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
ENC = [x for x in ENC if x != "-preset slow".split()[0] or True]
def run(*a): subprocess.run([str(x) for x in a], check=True)
def enc(): return ["-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p",
                   "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                   "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]

def build_video():
    # s1: 1700 (HDR) bahagian bercakap sahaja
    run("ffmpeg", "-y", "-loglevel", "error", "-ss", "0.6", "-to", "6.6", "-i", U + SRC["1700"] + ".mov",
        "-vf", TM + "," + SC, *enc(), W + "/s1.mp4")
    # s2: 1699_2 buang senyap
    inp = U + SRC["1699"] + ".mov"
    log = subprocess.run(["ffmpeg", "-i", inp, "-af", "silencedetect=noise=-40dB:d=0.4", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    dur = float(re.search(r"Duration: \d+:\d+:([\d.]+)", log).group(1)) + 60 * int(re.search(r"Duration: \d+:(\d+)", log).group(1))
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    keep, t = [], 0
    for i, s in enumerate(st):
        if s - t > .05: keep.append((t, s))
        t = en[i] if i < len(en) else dur
    if dur - t > .05: keep.append((t, dur))
    sel = "+".join(f"between(t,{max(a-.12,0):.3f},{b+.12:.3f})" for a, b in keep)
    run("ffmpeg", "-y", "-loglevel", "error", "-i", inp, "-vf", f"select='{sel}',setpts=N/FRAME_RATE/TB,{SC}",
        "-af", f"aselect='{sel}',asetpts=N/SR/TB,aresample=48000", *enc(), W + "/s2.mp4")
    open(W + "/list.txt", "w").write("file s1.mp4\nfile s2.mp4\n")
    run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-i", W + "/list.txt", "-c", "copy", W + "/main.mp4")
    for k in ("1694", "1689", "1690", "1691", "1692", "1693", "1696"):
        run("ffmpeg", "-y", "-loglevel", "error", "-i", U + SRC[k] + ".mov", "-an", "-t", "4",
            "-vf", TM + "," + SC, *[x for x in enc() if x not in ("-c:a", "aac", "-b:a", "192k", "-ar", "48000")], W + f"/b{k}.mp4")

# ---------- chalk art ----------
def font(sz): return ImageFont.truetype(FONT, sz)
def chalkify(mask, rough=0.35):
    a = np.array(mask, dtype=np.float32) / 255
    n = np.random.rand(*a.shape).astype(np.float32)
    n2 = np.array(Image.fromarray((np.random.rand(a.shape[0] // 3 + 1, a.shape[1] // 3 + 1) * 255).astype(np.uint8)).resize(
        (a.shape[1], a.shape[0]), Image.BILINEAR), dtype=np.float32) / 255
    tex = np.clip(1 - rough * (0.6 * n + 0.8 * n2) * 1.6 + 0.12, 0, 1)
    out = a * tex
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
def chalk_layer(size, draw_fn, color, rough=0.35):
    m = Image.new("L", size, 0); draw_fn(ImageDraw.Draw(m))
    m = chalkify(m, rough)
    lay = Image.new("RGBA", size, color + (0,)); lay.putalpha(m); return lay
def text_layer(size, lines, sz, color, y0, spacing=1.0, anchor_x=None):
    def f(d):
        y = y0
        for ln in lines:
            d.text((size[0] / 2 if anchor_x is None else anchor_x, y), ln, font=font(sz), fill=255, anchor="ma")
            y += sz * spacing
    return chalk_layer(size, f, color)
def wobble_rect(d, x0, y0, x1, y1, w=5, j=2):
    def seg(a, b):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / 14)
        pts = [(a[0] + (b[0] - a[0]) * i / n + random.uniform(-j, j), a[1] + (b[1] - a[1]) * i / n + random.uniform(-j, j)) for i in range(n + 1)]
        d.line(pts, fill=255, width=w, joint="curve")
    c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for i in range(4): seg(c[i], c[i + 1])
def star(d, cx, cy, r, w=4):
    import math
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 270, 72)]
    order = [0, 2, 4, 1, 3, 0]
    d.line([pts[i] for i in order], fill=255, width=w, joint="curve")

def make_bg():
    S = (1080, 1920)
    base = np.zeros((1920, 1080, 3), np.float32); base[:] = (31, 46, 42)
    yy, xx = np.mgrid[0:1920, 0:1080]
    vig = 1 - 0.38 * (((xx - 540) / 700) ** 2 + ((yy - 960) / 1200) ** 2)
    base *= vig[..., None]
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    sm = Image.new("L", S, 0); d = ImageDraw.Draw(sm)
    for _ in range(60):   # smudge kapur
        x, y = random.randint(-100, 1100), random.randint(0, 1920)
        d.line([(x, y), (x + random.randint(200, 600), y + random.randint(-80, 80))], fill=random.randint(10, 26), width=random.randint(40, 110))
    sm = sm.filter(ImageFilter.GaussianBlur(30))
    img = Image.composite(Image.new("RGB", S, (200, 215, 205)), img, sm)
    nz = (np.random.rand(1920, 1080, 1) * 14 - 7)
    img = Image.fromarray(np.clip(np.array(img, np.float32) + nz, 0, 255).astype(np.uint8)).convert("RGBA")
    # bingkai kayu
    fr = Image.new("RGBA", S, (0, 0, 0, 0)); fd = ImageDraw.Draw(fr)
    fd.rectangle([0, 0, 1079, 1919], outline=(139, 98, 64, 255), width=34)
    fd.rectangle([34, 34, 1045, 1885], outline=(92, 62, 38, 255), width=4)
    for _ in range(260):
        x = random.randint(0, 1079); y = random.choice([random.randint(0, 30), random.randint(1890, 1919)])
        fd.line([(x, y), (x + random.randint(20, 90), y)], fill=(110, 76, 48, 255), width=1)
    for _ in range(260):
        y = random.randint(0, 1919); x = random.choice([random.randint(0, 30), random.randint(1050, 1079)])
        fd.line([(x, y), (x, y + random.randint(20, 90))], fill=(110, 76, 48, 255), width=1)
    img.alpha_composite(fr)
    WH, YEL, GLD = (244, 244, 238), (255, 221, 110), (240, 200, 120)
    img.alpha_composite(text_layer(S, ["CANDIA"], 205, WH, 14))
    img.alpha_composite(text_layer(S, ["Gold Chain Mesh Sandal"], 86, YEL, 218))
    def sq(d):
        pts = [(220 + i * 12, 316 + (5 if i % 2 else -5)) for i in range(0, 53)]
        d.line(pts, fill=255, width=5, joint="curve")
    img.alpha_composite(chalk_layer(S, sq, YEL))
    def deco(d):
        star(d, 120, 150, 34); star(d, 960, 130, 26); star(d, 995, 215, 16); star(d, 85, 235, 15)
    img.alpha_composite(chalk_layer(S, deco, WH))
    def frm(d): wobble_rect(d, 76, 326 + 8, 1004, 1558 - 6 + 0, w=6, j=2.2)
    img.alpha_composite(chalk_layer(S, frm, WH))
    # sudut kapur kecil bawah
    def bd(d):
        d.line([(300, 1830), (780, 1830)], fill=255, width=4)
    img.alpha_composite(chalk_layer(S, bd, (190, 205, 195), 0.5))
    img.convert("RGB").save(W + "/bg.png")

SW = {"BLACK": "#141414", "TAN": "#b86b2e", "BROWN": "#8f7e6a", "PINK": "#f1a9c6", "CREAM": "#f0e6c8", "GOLD": "#d9b04a"}
def card(name, lines, sz=104, label=None, swatches=None):
    S = (1080, 230)
    lay = Image.new("RGBA", S, (0, 0, 0, 0))
    col = (255, 221, 110) if (label or swatches) else (244, 244, 238)
    if label:
        sz = 150; lines = [label]
    n = len(lines)
    y0 = (S[1] - n * sz * 0.92) / 2 - sz * 0.12 if n == 1 and not label else 14 if n > 1 else 20
    if n == 1 and not label: y0 = 40
    if label: y0 = 4
    if swatches:
        cx0 = 540 - (len(swatches) * 70) / 2 + 35
        lay.alpha_composite(text_layer(S, lines, sz, col, y0 if label else y0, 0.92))
        sw = Image.new("RGBA", S, (0, 0, 0, 0)); sd = ImageDraw.Draw(sw)
        for i, k in enumerate(swatches):
            cx = cx0 + i * 70; cy = 200
            sd.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=SW[k])
        lay.alpha_composite(sw)
        def ring(d):
            for i in range(len(swatches)):
                cx = cx0 + i * 70; d.ellipse([cx - 27, 173, cx + 27, 227], outline=255, width=3)
        lay.alpha_composite(chalk_layer(S, ring, (244, 244, 238), 0.3))
    else:
        lay.alpha_composite(text_layer(S, lines, sz, col, y0, 0.92))
    lay.save(f"{W}/{name}.png")

# ---------- jadual ----------
EV = [
 (0.3, 5.8, "i1", dict(lines=["Sandal Candia Wanita", "Gold Chain TP28111L"])),
 (6.0, 8.4, "k_all", dict(label="5 PILIHAN WARNA", lines=[], swatches=["BLACK", "BROWN", "CREAM", "TAN", "PINK"]), "1694"),
 (8.5, 11.9, "i2", dict(lines=["Rekaan minimalist &", "gold chain premium"])),
 (12.0, 14.2, "k_black", dict(label="BLACK", lines=[], swatches=["BLACK"]), "1689"),
 (14.3, 19.8, "i3", dict(lines=["Soft cushioned insole", "lembut sepanjang hari"])),
 (20.0, 22.2, "k_tan", dict(label="TAN", lines=[], swatches=["TAN"]), "1690"),
 (22.3, 27.8, "i4", dict(lines=["Slip-on: mudah sarung", "tanpa perlu ikat tali"])),
 (28.0, 30.2, "k_brown", dict(label="BROWN", lines=[], swatches=["BROWN"]), "1691"),
 (30.3, 35.8, "i5", dict(lines=["Anti-slip outsole", "lebih stabil & selamat"])),
 (36.0, 38.2, "k_pink", dict(label="PINK", lines=[], swatches=["PINK"]), "1692"),
 (38.3, 43.8, "i6", dict(lines=["Ringan, tak bebankan kaki"])),
 (44.0, 46.2, "k_cream", dict(label="CREAM", lines=[], swatches=["CREAM"]), "1693"),
 (46.3, 51.5, "i7", dict(lines=["Padan dengan dress, skirt,", "jeans & seluar panjang"])),
 (51.5, 55.9, "i8", dict(lines=["5 warna: Black, Brown,", "Cream, Tan, Pink"])),
 (56.0, 59.5, "k_gold", dict(label="GOLD CHAIN", lines=[], swatches=["GOLD"]), "1696"),
 (59.6, 63.5, "i9", dict(lines=["Saiz tersedia:", "36 | 37 | 38 | 39 | 40 | 41"])),
 (63.5, 68.5, "i10", dict(lines=["PERHATIAN: Cutting kecil &", "bahagian depan sedikit sempit"])),
 (68.5, 73.0, "i11", dict(lines=["Kaki normal: ambil 1 size lebih besar", "Kaki lebar/kembang: up 2 size"], sz=92)),
 (73.0, 76.5, "i12", dict(lines=["Antara dua saiz?", "Pilih saiz yang lebih besar"])),
 (76.5, 80.2, "i13", dict(lines=["Sesuai untuk jalan-jalan,", "shopping & travel"])),
]

def compose():
    make_bg()
    D = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", W + "/main.mp4"],
                             capture_output=True, text=True).stdout)
    inputs = ["-loop", "1", "-framerate", "30", "-t", f"{D}", "-i", W + "/bg.png", "-i", W + "/main.mp4"]
    fc = ["[1:v]scale=900:1600,crop=900:1200:0:70,unsharp=5:5:0.45:3:3:0.0,eq=contrast=1.04:saturation=1.08[m]",
          "[0:v][m]overlay=90:340:format=auto[b0]"]
    idx, last = 2, "b0"
    for ev in EV:
        s, e, name, kw = ev[:4]
        kk = ev[4] if len(ev) > 4 else None
        card(name, **kw)
        if kk:
            inputs += ["-i", f"{W}/b{kk}.mp4"]
            fc.append(f"[{idx}:v]trim=0:{e-s:.2f},setpts=PTS-STARTPTS+{s}/TB,scale=900:1600,crop=900:1200:0:170,"
                      f"unsharp=5:5:0.45:3:3:0.0,eq=contrast=1.04:saturation=1.08[v{idx}]")
            fc.append(f"[{last}][v{idx}]overlay=90:340:enable='between(t,{s},{e})':eof_action=pass[o{idx}]")
            last = f"o{idx}"; idx += 1
        inputs += ["-loop", "1", "-framerate", "30", "-t", f"{e-s+0.2:.2f}", "-i", f"{W}/{name}.png"]
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d=0.15:alpha=1,fade=t=out:st={e-s-0.15:.2f}:d=0.15:alpha=1,setpts=PTS-STARTPTS+{s}/TB[c{idx}]")
        fc.append(f"[{last}][c{idx}]overlay=0:1572:enable='between(t,{s},{e})':eof_action=pass[o{idx}]")
        last = f"o{idx}"; idx += 1
    fc.append(f"[{last}]format=yuv420p[v]")
    open(W + "/fc.txt", "w").write(";".join(fc))
    os.makedirs("output", exist_ok=True)
    run("ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex_script", W + "/fc.txt",
        "-map", "[v]", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
        "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{D}", "output/candia_chalkboard.mp4")

if __name__ == "__main__":
    import sys
    if "--skip-video" not in sys.argv: build_video()
    compose()
    print("output/candia_chalkboard.mp4")
