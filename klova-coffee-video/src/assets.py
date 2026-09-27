# -*- coding: utf-8 -*-
"""All paper cut-out assets, drawn procedurally in one palette."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
from lib import *


# ---------------------------------------------------------------- background (static camera, fixed light)
def make_background():
    r = np.random.default_rng(101)
    base = np.zeros((H, W, 3), np.float32)
    base[:] = C['bg']
    a, b = noise_field(H, W, 5, sigma_fine=0.8, coarse_div=16, sigma_coarse=3)
    tex = 1 + 0.02 * a + 0.011 * b
    # paper fibres
    fib = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(fib)
    for _ in range(2600):
        x, y = r.uniform(0, W), r.uniform(0, H)
        ang = r.uniform(0, math.pi)
        ln = r.uniform(6, 26)
        pts = []
        for k in range(5):
            t = k / 4
            pts.append((x + math.cos(ang) * ln * t + r.normal(0, 1.2), y + math.sin(ang) * ln * t + r.normal(0, 1.2)))
        d.line(pts, fill=int(r.uniform(40, 120)), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
    tex = tex * (1 - 0.05 * fib)
    # fixed soft key light from top-left + gentle vignette
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lg = 1.03 - 0.07 * ((xx / W) * 0.4 + (yy / H) * 0.6)
    vx, vy = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    vig = 1 - 0.10 * np.clip((vx ** 2 * 0.8 + vy ** 2 * 0.6) - 0.25, 0, 2)
    out = base * (tex * lg * vig)[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')


# ---------------------------------------------------------------- coffee bean (shaded, real-object look)
def render_bean(L, seed, ratio=0.70, tone=(112, 68, 40)):
    r = np.random.default_rng(seed)
    S = 4
    w = int(L * S)
    h = int(L * ratio * S)
    pad = int(0.25 * L * S)
    Wc, Hc = w + 2 * pad, h + 2 * pad
    yy, xx = np.mgrid[0:Hc, 0:Wc].astype(np.float32)
    u = (xx - Wc / 2) / (w / 2)
    v = (yy - Hc / 2) / (h / 2)
    v2 = v * (1 + 0.07 * u)
    r2 = u * u + v2 * v2
    edge = 1 - np.sqrt(r2)
    alpha = np.clip(edge * (w / 2) / 1.2, 0, 1)
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    n = np.stack([u, v2, z * 1.25], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
    Ld = np.array([-0.5, -0.6, 0.62], np.float32)
    Ld /= np.linalg.norm(Ld)
    lam = np.clip((n * Ld).sum(-1), 0, 1)
    amp = r.uniform(0.07, 0.13)
    ph = r.uniform(-0.3, 0.3)
    vc = amp * np.sin(np.pi * u * 0.95 + ph)
    d = v2 - vc
    cw = 0.08 * np.sqrt(np.clip(1 - u * u * 0.9, 0.05, 1))
    fade = np.clip((0.9 - np.abs(u)) * 7, 0, 1)
    crease = np.exp(-(d / cw) ** 2) * fade
    lip = np.exp(-((d + cw * 1.6) / (cw * 0.9)) ** 2) * fade
    base = np.array(tone, np.float32) * r.uniform(0.86, 1.1)
    col = base[None, None, :] * (0.30 + 0.95 * lam[..., None])
    col = col * (1 - 0.8 * crease[..., None]) + lip[..., None] * np.array([46, 30, 18], np.float32)
    spec = (lam ** 14) * 75
    col += spec[..., None] * np.array([1, 0.88, 0.76], np.float32)
    tx = ndimage.gaussian_filter(r.standard_normal((Hc, Wc)).astype(np.float32), 1.2)
    col *= (1 + 0.05 * tx / (tx.std() + 1e-6))[..., None]
    arr = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA').resize((Wc // S, Hc // S), Image.LANCZOS)


def bean_sprites(L, n=8, seed=0):
    tones = [(118, 72, 42), (100, 60, 36), (86, 52, 32), (124, 78, 46)]
    out = []
    for k in range(n):
        im = render_bean(L * (0.92 + 0.16 * ((k * 37) % 10) / 10), seed + k, 0.66 + 0.08 * ((k * 13) % 5) / 5,
                         tones[k % len(tones)])
        out.append(Sprite(im, blur=max(2, L // 14)))
    return out


# ---------------------------------------------------------------- googly eyes (drawn per state, cached)
_eye_cache = {}


def eye_sprite(r, lx=0.0, ly=0.0, mode='open'):
    key = (r, round(lx, 1), round(ly, 1), mode)
    if key in _eye_cache:
        return _eye_cache[key]
    s = SS(2 * r + 4, 2 * r + 4, ss=4, pad=3)
    cx = cy = r + 2
    if mode == 'happy':
        s.arc((cx - r * 0.8, cy - r * 0.3, cx + r * 0.8, cy + r * 1.1), 200, 340, C['esp'], max(3, r * 0.32))
    elif mode == 'closed':
        s.line([(cx - r * 0.8, cy + 2), (cx + r * 0.8, cy + 2)], C['esp'], max(3, r * 0.28))
    else:
        s.circle(cx, cy, r, fill=C['white'], outline=C['esp'], width=max(2, r * 0.12))
        pr = r * (0.52 if mode == 'open' else 0.34)
        m = r - pr - r * 0.14
        px, py = cx + lx * m, cy + ly * m
        s.circle(px, py, pr, fill=C['esp'])
        s.circle(px - pr * 0.35, py - pr * 0.35, pr * 0.28, fill=C['white'])
    spr = Sprite(s.result(), blur=2)
    _eye_cache[key] = spr
    return spr


def draw_eyes(canvas, host, ox, oy, sep, r, look=(0, 0), mode='open', scale=1.0):
    """host = (x, y, rot, scale, sx, sy) pose of the object carrying the eyes."""
    x, y, rot, hs, sx, sy = host
    for side in (-1, 1):
        ex, ey = local_to_world(x, y, rot, hs, ox + side * sep / 2, oy, sx, sy)
        place(canvas, eye_sprite(r, look[0], look[1], mode), ex, ey, rot=rot, scale=hs * scale, shadow=0.35)


# ---------------------------------------------------------------- mug (the hero character)
def make_mug():
    w, h = 330, 300
    s = SS(w, h, pad=12)
    # handle (behind body)
    s.ellipse((196, 110, 318, 238), fill=C['terra_d'])
    s.ellipse((226, 140, 288, 208), fill=(0, 0, 0, 0))
    # punch hole in the handle
    s.d.ellipse(s.box((226, 140, 288, 208)), fill=(0, 0, 0, 0))
    s.rrect((20, 44, 250, 292), 46, fill=C['terra'])
    # band
    s.rect((20, 196, 250, 228), fill=C['paper'])
    for k in range(6):
        s.circle(46 + k * 36, 212, 6, fill=C['terra_d'])
    # rim + coffee
    s.ellipse((16, 26, 254, 78), fill=C['terra_d'])
    s.ellipse((30, 34, 240, 70), fill=C['esp'])
    s.ellipse((52, 40, 218, 64), fill=(122, 74, 42))
    s.ellipse((72, 44, 198, 60), fill=(92, 56, 34))
    # soft highlight strip on the body
    s.rrect((40, 90, 58, 180), 9, fill=(236, 140, 104))
    return make_sprite(s.result(), border=8, seed=21)


def make_steam(phase):
    w, h = 220, 200
    s = SS(w, h, pad=10)
    for k, x0 in enumerate((50, 110, 170)):
        pts = []
        for j in range(24):
            t = j / 23
            y = h - t * (h - 20 - 30 * (k % 2))
            x = x0 + 16 * math.sin(t * 5.2 + phase * 2.1 + k * 1.3)
            pts.append((x, y))
        s.line(pts, (253, 250, 244, 230), 13)
    return make_sprite(s.result(), border=0, seed=40 + int(phase * 10), blur=5)


# ---------------------------------------------------------------- espresso machine
def make_machine():
    w, h = 500, 600
    s = SS(w, h, pad=12)
    # little cups on top tray
    for cx in (140, 250, 360):
        s.rrect((cx - 34, -30, cx + 34, 8), 10, fill=C['paper'])
    s.rrect((30, 0, 470, 40), 10, fill=C['kraft_d'])
    s.rrect((20, 34, 480, 572), 34, fill=C['esp'])
    s.rrect((56, 70, 444, 232), 22, fill=C['brown'])
    # gauge
    s.circle(378, 150, 44, fill=C['paper'], outline=C['kraft_d'], width=6)
    for a in range(200, 341, 28):
        t = math.radians(a)
        s.line([(378 + 30 * math.cos(t), 150 + 30 * math.sin(t)), (378 + 38 * math.cos(t), 150 + 38 * math.sin(t))],
               C['esp'], 4)
    s.line([(378, 150), (378 + 28 * math.cos(math.radians(300)), 150 + 28 * math.sin(math.radians(300)))],
           C['terra'], 6)
    s.circle(378, 150, 7, fill=C['esp'])
    # group head + portafilter
    s.rrect((196, 244, 304, 296), 10, fill=C['kraft_l'])
    s.rrect((176, 292, 324, 330), 12, fill=C['kraft'])
    s.rrect((24, 298, 190, 324), 12, fill=C['mustard'])
    # espresso cup
    s.rrect((212, 420, 288, 492), 14, fill=C['paper'])
    s.ellipse((276, 436, 312, 474), outline=C['paper'], width=9)
    s.line([(250, 332), (250, 418)], (92, 56, 34), 8, round_caps=False)
    # drip tray + feet
    s.rrect((70, 494, 430, 534), 10, fill=C['kraft_d'])
    for k in range(9):
        s.line([(96 + k * 38, 504), (96 + k * 38, 524)], C['brown'], 4, round_caps=False)
    s.rrect((64, 568, 130, 596), 8, fill=C['esp'])
    s.rrect((370, 568, 436, 596), 8, fill=C['esp'])
    return make_sprite(s.result(), border=8, seed=31)


def make_strip(w, h, color, seed):
    """Rough torn paper strip (used for the big X)."""
    s = SS(w, h, pad=8)
    r = rnd('strip', seed)
    pts = [(0, r.uniform(0, 8)), (w, r.uniform(0, 8)), (w - r.uniform(0, 10), h), (r.uniform(0, 10), h)]
    s.poly(pts, fill=color)
    return make_sprite(s.result(), border=3, border_color=color, seed=seed, rough=1.2)


# ---------------------------------------------------------------- magnifier, sparkles, stars
def make_magnifier():
    w, h = 280, 460
    s = SS(w, h, pad=12)
    s.rrect((118, 250, 162, 452), 20, fill=C['brown'])
    s.rrect((114, 300, 166, 330), 8, fill=C['mustard'])
    s.circle(140, 130, 128, fill=(250, 244, 232, 70))
    s.circle(140, 130, 128, outline=C['esp'], width=24)
    s.arc((50, 40, 230, 220), 200, 260, (255, 255, 255, 220), 12)
    return make_sprite(s.result(), border=7, seed=51)


def star_points(cx, cy, R, r, n=5, rot=-90):
    pts = []
    for k in range(2 * n):
        rad = R if k % 2 == 0 else r
        t = math.radians(rot + k * 180 / n)
        pts.append((cx + rad * math.cos(t), cy + rad * math.sin(t)))
    return pts


def make_star(R=62, color=C['mustard']):
    s = SS(2 * R, 2 * R, pad=8)
    s.poly(star_points(R, R, R, R * 0.48), fill=color)
    s.poly(star_points(R, R, R * 0.55, R * 0.26), fill=(246, 198, 104))
    return make_sprite(s.result(), border=7, seed=61 + R)


def make_sparkle(R=34, color=C['mustard']):
    s = SS(2 * R, 2 * R, pad=6)
    s.poly(star_points(R, R, R, R * 0.22, n=4, rot=-90), fill=color)
    return make_sprite(s.result(), border=4, seed=71 + R, blur=4)


def make_burst(R=250, color=C['mustard']):
    s = SS(2 * R, 2 * R, pad=10)
    for k in range(8):
        t = math.radians(k * 45 + 22)
        s.line([(R + (R - 90) * math.cos(t), R + (R - 90) * math.sin(t)),
                (R + (R - 20) * math.cos(t), R + (R - 20) * math.sin(t))], color, 16)
    return make_sprite(s.result(), border=5, seed=81, blur=4)


# ---------------------------------------------------------------- coffee bag
def bag_shape(w, h):
    top = h * 0.085
    pts = [(w * 0.04, top)]
    teeth = 12
    for k in range(teeth + 1):
        x = w * 0.04 + (w * 0.92) * k / teeth
        pts.append((x, top - (h * 0.022 if k % 2 else 0)))
    pts += [(w * 0.96, top), (w * 0.99, h * 0.55), (w * 0.975, h * 0.96), (w * 0.5, h * 1.0),
            (w * 0.025, h * 0.96), (w * 0.01, h * 0.55)]
    return pts


def make_bag(w, h, label_color, seed, klova=False):
    s = SS(w, h, pad=12)
    s.poly(bag_shape(w, h), fill=C['kraft'])
    # side folds
    s.poly([(w * 0.01, h * 0.55), (w * 0.04, h * 0.085), (w * 0.12, h * 0.085), (w * 0.10, h * 0.97), (w * 0.025, h * 0.96)],
           fill=(176, 131, 90))
    s.poly([(w * 0.99, h * 0.55), (w * 0.96, h * 0.085), (w * 0.90, h * 0.085), (w * 0.91, h * 0.97), (w * 0.975, h * 0.96)],
           fill=(186, 141, 98))
    # crimp seal
    s.rect((w * 0.04, h * 0.085, w * 0.96, h * 0.15), fill=C['kraft_d'])
    for k in range(22):
        x = w * 0.06 + k * (w * 0.88 / 21)
        s.line([(x, h * 0.095), (x, h * 0.14)], C['kraft'], 2, round_caps=False)
    if klova:
        s.rrect((w * 0.13, h * 0.36, w * 0.87, h * 0.88), 18, fill=C['esp'])
        s.text((w * 0.5, h * 0.575), 'كلوفا', h * 0.2, C['mustard'])
        s.line([(w * 0.25, h * 0.7), (w * 0.75, h * 0.7)], C['mustard'], 3)
        s.text((w * 0.5, h * 0.775), 'محاصيل قهوة مختصة', h * 0.052, C['paper'])
    else:
        s.rrect((w * 0.15, h * 0.34, w * 0.85, h * 0.88), 14, fill=C['paper'])
        s.rect((w * 0.15, h * 0.34 + 14, w * 0.85, h * 0.43), fill=label_color)
        s.rrect((w * 0.15, h * 0.34, w * 0.85, h * 0.43), 14, fill=label_color)
    return make_sprite(s.result(), border=7, seed=seed)


def make_bag_back(w, h):
    """Open-bag inner back wall (drawn behind the beans that jump in)."""
    s = SS(w, h * 0.2, pad=12)
    s.poly([(w * 0.05, h * 0.2), (w * 0.08, h * 0.03), (w * 0.5, 0), (w * 0.92, h * 0.03), (w * 0.95, h * 0.2)],
           fill=C['kraft_d'])
    s.poly([(w * 0.1, h * 0.2), (w * 0.14, h * 0.07), (w * 0.86, h * 0.07), (w * 0.9, h * 0.2)], fill=(92, 62, 40))
    return make_sprite(s.result(), border=6, seed=97)


# ---------------------------------------------------------------- flags (round stickers, palette-matched)
def make_flag(kind, R=48):
    s = SS(2 * R, 2 * R, ss=4, pad=4)
    D = 2 * R
    if kind == 'ethiopia':
        s.rect((0, 0, D, D / 3), fill=(92, 140, 70))
        s.rect((0, D / 3, D, 2 * D / 3), fill=C['mustard'])
        s.rect((0, 2 * D / 3, D, D), fill=C['terra'])
        s.circle(R, R, R * 0.38, fill=C['navy'])
        s.poly(star_points(R, R, R * 0.28, R * 0.11), fill=C['mustard'])
    elif kind == 'colombia':
        s.rect((0, 0, D, D / 2), fill=C['mustard'])
        s.rect((0, D / 2, D, 3 * D / 4), fill=C['navy'])
        s.rect((0, 3 * D / 4, D, D), fill=C['terra'])
    elif kind == 'brazil':
        s.rect((0, 0, D, D), fill=(92, 140, 70))
        s.poly([(R, R * 0.2), (D - R * 0.12, R), (R, D - R * 0.2), (R * 0.12, R)], fill=C['mustard'])
        s.circle(R, R, R * 0.42, fill=C['navy'])
        s.arc((R * 0.35, R * 0.75, R * 1.9, R * 1.9), 200, 330, C['white'], 4)
    im = s.result()
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).ellipse((4, 4, im.width - 5, im.height - 5), fill=255)
    a = np.minimum(np.asarray(im.split()[3]), np.asarray(mask))
    im.putalpha(Image.fromarray(a))
    return make_sprite(im, border=6, seed=hash(kind) % 1000)


def make_label_word(text, size, fg, bg, seed, padx=16, h=None):
    f = ImageFont.truetype(FONT_L, size)
    bb = f.getbbox(text, anchor='ls', direction='rtl', language='ar')
    tw = bb[2] - bb[0]
    h = h or int(size * 1.35)
    w = tw + 2 * padx
    s = SS(w, h, pad=6)
    s.rect((0, 0, w, h), fill=bg)
    s.text((w / 2 - (bb[0] + bb[2]) / 2 + tw / 2 - tw / 2, h * 0.5 + size * 0.2), text, size, fg, anchor='ms')
    return make_sprite(s.result(), border=3, border_color=bg, seed=seed, rough=1.0)


# ---------------------------------------------------------------- flavour bubble
def make_bubble(word, icon, seed):
    size = 46
    f = ImageFont.truetype(FONT_L, size)
    bb = f.getbbox(word, anchor='ls', direction='rtl', language='ar')
    tw = bb[2] - bb[0]
    w = tw + 130
    h = 118
    s = SS(w, h + 26, pad=10)
    s.rrect((0, 0, w, h), 30, fill=C['paper'])
    s.poly([(w * 0.5 - 20, h - 2), (w * 0.5 + 20, h - 2), (w * 0.5 + 4, h + 26)], fill=C['paper'])
    ix, iy = w - 52, h / 2
    if icon == 'berry':
        s.line([(ix, iy - 30), (ix + 10, iy - 40)], C['green_d'], 5)
        s.ellipse((ix + 2, iy - 46, ix + 30, iy - 30), fill=C['green'])
        for (dx, dy, c) in ((-12, -6, C['cherry_d']), (12, -4, C['cherry']), (0, 14, C['cherry'])):
            s.circle(ix + dx, iy + dy, 15, fill=c)
            s.circle(ix + dx - 5, iy + dy - 5, 4, fill=(250, 200, 190))
    elif icon == 'caramel':
        s.poly([(ix, iy - 36), (ix + 22, iy + 2), (ix - 22, iy + 2)], fill=C['mustard_d'])
        s.circle(ix, iy + 10, 24, fill=C['mustard_d'])
        s.circle(ix - 8, iy + 2, 7, fill=(250, 222, 160))
    elif icon == 'choco':
        s.rrect((ix - 30, iy - 30, ix + 30, iy + 30), 8, fill=C['esp'])
        for k in (-10, 10):
            s.line([(ix + k, iy - 28), (ix + k, iy + 28)], C['brown'], 4, round_caps=False)
            s.line([(ix - 28, iy + k), (ix + 28, iy + k)], C['brown'], 4, round_caps=False)
    s.text((42 + tw / 2, h * 0.5 + size * 0.22), word, size, C['esp'], anchor='ms')
    return make_sprite(s.result(), border=6, seed=seed)


# ---------------------------------------------------------------- takeaway cup, price tag, calendar, coins
def make_takeaway():
    w, h = 290, 450
    s = SS(w, h, pad=12)
    s.poly([(18, 72), (272, 72), (238, 450), (52, 450)], fill=C['white'])
    s.poly([(30, 190), (260, 190), (248, 330), (42, 330)], fill=C['kraft'])
    s.circle(145, 260, 42, fill=C['paper'])
    s.circle(145, 260, 30, outline=C['kraft_d'], width=5)
    s.rrect((4, 40, 286, 82), 14, fill=C['esp'])
    s.poly([(40, 44), (60, 6), (230, 6), (250, 44)], fill=C['brown'])
    s.rrect((170, 12, 214, 24), 6, fill=C['esp'])
    return make_sprite(s.result(), border=8, seed=121)


def make_price_tag():
    w, h = 190, 96
    s = SS(w, h, pad=8)
    s.poly([(0, h / 2), (38, 0), (w, 0), (w, h), (38, h)], fill=C['mustard'])
    s.circle(34, h / 2, 9, fill=(0, 0, 0, 0))
    s.d.ellipse(s.box((25, h / 2 - 9, 43, h / 2 + 9)), fill=(0, 0, 0, 0))
    s.text((118, h * 0.5 + 16), '٢٢ ر.س', 48, C['esp'], anchor='ms')
    return make_sprite(s.result(), border=6, seed=131)


AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'


def ar_num(n):
    return ''.join(AR_DIGITS[int(ch)] for ch in str(n))


def make_calendar(num):
    w, h = 250, 290
    s = SS(w, h, pad=12)
    s.rrect((0, 20, w, h), 18, fill=C['terra_d'])
    s.rrect((0, 20, w, 92), 18, fill=C['terra'])
    s.rect((0, 70, w, 92), fill=C['terra'])
    s.text((w / 2, 72), 'يوم', 40, C['paper'], anchor='ms')
    s.rect((12, 94, w - 12, h - 12), fill=C['paper'])
    s.text((w / 2, 250), ar_num(num), 150, C['esp'], anchor='ms')
    for x in (62, 188):
        s.rrect((x - 9, 0, x + 9, 44), 8, fill=C['esp'])
    return make_sprite(s.result(), border=7, seed=141)


def make_page(num):
    w, h = 226, 184
    s = SS(w, h, pad=6)
    s.rect((0, 0, w, h), fill=C['paper'])
    s.text((w / 2, 156), ar_num(num), 150, C['esp'], anchor='ms')
    return make_sprite(s.result(), border=4, seed=151 + num)


def make_coin():
    w, h = 150, 34
    s = SS(w, h, pad=6)
    s.rrect((0, 0, w, h), 16, fill=C['mustard_d'])
    s.rrect((0, 0, w, h - 8), 14, fill=C['mustard'])
    for k in range(13):
        x = 12 + k * 10.5
        s.line([(x, h - 7), (x, h - 2)], (160, 110, 36), 2, round_caps=False)
    s.rrect((18, 6, w - 18, 12), 3, fill=(248, 212, 130))
    return make_sprite(s.result(), border=3, seed=161, blur=4)


# ---------------------------------------------------------------- awning, cherries, chain, arrow
def make_awning():
    w, h = 940, 190
    s = SS(w, h, pad=12)
    n = 10
    sw = w / n
    s.rrect((-6, 0, w + 6, 34), 10, fill=C['esp'])
    for k in range(n):
        col = C['terra'] if k % 2 == 0 else C['paper']
        s.rect((k * sw, 32, (k + 1) * sw, 130), fill=col)
        s.ellipse((k * sw, 130 - sw / 2, (k + 1) * sw, 130 + sw / 2), fill=col)
    return make_sprite(s.result(), border=8, seed=171)


def make_branch(seed=0):
    w, h = 400, 280
    s = SS(w, h, pad=14)
    r = rnd('branch', seed)
    stem = [(10 + t * 380, 150 - 40 * math.sin(t * 2.6) + 10 * t) for t in np.linspace(0, 1, 20)]
    s.line(stem, C['brown'], 12)
    leaves = [(0.18, -1, 34), (0.42, 1, -30), (0.66, -1, 28), (0.9, 1, -20)]
    for (t, side, ang) in leaves:
        i = int(t * 19)
        bx, by = stem[i]
        L = 120
        a = math.radians(-90 * side + ang)
        tip = (bx + L * math.cos(a), by + L * math.sin(a))
        mid = ((bx + tip[0]) / 2, (by + tip[1]) / 2)
        nx, ny = -math.sin(a), math.cos(a)
        wdt = 34
        pts = [(bx, by)]
        for k in range(1, 12):
            u = k / 12
            px = bx + (tip[0] - bx) * u
            py = by + (tip[1] - by) * u
            off = wdt * math.sin(math.pi * u)
            pts.append((px + nx * off, py + ny * off))
        pts.append(tip)
        for k in range(11, 0, -1):
            u = k / 12
            px = bx + (tip[0] - bx) * u
            py = by + (tip[1] - by) * u
            off = wdt * math.sin(math.pi * u)
            pts.append((px - nx * off, py - ny * off))
        s.poly(pts, fill=C['green'] if side > 0 else C['green_d'])
        s.line([(bx, by), tip], (150, 172, 110), 3)
    for t in (0.1, 0.3, 0.55, 0.78):
        i = int(t * 19)
        bx, by = stem[i]
        for (dx, dy) in ((-16, 14), (14, 18), (0, -10)):
            c = C['cherry'] if r.random() > 0.3 else C['cherry_d']
            s.circle(bx + dx, by + dy, 17, fill=c)
            s.circle(bx + dx - 6, by + dy - 6, 5, fill=(248, 196, 186))
    return make_sprite(s.result(), border=7, seed=181 + seed)


def make_cherry():
    s = SS(56, 56, pad=6)
    s.circle(28, 28, 26, fill=C['cherry'])
    s.circle(18, 18, 7, fill=(248, 196, 186))
    s.circle(28, 28, 26, outline=C['cherry_d'], width=3)
    return make_sprite(s.result(), border=4, seed=191, blur=4)


def make_chain_sticker():
    R = 66
    s = SS(2 * R, 2 * R, pad=8)
    s.circle(R, R, R, fill=C['mustard'])
    im = s.result()
    link = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(link)
    d.rounded_rectangle((70, 150, 230, 250), radius=50, outline=rgba(C['esp']), width=26)
    d.rounded_rectangle((170, 150, 330, 250), radius=50, outline=rgba(C['esp']), width=26)
    link = link.rotate(35, resample=Image.BICUBIC).resize((100, 100), Image.LANCZOS)
    im.alpha_composite(link, (im.width // 2 - 50, im.height // 2 - 50))
    return make_sprite(im, border=6, seed=201)


def make_arrow():
    w, h = 130, 190
    s = SS(w, h, pad=8)
    s.poly([(w / 2, 0), (w, 80), (w * 0.68, 80), (w * 0.68, h), (w * 0.32, h), (w * 0.32, 80), (0, 80)],
           fill=C['terra'])
    return make_sprite(s.result(), border=7, seed=211)


# ---------------------------------------------------------------- transition sheet (torn kraft paper with stamp)
def make_sheet():
    w, h = W + 220, H + 80
    s = SS(w, h, ss=1, pad=40)
    r = rnd('sheet')
    L, R = [], []
    for k in range(60):
        y = h * k / 59
        L.append((r.uniform(0, 26) + 10 * math.sin(k * 1.7), y))
        R.append((w - r.uniform(0, 26) - 10 * math.sin(k * 1.3), y))
    rim = [(x - 8, y) for x, y in L] + [(x + 8, y) for x, y in reversed(R)]
    s.poly(rim, fill=C['kraft_l'])
    s.poly(L + list(reversed(R)), fill=C['kraft'])
    cx, cy = w / 2, h / 2
    s.circle(cx, cy, 230, outline=C['esp'], width=14)
    s.circle(cx, cy, 200, outline=C['esp'], width=5)
    s.text((cx, cy + 58), 'كلوفا', 170, C['esp'], anchor='ms')
    im = s.result()
    im = texturize(im, 0.06, 0.018, 222)
    return Sprite(im, blur=14)


# ---------------------------------------------------------------- caption word strips
def make_word(word, style, seed):
    size = 86
    f = ImageFont.truetype(FONT_L, size)
    bb = f.getbbox(word, anchor='ls', direction='rtl', language='ar')
    tw = bb[2] - bb[0]
    padx, h = 26, 126
    w = tw + 2 * padx
    bg, fg = {'n': (C['paper'], C['esp']), 'hl': (C['terra'], C['paper']),
              'brand': (C['esp'], C['mustard'])}[style]
    s = SS(w, h, pad=8)
    r = rnd('word', seed)
    q = [(r.uniform(-3, 4), r.uniform(-3, 4)), (w + r.uniform(-4, 3), r.uniform(-3, 4)),
         (w + r.uniform(-4, 3), h + r.uniform(-4, 3)), (r.uniform(-3, 4), h + r.uniform(-4, 3))]
    s.poly(q, fill=bg)
    s.text((padx - bb[0], 76), word, size, fg, anchor='ls')
    return make_sprite(s.result(), border=2, border_color=bg, seed=seed, rough=1.3, blur=6)
