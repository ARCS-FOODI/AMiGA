# Atmospheric & Luminosity Sensors

In addition to integrated soil telemetry, AMiGA natively supports I2C environmental and illumination sensors for atmospheric tracking in Controlled Agriculture.

## SCD41 (CO2, Temp, Humidity)
The backend leverages the Sensirion SCD41 for high-accuracy local environmental metrics.
- Uses photoacoustic NDIR sensing technology.
- **Capabilities**: Captures ambient Temperature, Relative Humidity, and parts-per-million (PPM) CO2 readings, providing crucial baseline information for greenhouse or closed-tent aeration logic.
- Implemented within the backend at `scd41.py`.

## TSL2561 (Luminosity)
Precise ambient lighting logic relies on the TSL2561 Digital Luminosity/Lux sensor.
- **Dual-Diode Sensing**: Accurately computes human-visible brightness alongside raw broad-spectrum (including infrared) capture.
- **Application**: Allows the `grow_scheduler` and backend to verify the output status of the lighting relays and estimate lux accumulation throughout the designated photoperiod independently from basic on/off states.
- Implemented within the backend at `tsl2561.py`.
