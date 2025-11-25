# backend/control.py
from __future__ import annotations

from typing import Dict, Any
import time
import csv
from pathlib import Path

from .settings import (
    DEFAULT_ADDR,
    DEFAULT_GAIN,
    DEFAULT_AVG,
    DEFAULT_DRY_V,
    DEFAULT_WET_V,
    DEFAULT_VOTE_K,
    DEFAULT_HZ,
    DEFAULT_DIR,
    DEFAULT_IRR_SEC,
    DEFAULT_COOLDOWN_S,
)
from . import sensors, pumps

# Paths for logging
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOG_FILE = DATA_DIR / "moisture_cycles.csv"


def _ensure_log_file_has_header() -> None:
    """
    Make sure data directory exists and CSV has a header row.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with LOG_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "pump",
                "target_threshold",
                "vote_k",
                "hz",
                "irrigate_seconds",
                "under_threshold_count",
                "triggered",
                "irrigated",
                "before_m0",
                "before_m1",
                "before_m2",
                "before_m3",
                "after_m0",
                "after_m1",
                "after_m2",
                "after_m3",
            ])


def _log_control_cycle_to_csv(result: Dict[str, Any]) -> None:
    """
    Append one row to the CSV log for a control cycle result.
    """
    _ensure_log_file_has_header()

    ts = time.time()
    pump = result.get("pump")
    target_threshold = result.get("target_threshold")
    vote_k = result.get("vote_k")
    hz = result.get("hz")
    irrigate_seconds = result.get("irrigate_seconds")
    under = result.get("under_threshold_count")
    triggered = result.get("triggered", False)
    irrigated = result.get("irrigated", False)

    # Before readings
    before = result.get("before") or {}
    before_readings = before.get("readings") or []
    if before_readings:
        before_pcts = before_readings[0].get("moisture_pct", [None, None, None, None])
    else:
        before_pcts = [None, None, None, None]

    # After readings (may be None if not irrigated)
    after = result.get("after")
    if after and (after.get("readings") or []):
        after_readings = after["readings"][0]
        after_pcts = after_readings.get("moisture_pct", [None, None, None, None])
    else:
        after_pcts = [None, None, None, None]

    row = [
        ts,
        pump,
        target_threshold,
        vote_k,
        hz,
        irrigate_seconds,
        under,
        int(bool(triggered)),
        int(bool(irrigated)),
        before_pcts[0],
        before_pcts[1],
        before_pcts[2],
        before_pcts[3],
        after_pcts[0],
        after_pcts[1],
        after_pcts[2],
        after_pcts[3],
    ]

    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def control_cycle_once(
    pump: str,
    target_threshold: float = 40.0,
    vote_k: int = DEFAULT_VOTE_K,
    hz: float = DEFAULT_HZ,
    irrigate_seconds: float = DEFAULT_IRR_SEC,
    direction: str = DEFAULT_DIR,
    addr: int = DEFAULT_ADDR,
    gain: int = DEFAULT_GAIN,
    avg: int = DEFAULT_AVG,
    dry_v: float = DEFAULT_DRY_V,
    wet_v: float = DEFAULT_WET_V,
) -> Dict[str, Any]:
    """
    One-step closed-loop cycle:

    1. Read moisture sensors once ("before").
    2. Count how many are below target_threshold.
    3. If under_count >= vote_k:
         - Run the given pump for irrigate_seconds.
         - Read sensors again ("after").
       Else:
         - No pump run; "after" = None.

    This is meant to be called either directly from the API
    or from control_cycle_continuous() below.
    """
    # Read before
    before = sensors.snapshot_sensors(
        addr=addr,
        gain=gain,
        samples=1,
        interval=0.0,
        avg=avg,
        dry_v=dry_v,
        wet_v=wet_v,
        thresh_pct=target_threshold,
        use_digital=False,
    )

    before_read = before["readings"][0]
    before_pcts = before_read["moisture_pct"]
    under = sum(1 for p in before_pcts if p < target_threshold)

    triggered = under >= vote_k
    irrigated = False
    pump_action: Dict[str, Any] | None = None
    after: Dict[str, Any] | None = None

    if triggered and irrigate_seconds > 0:
        # Run pump by seconds
        pump_action = pumps.run_pump_seconds(
            pump=pump,
            seconds=irrigate_seconds,
            hz=hz,
            direction=direction,
        )
        irrigated = True
        # Read after
        after = sensors.snapshot_sensors(
            addr=addr,
            gain=gain,
            samples=1,
            interval=0.0,
            avg=avg,
            dry_v=dry_v,
            wet_v=wet_v,
            thresh_pct=target_threshold,
            use_digital=False,
        )

    result: Dict[str, Any] = {
        "target_threshold": target_threshold,
        "vote_k": vote_k,
        "pump": pump,
        "hz": hz,
        "direction": direction,
        "irrigate_seconds": irrigate_seconds,
        "before": before,
        "after": after,
        "under_threshold_count": under,
        "triggered": triggered,
        "irrigated": irrigated,
        "pump_action": pump_action,
    }

    # Log this cycle to CSV
    try:
        _log_control_cycle_to_csv(result)
    except Exception as e:
        # Don't break control if logging fails; just print to server console
        print(f"[LOG] Failed to log control cycle to CSV: {e}")

    return result


def control_cycle_continuous(
    pump: str,
    target_threshold: float = 40.0,
    vote_k: int = DEFAULT_VOTE_K,
    hz: float = DEFAULT_HZ,
    irrigate_seconds: float = DEFAULT_IRR_SEC,
    direction: str = DEFAULT_DIR,
    addr: int = DEFAULT_ADDR,
    gain: int = DEFAULT_GAIN,
    avg: int = DEFAULT_AVG,
    dry_v: float = DEFAULT_DRY_V,
    wet_v: float = DEFAULT_WET_V,
    loop_interval: float = DEFAULT_COOLDOWN_S,
) -> None:
    """
    Simple continuous loop version of control_cycle_once.

    This will block the calling thread and keep:
      - reading moisture
      - deciding
      - maybe irrigating
      - logging to CSV
      - sleeping loop_interval seconds
    until the process is stopped (e.g. Ctrl+C in the server).
    """
    while True:
        result = control_cycle_once(
            pump=pump,
            target_threshold=target_threshold,
            vote_k=vote_k,
            hz=hz,
            irrigate_seconds=irrigate_seconds,
            direction=direction,
            addr=addr,
            gain=gain,
            avg=avg,
            dry_v=dry_v,
            wet_v=wet_v,
        )

        # Optional: basic log to server console
        before_pcts = result["before"]["readings"][0]["moisture_pct"]
        print(
            "[CONTROL] moisture%=", [f"{p:4.1f}" for p in before_pcts],
            "under=", result["under_threshold_count"],
            "irrigated=", result["irrigated"],
        )

        time.sleep(loop_interval)
