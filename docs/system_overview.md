# System Overview

AMiGA (Automated Modular Irrigation & Growth Assistant) is a research platform for Controlled Environment Agriculture (CEA). It integrates real-time environmental sensing with automated resource management (water, lighting, nutrients).

- **Platform:** Raspberry Pi / PC (Simulation)
- **Languages:** Python 3.10+, JavaScript (ES6+)
- **Frameworks:** FastAPI, React (Vite)
- **Core Controller:** [[main_controller]]

## Software Architecture

### Backend (Python)

The backend is a high-performance **FastAPI** application that serves as the hardware gateway. It handles:

- **Hardware Abstraction**: Unified classes for [[pumps]], [[sensors]], and [[sis]] (Soil Integrated Sensor).
- **Background Tasks**: The `grow_scheduler` coordinates daily feeding and light cycles.
- **Telemetry**: Real-time logging of [[scale]] (weight) and SIS data to CSV for later analysis.

### Frontend (React)

A responsive web dashboard built with **Vite** and **Tailwind CSS**. It provides:

- **Manual Overrides**: Instant control toggle for pumps and lights.
- **Rule Configuration**: User-defined moisture thresholds for automated irrigation.
- **Data Visualization**: Live graphing of soil health and system metrics.

## Hardware Composition

The AMiGA physical stack is modular and extensible:

- **Irrigation**: Peristaltic [[pumps]] driven by TMC2209 stepper drivers.
- **Lighting**: High-intensity grow [[lights]] managed via SSR relays.
- **Soil Intelligence**: [[sensors]] (Analog Moisture) and [[sis]] (7-in-1 NPK/pH/EC).
- **Atmospheric Monitoring**: SCD41 CO2/Temp/Humidity sensing.
- **Precision Metrics**: Integrated [[scale]] for nutrient and harvest weight tracking.

## Functional API & Usage

### API Endpoints (`/config`)

- `GET /config`: Global system configuration parameters.
- `POST /config/calibration`: Update ml/s rates for pumps or gain values for sensors.

## System Usage

- **Precision Automation**: The system uses a closed-loop feedback mechanism where sensor data directly informs pump activity.
- **Research Integrity**: Every action (relay toggle, motor step, sensor query) is written to `master.csv` with nanosecond-precision timestamps to support academic reproducibility within the FOODI initiative.
