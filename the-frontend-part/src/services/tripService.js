import api from './api'
export async function planTrip(payload) {
  const response = await api.post('/api/trips/plan/', payload)
  return response.data
}
