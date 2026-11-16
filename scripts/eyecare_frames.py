#!/usr/bin/env python3
"""Zoom licin (subpixel, easing) + matte orang. Hasil: work/zbase.mp4 (1080x1920) & work/zmatte.mp4 (540x960 gray).
Guna: eyecare_frames.py [mula_saat tamat_saat]  (julat = ujian pantas)"""
import sys, subprocess, numpy as np, os
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from eyecare_matte import matte
W, H, FPS = 1080, 1920, 30
FX, FY = 540.0, 700.0
# (masa, zoom) — easing smoothstep antara kunci; ramp >= 0.5s supaya tak bergetar
ZK = [(0,1.10),(1.8,1.04),(3.6,1.07),(4.3,1.16),(5.0,1.16),(6.0,1.05),(9.8,1.12),(10.4,1.12),(11.0,1.17),(12.9,1.17),
      (13.6,1.05),(16.8,1.13),(17.4,1.03),(18.6,1.03),(19.4,1.11),(20.9,1.11),(21.4,1.04),(23.5,1.14),(23.6,1.04),
      (28.7,1.08),(29.4,1.16),(31.3,1.16),(31.9,1.06),(36.0,1.10),(36.6,1.05),(40.9,1.11),(41.5,1.05),(41.9,1.05),
      (45.0,1.17),(45.5,1.05),(47.2,1.05),(49.2,1.11),(50.6,1.05),(52.9,1.14),(53.5,1.04),(53.7,1.04),(56.6,1.17)]
def zoom(t):
    if t <= ZK[0][0]: return ZK[0][1]
    for (t0, z0), (t1, z1) in zip(ZK, ZK[1:]):
        if t < t1:
            u = (t - t0) / (t1 - t0); u = u * u * (3 - 2 * u)
            return z0 + (z1 - z0) * u
    return ZK[-1][1]
def aff(z, fx, fy):  # keluaran->masukan: p_in = anchor + (p_out-anchor)/z
    return (1 / z, 0, fx - fx / z, 0, 1 / z, fy - fy / z)
if __name__ == "__main__":
    t0 = float(sys.argv[1]) if len(sys.argv) > 2 else 0.0
    t1 = float(sys.argv[2]) if len(sys.argv) > 2 else 1e9
    tag = "_test" if len(sys.argv) > 2 else ""
    dec = subprocess.Popen(["ffmpeg","-v","error","-ss",str(t0),"-i","work/cut.mp4","-t",str(t1-t0) if t1<1e8 else "999","-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
    eb = subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-crf","12","-preset","veryfast","-pix_fmt","yuv420p",f"work/zbase{tag}.mp4"],stdin=subprocess.PIPE)
    em = subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","gray","-s",f"{W//2}x{H//2}","-r",str(FPS),"-i","-","-c:v","libx264","-crf","10","-preset","veryfast","-pix_fmt","yuv420p",f"work/zmatte{tag}.mp4"],stdin=subprocess.PIPE)
    n = 0; prev = None; fs = W * H * 3
    while True:
        buf = dec.stdout.read(fs)
        if len(buf) < fs: break
        t = t0 + n / FPS; z = zoom(t)
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        im = Image.fromarray(fr)
        small = np.asarray(im.resize((W // 2, H // 2), Image.BILINEAR))
        m = matte(small)
        if prev is not None: m = 0.6 * m + 0.4 * prev
        prev = m
        mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
        mi = mi.transform((W // 2, H // 2), Image.AFFINE, aff(z, FX / 2, FY / 2), Image.BILINEAR)
        out = im.transform((W, H), Image.AFFINE, aff(z, FX, FY), Image.BICUBIC)
        eb.stdin.write(out.tobytes()); em.stdin.write(mi.tobytes()); n += 1
        if n % 100 == 0: print(n, flush=True)
    eb.stdin.close(); em.stdin.close(); eb.wait(); em.wait(); print("done", n)
