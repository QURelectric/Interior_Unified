#!/bin/bash

# Kill any old gpsd process
sudo pkill gpsd 2>/dev/null

# Start gpsd in the background listening for Android forwarded GPS data
gpsd -Nn udp://*:29998 &

GPSD_PID=$!

sleep 2

# Stop gpsd when script exits
cleanup() {
    kill $GPSD_PID 2>/dev/null
}
trap cleanup EXIT

# Run GPS reader
python3 gps_test.py