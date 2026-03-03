import minimalmodbus
import serial

# Configure the sensor
sensor = minimalmodbus.Instrument('/dev/ttyUSB1', 1) # Port and Slave Address (1)
sensor.serial.baudrate = 9600
sensor.serial.bytesize = 8
sensor.serial.parity = serial.PARITY_NONE
sensor.serial.stopbits = 1
sensor.serial.timeout = 1
sensor.mode = minimalmodbus.MODE_RTU

def read_npk():
    try:
        # Read 3 registers starting at 0x001E (30 decimal)
        # functioncode 3 is for 'Read Holding Registers'
        data = sensor.read_registers(30, 3, functioncode=3)
        
        n_val = data[0]
        p_val = data[1]
        k_val = data[2]
        
        print(f"Nitrogen (N): {n_val} mg/kg")
        print(f"Phosphorus (P): {p_val} mg/kg")
        print(f"Potassium (K): {k_val} mg/kg")
        
    except Exception as e:
        print(f"Failed to read sensor: {e}")

if __name__ == "__main__":
    read_npk()