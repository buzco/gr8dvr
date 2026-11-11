"""Pixel-art fossils for the GR8DVR boot screen: bone-white with sepia shading, dark outline, faint glow eyes."""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter

D = os.path.join(os.path.dirname(__file__), '..', 'app', 'gr8core', 'data')
BONE, SEP, DARK, OUT, GLOW = (232, 222, 196, 255), (170, 146, 106, 255), (110, 88, 62, 255), (40, 30, 22, 255), (90, 255, 220, 255)


def outline(im):
    """Add a 1px dark outline around opaque pixels."""
    a = im.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(3))
    o = Image.new('RGBA', im.size, OUT)
    o.putalpha(grown)
    o.alpha_composite(im)
    return o


def canvas(w, h):
    im = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def trilobite():                      # Cambrian - crawls on the sea floor, facing right
    im, d = canvas(24, 15)
    d.ellipse((2, 2, 21, 13), fill=SEP)
    d.pieslice((14, 1, 24, 14), -90, 90, fill=BONE)            # cephalon
    for x in range(5, 16, 2):                                  # thorax segments
        d.line((x, 3, x, 12), fill=DARK)
    d.rectangle((4, 6, 19, 9), fill=BONE)                      # axial lobe
    for x in range(5, 16, 2):
        d.point((x, 7), fill=DARK)
    d.polygon([(2, 5), (0, 7), (2, 10)], fill=SEP)             # pygidium
    d.line((16, 2, 10, 0), fill=SEP); d.line((16, 13, 10, 15), fill=SEP)   # genal spines
    d.point((20, 5), fill=GLOW); d.point((20, 10), fill=GLOW)  # eyes
    return outline(im)


def ammonite():                       # Mesozoic - coiled shell + tentacles, swims left->right
    im, d = canvas(28, 24)
    cx, cy = 11, 12
    d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=BONE)
    prev = None
    for i in range(0, 330):                                    # logarithmic spiral suture
        th = i / 330 * 3 * 2 * math.pi
        r = 0.9 * math.exp(0.1305 * th)
        p = (cx + r * math.cos(th), cy + r * math.sin(th))
        if prev:
            d.line((prev, p), fill=DARK)
        prev = p
    for k in range(26):                                        # ribs on the outer whorl
        th = 4 * math.pi + k / 26 * 2 * math.pi
        r0, r1 = 0.9 * math.exp(0.1305 * th), 0.9 * math.exp(0.1305 * (th + 2 * math.pi))
        r1 = min(r1, 11)
        d.line((cx + r0 * math.cos(th), cy + r0 * math.sin(th), cx + (r0 + (r1 - r0) * .8) * math.cos(th),
                cy + (r0 + (r1 - r0) * .8) * math.sin(th)), fill=SEP)
    for i, dy in enumerate((-4, -2, 0, 2, 4)):                 # tentacles from the aperture
        d.line((21, cy + dy // 2, 27, cy + dy + (1 if i % 2 else -1)), fill=SEP)
    d.point((21, cy - 4), fill=GLOW)
    return outline(im)


def anomalocaris():                   # Cambrian apex predator, lateral flaps
    im, d = canvas(40, 16)
    d.ellipse((6, 4, 34, 12), fill=SEP)
    for x in range(8, 32, 4):                                  # swimming flaps
        d.polygon([(x, 4), (x + 4, 4), (x + 2, 0)], fill=BONE)
        d.polygon([(x, 12), (x + 4, 12), (x + 2, 16)], fill=BONE)
    d.rectangle((10, 7, 32, 9), fill=BONE)
    d.polygon([(6, 6), (0, 3), (0, 13), (6, 10)], fill=SEP)    # tail fan
    d.arc((32, 6, 40, 16), 180, 330, fill=BONE)                # grasping appendages
    d.arc((32, 0, 40, 10), 30, 180, fill=BONE)
    d.point((33, 4), fill=GLOW); d.point((33, 12), fill=GLOW)  # stalked eyes
    return outline(im)


def orthocone():                      # Ordovician straight-shelled nautiloid
    im, d = canvas(44, 10)
    d.polygon([(0, 5), (34, 1), (34, 9)], fill=BONE)
    for x in range(6, 34, 4):                                  # septa
        d.line((x, 5 - x * 4 // 34, x, 5 + x * 4 // 34), fill=SEP)
    for dy in (-3, -1, 1, 3):
        d.line((34, 5 + dy // 2, 44, 5 + dy), fill=SEP)
    d.point((35, 3), fill=GLOW)
    return outline(im)


def ichthyosaur():                    # Jurassic fish-lizard skeleton
    im, d = canvas(60, 22)
    pts = [(x, 11 + 3 * math.sin((x - 8) / 9)) for x in range(6, 46)]
    for (x, y) in pts[::2]:                                    # vertebrae
        d.rectangle((x, y - 1, x + 1, y + 1), fill=BONE)
    for (x, y) in pts[8:24:2]:                                 # ribs
        d.line((x, y + 1, x - 2, y + 6), fill=SEP)
    d.polygon([(46, 8), (58, 11), (46, 14)], fill=BONE)        # long snout skull
    d.ellipse((44, 8, 50, 14), fill=BONE); d.point((47, 10), fill=GLOW)
    d.line((6, 11, 0, 3), fill=BONE); d.line((6, 11, 0, 19), fill=BONE)   # tail fluke
    d.polygon([(38, 13), (34, 20), (40, 15)], fill=SEP)        # flippers
    d.polygon([(20, 13), (17, 18), (22, 14)], fill=SEP)
    return outline(im)


def plesiosaur():                     # long-necked Mesozoic skeleton
    im, d = canvas(64, 26)
    for x in range(14, 34, 2):                                 # body spine
        d.rectangle((x, 12, x + 1, 13), fill=BONE)
    for x in range(16, 32, 2):
        d.line((x, 14, x, 18), fill=SEP)                       # ribs
    for k in range(14):                                        # neck curve
        x, y = 34 + k * 2, 12 - 6 * math.sin(k / 13 * math.pi / 2)
        d.rectangle((x, y, x + 1, y + 1), fill=BONE)
    d.ellipse((60, 3, 64, 7), fill=BONE); d.point((62, 4), fill=GLOW)
    for x in range(4, 14, 2):
        d.rectangle((x, 12 + (14 - x) // 4, x + 1, 13 + (14 - x) // 4), fill=BONE)   # tail
    for poly, c in (([(30, 12), (36, 5), (29, 11)], DARK), ([(18, 12), (13, 5), (17, 12)], DARK),
                    ([(30, 14), (35, 22), (28, 15)], SEP), ([(18, 14), (13, 22), (16, 14)], SEP)):   # paddles
        d.polygon(poly, fill=c)
    return outline(im)


def crinoid(h, frame):               # sea lily, rooted, sways
    im, d = canvas(16, h + 12)
    sway = (1 if frame else -1)
    for y in range(h):
        x = 8 + sway * (y / h) ** 2 * 2
        d.point((x, h + 11 - y), fill=SEP if y % 3 else BONE)
    top = (8 + sway * 2, 12)
    d.ellipse((top[0] - 2, top[1] - 2, top[0] + 2, top[1] + 2), fill=BONE)
    for k in range(-3, 4):                                     # feathery arms
        a = -math.pi / 2 + k * 0.38 + sway * 0.15
        d.line((top[0], top[1], top[0] + 7 * math.cos(a), top[1] + 9 * math.sin(a)), fill=BONE if k % 2 else SEP)
    return outline(im)


SPRITES = {'trilobite': trilobite, 'ammonite': ammonite, 'anomalocaris': anomalocaris, 'orthocone': orthocone,
           'ichthyosaur': ichthyosaur, 'plesiosaur': plesiosaur}


def background(W=600, H=300):
    """Deep space at the top dissolving into the abyss; strata on the sea floor."""
    rnd = random.Random(7)
    im = Image.new('RGB', (W, H))
    px = im.load()
    stops = [(0.0, (0, 0, 4)), (0.28, (4, 6, 22)), (0.45, (2, 22, 40)), (0.72, (1, 26, 38)), (1.0, (0, 8, 14))]
    for y in range(H):
        t = y / H
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                c = tuple(int(a + (b - a) * k) for a, b in zip(c0, c1))
        for x in range(W):
            # ordered dither so the gradient looks 8-bit
            b = ((x % 4) * 4 + (y % 4) * 2 + (x + y) % 3) % 4
            px[x, y] = tuple(min(255, v + (2 if b == 0 else 0)) for v in c)
    d = ImageDraw.Draw(im, 'RGBA')
    for _ in range(140):                                       # stars, fading out as we go down
        x, y = rnd.randrange(W), int(rnd.random() ** 2 * H * 0.42)
        a = int(255 * (1 - y / (H * 0.42)))
        col = rnd.choice([(255, 255, 255), (156, 242, 214), (0, 195, 137), (255, 180, 210)])
        d.point((x, y), fill=col + (a,))
        if rnd.random() < 0.08:
            d.line((x - 2, y, x + 2, y), fill=col + (a // 2,)); d.line((x, y - 2, x, y + 2), fill=col + (a // 2,))
    for k in range(5):                                         # light shafts from above the surface
        x0 = 60 + k * 120 + rnd.randrange(-20, 20)
        d.polygon([(x0, int(H * .33)), (x0 + 18, int(H * .33)), (x0 + 70, H), (x0 + 20, H)], fill=(120, 230, 255, 10))
    base = int(H * 0.86)                                       # sea floor with sediment strata
    strata = [(0, (34, 30, 26)), (6, (52, 44, 34)), (11, (40, 34, 30)), (16, (64, 54, 40)), (22, (30, 26, 24))]
    for x in range(W):
        top = base + int(3 * math.sin(x / 37) + 2 * math.sin(x / 11))
        for y in range(top, H):
            depth = y - top
            col = strata[0][1]
            for s, c in strata:
                if depth >= s:
                    col = c
            px[x, y] = col if (x + y) % 7 else tuple(v + 10 for v in col)
    for _ in range(16):                                        # little shell fossils in the strata
        x, y = rnd.randrange(W), rnd.randrange(base + 6, H - 2)
        d.arc((x - 3, y - 3, x + 3, y + 3), 0, 300, fill=(150, 130, 100, 200))
    return im


def build():
    for name, fn in SPRITES.items():
        im = fn()
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        im.save(os.path.join(D, f'fossil_{name}.png'))
        im.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(D, f'fossil_{name}_l.png'))
    for f in (0, 1):
        im = crinoid(34, f)
        im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(D, f'fossil_crinoid{f}.png'))



if __name__ == '__main__':
    build()
    names = list(SPRITES) + ['crinoid0']
    ims = [Image.open(os.path.join(D, f'fossil_{n}.png')) for n in names]
    sheet = Image.new('RGBA', (sum(i.width for i in ims) + 20 * len(ims), max(i.height for i in ims) + 20), (2, 22, 40, 255))
    x = 10
    for i in ims:
        sheet.alpha_composite(i, (x, 10)); x += i.width + 20
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save('/tmp/fossil_sheet.png')
    print('ok', sheet.size)
