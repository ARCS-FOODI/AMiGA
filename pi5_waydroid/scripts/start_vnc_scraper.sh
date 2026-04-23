#!/bin/bash
# Initial wait for the desktop to be ready
sleep 10
# INF loop
while true
do
    # Run the VNC script
    /usr/bin/x0vncserver -display :0 -passwordfile $HOME/.vnc/passwd -localhost no -AlwaysShared -AcceptSetDesktopSize=0

    # process
    sleep 2
done
