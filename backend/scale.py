import json
import os
import threading
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[0]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SCALE_STATE_FILE = DATA_DIR / "scale_state.json"

class ScaleManager:
    """
    Simulates a digital scale that measures weight in grams.
    Since we are simulating, we keep track of:
      1. Water weight added via pumps
      2. Simulated plant biomass growth over time
    """
    def __init__(self):
        self._lock = threading.Lock()
        
        # Internal state
        self.water_g = 0.0
        self.growth_g = 0.0
        self.tare_offset_g = 0.0
        
        # Growth simulation rate: e.g. 5g per hour
        self.growth_rate_g_per_sec = 5.0 / 3600.0
        
        self.last_update_time = None
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
                "last_update_time": current_time
            }
            tmp = SCALE_STATE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2))
            tmp.replace(SCALE_STATE_FILE)
        except Exception as e:
            print(f"[SCALE] Error saving state: {e}")

    def _simulate_growth(self):
        """Update plant growth since the last time we checked."""
        import time
        now = time.time()
        
        if self.last_update_time is not None:
            elapsed = max(0, now - self.last_update_time)
            self.growth_g += elapsed * self.growth_rate_g_per_sec
            
        self._save_state(now)
        self.last_update_time = now

    def add_water_g(self, grams: float):
        """Called by the pump module when water/food is dispensed."""
        with self._lock:
            self.water_g += grams
            self._simulate_growth()

    def get_weight(self) -> float:
        """Returns the current simulated weight reading, offset by the tare."""
        with self._lock:
            self._simulate_growth()
            absolute_weight = self.water_g + self.growth_g
            return absolute_weight - self.tare_offset_g

    def tare(self) -> float:
        """Zero out the scale (set the tare offset to the current absolute weight)."""
        with self._lock:
            self._simulate_growth()
            absolute_weight = self.water_g + self.growth_g
            self.tare_offset_g = absolute_weight
            self._save_state(self.last_update_time)
            return 0.0

manager = ScaleManager()
