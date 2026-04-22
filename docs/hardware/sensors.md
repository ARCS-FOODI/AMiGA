# Sensor Suite

## Moisture Array (ADS1115)
- **ADC:** **ADS1115** (4-channel, 16-bit I2C).
- **I2C Addresses:** Supports multiple multi-device arrays simultaneously via I2C (e.g. `0x48` for Tray 1, `0x4b` for Tray 2). The system's backend telemetry aggregates each device robustly into shared CSV arrays.
- **Gain:** `2/3` (±6.144V Range) — Required to safely read 5V sensor signals.
- **Physical Integration:** 
  - Up to 4 analog moisture sensors connected to channels **A0, A1, A2, A3**.
  - Optional digital wet/dry sensor on **BCM 6**.
- **Controller:** Software managed by `backend/sensors.py` (`SensorArray` class).

## Functional API & Usage

### API Endpoints (`/sensors`)
- `POST /sensors/read`: Take a snapshot of all channels. Parameters include:
    - `samples`: Number of distinct snapshots.
    - `avg`: Number of sub-samples to average per channel for noise reduction.
    - `interval`: Time between samples.
    - `invert_do`: Flip digital logic (Wet/Dry).

### System Usage
- **Closed-Loop Control**: Data from these sensors is the primary input for `control.py`. The "Vote-K" logic counts how many sensors report a voltage above the irrigation threshold before triggering a pump run.
- **Environment Logging**: Every read is logged to the `master.csv` file with a timestamp and sample index for long-term health tracking.
