# backend/pumps.py
from __future__ import annotations

import time
import threading
from typing import Dict, Any, List

from .settings import PUMP_PINS, CHIP, DEFAULT_HZ, DEFAULT_DIR, SIMULATE_GPIO
from . import config_store, scale

if not SIMULATE_GPIO:
    import lgpio
else:
    class MockLgpio:
        def gpiochip_open(self, chip): return 999
        def gpiochip_close(self, handle): pass
        def gpio_claim_output(self, handle, pin, level): pass
        def gpio_write(self, handle, pin, level): pass
    lgpio = MockLgpio()

_on_dispense_callbacks = []

def register_on_dispense_callback(callback):
    """Register a function to be called when a pump finishes dispensing: cb(data: dict)"""
    if callback not in _on_dispense_callbacks:
        _on_dispense_callbacks.append(callback)

def _trigger_dispense_callbacks(result: Dict[str, Any]) -> None:
    """Helper to fire callbacks with dispensed data."""
    for cb in _on_dispense_callbacks:
        try:
            cb(result)
        except Exception as e:
            print(f"[PUMP] Telemetry callback error: {e}")


class StepperPump:
    """
    Object-Oriented representation of a Stepper Motor Pump.
    Manages its own GPIO state, calibration data, and execution lock.
    """
    def __init__(self, name: str, pins: Dict[str, int], chip: int = CHIP):
        self.name = name
        self.pins = pins
        self.chip = chip
        self._handle = None
        self._lock = threading.Lock()
        
        # Public state
        self.is_running = False
        
        # Load initial calibration
        self.calibration_rate = self._load_calibration()

    def _load_calibration(self) -> float:
        return config_store.get_pump_calibration(self.name) or 0.0

    def refresh_calibration(self) -> None:
        """Update calibration rate from store."""
        self.calibration_rate = self._load_calibration()

    def initialize(self, handle: int) -> None:
        """
        Bind the pump to an open GPIO handle and set safe default states
        (EN HIGH = disabled, STEP=0, DIR=0).
        """
        self._handle = handle
        lgpio.gpio_claim_output(self._handle, self.pins["STEP"], 0)
        lgpio.gpio_claim_output(self._handle, self.pins["DIR"], 0)
        if "EN" in self.pins:
            lgpio.gpio_claim_output(self._handle, self.pins["EN"], 0)

    def _set_direction(self, dir_name: str) -> None:
        """Internal helper to set the DIR pin."""
        if not self._handle:
            raise RuntimeError(f"Pump {self.name} is not initialized.")
            
        name = dir_name.lower()
        if name in ("fwd", "forward", "cw"):
            lgpio.gpio_write(self._handle, self.pins["DIR"], 1)
        elif name in ("rev", "reverse", "ccw", "back"):
            lgpio.gpio_write(self._handle, self.pins["DIR"], 0)
        else:
            raise ValueError("dir must be 'forward' or 'reverse'")

    def _enable_driver(self, enable: bool) -> None:
        """Internal helper to enable or disable the individual EN pin for this driver."""
        if not self._handle or "EN" not in self.pins:
            return
            
        # Try Active HIGH logic (1 awake, 0 sleep)
        val = 1 if enable else 0
        lgpio.gpio_write(self._handle, self.pins["EN"], val)

    def _step_loop(self, hz: float, seconds: float) -> None:
        """Blocking loop that pulses the STEP pin."""
        if hz <= 0:
            raise ValueError("hz must be > 0")
        if seconds <= 0:
            return

        sp = self.pins["STEP"]
        half = 1.0 / (hz * 2.0)
        end_time = time.time() + seconds
        write = lgpio.gpio_write

        while time.time() < end_time:
            if manager.emergency_stop_active:
                break
            write(self._handle, sp, 1)
            time.sleep(half)
            write(self._handle, sp, 0)
            time.sleep(half)

    def run_for_seconds(
        self, 
        seconds: float, 
        hz: float = DEFAULT_HZ, 
        direction: str = DEFAULT_DIR
    ) -> Dict[str, Any]:
        """
        Run the pump for a specific duration. Thread-safe to prevent concurrent overlapping runs.
        """
        if manager.emergency_stop_active:
            raise RuntimeError("Pump operations are currently LOCKED by emergency stop.")
            
        if not self._lock.acquire(blocking=False):
            raise RuntimeError(f"Pump '{self.name}' is already running.")

        self.is_running = True
        if SIMULATE_GPIO: print(f"[MOCK] Pump '{self.name}' running for {seconds}s at {hz}Hz ({direction})")
        try:
            self._set_direction(direction)
            # Notify global manager we are starting
            manager.request_enable_driver(True)
            self._step_loop(hz, seconds)
        finally:
            self.is_running = False
            # Notify global manager we have stopped
            manager.request_enable_driver(False)
            self._lock.release()

        result = {
            "pump": self.name,
            "seconds": seconds,
            "hz": hz,
            "direction": direction,
            "status": "ok",
        }
        # Note: If called from dispense_ml, this will be triggered there with enriched data.
        # But for direct path, we trigger here.
        import traceback
        frames = traceback.extract_stack()
        if not any(f.name == "dispense_ml" for f in frames):
            _trigger_dispense_callbacks(result)
            
        return result

    def dispense_ml(
        self, 
        ml: float, 
        hz: float = DEFAULT_HZ, 
        direction: str = DEFAULT_DIR
    ) -> Dict[str, Any]:
        """
        Run pump based on target volume, using current calibration (ml/s).
        """
        self.refresh_calibration() # Ensure we have the latest calibration
        if self.calibration_rate <= 0.0:
            raise RuntimeError(
                f"Pump '{self.name}' has ml_per_sec=0. Set calibration via /pump/calibration first."
            )

        seconds = ml / self.calibration_rate
        
        # Hand off to standard run function for execution
        result = self.run_for_seconds(seconds, hz, direction)
        
        # Override the log and return values to reflect a volume-based run
        result.update({
            "ml": ml,
            "rate_ml_per_sec": self.calibration_rate,
        })
        
        # NOTE: Pass dispensed liquid over to the simulated scale (assuming 1ml = 1g)
        try:
            scale.manager.add_water_g(ml)
        except Exception as e:
            print(f"[SCALE] Failed to add water weight: {e}")
        
        _trigger_dispense_callbacks(result)
            
        return result

    def calibrate(self, run_seconds: float, hz: float = DEFAULT_HZ) -> Dict[str, Any]:
        """Run pump for fixed time for manual volume measurement."""
        result = self.run_for_seconds(run_seconds, hz, DEFAULT_DIR)
        
        return {
            "pump": self.name,
            "run_seconds": run_seconds,
            "hz": hz,
            "message": (
                f"Calibration run complete. Measure mL in your cylinder, then "
                f"POST the measured ml_per_sec to /pump/calibration for '{self.name}'."
            ),
        }


def step_for_seconds_multi(handle: int, pump_names: List[str], hz: float, seconds: float) -> None:
    """Helper function to step multiple pumps simultaneously."""
    if hz <= 0:
        raise ValueError("hz must be > 0")
    if seconds <= 0:
        return

    half = 1.0 / (hz * 2.0)
    end_time = time.time() + seconds
    write = lgpio.gpio_write

    step_pins = [PUMP_PINS[p]["STEP"] for p in pump_names]

    while time.time() < end_time:
        if manager.emergency_stop_active:
            break
        for sp in step_pins:
            write(handle, sp, 1)
        time.sleep(half)
        for sp in step_pins:
            write(handle, sp, 0)
        time.sleep(half)


class PumpManager:
    """
    Global manager for all pumps. Handles the GPIO chip lifecycle and multi-pump operations.
    """
    def __init__(self, chip_index: int = CHIP):
        self.chip_index = chip_index
        self._handle = None
        self.pumps: Dict[str, StepperPump] = {}
        
        self.emergency_stop_active = False
        self._manager_lock = threading.Lock()
        
        # Create instances
        for name, pins in PUMP_PINS.items():
            self.pumps[name] = StepperPump(name, pins, self.chip_index)

    def startup(self) -> None:
        """Open GPIO chip and initialize all pump pins and their EN pins."""
        self._handle = lgpio.gpiochip_open(self.chip_index)

        for pump in self.pumps.values():
            pump.initialize(self._handle)

    def shutdown(self) -> None:
        """Safely disable all pumps and release the GPIO chip."""
        self.emergency_stop_active = True
        if self._handle is not None:
            # Ensure all EN pins are put to sleep
            for pump in self.pumps.values():
                if "EN" in pump.pins:
                    lgpio.gpio_write(self._handle, pump.pins["EN"], 0)
            lgpio.gpiochip_close(self._handle)
            self._handle = None
            
    def set_emergency_stop(self, active: bool) -> None:
        self.emergency_stop_active = active
            
    def request_enable_driver(self, enable: bool) -> None:
        """
        [DEPRECATED/REMOVED]
        EN pins are now managed individually by StepperPump objects.
        """
        pass

    def get_pump(self, name: str) -> StepperPump:
        if name not in self.pumps:
            raise ValueError(f"Unknown pump '{name}'")
        return self.pumps[name]

    def run_multi_seconds(
        self, 
        pump_names: List[str], 
        seconds: float, 
        hz: float = DEFAULT_HZ, 
        direction: str = DEFAULT_DIR
    ) -> Dict[str, Any]:
        """Run multiple pumps simultaneously for the same duration."""
        if self.emergency_stop_active:
            raise RuntimeError("Pump operations are currently LOCKED by emergency stop.")
            
        if not self._handle:
            raise RuntimeError("PumpManager not initialized.")

        active_pumps = [self.get_pump(p) for p in pump_names]
        
        # Try to acquire locks for all requested pumps
        acquired_locks = []
        try:
            for p in active_pumps:
                if p._lock.acquire(blocking=False):
                    acquired_locks.append(p)
                else:
                    raise RuntimeError(f"Pump '{p.name}' is already running.")
            
            # Setup all
            for p in active_pumps:
                p.is_running = True
                p._set_direction(direction)
                p._enable_driver(True)
                
            # Run block
            step_for_seconds_multi(self._handle, pump_names, hz, seconds)
            
        finally:
            # Teardown all
            for p in acquired_locks:
                p._enable_driver(False)
                p.is_running = False
                p._lock.release()

        result = {
            "pumps": pump_names,
            "seconds": seconds,
            "hz": hz,
            "direction": direction,
            "status": "ok",
        }
        # Multi-pump events use a special pump name "multi:{names}"
        result["pump"] = f"multi:{','.join(pump_names)}"
        _trigger_dispense_callbacks(result)

        return result


# Global singleton
manager = PumpManager()

def _ensure_manager_started():
    if manager._handle is None:
        manager.startup()

def run_pump_seconds(pump: str, seconds: float, hz: float = DEFAULT_HZ, direction: str = DEFAULT_DIR) -> Dict[str, Any]:
    _ensure_manager_started()
    return manager.get_pump(pump).run_for_seconds(seconds, hz, direction)

def run_pumps_seconds(pumps_list: List[str], seconds: float, hz: float = DEFAULT_HZ, direction: str = DEFAULT_DIR) -> Dict[str, Any]:
    _ensure_manager_started()
    return manager.run_multi_seconds(pumps_list, seconds, hz, direction)

def calibrate_pump_seconds(pump: str, run_seconds: float, hz: float = DEFAULT_HZ) -> Dict[str, Any]:
    _ensure_manager_started()
    return manager.get_pump(pump).calibrate(run_seconds, hz)

def run_pump_ml(pump: str, ml: float, hz: float = DEFAULT_HZ, direction: str = DEFAULT_DIR) -> Dict[str, Any]:
    _ensure_manager_started()
    return manager.get_pump(pump).dispense_ml(ml, hz, direction)
