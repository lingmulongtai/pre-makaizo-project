import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class VideoCheckTests(unittest.TestCase):
    def setUp(self):
        self.cv2 = types.ModuleType("cv2")
        self.capture = Mock()
        self.cv2.VideoCapture = Mock(return_value=self.capture)
        self.cv2.imshow = Mock()
        self.cv2.waitKey = Mock(return_value=-1)
        self.cv2.destroyAllWindows = Mock()
        path = Path(__file__).resolve().parents[1] / "test_video_playback.py"
        spec = importlib.util.spec_from_file_location("video_check_test", path)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"cv2": self.cv2}):
            spec.loader.exec_module(self.module)

    def test_missing_file_does_not_open_capture(self):
        with patch.object(self.module.os.path, "isfile", return_value=False):
            self.assertFalse(self.module.test_video_playback("missing.mp4"))
        self.cv2.VideoCapture.assert_not_called()

    def test_open_failure_still_releases_capture(self):
        self.capture.isOpened.return_value = False
        with patch.object(self.module.os.path, "isfile", return_value=True):
            self.assertFalse(self.module.test_video_playback("video.mp4"))
        self.capture.release.assert_called_once()
        self.cv2.destroyAllWindows.assert_called_once()

    def test_video_end_and_quit_release_capture(self):
        self.capture.isOpened.return_value = True
        for frames, key in [([(False, None)], -1), ([(True, object())], ord("q"))]:
            with self.subTest(key=key):
                self.capture.reset_mock()
                self.cv2.destroyAllWindows.reset_mock()
                self.capture.read.side_effect = frames
                self.cv2.waitKey.return_value = key
                with patch.object(self.module.os.path, "isfile", return_value=True):
                    self.assertTrue(self.module.test_video_playback("video.mp4"))
                self.capture.release.assert_called_once()
                self.cv2.destroyAllWindows.assert_called_once()

    def test_display_exception_still_releases_capture(self):
        self.capture.isOpened.return_value = True
        self.capture.read.return_value = (True, object())
        self.cv2.imshow.side_effect = RuntimeError("display failed")
        with patch.object(self.module.os.path, "isfile", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "display failed"):
                self.module.test_video_playback("video.mp4")
        self.capture.release.assert_called_once()
        self.cv2.destroyAllWindows.assert_called_once()


if __name__ == "__main__":
    unittest.main()
