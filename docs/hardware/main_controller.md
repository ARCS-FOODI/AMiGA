# Main Controller

- **Platform:** Raspberry Pi
- **GPIO Chip:** `/dev/gpiochip0` (Configured as `CHIP = 0` in `backend/settings.py`)
- **Library:** Managed via `lgpio` for direct pin control.

## Functional API & Usage

### API Endpoints (`/control`)
- `POST /control/cycle-once`: Executes a single evaluation of the irrigation rules.
- `POST /control/run-continuous`: (Legacy/Test) Starts a blocking continuous control loop.

### System Usage
- **Global Orchestration**: The Pi runs the `amiga-grow-scheduler` thread, which coordinates lighting and feeding.
- **Event Logging**: All hardware events (motor steps, sensor reads, relay toggles) use device-specific CSV telemetry logging for system-wide auditing.
