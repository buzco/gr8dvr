#!/usr/bin/env python3
"""Trace a reference photo of the Mini DVR into a flat, palette-limited pixel illustration.
usage: trace_dvr.py <photo> <out.png> [grid_width=320] [scale=4]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

src, out = sys.argv[1], sys.argv[2]
GW = int(sys.argv[3]) if len(sys.argv) > 3 else 320
SC = int(sys.argv[4]) if len(sys.argv) > 4 else 4

im = Image.open(src).convert('RGB')
a = np.asarray(im).astype(np.float32)
lum = a @ np.array([.299, .587, .114], np.float32)
bg = np.median(np.concatenate([lum[:20].ravel(), lum[-20:].ravel()]))
dark = lum < bg - 40                                   # the device is far darker than the backdrop
dark = ndi.binary_closing(dark, iterations=6)
lbl, n = ndi.label(dark)
big = np.argmax(ndi.sum(dark, lbl, range(1, n + 1))) + 1
mask = ndi.binary_fill_holes(lbl == big)
mask = ndi.binary_opening(mask, iterations=3)
ys, xs = np.where(mask)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
pad = 8
crop = im.crop((x0 - pad, y0 - pad, x1 + pad, y1 + pad))
m = Image.fromarray((mask[y0 - pad:y1 + pad, x0 - pad:x1 + pad] * 255).astype(np.uint8))
GH = round(crop.height * GW / crop.width)
c = np.asarray(crop.resize((GW, GH), Image.BOX)).astype(np.float32)
mm = np.asarray(m.resize((GW, GH), Image.BOX)) > 140
L = c @ np.array([.299, .587, .114], np.float32)
sat = c.max(-1) - c.min(-1)

BODY = [(14, 15, 19), (24, 26, 31), (34, 37, 44), (46, 50, 59), (62, 67, 78), (84, 90, 104)]
INK, METAL, METAL_D, GOLD = (239, 230, 208), (176, 181, 191), (118, 123, 134), (200, 160, 70)
outp = np.zeros((GH, GW, 4), np.uint8)
edges = [22, 36, 50, 66, 90]                          # luminance bands for the matte body
for y in range(GH):
    for x in range(GW):
        if not mm[y, x]:
            continue
        l, s, (r, g, b) = L[y, x], sat[y, x], c[y, x]
        if l > 168:
            col = INK
        elif s > 28 and r > g > b and l > 70:
            col = GOLD
        elif l > 128:
            col = METAL
        elif l > 100:
            col = METAL_D
        else:
            col = BODY[sum(l > e for e in edges)]
        outp[y, x] = (*col, 255)
# ---- Y2K finish: blue-black gloss plastic, mint rim light, embossed chrome print
if '--y2k' in sys.argv:
    BODY2 = [(9, 12, 20), (16, 22, 34), (25, 33, 50), (37, 48, 70), (54, 68, 96), (78, 96, 128)]
    rgb = outp[..., :3].astype(int); on = outp[..., 3] > 0
    tone = {c: i for i, c in enumerate(BODY)}
    ink = np.all(rgb == INK, -1) & on
    for y in range(GH):
        for x in range(GW):
            if not on[y, x]:
                continue
            c = tuple(rgb[y, x])
            if c in tone:
                i = tone[c]
                d = (x * 0.55 - y) / GW                      # diagonal gloss sweep across the body
                if 0.05 < d < 0.16 or (0.03 < d < 0.05 and (x + y) % 2) or (0.16 < d < 0.19 and (x + y) % 2):
                    i = min(i + 1, 5)
                outp[y, x, :3] = BODY2[i]
            elif c == INK:
                below = y + 1 < GH and on[y + 1, x] and not ink[y + 1, x]
                above = y > 0 and on[y - 1, x] and not ink[y - 1, x]
                outp[y, x, :3] = (150, 172, 184) if below else (255, 255, 255) if above else (226, 238, 242)
            elif c == METAL:
                outp[y, x, :3] = (214, 232, 236) if (x + y) % 3 else (125, 255, 212)
            elif c == METAL_D:
                outp[y, x, :3] = (104, 122, 138)
    on = outp[..., 3] > 0
    for y in range(1, GH):                                    # mint rim light on every top-facing edge
        for x in range(GW):
            if on[y, x] and not on[y - 1, x] and not ink[y, x]:
                outp[y, x, :3] = (125, 255, 212)
                if y + 1 < GH and on[y + 1, x] and not ink[y + 1, x] and x % 2 == 0:
                    outp[y + 1, x, :3] = (40, 140, 112)
    for y in range(GH):                                       # cool blue rim on the left-facing edges
        for x in range(1, GW):
            if on[y, x] and not on[y, x - 1] and on[y - 1, x] if y else False:
                if not ink[y, x] and tuple(outp[y, x, :3]) != (125, 255, 212):
                    outp[y, x, :3] = (90, 120, 170)
# 1px outline
alpha = outp[..., 3] > 0
ring = ndi.binary_dilation(alpha) & ~alpha
outp[ring] = (4, 18, 14, 255) if '--y2k' in sys.argv else (10, 11, 14, 255)
res = Image.fromarray(outp, 'RGBA')
res.resize((GW * SC, GH * SC), Image.NEAREST).save(out, optimize=True)
print(out, res.size, '->', (GW * SC, GH * SC))
