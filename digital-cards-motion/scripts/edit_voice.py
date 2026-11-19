"""Tighten pauses in the Gemini voiceover, keep it < 20s, and export per-phrase timings for the animation."""
import json, re, subprocess, sys
import numpy as np

SRC = "audio/vo_Charon.wav"
TEMPO = 1.03
PHRASES = ["بطاقتك الرقمية", "توصلك في ثواني", "بدون شحن", "وبدون انتظار", "اختر بطاقتك", "ادفع بأمان",
           "واستلم الكود فورًا على جوالك", "ألعاب", "تسوّق", "ترفيه", "كلها في مكان واحد",
           "البطاقات الرقمية", "أسرع هدية", "وأذكى اختيار"]
SENTENCE_END = {1, 3, 6, 10}           # phrase indices that end a sentence
GAP_IN, GAP_OUT, HEAD, TAIL = 0.10, 0.24, 0.25, 0.85
SR = 48000

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", SRC, "-af", f"atempo={TEMPO}", "-ar", str(SR), "-ac", "1",
                "-f", "f32le", "audio/_tmp.f32"], check=True)
x = np.fromfile("audio/_tmp.f32", dtype=np.float32)
log = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "audio/_tmp.f32",
                      "-af", "silencedetect=noise=-38dB:d=0.16", "-f", "null", "-"], capture_output=True, text=True).stderr
starts = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", log)]
dur = len(x) / SR
# speech segments = complement of silences
sil = sorted(zip([0.0] + starts if ends and (not starts or ends[0] < starts[0]) else starts, ends))
segs, cur = [], 0.0
for s, e in sil:
    if s - cur > 0.05: segs.append((cur, s))
    cur = e
if dur - cur > 0.05: segs.append((cur, dur))
print("segments:", len(segs), [(round(a, 2), round(b, 2)) for a, b in segs])
if len(segs) != len(PHRASES):
    sys.exit("segment count mismatch")

PRE, POST, FADE = 0.04, 0.09, int(0.012 * SR)
out = [np.zeros(int(HEAD * SR), np.float32)]
t, timings = HEAD, []
for i, (a, b) in enumerate(segs):
    a2, b2 = max(0, a - PRE), min(dur, b + POST)
    seg = x[int(a2 * SR):int(b2 * SR)].copy()
    seg[:FADE] *= np.linspace(0, 1, FADE); seg[-FADE:] *= np.linspace(1, 0, FADE)
    timings.append({"i": i, "text": PHRASES[i], "start": round(t + (a - a2), 3), "end": round(t + (b - a2), 3)})
    out.append(seg); t += len(seg) / SR
    if i < len(segs) - 1:
        g = GAP_OUT if i in SENTENCE_END else GAP_IN
        out.append(np.zeros(int(g * SR), np.float32)); t += g
out.append(np.zeros(int(TAIL * SR), np.float32)); t += TAIL
y = np.concatenate(out)
y.astype(np.float32).tofile("audio/_tight.f32")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "audio/_tight.f32",
                "-af", "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=80,loudnorm=I=-15:TP=-1.5:LRA=7",
                "-ar", str(SR), "-ac", "2", "audio/voiceover_final.wav"], check=True)
for f in ("audio/_tmp.f32", "audio/_tight.f32"):
    import os; os.remove(f)
json.dump({"duration": round(len(y) / SR, 3), "phrases": timings}, open("audio/timings.json", "w"), ensure_ascii=False, indent=1)
print("final duration:", round(len(y) / SR, 3))
for p in timings: print(p)
