import RouteCard from './RouteCard'
export default function RouteList({ routes, selectedId, onSelect, recommendedId }) {
  return (
    <div className="route-list">
      {routes?.map((r) => (
        <RouteCard
          key={r.id}
          route={r}
          selected={selectedId === r.id}
          onSelect={onSelect}
          recommended={recommendedId === r.id}
        />
      ))}
    </div>
  )
}
