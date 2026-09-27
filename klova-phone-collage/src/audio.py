"""Synthesises every sound effect in code (no samples, no music) and mixes them under the voice-over.
usage: python3 audio.py sfx_events.json voice.wav mix.wav
"""
import json, sys
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(3)


def T(d):
    return np.arange(int(d * SR)) / SR


def env(d, a=0.002, tau=0.1):
    t = T(d)
    e = np.exp(-t / tau)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'lowpass', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'highpass', fs=SR, output='sos'), x)


def noise(d):
    return rng.standard_normal(int(d * SR))


def tone(f, d, tau, a=0.003, harm=((1, 1.0),)):
    t = T(d)
    s = sum(g * np.sin(2 * np.pi * f * h * t) for h, g in harm)
    return s * env(d, a, tau)


def sweep(f0, f1, d, tau):
    t = T(d)
    f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.002, tau)


def place(dst, src, at):
    i = int(at * SR)
    n = min(len(src), len(dst) - i)
    if n > 0:
        dst[i:i + n] += src[:n]


def norm(x, peak=0.8):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def moving_bp_noise(d, f0, f1, width=0.6):
    # noise through a band-pass whose centre glides from f0 to f1 (block-wise)
    x = noise(d)
    out = np.zeros_like(x)
    blk = 480
    for i in range(0, len(x), blk):
        c = f0 * (f1 / f0) ** (i / len(x))
        seg = bp(x[max(0, i - 2000):i + blk], c * (1 - width / 2), min(c * (1 + width / 2), SR / 2 - 100))
        out[i:i + blk] = seg[-len(x[i:i + blk]):]
    return out


# ---------------------------------------------------------------- sounds
def s_notif(p):
    a = tone(1318.5 * p, 0.6, 0.22, harm=((1, 1), (2, .25), (3, .08)))
    b = tone(1760 * p, 0.7, 0.3, harm=((1, 1), (2, .25), (3, .08)))
    out = np.zeros(int(0.9 * SR)); place(out, a, 0); place(out, b * 0.9, 0.095)
    return norm(out, .7)


def s_buzz(p):
    d = 0.32
    t = T(d)
    x = np.tanh(3 * np.sin(2 * np.pi * 172 * p * t)) * 0.6 + 0.4 * np.sin(2 * np.pi * 344 * p * t)
    e = ((t < 0.13) | ((t > 0.17) & (t < 0.3))).astype(float)
    e = lp(e, 60)
    return norm(lp(x * e, 900), .55)


def s_tap(p):
    c = bp(noise(0.012), 1800 * p, 6000) * env(0.012, 0.0005, 0.003)
    th = tone(190 * p, 0.04, 0.012)
    out = np.zeros(int(0.05 * SR)); place(out, c * 1.0, 0); place(out, th * 0.6, 0)
    return norm(out, .6)


def s_key(p):
    c = hp(noise(0.02), 1500) * env(0.02, 0.0003, 0.004)
    r = tone(2300 * p, 0.03, 0.006) * 0.5
    b = tone(420 * p, 0.03, 0.008) * 0.35
    out = np.zeros(int(0.035 * SR)); place(out, c, 0); place(out, r, 0); place(out, b, 0)
    return norm(out, .5 + 0.1 * rng.random())


def s_pop(p):
    s = sweep(480 * p, 1150 * p, 0.09, 0.035)
    c = bp(noise(0.006), 2000, 7000) * env(0.006, 0.0003, 0.002) * 0.3
    out = np.zeros(int(0.1 * SR)); place(out, s, 0); place(out, c, 0)
    return norm(out, .7)


def s_popimg(p):
    w = moving_bp_noise(0.16, 1200 * p, 3500 * p) * np.hanning(int(0.16 * SR)) * 0.35
    out = np.zeros(int(0.22 * SR)); place(out, w, 0); place(out, s_pop(0.85 * p), 0.05)
    return norm(out, .7)


def s_send(p):
    d = 0.2
    w = moving_bp_noise(d, 700 * p, 4200 * p) * np.sin(np.pi * T(d) / d) ** 2 * 0.8
    bl = sweep(620 * p, 1500 * p, 0.08, 0.03) * 0.5
    out = np.zeros(int(0.26 * SR)); place(out, w, 0); place(out, bl, 0.1)
    return norm(out, .65)


def s_whoosh(p):
    d = 0.42 / p
    x = moving_bp_noise(d, 350 * p, 2600 * p, 0.9)
    t = T(d)
    e = np.sin(np.pi * (t / d) ** 0.7) ** 2
    return norm(lp(x * e, 6000), .55)


def s_swipe(p):
    d = 0.24
    x = moving_bp_noise(d, 1500 * p, 5000 * p, 0.7)
    e = np.sin(np.pi * T(d) / d) ** 1.5
    return norm(x * e, .45)


def s_stamp(p):
    th = tone(88 * p, 0.3, 0.09, a=0.001, harm=((1, 1), (2, .3)))
    sub = tone(55 * p, 0.3, 0.12, a=0.001) * 0.6
    n = lp(noise(0.05), 1800) * env(0.05, 0.0005, 0.012)
    out = np.zeros(int(0.32 * SR)); place(out, th, 0); place(out, sub, 0); place(out, n * 0.9, 0)
    return norm(out, .9)


def s_marker(p):
    d = 0.28
    x = bp(noise(d), 2500 * p, 5200 * p) * (0.7 + 0.3 * np.sin(2 * np.pi * 38 * T(d)))
    e = np.sin(np.pi * T(d) / d) ** 0.8
    return norm(x * e, .35)


def s_shutter(p):
    def click(f):
        return bp(noise(0.012), f, f * 2.6) * env(0.012, 0.0003, 0.003)
    whirr = bp(noise(0.06), 600, 2500) * np.hanning(int(0.06 * SR)) * 0.35
    out = np.zeros(int(0.2 * SR))
    place(out, click(2400), 0); place(out, whirr, 0.012); place(out, click(1500) * 0.85, 0.075)
    place(out, tone(210, 0.05, 0.015) * 0.3, 0.075)
    return norm(out, .85)


def s_tick(p):
    return norm(tone(900 * p, 0.12, 0.035, harm=((1, 1), (2, .35), (4, .1))), .55)


def s_sticker(p):
    slap = lp(noise(0.04), 2500) * env(0.04, 0.0005, 0.01)
    th = tone(140 * p, 0.12, 0.035, a=0.001)
    cr = hp(noise(0.06), 4000) * env(0.06, 0.001, 0.02) * 0.4
    out = np.zeros(int(0.14 * SR)); place(out, slap, 0); place(out, th * 0.8, 0); place(out, cr, 0.01)
    return norm(out, .75)


def s_coin(p):
    f = 1560 * p
    parts = [(1, 1), (2.76, .5), (5.4, .25), (8.93, .12)]
    d = 0.55
    t = T(d)
    x = sum(g * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (0.22 / r ** 0.4)) for r, g in parts)
    x[:int(.001 * SR)] *= np.linspace(0, 1, int(.001 * SR))
    k = bp(noise(0.01), 3000, 9000) * env(0.01, 0.0003, 0.003) * 0.6
    out = np.zeros(int(0.6 * SR)); place(out, k, 0); place(out, x, 0.004)
    return norm(out, .6)


def s_heart(p):
    out = np.zeros(int(0.7 * SR))
    place(out, s_pop(1.3 * p) * 1.0, 0)
    place(out, tone(1568 * p, 0.5, 0.18, harm=((1, 1), (2, .2))) * 0.5, 0.06)
    place(out, tone(2093 * p, 0.5, 0.18, harm=((1, 1), (2, .2))) * 0.4, 0.12)
    return norm(out, .75)


def s_sparkle(p):
    out = np.zeros(int(0.7 * SR))
    for i, f in enumerate([2093, 2637, 3136, 4186, 3520]):
        place(out, tone(f * p, 0.3, 0.07, harm=((1, 1), (2, .15))) * (0.9 - i * 0.1), i * 0.042)
    return norm(out, .45)


def s_success(p):
    out = np.zeros(int(1.2 * SR))
    for i, f in enumerate([1046.5, 1318.5, 1568, 2093]):
        place(out, tone(f * p, 0.9, 0.3, harm=((1, 1), (2, .3), (3, .1))) * (1 if i < 3 else 1.1), i * 0.075)
    return norm(out, .75)


SOUNDS = {k[2:]: v for k, v in globals().items() if k.startswith('s_')}
BUS = {  # per-sound trim relative to the voice (linear); tuned so every effect sits 4-15 dB under the speech
    'notif': .19, 'buzz': .09, 'tap': .25, 'key': .42, 'pop': .2, 'popimg': .2, 'send': .3, 'whoosh': .32,
    'swipe': .24, 'stamp': .21, 'marker': .43, 'shutter': .51, 'tick': .26, 'sticker': .24, 'coin': .245,
    'heart': .195, 'sparkle': .137, 'success': .2,
}


def main(events_path, voice_path, out_path):
    ev = json.load(open(events_path))
    sr_v, v = wavfile.read(voice_path)
    v = v.astype(np.float32) / 32768
    if v.ndim > 1:
        v = v.mean(1)
    v = resample_poly(v, SR, sr_v).astype(np.float64)
    n = len(v)
    sfx = np.zeros(n)
    for e in ev:
        snd = SOUNDS[e['name']](e.get('pitch', 1))
        place(sfx, snd * e['gain'] * BUS[e['name']], max(0, e['t']))
    # gentle duck of the sfx bus while the voice is speaking
    ve = np.abs(v)
    k = int(0.03 * SR)
    ve = np.convolve(ve, np.ones(k) / k, 'same')
    duck = 1 - 0.3 * np.clip(ve / 0.08, 0, 1)
    mix = v + sfx * duck
    stereo = np.stack([mix, mix], 1)
    wavfile.write(out_path, SR, (np.clip(stereo, -1, 1) * 32767).astype(np.int16))
    wavfile.write(out_path.replace('.wav', '_sfx_only.wav'), SR, (np.clip(sfx, -1, 1) * 32767).astype(np.int16))
    print('voice rms', np.sqrt(np.mean(v ** 2)), 'sfx rms', np.sqrt(np.mean(sfx ** 2)), 'peak', np.max(np.abs(mix)))


if __name__ == '__main__':
    main(*sys.argv[1:4])
