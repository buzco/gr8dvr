#!/usr/bin/env python3
"""Generate app/gr8core/data/firmware.json from the firmware build (patch data only: offsets + bytes, no vendor code)."""
import hashlib, json, os, sys
FW = os.path.expanduser('~/fw'); sys.path.insert(0, '/home/claude/fw')
import build_buzdvr as B
REPO = B.REPO
meta = json.load(open(os.path.join(REPO, 'docs', 'patch.json')))
patches = [list(p) for p in meta['patches']] + [list(p) for p in B.our_patches(True)]
stock = sys.argv[1]
ram = bytearray(open(stock, 'rb').read()); assert hashlib.sha256(ram).hexdigest() == meta['cresfw_sha256']
ram += b'\xff' * (meta['ram_size'] - len(ram))
for off, old, new in patches:
    assert ram[off:off + len(old) // 2].hex() == old, hex(off)
    ram[off:off + len(new) // 2] = bytes.fromhex(new)
out = {
    'name': 'GR8DVR', 'version': sys.argv[2],
    'vendor_file': 'CRESFW.BIN (Eachine ProDVR / HMDVR 2015.05.26.01.IR)',
    'vendor_sha256': meta['cresfw_sha256'], 'vendor_size': meta['cresfw_size'], 'ram_size': meta['ram_size'],
    'adjust_sha256': hashlib.sha256(ram).hexdigest(),
    'cresfw_sha256': hashlib.sha256(ram[:meta['cresfw_size']]).hexdigest(),
    'credits': 'Built on open-minidvr-50i (MIT, eonflux7): 50i capture, RAM boot, poke hook, 31 kHz audio.',
    'config': {k: v for k, v in B.config_offsets().items()},
    'config_defaults': {'preset': B.DEFAULT_PRESET, 'fps': B.DEFAULT_FPS},
    'patches': patches,
}
json.dump(out, open(os.path.join(os.path.dirname(__file__), '..', 'app', 'gr8core', 'data', 'firmware.json'), 'w'), indent=0)
print(out['version'], len(patches), 'patches; CRESFW', out['cresfw_sha256'][:16], 'ADJUST', out['adjust_sha256'][:16])
