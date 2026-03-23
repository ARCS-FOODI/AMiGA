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
