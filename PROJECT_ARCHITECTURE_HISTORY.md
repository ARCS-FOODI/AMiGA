# Chunk 1 History (Commits 1-50)

## Overview

This initial phase establishes the core structure of the AMiGA project, transitioning from legacy scripts to a modernized monorepo architecture.

## Architectural Changes

- **Monorepo Establishment**: The project is structured with a clear separation between `backend/` (Python) and `frontend/` (React/TypeScript).
- **Core Backend Modules**:
  - `backend/api.py`: FastAPI or similar REST API for external interaction.
  - `backend/control.py`: Central orchestration logic for system operations.
  - `backend/pumps.py` & `backend/sensors.py`: Low-level hardware abstractions for pump control and sensor data acquisition.
  - `backend/config_store.py`: Persistent storage for system configuration.
- **Frontend Foundation**: Implementation of a Vite-based React application in the `frontend/` directory, using TypeScript for type safety.
- **Legacy Integration**: Large portions of the original codebase were moved to `legacy/` and `sensoil_legacy/`, indicating a major refactor or porting effort from "Sensoil".
- **Data Handling**: Introduction of `data/moisture_cycles.csv` for tracking environmental data.

## Key Components

- **System Controller**: The `control.py` module appears to be the heartbeat of the system.
- **Hardware Layer**: Direct GPIO or serial communication likely resides in `pumps.py` and `sensors.py`.
# Chunk 2 History (Commits 51-100)

## Overview

This phase marks a significant expansion of the system's capabilities, moving from basic hardware control to a more sophisticated automated "Grow" system with multimodal monitoring.

## Architectural Changes

- **Service Diversification**: The backend architecture introduced specialized modules:
  - `backend/grow_scheduler.py`: Logic for managing plant growth cycles and automated task scheduling.
  - `backend/light.py`: Dedicated control for lighting systems.
  - `backend/master_log.py`: Centralized logging for system-wide events.
- **Multimodal Monitoring & Imaging**:
  - Introduction of `data/ir_pics/` and associated CSV stats (`tray_ir_grid_stats.csv`), indicating the use of Infrared (IR) cameras for plant health or moisture monitoring.
  - The system started capturing and processing large volumes of visual data.
- **External Integrations**:
  - **Waydroid Integration**: Modules in `waydroid/` (`ocr_once.py`, `capture.py`) suggest the system interacts with an Android environment, possibly to OCR data from a third-party sensor app or controller.
  - **Lua Scripting**: Use of Lua in `kratky/` for experiment clocks and sensor reading, possibly for integration with specific hardware controllers (like ESP32 or similar) that prefer Lua.
- **Hydroponics Focus**: Explicit references to the "Kratky" method confirm the project's application in hydroponics automation.

## Key Components

- **Grow Scheduler**: Becomes a central component for temporal control of the environment.
- **Vision Pipeline**: Initial steps towards automated visual inspection via IR and OCR.
- **Interoperability Layer**: The project now bridges Python, Lua, and Android (via Waydroid).
# Chunk 3 History (Commits 101-150)

## Overview

This phase represents a major architectural "clean-up" and modernization. The system transitioned from monolithic files to modular, scalable structures in both the backend and frontend.

## Architectural Changes

- **FastAPI Modularization**:
  - The backend API was completely restructured from a single `api.py` to a directory-based FastAPI application (`backend/api/`).
  - Use of **Routers** (`routers/control.py`, `routers/light.py`, etc.) and Pydantic **Models** (`models.py`) for better organization and data validation.
- **Frontend Componentization**:
  - The frontend was refactored into a component-based architecture.
  - Specific UI components were created for each system function: `PumpControl`, `LightControl`, `SensorMonitor`, and `AutomationRules`.
  - Replaced the initial TypeScript setup with a more direct JSX structure, possibly for faster iteration or to simplify the stack for specific developers.
- **Improved DevOps & DX**:
  - **Cross-Platform Support**: Addition of installation scripts for Windows (.bat), Linux (.sh), and macOS.
  - **Simulation Infrastructure**: Introduction of `start_simulate.sh` and `start_simulate.bat`, allowing developers to run the system without physical hardware.
  - **Deployment scripts**: `start.sh` and `requirements.txt` formalized the running process.
- **Hardware Reliability**:
  - New diagnostic tools (`pump_diagnostic.py`) and barebones tests were added to harden the hardware interface layer.

## Key Components

- **FastAPI Router Layer**: Provides a clean, documented interface for all hardware operations.
- **React Component Library**: A tailored set of components for managing the hydroponics system.
- **Simulation Layer**: A critical development tool for testing logic without risking hardware.
# Chunk 4 History (Commits 151-200)

## Overview

This phase focused on increasing the system's "IQ" and reliability by integrating advanced sensors, persistent state management, and formalized documentation for both humans and AI.

## Architectural Changes

- **Advanced Sensor Integration**:
  - **Scale System**: Added `backend/scale.py` and a dedicated API router for weighing operations, supported by automated tests (`test_scale.py`).
  - **SIS Integration**: Added "SIS" (likely Soil/Solution Interaction System) monitoring.
  - **NPK Sensing**: Experimental support for NPK (Nitrogen, Phosphorus, Potassium) sensors in `sensoil/`.
- **State Persistence**:
  - Transitioned the scheduler to use `data/scheduler_state.json`, ensuring that growth cycles can resume correctly after a system reboot or crash.
- **Knowledge Base & AI Readiness**:
  - Added `.github/AI_INSTRUCTIONS.md`, establishing a "contract" for AI agents to follow when interacting with the codebase.
  - Created `docs/hardware_integration.md` to document the electrical and protocol details of the hardware layer.
- **Testing Maturity**:
  - Establishing a `backend/tests/` directory signifies a move towards a more professional, test-driven development approach for core hardware logic.
- **Frontend Expansion**:
  - New visualization components for the Scale and SIS systems were added to the dashboard.

## Key Components

- **Persistence Manager**: The logic handling `scheduler_state.json` is vital for long-term automated operations.
- **Diverse Hardware abstraction**: The system now handles Scales, Pumps, Lights, and various environmental sensors (SIS, NPK, Moisture) through a unified API.
- **AI Context Layer**: The inclusion of AI-specific instructions facilitates better collaboration between human developers and AI assistants.
# Chunk 5 History (Commits 201-219)

## Overview

The final phase marks the project's transition into a mature, production-ready system. Key focus areas included environmental precision (CO2), long-term telemetry, and exhaustive documentation.

## Architectural Changes

- **Environmental Precision (SCD41)**:
  - Integrated the **SCD41 CO2, temperature, and humidity sensor**.
  - Added a dedicated API router and frontend monitor for real-time CO2 tracking.
- **Telemetry Layer**:
  - Introduced `scale_telemetry.py` and `sis_telemetry.py`.
  - This architecture allows for persistent, granular tracking of sensor data over time, moving beyond immediate control to historical analysis.
- **Documentation Explosion**:
  - The `docs/` directory was significantly expanded with a structured `hardware/` sub-folder, documenting every major subsystem (lights, pumps, scale, SIS, SCD41).
  - `system_overview.md` was created to provide a coherent entry point for new developers or researchers.
- **Workflow Formalization**:
  - Added `.agent/workflows/doc-history.md`, codifying the process for maintaining architectural documentation using AI.
- **Interface Refinement**:
  - The `ScaleMonitor` component received a massive update, likely adding advanced calibration, taring, and historical graphing features.
  - Improved robustness in the `pumps.py` logic to handle edge cases in automated irrigation.

## Key Components

- **Telemetry Engine**: Enables data-driven decisions for "Grow" recipes.
- **Environmental Suite**: Now includes CO2 as a primary control variable alongside Light and Water.
- **Documentation Suite**: A professional-grade set of hardware and software manuals.
