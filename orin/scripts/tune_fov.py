import cv2
import numpy as np
import time

# --- Configuration ---
DEVICE_NODE = "/dev/video0" # Change to /dev/video2 for the other camera if you want to test it
WIDTH = 1920
HEIGHT = 1080
FRAMERATE = 30
CALIB_FILE = "calibration_data.yaml"

# Global vars
mtx = None
dist = None
mapx = None
mapy = None

def get_gstreamer_pipeline():
    return (
        f"v4l2src device={DEVICE_NODE} ! "
        f"video/x-raw, width={WIDTH}, height={HEIGHT}, framerate={FRAMERATE}/1, format=YUY2 ! "
        f"nvvidconv ! video/x-raw(memory:NVMM) ! "
        f"nvvidconv ! video/x-raw, format=BGRx ! "
        f"videoconvert ! video/x-raw, format=BGR ! "
        f"appsink drop=1"
    )

def dummy_callback(val):
    """
    OpenCV trackbars require a callback function, but we will 
    read the value directly in the main loop instead for safety.
    """
    pass

def main():
    global mtx, dist, mapx, mapy
    
    # 1. Load Calibration Data
    try:
        cv_file = cv2.FileStorage(CALIB_FILE, cv2.FILE_STORAGE_READ)
        if not cv_file.isOpened():
            raise Exception("File not found or unreadable.")
        mtx = cv_file.getNode("camera_matrix").mat()
        dist = cv_file.getNode("dist_coeff").mat()
        cv_file.release()
    except Exception as e:
        print(f"Error loading calibration data: {e}")
        return

    # 2. Window Setup
    window_name = "FOV Tuner"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    # 3. Pre-calculate the Maps ONCE with Alpha = 1.0 (Maximum FOV, retains all black bars)
    alpha = 1.0
    h, w = HEIGHT, WIDTH
    newcameramtx, roi_val = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), alpha, (w, h))
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w, h), 5)
    
    # Create the Trackbar Slider
    # Starts at 0 (No Zoom = Shows all black bars)
    cv2.createTrackbar("Zoom (0-100)", window_name, 0, 100, dummy_callback)
    
    # 4. Open Camera Feed
    cap = cv2.VideoCapture(get_gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    print("Starting Manual FOV Zoom Tuner... Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1) 
            continue

        # 5. Apply Undistortion (This frame will have black bars by default)
        dst = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)

        # 6. Read Trackbar Value
        try:
            zoom_val = cv2.getTrackbarPos("Zoom (0-100)", window_name)
        except cv2.error:
            # Handle sudden window closures gracefully
            break

        # 7. Apply Manual Zoom / Crop
        if zoom_val > 0:
            # Maximum we are allowed to crop is 35% of the frame from each side
            max_crop_w = int(WIDTH * 0.35)
            max_crop_h = int(HEIGHT * 0.35)
            
            # Calculate exactly how many pixels to crop away based on 0-100 slider
            crop_w = int(max_crop_w * (zoom_val / 100.0))
            crop_h = int(max_crop_h * (zoom_val / 100.0))
            
            # Perform the mathematical crop inwards
            cropped = dst[crop_h : HEIGHT - crop_h, crop_w : WIDTH - crop_w]
            
            # Resize it back to 1080p to create the "Zoom" effect
            seamless = cv2.resize(cropped, (WIDTH, HEIGHT))
        else:
            # Zoom = 0: Just show the raw undistorted frame with all black bars visible
            seamless = dst

        # 8. Add a text overlay so you know the exact zoom percentage
        cv2.putText(seamless, f"Current Zoom Power: {zoom_val}%", (30, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        cv2.imshow(window_name, seamless)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n==============================")
            print("YOUR OPTIMIZED SETTINGS:")
            print(f"Ideal Manual Crop Ratio: {zoom_val}%")
            print("==============================\n")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
