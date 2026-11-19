/* Notebook-style motion graphic. Everything is a pure function of time: window.setTime(t). */
(function () {
  const S = window.STROKES, TM = window.TEXTMAN;
  const NS = 'http://www.w3.org/2000/svg';
  const INK = '#1f1d1a', YEL = '#F6CF4E', YEL2 = '#F3C63A', BEI = '#EFE2C6';
  const DURATION = 17.2;
  const stage = document.getElementById('stage');
  const items = [];
  let uid = 0;

  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, f) => a + (b - a) * f;
  const easeIO = p => (p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const easeOut = p => 1 - Math.pow(1 - p, 3);
  const easeOutBack = p => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
  const penEase = p => .6 * p + .4 * easeIO(p);

  function el(tag, cls, parent) { const e = document.createElement(tag); if (cls) e.className = cls; if (parent) parent.appendChild(e); return e; }
  function sv(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function rng(seed) { let s = (seed * 2654435761) >>> 0 || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
  function smooth(pts, closed) {
    const P = closed ? [pts[pts.length - 1], ...pts, pts[0], pts[1]] : [pts[0], ...pts, pts[pts.length - 1]];
    let d = `M${P[1][0].toFixed(1)} ${P[1][1].toFixed(1)}`;
    for (let i = 1; i < P.length - 2; i++) {
      const p0 = P[i - 1], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += `C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
    }
    return d;
  }
  const reg = it => { items.push(it); return it; };

  /* ---------------- notebook ---------------- */
  const PAGE = { x: 44, y: 150, w: 992, h: 1730 };
  const RING_X = []; for (let x = 92; x <= 990; x += 48) RING_X.push(x);
  for (const off of [18, 9]) { const s = el('div', 'sheet', stage); s.style.top = (PAGE.y + off) + 'px'; s.style.left = (PAGE.x + off / 4) + 'px'; }

  function makePage(i, kind) {
    const page = el('div', 'page', stage); page.style.zIndex = 50 - i;
    const front = el('div', 'face', page);
    const paper = el('div', 'paper ' + kind, front);
    el('div', 'lines', paper); el('div', 'margin', paper);
    for (const x of RING_X) { const h = el('div', 'hole', paper); h.style.left = (x - PAGE.x - 11) + 'px'; }
    const under = sv('svg', { class: 'layer mb', width: 1080, height: 1920, viewBox: '0 0 1080 1920' }, front);
    const mid = el('div', 'layer', front);
    const over = sv('svg', { class: 'layer mb', width: 1080, height: 1920, viewBox: '0 0 1080 1920' }, front);
    const defs = sv('defs', {}, over);
    const cast = el('div', 'cast', front);
    const lift = el('div', 'lift', front);
    const back = el('div', 'face back', page);
    const bp = el('div', 'paper backside', back);
    for (const x of RING_X) { const h = el('div', 'hole', bp); h.style.left = (x - PAGE.x - 11) + 'px'; }
    return { page, front, under, mid, over, defs, cast, lift };
  }
  const pages = ['ruled', 'grid', 'ruled', 'grid', 'ruled'].map((k, i) => makePage(i, k));

  // spiral rings (static, over the pages)
  const rings = sv('svg', { id: 'rings', width: 1080, height: 300, viewBox: '0 0 1080 300' }, stage);
  for (const x of RING_X) {
    sv('path', { d: `M${x} 186 C ${x - 4} 150, ${x - 2} 116, ${x + 8} 112 C ${x + 18} 110, ${x + 21} 132, ${x + 19} 152`,
      fill: 'none', stroke: INK, 'stroke-width': 8, 'stroke-linecap': 'round' }, rings);
    sv('path', { d: `M${x + 1} 170 C ${x - 1} 146, ${x} 124, ${x + 7} 120`,
      fill: 'none', stroke: '#B9B0A2', 'stroke-width': 2.4, 'stroke-linecap': 'round' }, rings);
  }

  /* ---------------- pencil ---------------- */
  const pencil = sv('svg', { id: 'pencil', width: 420, height: 420, viewBox: '-60 -60 420 420' }, stage);
  const pg_ = sv('g', {}, pencil);
  sv('polygon', { points: '0,0 64,-20 64,20', fill: BEI, stroke: INK, 'stroke-width': 4.5, 'stroke-linejoin': 'round' }, pg_);
  sv('polygon', { points: '0,0 22,-7 22,7', fill: INK, stroke: INK, 'stroke-width': 3, 'stroke-linejoin': 'round' }, pg_);
  sv('rect', { x: 64, y: -20, width: 190, height: 40, fill: YEL, stroke: INK, 'stroke-width': 4.5, rx: 3 }, pg_);
  sv('path', { d: 'M70 -6 L248 -6 M70 7 L248 7', stroke: '#D9AE2C', 'stroke-width': 3 }, pg_);
  sv('rect', { x: 254, y: -20, width: 28, height: 40, fill: '#DCCBA7', stroke: INK, 'stroke-width': 4.5 }, pg_);
  sv('path', { d: 'M263 -18 L263 18 M273 -18 L273 18', stroke: INK, 'stroke-width': 2.5 }, pg_);
  sv('rect', { x: 282, y: -19, width: 30, height: 38, rx: 9, fill: '#F2E7D0', stroke: INK, 'stroke-width': 4.5 }, pg_);

  /* ---------------- elements ---------------- */
  // Pen-drawn raster (illustration or handwritten text) revealed along its skeleton strokes.
  function ink(pg, id, o) {
    const st = S[id], W = st.w, H = st.h;
    const dw = o.w || W, sc = dw / W, dh = H * sc;
    const rot = o.rot || 0;
    const svg = sv('svg', { class: 'ink', width: dw, height: dh, viewBox: `0 0 ${W} ${H}` }, pg.mid);
    svg.style.left = (o.cx - dw / 2) + 'px'; svg.style.top = (o.cy - dh / 2) + 'px';
    if (rot) svg.style.transform = `rotate(${rot}deg)`;
    const n = ++uid;
    const defs = sv('defs', {}, svg);
    const m = sv('mask', { id: 'm' + n, maskUnits: 'userSpaceOnUse', x: -40, y: -40, width: W + 80, height: H + 80 }, defs);
    const g = sv('g', { fill: 'none', stroke: '#fff', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, m);
    const strokes = st.strokes.map(s => {
      const cum = [0];
      for (let i = 1; i < s.pts.length; i++) cum.push(cum[i - 1] + Math.hypot(s.pts[i][0] - s.pts[i - 1][0], s.pts[i][1] - s.pts[i - 1][1]));
      const p = sv('path', { d: 'M' + s.pts.map(q => q[0] + ' ' + q[1]).join('L'), 'stroke-width': s.width * (o.widthMul || 1.15) }, g);
      p.style.visibility = 'hidden';
      return Object.assign({ el: p, cum, state: 0 }, s);
    });
    const full = sv('rect', { x: -40, y: -40, width: W + 80, height: H + 80, fill: '#fff', opacity: 0 }, m);
    const isText = !!TM[id];
    let zig = null, zigLen = 0;
    if (!isText) {
      const cm = sv('mask', { id: 'c' + n, maskUnits: 'userSpaceOnUse', x: -80, y: -80, width: W + 160, height: H + 160 }, defs);
      const rows = 6, pts = [];
      for (let r = 0; r <= rows; r++) {
        const y0 = (r - .3) * H / rows;
        pts.push([W * 1.05, y0], [-W * .05, y0 + H / rows * 1.15]);
      }
      for (let i = 1; i < pts.length; i++) zigLen += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      zig = sv('path', { d: 'M' + pts.map(p => p.join(' ')).join('L'), fill: 'none', stroke: '#fff', 'stroke-width': H / rows * 1.9,
        'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, cm);
      zig.style.visibility = 'hidden';
      sv('image', { href: `../build/ink/${id}_color.png`, width: W, height: H, mask: `url(#c${n})` }, svg);
    }
    sv('image', { href: isText ? '../' + TM[id].file : `../build/ink/${id}_ink.png`, width: W, height: H, mask: `url(#m${n})` }, svg);

    const total = st.total, t0 = o.t0, dur = o.dur;
    function head(L) {
      for (let i = 0; i < strokes.length; i++) {
        const s = strokes[i];
        if (L < s.start) {
          if (!i) return s.pts[0];
          const pv = strokes[i - 1], g0 = pv.start + pv.len, f = clamp((L - g0) / Math.max(1e-6, s.start - g0));
          const a = pv.pts[pv.pts.length - 1], b = s.pts[0];
          return [lerp(a[0], b[0], f), lerp(a[1], b[1], f)];
        }
        if (L <= s.start + s.len) {
          const d = L - s.start;
          let k = 1; while (k < s.cum.length - 1 && s.cum[k] < d) k++;
          const f = clamp((d - s.cum[k - 1]) / Math.max(1e-6, s.cum[k] - s.cum[k - 1]));
          return [lerp(s.pts[k - 1][0], s.pts[k][0], f), lerp(s.pts[k - 1][1], s.pts[k][1], f)];
        }
      }
      const s = strokes[strokes.length - 1]; return s.pts[s.pts.length - 1];
    }
    const rr = rot * Math.PI / 180;
    const toStage = (x, y) => {
      const rx = x * sc - dw / 2, ry = y * sc - dh / 2;
      return [o.cx + rx * Math.cos(rr) - ry * Math.sin(rr), o.cy + rx * Math.sin(rr) + ry * Math.cos(rr)];
    };
    return reg({
      t0, t1: t0 + dur, pen: o.pen !== false,
      update(t) {
        const L = penEase(clamp((t - t0) / dur)) * total;
        for (const s of strokes) {
          const d = L - s.start;
          if (d <= 0) { if (s.state) { s.el.style.visibility = 'hidden'; s.state = 0; } continue; }
          if (d >= s.len) { if (s.state !== 2) { s.el.style.visibility = 'visible'; s.el.style.strokeDasharray = 'none'; s.state = 2; } continue; }
          s.el.style.visibility = 'visible'; s.el.style.strokeDasharray = `${d.toFixed(2)} ${s.len + 50}`; s.state = 1;
        }
        full.setAttribute('opacity', clamp((t - (t0 + dur - .04)) / .14).toFixed(3));
        if (zig) {
          const cp = clamp((t - o.ct0) / o.cdur);
          zig.style.visibility = cp > 0 ? 'visible' : 'hidden';
          zig.style.strokeDasharray = `${(easeIO(cp) * zigLen).toFixed(1)} ${zigLen + 50}`;
        }
      },
      penAt(t) { const [x, y] = head(penEase(clamp((t - t0) / dur)) * total); return toStage(x, y); },
    });
  }

  // Vector doodle drawn with a pen (stage coordinates).
  function doodle(pg, d, o) {
    const layer = o.under ? pg.under : pg.over;
    const p = sv('path', { d, fill: 'none', stroke: o.color || INK, 'stroke-width': o.width || 6,
      'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, layer);
    const len = p.getTotalLength();
    p.style.visibility = 'hidden';
    const t0 = o.t0, dur = o.dur;
    return reg({
      t0, t1: t0 + dur, pen: o.pen !== false,
      update(t) {
        const f = clamp((t - t0) / dur);
        p.style.visibility = f > 0 ? 'visible' : 'hidden';
        p.style.strokeDasharray = `${(easeIO(f) * len).toFixed(1)} ${len + 50}`;
      },
      penAt(t) { const q = p.getPointAtLength(easeIO(clamp((t - t0) / dur)) * len); return [q.x, q.y]; },
    });
  }

  function arrow(pg, p0, p1, bend, t0, dur, seed = 1) {
    const r = rng(seed);
    const dx = p1[0] - p0[0], dy = p1[1] - p0[1], L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L;
    const c = [(p0[0] + p1[0]) / 2 + nx * bend * L, (p0[1] + p1[1]) / 2 + ny * bend * L];
    const pts = [];
    for (let i = 0; i <= 14; i++) {
      const u = i / 14, j = i > 0 && i < 14 ? (r() - .5) * 3.2 : 0;
      pts.push([(1 - u) * (1 - u) * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0] + nx * j,
                (1 - u) * (1 - u) * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1] + ny * j]);
    }
    doodle(pg, smooth(pts), { t0, dur: dur * .74, width: 6.5 });
    const tx = p1[0] - c[0], ty = p1[1] - c[1], tl = Math.hypot(tx, ty), ux = tx / tl, uy = ty / tl, hl = 38;
    const side = a => [p1[0] - hl * (ux * Math.cos(a) - uy * Math.sin(a)), p1[1] - hl * (uy * Math.cos(a) + ux * Math.sin(a))];
    const A = side(.52), B = side(-.48);
    doodle(pg, `M${A[0]} ${A[1]} L${p1[0]} ${p1[1]} L${B[0]} ${B[1]}`, { t0: t0 + dur * .76, dur: dur * .24, width: 6.5 });
  }

  function circleScribble(pg, cx, cy, rx, ry, t0, dur, seed = 3) {
    const pts = [], N = 44, th0 = -Math.PI * .3;
    for (let i = 0; i <= N; i++) {
      const u = i / N, th = th0 - u * Math.PI * 2 * 1.13;
      const k = 1 + .045 * Math.sin(3 * th + seed) + u * .07;
      pts.push([cx + rx * k * Math.cos(th), cy + ry * k * Math.sin(th)]);
    }
    doodle(pg, smooth(pts), { t0, dur, width: 6 });
  }

  function underline(pg, x0, x1, y, t0, dur, o = {}) {
    const pts = [], N = 36, waves = o.waves || 4, amp = o.amp == null ? 5 : o.amp;
    for (let i = 0; i <= N; i++) {
      const u = i / N;
      pts.push([x1 - (x1 - x0) * u, y + amp * Math.sin(u * Math.PI * 2 * waves) + (u - .5) * 5]);
    }
    doodle(pg, smooth(pts), { t0, dur, width: o.width || 11, color: o.color || YEL2, under: true });
  }

  function highlight(pg, cx, cy, w, h, t0, dur) {
    const x0 = cx - w / 2, x1 = cx + w / 2, y0 = cy - h / 2, y1 = cy + h / 2, r = rng(11);
    const top = [], bot = [];
    for (let i = 0; i <= 10; i++) { const u = i / 10; top.push([lerp(x0, x1, u), y0 + (r() - .5) * 6]); bot.push([lerp(x1, x0, u), y1 + (r() - .5) * 6]); }
    const d = 'M' + [...top, [x1 + 6, cy], ...bot, [x0 - 6, cy]].map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join('L') + 'Z';
    const n = ++uid;
    const cp = sv('clipPath', { id: 'h' + n }, pg.defs);
    const rect = sv('rect', { x: x1 + 10, y: y0 - 20, width: 0, height: h + 40 }, cp);
    sv('path', { d, fill: YEL, opacity: .85, 'clip-path': `url(#h${n})` }, pg.under);
    // the highlight lives in the under-layer, but its clipPath must be in the same svg
    pg.under.appendChild(cp);
    return reg({
      t0, t1: t0 + dur, pen: false,
      update(t) { const f = easeOut(clamp((t - t0) / dur)); const ww = (w + 20) * f; rect.setAttribute('x', x1 + 10 - ww); rect.setAttribute('width', ww); },
    });
  }

  function sticky(pg, cx, cy, w, h, rot, t0) {
    const s = el('div', 'sticky', pg.mid);
    Object.assign(s.style, { left: (cx - w / 2) + 'px', top: (cy - h / 2) + 'px', width: w + 'px', height: h + 'px' });
    return reg({
      t0, t1: t0 + .24, pen: false,
      update(t) {
        const f = clamp((t - t0) / .24);
        s.style.opacity = clamp(f * 3);
        s.style.transform = `rotate(${rot + (1 - f) * 6}deg) scale(${lerp(1.3, 1, easeOutBack(f))})`;
      },
    });
  }

  function box(pg, x, y, w, h, t0, dur, seed = 5) {
    const r = rng(seed), j = () => (r() - .5) * 5;
    const pts = [[x + w - 26, y + j()], [x + w * .5, y - 2 + j()], [x + 26, y + j()], [x + j(), y + 28], [x + j(), y + h * .5],
      [x + j(), y + h - 28], [x + 28, y + h + j()], [x + w * .5, y + h + 2 + j()], [x + w - 28, y + h + j()], [x + w + j(), y + h - 28],
      [x + w + j(), y + h * .5], [x + w + j(), y + 30], [x + w - 34, y - 3], [x + w * .62, y + 4]];
    const fill = sv('path', { d: smooth(pts.slice(0, 12), true), fill: BEI, opacity: 0 }, pg.under);
    doodle(pg, smooth(pts), { t0, dur, width: 5.5 });
    reg({ t0: t0 + dur * .5, t1: t0 + dur + .25, pen: false,
      update(t) { fill.setAttribute('opacity', (.9 * clamp((t - t0 - dur * .5) / (dur * .5 + .25))).toFixed(3)); } });
  }

  function checkBadge(pg, cx, cy, r, t0) {
    const g = sv('g', {}, pg.over);
    sv('circle', { cx, cy, r, fill: YEL, stroke: INK, 'stroke-width': 5 }, g);
    reg({ t0, t1: t0 + .2, pen: false, update(t) {
      const f = clamp((t - t0) / .2);
      g.style.visibility = f > 0 ? 'visible' : 'hidden';
      g.setAttribute('transform', `translate(${cx} ${cy}) scale(${lerp(.2, 1, easeOutBack(f))}) translate(${-cx} ${-cy})`);
    } });
    const s = r / 44;
    doodle(pg, smooth([[cx - 20 * s, cy + 1 * s], [cx - 6 * s, cy + 15 * s], [cx + 6 * s, cy - 2 * s], [cx + 21 * s, cy - 18 * s]]),
      { t0: t0 + .14, dur: .22, width: 7 });
  }

  function xMark(pg, cx, cy, s, t0, dur) {
    doodle(pg, smooth([[cx + s, cy - s], [cx + .1 * s, cy - .05 * s], [cx - s * .95, cy + s * 1.02]]), { t0, dur: dur * .45, width: 7.5 });
    doodle(pg, smooth([[cx - s, cy - s * .95], [cx, cy + .04 * s], [cx + s * 1.02, cy + s]]), { t0: t0 + dur * .55, dur: dur * .45, width: 7.5 });
  }

  function sparkle(pg, cx, cy, r, t0, dur) {
    const k = .2, P = [[0, -1], [k, -k], [1, 0], [k, k], [0, 1], [-k, k], [-1, 0], [-k, -k], [0, -1]];
    doodle(pg, 'M' + P.map(p => (cx + p[0] * r).toFixed(1) + ' ' + (cy + p[1] * r).toFixed(1)).join('L'), { t0, dur, width: 5 });
  }

  const tw = id => TM[id].w, th = id => TM[id].h;

  /* ================= SCENES ================= */
  // Voice segments (video time): S1 .59-3.07 | S2 3.53-6.36 | S3 6.82-9.65 | S4 10.18-13.30 | S5 13.90-16.06
  {
    const p = pages[0];
    const gw = id => tw(id) - 52;
    highlight(p, 540, 374, tw('s1_tag') - 40, 46, .08, .35);
    ink(p, 's1_tag', { cx: 540, cy: 360, t0: .12, dur: .6 });
    const total = gw('s1_num') + gw('s1_title') + 34, Rg = 540 + total / 2;
    const numCx = Rg - gw('s1_num') / 2, titCx = Rg - gw('s1_num') - 34 - gw('s1_title') / 2;
    ink(p, 's1_num', { cx: numCx, cy: 572, t0: .45, dur: .4 });
    ink(p, 's1_title', { cx: titCx, cy: 588, t0: .8, dur: .85 });
    circleScribble(p, numCx + 2, 578, 80, 102, 1.65, .45, 4);
    sparkle(p, 118, 492, 24, 2.55, .2);
    sparkle(p, 160, 440, 13, 2.7, .14);
    ink(p, 's1_sub', { cx: 540, cy: 790, t0: 1.45, dur: .8 });
    underline(p, 540 - tw('s1_sub') / 2 + 40, 540 + tw('s1_sub') / 2 - 40, 838, 2.2, .3, { waves: 3, amp: 4 });
    ink(p, 'hero', { cx: 556, cy: 1285, w: 800, t0: .55, dur: 1.75, ct0: 2.0, cdur: .55, pen: false });
    arrow(p, [150, 850], [212, 1045], -.35, 2.45, .45, 2);
  }
  {
    const p = pages[1];
    sticky(p, 790, 330, 340, 124, -4, 3.5);
    ink(p, 's2_label', { cx: 790, cy: 332, rot: -4, t0: 3.62, dur: .5 });
    ink(p, 's2_h1', { cx: 540, cy: 505, t0: 3.78, dur: .62 });
    ink(p, 's2_h2', { cx: 540, cy: 650, t0: 4.36, dur: .7 });
    underline(p, 540 - tw('s2_h2') / 2 + 50, 540 + tw('s2_h2') / 2 - 50, 722, 5.02, .3);
    ink(p, 'globe', { cx: 540, cy: 1065, w: 590, t0: 3.95, dur: 1.3, ct0: 5.0, cdur: .5, pen: false });
    arrow(p, [860, 1190], [905, 1415], -.45, 5.25, .4, 7);
    box(p, 96, 1440, 888, 176, 5.35, .45, 5);
    checkBadge(p, 905, 1528, 42, 5.6);
    ink(p, 's2_sol', { cx: 478, cy: 1528, t0: 5.68, dur: .62 });
  }
  {
    const p = pages[2];
    sticky(p, 790, 330, 350, 124, 3, 6.8);
    ink(p, 's3_label', { cx: 790, cy: 332, rot: 3, t0: 6.92, dur: .5 });
    ink(p, 's3_h1', { cx: 540, cy: 505, t0: 7.05, dur: .55 });
    ink(p, 's3_h2', { cx: 540, cy: 650, t0: 7.55, dur: .55 });
    underline(p, 540 - tw('s3_h2') / 2 + 40, 540 + tw('s3_h2') / 2 - 40, 722, 8.08, .26);
    ink(p, 'tag', { cx: 772, cy: 1010, w: 420, t0: 7.2, dur: .95, ct0: 8.05, cdur: .4, pen: false });
    ink(p, 'store', { cx: 302, cy: 1010, w: 430, t0: 7.6, dur: 1.05, ct0: 8.55, cdur: .4, pen: false });
    arrow(p, [640, 818], [420, 812], .42, 8.2, .42, 9);
    xMark(p, 772, 1268, 26, 8.55, .28);
    checkBadge(p, 302, 1270, 36, 8.85);
    box(p, 96, 1395, 888, 176, 8.7, .4, 8);
    checkBadge(p, 905, 1483, 42, 8.92);
    ink(p, 's3_sol', { cx: 478, cy: 1483, t0: 8.98, dur: .62 });
  }
  {
    const p = pages[3];
    sticky(p, 790, 330, 350, 124, -3, 10.1);
    ink(p, 's4_label', { cx: 790, cy: 332, rot: -3, t0: 10.22, dur: .5 });
    ink(p, 's4_h1', { cx: 540, cy: 505, t0: 10.38, dur: .82 });
    ink(p, 's4_h2', { cx: 540, cy: 640, t0: 11.2, dur: .72 });
    underline(p, 540 - tw('s4_h2') / 2 + 40, 540 - tw('s4_h2') / 2 + 330, 690, 11.95, .28, { waves: 3 });
    ink(p, 'lock', { cx: 540, cy: 1040, w: 560, t0: 10.55, dur: 1.35, ct0: 11.75, cdur: .5, pen: false });
    arrow(p, [835, 1210], [895, 1420], -.42, 12.05, .38, 4);
    box(p, 96, 1440, 888, 176, 12.15, .42, 12);
    checkBadge(p, 905, 1528, 42, 12.4);
    ink(p, 's4_sol', { cx: 478, cy: 1528, t0: 12.46, dur: .72 });
  }
  {
    const p = pages[4];
    ink(p, 'outro', { cx: 540, cy: 700, w: 600, t0: 13.9, dur: 1.3, ct0: 14.95, cdur: .5, pen: false });
    ink(p, 's5_h1', { cx: 540, cy: 1130, t0: 14.0, dur: .7 });
    highlight(p, 540, 1307, tw('s5_h2') - 70, 58, 14.72, .35);
    ink(p, 's5_h2', { cx: 540, cy: 1290, t0: 14.78, dur: .95 });
    sparkle(p, 175, 1095, 28, 15.35, .22);
    sparkle(p, 905, 1155, 22, 15.5, .2);
    sparkle(p, 935, 1095, 13, 15.66, .14);
    ink(p, 's5_cta', { cx: 540, cy: 1490, t0: 15.75, dur: .7 });
    underline(p, 540 - tw('s5_cta') / 2 + 40, 540 + tw('s5_cta') / 2 - 40, 1540, 16.42, .3, { waves: 5, amp: 6, color: INK, width: 5 });
  }

  /* ---------------- page flips ---------------- */
  const flips = [[3.08, 3.52], [6.36, 6.8], [9.66, 10.1], [13.34, 13.84]];
  function updateFlips(t) {
    flips.forEach(([a0, a1], i) => {
      const pg = pages[i], nx = pages[i + 1];
      const f = clamp((t - a0) / (a1 - a0));
      const a = 180 * easeIO(f), rad = a * Math.PI / 180;
      pg.page.style.transform = f > 0 ? `rotateX(${a.toFixed(2)}deg)` : 'none';
      pg.page.style.visibility = f >= 1 ? 'hidden' : 'visible';
      pg.lift.style.opacity = f > 0 && f < 1 ? (.9 * Math.sin(rad)).toFixed(3) : 0;
      const active = f > 0 && f < 1;
      if (active) {
        const yb = 186 + (PAGE.y + PAGE.h - 186) * Math.max(0, Math.cos(rad));
        nx.cast.style.height = Math.max(0, yb - PAGE.y + 90) + 'px';
        nx.cast.style.opacity = (a < 90 ? Math.sin(rad) : Math.max(0, (150 - a) / 60) * 1).toFixed(3);
      } else nx.cast.style.opacity = 0;
    });
  }

  /* ---------------- pencil follow ---------------- */
  const penItems = items.filter(i => i.pen);
  function updatePencil(t) {
    let best = null;
    for (const it of penItems) if (it.t0 <= t + .12 && (!best || it.t0 > best.t0)) best = it;
    let op = 0, pos = [-500, -500];
    if (best) {
      if (t < best.t0) { op = 1 - (best.t0 - t) / .12; pos = best.penAt(best.t0); }
      else if (t <= best.t1) { op = 1; pos = best.penAt(t); }
      else { op = 1 - (t - best.t1) / .18; pos = best.penAt(best.t1); }
      // between closely chained items keep the pen visible
      for (const it of penItems) if (it !== best && t >= it.t0 && t <= it.t1) op = 1;
    }
    op = clamp(op);
    const wob = Math.sin(t * 23) * 1.6 + Math.sin(t * 9.7) * 1.2;
    pencil.style.opacity = op.toFixed(3);
    pencil.style.transform = `translate(${(pos[0] - 60).toFixed(1)}px, ${(pos[1] - 60).toFixed(1)}px)`;
    pg_.setAttribute('transform', `rotate(${(48 + wob).toFixed(2)})`);
  }

  window.DURATION = DURATION;
  window.setTime = function (t) {
    for (const it of items) it.update(t);
    updateFlips(t);
    updatePencil(t);
  };
  window.setTime(0);
})();
