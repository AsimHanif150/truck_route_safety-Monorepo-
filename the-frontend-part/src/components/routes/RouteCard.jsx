import RiskBadge from '../common/RiskBadge'
import { formatDuration, formatNumber } from '../../utils/formatters'
export default function RouteCard({ route, selected, onSelect, recommended }) {
  const s = route.summary || {},
    risk =
      s.no_travel_miles > 0
        ? 'no_travel'
        : s.severe_miles > 0
          ? 'severe'
          : s.high_miles > 0
            ? 'high'
            : s.moderate_miles > 0
              ? 'moderate'
              : 'low'
  return (
    <button
      className={`route-card ${selected ? 'selected' : ''}`}
      onClick={() => onSelect(route.id)}
    >
      <div className="route-card-top">
        <div>
          <span className="route-name">{route.name || 'Route option'}</span>
          <div className="route-meta">
            {formatNumber(route.distance_miles)} mi <i /> {formatDuration(route.duration_minutes)}
          </div>
        </div>
        <div className="route-tags">
          {recommended && <span className="recommended">BEST MATCH</span>}
          <RiskBadge level={risk} />
        </div>
      </div>
      <div className="route-stats">
        <div>
          <b>{formatNumber(s.severe_miles)} mi</b>
          <small>Severe</small>
        </div>
        <div>
          <b>{formatNumber(s.high_miles)} mi</b>
          <small>High risk</small>
        </div>
        <div>
          <b>
            {Number(s.avg_risk || 0).toFixed(1)}
            <small>/ 4</small>
          </b>
          <small>Avg. risk</small>
        </div>
      </div>
      <div className="route-progress">
        <span
          style={{
            width: `${Math.max(3, 100 - ((s.severe_miles + s.high_miles) / (route.distance_miles || 1)) * 100)}%`,
          }}
        />
      </div>
      <div className="route-card-bottom">
        <span>{route.summary_text || 'View route checkpoints and weather'}</span>
        <span>View details →</span>
      </div>
    </button>
  )
}
