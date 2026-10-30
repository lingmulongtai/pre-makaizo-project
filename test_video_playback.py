"""Open a video with OpenCV to check playback without the show hardware."""

import argparse
import os

import cv2


def test_video_playback(video_path="test.mp4"):
    print(f"Testing playback for: {video_path}")
    if not os.path.isfile(video_path):
        print(f"Error: File '{video_path}' not found.")
        return False

    cap = cv2.VideoCapture(video_path)
    try:
        if not cap.isOpened():
            print("Error: Could not open video.")
            return False

        print("Video opened successfully. Press 'q' to quit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("End of video or read error.")
                break
            cv2.imshow("Video Test", frame)
            if cv2.waitKey(25) & 0xFF == ord("q"):
                break
        print("Test complete.")
        return True
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", default="test.mp4", help="Video path (default: test.mp4 in the current directory)")
    args = parser.parse_args()
    raise SystemExit(0 if test_video_playback(args.video) else 1)
