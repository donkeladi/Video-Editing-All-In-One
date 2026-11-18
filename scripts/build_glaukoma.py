#!/usr/bin/env python3
"""Video awareness glaukoma: potong+flip -> segmentasi orang -> overlay (belakang kepala + panel graf) -> subtitle -> loudnorm.

Guna:  python3 scripts/build_glaukoma.py [--probe 3,10,20]   (probe = simpan PNG pada saat output tertentu)
Perlu: work/seg2.tflite (selfie_multiclass_256x256), assets/glaukoma/*.jpg|webp (gambar produk/bahan).
"""
import subprocess as sp, numpy as np, os, sys, math, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

SRC = os.environ.get("SRC")
W, H, FPS = 1080, 1920, 30
WORK = "work"; ASSET = "assets/glaukoma"; os.makedirs(WORK, exist_ok=True); os.makedirs("output", exist_ok=True)

# ---- segmen yang dikekalkan (masa sumber) : buang senyap awal, jeda panjang, retake & ayat tak dalam skrip
KEEP = [(0.95, 34.95), (35.35, 55.85), (59.30, 70.30), (75.30, 78.40)]
OFF = []; _t = 0.0
for a, b in KEEP: OFF.append(_t); _t += b - a
DUR = _t
def src2out(s):
    for (a, b), o in zip(KEEP, OFF):
        if a <= s <= b: return o + s - a
    return None
def out2src(t):
    for (a, b), o in zip(KEEP, OFF):
        if o <= t < o + (b - a): return a + t - o
    return KEEP[-1][1]

# ---- subtitle (masa sumber, ikut sebutan sebenar)
SUBS = [
 (1.32,2.40,"Umur 40 ke atas?"),(2.60,4.42,"Mata nampak okay,"),(4.58,6.30,"pandangan pun okay?"),(6.42,7.18,"Tunggu dulu."),
 (7.62,10.0,"Ada satu penyakit mata namanya glaukoma,"),(10.10,11.95,"iaitu kerosakan pada saraf"),(12.02,14.92,"yang hantar gambar dari mata ke otak."),
 (15.18,16.05,"Pakar Sunway cakap,"),(16.10,17.80,"sehingga 40 peratus penglihatan"),(17.84,19.65,"boleh hilang tanpa kita sedar"),
 (19.72,22.40,"sebab ia mula dari penglihatan tepi,"),(22.80,24.70,"jadi pandangan depan nampak normal."),
 (24.76,25.70,"Tiada sakit."),(25.74,26.46,"Tiada tanda."),(26.48,28.60,"Dan bila dah hilang,"),(28.76,30.90,"tak boleh dipulihkan semula."),
 (30.96,32.90,"Rawatan hanya boleh halang"),(32.92,34.84,"ia jadi lebih teruk."),
 (35.38,37.20,"Di Malaysia, glaukoma"),(37.30,39.45,"ialah punca ketiga kebutaan."),(39.52,41.45,"Dan menurut WHO,"),
 (41.56,43.80,"lebih separuh kes"),(43.86,45.44,"dikesan lewat."),
 (46.00,48.20,"Cara tahu cuma satu sahaja."),(48.52,50.45,"Periksa mata, jangan"),(50.52,51.88,"tunggu rasa sakit,"),
 (51.90,54.15,"sebab glaukoma memang tak rasa sakit."),(54.20,55.80,"Booking dulu minggu ni."),
 (59.40,60.85,"Untuk sokongan harian,"),(60.90,61.95,"DS Pharma Eye Care,"),(61.98,63.60,"berdaftar MAL22076147T,"),
 (63.84,66.34,"digunakan secara tradisional untuk kesihatan mata."),(66.68,68.10,"Bukan rawatan penyakit mata"),(68.12,70.22,"dan bukan ganti pemeriksaan."),
 (75.40,77.96,"So, jumpa lagi dekat DS Pharma Eye Care."),
]

# ---- warna & font
PUR=(42,27,94); PUR2=(112,76,210); TEAL=(95,214,198); WHITE=(255,255,255); RED=(255,96,96); AMB=(255,196,64); GRN=(84,222,140); GREY=(190,185,215)
def F(w,s): return ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", int(s))
clamp=lambda x,a=0.0,b=1.0: max(a,min(b,x))
def eo(x): x=clamp(x); return 1-(1-x)**3
def eb(x):
    x=clamp(x); c=1.4; return 1+(c+1)*(x-1)**3+c*(x-1)**2
def at(ts,t0,dur=0.35): return eb((ts-t0)/dur)  # pop 0..1 selepas t0

class C:
    """Kanvas supersample 2x untuk lukisan licin."""
    def __init__(s,w,h,K=2): s.w,s.h,s.K=w,h,K; s.im=Image.new("RGBA",(w*K,h*K),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
    def _b(s,b): return [v*s.K for v in b]
    def rr(s,b,r,fill=None,outline=None,width=1): s.d.rounded_rectangle(s._b(b),r*s.K,fill=fill,outline=outline,width=max(1,int(width*s.K)))
    def el(s,b,fill=None,outline=None,width=1): s.d.ellipse(s._b(b),fill=fill,outline=outline,width=max(1,int(width*s.K)))
    def arc(s,b,a0,a1,fill,width): s.d.arc(s._b(b),a0,a1,fill=fill,width=int(width*s.K))
    def ln(s,pts,fill,width): s.d.line([v*s.K for p in pts for v in p],fill=fill,width=int(width*s.K),joint="curve")
    def poly(s,pts,fill): s.d.polygon([v*s.K for p in pts for v in p],fill=fill)
    def tx(s,xy,t,size,w="Bold",fill=WHITE,anchor="la"):
        s.d.text((xy[0]*s.K,xy[1]*s.K),t,font=F(w,size*s.K),fill=fill,anchor=anchor)
    def tw(s,t,size,w="Bold"): return F(w,size*s.K).getlength(t)/s.K
    def out(s): return s.im.resize((s.w,s.h),Image.LANCZOS)
def A(col,a): return (*col[:3],int(255*clamp(a)))

def card(c,accent=TEAL):
    c.rr((0,0,c.w,c.h),30,fill=(24,15,60,238),outline=A(accent,0.55),width=2)
    c.rr((0,0,c.w,8),4,fill=A(accent,0.9))
def pill(c,x,y,text,size,fg,bg,padx=22,h=None,anchor="l"):
    h=h or size*1.9; w=c.tw(text,size,"ExtraBold")+padx*2
    if anchor=="c": x-=w/2
    c.rr((x,y,x+w,y+h),h/2,fill=bg); c.tx((x+w/2,y+h/2),text,size,"ExtraBold",fg,"mm"); return w
def tick(c,cx,cy,r,col):
    c.el((cx-r,cy-r,cx+r,cy+r),fill=col); c.ln([(cx-r*.45,cy+r*.02),(cx-r*.1,cy+r*.38),(cx+r*.5,cy-r*.32)],WHITE,r*.28)
def cross(c,cx,cy,r,col):
    c.el((cx-r,cy-r,cx+r,cy+r),fill=col); k=r*.4
    c.ln([(cx-k,cy-k),(cx+k,cy+k)],WHITE,r*.28); c.ln([(cx-k,cy+k),(cx+k,cy-k)],WHITE,r*.28)
def eye(c,cx,cy,w=150,h=84,iris=PUR2):
    c.poly([(cx-w/2,cy),(cx-w/4,cy-h/2),(cx+w/4,cy-h/2),(cx+w/2,cy),(cx+w/4,cy+h/2),(cx-w/4,cy+h/2)],(245,245,255,255))
    c.el((cx-h*.42,cy-h*.42,cx+h*.42,cy+h*.42),fill=iris); c.el((cx-h*.2,cy-h*.2,cx+h*.2,cy+h*.2),fill=(15,10,35))
    c.el((cx-h*.12,cy-h*.28,cx-h*.02,cy-h*.18),fill=(255,255,255,230))
def brain(c,cx,cy,s=1.0):
    col=(255,170,205,255)
    for dx,dy,rw,rh in [(-28,0,52,46),(28,0,52,46),(0,-14,56,40),(0,14,56,38)]:
        c.el((cx+(dx-rw/2)*s,cy+(dy-rh/2)*s,cx+(dx+rw/2)*s,cy+(dy+rh/2)*s),fill=col)
    for dx in(-34,-8,18,38): c.arc((cx+(dx-12)*s,cy-26*s,cx+(dx+12)*s,cy+0*s),20,200,(200,110,150,255),3)
    c.ln([(cx,cy-34*s),(cx,cy+34*s)],(200,110,150,255),3)

PW,PH = 960,380
PS=0.86; PWS,PHS=int(PW*PS),int(PH*PS); PX,PY=(W-PWS)//2,985
def title(c,t,col=TEAL): c.tx((40,34),t,28,"ExtraBold",col)

# ================= PANEL: setiap fungsi (ts, tl) -> RGBA PIL =================
def sc_hook(ts,tl):
    c=C(PW,PH); card(c)
    title(c,"UMUR 40 KE ATAS?")
    c.tx((40,150),"40+",150,"Black",TEAL,"lm")
    for i,(txt,t0) in enumerate([("Mata nampak okay",4.04),("Pandangan pun okay",5.74)]):
        p=at(ts,t0-0.5)
        if p>0:
            y=120+i*100; c.rr((380,y-36,910,y+36),36,fill=A(WHITE,0.10*p)); c.tx((452,y),txt,36,"Bold",A(WHITE,p),"lm")
            if ts>=t0: tick(c,414,y,22*at(ts,t0,.3),GRN)
    if ts>=6.4: pill(c,PW/2,300,"TAPI TUNGGU DULU...",32,(40,20,0),AMB,28,60,"c")
    return c.out()

def sc_def(ts,tl):
    c=C(PW,PH); card(c); title(c,"APA ITU GLAUKOMA?")
    cy=165; ex,bx=140,820; mid0,mid1=395,565
    bad=ts>=10.54; pb=at(ts,10.54,.4)
    col=A(TEAL,1)
    c.ln([(ex+80,cy),(bx-70,cy)],(255,255,255,50),16)
    if not bad: c.ln([(ex+80,cy),(bx-70,cy)],A(TEAL,.85),10)
    else:
        c.ln([(ex+80,cy),(mid0,cy)],A(TEAL,.85),10); c.ln([(mid1,cy),(bx-70,cy)],(255,255,255,40),10)
        c.ln([(mid0,cy),(mid1,cy)],A(RED,.95),10)
        cross(c,(mid0+mid1)/2,cy,26*pb,RED)
    # paket gambar bergerak
    for k in range(5):
        u=(tl*0.55+k/5)%1; x=ex+80+u*(bx-70-ex-80)
        if bad and x>mid0: continue
        c.el((x-9,cy-9,x+9,cy+9),fill=(255,255,255,235))
    eye(c,ex,cy); brain(c,bx,cy,1.25)
    c.tx((ex,cy+76),"Mata",26,"SemiBold",GREY,"mm"); c.tx((bx,cy+76),"Otak",26,"SemiBold",GREY,"mm")
    c.tx(((mid0+mid1)/2,cy-52),"Saraf optik",26,"ExtraBold",RED if bad else TEAL,"mm")
    if bad:
        p=at(ts,10.8,.4)
        c.rr((60,285,900,345),30,fill=A(RED,.16*p),outline=A(RED,.7*p),width=2)
        c.tx((480,315),"Saraf rosak  =  gambar tak sampai ke otak",30,"Bold",A(WHITE,p),"mm")
    return c.out()

def sc_40(ts,tl):
    c=C(PW,PH); card(c)
    p=eo((ts-16.0)/1.6); cx,cy,r=200,198,128
    c.el((cx-r,cy-r,cx+r,cy+r),outline=(255,255,255,40),width=34)
    if p>0:
        c.arc((cx-r,cy-r,cx+r,cy+r),-90,-90+360*.40*p,RED,34)
        c.el((cx-17+0,cy-r-17,cx+17,cy-r+17),fill=RED) if p>0.02 else None
    c.tx((cx,cy),f"{int(round(40*p))}%",76,"Black",WHITE,"mm")
    c.tx((400,70),"Sehingga 40%",50,"Black",A(WHITE,at(ts,16.0)),"la")
    c.tx((400,138),"penglihatan boleh hilang",36,"SemiBold",A(WHITE,at(ts,17.3)),"la")
    p2=at(ts,18.5)
    if p2>0: c.tx((400,190),"tanpa disedari",52,"Black",A(RED,p2),"la")
    p3=at(ts,19.8)
    if p3>0: c.tx((400,262),"Bermula daripada penglihatan tepi",30,"Medium",A(GREY,p3),"la")
    pill(c,400,305,"Sumber: Pakar Sunway",26,PUR,TEAL,22,52)
    return c.out()

def sc_field(ts,tl):
    c=C(PW,PH); card(c); title(c,"PENGLIHATAN TEPI HILANG DAHULU")
    cx,cy,R=210,215,130
    shrink=eo((ts-22.8)/3.4)
    c.el((cx-R,cy-R,cx+R,cy+R),fill=(14,10,30,255),outline=A(WHITE,.4),width=3)
    ri=R-(R-58)*shrink
    for i in range(8):                      # tepi lembut
        rr=ri+ (7-i)*6; c.el((cx-rr,cy-rr,cx+rr,cy+rr),fill=(190,225,255,int(28)))
    c.el((cx-ri,cy-ri,cx+ri,cy+ri),fill=(205,232,255,255))
    c.el((cx-6,cy-6,cx+6,cy+6),fill=PUR)
    c.tx((cx,cy+R+22),"Pandangan",24,"SemiBold",GREY,"mm")
    p=at(ts,23.2);
    if p>0: tick(c,470,115,20*p,GRN); c.tx((505,115),"Depan: nampak normal",34,"Bold",A(WHITE,p),"lm")
    for t0,txt,y in [(24.76,"Tiada sakit",200),(25.74,"Tiada tanda",285)]:
        q=at(ts,t0,.3)
        if q>0:
            c.rr((470,y-32,900,y+32),32,fill=A(RED,.16*q),outline=A(RED,.8*q),width=2)
            cross(c,505,y,18*q,RED); c.tx((545,y),txt,34,"ExtraBold",A(WHITE,q),"lm")
    return c.out()

def sc_chart(ts,tl):
    c=C(PW,PH); card(c); title(c,"PENGLIHATAN SEIRING MASA")
    x0,x1,y0,y1=70,890,300,95
    c.ln([(x0,y0),(x1,y0)],(255,255,255,70),3); c.ln([(x0,y0),(x0,y1-15)],(255,255,255,70),3)
    def vis(u): return 1-0.62*(u**1.25)            # tanpa rawatan
    p=clamp((ts-26.6)/(34.6-26.6)); us=clamp((30.96-26.6)/(34.6-26.6))
    def pt(u,v): return (x0+u*(x1-x0-20), y0-(y0-y1)*v)
    n=60
    pts=[pt(i/n*p,vis(i/n*p)) for i in range(n+1)]
    if p>0.01:
        if p>us:   # selepas rawatan: garis hijau mendatar
            ui=us; vsplit=vis(ui)
            nn=[pt(ui+(p-ui)*i/20,vsplit) for i in range(21)]
            c.ln([pt(i/n*p,vis(i/n*p)) for i in range(n+1)],A(RED,.55),6)
            c.ln([pt(i/n*us,vis(i/n*us)) for i in range(n+1)],A(RED,1),7)
            c.ln(nn,GRN,7)
        else: c.ln(pts,RED,7)
        e=pts[-1] if p<=us else pt(p,vis(us)); c.el((e[0]-9,e[1]-9,e[0]+9,e[1]+9),fill=WHITE)
    if ts>=29.7:
        q=at(ts,29.7); px,py=pt(0.42,vis(0.42)); pill(c,px-80,py+46,"Tak boleh dipulihkan",24,WHITE,A(RED,.95*q),20,46)
    if ts>=32.46:
        q=at(ts,32.46); px,py=pt(0.60,vis(us)); pill(c,px-150,py-58,"Rawatan: halang jadi lebih teruk",24,(10,40,25),A(GRN,.97*q),20,46)
    c.tx((890,352),"Ilustrasi",24,"Medium",GREY,"rm")
    return c.out()

def sc_rank(ts,tl):
    c=C(PW,PH); card(c)
    ph=clamp((ts-39.7)/0.3)
    a1=1-ph
    if a1>0:
        title(c,"PUNCA KEBUTAAN DI MALAYSIA",A(TEAL,a1))
        rows=[("1","Punca lain",560,(255,255,255,70)),("2","Punca lain",430,(255,255,255,70)),("3","Glaukoma",330,A(RED,1))]
        for i,(n,l,w,col) in enumerate(rows):
            y=100+i*85; g=eo((ts-35.7-i*0.25)/0.6)
            c.el((40,y,100,y+60),fill=A(WHITE,.12*a1)); c.tx((70,y+30),n,32,"Black",A(WHITE,a1),"mm")
            c.rr((118,y,118+w*g,y+60),30,fill=(*col[:3],int(col[3]*a1)))
            if g>.6: c.tx((148,y+30),l,28,"Bold",A(WHITE,a1),"lm")
        q=at(ts,37.3)
        c.tx((830,205),"#3",170*clamp(q,.01,1.1)/1.0,"Black",A(RED,a1*clamp(q)),"mm")
    if ph>0:
        title(c,"KES DIKESAN LEWAT",A(TEAL,ph))
        cx,cy,r=200,205,120; p=eo((ts-40.4)/1.6)
        c.el((cx-r,cy-r,cx+r,cy+r),outline=A(WHITE,.15*ph),width=32)
        c.arc((cx-r,cy-r,cx+r,cy+r),-90,-90+360*.56*p,A(AMB,ph),32)
        c.tx((cx,cy),"> 50%",58,"Black",A(WHITE,ph),"mm")
        c.tx((400,120),"Lebih separuh kes",44,"Black",A(WHITE,ph*at(ts,41.5)),"la")
        c.tx((400,180),"dikesan lewat",56,"Black",A(AMB,ph*at(ts,43.8)),"la")
        pill(c,400,285,"Sumber: WHO",28,PUR,TEAL,24,54)
    return c.out()

def sc_check(ts,tl):
    c=C(PW,PH); card(c,GRN); title(c,"CARA TAHU CUMA SATU",GRN)
    if ts<48.4:
        eye(c,170,220,200,112); c.tx((310,220),"Satu cara sahaja",56,"Black",WHITE,"lm")
    p=at(ts,48.4)
    if p>0:
        c.rr((40,95,920,185),45,fill=A(GRN,.18*p),outline=A(GRN,.9*p),width=3)
        tick(c,95,140,26*p,GRN); c.tx((140,140),"PERIKSA MATA",52,"Black",A(WHITE,p),"lm")
    q=at(ts,50.5)
    if q>0:
        c.rr((40,205,920,275),35,fill=A(RED,.12*q),outline=A(RED,.7*q),width=2)
        cross(c,88,240,22*q,RED); t="Tunggu rasa sakit"
        c.tx((130,240),t,38,"SemiBold",A(GREY,q),"lm")
        sp=clamp((ts-51.9)/.4)
        if sp>0: c.ln([(125,240),(125+c.tw(t,38,"SemiBold")*sp+8,240)],A(RED,.95),5)
        if ts>=53.0: c.tx((905,240),"Glaukoma tak sakit",28,"Bold",A(AMB,at(ts,53.0)),"rm")
    r=at(ts,54.2)
    if r>0:
        c.rr((40,300,330,358),29,fill=A(TEAL,1)); c.rr((58,314,82,342),4,fill=PUR); c.rr((58,314,82,324),4,fill=RED)
        c.tx((98,329),"Booking minggu ni",24,"ExtraBold",PUR,"lm")
    return c.out()

IMG={}
def img(name,size,crop=None,circle=False):
    k=(name,size,crop,circle)
    if k in IMG: return IMG[k]
    im=Image.open(f"{ASSET}/{name}").convert("RGB")
    if crop: im=im.crop(crop)
    if circle:
        s=min(im.size); l=(im.width-s)//2; t=(im.height-s)//2; im=im.crop((l,t,l+s,t+s)).resize((size,size),Image.LANCZOS)
        m=Image.new("L",(size*3,size*3),0); ImageDraw.Draw(m).ellipse((0,0,size*3-1,size*3-1),fill=255); m=m.resize((size,size),Image.LANCZOS)
        im=im.convert("RGBA"); im.putalpha(m)
    else:
        im=im.resize(size if isinstance(size,tuple) else (size,int(size*im.height/im.width)),Image.LANCZOS).convert("RGBA")
    IMG[k]=im; return im
BOX=(140,520,1060,965)

def sc_prod(ts,tl):
    c=C(PW,PH); card(c)
    bx=img("hero.jpg",(400,int(400*445/920)),BOX);
    base=c.out(); base.alpha_composite(bx,(30,60)) if False else None
    c2=Image.new("RGBA",(PW,PH),(0,0,0,0)); c2.alpha_composite(base)
    bw=img("hero.jpg",(400,194),BOX); c2.alpha_composite(bw,(30,70))
    d=C(PW,PH);
    d.tx((470,70),"DS PHARMA",26,"ExtraBold",TEAL); d.tx((470,108),"EYE CARE",72,"Black",WHITE); d.tx((470,190),"Tablet kunyah 650mg",32,"SemiBold",GREY)
    p=at(ts,61.98,.4)
    if p>0:
        d.rr((470,255,910,330),37,fill=A(GRN,.16*p),outline=A(GRN,.9*p),width=2); tick(d,512,292,20*p,GRN)
        d.tx((548,292),"MAL22076147T",34,"ExtraBold",A(WHITE,p),"lm"); d.tx((470,352),"Berdaftar dengan KKM",22,"Medium",A(GREY,p),"lm")
    c2.alpha_composite(d.out()); return c2

ING=[("c5705a6e_x","bbb6291d-image.webp","Serbuk lobak merah","60mg"),("","f5f93dee-image.webp","Ekstrak avokado","15mg"),
     ("","f0df34c8-image.webp","Ekstrak goji","50mg"),("","c4c964f5-image.jpg","Ekstrak Eyebright","40mg")]
def sc_ing(ts,tl):
    c=C(PW,PH); card(c); title(c,"BAHAN UTAMA  •  DIGUNAKAN SECARA TRADISIONAL")
    base=c.out(); cw=215
    for i,(_,f,n,mg) in enumerate(ING):
        p=at(ts,63.9+i*0.25,.45)
        if p<=0: continue
        x=40+i*(cw+15); k=C(cw,300); k.rr((0,0,cw,300),26,fill=A(WHITE,.09*clamp(p)),outline=A(TEAL,.35*clamp(p)),width=2)
        k.tx((cw/2,232),n,22,"Bold",A(WHITE,clamp(p)),"mm"); k.tx((cw/2,268),mg,34,"Black",A(TEAL,clamp(p)),"mm")
        ko=k.out(); ko.alpha_composite(img(f,132,circle=True),(int((cw-132)/2),36));
        ko.putalpha(ko.getchannel("A").point(lambda v:v))
        base.alpha_composite(ko,(x,62+int((1-clamp(p))*20)))
    return base

def sc_warn(ts,tl):
    c=C(PW,PH); card(c,AMB)
    c.poly([(95,95),(135,185),(55,185)],AMB); c.tx((95,160),"!",52,"Black",(40,20,0),"mm")
    c.tx((180,72),"PENTING",30,"ExtraBold",AMB)
    for i,(t,t0) in enumerate([("Bukan rawatan penyakit mata",66.68),("Bukan ganti pemeriksaan mata",68.12)]):
        p=at(ts,t0-.1);
        if p>0:
            y=170+i*95; c.rr((180,y-34,920,y+34),34,fill=A(AMB,.12*p),outline=A(AMB,.7*p),width=2)
            cross(c,222,y,20*p,RED); c.tx((262,y),t,36,"Bold",A(WHITE,p),"lm")
    c.tx((40,318),"Ubat tradisional. Sila rujuk pakar farmasi /",24,"Medium",GREY,"lm"); c.tx((40,350),"doktor sebelum mengambil produk ini.",24,"Medium",GREY,"lm")
    return c.out()

def sc_end(ts,tl):
    c=C(PW,PH); card(c)
    c2=Image.new("RGBA",(PW,PH),(0,0,0,0)); c2.alpha_composite(c.out())
    c2.alpha_composite(img("hero.jpg",(400,194),BOX),(520,60))
    d=C(PW,PH)
    d.tx((40,60),"DS PHARMA",28,"ExtraBold",TEAL); d.tx((40,100),"EYE CARE",84,"Black",WHITE)
    d.tx((40,200),"Sokongan harian untuk",30,"SemiBold",GREY); d.tx((40,238),"kesihatan mata*",44,"ExtraBold",WHITE)
    d.rr((40,305,330,355),25,fill=A(GRN,.16),outline=A(GRN,.9),width=2); d.tx((185,330),"MAL22076147T",26,"ExtraBold",WHITE,"mm")
    d.tx((520,300),"Periksa mata dulu.",32,"ExtraBold",AMB,"lm"); d.tx((520,338),"*Digunakan secara tradisional",20,"Medium",GREY,"lm")
    c2.alpha_composite(d.out()); return c2

SCENES=[(1.2,7.25,sc_hook),(7.55,15.1,sc_def),(15.1,22.6,sc_40),(22.7,26.4,sc_field),(26.45,34.95,sc_chart),
        (35.35,45.6,sc_rank),(45.9,55.85,sc_check),(59.3,63.8,sc_prod),(63.8,66.6,sc_ing),(66.6,70.3,sc_warn),(75.3,78.4,sc_end)]

# ---- bayang panel (sekali)
_sh=Image.new("RGBA",(PWS+160,PHS+160),(0,0,0,0)); ImageDraw.Draw(_sh).rounded_rectangle((80,100,80+PWS,100+PHS),26,fill=(0,0,0,170)); SHADOW=_sh.filter(ImageFilter.GaussianBlur(26))
def panel_layer(ts):
    for a,b,fn in SCENES:
        if a<=ts<=b:
            tl=ts-a; fin=clamp(tl/0.4); fout=clamp((b-ts)/0.25)
            alpha=min(eo(fin),fout); dy=int((1-eb(fin))*60)
            L=Image.new("RGBA",(W,H),(0,0,0,0)); p=fn(ts,tl).resize((PWS,PHS),Image.LANCZOS)
            if alpha<1: p.putalpha(p.getchannel("A").point(lambda v,a=alpha:int(v*a)))
            sh=SHADOW.copy(); sh.putalpha(sh.getchannel("A").point(lambda v,a=alpha:int(v*a)))
            L.alpha_composite(sh,(PX-80,PY-80+dy)); L.alpha_composite(p,(PX,PY+dy)); return L,True
    return None,False

# ---- backdrop belakang kepala (tint + halo)
def _grad():
    y=np.linspace(0,1,H)[:,None]; x=np.linspace(-1,1,W)[None,:]
    a=(0.12+0.14*y)*np.ones((H,W)); a=a*(1-0.25*np.abs(x));
    col=np.zeros((H,W,4),np.uint8); col[...,0]=60+60*y.repeat(W,1); col[...,1]=28; col[...,2]=150; col[...,3]=(a*255).astype(np.uint8)
    return Image.fromarray(col,"RGBA")
TINT=_grad()
def halo_layer(t,hx,hy,ts):
    """Cahaya lembut di belakang kepala sahaja (tanpa bulatan/titik)."""
    k=Image.new("RGBA",(W//4,H//4),(0,0,0,0)); d=ImageDraw.Draw(k); cx,cy=hx/4,hy/4
    for r,al in [(230,10),(190,14),(150,18),(110,22)]:
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(*TEAL,al))
    return k.resize((W,H),Image.BILINEAR).filter(ImageFilter.GaussianBlur(18))

# ---- subtitle
_sc={}
def sub_sprite(text,wi):
    k=(text,wi)
    if k in _sc: return _sc[k]
    words=text.split(); f=F("ExtraBold",56); maxw=840; lines=[[]];
    for i,w in enumerate(words):
        cur=" ".join(x for x,_ in lines[-1]+[(w,i)])
        if lines[-1] and f.getlength(cur)>maxw: lines.append([])
        lines[-1].append((w,i))
    lh=72; im=Image.new("RGBA",(W,lh*len(lines)+30),(0,0,0,0)); d=ImageDraw.Draw(im)
    for li,ln in enumerate(lines):
        tot=f.getlength(" ".join(x for x,_ in ln)); x=(W-tot)/2; y=lh*li+38
        for w,i in ln:
            col=TEAL if i==wi else WHITE
            d.text((x,y),w,font=f,fill=col,anchor="lm",stroke_width=9,stroke_fill=(15,8,40,255))
            x+=f.getlength(w+" ")
    sh=im.filter(ImageFilter.GaussianBlur(6)); sh=Image.merge("RGBA",(Image.new("L",im.size,0),)*3+(sh.getchannel("A").point(lambda v:int(v*.6)),))
    out=Image.new("RGBA",im.size,(0,0,0,0)); out.alpha_composite(sh); out.alpha_composite(im); _sc[k]=out; return out
def sub_layer(ts):
    for a,b,t in SUBS:
        if a-0.03<=ts<=b+0.12:
            ws=t.split(); L=[len(w)+1 for w in ws]; u=clamp((ts-a)/max(b-a,.1)); acc=0; cut=u*sum(L); wi=len(ws)-1
            for i,l in enumerate(L):
                if cut<acc+l: wi=i; break
                acc+=l
            return sub_sprite(t,wi)
    return None

# ---- segmenter
SEG=None
def seg_masks(rgb):
    global SEG
    if SEG is None:
        SEG=vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=f"{WORK}/seg2.tflite"),output_confidence_masks=True,output_category_mask=False,running_mode=vision.RunningMode.IMAGE))
    sm=np.asarray(Image.fromarray(rgb).resize((270,480),Image.BILINEAR))
    r=SEG.segment(mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(sm)))
    cm=[np.squeeze(m.numpy_view()) for m in r.confidence_masks]
    person=np.clip((1-cm[0]-0.25)/0.5,0,1); hand=np.clip(((cm[2]+cm[5])-0.3)/0.4,0,1)*person
    up=lambda m:Image.fromarray((m*255).astype(np.uint8)).resize((W,H),Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.0))
    return person,up(person),up(hand)

HEAD=[540.0,420.0]
def compose(rgb,t):
    ts=out2src(t); base=Image.fromarray(rgb).convert("RGBA")
    person,pm,hm=seg_masks(rgb)
    ys,xs=np.nonzero(person>0.5)
    if len(ys):
        top=ys.min(); sel=ys<top+90; hx=xs[sel].mean()*W/270; hy=(top+75)*H/480
        HEAD[0]+=(hx-HEAD[0])*0.25; HEAD[1]+=(hy-HEAD[1])*0.25
    behind=base.copy(); behind.alpha_composite(TINT); behind.alpha_composite(halo_layer(t,HEAD[0],HEAD[1],ts))
    out=Image.composite(base,behind,pm)                       # orang di depan backdrop
    P,has=panel_layer(ts)
    if has:
        out.alpha_composite(P)
    S=sub_layer(ts)
    if S is not None: out.alpha_composite(S,(0,1335))
    return out.convert("RGB")

def build_base():
    parts=[];fa=[]
    for i,(a,b) in enumerate(KEEP):
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,hflip,fps={FPS},eq=contrast=1.04:saturation=1.08[v{i}]")
        fa.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={b-a-0.02:.3f}:d=0.02[a{i}]")
    n=len(KEEP); cc="".join(f"[v{i}][a{i}]" for i in range(n))+f"concat=n={n}:v=1:a=1[v][a]"
    fc=";".join(parts+fa+[cc])
    sp.run(["ffmpeg","-y","-v","error","-i",SRC,"-filter_complex",fc,"-map","[v]","-map","[a]","-c:v","libx264","-crf","14","-preset","fast","-pix_fmt","yuv420p","-c:a","aac","-b:a","256k",f"{WORK}/base.mp4"],check=True)

# ---- sound effect (dijana lokal, tiada kredit)
SR=48000
def _env(n,a=0.01,d=3.0):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t*d)
def sfx_pop(f=700,dur=.14):
    n=int(SR*dur); t=np.arange(n)/SR; fr=f*(1+0.6*np.exp(-t*40)); return np.sin(2*np.pi*np.cumsum(fr)/SR)*_env(n,.002,26)
def sfx_chime(f=880,dur=.6):
    n=int(SR*dur); t=np.arange(n)/SR; return (np.sin(2*np.pi*f*t)+.5*np.sin(2*np.pi*f*1.5*t)+.25*np.sin(2*np.pi*f*2*t))*_env(n,.004,7)/1.75
def sfx_ok(): return np.concatenate([sfx_chime(988,.18)[:int(SR*.09)],np.zeros(0)]) + 0 if False else _mix2(sfx_chime(784,.5),sfx_chime(1175,.5),int(SR*.09))
def _mix2(a,b,off):
    o=np.zeros(max(len(a),off+len(b))); o[:len(a)]+=a; o[off:off+len(b)]+=b; return o
def sfx_bad(): 
    n=int(SR*.28); t=np.arange(n)/SR; fr=220*np.exp(-t*2.2); return np.tanh(2.5*np.sin(2*np.pi*np.cumsum(fr)/SR))*_env(n,.003,9)*.7
def sfx_thud(dur=.5):
    n=int(SR*dur); t=np.arange(n)/SR; fr=110*np.exp(-t*7)+45; x=np.sin(2*np.pi*np.cumsum(fr)/SR)*_env(n,.002,8)
    c=np.random.RandomState(1).randn(n)*_env(n,.001,120)*.25; return x+c
def sfx_whoosh(dur=.45,lo=300,hi=3200,seed=0):
    n=int(SR*dur); rs=np.random.RandomState(seed); x=rs.randn(n); t=np.linspace(0,1,n)
    fc=lo*(hi/lo)**t; a=1-np.exp(-2*np.pi*fc/SR); y=np.zeros(n); z1=z2=0.0
    for i in range(n): z1+=a[i]*(x[i]-z1); z2+=a[i]*(z1-z2); y[i]=z1-z2
    e=np.sin(np.pi*t)**1.6; y=y*e; return y/(np.abs(y).max()+1e-9)
def sfx_rise(dur=1.5):
    n=int(SR*dur); t=np.arange(n)/SR; fr=300*(6**(t/dur)); x=np.sin(2*np.pi*np.cumsum(fr)/SR); e=np.minimum(1,t/.1)*np.minimum(1,(dur-t)/.15); return x*e*.6
def sfx_tick(): return sfx_pop(1500,.05)
def sfx_swipe(): return sfx_whoosh(.22,1500,6000,5)
def gen_sfx():
    out=np.zeros(int(SR*(DUR+1.0)))
    def put(src_t,snd,gain):
        t=src2out(src_t)
        if t is None: return
        i=int(t*SR); n=min(len(snd),len(out)-i)
        if n>0: out[i:i+n]+=snd[:n]*gain
    wh=[sfx_whoosh(.45,300,3200,k) for k in range(3)]
    for k,(a,b,fn) in enumerate(SCENES): put(a+0.02,wh[k%3],0.30)         # panel masuk
    ok,bad=sfx_ok(),sfx_bad()
    for t in (4.04,5.74,23.2): put(t,ok,.28)
    put(6.40,sfx_thud(),.50); put(10.54,bad,.40); put(16.0,sfx_rise(1.5),.22); put(17.55,ok,.26)
    put(18.5,sfx_pop(520),.35)
    for t in (24.76,25.74): put(t,bad,.30)
    put(29.7,sfx_thud(.35),.40); put(32.46,ok,.30)
    for i,t in enumerate((35.7,35.95,36.2)): put(t,sfx_pop(500+i*120,.12),.28)
    put(37.3,sfx_thud(),.55); put(40.4,sfx_rise(1.5),.22); put(41.95,sfx_pop(600),.30); put(43.8,sfx_pop(500),.32)
    put(48.4,ok,.32); put(50.5,bad,.28); put(51.9,sfx_swipe(),.30); put(54.2,sfx_pop(760),.35)
    put(61.98,ok,.32)
    for i in range(4): put(63.9+i*0.25,sfx_pop(620+i*90),.30)
    put(66.68,sfx_tick(),.35); put(68.12,sfx_tick(),.35); put(75.4,sfx_chime(1046,.7),.25)
    out=np.tanh(out*1.2)
    import wave
    with wave.open(f"{WORK}/sfx.wav","wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767*0.9).astype(np.int16).tobytes())

def write_srt():
    def f(t): h=int(t//3600); m=int(t%3600//60); s=t%60; return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}"
    out=[];n=1
    for a,b,t in SUBS:
        oa,ob=src2out(a),src2out(b)
        if oa is None or ob is None: continue
        out.append(f"{n}\n{f(oa)} --> {f(ob)}\n{t}\n"); n+=1
    open(f"{WORK}/glaukoma.srt","w").write("\n".join(out))

if __name__=="__main__":
    build_base(); write_srt(); gen_sfx()
    if "--probe" in sys.argv:
        for t in [float(x) for x in sys.argv[sys.argv.index("--probe")+1].split(",")]:
            raw=sp.run(["ffmpeg","-v","error","-ss",str(t),"-i",f"{WORK}/base.mp4","-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
            rgb=np.frombuffer(raw,np.uint8).reshape(H,W,3).copy(); compose(rgb,t).save(f"{WORK}/probe_{t:05.1f}.png")
        sys.exit()
    rd=sp.Popen(["ffmpeg","-v","error","-i",f"{WORK}/base.mp4","-f","rawvideo","-pix_fmt","rgb24","-"],stdout=sp.PIPE)
    wr=sp.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",f"{WORK}/base.mp4","-i",f"{WORK}/sfx.wav","-filter_complex","[1:a]aresample=48000,aformat=channel_layouts=mono[v];[2:a]aresample=48000[x];[v][x]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]","-map","0:v","-map","[a]",
                 "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest","output/glaukoma_awareness.mp4"],stdin=sp.PIPE)
    i=0
    while True:
        b=rd.stdout.read(W*H*3)
        if len(b)<W*H*3: break
        wr.stdin.write(np.frombuffer(b,np.uint8).reshape(H,W,3).copy().pipe if False else compose(np.frombuffer(b,np.uint8).reshape(H,W,3).copy(),i/FPS).tobytes()); i+=1
        if i%150==0: print(i,flush=True)
    wr.stdin.close(); wr.wait(); print("siap",i)
