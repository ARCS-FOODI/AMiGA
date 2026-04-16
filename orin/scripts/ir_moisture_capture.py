import cv2
import numpy as np
import os
import time
import threading
from datetime import datetime

# --- NEW: CALIBRATION CONSTANTS ---
CALIB_FILE = "calibration_data.yaml"
TARGET_ZOOM = 50.0 # Your preferred 50% seamless zoom crop!

class CameraStream:
    """
    Optimized Camera Handler for NVIDIA Jetson Orin.
    Uses GStreamer and hardware-accelerated decoding (NVDEC) via nvv4l2decoder.
    """
    def __init__(self, device_id=0, width=1920, height=1080, fps=30):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.frame = None
        self.stopped = False
        
        # --- JETSON ORIN OPTIMIZED PIPELINE ---
        self.pipeline = (
            f"v4l2src device=/dev/video{self.device_id} ! "
            f"image/jpeg, width={self.width}, height={self.height}, framerate={self.fps}/1 ! "
            "nvv4l2decoder mjpeg=1 ! "
            "nvvidconv ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! "
            "appsink drop=1"
        )
        
        # Try GStreamer pipeline first
        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        
        if not self.cap.isOpened():
            print(f"[WARNING] GStreamer failed. Falling back to V4L2 (CPU Decoding).")
            self.cap = cv2.VideoCapture(self.device_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        else:
            print(f"[GSTREAMER SUCCESS] HW-Accelerated Pipeline Active.")

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self.stopped = True
                continue
            self.frame = frame

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        time.sleep(0.5) 
        self.cap.release()

# --- PREPARE CALIBRATION MAPS ---
print("Loading calibration data...")
try:
    cv_file = cv2.FileStorage(CALIB_FILE, cv2.FILE_STORAGE_READ)
    if not cv_file.isOpened():
        raise Exception("File not found.")
    mtx = cv_file.getNode("camera_matrix").mat()
    dist = cv_file.getNode("dist_coeff").mat()
    cv_file.release()
    
    if mtx is None or dist is None:
         raise Exception("Missing matrix parameters.")
         
    # Generate maps using Base FOV
    w, h = 1920, 1080
    newcameramtx, _ = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1.0, (w, h))
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w, h), 5)
    
    # Pre-calculate 50% Zoom Crop Constraints
    max_crop_w = int(w * 0.35)
    max_crop_h = int(h * 0.35)
    crop_w = int(max_crop_w * (TARGET_ZOOM / 100.0))
    crop_h = int(max_crop_h * (TARGET_ZOOM / 100.0))
    print(f"[SUCCESS] Calibration & 50% Zoom Map Generated.")

except Exception as e:
    print(f"\n[ERROR] Could not load '{CALIB_FILE}'. Make sure you calibrated!")
    print(e)
    # Give dummy data so script doesn't crash but skips remap
    mtx = None

# --- SETUP DIRECTORIES ---
output_root = "recordings"
if not os.path.exists(output_root):
    os.makedirs(output_root)

session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
session_dir = os.path.join(output_root, f"session_{session_time}")
os.makedirs(session_dir)

# --- CONFIGURATION ---
CAPTURE_INTERVAL = 30.0 

# Initialize Optimized Stream (Cam 1 -> Core /dev/video0)
cam = CameraStream(device_id=0).start()

while cam.read() is None:
    print("Waiting for camera initialization...")
    time.sleep(0.5)

print(f"\n--- IR MOISTURE CAPTURE ACTIVE (WITH UNDISTORTION) ---")
print(f"Session: {session_dir}")
print(f"Interval: {CAPTURE_INTERVAL} seconds")
print(f"Target: 1080p @ 30fps")
print("Press 'q' in the window to stop tracking.\n")

# --- WINDOW SETUP ---
cv2.namedWindow('Original Camera Feed', cv2.WINDOW_NORMAL)
cv2.namedWindow('AI Moisture Heatmap', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Original Camera Feed', 640, 480) # Resize just initial bounds, can still maximize
cv2.resizeWindow('AI Moisture Heatmap', 640, 480)

last_snapshot_time = 0

try:
    while True:
        frame = cam.read()
        if frame is None:
            continue

        # --- NEW: APPLY UNDISTORTION & ZOOM ---
        if mtx is not None:
            # 1. Run the hardware remap correction
            dst = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)
            
            # 2. Slice off the black edges dynamically using our 50% zoom crop
            cropped_frame = dst[crop_h : h - crop_h, crop_w : w - crop_w]
            
            # 3. Scale back perfectly to 1080p
            seamless_frame = cv2.resize(cropped_frame, (w, h))
        else:
            seamless_frame = frame

        # Convert to Grayscale using the NEW seamless frame
        gray = cv2.cvtColor(seamless_frame, cv2.COLOR_BGR2GRAY)

        # Process Moisture Heatmap
        inverted_gray = cv2.bitwise_not(gray)
        moisture_map = cv2.applyColorMap(inverted_gray, cv2.COLORMAP_JET)

        # --- SNAPSHOT LOGIC ---
        current_time = time.time()
        if current_time - last_snapshot_time >= CAPTURE_INTERVAL:
            timestamp = datetime.now().strftime("%H%M%S")
            # Save Raw Only (using the cleanly undistorted feed!)
            raw_path = os.path.join(session_dir, f"moisture_{timestamp}_raw.jpg")
            cv2.imwrite(raw_path, seamless_frame)
            last_snapshot_time = current_time

        # Display Feeds (Both are now clean, edge-to-edge undistorted representations)
        cv2.imshow('Original Camera Feed', seamless_frame)
        cv2.imshow('AI Moisture Heatmap', moisture_map)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\nTracking interrupted by user.")

# Clean up
cam.stop()
cv2.destroyAllWindows()

print(f"\n--- SESSION FINISHED ---")
print(f"Files saved in: {session_dir}")
print("Run 'python3 timelapse_processor.py' to generate videos.")