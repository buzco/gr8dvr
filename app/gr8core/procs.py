"""Every ffmpeg the app starts goes through here: no console windows on Windows, and Cancel can stop them all."""
import os
import subprocess as _sp

PIPE, DEVNULL, CalledProcessError = _sp.PIPE, _sp.DEVNULL, _sp.CalledProcessError
_live = set()
cancelled = False


class Cancelled(Exception):
    pass


def Popen(*a, **k):
    if os.name == 'nt':
        k.setdefault('creationflags', 0x08000000)
    if cancelled:
        raise Cancelled()
    p = _sp.Popen(*a, **k)
    _live.add(p)
    return p


def run(cmd, check=False, capture_output=False, input=None, **k):
    if capture_output:
        k['stdout'], k['stderr'] = PIPE, PIPE
    p = Popen(cmd, stdin=PIPE if input is not None else None, **k)
    try:
        out, err = p.communicate(input)
    finally:
        _live.discard(p)
    if cancelled:
        raise Cancelled()
    if check and p.returncode:
        raise CalledProcessError(p.returncode, cmd, out, err)
    return _sp.CompletedProcess(cmd, p.returncode, out, err)


def cancel():
    global cancelled
    cancelled = True
    for p in list(_live):
        try:
            p.kill()
        except OSError:
            pass
    _live.clear()


def reset():
    global cancelled
    cancelled = False
