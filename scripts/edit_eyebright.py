#!/usr/bin/env python3
"""Edit video Eyebright: buang senyap, transisi xfade, zoom in/out beransur, subtitle ASS, -14 LUFS.
Guna: python3 scripts/edit_eyebright.py"""
import subprocess, os
SRC="input/eyebright.mov"; OUT="output/eyebright_final.mp4"
PAD=0.2; OV=0.2
# segmen ucapan (saat, video asal)
SEG=[(0.44,14.44),(16.22,28.12),(30.72,41.95),(43.36,58.0)]
# (mula, tamat, teks) ikut masa video asal; teks dibetulkan mengikut skrip
CH=[
(0.64,3.4,"Ada satu bunga, nama dia Eyebright."),
(3.5,6.0,"Orang Eropah dah guna berabad-abad."),
(6.2,8.2,"Dia digunakan secara tradisional"),
(8.3,10.4,"untuk mata yang merah dan radang."),
(10.5,14.2,"Sebab itu dinamakan Eyebright."),
(16.42,18.9,"Secara tradisional, orang guna juga"),
(18.9,21.9,"untuk hidung berair dan alahan bermusim."),
(22.1,24.4,"Kajian makmal pula jumpa ekstraknya"),
(24.5,27.9,"ada aktiviti antioksidan dan anti-radang."),
(30.92,32.0,"Tapi saya nak jujur,"),
(32.0,34.9,"kajian ke atas manusia masih terhad."),
(35.0,36.5,"Sebab itu, kita sebut"),
(36.5,38.9,"'digunakan secara tradisional',"),
(38.9,41.3,"bukan 'terbukti'."),
(43.56,47.4,"Tapi DS Pharma Eye Care ada ekstrak Eyebright."),
(47.5,49.2,"Berdaftar MAL22076147T,"),
(49.3,52.8,"digunakan secara tradisional untuk kesihatan mata."),
(52.9,54.6,"Jadi kalau nak dapatkan ni,"),
(54.5,57.9,"boleh cek bio sekarang. Bye bye!"),
]
lens=[b-a for a,b in SEG]
offs=[sum(lens[:i])-i*OV for i in range(len(SEG))]
def nt(t):
    for (a,b),o in zip(SEG,offs):
        if a-0.01<=t<=b+0.01: return o+t-a
    raise ValueError(t)
total=offs[-1]+lens[-1]
def ts(t):
    h=int(t//3600);m=int(t%3600//60);s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
os.makedirs("work",exist_ok=True); os.makedirs("output",exist_ok=True)
# ASS
ass=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 0","",
"[V4+ Styles]","Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
"Style: Default,Inter,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,70,70,430,1","",
"[Events]","Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
cs=[]
for a,b,t in CH:
    s,e=nt(a),nt(b); cs.append((s,e))
    ass.append(f"Dialogue: 0,{ts(s)},{ts(e)},Default,,0,0,0,,{{\\fad(80,80)}}{t}")
open("work/eyebright.ass","w").write("\n".join(ass)+"\n")
# zoom per blok 2 chunk
blocks=[(cs[i][0],cs[min(i+1,len(cs)-1)][1]) for i in range(0,len(cs),2)]
blocks[0]=(0,blocks[0][1])
blocks=[(blocks[i][0] if i==0 else blocks[i-1][1], blocks[i][1]) for i in range(len(blocks))]
blocks[-1]=(blocks[-1][0],total+1)
ZI,ZO=1.0,1.13
expr="1"
for i,(a,b) in reversed(list(enumerate(blocks))):
    z0,z1=(ZI,ZO) if i%2==0 else (ZO,ZI)
    expr=f"if(lt(t,{b:.3f}),{z0}+({z1-z0:.3f})*(t-{a:.3f})/{b-a:.3f},{expr})"
# filter graph
f=[]
for i,(a,b) in enumerate(SEG):
    f.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30[v{i}]")
    f.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]")
pv,pa="v0","a0"
for i in range(1,len(SEG)):
    f.append(f"[{pv}][v{i}]xfade=transition=fade:duration={OV}:offset={offs[i]:.3f}[x{i}]")
    f.append(f"[{pa}][a{i}]acrossfade=d={OV}[c{i}]")
    pv,pa=f"x{i}",f"c{i}"
f.append(f"[{pv}]scale=w='1080*({expr})':h='1920*({expr})':eval=frame:flags=bicubic,crop=1080:1920,setsar=1,ass=work/eyebright.ass[vout]")
f.append(f"[{pa}]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
open("work/filter.txt","w").write(";\n".join(f))
subprocess.run(["ffmpeg","-y","-i",SRC,"-filter_complex_script","work/filter.txt","-map","[vout]","-map","[aout]",
 "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","44100","-movflags","+faststart",OUT],check=True)
print(OUT,total)
