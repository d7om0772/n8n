# -*- coding: utf-8 -*-
"""Shared helpers: palette, paper textures, cut-out sprites, compositing."""
import math, os, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
FPS = 12

FONT_L = os.path.join(ROOT, 'fonts', 'Lalezar-Regular.ttf')
FONT_C = os.path.join(ROOT, 'fonts', 'Changa.ttf')

# One palette for the whole film (unified look)
C = dict(
    bg=(238, 226, 205), paper=(251, 245, 233), cream=(243, 230, 206),
    kraft=(198, 152, 106), kraft_d=(160, 117, 78), kraft_l=(219, 183, 140),
    esp=(45, 28, 20), brown=(96, 62, 41), brown_l=(138, 92, 60),
    terra=(210, 88, 50), terra_d=(168, 62, 36),
    mustard=(234, 177, 72), mustard_d=(192, 136, 46),
    green=(112, 139, 82), green_d=(78, 103, 58),
    cherry=(196, 54, 44), cherry_d=(138, 32, 28),
    navy=(58, 78, 108), white=(253, 250, 244),
)
SHADOW_RGB = (52, 30, 16)


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def seed_of(*parts):
    return zlib.crc32(repr(parts).encode()) & 0xffffffff


def rnd(*parts):
    return np.random.default_rng(seed_of(*parts))


# ---------------------------------------------------------------- textures
def noise_field(h, w, seed, sigma_fine=0.7, coarse_div=10, sigma_coarse=2.0):
    r = np.random.default_rng(seed)
    a = ndimage.gaussian_filter(r.standard_normal((h, w)).astype(np.float32), sigma_fine)
    a /= a.std() + 1e-6
    ch, cw = max(2, h // coarse_div), max(2, w // coarse_div)
    b = ndimage.gaussian_filter(r.standard_normal((ch, cw)).astype(np.float32), sigma_coarse)
    b /= b.std() + 1e-6
    b = np.asarray(Image.fromarray(b, 'F').resize((w, h), Image.BILINEAR))
    return a, b


def texturize(im, fine=0.035, coarse=0.03, seed=0):
    arr = np.asarray(im).astype(np.float32).copy()
    h, w = arr.shape[:2]
    a, b = noise_field(h, w, seed)
    t = 1 + fine * a + coarse * b
    arr[..., :3] *= t[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA')


def cut_border(im, bpx=7, color=C['white'], seed=0, rough=0.45, tex=True):
    """Adds an irregular hand-cut paper border around the silhouette."""
    pad = int(bpx * 1.6) + 6
    base = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    base.alpha_composite(im, (pad, pad))
    a = np.asarray(base)[..., 3].astype(np.float32) / 255.0
    dist = ndimage.distance_transform_edt(a < 0.5)
    r = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(r.standard_normal(a.shape).astype(np.float32), 3.0)
    n /= n.std() + 1e-6
    n2 = ndimage.gaussian_filter(r.standard_normal(a.shape).astype(np.float32), 0.8)
    n2 /= n2.std() + 1e-6
    thr = bpx * (1 + rough * 0.45 * n) + 0.35 * n2
    ab = np.clip(thr - dist + 0.5, 0, 1)
    ab = np.maximum(ab, a)
    lay = np.zeros(a.shape + (4,), np.float32)
    lay[..., :3] = color[:3]
    lay[..., 3] = ab * 255
    lay_im = Image.fromarray(lay.astype(np.uint8), 'RGBA')
    if tex:
        lay_im = texturize(lay_im, 0.03, 0.03, seed + 11)
    lay_im.alpha_composite(base)
    return lay_im


# ---------------------------------------------------------------- drawing canvas (supersampled)
class SS:
    """Supersampled RGBA drawing surface; coordinates are in final pixels."""

    def __init__(self, w, h, ss=3, pad=10):
        self.w, self.h, self.ss, self.pad = int(w), int(h), ss, pad
        self.im = Image.new('RGBA', ((self.w + 2 * pad) * ss, (self.h + 2 * pad) * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def P(self, x, y):
        return ((x + self.pad) * self.ss, (y + self.pad) * self.ss)

    def pts(self, pts):
        return [self.P(x, y) for x, y in pts]

    def box(self, b):
        x0, y0 = self.P(b[0], b[1])
        x1, y1 = self.P(b[2], b[3])
        return [x0, y0, x1, y1]

    def ellipse(self, b, fill=None, outline=None, width=0):
        self.d.ellipse(self.box(b), fill=_c(fill), outline=_c(outline), width=int(width * self.ss))

    def circle(self, cx, cy, r, fill=None, outline=None, width=0):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill, outline, width)

    def rect(self, b, fill=None, outline=None, width=0):
        self.d.rectangle(self.box(b), fill=_c(fill), outline=_c(outline), width=int(width * self.ss))

    def rrect(self, b, r, fill=None, outline=None, width=0):
        self.d.rounded_rectangle(self.box(b), radius=r * self.ss, fill=_c(fill), outline=_c(outline),
                                 width=int(width * self.ss))

    def poly(self, pts, fill=None, outline=None, width=0):
        self.d.polygon(self.pts(pts), fill=_c(fill), outline=_c(outline), width=int(width * self.ss))

    def line(self, pts, fill, width, round_caps=True):
        self.d.line(self.pts(pts), fill=_c(fill), width=int(width * self.ss), joint='curve')
        if round_caps:
            for (x, y) in (pts[0], pts[-1]):
                self.circle(x, y, width / 2.0 - 0.1, fill=fill)

    def arc(self, b, start, end, fill, width):
        self.d.arc(self.box(b), start, end, fill=_c(fill), width=int(width * self.ss))

    def text(self, xy, s, size, fill, font=FONT_L, anchor='mm', rtl=True):
        f = ImageFont.truetype(font, int(size * self.ss))
        kw = dict(direction='rtl', language='ar') if rtl else {}
        self.d.text(self.P(*xy), s, font=f, fill=_c(fill), anchor=anchor, **kw)

    def paste(self, im, cx, cy):
        big = im.resize((im.width * self.ss, im.height * self.ss), Image.BICUBIC)
        x, y = self.P(cx, cy)
        self.im.alpha_composite(big, (int(x - big.width / 2), int(y - big.height / 2)))

    def result(self):
        return self.im.resize((self.w + 2 * self.pad, self.h + 2 * self.pad), Image.LANCZOS)


def _c(c):
    if c is None:
        return None
    return rgba(c) if len(c) == 3 else tuple(c)


# ---------------------------------------------------------------- sprites + compositing
class Sprite:
    def __init__(self, im, blur=7, pad_for_shadow=True):
        if pad_for_shadow:
            p = int(blur * 2.5) + 2
            big = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
            big.alpha_composite(im, (p, p))
            im = big
        self.im = im
        self.shd = im.split()[3].filter(ImageFilter.GaussianBlur(blur)) if blur > 0 else im.split()[3]
        self.w, self.h = im.size


def make_sprite(im, border=7, border_color=C['white'], seed=0, tex=True, blur=7, rough=0.45):
    if tex:
        im = texturize(im, 0.035, 0.03, seed)
    if border:
        im = cut_border(im, border, border_color, seed + 3, rough)
    return Sprite(im, blur)


def paste(canvas, im, x, y):
    x, y = int(round(x)), int(round(y))
    w, h = im.size
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.width, x + w), min(canvas.height, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    canvas.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def place(canvas, spr, x, y, rot=0.0, scale=1.0, sx=1.0, sy=1.0, lift=0.0, alpha=1.0,
          shadow=1.0, key=None, jitter=0.0):
    """Put a paper cut-out on the table. rot in degrees CCW. lift 0..1 raises it (bigger, softer shadow)."""
    if key is not None and jitter > 0:
        r = rnd(key, round(x / 3), round(y / 3), round(rot), round(scale * 20))
        x += r.uniform(-1, 1) * 1.6 * jitter
        y += r.uniform(-1, 1) * 1.6 * jitter
        rot += r.uniform(-1, 1) * 0.8 * jitter
    im, sh = spr.im, spr.shd
    fx, fy = scale * sx, scale * sy
    if abs(fx - 1) > 1e-3 or abs(fy - 1) > 1e-3:
        nw, nh = max(1, int(round(im.width * fx))), max(1, int(round(im.height * fy)))
        im = im.resize((nw, nh), Image.BICUBIC)
        sh = sh.resize((nw, nh), Image.BILINEAR)
    if abs(rot) > 0.05:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        sh = sh.rotate(rot, resample=Image.BILINEAR, expand=True)
    if shadow > 0:
        ox, oy = (6 + lift * 18) * shadow, (9 + lift * 26) * shadow
        op = (0.40 - 0.14 * lift) * alpha
        if lift > 0.05:
            sh = sh.filter(ImageFilter.GaussianBlur(2 + lift * 7))
        lay = Image.new('RGBA', sh.size, SHADOW_RGB + (0,))
        lay.putalpha(sh.point(lambda v: int(v * op)))
        paste(canvas, lay, x - sh.width / 2 + ox, y - sh.height / 2 + oy)
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v: int(v * alpha)))
    paste(canvas, im, x - im.width / 2, y - im.height / 2)


def local_to_world(x, y, rot, scale, ox, oy, sx=1.0, sy=1.0):
    t = math.radians(rot)
    lx, ly = ox * scale * sx, oy * scale * sy
    return (x + lx * math.cos(t) + ly * math.sin(t), y - lx * math.sin(t) + ly * math.cos(t))


# ---------------------------------------------------------------- easing
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease_io(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def ease_out(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def ease_in(p):
    p = clamp(p)
    return p ** 3


def lerp(a, b, p):
    return a + (b - a) * p


def pop_scale(k):
    """Scale for the k-th image after an item is slapped down (stop-motion overshoot)."""
    return [1.28, 0.93, 1.03, 1.0][k] if 0 <= k < 4 else 1.0


def pop_lift(k):
    return [1.0, 0.25, 0.05, 0.0][k] if 0 <= k < 4 else 0.0
