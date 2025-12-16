#!/usr/bin/env python3
import os

# Force Qt to use X11 (xcb) instead of Wayland BEFORE importing cv2
os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2
import numpy as np
import datetime as dt
import csv
from pathlib import Path
import time
import json
import urllib.request
import urllib.error

# ===== PATHS (based on this file location) =====
# This file is at: AMIGA/legacy/cam/ir_tray_logger.py
this_file = Path(__file__).resolve()
base_dir = this_file.parents[2]  # -> AMIGA/

PICS_DIR = base_dir / "data" / "ir_pics"
CSV_DIR = base_dir / "data" / "ir_pics_csv"
STATUS_DIR = base_dir / "data"

PICS_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)
STATUS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = CSV_DIR / "tray_ir_grid_stats.csv"
STATUS_JSON = STATUS_DIR / "plant_status.json"
# ==============================================

# ===== CONFIG =====
SOURCE = 0
INTERVAL_SECONDS = 120.0

ROWS = 4
COLS = 4

# Your crop fractions (top, bottom, left, right)
CROP_TOP_FRAC = 0.215
CROP_BOTTOM_FRAC = 0.74
CROP_LEFT_FRAC = 0.295
CROP_RIGHT_FRAC = 0.615

SHOW_WINDOW = True

# ---- Day vs IR night auto-detect ----
# If saturation is low, treat it as IR/grayscale-like
DAY_SAT_THRESHOLD = 15.0  # tweak if needed

# ---- Green detection (HSV mask) ----
GREEN_HSV_LOWER = np.array([35, 80, 50], dtype=np.uint8)
GREEN_HSV_UPPER = np.array([85, 255, 255], dtype=np.uint8)

# ---- Germination detection ----
# Absolute trigger: detect a small amount of green (mean green fraction across tray)
GREEN_MEAN_TRIGGER = 0.015        # 0..1 (0.005 = 0.5% green). CHANGE THIS.
CONSECUTIVE_DAY_HITS = 1          # require K consecutive day frames to reduce noise

# Optional baseline mode (disabled by default)
USE_BASELINE = False
BASELINE_DAY_FRAMES = 10
GREEN_DELTA_TRIGGER = 0.02

# Optional: save a color crop during day for debugging/QA
SAVE_COLOR_WHEN_DAY = True

# Optional: webhook to notify another service (your pump controller / FastAPI)
GERMINATION_WEBHOOK_URL = ""  # e.g. "http://127.0.0.1:8000/events/germination"
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


def compute_green_fraction_grid(tray_bgr, rows, cols):
    """
    Returns per-cell green fraction (0..1) using HSV masking.
    """
    h, w, _ = tray_bgr.shape
    cell_h = h // rows
    cell_w = w // cols

    hsv = cv2.cvtColor(tray_bgr, cv2.COLOR_BGR2HSV)

    out = []
    for r in range(rows):
        for c in range(cols):
            y_start = r * cell_h
            y_end = (r + 1) * cell_h if r < rows - 1 else h
            x_start = c * cell_w
            x_end = (c + 1) * cell_w if c < cols - 1 else w

            cell_hsv = hsv[y_start:y_end, x_start:x_end]
            mask = cv2.inRange(cell_hsv, GREEN_HSV_LOWER, GREEN_HSV_UPPER)
            green_frac = float(mask.mean() / 255.0)  # 0..1
            out.append((r, c, green_frac))

    return out


def is_probably_day(frame_bgr, sat_thresh=DAY_SAT_THRESHOLD):
    """
    Heuristic: real daytime color tends to have higher saturation.
    """
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mean_sat = float(hsv[:, :, 1].mean())
    return mean_sat >= sat_thresh, mean_sat


def write_status(status_payload: dict):
    tmp = STATUS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(status_payload, indent=2))
    tmp.replace(STATUS_JSON)


def post_webhook(url: str, payload: dict, timeout=3.0):
    if not url:
        return
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            _ = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"[WARN] webhook failed: {e}")


def main():
    cap = cv2.VideoCapture(SOURCE)
    if not cap.isOpened():
        print("Could not open video source")
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("Warming up camera for 2 seconds...")
    warmup_end = time.time() + 2.0
    while time.time() < warmup_end:
        cap.read()
    print("Warmup complete, starting logging.")

    file_exists = OUTPUT_CSV.exists()
    f = OUTPUT_CSV.open("a", newline="")
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow([
            "timestamp",
            "frame",
            "mode",
            "mean_saturation",
            "plant_status",
            "row",
            "col",
            "gray_mean",
            "gray_std",
            "green_frac",
            "image_path_gray",
            "image_path_color",
        ])

    # ---- Plant status state machine ----
    plant_status = "pre-germination"
    write_status({
        "status": plant_status,
        "updated_at": dt.datetime.now().isoformat(),
        "note": "initialized",
    })

    # ---- Germination detector memory ----
    baseline_samples = []  # used only if USE_BASELINE=True
    baseline_green = None
    consecutive_hits = 0
    germination_detected_at = None

    frame_idx = 0

    try:
        while True:
            loop_start = time.time()

            ret, frame = cap.read()
            if not ret:
                print("No frame")
                break

            frame_idx += 1

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # Crop to tray (same crop for color + gray)
            y1 = int(CROP_TOP_FRAC * h)
            y2 = int(CROP_BOTTOM_FRAC * h)
            x1 = int(CROP_LEFT_FRAC * w)
            x2 = int(CROP_RIGHT_FRAC * w)

            tray_gray = gray[y1:y2, x1:x2]
            tray_color = frame[y1:y2, x1:x2]  # BGR

            # Day vs night(IR) detection
            is_day, mean_sat = is_probably_day(tray_color)
            mode = "day" if is_day else "night_ir"

            # Grayscale grid stats (always)
            gray_stats = compute_grid_stats(tray_gray, ROWS, COLS)

            # Green fractions + germination (day only)
            green_grid = None
            green_mean = None
            if is_day:
                green_grid = compute_green_fraction_grid(tray_color, ROWS, COLS)
                green_mean = float(np.mean([g for (_, _, g) in green_grid]))

                # Optional: baseline build
                if USE_BASELINE and baseline_green is None:
                    baseline_samples.append(green_mean)
                    if len(baseline_samples) >= BASELINE_DAY_FRAMES:
                        baseline_green = float(np.mean(baseline_samples))
                        print(f"[BASELINE] baseline_green set to {baseline_green:.4f} "
                              f"from {BASELINE_DAY_FRAMES} day frames")

                # Germination trigger logic (only once)
                if plant_status != "germinated":
                    if USE_BASELINE:
                        # Need baseline before triggering
                        if baseline_green is not None:
                            triggered = green_mean >= (baseline_green + GREEN_DELTA_TRIGGER)
                        else:
                            triggered = False
                    else:
                        # Absolute threshold: detect small amount of green
                        triggered = green_mean >= GREEN_MEAN_TRIGGER

                    if triggered:
                        consecutive_hits += 1
                    else:
                        consecutive_hits = 0

                    if consecutive_hits >= CONSECUTIVE_DAY_HITS:
                        plant_status = "germinated"
                        germination_detected_at = dt.datetime.now().isoformat()

                        payload = {
                            "event": "germination_detected",
                            "status": plant_status,
                            "detected_at": germination_detected_at,
                            "frame": frame_idx,
                            "baseline_green": baseline_green,
                            "green_mean": green_mean,
                            "green_mean_trigger": GREEN_MEAN_TRIGGER,
                            "mean_saturation": mean_sat,
                            "mode": mode,
                        }
                        print(f"[EVENT] Germination detected! {payload}")

                        # Signal to pump controller: write status + optional webhook
                        write_status({
                            "status": plant_status,
                            "updated_at": germination_detected_at,
                            "baseline_green": baseline_green,
                            "green_mean": green_mean,
                            "green_mean_trigger": GREEN_MEAN_TRIGGER,
                            "mean_saturation": mean_sat,
                            "mode": mode,
                            "frame": frame_idx,
                        })
                        post_webhook(GERMINATION_WEBHOOK_URL, payload)

            # Timestamp
            ts = dt.datetime.now()
            ts_iso = ts.isoformat()
            ts_safe = ts.strftime("%Y%m%d_%H%M%S")

            # Save images
            img_name_gray = f"tray_{ts_safe}_f{frame_idx:06d}_gray.png"
            img_path_gray = PICS_DIR / img_name_gray
            cv2.imwrite(str(img_path_gray), tray_gray)

            img_path_color = ""
            if SAVE_COLOR_WHEN_DAY and is_day:
                img_name_color = f"tray_{ts_safe}_f{frame_idx:06d}_color.jpg"
                img_path_color = PICS_DIR / img_name_color
                cv2.imwrite(str(img_path_color), tray_color)

            # Log to CSV per-cell
            green_map = {}
            if green_grid is not None:
                for (r, c, g) in green_grid:
                    green_map[(r, c)] = g

            for (r, c, m, s) in gray_stats:
                g = green_map.get((r, c), "")
                writer.writerow([
                    ts_iso,
                    frame_idx,
                    mode,
                    f"{mean_sat:.3f}",
                    plant_status,
                    r,
                    c,
                    f"{m:.6f}",
                    f"{s:.6f}",
                    (f"{g:.6f}" if g != "" else ""),
                    str(img_path_gray),
                    (str(img_path_color) if img_path_color else ""),
                ])
            f.flush()

            # Console preview
            if is_day and green_mean is not None:
                trig_info = f"thr={GREEN_MEAN_TRIGGER:.4f}" if not USE_BASELINE else f"baseline={baseline_green}"
                print(f"Frame {frame_idx} | mode={mode} sat={mean_sat:.1f} "
                      f"green_mean={green_mean:.4f} {trig_info} hits={consecutive_hits} "
                      f"status={plant_status} | saved {img_name_gray}")
            else:
                print(f"Frame {frame_idx} | mode={mode} sat={mean_sat:.1f} "
                      f"status={plant_status} | saved {img_name_gray}")

            # Optional window
            if SHOW_WINDOW:
                vis = frame.copy()
                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)

                tray_h = (y2 - y1)
                tray_w = (x2 - x1)
                cell_h = tray_h // ROWS
                cell_w = tray_w // COLS

                for r in range(1, ROWS):
                    y = y1 + r * cell_h
                    cv2.line(vis, (x1, y), (x2, y), (0, 255, 0), 1)
                for c in range(1, COLS):
                    x = x1 + c * cell_w
                    cv2.line(vis, (x, y1), (x, y2), (0, 255, 0), 1)

                # Labels: gray mean, and green% if day
                for (r, c, m, s) in gray_stats:
                    yc = int(y1 + (r + 0.5) * cell_h)
                    xc = int(x1 + (c + 0.5) * cell_w)
                    if is_day and green_grid is not None:
                        g = green_map.get((r, c), 0.0)
                        text = f"{m:.0f} | {g*100:.0f}%"
                    else:
                        text = f"{m:.0f}"
                    cv2.putText(
                        vis,
                        text,
                        (xc - 35, yc),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45,
                        (0, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )

                header = f"{mode} | sat={mean_sat:.1f} | status={plant_status}"
                if is_day and green_mean is not None:
                    header += f" | green_mean={green_mean:.3f} thr={GREEN_MEAN_TRIGGER:.3f} hits={consecutive_hits}"
                cv2.putText(
                    vis,
                    header,
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

                cv2.imshow("Tray monitor (day + IR)", vis)
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
        print("Stopped tray logger.")


if __name__ == "__main__":
    main()
