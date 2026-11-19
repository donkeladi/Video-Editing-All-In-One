#!/usr/bin/env python3
"""Matte penyampai (MODNet ONNX, Apache-2.0) untuk setiap bingkai -> work/matte/NNNNN.png (576x1024, uint8).
Model: https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx  -> work/models/modnet.onnx
Guna: eyecare_matte.py <video> <last_frame> [workers]"""
import sys, os, subprocess, numpy as np
from multiprocessing import Pool
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL = os.path.join(ROOT, "work/models/modnet.onnx"); OUT = os.path.join(ROOT, "work/matte"); FPS = 30
def job(a):
    video, s, e = a
    import onnxruntime as ort, cv2
    so = ort.SessionOptions(); so.intra_op_num_threads = 1
    sess = ort.InferenceSession(MODEL, so, providers=["CPUExecutionProvider"]); name = sess.get_inputs()[0].name
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{s / FPS:.5f}", "-i", video, "-frames:v", str(e - s + 1), "-vf", "scale=576:1024:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    sz = 576 * 1024 * 3
    for i in range(s, e + 1):
        b = p.stdout.read(sz)
        if len(b) < sz: break
        x = np.frombuffer(b, np.uint8).reshape(1024, 576, 3).astype(np.float32) / 127.5 - 1
        a = sess.run(None, {name: x.transpose(2, 0, 1)[None]})[0][0, 0]
        cv2.imwrite(f"{OUT}/{i:05d}.png", (a.clip(0, 1) * 255).astype(np.uint8))
    p.wait(); return s
if __name__ == "__main__":
    video, last = sys.argv[1], int(sys.argv[2]); nw = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    os.makedirs(OUT, exist_ok=True); n = last + 1; step = -(-n // (nw * 4))
    jobs = [(video, s, min(last, s + step - 1)) for s in range(0, n, step)]
    with Pool(nw) as p: p.map(job, jobs, chunksize=1)
    print("matte siap", len(os.listdir(OUT)))
