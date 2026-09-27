import sys, json, subprocess, time, os
from playwright.sync_api import sync_playwright
W,H,FPS = 1080,1920,30
mode = sys.argv[1]  # 'stills' or 'video'
dur = json.load(open('timing.json'))['duration']
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--allow-file-access-from-files','--force-color-profile=srgb'])
    pg = b.new_page(viewport={'width':W,'height':H}, device_scale_factor=1)
    pg.goto('file://'+os.path.abspath('index.html')); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(400)
    # preload: touch every element once so images decode
    for t in [x*0.5 for x in range(int(dur*2)+1)]: pg.evaluate(f'render({t})')
    pg.wait_for_timeout(300)
    if mode == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]
        os.makedirs('stills', exist_ok=True)
        for t in ts:
            pg.evaluate(f'render({t})'); pg.screenshot(path=f'stills/t{t:05.2f}.jpg', type='jpeg', quality=85)
    else:
        n = int(round(dur*FPS)); out = sys.argv[2]
        ff = subprocess.Popen(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-',
                               '-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-r',str(FPS),out], stdin=subprocess.PIPE)
        t0=time.time()
        for i in range(n):
            pg.evaluate(f'render({i/FPS})')
            ff.stdin.write(pg.screenshot(type='jpeg', quality=94))
            if i%60==0: print(i, n, round(time.time()-t0,1), flush=True)
        ff.stdin.close(); ff.wait()
    b.close()
