import serial
import time

# Common ports: '/dev/ttyUSB0' on Pi, 'COM3' on Windows
PORT = '/dev/ttyUSB0' 

# Standard baud rates to test
BAUD_RATES = [4800, 9600, 14400, 19200, 38400, 115200]

# Modbus RTU Query: Read Device ID (Register 0x0000)
# This is a common "Hello" command for these NPK sensors
# Format: [Address, Function, Reg_High, Reg_Low, Data_High, Data_Low, CRC_Low, CRC_High]
QUERY = b'\x01\x03\x00\x00\x00\x01\x84\x0A' 

def scan_sensor():
    print(f"Starting scan on {PORT}...")
    
    for baud in BAUD_RATES:
        print(f"Testing {baud} bps...", end=" ", flush=True)
        try:
            with serial.Serial(PORT, baud, timeout=1, parity=serial.PARITY_NONE, stopbits=1, bytesize=8) as ser:
                ser.flushInput()
                ser.write(QUERY)
                time.sleep(0.2)
                
                response = ser.read(ser.in_waiting)
                
                if response:
                    print(f"\n[!] SUCCESS: Found sensor at {baud} bps!")
                    print(f"Raw Response: {response.hex().upper()}")
                    return baud
                else:
                    print("No response.")
                    
        except Exception as e:
            print(f"Error: {e}")
            
    print("\nScan complete. No sensor detected. Check wiring (A/B) and power (12V-24V).")
    return None

if __name__ == "__main__":
    scan_sensor()