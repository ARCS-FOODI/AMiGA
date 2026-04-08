# backend/sensors.py
from __future__ import annotations

import time
import statistics
import threading
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .settings import (
    DEFAULT_ADDR,
    DEFAULT_GAIN,
    DEFAULT_AVG,
    DEFAULT_INTSEC,
    DEFAULT_DO_PIN,
    CHIP,
    SIMULATE_GPIO,
)

LOG_FILE = Path(__file__).resolve().parents[1] / "data" / "sensors.csv"

def _log_sensor_data_wide(device_name: str, ts: str, addr: int, v0: float, v1: float, v2: float, v3: float) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_exists = LOG_FILE.exists()
        with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "device_name", "addr", "v0", "v1", "v2", "v3"])
            writer.writerow([ts, device_name, addr, round(v0, 4), round(v1, 4), round(v2, 4), round(v3, 4)])
    except Exception as e:
        print(f"[LOG] Failed to write to {LOG_FILE.name}: {e}")


if not SIMULATE_GPIO:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    import lgpio
else:
    import random
    class MockI2C:
        def __init__(self, *args, **kwargs): pass
    class MockADS: 
        def __init__(self, *args, **kwargs): self.gain = 1
    class MockAnalogIn:
        def __init__(self, ads, chan):
            self._voltage = random.uniform(0.5, 3.2)
        @property
        def voltage(self):
            # random sensor jitter
            self._voltage += random.uniform(-0.15, 0.15)
            self._voltage = max(0.0, min(self._voltage, 3.3))
            return self._voltage
    class MockLgpio:
        def gpiochip_open(self, chip): return 999
        def gpiochip_close(self, handle): pass
        def gpio_claim_input(self, handle, pin): pass
        def gpio_read(self, handle, pin): return 1 # 1 = Dry

    board = type("board", (), {"SCL": 1, "SDA": 2, "I2C": lambda *a, **k: None})
    busio = type("busio", (), {"I2C": MockI2C})
    ADS = type("ADS", (), {"ADS1115": MockADS})
    AnalogIn = MockAnalogIn
    lgpio = MockLgpio()


class SensorArray:
    """
    Object-Oriented representation of the Sensor Array.
    Manages the I2C ADC connection and optional Digital Out (DO) pin.
    """
    def __init__(
        self, 
        addr: int = DEFAULT_ADDR, 
        gain: float = DEFAULT_GAIN, 
        do_pin: int = DEFAULT_DO_PIN,
        chip: int = CHIP
    ):
        self.addr = addr
        self.gain = gain
        self.do_pin = do_pin
        self.chip = chip
        
        self._i2c = None
        self._ads_dict = {}
        self._chans_dict = {}
        
        self._handle = None
        self._lock = threading.Lock()

    def initialize(self, handle: int = None, use_digital: bool = False) -> None:
        """Initialize the I2C connection to the ADC and optionally the DO pin."""
        with self._lock:
            # Init I2C ADC
            if not self._i2c:
                self._i2c = board.I2C()

            # Init DO pin if requested
            if use_digital and handle is not None:
                self._handle = handle
                lgpio.gpio_claim_input(self._handle, self.do_pin)

    def _ensure_adc(self, addr, gain):
        if not self._i2c:
            self._i2c = board.I2C()
        if addr not in self._ads_dict:
            ads = ADS.ADS1115(self._i2c, address=addr)
            ads.gain = gain
            self._ads_dict[addr] = ads
            self._chans_dict[addr] = [AnalogIn(ads, ch) for ch in (0, 1, 2, 3)]
        else:
            self._ads_dict[addr].gain = gain

    def _read_analog_channels(self, addr, avg: int) -> List[float]:
        voltages: List[float] = []
        n = max(1, avg)
        for ch in self._chans_dict[addr]:
            vals = [ch.voltage for _ in range(n)]
            voltages.append(statistics.mean(vals))
        return voltages

    def _read_digital_state(self, do_pin, invert: bool) -> Optional[str]:
        if self._handle is None:
            return None
        try:
            val = lgpio.gpio_read(self._handle, do_pin)
            if invert:
                val = 1 - val
            return "WET" if val == 0 else "DRY"
        except Exception:
            return None

    def snapshot(
        self,
        samples: int = 1,
        interval: float = DEFAULT_INTSEC,
        avg: int = DEFAULT_AVG,
        invert_do: bool = False,
        addr: int = None,
        gain: float = None,
        do_pin: int = None,
    ) -> Dict[str, Any]:
        """Take one or more sensor snapshots."""
        if not self._i2c:
            self.initialize()

        readings: List[Dict[str, Any]] = []

        with self._lock:
            req_addr = addr if addr is not None else self.addr
            req_gain = gain if gain is not None else self.gain
            req_do_pin = do_pin if do_pin is not None else self.do_pin
            
            self._ensure_adc(req_addr, req_gain)
            for i in range(1, samples + 1):
                volts = self._read_analog_channels(req_addr, avg)
                do_state = self._read_digital_state(req_do_pin, invert_do)
                ts = datetime.now().astimezone().isoformat()

                readings.append(
                    {
                        "index": i,
                        "voltages": volts,
                        "do_state": do_state,
                        "timestamp": ts,
                    }
                )

                _log_sensor_data_wide(
                    device_name="ads1115_array",
                    ts=ts,
                    addr=req_addr,
                    v0=volts[0],
                    v1=volts[1],
                    v2=volts[2],
                    v3=volts[3]
                )

                if i < samples:
                    time.sleep(interval)

        return {
            "addr": req_addr,
            "gain": req_gain,
            "readings": readings,
        }


class SensorManager:
    """Global manager for sensor hardware."""
    def __init__(self, chip_index: int = CHIP):
        self.chip_index = chip_index
        self._handle = None
        self.main_array = SensorArray(chip=self.chip_index)

    def startup(self, use_digital: bool = True) -> None:
        """Open GPIO chip for digital pins and initialize I2C."""
        self._handle = lgpio.gpiochip_open(self.chip_index)
        self.main_array.initialize(self._handle, use_digital=use_digital)

    def shutdown(self) -> None:
        """Release the GPIO chip."""
        if self._handle is not None:
            lgpio.gpiochip_close(self._handle)
            self._handle = None
            self.main_array._handle = None


# Global singleton
manager = SensorManager()

# --- Legacy Procedural Wrappers ---
def _ensure_manager(use_digital: bool = False):
    if manager._handle is None:
        manager.startup(use_digital=use_digital)

def snapshot_sensors(
    addr: int = DEFAULT_ADDR,
    gain: float = DEFAULT_GAIN,
    samples: int = 1,
    interval: float = DEFAULT_INTSEC,
    avg: int = DEFAULT_AVG,
    use_digital: bool = False,
    do_pin: int = DEFAULT_DO_PIN,
    invert_do: bool = False,
) -> Dict[str, Any]:
    
    _ensure_manager(use_digital)
    
    return manager.main_array.snapshot(
        samples=samples,
        interval=interval,
        avg=avg,
        invert_do=invert_do,
        addr=addr,
        gain=gain,
        do_pin=do_pin
    )
