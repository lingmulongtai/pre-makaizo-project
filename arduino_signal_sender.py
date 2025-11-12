"""Minimal Arduino signal sender.

This standalone helper loads the same ideas as ``dvd_show_controller.py`` but only
focuses on discovering the Arduino serial port and pushing a command byte
sequence. Use it when you want to trigger the board without running the full
show controller workflow.

Prerequisites
-------------
1. Install pyserial (``pip install pyserial``).
2. Plug the Arduino into the PC via USB and confirm it appears in Device Manager.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Iterable, Optional

import serial
import serial.tools.list_ports

ARDUINO_KEYWORDS: tuple[str, ...] = ("Arduino", "CH340", "USB-SERIAL")
DEFAULT_BAUDRATE = 9600
DEFAULT_TIMEOUT = 0.1
RESET_DELAY_SECONDS = 2.0


def find_arduino_port(keywords: Iterable[str] = ARDUINO_KEYWORDS) -> Optional[str]:
    """Return the most likely COM port that hosts an Arduino device."""

    print("Searching for Arduino port...")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if any(keyword in port.description for keyword in keywords):
            print(f"Found Arduino at: {port.device}")
            return port.device
    print("No Arduino-like device was detected.")
    return None


def connect_to_arduino(port: str, baudrate: int, timeout: float) -> serial.Serial:
    """Create and return an open serial connection to the Arduino."""

    print(f"Opening serial connection to {port} @ {baudrate} baud...")
    connection = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    time.sleep(RESET_DELAY_SECONDS)  # allow any auto-reset to complete
    return connection


def send_command(arduino: serial.Serial, payload: bytes, append_newline: bool) -> None:
    """Write ``payload`` (plus optional newline) to the serial connection."""

    data = payload + (b"\n" if append_newline else b"")
    arduino.write(data)
    arduino.flush()
    print(f"Sent {len(data)} bytes to Arduino.")


def parse_arguments(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Build a CLI interface so the script can be reused from a shell."""

    parser = argparse.ArgumentParser(
        description="Detect an Arduino serial port and send a single command string."
    )
    parser.add_argument(
        "--port",
        help="Explicit COM port to use (e.g. COM3). If omitted, auto-detect by name.",
    )
    parser.add_argument(
        "--command",
        default="M",
        help="ASCII command/string to send to the Arduino (default: 'M').",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=DEFAULT_BAUDRATE,
        help=f"Serial baud rate (default: {DEFAULT_BAUDRATE}).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Serial timeout in seconds (default: {DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--no-newline",
        action="store_true",
        help="Do not append a trailing newline to the command (default is newline).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without opening the port or sending data.",
    )

    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the command-line utility."""

    if sys.platform != "win32":
        raise SystemExit("This helper currently targets Windows-based serial ports.")

    args = parse_arguments(argv)

    if args.dry_run:
        target_port = args.port or "<auto-detect>"
        print(
            "Dry run enabled – nothing will be sent.\n"
            f"  Port: {target_port}\n"
            f"  Baudrate: {args.baudrate}\n"
            f"  Timeout: {args.timeout}\n"
            f"  Command: {args.command!r} (newline={'off' if args.no_newline else 'on'})"
        )
        return

    port = args.port or find_arduino_port()
    if port is None:
        raise SystemExit("Aborting: no Arduino port could be determined.")

    try:
        connection = connect_to_arduino(port, args.baudrate, args.timeout)
        send_command(connection, args.command.encode("utf-8"), not args.no_newline)
    finally:
        if "connection" in locals() and connection.is_open:
            print("Closing serial connection...")
            connection.close()


if __name__ == "__main__":
    main()
