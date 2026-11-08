"""Mixes the voiceover with the sound-effect events (no music) and writes mix.wav.
usage: python mix.py <voiceover.wav> <out.wav> [sfx_dir]"""
import sys, os, subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

SR = 48000
TOTAL = 35.0
HERE = os.path.dirname(os.path.abspath(__file__))
vo_path, out = sys.argv[1], sys.argv[2]
SFX = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'sfx_synth')

# (time s, sound, gain dB) -- times follow the animation cues in index.html
EV = [
    (0.02, 'swell', -14), (0.80, 'swipe', -17), (1.00, 'whoosh', -14), (1.30, 'swipe', -17), (1.47, 'pop', -15),
    (2.00, 'whoosh', -11), (2.30, 'riser', -19), (2.80, 'pop', -15), (3.02, 'click', -16),
    (3.24, 'whoosh', -11), (3.62, 'pop_hi', -17), (3.74, 'scribble', -18), (3.97, 'whoosh_down', -18), (3.98, 'ding', -13),
    (4.94, 'whoosh_big', -10), (5.10, 'swipe_hi', -20), (5.70, 'pop', -15), (6.12, 'swipe', -16), (6.62, 'impact', -9),
    (7.52, 'shutter', -12), (7.56, 'thump', -14), (7.86, 'shutter', -13), (8.14, 'pop', -15), (8.20, 'shutter', -13), (8.54, 'shutter', -13),
    (8.88, 'whoosh', -11), (8.96, 'pop_hi', -17), (10.20, 'swipe_hi', -20), (10.38, 'kaching', -10),
    (11.36, 'whoosh', -11), (11.44, 'pop', -17), (12.95, 'key_enter', -13),
    (13.00, 'swipe', -16), (13.14, 'swipe', -17), (13.28, 'swipe', -17),
    (14.08, 'click', -16), (14.20, 'click', -17), (14.32, 'click', -17),
    (15.20, 'pop', -14), (15.32, 'pop', -15), (15.44, 'pop', -15),
    (16.56, 'whoosh_big', -11), (17.70, 'swipe', -16), (18.12, 'impact', -10), (18.48, 'whoosh', -15),
    (19.86, 'click', -13), (19.95, 'pop_hi', -16),
    (20.72, 'glitch', -11), (20.78, 'buzz', -19), (20.92, 'glitch2', -12), (21.40, 'whoosh', -13),
    (21.56, 'swipe', -15), (22.30, 'tick', -15), (23.02, 'swipe', -15), (23.86, 'tick', -15), (24.42, 'swipe', -15), (24.66, 'pling', -15),
    (26.12, 'whoosh', -11), (27.75, 'swipe_hi', -20), (28.00, 'swipe', -16), (28.18, 'swipe', -16),
    (28.94, 'pop', -15), (29.05, 'pop_hi', -18), (29.25, 'pop', -15), (30.22, 'coins', -11), (30.24, 'thump', -16),
    (30.92, 'whoosh_big', -11), (31.06, 'swipe_hi', -20), (31.88, 'swipe', -17), (32.00, 'pop', -16),
    (32.62, 'whoosh', -14), (33.40, 'swipe', -17), (33.65, 'pop', -15), (34.05, 'pling', -14),
]
# counting ticks (6,000 and 1,000 counters)
for a, d in ((9.62, .62), (29.44, .72)):
    k = 0
    while True:
        p = (k / 9) ** 1.6
        if p > 1: break
        EV.append((a + d * p, 'tick', -21)); k += 1
# typing: search bar (15 chars in 1.28 s), letters of "أختار لك" (8 in .42 s), comment box (10 in .55 s)
for a, n, d, g in ((11.62, 15, 1.28, -15), (31.48, 8, .42, -19), (33.02, 10, .55, -16)):
    for i in range(n):
        EV.append((a + d * (i + .5) / n, f'key{i % 6}', g))


def load(p):
    sr, x = wavfile.read(p)
    x = x.astype(np.float32) / (32768.0 if x.dtype == np.int16 else 1.0)
    if x.ndim == 1: x = np.stack([x, x], 1)
    if sr != SR: x = resample_poly(x, SR, sr, axis=0)
    return x


mix = np.zeros((int(SR * TOTAL), 2), np.float32)
vo = load(vo_path)
mix[:len(vo)] += vo[:len(mix)] * 1.0
fx = np.zeros_like(mix)
cache = {}
for t, name, g in EV:
    if name not in cache:
        cache[name] = load(os.path.join(SFX, name + '.wav'))
    s = cache[name] * (10 ** (g / 20))
    i = int(t * SR)
    n = min(len(s), len(fx) - i)
    if n > 0: fx[i:i + n] += s[:n]
mix += fx
tmp = out + '.raw.wav'
wavfile.write(tmp, SR, np.clip(mix, -1, 1).astype(np.float32))
# loudness-normalise for TikTok (-14 LUFS, -1 dBTP)
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1.0:LRA=11', '-ar', str(SR), '-c:a', 'pcm_s16le', out], check=True)
os.remove(tmp)
print('events', len(EV), '->', out)
