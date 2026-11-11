# GR8DVR

Free firmware + importer for the common 53×33 mm **mini FPV DVR** (MJPEG, 3 buttons, 400 mAh) when used as a
capture box for analog / MiniDV camcorders. By Buzco · [gr8success.xyz/pages/gr8dvr](https://www.gr8success.xyz/pages/gr8dvr)

## Download
| System | File |
|---|---|
| Windows 10 / 11 | [GR8DVR.exe](https://github.com/buzco/gr8dvr/releases/latest/download/GR8DVR.exe) |
| macOS 11+ · Apple Silicon (M1-M4) | [GR8DVR-macOS-AppleSilicon.zip](https://github.com/buzco/gr8dvr/releases/latest/download/GR8DVR-macOS-AppleSilicon.zip) |
| macOS 11+ · Intel | [GR8DVR-macOS-Intel.zip](https://github.com/buzco/gr8dvr/releases/latest/download/GR8DVR-macOS-Intel.zip) |

GR8DVR is new and not code-signed. **Windows:** "unrecognised app" → More info → Run anyway.
**macOS:** unzip, drag GR8DVR to Applications, then right-click → Open the first time
(macOS 15+: System Settings → Privacy & Security → Open Anyway).

## What the GR8DVR firmware does
- **True 50i**: every field recorded (stock drops half), centred 704 px D1, always D1 whatever the menu says
- **Finest JPEG quality**, higher bitrate target, gentle write-buffer brake (no 2 s blocky dips)
- **31 kHz audio** (stock 8 kHz)
- **Buttons**: MENU = record, ▶ = next look 0-8 (red LED flashes the number), ◀ = 60 / 30 fps
- **Your start-up defaults**: the builder bakes your chosen look and frame rate into your personal firmware
- **Per-frame look stamps**: the importer grades each part of a clip with the look you picked while filming

## The GR8DVR app (Windows + macOS)
- **Media Converter**: AVCHD (.MTS), DV, AVI, MOV, MKV, VOB… → MP4 / H.265 / ProRes / GIF / MP3, with preview, rotate,
  date-based file names and an "already imported" memory.
- **Mini DVR Import**: finds the card by itself, weaves 50i → smooth 50p or cinematic 25p, edge crop, looks → H.264 MP4.
- **Mini DVR Firmware Builder**: **Try first** (runs once from RAM, nothing flashed) · **Install** · **Restore stock**.
  The app includes Eachine's original ProDVR `CRESFW.BIN` (unmodified, © Eachine, see `NOTICES.txt`) and applies
  GR8DVR's patches to it on your computer, checking every byte. Nothing to download separately.
- Run from source on any OS: `pip install numpy`, install ffmpeg, then `python app/gr8dvr.py`.

## Looks
0 None · 1 Black Fix · 2 Soft Cinema · 3 Dusk Split · 4 Teal & Orange · 5 Thermal · 6 Viridis · 7 Turbo · 8 Aerochrome IR

## Credits & licences
- Built on **[open-minidvr-50i](https://github.com/eonflux7/open-minidvr-50i)** by eonflux7 (MIT): 50i capture,
  RAM boot, poke hook, audio clock, `weave.py` (included unchanged in `app/gr8core/weave.py`).
- The builds bundle **FFmpeg** as separate executables (GPL; Windows build by BtbN, macOS static build from
  ffmpeg.martin-riedl.de; source: https://ffmpeg.org).
- GR8DVR code: MIT. Eachine's original firmware is included unmodified for convenience; all rights belong to
  Eachine / the manufacturer and no ownership is claimed (rights holders: contact us via gr8success.xyz).
- Credits: Eachine (base firmware), eonflux7 / open-minidvr-50i (MIT, the research this builds on), FFmpeg (GPL),
  NumPy (BSD), Python/Tk (PSF). Full text in `NOTICES.txt`.
- Flashing firmware is at your own risk. Keep the battery charged and USB connected while the DVR updates.
