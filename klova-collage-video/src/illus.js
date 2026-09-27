// Hand-drawn style SVG illustrations for each collage clipping.
// One shared palette so every shot sits in the same colour world.
const P = {
  cream: '#F4EAD7', cream2: '#EADBBE', paper: '#FBF7EE',
  espresso: '#2E1B12', coffee: '#6B3F24', coffee2: '#8A5532',
  caramel: '#B97A45', caramelL: '#D39B62', kraft: '#C08A55', kraftD: '#A06F40',
  terracotta: '#C2502F', terraD: '#9E3B22', terraL: '#E6A58A',
  mustard: '#DFA43A', mustardL: '#EFD29A',
  sage: '#8C9A6B', sageD: '#5F6E48', sageL: '#C9CFAE',
  blush: '#EBC3AE', latte: '#E9D9C0', ink: '#2B211C',
};

function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

function bean(x, y, rx, ry, rot, col, crease = '#24130B', hl = 0.22) {
  return `<g transform="translate(${x} ${y}) rotate(${rot})">
    <ellipse rx="${rx}" ry="${ry}" fill="${col}"/>
    <ellipse cx="${-rx * 0.25}" cy="${-ry * 0.35}" rx="${rx * 0.55}" ry="${ry * 0.35}" fill="#fff" opacity="${hl}"/>
    <path d="M ${-rx * 0.92} ${ry * 0.05} C ${-rx * 0.4} ${-ry * 0.5}, ${rx * 0.3} ${ry * 0.55}, ${rx * 0.92} ${-ry * 0.05}" stroke="${crease}" stroke-width="${ry * 0.2}" fill="none" stroke-linecap="round"/>
  </g>`;
}

function leaf(x, y, len, w, rot, col, vein = 'rgba(255,255,255,0.35)') {
  return `<g transform="translate(${x} ${y}) rotate(${rot})">
    <path d="M0 0 C ${len * 0.3} ${-w}, ${len * 0.75} ${-w}, ${len} 0 C ${len * 0.75} ${w}, ${len * 0.3} ${w}, 0 0 Z" fill="${col}"/>
    <path d="M${len * 0.05} 0 L ${len * 0.92} 0" stroke="${vein}" stroke-width="2.2" fill="none"/>
  </g>`;
}

function woodGrain(x, y, w, h, seed, col = 'rgba(80,45,20,0.18)') {
  const r = rng(seed); let s = '';
  for (let i = 0; i < 9; i++) {
    const yy = y + 10 + r() * (h - 20);
    s += `<path d="M ${x} ${yy} C ${x + w * 0.3} ${yy + (r() - 0.5) * 16}, ${x + w * 0.6} ${yy + (r() - 0.5) * 16}, ${x + w} ${yy + (r() - 0.5) * 10}" stroke="${col}" stroke-width="${1 + r() * 2}" fill="none"/>`;
  }
  return s;
}

function steamPath(x, y, h, phase = 0) {
  return `<path d="M ${x} ${y} C ${x - 18} ${y - h * 0.3}, ${x + 18} ${y - h * 0.55}, ${x} ${y - h * 0.8} S ${x - 10} ${y - h}, ${x - 4} ${y - h * 1.1}" stroke="#fff" stroke-width="7" stroke-linecap="round" fill="none" opacity="0.55"/>`;
}

// ---------- 1. Home brewing (pour over) 600x720 ----------
function homebrew() {
  const W = 600, H = 720;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#EFDFC2"/>
  <!-- window + light -->
  <rect x="40" y="40" width="250" height="300" rx="6" fill="#F8EEDA"/>
  <path d="M165 40 V340 M40 190 H290" stroke="#E4CFA9" stroke-width="10"/>
  <polygon points="40,40 290,40 520,560 200,560" fill="#FFF6E4" opacity="0.35"/>
  <!-- plant -->
  <g>
    ${leaf(95, 420, 110, 26, -115, P.sageD)}${leaf(95, 420, 120, 28, -70, P.sage)}${leaf(95, 420, 95, 24, -150, P.sage)}${leaf(95, 420, 100, 24, -35, P.sageD)}
    <path d="M55 420 H135 L125 520 H65 Z" fill="${P.terracotta}"/>
    <rect x="50" y="410" width="90" height="18" rx="4" fill="${P.terraD}"/>
  </g>
  <!-- counter -->
  <rect x="0" y="520" width="${W}" height="200" fill="${P.caramel}"/>
  <rect x="0" y="520" width="${W}" height="10" fill="${P.caramelL}"/>
  ${woodGrain(0, 535, W, 180, 5)}
  <!-- mug -->
  <g transform="translate(470 452)">
    <path d="M58 20 q34 0 34 28 q0 28 -34 28" stroke="${P.cream}" stroke-width="12" fill="none"/>
    <rect x="0" y="0" width="70" height="92" rx="10" fill="${P.cream}"/>
    <rect x="0" y="0" width="70" height="14" rx="6" fill="#E7D8BC"/>
    <rect x="0" y="40" width="70" height="10" fill="${P.terracotta}" opacity="0.85"/>
  </g>
  <!-- glass server -->
  <g transform="translate(245 400)">
    <path d="M150 50 q42 6 36 50 q-6 40 -40 42" stroke="#FFFFFF" stroke-width="10" fill="none" opacity="0.7"/>
    <path d="M0 0 H170 L160 150 Q158 170 138 170 H32 Q12 170 10 150 Z" fill="#FFFFFF" opacity="0.28"/>
    <path id="coffeeFill" d="M7 88 H163 L160 150 Q158 170 138 170 H32 Q12 170 10 150 Z" fill="#4A2A18" opacity="0.92"/>
    <path d="M0 0 H170 L160 150 Q158 170 138 170 H32 Q12 170 10 150 Z" fill="none" stroke="#FFFFFF" stroke-width="5" opacity="0.8"/>
    <rect x="18" y="16" width="10" height="120" rx="5" fill="#fff" opacity="0.5"/>
  </g>
  <!-- V60 dripper -->
  <g transform="translate(330 330)">
    <ellipse cx="0" cy="78" rx="72" ry="12" fill="#E8DCC6"/>
    <path d="M-40 60 H40 V76 H-40 Z" fill="#F3EBDD"/>
    <path d="M-112 -10 H112 L44 64 H-44 Z" fill="${P.paper}"/>
    <path d="M-112 -10 H112 L104 -2 H-104 Z" fill="#E9DFCB"/>
    <path d="M-70 0 L-26 58 M-30 0 L-10 58 M10 0 L10 58 M50 0 L28 58 M88 0 L40 58" stroke="#E6DAC4" stroke-width="4"/>
    <path d="M-112 -10 q-40 10 -40 30 q0 18 36 18" stroke="${P.paper}" stroke-width="14" fill="none"/>
    <!-- filter paper -->
    <path d="M-100 -12 L-86 -30 L-70 -14 L-54 -32 L-38 -14 L-22 -32 L-6 -14 L10 -32 L26 -14 L42 -32 L58 -14 L74 -32 L90 -14 L100 -12 Z" fill="#F7F0E2"/>
    <ellipse cx="0" cy="-10" rx="96" ry="14" fill="#5A331F"/>
    <ellipse cx="-10" cy="-12" rx="40" ry="6" fill="#8A5532" opacity="0.7"/>
  </g>
  <!-- gooseneck kettle -->
  <g transform="translate(470 175) rotate(-18)">
    <path d="M40 -10 q70 -10 70 60 q0 50 -40 70" stroke="${P.espresso}" stroke-width="13" fill="none" stroke-linecap="round"/>
    <path d="M-60 0 H60 L78 120 Q80 138 62 138 H-62 Q-80 138 -78 120 Z" fill="${P.espresso}"/>
    <rect x="-66" y="-12" width="132" height="18" rx="8" fill="#3E271B"/>
    <circle cx="0" cy="-20" r="11" fill="${P.caramel}"/>
    <rect x="-46" y="10" width="10" height="110" rx="5" fill="#fff" opacity="0.12"/>
    <path d="M-72 118 C -120 110, -130 60, -150 30 C -160 14, -176 8, -190 14" stroke="${P.espresso}" stroke-width="12" fill="none" stroke-linecap="round"/>
  </g>
</svg>`;
}

// ---------- 2. KLOVA bag 560x680 ----------
function bagSVG({ W = 560, H = 680, x = 280, y = 330, s = 1, label = P.cream, accent = P.terracotta, origin = 'SPECIALTY COFFEE', originAr = 'محاصيل مختصة', bg = true, bgCol = P.sageL, circle = '#DCE0C3' } = {}) {
  const bagBody = `<g transform="translate(${x} ${y}) scale(${s})">
    <ellipse cx="0" cy="270" rx="170" ry="16" fill="#000" opacity="0.12"/>
    <path d="M-150 -210 L150 -210 L158 250 Q158 266 140 266 L-140 266 Q-158 266 -158 250 Z" fill="${P.kraft}"/>
    <path d="M60 -210 L150 -210 L158 250 Q158 266 140 266 L80 266 Z" fill="${P.kraftD}" opacity="0.35"/>
    <path d="M-150 -210 L150 -210 L150 -178 L-150 -178 Z" fill="${P.kraftD}"/>
    <path d="M-150 -210 ${Array.from({ length: 16 }, (_, i) => `L ${-150 + (i + 0.5) * 18.75} ${i % 2 ? -210 : -218} `).join('')} L150 -210 Z" fill="${P.kraftD}"/>
    <path d="M-150 -168 H150" stroke="#8E5F33" stroke-width="3" stroke-dasharray="6 6" opacity="0.6"/>
    <circle cx="96" cy="-128" r="14" fill="#8E5F33" opacity="0.45"/><circle cx="96" cy="-128" r="6" fill="${P.kraft}"/>
    <rect x="-116" y="-90" width="232" height="250" rx="10" fill="${label}"/>
    <rect x="-116" y="-90" width="232" height="36" rx="10" fill="${accent}"/>
    <rect x="-116" y="-66" width="232" height="12" fill="${accent}"/>
    <text x="0" y="-66" text-anchor="middle" font-family="Special Elite" font-size="17" fill="${P.paper}" letter-spacing="3">${origin}</text>
    <text x="0" y="28" text-anchor="middle" font-family="Lalezar" font-size="84" fill="${P.espresso}">كلوفا</text>
    <text x="0" y="66" text-anchor="middle" font-family="Special Elite" font-size="26" fill="${P.espresso}" letter-spacing="8">KLOVA</text>
    <path d="M-70 86 H70" stroke="${P.espresso}" stroke-width="2"/>
    <text x="0" y="124" text-anchor="middle" font-family="Noto Kufi Arabic" font-weight="700" font-size="22" fill="${accent}">${originAr}</text>
    ${bean(-78, 134, 11, 7.5, -30, P.coffee)}${bean(78, 134, 11, 7.5, 30, P.coffee)}
  </g>`;
  if (!bg) return bagBody;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${bgCol}"/>
    <circle cx="${W / 2}" cy="${H * 0.46}" r="${W * 0.42}" fill="${circle}"/>
    ${leaf(70, 600, 150, 34, -60, P.sageD)}${leaf(70, 600, 130, 30, -100, P.sage)}${leaf(500, 610, 140, 30, -120, P.sage)}
    ${bagBody}
    ${(() => { const r = rng(9); let s = ''; for (let i = 0; i < 14; i++) s += bean(60 + r() * 440, 610 + r() * 55, 17, 12, r() * 360, [P.coffee, P.coffee2, '#5A331F'][i % 3]); return s; })()}
  </svg>`;
}

// ---------- 3. Espresso machine 560x680 ----------
function espresso() {
  const W = 560, H = 680;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="${P.mustardL}"/>
  <path d="M0 0 H${W} V120 H0 Z" fill="#F3DDAA"/>
  <rect x="0" y="560" width="${W}" height="120" fill="${P.caramel}"/>
  <rect x="0" y="560" width="${W}" height="9" fill="${P.caramelL}"/>
  ${woodGrain(0, 570, W, 110, 17)}
  <!-- cups on top -->
  <g transform="translate(190 118)"><rect x="0" y="0" width="46" height="36" rx="6" fill="${P.paper}"/><rect x="0" y="0" width="46" height="8" fill="${P.terracotta}"/></g>
  <g transform="translate(250 118)"><rect x="0" y="0" width="46" height="36" rx="6" fill="${P.paper}"/><rect x="0" y="0" width="46" height="8" fill="${P.sage}"/></g>
  <!-- body -->
  <rect x="110" y="150" width="340" height="415" rx="28" fill="${P.cream}"/>
  <rect x="360" y="150" width="90" height="415" rx="28" fill="#E4D3B4"/>
  <rect x="110" y="150" width="340" height="22" rx="10" fill="#D9C6A2"/>
  <!-- gauge -->
  <circle cx="280" cy="235" r="44" fill="${P.espresso}"/>
  <circle cx="280" cy="235" r="35" fill="${P.paper}"/>
  ${Array.from({ length: 9 }, (_, i) => { const a = (-210 + i * 30) * Math.PI / 180; return `<line x1="${280 + Math.cos(a) * 26}" y1="${235 + Math.sin(a) * 26}" x2="${280 + Math.cos(a) * 32}" y2="${235 + Math.sin(a) * 32}" stroke="${P.espresso}" stroke-width="3"/>`; }).join('')}
  <line x1="280" y1="235" x2="302" y2="216" stroke="${P.terracotta}" stroke-width="5" stroke-linecap="round"/>
  <circle cx="280" cy="235" r="5" fill="${P.espresso}"/>
  <!-- buttons -->
  <circle cx="170" cy="235" r="12" fill="${P.terracotta}"/><circle cx="390" cy="235" r="12" fill="${P.sageD}"/>
  <!-- group head -->
  <rect x="230" y="298" width="100" height="34" rx="8" fill="#8F877B"/>
  <rect x="240" y="330" width="80" height="22" rx="6" fill="#6F685E"/>
  <path d="M244 342 L120 372 Q106 376 110 388 Q114 398 128 394 L250 356 Z" fill="${P.coffee2}"/>
  <!-- steam wand -->
  <path d="M410 300 L410 330 Q410 350 426 368 L452 470" stroke="#8F877B" stroke-width="12" fill="none" stroke-linecap="round"/>
  <circle cx="410" cy="292" r="12" fill="#6F685E"/>
  <!-- drip tray -->
  <rect x="160" y="520" width="240" height="30" rx="6" fill="${P.espresso}"/>
  ${Array.from({ length: 11 }, (_, i) => `<rect x="${172 + i * 20}" y="526" width="10" height="18" rx="3" fill="#4A3326"/>`).join('')}
  <!-- espresso cup -->
  <g transform="translate(250 462)"><path d="M58 14 q22 0 22 18 q0 18 -22 18" stroke="${P.paper}" stroke-width="8" fill="none"/><path d="M0 0 H62 L56 52 Q54 60 44 60 H18 Q8 60 6 52 Z" fill="${P.paper}"/><ellipse cx="31" cy="4" rx="30" ry="6" fill="#5A331F"/></g>
</svg>`;
}

// ---------- 4. Beans close-up 640x560 ----------
function beans() {
  const W = 640, H = 560; const r = rng(4242); let s = '';
  const cols = ['#3E2214', '#4A2A18', '#57311C', '#653A21', '#734327', '#5E351E'];
  const items = [];
  for (let i = 0; i < 230; i++) items.push({ x: r() * (W + 60) - 30, y: r() * (H + 60) - 30, rx: 30 + r() * 10, ry: 21 + r() * 6, rot: r() * 360, c: cols[Math.floor(r() * cols.length)], hl: 0.12 + r() * 0.16 });
  items.sort((a, b) => a.y - b.y);
  for (const b of items) s += bean(b.x, b.y, b.rx, b.ry, b.rot, b.c, '#1E0F08', b.hl);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <defs><radialGradient id="vg" cx="0.45" cy="0.4" r="0.75"><stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.45"/></radialGradient>
    <radialGradient id="lt" cx="0.35" cy="0.3" r="0.6"><stop offset="0" stop-color="#FFD9A0" stop-opacity="0.22"/><stop offset="1" stop-color="#FFD9A0" stop-opacity="0"/></radialGradient></defs>
    <rect width="${W}" height="${H}" fill="${P.espresso}"/>${s}
    <rect width="${W}" height="${H}" fill="url(#lt)"/><rect width="${W}" height="${H}" fill="url(#vg)"/>
  </svg>`;
}

// ---------- 5. Coffee cherries / origins 580x700 ----------
function cherries() {
  const W = 580, H = 700; const r = rng(77); let s = '';
  // branch
  s += `<path d="M-20 690 C 120 560, 200 420, 300 320 S 480 120, 620 40" stroke="#6B4A2E" stroke-width="16" fill="none" stroke-linecap="round"/>`;
  const nodes = [[90, 590], [180, 470], [270, 350], [370, 250], [470, 160]];
  nodes.forEach(([x, y], i) => {
    s += leaf(x, y, 150 + r() * 30, 36, -150 + r() * 20, i % 2 ? P.sageD : '#6E7D52');
    s += leaf(x, y, 150 + r() * 30, 36, 20 + r() * 20, i % 2 ? '#6E7D52' : P.sageD);
  });
  nodes.forEach(([x, y], i) => {
    const n = 7 + Math.floor(r() * 4);
    for (let k = 0; k < n; k++) {
      const a = r() * Math.PI * 2, d = 10 + r() * 26;
      const cx = x + Math.cos(a) * d, cy = y + Math.sin(a) * d * 0.8;
      const pick = r();
      const col = pick < 0.62 ? '#B32E24' : pick < 0.82 ? '#D0502C' : pick < 0.92 ? '#E08A3A' : '#A6AD5C';
      const rad = 15 + r() * 5;
      s += `<circle cx="${cx}" cy="${cy}" r="${rad}" fill="${col}"/><circle cx="${cx - rad * 0.35}" cy="${cy - rad * 0.4}" r="${rad * 0.28}" fill="#fff" opacity="0.45"/><circle cx="${cx + rad * 0.5}" cy="${cy + rad * 0.45}" r="2.5" fill="#3a1a10" opacity="0.6"/>`;
    }
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${P.blush}"/>
    <circle cx="430" cy="140" r="90" fill="#F3D6B8"/>
    <path d="M40 120 C 140 60, 220 200, 330 130" stroke="${P.terracotta}" stroke-width="4" stroke-dasharray="3 12" stroke-linecap="round" fill="none" opacity="0.8"/>
    ${s}
    <g transform="translate(120 150) rotate(-8)">
      <path d="M0 0 H150 L175 32 L150 64 H0 Z" fill="${P.kraft}"/>
      <circle cx="152" cy="32" r="7" fill="${P.blush}"/>
      <text x="72" y="42" text-anchor="middle" font-family="Special Elite" font-size="26" fill="${P.espresso}" letter-spacing="3">ORIGIN</text>
    </g>
  </svg>`;
}

// ---------- 6. Tasting (top view) 560x620 ----------
function tasting() {
  const W = 560, H = 620;
  const berries = (x, y) => { let s = ''; const r = rng(x + y); for (let i = 0; i < 7; i++) { const cx = x + (r() - 0.5) * 70, cy = y + (r() - 0.5) * 60, rad = 14 + r() * 5; s += `<circle cx="${cx}" cy="${cy}" r="${rad}" fill="${['#8E2A3A', '#6D2340', '#B33A3A'][i % 3]}"/><circle cx="${cx - 4}" cy="${cy - 5}" r="4" fill="#fff" opacity="0.4"/>`; } return s; };
  const choc = (x, y, rot) => `<g transform="translate(${x} ${y}) rotate(${rot})"><rect x="0" y="0" width="96" height="70" rx="5" fill="#4A2A18"/>${[0, 1, 2].map(i => [0, 1].map(j => `<rect x="${6 + i * 30}" y="${6 + j * 30}" width="24" height="24" rx="3" fill="#5C3520"/>`).join('')).join('')}</g>`;
  const flower = (x, y) => `<g transform="translate(${x} ${y})">${[0, 72, 144, 216, 288].map(a => `<ellipse cx="0" cy="-24" rx="15" ry="26" fill="${P.terraL}" transform="rotate(${a})"/>`).join('')}<circle r="13" fill="${P.mustard}"/></g>`;
  const lemon = (x, y) => `<g transform="translate(${x} ${y})"><circle r="46" fill="#E9C24A"/><circle r="39" fill="#F6E7A6"/>${[0, 45, 90, 135, 180, 225, 270, 315].map(a => `<path d="M0 0 L${Math.cos(a * Math.PI / 180) * 36} ${Math.sin(a * Math.PI / 180) * 36}" stroke="#E9C24A" stroke-width="3"/>`).join('')}<circle r="5" fill="#F6E7A6"/></g>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <defs><radialGradient id="cof" cx="0.45" cy="0.45" r="0.6"><stop offset="0" stop-color="#7A4526"/><stop offset="0.8" stop-color="#4A2A18"/><stop offset="1" stop-color="#B97A45"/></radialGradient></defs>
    <rect width="${W}" height="${H}" fill="${P.cream}"/>
    <path d="M0 470 H${W} V${H} H0 Z" fill="${P.cream2}" opacity="0.6"/>
    ${berries(110, 120)}${flower(450, 110)}${choc(60, 450, -12)}${lemon(460, 500)}
    <ellipse cx="290" cy="318" rx="176" ry="172" fill="#000" opacity="0.08"/>
    <circle cx="280" cy="305" r="170" fill="${P.paper}"/>
    <circle cx="280" cy="305" r="150" fill="none" stroke="#EDE3D1" stroke-width="3"/>
    <path d="M395 305 q60 -8 70 24 q-6 30 -70 20" fill="${P.paper}" stroke="#E6DAC4" stroke-width="3"/>
    <circle cx="280" cy="305" r="118" fill="#F0E7D6"/>
    <circle cx="280" cy="305" r="102" fill="url(#cof)"/>
    <path d="M280 305 m-50 0 a50 50 0 1 1 100 0 a38 38 0 1 1 -76 0 a26 26 0 1 1 52 0" stroke="#C99461" stroke-width="5" fill="none" opacity="0.6"/>
    <g transform="translate(150 470) rotate(-38)"><ellipse cx="0" cy="0" rx="22" ry="30" fill="#CFC7B8"/><rect x="-5" y="24" width="10" height="120" rx="5" fill="#CFC7B8"/></g>
  </svg>`;
}

// ---------- 7. Takeaway cafe cups 540x640 ----------
function cafe() {
  const W = 540, H = 640;
  const cup = (x, y, s, sleeve) => `<g transform="translate(${x} ${y}) scale(${s})">
    <ellipse cx="0" cy="222" rx="80" ry="12" fill="#000" opacity="0.12"/>
    <path d="M-86 -150 H86 L64 220 H-64 Z" fill="${P.paper}"/>
    <path d="M30 -150 H86 L64 220 H40 Z" fill="#EDE3D1"/>
    <path d="M-78 -40 H78 L70 80 H-70 Z" fill="${sleeve}"/>
    <circle cx="0" cy="20" r="22" fill="${P.paper}" opacity="0.85"/>
    ${bean(0, 20, 12, 8, -30, P.coffee)}
    <rect x="-96" y="-176" width="192" height="30" rx="10" fill="#EDE3D1"/>
    <path d="M-80 -176 Q0 -216 80 -176 Z" fill="#E4D8C2"/>
    <rect x="-18" y="-204" width="36" height="10" rx="5" fill="${P.espresso}" opacity="0.7"/>
  </g>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${P.terraL}"/>
    <circle cx="270" cy="300" r="220" fill="#EDB79F"/>
    <rect x="0" y="540" width="${W}" height="100" fill="#D98E73"/>
    ${cup(190, 330, 1.0, P.kraft)}${cup(370, 380, 0.82, P.sage)}
    <g transform="translate(70 520)">${[0, 1, 2, 3].map(i => `<ellipse cx="0" cy="${-i * 12}" rx="34" ry="11" fill="${i % 2 ? P.mustard : '#C98E2A'}"/>`).join('')}</g>
  </svg>`;
}

// ---------- 8. Home mug with latte heart 580x680 ----------
function homeMug() {
  const W = 580, H = 680;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${P.latte}"/>
    <rect x="360" y="40" width="170" height="220" rx="6" fill="#F4EAD8"/>
    <path d="M445 40 V260 M360 150 H530" stroke="#E2D1B3" stroke-width="8"/>
    ${leaf(60, 330, 170, 40, -70, P.sage)}${leaf(60, 330, 150, 34, -110, P.sageD)}${leaf(60, 330, 140, 30, -40, P.sageD)}
    <!-- books -->
    <rect x="70" y="520" width="440" height="70" rx="8" fill="${P.sageD}"/>
    <rect x="70" y="520" width="440" height="12" fill="#77875A"/>
    <rect x="100" y="470" width="380" height="54" rx="6" fill="${P.terracotta}"/>
    <rect x="100" y="470" width="380" height="10" fill="#D4694A"/>
    <rect x="470" y="478" width="10" height="42" fill="${P.paper}"/>
    <rect x="0" y="590" width="${W}" height="90" fill="${P.caramel}"/>
    ${woodGrain(0, 596, W, 84, 23)}
    <!-- mug -->
    <g transform="translate(290 330)">
      <path d="M118 10 q74 0 74 62 q0 58 -74 60" stroke="${P.cream}" stroke-width="24" fill="none"/>
      <path d="M-130 -70 H130 V110 Q130 140 100 140 H-100 Q-130 140 -130 110 Z" fill="${P.cream}"/>
      <path d="M60 -70 H130 V110 Q130 140 100 140 H60 Z" fill="#E6D6B8"/>
      <rect x="-130" y="10" width="260" height="22" fill="${P.mustard}" opacity="0.9"/>
      <ellipse cx="0" cy="-70" rx="130" ry="34" fill="#E3D2B2"/>
      <ellipse cx="0" cy="-68" rx="116" ry="28" fill="${P.caramelL}"/>
      <path d="M0 -50 C -40 -72, -46 -96, -20 -96 C -8 -96, -2 -88, 0 -82 C 2 -88, 8 -96, 20 -96 C 46 -96, 40 -72, 0 -50 Z" fill="#FBF3E6"/>
      <path d="M0 -50 L 0 -40" stroke="#FBF3E6" stroke-width="4"/>
    </g>
  </svg>`;
}

// ---------- 9. Final product lineup 860x960 ----------
function finalShot() {
  const W = 860, H = 960; const r = rng(99); let beansS = '';
  for (let i = 0; i < 26; i++) beansS += bean(40 + r() * 780, 840 + r() * 110, 20, 14, r() * 360, [P.coffee, P.coffee2, '#5A331F'][i % 3]);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${P.cream}"/>
    <circle cx="430" cy="470" r="360" fill="${P.mustardL}"/>
    ${Array.from({ length: 24 }, (_, i) => { const a = i * 15 * Math.PI / 180; return `<path d="M${430 + Math.cos(a) * 380} ${470 + Math.sin(a) * 380} L${430 + Math.cos(a) * 420} ${470 + Math.sin(a) * 420}" stroke="${P.mustard}" stroke-width="10" stroke-linecap="round" opacity="0.6"/>`; }).join('')}
    ${leaf(90, 820, 200, 44, -60, P.sageD)}${leaf(90, 820, 170, 36, -105, P.sage)}${leaf(780, 830, 190, 40, -120, P.sage)}${leaf(780, 830, 160, 34, -75, P.sageD)}
    ${bagSVG({ bg: false, x: 205, y: 470, s: 0.78, label: P.cream, accent: P.sageD, origin: 'ETHIOPIA', originAr: 'إثيوبيا' })}
    ${bagSVG({ bg: false, x: 655, y: 470, s: 0.78, label: P.cream, accent: P.mustard, origin: 'BRAZIL', originAr: 'البرازيل' })}
    ${bagSVG({ bg: false, x: 430, y: 500, s: 1.0, label: P.cream, accent: P.terracotta, origin: 'COLOMBIA', originAr: 'كولومبيا' })}
    ${beansS}
  </svg>`;
}

const ILLUS = {
  homebrew: homebrew, bag: () => bagSVG(), espresso, beans, cherries, tasting, cafe, homeMug, final: finalShot,
};
if (typeof module !== 'undefined') module.exports = { ILLUS, P };
if (typeof window !== 'undefined') { window.ILLUS = ILLUS; window.PAL = P; }
