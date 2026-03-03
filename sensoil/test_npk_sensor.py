import minimalmodbus
import serial
import time

# 1. Identify port: usually /dev/ttyUSB0 on Raspberry Pi
PORT = '/dev/ttyUSB0'
SLAVE_ID = 1  # Default for almost all NPK sensors

# Initialize the sensor
sensor = minimalmodbus.Instrument(PORT, SLAVE_ID)
sensor.serial.baudrate = 9600  # Try 4800 if 9600 fails
sensor.serial.bytesize = 8
sensor.serial.parity = serial.PARITY_NONE
sensor.serial.stopbits = 1
sensor.serial.timeout = 1.0
sensor.mode = minimalmodbus.MODE_RTU

def read_npk():
    # Attempt Map A (Registers 30, 31, 32)
    try:
        print("Checking Register Map A (30-32)...")
        # read_registers(start_register, number_of_registers)
        data = sensor.read_registers(30, 3)
        return data
    except Exception:
        # Attempt Map B (Registers 4, 5, 6)
        try:
            print("Checking Register Map B (4-6)...")
            data = sensor.read_registers(4, 3)
            return data
        except Exception as e:
            print(f"Critical Error: {e}")
            return None

if __name__ == "__main__":
    result = read_npk()
    if result:
        print(f"Nitrogen (N): {result[0]} mg/kg")
        print(f"Phosphorus (P): {result[1]} mg/kg")
        print(f"Potassium (K): {result[2]} mg/kg")
    else:
        print("Final Troubleshooting: Swap A/B wires and check 12V Power.")