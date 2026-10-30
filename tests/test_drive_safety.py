import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


def load_controller():
    serial = types.ModuleType("serial")
    serial.Serial = object
    serial.tools = types.ModuleType("serial.tools")
    serial.tools.list_ports = types.ModuleType("serial.tools.list_ports")
    vlc = types.ModuleType("vlc")
    path = Path(__file__).resolve().parents[1] / "scripts" / "play_and_eject.py"
    spec = importlib.util.spec_from_file_location("play_and_eject_test", path)
    module = importlib.util.module_from_spec(spec)
    modules = {"serial": serial, "serial.tools": serial.tools,
               "serial.tools.list_ports": serial.tools.list_ports,
               "vlc": vlc, spec.name: module}
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class DriveSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = load_controller()

    def test_inferred_drive_must_be_optical(self):
        get_type = Mock(side_effect=[3, 5, 0])
        windll = types.SimpleNamespace(kernel32=types.SimpleNamespace(GetDriveTypeW=get_type))
        with patch.object(self.controller.ctypes, "windll", windll, create=True):
            self.assertIsNone(self.controller.infer_drive_letter(r"C:\test.mp4"))
            self.assertEqual(self.controller.infer_drive_letter(r"D:\video.mp4"), "D:")
            self.assertIsNone(self.controller.infer_drive_letter(r"E:\video.mp4"))
            self.assertIsNone(self.controller.infer_drive_letter(r"\\server\share\video.mp4"))
        self.assertEqual([call.args[0] for call in get_type.call_args_list], ["C:\\", "D:\\", "E:\\"])

    def test_failed_drive_query_disables_fallback(self):
        kernel32 = types.SimpleNamespace(GetDriveTypeW=Mock(side_effect=OSError("unavailable")))
        with patch.object(self.controller.ctypes, "windll", types.SimpleNamespace(kernel32=kernel32), create=True):
            self.assertIsNone(self.controller.infer_drive_letter(r"D:\video.mp4"))

    def test_mci_eject_failure_is_not_reported_as_success(self):
        send = Mock(side_effect=[0, 123, 0])
        windll = types.SimpleNamespace(winmm=types.SimpleNamespace(mciSendStringW=send))
        with patch.object(self.controller.ctypes, "windll", windll, create=True):
            self.assertFalse(self.controller.open_tray_mci())
        self.assertEqual(send.call_args_list[-1].args[0], "close cd")

    def test_mci_success_still_succeeds(self):
        send = Mock(return_value=0)
        windll = types.SimpleNamespace(winmm=types.SimpleNamespace(mciSendStringW=send))
        with patch.object(self.controller.ctypes, "windll", windll, create=True):
            self.assertTrue(self.controller.open_tray_mci())


if __name__ == "__main__":
    unittest.main()
