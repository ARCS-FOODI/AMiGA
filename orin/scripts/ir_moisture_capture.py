import cv2
import numpy as np
import os
import time
import threading
from datetime import datetime

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
        # 1. v4l2src: Standard USB camera source
        # 2. image/jpeg: MJPEG format (best for 1080p30 over USB)
        # 3. nvv4l2decoder: NVIDIA Hardware Decoder Engine
        # 4. nvvidconv: Hardware-accelerated color conversion
        # 5. appsink: Hand-off frames to OpenCV
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
        # Daemon=True ensures thread closes when main script exits
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
        time.sleep(0.5) # Give thread a moment to loop and see 'stopped'
        self.cap.release()

# --- SETUP DIRECTORIES ---
output_root = "recordings"
if not os.path.exists(output_root):
    os.makedirs(output_root)

session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
session_dir = os.path.join(output_root, f"session_{session_time}")
os.makedirs(session_dir)

# --- CONFIGURATION ---
# 30 seconds allows for 14 days of data to fit within ~20GB (at 500KB/pic)
CAPTURE_INTERVAL = 30.0 

# Initialize Optimized Stream
cam = CameraStream().start()


# Wait for the first frame to populate
while cam.read() is None:
    print("Waiting for camera initialization...")
    time.sleep(0.5)

print(f"\n--- IR MOISTURE CAPTURE ACTIVE ---")
print(f"Session: {session_dir}")
print(f"Interval: {CAPTURE_INTERVAL} seconds")
print(f"Target: 1080p @ 30fps")
print("Press 'q' in the window to stop tracking.\n")

# --- WINDOW SETUP ---
cv2.namedWindow('Original Camera Feed', cv2.WINDOW_NORMAL)
cv2.namedWindow('AI Moisture Heatmap', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Original Camera Feed', 640, 480)
cv2.resizeWindow('AI Moisture Heatmap', 640, 480)

# Trigger the first snapshot immediately on start
last_snapshot_time = 0

try:
    while True:
        # Pull the latest frame from the background thread
        frame = cam.read()
        if frame is None:
            continue

        # 2. Convert to Grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 3. Process the Moisture Concept:
        # Invert -> Jet Heatmap
        inverted_gray = cv2.bitwise_not(gray)
        moisture_map = cv2.applyColorMap(inverted_gray, cv2.COLORMAP_JET)

        # --- SNAPSHOT LOGIC ---
        current_time = time.time()
        if current_time - last_snapshot_time >= CAPTURE_INTERVAL:
            timestamp = datetime.now().strftime("%H%M%S")
            
            # Save Raw Only (Heatmap is generated later to save space)
            raw_path = os.path.join(session_dir, f"moisture_{timestamp}_raw.jpg")
            cv2.imwrite(raw_path, frame)
            
            last_snapshot_time = current_time

        # 4. Display both feeds
        cv2.imshow('Original Camera Feed', frame)
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