"""The 8 GR8DVR looks (+ 0 = none), applied per segment from the per-frame stamps (JPEG COM "BZ0".."BZ8")."""
import struct

BF = "curves=all='0/0 0.155/0 0.24/0.07 0.42/0.34 0.72/0.71 1/1',eq=saturation=1.12"
LOOKS = {
    0: ('None', 'Original picture, no grade', 'null'),
    1: ('Black Fix', 'Real blacks instead of the analog grey floor', BF),
    2: ('Soft Cinema', 'Gentle S-curve, warm highlights', BF + ",curves=all='0/0 0.25/0.22 0.5/0.5 0.75/0.78 1/0.97',colorbalance=rh=0.025:gh=0.01:bh=-0.02:bs=0.015,eq=saturation=0.93"),
    3: ('Dusk Split', 'Yellow highlights, blue shadows, purple mids', BF + ",colorbalance=rs=-0.02:bs=0.07:rm=0.035:gm=-0.025:bm=0.04:rh=0.05:gh=0.04:bh=-0.06,eq=saturation=0.97"),
    4: ('Teal & Orange', 'The classic film combo, subtle', BF + ",colorbalance=rs=-0.06:gs=0.015:bs=0.06:rm=0.02:bm=-0.02:rh=0.06:gh=0.02:bh=-0.06,eq=saturation=1.04"),
    5: ('Thermal', 'Heat-camera false colour (inferno)', BF + ",format=yuv444p,pseudocolor=preset=inferno"),
    6: ('Viridis', 'Viridis colour ramp', BF + ",format=yuv444p,pseudocolor=preset=viridis"),
    7: ('Turbo', 'Turbo colour ramp', BF + ",format=yuv444p,pseudocolor=preset=turbo"),
    8: ('Aerochrome IR', 'Infrared film: foliage turns pink-red', BF + ",colorchannelmixer=rr=0.15:rg=0.85:gr=0.85:gg=0.15:bb=1,eq=saturation=1.25:contrast=1.05"),
}
# Overscan crop (as a CRT hid it): drops the bottom lines where the DVR's encoder can overtake the capture,
# the WSS dots on the top line and the side edges; keeps 4:3, square pixels.
OVERSCAN = 'crop=660:540:30:4,scale=768:576:flags=lanczos,setsar=1'
FULL = 'scale=768:576:flags=lanczos,setsar=1'


def stamps(avi):
    """(fps_mode, preset) per recorded field from the JPEG COM stamp: "B5n" = 50p/60p, "B2n" = 25p/30p,
    legacy "BZn" = 50p; unstamped = (1, 0)."""
    with open(avi, 'rb') as f:
        d = f.read()
    movi = d.find(b'movi') - 4
    i = d.rfind(b'idx1')
    if movi < 0 or i < 0:
        return []
    n = struct.unpack('<I', d[i + 4:i + 8])[0] // 16
    out = []
    for k in range(n):
        cid, _, off, sz = struct.unpack('<4sIII', d[i + 8 + 16 * k:i + 24 + 16 * k])
        if cid != b'00dc':
            continue
        fr = d[movi + off + 8:movi + off + 8 + min(sz, 1024)]
        c = fr.find(b'\xff\xfe')
        t = fr[c + 4:c + 7] if c >= 0 else b''
        if len(t) == 3 and t[:1] == b'B' and 0 <= t[2] - 48 <= 8:
            out.append((0 if t[1:2] == b'2' else 1, t[2] - 48))
        else:
            out.append((1, 0))
    return out


def segments(tags, rate=50.0):
    segs, start = [], 0
    for j in range(1, len(tags) + 1):
        if j == len(tags) or tags[j] != tags[start]:
            segs.append((start / rate, j / rate, tags[start]))
            start = j
    return segs or [(0.0, 0.0, 0)]


def fps_mode(st):
    """Clip output mode: the mode most of the clip was filmed in (1 = 50p/60p, 0 = 25p/30p)."""
    return 1 if not st or sum(m for m, _ in st) * 2 >= len(st) else 0


def filter_graph(segs, overscan=True, looks=True, pre=''):
    base = (pre + ',' if pre else '') + (OVERSCAN if overscan else FULL)
    if not looks:
        segs = [(0.0, None, 0)]
    fc, labels = [], []
    for k, (a, b, p) in enumerate(segs):
        end = '' if (k == len(segs) - 1 or b is None) else f':end={b:.4f}'
        fc.append(f"[0:v]trim=start={a:.4f}{end},setpts=PTS-STARTPTS,{base},{LOOKS[p][2]},format=yuv420p[v{k}]")
        labels.append(f'[v{k}]')
    fc.append(''.join(labels) + f'concat=n={len(labels)}:v=1:a=0[v]')
    return ';'.join(fc)
