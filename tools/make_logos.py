#!/usr/bin/env python3
"""Recolour the GR8DVR / Buzco logos and render every logo PNG + the app icons (ico/icns) from them.
Logo dark = blue-black, logo light = pale pearl (lighter, less saturated than the old beige). Needs rsvg-convert."""
import io, os, subprocess
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'app', 'gr8core', 'data')
L = os.path.join(HERE, 'logo')
DARK, LIGHT = '#0a1030', '#f0ede6'
OLD_DARK, OLD_LIGHT = '#2b3340', '#efe6d0'


def svg(name, panel=True):
    s = open(os.path.join(L, name)).read().replace(OLD_DARK, DARK).replace(OLD_LIGHT, LIGHT)
    if panel:                                    # open counters of the light panels -> fill them with the light colour
        vb = s.split('viewBox="')[1].split('"')[0].split()
        s = s.replace('<g id="Layer_2"', f'<rect width="{vb[2]}" height="{vb[3]}" fill="{LIGHT}"/><g id="Layer_2"', 1)
    return s


def render(svg_text, width):
    png = subprocess.run(['rsvg-convert', '-w', str(width)], input=svg_text.encode(), capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert('RGBA')


def save_rgb(im, name):
    bg = Image.new('RGB', im.size, LIGHT); bg.paste(im, (0, 0), im); bg.save(os.path.join(D, name), optimize=True)


if __name__ == '__main__':
    stacked, horiz = svg('gr8dvr-beige.svg'), svg('gr8dvr-horiz-beige.svg')
    save_rgb(render(stacked, 300), 'logo.png')
    save_rgb(render(stacked, 340), 'logo_about.png')
    save_rgb(render(horiz, 203), 'logo_horiz.png')
    buz = open(os.path.join(L, 'buzco-horiz-beige.svg')).read().replace(OLD_LIGHT, LIGHT)
    render(buz, 150).save(os.path.join(D, 'buzco.png'), optimize=True)
    render(buz, 96).save(os.path.join(D, 'buzco_small.png'), optimize=True)
    for v in ('gr8dvr', 'gr8dvr-horiz'):          # keep recoloured sources next to the originals for the web
        open(os.path.join(L, f'{v}-pearl.svg'), 'w').write(svg(f'{v}-beige.svg'))
    open(os.path.join(L, 'buzco-horiz-pearl.svg'), 'w').write(buz)
    # app icon = the full GR8DVR logo, centred on a transparent square
    icons = {}
    for size in (16, 32, 48, 64, 128, 256, 512, 1024):
        pad = max(1, size // 32)
        logo = render(stacked, (size - 2 * pad) * 2).resize((size - 2 * pad, round((size - 2 * pad) * 142 / 379.54)), Image.LANCZOS)
        sq = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        sq.alpha_composite(logo, (pad, (size - logo.height) // 2))
        icons[size] = sq
        if size in (16, 32, 48, 64, 256):
            sq.save(os.path.join(D, f'icon_{size}.png'), optimize=True)
    icons[256].save(os.path.join(D, 'gr8dvr.ico'), sizes=[(s, s) for s in (16, 32, 48, 64, 128, 256)],
                    append_images=[icons[s] for s in (16, 32, 48, 64, 128)])
    icons[1024].save(os.path.join(D, 'gr8dvr.icns'))
    print('logos + icons written')
