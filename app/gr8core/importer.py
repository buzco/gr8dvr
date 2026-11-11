"""Import DVR recordings: weave both fields (open-minidvr-50i weave), overscan crop, looks, MP4."""
import argparse, glob, os, shutil, tempfile
from . import looks, procs, weave

weave.subprocess = procs

def find_clips(folder):
    """AVI recordings in a card root, its DCIM folders, or a plain folder."""
    pats = ['DCIM/*/*.AVI', 'DCIM/*/*.avi', '*.AVI', '*.avi']
    seen, out = set(), []
    for p in pats:
        for f in sorted(glob.glob(os.path.join(folder, p))):
            k = os.path.normcase(os.path.abspath(f))
            if k not in seen and os.path.getsize(f) > 64 * 1024:
                seen.add(k); out.append(f)
    return out


def weave_args(bob=True):
    return argparse.Namespace(bob=bob, both=False, prores=False, crf='14', w704=False, widescreen=False, wss=20.0,
                              parity='auto', pause=False, files=[])


def import_clip(src, dst_dir, use_looks=True, overscan=True, keep_576i=False, log=print, out_name=None, rotate='0°'):
    """Returns the list of files written. out_name = file name without extension."""
    name = os.path.splitext(os.path.basename(src))[0]
    stem = out_name or name
    os.makedirs(dst_dir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix='gr8dvr_')
    try:
        st = looks.stamps(src)
        p50 = looks.fps_mode(st) == 1
        mid = os.path.join(tmpdir, name + ('_p50.mp4' if p50 else '_i25.mp4'))
        log(f'{name}: weaving fields -> {"50p/60p smooth" if p50 else "25p/30p cinematic"}')
        weave.convert(src, mid, weave_args(p50))
        if keep_576i:
            log(f'{name}: 576i master')
            master = os.path.join(dst_dir, stem + '_576i.mp4')
            weave.convert(src, master, weave_args(False))
        segs = looks.segments([p for _, p in st]) if use_looks else [(0.0, None, 0)]
        for a, b, p in segs:
            if b is not None:
                log(f'  {a:7.2f}s - {b:7.2f}s  preset {p} {looks.LOOKS[p][0]}')
        out = os.path.join(dst_dir, stem + ('_GR8DVR.mp4' if use_looks else '_original.mp4'))
        log(f'{name}: grading -> {os.path.basename(out)}')
        graph = looks.filter_graph(segs, overscan, use_looks, pre='' if p50 else 'bwdif=mode=send_frame')
        from .convert import ROTATIONS
        vout = '[v]'
        if ROTATIONS.get(rotate):
            graph += f';[v]{ROTATIONS[rotate]}[vr]'
            vout = '[vr]'
        procs.run(['ffmpeg', '-v', 'error', '-y', '-i', mid, '-filter_complex', graph, '-map', vout, '-map', '0:a?',
                        '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out],
                       check=True)
        return [out] + ([master] if keep_576i else [])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
