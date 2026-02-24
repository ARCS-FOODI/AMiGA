# backend/light.py
from __future__ import annotations

import time
import threading
from datetime import datetime, time as dtime
from typing import Dict, Any

import lgpio

from .settings import CHIP, LIGHT_PIN
from . import master_log


class GrowLight:
    """
    Object-Oriented representation of the Grow Light Relay.
    Manages its own GPIO state and day/night scheduling logic.
    """
    def __init__(self, pin: int = LIGHT_PIN, chip: int = CHIP):
        self.pin = pin
        self.chip = chip
        self._handle = None
        self._lock = threading.Lock()
        
        # Logical state
        self.is_on = False
        
        # Schedule config
        self.mode = "manual"
        self.day_start = dtime(19, 0)
        self.day_end = dtime(7, 0)

    def initialize(self, handle: int) -> None:
        """Bind the light to an open GPIO handle and set as output."""
        self._handle = handle
        # Default to OFF on boot
        level = self._level_for_state(False)
        lgpio.gpio_claim_output(self._handle, self.pin, level)
        self.is_on = False

    def _level_for_state(self, on: bool) -> int:
        """
        Map logical light state to the actual GPIO level.
        Relay is wired ACTIVE-LOW:
          - GPIO LOW (0)  -> light ON
          - GPIO HIGH (1) -> light OFF
        """
        return 0 if on else 1

    def set_state(self, on: bool, log_source: str = "GrowLight.set_state") -> Dict[str, Any]:
        """Turn the light ON or OFF by driving the relay pin."""
        if not self._handle:
            raise RuntimeError("GrowLight is not initialized.")

        with self._lock:
            level = self._level_for_state(on)
            lgpio.gpio_write(self._handle, self.pin, level)
            self.is_on = on

        try:
            master_log.log_event(
                "light_state",
                source=log_source,
                light_on=on,
            )
        except Exception as e:
            print(f"[LOG] Failed to log light_state to master.csv: {e}")

        return {"light_pin": self.pin, "on": self.is_on}

    def toggle(self) -> Dict[str, Any]:
        """Flip the light from ON→OFF or OFF→ON."""
        return self.set_state(not self.is_on, log_source="GrowLight.toggle")

    def get_state(self) -> Dict[str, Any]:
        """Return logical state without touching hardware."""
        return {"light_pin": self.pin, "on": self.is_on}

    def set_after_delay(self, on: bool, delay: float) -> None:
        """Sleep, then set state (used by BackgroundTasks)."""
        time.sleep(delay)
        self.set_state(on, log_source="GrowLight.set_after_delay")

    def _parse_hhmm(self, value: str) -> dtime:
        parts = value.strip().split(":")
        if len(parts) < 2:
            raise ValueError("Time must be in HH:MM or HH:MM:SS format")
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
        return dtime(hour, minute, second)

    def set_config(self, mode: str, day_start: str, day_end: str) -> Dict[str, Any]:
        mode = mode.lower()
        if mode not in ("manual", "daynight"):
            raise ValueError("mode must be 'manual' or 'daynight'")

        self.mode = mode
        self.day_start = self._parse_hhmm(day_start)
        self.day_end = self._parse_hhmm(day_end)

        try:
            master_log.log_event(
                "light_config_set",
                source="GrowLight.set_config",
                note=f"mode={mode}, day_start={day_start}, day_end={day_end}",
            )
        except Exception as e:
            print(f"[LOG] Failed to log light_config_set: {e}")

        return self.get_config()

    def get_config(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "day_start": self.day_start.strftime("%H:%M:%S"),
            "day_end": self.day_end.strftime("%H:%M:%S"),
            "state": self.get_state(),
        }

    def _is_within_window(self, now: datetime) -> bool:
        t = now.time()
        if self.day_start < self.day_end:
            return self.day_start <= t < self.day_end
        else:
            return not (self.day_end <= t < self.day_start)

    def apply_daynight_now(self) -> Dict[str, Any]:
        now = datetime.now().astimezone()
        if self.mode != "daynight":
            return {
                "mode": self.mode,
                "applied": False,
                "within_window": None,
                "state": self.get_state(),
            }

        within = self._is_within_window(now)
        # Only update hardware if state actually needs to change, or force it
        result = self.set_state(within, log_source="GrowLight.apply_daynight_now")

        try:
            master_log.log_event(
                "light_daynight_apply",
                source="GrowLight.apply_daynight_now",
                light_on=result.get("on"),
                note=f"within_window={within}",
            )
        except Exception as e:
            print(f"[LOG] Failed to log light_daynight_apply: {e}")

        return {
            "mode": self.mode,
            "applied": True,
            "within_window": within,
            "state": result,
        }


class LightManager:
    """Global manager for lighting hardware."""
    def __init__(self, chip_index: int = CHIP):
        self.chip_index = chip_index
        self._handle = None
        self.main_light = GrowLight(pin=LIGHT_PIN, chip=self.chip_index)

    def startup(self) -> None:
        self._handle = lgpio.gpiochip_open(self.chip_index)
        self.main_light.initialize(self._handle)

    def shutdown(self) -> None:
        if self._handle is not None:
            # Safely turn light off on shutdown
            self.main_light.set_state(False, log_source="LightManager.shutdown")
            lgpio.gpiochip_close(self._handle)
            self._handle = None


# Global singleton
manager = LightManager()

# --- Legacy Procedural Wrappers ---
def _ensure_manager():
    if manager._handle is None:
        manager.startup()

def set_light(on: bool) -> Dict[str, Any]:
    _ensure_manager()
    return manager.main_light.set_state(on)

def get_light_state() -> Dict[str, Any]:
    return manager.main_light.get_state()

def toggle_light() -> Dict[str, Any]:
    _ensure_manager()
    return manager.main_light.toggle()

def set_light_after_delay(on: bool, delay: float) -> None:
    _ensure_manager()
    manager.main_light.set_after_delay(on, delay)

def get_light_config() -> Dict[str, Any]:
    return manager.main_light.get_config()

def set_light_config(mode: str, day_start: str, day_end: str) -> Dict[str, Any]:
    return manager.main_light.set_config(mode, day_start, day_end)

def apply_daynight_now() -> Dict[str, Any]:
    _ensure_manager()
    return manager.main_light.apply_daynight_now()
