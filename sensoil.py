import time
import board
import busio
import adafruit_bme680
#import adafruit_ads1x15.ads1115 as ADS
#from adafruit_ads1x15.analog_in import AnalogIn
from picamzero import Camera
import RPi.GPIO as GPIO
import gspread
from datetime import datetime
import os


from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


print("Script ran")

# ---------- SETTINGS ----------
DRIVE_FOLDER_ID = '1iOnB0KUDTNKRuHo55LPKTpORWarY-vtC'
TOKEN_PATH = 'credentials.json'
CLIENT_SECRET_PATH = 'raspberry_creds.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SLEEP_TIME = 600

# ---------- SENSOR SETUP ----------
SOIL_PIN1 = 17

SOIL_PIN2 = 27
SOIL_PIN3 = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(SOIL_PIN1, GPIO.IN)
GPIO.setup(SOIL_PIN2, GPIO.IN)
GPIO.setup(SOIL_PIN3, GPIO.IN)

i2c = busio.I2C(board.SCL, board.SDA)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
bme680.sea_level_pressure = 1013.25

## ---------- ADS1115 Water Conduct SENSOR SETUP ----------
## Specifying the amount of gain / can be adjusted
#ads = ADS.ADS1115(i2c)
#ads.gain = 1
#chan0 = AnalogIn(ads, ADS.P0)
##replace chan0, 1, 2 with tds_channel =
#chan1 = AnalogIn(ads, ADS.P0)
#chan2 = AnalogIn(ads, ADS.P0)

##Continuously printing out the values
#while True: 
#	print(f”MQ-135 Voltage: {chan.voltage}V”)
#	time.sleep(1)

cam = Camera()

# ---------- GOOGLE SHEETS SETUP ----------
gc = gspread.service_account(filename="/home/sensoil/raspberry_creds.json")
spreadsheet = gc.open_by_key("xxx")  
worksheet = spreadsheet.sheet1

# ---------- AUTHENTICATE GOOGLE DRIVE ----------
def authenticate_drive():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
    return creds

# ---------- UPLOAD IMAGE TO DRIVE ----------
def upload_file(file_path, folder_id, creds):
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    
    # Make the file publicly viewable
    service.permissions().create(fileId=file['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
    
    return file['webViewLink']

# ---------- MAIN LOOP ----------
def main():
    creds = authenticate_drive()
    print("Starting monitoring system...")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            temperature = round(bme680.temperature, 2)
            pressure = round(bme680.pressure, 2)
            humidity = round(bme680.humidity, 2)
            gas = round(bme680.gas, 2)
            altitude = round(bme680.altitude, 2)
            moisture1 = "Wet" if GPIO.input(SOIL_PIN1) == 0 else "Dry"
            moisture2 = "Wet" if GPIO.input(SOIL_PIN2) == 0 else "Dry"
            moisture3 = "Wet" if GPIO.input(SOIL_PIN3) == 0 else "Dry"
	## replace "Wet" if GPIO.input(SOIL_PIN1) == 0 else "Dry" with  “ round(chan0.voltage, 3)” “round(chan1.voltage, 3)” “round(chan2.voltage, 3)”
       ##modify this section

#tds_voltage = round(tds_channel.voltage, 3)
#tds_value = (133.42 * tds_voltage**3 - 255.86 * tds_voltage**2 + 857.39 * tds_voltage) * 0.5
#tds_value = round(tds_value, 2)

            # Take photo
            photo_filename = f"/home/sensoil/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cam.take_photo(photo_filename)

            # Upload photo and get link
            image_link = upload_file(photo_filename, DRIVE_FOLDER_ID, creds)
            print(f"Image uploaded: {image_link}")

            # Add data to Google Sheet
            worksheet.append_row([
                timestamp, temperature, pressure, humidity, gas, altitude,
                moisture1, moisture2, moisture3, image_link
            ])
	#print(f"Data logged: Voltage={tds_voltage}V | TDS={tds_value}ppm")
            print("Data logged successfully.")

            time.sleep(SLEEP_TIME)
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
