/* KLOVA — "phone UI as stage" collage. Everything is a pure function of time: window.seek(t). */
'use strict';
const DUR = 20.8;
const C = {rose: '#BD9484', roseD: '#9E6E5E', roseL: '#E8D5CB', cream: '#FFF3E4', paper: '#F5EAE1', white: '#FFFBF7', esp: '#2A1711'};

// ---------- math ----------
const cl = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const P = (t, t0, d) => cl((t - t0) / d);
const lerp = (a, b, k) => a + (b - a) * k;
const eOut = x => 1 - Math.pow(1 - x, 3);
const eOut5 = x => 1 - Math.pow(1 - x, 5);
const eIO = x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const eBack = (x, s = 1.7) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2);
const spring = x => (x >= 1 ? 1 : 1 - Math.exp(-6.5 * x) * Math.cos(11 * x));

// ---------- dom ----------
const stage = document.getElementById('stage');
function mk(tag, cls, parent, html, style) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  if (style) e.style.cssText = style;
  (parent || stage).appendChild(e);
  return e;
}
function tf(e, o = {}) {
  const {x = 0, y = 0, s = 1, sx, sy, r = 0} = o;
  e.style.transform = `translate(${x}px,${y}px) rotate(${r}deg) scale(${sx ?? s},${sy ?? s})`;
  if (o.o !== undefined) e.style.opacity = o.o;
}
const show = (e, v) => { e.style.display = v ? '' : 'none'; };

// ---------- sfx cue list (read by the renderer) ----------
const SFX = [];
const sfx = (t, name, gain = 1, pitch = 1) => SFX.push({t: +t.toFixed(3), name, gain, pitch});

// ---------- icons ----------
const I = {
  chevR: '<svg viewBox="0 0 24 24" width="100%" height="100%"><path d="M9 4.5l7.5 7.5L9 19.5" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  phone: '<svg viewBox="0 0 24 24" width="52" height="52"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 006.6 6.6l2.2-2.2a1 1 0 011-.25c1.1.37 2.3.57 3.6.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.57a1 1 0 01-.25 1z"/></svg>',
  video: '<svg viewBox="0 0 24 24" width="56" height="56"><rect x="1.5" y="6" width="14" height="12" rx="3.2" fill="currentColor"/><path d="M16.5 10.2l6-3.6v10.8l-6-3.6z" fill="currentColor"/></svg>',
  up: '<svg viewBox="0 0 24 24" width="54" height="54"><path d="M12 19.5V5M5.5 11.5L12 5l6.5 6.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  mic: '<svg viewBox="0 0 24 24" width="50" height="50"><rect x="8.5" y="3" width="7" height="12" rx="3.5" fill="currentColor"/><path d="M5.5 11.5a6.5 6.5 0 0013 0M12 18v3" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
  plus: '<svg viewBox="0 0 24 24" width="100%" height="100%"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 7.5v9M7.5 12h9" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
  bubble: '<svg viewBox="0 0 24 24" width="62" height="62"><path fill="currentColor" d="M12 3.5c5.2 0 9.3 3.5 9.3 7.9s-4.1 7.9-9.3 7.9c-1 0-2-.13-2.95-.4L4 20.8l1.25-4.1C3.7 15.3 2.7 13.4 2.7 11.4 2.7 7 6.8 3.5 12 3.5z"/></svg>',
  wallet: '<svg viewBox="0 0 24 24" width="60" height="60"><rect x="2.5" y="6" width="19" height="13.5" rx="3" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M5 6l10.5-3 1 3" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/><circle cx="17" cy="12.8" r="1.6" fill="currentColor"/></svg>',
  check: '<svg viewBox="0 0 24 24" width="64" height="64"><path d="M5 12.8l4.4 4.4L19.2 7.4" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  play: '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M7 4.5v15l12.5-7.5z" fill="currentColor"/></svg>',
  play2: '<svg viewBox="0 0 24 24" width="40" height="40"><path d="M7 4.5v15l12.5-7.5z" fill="currentColor"/></svg>',
  link: '<svg viewBox="0 0 24 24" width="38" height="38"><path d="M10 14a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1M14 10a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
  heart: '<path d="M50 88C18 66 6 50 6 32 6 18 17 8 30 8c9 0 15.5 4.6 20 12 4.5-7.4 11-12 20-12 13 0 24 10 24 24 0 18-12 34-44 56z"/>',
  comment: '<svg viewBox="0 0 24 24" width="72" height="72"><path d="M21 11.5a8.5 8.5 0 01-12.6 7.4L3 20.5l1.6-5A8.5 8.5 0 1121 11.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  share: '<svg viewBox="0 0 24 24" width="70" height="70"><path d="M21.5 3L10.5 13.5M21.5 3l-7 18.5-4-8-8.5-4z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  save: '<svg viewBox="0 0 24 24" width="70" height="70"><path d="M6 3h12v18l-6-4.5L6 21z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  torch: '<svg viewBox="0 0 24 24" width="56" height="56"><path d="M8 2.5h8v4l-2 3.5v11.5h-4V10L8 6.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  cam: '<svg viewBox="0 0 24 24" width="58" height="58"><path d="M3 8a2 2 0 012-2h2.5l1.5-2h6l1.5 2H19a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="13" r="3.8" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
  x: '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
};
const heartSvg = (w, fill, stroke, sw) => `<svg viewBox="0 0 100 100" width="${w}" height="${w}"><path d="M50 88C18 66 6 50 6 32 6 18 17 8 30 8c9 0 15.5 4.6 20 12 4.5-7.4 11-12 20-12 13 0 24 10 24 24 0 18-12 34-44 56z" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/></svg>`;

function ncard(parent, {icon, head, time, text, thumb, thumbBg, play, media}) {
  const e = mk('div', 'ncard', parent, `<div class="nrow">
    <div class="nicon">${icon}</div>
    <div class="nbody"><div class="nhead"><b>${head}</b><span>${time}</span></div><div class="ntext">${text}</div></div>
    ${thumb ? `<div class="nthumb" style="background:${thumbBg || C.rose}">${thumb}${play ? `<div class="play">${I.play}</div>` : ''}</div>` : ''}</div>
    ${media ? `<div class="nmedia">${media}<div class="play">${I.play2}</div><div class="pbar"><i></i></div></div>` : ''}`);
  return e;
}

// =====================================================================
// LAYERS
// =====================================================================
// ---------- lock screen ----------
const lock = mk('div', 'layer', null, '', 'z-index:1');
lock.id = 'lock';
const lockWall = mk('img', 'wall', lock); lockWall.src = 'assets/wall.jpg';
mk('div', 'shade', lock);
mk('div', 'date', lock, 'الأحد، ٢٧ سبتمبر');
const clockEl = mk('div', 'clock', lock, '10:08');
mk('div', 'lbtn', lock, I.torch, 'left:110px');
mk('div', 'lbtn', lock, I.cam, 'left:850px');
mk('div', 'homebar', lock, '', 'color:#FFF3E4');
const N1 = ncard(lock, {icon: I.bubble, head: 'كلوفا ☕', time: 'الآن', text: 'إذا تسوي قهوتك في البيت؟',
  thumb: '<img src="assets/latte.png" style="object-fit:contain;padding:10px">'});
const N2 = ncard(lock, {icon: I.bubble, head: 'كلوفا ☕', time: 'الآن', text: 'هذا الفيديو لك 👀',
  thumb: '<img src="assets/pourover.jpg">', play: true, media: '<img src="assets/pourover.jpg">'});
const N2thumb = N2.querySelector('.nthumb'), N2img = N2.querySelector('.nmedia img'), N2bar = N2.querySelector('.nmedia .pbar i');
const LOCK_TOP = 640, NSTEP = 236, NEXP = 520, EXP_T = 2.14;

// ---------- chat ----------
const chat = mk('div', 'layer', null, '', 'z-index:2');
chat.id = 'chat';
mk('div', 'pattern', chat, `<svg width="1080" height="1920"><defs><pattern id="beans" width="220" height="220" patternUnits="userSpaceOnUse">
  <g fill="#E3CFC4"><ellipse cx="40" cy="44" rx="15" ry="21" transform="rotate(30 40 44)"/><ellipse cx="150" cy="120" rx="13" ry="18" transform="rotate(-25 150 120)"/><ellipse cx="80" cy="180" rx="11" ry="15" transform="rotate(60 80 180)"/></g>
  <g stroke="#F5EAE1" stroke-width="3.5" fill="none" stroke-linecap="round"><path d="M33 30c10 8-2 20 12 28" transform="rotate(30 40 44)"/><path d="M146 107c8 7-3 17 9 25" transform="rotate(-25 150 120)"/><path d="M76 168c6 6-2 13 7 19" transform="rotate(60 80 180)"/></g>
  <circle cx="190" cy="30" r="5" fill="#E3CFC4"/><circle cx="120" cy="200" r="4" fill="#E3CFC4"/></pattern></defs><rect width="1080" height="1920" fill="url(#beans)"/></svg>`);
const msgLayer = mk('div', 'abs', chat, '', 'width:1080px;height:1920px');
const chead = mk('div', '', chat, `
  <div class="back">${I.chevR}</div>
  <div class="av"><img src="assets/logo_espresso.png"></div>
  <div class="who"><b>كلوفا ☕</b><span id="cstat">متصل الآن</span></div>
  <div class="acts">${I.video}${I.phone}</div>`);
chead.id = 'chead';
const cstat = chead.querySelector('#cstat');
mk('div', '', chat).id = 'inbg';
const inbar = mk('div', '', chat, `<div class="send">${I.mic}</div><div class="field"><span class="txt"></span></div><div class="plus">${I.plus}</div>`);
inbar.id = 'inbar';
const sendBtn = inbar.querySelector('.send'), fieldTxt = inbar.querySelector('.txt');
const kbd = mk('div', '', chat, '<div class="sug"><span>القهوة</span><span>مكينتي</span><span>ممتازة</span></div>');
kbd.id = 'kbd';
mk('div', 'homebar', kbd, '', 'color:#2A1711;top:608px');

// keyboard keys
const KEYS = {};
const ROWS = ['ضصثقفغعهخحج', 'شسيبلاتنمكط', 'ذءؤرىةوزظد'];
const KW = 88.4, KG = 8, KX0 = 12;
ROWS.forEach((row, ri) => {
  const chars = [...row];
  const n = ri === 2 ? chars.length + 1 : chars.length;
  const total = n * KW + (n - 1) * KG;
  const x0 = (1080 - total) / 2;
  chars.forEach((ch, ci) => {
    const x = 1080 - x0 - (ci + 1) * KW - ci * KG; // RTL: first char at the right
    const k = mk('div', 'key', kbd, ch, `left:${x}px;top:${84 + ri * 120}px;width:${KW}px`);
    KEYS[ch] = k;
  });
  if (ri === 2) mk('div', 'key fn', kbd, '⌫', `left:${x0}px;top:${84 + ri * 120}px;width:${KW}px;font-family:sans-serif`);
});
mk('div', 'key fn', kbd, '١٢٣', `left:${KX0}px;top:444px;width:150px`);
KEYS['😎'] = mk('div', 'key fn', kbd, '😊', `left:${KX0 + 160}px;top:444px;width:120px;font-size:46px`);
KEYS[' '] = mk('div', 'key', kbd, 'مسافة', `left:${KX0 + 290}px;top:444px;width:476px;font-size:36px;color:#9E6E5E`);
mk('div', 'key fn', kbd, '↵', `left:${KX0 + 776}px;top:444px;width:280px;font-family:sans-serif`);
const kpop = mk('div', 'kpop', kbd, '', 'display:none');

// messages
const IN = 'in', OUT = 'out';
const MSGS = [
  {t: 0, side: IN, type: 'chip', html: 'اليوم', silent: true},
  {t: 0, side: IN, type: 'text', html: 'إذا تسوي قهوتك في البيت؟', silent: true},
  {t: 1.88, side: IN, type: 'text', html: 'هذا الفيديو لك 👀', silent: true},
  {t: 1.9, side: IN, type: 'img', key: 'pour', clip: '0:15', silent: true, inner: `<img src="assets/pourover.jpg" style="object-position:50% 45%">`},
  {t: 3.32, dots: 3.0, side: IN, type: 'text', html: 'حنا كلوفا 👋'},
  {t: 4.30, dots: 3.86, side: IN, type: 'text', html: 'متجر متخصص في محاصيل القهوة'},
  {t: 4.64, side: IN, type: 'img', key: 'sack', clip: '0:09', inner: `<img class="cut" src="assets/sack.png">`, bg: C.rose},
  {t: 6.08, side: OUT, type: 'text', html: 'مكينتي ممتازة 😎'},
  {t: 6.34, side: IN, type: 'text', html: 'والفرق غالباً مو في المكينة'},
  {t: 6.86, side: IN, type: 'img', key: 'machine', clip: '0:06', bg: C.roseLL,
    inner: `<img class="cut" src="assets/espresso_ht.png">
      <svg class="xst" viewBox="0 0 100 100"><g stroke-linecap="round"><path d="M18 18L82 82M82 18L18 82" stroke="#FFF3E4" stroke-width="24"/><path d="M18 18L82 82M82 18L18 82" stroke="#9E6E5E" stroke-width="14"/></g></svg>`},
  {t: 8.42, side: IN, type: 'text', html: 'الفرق في <span class="hl">المحصول</span> نفسه'},
  {t: 8.72, side: IN, type: 'img', key: 'farmer', clip: '0:12', inner: `<img src="assets/farmer.jpg" style="object-position:55% 60%">`},
  {t: 18.84, dots: 18.52, side: IN, type: 'text', html: 'اختار محصولك من الرابط بالبايو 👆'},
  {t: 19.22, side: IN, type: 'link'},
];
MSGS.forEach(m => {
  if (m.type === 'text') m.el = mk('div', `msg ${m.side}`, msgLayer, m.html);
  else if (m.type === 'chip') m.el = mk('div', 'msg chip', msgLayer, m.html);
  else if (m.type === 'img') {
    m.el = mk('div', `msg ${m.side} media`, msgLayer, `<div class="imw" style="background:${m.bg || C.esp}">${m.inner}
      <div class="badge">${I.play}<span>${m.clip}</span></div><div class="pbar"><i></i></div></div>`);
    m.img = m.el.querySelector('.imw > img');
    m.bar = m.el.querySelector('.pbar i');
    m.x = m.el.querySelector('.xst');
  } else {
    m.el = mk('div', `msg ${m.side} media`, msgLayer, `<div class="lkimg"><img src="assets/bag_klova.png"></div>
      <div class="lkt"><b>كلوفا | محاصيل القهوة</b><span>${I.link} الرابط في البايو</span></div>`);
    m.img = m.el.querySelector('.lkimg img');
  }
  if (m.dots !== undefined) m.dotEl = mk('div', 'msg in dots', msgLayer, '<i></i><i></i><i></i>');
  m.hl = m.el.querySelector('.hl');
});
const MSG_BOTTOM = 1098, MSG_GAP = 20, DOTS_H = 112;
const MI = key => MSGS.findIndex(m => m.key === key || m.type === key);

// typing
const TYPE = [...'مكينتي ممتازة 😎'];
const TYPE_T0 = 5.0, TYPE_DT = 0.064, SEND_T = 6.04;
TYPE.forEach((ch, i) => sfx(TYPE_T0 + i * TYPE_DT, 'key', 0.9, 0.9 + ((i * 7) % 5) * 0.06));

// ---------- viewer ----------
const viewer = mk('div', 'layer', null, '', 'z-index:3');
viewer.id = 'viewer';
const vbg = mk('div', 'vbg', viewer);
const vtop = mk('div', 'vtop', viewer, `<div style="width:56px;height:56px">${I.chevR}</div><div><b>كلوفا</b></div><span>· اليوم</span>`);
const vimg = mk('div', 'vimg', viewer, '<img src="assets/farmer.jpg" style="object-position:55% 60%">');
const vimgIn = vimg.querySelector('img');
const vctl = mk('div', 'vctl', viewer, `<div class="bar"><i></i></div><div class="row"><span>0:04</span><span>${I.play2}</span><span>0:12</span></div>`);
const vbar = vctl.querySelector('.bar i');
const VRECT = {x: 0, y: 555, w: 1080, h: 810};

// screenshot thumbnail (a frozen copy of the viewer)
const shot = mk('div', 'layer', null, `<div class="vbg"></div>
  <div class="vtop"><div style="width:56px;height:56px">${I.chevR}</div><div><b>كلوفا</b></div><span>· اليوم</span></div>
  <div class="vimg" style="left:0;top:555px;width:1080px;height:810px"><img src="assets/farmer.jpg" style="object-position:55% 60%"></div>`);
shot.id = 'shot';
const shotImg = shot.querySelector('.vimg img');
const flash = mk('div', '', null); flash.id = 'flash';
const SHOT = {x: 60, y: 850, s: 0.3};

// ---------- album ----------
const album = mk('div', 'layer', null, '', 'z-index:4');
album.id = 'album';
const grid = mk('div', 'abs', album, '', 'width:1080px;height:1920px');
const ahead = mk('div', '', album, `<div class="bk"><div style="width:44px;height:44px">${I.chevR}</div>الألبومات</div>
  <h1>محاصيلنا</h1><div class="sub">من أكثر من بلد ✈️</div>`);
ahead.id = 'ahead';
const asub = ahead.querySelector('.sub');
const globe = mk('img', 'globe', album); globe.src = 'assets/globe_ht.png';
const TILES = [
  {name: 'اليمن', flag: '🇾🇪', html: '<img src="assets/pourover.jpg" style="object-position:50% 70%">'},
  {name: 'رواندا', flag: '🇷🇼', bg: C.esp, html: '<img class="cut" src="assets/bag_klova.png">'},
  {name: 'إثيوبيا', flag: '🇪🇹', html: '<img src="assets/farmer.jpg" style="object-position:62% 70%">'},
  {name: 'كينيا', flag: '🇰🇪', bg: C.roseL, html: '<img class="cut" src="assets/latte.png">'},
  {name: 'البرازيل', flag: '🇧🇷', bg: C.rose, html: '<img class="cut" src="assets/sack.png">'},
  {name: 'كولومبيا', flag: '🇨🇴', html: '<img src="assets/beans.jpg">'},
  {name: 'غواتيمالا', flag: '🇬🇹', bg: C.rose, html: '<img class="cut" src="assets/takeaway_ht.png">'},
  {name: 'بنما', flag: '🇵🇦', html: '<img src="assets/farmer.jpg" style="object-position:20% 30%">'},
];
const TW = 462, TX = [566, 52], TY0 = 444, TSTEP = 500;
TILES.forEach((d, i) => {
  d.x = TX[i % 2]; d.y = TY0 + Math.floor(i / 2) * TSTEP;
  d.el = mk('div', 'tile', grid, `${d.html}<div class="tlabel"><span class="flag">${d.flag}</span>${d.name}</div>`,
    `background:${d.bg || C.esp}`);
  d.img = d.el.querySelector('img');
  d.t = 10.7 + i * 0.13;
  sfx(d.t, 'tick', 0.55, 1 + i * 0.06);
});
const SCROLL = 380, SCROLL_T = 12.05;
const FLAVS = [
  {tile: 2, img: 'strawberry', label: 'توتي', t: 13.2, dx: -40, dy: -70, r: -10},
  {tile: 3, img: 'orange', label: 'حمضي', t: 13.56, dx: 250, dy: -60, r: 8},
  {tile: 4, img: 'chocolate', label: 'شوكولاتي', t: 13.92, dx: -30, dy: -40, r: -6},
];
FLAVS.forEach(f => {
  f.el = mk('div', 'flav', album, `<img src="assets/${f.img}.png"><div class="fp">${f.label}</div>`);
  sfx(f.t, 'sticker', 0.9);
});

// ---------- notification centre ----------
const nc = mk('div', 'layer', null, '', 'z-index:5');
nc.id = 'nc';
const ncbg = mk('div', 'ncbg', nc);
mk('h2', '', nc, 'الإشعارات');
const clr = mk('div', 'clr', nc, `${I.x}مسح الكل`);
const PAYS = [
  {t: 14.62, amt: '٢٢', day: 'الأحد'}, {t: 14.98, amt: '١٩', day: 'الاثنين'}, {t: 15.34, amt: '٢٥', day: 'الثلاثاء'},
  {t: 15.62, amt: '٢١', day: 'الأربعاء'}, {t: 15.92, amt: '٢٤', day: 'الخميس'},
];
PAYS.forEach((p, i) => {
  p.el = ncard(nc, {icon: I.wallet, head: 'المحفظة', time: p.day, text: `خصم ${p.amt} ر.س · كوفي ☕`,
    thumb: '<img src="assets/takeaway_ht.png" style="object-fit:contain;padding:12px">', thumbBg: C.rose});
  sfx(p.t, 'coin', 0.75, 1 + i * 0.07);
});
const NC_TOP = 340;

// ---------- post (favourite) ----------
const post = mk('div', 'layer', null, '', 'z-index:6');
post.id = 'post';
mk('div', '', post, `<div class="pav">☕</div><div><b>قهوتي في البيت</b><span>المفضلة · الآن</span></div>`).id = 'phead';
const pcard = mk('div', '', post, '<img src="assets/pourover.jpg">');
pcard.id = 'pcard';
const pimg = pcard.querySelector('img');
const bigHeart = mk('div', '', post, `<svg viewBox="0 0 100 100" width="360" height="360"><defs><clipPath id="hc"><rect id="hfill" x="0" y="100" width="100" height="100"/></clipPath>
  <linearGradient id="hg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#C99C8B"/><stop offset="1" stop-color="#9E6E5E"/></linearGradient></defs>
  <path d="${I.heart.match(/d="([^"]+)"/)[1]}" fill="rgba(42,23,17,.25)"/>
  <path d="${I.heart.match(/d="([^"]+)"/)[1]}" fill="url(#hg)" clip-path="url(#hc)"/>
  <path d="${I.heart.match(/d="([^"]+)"/)[1]}" fill="none" stroke="#FFF3E4" stroke-width="5.5" stroke-linejoin="round"/></svg>`);
bigHeart.id = 'bigheart';
const hfill = bigHeart.querySelector('#hfill');
const pacts = mk('div', '', post, `<div class="ph" style="width:76px;height:76px"></div>${I.comment}${I.share}<div class="sp"></div>${I.save}`);
pacts.id = 'pacts';
const pheart = pacts.querySelector('.ph');
const PARTS = [];
for (let i = 0; i < 12; i++) {
  const a = (i / 12) * Math.PI * 2 + 0.2;
  const e = mk('div', 'part', post, i % 2 ? heartSvg(60, C.cream, C.roseD, 6) : heartSvg(60, C.rose, C.cream, 6));
  PARTS.push({e, a, d: 250 + (i % 3) * 60});
}

// ---------- order notification ----------
const order = mk('div', 'layer', null, '', 'z-index:7;background:transparent;pointer-events:none');
const ORD = ncard(order, {icon: I.check, head: 'كلوفا ☕', time: 'الآن', text: 'تم الطلب · محصولك في الطريق',
  thumb: '<img src="assets/bag_klova.png" style="object-fit:contain;padding:10px 0 0">', thumbBg: C.rose});
const ORD_Y = 236;
const SPK = [];
for (let i = 0; i < 10; i++) {
  const col = i % 2 ? C.rose : C.cream;
  const e = mk('div', 'spk', order, `<svg viewBox="0 0 100 100" width="92" height="92"><path d="M50 4C54 38 62 46 96 50 62 54 54 62 50 96 46 62 38 54 4 50 38 46 46 38 50 4Z" fill="${col}" stroke="#9E6E5E" stroke-width="2"/></svg>`);
  SPK.push({e, a: Math.PI * (1.02 + 0.96 * i / 9), d: 60 + (i % 3) * 40});
}

// ---------- status bar, touches, grain ----------
const status = mk('div', '', null, `<span>10:08</span><span class="ic">
  <svg width="46" height="30" viewBox="0 0 46 30"><rect x="0" y="20" width="8" height="10" rx="2" fill="currentColor"/><rect x="12" y="14" width="8" height="16" rx="2" fill="currentColor"/><rect x="24" y="7" width="8" height="23" rx="2" fill="currentColor"/><rect x="36" y="0" width="8" height="30" rx="2" fill="currentColor"/></svg>
  <svg width="42" height="32" viewBox="0 0 24 18"><path d="M12 17l3.2-3.8a4.8 4.8 0 00-6.4 0zM5.3 9.6a10 10 0 0113.4 0l2-2.4a13.2 13.2 0 00-17.4 0zM1.2 4.8a16.2 16.2 0 0121.6 0l.9-1.1A17.8 17.8 0 00.3 3.7z" fill="currentColor"/></svg>
  <svg width="66" height="32" viewBox="0 0 66 32"><rect x="1.5" y="1.5" width="56" height="29" rx="8" fill="none" stroke="currentColor" stroke-width="3" opacity=".5"/><rect x="6" y="6" width="42" height="20" rx="4.5" fill="currentColor"/><rect x="60" y="11" width="4.5" height="10" rx="2" fill="currentColor" opacity=".5"/></svg></span>`);
status.id = 'status';

const TOUCHES = [
  {t: 2.66, x: 540, y: LOCK_TOP + 214 + 246},
  {t: 6.0, x: 92, y: 1196},
  {t: 9.3, x: 0, y: 0, msg: 'farmer'},
  {t: 10.36, x: SHOT.x + 162, y: SHOT.y + 270},
  {t: 16.14, x: 190, y: 244},
  {t: 17.6, x: 530, y: 800}, {t: 17.76, x: 548, y: 816},
  {t: 19.66, x: 0, y: 0, msg: 'link'},
];
TOUCHES.forEach(tc => { tc.dot = mk('div', 'tdot'); tc.ring = mk('div', 'tring'); sfx(tc.t, 'tap', 0.7); });
const DRAG = {t0: 14.2, t1: 14.52, x: 560, y0: 40, y1: 660};
DRAG.dot = mk('div', 'tdot');
const grain = mk('div', '', null); grain.id = 'grain';

// ---------- other sfx cues ----------
sfx(0.0, 'buzz', 0.8); sfx(0.02, 'notif', 1.0);
sfx(1.88, 'buzz', 0.7); sfx(1.9, 'notif', 0.95, 1.12);
sfx(EXP_T, 'swipe', 0.4, 1.3);
sfx(2.84, 'whoosh', 0.55);
MSGS.forEach(m => {
  if (m.silent) return;
  if (m.side === OUT) sfx(m.t - 0.04, 'send', 0.9);
  else sfx(m.t, m.type === 'text' ? 'pop' : 'popimg', 0.8);
});
sfx(7.72, 'stamp', 0.95);
sfx(8.95, 'marker', 0.5);
sfx(9.36, 'whoosh', 0.5, 1.2);
sfx(9.9, 'shutter', 1.0);
sfx(10.44, 'whoosh', 0.55, 0.9);
sfx(11.8, 'pop', 0.45, 0.8);
sfx(12.0, 'sticker', 0.8, 0.85);
sfx(12.05, 'swipe', 0.35);
sfx(14.24, 'whoosh', 0.6, 0.8);
sfx(16.26, 'swipe', 0.8);
sfx(16.5, 'whoosh', 0.45, 1.1);
sfx(17.82, 'heart', 1.0);
sfx(18.26, 'sparkle', 0.7);
sfx(18.5, 'whoosh', 0.55);
sfx(19.95, 'buzz', 0.6); sfx(19.96, 'success', 1.0); sfx(20.12, 'sparkle', 0.55);

// =====================================================================
// RENDER
// =====================================================================
function chatLayout(t) {
  // Bubbles are stacked from the bottom; each bubble's space grows with its own presence so older ones glide up.
  const items = [];
  for (const m of MSGS) {
    if (m.dots !== undefined) { if (t >= m.dots) items.push(m); } else if (t >= m.t) items.push(m);
  }
  // A new bubble rises from under the input bar while the older ones make room.
  let off = 0;
  const out = [];
  for (let i = items.length - 1; i >= 0; i--) {
    const m = items[i];
    let h, pres;
    if (m.dots !== undefined) {
      pres = eOut(P(t, m.dots, 0.3));
      h = t < m.t ? DOTS_H : lerp(DOTS_H, m.h, eOut(P(t, m.t, 0.28)));
    } else {
      pres = eOut(P(t, m.t, 0.34));
      h = m.h;
    }
    const bottom = MSG_BOTTOM - off + (h + MSG_GAP) * (1 - pres);
    out.push({m, y: bottom - h, h, pres});
    off += (h + MSG_GAP) * pres;
  }
  return out;
}
function msgImgRect(t, key) {
  const m = MSGS[MI(key)];
  const p = chatLayout(t).find(o => o.m === m);
  const x = m.side === IN ? 40 : 940 - m.w;
  return {x: x + 12, y: p.y + 12, w: 620, h: m.type === 'link' ? 300 : 440};
}

function renderLock(t) {
  const vis = t < 3.3;
  show(lock, vis);
  if (!vis) return;
  tf(lockWall, {s: lerp(1.14, 1.0, eOut(P(t, 0, 3.3)))});
  lockWall.style.transformOrigin = '50% 40%';
  tf(clockEl, {y: lerp(-30, 0, eOut(P(t, 0, 0.6))), o: lerp(0.4, 1, P(t, 0, 0.4))});
  const buzz = (t0) => Math.sin((t - t0) * 95) * 9 * Math.max(0, 1 - (t - t0) / 0.4) * (t >= t0 ? 1 : 0);
  const k1 = spring(P(t, -0.12, 0.6)), k2 = spring(P(t, 1.88, 0.6));
  const kx = eIO(P(t, EXP_T, 0.36));
  const y1 = LOCK_TOP + NSTEP * eOut(P(t, 1.88, 0.34)) + NEXP * kx;
  tf(N1, {x: buzz(0), y: y1 + lerp(70, 0, k1), s: lerp(0.86, 1, k1) * (1 - 0.03 * eOut(P(t, 1.88, 0.3))), o: cl(P(t, -0.12, 0.14))});
  const press = t >= 2.62 ? 1 - 0.03 * Math.sin(Math.PI * P(t, 2.62, 0.22)) : 1;
  N2.style.height = `${214 + NEXP * kx}px`;
  N2thumb.style.opacity = 1 - kx;
  tf(N2, {x: buzz(1.88), y: LOCK_TOP + lerp(70, 0, k2), s: lerp(0.86, 1, k2) * press, o: cl(P(t, 1.88, 0.14))});
  tf(N2img, {s: 1.04 + 0.1 * P(t, EXP_T, 1.5)});
  N2bar.style.width = `${(P(t, EXP_T, 3) * 100).toFixed(1)}%`;
}

function renderChat(t) {
  const vis = (t >= 2.8 && t < 9.8) || t >= 18.45;
  show(chat, vis);
  if (!vis) return;
  if (t < 3.3) {
    const k = eIO(P(t, 2.82, 0.4));
    const top = lerp(LOCK_TOP, 0, k), bot = lerp(1920 - LOCK_TOP - 214 - NEXP, 0, k), side = lerp(50, 0, k);
    chat.style.clipPath = `inset(${top}px ${side}px ${bot}px ${side}px round ${lerp(52, 0, k)}px)`;
    tf(chat, {});
  } else if (t >= 18.45) {
    chat.style.clipPath = 'none';
    tf(chat, {x: lerp(1080, 0, eOut(P(t, 18.45, 0.38)))});
  } else { chat.style.clipPath = 'none'; tf(chat, {}); }

  // status line
  const typing = MSGS.some(m => m.dots !== undefined && t >= m.dots && t < m.t);
  cstat.textContent = typing ? 'يكتب…' : 'متصل الآن';

  // bubbles
  MSGS.forEach(m => { show(m.el, false); if (m.dotEl) show(m.dotEl, false); });
  for (const p of chatLayout(t)) {
    const m = p.m;
    if (p.y + p.h < 180) continue;
    if (m.dotEl && t < m.t) {
      show(m.dotEl, true);
      const k = P(t, m.dots, 0.3);
      tf(m.dotEl, {x: 40, y: p.y, s: lerp(0.5, 1, eBack(k)), o: cl(k * 3)});
      m.dotEl.querySelectorAll('i').forEach((d, i) => {
        const ph = (t * 3.2 - i * 0.18) % 1;
        tf(d, {y: -14 * Math.max(0, Math.sin(ph * Math.PI * 2)), o: 0.5 + 0.5 * Math.max(0, Math.sin(ph * Math.PI * 2))});
      });
      continue;
    }
    if (t < m.t) continue;
    show(m.el, true);
    const k = P(t, m.t, 0.38);
    const x = m.type === 'chip' ? (1080 - m.w) / 2 : m.side === IN ? 40 : 940 - m.w;
    tf(m.el, {x, y: p.y, s: lerp(0.7, 1, eBack(k, 1.5)), o: cl(k * 4)});
    if (m.img && m.type === 'img') {
      const age = t - m.t;
      const bob = m.key === 'sack' ? Math.sin(age * 3) * 6 : 0;
      tf(m.img, {y: bob, s: 1.02 + 0.1 * eOut(P(age, 0, 5))});
      m.bar.style.width = `${(P(age, 0, 3.2) * 100).toFixed(2)}%`;
    }
    if (m.type === 'link') tf(m.img, {x: 0, y: Math.sin((t - m.t) * 2.4) * 8});
    if (m.x) {
      const ks = P(t, 7.72, 0.3);
      m.x.style.display = t >= 7.72 ? '' : 'none';
      tf(m.x, {s: lerp(2.3, 1, eOut5(ks)), r: lerp(25, -8, eOut(ks)), o: cl(ks * 5)});
      const shake = t >= 7.72 ? Math.sin((t - 7.72) * 70) * 10 * Math.max(0, 1 - (t - 7.72) / 0.3) : 0;
      tf(m.el, {x: x + shake, y: p.y, s: lerp(0.7, 1, eBack(k, 1.5)), o: cl(k * 4)});
    }
    if (m.hl) m.hl.style.backgroundSize = `${(eOut(P(t, 8.95, 0.35)) * 100).toFixed(1)}% 40%`;
    // hide the farmer image while it is "opened" in the viewer
    if (m.key === 'farmer') m.el.style.visibility = t >= 9.36 && t < 18 ? 'hidden' : 'visible';
  }

  // typing field + keyboard
  let n = 0;
  if (t >= TYPE_T0 && t < SEND_T) n = Math.min(TYPE.length, Math.floor((t - TYPE_T0) / TYPE_DT) + 1);
  const caretOn = (t >= TYPE_T0 && t < SEND_T) || Math.floor(t * 2.4) % 2 === 0;
  fieldTxt.innerHTML = n ? `${TYPE.slice(0, n).join('')}<span class="caret"></span>`
    : `${caretOn ? '<span class="caret"></span>' : ''}<span class="ph">اكتب رسالة…</span>`;
  const hasTxt = n > 0;
  sendBtn.innerHTML = hasTxt ? I.up : I.mic;
  sendBtn.style.background = hasTxt ? C.esp : C.roseL;
  sendBtn.style.color = hasTxt ? C.cream : C.esp;
  tf(sendBtn, {s: 1 - 0.12 * Math.sin(Math.PI * P(t, 5.98, 0.16))});
  Object.values(KEYS).forEach(k => k.classList.remove('on'));
  kpop.style.display = 'none';
  TYPE.forEach((ch, i) => {
    const tp = TYPE_T0 + i * TYPE_DT;
    if (t >= tp && t < tp + 0.085) {
      const k = KEYS[ch];
      k.classList.add('on');
      if (ch !== ' ' && ch !== '😎') {
        kpop.style.display = '';
        kpop.textContent = ch;
        kpop.style.left = `${parseFloat(k.style.left) + KW / 2 - 64}px`;
        kpop.style.top = `${parseFloat(k.style.top) - 150}px`;
      }
    }
  });
}

function renderViewer(t) {
  const vis = t >= 9.34 && t < 10.85;
  show(viewer, vis);
  if (!vis) return;
  const k = eIO(P(t, 9.36, 0.38));
  const r0 = msgImgRect(9.36, 'farmer');
  const x = lerp(r0.x, VRECT.x, k), y = lerp(r0.y, VRECT.y, k), w = lerp(r0.w, VRECT.w, k), h = lerp(r0.h, VRECT.h, k);
  Object.assign(vimg.style, {left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px`, borderRadius: `${lerp(36, 0, k)}px`});
  vbg.style.opacity = k;
  const ui = P(t, 9.6, 0.2);
  vtop.style.opacity = ui; vctl.style.opacity = ui;
  const kb = 1.02 + 0.1 * eOut(P(t, 8.72, 5)) + 0.06 * P(t, 9.36, 1.4);
  tf(vimgIn, {s: kb});
  vbar.style.width = `${(20 + 45 * P(t, 9.36, 1.6)).toFixed(1)}%`;
}

function renderShot(t) {
  flash.style.opacity = t >= 9.9 && t < 10.18 ? (t < 9.94 ? P(t, 9.9, 0.04) : 1 - eOut(P(t, 9.94, 0.24))) : 0;
  const vis = t >= 9.92 && t < 10.78;
  show(shot, vis);
  if (!vis) return;
  const kbAtShot = 1.02 + 0.1 * eOut(P(9.92, 8.72, 5)) + 0.06 * P(9.92, 9.36, 1.4);
  tf(shotImg, {s: kbAtShot});
  const k = eOut5(P(t, 9.98, 0.4));
  const press = 1 - 0.05 * Math.sin(Math.PI * P(t, 10.34, 0.2));
  const s = lerp(1, SHOT.s, k) * press;
  tf(shot, {x: lerp(0, SHOT.x, k) + (1 - press) * 540 * SHOT.s, y: lerp(0, SHOT.y, k) + (1 - press) * 960 * SHOT.s,
    s, r: lerp(0, -4, k), o: 1 - P(t, 10.5, 0.2)});
  shot.style.borderRadius = `${lerp(0, 150, k)}px`;
  shot.style.boxShadow = `0 0 0 ${lerp(0, 34, k)}px #FFF3E4, 0 40px 90px rgba(42,23,17,${0.45 * k})`;
}

function renderAlbum(t) {
  const vis = t >= 10.42 && t < 16.62;
  show(album, vis);
  if (!vis) return;
  const k = eIO(P(t, 10.44, 0.4));
  const l = lerp(SHOT.x, 0, k), tp = lerp(SHOT.y, 0, k);
  const r = lerp(1080 - SHOT.x - 1080 * SHOT.s, 0, k), b = lerp(1920 - SHOT.y - 1920 * SHOT.s, 0, k);
  album.style.clipPath = k < 1 ? `inset(${tp}px ${r}px ${b}px ${l}px round ${lerp(46, 0, k)}px)` : 'none';
  const sc = SCROLL * eIO(P(t, SCROLL_T, 0.85));
  TILES.forEach(d => {
    const kk = P(t, d.t, 0.42);
    tf(d.el, {x: d.x, y: d.y - sc + lerp(40, 0, eOut(kk)), s: lerp(0.6, 1, eBack(kk, 1.4)), o: cl(kk * 4)});
    tf(d.img, {s: 1.0 + 0.08 * P(t, 10.3, 4.3)});
  });
  const ks = P(t, 11.8, 0.35);
  tf(asub, {y: lerp(24, 0, eOut(ks)), o: ks});
  const kg = P(t, 12.0, 0.34);
  tf(globe, {s: lerp(2.0, 1, eOut5(kg)), r: lerp(30, -10, eOut(kg)) + Math.sin(t * 2) * 2, o: cl(kg * 5)});
  FLAVS.forEach(f => {
    const d = TILES[f.tile];
    const kf = P(t, f.t, 0.32);
    show(f.el, t >= f.t);
    tf(f.el, {x: d.x + f.dx, y: d.y - SCROLL + f.dy, s: lerp(1.9, 1, eOut5(kf)) * (1 + 0.02 * Math.sin((t - f.t) * 5)),
      r: lerp(f.r + 25, f.r, eOut(kf)), o: cl(kf * 5)});
  });
}

function renderNC(t) {
  const vis = t >= 14.2 && t < 16.82;
  show(nc, vis);
  if (!vis) return;
  const kin = eOut(P(t, DRAG.t0 + 0.04, 0.4));
  const kout = eIO(P(t, 16.5, 0.3));
  tf(nc, {y: lerp(-1920, 0, kin) - 1920 * kout});
  ncbg.style.background = `rgba(42,23,17,${0.74 + 0.22 * P(t, 16.28, 0.2)})`;
  tf(clr, {s: 1 - 0.08 * Math.sin(Math.PI * P(t, 16.12, 0.2))});
  PAYS.forEach((p, i) => {
    let y = NC_TOP;
    for (let j = i + 1; j < PAYS.length; j++) y += NSTEP * eOut(P(t, PAYS[j].t, 0.3));
    const kk = spring(P(t, p.t, 0.55));
    const out = eIO(P(t, 16.26 + (PAYS.length - 1 - i) * 0.035, 0.3));
    tf(p.el, {x: -1150 * out, y: y + lerp(-50, 0, kk), s: lerp(0.84, 1, kk), o: cl(P(t, p.t, 0.12))});
  });
}

function renderPost(t) {
  const vis = t >= 16.4 && t < 18.95;
  show(post, vis);
  if (!vis) return;
  const kx = eOut(P(t, 18.45, 0.38));
  tf(post, {x: -300 * kx});
  post.style.filter = kx > 0 ? `brightness(${1 - 0.3 * kx})` : 'none';
  tf(pimg, {s: lerp(1.16, 1.02, eOut(P(t, 16.45, 2.4))), y: lerp(-20, 10, P(t, 16.45, 2.4))});
  const kh = P(t, 17.8, 0.55);
  show(bigHeart, t >= 17.8);
  tf(bigHeart, {s: spring(kh) * (1 + 0.06 * Math.sin(Math.PI * P(t, 18.26, 0.2))), r: lerp(-14, 0, eOut(kh))});
  hfill.setAttribute('y', (100 - 100 * eIO(P(t, 17.92, 0.42))).toFixed(2));
  const kp = P(t, 17.86, 0.25);
  pheart.innerHTML = t >= 17.86 ? heartSvg(76, C.rose, C.roseD, 6) : heartSvg(76, 'none', C.esp, 7);
  tf(pheart, {s: t >= 17.86 ? lerp(1.5, 1, eBack(kp)) : 1});
  PARTS.forEach((pp, i) => {
    const k = P(t, 18.26 + (i % 3) * 0.02, 0.6);
    show(pp.e, k > 0 && k < 1);
    const d = pp.d * eOut(k);
    tf(pp.e, {x: 496 + Math.cos(pp.a) * d - 30, y: 800 + Math.sin(pp.a) * d - 30, s: lerp(0.4, 1, eOut(k)) * (1 - 0.5 * k),
      r: (i % 2 ? 1 : -1) * 30 * k, o: 1 - P(k, 0.6, 0.4)});
  });
}

function renderOrder(t) {
  const vis = t >= 19.9;
  show(order, vis);
  if (!vis) return;
  const k = spring(P(t, 19.92, 0.65));
  const buzz = Math.sin((t - 19.95) * 95) * 8 * Math.max(0, 1 - (t - 19.95) / 0.4) * (t >= 19.95 ? 1 : 0);
  tf(ORD, {x: buzz, y: lerp(-260, ORD_Y, k), s: lerp(0.9, 1, k) * (1 + 0.025 * Math.sin(Math.PI * P(t, 20.3, 0.3)))});
  SPK.forEach((sp, i) => {
    const kk = P(t, 20.12 + (i % 3) * 0.03, 0.55);
    show(sp.e, kk > 0 && kk < 1);
    const d = sp.d * eOut(kk);
    tf(sp.e, {x: 540 + Math.cos(sp.a) * (440 + d * 1.2) - 46, y: ORD_Y + 107 + Math.sin(sp.a) * (90 + d * 1.6) - 46,
      s: lerp(0.3, 1, eOut(kk)) * (1 - 0.6 * kk), r: 90 * kk, o: 1 - P(kk, 0.5, 0.5)});
  });
}

function renderStatus(t) {
  let c = C.esp;
  if (t < 2.95 || (t >= 9.5 && t < 10.6) || (t >= 14.45 && t < 16.62)) c = C.cream;
  status.style.color = c;
}

function renderTouch(t) {
  TOUCHES.forEach(tc => {
    const a = tc.t - 0.2, b = tc.t + 0.34;
    const vis = t >= a && t < b;
    show(tc.dot, vis); show(tc.ring, vis);
    if (!vis) return;
    let x = tc.x, y = tc.y;
    if (tc.msg !== undefined) {
      const r = msgImgRect(tc.t, tc.msg);
      x = r.x + r.w / 2; y = r.y + r.h / 2;
    }
    const kin = P(t, a, 0.14), kout = P(t, tc.t + 0.12, 0.22);
    const press = Math.sin(Math.PI * P(t, tc.t - 0.04, 0.14));
    tf(tc.dot, {x, y, s: lerp(1.35, 1, eOut(kin)) * (1 - 0.18 * press), o: 0.95 * eOut(kin) * (1 - kout)});
    const kr = P(t, tc.t, 0.3);
    tf(tc.ring, {x, y, s: lerp(0.8, 2.1, eOut(kr)), o: t >= tc.t ? 0.8 * (1 - kr) : 0});
  });
  const vis = t >= DRAG.t0 - 0.1 && t < DRAG.t1 + 0.2;
  show(DRAG.dot, vis);
  if (vis) {
    const k = eIO(P(t, DRAG.t0, DRAG.t1 - DRAG.t0));
    tf(DRAG.dot, {x: DRAG.x, y: lerp(DRAG.y0, DRAG.y1, k), o: 0.95 * P(t, DRAG.t0 - 0.1, 0.1) * (1 - P(t, DRAG.t1, 0.2))});
  }
}

function renderGrain(t) {
  const f = Math.floor(t * 30);
  grain.style.backgroundPosition = `${(f * 137) % 540}px ${(f * 263) % 960}px`;
}

function render(t) {
  renderLock(t); renderChat(t); renderViewer(t); renderShot(t); renderAlbum(t);
  renderNC(t); renderPost(t); renderOrder(t); renderStatus(t); renderTouch(t); renderGrain(t);
}

window.SFX = SFX;
window.DUR = DUR;
window.seek = t => { render(t); return true; };
(async () => {
  await Promise.all(['400', '500', '600', '700'].map(w => document.fonts.load(`${w} 50px "IBM Plex Sans Arabic"`, 'عربي abc 10:08')));
  await document.fonts.load('50px "Lalezar"', 'محاصيلنا');
  await document.fonts.ready;
  await Promise.all([...document.images].map(im => (im.complete ? 0 : new Promise(r => { im.onload = im.onerror = r; }))));
  // measure bubbles once fonts are in
  MSGS.forEach(m => { m.el.style.display = ''; m.w = m.el.offsetWidth; m.h = m.el.offsetHeight; });
  render(0);
  window.READY = true;
})();
