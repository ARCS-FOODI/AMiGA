from __future__ import annotations

import threading
import csv
from pathlib import Path
from datetime import datetime
from . import light

_thread: threading.Thread | None = None
_stop_flag = threading.Event()
_session_dir: Path | None = None
_interval: float = 5.0
_device_name = "GrowLightRelay"

def _tick() -> None:
    if not _session_dir:
        return
    try:
        data = light.manager.main_light.get_state()
        now_iso = datetime.now().astimezone().isoformat()
        
        file_path = _session_dir / "light_status.csv"
        file_exists = file_path.exists()
        
        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["time", "device_name", "is_on"])
            writer.writerow([
                now_iso, 
                _device_name, 
                data.get("on", "")
            ])
            
    except Exception as e:
        print(f"[LIGHT_TELEMETRY] Failed to read or write data: {e}")

def _run_forever() -> None:
    print(f"[LIGHT_TELEMETRY] Started Light telemetry thread. Saving to: {_session_dir}")
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
    
    _thread = threading.Thread(target=_run_forever, name="amiga-light-telemetry", daemon=True)
    _thread.start()

def stop() -> None:
    _stop_flag.set()
    if _thread:
        _thread.join(timeout=2.0)
