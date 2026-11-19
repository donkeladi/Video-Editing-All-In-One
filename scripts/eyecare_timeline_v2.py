"""Timeline v2: penyampai saiz asal (matte), semua grafik di BELAKANG penyampai. Kapsyen/slam/punch ikut v1."""
from eyecare_timeline import *   # warna, CAPTIONS, SLAMS, PUNCH, FLASHES, ZOOM_THROUGH, DUR ...
N1, N2, N3, NY, R = 190, 490, 790, 470, 90
PX = 800   # lajur kanan: pil hasil
ELEMENTS = [
 dict(id="g_carrot", kind="ghost", name="carrot", t0=0.0, t1=19.0, gx=870, gy=1180, ang=-28),
 dict(id="g_oil", kind="ghost", name="droplet", t0=19.0, t1=30.44, gx=540, gy=1130, ang=0),
 dict(id="g_avo", kind="ghost", name="avocado", t0=30.44, t1=43.2, gx=250, gy=1200, ang=14),
 dict(id="carrot_hook", kind="icon", name="carrot", t0=1.44, t1=4.20, cx=872, cy=760, size=190),
 dict(id="trk1", kind="tracker", step=1, title="BETA-KAROTIN", t0=4.32, t1=19.00),
 dict(id="trk2a", kind="tracker", step=2, title="LARUT LEMAK", t0=19.00, t1=21.30),
 dict(id="trk2b", kind="tracker", step=2, title="LARUT LEMAK", t0=23.40, t1=30.44),
 dict(id="trk3", kind="tracker", step=3, title="LEMAK BAIK", t0=30.44, t1=43.20),
 dict(id="trk4", kind="tracker", step=4, title="KANDUNGAN", t0=43.28, t1=50.94),
 # bab 1
 dict(id="n_carrot", kind="node", icon="carrot", cx=N1, cy=NY, r=R, label="lobak merah", t0=5.90, t1=17.90),
 dict(id="a1", kind="line", pts=[(298, NY), (382, NY)], t0=7.15, t1=17.90),
 dict(id="n_beta", kind="node", icon="particle", cx=N2, cy=NY, r=R, label="beta-karotin", t0=7.40, t1=17.90),
 dict(id="a2", kind="line", pts=[(598, NY), (682, NY)], t0=10.55, t1=17.90),
 dict(id="n_vitA", kind="node", icon="A", cx=N3, cy=NY, r=R, label="[vitamin A]", t0=10.88, t1=17.90),
 dict(id="b1", kind="line", pts=[(PX, 632), (PX, 686)], t0=13.60, t1=17.90),
 dict(id="c_night", kind="pill2", icon="moon", l1="penglihatan", l2="malam", cx=PX, cy=745, t0=13.92, t1=17.90),
 dict(id="b2", kind="line", pts=[(665, 745), (643, 745), (643, 875), (663, 875)], t0=15.30, t1=17.90),
 dict(id="c_imun", kind="pill2", icon="body", l1="daya tahan", l2="badan", cx=PX, cy=875, t0=15.56, t1=17.90),
 dict(id="src_kemenkes", kind="src", text="Sumber: Kemenkes Indonesia", t0=10.88, t1=17.90),
 # bab 2
 dict(id="n_karot", kind="node", icon="particle", cx=510, cy=NY, r=105, label="karotenoid", t0=19.00, t1=21.30),
 dict(id="oil_scene", kind="scene2", t0=23.40, t1=30.44),
 dict(id="t_karot", kind="tag", text="karotenoid", cx=285, cy=625, t0=23.50, t1=29.00),
 dict(id="t_minyak", kind="tag", text="minyak", cx=285, cy=625, t0=29.00, t1=30.44),
 dict(id="t_masak", kind="tag", text="dimasak", cx=720, cy=655, t0=27.90, t1=30.44),
 dict(id="src_msd", kind="src", text="Sumber: MSD Manual (versi Indonesia)", t0=23.98, t1=28.60),
 # bab 3
 dict(id="n_avo", kind="node", icon="avocado", cx=N1, cy=NY, r=R, label="avokado", t0=30.44, t1=43.20),
 dict(id="a3", kind="line", pts=[(298, NY), (382, NY)], t0=33.05, t1=43.20),
 dict(id="n_baik", kind="node", icon="droplet", cx=N2, cy=NY, r=R, label="lemak baik", t0=33.32, t1=43.20),
 dict(id="a4", kind="line", pts=[(598, NY), (682, NY)], t0=36.75, t1=43.20),
 dict(id="n_serap", kind="node", icon="oilparticle", cx=N3, cy=NY, r=R, label="serap lemak larut", t0=37.06, t1=43.20),
 dict(id="src_bh", kind="src", text="Sumber: Berita Harian 2019", t0=34.80, t1=38.90),
 # bab 4
 dict(id="product", kind="photo", name="front", t0=43.82, t1=50.94, cx=232, cy=495, h=230),
 dict(id="chip_mal", kind="chipS", text="MAL22076147T", t0=47.00, t1=50.94, cx=232, cy=655),
 dict(id="ing_carrot", kind="ing2", icon="carrot", name="Lobak merah", tag="serbuk", mg="60mg", cx=555, cy=495, t0=45.18, t1=50.94),
 dict(id="ing_avo", kind="ing2", icon="avocado", name="Avokado", tag="ekstrak", mg="15mg", cx=825, cy=495, t0=46.48, t1=50.94),
 dict(id="endcard", kind="end2", t0=56.54, t1=DUR),
]
def sfx_cues():
    c = []
    for s in SLAMS: c.append((s["t0"], "slam", -9))
    for T in ZOOM_THROUGH: c.append((T - 0.15, "whoosh", -17))
    for e in ELEMENTS:
        k = e["kind"]
        if k in ("icon", "photo", "scene2", "node", "pill2", "ing2", "end2"): c.append((e["t0"], "pop", -19))
        elif k in ("chipS", "src", "tag", "line"): c.append((e["t0"], "tick", -25))
    for t in FLASHES: c.append((t, "shimmer", -23))
    c.append((23.40, "sizzle", -31))
    return sorted(c)
