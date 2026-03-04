import minimalmodbus
import time

# Configuration
PORT = '/dev/ttyUSB0'  # The port that worked in mbpoll
SLAVE_ID = 1           # Your sensor's address
START_REG = 30         # The starting register that worked

# Initialize the sensor
# minimalmodbus handles the 9600-8N1 settings by default
instrument = minimalmodbus.Instrument(PORT, SLAVE_ID)
instrument.serial.baudrate = 9600
instrument.serial.timeout = 1

def read_soil_data():
    try:
        # Read 7 registers starting at 30
        # Function code 03 (Read Holding Registers) is used by default
        values = instrument.read_registers(START_REG, 7)

        print("-" * 30)
        print(f"Soil Data @ {time.strftime('%H:%M:%S')}")
        print(f"Moisture:    {values[0] / 10.0}%")
        print(f"Temperature: {values[1] / 10.0}°C")
        print(f"EC:          {values[2]} us/cm")
        print(f"pH:          {values[3] / 10.0}")
        print(f"Nitrogen:    {values[4]} mg/kg")
        print(f"Phosphorus:  {values[5]} mg/kg")
        print(f"Potassium:   {values[6]} mg/kg")
        
    except Exception as e:
        print(f"Failed to read sensor: {e}")

if __name__ == "__main__":
    print(f"Starting Soil Monitor on {PORT}...")
    while True:
        read_soil_data()
        time.sleep(5)  # Wait 5 seconds between readings