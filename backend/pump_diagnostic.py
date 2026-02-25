import time
import sys
import argparse

try:
    from settings import PUMP_PINS
except ImportError:
    print("Error: Could not import settings. Make sure you run this script from the backend directory:")
    print("cd /home/siyyo/Documents/arcs_foodi/AMiGA/backend && /home/siyyo/Documents/arcs_foodi/AMiGA/.venv/bin/python pump_diagnostic.py")
    sys.exit(1)

# Ensure user understands this requires a Python TMC2209 library to actually communicate over serial.
# The standard library for Raspberry Pi is: pip install TMC2209-PY
try:
    from TMC2209_PY.TMC2209 import TMC2209Configure
    from TMC2209_PY.uart import UART
    TMC_AVAILABLE = True
except ImportError:
    TMC_AVAILABLE = False


def run_real_uart_diagnostic(pump_name, serial_port, baudrate, address, en_pin):
    """
    The actual code that runs when you plug the UART wire in and install the library.
    """
    print(f"\n[Connecting to TMC2209 for '{pump_name}' on {serial_port}, Address {address}]")
    
    try:
        # Initialize the TMC driver over Serial
        uart = UART(serial_port, baudrate)
        tmc = TMC2209Configure(uart, MS1=-1, MS2=-1, EN=en_pin, node_address=address)
        
        # Read Registers
        sg_result = tmc.read_SG_RESULT()
        tmc.read_DRV_STATUS()
        tmc.read_IHOLD_IRUN()
        
        print(f"\n--- 📡 REAL UART Diagnostic Report for Pump: '{pump_name}' ---")
        print("[1] Connection Status")
        print(f"    > Motor Coil A Connected: {not tmc.drv_status.ola}")
        print(f"    > Motor Coil B Connected: {not tmc.drv_status.olb}")
        
        print("\n[2] StallGuard4™ Load Reading")
        print(f"    > Current Load Value:     {sg_result} (0=Stalled, 1023=No Load)")

        print("\n[3] Power Configuration")
        print(f"    > Run Current (IRUN):     {tmc.ihold_irun.IRUN}")
        print(f"    > Hold Current (IHOLD):   {tmc.ihold_irun.IHOLD}")

        print("\n[4] Driver Temperature & Errors")
        print(f"    > Overtemperature Warning: {bool(tmc.drv_status.otpw)}")
        print(f"    > Overtemperature Error:   {bool(tmc.drv_status.ot)}")
        print(f"    > Short to Ground (A/B):   {bool(tmc.drv_status.s2ga)} / {bool(tmc.drv_status.s2gb)}")
        print("-" * 60)
        
    except Exception as e:
        print(f"    ❌ Failed to communicate with TMC2209 driver over UART: {e}")
        print("       Check your wiring, baudrate, and ensure Serial is enabled in raspi-config.")


def main():
    parser = argparse.ArgumentParser(description="Pump TMC2209 UART Diagnostic Tool")
    parser.add_argument("--port", type=str, default="/dev/serial0", help="Serial port to use (e.g. /dev/serial0)")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baud rate for UART communication (default: 115200)")
    parser.add_argument("--addr-food", type=int, default=0, help="UART address for the food pump TMC2209 (default: 0)")
    parser.add_argument("--addr-water", type=int, default=1, help="UART address for the water pump TMC2209 (default: 1)")
    args = parser.parse_args()

    print("==========================================================")
    print("       AMiGA PUMP - TMC2209 UART DIAGNOSTIC TOOL          ")
    print("==========================================================")
    print("This script queries the 'Smart' TMC2209 stepper drivers")
    print("for motor connection status, load (stalls), and config.")
    print("==========================================================\n")

    if not TMC_AVAILABLE:
        print("⚠️ ERROR: The 'TMC2209-PY' python library is not installed.")
        print("To run the test on hardware, install it using the AMiGA virtual environment:")
        print("   /home/siyyo/Documents/arcs_foodi/AMiGA/.venv/bin/pip install TMC2209-PY")
        sys.exit(1)
        
    print(f"Running Hardware UART Tests...")
    # Map addresses based on user arguments
    address_map = {"food": args.addr_food, "water": args.addr_water} 
    for pump_name, pins in PUMP_PINS.items():
        addr = address_map.get(pump_name, 0)
        en_pin = pins.get("EN", -1)
        run_real_uart_diagnostic(pump_name, args.port, args.baudrate, addr, en_pin)

if __name__ == "__main__":
    main()
