from app.lap_timer import LapTimer


def show(label, state):
    print(f"\n--- {label} ---")
    print("LapArmed         =", state["LapArmed"])
    print("LapNumber        =", state["LapNumber"])
    print("LapTime          =", state["LapTime"])
    print("LastLapTime      =", state["LastLapTime"])
    print("BestLapTime      =", state["BestLapTime"])
    print("LapTimeDelta     =", state["LapTimeDelta"])
    print("TopSpeedThisLap  =", state["TopSpeedThisLap"])


START_FINISH_LEFT = (43.000000, -79.000100)
START_FINISH_RIGHT = (43.000000, -78.999900)

timer = LapTimer(
    START_FINISH_LEFT,
    START_FINISH_RIGHT,
    count_direction=1,
    min_lap_time_s=10.0,
    min_cross_interval_s=2.0,
    min_speed_kmh=5.0,
)

state = {
    "LapArmed": False,
    "LapNumber": 0,
    "LapTime": 0.0,
    "LapTimeDelta": None,
    "LastLapTime": None,
    "BestLapTime": None,
    "TopSpeedThisLap": 0.0,
}


def feed(lat, lon, t, speed):
    lap_done = timer.update_locked(
        state,
        lat=lat,
        lon=lon,
        timestamp=t,
        speed_kmh=speed,
    )
    print(
        f"t={t:>5.1f}  lat={lat:.7f} lon={lon:.7f} "
        f"speed={speed:>4.1f}  lap_done={lap_done}"
    )
    return lap_done


print("TEST 1: first crossing should arm timer but not count a lap")
feed(42.9999000, -79.000000, 0.0, 20.0)
feed(43.0001000, -79.000000, 1.0, 20.0)
show("after first crossing", state)

assert state["LapArmed"] is True
assert state["LapNumber"] == 0
assert state["LastLapTime"] is None
assert state["BestLapTime"] is None

print("\nTEST 2: second valid crossing after >10 s should count 1 lap")
feed(42.9999000, -79.000000, 12.0, 25.0)
lap_done = feed(43.0001000, -79.000000, 13.0, 25.0)
show("after second crossing", state)

assert lap_done is True
assert state["LapNumber"] == 1
assert state["LastLapTime"] is not None
assert abs(state["LastLapTime"] - 12.0) < 0.2
assert abs(state["BestLapTime"] - 12.0) < 0.2
assert state["LapTimeDelta"] is None

print("\nTEST 3: wrong-direction crossing should not count")
before_laps = state["LapNumber"]
feed(43.0001000, -79.000000, 20.0, 30.0)
lap_done = feed(42.9999000, -79.000000, 21.0, 30.0)
show("after wrong-direction crossing", state)

assert lap_done is False
assert state["LapNumber"] == before_laps

print("\nTEST 4: double-trigger too soon should be ignored")
feed(42.9999000, -79.000000, 26.0, 30.0)
lap_done = feed(43.0001000, -79.000000, 27.0, 30.0)
assert lap_done is True

before_laps = state["LapNumber"]
feed(42.9999000, -79.000000, 27.5, 30.0)
lap_done = feed(43.0001000, -79.000000, 28.0, 30.0)
show("after too-soon crossing", state)

assert lap_done is False
assert state["LapNumber"] == before_laps

print("\nTEST 5: crossing at too-low speed should be ignored")
before_laps = state["LapNumber"]
feed(42.9999000, -79.000000, 40.0, 2.0)
lap_done = feed(43.0001000, -79.000000, 41.0, 2.0)
show("after low-speed crossing", state)

assert lap_done is False
assert state["LapNumber"] == before_laps

print("\nTEST 6: moving around on one side of the line should never count a lap")

timer2 = LapTimer(
    START_FINISH_LEFT,
    START_FINISH_RIGHT,
    count_direction=1,
    min_lap_time_s=10.0,
    min_cross_interval_s=2.0,
    min_speed_kmh=5.0,
)

state2 = {
    "LapArmed": False,
    "LapNumber": 0,
    "LapTime": 0.0,
    "LapTimeDelta": None,
    "LastLapTime": None,
    "BestLapTime": None,
    "TopSpeedThisLap": 0.0,
}

def feed2(lat, lon, t, speed):
    lap_done = timer2.update_locked(
        state2,
        lat=lat,
        lon=lon,
        timestamp=t,
        speed_kmh=speed,
    )
    print(
        f"t={t:>5.1f}  lat={lat:.7f} lon={lon:.7f} "
        f"speed={speed:>4.1f}  lap_done={lap_done}"
    )
    return lap_done

# All of these points stay BELOW the finish line (lat < 43.000000),
# so the path moves around but never crosses it.
feed2(42.9998500, -79.0000500, 0.0, 20.0)
feed2(42.9998700, -79.0000000, 1.0, 22.0)
feed2(42.9998900, -78.9999500, 2.0, 24.0)
feed2(42.9998800, -79.0000200, 3.0, 18.0)
feed2(42.9998600, -79.0000700, 4.0, 19.0)

show("after no-crossing movement", state2)

assert state2["LapArmed"] is False
assert state2["LapNumber"] == 0
assert state2["LastLapTime"] is None
assert state2["BestLapTime"] is None
assert state2["LapTime"] == 0.0

print("TEST 6 PASSED")

print("\nALL TESTS PASSED")