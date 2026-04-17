import cv2
import numpy as np
import os
import time
import threading
from datetime import datetime
import sys

# --- Configuration ---
DEVICE_NODE_0 = "/dev/video0"
DEVICE_NODE_1 = "/dev/video2"  # or /dev/video1 if video2 is missing
WIDTH = 1920
HEIGHT = 1080
FRAMERATE = 30
CAPTURE_INTERVAL = 30.0
CALIB_FILE = "calibration_data.yaml"
OUTPUT_ROOT = "recordings"

class CameraStream:
    """
    Optimized Camera Handler for NVIDIA Jetson Orin.
    Uses GStreamer and hardware-accelerated decoding.
    """
    def __init__(self, device_node, width=1920, height=1080, fps=30):
        self.device_node = device_node
        self.width = width
        self.height = height
        self.fps = fps
        self.frame = None
        self.stopped = False
        
        # JETSON ORIN OPTIMIZED PIPELINE
        self.pipeline = (
            f"v4l2src device={self.device_node} ! "
            f"image/jpeg, width={self.width}, height={self.height}, framerate={self.fps}/1 ! "
            "nvv4l2decoder mjpeg=1 ! "
            "nvvidconv ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! "
            "appsink drop=1"
        )
        
        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        
        if not self.cap.isOpened():
            print(f"[WARNING] GStreamer failed for {device_node}. Falling back to V4L2...")
            self.cap = cv2.VideoCapture(self.device_node)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

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
        if self.cap.isOpened():
            self.cap.release()

def load_calibration(file_path):
    """Loads camera matrix and distortion coefficients."""
    try:
        cv_file = cv2.FileStorage(file_path, cv2.FILE_STORAGE_READ)
        if not cv_file.isOpened():
            return None, None
        mtx = cv_file.getNode("camera_matrix").mat()
        dist = cv_file.getNode("dist_coeff").mat()
        cv_file.release()
        return mtx, dist
    except Exception as e:
        print(f"[ERROR] Loading calibration: {e}")
        return None, None

def main():
    print("\n" + "="*50)
    print("   AMiGA GROW TRACKER: DUAL CAMERA SNAPSHOTS")
    print("="*50)

    # 1. Setup Directories
    session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(OUTPUT_ROOT, f"session_{session_time}")
    cam0_dir = os.path.join(session_dir, "cam0")
    cam1_dir = os.path.join(session_dir, "cam1")
    
    os.makedirs(cam0_dir, exist_ok=True)
    os.makedirs(cam1_dir, exist_ok=True)

    # 2. Load Calibration & Precompute Maps
    mtx, dist = load_calibration(CALIB_FILE)
    map_x, map_y = None, None
    if mtx is not None and dist is not None:
        print("[INFO] Calibration data loaded. Undistortion active.")
        newcameramtx, _ = cv2.getOptimalNewCameraMatrix(mtx, dist, (WIDTH, HEIGHT), 1, (WIDTH, HEIGHT))
        map_x, map_y = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (WIDTH, HEIGHT), 5)
    else:
        print("[WARNING] Calibration data NOT found. Saving RAW images.")

    # 3. Start Camera Streams
    print(f"[INFO] Initializing {DEVICE_NODE_0}...")
    cam0 = CameraStream(DEVICE_NODE_0).start()
    print(f"[INFO] Initializing {DEVICE_NODE_1}...")
    cam1 = CameraStream(DEVICE_NODE_1).start()

    # Wait for first frames
    start_wait = time.time()
    while (cam0.read() is None or cam1.read() is None) and (time.time() - start_wait < 5):
        time.sleep(0.1)
    
    if cam0.read() is None:
        print("[ERROR] Cam 0 failed to initialize.")
    if cam1.read() is None:
        print("[ERROR] Cam 1 failed to initialize.")
    
    print(f"\n[START] Tracking session: {session_time}")
    print(f"[INFO] Interval: {CAPTURE_INTERVAL}s")
    print(f"[INFO] Save path: {session_dir}")
    print("Press Ctrl+C to stop.\n")

    start_time = time.time()
    last_capture_time = 0
    
    try:
        while True:
            current_time = time.time()
            elapsed = int(current_time - start_time)
            hhmmss = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            
            # Update terminal with elapsed time (overwrites line)
            sys.stdout.write(f"\rElapsed Time: {hhmmss} | Monitoring cameras...")
            sys.stdout.flush()

            # Snapshot Logic
            if current_time - last_capture_time >= CAPTURE_INTERVAL:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                f0 = cam0.read()
                f1 = cam1.read()
                
                # Apply Undistortion if maps exist
                if map_x is not None and map_y is not None:
                    if f0 is not None: f0 = cv2.remap(f0, map_x, map_y, cv2.INTER_LINEAR)
                    if f1 is not None: f1 = cv2.remap(f1, map_x, map_y, cv2.INTER_LINEAR)
                
                # Save Images
                if f0 is not None:
                    path0 = os.path.join(cam0_dir, f"snap_{timestamp}.jpg")
                    cv2.imwrite(path0, f0)
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Cam 0: Saved {os.path.basename(path0)}")
                
                if f1 is not None:
                    path1 = os.path.join(cam1_dir, f"snap_{timestamp}.jpg")
                    cv2.imwrite(path1, f1)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Cam 1: Saved {os.path.basename(path1)}")
                
                last_capture_time = current_time

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n[STOP] Tracking interrupted by user.")
    finally:
        cam0.stop()
        cam1.stop()
        print(f"\nSession finished. Data stored in: {session_dir}")

if __name__ == "__main__":
    main()
