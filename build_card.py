# Builds the README card: an ASCII portrait from portrait.jpg beside a neofetch-style
# info column, written as dark_mode.svg and light_mode.svg next to this script.
# Edit the `rows` list below to change the text, then run (needs Pillow):
#   python3 readme/build_card.py
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image, ImageOps, ImageDraw, ImageFilter
HERE = Path(__file__).resolve().parent

# ---------- ASCII portrait ----------
src = Image.open(HERE / 'portrait.jpg').convert('L')
im = src.crop((300, 40, 1620, 1990)).filter(ImageFilter.UnsharpMask(radius=8, percent=180, threshold=2))
W, H = im.size
mask = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mask)
d.ellipse((140, 30, 1170, 1560), fill=255)
d.polygon([(40, H), (40, 1650), (250, 1420), (420, 1390), (900, 1390), (1100, 1420), (1290, 1650), (1290, H)], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(25))
ROWS = 34
COLS = round(ROWS * (W / H) / 0.5)
small = im.resize((COLS, ROWS), Image.LANCZOS)
m = mask.resize((COLS, ROWS), Image.LANCZOS)
small = ImageOps.equalize(small, mask=m.point(lambda v: 255 if v > 128 else 0))
# Darker parts of the photo get denser characters (hair, eyes, brows, shirt), the
# same convention as the card this is modelled on; it reads on either background.
RAMP = " .'`,:;~!|ijkx%#&@"
def ascii_lines():
    out = []
    for y in range(ROWS):
        row = ''
        for x in range(COLS):
            if m.getpixel((x, y)) < 110: row += ' '; continue
            v = (1 - small.getpixel((x, y)) / 255) ** 0.75
            row += RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]
        out.append(row.rstrip())
    return out
dark_art = light_art = ascii_lines()

# ---------- info column ----------
WIDTH = 60  # characters per info line
rows = [
    ('title', 'evan@parshall'),
    ('kv', 'Role', 'Software Engineer'),
    ('kv', 'Host', 'SEP'),
    ('kv', 'Location', 'Westfield, Indiana'),
    ('kv', 'Education', 'Purdue University'),
    ('kv', 'Previously', 'ZF, Product Innovation'),
    ('blank',),
    ('kv', 'Languages.Programming', 'Python, Swift, TypeScript'),
    ('kv', 'Languages.Real', 'English, Spanish, Portuguese, German'),
    ('kv', 'Interests', 'Controls, Applied Math, AI'),
    ('kv', 'Hobbies', 'Travel, Reading, Languages'),
    ('blank',),
    ('section', 'Projects'),
    ('kv', 'Ballast', 'Paced breathing, iPhone + Apple Watch'),
    ('kv', 'Papers', 'J. Mech. Sci. Tech., arXiv'),
    ('kv', 'Website', 'epparshall.github.io'),
    ('blank',),
    ('section', 'Stats'),
    ('kv', 'Books.Reviewed', '23'),
    ('kv', 'Countries.Written.Up', '8'),
    ('kv', 'Apps.Shipped', '1'),
    ('blank',),
    ('section', 'Contact'),
    ('kv', 'Email', 'epparshall.gcp@gmail.com'),
    ('kv', 'LinkedIn', 'evanparshall'),
    ('kv', 'GitHub', 'epparshall'),
]

FONT, LH, PAD = 16, 20, 20
CHAR = 9.6  # approx advance of a 16px monospace glyph
INFO_X = PAD + (COLS + 3) * CHAR
TOTAL_W = int(INFO_X + WIDTH * CHAR + PAD)
TOTAL_H = PAD * 2 + LH * max(ROWS, len(rows))
info_top = PAD + LH * max(0, (ROWS - len(rows)) // 2)

def svg(theme):
    c = {
        'dark':  dict(bg='#161b22', fg='#c9d1d9', key='#ffa657', value='#a5d6ff', dots='#616e7f'),
        'light': dict(bg='#f6f8fa', fg='#24292f', key='#953800', value='#0a3069', dots='#c2cfde'),
    }[theme]
    art = dark_art if theme == 'dark' else light_art
    out = [f'<?xml version="1.0" encoding="utf-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,Menlo,monospace" width="{TOTAL_W}px" height="{TOTAL_H}px" font-size="{FONT}px">',
           '<style>@font-face{src:local("Consolas"),local("Consolas Bold");font-family:"ConsolasFallback";font-display:swap;-webkit-size-adjust:109%;size-adjust:109%;}',
           f'.key{{fill:{c["key"]}}}.value{{fill:{c["value"]}}}.cc{{fill:{c["dots"]}}}text,tspan{{white-space:pre}}</style>',
           f'<rect width="{TOTAL_W}px" height="{TOTAL_H}px" fill="{c["bg"]}" rx="15"/>',
           f'<text x="{PAD}" y="{PAD + 15}" fill="{c["fg"]}" class="ascii">']
    for i, line in enumerate(art):
        out.append(f'<tspan x="{PAD}" y="{PAD + 15 + i * LH}">{escape(line)}</tspan>')
    out.append('</text>')
    out.append(f'<text x="{INFO_X:.0f}" y="{info_top + 15}" fill="{c["fg"]}">')
    y = info_top + 15
    for r in rows:
        x = f'{INFO_X:.0f}'
        if r[0] == 'title':
            out.append(f'<tspan x="{x}" y="{y}">{escape(r[1])}</tspan> {"-" * (WIDTH - len(r[1]) - 1)}')
        elif r[0] == 'section':
            out.append(f'<tspan x="{x}" y="{y}">- {escape(r[1])}</tspan> {"-" * (WIDTH - len(r[1]) - 3)}')
        elif r[0] == 'kv':
            key, val = r[1], r[2]
            dots = WIDTH - 2 - len(key) - 2 - len(val) - 1
            out.append(f'<tspan x="{x}" y="{y}" class="cc">. </tspan><tspan class="key">{escape(key)}</tspan>:<tspan class="cc"> {"." * dots} </tspan><tspan class="value">{escape(val)}</tspan>')
        else:
            out.append(f'<tspan x="{x}" y="{y}" class="cc">. </tspan>')
        y += LH
    out.append('</text>\n</svg>\n')
    return '\n'.join(out)

for theme in ('dark', 'light'):
    open(HERE / f'{theme}_mode.svg', 'w').write(svg(theme))
print(COLS, ROWS, TOTAL_W, TOTAL_H, len(rows))
