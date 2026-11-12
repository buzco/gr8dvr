"""The GR8DVR backdrop - deep space sinking into the deep sea, with sea-floor strata - rendered at any size
(numpy -> PPM -> Tk PhotoImage, no image library needed)."""
import numpy as np

STOPS = [(0.0, (0, 1, 22)), (0.3, (2, 10, 74)), (0.55, (4, 40, 150)), (0.8, (10, 82, 205)), (1.0, (16, 46, 150))]   # key-art blues
STAR_COLS = np.array([(251, 250, 255), (240, 237, 230), (170, 196, 255), (161, 174, 228)], float)
STRATA = [(0, (34, 30, 26)), (6, (52, 44, 34)), (11, (40, 34, 30)), (16, (64, 54, 40)), (22, (30, 26, 24))]


def render(W, H, floor=True, seed=7, stars=1.0, floor_at=0.86):
    W, H = max(1, int(W)), max(1, int(H))
    t = np.linspace(0, 1, H)
    col = np.stack([np.interp(t, [s[0] for s in STOPS], [s[1][i] for s in STOPS]) for i in range(3)], -1)
    img = np.repeat(col[:, None, :], W, 1)
    yy, xx = np.mgrid[0:H, 0:W]
    img += (((xx % 4) * 4 + (yy % 4) * 2 + (xx + yy) % 3) % 4 == 0)[..., None] * 2.0   # 8-bit dither
    rng = np.random.default_rng(seed)
    top = 0.33 * H
    for _ in range(max(2, W // 130)):                       # light shafts from the surface
        x0 = rng.uniform(-40, W)
        d = yy - top
        m = (d > 0) & (np.abs(xx - (x0 + d * 0.35)) < 9 + d * 0.25)
        img[m] += np.array([3.0, 6.0, 8.0])
    sky = H * 0.42
    n = int(W * sky * 0.0019 * stars)
    if n:
        ys = (rng.random(n) ** 2 * sky).astype(int)
        xs = rng.integers(0, W, n)
        a = (1 - ys / sky)[:, None]
        c = STAR_COLS[rng.integers(0, len(STAR_COLS), n)]
        img[ys, xs] = img[ys, xs] * (1 - a) + c * a
    if floor:
        x = np.arange(W)
        surf = (H * floor_at + 3 * np.sin(x / 37) + 2 * np.sin(x / 11)).astype(int)
        depth = yy - surf[None, :]
        fl = np.zeros((H, W, 3))
        for s, c in STRATA:
            fl[depth >= s] = c
        grain = ((xx + yy) % 7 == 0)[..., None] * 10.0
        m = depth >= 0
        img[m] = (fl + grain)[m]
    return np.clip(img, 0, 255).astype(np.uint8)


def floor_y(W, H, x, floor_at=0.86):
    return H * floor_at + 3 * np.sin(x / 37) + 2 * np.sin(x / 11)


def ppm(W, H, **kw):
    a = render(W, H, **kw)
    return b'P6 %d %d 255\n' % (a.shape[1], a.shape[0]) + a.tobytes()
