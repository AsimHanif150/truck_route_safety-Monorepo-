"""Risk at each checkpoint, per-route summaries, and the route recommendation. Pure logic."""
from .risk import LEVELS, SCORES, classify
from .weather import weather_key


def forecast_hour_for_eta(eta, start, max_hour):
    """Nearest forecast hour for the moment the truck reaches a checkpoint."""
    hour = round((eta - start).total_seconds() / 3600)
    return max(0, min(max_hour, hour))


def assess_route(route_id, name, route, checkpoints, forecasts, start, load_lb, max_hour):
    """Build the API representation of one route, including its risk summary."""
    miles = {level: 0.0 for level in LEVELS}
    weighted_score = 0.0
    out = []

    for n, cp in enumerate(checkpoints, start=1):
        hourly = [
            {
                'hour': w.hour,
                'wind_mph': w.wind_mph,
                'rain_in_hr': w.rain_in_hr,
                'snow_in_hr': w.snow_in_hr,
                'risk_level': classify(w.wind_mph, w.rain_in_hr, w.snow_in_hr, load_lb),
            }
            for w in forecasts[weather_key(cp.lat, cp.lng)]
        ]
        # The weather that matters is the weather when the truck actually gets there.
        at_eta = hourly[forecast_hour_for_eta(cp.eta, start, max_hour)]
        level = at_eta['risk_level']

        miles[level] += cp.segment_miles
        weighted_score += SCORES[level] * cp.segment_miles
        out.append(
            {
                'id': f'{route_id}-{n}',
                'lat': cp.lat,
                'lng': cp.lng,
                'mile': cp.mile,
                'eta': cp.eta.isoformat().replace('+00:00', 'Z'),
                'risk_level': level,
                'wind_mph': at_eta['wind_mph'],
                'rain_in_hr': at_eta['rain_in_hr'],
                'snow_in_hr': at_eta['snow_in_hr'],
                'forecast': hourly,
            }
        )

    summary = {f'{level}_miles': round(miles[level], 1) for level in LEVELS}
    summary['avg_risk'] = round(weighted_score / route.distance_miles, 2)

    return {
        'id': route_id,
        'name': name,
        'distance_miles': round(route.distance_miles, 1),
        'duration_minutes': round(route.duration_minutes),
        'summary': summary,
        'checkpoints': out,
    }


def rank_key(route):
    """Smaller is better. Follows the assessment order (severe, high, average risk, time),
    with No Travel miles first: a route with a No Travel stretch must never beat one
    that only has Severe stretches."""
    s = route['summary']
    return (
        s['no_travel_miles'],
        s['severe_miles'],
        s['high_miles'],
        s['avg_risk'],
        route['duration_minutes'],
    )


def pick_recommended(routes):
    return min(routes, key=rank_key)
