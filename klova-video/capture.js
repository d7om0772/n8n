// usage: node capture.js <outDir> <fps> <duration> [workers]   |  node capture.js preview <outDir> t1,t2,...
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const page_url = 'file://' + path.join(__dirname, 'render.html');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => { if (m.type() === 'error') console.error('PAGE:', m.text()); });
  page.on('pageerror', e => console.error('PAGEERR:', e.message));
  await page.goto(page_url);
  await page.evaluate(() => window.ready);
  return page;
}

async function shot(page, t, frame, file) {
  await page.evaluate(([t, f]) => window.render(t, f), [t, frame]);
  await page.screenshot({ path: file, type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920 } });
}

(async () => {
  const browser = await chromium.launch({ args: ['--disable-gpu', '--font-render-hinting=none'] });
  if (process.argv[2] === 'preview') {
    const out = process.argv[3]; fs.mkdirSync(out, { recursive: true });
    const times = process.argv[4].split(',').map(Number);
    const page = await openPage(browser);
    for (const t of times) await shot(page, t, Math.round(t * 30), path.join(out, `t_${t.toFixed(2)}.png`));
  } else {
    const out = process.argv[2]; const fps = +process.argv[3]; const dur = +process.argv[4]; const nw = +(process.argv[5] || 4);
    fs.mkdirSync(out, { recursive: true });
    const n = Math.round(dur * fps);
    let next = 0; const t0 = Date.now();
    const worker = async () => {
      const page = await openPage(browser);
      while (true) {
        const f = next++; if (f >= n) break;
        await shot(page, f / fps, f, path.join(out, `f_${String(f).padStart(4, '0')}.png`));
        if (f % 60 === 0) console.log(`frame ${f}/${n}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
      }
    };
    await Promise.all(Array.from({ length: nw }, worker));
    console.log('done', n, 'frames in', ((Date.now() - t0) / 1000).toFixed(1), 's');
  }
  await browser.close();
})();
