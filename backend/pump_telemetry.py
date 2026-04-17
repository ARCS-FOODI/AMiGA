from __future__ import annotations

import threading
import csv
from pathlib import Path
from datetime import datetime
from . import pumps

_thread: threading.Thread | None = None
_stop_flag = threading.Event()
_session_dir: Path | None = None
_interval: float = 5.0
_device_name = "Pumps"

def _tick() -> None:
    if not _session_dir:
        return
    try:
        now_iso = datetime.now().astimezone().isoformat()
        file_path = _session_dir / "pump_status.csv"
        file_exists = file_path.exists()
        
        # Sort pumps dynamically so we always have a consistent header order
        pump_names = sorted(pumps.manager.pumps.keys())
        header = ["time", "device_name"] + [f"{p}_running" for p in pump_names]
        
        row_data = [now_iso, _device_name]
        for p in pump_names:
            is_running = pumps.manager.pumps[p].is_running
            row_data.append(is_running)

        with file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(row_data)
            
    except Exception as e:
        print(f"[PUMP_TELEMETRY] Failed to read or write data: {e}")

def _run_forever() -> None:
    print(f"[PUMP_TELEMETRY] Started Pump telemetry thread. Saving to: {_session_dir}")
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
    
    _thread = threading.Thread(target=_run_forever, name="amiga-pump-telemetry", daemon=True)
    _thread.start()

def stop() -> None:
    _stop_flag.set()
    if _thread:
        _thread.join(timeout=2.0)
