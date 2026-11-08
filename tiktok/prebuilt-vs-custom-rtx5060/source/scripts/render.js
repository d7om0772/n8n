const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
// usage: node render.js outdir fps start end workers  |  node render.js outdir --times t1,t2,...
const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
let times;
if (process.argv[3] === '--times') times = process.argv[4].split(',').map(Number).map((t, i) => ({ t, name: `t_${t.toFixed(2)}.png` }));
else {
  const fps = +process.argv[3], s = +process.argv[4], e = +process.argv[5];
  times = []; for (let f = Math.round(s * fps); f < Math.round(e * fps); f++) times.push({ t: f / fps, name: `f_${String(f).padStart(5, '0')}.png` });
}
const W = +(process.argv[6] || process.argv[5] && process.argv[3] === '--times' ? 2 : 4) || 4;
(async () => {
  const browser = await chromium.launch({ args: ['--disable-web-security', '--allow-file-access-from-files'] });
  const workers = Math.min(W, times.length);
  let idx = 0, done = 0; const t0 = Date.now();
  await Promise.all(Array.from({ length: workers }, async () => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    page.on('pageerror', e => console.error('PAGEERR', e.message));
    await page.goto('file://' + path.resolve(__dirname, '../index.html'));
    await page.evaluate(() => window.ready);
    while (idx < times.length) {
      const job = times[idx++];
      await page.evaluate(t => window.renderFrame(t), job.t);
      await page.screenshot({ path: path.join(out, job.name), type: 'png' });
      done++; if (done % 60 === 0) console.log(done, '/', times.length, ((Date.now() - t0) / 1000).toFixed(1) + 's');
    }
    await page.close();
  }));
  await browser.close(); console.log('done', done, ((Date.now() - t0) / 1000).toFixed(1) + 's');
})();
