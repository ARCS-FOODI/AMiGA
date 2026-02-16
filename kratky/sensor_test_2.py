import time
import board
import busio
import adafruit_tsl2561
import adafruit_scd4x
import os

# Updated Path
DATA_FILE = "/home/foodi/Documents/AMiGA/kratky/sinfo"

def init_i2c():
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        return i2c
    except Exception as e:
        print(f"I2C Error: {e}")
        return None

def setup_scd41(scd4x_sensor):
    try:
        scd4x_sensor.stop_periodic_measurement()
        time.sleep(1)
        scd4x_sensor.start_periodic_measurement()
        return True
    except:
        return False

def main():
    # Ensure directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    i2c = init_i2c()
    if not i2c: return

    tsl = None
    scd4x = None
    
    try:
        tsl = adafruit_tsl2561.TSL2561(i2c)
    except:
        print("TSL2561 not found.")

    try:
        scd4x = adafruit_scd4x.SCD4X(i2c)
        setup_scd41(scd4x)
    except:
        print("SCD41 not found.")

    while True:
        try:
            lines = []
            if tsl:
                lines.append(f"Light: {tsl.lux if tsl.lux else 0:.1f} Lux")
            
            if scd4x and scd4x.data_ready:
                lines.append(f"CO2: {scd4x.CO2} ppm")
                lines.append(f"Temp: {scd4x.temperature:.1f} C")
                lines.append(f"Hum: {scd4x.relative_humidity:.1f} %")
            
            output_text = "\n".join(lines)
            
            # Atomic write: write to temp file then rename to avoid OBS reading empty file
            with open(DATA_FILE + ".tmp", "w") as f:
                f.write(output_text)
            os.replace(DATA_FILE + ".tmp", DATA_FILE)
            
            time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()