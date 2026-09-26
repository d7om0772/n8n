// usage: node render.js preview t1,t2,...   |  node render.js full <startFrame> <endFrame> <out.mp4>
const { chromium } = require('playwright-core');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const FPS = 30;

(async () => {
  const [mode, a, b, out] = process.argv.slice(2);
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--allow-file-access-from-files', '--font-render-hinting=none', '--disable-gpu-vsync', '--force-color-profile=srgb'],
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', (m) => console.log('[page]', m.text()));
  page.on('pageerror', (e) => console.log('[pageerror]', e.message));
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.waitForFunction(() => window.__READY === true, null, { timeout: 60000 });
  const cues = await page.evaluate(() => window.__CUES);
  const dur = await page.evaluate(() => window.__DUR);
  fs.writeFileSync(path.join(__dirname, 'cues.json'), JSON.stringify(cues, null, 1));

  if (mode === 'preview') {
    fs.mkdirSync(path.join(__dirname, 'preview'), { recursive: true });
    for (const ts of a.split(',')) {
      const t = parseFloat(ts);
      await page.evaluate((t) => window.renderFrame(t), t);
      await page.screenshot({ path: path.join(__dirname, 'preview', `f_${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 85 });
    }
  } else {
    const total = Math.round(dur * FPS);
    const f0 = parseInt(a || '0', 10), f1 = Math.min(total, parseInt(b || String(total), 10));
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) {
      await page.evaluate((t) => window.renderFrame(t), f / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      if ((f - f0) % 60 === 0) console.log(`frame ${f}/${f1} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
  }
  await browser.close();
})();
