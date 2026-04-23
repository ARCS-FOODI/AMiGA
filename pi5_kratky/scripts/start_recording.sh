#!/bin/bash

# Configuration
REC_DIR="/home/foodi/kratky/recordings"
LOG_FILE="/home/foodi/kratky/logs/ffmpeg_log.txt"
STREAM_KEY="$1"
NOW=$(date +"%Y%m%d-%H%M")
FILENAME="$REC_DIR/recording-$NOW.mkv"

# DEBUG: Print the exact time and key we received to the log
echo "------------------------------------------------" >> "$LOG_FILE"
echo "STARTING RECORDING AT: $NOW" >> "$LOG_FILE"
echo "RECEIVED STREAM KEY: '$STREAM_KEY'" >> "$LOG_FILE"

# Check if Key is empty (Common error)
if [ -z "$STREAM_KEY" ]; then
    echo "ERROR: No stream key passed! defaulting to 'test'" >> "$LOG_FILE"
    STREAM_KEY="test"
fi

echo "EXECUTING: ffmpeg -i rtmp://127.0.0.1/live/$STREAM_KEY ..." >> "$LOG_FILE"

# The Command
/usr/bin/ffmpeg -i rtmp://127.0.0.1/live/$STREAM_KEY -r 1 -c:v libx265 -crf 28 -preset ultrafast -f matroska "$FILENAME" 2>>"$LOG_FILE"