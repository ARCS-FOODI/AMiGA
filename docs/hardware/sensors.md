# Sensor Suite

## Moisture Array (ADS1115)
- **ADC:** **ADS1115** (4-channel, 16-bit I2C).
- **I2C Address:** `0x48`.
- **Gain:** `2/3` (±6.144V Range) — Required to safely read 5V sensor signals.
- **Physical Integration:** 
  - Up to 4 analog moisture sensors connected to channels **A0, A1, A2, A3**.
  - Optional digital wet/dry sensor on **BCM 6**.
- **Controller:** Software managed by `backend/sensors.py` (`SensorArray` class).
