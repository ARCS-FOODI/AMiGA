import cv2
import os
import time

# --- Configuration ---
DEVICE_NODE = "/dev/video0"
WIDTH = 1920
HEIGHT = 1080
FRAMERATE = 30
OUTPUT_DIR = "calibration_images"

def get_gstreamer_pipeline():
    """
    Constructs the GStreamer pipeline string for Jetson Orin.
    Forces resolution, framerate, and uses hardware acceleration (nvvidconv).
    """
    return (
        f"v4l2src device={DEVICE_NODE} ! "
        f"video/x-raw, width={WIDTH}, height={HEIGHT}, framerate={FRAMERATE}/1, format=YUY2 ! "
        f"nvvidconv ! video/x-raw(memory:NVMM) ! "
        f"nvvidconv ! video/x-raw, format=BGRx ! "
        f"videoconvert ! video/x-raw, format=BGR ! "
        f"appsink drop=1"
    )

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    pipeline = get_gstreamer_pipeline()
    print(f"Opening camera with pipeline:\n{pipeline}")
    
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    print("\n--- Controls ---")
    print("'c' : Capture and save frame")
    print("'q' : Quit")
    
    window_name = "Calibration Capture"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Warning: Failed to capture frame. Retrying...")
            time.sleep(0.1)
            continue

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            filename = os.path.join(OUTPUT_DIR, f"calib_{count:03d}.png")
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")
            count += 1
        elif key == ord('q'):
            print("Exiting...")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
