from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase

from trips.services.errors import TripPlanningError
from trips.services.geocoding import geocode
from trips.services.routing import _directions


def response(status=200, payload=None):
    r = Mock()
    r.status_code = status
    r.json.return_value = payload or {}
    r.raise_for_status.side_effect = None if status < 400 else requests.HTTPError()
    return r


class GeocodeTests(SimpleTestCase):
    def test_reads_lng_lat_order_from_geojson(self):
        payload = {'features': [{'geometry': {'coordinates': [-87.63, 41.878]},
                                 'properties': {'label': 'Chicago, IL, USA',
                                                'countrycode': 'US', 'name': 'Chicago', 'state': 'IL'}}]}
        with patch('trips.services.geocoding.requests.get', return_value=response(200, payload)):
            place = geocode('Chicago, IL')
        self.assertEqual((place.lat, place.lng), (41.878, -87.63))

    def test_unknown_place_is_a_user_error(self):
        with patch('trips.services.geocoding.requests.get', return_value=response(200, {'features': []})):
            with self.assertRaises(TripPlanningError) as ctx:
                geocode('Nowhereville')
        self.assertEqual(ctx.exception.status, 400)

    def test_empty_text_is_rejected_without_a_request(self):
        with patch('trips.services.geocoding.requests.get') as get:
            with self.assertRaises(TripPlanningError):
                geocode('   ')
        get.assert_not_called()

    def test_network_failure_becomes_502(self):
        with patch('trips.services.geocoding.requests.get', side_effect=requests.ConnectionError()):
            with self.assertRaises(TripPlanningError) as ctx:
                geocode('Chicago')
        self.assertEqual(ctx.exception.status, 502)


class DirectionsTests(SimpleTestCase):
    # OSRM answers in metres and seconds, with GeoJSON coordinates in [lng, lat] order.
    PAYLOAD = {'code': 'Ok', 'routes': [{
        'geometry': {'coordinates': [[-87.63, 41.878], [-104.99, 39.739]]},
        'distance': 160934.4,  # exactly 100 miles
        'duration': 54000,     # seconds -> 900 minutes
    }]}

    def test_parses_geometry_distance_and_duration(self):
        with patch('trips.services.routing.requests.get', return_value=response(200, self.PAYLOAD)) as get:
            route = _directions([(41.878, -87.63), (39.739, -104.99)])
        self.assertEqual(route.geometry[0], (41.878, -87.63))  # flipped to (lat, lng)
        self.assertAlmostEqual(route.distance_miles, 100.0, places=3)
        self.assertEqual(route.duration_minutes, 900)
        url = get.call_args.args[0]
        self.assertIn('-87.63,41.878;-104.99,39.739', url)  # the API wants lng,lat

    def test_error_statuses_map_to_clear_messages(self):
        for status, expected in ((429, 503), (403, 422), (404, 422), (500, 422)):
            with self.subTest(status=status):
                with patch('trips.services.routing.requests.get', return_value=response(status)):
                    with self.assertRaises(TripPlanningError) as ctx:
                        _directions([(1, 1), (2, 2)])
                self.assertEqual(ctx.exception.status, expected)

    def test_no_route_found_is_a_user_error(self):
        with patch('trips.services.routing.requests.get',
                   return_value=response(200, {'code': 'NoRoute', 'routes': []})):
            with self.assertRaises(TripPlanningError) as ctx:
                _directions([(1, 1), (2, 2)])
        self.assertEqual(ctx.exception.status, 422)

    def test_network_failure_becomes_502(self):
        with patch('trips.services.routing.requests.get', side_effect=requests.Timeout()):
            with self.assertRaises(TripPlanningError) as ctx:
                _directions([(1, 1), (2, 2)])
        self.assertEqual(ctx.exception.status, 502)