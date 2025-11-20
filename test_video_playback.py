import cv2
import os

def test_video_playback(video_path="test.mp4"):
    print(f"Testing playback for: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"Error: File '{video_path}' not found.")
        return

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    print("Video opened successfully. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("End of video or read error.")
            break

        cv2.imshow('Video Test', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Test complete.")

if __name__ == "__main__":
    test_video_playback()
