import cv2
import numpy as np
import os
import time
from datetime import datetime

# --- SETUP RECORDING & DIRECTORIES ---
# Ensure we have a base recordings folder
output_root = "recordings"
if not os.path.exists(output_root):
    os.makedirs(output_root)

# Create a unique session folder for this run's snapshots
session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
session_dir = os.path.join(output_root, f"session_{session_time}")
os.makedirs(session_dir)

# 1. Access the USB camera feed
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open video feed.")
    exit()

# Get frame dimensions for VideoWriter
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define the codec and create VideoWriter object
# 'XVID' codec is widely compatible for .mkv containers
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_filename = os.path.join(output_root, f"moisture_{session_time}.mkv")
out = cv2.VideoWriter(video_filename, fourcc, 20.0, (frame_width, frame_height))

print(f"--- MOISTURE TRACKER ACTIVE ---")
print(f"Recording Video: {video_filename}")
print(f"Saving Snapshots to: {session_dir}")
print("Press 'q' to stop recording and exit.")

# --- WINDOW SETUP ---
cv2.namedWindow('Original Camera Feed', cv2.WINDOW_NORMAL)
cv2.namedWindow('AI Moisture Heatmap', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Original Camera Feed', 640, 480)
cv2.resizeWindow('AI Moisture Heatmap', 640, 480)

# Tracker for snapshot timing
last_snapshot_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    # 2. Convert to Grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 3. Process the Moisture Concept:
    # Invert to turn DARK areas (wet) into BRIGHT values (signal)
    inverted_gray = cv2.bitwise_not(gray)
    
    # Apply JET heatmap (Blue=Dry, Red=Wet)
    moisture_map = cv2.applyColorMap(inverted_gray, cv2.COLORMAP_JET)

    # --- RECORDING & SNAPSHOTS ---
    # Write the heatmap frame to the .mkv video file
    out.write(moisture_map)

    # Interval Snapshot Logic (every 1 second)
    current_time = time.time()
    if current_time - last_snapshot_time >= 1.0:
        timestamp = datetime.now().strftime("%H%M%S")
        snapshot_path = os.path.join(session_dir, f"moisture_{timestamp}.jpg")
        cv2.imwrite(snapshot_path, moisture_map)
        last_snapshot_time = current_time

    # 4. Display both feeds
    cv2.imshow('Original Camera Feed', frame)
    cv2.imshow('AI Moisture Heatmap', moisture_map)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
out.release()
cv2.destroyAllWindows()
print(f"--- RECORDING FINISHED ---")
print(f"Total snapshots saved in: {session_dir}")