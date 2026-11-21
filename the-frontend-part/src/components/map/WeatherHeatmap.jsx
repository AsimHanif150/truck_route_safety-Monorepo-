import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import { HeatLayer } from 'leaflet.heat'

const OPTIONS = {
  radius: 34,
  blur: 25,
  max: 1,
  maxZoom: 10,
  gradient: { 0.25: '#37b7a5', 0.5: '#e9c64a', 0.75: '#ee873d', 1: '#d84a4a' },
}

// The layer is created once and updated in place with setLatLngs, which is far
// cheaper than removing and rebuilding it on every slider move.
export default function WeatherHeatmap({ points = [] }) {
  const map = useMap()
  const layerRef = useRef(null)

  useEffect(() => {
    const layer = new HeatLayer([], OPTIONS).addTo(map)
    layerRef.current = layer
    return () => {
      map.removeLayer(layer)
      layerRef.current = null
    }
  }, [map])

  useEffect(() => {
    layerRef.current?.setLatLngs(points.map((p) => [p.lat, p.lng, p.intensity ?? 0.5]))
  }, [points])

  return null
}
