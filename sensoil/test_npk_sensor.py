import serial
import time

PORT = '/dev/ttyUSB1'
BAUDS = [4800, 9600, 19200, 38400, 115200]
# This hex string queries Device ID (Address 255) to return its own Address
# Query: [FF 03 00 00 00 01 91 D4]
BROADCAST_QUERY = b'\xff\x03\x00\x00\x00\x01\x91\xd4'

def scan():
    print(f"Starting deep scan on {PORT}...")
    for baud in BAUDS:
        print(f"Checking {baud} baud...", end=" ", flush=True)
        try:
            with serial.Serial(PORT, baud, timeout=0.5) as ser:
                ser.write(BROADCAST_QUERY)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                if response:
                    print(f"\n[!!!] RESPONSE FOUND: {response.hex().upper()}")
                    print(f"Your sensor is set to {baud} baud.")
                    return
                else:
                    print("no response.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    scan()