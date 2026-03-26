# backend/scale_telemetry.py
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from . import scale

# Storage configuration
RUNTIME_DATA_DIR = Path.home() / ".amiga_runtime_data"
TELEMETRY_FILE = RUNTIME_DATA_DIR / "scale_bundles.txt"

# Memory limit for serving API requests (e.g., last 100 bundle averages)
MAX_HISTORY_LENGTH = 100

_thread: threading.Thread | None = None
_stop_flag = threading.Event()

# Thread-safe buffer for the current bundle
_buffer_lock = threading.Lock()
_current_buffer: List[Dict[str, Any]] = []

# Thread-safe history of bundle averages for the frontend
_history_lock = threading.Lock()
_bundle_history: List[Dict[str, Any]] = []


def _ensure_dir() -> None:
    RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _write_bundle(bundle_data: List[Dict[str, Any]], average_weight: float) -> None:
    """
    Writes a 20-point bundle as a human-readable table to the runtime text file.
    """
    _ensure_dir()
    
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        f"=== Bundle: {timestamp_str} ===",
        "Time                 | Weight (g)",
        "-----------------------------------"
    ]
    
    for point in bundle_data:
        # e.g., "2026-03-25 18:00:00 | 123.456"
        lines.append(f"{point['time']:<20} | {point['weight']:.3f}")
        
    lines.append("-----------------------------------")
    lines.append(f"Average Weight: {average_weight:.3f} g")
    lines.append("===================================\n\n")
    
    # Append to the single text file
    with TELEMETRY_FILE.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _tick() -> None:
    """
    Reads the scale, creates a datapoint, and compiles a bundle if 20 points are reached.
    """
    weight = scale.manager.get_weight()
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
            
            # Write out to text file
            try:
                _write_bundle(bundle_copy, avg_weight)
            except Exception as e:
                print(f"[TELEMETRY] Failed to write bundle: {e}")
            
            # Keep track in memory for the frontend graph
            with _history_lock:
                _bundle_history.append({"time": now_str, "average": avg_weight})
                # Evict oldest if we exceed max history to save memory
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
    print(f"[TELEMETRY] Started scale bundling thread. Saving to: {TELEMETRY_FILE}")
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
