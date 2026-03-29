# Kart Telemetry and Driver Dashboard

## Overview

This project implements a basic telemetry dashboard for a racing go-kart. It collects vehicle data (e.g., speed, battery state, motor temperature) from a CAN bus or simulation, maintains the data in a shared local state, and provides real-time visualization for the driver via a FastAPI web interface. The same data can be published via MQTT for a remote pit crew display.

### Project Structure

- `state.py` – contains the shared vehicle state dictionary and a thread lock.
- `can_sim.py` – simulates CAN bus updates; in a real implementation this will read from the kart’s CAN bus and update the shared state.
- `mqtt_client.py` – publishes the current state to an MQTT broker.
- `main.py` – FastAPI app providing:
  - `/driver` web page showing live telemetry via WebSockets.
  - background tasks for CAN updates and MQTT publishing.
- `templates/driver.html` – HTML template for the driver display.

### How it Works

1. The CAN or simulation thread continuously updates the shared vehicle state.
2. The MQTT thread reads the state and publishes it to the broker at a set rate.
3. FastAPI serves the driver page and streams updates over a WebSocket connection.
4. The driver’s web page connects to the WebSocket and updates values in real time.

---

## Installation Guide

1. Clone the repository:
`git clone <repository-url>`
`cd <repository-directory>`
2. Create a Python virtual environment:
`python3 -m venv .venv`
3. Activate the virtual environment:
- On Linux/macOS:
`source .venv/bin/activate`
- On Windows (PowerShell):
`.venv\Scripts\Activate.ps1`

4. Install required packages:
`pip install -r requirements.txt`

5. Run the FastAPI server:
`uvicorn app.main:app --host 0.0.0.0 --port 8000`

---

## Libraries Used

- FastAPI
- Uvicorn
- Jinja2
- Paho-MQTT

