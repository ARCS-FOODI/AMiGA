import subprocess
import time
import os

# --- CONFIGURATION ---
# Use the EXACT name from your xwininfo output
WINDOW_NAME = "Weston Compositor - screen0"
SAVE_PATH = "/home/sensoil/scripts/vivosun_full_snap.png"
INTERVAL = 5 

def get_window_id():
    print(f"Searching for: {WINDOW_NAME}")
    while True:
        try:
            # We use the -name flag with the exact string
            out = subprocess.check_output(["xdotool", "search", "--name", WINDOW_NAME])
            wid = out.decode().strip().split()[-1] # Grab the latest ID
            print(f"FOUND! Window ID: {wid}")
            return wid
        except Exception:
            # If search fails, let's try a broader search for just 'Weston'
            try:
                out = subprocess.check_output(["xdotool", "search", "--name", "Weston"])
                wid = out.decode().strip().split()[-1]
                print(f"Found via fallback! ID: {wid}")
                return wid
            except:
                print("Waiting for window to appear on desktop...")
                time.sleep(2)

def run_simple_capture():
    wid = get_window_id()
    while True:
        # Use the Window ID directly for the sharpest capture
        subprocess.run(["maim", "-i", wid, SAVE_PATH])
        print(f"[{time.strftime('%H:%M:%S')}] Snapshot saved.")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    run_simple_capture()
