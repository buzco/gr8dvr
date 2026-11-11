import hashlib, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from gr8core import firmware, looks, importer
STOCK = sys.argv[1]; CLIP = sys.argv[2]
fails = 0
def check(c, m):
    global fails; print(('ok   ' if c else 'FAIL ') + m); fails += not c
fw = firmware.info()
card = tempfile.mkdtemp()
open(os.path.join(card, 'UPOKE.BIN'), 'wb').write(b'x')
n = firmware.write(card, STOCK, 'try')
check(n == 'ADJUST.BIN' and hashlib.sha256(open(os.path.join(card, n), 'rb').read()).hexdigest() == fw['adjust_sha256'], 'try: ADJUST.BIN = released build')
check(sorted(os.listdir(card)) == ['ADJUST.BIN'], 'try: old BIN files removed, nothing else left')
n = firmware.write(card, STOCK, 'install')
check(sorted(os.listdir(card)) == ['CRESFW.BIN'] and hashlib.sha256(open(os.path.join(card, n), 'rb').read()).hexdigest() == fw['cresfw_sha256'], 'install: only CRESFW.BIN = GR8DVR')
gr8 = os.path.join(tempfile.mkdtemp(), 'CRESFW.BIN'); shutil.copy(os.path.join(card, n), gr8)
try:
    firmware.check_vendor(gr8); check(False, 'GR8DVR file rejected as base')
except firmware.FirmwareError as e:
    check('already a GR8DVR' in str(e), 'GR8DVR file rejected as base')
bad = os.path.join(tempfile.mkdtemp(), 'x.bin'); open(bad, 'wb').write(b'\0' * 1000)
try:
    firmware.write(card, bad, 'install'); check(False, 'wrong file rejected')
except firmware.FirmwareError:
    check(sorted(os.listdir(card)) == ['CRESFW.BIN'], 'wrong file rejected, card untouched')
n = firmware.write(card, STOCK, 'restore')
check(open(os.path.join(card, n), 'rb').read() == open(STOCK, 'rb').read(), 'restore: Eachine original written')
check(len(fw['patches']) > 30 and all(len(p) == 3 for p in fw['patches']), 'patch data only (no vendor image in the app)')
# looks graph sanity
g = looks.filter_graph([(0, 1, 1), (1, 2, 5), (2, None, 0)])
check(g.count('trim=') == 3 and 'pseudocolor=preset=inferno' in g and g.endswith('concat=n=3:v=1:a=0[v]'), 'looks graph built per segment')
# import a real clip
out = tempfile.mkdtemp()
logs = []
p = importer.import_clip(CLIP, out, log=logs.append)[0]
import subprocess
pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,sample_rate', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.split()
check(os.path.exists(p) and 'h264,768,576' in pr and any(x.startswith('aac') for x in pr), f'import -> {os.path.basename(p)} {pr}')
print('\n'.join(logs[:6]))
print('FAILS:', fails); sys.exit(fails > 0)
