"""Trim transparent margins of generated cutouts and downscale them for the layout."""
import glob, os
from PIL import Image
os.makedirs("build/el", exist_ok=True)
for f in sorted(glob.glob("assets/*.png")):
    im = Image.open(f).convert("RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox()
    im = im.crop(bbox)
    im.thumbnail((900, 900), Image.LANCZOS)
    name = os.path.basename(f)
    im.save(f"build/el/{name}", optimize=True)
    print(name, im.size)
