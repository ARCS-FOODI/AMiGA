# Hardware Integration Overview

This document provides an index of AMiGA's physical hardware integration and wiring configurations. Click on a component below for detailed technical documentation.

## Core Components
- [Physical Environment & Rigging](hardware/physical_environment.md) - Details the Vivosun tent setup and custom wooden AMiGA hardware tower.
- [System Overview](system_overview.md) - High-level software and hardware architecture.
- [Main Controller](hardware/main_controller.md) - Raspberry Pi and GPIO management.
- [Pumping System](hardware/pumps.md) - TMC2209 drivers and pump configurations.
- [Lighting System](hardware/lights.md) - Grow Light Relay and NC logic.

## Measurement & Sensing
- [Weight Measurement](hardware/scale.md) - U.S. Solid digital scale.
- [Moisture Sensor Array](hardware/sensors.md) - ADS1115 analog sensors.
- [Soil Integrated Sensor (SIS)](hardware/sis.md) - 7-in-1 NPK/pH/EC sensor via Modbus.
- [Atmospheric Sensors](hardware/atmospheric_sensors.md) - SCD41 (CO2/Temp/Hum) and TSL2561 (Luminosity).

## Edge Compute & Vision
- [Vivosun Telemetry Scraper](hardware/vivosun_telemetry.md) - Pi4 Android OCR automation pipeline.
- [Jetson Orin Vision](hardware/orin_vision.md) - Hardware-accelerated IR moisture tracking.
