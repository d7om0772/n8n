"""Procedural sound effects (no music) — fallbacks for SFX that could not be downloaded.
All functions return float32 stereo arrays (n, 2) at SR."""
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def _t(d):
    return np.arange(int(d * SR)) / SR


def stereo(x, pan=0.0):
    pan = np.clip(pan, -1, 1)
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * l, x * r], 1).astype(np.float32)


def band_sweep_noise(d, f0, f1, bw=0.5, curve=1.0):
    """White noise through a gaussian band whose centre sweeps f0->f1 (log), STFT overlap-add."""
    n = int(d * SR)
    N, H = 2048, 512
    noise = rng.standard_normal(n + N)
    out = np.zeros(n + N)
    win = np.hanning(N)
    freqs = np.fft.rfftfreq(N, 1 / SR)
    lf = np.log(np.maximum(freqs, 1))
    for s in range(0, n, H):
        p = (s / max(1, n)) ** curve
        fc = np.exp(np.log(f0) + (np.log(f1) - np.log(f0)) * p)
        mask = np.exp(-0.5 * ((lf - np.log(fc)) / bw) ** 2)
        seg = np.fft.rfft(noise[s:s + N] * win)
        out[s:s + N] += np.fft.irfft(seg * mask, N) * win
    out = out[:n]
    return out / (np.max(np.abs(out)) + 1e-9)


def env_ar(n, a, r, shape=2.0):
    """attack fraction a, release to end; returns envelope length n"""
    x = np.linspace(0, 1, n)
    e = np.where(x < a, (x / a) ** 1.5, ((1 - x) / (1 - a)) ** shape)
    return e


def whoosh(d=0.45, f0=300, f1=4000, pan_from=0.8, pan_to=-0.8, a=0.6):
    x = band_sweep_noise(d, f0, f1, bw=0.45)
    n = len(x)
    x = x * env_ar(n, a, 1 - a, 2.2)
    pans = np.linspace(pan_from, pan_to, n)
    l = np.cos((pans + 1) * np.pi / 4)
    r = np.sin((pans + 1) * np.pi / 4)
    return np.stack([x * l, x * r], 1).astype(np.float32) * 0.9


def riser(d=0.8, f0=200, f1=6000):
    x = band_sweep_noise(d, f0, f1, bw=0.35, curve=1.6)
    n = len(x)
    e = np.linspace(0, 1, n) ** 2.2
    e[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    return stereo(x * e * 0.8)


def click(d=0.025, f=3200, pan=0.0, gain=1.0):
    t = _t(d)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 260)
    nz = rng.standard_normal(len(t)) * np.exp(-t * 900)
    nz = np.diff(nz, prepend=0)
    return stereo((0.6 * s + 0.5 * nz) * gain, pan)


def tick(pan=0.0, gain=1.0, f=5200):
    return click(0.018, f, pan, gain * 0.8)


def pop(f0=950, f1=420, d=0.09, pan=0.0, gain=1.0):
    t = _t(d)
    f = f1 + (f0 - f1) * np.exp(-t * 45)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 38) * (1 - np.exp(-t * 2000))
    return stereo(s * gain, pan)


def impact(d=0.9, f0=130, f1=42, gain=1.0):
    t = _t(d)
    f = f1 + (f0 - f1) * np.exp(-t * 14)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 5.5)
    nz = band_sweep_noise(d, 2500, 400, bw=0.8) * np.exp(-t * 30)
    x = body * 0.95 + nz * 0.35
    x = np.tanh(x * 1.6) / np.tanh(1.6)
    return stereo(x * gain)


def thud(gain=1.0):
    t = _t(0.35)
    f = 60 + 90 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 14)
    nz = band_sweep_noise(0.35, 1800, 600, bw=0.7) * np.exp(-t * 60)
    return stereo((body + 0.45 * nz) * gain)


def typing(d=1.0, rate=(0.055, 0.11), gain=1.0, seed=3):
    r = np.random.default_rng(seed)
    n = int(d * SR)
    out = np.zeros((n, 2), np.float32)
    pos = 0.0
    while True:
        i = int(pos * SR)
        if i >= n - 2000:
            break
        k = click(0.03, r.uniform(1800, 3200), r.uniform(-0.25, 0.25), r.uniform(0.55, 1.0))
        th = pop(260, 140, 0.03, 0, 0.25)
        m = min(len(k), n - i)
        out[i:i + m] += k[:m]
        out[i:i + len(th)] += th[: max(0, min(len(th), n - i))]
        pos += r.uniform(*rate)
    return out * gain


def ticker(times, gain=0.5, f=4600):
    """sequence of ticks at given relative times (seconds)"""
    d = max(times) + 0.05
    out = np.zeros((int(d * SR), 2), np.float32)
    for k, tt in enumerate(times):
        i = int(tt * SR)
        c = tick((k % 2) * 0.3 - 0.15, gain, f)
        out[i:i + len(c)] += c[: len(out) - i]
    return out


def coin(gain=1.0):
    """metallic 'ka-ching'-like hit: inharmonic partials, two strikes (not musical)"""
    def strike(d, base):
        t = _t(d)
        parts = [(1.0, 1.0), (2.76, 0.6), (5.40, 0.4), (8.93, 0.25), (13.3, 0.15)]
        s = sum(a * np.sin(2 * np.pi * base * m * t + m) * np.exp(-t * (9 + m * 2.2)) for m, a in parts)
        nz = rng.standard_normal(len(t)) * np.exp(-t * 300) * 0.4
        return s + nz
    a = strike(0.7, 1180)
    b = strike(0.9, 1520)
    out = np.zeros(int(1.1 * SR))
    out[: len(a)] += a * 0.6
    o = int(0.075 * SR)
    out[o:o + len(b)] += b * 0.75
    out = out / np.max(np.abs(out))
    return stereo(out * gain)


def buzzer(d=0.42, gain=1.0):
    t = _t(d)
    sq = np.sign(np.sin(2 * np.pi * 138 * t)) * 0.5 + np.sign(np.sin(2 * np.pi * 146 * t)) * 0.5
    e = np.minimum(1, t * 200) * np.minimum(1, (d - t) * 30)
    x = sq * e
    # soften harsh highs with a crude moving average
    k = 6
    x = np.convolve(x, np.ones(k) / k, mode="same")
    return stereo(x * 0.55 * gain)


def glitch(d=0.22, gain=1.0, seed=5):
    r = np.random.default_rng(seed)
    n = int(d * SR)
    x = np.zeros(n)
    i = 0
    while i < n:
        L = int(r.uniform(0.004, 0.025) * SR)
        kind = r.integers(0, 3)
        tt = np.arange(L) / SR
        if kind == 0:
            seg = np.sign(np.sin(2 * np.pi * r.uniform(200, 2400) * tt))
        elif kind == 1:
            seg = np.repeat(r.uniform(-1, 1, L // 40 + 1), 40)[:L]
        else:
            seg = r.standard_normal(L) * 0.6
        x[i:i + L] = seg[: min(L, n - i)] * r.uniform(0.3, 1)
        i += L
    x *= np.minimum(1, (n - np.arange(n)) / (0.02 * SR))
    return stereo(x * 0.5 * gain, 0)


def blip(f=1320, d=0.07, gain=1.0, pan=0.0):
    t = _t(d)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 55) * np.minimum(1, t * 3000)
    return stereo(s * gain, pan)


def notif(gain=1.0):
    a = blip(1180, 0.09, 1.0)
    b = blip(1580, 0.14, 1.0)
    out = np.zeros((int(0.25 * SR), 2), np.float32)
    out[: len(a)] += a
    o = int(0.075 * SR)
    out[o:o + len(b)] += b
    return out * gain * 0.7


def shutter(gain=1.0):
    a = click(0.03, 2400, 0, 1.0)
    b = click(0.04, 1700, 0, 0.8)
    out = np.zeros((int(0.12 * SR), 2), np.float32)
    out[: len(a)] += a
    o = int(0.055 * SR)
    out[o:o + len(b)] += b
    return out * gain


def stamp(gain=1.0):
    th = thud(1.0)
    paper = stereo(band_sweep_noise(0.12, 3000, 900, bw=0.6) * np.exp(-_t(0.12) * 35) * 0.5)
    th[: len(paper)] += paper
    return th * gain
