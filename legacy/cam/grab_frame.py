import cv2
import time
from datetime import datetime

DEVICE_INDEX = 0  # adjust if needed

cap = cv2.VideoCapture(DEVICE_INDEX, cv2.CAP_V4L2)

# Try SD NTSC-ish first
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# If MJPEG is listed in v4l2-ctl, this makes life easier:
fourcc = cv2.VideoWriter_fourcc(*"MJPG")
cap.set(cv2.CAP_PROP_FOURCC, fourcc)

if not cap.isOpened():
    raise RuntimeError("Could not open video device")

print("Width:", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
print("Height:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("FPS:", cap.get(cv2.CAP_PROP_FPS))

# Warm up - throw away initial junk frames
for i in range(30):
    ret, frame = cap.read()
    if not ret:
        print("No frame", i)
        continue
    time.sleep(0.05)

# Now grab a real frame
ret, frame = cap.read()
if not ret:
    raise RuntimeError("Still no valid frame")

print("Frame shape:", frame.shape, "mean:", frame.mean())

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
fname = f"swann_debug_{ts}.png"
cv2.imwrite(fname, frame)
print("Saved", fname)

cap.release()
