# backend/tsl2561.py
from __future__ import annotations

import time
import random
import threading
from typing import Dict, Any, Optional
from datetime import datetime

from .settings import SIMULATE_GPIO
from . import master_log

if not SIMULATE_GPIO:
    import board
    import busio
    import adafruit_tsl2561
else:
    class MockTSL2561:
        def __init__(self, i2c):
            self._broadband = 500
            self._infrared = 150
            self._lux = 250
            
        @property
        def broadband(self):
            return self._broadband
            
        @property
        def infrared(self):
            return self._infrared
            
        @property
        def lux(self):
            return self._lux

        def update_mock_data(self):
            self._broadband = int(max(0, min(65535, self._broadband + random.uniform(-20, 20))))
            self._infrared = int(max(0, min(65535, self._infrared + random.uniform(-10, 10))))
            # Lux is derived from the other two usually, we just mock some fluctuation
            self._lux = int(max(0, min(2000, self._lux + random.uniform(-5, 5))))

    # Mocking hardware dependencies for Windows/macOS development
    board = type("board", (), {"I2C": lambda *a, **k: None})
    busio = type("busio", (), {"I2C": lambda *a, **k: None})
    adafruit_tsl2561 = type("adafruit_tsl2561", (), {"TSL2561": MockTSL2561})

class TSL2561Sensor:
    """
    Manages the connection to the Sensirion TSL2561 Luminosity sensor over I2C.
    Handles startup, reading, and simulation generation.
    """
    def __init__(self):
        self._i2c = None
        self._sensor = None
        self._lock = threading.Lock()

    def startup(self) -> None:
        """Initialize the I2C connection to TSL2561."""
        with self._lock:
            if not self._i2c:
                try:
                    self._i2c = board.I2C()
                    self._sensor = adafruit_tsl2561.TSL2561(self._i2c)
                    # Optional: enable features or set gain/integration time
                    # self._sensor.enabled = True
                    # self._sensor.gain = 0
                    # self._sensor.integration_time = 1
                except Exception as e:
                    print(f"[TSL2561] Hardware init failed: {e}")

    def shutdown(self) -> None:
        """Clean up."""
        with self._lock:
            if self._sensor:
                # Optionally set enabled to False to save power
                # try: self._sensor.enabled = False; except: pass
                pass
            self._sensor = None
            self._i2c = None

    def read_data(self) -> Dict[str, Any]:
        """Read broadband light, infrared light, and lux from the TSL2561 sensor."""
        ts = datetime.now().astimezone().isoformat()

        if SIMULATE_GPIO:
            if self._sensor:
                self._sensor.update_mock_data()
                broadband = self._sensor.broadband
                infrared = self._sensor.infrared
                lux = self._sensor.lux
            else:
                broadband = random.randint(300, 800)
                infrared = random.randint(100, 250)
                lux = random.randint(150, 400)

            return {
                "broadband": broadband,
                "infrared": infrared,
                "lux": lux,
                "timestamp": ts,
                "simulated": True
            }

        if not self._sensor:
            # Try to auto-initialize if not done yet
            self.startup()
            if not self._sensor:
                raise RuntimeError("TSL2561 Hardware not initialized")

        try:
            with self._lock:
                broadband = self._sensor.broadband
                infrared = self._sensor.infrared
                lux = self._sensor.lux

            data = {
                "broadband": broadband,
                "infrared": infrared,
                "lux": lux,
                "timestamp": ts,
                "simulated": False
            }

            try:
                master_log.log_event(
                    "tsl2561_read",
                    source="TSL2561Sensor.read_data",
                    **data
                )
            except Exception as e:
                print(f"[LOG] Failed to log tsl2561_read: {e}")

            return data

        except Exception as e:
            raise RuntimeError(f"Failed to read TSL2561 sensor: {e}")

# Global singleton
manager = TSL2561Sensor()

def snapshot_tsl2561() -> Dict[str, Any]:
    return manager.read_data()
