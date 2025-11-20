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
    DEFAULT_DRY_V,
    DEFAULT_WET_V,
    DEFAULT_THRESH,
    DEFAULT_DO_PIN,
    CHIP,
)


def v_to_pct(v: float, dry_v: float, wet_v: float) -> float:
    """Map voltage to 0–100% (dry→0, wet→100)."""
    if dry_v == wet_v:
        return 0.0
    pct = (dry_v - v) / (dry_v - wet_v) * 100.0
    return max(0.0, min(100.0, pct))


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
    dry_v: float = DEFAULT_DRY_V,
    wet_v: float = DEFAULT_WET_V,
    thresh_pct: float = DEFAULT_THRESH,
    use_digital: bool = False,
    do_pin: int = DEFAULT_DO_PIN,
    invert_do: bool = False,
) -> Dict[str, Any]:
    """
    Take one or more sensor snapshots and return structured data for the UI.
    """
    _, chans = init_ads(addr, gain)
    handle = open_digital_gpio(do_pin) if use_digital else None
    readings: List[Dict[str, Any]] = []
    try:
        for i in range(1, samples + 1):
            volts = read_four_channels(chans, avg)
            pcts = [v_to_pct(v, dry_v, wet_v) for v in volts]
            do_state = read_do_state(handle, do_pin, invert_do)
            readings.append({
                "index": i,
                "voltages": volts,
                "moisture_pct": pcts,
                "do_state": do_state,
                "timestamp": time.time(),
            })
            if i < samples:
                time.sleep(interval)
    finally:
        close_digital_gpio(handle)

    return {
        "addr": addr,
        "gain": gain,
        "dry_v": dry_v,
        "wet_v": wet_v,
        "thresh_pct": thresh_pct,
        "readings": readings,
    }
