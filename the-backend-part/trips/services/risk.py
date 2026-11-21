"""Weather risk rules from the assessment. Pure functions, no Django or network."""

LEVELS = ('low', 'moderate', 'high', 'severe', 'no_travel')
SCORES = {name: i for i, name in enumerate(LEVELS)}

# Lower bound of Moderate, High, Severe, No Travel for each condition.
# The assessment table overlaps at its edges (e.g. rain 0.25 is both Moderate's
# top and High's bottom). We treat every lower bound as inclusive. The one
# exception is the No Travel bound for rain and snow, which the table writes
# as ">1.00" and ">3.0", so those are strict.
WIND_BOUNDS = (25, 35, 45, 55)
RAIN_BOUNDS = (0.10, 0.25, 0.50, 1.00)
SNOW_BOUNDS = (0.5, 1.0, 2.0, 3.0)


def _level(value, bounds, strict_last=False):
    level = 0
    for i, bound in enumerate(bounds):
        is_last = i == len(bounds) - 1
        reached = value > bound if (is_last and strict_last) else value >= bound
        if reached:
            level = i + 1
    return level


def classify(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    """Return the risk level name for one checkpoint (worst of wind, rain, snow, load)."""
    level = max(
        _level(wind_mph, WIND_BOUNDS),
        _level(rain_in_hr, RAIN_BOUNDS, strict_last=True),
        _level(snow_in_hr, SNOW_BOUNDS, strict_last=True),
    )

    # Load rules can only raise the level, never lower it.
    if wind_mph >= 55:
        level = SCORES['no_travel']
    elif 45 <= wind_mph < 55 and load_lb > 30_000:
        level = SCORES['no_travel']
    elif 35 <= wind_mph < 45 and load_lb > 40_000:
        level = max(level, SCORES['severe'])

    return LEVELS[level]
