import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useEffect } from 'react'
import RoutePolyline from './RoutePolyline'
import CheckpointMarker from './CheckpointMarker'
import WeatherHeatmap from './WeatherHeatmap'

const icon = L.divIcon({
  className: 'map-pin',
  html: '<span>●</span>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
})

function Fit({ routes, selected }) {
  const map = useMap()
  useEffect(() => {
    const route = routes.find((item) => item.id === selected) || routes[0]
    if (route?.geometry?.length) map.fitBounds(route.geometry, { padding: [45, 45] })
  }, [routes, selected, map])
  return null
}

export default function RouteMap({ routes = [], selectedId, heatmap, showHeatmap, onCheckpoint }) {
  const active = routes.find((route) => route.id === selectedId) || routes[0]
  const origin = active?.geometry?.[0]
  const destination = active?.geometry?.at(-1)
  return (
    <MapContainer center={[39.5, -98.35]} zoom={4} scrollWheelZoom className="route-map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Fit routes={routes} selected={selectedId} />
      {routes.map((route) => (
        <RoutePolyline key={route.id} route={route} active={route.id === selectedId} />
      ))}
      {showHeatmap && <WeatherHeatmap points={heatmap || []} />}
      {origin && (
        <Marker position={origin} icon={icon}>
          <Popup>Trip origin</Popup>
        </Marker>
      )}
      {destination && (
        <Marker position={destination} icon={icon}>
          <Popup>Trip destination</Popup>
        </Marker>
      )}
      {routes.flatMap((route) =>
        (route.checkpoints || []).map((checkpoint) => (
          <CheckpointMarker
            key={checkpoint.id}
            checkpoint={checkpoint}
            active={route.id === selectedId}
            onClick={() => onCheckpoint({ ...checkpoint, route_name: route.name })}
          />
        )),
      )}
    </MapContainer>
  )
}
