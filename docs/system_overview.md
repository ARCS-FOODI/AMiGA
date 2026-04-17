# System Overview

AMiGA (Automated Modular Irrigation & Growth Assistant) is a research platform for Controlled Environment Agriculture (CEA). It integrates real-time environmental sensing with automated resource management (water, lighting, nutrients).

- **Platform:** Raspberry Pi / Jetson Orin / PC (Simulation)
- **Languages:** Python 3.10+, JavaScript (ES6+)
- **Frameworks:** FastAPI, React (Vite)
- **Core Controller:** [Main Controller](hardware/main_controller.md)

## Software Architecture

### Backend (Python)
The backend is a highly modular, high-performance **FastAPI** application serving as the hardware and telemetry gateway.
It is organized into specific directories for its core functions (`api/` for endpoints, `data/` for persisted local state files).

- **Hardware Abstraction**: Device-specific driver classes for pumps, lights, and sensors (scale, SIS, SCD41, TSL2561).
- **Background Tasks**: The `grow_scheduler` coordinates daily feeding and light cycles, alongside diagnostic scripts like `pump_diagnostic.py`.
- **Telemetry Processing**: Dedicated telemetry modules (`scale_telemetry.py`, `sis_telemetry.py`) funnel sub-sensor data asynchronously into organized databases or CSV stores.

### Edge Computing & Integrations
AMiGA expands beyond a single controller via external edge devices for extended data extraction:
- **Jetson Orin Vision**: High-performance hardware-accelerated image pipeline handling IR moisture heatmaps and timelapses.
- **Pi4 Telemetry Scraper**: Dedicated node to interactively OCR and scrape data from closed-ecosystem applications (e.g., Vivosun Android App).

### Frontend (React)
A responsive web dashboard built with **Vite** and **Tailwind CSS**. It provides:
- **Manual Overrides**: Instant control toggle for pumps and lights.
- **Rule Configuration**: User-defined moisture thresholds for automated irrigation.
- **Data Visualization**: Live graphing of soil health and system metrics.

## Hardware Composition
The AMiGA physical stack is modular:
- **Irrigation**: Peristaltic [Pumps](hardware/pumps.md) driven by TMC2209 stepper drivers.
- **Lighting**: High-intensity grow [Lights](hardware/lights.md) managed via SSR relays.
- **Atmospheric Sensors**: I2C environmental tracking using SCD41 (CO2/Temp/Hum) and TSL2561 (Luminosity).
- **Soil Intelligence**: [Sensors](hardware/sensors.md) (Analog Moisture Array) and [SIS](hardware/sis.md) (7-in-1 Modbus NPK/pH/EC).
- **Precision Metrics**: Integrated [Scale](hardware/scale.md) for harvest weight tracking.

## System Usage
- **Precision Automation**: Closed-loop feedback mechanism where sensor data directly informs pump activity.
- **Research Integrity**: Every action is written to CSVs with high-precision timestamps to support academic reproducibility within the FOODI initiative.
