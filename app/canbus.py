import can
import time
from app.state import vehicle_state, state_lock

MSG1_ID = 0x201
MSG2_ID = 0x202
MSG3_ID = 0x203

def decode_temp(raw):
    return raw - 40

def u16_le(lo, hi):
    return (hi << 8) | lo

def i16_le(low, high):
    val = (high << 8) | low
    if val >= 0x8000:  # If the sign bit is set, it's negative
        val -= 0x10000
    return val

def can_loop():
    bus = can.interface.Bus(channel="can0", interface="socketcan")
    while True:
        msg = bus.recv(timeout=1.0)
        if msg is None:
            continue
        if msg.is_error_frame or msg.is_remote_frame:
            continue
        data = msg.data
        arb_id = msg.arbitration_id
        try:
            with state_lock:
                # -------- MSG 1 --------
                if arb_id == MSG1_ID:
                    vehicle_state["batterySOC"]   = data[0]
                    vehicle_state["MotorTemp"]    = decode_temp(data[1])
                    vehicle_state["InverterTemp"] = decode_temp(data[2])

                # -------- MSG 2 --------
                elif arb_id == MSG2_ID:
                    motor_flags  = u16_le(data[0], data[1])
                    system_flags = u16_le(data[2], data[3])
                    op_hours     = u16_le(data[4], data[5])
                    op_minutes   = data[6]
                    op_seconds   = data[7]

                    vehicle_state["MotorFlag"]    = motor_flags
                    vehicle_state["SystemFlags"]  = [
                        (system_flags >> i) & 1 for i in range(16)
                    ]
                    vehicle_state["OperatingTime"] = {
                        "hours":   op_hours,
                        "minutes": op_minutes,
                        "seconds": op_seconds
                    }

                # -------- MSG 3 --------
                elif arb_id == MSG3_ID:
                    vehicle_state["FaultLevel"] = data[0]
                    vehicle_state["FaultCode"]  = data[1]
                    vehicle_state["Odometer"]   = u16_le(data[2], data[3]) / 10.0
                    vehicle_state["Current"]    = i16_le(data[4], data[5]) / 10.0
                    vehicle_state["Speed"]      = u16_le(data[6], data[7]) / 10.0
                    vehicle_state["timestamp"]  = time.time()

        except Exception as e:
            print(f"CAN parse error: {e}")

if __name__ == "__main__":
    can_loop()
