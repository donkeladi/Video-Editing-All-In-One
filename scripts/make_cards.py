#!/usr/bin/env python3
"""Tema Blueprint Breakdown: kad panel biru teknikal + grid + HUD. Output: work/cards/*.png dan cards.json
Label/penanda dilukis oleh edit_eyebright.py (ASS). Ilustrasi ditanda 'tidak mengikut skala'; tiada ukuran rekaan."""
from PIL import Image, ImageDraw, ImageFont
import os, json
os.makedirs("work/cards", exist_ok=True)
S=2
BG=(18,51,97); TXT=(237,245,255); ACC=(155,232,255)
MONO="/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
def F(sz): return ImageFont.truetype(MONO,int(sz*S))
PAD=16; HEAD=44; LH=34
# nama, sumber, crop, lebar_papar, header, nota, [(label, (fx0,fy0,fx1,fy1))]
CARDS=[
 ("flower","input/broll/flower.jpg",None,360,"FIG.01 / BUNGA","",
   [("Bunga (Flos)",(0.38,0.28,0.88,0.58)),("Daun",(0.10,0.55,0.42,0.72)),("Batang",(0.22,0.74,0.40,0.98))]),
 ("ingredients","input/broll/poster_ingredients.jpg",None,460,"FIG.02 / BAHAN","ILUSTRASI · TIDAK MENGIKUT SKALA",
   [("Ekstrak bunga Eyebright · 40mg",(0.335,0.465,0.595,0.575)),("No. MAL pada kotak",(0.17,0.73,0.21,0.85))]),
 ("box_back","input/broll/box_back.jpg",(110,780,700,560),460,"FIG.03 / LABEL","",
   [("Senarai bahan",(0.11,0.16,0.90,0.36)),("Amaran: rujuk ahli farmasi",(0.12,0.37,0.90,0.83)),("No. MAL22076147T",(0.13,0.85,0.48,0.94))]),
 ("box_front","input/broll/box_front.jpg",(0,640,1500,1080),460,"FIG.04 / HOLOGRAM","",
   [("Hologram keselamatan KKM",(0.37,0.11,0.64,0.27)),("'Traditionally used...'",(0.03,0.61,0.71,0.69))]),
]
def grid(im,step,a_minor,a_major,major=5):
    from PIL import Image as I
    lay=I.new("RGBA",im.size,(0,0,0,0)); d=ImageDraw.Draw(lay); w,h=im.size
    for i,x in enumerate(range(0,w,step)):
        d.line([x,0,x,h],fill=ACC+((a_major if i%major==0 else a_minor),),width=1)
    for i,y in enumerate(range(0,h,step)):
        d.line([0,y,w,y],fill=ACC+((a_major if i%major==0 else a_minor),),width=1)
    return I.alpha_composite(im.convert("RGBA"),lay)
def brackets(d,w,h,inset,ln,col,wd):
    for (x,y,sx,sy) in [(inset,inset,1,1),(w-inset,inset,-1,1),(inset,h-inset,1,-1),(w-inset,h-inset,-1,-1)]:
        d.line([x,y,x+sx*ln,y],fill=col,width=wd); d.line([x,y,x,y+sy*ln],fill=col,width=wd)
meta={}
for name,src,crop,Wd,fig,note,marks in CARDS:
    im=Image.open(src).convert("RGB")
    if crop: x,y,w,h=crop; im=im.crop((x,y,x+w,y+h))
    iw=Wd-2*PAD; ih=int(im.height*iw/im.width)
    Hd=HEAD+ih+12+len(marks)*LH+14
    card=Image.new("RGBA",(Wd*S,Hd*S),BG+(255,)); card=grid(card,10*S,18,40)
    d=ImageDraw.Draw(card)
    d.text((PAD*S,12*S),fig,font=F(17),fill=ACC)
    if note: 
        tw=d.textlength(note,font=F(10)); d.text((Wd*S-PAD*S-tw,17*S),note,font=F(10),fill=TXT)
    d.line([PAD*S,(HEAD-6)*S,(Wd-PAD)*S,(HEAD-6)*S],fill=ACC,width=S)
    card.paste(im.resize((iw*S,ih*S),Image.LANCZOS),(PAD*S,HEAD*S))
    d.rectangle([PAD*S-S,HEAD*S-S,(PAD+iw)*S+S,(HEAD+ih)*S+S],outline=ACC,width=2*S)
    d.line([PAD*S,(HEAD+ih+6)*S,(Wd-PAD)*S,(HEAD+ih+6)*S],fill=ACC+(120,),width=S)
    d.rectangle([0,0,Wd*S-1,Hd*S-1],outline=ACC,width=2*S)
    brackets(d,Wd*S,Hd*S,5*S,16*S,ACC,3*S)
    card.save(f"work/cards/{name}.png")
    meta[name]={"W":Wd,"H":Hd,"img":[PAD,HEAD,iw,ih],"legend_y":HEAD+ih+12,
      "marks":[{"label":l,"rect":[PAD+fx0*iw,HEAD+fy0*ih,PAD+fx1*iw,HEAD+fy1*ih]} for l,(fx0,fy0,fx1,fy1) in marks]}
    print(name,card.size)
json.dump(meta,open("work/cards/cards.json","w"))
# latar kad "Fakta": biru + grid + tanda sudut
bg=Image.new("RGBA",(1080,1920),BG+(255,)); bg=grid(bg,60,22,48)
d=ImageDraw.Draw(bg); brackets(d,1080,1920,40,70,ACC,4)
d.text((60,84),"BLUEPRINT / EYEBRIGHT",font=ImageFont.truetype(MONO,24),fill=ACC+(200,))
bg.convert("RGB").save("work/cards/bg_grid.png")
# HUD ringan atas video: grid sangat halus + sudut
hud=Image.new("RGBA",(1080,1920),(0,0,0,0)); hud=grid(hud,120,14,26,major=4)
d=ImageDraw.Draw(hud); brackets(d,1080,1920,36,56,ACC+(190,),3)
hud.save("work/cards/hud.png")
