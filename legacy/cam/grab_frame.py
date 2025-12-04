import cv2
from datetime import datetime

# change 0 -> 1,2,... if it's not the first /dev/video device
DEVICE_INDEX = 0

cap = cv2.VideoCapture(DEVICE_INDEX, cv2.CAP_V4L2)

# Ask for 1080p @ 30fps (the driver may clamp this)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    raise RuntimeError("Could not open video device")

ret, frame = cap.read()
if not ret:
    raise RuntimeError("Could not read frame from camera")

print("Frame shape:", frame.shape)  # (height, width, channels)

# Save a debug PNG so you can confirm it's working
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
fname = f"frame_{ts}.png"
cv2.imwrite(fname, frame)
print("Saved", fname)

cap.release()
