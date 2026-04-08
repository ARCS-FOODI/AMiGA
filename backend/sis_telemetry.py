import threading
import time
import csv
import json
from datetime import datetime
from pathlib import Path

from . import sis

RUNTIME_DATA_DIR = Path.home() / ".amiga_runtime_data"
TELEMETRY_FILE = RUNTIME_DATA_DIR / "sis_data.csv"

_thread: threading.Thread | None = None
_stop_flag = threading.Event()


def _ensure_dir() -> None:
    RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _init_csv() -> None:
    _ensure_dir()
    expected_header = [
        "time",
        "component",
        "moisture",
        "nitrogen",
        "temperature",
        "ph",
        "ec",
        "phosphorus",
        "potassium",
    ]
    expected_header_line = ",".join(expected_header)
    legacy_header_line = "time,data type,componeent,values"

    if not TELEMETRY_FILE.exists():
        with open(TELEMETRY_FILE, mode='w', newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(expected_header)
        return

    with open(TELEMETRY_FILE, mode='r', newline='', encoding="utf-8") as file:
        first_line = file.readline().strip()
        rest_lines = file.read().splitlines()

    if first_line == expected_header_line:
        return

    if first_line == legacy_header_line:
        data_lines = rest_lines
    else:
        data_lines = [first_line] + rest_lines if first_line else rest_lines

    with open(TELEMETRY_FILE, mode='w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(expected_header)
        for line in data_lines:
            file.write(line + "\n")


def _tick() -> None:
    """
    Reads the SIS sensor and writes a row to the CSV file.
    """
    try:
        data = sis.manager.read_data()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(TELEMETRY_FILE, mode='a', newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                now_str,
                "SIS",
                data.get("moisture", ""),
                data.get("nitrogen", ""),
                data.get("temperature", ""),
                data.get("ph", ""),
                data.get("ec", ""),
                data.get("phosphorus", ""),
                data.get("potassium", ""),
            ])
            
    except Exception as e:
        print(f"[SIS_TELEMETRY] Failed to read or write SIS data: {e}")


def _run_forever() -> None:
    """
    Background loop ticking roughly every 1.0 second.
    """
    print(f"[SIS_TELEMETRY] Started SIS telemetry thread. Saving to: {TELEMETRY_FILE}")
    _init_csv()
    while not _stop_flag.is_set():
        _tick()
        # Sleep for 1 second but allow fast interrupt
        _stop_flag.wait(1.0)


def start() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return

    _stop_flag.clear()
    
    _thread = threading.Thread(target=_run_forever, name="amiga-sis-telemetry", daemon=True)
    _thread.start()


def stop() -> None:
    _stop_flag.set()
    if _thread:
        _thread.join(timeout=2.0)
