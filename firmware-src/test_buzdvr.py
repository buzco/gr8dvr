"""Emulator tests for our additions (run the REAL patched bank code from out/ADJUST.BIN in tools/emu51.py)."""
import os, random, sys
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'repo', 'open-minidvr-50i-main')
sys.path.insert(0, os.path.join(REPO, 'tools'))
from emu51 import CPU
import poke
import build_buzdvr as B

RAM = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out_v101', 'ADJUST.BIN'), 'rb').read()
DEF = B.defaults_table()
USER = poke.build(['boot write 6BEC 02', 'rec write 56E6 05'])     # a different UPOKE.BIN on the card
fails = 0
def check(c, m):
    global fails; print(('ok   ' if c else 'FAIL ') + m); fails += not c

def cpu(bank, lo, hi):
    c = CPU()
    for a in range(lo, hi):
        c.code[a] = RAM[bank * 0x8000 + a - 0x8000]
    rnd = random.Random(7)
    for i in range(0x8000): c.x[i] = rnd.randrange(256)
    c.x[0x7008:0x700C] = b'\x34\x01\x56\x02'; c.sfr[0xA8] = 0x85
    return c

def boot(card, file):
    c = cpu(10, 0xDA00, 0xE000); log = []
    c.stubs[0x0CEE] = lambda c: c.rset(7, 1 if card else 0)
    def bA7A(c):
        src = c.r(2) << 8 | c.r(1); dst = c.r(4) << 8 | c.r(0)
        for i in range(11): c.x[dst + i] = c.code[src + i]
    c.stubs[0xBA7A] = bA7A
    def l0E3E(c):
        if file is None: c.rset(7, 0); return
        c.big[0x7FFE00:0x7FFE00 + len(file)] = file; c.rset(7, 1)
    c.stubs[0x0E3E] = l0E3E
    c.stubs[0xA517] = lambda c: log.append('A517')
    c.run(0xDA00)
    return c, log

c, log = boot(True, None)
check(bytes(c.x[0x6A00:0x6A00 + len(DEF)]) == DEF, 'no UPOKE.BIN: built-in defaults in 0x6A00')
check(c.x[0x6BEC] == 1, 'no UPOKE.BIN: boot entry applied (field gate = both fields)')
check(log == ['A517'], 'no UPOKE.BIN: continues to A517 once')
check((bytes(c.x[0x7008:0x700C]), c.sfr[0xA8]) == (b'\x34\x01\x56\x02', 0x85), 'no UPOKE.BIN: window + IE intact')

c, log = boot(False, None)
check(bytes(c.x[0x6A00:0x6A00 + len(DEF)]) == DEF and c.x[0x6BEC] == 1 and log == ['A517'], 'no card: defaults applied')

c, log = boot(True, USER)
check(bytes(c.x[0x6A00:0x6A00 + len(USER)]) == USER, 'UPOKE.BIN present: file used, not defaults')
check(c.x[0x6BEC] == 2 and log == ['A517'], 'UPOKE.BIN present: its boot entries applied, continues once')

c, log = boot(True, DEF)   # card with the release preset file = same result as built-in
check(c.x[0x6BEC] == 1, 'release UPOKE.BIN: same as built-in')

# rec hook (bank13) uses the built-in table at record start
c0, _ = boot(True, None); X = bytes(c0.x)
c = cpu(13, 0xE800, 0xEA00); c.x[:] = X; c.big[0x7D0000:0x7D8000] = bytes(0x8000)
c.run(0xE800)
check(c.x[0x56E6] == 9 and c.x[0x7204] == 8 and c.x[0x7208:0x720A] == b'\x87\x05' and c.x[0x77B2:0x77B4] == b'\x08\x08',
      'rec start with built-in defaults: finest quality, centred window, 31 kHz dividers')

# mode getter bank05:B087 -> always D1 (3)
for menu in (0, 1, 2, 3, 7):
    c = cpu(5, 0xB087, 0xB0BC)
    c.stubs[0x089E] = lambda c, m=menu: c.rset(7, m)
    c.run(0xB087)
    check(c.r(7) == 3 and c.x[0x1F43] == 3, f'menu size {menu} -> record mode 3 (D1)')

# ---- key hook (bank10:DD00, main loop): presets, COM stamp, LED ----
c = cpu(10, 0xDD00, 0xDE00)
c.x[0x6BD0:0x6BD8] = b'\xff\x00\x03\x01\x00\x00\x00\x04'   # as left by the boot tail (preset 1)
c.x[0x4883:0x4886] = b'NUL'
i2c = []
c.stubs[0x0E62] = lambda c: None
c.stubs[0x065E] = lambda c: i2c.append(1)
T = [0]
def loop(right=False, left=False, menu=False, newtick=True):
    if newtick: T[0] = (T[0] + 1) & 0xFF
    c.x[0x522C] = T[0]
    c.x[0x7782] = 0xFF & ~(0x20 if right else 0)
    c.x[0x7780] = 0xFF & ~(0x80 if left else 0)
    c.x[0x7781] = 0xFF & ~(0x80 if menu else 0)
    c.run(0xDD00)
    return bool(c.x[0x7773] & 0x40)
def press(**k):
    loop(**k); loop()
def flashes(ticks=200):
    seq = [loop() for _ in range(ticks)]
    n = sum(1 for i in range(1, len(seq)) if seq[i] and not seq[i - 1])
    return n, c.x[0x6BD4]
loop()
check(bytes(c.x[0x4883:0x4886]) == b'BZ1', 'COM stamp after boot: BZ1')
loop(right=True)
check(c.x[0x6BD3] == 2 and bytes(c.x[0x4883:0x4886]) == b'BZ1', '> -> preset 2 (stamp follows on the next pass)')
loop()
loop(newtick=False)
check(bytes(c.x[0x4883:0x4886]) == b'BZ2', 'stamp BZ2 written even without a new tick')
check(flashes() == (2, 0) and not loop(), 'LED: preset 2 -> exactly 2 flashes, sequence ends with LED off')
c.x[0x7773] = 0x00; loop(); loop()
check(c.x[0x7773] == 0x00, 'after the sequence the LED is left alone (firmware owns it)')
for _ in range(6): press(right=True)
check(c.x[0x6BD3] == 8, '> x6 -> preset 8'); flashes()
press(right=True)
check(c.x[0x6BD3] == 0, '> at 8 -> 0 (none)')
seq = [loop() for _ in range(200)]
ons = [i for i in range(1, len(seq)) if seq[i] and not seq[i - 1]]
long_ = sum(seq)
check(len(ons) == 1 and long_ == 12 and c.x[0x6BD4] == 0, 'LED: preset 0 -> one long flash (12 ticks)')
loop(newtick=False)
check(bytes(c.x[0x4883:0x4886]) == b'BZ0', 'stamp BZ0 for none')
press(right=True)
check(c.x[0x6BD3] == 1, '> at 0 -> 1'); flashes()
press(left=True)
check(c.x[0x6BD3] == 0, '< at 1 -> 0'); flashes()
press(left=True)
check(c.x[0x6BD3] == 8, '< at 0 wraps to 8')
check(flashes(300) == (8, 0), 'LED: preset 8 -> exactly 8 flashes (short phases again)')
press(left=True); press(left=True); press(left=True)
check(c.x[0x6BD3] == 5, '< x3 -> preset 5')
loop(right=True); n = c.x[0x6BD3]; loop(right=True); loop(right=True)
check(c.x[0x6BD3] == n == 6, '> held -> one step only')
loop(); loop(right=True, newtick=False)
check(c.x[0x6BD3] == 6, 'press inside the same tick ignored (debounce)')
press(menu=True)
check(c.x[0x6BD3] == 6 and i2c == [], 'MENU left to the firmware; no decoder writes (mono removed)')
check(c.x[0x6BD0] == 0xFF, 'fake released pin byte kept at FF')
flashes()
loop(newtick=False)
check(bytes(c.x[0x4883:0x4886]) == b'BZ6', 'stamp BZ6')

# ---- write-buffer brake bank13:8C32 (gentle) ----
for lvl, want in ((9, 8), (5, 4), (2, 1), (1, 1)):
    c = cpu(13, 0x8C32, 0x8C47)
    c.code[0x8C47] = 0x22                     # stop where the firmware applies the new level (LCALL 13FC)
    c.x[0x56E6] = lvl
    c.run(0x8C32)
    check(c.x[0x56E6] == want, f'buffer brake: level {lvl} -> {want} (was -4)')

# ---- key scan remap bytes (bank15) ----
o = lambda a: 15 * 0x8000 + a - 0x8000
check(RAM[o(0x93A1):o(0x93A4)] == bytes.fromhex('907781'), 'scan: firmware record key reads MENU pin (7781)')
check(RAM[o(0x9410):o(0x9413)] == bytes.fromhex('906bd0') and RAM[o(0x9547):o(0x954A)] == bytes.fromhex('906bd0'),
      'scan: firmware MENU and > keys read the always-released byte')
check(RAM[10 * 0x8000 + 0xB3B:10 * 0x8000 + 0xB3E] == bytes.fromhex('12dd00'), 'main loop calls our hook')
print('FAILS:', fails); sys.exit(fails > 0)
