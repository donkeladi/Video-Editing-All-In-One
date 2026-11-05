#!/usr/bin/env python3
"""Ukur sharpness (Laplacian var) dan gegar (pergerakan global, frame-ke-frame) per klip."""
import cv2, numpy as np, sys, glob, os
for p in sorted(glob.glob(sys.argv[1])):
    c = cv2.VideoCapture(p); prev=None; S=[]; M=[]
    while True:
        ok,f = c.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(f,(270,480)),cv2.COLOR_BGR2GRAY)
        S.append(cv2.Laplacian(g,cv2.CV_64F).var())
        if prev is not None:
            (dx,dy),_ = cv2.phaseCorrelate(np.float32(prev),np.float32(g)); M.append((dx,dy))
        prev=g
    M=np.array(M); S=np.array(S)
    # gegar = jitter selepas buang gerakan perlahan (high-pass trajectory)
    traj=np.cumsum(M,0); k=9
    smooth=np.stack([np.convolve(np.pad(traj[:,i],(k//2,k//2),'edge'),np.ones(k)/k,'valid') for i in (0,1)],1)
    jit=np.linalg.norm(traj-smooth,axis=1)
    print(os.path.basename(p), f"frames={len(S)} sharp med={np.median(S):.1f} min={S.min():.1f} | jitter mean={jit.mean():.2f} max={jit.max():.2f}")
    print("  sharp/0.5s:", " ".join(f"{S[i:i+15].mean():.0f}" for i in range(0,len(S),15)))
    print("  jitter/0.5s:", " ".join(f"{jit[i:i+15].mean():.1f}" for i in range(0,len(jit),15)))
