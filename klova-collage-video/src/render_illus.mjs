import { chromium } from 'playwright';
import path from 'path';
const dir = path.resolve('src');
const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 2, viewport: { width: 1000, height: 1100 } });
await page.goto('file://' + dir + '/illus.html');
await page.evaluate(() => document.fonts.ready);
const names = await page.evaluate(() => Object.keys(window.ILLUS));
for (const n of names) {
  await page.evaluate(n => { document.getElementById('s').innerHTML = window.ILLUS[n](); }, n);
  await page.evaluate(() => document.fonts.ready);
  await page.locator('#s svg').screenshot({ path: `assets/il_${n}.png`, omitBackground: true });
  console.log('rendered', n);
}
await browser.close();
