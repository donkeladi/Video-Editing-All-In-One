#!/usr/bin/env python3
"""Bina video DS Pharma Eye Care (gaya clinical). Guna: build_eyecare.py
Subtitle ditimingkan secara anggaran (skrip + pause senyap) - ganti dengan transkrip ASR bila ada."""
import re, subprocess, os
V="output/eyecare_raw_cut.mp4"
TEAL=r"{\c&HB6C42E&}"; WHITE=r"{\c&HFFFFFF&}"
# (teks, ...) ; *..* = serlah teal
CH=["Korang tau tak,","purata orang Malaysia online *8 jam* sehari?","Tu belum kira tengok TV lagi tau.",
"Cuba fikir.","Tolak *8 jam* tidur,","separuh masa kita bangun,","mata ni asyik tenung skrin je.",
"Mata ni tak reti complain…","tiba-tiba je petang dah rasa","*pedih, kering, kabur-kabur.*",
"Tu tanda mata korang dah *penat gila.*","Senang je, try *20-20-20.*","Setiap *20 minit,*","tengok jauh *20 kaki,*","*20 saat.*",
"Mata ada sepasang je.","*Jaga elok-elok.*"]
# pause (start,dur) dalam video _cut
P=[(0,.297),(2.816,.19),(4.004,.183),(6.076,.263),(6.854,.216),(7.303,.219),(9.329,.323),(18.218,.192),(25.904,.215),
(28.443,.382),(31.045,.381),(35.729,.284),(36.944,.344),(37.574,.217),(39.706,.341),(42.556,.225)]
dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",V]))
gaps=[(a,a+d) for a,d in P[1:]]
segs=[];t=P[0][0]+P[0][1]
for a,e in gaps: segs.append((t,a)); t=e
segs.append((t,dur))
tot=sum(b-a for a,b in segs)
def at(x):  # kedudukan masa ucapan kumulatif -> masa video
    for a,b in segs:
        if x<=b-a: return a+x
        x-=b-a
    return segs[-1][1]
# sejajarkan ikut suku kata: puncak tenaga suara (work/syl.py) <-> suku kata skrip
SP=["Korang tau tak,","purata orang Malaysia online lapan jam sehari?","Tu belum kira tengok TV lagi tau.","Cuba fikir.",
"Tolak lapan jam tidur,","separuh masa kita bangun,","mata ni asyik tenung skrin je.","Mata ni tak reti complain","tiba-tiba je petang dah rasa",
"pedih, kering, kabur-kabur.","Tu tanda mata korang dah penat gila.","Senang je, try dua puluh dua puluh dua puluh.","Setiap dua puluh minit,",
"tengok jauh dua puluh kaki,","dua puluh saat.","Mata ada sepasang je.","Jaga elok-elok."]
import json
pk=json.load(open("work/peaks.json")); sy=[len(re.findall(r"[aeiou]+",t.lower())) for t in SP]; N=sum(sy); r=len(pk)/N
PZ=[(a_,b_) for a_,b_ in gaps]
cntb=[sum(1 for q in pk if q<a_) for a_,b_ in PZ]   # bilangan suku kata sebelum tiap pause
st=[max(pk[0]-.18,0)];en=[];k=0
for n in sy[:-1]:
    k+=n; idx=k*r
    j=min(range(len(PZ)),key=lambda j:abs(cntb[j]-idx))
    if abs(cntb[j]-idx)<=2.5: en.append(PZ[j][0]+.05); st.append(PZ[j][1]-.05)   # snap ke pause
    else:
        t=(pk[min(int(idx)-1,len(pk)-1)]+pk[min(int(idx),len(pk)-1)])/2; en.append(t); st.append(t)
en.append(dur-.05)
# gabung chunk pendek (<0.9s) ke chunk seterusnya
i=0
while i<len(CH)-1:
    if en[i]-st[i]<.9 and i!=3:
        CH[i+1]=CH[i]+" "+CH[i+1]; st[i+1]=st[i]; del CH[i],st[i],en[i]
    else: i+=1
def ts(x):
    h=int(x//3600);m=int(x%3600//60);s=x%60
    return f"{h}:{m:02d}:{s:05.2f}"
def fmt(c): return re.sub(r"\*(.+?)\*",lambda m:TEAL+m.group(1)+WHITE,c)
hdr=f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter,66,&H00FFFFFF,&H00FFFFFF,&H66401E0A,&H00000000,1,0,0,0,100,100,0,0,3,18,0,2,80,80,600,1
Style: Tag,Inter,32,&H00FFFFFF,&H00FFFFFF,&H66401E0A,&H00000000,1,0,0,0,100,100,1,0,3,12,0,8,40,40,70,1
Style: Big,Inter,150,&H00B6C42E,&H00FFFFFF,&H00401E0A,&H00000000,1,0,0,0,100,100,0,0,1,6,0,8,40,40,260,1
Style: Small,Inter,42,&H00FFFFFF,&H00FFFFFF,&H00401E0A,&H00000000,1,0,0,0,100,100,2,0,1,4,0,8,40,40,430,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
ev=[f"Dialogue: 0,{ts(0)},{ts(dur)},Tag,,0,0,0,,DS PHARMA EYE CARE  ·  MAL22076147T"]
for i,c in enumerate(CH): ev.append(f"Dialogue: 1,{ts(st[i])},{ts(en[i])},Sub,,0,0,0,,{{\\fad(80,60)}}{fmt(c)}")
i0=[i for i,c in enumerate(CH) if '20-20-20' in c][0]; i1=[i for i,c in enumerate(CH) if '20 saat' in c][0]  # kad 20-20-20
a,b=st[i0],min(en[i1],st[i1]+2.5)
ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},Big,,0,0,0,,{{\\fad(150,150)\\t(0,200,\\fscx100\\fscy100)\\fscx70\\fscy70}}20-20-20")
ev.append(f"Dialogue: 2,{ts(a+.3)},{ts(b)},Small,,0,0,0,,{{\\fad(150,150)}}20 minit  •  20 kaki  •  20 saat")
open("work/eyecare.ass","w").write(hdr+"\n".join(ev)+"\n")
for i,c in enumerate(CH): print(f"{st[i]:6.2f}-{en[i]:6.2f} {c}")
# zoom punch-in
zs=[9.49,18.31,28.63,35.87]
Z="if(lt(t,9.49),1,if(lt(t,18.31),1.06,if(lt(t,28.63),1,if(lt(t,35.87),1.06,1))))"
vf=(f"eq=saturation=0.88:contrast=1.06:brightness=0.02,colorbalance=rs=-0.04:bs=0.06:rm=-0.03:bm=0.05,"
 f"scale=w='trunc(1080*({Z})/2)*2':h='trunc(1920*({Z})/2)*2':eval=frame,"
 f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*0.95',ass=work/eyecare.ass,fps=60,format=yuv420p")
af="highpass=f=80,afftdn=nr=10"
subprocess.run(["ffmpeg","-y","-v","error","-i",V,"-vf",vf,"-af",af,"-c:v","libx264","-crf","18","-preset","medium","-c:a","aac","-b:a","192k","work/eyecare_main.mp4"],check=True)
# end card
open("work/t1.txt","w").write("Dapatkan di TikTok Shop")
open("work/t2.txt","w").write("Ambil 1 tablet, 2 kali sehari, 30 minit sebelum makan,\nmengikut arahan pada label produk.")
open("work/t3.txt","w").write("Gunakan mengikut arahan pada label produk. Jika mempunyai masalah\nmata atau sedang mengambil ubat lain, dapatkan nasihat profesional\nkesihatan sebelum menggunakannya.")
F="/usr/share/fonts/opentype/inter/Inter-%s.otf"
fc=("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:6,eq=brightness=-0.08[bg];"
 "[0:v]scale=1080:-2[fg];[bg][fg]overlay=0:150[v1];"
 f"[v1]drawtext=fontfile={F%'Bold'}:textfile=work/t1.txt:fontcolor=0x2EC4B6:fontsize=60:x=(w-tw)/2:y=1330,"
 f"drawtext=fontfile={F%'SemiBold'}:textfile=work/t2.txt:fontcolor=white:fontsize=36:line_spacing=10:x=(w-tw)/2:y=1440,"
 f"drawtext=fontfile={F%'Regular'}:textfile=work/t3.txt:fontcolor=0xDDDDDD:fontsize=28:line_spacing=8:x=(w-tw)/2:y=1620,"
 "fade=t=in:d=0.3,fps=60,format=yuv420p[v]")
subprocess.run(["ffmpeg","-y","-v","error","-loop","1","-t","4","-i","assets/eyecare/ingredients_card.jpg","-f","lavfi","-t","4","-i","anullsrc=r=48000:cl=stereo",
 "-filter_complex",fc,"-map","[v]","-map","1:a","-c:v","libx264","-crf","18","-c:a","aac","-b:a","192k","-shortest","work/eyecare_end.mp4"],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i","work/eyecare_main.mp4","-i","work/eyecare_end.mp4","-filter_complex",
 "[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];[a0][1:a]concat=n=2:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11,volume=0.2dB,alimiter=limit=0.89[a];[0:v][1:v]concat=n=2:v=1:a=0[v]",
 "-map","[v]","-map","[a]","-c:v","libx264","-crf","18","-c:a","aac","-b:a","192k","-movflags","+faststart","output/eyecare_final.mp4"],check=True)
print("siap")
