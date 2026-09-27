// KLOVA — match-cut collage (TikTok 9:16).
// Every scene is built around one hero circle that sits at the same spot and
// size at each cut. The cut happens mid-spin / mid-push, with sub-frame
// motion blur, so the circle reads as one object travelling through places.
'use strict';

const W = 1080, H = 1920, FPS = 30, DUR = 20.8;
const CX = 540, CY = 1010, R0 = 300;
const COL = {
  ink: '#2A1711', ink2: '#3A2219', roast: '#703E2E', brand: '#BD9484', blush: '#E4C7B8',
  cream: '#F6ECDF', acc: '#D4542C', accD: '#7A2412', accL: '#F09669',
};
// cut times sit in the natural pauses of the voiceover
const CUTS = [3.14, 6.16, 8.30, 10.20, 13.04, 14.47, 16.64];
const ALLCUTS = [0, ...CUTS, DUR]; // 0 and DUR make the loop seamless

// ---------------------------------------------------------------- utils
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const easeInOut = u => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
const easeOut = u => 1 - Math.pow(1 - u, 3);
const easeIn = u => u * u * u;
const backOut = (u, s = 1.9) => 1 + (s + 1) * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2);
function erf(x) {
  const s = Math.sign(x); x = Math.abs(x);
  const t = 1 / (1 + 0.3275911 * x);
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return s * y;
}
const Phi = x => 0.5 * (1 + erf(x / Math.SQRT2));
function rng(seed) {
  let a = seed >>> 0;
  return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function kf(t, keys, ease = easeInOut) {
  const val = (a, b, u) => (Array.isArray(a) ? a.map((v, i) => lerp(v, b[i], u)) : lerp(a, b, u));
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) {
    if (t < keys[i + 1][0]) return val(keys[i][1], keys[i + 1][1], ease((t - keys[i][0]) / (keys[i + 1][0] - keys[i][0])));
  }
  return keys[keys.length - 1][1];
}
const pop = (t, t0, d = 0.32) => (t < t0 ? 0 : t >= t0 + d ? 1 : backOut((t - t0) / d));
const prog = (t, t0, d) => clamp((t - t0) / d);
function boil(seed, t, amp = 1) { // stop-motion wobble, 10 steps per second
  const r = rng(seed * 7919 + Math.floor(t * 10) * 104729);
  return { dx: (r() - 0.5) * 4 * amp, dy: (r() - 0.5) * 4 * amp, dr: (r() - 0.5) * 0.018 * amp };
}

// ---------------------------------------------------------------- camera
const SIG_Z = 0.16, HZ = Math.log(1.5);
function camZ(t) {
  // gentle push-in/out inside each scene (neutral at the cuts) + the push through every cut
  const i = sceneIndex(t), u = clamp((t - sceneStart(i)) / (sceneEnd(i) - sceneStart(i)));
  let s = 0.035 * Math.sin(Math.PI * u);
  for (const c of ALLCUTS) { const u = (t - c - SIG_Z) / SIG_Z; s += HZ * Math.exp(-0.5 * u * u); }
  return Math.exp(s);
}
const SIG_R = 0.2, AR = 0.22;
function camRoll(t) {
  let s = 0;
  for (const c of ALLCUTS) { const u = (t - c) / SIG_R; s += AR * u * Math.exp(-0.5 * u * u); }
  return s;
}
// hero spin: half a turn per cut, fastest exactly on the cut, 8 cuts -> 4 turns -> loops
const SPIN_A = Math.PI, SIG_S = 0.13;
function spin(t) {
  let s = 0;
  for (const c of ALLCUTS) s += SPIN_A * Phi((t - c) / SIG_S);
  return s;
}
function sceneIndex(t) { for (let i = 0; i < CUTS.length; i++) if (t < CUTS[i]) return i; return CUTS.length; }
const sceneStart = i => (i === 0 ? 0 : CUTS[i - 1]);
const sceneEnd = i => (i === CUTS.length ? DUR : CUTS[i]);
function heroAngle(t, i, rest) { // rest orientation reached mid-scene
  const mid = (sceneStart(i) + sceneEnd(i)) / 2;
  return spin(t) - spin(mid) + rest;
}

// ---------------------------------------------------------------- assets
const IMG = {};
const IMG_LIST = ['hero_latte', 'hero_orange', 'hero_cherries', 'beans', 'bag_klova', 'sack', 'strawberry', 'chocolate',
  'espresso', 'takeaway', 'pointing', 'pourover', 'logo_ink', 'logo_cream', 'grain'];
function loadImg(n) {
  return new Promise((res, rej) => { const im = new Image(); im.onload = () => { IMG[n] = im; res(); }; im.onerror = rej; im.src = 'assets/' + n + '.png'; });
}
let WORLD = null, COUNTRIES = null;
const COFFEE = { 76: 'BR', 170: 'CO', 231: 'ET', 404: 'KE', 887: 'YE' };
const PINS = [ // lon, lat, drop time (on the words of "نوفر لك محاصيل من أكثر من بلد")
  { id: 170, ll: [-74, 4.5], t: 11.18 },
  { id: 76, ll: [-51, -10], t: 11.40 },
  { id: 231, ll: [39.5, 8.5], t: 11.80 },
  { id: 404, ll: [37.9, 0.3], t: 12.04 },
  { id: 887, ll: [46.5, 15.5], t: 12.46 },
];

// ---------------------------------------------------------------- words / captions
let WORDS = [];
function parseSrt(txt) {
  const out = [];
  for (const blk of txt.trim().split(/\r?\n\r?\n/)) {
    const ln = blk.split(/\r?\n/);
    const m = ln[1].match(/(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)/);
    const ts = (h, mi, s, ms) => +h * 3600 + +mi * 60 + +s + +ms / 1000;
    out.push({ s: ts(m[1], m[2], m[3], m[4]), e: ts(m[5], m[6], m[7], m[8]), w: ln.slice(2).join(' ') });
  }
  return out;
}
const PHRASES = [
  { a: 1, text: 'إذا تسوي قهوتك في البيت؟', hl: [4], instant: true }, // hook: readable on frame 0
  { a: 6, text: 'هذا الفيديو لك', hl: [2] },
  { a: 9, text: 'حنا كلوفا', hl: [1] },
  { a: 11, text: 'متجر متخصص في محاصيل القهوة', hl: [3, 4] },
  { a: 16, text: 'والفرق غالباً مو في المكينة', hl: [4] },
  { a: 21, text: 'الفرق في المحصول نفسه', hl: [2] },
  { a: 25, text: 'عشان كذا نوفر لك محاصيل من أكثر من بلد', hl: [6, 7, 8] },
  { a: 34, text: 'كل واحد له طعمه', hl: [3] },
  { a: 38, text: 'بدون ما تدفع كل يوم في الكوفيّات', hl: [3, 4] },
  { a: 45, text: 'وبدون ما تتنازل عن الطعم', hl: [4] },
  { a: 50, text: 'اختار محصولك من الرابط بالبايو', hl: [3, 4] },
];

// ---------------------------------------------------------------- drawing helpers
const PATHS = new Map();
function tornPath(w, h, seed, amp = 7, step = 16) {
  const key = [w | 0, h | 0, seed, amp].join(':');
  if (PATHS.has(key)) return PATHS.get(key);
  const r = rng(seed), p = new Path2D();
  const x0 = -w / 2, y0 = -h / 2;
  const j = () => (r() - 0.5) * 2 * amp;
  p.moveTo(x0 + j() * 0.3, y0 + j() * 0.3);
  for (let x = x0 + step; x < x0 + w; x += step * (0.6 + r() * 0.8)) p.lineTo(x, y0 + j());
  for (let y = y0 + step; y < y0 + h; y += step * (0.6 + r() * 0.8)) p.lineTo(x0 + w + j(), y);
  for (let x = x0 + w - step; x > x0; x -= step * (0.6 + r() * 0.8)) p.lineTo(x, y0 + h + j());
  for (let y = y0 + h - step; y > y0; y -= step * (0.6 + r() * 0.8)) p.lineTo(x0 + j(), y);
  p.closePath();
  PATHS.set(key, p);
  return p;
}
function shadowOn(ctx, blur = 22, oy = 12, a = 0.38) {
  ctx.shadowColor = `rgba(24,12,8,${a})`; ctx.shadowBlur = blur; ctx.shadowOffsetX = 4; ctx.shadowOffsetY = oy;
}
function shadowOff(ctx) { ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 0; }
function sticker(ctx, img, x, y, w, rot = 0, sc = 1, alpha = 1, shadow = true) {
  if (sc <= 0.001 || alpha <= 0.001) return;
  const h = w * img.height / img.width;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc);
  if (shadow) shadowOn(ctx);
  ctx.drawImage(img, -w / 2, -h / 2, w, h);
  ctx.restore();
}
function tape(ctx, x, y, w, h, rot, seed) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  shadowOn(ctx, 6, 2, 0.18);
  ctx.fillStyle = 'rgba(246,236,223,0.78)';
  ctx.fill(tornPath(w, h, seed, 3, 8));
  ctx.restore();
}
function photoTorn(ctx, img, x, y, w, h, rot, seed, sc = 1, border = 14) {
  if (sc <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc);
  shadowOn(ctx);
  ctx.fillStyle = COL.cream; ctx.fill(tornPath(w + border * 2, h + border * 2, seed, 6));
  shadowOff(ctx);
  ctx.save(); ctx.clip(tornPath(w, h, seed + 1, 5));
  const s = Math.max(w / img.width, h / img.height);
  ctx.drawImage(img, -img.width * s / 2, -img.height * s / 2, img.width * s, img.height * s);
  ctx.restore();
  ctx.restore();
}
function strokePoly(ctx, pts, p, width, color) {
  if (p <= 0) return;
  let L = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  let rem = L * clamp(p);
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.lineWidth = width; ctx.strokeStyle = color;
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length && rem > 0; i++) {
    const d = seg[i - 1];
    if (rem >= d) ctx.lineTo(pts[i][0], pts[i][1]);
    else { const u = rem / d; ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u)); }
    rem -= d;
  }
  ctx.stroke(); ctx.restore();
}
function handLine(x0, y0, x1, y1, seed, n = 14, wob = 5) {
  const r = rng(seed), pts = [];
  for (let i = 0; i <= n; i++) { const u = i / n; pts.push([lerp(x0, x1, u) + (r() - 0.5) * wob, lerp(y0, y1, u) + (r() - 0.5) * wob]); }
  return pts;
}
function handCircle(cx, cy, rx, ry, seed, turns = 1.12, a0 = -2.2) {
  const r = rng(seed), pts = []; const n = 90;
  for (let i = 0; i <= n; i++) {
    const u = i / n, a = a0 + u * turns * Math.PI * 2, k = 1 + (r() - 0.5) * 0.025 + u * 0.05;
    pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
  }
  return pts;
}
function bean(ctx, x, y, s, rot, col = COL.roast) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  shadowOn(ctx, 8, 4, 0.3);
  ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(0, 0, s * 0.62, s * 0.44, 0, 0, Math.PI * 2); ctx.fill();
  shadowOff(ctx);
  ctx.strokeStyle = COL.ink; ctx.lineWidth = s * 0.08; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(-s * 0.5, 0); ctx.bezierCurveTo(-s * 0.15, -s * 0.2, s * 0.15, s * 0.2, s * 0.5, 0); ctx.stroke();
  ctx.fillStyle = 'rgba(246,236,223,0.25)'; ctx.beginPath(); ctx.ellipse(-s * 0.2, -s * 0.2, s * 0.22, s * 0.09, -0.4, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
function leaf(ctx, x, y, len, rot, sc, fill = COL.ink, vein = COL.acc) {
  if (sc <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc);
  shadowOn(ctx, 10, 6, 0.3);
  ctx.fillStyle = fill; ctx.beginPath(); ctx.moveTo(0, 0);
  ctx.quadraticCurveTo(len * 0.5, -len * 0.36, len, 0); ctx.quadraticCurveTo(len * 0.5, len * 0.36, 0, 0); ctx.fill();
  shadowOff(ctx);
  ctx.strokeStyle = vein; ctx.lineWidth = len * 0.035; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(len * 0.05, 0); ctx.quadraticCurveTo(len * 0.5, -len * 0.04, len * 0.92, 0); ctx.stroke();
  for (let i = 1; i <= 4; i++) {
    const u = i / 5.2;
    ctx.beginPath(); ctx.moveTo(len * u, -len * 0.02); ctx.lineTo(len * (u + 0.1), -len * 0.15); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(len * u, len * 0.01); ctx.lineTo(len * (u + 0.1), len * 0.14); ctx.stroke();
  }
  ctx.restore();
}
function sparkle(ctx, x, y, s, col = COL.cream, rot = 0) {
  if (s <= 0.5) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.fillStyle = col;
  ctx.beginPath();
  for (let i = 0; i < 4; i++) {
    const a = i * Math.PI / 2;
    ctx.lineTo(Math.cos(a) * s, Math.sin(a) * s);
    ctx.quadraticCurveTo(0, 0, Math.cos(a + Math.PI / 2) * s, Math.sin(a + Math.PI / 2) * s);
  }
  ctx.fill(); ctx.restore();
}
function heart(ctx, x, y, s, rot, sc) {
  if (sc <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc * s / 100, sc * s / 100);
  const p = new Path2D('M0 35 C -10 20 -60 5 -60 -25 C -60 -55 -20 -65 0 -35 C 20 -65 60 -55 60 -25 C 60 5 10 20 0 35 Z');
  shadowOn(ctx, 14, 8, 0.35);
  ctx.lineJoin = 'round'; ctx.lineWidth = 16; ctx.strokeStyle = COL.cream; ctx.stroke(p);
  shadowOff(ctx);
  ctx.fillStyle = COL.acc; ctx.fill(p);
  ctx.lineWidth = 3; ctx.strokeStyle = COL.ink; ctx.stroke(p);
  ctx.fillStyle = 'rgba(246,236,223,0.55)'; ctx.beginPath(); ctx.ellipse(-30, -30, 12, 7, -0.6, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
function flower(ctx, x, y, s, rot, sc) {
  if (sc <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc);
  shadowOn(ctx, 12, 6, 0.3);
  for (let i = 0; i < 6; i++) {
    ctx.save(); ctx.rotate(i * Math.PI / 3);
    ctx.fillStyle = COL.cream; ctx.beginPath(); ctx.ellipse(0, -s * 0.5, s * 0.24, s * 0.46, 0, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
  shadowOff(ctx);
  ctx.strokeStyle = COL.ink; ctx.lineWidth = 3;
  for (let i = 0; i < 6; i++) {
    ctx.save(); ctx.rotate(i * Math.PI / 3);
    ctx.beginPath(); ctx.ellipse(0, -s * 0.5, s * 0.24, s * 0.46, 0, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();
  }
  ctx.fillStyle = COL.acc; ctx.beginPath(); ctx.arc(0, 0, s * 0.22, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.restore();
}
function coinFace(ctx, r) {
  const g = ctx.createRadialGradient(-r * 0.35, -r * 0.4, r * 0.1, 0, 0, r);
  g.addColorStop(0, COL.accL); g.addColorStop(0.55, COL.acc); g.addColorStop(1, '#A83C1C');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  ctx.lineWidth = r * 0.06; ctx.strokeStyle = COL.accD; ctx.beginPath(); ctx.arc(0, 0, r * 0.95, 0, Math.PI * 2); ctx.stroke();
  ctx.setLineDash([r * 0.02, r * 0.045]); ctx.lineWidth = r * 0.035; ctx.strokeStyle = COL.accL;
  ctx.beginPath(); ctx.arc(0, 0, r * 0.83, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
  ctx.lineWidth = r * 0.012; ctx.strokeStyle = COL.accD; ctx.beginPath(); ctx.arc(0, 0, r * 0.76, 0, Math.PI * 2); ctx.stroke();
  ctx.font = `900 ${r * 0.62}px Alexandria`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.direction = 'rtl';
  ctx.fillStyle = 'rgba(246,236,223,0.55)'; ctx.fillText('ر.س', -r * 0.03, r * 0.02);
  ctx.fillStyle = COL.accD; ctx.fillText('ر.س', r * 0.015, r * 0.06);
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; sparkle(ctx, Math.cos(a) * r * 0.66, Math.sin(a) * r * 0.66, r * 0.035, COL.accD); }
}

// ---------------------------------------------------------------- backgrounds (pre-rendered)
const BG = {};
const BGX = -260, BGY = -260, BGW = W + 520, BGH = H + 520;
function mkCanvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function buildBackgrounds() {
  // home: top-down checkered tablecloth
  let c = mkCanvas(BGW, BGH), g = c.getContext('2d');
  g.fillStyle = COL.cream; g.fillRect(0, 0, BGW, BGH);
  const s = 120;
  for (let y = 0; y < BGH; y += s) for (let x = 0; x < BGW; x += s) {
    const a = (Math.floor(x / s) + Math.floor(y / s)) % 2;
    if (a) { g.fillStyle = COL.brand; g.fillRect(x, y, s, s); }
  }
  g.globalAlpha = 0.5;
  for (let y = 0; y < BGH; y += s) for (let x = 0; x < BGW; x += s) {
    if ((Math.floor(x / s) % 2) && !(Math.floor(y / s) % 2) || (!(Math.floor(x / s) % 2) && (Math.floor(y / s) % 2))) continue;
    g.fillStyle = COL.blush; g.fillRect(x + s * 0.5 - 1, y, 2, s); g.fillRect(x, y + s * 0.5 - 1, s, 2);
  }
  g.globalAlpha = 1;
  BG.home = c;

  // graph paper (machine)
  c = mkCanvas(BGW, BGH); g = c.getContext('2d');
  g.fillStyle = COL.cream; g.fillRect(0, 0, BGW, BGH);
  for (let x = 0; x < BGW; x += 40) { g.fillStyle = (x / 40) % 5 === 0 ? 'rgba(189,148,132,0.75)' : 'rgba(189,148,132,0.35)'; g.fillRect(x, 0, (x / 40) % 5 === 0 ? 3 : 1.5, BGH); }
  for (let y = 0; y < BGH; y += 40) { g.fillStyle = (y / 40) % 5 === 0 ? 'rgba(189,148,132,0.75)' : 'rgba(189,148,132,0.35)'; g.fillRect(0, y, BGW, (y / 40) % 5 === 0 ? 3 : 1.5); }
  BG.grid = c;

  // crop: terracotta paper with big plant doodles
  c = mkCanvas(BGW, BGH); g = c.getContext('2d');
  g.fillStyle = COL.acc; g.fillRect(0, 0, BGW, BGH);
  const r = rng(44);
  for (let i = 0; i < 26; i++) leaf(g, r() * BGW, r() * BGH, 150 + r() * 160, r() * Math.PI * 2, 1, 'rgba(122,36,18,0.55)', 'rgba(240,150,105,0.5)');
  g.fillStyle = 'rgba(246,236,223,0.22)';
  for (let y = 0; y < BGH; y += 34) for (let x = (y / 34) % 2 ? 17 : 0; x < BGW; x += 34) { g.beginPath(); g.arc(x, y, 2.4, 0, Math.PI * 2); g.fill(); }
  BG.crop = c;

  // world: espresso night with dot matrix
  c = mkCanvas(BGW, BGH); g = c.getContext('2d');
  g.fillStyle = COL.ink; g.fillRect(0, 0, BGW, BGH);
  g.fillStyle = 'rgba(189,148,132,0.28)';
  for (let y = 0; y < BGH; y += 30) for (let x = (y / 30) % 2 ? 15 : 0; x < BGW; x += 30) { g.beginPath(); g.arc(x, y, 2.2, 0, Math.PI * 2); g.fill(); }
  BG.world = c;

  // money: ruled receipt / notebook paper
  c = mkCanvas(BGW, BGH); g = c.getContext('2d');
  g.fillStyle = COL.cream; g.fillRect(0, 0, BGW, BGH);
  for (let y = 0; y < BGH; y += 64) { g.fillStyle = 'rgba(189,148,132,0.55)'; g.fillRect(0, y, BGW, 3); }
  g.fillStyle = 'rgba(212,84,44,0.55)'; g.fillRect(BGW - 260 - 150, 0, 4, BGH); g.fillRect(BGW - 260 - 140, 0, 2, BGH);
  BG.money = c;
}
function drawBg(ctx, name) { ctx.drawImage(BG[name], BGX, BGY); }
function drawRays(ctx, base, rayCol, n, rot) {
  ctx.fillStyle = base; ctx.fillRect(BGX, BGY, BGW, BGH);
  ctx.save(); ctx.translate(CX, CY); ctx.rotate(rot); ctx.fillStyle = rayCol;
  const R = 2400;
  for (let i = 0; i < n; i++) {
    const a0 = (i / n) * Math.PI * 2, a1 = a0 + Math.PI / n;
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, R, a0, a1); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}

// ---------------------------------------------------------------- heroes
function heroShadow(ctx, r) {
  ctx.save(); shadowOn(ctx, 46, 22, 0.5); ctx.fillStyle = COL.ink;
  ctx.beginPath(); ctx.arc(0, 0, r * 0.985, 0, Math.PI * 2); ctx.fill(); ctx.restore();
}
function heroImage(ctx, img, r) { ctx.drawImage(img, -r, -r, r * 2, r * 2); }
function heroBadge(ctx, r) {
  ctx.fillStyle = COL.cream; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = COL.ink; ctx.lineWidth = r * 0.03; ctx.beginPath(); ctx.arc(0, 0, r * 0.94, 0, Math.PI * 2); ctx.stroke();
  ctx.lineWidth = r * 0.012; ctx.beginPath(); ctx.arc(0, 0, r * 0.7, 0, Math.PI * 2); ctx.stroke();
  ctx.fillStyle = COL.acc; ctx.beginPath(); ctx.arc(0, 0, r * 0.66, 0, Math.PI * 2); ctx.fill();
  const txt = 'KLOVA  ✦  COFFEE CROPS  ✦  KLOVA  ✦  COFFEE CROPS  ✦  ';
  ctx.font = `700 ${r * 0.1}px Alexandria`; ctx.fillStyle = COL.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.direction = 'ltr';
  const chars = [...txt]; const step = (Math.PI * 2) / chars.length;
  chars.forEach((ch, i) => {
    ctx.save(); ctx.rotate(i * step); ctx.translate(0, -r * 0.82);
    ctx.fillText(ch === '✦' ? '•' : ch, 0, 0); ctx.restore();
  });
  const lw = r * 1.08, lh = lw * IMG.logo_cream.height / IMG.logo_cream.width;
  ctx.drawImage(IMG.logo_cream, -lw / 2, -lh / 2 - r * 0.02, lw, lh);
}
function heroGauge(ctx, r, needle) {
  ctx.fillStyle = COL.ink; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = COL.roast; ctx.lineWidth = r * 0.03; ctx.beginPath(); ctx.arc(0, 0, r * 0.93, 0, Math.PI * 2); ctx.stroke();
  ctx.fillStyle = COL.cream; ctx.beginPath(); ctx.arc(0, 0, r * 0.86, 0, Math.PI * 2); ctx.fill();
  const a0 = Math.PI * 0.75, sweep = Math.PI * 1.5;
  ctx.strokeStyle = COL.acc; ctx.lineWidth = r * 0.07; ctx.beginPath(); ctx.arc(0, 0, r * 0.72, a0 + sweep * 0.72, a0 + sweep); ctx.stroke();
  ctx.strokeStyle = COL.brand; ctx.beginPath(); ctx.arc(0, 0, r * 0.72, a0 + sweep * 0.45, a0 + sweep * 0.72); ctx.stroke();
  ctx.strokeStyle = COL.ink; ctx.lineCap = 'round';
  for (let i = 0; i <= 30; i++) {
    const a = a0 + sweep * i / 30, big = i % 5 === 0;
    ctx.lineWidth = big ? r * 0.025 : r * 0.012;
    ctx.beginPath(); ctx.moveTo(Math.cos(a) * r * (big ? 0.6 : 0.66), Math.sin(a) * r * (big ? 0.6 : 0.66));
    ctx.lineTo(Math.cos(a) * r * 0.78, Math.sin(a) * r * 0.78); ctx.stroke();
  }
  ctx.font = `800 ${r * 0.12}px Alexandria`; ctx.fillStyle = COL.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.direction = 'ltr';
  for (let i = 0; i <= 6; i++) { const a = a0 + sweep * i / 6; ctx.fillText(String(i * 3), Math.cos(a) * r * 0.46, Math.sin(a) * r * 0.46); }
  ctx.font = `700 ${r * 0.08}px Alexandria`; ctx.fillStyle = COL.roast; ctx.fillText('BAR', 0, r * 0.4);
  ctx.save(); ctx.rotate(a0 + sweep * needle);
  shadowOn(ctx, 10, 6, 0.35);
  ctx.fillStyle = COL.acc; ctx.beginPath(); ctx.moveTo(-r * 0.12, -r * 0.035); ctx.lineTo(r * 0.7, 0); ctx.lineTo(-r * 0.12, r * 0.035); ctx.closePath(); ctx.fill();
  ctx.restore();
  ctx.fillStyle = COL.ink; ctx.beginPath(); ctx.arc(0, 0, r * 0.08, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.beginPath(); ctx.ellipse(-r * 0.3, -r * 0.38, r * 0.34, r * 0.16, -0.6, 0, Math.PI * 2); ctx.fill();
}
function heroPorthole(ctx, r) {
  ctx.fillStyle = COL.cream; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  ctx.save(); ctx.beginPath(); ctx.arc(0, 0, r * 0.9, 0, Math.PI * 2); ctx.clip();
  ctx.drawImage(IMG.hero_cherries, -r * 0.9, -r * 0.9, r * 1.8, r * 1.8); ctx.restore();
  ctx.strokeStyle = COL.ink; ctx.lineWidth = r * 0.012;
  ctx.beginPath(); ctx.arc(0, 0, r * 0.9, 0, Math.PI * 2); ctx.stroke();
  ctx.beginPath(); ctx.arc(0, 0, r * 0.995, 0, Math.PI * 2); ctx.stroke();
}
function heroGlobe(ctx, r, lon, t) {
  const proj = d3.geoOrthographic().scale(r).translate([0, 0]).rotate([-lon, -12]).clipAngle(90);
  const path = d3.geoPath(proj, ctx);
  ctx.fillStyle = COL.brand; ctx.beginPath(); path({ type: 'Sphere' }); ctx.fill();
  ctx.strokeStyle = 'rgba(42,23,17,0.22)'; ctx.lineWidth = 1.5; ctx.beginPath(); path(d3.geoGraticule10()); ctx.stroke();
  ctx.fillStyle = COL.cream; ctx.beginPath(); path(WORLD); ctx.fill();
  for (const pin of PINS) {
    const k = prog(t, pin.t, 0.25);
    if (k <= 0) continue;
    const f = COUNTRIES.get(pin.id);
    if (!f) continue;
    ctx.fillStyle = COL.acc; ctx.globalAlpha = k; ctx.beginPath(); path(f); ctx.fill(); ctx.globalAlpha = 1;
  }
  ctx.strokeStyle = 'rgba(42,23,17,0.55)'; ctx.lineWidth = 1.2; ctx.beginPath(); path(WORLD_BORDERS); ctx.stroke();
  const g = ctx.createRadialGradient(-r * 0.4, -r * 0.45, r * 0.05, 0, 0, r);
  g.addColorStop(0, 'rgba(255,248,238,0.35)'); g.addColorStop(0.55, 'rgba(255,248,238,0)'); g.addColorStop(1, 'rgba(42,23,17,0.45)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = COL.ink; ctx.lineWidth = r * 0.02; ctx.beginPath(); ctx.arc(0, 0, r * 0.99, 0, Math.PI * 2); ctx.stroke();
  // pins
  const center = [lon, 12];
  for (const pin of PINS) {
    const k = pop(t, pin.t, 0.34);
    if (k <= 0) continue;
    const vis = d3.geoDistance(pin.ll, center);
    if (vis > Math.PI / 2 - 0.08) continue;
    const [px, py] = proj(pin.ll);
    const drop = (1 - clamp((t - pin.t) / 0.18)) * -90;
    const s = r * 0.13 * k * clamp((Math.PI / 2 - vis) / 0.35);
    ctx.save(); ctx.translate(px, py + drop);
    shadowOn(ctx, 8, 5, 0.4);
    ctx.fillStyle = COL.acc; ctx.beginPath();
    ctx.moveTo(0, 0); ctx.bezierCurveTo(-s * 0.2, -s * 0.5, -s * 0.55, -s * 0.75, -s * 0.55, -s * 1.1);
    ctx.arc(0, -s * 1.1, s * 0.55, Math.PI, 0); ctx.bezierCurveTo(s * 0.55, -s * 0.75, s * 0.2, -s * 0.5, 0, 0); ctx.fill();
    shadowOff(ctx);
    ctx.strokeStyle = COL.ink; ctx.lineWidth = 2.5; ctx.stroke();
    ctx.fillStyle = COL.cream; ctx.beginPath(); ctx.arc(0, -s * 1.1, s * 0.22, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
}
let WORLD_BORDERS = null;

// generic hero placement: world transform already applied
function withHero(ctx, x, y, r, ang, flip, fn, edgeCol, unmirror = false) {
  ctx.save(); ctx.translate(x, y);
  if (flip != null) {
    const fx = Math.cos(flip), edge = r * 0.07 * Math.sin(flip);
    ctx.save(); ctx.translate(edge, 0); ctx.scale(fx, 1); ctx.fillStyle = edgeCol;
    ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    ctx.scale(fx, 1);
    if (unmirror && fx < 0) ctx.scale(-1, 1);
  }
  ctx.rotate(ang);
  heroShadow(ctx, r);
  fn(ctx, r);
  ctx.restore();
}

// ---------------------------------------------------------------- scenes
// hero track helpers: size factor + offset (both back to neutral at the cuts)
function heroPos(t, keys) {
  const v = kf(t, keys);
  return { x: CX + v[1], y: CY + v[2], r: R0 * v[0] };
}

const SCENES = [
  // S1 — at home (0 .. 3.14)
  function s1(ctx, t) {
    drawBg(ctx, 'home');
    // pour-over photo taped at the top-left
    const kp = pop(t, 0.12, 0.4), b1 = boil(11, t);
    photoTorn(ctx, IMG.pourover, 250 + b1.dx, 700 + b1.dy, 300, 330, -0.14 + b1.dr, 5, kp);
    if (kp > 0.9) tape(ctx, 250, 540, 130, 38, 0.1, 9);
    // beans scattered on the cloth
    const r = rng(3);
    for (let i = 0; i < 7; i++) {
      const a = r() * Math.PI * 2, d = 380 + r() * 170;
      bean(ctx, CX + Math.cos(a) * d, CY + Math.sin(a) * d * 1.15, 46 + r() * 18, r() * 6, i % 3 ? COL.roast : COL.ink);
    }
    const h = heroPos(t, [[0, [1, 0, 0]], [2.9, [1, 0, 0]]]);
    withHero(ctx, h.x, h.y, h.r, heroAngle(t, 0, 0.35), null, (c, r) => heroImage(c, IMG.hero_latte, r));
    // "البيت" — a roof drawn on top of the cup
    const roof = [[h.x - h.r * 1.2, h.y - h.r * 0.45], [h.x, h.y - h.r * 1.42], [h.x + h.r * 1.2, h.y - h.r * 0.45]];
    const chim = [[h.x + h.r * 0.62, h.y - h.r * 0.96], [h.x + h.r * 0.62, h.y - h.r * 1.28], [h.x + h.r * 0.86, h.y - h.r * 1.28], [h.x + h.r * 0.86, h.y - h.r * 0.74]];
    const pr = prog(t, 1.28, 0.42);
    strokePoly(ctx, roof, pr, 16, COL.ink);
    strokePoly(ctx, chim, prog(t, 1.6, 0.22), 13, COL.ink);
    // "هذا الفيديو لك" — someone points at the viewer
    const kg = pop(t, 1.9, 0.42), b2 = boil(12, t);
    if (kg > 0) {
      sticker(ctx, IMG.pointing, 810 + b2.dx, lerp(2300, 1440, kg) + b2.dy, 430, 0.05 + b2.dr);
      const kb = pop(t, 2.66, 0.25);
      if (kb > 0) {
        ctx.save(); ctx.translate(600, 1160);
        for (let i = 0; i < 5; i++) {
          const a = -2.6 + i * 0.32;
          strokePoly(ctx, [[Math.cos(a) * 40, Math.sin(a) * 40], [Math.cos(a) * (40 + 60 * kb), Math.sin(a) * (40 + 60 * kb)]], 1, 10, COL.acc);
        }
        ctx.restore();
      }
    }
  },
  // S2 — KLOVA (3.14 .. 6.16)
  function s2(ctx, t) {
    drawRays(ctx, COL.ink, COL.ink2, 22, t * 0.12);
    const h = heroPos(t, [[3.14, [1, 0, 0]], [3.6, [1, 0, 0]], [4.4, [0.86, 0, -30]], [5.85, [0.86, 0, -30]], [6.1, [1, 0, 0]]]);
    // beans burst from behind the badge on "محاصيل القهوة"
    const r = rng(21);
    for (let i = 0; i < 16; i++) {
      const a = (i / 16) * Math.PI * 2 + r() * 0.3, d = 330 + r() * 230, s = 44 + r() * 26, rot0 = r() * 6;
      const k = easeOut(prog(t, 5.24 + (i % 4) * 0.035, 0.45));
      if (k <= 0) continue;
      const drift = (t - 5.24) * 12;
      bean(ctx, h.x + Math.cos(a) * (d * k + drift), h.y + Math.sin(a) * (d * k + drift) * 1.1, s, rot0 + k * 3 + t * 0.6, i % 3 ? COL.roast : COL.accD);
    }
    const kb = pop(t, 4.38, 0.42), bb = boil(22, t);
    if (kb > 0) {
      sticker(ctx, IMG.bag_klova, lerp(-300, 250, kb) + bb.dx, 1380 + bb.dy, 330, -0.14 + bb.dr);
      if (kb > 0.95) tape(ctx, 250, 1190, 120, 36, -0.35, 23);
    }
    const ks = pop(t, 4.62, 0.42), bs = boil(24, t);
    if (ks > 0) sticker(ctx, IMG.sack, lerp(1400, 840, ks) + bs.dx, 1400 + bs.dy, 380, 0.1 + bs.dr);
    withHero(ctx, h.x, h.y, h.r, heroAngle(t, 1, 0), null, heroBadge);
    // stamp ring pulse on "كلوفا"
    const kr = prog(t, 3.66, 0.45);
    if (kr > 0 && kr < 1) {
      ctx.save(); ctx.globalAlpha = 1 - kr; ctx.strokeStyle = COL.cream; ctx.lineWidth = 10;
      ctx.beginPath(); ctx.arc(h.x, h.y, h.r * (1.02 + kr * 0.35), 0, Math.PI * 2); ctx.stroke(); ctx.restore();
    }
  },
  // S3 — the machine (6.16 .. 8.30)
  function s3(ctx, t) {
    drawBg(ctx, 'grid');
    const km = pop(t, 6.46, 0.45), bm = boil(31, t);
    const out = easeIn(prog(t, 7.92, 0.36));
    if (km > 0) {
      sticker(ctx, IMG.espresso, 480 + bm.dx, lerp(2400, 1250, km) + out * 1100 + bm.dy, 720, -0.04 + bm.dr);
      // big X over the machine: "مو في المكينة"
      ctx.save(); ctx.translate(0, out * 1100);
      ctx.save(); shadowOn(ctx, 8, 6, 0.3);
      strokePoly(ctx, handLine(200, 950, 760, 1560, 5), prog(t, 7.52, 0.14), 34, COL.acc);
      strokePoly(ctx, handLine(770, 960, 190, 1550, 6), prog(t, 7.7, 0.14), 34, COL.acc);
      ctx.restore(); ctx.restore();
    }
    const h = heroPos(t, [[6.16, [1, 0, 0]], [6.42, [1, 0, 0]], [6.8, [0.56, 190, -330]], [7.86, [0.56, 190, -330]], [8.2, [1, 0, 0]]]);
    // needle: idles, jumps on "والفرق", flops, then whips round into the cut
    let needle = 0.22 + 0.02 * Math.sin(t * 40);
    needle += 0.45 * easeOut(prog(t, 6.36, 0.3)) - 0.5 * easeInOut(prog(t, 7.5, 0.3));
    needle += 3.0 * Math.pow(prog(t, 7.92, 0.38), 2);
    withHero(ctx, h.x, h.y, h.r, heroAngle(t, 2, 0), null, (c, r) => heroGauge(c, r, needle));
  },
  // S4 — the crop (8.30 .. 10.20)
  function s4(ctx, t) {
    drawBg(ctx, 'crop');
    const kb = pop(t, 8.9, 0.42), bb = boil(41, t);
    photoTorn(ctx, IMG.beans, 540 + bb.dx, lerp(2300, 1500, kb) + bb.dy, 820, 250, -0.06 + bb.dr, 41, kb > 0 ? 1 : 0);
    const h = heroPos(t, [[8.3, [1, 0, 0]], [8.55, [1, 0, 0]], [8.95, [0.86, 0, -40]], [9.95, [0.86, 0, -40]], [10.16, [1, 0, 0]]]);
    const angs = [-2.5, -0.62, 0.62, 2.5], ts = [9.04, 9.16, 9.28, 9.4];
    angs.forEach((a, i) => {
      const k = pop(t, ts[i], 0.34), bl = boil(42 + i, t);
      leaf(ctx, h.x + Math.cos(a) * h.r * 0.9, h.y + Math.sin(a) * h.r * 0.9, 190, a + 0.12 + bl.dr * 3, k, COL.ink, COL.accL);
    });
    withHero(ctx, h.x, h.y, h.r, heroAngle(t, 3, 0.2), null, heroPorthole);
    // "نفسه" — circled by hand
    strokePoly(ctx, handCircle(h.x, h.y, h.r * 1.14, h.r * 1.1, 8), prog(t, 9.68, 0.36), 14, COL.cream);
  },
  // S5 — the world (10.20 .. 13.04)
  function s5(ctx, t) {
    drawBg(ctx, 'world');
    const h = heroPos(t, [[10.2, [1, 0, 0]], [10.5, [1, 0, 0]], [10.85, [0.94, 0, 0]], [12.72, [0.94, 0, 0]], [12.98, [1, 0, 0]]]);
    // orbit ring + paper plane
    const ko = prog(t, 10.45, 0.3);
    if (ko > 0) {
      ctx.save(); ctx.translate(h.x, h.y); ctx.rotate(-0.35); ctx.globalAlpha = ko;
      ctx.setLineDash([18, 16]); ctx.lineDashOffset = -t * 60; ctx.strokeStyle = COL.brand; ctx.lineWidth = 5;
      ctx.beginPath(); ctx.ellipse(0, 0, h.r * 1.42, h.r * 0.5, 0, Math.PI, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
      ctx.restore();
    }
    // longitude: whip in from the Americas, settle on Africa / Arabia, whip out
    const lon = kf(t, [[10.2, -150], [10.9, -62], [11.55, -42], [12.2, 22], [12.6, 30], [13.04, 140]], u => u) + 0;
    withHero(ctx, h.x, h.y, h.r, heroAngle(t, 4, 0), null, (c, r) => heroGlobe(c, r, lon, t));
    if (ko > 0) {
      ctx.save(); ctx.translate(h.x, h.y); ctx.rotate(-0.35); ctx.globalAlpha = ko;
      ctx.setLineDash([18, 16]); ctx.lineDashOffset = -t * 60; ctx.strokeStyle = COL.brand; ctx.lineWidth = 5;
      ctx.beginPath(); ctx.ellipse(0, 0, h.r * 1.42, h.r * 0.5, 0, 0, Math.PI); ctx.stroke(); ctx.setLineDash([]);
      const a = (t - 10.45) * 2.4 + 0.4;
      const px = Math.cos(a) * h.r * 1.42, py = Math.sin(a) * h.r * 0.5;
      if (Math.sin(a) > -0.2) {
        ctx.translate(px, py); ctx.rotate(Math.atan2(Math.cos(a) * h.r * 0.5, -Math.sin(a) * h.r * 1.42));
        shadowOn(ctx, 6, 4, 0.4);
        ctx.fillStyle = COL.cream; ctx.beginPath(); ctx.moveTo(34, 0); ctx.lineTo(-24, -20); ctx.lineTo(-12, 0); ctx.lineTo(-24, 20); ctx.closePath(); ctx.fill();
        shadowOff(ctx); ctx.strokeStyle = COL.ink; ctx.lineWidth = 3; ctx.stroke();
        ctx.beginPath(); ctx.moveTo(34, 0); ctx.lineTo(-12, 0); ctx.stroke();
      }
      ctx.restore();
    }
  },
  // S6 — every crop has its own taste (13.04 .. 14.47)
  function s6(ctx, t) {
    drawRays(ctx, COL.brand, 'rgba(246,236,223,0.28)', 18, -t * 0.25);
    const h = heroPos(t, [[13.04, [1, 0, 0]], [13.2, [1, 0, 0]], [13.5, [0.8, 0, 0]], [14.18, [0.8, 0, 0]], [14.42, [1, 0, 0]]]);
    const b = i => boil(60 + i, t);
    sticker(ctx, IMG.strawberry, 250 + b(1).dx, 700 + b(1).dy, 270, -0.25 + b(1).dr, pop(t, 13.18, 0.3));
    sticker(ctx, IMG.chocolate, 770 + b(2).dx, 1330 + b(2).dy, 370, 0.16 + b(2).dr, pop(t, 13.4, 0.3));
    flower(ctx, 830 + b(3).dx, 690 + b(3).dy, 150, 0.2 + t * 0.4, pop(t, 13.74, 0.3));
    const kb = pop(t, 13.96, 0.3);
    if (kb > 0) { const r = rng(66); for (let i = 0; i < 5; i++) bean(ctx, 250 + (r() - 0.5) * 170, 1330 + (r() - 0.5) * 150, 60 * kb, r() * 6); }
    withHero(ctx, h.x, h.y, h.r, heroAngle(t, 5, 0), null, (c, r) => heroImage(c, IMG.hero_orange, r));
    const ksp = prog(t, 13.96, 0.4);
    [[-1.1, 1.18], [0.3, 1.25], [2.2, 1.2]].forEach(([a, d], i) => {
      const k = Math.sin(clamp(ksp * 1.3 - i * 0.12) * Math.PI);
      sparkle(ctx, h.x + Math.cos(a) * h.r * d, h.y + Math.sin(a) * h.r * d, 38 * k, COL.cream, t * 2);
    });
  },
  // S7 — no daily café bill (14.47 .. 16.64)
  function s7(ctx, t) {
    drawBg(ctx, 'money');
    const h = heroPos(t, [[14.47, [1, 0, 0]], [14.62, [1, 0, 0]], [14.95, [0.62, 150, -230]], [16.22, [0.62, 150, -230]], [16.56, [1, 0, 0]]]);
    const kt = pop(t, 14.62, 0.42), bt = boil(71, t);
    const outT = easeIn(prog(t, 16.2, 0.3));
    if (kt > 0) sticker(ctx, IMG.takeaway, lerp(-300, 250, kt) - outT * 700 + bt.dx, 1010 + bt.dy, 330, -0.12 + bt.dr);
    // coins fly out of the café cup on "تدفع"
    for (let i = 0; i < 6; i++) {
      const t0 = 14.98 + i * 0.07, k = prog(t, t0, 0.7);
      if (k <= 0 || k >= 1) continue;
      const x = 250 + lerp(0, -260 + i * 110, k), y = 740 - 900 * k + 1100 * k * k;
      ctx.save(); ctx.translate(x, y - 200 * Math.sin(k * Math.PI)); ctx.scale(Math.cos(k * 14 + i), 1);
      shadowOn(ctx, 8, 5, 0.3); coinFace(ctx, 44); ctx.restore();
    }
    // calendar strip — every day crossed on "كل يوم"
    const kc = pop(t, 15.3, 0.36), bc = boil(72, t);
    if (kc > 0) {
      ctx.save(); ctx.translate(530 + bc.dx, lerp(2200, 1390, kc) + outT * 700 + bc.dy); ctx.rotate(-0.03 + bc.dr);
      shadowOn(ctx); ctx.fillStyle = COL.blush; ctx.fill(tornPath(860, 200, 73, 6)); shadowOff(ctx);
      ctx.fillStyle = COL.acc; ctx.fillRect(-430, -100, 860, 34);
      for (let d = 0; d < 7; d++) {
        const x = 365 - d * 122, y = 22;
        ctx.strokeStyle = COL.ink; ctx.lineWidth = 3; ctx.strokeRect(x - 50, y - 50, 100, 100);
        const kx = prog(t, 15.4 + d * 0.065, 0.08);
        strokePoly(ctx, handLine(x - 34, y - 34, x + 34, y + 34, 80 + d, 4, 4), kx * 2, 12, COL.acc);
        strokePoly(ctx, handLine(x + 34, y - 34, x - 34, y + 34, 90 + d, 4, 4), kx * 2 - 1, 12, COL.acc);
      }
      ctx.restore();
    }
    // coin flip: rest -> spinning faster and faster -> edge-on exactly at the cut
    const wc = 5 * Math.PI / 1.64, tau = CUTS[6] - t;
    const flip = tau >= 1.64 ? Math.PI / 2 - wc * 1.64 / 2 : Math.PI / 2 - wc * tau + wc * tau * tau / (2 * 1.64);
    withHero(ctx, h.x, h.y, h.r, heroAngle(t, 6, 0), flip, coinFace, COL.accD, true);
  },
  // S8 — back home, the taste you keep + CTA (16.64 .. 20.8)
  function s8(ctx, t) {
    drawBg(ctx, 'home');
    const r = rng(3);
    for (let i = 0; i < 7; i++) {
      const a = r() * Math.PI * 2, d = 380 + r() * 170;
      bean(ctx, CX + Math.cos(a) * d, CY + Math.sin(a) * d * 1.15, 46 + r() * 18, r() * 6, i % 3 ? COL.roast : COL.ink);
    }
    const h = heroPos(t, [[16.64, [1, 0, 0]], [18.6, [1, 0, 0]], [18.95, [0.74, -165, 60]], [20.36, [0.74, -165, 60]], [20.74, [1, 0, 0]]]);
    // steam
    const ks = prog(t, 16.95, 0.5) * (1 - prog(t, 18.5, 0.3));
    if (ks > 0) {
      for (let i = 0; i < 3; i++) {
        const pts = [], x0 = h.x + (i - 1) * 90, y0 = h.y - h.r * 1.05;
        for (let j = 0; j <= 20; j++) { const u = j / 20; pts.push([x0 + Math.sin(u * 7 + t * 5 + i) * 22, y0 - u * 230]); }
        ctx.save(); ctx.globalAlpha = ks * 0.85;
        strokePoly(ctx, pts, clamp(prog(t, 16.95 + i * 0.12, 0.6)), 12, COL.ink); ctx.restore();
      }
    }
    // bag + arrow for the CTA
    const kbg = pop(t, 18.66, 0.42), bb = boil(81, t), outB = easeIn(prog(t, 20.4, 0.3));
    const bounce = 1 + 0.08 * Math.sin(clamp((t - 19.64) / 0.3) * Math.PI) + 0.08 * Math.sin(clamp((t - 20.02) / 0.3) * Math.PI);
    if (kbg > 0) {
      sticker(ctx, IMG.bag_klova, lerp(1500, 770, kbg) + outB * 800 + bb.dx, 1110 + bb.dy, 380, 0.1 + bb.dr, bounce);
      if (kbg > 0.95 && outB < 0.05) tape(ctx, 770, 895, 130, 38, 0.3, 83);
      // hand-drawn arrow from the caption down to the bag
      ctx.save(); ctx.globalAlpha = 1 - outB;
      const arrow = []; for (let j = 0; j <= 24; j++) { const u = j / 24; arrow.push([lerp(560, 740, u) + Math.sin(u * Math.PI) * 120, lerp(560, 815, u)]); }
      const pa = prog(t, 19.02, 0.34);
      strokePoly(ctx, arrow, pa, 14, COL.ink);
      if (pa >= 1) {
        strokePoly(ctx, [[700, 775], [740, 817], [780, 767]], prog(t, 19.36, 0.12), 14, COL.ink);
      }
      ctx.restore();
    }
    // "الطعم" — heart + sparkles
    const kh = pop(t, 18.16, 0.34) * (1 - easeIn(prog(t, 20.4, 0.25)));
    heart(ctx, h.x + h.r * 0.95, h.y - h.r * 0.95, 110, 0.25, kh);
    const ksp = prog(t, 18.16, 0.5) * (1 - prog(t, 20.4, 0.2));
    [[-2.3, 1.2], [-0.2, 1.28], [2.6, 1.18]].forEach(([a, d], i) => {
      sparkle(ctx, h.x + Math.cos(a) * h.r * d, h.y + Math.sin(a) * h.r * d, 34 * Math.sin(clamp(ksp * 1.2 - i * 0.1) * Math.PI * 0.5 + 0.0), COL.ink, t * 1.5);
    });
    // latte lands from the coin flip: edge-on at the cut -> flat after 1.5 turns
    const wc = 5 * Math.PI / 1.64, tau1 = 3 * Math.PI / wc, u = clamp(t - CUTS[6], 0, tau1);
    const flip = Math.PI / 2 + wc * u - wc * u * u / (2 * tau1);
    withHero(ctx, h.x, h.y, h.r, heroAngle(t, 7, 0.35 + Math.PI) + spinFix(), flip, (c, rr) => heroImage(c, IMG.hero_latte, rr), '#CDB8A6');
  },
];
// S1 and S8 show the same cup; keep them identical across the loop point
function spinFix() {
  // S1 angle at t=0 vs S8 angle at t=DUR must match (mod 2π)
  const a1 = heroAngle(0, 0, 0.35), a8 = heroAngle(DUR, 7, 0.35 + Math.PI);
  return a1 - a8 - 2 * Math.PI * Math.round((a1 - a8) / (2 * Math.PI));
}

function drawWorld(ctx, t) {
  const i = sceneIndex(t);
  const Z = camZ(t), roll = camRoll(t);
  ctx.save();
  ctx.translate(CX, CY); ctx.rotate(roll); ctx.scale(Z, Z); ctx.translate(-CX, -CY);
  SCENES[i](ctx, t);
  ctx.restore();
}

// ---------------------------------------------------------------- caption (fixed position)
const CAP_Y = 350, CAP_FONT = 66, CAP_MAXW = 860;
const CAP_LAYOUT = new Map();
function phraseAt(t) {
  let cur = null;
  PHRASES.forEach((p, i) => { if (t >= WORDS[p.a - 1].s - 0.02) cur = i; });
  return cur;
}
function capLayout(ctx, i) {
  if (CAP_LAYOUT.has(i)) return CAP_LAYOUT.get(i);
  const p = PHRASES[i], words = p.text.split(' ');
  ctx.font = `800 ${CAP_FONT}px Alexandria`; ctx.direction = 'rtl';
  const sp = ctx.measureText(' ').width * 1.1;
  const ws = words.map(w => ctx.measureText(w).width);
  const lines = []; let cur = [], cw = 0;
  words.forEach((w, k) => {
    if (cur.length && cw + sp + ws[k] > CAP_MAXW) { lines.push({ idx: cur, w: cw }); cur = []; cw = 0; }
    cw += (cur.length ? sp : 0) + ws[k]; cur.push(k);
  });
  lines.push({ idx: cur, w: cw });
  // balance two lines
  if (lines.length === 2 && lines[1].idx.length < lines[0].idx.length - 1) {
    const k = lines[0].idx.pop(); lines[1].idx.unshift(k);
    const calc = L => L.idx.reduce((s, j, n) => s + ws[j] + (n ? sp : 0), 0);
    lines[0].w = calc(lines[0]); lines[1].w = calc(lines[1]);
  }
  const lh = CAP_FONT * 1.42;
  const lay = { words, ws, sp, lines, lh, w: Math.max(...lines.map(l => l.w)) + 80, h: lines.length * lh + 34 };
  CAP_LAYOUT.set(i, lay);
  return lay;
}
function drawCaption(ctx, t) {
  const i = phraseAt(t);
  if (i === null) return;
  const p = PHRASES[i], L = capLayout(ctx, i);
  const t0 = WORDS[p.a - 1].s - 0.02, age = t - t0;
  const sc = age < 0.2 ? lerp(0.82, 1, backOut(clamp(age / 0.2), 2.4)) : 1;
  ctx.save(); ctx.translate(W / 2, CAP_Y); ctx.rotate(-0.022); ctx.scale(sc, sc);
  // two stacked torn papers: ink behind, cream on top — readable on any scene
  ctx.save(); ctx.translate(-10, 12); ctx.fillStyle = COL.ink; ctx.fill(tornPath(L.w, L.h, 300 + i, 6)); ctx.restore();
  ctx.save(); shadowOn(ctx, 18, 8, 0.3); ctx.fillStyle = COL.cream; ctx.fill(tornPath(L.w, L.h, 200 + i, 6)); ctx.restore();
  ctx.font = `800 ${CAP_FONT}px Alexandria`; ctx.direction = 'rtl'; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
  const top = -((L.lines.length - 1) * L.lh) / 2;
  L.lines.forEach((ln, li) => {
    let x = ln.w / 2;
    ln.idx.forEach(k => {
      const wd = WORDS[p.a - 1 + k];
      const a = p.instant ? 1 : clamp((t - wd.s + 0.04) / 0.12);
      if (a > 0) {
        ctx.save(); ctx.globalAlpha = a;
        ctx.fillStyle = p.hl.includes(k) ? COL.acc : COL.ink;
        ctx.fillText(L.words[k], x, top + li * L.lh + (1 - a) * 14 + 4);
        ctx.restore();
      }
      x -= L.ws[k] + L.sp;
    });
  });
  ctx.restore();
}

// ---------------------------------------------------------------- frame compositor
const main = document.getElementById('c');
const mctx = main.getContext('2d');
const sc = mkCanvas(W, H), sctx = sc.getContext('2d');
function renderFrame(fi) {
  const t = fi / FPS;
  const near = ALLCUTS.some(c => Math.abs(t - c) < 0.2);
  const N = near ? 10 : 2, shutter = 0.5 / FPS;
  for (let k = 0; k < N; k++) {
    let ts = t + (k / (N - 1) - 0.5) * shutter;
    if (ts < 0) ts += DUR;
    if (ts >= DUR) ts -= DUR;
    sctx.setTransform(1, 0, 0, 1, 0, 0);
    sctx.fillStyle = COL.cream; sctx.fillRect(0, 0, W, H);
    drawWorld(sctx, ts);
    mctx.globalAlpha = 1 / (k + 1);
    mctx.drawImage(sc, 0, 0);
  }
  mctx.globalAlpha = 1;
  drawCaption(mctx, t);
  // shared print finish: paper grain + soft vignette, identical on every shot
  mctx.save(); mctx.globalCompositeOperation = 'overlay'; mctx.globalAlpha = 0.5;
  const off = [[0, 0], [-37, -21], [-13, -44]][fi % 3];
  mctx.drawImage(IMG.grain, off[0], off[1], W + 60, H + 60);
  mctx.restore();
  const v = mctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.72);
  v.addColorStop(0, 'rgba(42,23,17,0)'); v.addColorStop(1, 'rgba(42,23,17,0.28)');
  mctx.fillStyle = v; mctx.fillRect(0, 0, W, H);
}

// sound design cues, read by sfx.py
const SFX = [
  { t: 0.0, k: 'impact', g: 0.9 },
  { t: 0.14, k: 'paper' }, { t: 1.28, k: 'scribble', d: 0.42 }, { t: 1.6, k: 'scribble', d: 0.22, g: 0.6 },
  { t: 1.92, k: 'pop_big' }, { t: 2.68, k: 'pop' },
  { t: 3.66, k: 'stamp' }, { t: 4.4, k: 'paper' }, { t: 4.64, k: 'paper', g: 0.8 },
  { t: 5.26, k: 'sprinkle' },
  { t: 6.4, k: 'slide' }, { t: 6.5, k: 'thud' }, { t: 6.36, k: 'gauge' }, { t: 7.52, k: 'stamp' }, { t: 7.7, k: 'stamp' },
  { t: 7.92, k: 'rev', d: 0.38 },
  { t: 8.92, k: 'paper' }, { t: 9.04, k: 'pop', g: 0.6 }, { t: 9.16, k: 'pop', g: 0.6, p: 1.12 }, { t: 9.28, k: 'pop', g: 0.6, p: 1.25 }, { t: 9.4, k: 'pop', g: 0.6, p: 1.4 },
  { t: 9.68, k: 'scribble', d: 0.36 },
  { t: 10.45, k: 'swish' },
  ...PINS.map((p, i) => ({ t: p.t, k: 'plink', p: 1 + i * 0.12 })),
  { t: 13.18, k: 'pop' }, { t: 13.4, k: 'pop', p: 1.15 }, { t: 13.74, k: 'pop', p: 1.3 }, { t: 13.96, k: 'pop_big' }, { t: 13.98, k: 'sparkle' },
  { t: 14.62, k: 'paper' }, { t: 14.98, k: 'kaching' }, { t: 15.3, k: 'paper', g: 0.7 },
  ...[0, 1, 2, 3, 4, 5, 6].map(d => ({ t: 15.4 + d * 0.065, k: 'tick', p: 1 + d * 0.05 })),
  { t: 15.95, k: 'flutter', d: 0.69 },
  { t: 16.95, k: 'steam', d: 1.3 }, { t: 18.16, k: 'pop_big' }, { t: 18.18, k: 'sparkle' },
  { t: 18.66, k: 'paper' }, { t: 19.02, k: 'scribble', d: 0.34 }, { t: 19.64, k: 'ding' }, { t: 20.02, k: 'pop', p: 1.2 },
  ...CUTS.map(c => ({ t: c, k: 'whoosh' })), { t: DUR, k: 'whoosh' },
];

// ---------------------------------------------------------------- boot
async function boot() {
  await Promise.all(IMG_LIST.map(loadImg));
  const [srt, topo] = await Promise.all([fetch('assets/voice.srt').then(r => r.text()), fetch('vendor/countries-110m.json').then(r => r.json())]);
  WORDS = parseSrt(srt);
  WORLD = topojson.feature(topo, topo.objects.land);
  WORLD_BORDERS = topojson.mesh(topo, topo.objects.countries, (a, b) => a !== b);
  const feats = topojson.feature(topo, topo.objects.countries).features;
  COUNTRIES = new Map(feats.map(f => [+f.id, f]));
  await document.fonts.load(`800 ${CAP_FONT}px Alexandria`, 'إذا تسوي');
  await document.fonts.load('800 40px Alexandria', 'KLOVA 0123');
  buildBackgrounds();
  window.renderFrame = renderFrame;
  window.SFX = SFX;
  window.FRAMES = Math.round(DUR * FPS);
  window.ready = true;
}
boot().catch(e => { window.bootError = String(e && e.stack || e); });
