# Soil Integrated Sensor (SIS)

- **Model:** 7-in-1 Soil Sensor (NPK + pH + EC + Temp + Moisture).
- **Protocol:** Modbus RTU over RS485-to-USB.
- **Port:** `/dev/ttyUSB1` (Slave ID: 1, 9600 baud).
- **Software Logic:** Managed by `backend/sis.py` (`SoilIntegratedSensor` class).
- **Registers:**
  - **pH:** Address 6 (Scale 100)
  - **Moisture:** Address 18 (Scale 10)
  - **Temp:** Address 19 (Scale 10, Signed)
  - **EC:** Address 21
  - **NPK:** Addresses 30, 31, 32

## Functional API & Usage

### API Endpoints (`/sis`)
- `POST /sis/read`: Performs a Modbus query to retrieve all 7 parameters (Moisture, Temp, EC, pH, N, P, K).

### System Usage
- **Precision Monitoring**: Provides high-accuracy data compared to generic moisture sensors.
- **NPK Tracking**: Used to determine if nutrient levels (Nitrogen, Phosphorus, Potassium) are within the ideal range for the current growth phase.
- **Soil Chemistry**: pH and EC (Electrical Conductivity) values are monitored to prevent nutrient lockout or root burn.

## Telemetry Logging (New Feature)

The AMiGA backend now strictly tracks historical SIS data utilizing a dedicated background thread manager (`backend/sis_telemetry.py`).
- **Interval:** Reads and records the 7-in-1 sensor payload exactly once every 1.0 second.
- **Log Location:** `~/.amiga_runtime_data/sis_data.csv`
- **CSV Output Format:**
  - `time`: Current Timestamp (YYYY-MM-DD HH:MM:SS)
  - `data type`: `telemetry`
  - `componeent`: `SIS.py`
  - `values`: Semicolon-separated key-value pairs (e.g., `ph=6.5; moisture=45.2; temperature=18.5; ec=800; ...`)
