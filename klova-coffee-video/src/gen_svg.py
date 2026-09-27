# Generates all illustrated collage assets as SVG (rasterized later by raster.js)
import os, math, random
OUT = os.path.join(os.path.dirname(__file__), 'svg')
os.makedirs(OUT, exist_ok=True)

CREAM = '#F1E6D2'; PAPER = '#FBF4E6'; KRAFT = '#C99B6D'; KRAFT_D = '#A87A4E'
ESP = '#24150E'; ROAST = '#6E3B22'; ORANGE = '#FF5B2E'; YELLOW = '#FFC93C'
OL = f'stroke="{ESP}" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"'


def save(name, w, h, body):
    with open(os.path.join(OUT, name + '.svg'), 'w') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>')


# ---------------------------------------------------------------- mug
save('mug', 640, 600, f'''
<defs><clipPath id="b"><path d="M120 170 L460 170 L440 470 Q435 520 385 520 L195 520 Q145 520 140 470 Z"/></clipPath></defs>
<ellipse cx="290" cy="528" rx="240" ry="44" fill="{CREAM}" {OL}/>
<ellipse cx="290" cy="520" rx="150" ry="20" fill="{KRAFT}" opacity=".6"/>
<path d="M445 245 C590 235 590 430 425 420" fill="none" stroke="{ESP}" stroke-width="66" stroke-linecap="round"/>
<path d="M445 245 C590 235 590 430 425 420" fill="none" stroke="{ORANGE}" stroke-width="44" stroke-linecap="round"/>
<path d="M120 170 L460 170 L440 470 Q435 520 385 520 L195 520 Q145 520 140 470 Z" fill="{ORANGE}"/>
<g clip-path="url(#b)">
  <rect x="100" y="300" width="400" height="70" fill="{CREAM}"/>
  <rect x="100" y="300" width="400" height="8" fill="{ESP}"/><rect x="100" y="362" width="400" height="8" fill="{ESP}"/>
  <rect x="160" y="190" width="34" height="300" rx="17" fill="#fff" opacity=".28"/>
</g>
<text x="292" y="352" font-family="Anton" font-size="44" letter-spacing="10" text-anchor="middle" fill="{ESP}">KLOVA</text>
<path d="M120 170 L460 170 L440 470 Q435 520 385 520 L195 520 Q145 520 140 470 Z" fill="none" {OL}/>
<ellipse cx="290" cy="170" rx="172" ry="40" fill="{CREAM}" {OL}/>
<ellipse cx="290" cy="174" rx="146" ry="28" fill="{ROAST}"/>
<ellipse cx="250" cy="168" rx="50" ry="8" fill="#9A5A36" opacity=".8"/>
''')

# ---------------------------------------------------------------- house
save('house', 820, 820, f'''
<rect x="560" y="120" width="80" height="170" fill="{ROAST}" {OL}/>
<rect x="545" y="100" width="110" height="40" fill="{ESP}"/>
<rect x="150" y="360" width="520" height="400" fill="{KRAFT}" {OL}/>
<g opacity=".25" stroke="{ESP}" stroke-width="4">
  <line x1="150" y1="440" x2="670" y2="440"/><line x1="150" y1="520" x2="670" y2="520"/><line x1="150" y1="600" x2="670" y2="600"/><line x1="150" y1="680" x2="670" y2="680"/>
</g>
<path d="M80 390 L410 110 L740 390 Z" fill="{ORANGE}" {OL}/>
<path d="M150 360 L410 150 L670 360" fill="none" stroke="{ESP}" stroke-width="6" opacity=".35"/>
<rect x="360" y="530" width="120" height="230" rx="8" fill="{ROAST}" {OL}/>
<circle cx="455" cy="650" r="9" fill="{YELLOW}"/>
<rect x="200" y="470" width="120" height="120" fill="{YELLOW}" {OL}/>
<line x1="260" y1="470" x2="260" y2="590" stroke="{ESP}" stroke-width="8"/><line x1="200" y1="530" x2="320" y2="530" stroke="{ESP}" stroke-width="8"/>
<rect x="530" y="470" width="100" height="100" fill="{YELLOW}" {OL}/>
<line x1="580" y1="470" x2="580" y2="570" stroke="{ESP}" stroke-width="8"/><line x1="530" y1="520" x2="630" y2="520" stroke="{ESP}" stroke-width="8"/>
<rect x="130" y="752" width="560" height="26" rx="6" fill="{ESP}"/>
''')

# ---------------------------------------------------------------- bean
for i, (fill, hl) in enumerate([(ROAST, '#96573A'), ('#4A2616', '#6E3B22'), ('#83482A', '#A8663F')]):
    save(f'bean{i}', 240, 320, f'''
<ellipse cx="120" cy="160" rx="92" ry="132" fill="{fill}" {OL}/>
<ellipse cx="88" cy="110" rx="26" ry="50" fill="{hl}" transform="rotate(-12 88 110)"/>
<path d="M120 36 C80 100 165 190 118 284" fill="none" stroke="{ESP}" stroke-width="14" stroke-linecap="round"/>
''')

# ---------------------------------------------------------------- coffee bag / pouch
def bag(name, label, txt, origin, note):
    tcol = CREAM if label in (ORANGE, ESP, ROAST) else ESP
    zig = ' '.join(f'L{60 + k * 20} {70 if k % 2 else 58}' for k in range(1, 20))
    save(name, 520, 760, f'''
<path d="M60 70 {zig} L460 70 L470 120 L490 680 Q492 720 452 722 L68 722 Q28 720 30 680 L50 120 Z" fill="{KRAFT}" {OL}/>
<path d="M50 120 L470 120" stroke="{ESP}" stroke-width="8"/>
<path d="M60 70 L460 70 L470 120 L50 120 Z" fill="{KRAFT_D}" {OL}/>
<path d="M80 140 L60 690" stroke="{KRAFT_D}" stroke-width="16" stroke-linecap="round"/>
<path d="M440 140 L460 690" stroke="{KRAFT_D}" stroke-width="16" stroke-linecap="round"/>
<circle cx="260" cy="190" r="26" fill="{KRAFT_D}" {OL}/><circle cx="260" cy="190" r="8" fill="{ESP}"/>
<rect x="100" y="260" width="320" height="360" rx="14" fill="{label}" {OL}/>
<rect x="118" y="278" width="284" height="324" rx="8" fill="none" stroke="{tcol}" stroke-width="4" stroke-dasharray="14 10" opacity=".7"/>
<text x="260" y="385" font-family="Lalezar" font-size="92" text-anchor="middle" fill="{tcol}">{txt}</text>
<line x1="150" y1="420" x2="370" y2="420" stroke="{tcol}" stroke-width="5"/>
<text x="260" y="495" font-family="Marhey" font-size="58" font-weight="700" text-anchor="middle" fill="{tcol}">{origin}</text>
<text x="260" y="570" font-family="Anton" font-size="30" letter-spacing="6" text-anchor="middle" fill="{tcol}" opacity=".85">{note}</text>
''')

bag('bag_orange', ORANGE, 'كلوفا', 'إثيوبيا', 'SINGLE ORIGIN')
bag('bag_yellow', YELLOW, 'كلوفا', 'كولومبيا', 'SINGLE ORIGIN')
bag('bag_cream', CREAM, 'كلوفا', 'البرازيل', 'SINGLE ORIGIN')
bag('bag_esp', ESP, 'كلوفا', 'اليمن', 'SINGLE ORIGIN')

# ---------------------------------------------------------------- espresso machine
save('machine', 860, 900, f'''
<rect x="110" y="120" width="640" height="60" rx="10" fill="{KRAFT}" {OL}/>
<g stroke="{ESP}" stroke-width="8"><line x1="150" y1="120" x2="150" y2="85"/><line x1="710" y1="120" x2="710" y2="85"/></g>
<rect x="140" y="70" width="580" height="22" rx="10" fill="{ESP}"/>
<rect x="190" y="30" width="80" height="44" rx="8" fill="{CREAM}" {OL}/><rect x="290" y="38" width="70" height="36" rx="8" fill="{ORANGE}" {OL}/>
<rect x="90" y="170" width="680" height="560" rx="36" fill="{CREAM}" {OL}/>
<rect x="90" y="170" width="680" height="120" rx="36" fill="{ESP}"/>
<rect x="90" y="250" width="680" height="40" fill="{ESP}"/>
<text x="430" y="252" font-family="Anton" font-size="62" letter-spacing="14" text-anchor="middle" fill="{CREAM}">ESPRESSO</text>
<circle cx="610" cy="380" r="62" fill="{PAPER}" {OL}/>
<g stroke="{ESP}" stroke-width="5">{''.join(f'<line x1="{610 + 48 * math.cos(math.radians(a))}" y1="{380 + 48 * math.sin(math.radians(a))}" x2="{610 + 38 * math.cos(math.radians(a))}" y2="{380 + 38 * math.sin(math.radians(a))}"/>' for a in range(150, 391, 30))}</g>
<line x1="610" y1="380" x2="650" y2="345" stroke="{ORANGE}" stroke-width="9" stroke-linecap="round"/><circle cx="610" cy="380" r="10" fill="{ESP}"/>
<circle cx="200" cy="360" r="26" fill="{ORANGE}" {OL}/><circle cx="270" cy="360" r="26" fill="{YELLOW}" {OL}/><circle cx="340" cy="360" r="26" fill="{KRAFT}" {OL}/>
<rect x="330" y="420" width="200" height="60" rx="10" fill="{ROAST}" {OL}/>
<rect x="360" y="478" width="140" height="36" rx="6" fill="{ESP}"/>
<path d="M500 490 L700 470 Q730 468 730 490 Q730 512 700 510 L500 512 Z" fill="{ESP}"/>
<g stroke="{ESP}" stroke-width="7"><line x1="400" y1="515" x2="400" y2="540"/><line x1="460" y1="515" x2="460" y2="540"/></g>
<path d="M370 560 L490 560 L480 640 Q478 660 458 660 L402 660 Q382 660 380 640 Z" fill="{ORANGE}" {OL}/>
<path d="M490 580 Q525 585 520 612 Q515 632 484 628" fill="none" stroke="{ESP}" stroke-width="9"/>
<path d="M150 420 L150 600 Q150 630 180 630" fill="none" stroke="{ESP}" stroke-width="14" stroke-linecap="round"/>
<rect x="130" y="400" width="44" height="30" rx="8" fill="{ESP}"/>
<rect x="130" y="670" width="600" height="46" rx="10" fill="{KRAFT}" {OL}/>
<g stroke="{ESP}" stroke-width="5" opacity=".6">{''.join(f'<line x1="{150 + k * 30}" y1="680" x2="{150 + k * 30}" y2="706"/>' for k in range(20))}</g>
<rect x="140" y="728" width="70" height="60" rx="8" fill="{ESP}"/><rect x="650" y="728" width="70" height="60" rx="8" fill="{ESP}"/>
<rect x="170" y="190" width="30" height="480" rx="15" fill="#fff" opacity=".0"/>
''')

# ---------------------------------------------------------------- coffee cherry branch
leaves = ''
for (x, y, a, s) in [(170, 250, -30, 1.1), (330, 150, 20, 1.0), (520, 210, -10, 1.15), (660, 120, 35, 0.9), (420, 380, 150, 1.0), (620, 360, 160, 0.95)]:
    veins = ''.join('<path d="M%d 0 L%d -22" stroke="%s" stroke-width="4"/>' % (40 + k * 35, 60 + k * 35, ROAST) for k in range(4))
    leaves += f'<g transform="translate({x} {y}) rotate({a}) scale({s*1.45})"><path d="M0 0 C40 -60 150 -60 200 0 C150 60 40 60 0 0 Z" fill="{ESP}" stroke="{ESP}" stroke-width="6"/><path d="M10 0 L185 0" stroke="{ROAST}" stroke-width="5"/>{veins}</g>'
cher = ''
for (x, y, r, c) in [(300, 300, 42, ORANGE), (350, 330, 40, '#E2451F'), (290, 360, 38, ORANGE), (350, 395, 36, '#E2451F'),
                     (520, 290, 40, ORANGE), (565, 315, 38, '#E2451F'), (515, 350, 36, ORANGE), (455, 300, 34, '#E2451F')]:
    cher += f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" {OL}/><circle cx="{x - r * .35}" cy="{y - r * .38}" r="{r * .22}" fill="{PAPER}" opacity=".75"/><circle cx="{x + r * .1}" cy="{y + r * .1}" r="5" fill="{ESP}" opacity=".5"/>'
save('cherry', 900, 700, f'''<g transform="translate(40 190) scale(.9)">
<path d="M30 300 C200 260 350 230 520 250 S760 220 830 160" fill="none" stroke="{ESP}" stroke-width="30" stroke-linecap="round"/>
<path d="M30 300 C200 260 350 230 520 250 S760 220 830 160" fill="none" stroke="{ROAST}" stroke-width="16" stroke-linecap="round"/>
{leaves}{cher}</g>''')

# ---------------------------------------------------------------- globe
continents = """
<path d="M150 200 C200 150 330 140 380 180 C400 200 360 230 380 260 C395 290 350 300 330 330 C310 360 280 380 260 420 C250 440 230 430 220 400 C200 350 170 330 150 300 C130 270 130 230 150 200 Z"/>
<path d="M290 470 C330 450 380 470 390 510 C400 560 360 600 340 650 C325 690 310 720 295 700 C280 660 285 610 270 570 C255 530 260 490 290 470 Z"/>
<path d="M470 180 C500 160 560 160 580 190 C595 215 560 230 540 240 C520 250 490 240 470 230 C455 215 455 195 470 180 Z"/>
<path d="M470 290 C520 270 600 280 620 330 C640 380 610 420 600 470 C590 530 560 590 520 620 C500 630 490 600 485 560 C480 510 450 480 440 430 C430 380 440 310 470 290 Z"/>
<path d="M610 180 C670 150 770 190 795 250 C805 300 765 320 725 310 C695 300 675 330 645 320 C615 300 615 260 610 230 Z"/>
<path d="M632 335 C662 335 690 355 680 385 C670 405 648 405 638 385 Z"/>
<path d="M650 560 C690 540 740 560 735 600 C730 630 680 640 660 620 C645 605 640 580 650 560 Z"/>"""
save('globe', 820, 820, f'''
<defs><clipPath id="g"><circle cx="410" cy="410" r="370"/></clipPath></defs>
<circle cx="410" cy="410" r="370" fill="{ORANGE}"/>
<g clip-path="url(#g)">
  <g fill="{CREAM}" stroke="{ESP}" stroke-width="8" stroke-linejoin="round">{continents}</g>
  <g fill="none" stroke="{ESP}" stroke-width="4" opacity=".45">
    <ellipse cx="410" cy="410" rx="120" ry="370"/><ellipse cx="410" cy="410" rx="250" ry="370"/><line x1="410" y1="40" x2="410" y2="780"/>
    <line x1="40" y1="410" x2="780" y2="410"/><ellipse cx="410" cy="410" rx="370" ry="130"/><ellipse cx="410" cy="410" rx="370" ry="260"/>
  </g>
  <path d="M600 120 A370 370 0 0 1 700 620" fill="none" stroke="#fff" stroke-width="30" opacity=".18" stroke-linecap="round"/>
</g>
<circle cx="410" cy="410" r="370" fill="none" {OL} stroke-width="12"/>
''')

# ---------------------------------------------------------------- plane
save('plane', 360, 240, f'''
<g transform="rotate(-8 180 120)">
<path d="M40 120 Q60 95 110 98 L300 98 Q340 100 340 120 Q340 140 300 142 L110 142 Q60 145 40 120 Z" fill="{CREAM}" {OL}/>
<path d="M170 100 L230 20 L262 20 L230 100 Z" fill="{ORANGE}" {OL}/>
<path d="M170 140 L230 220 L262 220 L230 140 Z" fill="{ORANGE}" {OL}/>
<path d="M52 110 L20 60 L50 60 L90 100 Z" fill="{ORANGE}" {OL}/>
<g fill="{ESP}">{''.join(f'<circle cx="{150 + k * 30}" cy="116" r="7"/>' for k in range(5))}</g>
</g>''')

# ---------------------------------------------------------------- passport stamps
stamps = [('stamp_eth', 'إثيوبيا', 'ETHIOPIA', ORANGE, 'rect'), ('stamp_col', 'كولومبيا', 'COLOMBIA', ESP, 'oval'),
          ('stamp_bra', 'البرازيل', 'BRAZIL', ROAST, 'rect'), ('stamp_yem', 'اليمن', 'YEMEN', ORANGE, 'oval'),
          ('stamp_ken', 'كينيا', 'KENYA', ESP, 'rect')]
for name, ar, en, col, shape in stamps:
    if shape == 'rect':
        frame = f'<rect x="20" y="20" width="440" height="280" rx="26" fill="none" stroke="{col}" stroke-width="12"/><rect x="40" y="40" width="400" height="240" rx="14" fill="none" stroke="{col}" stroke-width="5"/>'
    else:
        frame = f'<ellipse cx="240" cy="160" rx="222" ry="142" fill="none" stroke="{col}" stroke-width="12"/><ellipse cx="240" cy="160" rx="196" ry="118" fill="none" stroke="{col}" stroke-width="5"/>'
    save(name, 480, 320, f'''{frame}
<text x="240" y="104" font-family="Anton" font-size="34" letter-spacing="8" text-anchor="middle" fill="{col}">{en}</text>
<text x="240" y="205" font-family="Lalezar" font-size="96" text-anchor="middle" fill="{col}">{ar}</text>
<text x="240" y="254" font-family="Anton" font-size="24" letter-spacing="6" text-anchor="middle" fill="{col}">★ COFFEE ORIGIN ★</text>''')

# ---------------------------------------------------------------- flavor icons
save('berry', 420, 440, f'''
<path d="M210 120 C300 90 380 140 370 230 C360 320 270 400 210 420 C150 400 60 320 50 230 C40 140 120 90 210 120 Z" fill="{ORANGE}" {OL}/>
<g fill="{YELLOW}" stroke="{ESP}" stroke-width="3">{''.join(f'<ellipse cx="{x}" cy="{y}" rx="7" ry="11"/>' for x, y in [(130, 200), (210, 180), (290, 200), (160, 270), (250, 265), (320, 260), (110, 250), (205, 340), (160, 335), (260, 330), (210, 250)])}</g>
<path d="M210 130 L150 60 L200 90 L210 30 L225 90 L275 55 L230 130 Z" fill="{ESP}" stroke="{ESP}" stroke-width="8" stroke-linejoin="round"/>
<ellipse cx="130" cy="170" rx="20" ry="34" fill="#fff" opacity=".3" transform="rotate(30 130 170)"/>''')

save('choco', 460, 420, f'''
<g transform="rotate(-10 230 210)">
<rect x="60" y="60" width="340" height="300" rx="16" fill="{ROAST}" {OL}/>
{''.join(f'<rect x="{80 + c * 105}" y="{80 + r * 90}" width="90" height="75" rx="8" fill="#83482A" stroke="{ESP}" stroke-width="6"/>' for r in range(3) for c in range(3))}
<path d="M40 230 L420 190 L430 380 Q430 400 410 400 L60 400 Q40 400 40 380 Z" fill="{YELLOW}" {OL}/>
<path d="M40 230 L420 190" stroke="{ESP}" stroke-width="10"/>
<text x="235" y="330" font-family="Anton" font-size="56" letter-spacing="6" text-anchor="middle" fill="{ESP}">COCOA</text>
</g>''')

save('lemon', 440, 440, f'''
<circle cx="220" cy="220" r="190" fill="{YELLOW}" {OL}/>
<circle cx="220" cy="220" r="160" fill="#FFE08A" stroke="{PAPER}" stroke-width="10"/>
<g stroke="{PAPER}" stroke-width="10">{''.join(f'<line x1="220" y1="220" x2="{220 + 160 * math.cos(math.radians(a))}" y2="{220 + 160 * math.sin(math.radians(a))}"/>' for a in range(0, 360, 45))}</g>
<circle cx="220" cy="220" r="18" fill="{PAPER}"/>
<g fill="{YELLOW}" opacity=".9">{''.join(f'<ellipse cx="{220 + 95 * math.cos(math.radians(a + 22.5))}" cy="{220 + 95 * math.sin(math.radians(a + 22.5))}" rx="10" ry="22" transform="rotate({a + 22.5 + 90} {220 + 95 * math.cos(math.radians(a + 22.5))} {220 + 95 * math.sin(math.radians(a + 22.5))})"/>' for a in range(0, 360, 45))}</g>''')

petals = ''.join(f'<ellipse cx="220" cy="120" rx="62" ry="100" fill="{CREAM if k % 2 else PAPER}" {OL} transform="rotate({k * 72} 220 220)"/>' for k in range(5))
save('flower', 440, 440, f'''{petals}
<circle cx="220" cy="220" r="62" fill="{ORANGE}" {OL}/>
<g fill="{YELLOW}">{''.join(f'<circle cx="{220 + 30 * math.cos(math.radians(a))}" cy="{220 + 30 * math.sin(math.radians(a))}" r="9"/>' for a in range(0, 360, 60))}</g>''')

# ---------------------------------------------------------------- takeaway cup
save('tcup', 420, 620, f'''
<path d="M80 150 L340 150 L300 580 Q298 600 278 600 L142 600 Q122 600 120 580 Z" fill="{PAPER}" {OL}/>
<path d="M92 280 L328 280 L312 450 L108 450 Z" fill="{KRAFT}" {OL}/>
<g stroke="{ESP}" stroke-width="4" opacity=".35">{''.join(f'<line x1="{110 + k * 22}" y1="285" x2="{114 + k * 21}" y2="445"/>' for k in range(10))}</g>
<circle cx="210" cy="365" r="46" fill="{ORANGE}" {OL}/>
<path d="M190 350 Q210 330 230 350 Q210 400 190 350 Z" fill="{CREAM}"/>
<rect x="60" y="110" width="300" height="50" rx="14" fill="{ESP}"/>
<path d="M90 110 Q100 60 150 58 L270 58 Q320 60 330 110 Z" fill="{ESP}"/>
<rect x="170" y="44" width="80" height="20" rx="8" fill="{ESP}"/>
<rect x="120" y="170" width="18" height="400" rx="9" fill="#fff" opacity=".5"/>''')

# ---------------------------------------------------------------- receipt
items = [('لاتيه', '١٨'), ('سبانش لاتيه', '٢٢'), ('كورتادو', '١٧'), ('فلات وايت', '٢٠'), ('لاتيه', '١٨'), ('سبانش لاتيه', '٢٢'),
         ('آيس لاتيه', '٢١'), ('كورتادو', '١٧'), ('لاتيه', '١٨'), ('فلات وايت', '٢٠'), ('سبانش لاتيه', '٢٢'), ('آيس لاتيه', '٢١')]
top_zig = ' '.join(f'L{k * 25} {12 if k % 2 else 0}' for k in range(1, 21))
bot_zig = ' '.join(f'L{500 - k * 25} {1188 - (12 if k % 2 else 0)}' for k in range(1, 21))
rows = ''
for k, (a, p) in enumerate(items):
    y = 250 + k * 56
    rows += f'<text x="450" y="{y}" font-family="Cairo" font-size="34" text-anchor="end" fill="{ESP}">{a}</text><text x="50" y="{y}" font-family="Cairo" font-size="34" fill="{ESP}">{p}</text><line x1="{120}" y1="{y - 10}" x2="{440 - len(a) * 17}" y2="{y - 10}" stroke="{ESP}" stroke-width="3" stroke-dasharray="3 7" opacity=".5"/>'
save('receipt', 500, 1200, f'''
<path d="M0 0 {top_zig} L500 1188 {bot_zig} L0 1188 Z" fill="{PAPER}"/>
<text x="250" y="110" font-family="Lalezar" font-size="64" text-anchor="middle" fill="{ESP}">فاتورة الكوفي</text>
<text x="250" y="160" font-family="Anton" font-size="26" letter-spacing="8" text-anchor="middle" fill="{ESP}" opacity=".7">*** RECEIPT ***</text>
<line x1="40" y1="190" x2="460" y2="190" stroke="{ESP}" stroke-width="4" stroke-dasharray="12 8"/>
{rows}
<line x1="40" y1="930" x2="460" y2="930" stroke="{ESP}" stroke-width="4" stroke-dasharray="12 8"/>
<text x="450" y="1000" font-family="Lalezar" font-size="58" text-anchor="end" fill="{ORANGE}">المجموع</text>
<text x="50" y="1000" font-family="Lalezar" font-size="58" fill="{ORANGE}">٢٣٦ ر.س</text>
<g fill="{ESP}">{''.join(f'<rect x="{70 + k * 13}" y="1040" width="{random.Random(k).choice([3, 5, 8])}" height="90"/>' for k in range(28))}</g>''')

# ---------------------------------------------------------------- calendar pages
for num in ['١', '٢', '٣', '٤', '٥', '٦', '٧', '٣٠']:
    save(f'cal_{"x" if num == "٣٠" else "d"}{["١", "٢", "٣", "٤", "٥", "٦", "٧", "٣٠"].index(num)}', 480, 540, f'''
<rect x="20" y="60" width="440" height="460" rx="24" fill="{PAPER}" {OL}/>
<path d="M20 84 Q20 60 44 60 L436 60 Q460 60 460 84 L460 170 L20 170 Z" fill="{ORANGE}" {OL}/>
<text x="240" y="138" font-family="Lalezar" font-size="64" text-anchor="middle" fill="{CREAM}">يوم</text>
<g>{''.join(f'<rect x="{90 + k * 110}" y="25" width="26" height="80" rx="13" fill="{ESP}"/>' for k in range(3))}</g>
<text x="240" y="440" font-family="Lalezar" font-size="260" text-anchor="middle" fill="{ESP}">{num}</text>''')

# ---------------------------------------------------------------- coin
save('coin', 240, 240, f'''
<circle cx="120" cy="120" r="104" fill="{YELLOW}" {OL}/>
<circle cx="120" cy="120" r="76" fill="none" stroke="{ESP}" stroke-width="5" stroke-dasharray="6 8"/>
<g transform="rotate(25 120 120)"><ellipse cx="120" cy="120" rx="34" ry="48" fill="{ESP}"/><path d="M120 76 C104 104 136 136 120 164" fill="none" stroke="{YELLOW}" stroke-width="8" stroke-linecap="round"/></g>
<path d="M60 70 A80 80 0 0 1 120 40" fill="none" stroke="#fff" stroke-width="10" opacity=".5" stroke-linecap="round"/>''')

# ---------------------------------------------------------------- logo stamp
R = 380
circ_text = ' • '.join(['KLOVA', 'COFFEE CROPS'] * 3) + ' • '
save('logo', 820, 820, f'''
<defs><path id="cp" d="M410 410 m-320 0 a320 320 0 1 1 640 0 a320 320 0 1 1 -640 0"/></defs>
<circle cx="410" cy="410" r="{R}" fill="{ORANGE}" {OL} stroke-width="12"/>
<text font-family="Anton" font-size="52" letter-spacing="10" fill="{CREAM}"><textPath href="#cp" textLength="1960">{circ_text}</textPath></text>
<circle cx="410" cy="410" r="262" fill="{ESP}" {OL} stroke-width="12"/>
<circle cx="410" cy="410" r="238" fill="none" stroke="{CREAM}" stroke-width="4" stroke-dasharray="10 10"/>
<g transform="translate(410 235) rotate(25)"><ellipse cx="0" cy="0" rx="40" ry="56" fill="{KRAFT}"/><path d="M0 -52 C-18 -20 18 20 0 52" fill="none" stroke="{ESP}" stroke-width="9" stroke-linecap="round"/></g>
<text x="410" y="480" font-family="Lalezar" font-size="190" text-anchor="middle" fill="{CREAM}">كلوفا</text>
<text x="410" y="575" font-family="Marhey" font-weight="700" font-size="54" text-anchor="middle" fill="{YELLOW}">محاصيل القهوة</text>''')

# ---------------------------------------------------------------- rosette badge
scallop = ''.join(f'<circle cx="{300 + 205 * math.cos(math.radians(a))}" cy="{300 + 205 * math.sin(math.radians(a))}" r="40"/>' for a in range(0, 360, 20))
save('rosette', 600, 760, f'''
<path d="M210 420 L150 720 L220 680 L270 740 L310 450 Z" fill="{ORANGE}" {OL}/>
<path d="M390 420 L450 720 L380 680 L330 740 L290 450 Z" fill="{ORANGE}" {OL}/>
<g fill="{YELLOW}" stroke="{ESP}" stroke-width="10">{scallop}</g>
<circle cx="300" cy="300" r="212" fill="{YELLOW}"/>
<circle cx="300" cy="300" r="170" fill="{PAPER}" {OL}/>
<circle cx="300" cy="300" r="150" fill="none" stroke="{ESP}" stroke-width="4" stroke-dasharray="8 8"/>
<text x="300" y="300" font-family="Lalezar" font-size="120" text-anchor="middle" fill="{ESP}">الطعم</text>
<path d="M235 345 L285 390 L375 300" fill="none" stroke="{ORANGE}" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>''')

# ---------------------------------------------------------------- video frame w/ play
save('player', 820, 560, f'''
<rect x="20" y="20" width="780" height="520" rx="40" fill="{ESP}" {OL}/>
<rect x="50" y="50" width="720" height="400" rx="20" fill="{ROAST}"/>
<circle cx="410" cy="250" r="120" fill="{ORANGE}" {OL}/>
<path d="M375 185 L375 315 L480 250 Z" fill="{CREAM}" stroke="{CREAM}" stroke-width="14" stroke-linejoin="round"/>
<rect x="70" y="482" width="680" height="16" rx="8" fill="{CREAM}" opacity=".35"/>
<rect x="70" y="482" width="400" height="16" rx="8" fill="{YELLOW}"/>
<circle cx="470" cy="490" r="18" fill="{YELLOW}" {OL} stroke-width="6"/>''')

# ---------------------------------------------------------------- phone
tiles = ''
tcols = [ORANGE, KRAFT, ESP, YELLOW, ROAST, CREAM]
for k in range(6):
    x = 80 + (k % 3) * 190; y = 770 + (k // 3) * 250
    c = tcols[k]
    ic = ESP if c in (YELLOW, CREAM, KRAFT, ORANGE) else CREAM
    tiles += f'<rect x="{x}" y="{y}" width="176" height="236" rx="14" fill="{c}" stroke="{ESP}" stroke-width="6"/><g transform="translate({x + 88} {y + 118}) rotate({k * 25})"><ellipse rx="34" ry="48" fill="{ic}"/><path d="M0 -44 C-16 -15 16 15 0 44" fill="none" stroke="{c}" stroke-width="8" stroke-linecap="round"/></g>'
save('phone', 720, 1400, f'''
<rect x="20" y="20" width="680" height="1360" rx="90" fill="{ESP}" {OL}/>
<rect x="50" y="50" width="620" height="1300" rx="66" fill="{PAPER}"/>
<rect x="290" y="72" width="140" height="34" rx="17" fill="{ESP}"/>
<circle cx="360" cy="270" r="110" fill="{ORANGE}" {OL}/>
<text x="360" y="300" font-family="Lalezar" font-size="84" text-anchor="middle" fill="{CREAM}">كلوفا</text>
<text x="360" y="455" font-family="Lalezar" font-size="70" text-anchor="middle" fill="{ESP}">كلوفا</text>
<text x="360" y="515" font-family="Marhey" font-weight="700" font-size="36" text-anchor="middle" fill="{ROAST}">متجر محاصيل القهوة ☕</text>
<rect x="150" y="560" width="420" height="96" rx="48" fill="{YELLOW}" {OL} stroke-width="8"/>
<text x="400" y="626" font-family="Lalezar" font-size="52" text-anchor="middle" fill="{ESP}">الرابط</text>
<g transform="translate(245 608) rotate(-45)" fill="none" stroke="{ESP}" stroke-width="10"><rect x="-38" y="-16" width="44" height="32" rx="16"/><rect x="-6" y="-16" width="44" height="32" rx="16"/></g>
<line x1="80" y1="720" x2="640" y2="720" stroke="{ESP}" stroke-width="3" opacity=".25"/>
{tiles}''')

print('svgs written:', len(os.listdir(OUT)))
