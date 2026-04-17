from __future__ import annotations

import threading
import time
import csv
from pathlib import Path
from datetime import datetime
from . import sensors
from .settings import SENSOR_ADDRS

_thread: threading.Thread | None = None
_stop_flag = threading.Event()
_session_dir: Path | None = None
_interval: float = 5.0
_device_name = "ADS1115_Array"

def _tick() -> None:
    if not _session_dir:
        return
    
    # Debug: log the addresses we are about to poll
    # print(f"[SENSORS_TELEMETRY] Polling sensor addresses: {SENSOR_ADDRS}")
    
    for addr in SENSOR_ADDRS:
        try:
            data = sensors.manager.main_array.snapshot(addr=addr, samples=1, interval=0.0)
            device_id = data.get("device_id", f"Unknown_0x{addr:02x}")
            readings = data.get("readings", [])
            
            if not readings:
                print(f"[SENSORS_TELEMETRY] No readings returned for address 0x{addr:02x}")
                continue
                
            volts = readings[0].get("voltages", [None]*4)
            now_iso = datetime.now().astimezone().isoformat()
            
            file_path = _session_dir / "sensors.csv"
            file_exists = file_path.exists()
            
            with file_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["time", "device_id", "v0", "v1", "v2", "v3"])
                writer.writerow([
                    now_iso, 
                    device_id, 
                    round(volts[0], 4) if volts[0] is not None else "",
                    round(volts[1], 4) if volts[1] is not None else "",
                    round(volts[2], 4) if volts[2] is not None else "",
                    round(volts[3], 4) if volts[3] is not None else ""
                ])
        except Exception as e:
            print(f"[SENSORS_TELEMETRY] Failed to read or write data for 0x{addr:02x}: {e}")

def _run_forever() -> None:
    print(f"[SENSORS_TELEMETRY] Started sensors telemetry thread. Saving to: {_session_dir}")
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
    
    _thread = threading.Thread(target=_run_forever, name="amiga-sensors-telemetry", daemon=True)
    _thread.start()

def stop() -> None:
    _stop_flag.set()
    if _thread:
        _thread.join(timeout=2.0)
