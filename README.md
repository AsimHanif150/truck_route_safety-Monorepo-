# HaulSafe — Weather-Aware Truck Routing

A React + Django web app that helps a truck driver choose the safest route based on
**weather, load weight and travel time**.

- **Live app:** _add your hosted URL here_
- **Loom walkthrough:** _add your Loom link here_

## What it does

1. The user enters an origin, a destination, a departure date/time and the load weight.
2. The backend gets up to **three route options** and samples **checkpoints every 10, 25 or 50 miles**.
3. For every checkpoint it estimates the truck's **arrival time (ETA)** and reads the weather forecast
   for that hour.
4. Each checkpoint is scored with the risk and load rules below. Each route gets a summary:
   Severe miles, High miles, No Travel miles and average risk.
5. The backend **recommends the safest route**. If every route has a No Travel stretch, it recommends
   nothing and says so.
6. The UI shows all routes, checkpoints, ETAs and risk levels on a map, plus a **weather heatmap** with
   a **0–48 hour forecast slider**.

## Tech stack

| Part | Choice |
|---|---|
| Frontend | React + Vite, React Leaflet, Axios |
| Backend | Python, Django, Django REST Framework |
| Routing | OSRM public server (no API key) |
| Geocoding | Photon (OpenStreetMap data, no API key) |
| Weather | Open-Meteo forecast API (no API key) |

No API keys are needed to run the project.

## Project structure

```
the-backend-part/    Django API (trips app: serializers, views, services, tests)
the-frontend-part/   React dashboard (components, hooks, services)
```

Backend services are kept separate on purpose: `geocoding.py`, `routing.py` and `weather.py` talk to
outside APIs, while `risk.py`, `recommend.py` and `checkpoints.py` are plain Python with no network
calls, so they are easy to unit-test. `planner.py` ties them together and the view stays thin.

## Run it locally

### Backend

```bash
cd the-backend-part
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env
python manage.py runserver       # http://localhost:8000
```

### Frontend

```bash
cd the-frontend-part
npm install
copy .env.example .env           # macOS/Linux: cp .env.example .env
npm run dev                      # http://localhost:5173
```

Open the app at `http://localhost:5173` (the backend only allows that origin).

### Environment variables

| File | Variable | Purpose |
|---|---|---|
| backend `.env` | `SECRET_KEY` | Django secret key |
| backend `.env` | `DEBUG` | `true` for local development |
| backend `.env` | `ALLOWED_HOSTS` | Comma-separated hosts |
| backend `.env` | `CORS_ORIGINS` | Frontend origin(s) allowed to call the API |
| frontend `.env` | `VITE_API_BASE_URL` | Backend address, e.g. `http://localhost:8000` |
| frontend `.env` | `VITE_USE_MOCK` | `true` shows demo data without a backend |

## Run the tests

```bash
cd the-backend-part
python manage.py test trips
```

The tests use fake responses for the outside APIs, so they run offline. They cover every risk
threshold and boundary, all three load overrides, checkpoint sampling and ETAs, the route ranking,
the "no safe route" case, input validation and the full API response shape.

## Risk rules

At each checkpoint the **highest** applicable risk is used.

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind | < 25 mph | 25–34 | 35–44 | 45–54 | ≥ 55 |
| Rain | < 0.10 in/hr | 0.10–0.25 | 0.25–0.50 | 0.50–1.00 | > 1.00 |
| Snow | < 0.5 in/hr | 0.5–1.0 | 1.0–2.0 | 2.0–3.0 | > 3.0 |

**Load overrides**

- Wind ≥ 55 mph: No Travel for every load.
- Wind 45–54 mph and load > 30,000 lb: No Travel.
- Wind 35–44 mph and load > 40,000 lb: Severe.

### Route ranking

1. Fewest No Travel miles (a safety disqualifier)
2. Fewest Severe miles
3. Fewest High miles
4. Lowest average risk
5. Shortest travel time

If even the best route has No Travel miles, the API returns `recommended_route_id: null` and a warning,
and the UI says no safe route is available.

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

- `checkpoint_interval` is 10, 25 or 50 miles.
- `departure` must be within the next 14 days.
- Errors look like `{"error": "message"}` with status 400 (bad input), 422 (no route found),
  502 (an outside service is down) or 503 (an outside service is busy).

The response contains `origin`, `destination`, `forecast_start`, `forecast_hours`,
`recommended_route_id`, `warnings` and `routes`. Each route has its geometry, summary and
checkpoints, and each checkpoint carries the weather for all 49 forecast hours so the slider needs
no extra requests.

## Design decisions

- **Weather at arrival time:** each checkpoint uses the forecast for the hour the truck reaches it, not the
  departure hour.
- **Rates, not totals:** the weather API is asked for inches, and hourly precipitation is used as an
  hourly rate, matching the in/hr thresholds.
- **Risk is calculated on the backend only.** React just displays the result.
- **Fewer API calls:** nearby checkpoints share one forecast, requests are batched, and forecasts are
  cached for 30 minutes.
- **Timeouts and clear errors** on every outside call.

## Known limitations

- Routing uses OSRM's **standard driving profile**. Routes are **not guaranteed to be truck-legal**
  (height, weight and hazmat restrictions are not considered). The app shows a note about this.
- The forecast covers 48 hours. Checkpoints reached later than that reuse the last forecast hour, so
  their weather is only an approximation on very long trips.
- OSRM and Photon are free public servers with usage limits.
