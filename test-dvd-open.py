import ctypes
import argparse
import sys


def open_with_mci():
    """Attempt to open the CD/DVD tray using the Windows MCI API.

    Returns:
        True if the command was sent successfully, False otherwise.
    """
    try:
        # Open the CD audio device and assign an alias 'cd'
        # Some systems require the device to be opened before sending the door command.
        buf = ctypes.create_unicode_buffer(255)
        rc = ctypes.windll.winmm.mciSendStringW("open cdaudio alias cd", buf, 254, None)
        if rc != 0:
            # Non-zero return code indicates failure (no drive or other error).
            return False

        # Send command to open the tray
        ctypes.windll.winmm.mciSendStringW("set cd door open", None, 0, None)

        # Close the device handle
        ctypes.windll.winmm.mciSendStringW("close cd", None, 0, None)
        print("Sent command to open the DVD/CD tray using MCI.")
        return True
    except Exception as e:
        print(f"MCI method raised an exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Open the DVD/CD tray on Windows (English output).")
    parser.add_argument("--method", choices=["mci"], default="mci",
                        help="Method to use for opening the tray. 'mci' is default and most portable.")
    args = parser.parse_args()

    if sys.platform != 'win32':
        print("This script only works on Windows.")
        sys.exit(1)

    # Try the requested method (currently only MCI implemented)
    if args.method == 'mci':
        ok = open_with_mci()
        if not ok:
            print("MCI method failed. The system may not have a CD/DVD drive or the device name may differ.")
            sys.exit(2)
        else:
            print("Operation completed (MCI).")


if __name__ == "__main__":
    main()