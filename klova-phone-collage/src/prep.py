"""Builds graded assets (one unified colour grade across every photo) from raw/ into assets/."""
import numpy as np
from PIL import Image, ImageFilter
import os

os.makedirs('assets', exist_ok=True)
STOPS = [(0.0, (42, 23, 17)), (0.5, (189, 148, 132)), (1.0, (255, 243, 228))]


def gmap(lum):
    out = np.zeros(lum.shape + (3,), np.float32)
    xs = [s[0] for s in STOPS]
    for c in range(3):
        out[..., c] = np.interp(lum, xs, [s[1][c] / 255 for s in STOPS])
    return out


def grade(im, amt=0.35, desat=0.15):
    rgba = im.convert('RGBA')
    a = np.asarray(rgba).astype(np.float32) / 255
    rgb, alpha = a[..., :3], a[..., 3:]
    lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    rgb = rgb * (1 - desat) + lum[..., None] * desat
    rgb = rgb * (1 - amt) + gmap(lum) * amt
    rgb = 0.035 + rgb * 0.95  # lift blacks a touch (matte, paper-like)
    out = np.concatenate([np.clip(rgb, 0, 1), alpha], -1)
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA')


def up(im, f):
    im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))


def save_jpg(im, name, q=92):
    im.convert('RGB').save(f'assets/{name}', quality=q)


# photos
beans = Image.open('raw/beans.jpg')
farmer = Image.open('raw/farmer.jpg')
pour = Image.open('raw/pourover.jpg')
save_jpg(grade(up(farmer, 2.0)), 'farmer.jpg')
save_jpg(grade(up(beans, 1.6)), 'beans.jpg')
save_jpg(grade(up(pour, 2.0), amt=0.3), 'pourover.jpg')

# lock-screen wallpaper: beans, cover 1080x1920, blurred + darkened
w = grade(beans, amt=0.45).convert('RGB')
s = 1920 / w.height
w = w.resize((round(w.width * s), 1920), Image.LANCZOS)
x0 = (w.width - 1080) // 2
w = w.crop((x0, 0, x0 + 1080, 1920)).filter(ImageFilter.GaussianBlur(5))
save_jpg(w, 'wall.jpg', 88)

# cutouts / stickers (lighter grade so they sit in the same palette)
for n, amt in [('sack', .22), ('latte', .22), ('bag_klova', .15), ('orange', .28), ('strawberry', .28),
               ('chocolate', .2), ('espresso_ht', .0), ('globe_ht', .0), ('takeaway_ht', .0),
               ('pointing_ht', .0)]:
    im = Image.open(f'raw/{n}.png')
    g = grade(im, amt=amt, desat=.1) if amt else im.convert('RGBA')
    g.save(f'assets/{n}.png', optimize=True)
for n in ['logo_espresso', 'logo_cream']:
    Image.open(f'raw/{n}.png').save(f'assets/{n}.png')

# paper grain tile
rng = np.random.default_rng(7)
n = rng.normal(0.5, 0.18, (960, 540)).clip(0, 1)
Image.fromarray((n * 255).astype(np.uint8), 'L').save('assets/grain.png')
print('ok')
