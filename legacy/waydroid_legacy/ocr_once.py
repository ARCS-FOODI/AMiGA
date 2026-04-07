from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import pytesseract, subprocess, csv, os, time, re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IMG  = DATA / "s.png"
CSV  = DATA / "telemetry_full_ocr.csv"

# Patterns
PAT_HUM_AT   = re.compile(r"@?\s*(\d{1,3})\s*[％%]\b", re.U)                 # '@ 49%' or '49%' (also full-width ％)
PAT_VPD_KPA  = re.compile(r"(\d+(?:\.\d+)?)\s*k\s*pa\b", re.I)               # '13kPa' / '13 kPa'
PAT_AC_LINE  = re.compile(r"air\s+condition(?:er)?\s+([Oo][Nn]|[Oo][Ff][Ff])", re.I)
PAT_TEMP_ANY = re.compile(r"(-?\d+(?:\.\d+)?)\s*[°º]?\s*([CF])\b", re.I)     # '72.7F', '80.6 °F', etc.

def capture():
    DATA.mkdir(parents=True, exist_ok=True)
    with open(IMG, "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], check=True, stdout=f)

def ocr(psm=6):
    img = Image.open(IMG)
    g = ImageOps.grayscale(img)
    return pytesseract.image_to_string(g, config=f"--psm {psm}")

def parse_all(txt: str):
    out = {}

    # --- humidity
    m = PAT_HUM_AT.search(txt)
    if m:
        out["humidity_%"] = max(0, min(100, int(m.group(1))))

    # --- VPD
    m = PAT_VPD_KPA.search(txt)
    if m:
        out["vpd_kpa"] = float(m.group(1))

    # --- AC state
    m = PAT_AC_LINE.search(txt)
    if m:
        state = m.group(1).upper()
        out["ac_state"] = "ON" if state.startswith("ON") else "OFF"

    # --- collect all temps with line indices
    lines = txt.splitlines()
    temps = []  # (line_idx, val(float), unit('F'/'C'))
    for i, ln in enumerate(lines):
        for v,u in PAT_TEMP_ANY.findall(ln):
            try:
                temps.append((i, float(v), u.upper()))
            except ValueError:
                pass

    # --- find "Target Temperature" label
    tlabel_idx = next((i for i, ln in enumerate(lines)
                       if "target" in ln.lower() and "temp" in ln.lower()), -1)

    target_idx = None
    if tlabel_idx != -1:
        # pick the first temp within a small window *after* the label
        for i, v, u in temps:
            if tlabel_idx <= i <= tlabel_idx + 5:
                out["target_temp_val"]  = v
                out["target_temp_unit"] = u
                target_idx = i
                break

    # fallback for target if label missed
    if "target_temp_val" not in out and temps:
        i, v, u = temps[-1]
        out["target_temp_val"]  = v
        out["target_temp_unit"] = u
        target_idx = i

    # --- current temp = closest temp outside the target window (prefer above)
    if temps:
        win_start = tlabel_idx if tlabel_idx != -1 else (target_idx if target_idx is not None else 10**9)
        win_end   = (target_idx if target_idx is not None else win_start) + 5
        candidates = [(i, v, u) for (i, v, u) in temps if not (win_start <= i <= win_end)]
        if candidates:
            above = [(i, v, u) for (i, v, u) in candidates if i < win_start]
            if above:
                i, v, u = max(above, key=lambda t: t[0])   # closest above
            else:
                i, v, u = min(candidates, key=lambda t: abs(t[0] - win_start))
            out["current_temp_val"]  = v
            out["current_temp_unit"] = u

    return out

def main(interval=5):
    new = not CSV.exists()
    with CSV.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow([
                "ts",
                "humidity_%",
                "vpd_kpa",
                "ac_state",
                "current_temp_val","current_temp_unit",
                "target_temp_val","target_temp_unit"
            ])
        last = {
            "humidity_%": None, "vpd_kpa": None, "ac_state": None,
            "current_temp_val": None, "current_temp_unit": None,
            "target_temp_val": None, "target_temp_unit": None
        }
        while True:
            try:
                capture()
                txt6 = ocr(psm=6)
                parsed = parse_all(txt6)

                # sparse fallback if anything important missing
                needed = {"humidity_%","vpd_kpa","ac_state","target_temp_val","current_temp_val"}
                if not needed.issubset(parsed.keys()):
                    txt11 = ocr(psm=11)
                    alt = parse_all(txt11)
                    for k,v in alt.items():
                        parsed.setdefault(k, v)

                row = [
                    datetime.now().strftime("%F %T"),
                    parsed.get("humidity_%",        last["humidity_%"]),
                    parsed.get("vpd_kpa",           last["vpd_kpa"]),
                    parsed.get("ac_state",          last["ac_state"]),
                    parsed.get("current_temp_val",  last["current_temp_val"]),
                    parsed.get("current_temp_unit", last["current_temp_unit"]),
                    parsed.get("target_temp_val",   last["target_temp_val"]),
                    parsed.get("target_temp_unit",  last["target_temp_unit"]),
                ]
                w.writerow(row); f.flush()
                print(row)

                last = {
                    "humidity_%": row[1], "vpd_kpa": row[2], "ac_state": row[3],
                    "current_temp_val": row[4], "current_temp_unit": row[5],
                    "target_temp_val": row[6],  "target_temp_unit": row[7],
                }
                time.sleep(interval)

            except subprocess.CalledProcessError:
                os.system("adb kill-server >/dev/null 2>&1; adb start-server >/dev/null 2>&1")
                time.sleep(1)
            except Exception as e:
                print("WARN:", e)
                time.sleep(1)

if __name__ == "__main__":
    main()