/* KLOVA – collage motion graphic (1080x1920, 30fps). Timeline is driven by the SRT word timings. */
gsap.registerPlugin(MotionPathPlugin);
const FPS = 30, DUR = 20.8, LEAD = 0.03;

const C = {
  cream: '#F4EBDD', paper: '#FBF6EC', kraft: '#D2AE82', esp: '#2B1A12', coffee: '#6B4226',
  red: '#FF5A36', red2: '#E23B1E', mustard: '#FFC845', pink: '#BD9484', pinkL: '#EFC6B8',
  sage: '#8DB580', green: '#1F4B3A', sky: '#A8D8EA', lav: '#CDB8F0', ink: '#161210', white: '#FFFFFF',
};
const ST = {
  cream: { f: 'Cairo', w: 800, bg: C.cream, fg: C.esp },
  dark: { f: 'Lalezar', bg: C.esp, fg: C.cream },
  red: { f: 'Cairo', w: 900, bg: C.red, fg: '#FFF6E8' },
  mus: { f: 'Marhey', w: 700, bg: C.mustard, fg: C.esp },
  white: { f: 'Cairo', w: 900, bg: C.white, fg: C.red2 },
  pink: { f: 'Lemonada', w: 700, bg: C.pink, fg: C.esp },
  sage: { f: 'Blaka', bg: C.sage, fg: '#1E2B16' },
  ink: { f: 'ArefRuqaa', bg: C.ink, fg: C.mustard },
  lalR: { f: 'Lalezar', bg: C.red, fg: C.cream },
  lalM: { f: 'Lalezar', bg: C.mustard, fg: C.esp },
  lalW: { f: 'Lalezar', bg: C.white, fg: C.esp },
};
const DISP = [null, 'إذا', 'تسوّي', 'قهوتك', 'في', 'البيت', 'هذا', 'الفيديو', 'لك', 'حنا', 'كلوفا', 'متجر', 'متخصص', 'في', 'محاصيل', 'القهوة',
  'والفرق', 'غالباً', 'مو', 'في', 'المكينة', 'الفرق', 'في', 'المحصول', 'نفسه', 'عشان', 'كذا', 'نوفّر', 'لك', 'محاصيل', 'من', 'أكثر', 'من', 'بلد',
  'كل', 'واحد', 'له', 'طعمه', 'بدون', 'ما', 'تدفع', 'كل', 'يوم', 'في', 'الكوفيّات', 'وبدون', 'ما', 'تتنازل', 'عن', 'الطعم', 'اختار', 'محصولك', 'من', 'الرابط', 'بالبايو'];
const T = (i) => Math.max(0, SRT[i - 1].s - LEAD);

function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const R = mulberry32(20260926);
const rr = (a, b) => a + (b - a) * R();

const shakeEl = document.getElementById('shake');
const tl = gsap.timeline({ paused: true });
const CUES = [];
function sfx(t, name, gain = 1, o = {}) { CUES.push(Object.assign({ t: +Math.max(0, t).toFixed(3), name, gain }, o)); }

function el(tag, o = {}, parent = shakeEl) {
  const e = document.createElement(tag);
  if (o.cls) e.className = o.cls;
  if (o.text != null) e.textContent = o.text;
  if (o.html != null) e.innerHTML = o.html;
  if (o.style) Object.assign(e.style, o.style);
  if (o.attrs) for (const k in o.attrs) e.setAttribute(k, o.attrs[k]);
  parent.appendChild(e);
  return e;
}
function center(e, rot = 0) { gsap.set(e, { xPercent: -50, yPercent: -50, rotation: rot }); return e; }

// torn-paper polygon (mix of % and px so it works for any box size)
function jag(amt = 6, step = 6) {
  const p = [], J = () => (R() * amt * (R() < 0.12 ? 1.8 : 1)).toFixed(1);
  for (let x = 0; x <= 100.001; x += step) p.push(`${x.toFixed(2)}% ${J()}px`);
  for (let y = 0; y <= 100.001; y += step) p.push(`calc(100% - ${J()}px) ${y.toFixed(2)}%`);
  for (let x = 100; x >= -0.001; x -= step) p.push(`${x.toFixed(2)}% calc(100% - ${J()}px)`);
  for (let y = 100; y >= -0.001; y -= step) p.push(`${J()}px ${y.toFixed(2)}%`);
  return `polygon(${p.join(',')})`;
}
function outline(c, w) {
  const s = [];
  for (let a = 0; a < 16; a++) { const an = a / 16 * Math.PI * 2; s.push(`${(Math.cos(an) * w).toFixed(1)}px ${(Math.sin(an) * w).toFixed(1)}px 0 ${c}`); }
  return s.join(',');
}

// ---------- textures ----------
function noiseURL(w, h, fn) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); const id = g.createImageData(w, h);
  for (let i = 0; i < id.data.length; i += 4) { const v = fn(); id.data[i] = v[0]; id.data[i + 1] = v[1]; id.data[i + 2] = v[2]; id.data[i + 3] = 255; }
  g.putImageData(id, 0, 0);
  return [c, g];
}
function paperTex() {
  const [c, g] = noiseURL(600, 600, () => { const v = 232 + R() * 23; return [v, v - 3, v - 8]; });
  g.globalAlpha = 0.09;
  for (let k = 0; k < 700; k++) {
    g.strokeStyle = R() < 0.55 ? '#6b4a2a' : '#ffffff'; g.lineWidth = rr(0.5, 1.6);
    const x = rr(0, 600), y = rr(0, 600), a = rr(0, 6.28), l = rr(6, 34);
    g.beginPath(); g.moveTo(x, y);
    g.quadraticCurveTo(x + Math.cos(a) * l / 2 + rr(-5, 5), y + Math.sin(a) * l / 2 + rr(-5, 5), x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke();
  }
  g.globalAlpha = 0.05;
  for (let k = 0; k < 30; k++) {
    const x = rr(0, 600), y = rr(0, 600), r = rr(30, 110);
    const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, '#5a3a1a'); gr.addColorStop(1, 'rgba(90,58,26,0)');
    g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  return c.toDataURL('image/png');
}
document.documentElement.style.setProperty('--tex', `url(${paperTex()})`);
const grainEl = document.getElementById('grain');
const grains = [];
for (let k = 0; k < 4; k++) {
  const [c] = noiseURL(540, 960, () => { const v = 128 + (R() - 0.5) * 190; return [v, v, v]; });
  grains.push(el('div', { style: { backgroundImage: `url(${c.toDataURL('image/png')})` } }, grainEl));
}

// ---------- building blocks ----------
const scenes = [];
function makeScene(color, pattern) {
  const sc = el('div', { cls: 'scene' });
  el('div', { cls: 'fringe', style: { clipPath: jag(26, 1.1) } }, sc);
  const sh = el('div', { cls: 'sheet', style: { background: color, clipPath: jag(20, 1.3) } }, sc);
  if (pattern) el('div', { cls: 'pat', style: pattern }, sh);
  el('div', { cls: 'tex' }, sh);
  const content = el('div', { cls: 'content' }, sc);
  const s = { sc, sh, content };
  scenes.push(s);
  return s;
}
function enter(s, prev, t, from, dur = 0.24, ease = 'power3.out') {
  tl.set(s.sc, { visibility: 'visible', filter: 'drop-shadow(0px 0px 34px rgba(0,0,0,.5))' }, t);
  tl.fromTo(s.sc, Object.assign({ x: 0, y: 0, rotation: 0, scale: 1 }, from), { x: 0, y: 0, rotation: 0, scale: 1, duration: dur, ease }, t);
  tl.set(s.sc, { filter: 'none' }, t + dur + 0.02);
  if (prev) {
    const push = { duration: dur, ease: 'power2.in' };
    if (from.x) push.x = -from.x * 0.14;
    if (from.y) push.y = -from.y * 0.08;
    if (from.scale) push.scale = 1.25;
    tl.to(prev.content, push, t);
    tl.set(prev.sc, { visibility: 'hidden' }, t + dur + 0.03);
  }
  sfx(t - 0.08, 'whoosh', 0.5, { dur: 0.42, pan: from.x ? Math.sign(from.x) : 0 });
}
function camZoom(s, t0, t1, to = 1.055) { tl.fromTo(s.content, { scale: 1 }, { scale: to, duration: t1 - t0, ease: 'none', immediateRender: false }, t0); }

function block(parent, text, st, size, o = {}) {
  const w = el('div', { cls: 'bw' }, parent);
  const b = el('div', { cls: 'blk boil' + (o.lat ? ' lat' : ''), text }, w);
  Object.assign(b.style, { fontFamily: st.f, fontWeight: st.w || 400, background: st.bg, color: st.fg, fontSize: size + 'px', clipPath: jag(o.j || 5, o.js || 7) });
  return w;
}
function row(parent, x, y, gap = 16, o = {}) {
  const r = el('div', { cls: 'row', style: { left: x + 'px', top: y + 'px', gap: gap + 'px', direction: o.ltr ? 'ltr' : 'rtl' } }, parent);
  return center(r, o.rot || 0);
}
function popIn(e, t, o = {}) {
  const rot = o.rot ?? 0;
  const fr = o.fromRot ?? (rot + (R() < 0.5 ? -1 : 1) * rr(14, 26));
  tl.fromTo(e, { scale: o.from ?? 0, rotation: fr, autoAlpha: o.a0 ?? 0 },
    { scale: 1, rotation: rot, autoAlpha: 1, duration: o.dur ?? 0.32, ease: o.ease ?? 'back.out(2.4)' }, t);
  if (o.sfx !== null) sfx(t + (o.sfxOff ?? 0), o.sfx ?? 'pop', o.gain ?? 0.5, { pitch: o.pitch ?? rr(0.85, 1.3) });
}
function word(r, i, st, size, o = {}) {
  const w = block(r, o.text ?? DISP[i], st, size, o);
  const rot = o.rot ?? rr(-4.5, 4.5);
  popIn(w, o.t ?? T(i), Object.assign({}, o, { rot }));
  return w;
}
function shake(t, amp = 16, dur = 0.3) {
  const n = Math.round(dur * FPS);
  for (let k = 0; k < n; k++) {
    const d = 1 - k / n;
    tl.set(shakeEl, { x: rr(-1, 1) * amp * d, y: rr(-1, 1) * amp * d, rotation: rr(-1, 1) * amp * 0.05 * d }, t + k / FPS);
  }
  tl.set(shakeEl, { x: 0, y: 0, rotation: 0 }, t + n / FPS);
}
function flash(t, a = 0.45) { tl.fromTo('#flash', { opacity: a }, { opacity: 0, duration: 0.16, ease: 'power1.out', immediateRender: false }, t); }
function slam(e, t, o = {}) {
  const rot = o.rot ?? 0, d = o.dur ?? 0.17;
  tl.fromTo(e, { scale: o.from ?? 2.6, rotation: rot + (o.dr ?? -10), autoAlpha: 0 }, { scale: 1, rotation: rot, autoAlpha: 1, duration: d, ease: 'power3.in' }, t);
  shake(t + d, o.amp ?? 16, 0.3);
  if (o.sfx !== null) sfx(t + d - 0.01, o.sfx ?? 'stamp', o.gain ?? 0.75);
}
function sticker(parent, name, x, y, size, o = {}) {
  const w = el('div', { cls: 'abs stk', style: { left: x + 'px', top: y + 'px', width: size + 'px', height: (o.h ?? size) + 'px' } }, parent);
  el('img', { cls: 'boil', attrs: { src: o.src ?? `assets/emoji/${name}.svg` }, style: { filter: `url(#${size < 230 ? 'stkS' : 'stk'})` } }, w);
  return center(w, o.rot || 0);
}
function bigText(parent, text, x, y, size, o = {}) {
  const d = el('div', { cls: 'abs', style: { left: x + 'px', top: y + 'px' } }, parent);
  el('div', { cls: 'big boil', text, style: { fontFamily: o.f || 'Lalezar', fontSize: size + 'px', color: o.c || C.esp, textShadow: o.sh || '' } }, d);
  return center(d, o.rot || 0);
}
function tape(parent, x, y, rot, w = 190) {
  const t = el('div', { cls: 'tape', style: { left: x + 'px', top: y + 'px', width: w + 'px', clipPath: jag(5, 9) } }, parent);
  return center(t, rot);
}
function scribble(parent, x, y, w, h, d, color, sw, t, dur, o = {}) {
  const s = el('div', { cls: 'abs', style: { left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px' } }, parent);
  center(s, o.rot || 0);
  s.innerHTML = `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" style="overflow:visible"><path d="${d}" pathLength="1" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1 1" stroke-dashoffset="1"/></svg>`;
  tl.fromTo(s.querySelector('path'), { attr: { 'stroke-dashoffset': 1 } }, { attr: { 'stroke-dashoffset': 0 }, duration: dur, ease: o.ease || 'power1.inOut' }, t);
  if (o.sfx !== null) sfx(t, 'scribble', o.gain ?? 0.4, { dur: dur + 0.06 });
  return s;
}
// hand-drawn loop around an element (child of a .bw word wrapper); built after fonts load so it can be measured
const DEFER = [];
function circleAround(wrap, t, color = C.esp, dur = 0.42) {
  wrap.style.position = 'relative';
  const s = el('div', { style: { position: 'absolute', pointerEvents: 'none' } }, wrap);
  sfx(t, 'scribble', 0.4, { dur: dur + 0.05 });
  DEFER.push(() => {
    const W = wrap.offsetWidth * 1.3, H = wrap.offsetHeight * 1.7;
    Object.assign(s.style, { left: (-(W - wrap.offsetWidth) / 2) + 'px', top: (-(H - wrap.offsetHeight) / 2) + 'px', width: W + 'px', height: H + 'px' });
    const P = [[58, 6], [20, 4], [2, 30], [4, 55], [6, 84], [40, 97], [66, 94], [92, 90], [99, 62], [96, 40], [93, 16], [70, 3], [40, 9]].map(([x, y]) => `${(x * W / 100).toFixed(1)} ${(y * H / 100).toFixed(1)}`);
    const d = `M${P[0]} C ${P[1]}, ${P[2]}, ${P[3]} C ${P[4]}, ${P[5]}, ${P[6]} C ${P[7]}, ${P[8]}, ${P[9]} C ${P[10]}, ${P[11]}, ${P[12]}`;
    s.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" style="overflow:visible"><path d="${d}" pathLength="1" fill="none" stroke="${color}" stroke-width="12" stroke-linecap="round" stroke-dasharray="1 1" stroke-dashoffset="1"/></svg>`;
    tl.fromTo(s.querySelector('path'), { attr: { 'stroke-dashoffset': 1 } }, { attr: { 'stroke-dashoffset': 0 }, duration: dur, ease: 'power1.inOut' }, t);
  });
}
function burst(parent, x, y, t, color, r0 = 170, r1 = 320, n = 14, sw = 16) {
  const size = r1 * 2 + 60, c = size / 2;
  const s = el('div', { cls: 'abs', style: { left: x + 'px', top: y + 'px', width: size + 'px', height: size + 'px' } }, parent);
  center(s);
  let lines = '';
  for (let k = 0; k < n; k++) {
    const a = k / n * Math.PI * 2 + rr(-0.12, 0.12), a0 = r0 * rr(0.9, 1.1), a1 = r1 * rr(0.8, 1.05);
    lines += `<line x1="${(c + Math.cos(a) * a0).toFixed(1)}" y1="${(c + Math.sin(a) * a0).toFixed(1)}" x2="${(c + Math.cos(a) * a1).toFixed(1)}" y2="${(c + Math.sin(a) * a1).toFixed(1)}"/>`;
  }
  s.innerHTML = `<svg width="${size}" height="${size}"><g stroke="${color}" stroke-width="${sw}" stroke-linecap="round">${lines}</g></svg>`;
  tl.fromTo(s, { scale: 0.45, autoAlpha: 0 }, { scale: 1.2, autoAlpha: 1, duration: 0.2, ease: 'power2.out' }, t);
  tl.to(s, { autoAlpha: 0, duration: 0.22 }, t + 0.24);
  return s;
}
function bob(e, t, amp = 12, dur = 0.8, rep = 3) { tl.to(e, { y: `-=${amp}`, duration: dur, yoyo: true, repeat: rep, ease: 'sine.inOut' }, t); }
function bagSVG() {
  const id = 'b' + Math.floor(R() * 1e7);
  let crimp = '';
  for (let x = 40; x <= 360; x += 13) crimp += `M${x} 16v36`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 560" width="100%" height="100%" style="overflow:visible">
<defs><linearGradient id="${id}k" x1="0" x2="1"><stop offset="0" stop-color="#a97f52"/><stop offset=".14" stop-color="#d1a878"/><stop offset=".5" stop-color="#ddb88a"/><stop offset=".86" stop-color="#cda272"/><stop offset="1" stop-color="#9c7447"/></linearGradient></defs>
<path d="M28 44 L372 44 L386 518 Q388 550 356 552 L44 552 Q12 550 14 518 Z" fill="url(#${id}k)" stroke="#2B1A12" stroke-width="7" stroke-linejoin="round"/>
<rect x="22" y="10" width="356" height="46" rx="8" fill="#c79d6e" stroke="#2B1A12" stroke-width="7"/>
<path d="${crimp}" stroke="#8a643d" stroke-width="3"/>
<rect x="16" y="66" width="368" height="14" rx="7" fill="#aab2b9" stroke="#2B1A12" stroke-width="4"/>
<path d="M34 100 H366" stroke="#8a643d" stroke-width="4" stroke-dasharray="12 8"/>
<circle cx="326" cy="146" r="17" fill="#efe4d0" stroke="#2B1A12" stroke-width="5"/><circle cx="326" cy="146" r="6" fill="#2B1A12"/>
<g transform="rotate(-2 200 330)">
<rect x="66" y="186" width="268" height="300" rx="20" fill="#F4EBDD" stroke="#2B1A12" stroke-width="6"/>
<path d="M66 206 Q66 186 86 186 H314 Q334 186 334 206 V258 H66 Z" fill="#BD9484" stroke="#2B1A12" stroke-width="6"/>
<text x="200" y="244" text-anchor="middle" font-family="Anton" font-size="50" fill="#2B1A12" letter-spacing="8">KLOVA</text>
<text x="200" y="350" text-anchor="middle" font-family="Lalezar" font-size="92" fill="#2B1A12">كلوفا</text>
<text x="200" y="402" text-anchor="middle" font-family="Cairo" font-weight="800" font-size="29" fill="#6B4226">محاصيل قهوة مختصة</text>
<path d="M110 424 H290" stroke="#2B1A12" stroke-width="3" stroke-dasharray="4 6"/>
<text x="200" y="464" text-anchor="middle" font-family="Anton" font-size="23" fill="#2B1A12" letter-spacing="5">SPECIALTY COFFEE</text>
</g>
<path d="M44 110 Q 58 320 40 530" stroke="#fff" stroke-opacity=".3" stroke-width="12" fill="none" stroke-linecap="round"/>
</svg>`;
}
function bag(parent, x, y, w) {
  const b = el('div', { cls: 'abs', style: { left: x + 'px', top: y + 'px', width: w + 'px', height: (w * 1.4) + 'px', filter: 'drop-shadow(12px 16px 0 rgba(0,0,0,.28))' } }, parent);
  el('div', { cls: 'boil', html: bagSVG(), style: { width: '100%', height: '100%' } }, b);
  tape(b, w * 0.16, w * 0.06, -32, 150);
  tape(b, w * 0.84, w * 0.06, 32, 150);
  return center(b);
}
const halftone = (c, s = 30, r = 26) => ({ backgroundImage: `radial-gradient(circle, ${c} ${r}%, transparent ${r + 3}%)`, backgroundSize: `${s}px ${s}px` });
const masked = (o, m) => Object.assign(o, { maskImage: m, webkitMaskImage: m });

/* =================== SCENE 1 (0.00 – 1.84) "إذا تسوّي قهوتك في البيت" =================== */
const s1 = makeScene(C.kraft, masked(halftone('rgba(107,66,38,.25)', 28, 22), 'linear-gradient(160deg,#000 0%,transparent 42%,transparent 70%,#000 100%)'));
gsap.set(s1.sc, { visibility: 'visible' });
camZoom(s1, 0, 2.1, 1.06);
{
  const c = s1.content;
  const disc = center(el('div', { cls: 'abs', style: Object.assign({ left: '540px', top: '840px', width: '840px', height: '840px', borderRadius: '50%', backgroundColor: C.mustard, boxShadow: `0 0 0 14px ${C.esp}` }, halftone('#F2A922', 30, 30)) }, c));
  tl.fromTo(disc, { scale: 0.8, rotation: -30 }, { scale: 1, rotation: 0, duration: 0.5, ease: 'back.out(1.8)' }, 0);
  tl.to(disc, { rotation: 22, duration: 1.4, ease: 'none' }, 0.5);
  [[170, 560, 110, -30], [915, 600, 95, 25], [150, 1000, 90, 60], [930, 1010, 105, -10]].forEach(([x, y, s, r], k) => {
    const b = sticker(c, null, x, y, s, { src: 'assets/bean.svg', h: s * 1.3, rot: r });
    popIn(b, 0.08 + k * 0.12, { rot: r, sfx: null });
  });
  const cup = sticker(c, 'hot-beverage', 540, 830, 560, { rot: -4 });
  tl.fromTo(cup, { scale: 0.7, rotation: -14 }, { scale: 1, rotation: -4, duration: 0.7, ease: 'elastic.out(1,.45)' }, 0);
  tl.to(cup, { scaleX: 1.14, scaleY: 0.88, duration: 0.07, ease: 'power2.out' }, T(3));
  tl.to(cup, { scaleX: 1, scaleY: 1, duration: 0.45, ease: 'elastic.out(1,.35)' }, T(3) + 0.07);
  sfx(0, 'impact', 0.55);
  const r1 = row(c, 540, 300, 14);
  word(r1, 1, ST.cream, 112, { rot: -4, t: 0, from: 0.7, a0: 1, fromRot: -14, gain: 0.45, pitch: 1 });
  word(r1, 2, ST.dark, 124, { rot: 3 });
  const q = word(r1, 3, ST.lalR, 156, { rot: -3, pitch: 1.35 });
  sfx(T(3), 'sparkle', 0.22);
  const strip = center(el('div', { cls: 'abs', style: { left: '540px', top: '1330px', width: '1400px', height: '230px', background: C.paper, clipPath: jag(10, 2) } }, c), -8);
  tl.fromTo(strip, { x: -1450 }, { x: 0, duration: 0.3, ease: 'power3.out' }, 1.0);
  sfx(0.98, 'swish', 0.35);
  const house = sticker(c, 'house-with-garden', 235, 1120, 250, { rot: -10 });
  popIn(house, T(5) + 0.02, { rot: -10, sfx: null });
  const r2 = row(c, 560, 1330, 16, { rot: -8 });
  word(r2, 4, ST.white, 92, { rot: 2 });
  word(r2, 5, ST.lalM, 164, { rot: -2, pitch: 0.9 });
  const qm = bigText(c, '؟', 830, 1070, 330, { c: C.mustard, sh: outline(C.esp, 9) + `,14px 16px 0 ${C.esp}`, rot: 14 });
  popIn(qm, T(5) + 0.14, { rot: 14, ease: 'elastic.out(1,.4)', dur: 0.6, sfx: 'boing', gain: 0.4, pitch: 1 });
}

/* =================== SCENE 2 (1.84 – 3.16) "هذا الفيديو لك" =================== */
const s2 = makeScene(C.red, masked(halftone('rgba(255,246,232,.32)', 34, 28), 'linear-gradient(20deg,#000 0%,transparent 45%)'));
enter(s2, s1, 1.84, { x: 1250, rotation: 7 });
camZoom(s2, 1.84, 3.4, 1.05);
{
  const c = s2.content;
  const rays = center(el('div', { cls: 'abs', style: { left: '540px', top: '930px', width: '2800px', height: '2800px', borderRadius: '50%', background: 'repeating-conic-gradient(rgba(255,255,255,.0) 0deg 6deg, rgba(255,230,210,.16) 6deg 12deg)' } }, c));
  tl.fromTo(rays, { rotation: 0 }, { rotation: 18, duration: 1.6, ease: 'none', immediateRender: false }, 1.84);
  const f = sticker(c, 'index-pointing-at-the-viewer', 540, 900, 600);
  tl.fromTo(f, { scale: 0.2, rotation: -25, autoAlpha: 0 }, { scale: 0.55, rotation: -6, autoAlpha: 1, duration: 0.22, ease: 'back.out(2)' }, 1.92);
  tl.to(f, { scale: 0.98, rotation: 3, duration: 0.56, ease: 'power2.in' }, 2.14);
  sfx(1.94, 'pop', 0.4, { pitch: 0.7 });
  tl.to(f, { scale: 1.12, duration: 0.06, ease: 'power2.out' }, 2.7);
  tl.to(f, { scale: 1, duration: 0.4, ease: 'elastic.out(1,.4)' }, 2.76);
  const ra = row(c, 540, 290, 14);
  word(ra, 6, ST.cream, 112, { rot: -3 });
  const rb = row(c, 540, 440, 14);
  word(rb, 7, ST.dark, 142, { rot: 2, pitch: 1.1 });
  const clap = sticker(c, 'clapper-board', 190, 400, 190, { rot: -14 });
  popIn(clap, T(7) + 0.04, { rot: -14, sfx: 'shutter', gain: 0.35 });
  burst(c, 540, 1380, 2.7, C.cream, 190, 360, 16, 18);
  const rl = row(c, 540, 1380, 0, { rot: -6 });
  const lk = block(rl, 'لك', { f: 'Lalezar', bg: C.mustard, fg: C.esp }, 270, { j: 9 });
  slam(lk, 2.53, { rot: 0, amp: 22, sfx: 'stamp', gain: 0.8 });
  sfx(2.7, 'impact', 0.45);
  flash(2.7, 0.35);
}

/* =================== SCENE 3 (3.16 – 6.18) "حنا كلوفا متجر متخصص في محاصيل القهوة" =================== */
const s3 = makeScene(C.cream, { backgroundImage: 'linear-gradient(rgba(60,120,200,.16) 2px, transparent 2px), linear-gradient(90deg, rgba(60,120,200,.16) 2px, transparent 2px)', backgroundSize: '60px 60px' });
enter(s3, s2, 3.16, { y: -2150, rotation: -4 });
camZoom(s3, 3.16, 6.4, 1.05);
{
  const c = s3.content;
  // falling beans (behind everything)
  for (let k = 0; k < 20; k++) {
    const s = rr(55, 105), x = rr(40, 1040), t0 = 3.62 + rr(0, 0.9), r0 = rr(-180, 180);
    const b = sticker(c, null, x, -120, s, { src: 'assets/bean.svg', h: s * 1.3, rot: r0 });
    tl.fromTo(b, { y: 0, rotation: r0 }, { y: 2150, rotation: r0 + rr(-360, 360), duration: rr(0.9, 1.4), ease: 'power1.in' }, t0);
  }
  sfx(3.7, 'rattle', 0.28, { dur: 1.0 });
  const bg = bag(c, 540, 1000, 390);
  tl.fromTo(bg, { y: 1300, rotation: 10 }, { y: 0, rotation: -3, duration: 0.42, ease: 'back.out(1.3)' }, 3.24);
  sfx(3.22, 'swish', 0.35); sfx(3.6, 'thud', 0.45);
  bob(bg, 3.8, 10, 0.9, 2);
  const rh = row(c, 815, 240, 0, { rot: -7 });
  word(rh, 9, ST.white, 86, { rot: 0 });
  const kl = bigText(c, 'كلوفا', 520, 410, 250, { c: C.esp, sh: `12px 12px 0 ${C.red}`, rot: -3 });
  slam(kl, T(10) - 0.14, { rot: -3, amp: 18, sfx: 'impact', gain: 0.6 });
  flash(T(10) + 0.03, 0.25);
  sfx(T(10) + 0.05, 'sparkle', 0.3);
  const rk = row(c, 540, 620, 12, { ltr: true });
  const L = [['K', 'Anton', C.mustard, C.esp], ['L', 'Abril', C.esp, C.cream], ['O', 'Bungee', C.red, C.cream], ['V', 'Shrikhand', C.white, C.esp], ['A', 'Anton', C.sage, C.esp]];
  L.forEach(([ch, f, bgc, fg], k) => {
    const w = block(rk, ch, { f, bg: bgc, fg }, 92, { lat: true, j: 4 });
    const r = rr(-9, 9);
    popIn(w, T(10) + 0.12 + k * 0.075, { rot: r, from: 0, pitch: [1, 1.12, 1.26, 1.33, 1.5][k], gain: 0.38 });
  });
  const sd = sticker(c, 'seedling', 185, 1120, 180, { rot: -8 });
  popIn(sd, 4.02, { rot: -8, gain: 0.3 });
  const bn = sticker(c, 'beans', 895, 1150, 180, { rot: 12 });
  popIn(bn, 4.16, { rot: 12, gain: 0.3 });
  const s1r = row(c, 540, 1350, 14, { rot: -2 });
  sfx(T(11) - 0.02, 'rip', 0.35);
  word(s1r, 11, ST.red, 92, { rot: 2 });
  word(s1r, 12, ST.dark, 96, { rot: -2 });
  const s2r = row(c, 540, 1470, 12, { rot: 1.5 });
  word(s2r, 13, ST.white, 64, { rot: 3 });
  word(s2r, 14, ST.mus, 96, { rot: -2 });
  const qh = word(s2r, 15, ST.lalR, 100, { rot: 2, pitch: 1.3 });
  scribble(c, 450, 1552, 600, 50, 'M10 32 C 120 6, 220 50, 330 24 S 500 8, 590 30', C.esp, 12, T(14) + 0.05, 0.5, { rot: 1.5 });
  sfx(T(15) + 0.05, 'ding', 0.25, { pitch: 1.2 });
}

/* =================== SCENE 4 (6.18 – 8.34) "والفرق غالباً مو في المكينة" =================== */
const s4 = makeScene(C.esp, masked(halftone('rgba(255,235,210,.10)', 30, 30), 'radial-gradient(circle at 50% 50%, transparent 30%, #000 80%)'));
enter(s4, s3, 6.18, { y: 2150, rotation: 4 });
camZoom(s4, 6.18, 8.6, 1.06);
{
  const c = s4.content;
  center(el('div', { cls: 'abs', style: { left: '540px', top: '960px', width: '1000px', height: '1000px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,200,69,.28), rgba(255,200,69,0) 65%)' } }, c));
  const m = sticker(c, null, 540, 960, 640, { src: 'assets/machine.svg', h: 555 });
  tl.fromTo(m, { y: 1250, rotation: -6 }, { y: 0, rotation: 0, duration: 0.32, ease: 'back.out(1.2)' }, 6.24);
  sfx(6.22, 'swish', 0.3); sfx(6.52, 'thud', 0.55);
  const ra = row(c, 540, 280, 14);
  word(ra, 16, ST.cream, 116, { rot: -3 });
  const rb = row(c, 570, 430, 14, { rot: 4 });
  word(rb, 17, ST.lalM, 124, { rot: 0 });
  const th = sticker(c, 'thinking-face', 185, 430, 190, { rot: -10 });
  popIn(th, T(17) + 0.06, { rot: -10, gain: 0.3, pitch: 0.8 });
  scribble(c, 540, 960, 560, 520, 'M40 50 Q 260 250 520 470', '#FF3B2F', 40, T(18), 0.13, { ease: 'power2.out', gain: 0.45 });
  scribble(c, 540, 960, 560, 520, 'M515 45 Q 300 230 45 480', '#FF3B2F', 40, T(18) + 0.14, 0.13, { ease: 'power2.out', sfx: null });
  sfx(T(18) + 0.02, 'buzzer', 0.4);
  tl.set(m.querySelector('img'), { filter: 'url(#stk) grayscale(1) brightness(.72)' }, T(18) + 0.1);
  tl.to(m, { rotation: -5, duration: 0.3, ease: 'back.out(3)' }, T(18) + 0.1);
  shake(T(18) + 0.1, 12, 0.25);
  const rc = row(c, 540, 1400, 14, { rot: -2 });
  word(rc, 18, ST.lalR, 150, { rot: -4, pitch: 0.8 });
  word(rc, 19, ST.white, 72, { rot: 3 });
  word(rc, 20, ST.cream, 122, { rot: -1 });
}

/* =================== SCENE 5 (8.34 – 10.28) "الفرق في المحصول نفسه" =================== */
const s5 = makeScene(C.mustard, null);
enter(s5, s4, 8.34, { scale: 0.12, rotation: -120 }, 0.3);
camZoom(s5, 8.34, 10.6, 1.06);
{
  const c = s5.content;
  const sun = center(el('div', { cls: 'abs', style: { left: '540px', top: '930px', width: '2800px', height: '2800px', borderRadius: '50%', background: 'repeating-conic-gradient(#FFC845 0deg 8deg, #FFD978 8deg 16deg)' } }, c));
  tl.fromTo(sun, { rotation: 0 }, { rotation: 30, duration: 2.3, ease: 'none', immediateRender: false }, 8.34);
  const ch = sticker(c, null, 560, 930, 720, { src: 'assets/cherries.svg', h: 630, rot: -4 });
  popIn(ch, 8.44, { rot: -4, fromRot: -30, ease: 'elastic.out(1,.55)', dur: 0.7, gain: 0.4, pitch: 0.75 });
  bob(ch, 9.1, 10, 0.6, 1);
  [[235, 1190, 120, -20], [345, 1245, 105, 40], [170, 1290, 100, 80]].forEach(([x, y, s, r], k) => {
    const b = sticker(c, null, x, y, s, { src: 'assets/bean.svg', h: s * 1.3, rot: r });
    popIn(b, 8.62 + k * 0.08, { rot: r, sfx: 'click', gain: 0.3 });
  });
  const mg = sticker(c, 'magnifying-glass-tilted-left', 720, 820, 300, { rot: 8 });
  tl.fromTo(mg, { x: 420, y: 520, autoAlpha: 0, rotation: 40 }, { x: 0, y: 0, autoAlpha: 1, rotation: 8, duration: 0.36, ease: 'back.out(1.6)' }, 9.0);
  sfx(8.98, 'swish', 0.3);
  bob(mg, 9.4, 14, 0.4, 1);
  const sp1 = sticker(c, 'sparkles', 880, 620, 150, { rot: 10 });
  const sp2 = sticker(c, 'sparkles', 210, 740, 130, { rot: -12 });
  popIn(sp1, T(23) + 0.06, { rot: 10, sfx: null }); popIn(sp2, T(23) + 0.14, { rot: -12, sfx: null });
  sfx(T(23) + 0.05, 'sparkle', 0.35);
  const ra = row(c, 540, 245, 14);
  word(ra, 21, ST.dark, 118, { rot: -3 });
  const rb = row(c, 540, 450, 34, { rot: 2 });
  word(rb, 22, ST.white, 72, { rot: 4 });
  const mh = word(rb, 23, ST.lalR, 150, { rot: -2, pitch: 1.2 });
  circleAround(mh, T(23) + 0.12, C.esp, 0.45);
  const rc = row(c, 450, 1420, 0, { rot: -3 });
  word(rc, 24, ST.dark, 140, { rot: 0 });
  const ck = sticker(c, 'check-mark-button', 790, 1410, 200, { rot: 10 });
  slam(ck, T(24) + 0.02, { rot: 10, amp: 12, sfx: 'stamp', gain: 0.6 });
  sfx(T(24) + 0.2, 'ding', 0.35, { pitch: 1 });
}

/* =================== SCENE 6 (10.28 – 13.00) "عشان كذا نوفّر لك محاصيل من أكثر من بلد" =================== */
const s6 = makeScene(C.sky, halftone('rgba(255,255,255,.35)', 40, 12));
enter(s6, s5, 10.28, { x: -1250, rotation: -6 });
camZoom(s6, 10.28, 13.2, 1.05);
{
  const c = s6.content;
  const map = sticker(c, 'world-map', 540, 900, 880, { rot: -3 });
  popIn(map, 10.34, { rot: -3, from: 0.55, fromRot: -12, dur: 0.4, ease: 'back.out(1.6)', sfx: null });
  // flight path: dotted trail + plane
  const P0 = { x: 90, y: 1470 }, P1 = { x: 300, y: 820 }, P2 = { x: 760, y: 1250 }, P3 = { x: 1000, y: 470 };
  const bez = (t) => { const u = 1 - t; return { x: u * u * u * P0.x + 3 * u * u * t * P1.x + 3 * u * t * t * P2.x + t * t * t * P3.x, y: u * u * u * P0.y + 3 * u * u * t * P1.y + 3 * u * t * t * P2.y + t * t * t * P3.y }; };
  const fly0 = 10.5, fly1 = 12.9, ND = 44;
  for (let k = 1; k < ND; k++) {
    const p = bez(k / ND);
    const d = center(el('div', { cls: 'abs', style: { left: p.x + 'px', top: p.y + 'px', width: '16px', height: '16px', borderRadius: '50%', background: C.white, boxShadow: `0 0 0 4px ${C.esp}` } }, c));
    gsap.set(d, { autoAlpha: 0 });
    tl.set(d, { autoAlpha: 1 }, fly0 + (k / ND) * (fly1 - fly0));
  }
  const plane = sticker(c, 'airplane', 0, 0, 170);
  const pr = { p: 0 };
  const placePlane = () => { const a = bez(pr.p), b = bez(Math.min(1, pr.p + 0.01)); const ang = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI; gsap.set(plane, { x: a.x, y: a.y, rotation: ang + 45 }); };
  gsap.set(plane, { autoAlpha: 0 });
  tl.set(plane, { autoAlpha: 1 }, fly0);
  tl.to(pr, { p: 1, duration: fly1 - fly0, ease: 'none', onUpdate: placePlane }, fly0);
  placePlane();
  sfx(fly0, 'flyby', 0.22, { dur: 1.6 });
  const cards = [['et', 'إثيوبيا', 230, 640, -8], ['co', 'كولومبيا', 830, 690, 7], ['br', 'البرازيل', 320, 1070, 5], ['ye', 'اليمن', 650, 900, -5],
    ['ke', 'كينيا', 820, 1120, -8], ['rw', 'رواندا', 560, 1280, 6], ['gt', 'غواتيمالا', 170, 1290, -6]];
  const ct = [10.63, 10.86, 11.17, 11.4, 11.77, 12.0, 12.3];
  const pent = [1, 1.125, 1.25, 1.5, 1.667, 2, 2.25];
  cards.forEach(([code, name, x, y, r], k) => {
    const cd = el('div', { cls: 'card', style: { left: x + 'px', top: y + 'px' } }, c);
    el('img', { attrs: { src: `node_modules/flag-icons/flags/4x3/${code}.svg` } }, cd);
    el('div', { text: name }, cd);
    tape(cd, 106, 2, rr(-10, 10), 110);
    center(cd, r);
    popIn(cd, ct[k], { rot: r, pitch: pent[k] * 0.8, gain: 0.42 });
    sfx(ct[k] + 0.05, 'stamp', 0.18);
  });
  const ra = row(c, 540, 250, 14);
  word(ra, 25, ST.cream, 92, { rot: -3 });
  word(ra, 26, ST.dark, 92, { rot: 2 });
  const rb = row(c, 540, 390, 14, { rot: -1.5 });
  word(rb, 27, ST.red, 106, { rot: 2 });
  word(rb, 28, ST.white, 86, { rot: -3 });
  word(rb, 29, ST.lalM, 122, { rot: 1 });
  const rc = row(c, 540, 1500, 12, { rot: -2 });
  word(rc, 30, ST.white, 74, { rot: 3 });
  word(rc, 31, ST.dark, 118, { rot: -2 });
  word(rc, 32, ST.white, 74, { rot: 2 });
  const bl = word(rc, 33, ST.lalR, 142, { rot: -4, pitch: 1.4 });
  sfx(T(33) + 0.06, 'ding', 0.3, { pitch: 1.5 });
}

/* =================== SCENE 7 (13.00 – 14.50) "كل واحد له طعمه" =================== */
const s7 = makeScene(C.lav, halftone('rgba(255,255,255,.4)', 32, 24));
enter(s7, s6, 13.0, { x: 900, y: -1500, rotation: 12 });
camZoom(s7, 13.0, 14.8, 1.06);
{
  const c = s7.content;
  const cup = sticker(c, 'hot-beverage', 540, 970, 430, { rot: 4 });
  popIn(cup, 13.06, { rot: 4, from: 0.5, dur: 0.4, sfx: null });
  const fl = [['strawberry', 'فواكه', 215, 770, -10, T(34), ST.lalR], ['chocolate-bar', 'شوكولاتة', 855, 750, 9, T(35), ST.dark],
    ['cherry-blossom', 'زهور', 205, 1190, 7, T(36), ST.pink], ['lemon', 'حمضيات', 860, 1180, -8, 14.1, ST.mus], ['honey-pot', 'عسل', 540, 1395, 4, 14.3, ST.lalW]];
  fl.forEach(([name, label, x, y, r, t, st], k) => {
    const g = el('div', { cls: 'abs', style: { left: x + 'px', top: y + 'px', display: 'flex', flexDirection: 'column', alignItems: 'center' } }, c);
    const im = el('div', { style: { width: '180px', height: '180px' } }, g);
    el('img', { cls: 'boil', attrs: { src: `assets/emoji/${name}.svg` }, style: { width: '100%', height: '100%', filter: 'url(#stkS)' } }, im);
    const lb = block(g, label, st, 46, { j: 4 });
    lb.style.marginTop = '-14px';
    center(g, r);
    popIn(g, t, { rot: r, pitch: [1, 1.12, 1.25, 1.5, 1.68][k], gain: 0.42 });
  });
  const ra = row(c, 540, 245, 14);
  word(ra, 34, ST.cream, 96, { rot: -3, sfx: null });
  word(ra, 35, ST.dark, 104, { rot: 2, sfx: null });
  word(ra, 36, ST.white, 84, { rot: -2, sfx: null });
  const tm = bigText(c, 'طعمه', 490, 490, 220, { f: 'ArefRuqaa', c: C.red2, sh: outline(C.cream, 8) + `,12px 14px 0 ${C.esp}`, rot: -5 });
  slam(tm, T(37) - 0.12, { rot: -5, amp: 12, sfx: 'impact', gain: 0.4, from: 2.2 });
  sfx(T(37) + 0.06, 'sparkle', 0.3);
  const yum = sticker(c, 'face-savoring-food', 860, 470, 170, { rot: 12 });
  popIn(yum, T(37) + 0.14, { rot: 12, sfx: null });
}

/* =================== SCENE 8 (14.50 – 16.64) "بدون ما تدفع كل يوم في الكوفيّات" =================== */
const s8 = makeScene(C.green, halftone('rgba(255,246,232,.10)', 30, 26));
enter(s8, s7, 14.5, { y: 2150, rotation: -4 });
camZoom(s8, 14.5, 16.9, 1.05);
{
  const c = s8.content;
  const slot = center(el('div', { cls: 'abs', style: { left: '540px', top: '392px', width: '680px', height: '46px', borderRadius: '23px', background: '#111', boxShadow: `0 8px 0 rgba(0,0,0,.35), inset 0 0 0 5px #333` } }, c));
  popIn(slot, 14.56, { rot: 0, fromRot: 0, sfx: null });
  const rc = el('div', { cls: 'receipt', style: { clipPath: 'polygon(0 0,100% 0,100% calc(100% - 22px),95% 100%,90% calc(100% - 22px),85% 100%,80% calc(100% - 22px),75% 100%,70% calc(100% - 22px),65% 100%,60% calc(100% - 22px),55% 100%,50% calc(100% - 22px),45% 100%,40% calc(100% - 22px),35% 100%,30% calc(100% - 22px),25% 100%,20% calc(100% - 22px),15% 100%,10% calc(100% - 22px),5% 100%,0 calc(100% - 22px))' } }, c);
  rc.innerHTML = `<div class="in">
   <div style="text-align:center;font-weight:900;font-size:50px;line-height:1.4">فاتورة الكوفي ☕</div>
   <div style="text-align:center;font-size:30px;opacity:.7;font-family:Elite,Cairo">#0001 — كل يوم</div>
   <div class="hr"></div>
   <div class="ln"><span>لاتيه</span><span>٢٤ ر.س</span></div>
   <div class="ln"><span>سبانش لاتيه</span><span>٢٦ ر.س</span></div>
   <div class="ln"><span>V60</span><span>٢٨ ر.س</span></div>
   <div class="ln"><span>كورتادو</span><span>٢٢ ر.س</span></div>
   <div class="hr"></div>
   <div class="ln" style="font-weight:900;font-size:46px"><span>× ٣٠ يوم</span><span style="color:#E23B1E">💸💸💸</span></div>
  </div>`;
  tl.fromTo(rc, { height: 0 }, { height: 800, duration: 1.2, ease: 'steps(16)' }, 14.64);
  sfx(14.64, 'printer', 0.32, { dur: 1.2 });
  const ra = row(c, 540, 245, 14);
  word(ra, 38, ST.cream, 104, { rot: -3 });
  word(ra, 39, ST.white, 76, { rot: 3 });
  word(ra, 40, ST.lalR, 124, { rot: -2 });
  sfx(T(41) - 0.03, 'chaching', 0.5);
  sfx(T(41) + 0.05, 'flutter', 0.28, { dur: 0.7 });
  [[165, 560, -20, 190], [910, 520, 18, 170], [900, 1230, 10, 160]].forEach(([x, y, r, s], k) => {
    const mo = sticker(c, 'money-with-wings', 540, 820, s, { rot: r });
    tl.fromTo(mo, { x: 0, y: 0, scale: 0.2, autoAlpha: 0, rotation: 0 }, { x: x - 540, y: y - 820, scale: 1, autoAlpha: 1, rotation: r, duration: 0.55, ease: 'power2.out' }, T(41) + k * 0.06);
    bob(mo, T(41) + 0.6, 16, 0.35, 1);
  });
  const rb = row(c, 540, 1330, 30, { rot: 2 });
  word(rb, 41, ST.mus, 100, { rot: -2, sfx: null });
  word(rb, 42, ST.dark, 110, { rot: 3 });
  const rc2 = row(c, 540, 1465, 12, { rot: -2 });
  word(rc2, 43, ST.white, 72, { rot: 3 });
  word(rc2, 44, ST.lalR, 124, { rot: -2 });
  const no = sticker(c, 'prohibited', 540, 820, 400, { rot: -10 });
  slam(no, T(44) + 0.04, { rot: -10, amp: 18, sfx: 'stamp', gain: 0.8 });
  sfx(T(44) + 0.22, 'buzzer', 0.28, { pitch: 0.8 });
}

/* =================== SCENE 9 (16.64 – 18.64) "وبدون ما تتنازل عن الطعم" =================== */
const s9 = makeScene(C.pinkL, halftone('rgba(189,148,132,.35)', 30, 26));
enter(s9, s8, 16.64, { x: 1250, rotation: -6 });
camZoom(s9, 16.64, 18.9, 1.06);
{
  const c = s9.content;
  const halo = center(el('div', { cls: 'abs', style: Object.assign({ left: '540px', top: '930px', width: '760px', height: '760px', borderRadius: '50%', backgroundColor: C.white, boxShadow: `0 0 0 12px ${C.esp}` }, halftone('rgba(255,90,54,.25)', 26, 24)) }, c));
  popIn(halo, 16.68, { rot: 0, from: 0.4, dur: 0.35, sfx: null });
  tl.to(halo, { rotation: 20, duration: 1.8, ease: 'none' }, 16.9);
  const cup = sticker(c, 'hot-beverage', 540, 930, 480, { rot: -4 });
  popIn(cup, 16.74, { rot: -4, from: 0.4, dur: 0.45, ease: 'elastic.out(1,.5)', sfx: 'pop', pitch: 0.7, gain: 0.35 });
  for (let k = 0; k < 6; k++) {
    const x = rr(380, 720), s = rr(80, 120), t0 = 17.15 + k * 0.22;
    const h = sticker(c, 'red-heart', x, 760, s, { rot: rr(-20, 20) });
    gsap.set(h, { autoAlpha: 0 });
    tl.fromTo(h, { y: 0, scale: 0.3, autoAlpha: 1 }, { y: -rr(330, 430), scale: 1, duration: 0.9, ease: 'power1.out', immediateRender: false }, t0);
    tl.to(h, { autoAlpha: 0, duration: 0.25 }, t0 + 0.7);
  }
  const ra = row(c, 540, 250, 26);
  word(ra, 45, ST.dark, 110, { rot: -3 });
  word(ra, 46, ST.white, 76, { rot: 3 });
  const rb = row(c, 520, 405, 0, { rot: -2 });
  word(rb, 47, ST.lalR, 140, { rot: 0 });
  const stars = [];
  for (let k = 0; k < 5; k++) {
    const s = sticker(c, 'star', 540 + (k - 2) * 150, 1255 - (k === 2 ? 20 : k % 2 ? 8 : 0), 130, { rot: rr(-12, 12) });
    popIn(s, 17.4 + k * 0.15, { rot: rr(-10, 10), sfx: 'ding', pitch: [1, 1.125, 1.25, 1.5, 1.667][k] * 0.9, gain: 0.26 });
  }
  burst(c, 490, 1455, T(49) + 0.12, C.esp, 200, 290, 12, 12);
  const rc = row(c, 540, 1455, 22, { rot: -2 });
  word(rc, 48, ST.white, 76, { rot: 3 });
  const tt = word(rc, 49, ST.ink, 128, { rot: -3, pitch: 1.3 });
  sfx(T(49) + 0.08, 'sparkle', 0.35);
  const ch = sticker(c, 'smiling-face-with-heart-eyes', 865, 590, 180, { rot: 12 });
  popIn(ch, T(49) + 0.1, { rot: 12, sfx: null });
}

/* =================== SCENE 10 (18.64 – 20.80) "اختار محصولك من الرابط بالبايو" =================== */
const s10 = makeScene(C.kraft, masked(halftone('rgba(107,66,38,.22)', 28, 22), 'linear-gradient(200deg,#000 0%,transparent 40%,transparent 75%,#000 100%)'));
enter(s10, s9, 18.64, { y: -2150, rotation: 5 });
camZoom(s10, 18.64, 20.8, 1.045);
{
  const c = s10.content;
  const disc = center(el('div', { cls: 'abs', style: Object.assign({ left: '540px', top: '880px', width: '760px', height: '760px', borderRadius: '50%', backgroundColor: C.mustard, boxShadow: `0 0 0 14px ${C.esp}` }, halftone('#F2A922', 30, 30)) }, c));
  popIn(disc, 18.72, { rot: 0, from: 0.3, dur: 0.35, sfx: null });
  tl.to(disc, { rotation: 25, duration: 1.8, ease: 'none' }, 19.0);
  const bg = bag(c, 540, 880, 400);
  tl.fromTo(bg, { y: -1400, rotation: -12 }, { y: 0, rotation: 3, duration: 0.36, ease: 'back.out(1.25)' }, 18.7);
  sfx(19.02, 'thud', 0.5);
  bob(bg, 19.2, 10, 0.5, 2);
  const sp = sticker(c, 'sparkles', 830, 600, 150, { rot: 10 });
  popIn(sp, 19.12, { rot: 10, sfx: 'sparkle', gain: 0.25 });
  const sd = sticker(c, 'seedling', 220, 1110, 170, { rot: -8 });
  popIn(sd, 19.25, { rot: -8, gain: 0.25 });
  const ra = row(c, 540, 250, 14);
  word(ra, 50, ST.dark, 118, { rot: -3 });
  word(ra, 51, ST.lalR, 138, { rot: 2, pitch: 1.2 });
  const rm = row(c, 540, 1255, 0, { rot: 3 });
  word(rm, 52, ST.white, 70, { rot: 0 });
  const btn = center(el('div', { cls: 'btn', style: { left: '540px', top: '1405px' } }, c), -2);
  const w1 = el('span', { text: 'الرابط', style: { display: 'inline-block' } }, btn);
  const w2 = el('span', { text: 'بالبايو', style: { display: 'inline-block' } }, btn);
  const lk = el('img', { attrs: { src: 'assets/emoji/link.svg' }, style: { width: '100px', height: '100px', display: 'inline-block' } }, btn);
  popIn(btn, T(53), { rot: -2, fromRot: -12, dur: 0.34, sfx: 'pop', pitch: 1, gain: 0.5 });
  gsap.set(w2, { autoAlpha: 0 });
  popIn(w2, T(54), { rot: 0, fromRot: 12, sfx: 'pop', pitch: 1.3, gain: 0.45 });
  popIn(lk, T(54) + 0.1, { rot: 0, sfx: null });
  sfx(T(54) + 0.1, 'ding', 0.35, { pitch: 1.33 });
  const ring = center(el('div', { cls: 'abs', style: { left: '540px', top: '1405px', width: '860px', height: '200px', borderRadius: '110px', border: `8px solid ${C.esp}` } }, c));
  gsap.set(ring, { autoAlpha: 0 });
  const hand = sticker(c, 'backhand-index-pointing-up', 790, 1560, 200, { rot: -12 });
  tl.fromTo(hand, { y: 420, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.25, ease: 'power3.out' }, 20.02);
  tl.to(hand, { scale: 0.84, y: -22, duration: 0.08, ease: 'power2.out' }, 20.3);
  tl.to(hand, { scale: 1, y: 0, duration: 0.18, ease: 'power2.out' }, 20.38);
  sfx(20.32, 'tap', 0.5);
  tl.fromTo(ring, { scale: 0.9, autoAlpha: 1 }, { scale: 1.3, autoAlpha: 0, duration: 0.42, ease: 'power2.out', immediateRender: false }, 20.34);
  tl.to(btn, { scale: 0.93, duration: 0.08 }, 20.3);
  tl.to(btn, { scale: 1.07, duration: 0.14, ease: 'power2.out' }, 20.38);
  tl.to(btn, { scale: 1, duration: 0.2 }, 20.52);
}

// ---------- runtime ----------
tl.set({}, {}, DUR);
const boils = [...document.querySelectorAll('.boil')];
function boil(t) {
  const step = Math.floor(t * 8);
  boils.forEach((e, k) => {
    const h = mulberry32(k * 1000003 + step * 7919 + 17);
    e.style.translate = `${((h() - 0.5) * 5).toFixed(2)}px ${((h() - 0.5) * 5).toFixed(2)}px`;
    e.style.rotate = `${((h() - 0.5) * 2.2).toFixed(2)}deg`;
  });
}
let lastG = -1;
window.renderFrame = function (t) {
  tl.seek(t, false);
  boil(t);
  const g = Math.floor(t * FPS) % grains.length;
  if (g !== lastG) { grains.forEach((d, k) => d.style.visibility = k === g ? 'visible' : 'hidden'); lastG = g; }
};
window.__CUES = CUES.sort((a, b) => a.t - b.t);
window.__DUR = DUR;
(async () => {
  const fams = ['Lalezar', 'Cairo', 'Rakkas', 'ArefRuqaa', 'Anton', 'Abril', 'Bungee', 'Marker', 'Shrikhand', 'Marhey', 'ReemKufi', 'Blaka', 'Lemonada', 'Elite'];
  await Promise.all(fams.flatMap((f) => [document.fonts.load(`400 50px ${f}`, 'اب KLOVA'), document.fonts.load(`900 50px ${f}`, 'اب KLOVA')]));
  await Promise.all([...document.images].map((i) => i.decode().catch(() => console.log('img fail', i.src))));
  await document.fonts.ready;
  DEFER.forEach((f) => f());
  window.renderFrame(0);
  window.__READY = true;
})();
