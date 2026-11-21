import { useState } from 'react'
import Button from '../common/Button'

function toLocalDateTimeValue(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState(() => ({
    origin: 'Chicago, IL',
    destination: 'Denver, CO',
    departure: toLocalDateTimeValue(new Date(Date.now() + 3600000)),
    load_weight: 36000,
    checkpoint_interval: 25,
  }))
  const change = (event) => setForm({ ...form, [event.target.name]: event.target.value })
  const submit = (event) => {
    event.preventDefault()
    const departureDate = new Date(form.departure)
    onSubmit({
      ...form,
      departure: departureDate.toISOString(),
      load_weight: Number(form.load_weight),
      checkpoint_interval: Number(form.checkpoint_interval),
    })
  }
  return (
    <form className="trip-form" onSubmit={submit}>
      <div className="form-heading">
        <div>
          <span className="eyebrow">NEW JOURNEY</span>
          <h2>Plan a truck trip</h2>
        </div>
        <span className="form-icon">↗</span>
      </div>
      <label>
        Origin
        <input
          name="origin"
          value={form.origin}
          onChange={change}
          placeholder="City, state"
          required
        />
      </label>
      <label>
        Destination
        <input
          name="destination"
          value={form.destination}
          onChange={change}
          placeholder="City, state"
          required
        />
      </label>
      <div className="form-grid">
        <label>
          Departure date &amp; time
          <input
            type="datetime-local"
            name="departure"
            value={form.departure}
            onChange={change}
            required
          />
        </label>
        <label>
          Load weight (lb)
          <input
            type="number"
            name="load_weight"
            min="1"
            value={form.load_weight}
            onChange={change}
            required
          />
        </label>
      </div>
      <label>
        Weather checkpoint interval
        <select name="checkpoint_interval" value={form.checkpoint_interval} onChange={change}>
          <option value="10">Every 10 miles</option>
          <option value="25">Every 25 miles</option>
          <option value="50">Every 50 miles</option>
        </select>
      </label>
      <Button type="submit" disabled={loading}>
        {loading ? 'Planning routes…' : 'Find safest routes'} <span>→</span>
      </Button>
      <p className="form-footnote">Weather and load conditions are evaluated along your journey.</p>
    </form>
  )
}
