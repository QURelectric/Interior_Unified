import can
import time
from dataclasses import dataclass, asdict


# --------------------------------------------------
# CAN IDs
# Your Arduino example uses 0x100, 0x101, 0x102.
# If your final controller literally uses decimal 100/101/102,
# change these to 100, 101, 102.
# --------------------------------------------------
MSG1_ID = 0x100
MSG2_ID = 0x101
MSG3_ID = 0x102


@dataclass
class MotorControllerState:
    battery_soc: int | None = None                 # %
    motor_temp_c: int | None = None                # decoded using -40 offset
    inverter_temp_c: int | None = None             # decoded using -40 offset

    motor_flags: int | None = None                 # 16-bit
    system_flags: int | None = None                # 16-bit
    operating_time_seconds: int | None = None      # raw decoded 32-bit seconds
    operating_time_hms: str | None = None

    fault_level: int | None = None
    fault_code: int | None = None
    odometer: float | None = None                  # scaled /10
    current: float | None = None                   # scaled /10
    speed: float | None = None                     # scaled /10

    last_update_msg1: float | None = None
    last_update_msg2: float | None = None
    last_update_msg3: float | None = None


def decode_temp(raw: int) -> int:
    # [0,255] -> [-40,215] C
    return raw - 40


def decode_u16_be(msb: int, lsb: int) -> int:
    return (msb << 8) | lsb


def decode_u32_be(b0: int, b1: int, b2: int, b3: int) -> int:
    return (b0 << 24) | (b1 << 16) | (b2 << 8) | b3


def format_hms(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_msg1(data: bytes, state: MotorControllerState) -> None:
    if len(data) != 8:
        raise ValueError(f"MSG1 expected 8 bytes, got {len(data)}")

    state.battery_soc = data[0]
    state.motor_temp_c = decode_temp(data[1])
    state.inverter_temp_c = decode_temp(data[2])
    state.last_update_msg1 = time.time()


def parse_msg2(data: bytes, state: MotorControllerState) -> None:
    if len(data) != 8:
        raise ValueError(f"MSG2 expected 8 bytes, got {len(data)}")

    state.motor_flags = decode_u16_be(data[0], data[1])
    state.system_flags = decode_u16_be(data[2], data[3])

    operating_time_seconds = decode_u32_be(data[4], data[5], data[6], data[7])
    state.operating_time_seconds = operating_time_seconds
    state.operating_time_hms = format_hms(operating_time_seconds)

    state.last_update_msg2 = time.time()


def parse_msg3(data: bytes, state: MotorControllerState) -> None:
    if len(data) != 8:
        raise ValueError(f"MSG3 expected 8 bytes, got {len(data)}")

    state.fault_level = data[0]
    state.fault_code = data[1]

    odometer_raw = decode_u16_be(data[2], data[3])
    current_raw = decode_u16_be(data[4], data[5])
    speed_raw = decode_u16_be(data[6], data[7])

    state.odometer = odometer_raw / 10.0
    state.current = current_raw / 10.0
    state.speed = speed_raw / 10.0

    state.last_update_msg3 = time.time()


def print_state(state: MotorControllerState) -> None:
    print("\n--- Decoded Motor Controller State ---")
    print(f"Battery SOC      : {state.battery_soc} %")
    print(f"Motor Temp       : {state.motor_temp_c} C")
    print(f"Inverter Temp    : {state.inverter_temp_c} C")
    print(f"Motor Flags      : 0x{state.motor_flags:04X}" if state.motor_flags is not None else "Motor Flags      : None")
    print(f"System Flags     : 0x{state.system_flags:04X}" if state.system_flags is not None else "System Flags     : None")
    print(f"Operating Time   : {state.operating_time_seconds} s ({state.operating_time_hms})")
    print(f"Fault Level      : {state.fault_level}")
    print(f"Fault Code       : {state.fault_code}")
    print(f"Odometer         : {state.odometer}")
    print(f"Current          : {state.current}")
    print(f"Speed            : {state.speed}")
    print("--------------------------------------")


def main() -> None:
    state = MotorControllerState()

    # PiCAN guide example uses channel='can0' and python-can on SocketCAN. :contentReference[oaicite:1]{index=1}
    bus = can.interface.Bus(channel="can0", interface="socketcan")

    print("Listening on can0 for 0x100, 0x101, 0x102...")

    while True:
        msg = bus.recv(timeout=1.0)
        if msg is None:
            continue

        if msg.is_error_frame:
            print("Received CAN error frame")
            continue

        if msg.is_remote_frame:
            print("Ignoring remote frame")
            continue

        arbitration_id = msg.arbitration_id
        data = msg.data

        try:
            if arbitration_id == MSG1_ID:
                parse_msg1(data, state)
                print(f"RX MSG1 {hex(arbitration_id)} {data.hex(' ')}")

            elif arbitration_id == MSG2_ID:
                parse_msg2(data, state)
                print(f"RX MSG2 {hex(arbitration_id)} {data.hex(' ')}")

            elif arbitration_id == MSG3_ID:
                parse_msg3(data, state)
                print(f"RX MSG3 {hex(arbitration_id)} {data.hex(' ')}")

                # Print full decoded state whenever the 3rd packet arrives
                print_state(state)

            else:
                # Ignore unrelated CAN messages
                pass

        except Exception as e:
            print(f"Failed to parse message {hex(arbitration_id)}: {e}")


if __name__ == "__main__":
    main()
