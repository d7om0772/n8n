"""Synthesize every sound effect in code and mix it under the voiceover.

    python3 sfx.py assets/voice.wav sfx_events.json mix.wav

No background music: only the voice plus short effects. Each cut gets a
whoosh that peaks exactly on the cut plus a soft low thump; the effect bus is
ducked under the voice, then the mix is normalised to -14 LUFS in ffmpeg.
"""
import json
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt, resample_poly

SR = 48000
rng = np.random.default_rng(11)


def tt(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)


def norm(x, peak=1.0):
    m = np.abs(x).max() + 1e-9
    return x / m * peak


def noise(d):
    return rng.standard_normal(int(d * SR))


def expdec(d, tau, attack=0.003):
    t = tt(d)
    return np.minimum(t / attack, 1) * np.exp(-t / tau)


def sweep_sine(f0, f1, d, curve=1.0):
    t = tt(d)
    f = f0 + (f1 - f0) * (t / d) ** curve
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


# ------------------------------------------------------------------ sounds
def whoosh(pre=0.34, post=0.3):
    """Air sweep that peaks at index `pre` (the cut)."""
    d = pre + post
    n = int(d * SR)
    x = noise(d)
    t = tt(d)
    # time-varying band-pass via a bank of bands cross-faded along the sweep
    centers = [350, 600, 1000, 1700, 2800, 4200]
    pos = np.clip((t / pre), 0, 1) ** 1.3 * (len(centers) - 1)
    after = np.clip((t - pre) / post, 0, 1)
    pos = pos - after * 2.5
    out = np.zeros(n)
    for i, c in enumerate(centers):
        w = np.clip(1 - np.abs(pos - i), 0, 1)
        out += bp(x, c * 0.7, c * 1.4) * w
    env = np.where(t < pre, (t / pre) ** 2.4, np.exp(-(t - pre) / (post * 0.35)))
    out = norm(out * env)
    thump = sweep_sine(110, 45, 0.28) * expdec(0.28, 0.08, 0.004)
    body = np.zeros(n)
    k = int(pre * SR)
    body[k:k + len(thump)] = thump[: n - k]
    L = out * (1 - 0.55 * np.clip(t / d, 0, 1)) + body * 0.55
    R = out * (0.45 + 0.55 * np.clip(t / d, 0, 1)) + body * 0.55
    return np.stack([L, R], 1), pre


def pop(p=1.0):
    d = 0.14
    s = sweep_sine(900 * p, 380 * p, d, 0.5) * expdec(d, 0.045, 0.002)
    c = hp(noise(0.006), 2000) * 0.4
    s[: len(c)] += c
    return norm(s)


def pop_big(p=1.0):
    d = 0.22
    s = sweep_sine(260 * p, 720 * p, d, 0.6) * expdec(d, 0.07, 0.003)
    s += 0.35 * sweep_sine(520 * p, 1400 * p, d, 0.6) * expdec(d, 0.04, 0.002)
    c = hp(noise(0.008), 1500) * 0.5
    s[: len(c)] += c
    return norm(s)


def paper(p=1.0):
    d = 0.2
    x = bp(noise(d), 1200, 7000)
    crack = (rng.random(len(x)) < 0.012) * rng.standard_normal(len(x)) * 3
    env = expdec(d, 0.05, 0.006)
    return norm((x + crack) * env)


def slide():
    d = 0.3
    x = lp(bp(noise(d), 500, 5000), 3500)
    t = tt(d)
    env = np.sin(np.pi * t / d) ** 1.5
    return norm(x * env)


def scribble(d=0.4):
    x = bp(noise(d), 1800, 6500)
    t = tt(d)
    am = np.abs(np.sin(2 * np.pi * (15 + 5 * np.sin(2 * np.pi * 1.3 * t)) * t)) ** 1.5
    env = np.minimum(t / 0.02, 1) * np.minimum((d - t) / 0.04, 1)
    return norm(x * am * np.clip(env, 0, 1))


def stamp():
    d = 0.3
    s = sweep_sine(140, 48, d, 0.4) * expdec(d, 0.08, 0.002)
    n = lp(noise(0.06), 2400) * expdec(0.06, 0.015, 0.001)
    s[: len(n)] += n * 0.8
    return norm(s)


def thud():
    d = 0.3
    s = sweep_sine(90, 40, d, 0.5) * expdec(d, 0.09, 0.004)
    n = lp(noise(0.1), 900) * expdec(0.1, 0.03, 0.002)
    s[: len(n)] += n * 0.5
    return norm(s)


def tick(p=1.0):
    d = 0.03
    s = np.sin(2 * np.pi * 3200 * p * tt(d)) * expdec(d, 0.006, 0.0005)
    c = hp(noise(0.003), 3000)
    s[: len(c)] += c * 0.6
    return norm(s)


def gauge():
    out = np.zeros(int(0.45 * SR))
    for i in range(6):
        k = int(i * 0.03 * SR)
        tk = tick(0.8 + i * 0.06)
        out[k:k + len(tk)] += tk * 0.6
    t = tt(0.4)
    boing = np.sin(2 * np.pi * (230 + 30 * np.sin(2 * np.pi * 18 * t)) * t) * expdec(0.4, 0.12, 0.005)
    k = int(0.05 * SR)
    out[k:k + len(boing)] += boing * 0.7
    return norm(out)


def rev(d=0.4):
    t = tt(d)
    f = 70 + 330 * (t / d) ** 1.4
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    env = np.minimum(t / 0.05, 1) * np.minimum((d - t) / 0.04, 1)
    return norm(lp(saw, 1400) * np.clip(env, 0, 1))


def swish():
    x, _ = whoosh(0.18, 0.2)
    return x[:, 0] * 0.8 + x[:, 1] * 0.2


def plink(p=1.0):
    d = 0.45
    t = tt(d)
    f = 1400 * p * (1 + 0.03 * np.exp(-t / 0.02))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    return norm(s * expdec(d, 0.11, 0.002))


def sparkle():
    out = np.zeros(int(0.5 * SR))
    for i in range(7):
        f = rng.uniform(2600, 6200)
        s = np.sin(2 * np.pi * f * tt(0.25)) * expdec(0.25, 0.06, 0.002)
        k = int(i * 0.035 * SR)
        out[k:k + len(s)] += s * (1 - i * 0.08)
    return norm(out)


def kaching():
    out = np.zeros(int(1.0 * SR))
    clack = lp(noise(0.05), 3000) * expdec(0.05, 0.012, 0.001)
    out[: len(clack)] += clack * 0.7
    k = int(0.07 * SR)
    t = tt(0.9)
    bell = sum(a * np.sin(2 * np.pi * 1850 * r * t) * np.exp(-t / (0.35 / r ** 0.5)) for r, a in [(1, 1), (2.76, 0.5), (5.4, 0.25), (1.5, 0.3)])
    out[k:k + len(bell)] += bell * 0.8
    k2 = int(0.16 * SR)
    out[k2:k2 + len(bell)] += bell[: len(out) - k2] * 0.45
    return norm(out)


def flutter(d=0.7):
    out = np.zeros(int(d * SR) + int(0.05 * SR))
    tcur, i = 0.0, 0
    while tcur < d:
        rate = 10 + 26 * (tcur / d) ** 1.2
        s = np.sin(2 * np.pi * 4200 * tt(0.02)) * expdec(0.02, 0.004, 0.0005)
        k = int(tcur * SR)
        out[k:k + len(s)] += s * (0.5 + 0.5 * (tcur / d))
        tcur += 1 / rate
        i += 1
    return norm(out)


def sprinkle():
    """Beans scattering: a spray of tiny woody clicks."""
    out = np.zeros(int(0.6 * SR))
    for i in range(14):
        k = int((0.45 * (i / 14) ** 1.3 + rng.uniform(0, 0.03)) * SR)
        f = rng.uniform(900, 2200)
        s = np.sin(2 * np.pi * f * tt(0.03)) * expdec(0.03, 0.006, 0.0005) + bp(noise(0.03), 1500, 5000) * expdec(0.03, 0.004, 0.0005) * 0.5
        out[k:k + len(s)] += s * rng.uniform(0.5, 1)
    return norm(out)


def steam(d=1.3):
    t = tt(d)
    x = hp(noise(d), 3000)
    env = np.sin(np.pi * t / d) ** 2
    return norm(x * env)


def ding():
    d = 1.3
    t = tt(d)
    s = np.sin(2 * np.pi * 1318 * t) + 0.4 * np.sin(2 * np.pi * 2637 * t) + 0.15 * np.sin(2 * np.pi * 3951 * t)
    return norm(s * expdec(d, 0.35, 0.002))


def impact():
    d = 0.6
    s = sweep_sine(120, 38, d, 0.35) * expdec(d, 0.16, 0.002)
    n = lp(noise(0.12), 1800) * expdec(0.12, 0.03, 0.001)
    s[: len(n)] += n * 0.6
    return norm(s)


MONO = dict(pop=pop, pop_big=pop_big, paper=paper, slide=slide, scribble=scribble, stamp=stamp, thud=thud,
            tick=tick, gauge=gauge, rev=rev, swish=swish, plink=plink, sparkle=sparkle, kaching=kaching,
            flutter=flutter, sprinkle=sprinkle, steam=steam, ding=ding, impact=impact)
GAIN = dict(whoosh=0.4, pop=0.3, pop_big=0.36, paper=0.3, slide=0.28, scribble=0.2, stamp=0.45, thud=0.32, tick=0.18,
            gauge=0.28, sprinkle=0.3, rev=0.16, swish=0.3, plink=0.26, sparkle=0.2, kaching=0.32, flutter=0.16, steam=0.06,
            ding=0.28, impact=0.6)
PAN = dict(paper=-0.2, slide=0.2, plink=0.15, sparkle=0.25, kaching=-0.25, flutter=0.2)


def read_wav(path):
    w = wave.open(path)
    sr, ch = w.getframerate(), w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    x = x.reshape(-1, ch).mean(1)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g)
    return x


def main(voice_path, events_path, out_path):
    voice = read_wav(voice_path)
    n = len(voice)
    dur = n / SR
    bus = np.zeros((n + SR, 2))
    for ev in json.load(open(events_path)):
        k, t0 = ev['k'], ev['t']
        g = GAIN[k] * ev.get('g', 1.0)
        if k == 'whoosh':
            x, pre = whoosh()
            start = int((t0 - pre) * SR)
        else:
            fn = MONO[k]
            args = {}
            if 'p' in ev and k in ('pop', 'pop_big', 'tick', 'plink', 'paper'):
                args['p'] = ev['p']
            if 'd' in ev and k in ('scribble', 'rev', 'flutter', 'steam'):
                args['d'] = ev['d']
            m = fn(**args)
            pan = PAN.get(k, 0.0)
            x = np.stack([m * (1 - max(pan, 0)), m * (1 + min(pan, 0))], 1)
            start = int(t0 * SR)
        x = x * g
        a, b = max(start, 0), min(start + len(x), len(bus))
        if b > a:
            bus[a:b] += x[a - start:b - start]
    bus = bus[:n]
    # duck the effects under the voice (up to ~5 dB)
    env = np.sqrt(np.convolve(voice ** 2, np.ones(int(0.03 * SR)) / int(0.03 * SR), mode='same'))
    env = np.convolve(env, np.ones(int(0.08 * SR)) / int(0.08 * SR), mode='same')
    duck = 1 - 0.45 * np.clip(env / (env.max() * 0.35), 0, 1)
    bus *= duck[:, None]
    mix = np.stack([voice, voice], 1) * 0.9 + bus
    mix = mix / max(1.0, np.abs(mix).max() / 0.98)
    pcm = (mix * 32767).astype(np.int16)
    w = wave.open(out_path, 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
    w.close()
    print(f'wrote {out_path}: {dur:.2f}s')


if __name__ == '__main__':
    main(*sys.argv[1:4])
