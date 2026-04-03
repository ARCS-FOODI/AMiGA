#!/bin/bash

# 1. SETUP ENVIRONMENT
export XDG_RUNTIME_DIR=/run/user/1000
export DISPLAY=:0

# 2. CLEAN SLATE
waydroid session stop
pkill -9 weston
rm -f /run/user/1000/wayland-*
sleep 2

# 3. START WESTON
echo "Starting Weston..."
env DISPLAY=:0 weston --backend=x11-backend.so --width=700 --height=1000 --idle-time=0 &

# 4. FIND THE SOCKET
echo "Searching for Wayland socket..."
for i in {1..10}; do
    REAL_SOCKET=$(ls /run/user/1000/wayland-* 2>/dev/null | xargs basename 2>/dev/null | head -n 1)
    if [ -n "$REAL_SOCKET" ]; then
        export WAYLAND_DISPLAY=$REAL_SOCKET
        echo "SUCCESS: Found Weston on $WAYLAND_DISPLAY"
        break
    fi
    sleep 1
done

# 5. START ANDROID UI
echo "Launching Android UI..."
waydroid show-full-ui &

# 6. THE 50-SECOND SIMPLIFIED WAIT
echo "Waiting 60 seconds for Android to warm up..."
sleep 60

# 7. LAUNCH VIVOSUN
echo "Launching VIVOSUN App..."
waydroid app launch com.vivosun.android &

# 8. POSITION THE WINDOW
# We wait for the window to exist, then teleport it to your coordinates
echo "Positioning window at 1210, 75..."
sleep 5
WID=$(xdotool search --name "Weston" | head -n 1)
xwininfo -id $WID # Just to log it
xdotool windowmove $WID 1210 75
xdotool windowactivate $WID

# 9. START SCRAPER
echo "Starting Scraper..."
sleep 30
python3 /home/sensoil/vivosun_scraper.py
