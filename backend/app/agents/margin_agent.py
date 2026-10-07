class MarginAgent:
    """
    Applies the target margin from pricing.csv to the demand-adjusted cost.
    Riskier shipments carry a small extra margin (risk uplift), so the risk
    report directly affects the final price.
    """

    RISK_UPLIFT_PERCENT = {
        "LOW": 0.0,
        "MEDIUM": 2.0,
        "HIGH": 5.0,
        "UNKNOWN": 0.0,
    }

    def calculate_margin(self, demand_adjusted_cost, target_margin_percent, overall_risk):
        uplift = self.RISK_UPLIFT_PERCENT.get(overall_risk, 0.0)
        applied_margin = target_margin_percent + uplift

        selling_price = demand_adjusted_cost * (1 + applied_margin / 100)
        margin_amount = selling_price - demand_adjusted_cost

        return {
            "target_margin_percent": target_margin_percent,
            "risk_uplift_percent": uplift,
            "applied_margin_percent": round(applied_margin, 2),
            "margin_amount_usd": round(margin_amount, 2),
            "selling_price_per_container_usd": round(selling_price, 2),
        }