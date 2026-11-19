import wave, numpy as np, json, sys
src,out,meta=sys.argv[1:4]
w=wave.open(src); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)
# (start,end,label, gap_after)
segs=[(0.28,1.83,'title',0.28),(2.61,5.16,'title2',0.42),
      (6.21,7.34,'choose',0.22),(7.97,8.55,'games',0.16),(9.07,9.68,'shop',0.16),(10.11,10.82,'fun',0.42),
      (11.98,12.98,'pay',0.2),(13.35,14.63,'pay2',0.42),
      (15.71,18.10,'code',0.42),
      (19.13,20.51,'outro',0.24),(21.11,22.64,'outro2',0.0)]
PAD=0.07; LEAD=0.35; pieces=[np.zeros(int(LEAD*sr))]; t=LEAD; marks=[]
for s,e,lab,gap in segs:
    s=max(0,s-PAD); e=min(len(a)/sr,e+PAD)
    seg=a[int(s*sr):int(e*sr)].copy(); f=int(0.012*sr); seg[:f]*=np.linspace(0,1,f); seg[-f:]*=np.linspace(1,0,f)
    marks.append({'label':lab,'start':round(t,3),'end':round(t+len(seg)/sr,3)}); pieces.append(seg); t+=len(seg)/sr
    pieces.append(np.zeros(int(gap*sr))); t+=gap
y=np.concatenate(pieces); y=np.clip(y,-32768,32767).astype(np.int16)
o=wave.open(out,'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(y.tobytes())
json.dump(marks,open(meta,'w'),ensure_ascii=False,indent=1); print('total',round(t,2)); [print(m) for m in marks]
