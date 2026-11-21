from datetime import datetime, timedelta, timezone

from django.test import SimpleTestCase

from trips.services.checkpoints import Checkpoint
from trips.services.recommend import assess_route, forecast_hour_for_eta, pick_recommended, rank_key
from trips.services.routing import RouteOption
from trips.services.weather import HourWeather, weather_key

START = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
HOURS = 48


def series(wind):
    """wind: function hour -> mph (rain and snow zero)."""
    return [HourWeather(h, wind(h), 0.0, 0.0) for h in range(HOURS + 1)]


def checkpoint(mile, hours_after_start, segment=25.0):
    return Checkpoint(lat=40.0 + mile / 100, lng=-90.0, mile=mile,
                      eta=START + timedelta(hours=hours_after_start), segment_miles=segment)


def route(distance=100.0, minutes=120.0):
    return RouteOption(geometry=((40, -90), (41, -90)), distance_miles=distance, duration_minutes=minutes)


class EtaHourTests(SimpleTestCase):
    def test_rounds_to_nearest_hour(self):
        self.assertEqual(forecast_hour_for_eta(START + timedelta(minutes=89), START, HOURS), 1)
        self.assertEqual(forecast_hour_for_eta(START + timedelta(minutes=91), START, HOURS), 2)

    def test_clamped_to_the_forecast_window(self):
        self.assertEqual(forecast_hour_for_eta(START + timedelta(hours=60), START, HOURS), 48)
        self.assertEqual(forecast_hour_for_eta(START - timedelta(hours=2), START, HOURS), 0)


class AssessRouteTests(SimpleTestCase):
    def test_risk_uses_weather_at_the_eta_hour_not_departure(self):
        # Calm at hour 0, a 50 mph storm at hour 5: a checkpoint reached at hour 5 is hit.
        cps = [checkpoint(0, 0, 50), checkpoint(100, 5, 50)]
        forecasts = {weather_key(c.lat, c.lng): series(lambda h: 50.0 if h == 5 else 5.0) for c in cps}
        result = assess_route('r1', 'Route 1', route(), cps, forecasts, START, 20_000, HOURS)
        self.assertEqual([c['risk_level'] for c in result['checkpoints']], ['low', 'severe'])

    def test_load_rules_change_the_result(self):
        cps = [checkpoint(0, 0, 100)]
        forecasts = {weather_key(c.lat, c.lng): series(lambda h: 50.0) for c in cps}
        light = assess_route('r1', 'R', route(), cps, forecasts, START, 20_000, HOURS)
        heavy = assess_route('r1', 'R', route(), cps, forecasts, START, 35_000, HOURS)
        self.assertEqual(light['checkpoints'][0]['risk_level'], 'severe')
        self.assertEqual(heavy['checkpoints'][0]['risk_level'], 'no_travel')

    def test_summary_miles_and_weighted_average(self):
        cps = [checkpoint(0, 0, 60), checkpoint(100, 1, 40)]
        wind = {cps[0]: 5.0, cps[1]: 50.0}  # low, severe (3)
        forecasts = {weather_key(c.lat, c.lng): series(lambda h, c=c: wind[c]) for c in cps}
        s = assess_route('r1', 'R', route(100), cps, forecasts, START, 10_000, HOURS)['summary']
        self.assertEqual((s['low_miles'], s['severe_miles']), (60.0, 40.0))
        self.assertEqual(s['avg_risk'], 1.2)  # (0 * 60 + 3 * 40) / 100

    def test_each_checkpoint_carries_49_hourly_entries(self):
        cps = [checkpoint(0, 0, 100)]
        forecasts = {weather_key(c.lat, c.lng): series(lambda h: 5.0) for c in cps}
        cp = assess_route('r1', 'R', route(), cps, forecasts, START, 10_000, HOURS)['checkpoints'][0]
        self.assertEqual(len(cp['forecast']), 49)
        self.assertEqual(cp['eta'], '2026-11-20T08:00:00Z')


def fake(id_, no_travel=0, severe=0, high=0, avg=0.0, minutes=600):
    return {'id': id_, 'duration_minutes': minutes,
            'summary': {'no_travel_miles': no_travel, 'severe_miles': severe, 'high_miles': high, 'avg_risk': avg}}


class RankingTests(SimpleTestCase):
    def best(self, *routes):
        return pick_recommended(list(routes))['id']

    def test_fewest_severe_miles_wins_over_speed(self):
        self.assertEqual(self.best(fake('fast', severe=50, minutes=500), fake('safe', severe=10, minutes=900)), 'safe')

    def test_high_miles_break_a_severe_tie(self):
        self.assertEqual(self.best(fake('a', high=80), fake('b', high=20)), 'b')

    def test_average_risk_breaks_a_high_tie(self):
        self.assertEqual(self.best(fake('a', avg=1.2), fake('b', avg=0.8)), 'b')

    def test_travel_time_is_the_last_tiebreaker(self):
        self.assertEqual(self.best(fake('slow', minutes=900), fake('quick', minutes=700)), 'quick')

    def test_no_travel_stretch_never_beats_severe_only(self):
        blocked = fake('blocked', no_travel=20, severe=0)
        severe_only = fake('severe', no_travel=0, severe=100)
        self.assertEqual(self.best(blocked, severe_only), 'severe')

    def test_rank_key_order(self):
        self.assertEqual(rank_key(fake('x', 1, 2, 3, 0.5, 600)), (1, 2, 3, 0.5, 600))
