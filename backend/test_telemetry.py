import sys
import time
from water_telemetry import start, stop

print("Starting telemetry...")
start()
time.sleep(3)
print("Stopping telemetry...")
stop()
print("Done.")
