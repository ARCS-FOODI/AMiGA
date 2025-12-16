#!/usr/bin/env python3
# =============================================================================
# AeroLush C08 OCR Telemetry Logger
#
# OUTPUT (per line, printed + CSV append):
#   [timestamp, current_temp, target_temp, humidity, vpd_kpa, ac_state]
#
# DEFAULT BEHAVIOR (no flags):
#   - Captures a new Android screenshot every cycle via ADB
#   - Overwrites data/s.png each cycle
#   - OCR with Tesseract (PSM 6; fallback PSM 11 if needed)
#   - Parses and prints a single list in the order above
#   - Appends to data/telemetry_full_ocr.csv (header auto-created)
#
# COMMON FLAGS:
#   --interval 2      Capture/parse every 2 seconds (default 5)
#   --once            Run a single cycle and exit
#   --no-csv          Don’t write CSV (still prints the row)
#   --debug           Verbose logs: raw OCR, matches, picks, etc.
#   --img path.png    Parse an existing image (disables ADB capture)
#
# EXAMPLES:
#   python3 main.py                          # continuous ADB capture every 5s
#   python3 main.py --interval 2 --debug     # faster, with verbose debugging
#   python3 main.py --once --no-csv          # one row, print only
#   python3 main.py --img data/s.png --once  # single pass on a static image
# =============================================================================

from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import pytesseract, csv, sys, re, argparse, subprocess, os, time

# --- Paths
ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
DATA = ROOT / "data"
IMG  = DATA / "s.png"
CSV  = DATA / "telemetry_full_ocr.csv"

# --- Patterns
# Humidity notes:
#   Seen as: "@ 46% 2 1.5kPa", "G 46% 2 15kPa", and sometimes stray "@" on another line.
# Strategy: strict leader match [＠@QG] + fallback to first "<0-100>%".
PAT_HUM_STRICT = re.compile(r"[＠@QG]\s*([0-9O]{1,3})\s*[%％]")
PAT_HUM_LOOSE  = re.compile(r"\b([0-9O]{1,3})\s*[%％]\b")

# VPD: normalize OCR decimal mistakes (e.g., "1:7kPa" -> "1.7kPa", also "; , · •")
VPD_DECIMAL_SEP = re.compile(r"(?P<int>\d+)\s*[:;·•,]\s*(?P<frac>\d+)\s*(?=k\s*pa\b)", re.I)
VPD_ANY         = re.compile(r"(\d+(?:\.\d+)?)\s*k\s*pa\b", re.I)

# AC ON/OFF
PAT_AC_LINE  = re.compile(r"air\s*condition(?:er)?\s*([Oo][Nn]|[Oo][Ff][Ff])", re.I)

# Temperatures:
#  - Normal: "72.5°F", "80.6 F"
#  - Weird:  "80:°F"  (colon directly before degree symbol)
PAT_TEMP_ANY   = re.compile(r"(-?\d+(?:\.\d+)?)\s*[°º]?\s*([CF])\b", re.I)
PAT_TEMP_WEIRD = re.compile(r"(-?\d{2,3})\s*[:;·•,]\s*[°º]\s*([CF])\b", re.I)

def normalize_vpd_text(text: str) -> str:
    def _repl(m: re.Match) -> str:
        return f"{m.group('int')}.{m.group('frac')}"
    return VPD_DECIMAL_SEP.sub(_repl, text)

def clean_invisibles(text: str) -> str:
    return (
        text.replace("\u200b", "")   # ZWSP
            .replace("\u200a", "")   # hair space
            .replace("\ufeff", "")   # BOM
            .replace("\u202f", "")   # narrow no-break space
            .replace("\u00a0", " ")  # NBSP -> space
    )

def ocr_image(img_path: Path, psm: int, debug: bool=False) -> str:
    img = Image.open(img_path)
    gray = ImageOps.grayscale(img)
    txt = pytesseract.image_to_string(gray, config=f"--psm {psm}")
    if debug:
        print(f"\n==== DEBUG: RAW OCR (psm={psm}) ====")
        print(txt if txt.strip() else "<EMPTY>")
        print("===================================")
    return txt

def capture_screenshot(debug: bool=False):
    DATA.mkdir(parents=True, exist_ok=True)
    if debug:
        print("Capturing screenshot via ADB ->", IMG)
    with open(IMG, "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], check=True, stdout=f)

def parse_humidity(text: str, debug: bool=False) -> int | None:
    m = PAT_HUM_STRICT.search(text)
    if m:
        val = int(m.group(1).replace("O", "0"))
        if 0 <= val <= 100:
            if debug:
                print(f"Humidity(strict)  match={m.group(0)!r} -> {val}%")
            return val
    m2 = PAT_HUM_LOOSE.search(text)
    if m2:
        val = int(m2.group(1).replace("O", "0"))
        if 0 <= val <= 100:
            if debug:
                print(f"Humidity(fallback) match={m2.group(0)!r} -> {val}%")
            return val
    if debug:
        print("Humidity: no match")
    return None

def parse_all(text: str, last: dict | None = None, debug: bool = False) -> dict:
    last = last or {}
    out: dict = {}

    clean_text = clean_invisibles(text)
    lines = [ln.strip() for ln in clean_text.splitlines() if ln.strip()]

    # Temperatures (collect with positions) — include both normal and weird matches
    temps = []  # (line_idx, value(float), unit)
    for i, ln in enumerate(lines):
        for v, u in PAT_TEMP_ANY.findall(ln):
            try:
                temps.append((i, float(v), u.upper()))
            except ValueError:
                pass
        # Handle weird "80:°F" style
        for v, u in PAT_TEMP_WEIRD.findall(ln):
            try:
                # Treat as integer value (e.g., "80:°F" => 80.0)
                temps.append((i, float(v), u.upper()))
            except ValueError:
                pass

    if debug:
        print("\n==== DEBUG: TEMPERATURE MATCHES ====")
        if temps:
            for t in temps:
                print(f"line={t[0]} val={t[1]} unit={t[2]}")
        else:
            print("No temperature matches found.")
        print("====================================")

    # Locate "Target Temperature" line
    tlabel_idx = next((i for i, ln in enumerate(lines)
                       if "target" in ln.lower() and "temp" in ln.lower()), -1)
    if debug:
        print(f"\n==== DEBUG: TARGET LABEL INDEX ====\n{tlabel_idx}\n=================================")

    # Target: first temp at/after label (within small window), else last temp
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

    # Current: closest temp outside target window (prefer above), else first
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

    if debug:
        print("\n==== DEBUG: PICKED TEMPS ====")
        print(f"current_temp_val = {current_val}")
        print(f"target_temp_val  = {target_val}")
        print("================================")

    # Humidity (strict -> fallback)
    humidity = parse_humidity(clean_text, debug=debug)

    # VPD (kPa) — normalize weird decimal separators before matching
    vpd_text = normalize_vpd_text(clean_text)
    vpd_m = VPD_ANY.search(vpd_text)
    vpd = float(vpd_m.group(1)) if vpd_m else None
    if debug:
        match_str = vpd_m.group(0) if vpd_m else None
        print("\n==== DEBUG: VPD ====")
        if vpd_text is not clean_text:
            print("normalized:", repr(vpd_text))
        print(f"vpd_kpa = {vpd}  (match={match_str!r})")
        print("====================")

    # AC state
    ac_m = PAT_AC_LINE.search(clean_text)
    ac_state = ac_m.group(1).upper() if ac_m else None
    if ac_state == "OF":  # occasional OCR 'OFF' -> 'OF'
        ac_state = "OFF"
    if debug:
        print("\n==== DEBUG: AC STATE ====")
        if ac_m:
            print(f"ac_state = {ac_state}  (match={ac_m.group(0)!r})")
        else:
            print("No AC ON/OFF match found.")
        print("==========================")

    # Fill with fallbacks
    out["current_temp_val"] = current_val if current_val is not None else last.get("current_temp_val")
    out["target_temp_val"]  = target_val  if target_val  is not None else last.get("target_temp_val")
    out["humidity_%"]       = humidity    if humidity    is not None else last.get("humidity_%")
    out["vpd_kpa"]          = vpd         if vpd         is not None else last.get("vpd_kpa")
    out["ac_state"]         = ac_state    if ac_state    is not None else last.get("ac_state")

    if debug:
        print("\n==== DEBUG: FINAL PARSED ====")
        for k, v in out.items():
            print(f"{k:18s} = {v}")
        print("=============================")

    return out

def ensure_csv_header():
    CSV.parent.mkdir(parents=True, exist_ok=True)
    if not CSV.exists():
        with CSV.open("w", newline="") as f:
            csv.writer(f).writerow(["ts","current_temp_val","target_temp_val","humidity_%","vpd_kpa","ac_state"])

def append_csv_row(row):
    with CSV.open("a", newline="") as f:
        csv.writer(f).writerow(row); f.flush()

def one_cycle(img_source: str | None, use_adb: bool, debug: bool, last: dict) -> list:
    # Capture or locate image
    if use_adb:
        capture_screenshot(debug=debug)
        img_path = IMG
    else:
        img_path = Path(img_source)
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")

    # OCR with PSM 6 then fallback 11 if needed
    txt6 = ocr_image(img_path, psm=6, debug=debug)
    parsed = parse_all(txt6, last=last, debug=debug)

    needed = {"humidity_%","vpd_kpa","ac_state","target_temp_val","current_temp_val"}
    if any(parsed.get(k) is None for k in needed):
        if debug:
            print("Key fields missing; trying PSM 11 fallback…")
        txt11 = ocr_image(img_path, psm=11, debug=debug)
        alt = parse_all(txt11, last=parsed, debug=debug)
        for k, v in alt.items():
            if parsed.get(k) is None and v is not None:
                parsed[k] = v

    ts = datetime.now().strftime("%F %T")
    row = [
        ts,
        parsed.get("current_temp_val"),
        parsed.get("target_temp_val"),
        parsed.get("humidity_%"),
        parsed.get("vpd_kpa"),
        parsed.get("ac_state"),
    ]
    return row, parsed

def main():
    ap = argparse.ArgumentParser(description="Continuous OCR telemetry from Android screenshots")
    ap.add_argument("--img", help="Path to image (if provided, disables ADB capture)")
    ap.add_argument("--interval", type=float, default=5.0, help="Seconds between cycles (default 5)")
    ap.add_argument("--debug", action="store_true", help="Verbose debug output")
    ap.add_argument("--no-csv", action="store_true", help="Do not write CSV")
    ap.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    args = ap.parse_args()

    # Default to ADB capture if no image is provided
    use_adb = args.img is None

    # Preflight ADB if needed
    if use_adb:
        try:
            subprocess.run(["adb", "get-state"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            os.system("adb kill-server >/dev/null 2>&1; adb start-server >/dev/null 2>&1")
        except FileNotFoundError:
            print("ERROR: 'adb' not found on PATH and no --img provided.", file=sys.stderr)
            sys.exit(1)

    ensure_csv_header()

    last = {
        "current_temp_val": None,
        "target_temp_val": None,
        "humidity_%": None,
        "vpd_kpa": None,
        "ac_state": None,
    }

    def do_cycle():
        row, parsed = one_cycle(args.img, use_adb, args.debug, last)
        if not args.no_csv:
            append_csv_row(row)
        print(row)
        for k in last.keys():
            last[k] = parsed.get(k, last[k])

    try:
        if args.once:
            try:
                do_cycle()
            except subprocess.CalledProcessError:
                os.system("adb kill-server >/dev/null 2>&1; adb start-server >/dev/null 2>&1")
                do_cycle()
            return

        while True:
            try:
                do_cycle()
                time.sleep(args.interval)
            except subprocess.CalledProcessError:
                os.system("adb kill-server >/dev/null 2>&1; adb start-server >/dev/null 2>&1")
                time.sleep(1)
            except Exception as e:
                print("WARN:", e)
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping…")

if __name__ == "__main__":
    main()