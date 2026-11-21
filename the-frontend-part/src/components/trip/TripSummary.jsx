export default function TripSummary({ origin, destination, departure, loadWeight }) {
  return (
    <section className="panel trip-summary">
      <span className="eyebrow">TRIP SUMMARY</span>
      <h3>
        {origin || 'Origin'} → {destination || 'Destination'}
      </h3>
      <p>Departure: {departure ? new Date(departure).toLocaleString() : 'Not set'}</p>
      <p>Load: {loadWeight ? `${Number(loadWeight).toLocaleString()} lb` : 'Not set'}</p>
    </section>
  )
}
