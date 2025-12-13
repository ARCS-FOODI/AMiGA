# backend/light.py
from __future__ import annotations

from typing import Dict, Any
import time
from datetime import datetime, time as dtime

import lgpio

from .settings import CHIP, LIGHT_PIN
from . import master_log

# Track the logical state of the light in software.
# False = OFF, True = ON
_LIGHT_STATE: bool = False

# Day/night configuration (in-memory for now)
# mode: "manual" = only change via API
#       "daynight" = follow time window when apply_daynight_now() is called
_LIGHT_MODE: str = "manual"
_DAY_START: dtime = dtime(19, 0)  # 19:00 (7 PM)
_DAY_END: dtime = dtime(7, 0)     # 07:00 (7 AM)


def _with_handle(fn):
    """
    Small helper: open / close the gpiochip around each operation.
    """
    def wrapper(*args, **kwargs):
        handle = lgpio.gpiochip_open(CHIP)
        try:
            return fn(handle, *args, **kwargs)
        finally:
            lgpio.gpiochip_close(handle)
    return wrapper


def _level_for_state(on: bool) -> int:
    """
    Map logical light state to the actual GPIO level.

    Relay is wired ACTIVE-LOW:
      - GPIO LOW (0)  -> light ON
      - GPIO HIGH (1) -> light OFF
    """
    return 0 if on else 1


def _parse_hhmm(value: str) -> dtime:
    """
    Parse a 'HH:MM' or 'HH:MM:SS' string into a time object.
    Raises ValueError on bad format.
    """
    parts = value.strip().split(":")
    if len(parts) < 2:
        raise ValueError("Time must be in HH:MM or HH:MM:SS format")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return dtime(hour, minute, second)


def _is_within_window(now: datetime) -> bool:
    """
    Return True if 'now' is within the configured [DAY_START, DAY_END) window.

    Supports both:
      - Normal window (start < end), e.g. 07:00 -> 19:00
      - Overnight window (start > end), e.g. 19:00 -> 07:00 next day
    """
    global _DAY_START, _DAY_END
    t = now.time()

    if _DAY_START < _DAY_END:
        # Same-day window
        return _DAY_START <= t < _DAY_END
    else:
        # Overnight window (e.g. 19:00–07:00)
        return not (_DAY_END <= t < _DAY_START)


@_with_handle
def set_light(handle: int, on: bool) -> Dict[str, Any]:
    """
    Turn the light ON or OFF by driving the relay pin.

    This updates both the physical GPIO and the in-memory state.
    """
    global _LIGHT_STATE

    level = _level_for_state(on)

    # Configure as output and drive the desired level immediately.
    lgpio.gpio_claim_output(handle, LIGHT_PIN, level)
    lgpio.gpio_write(handle, LIGHT_PIN, level)

    _LIGHT_STATE = on

    # Log to master.csv
    try:
        master_log.log_event(
            "light_state",
            source="light.set_light",
            light_on=on,
        )
    except Exception as e:
        print(f"[LOG] Failed to log light_state to master.csv: {e}")

    return {
        "light_pin": LIGHT_PIN,
        "on": _LIGHT_STATE,
    }


def get_light_state() -> Dict[str, Any]:
    """
    Return the last commanded state of the light WITHOUT touching hardware.

    This avoids changing the relay just by asking for its state.
    """
    return {
        "light_pin": LIGHT_PIN,
        "on": _LIGHT_STATE,
    }


@_with_handle
def toggle_light(handle: int) -> Dict[str, Any]:
    """
    Flip the light from ON→OFF or OFF→ON based on the in-memory state.
    """
    global _LIGHT_STATE

    new_state = not _LIGHT_STATE
    level = _level_for_state(new_state)

    lgpio.gpio_claim_output(handle, LIGHT_PIN, level)
    lgpio.gpio_write(handle, LIGHT_PIN, level)

    _LIGHT_STATE = new_state

    # Log to master.csv (optional separate event from direct set_light)
    try:
        master_log.log_event(
            "light_state",
            source="light.toggle_light",
            light_on=_LIGHT_STATE,
        )
    except Exception as e:
        print(f"[LOG] Failed to log light_state (toggle) to master.csv: {e}")

    return {
        "light_pin": LIGHT_PIN,
        "on": _LIGHT_STATE,
    }


def set_light_after_delay(on: bool, delay: float) -> None:
    """
    Sleep for `delay` seconds, then set the light state.

    Intended to be used from a FastAPI BackgroundTask so the API call
    returns immediately while this runs in a worker thread.
    """
    time.sleep(delay)
    set_light(on)


# ---------- Day/Night configuration & logic ----------


def get_light_config() -> Dict[str, Any]:
    """
    Return the current light mode + day/night window (as strings) plus state.
    """
    return {
        "mode": _LIGHT_MODE,
        "day_start": _DAY_START.strftime("%H:%M:%S"),
        "day_end": _DAY_END.strftime("%H:%M:%S"),
        "state": get_light_state(),
    }


def set_light_config(mode: str, day_start: str, day_end: str) -> Dict[str, Any]:
    """
    Update the light mode and day/night window.

    mode: "manual" or "daynight"
    day_start/day_end: "HH:MM" or "HH:MM:SS"
    """
    global _LIGHT_MODE, _DAY_START, _DAY_END

    mode = mode.lower()
    if mode not in ("manual", "daynight"):
        raise ValueError("mode must be 'manual' or 'daynight'")

    start_time = _parse_hhmm(day_start)
    end_time = _parse_hhmm(day_end)

    _LIGHT_MODE = mode
    _DAY_START = start_time
    _DAY_END = end_time

    # Log config change to master.csv
    try:
        master_log.log_event(
            "light_config_set",
            source="light.set_light_config",
            note=f"mode={mode}, day_start={day_start}, day_end={day_end}",
        )
    except Exception as e:
        print(f"[LOG] Failed to log light_config_set to master.csv: {e}")

    return get_light_config()


def apply_daynight_now() -> Dict[str, Any]:
    """
    Evaluate the day/night rule and, if mode == 'daynight', set the light
    ON/OFF accordingly based on the current time.

    Returns a summary dict with:
      - mode
      - applied (bool)
      - within_window (bool | None)
      - state (light state dict)
    """
    now = datetime.now().astimezone()
    if _LIGHT_MODE != "daynight":
        # Do nothing; just report current state
        return {
            "mode": _LIGHT_MODE,
            "applied": False,
            "within_window": None,
            "state": get_light_state(),
        }

    within = _is_within_window(now)
    result = set_light(within)

    # Log application to master.csv
    try:
        master_log.log_event(
            "light_daynight_apply",
            source="light.apply_daynight_now",
            light_on=result.get("on"),
            note=f"within_window={within}",
        )
    except Exception as e:
        print(f"[LOG] Failed to log light_daynight_apply to master.csv: {e}")

    return {
        "mode": _LIGHT_MODE,
        "applied": True,
        "within_window": within,
        "state": result,
    }
