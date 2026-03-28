import math
import time
import gps

from app.state import vehicle_state, state_lock


def gps_loop():
    while True:
        session = None
        try:
            print("[GPS] Connecting to gpsd")
            session = gps.gps(mode=gps.WATCH_ENABLE)
            print("[GPS] Connected to gpsd")

            while True:
                report = session.next()

                if report["class"] != "TPV":
                    continue

                lat = getattr(report, "lat", float("nan"))
                lon = getattr(report, "lon", float("nan"))

                with state_lock:
                    vehicle_state["timestamp"] = time.time()

                    if math.isfinite(lat) and math.isfinite(lon):
                        vehicle_state["Latitude"] = lat
                        vehicle_state["Longitude"] = lon

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