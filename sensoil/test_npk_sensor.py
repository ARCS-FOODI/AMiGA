import time, datetime, signal
import serial
import RPi.GPIO as GPIO

# ================== USER CONFIG ==================
SERIAL_PORT   = "/dev/serial0"   # e.g. "/dev/ttyS0" or USB to RS485 adapter (like "/dev/ttyUSB0")
BAUDRATE      = 9600             # Default from specs
PARITY        = serial.PARITY_NONE # "Parity: None" from specs
STOPBITS      = serial.STOPBITS_ONE # 1 Stop Bit
BYTESIZE      = serial.EIGHTBITS    # 8 Data Bits
TIMEOUT       = 1.0

SLAVE_ADDR    = 1
DE_RE_GPIO    = 18

HOLDING_START = 0x001E  # N address=0x001E (30 Decimal). P=0x001F, K=0x0020
HOLDING_COUNT = 3       # We need 3 continuous registers for N, P, and K

SCALE_N = 1.0
SCALE_P = 1.0
SCALE_K = 1.0

INTERVAL_SECONDS = 1
RETRIES_PER_READ = 2
# ================================================

_running = True
def _stop(_sig, _frm):
    global _running
    _running = False

signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)

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
    return pdu + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

class RS485:
    def __init__(self):
        self.ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUDRATE,
            parity=PARITY,
            stopbits=STOPBITS,
            bytesize=BYTESIZE,
            timeout=TIMEOUT
        )
        # Using GPIO for DE/RE on an RS485 hat, you can remove this if using an auto DE/RE USB adapter
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DE_RE_GPIO, GPIO.OUT, initial=GPIO.LOW)

    def close(self):
        try:
            self.ser.close()
        finally:
            GPIO.cleanup(DE_RE_GPIO)

    def _tx(self, data: bytes):
        GPIO.output(DE_RE_GPIO, GPIO.HIGH)
        time.sleep(0.005)

        self.ser.write(data)
        self.ser.flush()

        time.sleep(0.005)
        GPIO.output(DE_RE_GPIO, GPIO.LOW)
        time.sleep(0.002)

    def read_regs(self, addr: int, start: int, count: int):
        req = build_read_holding(addr, start, count)

        # Clear any old bytes before sending
        self.ser.reset_input_buffer()

        self._tx(req)
        print("TX:", req.hex())

        head = self.ser.read(3)
        print("HEAD:", head.hex(), "len=", len(head))
        if len(head) < 3:
            print("Error: Received less than 3 bytes in response head.")
            return None

        a, func, nbytes = head
        if func == 0x83:
            _ = self.ser.read(3)
            print("Error: Received Modbus exception code 0x83.")
            return None

        rest = self.ser.read(nbytes + 2)
        reply = head + rest

        calc = crc16_modbus(reply[:-2])
        recv = reply[-2] | (reply[-1] << 8)
        if calc != recv or nbytes % 2:
            print(f"Error: CRC mismatch or invalid nbytes. Calc: {hex(calc)}, Recv: {hex(recv)}")
            return None

        data = reply[3:3+nbytes]
        regs = [(data[i] << 8) | data[i+1] for i in range(0, nbytes, 2)]
        return regs

def main():
    bus = RS485()
    try:
        next_wake = time.monotonic()
        while _running:
            regs = None
            for _ in range(1 + RETRIES_PER_READ):
                regs = bus.read_regs(SLAVE_ADDR, HOLDING_START, HOLDING_COUNT)
                if regs is not None:
                    break
                time.sleep(0.1)

            if regs and len(regs) >= 3:
                N = regs[0] / SCALE_N
                P = regs[1] / SCALE_P
                K = regs[2] / SCALE_K
            else:
                N = P = K = None

            # Values are typically returned as integers in mg/kg
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] N={N} mg/kg  P={P} mg/kg  K={K} mg/kg")

            next_wake += INTERVAL_SECONDS
            while _running:
                to_sleep = next_wake - time.monotonic()
                if to_sleep <= 0:
                    break
                time.sleep(min(1.0, to_sleep))
    finally:
        bus.close()

if __name__ == "__main__":
    main()
