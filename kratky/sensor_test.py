import time
import board
import busio
import adafruit_tsl2561
import adafruit_sgp30

def init_i2c():
    """Initializes the I2C bus on the Raspberry Pi 5."""
    try:
        # specific to Pi 5, this usually maps to the standard GPIO pins 2 & 3
        i2c = board.I2C()  # uses board.SCL and board.SDA
        return i2c
    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize I2C bus. {e}")
        return None

def test_tsl2561(i2c_bus):
    """Initializes and reads from the TSL2561 Luminosity Sensor."""
    print("\n--- Testing TSL2561 (Light) ---")
    try:
        sensor = adafruit_tsl2561.TSL2561(i2c_bus)
        
        # Optional: Set gain to measure low light or bright light
        # sensor.gain = 0  # Low gain (bright light)
        # sensor.gain = 1  # High gain (low light)
        
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
    """Initializes and reads from the SGP30 Air Quality Sensor."""
    print("\n--- Testing SGP30 (Air Quality) ---")
    try:
        sensor = adafruit_sgp30.Adafruit_SGP30(i2c_bus)
        
        # Warm up note: SGP30 needs 15 seconds to provide valid data
        print("Initializing... (SGP30 requires a specific startup command)")
        sensor.iaq_init()
        
        eCO2 = sensor.eCO2
        tvoc = sensor.TVOC
        
        print(f"Status: SUCCESS")
        print(f"eCO2: {eCO2} ppm")
        print(f"TVOC: {tvoc} ppb")
        
        if eCO2 == 400 and tvoc == 0:
            print("NOTE: Reading is 400/0. This is the default baseline.")
            print("The sensor may need 15-30 seconds of runtime to calibrate.")
            
        return True
    except ValueError:
        print("Status: FAILED (Sensor not found at address 0x58)")
        return False
    except Exception as e:
        print(f"Status: ERROR ({e})")
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
            # We re-test every 2 seconds to act as a monitor
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