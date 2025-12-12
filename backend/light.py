# backend/light.py
from __future__ import annotations

from typing import Dict, Any
import time

import lgpio

from .settings import CHIP, LIGHT_PIN
from . import master_log

# Track the logical state of the light in software.
# False = OFF, True = ON
_LIGHT_STATE: bool = False


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
