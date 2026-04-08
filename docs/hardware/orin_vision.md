# Jetson Orin Edge Vision

The AMiGA project utilizes an NVIDIA Jetson Orin to process high-definition computer vision, primarily targeting zero-latency moisture tracking via infrared (IR) analysis.

## GStreamer & Hardware Acceleration

The core capture script (`ir_moisture_capture.py`) is optimized specifically for the Jetson ecosystem.

- **Pipeline**: Utilizes `GStreamer` via OpenCV's video capture backend.
- **Hardware Decoding**: Standard USB capture is offloaded to the NVIDIA Hardware Decoder Engine (`nvv4l2decoder` and `nvvidconv`), avoiding high CPU overhead and ensuring smooth 1080p @ 30fps streaming.
- **Fallback**: If GStreamer is unavailable, the pipeline falls back gracefully to standard V4L2 CPU-based decoding.

## Heatmap Generation & Capture

- **Concept**: The IR feed captures variations correlating to moisture. The grayscale image is inverted and mapped through `cv2.COLORMAP_JET` to render a virtual heatmap.
- **Interval Storage**: The script captures sequential raw frames at user-configured intervals (default 30 seconds) into timestamped `sessions/` directories. Heatmaps are generated purely in-memory dynamically to drastically conserve raw disk space over multiple weeks of observation.

## Timelapse Processing

The accompanying tool (`timelapse_processor.py`) asynchronously stitches static session images into chronological videos.
- It dynamically generates "Virtual Heatmap" MKVs directly from raw JPEG captures if pre-rendered `_heat.jpg` files are absent, further enhancing flexible data review without requiring duplication of data at capture time.

## Directory
All scripts for this module reside in `orin/scripts/`.
