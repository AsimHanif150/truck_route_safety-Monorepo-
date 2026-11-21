"""Pick weather checkpoints along a route and estimate when the truck reaches each one.

Pure functions: no network, no Django. ETAs assume the truck keeps the route's average
speed for the whole trip (no rest stops), which is the simplest honest estimate.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from .geo import haversine_miles, interpolate

CHECKPOINT_INTERVALS = (10, 25, 50)  # miles allowed by the assessment


@dataclass(frozen=True)
class Checkpoint:
    lat: float
    lng: float
    mile: float  # distance from the start
    eta: datetime
    segment_miles: float  # stretch of road this checkpoint stands for (used for risk miles)


def _cumulative_miles(geometry):
    totals = [0.0]
    for a, b in zip(geometry, geometry[1:]):
        totals.append(totals[-1] + haversine_miles(a, b))
    return totals


def build_checkpoints(route, departure, interval_miles):
    """Checkpoints at mile 0, every `interval_miles`, and at the destination.

    `route` needs `.geometry`, `.distance_miles` and `.duration_minutes`;
    `departure` must be a timezone-aware datetime.
    """
    if interval_miles not in CHECKPOINT_INTERVALS:
        raise ValueError(f'interval must be one of {CHECKPOINT_INTERVALS}')
    geometry = route.geometry
    if len(geometry) < 2:
        raise ValueError('route needs at least two points')

    cumulative = _cumulative_miles(geometry)
    # The API's own distance is the reference; geometry length can differ slightly.
    scale = route.distance_miles / cumulative[-1] if cumulative[-1] else 1.0
    total = route.distance_miles

    targets = [0.0]
    mile = float(interval_miles)
    while mile < total:
        targets.append(mile)
        mile += interval_miles
    targets.append(total)

    points = []
    i = 0
    for target in targets:
        while i < len(cumulative) - 2 and cumulative[i + 1] * scale < target:
            i += 1
        start, end = cumulative[i] * scale, cumulative[i + 1] * scale
        t = 0.0 if end == start else min(1.0, max(0.0, (target - start) / (end - start)))
        points.append((interpolate(geometry[i], geometry[i + 1], t), target))

    checkpoints = []
    for n, ((lat, lng), mile) in enumerate(points):
        before = points[n - 1][1] if n > 0 else mile
        after = points[n + 1][1] if n < len(points) - 1 else mile
        low = 0.0 if n == 0 else (before + mile) / 2
        high = total if n == len(points) - 1 else (mile + after) / 2
        eta = departure + timedelta(minutes=route.duration_minutes * mile / total)
        checkpoints.append(
            Checkpoint(
                lat=round(lat, 5),
                lng=round(lng, 5),
                mile=round(mile, 1),
                eta=eta,
                segment_miles=high - low,
            )
        )
    return checkpoints
