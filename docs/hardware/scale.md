# Weight Measurement

- **Device:** **U.S. Solid USS-DBS61-50** Digital Balance Scale.
- **Interface:** RS232-to-USB Serial.
- **Port:** `/dev/ttyUSB0` (9600 baud, 8N1).
- **Controller:** Software managed by `backend/scale.py` (`ScaleManager` class).
- **Simulation:** A software-only mock is available (`_SimulatedScaleManager`) for development without hardware.
