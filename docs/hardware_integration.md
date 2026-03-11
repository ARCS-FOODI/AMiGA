# Hardware Integration Documentation

This document serves as a record for AMiGA's physical hardware integration, wiring configurations, and module interactions. Keeping this up to date is required for anyone performing dev work on software modules that interface with these components.

## Lighting System

### Grow Light Relay
- **GPIO Pin:** `LIGHT_PIN` (Configured in `backend/settings.py`)
- **Controller:** Software managed by `backend/light.py` (`GrowLight` class)
- **Physical Integration:** 
  - We use an external programmable relay module.
  - The relay interacts with a separate default control module that powers the lights.
  - Shorting the pins on the control module turns the lights **OFF**. Removing the short turns the lights **ON**.
- **Wiring Configuration (As of March 2026):**
  - **Terminal:** Normally Closed (NC)
  - **Default Unpowered Behavior:** By default, with the Raspberry Pi completely powered down, the relay loses power. The NC contacts remain closed, shorting the control module and keeping the lights **OFF**. This ensures the lights aren't active during system reboots or offline periods.
  - **Software Logic:**
    - To turn the light **ON**, we assert GPIO **HIGH** (1) to energize the relay, opening the NC circuit and removing the short.
    - To turn the light **OFF**, we assert GPIO **LOW** (0) to de-energize the relay, closing the NC circuit and shorting the module.

## Future Components...

*Add details for new hardware (pumps, sensors, probes, etc.) below as they are integrated or documented.*
