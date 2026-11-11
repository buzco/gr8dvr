"""Automatic Eachine download: zip / bare bin / Drive warning page / wrong file - against a local fake server."""
import http.server, io, os, sys, tempfile, threading, zipfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
os.environ['APPDATA'] = tempfile.mkdtemp()
from gr8core import firmware, library, vendor
vendor.CACHE = os.path.join(library.APPDIR.replace(library.APPDIR, os.environ['APPDATA']), 'GR8DVR', 'eachine', 'CRESFW.BIN')
STOCK = open(sys.argv[1], 'rb').read()
zb = io.BytesIO()
with zipfile.ZipFile(zb, 'w') as z:
    z.writestr('ProDVR firmware/readme.txt', 'x'); z.writestr('ProDVR firmware/cresfw.bin', STOCK)
ROUTES = {'/zip': (zb.getvalue(), 'application/zip'), '/bin': (STOCK, 'application/octet-stream'),
          '/warn': (b'<html><a href="/zip?x=1&amp;confirm=t">Download anyway</a></html>', 'text/html'),
          '/bad': (b'\0' * 5000, 'application/octet-stream')}
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body, ct = ROUTES[self.path.split('?')[0]]
        self.send_response(200); self.send_header('Content-Type', ct); self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
srv = http.server.HTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{srv.server_port}'
import urllib.request
def opener(req, timeout):                                   # rewrite drive.google.com links to the fake server
    u = req.full_url.replace('https://drive.google.com', base)
    return urllib.request.urlopen(urllib.request.Request(u, headers=req.headers), timeout=timeout)
fails = 0
def check(c, m):
    global fails; print(('ok   ' if c else 'FAIL ') + m); fails += not c
def fresh():
    if os.path.exists(vendor.CACHE): os.remove(vendor.CACHE)
for route in ('/zip', '/bin', '/warn'):
    fresh(); prog = []
    p = vendor.fetch(prog.append, urls=[base + route], opener=opener)
    check(open(p, 'rb').read() == STOCK and vendor.cached(), f'{route}: verified Eachine file cached')
fresh()
try:
    vendor.fetch(urls=[base + '/bad'], opener=opener); check(False, 'wrong file rejected')
except firmware.FirmwareError:
    check(not vendor.cached(), 'wrong file rejected, nothing cached')
fresh()
p = vendor.fetch(urls=['http://127.0.0.1:9/nothing', base + '/zip'], opener=opener)
check(vendor.cached() is not None, 'falls back to the second link')
print('FAILS:', fails); sys.exit(fails)
