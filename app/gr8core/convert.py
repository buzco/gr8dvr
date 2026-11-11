"""General media converter (any ffmpeg-readable video -> MP4/MOV/MKV/GIF/audio), rotate, preview frames."""
import json, os
import subprocess as _sp
from . import procs

_NOWIN = {'creationflags': 0x08000000} if os.name == 'nt' else {}   # previews are not cancellable jobs

VIDEO_EXT = ('.mts', '.m2ts', '.ts', '.avi', '.mov', '.mp4', '.m4v', '.mkv', '.wmv', '.mpg', '.mpeg', '.vob',
             '.3gp', '.flv', '.webm', '.dv', '.mod', '.tod')
ROTATIONS = {'0°': '', '90° ⟳': 'transpose=1', '90° ⟲': 'transpose=2', '180°': 'transpose=1,transpose=1',
             'Mirror': 'hflip'}
FORMATS = {   # label: (extension, video args, audio args, description)
    'MP4 · H.264 (plays everywhere)': ('.mp4', ['-c:v', 'libx264', '-pix_fmt', 'yuv420p'], ['-c:a', 'aac', '-b:a', '192k'],
                                      'Best for phones, Instagram, WhatsApp, iPhone and PC editing.'),
    'MP4 · H.265 (half the size)': ('.mp4', ['-c:v', 'libx265', '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1'], ['-c:a', 'aac', '-b:a', '192k'],
                                   'Smaller files at the same quality. Newer devices only.'),
    'MOV · ProRes 422 (editing)': ('.mov', ['-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le'], ['-c:a', 'pcm_s16le'],
                                  'Huge files, perfect for Premiere / Resolve / Final Cut.'),
    'MKV · H.264 (archive)': ('.mkv', ['-c:v', 'libx264', '-pix_fmt', 'yuv420p'], ['-c:a', 'flac'],
                             'Same picture as MP4 with lossless FLAC audio.'),
    'GIF (short clips)': ('.gif', [], [], 'Animated GIF, 480 px wide, 15 fps. Keep clips short.'),
    'MP3 · audio only': ('.mp3', ['-vn'], ['-c:a', 'libmp3lame', '-b:a', '256k'], 'Just the sound.'),
}
QUALITY = {'High': '16', 'Medium': '20', 'Small': '24'}


def probe(path):
    """Duration, size, interlacing, rotation of the first video stream."""
    r = procs.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', path],
                  capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
    except ValueError:
        return None
    v = next((s for s in j.get('streams', []) if s.get('codec_type') == 'video'), None)
    fmt = j.get('format', {})
    dur = float(fmt.get('duration', 0) or 0)
    ct = (fmt.get('tags') or {}).get('creation_time') or ((v or {}).get('tags') or {}).get('creation_time')
    if not v:
        return {'duration': dur, 'video': False, 'creation_time': ct, 'format': fmt.get('format_name')}
    fo = v.get('field_order', 'progressive')
    return {'duration': dur, 'video': True, 'width': v.get('width'), 'height': v.get('height'),
            'codec': v.get('codec_name'), 'interlaced': fo not in ('progressive', 'unknown', None),
            'fps': v.get('avg_frame_rate', '0/1'), 'creation_time': ct, 'format': fmt.get('format_name'),
            'rotation': _rot(v)}


def _rot(v):
    for sd in v.get('side_data_list', []) or []:
        if 'rotation' in sd:
            return int(sd['rotation'])
    return int((v.get('tags') or {}).get('rotate', 0) or 0)


def vfilters(info, rotate='0°', deinterlace=True, gif=False):
    f = []
    if deinterlace and info and info.get('interlaced'):
        f.append('bwdif=mode=send_field')            # interlaced camcorder footage (AVCHD 50i/60i, DV) -> smooth 50p/60p
    if ROTATIONS.get(rotate):
        f.append(ROTATIONS[rotate])
    if gif:
        f.append('fps=15,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse')
    return ','.join(f)


def command(src, dst, fmt, quality='High', rotate='0°', deinterlace=True, info=None):
    ext, vargs, aargs, _ = FORMATS[fmt]
    gif = ext == '.gif'
    vf = vfilters(info, rotate, deinterlace, gif)
    cmd = ['ffmpeg', '-hide_banner', '-v', 'error', '-y', '-i', src]
    if ext == '.mp3':
        return cmd + vargs + aargs + ['-progress', 'pipe:1', '-nostats', dst]
    if vf:
        cmd += ['-filter_complex' if gif else '-vf', vf]
    if gif:
        return cmd + ['-an', '-progress', 'pipe:1', '-nostats', dst]
    if vargs and vargs[1] in ('libx264', 'libx265'):
        vargs = vargs + ['-crf', QUALITY[quality], '-preset', 'slow']
    extra = ['-movflags', '+faststart'] if ext in ('.mp4', '.mov') else []
    return cmd + vargs + aargs + extra + ['-progress', 'pipe:1', '-nostats', dst]


def convert(src, out_dir, fmt, quality='High', rotate='0°', deinterlace=True, on_progress=None, name=None, info=None):
    info = info or probe(src)
    if info is None:
        raise RuntimeError('not a media file ffmpeg can read')
    ext = FORMATS[fmt][0]
    dst = os.path.join(out_dir, (name or os.path.splitext(os.path.basename(src))[0]) + ext)
    if os.path.abspath(dst) == os.path.abspath(src):
        dst = os.path.splitext(dst)[0] + '_converted' + ext
    os.makedirs(out_dir, exist_ok=True)
    p = procs.Popen(command(src, dst, fmt, quality, rotate, deinterlace, info), stdout=procs.PIPE,
                    stderr=procs.PIPE, text=True)
    dur = info['duration'] or 1
    for line in p.stdout:
        if line.startswith('out_time_us=') and on_progress:
            try:
                on_progress(min(1.0, int(line.split('=')[1]) / 1e6 / dur))
            except ValueError:
                pass
    err = p.stderr.read()
    rc = p.wait()
    procs._live.discard(p)
    if procs.cancelled:
        if os.path.exists(dst):
            os.remove(dst)
        raise procs.Cancelled()
    if rc != 0:
        raise RuntimeError(err.strip().splitlines()[-1] if err.strip() else 'ffmpeg failed')
    if on_progress:
        on_progress(1.0)
    return dst


def preview_png(src, t=0.0, rotate='0°', width=320, info=None, size=None):
    """One frame as PNG bytes (for the preview pane). size='320:240' forces a shape (DVR field pictures)."""
    vf = vfilters(info, rotate, deinterlace=True)
    vf = (vf + ',' if vf else '') + (f'scale={size}' if size else f'scale={width}:-2')
    if size and ROTATIONS.get(rotate):
        vf = f'scale={size},' + ROTATIONS[rotate]
    pre = max(0.0, t - 3.0)                      # coarse seek, then accurate decode (robust on .mts/.ts)
    for seek in (['-ss', f'{pre:.2f}', '-i', src, '-ss', f'{t - pre:.2f}'], ['-i', src, '-ss', f'{t:.2f}']):
        r = _sp.run(['ffmpeg', '-v', 'error'] + seek + ['-frames:v', '1', '-vf', vf,
                     '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, **_NOWIN)
        if r.stdout:
            return r.stdout
    return b''


def describe(info, fmt, quality, rotate, deinterlace):
    """Plain-language list of exactly what will happen to this clip."""
    if not info:
        return 'Reading the clip…'
    ext, vargs, _, desc = FORMATS[fmt]
    lines = []
    if info.get('video'):
        lines.append(f"Source: {info.get('codec', '?').upper()} {info['width']}×{info['height']} "
                     f"{'interlaced' if info.get('interlaced') else 'progressive'}, {_fps(info.get('fps'))} fps, "
                     f"{info['duration']:.1f} s")
        if deinterlace and info.get('interlaced') and ext != '.mp3':
            lines.append(f"Deinterlace: bwdif, each field becomes a frame → {_fps(info.get('fps'), 2)} fps smooth motion")
        if ROTATIONS.get(rotate):
            lines.append(f'Rotate: {rotate}')
    if ext == '.gif':
        lines.append('Output: GIF, 480 px wide, 15 fps, optimised palette, no sound')
    elif ext == '.mp3':
        lines.append('Output: MP3 256 kbit/s, sound only')
    else:
        codec = {'libx264': 'H.264', 'libx265': 'H.265 (HEVC)', 'prores_ks': 'ProRes 422 HQ'}[vargs[1]]
        q = f", quality CRF {QUALITY[quality]} ({quality.lower()})" if vargs[1] != 'prores_ks' else ''
        lines.append(f'Video: {codec}{q}, same resolution')
        lines.append('Audio: ' + {'.mov': 'uncompressed PCM', '.mkv': 'lossless FLAC'}.get(ext, 'AAC 192 kbit/s'))
        lines.append(f'Container: {ext[1:].upper()}' + (' with fast-start (plays while downloading)'
                                                        if ext in ('.mp4', '.mov') else ''))
    return '\n'.join(lines)


def _fps(r, mul=1):
    try:
        a, b = (r or '0/1').split('/')
        v = float(a) / float(b) * mul
        return f'{v:.2f}'.rstrip('0').rstrip('.')
    except (ValueError, ZeroDivisionError):
        return '?'
