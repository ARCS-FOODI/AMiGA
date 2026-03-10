# backend/npk_sensor.py
"""
NPK Soil Sensor Manager Module
Manages 7-in-1 NPK soil sensor communication via Modbus protocol
Reads: pH, Moisture, Temperature, EC, Nitrogen, Phosphorus, Potassium
"""

from __future__ import annotations

import time
import threading
import random
from typing import Optional, Dict, Any
from datetime import datetime

from .settings import SIMULATE

if not SIMULATE:
    try:
        import minimalmodbus
    except ImportError:
        minimalmodbus = None
else:
    minimalmodbus = None
    
    class MockModbusInstrument:
        """Mock Modbus instrument for simulation/testing"""
        def __init__(self, port: str, slave_id: int):
            self.port = port
            self.slave_id = slave_id
            # Simulate realistic soil sensor data
            self._base_values = {
                6: 680,      # pH * 100 = 6.8
                18: 550,     # Moisture * 10 = 55%
                19: 220,     # Temperature * 10 = 22°C
                21: 850,     # EC = 850 µs/cm
                30: 180,     # Nitrogen = 180 mg/kg
                31: 45,      # Phosphorus = 45 mg/kg
                32: 200,     # Potassium = 200 mg/kg
            }
            # Variability for each parameter (jitter)
            self._jitter = {
                6: 10,       # pH ±0.1
                18: 30,      # Moisture ±3%
                19: 20,      # Temperature ±2°C
                21: 100,     # EC ±100
                30: 20,      # Nitrogen ±20
                31: 5,       # Phosphorus ±5
                32: 30,      # Potassium ±30
            }
        
        def read_register(self, register: int, functioncode: int = 3, signed: bool = False) -> int:
            """Simulate reading a Modbus register with realistic jitter"""
            if register not in self._base_values:
                raise ValueError(f"Unknown register: {register}")
            
            base = self._base_values[register]
            jitter = random.uniform(-self._jitter[register], self._jitter[register])
            value = int(base + jitter)
            
            # Clamp to reasonable ranges
            if register == 6:  # pH
                value = max(400, min(1000, value))  # 4.0 - 10.0
            elif register == 18:  # Moisture
                value = max(0, min(1000, value))    # 0% - 100%
            elif register == 19:  # Temperature
                if signed and value > 32767:
                    value -= 65536
                value = max(-200, min(600, value))  # -20°C to 60°C
            elif register == 21:  # EC
                value = max(0, min(10000, value))   # 0 - 10000 µs/cm
            else:  # NPK values
                value = max(0, min(2000, value))    # 0 - 2000 mg/kg
            
            return value


class NPKSensor:
    """
    Interface for 7-in-1 NPK soil sensor via Modbus
    Handles serial communication and register reading
    """
    
    # Register addresses for sensor parameters
    REGISTER_MAP = {
        'ph': 6,
        'moisture': 18,
        'temperature': 19,
        'ec': 21,
        'nitrogen': 30,
        'phosphorus': 31,
        'potassium': 32,
    }
    
    # Scaling factors for each parameter
    SCALES = {
        'ph': 100.0,
        'moisture': 10.0,
        'temperature': 10.0,
        'ec': 1.0,
        'nitrogen': 1.0,
        'phosphorus': 1.0,
        'potassium': 1.0,
    }
    
    # Whether temperature register is signed
    SIGNED = {
        'ph': False,
        'moisture': False,
        'temperature': True,
        'ec': False,
        'nitrogen': False,
        'phosphorus': False,
        'potassium': False,
    }
    
    def __init__(
        self,
        port: str = '/dev/ttyUSB0',
        slave_id: int = 1,
        baudrate: int = 9600,
        timeout: float = 1.0
    ):
        """
        Initialize NPK sensor connection
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' or 'COM3')
            slave_id: Modbus slave address (1-247)
            baudrate: Serial baudrate (typically 9600)
            timeout: Serial timeout in seconds
        """
        self.port = port
        self.slave_id = slave_id
        self.baudrate = baudrate
        self.timeout = timeout
        
        self.instrument: Optional[minimalmodbus.Instrument] = None
        self._lock = threading.Lock()
        self._connected = False
        self._last_error: Optional[str] = None
        
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """Initialize Modbus connection to sensor"""
        try:
            if SIMULATE:
                # Use mock instrument for simulation
                self.instrument = MockModbusInstrument(self.port, self.slave_id)
            else:
                # Use real Modbus instrument
                self.instrument = minimalmodbus.Instrument(self.port, self.slave_id)
                self.instrument.serial.baudrate = self.baudrate
                self.instrument.serial.timeout = self.timeout
            
            # Test connection by reading a register
            _ = self.instrument.read_register(6, functioncode=3)
            self._connected = True
            self._last_error = None
        except Exception as e:
            self._connected = False
            self._last_error = str(e)
            self.instrument = None
    
    def connect(self) -> bool:
        """Attempt to connect to sensor"""
        with self._lock:
            self._initialize_connection()
            return self._connected
    
    def is_connected(self) -> bool:
        """Check if sensor is connected"""
        return self._connected and self.instrument is not None
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message"""
        return self._last_error
    
    def read_parameter(self, param_name: str) -> Optional[float]:
        """
        Read a single sensor parameter
        
        Args:
            param_name: Parameter name (ph, moisture, temperature, ec, nitrogen, phosphorus, potassium)
        
        Returns:
            Scaled parameter value or None if read failed
        """
        if param_name not in self.REGISTER_MAP:
            self._last_error = f"Unknown parameter: {param_name}"
            return None
        
        if not self.is_connected():
            self._last_error = "Sensor not connected"
            return None
        
        try:
            with self._lock:
                register = self.REGISTER_MAP[param_name]
                is_signed = self.SIGNED[param_name]
                scale = self.SCALES[param_name]
                
                raw_value = self.instrument.read_register(
                    register,
                    functioncode=3,
                    signed=is_signed
                )
                
                scaled_value = raw_value / scale
                self._last_error = None
                return scaled_value
        
        except Exception as e:
            self._last_error = str(e)
            self._connected = False
            return None
    
    def read_all_parameters(self) -> Dict[str, Optional[float]]:
        """
        Read all 7 sensor parameters
        
        Returns:
            Dictionary with parameter names as keys and values (or None if read failed)
        """
        if not self.is_connected():
            self._last_error = "Sensor not connected"
            return {param: None for param in self.REGISTER_MAP.keys()}
        
        results = {}
        try:
            with self._lock:
                for param_name, register in self.REGISTER_MAP.items():
                    try:
                        is_signed = self.SIGNED[param_name]
                        scale = self.SCALES[param_name]
                        
                        raw_value = self.instrument.read_register(
                            register,
                            functioncode=3,
                            signed=is_signed
                        )
                        
                        results[param_name] = raw_value / scale
                    except Exception as e:
                        self._last_error = str(e)
                        results[param_name] = None
        
        except Exception as e:
            self._last_error = str(e)
            self._connected = False
            for param in self.REGISTER_MAP.keys():
                results[param] = None
        
        return results
    
    def disconnect(self) -> None:
        """Close sensor connection"""
        with self._lock:
            if self.instrument is not None and hasattr(self.instrument.serial, 'close'):
                try:
                    self.instrument.serial.close()
                except:
                    pass
            self.instrument = None
            self._connected = False


class NPKSensorManager:
    """
    Singleton manager for NPK sensor
    Provides a global interface for the application
    """
    
    _instance: Optional[NPKSensorManager] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> NPKSensorManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.sensor: Optional[NPKSensor] = None
        self._initialized = True
    
    def initialize(
        self,
        port: str = '/dev/ttyUSB0',
        slave_id: int = 1,
        baudrate: int = 9600,
        timeout: float = 1.0
    ) -> bool:
        """
        Initialize the NPK sensor
        
        Returns:
            True if connection successful, False otherwise
        """
        self.sensor = NPKSensor(
            port=port,
            slave_id=slave_id,
            baudrate=baudrate,
            timeout=timeout
        )
        return self.sensor.is_connected()
    
    def read_all(self) -> Dict[str, Optional[float]]:
        """Read all sensor parameters"""
        if self.sensor is None:
            raise RuntimeError("NPK sensor not initialized. Call initialize() first.")
        
        return self.sensor.read_all_parameters()
    
    def read_parameter(self, param_name: str) -> Optional[float]:
        """Read single sensor parameter"""
        if self.sensor is None:
            raise RuntimeError("NPK sensor not initialized. Call initialize() first.")
        
        return self.sensor.read_parameter(param_name)
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.sensor is not None and self.sensor.is_connected()
    
    def get_status(self) -> Dict[str, Any]:
        """Get sensor status information"""
        if self.sensor is None:
            return {
                'connected': False,
                'error': 'Sensor not initialized',
            }
        
        return {
            'connected': self.sensor.is_connected(),
            'port': self.sensor.port,
            'slave_id': self.sensor.slave_id,
            'error': self.sensor.get_last_error(),
        }
    
    def shutdown(self) -> None:
        """Close sensor connection"""
        if self.sensor is not None:
            self.sensor.disconnect()


# Global singleton instance
manager = NPKSensorManager()
