// Tiny synthetic weather model: two moving storm cells over the central US.
const STORMS = [
  // Wind + snow front moving east across Nebraska.
  { lat: 41.3, lng: -107, vLng: 0.5, radius: 4, wind: 40, rain: 0, snow: 2.6 },
  // Slow rain band over Missouri / Kansas.
  { lat: 39.0, lng: -97, vLng: 0.2, radius: 3.2, wind: 22, rain: 0.8, snow: 0 },
]

const round = (n, digits = 2) => Number(n.toFixed(digits))

export function weatherAt(lat, lng, hour) {
  let wind = 8 + Math.abs(Math.sin(lat * 3 + lng)) * 6
  let rain = 0
  let snow = 0

  for (const s of STORMS) {
    const centerLng = s.lng + s.vLng * hour
    const distance = Math.hypot(lat - s.lat, (lng - centerLng) * Math.cos((lat * Math.PI) / 180))
    const k = Math.max(0, 1 - distance / s.radius)
    wind += k * s.wind
    rain += k ** 1.5 * s.rain
    snow += k ** 2 * s.snow
  }

  return { wind_mph: round(wind, 1), rain_in_hr: round(rain), snow_in_hr: round(snow) }
}
