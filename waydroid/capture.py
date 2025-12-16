# scripts/capture.py
from pathlib import Path
import subprocess, sys, os

ROOT = Path(__file__).resolve().parents[1]   # Waydroid/
DATA = ROOT / "data"
PNG  = DATA / "s.png"

def main():
    # Make sure data/ exists and you can write to it
    DATA.mkdir(parents=True, exist_ok=True)
    # Capture via ADB (you’re already authorized)
    try:
        with open(PNG, "wb") as f:
            subprocess.run(["adb", "exec-out", "screencap", "-p"], check=True, stdout=f)
        print(f"[OK] Saved {PNG}")
        return 0
    except Exception as e:
        print(f"[WARN] adb capture failed: {e}. Trying waydroid shell…")

    # Fallback path inside the container
    tmp = "/data/local/tmp/_s.png"
    subprocess.run(["sudo","waydroid","shell","--","screencap","-p", tmp], check=True)
    with open(PNG, "wb") as f:
        subprocess.run(["sudo","waydroid","shell","--","cat", tmp], check=True, stdout=f)
    print(f"[OK] Saved {PNG}")
    return 0

if __name__ == "__main__":
    sys.exit(main())