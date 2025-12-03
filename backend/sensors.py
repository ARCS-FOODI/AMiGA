# backend/sensors.py
from __future__ import annotations

import time
import statistics
from typing import List, Dict, Any, Optional

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import lgpio

from .settings import (
    DEFAULT_ADDR,
    DEFAULT_GAIN,
    DEFAULT_AVG,
    DEFAULT_INTSEC,
    DEFAULT_DO_PIN,
    CHIP,
)


def open_digital_gpio(do_pin: int, chip: int = CHIP):
    try:
        h = lgpio.gpiochip_open(chip)
        lgpio.gpio_claim_input(h, do_pin)
        return h
    except Exception:
        return None


def close_digital_gpio(handle):
    if handle is None:
        return
    try:
        lgpio.gpiochip_close(handle)
    except Exception:
        pass


def read_do_state(handle, do_pin: int, invert: bool) -> Optional[str]:
    if handle is None:
        return None
    try:
        val = lgpio.gpio_read(handle, do_pin)
        if invert:
            val = 1 - val
        # Many HW-103 boards pull DO LOW when wet.
        return "WET" if val == 0 else "DRY"
    except Exception:
        return None


def init_ads(addr: int, gain: int):
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=addr)
    ads.gain = gain
    # Channels A0..A3
    chans = [AnalogIn(ads, ch) for ch in (0, 1, 2, 3)]
    return ads, chans


def read_four_channels(chans, avg: int) -> List[float]:
    voltages: List[float] = []
    n = max(1, avg)
    for ch in chans:
        vals = [ch.voltage for _ in range(n)]
        voltages.append(statistics.mean(vals))
    return voltages


def snapshot_sensors(
    addr: int = DEFAULT_ADDR,
    gain: int = DEFAULT_GAIN,
    samples: int = 1,
    interval: float = DEFAULT_INTSEC,
    avg: int = DEFAULT_AVG,
    use_digital: bool = False,
    do_pin: int = DEFAULT_DO_PIN,
    invert_do: bool = False,
) -> Dict[str, Any]:
    """
    Take one or more sensor snapshots and return structured data for the UI.

    NOTE: Voltage-only API:
      - readings[i]["voltages"] : list of 4 voltages
      - readings[i]["do_state"] : "WET"/"DRY"/None (if DO enabled)
    """
    _, chans = init_ads(addr, gain)
    handle = open_digital_gpio(do_pin) if use_digital else None
    readings: List[Dict[str, Any]] = []

    try:
        for i in range(1, samples + 1):
            volts = read_four_channels(chans, avg)
            do_state = read_do_state(handle, do_pin, invert_do)
            readings.append(
                {
                    "index": i,
                    "voltages": volts,
                    "do_state": do_state,
                    "timestamp": time.time(),
                }
            )
            if i < samples:
                time.sleep(interval)
    finally:
        close_digital_gpio(handle)

    return {
        "addr": addr,
        "gain": gain,
        "readings": readings,
    }
