# backend/scd41.py
from __future__ import annotations

import time
import random
import threading
from typing import Dict, Any, Optional
from datetime import datetime

from .settings import SIMULATE_GPIO

if not SIMULATE_GPIO:
    import board
    import busio
    import adafruit_scd4x
else:
    class MockSCD4X:
        def __init__(self, i2c):
            self.CO2 = 400
            self.temperature = 25.0
            self.relative_humidity = 50.0

        def start_periodic_measurement(self):
            pass

        def stop_periodic_measurement(self):
            pass

        @property
        def data_ready(self) -> bool:
            return True

        def update_mock_data(self):
            self.CO2 = int(max(400, min(2000, self.CO2 + random.uniform(-10, 10))))
            self.temperature = max(10.0, min(40.0, self.temperature + random.uniform(-0.5, 0.5)))
            self.relative_humidity = max(20.0, min(80.0, self.relative_humidity + random.uniform(-1.0, 1.0)))

    # Mocking hardware dependencies for Windows/macOS development
    board = type("board", (), {"SCL": 1, "SDA": 2})
    busio = type("busio", (), {"I2C": lambda *a, **k: None})
    adafruit_scd4x = type("adafruit_scd4x", (), {"SCD4X": MockSCD4X})

class SCD41Sensor:
    """
    Manages the connection to the Sensirion SCD41 CO2 sensor over I2C.
    Handles startup, periodic measurement lifecycle, and simulation generation.
    """
    def __init__(self):
        self._i2c = None
        self._sensor = None
        self._lock = threading.Lock()

    def startup(self) -> None:
        """Initialize the I2C connection and start the sensor's periodic measurement."""
        with self._lock:
            if not self._i2c:
                try:
                    self._i2c = busio.I2C(board.SCL, board.SDA)
                    self._sensor = adafruit_scd4x.SCD4X(self._i2c)
                    self._sensor.start_periodic_measurement()
                except Exception as e:
                    print(f"[SCD41] Hardware init failed: {e}")

    def shutdown(self) -> None:
        """Stop periodic measurement and clean up."""
        with self._lock:
            if self._sensor:
                try:
                    self._sensor.stop_periodic_measurement()
                except Exception:
                    pass
            self._sensor = None
            self._i2c = None

    def read_data(self) -> Dict[str, Any]:
        """Read latest CO2, temperature, and humidity data from the SCD41 sensor."""
        ts = datetime.now().astimezone().isoformat()

        if SIMULATE_GPIO:
            if self._sensor:
                self._sensor.update_mock_data()
                co2 = self._sensor.CO2
                temp = round(self._sensor.temperature, 2)
                rh = round(self._sensor.relative_humidity, 2)
            else:
                co2 = random.randint(400, 800)
                temp = round(random.uniform(20.0, 30.0), 2)
                rh = round(random.uniform(40.0, 60.0), 2)

            return {
                "co2": co2,
                "temperature": temp,
                "humidity": rh,
                "timestamp": ts,
                "simulated": True
            }

        if not self._sensor:
            # Try to auto-initialize if not done yet
            self.startup()
            if not self._sensor:
                raise RuntimeError("SCD41 Hardware not initialized")

        try:
            with self._lock:
                if self._sensor.data_ready:
                    co2 = self._sensor.CO2
                    temp = self._sensor.temperature
                    rh = self._sensor.relative_humidity
                else:
                    # Return whatever was last buffered by the circuitpython library
                    co2 = self._sensor.CO2
                    temp = self._sensor.temperature
                    rh = self._sensor.relative_humidity

            data = {
                "co2": co2,
                "temperature": round(temp, 2) if temp is not None else None,
                "humidity": round(rh, 2) if rh is not None else None,
                "timestamp": ts,
                "simulated": False
            }
            return data

        except Exception as e:
            raise RuntimeError(f"Failed to read SCD41 sensor: {e}")

# Global singleton
manager = SCD41Sensor()

def snapshot_scd41() -> Dict[str, Any]:
    return manager.read_data()
