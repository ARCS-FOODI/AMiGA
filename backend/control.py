# backend/control.py
from __future__ import annotations

from typing import Dict, Any

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
)
from . import sensors, pumps


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
         - No pump run; "after" = None or same as before.

    Intended to be called repeatedly by the UI or a scheduler.
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

    return {
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
