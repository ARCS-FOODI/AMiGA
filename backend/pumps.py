# backend/pumps.py
from __future__ import annotations

import time
from typing import Dict, Any

import lgpio

from .settings import PUMP_PINS, CHIP, DEFAULT_HZ, DEFAULT_DIR
from . import config_store, master_log


def gpio_setup_outputs(handle: int) -> None:
    """
    Claim outputs for all defined pumps and set safe defaults
    (EN HIGH = disabled, STEP=0, DIR=0).
    """
    for pins in PUMP_PINS.values():
        lgpio.gpio_claim_output(handle, pins["STEP"], 0)
        lgpio.gpio_claim_output(handle, pins["DIR"],  0)
        lgpio.gpio_claim_output(handle, pins["EN"],   1)


def set_direction(handle: int, pump: str, dir_name: str) -> None:
    pins = PUMP_PINS[pump]
    name = dir_name.lower()
    if name in ("fwd", "forward", "cw"):
        lgpio.gpio_write(handle, pins["DIR"], 1)
    elif name in ("rev", "reverse", "ccw", "back"):
        lgpio.gpio_write(handle, pins["DIR"], 0)
    else:
        raise ValueError("dir must be 'forward' or 'reverse'")


def enable_driver(handle: int, pump: str, enable: bool) -> None:
    pins = PUMP_PINS[pump]
    lgpio.gpio_write(handle, pins["EN"], 0 if enable else 1)


def step_for_seconds(handle: int, pump: str, hz: float, seconds: float) -> None:
    if hz <= 0:
        raise ValueError("hz must be > 0")
    if seconds <= 0:
        return
    pins = PUMP_PINS[pump]
    sp = pins["STEP"]
    half = 1.0 / (hz * 2.0)
    end_time = time.time() + seconds
    write = lgpio.gpio_write
    while time.time() < end_time:
        write(handle, sp, 1); time.sleep(half)
        write(handle, sp, 0); time.sleep(half)


def step_for_seconds_multi(handle: int, pump_names: list[str], hz: float, seconds: float) -> None:
    if hz <= 0:
        raise ValueError("hz must be > 0")
    if seconds <= 0:
        return

    half = 1.0 / (hz * 2.0)
    end_time = time.time() + seconds
    write = lgpio.gpio_write

    # Cache STEP pins for all pumps
    step_pins = [PUMP_PINS[p]["STEP"] for p in pump_names]

    while time.time() < end_time:
        # rising edge on all STEP pins
        for sp in step_pins:
            write(handle, sp, 1)
        time.sleep(half)

        # falling edge on all STEP pins
        for sp in step_pins:
            write(handle, sp, 0)
        time.sleep(half)


def _with_handle(fn):
    """
    Small helper to open/close gpiochip0 around an operation.
    """

    def wrapper(*args, **kwargs):
        h = lgpio.gpiochip_open(CHIP)
        try:
            gpio_setup_outputs(h)
            return fn(h, *args, **kwargs)
        finally:
            # safety: disable all pumps and close
            try:
                for pump_name in PUMP_PINS.keys():
                    try:
                        enable_driver(h, pump_name, False)
                    except Exception:
                        pass
            except Exception:
                pass
            lgpio.gpiochip_close(h)

    return wrapper


@_with_handle
def run_pump_seconds(
    handle: int,
    pump: str,
    seconds: float,
    hz: float = DEFAULT_HZ,
    direction: str = DEFAULT_DIR,
) -> Dict[str, Any]:
    set_direction(handle, pump, direction)
    enable_driver(handle, pump, True)
    try:
        step_for_seconds(handle, pump, hz, seconds)
    finally:
        enable_driver(handle, pump, False)

    result = {
        "pump": pump,
        "seconds": seconds,
        "hz": hz,
        "direction": direction,
        "status": "ok",
    }

    # Log to master.csv
    try:
        master_log.log_event(
            "pump_run_seconds",
            source="pumps.run_pump_seconds",
            pump=pump,
            seconds=seconds,
            hz=hz,
            direction=direction,
        )
    except Exception as e:
        print(f"[LOG] Failed to log pump_run_seconds to master.csv: {e}")

    return result


@_with_handle
def run_pumps_seconds(
    handle: int,
    pumps_list: list[str],
    seconds: float,
    hz: float = DEFAULT_HZ,
    direction: str = DEFAULT_DIR,
) -> Dict[str, Any]:
    """
    Run multiple pumps simultaneously for the same duration and frequency.
    """
    # Set direction + enable all requested pumps
    for pump in pumps_list:
        set_direction(handle, pump, direction)
        enable_driver(handle, pump, True)

    try:
        step_for_seconds_multi(handle, pumps_list, hz, seconds)
    finally:
        for pump in pumps_list:
            enable_driver(handle, pump, False)

    result = {
        "pumps": pumps_list,
        "seconds": seconds,
        "hz": hz,
        "direction": direction,
        "status": "ok",
    }

    # Log to master.csv
    try:
        master_log.log_event(
            "pump_run_multi_seconds",
            source="pumps.run_pumps_seconds",
            pumps=",".join(pumps_list),
            seconds=seconds,
            hz=hz,
            direction=direction,
        )
    except Exception as e:
        print(f"[LOG] Failed to log pump_run_multi_seconds to master.csv: {e}")

    return result


@_with_handle
def calibrate_pump_seconds(
    handle: int,
    pump: str,
    run_seconds: float,
    hz: float = DEFAULT_HZ,
) -> Dict[str, Any]:
    """
    Run the pump for a fixed time to allow measuring mL/s externally.
    """
    set_direction(handle, pump, DEFAULT_DIR)
    enable_driver(handle, pump, True)
    try:
        step_for_seconds(handle, pump, hz, run_seconds)
    finally:
        enable_driver(handle, pump, False)

    result = {
        "pump": pump,
        "run_seconds": run_seconds,
        "hz": hz,
        "message": (
            f"Calibration run complete. Measure mL in your cylinder, then "
            f"POST the measured ml_per_sec to /pump/calibration for '{pump}'."
        ),
    }

    # Log to master.csv
    try:
        master_log.log_event(
            "pump_calibration_run",
            source="pumps.calibrate_pump_seconds",
            pump=pump,
            seconds=run_seconds,
            hz=hz,
        )
    except Exception as e:
        print(f"[LOG] Failed to log pump_calibration_run to master.csv: {e}")

    return result


@_with_handle
def run_pump_ml(
    handle: int,
    pump: str,
    ml: float,
    hz: float = DEFAULT_HZ,
    direction: str = DEFAULT_DIR,
) -> Dict[str, Any]:
    """
    Run pump based on target volume, using JSON calibration (ml/s).
    """
    rate = config_store.get_pump_calibration(pump) or 0.0
    if rate <= 0.0:
        raise RuntimeError(
            f"Pump '{pump}' has ml_per_sec=0. Set calibration via /pump/calibration first."
        )

    seconds = ml / rate
    set_direction(handle, pump, direction)
    enable_driver(handle, pump, True)
    try:
        step_for_seconds(handle, pump, hz, seconds)
    finally:
        enable_driver(handle, pump, False)

    result = {
        "pump": pump,
        "ml": ml,
        "hz": hz,
        "direction": direction,
        "rate_ml_per_sec": rate,
        "seconds": seconds,
        "status": "ok",
    }

    # Log to master.csv
    try:
        master_log.log_event(
            "pump_run_ml",
            source="pumps.run_pump_ml",
            pump=pump,
            ml=ml,
            seconds=seconds,
            hz=hz,
            direction=direction,
            note=f"rate_ml_per_sec={rate}",
        )
    except Exception as e:
        print(f"[LOG] Failed to log pump_run_ml to master.csv: {e}")

    return result
