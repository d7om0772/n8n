import numpy as np
from PIL import Image
rng = np.random.default_rng(7)

def fft_noise(n, beta, seed):
    """Tileable 1/f^beta noise, normalized to [-1,1]."""
    r = np.random.default_rng(seed)
    fx = np.fft.fftfreq(n)[:, None]; fy = np.fft.fftfreq(n)[None, :]
    f = np.sqrt(fx**2 + fy**2); f[0, 0] = 1
    spec = (r.normal(size=(n, n)) + 1j * r.normal(size=(n, n))) / f**beta
    spec[0, 0] = 0
    img = np.real(np.fft.ifft2(spec))
    img -= img.mean(); img /= np.abs(img).max()
    return img

def fibers(n, count, seed, length=(8, 40), width=1):
    r = np.random.default_rng(seed)
    acc = np.zeros((n, n), np.float32)
    for _ in range(count):
        x, y = r.uniform(0, n, 2); ang = r.uniform(0, np.pi); L = r.uniform(*length)
        val = r.choice([-1, 1]) * r.uniform(0.3, 1.0)
        steps = int(L)
        for s in range(steps):
            xx = int(x + np.cos(ang) * s) % n; yy = int(y + np.sin(ang) * s) % n
            acc[yy, xx] += val
            ang += r.normal(0, 0.05)
    return acc

def crumple(n, seed):
    """Soft crease shading: directional derivative of ridged noise."""
    base = fft_noise(n, 1.6, seed)
    ridged = 1 - np.abs(base)  # ridges along zero crossings
    ridged = ridged ** 6
    gy, gx = np.gradient(fft_noise(n, 2.2, seed + 1))
    light = (gx * 0.7 - gy * 0.7)
    light /= np.abs(light).max()
    return ridged, light

def kraft(n=2048):
    base = np.array([200, 162, 116], np.float32)  # #C8A274
    lo = fft_noise(n, 1.9, 1)         # large blotches
    mid = fft_noise(n, 1.2, 2)        # mottling
    hi = rng.normal(0, 1, (n, n))     # grain
    fib = fibers(n, 9000, 3)
    fib = np.clip(fib, -1.5, 1.5)
    ridged, light = crumple(n, 11)
    lum = 1 + lo * 0.035 + mid * 0.025 + hi * 0.018 + fib * 0.05 + light * 0.03 - ridged * 0.05
    img = base[None, None, :] * lum[:, :, None]
    # slight hue variation
    img[:, :, 0] *= 1 + mid * 0.01
    img[:, :, 2] *= 1 - lo * 0.02
    return np.clip(img, 0, 255).astype(np.uint8)

def paper(n, rgb, seed, fib_amt=0.03):
    mid = fft_noise(n, 1.3, seed)
    hi = np.random.default_rng(seed).normal(0, 1, (n, n))
    fib = np.clip(fibers(n, n * n // 700, seed + 5, (5, 20)), -1.5, 1.5)
    lum = 1 + mid * 0.015 + hi * 0.012 + fib * fib_amt
    img = np.array(rgb, np.float32)[None, None, :] * lum[:, :, None]
    return np.clip(img, 0, 255).astype(np.uint8)

Image.fromarray(kraft(2048)).save('assets/kraft.jpg', quality=93)
Image.fromarray(paper(768, (251, 247, 238), 21)).save('assets/paper_white.jpg', quality=92)
Image.fromarray(paper(768, (244, 234, 215), 22)).save('assets/paper_cream.jpg', quality=92)

# screen-space film grain frames (RGBA, mid-gray centered overlay)
for i in range(6):
    g = np.random.default_rng(100 + i).normal(0, 1, (960, 540))
    g = np.clip(128 + g * 38, 0, 255).astype(np.uint8)
    Image.fromarray(g, 'L').resize((1080, 1920), Image.NEAREST).save(f'assets/grain{i}.png')

# tape texture (semi transparent, fibrous)
n = 256
t = paper(n, (240, 232, 214), 31, 0.06)
a = np.full((n, n), 150, np.uint8)
Image.fromarray(np.dstack([t, a])).save('assets/tape.png')
print('ok')
