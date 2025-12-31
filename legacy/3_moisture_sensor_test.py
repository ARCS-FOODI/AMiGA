import time
import board
import busio
import RPi.GPIO as GPIO
from datetime import datetime


SOIL_PIN1 = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOIL_PIN1, GPIO.IN)

SOIL_PIN2 = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOIL_PIN2, GPIO.IN)

SOIL_PIN3 = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOIL_PIN3, GPIO.IN)

try:
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        moisture_sensor1 = "No" if GPIO.input(SOIL_PIN1) else "Yes"
        moisture_sensor2 = "No" if GPIO.input(SOIL_PIN2) else "Yes"
        moisture_sensor3 = "No" if GPIO.input(SOIL_PIN3) else "Yes"
        
        print("sensor 1: ", moisture_sensor1)
        print("sensor 2: ", moisture_sensor2)
        print("sensor 3: ", moisture_sensor3)
        
        time.sleep(10)
except KeyboardInterrupt:
    print("Program stopped by user")  
finally:
    GPIO.cleanup()
            
print("Success")