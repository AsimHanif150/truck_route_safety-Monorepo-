"""Hourly weather for checkpoints from Open-Meteo (free, no API key).

One request can cover many locations, so checkpoints are de-duplicated, grouped into
batches, and cached for a while to stay well inside the free limits.
"""
from dataclasses import dataclass
from datetime import timedelta

import requests
from django.core.cache import cache

from .errors import TripPlanningError

FORECAST_URL = 'https://api.open-meteo.com/v1/forecast'
# Sustained 10 m wind (not gusts), liquid precipitation (rain + showers) and snowfall depth.
HOURLY_FIELDS = 'wind_speed_10m,rain,showers,snowfall'
BATCH_SIZE = 50  # locations per request
TIMEOUT_SECONDS = 30
CACHE_SECONDS = 30 * 60


@dataclass(frozen=True)
class HourWeather:
    hour: int  # hours after the forecast start
    wind_mph: float
    rain_in_hr: float
    snow_in_hr: float


def weather_key(lat, lng):
    """Nearby checkpoints share one forecast: coordinates rounded to ~1 km."""
    return (round(lat, 2), round(lng, 2))


def _cache_key(key, start, hours):
    return f'wx:{key[0]}:{key[1]}:{start.strftime("%Y%m%d%H")}:{hours}'


def _series(location, start, hours):
    hourly = location.get('hourly') or {}
    index = {stamp: i for i, stamp in enumerate(hourly.get('time', []))}
    series = []
    for hour in range(hours + 1):
        stamp = (start + timedelta(hours=hour)).strftime('%Y-%m-%dT%H:%M')
        i = index.get(stamp)
        if i is None:
            raise TripPlanningError('Weather data does not cover the whole forecast window.', status=502)

        def value(field):
            values = hourly.get(field) or []
            return values[i] if i < len(values) and values[i] is not None else 0.0

        series.append(
            HourWeather(
                hour=hour,
                wind_mph=round(value('wind_speed_10m'), 1),
                rain_in_hr=round(value('rain') + value('showers'), 2),
                snow_in_hr=round(value('snowfall'), 2),
            )
        )
    return series


def _request_batch(keys, start, hours):
    params = {
        'latitude': ','.join(str(k[0]) for k in keys),
        'longitude': ','.join(str(k[1]) for k in keys),
        'hourly': HOURLY_FIELDS,
        'wind_speed_unit': 'mph',
        'precipitation_unit': 'inch',  # also makes snowfall inches per hour
        'timezone': 'UTC',
        'start_date': start.date().isoformat(),
        'end_date': (start + timedelta(hours=hours)).date().isoformat(),
    }
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        raise TripPlanningError('The weather service is unavailable. Please try again.', status=502)

    locations = [data] if isinstance(data, dict) else data  # one location returns an object
    if len(locations) != len(keys) or any('error' in loc for loc in locations):
        raise TripPlanningError('The weather service returned unexpected data.', status=502)
    return [_series(loc, start, hours) for loc in locations]


def fetch_forecasts(points, start, hours=48):
    """Return {weather_key: [HourWeather for hour 0..hours]} for the given (lat, lng) points.

    `start` is the top of the departure hour as a timezone-aware UTC datetime.
    """
    keys = sorted({weather_key(lat, lng) for lat, lng in points})
    result, missing = {}, []
    for key in keys:
        cached = cache.get(_cache_key(key, start, hours))
        if cached is None:
            missing.append(key)
        else:
            result[key] = cached

    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i : i + BATCH_SIZE]
        for key, series in zip(batch, _request_batch(batch, start, hours)):
            result[key] = series
            cache.set(_cache_key(key, start, hours), series, CACHE_SECONDS)
    return result
