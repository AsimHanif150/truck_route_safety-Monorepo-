// Demo-only copy of the assessment risk rules, used to build mock data.
// The Django backend is the source of truth for real trips.
import { RISK_ORDER } from '../../constants/riskLevels'

// Each rule lists the lower bound of Moderate, High, Severe and No travel.
// `strictLast` means No travel only starts strictly above the last bound.
const RULES = {
  wind: { bounds: [25, 35, 45, 55], strictLast: false },
  rain: { bounds: [0.1, 0.25, 0.5, 1.0], strictLast: true },
  snow: { bounds: [0.5, 1.0, 2.0, 3.0], strictLast: true },
}

function band(value, { bounds, strictLast }) {
  let level = 0
  bounds.forEach((bound, i) => {
    const isLast = i === bounds.length - 1
    if (isLast && strictLast ? value > bound : value >= bound) level = i + 1
  })
  return level
}

export function classifyWeather({ wind_mph, rain_in_hr, snow_in_hr }, loadLb) {
  let level = Math.max(
    band(wind_mph, RULES.wind),
    band(rain_in_hr, RULES.rain),
    band(snow_in_hr, RULES.snow),
  )

  // Load rules can only raise the level.
  if (wind_mph >= 55) level = 4
  else if (wind_mph >= 45 && loadLb > 30000) level = 4
  else if (wind_mph >= 35 && wind_mph < 45 && loadLb > 40000) level = Math.max(level, 3)

  return RISK_ORDER[level]
}
