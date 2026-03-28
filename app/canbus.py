import time
import random
from app.state import vehicle_state, state_lock

#### canbus.py ####
# This file will eventually hold the code to communicate with the motor controller
# right now this is only a simulated value

def can_loop():
    while True:
        with state_lock:
            vehicle_state["Speed"] = random.uniform(0, 80)
            vehicle_state["MotorTemp"] += random.uniform(-0.2, 0.5)
            vehicle_state["OperatingTime"] += 0.1
            vehicle_state["batterySOC"] -= 0.1
            vehicle_state["timestamp"] = time.time()
            if(random.uniform(0,100) >= 75):
                vehicle_state["MotorFlag"] = 1
            else: 
                vehicle_state["MotorFlag"] = 0
        time.sleep(0.1)  # 10 Hz

if __name__ == "__main__":
    can_loop()
