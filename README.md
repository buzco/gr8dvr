# GR8DVR

Free firmware + importer for the common 53×33 mm **mini FPV DVR** (MJPEG, 3 buttons, 400 mAh) when used as a
capture box for analog / MiniDV camcorders. By Buzco · [gr8success.xyz/pages/gr8dvr](https://www.gr8success.xyz/pages/gr8dvr)

## What GR8DVR 1.0.1 does
- **True 50i**: every field recorded (stock drops half), centred 704 px D1, always D1 whatever the menu says
- **Finest JPEG quality**, higher bitrate target, gentle write-buffer brake (no 2 s blocky dips)
- **31 kHz audio** (stock 8 kHz)
- **Buttons**: MENU = record, ◀/▶ = preset 0-8, red LED flashes the preset number (0 = one long flash)
- **Per-frame look stamps**: the importer grades each part of a clip with the preset you picked while filming
- Built-in settings: no files needed on the card after installing

## GR8DVR Utility (Windows)
`GR8DVR.exe`: **Try first** (runs once from RAM, nothing flashed) · **Install** · **Restore stock** ·
**Import** (weave 50i → overscan crop → looks → H.264 MP4, or original without looks).
The app includes Eachine's original ProDVR `CRESFW.BIN` (unmodified, © Eachine, see `NOTICES.txt`) and applies
GR8DVR's patches to it on your computer, checking every byte. Nothing to download separately.

## Looks
0 None · 1 Black Fix · 2 Soft Cinema · 3 Dusk Split · 4 Teal & Orange · 5 Thermal · 6 Viridis · 7 Turbo · 8 Aerochrome IR

## Credits & licences
- Built on **[open-minidvr-50i](https://github.com/eonflux7/open-minidvr-50i)** by eonflux7 (MIT): 50i capture,
  RAM boot, poke hook, audio clock, `weave.py` (included unchanged in `app/gr8core/weave.py`).
- The Windows build bundles **FFmpeg** (GPL build by BtbN, source: https://ffmpeg.org) as separate executables.
- GR8DVR code: MIT. Eachine's original firmware is included unmodified for convenience; all rights belong to
  Eachine / the manufacturer and no ownership is claimed (rights holders: contact us via gr8success.xyz).
- Credits: Eachine (base firmware), eonflux7 / open-minidvr-50i (MIT, the research this builds on), FFmpeg (GPL),
  NumPy (BSD), Python/Tk (PSF). Full text in `NOTICES.txt`.
- Flashing firmware is at your own risk. Keep the battery charged and USB connected while the DVR updates.
