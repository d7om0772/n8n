// Renders all frames at RFPS (sub-frames for motion blur) using N parallel pages.
import { chromium } from 'playwright';
import fs from 'fs';
const RFPS = 60, N = 4;
const browser = await chromium.launch();
const pages = [];
for (let i = 0; i < N; i++) {
  const p = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('pageerror', e => console.log('pageerror', e.message));
  await p.goto('http://127.0.0.1:8765/src/scene.html');
  await p.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); });
  pages.push(p);
}
const meta = await pages[0].evaluate(() => ({ ev: window.EVENTS, DUR: window.META.DUR }));
fs.writeFileSync('out/events.json', JSON.stringify(meta.ev, null, 1));
const total = Math.round(meta.DUR * RFPS);
const only = process.argv[2] ? process.argv[2].split('-').map(Number) : [0, total];
let next = only[0]; const t0 = Date.now(); let done = 0;
async function worker(p) {
  await p.evaluate(() => { for (let t = 0; t < window.META.DUR; t += 0.5) window.render(t); });
  while (true) {
    const f = next++; if (f >= only[1]) return;
    const t = f / RFPS;
    await p.evaluate(t => window.render(t), t);
    await p.screenshot({ path: `frames/f${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 94 });
    if (++done % 60 === 0) console.log(`${done}/${only[1] - only[0]} frames, ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
}
await Promise.all(pages.map(worker));
await browser.close();
console.log('done', total, 'frames in', ((Date.now() - t0) / 1000).toFixed(0), 's');
