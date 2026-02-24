# backend/grow_scheduler.py
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, Optional

from zoneinfo import ZoneInfo

from . import light, pumps, master_log

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PLANT_STATUS_FILE = DATA_DIR / "plant_status.json"
SCHED_STATE_FILE = DATA_DIR / "scheduler_state.json"

# ----------------------------
# USER TUNABLES
# ----------------------------

# Your timezone (scheduler decisions are made in this tz)
TZ_NAME = "America/Los_Angeles"

# Turn ON the day/night cycle starting on a fixed datetime (so the camera has light to detect green).
# Format: "YYYY-MM-DD HH:MM" (local time in TZ_NAME)
DAYNIGHT_START_AT = "2025-12-18 07:00"

# Day/night window (8–10 hours darkness required).
# Choose 10h dark (14h light): dark 20:00 -> 06:00
LIGHT_ON_START = "06:00"   # lights ON
LIGHT_ON_END   = "20:00"   # lights OFF

# Daily food dose AFTER germination
FOOD_PUMP_NAME = "food"
FOOD_ML_PER_DAY = 100.0
FOOD_DOSE_TIME = "12:00"   # noon local time (safer than midnight)

# How often the scheduler loop wakes up
TICK_SECONDS = 20.0

# ----------------------------

_thread: Optional[threading.Thread] = None
_stop_flag = threading.Event()


def _parse_hhmm(s: str) -> time:
    parts = s.strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid time '{s}' (expected HH:MM)")
    h = int(parts[0])
    m = int(parts[1])
    return time(hour=h, minute=m, second=0)


def _parse_local_datetime(s: str, tz: ZoneInfo) -> datetime:
    """
    Parse 'YYYY-MM-DD HH:MM' into timezone-aware datetime.
    """
    s = s.strip()
    # Accept either "YYYY-MM-DD HH:MM" or ISO-like "YYYY-MM-DDTHH:MM"
    s = s.replace("T", " ")
    dt_naive = datetime.strptime(s, "%Y-%m-%d %H:%M")
    return dt_naive.replace(tzinfo=tz)


def _read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _get_plant_status() -> str:
    data = _read_json(PLANT_STATUS_FILE, default={"status": "pre-germination"})
    return str(data.get("status", "pre-germination")).strip().lower()


def _get_state() -> Dict[str, Any]:
    return _read_json(SCHED_STATE_FILE, default={"last_food_date": ""})


def _set_state(state: Dict[str, Any]) -> None:
    _write_json_atomic(SCHED_STATE_FILE, state)


def _ensure_daynight_enabled() -> None:
    """
    Force light config into daynight mode with our schedule.
    """
    cfg = light.get_light_config()
    if cfg.get("mode") != "daynight":
        # IMPORTANT: light.set_light_config(mode, day_start, day_end)
        light.set_light_config("daynight", LIGHT_ON_START, LIGHT_ON_END)
        master_log.log_event(
            "scheduler_light_daynight_enabled",
            source="grow_scheduler._ensure_daynight_enabled",
            note=f"start={LIGHT_ON_START} end={LIGHT_ON_END}",
        )


def _apply_daynight_now() -> None:
    light.apply_daynight_now()


def _food_due(now: datetime, last_food_date: str) -> bool:
    dose_t = _parse_hhmm(FOOD_DOSE_TIME)
    scheduled = now.replace(hour=dose_t.hour, minute=dose_t.minute, second=0, microsecond=0)
    today = now.date().isoformat()
    return (now >= scheduled) and (last_food_date != today)


def _run_food_dose() -> None:
    result = pumps.manager.get_pump(FOOD_PUMP_NAME).dispense_ml(ml=FOOD_ML_PER_DAY)
    master_log.log_event(
        "scheduler_food_dose",
        source="grow_scheduler._run_food_dose",
        pump=FOOD_PUMP_NAME,
        ml=FOOD_ML_PER_DAY,
        note=f"scheduled_at={FOOD_DOSE_TIME} result={result.get('status','')}",
    )


def tick() -> None:
    """
    Scheduler behavior:
      - Starting DAYNIGHT_START_AT: enable daynight lighting and keep applying it.
      - Food dosing still requires plant_status == 'germinated'.
    """
    tz = ZoneInfo(TZ_NAME)
    now = datetime.now(tz)
    daynight_start = _parse_local_datetime(DAYNIGHT_START_AT, tz)

    # 1) Lighting is enabled after the fixed start time (regardless of germination)
    if now >= daynight_start:
        try:
            _ensure_daynight_enabled()
            _apply_daynight_now()
        except Exception as e:
            print(f"[SCHED] lighting tick failed: {e}")

    # 2) Daily food dose requires germination
    status = _get_plant_status()
    if status != "germinated":
        return

    state = _get_state()
    last_food_date = str(state.get("last_food_date", ""))

    if _food_due(now, last_food_date):
        try:
            _run_food_dose()
            state["last_food_date"] = now.date().isoformat()
            state["last_food_at"] = now.isoformat()
            _set_state(state)
        except Exception as e:
            master_log.log_event(
                "scheduler_food_dose_failed",
                source="grow_scheduler.tick",
                pump=FOOD_PUMP_NAME,
                ml=FOOD_ML_PER_DAY,
                note=str(e),
            )
            print(f"[SCHED] food dose failed: {e}")


def run_forever() -> None:
    while not _stop_flag.is_set():
        tick()
        _stop_flag.wait(TICK_SECONDS)


def start() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return

    if os.environ.get("AMIGA_DISABLE_SCHEDULER") == "1":
        print("[SCHED] disabled via AMIGA_DISABLE_SCHEDULER=1")
        return

    _stop_flag.clear()
    _thread = threading.Thread(target=run_forever, name="amiga-grow-scheduler", daemon=True)
    _thread.start()
    print("[SCHED] started")


def stop() -> None:
    _stop_flag.set()
