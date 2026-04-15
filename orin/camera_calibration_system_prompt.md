# System Context & Prompt: Jetson Orin Edge Camera Calibration Pipeline

## 1. System Architecture & Hardware Context
**Primary Compute:** NVIDIA Jetson Orin (ARM64 architecture, optimized for edge AI).
**Sensor Pipeline:** Annke Analog Security Camera -> Analog-to-Digital Converter (ADC) -> Video Encoder -> **USB Capture Interface**.
**Software Stack:** Python 3.x, OpenCV (cv2), Video4Linux2 (v4l2), GStreamer (optional but recommended for pipeline optimization).

*Directive for AI Models:* When generating code or troubleshooting for this environment, prioritize hardware acceleration and minimal CPU overhead. The Jetson Orin's CPU should be spared for logic, while hardware blocks (via GStreamer/nvvidconv) should handle video formatting where possible.

---

## 2. Mission Objective
Implement a highly performant, real-time camera calibration and undistortion pipeline. Since the camera is analog and passes through an ADC/Encoder to a USB interface, latency and signal degradation must be minimized. The pipeline must calculate the intrinsic camera matrix and distortion coefficients, save them, and apply them efficiently in a continuous real-time loop.

---

## 3. Implementation Rules & Best Practices

### A. Video Ingestion (USB on Jetson)
Since the feed comes via a USB capture device, rely on the `v4l2` backend. 
- Always verify the USB capture device's supported formats using terminal command: `v4l2-ctl --device=/dev/video0 --list-formats-ext`.
- If the USB device outputs **MJPEG**, use GStreamer with `nvjpegdec` to offload decoding to the hardware.
- If the USB device outputs **YUYV/RAW**, use GStreamer with `nvvidconv` to convert to BGR efficiently.
- **Example GStreamer Pipeline for RAW USB:** `v4l2src device=/dev/video0 ! video/x-raw, format=YUY2 ! nvvidconv ! video/x-raw(memory:NVMM) ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink drop=1`

### B. Calibration Data Collection
- Use a rigid, perfectly flat black-and-white checkerboard.
- Capture 30-50 frames at varying distances, angles, and skew orientations.
- Ensure the checkerboard covers different areas of the frame, especially the edges and corners where lens distortion is highest.
- Save frames to disk as lossless `.png` files to avoid compression artifacts that could shift corner detection.

### C. Calibration Processing (Run Once)
- Use `cv2.findChessboardCorners()` to detect the grid.
- **Critical:** Always refine the detected corners to sub-pixel accuracy using `cv2.cornerSubPix()` before calculating the matrix.
- Pass the refined points into `cv2.calibrateCamera()` to obtain the Camera Matrix ($K$) and Distortion Coefficients ($D$).
- Serialize and save these matrices to a `.yaml` or `.json` file. Do not hardcode these arrays into the application script.

### D. Real-Time Undistortion Loop (Continuous)
- **Do NOT** use `cv2.undistort()` inside the main `while True:` loop. It is too computationally expensive for high-FPS edge data collection.
- **Optimization Strategy:** 1. Load the `.yaml`/`.json` file during initialization.
  2. Compute the optimal new camera matrix using `cv2.getOptimalNewCameraMatrix()`.
  3. Pre-calculate the distortion maps *once* using `cv2.initUndistortRectifyMap()`.
  4. Inside the main frame-capture loop, use `cv2.remap()` using the pre-calculated maps.

---

## 4. Required File Structure
When building the project, structure the files as follows:
- `capture_samples.py`: Script to preview the USB feed and save calibration frames on keypress.
- `calibrate.py`: Script to process the saved images, perform the math, and generate `calibration_data.yaml`.
- `live_undistort.py`: The production script that reads the USB feed, loads the YAML, and applies `cv2.remap()` in real-time.

---

## 5. References & Resources
*Per user guidelines, all information and methodologies must be grounded in official documentation.*

1. **OpenCV Camera Calibration Tutorial:**
   - URL: https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html
   - *Use for:* Mathematical foundational context, `cornerSubPix`, and `calibrateCamera` usage.
2. **NVIDIA Jetson Linux Developer Guide (Multimedia API / V4L2):**
   - URL: https://docs.nvidia.com/jetson/archives/r35.4.1/DeveloperGuide/text/SD/Multimedia/V4l2VideoDecoder.html
   - *Use for:* Optimizing the V4L2 capture pipeline on the Orin architecture.
3. **OpenCV GStreamer Integration:**
   - URL: https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html
   - *Use for:* Constructing the `appsink` and `v4l2src` strings inside `cv2.VideoCapture()`.
