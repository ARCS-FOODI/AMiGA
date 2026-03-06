import time
import board
import busio
import adafruit_tsl2561
import adafruit_scd4x
import os
import minimalmodbus
from datetime import datetime  # Added for timestamp

# Specific Path and Filename
ENV_DATA_FILE = "/home/foodi/Documents/AMiGA/kratky/sinfo_env"
WATER_DATA_FILE = "/home/foodi/Documents/AMiGA/kratky/sinfo_water"
LOG_FILE = "/home/foodi/Documents/AMiGA/kratky/sensor_log.csv" # New Log File

def init_sensors():
    i2c = busio.I2C(board.SCL, board.SDA)
    tsl = None
    scd4x = None
    soil_sensor = None
    
    # Initialize I2C TSL2561
    try:
        tsl = adafruit_tsl2561.TSL2561(i2c)
    except Exception as e:
        print(f"TSL2561 Error: {e}")

    # Initialize I2C SCD41
    try:
        scd4x = adafruit_scd4x.SCD4X(i2c)
        scd4x.stop_periodic_measurement()
        time.sleep(1)
        scd4x.start_periodic_measurement()
    except Exception as e:
        print(f"SCD41 Error: {e}")

    # Initialize RS485 NPK Sensor
    try:
        soil_sensor = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
        soil_sensor.serial.baudrate = 9600
        soil_sensor.serial.timeout = 1
    except Exception as e:
        print(f"NPK RS485 Sensor Error: {e}")
        
    return tsl, scd4x, soil_sensor

def main():
    os.makedirs(os.path.dirname(ENV_DATA_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(WATER_DATA_FILE), exist_ok=True)
    tsl, scd4x, soil_sensor = init_sensors()

    # Define variables OUTSIDE the loop so they persist (prevents "N/A" flickering)
    lux_val = "N/A"
    temp_f = "N/A"
    hum_val = "N/A"
    co2_val = "N/A"
    
    # Soil Variables
    soil_moist = "N/A"
    soil_temp = "N/A"
    soil_ec = "N/A"
    soil_ph = "N/A"
    soil_n = "N/A"
    soil_p = "N/A"
    soil_k = "N/A"

    # Create CSV Header if file doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("Timestamp,Lux,Air_Temp_F,Humidity,CO2,Soil_Moisture,Soil_Temp_C,EC,pH,Nitrogen,Phosphorus,Potassium\n")

    # Time tracking for slower NPK reads
    last_soil_read = 0

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

            # 3. Update Soil (Slow - doing this every 5 seconds equivalent to old script so we don't spam modbus)
            current_time = time.time()
            if soil_sensor and (current_time - last_soil_read) >= 5:
                try:
                    ph = soil_sensor.read_register(6, functioncode=3) / 100.0
                    moisture = soil_sensor.read_register(18, functioncode=3) / 10.0
                    temperature = soil_sensor.read_register(19, functioncode=3, signed=True) / 10.0
                    ec = soil_sensor.read_register(21, functioncode=3)
                    
                    nitrogen = soil_sensor.read_register(30, functioncode=3)
                    phosphorus = soil_sensor.read_register(31, functioncode=3)
                    potassium = soil_sensor.read_register(32, functioncode=3)

                    soil_ph = f"{ph:.2f}"
                    soil_moist = f"{moisture:.1f}"
                    soil_temp = f"{temperature:.1f}"
                    soil_ec = f"{ec}"
                    soil_n = f"{nitrogen}"
                    soil_p = f"{phosphorus}"
                    soil_k = f"{potassium}"
                except Exception as e:
                    print(f"Modbus Read Error: {e}")
                last_soil_read = current_time

            # 4. Write to OBS Files (sinfo_env and sinfo_water)
            env_output = (
                f"=== ENVIRONMENT ===\n"
                f"Air Temp: {temp_f} °F\n"
                f"Hum: {hum_val} %\n"
                f"CO2: {co2_val} ppm\n"
                f"Lux: {lux_val} lx"
            )
            
            water_output = (
                f"=== WATER ===\n"
                f"Water Temp: {soil_temp} °C\n"
                f"pH: {soil_ph}\n"
                f"EC: {soil_ec} us/cm\n"
                f"NPK: {soil_n}-{soil_p}-{soil_k} mg/kg\n"
                f"Moist: {soil_moist} %"
            )

            with open(ENV_DATA_FILE + ".tmp", "w") as f:
                f.write(env_output)
            os.replace(ENV_DATA_FILE + ".tmp", ENV_DATA_FILE)

            with open(WATER_DATA_FILE + ".tmp", "w") as f:
                f.write(water_output)
            os.replace(WATER_DATA_FILE + ".tmp", WATER_DATA_FILE)

            # 5. Append to CSV Log (Records every second)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, "a") as f:
                f.write(f"{timestamp},{lux_val},{temp_f},{hum_val},{co2_val},{soil_moist},{soil_temp},{soil_ec},{soil_ph},{soil_n},{soil_p},{soil_k}\n")
            
            # Safe to sleep for just 1 second now because variables persist
            time.sleep(1)

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()