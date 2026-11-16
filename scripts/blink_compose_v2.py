#!/usr/bin/env python3
"""v2 klinikal: zoom perlahan + kad/kapsyen (tanpa matte/tint). Guna: blink_compose_v2.py work/blink out.mp4 [f1,f2,... -> still %05d.png]"""
import sys, os, subprocess, numpy as np, cv2
wd, out = sys.argv[1:3]; W,H,FPS=1080,1920,30; G=os.path.join(wd,os.environ.get("GDIR","g2")); ORIGIN=(540,650)
KEYS=[(0,1.0),(2.9,1.03),(3.119,1.03),(3.12,1.0),(10.0,1.035),(11.2,1.06),(12.9,1.04),(13.119,1.04),(13.12,1.0),(19.0,1.04),(21.0,1.02),(23.86,1.06),
      (24.6,1.01),(28.6,1.04),(29.6,1.0),(34.339,1.02),(34.34,1.05),(34.889,1.05),(34.89,1.0),(35.799,1.02),(35.80,1.05),(38.089,1.05),(38.09,1.0),(39.2,1.015)]
def zoom(t):
    for (a,sa),(b,sb) in zip(KEYS,KEYS[1:]):
        if a<=t<=b:
            if b-a<.01: return sb
            k=(t-a)/(b-a); return sa+(sb-sa)*k*k*(3-2*k)
    return KEYS[-1][1]
STILLS=[int(x) for x in sys.argv[3].split(',')] if len(sys.argv)>3 else None
p=subprocess.Popen(["ffmpeg","-v","error","-i",os.path.join(wd,"cut.mov"),"-f","rawvideo","-pix_fmt","bgr24","-"],stdout=subprocess.PIPE)
enc=None if STILLS else subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r","30","-i","-","-i",os.path.join(wd,os.environ.get("MIX","mix2.wav")),
  "-map","0:v","-map","1:a","-vf","format=yuv420p","-c:v","libx264","-crf","18","-preset","medium","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",out],stdin=subprocess.PIPE)
i=0
while True:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3 or i>=1174: break
    if STILLS and i not in STILLS: i+=1; continue
    s=zoom(i/FPS); A=np.array([[s,0,ORIGIN[0]*(1-s)],[0,s,ORIGIN[1]*(1-s)]],np.float32)
    f=cv2.warpAffine(np.frombuffer(b,np.uint8).reshape(H,W,3),A,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    L=cv2.imread(f"{G}/front/{i:05d}.png",cv2.IMREAD_UNCHANGED).astype(np.float32); a=L[...,3:4]/255
    o=np.clip(f*(1-a)+L[...,:3]*a,0,255).astype(np.uint8)
    if STILLS: cv2.imwrite(out%i,cv2.resize(o,(540,960)))
    else: enc.stdin.write(o.tobytes())
    i+=1
if not STILLS: enc.stdin.close(); enc.wait()
print("done",i)
