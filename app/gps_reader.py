import math
import time
import gps

from app.state import vehicle_state, state_lock
from app.lap_timer import LapTimer


# Replace these with the real GPS coordinates for the two ends of the start/finish line
# Order them LEFT to RIGHT while looking in the driving direction.
START_FINISH_LEFT = (43.000000, -79.000100)
START_FINISH_RIGHT = (43.000000, -78.999900)


# Create timer object and keep it alive for the whole program.
lap_timer = LapTimer(
    START_FINISH_LEFT,
    START_FINISH_RIGHT,
    count_direction=1,      # flip to -1 if it only works backwards
    min_lap_time_s=10.0,    # reject impossible tiny laps
    min_cross_interval_s=2.0,  # stop double-triggering near the line
    min_speed_kmh=5.0,      # ignore crossings if  moving too slow
)


def gps_loop():
    while True:
        session = None

        try:
            print("[GPS] Connecting to gpsd")
            session = gps.gps(mode=gps.WATCH_ENABLE)
            print("[GPS] Connected to gpsd")

            # GPS connection succeeded
            with state_lock:
                vehicle_state["GPSConnected"] = True

            while True:
                report = session.next()

                # Only care about normal position reports
                if report["class"] != "TPV":
                    continue

                # Try to read latitude and longitude.
                lat = getattr(report, "lat", float("nan"))
                lon = getattr(report, "lon", float("nan"))

                # Use one timestamp for this whole update
                now = time.time()

                with state_lock:
                    vehicle_state["timestamp"] = now

                    # Only update state if the GPS values are valid numbers
                    if math.isfinite(lat) and math.isfinite(lon):
                        vehicle_state["GPSConnected"] = True
                        vehicle_state["Latitude"] = lat
                        vehicle_state["Longitude"] = lon
                        vehicle_state["GPS"] = [lat, lon]

                        # Feed this GPS point into the lap timer.
                        # The lap timer will update LapTime, LapNumber, LastLapTime, BestLapTime, LapTimeDelta
                        lap_timer.update_locked(
                            vehicle_state,
                            lat=lat,
                            lon=lon,
                            timestamp=now,
                            speed_kmh=vehicle_state.get("Speed", 0.0),
                        )

        except KeyError:
            pass

        except StopIteration:
            print("[GPS] gpsd stream ended, retrying")
            time.sleep(1)

        except Exception as e:
            print(f"[GPS] Error: {e}")
            with state_lock:
                vehicle_state["GPSConnected"] = False
            time.sleep(1)