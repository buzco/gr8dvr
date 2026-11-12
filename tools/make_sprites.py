#!/usr/bin/env python3
"""Pixel-art sprites traced from reference photos (background removed, palette-limited, 1px outline):
nautilus_px.png + camcorder_px.png for the light-beam panel, nautilus_dvr(.png/_small.png) for the
Firmware Builder sidebar. Needs opencv-python-headless + scipy (build time only)."""
import os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, 'art')
D = os.path.join(HERE, '..', 'app', 'gr8core', 'data')
OUTLINE = (6, 8, 26, 255)


def biggest(m):
    lbl, n = ndi.label(m)
    if n == 0:
        return m
    return lbl == 1 + np.argmax(ndi.sum(m, lbl, range(1, n + 1)))


def cut_dark_bg(path, thr=34):
    """Subject on a black background (nautilus photo)."""
    im = Image.open(path).convert('RGB'); a = np.asarray(im).astype(np.float32)
    lum = a.max(-1)
    m = lum > thr
    m = ndi.binary_opening(m, iterations=2)
    m = biggest(m)
    m = ndi.binary_fill_holes(ndi.binary_closing(m, iterations=6))
    rgba = im.convert('RGBA'); rgba.putalpha(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1)))
    return rgba.crop(rgba.getbbox())


def cut_grabcut(path, rect):
    """Subject on a light studio background (camcorder photo)."""
    bgr = cv2.imread(path); mask = np.zeros(bgr.shape[:2], np.uint8)
    b, f = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(bgr, mask, rect, b, f, 10, cv2.GC_INIT_WITH_RECT)
    m = biggest((mask == 1) | (mask == 3))
    m = ndi.binary_fill_holes(ndi.binary_closing(m, iterations=2))
    rgba = Image.open(path).convert('RGBA'); rgba.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    return rgba.crop(rgba.getbbox())


# hand-traced outline of the camcorder photo (535 x 373): seeds GrabCut so no studio backdrop/floor survives
CAM_OUTLINE = [(44, 156), (60, 150), (100, 148), (148, 149), (152, 140), (155, 130), (175, 126), (207, 125), (212, 132),
               (240, 124), (262, 118), (283, 112), (290, 108), (305, 104), (320, 90), (350, 55), (360, 32), (375, 26),
               (400, 30), (418, 40), (425, 52), (420, 68), (400, 76), (380, 104), (388, 108), (395, 118), (398, 132),
               (400, 140), (410, 142), (414, 150), (414, 176), (408, 184), (488, 185), (489, 250), (492, 256),
               (487, 262), (485, 320), (470, 325), (300, 325), (290, 322), (240, 321), (205, 318), (170, 312),
               (155, 302), (148, 300), (120, 302), (70, 285), (55, 275), (48, 250), (42, 200), (42, 170)]


def cut_outline(path, outline):
    from PIL import ImageDraw
    bgr = cv2.imread(path); h, w = bgr.shape[:2]
    poly = Image.new('L', (w, h), 0); ImageDraw.Draw(poly).polygon(outline, fill=1)
    poly = np.asarray(poly).astype(bool)
    mask = np.full((h, w), cv2.GC_BGD, np.uint8)
    mask[ndi.binary_dilation(poly, iterations=5)] = cv2.GC_PR_BGD
    mask[poly] = cv2.GC_PR_FGD
    mask[ndi.binary_erosion(poly, iterations=7)] = cv2.GC_FGD
    b, f = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(bgr, mask, None, b, f, 8, cv2.GC_INIT_WITH_MASK)
    m = ndi.binary_fill_holes(biggest((mask == 1) | (mask == 3)))
    rgba = Image.open(path).convert('RGBA'); rgba.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    return rgba.crop(rgba.getbbox())


def pixelize(rgba, grid_w, colors, scale, sat=1.12, contrast=1.06, sharpen=80):
    """Downsample to a pixel grid (alpha-aware), crisp it up, quantise to a small palette, add a 1px outline."""
    from PIL import ImageEnhance
    gh = round(rgba.height * grid_w / rgba.width)
    small = rgba.resize((grid_w, gh), Image.LANCZOS)
    al = np.asarray(small)[..., 3]
    rgb = small.convert('RGB')
    if sharpen:
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1, percent=sharpen, threshold=2))
    rgb = ImageEnhance.Contrast(ImageEnhance.Color(rgb).enhance(sat)).enhance(contrast)
    rgbq = np.asarray(rgb.quantize(colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB'))
    on = al > 110
    out = np.zeros((gh, grid_w, 4), np.uint8)
    out[on, :3] = rgbq[on]; out[on, 3] = 255
    out[ndi.binary_dilation(on) & ~on] = OUTLINE
    return Image.fromarray(out, 'RGBA').resize((grid_w * scale, gh * scale), Image.NEAREST)


def main():
    naut = cut_dark_bg(os.path.join(ART, 'nautilus-photo.jpg'))
    naut.save('/tmp/_naut_cut.png')
    cam = cut_outline(os.path.join(ART, 'camcorder-photo.jpg'), CAM_OUTLINE)
    cam.save('/tmp/_cam_cut.png')
    pixelize(naut, 56, 24, 2).save(os.path.join(D, 'nautilus_px.png'))
    pixelize(cam, 56, 20, 2, sat=1.0).save(os.path.join(D, 'camcorder_px.png'))
    # sidebar: pixel nautilus resting on the pixel Mini DVR (from the tinted DVR cutout)
    dvr_png = '/tmp/_dvr_tinted.png'
    subprocess.run([sys.executable, os.path.join(HERE, 'cutout_dvr.py'), os.path.join(ART, 'minidvr-photo.png'),
                    dvr_png, '900', '--tint'], check=True, stdout=subprocess.DEVNULL)
    dvr = Image.open(dvr_png).convert('RGBA')
    for scale, name, gw_d, gw_n in ((2, 'nautilus_dvr.png', 76, 62), (1, 'nautilus_dvr_small.png', 76, 62)):
        dv = pixelize(dvr, gw_d, 20, scale, sat=1.0, contrast=1.0, sharpen=40)
        nt = pixelize(naut, gw_n, 24, scale)
        W = max(dv.width, nt.width)
        H = dv.height + nt.height - 8 * scale
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        im.alpha_composite(dv, ((W - dv.width) // 2, H - dv.height))
        im.alpha_composite(nt, ((W - nt.width) // 2 + 4 * scale, 0))
        im.save(os.path.join(D, name))
    print('sprites written')


if __name__ == '__main__':
    main()
