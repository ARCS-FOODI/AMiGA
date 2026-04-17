from __future__ import annotations

import threading
import csv
from pathlib import Path
from datetime import datetime
from . import tsl2561

_thread: threading.Thread | None = None
_stop_flag = threading.Event()
_session_dir: Path | None = None
_interval: float = 5.0
_device_name = "TSL2561"

def _tick() -> None:
    if not _session_dir:
        return
    try:
        data = tsl2561.manager.read_data()
        now_iso = datetime.now().astimezone().isoformat()
        
        file_path = _session_dir / "light_data.csv"
        file_exists = file_path.exists()
        
        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["time", "device_name", "broadband", "infrared", "lux"])
            writer.writerow([
                now_iso, 
                _device_name, 
                data.get("broadband", ""),
                data.get("infrared", ""),
                data.get("lux", "")
            ])
            
    except Exception as e:
        print(f"[TSL2561_TELEMETRY] Failed to read or write data: {e}")

def _run_forever() -> None:
    print(f"[TSL2561_TELEMETRY] Started TSL2561 telemetry thread. Saving to: {_session_dir}")
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
    
    _thread = threading.Thread(target=_run_forever, name="amiga-tsl2561-telemetry", daemon=True)
    _thread.start()

def stop() -> None:
    _stop_flag.set()
    if _thread:
        _thread.join(timeout=2.0)
