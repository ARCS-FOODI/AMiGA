# backend/sensors.py
from __future__ import annotations

import time
import statistics
import threading
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
from . import master_log

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

    board = type("board", (), {"SCL": 1, "SDA": 2})
    busio = type("busio", (), {"I2C": MockI2C})
    ADS = type("ADS", (), {"ADS1115": MockADS})
    AnalogIn = MockAnalogIn
    lgpio = MockLgpio()


class SensorArray:
    """
    Object-Oriented representation of a single ADS1115 Sensor Array.
    Manages the connection to a specific I2C address.
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
        
        self._ads = None
        self._chans = []
        self._handle = None
        self._lock = threading.Lock()

    def initialize(self, i2c_bus, handle: int = None, use_digital: bool = False) -> None:
        """Initialize the ADC at this specific address and optionally the DO pin."""
        with self._lock:
            # Init ADS1115 on the provided I2C bus
            if not self._ads:
                try:
                    self._ads = ADS.ADS1115(i2c_bus, address=self.addr)
                    self._ads.gain = self.gain
                    self._chans = [AnalogIn(self._ads, ch) for ch in (0, 1, 2, 3)]
                except Exception as e:
                    print(f"[ERROR] Failed to initialize ADC at {hex(self.addr)}: {e}")
                    raise

            # Init DO pin if requested
            if use_digital and handle is not None:
                self._handle = handle
                lgpio.gpio_claim_input(self._handle, self.do_pin)

    def _read_analog_channels(self, avg: int) -> List[float]:
        voltages: List[float] = []
        n = max(1, avg)
        for ch in self._chans:
            vals = [ch.voltage for _ in range(n)]
            voltages.append(statistics.mean(vals))
        return voltages

    def _read_digital_state(self, invert: bool) -> Optional[str]:
        if self._handle is None:
            return None
        try:
            val = lgpio.gpio_read(self._handle, self.do_pin)
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
    ) -> Dict[str, Any]:
        """Take one or more sensor snapshots."""
        if not self._chans:
            raise RuntimeError(f"SensorArray at {hex(self.addr)} is not initialized.")

        readings: List[Dict[str, Any]] = []

        with self._lock:
            for i in range(1, samples + 1):
                volts = self._read_analog_channels(avg)
                do_state = self._read_digital_state(invert_do)
                ts = datetime.now().astimezone().isoformat()

                readings.append(
                    {
                        "index": i,
                        "voltages": volts,
                        "do_state": do_state,
                        "timestamp": ts,
                    }
                )

                try:
                    master_log.log_event(
                        "sensor_read",
                        source="SensorArray.snapshot",
                        addr=self.addr,
                        gain=self.gain,
                        avg=avg,
                        sample_index=i,
                        v0=volts[0],
                        v1=volts[1],
                        v2=volts[2],
                        v3=volts[3],
                        do_state=do_state,
                        timestamp=ts,
                    )
                except Exception as e:
                    print(f"[LOG] Failed to log sensor_read: {e}")

                if i < samples:
                    time.sleep(interval)

        return {
            "addr": self.addr,
            "gain": self.gain,
            "readings": readings,
        }


class SensorManager:
    """Global manager for multiple sensor hardware arrays."""
    def __init__(self, chip_index: int = CHIP):
        self.chip_index = chip_index
        self._handle = None
        self._i2c = None
        self._arrays: Dict[int, SensorArray] = {}
        self._lock = threading.Lock()

    def startup(self) -> None:
        """Open common I2C bus and GPIO chip."""
        with self._lock:
            if not self._i2c:
                self._i2c = busio.I2C(board.SCL, board.SDA)
            if not self._handle:
                self._handle = lgpio.gpiochip_open(self.chip_index)

    def get_array(self, addr: int, do_pin: int = DEFAULT_DO_PIN, use_digital: bool = True) -> SensorArray:
        """Get or create a SensorArray for a specific address."""
        self.startup()
        with self._lock:
            if addr not in self._arrays:
                print(f"[SENSORS] Initializing new sensor array at {hex(addr)}")
                new_array = SensorArray(addr=addr, do_pin=do_pin, chip=self.chip_index)
                new_array.initialize(self._i2c, self._handle, use_digital=use_digital)
                self._arrays[addr] = new_array
            return self._arrays[addr]

    def shutdown(self) -> None:
        """Release the GPIO chip and clear arrays."""
        with self._lock:
            if self._handle is not None:
                lgpio.gpiochip_close(self._handle)
                self._handle = None
            self._arrays.clear()
            self._i2c = None


# Global singleton
manager = SensorManager()

# --- Legacy Procedural Wrappers ---
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
    
    # Get the array for the specific address
    array = manager.get_array(addr, do_pin=do_pin, use_digital=use_digital)
    
    # Update temporary runtime settings
    array.gain = gain
    if array._ads:
        array._ads.gain = gain
        
    return array.snapshot(
        samples=samples,
        interval=interval,
        avg=avg,
        invert_do=invert_do
    )
