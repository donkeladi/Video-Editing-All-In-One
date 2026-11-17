#!/usr/bin/env python3
"""Edit video awareness: overlay hero (di BELAKANG orang guna matte), panel bukti/carta (di hadapan), subtitle.
Guna:  build_edit.py preview t1 t2 ...      → work/preview.png
       build_edit.py render out_noaudio.mp4"""
import sys, json, math, subprocess, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
T0, T1 = 2.0, 49.6                     # trim senyap awal/akhir (saat sumber)
WK = '/home/user/Video-Editing-All-In-One/work/'
FD = '/usr/share/fonts/opentype/inter/'
PURPLE=(76,38,158); DEEP=(24,12,58); TEAL=(111,227,207); WHITE=(255,255,255); AMBER=(255,196,87); RED=(255,107,107); BLUE=(120,170,255)
_f={}
def font(wt,sz):
    k=(wt,sz)
    if k not in _f: _f[k]=ImageFont.truetype(f'{FD}Inter-{wt}.otf',sz)
    return _f[k]
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def seg(t,a,b,fin=0.35,fout=0.25):
    """kembalikan (in_progress, alpha) untuk elemen aktif a..b"""
    if t<a or t>b: return None
    pi=ease((t-a)/fin); po=min(1,(b-t)/fout); return pi, pi*ease(po)
def tw(d,s,f): return d.textlength(s,font=f)
def fit(d,s,wt,maxw,hi,lo):
    for sz in range(hi,lo-1,-4):
        if tw(d,s,font(wt,sz))<=maxw: return sz
    return lo
def wrap(d,s,f,maxw):
    lines=[];cur=''
    for w in s.split():
        t=(cur+' '+w).strip()
        if tw(d,t,f)<=maxw or not cur: cur=t
        else: lines.append(cur);cur=w
    if cur: lines.append(cur)
    return lines
def rrect_mask(size,r):
    m=Image.new('L',size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,size[0]-1,size[1]-1),r,fill=255); return m
def card(path,w,crop_top=0,r=26,pad=0):
    im=Image.open(path).convert('RGB')
    if crop_top: im=im.crop((0,crop_top,im.width,im.height))
    im=im.resize((w,int(im.height*w/im.width)),Image.LANCZOS).convert('RGBA')
    im.putalpha(rrect_mask(im.size,r)); return im
def panel_bg(w,h,r=40):
    im=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,w-1,h-1),r,fill=(22,11,52,238),outline=(111,227,207,150),width=3)
    return im
def paste_a(dst,src,xy,alpha=1.0):
    if alpha<=0: return
    if alpha<1:
        src=src.copy(); a=src.getchannel('A').point(lambda v:int(v*alpha)); src.putalpha(a)
    dst.alpha_composite(src,(int(xy[0]),int(xy[1]))) if xy[0]>=0 and xy[1]>=0 else dst.paste(src,(int(xy[0]),int(xy[1])),src)
def glow_text(img,xy,s,f,fill,anchor='mm',glow=(111,227,207,110),shadow=True,stroke=0):
    x,y=xy
    if shadow:
        sh=Image.new('RGBA',img.size,(0,0,0,0)); ds=ImageDraw.Draw(sh)
        ds.text((x,y+6),s,font=f,fill=(10,4,30,200),anchor=anchor,stroke_width=stroke)
        sh=sh.filter(ImageFilter.GaussianBlur(9)); img.alpha_composite(sh)
    ImageDraw.Draw(img).text((x,y),s,font=f,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=(30,14,70,255))

# ---------- aset ----------
C=WK+'crops/'
PX,PY,PW,PH=60,1000,960,440
A={}
def load():
    A['p_head']=card(C+'pantai_head.png',880); A['p_stat']=card(C+'pantai_stat.png',880)
    A['n_head']=card(C+'nst_head.png',880); A['prod']=card(C+'product_front.png',380,crop_top=60,r=30)
    A['bg']=panel_bg(PW,PH)
load()

# ---------- hero (di belakang orang) ----------
HERO=[(2.2,5.4,'AWARENESS · KESIHATAN MATA','UNTUK PELAJAR'),
 (5.4,9.6,'PANTAI HOSPITAL · 2026','KAJIAN PELAJAR'),
 (9.6,16.7,'PELAJAR UNIVERSITI MALAYSIA','{pct}'),
 (16.7,19.4,'NEW STRAITS TIMES','RAKYAT ONLINE'),
 (19.4,23.4,'PURATA SEHARI ONLINE','8 JAM'),
 (23.4,25.7,'SIMPTOM BIASA','MATA PENAT?'),
 (25.7,27.2,'SIMPTOM MATA PENAT','FAMILIAR TAK?'),
 (27.2,33.4,'TIP MATA SIHAT','20 · 20 · 20'),
 (33.4,37.0,'DS PHARMA','EYE CARE'),
 (37.0,42.2,'DS PHARMA EYE CARE','KUNYAH JE'),
 (42.2,44.2,'HOLOGRAM KKM','ADA KKM'),
 (44.2,47.5,'JANGAN RISAU','SEMAK SENDIRI'),
 (47.5,49.6,'DS PHARMA','EYE CARE')]
def hero_layer(t):
    img=Image.new('RGBA',(W,520),(0,0,0,0)); d=ImageDraw.Draw(img)
    for a,b,lab,big in HERO:
        s=seg(t,a,b,0.4,0.25)
        if not s: continue
        pi,al=s
        lay=Image.new('RGBA',(W,520),(0,0,0,0)); dl=ImageDraw.Draw(lay)
        if '{pct}' in big:
            v=89.9*ease((t-a-0.3)/2.0); big=f'{v:.1f}%'
        fl=font('SemiBold',36)
        # label berjarak huruf
        lab2=' '.join(lab) if False else lab
        dl.text((W/2,118),lab2,font=fl,fill=TEAL+(255,),anchor='mm')
        sz=fit(dl,big,'Black',940,270,110)
        glow_text(lay,(W/2,255+int((1-pi)*30)),big,font('Black',sz),WHITE+(255,),stroke=0)
        # garis aksen
        dl.rounded_rectangle((W/2-70,160+0,W/2+70,166),3,fill=TEAL+(255,)) if False else None
        al_img=lay.getchannel('A').point(lambda v:int(v*al)); lay.putalpha(al_img)
        img.alpha_composite(lay)
    return img

# ---------- panel hadapan ----------
def panel_content(name,t,a):
    P=A['bg'].copy(); d=ImageDraw.Draw(P)
    def head(txt,col=TEAL):
        d.text((40,36),txt,font=font('Bold',30),fill=col+(255,),anchor='lm')
    if name=='p_head':
        head('SUMBER · PANTAI HOSPITAL AMPANG'); P.alpha_composite(A['p_head'],(40,70))
        d.text((PW/2,350),'Dry, Gritty, Tired Eyes? — diterbitkan 22/05/2026',font=font('Medium',28),fill=(220,215,245,255),anchor='mm') if False else None
        d.text((PW/2,380),'Kajian pelajar universiti di Malaysia',font=font('SemiBold',36),fill=WHITE+(255,),anchor='mm')
    elif name=='p_stat':
        head('KAJIAN PELAJAR UNIVERSITI · MALAYSIA'); P.alpha_composite(A['p_stat'],(40,70))
        by=290; d.rounded_rectangle((40,by,920,by+46),23,fill=(255,255,255,40))
        f=ease((t-a-0.4)/2.0)*0.899
        d.rounded_rectangle((40,by,40+int(880*f)+1,by+46),23,fill=TEAL+(255,)) if f>0.01 else None
        d.text((PW/2,by+23),f'{f*100:.1f}%',font=font('ExtraBold',28),fill=DEEP+(255,) if f>0.12 else WHITE+(255,),anchor='mm') if False else None
        d.text((PW/2,372),'≈ 9 daripada 10 pelajar ada sekurang-kurangnya',font=font('Bold',32),fill=WHITE+(255,),anchor='mm')
        d.text((PW/2,412),'1 simptom digital eye strain',font=font('Bold',32),fill=TEAL+(255,),anchor='mm')
    elif name=='n_head':
        head('SUMBER · NEW STRAITS TIMES · 29 OKT 2025'); P.alpha_composite(A['n_head'],(40,72))
    elif name=='hours':
        head('RAKYAT MALAYSIA · PURATA ONLINE SEHARI')
        pw,gap=30,6; x0=(PW-(24*pw+23*gap))//2; y0,ph=120,150
        for k in range(24):
            lit=k<8 and (t-a-0.5-k*0.1)>0
            col=TEAL+(255,) if lit else (78,62,128,255)
            if lit: 
                ge=ease((t-a-0.5-k*0.1)/0.25)
                col=(int(111*ge+255*(1-ge)),int(227*ge+255*(1-ge)),int(207*ge+255*(1-ge)),255)
            d.rounded_rectangle((x0+k*(pw+gap),y0,x0+k*(pw+gap)+pw,y0+ph),10,fill=col)
        xe=x0+8*(pw+gap)-gap
        d.line((x0,y0+ph+22,xe,y0+ph+22),fill=TEAL+(255,),width=5)
        d.text((x0,y0+ph+60),'8 jam online',font=font('ExtraBold',44),fill=TEAL+(255,),anchor='lm')
        d.text((x0+24*(pw+gap)-gap,y0+ph+60),'daripada 24 jam',font=font('SemiBold',34),fill=(225,220,250,255),anchor='rm')
        d.text((PW/2,392),'Antara pengguna internet paling aktif di Asia Tenggara',font=font('Medium',30),fill=WHITE+(255,),anchor='mm')
    elif name=='symptoms':
        head('SIMPTOM MATA PENAT SEBAB SKRIN')
        items=[('KERING',AMBER,23.9),('PEDIH',RED,24.6),('KABUR',BLUE,25.3)]
        cw,cg=290,45; x0=(PW-(3*cw+2*cg))//2
        for k,(w_,col,ts) in enumerate(items):
            s=seg(t,ts,999,0.35,1)
            if not s: continue
            pi,al=s; x=x0+k*(cw+cg); y=110+int((1-pi)*40)
            chip=Image.new('RGBA',(cw,250),(0,0,0,0)); dc=ImageDraw.Draw(chip)
            dc.rounded_rectangle((0,0,cw-1,249),36,fill=col+(60,),outline=col+(255,),width=4)
            ic=Image.new('RGBA',(cw,140),(0,0,0,0)); di=ImageDraw.Draw(ic); cx,cy=cw//2,70
            di.ellipse((cx-70,cy-34,cx+70,cy+34),outline=col+(255,),width=8)
            if w_=='KABUR':
                p=Image.new('RGBA',(cw,140),(0,0,0,0)); ImageDraw.Draw(p).ellipse((cx-26,cy-26,cx+26,cy+26),fill=col+(255,)); ic.alpha_composite(p.filter(ImageFilter.GaussianBlur(7)))
            else: di.ellipse((cx-22,cy-22,cx+22,cy+22),fill=col+(255,))
            if w_=='PEDIH':
                for ang in (-40,0,40):
                    r=math.radians(ang-90); di.line((cx+math.cos(r)*52,cy+math.sin(r)*52-10,cx+math.cos(r)*74,cy+math.sin(r)*74-10),fill=col+(255,),width=6)
            if w_=='KERING':
                for dx in (-30,0,30): di.line((cx+dx,cy+46,cx+dx+6,cy+62),fill=col+(255,),width=6)
            chip.alpha_composite(ic,(0,14)); dc.text((cw/2,198),w_,font=font('ExtraBold',50),fill=WHITE+(255,),anchor='mm')
            al_i=chip.getchannel('A').point(lambda v:int(v*al)); chip.putalpha(al_i); P.alpha_composite(chip,(x,y))
        s=seg(t,25.8,999,0.3,1)
        if s: d.text((PW/2,392),'Familiar tak?',font=font('ExtraBold',44),fill=WHITE+(int(255*s[1]),),anchor='mm')
    elif name=='r2020':
        head('PERATURAN 20-20-20 · TIP MATA SIHAT')
        items=[('20','MINIT','setiap',27.9,29.3),('20','KAKI','pandang jauh',29.6,31.3),('20','SAAT','selama',31.5,33.0)]
        D=220; cg=60; x0=(PW-(3*D+2*cg))//2
        for k,(n,u,l,ts,te) in enumerate(items):
            s=seg(t,ts-0.2,999,0.3,1)
            if not s: continue
            pi,al=s; x=x0+k*(D+cg); y=90
            ring=Image.new('RGBA',(D,D+170),(0,0,0,0)); dr=ImageDraw.Draw(ring)
            dr.ellipse((8,8,D-8,D-8),outline=(255,255,255,50),width=16)
            prog=ease((t-ts)/(te-ts)); 
            if prog>0.01: dr.arc((8,8,D-8,D-8),-90,-90+360*prog,fill=TEAL+(255,),width=16)
            dr.text((D/2,D/2-6),n,font=font('Black',100),fill=WHITE+(255,),anchor='mm')
            dr.text((D/2,D+22),u,font=font('ExtraBold',44),fill=TEAL+(255,),anchor='mm')
            dr.text((D/2,D+68),l,font=font('Medium',32),fill=(225,220,250,255),anchor='mm')
            al_i=ring.getchannel('A').point(lambda v:int(v*al)); ring.putalpha(al_i); P.alpha_composite(ring,(x,y))
    elif name=='product':
        head('')
        pr=A['prod'].copy(); py=(PH-pr.height)//2
        if t>=42.2:
            hl=Image.new('RGBA',pr.size,(0,0,0,0)); dh=ImageDraw.Draw(hl); pu=3*abs(math.sin((t-42.2)*3))
            dh.rounded_rectangle((136-pu,16-pu,248+pu,72+pu),10,outline=TEAL+(255,),width=4); pr.alpha_composite(hl)
        P.alpha_composite(pr,(36,py)); x=440
        if t<37.0:
            d.text((x,100),'DS PHARMA',font=font('Bold',34),fill=TEAL+(255,),anchor='lm')
            d.text((x,172),'EYE CARE',font=font('Black',76),fill=WHITE+(255,),anchor='lm')
            d.text((x,238),'CHEWABLE TABLET',font=font('SemiBold',36),fill=(225,220,250,255),anchor='lm')
            for j,txt in enumerate(['10 tablet kunyah · 650mg','No. daftar: MAL22076147T']):
                tl=tw(d,txt,font('SemiBold',26)); yy=300+j*58
                d.rounded_rectangle((x,yy-24,x+tl+36,yy+24),24,fill=(255,255,255,35)); d.text((x+18,yy),txt,font=font('SemiBold',26),fill=WHITE+(255,),anchor='lm')
        elif t<42.2:
            k=ease((t-37.0)/0.35)
            d.text((x,110),'KUNYAH JE',font=font('Black',68),fill=TEAL+(int(255*k),),anchor='lm')
            for j,l in enumerate(['Digunakan secara','tradisional untuk','kesihatan mata']):
                d.text((x,186+j*46),l,font=font('Bold',38),fill=WHITE+(int(255*k),),anchor='lm')
            for j,l in enumerate(['Sila rujuk ahli farmasi / doktor','sebelum mengambil produk ini.']):
                d.text((x,342+j*34),l,font=font('Medium',26),fill=(215,210,240,int(255*k)),anchor='lm')
        else:
            k=ease((t-42.2)/0.35)
            d.text((x,100),'SEMAK PADA PEK',font=font('Bold',32),fill=TEAL+(int(255*k),),anchor='lm')
            for j,l in enumerate(['Hologram KKM','No. daftar MAL22076147T','Rujuk ahli farmasi / doktor']):
                yy=170+j*70; d.ellipse((x,yy-11,x+22,yy+11),fill=TEAL+(int(255*k),))
                d.text((x+40,yy),l,font=font('Bold',34 if j<2 else 30),fill=WHITE+(int(255*k),),anchor='lm')
    return P
PANELS=[('p_head',5.4,9.6),('p_stat',9.6,16.7),('n_head',16.7,19.4),('hours',19.4,23.4),('symptoms',23.4,27.2),('r2020',27.2,33.4),('product',33.4,49.6)]
def front_layer(t,subs):
    img=Image.new('RGBA',(W,760),(0,0,0,0)); d=ImageDraw.Draw(img)   # y offset 960
    for name,a,b in PANELS:
        s=seg(t,a,b,0.4,0.25)
        if not s: continue
        pi,al=s; P=panel_content(name,t,a)
        al_i=P.getchannel('A').point(lambda v:int(v*al)); P.putalpha(al_i)
        img.alpha_composite(P,(PX,PY-960+int((1-pi)*45)))
    # subtitle
    cur=None
    for a,b,txt in subs:
        if a<=t<=b: cur=txt
    if cur:
        f=font('ExtraBold',58); lines=wrap(d,cur,f,920)
        y=1515-960-(len(lines)-1)*38
        for ln in lines:
            ws=ln.split(' '); tot=tw(d,ln,f); x=W/2-tot/2
            for w_ in ws:
                key=any(c.isdigit() for c in w_) or w_.strip('.,:?!').lower() in KEY
                col=TEAL+(255,) if key else WHITE+(255,)
                d.text((x,y),w_,font=f,fill=col,anchor='lm',stroke_width=9,stroke_fill=(20,8,50,255))
                x+=tw(d,w_+' ',f)
            y+=76
    if t>=9.6:
        d.text((W/2,1648-960),'Sumber: Pantai Hospital, 2026 · NST / Ipsos Digital 2025',font=font('SemiBold',29),fill=(255,255,255,215),anchor='mm',stroke_width=4,stroke_fill=(20,8,50,230))
    return img
KEY={'pantai','hospital','new','straits','times','nst','eye','care','ds','pharma','tip','student'}

def make_subs():
    w=json.load(open(WK+'timing.json'))['words']; groups=[];cur=[]
    for x in w:
        cur.append(x)
        if x['w'][-1] in ',.:?!' or len(cur)>=4 or sum(len(c['w'])+1 for c in cur)>22: groups.append(cur);cur=[]
    if cur: groups.append(cur)
    subs=[]
    for i,g in enumerate(groups):
        a=g[0]['start']; b=g[-1]['end']+0.25
        if i+1<len(groups): b=min(b,groups[i+1][0]['start'])
        subs.append((a,b,' '.join(x['w'] for x in g)))
    return subs
ZOOM_CUTS=[5.4,9.6,16.7,19.4,23.4,27.2,33.4,37.0,42.2,47.5]
def zoom_at(t):
    z=1.0
    for c in ZOOM_CUTS:
        if t>=c: z=1.07 if z==1.0 else 1.0
    return z
GY=np.clip(1-np.arange(H)/760.0,0,1)[:,None,None].astype(np.float32)  # gradien gelap atas
def compose(f,a,t,subs):
    z=zoom_at(t)
    if z!=1.0:
        M=cv2.getRotationMatrix2D((W/2,900),0,z); f=cv2.warpAffine(f,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    a=cv2.resize(a,(W,H),interpolation=cv2.INTER_LINEAR).astype(np.float32)/255
    if z!=1.0: a=cv2.warpAffine(a,M,(W,H),flags=cv2.INTER_LINEAR)
    a=np.clip((a-0.12)/0.76,0,1); a=cv2.GaussianBlur(a,(0,0),1.2)[...,None]
    bg=f.astype(np.float32)*(0.88-0.46*GY)
    hl=np.array(hero_layer(t)); h=hl.shape[0]; al=hl[...,3:4].astype(np.float32)/255
    bg[:h]=bg[:h]*(1-al)+hl[...,2::-1].astype(np.float32)*al      # RGB→BGR
    out=bg*(1-a)+f.astype(np.float32)*a
    fl=np.array(front_layer(t,subs)); fh=fl.shape[0]; al=fl[...,3:4].astype(np.float32)/255
    out[960:960+fh]=out[960:960+fh]*(1-al)+fl[...,2::-1].astype(np.float32)*al
    return np.clip(out,0,255).astype(np.uint8)

if __name__=='__main__':
    mode=sys.argv[1]; subs=make_subs(); mat=np.load(WK+'matte.npy',mmap_mode='r'); cap=cv2.VideoCapture(WK+'main.mov')
    if mode=='preview':
        tiles=[]
        for t in map(float,sys.argv[2:]):
            i=int(round(t*FPS)); cap.set(cv2.CAP_PROP_POS_FRAMES,i); ok,f=cap.read()
            tiles.append(cv2.resize(compose(f,np.array(mat[i]),t,subs),(540,960)))
        cv2.imwrite(WK+'preview.png',np.hstack(tiles)); print('ok')
    else:
        out=sys.argv[2]; i0,i1=int(T0*FPS),int(T1*FPS); cap.set(cv2.CAP_PROP_POS_FRAMES,i0)
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
        for i in range(i0,i1):
            ok,f=cap.read()
            if not ok: break
            p.stdin.write(compose(f,np.array(mat[i]),i/FPS,subs).tobytes())
            if (i-i0)%150==0: print(i-i0,i1-i0,flush=True)
        p.stdin.close(); p.wait(); print('done')
