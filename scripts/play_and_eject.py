"""Play a video, eject the DVD tray, and trigger an Arduino motor.

This is the primary show controller script (Windows). It plays a video in VLC,
waits for it to complete, then ejects the DVD tray and triggers an Arduino motor.

Prerequisites:
  pip install python-vlc pyserial
  Install VLC Media Player on the machine.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import serial
import serial.tools.list_ports
import vlc

# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------
IOCTL_STORAGE_EJECT_MEDIA = 0x2D4808
DEFAULT_VIDEO_FILE_PATH = "test.mp4"
DEFAULT_MARGIN_SECONDS = 10.0
DEFAULT_EJECT_WAIT_SECONDS = 5.0
POLL_INTERVAL_SECONDS = 5.0
ARDUINO_KEYWORDS = ("Arduino", "CH340", "USB-SERIAL")


@dataclass
class ControllerConfig:
    """User-adjustable settings captured from the command line."""

    video_path: str
    margin_seconds: float
    eject_wait_seconds: float
    dry_run: bool
    arduino_port: Optional[str] = None


def parse_arguments(argv: Optional[Sequence[str]] = None) -> ControllerConfig:
    """Parse CLI arguments and return a :class:`ControllerConfig`."""

    parser = argparse.ArgumentParser(
        description="Play a video, eject the DVD tray, and trigger an Arduino motor."
    )
    parser.add_argument(
        "--video",
        default=DEFAULT_VIDEO_FILE_PATH,
        help="Path to the video file to play (defaults to test.mp4)",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=DEFAULT_MARGIN_SECONDS,
        help="Seconds to wait after the video ends before opening the tray.",
    )
    parser.add_argument(
        "--eject-wait",
        type=float,
        default=DEFAULT_EJECT_WAIT_SECONDS,
        help="Seconds to wait after ejecting before firing the motor.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip ejecting the tray and sending the Arduino command (for testing).",
    )
    parser.add_argument(
        "--port",
        help="Optional explicit COM port for the Arduino (e.g. COM3).",
    )

    args = parser.parse_args(argv)
    video_path = os.path.abspath(args.video)

    return ControllerConfig(
        video_path=video_path,
        margin_seconds=args.margin,
        eject_wait_seconds=args.eject_wait,
        dry_run=args.dry_run,
        arduino_port=args.port,
    )


def find_arduino_port(preferred_port: Optional[str] = None) -> Optional[str]:
    """Return the COM port that most likely hosts the Arduino board."""

    if preferred_port:
        print(f"Using provided Arduino port: {preferred_port}")
        return preferred_port

    print("Searching for Arduino port...")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if any(keyword in port.description for keyword in ARDUINO_KEYWORDS):
            print(f"Found Arduino at: {port.device}")
            return port.device
    return None


def connect_to_arduino(preferred_port: Optional[str] = None) -> serial.Serial:
    """Open a serial connection to the Arduino, waiting briefly for reset."""

    port = find_arduino_port(preferred_port)
    if port is None:
        raise RuntimeError("Could not find Arduino. Please check the USB connection.")

    print(f"Connecting to Arduino on {port}...")
    connection = serial.Serial(port=port, baudrate=9600, timeout=0.1)
    time.sleep(2)  # Allow the Arduino bootloader to finish resetting
    return connection


def ensure_video_exists(video_path: str) -> str:
    """Verify that the requested video can be found on disk."""

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    return video_path


def start_video_playback(video_path: str) -> Tuple[vlc.Instance, vlc.MediaPlayer]:
    """Initialise VLC, play the requested video, and validate startup success."""

    ensure_video_exists(video_path)
    print("File found. Initializing VLC...")

    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    player.set_fullscreen(True)

    print("Starting video playback...")
    player.play()
    time.sleep(1)  # Give VLC a moment to begin playback

    state = player.get_state()
    if state in (vlc.State.Error, vlc.State.Ended, vlc.State.Stopped):
        raise RuntimeError(f"VLC failed to start playback. State: {state}")

    return instance, player


def wait_until_video_finishes(
    player: vlc.MediaPlayer, poll_interval: float = POLL_INTERVAL_SECONDS
) -> None:
    """Block until VLC reports that the video has finished playing."""

    print("Video is playing... (checking state periodically)")
    state = player.get_state()
    while state not in (vlc.State.Ended, vlc.State.Stopped, vlc.State.Error):
        time.sleep(poll_interval)
        state = player.get_state()

    if state == vlc.State.Error:
        raise RuntimeError("Video playback ended with an error.")

    print("Video playback finished.")


def open_tray_mci(alias: str = "cd") -> bool:
    """Attempt to open the tray using the Windows MCI API."""

    try:
        rc = ctypes.windll.winmm.mciSendStringW(
            f"open cdaudio alias {alias}", None, 0, None
        )
        if rc != 0:
            print(f"MCI open reported error code: {rc}")
            return False

        ctypes.windll.winmm.mciSendStringW(f"set {alias} door open", None, 0, None)
        ctypes.windll.winmm.mciSendStringW(f"close {alias}", None, 0, None)
        print("Sent eject command via MCI.")
        return True
    except Exception as exc:  # pragma: no cover - Windows-specific
        print(f"MCI method raised exception: {exc}")
        return False


def open_tray_ioctl(drive_letter: str) -> bool:
    """Attempt to open the tray via IOCTL_STORAGE_EJECT_MEDIA."""

    try:
        dl = drive_letter.strip().upper()
        if len(dl) == 1:
            dl += ':'
        if dl.endswith('\\'):
            dl = dl[:-1]

        path = f"\\\\.\\{dl}"
        kernel32 = ctypes.windll.kernel32
        GENERIC_READ = 0x80000000
        FILE_SHARE_READ = 0x00000001
        FILE_SHARE_WRITE = 0x00000002
        OPEN_EXISTING = 3

        handle = kernel32.CreateFileW(
            path,
            GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            0,
            None,
        )
        INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
        if handle == INVALID_HANDLE_VALUE:
            print(f"CreateFile failed for {path}")
            return False

        bytes_returned = ctypes.c_ulong()
        result = kernel32.DeviceIoControl(
            handle,
            IOCTL_STORAGE_EJECT_MEDIA,
            None,
            0,
            None,
            0,
            ctypes.byref(bytes_returned),
            None,
        )
        kernel32.CloseHandle(handle)
        if result:
            print("Sent eject command via IOCTL.")
            return True
        print("DeviceIoControl returned failure.")
        return False
    except Exception as exc:  # pragma: no cover - Windows-specific
        print(f"IOCTL method raised exception: {exc}")
        return False


def open_tray(drive_letter: Optional[str]) -> bool:
    """Open the tray using MCI first, then IOCTL as a fallback."""

    if open_tray_mci():
        return True

    if drive_letter:
        print(f"Falling back to IOCTL for drive {drive_letter}")
        return open_tray_ioctl(drive_letter)

    print("No fallback available (no drive letter).")
    return False


def infer_drive_letter(video_path: str) -> Optional[str]:
    """Infer the optical drive letter from the video path if possible."""

    if len(video_path) >= 2 and video_path[1] == ':':
        return video_path[:2]
    return None


def trigger_arduino_motor(arduino: serial.Serial, command: bytes = b"M") -> None:
    """Send the motor activation command to the Arduino."""

    arduino.write(command)
    arduino.flush()
    print("Motor command sent to Arduino.")


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Application entry point."""

    if sys.platform != "win32":
        raise SystemExit("This script currently supports Windows only.")

    config = parse_arguments(argv)

    arduino: Optional[serial.Serial] = None
    player: Optional[vlc.MediaPlayer] = None
    _vlc_instance: Optional[vlc.Instance] = None  # Keep a reference alive while playing

    try:
        arduino = connect_to_arduino(config.arduino_port)

        print(f"Checking for video file: {config.video_path}")
        _vlc_instance, player = start_video_playback(config.video_path)

        wait_until_video_finishes(player)

        print(f"Waiting for margin: {config.margin_seconds} seconds...")
        time.sleep(config.margin_seconds)

        drive_letter = infer_drive_letter(config.video_path)

        if config.dry_run:
            print("Dry run enabled: skipping tray eject and motor command.")
        else:
            print("Ejecting DVD drive...")
            if not open_tray(drive_letter):
                raise RuntimeError(
                    f"Failed to open the tray for drive {drive_letter or 'unknown'}."
                )

            print(f"Waiting {config.eject_wait_seconds} seconds for tray to open...")
            time.sleep(config.eject_wait_seconds)

            trigger_arduino_motor(arduino)

    except Exception as exc:
        print("\n" + "=" * 30)
        print("FATAL ERROR:")
        print(f"An error occurred: {exc}")
        print("STOPPING SCRIPT. No signal sent to Arduino.")
        print("=" * 30 + "\n")
    finally:
        print("--- Cleaning up resources ---")

        if player is not None:
            try:
                print("Stopping VLC player...")
                player.stop()
            except Exception:
                pass

        if arduino is not None and getattr(arduino, "is_open", False):
            try:
                print("Closing connection to Arduino...")
                arduino.close()
            except Exception:
                pass

        print("Process complete.")


if __name__ == "__main__":
    main()
