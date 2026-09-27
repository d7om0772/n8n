# KLOVA collage motion video — compositor
# usage: python3 render.py preview t1 t2 ...   |   python3 render.py full out.mp4
import sys, os, math, json, subprocess
import numpy as np
from PIL import Image, ImageDraw
from lib import *

W, H, FPS = 1080, 1920, 30
DUR = 20.80
NF = int(round(DUR * FPS))
LEAD = 0.05  # visuals lead the voice slightly

SFX = []      # (time, name, gain, extra)
SHAKES = []   # (time, amp)


def sfx(t, name, gain=1.0, **kw):
    SFX.append((round(t, 3), name, gain, kw))


def shake(t, amp):
    SHAKES.append((t, amp))


# ------------------------------------------------------------------ easing
def c01(x): return max(0.0, min(1.0, x))
def out_cubic(p): return 1 - (1 - p) ** 3
def in_cubic(p): return p ** 3
def out_back(p, s=1.9):
    p -= 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2
def in_out(p): return 0.5 - 0.5 * math.cos(math.pi * p)


def jit(seed, k):
    r = np.random.default_rng(seed * 7919 + k * 104729 + 17)
    return r.uniform(-1, 1, 3)


# ------------------------------------------------------------------ sprite placement (premultiplied)
_pm = {}


def premul(spr):
    k = id(spr)
    if k not in _pm:
        _pm[k] = (spr, spr.convert('RGBa'))
    return _pm[k][1]


_mip = {}


def mip(spr, s):
    """return (image, residual scale) using a pre-shrunk copy when shrinking a lot"""
    if s >= 0.72:
        return premul(spr), s
    q = max(0.05, round(s / 0.05) * 0.05 + 0.05)
    k = (id(spr), q)
    if k not in _mip:
        if len(_mip) > 400:
            _mip.clear()
        im = spr.resize((max(1, int(spr.width * q)), max(1, int(spr.height * q))), Image.LANCZOS)
        _mip[k] = (spr, im.convert('RGBa'))
    return _mip[k][1], s / q


def place(canvas, spr, cx, cy, s=1.0, r=0.0, a=1.0, nocache=False):
    if spr is None or s <= 0.02 or a <= 0.01:
        return
    src, s = (spr.convert('RGBa'), s) if nocache else mip(spr, s)
    w, h = src.size
    rad = math.radians(r)
    co, si = math.cos(rad), math.sin(rad)
    hw, hh = w / 2 * s, h / 2 * s
    cs = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    xs = [cx + dx * co - dy * si for dx, dy in cs]
    ys = [cy + dx * si + dy * co for dx, dy in cs]
    X0, Y0 = max(0, int(math.floor(min(xs)))), max(0, int(math.floor(min(ys))))
    X1, Y1 = min(canvas.width, int(math.ceil(max(xs)))), min(canvas.height, int(math.ceil(max(ys))))
    if X1 <= X0 or Y1 <= Y0:
        return
    A = co / s; B = si / s; C = w / 2 + (co * (X0 - cx) + si * (Y0 - cy)) / s
    D = -si / s; E = co / s; F = h / 2 + (-si * (X0 - cx) + co * (Y0 - cy)) / s
    out = src.transform((X1 - X0, Y1 - Y0), Image.AFFINE, (A, B, C, D, E, F), resample=Image.BICUBIC).convert('RGBA')
    if a < 0.999:
        al = out.getchannel('A').point(lambda v: int(v * a))
        out.putalpha(al)
    canvas.alpha_composite(out, (X0, Y0))


# ------------------------------------------------------------------ elements
DUR_DEF = {'pop': 0.32, 'stamp': 0.15, 'drop': 0.38, 'rise': 0.38, 'left': 0.3, 'right': 0.3, 'fade': 0.2, 'none': 0.01, 'grow': 0.3}
_seed = [0]


class El:
    def __init__(self, spr, x, y, s=1.0, r=0.0, t=0.0, anim='pop', d=None, z=10, boil=1.8, fn=None, a=1.0, spin=-14, reveal=None, until=None, painter=None):
        self.spr, self.x, self.y, self.s, self.r, self.t = spr, x, y, s, r, t
        self.anim, self.d, self.z, self.boil, self.fn, self.a, self.spin = anim, d or DUR_DEF[anim], z, boil, fn, a, spin
        self.reveal, self.until, self.painter = reveal, until, painter
        _seed[0] += 1
        self.seed = _seed[0]

    def draw(self, canvas, t):
        lt = t - self.t
        if lt < 0 or (self.until is not None and t >= self.until):
            return
        if self.painter:
            self.painter(canvas, lt, t)
            return
        x, y, s, r, a = self.x, self.y, self.s, self.r, self.a
        p = c01(lt / self.d)
        an = self.anim
        if an == 'pop':
            s *= max(0.0, out_back(p)); r += (1 - out_cubic(p)) * self.spin
        elif an == 'stamp':
            s *= 1 + 1.3 * (1 - out_cubic(p)) ** 2; a *= c01(p * 3.5)
        elif an == 'drop':
            y -= 1000 * (1 - out_back(p, 1.3)); r += (1 - p) * 9
        elif an == 'rise':
            y += 1400 * (1 - out_back(p, 1.1)); r += (1 - p) * 7
        elif an == 'left':
            x -= 1200 * (1 - out_cubic(p)); r -= (1 - p) * 12
        elif an == 'right':
            x += 1200 * (1 - out_cubic(p)); r += (1 - p) * 12
        elif an == 'fade':
            a *= p
        elif an == 'grow':
            s *= out_cubic(p)
        if self.boil:
            j = jit(self.seed, int(t * 10))
            x += j[0] * self.boil; y += j[1] * self.boil; r += j[2] * self.boil * 0.3
        spr = self.spr(lt) if callable(self.spr) else self.spr
        if self.fn:
            st = {'x': x, 'y': y, 's': s, 'r': r, 'a': a}
            self.fn(lt, st)
            x, y, s, r, a = st['x'], st['y'], st['s'], st['r'], st['a']
        if spr is None:
            return
        if self.reveal:
            q = c01(lt / self.reveal)
            if q < 1:
                cw = max(1, int(spr.width * out_cubic(q)))
                spr2 = spr.crop((spr.width - cw, 0, spr.width, spr.height))  # reveal right→left
                off = (spr.width - cw) / 2 * s
                place(canvas, spr2, x + off * math.cos(math.radians(r)), y + off * math.sin(math.radians(r)), s, r, a)
                return
        place(canvas, spr, x, y, s, r, a)


class Scene:
    def __init__(self, name, t0, bg, trans='cut', td=0.2, zoom=(1.035, 1.09)):
        self.name, self.t0, self.bg, self.trans, self.td, self.zoom = name, t0, bg, trans, td, zoom
        self.els = []
        self.punches = []
        self.t1 = None

    def add(self, *a, **k):
        e = El(*a, **k)
        self.els.append(e)
        return e

    def punch(self, t, amt=0.05):
        self.punches.append((t, amt))

    def render(self, t):
        cv = self.bg.copy()
        for e in sorted(self.els, key=lambda e: e.z):
            e.draw(cv, t)
        lt = t - self.t0
        L = (self.t1 or DUR) - self.t0
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * in_out(c01(lt / L))
        for (pt, amt) in self.punches:
            if t >= pt:
                dt = t - pt
                z += amt * math.exp(-dt * 9) * (1 - math.exp(-dt * 60))
        sx = sy = sr = 0.0
        for (st, amp) in SHAKES:
            if st <= t < st + 0.45:
                dt = t - st
                env = amp * math.exp(-dt * 11)
                j = jit(int(st * 1000), int(t * 30))
                sx += j[0] * env; sy += j[1] * env; sr += j[2] * env * 0.08
        return camera(cv, z, sx, sy, sr)


def camera(cv, z, dx, dy, rot):
    rad = math.radians(rot)
    co, si = math.cos(rad), math.sin(rad)
    cx, cy = W / 2, H / 2
    A = co / z; B = si / z; D = -si / z; E = co / z
    C = cx - A * (cx + dx) - B * (cy + dy)
    F = cy - D * (cx + dx) - E * (cy + dy)
    return cv.transform((W, H), Image.AFFINE, (A, B, C, D, E, F), resample=Image.BILINEAR)


# ------------------------------------------------------------------ building blocks
def words_row(sc, items, y, maxw=930, gap=14, seed=0, z=20, x_center=W / 2):
    """items: (text, t, style, size[, anim]) laid out right-to-left"""
    sprs = []
    for i, it in enumerate(items):
        text, t, style, size = it[:4]
        fn = 'Marhey' if style.endswith('_m') else 'Lalezar'
        st = style[:-2] if style.endswith('_m') else style
        sp = word_sprite(text, st, size, fontname=fn, seed=seed * 10 + i)
        sprs.append((sp, content_size(sp)))
    total = sum(cs[0] for _, cs in sprs) + gap * (len(sprs) - 1)
    k = min(1.0, maxw / total)
    xr = x_center + total * k / 2
    rng = rng_for('row', seed, y)
    out = []
    for (sp, cs), it in zip(sprs, items):
        text, t, style, size = it[:4]
        anim = it[4] if len(it) > 4 else 'pop'
        w = cs[0] * k
        cx = xr - w / 2
        xr -= w + gap * k
        r = rng.uniform(-3.2, 3.2)
        yy = y + rng.uniform(-8, 8)
        e = sc.add(sp, cx, yy, s=k, r=r, t=t - LEAD, anim=anim, z=z, boil=1.4, spin=rng.choice([-12, 12]))
        out.append((e, cx, yy, w, cs[1] * k))
        if anim == 'stamp':
            sfx(t - LEAD, 'stamp_small', 0.7)
            shake(t - LEAD + 0.08, 9)
        else:
            sfx(t - LEAD, 'tick', 0.55)
    return out


_doodle_cache = {}


def doodle_el(sc, kind, x, y, w, h, t, d, color=ESP, width=14, z=25, seed=0, fill=None, hold=None, r=0):
    strokes = doodle(kind, w, h, seed)

    def spr(lt):
        p = c01(lt / d)
        q = round(p * 15 * d) / max(1e-6, 15 * d) if p < 1 else 1.0  # draw-on at 15fps (hand-made feel)
        k = (kind, w, h, seed, round(q, 3), color, width, fill)
        if k not in _doodle_cache:
            if len(_doodle_cache) > 600:
                _doodle_cache.clear()
            _doodle_cache[k] = draw_doodle(strokes, w, h, q, width=width, color=color, fill=fill)
        return _doodle_cache[k]
    return sc.add(spr, x, y, s=1, r=r, t=t, anim='none', z=z, boil=1.2)


def steam_painter(x0, y0, n=3, spread=46, height=210, color=ESP, width=11):
    def paint(cv, lt, t):
        k = int(t * 10)
        grow = c01(lt / 0.4)
        im = Image.new('RGBA', (int(spread * n + 120) * 2, int(height + 60) * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i in range(n):
            ph = k * 0.9 + i * 2.1
            pts = []
            L = height * (0.75 + 0.25 * math.sin(i * 1.7 + k * 0.3)) * grow
            for j in range(26):
                yy = j / 25 * L
                xx = 60 + i * spread + 16 * math.sin(yy * 0.035 + ph) * (0.4 + yy / height)
                pts.append((xx * 2, (height + 30 - yy) * 2))
            if len(pts) > 1:
                d.line(pts, fill=color + (230,), width=width * 2, joint='curve')
                for (px, py) in (pts[0], pts[-1]):
                    d.ellipse((px - width, py - width, px + width, py + width), fill=color + (230,))
        im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        cv.alpha_composite(im, (int(x0 - im.width / 2), int(y0 - im.height)))
    return paint


def bg_sheet(color, seed, dark=False, decor=()):
    im = paper_texture(W, H, color, seed=seed, dark=dark)
    for (spr, x, y, r) in decor:
        place(im, spr, x, y, 1.0, r, 1.0)
    return im


# ------------------------------------------------------------------ transitions
def _torn_edge_mask(axis, seed):
    rng = rng_for('edge', axis, seed)
    m = Image.new('L', (W, H), 255)
    d = ImageDraw.Draw(m)
    J = 26
    if axis == 'top':
        pts = [(0, 0)] + [(x, J / 2 + rng.uniform(-J / 2, J / 2) + 8 * math.sin(x / 90)) for x in range(0, W + 1, 10)] + [(W, 0)]
    else:  # left edge
        pts = [(0, 0)] + [(J / 2 + rng.uniform(-J / 2, J / 2) + 8 * math.sin(y / 90), y) for y in range(0, H + 1, 10)] + [(0, H)]
    d.polygon(pts, fill=0)
    return m


EDGE_TOP = None
EDGE_LEFT = None
TEAR = None


def init_transitions():
    global EDGE_TOP, EDGE_LEFT, TEAR
    EDGE_TOP = _torn_edge_mask('top', 1)
    EDGE_LEFT = _torn_edge_mask('left', 2)
    rng = rng_for('tear', 3)
    lowf = smooth_noise(1, H + 1, 120, rng)[0] * 70
    xs = [W / 2 + lowf[y] + rng.uniform(-9, 9) for y in range(0, H + 1, 8)]
    ys = list(range(0, H + 1, 8))
    left = Image.new('L', (W, H), 0)
    ImageDraw.Draw(left).polygon([(0, 0)] + list(zip(xs, ys)) + [(0, H)], fill=255)
    fiber = Image.new('L', (W, H), 0)
    ImageDraw.Draw(fiber).line(list(zip(xs, ys)), fill=255, width=16)
    TEAR = (left, fiber)


def paste_sheet(base, top, mask, dx, dy, shadow_dir):
    # shadow
    sh = Image.new('RGBA', (W, H), ESP + (0,))
    from PIL import ImageFilter
    sm = mask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55))
    sh.putalpha(sm)
    base.paste(sh, (int(dx + shadow_dir[0]), int(dy + shadow_dir[1])), sh)
    base.paste(top, (int(dx), int(dy)), mask)
    return base


def transition(kind, p, prev, new):
    if kind == 'slide_up':
        e = out_cubic(p)
        return paste_sheet(prev.copy(), new, EDGE_TOP, 0, H * (1 - e), (0, -18))
    if kind == 'slide_left':
        e = out_cubic(p)
        return paste_sheet(prev.copy(), new, EDGE_LEFT, W * (1 - e), 0, (-18, 0))
    if kind == 'slap':
        e = out_cubic(p)
        out = prev.copy()
        s = 1 + 0.22 * (1 - e); r = 5 * (1 - e)
        tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        place(tmp, new, W / 2, H / 2, s, r, c01(p * 2.5), nocache=True)
        out.alpha_composite(tmp)
        return out
    if kind == 'rip':
        e = in_cubic(p) * 0.35 + out_cubic(p) * 0.65
        left, fiber = TEAR
        out = new.copy()
        from PIL import ImageChops
        lmask = left
        rmask = ImageChops.invert(left)
        fib_l = ImageChops.multiply(fiber, lmask)
        fib_r = ImageChops.multiply(fiber, rmask)
        for mask, fib, sgn in ((lmask, fib_l, -1), (rmask, fib_r, 1)):
            piece = prev.copy()
            wh = Image.new('RGBA', (W, H), PAPER + (255,))
            piece.paste(wh, (0, 0), fib)
            piece.putalpha(mask)
            tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            place(tmp, piece, W / 2 + sgn * 760 * e, H / 2 + 60 * e, 1.0, sgn * 9 * e, 1.0, nocache=True)
            out.alpha_composite(tmp)
        return out
    return new


# ------------------------------------------------------------------ SCENES
SCENES = []


def build():
    init_transitions()
    T = lambda x: x  # noqa

    # ============ S1  hook: "إذا تسوي قهوتك في البيت ؟"
    decor = [(dots_disc(430, ORANGE, cell=26, seed=1), 540, 1200, 0),
             (torn_piece(760, 260, KRAFT, seed=11), 160, 1640, 12),
             (torn_piece(520, 180, KRAFT, seed=12), 960, 250, -8)]
    s1 = Scene('s1', 0.0, bg_sheet(CREAM, 1, decor=decor))
    house = load_asset('house', border=14, seed=1, scale=0.82)
    s1.add(house, 540, 1215, t=-0.11, anim='stamp', d=0.17, z=5)
    shake(0.05, 16); sfx(0.0, 'slam', 1.0); sfx(0.0, 'whoosh', 0.6)
    mug = load_asset('mug', border=14, seed=2, scale=0.60)
    s1.add(mug, 580, 1420, t=0.78 - LEAD, anim='pop', z=8, spin=10)
    sfx(0.73, 'pop', 0.9)
    s1.add(None, 0, 0, t=0.98, painter=steam_painter(565, 1245), z=7)
    words_row(s1, [('إذا', -0.06, 'paper', 140), ('تسوي', 0.44, 'paper', 140)], 390, seed=1)
    words_row(s1, [('قهوتك', 0.78, 'orange', 250)], 612, seed=2)
    words_row(s1, [('في', 1.20, 'cream', 120), ('البيت', 1.30, 'dark', 160)], 830, seed=3)
    doodle_el(s1, 'underline', 540, 752, 520, 44, 0.98, 0.22, color=ESP, width=12, seed=1)
    sfx(0.98, 'scribble', 0.45, dur=0.22)
    q = word_sprite('؟', 'sticker_yellow', 270, seed=5)
    s1.add(q, 885, 815, t=1.52, anim='pop', z=30, spin=40, fn=lambda lt, st: st.update(r=st['r'] + 10 * math.sin(lt * 9) * math.exp(-lt * 2)))
    sfx(1.52, 'boing', 0.8)
    SCENES.append(s1)

    # ============ S2  "هذا الفيديو لك"
    decor = [(torn_piece(1000, 560, PAPER, seed=21), 560, 560, -3),
             (dots_disc(300, ESP, cell=22, seed=2), 120, 1780, 0)]
    s2 = Scene('s2', 1.74, bg_sheet(KRAFT, 2, decor=decor), trans='slide_up', td=0.22)
    sfx(1.72, 'whoosh', 0.9)
    player = load_asset('player', border=14, seed=3, scale=0.95)
    s2.add(player, 540, 1245, t=1.78, anim='rise', z=5)
    words_row(s2, [('هذا', 1.88, 'paper', 150), ('الفيديو', 2.18, 'dark', 150)], 400, seed=4)
    lk = word_sprite('لك', 'sticker_orange', 380, seed=6)
    s2.add(lk, 540, 700, r=-4, t=2.68 - LEAD, anim='stamp', z=22)
    shake(2.70, 16); s2.punch(2.66, 0.07); sfx(2.63, 'hit', 1.0)
    doodle_el(s2, 'burst', 540, 700, 760, 560, 2.72, 0.14, color=ESP, width=12, seed=2, z=19)
    doodle_el(s2, 'circle', 540, 705, 600, 400, 2.76, 0.26, color=ESP, width=13, seed=3, z=24)
    sfx(2.76, 'scribble', 0.55, dur=0.26)
    SCENES.append(s2)

    # ============ S3  "حنا كلوفا"
    s3 = Scene('s3', 3.04, bg_sheet(ESP, 3, dark=True, decor=[(dots_disc(360, ROAST, cell=24, seed=3), 900, 1700, 0), (dots_disc(260, ROAST, cell=20, seed=4), 150, 300, 0)]),
               trans='rip', td=0.36)
    sfx(3.02, 'rip', 1.0)
    burst = sunburst(2200, 28, CREAM, 22)
    s3.add(burst, 540, 1070, t=3.04, anim='none', z=1, boil=0, fn=lambda lt, st: st.update(r=lt * 14))
    words_row(s3, [('حنا', 3.32, 'paper', 170)], 430, seed=5)
    logo = load_asset('logo', border=16, seed=4, scale=0.98)
    s3.add(logo, 540, 1080, t=3.66 - LEAD - 0.04, anim='stamp', d=0.16, z=10, fn=lambda lt, st: st.update(r=st['r'] + 0 * lt))
    shake(3.68, 24); s3.punch(3.64, 0.08)
    sfx(3.30, 'riser', 0.55, dur=0.32); sfx(3.60, 'stamp', 1.0); sfx(3.60, 'boom', 0.9)
    beans = [load_asset(f'bean{i}', border=8, seed=10 + i, scale=0.34) for i in range(3)]
    rng = rng_for('s3beans')
    for k in range(12):
        ang = k / 12 * 2 * math.pi + rng.uniform(-0.2, 0.2)
        dist = rng.uniform(470, 560)
        sp = rng.uniform(-400, 400)

        def fn(lt, st, ang=ang, dist=dist, sp=sp):
            e = out_cubic(c01(lt / 0.5))
            st['x'] = 540 + math.cos(ang) * dist * e * 1.0
            st['y'] = 1080 + math.sin(ang) * dist * 1.25 * e
            st['r'] = sp * e
            st['s'] = min(1.0, lt / 0.08)
        s3.add(beans[k % 3], 540, 1080, t=3.68, anim='none', z=8, fn=fn)
    sfx(3.68, 'scatter', 0.7)
    SCENES.append(s3)

    # ============ S4  "متجر متخصص في محاصيل القهوة"
    decor = [(dots_disc(380, YELLOW, cell=26, seed=5), 540, 1300, 0),
             (torn_piece(1200, 330, KRAFT, seed=41), 540, 1700, -4)]
    s4 = Scene('s4', 4.22, bg_sheet(CREAM, 4, decor=decor), trans='slap', td=0.15)
    sfx(4.20, 'slap', 1.0); shake(4.33, 12)
    bags = [load_asset(n, border=12, seed=20 + i, scale=sc) for i, (n, sc) in enumerate([('bag_orange', 0.6), ('bag_yellow', 0.6), ('bag_cream', 0.7)])]
    s4.add(bags[0], 265, 1300, r=-9, t=4.36, anim='rise', z=4)
    s4.add(bags[1], 815, 1300, r=9, t=4.50, anim='rise', z=4)
    s4.add(bags[2], 540, 1345, r=0, t=4.64, anim='rise', z=6)
    for tt in (4.36, 4.50, 4.64):
        sfx(tt, 'swish', 0.6)
    words_row(s4, [('متجر', 4.36, 'dark', 150), ('متخصص', 4.66, 'paper', 150)], 400, seed=6)
    words_row(s4, [('في', 5.14, 'cream', 120), ('محاصيل', 5.26, 'orange', 210)], 612, seed=7)
    words_row(s4, [('القهوة', 5.62, 'yellow', 230)], 835, seed=8)
    rng = rng_for('rain')
    bs = [load_asset(f'bean{i}', border=6, seed=30 + i, scale=0.24) for i in range(3)]
    for k in range(22):
        x0 = rng.uniform(70, 1010); t0 = 5.22 + k * 0.035 + rng.uniform(0, 0.03); v0 = rng.uniform(300, 700); spin = rng.uniform(-500, 500)
        r0 = rng.uniform(0, 360)

        def fn(lt, st, x0=x0, v0=v0, spin=spin, r0=r0):
            st['x'] = x0 + 40 * math.sin(lt * 3 + x0)
            st['y'] = -80 + v0 * lt + 0.5 * 2600 * lt * lt
            st['r'] = r0 + spin * lt
        s4.add(bs[k % 3], x0, -80, t=t0, anim='none', z=12 if k % 3 else 3, fn=fn, boil=0)
    sfx(5.22, 'rattle', 0.65, dur=0.9)
    SCENES.append(s4)

    # ============ S5  "والفرق غالباً مو في المكينة"
    decor = [(grid_paper(760, 620, seed=51), 540, 1230, 3), (dots_disc(260, ESP, cell=20, seed=6), 960, 1760, 0)]
    s5 = Scene('s5', 6.06, bg_sheet(KRAFT, 5, decor=decor), trans='slide_left', td=0.22)
    sfx(6.04, 'whoosh', 0.9)
    mach = load_asset('machine', border=14, seed=5, scale=0.86)

    def mach_fn(lt, st):
        tt = lt + 6.12
        if 7.95 <= tt < 8.3:
            st['x'] += 10 * math.sin(tt * 90); st['r'] += 1.5 * math.sin(tt * 70)
    s5.add(mach, 540, 1250, t=6.12, anim='drop', z=5, fn=mach_fn)
    shake(6.46, 12); sfx(6.44, 'thud', 0.9)
    words_row(s5, [('والفرق', 6.32, 'paper', 150), ('غالباً', 6.80, 'paper', 150)], 400, seed=9)
    words_row(s5, [('مو', 7.36, 'orange', 230, 'stamp'), ('في', 7.54, 'cream', 120), ('المكينة', 7.66, 'dark', 170)], 625, seed=10)
    doodle_el(s5, 'x', 540, 1240, 680, 620, 7.92, 0.30, color=ORANGE, width=38, seed=4, z=30)
    sfx(7.92, 'scribble', 0.8, dur=0.30); sfx(8.04, 'buzzer', 0.55)
    SCENES.append(s5)

    # ============ S6  "الفرق في المحصول نفسه"
    decor = [(dots_disc(330, ORANGE, cell=24, seed=7), 950, 330, 0), (torn_piece(1300, 380, KRAFT, seed=61), 540, 1320, -6)]
    s6 = Scene('s6', 8.28, bg_sheet(CREAM, 6, decor=decor), trans='slap', td=0.14)
    sfx(8.26, 'slap', 0.9); shake(8.38, 10)
    g = render_beans_gray()
    bp = riso_print(g, paper=CREAM, inks=((ORANGE, 12, 15, 0.9, (0, 0)), (ESP, 9, 45, 1.0, (3, 2))),
                    curves=(lambda x: np.clip((x - 0.2) * 1.4, 0, 1), lambda x: np.clip(x * 1.5 - 0.15, 0, 1)), seed=6)
    bp.putalpha(torn_mask(*bp.size, seed=6))
    bp = cutout(bp.resize((820, 623), Image.LANCZOS), border=14, seed=6)
    s6.add(bp, 540, 1290, r=-3, t=8.40, anim='stamp', d=0.14, z=4)
    sfx(8.40, 'shutter', 0.8)
    tp = tape_sprite(seed=3)
    s6.add(tp, 190, 1000, r=-28, t=8.50, anim='stamp', d=0.1, z=6)
    s6.add(tape_sprite(seed=4), 890, 1010, r=24, t=8.56, anim='stamp', d=0.1, z=6)
    sfx(8.50, 'tape', 0.5)
    cher = load_asset('cherry', border=12, seed=7, scale=0.62)
    s6.add(cher, 690, 1605, r=-8, t=9.08 - LEAD, anim='pop', z=9, spin=18)
    words_row(s6, [('الفرق', 8.42, 'dark', 170), ('في', 8.92, 'cream', 120)], 395, seed=11)
    # marker highlight behind "المحصول"
    wsp = word_sprite('المحصول', 'sticker', 230, seed=12, shadow=False)
    cw, ch = content_size(wsp)
    band = marker_band(cw + 40, int(ch * 0.55), seed=1)
    s6.add(band, 540, 650, r=-2, t=9.08 - LEAD, anim='none', reveal=0.22, z=18, boil=0.8)
    s6.add(word_sprite('المحصول', 'sticker', 230, seed=12), 540, 628, r=-2, t=9.08 - LEAD, anim='pop', z=20, spin=8)
    sfx(9.03, 'marker', 0.6, dur=0.22)
    words_row(s6, [('نفسه', 9.70, 'orange', 180)], 858, seed=13)
    doodle_el(s6, 'circle', 540, 1290, 960, 760, 9.14, 0.34, color=ORANGE, width=16, seed=5, z=8)
    sfx(9.14, 'scribble', 0.5, dur=0.34)
    for k, (x, y, sz, tt) in enumerate([(135, 950, 120, 9.66), (950, 1180, 150, 9.72), (160, 1560, 100, 9.80), (905, 720, 90, 9.76)]):
        st_ = draw_doodle(doodle('star', sz, sz, k), sz, sz, 1.0, width=8, color=ESP, fill=YELLOW)
        s6.add(st_, x, y, t=tt, anim='pop', z=26, spin=60, fn=lambda lt, st: st.update(r=st['r'] + lt * 40))
    sfx(9.66, 'ding', 0.8)
    SCENES.append(s6)

    # ============ S7  "عشان كذا نوفر لك محاصيل من أكثر من بلد"
    decor = [(dots_disc(300, KRAFT, cell=22, seed=8), 120, 1650, 0), (torn_piece(600, 240, KRAFT, seed=71), 960, 1760, 10)]
    s7 = Scene('s7', 10.14, bg_sheet(CREAM, 7, decor=decor), trans='rip', td=0.34)
    sfx(10.12, 'rip', 1.0)
    globe = load_asset('globe', border=14, seed=8, scale=0.8)
    s7.add(globe, 540, 1250, t=10.39, anim='pop', z=4, fn=lambda lt, st: st.update(r=st['r'] - lt * 5))
    sfx(10.39, 'pop', 0.8)
    plane = load_asset('plane', border=10, seed=9, scale=0.42)
    cxp, cyp, rxp, ryp = 540, 1250, 450, 400
    a0, a1, tp0, tp1 = math.radians(160), math.radians(160 + 330), 10.7, 12.88

    def pang(t):
        return a0 + (a1 - a0) * in_out(c01((t - tp0) / (tp1 - tp0)))

    def trail(cv, lt, t):
        d = ImageDraw.Draw(cv)
        a_now = pang(t)
        n = int((a_now - a0) / 0.07)
        for i in range(n):
            a = a0 + i * 0.07
            px, py = cxp + rxp * math.cos(a), cyp + ryp * math.sin(a)
            d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=ESP + (255,))
    s7.add(None, 0, 0, t=tp0, painter=trail, z=6)

    def plane_fn(lt, st):
        t = lt + tp0
        a = pang(t)
        st['x'], st['y'] = cxp + rxp * math.cos(a), cyp + ryp * math.sin(a)
        st['r'] = math.degrees(a) + 90
    s7.add(plane, 0, 0, t=tp0, anim='none', z=7, fn=plane_fn)
    sfx(10.7, 'flyby', 0.45, dur=2.1)
    words_row(s7, [('عشان', 10.44, 'paper', 125), ('كذا', 10.66, 'paper', 125), ('نوفر', 10.82, 'dark', 135), ('لك', 11.20, 'paper', 125)], 385, seed=14)
    words_row(s7, [('محاصيل', 11.34, 'orange', 200), ('من', 11.80, 'cream', 120)], 590, seed=15)
    words_row(s7, [('أكثر', 12.02, 'yellow', 180), ('من', 12.46, 'cream', 120), ('بلد', 12.60, 'dark', 180)], 800, seed=16)
    for (nm, x, y, r, tt) in [('stamp_eth', 250, 1010, -13, 11.34), ('stamp_col', 835, 1040, 10, 11.80), ('stamp_bra', 245, 1480, 9, 12.02),
                              ('stamp_yem', 830, 1470, -9, 12.46), ('stamp_ken', 545, 1600, 4, 12.60)]:
        sc_ = stamp_card(nm, 0.72, seed=sum(map(ord, nm)) % 100)
        s7.add(sc_, x, y, r=r, t=tt - LEAD, anim='stamp', d=0.12, z=12)
        sfx(tt - LEAD, 'stamp_small', 0.85); shake(tt - LEAD + 0.07, 8)
    SCENES.append(s7)

    # ============ S8  "كل واحد له طعمه"
    s8 = Scene('s8', 12.92, bg_sheet(ESP, 8, dark=True, decor=[(dots_disc(420, ROAST, cell=26, seed=9), 540, 1240, 0)]), trans='slide_up', td=0.22)
    sfx(12.90, 'whoosh', 0.9)
    lg = render_latte_gray()
    lp = riso_print(lg, paper=CREAM, inks=((ORANGE, 11, 15, 0.8, (0, 0)), (ESP, 8, 45, 1.0, (3, 2))),
                    curves=(lambda x: np.clip((x - 0.1) * 1.2, 0, 1), lambda x: np.clip(x * 1.5 - 0.2, 0, 1)), seed=8)
    lp.putalpha(torn_mask(*lp.size, seed=8, circle=True))
    lp = cutout(lp.resize((560, 560), Image.LANCZOS), border=16, seed=8)
    s8.add(lp, 540, 1240, t=13.18 - LEAD, anim='pop', z=4, fn=lambda lt, st: st.update(r=st['r'] + lt * 12))
    icons = [('berry', 'توتي', 13.18), ('choco', 'شوكولاتة', 13.40), ('lemon', 'حمضي', 13.76), ('flower', 'زهري', 13.96)]
    for k, (nm, lab, tt) in enumerate(icons):
        ic = load_asset(nm, border=12, seed=40 + k, scale=0.42)
        lb = word_sprite(lab, 'paper', 64, fontname='Marhey', seed=50 + k)
        base = math.radians(-135 + k * 90)

        def orb(lt, st, base=base, tt=tt, dy=0):
            a = base + (lt + tt - 13.1) * 0.35
            st['x'] = 540 + 330 * math.cos(a); st['y'] = 1240 + 350 * math.sin(a) + dy
        s8.add(ic, 0, 0, t=tt - LEAD, anim='pop', z=10, spin=25, fn=orb)
        s8.add(lb, 0, 0, t=tt - LEAD + 0.06, anim='pop', z=11, spin=-10, fn=lambda lt, st, base=base, tt=tt: orb(lt, st, base, tt, 118))
        sfx(tt - LEAD, 'pop', 0.8, pitch=1.0 + k * 0.18)
    words_row(s8, [('كل', 13.18, 'paper', 150), ('واحد', 13.40, 'paper', 150), ('له', 13.76, 'paper', 150)], 395, seed=17)
    words_row(s8, [('طعمه', 13.96, 'orange', 250, 'stamp')], 625, seed=18)
    s8.punch(13.93, 0.05)
    sfx(14.0, 'sparkle', 0.6)
    SCENES.append(s8)

    # ============ S9  "بدون ما تدفع كل يوم في الكوفيّات"
    decor = [(dots_disc(340, YELLOW, cell=24, seed=10), 250, 1150, 0), (torn_piece(1200, 300, KRAFT, seed=91), 540, 1720, 5)]
    s9 = Scene('s9', 14.44, bg_sheet(CREAM, 9, decor=decor), trans='slap', td=0.14)
    sfx(14.42, 'slap', 1.0); shake(14.55, 12)
    rec = load_asset('receipt', border=0, seed=11, scale=0.64)

    def rec_fn(lt, st):
        t = lt + 14.95
        p = c01((t - 14.95) / 1.0)
        st['y'] = -420 + (1120 + 420) * out_cubic(p) + 4 * math.sin(t * 40) * (1 - p)
    s9.add(rec, 815, -420, r=5, t=14.95, anim='none', z=3, fn=rec_fn)
    sfx(15.0, 'printer', 0.45, dur=0.95)
    cals = [load_asset(f'cal_d{i}', border=12, seed=60 + i, scale=0.56) for i in range(7)] + [load_asset('cal_x7', border=12, seed=67, scale=0.56)]

    def cal_spr(lt):
        t = lt + 15.31
        k = int(max(0, t - 15.42) / 0.075)
        return cals[min(k, len(cals) - 1)]
    s9.add(cal_spr, 255, 1110, r=-7, t=15.31 - LEAD, anim='pop', z=6)
    for k in range(7):
        sfx(15.42 + k * 0.075, 'flip', 0.35)
    coin = load_asset('coin', border=8, seed=12, scale=0.5)
    rng = rng_for('coins')
    for k in range(7):
        vx = rng.uniform(-900, 900); vy = rng.uniform(-900, -500); spin = rng.uniform(-600, 600)

        def cfn(lt, st, vx=vx, vy=vy, spin=spin):
            st['x'] = 330 + vx * lt; st['y'] = 470 + vy * lt + 0.5 * 4200 * lt * lt; st['r'] = spin * lt
        s9.add(coin, 330, 470, t=15.0 - LEAD, anim='none', z=5, fn=cfn, until=15.95)
    sfx(14.97, 'kaching', 1.3); shake(15.0, 8)
    cup = load_asset('tcup', border=12, seed=13, scale=0.40)
    for k, (x, y, r, tt) in enumerate([(430, 1455, -8, 15.95), (600, 1440, 5, 16.02), (760, 1460, -4, 16.09), (330, 1330, 7, 16.16), (510, 1300, -6, 16.23), (690, 1320, 8, 16.30)]):
        s9.add(cup, x, y, r=r, t=tt, anim='pop', z=8 - (k // 3), spin=20)
        sfx(tt, 'pop', 0.5, pitch=0.9 + k * 0.08)
    words_row(s9, [('بدون', 14.60, 'dark', 160), ('ما', 14.90, 'paper', 130), ('تدفع', 15.00, 'orange', 180)], 395, seed=19)
    words_row(s9, [('كل', 15.36, 'paper', 145), ('يوم', 15.60, 'yellow', 190)], 605, seed=20)
    words_row(s9, [('في', 15.86, 'cream', 120), ('الكوفيّات', 15.98, 'dark', 175)], 812, seed=21)
    SCENES.append(s9)

    # ============ S10 "وبدون ما تتنازل عن الطعم"
    decor = [(torn_piece(1100, 560, PAPER, seed=101), 540, 560, 3), (dots_disc(380, ORANGE, cell=26, seed=11), 520, 1330, 0)]
    s10 = Scene('s10', 16.52, bg_sheet(KRAFT, 10, decor=decor), trans='rip', td=0.32)
    sfx(16.50, 'rip', 1.0)
    mug2 = load_asset('mug', border=14, seed=14, scale=0.92)
    s10.add(mug2, 500, 1345, t=16.78 - LEAD, anim='pop', z=5, spin=-10)
    sfx(16.73, 'pop', 0.8)
    s10.add(None, 0, 0, t=16.95, painter=steam_painter(480, 1085, n=3, spread=62, height=200, width=13), z=4)
    ros = load_asset('rosette', border=14, seed=15, scale=0.5)
    s10.add(ros, 835, 1140, r=12, t=18.18 - LEAD - 0.03, anim='stamp', d=0.15, z=12)
    shake(18.2, 16); s10.punch(18.14, 0.05); sfx(18.10, 'stamp', 0.9); sfx(18.16, 'ding', 0.75)
    rng = rng_for('hearts')
    for k in range(6):
        x0 = 380 + rng.uniform(-60, 220); t0 = 17.30 + k * 0.16
        hs = int(rng.uniform(60, 95))
        hsp = draw_doodle(doodle('heart', hs, hs, k), hs, hs, 1.0, width=6, color=ESP, fill=ORANGE)

        def hfn(lt, st, x0=x0):
            st['y'] = 1060 - 330 * lt; st['x'] = x0 + 25 * math.sin(lt * 6); st['a'] = c01(1.3 - lt * 0.9)
        s10.add(hsp, x0, 1060, t=t0, anim='pop', z=9, fn=hfn, until=18.6)
    sfx(17.30, 'sparkle', 0.4)
    words_row(s10, [('وبدون', 16.78, 'paper', 150), ('ما', 17.22, 'paper', 130)], 395, seed=22)
    words_row(s10, [('تتنازل', 17.34, 'dark', 175), ('عن', 18.02, 'cream', 120)], 605, seed=23)
    words_row(s10, [('الطعم', 18.18, 'yellow', 220, 'stamp')], 818, seed=24)
    SCENES.append(s10)

    # ============ S11 "اختار محصولك من الرابط بالبايو"
    decor = [(dots_disc(420, ORANGE, cell=26, seed=12), 540, 1300, 0), (torn_piece(540, 200, KRAFT, seed=111), 130, 1500, -12)]
    s11 = Scene('s11', 18.56, bg_sheet(CREAM, 11, decor=decor), trans='slide_up', td=0.22, zoom=(1.035, 1.07))
    sfx(18.54, 'whoosh', 0.9)
    phone = load_asset('phone', border=14, seed=16, scale=0.66)
    s11.add(phone, 540, 1345, r=-2, t=18.62, anim='rise', z=5)
    words_row(s11, [('اختار', 18.80, 'paper', 150), ('محصولك', 19.08, 'orange', 200)], 385, seed=25)
    words_row(s11, [('من', 19.52, 'cream', 120), ('الرابط', 19.64, 'dark', 170)], 595, seed=26)
    words_row(s11, [('بالبايو', 20.02, 'yellow', 210, 'stamp')], 805, seed=27)
    doodle_el(s11, 'arrow_dr', 320, 1120, 240, 300, 20.08, 0.18, color=ESP, width=13, seed=6, z=24)
    sfx(20.08, 'scribble', 0.4, dur=0.18)
    # link pill position on phone (svg 360,608 relative to 720x1400 content, center 360,700)
    lx, ly = 540 + 0 * 0.66, 1345 + (608 - 700) * 0.66

    def ripple(cv, lt, t):
        d = ImageDraw.Draw(cv)
        for k in range(2):
            q = lt - k * 0.12
            if 0 <= q < 0.45:
                rr = 30 + 260 * out_cubic(q / 0.45)
                al = int(255 * (1 - q / 0.45))
                d.ellipse((lx - rr, ly - rr * 0.55, lx + rr, ly + rr * 0.55), outline=ORANGE + (al,), width=10)
        if lt < 0.25:
            rr = 36 * (1 - lt / 0.25) + 10
            d.ellipse((lx - rr, ly - rr, lx + rr, ly + rr), fill=ESP + (140,))
    s11.add(None, 0, 0, t=20.26, painter=ripple, z=26, until=21)
    sfx(20.26, 'tap', 0.9)
    logo2 = load_asset('logo', border=14, seed=17, scale=0.34)
    s11.add(logo2, 870, 1060, r=12, t=20.40, anim='stamp', d=0.14, z=28)
    shake(20.46, 14); sfx(20.38, 'stamp', 0.9); sfx(20.40, 'boom', 0.7)
    SCENES.append(s11)

    for i, sc in enumerate(SCENES):
        sc.t1 = SCENES[i + 1].t0 + SCENES[i + 1].td if i + 1 < len(SCENES) else DUR


# ------------------------------------------------------------------ final frame
GRAIN = None
VIG = None


def init_post():
    global GRAIN, VIG
    rng = np.random.default_rng(5)
    GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
    GRAIN = [np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) - 128 for g in GRAIN]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    VIG = (1 - 0.16 * np.clip(d - 0.55, 0, 1) ** 1.5)[..., None]


def frame(i):
    t = i / FPS
    idx = 0
    for k, sc in enumerate(SCENES):
        if t >= sc.t0:
            idx = k
    sc = SCENES[idx]
    img = sc.render(t)
    if idx > 0 and t < sc.t0 + sc.td:
        prev = SCENES[idx - 1].render(t)
        img = transition(sc.trans, c01((t - sc.t0) / sc.td), prev, img)
    arr = np.asarray(img.convert('RGB'), np.float32)
    arr = arr * VIG + GRAIN[int(t * 15) % len(GRAIN)][..., None] * 0.18
    return np.clip(arr, 0, 255).astype(np.uint8)


def setup():
    build()
    init_post()
    with open(os.path.join(HERE, 'sfx_events.json'), 'w') as f:
        json.dump({'sfx': SFX, 'dur': DUR}, f, ensure_ascii=False, indent=0)


if __name__ == '__main__':
    mode = sys.argv[1]
    setup()
    if mode == 'preview':
        os.makedirs(os.path.join(HERE, 'preview'), exist_ok=True)
        for a in sys.argv[2:]:
            t = float(a)
            Image.fromarray(frame(int(round(t * FPS)))).save(os.path.join(HERE, 'preview', f'f_{t:05.2f}.png'))
            print('saved', t)
    elif mode == 'full':
        from multiprocessing import Pool
        import imageio_ffmpeg
        out = sys.argv[2]
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        p = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-tune', 'grain', out], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for k, fr in enumerate(pool.imap(frame, range(NF), chunksize=3)):
                p.stdin.write(fr.tobytes())
                if k % 60 == 0:
                    print('frame', k, '/', NF, flush=True)
        p.stdin.close(); p.wait()
        print('done', out)
