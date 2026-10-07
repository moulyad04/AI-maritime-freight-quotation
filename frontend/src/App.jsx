import { useEffect, useState } from "react";
import {
  generateQuotation,
  getMyQuotations,
  getOptions,
  getRequiredDocuments
} from "./services/routeApi";
import { logout as logoutUser } from "./services/authApi";
import AuthPage from "./AuthPage";
import AdminDashboard from "./AdminDashboard";
import QuotationDetails, { money, RiskBadge } from "./QuotationDetails";
import "./App.css";

const PIPELINE = [
  { icon: "🧭", label: "Route" },
  { icon: "💰", label: "Pricing" },
  { icon: "🌦️", label: "Weather" },
  { icon: "🛃", label: "Customs" },
  { icon: "📋", label: "Risk report" },
  { icon: "📈", label: "Final price" }
];

function statusClass(status) {
  if (status === "accepted") return "status-badge status-accepted";
  if (status === "rejected") return "status-badge status-rejected";
  return "status-badge status-pending";
}

function App() {
  const [username, setUsername] = useState(
    localStorage.getItem("username") || ""
  );
  const [role, setRole] = useState(localStorage.getItem("role") || "");

  const [options, setOptions] = useState({
    origins: [],
    lanes: {},
    cargo_types: [],
    documents: [],
    total_routes: 0
  });

  const [formData, setFormData] = useState({
    origin: "",
    destination: "",
    cargo_type: "Electronics",
    containers: 10,
    documents_ready: []
  });

  const [requiredDocs, setRequiredDocs] = useState([]);
  const [quotation, setQuotation] = useState(null);
  const [myQuotations, setMyQuotations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogout = () => {
    logoutUser();
    setUsername("");
    setRole("");
    setQuotation(null);
    setMyQuotations([]);
    setError("");
  };

  const loadMyQuotations = async () => {
    try {
      const data = await getMyQuotations();
      setMyQuotations(data);
    } catch (err) {
      if (err.isAuthError) {
        handleLogout();
      }
    }
  };

  const loadOptions = async () => {
    try {
      const data = await getOptions();
      setOptions(data);

      const origin = data.origins.includes("Chennai") ? "Chennai" : data.origins[0] || "";
      const destinations = data.lanes[origin] || [];
      const destination = destinations.includes("Rotterdam")
        ? "Rotterdam"
        : destinations[0] || "";

      setFormData((prev) => ({ ...prev, origin, destination }));
    } catch (err) {
      if (err.isAuthError) {
        handleLogout();
      } else {
        setError("Could not load form options. Is the backend running?");
      }
    }
  };

  useEffect(() => {
    if (username && role === "customer") {
      loadOptions();
      loadMyQuotations();
    }
  }, [username, role]);

  // Whenever the cargo or destination changes, ask the backend which
  // customs documents are actually required for that combination.
  useEffect(() => {
    if (!username || role !== "customer") return;
    if (!formData.destination || !formData.cargo_type) return;

    getRequiredDocuments(formData.cargo_type, formData.destination)
      .then((data) => {
        setRequiredDocs(data.required_documents);
        // drop ticks for documents that are no longer required
        setFormData((prev) => ({
          ...prev,
          documents_ready: prev.documents_ready.filter((d) =>
            data.required_documents.includes(d)
          )
        }));
      })
      .catch((err) => {
        if (err.isAuthError) {
          handleLogout();
        }
      });
  }, [formData.cargo_type, formData.destination, username, role]);

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value
    });
  };

  const handleOriginChange = (event) => {
    const origin = event.target.value;
    const destinations = options.lanes[origin] || [];
    setFormData((prev) => ({
      ...prev,
      origin,
      destination: destinations.includes(prev.destination)
        ? prev.destination
        : destinations[0] || ""
    }));
  };

  const toggleDocument = (doc) => {
    setFormData((prev) => ({
      ...prev,
      documents_ready: prev.documents_ready.includes(doc)
        ? prev.documents_ready.filter((d) => d !== doc)
        : [...prev.documents_ready, doc]
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setQuotation(null);

    try {
      const result = await generateQuotation({
        ...formData,
        containers: Number(formData.containers)
      });
      setQuotation(result);
      await loadMyQuotations();
    } catch (err) {
      if (err.isAuthError) {
        setError(err.message);
        handleLogout();
      } else {
        setError("Unable to generate quotation. Please check the backend.");
      }
    } finally {
      setLoading(false);
    }
  };

  if (!username) {
    return (
      <AuthPage
        onAuthSuccess={(name, userRole) => {
          setUsername(name);
          setRole(userRole);
        }}
      />
    );
  }

  if (role === "admin") {
    return <AdminDashboard username={username} onLogout={handleLogout} />;
  }

  const success = quotation && quotation.status === "success";
  const pipelineState = loading ? "working" : success ? "done" : "idle";

  return (
    <div className="page">
      <div className="topbar">
        <div className="brand">
          <span className="brand-icon">⚓</span>
          <div>
            <h1>Maritime Freight Quotation</h1>
            <p className="topbar-subtitle">AI-powered pricing, weather and customs intelligence</p>
          </div>
        </div>
        <div className="topbar-user">
          <span className="user-chip">👤 {username}</span>
          <button type="button" className="btn-outline-light" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </div>

      <div className="page-body">
        <div className="hero">
          <div>
            <h2>Get a fully priced, risk-checked quote</h2>
            <p>Pick your lane, cargo and paperwork. Six agents do the rest.</p>
          </div>
          <div className="hero-stats">
            <div><b>{options.total_routes}</b><span>routes</span></div>
            <div><b>{options.origins.length}</b><span>origin ports</span></div>
            <div><b>6</b><span>AI agents</span></div>
          </div>
        </div>

        <div className="pipeline">
          {PIPELINE.map((step, index) => (
            <div
              key={step.label}
              className={`pipe-step pipe-${pipelineState} pipe-c${index}`}
              style={{ animationDelay: `${index * 0.12}s` }}
            >
              <span className="pipe-icon">{step.icon}</span>
              <span>{step.label}</span>
              {pipelineState === "done" && <em>✓</em>}
            </div>
          ))}
        </div>

        <div className="dashboard">
          <div className="card card-blue">
            <h2>Shipment details</h2>
            <form className="route-form" onSubmit={handleSubmit}>
              <div className="field">
                <label htmlFor="origin">Origin port</label>
                <select id="origin" name="origin" value={formData.origin} onChange={handleOriginChange}>
                  {options.origins.map((port) => (
                    <option key={port} value={port}>{port}</option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="destination">Destination port</label>
                <select id="destination" name="destination" value={formData.destination} onChange={handleChange}>
                  {(options.lanes[formData.origin] || []).map((port) => (
                    <option key={port} value={port}>{port}</option>
                  ))}
                </select>
              </div>

              <div className="field-row">
                <div className="field">
                  <label htmlFor="cargo_type">Cargo type</label>
                  <select id="cargo_type" name="cargo_type" value={formData.cargo_type} onChange={handleChange}>
                    {options.cargo_types.map((cargo) => (
                      <option key={cargo} value={cargo}>{cargo}</option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label htmlFor="containers">Containers</label>
                  <input
                    id="containers"
                    name="containers"
                    type="number"
                    min="1"
                    value={formData.containers}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="field">
                <label>Customs documents</label>
                <p className="doc-help">
                  Customs will ask for these documents for{" "}
                  <b>{formData.cargo_type}</b> going to <b>{formData.destination}</b>.
                  Tap the ones you already have. Anything left untapped is
                  flagged as missing, which raises your customs risk and can
                  raise the handling fee.
                </p>
                <div className="chip-group">
                  {requiredDocs.map((doc) => {
                    const on = formData.documents_ready.includes(doc);
                    return (
                      <button
                        type="button"
                        key={doc}
                        className={on ? "chip chip-on" : "chip"}
                        onClick={() => toggleDocument(doc)}
                      >
                        {on ? "✓ " : ""}{doc}
                      </button>
                    );
                  })}
                </div>
                <span className="doc-count">
                  {formData.documents_ready.length} of {requiredDocs.length} ready
                </span>
              </div>

              <button type="submit" className="btn-primary" disabled={loading || !formData.origin}>
                {loading ? "Agents are working..." : "Generate quotation"}
              </button>
            </form>
          </div>

          <div className="card card-teal">
            <h2>Quotation result</h2>

            {!quotation && !loading && !error && (
              <p className="empty-state">
                Choose your shipment details and generate a quotation to see
                the recommended route, price, weather and customs checks here.
              </p>
            )}

            {loading && <p className="empty-state">The agents are analysing routes, pricing, weather and customs...</p>}

            {error && <p className="form-error">{error}</p>}

            {success && (
              <>
                <div className="result-hero">
                  <div>
                    <span className="result-label">Recommended route</span>
                    <div className="result-code">
                      {quotation.recommended_route}
                      <span className="result-type">{quotation.route_type}</span>
                    </div>
                    <div className="result-path">
                      {quotation.origin} → {quotation.destination}
                    </div>
                  </div>
                  <div className="result-price">
                    <span className="result-label">Total quote</span>
                    <b>{money(quotation.total_freight_usd)}</b>
                    <small>{money(quotation.freight_per_container_usd)} per container × {quotation.containers}</small>
                  </div>
                </div>

                <div className="tiles">
                  <div className="tile tile-blue"><span>Route score</span><b>{quotation.route_score}</b></div>
                  <div className="tile tile-teal"><span>Transit</span><b>{quotation.transit_time_days} days</b></div>
                  <div className="tile tile-violet"><span>Distance</span><b>{quotation.distance_nm} nm</b></div>
                  <div className="tile tile-amber"><span>Overall risk</span><b><RiskBadge level={quotation.risk_report.overall_risk} /></b></div>
                </div>

                <div className="status-line">
                  Status: <span className={statusClass(quotation.quotation_status)}>{quotation.quotation_status}</span>
                  <span className="muted"> · awaiting admin review</span>
                </div>

                {quotation.alternatives.length > 0 && (
                  <>
                    <p className="alt-heading">Alternative routes ({quotation.alternatives.length})</p>
                    {quotation.alternatives.slice(0, 4).map((route) => (
                      <div className="alternative" key={route.route_id}>
                        <strong>{route.route_id}</strong>
                        <span>{route.route_type}</span>
                        <span>Score {route.route_score}</span>
                        <span>{route.transit_days} days</span>
                      </div>
                    ))}
                  </>
                )}
              </>
            )}

            {quotation && quotation.status === "not_found" && (
              <p className="form-error">{quotation.message}</p>
            )}
          </div>
        </div>

        {success && (
          <div className="section">
            <h2 className="section-title">Full breakdown</h2>
            <QuotationDetails details={quotation} />
          </div>
        )}

        {myQuotations.length > 0 && (
          <div className="card table-card">
            <h2>My quotations</h2>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Route</th>
                    <th>Containers</th>
                    <th>Total</th>
                    <th>Risk</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {myQuotations.map((q) => (
                    <tr key={q.id}>
                      <td>{q.id}</td>
                      <td>{q.origin} → {q.destination} ({q.recommended_route})</td>
                      <td>{q.containers}</td>
                      <td>{money(q.total_freight_usd)}</td>
                      <td>{q.overall_risk ? <RiskBadge level={q.overall_risk} /> : "-"}</td>
                      <td><span className={statusClass(q.status)}>{q.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;