export default function ForecastSlider({ value, onChange }) {
  return (
    <div className="forecast-control">
      <div className="forecast-label">
        <span>Forecast window</span>
        <b>{value} hours</b>
      </div>
      <input
        type="range"
        min="0"
        max="48"
        step="1"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <div className="range-labels">
        <span>Now</span>
        <span>24 hours</span>
        <span>48 hours</span>
      </div>
    </div>
  )
}
