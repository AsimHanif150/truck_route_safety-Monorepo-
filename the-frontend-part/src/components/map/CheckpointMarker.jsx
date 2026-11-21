import { CircleMarker, Tooltip } from 'react-leaflet'
import { riskColor } from '../../utils/riskColors'

export default function CheckpointMarker({ checkpoint, active = true, onClick }) {
  return (
    <CircleMarker
      center={[checkpoint.lat, checkpoint.lng]}
      radius={active ? 7 : 5}
      eventHandlers={{ click: onClick }}
      pathOptions={{
        color: '#fff',
        weight: 2,
        fillColor: riskColor(checkpoint.risk_level),
        fillOpacity: active ? 1 : 0.4,
        opacity: active ? 1 : 0.5,
      }}
    >
      <Tooltip>
        {checkpoint.route_name ? `${checkpoint.route_name} · ` : ''}Mile {checkpoint.mile} ·{' '}
        {checkpoint.risk_level}
      </Tooltip>
    </CircleMarker>
  )
}
