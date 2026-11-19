// Renders every text item to a tight transparent PNG (real Arabic shaping via Chromium).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'build', 'text');
const INK = '#1f1d1a';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const texts = JSON.parse(fs.readFileSync(path.join(__dirname, 'texts.json'), 'utf8'));
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    @font-face{font-family:Marhey;src:url(${path.join(ROOT, 'fonts/Marhey.ttf')});font-weight:300 800}
    html,body{margin:0;background:transparent}
    #t{display:inline-block;font-family:Marhey;color:${INK};direction:rtl;white-space:nowrap;
       padding:18px 26px;line-height:1.35}
  </style></head><body><span id="t"></span></body></html>`;
  const tmp = path.join(ROOT, 'build', '_text.html');
  fs.writeFileSync(tmp, html);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 600 }, deviceScaleFactor: 1 });
  await page.goto('file://' + tmp);
  const manifest = {};
  for (const t of texts) {
    let size = t.size;
    for (;;) {
      await page.evaluate(({ text, size, weight }) => {
        const el = document.getElementById('t');
        el.textContent = text; el.style.fontSize = size + 'px'; el.style.fontWeight = weight;
      }, { text: t.text, size, weight: t.weight });
      await page.evaluate(() => document.fonts.ready);
      const w = await page.evaluate(() => document.getElementById('t').getBoundingClientRect().width);
      if (w - 52 <= t.maxWidth || size < 20) break;
      size -= 2;
    }
    const el = await page.$('#t');
    const file = path.join(OUT, t.id + '.png');
    await el.screenshot({ path: file, omitBackground: true });
    const box = await el.boundingBox();
    manifest[t.id] = { file: 'build/text/' + t.id + '.png', w: Math.round(box.width), h: Math.round(box.height), size };
    console.log(t.id, size, Math.round(box.width), 'x', Math.round(box.height));
  }
  fs.writeFileSync(path.join(ROOT, 'build', 'text_manifest.json'), JSON.stringify(manifest, null, 1));
  await browser.close();
  fs.unlinkSync(tmp);
})();
