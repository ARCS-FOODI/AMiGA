import time
import board
import busio
import adafruit_tsl2561
import adafruit_scd4x
import os
from datetime import datetime  # Added for timestamp

# Specific Path and Filename
DATA_FILE = "/home/foodi/Documents/AMiGA/kratky/sinfo"
LOG_FILE = "/home/foodi/Documents/AMiGA/kratky/sensor_log.csv" # New Log File

def init_sensors():
    i2c = busio.I2C(board.SCL, board.SDA)
    tsl = None
    scd4x = None
    
    try:
        tsl = adafruit_tsl2561.TSL2561(i2c)
    except Exception as e:
        print(f"TSL2561 Error: {e}")

    try:
        scd4x = adafruit_scd4x.SCD4X(i2c)
        scd4x.stop_periodic_measurement()
        time.sleep(1)
        scd4x.start_periodic_measurement()
    except Exception as e:
        print(f"SCD41 Error: {e}")
        
    return tsl, scd4x

def main():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    tsl, scd4x = init_sensors()

    # Define variables OUTSIDE the loop so they persist (prevents "N/A" flickering)
    lux_val = "N/A"
    temp_f = "N/A"
    hum_val = "N/A"
    co2_val = "N/A"

    # Create CSV Header if file doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("Timestamp,Lux,Temp_F,Humidity,CO2\n")

    while True:
        try:
            # 1. Update Lux (Fast - updates every second)
            if tsl and tsl.lux is not None:
                lux_val = f"{tsl.lux:.1f}"
            
            # 2. Update Air (Slow - checks every second, but updates variables only when ready)
            if scd4x and scd4x.data_ready:
                co2_val = str(scd4x.CO2)
                temp_c = scd4x.temperature
                temp_f = f"{(temp_c * 9/5) + 32:.1f}"
                hum_val = f"{scd4x.relative_humidity:.1f}"

            # 3. Write to OBS File (sinfo)
            output = (
                f"Lux: {lux_val} lx\n"
                f"Temp: {temp_f} °F\n"
                f"Hum: {hum_val} %\n"
                f"CO2: {co2_val} ppm"
            )

            with open(DATA_FILE + ".tmp", "w") as f:
                f.write(output)
            os.replace(DATA_FILE + ".tmp", DATA_FILE)

            # 4. Append to CSV Log (Records every second)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, "a") as f:
                f.write(f"{timestamp},{lux_val},{temp_f},{hum_val},{co2_val}\n")
            
            # Safe to sleep for just 1 second now because variables persist
            time.sleep(1)

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()