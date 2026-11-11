#!/usr/bin/env python3
"""Web hero assets for gr8success.xyz/pages/gr8dvr: a 3/4-view pixel Mini DVR and a clean backdrop."""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'app'))
from gr8core import scene  # noqa: E402
from make_assets import _outline  # noqa: E402

OUT = os.path.join(HERE, '..', 'web')
BEIGE = (239, 230, 208, 255)
G = {'M': ['10001', '11011', '10101', '10001', '10001'], 'I': ['111', '010', '010', '010', '111'],
     'N': ['1001', '1101', '1011', '1001', '1001'], 'D': ['1110', '1001', '1001', '1001', '1110'],
     'V': ['10001', '10001', '10001', '01010', '00100'], 'R': ['1110', '1001', '1110', '1010', '1001'],
     ' ': ['00', '00', '00', '00', '00']}


def text(px, txt, x, y, col):
    for ch in txt:
        for yy, r in enumerate(G[ch]):
            for xx, b in enumerate(r):
                if b == '1':
                    px[x + xx, y + yy] = col
        x += len(G[ch][0]) + 1


def text_w(txt):
    return sum(len(G[c][0]) for c in txt) + len(txt) - 1


def hero_dvr():
    W, H = 90, 66
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); px = im.load()
    x0, y0, x1, y1, dx, dy = 4, 16, 64, 51, 12, 9              # front face + depth offset
    front, top, side = (54, 61, 77, 255), (92, 103, 123, 255), (34, 39, 50, 255)
    hi, top_hi, side_lo = (122, 134, 154, 255), (128, 140, 160, 255), (24, 28, 37, 255)
    d.polygon([(x0, y0), (x1, y0), (x1 + dx, y0 - dy), (x0 + dx, y0 - dy)], fill=top)
    d.polygon([(x1, y0), (x1 + dx, y0 - dy), (x1 + dx, y1 - dy), (x1, y1)], fill=side)
    d.rectangle((x0, y0, x1, y1), fill=front)
    d.line((x0 + dx, y0 - dy, x1 + dx, y0 - dy), fill=top_hi)              # top back edge
    d.line((x0, y0, x0 + dx, y0 - dy), fill=top_hi)
    d.line((x0, y0, x1, y0), fill=hi); d.line((x0, y0, x0, y1), fill=hi)   # front bevel
    d.line((x0 + 1, y1, x1, y1), fill=side_lo)
    d.line((x1, y0, x1 + dx, y0 - dy), fill=hi)
    # three buttons on the top: MENU, <, >
    for i, bx in enumerate((22, 31, 40)):
        cx, cy = bx + 6, y0 - 5
        d.polygon([(cx - 3, cy + 1), (cx + 2, cy + 1), (cx + 4, cy - 1), (cx - 1, cy - 1)], fill=(205, 194, 166, 255))
        d.line((cx - 3, cy + 2, cx + 2, cy + 2), fill=(120, 112, 94, 255))
        px[cx, cy] = (60, 66, 80, 255) if i else (224, 83, 63, 255)
    # front label plate
    d.rectangle((x0 + 4, y0 + 4, x1 - 4, y1 - 4), fill=(44, 50, 63, 255))
    d.line((x0 + 4, y1 - 4, x1 - 4, y1 - 4), fill=(78, 87, 104, 255))
    d.line((x1 - 4, y0 + 4, x1 - 4, y1 - 4), fill=(78, 87, 104, 255))
    cx = (x0 + x1) // 2
    text(px, 'MINI DVR', cx - text_w('MINI DVR') // 2, y0 + 10, BEIGE)
    d.line((cx - 18, y0 + 18, cx + 18, y0 + 18), fill=(90, 115, 148, 255))   # stripe
    d.line((cx - 18, y0 + 19, cx + 18, y0 + 19), fill=(0, 195, 137, 255))
    for i in range(4):                                                        # battery LEDs
        px[x0 + 9 + i * 3, y1 - 8] = (0, 195, 137, 255)
    px[x1 - 10, y1 - 8] = (224, 83, 63, 255); px[x1 - 9, y1 - 8] = (224, 83, 63, 255)  # REC
    # side: microSD slot + AV jack + USB
    d.polygon([(x1 + 3, y0 + 7), (x1 + 9, y0 + 2), (x1 + 9, y0 + 4), (x1 + 3, y0 + 9)], fill=(8, 10, 14, 255))  # microSD
    d.line((x1 + 4, y0 + 9, x1 + 9, y0 + 5), fill=(70, 78, 94, 255))
    d.ellipse((x1 + 4, y0 + 15, x1 + 8, y0 + 20), fill=(150, 156, 168, 255))
    px[x1 + 6, y0 + 17] = (12, 14, 18, 255)
    d.rectangle((x1 + 4, y0 + 25, x1 + 7, y0 + 27), fill=(12, 14, 18, 255))
    # AV cable coming out of the jack, curling down
    cab = [(x1 + 8, y0 + 18), (x1 + 11, y0 + 19), (x1 + 13, y0 + 22), (x1 + 14, y0 + 27), (x1 + 14, y0 + 33),
           (x1 + 15, y0 + 37), (x1 + 17, y0 + 39)]
    d.line(cab, fill=(26, 30, 38, 255), width=2)
    d.rectangle((x1 + 16, y0 + 39, x1 + 19, y0 + 44), fill=(220, 180, 60, 255))    # yellow RCA plug at the end
    d.line((x1 + 17, y0 + 40, x1 + 17, y0 + 43), fill=(250, 220, 120, 255))
    d.rectangle((x1 + 17, y0 + 45, x1 + 18, y0 + 47), fill=(180, 186, 196, 255))
    d.rectangle((x1 + 7, y0 + 16, x1 + 9, y0 + 19), fill=(205, 194, 166, 255))  # yellow-ish RCA plug body
    return _outline(im)


def backdrop(W=1600, H=675):
    return Image.frombytes('RGB', (W, H), scene.render(W, H, floor=True, seed=11, stars=1.2).tobytes())


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    s = hero_dvr()
    s.resize((s.width * 8, s.height * 8), Image.NEAREST).save(os.path.join(OUT, 'gr8dvr-minidvr.png'), optimize=True)
    backdrop().save(os.path.join(OUT, 'gr8dvr-hero-sea.jpg'), quality=86, optimize=True, progressive=True)
    print('web assets written')
