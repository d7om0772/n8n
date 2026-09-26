"""Synthesised score + foley for the 15s collage piece (120 BPM, bars start on odd seconds)."""
import wave
import numpy as np
from scipy import signal

SR = 44100
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(7)

drums = np.zeros((2, N))
music = np.zeros((2, N))
sfx = np.zeros((2, N))
send = np.zeros((2, N))  # reverb send


def tt(n):
    return np.arange(n) / SR


def noise(d):
    return rng.standard_normal(int(d * SR))


def filt(x, kind, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype=kind, fs=SR, output='sos'), x)


def sweep(f_arr):
    return np.sin(2 * np.pi * np.cumsum(f_arr) / SR)


def add(bus, sig, t, gain=1.0, pan=0.0, rev=0.0):
    i = int(round(t * SR))
    if i >= N or i + len(sig) <= 0:
        return
    s = sig[: N - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4) * 1.4142, np.sin((pan + 1) * np.pi / 4) * 1.4142
    bus[0, i:i + len(s)] += s * l
    bus[1, i:i + len(s)] += s * r
    if rev:
        send[0, i:i + len(s)] += s * l * rev
        send[1, i:i + len(s)] += s * r * rev


# ---------------- drums ----------------
def kick(d=0.45, low=48, tau=0.28):
    n = int(d * SR); t = tt(n)
    body = sweep(low + 115 * np.exp(-t / 0.032)) * np.exp(-t / tau)
    click = filt(noise(d), 'highpass', 3000) * np.exp(-t / 0.003) * 0.35
    return np.tanh((body + click) * 1.6)


def clap():
    d = 0.35; n = int(d * SR); t = tt(n); e = np.zeros(n)
    for o in (0, 0.011, 0.023):
        k = int(o * SR); e[k:] += np.exp(-(t[: n - k]) / 0.0045)
    e += 0.55 * np.exp(-t / 0.085)
    return filt(noise(d) * e, 'bandpass', [900, 3800])


def hat(open_=False):
    d = 0.3 if open_ else 0.08; t = tt(int(d * SR))
    return filt(noise(d), 'highpass', 7200) * np.exp(-t / (0.12 if open_ else 0.028))


def snare():
    d = 0.3; t = tt(int(d * SR))
    return filt(noise(d), 'bandpass', [1400, 7000]) * np.exp(-t / 0.1) + 0.6 * np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.06)


# ---------------- synths ----------------
def saw(f, t, ph):
    return signal.sawtooth(2 * np.pi * f * t + ph)


def pad(freqs, d, cutoff=1400, attack=0.35, release=0.6, det=0.005):
    n = int(d * SR); t = tt(n); L = np.zeros(n); Rr = np.zeros(n)
    for f in freqs:
        for k, dd in enumerate((-det, 0, det)):
            v = saw(f * (1 + dd), t, rng.random() * 6.28)
            if k == 0: L += v
            elif k == 2: Rr += v
            else: L += v * 0.7; Rr += v * 0.7
    env = np.clip(np.minimum(t / attack, (d - t) / release), 0, 1)
    return filt(L, 'lowpass', cutoff) * env, filt(Rr, 'lowpass', cutoff) * env


def stab(freqs, d=0.32):
    n = int(d * SR); t = tt(n); s = np.zeros(n)
    for f in freqs:
        for dd in (-0.006, 0, 0.006):
            s += saw(f * (1 + dd), t, rng.random() * 6.28)
    e1 = np.exp(-t / 0.05)
    s = filt(s, 'lowpass', 4200) * e1 + filt(s, 'lowpass', 900) * (1 - e1)
    return s * np.exp(-t / 0.11) * np.clip(t / 0.003, 0, 1)


def bass(f, d=0.24):
    n = int(d * SR); t = tt(n)
    s = np.sin(2 * np.pi * f * t) + 0.35 * filt(saw(f, t, 0), 'lowpass', 700)
    return np.tanh(1.4 * s) * np.exp(-t / 0.16) * np.clip(t / 0.004, 0, 1) * np.clip((d - t) / 0.01, 0, 1)


# ---------------- foley ----------------
def slap(strength=1.0):
    d = 0.3; t = tt(int(d * SR))
    body = filt(noise(d), 'bandpass', [260, 2600]) * np.exp(-t / 0.032)
    crack = filt(noise(d), 'highpass', 2600) * np.exp(-t / 0.01) * 0.55
    thud = sweep(80 + 70 * np.exp(-t / 0.018)) * np.exp(-t / 0.07) * 0.9
    return (body + crack + thud) * strength


def tape_rip(d=0.17):
    t = tt(int(d * SR))
    buzz = (signal.square(2 * np.pi * np.cumsum(70 + 90 * t / d) / SR) * 0.5 + 0.5)
    env = np.clip(t / 0.012, 0, 1) * np.clip((d - t) / 0.04, 0, 1)
    return filt(noise(d) * (0.35 + buzz), 'bandpass', [900, 7000]) * env


def marker(d=0.42):
    t = tt(int(d * SR))
    speed = np.abs(np.sin(np.pi * t / d * 2.2)) ** 0.7
    rub = filt(noise(d), 'bandpass', [1800, 5200]) * 0.6
    squeak = np.sin(2 * np.pi * np.cumsum(2900 + 250 * np.sin(2 * np.pi * 9 * t)) / SR) * 0.12
    return (rub + squeak) * speed * np.clip((d - t) / 0.05, 0, 1)


def stamp_snd():
    d = 0.35; t = tt(int(d * SR))
    return (sweep(65 + 50 * np.exp(-t / 0.02)) * np.exp(-t / 0.09) * 1.1
            + filt(noise(d), 'bandpass', [500, 2400]) * np.exp(-t / 0.02) * 0.8
            + filt(noise(d), 'highpass', 4000) * np.exp(-t / 0.004) * 0.4)


def snip():
    d = 0.08; t = tt(int(d * SR))
    ring = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((3150, 0.5), (4730, 0.35), (6900, 0.25))) * np.exp(-t / 0.014)
    return ring + filt(noise(d), 'highpass', 3500) * np.exp(-t / 0.004) * 0.8


def whoosh(d=0.45, up=False):
    n = int(d * SR); t = tt(n); x = noise(d); y = np.zeros(n); z = 0.0
    fc = (300 + 5500 * (t / d) ** 1.5) if up else (2600 * np.sin(np.pi * t / d) + 250)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    for i in range(n):
        z += a[i] * (x[i] - z); y[i] = z
    env = (t / d) ** 2 if up else np.sin(np.pi * t / d) ** 2
    return filt(y, 'highpass', 120) * env


def crack(big=False):
    d = 0.6 if big else 0.35; n = int(d * SR); t = tt(n); imp = np.zeros(n)
    k = (rng.random(n) < (0.012 if big else 0.008)) * rng.standard_normal(n)
    imp += k * np.exp(-t / (0.18 if big else 0.09))
    s = filt(imp, 'bandpass', [900, 9000]) * 3
    s += filt(noise(d), 'highpass', 3000) * np.exp(-t / 0.012) * 0.8
    for f in rng.uniform(2400, 6500, 5):
        s += np.sin(2 * np.pi * f * t) * np.exp(-t / 0.03) * 0.12
    if big:
        s += sweep(70 + 60 * np.exp(-t / 0.03)) * np.exp(-t / 0.15) * 1.0
    return s


def debris(d=0.6):
    n = int(d * SR); t = tt(n); k = (rng.random(n) < 0.004) * rng.uniform(-1, 1, n)
    return filt(k, 'bandpass', [1200, 8000]) * 3 * np.exp(-t / 0.25)


def typekey():
    d = 0.12; t = tt(int(d * SR))
    return filt(noise(d), 'bandpass', [1500, 6000]) * np.exp(-t / 0.006) + sweep(160 + 0 * t) * np.exp(-t / 0.02) * 0.4


def tick():
    d = 0.05; t = tt(int(d * SR))
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.006) + filt(noise(d), 'highpass', 5000) * np.exp(-t / 0.002) * 0.5


def plop():
    d = 0.18; t = tt(int(d * SR))
    return sweep(520 * np.exp(-t / 0.05) + 140) * np.exp(-t / 0.05)


def riser(d=0.95):
    n = int(d * SR); t = tt(n); p = t / d
    tone = sum(np.sin(2 * np.pi * np.cumsum(f0 * 2 ** (2.2 * p) * (1 + 0.004 * np.sin(2 * np.pi * 6 * t))) / SR) for f0 in (220, 330.5))
    nz = whoosh(d, up=True)
    return (tone * 0.18 * p ** 1.5 + nz * 0.9) * np.clip((d - t) / 0.01, 0, 1)


def crash(d=2.0):
    t = tt(int(d * SR))
    s = filt(noise(d), 'highpass', 4500) * np.exp(-t / 0.75)
    for f in (3120, 4410, 5230, 6810):
        s += np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t / 0.5) * 0.04
    return s


def sub_boom(d=1.6):
    t = tt(int(d * SR))
    return np.tanh(1.5 * sweep(30 + 45 * np.exp(-t / 0.08)) * np.exp(-t / 0.55))


# ================= ARRANGEMENT =================
A1, C2, F1, G1 = 55.0, 65.41, 43.65, 49.0
note = lambda n: 440 * 2 ** ((n - 69) / 12)
CH = {
    'Am': [note(57), note(60), note(64)], 'F': [note(53), note(57), note(60)],
    'C': [note(55), note(60), note(64)], 'G': [note(55), note(59), note(62)],
}
BARS = [(1, 'Am', A1), (3, 'F', F1), (5, 'C', C2), (7, 'G', G1), (9, 'Am', A1)]

kicks = [k * 0.5 for k in range(22)]
for tk in kicks:
    add(drums, kick(), tk, 0.95)
for b, _, _ in BARS:
    for off in (0.5, 1.5):
        add(drums, clap(), b + off, 0.42, 0.05, rev=0.35)
for k in range(40):
    th = 1.0 + k * 0.25
    if th >= 11: break
    if (k % 2) == 1:
        add(drums, hat(open_=th >= 9), th, 0.16 if th < 9 else 0.2, 0.25)
    elif th >= 5:
        add(drums, hat(), th, 0.07, -0.25)
for th in np.arange(9.0, 11.0, 0.125):
    if abs((th * 4) % 2 - 1) > 0.01:
        add(drums, hat(), th + 0.012 * ((th * 8) % 2), 0.06, -0.3)
for i, th in enumerate((8.5, 8.625, 8.75, 8.875)):
    add(drums, snare(), th, 0.25 + 0.12 * i, 0.1, rev=0.2)

# bass: sparse in bar A, octave-bouncing 8ths from the cut onward
for tb in (1.25, 1.75, 2.25, 2.75):
    add(music, bass(A1 * 2), tb, 0.35)
for b, _, root in BARS[1:]:
    for i in range(8):
        add(music, bass(root * (2 if i % 2 else 1)), b + i * 0.25, 0.5 if i % 2 == 0 else 0.4)
# chord stabs
for b, ch, _ in BARS[1:]:
    for off in (0.25, 0.75, 1.25, 1.625):
        add(music, stab(CH[ch]), b + off, 0.15, 0.0, rev=0.4)
# pads
l, r = pad(CH['Am'] + [note(45)], 3.2, cutoff=900, attack=0.8)
add(music, l, 0, 0.1, -0.6); add(music, r, 0, 0.1, 0.6)
l, r = pad(CH['F'] + [note(41), note(64)], 2.0, cutoff=750, attack=0.25, release=0.1)
add(music, l, 11.0, 0.13, -0.6); add(music, r, 11.0, 0.13, 0.6)
fin = [note(48), note(55), note(60), note(64), note(67), note(72), note(76)]
l, r = pad(fin, 2.0, cutoff=2600, attack=0.01, release=1.4)
add(music, l, 13.0, 0.12, -0.7, rev=0.3); add(music, r, 13.0, 0.12, 0.7, rev=0.3)
add(music, stab(fin, d=0.6), 13.0, 0.25, 0.0, rev=0.5)
add(music, bass(C2, d=1.2), 13.0, 0.5)

# drop 11–13: clock ticks, snare roll, riser, one beat of silence before the hit
for th in np.arange(11.0, 13.0, 0.5):
    add(sfx, tick(), th, 0.22, 0.2)
for i, th in enumerate([12.0, 12.25, 12.5, 12.625, 12.75, 12.8125, 12.875, 12.9063]):
    add(drums, snare(), th, 0.12 + 0.05 * i, 0.0, rev=0.25)
add(sfx, riser(0.94), 12.0, 0.55, 0.0)

# impact at 13.0
add(drums, kick(0.9, low=42, tau=0.5), 13.0, 1.1)
add(drums, sub_boom(), 13.0, 0.8)
add(sfx, crash(), 13.0, 0.55, 0.15, rev=0.3)
add(sfx, crash(), 13.004, 0.4, -0.3)
for k in range(10):
    add(sfx, slap(0.25), 13.02 + k * 0.035 + rng.random() * 0.02, 0.35, rng.uniform(-0.7, 0.7))
add(sfx, plop(), 13.46, 0.45, -0.4)

# foley synced to picture
for t0, s in ((0.0, 1.0), (0.5, 0.9), (1.0, 0.95), (1.5, 1.0), (7.0, 1.1), (5.0, 1.15), (12.0, 0.85)):
    add(sfx, slap(s), t0 + 0.06, 0.6, 0.0, rev=0.25)
for t0, s, p in ((4.5, 0.45, 0.2), (6.2, 0.35, 0.4), (6.25, 0.4, -0.3), (6.5, 0.6, 0.35), (11.0, 0.45, 0), (11.5, 0.5, 0), (13.5, 0.5, 0)):
    add(sfx, slap(s), t0 + 0.04, 0.55, p, rev=0.2)
for t0 in (4.5, 6.25, 11.25, 13.5):
    for k in range(3):
        add(sfx, typekey(), t0 + 0.02 + k * 0.045, 0.35, -0.2 + 0.2 * k)
for t0, p in ((2.0, -0.4), (2.03, 0.4), (5.5, 0.35), (5.75, -0.35), (6.58, 0.3), (13.58, 0.4)):
    add(sfx, tape_rip(), t0, 0.5, p)
add(sfx, marker(), 2.0, 0.35, -0.1)
for t0, p in ((2.5, 0.35), (14.0, 0.35)):
    add(sfx, stamp_snd(), t0 + 0.03, 0.8, p, rev=0.25)
add(sfx, whoosh(0.25, up=True), 3.0, 0.35, 0.5)
for k in range(0, 6):
    add(sfx, snip(), 3.25 + k / 6, 0.45, 0.6 - k * 0.25)
add(sfx, whoosh(0.55), 4.0, 0.6, 0.0)
add(sfx, whoosh(0.22), 4.8, 0.55, 0.0)
add(sfx, whoosh(0.3), 5.95, 0.45, 0.3)
add(sfx, crack(), 7.5, 0.7, 0.0, rev=0.3)
add(sfx, crack(big=True), 8.0, 0.8, 0.0, rev=0.3)
add(sfx, whoosh(0.5), 8.5, 0.6, 0.0)
add(sfx, debris(), 8.52, 0.6, 0.0)
add(sfx, whoosh(0.6, up=True), 10.4, 0.5, 0.0)

# vinyl bed
crk = np.zeros(N)
pos = rng.random(N) < 28 / SR
crk[pos] = rng.uniform(-1, 1, pos.sum())
crk = filt(crk, 'highpass', 1200) * 0.5 + filt(rng.standard_normal(N), 'bandpass', [400, 6000]) * 0.004
sfx[0] += crk * 0.6; sfx[1] += np.roll(crk, 37) * 0.6

# ================= MIX =================
# sidechain pump on the music bus from the kick grid
duck = np.ones(N); tA = tt(N)
for tk in kicks + [13.0]:
    i = int(tk * SR); seg = tA[: N - i]
    duck[i:] = np.minimum(duck[i:], 1 - 0.55 * np.exp(-seg / 0.11))
music *= duck

# small plate reverb on the send
ir_t = tt(int(0.9 * SR))
ir = rng.standard_normal((2, len(ir_t))) * np.exp(-ir_t / 0.25)
ir[:, : int(0.012 * SR)] = 0
wet = np.stack([signal.fftconvolve(filt(send[c], 'highpass', 300), ir[c])[:N] for c in range(2)]) * 0.03

mix = drums * 0.55 + music * 1.05 + sfx * 1.15 + wet
mix = np.stack([filt(ch, 'highpass', 28) for ch in mix])
# silence gap right before the hit (tension)
g = np.ones(N); a, b = int(12.94 * SR), int(13.0 * SR); g[a:b] = np.linspace(1, 0.0, b - a) ** 0.5; mix *= g
fade = np.ones(N); fs = int(14.55 * SR); fade[fs:] = np.linspace(1, 0, N - fs) ** 1.5; mix *= fade
fi = int(0.004 * SR); mix[:, :fi] *= np.linspace(0, 1, fi)

print('pre-clip peak', np.max(np.abs(mix)))
mix /= np.max(np.abs(mix))
mix = np.tanh(mix * 1.8) / np.tanh(1.8)
mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))
pcm = (mix.T * 32767).astype(np.int16)
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
for a_, b_ in ((0, 3), (3, 5), (5, 7), (7, 9), (9, 11), (11, 13), (13, 15)):
    print(f'{a_:>2}-{b_:<2}s  RMS {rms(mix[:, int(a_ * SR):int(b_ * SR)]):6.1f} dBFS')
print('peak', 20 * np.log10(np.max(np.abs(mix))), 'dBFS')
