import { buildMockPlan } from './mockTrip'
import { planTrip } from './tripService'

// Demo mode is opt-in (VITE_USE_MOCK=true). Real API failures are never hidden.
export async function getRoutes(payload) {
  if (import.meta.env.VITE_USE_MOCK === 'true') {
    await new Promise((resolve) => setTimeout(resolve, 700)) // let the loading state show
    return { data: buildMockPlan(payload), source: 'demo' }
  }
  const data = await planTrip(payload)
  return { data, source: 'api' }
}
