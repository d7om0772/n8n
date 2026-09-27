import numpy as np, wave, sys
from scipy import signal

SR = 48000
DUR = 20.8
rng = np.random.default_rng(7)

def t_(d): return np.arange(int(d * SR)) / SR

def adsr(n, a=0.002):
    e = np.ones(n); k = max(1, int(a * SR)); e[:k] = np.linspace(0, 1, k); return e

def bandnoise(d, lo, hi, order=4):
    x = rng.uniform(-1, 1, int(d * SR))
    sos = signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
    return signal.sosfilt(sos, x)

def lowpass(x, fc, order=4):
    return signal.sosfilt(signal.butter(order, fc, 'lowpass', fs=SR, output='sos'), x)

def highpass(x, fc, order=4):
    return signal.sosfilt(signal.butter(order, fc, 'highpass', fs=SR, output='sos'), x)

def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1; return x / m * peak

def sweep_noise(d, f0, f1, width=0.5, env=None):
    """noise whose spectral centre moves f0->f1 (log), via STFT masking"""
    n = int(d * SR); x = rng.uniform(-1, 1, n + 2048)
    f, tt, Z = signal.stft(x, SR, nperseg=1024, noverlap=768)
    prog = np.clip(tt / d, 0, 1)
    fc = np.exp(np.log(f0) + (np.log(f1) - np.log(f0)) * prog)
    lf = np.log(np.maximum(f, 1))[:, None]
    mask = np.exp(-0.5 * ((lf - np.log(fc)[None, :]) / width) ** 2)
    _, y = signal.istft(Z * mask, SR, nperseg=1024, noverlap=768)
    y = y[:n]
    if env is not None: y *= env(np.arange(n) / n)
    return norm(y)

def thump(f0, f1, d=0.35, tau=0.12, ftau=0.035):
    t = t_(d); f = f1 + (f0 - f1) * np.exp(-t / ftau)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / tau) * adsr(len(t), 0.002)

def snap(d=0.06, tau=0.018):
    x = bandnoise(d, 1500, 7000); return norm(x * np.exp(-t_(d) / tau))

def blip(f, d=0.12, tau=0.045, up=1.0):
    t = t_(d); ff = f * (1 + up * np.exp(-t / 0.012))
    return np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t / tau) * adsr(len(t), 0.001)

def bell(f, d=1.2, partials=((1, 1, .6), (2.0, .5, .35), (2.76, .35, .25), (5.4, .2, .12))):
    t = t_(d); y = np.zeros_like(t)
    for m, a, tau in partials: y += a * np.sin(2 * np.pi * f * m * t + rng.uniform(0, 6)) * np.exp(-t / tau)
    return y * adsr(len(t), 0.001)

def reverb(x, wet=0.14, d=0.9):
    ir = rng.uniform(-1, 1, int(d * SR)) * np.exp(-t_(d) / 0.22)
    ir = lowpass(ir, 5000); ir /= np.sqrt(np.sum(ir ** 2))
    w = signal.fftconvolve(x, ir)[:len(x)]
    return x + wet * w

# ---------------- sound library ----------------
def s_hit(p):
    body = 0.95 * thump(150 * p, 48 * p, 0.4, 0.11)
    s = np.zeros_like(body); sn = 0.3 * snap(); s[:len(sn)] += sn
    b = blip(620 * p, 0.14, 0.05, 0.6) * 0.3; s[:len(b)] += b
    return body + s

def s_pop(f=520):
    return blip(f, 0.1, 0.03, 1.2)

def s_whoosh(d=0.45, f0=500, f1=3500):
    return sweep_noise(d, f0, f1, 0.55, env=lambda u: np.sin(np.pi * np.clip(u, 0, 1)) ** 2)

def s_riser(d=1.25):
    n = sweep_noise(d, 250, 7000, 0.45, env=lambda u: u ** 2.2)
    t = t_(d); f = 180 * (4.5 ** (t / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2 * 0.35
    return norm(n[:len(t)] * 0.8 + tone)

def s_impact():
    d = 1.4
    b = thump(95, 32, d, 0.38, 0.06)
    n = lowpass(rng.uniform(-1, 1, int(d * SR)), 900) * np.exp(-t_(d) / 0.18) * 1.6
    c = np.zeros_like(b); sn = snap(0.08, 0.03); c[:len(sn)] = sn * 0.35
    return norm(b + n + c)

def s_ching():
    d = 0.9; y = np.zeros(int(d * SR))
    for off, amp in ((0.0, 1.0), (0.075, 0.8)):
        t = t_(d - off)
        z = sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / tau)
                for f, a, tau in ((2093, .6, .30), (3136, .5, .22), (4186, .45, .16), (5274, .3, .12), (6645, .25, .08)))
        i = int(off * SR); y[i:i + len(z)] += amp * z
    click = snap(0.02, 0.004); y[:len(click)] += click * 0.4
    # small coin tinks as they land
    for k in range(5):
        off = 0.35 + k * 0.09 + rng.uniform(0, 0.03); tb = blip(rng.uniform(3500, 5200), 0.08, 0.02, 0.0) * (0.35 - k * 0.05)
        i = int(off * SR); y[i:i + len(tb)] += tb[:max(0, len(y) - i)]
    return norm(y)

def s_stamp():
    b = thump(120, 38, 0.45, 0.12)
    n = lowpass(rng.uniform(-1, 1, len(b)), 1800) * np.exp(-t_(0.45) / 0.03)
    return norm(b + 0.9 * n)

def s_flick():
    return norm(bandnoise(0.03, 2200, 6500) * np.exp(-t_(0.03) / 0.006))

def s_tick():
    return blip(2600, 0.04, 0.008, 0.2)

def s_sparkle():
    d = 0.9; y = np.zeros(int(d * SR))
    for k in range(16):
        off = k * 0.045 + rng.uniform(0, 0.02); b = blip(rng.uniform(3200, 7400), 0.1, 0.035, 0.0) * (1 - k / 18)
        i = int(off * SR); y[i:i + len(b)] += b[:max(0, len(y) - i)]
    return norm(y)

def s_chime():
    d = 1.6; y = np.zeros(int(d * SR))
    for k, f in enumerate((1046.5, 1318.5, 1568.0, 2093.0)):
        b = bell(f, d - k * 0.08) * (1 - k * 0.12); i = int(k * 0.08 * SR); y[i:i + len(b)] += b
    return norm(y)

def s_scratch():
    return sweep_noise(0.22, 900, 3500, 0.35, env=lambda u: np.sin(np.pi * np.clip(u, 0, 1)) ** 0.7)

# ---------------- timeline ----------------
N = int(DUR * SR)
bus = np.zeros((N, 2))

def place(x, t, db, pan=0.0):
    g = 10 ** (db / 20); i = int(t * SR)
    x = x[:max(0, N - i)]
    l = g * np.cos((pan + 1) * np.pi / 4) * np.sqrt(2); r = g * np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
    bus[i:i + len(x), 0] += x * l; bus[i:i + len(x), 1] += x * r

FILL = [3.32, 4.36, 5.26, 7.66, 9.08, 10.44]
PAN = [0.35, -0.35, 0.35, -0.35, 0.35, -0.35]

# grid lines drawing
place(s_whoosh(0.5, 300, 2500), 0.0, -24)
for i in range(6): place(s_tick(), 0.05 + i * 0.07, -27, PAN[i])
# hook words
for tt, f, db in ((0.02, 480, -17), (0.44, 540, -17), (0.78, 400, -12), (1.2, 600, -18), (1.3, 660, -17)):
    place(s_pop(f), tt, db)
place(thump(110, 45, 0.3, 0.08), 0.78, -16)
place(s_whoosh(0.35, 800, 5000), 1.66, -20)
place(s_pop(720), 1.88, -13)
place(s_pop(900), 2.68, -15)
place(s_whoosh(0.4, 3000, 400), 2.95, -20)
# cells open on the beat, rising pitch
for k, (tt, pn) in enumerate(zip(FILL, PAN)):
    place(s_hit(1 + 0.07 * k), tt - 0.005, -9 + (2 if k == 5 else 0), pn * 0.6)
place(s_sparkle(), 10.46, -21, -0.3)
# stamp on the machine
place(s_stamp(), 8.02, -9, -0.3)
# origin chips pop with ascending pentatonic pitch
pent = [523, 587, 659, 784, 880, 1046]
for i in range(6): place(s_pop(pent[i]), 11.40 + i * 0.22, -15, PAN[i] * 0.8)
# flips to taste notes
for i in range(6): place(s_flick(), 13.18 + i * 0.2 + 0.08, -19, PAN[i] * 0.8)
for i in range(6): place(s_tick(), 13.18 + i * 0.2 + 0.1, -25, PAN[i] * 0.8)
# chips out
place(s_whoosh(0.3, 2500, 600), 14.58, -24)
# coins / paying
place(s_ching(), 15.0, -13)
# strike through "الكوفيّات"
place(s_scratch(), 16.13, -19)
# build-up + impact for the hero expansion
place(s_riser(1.2), 16.78 - 1.2, -15)
place(s_impact(), 16.78, -7)
place(s_whoosh(0.7, 300, 2800), 16.8, -17)
# kettle lifts away, CTA
place(s_whoosh(0.45, 1500, 500), 18.45, -24)
place(s_sparkle(), 18.8, -20)
place(s_chime(), 18.8, -19)
place(s_pop(640), 19.08, -18)
place(s_pop(700), 19.5, -14)
place(bell(1568, 0.9) * 0.9, 20.03, -16)
place(s_pop(420), 20.03, -18)

bus[:, 0] = reverb(bus[:, 0]); bus[:, 1] = reverb(bus[:, 1])

# ---------------- voice ----------------
with wave.open(sys.argv[1]) as w:
    sr = w.getframerate(); v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
v = signal.resample_poly(v, SR, sr)
v = norm(v, 0.89)
out = np.zeros((N, 2))
L = min(N, len(v)); out[:L, 0] += v[:L]; out[:L, 1] += v[:L]
out += bus
pk = np.max(np.abs(out))
if pk > 0.97: out *= 0.97 / pk
print('voice len', len(v) / SR, 'peak', pk)
with wave.open(sys.argv[2], 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
with wave.open(sys.argv[3], 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    b = bus / max(1e-9, np.max(np.abs(bus))) * 0.9
    w.writeframes((b * 32767).astype(np.int16).tobytes())
