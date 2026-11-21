import { useEffect, useState } from 'react'
import TripForm from '../components/trip/TripForm'
import RouteMap from '../components/map/RouteMap'
import RouteList from '../components/routes/RouteList'
import RouteComparison from '../components/routes/RouteComparison'
import WeatherPanel from '../components/weather/WeatherPanel'
import WeatherTimeline from '../components/weather/WeatherTimeline'
import Loader from '../components/common/Loader'
import useTripPlanner from '../hooks/useTripPlanner'
import useRoutes from '../hooks/useRoutes'
import useWeatherForecast from '../hooks/useWeatherForecast'

const NO_ROUTES = []

export default function Dashboard() {
  const { plan, loading, error, source, createPlan } = useTripPlanner()
  const routes = plan?.routes ?? NO_ROUTES
  const { selected, selectedId, setSelectedId } = useRoutes(routes, plan?.recommended_route_id)
  const { hours, setHours, heatmap } = useWeatherForecast(routes)
  const [checkpoint, setCheckpoint] = useState(null)
  const [heatEnabled, setHeatEnabled] = useState(true)
  const [showComparison, setShowComparison] = useState(false)

  // A checkpoint belongs to one route of one plan; drop it when either changes.
  useEffect(() => {
    setCheckpoint(null)
  }, [plan, selectedId])
  const recommendation = routes.find((route) => route.id === plan?.recommended_route_id)

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#">
          <span className="brand-mark">
            <i />
            <i />
            <i />
          </span>
          <span>
            haul<span className="brand-light">safe</span>
          </span>
        </a>
        <nav>
          <a className="nav-active" href="#planner">
            Trip planner
          </a>
          <a href="#routes">Route analysis</a>
          <a href="#weather">Weather</a>
        </nav>
        <div className="top-status">
          <span className="status-dot" /> DRIVER SAFETY CONSOLE
        </div>
      </header>
      <section className="hero-banner">
        <div>
          <span className="eyebrow light">WEATHER-AWARE TRUCK ROUTING</span>
          <h1>
            Every mile, <em>safer.</em>
          </h1>
          <p>
            Compare routes, understand weather exposure, and make confident decisions before you hit
            the road.
          </p>
        </div>
        <div className="hero-art">
          <div className="sun-orbit" />
          <div className="road-line">〰</div>
          <div className="hero-stat">
            <span>ROUTE INTELLIGENCE</span>
            <b>
              01 <small>/ 03</small>
            </b>
          </div>
        </div>
      </section>
      <div className="dashboard-grid" id="planner">
        <aside className="left-column">
          <TripForm onSubmit={createPlan} loading={loading} />
          <div className="safety-note">
            <span>✦</span>
            <div>
              <b>Safety comes first</b>
              <p>
                Routes are ranked by severe exposure, high-risk miles, average risk, then travel
                time.
              </p>
            </div>
          </div>
        </aside>
        <section className="main-column">
          {loading && (
            <div className="panel loading-panel">
              <Loader />
            </div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              {error}
            </div>
          )}
          {!plan && !loading && !error && (
            <div className="empty-state">
              <div className="empty-icon">↗</div>
              <h2>Your next journey starts here</h2>
              <p>
                Enter your origin, destination, departure time and load weight to compare three
                weather-aware routes.
              </p>
              <div className="empty-steps">
                <span>01 · Set trip details</span>
                <span>02 · Compare route risk</span>
                <span>03 · Choose with confidence</span>
              </div>
            </div>
          )}
          {plan && (
            <>
              <div className="section-head" id="routes">
                <div>
                  <span className="eyebrow">ROUTE OVERVIEW</span>
                  <h2>Choose your safest route</h2>
                </div>
                <div className="head-actions">
                  <span className={`data-source ${source === 'api' ? 'connected' : ''}`}>
                    {source === 'api' ? '● API CONNECTED' : '● DEMO DATA'}
                  </span>
                  <button
                    className="text-button"
                    onClick={() => setShowComparison(!showComparison)}
                  >
                    {showComparison ? 'Hide comparison' : 'Compare all routes'} ↗
                  </button>
                </div>
              </div>
              {plan.warnings?.length > 0 && (
                <div className="no-safe-banner" role="alert">
                  {plan.warnings.map((message) => (
                    <p key={message}>{message}</p>
                  ))}
                </div>
              )}
              {recommendation && (
                <div className="recommendation">
                  <div className="rec-icon">✦</div>
                  <div>
                    <span>RECOMMENDED ROUTE</span>
                    <b>{recommendation.name}</b>
                    <p>
                      Best ranked using severe miles, high-risk miles, average risk and journey
                      duration.
                    </p>
                  </div>
                  <span className="rec-check">✓</span>
                </div>
              )}
              <div className="map-panel">
                <div className="map-toolbar">
                  <div>
                    <b>Route map</b>
                    <span>All route options · Checkpoint weather</span>
                  </div>
                  <label className="toggle-label">
                    <input
                      type="checkbox"
                      checked={heatEnabled}
                      onChange={(event) => setHeatEnabled(event.target.checked)}
                    />{' '}
                    Weather heatmap
                  </label>
                </div>
                <RouteMap
                  routes={routes}
                  selectedId={selectedId}
                  heatmap={heatmap}
                  showHeatmap={heatEnabled}
                  onCheckpoint={setCheckpoint}
                />
                <div className="map-legend">
                  <span>
                    <i className="legend-line active-line" />
                    Selected route
                  </span>
                  <span>
                    <i className="legend-line other-line" />
                    Other routes
                  </span>
                  <span>
                    <i className="legend-dot" />
                    Weather checkpoints
                  </span>
                </div>
              </div>
              <div className="section-head compact">
                <div>
                  <span className="eyebrow">AVAILABLE OPTIONS</span>
                  <h2>
                    Route comparison <small>({routes.length})</small>
                  </h2>
                </div>
              </div>
              <p className="route-note" role="note">
                Routes use a standard driving profile and are not guaranteed to be truck-legal.
                Check height, weight and hazmat restrictions before you drive.
              </p>
              <RouteList
                routes={routes}
                selectedId={selectedId}
                onSelect={setSelectedId}
                recommendedId={plan.recommended_route_id}
              />
              {showComparison && (
                <div className="panel comparison-panel">
                  <h3>Side-by-side comparison</h3>
                  <RouteComparison routes={routes} />
                </div>
              )}
              <div className="section-head compact" id="weather">
                <div>
                  <span className="eyebrow">CHECKPOINT ANALYSIS</span>
                  <h2>Weather along the way</h2>
                </div>
              </div>
              <WeatherPanel
                forecast={hours}
                setForecast={setHours}
                checkpoint={checkpoint}
                setCheckpoint={setCheckpoint}
              />
              <div className="panel timeline-panel">
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">SELECTED ROUTE</span>
                    <h2>Checkpoint timeline</h2>
                  </div>
                  <span className="checkpoint-count">
                    {selected?.checkpoints?.length || 0} checkpoints
                  </span>
                </div>
                <WeatherTimeline
                  checkpoints={selected?.checkpoints || []}
                  onSelect={setCheckpoint}
                />
              </div>
            </>
          )}
        </section>
      </div>
      <footer>
        <span>© 2026 HaulSafe · Weather-aware truck routing</span>
        <span>Plan smart. Drive safe.</span>
      </footer>
    </main>
  )
}