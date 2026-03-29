# app/lap_timer.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


EARTH_RADIUS_M = 6371000.0


def cross_2d(vec_a: tuple[float, float], vec_b: tuple[float, float]) -> float:
    """
    2D cross product. Checking which side of a line a point is on. Line segment intersection math
    """
    return vec_a[0] * vec_b[1] - vec_a[1] * vec_b[0]


def latlon_to_local_xy(lat: float, lon: float, ref_lat: float, ref_lon: float,) -> tuple[float, float]:
    """
    Convert latitude/longitude into local X/Y coordinate system in meters.

    GPS comes in lat/lon, but geometric calculations are easier in a flat local coordinate system.
    """
    x_m = math.radians(lon - ref_lon) * EARTH_RADIUS_M * math.cos(math.radians(ref_lat))
    y_m = math.radians(lat - ref_lat) * EARTH_RADIUS_M
    return x_m, y_m


def segment_intersection_fraction(
    seg1_start: tuple[float, float],
    seg1_end: tuple[float, float],
    seg2_start: tuple[float, float],
    seg2_end: tuple[float, float],
) -> Optional[float]:
    """
    Check whether two line segments intersect.

    If they do, return a value t in [0, 1] telling where the intersection
    happened along the first segment:

        intersection = seg1_start + t * (seg1_end - seg1_start)

    Since GPs updates are discrete. If the finish line is crossed between two GPS samples, t allows us to estimate the crossing time

    Returns:
        t in [0, 1] if the segments intersect
        None if they do not intersect
    """
    seg1_vec = (seg1_end[0] - seg1_start[0], seg1_end[1] - seg1_start[1])
    seg2_vec = (seg2_end[0] - seg2_start[0], seg2_end[1] - seg2_start[1])

    denominator = cross_2d(seg1_vec, seg2_vec)

    # denominator near 0 means the lines are parallel (or almost parallel)
    if abs(denominator) < 1e-9:
        return None

    start_offset = (
        seg2_start[0] - seg1_start[0],
        seg2_start[1] - seg1_start[1],
    )

    t = cross_2d(start_offset, seg2_vec) / denominator
    u = cross_2d(start_offset, seg1_vec) / denominator

    # Both intersection parameters must fall within the finite segments
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        return t

    return None


@dataclass
class GpsSample:
    """
    One GPS sample used by the lap timer.
    """
    lat: float
    lon: float
    timestamp: float
    speed_kmh: float


class LapTimer:
    """
    Gate based lap timer.

    - Define the finish line using TWO GPS points:
        -left side of track
        -right side of track
    - Every time a new GPS point arrives, look at the segment from the
      previous GPS point to the current one.
    - If that segment crosses the finish-line segment, we crossed the line.

    Important:
    The finish-line points should be ordered LEFT to RIGHT when looking in the driving direction.
    If laps never count because the direction check is backwards, flip count_direction=1 to count_direction=-1
    """

    def __init__(
        self,
        start_finish_left: tuple[float, float],
        start_finish_right: tuple[float, float],
        *,
        count_direction: int = 1,
        min_lap_time_s: float = 10.0,
        min_cross_interval_s: float = 2.0,
        min_speed_kmh: float = 5.0,
    ) -> None:
        # Original GPS coordinates for the finish line ends
        self.start_finish_left_latlon = start_finish_left
        self.start_finish_right_latlon = start_finish_right

        # +1 means we only count crossings in one direction
        # -1 means we count the opposite direction instead
        self.count_direction = 1 if count_direction >= 0 else -1

        # Safety filters to avoid false lap triggers
        self.min_lap_time_s = min_lap_time_s
        self.min_cross_interval_s = min_cross_interval_s
        self.min_speed_kmh = min_speed_kmh

        # Use the midpoint of the finish line as the local XY reference
        self.reference_lat = (start_finish_left[0] + start_finish_right[0]) / 2.0
        self.reference_lon = (start_finish_left[1] + start_finish_right[1]) / 2.0

        # Finish line in local XY meters
        self.finish_line_left_xy = latlon_to_local_xy(
            start_finish_left[0],
            start_finish_left[1],
            self.reference_lat,
            self.reference_lon,
        )
        self.finish_line_right_xy = latlon_to_local_xy(
            start_finish_right[0],
            start_finish_right[1],
            self.reference_lat,
            self.reference_lon,
        )

        # Previous GPS sample to form a segment between old and new
        self.previous_sample: Optional[GpsSample] = None

        # Timing state
        self.current_lap_start_time: Optional[float] = None
        self.last_crossing_time: Optional[float] = None

        # Lap stats
        self.lap_count = 0
        self.last_lap_time: Optional[float] = None
        self.best_lap_time: Optional[float] = None
        self.top_speed_this_lap = 0.0

    def _gps_to_local_xy(self, lat: float, lon: float) -> tuple[float, float]:
        """
        Convert a GPS point into the same local XY system as the finish line.
        """
        return latlon_to_local_xy(lat, lon, self.reference_lat, self.reference_lon)

    def _point_side_of_finish_line(self, point_xy: tuple[float, float]) -> float:
        """
        Return which side of the finish line this point is on.

        Positive/negative tells us the side. Ensures crossing only work in the correct direction
        """
        finish_line_vector = (
            self.finish_line_right_xy[0] - self.finish_line_left_xy[0],
            self.finish_line_right_xy[1] - self.finish_line_left_xy[1],
        )
        point_from_line_start = (
            point_xy[0] - self.finish_line_left_xy[0],
            point_xy[1] - self.finish_line_left_xy[1],
        )
        return cross_2d(finish_line_vector, point_from_line_start)

    def _write_state(self, state: dict, timestamp: float) -> None:
        """
        Write the current lap timer values into the shared state dict.
        """
        state["LapArmed"] = self.current_lap_start_time is not None
        state["LapNumber"] = self.lap_count
        state["LastLapTime"] = self.last_lap_time
        state["BestLapTime"] = self.best_lap_time
        state["TopSpeedThisLap"] = self.top_speed_this_lap

        if self.current_lap_start_time is None:
            state["LapTime"] = 0.0
        else:
            state["LapTime"] = max(0.0, timestamp - self.current_lap_start_time)

    def update_locked(
        self,
        state: dict,
        lat: float,
        lon: float,
        timestamp: float,
        speed_kmh: float,
    ) -> bool:
        """
        Update the lap timer using one new GPS sample.

        Assumes
        - Caller already holds the shared state lock
        - 'state' is the shared vehicle state dict

        Returns:
            True a full lap was completed on this update
            False no lap completed
        """
        # Ignore invalid GPS/timestamp values
        if not (math.isfinite(lat) and math.isfinite(lon) and math.isfinite(timestamp)):
            return False

        speed_kmh = float(speed_kmh or 0.0)

        current_sample = GpsSample(
            lat=lat,
            lon=lon,
            timestamp=timestamp,
            speed_kmh=speed_kmh,
        )

        lap_completed = False

        # Keep the public state updated, even if no crossing happens
        self._write_state(state, timestamp)

        if self.previous_sample is not None:
            previous_xy = self._gps_to_local_xy(
                self.previous_sample.lat,
                self.previous_sample.lon,
            )
            current_xy = self._gps_to_local_xy(current_sample.lat, current_sample.lon)

            # was finish line crossed?
            crossing_fraction = segment_intersection_fraction(
                previous_xy,
                current_xy,
                self.finish_line_left_xy,
                self.finish_line_right_xy,
            )

            # Only consider crossings if above min speed threshold
            if crossing_fraction is not None and speed_kmh >= self.min_speed_kmh:
                previous_side = self._point_side_of_finish_line(previous_xy)
                current_side = self._point_side_of_finish_line(current_xy)

                # Count only the intended direction
                if self.count_direction > 0:
                    direction_is_correct = previous_side < 0.0 <= current_side
                else:
                    direction_is_correct = previous_side > 0.0 >= current_side

                # Estimate the exact time of crossing using interpolation
                crossing_time = (
                    self.previous_sample.timestamp
                    + crossing_fraction
                    * (current_sample.timestamp - self.previous_sample.timestamp)
                )

                # Prevent double triggering if GPS bounces near the line
                enough_time_since_last_cross = (
                    self.last_crossing_time is None
                    or (crossing_time - self.last_crossing_time) >= self.min_cross_interval_s
                )

                if direction_is_correct and enough_time_since_last_cross:
                    self.last_crossing_time = crossing_time

                    # First valid crossing starts the lap timer, but does NOT count a lap yet.
                    # kart rolls out
                    # crosses start/finish once
                    # that arms the timer
                    if self.current_lap_start_time is None:
                        self.current_lap_start_time = crossing_time
                        self.top_speed_this_lap = speed_kmh

                    else:
                        completed_lap_time = crossing_time - self.current_lap_start_time

                        # Ignore short laps caused by GPS glitches
                        if completed_lap_time >= self.min_lap_time_s:
                            best_lap_before_this_crossing = self.best_lap_time

                            self.last_lap_time = completed_lap_time

                            if (
                                self.best_lap_time is None
                                or completed_lap_time < self.best_lap_time
                            ):
                                self.best_lap_time = completed_lap_time

                            self.lap_count += 1
                            self.current_lap_start_time = crossing_time
                            self.top_speed_this_lap = 0.0
                            lap_completed = True

                            # Delta is relative to the best lap that existed BEFORE
                            # this newly completed lap was processed.
                            state["LapTimeDelta"] = (
                                None
                                if best_lap_before_this_crossing is None
                                else completed_lap_time - best_lap_before_this_crossing
                            )

        # If a lap is currently active, keep updating current lap elapsed time
        # and the max speed seen so far during this lap.
        if self.current_lap_start_time is not None:
            self.top_speed_this_lap = max(self.top_speed_this_lap, speed_kmh)
            state["LapTime"] = max(0.0, timestamp - self.current_lap_start_time)

        # Final write-back so state always matches the latest internal values
        self._write_state(state, timestamp)

        # Save current sample for next update
        self.previous_sample = current_sample

        return lap_completed