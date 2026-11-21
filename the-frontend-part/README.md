# HaulSafe — Weather-aware truck routing frontend

React 19 + Vite frontend for the Spotter Full Stack Developer assessment. The frontend includes a trip form, three-route comparison, interactive Leaflet map, route checkpoints, weather heatmap layer, 0–48 hour forecast control, and checkpoint weather details.

## Run locally

```bash
npm install
npm run dev
```

The app opens at the Vite URL shown in your terminal (normally `http://localhost:5173`).

## Backend connection

By default, the frontend calls Django at `http://localhost:8000`.

Create `.env` in the project root if your backend uses another host:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Expected endpoint:

`POST /api/trips/plan/`

Request JSON:

```json
{
  "origin": "Chicago, IL",
  "destination": "Denver, CO",
  "departure": "2026-11-20T13:00:00.000Z",
  "load_weight": 36000,
  "checkpoint_interval": 25
}
```

Expected response shape:

```json
{
  "origin": {"name": "Chicago, IL", "lat": 41.878, "lng": -87.63},
  "destination": {"name": "Denver, CO", "lat": 39.739, "lng": -104.99},
  "recommended_route_id": "route-2",
  "routes": [
    {
      "id": "route-2",
      "name": "Balanced route",
      "distance_miles": 1050,
      "duration_minutes": 950,
      "geometry": [[41.878, -87.63], [40.8, -92.0], [39.739, -104.99]],
      "summary": {
        "low_miles": 800,
        "moderate_miles": 180,
        "high_miles": 70,
        "severe_miles": 0,
        "no_travel_miles": 0,
        "avg_risk": 0.9
      },
      "checkpoints": [
        {
          "id": "cp-1",
          "lat": 40.8,
          "lng": -92.0,
          "mile": 280,
          "eta": "2026-11-20T13:00:00Z",
          "risk_level": "low",
          "wind_mph": 10,
          "rain_in_hr": 0,
          "snow_in_hr": 0,
          "forecast": [
            {"hour": 0, "wind_mph": 10, "rain_in_hr": 0, "snow_in_hr": 0, "risk_level": "low"},
            {"hour": 1, "wind_mph": 12, "rain_in_hr": 0.05, "snow_in_hr": 0, "risk_level": "low"}
          ]
        }
      ]
    }
  ]
}
```

- `geometry` uses `[latitude, longitude]` pairs.
- `risk_level` must be one of `low`, `moderate`, `high`, `severe`, `no_travel`.
- `summary` mileage values should be calculated by the backend.
- `recommended_route_id` should be chosen by the assessment priority: fewest severe miles, fewest high miles, lowest average risk, then shortest travel time.

The frontend does not silently replace API failures with sample data. To preview the bundled sample trip, set `VITE_USE_MOCK=true` in `.env`; otherwise backend/network errors are displayed in the dashboard. The demo trip is illustrative, not live weather or routing data.

## Frontend scope

This repository contains frontend code only. Route generation, geocoding, weather retrieval, checkpoint ETA calculations, risk/load-rule calculations, and route recommendation must be implemented by the Django backend. The frontend reads each checkpoint's `forecast` array by hour (0 through 48). Return 49 hourly entries per checkpoint for a complete slider experience. The selected hour updates the weather corridor heat layer and the selected checkpoint details without another API request. The map samples route geometry between vertices and uses the nearest checkpoint's hourly risk to color the corridor. Checkpoint markers for all three routes remain visible; inactive routes are dimmed.

## Design decisions

- Keep trip planning, route comparison, map analysis, and checkpoint details in one responsive dashboard to reduce navigation during trip review.
- Use a 0–48 hour client-side forecast slider so changing forecast time does not trigger repeated backend requests.
- Render dense heat samples along every route, not only checkpoint dots, to communicate weather exposure as a corridor.
- Keep all route checkpoints visible and dim routes that are not selected, preserving comparison context.
- Color route segments by nearby checkpoint risk so severe weather is visible directly on the map.
- Never disguise API failures as successful demo results; mock mode is explicitly opt-in through `VITE_USE_MOCK=true`.
- Convert the local `datetime-local` input to an ISO UTC timestamp before sending it to Django.

## Build

```bash
npm run build
npm run preview
```
