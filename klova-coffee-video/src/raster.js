// usage: node raster.js svgdir outdir  (renders every *.svg at its width/height attrs * scale)
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [svgdir, outdir, only] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const fontdir = path.resolve(__dirname, 'fonts');
  const css = ['Lalezar','Marhey','Anton','PermanentMarker','Alexandria','Cairo'].map(f =>
    `@font-face{font-family:'${f}';src:url('file://${fontdir}/${f}.ttf');}`).join('\n');
  for (const f of fs.readdirSync(svgdir).filter(f => f.endsWith('.svg'))) {
    if (only && !f.startsWith(only)) continue;
    const svg = fs.readFileSync(path.join(svgdir, f), 'utf8');
    const w = +svg.match(/width="(\d+)"/)[1], h = +svg.match(/height="(\d+)"/)[1];
    const html = `<html><head><style>${css} html,body{margin:0;background:transparent}</style></head><body>${svg}</body></html>`;
    const tmp = path.join(outdir, '_tmp.html'); fs.writeFileSync(tmp, html);
    await page.setViewportSize({ width: w, height: h });
    await page.goto('file://' + path.resolve(tmp));
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(outdir, f.replace('.svg', '.png')), omitBackground: true, clip: {x:0,y:0,width:w,height:h} });
    console.log('ok', f, w, h);
  }
  await browser.close();
})();
