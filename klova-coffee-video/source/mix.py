import numpy as np, wave, json, subprocess
SR=48000
def readwav(p):
    w=wave.open(p); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    if w.getnchannels()==2: x=x.reshape(-1,2).mean(1)
    return x, sr
# VO -> 48k via ffmpeg
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i','../voiceover.wav','-ar',str(SR),'-ac','1','vo48.wav'],check=True)
vo,_ = readwav('vo48.wav')
dur = json.load(open('timing.json'))['duration']
N = int(round(dur*SR))
vo = np.pad(vo,(0,max(0,N-len(vo))))[:N]
vo = vo/np.max(np.abs(vo))*0.89
fx = np.zeros(N, np.float32)
MASTER = 0.38
for ev in json.load(open('sfx_events.json')):
    x,_ = readwav(f"sfx/{ev['name']}.wav")
    o = int(round(max(0,ev['t'])*SR)); n = min(len(x), N-o)
    if n>0: fx[o:o+n] += x[:n]*ev['gain']*MASTER
# gentle ducking of sfx while voice is loud
env = np.convolve(np.abs(vo), np.ones(2400)/2400, mode='same')
duck = 1 - 0.35*np.clip(env/0.12,0,1)
mix = vo + fx*duck
mix = mix/ max(1.0, np.max(np.abs(mix))/0.97)
with wave.open('mix_raw.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
with wave.open('sfx_only.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(fx,-1,1)*32767).astype(np.int16).tobytes())
# loudness normalise for TikTok (~-14 LUFS, TP -1.5)
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i','mix_raw.wav','-af','loudnorm=I=-14:TP=-1.5:LRA=11','-ar',str(SR),'-ac','2','mix.wav'],check=True)
print('mixed', N/SR)
