# Weight Measurement

- **Device:** **U.S. Solid USS-DBS61-50** Digital Balance Scale.
- **Interface:** RS232-to-USB Serial.
- **Port:** `/dev/ttyUSB0` (9600 baud, 8N1).
- **Controller:** Software managed by `backend/scale.py` (`ScaleManager` class).
- **Simulation:** A software-only mock is available (`_SimulatedScaleManager`) for development without hardware.

## Functional API & Usage

### API Endpoints (`/scale`)
- `GET /scale/read`: Returns the current weight in grams.
- `POST /scale/tare`: Zeroes out the scale relative to its current load.

### System Usage
- **Weight Tracking**: Used to monitor the total weight of the growth basin. 
- **Simulated Growth**: In simulation mode, the weight increases over time based on a `growth_rate_g_per_sec` to mimic plant mass accumulation.
- **Liquid Accumulation**: In simulation mode, the scale's "weight" is incremented every time a pump dispenses liquid (assuming 1ml = 1g density).
