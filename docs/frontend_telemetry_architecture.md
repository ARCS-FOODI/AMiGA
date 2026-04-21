# Frontend Telemetry Architecture & Data Pipelining

This document outlines the data that the AMiGA frontend Dashboard currently receives, how the telemetry history pipelines operate, and the primary scaling hurdles (and solutions) regarding real-time visualization.

## 1. Overview of Data Received by the Frontend

The AMiGA dashboard relies heavily on real-time hardware status metrics and telemetry historical charts. This data is driven by the React component `TelemetryChart.jsx` which polls the backend for time-windowed slices of active recording sessions. 

The main dashboard (`App.jsx`) initializes 8 instances of `TelemetryChart`. Every 5 seconds (configurable via `POLL_INTERVALS.CHART`), the dashboard requests the following 5 unique CSV datasets from the active tracking session:

### A. Environment Conditions (`co2_data.csv`)
- **Source**: SCD41 Sensor
- **Data Columns**: `co2_ppm`, `humidity_percent`, `temperature_c`
- **Rendered instances**: 1 chart instance

### B. Luminosity (`light_data.csv`)
- **Source**: TSL2561 Sensor
- **Data Columns**: `lux`
- **Rendered instances**: 1 chart instance

### C. Soil Moisture Sensor Arrays (`sensors.csv`)
- **Source**: ADS1115 ADC Modules (I2C addressed, typically `0x48` and `0x4b`)
- **Data Columns**: `time`, `device_id`, `v0`, `v1`, `v2`, `v3` (representing raw voltages for 4 probes per tray).
- **Rendered instances**: 3 chart instances (One Comparative Matrix overlaying all devices, and two isolated charts for Tray 1 and Tray 2).

### D. Soil Chemistry and Nutrients (`sis_data.csv`)
- **Source**: SIS Modbus Sensors
- **Data Columns**: `nitrogen`, `phosphorus`, `potassium`, `ph`, `ec`, `temperature`
- **Rendered instances**: 2 chart instances (One specifically targeting NPK metrics, one targeting general chemistry).

### E. Yield / Biomas Weight (`scale_data.csv`)
- **Source**: Serial Payload Scale
- **Data Columns**: `weight_g`
- **Rendered instances**: 1 chart instance


---

## 2. The Scaling Hurdle: Data Pipelining and UI Freezing

**The Problem:**
Recently, we accelerated the data polling resolution to increase precision (e.g. backend recording sensor states up to 10Hz/10 records per second). 

By default, the `TelemetryChart` component fetches a 4-hour chronological slice of the CSV. At 10Hz, a 4-hour window holds **144,000 data rows**. 

1. **Network Payload:** The frontend requested this massive CSV over HTTP every 5 seconds.
2. **Main-thread CPU Thrash:** React then passed the CSV text string into `Papa.parse()` on the main event loop, resulting in browser lockouts.
3. **DOM Overload:** The charting library, `Recharts`, isn't optimized for thousands of data points at once. Injecting over one hundred thousand SVG node definitions per chart caused complete system latency ("hard time loading/operating").
4. **Multiplier Effect:** Because the dashboard features *8 independent charts*, this operation was executed 8 times simultaneously every 5 seconds.

---

## 3. The Implementation and Fix

To fix this, we implemented **Intelligent API Downsampling** directly on the backend without altering the frontend's visual timeline expectations.

### Backend Enhancements (`backend/api/routers/recording.py`)

1. **`max_points` Capping**: The endpoint `/active/window/{filename}` now accepts a `max_points` argument, automatically defaulting to `150`.
2. **Reverse Chronological Streaming**: We already utilized efficient reverse read-seeking to only grab the relevant last hours of data without loading the whole file into server memory.
3. **Equal Device Representation**: Instead of blindly removing rows, our new logic analyzes headers. If it detects a `device_id` or `device_name` string signature, it:
   - Group all valid timeline data by the device ID bucket.
   - Perform Systematic Sampling to reduce each bucket to maximum 150 points.
   - Merge and re-sort the results back into a strictly chronological timeline.

### Frontend Rendering & Canvas Optimizations (`frontend/src/components/TelemetryChart.jsx`)
While the backend downsampling successfully mitigated the bulk of the RAM memory overload, the system still encountered graphical crashes (the "black void" UI cutoff) on Linux hardware graphics acceleration due to the high volume of computationally heavy SVG Bézier curve vectors (e.g., drawing 150 smooth points * 8 charts * 4 data series simultaneously). To solve this:

1. **Spline Geometry Downgrade**: The Recharts graphing engine was forcibly downgraded from `type="monotone"` to `type="linear"`. This prevents the Javascript thread from executing thousands of expensive tangent calculation algorithms natively per tick, substituting complex `<path>` curves (C instructions) with lightweight point-to-point lines (L instructions) and bypassing hardware acceleration limits.
2. **Event Prioritization & Yielding**: We wrapped the React `setData` manipulation inside `startTransition`. This native React 18 feature forces the application to evaluate geometric chart reconstruction in a background-thread priority state, leaving the core UI event loop unblocked and avoiding gridlock latency.
3. **Data Constraint Hardening**: The maximum point threshold was further compressed on the frontend. The `fetchTelemetryWindow` module now enforces exactly `max_points=60` locally via URI parameters, mathematically ensuring that the canvas paints no more than one data point per 5-pixel radius on typical 300px UI cards, cutting graphic pipeline overhead by a resulting 66%.

### Results

The frontend still requests the 4-hour window. However, the backend mathematically filters the results and provides a tightly representative representation containing at most 150 points. 

- Data processing overhead dropped from megabytes to kilobytes.
- CSV parsing resolves in `<2 milliseconds`.
- DOM Rendering returns to instant-execution.
- Continuous lines remain smooth thanks to `Recharts` interpolating points cleanly, preserving the full scale and perspective of the multi-hour view without the data bloat.

---

## 4. Future-Proofing & Ongoing Monitoring

To ensure we never accidentally stumble into similar pipelining nightmares, we've implemented active frontend metrics:

### Dynamic Payload Metrics
In `frontend/src/api.js`, the `fetchTelemetryWindow` method evaluates the size (in KB) of incoming payloads:
- `< 50 KB`: Logs a standard `[METRIC] debug` event to the browser console.
- `> 50 KB`: Emits a `[METRIC NOTICE]` warn log to keep an eye on DOM performance.
- `> 500 KB`: Sounds an extreme `[METRIC ALERT]` siren to alert developers that the backend downsampling limits have likely failed.

### Architectural Inefficiencies Let's Keep an Eye On
Currently, every `TelemetryChart.jsx` instance resolves its own data independently over the network. 
- **The Issue**: Because `App.jsx` mounts three separate charts for `sensors.csv` (One Comparative, Tray 1, and Tray 2), and two for `sis_data.csv`, the client is re-requesting the **same exact CSV files** multiple times every 5 seconds.
- **The Ideal Future Fix**: If scaling hits bottlenecks again, we should implement a central `TelemetryContext` or `Redux Store` that fetches `sensors.csv` and `sis_data.csv` *once* per polling cycle, and distributes the data downward to the nested chart components. Currently, it's trivial due to the newly implemented downsampling constraint (150 rows), but something to keep in mind!
