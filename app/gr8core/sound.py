"""Tiny async WAV player for the retro UI sounds."""
import os
import shutil
import subprocess

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
enabled = True


def play(name):
    if not enabled:
        return
    path = os.path.join(DATA, name + '.wav')
    if not os.path.exists(path):
        return
    try:
        if os.name == 'nt':
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        elif shutil.which('afplay'):
            subprocess.Popen(['afplay', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which('aplay'):
            subprocess.Popen(['aplay', '-q', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:                                     # noqa: BLE001 - a sound must never break the app
        pass
