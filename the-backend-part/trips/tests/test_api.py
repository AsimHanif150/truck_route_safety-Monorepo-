from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.core.cache import cache
from rest_framework.test import APISimpleTestCase

from trips.services.errors import TripPlanningError
from trips.services.geocoding import Place
from trips.services.routing import RouteOption
from trips.services.weather import HourWeather

URL = '/api/trips/plan/'
ROUTE_KEYS = {'id', 'name', 'distance_miles', 'duration_minutes', 'geometry', 'summary', 'checkpoints'}
CHECKPOINT_KEYS = {'id', 'lat', 'lng', 'mile', 'eta', 'risk_level', 'wind_mph', 'rain_in_hr',
                   'snow_in_hr', 'forecast'}
SUMMARY_KEYS = {'low_miles', 'moderate_miles', 'high_miles', 'severe_miles', 'no_travel_miles', 'avg_risk'}


def good_request(**overrides):
    body = {
        'origin': 'Chicago, IL',
        'destination': 'Denver, CO',
        'departure': (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        'load_weight': 36000,
        'checkpoint_interval': 25,
    }
    body.update(overrides)
    return body


def fake_route(offset, minutes):
    geometry = tuple((41.9 - i * 0.025 + offset, -87.6 - i * 0.17) for i in range(100))
    return RouteOption(geometry=geometry, distance_miles=1000.0 + offset * 100, duration_minutes=minutes)


class PlanEndpointValidationTests(APISimpleTestCase):
    def post(self, **overrides):
        return self.client.post(URL, good_request(**overrides), format='json')

    def test_missing_field(self):
        body = good_request()
        del body['load_weight']
        response = self.client.post(URL, body, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Load weight', response.json()['error'])

    def test_bad_interval(self):
        self.assertEqual(self.post(checkpoint_interval=15).status_code, 400)

    def test_negative_weight(self):
        self.assertEqual(self.post(load_weight=-5).status_code, 400)

    def test_past_departure(self):
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        response = self.post(departure=past)
        self.assertEqual(response.status_code, 400)
        self.assertIn('past', response.json()['error'])

    def test_far_future_departure(self):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        self.assertEqual(self.post(departure=future).status_code, 400)

    def test_planning_errors_use_their_own_status_and_message(self):
        with patch('trips.views.build_plan', side_effect=TripPlanningError('No such place', 400)):
            response = self.post()
        self.assertEqual((response.status_code, response.json()), (400, {'error': 'No such place'}))

    def test_upstream_failure_is_502(self):
        with patch('trips.views.build_plan', side_effect=TripPlanningError('down', 502)):
            self.assertEqual(self.post().status_code, 502)


class PlanEndpointEndToEndTests(APISimpleTestCase):
    """Whole pipeline with only the three outside services replaced by fakes."""

    def setUp(self):
        cache.clear()

    def run_plan(self, wind=lambda lat, lng, hour: 10.0, **overrides):
        def fake_forecasts(points, start, hours):
            return {(round(lat, 2), round(lng, 2)): [HourWeather(h, wind(lat, lng, h), 0.0, 0.0) for h in range(hours + 1)]
                    for lat, lng in points}

        places = iter([Place('Chicago, IL, USA', 41.878, -87.63), Place('Denver, CO, USA', 39.739, -104.99)])
        routes = [fake_route(0, 900), fake_route(1.5, 950), fake_route(-1.5, 1000)]
        with patch('trips.services.planner.geocode', side_effect=lambda text: next(places)), \
             patch('trips.services.planner.get_route_options', return_value=routes), \
             patch('trips.services.planner.fetch_forecasts', side_effect=fake_forecasts):
            return self.client.post(URL, good_request(**overrides), format='json')

    def test_response_matches_the_shape_the_frontend_expects(self):
        data = self.run_plan().json()
        self.assertEqual({'origin', 'destination', 'forecast_start', 'forecast_hours', 'recommended_route_id',
                          'warnings', 'routes'}, set(data))
        self.assertEqual(data['forecast_hours'], 48)
        self.assertEqual(len(data['routes']), 3)
        for route in data['routes']:
            self.assertEqual(set(route), ROUTE_KEYS)
            self.assertEqual(set(route['summary']), SUMMARY_KEYS)
            self.assertGreater(len(route['geometry']), 2)
            self.assertEqual(len(route['geometry'][0]), 2)
            for cp in route['checkpoints']:
                self.assertEqual(set(cp), CHECKPOINT_KEYS)
                self.assertEqual(len(cp['forecast']), 49)
        self.assertIn(data['recommended_route_id'], {r['id'] for r in data['routes']})

    def test_summary_miles_add_up_to_the_distance(self):
        for route in self.run_plan().json()['routes']:
            total = sum(route['summary'][k] for k in SUMMARY_KEYS - {'avg_risk'})
            self.assertAlmostEqual(total, route['distance_miles'], delta=1.0)

    def test_checkpoint_interval_is_respected(self):
        for interval in (10, 50):
            route = self.run_plan(checkpoint_interval=interval).json()['routes'][0]
            miles = [cp['mile'] for cp in route['checkpoints']]
            self.assertEqual(miles[1] - miles[0], interval)

    def test_calm_weather_recommends_the_fastest_route(self):
        self.assertEqual(self.run_plan().json()['recommended_route_id'], 'r1')

    def test_storm_on_the_fastest_route_moves_the_recommendation(self):
        # Heavy wind only near the first route's latitude band.
        def storm(lat, lng, hour):
            return 40.0 if lat > 40.5 and lng < -93 and lat < 40.99 else 10.0

        calm = self.run_plan().json()['recommended_route_id']
        stormy = self.run_plan(wind=storm, load_weight=50_000).json()
        self.assertEqual(calm, 'r1')
        self.assertTrue(any(r['summary']['severe_miles'] > 0 for r in stormy['routes']))

    def test_no_travel_everywhere_adds_a_warning(self):
        data = self.run_plan(wind=lambda lat, lng, h: 60.0).json()
        self.assertTrue(data['warnings'])
        self.assertTrue(all(r['summary']['no_travel_miles'] > 0 for r in data['routes']))
        # No Travel is a disqualifier, so no route may be recommended.
        self.assertIsNone(data['recommended_route_id'])

    def test_forecast_start_is_the_top_of_the_departure_hour(self):
        departure = datetime(2026, 11, 20, 8, 37, tzinfo=timezone.utc)
        with patch('trips.serializers.timezone.now', return_value=departure - timedelta(hours=1)):
            data = self.run_plan(departure=departure.isoformat()).json()
        self.assertEqual(data['forecast_start'], '2026-11-20T08:00:00Z')


class CorsTests(APISimpleTestCase):
    def preflight(self, origin):
        return self.client.options(URL, HTTP_ORIGIN=origin, HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST')

    def test_frontend_origin_is_allowed(self):
        response = self.preflight('http://localhost:5173')
        self.assertEqual(response.headers.get('access-control-allow-origin'), 'http://localhost:5173')

    def test_other_origins_are_not(self):
        self.assertNotIn('access-control-allow-origin', self.preflight('http://evil.example').headers)