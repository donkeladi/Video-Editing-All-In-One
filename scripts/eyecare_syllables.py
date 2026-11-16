import numpy as np, wave, re, json
w=wave.open("work/cut16.wav");x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float);sr=16000
# bandpass via FFT
X=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/sr);X[(f<300)|(f>3000)]=0;y=np.fft.irfft(X,len(x))
e=np.sqrt(np.convolve(y**2,np.ones(320)/320,'same'))[::160]
g=np.exp(-0.5*(np.arange(-12,13)/3.0)**2);g/=g.sum();s=np.convolve(e,g,'same')
mx=s.max();pk=[]
for i in range(3,len(s)-3):
    if s[i]==s[i-3:i+4].max() and s[i]>mx*0.10:
        # prominence: dip to left/right
        l=s[max(0,i-12):i].min();r=s[i+1:i+13].min()
        if s[i]-max(l,r)>mx*0.035: pk.append(i)
pk=np.array(pk)/100
print(len(pk),"peaks",len(s)/100)
json.dump(pk.tolist(),open("work/peaks.json","w"))
