import RiskBadge from '../common/RiskBadge'
export default function WeatherTimeline({ checkpoints = [], onSelect }) {
  return (
    <div className="timeline">
      {checkpoints.map((c) => (
        <button key={c.id} className="timeline-item" onClick={() => onSelect(c)}>
          <span className="timeline-dot" style={{ background: `var(--${c.risk_level},#64748b)` }} />
          <span>
            <b>{c.mile} mi</b>
            <small>
              {c.eta
                ? new Date(c.eta).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
                : 'ETA pending'}
            </small>
          </span>
          <RiskBadge level={c.risk_level} />
        </button>
      ))}
    </div>
  )
}
