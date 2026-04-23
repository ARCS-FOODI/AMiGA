#!/bin/bash

# Configuration
DURATION=180
#DURATION=39600  # 11 hours in seconds
COOLDOWN=180     # 1 minute between segments

# 1. THE INITIAL BOOT DELAY
# Gives the Pi 5 time to initialize network/camera before the first launch
echo "System just started. Waiting 30s for network and camera..."
sleep 30

while true
do
    # 1. START OBS (Your verified command)
    # --startstreaming kicks off the feed
    # --disable-shutdown-check skips the safe mode prompt
    obs --startstreaming --disable-shutdown-check &

