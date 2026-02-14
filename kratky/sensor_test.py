import time
import board
import busio
import adafruit_tsl2561
import adafruit_scd4x

def init_i2c():
    """Initializes the I2C bus using busio."""
    try:
        # Explicitly uses the Pi 5 GPIO pins
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
        print(f"Lux: {sensor.lux if sensor.lux else 0:.2f}")
        print(f"Broadband: {sensor.broadband}")
        print("Status: SUCCESS")
        return True
    except ValueError:
        print("Status: FAILED (TSL2561 not found)")
        return False

def test_scd41(i2c_bus):
    """Initializes and reads from the SCD41 CO2 Sensor."""
    print("\n--- Testing SCD41 (True CO2) ---")
    try:
        sensor = adafruit_scd4x.SCD4X(i2c_bus)
        
        # 1. Start the sensing loop (only needs to run once per power-up)
        # If it's already running, this command is ignored, which is fine.
        try:
            sensor.start_periodic_measurement()
        except:
            pass # It might already be running

        # 2. Check if data is ready
        # The SCD41 updates every 5 seconds. If we query it too fast,
        # data_ready will be False.
        if sensor.data_ready:
            print(f"CO2: {sensor.CO2} ppm")
            print(f"Temperature: {sensor.temperature:.1f} C")
            print(f"Humidity: {sensor.relative_humidity:.1f} %")
            print("Status: SUCCESS")
        else:
            print("Status: WAITING (Sensor is collecting data, try again in 5s)")
            
        return True
    except ValueError:
        print("Status: FAILED (SCD41 not found at address 0x62)")
        return False

def main():
    print("Starting Updated Sensor Check (TSL2561 + SCD41)...")
    
    i2c = init_i2c()
    if not i2c:
        return

    try:
        while True:
            print("\n" + "="*30)
            print(f"Time: {time.ctime()}")
            
            test_tsl2561(i2c)
            test_scd41(i2c)
            
            print("="*30)
            # We sleep 5 seconds because the SCD41 only updates that often
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user.")

if __name__ == "__main__":
    main()