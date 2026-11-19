// usage: node capture.js <html> <outdir> <fps> <start_frame> <end_frame_excl> [times_csv]
const { chromium } = require('playwright');
const path=require('path');
(async()=>{
  const [html,out,fps,a,b,times]=process.argv.slice(2);
  const browser=await chromium.launch({args:['--force-color-profile=srgb','--disable-lcd-text']});
  const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
  await page.goto('file://'+path.resolve(html));
  await page.evaluate(()=>window.ready);
  await page.waitForTimeout(300);
  const list = times ? times.split(',').map(Number) : null;
  const frames = list ? list.map((t,i)=>({t,name:`test_${t.toFixed(2)}.jpg`})) :
    Array.from({length:+b-+a},(_,i)=>({t:(+a+i)/+fps,name:`f_${String(+a+i).padStart(5,'0')}.jpg`}));
  for(const f of frames){
    await page.evaluate(t=>window.renderAt(t),f.t);
    await page.screenshot({path:path.join(out,f.name),type:'jpeg',quality:94});
  }
  await browser.close();
})();
