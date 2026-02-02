import threading
import time

#### state.py ####
# this file holds the current object state of the vehicle, accessed by every other subroutine program


state_lock = threading.Lock()

vehicle_state = {
    "batterySOC": 72,
    "MotorTemp": 50,
    "InverterTemp": 55,
    "LapTime": 3.0,
    "LapTimeDelta": 0.1,
    "FaultLevel": 0,
    "FaultCode": 0,
    "MotorFlag": 0,
    "SystemFlags": [0]*16,
    "Odometer": 0.0,
    "Current": 0.0,
    "Speed": 10.0,
    "OperatingTime": 100.0,
    "timestamp": time.time()
}
