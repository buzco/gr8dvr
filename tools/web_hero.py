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


TINY = {'A': ['010', '101', '111', '101', '101'], 'V': ['101', '101', '101', '101', '010'], 'I': ['111', '010', '010', '010', '111'],
        'N': ['101', '111', '111', '111', '101'], 'O': ['111', '101', '101', '101', '111'], 'U': ['101', '101', '101', '101', '111'],
        'T': ['111', '010', '010', '010', '010'], 'M': ['10001', '11011', '10101', '10001', '10001'], 'E': ['111', '100', '110', '100', '111'],
        'F': ['111', '100', '110', '100', '100'], ' ': ['0', '0', '0', '0', '0'],
        '<': ['001', '011', '111', '011', '001'], '>': ['100', '110', '111', '110', '100']}


def tiny(px, txt, x, y, col):
    for ch in txt:
        g = TINY[ch]
        for yy, r in enumerate(g):
            for xx, b in enumerate(r):
                if b == '1':
                    px[x + xx, y + yy] = col
        x += len(g[0]) + 1


def tiny_w(txt):
    return sum(len(TINY[c][0]) for c in txt) + len(txt) - 1


def hero_dvr():
    """The real 3-button Mini DVR (matte black, white print), 3/4 view: top, front (USB-C, switch) and the AV side."""
    from PIL import ImageFont
    W, H, T, SH, M = 180, 84, 15, 4, 6            # top face size, thickness, shear (rows per px), margin
    INK = (239, 230, 208, 255)
    top = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(top); px = top.load()
    body, rim, dim = (40, 42, 48, 255), (74, 78, 88, 255), (30, 32, 37, 255)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=9, fill=body)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=9, outline=rim)
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=8, outline=(52, 55, 62, 255))
    for y in range(4, H - 4):                                      # soft matte sheen, dithered
        for x in range(6, W - 6):
            t = (x - y * 1.6) / W
            if 0.18 < t < 0.42 and (x + y) % 2 == 0 and ((x // 2 + y) % 3):
                px[x, y] = (46, 48, 55, 255)
    # MINI DVR
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 23)
    lbl = Image.new('L', (200, 40), 0); ImageDraw.Draw(lbl).text((0, 0), 'MINI DVR', font=f, fill=255)
    lbl = lbl.point(lambda v: 255 if v > 110 else 0); bb = lbl.getbbox(); lbl = lbl.crop(bb)
    top.paste(Image.new('RGBA', lbl.size, INK), (22, 31), lbl)
    # three buttons along the back edge + their print
    for i, bx in enumerate((118, 140, 162)):
        d.ellipse((bx - 5, 6, bx + 5, 15), fill=(18, 19, 23, 255))
        d.ellipse((bx - 4, 6, bx + 4, 13), fill=(58, 61, 70, 255))
        d.ellipse((bx - 3, 7, bx + 1, 9), fill=(92, 96, 108, 255))
    for yy in range(4):                                            # up / down triangles under buttons 1 and 3
        for xx in range(-yy, yy + 1):
            px[118 + xx, 19 + yy] = INK; px[162 + xx, 22 - yy] = INK
    tiny(px, 'MENU', 140 - tiny_w('MENU') // 2, 19, INK)
    # AV labels at the jack end
    tiny(px, '<AV IN', 5, 8, INK)
    tiny(px, '<AV OUT', 5, H - 13, INK)
    d.ellipse((12, 50, 22, 60), outline=INK); d.ellipse((15, 53, 19, 57), fill=dim)   # ring icon
    # battery gauge + bolt
    d.rectangle((60, 64, 86, 74), outline=INK); d.rectangle((87, 67, 88, 71), fill=INK)
    for i in range(4):
        d.rectangle((62 + i * 6, 66, 66 + i * 6, 72), fill=INK if i < 3 else (90, 94, 104, 255))
    for (x, y) in ((95, 63), (94, 64), (94, 65), (93, 66), (93, 67), (94, 67), (95, 67), (96, 67), (95, 68), (95, 69), (94, 70), (94, 71), (93, 72)):
        px[x, y] = INK
    # microSD icon + ON/OFF
    d.polygon([(152, 40), (162, 40), (162, 54), (149, 54), (149, 43)], fill=INK)
    for i in range(4):
        px[152 + i * 2, 42] = body
    tiny(px, 'ON', 160, 64, INK); tiny(px, 'OFF', 156, 72, INK)
    px[155, 66] = INK; px[154, 66] = INK
    # ---- assemble: cabinet view - top face flat, body extruded down-left (front + AV side visible)
    DX = T // 2
    OW, OH = W + DX + 2 * M, H + T + 2 * M
    ox, oy = M + DX, M
    face = Image.new('RGBA', (OW, OH), (0, 0, 0, 0)); face.paste(top, (ox, oy), top)
    mask = face.split()[3].point(lambda v: 255 if v else 0)
    im = Image.new('RGBA', (OW, OH), (0, 0, 0, 0))
    front, side = (22, 23, 27, 255), (33, 35, 41, 255)
    for k in range(T, 0, -1):
        im.paste(Image.new('RGBA', (OW, OH), front), (-(k * DX) // T, k), mask)
    ip = im.load()
    for y in range(OH):                                            # left of the top face's left edge = AV side
        for x in range(OW):
            if ip[x, y][3] and x < ox + 2 and y < oy + H - 3:
                ip[x, y] = side
    dd = ImageDraw.Draw(im)
    for yy in (oy + 16, oy + H - 22):                              # AV IN (back) + AV OUT (front) jacks
        xx = ox - DX // 2 - 1 + (0 if yy > oy + 40 else 1)
        dd.ellipse((xx - 3, yy + 3, xx + 2, yy + 11), fill=(8, 8, 10, 255))
        dd.ellipse((xx - 1, yy + 5, xx + 1, yy + 9), fill=(120, 124, 132, 255))
    fy = oy + H + 3                                                # front: USB-C + slide switch
    fx = ox - DX // 2
    dd.rounded_rectangle((fx + 104, fy, fx + 124, fy + 7), radius=3, fill=(8, 8, 10, 255))
    dd.rectangle((fx + 108, fy + 3, fx + 120, fy + 4), fill=(150, 154, 162, 255))
    dd.rectangle((fx + 156, fy + 1, fx + 168, fy + 7), fill=(8, 8, 10, 255))
    dd.rectangle((fx + 158, fy + 2, fx + 162, fy + 6), fill=(110, 114, 124, 255))
    im.alpha_composite(face)
    return _outline(im, (14, 15, 18, 255))


def backdrop(W=1600, H=675):
    return Image.frombytes('RGB', (W, H), scene.render(W, H, floor=True, seed=11, stars=1.2).tobytes())


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    s = hero_dvr()
    s.resize((s.width * 4, s.height * 4), Image.NEAREST).save(os.path.join(OUT, 'gr8dvr-minidvr.png'), optimize=True)
    backdrop().save(os.path.join(OUT, 'gr8dvr-hero-sea.jpg'), quality=86, optimize=True, progressive=True)
    print('web assets written')
