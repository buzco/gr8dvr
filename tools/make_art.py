#!/usr/bin/env python3
"""App artwork cut from the key illustration (tools/art/nautilus-prism.png, 970 x 580):
splash.png (boot screen), about.png (About tab, darkened + text scrim, padded so it fills any window),
sidebar.png (Firmware Builder strip), nautilus_real.png (helix storage) and nautilus_dvr(.png/_small.png)."""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'app', 'gr8core', 'data')
ART = Image.open(os.path.join(HERE, 'art', 'nautilus-prism.png')).convert('RGB')
AW, AH = ART.size                                  # 970 x 580
DEEP = (2, 4, 30)


def darken(im, k):
    return Image.eval(im, lambda v: int(v * k))


def scrim(size, box, strength, feather):
    """Soft dark rectangle (alpha mask) used to calm busy areas behind text."""
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).rectangle(box, fill=int(255 * strength))
    return m.filter(ImageFilter.GaussianBlur(feather))


def apply_scrim(im, mask, col=DEEP):
    return Image.composite(Image.new('RGB', im.size, col), im, mask)


def padded(im, W, H):
    """Centre im on a W x H canvas whose margins continue the picture as a blurred, darkened echo."""
    bg = im.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
    bg = darken(bg, .55)
    out = bg.copy()
    ox, oy = (W - im.width) // 2, (H - im.height) // 2
    fade = Image.new('L', im.size, 255)
    fd = ImageDraw.Draw(fade)
    for i in range(24):                              # feather the seam
        fd.rectangle((i, i, im.width - 1 - i, im.height - 1 - i), outline=int(255 * (i + 1) / 24))
    out.paste(im, (ox, oy), fade)
    return out


def splash():
    W, H = 600, 300
    s = W / AW
    im = ART.resize((W, round(AH * s)), Image.LANCZOS)
    im = im.crop((0, 22, W, 22 + H))
    im = darken(im, .9)
    im = apply_scrim(im, scrim((W, H), (150, 120, 450, 165), .55, 18))      # behind the version line
    im = apply_scrim(im, scrim((W, H), (0, 0, 130, 70), .35, 14))           # Buzco corner
    im.save(os.path.join(D, 'splash.png'), optimize=True)


def about():
    im = darken(ART, .82)                                                   # "a little bit" darker overall
    im = apply_scrim(im, scrim(im.size, (500, 150, 975, 480), .62, 38))     # text block (right of the shell)
    im = apply_scrim(im, scrim(im.size, (0, 0, 220, 90), .35, 20))          # Buzco corner
    padded(im, 1600, 1000).save(os.path.join(D, 'about.png'), optimize=True)


def sidebar():
    x0, x1 = 700, 905                                                       # prism on top, chip below
    strip = ART.crop((x0, 0, x1, AH))
    s = 216 / strip.width
    strip = strip.resize((216, round(AH * s)), Image.LANCZOS)
    strip = darken(strip, .86)
    strip = apply_scrim(strip, scrim(strip.size, (0, 470, 216, 545), .55, 16))      # behind the label
    H = 1000
    bg = strip.resize((216, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))
    bg = darken(bg, .6)
    out = bg.copy()
    oy = (H - strip.height) // 2
    fade = Image.new('L', strip.size, 255); fd = ImageDraw.Draw(fade)
    for i in range(30):
        fd.line((0, i, 215, i), fill=int(255 * (i + 1) / 30))
        fd.line((0, strip.height - 1 - i, 215, strip.height - 1 - i), fill=int(255 * (i + 1) / 30))
    out.paste(strip, (0, oy), fade)
    out.save(os.path.join(D, 'sidebar.png'), optimize=True)
    return oy


def nautilus_cutout():
    """GrabCut the nautilus out of the illustration (opencv only needed here, not by the app)."""
    import cv2
    bgr = cv2.cvtColor(np.asarray(ART), cv2.COLOR_RGB2BGR)
    mask = np.zeros(bgr.shape[:2], np.uint8)
    b, f = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(bgr, mask, (12, 145, 500, 425), b, f, 8, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    n, lbl, st, _ = cv2.connectedComponentsWithStats(m)
    m = np.where(lbl == 1 + np.argmax(st[1:, 4]), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    m = cv2.GaussianBlur(m, (3, 3), 0)
    rgba = ART.copy().convert('RGBA'); rgba.putalpha(Image.fromarray(m))
    # the shell runs off the bottom of the picture: fade the cut edge
    a = np.asarray(rgba).copy(); h = a.shape[0]
    a[h - 40:, :, 3] = (a[h - 40:, :, 3] * np.linspace(1, 0, 40)[:, None]).astype(np.uint8)
    rgba = Image.fromarray(a)
    return rgba.crop(rgba.getbbox())


def sprite(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def nautilus_assets():
    n = nautilus_cutout()
    sprite(n, 82).save(os.path.join(D, 'nautilus_real.png'), optimize=True)
    # Firmware Builder icon: the real nautilus resting on the real (tinted) Mini DVR
    dvr_png = '/tmp/_dvr_tinted.png'
    subprocess.run([sys.executable, os.path.join(HERE, 'cutout_dvr.py'), os.path.join(HERE, 'art', 'minidvr-photo.png'),
                    dvr_png, '900', '--tint'], check=True, stdout=subprocess.DEVNULL)
    dvr = Image.open(dvr_png).convert('RGBA')
    for scale, name in ((1, 'nautilus_dvr.png'), (.5, 'nautilus_dvr_small.png')):
        W = round(150 * scale)
        dv, nt = sprite(dvr, W), sprite(n, round(W * .7))
        H = dv.height + nt.height - round(30 * scale)
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        im.alpha_composite(dv, (0, H - dv.height))
        im.alpha_composite(nt, ((W - nt.width) // 2 - round(6 * scale), 0))
        im.save(os.path.join(D, name), optimize=True)


if __name__ == '__main__':
    splash(); about(); oy = sidebar(); nautilus_assets()
    print('art written; sidebar image offset', oy)
