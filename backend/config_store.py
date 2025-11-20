# backend/config_store.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

# Project root = two levels up from this file (adjust if needed)
BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"
CALIBRATION_FILE = CONFIG_DIR / "calibration.json"

DEFAULT_CALIBRATION: Dict[str, Any] = {
    "pumps": {
        "water": {"ml_per_sec": 4.436},
        "food": {"ml_per_sec": 0.0},
    }
}


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_calibration() -> Dict[str, Any]:
    _ensure_config_dir()
    if not CALIBRATION_FILE.exists():
        return DEFAULT_CALIBRATION.copy()
    try:
        with CALIBRATION_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        # Fallback if file is corrupted
        return DEFAULT_CALIBRATION.copy()
    return data


def save_calibration(data: Dict[str, Any]) -> None:
    _ensure_config_dir()
    with CALIBRATION_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_pump_calibration(pump: str) -> Optional[float]:
    data = load_calibration()
    pumps = data.get("pumps", {})
    pump_data = pumps.get(pump)
    if not pump_data:
        return None
    return float(pump_data.get("ml_per_sec", 0.0))


def set_pump_calibration(pump: str, ml_per_sec: float) -> Dict[str, Any]:
    data = load_calibration()
    pumps = data.setdefault("pumps", {})
    pumps[pump] = {"ml_per_sec": float(ml_per_sec)}
    save_calibration(data)
    return data
