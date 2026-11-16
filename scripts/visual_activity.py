#!/usr/bin/env python3
"""Aktiviti gerak kiri (baju putih) vs kanan (baju merah) dalam kamera B, stabil global. -> work/motion_B.npy"""
import cv2,numpy as np,sys
cap=cv2.VideoCapture("input/B.mp4");prev=None;rows=[]
while True:
    ok,f=cap.read()
    if not ok:break
    g=cv2.cvtColor(cv2.resize(f,(216,394)),cv2.COLOR_BGR2GRAY).astype(np.float32)
    if prev is None: rows.append((0,0,0,0));prev=g;continue
    (dx,dy),_=cv2.phaseCorrelate(prev,g)
    M=np.float32([[1,0,-dx],[0,1,-dy]]);gw=cv2.warpAffine(g,M,(216,394),borderMode=cv2.BORDER_REPLICATE)
    d=np.abs(gw-prev);d=cv2.GaussianBlur(d,(5,5),0)
    top=d[int(394*.25):int(394*.62)]
    # kepala sahaja (lebih tinggi) utk mulut
    head=d[int(394*.28):int(394*.48)]
    rows.append((top[:,:100].mean(),top[:,116:].mean(),head[:,:100].mean(),head[:,116:].mean()));prev=g
np.save("work/motion_B.npy",np.array(rows));print(len(rows))
