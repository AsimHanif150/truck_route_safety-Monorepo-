import { useDeferredValue, useMemo, useState } from 'react'
import { FORECAST_HOURS, RISK } from '../constants/riskLevels'

const MAX_SAMPLES_PER_ROUTE = 800
const MAX_GAP_DEGREES = 0.15 // fill larger gaps so sparse geometry still reads as a band

const toLatLng = (p) => (Array.isArray(p) ? p : [p.lat, p.lng])
const heatOf = (level) => RISK[level]?.heat ?? 0.15

// Heat intensity of one checkpoint for every forecast hour (index = hour).
function heatByHour(checkpoint) {
  const forecast = checkpoint.forecast || []
  return Array.from({ length: FORECAST_HOURS + 1 }, (_, hour) => {
    const step = forecast.find((f) => Number(f.hour) === hour) || forecast[hour] || checkpoint
    return heatOf(step.risk_level)
  })
}

// Points along every route, each tied to its nearest checkpoint. Built once per trip,
// so a slider move only needs a cheap array lookup per point.
function buildCorridor(routes) {
  const heat = []
  const samples = []

  for (const route of routes) {
    const checkpoints = route.checkpoints || []
    const geometry = (route.geometry || []).map(toLatLng)
    if (geometry.length < 2 || !checkpoints.length) continue

    const table = checkpoints.map(heatByHour)
    const offset = heat.length
    heat.push(...table)

    // Routes only move forward, so the nearest checkpoint index never goes backwards.
    let j = 0
    const dist = (p, c) => Math.hypot(c.lat - p[0], c.lng - p[1])
    const add = (point) => {
      while (
        j + 1 < checkpoints.length &&
        dist(point, checkpoints[j + 1]) <= dist(point, checkpoints[j])
      )
        j++
      samples.push({ lat: point[0], lng: point[1], row: offset + j })
    }

    const stride = Math.max(1, Math.ceil(geometry.length / MAX_SAMPLES_PER_ROUTE))
    let prev = null
    for (let i = 0; i < geometry.length; i += stride) {
      const point = geometry[i]
      if (prev) {
        const gap = Math.hypot(point[0] - prev[0], point[1] - prev[1])
        const steps = Math.min(40, Math.floor(gap / MAX_GAP_DEGREES))
        for (let s = 1; s <= steps; s++) {
          const t = s / (steps + 1)
          add([prev[0] + (point[0] - prev[0]) * t, prev[1] + (point[1] - prev[1]) * t])
        }
      }
      add(point)
      prev = point
    }
  }
  return { heat, samples }
}

// Slider state plus heatmap points for the chosen hour. The whole 48 h forecast arrives
// with the trip, so moving the slider never calls the server.
export default function useWeatherForecast(routes) {
  const [hours, setHours] = useState(0)
  const deferredHours = useDeferredValue(hours) // thumb stays instant, heatmap catches up

  const corridor = useMemo(() => buildCorridor(routes), [routes])
  const heatmap = useMemo(
    () =>
      corridor.samples.map((s) => ({
        lat: s.lat,
        lng: s.lng,
        intensity: corridor.heat[s.row][deferredHours],
      })),
    [corridor, deferredHours],
  )

  return { hours, setHours, heatmap }
}
