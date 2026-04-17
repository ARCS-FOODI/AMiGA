from __future__ import annotations
 
import threading
import csv
from pathlib import Path
from datetime import datetime
from . import pumps
 
_session_dir: Path | None = None
_device_name = "Pumps"

_heartbeat_thread: threading.Thread | None = None
_stop_flag = threading.Event()

def log_pump_event(data: dict, event_type: str = "DISPENSE") -> None:
    """Writes a pump event to the combined pump_events.csv."""
    if not _session_dir:
        return
    try:
        now_iso = datetime.now().astimezone().isoformat()
        file_path = _session_dir / "pump_events.csv"
        file_exists = file_path.exists()
        
        # Consistent header for events
        header = ["time", "event_type", "pump_name", "ml", "seconds", "hz", "direction"]
        
        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            
            writer.writerow([
                now_iso,
                event_type,
                data.get("pump", "unknown"),
                data.get("ml", ""),
                round(data.get("seconds", 0), 2),
                data.get("hz", ""),
                data.get("direction", "")
            ])
            
    except Exception as e:
        print(f"[PUMP_TELEMETRY] Failed to write event: {e}")

def _run_heartbeat() -> None:
    """Slow loop to confirm system is alive."""
    while not _stop_flag.is_set():
        # Heartbeat doesn't log specific pump data, just a system-is-alive entry
        log_pump_event({"pump": "SYSTEM"}, event_type="HEARTBEAT")
        if _stop_flag.wait(3600): # 1 hour
            break

def start(session_dir: str, interval: float = 5.0) -> None:
    """Initializes pump telemetry with event-driven logging and slow heartbeat."""
    global _session_dir, _heartbeat_thread
    
    _session_dir = Path(session_dir)
    _session_dir.mkdir(parents=True, exist_ok=True)
    _stop_flag.clear()
    
    # Register the callback in the hardware layer
    pumps.register_on_dispense_callback(log_pump_event)
    
    # Start heartbeat
    if not _heartbeat_thread or not _heartbeat_thread.is_alive():
        _heartbeat_thread = threading.Thread(target=_run_heartbeat, name="amiga-pump-heartbeat", daemon=True)
        _heartbeat_thread.start()
    
    log_pump_event({"pump": "SYSTEM"}, event_type="STARTUP")

def stop() -> None:
    """Stops the heartbeat thread."""
    _stop_flag.set()
    if _heartbeat_thread:
        _heartbeat_thread.join(timeout=2.0)
