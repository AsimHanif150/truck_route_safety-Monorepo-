// Ordered from safest to most dangerous. `score` is used for averages,
// `heat` is the 0-1 intensity used by the heatmap layer.
export const RISK = {
  low: { label: 'Low', score: 0, heat: 0.15, color: '#16a36a' },
  moderate: { label: 'Moderate', score: 1, heat: 0.4, color: '#d69b21' },
  high: { label: 'High', score: 2, heat: 0.65, color: '#e87932' },
  severe: { label: 'Severe', score: 3, heat: 0.85, color: '#dc4c4c' },
  no_travel: { label: 'No travel', score: 4, heat: 1, color: '#8b2635' },
}

export const RISK_ORDER = Object.keys(RISK)

export const FORECAST_HOURS = 48
