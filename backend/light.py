# backend/light.py
from __future__ import annotations

from typing import Dict, Any

import lgpio

from .settings import CHIP, LIGHT_PIN


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


@_with_handle
def set_light(handle: int, on: bool) -> Dict[str, Any]:
    """
    Turn the light ON or OFF by driving the relay pin high/low.
    """
    # configure as output and set initial level
    lgpio.gpio_claim_output(handle, LIGHT_PIN, 0)
    lgpio.gpio_write(handle, LIGHT_PIN, 1 if on else 0)

    return {
        "light_pin": LIGHT_PIN,
        "on": on,
    }


@_with_handle
def get_light_state(handle: int) -> Dict[str, Any]:
    """
    Read the current state of the light (relay output).
    """
    # we can read the level on the pin even if it is configured as output
    lgpio.gpio_claim_input(handle, LIGHT_PIN)
    value = lgpio.gpio_read(handle, LIGHT_PIN)

    return {
        "light_pin": LIGHT_PIN,
        "on": bool(value),
    }


@_with_handle
def toggle_light(handle: int) -> Dict[str, Any]:
    """
    Flip the light from ON→OFF or OFF→ON and return the new state.
    """
    # read current value
    lgpio.gpio_claim_input(handle, LIGHT_PIN)
    current = lgpio.gpio_read(handle, LIGHT_PIN)

    # switch to output and write the opposite level
    lgpio.gpio_claim_output(handle, LIGHT_PIN, current)
    new_value = 0 if current else 1
    lgpio.gpio_write(handle, LIGHT_PIN, new_value)

    return {
        "light_pin": LIGHT_PIN,
        "on": bool(new_value),
    }
