# backend/master_log.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any, Dict
import csv

# Paths for logging
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MASTER_LOG_FILE = DATA_DIR / "master.csv"

# Master CSV schema: all event rows share these columns.
COLUMNS = [
    "timestamp",            # ISO 8601 string with timezone
    "event_type",           # e.g. sensor_read, control_cycle, pump_run_seconds, light_state
    "source",               # module.function that logged the event

    # Pump-related fields
    "pump",                 # single pump name
    "pumps",                # comma-separated list for multi-pump events
    "seconds",              # duration of action (pump run, light on-for)
    "ml",                   # target volume for pump_run_ml
    "hz",                   # step frequency
    "direction",            # pump direction string

    # Light-related fields
    "light_on",             # True / False

    # Sensor-related fields
    "addr",
    "gain",
    "avg",
    "sample_index",
    "v0",
    "v1",
    "v2",
    "v3",
    "do_state",

    # Control / irrigation fields
    "target_threshold_v",
    "vote_k",
    "irrigate_seconds",
    "triggered",
    "irrigated",
    "under_threshold_count",

    # Generic text field for extra info
    "note",
]


def _ensure_master_log_has_header() -> None:
    """
    Ensure data directory exists and master.csv has a header row.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not MASTER_LOG_FILE.exists():
        with MASTER_LOG_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)


def log_event(event_type: str, **kwargs: Any) -> None:
    """
    Append a single event row to master.csv.

    - event_type: string label for the kind of event
    - kwargs: values for columns defined in COLUMNS. Unknown keys are ignored.
      If 'timestamp' is not provided, current time is used.
    """
    _ensure_master_log_has_header()

    ts = kwargs.pop("timestamp", None)
    if ts is None:
        ts = datetime.now().astimezone().isoformat()

    # Build row dict with defaults
    row: Dict[str, Any] = {col: "" for col in COLUMNS}
    row["timestamp"] = ts
    row["event_type"] = event_type

    # Fill known columns from kwargs
    for key, value in kwargs.items():
        if key in row and value is not None:
            row[key] = value

    # Write row in defined column order
    with MASTER_LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([row[col] for col in COLUMNS])
