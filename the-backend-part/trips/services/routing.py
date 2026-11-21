"""Build three distinct routes between two places (OSRM public server, car profile, no API key).
 
Why not use the provider's own "alternative routes" option? It is limited to fairly short
routes, and these trips are hundreds of miles long. Instead we ask for the fastest route,
then for routes that pass through a waypoint pushed to the left and to the right of the
midpoint. Routes that mostly overlap an existing one are thrown away.
 
Note: the public OSRM server only offers a car profile. A truck-aware provider (for example
OpenRouteService driving-hgv, Geoapify or HERE) can replace `_directions` without changing
anything else in this module.
"""
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
 
import requests
 
from .errors import TripPlanningError
from .geo import haversine_miles
 
DIRECTIONS_URL = 'https://router.project-osrm.org/route/v1/driving/'
TIMEOUT_SECONDS = 40
METERS_PER_MILE = 1609.344
HEADERS = {'User-Agent': 'HaulSafe-assessment/1.0'}
 
TARGET_ROUTES = 3
OFFSET_SCALES = (0.12, 0.25)  # sideways push, as a fraction of the straight-line distance
MAX_DURATION_RATIO = 1.6  # ignore detours more than 60% slower than the fastest route
DUPLICATE_OVERLAP = 0.85  # share of a route lying on another route => treat as the same route
SAME_ROAD_MILES = 2.5
MILES_PER_DEGREE_LAT = 69.0
 
 
@dataclass(frozen=True)
class RouteOption:
    geometry: tuple  # ((lat, lng), ...)
    distance_miles: float
    duration_minutes: float
 
 
def offset_waypoint(origin, destination, scale, side):
    """Midpoint of the trip pushed sideways (side = +1 or -1) by scale * trip length."""
    mid_lat = (origin[0] + destination[0]) / 2
    mid_lng = (origin[1] + destination[1]) / 2
    cos_lat = math.cos(math.radians(mid_lat))
 
    # Work in miles on a local flat plane: x = east, y = north.
    dx = (destination[1] - origin[1]) * cos_lat * MILES_PER_DEGREE_LAT
    dy = (destination[0] - origin[0]) * MILES_PER_DEGREE_LAT
    length = math.hypot(dx, dy)
    if length == 0:
        raise TripPlanningError('Origin and destination are the same place.')
 
    push = scale * length * side
    east = (-dy / length) * push  # perpendicular to the direction of travel
    north = (dx / length) * push
    return (
        mid_lat + north / MILES_PER_DEGREE_LAT,
        mid_lng + east / (MILES_PER_DEGREE_LAT * cos_lat),
    )
 
 
def overlap_fraction(route, other, samples=60):
    """Fraction of `route` that lies within SAME_ROAD_MILES of `other`."""
    points = route.geometry
    step = max(1, len(points) // samples)
    sampled = points[::step]
    close = sum(
        1
        for p in sampled
        if any(haversine_miles(p, q) <= SAME_ROAD_MILES for q in other.geometry)
    )
    return close / len(sampled)
 
 
def _directions(points):
    """Ask the routing API for one route through the given (lat, lng) points."""
    coords = ';'.join(f'{lng},{lat}' for lat, lng in points)
    try:
        response = requests.get(
            DIRECTIONS_URL + coords,
            params={'overview': 'full', 'geometries': 'geojson'},
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        raise TripPlanningError('The routing service is unavailable. Please try again.', status=502)
 
    if response.status_code == 429:
        raise TripPlanningError('Routing service is busy. Please try again later.', status=503)
    if response.status_code != 200:
        raise TripPlanningError('No route could be found between these places.', status=422)
 
    try:
        data = response.json()
    except ValueError:
        raise TripPlanningError('The routing service returned unexpected data.', status=502)
 
    if data.get('code') != 'Ok' or not data.get('routes'):
        raise TripPlanningError('No route could be found between these places.', status=422)
 
    route = data['routes'][0]
    return RouteOption(
        geometry=tuple((lat, lng) for lng, lat in route['geometry']['coordinates']),
        distance_miles=route['distance'] / METERS_PER_MILE,
        duration_minutes=route['duration'] / 60,
    )
 
 
def _try_directions(points):
    try:
        return _directions(points)
    except TripPlanningError:
        return None  # this detour is not drivable
 
 
def get_route_options(origin, destination):
    """Return up to three distinct routes, fastest first. `origin`/`destination` are (lat, lng)."""
    fastest = _directions([origin, destination])  # errors here mean the trip is impossible
 
    # Detours are requested in parallel; they are independent and each call is slow.
    vias = [
        offset_waypoint(origin, destination, scale, side)
        for scale in OFFSET_SCALES
        for side in (1, -1)
    ]
    with ThreadPoolExecutor(max_workers=2) as pool:  # polite to the public server
        candidates = list(pool.map(lambda via: _try_directions([origin, via, destination]), vias))
 
    routes = [fastest]
    for candidate in candidates:  # gentler detours come first
        if len(routes) >= TARGET_ROUTES:
            break
        if candidate is None:
            continue
        if candidate.duration_minutes > fastest.duration_minutes * MAX_DURATION_RATIO:
            continue
        if any(overlap_fraction(candidate, r) >= DUPLICATE_OVERLAP for r in routes):
            continue
        routes.append(candidate)
 
    return sorted(routes, key=lambda r: r.duration_minutes)
 

