import time
import board
import busio
import adafruit_bme680

i2c = busio.I2C(board.SCL, board.SDA)

bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)

bme680.sea_level_pressure = 1013.25

while True:
	print(f"Temperature: {bme680.temperature:.1f} degree C")
	print(f"Gas: {bme680.gas:.0f} ohm")
	print(f"Humidity: {bme680.humidity:.1f} %")
	print(f"pressure: {bme680.pressure:.1f} hPa")
	print(f"Altitude: {bme680.altitude:.2f} m\n")
	time.sleep(3)