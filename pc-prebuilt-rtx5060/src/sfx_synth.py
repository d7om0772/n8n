"""Procedural sound effects (no music: noise sweeps, clicks, thuds, metallic hits).
Writes 48 kHz stereo WAVs into ./sfx_synth/.  usage: python sfx_synth.py"""
import os
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sfx_synth')
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(SR * d)) / SR


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)


def sweep_noise(d, f0, f1, f2=None, q=0.9, blocks=64):
    """band-passed noise whose centre frequency glides f0 -> f1 (-> f2)."""
    n = int(SR * d)
    x = rng.standard_normal(n)
    y = np.zeros(n)
    idx = np.linspace(0, n, blocks + 1).astype(int)
    for i in range(blocks):
        p = i / (blocks - 1)
        if f2 is None:
            fc = f0 * (f1 / f0) ** p
        else:
            fc = f0 * (f1 / f0) ** (2 * p) if p < .5 else f1 * (f2 / f1) ** (2 * p - 1)
        lo, hi = fc / (1 + q), min(fc * (1 + q), SR / 2 - 100)
        seg = slice(max(0, idx[i] - 2048), idx[i + 1])
        yy = bp(x[seg], lo, hi)
        y[idx[i]:idx[i + 1]] = yy[-(idx[i + 1] - idx[i]):]
    return y


def env(n, a, r, curve=2.0):
    """attack fraction a, then decay to zero."""
    e = np.ones(n)
    na = max(1, int(n * a))
    e[:na] = np.linspace(0, 1, na) ** 1.5
    e[na:] = np.linspace(1, 0, n - na) ** curve
    return e


def stereo(x, pan_from=0.0, pan_to=0.0):
    p = np.linspace(pan_from, pan_to, len(x))
    l = x * np.cos((p + 1) * np.pi / 4)
    r = x * np.sin((p + 1) * np.pi / 4)
    return np.stack([l, r], 1)


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def save(name, x):
    os.makedirs(OUT, exist_ok=True)
    if x.ndim == 1:
        x = stereo(x)
    x = norm(x)
    # 5 ms fade in/out to avoid clicks
    f = int(SR * .005)
    x[:f] *= np.linspace(0, 1, f)[:, None]
    x[-f:] *= np.linspace(1, 0, f)[:, None]
    wavfile.write(os.path.join(OUT, name + '.wav'), SR, (x * 32767).astype(np.int16))


def metal(d, partials, decay, strike=0.002):
    t = t_(d)
    y = np.zeros_like(t)
    for f, a, k in partials:
        y += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t * k / decay)
    tr = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t / strike)
    return y + .6 * tr


def click(d=.03, fc=2500, body=.004):
    t = t_(d)
    n = hp(rng.standard_normal(len(t)), 800) * np.exp(-t / .0012)
    b = np.sin(2 * np.pi * fc * t) * np.exp(-t / body)
    return n * .8 + b * .5


def build():
    # whooshes / swipes
    w = sweep_noise(.55, 350, 2600, 700, q=.8)
    save('whoosh', stereo(w * env(len(w), .55, .45, 2.2), -.6, .6))
    w = sweep_noise(.85, 220, 1800, 400, q=.7) + .5 * lp(rng.standard_normal(int(SR * .85)), 300)
    save('whoosh_big', stereo(w * env(len(w), .5, .5, 2.5), .5, -.5))
    w = sweep_noise(.22, 1200, 5200, q=.9)
    save('swipe', stereo(w * env(len(w), .35, .65, 2.0), .3, -.3))
    w = sweep_noise(.16, 2200, 7000, q=1.0)
    save('swipe_hi', stereo(w * env(len(w), .3, .7, 2.0), -.2, .2))
    w = sweep_noise(.9, 300, 5200, q=.6)
    save('riser', w * np.linspace(0, 1, len(w)) ** 2.2 * env(len(w), .95, .05, 1))
    w = sweep_noise(.6, 4000, 250, q=.8)
    save('whoosh_down', stereo(w * env(len(w), .2, .8, 2.2), .4, -.4))
    # pop: short pitch-dropping blip + transient
    t = t_(.12)
    f = 260 + 900 * np.exp(-t / .012)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .03)
    save('pop', y + .3 * click(.12))
    t = t_(.1)
    f = 420 + 1500 * np.exp(-t / .008)
    save('pop_hi', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .022) + .2 * click(.1, 4000))
    # clicks / ticks / keys
    save('click', click(.05, 2300, .006))
    save('tick', click(.03, 4200, .0025) * .7)
    for i in range(6):
        d = .09
        y = np.zeros(int(SR * d))
        a = click(.02, rng.uniform(1700, 2600), .003) * rng.uniform(.7, 1)
        y[:len(a)] += a
        o = int(SR * rng.uniform(.035, .055))
        b = click(.02, rng.uniform(2400, 3400), .002) * .45
        y[o:o + len(b)] += b
        y += .15 * lp(rng.standard_normal(len(y)), 900) * np.exp(-t_(d) / .01)
        save(f'key{i}', y)
    # enter key (heavier)
    y = click(.12, 1400, .01) + .4 * lp(rng.standard_normal(int(SR * .12)), 500) * np.exp(-t_(.12) / .02)
    save('key_enter', y)
    # camera shutter: two mechanical clacks
    y = np.zeros(int(SR * .2))
    for o, g in ((0, 1), (.075, .8)):
        c = click(.05, 1800 + 600 * g, .005) + .5 * bp(rng.standard_normal(int(SR * .05)), 600, 3000) * np.exp(-t_(.05) / .008)
        y[int(o * SR):int(o * SR) + len(c)] += c * g
    save('shutter', y)
    # impact / thud
    t = t_(.7)
    f = 48 + 70 * np.exp(-t / .06)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .22)
    y += .5 * lp(rng.standard_normal(len(t)), 1200) * np.exp(-t / .03)
    save('impact', y)
    t = t_(.4)
    f = 70 + 120 * np.exp(-t / .03)
    save('thump', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .1) + .3 * click(.4, 900, .01))
    # metallic hits (single strikes, inharmonic partials => not musical notes)
    save('ding', metal(1.2, [(1873, 1, 1), (3212, .55, 1.6), (4781, .35, 2.2), (6630, .2, 3)], .5))
    save('pling', metal(.8, [(2650, 1, 1), (4310, .4, 1.8), (6980, .25, 2.6)], .28))
    clunk = lp(rng.standard_normal(int(SR * .12)), 900) * np.exp(-t_(.12) / .02)
    ching = metal(1.0, [(2310, 1, 1), (3550, .7, 1.4), (5260, .5, 1.9), (7020, .3, 2.6)], .35)
    y = np.zeros(int(SR * 1.1))
    y[:len(clunk)] += clunk * .9
    o = int(SR * .07)
    y[o:o + len(ching)] += ching[:len(y) - o]
    save('kaching', y)
    # coins: scattered tiny metallic ticks
    y = np.zeros(int(SR * .5))
    for i in range(9):
        o = int(SR * (i * .045 + rng.uniform(0, .02)))
        m = metal(.15, [(rng.uniform(3500, 5200), 1, 1), (rng.uniform(6000, 8000), .5, 1.5)], .05) * rng.uniform(.4, 1) * (1 - i / 12)
        y[o:o + len(m)] += m[:len(y) - o]
    save('coins', y)
    # glitch: gated, bit-crushed noise + buzz
    d = .38
    t = t_(d)
    n = rng.standard_normal(len(t))
    gate = (np.sin(2 * np.pi * 23 * t + 3 * np.sin(2 * np.pi * 5 * t)) > -.2).astype(float)
    buzz = np.sign(np.sin(2 * np.pi * 95 * t)) * .5
    y = (np.round((n * .5 + buzz) * 6) / 6) * gate
    y = bp(y, 200, 9000) * env(len(t), .02, .98, 1.3)
    save('glitch', y)
    d = .22
    t = t_(d)
    y = np.round(rng.standard_normal(len(t)) * 3) / 3 * (np.sin(2 * np.pi * 41 * t) > 0)
    save('glitch2', hp(y, 400) * env(len(t), .02, .98, 1.5))
    # error buzz: two short buzzy pulses (UI alert, not melodic)
    y = np.zeros(int(SR * .32))
    for o in (0, .16):
        tt = t_(.11)
        s = (2 * ((tt * 150) % 1) - 1) * np.exp(-tt / .06)
        y[int(o * SR):int(o * SR) + len(s)] += lp(s, 2500)
    save('buzz', y)
    # scribble (strike-through)
    t = t_(.25)
    y = bp(rng.standard_normal(len(t)), 1800, 5000) * (.6 + .4 * np.sin(2 * np.pi * 28 * t)) * env(len(t), .1, .9, 1.2)
    save('scribble', y)
    # soft airy swell for the opening
    w = sweep_noise(.7, 600, 6000, q=.7)
    save('swell', w * np.linspace(0, 1, len(w)) ** 1.8 * env(len(w), .9, .1, 1))


if __name__ == '__main__':
    build()
    print('wrote', sorted(os.listdir(OUT)))
