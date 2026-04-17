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

def get_recipe() -> Dict[str, Any]:
    return _read_json(RECIPE_FILE, default={})

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
    current_day = max(0, delta.days)
    
    active_phase = None
    for phase in recipe.get("phases", []):
        if phase.get("day_start", 0) <= current_day <= phase.get("day_end", 999):
            active_phase = phase
            break

    # Calculate total duration
    phases = recipe.get("phases", [])
    total_days = max((p.get("day_end", 0) for p in phases), default=0)

    state = _read_json(SCHED_STATE_FILE, default={"last_fluid_ts": 0, "running": False})
    is_running = state.get("running", False)

    return {
        "active": _thread is not None and _thread.is_alive(),
        "is_cycling": (active_phase is not None) and is_running,
        "current_day": current_day,
        "total_days": total_days,
        "phase": active_phase if is_running else None,
        "last_fluid_ts": state.get("last_fluid_ts", 0),
        "created_at": recipe.get("created_at")
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
        
    if fluid.get("trigger") == "moisture":
        state = _read_json(SCHED_STATE_FILE, default={"last_fluid_ts": 0})
        last_ts = state.get("last_fluid_ts", 0)
        cooldown_min = fluid.get("cooldown_minutes", 60)
        
        # Check cooldown
        if time.time() - last_ts < cooldown_min * 60:
            return
            
        # Use existing controller logic but inject recipe parameters
        try:
            pump_name = fluid.get("pump", "water")
            thresh_v = fluid.get("dry_threshold_v", 2.0)
            vk = fluid.get("vote_k", 2)
            dose_ml = fluid.get("dose_ml", 50.0)
            
            # We don't have an `evaluate_cycle` by ML natively yet, but we can compute seconds or just rely on pump's ml_per_sec natively:
            # Let's read sensors directly here to decide to dose. We can use the controller's logic or do it directly.
            
            s_array = sensors.manager.main_array
            before = s_array.snapshot(samples=1, interval=0.0, avg=5, invert_do=False)
            before_volts = before["readings"][0]["voltages"]
            
            over = sum(1 for v in before_volts if v > thresh_v)
            triggered = over >= vk
            
            if triggered:
                print(f"[SCHED] Moisture {before_volts} > {thresh_v}V. Dispensing {dose_ml}ml of {pump_name}.")
                p_obj = pumps.manager.get_pump(pump_name)
                p_obj.dispense_ml(dose_ml)
                state["last_fluid_ts"] = time.time()
                _write_json_atomic(SCHED_STATE_FILE, state)
        except Exception as e:
            print(f"[SCHED] Fluid control failed: {e}")

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
