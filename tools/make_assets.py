#!/usr/bin/env python3
"""Pixel-art assets for the GR8DVR Utility: wizard + mini DVR icon, splash (space + planets)."""
import math, os, random
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(__file__), '..', 'app', 'gr8core', 'data')

PAL = {'.': None, 'K': (12, 12, 14), 'k': (40, 40, 46), 'g': (78, 78, 86), 'W': (235, 235, 235), 'w': (170, 170, 178),
       'Y': (255, 214, 64), 'y': (200, 150, 30), 'P': (110, 56, 190), 'p': (70, 30, 130), 'q': (150, 96, 230),
       'S': (255, 240, 120), 'R': (255, 60, 118), 'G': (0, 195, 137), 'r': (200, 40, 40)}
# wizard hat (ASCII pixel rows) + mini DVR body drawn on a pixel grid with a 3x5 font
HAT = r"""
....................P...................
...................PqP..................
..................PqqP..................
.................PqqPp..................
................PqqPPp.....S............
...............PqqPPpp..................
..............PqqPSPpp.....S.S..........
.............PqqPPPppp......S...........
............PqqPPPPPpp..................
...........PqqPPPSPPppp.................
..........PqqPPPPPPPppp.................
.........PqqPPPPPPPPpppp................
........PqqPPPPPPPPPPpppp...............
......YYYYYYYYYYYYYYYYYYYYYY............
.....YyyyyyyyyyyyyyyyyyyyyyyY...........
"""
FONT = {'M': ['101', '111', '111', '101', '101'], 'I': ['111', '010', '010', '010', '111'],
        'N': ['101', '111', '111', '111', '101'], 'D': ['110', '101', '101', '101', '110'],
        'V': ['101', '101', '101', '101', '010'], 'R': ['110', '101', '110', '101', '101'], ' ': ['0'] * 5}

def wizard_dvr(scale):
    rows = HAT.strip('\n').split('\n')
    W, H = 42, len(rows) + 18
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if PAL.get(ch):
                px[x, y] = PAL[ch] + (255,)
    top = len(rows)
    d = ImageDraw.Draw(im)
    d.rectangle((3, top, 38, top + 15), fill=PAL['K'] + (255,))          # aluminium box, dark
    d.rectangle((4, top + 1, 37, top + 14), fill=PAL['k'] + (255,))
    d.line((4, top + 14, 37, top + 14), fill=PAL['g'] + (255,))
    for i, bx in enumerate((9, 13, 17)):                                  # 3 buttons
        px[bx, top + 2] = PAL['w'] + (255,)
    x = 6                                                                 # "MINI DVR"
    for ch in 'MINI DVR':
        g = FONT[ch]
        for yy, r in enumerate(g):
            for xx, bit in enumerate(r):
                if bit == '1':
                    px[x + xx, top + 5 + yy] = PAL['W'] + (255,)
        x += 4 if ch != ' ' else 2
    for i in range(4):                                                    # battery LEDs
        px[26 + i * 2, top + 12] = PAL['G'] + (255,)
    px[33, top + 12] = PAL['R'] + (255,)                                  # record LED
    d.rectangle((33, top + 3, 35, top + 4), fill=PAL['w'] + (255,))       # SD card mark
    d.rectangle((1, top + 6, 2, top + 9), fill=PAL['g'] + (255,))         # AV jacks
    d.rectangle((39, top + 6, 40, top + 9), fill=PAL['g'] + (255,))
    return im.resize((W * scale, H * scale), Image.NEAREST)

def planet(im, cx, cy, r, base, shade, light, ring=None, seed=1):
    rnd = random.Random(seed)
    px = im.load()
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            dx, dy = (x - cx) / r, (y - cy) / r
            if dx * dx + dy * dy > 1:
                continue
            lit = -dx * 0.6 - dy * 0.6 + math.sqrt(max(0, 1 - dx * dx - dy * dy)) * 0.7
            band = math.sin((dy + 0.15 * dx) * 9 + seed) * 0.15
            v = lit + band + ((x + y) % 2) * 0.06                     # ordered dither
            col = light if v > 0.75 else base if v > 0.25 else shade
            if 0 <= x < im.width and 0 <= y < im.height:
                px[x, y] = col
    if ring:
        for t in range(0, 720):
            a = t / 720 * 2 * math.pi
            for rr in (r * 1.6, r * 1.68, r * 1.76):
                x = int(cx + math.cos(a) * rr); y = int(cy + math.sin(a) * rr * 0.32)
                front = math.sin(a) > 0
                dxp, dyp = (x - cx) / r, (y - cy) / r
                if not front and dxp * dxp + dyp * dyp <= 1:
                    continue
                if 0 <= x < im.width and 0 <= y < im.height:
                    px[x, y] = ring

def splash():
    W, H = 200, 120                                              # drawn at 1/3, upscaled x3 (pixel look)
    sky = Image.open(os.path.join(D, 'sky.gif')).convert('RGB')
    im = sky.resize((W, int(sky.height * W / sky.width)), Image.NEAREST).crop((0, 0, W, H))
    planet(im, 158, 34, 20, (0, 150, 105), (0, 70, 50), (120, 235, 200), ring=(255, 60, 118), seed=3)
    planet(im, 22, 104, 30, (120, 60, 190), (60, 25, 110), (190, 140, 255), seed=7)
    planet(im, 128, 82, 4, (255, 214, 64), (170, 120, 20), (255, 245, 170), seed=2)
    im = im.resize((W * 3, H * 3), Image.NEAREST)
    icon = wizard_dvr(4)  # legacy splash (unused)
    im.paste(icon, (W * 3 - icon.width - 24, H * 3 - icon.height - 18), icon)
    return im

os.makedirs(D, exist_ok=True)

print('assets written')


# ---------------------------------------------------------------- converter animation sprites
def camcorder(scale=3):
    """Generic side-view handycam, lens pointing right (no brand) - key-art palette: pearl, ultramarine, blue-black."""
    W, H = 34, 22
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rim, body, hi, beige, cream = (124, 140, 214, 255), (14, 22, 70, 255), (44, 78, 176, 255), (214, 212, 226, 255), (240, 237, 230, 255)
    d.rectangle((7, 3, 21, 4), fill=beige); d.rectangle((7, 4, 8, 7), fill=beige); d.rectangle((20, 4, 21, 7), fill=beige)  # handle
    d.rectangle((1, 6, 7, 11), fill=rim); d.rectangle((0, 7, 1, 10), fill=beige)            # viewfinder + eyecup
    d.rectangle((5, 7, 25, 18), fill=rim); d.rectangle((6, 8, 24, 17), fill=body)           # body
    d.line((6, 8, 24, 8), fill=hi)
    d.rectangle((8, 10, 18, 16), fill=beige); d.rectangle((9, 11, 17, 15), fill=(6, 12, 44, 255))  # flip screen
    d.line((10, 12, 13, 12), fill=cream); d.point((16, 14), fill=(201, 90, 60, 255))
    d.point((22, 9), fill=(226, 96, 63, 255))                                                # REC lamp
    d.rectangle((25, 9, 29, 16), fill=body); d.rectangle((25, 9, 29, 16), outline=rim); d.line((26, 10, 28, 10), fill=hi)
    d.rectangle((29, 8, 32, 17), fill=beige); d.rectangle((30, 9, 32, 16), fill=(16, 40, 140, 255))   # lens + glass
    d.rectangle((31, 10, 31, 11), fill=cream); d.point((32, 14), fill=(143, 180, 255, 255))
    d.rectangle((6, 18, 24, 19), fill=rim)
    return im.resize((W * scale, H * scale), Image.NEAREST)


def crystal(scale=3):
    """Storage crystal: an amethyst data cluster on a dark plinth."""
    W, H = 30, 30
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    deep, mid, lite, hi = (70, 30, 120, 255), (120, 60, 190, 255), (175, 120, 240, 255), (255, 170, 220, 255)
    for (x, top, wd, ht) in ((5, 11, 6, 15), (17, 9, 6, 17), (10, 2, 8, 24)):   # three hex prisms
        bot = top + ht
        d.polygon([(x, top + 3), (x + wd // 2, top), (x + wd, top + 3), (x + wd, bot), (x, bot)], fill=mid)
        d.polygon([(x, top + 3), (x + wd // 2, top), (x + wd // 2, bot), (x, bot)], fill=lite)
        d.line((x + wd // 2, top + 1, x + wd // 2, bot), fill=deep)
        d.line((x + 1, top + 4, x + 1, bot - 3), fill=hi)
    for p in ((13, 6), (20, 13), (7, 15), (15, 18)):
        d.point(p, fill=(255, 255, 255, 255))
    d.rectangle((2, 26, 27, 29), fill=PAL['K'] + (255,)); d.line((3, 26, 26, 26), fill=PAL['g'] + (255,))
    for i in range(5):                                                           # activity LEDs on the plinth
        d.point((6 + i * 4, 28), fill=(0, 195, 137, 255))
    return im.resize((W * scale, H * scale), Image.NEAREST)


# ---------------------------------------------------------------- sounds (original, synthesized)
def sounds():
    import wave
    import numpy as np
    sr = 22050

    def t(sec):
        return np.arange(int(sr * sec)) / sr

    def env(n, a=0.005, r=0.08):
        e = np.ones(n); na, nr = min(n, int(sr * a)), min(n // 2, int(sr * r))
        e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr)
        return e

    def sq(f, sec, duty=0.5):
        x = t(sec); return np.where((x * f) % 1 < duty, 1.0, -1.0) * env(len(x))

    def tri(f, sec):
        x = t(sec); return (2 * np.abs(2 * ((x * f) % 1) - 1) - 1) * env(len(x))

    def bell(f, sec):
        x = t(sec); return np.sin(2 * np.pi * f * x + 2.2 * np.exp(-x * 6) * np.sin(2 * np.pi * f * 3.5 * x)) * np.exp(-x * 3.2)

    def save(name, y, gain=0.42):
        y = y / max(1e-9, np.abs(y).max()) * gain
        with wave.open(os.path.join(D, name), 'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
            f.writeframes((y * 32767).astype('<i2').tobytes())

    def cat(*parts):
        return np.concatenate(parts)

    def mix(*parts):
        n = max(len(p) for p in parts); out = np.zeros(n)
        for p in parts:
            out[:len(p)] += p
        return out

    # boot: tape-motor whirr sweeping up, a click, then a soft rising bell chord
    x = t(0.45); sweep = np.sin(2 * np.pi * np.cumsum(180 + 900 * x ** 2) / sr) * np.linspace(0.05, 0.35, len(x))
    click = np.zeros(int(sr * 0.04)); click[:60] = np.hanning(60)
    chord = mix(bell(523.25, 1.3), cat(np.zeros(int(sr * .09)), bell(659.25, 1.2)),
                cat(np.zeros(int(sr * .18)), bell(783.99, 1.1)), cat(np.zeros(int(sr * .27)), 0.8 * bell(1046.5, 1.0)))
    save('boot.wav', cat(sweep, click, chord), 0.38)
    # success: 8-bit arpeggio up + sparkle
    notes = [523.25, 659.25, 783.99, 1046.5]
    save('ok.wav', cat(*[sq(f, 0.065, 0.25) for f in notes], mix(sq(1318.5, 0.25, 0.125), 0.5 * tri(2093, 0.25))), 0.3)
    # error: two low descending buzzes
    save('error.wav', cat(sq(196, 0.16, 0.5), np.zeros(int(sr * .04)), sq(146.8, 0.30, 0.5)), 0.3)
    # card found: quick double blip
    save('card.wav', cat(tri(1318.5, 0.06), tri(1975.5, 0.09)), 0.35)
    # clip done (during a batch): tiny tick
    save('tick.wav', tri(2637, 0.035), 0.25)




ROCK_BANDS = [(4, (196, 170, 128)), (9, (122, 132, 148)), (13, (226, 212, 180)), (17, (150, 92, 70)),
              (21, (204, 186, 150)), (25, (92, 100, 116))]      # (top row, colour): sandstone, shale, limestone...


def rock(scale=3):
    """Storage entity: a block of sedimentary rock - strata bands with fossils inside."""
    W, H = 32, 30
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    shape = [(3, 6), (8, 3), (15, 4), (21, 2), (27, 5), (30, 11), (29, 20), (31, 27), (24, 29), (8, 29), (1, 27), (2, 17)]
    mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(shape, fill=255)
    body = Image.new('RGBA', (W, H)); bd = ImageDraw.Draw(body)
    for i, (y, c) in enumerate(ROCK_BANDS):
        y2 = ROCK_BANDS[i + 1][0] if i + 1 < len(ROCK_BANDS) else H
        for yy in range(y if i else 0, y2):
            tilt = 0
            for x in range(W):
                sh = 1.0 - 0.25 * (x > 22) + 0.08 * ((x * 7 + yy * 3) % 5 == 0)   # right side in shade, grain
                bd.point((x, yy + tilt), fill=tuple(int(v * sh) for v in c) + (255,))
        bd.line((0, y2 - 1, W, y2 - 1), fill=tuple(int(v * .7) for v in c) + (255,))
    for x, y in ((9, 15), (20, 23)):                                 # ammonite + shell fossils in the strata
        bd.arc((x - 2, y - 2, x + 2, y + 2), 0, 330, fill=(248, 240, 222, 255)); bd.point((x, y), fill=(248, 240, 222, 255))
    bd.ellipse((15, 10, 19, 12), fill=(236, 226, 200, 255)); bd.line((15, 11, 19, 11), fill=(120, 100, 80, 255))  # trilobite
    for x in (5, 25, 13):
        bd.point((x, 19), fill=(236, 226, 200, 255))
    im.paste(body, (0, 0), mask)
    out = mask.filter(__import__('PIL.ImageFilter', fromlist=['MaxFilter']).MaxFilter(3))
    o = Image.new('RGBA', (W, H), (30, 26, 22, 255)); o.putalpha(out); o.alpha_composite(im)
    return o.resize((W * scale, H * scale), Image.NEAREST)


if __name__ == '__main__':
    camcorder().save(os.path.join(D, 'camcorder.png'))
    rock().save(os.path.join(D, 'rock.png'))
    sounds()


# ---------------------------------------------------------------- nautilus + mini DVR (firmware builder icon)
def _outline(im, col=(30, 26, 22, 255)):
    from PIL import ImageFilter
    a = im.split()[3].point(lambda v: 255 if v > 0 else 0).filter(ImageFilter.MaxFilter(3))
    o = Image.new('RGBA', im.size, col); o.putalpha(a); o.alpha_composite(im)
    return o


def nautilus():
    """Nautilus pompilius facing right: shaded pearly shell, tapering tiger bands, umbilicus,
    spotted hood, pinhole eye and curling tentacles."""
    W, H = 40, 34
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = im.load()
    cx, cy, R = 15.0, 16.0, 14.5
    cream, shade, deep = (243, 235, 214), (214, 200, 170), (176, 158, 126)
    rust, brown = (178, 92, 58), (126, 64, 40)
    for y in range(H):
        for x in range(W):
            dx, dy = x + .5 - cx, y + .5 - cy
            r = math.hypot(dx, dy)
            if r > R:
                continue
            ang = math.degrees(math.atan2(dy, dx)) % 360          # 0 = right (aperture), 90 = down
            # 3D shading: light from top-left
            l = (-dx * .6 - dy * .8) / R
            c = cream if l > -.15 else shade if l > -.55 else deep
            if r > R - 1.2:
                c = deep if l < .2 else shade                     # rim
            # tiger bands: radial, wavy, only on the older (back) part of the shell, thinning near the aperture
            if 100 < ang < 350 and 3.5 < r < R - 1.0:
                wave = ang + 11 * math.sin(r / 3.0)
                width = 3 + 8 * (ang - 100) / 250                  # bold on the back, thin towards the aperture
                band = (wave % 27)
                if band < width:
                    c = brown if band < 1.6 or band > width - 1.2 else rust
            if r < 3.2:                                            # umbilicus with pearly ring
                c = (60, 46, 40) if r < 1.6 else (226, 220, 214)
            px[x, y] = c + (255,)
    d = ImageDraw.Draw(im)
    # soft body coming out of the aperture: tentacle bundle, eye, spotted hood on top
    d.ellipse((24, 15, 35, 27), fill=(206, 176, 146, 255))
    for i in range(9):                                            # tentacles fanning forward
        y0 = 17 + i * 1.1
        a = math.radians(-25 + i * 9)
        x1, y1 = 34 + 5.5 * math.cos(a), y0 + 5.5 * math.sin(a)
        d.line((31, y0, x1, y1), fill=(236, 220, 192, 255) if i % 2 else (196, 166, 136, 255))
        d.point((x1, y1 + (1 if i % 3 == 0 else 0)), fill=(236, 220, 192, 255))
    d.ellipse((27, 15, 32, 20), fill=(36, 42, 54, 255))            # pinhole eye
    d.point((28, 16), fill=(243, 235, 214, 255))
    hood = [(20, 6), (27, 4), (33, 7), (35, 12), (33, 15), (26, 15), (21, 12)]
    d.polygon(hood, fill=(116, 72, 50, 255))
    d.line((21, 12, 26, 15, 33, 15), fill=(84, 52, 38, 255))
    for x, y in ((24, 7), (28, 6), (31, 9), (27, 10), (24, 11), (32, 12), (29, 13)):
        d.point((x, y), fill=(236, 222, 196, 255))
    for x, y in ((9, 7), (8, 9), (10, 6)):                        # pearly highlight
        d.point((x, y), fill=(255, 252, 244, 255))
    return _outline(im)


def mini_dvr():
    """The Mini DVR, boxier (closer to its real 53 x 33 mm proportions)."""
    W, H = 44, 28
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); px = im.load()
    alu, alu_hi, alu_lo, face = (70, 78, 94, 255), (112, 122, 140, 255), (44, 50, 62, 255), (52, 58, 72, 255)
    d.rectangle((2, 1, 41, 26), fill=alu)
    d.line((3, 1, 40, 1), fill=alu_hi); d.line((2, 2, 2, 25), fill=alu_hi)
    d.line((3, 26, 41, 26), fill=alu_lo); d.line((41, 2, 41, 26), fill=alu_lo)
    d.rectangle((5, 4, 38, 23), fill=face)                         # front label plate
    for bx in (8, 12, 16):                                         # 3 buttons
        d.rectangle((bx, 5, bx + 1, 6), fill=(200, 188, 160, 255))
    G = {'M': ['10001', '11011', '10101', '10001', '10001'], 'I': ['111', '010', '010', '010', '111'],
         'N': ['1001', '1101', '1011', '1001', '1001'], 'D': ['1110', '1001', '1001', '1001', '1110'],
         'V': ['10001', '10001', '10001', '01010', '00100'], 'R': ['1110', '1001', '1110', '1010', '1001']}

    def word(txt, y0):
        w_ = sum(len(G[c][0]) for c in txt) + len(txt) - 1
        x = (W - w_) // 2
        for ch in txt:
            for yy, r in enumerate(G[ch]):
                for xx, bit in enumerate(r):
                    if bit == '1':
                        px[x + xx, y0 + yy] = (239, 230, 208, 255)
            x += len(G[ch][0]) + 1
    word('MINI', 9)
    word('DVR', 16)
    d.rectangle((34, 5, 36, 7), fill=(160, 170, 186, 255))        # SD card mark
    for i in range(4):                                            # battery LEDs + record LED
        px[25 + i * 2, 22] = (0, 195, 137, 255)
    px[34, 22] = (224, 83, 63, 255)
    d.rectangle((0, 9, 1, 13), fill=(150, 156, 168, 255)); d.rectangle((42, 9, 43, 13), fill=(150, 156, 168, 255))  # AV jacks
    return _outline(im)


def nautilus_dvr(scale):
    n, dv = nautilus(), mini_dvr()
    W = max(n.width, dv.width)
    H = n.height + dv.height - 4                                   # the nautilus rests on top of the DVR
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    im.alpha_composite(dv, ((W - dv.width) // 2, H - dv.height))
    im.alpha_composite(n, ((W - n.width) // 2 - 1, 0))
    return im.resize((W * scale, H * scale), Image.NEAREST)


if __name__ == '__main__':
    nautilus_dvr(4).save(os.path.join(D, 'nautilus_dvr.png'))
    nautilus_dvr(2).save(os.path.join(D, 'nautilus_dvr_small.png'))
