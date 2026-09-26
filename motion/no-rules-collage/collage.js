'use strict';
// «لا توجد أي قواعد» — 15s paper-collage motion piece, 1080x1920 @ 24fps, 120 BPM grid (beat = 0.5s)

const W = 1080, H = 1920, FPS = 24, DUR = 15, NF = FPS * DUR, M = 60;
const cv = document.getElementById('c');
const MAIN = cv.getContext('2d');
let g = MAIN, FRAME = 0;

const C = {
  kraft: '#C49A6A', cream: '#F2EADA', paper: '#FBF8EF', ink: '#171412', red: '#E63F2A',
  blue: '#2345D5', yellow: '#F7C21B', pink: '#F4A2BC', navy: '#15214D', orange: '#F07A1E',
  green: '#1E9C6A', inkBlue: '#1C3A8C',
};

// ---------- math ----------
function R(seed) {
  let a = (seed * 2654435761) >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const E = {
  out2: t => 1 - (1 - t) * (1 - t),
  out3: t => 1 - Math.pow(1 - t, 3),
  in2: t => t * t,
  in3: t => t * t * t,
  io3: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  back: t => { const s = 2.4; return 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2); },
};
const D2R = Math.PI / 180;
const st = t => Math.floor(t * 12 + 1e-4) / 12; // stop-motion "on twos"
const isAr = s => /[؀-ۿ]/.test(s);
const mk = (w, h) => { const c = document.createElement('canvas'); c.width = Math.max(1, Math.ceil(w)); c.height = Math.max(1, Math.ceil(h)); return c; };
const spr = (c, extra = {}) => ({ c, ax: c.width / 2, ay: c.height / 2, ...extra });
function withCtx(x, fn) { const p = g; g = x; try { fn(); } finally { g = p; } }
function poly(x, pts) { x.beginPath(); pts.forEach(([a, b], i) => (i ? x.lineTo(a, b) : x.moveTo(a, b))); x.closePath(); }
function rot2(x, y, r) { const c = Math.cos(r * D2R), s = Math.sin(r * D2R); return [x * c - y * s, x * s + y * c]; }

const FONT = {
  lalezar: s => `${s}px "Lalezar"`,
  rakkas: s => `${s}px "Rakkas"`,
  jomhuria: s => `${s}px "Jomhuria"`,
  blaka: s => `${s}px "Blaka"`,
  kufi: s => `700 ${s}px "Reem Kufi"`,
  ruqaa: s => `700 ${s}px "Aref Ruqaa"`,
  ruqaaR: s => `400 ${s}px "Aref Ruqaa"`,
  amiri: s => `400 ${s}px "Amiri"`,
  amiriB: s => `700 ${s}px "Amiri"`,
  cairo: s => `900 ${s}px "Cairo"`,
  marhey: s => `700 ${s}px "Marhey"`,
  anton: s => `${s}px "Anton"`,
  type: s => `${s}px "Special Elite"`,
  marker: s => `${s}px "Permanent Marker"`,
};

// ---------- textures ----------
let TEX, BGTEX, GRAIN = [], VIG;
function noiseLayer(x, w, h, r, cell, alpha) {
  const sw = Math.ceil(w / cell) + 3, sh = Math.ceil(h / cell) + 3;
  const s = mk(sw, sh), sx = s.getContext('2d'), id = sx.createImageData(sw, sh);
  for (let p = 0; p < sw * sh; p++) { const v = (r() * 255) | 0; id.data[p * 4] = id.data[p * 4 + 1] = id.data[p * 4 + 2] = v; id.data[p * 4 + 3] = 255; }
  sx.putImageData(id, 0, 0);
  x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
  x.globalAlpha = alpha; x.drawImage(s, -cell * 1.5, -cell * 1.5, sw * cell, sh * cell); x.globalAlpha = 1;
}
function paperTexture(w, h, seed) {
  const c = mk(w, h), x = c.getContext('2d'), r = R(seed);
  x.fillStyle = '#808080'; x.fillRect(0, 0, w, h);
  noiseLayer(x, w, h, r, 280, 0.22); noiseLayer(x, w, h, r, 70, 0.2); noiseLayer(x, w, h, r, 16, 0.16);
  const id = x.getImageData(0, 0, w, h), d = id.data;
  for (let i = 0; i < d.length; i += 4) { const n = (r() - 0.5) * 30; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
  x.putImageData(id, 0, 0);
  const nf = (w * h) / 650;
  for (let i = 0; i < nf; i++) {
    const px = r() * w, py = r() * h, len = 5 + r() * 24, a = r() * Math.PI * 2;
    x.strokeStyle = r() < 0.5 ? `rgba(255,255,255,${0.1 + r() * 0.14})` : `rgba(0,0,0,${0.06 + r() * 0.1})`;
    x.lineWidth = 0.5 + r() * 0.9; x.beginPath(); x.moveTo(px, py);
    x.quadraticCurveTo(px + Math.cos(a) * len / 2 + (r() - 0.5) * 6, py + Math.sin(a) * len / 2 + (r() - 0.5) * 6, px + Math.cos(a) * len, py + Math.sin(a) * len);
    x.stroke();
  }
  return c;
}
function texFill(x, w, h, alpha, seed, mode = 'overlay') {
  const r = R(seed + 101);
  x.save(); x.globalCompositeOperation = mode; x.globalAlpha = alpha;
  const ox = r() * Math.max(0, TEX.width - w - 200), oy = r() * Math.max(0, TEX.height - h - 200);
  x.translate(-ox, -oy);
  x.fillStyle = x.createPattern(TEX, 'repeat'); x.fillRect(-300, -300, w + ox + 600, h + oy + 600);
  x.restore();
}
function texturize(c, alpha = 0.5, seed = 1) {
  const x = c.getContext('2d'), mask = mk(c.width, c.height);
  mask.getContext('2d').drawImage(c, 0, 0);
  x.save(); x.setTransform(1, 0, 0, 1, 0, 0);
  texFill(x, c.width, c.height, alpha, seed);
  x.globalCompositeOperation = 'destination-in'; x.drawImage(mask, 0, 0); x.restore();
}
function inkify(x, w, h, amt, seed) {
  const r = R(seed + 7); const n = (w * h / 650) * amt;
  x.save(); x.globalCompositeOperation = 'destination-out';
  for (let i = 0; i < n; i++) { x.globalAlpha = 0.2 + r() * 0.65; x.beginPath(); x.arc(r() * w, r() * h, 0.4 + r() * r() * 3.4, 0, 7); x.fill(); }
  x.restore();
}

// ---------- text ----------
const MEAS = mk(8, 8).getContext('2d');
function setText(x, txt, font) { x.font = font; x.direction = isAr(txt) ? 'rtl' : 'ltr'; x.textAlign = 'center'; x.textBaseline = 'alphabetic'; }
function measure(txt, font) {
  setText(MEAS, txt, font); const m = MEAS.measureText(txt);
  return { w: m.actualBoundingBoxLeft + m.actualBoundingBoxRight, h: m.actualBoundingBoxAscent + m.actualBoundingBoxDescent, l: m.actualBoundingBoxLeft, a: m.actualBoundingBoxAscent };
}
function textCanvas(txt, font, color, o = {}) {
  const m = measure(txt, font), sw = o.margin || 0, hd = o.hard || 0, pad = 24 + sw + hd;
  const c = mk(m.w + pad * 2, m.h + pad * 2), x = c.getContext('2d');
  setText(x, txt, font);
  const ox = pad + m.l, oy = pad + m.a;
  if (sw) {
    const r = R(o.seed || 3); x.lineJoin = 'round'; x.lineWidth = sw * 2; x.strokeStyle = o.marginColor; x.fillStyle = o.marginColor;
    for (let k = 0; k < 5; k++) x.strokeText(txt, ox + (r() - 0.5) * sw * 0.5, oy + (r() - 0.5) * sw * 0.5);
  }
  if (hd) { x.fillStyle = o.hardColor || C.ink; x.fillText(txt, ox + hd, oy + hd); if (sw) { x.lineWidth = sw * 2; x.strokeStyle = o.hardColor || C.ink; x.strokeText(txt, ox + hd, oy + hd); } }
  x.fillStyle = color; x.fillText(txt, ox, oy);
  if (o.worn !== 0) inkify(x, c.width, c.height, o.worn ?? 0.8, o.seed || 5);
  return { c, w: c.width, h: c.height, m, pad };
}
function cutWord(txt, font, color, o = {}) {
  const t = textCanvas(txt, font, color, o);
  texturize(t.c, o.tex ?? 0.55, o.seed || 2);
  return spr(t.c, { w: t.m.w, h: t.m.h });
}

// ---------- paper scraps ----------
function tornShape(w, h, seed, o = {}) {
  const r = R(seed), rough = o.rough ?? 9, step = o.step ?? 6, torn = o.torn ?? [1, 1, 1, 1], cj = o.cj ?? 6;
  const corners = [[0, 0], [w, 0], [w, h], [0, h]].map(([x, y]) => [x + (r() - 0.5) * 2 * cj, y + (r() - 0.5) * 2 * cj]);
  const outer = [], inner = [];
  for (let e = 0; e < 4; e++) {
    const [x0, y0] = corners[e], [x1, y1] = corners[(e + 1) % 4];
    const dx = x1 - x0, dy = y1 - y0, len = Math.hypot(dx, dy), nx = dy / len, ny = -dx / len;
    const n = Math.max(2, Math.round(len / step));
    let wv = 0, wi = 0; const p1 = r() * 9, p2 = r() * 9, p3 = r() * 9;
    for (let i = 0; i < n; i++) {
      const u = i / n, bx = x0 + dx * u, by = y0 + dy * u;
      if (torn[e]) {
        wv = wv * 0.8 + (r() - 0.5) * rough * 0.7;
        const d = wv + Math.sin(u * len / 90 + p1) * rough * 0.45 + Math.sin(u * len / 31 + p2) * rough * 0.25;
        outer.push([bx + nx * d, by + ny * d]);
        wi = wi * 0.7 + (r() - 0.5) * 4;
        const inset = Math.max(1.5, 3 + (Math.sin(u * len / 45 + p3) * 0.5 + 0.5) * 8 + wi);
        inner.push([bx + nx * (d - inset), by + ny * (d - inset)]);
      } else { outer.push([bx, by]); inner.push([bx, by]); }
    }
  }
  return { outer, inner, hasTorn: torn.some(Boolean) };
}
function scrap(w, h, fill, o = {}) {
  const pad = o.pad ?? 34, seed = o.seed ?? 1;
  const c = mk(w + pad * 2, h + pad * 2), x = c.getContext('2d'); x.translate(pad, pad);
  const sh = tornShape(w, h, seed, o);
  if (sh.hasTorn) { poly(x, sh.outer); x.fillStyle = o.edge ?? '#FBF7EC'; x.fill(); }
  x.save(); poly(x, sh.inner); x.fillStyle = fill; x.fill(); x.clip();
  if (o.inside) o.inside(x, w, h);
  x.restore();
  x.save(); poly(x, sh.outer); x.clip(); texFill(x, w, h, o.tex ?? 0.55, seed); x.restore();
  if (o.after) o.after(x, w, h);
  return spr(c, { w, h });
}
function wordScrap(txt, font, o) {
  const t = textCanvas(txt, font, o.color, { worn: o.worn ?? 0.8, seed: o.seed });
  const px = o.px ?? 56, py = o.py ?? 38, w = t.m.w + px * 2, h = t.m.h + py * 2;
  return scrap(w, h, o.bg, { ...o, inside: (x, w, h) => { x.drawImage(t.c, w / 2 - t.w / 2 + (o.dx ?? 0), h / 2 - t.h / 2 + (o.dy ?? 0)); } });
}
function circlePts(rad, seed, jit = 1.6, n = 90) {
  const r = R(seed), pts = []; let wv = 0;
  for (let i = 0; i < n; i++) { wv = wv * 0.6 + (r() - 0.5) * jit; const a = (i / n) * Math.PI * 2; pts.push([Math.cos(a) * (rad + wv), Math.sin(a) * (rad + wv)]); }
  return pts;
}
function shapeSprite(w, h, pts, fill, seed, o = {}) {
  const pad = 20, c = mk(w + pad * 2, h + pad * 2), x = c.getContext('2d');
  x.translate(pad + w / 2, pad + h / 2); poly(x, pts); x.fillStyle = fill; x.fill();
  if (o.inside) { x.save(); x.clip(); o.inside(x); x.restore(); }
  texturize(c, o.tex ?? 0.5, seed);
  return spr(c, { w, h });
}
function jitterPts(pts, seed, a) { const r = R(seed); return pts.map(([x, y]) => [x + (r() - 0.5) * a, y + (r() - 0.5) * a]); }
function starSprite(r1, r2, n, fill, seed) {
  const pts = []; for (let i = 0; i < n * 2; i++) { const a = (i / (n * 2)) * Math.PI * 2 - Math.PI / 2, rr = i % 2 ? r2 : r1; pts.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
  return shapeSprite(r1 * 2, r1 * 2, jitterPts(pts, seed, 7), fill, seed);
}
function triSprite(w, h, fill, seed) { return shapeSprite(w, h, jitterPts([[0, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]], seed, 8), fill, seed); }
function circleSprite(rad, fill, seed) { return shapeSprite(rad * 2, rad * 2, circlePts(rad, seed), fill, seed); }
function halftoneDisc(rad, base, dot, o = {}) {
  const cell = o.cell || 17, ang = (o.ang ?? 15) * D2R, hl = o.hl ?? [-0.35, -0.4];
  return shapeSprite(rad * 2, rad * 2, circlePts(rad, o.seed || 3, 1.4), base, o.seed || 3, {
    inside: x => {
      x.fillStyle = dot;
      for (let gy = -rad * 1.5; gy < rad * 1.5; gy += cell) for (let gx = -rad * 1.5; gx < rad * 1.5; gx += cell) {
        const px = gx * Math.cos(ang) - gy * Math.sin(ang), py = gx * Math.sin(ang) + gy * Math.cos(ang);
        const v = clamp(Math.hypot(px - rad * hl[0], py - rad * hl[1]) / (rad * 1.55) * (o.gain ?? 1.15) - 0.12);
        const rr = cell * 0.6 * Math.sqrt(v); if (rr > 0.7) { x.beginPath(); x.arc(px, py, rr, 0, 7); x.fill(); }
      }
    },
  });
}
function halftoneField(rad, color, cell = 22, seed = 4) {
  const c = mk(rad * 2 + 20, rad * 2 + 20), x = c.getContext('2d'); x.translate(rad + 10, rad + 10); x.fillStyle = color;
  const ang = 20 * D2R;
  for (let gy = -rad * 1.5; gy < rad * 1.5; gy += cell) for (let gx = -rad * 1.5; gx < rad * 1.5; gx += cell) {
    const px = gx * Math.cos(ang) - gy * Math.sin(ang), py = gx * Math.sin(ang) + gy * Math.cos(ang);
    const v = clamp(1 - Math.hypot(px, py) / rad); const rr = cell * 0.62 * Math.sqrt(v);
    if (rr > 0.7) { x.beginPath(); x.arc(px, py, rr, 0, 7); x.fill(); }
  }
  texturize(c, 0.4, seed);
  return spr(c);
}
function tapeSprite(w, h, seed) {
  const pad = 16, c = mk(w + pad * 2, h + pad * 2), x = c.getContext('2d'); x.translate(pad, pad);
  const r = R(seed), pts = [[0, 0], [w, 0]], zz = Math.max(4, Math.round(h / 7));
  for (let i = 1; i < zz; i++) pts.push([w + (i % 2 ? -6 : 2) + (r() - 0.5) * 4, (h * i) / zz]);
  pts.push([w, h], [0, h]);
  for (let i = zz - 1; i > 0; i--) pts.push([(i % 2 ? 6 : -2) + (r() - 0.5) * 4, (h * i) / zz]);
  poly(x, pts); x.fillStyle = 'rgba(238,228,194,0.82)'; x.fill();
  x.save(); x.clip();
  for (let i = 0; i < 16; i++) { x.fillStyle = `rgba(255,255,255,${0.04 + r() * 0.12})`; x.fillRect(0, r() * h, w, 1 + r() * 3); }
  texFill(x, w, h, 0.3, seed); x.restore();
  x.strokeStyle = 'rgba(110,90,50,0.22)'; x.lineWidth = 1.2; poly(x, pts); x.stroke();
  return spr(c, { w, h });
}
function stampSprite(R0, color, seed = 9) {
  const S = R0 * 2 + 40, c = mk(S, S), x = c.getContext('2d'); x.translate(S / 2, S / 2);
  x.strokeStyle = color; x.fillStyle = color;
  x.lineWidth = 11; x.beginPath(); x.arc(0, 0, R0 - 8, 0, 7); x.stroke();
  x.lineWidth = 4; x.beginPath(); x.arc(0, 0, R0 - 44, 0, 7); x.stroke();
  const txt = 'NO RULES · NO RULES · '; x.font = FONT.anton(Math.round(R0 * 0.22)); x.textAlign = 'center'; x.textBaseline = 'middle';
  for (let i = 0; i < txt.length; i++) { x.save(); x.rotate((i / txt.length) * Math.PI * 2); x.translate(0, -(R0 - 26)); x.fillText(txt[i], 0, 0); x.restore(); }
  const f = FONT.lalezar(Math.round(R0 * 0.78)), m = measure('حُر', f); setText(x, 'حُر', f);
  x.fillText('حُر', m.l - m.w / 2, m.a - m.h / 2);
  const r = R(seed); x.globalCompositeOperation = 'destination-out';
  for (let i = 0; i < 900; i++) { x.globalAlpha = 0.25 + r() * 0.75; x.beginPath(); x.arc((r() - 0.5) * S, (r() - 0.5) * S, 0.5 + r() * r() * 5, 0, 7); x.fill(); }
  x.globalAlpha = 0.5; x.lineWidth = 2;
  for (let i = 0; i < 6; i++) { x.beginPath(); const a = r() * 7; x.moveTo(Math.cos(a) * R0, Math.sin(a) * R0); x.lineTo(Math.cos(a + 2.5) * R0, Math.sin(a + 2.5) * R0); x.stroke(); }
  return spr(c);
}
const WORDS = 'الفن التصميم الفكرة حر بلا حدود اللون الورق المقص الصمغ الحركة إيقاع خيال تجربة جديد مساحة صورة كلمة قصة عالم ضوء ظل شكل خط نقطة فوضى جميلة صناعة إبداع يوم كل من في على إلى مع هذا التي الذي قد هو هي بين عن المدينة الناس الوقت الصباح الشارع البحر الطريق الحلم القلب الصوت'.split(' ');
function newsLayout(x, w, h, seed, o = {}) {
  const r = R(seed), m = o.margin ?? 44; let y = m;
  x.fillStyle = C.ink;
  if (o.masthead) {
    setText(x, o.masthead, FONT.amiriB(o.mastSize || 118)); x.fillText(o.masthead, w / 2, y + (o.mastSize || 118) * 0.95);
    y += (o.mastSize || 118) * 1.25;
    x.fillRect(m, y, w - 2 * m, 6); x.fillRect(m, y + 12, w - 2 * m, 2);
    setText(x, o.dateline, FONT.amiri(30)); x.fillText(o.dateline, w / 2, y + 52); y += 72;
    x.fillRect(m, y, w - 2 * m, 2); y += 22;
  }
  const cols = o.cols ?? 3, gap = 28, cw = (w - 2 * m - gap * (cols - 1)) / cols;
  for (let ci = 0; ci < cols; ci++) {
    const right = w - m - ci * (cw + gap), left = right - cw;
    x.save(); x.beginPath(); x.rect(left, y, cw, h - y - m); x.clip();
    let yy = y + (ci === 0 && o.head ? 0 : 6);
    if (ci === 0 && o.head) {
      setText(x, o.head, FONT.amiriB(o.headSize || 58)); x.textAlign = 'right'; x.fillStyle = C.ink;
      x.fillText(o.head, right, yy + (o.headSize || 58)); yy += (o.headSize || 58) * 1.4;
    }
    while (yy < h - m) {
      const k = r();
      if (k < 0.12) {
        x.font = FONT.amiriB(40); x.textAlign = 'right'; x.fillStyle = C.ink;
        x.fillText(lineOf(x, r, cw * 0.95), right, yy + 40); yy += 58;
      } else if (k < 0.22) {
        const ih = cw * (0.55 + r() * 0.3); x.fillStyle = '#d9d0bd'; x.fillRect(left, yy, cw, ih);
        x.save(); x.beginPath(); x.rect(left, yy, cw, ih); x.clip(); x.fillStyle = '#2a2520';
        const cxp = left + cw * (0.3 + r() * 0.4), cyp = yy + ih * (0.3 + r() * 0.4), cr = ih * 0.4;
        for (let gy = yy; gy < yy + ih; gy += 9) for (let gx = left; gx < right; gx += 9) {
          const v = clamp(0.2 + ((gy - yy) / ih) * 0.45 + (Math.hypot(gx - cxp, gy - cyp) < cr ? 0.35 : 0));
          x.beginPath(); x.arc(gx, gy, 4.6 * Math.sqrt(v), 0, 7); x.fill();
        }
        x.restore(); yy += ih + 16;
      } else {
        x.font = FONT.amiri(25); x.textAlign = 'right'; x.fillStyle = '#3a342c';
        const n = 3 + ((r() * 8) | 0);
        for (let l = 0; l < n && yy < h - m; l++) { x.fillText(lineOf(x, r, l === n - 1 ? cw * (0.4 + r() * 0.5) : cw), right, yy + 26); yy += 34; }
        yy += 12;
      }
    }
    x.restore();
    if (ci < cols - 1) { x.fillStyle = 'rgba(0,0,0,.28)'; x.fillRect(left - gap / 2, y, 1.5, h - y - m); }
  }
}
function lineOf(x, r, maxW) {
  x.direction = 'rtl'; let s = '';
  for (let k = 0; k < 30; k++) { const wd = WORDS[(r() * WORDS.length) | 0], s2 = s ? s + ' ' + wd : wd; if (x.measureText(s2).width > maxW) break; s = s2; }
  return s;
}
function paperBG(color, texA, seed, extra) {
  const c = mk(W + M * 2, H + M * 2), x = c.getContext('2d');
  x.fillStyle = color; x.fillRect(0, 0, c.width, c.height);
  if (extra) { x.save(); x.translate(M, M); extra(x); x.restore(); }
  x.globalCompositeOperation = 'overlay'; x.globalAlpha = texA; x.drawImage(BGTEX, 0, 0);
  x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;
  return c;
}
function bg(c) { g.drawImage(c, -M, -M); }

// ---------- sprite placement ----------
function put(sp, x, y, o = {}) {
  const s = o.s ?? 1;
  g.save(); g.translate(x, y); g.rotate((o.r ?? 0) * D2R); g.scale(s * (o.sx ?? 1), s * (o.sy ?? 1));
  g.globalAlpha = o.a ?? 1; if (o.comp) g.globalCompositeOperation = o.comp;
  if ((o.shadow ?? 1) > 0) {
    const L = (o.lift ?? 1) * (1 + Math.max(0, s - 1) * 3), k = o.shadow ?? 1;
    g.shadowColor = `rgba(28,16,6,${0.4 * k})`; g.shadowBlur = 9 + 7 * L; g.shadowOffsetX = 3 + 5 * L; g.shadowOffsetY = 6 + 8 * L;
  }
  g.drawImage(sp.c, -sp.ax, -sp.ay);
  g.restore();
}
function boil(id, t, amp = 1.6, ramp = 0.45) {
  const k = Math.floor(t * 8 + 1e-4), r = R(id * 7919 + k * 104729 + 17);
  return { x: (r() - 0.5) * 2 * amp, y: (r() - 0.5) * 2 * amp, r: (r() - 0.5) * 2 * ramp };
}
function putB(id, t, sp, x, y, o = {}) { const b = boil(id, t, o.amp, o.ramp); put(sp, x + b.x, y + b.y, { ...o, r: (o.r ?? 0) + b.r }); }
function slam(t, t0, dur = 0.125, from = 1.85) {
  if (t < t0) return null;
  const p = prog(t, t0, t0 + dur), e = E.out3(p);
  let s = lerp(from, 1, e);
  if (p >= 1) s = 1 - 0.05 * Math.sin(prog(t, t0 + dur, t0 + dur + 0.125) * Math.PI);
  return { s, e, lift: 1 + Math.max(0, s - 1) * 2.5 };
}
function tapeIn(id, t, t0, sp, x, y, r) {
  if (t < t0) return; const s = lerp(1.3, 1, E.out3(prog(t, t0, t0 + 0.084)));
  putB(id, t, sp, x, y, { r, s, lift: 0.25 + (s - 1) * 2 });
}
function stampIn(t, t0, sp, x, y, r) {
  if (t < t0) return; const p = prog(t, t0, t0 + 0.084);
  put(sp, x, y, { r, s: lerp(1.35, 1, p), a: p < 1 ? 0.6 : 0.9, comp: 'multiply', shadow: 0 });
}
function enter(id, t, t0, sp, from, to, r0, r1, dur = 0.21, o = {}) {
  const tq = st(t); if (tq < t0) return;
  const p = E.out3(prog(tq, t0, t0 + dur));
  putB(id, t, sp, lerp(from[0], to[0], p), lerp(from[1], to[1], p), { ...o, r: lerp(r0, r1, p), lift: (o.lift ?? 1) + (1 - p) * 2 });
}
function corner(x, y, w, h, r, sx, sy, inset = 30) { const [dx, dy] = rot2(sx * (w / 2 - inset), sy * (h / 2 - inset), r); return [x + dx, y + dy]; }
function markerLoop(cx, cy, rx, ry, rot, p, seed, color, width) {
  if (p <= 0) return;
  const r = R(seed), N = 150, turns = 1.16, a0 = -2.4, ph = r() * 6, ph2 = r() * 6;
  const pts = [];
  for (let i = 0; i <= N; i++) {
    const u = i / N, a = a0 + u * turns * Math.PI * 2, k = 1 + 0.05 * Math.sin(u * 9 + ph) + 0.08 * u + 0.02 * Math.sin(u * 23 + ph2);
    const [dx, dy] = rot2(Math.cos(a) * rx * k, Math.sin(a) * ry * k, rot); pts.push([cx + dx, cy + dy]);
  }
  const n = Math.floor(p * N);
  g.save(); g.globalCompositeOperation = 'multiply'; g.strokeStyle = color; g.lineCap = 'round'; g.globalAlpha = 0.93;
  for (let i = 0; i < n; i++) {
    const u = i / N; g.lineWidth = width * (0.75 + 0.35 * Math.sin(u * Math.PI) + 0.1 * Math.sin(u * 17));
    g.beginPath(); g.moveTo(pts[i][0], pts[i][1]); g.lineTo(pts[i + 1][0], pts[i + 1][1]); g.stroke();
  }
  g.restore();
}

// ---------- special sprites ----------
function scissorHalf() {
  const c = mk(760, 300), x = c.getContext('2d'), px = 470, py = 150; x.translate(px, py);
  // blade (above the axis, pointing to -x)
  x.beginPath(); x.moveTo(46, -2); x.lineTo(-10, 5); x.quadraticCurveTo(-220, 9, -440, 1);
  x.quadraticCurveTo(-270, -26, -60, -34); x.quadraticCurveTo(20, -34, 46, -2); x.closePath();
  const gr = x.createLinearGradient(0, -34, 0, 8); gr.addColorStop(0, '#3b3e46'); gr.addColorStop(0.45, '#d9dce2'); gr.addColorStop(0.6, '#9ea3ad'); gr.addColorStop(1, '#2b2d33');
  x.fillStyle = gr; x.fill(); x.lineWidth = 3.5; x.strokeStyle = C.ink; x.stroke();
  x.strokeStyle = 'rgba(255,255,255,.7)'; x.lineWidth = 2; x.beginPath(); x.moveTo(-40, -18); x.quadraticCurveTo(-200, -12, -380, -2); x.stroke();
  // shank + ring (below the axis, to +x)
  x.beginPath(); x.moveTo(20, -10); x.quadraticCurveTo(90, 0, 150, 40); x.lineTo(132, 62); x.quadraticCurveTo(80, 28, 10, 18); x.closePath();
  x.fillStyle = C.red; x.fill(); x.lineWidth = 3.5; x.strokeStyle = C.ink; x.stroke();
  x.beginPath(); x.ellipse(205, 78, 78, 58, 0.35, 0, Math.PI * 2); x.ellipse(205, 78, 48, 32, 0.35, 0, Math.PI * 2, true);
  x.fillStyle = C.red; x.fill('evenodd'); x.stroke();
  texturize(c, 0.45, 12);
  return spr(c, { ax: px, ay: py });
}
function scissorsDraw(x, y, rot, open, lift = 2.4) {
  const [H1, H2] = [A.sciA, A.sciB];
  put(H2, x, y, { r: rot - open / 2, sy: -1, lift });
  put(H1, x, y, { r: rot + open / 2, lift });
  g.save(); g.translate(x, y); g.fillStyle = '#7d828c'; g.strokeStyle = C.ink; g.lineWidth = 3; g.beginPath(); g.arc(0, 0, 13, 0, 7); g.fill(); g.stroke();
  g.beginPath(); g.moveTo(-7, 0); g.lineTo(7, 0); g.stroke(); g.restore();
}
function eyeSprite() {
  return scrap(380, 230, '#F6F1E6', {
    seed: 61, rough: 7, inside: (x, w, h) => {
      x.save(); x.translate(w / 2, h / 2 + 6); const ew = 150, eh = 84;
      const almond = () => { x.beginPath(); x.moveTo(-ew, 0); x.bezierCurveTo(-ew * 0.5, -eh * 1.25, ew * 0.5, -eh * 1.25, ew, 0); x.bezierCurveTo(ew * 0.5, eh * 1.15, -ew * 0.5, eh * 1.15, -ew, 0); x.closePath(); };
      almond(); x.fillStyle = '#fff'; x.fill(); x.save(); x.clip();
      x.fillStyle = C.blue; x.beginPath(); x.arc(0, -4, 64, 0, 7); x.fill();
      x.strokeStyle = 'rgba(8,16,60,.55)'; x.lineWidth = 2;
      for (let a = 0; a < 44; a++) { const an = (a / 44) * Math.PI * 2; x.beginPath(); x.moveTo(Math.cos(an) * 30, -4 + Math.sin(an) * 30); x.lineTo(Math.cos(an) * 63, -4 + Math.sin(an) * 63); x.stroke(); }
      x.fillStyle = C.ink; x.beginPath(); x.arc(0, -4, 28, 0, 7); x.fill();
      x.fillStyle = '#fff'; x.beginPath(); x.arc(-18, -22, 11, 0, 7); x.fill();
      x.fillStyle = 'rgba(0,0,0,.18)'; x.fillRect(-ew, -eh, ew * 2, 26);
      x.restore(); almond(); x.lineWidth = 7; x.strokeStyle = C.ink; x.stroke();
      x.lineCap = 'round'; x.lineWidth = 6;
      for (let i = 0; i < 7; i++) {
        const u = 0.18 + (i / 6) * 0.64, P0 = [-ew, 0], P1 = [-ew * 0.5, -eh * 1.25], P2 = [ew * 0.5, -eh * 1.25], P3 = [ew, 0];
        const b = k => (1 - u) ** 3 * P0[k] + 3 * (1 - u) ** 2 * u * P1[k] + 3 * (1 - u) * u * u * P2[k] + u ** 3 * P3[k];
        const bx = b(0), by = b(1), nl = Math.hypot(bx, by + 60), nx = bx / nl, ny = (by + 60) / nl;
        x.beginPath(); x.moveTo(bx, by); x.lineTo(bx + nx * 24, by + ny * 24); x.stroke();
      }
      x.restore();
    },
  });
}
function checkerSprite(size, seed) {
  return scrap(size, size, C.cream, {
    seed, torn: [0, 0, 0, 0], cj: 5, inside: (x, w, h) => {
      const n = 5, s = w / n; x.fillStyle = C.ink;
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) if ((i + j) % 2) x.fillRect(i * s - 1, j * s - 1, s + 2, s + 2);
    },
  });
}
function squiggleSprite(color, seed) {
  const c = mk(340, 140), x = c.getContext('2d'); x.translate(170, 70);
  x.strokeStyle = color; x.lineWidth = 22; x.lineCap = 'round'; x.lineJoin = 'round'; x.beginPath();
  for (let i = -140; i <= 140; i += 4) { const y = Math.sin(i / 21) * 30; i === -140 ? x.moveTo(i, y) : x.lineTo(i, y); }
  x.stroke(); texturize(c, 0.5, seed); return spr(c);
}
function polaroidSprite() {
  const w = 380, h = 452;
  return scrap(w, h, '#FAF8F2', {
    seed: 31, torn: [0, 0, 0, 0], cj: 3, tex: 0.4, inside: (x) => {
      x.fillStyle = C.navy; x.fillRect(28, 28, w - 56, w - 56);
      const r = R(33); x.fillStyle = 'rgba(255,255,255,.8)';
      for (let i = 0; i < 40; i++) { x.beginPath(); x.arc(28 + r() * (w - 56), 28 + r() * (w - 56), 0.6 + r() * 1.8, 0, 7); x.fill(); }
      const moon = A.moon; x.drawImage(moon.c, w / 2 - moon.ax, 28 + (w - 56) / 2 - moon.ay);
      setText(x, 'بلا قواعد', FONT.ruqaaR(50)); x.fillStyle = C.inkBlue; x.fillText('بلا قواعد', w / 2, h - 22);
    },
  });
}
function notebookSprite(w, h) {
  return scrap(w, h, '#FBF8EE', {
    seed: 41, torn: [1, 0, 0, 0], rough: 8, cj: 4, inside: (x, w, h) => {
      x.strokeStyle = 'rgba(70,120,205,.55)'; x.lineWidth = 2.5;
      for (let y = 210; y < h - 20; y += 66) { x.beginPath(); x.moveTo(0, y); x.lineTo(w, y); x.stroke(); }
      x.strokeStyle = 'rgba(225,60,60,.65)'; x.lineWidth = 3; x.beginPath(); x.moveTo(w - 150, 0); x.lineTo(w - 150, h); x.stroke();
      setText(x, 'القواعد:', FONT.ruqaa(96)); x.textAlign = 'right'; x.fillStyle = C.ink; x.fillText('القواعد:', w - 180, 180);
      const items = ['١. التزم بالخطوط', '٢. لا تخرج عن الإطار', '٣. اتبع القالب', '٤. لا تُخطئ أبداً', '٥. انتظر الإذن'];
      x.font = FONT.ruqaaR(60); x.fillStyle = C.inkBlue;
      items.forEach((s, i) => { x.fillText(s, w - 180, 262 + 66 * (i + 1) + (i > 2 ? 330 : 0)); });
    },
    after: (x, w) => { x.save(); x.globalCompositeOperation = 'destination-out'; [260, 640, 1020].forEach(y => { x.beginPath(); x.arc(w - 70, y, 22, 0, 7); x.fill(); }); x.restore(); },
  });
}

// ---------- assets ----------
const A = {};
function build() {
  TEX = paperTexture(2048, 2048, 11);
  BGTEX = paperTexture(W + M * 2, H + M * 2, 21);
  for (let i = 0; i < 6; i++) {
    const c = mk(540, 960), x = c.getContext('2d'), id = x.createImageData(540, 960), r = R(500 + i);
    for (let p = 0; p < 540 * 960; p++) { const v = 128 + (r() + r() + r() - 1.5) * 90; id.data[p * 4] = id.data[p * 4 + 1] = id.data[p * 4 + 2] = v; id.data[p * 4 + 3] = 255; }
    x.putImageData(id, 0, 0); GRAIN.push(c);
  }
  VIG = mk(W, H); { const x = VIG.getContext('2d'), gr = x.createRadialGradient(W / 2, H / 2, H * 0.28, W / 2, H / 2, H * 0.72); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.42)'); x.fillStyle = gr; x.fillRect(0, 0, W, H); }

  // backgrounds
  A.kraft = paperBG(C.kraft, 0.95, 1, x => { const r = R(55); for (let i = 0; i < 2600; i++) { x.fillStyle = `rgba(${(60 + r() * 40) | 0},${(35 + r() * 20) | 0},15,${0.12 + r() * 0.35})`; x.beginPath(); x.arc(r() * W, r() * H, 0.4 + r() * 1.7, 0, 7); x.fill(); } });
  A.blueBG = paperBG(C.blue, 0.6, 2, x => { const f = halftoneField(520, 'rgba(12,24,90,.55)', 26, 7); x.drawImage(f.c, -300, H - 700); x.drawImage(f.c, W - 450, -520); });
  A.blackBG = paperBG('#151311', 0.7, 3);
  A.creamBG = paperBG('#F0E8D6', 0.75, 4, x => { const f = halftoneField(360, 'rgba(35,69,213,.22)', 22, 8); x.drawImage(f.c, W - 380, -260); x.drawImage(f.c, -300, H - 480); });
  A.redBG = paperBG(C.red, 0.6, 5, x => { const f = halftoneField(560, 'rgba(120,10,0,.4)', 28, 9); x.drawImage(f.c, W - 520, -560); x.drawImage(f.c, -600, H - 600); });
  A.mixBG = [C.yellow, C.blue, C.red, C.pink].map((c, i) => paperBG(c, 0.6, 10 + i));
  A.bands = [[C.blue, 11], [C.yellow, 12], [C.cream, 13], [C.ink, 14]].map(([c, s]) => scrap(1700, 440, c, { seed: s, torn: [1, 0, 1, 0], rough: 14 }));

  // scene 1
  A.graph = scrap(470, 350, '#FDFCF7', { seed: 7, torn: [1, 0, 1, 0], inside: (x, w, h) => {
    x.strokeStyle = 'rgba(60,120,200,.35)'; x.lineWidth = 1.2; for (let i = 0; i < w; i += 22) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i, h); x.stroke(); } for (let j = 0; j < h; j += 22) { x.beginPath(); x.moveTo(0, j); x.lineTo(w, j); x.stroke(); }
    x.strokeStyle = 'rgba(60,120,200,.6)'; x.lineWidth = 2.2; for (let i = 0; i < w; i += 110) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i, h); x.stroke(); } for (let j = 0; j < h; j += 110) { x.beginPath(); x.moveTo(0, j); x.lineTo(w, j); x.stroke(); }
  } });
  A.pinkDots = halftoneField(330, C.pink, 24, 5);
  A.news1 = scrap(600, 560, '#EFE8D6', { seed: 5, rough: 10, inside: (x, w, h) => newsLayout(x, w, h, 5, { cols: 2, head: 'الفن لا يطلب إذناً' }) });
  A.starBlack = starSprite(96, 40, 5, C.ink, 15);
  A.blueDot = circleSprite(64, C.blue, 16);
  A.w1 = wordScrap('لا', FONT.lalezar(330), { bg: C.red, color: C.cream, seed: 21, px: 70, py: 30 });
  A.w2 = wordScrap('توجد', FONT.rakkas(200), { bg: '#F6F0E2', color: C.ink, seed: 22, torn: [1, 0, 1, 1] });
  A.w3 = wordScrap('أي', FONT.jomhuria(360), { bg: C.blue, color: C.yellow, seed: 23, px: 70, py: 16, torn: [0, 1, 1, 0] });
  A.w4 = wordScrap('قواعد', FONT.ruqaa(190), { bg: C.yellow, color: C.ink, seed: 24, py: 30 });
  A.tape1 = tapeSprite(230, 66, 3); A.tape2 = tapeSprite(210, 62, 4); A.tape3 = tapeSprite(250, 70, 5); A.tape4 = tapeSprite(190, 58, 6);
  A.stamp = stampSprite(150, '#C72E1E', 9);
  A.stampCream = stampSprite(140, '#FFF3DC', 19);

  // scene 2
  A.sciA = scissorHalf(); A.sciB = A.sciA;
  A.cutWord = cutWord('قُص', FONT.lalezar(640), C.yellow, { margin: 18, marginColor: '#FBF6E6', seed: 31 });
  A.cutLabel = wordScrap('CUT', FONT.type(78), { bg: '#FBF8EE', color: C.ink, seed: 32, torn: [0, 1, 0, 1], px: 40, py: 22 });
  A.triYellow = triSprite(150, 130, C.yellow, 33); A.triCream = triSprite(110, 150, C.cream, 34); A.circleRed = circleSprite(46, C.red, 35);

  // scene 3
  A.newsPage = scrap(1230, 2090, '#EFE8D6', { seed: 41, rough: 12, inside: (x, w, h) => newsLayout(x, w, h, 41, { masthead: 'صحيفة بلا قواعد', mastSize: 120, dateline: 'السبت ٢٦ سبتمبر ٢٠٢٦  ·  العدد الأول  ·  ١٥ ثانية فقط', cols: 3, margin: 110 }) });
  A.sun = halftoneDisc(200, C.yellow, C.orange, { seed: 42, cell: 18 });
  A.triBlack = triSprite(270, 240, C.ink, 43);
  A.starPink = starSprite(84, 36, 5, C.pink, 44);
  A.paste = wordScrap('الصق', FONT.kufi(230), { bg: C.pink, color: C.ink, seed: 45 });
  A.pasteLabel = wordScrap('PASTE', FONT.type(70), { bg: '#FBF8EE', color: C.ink, seed: 46, torn: [0, 1, 0, 1], px: 36, py: 20 });
  A.moon = halftoneDisc(118, '#F3EBD6', C.navy, { seed: 47, cell: 12, hl: [0.3, -0.35] });
  A.polaroid = polaroidSprite();

  // scene 4
  A.notebook = notebookSprite(860, 1240);
  A.breakWord = cutWord('اكسر', FONT.cairo(250), C.red, { margin: 16, marginColor: '#FFF8EC', seed: 51 });

  // scene 5
  A.sunSm = halftoneDisc(110, C.orange, C.red, { seed: 52, cell: 14 });
  A.triBlue = triSprite(200, 180, C.blue, 53);
  A.circlePink = circleSprite(76, C.pink, 54);
  A.checker = checkerSprite(170, 55);
  A.eye = eyeSprite();
  A.squiggle = squiggleSprite(C.red, 56);
  A.squiggleInk = squiggleSprite(C.ink, 57);
  A.tapeSm = tapeSprite(170, 54, 58);
  A.mixLabel = wordScrap('MIX', FONT.anton(92), { bg: C.ink, color: C.yellow, seed: 59, torn: [0, 0, 0, 0], cj: 3, px: 26, py: 18 });
  A.starCream = starSprite(70, 30, 5, C.cream, 60);

  // scene 6
  A.q1 = wordScrap('القاعدة', FONT.kufi(170), { bg: C.ink, color: C.cream, seed: 61 });
  A.q2 = wordScrap('الوحيدة', FONT.lalezar(190), { bg: C.red, color: C.cream, seed: 62, torn: [1, 1, 1, 0] });
  A.qmark = cutWord('؟', FONT.lalezar(520), C.blue, { margin: 18, marginColor: '#FBF8EE', seed: 63 });
  A.rule1 = wordScrap('RULE #1', FONT.type(58), { bg: '#FBF8EE', color: C.ink, seed: 64, torn: [0, 1, 0, 1], px: 32, py: 20 });

  // scene 7
  A.start = cutWord('ابدأ', FONT.lalezar(560), C.cream, { hard: 20, hardColor: C.ink, seed: 71 });
  A.dot = circleSprite(36, C.ink, 72);
  A.startStrip = wordScrap('THE ONLY RULE: START', FONT.type(50), { bg: '#FBF8EE', color: C.ink, seed: 73, torn: [0, 1, 0, 1], px: 34, py: 22 });
  A.mCut = wordScrap('قُص', FONT.lalezar(120), { bg: C.blue, color: C.yellow, seed: 74, px: 40, py: 16 });
  A.mPaste = wordScrap('الصق', FONT.kufi(96), { bg: C.pink, color: C.ink, seed: 75, px: 36, py: 20 });
  A.mBreak = wordScrap('اكسر', FONT.cairo(88), { bg: '#FBF8EE', color: C.red, seed: 76, px: 36, py: 18 });
  A.mMix = wordScrap('اخلط', FONT.jomhuria(150), { bg: C.yellow, color: C.ink, seed: 77, px: 40, py: 6 });
}

// =================== SCENES ===================
// 1 — «لا توجد أي قواعد»  (0.0 – 3.0)
const S1W = [
  { k: 'w1', t: 0.0, x: 560, y: 590, r: -6 },
  { k: 'w2', t: 0.5, x: 470, y: 875, r: 3.5 },
  { k: 'w3', t: 1.0, x: 690, y: 1120, r: -4 },
  { k: 'w4', t: 1.5, x: 505, y: 1395, r: 4 },
];
function scene1(t) {
  bg(A.kraft);
  putB(1, t, A.graph, 190, 250, { r: -9 });
  putB(2, t, A.pinkDots, 930, 320, { comp: 'multiply', shadow: 0 });
  putB(3, t, A.news1, 240, 1700, { r: 7 });
  putB(4, t, A.starBlack, 120, 1130, { r: 12 });
  putB(5, t, A.blueDot, 975, 1400);
  S1W.forEach((w, i) => {
    const sl = slam(t, w.t); if (!sl) return;
    putB(10 + i, t, A[w.k], w.x, w.y, { r: w.r + (1 - sl.e) * (i % 2 ? 12 : -12), s: sl.s, lift: sl.lift });
  });
  const w1 = S1W[0], w4 = S1W[3];
  const [tx, ty] = corner(w1.x, w1.y, A.w1.w, A.w1.h, w1.r, -1, -1, 18);
  tapeIn(15, t, 2.0, A.tape1, tx, ty, -38);
  const [tx2, ty2] = corner(S1W[2].x, S1W[2].y, A.w3.w, A.w3.h, S1W[2].r, 1, 1, 14);
  tapeIn(16, t, 2.0, A.tape4, tx2, ty2, -30);
  if (t >= 2.0) markerLoop(w4.x, w4.y + 4, A.w4.w / 2 + 50, A.w4.h / 2 + 44, 4, E.out2(prog(t, 2.0, 2.42)), 77, C.red, 13);
  stampIn(t, 2.5, A.stamp, 860, 1660, -16);
}

// 2 — «قُص»  (3.0 – 5.0)
const CUT = { A: [1180, 700], B: [-120, 1200] };
const lineY = x => CUT.A[1] + ((x - CUT.A[0]) * (CUT.B[1] - CUT.A[1])) / (CUT.B[0] - CUT.A[0]);
const CUT_ANG = Math.atan2(CUT.B[1] - CUT.A[1], CUT.B[0] - CUT.A[0]) / D2R;
let SNAP, HT, HB;
function ensureSnap() {
  if (SNAP) return;
  SNAP = mk(W, H); const sx = SNAP.getContext('2d');
  withCtx(sx, () => { const z = 1.03; g.setTransform(z, 0, 0, z, (W / 2) * (1 - z), (H / 2) * (1 - z)); scene1(2.999); g.setTransform(1, 0, 0, 1, 0, 0); });
  const half = top => { const c = mk(W, H), x = c.getContext('2d'); x.beginPath();
    if (top) { x.moveTo(-10, -10); x.lineTo(W + 10, -10); x.lineTo(W + 10, lineY(W + 10)); x.lineTo(-10, lineY(-10)); }
    else { x.moveTo(-10, lineY(-10)); x.lineTo(W + 10, lineY(W + 10)); x.lineTo(W + 10, H + 10); x.lineTo(-10, H + 10); }
    x.closePath(); x.clip(); x.drawImage(SNAP, 0, 0); return c; };
  HT = half(true); HB = half(false);
}
function scene2(t) {
  ensureSnap();
  const tq = st(t);
  bg(A.blueBG);
  const reveal = prog(t, 4.0, 4.6);
  putB(20, t, A.triYellow, 180, 520, { r: -14 });
  putB(21, t, A.triCream, 900, 1560, { r: 18 });
  putB(22, t, A.circleRed, 880, 560);
  putB(23, t, A.cutWord, 540, 1000, { r: -5, s: lerp(1.14, 1, E.out3(reveal)), lift: 1.5 });
  if (t >= 4.5) { const s = lerp(1.3, 1, E.out3(prog(t, 4.5, 4.58))); putB(24, t, A.cutLabel, 560, 1370, { r: 3, s }); }
  if (t < 4.0) {
    g.drawImage(SNAP, 0, 0);
    const xs = lerp(1260, -470, prog(tq, 3.25, 4.08));
    // dashed coupon line (drawn right→left), then the cut slit behind the scissors
    const dp = E.out2(prog(t, 3.0, 3.25));
    g.save(); g.setLineDash([30, 20]); g.lineWidth = 6; g.strokeStyle = C.ink; g.globalAlpha = 0.9;
    const x0 = Math.min(CUT.A[0], xs); g.beginPath(); g.moveTo(x0, lineY(x0)); const xe = lerp(CUT.A[0], CUT.B[0], dp); g.lineTo(xe, lineY(xe)); g.stroke(); g.restore();
    if (t >= 3.25) {
      g.save(); g.lineWidth = 4; g.strokeStyle = 'rgba(15,10,5,.85)'; g.beginPath(); g.moveTo(W + 20, lineY(W + 20)); g.lineTo(xs, lineY(xs)); g.stroke(); g.restore();
      scissorsDraw(xs, lineY(xs), CUT_ANG - 180, 26 * Math.abs(Math.sin(6 * Math.PI * (tq - 3.25))));
    }
  } else {
    const sep = E.io3(prog(tq, 4.0, 4.55)), mx = 540, my = lineY(540);
    [[HT, -70, -1350, -10], [HB, 90, 1350, 8]].forEach(([img, dx, dy, dr]) => {
      g.save(); g.translate(mx + dx * sep, my + dy * sep); g.rotate(dr * D2R * sep); g.translate(-mx, -my);
      g.shadowColor = 'rgba(8,10,40,.5)'; g.shadowBlur = 30; g.shadowOffsetX = 8; g.shadowOffsetY = 16;
      g.drawImage(img, 0, 0); g.restore();
    });
  }
  // newspaper page slapped over at the end (lands on beat 5.0)
  if (t >= 4.8333) { const p = E.out3(prog(t, 4.8333, 5.0)); put(A.newsPage, 540 + (1 - p) * 140, 960 + (1 - p) * 1950, { r: (1 - p) * 9, lift: 1.6 }); }
}

// 3 — «الصق»  (5.0 – 7.0)
function scene3(t) {
  bg(A.kraft);
  put(A.newsPage, 540, 960, { shadow: 0 });
  enter(30, t, 6.0, A.sun, [1500, 320], [820, 450], 50, -8);
  enter(31, t, 6.0, A.triBlack, [-320, 1750], [215, 1500], -70, 12);
  enter(32, t, 6.0, A.starPink, [560, -300], [175, 610], 120, 14);
  const sl = slam(t, 5.0);
  const WX = 540, WY = 930, WR = -3;
  putB(33, t, A.paste, WX, WY, { r: WR + (1 - sl.e) * 10, s: sl.s, lift: sl.lift });
  let [tx, ty] = corner(WX, WY, A.paste.w, A.paste.h, WR, 1, -1, 22); tapeIn(34, t, 5.5, A.tape2, tx, ty, 38);
  [tx, ty] = corner(WX, WY, A.paste.w, A.paste.h, WR, -1, 1, 22); tapeIn(35, t, 5.75, A.tape3, tx, ty, 32);
  if (t >= 6.25) { const s = lerp(1.3, 1, E.out3(prog(t, 6.25, 6.33))); putB(36, t, A.pasteLabel, 400, 1170, { r: 2.5, s }); }
  if (t >= 6.5) {
    const s = lerp(1.35, 1, E.out3(prog(t, 6.5, 6.6)));
    putB(37, t, A.polaroid, 770, 1460, { r: 7, s, lift: 1 + (s - 1) * 3 });
    tapeIn(38, t, 6.58, A.tape1, 740, 1225, -6);
  }
}

// 4 — «اكسر»  (7.0 – 9.0)
const NB = { x: 540, y: 960, r: -3 }, BW = { x: 520, y: 1010, r: -9 };
let SHEETFULL, CRACKS, SHARDS, IMPACT;
function ensureShards() {
  if (SHARDS) return;
  SHEETFULL = mk(W, H);
  withCtx(SHEETFULL.getContext('2d'), () => { put(A.notebook, NB.x, NB.y, { r: NB.r, shadow: 0 }); put(A.breakWord, BW.x, BW.y, { r: BW.r, lift: 0.7 }); });
  const P = (IMPACT = [BW.x + 10, BW.y - 10]), r = R(404), N = 9;
  const angs = [...Array(N)].map((_, i) => (i / N) * Math.PI * 2 + (r() - 0.5) * 0.45).sort((a, b) => a - b);
  const rays = angs.map(ang => { const pts = [P]; let rad = 0, ring = -1; while (rad < 2700) { rad += 55 + r() * 95; const a = ang + (r() - 0.5) * 0.2; pts.push([P[0] + Math.cos(a) * rad, P[1] + Math.sin(a) * rad]); if (ring < 0 && rad > 210 + r() * 140) ring = pts.length - 1; } return { pts, ring }; });
  CRACKS = mk(W, H); { const x = CRACKS.getContext('2d'); x.lineJoin = 'round';
    const strokeAll = (w, col, off) => { x.lineWidth = w; x.strokeStyle = col; rays.forEach(ry => { x.beginPath(); ry.pts.forEach(([a, b], i) => (i ? x.lineTo(a + off, b + off) : x.moveTo(a + off, b + off))); x.stroke(); });
      rays.forEach((ry, i) => { const nx = rays[(i + 1) % N]; x.beginPath(); x.moveTo(ry.pts[ry.ring][0] + off, ry.pts[ry.ring][1] + off); x.lineTo(nx.pts[nx.ring][0] + off, nx.pts[nx.ring][1] + off); x.stroke(); }); };
    strokeAll(2, 'rgba(255,255,255,.9)', 2); strokeAll(4.5, C.ink, 0);
    x.globalCompositeOperation = 'destination-in'; x.drawImage(SHEETFULL, 0, 0); }
  SHARDS = [];
  rays.forEach((ra, i) => {
    const rb = rays[(i + 1) % N];
    const inner = [...ra.pts.slice(0, ra.ring + 1), ...rb.pts.slice(1, rb.ring + 1).reverse()];
    const outer = [...ra.pts.slice(ra.ring), ...rb.pts.slice(rb.ring).reverse()];
    [inner, outer].forEach(pts => {
      const xs = pts.map(p => clamp(p[0], 0, W)), ys = pts.map(p => clamp(p[1], 0, H));
      const bx = Math.floor(Math.min(...xs)), by = Math.floor(Math.min(...ys)), bw = Math.ceil(Math.max(...xs)) - bx, bh = Math.ceil(Math.max(...ys)) - by;
      if (bw < 4 || bh < 4) return;
      const c = mk(bw, bh), x = c.getContext('2d'); x.translate(-bx, -by); poly(x, pts); x.clip(); x.drawImage(SHEETFULL, 0, 0); x.drawImage(CRACKS, 0, 0);
      const cx = bx + bw / 2, cy = by + bh / 2, d = Math.hypot(cx - P[0], cy - P[1]) || 1;
      SHARDS.push({ c, bx, by, cx, cy, dx: (cx - P[0]) / d, dy: (cy - P[1]) / d, k: r(), inner: pts === inner });
    });
  });
}
function scene4(t) {
  bg(A.blackBG); ensureShards();
  const tq = st(t);
  if (t < 7.5) {
    put(A.notebook, NB.x, NB.y, { r: NB.r, lift: 0.6 });
    const sl = slam(t, 7.0, 0.125, 2.1);
    put(A.breakWord, BW.x, BW.y, { r: BW.r - (1 - sl.e) * 14, s: sl.s, lift: sl.lift });
  } else if (t < 8.0) {
    g.drawImage(SHEETFULL, 0, 0);
    const rad = 1500 * E.out2(prog(t, 7.5, 7.625));
    g.save(); g.beginPath(); g.arc(IMPACT[0], IMPACT[1], rad, 0, 7); g.clip(); g.drawImage(CRACKS, 0, 0); g.restore();
    if (t < 7.59) { // impact flash
      g.save(); g.translate(IMPACT[0], IMPACT[1]); g.fillStyle = '#FFF8E6'; g.beginPath();
      for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2, rr = i % 2 ? 40 : 150; i ? g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : g.moveTo(Math.cos(a) * rr, Math.sin(a) * rr); }
      g.closePath(); g.fill(); g.restore();
    }
  } else {
    const k1 = E.out3(prog(tq, 8.0, 8.09)), f = E.in2(prog(tq, 8.5, 8.96));
    SHARDS.forEach(s => {
      const d = k1 * (14 + s.k * 26) + f * (1300 + s.k * 900) * (s.inner ? 0.8 : 1);
      const rr = (k1 * (s.k - 0.5) * 7 + f * (s.k - 0.5) * 150) * D2R, sc = 1 + f * 0.3 * s.k;
      g.save(); g.translate(s.cx + s.dx * d, s.cy + s.dy * d); g.rotate(rr); g.scale(sc, sc); g.drawImage(s.c, s.bx - s.cx, s.by - s.cy); g.restore();
    });
    if (tq >= 8.5) { // paper dust
      const r = R(808), pf = prog(tq, 8.5, 9.0);
      for (let i = 0; i < 46; i++) { const a = r() * Math.PI * 2, sp = 300 + r() * 1300, sz = 4 + r() * 12;
        g.save(); g.translate(IMPACT[0] + Math.cos(a) * sp * E.out2(pf), IMPACT[1] + Math.sin(a) * sp * E.out2(pf)); g.rotate(r() * 6 + pf * 8); g.fillStyle = r() < 0.7 ? '#F6F0E2' : C.red; g.globalAlpha = 1 - pf * 0.6; g.fillRect(-sz / 2, -sz / 2, sz, sz * 0.7); g.restore(); }
    }
  }
}

// 5 — «اخلط»  (9.0 – 11.0)
const MIX_FONTS = [
  [FONT.lalezar, 1], [FONT.rakkas, 1], [FONT.jomhuria, 1.15], [FONT.kufi, 1], [FONT.amiriB, 1], [FONT.blaka, 1], [FONT.marhey, 1], [FONT.cairo, 1],
];
const MIX_PAL = [[C.ink, C.cream], [C.cream, C.ink], [C.blue, C.yellow], [C.red, C.cream], [C.yellow, C.ink], [C.pink, C.ink], [C.green, C.cream]];
const MIX_BG = [C.yellow, C.blue, C.red, C.pink], MIX_BAND = [C.blue, C.yellow, C.cream, C.ink];
const mixCache = {};
function mixSprite(f, k) {
  const fi = f % MIX_FONTS.length; let pi = (f * 3) % MIX_PAL.length;
  while (MIX_PAL[pi][0] === MIX_BG[k] || MIX_PAL[pi][0] === MIX_BAND[k]) pi = (pi + 1) % MIX_PAL.length;
  const key = fi + '_' + pi; if (mixCache[key]) return mixCache[key];
  const [fn, boost] = MIX_FONTS[fi], m = measure('اخلط', fn(100));
  const size = Math.round(Math.min((100 * 560) / m.w, (100 * 300) / m.h) * boost);
  return (mixCache[key] = wordScrap('اخلط', fn(size), { bg: MIX_PAL[pi][0], color: MIX_PAL[pi][1], seed: 90 + f, px: 50, py: 30 }));
}
let ORBIT;
function scene5(t) {
  if (!ORBIT) ORBIT = [
    [A.sunSm, 0.0, 470, 1, 0.7], [A.starBlack, 0.63, 360, 1.1, -0.9], [A.triBlue, 1.26, 470, 1, 0.5], [A.circlePink, 1.88, 380, 1, 0],
    [A.checker, 2.51, 470, 0.85, 0.6], [A.eye, 3.14, 380, 0.7, -0.3], [A.squiggleInk, 3.77, 470, 0.9, 0.8], [A.tapeSm, 4.4, 380, 1, 1.2],
    [A.mixLabel, 5.03, 470, 1, -0.4], [A.starCream, 5.65, 380, 1, 1],
  ];
  const tq = st(t), T = tq - 9, k = clamp(Math.floor((t - 9) / 0.5), 0, 3);
  bg(A.mixBG[k]);
  put(A.bands[k], 540, 960 + (k % 2 ? -150 : 170), { r: k % 2 ? 17 : -15, lift: 0.8 });
  const spin = T * 1.3 + T * T * 1.1, suck = E.in3(prog(tq, 10.42, 10.96));
  const bt = (t - 9) % 0.5, pulse = 1 + 0.08 * Math.exp(-bt / 0.09);
  ORBIT.forEach(([sp, a0, rad, s, rs], i) => {
    const a = a0 + spin * (i % 2 ? 0.85 : 1), rr = rad * pulse * (1 - suck);
    putB(50 + i, t, sp, 540 + Math.cos(a) * rr, 960 + Math.sin(a) * rr * 1.28, { r: (a0 * 57 + spin * rs * 60) % 360, s: s * (1 - suck * 0.85) });
  });
  const f = Math.floor((t - 9) * 8);
  putB(80, t, mixSprite(f, k), 540, 960, { r: f % 2 ? -4 : 3, s: pulse * (1 - suck * 0.97), lift: 1.4 });
}

// 6 — «القاعدة الوحيدة؟»  (11.0 – 13.0)
function pop(id, t, t0, sp, x, y, r, from = 1.14) {
  if (t < t0) return; const s = lerp(from, 1, E.out3(prog(t, t0, t0 + 0.084)));
  putB(id, t, sp, x, y, { r, s, lift: 1 + (s - 1) * 3, amp: 1.6 + 5 * prog(t, 12, 13) });
}
function scene6(t) {
  bg(A.creamBG);
  pop(60, t, 11.25, A.rule1, 540, 450, -2);
  pop(61, t, 11.0, A.q1, 540, 700, -3);
  pop(62, t, 11.5, A.q2, 545, 960, 2.5);
  const sl = slam(t, 12.0, 0.125, 1.9);
  if (sl) putB(63, t, A.qmark, 560, 1335, { r: 8 * Math.sin(2 * Math.PI * 1.5 * (st(t) - 12)) + (1 - sl.e) * 20, s: sl.s, lift: sl.lift, amp: 1.6 + 5 * prog(t, 12, 13) });
}

// 7 — «ابدأ.»  (13.0 – 15.0)
const BURST = [
  ['mCut', 240, 300, -10, 1], ['eye', 560, 250, 4, 0.72], ['mPaste', 850, 370, 8, 1],
  ['starBlack', 115, 690, 15, 0.8], ['sunSm', 1000, 640, 0, 0.85], ['circlePink', 110, 1230, 0, 0.9], ['triBlue', 960, 1250, -12, 0.9],
  ['mBreak', 250, 1535, 6, 1], ['mMix', 815, 1545, -6, 1], ['checker', 105, 1790, 10, 0.8], ['squiggleInk', 480, 1770, -8, 0.8], ['starCream', 990, 1010, 20, 0.7],
];
function scene7(t) {
  if (FRAME === 312) { g.fillStyle = '#FFF4DA'; g.fillRect(-M, -M, W + 2 * M, H + 2 * M); return; }
  bg(A.redBG);
  const tq = st(t);
  BURST.forEach(([k, x, y, r, s], j) => {
    const r0 = R(700 + j), d = 13.0 + j * 0.02, p = E.out3(prog(tq, d, d + 0.38));
    if (p <= 0) return;
    putB(90 + j, t, A[k], lerp(540, x, p), lerp(930, y, p), { r: lerp(r + (r0() - 0.5) * 300, r, p), s: lerp(0.25, 1, p) * s, lift: 1 + (1 - p) * 2 });
  });
  const sl = slam(t, 13.0, 0.125, 2.6), WX = 548, WY = 930;
  putB(100, t, A.start, WX, WY, { r: -3 + (1 - sl.e) * -16, s: sl.s, lift: sl.lift * 1.4 });
  if (t >= 13.25) {
    const p = prog(t, 13.25, 13.46), dx = WX - A.start.w / 2 - 58, dy = WY + A.start.h / 2 - 78;
    const y = p < 1 ? lerp(dy - 520, dy, E.in2(p)) : dy - 26 * Math.abs(Math.sin(prog(t, 13.46, 13.7) * Math.PI)) * (1 - prog(t, 13.46, 13.7));
    putB(101, t, A.dot, dx, y, { lift: 1 });
  }
  if (t >= 13.5) { const s = lerp(1.3, 1, E.out3(prog(t, 13.5, 13.58))); putB(102, t, A.startStrip, 540, 1305, { r: -2, s }); tapeIn(103, t, 13.58, A.tape4, 540 + 345, 1280, 62); }
  if (t >= 14.0) { const p = prog(t, 14.0, 14.084); put(A.stampCream, 875, 1785, { r: 12, s: lerp(1.35, 1, p), a: p < 1 ? 0.6 : 0.92, shadow: 0 }); }
}

// =================== CAMERA + POST ===================
const IMPACTS = [[0.125, 14], [0.625, 12], [1.125, 12], [1.625, 14], [2.5, 7], [5.0, 12], [7.125, 18], [7.5, 12], [8.0, 16], [8.5, 10], [9.0, 8], [9.5, 8], [10.0, 8], [10.5, 8], [12.125, 9], [13.125, 28], [14.0, 7]];
function camera(t, i) {
  let dx = 0, dy = 0;
  for (const [ti, a] of IMPACTS) if (t >= ti && t < ti + 0.3) { const d = a * Math.exp(-(t - ti) / 0.07), r = R(i * 31 + ((ti * 1000) | 0)); dx += (r() - 0.5) * 2 * d; dy += (r() - 0.5) * 2 * d; }
  let z = 1;
  if (t < 3) z = 1 + 0.03 * (t / 3);
  else if (t < 4) z = 1;
  else if (t < 5) z = 1 + 0.02 * prog(t, 4, 5);
  else if (t < 7) z = 1 + 0.03 * prog(t, 5, 7);
  else if (t < 9) z = 1.02 + 0.02 * prog(t, 7, 9);
  else if (t < 11) z = 1.02;
  else if (t < 13) { z = 1 + 0.015 * (t - 11) + 0.07 * E.in2(prog(t, 12, 12.92)); const r = R(i * 13 + 5), j = 7 * prog(t, 12, 13); dx += (r() - 0.5) * 2 * j; dy += (r() - 0.5) * 2 * j; }
  else z = 1 + 0.04 * E.io3(prog(t, 13.2, 15));
  if (!(t >= 3 && t < 4)) { dx += Math.sin(t * 2.1) * 1.3; dy += Math.cos(t * 1.7) * 1.3; }
  return { dx, dy, z };
}
function post(i) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.13; g.imageSmoothingEnabled = true; g.drawImage(GRAIN[i % 6], 0, 0, W, H);
  g.globalCompositeOperation = 'multiply'; g.globalAlpha = 1; g.drawImage(VIG, 0, 0);
  g.globalCompositeOperation = 'source-over';
  const r = R(9000 + i), f = (r() - 0.5) * 0.035; g.fillStyle = f > 0 ? `rgba(255,248,230,${f})` : `rgba(0,0,0,${-f})`; g.fillRect(0, 0, W, H);
  for (let k = 0; k < 4; k++) { if (r() < 0.5) continue; g.fillStyle = r() < 0.5 ? 'rgba(255,255,255,.35)' : 'rgba(0,0,0,.35)'; g.beginPath(); g.arc(r() * W, r() * H, 0.8 + r() * 2.2, 0, 7); g.fill(); }
  g.restore();
}
window.renderFrame = function (i) {
  FRAME = i; const t = i / FPS;
  g = MAIN; g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  const cam = camera(t, i);
  g.setTransform(cam.z, 0, 0, cam.z, (W / 2) * (1 - cam.z) + cam.dx, (H / 2) * (1 - cam.z) + cam.dy);
  if (t < 3) scene1(t); else if (t < 5) scene2(t); else if (t < 7) scene3(t); else if (t < 9) scene4(t); else if (t < 11) scene5(t); else if (t < 13) scene6(t); else scene7(t);
  post(i);
};

(async function boot() {
  const loads = [
    ['100px "Lalezar"', 'ابدأ'], ['100px "Rakkas"', 'توجد'], ['100px "Jomhuria"', 'أي'], ['100px "Blaka"', 'اخلط'],
    ['700 100px "Reem Kufi"', 'القاعدة'], ['700 100px "Aref Ruqaa"', 'قواعد'], ['400 100px "Aref Ruqaa"', 'بلا'], ['400 100px "Amiri"', 'الفن ٢٠٢٦'], ['700 100px "Amiri"', 'صحيفة'],
    ['900 100px "Cairo"', 'اخلط'], ['700 100px "Marhey"', 'اخلط'], ['100px "Lalezar"', 'NO.'], ['100px "Anton"', 'MIX'], ['100px "Special Elite"', 'CUT'], ['100px "Permanent Marker"', 'A'],
  ];
  await Promise.all(loads.map(([f, s]) => document.fonts.load(f, s)));
  await document.fonts.ready;
  const t0 = performance.now(); build();
  console.log('assets built in', Math.round(performance.now() - t0), 'ms; fonts ok:', loads.map(([f, s]) => document.fonts.check(f, s)).every(Boolean));
  window.NF = NF; window.READY = true;
})();
