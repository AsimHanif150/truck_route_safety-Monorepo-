import { Polyline } from 'react-leaflet'
import { riskColor } from '../../utils/riskColors'

const toLatLng = (point) => (Array.isArray(point) ? point : [point.lat, point.lng])

function nearestCheckpoint(route, point) {
  return (route.checkpoints || []).reduce((best, checkpoint) => {
    const distance = Math.hypot(checkpoint.lat - point[0], checkpoint.lng - point[1])
    return !best || distance < best.distance ? { checkpoint, distance } : best
  }, null)?.checkpoint
}

export default function RoutePolyline({ route, active }) {
  const points = (route.geometry || []).map(toLatLng)
  if (points.length < 2) return null
  return points.slice(0, -1).map((point, index) => {
    const checkpoint = nearestCheckpoint(route, point)
    return (
      <Polyline
        key={`${route.id}-segment-${index}`}
        positions={[point, points[index + 1]]}
        pathOptions={{
          color: riskColor(checkpoint?.risk_level || 'moderate'),
          weight: active ? 6 : 4,
          opacity: active ? 0.95 : 0.38,
        }}
      />
    )
  })
}
