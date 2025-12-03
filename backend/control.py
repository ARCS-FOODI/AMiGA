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
LOG_FILE = DATA_DIR / "moisture_cycles.csv"  # name kept for backward compatibility


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
                "target_threshold_v",      # voltage threshold in V
                "vote_k",
                "hz",
                "irrigate_seconds",
                "over_threshold_count",    # number of channels with v > threshold
                "triggered",
                "irrigated",
                "before_v0",
                "before_v1",
                "before_v2",
                "before_v3",
                "after_v0",
                "after_v1",
                "after_v2",
                "after_v3",
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

    # For backward compatibility with existing API key,
    # this count is "sensors considered dry" = v > threshold.
    over = result.get("under_threshold_count")

    triggered = result.get("triggered", False)
    irrigated = result.get("irrigated", False)

    # Before readings
    before = result.get("before") or {}
    before_readings = before.get("readings") or []
    if before_readings:
        before_volts = before_readings[0].get("voltages", [None, None, None, None])
    else:
        before_volts = [None, None, None, None]

    # After readings (may be None if not irrigated)
    after = result.get("after")
    if after and (after.get("readings") or []):
        after_readings = after["readings"][0]
        after_volts = after_readings.get("voltages", [None, None, None, None])
    else:
        after_volts = [None, None, None, None]

    row = [
        ts,
        pump,
        target_threshold,
        vote_k,
        hz,
        irrigate_seconds,
        over,
        int(bool(triggered)),
        int(bool(irrigated)),
        before_volts[0],
        before_volts[1],
        before_volts[2],
        before_volts[3],
        after_volts[0],
        after_volts[1],
        after_volts[2],
        after_volts[3],
    ]

    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def control_cycle_once(
    pump: str,
    target_threshold: float = 1.5,         # voltage threshold in V
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
    One-step closed-loop cycle, now based on voltage:

    1. Read sensors once ("before") and get voltages.
    2. Count how many channels have v > target_threshold (interpreted as "dry").
    3. If count >= vote_k:
         - Run the given pump for irrigate_seconds.
         - Read sensors again ("after").
       Else:
         - No pump run; "after" = None.
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
        # Just passed through for metadata; snapshot_sensors doesn't use it internally
        thresh_pct=target_threshold,
        use_digital=False,
    )

    before_read = before["readings"][0]
    before_volts = before_read["voltages"]

    # Dry condition: voltage > threshold (≈ old moisture_pct < 35%)
    under = sum(1 for v in before_volts if v > target_threshold)

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
        # NOTE: kept key name for compatibility; now counts v > threshold (dry)
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
    target_threshold: float = 1.5,
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
      - reading voltages
      - deciding based on voltage threshold
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

        # Basic log to server console showing voltages
        before_volts = result["before"]["readings"][0]["voltages"]
        print(
            "[CONTROL] volts=",
            [f"{v:4.3f}" for v in before_volts],
            "over_thresh=",
            result["under_threshold_count"],  # count of v > threshold
            "irrigated=",
            result["irrigated"],
        )

        time.sleep(loop_interval)
