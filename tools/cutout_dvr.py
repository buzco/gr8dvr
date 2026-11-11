#!/usr/bin/env python3
"""Cut the Mini DVR out of a product photo and give it a Y2K gloss grade.
usage: cutout_dvr.py <photo> <out.png> [width=1200]"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

src, out = sys.argv[1], sys.argv[2]
W = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
im = Image.open(src).convert('RGB')
a = np.asarray(im).astype(np.float32)
lum = a @ np.array([.299, .587, .114], np.float32)
bg = np.median(np.concatenate([lum[:20].ravel(), lum[-20:].ravel()]))
m = ndi.binary_closing(lum < bg - 40, iterations=6)
lbl, n = ndi.label(m)
m = ndi.binary_fill_holes(lbl == np.argmax(ndi.sum(m, lbl, range(1, n + 1))) + 1)
m = ndi.binary_opening(m, iterations=3)
ys, xs = np.where(m); pad = 24
box = (xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad)
alpha = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)).crop(box)
rgb = np.asarray(im.crop(box)).astype(np.float32) / 255
H, Wc = rgb.shape[:2]
# grade: deeper blacks, cool blue-teal shadows, crisp whites
L = rgb @ np.array([.299, .587, .114])
c = np.clip((rgb - .04) * 1.18, 0, 1)
shadow = (1 - np.clip(L / .35, 0, 1))[..., None]
c = c * (1 - .35 * shadow) + shadow * .35 * np.array([.05, .09, .16])
c = c + (np.clip(L - .1, 0, .3)[..., None]) * np.array([-.02, .05, .06])        # mint-cyan in the mids
# glossy diagonal streaks (screen)
yy, xx = np.mgrid[0:H, 0:Wc].astype(np.float32)
d = (xx * .62 - yy) / Wc
g = np.exp(-((d - .05) / .035) ** 2) * .22 + np.exp(-((d - .13) / .012) ** 2) * .16
c = 1 - (1 - c) * (1 - g[..., None] * np.array([.85, 1, .97]))
out_im = Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
out_im.putalpha(alpha)
out_im = out_im.resize((W, round(H * W / Wc)), Image.LANCZOS)
out_im.save(out, optimize=True)
print(out, out_im.size)

# ---- holographic glitter baked over the whole body
if '--glitter' in sys.argv:
    rng = np.random.default_rng(8)
    g = out_im.copy(); px = g.load(); A = np.asarray(g)[..., 3]
    ys, xs = np.where(A > 200)
    HOLO = [(125, 255, 212), (160, 240, 255), (255, 170, 230), (200, 180, 255), (255, 255, 255), (255, 236, 160)]
    for i in rng.choice(len(xs), size=len(xs) // 55, replace=False):
        x, y = int(xs[i]), int(ys[i]); r, gg, b = HOLO[rng.integers(len(HOLO))]
        k = rng.uniform(.35, 1.0)
        R, G_, B, a_ = px[x, y]
        px[x, y] = (int(R + (r - R) * k), int(G_ + (gg - G_) * k), int(B + (b - B) * k), a_)
        if k > .85 and x + 1 < g.width and y + 1 < g.height and A[y, x + 1] > 200:
            px[x + 1, y] = (int((R + r) / 2), int((G_ + gg) / 2), int((B + b) / 2), a_)
    g.save(out, optimize=True)
    print('glitter', out)
