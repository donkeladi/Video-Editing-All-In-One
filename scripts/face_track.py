#!/usr/bin/env python3
"""Jejak muka setiap bingkai sumber (YuNet) -> work/face.json: [[x,y,w,h] dalam koordinat 1080x1920 | null]."""
import cv2, json, subprocess, numpy as np, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 540, 960
det = cv2.FaceDetectorYN.create(os.path.join(ROOT, "assets/models/yunet.onnx"), "", (W, H), 0.6, 0.3, 5000)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(ROOT, "input/raw.mov"), "-vf", f"scale={W}:{H}", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
out = []
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    img = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()
    _, f = det.detect(img)
    if f is not None and len(f):
        r = max(f, key=lambda r: r[2] * r[3]); out.append([int(r[0] * 2), int(r[1] * 2), int(r[2] * 2), int(r[3] * 2)])
    else: out.append(None)
json.dump(out, open(os.path.join(ROOT, "work/face.json"), "w"))
print(len(out), "bingkai;", sum(o is None for o in out), "tanpa muka")
