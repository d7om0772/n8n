import wave, numpy as np, json
w = wave.open('../voiceover.wav'); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768
dur = len(x)/sr
hop = int(sr*0.01); n = len(x)//hop
rms = np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)+1e-12) for i in range(n)])
db = 20*np.log10(rms)
sm = np.convolve(db, np.ones(3)/3, mode='same')
segs = [
 (0.22,1.67,"إذا تسوي قهوتك في البيت؟"),
 (2.04,2.91,"هذا الفيديو لك"),
 (3.51,4.27,"حنا كلوفا"),
 (4.71,6.76,"متجر متخصص في محاصيل القهوة"),
 (7.30,7.79,"والفرق"),
 (8.10,9.28,"غالباً مو في المكينة"),
 (9.83,10.25,"الفرق"),
 (10.55,11.48,"في المحصول نفسه"),
 (11.95,12.58,"عشان كذا"),
 (13.00,14.94,"نوفر لك محاصيل من أكثر من بلد"),
 (15.34,16.29,"كل واحد له طعمه"),
 (16.75,18.51,"بدون ما تدفع كل يوم في الكوفيات"),
 (18.90,20.25,"وبدون ما تتنازل عن الطعم"),
 (20.79,22.50,"اختار محصولك من الرابط بالبايو"),
]
words=[]
for si,(s,e,t) in enumerate(segs):
    ws = t.split()
    L = [len(w.replace('ً','').replace('؟',''))+1.2 for w in ws]
    tot = sum(L); b=[s]; acc=s
    for l in L[:-1]:
        acc += (e-s)*l/tot
        # snap to local energy minimum within +-0.09s
        i0 = int((acc-0.09)*100); i1 = int((acc+0.09)*100)
        j = i0 + int(np.argmin(sm[i0:i1])); acc2 = j/100
        b.append(acc2)
    b.append(e)
    for k,wd in enumerate(ws):
        words.append(dict(seg=si, w=wd, s=round(b[k],3), e=round(b[k+1],3)))
json.dump(dict(duration=dur, segs=[dict(s=s,e=e,t=t) for s,e,t in segs], words=words), open('timing.json','w'), ensure_ascii=False, indent=1)
def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}"
with open('klova_coffee.srt','w') as f:
    for i,(s,e,t) in enumerate(segs,1):
        f.write(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n\n")
with open('klova_coffee_words.srt','w') as f:
    for i,wd in enumerate(words,1):
        f.write(f"{i}\n{ts(wd['s'])} --> {ts(wd['e'])}\n{wd['w']}\n\n")
print(dur)
for wd in words: print(wd['seg'], wd['s'], wd['e'], wd['w'])
