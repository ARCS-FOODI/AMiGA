import cv2
import time
from datetime import datetime

DEVICE_INDEX = 0  # /dev/video0

# Open using V4L2 backend
cap = cv2.VideoCapture(DEVICE_INDEX, cv2.CAP_V4L2)

if not cap.isOpened():
    raise RuntimeError("Could not open /dev/video0")

# Force YUYV (uncompressed) at 720x480 @ 30fps
fourcc = cv2.VideoWriter_fourcc(*"YUYV")
cap.set(cv2.CAP_PROP_FOURCC, fourcc)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 30)

print("After set():")
print("  Width :", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
print("  Height:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("  FPS   :", cap.get(cv2.CAP_PROP_FPS))

# ---- 5 second warmup ----
start = time.time()
i = 0
while time.time() - start < 5.0:
    ret, frame = cap.read()
    print(f"warmup {i}: ret={ret}")
    i += 1
    if not ret:
        time.sleep(0.05)

# Grab one real frame
ret, frame = cap.read()
print("Final read: ret =", ret)

if not ret or frame is None:
    cap.release()
    raise RuntimeError("read() failed: no valid frame returned")

print("Frame type :", type(frame))
print("Frame shape:", frame.shape)
print("Frame mean :", frame.mean())

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
fname = f"capture_{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}_{ts}.png"
cv2.imwrite(fname, frame)
print("Saved", fname)

cap.release()
