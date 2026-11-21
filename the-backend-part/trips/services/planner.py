"""Put the pieces together: places -> routes -> checkpoints -> weather -> risk -> recommendation."""
from datetime import timezone

from .checkpoints import build_checkpoints
from .geocoding import geocode
from .recommend import assess_route, pick_recommended
from .routing import get_route_options
from .weather import fetch_forecasts

FORECAST_HOURS = 48
MAX_GEOMETRY_POINTS = 2000  # keeps the response small; the map does not need every road vertex


def _simplify(geometry):
    """Thin out a long polyline evenly, always keeping the first and last point."""
    step = max(1, -(-len(geometry) // MAX_GEOMETRY_POINTS))  # ceiling division
    kept = list(geometry[::step])
    if kept[-1] != geometry[-1]:
        kept.append(geometry[-1])
    return [[round(lat, 5), round(lng, 5)] for lat, lng in kept]


def _iso(moment):
    return moment.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def plan_trip(origin_text, destination_text, departure, load_lb, interval_miles):
    """Return the JSON-ready trip plan. `departure` is a timezone-aware datetime."""
    origin = geocode(origin_text)
    destination = geocode(destination_text)
    options = get_route_options((origin.lat, origin.lng), (destination.lat, destination.lng))

    departure = departure.astimezone(timezone.utc)
    start = departure.replace(minute=0, second=0, microsecond=0)  # forecast hour 0

    checkpoint_sets = [build_checkpoints(route, departure, interval_miles) for route in options]
    points = [(cp.lat, cp.lng) for cps in checkpoint_sets for cp in cps]
    forecasts = fetch_forecasts(points, start, FORECAST_HOURS)

    routes = []
    for n, (route, checkpoints) in enumerate(zip(options, checkpoint_sets), start=1):
        name = f'Route {n} (Fastest)' if n == 1 else f'Route {n}'
        assessed = assess_route(f'r{n}', name, route, checkpoints, forecasts, start, load_lb, FORECAST_HOURS)
        assessed['geometry'] = _simplify(route.geometry)
        routes.append(assessed)

    best = pick_recommended(routes)
    recommended_id = best['id']
    warnings = []

    # pick_recommended ranks No Travel miles first, so if even the best route has some,
    # every route does. No Travel is a safety disqualifier: recommend nothing.
    if best['summary']['no_travel_miles'] > 0:
        recommended_id = None
        warnings.append(
            'No safe route is available: every route has stretches rated No Travel for '
            'this load and departure time. Consider leaving at a different time.'
        )

    return {
        'origin': {'name': origin.name, 'lat': origin.lat, 'lng': origin.lng},
        'destination': {'name': destination.name, 'lat': destination.lat, 'lng': destination.lng},
        'forecast_start': _iso(start),
        'forecast_hours': FORECAST_HOURS,
        'recommended_route_id': recommended_id,
        'warnings': warnings,
        'routes': routes,
    }