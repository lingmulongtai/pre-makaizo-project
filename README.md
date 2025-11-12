# Makaizo

This repository contains small utilities and Arduino sketches used to run a
simple DVD-driven motor show on Windows. The layout has been reorganized to
make each program's purpose explicit for easier sharing.

Repository layout (important files):

- `scripts/`
	- `send_arduino_command.py` — detect Arduino COM port and send a short command (used to trigger the motor).
	- `play_and_eject.py` — main show controller: play video with VLC, eject tray, and trigger Arduino.
	- `test_dvd_tray.py` — small helper that opens the DVD/CD tray (Windows MCI).

- `arduino/`
	- `sketch_nov4a.ino` — primary Arduino sketch (AccelStepper recommended).
	- `sketch_nov4a_no_accel.ino` — archived no-accel sketch (kept for reference / fallback).

Other notes
-----------

Prerequisites (Windows):

- Python 3.8+ with these packages installed:
	- `pyserial` (for Arduino serial comms)
	- `python-vlc` (for `play_and_eject.py`)

- VLC Media Player installed for video playback.

Quick usage examples (PowerShell):

```powershell
# Dry run (no serial port access) to see what would be sent:
python .\scripts\send_arduino_command.py --dry-run

# Play video (adjust --video path as needed):
python .\scripts\play_and_eject.py --video "D:\\video.mp4" --margin 10

# Test opening the tray:
python .\scripts\test_dvd_tray.py
```

Mapping of old -> new names
---------------------------

- `arduino_signal_sender.py` -> `scripts/send_arduino_command.py`
- `dvd_show_controller.py` -> `scripts/play_and_eject.py`
- `test-dvd-open.py` -> `scripts/test_dvd_tray.py`

If you want a different layout or prefer to keep everything at the top-level,
tell me and I can adapt the names / move files accordingly.

