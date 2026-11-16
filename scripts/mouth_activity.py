#!/usr/bin/env python3
"""Gerak mulut orang kiri (putih) & kanan (merah) dalam kamera B -> work/mouth_B.npy  (frame, [kiri,kanan])"""
import cv2,numpy as np,os
c=cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades,"haarcascade_frontalface_default.xml"))
cap=cv2.VideoCapture("input/B.mp4");SW=540
box={"L":None,"R":None};prevroi={"L":None,"R":None};rows=[];n=0;found=[0,0]
while True:
    ok,f=cap.read()
    if not ok:break
    s=SW/f.shape[1];g=cv2.cvtColor(cv2.resize(f,(SW,int(f.shape[0]*s))),cv2.COLOR_BGR2GRAY)
    H=g.shape[0]
    if n%3==0:
        fs=c.detectMultiScale(g[:int(H*.6)],1.1,6,minSize=(50,50))
        for side,rng in (("L",(0,SW*.5)),("R",(SW*.5,SW))):
            cand=[x for x in fs if rng[0]<=x[0]+x[2]/2<rng[1]]
            if cand:
                x=max(cand,key=lambda r:r[2]);new=np.array(x,float)
                box[side]=new if box[side] is None else .6*box[side]+.4*new
                found[0 if side=="L" else 1]+=1
    row=[]
    for side in "LR":
        b=box[side]
        if b is None:row.append(0);continue
        x,y,w,h=b.astype(int);y2=y+int(h*.62);ym=y+int(h*.6)
        roi=g[ym:y+int(h*1.05),x+int(w*.2):x+int(w*.8)]
        if roi.size==0:row.append(0);continue
        roi=cv2.resize(roi,(40,20)).astype(np.float32)
        row.append(0 if prevroi[side] is None else np.abs(roi-prevroi[side]).mean());prevroi[side]=roi
    rows.append(row);n+=1
np.save("work/mouth_B.npy",np.array(rows));print(n,"found L/R per 3rd frame",found)
