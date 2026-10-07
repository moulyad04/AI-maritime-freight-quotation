export function money(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return "-";
  return (
    "$" +
    n.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
  );
}

export function RiskBadge({ level }) {
  const key = (level || "unknown").toLowerCase();
  return <span className={`risk-badge risk-${key}`}>{level || "N/A"}</span>;
}

function Row({ label, value, strong }) {
  return (
    <div className={strong ? "kv kv-strong" : "kv"}>
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

/*
  Shows the pricing breakdown, weather, customs and risk report.
  `details` is either a fresh quotation from the API or the saved
  `details` object of a stored quotation (both use the same keys).

  Customers receive a simplified `pricing` object (no `margin`), so they
  get the customer price panel. Admins receive `margin` as well, so they
  get the full internal breakdown.
*/
function QuotationDetails({ details }) {
  if (!details) {
    return (
      <p className="empty-state">
        No detailed breakdown was saved for this older quotation.
      </p>
    );
  }

  const { pricing, weather, customs, risk_report: risk, margin } = details;
  const weatherOk = weather && weather.status === "success";
  const customsOk = customs && customs.status === "success";

  return (
    <div className="details">
      {risk && (
        <div className={`risk-banner risk-banner-${(risk.overall_risk || "unknown").toLowerCase()}`}>
          <div className="risk-banner-head">
            <h3>Shipment risk report</h3>
            <RiskBadge level={risk.overall_risk} />
          </div>
          <p className="risk-summary">{risk.summary}</p>
          <div className="risk-split">
            <span>🌦️ Weather: <RiskBadge level={risk.weather_risk} /></span>
            <span>🛃 Customs: <RiskBadge level={risk.customs_risk} /></span>
          </div>
          <ul className="risk-list">
            {risk.recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="detail-grid">
        {pricing && margin && (
          <div className="panel panel-pricing">
            <h3>💰 Pricing breakdown</h3>
            <Row label="Base freight" value={money(pricing.base_freight_usd)} />
            <Row label="Fuel surcharge" value={money(pricing.fuel_surcharge_usd)} />
            <Row label="Port charges" value={money(pricing.port_charge_usd)} />
            <Row label="Risk surcharge" value={money(pricing.risk_surcharge_usd)} />
            <Row label="Operating cost" value={money(pricing.operating_cost_usd)} strong />
            <Row label="Demand factor" value={`× ${pricing.demand_factor}`} />
            <Row label="Demand-adjusted cost" value={money(pricing.demand_adjusted_cost_usd)} strong />
            <Row label="Target margin" value={`${margin.target_margin_percent}%`} />
            <Row label="Risk uplift" value={`+${margin.risk_uplift_percent}%`} />
            <Row label="Margin amount" value={money(margin.margin_amount_usd)} />
            <Row label="Final price / container" value={money(margin.selling_price_per_container_usd)} strong />
          </div>
        )}

        {pricing && !margin && (
          <div className="panel panel-pricing">
            <h3>💰 Price breakdown</h3>
            <Row label="Base freight" value={money(pricing.base_freight_usd)} />
            <Row label="Fuel surcharge" value={money(pricing.fuel_surcharge_usd)} />
            <Row label="Port charges" value={money(pricing.port_charge_usd)} />
            <Row label="Service & risk handling" value={money(pricing.service_and_risk_fee_usd)} />
            <Row label="Price per container" value={money(pricing.final_price_per_container_usd)} strong />
            <p className="panel-note">
              Covers carrier, port and handling costs for this route. Higher
              weather or customs risk can increase the handling fee.
            </p>
          </div>
        )}

        {weatherOk && (
          <div className="panel panel-weather">
            <h3>🌦️ Weather assessment</h3>
            <div className="panel-badge-row">
              <RiskBadge level={weather.weather_risk} />
              <span className="muted">{weather.weather_condition} · {weather.risk_points} risk points</span>
            </div>
            <Row label="Region" value={weather.region} />
            <Row label="Wind speed" value={`${weather.wind_speed_knots} knots`} />
            <Row label="Wave height" value={`${weather.wave_height_m} m`} />
            <Row label="Visibility" value={`${weather.visibility_km} km`} />
            <Row label="Storm probability" value={`${weather.storm_probability_percent}%`} />
            <p className="panel-note">{weather.recommendation}</p>
          </div>
        )}

        {customsOk && (
          <div className="panel panel-customs">
            <h3>🛃 Customs validation</h3>
            <div className="panel-badge-row">
              <RiskBadge level={customs.customs_risk} />
              <span className={customs.validation_status === "READY" ? "pill pill-ok" : "pill pill-warn"}>
                {customs.validation_status}
              </span>
            </div>
            <ul className="doc-list">
              {customs.required_documents.map((doc) => {
                const missing = customs.missing_documents.includes(doc);
                return (
                  <li key={doc} className={missing ? "doc doc-missing" : "doc doc-ok"}>
                    <span>{missing ? "✗" : "✓"}</span> {doc}
                  </li>
                );
              })}
            </ul>
            {customs.issues.length > 0 && (
              <ul className="issue-list">
                {customs.issues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            )}
            <p className="panel-note">
              Estimated clearance: {customs.estimated_clearance_days} day
              {customs.estimated_clearance_days === 1 ? "" : "s"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default QuotationDetails;