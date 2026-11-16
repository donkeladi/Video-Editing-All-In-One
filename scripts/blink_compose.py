#!/usr/bin/env python3
"""Komposit akhir: video + matte orang + grafik belakang (green-screen style) + kapsyen + zoom licin + mix audio.
Guna: blink_compose.py work/blink output/<nama>.mp4 [frameStart frameEnd]"""
import sys, os, subprocess, numpy as np, cv2
wd, out = sys.argv[1], sys.argv[2]
FPS, W, H = 30, 1080, 1920
M = np.load(os.path.join(wd, "matte.npy"))
G = os.path.join(wd, "g")
ORIGIN = (540, 650)

# ---- zoom (kunci masa, skala); langkah di titik potong untuk sembunyi jump-cut ----
CUTS = [3.12, 13.12, 34.34, 34.89, 35.80, 38.09]
KEYS = [(0,1.0),(2.9,1.06),(3.119,1.06),(3.12,1.0),(6.5,1.05),(10.0,1.05),(10.76,1.05),(11.2,1.14),(12.9,1.08),(13.119,1.08),
        (13.12,1.02),(17.0,1.07),(18.5,1.07),(19.0,1.11),(19.6,1.04),(21.2,1.03),(23.86,1.13),(24.6,1.02),(26.4,1.02),(28.6,1.09),(29.6,1.0),
        (34.0,1.04),(34.339,1.04),(34.34,1.09),(34.889,1.09),(34.89,1.0),(35.799,1.03),(35.80,1.08),(38.089,1.1),(38.09,1.0),(39.2,1.03)]
def zoom(t):
    for (a,sa),(b,sb) in zip(KEYS,KEYS[1:]):
        if a<=t<=b:
            if b-a<.01: return sb
            k=(t-a)/(b-a); k=k*k*(3-2*k); return sa+(sb-sa)*k
    return KEYS[-1][1]
def blur_amt(t):  # latar kabur bila sebut "kabur"
    return float(np.clip((t-18.52)/.3,0,1)*(1-np.clip((t-19.0)/.5,0,1)))

def affine(s, shift=(0,0)):
    return np.array([[s,0,ORIGIN[0]*(1-s)+shift[0]],[0,s,ORIGIN[1]*(1-s)+shift[1]]],np.float32)

p = subprocess.Popen(["ffmpeg","-v","error","-i",os.path.join(wd,"cut.mov"),"-f","rawvideo","-pix_fmt","bgr24","-"],stdout=subprocess.PIPE)
nf = len(M)
STILLS = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv)>3 and ',' in sys.argv[3] else None
f0 = int(sys.argv[3]) if len(sys.argv)>3 and not STILLS else 0
f1 = int(sys.argv[4]) if len(sys.argv)>4 and not STILLS else nf
enc = None if STILLS else subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-i",os.path.join(wd,"mix.wav"),"-map","0:v","-map","1:a","-vf","format=yuv420p",
    "-c:v","libx264","-crf","18","-preset","medium","-c:a","aac","-b:a","192k","-af","loudnorm=I=-14:TP=-1.5:LRA=11","-shortest",
    "-movflags","+faststart", out], stdin=subprocess.PIPE)
def matte_at(i):
    i=min(max(i,0),nf-1)
    return M[i].astype(np.float32)/255
for i in range(nf):
    b = p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    if i<f0 or i>=f1 or (STILLS and i not in STILLS): continue
    t = i/FPS
    base = np.frombuffer(b,np.uint8).reshape(H,W,3)
    m = .25*matte_at(i-1)+.5*matte_at(i)+.25*matte_at(i+1)
    m = cv2.resize(m,(W,H),interpolation=cv2.INTER_CUBIC)
    m = np.clip((m-.28)/.44,0,1)
    m = cv2.erode(m,np.ones((5,5),np.uint8)); m = cv2.GaussianBlur(m,(0,0),2.0)
    s = zoom(t)
    A = affine(s)
    base_z = cv2.warpAffine(base,A,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    m_z = cv2.warpAffine(m,A,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)[...,None]
    L = cv2.imread(f"{G}/back/{i:05d}.png",cv2.IMREAD_UNCHANGED).astype(np.float32)   # BGRA
    sb = 1+(s-1)*.5
    L = cv2.warpAffine(L,affine(sb),(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
    bg = base_z.astype(np.float32)
    ba = blur_amt(t)
    if ba>0:
        bg = bg*(1-ba)+cv2.GaussianBlur(bg,(0,0),22)*ba
        L = L*(1-ba)+cv2.GaussianBlur(L,(0,0),14)*ba
    a = L[...,3:4]/255
    bg = bg*(1-a)+L[...,:3]*a          # grafik di atas latar...
    comp = bg*(1-m_z)+base_z.astype(np.float32)*m_z   # ...tapi orang di depan grafik
    FR = cv2.imread(f"{G}/front/{i:05d}.png",cv2.IMREAD_UNCHANGED).astype(np.float32)
    fa = FR[...,3:4]/255
    comp = comp*(1-fa)+FR[...,:3]*fa
    if STILLS: cv2.imwrite(out%i, cv2.resize(np.clip(comp,0,255).astype(np.uint8),(540,960)))
    else: enc.stdin.write(np.clip(comp,0,255).astype(np.uint8).tobytes())
if not STILLS: enc.stdin.close(); enc.wait()
print("done", nf)
