import time
import board
import busio
import adafruit_tsl2561
import adafruit_scd4x
import os

# Specific Path and Filename
DATA_FILE = "/home/foodi/Documents/AMiGA/kratky/sinfo"

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

    while True:
        try:
            # Gather values or set to N/A
            lux_val = f"{tsl.lux:.1f}" if (tsl and tsl.lux is not None) else "N/A"
            
            temp_val = "N/A"
            hum_val = "N/A"
            co2_val = "N/A"
            
            if scd4x and scd4x.data_ready:
                co2_val = str(scd4x.CO2)
                temp_val = f"{scd4x.temperature:.1f}"
                hum_val = f"{scd4x.relative_humidity:.1f}"

            # Format EXACTLY as requested
            output = (
                f"Lux: {lux_val}\n"
                f"Temp: {temp_val}\n"
                f"Hum: {hum_val}\n"
                f"CO2: {co2_val}"
            )

            # Atomic write to prevent OBS reading a partial file
            with open(DATA_FILE + ".tmp", "w") as f:
                f.write(output)
            os.replace(DATA_FILE + ".tmp", DATA_FILE)
            
            time.sleep(5)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()