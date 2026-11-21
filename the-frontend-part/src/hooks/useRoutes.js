import { useMemo, useState } from 'react'
export default function useRoutes(routes = [], recommendedId) {
  const [selectedId, setSelectedId] = useState('')
  const selected = useMemo(
    () =>
      routes.find((r) => r.id === selectedId) ||
      routes.find((r) => r.id === recommendedId) ||
      routes[0],
    [routes, selectedId, recommendedId],
  )
  return { selected, selectedId: selected?.id || '', setSelectedId }
}
