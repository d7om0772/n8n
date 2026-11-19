// Render scene/index.html frame-by-frame with Playwright, then mux with the voiceover via ffmpeg.
//   node scripts/render.cjs                 -> output/digital-cards.mp4
//   node scripts/render.cjs --stills 1,4.2  -> output/stills/t_<sec>.png (quick preview)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');

const ROOT = path.join(__dirname, '..');
const FPS = 30;
const timings = JSON.parse(fs.readFileSync(path.join(ROOT, 'audio/timings.json'), 'utf8'));
const args = process.argv.slice(2);
const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;

(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.error('[page error]', e.message));
  await page.addInitScript(t => { window.TIMINGS = t; }, timings);
  await page.goto('file://' + path.join(ROOT, 'scene/index.html'));
  await page.evaluate(() => window.ready);
  const dur = await page.evaluate(() => window.DURATION);

  if (stillsArg) {
    fs.mkdirSync(path.join(ROOT, 'output/stills'), { recursive: true });
    for (const s of stillsArg.split(',').map(Number)) {
      // seek forward from 0 so every tween records its start values in order
      await page.evaluate(() => window.renderAt(0));
      await page.evaluate(t => window.renderAt(t), s);
      await page.screenshot({ path: path.join(ROOT, `output/stills/t_${s.toFixed(2)}.png`) });
    }
    await browser.close();
    return;
  }

  const frames = Math.round(dur * FPS);
  const out = path.join(ROOT, 'output/digital-cards.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-i', path.join(ROOT, 'audio/voiceover_final.wav'),
    '-map', '0:v', '-map', '1:a',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-r', String(FPS), '-c:a', 'aac', '-b:a', '192k', '-t', dur.toFixed(3), '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.renderAt(t), i / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${frames}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c))));
  await browser.close();
  console.log('done ->', out);
})();
