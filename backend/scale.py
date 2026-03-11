# backend/scale.py
from __future__ import annotations

import threading
import time
import serial
import re
from typing import Dict, Any, Optional

from .settings import SIMULATE
from . import master_log

SCALE_PORT = "/dev/ttyUSB0"
SCALE_BAUDRATE = 9600
SCALE_BYTESIZE = serial.EIGHTBITS
SCALE_PARITY = serial.PARITY_NONE
SCALE_STOPBITS = serial.STOPBITS_ONE
SCALE_TIMEOUT = 1.0


class MockSerial:
    def __init__(self, *args, **kwargs):
        self.is_open = True
        self.mock_weight = 0.0

    def readline(self) -> bytes:
        # Simulate an evolving weight
        self.mock_weight += 0.1
        if self.mock_weight > 5000:
            self.mock_weight = 0.0
        
        # Give a slight delay simulating serial reading speed
        time.sleep(0.5)
        # Assuming US Solid scale outputs something like "   123.45 g \r\n"
        return f"   {self.mock_weight:.2f} g \r\n".encode("ascii")
        
    def close(self):
        self.is_open = False


class Scale:
    """
    Handles serial connection to the USS-DBS61-50 U.S. Solid Scale.
    Continously polls the balance and stores the latest reading to avoid blocking REST APIs.
    """
    def __init__(self, port: str = SCALE_PORT, baudrate: int = SCALE_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None
        self._latest_weight: Optional[float] = None
        self._latest_unit: Optional[str] = None
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True

            try:
                if SIMULATE:
                    self.ser = MockSerial()
                else:
                    self.ser = serial.Serial(
                        port=self.port,
                        baudrate=self.baudrate,
                        bytesize=SCALE_BYTESIZE,
                        parity=SCALE_PARITY,
                        stopbits=SCALE_STOPBITS,
                        timeout=SCALE_TIMEOUT
                    )
                # start reading thread
                self._thread = threading.Thread(target=self._read_loop, daemon=True)
                self._thread.start()
            except Exception as e:
                self._running = False
                print(f"[ERROR] Failed to init Scale serial on {self.port}: {e}")
                try:
                    master_log.log_event("scale_error", source="Scale.start", error=str(e))
                except Exception:
                    pass

    @staticmethod
    def parse_weight_line(text: str) -> tuple[Optional[float], Optional[str]]:
        pattern = re.compile(r"[-+]?\s*(\d*\.?\d+)\s*([a-zA-Z]+)")
        match = pattern.search(text)
        if match:
            wt_str = match.group(1).replace(" ", "")
            unit = match.group(2)
            try:
                wt = float(wt_str)
                return wt, unit
            except ValueError:
                pass
        return None, None

    def _read_loop(self):
        while self._running:
            try:
                if self.ser and getattr(self.ser, 'is_open', False):
                    line = self.ser.readline()
                    if line:
                        text = line.decode('ascii', errors='ignore').strip()
                        if not text:
                            continue
                        
                        wt, unit = self.parse_weight_line(text)
                        if wt is not None:
                            with self._lock:
                                self._latest_weight = wt
                                self._latest_unit = unit
                else:
                    time.sleep(1.0) # Wait before retry if not open
            except Exception as e:
                # If reading fails, pause a bit to avoid CPU spin lock
                time.sleep(0.5)

    def stop(self):
        with self._lock:
            self._running = False
            if self.ser:
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None

    def get_latest(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "weight": self._latest_weight,
                "unit": self._latest_unit,
                "port": self.port,
                "simulated": SIMULATE
            }

class ScaleManager:
    def __init__(self):
        self.scale = Scale()

    def startup(self):
        self.scale.start()

    def shutdown(self):
        self.scale.stop()

# Global singleton
manager = ScaleManager()
