// node src/render.js preview <outdir> t1 t2 ...   -> PNG stills
// node src/render.js video <out.mp4> [fps]         -> full render muxed with the voice-over
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const AUDIO = path.join(ROOT, 'audio', 'voice.wav');
const AUDIO_OFFSET = 0.3; // seconds of silence before the voice starts

(async () => {
  const [mode, out, ...rest] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto('file://' + path.join(ROOT, 'src', 'index.html'));
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.querySelectorAll('image')].map(im => new Promise(r => {
      const i = new Image(); i.onload = i.onerror = r; i.src = im.getAttribute('href');
    })));
  });
  await page.waitForTimeout(400);
  const stage = await page.$('#stage');
  const shot = () => stage.screenshot({ type: 'png' });

  if (mode === 'preview') {
    fs.mkdirSync(out, { recursive: true });
    for (const ts of rest) {
      const t = parseFloat(ts);
      await page.evaluate(t => window.setTime(t), t);
      fs.writeFileSync(path.join(out, `t_${t.toFixed(2)}.png`), await shot());
    }
  } else {
    const fps = parseInt(rest[0] || '30', 10);
    const dur = await page.evaluate(() => window.DURATION);
    const n = Math.round(dur * fps);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
      '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
      '-itsoffset', String(AUDIO_OFFSET), '-i', AUDIO,
      '-filter_complex', '[1:a]apad,atrim=0:' + dur.toFixed(3) + ',afade=t=out:st=' + (dur - 0.25).toFixed(3) + ':d=0.25[a]',
      '-map', '0:v', '-map', '[a]',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
      '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
      '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-t', dur.toFixed(3), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    let ffDead = false;
    ff.on('close', c => { ffDead = true; if (c) { console.error('ffmpeg exited', c); process.exit(1); } });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      await page.evaluate(t => window.setTime(t), i / fps);
      const buf = await shot();
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 60 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    if (!ffDead) await new Promise(r => ff.on('close', r));
    console.log('wrote', out);
  }
  await browser.close();
})();
