import cv2
import numpy as np
import time

# --- Configuration ---
DEVICE_NODE_1 = "/dev/video0"
DEVICE_NODE_2 = "/dev/video2" # Often /dev/video1 is used for metadata, video2 is the 2nd camera
WIDTH = 1920
HEIGHT = 1080
FRAMERATE = 30
CALIB_FILE = "calibration_data.yaml"

def get_gstreamer_pipeline(device_node):
    """
    Constructs the GStreamer pipeline string for Jetson Orin.
    Forces resolution, framerate, and uses hardware acceleration (nvvidconv).
    """
    return (
        f"v4l2src device={device_node} ! "
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
    print("Computing optimal camera matrix and undistortion maps...")
    
    h, w = HEIGHT, WIDTH
    
    # Adjust scaling factor alpha (0 = crop blank areas, 1 = retain all pixels)
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
    
    # Generate maps for remap() - Used by BOTH cameras since they are identical models
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w, h), 5)
    
    # 3. Open Camera Feeds
    print(f"Opening Feed 1: {DEVICE_NODE_1}")
    cap1 = cv2.VideoCapture(get_gstreamer_pipeline(DEVICE_NODE_1), cv2.CAP_GSTREAMER)
    
    print(f"Opening Feed 2: {DEVICE_NODE_2}")
    cap2 = cv2.VideoCapture(get_gstreamer_pipeline(DEVICE_NODE_2), cv2.CAP_GSTREAMER)

    if not cap1.isOpened() or not cap2.isOpened():
        print(f"Error: Could not open one or both video devices. Check device nodes.")
        # Attempt graceful exit of whatever did open
        if cap1.isOpened(): cap1.release()
        if cap2.isOpened(): cap2.release()
        return

    print("Starting dual live feed... Press 'q' to quit.")
    
    window_name = "Dual Live Undistort (Left: Orig | Right: Undistorted)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    while True:
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        
        if not ret1 or not ret2:
            print("Warning: Failed to capture from one or both cameras. Retrying...")
            time.sleep(0.1) 
            continue

        # 4. Apply Real-Time Undistortion Map to BOTH feeds
        dst1 = cv2.remap(frame1, mapx, mapy, cv2.INTER_LINEAR)
        dst2 = cv2.remap(frame2, mapx, mapy, cv2.INTER_LINEAR)

        # 5. Composite Quadrant View (Scale to 960x540 for a beautiful 1080p 4-square)
        scale_size = (960, 540)
        
        # Top Row: Camera 1
        s_orig1 = cv2.resize(frame1, scale_size)
        s_dst1 = cv2.resize(dst1, scale_size)
        
        # Bottom Row: Camera 2
        s_orig2 = cv2.resize(frame2, scale_size)
        s_dst2 = cv2.resize(dst2, scale_size)
        
        # Add labels for visual clarity
        cv2.putText(s_orig1, "Cam 1 (Original)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(s_dst1, "Cam 1 (Undistorted)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.putText(s_orig2, "Cam 2 (Original)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(s_dst2, "Cam 2 (Undistorted)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        top_row = np.hstack((s_orig1, s_dst1))
        bottom_row = np.hstack((s_orig2, s_dst2))
        
        # Combine all into a 1920x1080 canvas
        combined = np.vstack((top_row, bottom_row))
        
        cv2.imshow(window_name, combined)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap1.release()
    cap2.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
