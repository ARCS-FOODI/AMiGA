import time
import board
import busio
import adafruit_tsl2561
import adafruit_sgp30

def init_i2c():
    """Initializes the I2C bus."""
    try:
        # Using explicit busio for better stability on Pi 5
        i2c = busio.I2C(board.SCL, board.SDA)
        return i2c
    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize I2C bus. {e}")
        return None

def test_tsl2561(i2c_bus):
    """Initializes and reads from the TSL2561 Luminosity Sensor."""
    print("\n--- Testing TSL2561 (Light) ---")
    try:
        sensor = adafruit_tsl2561.TSL2561(i2c_bus)
        
        lux = sensor.lux
        broadband = sensor.broadband
        infrared = sensor.infrared
        
        print(f"Status: SUCCESS")
        print(f"Lux: {lux if lux is not None else 0:.2f}")
        print(f"Broadband Light: {broadband}")
        print(f"Infrared Light: {infrared}")
        return True
    except ValueError:
        print("Status: FAILED (Sensor not found at address 0x39 or 0x29)")
        return False
    except Exception as e:
        print(f"Status: ERROR ({e})")
        return False

def test_sgp30(i2c_bus):
    """Initializes and reads from the SGP30 Air Quality Sensor at 0x48."""
    print("\n--- Testing SGP30 (Air Quality) ---")
    try:
        # UPDATED: Forcing the library to look at address 0x48
        sensor = adafruit_sgp30.Adafruit_SGP30(i2c_bus, address=0x48)
        
        print("Initializing... (SGP30 requires a specific startup command)")
        sensor.iaq_init()
        
        # SGP30 needs a moment to stabilize after init
        time.sleep(1)
        
        eCO2 = sensor.eCO2
        tvoc = sensor.TVOC
        
        print(f"Status: SUCCESS")
        print(f"eCO2: {eCO2} ppm")
        print(f"TVOC: {tvoc} ppb")
        
        if eCO2 == 400 and tvoc == 0:
            print("NOTE: Reading is 400/0 (Calibration Baseline).")
            
        return True
    except ValueError:
        print("Status: FAILED (Sensor not found at address 0x48)")
        return False
    except Exception as e:
        print(f"Status: ERROR ({e})")
        print("Note: If this error mentions 'register', it might be because 0x48 is the ADS1115, not the SGP30.")
        return False

def main():
    print("Starting Modular Sensor Check for Raspberry Pi 5...")
    
    # 1. Setup I2C
    i2c = init_i2c()
    if not i2c:
        return

    # 2. Main Loop
    try:
        while True:
            print("\n" + "="*30)
            print(f"Time: {time.ctime()}")
            
            test_tsl2561(i2c)
            test_sgp30(i2c)
            
            print("="*30)
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user.")

if __name__ == "__main__":
    main()