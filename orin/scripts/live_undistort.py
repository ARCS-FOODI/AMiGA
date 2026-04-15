import cv2
import numpy as np
import time

# --- Configuration ---
DEVICE_NODE = "/dev/video0"
WIDTH = 1920
HEIGHT = 1080
FRAMERATE = 30
CALIB_FILE = "calibration_data.yaml"

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
    # 1. Load Calibration Data
    try:
        cv_file = cv2.FileStorage(CALIB_FILE, cv2.FILE_STORAGE_READ)
        if not cv_file.isOpened():
            raise Exception("File not found or unreadable.")
            
        mtx = cv_file.getNode("camera_matrix").mat()
        dist = cv_file.getNode("dist_coeff").mat()
        cv_file.release()
        
        if mtx is None or dist is None:
             raise Exception("Missing matrix or distortion data in yaml.")
             
        print("Successfully loaded calibration data.")
    except Exception as e:
        print(f"Error loading calibration data: {e}")
        print("Please run calibrate.py first to generate the configuration.")
        return

    # 2. Pre-calculate the Rectification Maps for Performance
    # We do this OUTSIDE the loop.
    print("Computing optimal camera matrix and undistortion maps...")
    
    # Using typical frame shape (Height, Width)
    h, w = HEIGHT, WIDTH
    
    # Adjust scaling factor alpha (0 = crop everything that's blank, 1 = retain all pixels)
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
    
    # Generate maps for remap()
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w, h), 5)
    
    # 3. Open Camera Feed
    pipeline = get_gstreamer_pipeline()
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    print("Starting live feed... Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Warning: Failed to capture frame. Retrying...")
            # Robust error handling for USB disconnects / dropped frames
            time.sleep(0.1) 
            continue

        # 4. Apply Real-Time Undistortion Map
        # Using remap is significantly faster than cv2.undistort inside the loop
        dst = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)

        # Optional: Crop the image based on ROI if alpha > 0 and black borders appear
        # x, y, w_roi, h_roi = roi
        # dst = dst[y:y+h_roi, x:x+w_roi]

        # Stack Original and Undistorted for preview purposes
        # Note: If running on a headless edge device in production, remove imshow
        scaled_orig = cv2.resize(frame, (960, 540))
        scaled_dst = cv2.resize(dst, (960, 540))
        combined = np.hstack((scaled_orig, scaled_dst))
        
        cv2.imshow("Live Undistort (Left: Original | Right: Undistorted)", combined)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
