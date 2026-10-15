# Builds the README card: an ASCII portrait from portrait.jpg beside a neofetch-style
# info column, written as dark_mode.svg and light_mode.svg next to this script.
#
# Edit the `rows` list below to change the text, then run:
#   python3 build_card.py          (needs numpy, opencv-python, pillow)
#
# portrait_mask.png cuts the background out of the photo. It came from Apple's Vision
# framework; regenerate it for a new photo with:
#   swift mask.swift portrait.jpg portrait_mask.png
from pathlib import Path
from xml.sax.saxutils import escape

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent

# ---------- ASCII portrait ----------
# The portrait is drawn in a smaller font than the info column. ASCII art only reads
# as a picture when the characters are small enough to blend together.
ART_FONT, ART_LH = 10, 12   # px; keep LH/ART_FONT near 1.2 so the cells stay ~2:1
ART_ROWS = 50
RAMP = " .:-=+*#%@"

img = cv2.imread(str(HERE / 'portrait.jpg'))
mask = cv2.imread(str(HERE / 'portrait_mask.png'), 0)
x0, y0, x1, y1 = 230, 60, 1770, 1990            # head and shoulders
gray = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32)
m = mask[y0:y1, x0:x1].astype(np.float32) / 255
lo, hi = np.percentile(gray[m > 0.5], [3, 99])
tone = np.clip((gray - lo) / (hi - lo), 0, 1)    # 0 = darkest part of you, 1 = brightest
H, W = gray.shape
ART_COLS = round(ART_ROWS * (W / H) * (ART_LH / (ART_FONT * 0.6)))

def shrink(a):
    return cv2.resize(a, (ART_COLS, ART_ROWS), interpolation=cv2.INTER_AREA).clip(0, 1)

t, mm = shrink(tone), shrink(m)
# Edges inside the face (eyes, brows, nose, mouth), max-pooled so thin features survive.
blur = cv2.GaussianBlur(gray, (0, 0), 4)
edges = cv2.magnitude(cv2.Sobel(blur, cv2.CV_32F, 1, 0), cv2.Sobel(blur, cv2.CV_32F, 0, 1))
edges *= cv2.erode(m, np.ones((35, 35))) > 0.5   # ignore the outline of the cutout
edges = shrink(cv2.dilate(edges / np.percentile(edges[edges > 0], 98), np.ones((7, 7))))

def to_text(density, min_index=0):
    return [''.join(' ' if mm[y, x] < 0.5 else
                    RAMP[max(min_index, min(len(RAMP) - 1, int(density[y, x] * len(RAMP))))]
                    for x in range(ART_COLS)).rstrip()
            for y in range(ART_ROWS)]

# Light card: dark ink, so dark parts of the photo get dense characters.
light_art = to_text(np.clip((1 - t) ** 1.6 + 0.25 * edges, 0, 1))
# Dark card: light ink, so bright parts get dense characters (a positive, not a negative).
dark_art = to_text(np.clip(t ** 1.4 - 0.3 * edges, 0, 1), min_index=1)

# ---------- info column ----------
WIDTH = 56  # characters per info line
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
CHAR = FONT * 0.6  # approx advance of a monospace glyph
ART_W = ART_COLS * ART_FONT * 0.6
ART_H = ART_ROWS * ART_LH
INFO_X = PAD + ART_W + 40
TOTAL_W = int(INFO_X + WIDTH * CHAR + PAD)
TOTAL_H = int(PAD * 2 + max(ART_H, LH * len(rows)))
info_top = PAD + max(0, (ART_H - LH * len(rows)) / 2)

def svg(theme):
    c = {
        'dark':  dict(bg='#161b22', fg='#c9d1d9', key='#ffa657', value='#a5d6ff', dots='#616e7f'),
        'light': dict(bg='#f6f8fa', fg='#24292f', key='#953800', value='#0a3069', dots='#c2cfde'),
    }[theme]
    art = dark_art if theme == 'dark' else light_art
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,Menlo,monospace" width="{TOTAL_W}px" height="{TOTAL_H}px" font-size="{FONT}px">',
           '<style>@font-face{src:local("Consolas"),local("Consolas Bold");font-family:"ConsolasFallback";font-display:swap;-webkit-size-adjust:109%;size-adjust:109%;}',
           f'.key{{fill:{c["key"]}}}.value{{fill:{c["value"]}}}.cc{{fill:{c["dots"]}}}text,tspan{{white-space:pre}}</style>',
           f'<rect width="{TOTAL_W}px" height="{TOTAL_H}px" fill="{c["bg"]}" rx="15"/>',
           f'<text x="{PAD}" y="{PAD}" fill="{c["fg"]}" font-size="{ART_FONT}px">']
    for i, line in enumerate(art):
        out.append(f'<tspan x="{PAD}" y="{PAD + ART_FONT + i * ART_LH:.1f}">{escape(line)}</tspan>')
    out.append('</text>')
    x = f'{INFO_X:.0f}'
    out.append(f'<text x="{x}" y="{info_top + 15:.0f}" fill="{c["fg"]}">')
    y = info_top + 15
    for r in rows:
        if r[0] == 'title':
            out.append(f'<tspan x="{x}" y="{y:.0f}">{escape(r[1])}</tspan> {"-" * (WIDTH - len(r[1]) - 1)}')
        elif r[0] == 'section':
            out.append(f'<tspan x="{x}" y="{y:.0f}">- {escape(r[1])}</tspan> {"-" * (WIDTH - len(r[1]) - 3)}')
        elif r[0] == 'kv':
            key, val = r[1], r[2]
            dots = WIDTH - 2 - len(key) - 2 - len(val) - 1
            out.append(f'<tspan x="{x}" y="{y:.0f}" class="cc">. </tspan><tspan class="key">{escape(key)}</tspan>:<tspan class="cc"> {"." * dots} </tspan><tspan class="value">{escape(val)}</tspan>')
        else:
            out.append(f'<tspan x="{x}" y="{y:.0f}" class="cc">. </tspan>')
        y += LH
    out.append('</text>\n</svg>\n')
    return '\n'.join(out)

for theme in ('dark', 'light'):
    (HERE / f'{theme}_mode.svg').write_text(svg(theme))
print(f'art {ART_COLS}x{ART_ROWS}, card {TOTAL_W}x{TOTAL_H}')
