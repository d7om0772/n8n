"""Procedural foley for the scrapbook collage: paper, tape, rubber stamps, marker.
Reads out/events.json (cue list exported by the scene) and writes out/sfx.wav (48 kHz)."""
import json
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 21.5
rng = np.random.default_rng(2024)


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='high', fs=SR, output='sos'), x)


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def crinkle(dur, rate=180, lo=900, hi=9000, decay=0.004):
    """Paper crinkle: sparse random clicks with tiny noisy resonances."""
    n = int(dur * SR)
    out = np.zeros(n + 2000)
    count = rng.poisson(rate * dur)
    for _ in range(count):
        i = rng.integers(0, n)
        L = int(rng.uniform(0.6, 4.0) * 1e-3 * SR)
        burst = rng.normal(0, 1, L) * env_exp(L, rng.uniform(0.3, 1.0) * decay)
        out[i:i + L] += burst * rng.uniform(0.2, 1.0) ** 2
    return bp(out[:n], lo, hi)


def swept_noise(dur, f0, f1, width=0.9, curve=None):
    """Noise through a time-varying band (STFT shaping) -> whooshes."""
    n = int(dur * SR)
    x = rng.normal(0, 1, n + 4096)
    f, t, Z = signal.stft(x, SR, nperseg=1024)
    tt = np.clip(t / dur, 0, 1)
    if curve is None:
        fc = f0 * (f1 / f0) ** tt
    else:
        fc = curve(tt)
    lf = np.log2(np.maximum(f, 20))[:, None]
    mask = np.exp(-0.5 * ((lf - np.log2(fc)[None, :]) / width) ** 2)
    _, y = signal.istft(Z * mask, SR, nperseg=1024)
    return y[:n]


def adsr(n, a, d_start, total_decay=None):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na) ** 2
    if total_decay:
        nd = int(total_decay * SR)
        start = max(na, n - nd)
        e[start:] *= np.linspace(1, 0, n - start) ** 1.5
    return e


# ------------------------------------------------------------------ sounds
def s_drop(big=False):
    d = 0.36 if not big else 0.4
    w = swept_noise(d, 500, 2600 if not big else 2000, 0.8)
    n = len(w)
    e = np.linspace(0, 1, n) ** 2.2  # rises as the clipping falls toward the page
    w = w * e
    cr = crinkle(d, 70, 1500, 8000) * np.linspace(0.2, 1, n)
    return norm(w, 1) * (0.28 if not big else 0.36) + norm(cr, 1) * 0.10


def s_land(big=False):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    thump_f = (130 if not big else 95) * np.exp(-t * 12) + 55
    thump = np.sin(2 * np.pi * np.cumsum(thump_f) / SR) * env_exp(n, 0.05 if not big else 0.075)
    slap = lp(rng.normal(0, 1, n), 3500) * env_exp(n, 0.012)
    flap = bp(rng.normal(0, 1, n), 600, 2400) * env_exp(n, 0.03)
    tail = np.zeros(n)
    cr = crinkle(0.3, 240, 1200, 9000)
    tail[int(0.01 * SR):int(0.01 * SR) + len(cr)] = cr * np.linspace(1, 0, len(cr)) ** 1.5
    out = norm(thump) * (0.55 if not big else 0.8) + norm(slap) * 0.55 + norm(flap) * 0.3 + norm(tail) * 0.28
    return out * (0.62 if not big else 0.8)


def s_tape():
    """Masking tape pulled off the roll: stick-slip buzz with a rising rate, then a soft pat."""
    d = 0.26
    n = int(d * SR)
    out = np.zeros(n)
    tpos = 0.0
    while True:
        u = tpos / d
        rate = 260 + 520 * u + rng.normal(0, 40)
        tpos += 1.0 / max(rate, 80)
        i = int(tpos * SR)
        if i >= n - 200:
            break
        L = int(rng.uniform(0.25, 0.9) * 1e-3 * SR)
        out[i:i + L] += rng.normal(0, 1, L) * env_exp(L, 0.0003) * rng.uniform(0.4, 1.0)
    out = bp(out, 700, 7000)
    e = adsr(n, 0.015, 0, 0.07)
    body = bp(rng.normal(0, 1, n), 1500, 5000) * 0.25
    rip = (out + body) * e
    pat = lp(rng.normal(0, 1, int(0.08 * SR)), 2500) * env_exp(int(0.08 * SR), 0.01)
    res = np.concatenate([norm(rip) * 0.42, np.zeros(int(0.03 * SR)), norm(pat) * 0.22])
    return res


def s_stamp(big=False):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = (95 if big else 120) * np.exp(-t * 18) + 48
    thud = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.07 if big else 0.05)
    knock = bp(rng.normal(0, 1, n), 180, 900) * env_exp(n, 0.028)
    clack = hp(rng.normal(0, 1, n), 2500) * env_exp(n, 0.004)
    rub = bp(rng.normal(0, 1, n), 300, 1200) * env_exp(n, 0.06) * 0.3
    pre = np.zeros(n)  # tiny wooden handle rattle before the hit
    out = norm(thud) * 1.0 + norm(knock) * 0.7 + norm(clack) * 0.35 + norm(rub) * 0.2 + pre
    return norm(out) * (0.95 if big else 0.8)


def s_pop():
    """Sticker peeled and slapped on: short peel zip + tap."""
    n1 = int(0.07 * SR)
    peel = bp(rng.normal(0, 1, n1), 2500, 9000) * np.linspace(0.2, 1, n1) ** 2
    n2 = int(0.12 * SR)
    t = np.arange(n2) / SR
    tap = np.sin(2 * np.pi * (700 * np.exp(-t * 30) + 260) * t) * env_exp(n2, 0.02)
    slap = lp(rng.normal(0, 1, n2), 4000) * env_exp(n2, 0.006)
    return np.concatenate([norm(peel) * 0.16, norm(tap) * 0.32 + norm(slap) * 0.3])


def s_marker(dur):
    """Felt marker scribbling fast strokes."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    fr = bp(rng.normal(0, 1, n), 2200, 7500)
    strokes = np.abs(np.sin(np.pi * t * (2 / dur))) ** 0.6  # two strokes
    squeak = 0.5 + 0.5 * np.sin(2 * np.pi * 180 * t + np.cumsum(rng.normal(0, 0.05, n)))
    grit = 0.6 + 0.4 * np.abs(lp(rng.normal(0, 1, n), 300)) / 0.5
    out = fr * strokes * (0.7 + 0.3 * squeak) * np.clip(grit, 0, 1.5)
    return norm(out * adsr(n, 0.01, 0, 0.03)) * 0.34


def s_receipt(dur):
    n = int(dur * SR)
    slide = swept_noise(dur, 1200, 2600, 0.7) * adsr(n, 0.05, 0, 0.12)
    ratchet = np.zeros(n)
    step = int(SR / 38)
    for i in range(0, n - 300, step):
        L = 200
        ratchet[i:i + L] += rng.normal(0, 1, L) * env_exp(L, 0.0006)
    ratchet = bp(ratchet, 1500, 6000) * adsr(n, 0.05, 0, 0.1)
    return norm(slide) * 0.18 + norm(ratchet) * 0.1 + norm(crinkle(dur, 60)) * 0.06


def s_swoosh(dur):
    d = min(max(dur, 0.35), 1.8)
    n = int(d * SR)
    curve = lambda u: 350 * (6 ** np.sin(np.pi * u))  # up then down
    w = swept_noise(d, 0, 0, 1.0, curve)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6
    lvl = 0.15 if dur < 1 else 0.24
    return norm(w * e) * lvl + norm(crinkle(d, 40, 2000, 8000) * e) * 0.04


def s_peel():
    return s_swoosh(0.35) * 1.2 + np.pad(s_tape()[:int(0.2 * SR)] * 0.5, (0, max(0, int(0.35 * SR) - int(0.2 * SR))))[:int(0.35 * SR)]


def s_drop_soft():
    return s_drop() * 0.5 + np.pad(s_land() * 0.35, (int(0.28 * SR), 0))[:int(0.36 * SR)] if False else np.concatenate([s_drop() * 0.45, s_land() * 0.35])


def s_word(big):
    n = int(0.05 * SR)
    tick = lp(rng.normal(0, 1, n), 5000) * env_exp(n, 0.005)
    return norm(tick) * (0.07 if big else 0.045)


# ------------------------------------------------------------------ mix
events = json.load(open('out/events.json'))
N = int(DUR * SR) + SR
track = np.zeros(N)


def put(t, x):
    i = int(t * SR)
    j = min(N, i + len(x))
    if i < N:
        track[i:j] += x[:j - i]


for e in events:
    t, ty = e['t'], e['type']
    if ty == 'drop': put(t, s_drop())
    elif ty == 'dropBig': put(t, s_drop(True))
    elif ty == 'land': put(t - 0.005, s_land())
    elif ty == 'landBig': put(t - 0.005, s_land(True))
    elif ty == 'tape': put(t, s_tape())
    elif ty == 'stamp': put(t - 0.01, s_stamp())
    elif ty == 'stampBig': put(t - 0.01, s_stamp(True))
    elif ty == 'pop': put(t - 0.06, s_pop())
    elif ty == 'marker': put(t, s_marker(e['dur']))
    elif ty == 'receipt': put(t, s_receipt(e['dur']))
    elif ty == 'swoosh': put(t, s_swoosh(e['dur']))
    elif ty == 'peel': put(t, s_peel())
    elif ty == 'dropSoft': put(t, s_drop_soft())
    elif ty == 'word': put(t, s_word(e.get('big', False)))

# gentle room: tiny early reflections so the foley sits in one space
ir = np.zeros(int(0.06 * SR)); ir[0] = 1
for d, g in [(0.011, 0.18), (0.019, 0.12), (0.031, 0.08), (0.047, 0.05)]:
    ir[int(d * SR)] = g
track = signal.fftconvolve(track, ir)[:N]
track = hp(track, 40)
track = np.tanh(track * 1.2) / 1.2  # soft clip
track = track[:int(DUR * SR)]
track = norm(track, 0.89)
wavfile.write('out/sfx.wav', SR, (track * 32767).astype(np.int16))
print('sfx written', len(events), 'cues')
