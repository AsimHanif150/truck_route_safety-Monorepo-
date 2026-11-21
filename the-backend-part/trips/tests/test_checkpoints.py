from datetime import datetime, timezone

from django.test import SimpleTestCase

from trips.services.checkpoints import build_checkpoints
from trips.services.geo import haversine_miles
from trips.services.routing import RouteOption

DEPARTURE = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)


def straight_route(distance_miles=100.0, duration_minutes=100.0, points=11):
    """A route straight north along one meridian, so distances are easy to check."""
    degrees = distance_miles / 69.09  # about 69.09 miles per degree of latitude
    geometry = tuple((40 + degrees * i / (points - 1), -90.0) for i in range(points))
    return RouteOption(geometry=geometry, distance_miles=distance_miles, duration_minutes=duration_minutes)


class CheckpointSpacingTests(SimpleTestCase):
    def test_miles_at_requested_interval(self):
        cps = build_checkpoints(straight_route(100), DEPARTURE, 25)
        self.assertEqual([c.mile for c in cps], [0, 25, 50, 75, 100])

    def test_destination_is_last_checkpoint_even_when_not_a_multiple(self):
        cps = build_checkpoints(straight_route(95), DEPARTURE, 25)
        self.assertEqual([c.mile for c in cps], [0, 25, 50, 75, 95])

    def test_no_duplicate_when_distance_is_exact_multiple(self):
        cps = build_checkpoints(straight_route(50), DEPARTURE, 10)
        self.assertEqual(len(cps), 6)

    def test_rejects_unsupported_interval(self):
        with self.assertRaises(ValueError):
            build_checkpoints(straight_route(), DEPARTURE, 15)

    def test_points_lie_where_the_miles_say(self):
        route = straight_route(100)
        cps = build_checkpoints(route, DEPARTURE, 25)
        start = route.geometry[0]
        for c in cps:
            self.assertAlmostEqual(haversine_miles(start, (c.lat, c.lng)), c.mile, delta=0.5)

    def test_first_and_last_points_match_the_route_ends(self):
        route = straight_route(100)
        cps = build_checkpoints(route, DEPARTURE, 50)
        self.assertAlmostEqual(cps[0].lat, route.geometry[0][0], places=4)
        self.assertAlmostEqual(cps[-1].lat, route.geometry[-1][0], places=4)


class EtaTests(SimpleTestCase):
    def test_eta_grows_with_distance_at_constant_speed(self):
        cps = build_checkpoints(straight_route(100, duration_minutes=120), DEPARTURE, 25)
        minutes = [(c.eta - DEPARTURE).total_seconds() / 60 for c in cps]
        self.assertEqual(minutes, [0, 30, 60, 90, 120])

    def test_first_eta_is_departure(self):
        cps = build_checkpoints(straight_route(), DEPARTURE, 10)
        self.assertEqual(cps[0].eta, DEPARTURE)


class SegmentMilesTests(SimpleTestCase):
    def test_segments_add_up_to_the_route_distance(self):
        for distance in (95, 100, 333):
            for interval in (10, 25, 50):
                with self.subTest(distance=distance, interval=interval):
                    cps = build_checkpoints(straight_route(distance), DEPARTURE, interval)
                    self.assertAlmostEqual(sum(c.segment_miles for c in cps), distance, places=6)

    def test_provider_distance_is_the_reference(self):
        # Geometry is about 100 miles long but the API says 120: miles follow the API.
        route = straight_route(100)
        route = RouteOption(route.geometry, distance_miles=120.0, duration_minutes=100.0)
        cps = build_checkpoints(route, DEPARTURE, 50)
        self.assertEqual(cps[-1].mile, 120)
