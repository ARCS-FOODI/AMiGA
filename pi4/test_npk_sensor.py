import minimalmodbus
import time

# Configuration
PORT = '/dev/ttyUSB0'  # The port that worked in mbpoll
SLAVE_ID = 1           # Your sensor's address
# Initialize the sensor
# minimalmodbus handles the 9600-8N1 settings by default
instrument = minimalmodbus.Instrument(PORT, SLAVE_ID)
instrument.serial.baudrate = 9600
instrument.serial.timeout = 1

def read_soil_data():
    try:
        # Read individual registers using function code 3 (0x03)
        ph = instrument.read_register(6, functioncode=3) / 100.0
        moisture = instrument.read_register(18, functioncode=3) / 10.0
        temperature = instrument.read_register(19, functioncode=3, signed=True) / 10.0
        ec = instrument.read_register(21, functioncode=3)
        
        nitrogen = instrument.read_register(30, functioncode=3)
        phosphorus = instrument.read_register(31, functioncode=3)
        potassium = instrument.read_register(32, functioncode=3)

        print("-" * 30)
        print(f"Soil Data @ {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"pH:          {ph:.2f}")
        print(f"Moisture:    {moisture:.1f}%")
        print(f"Temperature: {temperature:.1f}°C")
        print(f"EC:          {ec} us/cm")
        print(f"Nitrogen:    {nitrogen} mg/kg")
        print(f"Phosphorus:  {phosphorus} mg/kg")
        print(f"Potassium:   {potassium} mg/kg")
        
    except Exception as e:
        print(f"Failed to read sensor: {e}")

if __name__ == "__main__":
    print(f"Starting Soil Monitor on {PORT}...")
    while True:
        read_soil_data()
        time.sleep(5)  # Wait 5 seconds between readings