#!/usr/bin/env python3
"""Jana matte orang per frame -> work/blink/matte.npy (uint8, 480x270). Guna: blink_matte.py cut.mov u2net_human_seg.onnx out_dir"""
import sys, os, subprocess, numpy as np, cv2, onnxruntime as ort
vid, model, out = sys.argv[1:4]
sess=ort.InferenceSession(model,providers=["CPUExecutionProvider"])
mean=np.array([0.485,0.456,0.406],np.float32); std=np.array([0.229,0.224,0.225],np.float32)
W,H=1080,1920
p=subprocess.Popen(["ffmpeg","-v","error","-i",vid,"-f","rawvideo","-pix_fmt","bgr24","-"],stdout=subprocess.PIPE)
M=[]
while True:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    im=np.frombuffer(b,np.uint8).reshape(H,W,3)
    x=cv2.resize(cv2.cvtColor(im,cv2.COLOR_BGR2RGB),(320,320),interpolation=cv2.INTER_AREA).astype(np.float32)/255
    o=sess.run(None,{sess.get_inputs()[0].name:((x-mean)/std).transpose(2,0,1)[None]})[0][0,0]
    o=(o-o.min())/(o.max()-o.min()+1e-6)
    M.append((cv2.resize(o,(270,480),interpolation=cv2.INTER_AREA)*255).astype(np.uint8))
np.save(os.path.join(out,"matte.npy"),np.array(M)); print(len(M))
