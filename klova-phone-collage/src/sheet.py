import sys, glob
from PIL import Image, ImageDraw
fs = sorted(glob.glob('preview/f_*.jpg'))
if len(sys.argv) > 2: fs = [f for f in fs if any(f'f_{float(x):05.2f}' in f for x in sys.argv[2].split(','))]
cols = min(len(fs), 4); w, h = 405, 720
rows = (len(fs) + cols - 1) // cols
sh = Image.new('RGB', (cols * w, rows * (h + 30)), 'white')
d = ImageDraw.Draw(sh)
for i, f in enumerate(fs):
    im = Image.open(f).resize((w, h))
    x, y = (i % cols) * w, (i // cols) * (h + 30)
    sh.paste(im, (x, y + 30)); d.text((x + 8, y + 8), f.split('_')[-1][:-4], fill='black')
sh.save(sys.argv[1], quality=85)
