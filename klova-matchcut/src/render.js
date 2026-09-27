// Frame renderer: serves this folder, drives main.js in headless Chromium,
// and pipes PNG frames into ffmpeg.
//   node render.js stills <outDir> <t1,t2,...>
//   node render.js video <out.mp4> [workers]
const path = require('path');
const http = require('http');
const fs = require('fs');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = __dirname;
const TYPES = { '.html': 'text/html', '.js': 'application/javascript', '.png': 'image/png', '.json': 'application/json',
  '.woff2': 'font/woff2', '.srt': 'text/plain; charset=utf-8' };

function serve() {
  const srv = http.createServer((req, res) => {
    const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
    fs.readFile(p, (e, d) => {
      if (e) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      res.end(d);
    });
  });
  return new Promise(r => srv.listen(0, '127.0.0.1', () => r(srv)));
}

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  await page.waitForFunction(() => window.ready || window.bootError, null, { timeout: 60000 });
  const err = await page.evaluate(() => window.bootError);
  if (err) throw new Error(err);
  return page;
}

async function shot(page, fi) {
  await page.evaluate(i => window.renderFrame(i), fi);
  return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920 } });
}

function ffmpegOut(file) {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', '30', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg ' + c)))));
  return { ff, done };
}
const write = (s, buf) => new Promise(r => (s.write(buf) ? r() : s.once('drain', r)));

(async () => {
  const [mode, out, arg] = process.argv.slice(2);
  const srv = await serve();
  const port = srv.address().port;
  const launch = () => chromium.launch({ args: ['--disable-gpu', '--disable-accelerated-2d-canvas', '--force-color-profile=srgb'] });
  const browser = await launch();
  const extra = [];
  try {
    if (mode === 'stills') {
      fs.mkdirSync(out, { recursive: true });
      const page = await openPage(browser, port);
      for (const t of arg.split(',').map(Number)) {
        const buf = await shot(page, Math.round(t * 30));
        fs.writeFileSync(path.join(out, `f_${t.toFixed(2).padStart(5, '0')}.png`), buf);
      }
    } else if (mode === 'video') {
      const workers = +(arg || 4);
      const probe = await openPage(browser, port);
      const total = await probe.evaluate(() => window.FRAMES);
      fs.writeFileSync(path.join(ROOT, 'sfx_events.json'), JSON.stringify(await probe.evaluate(() => window.SFX), null, 1));
      await probe.close();
      const chunk = Math.ceil(total / workers);
      const parts = [];
      const t0 = Date.now();
      await Promise.all(Array.from({ length: workers }, async (_, w) => {
        const a = w * chunk, b = Math.min(total, a + chunk);
        if (a >= b) return;
        const file = path.join(path.dirname(out), `part_${w}.mp4`);
        parts[w] = file;
        const b2 = await launch(); extra.push(b2);
        const page = await openPage(b2, port);
        const { ff, done } = ffmpegOut(file);
        for (let i = a; i < b; i++) {
          await write(ff.stdin, await shot(page, i));
          if (w === 0 && (i - a) % 20 === 0) console.log(`frame ${i - a}/${b - a} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
        }
        ff.stdin.end();
        await done;
        await page.close();
      }));
      const list = path.join(path.dirname(out), 'parts.txt');
      fs.writeFileSync(list, parts.filter(Boolean).map(p => `file '${path.resolve(p)}'`).join('\n'));
      await new Promise((res, rej) => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out], { stdio: 'inherit' })
        .on('close', c => (c === 0 ? res() : rej(new Error('concat ' + c)))));
      parts.filter(Boolean).forEach(p => fs.unlinkSync(p)); fs.unlinkSync(list);
      console.log('done', out, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
  } finally {
    await Promise.all(extra.map(b => b.close()));
    await browser.close();
    srv.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
