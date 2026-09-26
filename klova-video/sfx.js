// Synthesizes every SFX cue from cues.json into one stereo 48k WAV (no samples, no music).
const fs = require('fs');
const SR = 48000;
const cues = JSON.parse(fs.readFileSync(__dirname + '/cues.json', 'utf8'));
const DUR = parseFloat(process.argv[2] || '20.8');
const OUT = process.argv[3] || __dirname + '/sfx.wav';
const N = Math.ceil(DUR * SR);
const L = new Float32Array(N + SR * 2), Rt = new Float32Array(N + SR * 2);

let seed = 987654321;
const rnd = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
const noise = () => rnd() * 2 - 1;
const TAU = Math.PI * 2;

class Biquad {
  constructor(type, f, Q = 0.707) { this.x1 = this.x2 = this.y1 = this.y2 = 0; this.type = type; this.set(f, Q); }
  set(f, Q = this.Q) {
    this.Q = Q;
    const w = TAU * Math.min(Math.max(f, 20), SR * 0.45) / SR, c = Math.cos(w), s = Math.sin(w), a = s / (2 * Q);
    let b0, b1, b2;
    if (this.type === 'lp') { b0 = (1 - c) / 2; b1 = 1 - c; b2 = (1 - c) / 2; }
    else if (this.type === 'hp') { b0 = (1 + c) / 2; b1 = -(1 + c); b2 = (1 + c) / 2; }
    else { b0 = a; b1 = 0; b2 = -a; }
    const a0 = 1 + a;
    this.b0 = b0 / a0; this.b1 = b1 / a0; this.b2 = b2 / a0; this.a1 = -2 * c / a0; this.a2 = (1 - a) / a0;
    return this;
  }
  run(x) {
    const y = this.b0 * x + this.b1 * this.x1 + this.b2 * this.x2 - this.a1 * this.y1 - this.a2 * this.y2;
    this.x2 = this.x1; this.x1 = x; this.y2 = this.y1; this.y1 = y; return y;
  }
}
const mono = (d) => new Float32Array(Math.ceil(d * SR));
const env = (t, a, dcy) => (1 - Math.exp(-t / a)) * Math.exp(-t / dcy);

// ---------------- generators: return {m} (mono) or {l, r} ----------------
const G = {
  pop({ pitch = 1 }) {
    const o = mono(0.16); let ph = 0; const hp = new Biquad('hp', 2500);
    for (let i = 0; i < o.length; i++) {
      const t = i / SR, f = 360 * pitch * (1 + 1.4 * (1 - Math.exp(-t / 0.016)));
      ph += TAU * f / SR;
      o[i] = (Math.sin(ph) + 0.18 * Math.sin(2 * ph)) * env(t, 0.0012, 0.034) * 0.95 + (t < 0.005 ? hp.run(noise()) * 0.35 * (1 - t / 0.005) : 0);
    }
    return { m: o };
  },
  click({ pitch = 1 }) {
    // crisp UI/mouse click: noise impulse through resonant bands, small release click, peak-normalized to 1
    const o = mono(0.07), p = 1 + (pitch - 1) * 0.25;
    const hp = new Biquad('hp', 1800), bp = new Biquad('bp', 3300 * p, 3), bp2 = new Biquad('bp', 1100 * p, 2);
    let pk = 0;
    for (let i = 0; i < o.length; i++) {
      const t = i / SR;
      const e = Math.exp(-t / 0.0012) + (t >= 0.032 ? Math.exp(-(t - 0.032) / 0.0009) * 0.3 : 0);
      const x = noise() * e;
      o[i] = hp.run(x) * 0.6 + bp.run(x) * 2.2 + bp2.run(x) * 1.2;
      pk = Math.max(pk, Math.abs(o[i]));
    }
    for (let i = 0; i < o.length; i++) o[i] /= pk;
    return { m: o };
  },
  tap() {
    const o = mono(0.1); const hp = new Biquad('hp', 3000);
    for (let i = 0; i < o.length; i++) { const t = i / SR; o[i] = Math.sin(TAU * (1500 - 3000 * t) * t) * env(t, 0.0008, 0.014) * 0.6 + hp.run(noise()) * Math.exp(-t / 0.002) * 0.45; }
    return { m: o };
  },
  whoosh({ dur = 0.42, pan = 0, base = 240 }) {
    const n = Math.ceil(dur * SR), l = new Float32Array(n), r = new Float32Array(n);
    const bp1 = new Biquad('bp', 500, 0.9), bp2 = new Biquad('bp', 500, 0.9), lp = new Biquad('lp', 6000);
    const sweep = pan === 0 ? 0.5 : 1;
    for (let i = 0; i < n; i++) {
      const x = i / n;
      const s = x < 0.62 ? x / 0.62 : 1 - (x - 0.62) / 0.38 * 0.65;
      if (i % 16 === 0) { const fc = base * Math.pow(11, s); bp1.set(fc, 0.9); bp2.set(fc * 1.05, 0.9); }
      const e = x < 0.62 ? Math.pow(x / 0.62, 2.2) : Math.pow(1 - (x - 0.62) / 0.38, 1.6);
      const v = lp.run(bp2.run(bp1.run(noise()))) * e * 3.2;
      const pos = pan === 0 ? (x - 0.5) * sweep : -pan * (1 - 2 * x) * sweep; // -1..1
      const a = (pos + 1) * Math.PI / 4;
      l[i] = v * Math.cos(a) * 1.3; r[i] = v * Math.sin(a) * 1.3;
    }
    return { l, r };
  },
  swish(p) { return G.whoosh(Object.assign({ dur: 0.26, base: 600 }, p)); },
  impact() {
    const o = mono(1.0); let ph = 0; const lp = new Biquad('lp', 260), hp = new Biquad('hp', 3000);
    for (let i = 0; i < o.length; i++) {
      const t = i / SR, f = 105 * Math.exp(-t / 0.11) + 38; ph += TAU * f / SR;
      const v = Math.sin(ph) * env(t, 0.002, 0.38) * 1.0 + lp.run(noise()) * Math.exp(-t / 0.05) * 1.6 + hp.run(noise()) * Math.exp(-t / 0.004) * 0.3;
      o[i] = Math.tanh(v * 1.5) / Math.tanh(1.5);
    }
    return { m: o };
  },
  stamp() {
    const o = mono(0.4); let ph = 0; const bp = new Biquad('bp', 1500, 0.7), hp = new Biquad('hp', 3200);
    for (let i = 0; i < o.length; i++) {
      const t = i / SR, f = 175 * Math.exp(-t / 0.03) + 62; ph += TAU * f / SR;
      const v = Math.sin(ph) * env(t, 0.001, 0.075) * 0.95 + bp.run(noise()) * Math.exp(-t / 0.02) * 1.6 + hp.run(noise()) * Math.exp(-t / 0.008) * 0.5;
      o[i] = Math.tanh(v * 1.4) / Math.tanh(1.4);
    }
    return { m: o };
  },
  thud() {
    const o = mono(0.35); let ph = 0; const lp = new Biquad('lp', 320);
    for (let i = 0; i < o.length; i++) { const t = i / SR, f = 95 * Math.exp(-t / 0.05) + 46; ph += TAU * f / SR; o[i] = Math.sin(ph) * env(t, 0.0015, 0.085) + lp.run(noise()) * Math.exp(-t / 0.022) * 0.9; }
    return { m: o };
  },
  scribble({ dur = 0.45 }) {
    const o = mono(dur); const bp = new Biquad('bp', 3200, 1.4), lp = new Biquad('lp', 900);
    for (let i = 0; i < o.length; i++) {
      const t = i / SR, am = 0.3 + 0.7 * Math.pow(Math.abs(Math.sin(Math.PI * 12.5 * t + 0.9 * Math.sin(TAU * 3.1 * t))), 0.6);
      const e = Math.min(1, t / 0.02) * Math.min(1, (dur - t) / 0.05);
      o[i] = (bp.run(noise()) * 1.7 + lp.run(noise()) * 0.25) * am * e;
    }
    return { m: o };
  },
  buzzer({ pitch = 1 }) {
    const o = mono(0.46);
    const seg = [[0, 0.16, 185 * pitch], [0.2, 0.44, 140 * pitch]];
    for (let i = 0; i < o.length; i++) {
      const t = i / SR; let v = 0;
      for (const [a, b, f] of seg) {
        if (t < a || t > b) continue;
        const tt = t - a, e = Math.min(1, tt / 0.006) * Math.min(1, (b - t) / 0.02);
        for (let h = 1; h * f < 3200; h += 2) v += Math.sin(TAU * f * h * tt) / h * e;
      }
      o[i] = Math.tanh(v * 0.9) * 0.55;
    }
    return { m: o };
  },
  ding({ pitch = 1 }) {
    const o = mono(1.1); const f0 = 1568 * pitch;
    const P = [[1, 1, 0.55], [2.0, 0.42, 0.3], [3.0, 0.2, 0.17], [4.16, 0.12, 0.09]];
    for (let i = 0; i < o.length; i++) { const t = i / SR; let v = 0; for (const [q, a, d] of P) v += Math.sin(TAU * f0 * q * t + q) * a * env(t, 0.0015, d); o[i] = v * 0.45; }
    return { m: o };
  },
  sparkle() {
    const n = Math.ceil(0.7 * SR), l = new Float32Array(n), r = new Float32Array(n);
    for (let k = 0; k < 13; k++) {
      const t0 = rnd() * 0.45, f = 2600 + rnd() * 4200, pos = rnd() * 2 - 1, a = (pos + 1) * Math.PI / 4, amp = 0.16 + rnd() * 0.12;
      const s0 = Math.floor(t0 * SR);
      for (let i = 0; i < 0.09 * SR && s0 + i < n; i++) { const t = i / SR, v = Math.sin(TAU * f * t) * env(t, 0.0008, 0.024) * amp; l[s0 + i] += v * Math.cos(a); r[s0 + i] += v * Math.sin(a); }
    }
    const hp = new Biquad('hp', 6500);
    for (let i = 0; i < n; i++) { const t = i / SR, v = hp.run(noise()) * env(t, 0.03, 0.18) * 0.12; l[i] += v; r[i] += v; }
    return { l, r };
  },
  chaching() {
    const o = mono(1.2); const hp = new Biquad('hp', 3000), lp = new Biquad('lp', 400);
    const bell = (t, f0, amp) => { if (t < 0) return 0; const P = [[1, 1, 0.5], [2.76, 0.5, 0.3], [5.4, 0.3, 0.14], [8.93, 0.15, 0.07]]; let v = 0; for (const [q, a, d] of P) v += Math.sin(TAU * f0 * q * t) * a * env(t, 0.001, d); return v * amp; };
    for (let i = 0; i < o.length; i++) {
      const t = i / SR;
      let v = hp.run(noise()) * (Math.exp(-t / 0.02) + (t > 0.06 ? Math.exp(-(t - 0.06) / 0.02) : 0)) * 0.7;
      v += lp.run(noise()) * Math.exp(-t / 0.03) * 0.6;
      v += bell(t - 0.12, 2093, 0.45) + bell(t - 0.145, 2637, 0.35);
      o[i] = v;
    }
    return { m: o };
  },
  printer({ dur = 1.2 }) {
    const o = mono(dur + 0.05); const bp = new Biquad('bp', 2600, 1.2), lp = new Biquad('lp', 500);
    let ph = 0;
    for (let i = 0; i < o.length; i++) {
      const t = i / SR, k = t * 26, tt = (k - Math.floor(k)) / 26;
      ph += TAU * 95 / SR;
      const motor = lp.run(((ph / TAU) % 1) * 2 - 1) * 0.35;
      const tick = bp.run(noise()) * Math.exp(-tt / 0.0025) * 1.3 + Math.sin(TAU * 720 * tt) * Math.exp(-tt / 0.006) * 0.25;
      const e = Math.min(1, t / 0.02) * Math.min(1, Math.max(0, (dur - t) / 0.04));
      o[i] = (motor + tick) * e;
    }
    return { m: o };
  },
  rattle({ dur = 1.0 }) {
    const n = Math.ceil((dur + 0.1) * SR), l = new Float32Array(n), r = new Float32Array(n);
    for (let k = 0; k < 80; k++) {
      const t0 = dur * Math.pow(rnd(), 1.7), f = 1500 + rnd() * 2800, a = rnd() * Math.PI / 2, amp = (0.08 + rnd() * 0.3) * (1 - t0 / dur * 0.6);
      const s0 = Math.floor(t0 * SR);
      for (let i = 0; i < 0.02 * SR && s0 + i < n; i++) { const t = i / SR, v = (Math.sin(TAU * f * t) * 0.8 + noise() * 0.3) * Math.exp(-t / 0.0035) * amp; l[s0 + i] += v * Math.cos(a); r[s0 + i] += v * Math.sin(a); }
    }
    return { l, r };
  },
  boing({ pitch = 1 }) {
    const o = mono(0.6); let ph = 0;
    for (let i = 0; i < o.length; i++) { const t = i / SR, f = 200 * pitch * (1 + 0.7 * t) * (1 + 0.28 * Math.sin(TAU * 10.5 * t) * Math.exp(-t / 0.22)); ph += TAU * f / SR; o[i] = (Math.sin(ph) + 0.3 * Math.sin(2 * ph)) * env(t, 0.004, 0.24) * 0.7; }
    return { m: o };
  },
  shutter() {
    const o = mono(0.2); const hp = new Biquad('hp', 2200), bp = new Biquad('bp', 420, 2);
    for (let i = 0; i < o.length; i++) { const t = i / SR; const hit = (x) => x < 0 ? 0 : Math.exp(-x / 0.005); o[i] = hp.run(noise()) * (hit(t) + 0.7 * hit(t - 0.075)) * 0.8 + bp.run(noise()) * (hit(t) * 2 + hit(t - 0.075) * 1.5) * 1.2; }
    return { m: o };
  },
  flyby({ dur = 1.6 }) {
    const n = Math.ceil(dur * SR), l = new Float32Array(n), r = new Float32Array(n);
    const lp = new Biquad('lp', 400), lp2 = new Biquad('lp', 700); let ph = 0;
    for (let i = 0; i < n; i++) {
      const x = i / n, b = Math.pow(Math.sin(Math.PI * x), 2);
      if (i % 32 === 0) lp.set(300 + 1400 * b);
      ph += TAU * (125 - 35 * x) / SR;
      const v = (lp.run(noise()) * 1.4 + lp2.run(((ph / TAU) % 1) * 2 - 1) * 0.5) * b;
      const a = x * Math.PI / 2;
      l[i] = v * Math.cos(a); r[i] = v * Math.sin(a);
    }
    return { l, r };
  },
  rip() {
    const o = mono(0.32); const bp = new Biquad('bp', 3000, 1.1); let g = 1;
    for (let i = 0; i < o.length; i++) {
      const t = i / SR; if (i % 96 === 0) { g = Math.pow(rnd(), 2) * 1.6 + 0.1; bp.set(3500 - 7000 * t, 1.1); }
      o[i] = bp.run(noise()) * g * Math.min(1, t / 0.006) * Math.min(1, (0.32 - t) / 0.08) * 1.4;
    }
    return { m: o };
  },
  flutter({ dur = 0.7 }) {
    const o = mono(dur + 0.05); const lp = new Biquad('lp', 1600);
    for (let i = 0; i < o.length; i++) { const t = i / SR, k = t * 13, tt = (k - Math.floor(k)) / 13; o[i] = lp.run(noise()) * Math.exp(-tt / 0.016) * (1 - t / (dur + 0.05)) * 1.1; }
    return { m: o };
  },
};

// Two tracks: the main SFX bed (unchanged balance) and a clicks track where every former
// "pop" cue is a click at unit gain, so the track's volume in the mix is the click level.
const CLICK_CUES = new Set(['pop', 'click']);
const missing = new Set();
function renderTrack(list, forceGain) {
  const Lb = new Float32Array(N + SR * 2), Rb = new Float32Array(N + SR * 2);
  for (const c of list) {
    const gen = G[c.name];
    if (!gen) { missing.add(c.name); continue; }
    const res = gen(c), gain = forceGain ?? c.gain;
    const s0 = Math.round(c.t * SR);
    if (res.m) {
      const pos = c.pan != null && c.name !== 'whoosh' ? c.pan * 0.5 : (rnd() - 0.5) * 0.4;
      const a = (pos + 1) * Math.PI / 4, gl = Math.cos(a) * Math.SQRT2, gr = Math.sin(a) * Math.SQRT2;
      for (let i = 0; i < res.m.length; i++) { Lb[s0 + i] += res.m[i] * gain * gl; Rb[s0 + i] += res.m[i] * gain * gr; }
    } else {
      for (let i = 0; i < res.l.length; i++) { Lb[s0 + i] += res.l[i] * gain; Rb[s0 + i] += res.r[i] * gain; }
    }
  }
  return [Lb, Rb];
}
function writeWav(file, Lb, Rb, scale) {
  let peak = 0;
  for (let i = 0; i < N; i++) { const f = Math.min(1, (N - i) / (0.03 * SR)); Lb[i] *= f * scale; Rb[i] *= f * scale; peak = Math.max(peak, Math.abs(Lb[i]), Math.abs(Rb[i])); }
  const sc = peak > 1 ? 1 / peak : 1;
  const buf = Buffer.alloc(44 + N * 6);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 6, 4); buf.write('WAVE', 8); buf.write('fmt ', 12);
  buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 6, 28); buf.writeUInt16LE(6, 32); buf.writeUInt16LE(24, 34);
  buf.write('data', 36); buf.writeUInt32LE(N * 6, 40);
  for (let i = 0; i < N; i++) {
    buf.writeIntLE(Math.round(Math.max(-1, Math.min(1, Lb[i] * sc)) * 8388607), 44 + i * 6, 3);
    buf.writeIntLE(Math.round(Math.max(-1, Math.min(1, Rb[i] * sc)) * 8388607), 47 + i * 6, 3);
  }
  fs.writeFileSync(file, buf);
  console.log(`${file}: peak=${peak.toFixed(3)} limitScale=${sc.toFixed(3)}`);
}
const [mL, mR] = renderTrack(cues.filter((c) => !CLICK_CUES.has(c.name)));
writeWav(OUT, mL, mR, 0.847); // same master scale as the approved first mix
const clickCues = [];
for (const c of cues.filter((x) => CLICK_CUES.has(x.name)).sort((a, b) => a.t - b.t)) {
  if (clickCues.length && c.t - clickCues[clickCues.length - 1].t < 0.045) continue; // merge simultaneous clicks
  clickCues.push(Object.assign({}, c, { name: 'click', pan: 0 }));
}
console.log(`clicks: ${clickCues.length}`);
const [cL, cR] = renderTrack(clickCues, 1);
writeWav(OUT.replace(/\.wav$/, '') + '_clicks.wav', cL, cR, 1);
if (missing.size) console.log('missing generators:', [...missing]);
