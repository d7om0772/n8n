# Procedural SFX library + mixer (no music). usage: python3 sfx.py voice.wav out.wav
import sys, json, math, os
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
R = np.random.default_rng(42)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env_ad(n, a, d, curve=5.0):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-5), np.exp(-(t - a) / max(d, 1e-5) * curve / 5 * 5))
    return e


def exp_dec(d, tau):
    t = t_(d)
    return np.exp(-t / tau)


def noise(d):
    return R.standard_normal(int(d * SR))


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='high', fs=SR, output='sos'), x)


def svf_sweep(x, f0, f1, q=1.2, shape=None):
    """state-variable bandpass with swept center frequency"""
    n = len(x)
    tt = np.linspace(0, 1, n)
    if shape is None:
        f = f0 * (f1 / f0) ** tt
    else:
        f = shape(tt)
    out = np.zeros(n)
    low = band = 0.0
    fc = 2 * np.sin(np.pi * np.clip(f, 20, SR / 6) / SR)
    damp = 1.0 / q
    for i in range(n):
        high = x[i] - low - damp * band
        band += fc[i] * high
        low += fc[i] * band
        out[i] = band
    return out


def sine_glide(d, f0, f1, curve='exp'):
    t = t_(d)
    if curve == 'exp':
        f = f0 * (f1 / f0) ** (t / d)
    else:
        f = f0 + (f1 - f0) * (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph)


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def fade(x, fi=0.002, fo=0.01):
    n = len(x)
    a = int(fi * SR); b = int(fo * SR)
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x


# ---------------------------------------------------------------- sounds (mono float)
def s_whoosh(d=0.45, up=True):
    n = noise(d)
    shape = (lambda tt: 350 + 3200 * np.sin(np.pi * tt) ** 1.5) if up else None
    x = svf_sweep(n, 400, 3000, q=1.6, shape=shape)
    tt = np.linspace(0, 1, len(x))
    e = np.sin(np.pi * np.clip(tt / 0.65, 0, 1) * 0.5) ** 2 * np.where(tt > 0.65, np.exp(-(tt - 0.65) * 12), 1)
    return fade(norm(x * e, 0.9))


def s_swish():
    x = s_whoosh(0.22)
    return norm(hp(x, 900), 0.8)


def s_pop(pitch=1.0):
    d = 0.11
    body = sine_glide(d, 950 * pitch, 260 * pitch) * exp_dec(d, 0.028)
    click = hp(noise(d), 3000) * exp_dec(d, 0.003) * 0.35
    return fade(norm(body + click, 0.9), 0.0005)


def s_tick():
    d = 0.06
    x = bp(noise(d), 1800, 5200) * exp_dec(d, 0.006) * 0.8 + sine_glide(d, 320, 160) * exp_dec(d, 0.012) * 0.6
    return fade(norm(x, 0.6), 0.0005)


def s_thud(f=70):
    d = 0.4
    x = sine_glide(d, f * 1.6, f * 0.65) * exp_dec(d, 0.09)
    x += lp(noise(d), 700) * exp_dec(d, 0.02) * 0.8
    return fade(norm(np.tanh(x * 1.5), 0.95), 0.0005)


def s_slap():
    d = 0.3
    crack = bp(noise(d), 700, 6500) * exp_dec(d, 0.018)
    low = sine_glide(d, 150, 70) * exp_dec(d, 0.05) * 0.9
    return fade(norm(crack * 1.1 + low, 0.95), 0.0003)


def s_slam():
    d = 0.6
    x = s_thud(60)[:int(d * SR)] if False else None
    body = sine_glide(d, 110, 42) * exp_dec(d, 0.14)
    crack = bp(noise(d), 500, 5000) * exp_dec(d, 0.03)
    return fade(norm(np.tanh((body * 1.4 + crack * 0.9) * 1.3), 0.95), 0.0003)


def s_stamp(small=False):
    d = 0.35 if small else 0.5
    k = 1.5 if small else 1.0
    body = sine_glide(d, 140 * k, 55 * k) * exp_dec(d, 0.07 if small else 0.11)
    knock = np.sin(2 * np.pi * 230 * k * t_(d)) * exp_dec(d, 0.025) * 0.6
    click = bp(noise(d), 1500, 7000) * exp_dec(d, 0.006) * 0.9
    return fade(norm(np.tanh((body + knock + click) * 1.6), 0.95), 0.0003)


def s_boom():
    d = 1.3
    sub = sine_glide(d, 70, 32) * exp_dec(d, 0.35)
    rum = lp(noise(d), 160, 4) * exp_dec(d, 0.25) * 2.0
    return fade(norm(np.tanh((sub + rum) * 1.8), 0.95), 0.001, 0.2)


def s_hit():
    d = 0.8
    x = s_boom()[:int(d * SR)] * 0.9
    snare = bp(noise(d), 900, 6000) * exp_dec(d, 0.06) * 0.7
    x = x + snare
    p = s_pop(0.8); x[:len(p)] += p * 0.6
    return fade(norm(x, 0.95), 0.0005, 0.1)


def s_rip():
    d = 0.5
    n = int(d * SR)
    grains = np.zeros(n)
    t = 0
    while t < n:
        grains[t] = R.uniform(0.3, 1.0) * R.choice([-1, 1])
        t += int(R.uniform(0.0006, 0.004) * SR)
    x = bp(signal.lfilter([1], [1, -0.6], grains), 900, 7000)
    x += bp(noise(d), 1500, 5000) * 0.15
    tt = np.linspace(0, 1, n)
    e = np.clip(tt / 0.08, 0, 1) * (0.7 + 0.3 * np.sin(tt * 40) ** 2) * np.exp(-tt * 2.2)
    return fade(norm(x * e, 0.9))


def s_riser(d=0.35):
    x = svf_sweep(noise(d), 300, 7000, q=2.0)
    x += sine_glide(d, 200, 900) * 0.25
    tt = np.linspace(0, 1, len(x))
    return fade(norm(x * tt ** 2, 0.8), 0.001, 0.005)


def clicks(d, rate0, rate1, f_lo=1800, f_hi=4200, decay=0.008):
    n = int(d * SR)
    out = np.zeros(n + int(0.05 * SR))
    t = 0.0
    while t < d:
        i = int(t * SR)
        f = R.uniform(f_lo, f_hi)
        L = int(0.03 * SR)
        tt = np.arange(L) / SR
        ping = np.sin(2 * np.pi * f * tt) * np.exp(-tt / decay) * R.uniform(0.3, 1.0)
        ping += R.standard_normal(L) * np.exp(-tt / 0.001) * 0.3
        out[i:i + L] += ping
        rate = rate0 + (rate1 - rate0) * (t / d)
        t += R.exponential(1 / rate)
    return out


def s_scatter():
    return fade(norm(clicks(0.45, 120, 15), 0.8))


def s_rattle(d=0.9):
    x = clicks(d, 25, 60, 1500, 3500, 0.01)
    x = x[:int((d + 0.05) * SR)]
    return fade(norm(x, 0.8), 0.001, 0.05)


def s_scribble(d=0.3):
    n = noise(d)
    x = bp(n, 1400, 5500)
    tt = t_(d)
    am = 0.35 + 0.65 * np.abs(np.sin(2 * np.pi * 7.5 * tt + R.uniform(0, 3)))
    x = x * am * (0.8 + 0.2 * np.sin(2 * np.pi * 31 * tt))
    return fade(norm(x, 0.7), 0.01, 0.03)


def s_marker(d=0.22):
    x = bp(noise(d), 1200, 4500)
    tt = np.linspace(0, 1, len(x))
    return fade(norm(x * np.sin(np.pi * tt) ** 0.5, 0.6), 0.005, 0.02)


def s_boing():
    d = 0.55
    tt = t_(d)
    f = 190 + 150 * (tt / d) + 70 * np.sin(2 * np.pi * 16 * tt) * np.exp(-tt * 5)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_dec(d, 0.18)
    x += 0.3 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * exp_dec(d, 0.1)
    return fade(norm(x, 0.8), 0.002)


def s_buzzer():
    d = 0.42
    tt = t_(d)
    x = signal.square(2 * np.pi * 105 * tt) + signal.square(2 * np.pi * 111 * tt)
    x = lp(x, 1800)
    gate = np.where((tt < 0.17) | ((tt > 0.22) & (tt < 0.40)), 1.0, 0.0)
    gate = np.convolve(gate, np.ones(200) / 200, mode='same')
    return fade(norm(x * gate, 0.55))


def s_shutter():
    d = 0.2
    x = np.zeros(int(d * SR))
    for t0, g in ((0.0, 1.0), (0.07, 0.8)):
        i = int(t0 * SR)
        L = int(0.03 * SR)
        x[i:i + L] += hp(noise(0.03), 2500) * exp_dec(0.03, 0.004) * g
        x[i:i + L] += np.sin(2 * np.pi * 900 * t_(0.03)) * exp_dec(0.03, 0.006) * 0.4 * g
    return fade(norm(x, 0.8), 0.0003)


def s_tape():
    d = 0.28
    n = int(d * SR)
    x = np.zeros(n)
    t = 0
    while t < n:
        x[t] = R.uniform(0.2, 1)
        t += int(R.uniform(0.0015, 0.005) * SR)
    x = bp(x, 1500, 8000) + bp(noise(d), 2000, 6000) * 0.1
    tt = np.linspace(0, 1, n)
    return fade(norm(x * np.sin(np.pi * tt), 0.7))


def bell(f, d=1.4, decay=0.35, partials=((1, 1), (2.76, 0.5), (5.4, 0.25), (8.9, 0.12))):
    tt = t_(d)
    x = np.zeros(len(tt))
    for m, a in partials:
        x += a * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt / (decay / (m ** 0.5)))
    return x


def s_ding():
    x = bell(1320) + 0.6 * np.pad(bell(1760, 1.32), (int(0.08 * SR), 0))[:int(1.4 * SR)]
    return fade(norm(x, 0.7), 0.001, 0.2)


def s_sparkle():
    d = 0.8
    x = np.zeros(int(d * SR))
    for k in range(7):
        i = int(k * 0.07 * SR)
        b = bell(R.uniform(2600, 5200), 0.3, 0.08)
        x[i:i + len(b)] += b[:len(x) - i] * R.uniform(0.4, 1)
    return fade(norm(x, 0.5), 0.001, 0.1)


def s_flyby(d=2.1):
    tt = t_(d)
    pos = tt / d
    dop = 1 + 0.12 * np.tanh((0.5 - pos) * 5)
    f = 140 * dop
    saw = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    x = lp(saw, 900) * 0.3 + svf_sweep(noise(d), 600, 2000, q=1.0, shape=lambda t: 500 + 1800 * np.exp(-((t - 0.5) / 0.22) ** 2))
    e = np.exp(-((pos - 0.5) / 0.28) ** 2)
    return fade(norm(x * e, 0.7), 0.05, 0.1)


def s_printer(d=0.95):
    tt = t_(d)
    pulses = (np.sin(2 * np.pi * 55 * tt) > 0.6).astype(float)
    x = bp(noise(d), 900, 3200) * pulses + 0.25 * np.sin(2 * np.pi * 120 * tt)
    gate = (np.sin(2 * np.pi * 3.2 * tt) > -0.7).astype(float)
    gate = np.convolve(gate, np.ones(300) / 300, mode='same')
    return fade(norm(x * gate, 0.6), 0.01, 0.05)


def s_flip():
    d = 0.09
    x = bp(noise(d), 1800, 6500)
    tt = np.linspace(0, 1, len(x))
    return fade(norm(x * np.sin(np.pi * tt ** 0.6) * np.exp(-tt * 2), 0.6))


def s_kaching():
    d = 1.2
    x = np.zeros(int(d * SR))
    # drawer / mechanism
    for k in range(4):
        i = int(k * 0.025 * SR)
        L = int(0.02 * SR)
        x[i:i + L] += bp(noise(0.02), 1500, 6000) * exp_dec(0.02, 0.004) * 0.7
    i = int(0.1 * SR)
    b = bell(2093, 1.0, 0.3) + 0.8 * bell(2637, 1.0, 0.28)
    x[i:i + len(b)] += b[:len(x) - i] * 0.9
    # coins jingle
    for k in range(10):
        i = int((0.12 + R.uniform(0, 0.35)) * SR)
        c = bell(R.uniform(3800, 6500), 0.25, 0.05)
        x[i:i + len(c)] += c[:len(x) - i] * R.uniform(0.2, 0.5)
    return fade(norm(x, 0.85), 0.0005, 0.1)


def s_tap():
    d = 0.08
    x = np.sin(2 * np.pi * 1500 * t_(d)) * exp_dec(d, 0.01) * 0.6 + hp(noise(d), 3000) * exp_dec(d, 0.002) * 0.6
    x += sine_glide(d, 300, 150) * exp_dec(d, 0.015) * 0.5
    return fade(norm(x, 0.8), 0.0003)


def make(name, kw):
    if name == 'whoosh': return s_whoosh()
    if name == 'swish': return s_swish()
    if name == 'pop': return s_pop(kw.get('pitch', 1.0))
    if name == 'tick': return s_tick()
    if name == 'thud': return s_thud()
    if name == 'slap': return s_slap()
    if name == 'slam': return s_slam()
    if name == 'stamp': return s_stamp()
    if name == 'stamp_small': return s_stamp(True)
    if name == 'boom': return s_boom()
    if name == 'hit': return s_hit()
    if name == 'rip': return s_rip()
    if name == 'riser': return s_riser(kw.get('dur', 0.35))
    if name == 'scatter': return s_scatter()
    if name == 'rattle': return s_rattle(kw.get('dur', 0.9))
    if name == 'scribble': return s_scribble(kw.get('dur', 0.3))
    if name == 'marker': return s_marker(kw.get('dur', 0.22))
    if name == 'boing': return s_boing()
    if name == 'buzzer': return s_buzzer()
    if name == 'shutter': return s_shutter()
    if name == 'tape': return s_tape()
    if name == 'ding': return s_ding()
    if name == 'sparkle': return s_sparkle()
    if name == 'flyby': return s_flyby(kw.get('dur', 2.1))
    if name == 'printer': return s_printer(kw.get('dur', 0.95))
    if name == 'flip': return s_flip()
    if name == 'kaching': return s_kaching()
    if name == 'tap': return s_tap()
    raise KeyError(name)


# per-sound bus level (relative, before global SFX gain) and stereo pan
LEVEL = {'tick': 0.30, 'pop': 1.0, 'whoosh': 0.5, 'swish': 0.8, 'slap': 0.5, 'slam': 0.35, 'stamp': 0.45, 'stamp_small': 0.55,
         'boom': 0.45, 'hit': 0.5, 'rip': 0.6, 'riser': 0.9, 'scatter': 0.15, 'rattle': 1.0, 'scribble': 1.2, 'marker': 1.0,
         'boing': 0.5, 'buzzer': 0.5, 'shutter': 0.9, 'tape': 0.9, 'ding': 0.7, 'sparkle': 0.6, 'flyby': 1.0, 'printer': 0.3,
         'flip': 0.5, 'kaching': 0.7, 'tap': 1.0, 'thud': 0.5}


def main(voice_path, events_path, out_path):
    ev = json.load(open(events_path))
    dur = ev['dur']
    N = int(dur * SR) + int(0.2 * SR)
    sr_v, v = wavfile.read(voice_path)
    v = v.astype(np.float64) / 32768.0
    if v.ndim > 1:
        v = v.mean(axis=1)
    v = signal.resample_poly(v, SR, sr_v)
    voice = np.zeros(N); voice[:min(N, len(v))] = v[:N]
    voice = norm(voice, 0.89)
    bus = np.zeros((N, 2))
    rng = np.random.default_rng(3)
    for (t, name, gain, kw) in ev['sfx']:
        x = make(name, kw) * gain * LEVEL[name]
        i = int(max(0, t) * SR)
        L = min(len(x), N - i)
        if L <= 0:
            continue
        pan = kw.get('pan', rng.uniform(-0.25, 0.25))
        if name in ('whoosh', 'flyby'):
            # moving pan for motion sounds
            p = np.linspace(-0.5, 0.5, L)
            lg, rg = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)
        else:
            lg = math.cos((pan + 1) * math.pi / 4); rg = math.sin((pan + 1) * math.pi / 4)
        bus[i:i + L, 0] += x[:L] * lg * 1.41
        bus[i:i + L, 1] += x[:L] * rg * 1.41
    # sidechain: keep SFX short-term level >= 7 dB under the voice while it speaks
    win = int(0.05 * SR)
    k = np.ones(win) / win
    venv = np.sqrt(np.convolve(voice ** 2, k, mode='same')) + 1e-6
    senv = np.sqrt(np.convolve(bus.mean(1) ** 2, k, mode='same')) + 1e-6
    vdb = 20 * np.log10(venv); sdb = 20 * np.log10(senv)
    active = vdb > -38
    target = np.where(active, vdb - 7.0, -14.0)
    gdb = np.minimum(0.0, target - sdb)
    g = 10 ** (gdb / 20)
    # smooth: fast attack, slower release
    sm = np.empty_like(g); cur = 1.0
    att = 1 - math.exp(-1 / (0.004 * SR)); rel = 1 - math.exp(-1 / (0.09 * SR))
    for i in range(len(g)):
        c = att if g[i] < cur else rel
        cur += (g[i] - cur) * c
        sm[i] = cur
    bus *= sm[:, None]
    mix = np.stack([voice, voice], axis=1) + bus
    # soft clip safety
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    wavfile.write(out_path, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    wavfile.write(out_path.replace('.wav', '_sfxonly.wav'), SR, (np.clip(bus, -1, 1) * 32767).astype(np.int16))
    print('mixed', out_path, 'events', len(ev['sfx']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
