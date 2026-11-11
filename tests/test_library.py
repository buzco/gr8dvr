"""Card scan, already-imported ledger, export names."""
import datetime, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from gr8core import library
fails = 0
def check(c, m):
    global fails; print(('ok   ' if c else 'FAIL ') + m); fails += not c
d = tempfile.mkdtemp()
a = os.path.join(d, '00000.MTS'); open(a, 'wb').write(os.urandom(3 << 20))
b = os.path.join(d, 'copy.MTS'); open(b, 'wb').write(open(a, 'rb').read())
c = os.path.join(d, 'other.MTS'); open(c, 'wb').write(os.urandom(3 << 20))
check(library.fingerprint(a) == library.fingerprint(b) != library.fingerprint(c), 'fingerprint = content, not name')
led = library.Ledger(os.path.join(d, 'led.json'))
out = os.path.join(d, 'out.mp4'); open(out, 'w').write('x')
led.add(library.fingerprint(a), a, [out])
check(library.Ledger(os.path.join(d, 'led.json')).lookup(library.fingerprint(b)) is not None, 'renamed copy is recognised')
os.remove(out)
check(led.lookup(library.fingerprint(a)) is None, 'deleted export -> clip counts as new again')
when = datetime.datetime(2026, 11, 2, 10, 30, 5)
check(library.export_name(a, when) == '2026-11-02_10-30-05_00000', 'dated name')
check(library.export_name(a, None) == '00000', 'undated name')
os.utime(a, (0, datetime.datetime(2000, 1, 1).timestamp()))
check(library.recorded(a) is None, 'clockless DVR date ignored')
check(library.recorded(a, {'creation_time': '2026-10-30T09:15:00.000000Z'}).year == 2026, 'container date used')
open(os.path.join(d, 'x.mp4'), 'w').write('1')
check(library.unique(os.path.join(d, 'x.mp4')).endswith('x (2).mp4'), 'never overwrites')
print('FAILS:', fails); sys.exit(fails)
