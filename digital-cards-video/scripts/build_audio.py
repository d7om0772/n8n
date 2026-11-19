import wave, json, subprocess, numpy as np, os
SR = 24000
HEAD, GAP, TAIL, MAXLEN = 0.30, 0.16, 0.75, 19.8
def load(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
def save(p, x, sr=SR):
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(np.clip(x, -32768, 32767).astype(np.int16).tobytes())
def compress(x, thr_db=-40, max_pause=0.20, win=0.01):
    n = int(SR * win); frames = len(x) // n
    rms = np.array([np.sqrt(np.mean(x[i*n:(i+1)*n]**2) + 1e-9) for i in range(frames)])
    db = 20 * np.log10(rms / 32768); voiced = db > thr_db
    idx = np.where(voiced)[0]; first, last = idx[0], idx[-1]
    out, i, keep = [], first, int(max_pause / win)
    while i <= last:
        if voiced[i]: out.append(x[i*n:(i+1)*n]); i += 1
        else:
            j = i
            while j <= last and not voiced[j]: j += 1
            run = j - i; k = min(run, keep)
            seg = x[i*n:(i+k)*n].copy()  # keep the start of the pause (natural decay), fade it
            out.append(seg * np.linspace(1, 0.0, len(seg))); i = j
    pad = int(0.04 * SR)  # tiny lead-in/out so consonants aren't clipped
    pre = x[max(0, first*n - pad):first*n]; post = x[(last+1)*n:(last+1)*n + pad]
    return np.concatenate([pre] + out + [post])
clips = [compress(load(f"audio/s{i}.wav")) for i in range(1, 6)]
speech = sum(len(c) for c in clips) / SR
budget = MAXLEN - HEAD - TAIL - GAP * 4
tempo = max(1.0, speech / budget)
print(f"speech {speech:.2f}s budget {budget:.2f}s tempo {tempo:.3f}")
os.makedirs("audio/proc", exist_ok=True)
durs = []
for i, c in enumerate(clips, 1):
    save(f"audio/proc/c{i}.wav", c)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"audio/proc/c{i}.wav", "-af",
        f"rubberband=tempo={tempo:.4f}:pitchq=quality:transients=smooth,aresample=48000", f"audio/proc/t{i}.wav"], check=True)
    with wave.open(f"audio/proc/t{i}.wav") as w: durs.append(w.getnframes() / w.getframerate())
t, starts = HEAD, []
for d in durs: starts.append(t); t += d + GAP
total = t - GAP + TAIL
segs = [(s, s + d) for s, d in zip(starts, durs)]
json.dump({"tempo": tempo, "voice": segs, "total": round(total, 3)}, open("timeline.json", "w"), indent=1)
print(json.dumps(segs), "total", round(total, 3))
# assemble narration track at 48k
out = np.zeros(int(total * 48000) + 10, dtype=np.float32)
for i, s in enumerate(starts, 1):
    with wave.open(f"audio/proc/t{i}.wav") as w: x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    a = int(s * 48000); out[a:a+len(x)] += x
save("audio/narration_raw.wav", out, 48000)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "audio/narration_raw.wav", "-af",
    "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=80,loudnorm=I=-15:TP=-1.5:LRA=7", "-ar", "48000", "audio/narration.wav"], check=True)
