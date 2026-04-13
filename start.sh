#!/bin/bash

cd /home/ORIONII/Interior_Unified

echo "[CAN] Loading SPI and MCP2517FD kernel modules..."
sudo /sbin/modprobe spi-bcm2835
sudo /sbin/modprobe mcp251xfd

sudo /sbin/ip link set can0 up type can bitrate $BITRATE

if ip link show can0 | grep -q "UP"; then
    echo "[CAN] can0 is up"
else
    echo "[CAN] WARNING: can0 failed init"
fi

echo "[SERVER] Starting uvicorn..."
exec "/home/ORIONII/Interior_Unified/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000
