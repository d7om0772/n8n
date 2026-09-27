import numpy as np, wave
SR = 48000
rng = np.random.default_rng(7)
def env_exp(n, tau): return np.exp(-np.arange(n)/(tau*SR))
def save(name, x, peak=0.9):
    x = x / (np.max(np.abs(x))+1e-9) * peak
    fade = min(len(x), int(0.004*SR)); x[-fade:] *= np.linspace(1,0,fade)
    with wave.open(f'sfx/{name}.wav','wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype(np.int16).tobytes())
def sweep(f0, f1, dur, shape='exp'):
    n=int(dur*SR); t=np.arange(n)/SR
    f = f0*(f1/f0)**(t/dur) if shape=='exp' else np.linspace(f0,f1,n)
    return np.sin(2*np.pi*np.cumsum(f)/SR)
def lp(x, a):  # one-pole lowpass
    y=np.zeros_like(x); s=0.0
    for i,v in enumerate(x): s += a*(v-s); y[i]=s
    return y
def bp_noise(dur, f0, f1, q=6):
    n=int(dur*SR); x=rng.standard_normal(n); y=np.zeros(n)
    # time-varying 2-pole resonator
    fs=f0*(f1/f0)**(np.arange(n)/n); r=1-np.pi*fs/(SR*q)*2
    y1=y2=0.0
    for i in range(n):
        th=2*np.pi*fs[i]/SR; yy=x[i]*(1-r[i]) + 2*r[i]*np.cos(th)*y1 - r[i]*r[i]*y2
        y2=y1; y1=yy; y[i]=yy
    return y
# pop: bubbly pitch drop
def pop(f0=700, f1=260, dur=0.09):
    x = sweep(f0,f1,dur)*env_exp(int(dur*SR), dur/3.5)
    click = rng.standard_normal(int(0.004*SR))*np.linspace(1,0,int(0.004*SR))*0.25
    x[:len(click)] += click; return x
save('pop', pop()); save('pop_hi', pop(1100,480,0.07)); save('pop_lo', pop(420,150,0.12))
save('pop_big', np.concatenate([pop(520,120,0.16)]) )
# tick for words
t = rng.standard_normal(int(0.012*SR))*env_exp(int(0.012*SR),0.002); save('tick', np.diff(np.concatenate([[0],t])), 0.7)
# whoosh
n=int(0.38*SR); w = bp_noise(0.38, 300, 2600, q=2.5); e=np.sin(np.linspace(0,np.pi,n))**2.2; save('whoosh', w*e, 0.8)
n=int(0.22*SR); w = bp_noise(0.22, 700, 3500, q=2.5); e=np.sin(np.linspace(0,np.pi,n))**2; save('swish', w*e, 0.8)
# boom / impact
n=int(0.5*SR); b = sweep(95,38,0.5)*env_exp(n,0.14); nz = lp(rng.standard_normal(n),0.08)*env_exp(n,0.03)
save('boom', b+0.5*nz)
# stamp: thud + paper slap
n=int(0.18*SR); th = sweep(160,70,0.18)*env_exp(n,0.04); sl = rng.standard_normal(n)*env_exp(n,0.012)
save('stamp', th+0.35*sl)
# ding bell
def bell(f, dur=1.0, parts=((1,1),(2.76,0.4),(5.4,0.2),(8.9,0.08))):
    n=int(dur*SR); t=np.arange(n)/SR; x=np.zeros(n)
    for m,a in parts: x += a*np.sin(2*np.pi*f*m*t)*np.exp(-t*(3+m*1.5))
    x[:int(0.002*SR)] *= np.linspace(0,1,int(0.002*SR)); return x
save('ding', bell(1318.5, 1.1), 0.8)
# ka-ching: click + two bells
n=int(0.9*SR); x=np.zeros(n)
cl = rng.standard_normal(int(0.03*SR))*env_exp(int(0.03*SR),0.006); x[:len(cl)] += 0.6*cl
b1 = bell(2093,0.8); b2 = bell(2637,0.75); o=int(0.07*SR); x[o:o+len(b1)] += 0.7*b1[:n-o]; o2=int(0.13*SR); x[o2:o2+len(b2)] += 0.8*b2[:n-o2]
save('kaching', x, 0.85)
# buzzer (wrong): two short low square-ish tones
def sq(f,dur):
    n=int(dur*SR); t=np.arange(n)/SR; s=np.tanh(4*np.sin(2*np.pi*f*t)); e=np.ones(n); a=int(0.008*SR); e[:a]=np.linspace(0,1,a); e[-a:]=np.linspace(1,0,a); return lp(s*e,0.25)
bz = np.concatenate([sq(155,0.13), np.zeros(int(0.05*SR)), sq(140,0.2)]); save('buzzer', bz, 0.6)
# sparkle
n=int(0.6*SR); x=np.zeros(n)
for k in range(9):
    o=int(rng.uniform(0,0.4)*SR); f=rng.uniform(2400,5200); d=int(0.12*SR)
    tt=np.arange(d)/SR; x[o:o+d] += np.sin(2*np.pi*f*tt)*np.exp(-tt*30)*rng.uniform(0.4,1)
save('sparkle', x, 0.6)
# printer ticks (receipt)
n=int(0.05*SR); x = rng.standard_normal(n)*env_exp(n,0.006); save('print', np.diff(np.concatenate([[0],x])), 0.6)
# heart bloop (soft, two-tone)
x = np.concatenate([pop(380,620,0.11)*0.9, pop(520,820,0.12)]); save('bloop', x, 0.8)
# riser for end card
n=int(0.55*SR); w = bp_noise(0.55, 400, 4000, q=3); e=(np.linspace(0,1,n)**2.5); e[-int(0.03*SR):]*=np.linspace(1,0,int(0.03*SR)); save('riser', w*e, 0.7)
print('ok')
