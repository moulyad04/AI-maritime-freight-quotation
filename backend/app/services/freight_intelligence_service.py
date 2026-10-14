from app.services.quotation_service import QuotationService


class FreightIntelligenceService:
    """
    Freight Intelligence Engine (Milestone 3, Step 1).

    Runs the existing agent pipeline once (Route, Pricing, Weather, Customs,
    Shipment Risk, Margin) and combines everything into one unified response:
    route intelligence, pricing intelligence, risk intelligence and a
    business recommendation.

    Cost and profit figures are internal. They are included only when
    is_admin=True, so customers never receive them.
    """

    RISK_INDEX = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

    def __init__(self, quotation_service=None):
        self.quotation_service = quotation_service or QuotationService()

    def generate_freight_intelligence(
        self,
        origin,
        destination,
        cargo_type,
        containers,
        documents_ready=None,
        is_admin=False,
    ):
        q = self.quotation_service.generate_quotation(
            origin=origin,
            destination=destination,
            cargo_type=cargo_type,
            containers=containers,
            documents_ready=documents_ready,
        )

        if q.get("status") != "success":
            return q

        risk = q["risk_report"]
        customs = q["customs"]
        missing = customs.get("missing_documents", [])
        overall = risk["overall_risk"]

        route_intelligence = {
            "recommended_route": q["recommended_route"],
            "route_type": q["route_type"],
            "route_score": q["route_score"],
            "transit_time_days": q["transit_time_days"],
            "distance_nm": q["distance_nm"],
            "transshipments": q["transshipments"],
        }

        pricing_intelligence = {
            "price_per_container_usd": q["freight_per_container_usd"],
            "total_quotation_usd": q["total_freight_usd"],
        }
        if is_admin:
            containers_n = q["containers"]
            cost_per_container = q["pricing"]["demand_adjusted_cost_usd"]
            pricing_intelligence.update({
                "total_cost_usd": round(cost_per_container * containers_n, 2),
                "total_profit_usd": round(
                    q["margin"]["margin_amount_usd"] * containers_n, 2
                ),
                "applied_margin_percent": q["margin"]["applied_margin_percent"],
            })

        risk_intelligence = {
            "weather_risk": risk["weather_risk"],
            "customs_risk": risk["customs_risk"],
            "customs_status": "Complete" if not missing else "Documents missing",
            "overall_risk": overall,
            "risk_score": self.RISK_INDEX.get(overall),  # 1 = LOW, 2 = MEDIUM, 3 = HIGH
            "missing_documents": missing,
        }

        return {
            "status": "success",
            "shipment": {
                "origin": origin,
                "destination": destination,
                "cargo_type": cargo_type,
                "containers": containers,
            },
            "route_intelligence": route_intelligence,
            "pricing_intelligence": pricing_intelligence,
            "risk_intelligence": risk_intelligence,
            "business_recommendation": self._recommend(overall, missing, risk),
            "alternatives": q.get("alternatives", []),
        }

    @staticmethod
    def _recommend(overall, missing, risk):
        if overall == "HIGH":
            decision = "REVIEW BEFORE COMMITTING"
        elif overall == "MEDIUM" or missing:
            decision = "PROCEED WITH CONDITIONS"
        else:
            decision = "PROCEED"

        return {
            "decision": decision,
            "summary": risk["summary"],
            "actions": risk["recommendations"],
        }

