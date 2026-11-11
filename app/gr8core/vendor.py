"""Eachine's original CRESFW.BIN: bundled with GR8DVR (unmodified, credited in the notices) so the Firmware Builder
works offline. If the bundled copy is missing (e.g. a source checkout without it), it is fetched from Eachine's own
official download instead. Either way it is verified by SHA-256 before use."""
import hashlib, io, os, re, urllib.request, zipfile

from . import firmware, library

DRIVE_ID = '0Byt2NbI2R7eZVDdERF91aWxlTlE'        # Eachine's official ProDVR firmware package
URLS = [f'https://drive.google.com/uc?export=download&id={DRIVE_ID}',
        f'https://drive.usercontent.google.com/download?id={DRIVE_ID}&export=download&confirm=t']
CACHE = os.path.join(library.APPDIR, 'eachine', 'CRESFW.BIN')
UA = {'User-Agent': 'Mozilla/5.0 (GR8DVR firmware builder)'}


BUNDLED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'vendor', 'CRESFW_eachine.BIN')


def bundled():
    try:
        firmware.check_vendor(BUNDLED)
        return BUNDLED
    except firmware.FirmwareError:
        return None


def cached():
    """Path of a verified local copy, or None."""
    try:
        firmware.check_vendor(CACHE)
        return CACHE
    except firmware.FirmwareError:
        return None


def _get(url, on_progress, opener):
    with opener(urllib.request.Request(url, headers=UA), timeout=30) as r:
        total = int(r.headers.get('Content-Length') or 0)
        ctype = r.headers.get('Content-Type', '')
        buf, n = io.BytesIO(), 0
        while True:
            chunk = r.read(64 * 1024)
            if not chunk:
                break
            buf.write(chunk); n += len(chunk)
            if on_progress and total:
                on_progress(min(1.0, n / total))
        return buf.getvalue(), ctype


def _extract(blob):
    """CRESFW.BIN bytes from a zip (any folder, any case) or a bare .BIN."""
    want = firmware.info()['vendor_sha256']
    if blob[:2] == b'PK':
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for n in z.namelist():
                if os.path.basename(n).upper() == 'CRESFW.BIN':
                    data = z.read(n)
                    if hashlib.sha256(data).hexdigest() == want:
                        return data
        return None
    return blob if hashlib.sha256(blob).hexdigest() == want else None


def _follow(html):
    """Next URL from Google Drive's 'large file / can't scan' page: its download form or a confirm link."""
    import html as H
    f = re.search(r'<form[^>]*id="download-form"[^>]*action="([^"]+)"(.*?)</form>', html, re.S)
    if f:
        q = '&'.join(f'{n}={v}' for n, v in re.findall(r'name="([^"]+)"\s+value="([^"]*)"', f.group(2)))
        return H.unescape(f.group(1)) + ('?' + q if q else '')
    m = re.search(r'href="([^"]*confirm=[^"]*)"', html)
    if m:
        u = H.unescape(m.group(1))
        return 'https://drive.google.com' + u if u.startswith('/') else u
    return None


def fetch(on_progress=None, urls=None, opener=urllib.request.urlopen):
    """Download, verify and cache Eachine's CRESFW.BIN. Returns the cached path."""
    if bundled():
        return BUNDLED
    if cached():
        return CACHE
    last = 'no response'
    for url in urls or URLS:
        try:
            blob, ctype = _get(url, on_progress, opener)
        except Exception as e:                          # noqa: BLE001 - try the next mirror of the same file
            last = str(e)
            continue
        if 'html' in ctype and blob[:2] != b'PK':      # Drive's "can't scan for viruses" page -> follow its form
            nxt = _follow(blob.decode('utf-8', 'replace'))
            if nxt:
                try:
                    blob, ctype = _get(nxt, on_progress, opener)
                except Exception as e:                  # noqa: BLE001
                    last = str(e)
                    continue
        data = _extract(blob)
        if data:
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            with open(CACHE + '.tmp', 'wb') as f:
                f.write(data)
            os.replace(CACHE + '.tmp', CACHE)
            return CACHE
        last = 'the download was not the expected Eachine file'
    raise firmware.FirmwareError(f'Could not get the Eachine firmware automatically ({last}). '
                                 'Check your internet connection and try again, or pick the file yourself.')
