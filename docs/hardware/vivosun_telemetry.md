# Vivosun Environmental Telemetry

Due to the lack of an officially supported local API, AMiGA retrieves telemetry from Vivosun grow environments through a Raspberry Pi 4 equipped with specialized Optical Character Recognition (OCR) scraping pipelines.

## OCR Pipeline

The scraper (`vivosun_scraper.py`) continually samples the graphical interface of the official Vivosun application to collect environmental metrics.

1.  **Image Sourcing**: Captures the Android application screen either natively via Android Debug Bridge (`adb`) or through `Waydroid` container utilities.
2.  **Processing**: Images are converted to grayscale mappings through `PIL` to enhance contrast.
3.  **Extraction**: `Tesseract` (via `pytesseract`) is utilized with specific Page Segmentation Modes (PSMs) to grab text blocks.
4.  **Parsing**: Complex Regex structures deduce patterns for Target Temperature, Current Temperature, Relative Humidity, VPD (Vapor Pressure Deficit), and AC device states, resolving ambiguous character scans (e.g., swapping `O` for `0`).

## Persistence

Extracted states are validated, timestamped, and immediately appended to a rolling CSV dataset (`vivosun_telemetry.csv`). To protect dataset integrity from errant OCR results, missing readings seamlessly fall back to previous verified states.

## Directory Reference
All scripts for this module reside in `pi4/scripts/`.
