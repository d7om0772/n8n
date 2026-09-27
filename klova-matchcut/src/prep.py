"""Prepare collage assets with one shared riso-style grade.

Every photo goes through the same pipeline so no shot drifts in colour:
luminance -> 4-stop gradient map (espresso -> rose -> cream), red/orange
hues pushed to the single terracotta accent, then a fine print dot screen
in the shadows. Hero objects are cut to clean circles for the match cuts.
"""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
OUT = os.path.join(HERE, 'assets')
os.makedirs(OUT, exist_ok=True)

INK = (42, 23, 17)
ROAST = (112, 62, 46)
BRAND = (189, 148, 132)
CREAM = (246, 236, 223)
ACC_D = (122, 36, 18)
ACC = (212, 84, 44)
ACC_L = (240, 150, 105)


def hexs(c):
    return np.array(c, dtype=np.float32) / 255.0


def gradmap(L, stops):
    pos = np.array([p for p, _ in stops], dtype=np.float32)
    cols = np.stack([hexs(c) for _, c in stops])
    out = np.empty(L.shape + (3,), np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(L, pos, cols[:, ch])
    return out


def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0)
    return h, s, mx


def dot_screen(shape, period=7.0, angle=22.0):
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.deg2rad(angle)
    u = (xx * np.cos(a) + yy * np.sin(a)) / period
    v = (-xx * np.sin(a) + yy * np.cos(a)) / period
    # distance to nearest cell centre, 0 at centre .. ~0.707 at corner
    du = u - np.round(u)
    dv = v - np.round(v)
    return np.sqrt(du * du + dv * dv)


def grade(img, contrast=1.12, lift=0.0, accent=1.0, dots=0.55, period=6.5):
    a = np.asarray(img.convert('RGBA')).astype(np.float32) / 255.0
    rgb, alpha = a[..., :3], a[..., 3]
    L = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    L = np.clip((L - 0.5) * contrast + 0.5 + lift, 0, 1)
    base = gradmap(L, [(0.0, INK), (0.30, ROAST), (0.62, BRAND), (0.93, CREAM), (1.0, CREAM)])
    h, s, v = rgb_to_hsv(rgb)
    hue_w = np.clip(1 - np.abs(((h + 30) % 360) - 40) / 45.0, 0, 1)  # reds..oranges
    w = np.clip((s - 0.25) * 1.8, 0, 1) * hue_w * np.clip(v * 1.6, 0, 1) * accent
    accc = gradmap(L, [(0.0, ACC_D), (0.45, ACC), (0.85, ACC_L), (1.0, CREAM)])
    out = base * (1 - w[..., None]) + accc * w[..., None]
    if dots > 0:
        # amplitude-modulated screen: darker areas get bigger ink dots
        d = dot_screen(L.shape, period)
        dark = np.clip(1 - L, 0, 1)
        radius = np.sqrt(dark) * 0.62
        ink = np.clip((radius - d) * 6.0, 0, 1) * dots * np.clip(dark * 1.6, 0, 1)
        out = out * (1 - ink[..., None] * 0.55) + hexs(INK) * ink[..., None] * 0.55
    res = np.concatenate([out, alpha[..., None]], -1)
    return Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8), 'RGBA')


def fit_circle(alpha, thr=128):
    m = alpha > thr
    ys, xs = np.nonzero(m)
    cx, cy = xs.mean(), ys.mean()
    area = m.sum()
    r = np.sqrt(area / np.pi)
    return cx, cy, r


def circle_cut(img, cx, cy, r, size=800):
    img = img.convert('RGBA')
    box = (cx - r, cy - r, cx + r, cy + r)
    c = img.resize((size, size), Image.LANCZOS, box=box)
    mask = Image.new('L', (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((2, 2, size * 4 - 3, size * 4 - 3), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    arr = np.asarray(c).copy()
    arr[..., 3] = (arr[..., 3].astype(np.float32) * np.asarray(mask) / 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def load(name):
    return Image.open(os.path.join(RAW, name)).convert('RGBA')


def save(im, name):
    im.save(os.path.join(OUT, name), optimize=True)
    print('wrote', name, im.size)


def main():
    # --- hero circles -------------------------------------------------
    latte = load('latte.png')
    cx, cy, r = fit_circle(np.asarray(latte)[..., 3])
    save(grade(circle_cut(latte, cx, cy, r - 13), accent=0.55, dots=0.35), 'hero_latte.png')

    orange = load('orange.png')
    cx, cy, r = fit_circle(np.asarray(orange)[..., 3])
    save(grade(circle_cut(orange, cx, cy, r - 12), accent=1.0, dots=0.35), 'hero_orange.png')

    farmer = Image.open(os.path.join(RAW, 'farmer.jpg')).convert('RGBA')
    # the cupped hands full of cherries sit left of centre
    save(grade(circle_cut(farmer, 350, 285, 250), accent=1.15, dots=0.45, contrast=1.2), 'hero_cherries.png')

    beans = Image.open(os.path.join(RAW, 'beans.jpg')).convert('RGBA')
    save(grade(beans, dots=0.4, contrast=1.15, lift=0.05), 'beans.png')

    # --- stickers (keep their paper border) ---------------------------
    for name, acc in [('bag_klova.png', 0.6), ('sack.png', 0.6), ('strawberry.png', 1.1),
                      ('chocolate.png', 0.6), ('espresso_ht.png', 0),
                      ('takeaway_ht.png', 0), ('pointing_ht.png', 0)]:
        im = load(name)
        g = grade(im, accent=acc, dots=0.0 if name.endswith('_ht.png') else 0.4)
        save(g, name.replace('_ht', ''))

    pour = Image.open(os.path.join(RAW, 'pourover.jpg')).convert('RGBA')
    save(grade(pour, dots=0.4, contrast=1.2, lift=-0.03), 'pourover.png')

    # logo: cream + ink versions from the alpha mask
    m = Image.open(os.path.join(RAW, 'logo_mask.png')).convert('L')
    for nm, col in [('logo_ink.png', INK), ('logo_cream.png', CREAM)]:
        lo = Image.new('RGBA', m.size, col + (0,))
        lo.putalpha(m)
        save(lo, nm)

    # paper grain overlay (grey around 128 -> used with soft-light/overlay)
    rng = np.random.default_rng(7)
    H, W = 1920, 1080
    n = rng.normal(0, 1, (H, W)).astype(np.float32)
    fine = np.asarray(Image.fromarray(((n * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
    coarse = rng.normal(0, 1, (H // 24, W // 24)).astype(np.float32)
    coarse = np.asarray(Image.fromarray(((coarse * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    fib = np.zeros((H, W), np.float32)
    im = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(im)
    for _ in range(900):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        ang = rng.uniform(0, np.pi)
        ln = rng.uniform(8, 40)
        dr.line((x, y, x + np.cos(ang) * ln, y + np.sin(ang) * ln), fill=int(rng.uniform(40, 110)), width=1)
    fib = np.asarray(im.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255
    g = 0.5 + (fine - 0.5) * 0.35 + (coarse - 0.5) * 0.18 - fib * 0.25
    save(Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8), 'L'), 'grain.png')


if __name__ == '__main__':
    main()
