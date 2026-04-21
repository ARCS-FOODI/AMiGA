# backend/grow_scheduler.py
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from zoneinfo import ZoneInfo
from . import light, pumps, sensors
from .control import controller

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RECIPE_FILE = DATA_DIR / "current_recipe.json"
SCHED_STATE_FILE = DATA_DIR / "scheduler_state.json"

# Settings
TZ_NAME = "America/Los_Angeles"
TICK_SECONDS = 20.0

_thread: Optional[threading.Thread] = None
_stop_flag = threading.Event()

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

DEFAULT_RECIPE = {
  "name": "Kale Microgreens",
  "phases": [
    {
      "day_start": 0,
      "day_end": 3,
      "name": "Germination (Blackout)",
      "lighting": {
        "mode": "off"
      },
      "fluid_control": {
        "pump": "water",
        "trigger": "moisture",
        "sensor_override": False,
        "dry_threshold_v": 4.0,
        "priming_v": 2.5,
        "super_dry_v": 5.3,
        "vote_k": 2,
        "dose_ml": 50,
        "hz": 10000,
        "cooldown_minutes": 60,
        "irrigate_at": [],
        "interval_hours": 24
      }
    },
    {
      "day_start": 3,
      "day_end": 10,
      "name": "Light Growth",
      "lighting": {
        "mode": "daynight",
        "on_time": "06:00",
        "off_time": "20:00"
      },
      "fluid_control": {
        "pump": "food",
        "trigger": "moisture",
        "sensor_override": False,
        "dry_threshold_v": 4.2,
        "priming_v": 2.5,
        "super_dry_v": 5.3,
        "vote_k": 2,
        "dose_ml": 200,
        "hz": 10000,
        "cooldown_minutes": 360,
        "notes": "MaxiGro 10-5-14",
        "irrigate_at": [],
        "interval_hours": 24
      }
    }
  ]
}

def _time_matches(target_hhmm: str, now: datetime) -> bool:
    """Checks if the current clock time matches HH:MM string."""
    try:
        return now.strftime("%H:%M") == target_hhmm
    except:
        return False

def get_recipe() -> Dict[str, Any]:
    recipe = _read_json(RECIPE_FILE, default={})
    if not recipe or "phases" not in recipe or not recipe["phases"]:
        return DEFAULT_RECIPE
    return recipe

def set_recipe(recipe: Dict[str, Any]) -> None:
    # Ensure created_at is present to track day 0
    if "created_at"  not in recipe:
        tz = ZoneInfo(TZ_NAME)
        recipe["created_at"] = datetime.now(tz).isoformat()
    _write_json_atomic(RECIPE_FILE, recipe)
    # Reset internal tracking state on new recipe and set running: True
    _write_json_atomic(SCHED_STATE_FILE, {"last_fluid_ts": 0, "running": True})

def stop_cycle() -> None:
    state = _read_json(SCHED_STATE_FILE, default={"last_fluid_ts": 0, "running": False})
    state["running"] = False
    _write_json_atomic(SCHED_STATE_FILE, state)

def get_grow_status() -> Dict[str, Any]:
    recipe = get_recipe()
    if not recipe:
        return {"active": False, "current_day": 0, "phase": None}
    
    tz = ZoneInfo(TZ_NAME)
    now = datetime.now(tz)
    try:
        created_at = datetime.fromisoformat(recipe.get("created_at", now.isoformat()))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=tz)
    except:
        created_at = now
        
    delta = now - created_at
    current_day_float = max(0, delta.total_seconds() / 86400.0)
    current_day = int(current_day_float)
    
    phases = recipe.get("phases", [])
    active_phase = None
    next_phase = None
    active_phase_index = -1

    for i, phase in enumerate(phases):
        # Precision Phase Transition: 
        # Compare current_day_float against phase boundaries [start, end)
        start = float(phase.get("day_start", 0))
        end = float(phase.get("day_end", 999))

        # Check if we are within this phase. 
        # For the very last phase, we allow it to be inclusive of the end day.
        is_last = (i == len(phases) - 1)
        if start <= current_day_float < end or (is_last and current_day_float == end):
            active_phase = phase
            active_phase_index = i
            if i + 1 < len(phases):
                next_phase = phases[i+1]
            break

    # Calculate total duration
    total_days = max((p.get("day_end", 0) for p in phases), default=0)

    state = _read_json(SCHED_STATE_FILE, default={"last_fluid_ts": 0, "running": False})
    is_running = state.get("running", False)

    # Add live moisture snapshot for UI "Relative Moisture" display
    current_voltages = []
    try:
        snap = sensors.manager.main_array.snapshot(samples=1, avg=3)
        current_voltages = snap["readings"][0]["voltages"]
    except:
        pass

    # Phase specific metrics
    phase_end_day = active_phase.get("day_end", 0) if active_phase else 0
    phase_remaining_days = max(0, phase_end_day - current_day_float) if active_phase else 0

    return {
        "active": _thread is not None and _thread.is_alive(),
        "is_cycling": (active_phase is not None) and is_running,
        "current_day": current_day,
        "current_day_float": round(current_day_float, 3),
        "total_days": total_days,
        "phase": active_phase if is_running else None,
        "next_phase": next_phase.get("name") if next_phase else None,
        "phase_end_day": phase_end_day,
        "phase_remaining_days": round(phase_remaining_days, 3),
        "last_fluid_ts": state.get("last_fluid_ts", 0),
        "created_at": recipe.get("created_at"),
        "current_voltages": current_voltages
    }

def tick() -> None:
    tz = ZoneInfo(TZ_NAME)
    now = datetime.now(tz)
    
    status = get_grow_status()
    phase = status.get("phase")
    if not phase:
        return

    # --- 1) Lighting Enforcement ---
    light_cfg = phase.get("lighting", {})
    l_mode = light_cfg.get("mode", "off")
    
    current_light = light.manager.main_light.get_config()
    if current_light.get("mode") != l_mode:
        if l_mode == "daynight":
            on_t = light_cfg.get("on_time", "06:00")
            off_t = light_cfg.get("off_time", "20:00")
            light.manager.main_light.set_config("daynight", on_t, off_t)
            light.manager.main_light.apply_daynight_now()
        elif l_mode == "off":
            light.manager.main_light.set_config("manual", "00:00", "00:00")
            light.manager.main_light.set_state(False)
        elif l_mode == "on":
            light.manager.main_light.set_config("manual", "00:00", "00:00")
            light.manager.main_light.set_state(True)

    # --- 2) Fluid Control Enforcement ---
    fluid = phase.get("fluid_control", {})
    if not fluid or fluid.get("dose_ml", 0) <= 0:
        return

    state = _read_json(SCHED_STATE_FILE, default={"last_fluid_ts": 0})
    last_ts = state.get("last_fluid_ts", 0)
    cooldown_min = fluid.get("cooldown_minutes", 60)
    
    # Check cooldown (safety guard for all modes)
    if time.time() - last_ts < cooldown_min * 60:
        return

    trigger = fluid.get("trigger", "moisture")
    pump_name = fluid.get("pump", "water")
    dose_ml = fluid.get("dose_ml", 50.0)
    req_hz = fluid.get("hz", 10000.0)
    triggered = False
    log_reason = ""

    if trigger == "moisture":
        sensor_override = fluid.get("sensor_override", False)
        if sensor_override:
            triggered = True
            log_reason = "Sensor override (forced)"
        else:
            try:
                thresh_v = fluid.get("dry_threshold_v", 2.0)
                vk = fluid.get("vote_k", 2)
                s_array = sensors.manager.main_array
                before = s_array.snapshot(samples=1, interval=0.0, avg=5, invert_do=False)
                before_volts = before["readings"][0]["voltages"]
                over = sum(1 for v in before_volts if v > thresh_v)
                triggered = over >= vk
                log_reason = f"Moisture {before_volts} > {thresh_v}V"
            except Exception as e:
                print(f"[SCHED] Moisture check failed: {e}")

    elif trigger == "scheduled":
        irrigate_at = fluid.get("irrigate_at", [])
        interval_h = fluid.get("interval_hours")

        if irrigate_at:
            # Clock-time check
            if any(_time_matches(t, now) for t in irrigate_at):
                triggered = True
                now_str = now.strftime("%H:%M")
                log_reason = f"Scheduled clock-time ({now_str})"
        elif interval_h and interval_h > 0:
            # Interval check
            if time.time() - last_ts >= interval_h * 3600:
                triggered = True
                log_reason = f"Scheduled interval ({interval_h}h elapsed)"

    if triggered:
        try:
            print(f"[SCHED] Trigger: {log_reason}. Dispensing {dose_ml}ml of {pump_name} at {req_hz}Hz.")
            p_obj = pumps.manager.get_pump(pump_name)
            p_obj.dispense_ml(dose_ml, hz=req_hz)
            state["last_fluid_ts"] = time.time()
            _write_json_atomic(SCHED_STATE_FILE, state)
        except Exception as e:
            print(f"[SCHED] Dispense failed: {e}")

def run_forever() -> None:
    print("[SCHED] Thread starting.")
    while not _stop_flag.is_set():
        tick()
        _stop_flag.wait(TICK_SECONDS)
    print("[SCHED] Thread stopping.")

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
