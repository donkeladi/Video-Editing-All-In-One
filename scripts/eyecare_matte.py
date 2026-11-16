"""Matte orang (kepala/bahu) untuk kad 'di belakang kepala' — tanpa model AI.
Anggar plat langsir: langsir berlipat menegak & kamera statik, jadi tiap lajur diwakili median baris atas kepala.
Skala kerja 540x960. Pulangkan alpha float [0..1] saiz 540x960 (hanya sah dalam ROI y<ROI_Y1)."""
import numpy as np
from PIL import Image, ImageFilter
ROI_Y0, ROI_Y1, ROI_X0 = 140, 380, 125          # baris (skala 540x960): ~y 280..840 pada 1080x1920
PLATE_Y0, PLATE_Y1 = 100, 200      # baris langsir sentiasa kosong (di atas kepala)
def _filt(m, kind, size):
    im = Image.fromarray((m * 255).astype(np.uint8))
    im = im.filter(ImageFilter.MaxFilter(size) if kind == "max" else ImageFilter.MinFilter(size))
    return np.asarray(im) > 127
def matte(frame, thr=34):
    """frame: uint8 (960,540,3)"""
    a = frame.astype(np.int16)
    plate = np.median(a[PLATE_Y0:PLATE_Y1], axis=0)           # (540,3) per lajur
    # trend menegak (langsir sedikit lebih gelap ke bawah) dianggar dari 2 jalur
    d = np.abs(a[ROI_Y0:ROI_Y1] - plate[None]).max(axis=2)
    m = d > thr
    m = _filt(m, "max", 5); m = _filt(m, "min", 5)             # tutup lubang kecil
    m = _filt(m, "min", 5); m = _filt(m, "max", 5)             # buang bintik
    m = _filt(m, "min", 3)                                      # hakis tepi: buang halo langsir
    out = np.zeros(frame.shape[:2], np.float32)
    m[:, :ROI_X0] = False                                       # pokok di kiri bukan orang
    out[ROI_Y0:ROI_Y1] = m
    return out
