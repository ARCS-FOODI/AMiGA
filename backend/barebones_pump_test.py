import argparse
import time
import sys

# Attempt to load the settings module natively.
try:
    from settings import PUMP_PINS, CHIP
except ImportError:
    print("Error: Could not import settings. Make sure you run this script from the backend directory:")
    print("cd /home/siyyo/Documents/arcs_foodi/AMiGA/backend && /home/siyyo/Documents/arcs_foodi/AMiGA/.venv/bin/python barebones_pump_test.py")
    sys.exit(1)

try:
    import lgpio
except ImportError:
    print("Error: lgpio is not installed in this environment.")
    print("Please ensure you are using the virtual environment or install lgpio.")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Barebones Pump Stepper Test Toolkit")
    pump_names = list(PUMP_PINS.keys())
    parser.add_argument("--pump", type=str, required=True, choices=pump_names, 
                        help=f"Name of the pump to test, options: {pump_names}")
    parser.add_argument("--hz", type=float, default=1000, help="Stepping frequency (Hz), default 1000")
    parser.add_argument("--sec", type=float, default=2.0, help="Duration to run in seconds, default 2.0")
    parser.add_argument("--dir", type=int, default=1, choices=[0, 1], help="Direction (1 for forward, 0 for reverse), default 1")
    return parser.parse_args()


def test_pump(pump_name, duration_sec, hz, direction):
    pins = PUMP_PINS[pump_name]
    step_pin = pins.get("STEP")
    dir_pin = pins.get("DIR")
    en_pin = pins.get("EN")

    if step_pin is None or dir_pin is None:
        print(f"Error: Pump '{pump_name}' is missing STEP or DIR pins in settings.py")
        return

    print(f"\n[Barebones Pump Test] Testing '{pump_name}' pump")
    print(f" - STEP Pin: {step_pin}")
    print(f" - DIR Pin:  {dir_pin}")
    if en_pin is not None:
        print(f" - EN Pin:   {en_pin}")
    
    print(f" - Duration: {duration_sec} seconds")
    print(f" - Speed:    {hz} Hz")
    print(f" - Direction: {'Forward (1)' if direction >= 1 else 'Reverse (0)'}")
    print(f" - GPIO Chip: {CHIP}")
    print("\nInitializing GPIO...")

    try:
        # Open chip directly
        handle = lgpio.gpiochip_open(CHIP)
    except Exception as e:
        print(f"Error: Could not open gpiochip {CHIP}: {e}")
        return

    try:
        # Claim outputs and set initial low state
        lgpio.gpio_claim_output(handle, step_pin, 0)
        lgpio.gpio_claim_output(handle, dir_pin, 0)

        # If EN is present, claim it and disable it (EN is usually active LOW, so 1 = disabled)
        if en_pin is not None:
            lgpio.gpio_claim_output(handle, en_pin, 1) 

        # Set direction
        lgpio.gpio_write(handle, dir_pin, direction)

        # Enable driver
        if en_pin is not None:
            lgpio.gpio_write(handle, en_pin, 0)

        print("Running the pump now...")
        
        half_delay = 1.0 / (hz * 2.0)
        end_time = time.time() + duration_sec
        steps_taken = 0
        
        while time.time() < end_time:
            lgpio.gpio_write(handle, step_pin, 1)
            time.sleep(half_delay)
            lgpio.gpio_write(handle, step_pin, 0)
            time.sleep(half_delay)
            steps_taken += 1

        print(f"Test complete. Steps taken (approx): {steps_taken}")

    except Exception as e:
        print(f"An error occurred during test: {e}")
    finally:
        # Clean up and disable driver
        if en_pin is not None:
            try:
                lgpio.gpio_write(handle, en_pin, 1)
            except Exception:
                pass
        lgpio.gpiochip_close(handle)
        print("GPIO resources released.")


def main():
    args = parse_args()
    try:
        test_pump(args.pump, args.sec, args.hz, args.dir)
    except KeyboardInterrupt:
        print("\nTest interrupted by user. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
