# backend/scale_telemetry.py
import threading
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from . import scale

# Memory limit for serving API requests (e.g., last 100 bundle averages)
MAX_HISTORY_LENGTH = 100

_thread: threading.Thread | None = None
_stop_flag = threading.Event()
_session_dir: Path | None = None
_interval: float = 5.0
_device_name = "USS-DBS61-50"

# Thread-safe buffer for the current bundle computation (API read history)
_buffer_lock = threading.Lock()
_current_buffer: List[Dict[str, Any]] = []

# Thread-safe history of bundle averages for the frontend
_history_lock = threading.Lock()
_bundle_history: List[Dict[str, Any]] = []

def _tick() -> None:
    weight = scale.manager.get_weight()
    
    # 1. Provide Real-time CSV logging if active
    if _session_dir:
        try:
            now_iso = datetime.now().astimezone().isoformat()
            file_path = _session_dir / "scale_data.csv"
            file_exists = file_path.exists()
            
            with file_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["time", "device_name", "weight_g"])
                writer.writerow([now_iso, _device_name, round(weight, 3)])
        except Exception as e:
            print(f"[SCALE_TELEMETRY] Failed to write CSV datapoint: {e}")
        
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
    print(f"[SCALE_TELEMETRY] Started scale telemetry thread. Saving to: {_session_dir}")
    while not _stop_flag.is_set():
        _tick()
        _stop_flag.wait(_interval)

def start(session_dir: str, interval: float = 5.0) -> None:
    global _thread, _session_dir, _interval
    if _thread and _thread.is_alive():
        return
        
    _session_dir = Path(session_dir)
    _session_dir.mkdir(parents=True, exist_ok=True)
    _interval = interval
    _stop_flag.clear()
    
    _thread = threading.Thread(target=_run_forever, name="amiga-scale-telemetry", daemon=True)
    _thread.start()

def stop() -> None:
    _stop_flag.set()
    if _thread:
        _thread.join(timeout=2.0)
