"""Builds index.html (scene graph + animation engine) and sfx_events.json from the timeline."""
import json

T = json.load(open('timing.json', encoding='utf-8'))
W = T['words']
DUR = T['duration']
LEAD = 0.04  # words appear slightly before they are spoken

BG, ESP, CREAM, ROSE_D, ROSE_L = '#BD9484', '#2A1711', '#FFF3E4', '#9E6E5E', '#D9BBAE'

els = []   # element dicts consumed by the JS engine
html = []  # markup
sfx = []   # {t, name, gain}
punch = []  # stage punch times


def wt(i):
    return round(W[i]['s'] - LEAD, 3)


def add(e, markup):
    els.append(e)
    html.append(markup)


def S(t, name, gain=1.0):
    sfx.append(dict(t=round(t, 3), name=name, gain=gain))


# ---------- SVG helpers ----------
def svg_circle(color):
    return f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="{color}"/></svg>'


def svg_burst(color, n=18, inner=0.8):
    import math
    pts = []
    for k in range(2 * n):
        r = 50 if k % 2 == 0 else 50 * inner
        a = math.pi * k / n
        pts.append(f'{50 + r * math.cos(a):.2f},{50 + r * math.sin(a):.2f}')
    return f'<svg viewBox="0 0 100 100"><polygon points="{" ".join(pts)}" fill="{color}"/></svg>'


def svg_blob(color):
    return ('<svg viewBox="0 0 200 200"><path fill="%s" d="M43.5,-58.9C55.2,-50.1,62.8,-36,67.4,-20.9C72,-5.8,73.6,10.3,68.3,24.1C63,37.9,50.8,49.4,36.9,57.7C23,66,7.4,71.1,-9.4,72.4C-26.2,73.7,-44.2,71.2,-56.3,61.1C-68.4,51,-74.6,33.3,-76.3,15.8C-78,-1.7,-75.2,-19,-66.6,-32.3C-58,-45.6,-43.6,-54.9,-29.4,-62.8C-15.2,-70.7,-1.2,-77.2,12.3,-74.6C25.8,-72,31.8,-67.7,43.5,-58.9Z" transform="translate(100 100) scale(1.3)"/></svg>' % color)


def svg_ring(color):
    return (f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="47" fill="none" stroke="{color}" '
            f'stroke-width="2.2" stroke-dasharray="6 5" stroke-linecap="round"/></svg>')


ICON = {
    'house': f'<svg viewBox="0 0 100 100"><rect x="4" y="4" width="92" height="92" rx="24" fill="{CREAM}"/>'
             f'<path d="M22 50 L50 26 L78 50" fill="none" stroke="{ESP}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<path d="M31 45 V76 H69 V45" fill="none" stroke="{ESP}" stroke-width="8" stroke-linejoin="round"/>'
             f'<rect x="44" y="56" width="12" height="20" fill="{ESP}"/></svg>',
    'qmark': f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="{ESP}"/>'
             f'<text x="50" y="73" text-anchor="middle" font-family="Lalezar" font-size="72" fill="{CREAM}">؟</text></svg>',
    'xmark': f'<svg viewBox="0 0 100 100"><g stroke-linecap="round">'
             f'<path d="M18 18 L82 82 M82 18 L18 82" stroke="{CREAM}" stroke-width="22"/>'
             f'<path d="M18 18 L82 82 M82 18 L18 82" stroke="{ESP}" stroke-width="13"/></g></svg>',
    'check': f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="{ESP}" stroke="{CREAM}" stroke-width="4"/>'
             f'<path d="M28 52 L44 67 L73 34" fill="none" stroke="{CREAM}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'heart': f'<svg viewBox="0 0 100 100"><path d="M50 88 C18 64 6 48 6 31 C6 17 17 7 30 7 C39 7 46 12 50 20 C54 12 61 7 70 7 C83 7 94 17 94 31 C94 48 82 64 50 88Z" '
             f'fill="{ESP}" stroke="{CREAM}" stroke-width="5" stroke-linejoin="round"/></svg>',
    'heart_c': f'<svg viewBox="0 0 100 100"><path d="M50 88 C18 64 6 48 6 31 C6 17 17 7 30 7 C39 7 46 12 50 20 C54 12 61 7 70 7 C83 7 94 17 94 31 C94 48 82 64 50 88Z" '
               f'fill="{CREAM}" stroke="{ESP}" stroke-width="5" stroke-linejoin="round"/></svg>',
    'spark': f'<svg viewBox="0 0 100 100"><path d="M50 2 C54 38 62 46 98 50 C62 54 54 62 50 98 C46 62 38 54 2 50 C38 46 46 38 50 2Z" fill="{CREAM}"/></svg>',
    'spark_e': f'<svg viewBox="0 0 100 100"><path d="M50 2 C54 38 62 46 98 50 C62 54 54 62 50 98 C46 62 38 54 2 50 C38 46 46 38 50 2Z" fill="{ESP}"/></svg>',
    'arrow_up': f'<svg viewBox="0 0 100 100"><path d="M50 10 L50 88 M22 38 L50 10 L78 38" fill="none" stroke="{ESP}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'bean': f'<svg viewBox="0 0 100 100"><ellipse cx="50" cy="50" rx="30" ry="42" fill="{ESP}" transform="rotate(25 50 50)"/>'
            f'<path d="M40 16 C60 36 38 62 58 86" fill="none" stroke="{CREAM}" stroke-width="6" stroke-linecap="round" transform="rotate(25 50 50)"/></svg>',
}

SOC = {
    'link': f'<svg viewBox="0 0 24 24"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" fill="none" stroke="{CREAM}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" fill="none" stroke="{CREAM}" stroke-width="2.4" stroke-linecap="round"/></svg>',
    'tiktok': f'<svg viewBox="0 0 24 24"><path fill="{ESP}" d="M16.6 2h-3.2v13.1a2.9 2.9 0 1 1-2.9-2.9c.3 0 .6 0 .9.1V9a6.1 6.1 0 1 0 5.2 6V8.5a7.6 7.6 0 0 0 4.4 1.4V6.7A4.4 4.4 0 0 1 16.6 2z"/></svg>',
    'insta': f'<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="5.5" fill="none" stroke="{ESP}" stroke-width="2.3"/>'
             f'<circle cx="12" cy="12" r="4.2" fill="none" stroke="{ESP}" stroke-width="2.3"/><circle cx="17.4" cy="6.6" r="1.4" fill="{ESP}"/></svg>',
    'whats': f'<svg viewBox="0 0 24 24"><path fill="{ESP}" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2z"/>'
             f'<path fill="{ESP}" d="M16.6 14.2c-.3-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a.9.9 0 0 0-.7.3 2.8 2.8 0 0 0-.9 2.1 4.9 4.9 0 0 0 1 2.6 11.2 11.2 0 0 0 4.3 3.8c1.6.7 2.2.7 3 .6a2.5 2.5 0 0 0 1.7-1.2 2 2 0 0 0 .1-1.2c0-.1-.2-.2-.4-.3z"/></svg>',
    'phone': f'<svg viewBox="0 0 24 24"><path fill="{ESP}" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.2 11.4 11.4 0 0 0 3.6.6 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.2.2 2.5.6 3.6a1 1 0 0 1-.3 1z"/></svg>',
}


# ---------- element builders ----------
_id = [0]


def nid(p):
    _id[0] += 1
    return f'{p}{_id[0]}'


def item(inner, t0, t1, cx, cy, w, rot=0, z=10, anim='pop', d=None, idle=None, kf=None, cls='', sfx_name=None, gain=1.0, out=None, style=''):
    i = nid('e')
    e = dict(id=i, t0=round(t0, 3), t1=round(t1, 3), cx=cx, cy=cy, w=w, rot=rot, anim=anim, idle=idle or [], kf=kf or [], out=out)
    if d is not None:
        e['d'] = d
    add(e, f'<div id="{i}" class="it {cls}" style="width:{w}px;z-index:{z};{style}">{inner}</div>')
    if sfx_name:
        S(t0, sfx_name, gain)
    return i


def img(src, *a, shadow=True, **k):
    cls = k.pop('cls', '') + (' sh' if shadow else '')
    return item(f'<img src="{src}">', *a, cls=cls, **k)


def frame(src, t0, t1, cx, cy, w, h, rot=0, **k):
    inner = f'<div class="frame" style="height:{h}px"><img src="{src}"></div>'
    return item(inner, t0, t1, cx, cy, w, rot=rot, cls='sh', **k)


def shape(svg, t0, t1, cx, cy, w, rot=0, z=2, **k):
    return item(svg, t0, t1, cx, cy, w, rot=rot, z=z, **k)


def line(t1, cy, words, size=112, z=40, gap=26):
    """words: list of (text, t0, style) style in {'n','tag','cr'}"""
    lid = nid('l')
    spans = []
    for (txt, t0, st) in words:
        wid = nid('w')
        els.append(dict(id=wid, t0=round(t0, 3), t1=round(t1, 3), inline=True, anim='word', idle=[]))
        spans.append(f'<span id="{wid}" class="w {st}">{txt}</span>')
        S(t0, 'tick', 0.35)
    els.append(dict(id=lid, t0=min(w[1] for w in words), t1=round(t1, 3), cx=540, cy=cy, w=1080, rot=0, anim='none', idle=[], kf=[]))
    html.append(f'<div id="{lid}" class="it line" style="width:1080px;z-index:{z};font-size:{size}px;gap:{gap}px">{"".join(spans)}</div>')


def stamp_card(ar, en, t0, t1, cx, cy, rot, sfxn='stamp'):
    inner = (f'<div class="stamp"><svg class="perf" viewBox="0 0 290 210" preserveAspectRatio="none">'
             f'<defs><mask id="m{cx}{cy}"><rect width="290" height="210" fill="#fff"/>'
             + ''.join(f'<circle cx="{x}" cy="0" r="7" fill="#000"/><circle cx="{x}" cy="210" r="7" fill="#000"/>' for x in range(5, 291, 20))
             + ''.join(f'<circle cx="0" cy="{y}" r="7" fill="#000"/><circle cx="290" cy="{y}" r="7" fill="#000"/>' for y in range(5, 211, 20))
             + f'</mask></defs><rect width="290" height="210" fill="{CREAM}" mask="url(#m{cx}{cy})"/>'
             f'<rect x="18" y="18" width="254" height="174" rx="6" fill="none" stroke="{ESP}" stroke-width="3" stroke-dasharray="7 6"/></svg>'
             f'<div class="st-in"><div class="st-ar">{ar}</div><div class="st-en">{en}</div></div>'
             f'<div class="st-bean">{ICON["bean"]}</div></div>')
    return item(inner, t0, t1, cx, cy, 290, rot=rot, z=30, anim='stamp', cls='sh', sfx_name=sfxn, gain=0.9)


# =====================================================================
# SCENES
# =====================================================================
SC = [0.0, 1.95, 3.42, 4.62, 7.18, 9.68, 11.82, 12.92, 15.22, 16.62, 18.72, 20.40, DUR + 0.5]
L1, L2 = 1296, 1440

# logo: always visible, small top-centre; grows into the end card
img('assets/logo_espresso.png', -0.2, SC[11], 540, 236, 140, z=90, anim='pop', d=0.35, shadow=False)
logo_kf = [dict(t=SC[11], cx=540, cy=236, w=140), dict(t=SC[11] + 0.42, cx=540, cy=560, w=300, ease='back')]
img('assets/logo_cream.png', SC[11], DUR + 1, 540, 236, 140, z=90, anim='none', kf=logo_kf, shadow=False)

# --- S1 hook: 0.00 - 1.95
s0, s1 = SC[0], SC[1]
shape(svg_blob(ROSE_L), s0 - 0.2, s1, 560, 720, 820, rot=10, idle=[dict(type='spin', rate=6)])
frame('assets/pourover.jpg', s0 - 0.14, s1, 540, 715, 580, 632, rot=-3, anim='pop', d=0.34,
      idle=[dict(type='zoom', rate=0.025), dict(type='float', amp=6, freq=0.6)], sfx_name='whoosh', gain=0.8)
S(0.10, 'pop_big', 0.8)
item(ICON['qmark'], 1.30, s1, 845, 420, 170, rot=12, z=35, anim='popRot', idle=[dict(type='wiggle', amp=7, freq=2.2)], sfx_name='pop_hi', gain=0.9)
item(ICON['house'], wt(4) + 0.02, s1, 250, 1060, 170, rot=-10, z=35, anim='popRot', idle=[dict(type='float', amp=8, freq=1.2)], sfx_name='pop', gain=0.9)
line(s1, L1, [('إذا', wt(0), 'n'), ('تسوي', wt(1), 'n'), ('قهوتك', wt(2), 'cr')])
line(s1, L2, [('في', wt(3), 'n'), ('البيت؟', wt(4), 'tag')], size=124)

# --- S2 "هذا الفيديو لك": 1.95 - 3.42
s0, s1 = SC[1], SC[2]
shape(svg_burst(ESP), s0, s1, 560, 730, 780, idle=[dict(type='spin', rate=14)], anim='pop', d=0.3)
img('assets/pointing_ht.png', s0, s1, 545, 752, 415, anim='slideU', d=0.3,
    idle=[dict(type='zoom', rate=0.025)], sfx_name='whoosh', gain=0.9)
item(ICON['spark'], wt(7), s1, 215, 470, 120, rot=0, z=35, anim='popRot', idle=[dict(type='spin', rate=40)])
item(ICON['spark'], wt(7) + 0.06, s1, 880, 1080, 90, rot=0, z=35, anim='popRot', idle=[dict(type='spin', rate=-50)])
line(s1, L1, [('هذا', wt(5), 'n'), ('الفيديو', wt(6), 'n')], size=108)
line(s1, L2, [('لك!', wt(7), 'tag')], size=150)
S(wt(7), 'boom', 0.9)
punch.append(wt(7) + 0.02)

# --- S3 "حنا كلوفا": 3.42 - 4.62
s0, s1 = SC[2], SC[3]
shape(svg_circle(CREAM), s0, s1, 540, 760, 700, anim='pop', d=0.22, idle=[dict(type='zoom', rate=0.03)])
shape(svg_ring(ESP), s0 + 0.05, s1, 540, 760, 790, anim='pop', d=0.34, idle=[dict(type='spin', rate=-18)], z=3)
img('assets/bag_klova.png', s0, s1, 540, 765, 400, rot=-4, anim='popRot', d=0.36,
    idle=[dict(type='float', amp=10, freq=0.9), dict(type='wiggle', amp=2, freq=0.9)], sfx_name='pop_big', gain=1.0)
item(ICON['spark_e'], wt(9), s1, 250, 520, 110, z=35, anim='popRot', idle=[dict(type='spin', rate=60)])
item(ICON['spark_e'], wt(9) + 0.07, s1, 835, 980, 80, z=35, anim='popRot', idle=[dict(type='spin', rate=-60)])
item(ICON['spark_e'], wt(9) + 0.12, s1, 850, 470, 60, z=35, anim='popRot', idle=[dict(type='spin', rate=70)])
S(wt(9), 'sparkle', 0.8)
line(s1, 1330, [('حنّا', wt(8), 'n'), ('كلوفا', wt(9), 'tag')], size=140)

# --- S4 "متجر متخصص في محاصيل القهوة": 4.62 - 7.18
s0, s1 = SC[3], SC[4]
shape(svg_blob(ROSE_L), s0, s1, 600, 640, 860, rot=-20, idle=[dict(type='spin', rate=-5)])
frame('assets/farmer.jpg', s0, s1, 575, 600, 690, 518, rot=3, anim='slideL', d=0.3,
      idle=[dict(type='drift', vx=-8, vy=0), dict(type='zoom', rate=0.012)], sfx_name='whoosh', gain=0.9)
frame('assets/beans.jpg', wt(13), s1, 285, 1010, 360, 360, rot=-8, anim='popRot', d=0.32,
      idle=[dict(type='float', amp=7, freq=0.8)], sfx_name='pop', gain=1.0)
item(ICON['bean'], wt(14), s1, 860, 1010, 130, rot=20, z=35, anim='popRot', idle=[dict(type='wiggle', amp=10, freq=1.5)], sfx_name='pop_hi', gain=0.7)
item(ICON['bean'], wt(14) + 0.08, s1, 760, 1120, 80, rot=-30, z=35, anim='popRot', idle=[dict(type='wiggle', amp=12, freq=1.8)])
line(s1, L1, [('متجر', wt(10), 'n'), ('متخصص', wt(11), 'tag')], size=112)
line(s1, L2, [('في', wt(12), 'n'), ('محاصيل', wt(13), 'cr'), ('القهوة', wt(14), 'cr')], size=112)

# --- S5 "والفرق غالباً مو في المكينة": 7.18 - 9.68
s0, s1 = SC[4], SC[5]
shape(svg_blob(ROSE_D), s0, s1, 540, 750, 800, rot=40, idle=[dict(type='spin', rate=5)], anim='pop', d=0.3)
X_T = wt(17)
img('assets/espresso_ht.png', s0, s1, 540, 760, 600, rot=-3, anim='slideR', d=0.3,
    idle=[dict(type='float', amp=6, freq=0.7), dict(type='shake', t=X_T, amp=16, dur=0.35)], sfx_name='whoosh', gain=0.9)
item(ICON['xmark'], X_T, s1, 575, 735, 430, rot=-6, z=45, anim='stamp', d=0.16, sfx_name='buzzer', gain=0.9)
S(X_T, 'stamp', 1.0)
punch.append(X_T + 0.02)
line(s1, L1, [('والفرق', wt(15), 'tag')], size=124)
line(s1, L2, [('غالباً', wt(16), 'n'), ('مو', wt(17), 'cr'), ('في', wt(18), 'n'), ('المكينة', wt(19) + 0.03, 'n')], size=104, gap=22)

# --- S6 "الفرق في المحصول نفسه": 9.68 - 11.82
s0, s1 = SC[5], SC[6]
shape(svg_burst(CREAM, n=22, inner=0.84), s0, s1, 540, 745, 800, anim='pop', d=0.22, idle=[dict(type='spin', rate=12)])
img('assets/sack.png', s0, s1, 540, 770, 620, rot=2, anim='popRot', d=0.36,
    idle=[dict(type='zoom', rate=0.035), dict(type='float', amp=6, freq=0.8)], sfx_name='pop_big', gain=1.0)
S(s0, 'swish', 0.7)
CH_T = wt(23)
item(ICON['check'], CH_T, s1, 840, 470, 200, rot=-8, z=45, anim='stamp', d=0.16, sfx_name='ding', gain=0.8)
S(CH_T, 'stamp', 0.7)
punch.append(CH_T + 0.02)
line(s1, L1, [('الفرق', wt(20), 'tag')], size=124)
line(s1, L2, [('في', wt(21), 'n'), ('المحصول', wt(22), 'n'), ('نفسه', CH_T, 'cr')], size=112)

# --- S7 "عشان كذا" (globe) 11.82 - 12.92 ; globe continues through S8
s0, s1 = SC[6], SC[7]
shape(svg_ring(CREAM), s0, SC[8], 540, 760, 740, anim='pop', d=0.34, z=3,
      idle=[dict(type='spin', rate=30)], kf=[dict(t=s1, cx=540, cy=760, w=740), dict(t=s1 + 0.3, cx=540, cy=780, w=470)])
shape(svg_circle(ROSE_L), s0, SC[8], 540, 760, 640, anim='pop', d=0.22, z=2,
      kf=[dict(t=s1, cx=540, cy=760, w=640), dict(t=s1 + 0.3, cx=540, cy=780, w=400)])
img('assets/globe_ht.png', s0, SC[8], 540, 765, 470, rot=-6, anim='popRot', d=0.36,
    idle=[dict(type='wiggle', amp=5, freq=0.9)], kf=[dict(t=s1, cx=540, cy=765, w=470), dict(t=s1 + 0.3, cx=540, cy=785, w=300)],
    sfx_name='whoosh', gain=0.9)
S(s0 + 0.08, 'pop', 0.8)
line(s1, 1330, [('عشان', wt(24), 'n'), ('كذا', wt(25), 'tag')], size=140)

# --- S8 origins: 12.92 - 15.22
s0, s1 = SC[7], SC[8]
stamp_card('إثيوبيا', 'ETHIOPIA', wt(27), s1, 240, 470, -8)
stamp_card('كولومبيا', 'COLOMBIA', wt(28), s1, 840, 480, 7)
stamp_card('البرازيل', 'BRAZIL', wt(29) + 0.02, s1, 215, 900, 6)
stamp_card('اليمن', 'YEMEN', wt(30), s1, 865, 915, -6)
stamp_card('كينيا', 'KENYA', wt(32) - 0.06, s1, 540, 1130, -3)
punch.append(wt(32))
line(s1, L1 + 40, [('نوفر', wt(26), 'n'), ('لك', wt(27), 'n'), ('محاصيل', wt(28), 'cr')], size=106)
line(s1, L2 + 50, [('من', wt(29), 'n'), ('أكثر', wt(30), 'n'), ('من', wt(31), 'n'), ('بلد', wt(32), 'tag')], size=106, gap=22)

# --- S9 flavours: 15.22 - 16.62
s0, s1 = SC[8], SC[9]
shape(svg_circle(CREAM), s0, s1, 540, 770, 520, anim='pop', d=0.22, idle=[dict(type='zoom', rate=0.04)])
img('assets/bag_klova.png', s0, s1, 540, 775, 300, rot=4, anim='popRot', d=0.32,
    idle=[dict(type='float', amp=8, freq=1.0)], sfx_name='pop_big', gain=0.9)
img('assets/strawberry.png', wt(34), s1, 225, 520, 250, rot=-12, anim='popRot', idle=[dict(type='float', amp=9, freq=1.1)], sfx_name='pop', gain=0.9)
img('assets/chocolate.png', wt(35), s1, 830, 560, 340, rot=10, anim='popRot', idle=[dict(type='float', amp=8, freq=0.9)], sfx_name='pop_hi', gain=0.9)
img('assets/orange.png', wt(36), s1, 250, 1010, 270, rot=8, anim='popRot', idle=[dict(type='spin', rate=12)], sfx_name='pop', gain=0.9)
item('<div class="lbl">توتي</div>', wt(34) + 0.08, s1, 230, 690, 220, rot=-6, z=36, anim='pop', d=0.22)
item('<div class="lbl">شوكولاتة</div>', wt(35) + 0.08, s1, 835, 720, 300, rot=5, z=36, anim='pop', d=0.22)
item('<div class="lbl">حمضي</div>', wt(36) + 0.08, s1, 250, 1175, 220, rot=4, z=36, anim='pop', d=0.22)
item(ICON['spark_e'], wt(36) + 0.1, s1, 850, 1040, 100, z=35, anim='popRot', idle=[dict(type='spin', rate=50)])
S(wt(36) + 0.1, 'sparkle', 0.6)
line(s1, L1, [('كل', wt(33), 'n'), ('واحد', wt(34), 'n')], size=118)
line(s1, L2, [('له', wt(35), 'n'), ('طعمه', wt(36), 'tag')], size=124)

# --- S10 cafes: 16.62 - 18.72
s0, s1 = SC[9], SC[10]
shape(svg_blob(ROSE_L), s0, s1, 470, 760, 820, rot=-30, idle=[dict(type='spin', rate=-6)])
img('assets/takeaway_ht.png', s0, s1, 315, 770, 360, rot=-7, anim='slideL', d=0.3,
    idle=[dict(type='wiggle', amp=3, freq=1.2)], sfx_name='whoosh', gain=0.9)
rc_lines = ''.join(f'<div class="rl" id="rl{k}"><span>لاتيه</span><i></i><span>٢٤</span></div>' for k in range(6))
receipt = (f'<div class="receipt"><div class="rh">فاتورة الكوفي</div>{rc_lines}'
           f'<div class="rt" id="rtot"><span>كل يوم!</span></div></div>')
rid = item(receipt, s0 + 0.12, s1, 765, 705, 400, rot=5, z=20, anim='slideD', d=0.32, idle=[dict(type='float', amp=5, freq=0.7)], sfx_name='swish', gain=0.7)
for k in range(6):
    tk = s0 + 0.42 + k * 0.2
    els.append(dict(id=f'rl{k}', t0=round(tk, 3), t1=s1, inline=True, anim='print', idle=[]))
    S(tk, 'print', 0.6)
els.append(dict(id='rtot', t0=wt(40), t1=s1, inline=True, anim='stampInline', idle=[]))
S(wt(39), 'kaching', 0.85)
S(wt(40), 'stamp', 0.8)
punch.append(wt(40) + 0.02)
line(s1, L1, [('بدون', wt(37), 'n'), ('ما', wt(38), 'n'), ('تدفع', wt(39), 'cr')], size=112)
line(s1, L2, [('كل', wt(40), 'tag'), ('يوم', wt(41), 'tag'), ('في', wt(42), 'n'), ('الكوفيات', wt(43), 'n')], size=100, gap=20)

# --- S11 closing: 18.72 - 20.40
s0, s1 = SC[10], SC[11]
shape(svg_circle(CREAM), s0, s1, 540, 760, 700, anim='pop', d=0.22, idle=[dict(type='zoom', rate=0.03)])
img('assets/latte.png', s0, s1, 540, 760, 580, anim='popRot', d=0.36, idle=[dict(type='spin', rate=9)], sfx_name='pop_big', gain=0.9)
S(s0, 'swish', 0.6)
HT = wt(48)
item(ICON['heart'], HT, s1, 800, 470, 250, rot=12, z=45, anim='popRot', d=0.3, idle=[dict(type='beat', freq=2.2, amp=0.08)], sfx_name='bloop', gain=0.9)
item(ICON['heart_c'], HT + 0.08, s1, 255, 1040, 130, rot=-14, z=45, anim='popRot', idle=[dict(type='beat', freq=2.2, amp=0.1)])
item(ICON['heart'], HT + 0.14, s1, 880, 1060, 90, rot=10, z=45, anim='popRot', idle=[dict(type='beat', freq=2.2, amp=0.1)])
S(HT + 0.05, 'sparkle', 0.7)
punch.append(HT + 0.02)
line(s1, L1, [('وبدون', wt(44), 'n'), ('ما', wt(45), 'n'), ('تتنازل', wt(46), 'n')], size=112)
line(s1, L2, [('عن', wt(47), 'n'), ('الطعم', HT, 'tag')], size=128)

# --- S12 end card: 20.40 - end
s0, s1 = SC[11], SC[12]
S(s0 - 0.5, 'riser', 0.5)
shape(svg_circle(ESP), s0, s1, 540, 560, 470, anim='pop', d=0.34, z=5, idle=[dict(type='zoom', rate=0.02)])
shape(svg_ring(ESP), s0 + 0.06, s1, 540, 560, 560, anim='pop', d=0.36, z=4, idle=[dict(type='spin', rate=20)])
S(s0, 'pop_big', 1.0)
S(s0, 'whoosh', 0.7)
rows = [
    (f'<div class="pill">{SOC["link"]}<span dir="ltr">salla.sa/klova.sa</span></div>', 1160, 560),
    (f'<div class="crow"><span dir="ltr">@klova.sa</span>{SOC["tiktok"]}{SOC["insta"]}</div>', 1266, 560),
    (f'<div class="crow"><span dir="ltr">053 927 5975</span>{SOC["whats"]}</div>', 1362, 560),
    (f'<div class="crow"><span dir="ltr">054 119 2777</span>{SOC["phone"]}</div>', 1458, 560),
]
for k, (m, y, wdt) in enumerate(rows):
    item(m, s0 + 0.24 + k * 0.12, s1, 540, y, wdt, z=50, anim='slideUp_s', d=0.3, sfx_name='pop_hi', gain=0.55)
item(ICON['arrow_up'], wt(53) + 0.05, s1, 905, 1010, 80, z=50, anim='pop', idle=[dict(type='bob', amp=12, freq=2.5)])
line(s1, 880, [('اختار', wt(49), 'n'), ('محصولك', wt(50), 'tag')], size=110)
line(s1, 1010, [('من', wt(51), 'n'), ('الرابط', wt(52), 'n'), ('بالبايو', wt(53), 'cr')], size=96, gap=20)
S(wt(53) + 0.05, 'ding', 0.6)

# =====================================================================
spec = dict(duration=DUR, elements=els, punch=punch, bg=BG)
json.dump(sorted(sfx, key=lambda x: x['t']), open('sfx_events.json', 'w'), indent=0)

CSS = f"""
@font-face{{font-family:'Lalezar';src:url(fonts/lalezar_zrfl0HLVx-HwTP82YaL4IxL0.woff2) format('woff2');unicode-range:U+0600-06FF,U+0750-077F,U+FB50-FDFF,U+FE70-FEFC,U+200C-200E;}}
@font-face{{font-family:'Lalezar';src:url(fonts/lalezar_zrfl0HLVx-HwTP82Yaf4Iw.woff2) format('woff2');unicode-range:U+0000-00FF,U+2000-206F;}}
@font-face{{font-family:'Cairo';font-weight:200 1000;src:url(fonts/cairo_SLXVc1nY6HkvangtZmpQdkhzfH5lkSscQyyS4J0.woff2) format('woff2');unicode-range:U+0600-06FF,U+0750-077F,U+FB50-FDFF,U+FE70-FEFC,U+200C-200E;}}
@font-face{{font-family:'Cairo';font-weight:200 1000;src:url(fonts/cairo_SLXVc1nY6HkvangtZmpQdkhzfH5lkSscRiyS.woff2) format('woff2');unicode-range:U+0000-00FF,U+2000-206F;}}
html,body{{margin:0;padding:0;background:{BG};}}
#stage{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{BG};}}
#content{{position:absolute;inset:0;transform-origin:540px 800px;}}
.it{{position:absolute;left:0;top:0;visibility:hidden;will-change:transform;}}
.it img{{display:block;width:100%;height:auto;}}
.it svg{{display:block;width:100%;height:auto;overflow:visible;}}
.sh{{filter:drop-shadow(0 14px 0 rgba(42,23,17,.18));}}
.frame{{width:100%;border-radius:40px;overflow:hidden;border:12px solid #FFF8EE;box-sizing:border-box;background:#FFF8EE;}}
.frame img{{width:100%;height:100%;object-fit:cover;}}
.line{{display:flex;justify-content:center;align-items:center;direction:rtl;font-family:'Lalezar';line-height:1.05;color:{ESP};}}
.w{{display:inline-block;visibility:hidden;white-space:nowrap;}}
.w.cr{{color:{CREAM};text-shadow:0.045em 0.055em 0 {ESP};}}
.w.tag{{color:{CREAM};background:{ESP};padding:0.02em 0.28em 0.1em;border-radius:0.2em;}}
.stamp{{position:relative;width:290px;height:210px;}}
.stamp .perf{{position:absolute;inset:0;width:100%;height:100%;}}
.st-in{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;}}
.st-ar{{font-family:'Lalezar';font-size:64px;line-height:1;color:{ESP};margin-top:-6px;}}
.st-en{{font-family:'Cairo';font-weight:800;font-size:21px;letter-spacing:.3em;color:{ESP};opacity:.8;margin-top:6px;}}
.st-bean{{position:absolute;width:44px;left:26px;top:22px;}}
.lbl{{font-family:'Lalezar';font-size:54px;color:{CREAM};background:{ESP};border-radius:18px;padding:2px 22px 8px;text-align:center;direction:rtl;width:max-content;margin:0 auto;}}
.receipt{{background:#FFF8EE;padding:26px 30px 44px;font-family:'Cairo';font-weight:800;color:{ESP};direction:rtl;
  clip-path:polygon(0 0,100% 0,100% calc(100% - 18px),95% 100%,90% calc(100% - 18px),85% 100%,80% calc(100% - 18px),75% 100%,70% calc(100% - 18px),65% 100%,60% calc(100% - 18px),55% 100%,50% calc(100% - 18px),45% 100%,40% calc(100% - 18px),35% 100%,30% calc(100% - 18px),25% 100%,20% calc(100% - 18px),15% 100%,10% calc(100% - 18px),5% 100%,0 calc(100% - 18px));}}
.rh{{font-family:'Lalezar';font-weight:400;font-size:46px;text-align:center;border-bottom:4px dashed {ESP};padding-bottom:8px;margin-bottom:10px;}}
.rl{{display:flex;align-items:center;gap:12px;font-size:34px;line-height:1.55;visibility:hidden;}}
.rl i{{flex:1;border-bottom:4px dotted {ESP};opacity:.55;height:0;margin-top:10px;}}
.rt{{margin-top:14px;text-align:center;visibility:hidden;}}
.rt span{{display:inline-block;font-family:'Lalezar';font-weight:400;font-size:56px;color:{CREAM};background:{ESP};padding:2px 26px 10px;border-radius:14px;transform:rotate(-4deg);}}
.pill{{display:flex;align-items:center;justify-content:center;gap:16px;background:{ESP};color:{CREAM};border-radius:60px;padding:12px 34px 18px;font-family:'Cairo';font-weight:800;font-size:48px;width:max-content;margin:0 auto;}}
.pill svg{{width:44px;height:44px;}}
.crow{{display:flex;align-items:center;justify-content:center;gap:16px;color:{ESP};font-family:'Cairo';font-weight:900;font-size:54px;width:max-content;margin:0 auto;}}
.crow svg{{width:50px;height:50px;}}
"""

JS = r"""
const SPEC = __SPEC__;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const eOutCubic=p=>1-Math.pow(1-p,3);
const eOutQuart=p=>1-Math.pow(1-p,4);
const eInOut=p=>p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2;
const eOutBack=(p,s=1.9)=>{const c3=s+1;return 1+c3*Math.pow(p-1,3)+s*Math.pow(p-1,2);};
const nodes={};
for(const e of SPEC.elements){nodes[e.id]=document.getElementById(e.id);}
function kfState(e,t){
  let cx=e.cx,cy=e.cy,w=e.w;
  const k=e.kf||[];
  if(k.length){
    if(t<=k[0].t){cx=k[0].cx;cy=k[0].cy;w=k[0].w;}
    else if(t>=k[k.length-1].t){const l=k[k.length-1];cx=l.cx;cy=l.cy;w=l.w;}
    else{for(let i=0;i<k.length-1;i++){const a=k[i],b=k[i+1];if(t>=a.t&&t<=b.t){let p=(t-a.t)/(b.t-a.t);p=(b.ease==='back')?eOutBack(p,1.4):eInOut(p);cx=a.cx+(b.cx-a.cx)*p;cy=a.cy+(b.cy-a.cy)*p;w=a.w+(b.w-a.w)*p;break;}}}
  }
  return {cx,cy,w};
}
function render(t){
  for(const e of SPEC.elements){
    const el=nodes[e.id];
    if(t<e.t0||t>=e.t1){el.style.visibility='hidden';continue;}
    el.style.visibility='visible';
    const lt=t-e.t0; const la=lt+(e.pre!==undefined?e.pre:(e.inline?0:0.07)); let s=1,op=1,tx=0,ty=0,r=0;
    const d=e.d||({pop:.3,popRot:.34,word:.2,slideL:.3,slideR:.3,slideU:.3,slideD:.32,stamp:.16,print:.12,stampInline:.18,slideUp_s:.3,none:0})[e.anim]||.3;
    const p=clamp(la/(d||1e-6),0,1);
    switch(e.anim){
      case 'pop': s=0.2+0.8*eOutBack(p); op=clamp(la/.04,0,1); break;
      case 'popRot': s=0.2+0.8*eOutBack(p); r=-18*(1-eOutCubic(p)); op=clamp(la/.04,0,1); break;
      case 'word': s=0.45+0.55*eOutBack(p,2.4); ty=26*(1-eOutCubic(p)); op=clamp(lt/.05,0,1); break;
      case 'slideL': tx=-1150*(1-eOutBack(p,1.2)); break;
      case 'slideR': tx=1150*(1-eOutBack(p,1.2)); break;
      case 'slideU': ty=1300*(1-eOutBack(p,1.15)); break;
      case 'slideD': ty=-1300*(1-eOutBack(p,1.15)); break;
      case 'slideUp_s': ty=90*(1-eOutCubic(p)); op=clamp(lt/.12,0,1); s=0.85+0.15*eOutBack(p); break;
      case 'stamp': s=1+1.1*(1-eOutCubic(p)); op=clamp(lt/.05,0,1); break;
      case 'stampInline': s=1+0.9*(1-eOutCubic(p)); op=clamp(lt/.05,0,1); break;
      case 'print': op=clamp(lt/.06,0,1); ty=-10*(1-p); break;
    }
    for(const idl of (e.idle||[])){
      switch(idl.type){
        case 'zoom': s*=1+idl.rate*lt; break;
        case 'float': ty+=idl.amp*Math.sin(2*Math.PI*idl.freq*lt); break;
        case 'bob': ty+=-Math.abs(idl.amp*Math.sin(Math.PI*idl.freq*lt)); break;
        case 'wiggle': r+=idl.amp*Math.sin(2*Math.PI*idl.freq*lt); break;
        case 'spin': r+=idl.rate*lt; break;
        case 'drift': tx+=idl.vx*lt; ty+=idl.vy*lt; break;
        case 'beat': {const ph=(lt*idl.freq)%1; s*=1+idl.amp*Math.exp(-ph*9)*Math.sin(Math.PI*Math.min(1,ph*6));} break;
        case 'shake': {const q=t-idl.t; if(q>0&&q<idl.dur){const a=idl.amp*(1-q/idl.dur); tx+=a*Math.sin(q*95); r+=a*0.15*Math.sin(q*70);} } break;
      }
    }
    el.style.opacity=op;
    if(e.inline){ el.style.transform=`translate(${tx}px,${ty}px) rotate(${r}deg) scale(${s})`; continue; }
    const k=kfState(e,t);
    if(k.w!==e._w){ el.style.width=k.w+'px'; e._w=k.w; }
    el.style.transform=`translate(${k.cx}px,${k.cy}px) translate(-50%,-50%) translate(${tx}px,${ty}px) rotate(${(e.rot||0)+r}deg) scale(${s})`;
  }
  let ps=1;
  for(const pt of SPEC.punch){const q=t-pt; if(q>=0&&q<.28){ps=Math.max(ps,1+0.045*Math.sin(Math.PI*q/.28));}}
  document.getElementById('content').style.transform=`scale(${ps})`;
}
window.render=render;
render(0);
"""

page = f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><title>KLOVA coffee</title><style>{CSS}</style></head>
<body><div id="stage"><div id="content">{''.join(html)}</div></div>
<script>{JS.replace('__SPEC__', json.dumps(spec, ensure_ascii=False))}</script></body></html>"""
open('index.html', 'w', encoding='utf-8').write(page)
print('elements', len(els), 'sfx', len(sfx), 'duration', DUR)
