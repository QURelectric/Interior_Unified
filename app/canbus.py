import can
import time
from app.state import vehicle_state, state_lock

MSG1_ID = 0x100
MSG2_ID = 0x101
MSG3_ID = 0x102


def decode_temp(raw):
    return raw - 40


def u16(msb, lsb):
    return (msb << 8) | lsb


def u32(b0, b1, b2, b3):
    return (b0 << 24) | (b1 << 16) | (b2 << 8) | b3


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
                    vehicle_state["batterySOC"] = data[0]
                    vehicle_state["MotorTemp"] = decode_temp(data[1])
                    vehicle_state["InverterTemp"] = decode_temp(data[2])

                # -------- MSG 2 --------
                elif arb_id == MSG2_ID:
                    motor_flag = u16(data[0], data[1])
                    system_flags = u16(data[2], data[3])
                    operating_time = u32(data[4], data[5], data[6], data[7])

                    vehicle_state["MotorFlag"] = motor_flag

                    # convert 16-bit flags → list of bits (matches your state)
                    vehicle_state["SystemFlags"] = [
                        (system_flags >> i) & 1 for i in range(16)
                    ]

                    vehicle_state["OperatingTime"] = operating_time

                # -------- MSG 3 --------
                elif arb_id == MSG3_ID:
                    vehicle_state["FaultLevel"] = data[0]
                    vehicle_state["FaultCode"] = data[1]

                    vehicle_state["Odometer"] = u16(data[2], data[3]) / 10.0
                    vehicle_state["Current"] = u16(data[4], data[5]) / 10.0
                    vehicle_state["Speed"] = u16(data[6], data[7]) / 10.0

                    vehicle_state["timestamp"] = time.time()

        except Exception as e:
            print(f"CAN parse error: {e}")


if __name__ == "__main__":
    can_loop()
