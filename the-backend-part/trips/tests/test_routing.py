from unittest.mock import patch

from django.test import SimpleTestCase

from trips.services.errors import TripPlanningError
from trips.services.geo import haversine_miles
from trips.services.routing import (
    RouteOption,
    get_route_options,
    offset_waypoint,
    overlap_fraction,
)

CHICAGO = (41.878, -87.63)
DENVER = (39.739, -104.99)


def line(a, b, n=40):
    return tuple((a[0] + (b[0] - a[0]) * i / (n - 1), a[1] + (b[1] - a[1]) * i / (n - 1)) for i in range(n))


def route_via(via, duration=900.0):
    """Fake route that really passes through `via`, like a real routing API would."""
    geometry = line(CHICAGO, via, 30) + line(via, DENVER, 30)[1:]
    return RouteOption(geometry=geometry, distance_miles=1000.0, duration_minutes=duration)


class OffsetWaypointTests(SimpleTestCase):
    def test_sides_are_opposite_and_equally_far(self):
        left = offset_waypoint(CHICAGO, DENVER, 0.2, 1)
        right = offset_waypoint(CHICAGO, DENVER, 0.2, -1)
        mid = ((CHICAGO[0] + DENVER[0]) / 2, (CHICAGO[1] + DENVER[1]) / 2)
        self.assertAlmostEqual(haversine_miles(mid, left), haversine_miles(mid, right), delta=1)
        # One waypoint sits north of the straight line and the other south of it.
        self.assertLess((left[0] - mid[0]) * (right[0] - mid[0]), 0)

    def test_distance_scales_with_trip_length(self):
        straight = haversine_miles(CHICAGO, DENVER)
        mid = ((CHICAGO[0] + DENVER[0]) / 2, (CHICAGO[1] + DENVER[1]) / 2)
        pushed = haversine_miles(mid, offset_waypoint(CHICAGO, DENVER, 0.2, 1))
        self.assertAlmostEqual(pushed, 0.2 * straight, delta=0.03 * straight)

    def test_same_place_is_rejected(self):
        with self.assertRaises(TripPlanningError):
            offset_waypoint(CHICAGO, CHICAGO, 0.2, 1)


class OverlapTests(SimpleTestCase):
    def test_identical_routes_fully_overlap(self):
        r = route_via((40.8, -96.0))
        self.assertEqual(overlap_fraction(r, r), 1.0)

    def test_routes_far_apart_do_not_overlap_in_the_middle(self):
        north = route_via((44.0, -96.0))
        south = route_via((37.0, -96.0))
        self.assertLess(overlap_fraction(north, south), 0.5)


class GetRouteOptionsTests(SimpleTestCase):
    def fake_directions(self, durations=None):
        durations = durations or {}

        def fake(points):
            if len(points) == 2:
                return route_via(((CHICAGO[0] + DENVER[0]) / 2, (CHICAGO[1] + DENVER[1]) / 2), 900)
            via = points[1]
            return route_via(via, durations.get('north' if via[0] > 40.8 else 'south', 1000))

        return fake

    def test_returns_three_distinct_routes_fastest_first(self):
        with patch('trips.services.routing._directions', side_effect=self.fake_directions()):
            routes = get_route_options(CHICAGO, DENVER)
        self.assertEqual(len(routes), 3)
        durations = [r.duration_minutes for r in routes]
        self.assertEqual(durations, sorted(durations))

    def test_drops_detours_that_are_far_too_slow(self):
        fake = self.fake_directions({'north': 5000, 'south': 5000})
        with patch('trips.services.routing._directions', side_effect=fake):
            routes = get_route_options(CHICAGO, DENVER)
        self.assertEqual(len(routes), 1)

    def test_drops_a_duplicate_of_the_direct_route(self):
        direct = route_via(((CHICAGO[0] + DENVER[0]) / 2, (CHICAGO[1] + DENVER[1]) / 2))
        with patch('trips.services.routing._directions', return_value=direct):
            routes = get_route_options(CHICAGO, DENVER)
        self.assertEqual(len(routes), 1)

    def test_a_failing_detour_is_skipped_not_fatal(self):
        base = self.fake_directions()

        def flaky(points):
            if len(points) == 3 and points[1][0] > 40.8:
                raise TripPlanningError('no route', status=422)
            return base(points)

        with patch('trips.services.routing._directions', side_effect=flaky):
            routes = get_route_options(CHICAGO, DENVER)
        self.assertGreaterEqual(len(routes), 2)

    def test_failure_of_the_direct_route_is_fatal(self):
        with patch('trips.services.routing._directions', side_effect=TripPlanningError('x', 422)):
            with self.assertRaises(TripPlanningError):
                get_route_options(CHICAGO, DENVER)