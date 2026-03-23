# Pumping System

Precise fluid delivery is handled by stepper motors driven by "smart" drivers.

## Stepper Drivers (TMC2209)
- **Model:** Trinamic TMC2209
- **Communication:** UART via `/dev/serial0` (115200 baud)
- **Features:** StallGuard (load sensing), individual Enable control.
- **Node Addresses:** 
  - Food Pump: `0`
  - Water Pump: `1`

## Pump Configuration
- **Water Pump**
  - **STEP:** BCM 16
  - **DIR:** BCM 26
  - **EN:** BCM 17
- **Food Pump**
  - **STEP:** BCM 27
  - **DIR:** BCM 22
  - **EN:** BCM 24
- **Software Management:** Controlled via `backend/pumps.py` and `backend/pump_diagnostic.py`.
- **Note:** EN pins are active LOW (Logic `0` enables the driver, `1` disables/sleeps). Each pump has a dedicated EN pin to prevent cross-talk and vibration issues.

## Functional API & Usage

### API Endpoints (`/pump`)
- `POST /pump/run-seconds`: Run a specific pump for a fixed duration.
- `POST /pump/run-ml`: Dispense a specific volume (ml) using the latest calibration data.
- `POST /pump/run-multi-seconds`: Run multiple pumps simultaneously (e.g., for flushing or mixing).
- `POST /pump/calibrate-seconds`: Trigger a timed run for manual volume measurement.
- `GET /pump/calibration`: Fetch all current ml/s rates.
- `POST /pump/calibration`: Update the ml/s rate for a specific pump.

### System Usage
- **Irrigation Logic**: The `control.py` module uses the **Water Pump** to automatically hydrate plants when moisture sensors cross a specific threshold.
- **Nutrient Dosing**: The `grow_scheduler.py` module triggers the **Food Pump** daily once plant germination is detected, delivering a precise "dose" of solution.
- **Calibration Storing**: Rates are persisted in `config/calibration.json` via the `config_store.py` module.
