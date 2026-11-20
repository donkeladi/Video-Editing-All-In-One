#!/usr/bin/env python3
"""Hasilkan kad gaya keratan akhbar (kertas, header, kapsyen, bayang) untuk pop-up. Output: work/cards/*.png"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
os.makedirs("work/cards", exist_ok=True)
SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"; SANS="/usr/share/fonts/opentype/inter/Inter-Bold.otf"
PAPER=(247,244,236); INK=(24,32,40); TEAL=(20,150,140)
# (nama, sumber, crop(x,y,w,h)|None, kapsyen, lebar_dalam)
CARDS=[
 ("flower","input/broll/flower.jpg",None,"Eyebright (Euphrasia)",520),
 ("ingredients","input/broll/poster_ingredients.jpg",None,"Ekstrak Eyebright 40mg",780),
 ("box_back","input/broll/box_back.jpg",(110,780,700,560),"Berdaftar KKM · MAL22076147T",780),
 ("box_front","input/broll/box_front.jpg",(0,640,1500,1080),"Digunakan secara tradisional",780),
]
def wrap(d,t,f,w):
    out=[];cur=""
    for wd in t.split():
        if d.textlength((cur+" "+wd).strip(),font=f)<=w: cur=(cur+" "+wd).strip()
        else: out.append(cur);cur=wd
    return out+[cur]
for name,src,crop,cap,W in CARDS:
    im=Image.open(src).convert("RGB")
    if crop: x,y,w,h=crop; im=im.crop((x,y,x+w,y+h))
    im=im.resize((W,int(im.height*W/im.width)),Image.LANCZOS)
    pad=28; fh=ImageFont.truetype(SANS,26); fc=ImageFont.truetype(SERIF,36)
    tmp=ImageDraw.Draw(Image.new("RGB",(10,10)))
    lines=wrap(tmp,cap,fc,W-24)
    head=64; capH=len(lines)*48+34
    cw=W+2*pad; ch=pad+head+im.height+capH+pad
    card=Image.new("RGB",(cw,ch),PAPER); d=ImageDraw.Draw(card)
    # header
    d.rectangle([pad,pad+10,pad+10,pad+38],fill=TEAL)
    d.text((pad+24,pad+8),"F A K T A   K E S I H A T A N",font=fh,fill=INK)
    d.line([pad,pad+head-8,cw-pad,pad+head-8],fill=INK,width=3)
    card.paste(im,(pad,pad+head))
    y=pad+head+im.height+16
    d.rectangle([pad,y+4,pad+8,y+len(lines)*48-4],fill=TEAL)
    for i,l in enumerate(lines): d.text((pad+24,y+i*48),l,font=fc,fill=INK)
    # bayang + tepi
    m=50; out=Image.new("RGBA",(cw+2*m,ch+2*m),(0,0,0,0))
    sh=Image.new("RGBA",out.size,(0,0,0,0)); ImageDraw.Draw(sh).rectangle([m+8,m+14,m+cw+8,m+ch+14],fill=(0,0,0,150))
    out=Image.alpha_composite(out,sh.filter(ImageFilter.GaussianBlur(14)))
    out.paste(card.convert("RGBA"),(m,m))
    out.save(f"work/cards/{name}.png"); print(name,out.size)
