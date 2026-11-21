import { useState } from 'react'
import { getRoutes } from '../services/routeService'

export default function useTripPlanner() {
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [source, setSource] = useState('api')

  const createPlan = async (payload) => {
    setLoading(true)
    setError('')
    try {
      const result = await getRoutes(payload)
      setPlan(result.data)
      setSource(result.source)
    } catch (requestError) {
      setPlan(null)
      setError(
        requestError.response?.data?.error ||
          requestError.message ||
          'Unable to plan this trip. Check the backend and try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  return { plan, loading, error, source, createPlan, setPlan }
}
