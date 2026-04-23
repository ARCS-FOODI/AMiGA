import time
import board
import busio
import adafruit_tsl2561
import adafruit_scd4x

def init_i2c():
    """Initializes the I2C bus."""
    try:
        # Explicitly uses the Pi 5 GPIO pins
        i2c = busio.I2C(board.SCL, board.SDA)
        return i2c
    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize I2C bus. {e}")
        return None

def setup_scd41(scd4x_sensor):
    """
    Forces the SCD41 into a known clean state.
    Returns True if successful, False if it times out.
    """
    print(" >> SCD41: Stopping any previous measurements...")
    try:
        scd4x_sensor.stop_periodic_measurement()
    except:
        # If it wasn't measuring, this might fail, which is fine.
        pass
    
    time.sleep(1) # Give it a second to breathe
    
    print(" >> SCD41: Starting periodic measurements...")
    scd4x_sensor.start_periodic_measurement()
    
    print(" >> SCD41: Waiting for first reading (this takes 5-10 seconds)...")
    
    # We will wait up to 15 seconds for the first packet
    start_time = time.time()
    while time.time() - start_time < 15:
        if scd4x_sensor.data_ready:
            print(" >> SCD41: First data received! Sensor is active.")
            return True
        time.sleep(1)
        print("    ... waiting for data ...")
        
    print(" >> SCD41 ERROR: Timed out waiting for data.")
    return False

def main():
    print("Starting Robust Sensor Check...")
    
    i2c = init_i2c()
    if not i2c:
        return

    # --- SENSOR SETUP ---
    tsl = None
    scd4x = None
    
    # Setup TSL2561
    try:
        tsl = adafruit_tsl2561.TSL2561(i2c)
    except ValueError:
        print("ERROR: TSL2561 not found.")

    # Setup SCD41
    try:
        scd4x = adafruit_scd4x.SCD4X(i2c)
        if setup_scd41(scd4x) == False:
            print("WARNING: SCD41 is connected but not returning data.")
    except ValueError:
        print("ERROR: SCD41 not found at address 0x62.")

    # --- MAIN LOOP ---
    print("\n--- Entering Main Loop (Updates every 5s) ---")
    while True:
        try:
            # 1. Read Light
            if tsl:
                print(f"Light: {tsl.lux if tsl.lux else 0:.1f} Lux")
            
            # 2. Read Air
            if scd4x and scd4x.data_ready:
                print(f"CO2:   {scd4x.CO2} ppm")
                print(f"Temp:  {scd4x.temperature:.1f} C")
                print(f"Hum:   {scd4x.relative_humidity:.1f} %")
            elif scd4x:
                print("CO2:   (No new data this cycle)")
            
            print("-" * 20)
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"Loop Error: {e}")

if __name__ == "__main__":
    main()