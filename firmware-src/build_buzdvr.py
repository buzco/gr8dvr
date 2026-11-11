#!/usr/bin/env python3
"""Build our DVR firmware on top of open-minidvr-50i release 1 (MIT).

Adds, on top of docs/patch.json:
  1. Built-in default settings: if UPOKE.BIN is missing (or no card), the boot hook (bank10) fills the poke
     buffer 0x6A00 with the release preset (pokes/release_50i.txt) and applies its boot entries. A UPOKE.BIN on the
     card still overrides everything (that is how the settings editor will work).
  2. Always D1: bank05:B087 (menu Size -> record mode) always returns mode 3 (D1 704x288), whatever the menu says.

  3. Rate target doubled (q 4 -> 2): JPEG stays at the finest level; coarser levels caused the bottom tear
     (PICT0019: 27% torn-looking fields at level 8 vs 11% at level 9).

Usage: build_buzdvr.py CRESFW.BIN OUTDIR
Writes OUTDIR/ADJUST.BIN (RAM test, nothing flashed) and OUTDIR/CRESFW.BIN (permanent install, later).
"""
import hashlib, json, os, sys
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'repo', 'open-minidvr-50i-main')
sys.path.insert(0, os.path.join(REPO, 'tools')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import poke

B10 = 10 * 0x8000 - 0x8000          # RAM/flash offset of bank10 CPU address a = B10 + a
B05 = 5 * 0x8000 - 0x8000

def defaults_table():
    return poke.build(open(os.path.join(REPO, 'pokes', 'release_50i.txt')).read().splitlines())

from asm51 import assemble
H = bytes.fromhex
def dptr(a): return bytes([0x90, a >> 8, a & 0xFF])
def movx_imm(a, v): return dptr(a) + bytes([0x74, v, 0xF0])          # [a] = v

KEYVARS = 0x6BD0   # 6BD0 = 0xFF fake "released" pin for keys hidden from the firmware, 6BD1 last tick,
                   # 6BD2 previous pressed bits (bit0 = >, bit1 = <), 6BD3 preset 1..8,
                   # 6BD4 LED phase counter, 6BD5 ticks left in phase, 6BD6 = 2 * flashes, 6BD7 ticks per phase
                   # preset 0 = none (stamp BZ0, one long flash), 1..8 = looks (N short flashes)
COM = 0x4883       # JPEG header template 4640 (copied into every frame): COM segment text "NUL" -> "BZn"
LED_PORT, LED_ON = 0x7773, 0x40     # red record LED = 7773 bit 6 (polarity: bit set = on, unverified)
PHASE = 4                           # ticks per LED phase (tick ~ 1 per frame)

def boot_tail():
    # reset our key/preset state (preset 1), then continue where the firmware's boot path continues
    return [movx_imm(0x6BD0, 0xFF), movx_imm(0x6BD1, 0x00), movx_imm(0x6BD2, 0x03), movx_imm(0x6BD3, 0x01),
            movx_imm(0x6BD4, 0x00), movx_imm(0x6BD5, 0x00), movx_imm(0x6BD6, 0x00), movx_imm(0x6BD7, PHASE),
            ('ljmp', 0xA517)]

def hook_code():
    tbl = defaults_table()
    items = [('label', 'succ'), ('lcall', 0xDA8E), ('ljmp', 'tail'),          # DB00: apply file entries
             ('label', 'dflt'), dptr(0x6A00)]                                 # DB06: built-in defaults
    for b in tbl:
        items.append(bytes([0x74, b, 0xF0, 0xA3]))                           # MOV A,#b; MOVX @DPTR,A; INC DPTR
    items += [H('7F01'), ('lcall', 0xDA8E), ('label', 'tail')] + boot_tail()
    code, labels = assemble(0xDB00, items)
    assert labels['succ'] == 0xDB00 and labels['dflt'] == 0xDB06
    return code

def key_code():
    """Main-loop hook (bank10:8B3B, was LCALL 0E62 = key scan): run the firmware's scan, then ours.
    Physical keys (active low): < = 7780.7, MENU = 7781.7, > = 7782.5. The scan is patched so the firmware's
    record key reads MENU and its other two keys read 6BD0 (always released).
    < / > step the preset 1..8 (wrapping); every frame's JPEG COM says "BZ<preset>"; the red LED pauses
    3 phases, then flashes <preset> times (PHASE ticks on / PHASE off, ending off), then is handed back to
    the firmware. Preset 0 (none) = one long flash (3 x PHASE)."""
    items = [
        movx_imm(0x6BD0, 0xFF),
        ('lcall', 0x0E62),                                   # firmware key scan (bank15:9371)
        # stamp the preset into the JPEG header template (every pass: cheap, survives any re-init)
        movx_imm(COM, ord('B')), movx_imm(COM + 1, ord('Z')),
        dptr(0x6BD3), H('E0'), H('2430'), dptr(COM + 2), H('F0'),       # '0' + preset
        # once per system tick
        dptr(0x522C), H('E0FF'),
        dptr(0x6BD1), H('E06F'), ('jnz', 'newtick'), ('ljmp', 'done'),
        ('label', 'newtick'),
        H('EFF0'),
        # ---- LED sequence ----
        dptr(0x6BD4), H('E0'), ('jz', 'keys'),               # idle
        dptr(0x6BD5), H('E014F0'), ('jnz', 'ledset'),        # ticks left in phase -1
        H('C0E0'), dptr(0x6BD7), H('E0'), dptr(0x6BD5), H('F0'), H('D0E0'),   # new phase: reload length
        dptr(0x6BD4), H('E014F0'), ('jz', 'keys'),           # phase counter -1; 0 = done, firmware owns LED
        ('label', 'ledset'),
        dptr(0x6BD4), H('E0FE'),                             # R6 = phase counter
        dptr(0x6BD6), H('E0C39E'), ('jc', 'off'),            # counter > 2N -> pause (off)
        H('EE'), ('jb', 0xE0, 'off'),                        # odd -> off, even -> on (ends with an off phase)
        dptr(LED_PORT), H('E044%02XF0' % LED_ON), ('sjmp', 'keys'),
        ('label', 'off'),
        dptr(LED_PORT), H('E054%02XF0' % (0xFF ^ LED_ON)),
        # ---- keys ----
        ('label', 'keys'),
        H('7E00'),                                           # R6 = pressed bits
        dptr(0x7782), H('E0'), ('jb', 0xE5, 'n1'), H('EE4401FE'),   # > pressed -> bit0
        ('label', 'n1'),
        dptr(0x7780), H('E0'), ('jb', 0xE7, 'n2'), H('EE4402FE'),   # < pressed -> bit1
        ('label', 'n2'),
        dptr(0x6BD2), H('E0F4'), H('5EFD'),                  # R5 = ~prev & now (new presses)
        H('EEF0'),                                           # prev = now
        H('ED'), ('jnb', 0xE0, 'nl'),
        dptr(0x6BD3), H('E004'), ('cjne', 9, 'st'), H('E4'), ('sjmp', 'st'),        # > : next, 8 -> 0 (none)
        ('label', 'nl'),
        H('ED'), ('jb', 0xE1, 'prev'), ('ljmp', 'done'),
        ('label', 'prev'),
        dptr(0x6BD3), H('E0'), ('jnz', 'dec'), H('7409'), ('label', 'dec'), H('14'),   # < : previous, 0 -> 8
        ('label', 'st'),
        H('F0FF'),                                           # store preset, R7 = preset
        H('7E%02X' % PHASE), ('jnz', 'nz'),                  # R6 = phase length
        H('7F01'), H('7E%02X' % (PHASE * 3)),                # preset 0: one long flash
        ('label', 'nz'),
        dptr(0x6BD7), H('EEF0'),
        H('EF2F'), dptr(0x6BD6), H('F0'),                    # 2N
        H('2403'), dptr(0x6BD4), H('F0'),                    # phases = 2N + 3 (3 off phases first)
        dptr(0x6BD5), H('EEF0'),
        ('label', 'done'), H('22'),
    ]
    code, _ = assemble(0xDD00, items)
    return code

# (offset, original, new)
def our_patches(keys=True):
    code = hook_code()
    assert 0xDB00 + len(code) < 0xDD00
    p = [
        (B10 + 0xDA88, '12da8e', '02db00'),                 # success path -> DB00 (apply file entries, continue)
        (B10 + 0xDA8B, '02a517', '02db06'),                 # no card / no UPOKE.BIN -> built-in defaults
        (B10 + 0xDB00, '00' * len(code), code.hex()),
        (B05 + 0xB08A, 'ef60', '8014'),                     # B087: MOV A,R7; JZ -> SJMP B0A0 ([1F43]=3, D1)
        (0x294DB, '04', '02'),                              # rate target w*h/q: q 4 -> 2 (~100 KB/field), so rate
        (0x2A6E6, '04', '02'),                              #   control never steps coarser (coarse = tearing band)
    ]
    if keys:
        kc = key_code()
        B15 = 15 * 0x8000 - 0x8000
        p += [
            (B10 + 0xDD00, '00' * len(kc), kc.hex()),
            (B10 + 0x8B3B, '120e62', '12dd00'),             # main loop: key scan -> our hook (calls the scan)
            (B15 + 0x93A1, '907780', '907781'),             # firmware record key reads MENU instead of <
            (B15 + 0x9410, '907781', '906bd0'),             # firmware MENU key: always released
            (B15 + 0x9547, '907782', '906bd0'),             # firmware > key: always released
        ]
    p += [
        # write-buffer brake (bank13:8C26): was "level -= 4 (min 1)" in one go -> now 1 level per check (min 1);
        # it runs per frame, so it still steps further if the buffer stays short
        (13 * 0x8000 - 0x8000 + 0x8C38, '04', '01'),
        (13 * 0x8000 - 0x8000 + 0x8C3D, 'fc', 'ff'),
    ]
    return p

def build(src, outdir):
    meta = json.load(open(os.path.join(REPO, 'docs', 'patch.json')))
    ram = bytearray(open(src, 'rb').read())
    if hashlib.sha256(ram).hexdigest() != meta['cresfw_sha256']:
        sys.exit('not the tested Eachine CRESFW.BIN - refusing')
    ram += b'\xff' * (meta['ram_size'] - len(ram))
    for off, old, new in meta['patches'] + [list(p) for p in our_patches(KEYS)]:
        if ram[off:off + len(old) // 2].hex() != old:
            sys.exit(f'unexpected bytes at 0x{off:x}')
        ram[off:off + len(new) // 2] = bytes.fromhex(new)
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'ADJUST.BIN'), 'wb').write(ram)
    open(os.path.join(outdir, 'CRESFW.BIN'), 'wb').write(ram[:meta['cresfw_size']])
    for n in ('ADJUST.BIN', 'CRESFW.BIN'):
        d = open(os.path.join(outdir, n), 'rb').read()
        print(f'{n}: {len(d)} bytes sha256 {hashlib.sha256(d).hexdigest()}')
    return ram

KEYS = '--nokeys' not in sys.argv
if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
