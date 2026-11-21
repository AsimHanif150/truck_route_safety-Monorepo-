// Demo data generator. Its output is the API contract the Django backend must follow:
//
// plan = {
//   origin, destination, forecast_start (ISO), forecast_hours (48),
//   recommended_route_id,
//   routes: [{
//     id, name, distance_miles, duration_minutes,
//     geometry: [[lat, lng], ...],
//     summary: { low_miles, moderate_miles, high_miles, severe_miles, no_travel_miles, avg_risk },
//     checkpoints: [{
//       id, lat, lng, mile, eta, risk_level, wind_mph, rain_in_hr, snow_in_hr,  // weather at ETA
//       forecast: [{ hour, wind_mph, rain_in_hr, snow_in_hr, risk_level }, ...]   // hours 0..48
//     }]
//   }]
// }
import { FORECAST_HOURS, RISK } from '../constants/riskLevels'
import { classifyWeather } from './mock/riskRules'
import { weatherAt } from './mock/weatherModel'

const GEOMETRY_STEPS = 96
const CHECKPOINT_EVERY = 8 // geometry steps, so 12 checkpoints per route

const ROUTE_DEFS = [
  {
    id: 'r1',
    name: 'Route 1 (Fastest)',
    distance: 1004,
    minutes: 900,
    waypoints: [
      [41.878, -87.63],
      [41.586, -93.625],
      [41.256, -95.934],
      [41.124, -100.765],
      [39.739, -104.99],
    ],
  },
  {
    id: 'r2',
    name: 'Route 2 (Balanced)',
    distance: 1050,
    minutes: 950,
    waypoints: [
      [41.878, -87.63],
      [40.8, -92.0],
      [40.8, -96.7],
      [40.2, -100.5],
      [39.739, -104.99],
    ],
  },
  {
    id: 'r3',
    name: 'Route 3 (Southern)',
    distance: 1120,
    minutes: 1020,
    waypoints: [
      [41.878, -87.63],
      [39.5, -91.0],
      [39.1, -95.7],
      [38.9, -100.0],
      [39.739, -104.99],
    ],
  },
]

// Point at `fraction` (0-1) along a polyline, by cumulative length.
function pointAlong(waypoints, fraction) {
  const lengths = waypoints
    .slice(1)
    .map((p, i) => Math.hypot(p[0] - waypoints[i][0], p[1] - waypoints[i][1]))
  const target = fraction * lengths.reduce((a, b) => a + b, 0)
  let walked = 0
  for (let i = 0; i < lengths.length; i++) {
    if (walked + lengths[i] >= target || i === lengths.length - 1) {
      const t = lengths[i] ? (target - walked) / lengths[i] : 0
      const [a, b] = [waypoints[i], waypoints[i + 1]]
      return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
    }
    walked += lengths[i]
  }
}

function buildRoute(def, { startMs, loadLb }) {
  const geometry = []
  for (let i = 0; i <= GEOMETRY_STEPS; i++)
    geometry.push(pointAlong(def.waypoints, i / GEOMETRY_STEPS))

  const checkpoints = []
  for (let i = CHECKPOINT_EVERY; i < GEOMETRY_STEPS; i += CHECKPOINT_EVERY) {
    const fraction = i / GEOMETRY_STEPS
    const [lat, lng] = geometry[i]
    const etaMs = startMs + fraction * def.minutes * 60000
    const etaHour = Math.min(FORECAST_HOURS, Math.round((etaMs - startMs) / 3600000))

    const forecast = Array.from({ length: FORECAST_HOURS + 1 }, (_, hour) => {
      const w = weatherAt(lat, lng, hour)
      return { hour, ...w, risk_level: classifyWeather(w, loadLb) }
    })

    const { wind_mph, rain_in_hr, snow_in_hr, risk_level } = forecast[etaHour]
    checkpoints.push({
      id: `${def.id}-${checkpoints.length + 1}`,
      lat,
      lng,
      mile: Math.round(fraction * def.distance),
      eta: new Date(etaMs).toISOString(),
      risk_level,
      wind_mph,
      rain_in_hr,
      snow_in_hr,
      forecast,
    })
  }

  // Each checkpoint stands for an equal share of the route.
  const milesEach = def.distance / checkpoints.length
  const summary = {
    low_miles: 0,
    moderate_miles: 0,
    high_miles: 0,
    severe_miles: 0,
    no_travel_miles: 0,
  }
  let scoreTotal = 0
  for (const c of checkpoints) {
    const key = c.risk_level === 'no_travel' ? 'no_travel_miles' : `${c.risk_level}_miles`
    summary[key] += Math.round(milesEach)
    scoreTotal += RISK[c.risk_level].score
  }
  summary.avg_risk = Number((scoreTotal / checkpoints.length).toFixed(2))

  return {
    id: def.id,
    name: def.name,
    distance_miles: def.distance,
    duration_minutes: def.minutes,
    geometry,
    summary,
    checkpoints,
  }
}

// Same order the assessment asks for, with No travel miles checked first.
const rankKey = (r) => [
  r.summary.no_travel_miles,
  r.summary.severe_miles,
  r.summary.high_miles,
  r.summary.avg_risk,
  r.duration_minutes,
]

function compareRoutes(a, b) {
  const [ka, kb] = [rankKey(a), rankKey(b)]
  for (let i = 0; i < ka.length; i++) if (ka[i] !== kb[i]) return ka[i] - kb[i]
  return 0
}

export function buildMockPlan(payload = {}) {
  const departure = payload.departure ? new Date(payload.departure) : new Date()
  const startMs = Math.floor(departure.getTime() / 3600000) * 3600000 // top of the hour
  const loadLb = Number(payload.load_weight) || 36000

  const routes = ROUTE_DEFS.map((def) => buildRoute(def, { startMs, loadLb }))
  const best = [...routes].sort(compareRoutes)[0]

  return {
    // Demo data always travels Chicago -> Denver; only the labels follow the form.
    origin: { name: payload.origin || 'Chicago, IL', lat: 41.878, lng: -87.63 },
    destination: { name: payload.destination || 'Denver, CO', lat: 39.739, lng: -104.99 },
    forecast_start: new Date(startMs).toISOString(),
    forecast_hours: FORECAST_HOURS,
    recommended_route_id: best.id,
    routes,
  }
}
