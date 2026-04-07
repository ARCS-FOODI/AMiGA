# backend/pump_telemetry.py
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

# Storage configuration
RUNTIME_DATA_DIR = Path.home() / ".amiga_runtime_data"
TELEMETRY_FILE = RUNTIME_DATA_DIR / "pump_telemetry.csv"

def _ensure_dir() -> None:
    RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)

def log_action(pump_name: str, action_type: str, details: Dict[str, Any]) -> None:
    """
    Logs an explicitly requested pump action to the telemetry CSV.
    """
    try:
        # ISO 8601 formatting, using UTC
        now_str = datetime.now(timezone.utc).isoformat()
        
        # Structure explicitly into a wide table
        action = action_type
        direction = details.get("direction", "")
        amount = details.get("amount_ml", "")
        seconds = details.get("seconds", "")
        hz = details.get("hz", "")
        
        display_names = {
            "water": "water_pump",
            "food": "food_pump"
        }
        display_name = display_names.get(pump_name, pump_name)
        
        row = [
            now_str,
            display_name, 
            action,
            direction,
            amount,
            seconds,
            hz
        ]
        
        _ensure_dir()
        
        file_exists = TELEMETRY_FILE.exists()
        
        with TELEMETRY_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write header if file is purely new
            if not file_exists or TELEMETRY_FILE.stat().st_size == 0:
                writer.writerow(["Time", "Component", "Action", "Direction", "Amount (mL)", "Duration (s)", "Frequency (Hz)"])
            writer.writerow(row)
            
    except Exception as e:
        print(f"[PUMP TELEMETRY] Failed to write data: {e}")
