# HaulSafe backend (Django + DRF)

Plans three truck routes between two US places, samples weather along each route at the
truck's estimated arrival time, scores the risk with the assessment rules, and recommends
the safest route.

## Run

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # then put your OpenRouteService key in ORS_API_KEY
python manage.py test
python manage.py runserver     # http://localhost:8000
```

Free OpenRouteService key: https://openrouteservice.org/dev/#/signup. Open-Meteo needs no key.

## API

`POST /api/trips/plan/`

```json
{
  "origin": "Chicago, IL",
  "destination": "Denver, CO",
  "departure": "2026-11-21T08:00:00Z",
  "load_weight": 36000,
  "checkpoint_interval": 25
}
```

`checkpoint_interval` is 10, 25 or 50 miles. Departure must be within the next 14 days.
Errors are `{"error": "message"}` with status 400 (bad input), 422 (no truck route),
502 (a provider is down) or 503 (API key missing, rejected or out of quota).

The response shape is documented at the top of the frontend's `src/services/mockTrip.js`.

## How it works

| Step | File | Notes |
| --- | --- | --- |
| Geocode | `services/geocoding.py` | OpenRouteService geocoder, US only |
| Routes | `services/routing.py` | Fastest HGV route + two detours through waypoints pushed north/south of the midpoint; near-duplicates and detours over 60% slower are dropped |
| Checkpoints | `services/checkpoints.py` | Mile 0, every N miles, destination; ETA assumes constant average speed |
| Weather | `services/weather.py` | Open-Meteo hourly, 49 values per checkpoint, batched and cached 30 min |
| Risk | `services/risk.py` | Assessment table and load rules |
| Ranking | `services/recommend.py` | See below |
| Glue | `services/planner.py`, `views.py` | |

## Decisions worth knowing

- **Why waypoint detours instead of the provider's alternative routes:** those are limited
  to fairly short routes; these trips are hundreds of miles.
- **Table edges:** the risk table overlaps (e.g. rain 0.25). Lower bounds are inclusive, so
  0.25 in/hr is High. Only the No Travel bounds for rain (>1.00) and snow (>3.0) are strict.
  Load rules can only raise a level.
- **Weather used:** sustained 10 m wind (not gusts), rain + showers for rain, snowfall depth
  per hour for snow. Each checkpoint is scored with the forecast hour nearest to the truck's ETA.
- **Risk miles:** each checkpoint stands for the stretch of road halfway to its neighbours, so
  the miles per level add up exactly to the route distance. `avg_risk` is weighted by those miles.
- **Ranking:** No Travel miles, then Severe miles, then High miles, then average risk, then
  duration. No Travel comes first so a route with an impassable stretch can never beat one that
  is only Severe. If every route has No Travel miles, the response includes a warning.
- **Not modelled:** rest stops, traffic, temperature/ice, road closures.

## Tests

`python manage.py test` runs 76 tests. HTTP calls to the outside services are mocked.
