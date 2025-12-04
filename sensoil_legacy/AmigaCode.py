import os, time, csv, signal, datetime
import serial, RPi.GPIO as GPIO, smbus
import board, busio
import gspread
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15 import ads1115 as ADS
import adafruit_scd4x
from picamzero import Camera

# ---- Google Drive API (for image upload) ----
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

print("Script ran")

# ========================= USER CONFIG =========================
# Google Sheets
SERVICE_ACCOUNT_FILE = "/home/sensoil/raspberry_creds.json"     # <-- change
SHEET_ID             = "1OC5V8gO9rsCw6s7kmA14LkwaMYxl2B4F0VYINSpyAGY"                      # <-- change
SHEET_TAB            = "Sheet1"                                  # <-- change or keep

# Google Drive (for image upload)
DRIVE_FOLDER_ID     = '1iOnB0KUDTNKRuHo55LPKTpORWarY-vtC'                     # <-- change
TOKEN_PATH          = 'token4.json'           # caches user token
CLIENT_SECRET_PATH  = 'raspberry_creds.json'       # OAuth client secret
SCOPES              = ['https://www.googleapis.com/auth/drive.file']

# Loop cadence
INTERVAL_SECONDS     = 10

# Use SCD41 temperature for EC compensation
USE_SCD41_TEMP       = True

# ADS1115 channel mapping
TDS_CH               = ADS.P0   # TDS v1.0 on A0
MQ135_CH             = ADS.P1   # optional MQ-135 on A1

# Light sensor I2C address (raw channels)
LUX_ADDR             = 0x39

# RS485 (Modbus RTU) for NPK sensor
SERIAL_PORT          = "/dev/serial0"  # or "/dev/ttyS0"
BAUDRATE             = 9600
PARITY               = serial.PARITY_NONE
STOPBITS             = serial.STOPBITS_ONE
BYTESIZE             = serial.EIGHTBITS
TIMEOUT              = 0.4
SLAVE_ADDR           = 1
DE_RE_GPIO           = 18
HOLDING_START        = 0x001E     # adjust per sensor
HOLDING_COUNT        = 6
SCALE_N = SCALE_P = SCALE_K = 1.0

# TDS processing
CAL_FACTOR           = 1.00       # adjust during calibration
SAMPLES_PER_READ     = 10
PER_SAMPLE_DELAY     = 0.01       # seconds between ADS samples
# ===============================================================

_running = True
def _stop(_sig, _frm):
    global _running
    _running = False
signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)

# ---------------- Google Sheets helpers ----------------
def init_sheets():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(SHEET_TAB)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=SHEET_TAB, rows=1000, cols=20)
    return ws

def append_row_safely(ws, row):
    try:
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        print(f"[upload error] {e}")
        return False

# ---------------- Google Drive (OAuth) ----------------
def authenticate_drive():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
    return creds

def upload_file(file_path, folder_id, creds):
    """Upload a file to Drive → make public → return webViewLink"""
    service = build("drive", "v3", credentials=creds)
    file_metadata = {"name": os.path.basename(file_path), "parents": [folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    file  = service.files().create(body=file_metadata, media_body=media,
                                   fields="id, webViewLink").execute()
    # Public read
    service.permissions().create(fileId=file["id"],
                                 body={"type":"anyone","role":"reader"}).execute()
    return file["webViewLink"]

# ---------------- Modbus / RS485 for NPK ----------------
def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            lsb = crc & 1
            crc >>= 1
            if lsb:
                crc ^= 0xA001
    return crc & 0xFFFF

def build_read_holding(addr: int, start: int, count: int) -> bytes:
    pdu = bytes([addr, 0x03, (start>>8)&0xFF, start&0xFF, (count>>8)&0xFF, count&0xFF])
    crc = crc16_modbus(pdu)
    return pdu + bytes([crc & 0xFF, (crc >> 8) & 0xFF])  # lo, hi

class RS485:
    def __init__(self):
        self.ser = serial.Serial(
            port=SERIAL_PORT, baudrate=BAUDRATE, parity=PARITY,
            stopbits=STOPBITS, bytesize=BYTESIZE, timeout=TIMEOUT
        )
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DE_RE_GPIO, GPIO.OUT, initial=GPIO.LOW)  # RX default

    def close(self):
        try:
            self.ser.close()
        finally:
            GPIO.cleanup(DE_RE_GPIO)

    def _tx(self, data: bytes):
        GPIO.output(DE_RE_GPIO, GPIO.HIGH)
        time.sleep(0.001)
        self.ser.write(data)
        self.ser.flush()
        char_time = 11/self.ser.baudrate
        tx_time = char_time*len(data)+char_time*2
        time.sleep(tx_time)
        GPIO.output(DE_RE_GPIO, GPIO.LOW)

    def _read_exact(self, n: int) -> bytes:
        """Read exactly n bytes or return fewer if timed out."""
        buf = bytearray()
        while len(buf) < n:
            chunk = self.ser.read(n - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        return bytes(buf)

    def read_regs(self, addr: int, start: int, count: int):
        req = build_read_holding(addr, start, count)
        #print("TX:", req.hex())  # DEBUG
        self._tx(req)

        head = self._read_exact(3)  # addr, func, nbytes
        #print("RX head:", head.hex(), "len:", len(head))  # DEBUG
        if len(head) < 3:
            return None

        recv_addr, func, nbytes = head

        if recv_addr != addr:
        # Different slave replied or line noise
            print(f"Unexpected addr: {recv_addr}")
            return None

    # Exception response: addr, func|0x80, ex_code, CRC_lo, CRC_hi
        if func & 0x80:
            ex = self._read_exact(3)  # ex_code + CRC
            print("Modbus exception:", (func, ex.hex()))
            return None

        rest = self._read_exact(nbytes + 2)  # data + CRC
        print("RX rest:", rest.hex(), "len:", len(rest))  # DEBUG

        if len(rest) < nbytes + 2:
            return None

        reply = head + rest

    # CRC check (low byte first in RTU)
        calc = crc16_modbus(reply[:-2])
        recv_crc = reply[-2] | (reply[-1] << 8)
        if calc != recv_crc:
            print(f"CRC mismatch: calc=0x{calc:04X}, recv=0x{recv_crc:04X}")
            return None

        if nbytes % 2:
            print(f"Unexpected byte count {nbytes} (should be even)")
            return None

        data = reply[3:3+nbytes]
        regs = [(data[i] << 8) | data[i+1] for i in range(0, nbytes, 2)]
        print("Regs:", regs)  # DEBUG
        return regs



# ---------------- SCD4x temperature provider ----------------
def get_temperature_provider(i2c):
    if USE_SCD41_TEMP:
        try:
            scd4x = adafruit_scd4x.SCD4X(i2c)
            scd4x.start_periodic_measurement()
            print("SCD4x detected — using its temperature for EC compensation.")
            t_last = [time.monotonic() - 10]
            t_cache = [25.0]
            def _temp():
                now = time.monotonic()
                if now - t_last[0] > 1.0 and scd4x.data_ready:
                    t_cache[0] = float(scd4x.temperature)
                    t_last[0] = now
                return t_cache[0]
            return _temp, scd4x
        except Exception as e:
            print(f"Note: SCD4x not used ({e}). Using fixed 25.0 °C.")
    return (lambda: 25.0), None

# ---------------- TDS/EC conversion ----------------
def voltage_to_ec_uScm(voltage_v: float, temp_c: float, k_cal: float = 1.0) -> float:
    # ~2%/°C compensation
    comp_coeff = 1.0 + 0.02 * (temp_c - 25.0)
    v_comp = voltage_v / comp_coeff
    # DFRobot-style polynomial to TDS (ppm), then to EC (µS/cm)
    tds_ppm = (133.42 * v_comp**3 - 255.86 * v_comp**2 + 857.39 * v_comp) * 0.5
    ec_uScm = (tds_ppm * 2.0) * k_cal
    return max(0.0, ec_uScm)

# ---------------- Light sensor (raw channels) ----------------
def init_lux_sensor(bus: smbus.SMBus):
    # Power on + integration config (example)
    bus.write_byte_data(LUX_ADDR, 0x00 | 0x80, 0x03)
    bus.write_byte_data(LUX_ADDR, 0x01 | 0x80, 0x02)
    time.sleep(0.5)

def read_lux_raw(bus: smbus.SMBus):
    data  = bus.read_i2c_block_data(LUX_ADDR, 0x0C | 0x80, 2)
    data1 = bus.read_i2c_block_data(LUX_ADDR, 0x0E | 0x80, 2)
    ch0   = data[1]*256 + data[0]
    ch1   = data1[1]*256 + data1[0]
    visible = ch0 - ch1
    return ch0, ch1, visible

# ---------------- Camera ----------------
cam = Camera()  # picamzero camera object (used below)  :contentReference[oaicite:1]{index=1}

# ---------------- Main ----------------
def main():
    # Sheets + Drive
    ws    = init_sheets()
    creds = authenticate_drive()

    # I2C
    i2c = busio.I2C(board.SCL, board.SDA)

    # SCD4x (CO2/T/RH + temp provider)
    temp_fn, scd4x = get_temperature_provider(i2c)

    # ADS1115
    ads = ADS.ADS1115(i2c); ads.gain = 1; ads.data_rate = 128
    chan_tds   = AnalogIn(ads, TDS_CH)
    chan_mq135 = AnalogIn(ads, MQ135_CH)

    # Light sensor on kernel I2C (smbus)
    bus = smbus.SMBus(1)
    init_lux_sensor(bus)

    # RS485 for NPK
    rs = RS485()

    next_wake = time.monotonic()
    try:
        while _running:
            # --- SCD4x readings ---
            co2 = t = rh = None
            try:
                if scd4x and scd4x.data_ready:
                    co2 = int(scd4x.CO2)
                    t   = round(float(scd4x.temperature), 2)
                    rh  = round(float(scd4x.relative_humidity), 1)
            except Exception:
                pass

            # --- Light raw channels ---
            try:
                ch0, ch1, vis = read_lux_raw(bus)
            except Exception:
                ch0 = ch1 = vis = None

            # --- TDS/EC ---
            acc_v = 0.0
            for _ in range(SAMPLES_PER_READ):
                acc_v += chan_tds.voltage
                time.sleep(PER_SAMPLE_DELAY)
            t_c   = temp_fn()
            tds_v = acc_v / SAMPLES_PER_READ
            ec_uS = round(voltage_to_ec_uScm(tds_v, t_c, CAL_FACTOR), 1)

            # --- MQ-135 voltage (optional) ---
            try:
                mq135_v = round(chan_mq135.voltage, 4)
            except Exception:
                mq135_v = None

            # --- NPK via RS485 ---
            N = P = K = ""
            try:
                regs = rs.read_regs(SLAVE_ADDR, HOLDING_START, HOLDING_COUNT)
                if regs and len(regs) >= 3:
                    N = regs[0] / SCALE_N
                    P = regs[1] / SCALE_P
                    K = regs[2] / SCALE_K
            except Exception:
                pass

            # --- Take Photo ---
            ts_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            photo_filename = f"/home/sensoil/photo_{ts_file}.jpg"  # build path
            cam.take_photo(photo_filename)                         # snap  :contentReference[oaicite:2]{index=2}

            # --- Upload Photo to Drive (get shareable link) ---
            image_link = upload_file(photo_filename, DRIVE_FOLDER_ID, creds)  #  :contentReference[oaicite:3]{index=3}

            # --- Print to shell ---
            ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("------")
            print(
                f"[{ts}] "
                f"CO2={co2 if co2 is not None else 'NA'} ppm | "
                f"T={t if t is not None else t_c:.2f} °C | "
                f"RH={rh if rh is not None else 'NA'} % | "
                f"Full={ch0 if ch0 is not None else 'NA'} | "
                f"IR={ch1 if ch1 is not None else 'NA'} | "
                f"Vis={vis if vis is not None else 'NA'} | "
                f"TDS_V={tds_v:.4f} V | EC={ec_uS:.1f} µS/cm | "
                f"MQ135_V={mq135_v if mq135_v is not None else 'NA'} | "
                f"N={N if N != '' else 'NA'} P={P if P != '' else 'NA'} K={K if K != '' else 'NA'} | "
                f"Image={image_link}"
            )

            # --- Upload same row to Google Sheets (incl. image link) ---
            row = [
                ts,
                co2, (t if t is not None else round(t_c, 2)), rh,
                ch0, ch1, vis,
                round(ec_uS, 1),
                N, P, K,
                image_link
            ]
            append_row_safely(ws, row)  # row includes image_link  :contentReference[oaicite:4]{index=4}

            # drift-free cadence
            next_wake += INTERVAL_SECONDS
            while _running:
                to_sleep = next_wake - time.monotonic()
                if to_sleep <= 0:
                    break
                time.sleep(min(1.0, to_sleep))

    finally:
        try:
            if scd4x: scd4x.stop_periodic_measurement()
        except Exception:
            pass
        try:
            rs.close()
        except Exception:
            pass
        try:
            bus.close()
        except Exception:
            pass
        print("Stopped.")

if __name__ == "__main__":
    main()

