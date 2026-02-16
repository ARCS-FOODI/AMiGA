import time
import board
import busio
import adafruit_tsl2561
import adafruit_scd4x
import os
from datetime import datetime

# Paths
BASE_DIR = "/home/foodi/Documents/AMiGA/kratky"
DATA_FILE = os.path.join(BASE_DIR, "sinfo")
LOG_FILE = os.path.join(BASE_DIR, "sensor_log.csv")

def init_sensors():
    i2c = busio.I2C(board.SCL, board.SDA)
    tsl, scd4x = None, None
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
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Initialize Log CSV with headers if it doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("Timestamp,Lux,Temp_F,Humidity,CO2\n")

    tsl, scd4x = init_sensors()

    print(f"Logging started. Saving to {LOG_FILE}")

    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Read Light
            lux_val = f"{tsl.lux:.1f}" if (tsl and tsl.lux is not None) else "N/A"
            
            # Read Air (only updates if data_ready is True)
            temp_f, hum_val, co2_val = "N/A", "N/A", "N/A"
            
            if scd4x and scd4x.data_ready:
                temp_c = scd4x.temperature
                temp_f = f"{(temp_c * 9/5) + 32:.1f}"
                hum_val = f"{scd4x.relative_humidity:.1f}"
                co2_val = str(scd4x.CO2)

                # 1. Log to CSV (Scientific Data Collection)
                # We log inside this 'if' so we don't log duplicate data 5 times a second
                with open(LOG_FILE, "a") as f:
                    f.write(f"{timestamp},{lux_val},{temp_f},{hum_val},{co2_val}\n")

            # 2. Update the OBS display file (sinfo)
            output = (
                f"Lux: {lux_val} lx\n"
                f"Temp: {temp_f} °F\n"
                f"Hum: {hum_val} %\n"
                f"CO2: {co2_val} ppm"
            )
            
            with open(DATA_FILE + ".tmp", "w") as f:
                f.write(output)
            os.replace(DATA_FILE + ".tmp", DATA_FILE)

            # Sleep for 1 second as requested
            time.sleep(1)
            
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()