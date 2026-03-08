import time
import math
import gps

session = gps.gps(mode=gps.WATCH_ENABLE)

latest = None
last_print = 0

while True:
    try:
        report = session.next()

        if report["class"] == "TPV":
            lat = getattr(report, "lat", float("nan"))
            lon = getattr(report, "lon", float("nan"))
            mode = getattr(report, "mode", 0)
            t = getattr(report, "time", "unknown")

            if math.isfinite(lat) and math.isfinite(lon):
                latest = (t, lat, lon, mode)

        now = time.time()
        if now - last_print >= 10:
            last_print = now
            if latest is None:
                print("Not connected to GPS")

            else:
                t, lat, lon, mode = latest
                print(f"time={t} mode={mode} lat={lat:.6f} lon={lon:.6f}")

    except KeyError:
        pass
    except StopIteration:
        time.sleep(1)          
