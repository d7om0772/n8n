// KLOVA — scrapbook collage motion piece. Deterministic: render(t) draws frame at time t.
const FPS = 30, DUR = 21.5, SW = 1080, SH = 1920;
const WORLD = { w: 2700, h: 4800 };
const PAL = window.PAL;
const A = '../assets/';

// ---------------- utilities ----------------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const easeInOut = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const easeOut = t => 1 - Math.pow(1 - t, 3);
const easeIn = t => t * t;
function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function hash(n) { const r = rng(n * 7919 + 13); r(); return r(); }
const EVENTS = []; // sound cues, exported for the audio mixer
const cue = (t, type, extra = {}) => EVENTS.push({ t: +t.toFixed(3), type, ...extra });
const IMPACTS = []; // camera micro shakes
const impact = (t, s) => IMPACTS.push({ t, s });

// torn / irregular rectangle outline
function tornPoly(w, h, seed, amp = 3, step = 22, inset = 0) {
  const r = rng(seed), pts = [];
  const edge = (x0, y0, x1, y1, nx, ny) => {
    const len = Math.hypot(x1 - x0, y1 - y0), n = Math.max(2, Math.round(len / step));
    for (let i = 0; i < n; i++) {
      const u = i / n, j = (r() - 0.5) * 2 * amp + (r() < 0.08 ? -amp * 1.6 : 0);
      pts.push([x0 + (x1 - x0) * u + nx * j, y0 + (y1 - y0) * u + ny * j]);
    }
  };
  const a = inset;
  edge(a, a, w - a, a, 0, -1); edge(w - a, a, w - a, h - a, 1, 0);
  edge(w - a, h - a, a, h - a, 0, 1); edge(a, h - a, a, a, -1, 0);
  return pts;
}
const polyPath = pts => 'M' + pts.map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' L') + ' Z';
function pctPoly(seed, amp = 2.2, n = 5, side = 1.2) { // CSS polygon in % for word pieces
  const r = rng(seed), pts = [];
  for (let i = 0; i <= n; i++) pts.push([i / n * 100, (r() - 0.5) * side * 2 + side]);
  for (let i = 1; i <= 3; i++) pts.push([100 - (r() * amp), i / 4 * 100]);
  for (let i = n; i >= 0; i--) pts.push([i / n * 100, 100 - side - (r() - 0.5) * side * 2]);
  for (let i = 3; i >= 1; i--) pts.push([r() * amp, i / 4 * 100]);
  return 'polygon(' + pts.map(p => p[0].toFixed(1) + '% ' + p[1].toFixed(1) + '%').join(',') + ')';
}
function el(tag, cls, parent, style = {}) {
  const e = document.createElement(tag); if (cls) e.className = cls; Object.assign(e.style, style); if (parent) parent.appendChild(e); return e;
}
const svgNS = 'http://www.w3.org/2000/svg';

// ---------------- DOM roots ----------------
const stage = document.getElementById('stage');
const world = el('div', 'world', stage, { width: WORLD.w + 'px', height: WORLD.h + 'px' });
const bg = el('div', 'bg', world, { left: '-2400px', top: '-2400px', width: (WORLD.w + 4800) + 'px', height: (WORLD.h + 4800) + 'px' });
const screenLayer = el('div', 'screen', stage);
const vign = el('img', 'overlay', stage); vign.src = A + 'vignette.png';
const grain = el('img', 'overlay grain', stage);

// coffee ring stains baked into the page (subtle)
function ring(x, y, r, rot) {
  const s = el('div', 'stain', world, { left: (x - r) + 'px', top: (y - r) + 'px', width: 2 * r + 'px', height: 2 * r + 'px', transform: `rotate(${rot}deg)` });
  s.innerHTML = `<svg width="${2 * r}" height="${2 * r}" viewBox="0 0 ${2 * r} ${2 * r}"><circle cx="${r}" cy="${r}" r="${r - 14}" fill="none" stroke="#6B3F24" stroke-width="9" opacity="0.10"/><circle cx="${r}" cy="${r}" r="${r - 22}" fill="none" stroke="#6B3F24" stroke-width="3" opacity="0.07" stroke-dasharray="120 30 60 20"/></svg>`;
}
ring(2380, 1250, 170, 20); ring(330, 3050, 150, -40); ring(2330, 4620, 160, 60);

// ---------------- element registry ----------------
const ITEMS = [];

// generic drop animation state: returns {vis, dx, dy, rot, s, h}
function dropState(t, t0, dur = 0.34, from = { dx: 0, dy: -900, rot: 14, s: 1.22 }) {
  if (t < t0) return { vis: false };
  const u = (t - t0) / dur;
  if (u < 1) {
    const e = easeIn(u);
    return { vis: true, dx: from.dx * (1 - e), dy: from.dy * (1 - e), rot: from.rot * (1 - e), s: lerp(from.s, 1, e), h: 1 - e };
  }
  const k = t - t0 - dur; // settle: damped wobble + squash
  const damp = Math.exp(-k * 9);
  return { vis: true, dx: 0, dy: -10 * damp * Math.sin(k * 26), rot: -from.rot * 0.12 * damp * Math.cos(k * 20), s: 1 - 0.018 * damp * Math.cos(k * 30), h: 0 };
}
function shadowCSS(h, base = 1) {
  const dx = 5 + 26 * h, dy = 9 + 46 * h, blur = 7 + 34 * h, a = (0.36 - 0.14 * h) * base;
  return `drop-shadow(${dx.toFixed(1)}px ${dy.toFixed(1)}px ${blur.toFixed(1)}px rgba(46,27,18,${a.toFixed(3)}))`;
}

// ---------------- cards (printed clippings) ----------------
let uid = 0;
function card({ layer = world, img, iw, ih, x, y, rot, t0, border = 24, from, tapes = [], anim = null, kb = { z0: 1.0, z1: 1.07, px: -10, py: 8 }, z = 10, seed, decor = null, big = false }) {
  const id = ++uid; seed = seed || id * 101;
  const w = iw + border * 2, h = ih + border * 2;
  const root = el('div', 'item', layer, { left: (x - w / 2) + 'px', top: (y - h / 2) + 'px', width: w + 'px', height: h + 'px', zIndex: z });
  let decorEl = null;
  if (decor) {
    decorEl = el('div', 'decor', root, { left: decor.dx + 'px', top: decor.dy + 'px', width: decor.w + 'px', height: decor.h + 'px', background: decor.col, clipPath: `path('${polyPath(tornPoly(decor.w, decor.h, seed + 7, 7, 26))}')`, transform: `rotate(${decor.rot}deg)` });
  }
  const outer = polyPath(tornPoly(w, h, seed, 3.2, 20));
  const inner = polyPath(tornPoly(iw, ih, seed + 3, 1.1, 30).map(p => [p[0] + border, p[1] + border]));
  const holder = el('div', 'cardbody', root, { width: w + 'px', height: h + 'px' });
  holder.innerHTML = `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="${svgNS}">
    <defs><pattern id="pw${id}" patternUnits="userSpaceOnUse" width="768" height="768"><image href="${A}paper_white.jpg" width="768" height="768"/></pattern>
    <clipPath id="ci${id}"><path d="${inner}"/></clipPath>
    <linearGradient id="gl${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.10"/><stop offset="0.45" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.06"/></linearGradient></defs>
    <path d="${outer}" fill="url(#pw${id})"/>
    <g clip-path="url(#ci${id})"><image class="kb" href="${A}${img}" x="${border}" y="${border}" width="${iw}" height="${ih}" preserveAspectRatio="xMidYMid slice"/>
    <g class="anim" transform="translate(${border} ${border})"></g>
    <rect x="${border}" y="${border}" width="${iw}" height="${ih}" fill="url(#gl${id})"/></g>
    <path d="${inner}" fill="none" stroke="rgba(0,0,0,0.10)" stroke-width="2"/>
  </svg>`;
  const kbImg = holder.querySelector('.kb');
  const animG = holder.querySelector('.anim');
  const tapeEls = tapes.map((tp, i) => {
    const tw = tp.w || 170, th = 52;
    const te = el('div', 'tape', root, { left: (tp.x - tw / 2) + 'px', top: (tp.y - th / 2) + 'px', width: tw + 'px', height: th + 'px', clipPath: `path('${polyPath(tapeShape(tw, th, seed + 50 + i))}')` });
    return { el: te, rot: tp.rot, t: t0 + (tp.dt ?? (0.42 + i * 0.1)) };
  });
  tapeEls.forEach(te => cue(te.t - 0.06, 'tape'));
  cue(t0, big ? 'dropBig' : 'drop'); cue(t0 + 0.34, big ? 'landBig' : 'land'); impact(t0 + 0.34, big ? 7 : 4);
  const it = {
    t0, update(t) {
      const st = dropState(t, t0, 0.34, from || { dx: 60, dy: -950, rot: rot > 0 ? 16 : -16, s: 1.22 });
      if (!st.vis) { root.style.display = 'none'; return; }
      root.style.display = 'block';
      root.style.transform = `translate(${st.dx}px, ${st.dy}px) rotate(${rot + st.rot}deg) scale(${st.s})`;
      root.style.filter = shadowCSS(st.h);
      const k = clamp((t - t0) / 7);
      const zz = lerp(kb.z0, kb.z1, easeOut(k));
      kbImg.setAttribute('transform', `translate(${w / 2 + kb.px * k} ${h / 2 + kb.py * k}) scale(${zz}) translate(${-w / 2} ${-h / 2})`);
      if (anim) anim(animG, t - t0, t);
      for (const te of tapeEls) {
        const u = clamp((t - te.t) / 0.1);
        te.el.style.display = u > 0 ? 'block' : 'none';
        te.el.style.transform = `rotate(${te.rot}deg) scaleX(${easeOut(u)})`;
      }
    }
  };
  ITEMS.push(it); return it;
}
function tapeShape(w, h, seed) {
  const r = rng(seed), pts = [];
  const teeth = 5;
  pts.push([0, 0]);
  for (let i = 1; i <= 8; i++) pts.push([w * i / 8, (r() - 0.5) * 1.5]);
  for (let i = 1; i < teeth * 2; i++) pts.push([w - (i % 2 ? 7 + r() * 4 : r() * 3), h * i / (teeth * 2)]);
  pts.push([w, h]);
  for (let i = 7; i >= 1; i--) pts.push([w * i / 8, h + (r() - 0.5) * 1.5]);
  pts.push([0, h]);
  for (let i = teeth * 2 - 1; i >= 1; i--) pts.push([(i % 2 ? 7 + r() * 4 : r() * 3), h * i / (teeth * 2)]);
  return pts;
}

// ---------------- word pieces (ransom style captions) ----------------
const STY = {
  n: { bg: PAL.paper, fg: PAL.espresso, tex: 'paper_white.jpg' },
  c: { bg: PAL.cream, fg: PAL.espresso, tex: 'paper_cream.jpg' },
  m: { bg: PAL.mustard, fg: PAL.espresso },
  t: { bg: PAL.terracotta, fg: PAL.paper },
  s: { bg: PAL.sageD, fg: PAL.paper },
  e: { bg: PAL.espresso, fg: PAL.cream },
};
function phrase({ layer = world, x, y, rot = 0, lines, size = 64, z = 40, gap = 10, lineGap = 14, seed = 1, tOut = null }) {
  const root = el('div', 'phrase', layer, { left: x + 'px', top: y + 'px', zIndex: z, transform: `translate(-50%, 0) rotate(${rot}deg)` });
  const r = rng(seed * 31 + 7);
  const words = [];
  lines.forEach((ln, li) => {
    const row = el('div', 'row', root, { gap: gap + 'px', marginTop: li ? lineGap + 'px' : '0' });
    ln.forEach(([txt, tt, sty = 'n', sz]) => {
      const S = STY[sty];
      const w = el('span', 'word', row, {
        fontSize: (sz || size) + 'px', color: S.fg,
        backgroundColor: S.bg, backgroundImage: S.tex ? `url(${A}${S.tex})` : 'none',
        clipPath: pctPoly(Math.floor(r() * 1e6)),
      });
      w.textContent = txt;
      const jr = (r() - 0.5) * 6, jy = (r() - 0.5) * 10;
      words.push({ el: w, t: tt, jr, jy, seed: r() * 1000 });
      cue(tt, 'word', { big: !!sz || sty !== 'n' });
    });
  });
  const it = {
    update(t) {
      let any = false;
      for (const w of words) {
        if (t < w.t - 0.02) { w.el.style.visibility = 'hidden'; continue; }
        any = true; w.el.style.visibility = 'visible';
        const f = Math.floor((t - w.t + 0.02) * FPS); // stop-motion pop over 3 frames
        const s = f <= 0 ? 1.34 : f === 1 ? 1.12 : f === 2 ? 0.97 : 1;
        const hand = Math.floor(t * 6 + w.seed); // subtle hand-moved jitter at 6fps
        const jj = (hash(hand) - 0.5) * 0.6;
        w.el.style.transform = `translateY(${w.jy}px) rotate(${w.jr + jj}deg) scale(${s})`;
      }
      root.style.display = any ? 'block' : 'none';
      if (tOut !== null) {
        const u = clamp((t - tOut) / 0.26);
        root.style.transform = `translate(calc(-50% + ${-1500 * easeIn(u)}px), ${-120 * easeIn(u)}px) rotate(${rot - 18 * easeIn(u)}deg)`;
        if (u >= 1) root.style.display = 'none';
      }
    }
  };
  if (tOut !== null) cue(tOut, 'peel');
  ITEMS.push(it); return it;
}

// ---------------- generic dropped paper bits ----------------
function bit({ layer = world, x, y, w, h, rot, t0, html, z = 8, sound = 'dropSoft', tapes = [] }) {
  const root = el('div', 'item', layer, { left: (x - w / 2) + 'px', top: (y - h / 2) + 'px', width: w + 'px', height: h + 'px', zIndex: z });
  root.innerHTML = html;
  const tapeEls = tapes.map((tp, i) => { const tw = tp.w || 150, th = 46; const te = el('div', 'tape', root, { left: (tp.x - tw / 2) + 'px', top: (tp.y - th / 2) + 'px', width: tw + 'px', height: th + 'px', clipPath: `path('${polyPath(tapeShape(tw, th, 900 + i + x))}')` }); return { el: te, rot: tp.rot, t: t0 + 0.4 + i * 0.08 }; });
  cue(t0, sound);
  const it = { update(t) {
    const st = dropState(t, t0, 0.3, { dx: 30, dy: -600, rot: rot > 0 ? 18 : -18, s: 1.25 });
    if (!st.vis) { root.style.display = 'none'; return; }
    root.style.display = 'block';
    root.style.transform = `translate(${st.dx}px, ${st.dy}px) rotate(${rot + st.rot}deg) scale(${st.s})`;
    root.style.filter = shadowCSS(st.h, 0.9);
    for (const te of tapeEls) { const u = clamp((t - te.t) / 0.1); te.el.style.display = u > 0 ? 'block' : 'none'; te.el.style.transform = `rotate(${te.rot}deg) scaleX(${easeOut(u)})`; }
  } };
  ITEMS.push(it); return it;
}

// ---------------- stamps ----------------
function stamp({ layer = world, x, y, rot, t0, svg, w, h, z = 60, ink = 1, big = false, clean = false }) {
  const root = el('div', clean ? 'stamp clean' : 'stamp', layer, { left: (x - w / 2) + 'px', top: (y - h / 2) + 'px', width: w + 'px', height: h + 'px', zIndex: z, opacity: ink });
  root.innerHTML = svg;
  cue(t0, big ? 'stampBig' : 'stamp'); impact(t0 + 0.04, big ? 8 : 5);
  const it = {
    update(t) {
      if (t < t0) { root.style.display = 'none'; return; }
      root.style.display = 'block';
      const f = Math.floor((t - t0) * FPS);
      const s = f <= 0 ? 1.25 : f === 1 ? 1.04 : 1;
      root.style.transform = `rotate(${rot}deg) scale(${s})`;
    }
  };
  ITEMS.push(it); return it;
}
function rectStampSVG(w, h, ar, en, col) {
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <rect x="6" y="6" width="${w - 12}" height="${h - 12}" rx="10" fill="none" stroke="${col}" stroke-width="7"/>
    <rect x="17" y="17" width="${w - 34}" height="${h - 34}" rx="6" fill="none" stroke="${col}" stroke-width="3"/>
    <text x="${w / 2}" y="${h * (en ? 0.56 : 0.66)}" text-anchor="middle" font-family="Lalezar" font-size="${en ? h * 0.40 : h * 0.44}" fill="${col}">${ar}</text>
    ${en ? `<text x="${w / 2}" y="${h * 0.8}" text-anchor="middle" font-family="Special Elite" font-size="${h * 0.15}" letter-spacing="4" fill="${col}">${en}</text>` : ''}
  </svg>`;
}
function solidStampSVG(w, h, ar, col) {
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <rect x="4" y="4" width="${w - 8}" height="${h - 8}" rx="14" fill="${col}"/>
    <rect x="16" y="16" width="${w - 32}" height="${h - 32}" rx="8" fill="none" stroke="#FBF7EE" stroke-width="4"/>
    <text x="${w / 2}" y="${h * 0.68}" text-anchor="middle" font-family="Lalezar" font-size="${h * 0.5}" fill="#FBF7EE">${ar}</text>
  </svg>`;
}
function roundStampSVG(R, col, center = 'كلوفا', ringTxt = 'SPECIALTY COFFEE ★ KLOVA ★ ') {
  const id = 'rs' + (++uid);
  return `<svg width="${2 * R}" height="${2 * R}" viewBox="0 0 ${2 * R} ${2 * R}">
    <defs><path id="${id}" d="M ${R} ${R} m ${-(R - 36)} 0 a ${R - 36} ${R - 36} 0 1 1 ${2 * (R - 36)} 0 a ${R - 36} ${R - 36} 0 1 1 ${-2 * (R - 36)} 0"/></defs>
    <circle cx="${R}" cy="${R}" r="${R - 6}" fill="none" stroke="${col}" stroke-width="7"/>
    <circle cx="${R}" cy="${R}" r="${R - 58}" fill="none" stroke="${col}" stroke-width="3"/>
    <text font-family="Special Elite" font-size="${R * 0.2}" fill="${col}" letter-spacing="2"><textPath href="#${id}">${ringTxt}${ringTxt}</textPath></text>
    <text x="${R}" y="${R * 1.16}" text-anchor="middle" font-family="Lalezar" font-size="${R * 0.52}" fill="${col}">${center}</text>
  </svg>`;
}

// ---------------- stickers (die-cut, hand-moved on 8fps) ----------------
function sticker({ layer = world, x, y, rot, t0, svg, w, h, z = 70, sound = 'pop' }) {
  const root = el('div', 'sticker', layer, { left: (x - w / 2) + 'px', top: (y - h / 2) + 'px', width: w + 'px', height: h + 'px', zIndex: z });
  root.innerHTML = svg;
  cue(t0, sound);
  const seed = uid++ * 17;
  const it = {
    update(t) {
      if (t < t0) { root.style.display = 'none'; return; }
      root.style.display = 'block';
      const f = Math.floor((t - t0) * 10); // 10 fps "hand" frames for pop
      const s = f === 0 ? 0.55 : f === 1 ? 1.18 : f === 2 ? 0.95 : 1;
      const hf = Math.floor(t * 8 + seed); // keeps nudging like it's moved by hand
      const jr = (hash(hf) - 0.5) * 5, jx = (hash(hf + 99) - 0.5) * 4, jy = (hash(hf + 7) - 0.5) * 4;
      root.style.transform = `translate(${jx}px, ${jy}px) rotate(${rot + jr}deg) scale(${s})`;
    }
  };
  ITEMS.push(it); return it;
}
const starSVG = (s, col = PAL.mustard) => `<svg width="${s}" height="${s}" viewBox="-60 -60 120 120"><path d="${starPath(50, 22)}" fill="${col}" stroke="#FBF7EE" stroke-width="10" stroke-linejoin="round"/></svg>`;
function starPath(R, r) { let d = ''; for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r : R; d += (i ? 'L' : 'M') + (Math.cos(a) * rr).toFixed(1) + ' ' + (Math.sin(a) * rr).toFixed(1); } return d + 'Z'; }
const heartSVG = (s, col = PAL.terracotta) => `<svg width="${s}" height="${s}" viewBox="-60 -60 120 120"><path d="M0 40 C -60 0, -52 -46, -22 -46 C -8 -46, -2 -36, 0 -28 C 2 -36, 8 -46, 22 -46 C 52 -46, 60 0, 0 40 Z" fill="${col}" stroke="#FBF7EE" stroke-width="9" stroke-linejoin="round"/></svg>`;
function tagSVG(txt, col, fg, w = 250, h = 96) {
  return `<svg width="${w + 16}" height="${h + 16}" viewBox="-8 -8 ${w + 16} ${h + 16}">
    <path d="M22 0 H${w} V${h} H22 L0 ${h / 2} Z" fill="${col}" stroke="#FBF7EE" stroke-width="7" stroke-linejoin="round"/>
    <circle cx="24" cy="${h / 2}" r="8" fill="#FBF7EE"/>
    <text x="${w / 2 + 14}" y="${h * 0.7}" text-anchor="middle" font-family="Lalezar" font-size="${h * 0.56}" fill="${fg}">${txt}</text></svg>`;
}

// ---------------- marker doodles ----------------
function doodle({ layer = world, paths, t0, dur, col = PAL.terracotta, width = 16, z = 65, w = 2700, h = 4800, ox = 0, oy = 0 }) {
  const root = el('div', 'doodle', layer, { left: ox + 'px', top: oy + 'px', width: w + 'px', height: h + 'px', zIndex: z });
  root.innerHTML = `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${paths.map(d => `<path d="${d}" fill="none" stroke="${col}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round" opacity="0.92"/>`).join('')}</svg>`;
  const ps = [...root.querySelectorAll('path')].map(p => ({ p, L: p.getTotalLength() }));
  ps.forEach(o => { o.p.style.strokeDasharray = o.L; });
  const total = ps.reduce((a, o) => a + o.L, 0);
  cue(t0, 'marker', { dur });
  const it = {
    update(t) {
      if (t < t0) { root.style.display = 'none'; return; }
      root.style.display = 'block';
      let drawn = total * clamp((t - t0) / dur);
      for (const o of ps) { const d = clamp(drawn, 0, o.L); o.p.style.strokeDashoffset = o.L - d; drawn -= o.L; }
    }
  };
  ITEMS.push(it); return it;
}

// ---------------- receipt ----------------
function receipt({ x, y, rot, t0, tUnroll0, tUnroll1, z = 30 }) {
  const w = 300, H = 560;
  const root = el('div', 'item', world, { left: (x - w / 2) + 'px', top: (y - H / 2) + 'px', width: w + 'px', height: H + 'px', zIndex: z });
  const clip = el('div', '', root, { position: 'absolute', left: 0, top: 0, width: w + 'px', height: H + 'px', overflow: 'hidden' });
  const zig = []; for (let i = 0; i <= 20; i++) zig.push(`${(i / 20 * 100).toFixed(1)}% ${i % 2 ? 100 : 97.2}%`);
  const paper = el('div', 'receipt', clip, { width: w + 'px', height: H + 'px', clipPath: `polygon(0 0, 100% 0, ${zig.reverse().join(',')})` });
  const days = ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'];
  paper.innerHTML = `<div class="rhead">CAFÉ · RECEIPT</div><div class="rsep">- - - - - - - - - - - - - -</div>` +
    days.map(d => `<div class="rline"><span>قهوة ${d}</span><span class="dots">..........</span><span>✓</span></div>`).join('') +
    `<div class="rsep">- - - - - - - - - - - - - -</div><div class="rtot">المجموع: <b>كل يوم!</b></div><div class="rbar"></div>`;
  cue(t0, 'drop'); cue(t0 + 0.34, 'land'); cue(tUnroll0, 'receipt', { dur: tUnroll1 - tUnroll0 });
  const it = {
    update(t) {
      const st = dropState(t, t0, 0.34, { dx: -40, dy: -800, rot: -12, s: 1.2 });
      if (!st.vis) { root.style.display = 'none'; return; }
      root.style.display = 'block';
      root.style.transform = `translate(${st.dx}px, ${st.dy}px) rotate(${rot + st.rot}deg) scale(${st.s})`;
      root.style.filter = shadowCSS(st.h);
      const u = clamp((t - tUnroll0) / (tUnroll1 - tUnroll0));
      const hh = lerp(150, H, easeInOut(u));
      clip.style.height = hh + 'px';
    }
  };
  ITEMS.push(it); return it;
}

// ---------------- hook clipping ----------------
function hookClip({ x, y, rot, t0 }) {
  const w = 1000, h = 340;
  const root = el('div', 'item', world, { left: (x - w / 2) + 'px', top: (y - h / 2) + 'px', width: w + 'px', height: h + 'px', zIndex: 20 });
  const shape = polyPath(tornPoly(w, h, 991, 6, 16));
  root.innerHTML = `<div class="hookpaper" style="clip-path:path('${shape}')">
      <div class="hl1">إذا تسوي قهوتك</div><div class="hl2">في <span>البيت؟</span></div></div>`;
  cue(t0, 'dropBig'); cue(t0 + 0.34, 'landBig'); impact(t0 + 0.34, 7);
  const it = {
    update(t) {
      const st = dropState(t, t0, 0.34, { dx: 0, dy: -700, rot: -10, s: 1.35 });
      if (!st.vis) { root.style.display = 'none'; return; }
      root.style.display = 'block';
      root.style.transform = `translate(${st.dx}px, ${st.dy}px) rotate(${rot + st.rot}deg) scale(${st.s})`;
      root.style.filter = shadowCSS(st.h);
    }
  };
  ITEMS.push(it); return it;
}

// =====================================================================
//                              THE PAGE
// =====================================================================
const IL = { homebrew: [600, 720], bag: [560, 680], espresso: [560, 680], beans: [640, 560], cherries: [580, 700], tasting: [560, 620], cafe: [540, 640], homeMug: [580, 680], final: [860, 960] };
const C = (name, o) => card({ img: `il_${name}.png`, iw: IL[name][0], ih: IL[name][1], ...o });

// animated inner layers ------------------------------------------------
function animHomebrew(g, lt, t) {
  if (!g._init) {
    g.innerHTML = `<path class="stream" fill="none" stroke="#4A2A18" stroke-width="6" stroke-linecap="round" opacity="0.9"/>
      <circle class="d1" r="5" fill="#4A2A18"/><circle class="d2" r="4.5" fill="#4A2A18"/>
      <path class="st1" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" opacity="0.5"/>
      <path class="st2" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity="0.4"/>`;
    g._init = true;
  }
  const w = Math.sin(t * 9) * 3, w2 = Math.sin(t * 13 + 1) * 2;
  g.querySelector('.stream').setAttribute('d', `M 294 247 C ${300 + w} 270, ${306 + w2} 292, ${312 + w} 312`);
  const d1 = (t * 1.6) % 1, d2 = (t * 1.6 + 0.5) % 1;
  const dy = p => 420 + easeIn(p) * 70;
  g.querySelector('.d1').setAttribute('cy', dy(d1)); g.querySelector('.d1').setAttribute('cx', 330);
  g.querySelector('.d2').setAttribute('cy', dy(d2)); g.querySelector('.d2').setAttribute('cx', 330);
  const steam = (cls, x, y, ph) => { const k = (t * 0.6 + ph) % 1; const yy = y - k * 90; const a = Math.sin(k * Math.PI);
    const e = g.querySelector(cls); e.setAttribute('d', `M ${x} ${yy} c -14 -20, 14 -34, 0 -56 c -10 -16, 6 -26, 2 -36`); e.setAttribute('opacity', (0.5 * a).toFixed(2)); };
  steam('.st1', 505, 440, 0); steam('.st2', 312, 400, 0.45);
}
function animEspresso(g, lt, t) {
  if (!g._init) { g.innerHTML = `<path class="sh" fill="none" stroke="#4A2A18" stroke-width="5" stroke-linecap="round"/><path class="st1" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"/>`; g._init = true; }
  const w = Math.sin(t * 17) * 1.2;
  g.querySelector('.sh').setAttribute('d', `M ${281 + w} 354 L ${281 - w} 462`);
  const k = (t * 0.55) % 1; const e = g.querySelector('.st1');
  e.setAttribute('d', `M 281 ${452 - k * 70} c -12 -16, 12 -30, 0 -48 c -8 -14, 6 -22, 2 -30`); e.setAttribute('opacity', (0.5 * Math.sin(k * Math.PI)).toFixed(2));
}
function animMug(g, lt, t) {
  if (!g._init) { g.innerHTML = `<path class="st1" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round"/><path class="st2" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round"/><path class="st3" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"/>`; g._init = true; }
  [['.st1', 250, 0], ['.st2', 300, 0.35], ['.st3', 340, 0.7]].forEach(([c, x, ph]) => {
    const k = (t * 0.5 + ph) % 1; const e = g.querySelector(c); const y = 230 - k * 110;
    e.setAttribute('d', `M ${x} ${y} c -18 -24, 18 -40, 0 -68 c -12 -20, 8 -32, 3 -44`); e.setAttribute('opacity', (0.55 * Math.sin(k * Math.PI)).toFixed(2));
  });
}
function animCafe(g, lt, t) {
  if (!g._init) { g.innerHTML = `<path class="st1" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round"/>`; g._init = true; }
  const k = (t * 0.5) % 1; const e = g.querySelector('.st1');
  e.setAttribute('d', `M 190 ${120 - k * 90} c -14 -20, 14 -34, 0 -56 c -10 -16, 6 -26, 2 -36`); e.setAttribute('opacity', (0.5 * Math.sin(k * Math.PI)).toFixed(2));
}

// ---- 0–3s : HOOK ----
hookClip({ x: 1350, y: 1185, rot: 1.5, t0: 0.03 });
C('homebrew', { x: 1350, y: 650, rot: -3, t0: 0.78, anim: animHomebrew, tapes: [{ x: 60, y: 30, rot: -38 }, { x: 588, y: 30, rot: 36 }], z: 12,
  decor: { dx: -90, dy: 90, w: 300, h: 420, col: PAL.mustardL, rot: -9 } });
stamp({ x: 1490, y: 1350, rot: -6, t0: 1.9, w: 560, h: 170, svg: solidStampSVG(560, 170, 'هذا الفيديو لك', PAL.terracotta), z: 70, big: true, ink: 1, clean: true });
sticker({ x: 900, y: 1400, rot: -14, t0: 2.35, w: 150, h: 150, svg: heartSVG(150) });
sticker({ x: 1860, y: 470, rot: 12, t0: 2.6, w: 110, h: 110, svg: starSVG(110) });

// ---- 3.3s : KLOVA ----
C('bag', { x: 700, y: 1990, rot: 5, t0: 3.18, tapes: [{ x: 300, y: 18, rot: -4, w: 190 }], z: 14,
  decor: { dx: 330, dy: 380, w: 380, h: 300, col: PAL.sageL, rot: 12 } });
stamp({ x: 1000, y: 1700, rot: 14, t0: 4.36, w: 230, h: 230, svg: roundStampSVG(115, PAL.terracotta), z: 60 });
phrase({ x: 740, y: 2360, rot: -2, seed: 2, lines: [[['حنا', 3.32, 'n'], ['كلوفا', 3.66, 'm', 84]], [['متجر', 4.36], ['متخصص', 4.66], ['في', 5.14]], [['محاصيل', 5.26, 's'], ['القهوة', 5.62, 's']]] });

// ---- 6.3s : not the machine ----
C('espresso', { x: 2000, y: 2140, rot: -6, t0: 6.22, anim: animEspresso, tapes: [{ x: 40, y: 360, rot: 80, w: 150 }, { x: 568, y: 40, rot: 40 }], z: 15,
  decor: { dx: -110, dy: -60, w: 320, h: 360, col: PAL.blush, rot: -14 } });
phrase({ x: 1990, y: 2540, rot: 2, seed: 3, lines: [[['والفرق', 6.32], ['غالباً', 6.8]], [['مو', 7.36, 't'], ['في', 7.54, 't'], ['المكينة', 7.66, 't', 76]]] });
doodle({ paths: ['M 1790 1920 C 1900 2050, 2050 2220, 2190 2380', 'M 2200 1930 C 2080 2060, 1930 2240, 1800 2390'], t0: 7.4, dur: 0.5, width: 20 });

// ---- 8.4s : the crop itself ----
C('beans', { x: 1300, y: 3130, rot: -4, t0: 8.36, tapes: [{ x: 90, y: 20, rot: -30 }, { x: 600, y: 590, rot: -30 }], z: 16, kb: { z0: 1.0, z1: 1.12, px: 14, py: -10 } });
phrase({ x: 1320, y: 3475, rot: -1.5, seed: 4, lines: [[['الفرق', 8.42], ['في', 8.92]], [['المحصول', 9.08, 'm', 80], ['نفسه', 9.7, 'm', 80]]] });
doodle({ paths: ['M 1180 3000 C 1380 2930, 1560 3020, 1540 3150 C 1520 3280, 1250 3320, 1110 3230 C 990 3150, 1040 3010, 1230 2985'], t0: 9.1, dur: 0.55, width: 14, col: PAL.mustard });
sticker({ x: 1690, y: 2880, rot: 10, t0: 9.72, w: 130, h: 130, svg: starSVG(130) });

// ---- 10.4s : many origins ----
C('cherries', { x: 620, y: 3880, rot: -3, t0: 10.36, tapes: [{ x: 320, y: 16, rot: 3, w: 200 }], z: 17,
  decor: { dx: 380, dy: -70, w: 330, h: 300, col: PAL.cream, rot: 16 } });
phrase({ x: 680, y: 4295, rot: 1.5, seed: 5, lines: [[['عشان', 10.44], ['كذا', 10.66], ['نوفر', 10.82], ['لك', 11.2]], [['محاصيل', 11.34, 's'], ['من', 11.8], ['أكثر', 12.02], ['من', 12.46], ['بلد', 12.6, 't', 76]]] });
stamp({ x: 330, y: 3600, rot: -12, t0: 11.86, w: 300, h: 132, svg: rectStampSVG(300, 132, 'إثيوبيا', 'ETHIOPIA', PAL.terracotta) });
stamp({ x: 935, y: 3650, rot: 9, t0: 12.16, w: 310, h: 132, svg: rectStampSVG(310, 132, 'كولومبيا', 'COLOMBIA', PAL.sageD) });
stamp({ x: 340, y: 4120, rot: 7, t0: 12.46, w: 300, h: 132, svg: rectStampSVG(300, 132, 'البرازيل', 'BRAZIL', PAL.coffee) });
stamp({ x: 925, y: 4090, rot: -8, t0: 12.8, w: 260, h: 132, svg: rectStampSVG(260, 132, 'كينيا', 'KENYA', PAL.terraD) });

// ---- 13.2s : each has its taste ----
C('tasting', { x: 2070, y: 3330, rot: 6, t0: 13.1, tapes: [{ x: 30, y: 30, rot: -42 }, { x: 578, y: 640, rot: -42 }], z: 18 });
phrase({ x: 2030, y: 3715, rot: -2, seed: 6, lines: [[['كل', 13.18], ['واحد', 13.4], ['له', 13.76], ['طعمه', 13.96, 'm', 84]]] });
sticker({ x: 1830, y: 3070, rot: -10, t0: 13.45, w: 266, h: 112, svg: tagSVG('توتي', '#8E2A3A', PAL.paper, 220, 96) });
sticker({ x: 2340, y: 3130, rot: 12, t0: 13.7, w: 296, h: 112, svg: tagSVG('شوكولاتة', PAL.coffee, PAL.paper, 250, 96) });
sticker({ x: 1830, y: 3560, rot: 8, t0: 13.95, w: 246, h: 112, svg: tagSVG('زهري', PAL.terraL, PAL.espresso, 200, 96) });
sticker({ x: 2330, y: 3560, rot: -9, t0: 14.2, w: 246, h: 112, svg: tagSVG('حمضي', PAL.mustard, PAL.espresso, 200, 96) });

// ---- 14.6s : without paying the café every day ----
C('cafe', { x: 2020, y: 4190, rot: -4, t0: 14.52, anim: animCafe, tapes: [{ x: 294, y: 14, rot: -2, w: 180 }], z: 19,
  decor: { dx: 380, dy: 420, w: 300, h: 320, col: PAL.mustardL, rot: -8 } });
receipt({ x: 1560, y: 4230, rot: 7, t0: 14.72, tUnroll0: 15.0, tUnroll1: 15.8, z: 21 });
phrase({ x: 1800, y: 4560, rot: 1.5, seed: 7, lines: [[['بدون', 14.6], ['ماتدفع', 14.9], ['كل', 15.36], ['يوم', 15.6]], [['في', 15.86], ['الكوفيّات', 15.98, 't', 80]]] });
doodle({ paths: ['M 1440 3990 C 1520 4150, 1600 4320, 1700 4470', 'M 1700 4000 C 1620 4160, 1530 4330, 1430 4470'], t0: 16.02, dur: 0.4, width: 18 });

// ---- 16.8s : pull back, never compromise on taste ----
C('homeMug', { x: 1350, y: 2340, rot: -5, t0: 17.05, anim: animMug, tapes: [{ x: 50, y: 40, rot: -40 }, { x: 610, y: 40, rot: 40 }], z: 25, big: true,
  from: { dx: 0, dy: -1600, rot: -20, s: 1.5 } });
sticker({ x: 1700, y: 1990, rot: 14, t0: 18.12, w: 170, h: 170, svg: heartSVG(170) });
sticker({ x: 1010, y: 2690, rot: -12, t0: 18.3, w: 140, h: 140, svg: heartSVG(140, PAL.mustard) });
phrase({ layer: screenLayer, x: 540, y: 1150, rot: -2, seed: 8, size: 76, z: 80, tOut: 18.5, lines: [[['وبدون', 16.78], ['ماتتنازل', 17.22]], [['عن', 18.02, 'n', 88], ['الطعم', 18.18, 'm', 96]]] });

// page fillers dropping in while we pull back (the page fills up)
bit({ x: 430, y: 760, w: 380, h: 150, rot: -12, t0: 17.5, html: `<div class="ticket"><div class="tk1">HOME CAFÉ</div><div class="tk2">★ ADMIT ONE ★</div><div class="tk3">No. 0725</div></div>` });
C('beans', { x: 2260, y: 820, rot: 9, t0: 17.62, iw: 320, ih: 280, border: 16, z: 7, tapes: [{ x: 176, y: 8, rot: -3, w: 130 }], kb: { z0: 1.3, z1: 1.35, px: 0, py: 0 } });
bit({ x: 420, y: 3170, w: 400, h: 250, rot: 5, t0: 17.74, html: `<div class="note">قهوة البيت<br><span>أحلى ♥</span></div>`, tapes: [{ x: 200, y: 4, rot: 2, w: 140 }] });
C('cherries', { x: 2360, y: 1330, rot: -7, t0: 17.86, iw: 280, ih: 300, border: 16, z: 7, kb: { z0: 1.5, z1: 1.55, px: 0, py: 0 } });
bit({ x: 420, y: 4620, w: 360, h: 140, rot: 8, t0: 17.98, html: `<div class="ticket alt"><div class="tk1">FRESH CROP</div><div class="tk2">SPECIALTY ★ BEANS</div></div>` });
sticker({ x: 2480, y: 2860, rot: 10, t0: 18.05, w: 120, h: 120, svg: starSVG(120, PAL.sage) });
sticker({ x: 280, y: 1500, rot: -10, t0: 18.12, w: 110, h: 110, svg: starSVG(110) });

// ---- 18.5s : final big clipping (product) + CTA ----
C('final', { layer: screenLayer, x: 540, y: 690, rot: -2.5, t0: 18.46, z: 90, big: true, border: 26,
  from: { dx: 0, dy: -1500, rot: -9, s: 1.3 }, kb: { z0: 1.0, z1: 1.05, px: 0, py: -6 },
  tapes: [{ x: 70, y: 40, rot: -40, w: 200, dt: 0.4 }, { x: 842, y: 40, rot: 40, w: 200, dt: 0.52 }] });
phrase({ layer: screenLayer, x: 560, y: 1225, rot: 1.5, seed: 9, size: 80, z: 95, lines: [[['اختار', 18.8, 'n'], ['محصولك', 19.08, 'm', 92]], [['من', 19.52], ['الرابط', 19.64, 't', 88], ['بالبايو', 20.02, 't', 88]]] });
doodle({ layer: screenLayer, w: 1080, h: 1920, z: 96, paths: ['M 150 1250 C 90 1330, 90 1430, 150 1520', 'M 108 1480 L 152 1526 L 196 1478'], t0: 20.3, dur: 0.45, width: 14 });
stamp({ layer: screenLayer, x: 840, y: 250, rot: 14, t0: 20.62, w: 250, h: 250, svg: roundStampSVG(125, PAL.terracotta), z: 97, big: true });
sticker({ layer: screenLayer, x: 170, y: 250, rot: -12, t0: 20.9, w: 130, h: 130, svg: starSVG(130), z: 97 });

// ---------------- camera ----------------
const CAM = [
  [0.0, 1350, 1150, 1.14, 0], [0.7, 1350, 1120, 1.12, 0], [1.35, 1350, 930, 1.07, -0.3], [2.95, 1350, 950, 1.03, -0.6],
  [3.4, 730, 2225, 1.12, 0.8], [6.0, 740, 2240, 1.16, 0.3],
  [6.45, 1985, 2375, 1.12, -0.8], [8.2, 1990, 2390, 1.16, -0.4],
  [8.62, 1305, 3350, 1.12, 0.6], [10.2, 1310, 3360, 1.16, 0.2],
  [10.62, 645, 4110, 1.08, -0.6], [12.98, 650, 4120, 1.11, -0.2],
  [13.36, 2065, 3545, 1.1, 0.8], [14.36, 2068, 3555, 1.13, 0.5],
  [14.76, 1830, 4420, 1.06, -0.6], [16.62, 1835, 4430, 1.09, -0.4],
  [18.3, 1350, 2400, 0.4, 0], [DUR, 1350, 2400, 0.415, 0.3],
];
for (let i = 1; i < CAM.length; i++) { const a = CAM[i - 1], b = CAM[i]; if (Math.hypot(b[1] - a[1], b[2] - a[2]) > 300) cue(a[0], 'swoosh', { dur: b[0] - a[0] }); }
function camera(t) {
  let i = 1; while (i < CAM.length - 1 && t > CAM[i][0]) i++;
  const a = CAM[i - 1], b = CAM[i];
  const u = easeInOut(clamp((t - a[0]) / (b[0] - a[0])));
  const z = Math.exp(lerp(Math.log(a[3]), Math.log(b[3]), u));
  let sx = 0, sy = 0;
  for (const im of IMPACTS) { const k = t - im.t; if (k >= 0 && k < 0.4) { const d = Math.exp(-k * 14) * im.s; sx += Math.sin(k * 70) * d * 0.6; sy += Math.cos(k * 55) * d; } }
  return { cx: lerp(a[1], b[1], u), cy: lerp(a[2], b[2], u), z, r: lerp(a[4], b[4], u), sx, sy };
}

// ---------------- render ----------------
function render(t) {
  const c = camera(t);
  world.style.transform = `translate(${SW / 2 + c.sx}px, ${SH / 2 + c.sy}px) rotate(${c.r}deg) scale(${c.z}) translate(${-c.cx}px, ${-c.cy}px)`;
  for (const it of ITEMS) it.update(t);
  grain.src = A + 'grain' + (Math.floor(t * 15) % 6) + '.png';
}
window.render = render;
window.EVENTS = EVENTS;
window.META = { FPS, DUR };
