#!/usr/bin/env python3
"""Hasilkan alpha matte orang (RVM, onnxruntime) → .npy memmap uint8 (N,H,W) pada 540x960.
Guna: matte_person.py <video> <rvm.onnx> <out.npy>"""
import sys, cv2, numpy as np, onnxruntime as ort
vid, model, out = sys.argv[1:4]
W, H = 540, 960
cap = cv2.VideoCapture(vid); N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
s = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
rec = [np.zeros((1,1,1,1), np.float32) for _ in range(4)]
ratio = np.array([0.5], np.float32)
mm = np.lib.format.open_memmap(out, mode='w+', dtype=np.uint8, shape=(N, H, W))
i = 0
while True:
    ok, f = cap.read()
    if not ok: break
    x = cv2.cvtColor(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
    x = (x.astype(np.float32)/255).transpose(2,0,1)[None]
    fgr, pha, *rec = s.run(None, dict(src=x, r1i=rec[0], r2i=rec[1], r3i=rec[2], r4i=rec[3], downsample_ratio=ratio))
    mm[i] = (np.clip(pha[0,0], 0, 1)*255).astype(np.uint8); i += 1
    if i % 100 == 0: print(i, N, flush=True)
mm.flush(); print('done', i)
