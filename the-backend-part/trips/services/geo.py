"""Small geographic helpers shared by routing and checkpoints. Pure functions."""
import math

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(a, b):
    """Great-circle distance between two (lat, lng) points, in miles."""
    lat1, lng1, lat2, lng2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(h))


def interpolate(a, b, t):
    """Point a fraction t (0-1) of the way from a to b (fine for short segments)."""
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
