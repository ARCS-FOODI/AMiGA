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
