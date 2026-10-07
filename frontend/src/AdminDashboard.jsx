import { useEffect, useState } from "react";
import { getAllQuotations, decideQuotation, updateQuotation } from "./services/routeApi";
import QuotationDetails, { money, RiskBadge } from "./QuotationDetails";

function statusClass(status) {
  if (status === "accepted") return "status-badge status-accepted";
  if (status === "rejected") return "status-badge status-rejected";
  return "status-badge status-pending";
}

function AdminDashboard({ username, onLogout }) {
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actingId, setActingId] = useState(null);
  const [selectedDate, setSelectedDate] = useState("");

  const [editingId, setEditingId] = useState(null);
  const [editValues, setEditValues] = useState({});
  const [expandedId, setExpandedId] = useState(null);

  const loadQuotations = async (date = "") => {
    setLoading(true);
    setError("");
    try {
      const data = await getAllQuotations(date);
      setQuotations(data);
    } catch (err) {
      if (err.isAuthError) {
        setError(err.message);
        onLogout();
      } else {
        setError("Could not load quotations. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuotations();
  }, []);

  const handleDateChange = (event) => {
    const date = event.target.value;
    setSelectedDate(date);
    loadQuotations(date);
  };

  const handleClearFilter = () => {
    setSelectedDate("");
    loadQuotations();
  };

  const handleDecision = async (id, status) => {
    setActingId(id);
    try {
      await decideQuotation(id, status);
      await loadQuotations(selectedDate);
    } catch (err) {
      if (err.isAuthError) {
        setError(err.message);
        onLogout();
      } else {
        setError("Could not update this quotation.");
      }
    } finally {
      setActingId(null);
    }
  };

  const startEdit = (q) => {
    setEditingId(q.id);
    setEditValues({
      recommended_route: q.recommended_route,
      containers: q.containers,
      freight_per_container_usd: q.freight_per_container_usd,
      total_freight_usd: q.total_freight_usd,
      transit_time_days: q.transit_time_days
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValues({});
  };

  const handleEditChange = (field, value) => {
    setEditValues((prev) => ({ ...prev, [field]: value }));
  };

  const saveEdit = async (id) => {
    setActingId(id);
    try {
      await updateQuotation(id, {
        recommended_route: editValues.recommended_route,
        containers: Number(editValues.containers),
        freight_per_container_usd: Number(editValues.freight_per_container_usd),
        total_freight_usd: Number(editValues.total_freight_usd),
        transit_time_days: Number(editValues.transit_time_days)
      });
      setEditingId(null);
      setEditValues({});
      await loadQuotations(selectedDate);
    } catch (err) {
      if (err.isAuthError) {
        setError(err.message);
        onLogout();
      } else {
        setError("Could not save changes to this quotation.");
      }
    } finally {
      setActingId(null);
    }
  };

  const toggleDetails = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const count = (status) => quotations.filter((q) => q.status === status).length;
  const totalValue = quotations.reduce((sum, q) => sum + (Number(q.total_freight_usd) || 0), 0);

  return (
    <div className="page">
      <div className="topbar">
        <div className="brand">
          <span className="brand-icon">⚓</span>
          <div>
            <h1>Admin dashboard</h1>
            <p className="topbar-subtitle">Review, edit and decide on customer quotations</p>
          </div>
        </div>
        <div className="topbar-user">
          <span className="user-chip">🛡️ {username} · admin</span>
          <button type="button" className="btn-outline-light" onClick={onLogout}>
            Log out
          </button>
        </div>
      </div>

      <div className="page-body">
        <div className="kpis">
          <div className="kpi kpi-blue"><span>Quotations</span><b>{quotations.length}</b></div>
          <div className="kpi kpi-amber"><span>Pending</span><b>{count("pending")}</b></div>
          <div className="kpi kpi-green"><span>Accepted</span><b>{count("accepted")}</b></div>
          <div className="kpi kpi-red"><span>Rejected</span><b>{count("rejected")}</b></div>
          <div className="kpi kpi-violet"><span>Total value</span><b>{money(totalValue)}</b></div>
        </div>

        <div className="card table-card card-blue">
          <div className="filter-row">
            <label htmlFor="date-filter">Filter by date</label>
            <input
              id="date-filter"
              type="date"
              value={selectedDate}
              onChange={handleDateChange}
            />
            {selectedDate && (
              <button type="button" className="btn-outline" onClick={handleClearFilter}>
                Clear filter
              </button>
            )}
            <span className="filter-count">
              {loading
                ? "Loading..."
                : `${quotations.length} quotation${quotations.length === 1 ? "" : "s"}`}
              {selectedDate ? ` on ${selectedDate}` : " · all time"}
            </span>
          </div>

          {error && <p className="form-error">{error}</p>}

          {!loading && !error && quotations.length === 0 && (
            <p className="empty-state">
              {selectedDate
                ? `No quotations were generated on ${selectedDate}.`
                : "No quotations have been generated yet."}
            </p>
          )}

          {!loading && quotations.length > 0 && (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Customer</th>
                    <th>Lane</th>
                    <th>Route</th>
                    <th>Containers</th>
                    <th>Per container</th>
                    <th>Total</th>
                    <th>Transit</th>
                    <th>Risk</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {quotations.map((q) => {
                    const isEditing = editingId === q.id;
                    return [
                      <tr key={q.id}>
                        <td>{q.id}</td>
                        <td>{q.username}</td>
                        <td>{q.origin} → {q.destination}</td>

                        <td>
                          {isEditing ? (
                            <input
                              className="edit-input"
                              value={editValues.recommended_route}
                              onChange={(e) => handleEditChange("recommended_route", e.target.value)}
                            />
                          ) : (
                            q.recommended_route
                          )}
                        </td>

                        <td>
                          {isEditing ? (
                            <input
                              className="edit-input edit-input-narrow"
                              type="number"
                              min="1"
                              value={editValues.containers}
                              onChange={(e) => handleEditChange("containers", e.target.value)}
                            />
                          ) : (
                            q.containers
                          )}
                        </td>

                        <td>
                          {isEditing ? (
                            <input
                              className="edit-input edit-input-narrow"
                              type="number"
                              step="0.01"
                              value={editValues.freight_per_container_usd}
                              onChange={(e) => handleEditChange("freight_per_container_usd", e.target.value)}
                            />
                          ) : (
                            money(q.freight_per_container_usd)
                          )}
                        </td>

                        <td>
                          {isEditing ? (
                            <input
                              className="edit-input edit-input-narrow"
                              type="number"
                              step="0.01"
                              value={editValues.total_freight_usd}
                              onChange={(e) => handleEditChange("total_freight_usd", e.target.value)}
                            />
                          ) : (
                            <b>{money(q.total_freight_usd)}</b>
                          )}
                        </td>

                        <td>
                          {isEditing ? (
                            <input
                              className="edit-input edit-input-narrow"
                              type="number"
                              min="1"
                              value={editValues.transit_time_days}
                              onChange={(e) => handleEditChange("transit_time_days", e.target.value)}
                            />
                          ) : (
                            `${q.transit_time_days} d`
                          )}
                        </td>

                        <td>{q.overall_risk ? <RiskBadge level={q.overall_risk} /> : "-"}</td>
                        <td>{q.created_at.slice(0, 10)}</td>
                        <td><span className={statusClass(q.status)}>{q.status}</span></td>

                        <td>
                          {isEditing ? (
                            <div className="action-buttons">
                              <button
                                type="button"
                                className="btn-accept"
                                disabled={actingId === q.id}
                                onClick={() => saveEdit(q.id)}
                              >
                                Save
                              </button>
                              <button
                                type="button"
                                className="btn-outline"
                                disabled={actingId === q.id}
                                onClick={cancelEdit}
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <div className="action-buttons">
                              <button
                                type="button"
                                className="btn-details"
                                onClick={() => toggleDetails(q.id)}
                              >
                                {expandedId === q.id ? "Hide" : "Details"}
                              </button>
                              <button
                                type="button"
                                className="btn-outline"
                                disabled={actingId !== null}
                                onClick={() => startEdit(q)}
                              >
                                Edit
                              </button>
                              {q.status === "pending" && (
                                <>
                                  <button
                                    type="button"
                                    className="btn-accept"
                                    disabled={actingId === q.id}
                                    onClick={() => handleDecision(q.id, "accepted")}
                                  >
                                    Accept
                                  </button>
                                  <button
                                    type="button"
                                    className="btn-reject"
                                    disabled={actingId === q.id}
                                    onClick={() => handleDecision(q.id, "rejected")}
                                  >
                                    Reject
                                  </button>
                                </>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>,
                      expandedId === q.id && (
                        <tr key={`${q.id}-details`} className="details-row">
                          <td colSpan="12">
                            <QuotationDetails details={q.details} />
                          </td>
                        </tr>
                      )
                    ];
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;