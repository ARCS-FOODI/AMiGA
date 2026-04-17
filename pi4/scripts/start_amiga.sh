#!/bin/bash

# Initial wait for the desktop and network to be ready
sleep 15

# INF loop to keep the AMiGA server running even if it crashes
while true
do
    echo "Starting AMiGA Server..."
    # Change to the scripts directory
    cd /home/sensoil/Documents/AMiGA/scripts
    
    # Run the startup script
    ./start.sh

    # If the script exits, wait a few seconds before restarting
    echo "AMiGA Server stopped. Restarting in 5 seconds..."
    sleep 5
done
