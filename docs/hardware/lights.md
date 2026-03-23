# Lighting System

## Grow Light Relay
- **GPIO Pin:** `LIGHT_PIN` (Configured in `backend/settings.py`)
- **Controller:** Software managed by `backend/light.py` (`GrowLight` class)
- **Physical Integration:** 
  - We use an external programmable relay module.
  - The relay interacts with a separate default control module that powers the lights.
  - Shorting the pins on the control module turns the lights **OFF**. Removing the short turns the lights **ON**.
- **Wiring Configuration (As of March 2026):**
  - **Terminal:** Normally Closed (NC)
  - **Default Unpowered Behavior:** By default, with the Raspberry Pi completely powered down, the relay loses power. The NC contacts remain closed, shorting the control module and keeping the lights **OFF**.
  - **Software Logic:**
    - To turn the light **ON**, we assert GPIO **HIGH** (1) to energize the relay, opening the NC circuit and removing the short.
    - To turn the light **OFF**, we assert GPIO **LOW** (0) to de-energize the relay, closing the NC circuit and shorting the module.

## Functional API & Usage

### API Endpoints (`/light`)
- `GET /light`: Retrieve current logical status.
- `POST /light`: Manually set state to ON or OFF.
- `POST /light/toggle`: Flip the current state.
- `POST /light/on-for`: Turn light ON for a specific duration (seconds), then automatically turn OFF.
- `GET /light/config`: View current mode (manual/daynight) and schedule.
- `POST /light/config`: Update schedule (start/end times) and switch modes.

### System Usage
- **Automated Scheduling**: The `grow_scheduler.py` module manages the "Day/Night" cycle. It ensures the relay is energized during day hours to provide light to the plants.
- **Safety Defaults**: On system failure or shutdown, the GPIO defaults to LOW, which (due to NC wiring) ensures the light remains **OFF** to avoid unexpected high-power usage or safety risks.
