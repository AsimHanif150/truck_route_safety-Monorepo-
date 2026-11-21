from django.test import SimpleTestCase

from trips.services.risk import classify


class WindTests(SimpleTestCase):
    def test_bands_with_light_load(self):
        cases = {10: 'low', 24.9: 'low', 25: 'moderate', 34.9: 'moderate',
                 35: 'high', 44.9: 'high', 45: 'severe', 54.9: 'severe', 55: 'no_travel'}
        for wind, expected in cases.items():
            with self.subTest(wind=wind):
                self.assertEqual(classify(wind, 0, 0, 10_000), expected)


class RainSnowTests(SimpleTestCase):
    def test_rain_bands(self):
        cases = {0.09: 'low', 0.10: 'moderate', 0.25: 'high', 0.50: 'severe',
                 1.00: 'severe', 1.01: 'no_travel'}
        for rain, expected in cases.items():
            with self.subTest(rain=rain):
                self.assertEqual(classify(0, rain, 0, 10_000), expected)

    def test_snow_bands(self):
        cases = {0.4: 'low', 0.5: 'moderate', 1.0: 'high', 2.0: 'severe',
                 3.0: 'severe', 3.1: 'no_travel'}
        for snow, expected in cases.items():
            with self.subTest(snow=snow):
                self.assertEqual(classify(0, 0, snow, 10_000), expected)


class LoadRuleTests(SimpleTestCase):
    def test_no_travel_at_55_for_any_load(self):
        self.assertEqual(classify(55, 0, 0, 1), 'no_travel')

    def test_45_to_54_heavy_load_is_no_travel(self):
        self.assertEqual(classify(45, 0, 0, 30_001), 'no_travel')
        self.assertEqual(classify(54, 0, 0, 30_001), 'no_travel')

    def test_45_to_54_at_exactly_30000_is_severe(self):
        self.assertEqual(classify(50, 0, 0, 30_000), 'severe')

    def test_35_to_44_over_40000_is_severe(self):
        self.assertEqual(classify(40, 0, 0, 40_001), 'severe')

    def test_35_to_44_at_exactly_40000_stays_high(self):
        self.assertEqual(classify(40, 0, 0, 40_000), 'high')

    def test_load_never_lowers_the_level(self):
        # Heavy snow is Severe on its own; the wind load rule must not downgrade it.
        self.assertEqual(classify(36, 0, 2.5, 45_000), 'severe')


class CombinationTests(SimpleTestCase):
    def test_worst_condition_wins(self):
        self.assertEqual(classify(10, 0.3, 0.6, 10_000), 'high')
