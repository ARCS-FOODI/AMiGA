# backend/control.py
from __future__ import annotations

from typing import Dict, Any, Optional
import time
import csv
from pathlib import Path
from datetime import datetime

from .settings import (
    DEFAULT_ADDR,
    DEFAULT_GAIN,
    DEFAULT_AVG,
    DEFAULT_VOTE_K,
    DEFAULT_HZ,
    DEFAULT_DIR,
    DEFAULT_IRR_SEC,
    DEFAULT_COOLDOWN_S,
    DEFAULT_THRESH,  
)
from . import sensors, pumps, master_log

# Paths for legacy logging (keeping for backward compatibility)
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOG_FILE = DATA_DIR / "moisture_cycles.csv"  


class IrrigationController:
    """
    Object-Oriented Controller for executing irrigation logic based on sensor readings.
    Decouples decision-making rules from the underlying hardware calls.
    """
    def __init__(self):
        pass

    def _ensure_log_file_has_header(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not LOG_FILE.exists():
            with LOG_FILE.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "pump", "target_threshold_v", "vote_k", "hz",
                    "irrigate_seconds", "over_threshold_count", "triggered",
                    "irrigated", "before_v0", "before_v1", "before_v2", "before_v3",
                    "after_v0", "after_v1", "after_v2", "after_v3"
                ])

    def _log_to_legacy_csv(self, result: Dict[str, Any]) -> None:
        self._ensure_log_file_has_header()
        ts = datetime.now().astimezone().isoformat()
        
        pump = result.get("pump")
        target_threshold = result.get("target_threshold")
        vote_k = result.get("vote_k")
        hz = result.get("hz")
        irrigate_seconds = result.get("irrigate_seconds")
        over = result.get("under_threshold_count")
        triggered = result.get("triggered", False)
        irrigated = result.get("irrigated", False)

        before = result.get("before") or {}
        before_readings = before.get("readings") or []
        before_volts = before_readings[0].get("voltages", [None]*4) if before_readings else [None]*4

        after = result.get("after")
        after_readings = after.get("readings") or [] if after else []
        after_volts = after_readings[0].get("voltages", [None]*4) if after_readings else [None]*4

        row = [
            ts, pump, target_threshold, vote_k, hz, irrigate_seconds, over,
            int(bool(triggered)), int(bool(irrigated)),
            before_volts[0], before_volts[1], before_volts[2], before_volts[3],
            after_volts[0], after_volts[1], after_volts[2], after_volts[3],
        ]

        with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def evaluate_cycle(
        self,
        pump_name: str,
        target_threshold: float = DEFAULT_THRESH, 
        vote_k: int = DEFAULT_VOTE_K,
        hz: float = DEFAULT_HZ,
        irrigate_seconds: float = DEFAULT_IRR_SEC,
        direction: str = DEFAULT_DIR,
        addr: int = DEFAULT_ADDR,
        gain: int = DEFAULT_GAIN,
        avg: int = DEFAULT_AVG,
    ) -> Dict[str, Any]:
        """
        One-step closed-loop cycle, querying the global SensorManager natively.
        """
        # 1. Temporarily configure main array for this specific read if needed
        # (Though ideally the UI just sets the global config, we allow overrides here)
        s_array = sensors.manager.main_array
        s_array.addr = addr
        s_array.gain = gain

        # Read "before" state
        before = s_array.snapshot(samples=1, interval=0.0, avg=avg, invert_do=False)
        before_volts = before["readings"][0]["voltages"]

        # Count sensors over threshold
        over = sum(1 for v in before_volts if v > target_threshold)
        triggered = over >= vote_k
        
        irrigated = False
        pump_action = None
        after = None

        if triggered and irrigate_seconds > 0:
            # 2. Command the PumpManager
            p_obj = pumps.manager.get_pump(pump_name)
            pump_action = p_obj.run_for_seconds(
                seconds=irrigate_seconds,
                hz=hz,
                direction=direction,
            )
            irrigated = True
            
            # Read "after" state
            after = s_array.snapshot(samples=1, interval=0.0, avg=avg, invert_do=False)

        result = {
            "target_threshold": target_threshold,
            "vote_k": vote_k,
            "pump": pump_name,
            "hz": hz,
            "direction": direction,
            "irrigate_seconds": irrigate_seconds,
            "before": before,
            "after": after,
            "under_threshold_count": over, # Keeping legacy key name
            "triggered": triggered,
            "irrigated": irrigated,
            "pump_action": pump_action,
        }

        try:
            self._log_to_legacy_csv(result)
        except Exception as e:
            print(f"[LOG] Failed to log control cycle to moisture_cycles.csv: {e}")

        try:
            master_log.log_event(
                "control_cycle",
                source="IrrigationController.evaluate_cycle",
                pump=pump_name,
                target_threshold_v=target_threshold,
                vote_k=vote_k,
                hz=hz,
                irrigate_seconds=irrigate_seconds,
                triggered=triggered,
                irrigated=irrigated,
                under_threshold_count=over,
                v0=before_volts[0],
                v1=before_volts[1],
                v2=before_volts[2],
                v3=before_volts[3],
            )
        except Exception as e:
            print(f"[LOG] Failed to log control_cycle to master.csv: {e}")

        return result

    def run_continuous(
        self,
        pump_name: str,
        target_threshold: float = DEFAULT_THRESH,
        vote_k: int = DEFAULT_VOTE_K,
        hz: float = DEFAULT_HZ,
        irrigate_seconds: float = DEFAULT_IRR_SEC,
        direction: str = DEFAULT_DIR,
        addr: int = DEFAULT_ADDR,
        gain: int = DEFAULT_GAIN,
        avg: int = DEFAULT_AVG,
        loop_interval: float = DEFAULT_COOLDOWN_S,
    ) -> None:
        """
        Blocking loop that continuously evaluates the cycle rules.
        """
        while True:
            result = self.evaluate_cycle(
                pump_name=pump_name,
                target_threshold=target_threshold,
                vote_k=vote_k,
                hz=hz,
                irrigate_seconds=irrigate_seconds,
                direction=direction,
                addr=addr,
                gain=gain,
                avg=avg,
            )

            before_volts = result["before"]["readings"][0]["voltages"]
            print(
                "[CONTROL] volts=",
                [f"{v:4.3f}" for v in before_volts],
                "over_thresh=", result["under_threshold_count"],
                "irrigated=", result["irrigated"],
            )

            time.sleep(loop_interval)


# Global instance for easy API import
controller = IrrigationController()

# --- Legacy Procedural Wrappers (For backward compatibility) ---
def control_cycle_once(*args, **kwargs):
    return controller.evaluate_cycle(*args, **kwargs)

def control_cycle_continuous(*args, **kwargs):
    return controller.run_continuous(*args, **kwargs)
