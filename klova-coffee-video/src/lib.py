# Collage toolkit: paper textures, cut-out styling, word strips, halftone prints, doodles, tape
import os, math, random, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
ASSETS = os.path.join(HERE, 'assets')
CACHE = os.path.join(HERE, 'cache')
os.makedirs(CACHE, exist_ok=True)


def hx(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


CREAM = hx('#F1E6D2'); PAPER = hx('#FBF4E6'); KRAFT = hx('#C99B6D'); KRAFT_D = hx('#A87A4E')
ESP = hx('#24150E'); ROAST = hx('#6E3B22'); ORANGE = hx('#FF5B2E'); YELLOW = hx('#FFC93C')

_fonts = {}


def font(name, size):
    k = (name, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(os.path.join(FONTS, name + '.ttf'), size)
    return _fonts[k]


def rng_for(*key):
    h = hashlib.md5(repr(key).encode()).hexdigest()
    return np.random.default_rng(int(h[:8], 16))


# ------------------------------------------------------------------ noise helpers
def smooth_noise(h, w, scale, rng):
    small = rng.random((max(2, h // scale + 2), max(2, w // scale + 2))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w + scale * 2, h + scale * 2), Image.BICUBIC)
    a = np.asarray(im, np.float32)[scale:scale + h, scale:scale + w] / 255.0
    return (a - 0.5) * 2


def paper_texture(w, h, color, seed=0, dark=False, fibers=True):
    rng = rng_for('paper', w, h, seed)
    base = np.ones((h, w, 3), np.float32) * np.array(color, np.float32)
    n = 0.016 * smooth_noise(h, w, 160, rng) + 0.010 * smooth_noise(h, w, 40, rng) + rng.normal(0, 0.016, (h, w)).astype(np.float32)
    if fibers:
        fib = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(fib)
        for _ in range(int(w * h / 2500)):
            x, y = rng.random() * w, rng.random() * h
            a = rng.random() * math.pi
            L = 6 + rng.random() * 22
            d.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], fill=int(40 + rng.random() * 60), width=1)
        fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255.0
        n += (fib * 0.10) if dark else (-fib * 0.07)
    for _ in range(int(w * h / 60000)):  # specks
        x, y = int(rng.random() * w), int(rng.random() * h)
        r = 1 + int(rng.random() * 2)
        n[max(0, y - r):y + r, max(0, x - r):x + r] += (0.25 if dark else -0.25) * rng.random()
    out = np.clip(base * (1 + n[..., None]), 0, 255).astype(np.uint8)
    return Image.fromarray(out).convert('RGBA')


# ------------------------------------------------------------------ cut-out styling
def autocrop(im, pad=0):
    a = np.asarray(im.getchannel('A'))
    ys, xs = np.nonzero(a > 3)
    if len(xs) == 0:
        return im
    return im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + 1 + pad), min(im.height, ys.max() + 1 + pad)))


def cutout(im, border=12, bcol=PAPER, shadow=(9, 14, 10, 0.38), rough=3.0, seed=0, texture=True, scale=1.0):
    """White hand-cut paper border + drop shadow + print texture. Keeps the object centered."""
    im = autocrop(im.convert('RGBA'))
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    rng = rng_for('cut', im.size, seed)
    sx, sy, sb, so = shadow if shadow else (0, 0, 0, 0)
    pad = int(border + rough * 2 + max(abs(sx), abs(sy)) + sb * 3 + 4)
    W, H = im.width + pad * 2, im.height + pad * 2
    obj = Image.new('RGBA', (W, H), (0, 0, 0, 0)); obj.paste(im, (pad, pad))
    arr = np.asarray(obj, np.float32)
    a = arr[..., 3] / 255.0
    if texture:
        tex = 1 + 0.022 * smooth_noise(H, W, 30, rng) + rng.normal(0, 0.025, (H, W)).astype(np.float32)
        arr[..., :3] *= tex[..., None]
    if border > 0:
        dist = ndimage.distance_transform_edt(a < 0.5)
        wob = smooth_noise(H, W, 18, rng) * rough + smooth_noise(H, W, 5, rng) * rough * 0.35
        bm = np.clip(border + 0.5 - dist + wob, 0, 1)
        bm = np.maximum(bm, a)
        btex = np.array(bcol, np.float32)[None, None, :] * (1 + rng.normal(0, 0.02, (H, W, 1)).astype(np.float32))
        rgb = arr[..., :3] * a[..., None] + btex * (1 - a[..., None])
        alpha = bm
    else:
        rgb = arr[..., :3]; alpha = a
    out = np.zeros((H, W, 4), np.float32)
    if shadow:
        sh = ndimage.gaussian_filter(alpha, sb)
        sh = ndimage.shift(sh, (sy, sx), order=1)
        out[..., :3] = np.array(ESP, np.float32)
        out[..., 3] = sh * so
    # composite object over shadow
    oa = alpha
    ra = oa + out[..., 3] * (1 - oa)
    rc = (rgb * oa[..., None] + out[..., :3] * (out[..., 3] * (1 - oa))[..., None]) / np.maximum(ra, 1e-6)[..., None]
    res = np.dstack([np.clip(rc, 0, 255), np.clip(ra * 255, 0, 255)]).astype(np.uint8)
    return Image.fromarray(res, 'RGBA')


def load_asset(name, **kw):
    key = 'asset_' + name + '_' + hashlib.md5(repr(sorted(kw.items())).encode()).hexdigest()[:8]
    p = os.path.join(CACHE, key + '.png')
    if os.path.exists(p):
        return Image.open(p).convert('RGBA')
    im = Image.open(os.path.join(ASSETS, name + '.png')).convert('RGBA')
    out = cutout(im, **kw)
    out.save(p)
    return out


# ------------------------------------------------------------------ word strips
STYLES = {
    'paper': (PAPER, ESP), 'cream': (CREAM, ESP), 'dark': (ESP, CREAM), 'orange': (ORANGE, PAPER),
    'yellow': (YELLOW, ESP), 'kraft': (KRAFT, ESP), 'roast': (ROAST, CREAM),
}


def torn_poly(w, h, rng, jag=7, step=9, wave=2.5):
    pts = []
    for x in np.arange(0, w + 1, step * 2):  # top
        pts.append((x, rng.uniform(-wave, wave)))
    for y in np.arange(0, h + 1, step):  # right
        pts.append((w + rng.uniform(-jag, jag * 0.4), y))
    for x in np.arange(w, -1, -step * 2):  # bottom
        pts.append((x, h + rng.uniform(-wave, wave)))
    for y in np.arange(h, -1, -step):  # left
        pts.append((rng.uniform(-jag * 0.4, jag), y))
    return pts


def word_sprite(text, style='paper', size=130, fontname='Lalezar', seed=0, padx=None, pady=None, shadow=True):
    key = 'word_' + hashlib.md5(repr((text, style, size, fontname, seed, padx, pady, shadow)).encode()).hexdigest()[:12]
    p = os.path.join(CACHE, key + '.png')
    if os.path.exists(p):
        return Image.open(p).convert('RGBA')
    rng = rng_for('word', text, style, seed)
    f = font(fontname, size)
    l, t, r, b = f.getbbox(text, direction='rtl', language='ar')
    tw, th = r - l, b - t
    if style == 'sticker' or style.startswith('sticker_'):
        col = {'sticker': ESP, 'sticker_orange': ORANGE, 'sticker_yellow': YELLOW, 'sticker_cream': PAPER}[style]
        sw = max(6, int(size * 0.075))
        pad = sw + 6
        im = Image.new('RGBA', (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        strokecol = ESP if col in (PAPER, YELLOW) else PAPER
        d.text((pad - l, pad - t), text, font=f, fill=col + (255,), direction='rtl', language='ar', stroke_width=sw, stroke_fill=strokecol + (255,))
        out = cutout(im, border=0, rough=0, seed=seed, shadow=(8, 12, 8, 0.4) if shadow else None, texture=False)
    else:
        bg, fg = STYLES[style]
        px = padx if padx is not None else int(size * 0.28)
        py = pady if pady is not None else int(size * 0.12)
        w, h = tw + px * 2, th + py * 2
        m = 12
        mask = Image.new('L', (w + m * 2, h + m * 2), 0)
        ImageDraw.Draw(mask).polygon([(x + m, y + m) for x, y in torn_poly(w, h, rng)], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0.7))
        dark = style in ('dark', 'roast')
        tex = paper_texture(w + m * 2, h + m * 2, bg, seed=seed + len(text), dark=dark)
        tex.putalpha(mask)
        d = ImageDraw.Draw(tex)
        d.text((m + px - l, m + py - t), text, font=f, fill=fg + (255,), direction='rtl', language='ar')
        out = cutout(tex, border=0, rough=0, seed=seed, shadow=(8, 12, 8, 0.4) if shadow else None, texture=False)
    out.save(p)
    return out


def content_size(sprite):
    """approx visible size (without shadow/padding) - used for layout"""
    a = np.asarray(sprite.getchannel('A'))
    ys, xs = np.nonzero(a > 200)
    if len(xs) == 0:
        return sprite.size
    return xs.max() - xs.min(), ys.max() - ys.min()


# ------------------------------------------------------------------ marker band (yellow highlighter)
def marker_band(w, h, color=YELLOW, seed=0):
    rng = rng_for('band', w, h, seed)
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # several overlapping rough strokes
    for k in range(3):
        y0 = 20 + rng.uniform(-6, 6); y1 = 20 + h + rng.uniform(-6, 6)
        pts = [(20 + rng.uniform(-10, 6), y0 + rng.uniform(-4, 4)), (20 + w + rng.uniform(-6, 10), y0 + rng.uniform(-8, 8)),
               (20 + w + rng.uniform(-4, 12), y1 + rng.uniform(-8, 8)), (20 + rng.uniform(-12, 4), y1 + rng.uniform(-4, 4))]
        d.polygon(pts, fill=color + (170,))
    arr = np.asarray(im, np.float32)
    streak = 1 + 0.06 * smooth_noise(im.height, im.width, 3, rng)
    arr[..., :3] *= streak[..., None]
    arr[..., 3] = np.clip(arr[..., 3] * 1.4, 0, 255)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ halftone riso prints
def halftone_layer(gray, cell, angle, gain=1.0, ss=2):
    """gray: float HxW, 1=white. returns ink coverage HxW (0..1)"""
    H, W = gray.shape
    yy, xx = np.mgrid[0:H * ss, 0:W * ss].astype(np.float32) / ss
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    u = xx * c + yy * s; v = -xx * s + yy * c
    uc = (np.floor(u / cell) + 0.5) * cell; vc = (np.floor(v / cell) + 0.5) * cell
    # back to image coords
    xc = uc * c - vc * s; yc = uc * s + vc * c
    gx = np.clip(xc.astype(int), 0, W - 1); gy = np.clip(yc.astype(int), 0, H - 1)
    blur = ndimage.gaussian_filter(gray, cell * 0.35)
    dark = np.clip((1 - blur[gy, gx]) * gain, 0, 1)
    r = cell * 0.5 * 1.42 * np.sqrt(dark)
    dist = np.sqrt((u - uc) ** 2 + (v - vc) ** 2)
    cov = (dist < r).astype(np.float32)
    cov = cov.reshape(H, ss, W, ss).mean(axis=(1, 3))
    return cov


def riso_print(gray, paper=CREAM, inks=((ORANGE, 11, 15, 0.9, (0, 0)), (ESP, 8, 45, 1.0, (3, 2))), curves=(None, None), seed=0):
    H, W = gray.shape
    rng = rng_for('riso', W, H, seed)
    base = np.asarray(paper_texture(W, H, paper, seed=seed).convert('RGB'), np.float32) / 255.0
    for (col, cell, ang, gain, off), cv in zip(inks, curves):
        g = cv(gray) if cv else gray
        cov = halftone_layer(g, cell, ang, gain)
        cov = ndimage.shift(cov, off, order=1)
        cov *= np.clip(1 + 0.25 * smooth_noise(H, W, 25, rng), 0.6, 1.0)  # uneven ink
        ink = np.array(col, np.float32) / 255.0
        base = base * (1 - cov[..., None] * (1 - ink[None, None, :]))
    return Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert('RGBA')


def render_beans_gray(W=1000, H=760, n=170, seed=1):
    rng = rng_for('beans', seed)
    ss = 2
    img = Image.new('L', (W * ss, H * ss), 95)
    # bean template
    bw, bh = 118 * ss, 160 * ss
    yy, xx = np.mgrid[-bh // 2:bh // 2, -bw // 2:bw // 2].astype(np.float32)
    e = (xx / (bw / 2)) ** 2 + (yy / (bh / 2)) ** 2
    inside = e < 1
    shade = 0.86 - 0.38 * np.clip((xx / bw + yy / bh) * 1.1 + 0.25, 0, 1) - 0.22 * e ** 2
    crease = np.abs(xx - 14 * ss * np.sin(yy / bh * math.pi * 1.6)) < 6 * ss
    val = np.where(crease & (np.abs(yy) < bh * 0.43), 0.1, shade)
    tmpl = Image.fromarray((np.clip(val, 0, 1) * 255).astype(np.uint8))
    alpha = Image.fromarray((inside * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))
    shadow = Image.fromarray((inside * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))
    for _ in range(n):
        s = rng.uniform(0.75, 1.15)
        rot = rng.uniform(0, 360)
        t = tmpl.resize((int(bw * s), int(bh * s))).rotate(rot, expand=True, resample=Image.BICUBIC)
        a = alpha.resize((int(bw * s), int(bh * s))).rotate(rot, expand=True, resample=Image.BICUBIC)
        sh = shadow.resize((int(bw * s), int(bh * s))).rotate(rot, expand=True, resample=Image.BICUBIC)
        x = int(rng.uniform(-60, W * ss)); y = int(rng.uniform(-60, H * ss))
        img.paste(Image.new('L', sh.size, 20), (x + 8, y + 12), sh.point(lambda v: v * 0.6))
        img.paste(t, (x, y), a)
    g = np.asarray(img.resize((W, H), Image.LANCZOS), np.float32) / 255.0
    return g


def render_latte_gray(S=900):
    ss = 2; N = S * ss
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / ss
    cx = cy = S / 2
    def circ(x, y, r):
        return np.sqrt((xx - x) ** 2 + (yy - y) ** 2) < r
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    g = np.full((N, N), 0.62, np.float32)  # table
    g = np.where(np.sqrt((xx - cx - 18) ** 2 + (yy - cy - 26) ** 2) < 405, 0.42, g)  # saucer shadow
    g = np.where(d < 400, 0.93 - 0.12 * (d / 400) ** 4, g)  # saucer
    g = np.where((d < 312) & (d > 300), 0.78, g)
    # handle
    hx_ = (xx > cx + 270) & (xx < cx + 390) & (np.abs(yy - cy) < 42)
    g = np.where(hx_, 0.97 - 0.1 * ((yy - cy) / 42) ** 2, g)
    g = np.where(np.sqrt((xx - cx - 20) ** 2 + (yy - cy - 22) ** 2) < 300, np.minimum(g, 0.55), g)  # cup shadow
    g = np.where(d < 300, 0.99 - 0.05 * (d / 300) ** 2, g)  # cup rim
    coffee = d < 258
    crema = 0.33 + 0.22 * (d / 258) ** 1.5
    g = np.where(coffee, crema, g)
    # latte art: heart
    hx0, hy0, hs = cx, cy + 10, 120
    X = (xx - hx0) / hs; Y = -(yy - hy0) / hs
    heart = (X ** 2 + Y ** 2 - 1) ** 3 - X ** 2 * Y ** 3 < 0
    g = np.where(coffee & heart, 0.95, g)
    ring = (np.abs(d - 150) < 6) & coffee & ~heart
    g = np.where(ring, 0.8, g)
    g = g.reshape(S, ss, S, ss).mean(axis=(1, 3))
    return ndimage.gaussian_filter(g, 1.2)


def torn_mask(w, h, seed=0, jag=10, circle=False):
    rng = rng_for('tornmask', w, h, seed)
    m = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(m)
    if circle:
        pts = []
        for k in range(360):
            a = math.radians(k)
            r = min(w, h) / 2 - jag - rng.uniform(0, jag)
            pts.append((w / 2 + r * math.cos(a), h / 2 + r * math.sin(a)))
        d.polygon(pts, fill=255)
    else:
        pts = []
        step = 8
        for x in range(0, w, step): pts.append((x, jag + rng.uniform(-jag, jag)))
        for y in range(0, h, step): pts.append((w - jag + rng.uniform(-jag, jag), y))
        for x in range(w, 0, -step): pts.append((x, h - jag + rng.uniform(-jag, jag)))
        for y in range(h, 0, -step): pts.append((jag + rng.uniform(-jag, jag), y))
        d.polygon(pts, fill=255)
    return m.filter(ImageFilter.GaussianBlur(0.8))


# ------------------------------------------------------------------ tape
def tape_sprite(w=230, h=70, seed=0, color=(236, 222, 190)):
    rng = rng_for('tape', w, h, seed)
    im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    pts = []
    for y in range(0, h + 1, 7): pts.append((10 + rng.uniform(0, 7), 10 + y))
    for y in range(h, -1, -7): pts.append((10 + w - rng.uniform(0, 7), 10 + y))
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).polygon(pts, fill=175)
    tex = paper_texture(im.width, im.height, color, seed=seed, fibers=False)
    tex.putalpha(m)
    arr = np.asarray(tex, np.float32)
    arr[..., :3] *= (1 + 0.012 * np.sin(np.arange(im.width) / 3.0))[None, :, None]
    return cutout(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)), border=0, rough=0, shadow=(2, 3, 3, 0.2), texture=False)


# ------------------------------------------------------------------ doodles
def wobble_path(pts, rng, amp=2.0):
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in pts]


def doodle(kind, w, h, seed=0):
    """returns list of strokes (polylines) inside a w x h box"""
    rng = rng_for('doodle', kind, w, h, seed)
    cx, cy = w / 2, h / 2
    S = []
    if kind == 'circle':
        pts = []
        turns = 1.12
        a0 = rng.uniform(0, 6.28)
        for k in range(160):
            t = k / 159
            a = a0 + t * turns * 2 * math.pi
            rx = w / 2 * (0.95 + 0.05 * math.sin(3 * a)) * (1 - 0.04 * t)
            ry = h / 2 * (0.95 + 0.05 * math.cos(2 * a)) * (1 - 0.03 * t)
            pts.append((cx + rx * math.cos(a) - 0.0, cy + ry * math.sin(a)))
        S.append(pts)
    elif kind == 'underline':
        pts = []
        for k in range(80):
            t = k / 79
            pts.append((w * 0.97 - t * w * 0.94, cy + math.sin(t * math.pi * 5) * h * 0.3 * (1 - 0.3 * t)))
        S.append(pts)
    elif kind == 'x':
        S.append([(w * 0.1 + t * w * 0.8 + rng.uniform(-3, 3), h * 0.08 + t * h * 0.84 + 30 * math.sin(t * 3)) for t in np.linspace(0, 1, 40)])
        S.append([(w * 0.9 - t * w * 0.8 + rng.uniform(-3, 3), h * 0.1 + t * h * 0.8 - 25 * math.sin(t * 3)) for t in np.linspace(0, 1, 40)])
    elif kind == 'check':
        S.append([(w * 0.08, h * 0.55), (w * 0.38, h * 0.88), (w * 0.95, h * 0.1)])
    elif kind in ('arrow_l', 'arrow_r', 'arrow_u', 'arrow_d', 'arrow_dr'):
        # curved arrow from tail to head
        if kind == 'arrow_dr': a, b, c = (0.15, 0.03), (0.0, 0.85), (0.95, 0.9)
        elif kind == 'arrow_r': a, b, c = (0.05, 0.7), (0.5, 0.05), (0.95, 0.5)
        elif kind == 'arrow_l': a, b, c = (0.95, 0.7), (0.5, 0.05), (0.05, 0.5)
        elif kind == 'arrow_u': a, b, c = (0.3, 0.95), (0.95, 0.5), (0.5, 0.05)
        else: a, b, c = (0.3, 0.05), (0.95, 0.5), (0.5, 0.95)
        pts = []
        for t in np.linspace(0, 1, 60):
            x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * c[0]
            y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * c[1]
            pts.append((x * w, y * h))
        S.append(pts)
        (x1, y1), (x0, y0) = pts[-1], pts[-6]
        ang = math.atan2(y1 - y0, x1 - x0)
        L = min(w, h) * 0.28
        S.append([(x1 + L * math.cos(ang + 2.6), y1 + L * math.sin(ang + 2.6)), (x1, y1), (x1 + L * math.cos(ang - 2.6), y1 + L * math.sin(ang - 2.6))])
    elif kind == 'star':
        # 4-point sparkle
        pts = []
        for k in range(9):
            a = k * math.pi / 4 - math.pi / 2
            r = (w / 2 if k % 2 == 0 else w * 0.13)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        S.append(pts)
    elif kind == 'heart':
        pts = []
        for t in np.linspace(0, 2 * math.pi, 90):
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            pts.append((cx + x / 34 * w, cy + y / 34 * h))
        S.append(pts)
    elif kind == 'burst':
        for k in range(8):
            a = k * math.pi / 4 + 0.2
            S.append([(cx + math.cos(a) * w * 0.28, cy + math.sin(a) * h * 0.28), (cx + math.cos(a) * w * 0.48, cy + math.sin(a) * h * 0.48)])
    return [wobble_path(s, rng, 1.2) for s in S]


def stroke_len(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def draw_doodle(strokes, w, h, progress, width=14, color=ESP, fill=None, ss=2):
    pad = width * 2
    im = Image.new('RGBA', ((w + pad * 2) * ss, (h + pad * 2) * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    total = sum(stroke_len(s) for s in strokes)
    remain = total * max(0.0, min(1.0, progress))
    if fill is not None and progress >= 1:
        for s in strokes:
            d.polygon([((x + pad) * ss, (y + pad) * ss) for x, y in s], fill=fill + (255,))
    for s in strokes:
        if remain <= 0:
            break
        seg = [s[0]]
        L = 0
        for i in range(len(s) - 1):
            l = math.hypot(s[i + 1][0] - s[i][0], s[i + 1][1] - s[i][1])
            if L + l >= remain:
                f = (remain - L) / max(l, 1e-6)
                seg.append((s[i][0] + (s[i + 1][0] - s[i][0]) * f, s[i][1] + (s[i + 1][1] - s[i][1]) * f))
                L = remain
                break
            seg.append(s[i + 1]); L += l
        remain -= L
        P = [((x + pad) * ss, (y + pad) * ss) for x, y in seg]
        if len(P) > 1:
            d.line(P, fill=color + (255,), width=width * ss, joint='curve')
        r = width * ss / 2
        for (x, y) in (P[0], P[-1]):
            d.ellipse((x - r, y - r, x + r, y + r), fill=color + (255,))
    return im.resize((w + pad * 2, h + pad * 2), Image.LANCZOS)


# ------------------------------------------------------------------ decor helpers
def dots_disc(r, color, cell=22, seed=0, falloff=1.0, angle=45):
    S = 2 * r
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    gray = np.clip(0.15 + 0.85 * d ** falloff, 0, 1)
    gray = np.where(d > 1, 1.0, gray)
    cov = halftone_layer(gray.astype(np.float32), cell, angle, 1.0, ss=1)
    im = np.zeros((S, S, 4), np.uint8)
    im[..., :3] = color
    im[..., 3] = (cov * 255).astype(np.uint8)
    return Image.fromarray(im, 'RGBA')


def torn_piece(w, h, color, seed=0, dark=False, shadow=True, jag=9):
    tex = paper_texture(w, h, color, seed=seed, dark=dark)
    tex.putalpha(torn_mask(w, h, seed=seed, jag=jag))
    return cutout(tex, border=0, rough=0, shadow=(6, 10, 8, 0.3) if shadow else None, seed=seed, texture=False)


def grid_paper(w, h, seed=0):
    tex = paper_texture(w, h, PAPER, seed=seed)
    d = ImageDraw.Draw(tex)
    for x in range(0, w, 34): d.line([(x, 0), (x, h)], fill=(120, 170, 190, 90), width=2)
    for y in range(0, h, 34): d.line([(0, y), (w, y)], fill=(120, 170, 190, 90), width=2)
    tex.putalpha(torn_mask(w, h, seed=seed))
    return cutout(tex, border=0, rough=0, shadow=(6, 10, 8, 0.3), seed=seed, texture=False)


def sunburst(S=2000, n=24, color=CREAM, alpha=26):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = a0 + math.pi / n
        d.polygon([(c, c), (c + S * math.cos(a0), c + S * math.sin(a0)), (c + S * math.cos(a1), c + S * math.sin(a1))], fill=color + (alpha,))
    return im


def stamp_card(name, scale=1.0, seed=0):
    key = f'stampcard_{name}_{scale}_{seed}'
    p = os.path.join(CACHE, key + '.png')
    if os.path.exists(p):
        return Image.open(p).convert('RGBA')
    ink = autocrop(Image.open(os.path.join(ASSETS, name + '.png')).convert('RGBA'))
    ink = ink.resize((int(ink.width * scale), int(ink.height * scale)), Image.LANCZOS)
    rng = rng_for('stampink', name, seed)
    arr = np.asarray(ink, np.float32)
    h, w = arr.shape[:2]
    grunge = np.clip(0.85 + 0.5 * smooth_noise(h, w, 14, rng) + 0.2 * smooth_noise(h, w, 4, rng), 0.5, 1)
    holes = rng.random((h, w)) > 0.025
    arr[..., 3] *= grunge * holes
    ink = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    m = 34
    card = paper_texture(w + m * 2, h + m * 2, PAPER, seed=seed + 7)
    card.alpha_composite(ink, (m, m))
    card.putalpha(torn_mask(w + m * 2, h + m * 2, seed=seed, jag=7))
    out = cutout(card, border=0, rough=0, shadow=(7, 11, 8, 0.35), seed=seed, texture=False)
    out.save(p)
    return out
