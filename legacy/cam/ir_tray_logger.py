#!/usr/bin/env python3
import os
import cv2
import numpy as np
import datetime as dt
import csv
from pathlib import Path
import time

os.environ["QT_QPA_PLATFORM"] = "xcb"

# ===== CONFIG =====
SOURCE = 0                 # camera index or RTSP URL
INTERVAL_SECONDS = 10.0    # seconds between logs

ROWS = 4
COLS = 4
OUTPUT_CSV = "tray_ir_grid_stats.csv"

# Your crop fractions (top, bottom, left, right)
CROP_TOP_FRAC = 0.187
CROP_BOTTOM_FRAC = 0.74
CROP_LEFT_FRAC = 0.295
CROP_RIGHT_FRAC = 0.615

# Show window with grid overlay + means for debugging
# Set to False for long-term runs to save CPU
SHOW_WINDOW = True
# ==================


def compute_grid_stats(tray_gray, rows, cols):
    h, w = tray_gray.shape
    cell_h = h // rows
    cell_w = w // cols
    stats = []

    for r in range(rows):
        for c in range(cols):
            y_start = r * cell_h
            y_end = (r + 1) * cell_h if r < rows - 1 else h
            x_start = c * cell_w
            x_end = (c + 1) * cell_w if c < cols - 1 else w

            cell = tray_gray[y_start:y_end, x_start:x_end]
            mean_intensity = float(cell.mean())
            std_intensity = float(cell.std())
            stats.append((r, c, mean_intensity, std_intensity))

    return stats


def main():
    cap = cv2.VideoCapture(SOURCE)
    if not cap.isOpened():
        print("Could not open video source")
        return

    # Optional: keep buffer small so we always get "latest" frame
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # --- Warm up camera for 2 seconds ---
    print("Warming up camera for 2 seconds...")
    warmup_end = time.time() + 2.0
    while time.time() < warmup_end:
        cap.read()
    print("Warmup complete, starting logging.")

    out_path = Path(OUTPUT_CSV)
    file_exists = out_path.exists()
    f = out_path.open("a", newline="")
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["timestamp", "frame", "row", "col", "mean", "std"])

    frame_idx = 0

    try:
        while True:
            loop_start = time.time()

            ret, frame = cap.read()
            if not ret:
                print("No frame")
                break

            frame_idx += 1

            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # Crop to tray
            y1 = int(CROP_TOP_FRAC * h)
            y2 = int(CROP_BOTTOM_FRAC * h)
            x1 = int(CROP_LEFT_FRAC * w)
            x2 = int(CROP_RIGHT_FRAC * w)
            tray = gray[y1:y2, x1:x2]

            stats = compute_grid_stats(tray, ROWS, COLS)
            ts = dt.datetime.now().isoformat()

            # Log to CSV
            for (r, c, m, s) in stats:
                writer.writerow([ts, frame_idx, r, c, f"{m:.6f}", f"{s:.6f}"])
            f.flush()

            print(
                f"Frame {frame_idx} | first cell mean/std: "
                f"{stats[0][2]:.2f}/{stats[0][3]:.2f}"
            )

            # Optional on-screen preview
            if SHOW_WINDOW:
                vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)

                tray_h, tray_w = tray.shape
                cell_h = tray_h // ROWS
                cell_w = tray_w // COLS

                # grid lines
                for r in range(1, ROWS):
                    y = y1 + r * cell_h
                    cv2.line(vis, (x1, y), (x2, y), (0, 255, 0), 1)
                for c in range(1, COLS):
                    x = x1 + c * cell_w
                    cv2.line(vis, (x, y1), (x, y2), (0, 255, 0), 1)

                # mean labels
                for (r, c, m, s) in stats:
                    yc = int(y1 + (r + 0.5) * cell_h)
                    xc = int(x1 + (c + 0.5) * cell_w)
                    text = f"{m:.0f}"
                    cv2.putText(
                        vis,
                        text,
                        (xc - 20, yc),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )

                cv2.imshow("IR tray with means", vis)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break

            # Keep loop period ~ INTERVAL_SECONDS
            elapsed = time.time() - loop_start
            sleep_for = INTERVAL_SECONDS - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    finally:
        cap.release()
        f.close()
        if SHOW_WINDOW:
            cv2.destroyAllWindows()
        print("Stopped IR tray logger.")


if __name__ == "__main__":
    main()
