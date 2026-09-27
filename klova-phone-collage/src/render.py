"""Render frames of index.html with headless Chromium.
usage:
  python3 render.py preview 0.5,3.4,...      -> preview/f_<t>.jpg
  python3 render.py video out.mp4 [fps]       -> silent H.264 video + sfx_events.json
"""
import json, subprocess, sys, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'


def open_page(p):
    b = p.chromium.launch(executable_path=CHROME, args=['--force-color-profile=srgb', '--font-render-hinting=none'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
    pg.goto('file://' + os.path.join(HERE, 'index.html'))
    pg.wait_for_function('window.READY === true', timeout=60000)
    return b, pg


def main():
    mode = sys.argv[1]
    with sync_playwright() as p:
        b, pg = open_page(p)
        if mode == 'preview':
            os.makedirs(os.path.join(HERE, 'preview'), exist_ok=True)
            for t in [float(x) for x in sys.argv[2].split(',')]:
                pg.evaluate(f'window.seek({t})')
                pg.screenshot(path=os.path.join(HERE, 'preview', f'f_{t:05.2f}.jpg'), type='jpeg', quality=85)
        else:
            out = sys.argv[2]
            fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            dur = pg.evaluate('window.DUR')
            json.dump(pg.evaluate('window.SFX'), open(os.path.join(HERE, 'sfx_events.json'), 'w'), ensure_ascii=False, indent=1)
            n = round(dur * fps)
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(fps), '-c:v', 'png',
                                   '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p',
                                   '-profile:v', 'high', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
            for i in range(n):
                pg.evaluate(f'window.seek({i / fps})')
                ff.stdin.write(pg.screenshot(type='png'))
                if i % 60 == 0:
                    print(f'frame {i}/{n}', flush=True)
            ff.stdin.close()
            ff.wait()
        b.close()


main()
