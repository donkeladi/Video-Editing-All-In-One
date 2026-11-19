"""Timeline projek Eye Care (semua masa = saat pada audio sumber, ASR word-level; ±0.1-0.2s)."""
FPS = 30
SRC_END = 58.83          # tamat footage
LAST_WORD = 56.54        # perkataan terakhir dituturkan
DUR = 59.70              # 3.16s selepas perkataan terakhir (end card)
NF = int(round(DUR * FPS))

# warna disampel daripada gambar kotak (median piksel)
PURPLE = (0x4C, 0x36, 0x7A)      # foto kotak sebenar, 20% ungu tergelap
TEAL = (0x7D, 0xCC, 0xCE)        # render bersih, jalur teal kotak
PURPLE_DARK = (0x2E, 0x20, 0x50) # diterbitkan: PURPLE x0.6 (latar sahaja)

SEGMENTS = [("L1", 0.0, 4.32), ("S", 4.32, 21.30), ("L1", 21.30, 23.40),
            ("S", 23.40, 50.94), ("L1", 50.94, 56.54), ("S", 56.54, DUR)]
ZOOM_THROUGH = [4.32, 21.30, 56.54]          # 0.15s keluar + 0.15s masuk
PUNCH = [2.40, 10.88, 50.28]                 # rugi / vitamin / tradisional
FLASHES = [21.46, 43.82, 56.54]
SLAMS = [dict(t0=0.0, t1=1.90, lines=["[MENTAH]", "JE?"]),
         dict(t0=21.46, t1=23.10, lines=["LARUT", "[LEMAK]"])]

# kapsyen: (mula, tamat, teks) — [..] = kata kunci (kotak teal). Ikut audio, ejaan standard.
CAPTIONS = [
 (0.00, 1.16, "Korang yang mana"), (1.16, 2.40, "suka [lobak merah]"),
 (2.40, 3.40, "[rugi] kalau makan"), (3.40, 4.32, "macam tu sahaja"),
 (4.32, 5.90, "Sebab apa dalam"), (5.90, 6.84, "[lobak merah] dia"),
 (6.84, 7.40, "kaya dengan"), (7.40, 8.40, "[beta-karotin]"),
 (8.40, 9.54, "yang membantu badan"), (9.54, 10.88, "tukarkan ia jadi"),
 (10.88, 12.06, "[vitamin A]"), (12.08, 13.40, "Yang penting ia"),
 (13.40, 13.92, "juga untuk"), (13.92, 15.02, "[penglihatan malam]"),
 (15.02, 15.56, "dan juga"), (15.56, 17.30, "[daya tahan] badan"),
 (17.52, 18.48, "Masalah yang"), (18.48, 19.00, "dekat sini"),
 (19.00, 20.40, "[karotenoid]"), (20.44, 21.46, "[karotenoid] ini"),
 # 21.46-23.10 : slam "LARUT LEMAK" menggantikan kapsyen
 (23.10, 25.06, "Manual [MSD] cakap"), (25.06, 26.46, "ia paling baik"),
 (26.46, 27.86, "diserap daripada sayur"), (27.86, 28.74, "yang dimasak dengan"),
 (28.74, 29.64, "sedikit [lemak]"), (29.64, 30.44, "ataupun [minyak]"),
 (30.44, 32.76, "[Avokado] pun ada"), (32.76, 33.64, "sumber [lemak]"),
 (33.64, 34.44, "yang baik"), (34.44, 35.66, "[Berita Harian]"),
 (35.66, 36.30, "ada tulis"), (36.30, 37.52, "ia membantu serap"),
 (37.52, 38.84, "[lemak] yang larut"), (38.84, 40.20, "Ada tertulis dalam"),
 (40.20, 41.62, "[Berita Harian 2019]"), (41.62, 42.56, "kalau tak"),
 (42.56, 43.28, "silap saya"), (43.28, 44.36, "Dalam DS Pharma"),
 (44.36, 45.18, "[Eye Care] pun"), (45.18, 46.28, "ada [lobak merah]"),
 (46.28, 47.00, "dan [avokado]"), (47.00, 48.58, "berdaftar dengan [MAL]"),
 (48.58, 49.62, "dan digunakan"), (49.62, 50.94, "secara [tradisional]"),
 (50.94, 52.40, "untuk [kesihatan mata]"),
 # 52.72-56.54 : TIDAK dikapsyen (ayat ajakan tiada dalam brief + perkataan tak jelas)
]

# elemen grafik (overlay / kad / chip)
ELEMENTS = [
 dict(id="carrot_hook", kind="icon", name="carrot", t0=1.44, t1=4.20, cx=872, cy=650, size=170),
 dict(id="carrot_big", kind="icon", name="carrot", t0=4.50, t1=7.30, cx=510, cy=580, size=380),
 dict(id="card_a", kind="card_a", t0=7.40, t1=17.90),
 dict(id="src_kemenkes", kind="src", text="Sumber: Kemenkes Indonesia", t0=10.88, t1=17.90),
 dict(id="chip_night", kind="chip", text="penglihatan malam", t0=13.92, t1=17.90, cx=510, cy=745),
 dict(id="chip_imun", kind="chip", text="daya tahan badan", t0=15.56, t1=17.90, cx=510, cy=835),
 dict(id="particle_intro", kind="particle", t0=19.00, t1=21.30, orbit=False),
 dict(id="chip_karot", kind="chip", text="karotenoid", t0=19.20, t1=21.30, cx=510, cy=760),
 dict(id="oil_scene", kind="particle", t0=23.40, t1=30.44, orbit=True, pan=True),
 dict(id="src_msd", kind="src", text="Sumber: MSD Manual (versi Indonesia)", t0=23.98, t1=28.60),
 dict(id="avocado", kind="icon", name="avocado", t0=30.44, t1=43.20, cx=310, cy=590, size=380),
 dict(id="chip_lemak", kind="chip", text="lemak baik", t0=33.32, t1=43.20, cx=745, cy=590),
 dict(id="src_bh", kind="src", text="Sumber: Berita Harian 2019", t0=34.80, t1=38.90),
 dict(id="product", kind="photo", name="front", t0=43.82, t1=50.94, cx=510, cy=575, h=450),
 dict(id="chip_mal", kind="chip", text="Berdaftar [MAL22076147T]", t0=47.00, t1=50.94, cx=510, cy=850),
 dict(id="endcard", kind="endcard", t0=56.54, t1=DUR),
]

def sfx_cues():
    """(masa, jenis, gain_dB) — SFX procedural."""
    c = []
    for s in SLAMS: c.append((s["t0"], "slam", -9))
    for T in ZOOM_THROUGH: c.append((T - 0.15, "whoosh", -17))
    for e in ELEMENTS:
        k = e["kind"]
        if k in ("icon", "photo", "particle", "card_a", "endcard"): c.append((e["t0"], "pop", -19))
        elif k in ("chip", "src"): c.append((e["t0"], "tick", -24))
    for t in FLASHES: c.append((t, "shimmer", -23))
    c.append((23.40, "sizzle", -31))
    return sorted(c)
