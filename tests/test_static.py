"""CI checks that need no vendor file: patch data shape and looks graph."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from gr8core import firmware, looks
fw = firmware.info()
import hashlib
b = open(os.path.join(os.path.dirname(__file__), '..', 'app', 'gr8core', 'data', 'vendor', 'CRESFW_eachine.BIN'), 'rb').read()
assert hashlib.sha256(b).hexdigest() == fw['vendor_sha256'], 'bundled Eachine firmware is the exact original'
assert fw['version'] and len(fw['vendor_sha256']) == 64 and len(fw['cresfw_sha256']) == 64
assert all(isinstance(o, int) and len(a) == len(b) for o, a, b in fw['patches']), 'patch entries must keep size'
assert max(o + len(b) // 2 for o, a, b in fw['patches']) <= fw['ram_size']
assert sum(len(b) // 2 for o, a, b in fw['patches']) < 8192, 'patch data only, no vendor image'
g = looks.filter_graph(looks.segments([1] * 10 + [5] * 10 + [0] * 5))
assert g.count('[0:v]trim') == 3 and 'concat=n=3' in g
print('static tests ok:', fw['name'], fw['version'], len(fw['patches']), 'patches')
firmware.build(b, 4, 0); print('build from bundled firmware ok')
