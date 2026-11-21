import ForecastSlider from './ForecastSlider'
import CheckpointDetails from './CheckpointDetails'

export default function WeatherPanel({ forecast, setForecast, checkpoint, setCheckpoint }) {
  return (
    <section className="panel weather-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">WEATHER INTELLIGENCE</span>
          <h2>Trip conditions</h2>
        </div>
        <span className="live-dot">Forecast</span>
      </div>
      <ForecastSlider value={forecast} onChange={setForecast} />
      <div className="heat-legend">
        <span>
          <i style={{ background: '#37b7a5' }} />
          Low
        </span>
        <span>
          <i style={{ background: '#e9c64a' }} />
          Moderate
        </span>
        <span>
          <i style={{ background: '#ee873d' }} />
          High
        </span>
        <span>
          <i style={{ background: '#d84a4a' }} />
          Severe
        </span>
      </div>
      <CheckpointDetails
        checkpoint={checkpoint}
        onClose={() => setCheckpoint(null)}
        hour={forecast}
      />
    </section>
  )
}
