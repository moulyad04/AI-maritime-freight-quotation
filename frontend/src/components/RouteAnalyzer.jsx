import { useState } from 'react'
import { analyzeRoute } from '../api'

const initialForm = {
  origin: 'Chennai',
  destination: 'Rotterdam',
  cargo_type: 'Electronics',
  containers: 10,
}

export default function RouteAnalyzer({ token, username, onLogout }) {
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await analyzeRoute(
        { ...form, containers: Number(form.containers) },
        token,
      )
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">⚓</span>
          <span>Agentic Maritime Brokerage</span>
        </div>
        <div className="topbar-right">
          <span className="user-chip">{username}</span>
          <button className="btn-ghost" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="content">
        <section className="panel form-panel">
          <h2>Shipment request</h2>
          <p className="panel-subtitle">
            Tell the Route Agent what you need to move.
          </p>

          <form onSubmit={handleSubmit} className="route-form">
            <label className="field">
              <span>Origin</span>
              <input
                value={form.origin}
                onChange={(e) => updateField('origin', e.target.value)}
                required
              />
            </label>

            <label className="field">
              <span>Destination</span>
              <input
                value={form.destination}
                onChange={(e) => updateField('destination', e.target.value)}
                required
              />
            </label>

            <label className="field">
              <span>Cargo type</span>
              <input
                value={form.cargo_type}
                onChange={(e) => updateField('cargo_type', e.target.value)}
                required
              />
            </label>

            <label className="field">
              <span>Containers</span>
              <input
                type="number"
                min="1"
                value={form.containers}
                onChange={(e) => updateField('containers', e.target.value)}
                required
              />
            </label>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Analyzing route…' : 'Analyze route'}
            </button>
          </form>
        </section>

        <section className="panel result-panel">
          <h2>Route Agent recommendation</h2>

          {error && <p className="auth-error">{error}</p>}

          {!result && !error && (
            <p className="empty-state">
              Submit a shipment request to see the Route Agent's recommendation.
            </p>
          )}

          {result && result.status === 'not_found' && (
            <p className="empty-state">{result.message}</p>
          )}

          {result && result.status === 'success' && (
            <div>
              <p className="result-reason" style={{ marginBottom: 20 }}>
                Comparing {result.routes.length} route
                {result.routes.length > 1 ? 's' : ''} from {result.origin} to{' '}
                {result.destination}. {result.reason}
              </p>

              <div className="route-list">
                {result.routes.map((route) => (
                  <div
                    key={route.route_id}
                    className={
                      'route-card' +
                      (route.is_recommended ? ' route-card-best' : '')
                    }
                  >
                    <div className="result-route">
                      <span className="route-code">{route.route_id}</span>
                      <span className="route-path">
                        {result.origin} → {result.destination}
                      </span>
                      {route.is_recommended && (
                        <span className="best-badge">Recommended</span>
                      )}
                    </div>

                    <dl className="result-grid">
                      <div>
                        <dt>Transit time</dt>
                        <dd>{route.transit_time_days} days</dd>
                      </div>
                      <div>
                        <dt>Distance</dt>
                        <dd>{route.distance_nm.toLocaleString()} NM</dd>
                      </div>
                      <div>
                        <dt>Transshipments</dt>
                        <dd>{route.transshipments}</dd>
                      </div>
                      <div>
                        <dt>Route type</dt>
                        <dd>{route.route_type}</dd>
                      </div>
                      <div>
                        <dt>Base freight</dt>
                        <dd>${route.base_freight_usd.toLocaleString()}</dd>
                      </div>
                      <div>
                        <dt>Containers</dt>
                        <dd>{result.containers}</dd>
                      </div>
                    </dl>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}