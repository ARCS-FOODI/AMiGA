# backend/sis.py
import time
import random
import threading
from typing import Dict, Any
from .settings import DEFAULT_SIS_PORT, DEFAULT_SIS_SLAVE_ID, SIMULATE_GPIO

try:
    if not SIMULATE_GPIO:
        import minimalmodbus
    else:
        minimalmodbus = None
except ImportError:
    minimalmodbus = None

class SoilIntegratedSensor:
    def __init__(self, port: str = DEFAULT_SIS_PORT, slave_id: int = DEFAULT_SIS_SLAVE_ID):
        self.port = port
        self.slave_id = slave_id
        self.instrument = None
        self._lock = threading.Lock()
        
        if not SIMULATE_GPIO and minimalmodbus:
            try:
                self.instrument = minimalmodbus.Instrument(self.port, self.slave_id)
                self.instrument.serial.baudrate = 9600
                self.instrument.serial.timeout = 1
            except Exception as e:
                print(f"[SIS] Hardware init failed: {e}")

    def read_data(self) -> Dict[str, Any]:
        if SIMULATE_GPIO:
            # Simulate realistic values
            return {
                "ph": round(random.uniform(5.5, 7.5), 2),
                "moisture": round(random.uniform(20.0, 80.0), 1),
                "temperature": round(random.uniform(18.0, 28.0), 1),
                "ec": random.randint(200, 1500),
                "nitrogen": random.randint(10, 50),
                "phosphorus": random.randint(5, 30),
                "potassium": random.randint(40, 200),
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "simulated": True
            }

        if not self.instrument:
            raise RuntimeError("SIS Hardware not initialized (check PORT and SLAVE_ID)")

        with self._lock:
            try:
                # Read registers as per test_npk_sensor.py
                ph = self.instrument.read_register(6, functioncode=3) / 100.0
                moisture = self.instrument.read_register(18, functioncode=3) / 10.0
                temperature = self.instrument.read_register(19, functioncode=3, signed=True) / 10.0
                ec = self.instrument.read_register(21, functioncode=3)
                nitrogen = self.instrument.read_register(30, functioncode=3)
                phosphorus = self.instrument.read_register(31, functioncode=3)
                potassium = self.instrument.read_register(32, functioncode=3)
                ts = time.strftime('%Y-%m-%d %H:%M:%S')

                data = {
                    "ph": ph,
                    "moisture": moisture,
                    "temperature": temperature,
                    "ec": ec,
                    "nitrogen": nitrogen,
                    "phosphorus": phosphorus,
                    "potassium": potassium,
                    "timestamp": ts,
                    "simulated": False
                }

                return data

            except Exception as e:
                raise RuntimeError(f"Failed to read SIS sensor: {e}")

# Global singleton
manager = SoilIntegratedSensor()

def snapshot_sis(port: str = None, slave_id: int = None) -> Dict[str, Any]:
    # Use provided or default
    p = port or manager.port
    s = slave_id or manager.slave_id
    
    # If different from manager, create temporary instance or re-init?
    # For now, simplest path:
    if p != manager.port or s != manager.slave_id:
        temp_sensor = SoilIntegratedSensor(port=p, slave_id=s)
        return temp_sensor.read_data()
    
    return manager.read_data()
