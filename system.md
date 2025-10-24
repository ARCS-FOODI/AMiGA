# AMiGA System Overview

The AMiGA system.py is an automated plant irrigation controller implemented on a Raspberry Pi 5. The system operates through moisture-based feedback control, utilizing sensor data to manage water distribution.

## System Components

1. **Moisture Monitoring System**
   - Four soil moisture sensors for distributed measurement points
   - ADS1115 analog-to-digital converter for sensor readings
   - Moisture values are converted to percentages (0% dry to 100% saturated)

2. **Water Distribution System**
   - Peristaltic pump controlled by TMC2209 driver
   - Capable of timed operation or volumetric dispensing
   - Programmable flow rates through step frequency control

3. **Operating Modes**

The system implements three primary operating modes:
   - **Calibration Mode**: Determines pump flow rate for volumetric dispensing
   - **Sensor Mode**: Displays real-time moisture readings from all sensors
   - **Full Mode**: Autonomous operation with moisture-based irrigation control

## Operational Logic

The system follows this control sequence:
1. Continuous monitoring of all moisture sensors
2. Threshold comparison with configurable parameters
3. Irrigation activation when moisture conditions meet trigger criteria
4. Timed cooldown period between irrigation cycles

Example configuration: Irrigation trigger when 2/4 sensors report below 40% moisture, followed by a 5-second water distribution cycle and 10-minute cooldown period.

## Technical Features

- Four-channel moisture monitoring capability
- Configurable moisture thresholds
- Precise volumetric or time-based water distribution
- Cooldown period implementation for preventing oversaturation
- Real-time moisture level monitoring
- Compatible with both analog and digital moisture sensors

## Applications

The system is applicable in:
- Indoor cultivation environments
- Greenhouse installations
- Precision irrigation requirements
- Moisture-sensitive plant cultivation

The implementation improves upon timer-based systems by incorporating feedback control, resulting in demand-based irrigation scheduling rather than fixed-interval operation. This approach optimizes water usage and maintains consistent soil moisture levels.