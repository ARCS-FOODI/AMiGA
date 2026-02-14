import time
import board
import busio
import adafruit_tsl2561
import adafruit_sgp30

def debug_i2c_bus():
    """Scans the I2C bus to list all connected devices."""
    print("\n--- DEBUG: Scanning I2C Bus ---")
    
    # Force a software I2C scan (most robust method)
    try:
        # We use the default board SCL/SDA
        i2c = board.I2C()
        
        # We must lock the bus before scanning
        while not i2c.try_lock():
            pass
            
        found_addresses = i2c.scan()
        i2c.unlock()
        
        print(f"Devices found: {len(found_addresses)}")
        
        if len(found_addresses) == 0:
            print("RESULT: No devices found! Check your wiring.")
            return None
            
        print("Addresses found (Hex):", [hex(device_address) for device_address in found_addresses])
        
        # Check for our specific friends
        if 0x39 in found_addresses or 0x29 in found_addresses:
            print(" - TSL2561 (Light) confirmed present.")
        if 0x58 in found_addresses:
            print(" - SGP30 (Air) confirmed present.")
        else:
            print(" - SGP30 (0x58) MISSING. It is not replying.")
            
        return i2c
        
    except Exception as e:
        print(f"CRITICAL BUS ERROR: {e}")
        return None

def test_sgp30_robust(i2c_bus):
    """Tries to initialize SGP30 with extended error handling."""
    print("\n--- Testing SGP30 (Air Quality) ---")
    try:
        # 1. Initialize the library
        # Frequency Note: SGP30 sometimes prefers a slower clock (100kHz is standard)
        sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c_bus)
        
        print("SGP30 Object created. Attempting to read serial number...")
        # Reading serial is a good "soft" test of communication
        print(f"Serial: {sgp30.serial}")

        print("Initializing IAQ algorithm... (This resets the baseline)")
        sgp30.iaq_init()
        
        # Wait a moment for the first measurement to be ready
        time.sleep(1)
        
        print(f"eCO2: {sgp30.eCO2} ppm")
        print(f"TVOC: {sgp30.TVOC} ppb")
        print("Status: SUCCESS")
        return True

    except ValueError:
        print("Status: FAILED (Address 0x58 not responding)")
        print("Troubleshooting: Check the SCL/SDA wires specifically on the SGP30.")
        return False
    except OSError as e:
        print(f"Status: IO ERROR ({e})")
        print("Troubleshooting: This is often a 'Clock Stretching' issue or loose wire.")
        return False

def main():
    print("Starting Diagnostic Run...")
    
    # 1. Run the Scanner first
    i2c = debug_i2c_bus()
    
    if i2c:
        # 2. If bus is okay, run the specific sensor tests
        # We skip TSL2561 since you confirmed it works, focusing on SGP30
        test_sgp30_robust(i2c)
    
    print("\nDiagnostic Run Complete.")

if __name__ == "__main__":
    main()