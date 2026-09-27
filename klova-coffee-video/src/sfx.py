# -*- coding: utf-8 -*-
"""Synthesised stop-motion foley (no music): pops, paper taps, bean rattles, stamps, whooshes..."""
import json, math, os, wave
import numpy as np
from scipy import signal

ROOT = os.path.dirname(os.path.abspath(__file__))
SR = 48000
DUR = 20.8
rng = np.random.default_rng(42)


def n_(d):
    return int(d * SR)


def t_(d):
    return np.arange(n_(d)) / SR


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def lp(x, hi, order=2):
    return signal.sosfilt(signal.butter(order, hi, btype='low', fs=SR, output='sos'), x)


def hp(x, lo, order=2):
    return signal.sosfilt(signal.butter(order, lo, btype='high', fs=SR, output='sos'), x)


def expenv(d, tau, attack=0.001):
    t = t_(d)
    e = np.exp(-t / tau)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return e * a


def sweep(f0, f1, d):
    t = t_(d)
    f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def noise(d):
    return rng.standard_normal(n_(d))


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def mix_at(buf, x, t0):
    i = int(t0 * SR)
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i]


# ------------------------------------------------------------------ sound designs
def s_pop(p):
    d = 0.12
    body = sweep(1150 * p, 360 * p, d) * expenv(d, 0.028, 0.0015)
    click = bp(noise(d), 2500, 9000) * expenv(d, 0.0025)
    return norm(body + 0.35 * norm(click), 0.9)


def s_tick(p):
    d = 0.07
    a = bp(noise(d), 1400 * p, 6500) * expenv(d, 0.006)
    b = np.sin(2 * np.pi * 190 * p * t_(d)) * expenv(d, 0.014)
    return norm(norm(a) + 0.5 * b, 0.8)


def s_rattle(p):
    d = 0.1
    out = np.zeros(n_(d))
    for _ in range(rng.integers(3, 6)):
        f = rng.uniform(2600, 4800) * p
        c = (0.6 * bp(noise(0.02), 2200, 9000) + np.sin(2 * np.pi * f * t_(0.02))) * expenv(0.02, 0.0028)
        mix_at(out, c * rng.uniform(0.5, 1.0), rng.uniform(0, 0.075))
    return norm(out, 0.7)


def s_ding(p):
    d = 1.6
    t = t_(d)
    f = 1318.5 * p
    x = np.zeros(n_(d))
    for (m, a, tau) in ((1, 1.0, 0.9), (2.0, 0.35, 0.5), (2.76, 0.3, 0.35), (5.4, 0.12, 0.18)):
        x += a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / tau)
    x *= np.clip(t / 0.002, 0, 1)
    return norm(x, 0.8)


def s_boing(p):
    d = 0.42
    t = t_(d)
    f = (190 + 260 * (1 - np.exp(-t / 0.05))) * p * (1 + 0.22 * np.sin(2 * np.pi * 17 * t) * np.exp(-t / 0.2))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * expenv(d, 0.13, 0.004)
    return norm(x, 0.8)


def s_sparkle(p):
    d = 0.45
    out = np.zeros(n_(d))
    for k, f in enumerate((1760, 2217, 2637, 3136, 3520)):
        pip = (np.sin(2 * np.pi * f * p * t_(0.12)) + 0.3 * np.sin(4 * np.pi * f * p * t_(0.12))) * expenv(0.12, 0.035)
        mix_at(out, pip * (0.7 + 0.06 * k), k * 0.045)
    return norm(out, 0.7)


def s_whoosh(p):
    d = 0.38
    x = noise(d)
    t = t_(d)
    fc = 500 + 2600 * np.sin(np.pi * t / d) ** 2 * p
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    y = hp(y, 250)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6
    return norm(y * env, 0.7)


def s_thud(p):
    d = 0.35
    body = sweep(95 * p, 48 * p, d) * expenv(d, 0.11, 0.002)
    slap = lp(noise(d), 1800) * expenv(d, 0.02)
    click = bp(noise(d), 2000, 8000) * expenv(d, 0.002)
    return norm(body + 0.45 * norm(slap) + 0.2 * norm(click), 0.95)


def s_stamp(p):
    d = 0.4
    body = sweep(120 * p, 55 * p, d) * expenv(d, 0.09, 0.0015)
    paper = bp(noise(d), 700, 5500) * expenv(d, 0.03)
    return norm(body + 0.6 * norm(paper), 0.95)


def s_scribble(p):
    d = 0.1
    t = t_(d)
    x = bp(noise(d), 1700 * p, 4600 * p) * (0.55 + 0.45 * np.sin(2 * np.pi * 26 * t + rng.uniform(0, 6)))
    x *= np.clip(t / 0.01, 0, 1) * np.clip((d - t) / 0.01, 0, 1)
    return norm(x, 0.6)


def s_tap(p):
    d = 0.18
    body = np.sin(2 * np.pi * 150 * p * t_(d)) * expenv(d, 0.035, 0.001)
    paper = bp(noise(d), 500, 3200) * expenv(d, 0.012)
    return norm(body + 0.7 * norm(paper), 0.9)


def s_bubble(p):
    d = 0.16
    x = sweep(320 * p, 980 * p, 0.07)
    x = np.concatenate([x, np.zeros(n_(d) - len(x))]) * expenv(d, 0.05, 0.004)
    return norm(x, 0.8)


def s_flip(p):
    d = 0.12
    t = t_(d)
    env = np.exp(-((t - 0.012) / 0.008) ** 2) + 0.7 * np.exp(-((t - 0.055) / 0.012) ** 2)
    return norm(bp(noise(d), 900 * p, 6500) * env, 0.75)


def s_clink(p):
    d = 0.3
    t = t_(d)
    x = sum(a * np.sin(2 * np.pi * f * p * t) * np.exp(-t / tau)
            for (f, a, tau) in ((3150, 1, 0.1), (4720, 0.6, 0.07), (6180, 0.35, 0.05)))
    x = x * np.clip(t / 0.0008, 0, 1) + 0.25 * bp(noise(d), 4000, 10000) * expenv(d, 0.002)
    return norm(x, 0.6)


def s_chaching(p):
    d = 0.9
    out = np.zeros(n_(d))
    cha = bp(noise(0.08), 2500, 9000) * expenv(0.08, 0.02)
    mix_at(out, norm(cha, 0.6), 0)
    t = t_(0.8)
    ch = sum(a * np.sin(2 * np.pi * f * p * t) * np.exp(-t / tau)
             for (f, a, tau) in ((2093, 1, 0.45), (2637, 0.7, 0.35), (3951, 0.4, 0.25), (5274, 0.25, 0.15)))
    mix_at(out, norm(ch, 0.8), 0.07)
    mix_at(out, norm(ch, 0.45), 0.16)
    return norm(out, 0.85)


def s_hop(p):
    d = 0.08
    x = sweep(650 * p, 1400 * p, d) * expenv(d, 0.02, 0.002) + 0.3 * bp(noise(d), 2500, 7000) * expenv(d, 0.01)
    return norm(x, 0.6)


def s_plink(p):
    d = 0.1
    x = np.sin(2 * np.pi * 950 * p * t_(d)) * expenv(d, 0.018) + 0.8 * bp(noise(d), 1500, 4500) * expenv(d, 0.004)
    return norm(x, 0.7)


def s_sheet(p):
    d = 0.42
    t = t_(d)
    x = bp(noise(d), 350, 4200)
    env = np.clip(t / 0.1, 0, 1) * np.exp(-np.clip(t - 0.12, 0, None) / 0.1)
    crin = np.zeros(n_(d))
    for _ in range(14):
        mix_at(crin, bp(noise(0.01), 2000, 8000) * expenv(0.01, 0.0015) * rng.uniform(0.3, 1), rng.uniform(0, 0.3))
    return norm(norm(x * env) + 0.6 * crin, 0.75)


def s_shutter(p):
    d = 0.14
    out = np.zeros(n_(d))
    for (t0, g) in ((0.0, 1.0), (0.048, 0.8)):
        c = bp(noise(0.03), 1800, 10000) * expenv(0.03, 0.003) + 0.5 * np.sin(2 * np.pi * 260 * t_(0.03)) * expenv(0.03, 0.007)
        mix_at(out, c * g, t0)
    return norm(out, 0.7)


DESIGN = dict(pop=s_pop, tick=s_tick, rattle=s_rattle, ding=s_ding, boing=s_boing, sparkle=s_sparkle,
              whoosh=s_whoosh, thud=s_thud, stamp=s_stamp, scribble=s_scribble, tap=s_tap, bubble=s_bubble,
              flip=s_flip, clink=s_clink, chaching=s_chaching, hop=s_hop, plink=s_plink, sheet=s_sheet,
              shutter=s_shutter)
# per-type level (relative) — keeps the voice on top
LEVEL = dict(pop=0.42, tick=0.22, rattle=0.2, ding=0.3, boing=0.3, sparkle=0.22, whoosh=0.32, thud=0.55,
             stamp=0.55, scribble=0.22, tap=0.3, bubble=0.36, flip=0.3, clink=0.24, chaching=0.34, hop=0.2,
             plink=0.26, sheet=0.34, shutter=0.28)


def read_voice(path):
    w = wave.open(path)
    sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    if sr != SR:
        g = math.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g)
    return x


def main():
    ev = json.load(open(os.path.join(ROOT, 'events.json')))
    total = n_(DUR)
    L = np.zeros(total + SR)
    R = np.zeros(total + SR)
    for k, (t, name, gain, pitch) in enumerate(ev):
        x = DESIGN[name](pitch) * gain * LEVEL[name]
        pan = ((k * 0.37) % 1.0 - 0.5) * 0.5  # gentle stereo spread
        mix_at(L, x * math.sqrt(0.5 - pan), t)
        mix_at(R, x * math.sqrt(0.5 + pan), t)
    L, R = L[:total], R[:total]
    v = read_voice(os.path.join(ROOT, 'voice.wav'))
    v = v[:total]
    v = np.pad(v, (0, total - len(v)))
    v = norm(v, 0.8) * math.sqrt(0.5) * 1.414
    out = np.stack([v + L, v + R], 1)
    # soft clip safety
    out = np.tanh(out * 1.05) / np.tanh(1.05)
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    w = wave.open(os.path.join(ROOT, 'mix.wav'), 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
    w.close()
    sfx_only = np.stack([L, R], 1)
    print('events', len(ev), 'voice peak', np.abs(v).max(), 'sfx peak', np.abs(sfx_only).max(),
          'sfx rms', np.sqrt((sfx_only ** 2).mean()), 'voice rms', np.sqrt((v ** 2).mean()))


if __name__ == '__main__':
    main()
