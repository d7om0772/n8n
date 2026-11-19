// Usage: node render.cjs out.mp4            -> full render piped into ffmpeg
//        node render.cjs --stills dir t1 t2 -> PNG stills for review
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
const ROOT = path.resolve(__dirname, '..');
(async () => {
  const browser = await chromium.launch({ args: ['--font-render-hinting=none', '--disable-lcd-text'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await page.goto('file://' + path.join(ROOT, 'index.html'));
  await page.waitForFunction(() => window.READY === true, null, { timeout: 30000 });
  const args = process.argv.slice(2);
  if (args[0] === '--stills') {
    const dir = args[1]; fs.mkdirSync(dir, { recursive: true });
    for (const t of args.slice(2)) {
      await page.evaluate(t => window.seek(t), +t);
      await page.screenshot({ path: path.join(dir, `t${(+t).toFixed(2)}.png`) });
    }
  } else {
    const out = args[0], FPS = 30;
    const TL = await page.evaluate(() => window.TL);
    const N = Math.round(TL.total * FPS);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
      '-i', path.join(ROOT, 'audio/narration.wav'),
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', String(FPS),
      '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', TL.total.toFixed(3), '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < N; i++) {
      await page.evaluate(t => window.seek(t), i / FPS);
      const buf = await page.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 60 === 0) console.log(`frame ${i}/${N} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log('done', out);
  }
  await browser.close();
})();
