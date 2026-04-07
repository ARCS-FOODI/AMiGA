# Pump Telemetry Implementation

This document details the recent updates made to implement universal, on-demand pump telemetry for the AMiGA system.

## Summary of Changes

1. **Telemetry Logging Module (`backend/pump_telemetry.py`)**
   - Created a new module to handle logging explicitly requested pump actions.
   - Saves telemetry data to a localized wide CSV table at `~/.amiga_runtime_data/pump_telemetry.csv`.
   - The CSV structure captures: `Time`, `Component`, `Action`, `Direction`, `Amount (mL)`, `Duration (s)`, and `Frequency (Hz)`.
   - Normalizes display names to standard formats (e.g., `water_pump` and `food_pump`).

2. **Pump API Router Logging (`backend/api/routers/pumps.py`)**
   - Integrated the `pump_telemetry.log_action()` function into the API endpoints to record user-triggered actions.
   - `api_run_pump_seconds` logs a **"Manual Prime"** event, recording direction, seconds, and Hz.
   - `api_run_pumps_seconds` logs a **"Manual Prime (Multi)"** event for multiple pump targets.
   - `api_run_pump_ml` logs a **"Dispense Volume"** event, recording the volume (mL).

3. **Stepper Pump State Tracking (`backend/pumps.py`)**
   - Added a public `self.direction` state attribute to the `StepperPump` class (defaults to `"forward"`).
   - Updated the `set_direction()` method to update `self.direction` (`forward` or `reverse`) when the GPIO pins are toggled, allowing the telemetry to accurately record the active motor direction.

4. **Testing Infrastructure (`backend/test_telemetry.py`)**
   - Added a testing script (`test_telemetry.py`) to verify the telemetry module's lifecycle capabilities.

## Architecture & Benefits

The previous telemetry system relied on continuous background polling. This new architecture creates an **event-based ledger**. Every time a user initiates a pump action through the frontend dashboard or API, the backend immediately records exactly what operation was performed and its configuration details. This reduces redundant idle data and ensures clean logs.
