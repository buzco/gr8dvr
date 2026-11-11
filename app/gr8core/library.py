"""Finds cards/camcorders, remembers what was already imported, names exports, keeps settings."""
import datetime
import glob
import hashlib
import json
import os
import string
import sys


if os.name == 'nt':
    APPDIR = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'GR8DVR')
elif sys.platform == 'darwin':
    APPDIR = os.path.expanduser('~/Library/Application Support/GR8DVR')
else:
    APPDIR = os.path.join(os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config'), 'GR8DVR')
SETTINGS = os.path.join(APPDIR, 'settings.json')
LEDGER = os.path.join(APPDIR, 'imported.json')

KINDS = {
    'avchd': ('Camcorder (AVCHD)', ['PRIVATE/AVCHD/BDMV/STREAM/*.MTS', 'PRIVATE/AVCHD/BDMV/STREAM/*.mts',
                                    'AVCHD/BDMV/STREAM/*.MTS', 'AVCHD/BDMV/STREAM/*.mts']),
    'dvr': ('Mini DVR card', ['*.AVI', '*.avi', 'DCIM/*/PICT*.AVI', 'DCIM/*/PICT*.avi']),
    'camera': ('Camera card', ['DCIM/*/*.MP4', 'DCIM/*/*.MOV', 'DCIM/*/*.mp4', 'DCIM/*/*.mov', 'DCIM/*/*.AVI',
                               'DCIM/*/*.MTS', 'PRIVATE/M4ROOT/CLIP/*.MP4', 'MP_ROOT/*/*.MP4', 'MP_ROOT/*/*.MOD']),
}


# ------------------------------------------------------------ settings
def load_settings():
    try:
        with open(SETTINGS, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(**kw):
    s = load_settings()
    s.update(kw)
    os.makedirs(APPDIR, exist_ok=True)
    with open(SETTINGS, 'w', encoding='utf-8') as f:
        json.dump(s, f, indent=1)


# ------------------------------------------------------------ drives
def drives():
    """[(root, removable)] - removable cards first."""
    if os.name != 'nt':
        roots = [p for p in glob.glob('/media/*/*') + glob.glob('/run/media/*/*') + glob.glob('/Volumes/*')
                 if os.path.isdir(p) and os.path.realpath(p) != '/']      # macOS: skip the startup disk alias
        return [(r, True) for r in roots]
    import ctypes
    out = []
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, d in enumerate(string.ascii_uppercase):
        if mask >> i & 1 and d not in 'AB':
            root = f'{d}:\\'
            t = ctypes.windll.kernel32.GetDriveTypeW(root)
            if t in (2, 3):                      # 2 removable, 3 fixed (USB card readers sometimes say fixed)
                out.append((root, t == 2))
    return sorted(out, key=lambda r: not r[1])


def scan(kinds=('avchd', 'camera'), extra=()):
    """Find sources: [{'kind','label','root','clips'}]. Only removable drives + remembered/extra folders."""
    found = []
    roots = [r for r, rem in drives() if rem] + [p for p in extra if p and os.path.isdir(p)]
    seen = set()
    for root in roots:
        for k in kinds:
            label, pats = KINDS[k]
            clips = []
            for p in pats:
                clips += glob.glob(os.path.join(root, p))
            if k == 'dvr':
                clips = [c for c in clips if os.path.basename(c).upper().startswith('PICT')]
            clips = sorted({os.path.normcase(os.path.abspath(c)): c for c in clips
                            if os.path.getsize(c) > 64 * 1024}.values())
            if clips:
                key = (k, os.path.normcase(os.path.abspath(root)))
                if key not in seen:
                    seen.add(key)
                    found.append({'kind': k, 'label': f'{label} on {root.rstrip(chr(92))}', 'root': root,
                                  'clips': clips})
    return found


def folder_clips(folder, exts):
    out = []
    for a, _, ns in os.walk(folder):
        out += [os.path.join(a, n) for n in sorted(ns) if n.lower().endswith(exts)]
    return out


# ------------------------------------------------------------ already imported?
def fingerprint(path):
    """Content id (size + first/last MiB): survives renames and the camera reusing 00000.MTS on a new card."""
    h = hashlib.sha1()
    size = os.path.getsize(path)
    h.update(str(size).encode())
    with open(path, 'rb') as f:
        h.update(f.read(1 << 20))
        if size > 2 << 20:
            f.seek(-(1 << 20), 2)
            h.update(f.read())
    return h.hexdigest()[:20]


class Ledger:
    def __init__(self, path=LEDGER):
        self.path = path
        try:
            with open(path, encoding='utf-8') as f:
                self.data = json.load(f)
        except (OSError, ValueError):
            self.data = {}

    def lookup(self, fp):
        """Earlier export for this clip if its file still exists, else None."""
        e = self.data.get(fp)
        if e and any(os.path.exists(o) for o in e.get('outputs', [])):
            return e
        return None

    def add(self, fp, src, outputs):
        self.data[fp] = {'source': os.path.basename(src), 'outputs': list(outputs),
                         'when': datetime.datetime.now().isoformat(timespec='seconds')}
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=1)
        os.replace(tmp, self.path)


# ------------------------------------------------------------ names
def recorded(path, info=None):
    """When the clip was filmed: container tag, else file time if plausible, else None.
    (The mini DVR has no clock, so its file dates are meaningless.)"""
    tag = (info or {}).get('creation_time')
    if tag:
        try:
            return datetime.datetime.fromisoformat(tag.replace('Z', '+00:00')).astimezone().replace(tzinfo=None)
        except ValueError:
            pass
    t = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    if 2005 <= t.year and t <= datetime.datetime.now() + datetime.timedelta(days=1):
        return t
    return None


def export_name(src, when, suffix=''):
    """2026-11-11_14-32-05_00425.mp4  /  undated: 00425.mp4"""
    base = os.path.splitext(os.path.basename(src))[0]
    stamp = when.strftime('%Y-%m-%d_%H-%M-%S_') if when else ''
    return f'{stamp}{base}{suffix}'


def unique(path):
    if not os.path.exists(path):
        return path
    a, b = os.path.splitext(path)
    n = 2
    while os.path.exists(f'{a} ({n}){b}'):
        n += 1
    return f'{a} ({n}){b}'


def dated_dir(base):
    return os.path.join(base, datetime.date.today().isoformat())


def default_base(sub):
    v = os.path.join(os.path.expanduser('~'), 'Movies' if sys.platform == 'darwin' else 'Videos')
    return os.path.join(v if os.path.isdir(v) else os.path.expanduser('~'), 'GR8DVR', sub)


def human_size(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or u == 'GB':
            return f'{n:.0f} {u}' if u in ('B', 'KB') else f'{n:.1f} {u}'
        n /= 1024



