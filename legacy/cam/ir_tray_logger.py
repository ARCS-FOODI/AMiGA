#!/usr/bin/env python3
"""
IR tray logger (hard-coded config)

- Opens a video source (USB capture card, DVR, etc.)
- Every N seconds:
    * grabs one frame
    * converts to grayscale
    * crops to the tray area
    * divides it into a grid (ROWS x COLS)
    * computes mean + std intensity per cell
    * appends results to a CSV file

Just edit the CONFIG section below to match your setup.
"""

import csv
import datetime as dt
import signal
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# =========================
# CONFIG – EDIT THESE
# =========================

# Video source:
#   - For local capture card: 0 or 1, etc.
#   - For RTSP stream: "rtsp://user:pass@ip:554/your_stream"
SOURCE = 0  # or "rtsp://..."

# How often to log (seconds between captures)
INTERVAL_SECONDS = 60.0  # e.g. 60 = once per minute

# Grid over the tray
ROWS = 4
COLS = 4

# Output CSV path
OUTPUT_CSV = "tray_ir_grid_stats.csv"

# Crop as FRACTIONS of the full frame (0.0–1.0)
# Tune these by using PREVIEW_MODE = True first
CROP_TOP_FRAC = 0.15
CROP_BOTTOM_FRAC = 0.90
CROP_LEFT_FRAC = 0.20
CROP_RIGHT_FRAC = 0.80

# Set to True to show live preview with crop+grid (no logging)
# Set to False to actually log to CSV
PREVIEW_MODE = True  # change to False when ready to log

# =========================
# END CONFIG
# =========================

STOP_REQUESTED = False


def handle_sigint(signum, frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True
    print("\n[INFO] Stop requested, finishing current iteration...")


signal.signal(signal.SIGINT, handle_sigint)


def compute_grid_stats(tray_gray: np.ndarray, rows: int, cols: int):
    """Compute mean and std intensity for each cell in a rows x cols grid."""
    h, w = tray_gray.shape
    cell_h = h // rows
    cell_w = w // cols

    results = []
    for r in range(rows):
        for c in range(cols):
            y_start = r * cell_h
            y_end = (r + 1) * cell_h if r < rows - 1 else h
            x_start = c * cell_w
            x_end = (c + 1) * cell_w if c < cols - 1 else w

            cell = tray_gray[y_start:y_end, x_start:x_end]
            mean_intensity = float(cell.mean())
            std_intensity = float(cell.std())

            results.append(
                {
                    "row": r,
                    "col": c,
                    "mean_intensity": mean_intensity,
                    "std_intensity": std_intensity,
                }
            )
    return results


def open_capture(source):
    if isinstance(source, int):
        cap = cv2.VideoCapture(source)
    else:
        # if it's a string like "0", try to cast to int
        if isinstance(source, str) and source.isdigit():
            cap = cv2.VideoCapture(int(source))
        else:
            cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {source}")
        sys.exit(1)
    return cap


def main():
    cap = open_capture(SOURCE)

    out_path = Path(OUTPUT_CSV)
    csv_file = None
    writer = None

    if not PREVIEW_MODE:
        file_exists = out_path.exists()
        csv_file = out_path.open("a", newline="")
        writer = csv.writer(csv_file)
        if not file_exists:
            writer.writerow(
                [
                    "timestamp_iso",
                    "frame_index",
                    "row",
                    "col",
                    "mean_intensity",
                    "std_intensity",
                ]
            )

    frame_index = 0
    print(
        "[INFO] Starting "
        + ("PREVIEW mode." if PREVIEW_MODE else "LOGGING mode.")
        + " Press Ctrl+C to stop."
    )

    try:
        while not STOP_REQUESTED:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Could not read frame from camera.")
                time.sleep(1.0)
                continue

            frame_index += 1

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # Compute crop region in pixels
            y1 = int(CROP_TOP_FRAC * h)
            y2 = int(CROP_BOTTOM_FRAC * h)
            x1 = int(CROP_LEFT_FRAC * w)
            x2 = int(CROP_RIGHT_FRAC * w)

            tray = gray[y1:y2, x1:x2]

            if PREVIEW_MODE:
                # Show crop and grid overlay
                vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)

                tray_h, tray_w = tray.shape
                cell_h = tray_h // ROWS
                cell_w = tray_w // COLS

                # Draw grid
                for r in range(1, ROWS):
                    y = y1 + r * cell_h
                    cv2.line(vis, (x1, y), (x2, y), (0, 255, 0), 1)
                for c in range(1, COLS):
                    x = x1 + c * cell_w
                    cv2.line(vis, (x, y1), (x, y2), (0, 255, 0), 1)

                cv2.imshow("IR Tray Preview", vis)
                key = cv2.waitKey(30) & 0xFF
                if key == 27:  # Esc
                    break

                continue  # loop again, no logging

            # Logging mode
            stats = compute_grid_stats(tray, ROWS, COLS)
            timestamp_iso = dt.datetime.now().isoformat()

            for cell in stats:
                writer.writerow(
                    [
                        timestamp_iso,
                        frame_index,
                        cell["row"],
                        cell["col"],
                        f"{cell['mean_intensity']:.6f}",
                        f"{cell['std_intensity']:.6f}",
                    ]
                )

            csv_file.flush()
            print(
                f"[INFO] Logged frame {frame_index} at {timestamp_iso} "
                f"(first cell mean: {stats[0]['mean_intensity']:.2f})"
            )

            time.sleep(INTERVAL_SECONDS)

    finally:
        cap.release()
        cv2.destroyAllWindows()
        if csv_file is not None:
            csv_file.close()
        print("[INFO] Capture stopped, resources released.")


if __name__ == "__main__":
    main()
