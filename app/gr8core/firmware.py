"""Build GR8DVR from Eachine's original CRESFW.BIN (bundled, see NOTICES) plus GR8DVR's patch data."""
import hashlib, json, os, shutil

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'firmware.json')


class FirmwareError(Exception):
    pass


def info():
    with open(DATA) as f:
        return json.load(f)


def check_vendor(path):
    """Return the vendor file's bytes if it is the exact Eachine file GR8DVR is built for."""
    fw = info()
    try:
        data = open(path, 'rb').read()
    except OSError as e:
        raise FirmwareError(f'Could not read the file: {e}')
    h = hashlib.sha256(data).hexdigest()
    if h == fw['cresfw_sha256']:
        raise FirmwareError('This is already a GR8DVR file, not the Eachine original. Pick Eachine\'s CRESFW.BIN.')
    if h != fw['vendor_sha256']:
        raise FirmwareError('This is not the Eachine firmware GR8DVR needs '
                            f'(expected {fw["vendor_size"]:,} bytes, SHA-256 {fw["vendor_sha256"][:12]}…). '
                            'Download Eachine\'s official ProDVR firmware and pick its CRESFW.BIN.')
    return data


def build(vendor_bytes, preset=None, fps=None):
    """Return (adjust_image, cresfw_image) for GR8DVR with the user's power-on defaults
    (preset 0-8, fps 1 = 50p/60p or 0 = 25p/30p). The released build is verified first, then only the two
    default bytes are changed."""
    fw = info()
    ram = bytearray(vendor_bytes) + b'\xff' * (fw['ram_size'] - len(vendor_bytes))
    for off, old, new in fw['patches']:
        if ram[off:off + len(old) // 2].hex() != old:
            raise FirmwareError(f'Unexpected bytes at 0x{off:x} - wrong base file.')
        ram[off:off + len(new) // 2] = bytes.fromhex(new)
    adjust, cres = bytes(ram), bytes(ram[:fw['vendor_size']])
    if hashlib.sha256(adjust).hexdigest() != fw['adjust_sha256'] or hashlib.sha256(cres).hexdigest() != fw['cresfw_sha256']:
        raise FirmwareError('Build check failed (result does not match the released GR8DVR). Nothing was written.')
    cfg = fw['config']
    for key, val, lo, hi in (('preset', preset, 0, 8), ('fps', fps, 0, 1)):
        if val is None:
            continue
        if not lo <= int(val) <= hi:
            raise FirmwareError(f'Invalid {key}: {val}')
        ram[cfg[key]] = int(val)
    return bytes(ram), bytes(ram[:fw['vendor_size']])


def _clean_card(card):
    for n in ('ADJUST.BIN', 'CRESFW.BIN', 'UPOKE.BIN'):
        for name in (n, '._' + n):                       # '._' = macOS AppleDouble twin on FAT cards
            p = os.path.join(card, name)
            if os.path.exists(p):
                os.remove(p)


def write(card, vendor_path, mode, preset=None, fps=None):
    """mode: 'try' (ADJUST.BIN, runs from RAM once, nothing flashed), 'install' (CRESFW.BIN, permanent),
    'restore' (Eachine original as CRESFW.BIN). Returns the file name written."""
    if not os.path.isdir(card):
        raise FirmwareError('Pick the SD card (its root folder).')
    data = check_vendor(vendor_path)
    if mode == 'restore':
        name, blob = 'CRESFW.BIN', data
    else:
        adjust, cres = build(data, preset, fps)
        name, blob = ('ADJUST.BIN', adjust) if mode == 'try' else ('CRESFW.BIN', cres)
    _clean_card(card)
    tmp = os.path.join(card, name + '.tmp')
    with open(tmp, 'wb') as f:
        f.write(blob); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, os.path.join(card, name))
    if open(os.path.join(card, name), 'rb').read() != blob:
        raise FirmwareError('Read-back check failed: the card did not store the file correctly. Try another card.')
    return name
