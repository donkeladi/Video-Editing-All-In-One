#!/usr/bin/env python3
"""Diarization ringkas: MFCC+F0 per perkataan -> KMeans. Output work/words_spk.json"""
import json,sys,numpy as np,librosa
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
y,sr=librosa.load("work/A.mp3",sr=16000)
segs=json.load(open("work/A.json"))
W=[w|{"seg":i} for i,s in enumerate(segs) for w in s["words"]]
X=[];idx=[]
for i,w in enumerate(W):
    a,b=int(w["s"]*sr),int(w["e"]*sr)
    if b-a<sr*0.18: continue
    c=y[a:b]
    m=librosa.feature.mfcc(y=c,sr=sr,n_mfcc=20,n_fft=512,hop_length=160).mean(1)
    f=librosa.yin(c,fmin=90,fmax=450,sr=sr,frame_length=1024); f0=np.median(f)
    X.append(np.r_[m[1:],np.log(f0)*3]);idx.append(i)
Xs=StandardScaler().fit_transform(np.array(X))
k=int(sys.argv[1]) if len(sys.argv)>1 else 2
lab=KMeans(k,n_init=20,random_state=0).fit_predict(Xs)
for j,l in zip(idx,lab): W[j]["spk"]=int(l)
json.dump(W,open("work/words_spk.json","w"),ensure_ascii=False)
for c in range(k):
    ws=[W[j] for j,l in zip(idx,lab) if l==c]; print("cluster",c,len(ws),"f0",np.exp(np.median([X[idx.index(W.index(w))][-1] for w in ws])/3).round(0),[w["w"] for w in ws[:25]])
