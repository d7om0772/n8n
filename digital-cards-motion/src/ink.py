"""Turns line-art images and rendered text into "pen paths".

For each asset it writes:
  build/ink/<id>_ink.png    black ink layer (RGBA)           [images only; text PNG is its own ink]
  build/ink/<id>_color.png  colour fills with the ink lifted  [images only]
and a JSON entry with the skeleton strokes (centre lines), ordered the way a pen would draw them.
The page uses those strokes as a growing SVG mask, so the real artwork is revealed along the pen path.
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'ink')
INK_RGB = (31, 29, 26)

N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def trace_skeleton(sk):
    """Split a 1px skeleton into polylines between endpoints/junctions (plus closed loops)."""
    H, W = sk.shape
    pad = np.pad(sk, 1).astype(np.uint8)
    deg = ndimage.convolve(pad, np.ones((3, 3), np.uint8), mode='constant')[1:-1, 1:-1] - 1
    deg = np.where(sk, deg, 0)
    pts = set(zip(*np.nonzero(sk)))
    node = {p for p in pts if deg[p] != 2}
    visited_edges = set()

    def nbrs(p):
        y, x = p
        for dy, dx in N8:
            q = (y + dy, x + dx)
            if q in pts:
                yield q

    polylines = []

    def walk(a, b):
        line = [a, b]
        visited_edges.add((a, b)); visited_edges.add((b, a))
        prev, cur = a, b
        while cur not in node:
            nxt = None
            for q in nbrs(cur):
                if q != prev and (cur, q) not in visited_edges:
                    nxt = q
                    break
            if nxt is None:
                break
            visited_edges.add((cur, nxt)); visited_edges.add((nxt, cur))
            line.append(nxt)
            prev, cur = cur, nxt
            if cur == a:
                break
        return line

    for p in node:
        for q in nbrs(p):
            if (p, q) not in visited_edges:
                polylines.append(walk(p, q))
    # isolated dots
    for p in node:
        if deg[p] == 0:
            polylines.append([p])
    # pure loops (no endpoint/junction)
    for p in pts:
        if p in node:
            continue
        for q in nbrs(p):
            if (p, q) not in visited_edges:
                node.add(p)
                polylines.append(walk(p, q))
                node.discard(p)
    return [[(x, y) for (y, x) in l] for l in polylines]


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0], float), np.array(pts[-1], float)
    ab = b - a
    n = np.hypot(*ab)
    P = np.array(pts, float)
    if n == 0:
        d = np.hypot(*(P - a).T)
    else:
        V = P - a
        d = np.abs(ab[0] * V[:, 1] - ab[1] * V[:, 0]) / n
    i = int(np.argmax(d))
    if d[i] > eps:
        return rdp(pts[:i + 1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def order_strokes(strokes, mode):
    """Greedy pen order. mode='rtl' for Arabic text, 'draw' for illustrations."""
    left = list(range(len(strokes)))
    out = []
    if mode == 'rtl':
        start = max(left, key=lambda i: max(p[0] for p in strokes[i]['pts']) - 0.3 * min(p[1] for p in strokes[i]['pts']))
    else:
        start = min(left, key=lambda i: min(p[1] + 0.35 * p[0] for p in strokes[i]['pts']))
    s = strokes[start]
    if mode == 'rtl' and s['pts'][0][0] < s['pts'][-1][0]:
        s['pts'].reverse()
    out.append(s); left.remove(start)
    cur = s['pts'][-1]
    xfront = max(p[0] for p in s['pts'])
    while left:
        best, bcost, brev = None, 1e18, False
        for i in left:
            pts = strokes[i]['pts']
            for rev, e in ((False, pts[0]), (True, pts[-1])):
                d = math.dist(cur, e)
                if mode == 'rtl':
                    xr = max(p[0] for p in pts)
                    d += 3.0 * max(0.0, xr - cur[0] - 25) + 0.15 * max(0.0, xfront - xr)
                if d < bcost:
                    best, bcost, brev = i, d, rev
        s = strokes[best]
        if brev:
            s['pts'].reverse()
        out.append(s); left.remove(best)
        cur = s['pts'][-1]
    return out


def process(asset_id, ink_alpha, mode, binary_thresh=0.5, eps=0.8, min_len=2.0):
    """ink_alpha: float array 0..1 (1 = ink)."""
    binary = ink_alpha > binary_thresh
    binary = ndimage.binary_opening(binary, iterations=1) | (ndimage.binary_erosion(binary) & binary)
    dt = ndimage.distance_transform_edt(binary)
    sk = skeletonize(binary)
    lines = trace_skeleton(sk)
    strokes = []
    for l in lines:
        width = 2.0 * max(dt[int(y), int(x)] for x, y in l) + 4.0
        L = plen(l)
        if L < min_len and len(l) > 1:
            # tiny spur: keep only if it is a blob on its own
            if width < 8:
                continue
        simp = rdp(l, eps) if len(l) > 2 else l
        if len(simp) == 1:
            simp = [simp[0], (simp[0][0] + 0.5, simp[0][1])]
        strokes.append({'pts': [list(map(float, p)) for p in simp], 'width': round(float(width), 1)})
    strokes = order_strokes(strokes, mode)
    total = 0.0
    prev = None
    for s in strokes:
        if prev is not None:
            total += min(math.dist(prev, s['pts'][0]), 220) * 0.22  # pen-lift travel time
        s['start'] = round(total, 2)
        L = max(plen(s['pts']), 0.6)
        s['len'] = round(L, 2)
        total += L
        prev = s['pts'][-1]
        s['pts'] = [[round(x, 1), round(y, 1)] for x, y in s['pts']]
    return {'strokes': strokes, 'total': round(total, 2)}


def main():
    os.makedirs(OUT, exist_ok=True)
    result = {}
    # illustrations
    for name in ['hero', 'globe', 'tag', 'store', 'lock', 'outro']:
        im = np.asarray(Image.open(os.path.join(ROOT, 'images', name + '.png')).convert('RGB')).astype(float) / 255
        L = 0.299 * im[..., 0] + 0.587 * im[..., 1] + 0.114 * im[..., 2]
        alpha = np.clip((0.62 - L) / 0.42, 0, 1)
        H, W = L.shape
        ink = np.zeros((H, W, 4), np.uint8)
        ink[..., :3] = INK_RGB
        ink[..., 3] = (alpha * 255).astype(np.uint8)
        Image.fromarray(ink).save(os.path.join(OUT, name + '_ink.png'))
        # colour layer with ink lifted, so the colour wipe never reveals undrawn lines
        lift = ndimage.grey_dilation(alpha, size=(3, 3))[..., None]
        col = im + (1 - im) * lift
        # also flatten near-white to pure white (paper shows through via multiply)
        col = np.where(col > 0.965, 1.0, col)
        Image.fromarray((col * 255).astype(np.uint8)).save(os.path.join(OUT, name + '_color.png'))
        r = process(name, alpha, 'draw')
        r.update(w=W, h=H)
        result[name] = r
        print(name, len(r['strokes']), 'strokes, total', r['total'])
    # text
    man = json.load(open(os.path.join(ROOT, 'build', 'text_manifest.json')))
    for tid, m in man.items():
        im = np.asarray(Image.open(os.path.join(ROOT, m['file'])).convert('RGBA')).astype(float) / 255
        alpha = im[..., 3]
        r = process(tid, alpha, 'rtl', eps=0.6)
        r.update(w=alpha.shape[1], h=alpha.shape[0])
        result[tid] = r
        print(tid, len(r['strokes']), 'strokes, total', r['total'])
    with open(os.path.join(ROOT, 'build', 'strokes.js'), 'w') as f:
        f.write('window.STROKES = ' + json.dumps(result, separators=(',', ':')) + ';\n')
        f.write('window.TEXTMAN = ' + json.dumps(man, separators=(',', ':')) + ';\n')


if __name__ == '__main__':
    main()
