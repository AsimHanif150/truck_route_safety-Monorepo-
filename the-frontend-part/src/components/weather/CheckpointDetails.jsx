import RiskBadge from '../common/RiskBadge'
import { formatEta } from '../../utils/formatters'

export default function CheckpointDetails({ checkpoint, onClose, hour = 0 }) {
  if (!checkpoint) return null
  const weather =
    checkpoint.forecast?.find((item) => Number(item.hour) === hour) ||
    checkpoint.forecast?.[hour] ||
    checkpoint
  const level = weather.risk_level || checkpoint.risk_level
  return (
    <div className="checkpoint-detail">
      <div className="detail-head">
        <div>
          <span className="eyebrow">CHECKPOINT · {checkpoint.mile} MI</span>
          <h3>{checkpoint.route_name || 'Weather conditions'}</h3>
        </div>
        <button className="icon-button" onClick={onClose}>
          ×
        </button>
      </div>
      <div className="detail-risk">
        <RiskBadge level={level} />
        <span>Estimated arrival: {formatEta(checkpoint.eta)}</span>
      </div>
      <div className="weather-metrics">
        <div>
          💨<b>{weather.wind_mph ?? '—'} mph</b>
          <small>Wind</small>
        </div>
        <div>
          🌧<b>{weather.rain_in_hr ?? '—'} in/hr</b>
          <small>Rain</small>
        </div>
        <div>
          ❄<b>{weather.snow_in_hr ?? '—'} in/hr</b>
          <small>Snow</small>
        </div>
      </div>
    </div>
  )
}
