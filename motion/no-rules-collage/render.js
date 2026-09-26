// Usage: node render.js [outDir] [frameList e.g. "0,12,40-60"]
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const http = require('http'), fs = require('fs'), path = require('path');

const root = __dirname;
const outDir = path.resolve(root, process.argv[2] || 'frames');
const list = process.argv[3];
const TYPES = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.woff': 'font/woff' };

const srv = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => {
    if (e) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); res.end(d);
  });
});

srv.listen(0, '127.0.0.1', async () => {
  const port = srv.address().port;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => { console.error('[pageerror]', e); process.exitCode = 1; });
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  await page.waitForFunction('window.READY === true', null, { timeout: 180000 });
  const NF = await page.evaluate('window.NF');
  let frames = [...Array(NF).keys()];
  if (list) frames = list.split(',').flatMap(s => { const [a, b] = s.split('-').map(Number); return b === undefined ? [a] : [...Array(b - a + 1).keys()].map(k => a + k); });
  fs.mkdirSync(outDir, { recursive: true });
  const t0 = Date.now();
  for (const i of frames) {
    const data = await page.evaluate(i => { window.renderFrame(i); return document.getElementById('c').toDataURL('image/jpeg', 0.96); }, i);
    fs.writeFileSync(path.join(outDir, `f${String(i).padStart(4, '0')}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
    if (frames.length > 20 && i % 24 === 0) console.log(`frame ${i}/${NF} (${((Date.now() - t0) / 1000).toFixed(1)}s)`);
  }
  console.log(`rendered ${frames.length} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await browser.close(); srv.close();
});
