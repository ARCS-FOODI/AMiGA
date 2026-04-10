# backend/scale_telemetry.py
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from . import scale

# Storage configuration
RUNTIME_DATA_DIR = Path.home() / ".amiga_runtime_data"
TELEMETRY_CSV = RUNTIME_DATA_DIR / "scale_bundles.csv"

# Memory limit for serving API requests (e.g., last 100 bundle averages)
MAX_HISTORY_LENGTH = 100

_thread: threading.Thread | None = None
_stop_flag = threading.Event()

# Thread-safe buffer for the current bundle computation
_buffer_lock = threading.Lock()
_current_buffer: List[Dict[str, Any]] = []

# Thread-safe history of bundle averages for the frontend
_history_lock = threading.Lock()
_bundle_history: List[Dict[str, Any]] = []


def _ensure_dir() -> None:
    RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _append_csv_datapoint(weight: float) -> None:
    """
    Appends a single strict CSV datapoint with TIME, Device Name, Plant_ID, and Weight.
    """
    _ensure_dir()
    
    # Generate 5806 / ISO 8601 formatting timestamp
    now_iso = datetime.now().astimezone().isoformat()
    device_name = "USS-DBS61-50"
    plant_id = "AMiGA_1"
    
    csv_line = f"{now_iso},{device_name},{plant_id},{weight:.3f}\n"
    
    # Append to the singular CSV file
    with TELEMETRY_CSV.open("a", encoding="utf-8") as f:
        f.write(csv_line)


def _tick() -> None:
    """
    Reads the scale, appends a line to the CSV, and caches standard points locally.
    """
    weight = scale.manager.get_weight()
    
    # 1. Immediately log to CSV
    try:
        _append_csv_datapoint(weight)
    except Exception as e:
        print(f"[TELEMETRY] Failed to write CSV datapoint: {e}")
        
    # 2. Process bundle caching for existing endpoint compatibility
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _buffer_lock:
        _current_buffer.append({"time": now_str, "weight": weight})
        
        if len(_current_buffer) >= 20:
            # We have a full bundle
            bundle_copy = list(_current_buffer)
            _current_buffer.clear()
            
            # Compute average
            total_weight = sum(pt["weight"] for pt in bundle_copy)
            avg_weight = total_weight / len(bundle_copy)
            
            # Keep track in memory for the frontend graph endpoint
            with _history_lock:
                _bundle_history.append({"time": now_str, "average": avg_weight})
                if len(_bundle_history) > MAX_HISTORY_LENGTH:
                    _bundle_history.pop(0)


def get_recent_averages() -> List[Dict[str, Any]]:
    """ Returns the recent history of bundle averages to be served by the REST API. """
    with _history_lock:
        return list(_bundle_history)


def _run_forever() -> None:
    """
    Background loop ticking roughly every 1.0 second.
    """
    print(f"[TELEMETRY] Started scale telemetry logger. Target: {TELEMETRY_CSV}")
    while not _stop_flag.is_set():
        _tick()
        # Sleep for 1 second but allow fast interrupt
        _stop_flag.wait(1.0)


def start() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return

    _stop_flag.clear()
    
    with _buffer_lock:
        _current_buffer.clear()
        
    _thread = threading.Thread(target=_run_forever, name="amiga-scale-telemetry", daemon=True)
    _thread.start()


def stop() -> None:
    _stop_flag.set()
    if _thread:
        _thread.join(timeout=2.0)
