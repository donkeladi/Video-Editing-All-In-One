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

# elemen grafik: gaya infografik carta aliran (nod + anak panah + bar bab)
N1, N2, N3 = 190, 490, 790
ELEMENTS = [
 dict(id="carrot_hook", kind="icon", name="carrot", t0=1.44, t1=4.20, cx=872, cy=650, size=170),
 # bar bab
 dict(id="trk1", kind="tracker", step=1, title="BETA-KAROTIN", t0=4.32, t1=19.00),
 dict(id="trk2a", kind="tracker", step=2, title="LARUT LEMAK", t0=19.00, t1=21.30),
 dict(id="trk2b", kind="tracker", step=2, title="LARUT LEMAK", t0=23.40, t1=30.44),
 dict(id="trk3", kind="tracker", step=3, title="LEMAK BAIK", t0=30.44, t1=43.20),
 dict(id="trk4", kind="tracker", step=4, title="KANDUNGAN", t0=43.28, t1=50.94),
 # bab 1: lobak merah -> beta-karotin -> vitamin A -> dua chip
 dict(id="n_carrot", kind="node", icon="carrot", cx=N1, cy=520, r=95, label="lobak merah", t0=5.90, t1=17.90),
 dict(id="a1", kind="line", pts=[(305, 520), (375, 520)], t0=7.15, t1=17.90),
 dict(id="n_beta", kind="node", icon="particle", cx=N2, cy=520, r=95, label="beta-karotin", t0=7.40, t1=17.90),
 dict(id="a2", kind="line", pts=[(605, 520), (675, 520)], t0=10.55, t1=17.90),
 dict(id="n_vitA", kind="node", icon="A", cx=N3, cy=520, r=95, label="[vitamin A]", t0=10.88, t1=17.90),
 dict(id="src_kemenkes", kind="src", text="Sumber: Kemenkes Indonesia", t0=10.88, t1=17.90),
 dict(id="b1", kind="line", pts=[(790, 690), (790, 712), (305, 712), (305, 735)], t0=13.60, t1=17.90),
 dict(id="c_night", kind="infocard", icon="moon", text="penglihatan malam", cx=305, cy=775, w=470, t0=13.92, t1=17.90),
 dict(id="b2", kind="line", pts=[(790, 712), (790, 735)], t0=15.30, t1=17.90),
 dict(id="c_imun", kind="infocard", icon="body", text="daya tahan badan", cx=750, cy=775, w=410, t0=15.56, t1=17.90),
 # bab 2: karotenoid larut lemak
 dict(id="n_karot", kind="node", icon="particle", cx=510, cy=540, r=125, label="karotenoid", t0=19.00, t1=21.30),
 dict(id="oil_scene", kind="particle", t0=23.40, t1=30.44, orbit=True, pan=True),
 dict(id="co_karot", kind="callout", text="karotenoid", cx=250, cy=400, target=(440, 462), t0=23.50, t1=30.44),
 dict(id="co_masak", kind="callout", text="dimasak", cx=795, cy=645, target=(690, 715), t0=27.90, t1=30.44),
 dict(id="co_minyak", kind="callout", text="minyak", cx=790, cy=400, target=(640, 462), t0=29.00, t1=30.44),
 dict(id="src_msd", kind="src", text="Sumber: MSD Manual (versi Indonesia)", t0=23.98, t1=28.60),
 # bab 3: avokado -> lemak baik -> serap lemak larut
 dict(id="n_avo", kind="node", icon="avocado", cx=N1, cy=540, r=95, label="avokado", t0=30.44, t1=43.20),
 dict(id="a3", kind="line", pts=[(305, 540), (375, 540)], t0=33.05, t1=43.20),
 dict(id="n_baik", kind="node", icon="droplet", cx=N2, cy=540, r=95, label="lemak baik", t0=33.32, t1=43.20),
 dict(id="a4", kind="line", pts=[(605, 540), (675, 540)], t0=36.75, t1=43.20),
 dict(id="n_serap", kind="node", icon="oilparticle", cx=N3, cy=540, r=95, label="serap lemak larut", t0=37.06, t1=43.20),
 dict(id="src_bh", kind="src", text="Sumber: Berita Harian 2019", t0=34.80, t1=38.90),
 # bab 4: produk + kandungan sebenar pada label
 dict(id="product", kind="photo", name="front", t0=43.82, t1=50.94, cx=312, cy=560, h=330),
 dict(id="ing_carrot", kind="ingcard", icon="carrot", name="Lobak merah", tag="serbuk", mg="60mg", cx=775, cy=470, t0=45.18, t1=50.94),
 dict(id="ing_avo", kind="ingcard", icon="avocado", name="Avokado", tag="ekstrak", mg="15mg", cx=775, cy=665, t0=46.48, t1=50.94),
 dict(id="chip_mal", kind="chip", text="Berdaftar [MAL22076147T]", t0=47.00, t1=50.94, cx=510, cy=830),
 dict(id="endcard", kind="endcard", t0=56.54, t1=DUR),
]

def sfx_cues():
    """(masa, jenis, gain_dB) — SFX procedural."""
    c = []
    for s in SLAMS: c.append((s["t0"], "slam", -9))
    for T in ZOOM_THROUGH: c.append((T - 0.15, "whoosh", -17))
    for e in ELEMENTS:
        k = e["kind"]
        if k in ("icon", "photo", "particle", "node", "infocard", "ingcard", "endcard"): c.append((e["t0"], "pop", -19))
        elif k in ("chip", "src", "callout", "line"): c.append((e["t0"], "tick", -25))
    for t in FLASHES: c.append((t, "shimmer", -23))
    c.append((23.40, "sizzle", -31))
    return sorted(c)
