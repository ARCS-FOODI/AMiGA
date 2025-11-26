#!/usr/bin/env python3
"""
Unified irrigation controller for Raspberry Pi 5
- Reads 4x soil moisture (HW-103/ADS1115 A0..A3)
- Drives a peristaltic pump via TMC2209 (STEP/DIR/EN using lgpio)

Scenarios (choose one subcommand):
  1) calibrate    → Run pump for N seconds at given Hz to measure mL/s
  2) sensors      → Print A0..A3 voltages + % moisture (and optional DO)
  3) full         → Auto-irrigate when at least K of 4 sensors < threshold%

Examples:
  python system.py calibrate --seconds 60 --hz 50000
  python system.py sensors --samples 20 --interval 1 --avg 5
  python system.py full --hz 50000 --threshold 40 --vote 2 \
       --irrigate-seconds 5 --cooldown 10

Hardware:
  ADS1115 I2C @ 0x48 (SDA=SDA, SCL=SCL)
  A0..A3 from HW-103 AO pins (or other analog moisture sensors)
  Optional HW-103 DO → BCM GPIO26 (Pin 37)  # UPDATED

  TMC2209/TMCxxxx driver (peristaltic pump):
    STEP = BCM17 (Pin 11)
    DIR  = BCM27 (Pin 13)
    EN   = BCM22 (Pin 15, active LOW)

Requirements:
  pip install adafruit-blinka adafruit-circuitpython-ads1x15
  sudo apt install -y python3-lgpio
  sudo raspi-config  # enable I2C

Note:
  - For volume-based runs, set ML_PER_SEC after calibration.
  - Default behavior for 'full' is seconds-based to avoid needing ML_PER_SEC.
"""
import argparse
import time
import statistics
from typing import List, Tuple

# ---- Sensor libs (I2C/ADS1115) ----
import board, busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ---- GPIO for motor driver ----
import lgpio

# ---------------- CONFIG (edit if needed) ----------------
# Motor pins (BCM numbering)
STEP_PIN = 17
DIR_PIN  = 27
EN_PIN   = 22
CHIP     = 0  # usually /dev/gpiochip0

# Pump calibration: set after you run 'calibrate'
ML_PER_SEC = 0.0  # measured_ml / seconds

# Sensor defaults
DEFAULT_ADDR   = 0x48
DEFAULT_GAIN   = 1          # ±4.096 V
DEFAULT_AVG    = 5
DEFAULT_INTSEC = 1.0
DEFAULT_SAMPLES= 30
DEFAULT_DRY_V  = 2.00
DEFAULT_WET_V  = 0.60
DEFAULT_THRESH = 35.0       # % moisture for classification, if needed
DEFAULT_DO_PIN = 26         # UPDATED: BCM26 = physical pin 37

# Motor defaults
DEFAULT_HZ     = 300
DEFAULT_DIR    = "forward"

# Full scenario defaults
DEFAULT_VOTE_K      = 2     # need at least K of 4 under threshold
DEFAULT_COOLDOWN_S  = 10.0  # wait after an irrigation cycle
DEFAULT_IRR_SEC     = 5.0   # seconds to run pump when triggered
# ---------------------------------------------------------

# ---------------- Utility: moisture mapping --------------
def v_to_pct(v: float, dry_v: float, wet_v: float) -> float:
    """Map voltage to 0–100% (dry→0, wet→100)."""
    if dry_v == wet_v:
        return 0.0
    pct = (dry_v - v) / (dry_v - wet_v) * 100.0
    return max(0.0, min(100.0, pct))

# Optional DO via lgpio (read-only)

def open_digital_gpio(do_pin: int, chip: int = CHIP):
    try:
        h = lgpio.gpiochip_open(chip)
        lgpio.gpio_claim_input(h, do_pin)
        return h
    except Exception:
        return None

def close_digital_gpio(handle):
    if handle is None:
        return
    try:
        lgpio.gpiochip_close(handle)
    except Exception:
        pass

def read_do_state(handle, do_pin: int, invert: bool) -> str | None:
    if handle is None:
        return None
    try:
        val = lgpio.gpio_read(handle, do_pin)
        if invert:
            val = 1 - val
        # Many HW-103 boards pull DO LOW when wet.
        return "WET" if val == 0 else "DRY"
    except Exception:
        return None

# --------------- Motor helpers (lgpio) -------------------

def gpio_setup_outputs(h):
    # Safe defaults: EN high (disabled)
    lgpio.gpio_claim_output(h, STEP_PIN, 0)
    lgpio.gpio_claim_output(h, DIR_PIN,  0)
    lgpio.gpio_claim_output(h, EN_PIN,   1)

def set_direction(h, dir_name: str):
    name = dir_name.lower()
    if name in ("fwd", "forward", "cw"):
        lgpio.gpio_write(h, DIR_PIN, 1)
    elif name in ("rev", "reverse", "ccw", "back"):
        lgpio.gpio_write(h, DIR_PIN, 0)
    else:
        raise ValueError("dir must be 'forward' or 'reverse'")

def enable_driver(h, enable: bool):
    lgpio.gpio_write(h, EN_PIN, 0 if enable else 1)  # EN active LOW

def step_for_seconds(h, hz: float, seconds: float):
    if hz <= 0:
        raise ValueError("hz must be > 0")
    if seconds <= 0:
        return
    half = 1.0 / (hz * 2.0)
    end_time = time.time() + seconds
    sp = STEP_PIN
    write = lgpio.gpio_write
    while time.time() < end_time:
        write(h, sp, 1); time.sleep(half)
        write(h, sp, 0); time.sleep(half)

# --------------- Motor run modes -------------------------

def motor_calibrate(run_seconds: float, hz: float):
    print(f"[CALIBRATE] {run_seconds:.1f}s @ {hz:.0f} Hz…")
    h = lgpio.gpiochip_open(CHIP)
    try:
        gpio_setup_outputs(h)
        set_direction(h, DEFAULT_DIR)
        enable_driver(h, True)
        try:
            step_for_seconds(h, hz, run_seconds)
        finally:
            enable_driver(h, False)
    finally:
        lgpio.gpiochip_close(h)
    print("[CALIBRATE] Done → measure mL, then set ML_PER_SEC = measured_ml / seconds")


def motor_run_seconds(seconds: float, hz: float, direction: str):
    print(f"[RUN] {seconds:.2f}s @ {hz:.0f} Hz dir={direction}")
    h = lgpio.gpiochip_open(CHIP)
    try:
        gpio_setup_outputs(h)
        set_direction(h, direction)
        enable_driver(h, True)
        try:
            step_for_seconds(h, hz, seconds)
        finally:
            enable_driver(h, False)
    finally:
        lgpio.gpiochip_close(h)
    print("[RUN] Complete.")


def motor_run_ml(ml: float, hz: float, direction: str):
    if ML_PER_SEC <= 0.0:
        raise RuntimeError("ML_PER_SEC is 0. Run 'calibrate' first or use seconds-based irrigation.")
    seconds = ml / ML_PER_SEC
    print(f"[RUN] {ml:.1f} mL @ {ML_PER_SEC:.3f} mL/s → {seconds:.2f}s @ {hz:.0f} Hz")
    motor_run_seconds(seconds, hz, direction)

# --------------- Sensor helpers -------------------------

def init_ads(addr: int, gain: int):
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=addr)
    ads.gain = gain
    # Create channels A0..A3 (ints used to match user's working setup)
    chans = [AnalogIn(ads, ch) for ch in (0, 1, 2, 3)]
    return ads, chans


def read_four_channels(chans, avg: int) -> List[float]:
    voltages: List[float] = []
    n = max(1, avg)
    for ch in chans:
        vals = [ch.voltage for _ in range(n)]
        voltages.append(statistics.mean(vals))
    return voltages


# --------------- Scenarios -------------------------------

def scenario_calibrate(args):
    motor_calibrate(args.seconds, args.hz)


def scenario_sensors(args):
    ads, chans = init_ads(args.addr, args.gain)
    # Always open DO now
    do_handle = open_digital_gpio(args.do_pin)
    try:
        print(f"[INFO] ADS1115 @ 0x{args.addr:02X}, gain={args.gain}")
        print(f"[INFO] Calib: DRY≈{args.dry:.2f} V, WET≈{args.wet:.2f} V; threshold={args.thresh_pct:.1f}%")
        print(f"[INFO] DO on BCM{args.do_pin}{' (invert)' if args.invert else ''}")  # UPDATED

        for i in range(1, args.samples + 1):
            volts = read_four_channels(chans, args.avg)
            pcts  = [v_to_pct(v, args.dry, args.wet) for v in volts]
            do_state = read_do_state(do_handle, args.do_pin, args.invert)
            a0 = f"A0={volts[0]:.3f}V (~{pcts[0]:5.1f}%)"
            status = f"| DO={do_state}" if do_state is not None else ""
            a123 = (
                f" | A1={volts[1]:.3f}V (~{pcts[1]:5.1f}%)"
                f" | A2={volts[2]:.3f}V (~{pcts[2]:5.1f}%)"
                f" | A3={volts[3]:.3f}V (~{pcts[3]:5.1f}%)"
            )
            print(f"{i:02d}/{args.samples}  {a0} {status}{a123}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[INFO] Stopped.")
    finally:
        close_digital_gpio(do_handle)


def scenario_full(args):
    """Closed-loop irrigation: if ≥K of 4 sensors are below threshold%, run pump."""
    # Init sensors
    ads, chans = init_ads(args.addr, args.gain)

    # Motor prep
    h = lgpio.gpiochip_open(CHIP)
    gpio_setup_outputs(h)
    set_direction(h, args.dir)

    print(f"[FULL] Threshold={args.threshold:.1f}% | Vote K={args.vote} | Hz={args.hz:.0f}\n"
          f"       Irrigate={'{:.1f}s'.format(args.irrigate_seconds) if args.irrigate_seconds>0 else str(args.irrigate_ml)+' mL'} | "
          f"Cooldown={args.cooldown:.1f}s")

    try:
        while True:
            volts = read_four_channels(chans, args.avg)
            pcts  = [v_to_pct(v, args.dry, args.wet) for v in volts]
            under = sum(1 for p in pcts if p < args.threshold)
            print(f"[FULL] Moisture %: {[f'{p:4.1f}' for p in pcts]}  → under={under}")

            if under >= args.vote:
                print("[FULL] Trigger: condition met → irrigating…")
                enable_driver(h, True)
                try:
                    if args.irrigate_ml > 0.0:
                        if ML_PER_SEC <= 0.0:
                            raise RuntimeError("ML_PER_SEC is 0. Calibrate or use --irrigate-seconds.")
                        seconds = args.irrigate_ml / ML_PER_SEC
                        step_for_seconds(h, args.hz, seconds)
                    else:
                        step_for_seconds(h, args.hz, args.irrigate_seconds)
                finally:
                    enable_driver(h, False)
                print(f"[FULL] Irrigation done. Cooling down {args.cooldown:.1f}s…")
                time.sleep(args.cooldown)
            else:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[FULL] Stopped by user.")
    finally:
        try:
            enable_driver(h, False)
        except Exception:
            pass
        lgpio.gpiochip_close(h)


# --------------- CLI ------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description="Pi5 irrigation controller (ADS1115 + TMC2209)")
    sub = p.add_subparsers(dest="cmd", required=True)

    # ---- calibrate ----
    pc = sub.add_parser("calibrate", help="Run pump for N seconds to measure mL/s")
    pc.add_argument("--seconds", type=float, required=True, help="Run time for calibration")
    pc.add_argument("--hz", type=float, default=DEFAULT_HZ, help="Step frequency (e.g., 50000)")
    pc.set_defaults(func=scenario_calibrate)

    # ---- sensors ----
    ps = sub.add_parser("sensors", help="Print A0..A3 voltages & % moisture")
    ps.add_argument("--addr", type=lambda x: int(x, 0), default=DEFAULT_ADDR)
    ps.add_argument("--gain", type=int, default=DEFAULT_GAIN)
    ps.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    ps.add_argument("--interval", type=float, default=DEFAULT_INTSEC)
    ps.add_argument("--avg", type=int, default=DEFAULT_AVG)
    ps.add_argument("--dry", type=float, default=DEFAULT_DRY_V)
    ps.add_argument("--wet", type=float, default=DEFAULT_WET_V)
    ps.add_argument("--thresh-pct", dest="thresh_pct", type=float, default=DEFAULT_THRESH)
    # Removed --digital flag; DO is always read
    ps.add_argument("--do-pin", type=int, default=DEFAULT_DO_PIN)
    ps.add_argument("--invert", action="store_true", help="Invert DO logic")
    ps.set_defaults(func=scenario_sensors)

    # ---- full ----
    pf = sub.add_parser("full", help="Auto-irrigate when ≥K sensors < threshold%")
    pf.add_argument("--addr", type=lambda x: int(x, 0), default=DEFAULT_ADDR)
    pf.add_argument("--gain", type=int, default=DEFAULT_GAIN)
    pf.add_argument("--avg", type=int, default=DEFAULT_AVG)
    pf.add_argument("--interval", type=float, default=DEFAULT_INTSEC, help="Poll interval when not irrigating")
    pf.add_argument("--dry", type=float, default=DEFAULT_DRY_V)
    pf.add_argument("--wet", type=float, default=DEFAULT_WET_V)
    pf.add_argument("--threshold", type=float, default=40.0, help="Moisture % threshold to trigger (<)")
    pf.add_argument("--vote", type=int, default=DEFAULT_VOTE_K, help="# of sensors below threshold to trigger")
    pf.add_argument("--hz", type=float, default=DEFAULT_HZ)
    pf.add_argument("--dir", default=DEFAULT_DIR)
    grp = pf.add_mutually_exclusive_group()
    grp.add_argument("--irrigate-seconds", type=float, default=DEFAULT_IRR_SEC)
    grp.add_argument("--irrigate-ml", type=float, default=0.0)
    pf.add_argument("--cooldown", type=float, default=DEFAULT_COOLDOWN_S)
    pf.set_defaults(func=scenario_full)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()