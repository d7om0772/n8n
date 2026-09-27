# -*- coding: utf-8 -*-
"""KLOVA stop-motion collage — 12 images per second, 1080x1920, synced to the voice-over SRT."""
import json, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
from lib import *
from assets import *

DUR = 20.8
N = int(math.ceil(DUR * FPS))  # 250 images
OUT = os.path.join(ROOT, 'frames')
os.makedirs(OUT, exist_ok=True)


def F(t):
    return int(math.floor(t * FPS + 1e-6))


# =============================================================== assets
T0 = time.time()
BG = make_background()
BEANS = bean_sprites(36, 10, seed=500)
HERO = Sprite(render_bean(420, 77, 0.68, (110, 66, 38)), blur=14)
MUG = make_mug()
STEAM = [make_steam(p) for p in (0.0, 1.0, 2.0)]
MACHINE = make_machine()
XS1 = make_strip(640, 82, C['terra'], 1)
XS2 = make_strip(600, 82, C['terra'], 2)
XS3 = make_strip(520, 74, C['terra'], 3)
XS4 = make_strip(500, 74, C['terra'], 4)
MAG = make_magnifier()
STAR = make_star(62)
SPARK = make_sparkle(34)
SPARK_S = make_sparkle(24)
BURST = make_burst(250)
BAGS = {
    'R': make_bag(240, 350, C['green'], 301),
    'M': make_bag(240, 350, C['mustard'], 302),
    'L': make_bag(240, 350, C['terra'], 303),
}
FLAGS = {'R': make_flag('ethiopia'), 'M': make_flag('colombia'), 'L': make_flag('brazil')}
NAMES = {'R': 'إثيوبيا', 'M': 'كولومبيا', 'L': 'البرازيل'}
BUBBLES = {'R': make_bubble('توتي', 'berry', 5), 'M': make_bubble('كراميل', 'caramel', 6),
           'L': make_bubble('شوكولاتة', 'choco', 7)}
TAKEAWAY = make_takeaway()
PRICE = make_price_tag()
CALS = {n: make_calendar(n) for n in range(1, 10)}
PAGES = {n: make_page(n) for n in range(1, 10)}
COIN = make_coin()
AWNING = make_awning()
BRANCH_L = make_branch(0)
BRANCH_R = Sprite(ImageOps.mirror(make_branch(1).im), blur=7)
CHAIN = make_chain_sticker()
ARROW = make_arrow()
SHEET = make_sheet()


def make_name_tag(text, seed):
    size = 36
    f = ImageFont.truetype(FONT_L, size)
    bb = f.getbbox(text, anchor='ls', direction='rtl', language='ar')
    tw = bb[2] - bb[0]
    w, h = tw + 28, 52
    s = SS(w, h, pad=6)
    s.rect((0, 0, w, h), fill=C['esp'])
    s.text((14 - bb[0], 36), text, size, C['paper'], anchor='ls')
    return make_sprite(s.result(), border=2, border_color=C['esp'], seed=seed, rough=1.2, blur=4)


NAME_TAGS = {k: make_name_tag(v, 610 + i) for i, (k, v) in enumerate(NAMES.items())}

# big KLOVA bag with an open top (for the final scene)
GW, GH = 440, 620


def make_open_bag():
    w, h = GW, GH
    s = SS(w, h, pad=12)
    top = h * 0.08
    s.poly([(w * 0.04, top), (w * 0.96, top), (w * 0.99, h * 0.55), (w * 0.975, h * 0.96), (w * 0.5, h),
            (w * 0.025, h * 0.96), (w * 0.01, h * 0.55)], fill=C['kraft'])
    s.poly([(w * 0.01, h * 0.55), (w * 0.04, top), (w * 0.12, top), (w * 0.10, h * 0.97), (w * 0.025, h * 0.96)],
           fill=(176, 131, 90))
    s.poly([(w * 0.99, h * 0.55), (w * 0.96, top), (w * 0.90, top), (w * 0.91, h * 0.97), (w * 0.975, h * 0.96)],
           fill=(186, 141, 98))
    s.line([(w * 0.06, top + 3), (w * 0.94, top + 3)], C['kraft_l'], 5, round_caps=False)
    s.rrect((w * 0.13, h * 0.36, w * 0.87, h * 0.88), 18, fill=C['esp'])
    s.text((w * 0.5, h * 0.575), 'كلوفا', h * 0.2, C['mustard'])
    s.line([(w * 0.25, h * 0.7), (w * 0.75, h * 0.7)], C['mustard'], 3)
    s.text((w * 0.5, h * 0.775), 'محاصيل قهوة مختصة', h * 0.052, C['paper'])
    return make_sprite(s.result(), border=8, seed=701)


def make_open_bag_back():
    w, h = GW, GH * 0.12
    s = SS(w, h, pad=12)
    s.poly([(w * 0.04, h), (w * 0.07, h * 0.08), (w * 0.93, h * 0.08), (w * 0.96, h)], fill=C['kraft_d'])
    s.poly([(w * 0.09, h), (w * 0.12, h * 0.36), (w * 0.88, h * 0.36), (w * 0.91, h)], fill=(70, 44, 28))
    return make_sprite(s.result(), border=6, seed=702)


GBAG = make_open_bag()
GBACK = make_open_bag_back()


# =============================================================== captions (word strips, synced to SRT)
PHR = [
    (0.00, 1.88, [('إذا', 0.00, 'n'), ('تسوي', 0.44, 'n'), ('قهوتك', 0.78, 'hl'), ('في', 1.20, 'n'), ('البيت؟', 1.30, 'hl')]),
    (1.88, 3.24, [('هذا', 1.88, 'n'), ('الفيديو', 2.18, 'n'), ('لك', 2.68, 'hl')]),
    (3.32, 4.36, [('حنا', 3.32, 'n'), ('كلوفا', 3.66, 'brand')]),
    (4.36, 6.10, [('متجر', 4.36, 'n'), ('متخصص', 4.66, 'n'), ('في', 5.14, 'n'), ('محاصيل', 5.26, 'hl'), ('القهوة', 5.62, 'hl')]),
    (6.32, 8.42, [('والفرق', 6.32, 'n'), ('غالباً', 6.80, 'n'), ('مو', 7.36, 'hl'), ('في', 7.54, 'n'), ('المكينة', 7.66, 'n')]),
    (8.42, 10.44, [('الفرق', 8.42, 'n'), ('في', 8.92, 'n'), ('المحصول', 9.08, 'hl'), ('نفسه', 9.70, 'hl')]),
    (10.44, 11.80, [('عشان', 10.44, 'n'), ('كذا', 10.66, 'n'), ('نوفر', 10.82, 'n'), ('لك', 11.20, 'n'), ('محاصيل', 11.34, 'hl')]),
    (11.80, 13.18, [('من', 11.80, 'n'), ('أكثر', 12.02, 'n'), ('من', 12.46, 'n'), ('بلد', 12.60, 'hl')]),
    (13.18, 14.58, [('كل', 13.18, 'n'), ('واحد', 13.40, 'n'), ('له', 13.76, 'n'), ('طعمه', 13.96, 'hl')]),
    (14.60, 16.66, [('بدون', 14.60, 'n'), ('ما', 14.90, 'n'), ('تدفع', 15.00, 'hl'), ('كل', 15.36, 'n'), ('يوم', 15.60, 'n'),
                    ('في', 15.86, 'n'), ('الكوفيّات', 15.98, 'hl')]),
    (16.78, 18.66, [('وبدون', 16.78, 'n'), ('ما', 17.22, 'n'), ('تتنازل', 17.34, 'n'), ('عن', 18.02, 'n'), ('الطعم', 18.18, 'hl')]),
    (18.80, 99.0, [('اختار', 18.80, 'n'), ('محصولك', 19.08, 'hl'), ('من', 19.52, 'n'), ('الرابط', 19.64, 'n'), ('بالبايو', 20.02, 'hl')]),
]


def word_width(word):
    f = ImageFont.truetype(FONT_L, 86)
    bb = f.getbbox(word, anchor='ls', direction='rtl', language='ar')
    return bb[2] - bb[0] + 52


CAP = []  # per phrase: list of dict(spr, x, y, rot, f)
for pi, (ts, te, words) in enumerate(PHR):
    items = []
    for wi, (wd, tw, st) in enumerate(words):
        items.append(dict(word=wd, spr=make_word(wd, st, 1000 + pi * 20 + wi), w=word_width(wd), f=F(tw), st=st))
    # RTL line wrap
    lines, cur, cw = [], [], 0
    GAP, MAXW = 6, 930
    for it in items:
        need = it['w'] + (GAP if cur else 0)
        if cur and cw + need > MAXW:
            lines.append(cur)
            cur, cw = [], 0
            need = it['w']
        cur.append(it)
        cw += need
    lines.append(cur)
    y0 = 372 if len(lines) <= 2 else 330
    for li, ln in enumerate(lines):
        tot = sum(it['w'] for it in ln) + GAP * (len(ln) - 1)
        xr = 540 + tot / 2
        for it in ln:
            r = rnd('cap', pi, it['word'], it['f'])
            it['x'] = xr - it['w'] / 2 + r.uniform(-4, 4)
            it['y'] = y0 + li * 128 + r.uniform(-7, 7)
            it['rot'] = r.uniform(-3.2, 3.2)
            xr -= it['w'] + GAP
    CAP.append((F(ts), F(te), items))


def draw_captions(cv, i, ev):
    for (fs, fe, items) in CAP:
        if not (fs <= i < fe):
            continue
        for it in items:
            k = i - it['f']
            if k < 0:
                continue
            if k == 0:
                if it['st'] == 'n':
                    ev.append((i, 'tick', 0.55, 1.0 + 0.1 * ((it['f'] * 7) % 5)))
                else:
                    ev.append((i, 'pop', 0.75, 1.0 + 0.08 * ((it['f'] * 3) % 4)))
            place(cv, it['spr'], it['x'], it['y'] - 10 * pop_lift(k), rot=it['rot'] + (4 if k == 0 else 0),
                  scale=pop_scale(k), lift=pop_lift(k))


# =============================================================== beans: house (scene A) -> brand word (scene B)
def house_targets():
    segs = [((250, 1000), (540, 700)), ((540, 700), (830, 1000)), ((295, 1000), (295, 1400)),
            ((295, 1400), (785, 1400)), ((785, 1400), (785, 1000))]
    pts = []
    for (a, b) in segs:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(round(L / 40)))
        ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
        for k in range(n):
            t = k / n
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, ang))
    pts.append((785, 1000, 90))
    return pts


def word_targets():
    size = 470
    f = ImageFont.truetype(FONT_L, size)
    im = Image.new('L', (1400, 900), 0)
    d = ImageDraw.Draw(im)
    d.text((700, 450), 'كلوفا', font=f, fill=255, anchor='mm', direction='rtl', language='ar')
    bb = im.getbbox()
    m = np.asarray(im) > 128
    m = ndimage.binary_erosion(m, iterations=9)
    pts = []
    r = np.random.default_rng(9)
    sp = 26
    for row, y in enumerate(np.arange(bb[1], bb[3], sp * 0.866)):
        off = (sp / 2) if row % 2 else 0
        for x in np.arange(bb[0] + off, bb[2], sp):
            xi, yi = int(x), int(y)
            if 0 <= yi < m.shape[0] and 0 <= xi < m.shape[1] and m[yi, xi]:
                pts.append((x + r.uniform(-3, 3), y + r.uniform(-3, 3), r.uniform(0, 180)))
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    return [(540 + (x - cx), 1085 + (y - cy), a) for (x, y, a) in pts], (bb[2] - bb[0], bb[3] - bb[1])


HOUSE = house_targets()
WORD, WORD_SIZE = word_targets()
NB = max(len(WORD), len(HOUSE))
NH = len(HOUSE)
_r = np.random.default_rng(3)
# scene A: house beans start scattered on the table
A_START = []
for j in range(NH):
    while True:
        x, y = _r.uniform(70, 1010), _r.uniform(640, 1720)
        if not (380 < x < 700 and 1080 < y < 1390):
            break
    A_START.append((x, y, _r.uniform(0, 360)))
A_DELAY = _r.uniform(0, 0.28, NH)
A_ARC = _r.uniform(-50, 50, NH)
# scene B: assign house beans to nearest word targets, the rest fly in from the sides
cost = np.array([[math.hypot(hx - wx, hy - wy) for (wx, wy, _) in WORD] for (hx, hy, _) in HOUSE])
rows, cols = linear_sum_assignment(cost)
B_TARGET = [None] * NB
B_FROM = [None] * NB
for hj, wj in zip(rows, cols):
    B_TARGET[hj] = WORD[wj]
    B_FROM[hj] = HOUSE[hj]
rest = [wj for wj in range(len(WORD)) if wj not in set(cols)]
for k, wj in enumerate(rest):
    j = NH + k
    wx, wy, wa = WORD[wj]
    side = -1 if wx < 540 else 1
    B_TARGET[j] = WORD[wj]
    B_FROM[j] = (540 + side * _r.uniform(640, 900), wy + _r.uniform(-420, 420), _r.uniform(0, 360))
B_DELAY = _r.uniform(0, 0.3, NB)
B_ARC = _r.uniform(-70, 70, NB)
B_KIND = [j % len(BEANS) for j in range(NB)]


def bean_pose(j, t, i):
    lift = 0.0
    if j < NH and t < 3.32:
        sx, sy, sa = A_START[j]
        ex, ey, ea = HOUSE[j]
        ea = ea + (180 if (j % 2) else 0) + ((j * 37) % 17 - 8)
        p = ease_io((t - A_DELAY[j]) / 0.58)
        x, y = lerp(sx, ex, p), lerp(sy, ey, p)
        dx, dy = ex - sx, ey - sy
        L = math.hypot(dx, dy) + 1e-6
        x += -dy / L * A_ARC[j] * math.sin(math.pi * p)
        y += dx / L * A_ARC[j] * math.sin(math.pi * p)
        a = lerp(sa, ea, p)
        lift = 0.8 * math.sin(math.pi * p)
        # the "wave hop" on "هذا الفيديو لك"
        for fh in (F(1.88), F(2.68)):
            k = i - (fh + int((1080 - ex) / 300))
            if k == 0:
                y -= 24
                lift = 0.8
            elif k == 1:
                y -= 7
                lift = 0.25
        return x, y, a, lift, True
    if t < 3.32:
        return None
    sx, sy, sa = B_FROM[j]
    ex, ey, ea = B_TARGET[j]
    if j < NH:
        sa = sa + (180 if (j % 2) else 0) + ((j * 37) % 17 - 8)
    p = ease_io((t - 3.32 - B_DELAY[j]) / 0.62)
    x, y = lerp(sx, ex, p), lerp(sy, ey, p)
    dx, dy = ex - sx, ey - sy
    L = math.hypot(dx, dy) + 1e-6
    x += -dy / L * B_ARC[j] * math.sin(math.pi * p)
    y += dx / L * B_ARC[j] * math.sin(math.pi * p)
    a = lerp(sa, ea + 360 * (1 if j % 3 == 0 else 0), p)
    lift = 0.9 * math.sin(math.pi * p)
    return x, y, a, lift, 0 < p < 1


# =============================================================== scenes
def steam(cv, x, y, i, scale=1.0):
    place(cv, STEAM[(i // 2) % 3], x, y, scale=scale, shadow=0.3)


def mug_eyes(cv, pose, look, mode='open'):
    draw_eyes(cv, pose, -30, -8, 66, 20, look, mode)


def scene_AB(cv, i, t, ev):
    # ---- beans
    moving_any = False
    for j in range(NB):
        bp = bean_pose(j, t, i)
        if bp is None:
            continue
        x, y, a, lift, mv = bp
        if -80 < x < 1160 and -80 < y < 2000:
            place(cv, BEANS[B_KIND[j]], x, y, rot=a, lift=lift, key=('bean', j), jitter=1.0 if mv else 0)
        moving_any = moving_any or mv
    if i <= F(0.9) and i % 1 == 0:
        ev.append((i, 'rattle', 0.5, 1.0 + 0.05 * (i % 3)))
    if F(3.32) <= i <= F(4.2):
        ev.append((i, 'rattle', 0.6, 0.9 + 0.05 * (i % 4)))
    if i in (F(1.88), F(2.68)):
        ev.append((i, 'rattle', 0.45, 1.3))
    if i == F(4.25):
        ev.append((i, 'ding', 0.8, 1.0))

    # ---- mug (hero) in scene A
    fm = F(0.78)
    if fm <= i < F(3.24):
        k = i - fm
        mx, my = 540, 1235
        sc = pop_scale(k)
        lift = pop_lift(k)
        sy = 1.0
        for fh in (F(2.18),):
            kh = i - fh
            if kh == 0:
                my -= 46; lift = 1.0; sy = 1.07
            elif kh == 1:
                my -= 12; lift = 0.3; sy = 0.95
        kl = i - F(2.68)
        if 0 <= kl < 3:
            sc *= [1.14, 0.97, 1.0][kl]
        ke = i - F(3.0)
        if ke >= 0:
            my += [50, 300, 800, 1400][min(ke, 3)]
            lift = 0.5
        if k == 0:
            ev.append((i, 'pop', 1.0, 0.85))
        if kl == 0:
            ev.append((i, 'boing', 0.7, 1.0))
            ev.append((i, 'sparkle', 0.55, 1.0))
        if i == F(2.18):
            ev.append((i, 'boing', 0.55, 0.8))
        if ke == 0:
            ev.append((i, 'whoosh', 0.7, 1.0))
        if F(2.68) <= i < F(3.0):
            place(cv, BURST, mx - 10, my - 20, rot=(i - F(2.68)) * 4, scale=[0.8, 1.05, 1.0, 1.0][min(kl, 3)],
                  shadow=0.5)
        if k >= 2 and ke < 1:
            steam(cv, mx - 30, my - 212, i)
        pose = (mx, my, 0, sc, 1.0, sy)
        place(cv, MUG, mx, my, scale=sc, sy=sy, lift=lift, key='mug', jitter=1.0 if (k < 3 or ke >= 0) else 0)
        blink = i in (F(1.55), F(1.55) + 1)
        look = (0, 0) if i < F(1.88) else ((0.0, -0.6) if i < F(2.6) else (0, 0.15))
        mug_eyes(cv, pose, look, 'closed' if blink else 'open')

    # ---- scene B: awning drop = the word becomes a shop sign
    fa = F(4.36)
    if i >= fa:
        k = i - fa
        ys = [470, 690, 742, 735]
        y = ys[min(k, 3)]
        lift = [1.0, 0.45, 0.0, 0.0][min(k, 3)]
        sy = [1.0, 1.0, 0.95, 1.0][min(k, 3)]
        place(cv, AWNING, 540, y, sy=sy, lift=lift, scale=1.04 if k == 0 else 1.0, key='awn', jitter=1 if k < 3 else 0)
        if k == 0:
            ev.append((i, 'whoosh', 0.5, 1.3))
        if k == 2:
            ev.append((i, 'thud', 0.9, 1.0))
    fb = F(5.26)
    if i >= fb:
        k = i - fb
        xs = [-150, 90, 196, 212]
        x = xs[min(k, 3)]
        lift = [0.8, 0.5, 0.1, 0.0][min(k, 3)]
        place(cv, BRANCH_L, x, 1425, rot=-8, lift=lift, key='brL', jitter=1 if k < 3 else 0)
        place(cv, BRANCH_R, 1080 - x, 1440, rot=8, lift=lift, key='brR', jitter=1 if k < 3 else 0)
        if k == 0:
            ev.append((i, 'whoosh', 0.45, 1.5))
        if k == 2:
            ev.append((i, 'pop', 0.8, 0.9))
            ev.append((i, 'pop', 0.6, 1.1))


def scene_C(cv, i, t, ev):
    # ---- espresso machine
    fo = F(8.42)
    mx, my = 540, 1090
    dx = 0
    shake = {F(7.36): 12, F(7.36) + 1: -10, F(7.36) + 2: 8, F(7.36) + 3: -5, F(7.36) + 4: 2}
    dx += shake.get(i, 0)
    ko = i - fo
    if ko >= 0:
        dx += [-140, -470, -1050, -2000][min(ko, 3)]
        if ko == 0:
            ev.append((i, 'whoosh', 0.8, 0.9))
    if ko < 3:
        lift = 0.4 if ko >= 0 else 0
        pose = (mx + dx, my, 0, 1.0, 1.0, 1.0)
        place(cv, MACHINE, mx + dx, my, lift=lift, key='mach', jitter=1 if (i in shake or ko >= 0) else 0)
        worried = i >= F(7.36)
        look = (0.1, 0.8) if worried else ((-0.3, -0.6) if (i // 6) % 2 == 0 else (0.35, -0.5))
        if i in (F(6.9), F(6.9) + 1):
            draw_eyes(cv, pose, -30, -150, 100, 34, (0, 0), 'closed')
        else:
            draw_eyes(cv, pose, -30, -150, 100, 34, look, 'small' if worried else 'open')
        for (fx, spr, rot) in ((F(7.36), XS1, 38), (F(7.36) + 2, XS2, -40)):
            k = i - fx
            if k >= 0:
                place(cv, spr, mx + dx, my - 10, rot=rot + (5 if k == 0 else 0), scale=pop_scale(k), lift=pop_lift(k))
                if k == 0:
                    ev.append((i, 'stamp', 1.0, 1.0 if fx == F(7.36) else 0.9))
    # ---- hero bean: "the difference is the crop itself"
    if ko >= 0:
        kb = ko
        xs = [1450, 1060, 740, 592, 548, 540]
        rots = [34, 20, 4, -8, -14, -15]
        lifts = [0.8, 0.8, 0.6, 0.3, 0.1, 0.0]
        x = xs[min(kb, 5)]
        rot = rots[min(kb, 5)]
        lift = lifts[min(kb, 5)]
        kp = i - F(10.14)
        if kp >= 0:
            x -= [160, 520, 1100, 2000][min(kp, 3)]
            if kp == 0:
                ev.append((i, 'whoosh', 0.7, 1.1))
        if x > -400:
            place(cv, HERO, x, 1090, rot=rot, lift=lift, key='hero', jitter=1 if (kb < 6 or kp >= 0) else 0)
            # hand-drawn marker circle
            fc = F(9.08)
            kc = i - fc
            if kc >= 0:
                frac = [0.2, 0.42, 0.64, 0.86, 1.0, 1.1][min(kc, 5)]
                draw_marker(cv, x, 1090, frac)
                if kc < 5:
                    ev.append((i, 'scribble', 0.55, 1.0 + 0.07 * kc))
            # magnifier
            fg = F(9.62)
            kg = i - fg
            if kg >= 0:
                pos = [(1060, 1700), (900, 1480), (792, 1352), (774, 1330)]
                rr = [-50, -40, -33, -30]
                gx, gy = pos[min(kg, 3)]
                place(cv, MAG, gx + (x - 540), gy, rot=rr[min(kg, 3)], lift=0.6 if kg < 3 else 0, key='mag',
                      jitter=1 if kg < 3 else 0)
                if kg == 0:
                    ev.append((i, 'whoosh', 0.45, 1.6))
                if kg == 3:
                    ev.append((i, 'sparkle', 0.7, 1.0))
                for (fs, sx, sy, spr) in ((fg + 3, 300, 870, SPARK), (fg + 4, 815, 860, SPARK_S),
                                          (fg + 5, 270, 1290, SPARK_S)):
                    ks = i - fs
                    if ks >= 0:
                        place(cv, spr, sx + (x - 540), sy, scale=pop_scale(ks), rot=ks * 7, shadow=0.6)
    if ko == 0:
        ev.append((i, 'boing', 0.4, 1.3))


def draw_marker(cv, cx, cy, frac):
    rx, ry = 292, 214
    n = max(2, int(80 * frac))
    pts = []
    for k in range(n + 1):
        a = math.radians(205 - 360 * frac * k / n)
        w = 1 + 0.04 * math.sin(k * 0.37) + 0.02 * (k / 80)
        pts.append((cx + rx * w * math.cos(a), cy + ry * w * math.sin(a) - 6 * (k / 80)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = min(xs) - 20, min(ys) - 20
    s = SS(max(xs) - x0 + 20, max(ys) - y0 + 20, ss=2, pad=6)
    s.line([(px - x0, py - y0) for px, py in pts], C['terra'], 15)
    spr = Sprite(s.result(), blur=3)
    place(cv, spr, x0 + s.w / 2, y0 + s.h / 2, shadow=0.35)


BAG_CFG = {  # key: (start frame, end x, hops)
    'L': (F(10.44) - 2, 235, 5),
    'M': (F(10.44) + 1, 540, 4),
    'R': (F(10.44) + 4, 845, 3),
}
BAG_Y = 1150
BSC = 1.1


def bag_pose(key, i):
    s0, ex, n = BAG_CFG[key]
    sx = 1260
    if i < s0:
        return None
    k = i - s0
    h, ph = k // 3, k % 3
    if h >= n:
        kl = k - 3 * n
        sy = 0.93 if kl == 0 else (1.02 if kl == 1 else 1.0)
        return (ex, BAG_Y + (6 if kl == 0 else 0), 0, BSC, 1.0 / sy if kl < 2 else 1.0, sy), 0.0, kl == 0, False
    x0 = sx + (ex - sx) * h / n
    x1 = sx + (ex - sx) * (h + 1) / n
    if ph == 0:
        return (x0, BAG_Y + 6, 0, BSC, 1.05, 0.94), 0.0, h > 0, True
    if ph == 1:
        return (lerp(x0, x1, 0.5), BAG_Y - 52, 6, BSC, 0.97, 1.05), 0.95, False, True
    return (lerp(x0, x1, 0.88), BAG_Y - 16, 3, BSC, 1.0, 1.0), 0.35, False, True


def scene_D(cv, i, t, ev):
    for key in ('L', 'M', 'R'):
        r = bag_pose(key, i)
        if r is None:
            continue
        pose, lift, landed, moving = r
        x, y, rot, sc, sx, sy = pose
        place(cv, BAGS[key], x, y, rot=rot, scale=sc, sx=sx, sy=sy, lift=lift, key=('bag', key), jitter=1 if moving else 0)
        if landed:
            ev.append((i, 'tap', 0.75, {'L': 0.9, 'M': 1.0, 'R': 1.12}[key]))
        # eyes
        if moving:
            look, mode = (-0.85, 0.1), 'open'
        else:
            blink_f = {'L': F(12.9), 'M': F(12.4), 'R': F(13.0)}[key]
            if i in (blink_f, blink_f + 1):
                look, mode = (0, 0), 'closed'
            elif i >= F(13.18):
                look, mode = (0.0, -0.8), 'open'
            else:
                look, mode = (0.0, 0.1), 'open'
        draw_eyes(cv, pose, 0, -92, 58, 17, look, mode)
        # flag + origin name sticker
        ff = {'R': F(12.02), 'M': F(12.3), 'L': F(12.6)}[key]
        k = i - ff
        if k >= 0:
            fx, fy = local_to_world(x, y, rot, sc, 0, 22, sx, sy)
            place(cv, FLAGS[key], fx, fy - 8 * pop_lift(k), rot=rot + (key == 'M') * 4 - 3, scale=sc * pop_scale(k),
                  lift=pop_lift(k))
            nx, ny = local_to_world(x, y, rot, sc, 0, 110, sx, sy)
            place(cv, NAME_TAGS[key], nx, ny, rot=rot - 2 + (key == 'L') * 3, scale=sc * pop_scale(k), lift=pop_lift(k),
                  shadow=0.6)
            if k == 0:
                ev.append((i, 'pop', 1.0, {'R': 1.0, 'M': 1.12, 'L': 1.25}[key]))
        # flavour bubble
        fb = {'R': F(13.28), 'M': F(13.6), 'L': F(13.92)}[key]
        kb = i - fb
        if kb >= 0:
            by = {'R': 845, 'M': 795, 'L': 845}[key]
            place(cv, BUBBLES[key], x, by - 10 * pop_lift(kb), rot={'R': 3, 'M': -2, 'L': 2}[key],
                  scale=1.15 * pop_scale(kb), lift=pop_lift(kb))
            if kb == 0:
                ev.append((i, 'bubble', 0.9, {'R': 1.0, 'M': 1.15, 'L': 1.3}[key]))


def scene_E(cv, i, t, ev):
    cx, cy = 360, 1110
    kx = [i - F(16.32), i - F(16.32) - 1]
    lift = 0.0
    place(cv, TAKEAWAY, cx, cy, scale=1.1, key='take', jitter=0)
    # price tag
    kp = i - F(15.0)
    if kp >= 0:
        place(cv, PRICE, 525, 985, rot=-14 + (5 if kp == 0 else 0), scale=pop_scale(kp), lift=pop_lift(kp))
        if kp == 0:
            ev.append((i, 'pop', 0.9, 1.2))
    # calendar + coins: every day you pay again
    flips = [F(15.08) + 2 * n for n in range(7)]
    done = sum(1 for f in flips if i >= f)
    place(cv, CALS[1 + done], 790, 895, scale=1.1)
    for n in range(done):
        f = flips[n]
        kc = i - f
        y = 1325 - n * 24
        if kc == 0:
            place(cv, COIN, 790 + (n % 2) * 4, y - 70, lift=0.8, rot=3)
        else:
            place(cv, COIN, 790 + (n % 2) * 4 - (n % 3), y, rot=(n % 3) - 1, shadow=0.6)
    for n, f in enumerate(flips):
        kf = i - f
        if kf == 0:
            place(cv, PAGES[1 + n], 830, 780, rot=16, lift=1.0)
            ev.append((i, 'flip', 0.7, 1.0 + 0.04 * n))
            ev.append((i + 1, 'clink', 0.55, 1.0 + 0.06 * n))
        elif kf == 1:
            place(cv, PAGES[1 + n], 900, 600, rot=34, scale=0.9, lift=1.0)
    if i == F(15.98):
        ev.append((i, 'chaching', 0.9, 1.0))
    # the big X: no more paying the café every day
    for (k, spr, rot) in ((kx[0], XS3, 40), (kx[1], XS4, -38)):
        if k >= 0:
            place(cv, spr, cx, cy, rot=rot + (5 if k == 0 else 0), scale=pop_scale(k), lift=pop_lift(k))
            if k == 0:
                ev.append((i, 'stamp', 0.95, 1.05))


STAR_POS = [(886, 955), (742, 806), (540, 752), (338, 806), (194, 955)]


def scene_F(cv, i, t, ev):
    mx, my = 540, 1205
    sc = 1.15
    lift, sy = 0.0, 1.0
    kh = i - F(18.17)
    if kh == 0:
        my -= 50; lift = 1.0; sy = 1.07
    elif kh == 1:
        my -= 14; lift = 0.3; sy = 0.95
    if kh == 0:
        ev.append((i, 'boing', 0.7, 1.15))
        ev.append((i, 'sparkle', 0.6, 1.2))
    steam(cv, mx - 30 * sc, my - 212 * sc, i, sc)
    pose = (mx, my, 0, sc, 1.0, sy)
    place(cv, MUG, mx, my, scale=sc, sy=sy, lift=lift, key='mugF', jitter=1 if kh in (0, 1) else 0)
    fst = [F(17.14) + 2 * n for n in range(5)]
    shown = [f for f in fst if i >= f]
    if i >= F(17.9):
        mug_eyes(cv, pose, (0, 0), 'happy')
    else:
        look = (0.0, -0.9)
        if shown:
            n = len(shown) - 1
            sx_, sy_ = STAR_POS[n]
            look = ((sx_ - mx) / 400, -0.9)
        mug_eyes(cv, pose, look, 'open')
    for n, f in enumerate(fst):
        k = i - f
        if k >= 0:
            x, y = STAR_POS[n]
            wig = 0
            if i >= F(18.17) and (i - F(18.17)) < 3:
                wig = [-10, 6, 0][i - F(18.17)]
            place(cv, STAR, x, y + wig, rot=(n - 2) * -8 + (12 if k == 0 else 0), scale=pop_scale(k), lift=pop_lift(k))
            if k == 0:
                ev.append((i, 'pop', 0.95, 0.9 + 0.12 * n))


G_BEANS = []
_rg = np.random.default_rng(21)
for n in range(14):
    side = -1 if n % 2 == 0 else 1
    sx = 540 + side * _rg.uniform(300, 430)
    sy = _rg.uniform(1470, 1600)
    G_BEANS.append(dict(sx=sx, sy=sy, a=_rg.uniform(0, 360), f=F(18.84) + int(n * 1.25),
                        ex=540 + _rg.uniform(-90, 90), kind=n % len(BEANS), spin=_rg.uniform(-300, 300)))
G_PILE = []
for n in range(22):
    side = -1 if n % 2 == 0 else 1
    G_PILE.append((540 + side * _rg.uniform(290, 440), _rg.uniform(1480, 1640), _rg.uniform(0, 360), n % len(BEANS)))


def scene_G(cv, i, t, ev):
    bx, by = 540, 1150
    top = by - GH / 2
    # static bean piles on the table
    for (x, y, a, kd) in G_PILE:
        place(cv, BEANS[kd], x, y, rot=a)
    # back wall of the open bag
    place(cv, GBACK, bx, top + GH * 0.06 + 2, shadow=0.0)
    # beans hopping into the bag
    for n, b in enumerate(G_BEANS):
        k = i - b['f']
        if k < 0:
            place(cv, BEANS[b['kind']], b['sx'], b['sy'], rot=b['a'])
            continue
        if k > 4:
            continue
        p = k / 4
        x = lerp(b['sx'], b['ex'], ease_io(p))
        y = lerp(b['sy'], top + 40, p) - math.sin(math.pi * p) * 330
        place(cv, BEANS[b['kind']], x, y, rot=b['a'] + b['spin'] * p, lift=0.9 * math.sin(math.pi * p) + 0.2,
              key=('gb', n), jitter=1)
        if k == 0:
            ev.append((i, 'hop', 0.5, 0.9 + 0.05 * (n % 5)))
        if k == 4:
            ev.append((i, 'plink', 0.5, 0.9 + 0.06 * (n % 6)))
    place(cv, GBAG, bx, by)
    pose = (bx, by, 0, 1.0, 1.0, 1.0)
    fw = F(20.42)
    if i >= fw and i - fw < 5:
        for side, mode in ((-1, 'open'), (1, 'happy')):
            ex, ey = local_to_world(bx, by, 0, 1.0, side * 48, -160)
            place(cv, eye_sprite(30, 0, 0, mode), ex, ey, shadow=0.35)
        if i == fw:
            ev.append((i, 'ding', 0.8, 1.25))
    else:
        look = (0.0, 0.0)
        if i < F(19.5):
            active = [b for b in G_BEANS if 0 <= i - b['f'] <= 4]
            if active:
                look = (0.0, -0.9)
        else:
            look = (-0.5, -0.8) if i >= F(20.02) else (0.6, -0.5)
        draw_eyes(cv, pose, 0, -160, 96, 30, look, 'open')
    kc = i - F(19.64)
    if kc >= 0:
        place(cv, CHAIN, 758, 872, rot=12 + (8 if kc == 0 else 0), scale=pop_scale(kc), lift=pop_lift(kc))
        if kc == 0:
            ev.append((i, 'pop', 1.0, 1.15))
    ka = i - F(20.02)
    if ka >= 0:
        bounce = -16 if (ka // 2) % 2 == 1 else 0
        place(cv, ARROW, 540, 712 + bounce, scale=0.8 * pop_scale(ka), lift=pop_lift(ka) + (0.3 if bounce else 0),
              rot=6)
        if ka == 0:
            ev.append((i, 'pop', 1.0, 1.3))
        elif ka % 4 == 2:
            ev.append((i, 'tick', 0.35, 1.4))



# =============================================================== transitions (torn kraft sheet slides across)
WIPES = [(F(6.08), 1), (F(14.42), -1), (F(16.58), 1), (F(18.5), -1)]


def draw_wipe(cv, i, ev):
    for (f0, d) in WIPES:
        k = i - f0
        if 0 <= k < 4:
            lefts = [620, -110, -760, -1400]
            L = lefts[k]
            cx = L + (W + 220) / 2
            if d < 0:
                cx = W - cx
            place(cv, SHEET, cx, 960, rot=(1.2 if k % 2 else -0.8) * d, lift=0.5, shadow=1.3)
            if k == 0:
                ev.append((i, 'sheet', 0.8, 1.0))
            if k == 1:
                ev.append((i, 'shutter', 0.7, 1.0))


def scene_for(i):
    if i <= WIPES[0][0] + 1:
        return scene_AB
    if i < F(10.44) - 2:
        return scene_C
    if i <= WIPES[1][0] + 1:
        return scene_CD
    if i <= WIPES[2][0] + 1:
        return scene_E
    if i <= WIPES[3][0] + 1:
        return scene_F
    return scene_G


def scene_CD(cv, i, t, ev):
    if i < F(10.44) + 1:
        scene_C(cv, i, t, ev)
    scene_D(cv, i, t, ev)


def render_frame(i):
    t = i / FPS
    ev = []
    cv = BG.copy()
    scene_for(i)(cv, i, t, ev)
    draw_captions(cv, i, ev)
    draw_wipe(cv, i, ev)
    arr = np.asarray(cv.convert('RGB')).astype(np.float32)
    g = np.random.default_rng(1000 + i).normal(0, 2.4, arr.shape[:2]).astype(np.float32)
    arr += g[..., None]
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(OUT, '%04d.jpg' % i), quality=96, subsampling=0)
    return ev


if __name__ == '__main__':
    print('assets built in %.1fs; beans word=%d house=%d word size=%s' % (time.time() - T0, len(WORD), NH, WORD_SIZE))
    frames = list(range(N))
    if len(sys.argv) > 1:
        frames = [int(a) for a in sys.argv[1].split(',')]
    from multiprocessing import Pool
    t1 = time.time()
    with Pool(4) as pool:
        evs = pool.map(render_frame, frames, chunksize=4)
    allev = sorted([e for es in evs for e in es])
    if len(frames) == N:
        json.dump([[e[0] / FPS, e[1], e[2], e[3]] for e in allev], open(os.path.join(ROOT, 'events.json'), 'w'),
                  ensure_ascii=False, indent=0)
    print('rendered %d frames in %.1fs, %d sfx events' % (len(frames), time.time() - t1, len(allev)))
