import cv2
import time
import csv
from datetime import datetime
import numpy as np

DEVICE_INDEX = 0          # /dev/video0
INTERVAL_SEC = 60         # how often to log, in seconds
CSV_PATH = "kale_ir_metrics.csv"

# If your tray doesn't fill the whole frame, you can crop later:
# For now, use the full frame; we'll expose ROI vars to tweak.
ROI_Y1, ROI_Y2 = 0, None  # top:bottom
ROI_X1, ROI_X2 = 0, None  # left:right

def analyze_frame(frame):
    """
    Take a BGR frame (np.array) and return metrics dict:
      - coverage_pct
      - avg_intensity
      - uniformity_index
    """

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Crop region of interest (tray area)
    y1 = ROI_Y1
    y2 = ROI_Y2 if ROI_Y2 is not None else gray.shape[0]
    x1 = ROI_X1
    x2 = ROI_X2 if ROI_X2 is not None else gray.shape[1]
    roi = gray[y1:y2, x1:x2]

    # Smooth noise a bit
    blur = cv2.GaussianBlur(roi, (5, 5), 0)

    # Otsu threshold to separate "plant" vs background
    # Depending on how the plants look in IR, you may want THRESH_BINARY_INV instead.
    _, mask = cv2.threshold(
        blur, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # If you find that background is white and plants are dark,
    # uncomment this to invert:
    # mask = cv2.bitwise_not(mask)

    # Basic coverage: fraction of white pixels in mask
    plant_pixels = np.count_nonzero(mask)
    total_pixels = mask.size
    coverage_pct = 100.0 * plant_pixels / total_pixels if total_pixels > 0 else 0.0

    # Average intensity (for sanity / rough "brightness" tracking)
    avg_intensity = float(roi.mean())

    # Uniformity: split into a 4x4 grid and look at coverage variance
    grid_rows = 4
    grid_cols = 4
    cell_h = mask.shape[0] // grid_rows
    cell_w = mask.shape[1] // grid_cols

    coverages = []
    for gy in range(grid_rows):
        for gx in range(grid_cols):
            y_start = gy * cell_h
            y_end = (gy + 1) * cell_h if gy < grid_rows - 1 else mask.shape[0]
            x_start = gx * cell_w
            x_end = (gx + 1) * cell_w if gx < grid_cols - 1 else mask.shape[1]
            cell = mask[y_start:y_end, x_start:x_end]
            cell_total = cell.size
            if cell_total == 0:
                continue
            cell_plant = np.count_nonzero(cell)
            coverages.append(100.0 * cell_plant / cell_total)

    if coverages:
        uniformity_index = float(np.std(coverages))
    else:
        uniformity_index = 0.0

    return {
        "coverage_pct": coverage_pct,
        "avg_intensity": avg_intensity,
        "uniformity_index": uniformity_index,
    }


def main():
    cap = cv2.VideoCapture(DEVICE_INDEX, cv2.CAP_V4L2)

    if not cap.isOpened():
        raise RuntimeError("Could not open video device /dev/video0")

    # Use YUYV at 720x480 @ 30fps (from your v4l2-ctl list)
    fourcc = cv2.VideoWriter_fourcc(*"YUYV")
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("After set():")
    print("  Width :", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("  Height:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("  FPS   :", cap.get(cv2.CAP_PROP_FPS))

    # 5-second warmup
    start = time.time()
    i = 0
    while time.time() - start < 5.0:
        ret, frame = cap.read()
        print(f"warmup {i}: ret={ret}")
        i += 1
        if not ret:
            time.sleep(0.05)

    # Prepare CSV (add header if file is new/empty)
    try:
        # check if file exists and non-empty
        with open(CSV_PATH, "r") as f:
            has_header = bool(f.readline().strip())
    except FileNotFoundError:
        has_header = False

    csv_file = open(CSV_PATH, "a", newline="")
    writer = csv.writer(csv_file)
    if not has_header:
        writer.writerow(["timestamp", "coverage_pct", "avg_intensity", "uniformity_index"])

    print("Starting logging loop (Ctrl+C to stop)...")
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("WARN: failed to read frame, retrying next interval")
                time.sleep(INTERVAL_SEC)
                continue

            ts = datetime.now().isoformat(timespec="seconds")

            metrics = analyze_frame(frame)
            row = [
                ts,
                metrics["coverage_pct"],
                metrics["avg_intensity"],
                metrics["uniformity_index"],
            ]
            writer.writerow(row)
            csv_file.flush()

            print(
                f"{ts} | coverage={metrics['coverage_pct']:.1f}% "
                f"avg_int={metrics['avg_intensity']:.1f} "
                f"uniformity={metrics['uniformity_index']:.2f}"
            )

            time.sleep(INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\nStopping logging loop...")

    finally:
        csv_file.close()
        cap.release()


if __name__ == "__main__":
    main()
