import time
import sys
import argparse

try:
    from settings import PUMP_PINS, SIMULATE
except ImportError:
    print("Error: Could not import settings. Make sure you run this script from the backend directory:")
    print("cd /home/siyyo/Documents/arcs_foodi/AMiGA/backend && /home/siyyo/Documents/arcs_foodi/AMiGA/.venv/bin/python pump_diagnostic.py")
    sys.exit(1)

# Ensure user understands this requires a Python TMC2209 library to actually communicate over serial.
# The standard library for Raspberry Pi is: pip install TMC2209
try:
    from TMC_2209.TMC_2209_StepperDriver import *
    TMC_AVAILABLE = True
except ImportError:
    TMC_AVAILABLE = False


def print_mock_uart_diagnostic(pump_name):
    """
    Shows the user exactly what information the UART connection will provide
    once the single wire is plugged in and the library is installed.
    """
    print(f"\n--- 📡 UART Diagnostic Report for Pump: '{pump_name}' ---")
    
    # 1. Connection Status
    print("[1] Connection Status (Open Load Detection)")
    print("    > Motor Coil A Connected: True   (OK)")
    print("    > Motor Coil B Connected: False  (❌ WARNING: WIRE DISCONNECTED!)")
    
    # 2. Load & Stalls
    print("\n[2] StallGuard4™ Load Reading (0-1023)")
    print("    > Current Load Value:     450    (Pumping smoothly)")
    print("    > Stall Threshold:        50     (Will stop if load drops below 50)")

    # 3. Current & Power Configuration
    print("\n[3] Power Configuration (No screwdrivers needed)")
    print("    > Run Current (IRUN):     800 mA")
    print("    > Hold Current (IHOLD):   100 mA (Cooling down while idle)")
    print("    > Microstepping (MRES):   1/16   (Smooth motion)")

    # 4. Thermal diagnostics
    print("\n[4] Driver Temperature & Errors")
    print("    > Overtemperature Pre-Warning: False (120C+)")
    print("    > Overtemperature Error:       False (150C+ Shutdown)")
    print("    > Short to Ground (Coil A):    False")
    print("    > Short to Ground (Coil B):    False")
    print("    > Short to Power (Coils):      False")
    
    print("-" * 60)


def run_real_uart_diagnostic(pump_name, serial_port, address):
    """
    The actual code that runs when you plug the UART wire in and install the library.
    """
    print(f"\n[Connecting to TMC2209 for '{pump_name}' on {serial_port}, Address {address}]")
    
    try:
        # Initialize the TMC driver over Serial
        tmc = TMC_2209(pin_step=-1, pin_dir=-1, pin_en=-1) # We use lgpio for Step/Dir, just need UART here
        tmc.set_uart_pin(tx_pin=14, rx_pin=15) # Standard Pi UART pins
        tmc.set_motor_address(address)
        
        # Read Registers
        sg_result = tmc.get_stallguard_result()
        is_open_load_a, is_open_load_b = tmc.get_open_load()
        irun = tmc.get_run_current()
        ihold = tmc.get_hold_current()
        otpw, ot = tmc.get_overtemperature()
        s2ga, s2gb = tmc.get_short_to_ground()
        
        print(f"\n--- 📡 REAL UART Diagnostic Report for Pump: '{pump_name}' ---")
        print("[1] Connection Status")
        print(f"    > Motor Coil A Connected: {not is_open_load_a}")
        print(f"    > Motor Coil B Connected: {not is_open_load_b}")
        
        print("\n[2] StallGuard4™ Load Reading")
        print(f"    > Current Load Value:     {sg_result} (0=Stalled, 1023=No Load)")

        print("\n[3] Power Configuration")
        print(f"    > Run Current (IRUN):     {irun} mA")
        print(f"    > Hold Current (IHOLD):   {ihold} mA")

        print("\n[4] Driver Temperature & Errors")
        print(f"    > Overtemperature Warning: {otpw}")
        print(f"    > Overtemperature Error:   {ot}")
        print(f"    > Short to Ground (A/B):   {s2ga} / {s2gb}")
        print("-" * 60)
        
    except Exception as e:
        print(f"    ❌ Failed to communicate with TMC2209 driver over UART: {e}")
        print("       Check your wiring, baudrate, and ensure Serial is enabled in raspi-config.")


def main():
    parser = argparse.ArgumentParser(description="Pump TMC2209 UART Diagnostic Tool")
    parser.add_argument("--real", action="store_true", help="Attempt to run real UART hardware connection.")
    parser.add_argument("--port", type=str, default="/dev/ttyAMA0", help="Serial port to use (e.g. /dev/ttyAMA0)")
    args = parser.parse_args()

    print("==========================================================")
    print("       AMiGA PUMP - TMC2209 UART DIAGNOSTIC TOOL          ")
    print("==========================================================")
    print("This script queries the 'Smart' TMC2209 stepper drivers")
    print("for motor connection status, load (stalls), and config.")
    print("==========================================================\n")

    if args.real:
        if not TMC_AVAILABLE:
            print("⚠️ ERROR: The 'TMC2209' python library is not installed.")
            print("To run the REAL test, install it using the AMiGA virtual environment:")
            print("   /home/siyyo/Documents/arcs_foodi/AMiGA/.venv/bin/pip install TMC2209")
            sys.exit(1)
            
        print("Running REAL Hardware UART Tests...")
        # Assume addresses 0 and 1 for food and water pumps for this test
        address_map = {"food": 0, "water": 1} 
        for pump_name in PUMP_PINS.keys():
            addr = address_map.get(pump_name, 0)
            run_real_uart_diagnostic(pump_name, args.port, addr)
    else:
        print("Running in DEMO/INFORMATIONAL mode (Since the drivers aren't wired yet!)")
        print("Run with: `python3 pump_diagnostic.py --real` to test actual hardware.\n")
        
        for pump_name in PUMP_PINS.keys():
            print_mock_uart_diagnostic(pump_name)
            time.sleep(0.5)
            
        print("\nWhen you are ready to use this for real, just plug the UART wire in")
        print("and run `/home/siyyo/Documents/arcs_foodi/AMiGA/.venv/bin/pip install TMC2209`!")

if __name__ == "__main__":
    main()
