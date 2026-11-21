import { formatDuration } from '../../utils/formatters'
export default function RouteComparison({ routes }) {
  return (
    <div className="comparison-wrap">
      <table className="comparison">
        <thead>
          <tr>
            <th>Route</th>
            <th>Distance</th>
            <th>Travel time</th>
            <th>Severe miles</th>
            <th>High miles</th>
            <th>Avg. risk</th>
          </tr>
        </thead>
        <tbody>
          {routes.map((r) => (
            <tr key={r.id}>
              <td>{r.name}</td>
              <td>{r.distance_miles} mi</td>
              <td>{formatDuration(r.duration_minutes)}</td>
              <td>{r.summary?.severe_miles ?? 0}</td>
              <td>{r.summary?.high_miles ?? 0}</td>
              <td>{Number(r.summary?.avg_risk || 0).toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
