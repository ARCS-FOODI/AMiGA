# backend/scale.py
"""
USS-DBS61-50 U.S. Solid Digital Balance Scale driver.

- SIMULATE = True  →  mock weight using growth simulation (no hardware needed)
- SIMULATE = False →  read real RS232/USB serial data from /dev/ttyUSB0
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .settings import SIMULATE_SCALE

# ── Serial configuration (USS-DBS61-50 defaults) ────────────────────────────
SCALE_PORT = "/dev/ttyUSB0"
SCALE_BAUDRATE = 9600

# ── Persistent state file (simulation mode) ──────────────────────────────────
ROOT = Path(__file__).resolve().parents[0]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SCALE_STATE_FILE = DATA_DIR / "scale_state.json"


# ═══════════════════════════════════════════════════════════════════════════════
#  Simulation-only ScaleManager (no hardware required)
# ═══════════════════════════════════════════════════════════════════════════════
class _SimulatedScaleManager:
    """
    Mock scale that keeps track of water weight and simulated plant growth.
    Used when SIMULATE = True (start_simulate.sh).
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.water_g = 0.0
        self.growth_g = 0.0
        self.tare_offset_g = 0.0
        self.growth_rate_g_per_sec = 5.0 / 3600.0  # 5 g per hour
        self.last_update_time: Optional[float] = None
        self._load_state()

    def _load_state(self):
        if SCALE_STATE_FILE.exists():
            try:
                data = json.loads(SCALE_STATE_FILE.read_text())
                self.water_g = data.get("water_g", 0.0)
                self.growth_g = data.get("growth_g", 0.0)
                self.tare_offset_g = data.get("tare_offset_g", 0.0)
                self.last_update_time = data.get("last_update_time", None)
            except Exception as e:
                print(f"[SCALE] Error loading state: {e}")

    def _save_state(self, current_time: float):
        try:
            data = {
                "water_g": self.water_g,
                "growth_g": self.growth_g,
                "tare_offset_g": self.tare_offset_g,
                "last_update_time": current_time,
            }
            tmp = SCALE_STATE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2))
            tmp.replace(SCALE_STATE_FILE)
        except Exception as e:
            print(f"[SCALE] Error saving state: {e}")

    def _simulate_growth(self):
        now = time.time()
        if self.last_update_time is not None:
            elapsed = max(0, now - self.last_update_time)
            self.growth_g += elapsed * self.growth_rate_g_per_sec
        self._save_state(now)
        self.last_update_time = now

    # -- Public API (matches _HardwareScaleManager) ---------------------------

    def add_water_g(self, grams: float):
        """Called by the pump module when water/food is dispensed."""
        with self._lock:
            self.water_g += grams
            self._simulate_growth()

    def get_weight(self) -> float:
        with self._lock:
            self._simulate_growth()
            return (self.water_g + self.growth_g) - self.tare_offset_g

    def tare(self) -> float:
        with self._lock:
            self._simulate_growth()
            self.tare_offset_g = self.water_g + self.growth_g
            self._save_state(self.last_update_time)
            return 0.0

    def startup(self):
        print("[SCALE] Simulation mode – no serial port needed.")

    def shutdown(self):
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Hardware ScaleManager (RS232 via pyserial)
# ═══════════════════════════════════════════════════════════════════════════════
class _HardwareScaleManager:
    """
    Reads the USS-DBS61-50 via RS232→USB continuously on a background thread
    and caches the latest weight so that REST API calls never block on I/O.
    """
    def __init__(self, port: str = SCALE_PORT, baudrate: int = SCALE_BAUDRATE):
        self.port = port
        self.baudrate = baudrate

        self._lock = threading.Lock()
        self._latest_weight: Optional[float] = None
        self._tare_offset: float = 0.0
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._ser = None  # serial.Serial instance

    # -- Background serial reader ---------------------------------------------

    @staticmethod
    def parse_weight_line(text: str) -> Optional[float]:
        """
        Parse the ASCII string that the USS-DBS61-50 sends over RS232.
        Typical formats:  '   123.45 g', ' + 12.340 g', ' -  0.50 g'
        Returns weight in grams, or None if line is unparseable.
        """
        pattern = re.compile(r"[-+]?\s*(\d+\.?\d*)")
        match = pattern.search(text)
        if match:
            try:
                return float(match.group(1).replace(" ", ""))
            except ValueError:
                return None
        return None

    def _read_loop(self):
        """Continuous serial reader running in a daemon thread."""
        while self._running:
            try:
                if self._ser and self._ser.is_open:
                    line = self._ser.readline()
                    if line:
                        text = line.decode("ascii", errors="ignore").strip()
                        if not text:
                            continue
                        wt = self.parse_weight_line(text)
                        if wt is not None:
                            with self._lock:
                                self._latest_weight = wt
                else:
                    time.sleep(1.0)
            except Exception:
                time.sleep(0.5)

    # -- Public API -----------------------------------------------------------

    def startup(self):
        """Open the serial port and start the polling thread."""
        import serial  # import here so simulation mode never needs pyserial

        with self._lock:
            if self._running:
                return
            self._running = True

        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
            )
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            print(f"[SCALE] Hardware mode – reading from {self.port} @ {self.baudrate} baud.")
        except Exception as e:
            self._running = False
            print(f"[SCALE] ❌ Failed to open serial port {self.port}: {e}")

    def shutdown(self):
        """Cleanly stop the reader thread and close the port."""
        self._running = False
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    def get_weight(self) -> float:
        """Return latest weight minus the software tare offset."""
        with self._lock:
            raw = self._latest_weight if self._latest_weight is not None else 0.0
            return raw - self._tare_offset

    def tare(self) -> float:
        """Zero the scale by recording the current weight as the offset."""
        with self._lock:
            raw = self._latest_weight if self._latest_weight is not None else 0.0
            self._tare_offset = raw
            return 0.0

    def add_water_g(self, grams: float):
        """No-op on real hardware — the physical scale tracks this."""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Global singleton – pick the right implementation based on SIMULATE flag
# ═══════════════════════════════════════════════════════════════════════════════
if SIMULATE_SCALE:
    manager = _SimulatedScaleManager()
else:
    manager = _HardwareScaleManager()
