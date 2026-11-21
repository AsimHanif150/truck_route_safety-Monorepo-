from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import SimpleTestCase

from trips.services.errors import TripPlanningError
from trips.services.weather import BATCH_SIZE, fetch_forecasts, weather_key

START = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
HOURS = 48


def location(wind=10.0, rain=0.0, showers=0.0, snow=0.0, hours=HOURS):
    """Open-Meteo style payload for one location, covering whole days like the real API."""
    first = datetime(2026, 11, 20, 0, 0)
    times = [(first + timedelta(hours=h)).strftime('%Y-%m-%dT%H:%M') for h in range(24 * 4)]
    n = len(times)
    return {'hourly': {'time': times, 'wind_speed_10m': [wind] * n, 'rain': [rain] * n,
                       'showers': [showers] * n, 'snowfall': [snow] * n}}


def ok(payload):
    r = Mock()
    r.json.return_value = payload
    r.raise_for_status.return_value = None
    return r


class FetchForecastsTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_single_location_object_and_series_shape(self):
        with patch('trips.services.weather.requests.get', return_value=ok(location(wind=12.34))):
            result = fetch_forecasts([(41.878, -87.63)], START, HOURS)
        series = result[weather_key(41.878, -87.63)]
        self.assertEqual(len(series), HOURS + 1)
        self.assertEqual([s.hour for s in series][:3], [0, 1, 2])
        self.assertEqual(series[0].wind_mph, 12.3)

    def test_hour_zero_is_the_start_hour(self):
        payload = location()
        payload['hourly']['wind_speed_10m'][8] = 41.0  # 08:00 on the start day
        with patch('trips.services.weather.requests.get', return_value=ok(payload)):
            series = fetch_forecasts([(40, -90)], START, HOURS)[weather_key(40, -90)]
        self.assertEqual(series[0].wind_mph, 41.0)

    def test_rain_adds_showers_and_none_counts_as_zero(self):
        payload = location(rain=0.1, showers=0.05)
        payload['hourly']['snowfall'] = [None] * len(payload['hourly']['time'])
        with patch('trips.services.weather.requests.get', return_value=ok(payload)):
            series = fetch_forecasts([(40, -90)], START, HOURS)[weather_key(40, -90)]
        self.assertEqual(series[0].rain_in_hr, 0.15)
        self.assertEqual(series[0].snow_in_hr, 0.0)

    def test_requests_ask_for_us_units_and_utc(self):
        with patch('trips.services.weather.requests.get', return_value=ok(location())) as get:
            fetch_forecasts([(40, -90)], START, HOURS)
        params = get.call_args.kwargs['params']
        self.assertEqual(params['wind_speed_unit'], 'mph')
        self.assertEqual(params['precipitation_unit'], 'inch')
        self.assertEqual(params['timezone'], 'UTC')
        self.assertEqual((params['start_date'], params['end_date']), ('2026-11-20', '2026-11-22'))

    def test_nearby_points_share_one_request_slot(self):
        with patch('trips.services.weather.requests.get', return_value=ok(location())) as get:
            result = fetch_forecasts([(40.001, -90.001), (40.002, -90.002)], START, HOURS)
        self.assertEqual(len(result), 1)
        self.assertEqual(get.call_args.kwargs['params']['latitude'], '40.0')

    def test_many_points_are_split_into_batches(self):
        points = [(30 + i * 0.1, -90.0) for i in range(BATCH_SIZE + 5)]

        def fake_get(url, params, timeout):
            count = len(params['latitude'].split(','))
            return ok([location() for _ in range(count)])

        with patch('trips.services.weather.requests.get', side_effect=fake_get) as get:
            result = fetch_forecasts(points, START, HOURS)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(len(result), BATCH_SIZE + 5)

    def test_second_call_uses_the_cache(self):
        with patch('trips.services.weather.requests.get', return_value=ok(location())) as get:
            fetch_forecasts([(40, -90)], START, HOURS)
            fetch_forecasts([(40, -90)], START, HOURS)
        self.assertEqual(get.call_count, 1)

    def test_missing_hours_are_an_error_not_silent_zeros(self):
        short = location()
        for field in short['hourly']:
            short['hourly'][field] = short['hourly'][field][:20]  # ends before the window does
        with patch('trips.services.weather.requests.get', return_value=ok(short)):
            with self.assertRaises(TripPlanningError) as ctx:
                fetch_forecasts([(40, -90)], START, HOURS)
        self.assertEqual(ctx.exception.status, 502)

    def test_network_failure_becomes_502(self):
        with patch('trips.services.weather.requests.get', side_effect=requests.Timeout()):
            with self.assertRaises(TripPlanningError) as ctx:
                fetch_forecasts([(40, -90)], START, HOURS)
        self.assertEqual(ctx.exception.status, 502)

    def test_api_error_payload_becomes_502(self):
        with patch('trips.services.weather.requests.get', return_value=ok({'error': True, 'reason': 'x'})):
            with self.assertRaises(TripPlanningError):
                fetch_forecasts([(40, -90)], START, HOURS)
