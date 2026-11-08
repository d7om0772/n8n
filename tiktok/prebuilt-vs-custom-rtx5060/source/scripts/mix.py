"""Build the SFX bed from a cue sheet and mix it under the voiceover.
Openverse (Wikimedia Commons) sounds are used where downloaded; otherwise a procedural fallback."""
import json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import sfx_synth as S

SR = S.SR
DUR = 34.0
ROOT = os.path.join(os.path.dirname(__file__), "..")


def load_wav(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    pk = np.max(np.abs(x)) + 1e-9
    return x / pk


OV = {  # name -> openverse short id
    "swipe2": "722d27ff", "sel": "bc7cb631", "coins": "87e9e7eb", "keys": "0884f34a", "error": "e223ae42",
    "notif": "7556201c", "pickup": "262ae44a", "hit": "af5ba6e5", "tick": "11e3fb48", "swipe3": "f6dad189",
    "swipe": "34b3887d", "fade": "d1719f98",
}
FALLBACK = {
    "swipe2": lambda: S.whoosh(0.5, 400, 5000), "sel": lambda: S.pop(1300, 700, 0.07),
    "coins": lambda: S.coin(), "keys": lambda: S.typing(1.0), "error": lambda: S.buzzer(),
    "notif": lambda: S.notif(), "pickup": lambda: S.pop(), "hit": lambda: S.impact(0.6, 160, 50),
    "tick": lambda: S.tick(), "swipe3": lambda: S.whoosh(0.38, 600, 6000), "swipe": lambda: S.whoosh(0.5, 250, 3500),
    "fade": lambda: S.whoosh(0.7, 200, 2500, 0.5, -0.5, 0.75),
}
USED = {}


def snd(name):
    if name in OV and os.path.exists(f"{ROOT}/sfx/wav/{OV[name]}.wav"):
        USED[name] = "openverse:" + OV[name]
        return load_wav(f"{ROOT}/sfx/wav/{OV[name]}.wav")
    if name in FALLBACK:
        USED[name] = "synth"
        return FALLBACK[name]()
    USED[name] = "synth"
    return getattr(S, name)()


bed = np.zeros((int((DUR + 1) * SR), 2), np.float32)


def put(t, x, db=0.0, maxlen=None):
    if isinstance(x, str):
        x = snd(x)
    if maxlen:
        x = x[: int(maxlen * SR)].copy()
        fl = min(len(x), int(0.03 * SR))
        x[-fl:] *= np.linspace(1, 0, fl)[:, None]
    g = 10 ** (db / 20)
    i = int(t * SR)
    if i < 0:
        x = x[-i:]; i = 0
    m = min(len(x), len(bed) - i)
    bed[i:i + m] += x[:m] * g


def ease_ticks(t0, t1, steps, power=3):
    # times where an ease-out cubic counter crosses k/steps
    out = []
    for k in range(1, steps + 1):
        v = k / steps
        p = 1 - (1 - v) ** (1 / power)
        out.append(t0 + p * (t1 - t0))
    return out


# ---------------- cue sheet (video time = voice time) ----------------
# S1a hook
put(0.00, S.impact(1.2, 110, 38), -12)
put(0.05, S.blip(1900, 0.06), -24)                 # REC beep
put(1.40, "swipe3", -17)                            # highlight box
put(1.44, S.thud(), -14)
put(1.76, S.whoosh(0.3, 1500, 7000, 0.6, -0.6, 0.3), -18)   # strike
put(2.03, "swipe2", -12)                            # wipe
# S1b
put(2.74, "sel", -16)
put(2.45, S.riser(1.05, 300, 5000), -24)
put(3.45, "pickup", -15)
put(3.45, S.whoosh(0.35, 3000, 400, -0.3, 0.3), -22)
put(4.20, S.impact(0.7, 170, 55), -13)
put(4.21, "swipe3", -19)
put(4.38, "sel", -14)
put(4.78, "swipe", -12)                             # wipe to S2
# S2
put(5.55, S.shutter(), -14)
put(5.6, S.whoosh(0.45, 300, 3000, -0.4, 0.4), -22)
put(6.08, S.thud(), -13)
put(6.42, S.ticker([i * 0.035 for i in range(12)], 0.6), -16)  # digit roll
put(7.05, S.whoosh(0.35, 500, 5000, 0.2, -0.2), -19)
put(7.62, "sel", -17)
for i in range(7):
    put(7.22 + i * 0.17 + 0.1, S.pop(1100 + i * 40, 520, 0.08), -16)
put(7.35, S.ticker([t - 7.35 for t in ease_ticks(7.35, 9.15, 26)], 0.35, 6200), -20)
put(9.13, "coins", -10)
put(9.13, S.thud(), -16)
put(10.08, "swipe2", -12)                           # wipe to S3
# S3
put(10.42, S.whoosh(0.55, 200, 2500, 0, 0, 0.7), -15)  # phone slide
put(10.95, "keys", -15, maxlen=1.0)
put(11.06, "sel", -18)
for i in range(4):
    put(12.2 + i * 0.26, "pickup", -17)
for i in range(3):
    put(13.82 + i * 0.08, S.blip(1500 + i * 180, 0.06), -20)
put(14.55, S.ticker([0, 0.1, 0.2, 0.3], 0.6, 3800), -18)
put(15.10, S.stamp(), -9)
put(15.12, "swipe3", -18)
put(15.55, S.riser(0.28, 500, 7000), -16)
# S4
put(15.80, S.impact(0.8, 140, 45), -14)
put(15.80, S.glitch(0.16), -22)
put(16.98, S.impact(1.0, 180, 40), -9)
put(16.98, S.glitch(0.26, seed=9), -18)
put(17.70, S.whoosh(0.4, 300, 3000, -0.3, 0.3), -20)
put(17.75, S.ticker([t - 17.75 for t in ease_ticks(17.75, 18.7, 16)], 0.4, 6000), -20)
put(18.64, "coins", -14)
# S5a warning
put(19.20, "error", -13)
put(19.20, S.impact(0.6, 160, 60), -18)
put(19.50, S.buzzer(0.32), -22)
put(19.85, "swipe", -13)                            # wipe
# S5b
put(20.75, "pickup", -15)
put(21.45, S.whoosh(0.3, 2000, 500, 0.3, -0.3), -22)
put(22.15, "pickup", -15)
put(22.92, "swipe2", -15)                           # sheet in
put(23.40, S.riser(1.0, 600, 4000), -27)
for i in range(4):
    put(23.5 + i * 0.25, S.tick(0, 0.9, 3500 + i * 300), -17)
put(24.58, "swipe", -12)                            # wipe
# S6
put(25.10, S.whoosh(0.8, 200, 1800, 0.6, -0.6, 0.8), -20)
put(25.88, "sel", -17)
put(26.60, S.whoosh(0.7, 250, 2200, 0.6, -0.6, 0.8), -18)
put(27.36, "sel", -17)
put(28.00, S.click(0.03, 2600), -14)
put(28.05, S.ticker([t - 28.05 for t in ease_ticks(28.05, 28.6, 10)], 0.4, 6000), -20)
put(28.55, "coins", -11)
put(28.98, "swipe2", -12)                           # wipe to S7
# S7
put(30.16, "sel", -17)
put(30.52, S.whoosh(0.5, 200, 2600, 0, 0, 0.7), -15)
for i in range(3):
    put(31.0 + i * 0.32, "notif", -17)
put(31.05, "sel", -19)
put(32.2, "keys", -16, maxlen=0.8)
put(33.1, S.whoosh(0.3, 800, 6000, 0.2, -0.6, 0.4), -17)
put(33.12, "notif", -13)

# ---------------- write bed ----------------
bed = bed[: int(DUR * SR)]
pk = np.max(np.abs(bed))
print("bed peak", pk)
bed_soft = np.tanh(bed * 1.2) / 1.2  # gentle safety saturation on stacked peaks
bed_soft.astype(np.float32).tofile(f"{ROOT}/sfx/bed.f32")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", f"{ROOT}/sfx/bed.f32",
                f"{ROOT}/sfx/bed.wav"], check=True)
json.dump(USED, open(f"{ROOT}/sfx/used.json", "w"), indent=1)
print(json.dumps(USED, indent=1))
