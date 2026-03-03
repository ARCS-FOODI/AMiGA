import serial
import time

PORT = '/dev/ttyUSB1'

try:
    # Open the port at 9600
    ser = serial.Serial(PORT, 9600, timeout=1)
    
    # The message to send
    test_msg = b'HELLO_RS485'
    print(f"Sending: {test_msg}")
    
    ser.write(test_msg)
    time.sleep(0.1) # Give the hardware a tiny bit of time to toggle
    
    # Try to read back what we sent
    response = ser.read(len(test_msg))
    
    if response == test_msg:
        print("LOOPBACK SUCCESS: The adapter is working perfectly!")
    else:
        print(f"LOOPBACK FAILED: Sent {test_msg}, but received {response}")
        print("If received is empty, the adapter's receiver is dead.")
        
    ser.close()
except Exception as e:
    print(f"Error: {e}")