from __future__ import annotations
 
import threading
import csv
from pathlib import Path
from datetime import datetime
from . import light
 
_session_dir: Path | None = None
_device_name = "GrowLightRelay"

_heartbeat_thread: threading.Thread | None = None
_stop_flag = threading.Event()

def log_light_event(is_on: bool, event_type: str = "STATUS") -> None:
    """Writes the light state to CSV. Can be called by event or heartbeat."""
    if not _session_dir:
        return
    try:
        now_iso = datetime.now().astimezone().isoformat()
        file_path = _session_dir / "light_status.csv"
        file_exists = file_path.exists()
        
        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["time", "device_name", "is_on", "event_type"])
            writer.writerow([
                now_iso, 
                _device_name, 
                is_on,
                event_type
            ])
            
    except Exception as e:
        print(f"[LIGHT_TELEMETRY] Failed to write event: {e}")

def _run_heartbeat() -> None:
    """Slow loop to log current state periodically even if no changes occur."""
    while not _stop_flag.is_set():
        log_light_event(light.manager.main_light.is_on, event_type="HEARTBEAT")
        # Wait 1 hour between heartbeats
        if _stop_flag.wait(3600):
            break

def start(session_dir: str, interval: float = 5.0) -> None:
    """
    Initializes telemetry. 
    Registers event callback and starts a slow heartbeat thread.
    """
    global _session_dir, _heartbeat_thread
    
    _session_dir = Path(session_dir)
    _session_dir.mkdir(parents=True, exist_ok=True)
    _stop_flag.clear()
    
    # Register the callback in the hardware layer
    light.register_callback(lambda on: log_light_event(on, event_type="CHANGE"))
    
    # Start slow heartbeat
    if not _heartbeat_thread or not _heartbeat_thread.is_alive():
        _heartbeat_thread = threading.Thread(target=_run_heartbeat, name="amiga-light-heartbeat", daemon=True)
        _heartbeat_thread.start()
    
    # Log initial state
    log_light_event(light.manager.main_light.is_on, event_type="STARTUP")

def stop() -> None:
    """Stops the heartbeat thread."""
    _stop_flag.set()
    if _heartbeat_thread:
        _heartbeat_thread.join(timeout=2.0)
