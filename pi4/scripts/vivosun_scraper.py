import subprocess
import time
import os
import csv
import re
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import pytesseract

# --- HARDCODED CONFIGURATION ---
SCRIPT_DIR = Path(__file__).resolve().parent
IMG_PATH = SCRIPT_DIR / "s.png"
CSV_PATH = SCRIPT_DIR / "vivosun_telemetry.csv"
INTERVAL = 5.0

# --- PATTERNS ---
PAT_HUM_STRICT = re.compile(r"[＠@QG]\s*([0-9O]{1,3})\s*[%％]")
PAT_HUM_LOOSE  = re.compile(r"\b([0-9O]{1,3})\s*[%％]\b")
VPD_DECIMAL_SEP = re.compile(r"(?P<int>\d+)\s*[:;·•,]\s*(?P<frac>\d+)\s*(?=k\s*pa\b)", re.I)
VPD_ANY         = re.compile(r"(\d+(?:\.\d+)?)\s*k\s*pa\b", re.I)
PAT_AC_LINE     = re.compile(r"air\s*condition(?:er)?\s*([Oo][Nn]|[Oo][Ff][Ff])", re.I)
PAT_TEMP_ANY    = re.compile(r"(-?\d+(?:\.\d+)?)\s*[°º]?\s*([CF])\b", re.I)
PAT_TEMP_WEIRD  = re.compile(r"(-?\d{2,3})\s*[:;·•,]\s*[°º]\s*([CF])\b", re.I)

def normalize_vpd_text(text: str) -> str:
    def _repl(m: re.Match) -> str:
        return f"{m.group('int')}.{m.group('frac')}"
    return VPD_DECIMAL_SEP.sub(_repl, text)

def clean_invisibles(text: str) -> str:
    return (
        text.replace("\u200b", "")
            .replace("\u200a", "")
            .replace("\ufeff", "")
            .replace("\u202f", "")
            .replace("\u00a0", " ")
    )

def capture_screenshot():
    # Try ADB first
    try:
        with open(IMG_PATH, "wb") as f:
            subprocess.run(["adb", "exec-out", "screencap", "-p"], check=True, stdout=f)
        return True
    except Exception as e:
        print(f"[WARN] adb capture failed: {e}. Trying waydroid shell...")
    
    # Fallback to Waydroid shell
    try:
        tmp = "/data/local/tmp/_s.png"
        subprocess.run(["sudo", "waydroid", "shell", "--", "screencap", "-p", tmp], check=True)
        with open(IMG_PATH, "wb") as f:
            subprocess.run(["sudo", "waydroid", "shell", "--", "cat", tmp], check=True, stdout=f)
        return True
    except Exception as e:
        print(f"[ERROR] Both adb and waydroid capture failed: {e}")
        return False

def ocr_image(psm: int) -> str:
    if not IMG_PATH.exists():
        return ""
    img = Image.open(IMG_PATH)
    gray = ImageOps.grayscale(img)
    return pytesseract.image_to_string(gray, config=f"--psm {psm}")

def parse_humidity(text: str) -> int | None:
    m = PAT_HUM_STRICT.search(text)
    if m:
        val = int(m.group(1).replace("O", "0"))
        if 0 <= val <= 100:
            return val
    m2 = PAT_HUM_LOOSE.search(text)
    if m2:
        val = int(m2.group(1).replace("O", "0"))
        if 0 <= val <= 100:
            return val
    return None

def parse_all(text: str, last: dict | None = None) -> dict:
    last = last or {}
    out: dict = {}

    clean_text = clean_invisibles(text)
    lines = [ln.strip() for ln in clean_text.splitlines() if ln.strip()]

    # Collect temps
    temps = []
    for i, ln in enumerate(lines):
        for v, u in PAT_TEMP_ANY.findall(ln):
            try:
                temps.append((i, float(v), u.upper()))
            except ValueError:
                pass
        for v, u in PAT_TEMP_WEIRD.findall(ln):
            try:
                temps.append((i, float(v), u.upper()))
            except ValueError:
                pass

    # Find Target Temperature label
    tlabel_idx = next((i for i, ln in enumerate(lines) if "target" in ln.lower() and "temp" in ln.lower()), -1)

    target_val = None
    target_idx = None
    if tlabel_idx != -1:
        for i, v, u in temps:
            if tlabel_idx <= i <= tlabel_idx + 5:
                target_val = v
                target_idx = i
                break
    
    if target_val is None and temps:
        i, v, u = temps[-1]
        target_val = v
        target_idx = i

    # Find Current Temperature
    current_val = None
    if temps:
        win_start = tlabel_idx if tlabel_idx != -1 else (target_idx if target_idx is not None else 10**9)
        win_end   = (target_idx if target_idx is not None else win_start) + 5
        candidates = [(i, v, u) for (i, v, u) in temps if not (win_start <= i <= win_end)]
        if candidates:
            above = [(i, v, u) for (i, v, u) in candidates if i < win_start]
            if above:
                i, v, u = max(above, key=lambda t: t[0])
            else:
                i, v, u = min(candidates, key=lambda t: abs(t[0] - win_start))
            current_val = v
        else:
            current_val = temps[0][1]

    humidity = parse_humidity(clean_text)

    vpd_text = normalize_vpd_text(clean_text)
    vpd_m = VPD_ANY.search(vpd_text)
    vpd = float(vpd_m.group(1)) if vpd_m else None

    ac_state = None
    ac_m = PAT_AC_LINE.search(clean_text)
    if ac_m:
        ac_state = ac_m.group(1).upper()
        if ac_state == "OF":
            ac_state = "OFF"

    # Fill fallbacks
    out["current_temp_val"] = current_val if current_val is not None else last.get("current_temp_val")
    out["target_temp_val"]  = target_val  if target_val  is not None else last.get("target_temp_val")
    out["humidity_%"]       = humidity    if humidity    is not None else last.get("humidity_%")
    out["vpd_kpa"]          = vpd         if vpd         is not None else last.get("vpd_kpa")
    out["ac_state"]         = ac_state    if ac_state    is not None else last.get("ac_state")

    return out

def ensure_csv_header():
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="") as f:
            csv.writer(f).writerow(["ts","current_temp_val","target_temp_val","humidity_%","vpd_kpa","ac_state"])

def run_scraper_loop():
    print(f"Starting Vivosun Scraper... Will save to {CSV_PATH} every {INTERVAL} seconds.")
    ensure_csv_header()
    
    last_state = {
        "current_temp_val": None,
        "target_temp_val": None,
        "humidity_%": None,
        "vpd_kpa": None,
        "ac_state": None,
    }

    try:
        while True:
            # 1. Capture Image
            if not capture_screenshot():
                time.sleep(INTERVAL)
                continue
            
            # 2. Extract Data
            txt6 = ocr_image(psm=6)
            parsed = parse_all(txt6, last=last_state)

            # Try fallback OCR if data is missing
            needed = {"humidity_%", "vpd_kpa", "ac_state", "target_temp_val", "current_temp_val"}
            if any(parsed.get(k) is None for k in needed):
                txt11 = ocr_image(psm=11)
                alt = parse_all(txt11, last=parsed)
                for k, v in alt.items():
                    if parsed.get(k) is None and v is not None:
                        parsed[k] = v

            # 3. Format and Log Data
            ts = datetime.now().strftime("%F %T")
            row = [
                ts,
                parsed.get("current_temp_val"),
                parsed.get("target_temp_val"),
                parsed.get("humidity_%"),
                parsed.get("vpd_kpa"),
                parsed.get("ac_state")
            ]
            
            with CSV_PATH.open("a", newline="") as f:
                csv.writer(f).writerow(row)
                
            print(f"[{ts}] Logged: {row}")
            
            # Update last state
            for k in last_state.keys():
                last_state[k] = parsed.get(k, last_state[k])
                
            # 4. Wait
            time.sleep(INTERVAL)
            
    except KeyboardInterrupt:
        print("\nScraper stopped by user.")
    except Exception as e:
        print(f"\nScraper encountered an error: {e}")

if __name__ == "__main__":
    run_scraper_loop()
