export const toLatLng = (geometry) =>
  (geometry || []).map((p) => (Array.isArray(p) ? p : [p.lat, p.lng]))
